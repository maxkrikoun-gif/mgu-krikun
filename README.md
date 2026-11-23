# mgu-krikun — интернет, VPN и каталог для BMW iDrive 7 (MGU)

Личный источник и документация для **MGU Store** под аккаунтом [maxkrikoun-gif](https://github.com/maxkrikoun-gif).

Цели:

- Поднять **интернет с телефона** (`mgu-uplink`) и **VPN-туннель** на головном устройстве.
- Смотреть **YouTube** через [RideTube](https://github.com/JustAnotherPU/ridetube) в РФ (нужен обход блокировок).
- Не хранить ключи Amnezia / WireGuard в репозитории.

## Что поставить в Store (порядок)

| Шаг | Источник в Store | Что ставить |
|-----|------------------|-------------|
| 1 | *(уже есть)* `robertnisipeanu/mgu-store` | Store, **mgu-uplink**, mgu-updater, mgu-deploy |
| 2 | `JustAnotherPU/mgu-apps` → **Releases** | **jap-wireproxy** (WireGuard → SOCKS5), при необходимости jap_sysmon |
| 3 | `JustAnotherPU/ridetube` → **Releases** | **RideTube** (+ сервисы и Node 22) |
| 4 | по желанию | `DarkMuse1/idrive7-apps-ru` и др. |

Подробно: [docs/store-sources.md](docs/store-sources.md).

## Цепочка «телефон → VPN → YouTube»

```text
Телефон (USB-тетеринг или Wi‑Fi hotspot)
    → mgu-uplink (отдельная маршрутизация для разрешённых приложений)
    → jap-wireproxy (WireGuard к вашему серверу / хабу)
    → SOCKS5 127.0.0.1:1065
    → proxy в Store (updater.local.conf) → трафик RideTube и загрузки Store
```

Настройка VPN и прокси: [docs/vpn-chain.md](docs/vpn-chain.md).

Примеры **без секретов**: [config/examples/](config/examples/).

## Важно про Amnezia (`fr74.vpn`)

Файл `vpn://…` из Amnezia — **не** конфиг для `jap-wireproxy`. На ГУ нужен обычный **WireGuard** (ключи peer + endpoint) или VPN **на телефоне** + uplink.

Ключи **не коммитить**. Если ключ попадал в чат — перевыпустите конфиг в Amnezia.

## Свой источник в Store

Сейчас репозиторий — **документация и шаблоны**. Полноценный источник с приложением «Net Lab» (статус uplink + VPN + тесты) — в `apps/` (в разработке).

Когда появится релиз с `catalog.json`, в Store: **+ Добавить источник** → `maxkrikoun-gif/mgu-krikun` → **Releases**.

## Лицензия

MIT — только файлы этого репозитория. RideTube, MGU Store, wireproxy — лицензии upstream-проектов.