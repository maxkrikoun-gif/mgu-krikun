#!/usr/bin/env bash
# Скачивает Xray-core linux-amd64 и собирает krikun-runas (stub: копия из jap-runas-паттерна).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
BUILD="$ROOT/build"
mkdir -p "$BUILD"

# Pin версии — обновлять осознанно. См. https://github.com/XTLS/Xray-core/releases
XRAY_VERSION="${XRAY_VERSION:-25.10.15}"
ARCH=linux-64

ZIP="Xray-${XRAY_VERSION}-${ARCH}.zip"
URL="https://github.com/XTLS/Xray-core/releases/download/v${XRAY_VERSION}/${ZIP}"

if [ ! -f "$BUILD/xray" ]; then
	echo "Загрузка $URL ..."
	curl -fsSL "$URL" -o "$BUILD/$ZIP"
	unzip -o "$BUILD/$ZIP" -d "$BUILD"
	mv "$BUILD/xray" "$BUILD/xray.bin" 2>/dev/null || true
	[ -f "$BUILD/xray" ] || [ -f "$BUILD/xray.bin" ] || { echo "xray binary not found in zip"; exit 1; }
	[ -f "$BUILD/xray" ] || mv "$BUILD/xray.bin" "$BUILD/xray"
	chmod 755 "$BUILD/xray"
	rm -f "$BUILD/$ZIP"
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