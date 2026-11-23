# Xray на MGU (идея и архитектура)

## Почему не «просто поставить xray install»

ГУ iDrive 7:

- **linux/amd64** (см. сборка jap-wireproxy: `GOARCH=amd64`);
- **нет TUN в ядре**, только подписанные модули — полноценный `tun`/`xray tun` как на обычном Linux **нельзя**;
- интернет у сторонних сервисов — только через **mgu-uplink** (отдельный uid, `"internet": true` в `component.json`);
- произвольные systemd-юниты без **mgu-deploy** опасны (recmgr, safe mode).

Вывод: Xray на ГУ возможен в режиме **как wireproxy** — **локальный SOCKS5/HTTP inbound**, трафик в VPS по **VLESS/VMess/Reality**, без TUN.

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

**WireGuard на машине не используем** — только Xray на ГУ (вариант ниже).

## Выбранный вариант

**Xray на ГУ** — tool `krikun-xray`, конфиг как в Amnezia (VLESS/Reality), без jap-wireproxy.

## Вариант 2: tool для MGU Store (черновик ТЗ)

Идентификатор, например: `krikun-xray` (префикс свой, не пересекать `jap-*`).

По образцу `tools/jap-wireproxy` в [mgu-apps](https://github.com/JustAnotherPU/mgu-apps):

| Элемент | Содержание |
|---------|------------|
| Бинарник | [Xray-core](https://github.com/XTLS/Xray-core) `linux-64`, статическая сборка, pin версии |
| Конфиг | `/var/opt/krikun-xray/conf/config.json` (права root:uid, 0640) |
| Inbound | `socks`, `listen: 127.0.0.1`, `port: 1080` (или 1065 — как у wireproxy) |
| Outbound | VLESS/Reality из экспорта Amnezia (uuid, host, port, pbk, sid, flow, sni) |
| Supervisor | Ждёт `mgu-uplink` online (как wireproxy + `status.json`) |
| `component.json` | `"internet": true`, uid, `MemoryLimit`, без лишних capabilities |
| Store | Releases + `catalog.json` в репо `maxkrikoun-gif/mgu-krikun` |

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

## MTU = 1400

Для **Xray over TCP/Reality** это не WG `Interface MTU`. При обрывах на LTE — тюнинг uplink/сервера; при необходимости `sockopt` в outbound Xray. Стартовать можно с дефолтов Amnezia.

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

Если POC ок — перенос в **mgu-deploy tool**, как wireproxy.

## Рекомендация

1. Экспорт из Amnezia: **формат Xray JSON** (не `vpn://`).
2. POC SOCKS на ГУ (ручной запуск).
3. Оформить `krikun-xray` в `maxkrikoun-gif/mgu-krikun` + catalog release.
4. RideTube: `proxy = socks5://127.0.0.1:1080`.

WireGuard на машине **не планируется** — только VLESS на fr74.