#!/usr/bin/env python3
"""Generate and iteratively score TikTok slideshow campaigns for any app.

Hook-first pipeline:
1. Generate hook-only candidates.
2. Score hooks against TikTok slideshow research.
3. Build variable-length scripts only from the strongest hooks.
4. Write campaign artifacts and Postiz draft payloads.

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

CHERRY_HOOK_SEEDS = [
    {
        "hook": "the reply was four words",
        "category": "private_moment",
        "body": ["somehow it became a project", "you wrote it", "deleted it", "then waited until replying felt weird", "next time, make the reply smaller"],
        "symbol": "a glowing unopened envelope beside a small bridge of cherry-red pixels",
        "caption": "The reply does not have to be perfect. It just has to be small enough to send. Cherry is on Google Play.",
    },
    {
        "hook": "you saw them first, so now it counts",
        "category": "private_moment",
        "body": ["not saying hi feels like a decision", "so you look away first", "and pretend it was nothing", "Cherry is for practicing the tiny version"],
        "symbol": "a tiny red dot hiding behind a streetlight while two paths almost meet",
        "caption": "A small social rep is still a rep. Cherry is on Google Play.",
    },
    {
        "hook": "cancelling plans has a half-life",
        "category": "consequence",
        "body": ["first relief", "then quiet", "then the next invite feels heavier", "not a character flaw", "just a rep your brain never got"],
        "symbol": "a calendar square dissolving into a small open doorway with warm cherry light",
        "caption": "Avoidance is relief with interest. Cherry helps you practice tiny social reps without needing confidence first.",
    },
    {
        "hook": "you did not ignore them. you panicked quietly.",
        "category": "correction",
        "body": ["there was no plan", "just a sudden blank", "then the moment moved on without you", "practice the smallest hello first"],
        "symbol": "two tiny speech bubbles passing like ships under a muted purple sky",
        "caption": "Cherry helps turn social moments into small reps instead of identity tests.",
    },
    {
        "hook": "the relief lasted twelve minutes",
        "category": "consequence",
        "body": ["then the room got quiet", "then your brain replayed the invite", "then next time felt bigger", "that is the loop", "start with a smaller rep"],
        "symbol": "a soft clock face melting into a tiny warm doorway",
        "caption": "Relief can be expensive. Cherry helps you practice one tiny rep at a time.",
    },
    {
        "hook": "\u201chey\u201d should not feel like a cliff",
        "category": "question",
        "body": ["but sometimes it does", "because your brain treats tiny openings like jumps", "so make the jump smaller", "one word still counts"],
        "symbol": "a single word bubble floating beside a small cliff with cherry-red pixels below",
        "caption": "Start smaller than confidence. Cherry is on Google Play.",
    },
    {
        "hook": "you changed aisles to avoid saying hi",
        "category": "private_moment",
        "body": ["then acted like you needed cereal", "your brain called it safety", "your body called it relief", "but the rep was still there", "just smaller next time"],
        "symbol": "two soft supermarket aisles becoming parallel pixel paths that nearly meet",
        "caption": "Cherry is for the tiny social reps nobody else sees.",
    },
    {
        "hook": "the text got heavier after \u201cseen\u201d",
        "category": "private_moment",
        "body": ["before that it was just a message", "after that it became evidence", "so you waited", "and it got heavier", "answer the smallest honest version"],
        "symbol": "a glowing phone moon over a small notebook and a cherry-red dot",
        "caption": "The smallest honest reply is often the rep. Cherry is on Google Play.",
    },
    {
        "hook": "confidence is the wrong starting point",
        "category": "counterintuitive",
        "body": ["confidence comes after evidence", "evidence comes after reps", "reps have to be tiny enough to do", "start there"],
        "symbol": "a small staircase made of cherry-red pixels under a quiet streetlight",
        "caption": "Do not wait to feel confident. Build tiny evidence first with Cherry.",
    },
    {
        "hook": "your brain still counted it",
        "category": "consequence",
        "body": ["even if you called it nothing", "even if nobody noticed", "avoidance teaches too", "teach one tiny entrance instead"],
        "symbol": "a tiny receipt printer counting invisible marks beside an open notebook",
        "caption": "Cherry helps you log what happened and pick one smaller social rep.",
    },
    {
        "hook": "you rehearsed hello and still avoided them",
        "category": "private_moment",
        "body": ["the script was not the problem", "the first rep was too big", "make the moment smaller", "then practice that"],
        "symbol": "a blinking cursor turning into a tiny doorway under warm light",
        "caption": "Cherry is for shrinking social reps until they are doable.",
    },
    {
        "hook": "\u201cjust say hi\u201d skips the hard part",
        "category": "counterintuitive",
        "body": ["the hard part is the second before", "when your body votes no", "so practice that moment", "not the perfect version"],
        "symbol": "a tiny bridge of light stopping one pixel before the other side",
        "caption": "Cherry helps with the tiny moment before the social move.",
    },
    {
        "hook": "you waited until replying was weird",
        "category": "private_moment",
        "body": ["then the delay became the problem", "not the message", "so next time", "send the smaller reply first"],
        "symbol": "an envelope slowly growing a shadow while a cherry-red dot waits beside it",
        "caption": "Small replies beat perfect replies. Cherry is on Google Play.",
    },
    {
        "hook": "the exit plan started before you arrived",
        "category": "private_moment",
        "body": ["where to stand", "when to leave", "what excuse to use", "that is a lot of work", "practice one entrance instead"],
        "symbol": "a tiny map with one red exit sign and one warm open doorway",
        "caption": "Cherry helps turn social planning into tiny practice reps.",
    },
    {
        "hook": "social anxiety loves vague advice",
        "category": "counterintuitive",
        "body": ["be confident", "put yourself out there", "just talk more", "none of that is a rep", "make it specific"],
        "symbol": "a foggy signpost sharpening into one tiny cherry-red arrow",
        "caption": "Cherry turns vague social goals into tiny reps.",
    },
    {
        "hook": "you were not rude. you froze.",
        "category": "correction",
        "body": ["then judged yourself like it was a choice", "but your body moved first", "next time does not need courage", "it needs a smaller rep"],
        "symbol": "a frozen speech bubble thawing into one small cherry-red dot",
        "caption": "Cherry is for tiny social reps after the freeze.",
    },
    {
        "hook": "the call rang like an alarm",
        "category": "private_moment",
        "body": ["it was only a phone call", "your body did not care", "so you watched it end", "then felt ridiculous", "start with the smaller version"],
        "symbol": "a phone glowing like a red moon beside a quiet open window",
        "caption": "Cherry helps you practice the smaller version before the big one.",
    },
    {
        "hook": "you knew the answer and let silence win",
        "category": "private_moment",
        "body": ["not because you had nothing to say", "because entering felt too loud", "the rep is not knowing", "the rep is joining"],
        "symbol": "a single glowing chair at a long abstract table",
        "caption": "Cherry helps you practice tiny entries into social moments.",
    },
    {
        "hook": "the hard part was being perceived",
        "category": "correction",
        "body": ["not the words", "not the room", "not even the person", "just becoming visible", "practice tiny visibility"],
        "symbol": "a small cherry-red dot stepping into warm light from a muted shadow",
        "caption": "Tiny visibility reps count. Cherry is on Google Play.",
    },
    {
        "hook": "the group chat moved on without you",
        "category": "consequence",
        "body": ["which almost felt like relief", "until it felt like proof", "that is the trap", "send the smaller version sooner"],
        "symbol": "several tiny speech bubbles drifting past one quiet red dot",
        "caption": "Cherry helps you make social reps small enough to happen.",
    },
]

GENERIC_HOOK_TEMPLATES = [
    ("private_moment", "you keep making {pain_scene} a tomorrow problem"),
    ("consequence", "later is starting to cost more"),
    ("correction", "you are not lazy. the next step is too vague."),
    ("counterintuitive", "motivation is the wrong starting point"),
    ("question", "why does the first step feel so heavy?"),
]

FORBIDDEN_HOOK_PHRASES = [
    "stop scrolling",
    "you need to hear this",
    "changed my life",
    "unpopular opinion",
    "nobody talks about",
    "cured",
    "guaranteed",
    "clinically proven",
]


@dataclass
class HookCandidate:
    text: str
    category: str
    score: int
    score_breakdown: dict[str, int]
    body: list[str]
    symbol: str
    caption: str


@dataclass
class Slideshow:
    app: str
    title: str
    hook: str
    hook_category: str
    hook_score: int
    slides: list[str]
    caption: str
    image_prompt: str
    slide_image_prompts: list[str]
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
        return [seed["hook"] for seed in CHERRY_HOOK_SEEDS]
    scenes = app.get("pain_scenes") or ["do the thing you keep avoiding"]
    out = []
    for scene in scenes:
        for template in DEFAULT_PRIVATE_BEHAVIOR_TEMPLATES[:3]:
            out.append(template.format(pain_scene=scene))
    return out


def app_insert(app: dict) -> str:
    mechanisms = ", ".join(app.get("core_mechanism", [])[:2])
    return f"{app['app']} helps with {mechanisms} — without turning it into another vague intention."


def clean_words(text: str) -> list[str]:
    return text.lower().replace(",", "").replace(".", "").replace("?", "").replace("\u201c", "").replace("\u201d", "").split()


def score_hook(app: dict, text: str, category: str) -> dict[str, int]:
    words = clean_words(text)
    lower = text.lower()
    pain_terms = {"reply", "text", "seen", "hi", "hello", "call", "plans", "silence", "avoid", "froze", "rude", "confidence", "brain", "group", "chat", "aisles"}
    if app["slug"] != "cherry":
        pain_terms |= set(" ".join(app.get("pain_scenes", [])).lower().replace(",", "").split())
    private_specificity = 2 if len(pain_terms & set(words)) >= 2 else 1 if len(pain_terms & set(words)) == 1 else 0
    recognition_markers = ["you", "your", "reply", "text", "seen", "hi", "plans", "froze", "call", "group chat"]
    recognition = 2 if any(m in lower for m in recognition_markers[:2]) and any(m in lower for m in recognition_markers[2:]) else 1 if "you" in words or "your" in words else 0
    tension_terms = ["worst", "heavier", "half-life", "counted", "cliff", "wrong", "quietly", "relief", "cost", "weird", "decision", "alarm"]
    tension = 2 if any(t in lower for t in tension_terms) else 1 if category in {"consequence", "counterintuitive", "correction"} else 0
    brevity = 2 if 4 <= len(words) <= 11 else 1 if 3 <= len(words) <= 14 else 0
    non_generic = 0 if any(p in lower for p in FORBIDDEN_HOOK_PHRASES) else 2
    non_salesy = 0 if app["app"].lower() in lower or "app" in words else 2
    visual_compatibility = 2 if len(text) <= 62 else 1 if len(text) <= 82 else 0
    return {
        "private_specificity": private_specificity,
        "recognition": recognition,
        "tension": tension,
        "brevity": brevity,
        "non_generic": non_generic,
        "non_salesy": non_salesy,
        "visual_compatibility": visual_compatibility,
    }


def generate_hook_candidates(app: dict, rng: random.Random, minimum: int = 20) -> list[HookCandidate]:
    candidates: list[HookCandidate] = []
    if app["slug"] == "cherry":
        seeds = list(CHERRY_HOOK_SEEDS)
        rng.shuffle(seeds)
        for seed in seeds:
            breakdown = score_hook(app, seed["hook"], seed["category"])
            candidates.append(HookCandidate(
                text=seed["hook"],
                category=seed["category"],
                score=sum(breakdown.values()),
                score_breakdown=breakdown,
                body=seed["body"],
                symbol=seed["symbol"],
                caption=seed["caption"],
            ))
    else:
        scenes = app.get("pain_scenes") or ["the thing you keep avoiding"]
        for category, template in GENERIC_HOOK_TEMPLATES:
            for scene in scenes:
                text = template.format(pain_scene=scene.lower())
                breakdown = score_hook(app, text, category)
                candidates.append(HookCandidate(
                    text=text,
                    category=category,
                    score=sum(breakdown.values()),
                    score_breakdown=breakdown,
                    body=[rng.choice(GENERIC_HIDDEN_LOOPS), rng.choice(GENERIC_REFRAMES), rng.choice(GENERIC_MICRO_ACTIONS), app_insert(app)],
                    symbol=rng.choice(SYMBOLS)[1],
                    caption=f"{app['app']}: {app['positioning']} {app.get('primary_cta', 'Learn more')}: {app.get('primary_url', '')}",
                ))
    # Ensure at least `minimum` rows in the hook audit by deterministic mutations.
    base = list(candidates)
    suffixes = ["", " — smaller", " — before it gets heavier", " — start there"]
    idx = 0
    while len(candidates) < minimum and base:
        b = base[idx % len(base)]
        text = (b.text + suffixes[(idx // len(base)) % len(suffixes)]).replace("  ", " ").strip(" —")
        breakdown = score_hook(app, text, b.category)
        candidates.append(HookCandidate(text, b.category, sum(breakdown.values()), breakdown, b.body, b.symbol, b.caption))
        idx += 1
    uniq: dict[str, HookCandidate] = {}
    for h in sorted(candidates, key=lambda x: (x.score, x.score_breakdown["tension"], -len(x.text)), reverse=True):
        uniq.setdefault(h.text, h)
    return list(uniq.values())


def choose_slide_count(hook: HookCandidate) -> int:
    body_len = len(hook.body)
    # Leave room for a final-save/CTA slide when the emotional loop is short.
    if hook.category in {"private_moment", "correction"}:
        return min(6, max(5, body_len + 2))
    if hook.category == "consequence":
        return min(7, max(6, body_len + 2))
    return min(6, max(5, body_len + 2))


def final_cta_for_hook(hook: HookCandidate) -> str:
    if hook.category == "correction":
        return "save this for the next freeze"
    if hook.category == "consequence":
        return "save this before the next loop"
    if hook.category == "counterintuitive":
        return "start with the smallest real rep"
    if hook.category == "question":
        return "make the next version smaller"
    return "save this for your next tiny rep"


def has_late_cta(slides: list[str]) -> bool:
    tail = " ".join(slides[-2:]).lower()
    return any(x in tail for x in ["save", "try", "start", "practice", "cherry", "comment", "share"])


def themed_slide_prompts(app: dict, slides: list[str], hook: HookCandidate) -> list[str]:
    lane = app.get("visual_lane", {})
    palette = ", ".join(lane.get("palette", [])) or "deep saturated palette"
    avoid = ", ".join(lane.get("avoid", [])) or "readable text, devices"
    scene_pool = lane.get("scene_pool", []) or ["cozy cafe corner", "city crosswalk at dusk", "apartment bedroom with warm lamp glow", "tree-lined path after rain"]
    related_anchor = rng_anchor_from_hook(hook)
    prompts = []
    for idx, slide in enumerate(slides):
        scene = scene_pool[idx % len(scene_pool)]
        phase = scene_phase(idx, len(slides))
        prompts.append(
            f"{lane.get('style', 'pixel-art editorial scene background')}, {scene}, {phase}, "
            f"same campaign world as '{related_anchor}', emotionally aligned to slide text '{slide}', "
            f"lively, saturated deep colors, deep contrast, warm cinematic light, no people close-up, no faces emphasized, "
            f"vertical 4:5 TikTok composition, lots of clean negative space for centered text, palette: {palette}, "
            f"avoid: {avoid}."
        )
    return prompts


def sanitize_visual_anchor(text: str) -> str:
    lower = text.lower()
    replacements = {
        "speech bubble": "empty chair by a cafe window",
        "speech bubbles": "empty chairs by cafe windows",
        "phone": "warm window light",
        "glowing phone moon": "glowing streetlamp moon",
        "receipt printer": "faded paper receipt on a counter",
        "envelope": "sealed note on a table",
        "calendar square": "doorway marked by late light",
        "notebook": "paper page",
    }
    out = text
    for old, new in replacements.items():
        out = out.replace(old, new).replace(old.title(), new)
    return out
def rng_anchor_from_hook(hook: HookCandidate) -> str:
    symbol = sanitize_visual_anchor(hook.symbol.replace("a ", "").replace("an ", ""))
    return symbol[:120]


def scene_phase(idx: int, total: int) -> str:
    if idx == 0:
        return "opening scene, strongest contrast, immediate mood"
    if idx == total - 1:
        return "closing scene, slightly warmer hopeful turn"
    if idx <= 1:
        return "early tension scene"
    if idx >= total - 2:
        return "late release scene"
    return "mid-sequence reflective scene"

def title_from_hook(app: dict, hook: str) -> str:
    words = [w.strip("\u201c\u201d'\"") for w in clean_words(hook) if w not in {"you", "your", "the", "and", "to", "it", "is", "was", "a", "an"}]
    title = " ".join(words[:5]).title() or "Slideshow"
    return f"{app['app']} — {title}"


def build_from_hook(app: dict, hook: HookCandidate) -> Slideshow:
    slide_count = choose_slide_count(hook)
    slides = [hook.text] + hook.body[: slide_count - 1]
    if not has_late_cta(slides) and len(slides) < 7:
        slides.append(final_cta_for_hook(hook))
    elif not has_late_cta(slides):
        slides[-1] = final_cta_for_hook(hook)
    lane = app.get("visual_lane", {})
    palette = ", ".join(lane.get("palette", [])) or "deep saturated palette"
    avoid = ", ".join(lane.get("avoid", [])) or "readable text, devices"
    master_anchor = sanitize_visual_anchor(hook.symbol)
    image_prompt = (
        f"{lane.get('style', 'pixel-art editorial scene background')}, {master_anchor}, "
        f"emotionally evocative through a real-world setting rendered as clean pixel art, lively but moody, saturated deep colors, "
        f"palette: {palette}, warm cinematic light, vertical 4:5 TikTok composition, lots of clean negative space for centered text, avoid: {avoid}."
    )
    slide_image_prompts = themed_slide_prompts(app, slides, hook)
    caption = f"{hook.caption} {app.get('primary_url', '')}".strip()
    hashtags = app.get("hashtags", [])[:5]
    score_breakdown = score_candidate(app, hook, slides, caption, image_prompt, slides[-1])
    score = min(100, int((hook.score / 14) * 40) + sum(score_breakdown.values()))
    return Slideshow(
        app=app["slug"],
        title=title_from_hook(app, hook.text),
        hook=hook.text,
        hook_category=hook.category,
        hook_score=hook.score,
        slides=slides,
        caption=caption,
        image_prompt=image_prompt,
        slide_image_prompts=slide_image_prompts,
        hashtags=hashtags,
        score=score,
        score_breakdown=score_breakdown,
        mutation_notes=critic_notes(score_breakdown, hook),
    )


def build_generic_candidate(app: dict, rng: random.Random, i: int) -> Slideshow:
    hook = rng.choice(behavior_bank(app))
    loop = rng.choice(GENERIC_HIDDEN_LOOPS)
    reframe = rng.choice(GENERIC_REFRAMES)
    action = rng.choice(GENERIC_MICRO_ACTIONS)
    symbol_name, symbol_desc = rng.choice(SYMBOLS)
    desired = rng.choice(app.get("desired_outcomes") or ["make progress"])
    trigger = rng.choice(GENERIC_COMMENT_TRIGGERS)
    slides = [hook, loop, f"That is why '{desired}' needs a tiny repeatable system, not just another good intention.", reframe, action, app_insert(app)]
    cta = f"{app.get('primary_cta', 'Learn more')}: {app.get('primary_url', 'TODO')}"
    caption = f"{hook} Start with one tiny rep, then make the next one easier to repeat. {app['app']}: {app['positioning']} {cta}"
    lane = app.get("visual_lane", {})
    palette = ", ".join(lane.get("palette", [])) or "deep saturated palette"
    avoid = ", ".join(lane.get("avoid", [])) or "readable text, devices"
    image_prompt = f"{lane.get('style', 'pixel-art editorial scene background')}, {symbol_desc}, palette: {palette}, emotionally evocative through a real-world setting rendered as clean pixel art, lively but moody, saturated deep colors, warm cinematic light, vertical 4:5 TikTok composition, avoid: {avoid}."
    hb = score_hook(app, hook, "private_moment")
    h = HookCandidate(hook, "private_moment", sum(hb.values()), hb, slides[1:], symbol_desc, caption)
    slide_image_prompts = themed_slide_prompts(app, slides, h)
    score_breakdown = score_candidate(app, h, slides, caption, image_prompt, trigger)
    score = min(100, int((h.score / 14) * 40) + sum(score_breakdown.values()))
    return Slideshow(app=app["slug"], title=f"{app['app']} — {symbol_name.title()} Rep #{i:03d}", hook=hook, hook_category=h.category, hook_score=h.score, slides=slides, caption=caption, image_prompt=image_prompt, slide_image_prompts=slide_image_prompts, hashtags=app.get("hashtags", [])[:5], score=score, score_breakdown=score_breakdown, mutation_notes=critic_notes(score_breakdown, h))


def build_candidates(app: dict, rng: random.Random, iterations: int) -> tuple[list[HookCandidate], list[Slideshow]]:
    hook_candidates = generate_hook_candidates(app, rng, minimum=max(20, min(iterations, 30)))
    if app["slug"] == "cherry":
        eligible_hooks = [h for h in hook_candidates if h.score >= 10]
        slideshows = [build_from_hook(app, h) for h in eligible_hooks]
        return hook_candidates, slideshows
    slideshows = [build_generic_candidate(app, rng, i + 1) for i in range(iterations)]
    return hook_candidates, slideshows


def score_candidate(app: dict, hook: HookCandidate, slides: list[str], caption: str, image_prompt: str, trigger: str) -> dict[str, int]:
    retention = 18 if 4 <= len(slides) <= 6 and all(len(s) <= 88 for s in slides) else 12 if 4 <= len(slides) <= 7 else 6
    emotional_markers = ["relief", "heavy", "avoid", "silence", "safe", "froze", "rude", "cliff", "weird", "counted", "quiet", "perceived"]
    emotional = 8 + min(10, sum(1 for w in emotional_markers if any(w in s.lower() for s in slides)))
    reframe = 14 if any(x in " ".join(slides).lower() for x in ["smaller", "tiny", "rep", "confidence", "not a character", "not rude", "not ignore"]) else 8
    first_to_second = f"{slides[0]} -> {slides[1]}".lower() if len(slides) > 1 else ""
    bridge_terms = ["because", "then", "so", "but", "after", "before", "until", "without", "choice", "proof", "loop", "hard"]
    swipe_bridge = 10 if any(t in first_to_second for t in bridge_terms) and slides[0].lower() != slides[1].lower() else 5
    app_late = 10 if app["app"].lower() not in slides[0].lower() and (any(app["app"].lower() in s.lower() for s in slides[-2:]) or app["app"].lower() in caption.lower()) else 7
    late_cta = 8 if has_late_cta(slides) else 3
    forbidden = [f.lower() for f in app.get("forbidden_claims", [])] + ["cure", "guaranteed", "clinically proven"]
    safety = 0 if any(f and f in caption.lower() for f in forbidden) else 10
    engagement = 8 if hook.category in {"private_moment", "correction", "consequence"} else 6
    visual = 5 if "pixel" in image_prompt.lower() and "symbolic" in image_prompt.lower() and "negative space" in image_prompt.lower() else 3
    return {"retention_chain": retention, "emotional_resonance": min(18, emotional), "novel_reframe": reframe, "swipe_bridge": swipe_bridge, "app_fit_late": app_late, "late_cta": late_cta, "safety": safety, "engagement_trigger": engagement, "visual_evocativeness": visual}


def critic_notes(score_breakdown: dict[str, int], hook: HookCandidate) -> list[str]:
    notes = [f"Hook-first pipeline: category={hook.category}, hook_score={hook.score}/14, breakdown={hook.score_breakdown}."]
    if hook.score < 10:
        notes.append("Reject unless manually approved: hook score is below scheduling threshold.")
    if score_breakdown["retention_chain"] < 18:
        notes.append("Tighten slide count/line length; first swipe path is not crisp enough.")
    if score_breakdown["swipe_bridge"] < 10:
        notes.append("Strengthen the slide-1-to-slide-2 bridge; the hook should make swipe 1 feel unresolved.")
    if score_breakdown["app_fit_late"] < 10:
        notes.append("Keep Cherry/product mention late; do not lead with app language.")
    if score_breakdown["late_cta"] < 8:
        notes.append("Add final/penultimate save, start, or practice CTA; carousel sources recommend an ending action.")
    if score_breakdown["visual_evocativeness"] < 5:
        notes.append("Make visual symbol more evocative and leave more negative space for centered text.")
    if len(notes) == 1:
        notes.append("Candidate passes hook-first slideshow rubric; test with real swipe-through analytics.")
    return notes


def select_winners(candidates: Iterable[Slideshow], n: int = 12) -> list[Slideshow]:
    uniq = {}
    for c in sorted(candidates, key=lambda x: (x.score, x.hook_score, -len(x.slides)), reverse=True):
        if c.hook not in uniq:
            uniq[c.hook] = c
    return list(uniq.values())[:n]


def markdown_campaign(app: dict, winners: list[Slideshow]) -> str:
    lines = [f"# {app['app']} Slideshow Campaign — Generated Batch", "", f"CTA: {app.get('primary_cta')}", f"URL: {app.get('primary_url')}", ""]
    for idx, w in enumerate(winners, 1):
        lines += [f"## Post {idx}: {w.title}", "", f"Score: **{w.score}/100**", f"Hook: **{w.hook}**", f"Hook category: `{w.hook_category}`", f"Hook score: **{w.hook_score}/14**", f"Slide count: **{len(w.slides)}**", "", "### Slides", ""]
        lines += [f"{sidx}. {slide}" for sidx, slide in enumerate(w.slides, 1)]
        lines += ["", "### Caption", "", w.caption, "", "### Master Image Prompt", "", w.image_prompt, "", "### Slide Image Prompts", ""]
        lines += [f"{pidx}. {prompt}" for pidx, prompt in enumerate(w.slide_image_prompts, 1)]
        lines += ["", "### Hashtags", "", " ".join(w.hashtags), "", "### Critic Notes", ""]
        lines += [f"- {note}" for note in w.mutation_notes]
        lines.append("")
    return "\n".join(lines)


def postiz_payloads(winners: list[Slideshow]) -> list[dict]:
    payloads = []
    for w in winners:
        body = "".join(f"<p>{html.escape(slide)}</p>" for slide in w.slides)
        body += f"<p></p><p>{html.escape(w.caption)}</p><p></p><p>{html.escape(' '.join(w.hashtags))}</p>"
        payloads.append({
            "title": w.title[:90],
            "content_html": body,
            "attachment_needed": True,
            "slide_count": len(w.slides),
            "hook": w.hook,
            "hook_category": w.hook_category,
            "hook_score": w.hook_score,
            "image_prompt": w.image_prompt,
            "slide_image_prompts": w.slide_image_prompts,
            "score": w.score,
            "settings": {"privacy_level": "SELF_ONLY", "duet": False, "stitch": False, "comment": True, "autoAddMusic": "no", "brand_content_toggle": False, "brand_organic_toggle": False, "video_made_with_ai": True, "content_posting_method": "UPLOAD"},
        })
    return payloads


def write_hook_audit(app: dict, hooks: list[HookCandidate]) -> None:
    out = ROOT / "run_logs" / f"{app['slug']}_hook_audit.md"
    lines = ["# Hook Audit", "", f"App: {app['app']}", f"Generated hooks: {len(hooks)}", "", "| Score | Category | Hook | Breakdown |", "|---:|---|---|---|"]
    for h in sorted(hooks, key=lambda x: x.score, reverse=True):
        lines.append(f"| {h.score}/14 | {h.category} | {h.text} | `{json.dumps(h.score_breakdown, sort_keys=True)}` |")
    out.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", default="cherry")
    parser.add_argument("--iterations", type=int, default=150)
    parser.add_argument("--seed", type=int, default=20260707)
    args = parser.parse_args()
    app = load_app(args.app)
    rng = random.Random(args.seed)
    hook_candidates, candidates = build_candidates(app, rng, args.iterations)
    winners = select_winners(candidates, 12)

    out_dir = ROOT / "campaigns" / app["slug"]
    out_dir.mkdir(parents=True, exist_ok=True)
    (ROOT / "postiz").mkdir(parents=True, exist_ok=True)
    (ROOT / "run_logs").mkdir(parents=True, exist_ok=True)
    write_hook_audit(app, hook_candidates)
    (out_dir / "latest_campaign.md").write_text(markdown_campaign(app, winners))
    (out_dir / "latest_campaign.json").write_text(json.dumps([asdict(w) for w in winners], indent=2))
    (ROOT / "postiz" / f"{app['slug']}_postiz_drafts.json").write_text(json.dumps(postiz_payloads(winners), indent=2))

    log = ["# Iteration Log", "", f"App: {app['app']}", f"Iterations requested: {args.iterations}", f"Hook candidates generated: {len(hook_candidates)}", f"Slideshow candidates generated: {len(candidates)}", f"Winners selected: {len(winners)}", "", "## Top Scores", ""]
    for w in winners:
        log.append(f"- {w.score}/100 — {w.hook} ({w.hook_category}, hook {w.hook_score}/14, {len(w.slides)} slides)")
    (ROOT / "run_logs" / f"{app['slug']}_iteration_log.md").write_text("\n".join(log) + "\n")
    print(json.dumps({"app": app["slug"], "iterations": args.iterations, "hook_candidates": len(hook_candidates), "slideshow_candidates": len(candidates), "winners": len(winners), "top_score": winners[0].score, "top_hook": winners[0].hook, "top_hook_score": winners[0].hook_score, "top_slide_count": len(winners[0].slides)}, indent=2))


if __name__ == "__main__":
    main()
