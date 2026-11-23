#!/bin/sh
# SPDX-License-Identifier: MIT
# Root: обрабатывает запросы из приложения «Krikun: сеть» (/run/krikun-xray/requests/*.json)
set -u
RUN=/run/krikun-xray
REQ=$RUN/requests
RES=$RUN/responses
NETCTL=/var/opt/krikun-xray/current/netctl.sh
CANCEL_FLAG=$RUN/cancel-connectivity-test
TEST_PID=$RUN/connectivity-test.pid
TICK=${KRIKUN_REQ_TICK:-1}
REAP_TICKS=${KRIKUN_REQ_REAP_EVERY:-120}

mkdir -p "$REQ" "$RES"
chmod 1777 "$REQ" "$RES" 2>/dev/null || chmod 0777 "$REQ" "$RES"

reap_stale() {
	# tmpfs /run: не копить забытые JSON после сбоя приложения
	find "$RES" -maxdepth 1 -type f -name '*.json' -mmin +15 -delete 2>/dev/null || true
	find "$REQ" -maxdepth 1 -type f -name '*.json' -mmin +15 -delete 2>/dev/null || true
}

test_pid_alive() {
	[ -f "$TEST_PID" ] || return 1
	tpid=$(cat "$TEST_PID" 2>/dev/null || true)
	[ -n "$tpid" ] && kill -0 "$tpid" 2>/dev/null
}

process_one() {
	f=$1
	id=$(basename "$f" .json)
	# shellcheck disable=SC2002
	body=$(cat "$f")
	rm -f "$f"
	op=$(echo "$body" | sed -n 's/.*"op"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
	path=$(echo "$body" | sed -n 's/.*"path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
	reply_to=$(echo "$body" | sed -n 's/.*"reply_to"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
	out=$RES/"$id".json
	: >"$out.tmp"
	if [ ! -x "$NETCTL" ]; then
		echo '{"ok":false,"error":"netctl missing"}' >"$out"
		return
	fi
	case "$op" in
	import)
		if "$NETCTL" import "$path" >"$out.tmp" 2>&1; then
			printf '{"ok":true,"op":"import","message":' >"$out"
			sed 's/"/\\"/g' "$out.tmp" | awk '{printf "\"%s\"}", $0}'
			echo >>"$out"
		else
			msg=$(tr '\n' ' ' <"$out.tmp" | sed 's/"/\\"/g')
			printf '{"ok":false,"op":"import","error":"%s"}\n' "$msg" >"$out"
		fi
		;;
	delete_config|delete-config)
		if "$NETCTL" delete-config >"$out.tmp" 2>&1; then
			echo '{"ok":true,"op":"delete_config"}' >"$out"
		else
			echo '{"ok":false,"op":"delete_config"}' >"$out"
		fi
		;;
	start)
		if "$NETCTL" start >"$out.tmp" 2>&1; then
			echo '{"ok":true,"op":"start"}' >"$out"
		else
			echo '{"ok":false,"op":"start"}' >"$out"
		fi
		;;
	stop)
		if "$NETCTL" stop >"$out.tmp" 2>&1; then
			echo '{"ok":true,"op":"stop"}' >"$out"
		else
			echo '{"ok":false,"op":"stop"}' >"$out"
		fi
		;;
	status)
		"$NETCTL" status >"$out.tmp" 2>&1 || true
		echo '{"ok":true,"op":"status","lines":[]}' >"$out"
		;;
	connectivity_test|test)
		if test_pid_alive; then
			printf '{"ok":false,"op":"connectivity_test","error":"тест уже выполняется"}\n' >"$out"
			return 0
		fi
		rm -f "$CANCEL_FLAG"
		(
			if "$NETCTL" connectivity-test >"$out" 2>"$out.tmp"; then
				:
			elif [ -s "$out" ]; then
				:
			else
				msg=$(tr '\n' ' ' <"$out.tmp" | sed 's/"/\\"/g')
				printf '{"ok":false,"op":"connectivity_test","error":"%s"}\n' "$msg" >"$out"
			fi
			rm -f "$TEST_PID" "$out.tmp"
			chmod 644 "$out" 2>/dev/null || true
		) &
		echo $! >"$TEST_PID"
		return 0
		;;
	cancel_connectivity_test|cancel_test)
		: >"$CANCEL_FLAG" 2>/dev/null || echo 1 >"$CANCEL_FLAG"
		if [ -f "$TEST_PID" ]; then
			tpid=$(cat "$TEST_PID" 2>/dev/null || true)
			[ -n "$tpid" ] && kill -TERM "$tpid" 2>/dev/null || true
		fi
		if [ -n "$reply_to" ] && [ ! -f "$RES/$reply_to.json" ]; then
			printf '{"ok":false,"cancelled":true,"op":"connectivity_test","error":"остановлено пользователем"}\n' \
				>"$RES/$reply_to.json"
			chmod 644 "$RES/$reply_to.json" 2>/dev/null || true
		fi
		echo '{"ok":true,"op":"cancel_connectivity_test"}' >"$out"
		;;
	*)
		echo '{"ok":false,"error":"unknown op"}' >"$out"
		;;
	esac
	rm -f "$out.tmp"
	chmod 644 "$out" 2>/dev/null || true
}

tick=0
while :; do
	for f in "$REQ"/*.json; do
		[ -f "$f" ] || break
		process_one "$f"
	done
	tick=$((tick + 1))
	if [ $((tick % REAP_TICKS)) -eq 0 ]; then
		reap_stale
		if [ -f "$TEST_PID" ] && ! test_pid_alive; then
			rm -f "$TEST_PID"
		fi
	fi
	sleep "$TICK"
done