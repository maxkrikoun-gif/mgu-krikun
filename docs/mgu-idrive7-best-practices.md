# Лучшие практики экосистемы BMW MGU для iDrive 7

Дата ревизии: **24 ноября 2026** (база сравнения: `maxkrikoun-gif/mgu-krikun`, ветка `main`).

Связанные документы репозитория (без дублирования полных обзоров):
- Краткий чеклист правил для агентов: [`.cursor/rules/mgu-krikun-hu.mdc`](../.cursor/rules/mgu-krikun-hu.mdc) (`alwaysApply`)
- Жёсткие ограничения проекта: [`CONSTRAINTS.md`](../CONSTRAINTS.md)
- Порядок первой установки на ГУ: [`docs/first-run-hu.md`](first-run-hu.md)
- Глубокий разбор внутренностей `mgu-deploy` / `oap_link`: [`docs/mgu-ecosystem-patterns.md`](mgu-ecosystem-patterns.md)
- Полный разбор YouTube-клиентов и форков: [`docs/mgu-youtube-landscape.md`](mgu-youtube-landscape.md)
- Полный разбор Xray / прокси-решений: [`docs/mgu-xray-landscape.md`](mgu-xray-landscape.md)

> **Границы обзора (только iDrive 7 / `mguHmi: ["ID7"]`):** репозитории и пакеты исключительно под iDrive 8 (например [`waliworld/iDrive8-RideTube`](https://github.com/waliworld/iDrive8-RideTube), ID8-компоненты [`IterioDev/car-apps`](https://github.com/IterioDev/car-apps) и [`rishik250809/idrive8-app-test`](https://github.com/rishik250809/idrive8-app-test)) намеренно исключены — целевое ГУ работает только на **iDrive 7**.

Проанализированные источники: [`FidelisClayton/awesome-bmw-mgu`](https://github.com/FidelisClayton/awesome-bmw-mgu), [`robertnisipeanu/mgu-store`](https://github.com/robertnisipeanu/mgu-store), [`JustAnotherPU/ridetube`](https://github.com/JustAnotherPU/ridetube), [`JustAnotherPU/mgu-apps`](https://github.com/JustAnotherPU/mgu-apps), [`istt1899/x3`](https://github.com/istt1899/x3) (`media/core`), [`Oussemf/idrive-apps`](https://github.com/Oussemf/idrive-apps), [`Drake1804/bube-releases`](https://github.com/Drake1804/bube-releases), [`tiraUnderCode23/AQ_MGU`](https://github.com/tiraUnderCode23/AQ_MGU), [`zhanyce/mgu-apps-zh`](https://github.com/zhanyce/mgu-apps-zh), [`JackieZ123430/mgu-store-cn`](https://github.com/JackieZ123430/mgu-store-cn), [`cauliflowermossgrape/idrive7-apps`](https://github.com/cauliflowermossgrape/idrive7-apps), [`DarkMuse1/idrive7-apps-ru`](https://github.com/DarkMuse1/idrive7-apps-ru).

---

## 1. Store, catalog и упаковка пакетов (`64 MiB`, `files[]`, `unit` vs `build` на ГУ)

По спецификации [`robertnisipeanu/mgu-store`](https://github.com/robertnisipeanu/mgu-store/blob/main/docs/PUBLISHING.md) источник в MGU Store может быть в режимах **Releases**, **Catalog** или **Repo tree**. **`mgu-krikun` использует только Repo tree** (ветка `main`, `mgu-repo.json`); второй канал Catalog для этого репо запрещён контрактом.

### Ключевые инженерные правила упаковки

1. **Поставка приложений как `build: "unit"`, а не `build.py` на ГУ.**
   - В `cauliflowermossgrape/idrive7-apps`, `DarkMuse1/idrive7-apps-ru`, `Oussemf/idrive-apps` и `tiraUnderCode23/AQ_MGU` приложения собираются на самом ГУ через Python-скрипт (`kit/tools/build.py`). На машине этот шаг выполняется непривилегированным процессом **без сети** с жёстким потолком **10 минут и 200 МБ RAM**, требует перекачки `shared[]` и порождает проблемы с локальными суффиксами версий (`-ru.1`).
   - В `robertnisipeanu/mgu-store` (`robertn_store`) и у нас в `mgu-krikun` используется **`"build": "unit"`** (source package с готовым деревом `package/` в git): ГУ выполняет только быструю линковку `oap_link.js` против штатного donor-пакета за секунды.
   - При сочетании `components[]` (`build: "unit"`) и секции `apps` в `mgu-repo.json` каждый `unit`-пакет обязан быть перечислен в `apps.exclude` (паттерн `DarkMuse1/idrive7-apps-ru` для `mgu_unified` и наш `pass1_catalog`), иначе Store увидит дублирующийся ID.

2. **Лимит ~64 MiB на скачивание и запрет Git LFS для ГУ.**
   - На мобильном/Wi-Fi аплинке ГУ и внутри воркеров распаковки (`SPLIT_MAX = 64 MiB` в `oap_link.js`, лимиты архивов в `mgu-updater`) пакеты свыше **64 MiB** рискуют оборваться по памяти или таймауту.
   - ГУ скачивает `codeload` tarball ветки без поддержки Git LFS (вместо бинарника приедет текстовый LFS-pointer на 130 байт). В `mgu-krikun` бинарник `jap-node22` (~48 МБ в сжатом виде, 137 МБ ELF) хранится в git нарезанным на `prebuilt/node.part.a*.gz` и склеивается на месте через `assemble.sh`.

3. **Строгий контракт `tools/oap_pack.js` (`files[]`, `npm-shrinkwrap.json`, плоский `ustar`).**
   - Упаковщик `oap_pack.js` на ГУ читает `package/package.json` и безусловно вызывает `pkg.files.forEach(...)`. Если массив `files[]` не задан или пуст, установка падает с `Cannot read property 'forEach' of undefined`; если хотя бы один путь из `files[]` отсутствует на диске — с `missing`.
   - `oap_pack.js` формирует плоский `ustar`-архив с владельцем `0:0`, правами `0644`, фиксированным `mtime`, байтом ОС `GZIP_OS_UNIX = 3` и автоматическим пропуском `.DS_Store` / `._*` (штатный `tar` на ГУ отвергает архивы с macOS extended attributes).
   - Рядом с `package.json` должен лежать согласованный по `version` `npm-shrinkwrap.json` (проверяется нашим `audit-mgu-architecture.py`).

4. **Никакого `node_modules/oap-sdk` в репозитории.**
   - Проприетарный SDK BMW нельзя публиковать (правило `mgu-store` и `idrive7-apps`). На ГУ `oap_link.js` извлекает модули SDK только из заводских пакетов прошивки (`preinstalled_apps` / штатные `oap_*` без флага `mguLocalOnly`).

5. **Явный `"mguHmi": ["ID7"]`, локализованные метаданные `texts.ru` и гигиена ID.**
   - Все компоненты для седьмого поколения обязаны явно указывать `"mguHmi": ["ID7"]` и иконку PNG `<= 128 KiB`.
   - Региональные каталоги (`zhanyce/mgu-apps-zh`, `JackieZ123430/mgu-store-cn`, `DarkMuse1/idrive7-apps-ru`) заполняют `texts.<lang>` (`title`, `description`) на каждом `app` и `tool`, чтобы карточки в Store отображались на языке водителя ещё до установки.
   - **Антипаттерн из раздела `Caution` в `awesome-bmw-mgu`:** нельзя публиковать в своём `catalog.json` чужие базовые системные пакеты (`mgu-render`, `cluster-render`, `mgu-inputgate`) под теми же ID с завышенными версиями (`10.10.10`). В `mgu-krikun` чужая база исключена через `exclude_from_catalog` в `deps.manifest.json`.
   - Для сторонних и GPL-компонентов хорошим тоном считаются манифесты происхождения (`SOURCE.json` в `zhanyce/mgu-apps-zh`, `PORT.json` / `PROVENANCE.json` в `tiraUnderCode23/AQ_MGU`) или приложенный архив исходников релиза (`bube-source-<commit>.tar.gz` в `Drake1804/bube-releases`).

| Практика упаковки и Store | Кто применяет | Статус в `mgu-krikun` |
|---|---|---|
| `build: "unit"` + `apps.exclude` (без `build.py` на ГУ) | `robertnisipeanu/mgu-store`, `DarkMuse1` | **Есть** (`mgu-repo.json` + `pass1_catalog`) |
| Контроль лимита `64 MiB` и защита от LFS-pointer | `mgu-store`, `istt1899/x3` | **Есть** (`pass2`, `pass5`, `node.part.*.gz`) |
| Обязательный `files[]` + синхронный `npm-shrinkwrap.json` | `mgu-store` (`oap_pack.js`), `idrive7-apps` | **Есть** (`simulate-oap-pack.py`, `pass11`) |
| Без `oap-sdk` в git (линковка с donor на ГУ) | Все легальные репо MGU Store | **Есть** (`preflight-store.py`) |
| Запрет re-host базовых tools чужих источников | `awesome-bmw-mgu`, `eroobeeroo/idrive7-apps` | **Есть** (`exclude_from_catalog`) |
| Полные карточки `texts.ru` и `"mguHmi": ["ID7"]` | `DarkMuse1`, `istt1899`, `zhanyce` (для `zh`) | **Есть** (все 7 пакетов репо) |

---

## 2. Tools: `internet` UID, `runas` (никогда `User=` в unit) и контракт `mgu-deploy`

Инструменты (`kind: "tool"`, манифест `component.json`) ставятся транзакционно через `/var/opt/mgu-deploy/mgu-deploy.sh` в `/var/opt/<id>/versions/<ver>/` с симлинком `current/`.

### Критичные правила для фоновых служб на ГУ

1. **Интернет по UID (`"internet": true` + `uids`) и почему запрещён `User=<uid>` в systemd.**
   - Демон `mgu-uplink` маршрутизирует трафик в интернет (таблица маршрутизации `110`) только для разрешённых числовых UID: либо статического списка `"uids": [3922]` (как `3921` в `jap-wireproxy` и `3922` в `krikun-xray`), либо файла `"uids": "state/internet-uids"` (как в `jap-ridetube-d`).
   - На головном устройстве MGU у этих UID **нет записи в `/etc/passwd`**. Директива `User=3922` в `.service` приводит к мгновенному отказу `systemd` 237 (`status=217/USER`) на старте юнита.
   - **Эталонное решение (`JustAnotherPU/mgu-apps` → `jap-runas`):** юнит стартует от `root` (чтобы отработал `ExecStartPre`), а `ExecStart` вызывает крошечный статический `linux/amd64` ELF-хелпер (`jap-runas` на Go или наш `krikun-runas` на C), который делает `setgroups(0, NULL)` → `setgid(uid)` → `setuid(uid)`, проверяет невозможность возврата `setuid(0) != 0` и делает `execv`.

2. **Ловушка `RuntimeDirectory=` в systemd 237 на MGU.**
   - Как зафиксировано на реальной машине в `jap-wireproxy/setup.sh`, systemd 237 на ГУ при каждом запуске команды переприсваивает корень `/run/<service>` (`RuntimeDirectory`) обратно пользователю юнита (`root:root`), даже если `ExecStartPre` менял владельца.
   - Поэтому демон под UID `3921`/`3922` не должен писать в корень `/run/<service>` или делать там `mkdir`: `setup.sh` (под `root`) обязан создавать вложенный каталог `/run/<service>/s`, проверять `[ ! -L "$d" ]` и выставлять `chown <uid>:<uid> /run/<service>/s && chmod 0700 /run/<service>/s`.

3. **Транзакция установки, `idle`-режим, `check.sh`, `recmgr` и `LimitCORE=1`.**
   - `mgu-deploy` проверяет, что через **10 секунд** после старта все юниты компонента находятся в состоянии `active` и не ушли в рестарт, после чего запускает `check[]` из `current/`. Любая ошибка вызывает автоматический **rollback** к предыдущей версии.
   - Если пользовательский конфиг ещё не загружен (например нет `wireproxy.conf` или `config.json`), `start.sh` **не должен завершаться с ошибкой**: он переходит в тихий цикл ожидания (`idle: ...`) с `trap ... TERM INT`, удерживая сервис `active`.
   - Скрипт `check.sh` обязан быть полностью **оффлайновым** и проверять запускаемость ELF-бинарников / синтаксис модулей относительно `MGU_TOOL_CURRENT` или `$(dirname "$0")`.
   - Все исполняемые ELF-файлы сторонних процессов должны попадать в белый список BMW crash handler (автоматически по имени бинарника из `files[]` либо через `crashNames`, как `"crashNames": ["ytdec"]`), иначе падение воркера перезагрузит всё ГУ.
   - В systemd-юнитах `JustAnotherPU` и `mgu-deploy` ставится **`LimitCORE=1`** (а не `0`): при pipe `core_pattern` ядро Linux на MGU игнорирует лимит `0`, но пропускает дамп при `1` (защита от рекурсии), не будя штатный crash handler.
   - Для запуска новых программ всегда использовать путь `/var/opt/<id>/current/...`, а не `versions/<ver>/...` (старые версии удаляются при повторном обновлении).

| Практика для `tools` | Кто применяет | Статус в `mgu-krikun` |
|---|---|---|
| `"internet": true` + `uids` + `runas` вместо `User=` | `JustAnotherPU/mgu-apps` (`jap-wireproxy`) | **Есть** (`krikun-runas` C ELF + `pass6`/`pass8`/`pass11`) |
| Проверка, что в `prebuilt/` нет macOS `Mach-O` | Собственный опыт инцидентов на Mac | **Есть** (`audit-mgu-architecture.py`) |
| Оффлайновый `check.sh` + `idle`-режим без конфига | `jap-wireproxy`, `jap-node22`, `jap-ridetube-d` | **Есть** (`krikun-xray@0.0.8`: без `file(1)`, прямой `xray version` + ELF magic fallback) |
| Согласованность `recmgr`, `crashNames`, `LimitCORE=1` | `mgu-store` (`mgu-deploy`), `ridetube` | **Есть** (`jap-ridetube-d`, `validate-component-json.py`) |
| Подкаталог `/run/<svc>/s` с `chown <uid>` в `setup.sh` | `jap-wireproxy` (systemd 237 fix) | **Есть** с `krikun-xray@0.0.6` (`setup.sh`: `! -L`, `chown 3922:3922`) |

---

## 3. Apps: `mgu-app.json`, `modules[]` и правила кавычек `oap_link.js`

На ГУ исходный пакет приложения (`mgu-app.json`) собирается встроенным линковщиком [`tools/oap_link.js`](https://github.com/robertnisipeanu/mgu-store/blob/main/tools/oap_link.js) (работает на штатном **Node 8** без внешних зависимостей).

### Почему кавычки в `require(...)` решают судьбу сборки на ГУ

В `oap_link.js` функция поиска зависимостей модуля устроена буквально так:

```javascript
function requiresOf(source) {
    const names = new Set();
    const re = /require\('([^']+)'\)/g;
    // ...
}
```

Из этой регулярки вытекают два жёстких закона для всех `unit`-приложений:

1. **Внутренние модули приложения (`modules[]`) и `sdk[]` — строго в одинарных кавычках:**
   - `oap_link.js` присваивает каждому файлу из `modules[]` бандл-имя `./<basename>.js` (ID начиная с `10000`, точка входа — строго `modules[0]`).
   - Внутри модулей вызов соседа пишется как `require('./yt.js')` (с расширением `.js`, плоское имя без вложенных подпапок), а SDK — точным именем из массива `sdk[]` (`require('oap-sdk/src/core/OnlineApp.js')`).
2. **Файлы рантайма на диске вне бандла (`./kit/...`) — строго в двойных кавычках:**
   - Если написать `require('./kit/mgu.js')` в одинарных кавычках, `oap_link.js` захватит эту строку, не найдёт `./kit/mgu.js` ни в `modules[]`, ни в `sdk[]`, ни в `builtinModules`, и прервёт установку с фатальной ошибкой `not an app module, a Node builtin or an sdk name in mgu-app.json`.
   - Запись в **двойных кавычках** `require("./kit/mgu.js")` прозрачно проходит сквозь `oap_link.js` и исполняется уже во время работы приложения штатным загрузчиком Node.js с диска (`package/javascript/kit/`).
   - **Важный нюанс двух режимов `oap_link` (подробно в [`docs/mgu-ecosystem-patterns.md`](mgu-ecosystem-patterns.md)):** при установке готового `.tgz` из релиза `catalog` (без `mgu-app.json`) отрабатывает `oap_link.preparePackage()`, который сам создаёт `node_modules/oap-sdk` на диске для `kit/mgu.js`. А при установке напрямую с ветки `branch:main` через `"build": "unit"` вызывается `oap_link.build()`, который **не создаёт** `node_modules/oap-sdk` и валится на post-check `needsSdk()`, если `kit/mgu.js` вызывает `require('oap-sdk')`. В `DarkMuse1/idrive7-apps-ru` для уже собранных App Kit пакетов на ветке вместо `"build": "unit"` используется короткий Node 8 упаковщик `tools/prebuilt_package.js` (`"build": { "node": "..." }`), переводящий ветку в штатный режим `preparePackage()`.

### Дополнительные инварианты `mgu-app.json` и среды OAP

- **Тройное равенство версий и строгий semver:** `mgu-app.json` проверяет регуляркой `/^\d+\.\d+\.\d+$/` (никаких `-ru.1` или `v1.0.0`) и требует точного совпадения `id` и `version` с `<tree>/package.json` (а для каталога — и с `app.json`).
- **Точка входа:** `modules[0]` обязан указывать на файл `main` из `package/package.json` (например `"package/javascript/app.js"` — пути в `modules[]` считаются от `apps/<id>/`).
- **Доступ в сеть для UI-приложения:** флаг `"internet": true` в `mgu-app.json` автоматически конвертируется линковщиком в `"mguInternet": true` в итоговом `package.json`.
- **Совместимость с Node 8.16.2 (2019 MGU — вплоть до 8.9.4):** OAP-контейнер BMW крутится на системном Node 8, даже если на ГУ установлен `jap-node22`. В коде UI нельзя использовать синтаксис ES2020+ (`?.`, `??`), глобальный `URL` (нужно `require('url').URL`), `EventEmitter.prototype.off` (нужно `removeListener`) и `fs.mkdirSync(p, { recursive: true })` (баг `#114` в `idrive7-apps`).

---

## 4. Линейка RideTube: связка `service + app`, `vendor/jpeg-js` в git, `jap-node22`

Подробное сравнение всех 4 независимых YouTube-движков и 25+ форков вынесено в [`docs/mgu-youtube-landscape.md`](mgu-youtube-landscape.md). Ниже — инженерные практики, сделавшие архитектуру `JustAnotherPU/ridetube` (и доработки `istt1899/x3`) де-факто стандартом на iDrive 7:

1. **Двухконтурная архитектура `jap_ridetube` (OAP UI) + `jap-ridetube-d` (daemon).**
   - Приложение `jap_ridetube` отвечает только за экран, шайбу iDrive (`mgu-inputgate`), тач и состояние вождения, общаясь с демоном через UNIX-сокет `/run/jap-ridetube-d/ctl.sock`.
   - Демон `jap-ridetube-d` работает под `User=root` ради SOME/IP-сессии со штатным `MediaPlayer` BMW (руль, громкость, штатный аудиофокус), декодирует H.264 аппаратно на GPU через `ytdec` (Intel Media SDK → `/dev/shm/mgu-video-ridetube` → видеослой `mgu-render`), а все походы в сеть (`ytfetch.py` / `ytdlp.pyz` на `mgu-python` и `thumb.js` на `jap-node22`) сбрасывает на собственный непривилегированный `fetch`-UID (`"uids": "state/internet-uids"`).

2. **Разделение ролей системного Node 8 и `jap-node22` (`glibc 2.17`).**
   - Управляющий процесс `ytd.js` в `jap-ridetube-d.service` запускается штатным `/usr/bin/node --max-http-header-size=65536` — флаг обязателен, так как `youtube.com/tv` возвращает ~11 КБ HTTP-заголовков, а лимит 8 КБ в Node 8.14+ рвёт соединение с `HPE_HEADER_OVERFLOW`.
   - Современный TLS, Mozilla CA roots, декодирование превью (`thumb.js`) и JS-челленджи `yt-dlp` выполняются через отдельный пакет **`jap-node22`** (`22.23.4`). Официальные сборки Node 22 требуют `glibc >= 2.28` и на MGU (`glibc 2.27`, нет `/lib64`) не стартуют; поэтому `JustAnotherPU/mgu-apps` использует сборку `unofficial-builds` `linux-x64-glibc-217` с пропатченным ELF-интерпретатором `/lib/ld-linux-x86-64.so.2`.

3. **Буферизация активного видео в RAM (`tmpfs`), а не на eMMC.**
   - Чтобы просмотр видео не изнашивал напаянную флеш-память ГУ, `ExecStartPre` в `jap-ridetube-d.service` монтирует `/run/jap-ridetube-media` в `tmpfs` (`size=256m,mode=0711,nosuid,nodev,noexec`), а `ExecStopPost` размонтирует и освобождает память при остановке.

4. **Вендоринг `vendor/jpeg-js` прямо в git и проверка в `check.sh`.**
   - Все файлы из `component.json -> files[]` должны физически быть закоммичены в git внутри папки компонента (глобальные правила `.gitignore` на `vendor/` или `build/` часто ломают упаковку tool-артефакта).
   - В `ridetube` и `Oussemf`/`istt1899` скрипт `tools/vendor_jpeg.sh` скачивает `jpeg-js@0.4.4` с проверкой `sha512` и кладёт `decoder.js` + `LICENSE` в `native/jap-ridetube-d/vendor/jpeg-js/`, а `check.sh` при деплое оффлайн проверяет связку `jap-node22` + `decoder.js` + `thumb.js`.

5. **Практики форка `istt1899/x3` (`media/core`) для РФ и кириллицы.**
   - **Кириллические атласы шрифтов (`bake_cyrillic.py`):** предзапекание глифов `U+0400..U+04FF` из лицензионного Ubuntu TTF в JSON-атлас с жёсткой проверкой бюджета высоты текстуры GPU (`atlasH <= 2048`).
   - **Безопасный `proxy.js` под Node 8/22:** поддержка `http://` и `socks5://` / `socks5h://` с ограничением размера ответа прокси (`cap`), очисткой слушателей через `removeListener` и передачей прокси-реквизитов дочерним процессам строго через `stdin` JSON (а не `argv` или `env`, которые видны всем процессам в `ps` на ГУ). Авторские наработки `proxy.js` позже вошли в основной `JustAnotherPU/ridetube`.

---

## 5. Прокси на ГУ: паттерн `jap-wireproxy` vs наш `krikun-xray`

Полная карта прокси-решений разобрана в [`docs/mgu-xray-landscape.md`](mgu-xray-landscape.md). На ГУ MGU в ядре **отсутствует драйвер `tun`** (разрешены только подписанные модули BMW), поэтому любой обход строится как **userspace-демон с локальным SOCKS5 на `127.0.0.1`**.

Почему в `mgu-krikun` запрещён `wireproxy` ([`CONSTRAINTS.md`](../CONSTRAINTS.md)): протокол WireGuard блокируется ТСПУ в РФ, тогда как **Xray-core (VLESS + XTLS-Reality)** проходит штатно. При этом точка стыковки с экосистемой одна и та же — строка `proxy = socks5://127.0.0.1:1080` в `/var/opt/mgu-updater/updater.local.conf`, которую прозрачно читают и Store, и `jap-ridetube-d`, и `jap-filmix-d` без жёсткой `requires`-зависимости между пакетами.

| Критерий | `jap-wireproxy` (`JustAnotherPU/mgu-apps`) | `krikun-xray` + `krikun_seti` (`mgu-krikun`) |
|---|---|---|
| Протокол туннеля | WireGuard в userspace (`127.0.0.1:1065`) — режется ТСПУ в РФ | **VLESS / Reality** (`Xray-core`, `127.0.0.1:1080`) — работает в РФ |
| Управление и импорт конфига | Только вручную по SSH (`root:3921 0640`) | **Без SSH:** русское приложение «Krikun: сеть» на экране ГУ + импорт с USB (`KRIKUN/xray.json`) + переключение `updater.local.conf` |
| Понижение привилегий | `jap-runas 3921` (Go ELF) | `krikun-runas 3922` (компактный C ELF) |
| Права на `/run/<svc>/s` (systemd 237) | `setup.sh` делает `mkdir`, проверку `! -L`, `chown 3921:3921`, `0700` | **Внедрено в `0.0.6`** (`setup.sh`: `! -L`, `chown 3922:3922`) |
| Память Go-рантайма | `GOGC=30 GOMEMLIMIT=48MiB` (26–29 МБ вместо 166 МБ на авто) | **Внедрено в `0.0.6`** (`GOGC=30 GOMEMLIMIT=96MiB`) |
| Pre-flight конфига перед стартом | `wireproxy -n` (configtest), `mtime` reload, запрет `0.0.0.0`, проверка занятости порта | **Частично в `0.0.6`** (`xray run -test -c`; стоит добавить отслеживание `mtime` и проверку порта `:1080`) |
| Реакция на `mgu-uplink` и DNS | Следит за `/run/mgu-uplink/status.json`, профили `HOME_SSID`/LTE, DoH-резолвер `resolve.js` | Опирается на прямой IP сервера в экспорте Amnezia и `socks5h://` резолв на VPS |

---

## 6. Preflight и CI: что делают топ-репозитории

Ошибки упаковки на ПК стоят дорого на машине (невидимая плитка, откат транзакции `mgu-deploy`, рестарт-шторм сервиса). Зрелые репозитории экосистемы выстроили многослойный CI:

1. **`cauliflowermossgrape/idrive7-apps` (`app-tests.yml`):**
   - Гоняет синтетические тесты всех приложений и записанных CAN/SOME-IP фикстур на Node 22 + Python 3.12 (без SDK и без автомобиля).
   - **Главная находка — отдельный джоб `node8-runtime` (`node-version: '8.16.2'`):** проверяет рантайм на точной версии Node головного устройства, чтобы функции из Node 10+ не просочились в машину.
   - Собирает локализованные стейджи с `--preview-only` (без SDK) и проверяет покрытие всех строк глифами шрифтовых атласов (`test_zh.js`, `test_import_diagnostic_ru.py`).

2. **`robertnisipeanu/mgu-store` (`versions.yml`, `release.yml`, `installer.yml`):**
   - Все GitHub Actions жёстко прибиты к полным SHA коммитов (`actions/checkout@3d3c42e5...`) с `persist-credentials: false`.
   - На каждый PR `release.js versions HEAD^1` проверяет неизменность базовых версий и заполненность `CHANGELOG` (`## Unreleased`), а публикация `catalog` атомарно штампует версии по `SOURCE_DATE_EPOCH`.

3. **`Oussemf/idrive-apps` (`validate.yml`):**
   - Короткий практичный пайплайн для форков RideTube: `python kit/tools/build.py --sdk-free <app>` → unit-тесты `kit/tools/test_*.js` (включая `test_parked.js`, `test_life.js`) → установка `ffmpeg` и прогон тестов демона `native/jap-ridetube-d/test/test_*.js` + `test_ytfetch.py`.

4. **`istt1899/x3` (`media-runtime.yml`, `media-publication.yml`):**
   - **Эмуляция ГУ в изолированном Linux namespace:** скачивает опубликованный `.tgz` по SHA-256, сверяет права и хэши каждого файла с `component.json`, поднимает `sudo unshare --mount --net` (оставляя только интерфейс `lo`, `tmpfs` на `/var/opt` и симлинк `/usr/bin/node`) и исполняет реальный `check.sh` пакета оффлайн, сохраняя JSON-артефакт доказательства (`evidence`).
   - Второй workflow (`media-publication.yml`) скачивает репозиторий через `codeload.github.com` без токена и проверяет доступность всех URL и SHA-256 в `catalog.json`.

5. **`zhanyce/mgu-apps-zh` (`tools/build.py check`):**
   - Единая оффлайн-команда валидации каталога на 73 пакета: сверяет SHA-256 входных архивов, тройные semver-версии, наличие лицензий, `SOURCE.json` и глифы локализации.

6. **Что уже есть у нас в `mgu-krikun`:**
   - Локальный `python3 scripts/preflight-store.py` (11 проходов: `validate-mgu-app.py`, `validate-component-json.py`, `simulate-hu-tool.py`, `simulate-oap-pack.py`, `audit-mgu-architecture.py`, `audit-store-5pass.py`, `audit-systemd-units.py`, `audit-checks-on-hu-mock.py`) уже ловит специфичные для ГУ баги лучше большинства форков (Mach-O, `User=3922`, одинарные кавычки `./kit/`, `files[]`, `shrinkwrap`, лимит 64 MiB).
   - Добавлен `.github/workflows/preflight.yml`, однако на чистом облачном раннере GitHub у него есть узкое место: `simulate-oap-pack.py` требует `node` и локальный кэш `.cache/artifacts/mgu-deploy@0.8.29.tgz` (папка `.cache/` не в git).

---

## 7. Чеклист: что позаимствовать в `mgu-krikun`

Ниже — 8 конкретных улучшений из практики `mgu-store`, `jap-wireproxy`, `ridetube`, `idrive7-apps` и `DarkMuse1` (детали путей также см. в [`docs/mgu-ecosystem-patterns.md`](mgu-ecosystem-patterns.md)), не нарушающих [`CONSTRAINTS.md`](../CONSTRAINTS.md). Базовые фиксы `/run/krikun-xray/s`, `GOGC=30 GOMEMLIMIT=96MiB` и `xray run -test` уже внесены в `krikun-xray@0.0.6`.

- [ ] **1. Перевести App Kit приложения на канале `branch:main` в режим `preparePackage` (`mgu-repo.json`):** заменить `"build": "unit"` (где `oap_link.build` конфликтует с `require('oap-sdk')` внутри `kit/mgu.js` и игнорирует `app.json`) на короткий Node 8 упаковщик по образцу `DarkMuse1/idrive7-apps-ru` (`tools/prebuilt_package.js`), чтобы и `main`, и `catalog` ставились единообразно через `oap_link.preparePackage()`.
- [x] **2. Убрать `file -b` из `tools/krikun-xray/check.sh`:** с `0.0.7` — `xray version`, `krikun-runas` (rc=2) и fallback ELF magic без `file(1)` (mock `pass7` на Mac).
- [x] **3. Права статуса и `mtime` в `krikun-xray@0.0.8`:** `/run/krikun-xray/s` → `0755`, `state` → `0644`, перезагрузка по `mtime` `config.json`; в backlog — проверка занятости `:1080` до старта.
- [ ] **4. Выделенный интернет-UID и защита сокета в `jap-filmix-d` (паттерн `jap-ridetube-d/ytd.js`):** реализовать `pickFetchUid` с записью в `state/internet-uids` + `/var/opt/mgu-uplink/uids.d/jap-filmix-d` и чтением DNS из `/run/mgu-uplink/lease.json` (чтобы прямой режим работал без root-блокировки `mgu-uplink`), а права `ctl.sock` сузить с `0666` до `<app_uid>:root 0600` (`0660 root:tm_oap_app`).
- [ ] **5. Capability `mguNeeds: ["renderer"]` вместо жёсткого пина рендерера (`krikun_seti`, `filmix_promax`):** по образцу `mgu-store` и `iteriodev_seats` запрашивать способность `"renderer"`, чтобы 2D-приложения работали поверх уже установленного `mgu-render` или `idrive7-renderd`.
- [ ] **6. Автономность `.github/workflows/preflight.yml` и джоб `Node 8.16.2` (паттерн `idrive7-apps`):** добавить `actions/setup-node@v4`, отвязать `scripts/simulate-oap-pack.py` от локального `.cache/artifacts/mgu-deploy@*.tgz`, и добавить шаг проверки всех JS-модулей приложений на реальном **Node 8.16.2** (или `check_node8.sh` из `ridetube`).
- [ ] **7. Дополнительный systemd hardening и лицензии в `krikun-xray`:** добавить в `krikun-xray.service` директивы `ProtectKernelTunables=yes`, `ProtectKernelModules=yes`, `ProtectControlGroups=yes`, `LimitCORE=1`, явный `"krikun-xray-ctl"` в `recmgr`, а в `files[]` — `LICENSE.xray` (`MPL-2.0`) и `COPYING.krikun-runas` (`GPL-3.0-or-later`).
- [ ] **8. Автопроверка кириллических глифов при сборке UI (паттерн `idrive7-apps` / `zhanyce` / `istt1899`):** сверять в preflight все русские строки `apps/*` и `locales/ru.json` с символами шрифтовых атласов `package/javascript/kit/fonts/*.json`, исключая квадраты вместо букв на экране ГУ.

---

## Приложение: текущие версии пакетов `mgu-krikun` (`main`)

| Компонент (`id`) | Тип | Версия | Назначение |
|---|---|---|---|
| `jap-node22` | `tool` | `22.23.4` | Node.js 22 (`glibc 2.17`) для сервисов YouT и Filmix (сборка из `node.part.*.gz`) |
| `krikun-xray` | `tool` | `0.0.8` | Локальный клиент Xray (VLESS/Reality) на `127.0.0.1:1080`, запуск через `krikun-runas` (`uid 3922`) |
| `krikun_seti` | `app` (`unit`) | `0.0.5` | Русский интерфейс «Krikun: сеть» (импорт конфига с USB, управление `updater.local.conf`, тест IP) |
| `jap-ridetube-d` | `tool` | `0.5.6` | Сервис YouT (`ytdec` GPU декод + `MediaPlayer` BMW + `vendor/jpeg-js` + прокси Store) |
| `jap_ridetube` | `app` (`unit`) | `0.6.6` | Клиент YouT (патчи RU по умолчанию, VIM без дисклеймера, `pause`/`resume`) |
| `jap-filmix-d` | `tool` | `0.0.3` | Сервис Filmix |
| `filmix_promax` | `app` (`unit`) | `0.0.4` | Клиент FilmixProMax |

Внешние базовые компоненты (ставятся на ГУ **до** наших `apps` из дефолтных источников Store): `mgu-deploy` `0.7.0+`, `mgu-updater` `0.8.40+`, `mgu-python` `1.0.2+`, `mgu-render` `0.6.11+`, `mgu-inputgate` `1.0.0+`, `idrive7-renderd` `2.1.10+`.

Команды сопровождения:

```bash
python3 scripts/preflight-store.py          # обязательный preflight (11 проходов) перед push в main
python3 scripts/preflight-store.py          # обязательно перед push (11 проходов)
```
