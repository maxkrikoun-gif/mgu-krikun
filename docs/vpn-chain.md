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

## Проверки

```bash
mgu-uplink status
systemctl status krikun-xray   # после установки tool
grep '^proxy' /var/opt/mgu-updater/updater.local.conf
```

В машине: RideTube → **Health check**.