#!/usr/bin/env python3
"""
Архитектурные проверки MGU (не покрытые validate/simulate): prebuilt ELF, recmgr,
internet uid в systemd, shrinkwrap, oap_link kit-кавычки, запрет wireproxy.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MACH_O = (
    b"\xfe\xed\xfa\xce",
    b"\xfe\xed\xfa\xcf",
    b"\xca\xfe\xba\xbe",
    b"\xce\xfa\xed\xfe",
    b"\xcf\xfa\xed\xfe",
)
KIT_SQ = re.compile(r"""require\s*\(\s*'\./kit/""")
USER_UID = re.compile(r"^User\s*=\s*(\d+)\s*$", re.M)
BANNED_IDS = re.compile(r"wireproxy|wireguard", re.I)
SKIP_PREBUILT_SUFFIX = {".gz", ".pyz", ".json", ".txt", ".md", ".LICENSE"}


def git_tracked_under(prefix: str, glob: str) -> list[Path]:
    proc = subprocess.run(
        ["git", "ls-files", glob],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    out: list[Path] = []
    for line in proc.stdout.splitlines():
        p = line.strip()
        if p.startswith(prefix):
            out.append(ROOT / p)
    return out


def strip_line_comment(line: str) -> str:
    if "//" in line:
        return line[: line.index("//")]
    return line


def check_prebuilt_elf(errs: list[str]) -> None:
    for base in (ROOT / "tools", ROOT / "native"):
        if not base.is_dir():
            continue
        for pre in base.glob("*/prebuilt/*"):
            if not pre.is_file():
                continue
            if pre.suffix.lower() in {".gz"} or pre.name in ("LICENSE", "node"):
                continue
            if pre.suffix.lower() in {".pyz"}:
                continue
            head = pre.read_bytes()[:4]
            if head in MACH_O:
                errs.append(f"prebuilt: {pre.relative_to(ROOT)} — Mach-O (нужен linux/amd64 ELF)")
                continue
            if pre.stat().st_size > 64 * 1024 and pre.suffix not in (".sh",):
                probe = subprocess.run(
                    ["file", "-b", str(pre)],
                    capture_output=True,
                    text=True,
                )
                out = probe.stdout.strip()
                if "Mach-O" in out:
                    errs.append(f"prebuilt: {pre.relative_to(ROOT)}: {out}")
                elif "ELF" in out and "x86-64" not in out and "executable" in out.lower():
                    errs.append(f"prebuilt: {pre.relative_to(ROOT)}: не x86-64 ELF: {out}")


def check_component_architecture(errs: list[str], warns: list[str]) -> None:
    repo = json.loads((ROOT / "mgu-repo.json").read_text())
    listed = {t["id"]: ROOT / t["path"] for t in repo.get("tools", [])}
    for comp_path in list((ROOT / "native").glob("*/component.json")) + list(
        (ROOT / "tools").glob("*/component.json")
    ):
        comp = json.loads(comp_path.read_text(encoding="utf-8"))
        cid = comp.get("id") or comp_path.parent.name
        if BANNED_IDS.search(cid):
            errs.append(f"{cid}: идентификатор wireproxy/wireguard запрещён (CONSTRAINTS)")
        base = comp_path.parent

        if comp.get("internet"):
            uids = comp.get("uids")
            if uids is None:
                errs.append(f"{cid}: internet:true без uids / state/internet-uids")

        unit_names = {u.get("name", "").replace(".service", "") for u in comp.get("units") or []}
        unit_names.discard("")
        for rn in comp.get("recmgr") or []:
            if rn not in unit_names and f"{rn}.service" not in {u.get("name") for u in comp.get("units") or []}:
                if rn not in unit_names:
                    errs.append(f"{cid}: recmgr {rn!r} не совпадает с units[].name")
        for ent in comp.get("files") or []:
            rel = ent.get("from") or ent.get("path")
            if isinstance(rel, str) and "/vendor/" in rel.replace("\\", "/"):
                src = base / rel
                if not src.is_file():
                    errs.append(f"{cid}: vendor path missing {rel}")

        for u in comp.get("units") or []:
            rel = u.get("from")
            name = u.get("name")
            if not rel or not name:
                continue
            unit_file = base / rel
            if not unit_file.is_file():
                errs.append(f"{cid}: unit file missing {rel}")
                continue
            text = unit_file.read_text(encoding="utf-8", errors="replace")
            internet_uids: set[str] = set()
            if comp.get("internet"):
                raw = comp.get("uids")
                if isinstance(raw, list):
                    internet_uids = {str(x) for x in raw}
            for m in USER_UID.finditer(text):
                uid = m.group(1)
                if uid in internet_uids:
                    errs.append(
                        f"{cid} {name}: User={uid} — на ГУ нет passwd; используй runas/setuid-chelper"
                    )
            non_comment = "\n".join(
                ln for ln in text.splitlines() if not ln.lstrip().startswith("#")
            )
            if BANNED_IDS.search(non_comment):
                errs.append(f"{cid} {name}: wireproxy/wireguard в unit (не Xray)")


def check_shrinkwrap(errs: list[str]) -> None:
    for pkg in (ROOT / "apps").glob("*/package/package.json"):
        pkg_data = json.loads(pkg.read_text(encoding="utf-8"))
        sw = pkg.parent / "npm-shrinkwrap.json"
        if not sw.is_file():
            errs.append(f"{pkg.parent.parent.name}: нет npm-shrinkwrap.json (oap_pack)")
            continue
        sw_data = json.loads(sw.read_text(encoding="utf-8"))
        if sw_data.get("version") != pkg_data.get("version"):
            errs.append(
                f"{pkg.parent.parent.name}: shrinkwrap {sw_data.get('version')} "
                f"!= package.json {pkg_data.get('version')}"
            )


def check_kit_single_quote(errs: list[str]) -> None:
    for js in git_tracked_under("apps/", "apps/"):
        if js.suffix != ".js":
            continue
        try:
            text = js.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        in_block = False
        for line in text.splitlines():
            s = line.strip()
            if "/*" in line and "*/" not in line:
                in_block = True
            if in_block:
                if "*/" in line:
                    in_block = False
                continue
            if s.startswith("*"):
                continue
            chunk = strip_line_comment(line)
            if KIT_SQ.search(chunk):
                errs.append(
                    f"{js.relative_to(ROOT)}: require('./kit/...') с одинарными кавычками "
                    f"(oap_link на ГУ — только double quotes для ./kit/)"
                )
                break


def check_no_wireproxy_artifacts(errs: list[str]) -> None:
    proc = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    for line in proc.stdout.splitlines():
        low = line.lower()
        if "wireproxy" in low or "wireguard" in low:
            if low.startswith("docs/") or low.endswith(".md"):
                continue
            errs.append(f"tracked file запрещённого стека: {line}")


def main() -> int:
    errs: list[str] = []
    warns: list[str] = []
    check_prebuilt_elf(errs)
    check_component_architecture(errs, warns)
    check_shrinkwrap(errs)
    check_kit_single_quote(errs)
    check_no_wireproxy_artifacts(errs)

    if warns:
        print("WARN:")
        for w in warns:
            print(f"  ⚠ {w}")
    if errs:
        print("audit-mgu-architecture FAIL:")
        for e in errs:
            print(f"  ✗ {e}")
        return 1
    print("audit-mgu-architecture OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())