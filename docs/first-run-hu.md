# Первый запуск на ГУ (iDrive 7)

**Один пользовательский источник Store:** `maxkrikoun-gif/mgu-krikun` (**main** или Releases → **catalog**).

Полный контекст практик: [mgu-idrive7-best-practices.md](mgu-idrive7-best-practices.md).

## Версии в catalog (сейчас)

| Порядок | id | version | kind |
|--------:|-----|---------|------|
| 0 | jap-node22 | 22.23.4 | tool |
| 1 | krikun-xray | 0.0.8 | tool |
| 2 | krikun_seti | 0.0.5 | app |
| 3 | jap-ridetube-d | 0.5.6 | tool |
| 4 | jap_ridetube (YouT) | 0.6.6 | app |
| 5 | jap-filmix-d | 0.0.3 | tool |
| 6 | filmix_promax | 0.0.4 | app |

**Из других источников Store (до apps):** mgu-store (`mgu-render` **0.6.11**, `mgu-inputgate` **1.0.0**, …), idrive7-apps (**idrive7-renderd** **2.1.10** для Krikun: сеть и FilmixProMax).

## Порядок установки

1. **Node.js 22** (jap-node22)
2. **Krikun Xray** (krikun-xray)
3. **Krikun: сеть** (krikun_seti) — импорт Xray JSON с USB, «Запустить обход»
4. **YouT (сервис)** jap-ridetube-d → **YouT** jap_ridetube
5. **Filmix (сервис)** jap-filmix-d → **FilmixProMax**

Apps — **unit** (`package/` в git). После правок на Mac: `python3 scripts/sync-unit-package.py <id> --strip-locale-suffix` при необходимости.

## Proxy (обход блокировок)

Xray и YouTube **не связаны через `requires`**. Связь только через файл Store:

```text
/var/opt/mgu-updater/updater.local.conf
proxy = socks5://127.0.0.1:1080
```

- Пишет **Krikun: сеть** («Запустить обход») через `enable-proxy.sh`; снимает — `disable-proxy.sh`.
- Читают **Store**, **jap-ridetube-d** (`proxy.js`), **jap-filmix-d**.
- Пример: [config/examples/updater.local.conf.example](../config/examples/updater.local.conf.example).

Схема: [vpn-chain.md](vpn-chain.md).

## Перед push в main (на Mac)

```bash
python3 scripts/validate-mgu-app.py    # unit-apps, modules[]
python3 scripts/preflight-store.py     # 11 проходов — обязательно OK
# при смене версий / tgz:
python3 scripts/catalog-release.py --fast
```

Private repo: GitHub token в настройках Store на ГУ. **Node 22** — части `node.part.*` в git, на install собирается `bin/node` (Git LFS на ГУ не нужен).

## После установки в машине (чеклист)

1. **Uplink:** `mgu-uplink status` — интернет с телефона активен.
2. **Xray:** в **Krikun: сеть** — импорт `KRIKUN/xray.json` с USB (если ещё нет), **Запустить обход**; убедиться, что proxy включён: `grep '^proxy' /var/opt/mgu-updater/updater.local.conf`.
3. **Службы:** `systemctl is-active krikun-xray jap-ridetube-d` — `active` (после первого запуска компонентов).
4. **YouT:** открыть приложение → **Health check** (сеть + proxy).
5. При сбое загрузок Store — снова **Запустить обход** и проверить строку proxy (см. [memory-hu.md](memory-hu.md)).