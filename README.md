# mgu-krikun — единый каталог MGU + Xray

Личный контур: [maxkrikoun-gif/mgu-krikun](https://github.com/maxkrikoun-gif) (private), SSH **`~/.ssh/mgu_krikun`** ([docs/project-identity.md](docs/project-identity.md)).

**В MGU Store добавляется только этот репозиторий** (плюс сам Store с `robertnisipeanu/mgu-store`, если его ещё нет). RideTube, **krikun-xray** и все приложения — **внутри** `mgu-krikun`, не отдельными источниками: [docs/store-single-source.md](docs/store-single-source.md).

**Правило русификации:** всё, что мы кладём в репо и catalog, — **полностью на русском** (меню, Store, tools). Не «одно приложение», а **каждый** компонент. [docs/russian-only.md](docs/russian-only.md) · [CONSTRAINTS.md](CONSTRAINTS.md).

Обход блокировок — **Xray (VLESS/Reality)** с **fr74** (Amnezia), SOCKS на ГУ ([docs/xray-on-hu-design.md](docs/xray-on-hu-design.md)).

## Цели

- **mgu-uplink** — интернет с телефона.
- **krikun-xray** (tool) и **krikun_seti** (app «Krikun: сеть») — **отдельно** от YouTube, см. [docs/krikun-client.md](docs/krikun-client.md).
- **RideTube** (`jap_ridetube` + `jap-ridetube-d`) — **отдельное** приложение и сервис; в catalog свой `.tgz`, без зависимости от krikun-xray. [docs/components-separate.md](docs/components-separate.md).
- RU-приложения — из **одного** catalog этого репо.
- Секреты Amnezia **не** в git.

## Store на ГУ

Добавить источник → **maxkrikoun-gif/mgu-krikun** (Store читает **main** или релиз **catalog**).

Схема repo tree: [docs/main-repo-tree.md](docs/main-repo-tree.md).  
Первый запуск (iDrive 7): [docs/first-run-hu.md](docs/first-run-hu.md).  
Практики экосистемы (ID7): [docs/mgu-idrive7-best-practices.md](docs/mgu-idrive7-best-practices.md).  
Чеклист для Cursor: `.cursor/rules/mgu-krikun-hu.mdc` (`alwaysApply`).

## Цепочка сети

```text
Телефон → mgu-uplink
              ↓
         krikun-xray (SOCKS → VLESS fr74)
              ↓
         proxy в updater.local.conf
              ↓
         RideTube / загрузки Store
```

Пример Xray: [config/examples/xray-config.json.example](config/examples/xray-config.json.example).

## Amnezia

Экспорт **Xray JSON**, не `vpn://`. Файлы `*.vpn` — только локально.

## GitHub

[docs/github-create.md](docs/github-create.md).

## Лицензия

MIT — обвязка этого репо. Upstream (Store, RideTube, idrive7-apps-ru, Xray-core) — их лицензии.