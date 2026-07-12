#!/usr/bin/env python3
"""Generate reaction-face EXPRESSION VARIANTS from ONE reference photo.

Workflow the founder asked for: drop in a single reference photo of a person, then
produce that SAME person in different poses/expressions for the UGC reaction slides.
Identity is preserved by editing the reference image (not text-to-image), so the face
stays consistent across every slideshow.

Output: faces/<app>/<mood>.png  (mood = shock, caught_out, emotional, dread,
recognition, late_night, neutral) — exactly the filenames render_slides.py auto-picks
by matching each post's `reaction_face`.

REQUIREMENTS
------------
Needs an image model that accepts a REFERENCE IMAGE (identity-preserving edit):
  - OpenAI gpt-image-1 / gpt-image-2 via the images.edit endpoint  -> set OPENAI_API_KEY
  - (or adapt _generate_variant() to FAL InstantID / PuLID / IP-Adapter)
The built-in Hermes `image_generate` tool is text-to-image only and canNOT preserve a
reference identity, so this dedicated script exists. It reads OPENAI_API_KEY from the
environment or /opt/data/.env.

USAGE
-----
  python scripts/gen_face_variants.py --app held --reference /path/to/person.jpg
  python scripts/gen_face_variants.py --app held --reference person.jpg --moods shock,caught_out,emotional

Each generated face is a vertical, authentic amateur-selfie-style portrait of the SAME
person, natural indoor light, no glam, native TikTok UGC feel.
"""
from __future__ import annotations

import argparse
import base64
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The expression prompt per mood. Kept plain + authentic so results read as real UGC,
# not a stock model. Identity comes from the reference image, not these words.
MOOD_PROMPTS = {
    "shock": "same person, genuine shocked expression, wide eyes, eyebrows raised, mouth slightly open, caught off guard",
    "caught_out": "same person, caught-out half-embarrassed expression, awkward half-smile, looking slightly to the side",
    "emotional": "same person, quietly emotional expression, soft eyes, looking down or away, tender and vulnerable, holding back",
    "dread": "same person, overwhelmed anxious expression, tired eyes, slightly slumped, quietly dreading something",
    "recognition": "same person, gentle knowing half-smile, warm recognition, calm and soft",
    "late_night": "same person, tired late-night expression, dim warm phone-glow light on the face, lying down or slumped",
    "neutral": "same person, neutral candid resting expression, relaxed, natural",
}

STYLE = ("authentic amateur phone-selfie, vertical portrait, natural indoor light, "
         "no makeup glam, plain everyday look, slight softness, real UGC TikTok aesthetic, "
         "no text, no logos, keep the same face and identity as the reference")


def _load_env_key() -> str | None:
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    env = Path("/opt/data/.env")
    if env.exists():
        for ln in env.read_text().splitlines():
            if ln.startswith("OPENAI_API_KEY="):
                return ln.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _generate_variant(reference: Path, prompt: str, api_key: str, size: str = "1024x1536") -> bytes:
    """Call OpenAI images.edit with the reference face. Returns PNG bytes.

    Swap this function body to target FAL InstantID/PuLID if preferred.
    """
    from openai import OpenAI  # lazy import so the script loads without the dep

    client = OpenAI(api_key=api_key)
    with reference.open("rb") as fh:
        res = client.images.edit(
            model="gpt-image-1",
            image=fh,
            prompt=f"{prompt}. {STYLE}",
            size=size,
        )
    return base64.b64decode(res.data[0].b64_json)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", default="held")
    ap.add_argument("--reference", required=True, help="path to the reference face photo")
    ap.add_argument("--moods", default="all",
                    help="comma list of moods or 'all' (" + ",".join(MOOD_PROMPTS) + ")")
    ap.add_argument("--size", default="1024x1536")
    args = ap.parse_args()

    ref = Path(args.reference)
    if not ref.is_file():
        raise SystemExit(f"reference not found: {ref}")

    api_key = _load_env_key()
    if not api_key:
        raise SystemExit(
            "No OPENAI_API_KEY found (env or /opt/data/.env).\n"
            "Reference-based face generation needs an image model that accepts a reference image.\n"
            "Add OPENAI_API_KEY (gpt-image-1 edit access) or adapt _generate_variant() for FAL InstantID.\n"
            "UNTIL THEN: drop expression photos of the person manually into "
            f"faces/{args.app}/ named shock.png, caught_out.png, emotional.png, etc."
        )

    moods = list(MOOD_PROMPTS) if args.moods == "all" else [m.strip() for m in args.moods.split(",") if m.strip()]
    out_dir = ROOT / "faces" / args.app
    out_dir.mkdir(parents=True, exist_ok=True)

    for mood in moods:
        if mood not in MOOD_PROMPTS:
            print(f"[skip] unknown mood '{mood}'")
            continue
        print(f"[gen] {mood} from {ref.name} ...")
        png = _generate_variant(ref, MOOD_PROMPTS[mood], api_key, size=args.size)
        (out_dir / f"{mood}.png").write_bytes(png)
        print(f"[ok]  faces/{args.app}/{mood}.png")
    print(f"[done] variants in {out_dir}")


if __name__ == "__main__":
    main()
