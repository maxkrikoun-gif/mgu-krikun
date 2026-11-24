#!/usr/bin/env python3
"""Прогон check.sh в mock /var/opt/.../current (без ГУ)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def stage_tool(tool_dir: Path, comp: dict, mock_opt: Path) -> Path:
    tid = comp["id"]
    cur = mock_opt / tid / "current"
    cur.mkdir(parents=True)
    conf = mock_opt / tid / "conf"
    conf.mkdir(parents=True)
    for ent in comp.get("files") or []:
        src = tool_dir / ent["from"]
        dst = cur / ent["path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        mode = int(ent.get("mode", "0644"), 8)
        dst.chmod(mode & 0o777)
    return cur


def main() -> int:
    errs: list[str] = []
    repo = json.loads((ROOT / "mgu-repo.json").read_text())
    with tempfile.TemporaryDirectory() as td:
        mock = Path(td) / "var" / "opt"
        for t in repo.get("tools", []):
            tool_dir = ROOT / t["path"]
            comp = json.loads((tool_dir / "component.json").read_text())
            cur = stage_tool(tool_dir, comp, mock)
            conf_dir = mock / comp["id"] / "conf"
            for chk in comp.get("check") or []:
                script = cur / chk
                if comp["id"] == "jap-node22":
                    subprocess.run(["/bin/sh", str(cur / "assemble.sh")], cwd=cur, check=True)
                    r = subprocess.run(["/bin/sh", "-n", str(script)], capture_output=True, text=True)
                    if r.returncode:
                        errs.append(f"jap-node22: sh -n check.sh: {r.stderr}")
                    continue
                if comp["id"] in ("jap-ridetube-d", "jap-filmix-d"):
                    r = subprocess.run(["/bin/sh", "-n", str(script)], capture_output=True, text=True)
                    if r.returncode:
                        errs.append(f"{comp['id']}: sh -n {chk}: {r.stderr.strip()}")
                    continue
                env = {
                    **os.environ,
                    "MGU_NODE": "/bin/false",
                    "MGU_TOOL_CURRENT": str(cur),
                    "MGU_TOOL_CONF": str(conf_dir / "config.json"),
                }
                r = subprocess.run(
                    ["/bin/sh", str(script)],
                    cwd=cur,
                    env=env,
                    capture_output=True,
                    text=True,
                )
                if r.returncode != 0:
                    errs.append(
                        f"{comp['id']} check FAIL ({r.returncode}): {r.stderr.strip() or r.stdout.strip()}"
                    )
    if errs:
        print("audit-checks-mock FAIL:")
        for e in errs:
            print(f"  ✗ {e}")
        return 1
    print("audit-checks-mock OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())