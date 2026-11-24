# Доступ к ГУ для отладки (и для агента в Cursor)

Cursor **не подключается к MGU напрямую** (нет MCP для iDrive). Схема: **SSH с Mac → логи с ГУ → вставка в чат**; агент сверяет с `mgu-krikun` и правит `main`.

Ключ **`~/.ssh/mgu_krikun`** — только **GitHub**. SSH на машину — отдельно (**mgu-store**, см. ниже).

## SSH с Mac (рекомендуется)

1. Клон [robertnisipeanu/mgu-store](https://github.com/robertnisipeanu/mgu-store).
2. Материалы в `~/.config/mgu-store/assets/` (`mgu_ssh_key_rsa.pem` и при первом разе **arm-debug** — не в git).
3. Сеть: **ENET** или хотспот **`DIRECT-BMW`**; на Mac relay **`127.0.0.1:2222`** → ГУ **:22**.
4. Подключение:

```bash
cd /path/to/mgu-store
node deploy/hu connect --hold 600
# во втором терминале — строку ssh, которую напечатает скрипт
```

Или, если relay уже поднят:

```bash
ssh -p 2222 \
  -o StrictHostKeyChecking=no \
  -o HostKeyAlgorithms=+ssh-rsa \
  -o PubkeyAcceptedAlgorithms=+ssh-rsa \
  -i "$HOME/.config/mgu-store/assets/mgu_ssh_key_rsa.pem" \
  root@127.0.0.1
```

Справка: `deploy/hu` (`connect`, `status`, `--wifi`, `--hu-ip`, `--lport 2222`).

**На ГУ без mgu-store:** иногда ставят пакет OpenSSH из Store (чужой каталог) — логин/пароль только из описания пакета; `mgu-krikun` своего SSH не поставляет.

## Только чтение (ошибки Store / apps)

```sh
journalctl -u mgu-updater --since "2 hours ago" --no-pager | tail -n 200
journalctl -u 'mgu-deploy*' --since "2 hours ago" --no-pager | tail -n 200
ls -la /var/opt/mgu-updater/ /var/opt/mgu-deploy/ 2>/dev/null
ls /run/mgu-updater/scratch/verified/*.tgz 2>/dev/null | tail -5
tar tzf /run/mgu-updater/scratch/verified/krikun_seti@*.tgz 2>/dev/null | head -25
mgu-uplink status 2>/dev/null || true
```

Не присылать в чат: ключи Xray, полные PAT GitHub, proxy URL с паролями.

## Блок для вставки агенту

```text
Коммит Store на экране: ______
Текст ошибки UI: ______
=== journalctl mgu-updater (tail 200) ===
...
=== tar tzf проблемного tgz (head 25) ===
...
```

См. также [first-run-hu.md](first-run-hu.md), [memory-hu.md](memory-hu.md).