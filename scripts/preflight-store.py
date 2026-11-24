#!/usr/bin/env python3
"""Полный preflight каталога maxkrikoun-gif/mgu-krikun (как перед установкой на ГУ)."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQ_JS = re.compile(r"""require\s*\(\s*['"](\./[^'"]+)['"]\s*\)""")


def fail(errs: list[str]) -> None:
    print("PREFLIGHT FAIL:\n" + "\n".join(f"  ✗ {e}" for e in errs))
    sys.exit(1)


def main() -> int:
    errs: list[str] = []
    warns: list[str] = []

    for script in ("validate-mgu-app.py", "validate-component-json.py", "simulate-hu-tool.py"):
        p = subprocess.run([sys.executable, str(ROOT / "scripts" / script)], capture_output=True, text=True)
        print(p.stdout, end="")
        if p.returncode:
            errs.append(f"{script} failed")
            if p.stdout:
                errs.extend("  " + line for line in p.stdout.splitlines() if "FAIL" in line or "✗" in line)

    repo = json.loads((ROOT / "mgu-repo.json").read_text())
    listed: dict[str, str] = {}
    for c in repo.get("components", []):
        listed[c["id"]] = c["path"]
    for t in repo.get("tools", []):
        listed[t["id"]] = t["path"]

    # versions + icons
    for cid, rel in sorted(listed.items()):
        base = ROOT / rel
        if not base.is_dir():
            errs.append(f"{cid}: path {rel} missing")
            continue
        if (base / "icon.png").is_file() or (base / "component.json").is_file():
            pass
        elif c_app := base / "app.json":
            if c_app.is_file() and not (base / "icon.png").is_file():
                errs.append(f"{cid}: no icon.png in {rel}")

        if (base / "component.json").is_file():
            comp = json.loads((base / "component.json").read_text())
            if comp.get("id") != cid:
                errs.append(f"{cid}: component id {comp.get('id')}")
            ver = comp.get("version")
            if not comp.get("check"):
                warns.append(f"{cid}: component.json без check[]")
            if comp.get("kind") == "tool" and "units" not in comp and not comp.get("units"):
                if cid != "jap-node22":
                    warns.append(f"{cid}: tool без units (демон не стартует?)")
        if (base / "app.json").is_file():
            app = json.loads((base / "app.json").read_text())
            if app.get("id") != cid:
                errs.append(f"{cid}: app.json id {app.get('id')}")
            for dep, need in (app.get("requires") or {}).items():
                if dep in listed:
                    comp = json.loads((ROOT / listed[dep] / "component.json").read_text())
                    have = str(comp.get("version", ""))
                    if have and have != str(need):
                        warns.append(f"{cid} requires {dep}@{need}, repo has @{have}")
                elif dep not in (
                    "mgu-render",
                    "mgu-inputgate",
                    "mgu-deploy",
                    "mgu-python",
                    "mgu-updater",
                    "idrive7-renderd",
                ):
                    warns.append(f"{cid}: requires {dep} (не в mgu-repo — нужен другой Store-источник)")

    # mgu-app module graph (bundled requires)
    for mf in (ROOT / "apps").glob("*/mgu-app.json"):
        m = json.loads(mf.read_text())
        app_dir = mf.parent
        base_names = {Path(f).name.replace(".js", "") for f in m.get("modules", [])}
        for f in m.get("modules", []):
            if "/kit/" in f.replace("\\", "/"):
                continue  # kit/*.js грузят соседей с диска, не в bundle
            text = (app_dir / f).read_text(encoding="utf-8", errors="replace")
            for r in REQ_JS.findall(text):
                if r.startswith("./kit/"):
                    continue
                dep = Path(r).name.replace(".js", "")
                if dep not in base_names:
                    errs.append(f"{mf.parent.name}: {Path(f).name} requires {r}, нет в modules[]")

    parts = sorted((ROOT / "tools/jap-node22/prebuilt").glob("node.part.*"))
    node = ROOT / "tools/jap-node22/prebuilt/node"
    if parts:
        total = sum(p.stat().st_size for p in parts)
        if total < 50_000_000:
            errs.append(f"jap-node22: node.part.* слишком малы ({total} bytes)")
    elif node.is_file():
        if node.stat().st_size < 50_000_000:
            head = node.read_bytes()[:40]
            if b"git-lfs" in head:
                errs.append("jap-node22: prebuilt/node — LFS pointer (нужны node.part.* в git)")
            else:
                errs.append(f"jap-node22 prebuilt/node слишком маленький")
    else:
        errs.append("jap-node22: нет node.part.* и нет prebuilt/node")

    for app in repo.get("components", []):
        if app.get("build") != "unit":
            continue
        oap = ROOT / app["path"] / "package" / "node_modules" / "oap-sdk"
        if oap.exists():
            errs.append(f"{app['id']}: package/node_modules/oap-sdk — убери (unit, donor на ГУ)")

    if warns:
        print("WARN:\n" + "\n".join(f"  ⚠ {w}" for w in warns))
    if errs:
        fail(errs)
    print("PREFLIGHT OK (см. WARN — внешние зависимости Store)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())