# RideTube — адаптация под mgu-krikun

**Не** объединяем с krikun-xray / krikun_seti. Берём upstream, правим минимум, публикуем **два** пакета в catalog: `jap_ridetube` + `jap-ridetube-d`.

## Источник

- Upstream: https://github.com/JustAnotherPU/ridetube (GPL-3.0-or-later)
- У нас: **в корне `mgu-krikun`**: `apps/jap_ridetube`, `native/`, `kit/`, `licenses/ridetube/`
- Обновление: `python3 scripts/fetch-ridetube.py`, затем патчи из `docs/ridetube-krikun-patches.md`

## Что меняем (наши отличия)

| Область | Upstream | У нас |
|---------|----------|--------|
| Store-источник | `JustAnotherPU/ridetube` | только `maxkrikoun-gif/mgu-krikun` |
| Язык по умолчанию | `auto` / en | **`ru`** в `apps/jap_ridetube/app.json` |
| catalog | их release `catalog` | наш `catalog` + обязательный `texts.ru` |
| Proxy | опция Store proxy | то же; SOCKS задаёт **krikun-xray** в `updater.local.conf` |
| Брендинг catalog | RideTube | `texts.ru` title/description на русском |

## Что **не** трогаем без нужды

- Архитектура app + `jap-ridetube-d` + `ytdec` — как upstream
- Логику `ytd.js`, InnerTube, буфер RAM — не переписываем
- Не вшиваем Xray в manifest RideTube (`requires` на krikun-xray **нет**)

## Сборка catalog (позже)

По образцу upstream `tools/release.py` / `kit/tools/build.py`:

1. `apps/jap_ridetube` — патч RU default
2. Сборка `.tgz` для `jap-ridetube-d` и `jap_ridetube` (oap-sdk, jap-node22 из Store)
3. Выкладка в релиз `catalog` репо `mgu-krikun` с `texts.ru` на оба компонента

Скрипт-обёртка: `scripts/build-ridetube-catalog.sh` (TODO).

## Чеклист перед релизом catalog

См. [russian-only.md](russian-only.md):

- [ ] Дефолт `language: ru`
- [ ] Меню, Health check, ошибки — русский
- [ ] В Store названия из `texts.ru`
- [ ] С krikun-xray: proxy Store → Health check OK
- [ ] LICENSE / THIRD_PARTY_LICENSES в артефакте

## Правовая

RideTube — GPL-3.0; при распространении catalog соблюдаем лицензию upstream, в README/catalog — автор JustAnotherPU.