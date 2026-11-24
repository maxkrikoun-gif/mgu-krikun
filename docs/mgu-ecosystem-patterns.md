# Паттерны экосистемы MGU / iDrive 7: разбор upstream-репозиториев

Сравнительный анализ соседних репозиториев под BMW MGU (iDrive 7 / iDrive 8) и их правил упаковки, `mgu-deploy`, `oap_link`, `systemd` + `runas`, сетевых UID и проверок перед установкой на ГУ.

## Исследованные репозитории

1. **[JustAnotherPU/mgu-apps](https://github.com/JustAnotherPU/mgu-apps)** — эталон сетевого userspace-демона с привилегированным стартом и сбросом root без записи в `/etc/passwd` (`tools/jap-wireproxy`: `jap-runas`, `setup.sh`, `start.sh`, `check.sh`, `jap-wireproxy.service`) и упаковки тяжёлого runtime (`tools/jap-node22`). *(Сам стек WireGuard/wireproxy в `mgu-krikun` запрещён по [CONSTRAINTS.md](../CONSTRAINTS.md) — берём только системные паттерны `runas`, `systemd`, `RuntimeDirectory`, `check.sh`.)*
2. **[robertnisipeanu/mgu-store](https://github.com/robertnisipeanu/mgu-store)** — первоисточник правил установки на ГУ: `tools/oap_link.js`, `tools/oap_pack.js`, `deploy/hu`, `deploy/unit/mgu-deploy.js`, `native/mgu-updater/js/{sources,uids,build}.js`, `docs/PUBLISHING.md`, эталон source-приложения `apps/robertn_store`.
3. **[JustAnotherPU/ridetube](https://github.com/JustAnotherPU/ridetube)** — эталон пары «OAP-приложение App Kit + root-демон с собственным динамическим internet UID» (`apps/jap_ridetube` + `native/jap-ridetube-d`: `vendor/jpeg-js`, `uids: "state/internet-uids"`, `tools/release.py`, `tools/check_node8.sh`).
4. **[DarkMuse1/idrive7-apps-ru](https://github.com/DarkMuse1/idrive7-apps-ru)** и **[cauliflowermossgrape/idrive7-apps](https://github.com/cauliflowermossgrape/idrive7-apps)** — раскладка `mgu-repo.json` с тремя типами сборки приложений: `build.python` с `shared` (App Kit), `build: "unit"` с `mgu-app.json` (`third_party/iteriodev-seats/app`), и `tools/prebuilt_package.js` (`build.node` для готового пакета без `build.py` на ГУ).

---

## 1. Сравнение технических решений по узлам

### 1.1. Сетевой демон без `User=` в systemd (`jap-wireproxy` vs `krikun-xray`)

На BMW MGU `mgu-uplink` выпускает в интернет **только числовые UID** из `/var/opt/mgu-uplink/uids.d/<id>` (никогда `uid 0`), а штатный `systemd 237` отказывает в `User=3922`, потому что этого UID нет в `/etc/passwd`.

- **Как сделано в `JustAnotherPU/mgu-apps` (`tools/jap-wireproxy`):**
  - `component.json`: `"internet": true, "uids": [3921]` — `mgu-deploy` пишет `3921\n` в `/var/opt/mgu-uplink/uids.d/jap-wireproxy`.
  - `runas/main.go` (`jap-runas`): статический Go ELF (`CGO_ENABLED=0 GOOS=linux GOARCH=amd64`, `-trimpath -ldflags "-s -w"`): `syscall.Setgroups(nil)` → `Setgid(uid)` → `Setuid(uid)` → проверка `Setuid(0) != nil` → `syscall.Exec(...)`. При плохих аргументах выходит с кодом `2`.
  - `systemd/jap-wireproxy.service`: **без `User=`**; `ExecStartPre=/bin/sh .../setup.sh` (как `root`), `ExecStart=.../jap-runas 3921 .../start.sh`.
  - **`NoNewPrivileges=yes` + `runas` совместимы:** `NoNewPrivileges=yes` блокирует *повышение* привилегий через setuid-бит при `execve`, но **не мешает `root` сбрасывать привилегии**, если в `CapabilityBoundingSet=` оставлены `CAP_CHOWN CAP_FOWNER CAP_SETUID CAP_SETGID` (`CAP_SETGID` обязателен и для `setgroups(nil)`). Дополнительно включены `ProtectKernelTunables=yes`, `ProtectKernelModules=yes`, `ProtectControlGroups=yes`.
  - **Нюанс `systemd 237` с `RuntimeDirectory=` (`setup.sh`):** на MGU `systemd 237` после `ExecStartPre` возвращает владельца `/run/<name>` обратно `root:root 0755`. Поэтому `setup.sh` создаёт **подкаталог** `/run/jap-wireproxy/s` (с проверкой `[ ! -L ]`) и отдаёт его `chown 3921:3921`. Сам демон пишет рантайм-состояние только внутрь `s/`.
  - **`check.sh` без внешних утилит:** никаких вызовов `file(1)` (`libmagic` может отсутствовать в Yocto на ГУ). Только прямой запуск из `d=$(cd "$(dirname "$0")" && pwd)`: `"$d/wireproxy" -v | grep ...` и проверка кода возврата `jap-runas` (`[ "$rc" -eq 2 ]`).
  - **`start.sh`:** следит за `mtime` конфига (горячее перечитывание без рестарта unit), проверяет занятость порта `127.0.0.1:<port>` через `/usr/bin/node` до старта (`EADDRINUSE` не вызывает рестарт-шторм systemd), прогоняет `configtest`, проверяет `/run/mgu-uplink/status.json` и резолвит домены через DoH / `/run/mgu-uplink/lease.json` (системный резолвер ГУ ничего не отвечает).

### 1.2. Два режима `tools/oap_link.js` и почему нельзя смешивать App Kit с `mgu-app.json`

В `robertnisipeanu/mgu-store/tools/oap_link.js` и `deploy/unit/mgu-deploy.js` реализованы **два несовместимых конвейера** подготовки OAP-приложений на ГУ:

1. **Bundle mode (`oap_link.build` — по `mgu-app.json`, т.е. `"build": "unit"`):**
   - Используется в `apps/robertn_store` и `third_party/iteriodev-seats/app`.
   - `readManifest`: `schema === 1`, `id` (`^[A-Za-z0-9][A-Za-z0-9._-]*$`), строгий `version` `x.y.z`, совпадение `name@version` с `<tree>/package.json`, все `modules` — существующие `.js` (первый — точка входа, все `basename` уникальны), непустой `sdk`.
   - `nodeCheck`: каждый модуль компилируется на ГУ через `new vm.Script(Module.wrap(text))` под **Node 8**.
   - `requiresOf`: ищет **строго одинарные кавычки** `/require\('([^']+)'\)/g` по **всем** файлам из `modules[]` **без вырезания JSDoc/комментариев**. Каждое имя обязано быть `'./<basename>.js'` из `modules[]`, строкой из `sdk[]` или builtin Node 8.
   - **Критическая ловушка post-check (`mgu-deploy.js:2969`):** сразу после `link.build(a.dir, out)` установщик вызывает `b = validateArtifact(out, stage)` и требует `!b.prepare`. Поле `b.prepare` вызывает `linker().needsSdk(pkgDir)`, которое возвращает `true`, если **любой** не-browserify `.js` внутри `package/` содержит `require('oap-sdk')` или `require("oap-sdk")`, а `node_modules/oap-sdk` отсутствует. Так как `link.build()` **не генерирует** `node_modules/oap-sdk` (он линкует SDK только внутрь `javascript/app.js`), наличие в `package/javascript/kit/mgu.js` строки `const { OnlineApp, logging } = require('oap-sdk')` приводит к отказу `mgu-deploy`:
     `the prepared package is not <id> <version>` (и `Cannot find module 'oap-sdk'` в рантайме, даже если обойти `requiresOf` двойными кавычками `require("./kit/mgu")`).
   - **Чтение метаданных в `branch:main` (`mgu-updater/js/sources.js:467`):** для `build: "unit"` магазин читает **только `mgu-app.json`** (и переопределения из `mgu-repo.json`), полностью игнорируя `app.json` и `apps/<id>/icon.png` (иконка берётся из `<tree>/rhmiData/application.json`). Поэтому `iteriodev_seats` кладёт `title`, `description`, `texts.ru`, `requires`, `needs`, `mguHmi`, `uninstallable` прямо в `mgu-app.json`.

2. **Module mode (`oap_link.preparePackage` — пакет OAP без `mgu-app.json` и без `"build": "unit"` в `catalog.json`):**
   - Используется в `JustAnotherPU/ridetube` (`tools/release.py`) и в нашем `scripts/catalog-release.py` для `dist/catalog/`.
   - В архиве `<id>@<version>.tgz` лежит `package/package.json` (или плоское дерево) **без `mgu-app.json` и без `node_modules/oap-sdk`**.
   - На ГУ `mgu-deploy.js` видит `needsSdk(pkgDir) === true`, запускает `oap_link.preparePackage()` и **генерирует `node_modules/oap-sdk/index.js`** из стокового BMW-донора (`sdkModule`). Все файлы `javascript/*.js` и `javascript/kit/*.js` остаются обычными CommonJS-модулями на диске — работают любые `require('./kit/mgu')`, `require('./fx.js')`, любые кавычки и JSDoc-комментарии.
   - Как сделать так же на канале `branch:main` (`mgu-repo.json`) без тяжёлого Python `build.py`: паттерн `DarkMuse1/idrive7-apps-ru` (`tools/prebuilt_package.js` — `build: { "node": "...", "output": "..." }`) либо компактный Node 8 скрипт на базе `oap_pack.js`, пакующий `apps/<id>/package/` в `$MGU_OUT/<id>@<version>.tgz` (без `mgu-app.json`). Тогда и `catalog`, и `branch:main` идут через единый `preparePackage()` (module mode), а `sources.js` штатно читает `app.json` и `icon.png`.

### 1.3. `tools/oap_pack.js` и схема `validateTool` в `deploy/unit/mgu-deploy.js`

- **`oap_pack.js`:**
  - `package.json` обязан иметь непустой массив `files[]`, и каждый элемент `files[]` обязан существовать в `package/` (иначе `forEach of undefined` или `files[] names <entry>, which is missing`).
  - Автоматически проставляет `"mguLocalOnly": true`, пропускает `.DS_Store` и `._*` (macOS xattr ломают `tar` на ГУ), выставляет `0:0`, `0644`, фиксированный `MTIME` и `GZIP_OS_UNIX = 3`.
- **`mgu-deploy.js` (`validateTool`) до установки проверяет:**
  - `id`: только `^[a-z0-9][a-z0-9-]*$` (строчные буквы, цифры, дефис; в отличие от `app`, `_` и `.` запрещены).
  - `kind === "tool"`, `version` строго `^\d+\.\d+\.\d+$`.
  - `files[]`: `safeRel(path)` (без `/`, `..`, `\`), восьмеричный `mode` (`^[0-7]{3,4}$`), `sha256` (считает `deploy/hu artifact`).
  - `check[]`: массив строк, где **`check[0]` обязан точно совпадать с одним из `files[].path`**. Запускается из `/var/opt/<id>/current` после старта сервисов; при ненулевом коде `mgu-deploy` откатывает версию.
  - `internet: true`: требует `uids` — либо непустой массив целых `> 0` (`[3922]`), либо `safeRel`-путь к файлу внутри `/var/opt/<id>/` (`"state/internet-uids"`).
  - `recmgr[]` и `restart[]`: не могут содержать `oapcontroller` / `oapcontroller.service`. При этом `recmgrNamesOf(c)` сам добавляет базовые имена всех `.service`/`.socket` из `units[]` в `/etc/recmgr-restartlist.conf`, а исполняемые ELF из `files[]` и имена из `crashNames[]` — в `[Whitelist]` crash-handler (`dlt-cdh`), плюс ко всем unit'ам добавляется drop-in `LimitCORE=1`.
  - `activate` / `deactivate`: только `["node", ...]` или `[<исполняемый файл из files[] с mode & 0111>, ...]` без `..` (никогда не через shell).
  - `mguHmi`: непустой массив уникальных значений из `["ID7", "ID8"]`.

### 1.4. `JustAnotherPU/ridetube` — `vendor/jpeg-js`, динамический `state/internet-uids` и Node 8 gate

- **Вендоринг JS-зависимостей демона (`native/jap-ridetube-d/tools/vendor_jpeg.sh`):**
  - На ГУ нет системного декодера JPEG и нет `npm install`. Скрипт скачивает tarball с `registry.npmjs.org`, сверяет зашитый `SHA512`, извлекает только `decoder.js` + `LICENSE`, пишет `VERSION`, а `component.json` явно перечисляет каждый файл `vendor/jpeg-js/*` в `files[]`. `check.sh` офлайн проверяет `require('$d/vendor/jpeg-js/decoder.js')` под `jap-node22`.
- **Динамический `uids: "state/internet-uids"` без `User=` в systemd (`ytd.js` + `mgu-updater/js/uids.js`):**
  - Если демон обязан работать от `User=root` (например, ради SOME/IP к BMW MediaPlayer и `chown` сокета под UID приложения), он **не может** ходить в интернет напрямую из `uid 0`.
  - Паттерн `pickFetchUid` (`ytd.js:268`, по образцу `mgu-updater/js/uids.js`): читает `/etc/passwd`, `/etc/group`, `/var/opt/public/oap`, `uids.txt`, `/var/opt/mgu-uplink/uids.d/*`, `mgu-updater/state/uids.json` и диапазоны `usableUidsAndGids` из `config/base.json` запущенного MainApp; выбирает первый свободный UID выше диапазона OAP-приложений; сохраняет его в `state/uids.json`, пишет в **`state/internet-uids` И сразу в `/var/opt/mgu-uplink/uids.d/<tool-id>`**; все сетевые запросы выполняет в дочернем процессе с `{ uid: fetchUid, gid: fetchUid }` и DNS-резолвером из `/run/mgu-uplink/lease.json` (`uplinkLookup`).
  - Сокет управления `ctl.sock` запирается на `<app_uid>:root 0600` (по записи в `/var/opt/public/oap/oap_12201/data/apps/<app>.json`), с откатом к `0660 root:tm_oap_app` только пока UID приложения неизвестен.
- **Проверка совместимости с системным Node 8 (`tools/check_node8.sh`) и даты `BUILT` (`tools/release.py`):**
  - OAP-приложения в MainApp и скрипты под `/usr/bin/node` работают на **Node 8.9.4 / 8.16.2**. Скрипт `check_node8.sh` ловит синтаксис ES2020+ (`?.`, `??`, `catch {}`) и новые API (`.rmSync`, `.replaceAll`, `.matchAll`, `.flat`, `.flatMap`, `Object.fromEntries`, `Promise.allSettled`, `globalThis`, lookbehind `(?<=`).
  - `tools/release.py` проверяет, что `const BUILT = 'YYYY-MM-DD'` в `ytd.js` не в будущем по UTC (иначе обход просроченных сертификатов при сбитых часах ГУ сработает на машине с правильным временем).

### 1.5. Универсальная зависимость от рендерера (`mguNeeds: ["renderer"]`)

- В `robertnisipeanu/mgu-store` (`mgu-render`) и `cauliflowermossgrape/idrive7-apps` (`idrive7-renderd`) оба рендерера объявляют способность `"mguProvides": "renderer"` и могут стоять бок о бок.
- В `DarkMuse1/idrive7-apps-ru` (`third_party/iteriodev-seats/app/mgu-app.json`) приложения с обычным 2D/GPU-рисованием указывают `"needs": ["renderer"]` (в `catalog.json` — `"mguNeeds": ["renderer"]`), вместо жёсткого пина только на `idrive7-renderd` или только на `mgu-render`.

---

## 2. Что в `mgu-krikun` уже совпадает с лучшими практиками upstream

- **Статический ELF `krikun-runas` + `uids: [3922]` без `User=3922` в unit:** `tools/krikun-xray/runas/main.go`, `tools/krikun-xray/component.json` и `tools/krikun-xray/systemd/krikun-xray.service` повторяют архитектуру `jap-runas` (`NoNewPrivileges=yes` + `CapabilityBoundingSet=CAP_CHOWN CAP_FOWNER CAP_SETUID CAP_SETGID`).
- **Сборка и каталог `catalog` (Module mode):** `scripts/catalog-release.py` пакует `apps/{krikun_seti,filmix_promax,jap_ridetube}` без `node_modules/oap-sdk` и без `"build": "unit"` в `dist/catalog/catalog.json` — на ГУ штатно отрабатывает `oap_link.preparePackage()` с генерацией `oap-sdk` от донора; `jap-node22@22.23.4.tgz` в каталоге байт-в-байт совпадает с `JustAnotherPU/mgu-apps` (`sha256: c62a8e...`).
- **Вендоринг `vendor/jpeg-js` в `jap-ridetube-d`:** `native/jap-ridetube-d/component.json` и `native/jap-ridetube-d/vendor/jpeg-js/{decoder.js,LICENSE,VERSION}` полностью соответствуют upstream `JustAnotherPU/ridetube`, а все `from` в `component.json` локализованы внутри каталога `native/jap-ridetube-d/`.
- **Инварианты `oap_pack.js` и MainApp в `apps/*/package/`:** во всех трёх приложениях заполнены и проверены `files[]`, `npm-shrinkwrap.json` с совпадающей версией, `permissions.json` (`masterAccessTable`, `masterRegistrationTable`), `manifest.json` и `mguLocalOnly: true`; синтаксис `apps/**/*.js` чист под Node 8.
- **Разделение Xray и клиентов без жёсткого `requires`:** связь `krikun-xray` ↔ `jap-ridetube-d` / `jap-filmix-d` идёт через настройку `proxy` в `updater.local.conf` (`proxy.js` из upstream).

---

## 3. Что нужно перенять в `mgu-krikun` (ADOPT — с путями файлов)

1. **Убрать конфликт App Kit (`kit/mgu.js`) с `oap_link.build` на канале `branch:main` (как в `JustAnotherPU/ridetube` + `DarkMuse1/idrive7-apps-ru`):**
   - *Файлы:* `mgu-repo.json`, `scripts/pack-staged-app.js` *(новый короткий Node 8 упаковщик на базе `oap_pack.js`)*, `apps/krikun_seti/mgu-app.json`, `apps/filmix_promax/mgu-app.json`, `apps/jap_ridetube/mgu-app.json`, `scripts/validate-mgu-app.py`.
   - *Что сделать:* перевести наши три App Kit приложения в `mgu-repo.json` с `"build": "unit"` (`mgu-app.json` → `oap_link.build`, который не создаёт `node_modules/oap-sdk` и валится на `needsSdk()` в `mgu-deploy.js:2970`, на `kit/mgu.js` в `filmix_promax` и на JSDoc `require('./health')` в `jap_ridetube`) на лёгкий Node 8 `"build": { "node": "scripts/pack-staged-app.js", "args": ["{dir}"], "output": "{dir}/{id}@{version}.tgz", "shared": ["scripts/pack-staged-app.js"] }` (по образцу `tools/prebuilt_package.js` у `DarkMuse1`). Тогда на ГУ и из `catalog`, и из `branch:main` пакет ставится через `oap_link.preparePackage()`, а `sources.js` читает `app.json` (`title`, `texts.ru`, `requires`, `icon.png`).
2. **Починить `/run/krikun-xray/s` и права файла состояния в `krikun-xray` (как в `JustAnotherPU/mgu-apps/tools/jap-wireproxy/{setup,start}.sh`):**
   - *Файлы:* `tools/krikun-xray/setup.sh`, `tools/krikun-xray/start.sh`, `tools/krikun-xray/systemd/krikun-xray.service`, `tools/krikun-xray/systemd/krikun-xray-ctl.service`.
   - *Что сделать:* создавать `/run/krikun-xray/s` в `setup.sh` от `root` (`[ ! -L ]`, `mkdir -p`, `chown 3922:3922`, `chmod 0755`), а в `start.sh` убрать `umask 077` для `/run/krikun-xray/s/state` (иначе `mkdir` от `uid 3922` внутри `0755 root:root` падает с `Permission denied`, а `0600` не даёт OAP-приложению `krikun_seti` прочитать статус). Добавить в `start.sh` отслеживание `mtime` `config.json` и pre-check `"$BIN" test -c "$CFG"`, а в `.service` — `ProtectKernelTunables=yes`, `ProtectKernelModules=yes`, `ProtectControlGroups=yes`.
3. ~~**Заменить `file -b` в `tools/krikun-xray/check.sh`**~~ **Сделано в `krikun-xray@0.0.7`** (прямой запуск + ELF magic, как у `jap-wireproxy/check.sh`):
   - *Файлы:* `tools/krikun-xray/check.sh`, `scripts/audit-checks-on-hu-mock.py`.
   - *Что сделать:* вместо `file -b "$D/xray"` (утилиты `file` может не быть в образе Yocto на ГУ → пустой вывод → ложный `exit 1` и откат пакета!) вызывать `"$D/xray" version >/dev/null` и проверять код возврата `krikun-runas` без аргументов (`rc=0; "$D/krikun-runas" 2>/dev/null || rc=$?; [ "$rc" -eq 2 ]`). Также явно добавить `"krikun-xray-ctl"` в `recmgr` в `tools/krikun-xray/component.json`.
4. **Реализовать реальный интернет-UID и защиту `ctl.sock` в `jap-filmix-d` (как в `JustAnotherPU/ridetube/native/jap-ridetube-d/ytd.js` или `jap-wireproxy`):**
   - *Файлы:* `native/jap-filmix-d/component.json`, `native/jap-filmix-d/filmix-d.js`, `native/jap-filmix-d/filmix-api.js`, `native/jap-filmix-d/systemd/jap-filmix-d.service`.
   - *Что сделать:* сейчас `jap-filmix-d` декларирует `"uids": "state/internet-uids"`, но работает от `User=root`, не создаёт `state/internet-uids` / `uids.d/jap-filmix-d` и не читает DNS из `/run/mgu-uplink/lease.json` — поэтому прямой выход (`mode: 'direct'` без запущенного `krikun-xray`) на ГУ заблокирован фаерволом `mgu-uplink`. Нужно либо вынести `pickFetchUid` + `uplinkLookup` по образцу `ytd.js`/`thumb.js`, либо запускать демон через `runas` с выделенным UID; права `/run/jap-filmix-d/ctl.sock` сузить с `0666` до `<app_uid>:root 0600` (fallback `0660 root:tm_oap_app`).
5. **Перевести зависимость рендерера в 2D-приложениях на capability `mguNeeds: ["renderer"]` (как в `robertnisipeanu/mgu-store` и `iteriodev_seats`):**
   - *Файлы:* `apps/krikun_seti/app.json`, `apps/filmix_promax/app.json`, `scripts/catalog-release.py`, `scripts/audit-store-5pass.py`.
   - *Что сделать:* заменить жёсткий `"idrive7-renderd": "2.1.10"` в `krikun_seti` и `filmix_promax` на `"mguNeeds": ["renderer"]` (`"needs": ["renderer"]`), чтобы приложения ставились и поверх `mgu-render` из `mgu-store` без обязательного подключения второго репозитория `idrive7-apps`.
