#!/bin/sh
# SPDX-License-Identifier: MIT
# Root activate helper: включить proxy для Store/RideTube
set -eu
F=/var/opt/mgu-updater/updater.local.conf
LINE='proxy = socks5://127.0.0.1:1080'
mkdir -p /var/opt/mgu-updater
if [ -f "$F" ] && grep -q '^proxy' "$F"; then
	sed -i.bak "s|^proxy.*|$LINE|" "$F" 2>/dev/null || sed -i '' "s|^proxy.*|$LINE|" "$F"
else
	printf '%s\n' "$LINE" >>"$F"
fi
echo "proxy включён: $LINE"