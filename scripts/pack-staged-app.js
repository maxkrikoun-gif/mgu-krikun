'use strict';
/**
 * Pack apps/<id>/package/ into <id>@<version>.tgz (oap_pack flat layout).
 * Node 8 on the HU; единственный путь упаковки App Kit на branch:main (preparePackage).
 *
 * mgu-repo.json:
 *   "build": {
 *     "node": "scripts/pack-staged-app.js",
 *     "args": ["{dir}"],
 *     "output": "{dir}/{id}@{version}.tgz",
 *     "shared": ["scripts/pack-staged-app.js", "tools/oap_pack.js"]
 *   }
 */
const fs = require('fs');
const path = require('path');
const { pack } = require('../tools/oap_pack.js');

function fail(msg) {
    process.stderr.write(`${msg}\n`);
    process.exit(1);
}

if (process.argv.length !== 3) {
    fail('usage: node scripts/pack-staged-app.js <app-dir-relative-to-repo>');
}

const repoRoot = path.join(__dirname, '..');
const appRel = process.argv[2].replace(/\\/g, '/');
const appDir = path.join(repoRoot, appRel);
const specPath = path.join(appDir, 'app.json');
if (!fs.existsSync(specPath)) {
    fail(`${appRel}: no app.json`);
}
const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
const pkgDir = path.join(appDir, 'package');
if (!fs.existsSync(path.join(pkgDir, 'package.json'))) {
    fail(`${appRel}: no package/package.json`);
}
const name = `${spec.id}@${spec.version}.tgz`;
const outFile = path.join(appDir, name);
const files = pack(pkgDir, outFile);
const distDir = path.join(repoRoot, 'dist');
fs.mkdirSync(distDir, { recursive: true });
fs.copyFileSync(outFile, path.join(distDir, name));
const st = fs.statSync(outFile);
process.stdout.write(`${name}: ${st.size} bytes, ${files.length} paths\n`);