#!/bin/sh
# Собрать bin/node из node.part.* или node.part.*.gz (ГУ: current/; dev: prebuilt/).
set -eu
d=$(cd "$(dirname "$0")" && pwd)
out="$d/bin/node"
mkdir -p "$d/bin"
parts=""
for base in "$d" "$d/prebuilt"; do
    if ls "$base"/node.part.*.gz >/dev/null 2>&1; then
        parts=$(ls "$base"/node.part.*.gz | sort)
        break
    fi
    if ls "$base"/node.part.* >/dev/null 2>&1; then
        case "$(ls "$base"/node.part.* | head -1)" in
            *.gz) ;;
            *) parts=$(ls "$base"/node.part.* | sort); break ;;
        esac
    fi
done
if [ -z "$parts" ]; then
    echo "assemble: нет node.part.* (.gz) в $d" >&2
    exit 1
fi
tmp="$out.new"
: >"$tmp"
for p in $parts; do
    case "$p" in
        *.gz) gunzip -c "$p" >>"$tmp" ;;
        *) cat "$p" >>"$tmp" ;;
    esac
done
chmod 0755 "$tmp"
mv -f "$tmp" "$out"