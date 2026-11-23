#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
mkdir -p /run/krikun-xray/requests /run/krikun-xray/responses
chmod 1777 /run/krikun-xray/requests /run/krikun-xray/responses 2>/dev/null || true
sh "$DIR/import-config.sh"