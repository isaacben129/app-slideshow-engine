#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
from pathlib import Path

import yaml
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from postiz_retry import retry_publish

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CFG = Path('/opt/data/config.yaml')
DEFAULT_INTEGRATION_ID = 'cmrb2tjm80001ow6vkzhk1yg9'


def build_content_html(slides: list[str], caption: str, hashtags: list[str]) -> str:
    body = ''.join(f'<p>{s}</p>' for s in slides)
    body += f'<p></p><p>{caption}</p><p></p><p>{" ".join(hashtags)}</p>'
    return body


async def upload_and_schedule(url: str, integration_id: str, base_url: str, title: str, slides: list[str], caption: str, hashtags: list[str], settings: dict) -> dict:
    uploaded = []
    async with streamablehttp_client(url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for i in range(1, len(slides) + 1):
                up = await session.call_tool('uploadFromUrlTool', {'url': f'{base_url}/slide_{i:02d}.jpg'})
                upj = up.structuredContent or json.loads(up.content[0].text)
                uploaded.append(upj['path'])
            args = {
                'socialPost': [{
                    'integrationId': integration_id,
                    'isPremium': False,
                    'date': dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
                    'shortLink': False,
                    'type': 'draft',
                    'postsAndComments': [{'content': build_content_html(slides, caption, hashtags), 'attachments': uploaded}],
                    'settings': [{'key': k, 'value': v} for k, v in settings.items()],
                }]
            }
            res = await session.call_tool('integrationSchedulePostTool', args)
            return {'uploads': uploaded, 'schedule': res.structuredContent or json.loads(res.content[0].text)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--payload', required=True, help='Path to one selected draft payload JSON')
    ap.add_argument('--base-url', required=True, help='HTTP base URL hosting slide_01.jpg etc')
    ap.add_argument('--integration-id', default=DEFAULT_INTEGRATION_ID)
    ap.add_argument('--config', default=str(DEFAULT_CFG))
    ap.add_argument('--title-prefix', default='AUTO')
    args = ap.parse_args()

    payload = json.loads(Path(args.payload).read_text())
    cfg = yaml.safe_load(Path(args.config).read_text())
    url = cfg['mcp_servers']['postiz']['url']
    title = f"{args.title_prefix} — {payload['title']}"
    settings = dict(payload.get('settings', {}))
    settings['title'] = title[:90]
    result = retry_publish(
        lambda: upload_and_schedule(
            url=url,
            integration_id=args.integration_id,
            base_url=args.base_url.rstrip('/'),
            title=title,
            slides=payload['slides'],
            caption=payload['caption'],
            hashtags=payload.get('hashtags', []),
            settings=settings,
        ),
        attempts=6, base_delay=30.0)
    print(json.dumps({'title': title, **result}, indent=2))


if __name__ == '__main__':
    main()
