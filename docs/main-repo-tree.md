# Ветка `main` для MGU Store (repo tree)

Store по умолчанию читает **default branch** (`main`). Отдельно «Releases» на ГУ не выбирается — как у тебя.

## Правило upstream

**Tools** в repo tree **не собираются на ГУ** — в git лежат **prebuilt** (см. idrive7 `kit/renderd/prebuilt`).  
**Apps** из `apps/*` **собираются на ГУ** (`mgu-repo.json` → `kit/tools/build.py`).

## Структура `mgu-krikun`

| Пакет | В git |
|-------|--------|
| Приложения | `apps/<id>/app.json`, `icon.png`, исходники |
| **jap-node22** | `tools/jap-node22/prebuilt/node` (Git LFS), `LICENSE`, `component.json` |
| **krikun-xray** | `tools/krikun-xray/prebuilt/xray`, `krikun-runas` |
| **jap-ridetube-d** | `native/jap-ridetube-d/prebuilt/ytdec`, `ytdlp.pyz` |
| **jap-filmix-d** | только `.js` (без prebuilt) |

Сборка на Mac (`build.sh`) — только чтобы **обновить prebuilt**, потом commit (+ LFS для node).

## Обновить prebuilt на Mac (вручную)

```bash
# krikun-xray
cd tools/krikun-xray && ./build.sh
cp build/xray build/krikun-runas prebuilt/

# jap-node22 — из уже собранного catalog .tgz
tar -xOf .cache/artifacts/jap-node22@22.23.4.tgz files/bin/node > tools/jap-node22/prebuilt/node
tar -xOf .cache/artifacts/jap-node22@22.23.4.tgz files/LICENSE > tools/jap-node22/prebuilt/LICENSE
chmod +x tools/jap-node22/prebuilt/node

# ridetube-d — из .tgz или ./build.sh (MGU_STORE=…)
tar -xOf .cache/artifacts/jap-ridetube-d@0.5.4.tgz files/ytdec -O > native/jap-ridetube-d/prebuilt/ytdec
tar -xOf .cache/artifacts/jap-ridetube-d@0.5.4.tgz files/ytdlp.pyz -O > native/jap-ridetube-d/prebuilt/ytdlp.pyz
chmod +x native/jap-ridetube-d/prebuilt/ytdec
```

`git lfs track tools/jap-node22/prebuilt/node` перед push node.

## На ГУ

Один источник: `maxkrikoun-gif/mgu-krikun` (будет **main**, 7 компонентов — норма).  
База BMW — из mgu-store / idrive7 (как раньше).

Порядок: **jap-node22** → **krikun-xray** → **jap-ridetube-d** / **jap-filmix-d** → приложения.