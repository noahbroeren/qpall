"""Per-article photos for collars and lids.

Source: Noah's folder "Q-Pall fotos per SKU 2026-10-14" (originally from qpall.com), copied to
input/raw/acc-sku/. Every photo is cut to the product (white or transparent background), then placed
centred on a white 3:2 canvas with the same margin, so all cards look alike. Output goes to
input/acc-photos/<sku in lower case>.webp; build_assets.py turns those into
/assets/img/acc/photo-<sku>.webp and build.py uses them on the accessory cards.

Run: python3 tools/acc_sku_photos.py
"""
import os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'input/raw/acc-sku')
OUT = os.path.join(ROOT, 'input/acc-photos')

# sku -> source file (first photo of the article on qpall.com)
PHOTOS = {
    'QPKVOUWR6080-4': 'QPKVOUWR6080-4_kunststof-palletopzetrand-600x800x200_01.webp',
    'QPKVOUWR1208-4': 'QPKVOUWR1208-4_kunststof-palletopzetrand-1200x800x200_01.webp',
    'QPKVOUWR1208-6': 'QPKVOUWR1208-6_kunststof-palletopzetrand-1200x800x200_01.webp',
    'QPHKVOUWR1208-6': 'QPHKVOUWR1208-6_kunststof-palletopzetrand-1200x800x200_01.webp',
    'QPKKVOUWR1208-6': 'QPKKVOUWR1208-6_kunststof-palletopzetrand-1200x800x200_01.webp',
    'QPKVOUWR1210-4': 'QPKVOUWR1210-4_kunststof-palletopzetrand-1200x1000x200_01.webp',
    'QPKVOUWR1210-6': 'QPKVOUWR1210-6_kunststof-palletopzetrand-1200x1000x200_01.webp',
    'QPKVOUWR1212-4': 'QPKVOUWR1212-4_kunststof-palletopzetrand-1200x1200x200_01.webp',
    'QPKDECK-6080': 'QPKDECK-6080_kunststof-palletdeksel-820x620x4_01.webp',
    'QPKDECK-1208': 'QPKDECK-1208_kunststof-palletdeksel-1220x820x4_01.webp',
    'QPKDECK1210': 'QPKDECK1210_kunststof-palletdeksel-1220x1020x4_01.webp',
    'QPKKDECK-1208': 'QPKKDECK-1208_kunststof-palletdeksel-1200x800x2-9_01.webp',
}
W, H = 960, 640          # 3:2, same as the card image box
FILL_W, FILL_H = .86, .80  # product fills at most this part of the canvas


def on_white(im):
    im = im.convert('RGBA')
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    return bg.convert('RGB')


def bbox(im):
    a = np.asarray(im.convert('RGB')).astype(int)
    ink = (255 - a).max(axis=2) > 14      # anything that is not (almost) white
    ys, xs = np.where(ink)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def main():
    os.makedirs(OUT, exist_ok=True)
    for sku, fn in PHOTOS.items():
        im = on_white(Image.open(os.path.join(SRC, fn)))
        im = im.crop(bbox(im))
        s = min(W * FILL_W / im.width, H * FILL_H / im.height)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        c = Image.new('RGB', (W, H), 'white')
        c.paste(im, ((W - im.width) // 2, (H - im.height) // 2))
        c.save(os.path.join(OUT, sku.lower() + '.webp'), 'WEBP', quality=92, method=6)
        print(sku, im.size)


if __name__ == '__main__':
    main()
