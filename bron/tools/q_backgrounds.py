"""Q-Pall 'Q op ondergrond' artwork -> transparent WebP backgrounds for the website.

Input : input/brand/q/q-<kleur>.png  (5906 x 5906, the Q on the brand navy #2A2949)
Output: static/img/q/q-<kleur>-{600,900,1200,1800}.avif  (small, for all current browsers)
        static/img/q/q-<kleur>-{900,1200,1800}.webp      (fallback for older browsers)
        Transparent: the navy is removed with a colour-to-alpha step, so the Q can sit on any dark
        background. AVIF is ~8x smaller than the WebP at the same look (smooth gradients, no banding);
        a WebP with a lower alpha quality bands visibly, so the WebP fallback keeps alpha_quality 90.
Run once after changing the artwork:  python3 tools/q_backgrounds.py
"""
import glob, os
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = np.array([42, 41, 73], dtype=np.float32) / 255.0
OUT = os.path.join(ROOT, 'static', 'img', 'q')


def color_to_alpha(rgb):
    """GIMP-style colour-to-alpha against BG: composited back over BG it gives the original."""
    c = rgb.astype(np.float32) / 255.0
    b = BG[None, None, :]
    up = np.where(c > b, (c - b) / np.maximum(1 - b, 1e-6), 0)
    down = np.where(c < b, (b - c) / np.maximum(b, 1e-6), 0)
    a = np.clip(np.max(np.maximum(up, down), axis=2), 0, 1)
    a3 = np.maximum(a[..., None], 1e-6)
    col = np.clip((c - b) / a3 + b, 0, 1)
    col = np.where(a[..., None] > 0.002, col, 0)
    return np.dstack([col, a]) * 255


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in sorted(glob.glob(os.path.join(ROOT, 'input/brand/q/q-*.png'))):
        name = os.path.splitext(os.path.basename(f))[0]
        im = Image.open(f).convert('RGB')
        W = im.width
        # the Q sits roughly in 17-82% x 21-76% y; keep a margin so nothing touches the edge
        box = (int(W * .12), int(W * .155), int(W * .87), int(W * .815))
        im = im.crop(box).resize((2400, round(2400 * (box[3] - box[1]) / (box[2] - box[0]))), Image.LANCZOS)
        rgba = Image.fromarray(color_to_alpha(np.asarray(im)).round().astype(np.uint8), 'RGBA')
        for w in (600, 900, 1200, 1800):
            r = rgba.resize((w, round(rgba.height * w / rgba.width)), Image.LANCZOS)
            r.save(os.path.join(OUT, f'{name}-{w}.avif'), 'AVIF', quality=45, speed=4)
            if w >= 900:
                r.save(os.path.join(OUT, f'{name}-{w}.webp'), 'WEBP', quality=82, method=6, alpha_quality=90)
        print(name, rgba.size, {f: os.path.getsize(os.path.join(OUT, f'{name}-{f}')) // 1024
                                for f in ('600.avif', '1200.avif', '1800.avif', '900.webp', '1800.webp')}, 'KB')


if __name__ == '__main__':
    main()
