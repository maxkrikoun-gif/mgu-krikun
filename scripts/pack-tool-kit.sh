#!/usr/bin/env bash
# Упаковка mgu-deploy tool kit: deploy/hu artifact (из клона mgu-store).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOL_DIR="${1:?usage: pack-tool-kit.sh <path-to-tool-dir>}"
MGU_STORE="${MGU_STORE:-$ROOT/.cache/mgu-store}"
HU="${MGU_STORE}/deploy/hu"
OUT_DIR="${2:-$TOOL_DIR/dist}"
mkdir -p "$OUT_DIR"
if [[ ! -x "$HU" ]] && [[ ! -f "$HU" ]]; then
  echo "pack-tool-kit: нет $HU — задайте MGU_STORE или дождитесь catalog-release.py (клонирует store)" >&2
  exit 1
fi
node "$HU" artifact "$TOOL_DIR" --out "$OUT_DIR"