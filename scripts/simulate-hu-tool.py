#!/usr/bin/env python3
"""
Симуляция mgu-deploy: component.json → /var/opt/<id>/current/<path>.
Ловит LFS-pointer вместо ELF, отсутствующие from=, пустой jap-node22 после assemble.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LFS = re.compile(rb"^version https://git-lfs\.github\.com/spec/v1", re.MULTILINE)
ELF = b"\x7fELF"


def tool_dirs() -> list[Path]:
    repo = json.loads((ROOT / "mgu-repo.json").read_text())
    out = []
    for t in repo.get("tools", []):
        out.append(ROOT / t["path"])
    return out


def parse_lfs_pointer(data: bytes) -> tuple[int | None, str | None]:
    lines = data.decode("utf-8", errors="replace").splitlines()
    size = None
    err = None
    for i, line in enumerate(lines[:5], 1):
        if i == 3 and line.startswith("size "):
            try:
                size = int(line.split()[1])
            except (IndexError, ValueError):
                err = f"line 3: invalid size line {line!r}"
        if i == 3 and not line.startswith("size ") and data.startswith(b"version https://git-lfs"):
            err = err or "line 3 size not found (LFS pointer битый или обрезанный)"
    return size, err


def simulate_tool(tool_dir: Path) -> list[str]:
    comp_path = tool_dir / "component.json"
    if not comp_path.is_file():
        return []
    errs: list[str] = []
    comp = json.loads(comp_path.read_text())
    cid = comp.get("id", tool_dir.name)
    stage = Path(f"/tmp/sim-hu-{cid}")
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    current = stage / "current"
    current.mkdir()

    for ent in comp.get("files") or []:
        rel = ent.get("from") or ent.get("path")
        dest_name = ent.get("path")
        if not rel or not dest_name:
            errs.append(f"{cid}: bad files[] entry {ent}")
            continue
        src = tool_dir / rel
        if ".." in Path(rel).parts:
            errs.append(f"{cid}: from {rel!r} вне каталога tool")
            continue
        if not src.is_file():
            errs.append(f"{cid}: нет {src.relative_to(ROOT)}")
            continue
        dest = current / dest_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    for rel in comp.get("check") or []:
        check = current / rel
        if not check.is_file():
            errs.append(f"{cid}: check {rel} not staged")
            continue
        # ELF / LFS on anything named node or *.part
        for f in current.rglob("*"):
            if not f.is_file():
                continue
            head = f.read_bytes()[:256]
            if LFS.search(head):
                lfs_size, lfs_err = parse_lfs_pointer(f.read_bytes()[:512])
                errs.append(
                    f"{cid}: {f.relative_to(current)} — LFS pointer "
                    f"({lfs_err or f'ожидали size {lfs_size}'}) → на ГУ check/upstream упадёт"
                )

    if cid == "jap-node22":
        node_path = current / "bin" / "node"
        parts = list(current.glob("node.part.*"))
        if parts and (not node_path.is_file() or node_path.stat().st_size < 50_000_000):
            asm = current / "assemble.sh"
            if asm.is_file():
                r = subprocess.run(
                    ["/bin/sh", str(asm)],
                    cwd=current,
                    capture_output=True,
                    text=True,
                )
                if r.returncode:
                    errs.append(f"jap-node22: assemble.sh failed: {r.stderr.strip() or r.stdout}")
        if node_path.is_file():
            head = node_path.read_bytes()[:4]
            if head != ELF:
                errs.append(f"jap-node22: bin/node не ELF после assemble (первые байты {head!r})")
            elif node_path.stat().st_size < 50_000_000:
                errs.append(f"jap-node22: bin/node слишком мал ({node_path.stat().st_size} B)")
        elif not parts:
            errs.append(f"jap-node22: нет node.part.* и нет bin/node")

    return errs


def main() -> int:
    all_errs: list[str] = []
    for td in tool_dirs():
        all_errs.extend(simulate_tool(td))
    if all_errs:
        print("simulate-hu-tool FAIL:\n" + "\n".join(f"  ✗ {e}" for e in all_errs))
        return 1
    print(f"simulate-hu-tool OK: {len(tool_dirs())} tools")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())