# Создать репозиторий на GitHub (maxkrikoun-gif)

Проект с нуля: аккаунт **maxkrikoun-gif**, SSH **`~/.ssh/mgu_krikun`** (см. [project-identity.md](project-identity.md)).

`gh` на этой машине не установлен — через веб:

1. Войти как **maxkrikoun-gif** на [github.com](https://github.com).
2. **Repositories → New** → имя, например: `mgu-krikun`.
3. **Private** рекомендуется (даже без ключей — личная схема сети).
4. Без README (уже есть локально).

Локально:

```bash
cd /Users/m.krikun/bmw
git init -b main
git add -A
git commit -m "docs: MGU uplink, Xray, RideTube chain"
git remote add origin git@github.com-mgu-krikun:maxkrikoun-gif/mgu-krikun.git
git push -u origin main
```

Проверка перед push:

```bash
git status
git diff --cached
# В индексе НЕ должно быть *.vpn и ключей
```

В Store: **`maxkrikoun-gif/mgu-krikun`**, ветка **`main`** ([store-single-source.md](store-single-source.md)).