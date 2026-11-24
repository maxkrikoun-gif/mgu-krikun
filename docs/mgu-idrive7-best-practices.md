# MGU / iDrive 7 — практики (только ID7)

Краткий чеклист для агентов: [`.cursor/rules/mgu-krikun-hu.mdc`](../.cursor/rules/mgu-krikun-hu.mdc) (`alwaysApply`).  
Жёсткие обязательства: [CONSTRAINTS.md](../CONSTRAINTS.md).  
Первый запуск: [first-run-hu.md](first-run-hu.md).

Сводка по экосистеме (awesome-bmw-mgu, JustAnotherPU, mgu-store, **istt1899/x3**, Oussemf, idrive7-apps) с колонкой **«у нас»**. **iDrive 8, WireGuard, wireproxy** — вне scope.

---

## Зачем preflight

На Mac можно собрать catalog, но ГУ ломается на мелочах: `oap_link` и кавычки в `require('./kit/…')`, `oap_pack` без `files[]`, systemd с `User=3922`, Mach-O в `prebuilt/`.

`python3 scripts/preflight-store.py` — **11 проходов**, включая `audit-mgu-architecture.py` (ELF, runas, kit-кавычки, shrinkwrap, запрет wireproxy) и mock `check.sh`.

| Практика | У кого | У нас |
|----------|--------|-------|
| Preflight перед push | Oussemf `validate.yml` (тяжёлый: node+ffmpeg) | ✓ `preflight-store.py` + CI `.github/workflows/preflight.yml` |
| 64 MiB лимит пакета | mgu-store `oap_pack` | ✓ `audit-store-5pass` pass 2 |
| dist/catalog vs repo | release repos | ✓ pass 9 |

---

## Store, catalog, упаковка

| Практика | У кого | У нас |
|----------|--------|-------|
| Один catalog-json + `.tgz` на id | bube-releases, AQ_MGU | ✓ `dist/catalog/catalog.json`, тег **`catalog`** |
| **unit-app**: `package/` в git, без `build.py` на ГУ | idrive7-apps-ru | ✓ `mgu-repo.json` → `build: unit` |
| `files[]` в `package/package.json` | idrive7-apps | ✓ preflight |
| Не re-host mgu-store / idrive7 | сообщество | ✓ `exclude_from_catalog` |
| `texts.ru` в catalog | mgu-apps-zh, store-cn | ✓ все наши id |
| Сборка catalog на Mac | JustAnotherPU | ✓ `catalog-release.py --fast` |

**У нас нет (намеренно):** сборка apps на ГУ; публичная «витрина» как AQ_MGU; iDrive 8 renderer.

---

## oap_link и app

После install Store подменяет entry (`oap_link.js`).

- `modules[]` — пути от `apps/<id>/`, не `javascript/...` без префикса.
- `require("./kit/foo.js")` — **двойные** кавычки для kit.
- Sibling-модули — `require('./bar.js')`, имена согласованы с `modules[]`.
- Граф `require()` ⊆ `modules[]` — preflight.

| Практика | У кого | У нас |
|----------|--------|-------|
| oap_link quoting | типичные инциденты mgu-store | ✓ audit + validate-mgu-app |
| RU тексты водителю | DarkMuse1, istt1899 | ✓ [russian-only.md](russian-only.md) |

---

## Tools: uid, runas, systemd, check

| Практика | У кого | У нас |
|----------|--------|-------|
| `"internet": true` + uplink uid | jap-ridetube-d, wireproxy | ✓ krikun-xray `3922`, jap-ridetube-d uids.d |
| **Не `User=` в unit** | jap-runas, jap-wireproxy | ✓ `krikun-runas` + `audit-systemd-units.py` |
| `NoNewPrivileges=yes`, лимиты RAM/CPU | jap-wireproxy | ✓ `krikun-xray.service` |
| Supervisor loop `start.sh` | wireproxy | ✓ `tools/krikun-xray/start.sh` |
| `check.sh` offline smoke | JustAnotherPU ridetube | ✓ jpeg-js vendor + ytdlp.pyz (jap-ridetube-d) |
| **vendor/jpeg-js в git** | ridetube upstream | ✓ `native/jap-ridetube-d/vendor/jpeg-js/` |
| prebuilt **linux-amd64 ELF** | все tools | ✓ audit-mgu-architecture |
| recmgr / crashNames | mgu-deploy | ✓ component.json сервисов |

**У нас нет:** wireproxy/TUN; `User=` в unit.

Store качает один каталог tool; всё из `files[]` — в git (не gitignore для prebuilt).

---

## Proxy и сеть (istt1899 + Store)

```text
mgu-uplink → krikun-xray (SOCKS 127.0.0.1:1080)
          → proxy в /var/opt/mgu-updater/updater.local.conf
          → Store, jap-ridetube-d (proxy.js), jap-filmix-d
```

| Практика | У кого | У нас |
|----------|--------|-------|
| Одна строка `proxy` в updater.local.conf | mgu-store, istt1899 | ✓ |
| enable/disable root helpers | — | ✓ `enable-proxy.sh`, `disable-proxy.sh`, **Krikun: сеть** |
| RideTube без `requires` xray | upstream | ✓ [components-separate.md](components-separate.md) |
| Таймауты / lease uplink в ytd.js | istt1899, upstream | ✓ upstream jap-ridetube-d (без отдельного форка) |
| Health check в UI | ridetube | ✓ YouT → Health check |

Детали: [vpn-chain.md](vpn-chain.md), [xray-on-hu-design.md](xray-on-hu-design.md).

---

## Версии catalog (текущий main)

| id | version |
|----|---------|
| jap-node22 | 22.23.4 |
| krikun-xray | 0.0.5 |
| krikun_seti | 0.0.5 |
| jap-ridetube-d | 0.5.6 |
| jap_ridetube | 0.6.6 |
| jap-filmix-d | 0.0.3 |
| filmix_promax | 0.0.4 |

Вне Store-источника mgu-krikun: **mgu-render** 0.6.11, **mgu-inputgate** 1.0.0, **idrive7-renderd** 2.1.10 — ставить **до** наших apps.

---

## Автоматизация

```bash
python3 scripts/preflight-store.py    # перед каждым push
python3 scripts/catalog-release.py --fast   # при смене version / tgz
```

RideTube upstream: `fetch-ridetube.py` → `apply-ridetube-patches.py` → `verify-ridetube.py` — [ridetube-krikun-patches.md](ridetube-krikun-patches.md).

CI: [.github/workflows/preflight.yml](../.github/workflows/preflight.yml) на push/PR в `main`.