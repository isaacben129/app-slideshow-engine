#!/usr/bin/env python3
"""Render + publish ONE slideshow end-to-end (app-aware: cherry | held).

Used by the 3/day crons and for manual batches. Samples distinct backgrounds
from the app's pool (so we never need fresh image-gen to keep posting),
renders via render_slides.py, then publishes via postiz_publish_datauri.py.

App style lanes (render_slides.py handles the actual treatment via 'auto'):
  cherry -> pixelated pixel-art backgrounds, no faces.
  held   -> fully crisp (NOTHING pixelated); slide 1 uses the reaction FACE
            from faces/held/ (mood-matched), slides 2+ crisp photo scenes.

Usage:
  python scripts/make_post.py --app held  --post-index 0 --date 2026-07-11T11:00:00Z --sample-bg
  python scripts/make_post.py --app cherry --post-index 0 --date 2026-07-11T11:00:00Z --sample-bg
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENDER_PY = ROOT / ".venv_render" / "bin" / "python"
PUBLISH_PY = Path("/opt/hermes/.venv/bin/python")

# Per-app defaults so the same script serves every brand lane.
APP_DEFAULTS = {
    "cherry": {"pool": "backgrounds/cherry_pool", "title_prefix": "CHERRY", "faces": None},
    "held":   {"pool": "backgrounds/held_pool",   "title_prefix": "HELD",   "faces": "faces/held"},
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", default="cherry", choices=sorted(APP_DEFAULTS))
    ap.add_argument("--post-index", type=int, required=True)
    ap.add_argument("--date", required=True, help="UTC ISO datetime")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--sample-bg", action="store_true", help="sample N distinct bg from pool")
    ap.add_argument("--bg-pool", default=None)
    ap.add_argument("--face", default=None, help="override face image FILE or DIR (held)")
    ap.add_argument("--title-prefix", default=None)
    ap.add_argument("--privacy", default="PUBLIC_TO_EVERYONE")
    ap.add_argument("--type", default="schedule", choices=["schedule", "draft"])
    ap.add_argument("--integration-id", default=None, help="Postiz integration id override")
    args = ap.parse_args()

    defaults = APP_DEFAULTS[args.app]
    bg_pool = args.bg_pool or str(ROOT / defaults["pool"])
    title_prefix = args.title_prefix or defaults["title_prefix"]
    face_arg = args.face or (str(ROOT / defaults["faces"]) if defaults["faces"] else None)

    campaign = ROOT / "campaigns" / args.app / "latest_campaign.json"
    camp = json.loads(campaign.read_text())
    post = camp[args.post_index]
    n = len(post["slides"])

    if args.sample_bg:
        pool = sorted(p for p in Path(bg_pool).iterdir()
                      if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"})
        if len(pool) < n:
            raise SystemExit(f"bg pool {bg_pool} has {len(pool)} images but post needs {n}")
        chosen = random.sample(pool, n)
        bgdir = Path("/tmp") / f"{args.app}_bg" / f"p{args.post_index}"
        bgdir.mkdir(parents=True, exist_ok=True)
        for i, f in enumerate(chosen):
            shutil.copy(f, bgdir / f"bg_{i:02d}{f.suffix.lower()}")
        bg_arg = str(bgdir)
    else:
        bg_arg = None

    out = Path(args.out_dir) if args.out_dir else ROOT / "rendered" / args.app / f"post{args.post_index}"
    out.mkdir(parents=True, exist_ok=True)

    print(f"[render] {args.app} post {args.post_index}: {post.get('hook', post['title'])}  ({n} slides)")
    render_cmd = [
        str(RENDER_PY), str(ROOT / "src" / "slideshow_engine" / "render_slides.py"),
        "--app", args.app, "--post-index", str(args.post_index),
        "--out-dir", str(out),
    ]
    if bg_arg:
        render_cmd += ["--background-dir", bg_arg]
    if face_arg:
        render_cmd += ["--face", face_arg]
    subprocess.run(render_cmd, check=True)

    print(f"[publish] -> {args.date}")
    pub_cmd = [
        str(PUBLISH_PY), str(ROOT / "scripts" / "postiz_publish_datauri.py"),
        "--out-dir", str(out), "--post-index", str(args.post_index),
        "--app", args.app,
        "--date", args.date, "--title-prefix", title_prefix,
        "--privacy", args.privacy, "--type", args.type,
    ]
    if args.integration_id:
        pub_cmd += ["--integration-id", args.integration_id]
    subprocess.run(pub_cmd, check=True)
    print(f"[done] {args.app} post {args.post_index}")


if __name__ == "__main__":
    main()
