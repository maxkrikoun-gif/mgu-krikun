#!/usr/bin/env python3
"""component.json: файлы from= только внутри каталога tool (Store качает один path/)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate(tool_dir: Path) -> list[str]:
    comp = tool_dir / "component.json"
    if not comp.is_file():
        return []
    cid = tool_dir.name
    data = json.loads(comp.read_text(encoding="utf-8"))
    errs: list[str] = []
    for ent in data.get("files") or []:
        if not isinstance(ent, dict):
            continue
        rel = ent.get("from") or ent.get("path")
        if not isinstance(rel, str):
            continue
        if ".." in Path(rel).parts:
            p = (tool_dir / rel).resolve()
            try:
                p.relative_to(tool_dir.resolve())
            except ValueError:
                errs.append(f"{cid}: from {rel!r} вне {tool_dir.name}/ (Store не видит kit/, licenses/…)")
                continue
        src = tool_dir / rel
        if not src.is_file():
            errs.append(f"{cid}: нет файла {rel}")
    return errs


def main() -> int:
    tools = list((ROOT / "native").glob("*/component.json")) + list(
        (ROOT / "tools").glob("*/component.json")
    )
    all_errs: list[str] = []
    for comp in tools:
        all_errs.extend(validate(comp.parent))
    if all_errs:
        print("FAIL component.json:\n" + "\n".join(f"  - {e}" for e in all_errs))
        return 1
    print(f"OK: {len(tools)} component.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())