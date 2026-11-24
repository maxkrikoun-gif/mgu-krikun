# Иконки приложений под MGU / iDrive

## Формат

| Параметр | Значение |
|----------|----------|
| Файл | `apps/<id>/icon.png` (см. `mgu-repo.json` → `apps.icon`) |
| Repo tree | у каждого app в `components[]` поле **`"icon": "icon.png"`** (иначе Store рисует букву из `iconGlyph`) |
| Catalog | в `catalog.json`: `"icon"` + `"iconSha256"`, PNG в assets релиза |
| Размер | **140×140** px, RGBA |
| Скругление | **r = 32** px (внешняя плитка) |
| Safe zone | отступ **14** px от края (контент в 112×112) |

Store/iDrive рисуют плитку со скруглением — иконка уже содержит форму тайла и прозрачные углы.

## Сборка

```bash
python3 scripts/build-mgu-icons.py
```

Пересобирает:

- `apps/jap_ridetube/icon.png` — логотип YouTube (ассет из чата) + подпись **YouT**
- `apps/filmix_promax/icon.png` — красный play, **Filmix**
- `apps/krikun_seti/icon.png` — сеть / обход, **сеть**

Исходник SVG для YouT: `apps/jap_ridetube/icon.svg` (упрощённый вектор; в Store идёт PNG).

## Замена логотипа YouT

Положить PNG в путь из `YT_LOGO` в `scripts/build-mgu-icons.py` или обновить путь и перезапустить скрипт.