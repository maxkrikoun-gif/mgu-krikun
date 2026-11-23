# Контракт проекта mgu-krikun

Жёсткие правила (не ослаблять без явного решения владельца).

1. **Один пользовательский источник в Store:** `maxkrikoun-gif/mgu-krikun` (см. [docs/store-single-source.md](docs/store-single-source.md)).
2. **Полная русификация** всего, что попадает в этот репозиторий и catalog: [docs/russian-only.md](docs/russian-only.md).
3. **Только Xray** на ГУ для обхода, без WireGuard/wireproxy: [docs/xray-on-hu-design.md](docs/xray-on-hu-design.md).
4. **Секреты VPN** (uuid, Reality, `*.vpn`) — не в git.
5. **SSH/GitHub** — только ключ `mgu_krikun`, аккаунт `maxkrikoun-gif`.
6. **RideTube и Xray — отдельные пакеты** в catalog (разные app/tool id), без `requires` друг на друга; связь только через `proxy` в `updater.local.conf`. См. [docs/components-separate.md](docs/components-separate.md).
7. **Обновление RideTube:** `python3 scripts/fetch-ridetube.py` → `python3 scripts/apply-ridetube-patches.py` → `python3 scripts/verify-ridetube.py` (ожидаемо 2 mismatch по патчам).
8. **Перед релизом catalog:** чеклист [docs/russian-only.md](docs/russian-only.md) + [docs/first-run-hu.md](docs/first-run-hu.md).