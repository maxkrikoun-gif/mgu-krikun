# Один репозиторий в Store

```text
maxkrikoun-gif/mgu-krikun
```

На ГУ Store сам вешает **ветку `main`** (repo tree) — отдельно канал не выбирается.  
Схема: [main-repo-tree.md](main-repo-tree.md).

**7 компонентов** — норма: 3 app + 4 tool из `mgu-repo.json`.

База (deploy, python, render, idrive7-renderd, inputgate, uplink) — из **других** уже стоящих источников.

Private: GitHub token в Store → Settings.

Catalog-релиз на GitHub — опционально для Mac (`scripts/publish-catalog-release.sh`), **не** второй источник на ГУ.