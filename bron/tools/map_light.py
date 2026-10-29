"""Static, light Europe map with the Q-Pall factories and a 600 km delivery radius.

Input : input/land-50m.json (world-atlas 2.0.2 / Natural Earth land, public domain)
Output: data/europe-map-light.svg  (inlined on the homepage and the produce-local page)
No third-party libraries needed.  Run:  python3 tools/map_light.py
"""
import json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
topo = json.load(open(os.path.join(ROOT, 'input/land-50m.json')))
sc, tr = topo['transform']['scale'], topo['transform']['translate']

arcs = []
for arc in topo['arcs']:
    x = y = 0
    pts = []
    for dx, dy in arc:
        x += dx
        y += dy
        pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
    arcs.append(pts)


def ring(idx):
    pts = []
    for i in idx:
        a = arcs[i] if i >= 0 else list(reversed(arcs[~i]))
        pts.extend(a if not pts else a[1:])
    return pts


LON0, LON1, LAT0, LAT1 = -11.0, 22.5, 36.6, 60.6
K = math.cos(math.radians(49))
W = 640
SX = W / ((LON1 - LON0) * K)
H = round((LAT1 - LAT0) * SX)
KM_PER_DEG = 111.2


def proj(lon, lat):
    return ((lon - LON0) * K * SX, (LAT1 - lat) * SX)


def simplify(pts, tol=0.55):
    """Ramer-Douglas-Peucker on projected points (keeps the file small)."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1
        n = math.hypot(dx, dy) or 1e-9
        best, idx = 0.0, -1
        for i in range(a + 1, b):
            x0, y0 = pts[i]
            d = abs(dy * x0 - dx * y0 + x2 * y1 - y2 * x1) / n if n > 1e-9 else math.hypot(x0 - x1, y0 - y1)
            if d > best:
                best, idx = d, i
        if best > tol and idx > 0:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(pts, keep) if k]


def clip(pts, x0, y0, x1, y1):
    """Sutherland-Hodgman: clip a closed ring to the rectangle (drops off-map coastline)."""
    def cut(points, inside, inter):
        res = []
        for i, cur in enumerate(points):
            prev = points[i - 1]
            if inside(cur):
                if not inside(prev):
                    res.append(inter(prev, cur))
                res.append(cur)
            elif inside(prev):
                res.append(inter(prev, cur))
        return res

    def ix(a, b, x):
        t = (x - a[0]) / (b[0] - a[0])
        return (x, a[1] + t * (b[1] - a[1]))

    def iy(a, b, y):
        t = (y - a[1]) / (b[1] - a[1])
        return (a[0] + t * (b[0] - a[0]), y)

    for inside, inter in ((lambda p: p[0] >= x0, lambda a, b: ix(a, b, x0)),
                          (lambda p: p[0] <= x1, lambda a, b: ix(a, b, x1)),
                          (lambda p: p[1] >= y0, lambda a, b: iy(a, b, y0)),
                          (lambda p: p[1] <= y1, lambda a, b: iy(a, b, y1))):
        if not pts:
            break
        pts = cut(pts, inside, inter)
    return pts


def inside(pts, pad=3.0):
    return any(LON0 - pad <= lo <= LON1 + pad and LAT0 - pad <= la <= LAT1 + pad for lo, la in pts)


paths = []
for g in topo['objects']['land']['geometries']:
    polys = [g['arcs']] if g['type'] == 'Polygon' else g['arcs']
    for p in polys:
        if not inside(ring(p[0])):
            continue
        sub = []
        for r in p:
            pts = ring(r)
            if len(pts) < 4:
                continue
            xy = clip([proj(lo, la) for lo, la in pts], -6, -6, W + 6, H + 6)
            if len(xy) < 4:
                continue
            xy = simplify(xy)
            out, last = [], None
            for x, y in xy:
                q = (round(x, 1), round(y, 1))
                if q != last:
                    out.append(q)
                    last = q
            if len(out) < 4:
                continue
            sub.append('M' + 'L'.join(f'{x:g} {y:g}' for x, y in out) + 'Z')
        if sub:
            paths.append(''.join(sub))

FACTORIES = [  # code, name, lon, lat, label offset (dx, dy), anchor
    ('B', 'Balk', 5.58, 52.90, (12, -10), 'start'),
    ('R', 'Ribe', 8.77, 55.33, (12, 4), 'start'),
    ('M', 'Marktoberdorf', 10.62, 47.78, (12, 4), 'start'),
    ('N', 'Nantes', -1.55, 47.22, (-12, 4), 'end'),
    ('L', 'Lleida', 0.62, 41.62, (12, 4), 'start'),
    ('C', 'Chesterfield', -1.43, 53.23, (-12, 4), 'end'),
]
HQ = ('V', 'Veghel', 5.55, 51.62)
R_KM = 600
LBL = ('font-family="Poppins,system-ui,sans-serif" font-size="16" font-weight="600" fill="#1D1C4C" paint-order="stroke" '
       'stroke="#F3F3F3" stroke-width="3" stroke-linejoin="round"')

# Interactive: every factory is a focusable group (data-fac = location code). site.js highlights its
# 600 km circle and shows the info card; build.py fills in the language-dependent texts (__TITLE__, __L_<code>__).
r = R_KM / KM_PER_DEG * SX
svg = [f'<svg class="eu-map" viewBox="0 0 {W} {H}" role="group" aria-labelledby="eu-map-t" xmlns="http://www.w3.org/2000/svg">',
       '<title id="eu-map-t">__TITLE__</title>',
       f'<rect width="{W}" height="{H}" fill="#F3F3F3"/>',
       '<g fill="#FFFFFF" fill-rule="evenodd" stroke="#DCDCE6" stroke-width=".8" stroke-linejoin="round">' + ''.join(f'<path d="{d}"/>' for d in paths) + '</g>',
       '<g class="m-radii" fill="#F37321" fill-opacity=".06" stroke="#F37321" stroke-width="1.4" stroke-dasharray="5 5">']
for code, name, lo, la, _, _ in FACTORIES:
    x, y = proj(lo, la)
    svg.append(f'<circle class="m-r" data-fac="{code}" cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}"/>')
svg.append('</g>')
code, name, lo, la = HQ
x, y = proj(lo, la)
svg.append(f'<g class="m-fac m-hqg" data-fac="{code}" tabindex="0" role="button" aria-pressed="false" aria-label="__L_{code}__">'
           f'<circle class="m-hit" cx="{x:.1f}" cy="{y:.1f}" r="18" fill="transparent"/>'
           f'<rect class="m-sq" x="{x - 6:.1f}" y="{y - 6:.1f}" width="12" height="12" rx="3" fill="#1D1C4C"/>'
           f'<text class="m-lbl m-hq" x="{x + 12:.1f}" y="{y + 5:.1f}" text-anchor="start" {LBL}>{name}</text></g>')
for code, name, lo, la, (dx, dy), anchor in FACTORIES:
    x, y = proj(lo, la)
    svg.append(f'<g class="m-fac" data-fac="{code}" tabindex="0" role="button" aria-pressed="false" aria-label="__L_{code}__">'
               f'<circle class="m-hit" cx="{x:.1f}" cy="{y:.1f}" r="18" fill="transparent"/>'
               f'<circle class="m-dot" cx="{x:.1f}" cy="{y:.1f}" r="7" fill="#F37321" stroke="#fff" stroke-width="2.5"/>'
               f'<text class="m-lbl" x="{x + dx:.1f}" y="{y + dy:.1f}" text-anchor="{anchor}" {LBL}>{name}</text></g>')
svg.append('</svg>')
out = ''.join(svg)
open(os.path.join(ROOT, 'data/europe-map-light.svg'), 'w', encoding='utf-8').write(out)
print(f'map {W}x{H}, {len(paths)} land paths, {len(out) // 1024} KB, radius {r:.1f}px')
