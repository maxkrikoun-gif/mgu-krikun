#!/bin/sh
# SPDX-License-Identifier: MIT
# Uid 3922: только запуск Xray по /var/opt/krikun-xray/conf/config.json (импорт делает root в setup.sh)
set -u
D=${KRIKUN_XRAY_CONF:-/var/opt/krikun-xray/conf}
R=/run/krikun-xray/s
BIN=${KRIKUN_XRAY_BIN:-/var/opt/krikun-xray/current/xray}
CFG=$D/config.json
ST=$R/state
TICK=${KRIKUN_XRAY_TICK:-5}
child=
said=

say() {
	[ "$1" = "$said" ] || { echo "$1"; printf '%s\n' "$1" >"$ST"; said=$1; }
}
stopchild() { [ -n "$child" ] && kill "$child" 2>/dev/null && wait "$child" 2>/dev/null; child=; }
trap 'stopchild; exit 0' TERM INT

loop() {
	if [ ! -f "$CFG" ]; then
		say "idle: нет config.json — USB KRIKUN/xray.json (перезапуск службы) или incoming/xray.json"
		stopchild
		sleep "$TICK"
		return
	fi
	[ -r "$CFG" ] || { say "idle: нет прав на $CFG"; stopchild; sleep "$TICK"; return; }
	if [ -z "$child" ]; then
		"$BIN" run -c "$CFG" &
		child=$!
		say "running: SOCKS 127.0.0.1:1080 (конфиг на ГУ)"
	fi
	if ! kill -0 "$child" 2>/dev/null; then
		wait "$child" 2>/dev/null || true
		child=
		say "stopped: xray завершился, перезапуск через ${TICK}s"
	fi
	sleep "$TICK"
}

mkdir -p "$R"
umask 077
while :; do loop; done