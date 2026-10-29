#!/usr/bin/env python3
"""Toleranties en radiusmaten uit de technische tekeningen halen (gebruikt door tools/cad_views.py).

Wat er weg gaat (op basis van de vectorgegevens in de pdf, dus niet op gevoel in de afbeelding):
  - toleranties achter een maat: de kleinere, gestapelde tekens zoals "+1 / -3" of "±2"
  - het ovaal (keurmaat-kader) om een maat heen, zodat er alleen "1200" overblijft
  - radiusmaten zoals "R30", met hun aanwijslijn en pijlpunt
Wat blijft: alle andere maten, maatlijnen en de vorm van de pallet. Lijnen van de tekening die toevallig
onder een weggehaald stuk doorlopen worden beschermd, zodat er geen gaatjes in de tekening vallen.

Gebruik (los, ter controle):  python3 tools/cad_clean.py <tekening.pdf> [uit.png]
  -> schrijft een overzicht met rood gemarkeerd wat er weg gaat.
Vereist: pdfplumber, numpy, Pillow.
"""
import math, re, sys
import numpy as np
from PIL import Image, ImageDraw
import pdfplumber

SIGNS = set('+-±−–²')   # ² = ± in a few drawings whose font maps the glyph wrongly


def _dir(c):
    a, b = c['matrix'][0], c['matrix'][1]
    s = math.hypot(a, b) or 1.0
    return s, (a / s, b / s)


def _clusters(chars):
    """Group characters into labels: same writing direction and close together."""
    n = len(chars)
    info = []
    for c in chars:
        s, d = _dir(c)
        info.append((s, d, ((c['x0'] + c['x1']) / 2, (c['top'] + c['bottom']) / 2)))
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    # grid for speed
    cell = 14.0
    grid = {}
    for i, (_, _, (x, y)) in enumerate(info):
        grid.setdefault((int(x // cell), int(y // cell)), []).append(i)
    for i, (si, di, (xi, yi)) in enumerate(info):
        gx, gy = int(xi // cell), int(yi // cell)
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                for j in grid.get((gx + ox, gy + oy), ()):
                    if j <= i:
                        continue
                    sj, dj, (xj, yj) = info[j]
                    if abs(di[0] * dj[1] - di[1] * dj[0]) > 0.09 or di[0] * dj[0] + di[1] * dj[1] < 0:
                        continue
                    if math.hypot(xi - xj, yi - yj) < 1.25 * max(si, sj):
                        parent[find(i)] = find(j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    out = []
    for idx in groups.values():
        cs = [chars[i] for i in idx]
        d = info[idx[0]][1]
        # reading order along the baseline (PDF y is up in the matrix)
        cs.sort(key=lambda c: c['matrix'][4] * d[0] + c['matrix'][5] * d[1])
        out.append(cs)
    return out


def _bbox(objs, pad=0.0):
    return (min(o['x0'] for o in objs) - pad, min(o['top'] for o in objs) - pad,
            max(o['x1'] for o in objs) + pad, max(o['bottom'] for o in objs) + pad)


def _inter(a, b):
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def _inside(p, b):
    return b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3]


def analyse(page):
    chars = [c for c in page.chars if c['text'].strip()]
    lines = page.lines
    curves = page.curves
    drop_chars, drop_paths, notes = [], [], []

    clusters = _clusters(chars)
    digit_cl = [(max(_dir(c)[0] for c in k), _bbox(k)) for k in clusters if any(c['text'].isdigit() for c in k)]
    for cl in clusters:
        big = max(_dir(c)[0] for c in cl)
        text = ''.join(c['text'] for c in cl)
        main = [c for c in cl if _dir(c)[0] > 0.85 * big]
        small = [c for c in cl if _dir(c)[0] <= 0.85 * big]
        main_txt = ''.join(c['text'] for c in main)
        has_digits = any(ch.isdigit() for ch in main_txt)

        # --- radius: "R30", "4x R30", "R 12,5"
        if re.search(r'(^|[\sxX×])R\s?\d', main_txt) and len(main_txt) <= 12:
            box = _bbox(cl)
            drop_chars += cl
            pad = 0.6 * big
            hit = (box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad)
            _, d = _dir(cl[0])
            tang = math.atan2(-d[1], d[0])                 # text direction in page (top-down) coordinates

            def ang(l):
                (x0, y0), (x1, y1) = l['pts'][0], l['pts'][-1]
                return math.atan2(y1 - y0, x1 - x0)

            def length(l):
                (x0, y0), (x1, y1) = l['pts'][0], l['pts'][-1]
                return math.hypot(x1 - x0, y1 - y0)

            def heads_at(p):
                return [c for c in curves if len(c['pts']) <= 6 and c['x1'] - c['x0'] < 2.5 * big
                        and c['bottom'] - c['top'] < 2.5 * big
                        and any(math.hypot(q[0] - p[0], q[1] - p[1]) < 0.6 for q in c['pts'])]
            # the leader runs along the text (aligned radius text) and starts at/under it
            lead = [l for l in lines if (_inside(l['pts'][0], hit) or _inside(l['pts'][-1], hit))
                    and abs(math.sin(ang(l) - tang)) < 0.12 and length(l) > 0.5 * big]
            ends = [p for l in lead for p in (l['pts'][0], l['pts'][-1])]
            # short collinear continuation past the arrow (runs on to the arc), at most a few pieces
            for _ in range(3):
                more = [l for l in lines if l not in lead and length(l) <= 1.5 * big
                        and any(math.hypot(p[0] - q[0], p[1] - q[1]) < 0.4 for p in (l['pts'][0], l['pts'][-1]) for q in ends)
                        and any(abs(math.sin(ang(l) - ang(m))) < 0.05 for m in lead)]
                if not more:
                    break
                lead += more
                ends += [p for l in more for p in (l['pts'][0], l['pts'][-1])]
            # horizontal text on a shoulder: one bent leg, only if it ends in an arrowhead
            for l in lines:
                if l in lead:
                    continue
                p0, p1 = l['pts'][0], l['pts'][-1]
                for a, b in ((p0, p1), (p1, p0)):
                    if any(math.hypot(a[0] - q[0], a[1] - q[1]) < 0.4 for q in ends) and not _inside(b, hit) \
                            and heads_at(b) and length(l) < 25 * big:
                        lead.append(l)
                        ends += [a, b]
                        break
            heads = []
            for p in ends:
                heads += [c for c in heads_at(p) if c not in heads]
            drop_paths += lead + heads
            notes.append(('radius', main_txt, len(lead), len(heads)))
            continue

        if not has_digits:
            continue
        tol = []
        # a tolerance that ended up as its own little label ("+1" above "-3", or "±0,50" a bit apart)
        if not small and re.fullmatch(r'[±+\-−–]\s?\d+([.,]\d+)?', main_txt.strip()):
            box = _bbox(cl)
            for sc, ob in digit_cl:
                if ob == box:
                    continue
                gap = max(ob[0] - box[2], box[0] - ob[2], ob[1] - box[3], box[1] - ob[3], 0)
                if gap < 2.5 * big and (sc >= 1.12 * big or main_txt.strip()[0] == '±'):
                    drop_chars += cl
                    notes.append(('tol-los', main_txt.strip()))
                    break
            continue
        if small and any(c['text'] in SIGNS for c in small):
            tol = small
        elif small:
            notes.append(('klein-onbekend', main_txt.strip(), ''.join(c['text'] for c in small)))
        else:
            # same-size "±2" behind a value
            for i, c in enumerate(cl):
                if c['text'] in ('±', '²') and any(ch['text'].isdigit() for ch in cl[:i]):
                    tol = cl[i:]
                    break
        # oval (inspection frame) around the value
        box = _bbox(cl)
        pad = 2.0 * big          # room for a symbol drawn as lines in front of the value (□1100)
        near = (box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad)
        semis = [c for c in curves if len(c['pts']) >= 10 and not c.get('fill')
                 and max(c['x1'] - c['x0'], c['bottom'] - c['top']) < 2.6 * big and _inter(c_box(c), near)]
        oval = []
        # an oval = two half circles joined by two straight lines, and the value must sit inside it
        # (so the rounded slots of the pallet itself are never touched)
        cx_, cy_ = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2

        def near_end(p, c):
            return any(math.hypot(p[0] - q[0], p[1] - q[1]) < 0.4 for q in (c['pts'][0], c['pts'][-1]))
        for i1 in range(len(semis)):
            for i2 in range(i1 + 1, len(semis)):
                s1, s2 = semis[i1], semis[i2]
                conn = [l for l in lines if (near_end(l['pts'][0], s1) and near_end(l['pts'][-1], s2))
                        or (near_end(l['pts'][0], s2) and near_end(l['pts'][-1], s1))]
                if len(conn) < 2:
                    continue
                ob = _bbox([s1, s2] + conn)
                t_small, t_large = sorted((box[2] - box[0], box[3] - box[1]))
                o_small, o_large = sorted((ob[2] - ob[0], ob[3] - ob[1]))
                snug = o_small <= t_small + 1.6 * big and o_large <= t_large + 4 * big   # hugs the text, unlike a slot
                e = 0.3 * big                                   # glyph boxes include some white space
                inside = ob[0] - e <= box[0] and box[2] <= ob[2] + e and ob[1] - e <= box[1] and box[3] <= ob[3] + e
                if snug and inside and ob[0] < cx_ < ob[2] and ob[1] < cy_ < ob[3]:
                    oval += [s1, s2] + conn
        if tol or oval:
            drop_chars += tol
            drop_paths += oval
            notes.append(('maat', main_txt.strip(), ''.join(c['text'] for c in tol), 'ovaal' if oval else ''))
    return drop_chars, drop_paths, notes


def c_box(o):
    return (o['x0'], o['top'], o['x1'], o['bottom'])


def _draw_path(dr, o, kx, ky, w, fill=False):
    pts = [(p[0] * kx, p[1] * ky) for p in o['pts']]
    if len(pts) < 2:
        return
    if fill or (o.get('fill') and len(pts) <= 6):
        dr.polygon(pts, fill=255, outline=255)
    dr.line(pts, fill=255, width=max(1, int(round(w))))


def erase_mask(pdf, shape, page_no=0):
    """Boolean mask (True = make white) for a rendering of the page with the given (h, w)."""
    hh, ww = shape
    with pdfplumber.open(pdf) as doc:
        page = doc.pages[page_no]
        kx, ky = ww / float(page.width), hh / float(page.height)
        dchars, dpaths, notes = analyse(page)
        if not dchars and not dpaths:
            return None, notes
        er = Image.new('L', (ww, hh), 0)
        de = ImageDraw.Draw(er)
        for c in dchars:                                   # glyphs can stick out of their box a little
            m = max(2.0, 0.15 * _dir(c)[0] * kx)
            de.rectangle([c['x0'] * kx - m, c['top'] * ky - m, c['x1'] * kx + m, c['bottom'] * ky + m], fill=255)
        for o in dpaths:
            _draw_path(de, o, kx, ky, (o.get('linewidth') or 0.5) * kx + 4)
        E = np.array(er) > 0
        # protect everything else that crosses the erased area
        ys, xs = np.where(E)
        region = (xs.min() / kx - 2, ys.min() / ky - 2, xs.max() / kx + 2, ys.max() / ky + 2)
        drop_ids = {id(o) for o in dpaths}
        drop_c = {id(c) for c in dchars}
        pr = Image.new('L', (ww, hh), 0)
        dp = ImageDraw.Draw(pr)
        for o in page.lines + page.curves + page.rects:
            if id(o) in drop_ids or not _inter(c_box(o), region):
                continue
            if 'pts' not in o:
                continue
            _draw_path(dp, o, kx, ky, (o.get('linewidth') or 0.5) * kx + 1.5)
        for c in page.chars:
            if id(c) in drop_c or not c['text'].strip() or not _inter(c_box(c), region):
                continue
            dp.rectangle([c['x0'] * kx, c['top'] * ky, c['x1'] * kx, c['bottom'] * ky], fill=255)
        P = np.array(pr) > 0
        return E & ~P, notes


if __name__ == '__main__':
    pdf = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else 'cad_clean_check.png'
    import subprocess, tempfile, os
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(['pdftoppm', '-gray', '-r', '200', '-png', '-singlefile', pdf, os.path.join(d, 'p')], check=True,
                       stderr=subprocess.DEVNULL)
        g = np.array(Image.open(os.path.join(d, 'p.png')).convert('L'))
    m, notes = erase_mask(pdf, g.shape)
    for n in notes:
        print(n)
    rgb = np.stack([g] * 3, -1)
    if m is not None:
        rgb[m & (g < 200)] = (230, 30, 30)
    Image.fromarray(rgb).save(out)
    print('->', out)
