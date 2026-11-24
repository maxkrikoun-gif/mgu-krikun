# Первый запуск на ГУ

Один источник: **`maxkrikoun-gif/mgu-krikun`** (main).

Перед push (unit-app): `python3 scripts/validate-mgu-app.py` — те же правила, что `mgu-updater` / `tools/oap_link.js` на ГУ (`modules` = пути **от** `apps/<id>/`, например `package/javascript/app.js`, не `javascript/...`; версия = `package/package.json`).

Порядок: **jap-node22** → **krikun-xray** → **Krikun: сеть** → **YouT (сервис) 0.5.5** → **YouT 0.6.5** → **Filmix (сервис) 0.0.3** → **FilmixProMax 0.0.3**.

Перед push: `python3 scripts/preflight-store.py`.

Apps **unit** (готовый `package/` в git, без `build.py` на ГУ). После `build.py` на Mac: `python3 scripts/sync-unit-package.py <id> --strip-locale-suffix`.

База: mgu-store, idrive7-apps.

Private: GitHub token в Store (private repo). **Node.js 22** — бинарник частями `node.part.*`, при install `check.sh` собирает `bin/node` (Git LFS на ГУ не используется).