#!/usr/bin/env python3
"""Footer badges: input/brand/badges/* -> static/img/brand/badge-*.webp (transparent, 160 px high = 2x the footer size).

  recycled-100.png          "Bijna 100% gerecycled kunststof" (sticker)
  ecovadis-bronze-2026.svg  EcoVadis Bronze, oktober 2026 (top 35%) - the only badge in the footer since update 12
  ecovadis-bronze-2025.svg  EcoVadis Bronze, juni 2025 (expired, not used)
  ecovadis-silver-2023.svg  EcoVadis Silver 2023 (expired, not used)
Only rerun when a badge changes:  python3 tools/badges.py   (needs Playwright/Chromium for the SVGs).
"""
import asyncio, io, os
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'input', 'brand', 'badges')
OUT = os.path.join(ROOT, 'static', 'img', 'brand')
H = 160


async def svg_png(path, size=900):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': size, 'height': size})
        import tempfile
        with tempfile.NamedTemporaryFile('w', suffix='.html', dir=os.path.dirname(path), delete=False) as f:
            f.write(f'<html><body style="margin:0;background:transparent"><img src="{os.path.basename(path)}" '
                    f'style="width:{size}px;height:{size}px;display:block"></body></html>')
        await pg.goto('file://' + f.name)
        os.unlink(f.name)
        await pg.wait_for_timeout(400)
        png = await pg.screenshot(omit_background=True)
        await b.close()
    return Image.open(io.BytesIO(png)).convert('RGBA')


def save(im, name):
    im = im.crop(im.getchannel('A').getbbox())
    w = round(im.width * H / im.height)
    im = im.resize((w, H), Image.LANCZOS)
    im.save(os.path.join(OUT, f'badge-{name}.webp'), 'WEBP', quality=90, method=6)
    print(name, im.size)


save(Image.open(os.path.join(SRC, 'recycled-100.png')).convert('RGBA'), 'recycled')
for n in ('ecovadis-bronze-2026',):
    save(asyncio.run(svg_png(os.path.join(SRC, n + '.svg'))), n)
