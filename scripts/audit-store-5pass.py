#!/usr/bin/env python3
"""
Обязательный preflight перед push (расширяется по каждому инциденту на ГУ).
Базовые 5 проходов + systemd + mock check.sh.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE_LIMIT = 64 * 1024 * 1024
LFS = re.compile(rb"^version https://git-lfs\.github\.com/spec/v1")
REQ_JS = re.compile(r"""require\s*\(\s*['"](\./[^'"]+)['"]\s*\)""")
EXTERNAL = frozenset(
    {
        "mgu-render",
        "mgu-inputgate",
        "mgu-deploy",
        "mgu-python",
        "mgu-updater",
        "idrive7-renderd",
    }
)


def git_tracked_bytes(rel: str) -> int:
    proc = subprocess.run(
        ["git", "ls-files", rel],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    total = 0
    for line in proc.stdout.splitlines():
        p = ROOT / line.strip()
        if p.is_file():
            total += p.stat().st_size
    return total


def pass1_catalog() -> tuple[list[str], list[str]]:
    """Проход 1: mgu-repo — все id, версии, unit, нет build на tools."""
    errs: list[str] = []
    warns: list[str] = []
    repo = json.loads((ROOT / "mgu-repo.json").read_text())
    ids: list[str] = []
    for c in repo.get("components", []):
        ids.append(c["id"])
        if c.get("kind") == "app" and c.get("build") != "unit":
            errs.append(f"pass1: {c['id']} не unit build (на ГУ снова build.py)")
        p = ROOT / c["path"]
        if not (p / "mgu-app.json").is_file():
            errs.append(f"pass1: {c['id']} без mgu-app.json")
        if not (p / "package" / "package.json").is_file():
            errs.append(f"pass1: {c['id']} без package/package.json")
    ex = set(repo.get("apps", {}).get("exclude") or [])
    for c in repo.get("components", []):
        if c.get("kind") == "app" and c["id"] not in ex:
            errs.append(f"pass1: {c['id']} не в apps.exclude (дубль в Store)")
    for t in repo.get("tools", []):
        ids.append(t["id"])
        if not (ROOT / t["path"] / "component.json").is_file():
            errs.append(f"pass1: tool {t['id']} нет component.json")
    from collections import Counter

    for k, v in Counter(ids).items():
        if v > 1:
            errs.append(f"pass1: дубль id {k}")
    apps_dir = ROOT / "apps"
    for app_json in apps_dir.glob("*/app.json"):
        aid = json.loads(app_json.read_text()).get("id")
        if aid not in ids:
            warns.append(f"pass1: apps/{app_json.parent.name} не в mgu-repo (мёртвый каталог?)")
    return errs, warns


def pass2_store_download() -> tuple[list[str], list[str]]:
    """Проход 2: размер git-tracked папки (лимит Store ~64 MiB на job)."""
    errs: list[str] = []
    warns: list[str] = []
    repo = json.loads((ROOT / "mgu-repo.json").read_text())
    for c in repo.get("components", []) + repo.get("tools", []):
        rel = c["path"]
        nbytes = git_tracked_bytes(rel)
        mib = nbytes / 1024 / 1024
        tag = f"{c['id']} ({rel}): {mib:.1f} MiB git"
        if nbytes > STORE_LIMIT:
            errs.append(f"pass2: {tag} > 64 MiB — скачивание с GitHub может оборваться")
        elif nbytes > STORE_LIMIT * 0.85:
            warns.append(f"pass2: {tag} близко к лимиту")
    return errs, warns


def pass3_install_layout() -> tuple[list[str], list[str]]:
    """Проход 3: файлы from=, LFS-pointer, simulate scripts."""
    errs: list[str] = []
    for script in ("validate-component-json.py", "simulate-hu-tool.py", "validate-mgu-app.py"):
        p = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if p.returncode:
            errs.append(f"pass3: {script} FAIL\n{p.stdout}")
    return errs, []


def pass4_dependencies() -> tuple[list[str], list[str]]:
    """Проход 4: requires, версии пинов, внешние зависимости."""
    errs: list[str] = []
    warns: list[str] = []
    repo = json.loads((ROOT / "mgu-repo.json").read_text())
    listed: dict[str, str] = {}
    versions: dict[str, str] = {}
    for c in repo.get("components", []):
        listed[c["id"]] = c["path"]
        versions[c["id"]] = json.loads((ROOT / c["path"] / "app.json").read_text())["version"]
        mj = json.loads((ROOT / c["path"] / "mgu-app.json").read_text())
        if mj["version"] != versions[c["id"]]:
            errs.append(f"pass4: {c['id']} app.json {versions[c['id']]} != mgu-app {mj['version']}")
        pj = json.loads((ROOT / c["path"] / "package/package.json").read_text())
        if pj.get("version") != versions[c["id"]]:
            errs.append(f"pass4: {c['id']} package.json {pj.get('version')} != app {versions[c['id']]}")
    for t in repo.get("tools", []):
        listed[t["id"]] = t["path"]
        comp = json.loads((ROOT / t["path"] / "component.json").read_text())
        versions[t["id"]] = str(comp["version"])

    for c in repo.get("components", []):
        app = json.loads((ROOT / c["path"] / "app.json").read_text())
        for dep, need in (app.get("requires") or {}).items():
            if dep in listed:
                have = versions.get(dep)
                if have and str(need) != str(have):
                    errs.append(f"pass4: {c['id']} requires {dep}@{need}, в репо @{have}")
            elif dep in EXTERNAL:
                warns.append(
                    f"pass4: {c['id']} требует {dep}@{need} — поставить из mgu-store/idrive7-apps ДО app"
                )
            else:
                errs.append(f"pass4: {c['id']} requires неизвестный {dep}@{need}")

    comp = json.loads((ROOT / "native/jap-filmix-d/component.json").read_text())
    if not comp.get("units"):
        errs.append("pass4: jap-filmix-d без systemd units")
    if not comp.get("check"):
        errs.append("pass4: jap-filmix-d без check")
    return errs, warns


def pass5_runtime_smoke() -> tuple[list[str], list[str]]:
    """Проход 5: ELF/LFS в артефактах, module graph, jap-node22 assemble."""
    errs: list[str] = []
    warns: list[str] = []
    repo = json.loads((ROOT / "mgu-repo.json").read_text())
    for t in repo.get("tools", []):
        base = ROOT / t["path"]
        comp = json.loads((base / "component.json").read_text())
        for ent in comp.get("files", []):
            src = base / (ent.get("from") or ent["path"])
            if src.is_file():
                head = src.read_bytes()[:64]
                if LFS.search(head):
                    errs.append(f"pass5: {t['id']} {src.name} — LFS pointer в git")
                if ent.get("path") in ("xray", "bin/node") and head[:4] != b"\x7fELF":
                    errs.append(f"pass5: {t['id']} {src.name} не ELF (на ГУ exec fail)")
                if src.name == "xray" and b"Mach-O" in head or (
                    src.suffix != ".gz" and head[:4] not in (b"\x7fELF", b"#!/")
                    and ent.get("mode", "").startswith("075")
                    and src.name not in ("krikun-runas",)
                ):
                    pass  # shell scripts in files[] — from *.sh

    xray_bin = ROOT / "tools/krikun-xray/prebuilt/xray"
    if xray_bin.is_file():
        probe = subprocess.run(["file", "-b", str(xray_bin)], capture_output=True, text=True)
        if "x86-64" not in probe.stdout or "ELF" not in probe.stdout:
            errs.append(f"pass5: krikun-xray/xray: {probe.stdout.strip()}")

    if t_id := "jap-node22":
        asm = ROOT / "tools/jap-node22/assemble.sh"
        if asm.is_file():
            import shutil
            import tempfile

            with tempfile.TemporaryDirectory() as td:
                stage = Path(td) / "current"
                stage.mkdir()
                comp = json.loads((ROOT / "tools/jap-node22/component.json").read_text())
                for ent in comp["files"]:
                    src = ROOT / "tools/jap-node22" / ent["from"]
                    dest = stage / ent["path"]
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
                r = subprocess.run(["/bin/sh", str(stage / "assemble.sh")], cwd=stage, capture_output=True, text=True)
                if r.returncode:
                    errs.append(f"pass5: jap-node22 assemble FAIL: {r.stderr or r.stdout}")
                node = stage / "bin" / "node"
                if not node.is_file() or node.stat().st_size < 50_000_000:
                    errs.append("pass5: jap-node22 assemble не дал ELF >50MB")
                elif node.read_bytes()[:4] != b"\x7fELF":
                    errs.append("pass5: jap-node22 bin/node не ELF")

    for mf in (ROOT / "apps").glob("*/mgu-app.json"):
        m = json.loads(mf.read_text())
        app_dir = mf.parent
        if not (app_dir / "package" / "manifest.json").is_file():
            errs.append(f"pass5: {app_dir.name} package/manifest.json missing (SOME/IP)")
        pkg = app_dir / "package"
        for must in ("permissions.json", "package.json"):
            if not (pkg / must).is_file():
                errs.append(f"pass5: {app_dir.name} package/{must} missing")

    return errs, warns


def pass6_systemd() -> tuple[list[str], list[str]]:
    errs: list[str] = []
    p = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "audit-systemd-units.py")],
        capture_output=True,
        text=True,
    )
    print(p.stdout, end="")
    if p.returncode:
        errs.append("pass6: audit-systemd-units.py failed")
    return errs, []


def pass7_mock_checks() -> tuple[list[str], list[str]]:
    errs: list[str] = []
    p = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "audit-checks-on-hu-mock.py")],
        capture_output=True,
        text=True,
    )
    print(p.stdout, end="")
    if p.returncode:
        errs.append("pass7: audit-checks-on-hu-mock.py failed")
    return errs, []


def pass8_krikun_xray_units() -> tuple[list[str], list[str]]:
    """Проход 8: krikun-xray unit + ELF runas (инцидент User=3922 / Mach-O runas)."""
    errs: list[str] = []
    svc = ROOT / "tools/krikun-xray/systemd/krikun-xray.service"
    if svc.is_file():
        text = svc.read_text(encoding="utf-8")
        if re.search(r"^User\s*=\s*3922\b", text, re.M):
            errs.append("pass8: krikun-xray.service: User=3922 (systemd без passwd)")
        if "krikun-runas" not in text:
            errs.append("pass8: krikun-xray.service: нет krikun-runas")
    runas = ROOT / "tools/krikun-xray/prebuilt/krikun-runas"
    if runas.is_file():
        r = subprocess.run(["file", "-b", str(runas)], capture_output=True, text=True)
        if "ELF" not in r.stdout or "x86-64" not in r.stdout:
            errs.append(f"pass8: prebuilt/krikun-runas: {r.stdout.strip()}")
    else:
        errs.append("pass8: нет prebuilt/krikun-runas (bash build.sh)")
    return errs, []


def pass9_catalog_json() -> tuple[list[str], list[str]]:
    """Проход 9: dist/catalog не врёт о версиях (если файл есть)."""
    errs: list[str] = []
    warns: list[str] = []
    cat = ROOT / "dist/catalog/catalog.json"
    if not cat.is_file():
        warns.append("pass9: нет dist/catalog/catalog.json (только main — ок)")
        return errs, warns
    repo = json.loads((ROOT / "mgu-repo.json").read_text())
    want: dict[str, str] = {}
    for t in repo.get("tools", []):
        comp = json.loads((ROOT / t["path"] / "component.json").read_text())
        want[comp["id"]] = str(comp["version"])
    for c in repo.get("components", []):
        want[c["id"]] = json.loads((ROOT / c["path"] / "app.json").read_text())["version"]
    data = json.loads(cat.read_text())
    for ent in data.get("components") or data.get("catalog") or []:
        if not isinstance(ent, dict):
            continue
        cid = ent.get("id")
        if cid not in want:
            continue
        av = str(ent.get("version") or ent.get("spec", {}).get("version") or "")
        blob = ent.get("artifact") or ent.get("spec", {}).get("artifact") or {}
        name = str(blob.get("name") or "")
        if av and av != want[cid]:
            warns.append(f"pass9: catalog {cid} version {av} != repo {want[cid]}")
        if want[cid] not in name and name:
            warns.append(f"pass9: catalog artifact {name} не содержит @{want[cid]}")
    return errs, warns


def pass11_mgu_architecture() -> tuple[list[str], list[str]]:
    """Проход 11: ELF/recmgr/internet uid/shrinkwrap/oap kit quotes/wireproxy."""
    errs: list[str] = []
    p = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "audit-mgu-architecture.py")],
        capture_output=True,
        text=True,
    )
    print(p.stdout, end="")
    if p.returncode:
        errs.append("pass11: audit-mgu-architecture.py failed")
    return errs, []


def pass10_check_preflight_hooks() -> tuple[list[str], list[str]]:
    """Проход 10: full mock check.sh — пути /var/opt через MGU_TOOL_* (инцидент krikun-xray)."""
    full_mock = frozenset({"krikun-xray"})
    errs: list[str] = []
    for comp_path in ROOT.glob("**/component.json"):
        comp = json.loads(comp_path.read_text())
        if comp.get("id") not in full_mock:
            continue
        for chk in comp.get("check") or []:
            sh = comp_path.parent / chk
            if not sh.is_file():
                continue
            text = sh.read_text(encoding="utf-8", errors="replace")
            if "/var/opt/" in text and "MGU_TOOL_CURRENT" not in text:
                errs.append(
                    f"pass10: {comp.get('id')} {chk} хардкод /var/opt без MGU_TOOL_CURRENT"
                )
    return errs, []


def main() -> int:
    all_errs: list[str] = []
    all_warns: list[str] = []
    names = (
        "Каталог mgu-repo",
        "Лимит 64 MiB (git)",
        "Раскладка /var/opt/.../current",
        "Зависимости requires",
        "Smoke assemble / manifest",
        "systemd (runas / NoNewPrivileges)",
        "check.sh на mock current/",
        "krikun-xray systemd (NoNewPrivileges)",
        "dist/catalog vs repo",
        "check.sh MGU_TOOL_* hooks",
        "MGU architecture (ELF/recmgr/…)",
    )
    steps = (
        pass1_catalog,
        pass2_store_download,
        pass3_install_layout,
        pass4_dependencies,
        pass5_runtime_smoke,
        pass6_systemd,
        pass7_mock_checks,
        pass8_krikun_xray_units,
        pass9_catalog_json,
        pass10_check_preflight_hooks,
        pass11_mgu_architecture,
    )
    for i, fn in enumerate(steps, 1):
        e, w = fn()
        print(f"=== Проход {i}: {names[i-1]} ===")
        print(f"  errors: {len(e)}, warns: {len(w)}")
        all_errs.extend(e)
        all_warns.extend(w)
    if all_warns:
        print("\nWARN:")
        for w in all_warns:
            print(f"  ⚠ {w}")
    if all_errs:
        print("\nFAIL:")
        for e in all_errs:
            print(f"  ✗ {e}")
        return 1
    print(f"\naudit-store: OK ({len(steps)}/{len(steps)} проходов)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())