"""Brochure ("boekje") images for the website: product catalogue, PPWR declaration and technical datasheet.

All three use the real catalogue booklet photo (input/catalogus-mockup.png) and the real cover artwork
(page 1 of input/catalogus/en.pdf, vector):
  * catalogus  = the catalogue cover as it is
  * ppwr       = the same cover art recoloured green, with PPWR text
  * datasheet  = the same cover art recoloured light blue, with datasheet text
The flat cover is put into the booklet photo with the same perspective, page edges, shadow, colour tone and
lighting, so the three images look like one series.

Output: input/mockups/q-pall-boekje-{catalogus,ppwr,technische-datasheet}.png (+ the flat covers).
The website build turns these into /assets/img/booklets/*.webp.
Needs: pikepdf, opencv-python, numpy, playwright (chromium), poppler (pdftoppm).
Run:   python3 tools/booklets.py
"""
import asyncio, os, subprocess, tempfile
from decimal import Decimal
import cv2, numpy as np, pikepdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, 'input/catalogus/en.pdf')
MOCK = os.path.join(ROOT, 'input/catalogus-mockup.png')
FONTS = os.path.join(ROOT, 'static/fonts')
OUT = os.path.join(ROOT, 'input/mockups')
TMP = tempfile.mkdtemp(prefix='qp-booklets-')

# cover texts (English, like the catalogue, so one image works in all six languages)
BOOKLETS = {
    'ppwr': {'cmyk': (0.44, 0.08, 0.78, 0.04),                       # = #8EBC54, green of the "Q op ondergrond" art
             'lines': [('Reusable pallets', 0), ('ready for the', 0), ('EU PPWR', 1)], 'caps': 'PPWR · EU 2025/40'},
    'technische-datasheet': {'cmyk': (0.64, 0.04, 0.08, 0.04),       # = #57B9D5, light blue of the "Q op ondergrond" art
             'lines': [('Every pallet,', 0), ('every detail,', 0), ('one datasheet', 1)], 'caps': 'TECHNICAL DATASHEET'},
}
DPI = 200
W, H = 1654, 2339            # A4 at 200 dpi
S = W / 595.276              # px per pt
LAST_ART_OP = 21979          # catalogue page 1: last operator of the artwork (after it: the logo)


# ------------------------------------------------------------------------------------------- cover art
def cover_art(out_png, cmyk=None):
    """Catalogue page 1 without its text (logo kept); optionally with the tube colour replaced."""
    pdf = pikepdf.open(PDF)
    while len(pdf.pages) > 1:
        del pdf.pages[-1]
    pg = pdf.pages[0]
    ops = pikepdf.parse_content_stream(pg)
    # drop only the text-showing operators so the colour state set inside BT/ET (used by the logo) survives
    kept = [x for x in ops if str(x[1]) not in ('Tj', 'TJ', "'", '"')]
    pg.Contents = pdf.make_stream(pikepdf.unparse_content_stream(kept))
    if cmyk:
        pg.Resources.Shading.Sh0.Function.Functions[0].C0 = pikepdf.Array([Decimal(str(v)) for v in cmyk])
    tmp_pdf = os.path.join(TMP, os.path.basename(out_png) + '.pdf')
    pdf.save(tmp_pdf)
    subprocess.run(['pdftoppm', '-r', str(DPI), '-png', '-singlefile', tmp_pdf, out_png[:-4]], check=True)


def cover_html(art_png, lines, caps, url='qpall.com'):
    """Same type layout as the catalogue cover (positions and sizes taken from the PDF)."""
    def line(txt, x, base, size, weight, ls):
        return (f'<div style="position:absolute;left:{x * S:.2f}px;top:{(base - .85 * size) * S:.2f}px;font:{weight} {size * S:.3f}px/1 Poppins;'
                f'letter-spacing:{ls}em;white-space:nowrap;color:#fff">{txt}</div>')
    h = ['<!doctype html><html><head><meta charset="utf-8"><style>',
         f"@font-face{{font-family:Poppins;font-weight:400;src:url(file://{FONTS}/poppins-400.woff2)}}",
         f"@font-face{{font-family:Poppins;font-weight:700;src:url(file://{FONTS}/poppins-700.woff2)}}",
         f'html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden}}body{{position:relative;'
         f'background:url(file://{art_png}) 0 0/{W}px {H}px no-repeat;-webkit-font-smoothing:antialiased;font-kerning:normal}}</style></head><body>']
    for (t, bold), base in zip(lines, [292.65, 346.17, 399.69]):
        h.append(line(t, 71.3386, base, 44.6, 700 if bold else 400, -0.006 if bold else -0.015))
    h.append(line(caps, 74.1732, 463.76, 10, 400, 0.425))
    h.append(line(url, 74.1732, 785.2, 18, 700, 0))
    h.append('</body></html>')
    return ''.join(h)


async def render_html(jobs):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': W, 'height': H})
        for html, out in jobs:
            f = os.path.join(TMP, 'cover.html')
            open(f, 'w', encoding='utf-8').write(html)
            await pg.goto('file://' + f)
            await pg.evaluate('document.fonts.ready')
            await pg.wait_for_timeout(300)
            await pg.screenshot(path=out)
        await b.close()


# ------------------------------------------------------------------------------------------- mockup
def cross2(a, b):
    return a[0] * b[1] - a[1] * b[0]


def inter(l1, l2):
    p, r = l1
    q, s = l2
    return p + cross2(q - p, s) / cross2(r, s) * r


class Mockup:
    """Fits the booklet photo once (cover outline, colour tone, lighting) and pastes flat covers into it."""

    def __init__(self, flat_original):
        M = cv2.imread(MOCK, cv2.IMREAD_UNCHANGED)
        self.M, self.alpha = M, M[:, :, 3]
        self.rgb = M[:, :, :3].astype(np.float32)
        F0 = cv2.imread(flat_original).astype(np.float32)
        mx, mn = M[:, :, :3].max(axis=2).astype(int), M[:, :, :3].min(axis=2).astype(int)
        # printed cover (not the white page edges); outline -> 4 fitted lines -> corners
        cover = ((self.alpha > 250) & ((mn < 140) | ((mx - mn) > 60))).astype(np.uint8) * 255
        cover = cv2.morphologyEx(cover, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        cnts, _ = cv2.findContours(cover, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        c = max(cnts, key=cv2.contourArea).reshape(-1, 2).astype(np.float32)
        hull = cv2.convexHull(c.astype(np.int32))
        ap = cv2.approxPolyDP(hull, 0.02 * cv2.arcLength(hull, True), True).reshape(-1, 2).astype(np.float32)
        ap = np.roll(ap, -int(np.argmin(ap[:, 1])), axis=0)
        if cross2(ap[1] - ap[0], ap[2] - ap[1]) < 0:
            ap = np.roll(ap[::-1], 1, axis=0)
        lines = []
        for k in range(4):
            a, b = ap[k], ap[(k + 1) % 4]
            d = b - a
            L = np.linalg.norm(d)
            n = np.array([-d[1], d[0]]) / L
            t = ((c - a) @ d) / (L * L)
            sel = c[(t > .08) & (t < .92) & (np.abs((c - a) @ n) < 6)]
            vx, vy, x0, y0 = cv2.fitLine(sel, cv2.DIST_HUBER, 0, .01, .01).ravel()
            lines.append((np.array([x0, y0]), np.array([vx, vy])))
        quad = np.array([inter(lines[(k - 1) % 4], lines[k]) for k in range(4)], np.float32)
        self.Hq = cv2.getPerspectiveTransform(np.float32([[0, 0], [W, 0], [W, H], [0, H]]), quad)
        # the catalogue cover in the photo is aligned on its artwork (SIFT) to learn tone and light
        sift = cv2.SIFT_create(8000)
        k1, d1 = sift.detectAndCompute(cv2.cvtColor(F0.astype(np.uint8), cv2.COLOR_BGR2GRAY), None)
        k2, d2 = sift.detectAndCompute(cv2.cvtColor(M[:, :, :3], cv2.COLOR_BGR2GRAY), None)
        good = [a for a, b in cv2.BFMatcher().knnMatch(d1, d2, k=2) if a.distance < .75 * b.distance]
        Hs, _ = cv2.findHomography(np.float32([k1[g.queryIdx].pt for g in good]), np.float32([k2[g.trainIdx].pt for g in good]), cv2.RANSAC, 3.0)
        W0 = cv2.warpPerspective(F0, Hs, (M.shape[1], M.shape[0]), flags=cv2.INTER_AREA)
        inside = cv2.erode(cover, np.ones((15, 15), np.uint8)) > 0
        sel = inside & (W0.min(axis=2) < 140) & (self.rgb.min(axis=2) < 140)
        fl, mk = W0[sel], self.rgb[sel]
        navy, orange = np.array([71, 33, 29], np.float32), np.array([27, 81, 241], np.float32)     # BGR
        hq = np.zeros(self.alpha.shape, np.uint8)
        cv2.fillPoly(hq, [np.round(quad).astype(np.int32)], 1)
        hq = cv2.erode(hq, np.ones((25, 25), np.uint8)) > 0
        mn_, mx_ = self.rgb.min(axis=2), self.rgb.max(axis=2)
        anch_in = [navy, orange, np.full(3, 255, np.float32)]
        anch_out = [np.median(mk[np.abs(fl - navy).sum(1) < 18], 0), np.median(mk[np.abs(fl - orange).sum(1) < 40], 0),
                    np.median(self.rgb[hq & (mn_ > 170) & ((mx_ - mn_) < 30)], axis=0)]
        self.curves = []
        for ch in range(3):
            pts = sorted((float(anch_in[i][ch]), float(anch_out[i][ch])) for i in range(3))
            self.curves.append((np.array([0.0] + [p[0] for p in pts]), np.array([max(0.0, pts[0][1] - pts[0][0] * .4)] + [p[1] for p in pts])))
        pred = self.tone(W0)
        # lighting: smooth quadratic surface fitted on plain navy areas only
        bright = ((W0.max(axis=2) > 120) | (mx_ > 120)).astype(np.uint8)
        px = sel & (np.abs(W0 - navy).sum(axis=2) < 12) & ~(cv2.dilate(bright, np.ones((31, 31), np.uint8)) > 0)
        yy, xx = np.nonzero(px)
        r = self.rgb[px].sum(axis=1) / np.maximum(pred[px].sum(axis=1), 1)
        sc = np.array([1, 1e3, 1e3, 1e6, 1e6, 1e6])
        X = np.stack([np.ones_like(xx), xx, yy, xx * xx, xx * yy, yy * yy], 1).astype(np.float64) / sc
        coef = np.linalg.lstsq(X, r, rcond=None)[0]
        for _ in range(3):
            res = r - X @ coef
            keep = np.abs(res) < 2.5 * res.std()
            coef = np.linalg.lstsq(X[keep], r[keep], rcond=None)[0]
        gy, gx = np.mgrid[0:M.shape[0], 0:M.shape[1]]
        G = np.stack([np.ones_like(gx), gx, gy, gx * gx, gx * gy, gy * gy], -1).astype(np.float64) / sc
        self.light = np.clip(G @ coef, .85, 1.15).astype(np.float32)
        # paste area: the quad, pushed out 10 px at the (slightly curved) top and left edge
        cen = quad.mean(axis=0)
        shifted = []
        for k, (p, d) in enumerate(lines):
            n = np.array([-d[1], d[0]])
            n = -n if np.dot(p - cen, n) < 0 else n
            shifted.append((p + n * (10 if k in (0, 3) else 0), d))
        q2 = np.array([inter(shifted[(k - 1) % 4], shifted[k]) for k in range(4)], np.float32)
        big = np.zeros((M.shape[0] * 4, M.shape[1] * 4), np.uint8)
        cv2.fillPoly(big, [np.round(q2 * 4).astype(np.int32)], 255, lineType=cv2.LINE_AA)
        self.mask = cv2.resize(big, (M.shape[1], M.shape[0]), interpolation=cv2.INTER_AREA).astype(np.float32)[..., None] / 255

    def tone(self, img):
        return np.dstack([np.interp(img[:, :, ch], *self.curves[ch]) for ch in range(3)]).astype(np.float32)

    def make(self, flat, out):
        F = cv2.imread(flat).astype(np.float32)
        Wn = cv2.warpPerspective(F, self.Hq, (self.M.shape[1], self.M.shape[0]), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE)
        new = np.clip(self.tone(Wn) * self.light[..., None], 0, 255)
        img = np.dstack([self.rgb * (1 - self.mask) + new * self.mask, self.alpha]).astype(np.uint8)
        x, y, w, h = cv2.boundingRect((self.alpha > 0).astype(np.uint8))
        cv2.imwrite(out, img[y:y + h, x:x + w])


def main():
    os.makedirs(OUT, exist_ok=True)
    flat_cat = os.path.join(OUT, 'cover-catalogus-plat.png')
    subprocess.run(['pdftoppm', '-f', '1', '-l', '1', '-r', str(DPI), '-png', '-singlefile', PDF, flat_cat[:-4]], check=True)
    jobs = []
    for key, b in BOOKLETS.items():
        art = os.path.join(TMP, f'art-{key}.png')
        cover_art(art, b['cmyk'])
        jobs.append((cover_html(art, b['lines'], b['caps']), os.path.join(OUT, f'cover-{key}-plat.png')))
    asyncio.run(render_html(jobs))
    mock = Mockup(flat_cat)
    for key in ['catalogus'] + list(BOOKLETS):
        mock.make(os.path.join(OUT, f'cover-{key}-plat.png'), os.path.join(OUT, f'q-pall-boekje-{key}.png'))
        print('booklet', key)


if __name__ == '__main__':
    main()
