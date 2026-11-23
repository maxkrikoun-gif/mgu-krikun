#!/usr/bin/env bash
# Подсказка параметров Filmix API из APK / распакованной папки (jadx, apktool).
set -euo pipefail
ROOT="${1:-}"
if [[ -z "$ROOT" || ! -e "$ROOT" ]]; then
  echo "Использование: $0 /path/to/FilmixProMax.apk|/path/to/jadx-out/" >&2
  exit 2
fi
SEARCH="$(mktemp -d)"
trap 'rm -rf "$SEARCH"' EXIT

if [[ -f "$ROOT" && "$ROOT" == *.apk ]]; then
  if command -v unzip >/dev/null; then
    unzip -qq -o "$ROOT" -d "$SEARCH" 2>/dev/null || true
    ROOT="$SEARCH"
  else
    echo "Нужен unzip или укажите папку jadx-out" >&2
    exit 1
  fi
fi

echo "=== user_dev_apk / token_request / filmix host ==="
rg -n "user_dev_apk|token_request|filmixapp|filmix\.gg/consoles|user_profile" "$ROOT" 2>/dev/null | head -40 || true

echo ""
echo "=== user_dev_apk значения ==="
rg -o "user_dev_apk[=][0-9.]+" "$ROOT" 2>/dev/null | sort -u | head -10 || true

echo ""
echo "Подставьте в jap-filmix-d: FILMIX_DEV_APK=... FILMIX_API_HOST=..."