#!/usr/bin/env python3
"""Illustration for the news article 'Gerecycled PE-HD 2: wat is het precies?' (all languages).

Writes root/assets/img/news/hdpe-2.svg (copied to /assets/img/news/ by build.py) and a raster copy
input/brand/photo-hdpe.webp for the share image (tools/og.py). Text is converted
to Poppins outlines, so the SVG looks the same everywhere (an <img> SVG cannot load web fonts).
Layout: a clean recycling triangle (three chasing arrows, each wrapped around one corner) with the
resin code 2 in the middle and 'HDPE' below it.
"""
import math, os, re
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = {w: TTFont(os.path.join(ROOT, f'static/fonts/poppins-{w}.woff2')) for w in (500, 600)}
W, H = 1600, 1000
NAVY, NAVY2, GREEN, ORANGE = '#1D1C4C', '#2E2D63', '#94C24A', '#F37321'


def text_path(txt, size, weight=600, anchor='middle', x=0, y=0, track=0):
    """SVG path data for txt at baseline (x, y)."""
    f = FONTS[weight]
    gs, cmap, hmtx = f.getGlyphSet(), f.getBestCmap(), f['hmtx']
    s = size / f['head'].unitsPerEm
    names = [cmap[ord(c)] for c in txt]
    adv = [hmtx[n][0] * s + track for n in names]
    total = sum(adv) - track
    x0 = x - (total / 2 if anchor == 'middle' else total if anchor == 'end' else 0)
    out, cx = [], x0
    for n, a in zip(names, adv):
        pen = SVGPathPen(gs)
        gs[n].draw(TransformPen(pen, (s, 0, 0, -s, cx, y)))
        out.append(pen.getCommands())
        cx += a
    return ' '.join(out)


def glyph_bounds(ch, size, weight=600):
    """Ink box of one glyph in SVG coordinates relative to its origin on the baseline: (x0, y0, x1, y1), y down."""
    f = FONTS[weight]
    gs = f.getGlyphSet()
    bp = BoundsPen(gs)
    gs[f.getBestCmap()[ord(ch)]].draw(bp)
    k = size / f['head'].unitsPerEm
    x0, y0, x1, y1 = bp.bounds
    return x0 * k, -y1 * k, x1 * k, -y0 * k


def cap_height(size, weight=600):
    f = FONTS[weight]
    bp = BoundsPen(f.getGlyphSet())
    f.getGlyphSet()['H'].draw(bp)
    return bp.bounds[3] * size / f['head'].unitsPerEm


def rounded_triangle(cx, cy, R, rc, n_arc=40):
    """Points (x, y) along an equilateral triangle (point up) with rounded corners, clockwise from the top
    corner, plus the cumulative length; corner i sits at s_corner[i]."""
    C = [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a))) for a in (-90, 30, 150)]
    pts, corner_mid = [], []
    for i in range(3):
        p0, p1, p2 = C[i - 1], C[i], C[(i + 1) % 3]
        # tangent points at distance d from the corner (interior angle 60 deg)
        d = rc / math.tan(math.radians(30))
        def toward(a, b, dist):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            return (a[0] + (b[0] - a[0]) * dist / L, a[1] + (b[1] - a[1]) * dist / L)
        t_in, t_out = toward(p1, p0, d), toward(p1, p2, d)
        # arc centre: along the bisector, at rc / sin(30) from the corner
        bis = ((p0[0] + p2[0]) / 2 - p1[0], (p0[1] + p2[1]) / 2 - p1[1])
        bl = math.hypot(*bis)
        oc = (p1[0] + bis[0] / bl * rc / math.sin(math.radians(30)), p1[1] + bis[1] / bl * rc / math.sin(math.radians(30)))
        a0 = math.atan2(t_in[1] - oc[1], t_in[0] - oc[0])
        a1 = math.atan2(t_out[1] - oc[1], t_out[0] - oc[0])
        while a1 < a0:
            a1 += 2 * math.pi
        if a1 - a0 > math.pi:            # take the short way round
            a1 -= 2 * math.pi
        pts.append(t_in)
        for k in range(1, n_arc):
            a = a0 + (a1 - a0) * k / n_arc
            pts.append((oc[0] + rc * math.cos(a), oc[1] + rc * math.sin(a)))
        corner_mid.append(len(pts) - n_arc // 2)
        pts.append(t_out)
    # cumulative length on the closed loop
    cum = [0.0]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return pts, cum, [cum[i] for i in corner_mid]


def point_at(pts, cum, s):
    total = cum[-1]
    s %= total
    for i in range(len(pts)):
        if cum[i] <= s <= cum[i + 1]:
            a, b = pts[i], pts[(i + 1) % len(pts)]
            t = (s - cum[i]) / max(cum[i + 1] - cum[i], 1e-9)
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), (b[0] - a[0], b[1] - a[1])
    return pts[0], (1, 0)


def recycle_symbol(cx, cy, R, w, gap, head_len, head_w):
    """Three chasing arrows, each wrapped symmetrically around one corner of a rounded triangle."""
    pts, cum, sc = rounded_triangle(cx, cy, R, R * .2)
    third = cum[-1] / 3
    shafts, heads = [], []
    for i in range(3):
        s0 = sc[i] - third / 2 + gap / 2
        s1 = sc[i] + third / 2 - gap / 2 - head_len
        n = 120
        se = s1 + 3                      # run the shaft a little under the head: no hairline seam
        poly = [point_at(pts, cum, s0 + (se - s0) * k / n)[0] for k in range(n + 1)]
        shafts.append('M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in poly))
        (ex, ey), (tx, ty) = point_at(pts, cum, s1)
        tl = math.hypot(tx, ty)
        ux, uy = tx / tl, ty / tl
        nx, ny = -uy, ux
        tip = (ex + ux * head_len, ey + uy * head_len)
        heads.append(f'M{tip[0]:.1f},{tip[1]:.1f} L{ex + nx * head_w / 2:.1f},{ey + ny * head_w / 2:.1f} '
                     f'L{ex - nx * head_w / 2:.1f},{ey - ny * head_w / 2:.1f} Z')
    return shafts, heads


def main():
    cx, cy, R, sw = 800, 410, 250, 40
    shafts, heads = recycle_symbol(cx, cy, R, sw, gap=60, head_len=56, head_w=98)
    # the 2: centred on its own ink (not the advance width), at the optical centre of the triangle =
    # midway between the centroid and the centre of the symbol's bounding box
    xs, ys = [], []
    for d in shafts + heads:
        for x, y in re.findall(r'(-?[\d.]+),(-?[\d.]+)', d):
            xs.append(float(x)); ys.append(float(y))
    top, bot = min(ys) - sw / 2, max(ys) + sw / 2
    oy = (cy + (top + bot) / 2) / 2
    size = 190
    ink = glyph_bounds('2', size)
    two = text_path('2', size, 600, 'start', cx - (ink[0] + ink[2]) / 2, oy - (ink[1] + ink[3]) / 2)
    hdpe = text_path("HDPE", 96, 600, "middle", cx, 812, track=14)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{NAVY2}"/><stop offset="1" stop-color="{NAVY}"/></linearGradient>
<radialGradient id="glow" cx="50%" cy="40%" r="46%"><stop offset="0" stop-color="#5A59B8" stop-opacity=".5"/><stop offset="1" stop-color="#5A59B8" stop-opacity="0"/></radialGradient>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<rect width="{W}" height="{H}" fill="url(#glow)"/>
<g fill="none" stroke="#fff" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="butt">{''.join(f'<path d="{p}"/>' for p in shafts)}</g>
<g fill="#fff">{''.join(f'<path d="{h}"/>' for h in heads)}</g>
<path d="{two}" fill="#fff"/>
<path d="{hdpe}" fill="#fff"/>
<rect x="{cx - 60}" y="850" width="120" height="8" rx="4" fill="{ORANGE}"/>
</svg>
'''
    dest = os.path.join(ROOT, 'root/assets/img/news/hdpe-2.svg')
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, 'w').write(svg)
    print(dest, len(svg) // 1024, 'KB')
    # raster copy for the share (OG) image: input/brand/photo-hdpe.webp (tools/og.py, page news-hdpe)
    from playwright.sync_api import sync_playwright
    from PIL import Image
    import io
    tmp = os.path.join(os.path.dirname(dest), '_render.html')
    open(tmp, 'w').write(f'<body style="margin:0"><img src="hdpe-2.svg" style="width:{W}px;height:{H}px;display:block"></body>')
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': W, 'height': H})
        pg.goto('file://' + tmp)
        pg.wait_for_timeout(300)
        png = pg.screenshot()
        b.close()
    os.remove(tmp)
    Image.open(io.BytesIO(png)).convert('RGB').save(os.path.join(ROOT, 'input/brand/photo-hdpe.webp'), 'WEBP', quality=90, method=6)


if __name__ == '__main__':
    main()
