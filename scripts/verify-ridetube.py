#!/usr/bin/env python3
"""Сверка дерева RideTube в mgu-krikun с upstream (git blob sha с GitHub API)."""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

REPO = "JustAnotherPU/ridetube"
BRANCH = "main"
SKIP_PREFIX = ("docs/media/",)
SKIP_PART = ("/.font-cache/",)


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def upstream_tree() -> dict[str, str]:
    url = f"https://api.github.com/repos/{REPO}/git/trees/{BRANCH}?recursive=1"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    out = {}
    for ent in data.get("tree", []):
        if ent.get("type") != "blob":
            continue
        p = ent["path"]
        if any(p.startswith(s) for s in SKIP_PREFIX):
            continue
        if any(s in p for s in SKIP_PART):
            continue
        out[p] = ent["sha"]
    return out


def local_path(root: Path, upstream_rel: str) -> Path:
    if upstream_rel in ("LICENSE", "THIRD_PARTY_LICENSES", "CHANGELOG.md"):
        return root / "licenses" / "ridetube" / upstream_rel
    if upstream_rel in ("README.md", "README.zh-CN.md", ".gitignore"):
        return root / "docs" / "ridetube-upstream" / upstream_rel
    if upstream_rel.startswith("tools/"):
        return root / "tools" / "ridetube" / upstream_rel[len("tools/") :]
    return root / upstream_rel


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    print("upstream: API tree…", flush=True)
    remote = upstream_tree()
    print(f"ожидается файлов: {len(remote)}", flush=True)

    ok = 0
    missing = []
    sha_mismatch = []
    local_only = []

    for rel, remote_sha in sorted(remote.items()):
        lp = local_path(root, rel)
        if not lp.is_file():
            missing.append(rel)
            continue
        data = lp.read_bytes()
        local_sha = git_blob_sha(data)
        if local_sha != remote_sha:
            sha_mismatch.append((rel, remote_sha[:8], local_sha[:8]))
        else:
            ok += 1

    # Локальные патчи — ожидаемо не совпадать с upstream
    patches = []
    app = root / "apps/jap_ridetube/app.json"
    if app.is_file() and "language" in app.read_text():
        patches.append("apps/jap_ridetube/app.json (возможен патч RU)")
    comp = root / "native/jap-ridetube-d/component.json"
    if comp.is_file() and "licenses/ridetube" in comp.read_text():
        patches.append("native/jap-ridetube-d/component.json (пути LICENSE)")

    print(f"\n=== sha OK: {ok}/{len(remote)} ===")
    if missing:
        print(f"НЕТ на диске ({len(missing)}):")
        for m in missing[:15]:
            print(f"  - {m}")
        if len(missing) > 15:
            print(f"  … и ещё {len(missing) - 15}")
    if sha_mismatch:
        print(f"SHA mismatch ({len(sha_mismatch)}):")
        for rel, r, l in sha_mismatch[:20]:
            print(f"  - {rel}  remote={r}… local={l}…")
        if len(sha_mismatch) > 20:
            print(f"  … и ещё {len(sha_mismatch) - 20}")
    if patches:
        print("\nНаши патчи (mismatch ожидаем):")
        for p in patches:
            print(f"  * {p}")

    # Структура
    checks = [
        ("apps/jap_ridetube", root / "apps/jap_ridetube" / "app.json"),
        ("apps/krikun_seti", root / "apps/krikun_seti" / "app.json"),
        ("native/jap-ridetube-d", root / "native/jap-ridetube-d" / "component.json"),
        ("native/ytdec", root / "native/ytdec" / "Makefile"),
        ("kit/", root / "kit" / "tools" / "build.py"),
        ("tools/krikun-xray", root / "tools/krikun-xray" / "component.json"),
        ("tools/ridetube", root / "tools/ridetube" / "release.py"),
    ]
    print("\n=== структура mgu-krikun ===")
    for name, p in checks:
        print(f"  {'OK' if p.is_file() else 'MISSING'}  {name}")

    if missing:
        return 2
    if sha_mismatch:
        # only fail if mismatch not explainable by patches
        patch_paths = {"apps/jap_ridetube/app.json", "native/jap-ridetube-d/component.json"}
        bad = [m for m, _, _ in sha_mismatch if m not in patch_paths]
        if bad:
            return 1
        print("\n(только патченные файлы отличаются от upstream — норма)")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())