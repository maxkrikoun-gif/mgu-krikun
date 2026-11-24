#!/usr/bin/env python3
"""Дописывает package.json → files[] для oap_pack (обязательно на ГУ после oap_link)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Как в idrive7-apps: перечисление каталогов/файлов дерева OAP (oap_pack.js members).
DEFAULT = (
    "package.json",
    "config",
    "javascript",
    "manifest.json",
    "npm-shrinkwrap.json",
    "permissions.json",
    "rhmiData",
)


def main() -> int:
    app_id = sys.argv[1] if len(sys.argv) > 1 else None
    apps = [ROOT / "apps" / app_id] if app_id else sorted((ROOT / "apps").glob("*"))
    changed = 0
    for app_dir in apps:
        pkg = app_dir / "package" / "package.json"
        if not pkg.is_file() or not (app_dir / "mgu-app.json").is_file():
            continue
        data = json.loads(pkg.read_text(encoding="utf-8"))
        if isinstance(data.get("files"), list) and data["files"]:
            continue
        files = []
        base = pkg.parent
        for name in DEFAULT:
            p = base / name
            if p.exists():
                files.append(name)
        if (base / "LICENSE.kit").is_file():
            files.append("LICENSE.kit")
        if not files:
            print(f"SKIP {app_dir.name}: пустой package/", file=sys.stderr)
            continue
        data["files"] = files
        pkg.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"OK {app_dir.name}: files[] ({len(files)} entries)")
        changed += 1
    return 0 if changed else 1


if __name__ == "__main__":
    raise SystemExit(main())