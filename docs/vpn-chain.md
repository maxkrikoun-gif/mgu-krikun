# VPN fr74 / Amnezia и YouTube на MGU

## Два рабочих варианта

### Вариант A (проще): VPN на телефоне

1. На телефоне включить **Amnezia** (хаб `fr74`) и **раздачу интернета** (USB-тетеринг или Wi‑Fi hotspot).
2. На ГУ **mgu-uplink** подхватывает телефон — весь исходящий трафик разрешённых приложений уже идёт через VPN телефона.
3. В Store/ RideTube **прокси не обязателен**, если YouTube открывается с телефонного VPN.

**Минус:** VPN живёт на телефоне; разряд, обрыв USB, iOS Restricted Mode.

### Вариант B (на ГУ): jap-wireproxy + SOCKS5

1. **mgu-uplink** — интернет с телефона/LTE.
2. **jap-wireproxy** ([JustAnotherPU/mgu-apps](https://github.com/JustAnotherPU/mgu-apps)) — **классический WireGuard** до **вашего** сервера, SOCKS5 на `127.0.0.1:1065`.
3. Прописать прокси для Store (RideTube подхватит автоматически):

```ini
# /var/opt/mgu-updater/updater.local.conf (на ГУ, НЕ в git)
proxy = socks5://127.0.0.1:1065
```

Конфиг wireproxy на ГУ (пример без ключей): [../config/examples/wireproxy.conf.example](../config/examples/wireproxy.conf.example).

## Почему нельзя «залить fr74.vpn в репо»

- `vpn://…` / файл Amnezia — **проприетарная упаковка**, часто **AmneziaWG** (обфускация), не тот же формат, что `wireproxy.conf`.
- `jap-wireproxy` понимает **стандартный** [wireproxy INI](https://github.com/whyvl/wireproxy#configuration) с **отдельными** ключами peer для машины.

**Что сделать на хабе fr74:**

1. В Amnezia на сервере/хабе создать **отдельного WireGuard peer «BMW MGU»** с обычным WG (если Amnezia отдаёт `.conf` с `Interface` / `Peer` — использовать его параметры).
2. Сгенерировать **новую** пару ключей только для машины (не переиспользовать ключ телефона).
3. Вручную перенести `PrivateKey`, `PublicKey`, `Endpoint`, `AllowedIPs` в `/var/opt/jap-wireproxy/conf/` на ГУ (SSH).

Если Amnezia выдаёт **только** `vpn://` без классического WG — оставайтесь на **варианте A** или поднимите отдельный **чистый WG** на том же VPS рядом с fr74.

## Проверки (тесты)

### На ГУ (SSH, root)

```bash
# uplink
mgu-uplink status
cat /run/mgu-uplink/status.json

# wireproxy
systemctl status jap-wireproxy
cat /run/jap-wireproxy/s/state 2>/dev/null || true

# прокси Store
grep -E '^proxy' /var/opt/mgu-updater/updater.local.conf
```

### В машине

1. Store → убедиться, что загрузка источников идёт (при блокировке GitHub — `proxy` обязателен).
2. RideTube → меню → **Health check** — все строки зелёные, особенно internet.
3. Открыть короткое видео на стоянке.

### На Mac (до поездки)

- Проверить, что WG-сервер отвечает (Amnezia / `wg show` на VPS).
- Не хранить `fr74.vpn` в репозитории — только локально, права `chmod 600`.

## Безопасность

- Ключ из переписки в мессенджере/чате — **считать скомпрометированным**, перевыпустить в Amnezia.
- SOCKS5 на `127.0.0.1` без пароля — любой процесс на ГУ может им пользоваться; ограничивайте `AllowedIPs` на сервере и firewall на VPS.