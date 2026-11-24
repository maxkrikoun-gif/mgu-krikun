#!/usr/bin/env bash
# Скачивает Xray-core linux-amd64 и собирает krikun-runas (stub: копия из jap-runas-паттерна).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"
BUILD="$ROOT/build"
mkdir -p "$BUILD"

# Pin версии — обновлять осознанно. См. https://github.com/XTLS/Xray-core/releases
XRAY_VERSION="${XRAY_VERSION:-26.11.9}"
ARCH=linux-64

# С v26 asset: Xray-linux-64.zip (без версии в имени файла)
ZIP="Xray-${ARCH}.zip"
URL="https://github.com/XTLS/Xray-core/releases/download/v${XRAY_VERSION}/${ZIP}"
CACHE_ZIP="$REPO_ROOT/.cache/xray-core/v${XRAY_VERSION}/${ZIP}"

if [ -f "$BUILD/xray" ] && [ -f "$BUILD/krikun-runas" ]; then
	echo "OK (кэш): $BUILD/xray"
	exit 0
fi

if [ ! -f "$BUILD/xray" ]; then
	mkdir -p "$(dirname "$CACHE_ZIP")"
	if [ ! -f "$CACHE_ZIP" ]; then
		echo "Загрузка $URL → .cache (один раз) …"
		rm -f "${CACHE_ZIP}.part" "${CACHE_ZIP}.aria2"
		if command -v aria2c >/dev/null; then
			aria2c -x16 -s16 -k1M -d "$(dirname "$CACHE_ZIP")" -o "$(basename "$CACHE_ZIP")" "$URL"
		else
			curl -fsSL --connect-timeout 15 --max-time 600 -C - "$URL" -o "${CACHE_ZIP}.part"
			mv "${CACHE_ZIP}.part" "$CACHE_ZIP"
		fi
	fi
	unzip -o -q "$CACHE_ZIP" -d "$BUILD"
	mv "$BUILD/xray" "$BUILD/xray.bin" 2>/dev/null || true
	[ -f "$BUILD/xray" ] || [ -f "$BUILD/xray.bin" ] || { echo "xray binary not found in zip"; exit 1; }
	[ -f "$BUILD/xray" ] || mv "$BUILD/xray.bin" "$BUILD/xray"
	chmod 755 "$BUILD/xray"
fi

# Минимальный runas: setuid drop (на машине можно заменить копией jap-runas из mgu-apps)
cat >"$BUILD/krikun-runas.c" <<'EOF'
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
int main(int argc, char **argv) {
	if (argc < 3) { fprintf(stderr, "usage: krikun-runas <uid> <cmd> [args...]\n"); return 1; }
	uid_t u = (uid_t)atoi(argv[1]);
	if (setgroups(0, NULL) || setgid(u) || setuid(u)) { perror("drop priv"); return 1; }
	execvp(argv[2], argv + 2);
	perror("exec");
	return 1;
}
EOF
cc -O2 -o "$BUILD/krikun-runas" "$BUILD/krikun-runas.c"
echo "OK: $BUILD/xray $BUILD/krikun-runas"