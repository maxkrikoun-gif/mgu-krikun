# Источник MGU Store — только `main`

На головном устройстве **один** наш источник каталога:

```text
maxkrikoun-gif/mgu-krikun
```

В настройках Store выбирается **ветка `main`** (repo tree, `mgu-repo.json` в корне).  
**Не** добавляй второй источник с тем же репо на **Releases → `catalog`** — это дубль и ломает список пакетов.

Релиз `catalog` на GitHub — **зеркало для Mac** (готовые `.tgz` без сборки на ГУ). Для ежедневной установки используй **main**.

---

## Что уже есть на твоём ГУ (не дублируем в git)

Подключённые ранее источники остаются для **базы BMW-сообщества**:

| Источник | Зачем |
|----------|--------|
| `robertnisipeanu/mgu-store` | deploy, python, updater, render, uplink |
| `cauliflowermossgrape/idrive7-apps` | idrive7-renderd, mgu-inputgate |
| `idrive-apps`, `car-apps`, system-monitor | как было |

Из **`mgu-krikun` / main** ставим **только своё**:

| Пакет | Назначение |
|-------|------------|
| **jap-node22** | Node 22 (сборка на ГУ из `tools/jap-node22/build.sh`) |
| **krikun-xray**, **Krikun: сеть** | обход / proxy Store |
| **jap-ridetube-d**, **YouT** | YouTube |
| **jap-filmix-d**, **FilmixProMax** | Filmix |

Store **склеивает** `requires` между источниками: база — из mgu-store / idrive7, приложения и node22/xray — из `mgu-krikun`.

---

## Приватный репозиторий

`mgu-krikun` — **private**. В Store → Settings нужен **GitHub token** с read на репо ([project-identity.md](project-identity.md), [github-tokens.md](github-tokens.md)).

---

## Сеть (Xray)

- **mgu-uplink** — из `robertnisipeanu/mgu-store` (интернет с телефона).
- **krikun-xray** — из `mgu-krikun` / main; proxy `socks5://127.0.0.1:1080` в updater.

---

## Публикация catalog (опционально, не для Store)

Только на Mac, если нужны готовые `.tgz`:

```bash
python3 scripts/catalog-release.py --fast
bash scripts/publish-catalog-release.sh
```

См. [catalog-release.md](catalog-release.md). На ГУ **не** переключайся на этот релиз как на источник.