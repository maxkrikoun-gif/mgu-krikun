# Обзор решений Xray / V2Ray / VLESS / прокси для BMW MGU (iDrive 7 / MGU Store)

Дата ревизии исследования: **2026-11-24** (база сравнения: `maxkrikoun-gif/mgu-krikun` @ `d982714`, `krikun-xray` `0.0.5` + `krikun_seti` `0.0.5`).

---

## Короткий вывод («кто уже делал»)

**Публичных пакетов Xray / V2Ray / sing-box / Clash (mihomo) / VLESS / Reality для установки на само ГУ BMW MGU (`mgu-store` / `mgu-deploy`) нет ни у кого.**

Проверены:
- поиск кода и репозиториев GitHub (`mgu-deploy` + `xray`/`v2ray`/`vless`/`reality`/`trojan`/`shadowsocks`/`sing-box`/`clash`/`mihomo`/`socks5`/`1080`, все `component.json`, `catalog.json`, `mgu-repo.json`, `mgu-uplink.service`);
- кураторские реестры экосистемы: [`FidelisClayton/awesome-bmw-mgu`](https://github.com/FidelisClayton/awesome-bmw-mgu), [`tiraUnderCode23/AQ_MGU`](https://github.com/tiraUnderCode23/AQ_MGU) (`data/community-store-sources.json`);
- все форки `robertnisipeanu/mgu-store`, `JustAnotherPU/mgu-apps`, `IterioDev/car-apps`;
- китайские каталоги (`JackieZ123430/MGU-CN-XIAOBAI` — 100+ пакетов, `JackieZ123430/jap-mgu-apps-cn`, `zhanyce/mgu-apps-zh` — 73 приложения и 21 tool);
- русскоязычные и СНГ-репозитории (`istt1899/x3`, `istt1899/ridetube`, `DarkMuse1/idrive7-apps-ru`, `DimonPrograms/dimonprograms-apps`, `asloocod/bmw-mgu-apps-public`, `kern4466/mgu-store-ua`, `Raslin777/mgu-private-apps`);
- публичные обсуждения Drive2, Bimmerpost и индексируемые Telegram-каналы.

В публичном поле на ГУ существуют **только два локальных туннельных демона** и **три смежных прокси-механизма**:
1. **`jap-wireproxy`** (`JustAnotherPU/mgu-apps`) — только userspace **WireGuard** → `127.0.0.1:1065` (без обхода DPI/ТСПУ, без VLESS/Reality).
2. **`iteriodev-tailscale`** (`IterioDev/car-apps`) — только userspace **Tailscale** → опциональный SOCKS5 `127.0.0.2:1055` (mesh-сеть, закрытая лицензия PolyForm Strict).
3. **Внешний прокси** в `robertnisipeanu/mgu-store` (`Settings → Proxy` / `updater.local.conf`) и в `istt1899/ridetube` → `JustAnotherPU/ridetube` — рассчитан на то, что Clash/Xray/sing-box крутится **снаружи ГУ** (на телефоне, роутере или ноутбуке в LAN, например `192.168.8.1:7890`). Именно так решает задачу китайское сообщество, поэтому нативного `xray`/`clash` под MGU в CN-источниках не появилось.

Таким образом, связка **`krikun-xray` + `krikun_seti`** в `mgu-krikun` — единственная известная реализация локального клиента Xray (VLESS/Reality) непосредственно на ГУ MGU с управлением с экрана автомобиля без SSH.

---

## Сводная таблица ландшафта

| Repo / автор | Подход | SOCKS / TUN | Статус | Ссылка | Сравнение с нашим `krikun-xray` (`0.0.5`) |
|---|---|---|---|---|---|
| **`maxkrikoun-gif/mgu-krikun`** (`krikun-xray` + `krikun_seti`) | Нативный **Xray-core** (`v26.11.9`, `linux-64`) на ГУ + root IPC `krikun-xray-ctl` + RU OAP-приложение «Krikun: сеть» | Userspace **SOCKS5 `127.0.0.1:1080`** (без TUN; uid `3922` через `krikun-runas`) | В репо `0.0.5` (`d982714`), preflight OK, ждёт обкатки на живом ГУ | `tools/krikun-xray/`, `apps/krikun_seti/` | Базовый референс: VLESS/Reality (экспорт JSON из Amnezia), импорт с USB без SSH, вкл/выкл `proxy` в `updater.local.conf`, тест связи и внешнего IP, полностью русский UI. |
| **`JustAnotherPU/mgu-apps`** (`jap-wireproxy` `1.1.3`) | Userspace **WireGuard** (`wireproxy v1.1.3-mgu2` + патч `wireguard-go` на `WG_TCP_SNDBUF`), DoH-резолвер на Node 8, профили `HOME_SSID` / mobile | Userspace **SOCKS5 `127.0.0.1:1065`** (без TUN; uid `3921` через `jap-runas`) | **Car-tested** (BMW X5 G05, ID7, замеры Wi-Fi и 5G) | [JustAnotherPU/mgu-apps](https://github.com/JustAnotherPU/mgu-apps/tree/main/tools/jap-wireproxy) | **Не Xray**: голый WireGuard в РФ режется ТСПУ, конфиг только руками по SSH, нет GUI-приложения. Зато **эталонная обвязка Go-демона под MGU** (MIT): DoH, `GOGC`/`GOMEMLIMIT`, `configtest`, защита `/run/<svc>/s` под systemd 237 — см. раздел «Что позаимствовать». |
| **`IterioDev/car-apps`** (`iteriodev-tailscale` `1.104.6` + `iteriodev_tailscale`) | Userspace **Tailscale** (`tailscaled` от uid `3910`) + GUI-приложение с входом по QR-коду | Userspace, без TUN; опциональный **SOCKS5 `127.0.0.2:1055`** (вкл. по SSH через файл `socks5-port`) | **Car-tested на ID8**, совместим с ID7 (на ID7 автором в машине не гонялся) | [IterioDev/car-apps](https://github.com/IterioDev/car-apps) | Для доступа в домашний tailnet (Moonride / Screen share), не для обхода блокировок через VLESS/Reality; на 5G часто уходит в DERP-реле и медленнее `wireproxy`. **Лицензия PolyForm Strict 1.0.0** — код заимствовать нельзя. |
| **`robertnisipeanu/mgu-store`** (`mgu-updater` + `mgu-uplink`) | Встроенный **клиент внешнего прокси** для скачивания пакетов/сборок + по-UID маршрутизация интернета (`table 110`, `uids.d`) | Поддержка исходящего `http://` и `socks5://` в `/var/opt/mgu-updater/updater.local.conf` (не поднимает свой прокси-сервер) | **Car-tested** (базовый компонент Store на ID7/ID8) | [robertnisipeanu/mgu-store](https://github.com/robertnisipeanu/mgu-store) | Не содержит Xray/VPN-ядра, но даёт штатную точку интеграции: `krikun-xray` пишет `proxy = socks5://127.0.0.1:1080` в `updater.local.conf`, благодаря чему и Store, и RideTube прозрачно идут через наш локальный Xray. |
| **`istt1899/ridetube`** и **`istt1899/x3`** (`media/core`, `0.3.11`–`0.3.16`) | Форк RideTube + медиакомбайн (YouTube, VK Видео, RUTUBE) с **клиентским туннелем HTTP CONNECT / SOCKS5** (`proxy.js`, совместимость с Node 8) | Исходящий клиент к внешнему `socks5://user:pass@host:port` из `state/proxy.json` (своего демона Xray на ГУ нет) | ПК/CI-тесты (Linux + Node 8.17), фиксы стриминга по фидбеку владельца | [istt1899/x3](https://github.com/istt1899/x3/tree/main/media/core), [istt1899/ridetube](https://github.com/istt1899/ridetube) | Решал ту же боль блокировки YouTube в РФ, но через **внешний прокси с логином/паролем на VPS** (настройка по SSH) без шифрования VLESS/Reality от ГУ до VPS. Код его `proxy.js` в итоге вошёл в апстрим `JustAnotherPU/ridetube`. |
| **`JustAnotherPU/ridetube`** (`jap-ridetube-d` ≥ `0.5.3`) | Штатная поддержка прокси MGU Store внутри демона YouTube (`ytd.js`, `thumb.js`, `ytfetch.py` / `yt-dlp`) | Потребитель `proxy = socks5://...` из `updater.local.conf` (`socks5h://`, резолв имён строго на прокси, fail-closed) | **Car-tested** (ID7) | [JustAnotherPU/ridetube](https://github.com/JustAnotherPU/ridetube) | Идеально стыкуется с `krikun-xray`: при включении обхода в «Krikun: сеть» RideTube сразу пускает OAuth, ленты, превью и видеопоток через `127.0.0.1:1080` без `requires`-связки между пакетами. |
| **`alexp50/bmw-apps`** (`hotspot-studio-helper` `0.1.7` + `hotspot_studio`) | Python userspace прокси для **раздачи LTE-аплинка ГУ клиентам салонного Wi-Fi хотспота BMW** (обход отсутствия NAT в ядре MGU) | Слушает `172.16.222.97:3128` (HTTP) и `172.16.222.97:1088` (SOCKS5) под `User=nobody` (`uid 65534`) | Опубликован в Store и CN-каталогах | [alexp50/bmw-apps](https://github.com/alexp50/bmw-apps) | Противоположное направление трафика (клиенты в салоне → ГУ → обычный аплинк). Нет ни Xray, ни шифрования/обхода блокировок для приложений самого ГУ. |
| **`JackieZ123430/MGU-CN-XIAOBAI`** и **`zhanyce/mgu-apps-zh`** | Крупнейшие китайские каталоги MGU Store (73–100+ пакетов: перевод UI, музыка NetEase/QQ/Qishui, браузер, RideTube) | Нет своего VPN/прокси-ядра на ГУ; используют внешний Clash/v2ray/sing-box в LAN через `Settings → Proxy` | Активно поддерживаются (ноябрь 2026) | [MGU-CN-XIAOBAI](https://github.com/JackieZ123430/MGU-CN-XIAOBAI), [mgu-apps-zh](https://github.com/zhanyce/mgu-apps-zh) | Подтверждает отсутствие скрытого китайского пакета `mgu-xray` / `mgu-clash` / `mgu-singbox`: в CN-среде прокси держат на раздающем смартфоне или роутере. |

---

## Честное сравнение с `tools/krikun-xray/` и что стоит перенять

Готового Xray-инструмента лучше нашего **не существует**, а по UX для водителя (`krikun_seti`: русский интерфейс на экране ГУ, выбор `.json` с флешки без SSH, управление `updater.local.conf`, пинг/проверка внешнего IP с отменой) `mgu-krikun` заметно впереди консольных `jap-wireproxy` и `iteriodev-tailscale` (где SOCKS/конфиги настраиваются только root-командами по SSH).

Однако на уровне **низкоуровневой обвязки сетевого Go-демона на реальном Linux ГУ (systemd 237 + `mgu-uplink`)** пакет **`jap-wireproxy` из `JustAnotherPU/mgu-apps`** проработан глубже и уже прошёл отладку на живой машине.

### Лицензионная чистота (без GPL-ловушек и слепого копирования)

- **`IterioDev/car-apps`** распространяется под **`PolyForm Strict License 1.0.0`** — любые производные работы, копирование и модификация кода **запрещены**. Оттуда ничего не берём.
- **`JustAnotherPU/mgu-apps`**:
  - скрипты `setup.sh`, `start.sh`, `resolve.js`, `check.sh` и unit-файл `jap-wireproxy.service` опубликованы под **MIT** — архитектурные паттерны (или фрагменты со стандартным уведомлением MIT) полностью совместимы с нашим MIT-пакетом;
  - утилита `jap-runas` — **`GPL-3.0-or-later`** (наш отдельный бинарник `tools/krikun-xray/runas/` уже явно лицензирован под `GPL-3.0-or-later`, что не заражает shell-скрипты и агрегат пакета при раздельной поставке);
  - сам бинарник **`Xray-core`** распространяется под **`MPL-2.0`** (file-level copyleft: при поставке неизменённого бинарника достаточно приложить текст `MPL-2.0` и ссылку на релиз `XTLS/Xray-core`).

### Что конкретно стоит доработать в `tools/krikun-xray/` по опыту `jap-wireproxy` и `mgu-uplink`

1. **Права на `/run/krikun-xray/s` под systemd 237 на ГУ (важный потенциальный баг старта)**
   - **Как у нас сейчас (`0.0.5`):** в `krikun-xray.service` задано `RuntimeDirectory=krikun-xray` (`0755`, владелец `root:root`). `setup.sh` создаёт только `/run/krikun-xray/requests` и `responses`, но **не создаёт** `/run/krikun-xray/s` с владельцем `3922:3922`. Затем `start.sh` уже под `uid 3922` выполняет `mkdir -p /run/krikun-xray/s` и пишет в `/run/krikun-xray/s/state` — внутри `0755 root:root` это даст `Permission denied`.
   - **Как проверено на машине в `jap-wireproxy`:** systemd 237 на MGU при каждом старте возвращает сам `RuntimeDirectory` пользователю юнита (`root`), поэтому `setup.sh` (под `root`) обязан явно создавать подкаталог `/run/krikun-xray/s`, проверять отсутствие симлинков (`[ ! -L "$d" ]`) и делать `chown 3922:3922 /run/krikun-xray/s && chmod 0700 /run/krikun-xray/s`.

2. **Ограничение аппетитов памяти Go-рантайма (`GOGC` и `GOMEMLIMIT`)**
   - **Почему важно:** `xray`, как и `wireproxy`, написан на Go. На реальном ГУ замеры `JustAnotherPU` показали, что без настроек GC Go-прокси под трафиком раздувает RSS до **140–166 МБ** (опасно близко к нашему `MemoryLimit=192M` в `krikun-xray.service`), тогда как с `export GOGC=30 GOMEMLIMIT=96MiB` (или `128MiB` для Xray с Reality/буферами) потребление держится в районе **25–45 МБ** без OOM-убийств сервисов ГУ.

3. **Предстартовая валидация конфига (`xray run -test -c "$CFG"`) и строгая проверка loopback**
   - **Как у нас сейчас:** `check.sh` проверяет только `grep -q '127.0.0.1' "$CFG"`, а `start.sh` сразу запускает `xray run -c "$CFG"`. Если на флешке окажется синтаксически битый JSON, опечатка в параметрах Reality или inbound на `0.0.0.0:1080`, демон уйдёт в бесконечный цикл перезапуска каждые 5 секунд (либо откроет прокси наружу).
   - **Что внедрить:** перед стартом прогонять `"$BIN" run -test -c "$CFG"`, а также проверять через `node` (штатный `/usr/bin/node` на ГУ), что JSON валиден, все `inbounds` слушают строго `127.0.0.1` / `::1`, и порт `1080` не занят чужим процессом. При ошибке — переводить статус в понятную русскую строку `idle: ошибка в config.json (...)` без рестарт-шторма.

4. **Учёт состояния `mgu-uplink` и особенностей DNS на ГУ**
   - По документации `mgu-uplink`, системный резолвер ГУ не имеет выхода в интернет (процессы с разрешённым UID ходят через таблицу маршрутизации `110` и получают `EHOSTUNREACH`, пока аплинк оффлайн, а DNS-серверы аплинка лежат в `/run/mgu-uplink/lease.json`).
   - Если в `config.json` адрес сервера `fr74` указан **IPv4-адресом** (стандарт для экспорта Amnezia) — Xray подключается напрямую без DNS, а домены целевых сайтов (`youtube.com` и т.д.) резолвятся уже на стороне VPS (`socks5h://`).
   - Если же когда-либо понадобится доменное имя самого VPS в `vnext.address`, стоит учитывать `/run/mgu-uplink/status.json` (`"state": "online"`) и задавать в конфиге Xray встроенный `dns` (например `https+local://1.1.1.1/dns-query` или чтение DNS из `lease.json`).

5. **Дополнительный systemd hardening и лицензионные файлы в архиве `.tgz`**
   - На systemd 237 BMW MGU проверенно работают без ошибок `Unknown lvalue` директивы `ProtectKernelTunables=yes`, `ProtectKernelModules=yes`, `ProtectControlGroups=yes` и `LimitCORE=0` (чтобы крэш не писал тяжёлый дамп).
   - Для полной формальной чистоты дистрибуции в `tools/krikun-xray/component.json` стоит включить текстовые файлы `LICENSE.xray` (`MPL-2.0`) и `COPYING.krikun-runas` (`GPL-3.0-or-later`) по аналогии с `THIRD_PARTY_LICENSES` в `jap-ridetube-d`.
