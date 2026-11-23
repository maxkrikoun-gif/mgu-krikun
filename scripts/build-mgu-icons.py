#!/usr/bin/env python3
"""Сборка icon.png 140×140 под плитку iDrive / MGU Store (скругление, safe zone)."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SIZE = 140
RADIUS = 32
PAD = 14
INNER = SIZE - 2 * PAD

YT_LOGO = Path(
    '/Users/m.krikun/.cursor/projects/Users-m-krikun-bmw/assets/'
    'image-3a0e2941-eb5a-4f80-9dd1-597db6438a85.png'
)


def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
        '/System/Library/Fonts/Supplemental/Arial.ttf',
        '/Library/Fonts/Arial Bold.ttf',
    ]
    if not bold:
        candidates = [
            '/System/Library/Fonts/Supplemental/Arial.ttf',
            '/Library/Fonts/Arial.ttf',
        ] + candidates
    for path in candidates:
        p = Path(path)
        if p.is_file():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def _tile(bg: tuple[int, int, int]) -> Image.Image:
    img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 0, SIZE - 1, SIZE - 1), radius=RADIUS, fill=bg + (255,))
    return img


def _play_triangle(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, fill: tuple[int, int, int]) -> None:
    h = r * math.sqrt(3) / 2
    pts = [(cx - r * 0.45, cy - h), (cx - r * 0.45, cy + h), (cx + r * 0.85, cy)]
    draw.polygon(pts, fill=fill)


def render_yout() -> Image.Image:
    img = _tile((15, 15, 15))
    ox = PAD
    oy = PAD
    box = INNER
    if YT_LOGO.is_file():
        logo = Image.open(YT_LOGO).convert('RGBA')
        lw, lh = logo.size
        scale = min(box / lw, (box - 18) / lh)
        nw, nh = max(1, int(lw * scale)), max(1, int(lh * scale))
        logo = logo.resize((nw, nh), Image.Resampling.LANCZOS)
        px = ox + (box - nw) // 2
        py = oy + (box - nh) // 2 - 4
        img.alpha_composite(logo, (px, py))
    else:
        draw = ImageDraw.Draw(img)
        rx, ry = SIZE // 2, SIZE // 2 - 6
        draw.rounded_rectangle((rx - 44, ry - 30, rx + 44, ry + 30), radius=12, fill=(255, 0, 0))
        _play_triangle(draw, rx + 4, ry, 22, (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = _font(22)
    label = 'YouT'
    tw = draw.textlength(label, font=font)
    draw.text(((SIZE - tw) / 2, SIZE - PAD - 20), label, fill=(180, 180, 180), font=font)
    return img


def render_filmix() -> Image.Image:
    img = _tile((20, 10, 12))
    draw = ImageDraw.Draw(img)
    cx, cy = SIZE // 2, SIZE // 2 - 8
    draw.rounded_rectangle((cx - 46, cy - 32, cx + 46, cy + 32), radius=14, fill=(229, 9, 20))
    _play_triangle(draw, cx + 3, cy, 26, (255, 255, 255))
    font = _font(16, bold=False)
    label = 'Filmix'
    tw = draw.textlength(label, font=font)
    tx = (SIZE - tw) / 2
    ty = SIZE - PAD - 20
    draw.text((tx, ty), label, fill=(245, 245, 245), font=font)
    ix = tx + draw.textlength('film', font=font) + 1
    draw.ellipse((ix, ty + 2, ix + 6, ty + 8), fill=(240, 90, 40))
    return img


def render_krikun_seti() -> Image.Image:
    img = _tile((13, 27, 42))
    draw = ImageDraw.Draw(img)
    accent = (60, 200, 255)
    cx, cy = SIZE // 2, SIZE // 2 - 6
    draw.arc((cx - 38, cy - 30, cx + 38, cy + 26), 200, 340, fill=accent, width=4)
    nodes = [(cx - 28, cy + 8), (cx, cy - 18), (cx + 30, cy + 10)]
    for x, y in nodes:
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=accent)
    draw.line([nodes[0], nodes[1], nodes[2]], fill=accent, width=3)
    draw.polygon(
        [(cx + 36, cy + 2), (cx + 52, cy + 10), (cx + 36, cy + 18)],
        fill=(100, 220, 140),
    )
    font = _font(15, bold=False)
    label = 'сеть'
    tw = draw.textlength(label, font=font)
    draw.text(((SIZE - tw) / 2, SIZE - PAD - 18), label, fill=(200, 220, 235), font=font)
    return img


def save(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format='PNG', optimize=True)
    print('wrote', path, path.stat().st_size, 'bytes')


def main() -> None:
    save(render_yout(), ROOT / 'apps/jap_ridetube/icon.png')
    save(render_filmix(), ROOT / 'apps/filmix_promax/icon.png')
    save(render_krikun_seti(), ROOT / 'apps/krikun_seti/icon.png')


if __name__ == '__main__':
    main()