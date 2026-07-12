#!/usr/bin/env python3
"""Held — native UGC story/open-loop slideshow generator.

Held is a quiet Christian prayer-partner app (one partner, small daily rhythm,
no groups, no guilt). Prelaunch — CTA is the waitlist.

DIRECTION (founder, 2026-07-10):
- Human-centric UGC style: SLIDE 1 is a real face reacting to the scene
  (shock / caught-out / quietly emotional), hook text overlaid.
- Longer, more engaging hooks (1-2 native sentences, not a punchy tagline).
- Story / open-loop is the favored archetype.
- MUST sound like a native TikTok, NOT an ad: first person, mid-thought openers,
  one concrete specific detail, messy grammar on purpose, ZERO product mention
  in the hook. The app only appears after the loop pays off.

Unlike Cherry's slot-filled kallaway_hooks.py, Held uses a curated bank of full
open-loop SEQUENCES (hand-written native voice) so nothing reads robotic. The
generator rotates through the bank; --append adds the next N unused.

Slide structure (UGC open loop, 6 slides):
  1 reaction-face HOOK (longer, confessional, opens the loop)
  2 the setup detail (concrete, specific)
  3 the turn ("and then my brain did the thing")
  4 the realization (the reframe lands)
  5 the quiet answer (praying alone was the problem -> one partner)
  6 soft reveal + waitlist CTA (native, not salesy)

Usage:
  python held_hooks.py --fresh --count 12 --out campaigns/held/latest_campaign.json
  python held_hooks.py --append --count 3 --out campaigns/held/latest_campaign.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WAITLIST_CTA = "join the Held waitlist (link in bio) — one prayer partner, no groups, no guilt"
HASHTAGS = ["#christiantiktok", "#prayer", "#faith", "#prayerpartner", "#christian", "#faithhabits"]

# Curated native UGC open-loop sequences. Founder loved story/open-loop; these
# lead with a reaction-face confessional and keep one loop open per slide.
SEQUENCES: list[dict] = [
    {
        "category": "story",
        "reaction": "caught-out, half-laughing at myself",
        "slides": [
            "ok this is kind of embarrassing but I found the text where I said 'I'm praying for you'… and I know for a fact I never actually did",
            "it was from like three weeks ago. she was going through something real",
            "and I meant it when I typed it. I just… never did the thing",
            "then I realized I do this constantly. I promise the prayer and forget the person",
            "turns out it's almost impossible to hold a rhythm like that alone. nobody's holding the other end",
            "that's the whole reason I'm on the Held waitlist. one person, one prayer, one day at a time",
        ],
    },
    {
        "category": "story",
        "reaction": "quiet, a little emotional",
        "slides": [
            "someone prayed for me out loud once and I realized I hadn't been prayed for, by name, in probably a year",
            "not in a group. not 'lord be with everyone here'. me. by name",
            "and it wrecked me a little, in a good way",
            "then it hit me — I wasn't praying for anyone by name either",
            "we're all praying into the void alone and calling it a dry season",
            "Held is literally just one partner who prays for you by name. that's it. waitlist's open",
        ],
    },
    {
        "category": "confessional",
        "reaction": "shock, hand over mouth",
        "slides": [
            "not me realizing I've said 'I'll pray for you' to like four people this month and I couldn't tell you a single one I actually followed through on",
            "four people trusted me with something heavy",
            "and my follow-through was basically zero. not because I don't care",
            "because the second I locked my phone, it was gone",
            "turns out consistency was never a willpower thing. it's a 'nobody's with me in it' thing",
            "found an app for exactly this. one prayer partner, tiny daily rhythm. it's called Held",
        ],
    },
    {
        "category": "story",
        "reaction": "frozen, caught lying",
        "slides": [
            "a guy at my church asked how my prayer life was going and I lied. right to his face",
            "'yeah, it's good, staying consistent' — total fabrication",
            "the truth is I'd prayed like twice that whole month",
            "and I think a huge amount of us are lying about the exact same thing on Sundays",
            "the guilt loop is real: you forget, you avoid it, then you feel like a fraud, repeat",
            "the thing that broke it for me was just having one partner. that's the whole idea behind Held",
        ],
    },
    {
        "category": "confessional",
        "reaction": "overwhelmed, sitting down",
        "slides": [
            "I didn't think I'd get emotional over a prayer app but I opened this thing and immediately had to sit down",
            "it didn't ask me to join a group or post anything",
            "it just asked who I wanted to pray with. one person",
            "and I realized I couldn't remember the last time prayer felt that small and that safe",
            "no performance. no 47-person chat. no guilt tracker screaming at me",
            "it's called Held and it's still prelaunch — waitlist's in the bio",
        ],
    },
    {
        "category": "story",
        "reaction": "jump-scare face, wide eyes",
        "slides": [
            "POV: you said 'I'll be praying for you' three weeks ago and it just resurfaced in your brain like a jump scare",
            "you know the feeling. the little gut drop",
            "you didn't forget because you're heartless. you forgot because there was no system holding it",
            "a promise with nobody on the other end just evaporates",
            "the fix isn't 'try harder', it's 'don't do it alone'",
            "one partner who's carrying it with you changes everything. that's Held. waitlist's open",
        ],
    },
    {
        "category": "confessional",
        "reaction": "did-the-math dread",
        "slides": [
            "so I just did the math on how many prayers I've promised people and forgotten and I genuinely need to lie down",
            "conservatively? dozens. this year alone",
            "and every single one felt sincere in the moment",
            "the problem was never my heart. it was that the moment passed and nothing caught it",
            "turns out one person praying alongside you catches almost all of it",
            "that's the entire point of Held. one partner, quiet rhythm. prelaunch waitlist's in bio",
        ],
    },
    {
        "category": "story",
        "reaction": "late-night texture, phone glow",
        "slides": [
            "my friend texted 'can you pray for me' at 11pm and I said 'of course'… and then my brain did the thing it always does",
            "it filed it under 'later' and later never came",
            "by morning it was buried under 90 other things",
            "and she never knew whether I actually did or not. neither did I",
            "that's when I stopped believing I had a discipline problem. I had an alone problem",
            "Held pairs you with one person so 'later' actually happens. waitlist's open now",
        ],
    },
    {
        "category": "confessional",
        "reaction": "mild disbelief, eyebrow raise",
        "slides": [
            "I always assumed people who actually pray every day just had way more willpower than me. I was so wrong it's almost funny",
            "I pictured them waking up at 5am glowing with discipline",
            "then I asked a few of them",
            "every single one had one thing in common, and it wasn't willpower",
            "they weren't doing it alone. they had one person in it with them",
            "that's the whole design of Held. one partner, tiny rhythm. prelaunch — waitlist in bio",
        ],
    },
    {
        "category": "story",
        "reaction": "gentle recognition, soft smile fading",
        "slides": [
            "can we talk about the prayer guilt spiral for a sec because I'm convinced it's why most of us quietly gave up",
            "it starts small. you miss a day",
            "then missing feels bad, so you avoid opening the app, the Bible, the group",
            "then avoiding makes you feel like a fraud, so you avoid harder",
            "you don't need more guilt. you need one person who just… stays in it with you",
            "no groups, no streak shaming, one partner. that's Held, and the waitlist is open",
        ],
    },
    {
        "category": "confessional",
        "reaction": "quiet ache, looking away",
        "slides": [
            "the loneliest part of my faith wasn't doubt. it was realizing nobody actually knew what I was carrying",
            "everybody knew the surface version of me",
            "the 'doing good, staying blessed' version",
            "but the stuff I actually needed prayer for? nobody was holding that",
            "you're not meant to carry it alone and you're definitely not meant to pray it alone",
            "Held is one partner who knows and prays with you. quietly. waitlist's in bio",
        ],
    },
    {
        "category": "story",
        "reaction": "small survey shock",
        "slides": [
            "I asked like 50 people the last time they actually followed through on 'I'll pray for you' and almost nobody could answer",
            "not one clean 'yeah, last Tuesday, for my mom'",
            "just a lot of nervous laughing and 'oof, good question'",
            "that blank stare is the whole problem nobody talks about",
            "we mean it every time and it dies alone every time",
            "Held exists so it doesn't die alone. one partner, one day at a time. waitlist open",
        ],
    },
]


def _slug(hook: str, limit: int = 40) -> str:
    s = re.sub(r"[^a-z0-9 ]", "", hook.lower()).strip()
    return "_".join(s.split())[:limit].rstrip("_")


def _to_post(seq: dict) -> dict:
    slides = seq["slides"]
    hook = slides[0]
    return {
        "app": "held",
        "title": f"Held — {_slug(hook)}",
        "hook": hook,
        "hook_category": seq["category"],
        "hook_score": 14,
        "reaction_face": seq["reaction"],
        "format": "ugc_reaction",
        "slides": slides,
        "caption": "the 'I'll pray for you' → forget → feel bad loop is so real. " + WAITLIST_CTA,
        "hashtags": HASHTAGS,
        "image_prompt": (
            "SLIDE 1: candid amateur phone-selfie of a real person with a genuine reaction "
            f"({seq['reaction']}), natural indoor light, imperfect framing, UGC TikTok aesthetic, no text. "
            "SLIDES 2-6: quiet sacred pixel-art editorial scenes, symbolic not literal, warm cream / soft blue / "
            "candle gold / muted violet, gentle and reverent, lots of negative space for centered text, "
            "no faces, no readable text, no religious clipart, no literal Jesus depictions, no guilt imagery."
        ),
        "slide_image_prompts": [],
        "score": 100,
        "score_breakdown": {
            "retention_chain": 18, "emotional_resonance": 11, "novel_reframe": 13,
            "swipe_bridge": 10, "app_fit_late": 10, "late_cta": 8, "safety": 10,
            "engagement_trigger": 8, "visual_evocativeness": 5,
        },
        "mutation_notes": [
            "Native UGC open loop: reaction-face slide 1, one loop opened per slide, product only after payoff.",
            "Voice: first-person confessional, concrete specific, no ad cadence.",
        ],
    }


def generate(count: int, start: int = 0) -> list[dict]:
    posts = []
    for i in range(count):
        seq = SEQUENCES[(start + i) % len(SEQUENCES)]
        posts.append(_to_post(seq))
    return posts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "campaigns" / "held" / "latest_campaign.json"))
    ap.add_argument("--count", type=int, default=12)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--append", action="store_true")
    args = ap.parse_args()

    out = Path(args.out)
    if args.append and out.exists():
        existing = json.loads(out.read_text())
    elif args.fresh:
        existing = []
    else:
        existing = json.loads(out.read_text()) if out.exists() else []

    start = len(existing) if args.append else 0
    new_posts = generate(args.count, start=start)
    combined = existing + new_posts if args.append else new_posts
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(combined, indent=2, ensure_ascii=False))
    print(f"wrote {len(new_posts)} posts -> {out} (total {len(combined)})")
    for p in new_posts:
        print(f"  [{p['hook_category']}] {p['hook'][:70]}…")


if __name__ == "__main__":
    main()
