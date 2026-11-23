# Один источник в MGU Store

## Правило

На головном устройстве **не добавляем** чужие каталоги:

| Не добавлять в Store | Зачем раньше брали |
|----------------------|-------------------|
| `DarkMuse1/idrive7-apps-ru` | русифицированные приложения |
| `JustAnotherPU/ridetube` | YouTube |
| `JustAnotherPU/mgu-apps` | node22, прочие tools |
| `cauliflowermossgrape/idrive7-apps` | базовые приложения BMW-сообщества |

Всё это **везём через один репозиторий**:

```text
maxkrikoun-gif/mgu-krikun
```

Сам **MGU Store** (`robertnisipeanu/mgu-store`) — это приложение-магазин на ГУ. Его источник/установка **отдельно** (часто уже стоит с заводской/сторонней прошивкой). Дополнительно в настройках Store добавляется **только** `maxkrikoun-gif/mgu-krikun`.

## Как Store читает этот репо

Два рабочих режима (см. [PUBLISHING.md](https://github.com/robertnisipeanu/mgu-store/blob/main/docs/PUBLISHING.md) upstream):

| Режим | В Store выбрать | Что в репо |
|-------|-----------------|------------|
| **Catalog** (рекомендуем сначала) | **Releases** → релиз с именем **`catalog`** | `catalog.json` + `.tgz` в assets |
| **Repo tree** | ветка **`main`** (или тег) | `mgu-repo.json` + исходники в дереве |

Оба варианта дают **одну строку** `owner/repo` в «Добавить источник».

### Catalog-сборка (план)

1. Собрать OAP-пакеты **только с русским UI** (см. [russian-only.md](russian-only.md)):
   - приложения: ветка **DarkMuse1/idrive7-apps-ru**, сборка `--language ru`;
   - **RideTube**: `apps/jap_ridetube` + дефолт **Русский**, проверка всех меню;
   - **krikun-xray** и любые tools — `texts.ru`, русские строки.
2. **Не включать** в catalog английские пакеты «для теста».
3. Один релиз **`catalog`**, `catalog.json` (schema 2): у **каждого** component есть `texts.ru`.
4. На ГУ: источник `maxkrikoun-gif/mgu-krikun`, режим Releases.

Скрипт публикации — позже в `catalog/` (по образцу `mgu-store release/release.js`).

### Repo tree (альтернатива)

Исходники upstream кладём **внутрь** `mgu-krikun` (git subtree, без отдельных источников в Store):

```bash
cd /Users/m.krikun/bmw

# Русифицированные приложения (пример)
git subtree add --prefix=vendor/idrive7-apps-ru \
  https://github.com/DarkMuse1/idrive7-apps-ru.git main --squash

# RideTube: обновление upstream (скачивание → корень репо, не vendor/)
python3 scripts/fetch-ridetube.py
# затем снова патч RU — docs/ridetube-krikun-patches.md
```

Корневой `mgu-repo.json`: `apps/*`, `native/jap-ridetube-d`, `tools/krikun-xray`. Store — **только** `maxkrikoun-gif/mgu-krikun`.

Сборка на ГУ — долго и нужен donor oap-sdk на машине; для личного контура чаще удобнее **catalog** с готовыми `.tgz`.

## Приватный репозиторий

`mgu-krikun` — **private**. В Store → Settings укажите **GitHub token** с доступом к `maxkrikoun-gif/mgu-krikun`, иначе ГУ не скачает catalog/assets (см. [project-identity.md](project-identity.md)).

## Сеть (Xray)

Независимо от режима каталога:

- **mgu-uplink** (из Store/robertnisipeanu) — интернет с телефона;
- **krikun-xray** — из **этого же** источника `mgu-krikun`;
- `proxy = socks5://127.0.0.1:1080` в `updater.local.conf` — RideTube и загрузки.

## Лицензии

Upstream (DarkMuse, JustAnotherPU, Xray-core) остаются под своими лицензиями. В README/catalog указываем авторов; в git — subtree или явные ссылки на коммиты upstream.