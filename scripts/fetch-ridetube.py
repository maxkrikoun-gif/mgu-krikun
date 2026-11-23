#!/usr/bin/env python3
"""Обновить RideTube (upstream) прямо в дерево mgu-krikun — без vendor/."""
from __future__ import annotations

import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = "JustAnotherPU/ridetube"
BRANCH = "main"
WORKERS = 24
TIMEOUT = 30
SKIP_PREFIX = ("docs/media/",)
SKIP_PART = ("/.font-cache/",)


def tree_paths() -> list[str]:
    url = f"https://api.github.com/repos/{REPO}/git/trees/{BRANCH}?recursive=1"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        data = json.load(r)
    if data.get("truncated"):
        sys.stderr.write("WARN: tree truncated\n")
    out = []
    for ent in data.get("tree", []):
        if ent.get("type") != "blob":
            continue
        p = ent["path"]
        if any(p.startswith(s) for s in SKIP_PREFIX):
            continue
        if any(s in p for s in SKIP_PART):
            continue
        out.append(p)
    return out


def target_path(root: Path, rel: str) -> Path:
    """Upstream path → путь в mgu-krikun."""
    if rel in ("LICENSE", "THIRD_PARTY_LICENSES", "CHANGELOG.md"):
        return root / "licenses" / "ridetube" / rel
    if rel in ("README.md", "README.zh-CN.md"):
        return root / "docs" / "ridetube-upstream" / rel
    if rel.startswith("tools/"):
        return root / "tools" / "ridetube" / rel[len("tools/") :]
    return root / rel


def fetch_one(root: Path, rel: str) -> tuple[str, str | None]:
    url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{rel}"
    target = target_path(root, rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=TIMEOUT) as r:
            target.write_bytes(r.read())
        return rel, None
    except Exception as e:
        return rel, str(e)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    print("API: список файлов…", flush=True)
    paths = tree_paths()
    print(f"скачать: {len(paths)} → корень {root}", flush=True)

    failed: list[str] = []
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(fetch_one, root, p): p for p in paths}
        for fut in as_completed(futs):
            rel, err = fut.result()
            done += 1
            if err:
                failed.append(f"{rel}: {err}")
            elif done % 50 == 0 or done == len(paths):
                print(f"  {done}/{len(paths)}", flush=True)

    app = root / "apps" / "jap_ridetube" / "app.json"
    if not app.is_file():
        print("FATAL: нет apps/jap_ridetube/app.json", file=sys.stderr)
        return 1
    print("Готово. Дальше: apply-ridetube-patches.py → verify-ridetube.py", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())