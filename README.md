# App Slideshow Engine

A durable, rollbackable **general-purpose app slideshow engine** for producing TikTok/short-form slideshow campaigns that are attention-grabbing, emotionally evocative, engagement-oriented, and sales-linked.

Cherry is the first app config and proving ground, but the system is designed to support any app in the studio: Cherry, Held, future niche apps, and service/product launches.

Core constraints:

- Use app-specific product briefs, not hardcoded assumptions.
- Keep pixelated / symbolic / non-literal media backgrounds when that is the selected visual lane.
- Optimize for recognition, retention, comments, saves, profile clicks, and conversions.
- Respect each app's forbidden claims and compliance boundaries.

## Quickstart

```bash
python3 src/slideshow_engine/generate_campaign.py --app cherry --iterations 150
python3 -m pytest tests -q
```

Outputs land in:

- `campaigns/cherry/latest_campaign.md`
- `campaigns/cherry/latest_campaign.json`
- `postiz/cherry_postiz_drafts.json`
- `run_logs/iteration_log.md`

## System loop

```text
App Brief
→ Audience Pain Map
→ Hook Bank
→ Script Variants
→ Scoring Rubric
→ Critic Pass
→ Winner Selection
→ Visual Prompt Generation
→ Postiz Draft Payload
→ Analytics Review Template
→ Next Mutation
```
