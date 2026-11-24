#!/usr/bin/env python3
"""Локально вызывает oap_pack.pack() как на ГУ после oap_link (нужен Node + donor не требуется)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def unpack_oap_pack() -> Path:
    stub = Path("/tmp/mdep/files/oap_pack.js")
    if stub.is_file():
        return stub.parent
    cache = ROOT / ".cache" / "artifacts" / "mgu-deploy@0.8.29.tgz"
    if not cache.is_file():
        raise SystemExit("нет .cache/artifacts/mgu-deploy@*.tgz — скачай donor mgu-deploy")
    td = Path(tempfile.mkdtemp(prefix="mdep-"))
    subprocess.run(
        ["tar", "-xzf", str(cache), "-C", str(td)],
        check=True,
        capture_output=True,
    )
    inner = next(td.glob("**/oap_pack.js"), None)
    if not inner:
        raise SystemExit("в tgz нет oap_pack.js")
    return inner.parent


def main() -> int:
    oap_dir = unpack_oap_pack()
    errs: list[str] = []
    for mf in sorted((ROOT / "apps").glob("*/mgu-app.json")):
        pkg = mf.parent / "package"
        pj = pkg / "package.json"
        if not pj.is_file():
            continue
        data = json.loads(pj.read_text(encoding="utf-8"))
        if not data.get("files"):
            errs.append(f"{mf.parent.name}: нет files[]")
            continue
        out = Path(tempfile.mktemp(suffix=".tgz"))
        node = f"""
const {{pack}} = require({json.dumps(str(oap_dir / "oap_pack.js"))});
pack({json.dumps(str(pkg))}, {json.dumps(str(out))});
"""
        r = subprocess.run(["node", "-e", node], capture_output=True, text=True)
        out.unlink(missing_ok=True)
        if r.returncode:
            msg = (r.stderr or r.stdout or "pack failed").strip().splitlines()[-1]
            errs.append(f"{mf.parent.name}: {msg}")
        else:
            print(f"OK oap_pack {mf.parent.name}")
    if errs:
        print("OAP_PACK FAIL:\n" + "\n".join(f"  ✗ {e}" for e in errs))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())