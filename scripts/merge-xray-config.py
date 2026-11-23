#!/usr/bin/env python3
"""Слить экспорт Amnezia (outbound) с локальным SOCKS inbound. Секреты только в выходной файл — не коммитить."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEMPLATE = REPO / "config/examples/xray-config.json.example"

SOCKS_INBOUND = {
    "tag": "socks-in",
    "protocol": "socks",
    "listen": "127.0.0.1",
    "port": 1080,
    "settings": {"udp": True},
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Amnezia Xray JSON → полный config для ГУ")
    ap.add_argument("amnezia", type=Path, help="файл экспорта из Amnezia")
    ap.add_argument("-o", "--output", type=Path, required=True, help="куда писать (вне git)")
    args = ap.parse_args()
    data = json.loads(args.amnezia.read_text(encoding="utf-8"))
    if "outbounds" not in data and "outbound" in data:
        data["outbounds"] = [data.pop("outbound")]
    if "inbounds" not in data:
        data["inbounds"] = []
    tags = {i.get("tag") for i in data["inbounds"]}
    if "socks-in" not in tags:
        data["inbounds"].append(SOCKS_INBOUND)
    if "routing" not in data:
        data["routing"] = {
            "domainStrategy": "AsIs",
            "rules": [{"type": "field", "inboundTag": ["socks-in"], "outboundTag": data["outbounds"][0].get("tag", "proxy")}],
        }
    out = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    args.output.write_text(out, encoding="utf-8")
    print(f"OK: {args.output} ({len(out)} bytes)")
    print("USB: скопируйте на флешку как KRIKUN/xray.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())