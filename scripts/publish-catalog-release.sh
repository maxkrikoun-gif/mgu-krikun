#!/usr/bin/env bash
# Сборка + GitHub Release «catalog» (нужен gh auth login).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 scripts/catalog-release.py --fast -j 10
test -f dist/catalog/catalog.json
repo="${MGU_GITHUB_REPO:-maxkrikoun-gif/mgu-krikun}"
if ! gh release view catalog --repo "$repo" &>/dev/null; then
  gh release create catalog --repo "$repo" --title catalog \
    --notes "MGU Store catalog (без дублей mgu-store/idrive7). На ГУ: Releases → catalog."
fi
gh release upload catalog --repo "$repo" dist/catalog/* --clobber
echo "OK: https://github.com/$repo/releases/tag/catalog"