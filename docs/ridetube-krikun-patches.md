# Патчи YouT (RideTube upstream) в mgu-krikun

Автоматически: `python3 scripts/apply-ridetube-patches.py`

| Файл | Патч |
|------|------|
| `apps/jap_ridetube/app.json` | бренд **YouT**; `language` → **ru**; `store_proxy` → **true**; **`video_driving`** → **true**; **`texts.ru`** |
| `apps/jap_ridetube/main.js` | **без disclaimer**; **Закрыть** (`BTN_EXIT`, rail); `ctx.exitApp` |
| `kit/runtime/mgu.js` | **`ctx.exitApp()`** — выход из любого app mgu-krikun |
| `apps/krikun_seti/` | **`BTN_EXIT` «Закрыть»** на всех экранах |
| `apps/jap_ridetube/yt.js` | **`driveLock`**: картинка в движении сразу, без `video_driving_ok` / стоянки; `pause` / `resume` |
| `apps/jap_ridetube/main.js` | **закрытие → пауза**; **повторный запуск → resume**; без `background('playing')` |
| `native/jap-ridetube-d/ytd.js` | при отвале клиента: **pause**, не `stop`, пока играло |
| `kit/runtime/locales/ru.json` | RideTube → **YouT** в переводах |
| `apps/jap_ridetube/main.js` | заголовок на экране **YouT** |
| `native/jap-ridetube-d/component.json` | LICENSE → `licenses/ridetube/`; **`texts.ru`** |

Цикл обновления:

```bash
python3 scripts/fetch-ridetube.py
python3 scripts/apply-ridetube-patches.py
python3 scripts/verify-ridetube.py
```

Исходник: [JustAnotherPU/ridetube](https://github.com/JustAnotherPU/ridetube) (GPL-3.0-or-later).