# GitHub: доступ с ГУ и Mac

## ГУ (Store)

Store → Settings → Accounts → **Add token**  
Fine-grained → репозиторий `mgu-krikun` → **Contents: Read-only**.

Этого хватает, чтобы клонировать ветку **`main`** и ставить компоненты из `mgu-repo.json`.

## Mac (разработка)

```bash
git push   # SSH ~/.ssh/mgu_krikun
```

Публикация отдельного релиза **`catalog`** для этого репозитория **не используется** — канал поставки только `main`.

Для приватного репо на ГУ тот же fine-grained PAT с **Contents: Read-only** (только в настройках Store на ГУ, не в git).