# Store — один репозиторий

```text
maxkrikoun-gif/mgu-krikun   (ветка main, repo tree)
```

**Не использовать** релиз GitHub с тегом `catalog` для этого репозитория — дублирует `main` и ломает единый контракт упаковки.

**jap-node22** встроен: `vendor/mgu-apps/jap-node22@22.23.4.tgz` + `tools/jap-node22` (тот же `.tgz`, что у JustAnotherPU/mgu-apps). **JustAnotherPU/mgu-apps в Store добавлять не нужно.**

Apps и tools из `mgu-repo.json` ставятся с ветки `main` (на ГУ — `pack-staged-app.js` / `component.json`, без второго зеркала `.tgz` в git).

База BMW: mgu-store, idrive7-apps — как уже стоят.

Схема: [main-repo-tree.md](main-repo-tree.md).