#!/bin/sh
# Собрать bin/node из node.part.* (на ГУ — в current/; в git — prebuilt/).
set -eu
d=$(cd "$(dirname "$0")" && pwd)
out="$d/bin/node"
mkdir -p "$d/bin"
if ls "$d"/node.part.* >/dev/null 2>&1; then
    parts=$(ls "$d"/node.part.* | sort)
elif ls "$d"/prebuilt/node.part.* >/dev/null 2>&1; then
    parts=$(ls "$d"/prebuilt/node.part.* | sort)
else
    echo "assemble: нет node.part.* в $d (и нет prebuilt/)" >&2
    exit 1
fi
tmp="$out.new"
: >"$tmp"
for p in $parts; do
    cat "$p" >>"$tmp"
done
chmod 0755 "$tmp"
mv -f "$tmp" "$out"