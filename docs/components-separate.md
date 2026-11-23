# Отдельные компоненты (RideTube ≠ Xray)

В **одном** Store-источнике `mgu-krikun`, но в catalog — **разные пакеты**, без общего приложения и без `requires` друг на друга.

## Три независимые линии

| Пакет | kind | id | Назначение |
|-------|------|-----|------------|
| **Krikun Xray** | tool | `krikun-xray` | SOCKS `127.0.0.1:1080`, конфиг на ГУ |
| **Krikun: сеть** | app | `krikun_seti` | UI: импорт USB, старт/стоп обхода, тест (RU) |
| **RideTube** | app | `jap_ridetube` | YouTube в машине (RU по умолчанию) |
| **RideTube service** | tool | `jap-ridetube-d` | Демон: yt-dlp, декод, MediaPlayer |
| **FilmixProMax** | app | `filmix_promax` | Filmix: код на consoles, каталог |
| **Filmix service** | tool | `jap-filmix-d` | Демон Filmix API v2 (proxy = как Store, от Xray) |

**Не делаем:** один OAP «Xray+YouTube», общий `main.js`, `requires: { "krikun-xray": ... }` у RideTube.

## Связь только через Store proxy

```text
krikun_seti  →  вкл/выкл krikun-xray + строка proxy в updater.local.conf
RideTube     →  настройка «proxy Store» (читает ту же строку)
```

RideTube **может** стоять без Xray (прямой uplink). Xray **может** стоять без RideTube (Store, другие apps).

## Установка на ГУ

1. **krikun-xray** (tool)
2. **krikun_seti** (app) — по желанию, для управления обходом
3. **jap-ridetube-d** + **jap_ridetube** — из этого же репо (`native/`, `apps/`)

Порядок 1→3 для обхода блокировок: сначала SOCKS, потом proxy, потом RideTube.

## В git

| Путь | Компонент |
|------|-----------|
| `tools/krikun-xray/` | Xray |
| `apps/krikun_seti/` | Krikun: сеть |
| `apps/jap_ridetube`, `native/jap-ridetube-d`, `kit/` | RideTube в **mgu-krikun**, не внутри krikun-xray |

См. [store-single-source.md](store-single-source.md), [krikun-client.md](krikun-client.md).