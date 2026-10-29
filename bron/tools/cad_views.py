#!/usr/bin/env python3
"""Technische tekeningen voor de datasheets: bovenaanzicht + beide zijaanzichten uit de SolidWorks-pdf's.

Alle Q-Pall/AVK-tekeningen hebben dezelfde opbouw: bovenaanzicht linksboven, het korte zijaanzicht
rechts ervan, het lange zijaanzicht eronder. Het script zoekt die drie aanzichten, knipt ze uit,
zet ze dicht bij elkaar (zelfde uitlijning als op de tekening) en schrijft input/cad/<artikel-id>.png
(navy lijnen, transparant). tools/datasheets.py zet die op pagina 2 van de datasheet.

Invoer:  input/cad/map.json        [artikel-id, artikelnummer, Drive-bestand-id, bestandsnaam] per artikel
         input/cad/overrides.json  handmatige vakken (paginafracties) voor afwijkende tekeningen
         de pdf's zelf als <Drive-id>.pdf in een map (standaard input/cad/pdf/, niet in het pakket)
Gebruik: python3 tools/cad_views.py <map-met-pdfs> [drive-id ...]
Controle: input/cad/dbg/<artikel-id>.png toont de gevonden vakken (rood = boven, blauw = kort, groen = lang).
Lege blokjes of rare tekens in de maten? Dan mist de pdf zijn lettertype: eerst tools/cad_fontfix.py op die pdf.
Toleranties (+1/-3, ±5), keurmaat-ovalen en radiusmaten (R30) worden weggelaten via tools/cad_clean.py;
zet "keep_tolerances": true in overrides.json om dat voor een tekening uit te zetten.
Vereist: pdftoppm (poppler), numpy, scipy, Pillow, pdfplumber.
"""
import json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cad_clean import erase_mask   # toleranties, keurmaat-ovalen en radiusmaten weghalen



def render(pdf, width):
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(['pdftoppm', '-gray', '-scale-to-x', str(width), '-scale-to-y', '-1',
                        '-png', '-singlefile', pdf, os.path.join(d, 'p')],
                       check=True, stderr=subprocess.DEVNULL)
        return np.array(Image.open(os.path.join(d, 'p.png')).convert('L'))


def boxes_of(mask):
    lab, n = ndi.label(mask)
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        if sl is None:
            continue
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        out.append(dict(i=i, x0=x0, y0=y0, x1=x1, y1=y1, w=x1 - x0, h=y1 - y0))
    return lab, out


def frame_inner(ink):
    """Bounding box of the drawing area inside the sheet frame (long straight frame lines)."""
    H, W = ink.shape
    rows = ink.mean(axis=1)
    cols = ink.mean(axis=0)
    # frame lines: rows/cols with ink over > 60% of the width/height
    ry = [y for y in range(H) if rows[y] > 0.6]
    rx = [x for x in range(W) if cols[x] > 0.6]
    top = max([y for y in ry if y < H * 0.15], default=0)
    bot = min([y for y in ry if y > H * 0.85], default=H)
    lef = max([x for x in rx if x < W * 0.15], default=0)
    rig = min([x for x in rx if x > W * 0.85], default=W)
    return top, bot, lef, rig


def detect(pdf, L, W, width=2400, debug=False):
    g = render(pdf, width)
    H, Wd = g.shape
    ink = g < 180
    t, b, l, r = frame_inner(ink)
    pad = int(Wd * 0.004)
    area = np.zeros_like(ink)
    area[t + pad:b - pad, l + pad:r - pad] = True
    ink2 = ink & area
    # drop long frame-like lines inside (zone ticks) - none expected after crop
    k = max(3, int(Wd * 0.006))
    dil = ndi.binary_dilation(ink2, structure=np.ones((k, k), bool))
    lab, bx = boxes_of(dil)
    pagearea = (b - t) * (r - l)
    for x in bx:
        x['a'] = x['w'] * x['h'] / pagearea
    big = [x for x in bx if x['a'] > 0.004]
    want = L / W
    # top view: aspect ~ L/W (dimension lines add some slack), big, top-left most
    cands = []
    for x in big:
        asp = x['w'] / x['h']
        if 0.72 * want < asp < 1.45 * want and x['a'] > 0.03:
            cands.append(x)
    if not cands:
        return None, (g, bx, t, b, l, r)
    top = min(cands, key=lambda x: (x['x0'] + x['y0']))
    # short side view: right of top view, overlapping vertically
    def voverlap(a, c):
        return max(0, min(a['y1'], c['y1']) - max(a['y0'], c['y0'])) / min(a['h'], c['h'])
    def hoverlap(a, c):
        return max(0, min(a['x1'], c['x1']) - max(a['x0'], c['x0'])) / min(a['w'], c['w'])
    right = [x for x in big if x is not top and x['x0'] >= top['x1'] - 5 and voverlap(top, x) > 0.5
             and x['w'] < top['w'] * 0.6]
    below = [x for x in big if x is not top and x['y0'] >= top['y1'] - 5 and hoverlap(top, x) > 0.5
             and x['h'] < top['h'] * 0.6]
    side_s = min(right, key=lambda x: x['x0']) if right else None
    side_l = min(below, key=lambda x: x['y0']) if below else None
    res = dict(size=[Wd, H], top=top, short=side_s, long=side_l,
               labels=[top['i']] + ([side_s['i']] if side_s else []) + ([side_l['i']] if side_l else []))
    return res, (g, lab, bx, t, b, l, r)



Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.join(ROOT, 'input', 'cad')
PROD = os.path.join(ROOT, 'data', 'products.json')
PDF_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'pdf')
NAVY = (29, 26, 77)
OVR = os.path.join(HERE, 'overrides.json')

# dimensions per article number (L, W in mm)
models = {v['sku']: {'L': int(float(v['L'])), 'W': int(float(v['W']))} for m in json.load(open(PROD))['models'] for v in m['variants']}
mp = json.load(open(os.path.join(HERE, 'map.json')))
ovr = json.load(open(OVR)) if os.path.exists(OVR) else {}
DBG = os.path.join(HERE, 'dbg')
os.makedirs(DBG, exist_ok=True)
models_by_base = models
TOPW = 1500            # px width of the top view in the output


def render_scaled(pdf, width):
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(['pdftoppm', '-gray', '-scale-to-x', str(int(width)), '-scale-to-y', '-1',
                        '-png', '-singlefile', pdf, os.path.join(d, 'p')], check=True,
                       stderr=subprocess.DEVNULL)
        return np.array(Image.open(os.path.join(d, 'p.png')).convert('L'))


def clean_view(lab, box, tol=4):
    """labels inside box that stick out of it (foreign leader lines etc.)"""
    x0, y0, x1, y1 = box
    sub = lab[y0:y1, x0:x1]
    bad = []
    objs = ndi.find_objects(lab)
    for l in np.unique(sub):
        if l == 0:
            continue
        sl = objs[l - 1]
        if sl[0].start < y0 - tol or sl[0].stop > y1 + tol or sl[1].start < x0 - tol or sl[1].stop > x1 + tol:
            bad.append(l)
    return bad


only = sys.argv[2:]
done = {}
seen = set()
for art, base, pid, title in mp:
    if only and pid not in only and art not in only:
        continue
    if base not in models:      # artikel staat niet (meer) op de site; de bestaande png blijft staan
        print('skip', base); continue
    m = dict(models[base], id=art)
    L, W = max(m['L'], m['W']), min(m['L'], m['W'])
    pdf = os.path.join(PDF_DIR, pid + '.pdf')
    o = ovr.get(pid, {})
    res, dbg = detect(pdf, L, W)
    g, lab = dbg[0], dbg[1]
    Hd, Wd = g.shape
    info = dict(title=title, base=base)
    views = {}
    if res is not None:
        for k in ('top', 'short', 'long'):
            v = res[k]
            if v: views[k] = [v['x0'], v['y0'], v['x1'], v['y1']]
    for k, fr in o.get('boxes', {}).items():          # manual boxes in page fractions
        if fr is None:
            views.pop(k, None)
        else:
            views[k] = [int(fr[0] * Wd), int(fr[1] * Hd), int(fr[2] * Wd), int(fr[3] * Hd)]
    if 'top' not in views:
        print('FAIL', base, title); done[pid] = None; continue
    info['found'] = sorted(views)
    t = views['top']
    s = TOPW / (t[2] - t[0])
    hi = render_scaled(pdf, Wd * s)
    hh, ww = hi.shape
    for a, b_, c, e in o.get('pdrop', []):              # page fractions blanked out
        hi[int(b_ * hh):int(e * hh), int(a * ww):int(c * ww)] = 255
    if not o.get('keep_tolerances'):
        em, _notes = erase_mask(pdf, hi.shape)
        if em is not None:
            hi[em] = 255
        info['clean'] = [n for n in _notes if not (n[0] == 'maat' and len(n[2]) > 12)]
    sx, sy = ww / Wd, hh / Hd
    crops = {}
    for k, b in views.items():
        pad = 6
        b = [max(0, b[0] - pad), max(0, b[1] - pad), min(Wd, b[2] + pad), min(Hd, b[3] + pad)]
        bad = [] if o.get('keepall') else clean_view(lab, b)
        X0, Y0, X1, Y1 = int(b[0] * sx), int(b[1] * sy), int(b[2] * sx), int(b[3] * sy)
        c = hi[Y0:Y1, X0:X1].astype(np.float32).copy()
        if bad:
            mk = np.isin(lab[b[1]:b[3], b[0]:b[2]], bad)
            mk = ndi.binary_dilation(mk, iterations=2)
            mk = np.array(Image.fromarray(mk.astype(np.uint8) * 255).resize((X1 - X0, Y1 - Y0), Image.NEAREST)) > 0
            c[mk] = 255
        for a, b_, cc, e in o.get('drop', {}).get(k, []):     # fractions of this view crop
            c[int(b_ * c.shape[0]):int(e * c.shape[0]), int(a * c.shape[1]):int(cc * c.shape[1])] = 255
        ys, xs = np.where(c < 200)
        if len(xs) == 0:
            continue
        crops[k] = (c[ys.min():ys.max() + 1, xs.min():xs.max() + 1], X0 + xs.min(), Y0 + ys.min())
    # compose: keep projection alignment, close the gaps
    G = int(TOPW * 0.07)
    tc, tx, ty = crops['top']
    place = {'top': (0, 0)}
    if 'short' in crops:
        c, x, y = crops['short']
        place['short'] = (tc.shape[1] + G, y - ty)
    if 'long' in crops:
        c, x, y = crops['long']
        place['long'] = (x - tx, tc.shape[0] + G)
    if 'short' in place and 'long' in place:           # never let the two side views touch
        sx0, sy0 = place['short']; sh_, sw_ = crops['short'][0].shape
        lx0, ly0 = place['long']; lh_, lw_ = crops['long'][0].shape
        if lx0 + lw_ > sx0 - G // 2 and ly0 < sy0 + sh_ + G // 2:
            place['long'] = (lx0, sy0 + sh_ + G // 2)
    minx = min(p[0] for p in place.values()); miny = min(p[1] for p in place.values())
    maxx = max(place[k][0] + crops[k][0].shape[1] for k in place)
    maxy = max(place[k][1] + crops[k][0].shape[0] for k in place)
    canvas = np.full((maxy - miny, maxx - minx), 255, np.float32)
    for k, (px, py) in place.items():
        c = crops[k][0]
        sl = canvas[py - miny:py - miny + c.shape[0], px - minx:px - minx + c.shape[1]]
        np.minimum(sl, c, out=sl)
    canvas = ndi.minimum_filter(canvas, size=2)
    pad = 10
    canvas = np.pad(canvas, pad, constant_values=255)
    alpha = np.clip((255 - canvas) * 1.3, 0, 255).astype(np.uint8)
    rgba = np.zeros(canvas.shape + (4,), np.uint8)
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = NAVY
    rgba[..., 3] = alpha
    im = Image.fromarray(rgba, 'RGBA')
    im.save(os.path.join(HERE, m['id'] + '.png'), optimize=True)
    info['px'] = im.size
    done[pid] = info
    ov = Image.fromarray(g).convert('RGB').resize((Wd // 3, Hd // 3))
    dr = ImageDraw.Draw(ov)
    for c, k in (('red', 'top'), ('blue', 'short'), ('green', 'long')):
        if k in views:
            dr.rectangle([v // 3 for v in views[k]], outline=c, width=3)
    ov.save(os.path.join(DBG, m['id'] + '.png'))
    print('ok', base, info['found'], im.size, info.get('clean'))
