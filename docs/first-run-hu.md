# Первый запуск на ГУ

Один источник: **`maxkrikoun-gif/mgu-krikun`** (main).

Перед push (unit-app): `python3 scripts/validate-mgu-app.py` — те же правила, что `mgu-updater` / `tools/oap_link.js` на ГУ (`modules` = пути **от** `apps/<id>/`, например `package/javascript/app.js`, не `javascript/...`; версия = `package/package.json`).

Порядок: **jap-node22** → **krikun-xray** → **Krikun: сеть** → **YouT (сервис) 0.5.5** → **YouT 0.6.5** → **jap-filmix-d** → **FilmixProMax 0.0.3**.

Apps **unit** (готовый `package/` в git, без `build.py` на ГУ). После `build.py` на Mac: `python3 scripts/sync-unit-package.py <id> --strip-locale-suffix`.

База: mgu-store, idrive7-apps.

Private: GitHub token в Store (нужен для LFS `prebuilt/node` и private repo).