# Идентификация проекта (отдельно от работы)

Проект **mgu-krikun** — свой контур. Ключ **`mgu_krikun`**, не общий рабочий `id_ed25519` и не другие ключи.

## SSH-ключ проекта

| Файл | Назначение |
|------|------------|
| `~/.ssh/mgu_krikun` | приватный (только на Mac, в git **никогда**) |
| `~/.ssh/mgu_krikun.pub` | добавить в GitHub → maxkrikoun-gif → SSH keys |

Комментарий в ключе: `mgu-krikun`. Тип ключа: **RSA 4096** (в GitHub строка начинается с `ssh-rsa`, не `ssh-ed25519`). Это **не** имя файла `id_ed25519` — только алгоритм в начале строки.

Показать публичный ключ:

```bash
cat ~/.ssh/mgu_krikun.pub | pbcopy
```

## Git только для этого каталога

Remote (алиас в `~/.ssh/config`):

```text
git@github.com-mgu-krikun:maxkrikoun-gif/mgu-krikun.git
```

В репозитории включено `core.sshCommand` → всегда `~/.ssh/mgu_krikun`, даже если для `github.com` в config другие правила.

Проверка:

```bash
ssh -T git@github.com-mgu-krikun
# Hi maxkrikoun-gif!

git -C /Users/m.krikun/bmw remote -v
```

## GitHub

- Аккаунт: **maxkrikoun-gif**
- Репозиторий: **mgu-krikun**
- В GitHub только **`mgu_krikun.pub`**; лишние тестовые ключи удалить

## MGU / секреты

- VPN/Xray — не в git
- В Store **один** пользовательский источник: `maxkrikoun-gif/mgu-krikun` (всё внутри; **каждый** компонент — русские меню: [russian-only.md](russian-only.md))
- Репозиторий **private** → в MGU Store **Settings** нужен **GitHub Personal Access Token** (read доступ к repo), иначе catalog/assets не скачаются

Создание репо: [github-create.md](github-create.md). Каталог: [store-single-source.md](store-single-source.md).