#!/usr/bin/env python3
"""Сборка dist/catalog/ для GitHub Release «catalog»: все зависимости + наши пакеты.

  python3 scripts/catalog-release.py
  python3 scripts/catalog-release.py --base https://github.com/maxkrikoun-gif/mgu-krikun/releases/download/catalog/

Нужно: curl, git, node, python3.12 (опц.), unzip, cc (krikun-xray).
MGU_STORE: клон robertnisipeanu/mgu-store (скрипт кладёт в .cache/mgu-store).
Ridetube: без oap-sdk — берёт jap_ridetube / jap-ridetube-d с JustAnotherPU/ridetube catalog (сборка на ГУ — позже).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "catalog" / "deps.manifest.json"
OUT = ROOT / "dist" / "catalog"
CACHE = ROOT / ".cache"
ART_CACHE = CACHE / "artifacts"
MGU_STORE = Path(os.environ.get("MGU_STORE", CACHE / "mgu-store-minimal"))
RIDETUBE_CATALOG = "https://github.com/JustAnotherPU/ridetube/releases/download/catalog/catalog.json"
RIDETUBE_BASE = "https://github.com/JustAnotherPU/ridetube/releases/download/catalog/"
# Файлы ≥ этого размера — aria2c (-x16), остальное — один curl --parallel (-Z)
ARIA2_MIN_BYTES = 3 * 1024 * 1024


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def log(msg: str) -> None:
    print(msg, flush=True)


def _aria2_available() -> bool:
    return shutil.which("aria2c") is not None


def download_aria2(url: str, dest: Path, timeout: int = 1800) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    if part.is_file():
        part.unlink()
    log(f"  aria2 {dest.name} (16×) …")
    subprocess.run(
        [
            "aria2c",
            "-x",
            "16",
            "-s",
            "16",
            "-k",
            "1M",
            "--file-allocation=none",
            "--allow-overwrite=true",
            "--auto-file-renaming=false",
            f"--timeout={timeout}",
            "--max-tries=5",
            "-d",
            str(part.parent),
            "-o",
            part.name,
            url,
        ],
        check=True,
    )
    os.replace(part, dest)
    log(f"  ok {dest.name} ({dest.stat().st_size // 1024} KiB)")


def download_curl_one(url: str, dest: Path, timeout: int = 600) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    subprocess.run(
        [
            "curl",
            "-fsSL",
            "--connect-timeout",
            "30",
            "--max-time",
            str(timeout),
            "-C",
            "-",
            "-o",
            str(part),
            url,
        ],
        check=True,
    )
    os.replace(part, dest)


def download_curl_parallel(jobs: list[tuple[Path, str]], parallel_max: int, timeout: int = 600) -> None:
    if not jobs:
        return
    n = min(len(jobs), parallel_max)
    log(f"  curl -Z × {n} для {len(jobs)} мелких файлов …")
    cmd = [
        "curl",
        "-fsSL",
        "-Z",
        f"--parallel-max",
        str(n),
        "--connect-timeout",
        "30",
        "--max-time",
        str(timeout),
    ]
    for dest, url in jobs:
        dest.parent.mkdir(parents=True, exist_ok=True)
        cmd.extend(["-o", str(dest.with_suffix(dest.suffix + ".part")), url])
    subprocess.run(cmd, check=True)
    for dest, _ in jobs:
        part = dest.with_suffix(dest.suffix + ".part")
        os.replace(part, dest)
        log(f"  ok {dest.name} ({dest.stat().st_size // 1024} KiB)")


def download(url: str, dest: Path, timeout: int = 600, size_hint: int = 0) -> None:
    if dest.is_file():
        return
    use_aria2 = _aria2_available() and size_hint >= ARIA2_MIN_BYTES
    if use_aria2:
        download_aria2(url, dest, timeout=timeout)
    else:
        log(f"  curl {dest.name} …")
        download_curl_one(url, dest, timeout=timeout)
        log(f"  ok {dest.name} ({dest.stat().st_size // 1024} KiB)")


def load_json_url(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def ensure_mgu_store() -> None:
    """Только deploy/hu + tools/oap_pack.js (~30 KiB). Полный git clone mgu-store не нужен."""
    hu = MGU_STORE / "deploy" / "hu"
    pack = MGU_STORE / "tools" / "oap_pack.js"
    if hu.is_file() and pack.is_file():
        return
    log("mgu-store-minimal: deploy/hu + tools/oap_pack.js")
    CACHE.mkdir(parents=True, exist_ok=True)
    (MGU_STORE / "deploy").mkdir(parents=True, exist_ok=True)
    (MGU_STORE / "tools").mkdir(parents=True, exist_ok=True)
    base = "https://raw.githubusercontent.com/robertnisipeanu/mgu-store/main"
    download(f"{base}/deploy/hu", hu, timeout=60)
    download(f"{base}/tools/oap_pack.js", pack, timeout=60)
    hu.chmod(0o755)


def pack_tool(tool_dir: Path) -> Path:
    dist = tool_dir / "dist"
    shutil.rmtree(dist, ignore_errors=True)
    dist.mkdir(parents=True)
    hu = MGU_STORE / "deploy" / "hu"
    subprocess.check_call(["node", str(hu), "artifact", str(tool_dir), "--out", str(dist)])
    tgxs = list(dist.glob("*.tgz"))
    if len(tgxs) != 1:
        sys.exit(f"pack_tool: ожидался один .tgz в {dist}, есть: {tgxs}")
    return tgxs[0]


def artifact_entry(path: Path, base: str) -> dict:
    name = path.name
    return {
        "name": name,
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
        "url": base + name if not base.startswith("http") else base + name,
    }


def artifact_url(comp: dict, base_url: str) -> str:
    art = comp["artifact"]
    return art.get("url") or (base_url + art["name"])


def prefetch_artifact_specs(specs: list[dict], parallel_max: int) -> None:
    """Кэш .cache/artifacts: мелкие — curl -Z пачкой; крупные — aria2 параллельно."""
    ART_CACHE.mkdir(parents=True, exist_ok=True)
    todo: list[dict] = []
    for s in specs:
        dest = ART_CACHE / s["name"]
        if dest.is_file() and sha256_file(dest) == s["sha256"]:
            continue
        todo.append(s)
    if not todo:
        log("  все .tgz уже в кэше")
        return
    small_jobs: list[tuple[Path, str]] = []
    big: list[dict] = []
    for s in todo:
        dest = ART_CACHE / s["name"]
        size = int(s.get("size") or 0)
        if size >= ARIA2_MIN_BYTES and _aria2_available():
            big.append(s)
        else:
            small_jobs.append((dest, s["url"]))
    download_curl_parallel(small_jobs, parallel_max)
    if big:
        workers = min(len(big), parallel_max)
        log(f"  aria2: {len(big)} крупных, потоков={workers}")
        with ThreadPoolExecutor(max_workers=workers) as pool:
            def grab(s: dict) -> str:
                download(s["url"], ART_CACHE / s["name"], size_hint=int(s.get("size") or 0))
                return s["name"]

            for fut in as_completed([pool.submit(grab, s) for s in big]):
                log(f"  готово: {fut.result()}")
    for s in todo:
        dest = ART_CACHE / s["name"]
        if not dest.is_file() or sha256_file(dest) != s["sha256"]:
            dest.unlink(missing_ok=True)
            sys.exit(f"sha256 mismatch for {s['name']}")


def copy_cached_to_out(name: str, out: Path) -> Path:
    src = ART_CACHE / name
    if not src.is_file():
        sys.exit(f"нет в кэше: {name}")
    dest = out / name
    shutil.copy2(src, dest)
    return dest


def excluded_from_catalog(manifest: dict) -> set[str]:
    return set(manifest.get("exclude_from_catalog") or [])


def collect_remote_artifacts(manifest: dict) -> tuple[list[dict], dict, dict]:
    """Upstream .tgz + ridetube (минус exclude_from_catalog)."""
    specs: list[dict] = []
    seen: set[str] = set()
    upstream: dict[str, dict] = {}
    skip = excluded_from_catalog(manifest)

    for src in manifest["sources"]:
        cat = load_json_url(src["catalog_url"])
        base = src.get("base_url", "")
        for cid in src["components"]:
            if cid in skip:
                continue
            comp = next(c for c in cat["components"] if c["id"] == cid)
            art = comp["artifact"]
            if art["name"] not in seen:
                seen.add(art["name"])
                specs.append(
                    {
                        "name": art["name"],
                        "url": artifact_url(comp, base),
                        "sha256": art["sha256"],
                        "size": int(art.get("size") or 0),
                    }
                )
            upstream[cid] = comp

    rt_cat = load_json_url(RIDETUBE_CATALOG)
    ridetube: dict[str, dict] = {}
    for cid in ("jap-ridetube-d", "jap_ridetube"):
        comp = next(c for c in rt_cat["components"] if c["id"] == cid)
        art = comp["artifact"]
        if art["name"] not in seen:
            seen.add(art["name"])
            specs.append(
                {
                    "name": art["name"],
                    "url": artifact_url(comp, RIDETUBE_BASE),
                    "sha256": art["sha256"],
                    "size": int(art.get("size") or 0),
                }
            )
        ridetube[cid] = comp

    return specs, upstream, ridetube


def ensure_idrive7_tar(ref: str) -> Path:
    tgz = CACHE / f"idrive7-apps-{ref}.tar.gz"
    if tgz.is_file() and tgz.stat().st_size > 1_000_000:
        return tgz
    url = f"https://codeload.github.com/cauliflowermossgrape/idrive7-apps/tar.gz/{ref}"
    # idrive7 tree — десятки МБ
    download(url, tgz, size_hint=20 * 1024 * 1024)
    return tgz


def _extract_idrive7_prefixes(tar: tarfile.TarFile, rel_paths: list[str]) -> dict[str, str]:
    prefixes: dict[str, str] = {}
    for rel_path in rel_paths:
        for m in tar.getmembers():
            if m.name.endswith(f"/{rel_path}/component.json"):
                prefixes[rel_path] = m.name[: -len("/component.json")]
                break
        if rel_path not in prefixes:
            sys.exit(f"idrive7: не найден {rel_path}/component.json")
    return prefixes


def _extract_idrive7_tree(tar: tarfile.TarFile, prefix: str, work: Path) -> None:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    plen = len(prefix) + 1
    for m in tar.getmembers():
        if m.name.startswith(prefix + "/") and m.isfile():
            rel = m.name[plen:]
            dest = work / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(m) as src, open(dest, "wb") as dst:
                shutil.copyfileobj(src, dst)


def fetch_idrive7_tools(tool_specs: list[dict], ref: str) -> dict[str, Path]:
    """Один проход по tar + параллельная упаковка."""
    tgz = ensure_idrive7_tar(ref)
    rel_paths = [s["path"] for s in tool_specs]
    with tarfile.open(tgz, "r:gz") as tar:
        prefixes = _extract_idrive7_prefixes(tar, rel_paths)
        for spec in tool_specs:
            work = CACHE / "idrive7-tools" / spec["id"]
            _extract_idrive7_tree(tar, prefixes[spec["path"]], work)

    out: dict[str, Path] = {}

    def pack_one(spec: dict) -> tuple[str, Path]:
        work = CACHE / "idrive7-tools" / spec["id"]
        return spec["id"], pack_tool(work)

    with ThreadPoolExecutor(max_workers=len(tool_specs)) as pool:
        for fut in as_completed([pool.submit(pack_one, s) for s in tool_specs]):
            tid, path = fut.result()
            out[tid] = path
    return out


def load_component_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_app_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


XRAY_BIN = ROOT / "tools/krikun-xray/build/xray"


def app_dist_tgz(app_id: str) -> Path | None:
    """dist/<id>@<ver>.tgz; для --language ru версия может быть 0.0.2-ru.1."""
    dist = ROOT / "dist"
    cands = sorted(dist.glob(f"{app_id}@*.tgz"), key=lambda p: p.stat().st_mtime, reverse=True)
    return cands[0] if cands else None


def version_from_dist_tgz(path: Path) -> str:
    name = path.name
    if "@" not in name or not name.endswith(".tgz"):
        sys.exit(f"неверное имя пакета: {name}")
    return name.rsplit("@", 1)[1][:-4]


def ensure_xray_built(*, force: bool = False) -> None:
    if not force and XRAY_BIN.is_file():
        log("  krikun-xray: бинарь в кэше, build.sh пропуск")
        return
    subprocess.check_call(["bash", str(ROOT / "tools/krikun-xray/build.sh")], cwd=ROOT)


def attach_store_icon(entry: dict, icon_basename: str, png_src: Path, out_dir: Path) -> None:
    """catalog.json: icon + iconSha256, PNG в assets релиза (≤128 KiB)."""
    if not png_src.is_file():
        return
    if png_src.stat().st_size > 128 * 1024:
        log(f"  warn: {png_src.name} > 128 KiB, Store может отказать")
    dest = out_dir / icon_basename
    shutil.copy(png_src, dest)
    entry["icon"] = icon_basename
    entry["iconSha256"] = sha256_file(dest)


def texts_ru(manifest: dict, cid: str, fallback_title: str, fallback_desc: str) -> dict:
    t = manifest.get("texts_ru", {}).get(cid)
    if t:
        return {"ru": t}
    return {"ru": {"title": fallback_title, "description": fallback_desc}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--base",
        default="https://github.com/maxkrikoun-gif/mgu-krikun/releases/download/catalog/",
        help="База URL для artifact.url в catalog.json",
    )
    ap.add_argument("--skip-xray-build", action="store_true", help="Не вызывать build.sh (нужен готовый build/xray)")
    ap.add_argument(
        "--fast",
        action="store_true",
        help="Тёплый кэш: без сети если sha ok; xray/apps только если нет артефактов (цель ~5 с)",
    )
    ap.add_argument(
        "--bundle-all-deps",
        action="store_true",
        help="Включить в catalog всё из deps.manifest (игнор exclude_from_catalog)",
    )
    ap.add_argument("-j", "--jobs", type=int, default=10, help="curl -Z / aria2 параллельность")
    args = ap.parse_args()
    base = args.base if args.base.endswith("/") else args.base + "/"

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if args.bundle_all_deps:
        manifest = {**manifest, "exclude_from_catalog": []}
    exc = excluded_from_catalog(manifest)
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)

    t0 = time.monotonic()
    log("=== catalog-release: старт ===")
    if args.fast:
        args.skip_xray_build = args.skip_xray_build or XRAY_BIN.is_file()
    if exc:
        log(f"  не пакуем (уже в других источниках Store): {', '.join(sorted(exc))}")
    ensure_mgu_store()
    components: list[dict] = []
    by_id: dict[str, dict] = {}

    log("=== 0/5: параллельная загрузка .tgz (кэш .cache/artifacts) ===")
    art_specs, upstream_comps, ridetube_comps = collect_remote_artifacts(manifest)
    id7 = manifest["idrive7_tools"]
    id7_ref = id7["ref"]
    id7_tool_specs = [t for t in id7["tools"] if t["id"] not in exc]

    def prefetch_id7() -> str | None:
        if not id7_tool_specs:
            return None
        ensure_idrive7_tar(id7_ref)
        return f"idrive7-apps-{id7_ref}.tar.gz"

    if not _aria2_available():
        log("  подсказка: brew install aria2 — ускорит jap-node22 и mgu-python (16 потоков на файл)")
    with ThreadPoolExecutor(max_workers=2) as pool:
        f_art = pool.submit(prefetch_artifact_specs, art_specs, args.jobs)
        f_id7 = pool.submit(prefetch_id7) if id7_tool_specs else None
        f_art.result()
        if f_id7 is not None:
            f_id7.result()

    log("=== 1/5: catalog entries (база + jap-node22) ===")
    for cid, comp in upstream_comps.items():
        name = comp["artifact"]["name"]
        copy_cached_to_out(name, OUT)
        entry = dict(comp)
        entry["artifact"] = artifact_entry(OUT / name, base)
        tr = manifest["texts_ru"].get(cid)
        if tr:
            entry["texts"] = {"ru": tr}
        components.append(entry)
        by_id[cid] = entry

    if id7_tool_specs:
        log("=== 2/5: idrive7 kit tools ===")
        id7_tgz = fetch_idrive7_tools(id7_tool_specs, id7_ref)
    else:
        log("=== 2/5: idrive7 kit — пропуск (уже в cauliflowermossgrape/idrive7-apps) ===")
        id7_tgz = {}
    for spec in id7_tool_specs:
        cid = spec["id"]
        tgz = id7_tgz[cid]
        shutil.copy(tgz, OUT / tgz.name)
        cj = json.loads((CACHE / "idrive7-tools" / cid / "component.json").read_text())
        entry = {
            "id": cid,
            "kind": "tool",
            "title": cj.get("title", cid),
            "description": cj.get("description", ""),
            "version": cj["version"],
            "artifact": artifact_entry(OUT / tgz.name, base),
            "requires": cj.get("requires", {}),
            "uninstallable": cj.get("uninstallable", True),
            "mguHmi": cj.get("mguHmi", ["ID7"]),
            "texts": texts_ru(manifest, cid, cj.get("title", cid), cj.get("description", "")),
        }
        if cj.get("optional"):
            entry["optional"] = True
        if cid == "mgu-inputgate":
            entry["needs"] = ["renderer"]
        components.append(entry)
        by_id[cid] = entry

    log("=== 3/5: krikun-xray, jap-filmix-d ===")
    if not args.skip_xray_build:
        ensure_xray_built()
    elif not XRAY_BIN.is_file():
        sys.exit("нет tools/krikun-xray/build/xray — убери --skip-xray-build или один раз build.sh")

    def do_pack(path: str) -> Path:
        return pack_tool(ROOT / path)

    with ThreadPoolExecutor(max_workers=2) as pool:
        fx_fut = pool.submit(do_pack, "native/jap-filmix-d")
        xr_fut = pool.submit(do_pack, "tools/krikun-xray")
        xray_tgz = xr_fut.result()
        fx_path = fx_fut.result()
    shutil.copy(xray_tgz, OUT / xray_tgz.name)
    xc = load_component_json(ROOT / "tools/krikun-xray/component.json")
    xray_entry = {
        "id": "krikun-xray",
        "kind": "tool",
        "title": xc["title"],
        "description": xc["description"],
        "version": xc["version"],
        "artifact": artifact_entry(OUT / xray_tgz.name, base),
        "requires": xc["requires"],
        "uninstallable": True,
        "mguHmi": xc.get("mguHmi", ["ID7"]),
        "texts": xc.get("texts") or texts_ru(manifest, "krikun-xray", xc["title"], xc["description"]),
    }
    components.append(xray_entry)
    by_id["krikun-xray"] = xray_entry

    fx_tgz = fx_path
    shutil.copy(fx_tgz, OUT / fx_tgz.name)
    fc = load_component_json(ROOT / "native/jap-filmix-d/component.json")
    fx_tool = {
        "id": "jap-filmix-d",
        "kind": "tool",
        "title": fc["title"],
        "description": fc["description"],
        "version": fc["version"],
        "artifact": artifact_entry(OUT / fx_tgz.name, base),
        "requires": fc["requires"],
        "uninstallable": True,
        "internet": True,
        "mguHmi": fc.get("mguHmi", ["ID7"]),
        "texts": fc.get("texts"),
    }
    components.append(fx_tool)
    by_id["jap-filmix-d"] = fx_tool

    log("=== 4/5: YouT (jap-ridetube-d + jap_ridetube, re-host) ===")
    for cid in ("jap-ridetube-d", "jap_ridetube"):
        comp = ridetube_comps[cid]
        name = comp["artifact"]["name"]
        copy_cached_to_out(name, OUT)
        entry = dict(comp)
        entry["artifact"] = artifact_entry(OUT / name, base)
        if cid == "jap_ridetube":
            entry["texts"] = {
                "ru": {
                    "title": "YouT",
                    "description": "YouTube в машине. RU по умолчанию. Proxy Store (krikun-xray).",
                }
            }
            attach_store_icon(entry, "jap_ridetube.png", ROOT / "apps/jap_ridetube/icon.png", OUT)
        elif cid == "jap-ridetube-d":
            entry["texts"] = {
                "ru": {
                    "title": "YouT (сервис)",
                    "description": "Демон YouTube на ГУ.",
                }
            }
        components.append(entry)
        by_id[cid] = entry

    log("=== 5/5: Krikun: сеть, FilmixProMax (build.py) ===")
    repo_comps = {c["id"]: c for c in json.loads((ROOT / "mgu-repo.json").read_text())["components"]}
    app_ids = ("krikun_seti", "filmix_promax")
    need_build = [
        aid
        for aid in app_ids
        if not (args.fast and app_dist_tgz(aid) is not None)
    ]
    if need_build:
        subprocess.check_call(
            [sys.executable, str(ROOT / "kit/tools/build.py"), "--language", "ru", *need_build],
            cwd=ROOT,
        )
    elif app_ids:
        log("  apps: dist/*.tgz из кэша (--fast)")
    for app_id in ("krikun_seti", "filmix_promax"):
        app = load_app_json(ROOT / "apps" / app_id / "app.json")
        raw_pkg = app_dist_tgz(app_id)
        if raw_pkg is None:
            sys.exit(f"build.py не создал dist/{app_id}@*.tgz")
        ver = version_from_dist_tgz(raw_pkg)
        pack_path = OUT / raw_pkg.name
        strip_oap_sdk(raw_pkg, pack_path)
        req_entry = repo_comps[app_id]
        entry = {
            "id": app_id,
            "kind": "app",
            "title": app.get("title", app_id),
            "description": app.get("description", ""),
            "version": ver,
            "artifact": artifact_entry(pack_path, base),
            "requires": req_entry["requires"],
            "uninstallable": True,
            "mguHmi": app.get("mguHmi", ["ID7"]),
            "texts": app.get("texts") or req_entry.get("texts"),
        }
        attach_store_icon(entry, f"{app_id}.png", ROOT / "apps" / app_id / "icon.png", OUT)
        components.append(entry)
        by_id[app_id] = entry

    # optional: touch renderer
    if (ROOT / "native/mgu-render-id7-touch/component.json").is_file():
        try:
            ttgz = pack_tool(ROOT / "native/mgu-render-id7-touch")
            shutil.copy(ttgz, OUT / ttgz.name)
            tc = load_component_json(ROOT / "native/mgu-render-id7-touch/component.json")
            te = {
                "id": tc["id"],
                "kind": "tool",
                "title": tc["title"],
                "description": tc["description"],
                "version": tc["version"],
                "artifact": artifact_entry(OUT / ttgz.name, base),
                "requires": tc.get("requires", {}),
                "optional": True,
                "uninstallable": True,
                "mguHmi": tc.get("mguHmi", ["ID7"]),
                "texts": {
                    "ru": {
                        "title": "Касание на весь экран",
                        "description": "Для YouT: левая кромка экрана в приложении (опционально).",
                    }
                },
            }
            components.append(te)
        except Exception as e:
            print(f"  skip mgu-render-id7-touch: {e}")

    note = (
        "maxkrikoun-gif/mgu-krikun: наши пакеты + jap-node22/YouT/Filmix/xray; "
        "mgu-store и idrive7-renderd — из других источников Store"
        if exc
        else "maxkrikoun-gif/mgu-krikun — полный catalog (все зависимости внутри)"
    )
    catalog = {"schema": 2, "comment": note, "components": components}
    (OUT / "catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    elapsed = time.monotonic() - t0
    print("\n=== dist/catalog ===")
    for n in sorted(OUT.iterdir()):
        if n.is_file():
            print(f"{n.stat().st_size:>12}  {n.name}")
    log(f"=== готово за {elapsed:.1f} с ===")
    if elapsed > 15 and args.fast:
        log("  подсказка: первый прогон дольше (xray/jap-node22); повторный --fast обычно <10 с")


def strip_oap_sdk(src: Path, dst: Path, mtime: int = 0) -> None:
    """OAP .tgz без node_modules/oap-sdk (как tools/ridetube/release.py)."""
    import gzip
    import io

    mtime = mtime or int(os.environ.get("SOURCE_DATE_EPOCH", "0"))
    with tarfile.open(src, "r:gz") as tar:
        members = [(m, tar.extractfile(m).read() if m.isfile() else None) for m in tar.getmembers()]
    keep = [(m, d) for m, d in members if "node_modules/oap-sdk" not in m.name]
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.USTAR_FORMAT) as out:
        for m, d in sorted(keep, key=lambda x: x[0].name):
            m.uid = m.gid = 0
            m.uname = m.gname = ""
            m.mtime = mtime
            out.addfile(m, io.BytesIO(d) if d is not None else None)
    with open(dst, "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=mtime, filename="") as g:
        g.write(buf.getvalue())


if __name__ == "__main__":
    main()