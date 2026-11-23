#!/bin/sh
# SPDX-License-Identifier: MIT
# Root: импорт, удаление, запуск/остановка (вызывается из request-processor.sh)
set -eu
D=/var/opt/krikun-xray/conf
CFG="$D/config.json"
G=3922
SVC=krikun-xray.service
CTL_SVC=krikun-xray-ctl.service
TOOL_DIR=/var/opt/krikun-xray/current
SOCKS=socks5h://127.0.0.1:1080
IPIFY=https://api.ipify.org
IPIFY_HTTP=http://api.ipify.org
CANCEL_FLAG=/run/krikun-xray/cancel-connectivity-test
TEST_PROGRESS=/run/krikun-xray/connectivity-test.progress

# shellcheck disable=SC2059
json_str() {
	# экранирование для JSON-строки
	printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

test_cancelled() {
	[ -f "$CANCEL_FLAG" ]
}

progress_ping() {
	host=$1
	n=$2
	mkdir -p /run/krikun-xray 2>/dev/null || true
	printf 'ping %s: пакет %s/3\n' "$host" "$n" >"$TEST_PROGRESS" 2>/dev/null || true
}

ping_check() {
	host=$1
	if ! command -v ping >/dev/null 2>&1; then
		printf '%s\n%s' "false" "ping: нет утилиты"
		return 1
	fi
	tmp=/tmp/krikun-ping.$$
	: >"$tmp"
	ok=false
	i=1
	while [ "$i" -le 3 ]; do
		if test_cancelled; then
			rm -f "$tmp"
			printf '%s\n%s' "cancelled" "остановлено ($host, пакет $i/3)"
			return 2
		fi
		progress_ping "$host" "$i"
		if ping -c 1 -W 5 "$host" >>"$tmp" 2>&1; then
			ok=true
		fi
		i=$((i + 1))
	done
	detail=$(tail -n 2 "$tmp" | tr '\n' ' ' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
	rm -f "$tmp"
	[ -n "$detail" ] || detail="нет ответа"
	printf '%s\n%s' "$ok" "$detail"
	return 0
}

emit_connectivity_json() {
	cancelled=$1
	g_ok=$2
	g_detail=$3
	y_ok=$4
	y_detail=$5
	ext_ip=$6
	ip_via=$7
	proxy_up=$8
	gd=$(json_str "$g_detail")
	yd=$(json_str "$y_detail")
	ev=$(json_str "$ip_via")
	ei=$(json_str "$ext_ip")
	if [ "$cancelled" -eq 1 ]; then
		printf '{"ok":false,"cancelled":true,"op":"connectivity_test",'
	else
		printf '{"ok":true,"op":"connectivity_test",'
	fi
	printf '"ping_google":{"ok":%s,"host":"google.com","detail":"%s"},' "$g_ok" "$gd"
	printf '"ping_youtube":{"ok":%s,"host":"youtube.com","detail":"%s"},' "$y_ok" "$yd"
	printf '"external_ip":"%s","ip_via":"%s","xray_active":%s}\n' "$ei" "$ev" \
		"$([ "$proxy_up" -eq 1 ] && echo true || echo false)"
}

fetch_external_ip() {
	use_proxy=$1
	if command -v curl >/dev/null 2>&1; then
		if [ "$use_proxy" = "1" ]; then
			curl -fsS --max-time 12 --proxy "$SOCKS" "$IPIFY" 2>/dev/null \
				|| curl -fsS --max-time 12 --proxy "$SOCKS" "$IPIFY_HTTP" 2>/dev/null
		else
			curl -fsS --max-time 12 "$IPIFY" 2>/dev/null \
				|| curl -fsS --max-time 12 "$IPIFY_HTTP" 2>/dev/null
		fi
		return
	fi
	if command -v wget >/dev/null 2>&1; then
		if [ "$use_proxy" = "1" ]; then
			wget -qO- --timeout=12 --proxy=on -e use_proxy=yes -e http_proxy="$SOCKS" -e https_proxy="$SOCKS" "$IPIFY" 2>/dev/null
		else
			wget -qO- --timeout=12 "$IPIFY" 2>/dev/null
		fi
	fi
}

cmd=${1:-}; shift || true

mkdir -p "$D"
chown root:"$G" "$D" 2>/dev/null || true
chmod 750 "$D" 2>/dev/null || true

case "$cmd" in
list-media)
	for base in /media /run/media; do
		[ -d "$base" ] || continue
		for m in "$base"/*; do
			[ -d "$m" ] || continue
			printf '%s\n' "$m"
		done
	done
	;;

list-json)
	mount=${1:-}
	[ -n "$mount" ] && [ -d "$mount" ] || { echo "list-json: нет каталога" >&2; exit 1; }
	find "$mount" -maxdepth 4 -type f \( -name 'xray.json' -o -name '*.json' \) 2>/dev/null \
		| grep -v '/\.' | head -50
	;;

import)
	src=${1:-}
	[ -n "$src" ] && [ -f "$src" ] && [ -r "$src" ] || { echo "import: файл не найден: $src" >&2; exit 1; }
	cp "$src" "$CFG.new"
	mv "$CFG.new" "$CFG"
	chown root:"$G" "$CFG"
	chmod 640 "$CFG"
	echo "ok: сохранён на ГУ $CFG"
	;;

delete-config)
	rm -f "$CFG"
	echo "ok: config.json удалён с ГУ"
	;;

start)
	systemctl start "$SVC" 2>/dev/null || systemctl start "$CTL_SVC" 2>/dev/null || true
	if [ -x "$TOOL_DIR/enable-proxy.sh" ]; then
		sh "$TOOL_DIR/enable-proxy.sh"
	fi
	systemctl restart "$SVC" 2>/dev/null || true
	echo "ok: обход запущен (proxy 127.0.0.1:1080)"
	;;

stop)
	systemctl stop "$SVC" 2>/dev/null || true
	if [ -x "$TOOL_DIR/disable-proxy.sh" ]; then
		sh "$TOOL_DIR/disable-proxy.sh"
	fi
	echo "ok: обход остановлен, proxy снят"
	;;

status)
	if [ -f "$CFG" ]; then echo "config: есть ($CFG)"; else echo "config: нет"; fi
	if systemctl is-active --quiet "$SVC" 2>/dev/null; then echo "service: running"; else echo "service: stopped"; fi
	if [ -f /var/opt/mgu-updater/updater.local.conf ] && grep -q '^proxy' /var/opt/mgu-updater/updater.local.conf 2>/dev/null; then
		grep '^proxy' /var/opt/mgu-updater/updater.local.conf
	else
		echo "proxy: выкл"
	fi
	;;

connectivity-test)
	rm -f "$CANCEL_FLAG"
	mkdir -p /run/krikun-xray 2>/dev/null || true
	printf 'старт\n' >"$TEST_PROGRESS" 2>/dev/null || true
	proxy_up=0
	if systemctl is-active --quiet "$SVC" 2>/dev/null && [ -f "$CFG" ]; then
		proxy_up=1
	fi
	g_ok=false
	g_detail="не выполнялся"
	y_ok=false
	y_detail="не выполнялся"
	cancelled=0

	py=$(ping_check youtube.com) || st=$?
	st=${st:-0}
	y_ok=$(printf '%s' "$py" | sed -n '1p')
	y_detail=$(printf '%s' "$py" | sed -n '2,$p' | tr '\n' ' ')
	[ "$y_ok" = "cancelled" ] && y_ok=false
	if [ "$st" -eq 2 ] || test_cancelled; then
		cancelled=1
		emit_connectivity_json 1 "$g_ok" "$g_detail" "$y_ok" "$y_detail" "—" "—" "$proxy_up"
		rm -f "$TEST_PROGRESS"
		exit 0
	fi

	pg=$(ping_check google.com) || st=$?
	st=${st:-0}
	g_ok=$(printf '%s' "$pg" | sed -n '1p')
	g_detail=$(printf '%s' "$pg" | sed -n '2,$p' | tr '\n' ' ')
	[ "$g_ok" = "cancelled" ] && g_ok=false
	if [ "$st" -eq 2 ] || test_cancelled; then
		cancelled=1
		emit_connectivity_json 1 "$g_ok" "$g_detail" "$y_ok" "$y_detail" "—" "—" "$proxy_up"
		rm -f "$TEST_PROGRESS"
		exit 0
	fi

	if test_cancelled; then
		cancelled=1
		emit_connectivity_json 1 "$g_ok" "$g_detail" "$y_ok" "$y_detail" "—" "—" "$proxy_up"
		rm -f "$TEST_PROGRESS"
		exit 0
	fi
	printf 'внешний IP\n' >"$TEST_PROGRESS" 2>/dev/null || true

	ip_via="напрямую"
	ext_ip=""
	if [ "$proxy_up" -eq 1 ]; then
		ip_via="обход (SOCKS 127.0.0.1:1080)"
		ext_ip=$(fetch_external_ip 1) || true
	fi
	if test_cancelled; then
		cancelled=1
		emit_connectivity_json 1 "$g_ok" "$g_detail" "$y_ok" "$y_detail" "—" "—" "$proxy_up"
		rm -f "$TEST_PROGRESS"
		exit 0
	fi
	if [ -z "$ext_ip" ]; then
		ext_ip=$(fetch_external_ip 0) || true
		if [ "$proxy_up" -eq 1 ] && [ -n "$ext_ip" ]; then
			ip_via="напрямую (обход включён, но IP через SOCKS не получен)"
		fi
	fi
	[ -n "$ext_ip" ] || ext_ip="не удалось получить"
	emit_connectivity_json "$cancelled" "$g_ok" "$g_detail" "$y_ok" "$y_detail" "$ext_ip" "$ip_via" "$proxy_up"
	rm -f "$TEST_PROGRESS"
	;;

*)
	echo "usage: netctl.sh list-media | list-json <mount> | import <path> | delete-config | start | stop | status | connectivity-test" >&2
	exit 1
	;;
esac