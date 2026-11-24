# Ветка `main` для MGU Store

## Tools

| id | В `mgu-krikun` main |
|----|---------------------|
| krikun-xray | `tools/krikun-xray/prebuilt/` |
| jap-ridetube-d | `native/jap-ridetube-d/prebuilt/` |
| jap-filmix-d | исходники `.js` |
| **jap-node22** | **нет** — как у RideTube: готовый `jap-node22@22.23.4.tgz` из **JustAnotherPU/mgu-apps** |

Пин артефакта: [main/external-deps.json](../main/external-deps.json) (size/sha256 как `tools/ridetube/release.py`).

## jap-node22 на ГУ

В Store **ещё один** источник (общий пакет сообщества, не дубль krikun):

```text
JustAnotherPU/mgu-apps
```

Store прочитает **Releases/catalog** (или main — как даст UI). Установить **jap-node22** 22.23.4 **до** YouT/Filmix.

Приложения в `mgu-krikun` держат `"requires": { "jap-node22": "22.23.4" }` — Store склеивает источники.

## Apps

`apps/*` → сборка на ГУ через `kit/tools/build.py --language ru`.

## Catalog release (Mac)

`scripts/catalog-release.py` по-прежнему **скачивает** тот же `.tgz` с mgu-apps и кладёт в наш релиз `catalog` (для офлайн/зеркала), в **main** node не коммитим.