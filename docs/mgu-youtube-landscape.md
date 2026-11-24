# Ландшафт YouTube-клиентов для BMW MGU (iDrive 7 / iDrive 8)

Дата среза: **24 ноября 2026**.  
Охват: публичные репозитории GitHub (код, issues, PR, релизные каталоги MGU Store), агрегаторы (`FidelisClayton/awesome-bmw-mgu`, `tiraUnderCode23/AQ_MGU`, `zhanyce/mgu-apps-zh`, `tjmodsss/tjm-extras`), а также обсуждения на Drive2, Bimmerpost и в Telegram.

---

## 1. Честный подсчёт: сколько реально независимых разработок?

Интернет **не сводится к одному репозиторию**. Но важно чётко разделить **независимые кодовые базы** (с нуля написанные приложения и демоны), **дерево форков и модификаций RideTube** и **косвенные способы запуска YouTube на ГУ**.

Итоговая картина по состоянию на ноябрь 2026:

1. **4 полностью независимых нативных YouTube-проекта (отдельные кодовые базы и плеерные демоны):**
   - **RideTube** (`JustAnotherPU/ridetube`) — основной и самый зрелый клиент для ID7 (аппаратный декод `ytdec` на Intel Media SDK + звук через штатный `MediaPlayer` BMW).
   - **Bube / YouTube for iDrive 7** (`Drake1804/bube-releases`) — полностью отдельный плеер (вышел **03.11.2026**, на сутки раньше публичного `ridetube`!), свой демон `drake1804-ytplay` (`ytplay` + `ytaudio` + `ffmpeg` + `QuickJS` + `yt-dlp`), экспериментальный вывод звука напрямую в ALSA `smartx:`.
   - **JLTube-MGU** (`shjeladze/JLTube-MGU`) — самый ранний публичный прототип (**02.11.2026**, ID7 + ID8), без `idrive7-apps` kit (чистый RHMI XML/JSON + `mgu-app.json`), демон `jltube-player` на Python safety broker + `QuickJS` + `yt-dlp` + static musl `FFmpeg`; звук не реализован (`-an`), на реальной машине не запускался.
   - **MGU Video Hub** (`NamelsMissing/mgu-apps` → `apps/mgu_video_hub`) — независимый локальный/USB/YouTube видеоплеер на `ffmpeg` + `yt-dlp` + `aplay` с отправкой YouTube-ссылок с телефона по QR (без `jap-ridetube-d` и без `ytdec`).

2. **Дерево развития вокруг RideTube (~25 репозиториев, из них ~10 содержательных форков/портов и ~15 зеркал/чистых форков):**
   - **Порты на iDrive 8 и редизайны UI:** `waliworld/iDrive8-RideTube` (**BeeMTube2**, проверен на BMW M2 G87 ID8), `TheoneLT83/CarTube` (**CarTube** — объединённый ID7+ID8 клиент со вкладками в стиле `idrive7-apps` и собственными ID `cartube` / `cartube-d`), `Oussemf/idrive-apps` (`oussem_youtube`, WIP-порт со сборкой на ГУ).
   - **Русскоязычные VPN/Proxy-сборки (обход блокировок РФ на MGU без TUN/NAT):** `maxkrikoun-gif/mgu-krikun` (**YouT** + `krikun-xray`), `planetapokera2-debug/ridetube-vpn` (SOCKS5 `bmw-vpn` на `:1065`), `sashkafff-ai/bmw-g30-idrive7-apps` (`RideTube + VLESS` с переключателем в меню, проверен на G30), `istt1899/x3` (`media/core` — фиксы кириллицы, таймаутов TV OAuth и `proxy.js` HTTP/SOCKS5).
   - **Аппаратные и функциональные ветки:** `ShakHybridLab/apps` (`ridetube_cluster` — вывод видео RideTube в приборную панель и на HUD через `cluster-render`), `7amoody1985/ridetube` + `mgu-apps-lab` (стриминг в RAM `tmpfs` вместо флеша — позже влит в upstream 0.5.1), `MOHASBI/ridetube` (картинка в движении), а также китайский клиент Bilibili `SleepyK911/RideBili` на движке RideTube.

3. **Косвенные способы смотреть YouTube через MGU Store (ещё 2 технических класса):**
   - **Нативные Chromium-браузеры на ГУ:** `pllanaio/mgu-browser` и `Vizualyse/idrive-apps` (`vizualyse_chromium`).
   - **Нативные AirPlay-приёмники с прямым подхватом YouTube URL на ГУ:** `aurelmarius/bmw-apps` (`aurelm_myairplay` на базе UxPlay + GPU-декодер Moonride + FFmpeg: при нажатии AirPlay в приложении YouTube на iPhone сама ГУ тянет поток до 720p через `mgu-uplink` со звуком в динамики авто), а также Screen Mirroring (`pllanaio/bmw-airplay`, `DanielZagaynov/idrive-apps`, `noth4m4d/mgu-hamadstools`).

4. **Где YouTube НЕТ (вопреки частым предположениям):**
   - `cauliflowermossgrape/idrive7-apps` — YouTube-клиента нет (только телеметрия, диагностика, Doom и SDK `kit/` + `mgu-inputgate`).
   - `robertnisipeanu/mgu-store` и `robertnisipeanu/idrive-apps` — YouTube-клиента нет (дают инфраструктуру: `mgu-render` с поддержкой видеослоя `/dev/shm/mgu-video-*`, `mgu-uplink`, `mgu-python`, `mgu-deploy`, `cluster-render`).
   - `DarkMuse1/idrive7-apps-ru` — YouTube-клиента нет (русская локализация диагностических и сервисных приложений `idrive7-apps` / `bimmer-lab` / `car-apps`).

---

## 2. Сводная таблица проектов

### А. Нативные YouTube-клиенты и содержательные форки

| Проект (ID пакетов) | Автор | Репозиторий | Активен? (посл. пуш / статус) | Связь с `JustAnotherPU/ridetube` | Стек и архитектура (app + daemon?) |
|---|---|---|---|---|---|
| **RideTube** (`jap_ridetube` + `jap-ridetube-d`) | JustAnotherPU | [JustAnotherPU/ridetube](https://github.com/JustAnotherPU/ridetube) | **Да** (22.11.2026, активно развивается, car-tested X5 G05 ID7) | **Оригинал (upstream)** ветки RideTube | OAP app (Node 8, `idrive7-apps` kit) + root/user демон `jap-ridetube-d` (`jap-node22`) + `ytdlp.pyz` (`mgu-python`, автообновление) + аппаратный H.264 GPU-декодер **`ytdec`** (Intel Media SDK → `/dev/shm/mgu-video-ridetube` → `mgu-render`) + штатный BMW `MediaPlayer` для звука, RAM-буфер, TV OAuth, SponsorBlock |
| **Bube / YouTube for iDrive 7** (`drake1804_youtube` + `drake1804-ytplay` + `drake1804_checks`) | Drake1804 (Pavlo Shkaran) | [Drake1804/bube-releases](https://github.com/Drake1804/bube-releases) | **Заморожен / ранний релиз** (03.11.2026; видео проверено на авто, звук без аудиовыхода) | **Независимый проект** (вышел на день раньше RideTube; приватный git, но полные исходники `bube-source-*.tar.gz` в релизе под GPL-3.0) | OAP app + диагностический пакет Checks + демон **`drake1804-ytplay`** (UID 3920: нативные бинарники `ytplay` и `ytaudio`, статический **`ffmpeg`**, **`QuickJS` (`qjs`)**, `yt-dlp.zip` + `python-3.12.15.zip`, вход через QR-релей, попытка вывода звука напрямую в ALSA `smartx:` CarPlay/AA) |
| **JLTube-MGU** (`shjeladze_jltube` + `jltube-player` + `shjeladze_inspector`) | shjeladze | [shjeladze/JLTube-MGU](https://github.com/shjeladze/JLTube-MGU) | **Прототип** (02.11.2026, v0.4.0, не тестировался на машине) | **Независимый проект** (собственный RHMI генератор без `idrive7-apps` kit) | Dual-layout ID7/ID8 OAP source app (`mgu-app.json`, `OnlineApp`) + демон **`jltube-player`** (Python safety broker с `SO_PEERCRED` и жёсткой блокировкой вне `P`, воркер UID 3921 в mount namespace: `yt-dlp` zipimport + `QuickJS` + static musl `FFmpeg` → `/dev/shm/mgu-video-jltube` I420 → `mgu-render`; звук отключён `-an`) |
| **MGU Video Hub** (`mgu_video_hub` + `mgu-video-net`) | NamelsMissing | [NamelsMissing/mgu-apps](https://github.com/NamelsMissing/mgu-apps) (`apps/mgu_video_hub`) | **Да** (24.11.2026, v0.2.0 протестирован на ПК с ffmpeg, ждёт проверки в авто) | **Независимый проект** (универсальный видеоплеер + вкладка YouTube) | OAP app (`idrive7-apps` kit, `mguInternet: true`, локальный loopback-прокси для `*.googlevideo.com`) + root firewall-tool `mgu-video-net` (порт 18879 для отправки ссылок/файлов с телефона по QR) + `yt-dlp` + живой декод **`ffmpeg`** (15 fps I420 `/dev/shm/mgu-video-vhub-*` → `mgu-render` v4) + `aplay` / Audio EQ |
| **BeeMTube2** (`jap_ridetube` для ID8) | waliworld | [waliworld/iDrive8-RideTube](https://github.com/waliworld/iDrive8-RideTube) | **Да** (16.11.2026, проверен на BMW M2 G87 с iDrive 8 / MGU21) | **Порт RideTube под iDrive 8** | Адаптация UI и `kit/id8/` под изогнутый экран ID8 (2880×960, свайпы, двойной тап ±10 с, собственная клавиатура, режимы Zoom/Fill) + демон `jap-ridetube-d` / `ytdec` + BMW `MediaPlayer` |
| **CarTube** (`cartube`, `cartube8`, `cartube-d`, `cartube-node22`) | TheoneLT83 | [TheoneLT83/CarTube](https://github.com/TheoneLT83/CarTube) | **Да** (23.11.2026, дефолтный источник в `TheoneLT83/mgu-store`) | **Производный от RideTube + iDrive8-RideTube** (собственные ID, ставится параллельно с RideTube) | OAP app для **ID7 и ID8** (переделан UI под шапку-вкладки `idrive7-apps`, чтобы оставались видны часы и иконки BMW) + демон `cartube-d` (`cartube-node22`) + бинарники `ytdec` и `yt-dlp` от JustAnotherPU по SHA-256 |
| **YouT в mgu-krikun** (`jap_ridetube` + `jap-ridetube-d`) | maxkrikoun-gif | [maxkrikoun-gif/mgu-krikun](https://github.com/maxkrikoun-gif/mgu-krikun) (private) | **Да** (24.11.2026, `0.6.6` / `0.5.6`) | **Прямой вендоринг дерева RideTube + авто-патчи** (внутри единого RU-источника Store) | Стек RideTube (`jap_ridetube` unit-app без `build.py` на ГУ + `jap-ridetube-d` + встроенный `jap-node22`); дефолт `ru`, обход через Store proxy (`krikun-xray` SOCKS5 `:1080`), VIM без дисклеймера, `pause`/`resume` при закрытии/открытии |
| **RideTube (VPN build)** (`jap_ridetube` + `jap-ridetube-d` 0.3.10) | planetapokera2-debug | [planetapokera2-debug/ridetube-vpn](https://github.com/planetapokera2-debug/ridetube-vpn) | **Да** (22.11.2026, RU-сообщество) | **Модификация `jap-ridetube-d`** от RideTube (UI-пакет автора без изменений) | Стек RideTube + модуль `socks.js` в демоне: заворачивает трафик YouTube/обложек/`ytfetch.py` в локальный SOCKS5 `127.0.0.1:1065` (тулза `planetapokera2-debug/bmw-vpn` или `jap-wireproxy`), при выключенном VPN идёт напрямую |
| **RideTube 0.6.2 + VLESS** (в наборе G30 apps) | sashkafff-ai | [sashkafff-ai/bmw-g30-idrive7-apps](https://github.com/sashkafff-ai/bmw-g30-idrive7-apps) | **Да** (22.11.2026, проверен на BMW G30 ID7, USB-релизы) | **Модификация RideTube 0.6.2 / 0.5.2** под комплектный Xray | Стек RideTube + переключатель «Прокси VLESS» прямо в меню приложения для маршрутизации поиска, входа, обложек и видео через соседний пакет `VLESS VPN 0.2.5` (Xray SOCKS5 `:10808` / HTTP `:10809`) |
| **RideTube (X3 media/core)** (`jap_ridetube` 0.3.13) | istt1899 | [istt1899/x3](https://github.com/istt1899/x3) (`media/core/`) | **Да** (24.11.2026, сетевые тесты на ПК пройдены, авто в процессе) | **Инженерный форк RideTube 0.3.7–0.3.13** (`proxy.js` отмечен автором upstream в issue #14) | Стек RideTube + `proxy.js` (HTTP/SOCKS5 совместимый с Node 8/22), кириллический шрифтовой атлас Ubuntu, исправление зависаний TV OAuth и `repack_service.py` |
| **RideTube on cluster** (`ridetube_cluster` + патченный `ridetube/`) | ShakHybridLab | [ShakHybridLab/apps](https://github.com/ShakHybridLab/apps) (`bimmer/apps/ridetube_cluster`, `ridetube/`) | **Да** (23.11.2026, стендовые тесты, на авто не проверялся) | **Компаньон + микро-патч `jap-ridetube-d`** | Патчит права на буфер кадров `jap-ridetube-d` и через отдельное OAP-приложение выводит видео RideTube (до 15 fps, 640 px) в окно приборной панели `ShakTheme` и на проекцию **HUD** через `cluster-render` (строго на стоянке) |
| **RideTube (lab-ram)** (`mdq_ridetube` + `mdq-ridetube-d`) | 7amoody1985 | [7amoody1985/ridetube](https://github.com/7amoody1985/ridetube) · [7amoody1985/mgu-apps-lab](https://github.com/7amoody1985/mgu-apps-lab) | **Да** (20.11.2026, проверен на X5 G05; фича влита в upstream 0.5.1) | **Экспериментальный форк RideTube** со своими ID (`mdq_*`) | Стек RideTube + стриминг активного видео через `tmpfs` (256 МБ RAM с подгрузкой на 2 мин вперёд вместо записи целиком на флеш) + оверлей статистики потока |
| **RideTube (VIM)** | MOHASBI | [MOHASBI/ridetube](https://github.com/MOHASBI/ridetube) | **Да** (24.11.2026) | **Минимальный форк RideTube** | Стек RideTube со снятым ограничением показа картинки в движении |
| **YouTube pour iDrive** (`oussem_youtube` + `jap-ridetube-d`) | Oussemf | [Oussemf/idrive-apps](https://github.com/Oussemf/idrive-apps) | **WIP** (15.11.2026) | **Форк RideTube** (ревизия `6336494`) | Переименованный OAP пакет `oussem_youtube` (сборка на самой ГУ с ветки `main`) + совместимость со службой `jap-ridetube-d` |

### Б. Родственные видеоклиенты, репаки каталогов и косвенные решения для YouTube

| Проект / Ресурс | Автор | Ссылка | Активен? | Связь с RideTube | Как относится к YouTube на MGU |
|---|---|---|---|---|---|
| **RideBili** (`ride_bili`) | SleepyK911 | [SleepyK911/RideBili](https://github.com/SleepyK911/RideBili) | **Да** (23.11.2026) | **Порт движка RideTube на Bilibili** | Не YouTube, а китайский видеохостинг Bilibili: QR-вход, поиск, `ytdec` H.264 GPU декод + `mgu-render` + аудио в авто |
| **myAirPlay** (`aurelm_myairplay` + `aurelm-myairplay`) | aurelmarius | [aurelmarius/bmw-apps](https://github.com/aurelmarius/bmw-apps) | **Да** (ноябрь 2026, car-tested) | Общий подход к GPU-декоду (из `JustAnotherPU/moonride` + FFmpeg) | Нативный AirPlay-приёмник (UxPlay): по кнопке AirPlay в YouTube на iPhone **сама ГУ качает и крутит YouTube до 720p** через `mgu-uplink` с управлением шайбой iDrive (без активного CarPlay) + зеркалирование экрана |
| **MGU Browser** (`mgu_browser`) / **Vizualyse Chromium** | pllanaio / Vizualyse | [pllanaio/mgu-browser](https://github.com/pllanaio/mgu-browser) · [Vizualyse/idrive-apps](https://github.com/Vizualyse/idrive-apps) | **Эксперимент** (ноябрь 2026) | Не связаны | Полноценный Chromium на ГУ поверх `mgu-render` (управление шайбой, вкладки); теоретически открывает веб-версию YouTube, но звук/DRM/тачпад ещё дорабатываются |
| **TJM Extras** (`TJM RideTube`, `TJM CarTube`) | tjmodsss | [tjmodsss/tjm-extras](https://github.com/tjmodsss/tjm-extras) | **Да** (09.11.2026) | **Зеркало бинарных пакетов** RideTube и CarTube | Переупаковывает проверенные по SHA-256 `.tgz` от JustAnotherPU и TheoneLT83 со своими иконками и префиксом `TJM` |
| **MGU 中文应用源** (`ridetube-cn`) | zhanyce / JackieZ123430 | [zhanyce/mgu-apps-zh](https://github.com/zhanyce/mgu-apps-zh) · [JackieZ123430/ridetube-cn](https://github.com/JackieZ123430/ridetube-cn) | **Да** (24.11.2026) | **Китайская локализация и пересборка** RideTube | Каталог на 73 китайских приложения; перевод `JackieZ123430` также официально влит в upstream `JustAnotherPU/ridetube` (PR #3, #16) |
| **AQ_MGU** | tiraUnderCode23 | [tiraUnderCode23/AQ_MGU](https://github.com/tiraUnderCode23/AQ_MGU) | **Да** (20.11.2026) | **Агрегатор снапшотов** | Хранит копии `drake1804-ytplay`, `drake1804-checks` и `NamelsMissing/mgu-apps` (`mgu_video_hub`) в едином каталоге |
| **Прочие GitHub-форки `ridetube`** | `marilykinson-glitch`, `alexarghir98`, `cars-done`, `Asksket`, `onurciner` (`cockpittube`), `zee4iqra-oss` (`ridetubezee`), `bmw-repos`, `okanongun`, `dmk0202`, `patidani`, `renzorlive`, `divxon44`, `useryusuf869` | Сетка форков `JustAnotherPU/ridetube` | Ноябрь 2026 | **Прямые форки** | Часть (`marilykinson-glitch`, `alexarghir98`, `cars-done`, `Asksket`) служила фиче-ветками для PR в upstream (история, плейлисты, перемотка тачем, кнопки на руле, автообновление `yt-dlp`, кириллица — см. [issue #14](https://github.com/JustAnotherPU/ridetube/issues/14)); остальные — личные копии/зеркала |
| **MGUnlock.PRO / сервисные установщики (РФ)** | Коммерческие проекты (Drive2 / TG) | `t.me/mgunlock_pro` и посты на Drive2 | **Да** (ноябрь 2026) | Закрытые обёртки | Android-приложение / платная удалённая установка root + MGU Store с рекламой «плюсом идёт YouTube, работающий в России» — без собственного публичного плеера (комбинация готового Store + RideTube + VPN/прокси) |

---

## 3. Сравнение технических подходов в 4 независимых ветках

| Узел пайплайна | 1. RideTube (`JustAnotherPU`) | 2. Bube (`Drake1804`) | 3. JLTube-MGU (`shjeladze`) | 4. MGU Video Hub (`NamelsMissing`) |
|---|---|---|---|---|
| **UI на ГУ (OAP)** | `idrive7-apps` GPU canvas kit (`mgu-render` + `mgu-inputgate`), Node 8 | Собственный OAP пакет (`drake1804_youtube`) + `drake1804_checks` | Чистый RHMI XML/JSON (`mgu-app.json`, ID7 + ID8), без `idrive7-apps` kit | `idrive7-apps` GPU canvas kit (`mgu-render` v4), Node 8 |
| **Фоновый сервис** | `jap-ridetube-d` на Node.js 22 (`jap-node22`), сокет `/run/jap-ridetube-d/ctl.sock` | `drake1804-ytplay` (UID 3920), бинарник `ytplay` | `jltube-player` (Python safety broker + воркер UID 3921 в mountns), `/run/jltube-player/control.sock` | Внутри OAP app (`mguInternet: true`) + root firewall-tool `mgu-video-net` |
| **Получение потока YouTube** | InnerTube TV клиент в Node 22 + `ytdlp.pyz` (`mgu-python`, автоапдейт по SHA256) | `yt-dlp.zip` + `python-3.12.15.zip` + **`QuickJS` (`qjs`)** для JS-челленджей | `yt-dlp` zipimport (`mgu-python` 3.12) + **`QuickJS` (`qjs`)** | `yt-dlp` по ссылкам, присланным с телефона по QR (кеш URL на 10 мин) |
| **Декодирование видео** | **Аппаратное (GPU):** `ytdec` на **Intel Media SDK (MFX)** H.264 → `/dev/shm/mgu-video-ridetube` | **Программное (CPU):** статический `ffmpeg` (до 720p) | **Программное (CPU):** static musl `FFmpeg` → `/dev/shm/mgu-video-jltube` (I420 triple-buffer) | **Программное (CPU):** `ffmpeg` (15 fps pacing) → `/dev/shm/mgu-video-vhub-*` |
| **Вывод звука** | **Штатный `MediaPlayer` BMW** (работает стабильно, штатная громкость и кнопки руля) | Эксперимент: бинарник `ytaudio` напрямую в ALSA `smartx:` (`CarPlayMain` / `AndroidAutoMedia`); на авто звук пока не пошёл | Отключён (`-an`), маршрутизация звука не реализована | `aplay` / ALSA + собственный экран эквалайзера |
| **Авторизация YouTube** | Штатный TV device code (`google.com/device`), локально на ГУ | QR-вход через внешний облачный релей автора (whitelist Google-проекта, на 7 дней) | Без аккаунта (только публичный поиск и ссылки) | Без аккаунта (отправка ссылок со смартфона в локальной сети) |

**Главный инженерный вывод:** именно связка **Intel Media SDK GPU-декодера (`ytdec`) + штатного аудиоплеера BMW (`MediaPlayer`) + локального TV OAuth без внешних релеев** сделала `JustAnotherPU/ridetube` де-факто стандартом, вокруг которого выросло 20+ форков (включая ID8-порт `BeeMTube2`, `CarTube` и все рабочие российские VPN/VLESS-сборки). Независимые альтернативы (`Bube`, `JLTube-MGU`, `MGU Video Hub`) упёрлись прежде всего в закрытую аудиомаршрутизацию MGU (AVB / Intel `smartx:` ALSA locks) и нагрузку программного `ffmpeg` на CPU.

---

## 4. Что такое `jap_ridetube` в `mgu-krikun` (`/Users/m.krikun/bmw`)

По результатам проверки скриптов и документации этого репозитория ([docs/store-single-source.md](store-single-source.md), [docs/ridetube-adaptation.md](ridetube-adaptation.md), [docs/ridetube-krikun-patches.md](ridetube-krikun-patches.md), `scripts/fetch-ridetube.py`, `scripts/apply-ridetube-patches.py`, `scripts/verify-ridetube.py`, `scripts/catalog-release.py`):

1. **Способ включения в репозиторий — прямой вендоринг файлов (не git-fork и не git-submodule/subtree):**
   - `scripts/fetch-ridetube.py` скачивает дерево ветки `main` из `JustAnotherPU/ridetube` через GitHub Trees/Raw API прямо в корень `mgu-krikun`:
     - `apps/jap_ridetube/`, `native/jap-ridetube-d/`, `native/ytdec/`, `native/mgu-render-id7-touch/`, `kit/` ложатся по тем же путям в корень;
     - `tools/*` перекладываются в `tools/ridetube/*`;
     - `LICENSE`, `THIRD_PARTY_LICENSES`, `CHANGELOG.md` — в `licenses/ridetube/*`;
     - `README.md`, `README.zh-CN.md` — в `docs/ridetube-upstream/*`.
   - `scripts/verify-ridetube.py` сверяет локальные файлы с git blob SHA-1 апстрима, контролируя, что отличаются только явно пропатченные файлы.

2. **Архитектура поставки для MGU Store («один источник»):**
   - В `mgu-repo.json` и `scripts/catalog-release.py` пакет `jap_ridetube` оформлен как **`unit-app`** с готовым деревом `apps/jap_ridetube/package/` (линковка `oap_link` на ГУ против штатного SDK авто без запуска тяжёлого `build.py` на голове и без `oap-sdk` в git).
   - Текущие версии в `dist/catalog/catalog.json`: **`jap_ridetube@0.6.6`** + **`jap-ridetube-d@0.5.6`**.
   - Среда выполнения **`jap-node22@22.23.4`** встроена прямо в этот же репозиторий (`tools/jap-node22`), поэтому пользователю в MGU Store не нужно добавлять ни `JustAnotherPU/ridetube`, ни `JustAnotherPU/mgu-apps` — только `maxkrikoun-gif/mgu-krikun`.

3. **Собственные патчи `mgu-krikun` (`scripts/apply-ridetube-patches.py`):**
   - **Брендинг и полная русификация:** название изменено на **YouT** (`iconGlyph: "YT"`), `language` по умолчанию `"ru"`, заполнены русские карточки `texts.ru` для приложения и сервиса.
   - **Интеграция с обходом блокировок без жёсткой сцепки пакетов:** `store_proxy` включён по умолчанию (`true`). `jap-ridetube-d` берёт `proxy = socks5://127.0.0.1:1080` из `/var/opt/mgu-updater/updater.local.conf`, куда его прописывает отдельный инструмент `krikun-xray` (VLESS/Reality), при этом зависимости `requires` на `krikun-xray` у `jap_ridetube` нет ([docs/components-separate.md](components-separate.md)).
   - **Видео в движении сразу:** `video_driving` по умолчанию `true`, в `yt.js` упрощён `driveLock` (снято требование первичного включения на стоянке `video_driving_ok`), в `main.js` убран экран-дисклеймер `risk`.
   - **Пауза и автопродолжение вместо сброса:** добавлена кнопка `BTN_EXIT` («Закрыть» / `ctx.exitApp()`), отключён фоновый hold `ctx.background('playing')`; при уходе с экрана или закрытии приложения `main.js` и `ytd.js` переводят плеер в **`pause`** (а не `stop`), а при следующем открытии YouT автоматически продолжает воспроизведение с того же места (`resume`).
