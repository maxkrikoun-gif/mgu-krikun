#!/usr/bin/env python3
"""Проверка apps/*/mgu-app.json по rules tools/oap_link.js readManifest (mgu-store)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
REQ_SQ = re.compile(r"""require\s*\(\s*'([^']+)'\s*\)""")
NODE_BUILTINS = frozenset(
    {
        "fs",
        "path",
        "crypto",
        "net",
        "events",
        "zlib",
        "util",
        "os",
        "child_process",
        "http",
        "https",
        "url",
        "stream",
        "buffer",
        "string_decoder",
        "assert",
        "dns",
        "tls",
        "querystring",
        "dgram",
        "readline",
        "vm",
        "module",
    }
)


def safe_rel(p: str) -> bool:
    if not p or p.startswith("/") or ".." in p.split("/"):
        return False
    return True


def validate_app_dir(app_dir: Path) -> list[str]:
    errs: list[str] = []
    mf = app_dir / "mgu-app.json"
    if not mf.is_file():
        return []

    try:
        m = json.loads(mf.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"{app_dir.name}/mgu-app.json: JSON: {e}"]

    pref = f"{app_dir.name}/mgu-app.json"

    if m.get("schema") != 1:
        errs.append(f"{pref}: schema is not 1")
    if not APP_ID.match(m.get("id") or ""):
        errs.append(f"{pref}: bad id {m.get('id')!r}")
    if not SEMVER.match(m.get("version") or ""):
        errs.append(f"{pref}: version is not x.y.z: {m.get('version')!r}")
    tree = m.get("tree")
    pkg_json = app_dir / str(tree) / "package.json"
    if not safe_rel(str(tree or "")) or not pkg_json.is_file():
        return [f"SKIP {app_dir.name}: tree {tree!r} — нет package/ (build.py или unit позже)"]

    modules = m.get("modules")
    if (
        not isinstance(modules, list)
        or not modules
        or not all(
            isinstance(f, str)
            and safe_rel(f)
            and f.endswith(".js")
            and (app_dir / f).is_file()
            for f in modules
        )
    ):
        missing = []
        if isinstance(modules, list):
            for f in modules:
                if not (app_dir / f).is_file():
                    missing.append(f)
        errs.append(
            f"{pref}: modules must name the app's .js files, the entry first"
            + (f" (missing: {missing})" if missing else "")
        )

    sdk = m.get("sdk")
    if not isinstance(sdk, list) or not sdk or not all(isinstance(n, str) and n for n in sdk):
        errs.append(f"{pref}: sdk must list the require names the donor resolves")

    try:
        pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errs.append(f"{app_dir.name}/{tree}/package.json: JSON: {e}")
        return errs

    if pkg.get("name") != m.get("id") or pkg.get("version") != m.get("version"):
        errs.append(
            f"{pref}: {tree}/package.json is {pkg.get('name')}@{pkg.get('version')}, "
            f"not {m.get('id')}@{m.get('version')}"
        )

    main = pkg.get("main")
    if isinstance(main, str) and modules and isinstance(modules, list):
        first = modules[0]
        expected = f"{tree}/{main}" if not main.startswith(f"{tree}/") else main
        # entry file: first module should be the package.json main under tree
        main_path = f"{tree}/{pathlib_main(main)}"
        if first != main_path and first != main:
            errs.append(
                f"{pref}: first module {first!r} should be entry {main_path!r} (package.json main)"
            )

    # oap_link на ГУ (build на head unit): ids = ./<basename>; см. robertnisipeanu/mgu-store tools/oap_link.js
    if app_dir.name != "krikun_seti" or not isinstance(modules, list):
        return errs
    if isinstance(modules, list):
        ids = {f"./{Path(f).name}" for f in modules}
        sdk_list = m.get("sdk") if isinstance(m.get("sdk"), list) else []
        for rel in modules:
            text = (app_dir / rel).read_text(encoding="utf-8", errors="replace")
            for name in REQ_SQ.findall(text):
                if name in ids or name in sdk_list or name in NODE_BUILTINS:
                    continue
                if name.startswith("./kit/") or name.startswith("../"):
                    errs.append(
                        f"{pref}: {rel}: require('{name}') — на ГУ oap_link; "
                        f"для kit используй require(\"{name}\") (двойные кавычки)"
                    )
                else:
                    base = Path(name).name
                    if not name.endswith(".js") and f"./{base}" in ids:
                        errs.append(
                            f"{pref}: {rel}: require('{name}') → require('./{base}') для oap_link"
                        )
                    else:
                        errs.append(
                            f"{pref}: {rel}: require('{name}') — не модуль, не sdk (oap_link на ГУ)"
                        )

    return errs


def pathlib_main(main: str) -> str:
    return main.replace("\\", "/")


def main() -> int:
    apps = sorted((ROOT / "apps").glob("*/mgu-app.json"))
    if not apps:
        print("Нет apps/*/mgu-app.json", file=sys.stderr)
        return 1
    skips: list[str] = []
    all_errs: list[str] = []
    for mf in apps:
        res = validate_app_dir(mf.parent)
        for line in res:
            if line.startswith("SKIP "):
                skips.append(line)
            else:
                all_errs.append(line)
    for line in skips:
        print(line)
    if all_errs:
        print("FAIL mgu-app validation:\n" + "\n".join(f"  - {e}" for e in all_errs))
        return 1
    ok = len(apps) - len(skips)
    print(f"OK: {ok} mgu-app.json" + (f" (+{len(skips)} skip)" if skips else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())