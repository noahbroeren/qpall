"""Generate a dotted Europe map (SVG) with Q-Pall production sites, in the style of the catalog.

Writes data/europe_map.json with dot coordinates + pin positions so the site builder
can inline it (keeps it themeable via CSS classes).
"""
import json, math, os
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.ops import unary_union
from shapely.prepared import prep

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPO = os.path.join(ROOT, 'input/land-50m.json')  # world-atlas 2.0.2 (Natural Earth, publiek domein)

topo = json.load(open(TOPO))
sc = topo['transform']['scale']; tr = topo['transform']['translate']
arcs = []
for arc in topo['arcs']:
    x = y = 0; pts = []
    for dx, dy in arc:
        x += dx; y += dy
        pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
    arcs.append(pts)


def ring(idx):
    pts = []
    for i in idx:
        a = arcs[i] if i >= 0 else list(reversed(arcs[~i]))
        pts.extend(a if not pts else a[1:])
    return pts


polys = []
geom = topo['objects']['land']
for g in geom['geometries']:
    if g['type'] == 'Polygon':
        rings = [ring(r) for r in g['arcs']]
        polys.append(Polygon(rings[0], rings[1:]))
    elif g['type'] == 'MultiPolygon':
        for p in g['arcs']:
            rings = [ring(r) for r in p]
            if len(rings[0]) >= 3:
                polys.append(Polygon(rings[0], rings[1:]))
land = prep(unary_union([p.buffer(0) for p in polys]))

LON0, LON1, LAT0, LAT1 = -11.5, 31.5, 35.0, 64.5
K = math.cos(math.radians(50))
W = 1000
sx = W / ((LON1 - LON0) * K)
H = (LAT1 - LAT0) * sx


def proj(lon, lat):
    return ((lon - LON0) * K * sx, (LAT1 - lat) * sx)


step_lat = 0.62
dots = []
lat = LAT1
row = 0
while lat >= LAT0:
    step_lon = step_lat / K
    off = (step_lon / 2) if row % 2 else 0
    lon = LON0 + off
    while lon <= LON1:
        if land.contains(Point(lon, lat)):
            x, y = proj(lon, lat)
            dots.append([round(x, 1), round(y, 1)])
        lon += step_lon
    lat -= step_lat
    row += 1

SITES = [
    {'id': 'veghel', 'name': 'Veghel', 'cc': 'NL', 'lat': 51.616, 'lon': 5.549, 'hq': True},
    {'id': 'balk', 'name': 'Balk', 'cc': 'NL', 'lat': 52.897, 'lon': 5.579},
    {'id': 'ribe', 'name': 'Ribe', 'cc': 'DK', 'lat': 55.328, 'lon': 8.762},
    {'id': 'marktoberdorf', 'name': 'Marktoberdorf', 'cc': 'DE', 'lat': 47.778, 'lon': 10.617},
    {'id': 'nantes', 'name': 'Nantes', 'cc': 'FR', 'lat': 47.218, 'lon': -1.553},
    {'id': 'lleida', 'name': 'Lleida', 'cc': 'ES', 'lat': 41.617, 'lon': 0.62},
]
km_per_deg_lat = 111.2
r600 = 600 / km_per_deg_lat * sx  # radius of 600 km in px (north-south)
for s in SITES:
    s['x'], s['y'] = [round(v, 1) for v in proj(s['lon'], s['lat'])]
json.dump({'w': W, 'h': round(H), 'dots': dots, 'sites': SITES, 'r600': round(r600, 1), 'dot_r': round(step_lat * sx * 0.36, 2)},
          open(os.path.join(ROOT, 'data/europe_map.json'), 'w'))
print(len(dots), W, round(H), r600)
