#!/usr/bin/env python3
"""Generate and iteratively score TikTok slideshow campaigns for any app.

Deterministic and repo-friendly: every run writes markdown, JSON, Postiz payloads,
and an iteration log so changes are reviewable in git.
"""
from __future__ import annotations

import argparse
import html
import json
import random
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]

DEFAULT_PRIVATE_BEHAVIOR_TEMPLATES = [
    "You keep meaning to {pain_scene}, but the moment keeps passing.",
    "You know {pain_scene} matters, but somehow it becomes tomorrow's problem.",
    "You do the tiny workaround instead of {pain_scene}.",
    "You wait for motivation before {pain_scene}.",
    "You make the plan smaller in your head until it disappears.",
    "You say 'later' because later feels safer than starting.",
    "You want the outcome, but the first step feels weirdly heavy.",
    "You are not lazy. The system around this is just too vague.",
]

GENERIC_HIDDEN_LOOPS = [
    "The problem is not that you do not care. It is that the next step is too undefined.",
    "Your brain keeps choosing the familiar loop because it has no smaller script to run.",
    "Avoidance feels like relief, but it also teaches the habit to come back stronger.",
    "The longer you wait, the more the tiny action starts to feel like a whole identity test.",
    "You cannot build trust with yourself from intentions alone. You need repeatable evidence.",
]

GENERIC_REFRAMES = [
    "The goal is not to transform overnight.",
    "The win is not perfection. The win is a repeatable rep.",
    "Make it small enough to do before your brain talks you out of it.",
    "You do not need a bigger promise. You need a smaller next action.",
    "Consistency usually starts when the step gets embarrassingly specific.",
]

GENERIC_MICRO_ACTIONS = [
    "One action small enough to complete today.",
    "One note afterward: what did I expect, and what actually happened?",
    "One repeatable rep instead of a vague goal.",
    "One version so small it almost feels silly.",
    "One checkpoint you can actually mark done.",
]

GENERIC_COMMENT_TRIGGERS = [
    "What is the smallest version of this you could actually do today?",
    "Comment 'rep' if you know the first step is the hardest part.",
    "Save this for the next time the goal gets too vague.",
    "Which part is hardest: starting, continuing, or coming back after you miss?",
    "What tiny action would still feel like a real win?",
]

SYMBOLS = [
    ("blinking cursor", "a glowing blinking cursor in an empty message box slowly becoming a tiny open doorway"),
    ("receipt printer", "a long blank receipt from an old printer turning into a field notebook"),
    ("empty chair", "an empty chair under warm light with a tiny dotted path leading toward it"),
    ("storm radar", "a red storm radar circle fading into a quiet streetlight over a notebook"),
    ("unopened envelope", "an unopened envelope on a table with a tiny bridge of light behind it"),
    ("conference table", "a long abstract conference table with one tiny glowing chair"),
    ("locked door", "a small locked door with a colored keyhole and a staircase behind it"),
    ("missed call glow", "a phone screen glowing like a small moon beside an open window"),
    ("single candle", "a single candle beside two small cups on a quiet table"),
    ("tiny bridge", "a tiny bridge of light crossing a dark but gentle gap"),
]

CHERRY_BEHAVIOR_OVERRIDES = [
    "You rehearse a 10-second sentence for 20 minutes.",
    "You type the group chat reply, delete it, then type it again.",
    "You cancel plans and feel relief for exactly 12 minutes.",
    "You pretend not to see someone so you do not have to say hi first.",
    "You let the phone ring because answering feels like jumping off a ledge.",
    "You join the call hoping nobody asks you anything.",
    "You wait until the conversation moves on so your reply is no longer needed.",
    "You open the message, close it, and call that progress.",
    "You plan your exit before you even arrive.",
    "You know the answer but let the silence win.",
]

@dataclass
class Slideshow:
    app: str
    title: str
    hook: str
    slides: list[str]
    caption: str
    image_prompt: str
    hashtags: list[str]
    score: int
    score_breakdown: dict[str, int]
    mutation_notes: list[str]


def load_app(slug: str) -> dict:
    path = ROOT / "data" / f"apps_{slug}.json"
    if not path.exists():
        raise SystemExit(f"Missing app config: {path}")
    return json.loads(path.read_text())


def behavior_bank(app: dict) -> list[str]:
    if app["slug"] == "cherry":
        return CHERRY_BEHAVIOR_OVERRIDES
    scenes = app.get("pain_scenes") or ["do the thing you keep avoiding"]
    out = []
    for scene in scenes:
        for template in DEFAULT_PRIVATE_BEHAVIOR_TEMPLATES[:3]:
            out.append(template.format(pain_scene=scene))
    return out


def app_insert(app: dict) -> str:
    mechanisms = ", ".join(app.get("core_mechanism", [])[:2])
    return f"{app['app']} helps with {mechanisms} — without turning it into another vague intention."


def build_candidate(app: dict, rng: random.Random, i: int) -> Slideshow:
    hook = rng.choice(behavior_bank(app))
    loop = rng.choice(GENERIC_HIDDEN_LOOPS)
    reframe = rng.choice(GENERIC_REFRAMES)
    action = rng.choice(GENERIC_MICRO_ACTIONS)
    trigger = rng.choice(GENERIC_COMMENT_TRIGGERS)
    symbol_name, symbol_desc = rng.choice(SYMBOLS)
    desired = rng.choice(app.get("desired_outcomes") or ["make progress"])

    title = f"{app['app']} — {symbol_name.title()} Rep #{i:03d}"
    slides = [
        hook,
        loop,
        f"That is why '{desired}' needs a tiny repeatable system, not just another good intention.",
        reframe,
        action,
        "Then log what happened so the next rep gets easier to choose.",
        app_insert(app),
        trigger,
    ]
    cta = f"{app.get('primary_cta', 'Learn more')}: {app.get('primary_url', 'TODO')}"
    caption = (
        f"{hook} The fix is not a giant breakthrough. Start with one tiny rep, then make the next one easier to repeat. "
        f"{app['app']}: {app['positioning']} {cta}"
    )
    lane = app.get("visual_lane", {})
    palette = ", ".join(lane.get("palette", [])) or "warm, muted palette"
    avoid = ", ".join(lane.get("avoid", [])) or "readable text"
    image_prompt = (
        f"{lane.get('style', 'pixel-art dreamlike editorial background')}, {symbol_desc}, "
        f"palette: {palette}, emotionally evocative, symbolic not literal, soft grain, vertical 4:5 TikTok composition, avoid: {avoid}."
    )
    hashtags = app.get("hashtags", [])[:5]
    score_breakdown = score_candidate(app, hook, slides, caption, image_prompt, trigger)
    score = sum(score_breakdown.values())
    mutation_notes = critic_notes(score_breakdown)
    return Slideshow(app=app["slug"], title=title, hook=hook, slides=slides, caption=caption, image_prompt=image_prompt, hashtags=hashtags, score=score, score_breakdown=score_breakdown, mutation_notes=mutation_notes)


def score_candidate(app: dict, hook: str, slides: list[str], caption: str, image_prompt: str, trigger: str) -> dict[str, int]:
    pain_words = set(" ".join(app.get("pain_scenes", [])).lower().replace(",", "").split())
    hook_words = set(hook.lower().replace(",", "").replace(".", "").split())
    specificity = 12 + min(8, len(pain_words & hook_words))
    retention = 15 if len(slides) == 8 and all(len(s) <= 135 for s in slides[:6]) else 10
    emotional_markers = ["relief", "heavy", "avoid", "hardest", "vague", "win", "easier", "intention", "silence", "safe"]
    emotional = 8 + min(7, sum(1 for w in emotional_markers if any(w in s.lower() for s in slides)))
    reframe = 15 if any(x in " ".join(slides).lower() for x in ["goal is not", "win is not", "smaller", "evidence", "repeatable"]) else 8
    app_fit = 10 if app["app"] in " ".join(slides) and any(m.split()[0].lower() in " ".join(slides).lower() for m in app.get("core_mechanism", [])) else 6
    forbidden = [f.lower() for f in app.get("forbidden_claims", [])]
    safety = 0 if any(f and f in caption.lower() for f in forbidden) else 10
    engagement = 10 if "?" in trigger or "comment" in trigger.lower() or "save" in trigger.lower() else 5
    visual = 5 if "pixel" in image_prompt.lower() and "symbolic" in image_prompt.lower() and "avoid" in image_prompt.lower() else 3
    return {"hook_specificity": min(20, specificity), "retention_chain": retention, "emotional_resonance": min(15, emotional), "novel_reframe": reframe, "app_fit": app_fit, "safety": safety, "engagement_trigger": engagement, "visual_evocativeness": visual}


def critic_notes(score_breakdown: dict[str, int]) -> list[str]:
    notes = []
    if score_breakdown["hook_specificity"] < 16:
        notes.append("Make the hook name a more private, concrete behavior from the app avatar's life.")
    if score_breakdown["retention_chain"] < 15:
        notes.append("Shorten slides and strengthen swipe-to-next curiosity.")
    if score_breakdown["engagement_trigger"] < 10:
        notes.append("Add confession-style comment trigger or save trigger.")
    if score_breakdown["visual_evocativeness"] < 5:
        notes.append("Make visual symbol more evocative and less literal.")
    if not notes:
        notes.append("Candidate passes current conversion-oriented slideshow rubric; test with real analytics.")
    return notes


def select_winners(candidates: Iterable[Slideshow], n: int = 12) -> list[Slideshow]:
    uniq = {}
    for c in sorted(candidates, key=lambda x: x.score, reverse=True):
        if c.hook not in uniq:
            uniq[c.hook] = c
    return list(uniq.values())[:n]


def markdown_campaign(app: dict, winners: list[Slideshow]) -> str:
    lines = [f"# {app['app']} Slideshow Campaign — Generated Batch", "", f"CTA: {app.get('primary_cta')}", f"URL: {app.get('primary_url')}", ""]
    for idx, w in enumerate(winners, 1):
        lines += [f"## Post {idx}: {w.title}", "", f"Score: **{w.score}/100**", "", "### Slides", ""]
        lines += [f"{sidx}. {slide}" for sidx, slide in enumerate(w.slides, 1)]
        lines += ["", "### Caption", "", w.caption, "", "### Image Prompt", "", w.image_prompt, "", "### Hashtags", "", " ".join(w.hashtags), "", "### Critic Notes", ""]
        lines += [f"- {note}" for note in w.mutation_notes]
        lines.append("")
    return "\n".join(lines)


def postiz_payloads(winners: list[Slideshow]) -> list[dict]:
    payloads = []
    for w in winners:
        body = "".join(f"<p>{html.escape(slide)}</p>" for slide in w.slides)
        body += f"<p></p><p>{html.escape(w.caption)}</p><p></p><p>{html.escape(' '.join(w.hashtags))}</p>"
        payloads.append({"title": w.title[:90], "content_html": body, "attachment_needed": True, "image_prompt": w.image_prompt, "score": w.score, "settings": {"privacy_level": "SELF_ONLY", "duet": False, "stitch": False, "comment": True, "autoAddMusic": "no", "brand_content_toggle": False, "brand_organic_toggle": False, "video_made_with_ai": True, "content_posting_method": "UPLOAD"}})
    return payloads


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", default="cherry")
    parser.add_argument("--iterations", type=int, default=150)
    parser.add_argument("--seed", type=int, default=20260707)
    args = parser.parse_args()
    app = load_app(args.app)
    rng = random.Random(args.seed)
    candidates = [build_candidate(app, rng, i + 1) for i in range(args.iterations)]
    winners = select_winners(candidates, 12)

    out_dir = ROOT / "campaigns" / app["slug"]
    out_dir.mkdir(parents=True, exist_ok=True)
    (ROOT / "postiz").mkdir(parents=True, exist_ok=True)
    (ROOT / "run_logs").mkdir(parents=True, exist_ok=True)
    (out_dir / "latest_campaign.md").write_text(markdown_campaign(app, winners))
    (out_dir / "latest_campaign.json").write_text(json.dumps([asdict(w) for w in winners], indent=2))
    (ROOT / "postiz" / f"{app['slug']}_postiz_drafts.json").write_text(json.dumps(postiz_payloads(winners), indent=2))

    log = ["# Iteration Log", "", f"App: {app['app']}", f"Iterations requested: {args.iterations}", f"Candidates generated: {len(candidates)}", f"Winners selected: {len(winners)}", "", "## Top Scores", ""]
    for w in winners:
        log.append(f"- {w.score}/100 — {w.hook}")
    (ROOT / "run_logs" / f"{app['slug']}_iteration_log.md").write_text("\n".join(log) + "\n")
    print(json.dumps({"app": app["slug"], "iterations": args.iterations, "winners": len(winners), "top_score": winners[0].score}, indent=2))


if __name__ == "__main__":
    main()
