#!/usr/bin/env python3
"""Stellingillustratie voor het kennisbankartikel over belasting (templates/_load_ill.html, kind 'racking').

Een conventionele palletstelling schuin van voren-links gezien (zodat de diepte zichtbaar is): twee
staanderframes, een voorste en een achterste ligger, twee beladen pallets waarvan de drie onderlatten
dwars over beide liggers liggen. De pallets buigen niet. Het script rekent de 3D-blokken om naar een
vlakke SVG (orthografische projectie, schilderen van achter naar voor) en schrijft die tussen de
markeringen RACK-START / RACK-END in templates/_load_ill.html. Teksten komen uit i18n (load_ill).
Gebruik: python3 tools/rack_ill.py
"""
import math, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, 'templates', '_load_ill.html')

YAW, PITCH = math.radians(-30), math.radians(18)
cy, sy, cp, sp = math.cos(YAW), math.sin(YAW), math.cos(PITCH), math.sin(PITCH)


def proj(x, y, z):
    xr = x * cy + z * sy                 # depth (z) goes up-left, the bay (x) up-right
    zr = -x * sy + z * cy
    yr = y * cp + zr * sp
    return xr, -yr


# ---------------------------------------------------------------- scene (mm)
W, D = 2880, 1100            # bay width (outer posts), frame depth
PW, PD = 90, 70              # post section
BY, BH, BD = 560, 110, 55    # beam: underside, height, depth
TOP = BY + BH                # beam top = runner underside
H = 1750                     # post height
P_W, P_D = 800, 1200         # pallet width (along the beam) and depth (across the beams)
RUN_H, BLK_H, DECK_H = 30, 88, 32
LOAD_H = 560
PAL_X = [1040, 1915]         # pallet x positions; the left place stays empty so both beams show
PZ0 = (D - P_D) / 2          # -50: 50 mm overhang front and back

C = {
    'post': ('#1D1C4C', '#2B2A63', '#3A3980'),          # front, left side, top
    'brace': ('#4B4A86', '#4B4A86', '#4B4A86'),
    'beam': ('#F37321', '#DA671D', '#F8A066'),
    'pal': ('#36355F', '#2A2950', '#4A4980'),
}
# bag colours per face: gap/shadow, bag, print band
BAG = {'front': ('#C2C7DA', '#E4E6F0', '#D3D7E6'), 'side': ('#B3B9CF', '#CDD1E1', '#C2C7DA'),
       'top': ('#D3D7E6', '#F1F2F7', '#E2E5EF')}
LAYERS = 5
items = []   # (svg string) in paint order


def poly(pts, fill, extra=''):
    d = 'M' + 'L'.join(f'{x:.1f} {y:.1f}' for x, y in pts) + 'Z'
    return f'<path d="{d}" fill="{fill}"{extra}/>'


def box(x0, x1, y0, y1, z0, z1, col, faces=('left', 'front', 'top')):
    f, s, t = col
    out = []
    P = lambda x, y, z: proj(x, y, z)
    if 'left' in faces:
        out.append(poly([P(x0, y0, z0), P(x0, y0, z1), P(x0, y1, z1), P(x0, y1, z0)], s))
    if 'top' in faces:
        out.append(poly([P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)], t))
    if 'front' in faces:
        out.append(poly([P(x0, y0, z0), P(x1, y0, z0), P(x1, y1, z0), P(x0, y1, z0)], f))
    return ''.join(out)


def line(a, b, col, w):
    (x0, y0), (x1, y1) = proj(*a), proj(*b)
    return f'<path d="M{x0:.1f} {y0:.1f}L{x1:.1f} {y1:.1f}" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>'


# floor
items.append(poly([proj(-150, 0, -250), proj(W + 150, 0, -250), proj(W + 150, 0, D + 200), proj(-150, 0, D + 200)], '#E7E8F1'))


def bracing(x):
    """Steel bracing of an upright frame (same on both sides): horizontals at the bottom and top, diagonals between."""
    out = []
    zf, zb = PD / 2, D - PD / 2
    ys = [150, 530, 910, 1290, H - 110]
    out.append(line((x, ys[0], zf), (x, ys[0], zb), '#4B4A86', 5))
    out.append(line((x, ys[-1], zf), (x, ys[-1], zb), '#4B4A86', 5))
    for k in range(len(ys) - 1):
        a, b = (zf, zb) if k % 2 == 0 else (zb, zf)
        out.append(line((x, ys[k], a), (x, ys[k + 1], b), '#4B4A86', 5))
    return ''.join(out)


# far parts: back posts, back beam, right frame with its bracing
items.append(box(0, PW, 0, H, D - PD, D, C['post']))
items.append(box(W - PW, W, 0, H, D - PD, D, C['post']))
items.append(box(PW, W - PW, BY, TOP, D - BD, D, C['beam']))
items.append(bracing(W - PW / 2))
items.append(box(W - PW, W, 0, H, 0, PD, C['post']))
# front beam (below the pallets' front overhang, so painted before them)
items.append(box(PW, W - PW, BY, TOP, 0, BD, C['beam']))
items.append(box(PW, W - PW, BY, BY + 18, 0, 1, ('#DA671D',) * 3, faces=('front',)))

contact = None
tops = []
loads = []
for px in reversed(PAL_X):              # right pallet first (further from the viewer)
    z0, z1 = PZ0, PZ0 + P_D
    runs = [(px, px + 100), (px + 350, px + 450), (px + 700, px + 800)]
    # runners (across both beams), blocks, deck - right runner first
    for rx0, rx1 in reversed(runs):
        items.append(box(rx0, rx1, TOP, TOP + RUN_H, z0, z1, C['pal']))
        for bz0, bz1 in ((z1 - 100, z1), ((z0 + z1) / 2 - 50, (z0 + z1) / 2 + 50), (z0, z0 + 100)):
            items.append(box(rx0, rx1, TOP + RUN_H, TOP + RUN_H + BLK_H, bz0, bz1, C['pal']))
    yd = TOP + RUN_H + BLK_H
    items.append(box(px, px + P_W, yd, yd + DECK_H, z0, z1, C['pal']))
    # load: 25 kg bags (square, in the colours of the other illustrations), stacked in interlocking layers (drawn after the fit)
    y0, y1 = yd + DECK_H, yd + DECK_H + LOAD_H
    lx0, lx1, lz0, lz1 = px + 8, px + P_W - 8, z0 + 8, z1 - 8
    items.append(box(lx0, lx1, y0, y1, lz0, lz1, (BAG['front'][0], BAG['side'][0], BAG['top'][0])))
    items.append(f'@@BAGS{len(loads)}@@')
    loads.append((lx0, lx1, y0, y1, lz0, lz1))
    tops.append(((lx0 + lx1) / 2, y1, (lz0 + lz1) / 2))
    if px == PAL_X[0]:
        contact = (px, TOP + RUN_H / 2, D / 2)   # side of the left runner, halfway between the beams

# near parts: left frame, the same as the right one
items.append(bracing(PW / 2))
items.append(box(0, PW, 0, H, 0, PD, C['post']))
# base plates
for x in (0, W - PW):
    items.append(box(x - 15, x + PW + 15, 0, 8, -15, PD + 15, ('#14133A', '#14133A', '#2B2A63')))

# ---------------------------------------------------------------- fit into the viewBox
pts = []
for s in items:
    for m in re.finditer(r'(-?\d+\.\d) (-?\d+\.\d)', s):
        pts.append((float(m.group(1)), float(m.group(2))))
minx, maxx = min(p[0] for p in pts), max(p[0] for p in pts)
miny, maxy = min(p[1] for p in pts), max(p[1] for p in pts)
VW = 768
pad_x, pad_top, pad_bot = 40, 40, 64           # room for arrows above, labels below
sc = (VW - 2 * pad_x) / (maxx - minx)
VH = round((maxy - miny) * sc + pad_top + pad_bot)


def T(x, y):
    return (x - minx) * sc + pad_x, (y - miny) * sc + pad_top


def tr(s):
    return re.sub(r'(-?\d+\.\d) (-?\d+\.\d)', lambda m: '%.1f %.1f' % T(float(m.group(1)), float(m.group(2))), s)


def S(x, y, z):
    return T(*proj(x, y, z))


def face(o, eu, ev, w, h, rows, col):
    """Bags on one face: o = 3D top-left corner, eu/ev = 3D unit steps right/down, rows = list of cell widths per row."""
    ox, oy = S(*o)
    ux, uy = S(o[0] + eu[0], o[1] + eu[1], o[2] + eu[2])
    vx, vy = S(o[0] + ev[0], o[1] + ev[1], o[2] + ev[2])
    m = f'matrix({ux - ox:.5f} {uy - oy:.5f} {vx - ox:.5f} {vy - oy:.5f} {ox:.1f} {oy:.1f})'
    bg, bag, band = col
    out = [f'<g transform="{m}">']
    rh = h / len(rows)
    for r, widths in enumerate(rows):
        u = 0
        for cw in widths:
            g = 6
            bw, bh = cw * w - 2 * g, rh - 2 * g
            x0, y0 = u + g, r * rh + g
            out.append(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{bw:.0f}" height="{bh:.0f}" fill="{bag}"/>')
            if bw > 120:                                   # print band across the middle of a whole bag
                out.append(f'<rect x="{x0 + bw * 0.43:.0f}" y="{y0:.0f}" width="{bw * 0.14:.0f}" height="{bh:.0f}" fill="{band}"/>')
            u += cw * w
    out.append('</g>')
    return ''.join(out)


A, B = [0.5, 0.5], [0.25, 0.5, 0.25]          # joints shift every layer: an interlocking stack
bags = []
for lx0, lx1, y0, y1, lz0, lz1 in loads:
    w, h, d = lx1 - lx0, y1 - y0, lz1 - lz0
    front = face((lx0, y1, lz0), (1, 0, 0), (0, -1, 0), w, h, [A if r % 2 == 0 else B for r in range(LAYERS)], BAG['front'])
    side = face((lx0, y1, lz1), (0, 0, -1), (0, -1, 0), d, h, [B if r % 2 == 0 else A for r in range(LAYERS)], BAG['side'])
    top = face((lx0, y1, lz1), (1, 0, 0), (0, 0, -1), w, d, [A, A], BAG['top'])
    bags.append(front + side + top)

body = ''.join(tr(s) for s in items)
for k, b in enumerate(bags):
    body = body.replace(f'@@BAGS{k}@@', b)

# arrows above the loads
arrows = ''
for (x, y, z) in tops:
    ax, ay = T(*proj(x, y, z))
    arrows += f'{{{{ arrow({ax:.1f}, {ay - 66:.1f}, {ay - 6:.1f}) }}}}'
# labels
bx, by = T(*proj(W * 0.6, BY, 0))
cx, cyy = T(*proj(*contact))
lab_y = VH - 26
labels = (f'<path d="M{cx:.1f} {cyy + 3:.1f}V{lab_y - 26:.1f}" stroke="#9A99B5" stroke-width="2" stroke-dasharray="3 5" stroke-linecap="round"/>'
          f'<circle cx="{cx:.1f}" cy="{cyy:.1f}" r="5" fill="#fff" stroke="#1D1C4C" stroke-width="2.5"/>'
          f'<text class="mid" x="{min(max(cx, 230), VW - 230):.1f}" y="{lab_y:.1f}" font-size="21" font-weight="600" fill="#1D1C4C" text-anchor="middle">{{{{ L.runners }}}}</text>'
          f'<text class="lbl" x="{bx:.1f}" y="{by + 30:.1f}" font-size="18" fill="#706F8F" text-anchor="middle">{{{{ L.beam }}}}</text>')

svg = (f'<svg viewBox="0 0 {VW} {VH}" role="img" aria-label="{{{{ L.alt_racking }}}}" xmlns="http://www.w3.org/2000/svg">\n'
       f'  <rect width="{VW}" height="{VH}" rx="14" fill="#F3F3F7"/>\n  {body}\n  {arrows}\n  {labels}\n</svg>')

src = open(TPL, encoding='utf-8').read()
new = re.sub(r'(\{#- RACK-START -#\}\n).*?(\{#- RACK-END -#\})', lambda m: m.group(1) + svg + '\n' + m.group(2), src, flags=re.S)
if new == src and 'RACK-START' not in src:
    raise SystemExit('markers RACK-START / RACK-END missing in templates/_load_ill.html')
open(TPL, 'w', encoding='utf-8').write(new)
print('racking illustration written', VW, 'x', VH)
