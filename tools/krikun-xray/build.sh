#!/usr/bin/env bash
# Xray-core linux-amd64 + krikun-runas (ELF, как jap-runas).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"
BUILD="$ROOT/build"
PREB="$ROOT/prebuilt"
mkdir -p "$BUILD" "$PREB"

XRAY_VERSION="${XRAY_VERSION:-26.11.9}"
ARCH=linux-64
ZIP="Xray-${ARCH}.zip"
URL="https://github.com/XTLS/Xray-core/releases/download/v${XRAY_VERSION}/${ZIP}"
CACHE_ZIP="$REPO_ROOT/.cache/xray-core/v${XRAY_VERSION}/${ZIP}"

build_runas() {
	if [ -f "$PREB/krikun-runas" ] && file "$PREB/krikun-runas" | grep -q 'ELF.*x86-64'; then
		echo "OK (prebuilt): $PREB/krikun-runas"
		return
	fi
	echo "Сборка krikun-runas (GOOS=linux GOARCH=amd64) …"
	local go_bin=go
	for g in "$REPO_ROOT/.cache"/go*/go/bin/go; do
		[ -x "$g" ] && go_bin="$g" && break
	done
	(
		cd "$ROOT/runas"
		GOOS=linux GOARCH=amd64 CGO_ENABLED=0 "$go_bin" build -ldflags='-s -w' -o "$PREB/krikun-runas" .
	) || {
		echo "go build failed — static C (musl-cross / cc -static) …" >&2
		local cc=""
		for c in x86_64-linux-musl-gcc x86_64-linux-gnu-gcc; do
			command -v "$c" >/dev/null && cc="$c" && break
		done
		[ -n "$cc" ] || { echo "нет go и нет linux cross-cc для krikun-runas.c" >&2; exit 1; }
		"$cc" -static -O2 -s -o "$PREB/krikun-runas" "$ROOT/runas/krikun-runas.c"
	}
	chmod 755 "$PREB/krikun-runas"
	if ! file "$PREB/krikun-runas" | grep -q 'ELF.*x86-64'; then
		echo "krikun-runas не ELF x86-64: $(file "$PREB/krikun-runas")" >&2
		exit 1
	fi
	echo "OK: $PREB/krikun-runas"
}

if [ -f "$PREB/xray" ] && file "$PREB/xray" | grep -q 'ELF.*x86-64'; then
	build_runas
	echo "OK (prebuilt): $PREB/xray"
	exit 0
fi

mkdir -p "$(dirname "$CACHE_ZIP")"
if [ ! -f "$CACHE_ZIP" ]; then
	echo "Загрузка $URL → .cache …"
	rm -f "${CACHE_ZIP}.part"
	curl -fsSL --connect-timeout 15 --max-time 600 -C - "$URL" -o "${CACHE_ZIP}.part"
	mv "${CACHE_ZIP}.part" "$CACHE_ZIP"
fi
unzip -o -q "$CACHE_ZIP" -d "$BUILD"
[ -f "$BUILD/xray" ] || [ -f "$BUILD/xray.bin" ] || { echo "xray binary not found in zip"; exit 1; }
[ -f "$BUILD/xray" ] || mv "$BUILD/xray.bin" "$BUILD/xray"
chmod 755 "$BUILD/xray"
cp -f "$BUILD/xray" "$PREB/xray"
if ! file "$PREB/xray" | grep -q 'ELF.*x86-64'; then
	echo "xray не ELF x86-64: $(file "$PREB/xray")" >&2
	exit 1
fi
build_runas
echo "OK: $PREB/xray"