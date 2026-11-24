# GitHub: два доступа (ГУ и Mac)

## Почему «вчерашний токен» не для релизов

Fine-grained PAT для **MGU Store** обычно делали так:

- **Repository:** только `mgu-krikun`
- **Contents: Read-only**

Этого **хватает ГУ** (скачать `main` / assets catalog).  
Для **загрузки Release** с Mac нужно **Contents: Read and write** (или `gh auth login`).

Токен в Store на ГУ **не попадает** в keychain Mac — агент его не видит.

## ГУ (как вчера)

Store → Settings → Accounts → **Add token**  
Fine-grained → `mgu-krikun` → **Contents: Read-only**.

## Mac (релиз `catalog`, агент)

Один раз:

```bash
gh auth login -h github.com -p https -w
```

Аккаунт **maxkrikoun-gif**, права на API через OAuth (релизы и upload).

Дальше агент:

```bash
bash scripts/publish-catalog-release.sh
```

Альтернатива без `gh`: fine-grained PAT с **Contents: Read and write** → только в keychain Mac, **не** в git:

```bash
# один раз, токен не в чат
export GH_TOKEN='github_pat_…'
security add-generic-password -a maxkrikoun-gif -s mgu-krikun-gh-release -w "$GH_TOKEN"
```

Скрипт публикации читает `mgu-krikun-gh-release` из keychain, если `gh` не залогинен.