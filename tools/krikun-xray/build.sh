#!/usr/bin/env bash
# Скачивает Xray-core linux-amd64. runas — shell (krikun-runas.sh), не кросс-компиляция.
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

if [ -f "$PREB/xray" ] && file "$PREB/xray" | grep -q 'ELF.*x86-64'; then
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
echo "OK: $PREB/xray"