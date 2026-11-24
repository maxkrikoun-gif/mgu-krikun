#!/usr/bin/env python3
"""Скопировать dist/<id>/source + rhmiData → apps/<id>/package/ для unit в Store."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
APPS = ROOT / "apps"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("app_id", nargs="+")
    ap.add_argument(
        "--strip-locale-suffix",
        action="store_true",
        help="package.json version: убрать -ru.1 / -zh-CN.N (mgu-app только x.y.z)",
    )
    args = ap.parse_args()
    for app_id in args.app_id:
        src = DIST / app_id / "source"
        rh = DIST / app_id / "rhmiData"
        if not src.is_dir():
            print(f"SKIP {app_id}: нет {src} — сначала kit/tools/build.py", file=sys.stderr)
            continue
        dest = APPS / app_id / "package"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        if rh.is_dir():
            out_rh = dest / "rhmiData"
            if out_rh.exists():
                shutil.rmtree(out_rh)
            shutil.copytree(rh, out_rh)
        pkg = dest / "package.json"
        if args.strip_locale_suffix and pkg.is_file():
            data = json.loads(pkg.read_text(encoding="utf-8"))
            ver = str(data.get("version", ""))
            if "-" in ver:
                base = ver.split("-", 1)[0]
                data["version"] = base
                pkg.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        app_json = APPS / app_id / "app.json"
        ver = json.loads(app_json.read_text(encoding="utf-8")).get("version", "?")
        print(f"OK {app_id} → {dest} (app.json version {ver})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())