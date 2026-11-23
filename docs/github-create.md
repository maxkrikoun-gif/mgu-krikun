# Создать репозиторий на GitHub (maxkrikoun-gif)

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
git commit -m "docs: MGU uplink, wireproxy, RideTube chain"
git remote add origin git@github.com:maxkrikoun-gif/mgu-krikun.git
git push -u origin main
```

Проверка перед push:

```bash
git status
git diff --cached
# В индексе НЕ должно быть *.vpn и ключей
```

В Store источник `maxkrikoun-gif/mgu-krikun` имеет смысл после первого **Releases/catalog** с приложением; пока достаточно документации и ручной настройки по `vpn-chain.md`.