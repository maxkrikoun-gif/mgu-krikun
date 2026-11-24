#!/usr/bin/env bash
# Минимальный набор mgu-store для pack tool kit (секунды, не git clone).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${MGU_STORE:-$ROOT/.cache/mgu-store-minimal}"
BASE="https://raw.githubusercontent.com/robertnisipeanu/mgu-store/main"
mkdir -p "$OUT/deploy" "$OUT/tools"
curl -fsSL --max-time 60 "$BASE/deploy/hu" -o "$OUT/deploy/hu"
curl -fsSL --max-time 60 "$BASE/tools/oap_pack.js" -o "$OUT/tools/oap_pack.js"
chmod 755 "$OUT/deploy/hu"
echo "OK: $OUT"