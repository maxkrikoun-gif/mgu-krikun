# Источники MGU Store (только свой каталог)

## На машине в Store

| Что | Источник в UI | Примечание |
|-----|---------------|------------|
| MGU Store, uplink, deploy | `robertnisipeanu/mgu-store` | сам магазин (если ещё не стоит) |
| **Всё остальное** | **`maxkrikoun-gif/mgu-krikun`** | единственный **добавляемый** каталог |

Строка в «Добавить источник»:

```text
maxkrikoun-gif/mgu-krikun
```

Больше **никаких** `DarkMuse1/...`, `JustAnotherPU/...` и т.п.

Подробно: [store-single-source.md](store-single-source.md).

## Что должно быть внутри `mgu-krikun`

| Компонент | Откуда берём в git (не в Store) | Зачем |
|-----------|----------------------------------|-------|
| **krikun-xray** | `tools/krikun-xray` | SOCKS → fr74 (**отдельный** tool) |
| **krikun_seti** | `apps/krikun_seti` | UI обхода (**отдельное** app) |
| **RideTube** app + **jap-ridetube-d** | `apps/jap_ridetube`, `native/jap-ridetube-d`, RU default | YouTube (**не** часть Xray) |
| Прочие RU apps | **DarkMuse1/idrive7-apps-ru**, сборка `ru` | community-приложения |

Связь Xray ↔ RideTube только через `proxy = socks5://127.0.0.1:1080` — [components-separate.md](components-separate.md).

**Правило:** [russian-only.md](russian-only.md) — **все** пункты меню и тексты Store для **каждого** пакета из `main`.

Установка — сразу после добавления источника и обновления ветки `main` (без отдельного релиза GitHub).

## Proxy

`/var/opt/mgu-updater/updater.local.conf`:

```ini
proxy = socks5://127.0.0.1:1080
```

## Порядок на ГУ

1. Store + **mgu-uplink** (robertnisipeanu, если нужно).
2. Один источник **`maxkrikoun-gif/mgu-krikun`** + token для private.
3. Установить **krikun-xray**, прописать proxy, поднять uplink.
4. Из того же источника — **RideTube** и нужные RU-приложения.