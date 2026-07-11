# Cherry × Kallaway Hook Framework (2026-07-10)

Applied after the founder rejected the first batch of hooks ("not scroll-stoppers, pacing is flat").
Source: Kallaway — *Short-Form Hooks Workshop* (hooks drive ~80% of results; curiosity-gap
algorithms + pattern interrupts + 6 hook archetypes + 4-component structure + chained open loops).

## The core principle
The first 1–3 seconds decide everything. A hook must create a **curiosity gap** — an information
vacuum the brain is compelled to close. For a *slideshow*, the retention engine is the
**cross-slide open loop**: every slide (except the last) ends on a gap that is ONLY resolved on
the next slide. The old engine had "one thought per slide" with no gap — so swipe-2 felt resolved
and people bounced.

## The 6 Kallaway archetypes (all scroll-stoppers)
1. **Contrarian** — attack common advice. "the 'just breathe' advice is a scam for people who already feel safe."
2. **Controversial / hot take** — take a stance that invites disagreement. "your anxiety isn't the problem. your reaction to it is."
3. **Relatable / identity reframe** — "you're not X, you're Y." "you're not boring, you're unscripted."
4. **Curiosity gap / incomplete** — withhold the payoff. "the reason the phone rang like an alarm isn't what you think."
5. **Story / open loop** — "i asked 300 anxious people one question. the answer broke the advice."
6. **Nobody-talks-about** — surface the unsaid. "nobody talks about the part of anxiety that isn't fear."

## Slide structure (5–6 slides, every beat pulls to the next)
- **Slide 1 = HOOK**: the scroll-stopper. Controversial / surprising / gap.
- **Slide 2**: open a loop ("here's the part nobody says out loud").
- **Slide 3**: tension / partial reveal.
- **Slide 4**: the twist / reveal.
- **Slide 5**: the tiny-rep pivot (gap to next: "the fix is smaller than a breath").
- **Slide 6**: close the loop + CTA (save / comment / follow).

## How it's generated
`src/slideshow_engine/kallaway_hooks.py` holds Cherry angle libraries (false advice, truths,
private moments, relief reframes, micro-reps) and the 6 archetype builders. `generate(n)` rotates
archetypes + angles so repeats land far apart. Output is appended to
`campaigns/cherry/latest_campaign.json`. The 3/day cron calls it with `--append --count 3`.

## Bridge phrases that force the swipe (examples)
"here's the part nobody says out loud" · "it's not what you think" · "and that changes everything" ·
"the missing answer is the whole problem" · "so the real fix is smaller than a breath".

## Cadence
3 posts/day (corrected from 3/week on 2026-07-10). Daily cron `cherry-weekly-slideshows`
(renamed conceptually to daily) generates + schedules 3 at 11:00 / 15:00 / 19:00 UTC.
