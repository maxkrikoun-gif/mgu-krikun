#!/bin/sh
# mgu-deploy check: node22 грузит JS демона (offline).
set -eu
d=$(cd "$(dirname "$0")" && pwd)
NODE="${MGU_NODE:-/var/opt/jap-node22/current/bin/node}"
exec "$NODE" -e "require('$d/filmix-api');require('$d/filmix-auth');require('$d/proxy')"