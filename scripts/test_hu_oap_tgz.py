#!/usr/bin/env python3
"""Проверка pack-staged-app.js: в корне OAP tgz обязан быть package.json (как validateArtifact на ГУ)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HU_ERR = "no package.json"  # built-<id>@<ver>.tgz: no package.json (mgu-updater / mgu-deploy)


def main() -> int:
    errs: list[str] = []
    repo = json.loads((ROOT / "mgu-repo.json").read_text(encoding="utf-8"))
    for c in repo.get("components", []):
        if c.get("kind") != "app":
            continue
        b = c.get("build")
        if not (isinstance(b, dict) and b.get("node") == "scripts/pack-staged-app.js"):
            continue
        rel = c["path"]
        app_dir = ROOT / rel
        if not (app_dir / "app.json").is_file():
            errs.append(f"{c['id']}: нет {rel}/app.json")
            continue
        with tempfile.TemporaryDirectory(prefix="hu-oap-tgz-") as td:
            out_dir = Path(td)
            r = subprocess.run(
                ["node", str(ROOT / "scripts" / "pack-staged-app.js"), rel],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            if r.returncode:
                msg = (r.stderr or r.stdout or "pack-staged failed").strip().splitlines()[-1]
                errs.append(f"{c['id']}: {msg}")
                continue
            spec = json.loads((app_dir / "app.json").read_text(encoding="utf-8"))
            name = f"{spec['id']}@{spec['version']}.tgz"
            tgz = app_dir / name
            if not tgz.is_file():
                errs.append(f"{c['id']}: нет {name} после pack-staged")
                continue
            lst = subprocess.run(
                ["tar", "tzf", str(tgz)],
                capture_output=True,
                text=True,
                check=True,
            )
            roots = {line.split("/", 1)[0] for line in lst.stdout.splitlines() if line}
            if "package.json" not in roots:
                errs.append(f"built-{name}: {HU_ERR}")
            else:
                print(f"OK pack-staged {c['id']}")
    if errs:
        print("HU_OAP_TGZ FAIL:\n" + "\n".join(f"  ✗ {e}" for e in errs))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())