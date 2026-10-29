#!/usr/bin/env python3
"""Free-standing pallet photos for the homepage hero and the OG images: input/hero/<light|medium|heavy>.png

Source: the product photo of the hero model (build.HERO_MODELS / HERO_PHOTO). Steps:
1. rembg (model isnet-general-use) makes a mask of the pallet.
2. The edge pixels are 'decontaminated' (the white studio background is removed from the colour).
3. The photo shadow on the white floor is kept, but as a DARK, semi-transparent shadow
   (no white haze on the dark hero background).
4. Trimmed to the pallet + shadow.

Requires: pip install "rembg[cpu]" opencv-python-headless  (downloads the model on first use, ~180 MB).
Only needed when a hero model or photo changes; the PNGs are part of the source package.
"""
import os, sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
SHADOW = np.array([12, 10, 28], np.float32)     # shadow colour (very dark navy)
EXTRA = [('promo', 'qp1210mb3r-cd-ao', 1)]       # (output name, model, photo number)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def cutout(src, session):
    from rembg import remove
    im = Image.open(src).convert('RGB')
    M = np.asarray(remove(im, session=session, only_mask=True).convert('L')).astype(np.float32) / 255
    C = np.asarray(im).astype(np.float32)
    L = C @ np.array([.2126, .7152, .0722], np.float32)
    sat = C.max(2) - C.min(2)
    H, W = L.shape
    border = np.concatenate([L[:20].ravel(), L[-20:].ravel(), L[:, :20].ravel(), L[:, -20:].ravel()])
    bg = np.percentile(border, 60)                        # brightness of the studio background
    s = np.clip((bg - L) / bg, 0, 1)                      # how much darker than the background = shadow
    sa = np.clip(s * 1.35, 0, .9) * (1 - smoothstep(20, 40, sat))
    Ms = np.maximum(M, 1e-3)[..., None]
    F = np.clip((C - (1 - M[..., None]) * bg) / Ms, 0, 255)
    F = np.where(M[..., None] > 0.98, C, F)
    A = M + (1 - M) * sa
    col = (M[..., None] * F + ((1 - M) * sa)[..., None] * SHADOW) / np.maximum(A, 1e-4)[..., None]
    out = Image.fromarray(np.dstack([np.clip(col, 0, 255), np.clip(A * 255, 0, 255)]).astype(np.uint8), 'RGBA')
    a = np.asarray(out)[..., 3]
    ys, xs = np.where(a > 6)
    return out.crop((max(xs.min() - 10, 0), max(ys.min() - 10, 0), min(xs.max() + 10, W), min(ys.max() + 10, H)))


def main():
    from rembg import new_session
    import build
    session = new_session('isnet-general-use')
    for cls, mid in build.HERO_MODELS.items():
        n = build.HERO_PHOTO.get(cls, 0) + 1
        src = os.path.join(ROOT, 'input/photos', mid, f'{n}.webp')
        dest = os.path.join(ROOT, 'input/hero', cls + '.png')
        cutout(src, session).save(dest, optimize=True)
        print(cls, mid, n, '->', dest)
    # homepage antislip promo card: the same treatment, free-standing on the dark card
    for name, mid, n in EXTRA:
        src = os.path.join(ROOT, 'input/photos', mid, f'{n}.webp')
        dest = os.path.join(ROOT, 'input/hero', name + '.png')
        cutout(src, session).save(dest, optimize=True)
        print(name, mid, n, '->', dest)


if __name__ == '__main__':
    main()
