# Источники MGU Store (без WireGuard)

## Целевой стек

| Компонент | Откуда | Зачем |
|-----------|--------|--------|
| Store + uplink | `robertnisipeanu/mgu-store` | магазин и **интернет с телефона** |
| RideTube | `JustAnotherPU/ridetube` (Releases) | YouTube |
| Xray на ГУ | `maxkrikoun-gif/mgu-krikun` (Releases, позже) | SOCKS → fr74 (VLESS/Reality) |

**WireGuard / `JustAnotherPU/mgu-apps` / jap-wireproxy не ставим.**

## RideTube

[JustAnotherPU/ridetube](https://github.com/JustAnotherPU/ridetube) — клиент YouTube для iDrive 7:

- нужен **mgu-uplink**;
- в РФ нужен **proxy** в `updater.local.conf` (через локальный Xray);
- **Health check** в меню приложения.

## mgu-uplink

Не VPN. Раздаёт интернет выбранным процессам с телефона / LTE / Wi‑Fi hotspot.

RideTube без uplink не выйдет в сеть.

## Proxy (Store + RideTube)

Один файл на ГУ: `/var/opt/mgu-updater/updater.local.conf`

```ini
proxy = socks5://127.0.0.1:1080
```

(порт как у **krikun-xray**; Store → Settings → Proxy — то же значение)

RideTube читает этот файл автоматически.

## Порядок установки

1. **mgu-uplink** (уже с Store).
2. **krikun-xray** — когда выложен релиз в этом репо; конфиг из Amnezia (Xray JSON) на ГУ.
3. Прописать **proxy** (см. выше).
4. Телефон, тетеринг → uplink online.
5. **JustAnotherPU/ridetube** → RideTube → Health check.

Дизель 3.0 на YouTube/Xray не влияет.