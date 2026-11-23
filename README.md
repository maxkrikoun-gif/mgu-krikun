# mgu-krikun — Xray, интернет и YouTube на BMW iDrive 7 (MGU)

Личный контур с нуля: [maxkrikoun-gif/mgu-krikun](https://github.com/maxkrikoun-gif), SSH **`~/.ssh/mgu_krikun`** ([docs/project-identity.md](docs/project-identity.md)).

**WireGuard на машине не используем.** Обход — **Xray (VLESS/Reality)** с хаба **fr74** (Amnezia), клиент на ГУ в режиме SOCKS (как задумано в [docs/xray-on-hu-design.md](docs/xray-on-hu-design.md)).

## Цели

- **mgu-uplink** — интернет с телефона (USB / hotspot).
- **krikun-xray** (в разработке) — Xray на ГУ, SOCKS `127.0.0.1:1080` → fr74.
- **RideTube** — YouTube через тот же proxy, что и Store.
- Секреты Amnezia **не** в git.

## Что поставить в Store сейчас

| Шаг | Источник | Что ставить |
|-----|----------|-------------|
| 1 | `robertnisipeanu/mgu-store` | Store, **mgu-uplink**, updater, deploy |
| 2 | `JustAnotherPU/ridetube` → **Releases** | RideTube (+ node22 и сервисы) |
| 3 | `maxkrikoun-gif/mgu-krikun` → **Releases** | **krikun-xray** (когда появится catalog) |
| опционально | `DarkMuse1/idrive7-apps-ru` | русские приложения |

**jap-wireproxy / WireGuard не нужны.**

Подробно: [docs/store-sources.md](docs/store-sources.md).

## Цепочка без WG

```text
Телефон → mgu-uplink
              ↓
         krikun-xray (SOCKS 127.0.0.1:1080 → VLESS fr74)
              ↓
         proxy в updater.local.conf
              ↓
         RideTube / Store
```

Пошагово: [docs/xray-on-hu-design.md](docs/xray-on-hu-design.md).

Пример конфига: [config/examples/xray-config.json.example](config/examples/xray-config.json.example).

## Amnezia

Экспортируйте **Xray JSON** из Amnezia, не `vpn://`. Файлы `*.vpn` — только локально на Mac/ГУ.

## Репозиторий на GitHub

Инструкция: [docs/github-create.md](docs/github-create.md).

## Лицензия

MIT — файлы этого репо. RideTube, MGU Store, Xray-core — лицензии upstream.