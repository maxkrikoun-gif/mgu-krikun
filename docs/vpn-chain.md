# Сеть на ГУ: uplink + Xray

## Схема

```text
Телефон (USB / hotspot) → mgu-uplink
                                ↓
                          krikun-xray (SOCKS → VLESS fr74)
                                ↓
proxy = socks5://127.0.0.1:1080  →  RideTube, Store
```

Детали сборки tool: [xray-on-hu-design.md](xray-on-hu-design.md).

## Amnezia fr74

- Импорт только как **конфиг Xray** (JSON), не `vpn://`.
- Секреты в `/var/opt/krikun-xray/conf/` на ГУ, не в GitHub.

## updater.local.conf и enable-proxy

Единая точка для Store и демонов:

| Файл | Кто пишет | Кто читает |
|------|-----------|------------|
| `/var/opt/mgu-updater/updater.local.conf` | **Krikun: сеть** / `netctl.sh` → `enable-proxy.sh` / `disable-proxy.sh` | Store (загрузки), `jap-ridetube-d/proxy.js`, `jap-filmix-d/proxy.js` |

Строка при обходе (SOCKS только на localhost):

```text
proxy = socks5://127.0.0.1:1080
```

Пример-шаблон в репо: [config/examples/updater.local.conf.example](../config/examples/updater.local.conf.example).  
Ручное редактирование на ГУ не требуется, если пользуетесь приложением **Krikun: сеть**.

## Проверки

```bash
mgu-uplink status
systemctl status krikun-xray   # после установки tool
grep '^proxy' /var/opt/mgu-updater/updater.local.conf
```

В машине: **YouT** → **Health check**.