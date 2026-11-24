# Публикация catalog (зеркало на Mac, не источник Store)

## Зачем

На ГУ источник — **только ветка `main`** ([store-single-source.md](store-single-source.md)).

Релиз **`catalog`** — готовые `.tgz` для выкладки / офлайн-раздачи. С `--bundle-all-deps` можно упаковать и базу mgu-store; без флага — только то, что в [deps.manifest.json](../catalog/deps.manifest.json) (без дублей чужих источников).

На **main** есть `tools/jap-node22` (сборка на ГУ) — Filmix/YouT **не требуют** второго источника Releases.

## Сборка (на Mac)

```bash
cd /Users/m.krikun/bmw
python3 scripts/catalog-release.py --fast  # повторная сборка с кэшем (~5–15 с)
python3 scripts/catalog-release.py -j 10   # без дублей mgu-store/idrive7 (см. exclude_from_catalog)
python3 scripts/catalog-release.py --bundle-all-deps   # всё в одном catalog

# Сильно быстрее на больших файлах (jap-node22, mgu-python):
brew install aria2
# выход: dist/catalog/catalog.json + все .tgz
```

Повторный запуск reuse кэша — скачиваются только новые/битые файлы.

## GitHub Release

1. Создать/обновить релиз с тегом **`catalog`** (не semver).
2. Загрузить **все файлы** из `dist/catalog/` как assets (включая `catalog.json`).
3. **На ГУ не подключать** этот релиз как Store-источник — только **main**.

## Порядок установки на ГУ

1. `mgu-deploy` → `mgu-updater` → `mgu-uplink` (интернет)
2. `mgu-python`, `jap-node22`, `mgu-render`
3. `idrive7-renderd`, `mgu-inputgate` (после inputgate — перезапуск ГУ)
4. `krikun-xray` → **Krikun: сеть**
5. `jap-ridetube-d` → **YouT**; `jap-filmix-d` → **FilmixProMax**

## Версии

При изменении пакетов поднимайте `version` в `component.json` / `app.json` и пересобирайте catalog.