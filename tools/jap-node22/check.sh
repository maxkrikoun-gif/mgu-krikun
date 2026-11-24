#!/bin/sh
# mgu-deploy "check": node v22.23.4 + crypto; offline. Сначала assemble, если bin/node ещё нет.
set -eu
d=$(cd "$(dirname "$0")" && pwd)
node="$d/bin/node"
if [ ! -f "$node" ] || [ "$(wc -c <"$node" | tr -d ' ')" -lt 50000000 ]; then
    first=$(head -1 "$node" 2>/dev/null || true)
    if echo "$first" | grep -q 'git-lfs.github.com'; then
        echo "check: bin/node — LFS-pointer, не бинарник (обновите каталог / jap-node22 с node.part.*)" >&2
        rm -f "$node"
    fi
    "$d/assemble.sh"
fi
exec "$node" -e 'require("crypto").createHash("sha256");process.exit(process.version==="v22.23.4"?0:1)'