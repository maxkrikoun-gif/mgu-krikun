#!/usr/bin/env python3
"""systemd unit'ы: несовместимости с runas, битые After=, пути ExecStart vs component.json."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNAS = re.compile(r"runas|setuid", re.I)
NOPRIV = re.compile(r"^NoNewPrivileges\s*=\s*yes\b", re.M | re.I)


def tools_with_units() -> list[tuple[str, Path, dict]]:
    out: list[tuple[str, Path, dict]] = []
    repo = json.loads((ROOT / "mgu-repo.json").read_text())
    for t in repo.get("tools", []):
        comp = json.loads((ROOT / t["path"] / "component.json").read_text())
        base = ROOT / t["path"]
        for u in comp.get("units") or []:
            name = u.get("name") or u.get("unit")
            rel = u.get("from")
            if name and rel:
                out.append((t["id"], base / rel, comp))
    return out


def main() -> int:
    errs: list[str] = []
    warns: list[str] = []

    for tid, unit_path, comp in tools_with_units():
        if not unit_path.is_file():
            errs.append(f"{tid}: нет unit {unit_path.relative_to(ROOT)}")
            continue
        text = unit_path.read_text(encoding="utf-8")
        if NOPRIV.search(text) and (RUNAS.search(text) or "krikun-runas" in text):
            errs.append(
                f"{tid} {unit_path.name}: NoNewPrivileges=yes + runas/setuid → drop priv на ГУ (activating)"
            )
        for line in text.splitlines():
            if line.strip().startswith("After=") and "jap-node22.service" in line:
                warns.append(f"{tid}: After=jap-node22.service — у jap-node22 нет unit (гармless)")
            if "MemoryLimit=" in line and "128M" in line:
                warns.append(f"{tid}: MemoryLimit=128M — тяжёлые бинарники могут OOM")

        installed = {ent["path"] for ent in comp.get("files") or []}
        for m in re.finditer(r"ExecStart(?:Pre)?=.*(/var/opt/\S+/current/(\S+))", text):
            full, base = m.group(1), m.group(2).split()[0].rstrip("'\"")
            # only check paths under this tool's /current/
            if f"/var/opt/{tid}/" in full and base not in installed and base not in ("start.sh", "setup.sh"):
                if not any(base in p for p in installed):
                    errs.append(f"{tid}: ExecStart ссылается на {base}, нет в component files[]")

    # sh -n все check.sh
    for comp_path in ROOT.glob("**/component.json"):
        comp = json.loads(comp_path.read_text())
        for chk in comp.get("check") or []:
            sh = comp_path.parent / chk
            if not sh.is_file():
                errs.append(f"{comp.get('id')}: check {chk} missing")
                continue
            r = subprocess.run(["sh", "-n", str(sh)], capture_output=True, text=True)
            if r.returncode:
                errs.append(f"{comp.get('id')}: sh -n {chk}: {r.stderr.strip()}")

    if warns:
        print("WARN:")
        for w in warns:
            print(f"  ⚠ {w}")
    if errs:
        print("audit-systemd FAIL:")
        for e in errs:
            print(f"  ✗ {e}")
        return 1
    print(f"audit-systemd OK ({len(list(tools_with_units()))} units)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())