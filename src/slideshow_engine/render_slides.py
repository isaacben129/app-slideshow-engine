#!/usr/bin/env python3
"""Render real slideshow images with text burned onto each slide.

TikTok slideshow != one image + long caption. This script creates one vertical image
per slide, using either a shared background or one related background per slide.
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
    # Intentionally pixelated editorial look (founder direction: pixelated, not realistic).
    small = img.resize((200, 356), Image.Resampling.BILINEAR)
    img = small.resize((W, H), Image.Resampling.NEAREST)
    return img.filter(ImageFilter.GaussianBlur(radius=0.4))


def make_crisp(path: Path) -> Image.Image:
    """Cover-crop to 9:16 at full resolution — NO pixelation.

    Used for UGC reaction-face slides (slide 1). The face must stay crisp and
    photographic; pixelating it would kill the native/human feel.
    """
    img = Image.open(path).convert("RGB")
    scale = max(W / img.width, H / img.height)
    img = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
    left = (img.width - W) // 2
    top = (img.height - H) // 2
    return img.crop((left, top, left + W, top + H))


# Map a post's free-text reaction_face to a face-library filename stem.
_MOOD_KEYWORDS = {
    "shock": ["shock", "wide eyes", "jump", "disbelief", "hand over mouth"],
    "caught_out": ["caught", "embarrass", "half-laugh", "lying", "frozen"],
    "emotional": ["emotional", "ache", "tear", "cry", "quiet", "looking away", "soft"],
    "dread": ["dread", "math", "overwhelmed", "sitting down"],
    "recognition": ["recognition", "smile", "gentle"],
    "late_night": ["late-night", "late night", "phone glow"],
}


def resolve_face(face_arg: str | None, app: str, reaction_face: str) -> Path | None:
    """Find the reaction-face image for slide 1.

    - face_arg is a FILE -> use it directly.
    - face_arg is a DIR (or None -> faces/<app>/) -> pick by matching reaction_face
      to a mood file (shock.png, caught_out.png, ...); else neutral.png; else first file.
    Returns None if no face image is available (caller falls back to pixel bg).
    """
    if face_arg:
        p = Path(face_arg)
        if p.is_file():
            return p
        face_dir = p if p.is_dir() else None
    else:
        face_dir = None
    if face_dir is None:
        cand = ROOT / "faces" / app
        face_dir = cand if cand.is_dir() else None
    if face_dir is None:
        return None
    files = {p.stem.lower(): p for p in face_dir.iterdir()
             if p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}}
    if not files:
        return None
    rl = (reaction_face or "").lower()
    for mood, kws in _MOOD_KEYWORDS.items():
        if any(k in rl for k in kws) and mood in files:
            return files[mood]
    if "neutral" in files:
        return files["neutral"]
    return sorted(files.values())[0]


def load_background_paths(single_background: str | None, background_dir: str | None, total: int) -> list[Path]:
    if background_dir:
        bg_dir = Path(background_dir)
        files = sorted([p for p in bg_dir.iterdir() if p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}])
        if len(files) < total:
            raise SystemExit(f"background-dir {bg_dir} has {len(files)} images but slideshow needs {total}")
        return files[:total]
    if single_background:
        return [Path(single_background) for _ in range(total)]
    raise SystemExit("Provide --background or --background-dir")


def render_slide(bg: Image.Image, text: str, idx: int, total: int, out: Path,
                 app_label: str = "Cherry", is_crisp: bool = False):
    img = bg.copy().convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    # progress dots stay low and quiet (no text-background panel, no black overlay)
    dot_y = 1710
    total_w = total * 20 + (total - 1) * 16
    start_x = (W - total_w) // 2
    for i in range(total):
        fill = (196, 30, 58, 235) if i == idx - 1 else (255, 246, 230, 95)
        x = start_x + i * 36
        od.ellipse((x, dot_y, x + 20, dot_y + 20), fill=fill)
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    margin = 118
    if is_crisp:
        # UGC reaction-face slide: keep the face visible — hook sits in the top band.
        # Longer native hooks need room, so start higher and allow more height.
        text_top = 150
        text_height = 560
        start_size = 60
    else:
        # Centered text, placed moderately high but BELOW the upper third (no black overlay).
        text_top = 740
        text_height = 640
        start_size = 56
    font, lines, line_h = fit_text(draw, text, W - 2 * margin, text_height, start_size=start_size)
    if is_crisp:
        # Localized readability scrim behind the hook ONLY (not a full-slide black panel):
        # a soft rounded band sized to the text block so the face below stays clean.
        block_h = len(lines) * line_h
        scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(scrim)
        pad = 34
        sd.rounded_rectangle(
            (margin - pad, text_top - pad, W - margin + pad, text_top + block_h + pad),
            radius=40, fill=(8, 6, 12, 120),
        )
        scrim = scrim.filter(ImageFilter.GaussianBlur(radius=18))
        img = Image.alpha_composite(img, scrim)
        draw = ImageDraw.Draw(img)
    y = text_top
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (W - text_w) // 2
        # Tiny black letter outline only — no drop shadow, no overlay panel.
        draw.text((x, y), line, font=font, fill=(255, 246, 230, 250), stroke_width=3, stroke_fill=(6, 5, 10, 235))
        y += line_h
    small_font = ImageFont.truetype(FONT_REG, 28)
    draw.text((82, 1810), app_label, font=small_font, fill=(255, 246, 230, 150))
    draw.text((W - 132, 1810), f"{idx}/{total}", font=small_font, fill=(255, 246, 230, 150))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, quality=94)


def _parse_slide_set(arg: str | None, total: int, auto_value: set[int]) -> set[int]:
    """Parse a slide selector: 'auto' -> auto_value, 'all' -> every slide,
    'none'/'' -> empty, or a comma list of 1-indexed slides."""
    if arg is None or arg == "auto":
        return set(auto_value)
    a = arg.strip().lower()
    if a == "all":
        return set(range(1, total + 1))
    if a in {"", "none"}:
        return set()
    return {int(x) for x in a.split(",") if x.strip().isdigit()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", default="cherry")
    ap.add_argument("--post-index", type=int, default=0)
    ap.add_argument("--background", default=None)
    ap.add_argument("--background-dir", default=None)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--face", default=None,
                    help="Reaction-face image FILE or DIR for the face slide(s). "
                         "Default: faces/<app>/ (mood-matched to post reaction_face).")
    ap.add_argument("--face-slides", default="auto",
                    help="1-indexed slides that use the reaction FACE image. "
                         "'auto' (slide 1 when format==ugc_reaction), 'none', or comma list.")
    ap.add_argument("--crisp-slides", default="auto",
                    help="1-indexed slides rendered crisp/photographic (NOT pixelated). "
                         "'auto' (ALL slides when format==ugc_reaction, else none), "
                         "'all', 'none', or comma list. Cherry stays pixelated; Held is all-crisp.")
    args = ap.parse_args()
    data = json.loads((ROOT / "campaigns" / args.app / "latest_campaign.json").read_text())
    post = data[args.post_index]
    slides = post["slides"]
    n = len(slides)
    app_label = post.get("app", args.app).capitalize()
    is_ugc = post.get("format") == "ugc_reaction"

    # Face goes on slide 1 for UGC reaction posts; UGC posts are fully crisp (no pixelation).
    face_slides = _parse_slide_set(args.face_slides, n, {1} if is_ugc else set())
    crisp_slides = _parse_slide_set(args.crisp_slides, n, set(range(1, n + 1)) if is_ugc else set())
    # A face slide is always crisp — a pixelated face defeats the UGC hook.
    crisp_slides |= face_slides

    bg_paths = load_background_paths(args.background, args.background_dir, n)

    face_path = None
    if face_slides:
        face_path = resolve_face(args.face, post.get("app", args.app), post.get("reaction_face", ""))
        if face_path is None:
            print(f"[warn] face slides {sorted(face_slides)} requested but no face image found "
                  f"(faces/{post.get('app', args.app)}/ or --face); using pool background instead.")
            face_slides = set()

    # Build the per-slide image with the right treatment.
    backgrounds: list[Image.Image] = []
    for i in range(1, n + 1):
        if i in face_slides and face_path is not None:
            backgrounds.append(make_crisp(face_path))
        elif i in crisp_slides:
            backgrounds.append(make_crisp(bg_paths[i - 1]))
        else:
            backgrounds.append(make_bg(bg_paths[i - 1]))

    out_dir = Path(args.out_dir) if args.out_dir else ROOT / "rendered" / args.app / post["title"].replace(" ", "_").replace("/", "-")
    for i, (text, bg) in enumerate(zip(slides, backgrounds), 1):
        render_slide(bg, text, i, n, out_dir / f"slide_{i:02d}.jpg",
                     app_label=app_label, is_crisp=(i in crisp_slides))
    meta = {"title": post["title"], "slides": slides, "out_dir": str(out_dir),
            "background_mode": "dir" if args.background_dir else "single",
            "crisp_slides": sorted(crisp_slides), "face_slides": sorted(face_slides),
            "face_used": str(face_path) if face_path else None,
            "slide_image_prompts": post.get("slide_image_prompts", [])}
    (out_dir / "manifest.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
