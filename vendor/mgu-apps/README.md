# Vendored: JustAnotherPU/mgu-apps

`jap-node22@22.23.4.tgz` — тот же artifact, что в [mgu-apps catalog](https://github.com/JustAnotherPU/mgu-apps/releases/download/catalog/jap-node22%4022.23.4.tgz).

Пин: `main/external-deps.json` (size/sha256).

Обновление версии (на Mac):

```bash
curl -fsSL -o vendor/mgu-apps/jap-node22@NEW.tgz 'URL из mgu-apps'
shasum -a 256 vendor/mgu-apps/jap-node22@NEW.tgz   # сверить с external-deps
tar -xOf vendor/mgu-apps/jap-node22@NEW.tgz files/bin/node > tools/jap-node22/prebuilt/node
tar -xOf vendor/mgu-apps/jap-node22@NEW.tgz files/LICENSE > tools/jap-node22/prebuilt/LICENSE
tar -xOf vendor/mgu-apps/jap-node22@NEW.tgz files/check.sh > tools/jap-node22/check.sh
chmod +x tools/jap-node22/prebuilt/node tools/jap-node22/check.sh
```

`prebuilt/node` в git — **Git LFS** (>100 MB сырого ELF).