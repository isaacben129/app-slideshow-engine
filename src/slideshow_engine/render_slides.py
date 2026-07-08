#!/usr/bin/env python3
"""Render real slideshow images with text burned onto each slide.

TikTok slideshow != one image + long caption. This script creates one vertical image
per slide, using a shared symbolic pixel background and readable overlay text.
"""
from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
W, H = 1080, 1920
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def fit_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, max_height: int, start_size: int = 86):
    size = start_size
    while size >= 42:
        font = ImageFont.truetype(FONT_BOLD, size)
        avg_chars = max(10, int(max_width / (size * 0.55)))
        lines = []
        for para in text.split("\n"):
            lines.extend(textwrap.wrap(para, width=avg_chars) or [""])
        line_h = int(size * 1.22)
        height = len(lines) * line_h
        widths = [draw.textbbox((0, 0), line, font=font)[2] for line in lines]
        if height <= max_height and (not widths or max(widths) <= max_width):
            return font, lines, line_h
        size -= 4
    font = ImageFont.truetype(FONT_BOLD, 42)
    lines = textwrap.wrap(text, width=22)
    return font, lines, 54


def make_bg(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    # Cover crop to 9:16
    scale = max(W / img.width, H / img.height)
    img = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
    left = (img.width - W) // 2
    top = (img.height - H) // 2
    img = img.crop((left, top, left + W, top + H))
    # Pixelated but not unreadable
    small = img.resize((180, 320), Image.Resampling.BILINEAR)
    img = small.resize((W, H), Image.Resampling.NEAREST)
    return img.filter(ImageFilter.GaussianBlur(radius=0.6))


def render_slide(bg: Image.Image, text: str, idx: int, total: int, out: Path):
    img = bg.copy().convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    # dark translucent text panel
    margin = 90
    panel_top = 470
    panel_bottom = 1390
    od.rounded_rectangle((margin, panel_top, W - margin, panel_bottom), radius=46, fill=(18, 12, 28, 188), outline=(255, 246, 230, 50), width=3)
    # progress dots
    dot_y = 1660
    total_w = total * 28 + (total - 1) * 18
    start_x = (W - total_w) // 2
    for i in range(total):
        fill = (196, 30, 58, 255) if i == idx - 1 else (255, 246, 230, 110)
        x = start_x + i * 46
        od.ellipse((x, dot_y, x + 28, dot_y + 28), fill=fill)
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    font, lines, line_h = fit_text(draw, text, W - 2 * (margin + 70), panel_bottom - panel_top - 180)
    block_h = len(lines) * line_h
    y = panel_top + ((panel_bottom - panel_top) - block_h) // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (W - (bbox[2] - bbox[0])) // 2
        # shadow
        draw.text((x + 4, y + 4), line, font=font, fill=(0, 0, 0, 170))
        draw.text((x, y), line, font=font, fill=(255, 246, 230, 255))
        y += line_h
    small_font = ImageFont.truetype(FONT_REG, 34)
    draw.text((82, 1780), "Cherry • social reps", font=small_font, fill=(255, 246, 230, 190))
    draw.text((W - 190, 1780), f"{idx}/{total}", font=small_font, fill=(255, 246, 230, 190))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, quality=94)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", default="cherry")
    ap.add_argument("--post-index", type=int, default=0)
    ap.add_argument("--background", required=True)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()
    data = json.loads((ROOT / "campaigns" / args.app / "latest_campaign.json").read_text())
    post = data[args.post_index]
    slides = post["slides"]
    bg = make_bg(Path(args.background))
    out_dir = Path(args.out_dir) if args.out_dir else ROOT / "rendered" / args.app / post["title"].replace(" ", "_").replace("/", "-")
    for i, text in enumerate(slides, 1):
        render_slide(bg, text, i, len(slides), out_dir / f"slide_{i:02d}.jpg")
    meta = {"title": post["title"], "slides": slides, "out_dir": str(out_dir)}
    (out_dir / "manifest.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
