#!/bin/sh
# SPDX-License-Identifier: MIT
# Сброс привилегий от root (отладка). Служба: User=3922 в krikun-xray.service.
set -eu
u=${1:-}
shift || true
[ -n "$u" ] && [ -n "${1:-}" ] || {
	echo "usage: krikun-runas <uid> <cmd> [args...]" >&2
	exit 1
}
[ "$(id -u)" -eq 0 ] || {
	echo "krikun-runas: только от root (или USE: systemctl)" >&2
	exit 1
}
if command -v runuser >/dev/null 2>&1; then
	exec runuser -u "#$u" -- "$@"
fi
if command -v su >/dev/null 2>&1; then
	exec su -s /bin/sh "#$u" -c 'exec "$@"' -- "$@"
fi
echo "krikun-runas: нет runuser/su" >&2
exit 1