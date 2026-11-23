#!/bin/sh
# SPDX-License-Identifier: MIT
# Root: один раз скопировать xray.json на ГУ в /var/opt/krikun-xray/conf/config.json
# Флешку после этого можно вынуть — Xray читает только сохранённый файл.
set -eu
D=/var/opt/krikun-xray/conf
INC=/var/opt/krikun-xray/incoming
CFG="$D/config.json"
G=3922

mkdir -p "$D" "$INC"
chown root:"$G" "$D" "$INC"
chmod 750 "$D" "$INC"

# Авто-импорт только если config ещё нет (ручной выбор — через приложение «Сеть» + netctl import)
if [ -f "$CFG" ]; then
	exit 0
fi

imported=
if [ -f "$INC/xray.json" ] && [ -r "$INC/xray.json" ]; then
	cp "$INC/xray.json" "$CFG.new"
	imported=incoming
	rm -f "$INC/xray.json" "$INC/force-import"
elif [ -f "$INC/force-import" ]; then
	:
else
	for f in /media/*/KRIKUN/xray.json /run/media/*/KRIKUN/xray.json; do
		[ -f "$f" ] || continue
		[ -r "$f" ] || continue
		cp "$f" "$CFG.new"
		imported="usb:$f"
		break
	done
fi

[ -n "$imported" ] || exit 0
[ -f "$CFG.new" ] || exit 0

mv "$CFG.new" "$CFG"
chown root:"$G" "$CFG"
chmod 640 "$CFG"
echo "krikun-xray: сохранён config.json на ГУ (источник: $imported)"