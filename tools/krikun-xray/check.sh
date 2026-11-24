#!/bin/sh
# SPDX-License-Identifier: MIT
# mgu-deploy check: без file(1) на Yocto; на dev-машине linux ELF не исполняется — fallback по magic.
set -eu
D="${MGU_TOOL_CURRENT:-/var/opt/krikun-xray/current}"
CFG="${MGU_TOOL_CONF:-/var/opt/krikun-xray/conf/config.json}"

elf_magic_ok() {
	# первые 4 байта: 7f ELF
	[ -f "$1" ] || return 1
	m=$(dd if="$1" bs=1 count=4 2>/dev/null | LC_ALL=C od -An -t x1 | tr -d ' \n')
	[ "$m" = "7f454c46" ]
}

probe_xray() {
	if "$D/xray" version >/dev/null 2>&1; then
		return 0
	fi
	elf_magic_ok "$D/xray"
}

probe_runas() {
	rc=0
	"$D/krikun-runas" 2>/dev/null || rc=$?
	if [ "$rc" -eq 2 ]; then
		return 0
	fi
	elf_magic_ok "$D/krikun-runas"
}

[ -x "$D/xray" ] || { echo "krikun-xray: нет $D/xray"; exit 1; }
[ -x "$D/krikun-runas" ] || { echo "krikun-xray: нет $D/krikun-runas"; exit 1; }
if ! probe_xray; then
	echo "krikun-xray: xray не linux-amd64 ELF"
	exit 1
fi
if ! probe_runas; then
	echo "krikun-xray: krikun-runas не linux-amd64 ELF"
	exit 1
fi
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