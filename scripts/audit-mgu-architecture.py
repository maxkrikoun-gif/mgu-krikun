#!/usr/bin/env python3
"""
Архитектурные проверки MGU по правилам upstream (mgu-store, mgu-apps, ridetube):
- prebuilt linux/amd64 ELF (не Mach-O);
- схема validateTool из mgu-deploy.js (id, semver, files/mode, check[0], dropins, hooks, mguHmi, oapcontroller);
- systemd + runas + NoNewPrivileges + CapabilityBoundingSet (CAP_SETUID/CAP_SETGID);
- shrinkwrap, permissions.json ACL tables, manifest.json, icon.png <= 128 KiB;
- Node 8 gate (check_node8.sh из ridetube) для apps/ и Node-8 демонов;
- ytd.js BUILT <= today UTC;
- предупреждения об upstream-расхождениях (--strict превращает WARN в FAIL):
  oap_link.build + needsSdk на branch:main, пустой state/internet-uids, file -b в check.sh, /run/<id>/s под runas.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MACH_O = (
    b"\xfe\xed\xfa\xce",
    b"\xfe\xed\xfa\xcf",
    b"\xca\xfe\xba\xbe",
    b"\xce\xfa\xed\xfe",
    b"\xcf\xfa\xed\xfe",
)
KIT_SQ = re.compile(r"""require\s*\(\s*'\./kit/""")
OAP_LINK_REQ_SQ = re.compile(r"""require\('([^']+)'\)""")
REQUIRES_OAP_SDK = re.compile(r"""require\(\s*(['"])oap-sdk\1\s*\)""")
BROWSERIFIED = re.compile(
    r"""^\s*(?:/\*[\s\S]*?\*/\s*)?(?:\(function\(\)\{function r\(e,n,t\)\{|!function\(\)\{return function r\(e,n,t\)\{)"""
)
USER_UID = re.compile(r"^User\s*=\s*(\d+)\s*$", re.M)
CAP_BOUNDING = re.compile(r"^CapabilityBoundingSet\s*=\s*(.*)$", re.M)
BANNED_IDS = re.compile(r"wireproxy|wireguard", re.I)
TOOL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
OCTAL_MODE_RE = re.compile(r"^[0-7]{3,4}$")
DROPIN_UNIT_RE = re.compile(r"^[A-Za-z0-9_.@-]{1,100}\.(service|socket|target|mount|path|timer)$")
DROPIN_NAME_RE = re.compile(r"^[A-Za-z0-9_.@-]{1,100}\.conf$")
NODE8_NEWER_API = re.compile(
    r"\.rmSync\(|\.replaceAll\(|\.matchAll\(|\.flatMap\(|\.flat\(|"
    r"Object\.fromEntries|Promise\.allSettled|globalThis|\(\?<[=!]"
)
NODE8_NEWER_SYNTAX = re.compile(r"\?\.[A-Za-z_$]|\?\?|catch\s*\{")
NODE8_BUILTINS = frozenset(
    {
        "assert",
        "buffer",
        "child_process",
        "crypto",
        "dgram",
        "dns",
        "events",
        "fs",
        "http",
        "https",
        "module",
        "net",
        "os",
        "path",
        "querystring",
        "readline",
        "stream",
        "string_decoder",
        "timers",
        "tls",
        "tty",
        "url",
        "util",
        "v8",
        "vm",
        "zlib",
    }
)


def safe_rel(p: object) -> bool:
    return (
        isinstance(p, str)
        and bool(p)
        and not p.startswith("/")
        and ".." not in p.split("/")
        and "\\" not in p
    )


def git_tracked_under(prefix: str, glob: str) -> list[Path]:
    proc = subprocess.run(
        ["git", "ls-files", glob],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    out: list[Path] = []
    for line in proc.stdout.splitlines():
        p = line.strip()
        if p.startswith(prefix):
            out.append(ROOT / p)
    return out


def strip_line_comment(line: str) -> str:
    if "//" in line:
        return line[: line.index("//")]
    return line


def check_prebuilt_elf(errs: list[str]) -> None:
    for base in (ROOT / "tools", ROOT / "native"):
        if not base.is_dir():
            continue
        for pre in base.glob("*/prebuilt/*"):
            if not pre.is_file():
                continue
            if pre.suffix.lower() in {".gz", ".pyz"} or pre.name in ("LICENSE", "node"):
                continue
            head = pre.read_bytes()[:4]
            if head in MACH_O:
                errs.append(f"prebuilt: {pre.relative_to(ROOT)} — Mach-O (нужен linux/amd64 ELF)")
                continue
            if pre.stat().st_size > 64 * 1024 and pre.suffix not in (".sh",):
                probe = subprocess.run(
                    ["file", "-b", str(pre)],
                    capture_output=True,
                    text=True,
                )
                out = probe.stdout.strip()
                if "Mach-O" in out:
                    errs.append(f"prebuilt: {pre.relative_to(ROOT)}: {out}")
                elif "ELF" in out and "x86-64" not in out and "executable" in out.lower():
                    errs.append(f"prebuilt: {pre.relative_to(ROOT)}: не x86-64 ELF: {out}")


def check_mgu_deploy_tool_schema(comp: dict, base: Path, errs: list[str], warns: list[str]) -> None:
    """Правила validateTool из robertnisipeanu/mgu-store deploy/unit/mgu-deploy.js."""
    cid = str(comp.get("id") or "")
    if not TOOL_ID_RE.match(cid):
        errs.append(f"{base.name}: component.json bad tool id {cid!r} (нужен ^[a-z0-9][a-z0-9-]*$)")
    if comp.get("kind") != "tool":
        errs.append(f"{cid}: kind != 'tool'")
    if not SEMVER_RE.match(str(comp.get("version") or "")):
        errs.append(f"{cid}: version {comp.get('version')!r} не x.y.z")

    hmi = comp.get("mguHmi")
    if hmi is not None:
        if (
            not isinstance(hmi, list)
            or not hmi
            or any(x not in ("ID7", "ID8") for x in hmi)
            or len(set(hmi)) != len(hmi)
        ):
            errs.append(f"{cid}: mguHmi должен быть непустым подмножеством ['ID7', 'ID8']")

    files = comp.get("files")
    if not isinstance(files, list):
        errs.append(f"{cid}: files[] отсутствует")
        files = []
    file_modes: dict[str, int] = {}
    for ent in files:
        if not isinstance(ent, dict):
            errs.append(f"{cid}: некорректный элемент files[]: {ent!r}")
            continue
        p = ent.get("path")
        mode = str(ent.get("mode") or "")
        if not safe_rel(p) or not OCTAL_MODE_RE.match(mode):
            errs.append(f"{cid}: bad files[] entry path={p!r} mode={mode!r}")
            continue
        file_modes[str(p)] = int(mode, 8)

    chk = comp.get("check")
    if chk is not None:
        if (
            not isinstance(chk, list)
            or not chk
            or not all(isinstance(x, str) and x for x in chk)
            or chk[0] not in file_modes
        ):
            errs.append(f"{cid}: check[0] обязан ссылаться на files[].path (mgu-deploy.js validateTool)")

    for hook in ("activate", "deactivate"):
        hv = comp.get(hook)
        if hv is None:
            continue
        ok = (
            isinstance(hv, list)
            and len(hv) > 0
            and all(isinstance(s, str) and s and ".." not in s.split("/") for s in hv)
            and (hv[0] == "node" or (hv[0] in file_modes and (file_modes[hv[0]] & 0o111) != 0))
        )
        if not ok:
            errs.append(f"{cid}: {hook} должен быть ['node', ...] или исполняемым files[].path без '..'")

    for d in comp.get("dropins") or []:
        if (
            not isinstance(d, dict)
            or not DROPIN_UNIT_RE.match(str(d.get("unit") or ""))
            or not DROPIN_NAME_RE.match(str(d.get("name") or ""))
        ):
            errs.append(f"{cid}: bad dropins entry {d!r}")
            continue
        src = base / str(d.get("from") or d.get("name"))
        if not src.is_file():
            errs.append(f"{cid}: drop-in missing {src.relative_to(base)}")

    for en in comp.get("enable") or []:
        if not isinstance(en, dict) or not safe_rel(en.get("unit")) or not safe_rel(en.get("target")):
            errs.append(f"{cid}: bad enable[] entry {en!r}")

    for n in list(comp.get("recmgr") or []) + list(comp.get("restart") or []):
        if n in ("oapcontroller", "oapcontroller.service"):
            errs.append(f"{cid}: {n} запрещён в recmgr/restart (mgu-deploy.js)")


def check_component_architecture(errs: list[str], warns: list[str]) -> None:
    for comp_path in sorted(
        list((ROOT / "native").glob("*/component.json"))
        + list((ROOT / "tools").glob("*/component.json"))
    ):
        comp = json.loads(comp_path.read_text(encoding="utf-8"))
        cid = comp.get("id") or comp_path.parent.name
        if BANNED_IDS.search(cid):
            errs.append(f"{cid}: идентификатор wireproxy/wireguard запрещён (CONSTRAINTS)")
        base = comp_path.parent
        check_mgu_deploy_tool_schema(comp, base, errs, warns)

        if comp.get("internet"):
            uids = comp.get("uids")
            if uids is None:
                errs.append(f"{cid}: internet:true без uids / state/internet-uids")
            elif isinstance(uids, str):
                if not safe_rel(uids):
                    errs.append(f"{cid}: bad internet uids path {uids!r}")
                else:
                    # Проверяем, что код демона реально пишет этот файл (паттерн jap-ridetube-d ytd.js)
                    needle = Path(uids).name
                    writes_uid = False
                    for src in base.rglob("*"):
                        if not src.is_file() or src.name == "component.json" or "/dist/" in str(src):
                            continue
                        if src.suffix in {".js", ".sh", ".py", ".go", ".c"}:
                            txt = src.read_text(encoding="utf-8", errors="replace")
                            if needle in txt or "uids.d" in txt:
                                writes_uid = True
                                break
                    if not writes_uid:
                        warns.append(
                            f"{cid}: internet:true с uids={uids!r}, но код в {base.relative_to(ROOT)} "
                            f"не пишет {needle}/uids.d (mgu-uplink блокирует прямой трафик от root)"
                        )
            elif not (isinstance(uids, list) and uids and all(isinstance(u, int) and u > 0 for u in uids)):
                errs.append(f"{cid}: internet uids должен быть непустым списком int > 0 или safeRel")

        unit_names = {u.get("name", "").replace(".service", "") for u in comp.get("units") or []}
        unit_names.discard("")
        recmgr_set = set(comp.get("recmgr") or [])
        for rn in recmgr_set:
            if rn not in unit_names and f"{rn}.service" not in {u.get("name") for u in comp.get("units") or []}:
                errs.append(f"{cid}: recmgr {rn!r} не совпадает с units[].name")
        if recmgr_set and unit_names - recmgr_set:
            missing_rec = sorted(unit_names - recmgr_set)
            warns.append(
                f"{cid}: units {missing_rec} не перечислены явно в recmgr[] "
                f"(mgu-deploy добавит сам, но лучше указать явно)"
            )

        for ent in comp.get("files") or []:
            rel = ent.get("from") or ent.get("path")
            if isinstance(rel, str) and "/vendor/" in rel.replace("\\", "/"):
                src = base / rel
                if not src.is_file():
                    errs.append(f"{cid}: vendor path missing {rel}")

        for chk_rel in comp.get("check") or []:
            chk_file = base / chk_rel
            if chk_file.is_file():
                chk_txt = chk_file.read_text(encoding="utf-8", errors="replace")
                if re.search(r"\bfile\s+-b\b", chk_txt):
                    warns.append(
                        f"{cid} {chk_rel}: использует `file -b` — на Yocto ГУ утилиты file может не быть "
                        f"(лучше прямой запуск бинарника, как в jap-wireproxy/check.sh)"
                    )

        for u in comp.get("units") or []:
            rel = u.get("from")
            name = u.get("name")
            if not rel or not name:
                continue
            unit_file = base / rel
            if not unit_file.is_file():
                errs.append(f"{cid}: unit file missing {rel}")
                continue
            text = unit_file.read_text(encoding="utf-8", errors="replace")
            internet_uids: set[str] = set()
            if comp.get("internet"):
                raw = comp.get("uids")
                if isinstance(raw, list):
                    internet_uids = {str(x) for x in raw}
            for m in USER_UID.finditer(text):
                uid = m.group(1)
                if uid in internet_uids:
                    errs.append(
                        f"{cid} {name}: User={uid} — на ГУ нет passwd; используй runas/setuid-helper"
                    )
            non_comment = "\n".join(
                ln for ln in text.splitlines() if not ln.lstrip().startswith("#")
            )
            if BANNED_IDS.search(non_comment):
                errs.append(f"{cid} {name}: wireproxy/wireguard в unit (не Xray)")

            # Если unit использует *-runas, проверяем CapabilityBoundingSet и RuntimeDirectory subdir
            if re.search(r"\b[a-z0-9_-]*runas\b", non_comment):
                cap_m = CAP_BOUNDING.search(non_comment)
                if cap_m:
                    caps = set(cap_m.group(1).split())
                    for needed_cap in ("CAP_SETUID", "CAP_SETGID"):
                        if needed_cap not in caps:
                            errs.append(
                                f"{cid} {name}: runas требует {needed_cap} в CapabilityBoundingSet "
                                f"(setgroups/setgid/setuid)"
                            )
                rt_m = re.search(r"^RuntimeDirectory\s*=\s*(\S+)", non_comment, re.M)
                setup_sh = base / "setup.sh"
                start_sh = base / "start.sh"
                if rt_m and setup_sh.is_file() and start_sh.is_file():
                    rt_dir = f"/run/{rt_m.group(1)}"
                    setup_txt = setup_sh.read_text(encoding="utf-8", errors="replace")
                    start_txt = start_sh.read_text(encoding="utf-8", errors="replace")
                    for sub_m in re.finditer(re.escape(rt_dir) + r"/([A-Za-z0-9_.-]+)", start_txt):
                        sub_path = f"{rt_dir}/{sub_m.group(1)}"
                        if not re.search(rf"{re.escape(sub_path)}(?![A-Za-z0-9_.-])", setup_txt):
                            warns.append(
                                f"{cid}: start.sh (под runas uid) использует {sub_path}, но setup.sh "
                                f"не создаёт/chown его от root (на systemd 237 {rt_dir} принадлежит root:root 0755)"
                            )
                        elif re.search(r"chmod\s+0?700\s+[\"']?\$R", setup_txt) and "STATE=" not in setup_txt:
                            # Проверяем, не читает ли OAP-приложение файл из этого каталога
                            for app_js in git_tracked_under("apps/", "apps/"):
                                if app_js.suffix == ".js" and sub_path in app_js.read_text(
                                    encoding="utf-8", errors="replace"
                                ):
                                    warns.append(
                                        f"{cid}: setup.sh ставит chmod 0700 на {sub_path}, но "
                                        f"{app_js.relative_to(ROOT)} (OAP uid) читает оттуда статус -> EACCES"
                                    )
                                    break


def check_oap_packages_and_unit_links(errs: list[str], warns: list[str]) -> None:
    repo = json.loads((ROOT / "mgu-repo.json").read_text(encoding="utf-8"))
    unit_apps = {
        c["id"]
        for c in repo.get("components", [])
        if c.get("kind") == "app" and c.get("build") == "unit"
    }

    for app_dir in sorted((ROOT / "apps").glob("*")):
        if not app_dir.is_dir():
            continue
        aid = app_dir.name
        icon = app_dir / "icon.png"
        if icon.is_file() and icon.stat().st_size > 128 * 1024:
            errs.append(f"{aid}: icon.png > 128 KiB ({icon.stat().st_size} B) — Store лимит 128 KiB")

        pkg_dir = app_dir / "package"
        pkg = pkg_dir / "package.json"
        if not pkg.is_file():
            continue
        pkg_data = json.loads(pkg.read_text(encoding="utf-8"))
        sw = pkg_dir / "npm-shrinkwrap.json"
        if not sw.is_file():
            errs.append(f"{aid}: нет npm-shrinkwrap.json (MainApp/oap_link)")
        else:
            sw_data = json.loads(sw.read_text(encoding="utf-8"))
            if sw_data.get("version") != pkg_data.get("version"):
                errs.append(
                    f"{aid}: shrinkwrap {sw_data.get('version')} != package.json {pkg_data.get('version')}"
                )

        perm = pkg_dir / "permissions.json"
        if perm.is_file():
            perm_data = json.loads(perm.read_text(encoding="utf-8"))
            for tbl in ("masterAccessTable", "masterRegistrationTable"):
                if not isinstance(perm_data.get(tbl), list):
                    errs.append(f"{aid}: permissions.json без списка {tbl} (MainApp aclManager)")

        someip_name = (pkg_data.get("oapAppSettings") or {}).get("someipManifest") or "manifest.json"
        someip_file = pkg_dir / someip_name
        if someip_file.is_file():
            sm = json.loads(someip_file.read_text(encoding="utf-8"))
            if not isinstance(sm, dict) or (
                sm.get("proxies") is not None and not isinstance(sm.get("proxies"), dict)
            ):
                errs.append(f"{aid}: {someip_name} некорректен (proxies должен быть объектом)")

        # Симуляция реального oap_link.build + mgu-deploy post-check для build: "unit" на branch:main
        mf = app_dir / "mgu-app.json"
        if aid in unit_apps and mf.is_file():
            m = json.loads(mf.read_text(encoding="utf-8"))
            modules = m.get("modules") or []
            sdk = set(m.get("sdk") or [])
            mod_ids = {f"./{Path(f).name}" for f in modules}
            if len(mod_ids) != len(modules):
                errs.append(f"{aid}/mgu-app.json: дублирующиеся basename в modules[] (oap_link.js link)")
            for mod_rel in modules:
                mod_file = app_dir / mod_rel
                if not mod_file.is_file():
                    continue
                src_text = mod_file.read_text(encoding="utf-8", errors="replace")
                for req_name in OAP_LINK_REQ_SQ.findall(src_text):
                    if req_name not in mod_ids and req_name not in sdk and req_name not in NODE8_BUILTINS:
                        warns.append(
                            f"{aid} (branch:main build:unit): {mod_rel} содержит require('{req_name}') — "
                            f"oap_link.build на ГУ откажет (не в modules/sdk/builtins)"
                        )
                        break

            # Проверка mgu-deploy.js:2970: needsSdk(out) после oap_link.build
            built_skip = {"javascript/app.js", "javascript/build.json"}
            for js_file in pkg_dir.rglob("*.js"):
                rel_js = js_file.relative_to(pkg_dir).as_posix()
                if rel_js in built_skip or "node_modules/" in rel_js:
                    continue
                txt = js_file.read_text(encoding="utf-8", errors="replace")
                if REQUIRES_OAP_SDK.search(txt) and not BROWSERIFIED.search(txt):
                    warns.append(
                        f"{aid} (branch:main build:unit): {rel_js} вызывает require('oap-sdk'), но "
                        f"oap_link.build не создаёт node_modules/oap-sdk -> mgu-deploy откажет на branch:main "
                        f"(в catalog release работает через preparePackage)"
                    )
                    break

            app_json = app_dir / "app.json"
            if app_json.is_file():
                aj = json.loads(app_json.read_text(encoding="utf-8"))
                missing_meta = [
                    k for k in ("title", "requires", "texts") if aj.get(k) and m.get(k) is None
                ]
                if missing_meta:
                    warns.append(
                        f"{aid} (branch:main build:unit): поля {missing_meta} есть в app.json, но не в "
                        f"mgu-app.json (sources.js на branch:main читает только mgu-app.json)"
                    )


def check_kit_single_quote(errs: list[str]) -> None:
    for js in git_tracked_under("apps/", "apps/"):
        if js.suffix != ".js":
            continue
        try:
            text = js.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        in_block = False
        for line in text.splitlines():
            s = line.strip()
            if "/*" in line and "*/" not in line:
                in_block = True
            if in_block:
                if "*/" in line:
                    in_block = False
                continue
            if s.startswith("*"):
                continue
            chunk = strip_line_comment(line)
            if KIT_SQ.search(chunk):
                errs.append(
                    f"{js.relative_to(ROOT)}: require('./kit/...') с одинарными кавычками "
                    f"(oap_link на ГУ — только double quotes для ./kit/)"
                )
                break


def check_node8_compat(errs: list[str]) -> None:
    """Node 8 gate по образцу JustAnotherPU/ridetube tools/check_node8.sh."""
    targets = [p for p in git_tracked_under("apps/", "apps/") if p.suffix == ".js"]
    rt_dir = ROOT / "native" / "jap-ridetube-d"
    if rt_dir.is_dir():
        for p in sorted(rt_dir.glob("*.js")):
            if p.name != "thumb.js":  # thumb.js работает под jap-node22
                targets.append(p)

    for js in targets:
        if not js.is_file():
            continue
        text = js.read_text(encoding="utf-8", errors="replace")
        in_block = False
        for lineno, line in enumerate(text.splitlines(), 1):
            s = line.strip()
            if "/*" in line and "*/" not in line:
                in_block = True
            if in_block:
                if "*/" in line:
                    in_block = False
                continue
            if s.startswith("*"):
                continue
            code = strip_line_comment(line)
            m_api = NODE8_NEWER_API.search(code)
            if m_api:
                errs.append(
                    f"node8: {js.relative_to(ROOT)}:{lineno}: API {m_api.group(0)!r} отсутствует в Node 8 на ГУ"
                )
                break
            m_syn = NODE8_NEWER_SYNTAX.search(code)
            if m_syn:
                errs.append(
                    f"node8: {js.relative_to(ROOT)}:{lineno}: синтаксис {m_syn.group(0)!r} не поддерживается Node 8"
                )
                break


def check_ridetube_built_date(errs: list[str]) -> None:
    """Проверка BUILT из JustAnotherPU/ridetube tools/release.py."""
    ytd = ROOT / "native" / "jap-ridetube-d" / "ytd.js"
    if not ytd.is_file():
        return
    text = ytd.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^const BUILT = '(\d{4}-\d\d-\d\d)';", text, re.M)
    today_utc = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    if not m or m.group(1) > today_utc:
        errs.append(
            f"jap-ridetube-d/ytd.js: BUILT={m.group(1) if m else None!r} > {today_utc} UTC "
            f"(отключит проверку дат TLS-сертификатов на ГУ с верными часами)"
        )


def check_no_wireproxy_artifacts(errs: list[str]) -> None:
    proc = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    for line in proc.stdout.splitlines():
        low = line.lower()
        if "wireproxy" in low or "wireguard" in low:
            if low.startswith("docs/") or low.endswith(".md"):
                continue
            errs.append(f"tracked file запрещённого стека: {line}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Архитектурный preflight MGU по правилам upstream.")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Считать предупреждения о расхождениях с upstream (WARN) ошибками (FAIL).",
    )
    args = ap.parse_args()

    errs: list[str] = []
    warns: list[str] = []
    check_prebuilt_elf(errs)
    check_component_architecture(errs, warns)
    check_oap_packages_and_unit_links(errs, warns)
    check_kit_single_quote(errs)
    check_node8_compat(errs)
    check_ridetube_built_date(errs)
    check_no_wireproxy_artifacts(errs)

    if args.strict and warns:
        errs.extend(f"[strict] {w}" for w in warns)
        warns = []

    if warns:
        print("WARN:")
        for w in warns:
            print(f"  ⚠ {w}")
    if errs:
        print("audit-mgu-architecture FAIL:")
        for e in errs:
            print(f"  ✗ {e}")
        return 1
    print("audit-mgu-architecture OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
