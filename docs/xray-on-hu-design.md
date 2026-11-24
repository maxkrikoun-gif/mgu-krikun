# Xray на MGU (идея и архитектура)

## Почему не «просто поставить xray install»

ГУ iDrive 7:

- **linux/amd64** (сборка tool: `GOARCH=amd64`, как у других пакетов mgu-deploy);
- **нет TUN в ядре**, только подписанные модули — полноценный `tun`/`xray tun` как на обычном Linux **нельзя**;
- интернет у сторонних сервисов — только через **mgu-uplink** (отдельный uid, `"internet": true` в `component.json`);
- произвольные systemd-юниты без **mgu-deploy** опасны (recmgr, safe mode).

Вывод: на ГУ нужен **локальный SOCKS5/HTTP inbound**, трафик на VPS по **VLESS/VMess/Reality**, без TUN.

## Целевая схема

```text
RideTube / Store  →  proxy socks5://127.0.0.1:1080
                            ↓
                     Xray (inbound: socks, 127.0.0.1 only)
                            ↓
                     outbound: VLESS+Reality → fr74
                            ↓
                     mgu-uplink (uid сервиса) → телефон/LTE
```

## Tool для MGU Store (черновик ТЗ)

Идентификатор: **`krikun-xray`** (свой префикс).

По образцу **mgu-deploy tools** в экосистеме Store (например [mgu-apps](https://github.com/JustAnotherPU/mgu-apps)):

| Элемент | Содержание |
|---------|------------|
| Бинарник | [Xray-core](https://github.com/XTLS/Xray-core) `linux-64`, статическая сборка, pin версии |
| Конфиг | `/var/opt/krikun-xray/conf/config.json` (права root:uid, 0640) |
| Inbound | `socks`, `listen: 127.0.0.1`, `port: 1080` |
| Outbound | VLESS/Reality из экспорта Amnezia (uuid, host, port, pbk, sid, flow, sni) |
| Supervisor | Ждёт `mgu-uplink` online (по `status.json`, как у других сетевых tools) |
| `component.json` | `"internet": true`, uid, `MemoryLimit`, без лишних capabilities |
| Store | ветка `main` + `mgu-repo.json` в `maxkrikoun-gif/mgu-krikun` |

**Не включать в репозиторий:** uuid, ключи Reality, `vpn://`.

### Пример skeleton `config.json` (плейсхолдеры)

```json
{
  "log": { "loglevel": "warning" },
  "inbounds": [{
    "tag": "socks-in",
    "protocol": "socks",
    "listen": "127.0.0.1",
    "port": 1080,
    "settings": { "udp": true }
  }],
  "outbounds": [{
    "tag": "fr74",
    "protocol": "vless",
    "settings": {
      "vnext": [{
        "address": "REPLACE_HOST",
        "port": 443,
        "users": [{ "id": "REPLACE_UUID", "encryption": "none", "flow": "xtls-rprx-vision" }]
      }]
    },
    "streamSettings": {
      "network": "tcp",
      "security": "reality",
      "realitySettings": {
        "serverName": "REPLACE_SNI",
        "publicKey": "REPLACE_PBK",
        "shortId": "REPLACE_SID",
        "fingerprint": "chrome"
      }
    }
  }],
  "routing": {
    "domainStrategy": "AsIs",
    "rules": [{ "type": "field", "inboundTag": ["socks-in"], "outboundTag": "fr74" }]
  }
}
```

На ГУ в Store/RideTube:

```ini
proxy = socks5://127.0.0.1:1080
```

## MTU и LTE

Для **Xray over TCP/Reality** отдельный MTU туннеля на ГУ не настраиваем. При обрывах на LTE — тюнинг uplink/сервера; при необходимости `sockopt` в outbound Xray. Стартовать можно с дефолтов Amnezia.

## Проверки

```bash
mgu-uplink status
systemctl status krikun-xray    # после реализации
# с ГУ (uid с интернетом или через тестовый скрипт в пакете):
curl -x socks5h://127.0.0.1:1080 -m 10 -o /dev/null -w '%{http_code}\n' https://www.youtube.com/
```

RideTube → Health check.

## Быстрый POC (только для отладки, не в прод)

SSH root, **вручную** (вне Store — на свой риск, не в recmgr):

1. Положить бинарник в `/var/opt/...`, конфиг из Amnezia.
2. Запустить от uid с доступом uplink.
3. Проверить SOCKS → YouTube.

Если POC ок — оформить **mgu-deploy tool** в каталоге этого репо.

## Рекомендация

1. Экспорт из Amnezia: **формат Xray JSON** (не `vpn://`).
2. POC SOCKS на ГУ (ручной запуск).
3. Оформить `krikun-xray` в `maxkrikoun-gif/mgu-krikun` + catalog release.
4. RideTube: `proxy = socks5://127.0.0.1:1080`.