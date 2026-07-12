#!/usr/bin/env python3
from pathlib import Path
from PIL import Image

sources = [
    Path('/opt/data/cache/images/openai_codex_gpt-image-2-medium_20260708_153820_3701a8a9.png'),
    Path('/opt/data/cache/images/openai_codex_gpt-image-2-medium_20260708_153909_a742655c.png'),
    Path('/opt/data/cache/images/openai_codex_gpt-image-2-medium_20260708_154001_8962c092.png'),
    Path('/opt/data/cache/images/openai_codex_gpt-image-2-medium_20260708_154100_cd5d496b.png'),
    Path('/opt/data/cache/images/openai_codex_gpt-image-2-medium_20260708_154143_2c2deb67.png'),
    Path('/opt/data/cache/images/openai_codex_gpt-image-2-medium_20260708_154235_2bee5ec9.png'),
]
out_dir = Path('/opt/data/studio/systems/app-slideshow-engine/backgrounds/cherry_fresh_doorway')
out_dir.mkdir(parents=True, exist_ok=True)
for idx, src in enumerate(sources, 1):
    img = Image.open(src).convert('RGB')
    out = out_dir / f'bg_{idx:02d}.jpg'
    img.save(out, quality=95)
print(out_dir)
