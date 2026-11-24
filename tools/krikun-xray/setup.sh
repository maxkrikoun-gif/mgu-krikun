#!/bin/sh
# SPDX-License-Identifier: MIT
# root (ExecStartPre): conf/, /run/krikun-xray/s для uid 3922 (systemd 237). s/ — 0755: статус читает OAP krikun_seti (не 0700 как у jap-wireproxy с ключом).
set -eu
DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
U=3922
C=/var/opt/krikun-xray/conf
R=/run/krikun-xray/s
for d in "$C" "$R"; do
	[ -L "$d" ] && { echo "setup.sh: $d is a link" >&2; exit 1; }
done
mkdir -p "$C" "$R" /run/krikun-xray/requests /run/krikun-xray/responses
chown root:"$U" "$C"
chmod 0750 "$C"
chown "$U":"$U" "$R"
chmod 0755 "$R"
chmod 1777 /run/krikun-xray/requests /run/krikun-xray/responses 2>/dev/null || true
sh "$DIR/import-config.sh"