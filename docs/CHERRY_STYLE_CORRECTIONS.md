# Cherry TikTok Style Corrections — 2026-07-08

## Source

Direct founder correction after seeing rendered draft.

## Hard visual rules

1. A slideshow must be multiple image slides with text burned into each slide.
2. Do **not** put a black overlay box/panel behind text.
3. Font size should be about half the previous renderer size.
4. Text should sit much higher: around the baseline of the upper third of the image.
5. Keep pixelated, symbolic/non-literal backgrounds.
6. Backgrounds should feel more evocative, not literal app screenshots or generic anxiety art.

## Copy rules from correction

The prior account style/copy was better than the new generated copy. New system should move away from:

- generic therapy/coaching language,
- obvious “problem → app solves it” pacing,
- overly explained slides,
- long founder-y captions,
- immediate product insertion.

Move toward:

- shorter slides,
- more restraint,
- more negative space,
- one thought per slide,
- private/recognizable moments,
- quieter emotional escalation,
- app mention only at the end or caption,
- less “AI motivational” voice.

## Postiz lookup attempt

Checked Postiz via:

- browser UI at `https://social.havencompanion.app`, but this runtime is unauthenticated and lands on `/auth`.
- Postiz MCP raw client: available tools are scheduling/upload/schema/generate/ask, but there is no list-history/list-posts tool.
- Postiz API `/api/posts` returns 401 without browser session auth.

Conclusion: the system can schedule and upload through MCP, but cannot currently inspect historic Postiz posts from this runtime without an authenticated UI session or a Postiz history/list API/tool.
