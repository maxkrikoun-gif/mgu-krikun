# Источники MGU Store для maxkrikoun-gif

Формат имени: `владелец/репозиторий` (без `https://`).

## RideTube — что это

**RideTube** ([JustAnotherPU/ridetube](https://github.com/JustAnotherPU/ridetube)) — неофициальный **клиент YouTube** для iDrive 7:

- ставится из Store (layout **Releases**);
- работает **на ГУ**, нужен интернет через **mgu-uplink**;
- в РФ без VPN/прокси YouTube часто недоступен;
- в меню есть **Health check** — проверка сервиса, интернета, места на диске, аудио;
- при вождении по умолчанию только звук (как подкаст).

Это **не** Android APK и не официальное приложение Google.

## mgu-uplink — что это

Компонент из [mgu-store](https://github.com/robertnisipeanu/mgu-store/tree/main/native/mgu-uplink):

- даёт **интернет только выбранным** процессам/приложениям (изоляция от остальной системы ГУ);
- поднимает канал с **телефона** (USB tethering RNDIS/NCM, iPhone Personal Hotspot), **Wi‑Fi** (hotspot телефона), USB LTE-стика и т.д.;
- **не является VPN** — маршрутизатор «в мир» для разрешённых uid;
- статус: `/run/mgu-uplink/status.json` (на ГУ, root/SSH).

RideTube **зависит** от uplink: без линка Health check покажет ошибку интернета.

## Прокси Store и RideTube

RideTube читает ту же настройку прокси, что и MGU Store:

- файл на ГУ: `/var/opt/mgu-updater/updater.local.conf`
- строка: `proxy = socks5://127.0.0.1:1065` (порт как у `jap-wireproxy`, см. [vpn-chain.md](vpn-chain.md))
- либо **Store → Settings → Proxy** (тот же конфиг)

Так трафик YouTube идёт через SOCKS5 → WireGuard, а не напрямую в заблокированную сеть.

## Рекомендуемый порядок установки

1. Убедиться, что **mgu-uplink** установлен (идёт с Store).
2. **JustAnotherPU/mgu-apps** (Releases) → **jap-wireproxy** — настроить WG на ГУ (см. vpn-chain.md).
3. Прописать **proxy** для Store / RideTube.
4. Подключить телефон, проверить uplink (статус в Store или SSH).
5. **JustAnotherPU/ridetube** (Releases) → RideTube → **Health check** в приложении.

## Дизель 3.0

RideTube и uplink/VPN **не зависят** от типа ДВС. Осторожнее с приложениями, пишущими в ECU (exhaust flap, start/stop) — для бензина.