#!/usr/bin/env python3
"""Publish a rendered Cherry slideshow to TikTok via Postiz — NO temp HTTP hosting.

Reads slide_XX.jpg files from --out-dir, base64-encodes each into a `data:` URI,
uploads via the MCP `uploadFromUrlTool` (which accepts data URIs), then schedules
the post with `integrationSchedulePostTool`. The Cloudflare WAF blocks direct REST
uploads, but the MCP path is allowlisted, so this stays fully server-to-server.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import datetime as dt
import glob
import json
from pathlib import Path

import yaml
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from postiz_retry import retry_publish

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CFG = Path('/opt/data/config.yaml')
DEFAULT_INTEGRATION_ID = 'cmrb2tjm80001ow6vkzhk1yg9'
PPT = ROOT / 'campaigns' / 'cherry' / 'latest_campaign.json'


def build_content_html(caption: str, hashtags: list[str]) -> str:
    body = f'<p>{caption}</p>'
    if hashtags:
        body += f'<p>{" ".join(hashtags)}</p>'
    return body


async def publish(url: str, integration_id: str, out_dir: Path, payload: dict,
                  when: str, title_prefix: str, privacy: str, post_type: str) -> dict:
    slides = payload['slides']
    slide_files = sorted(glob.glob(str(out_dir / 'slide_*.jpg')))
    if len(slide_files) < len(slides):
        raise SystemExit(f"only {len(slide_files)} slide images but {len(slides)} slides")

    uploaded: list[str] = []
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for f in slide_files:
                b64 = base64.b64encode(Path(f).read_bytes()).decode()
                data_uri = f'data:image/jpeg;base64,{b64}'
                up = await session.call_tool('uploadFromUrlTool', {'url': data_uri})
                upj = up.structuredContent or json.loads(up.content[0].text)
                uploaded.append(upj['path'])
            settings = [
                {'key': 'title', 'value': f"{title_prefix} — {payload['title']}"[:90]},
                {'key': 'privacy_level', 'value': privacy},
                {'key': 'duet', 'value': False},
                {'key': 'stitch', 'value': False},
                {'key': 'comment', 'value': True},
                {'key': 'autoAddMusic', 'value': 'no'},
                {'key': 'brand_content_toggle', 'value': False},
                {'key': 'brand_organic_toggle', 'value': False},
                {'key': 'video_made_with_ai', 'value': True},
                {'key': 'content_posting_method', 'value': 'UPLOAD'},
            ]
            args = {
                'socialPost': [{
                    'integrationId': integration_id,
                    'isPremium': False,
                    'date': when,
                    'shortLink': False,
                    'type': post_type,
                    'postsAndComments': [{
                        'content': build_content_html(payload.get('caption', ''), payload.get('hashtags', [])),
                        'attachments': uploaded,
                    }],
                    'settings': settings,
                }]
            }
            res = await session.call_tool('integrationSchedulePostTool', args)
            raw = {
                'structured': res.structuredContent,
                'content': [getattr(c, 'text', None) for c in res.content],
            }
            Path('/tmp/postiz_last_schedule.json').write_text(json.dumps(raw, default=str, indent=2))
            try:
                sched = res.structuredContent or json.loads(res.content[0].text)
            except Exception:
                sched = {'raw_content': [getattr(c, 'text', str(c)) for c in res.content]}
            return {'uploads': uploaded, 'schedule': sched}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--post-index', type=int, default=0, help='index into latest_campaign.json for caption/hashtags/title')
    ap.add_argument('--payload', default=None, help='explicit payload JSON (overrides --post-index)')
    ap.add_argument('--app', default='cherry', help='campaign app folder (cherry|held); selects campaigns/<app>/latest_campaign.json')
    ap.add_argument('--campaign', default=None, help='explicit campaign JSON path (overrides --app)')
    ap.add_argument('--date', required=True, help='UTC ISO datetime, e.g. 2026-07-13T16:00:00Z')
    ap.add_argument('--integration-id', default=DEFAULT_INTEGRATION_ID)
    ap.add_argument('--config', default=str(DEFAULT_CFG))
    ap.add_argument('--title-prefix', default='CHERRY')
    ap.add_argument('--privacy', default='PUBLIC')
    ap.add_argument('--type', default='schedule', choices=['schedule', 'draft'])
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text())
    url = cfg['mcp_servers']['postiz']['url']
    if args.payload:
        payload = json.loads(Path(args.payload).read_text())
    else:
        camp_path = Path(args.campaign) if args.campaign else (ROOT / 'campaigns' / args.app / 'latest_campaign.json')
        data = json.loads(camp_path.read_text())
        payload = data[args.post_index]
    out_dir = Path(args.out_dir)
    result = retry_publish(
        lambda: publish(url, args.integration_id, out_dir, payload,
                        args.date, args.title_prefix, args.privacy, args.type),
        attempts=6, base_delay=30.0)
    print(json.dumps({'title': payload['title'], 'n_uploads': len(result['uploads']),
                      'schedule': result['schedule']}, indent=2))


if __name__ == '__main__':
    main()
