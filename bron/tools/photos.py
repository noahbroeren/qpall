"""Productfoto's normaliseren naar input/photos/<model-id>/.

Eenmalig/handmatig: leest de keuze uit /home/claude/work/photo_choice.json (Drive-foto's per SKU)
en de catalogusfoto's uit input/raw/. Schrijft per model:
  input/photos/<model-id>/1.webp   hoofdfoto (vrijstaand op wit, 3:2, 1800 px breed)
  input/photos/<model-id>/2.webp … extra aanzichten
en input/photos.json  {model-id: {"n": aantal, "src": ["drive"|"catalog", ...], "exact": bool}}

Nieuwe foto toevoegen zonder dit script: zet een WebP/PNG (wit of transparant) in
input/photos/<model-id>/<nr>.webp en pas input/photos.json aan.
"""
import json, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'input/raw')
OUT = os.path.join(ROOT, 'input/photos')
CHOICE = os.environ.get('QP_PHOTO_CHOICE', '/home/claude/work/photo_choice.json')
W, H = 1800, 1200          # 3:2 canvas
FILL_W, FILL_H = .86, .80  # max object size within canvas


def load_rgb(path):
    im = Image.open(path)
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA')
        bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        im = bg
    return im.convert('RGB')


def normalise(path, allow_cover=True):
    im = load_rgb(path)
    a = np.asarray(im.convert('L'))
    mask = a < 244
    ys, xs = np.where(mask)
    if len(xs):
        pad = 4
        x0, x1 = max(0, xs.min() - pad), min(im.width, xs.max() + pad)
        y0, y1 = max(0, ys.min() - pad), min(im.height, ys.max() + pad)
        im = im.crop((x0, y0, x1, y1))
    touches = sum([xs.min() <= 2, ys.min() <= 2, xs.max() >= a.shape[1] - 3, ys.max() >= a.shape[0] - 3]) if len(xs) else 0
    if allow_cover and touches >= 3:
        # detail/close-up: fill the canvas (cover)
        r = max(W / im.width, H / im.height)
        im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
        l, t = (im.width - W) // 2, (im.height - H) // 2
        return im.crop((l, t, l + W, t + H))
    r = min(W * FILL_W / im.width, H * FILL_H / im.height)
    im = im.resize((max(1, round(im.width * r)), max(1, round(im.height * r))), Image.LANCZOS)
    canvas = Image.new('RGB', (W, H), (255, 255, 255))
    canvas.paste(im, ((W - im.width) // 2, (H - im.height) // 2 + round(H * .02)))
    return canvas


def raw_path(xref):
    for ext in ('.webp', '.png', '.jpg'):
        p = os.path.join(RAW, f'x{xref}{ext}')
        if os.path.exists(p):
            return p
    return None


def main():
    prod = json.load(open(os.path.join(ROOT, 'data/products.json')))
    choice = json.load(open(CHOICE)) if os.path.exists(CHOICE) else {}
    os.makedirs(OUT, exist_ok=True)
    meta = {}
    for m in prod['models']:
        c = choice.get(m['id'], {})
        srcs = []
        if c.get('primary'):
            srcs.append(('drive', c['primary']))
        elif m.get('img'):
            srcs.append(('catalog', raw_path(m['img'])))
        for g in c.get('gallery', [])[:3]:
            srcs.append(('drive', g))
        srcs = [(k, p) for k, p in srcs if p and os.path.exists(p)]
        d = os.path.join(OUT, m['id'])
        os.makedirs(d, exist_ok=True)
        for i, (k, p) in enumerate(srcs, 1):
            normalise(p, allow_cover=i > 1).save(os.path.join(d, f'{i}.webp'), 'WEBP', quality=90, method=6)
        meta[m['id']] = {'n': len(srcs), 'src': [k for k, _ in srcs],
                         'exact': bool(c.get('primary')) or bool(m.get('img_exact'))}
        print(m['id'], meta[m['id']])
    json.dump(meta, open(os.path.join(ROOT, 'input/photos.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
