#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
D=/var/opt/krikun-xray/conf
CFG=$D/config.json
if [ ! -f "$CFG" ]; then
	echo "krikun-xray: нет конфигурации ($CFG)"
	exit 1
fi
if ! grep -q '"127.0.0.1"' "$CFG" && ! grep -q '127.0.0.1' "$CFG"; then
	echo "krikun-xray: в конфиге должен быть inbound на 127.0.0.1"
	exit 1
fi
echo "krikun-xray: конфиг найден"
exit 0