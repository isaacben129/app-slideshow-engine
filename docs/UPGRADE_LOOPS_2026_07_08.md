# Upgrade Loops — 2026-07-08

Goal: repeat the improvement pattern: audit weak point → research → implement → verify.

## Loop 1 — Renderer readability

### Audit

The corrected renderer removed the black box/drop shadow and centered the text, but after the reduction it was slightly conservative. Founder asked to increase text size by 25%.

### Research / basis

TikTok carousel design sources repeatedly emphasize clear, concise, large readable text and strong contrast while keeping text away from edges/UI. This supports increasing size as long as auto-fit and outline remain.

Sources:

- UseVisuals TikTok Carousel Best Practices — clear concise text overlays, large readable fonts, strong contrast, avoid edges/UI.
- UseVisuals TikTok Carousel Tips — 9:16 format, concise text, carousel pacing.

### Change

`render_slides.py` start font size changed from `44` to `55`, exactly +25%, while retaining auto-fit for longer lines and the tiny black outline.

## Loop 2 — Slide-1-to-slide-2 bridge

### Audit

The hook scorecard ranked hooks well, but the slideshow score did not explicitly evaluate whether slide 2 resolves/deepens the hook. That means a strong hook could be followed by a flat second slide.

### Research / basis

Carousel hook sources frame slide one as a curiosity gap where the swipe is the resolution. PostWaffle says the first slide has about 2 seconds and must create a reason to swipe. ImagineArt summarizes carousel hooks as headline + visual creating a psychological gap that only resolves when the viewer keeps swiping.

Sources:

- PostWaffle — `15 TikTok Carousel Hook Formulas That Get People Swiping`
- ImagineArt — `15 Best Carousel Hooks That Keep People Swiping`

### Change

Added `swipe_bridge` scoring to evaluate whether slide 1 and slide 2 have an unresolved logical bridge using terms like because/then/so/but/after/before/choice/proof/loop/hard.

## Loop 3 — Ending CTA / save behavior

### Audit

Some scripts ended emotionally but did not consistently include a final or penultimate action. Carousel research recommends ending with a CTA, summary, save/share/comment prompt, or thought-provoking question.

### Research / basis

UseVisuals carousel guides recommend final-slide CTAs like save/comment/share/link in bio and note every slide should add value. Search snippets also showed final/penultimate CTA placement as a carousel best practice.

Sources:

- UseVisuals TikTok Carousel Post Tips
- UseVisuals TikTok Carousel Best Practices

### Change

Added `final_cta_for_hook()` and `has_late_cta()`. The generator now appends or replaces the final slide with a context-specific CTA when needed, e.g. `save this for the next freeze` or `save this before the next loop`. Added `late_cta` scoring.

## Verification required after implementation

- Regenerate Cherry/Held campaigns.
- Run tests.
- Render top Cherry slideshow with 25% larger text.
- Visually inspect slide 1 and a longer slide.
- Push repo and create a new Postiz draft.
