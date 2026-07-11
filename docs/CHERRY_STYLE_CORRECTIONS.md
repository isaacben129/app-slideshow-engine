# Cherry TikTok Style Corrections — 2026-07-08

## Source

Direct founder correction after seeing rendered draft.

## Hard visual rules

1. A slideshow must be multiple image slides with text burned into each slide.
2. Do **not** put a black overlay box/panel behind text.
3. Font size should be about half the previous renderer size.
4. Text should sit moderately high but **lower than the upper third** (renderer uses ~y=740 on a 1920 frame), centered, with a tiny black outline only — no black overlay panel.
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

## Renderer fixes (2026-07-10)

- `make_bg` was downsampling every background to 180×320 then nearest-upscaling back to 1080×1920, flattening all detail. Changed to 200×356 — keeps the pixelated aesthetic but crisper/saturated.
- Text moved from y=360 (pinned to top) to y=740 (below upper third); removed the top black gradient overlay. Text uses a tiny black outline only.
- Upload path: `uploadFromUrlTool` accepts a base64 `data:` URI, so slides upload with **no temp HTTP server and no permissions**. See `scripts/postiz_publish_datauri.py`.
- Direct Postiz REST upload is blocked by a Cloudflare WAF (error 1010) on every `/api/*` route except the allowlisted MCP path — use the MCP tools, not curl.
