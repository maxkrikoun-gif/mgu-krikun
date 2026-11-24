# Первый запуск на ГУ

Один источник: **`maxkrikoun-gif/mgu-krikun`** (main).

Перед push (unit-app): `python3 scripts/validate-mgu-app.py` — те же правила, что `mgu-updater` / `tools/oap_link.js` на ГУ (`modules` = пути **от** `apps/<id>/`, например `package/javascript/app.js`, не `javascript/...`; версия = `package/package.json`).

Порядок: **jap-node22** → **krikun-xray** → **Krikun: сеть** → **jap-ridetube-d** → **YouT** → **jap-filmix-d** → **FilmixProMax**.

База: mgu-store, idrive7-apps.

Private: GitHub token в Store (нужен для LFS `prebuilt/node` и private repo).