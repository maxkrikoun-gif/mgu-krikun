#!/usr/bin/env bash
# Сборка + GitHub Release «catalog».
# Авторизация: gh auth login ИЛИ export GH_TOKEN=<PAT с repo>.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 scripts/catalog-release.py --fast -j 10
test -f dist/catalog/catalog.json
repo="${MGU_GITHUB_REPO:-maxkrikoun-gif/mgu-krikun}"

upload_with_curl() {
  local token="$1"
  local owner="${repo%%/*}"
  local name="${repo##*/}"
  local api="https://api.github.com/repos/${owner}/${name}"
  local rel
  rel="$(curl -fsSL -H "Authorization: Bearer ${token}" -H "Accept: application/vnd.github+json" \
    "${api}/releases/tags/catalog" 2>/dev/null || true)"
  if [ -z "$rel" ] || ! echo "$rel" | grep -q '"id"'; then
    rel="$(curl -fsSL -X POST -H "Authorization: Bearer ${token}" -H "Accept: application/vnd.github+json" \
      "${api}/releases" \
      -d '{"tag_name":"catalog","name":"catalog","body":"MGU Store catalog (без дублей mgu-store/idrive7). На ГУ: Releases → catalog."}')"
  fi
  local rid upload
  rid="$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())['id'])" <<<"$rel")"
  upload="$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())['upload_url'].split('{')[0])" <<<"$rel")"
  echo "Release id=${rid}, upload…"
  for f in dist/catalog/*; do
    [ -f "$f" ] || continue
    bn="$(basename "$f")"
    echo "  ${bn} …"
    curl -fsSL -X POST \
      -H "Authorization: Bearer ${token}" \
      -H "Accept: application/vnd.github+json" \
      -H "Content-Type: application/octet-stream" \
      "${upload}?name=${bn}" \
      --data-binary @"$f" >/dev/null
  done
}

if [ -n "${GH_TOKEN:-}" ]; then
  upload_with_curl "$GH_TOKEN"
elif gh auth status &>/dev/null; then
  if ! gh release view catalog --repo "$repo" &>/dev/null; then
    gh release create catalog --repo "$repo" --title catalog \
      --notes "MGU Store catalog (без дублей mgu-store/idrive7). На ГУ: Releases → catalog."
  fi
  gh release upload catalog --repo "$repo" dist/catalog/* --clobber
else
  echo "Нужен GH_TOKEN или gh auth login. Пример:" >&2
  echo "  export GH_TOKEN=ghp_…   # тот же класс PAT, что Store на ГУ" >&2
  echo "  bash scripts/publish-catalog-release.sh" >&2
  exit 1
fi
echo "OK: https://github.com/${repo}/releases/tag/catalog"