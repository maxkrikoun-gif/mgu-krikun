#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
F=/var/opt/mgu-updater/updater.local.conf
[ -f "$F" ] || exit 0
sed -i.bak '/^proxy =/d' "$F" 2>/dev/null || sed -i '' '/^proxy =/d' "$F"
echo "proxy отключён в $F"