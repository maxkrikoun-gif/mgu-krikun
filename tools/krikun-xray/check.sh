#!/bin/sh
# SPDX-License-Identifier: MIT
# mgu-deploy check: бинарники OK; config — желателен для SOCKS, без него idle допустим.
set -eu
D="${MGU_TOOL_CURRENT:-/var/opt/krikun-xray/current}"
CFG="${MGU_TOOL_CONF:-/var/opt/krikun-xray/conf/config.json}"
[ -x "$D/xray" ] || { echo "krikun-xray: нет $D/xray"; exit 1; }
[ -x "$D/krikun-runas" ] || { echo "krikun-xray: нет $D/krikun-runas"; exit 1; }
case "$(file -b "$D/krikun-runas" 2>/dev/null || true)" in
*ELF*x86-64*) ;;
*) echo "krikun-xray: krikun-runas не ELF linux-amd64"; exit 1 ;;
esac
case "$(file -b "$D/xray" 2>/dev/null || true)" in
*ELF*x86-64*) ;;
*) echo "krikun-xray: xray не ELF linux-amd64"; exit 1 ;;
esac
if [ ! -f "$CFG" ]; then
	echo "krikun-xray: конфиг пока нет ($CFG) — idle до USB KRIKUN/xray.json или «Krikun: сеть»"
	exit 0
fi
if ! grep -q '127.0.0.1' "$CFG"; then
	echo "krikun-xray: в конфиге должен быть inbound на 127.0.0.1"
	exit 1
fi
echo "krikun-xray: конфиг найден"
exit 0