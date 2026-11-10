"""Build structured product data from the PIM export + price list + catalog image map.

Output: data/products.json  (models, accessories)
"""
import json, re, os, collections
import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
XLSX = os.environ.get('QP_PIM', os.path.join(ROOT, 'input/pim-export.xlsx'))
PRICE_CSV = os.path.join(ROOT, 'data/prijzen.csv')
IMGMAP = json.load(open(os.path.join(ROOT, 'input/imgmap.json')))


def load_prices():
    """data/prijzen.csv (artikelnummer;prijs_eur_excl_btw;productielocatie;moq_op_aanvraag;...) is leidend."""
    import csv
    if not os.path.exists(PRICE_CSV):
        raise SystemExit('data/prijzen.csv ontbreekt')
    out = {}
    with open(PRICE_CSV, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f, delimiter=';'):
            sku = (r.get('artikelnummer') or '').strip()
            if not sku:
                continue
            pr = (r.get('prijs_eur_excl_btw') or '').strip().replace('€', '').replace(' ', '')
            if ',' in pr:
                pr = pr.replace('.', '').replace(',', '.')
            out[sku] = {'price': float(pr) if pr else None, 'loc': (r.get('productielocatie') or '').strip().upper() or None,
                        'moq_on_request': (r.get('moq_op_aanvraag') or '').strip().lower() in ('ja', 'yes', 'j', '1', 'true')}
    return out


PRICES = load_prices()

# ---------------------------------------------------------------- nieuwe productdata (6 talen, oktober 2026)
NEW_XLSX = os.path.join(ROOT, 'input/producten-6-talen.xlsx')
PPWR_DIR = os.path.join(ROOT, 'input/ppwr')
LANGS6 = ['nl', 'en', 'de', 'fr', 'it', 'es']
LOC_CODE = {'balk': 'B', 'veghel': 'V', 'ribe': 'R', 'marktoberdorf': 'M', 'lleida': 'L', 'nantes': 'N', 'chesterfield': None}   # update 45: Chesterfield is not shown


def load_new():
    """input/producten-6-talen.xlsx: titels, SEO-teksten, materiaal en huidige productielocatie per artikel."""
    out = {}
    if not os.path.exists(NEW_XLSX):
        return out
    ws = openpyxl.load_workbook(NEW_XLSX).active
    rows = list(ws.iter_rows(values_only=True))
    head = [str(h or '').strip() for h in rows[0]]
    def col(name, nth=0):
        idx = [i for i, h in enumerate(head) if h == name]
        return idx[nth] if len(idx) > nth else None
    for r in rows[1:]:
        if not r or not r[0]:
            continue
        sku = str(r[0]).strip()
        loc_raw = (r[col('Huidige locatie')] or '').strip() if col('Huidige locatie') is not None else ''
        code = LOC_CODE.get(loc_raw.split('(')[0].strip().lower()) if loc_raw else None
        out[sku] = {
            'title': {l: (r[col(f'Article title ({l})')] or '').strip() for l in LANGS6},
            'seo': {l: (r[col(f'SEO ({l})')] or '').strip() for l in LANGS6},
            'material': (r[col('Materiaal')] or '').strip() or None,
            'loc': code,
            'loc_raw': loc_raw or None,
            'static': r[col('Static')], 'dynamic': r[col('Dynamic')], 'racking': r[col('Racking')],
            'L': r[col('Length')], 'W': r[col('Width')], 'H': r[col('Height')], 'weight': r[col('Weight')],
        }
    return out


def load_ppwr():
    """SKU -> [PG-nummers] uit de PPWR-conformiteitsverklaringen (input/ppwr/*.pdf, pdftotext nodig)."""
    import glob, subprocess
    cache = os.path.join(ROOT, 'data/ppwr-map.json')
    out = {}
    files = sorted(glob.glob(os.path.join(PPWR_DIR, '*.pdf')))
    try:
        for f in files:
            txt = subprocess.run(['pdftotext', '-layout', f, '-'], capture_output=True, text=True).stdout
            m = re.search(r'GTIN/Product reference\s+SKU:(.*?)\n\n', txt, re.S)
            pg = re.search(r'PG-(\d+)', os.path.basename(f)).group(1)
            if not m:
                continue
            for sku in [x.strip() for x in re.sub(r'\s+', ' ', m.group(1)).split(',') if x.strip()]:
                out.setdefault(sku, []).append({'pg': pg, 'file': os.path.basename(f)})
        json.dump(out, open(cache, 'w'), indent=1)
    except FileNotFoundError:
        if os.path.exists(cache):
            out = json.load(open(cache))
    return out


NEW = load_new()
PPWR = load_ppwr()

LOC = {
    'B': {'nl': 'Balk', 'en': 'Balk', 'cc': 'NL'},
    'V': {'nl': 'Veghel', 'en': 'Veghel', 'cc': 'NL'},
    'R': {'nl': 'Ribe', 'en': 'Ribe', 'cc': 'DK'},
    'M': {'nl': 'Marktoberdorf', 'en': 'Marktoberdorf', 'cc': 'DE'},
    'L': {'nl': 'Lleida', 'en': 'Lleida', 'cc': 'ES'},
    'N': {'nl': 'Nantes', 'en': 'Nantes', 'cc': 'FR'},
}

SIZE_FROM_DIM = {
    '400 x 600 mm': '600x400', '600 x 800 mm': '600x800', '760 x 1140 mm': '760x1140',
    '1100 x 1100 mm': '1100x1100', '1140 x 1140 mm': '1140x1140', '1200 x 800 mm': '1200x800',
    '1200 x 1000 mm': '1200x1000', '1200 x 1200 mm': '1200x1200', '1100 x 1300 mm': '1300x1100',
}


def kg(v):
    if v is None:
        return None
    s = str(v).strip()
    if not s or s.lower().startswith('not'):
        return None
    s = s.replace('kg', '').replace('.', '').strip()
    return int(s)


def slugify(s):
    s = s.lower()
    s = (s.replace('ë', 'e').replace('é', 'e').replace('ï', 'i').replace('ö', 'o')
         .replace('ü', 'u').replace('ä', 'a').replace('×', 'x'))
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s


def base_sku(sku):
    return re.sub(r'^[1-5N]\.', '', sku)


def parse_support(s):
    if not s:
        return None
    m = re.match(r'(\d+)\s+(runners|feet)', s)
    return {'n': int(m.group(1)), 'type': 'runners' if m.group(2) == 'runners' else 'feet'}


def special_of(sku, title):
    t = title.lower()
    if t.startswith('cp'):
        return t.split()[0]  # cp1, cp3, cp6, cp9
    if 'cleanroom' in t:
        return 'cleanroom'
    if t.startswith('hygienic'):
        return 'hygienic'
    if t.startswith('h1'):
        return 'h1'
    if 'pool pallet' in t:
        return 'pool'
    if t.startswith('industrial'):
        return 'industrial'
    if t.startswith('display'):
        return 'display'
    if sku.startswith('QP4048'):
        return 'us'
    return None


def acc_kind(sku):
    if sku.startswith('QGR'):
        return 'grating'
    if sku.startswith('QKR'):
        return 'grid'
    if sku.startswith('QPBIN'):
        return 'driptray'
    if sku.startswith('QPFS'):
        return 'freezer'
    if 'VOUWR' in sku:
        return 'collar'
    if 'DECK' in sku:
        return 'lid'
    if 'RUN' in sku:
        return 'runner'
    return None


def num(v):
    if v is None:
        return None
    try:
        f = float(v)
        return int(f) if f == int(f) else f
    except Exception:
        return None


# articles that are in the PIM but must not be on the website (update 14, Noah 27-10-2026:
# QP76114LB9RR(-CD) are not on qpall.com, have no mould number and duplicate QP76114LB3RR(-CD))
EXCLUDE = {'QP76114LB9RR', 'QP76114LB9RR-CD'}
# single articles of a family that must not be on the website (update 15, Noah 27-10-2026: QPW1210HP5RR-CDG eruit;
# QPW1210HP5RR-CD stays). They leave before grouping, so the family's ranges, prices and locations no longer count them.
EXCLUDE_VARIANTS = {'QPW1210HP5RR-CDG',                                        # update 15
                    'N.QP1210LB9FR', 'N.QP1210LB3RR', 'N.QP1210LB9FR-CD',     # update 19 (Noah 28-10-2026)
                    'QP4048MB6RR-CD',                                            # update 22 (Noah 28-10-2026)
                    # update 45 (Noah 10-11-2026): off the site; the 2.QP1210MB3RR articles are drafts (site_config.DRAFT_SKUS)
                    'QP4048MB3RR', 'QP4048MB3RR-CD', 'QP4048MB6RR', '2.QP1210MB3RR', '2.QP1210MB3RR-CD', '2.QP1210MB3RR-CP1'}


def load_rows():
    wb = openpyxl.load_workbook(XLSX)
    ws = wb.active
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if not r[9]:
            continue
        cats = [c.strip() for c in (r[7] or '').split('|') if c.strip()]
        rows.append({
            'sku': r[9].strip(), 'title': r[0].strip(), 'content_en': r[1],
            'deck': (r[2] or '').strip() or None, 'support_raw': r[3],
            'dynamic': kg(r[4]), 'static': kg(r[5]), 'racking': kg(r[6]),
            'cats': cats, 'dim': r[8], 'cls': (r[11] or '').strip().lower() or None,
            'L': num(r[12]), 'W': num(r[13]), 'H': num(r[14]), 'weight': num(r[15]),
            'pack': num(r[16]), 'seo_title_en': r[17], 'seo_desc_en': r[18],
        })
    return rows


IMG_BY_SKU = {}
for i in IMGMAP:
    if i['sku']:
        IMG_BY_SKU.setdefault(i['sku'], i['xref'])
IMG_BY_BASE = {}
for k, v in IMG_BY_SKU.items():
    IMG_BY_BASE.setdefault(base_sku(k), v)


def build():
    rows = load_rows()
    pallets = [r for r in rows if r['deck'] and r['support_raw'] and r['sku'] not in EXCLUDE_VARIANTS]
    accs = [r for r in rows if not (r['deck'] and r['support_raw'])]

    # ---------- group pallets by base sku ----------
    groups = collections.OrderedDict()
    for r in pallets:
        groups.setdefault(base_sku(r['sku']), []).append(r)

    def sig(r):
        return (r['L'], r['W'], r['H'], r['deck'], r['support_raw'], r['cls'], special_of(r['sku'], r['title']),
                r['static'], r['dynamic'], r['racking'], '-AO' in r['sku'])

    # merge base groups with identical full spec signature (e.g. -AS / -SSB)
    merged = collections.OrderedDict()
    sigmap = {}
    for b, rs in groups.items():
        s = tuple(sorted(set(sig(r) for r in rs)))
        key = s if len(s) == 1 else None
        if key and key in sigmap:
            merged[sigmap[key]].extend(rs)
        else:
            merged[b] = list(rs)
            if key:
                sigmap[key] = b

    models = []
    for b, rs in merged.items():
        variants = []
        for r in rs:
            p = PRICES.get(r['sku'], {})
            nw = NEW.get(r['sku'], {})
            variants.append({
                'sku': r['sku'], 'L': r['L'], 'W': r['W'], 'H': r['H'], 'weight': r['weight'],
                'static': r['static'], 'dynamic': r['dynamic'], 'racking': r['racking'], 'pack': r['pack'],
                'price': p.get('price'),
                # productielocatie: 'Huidige locatie' uit de nieuwe productdata is leidend; leeg = op aanvraag
                'loc': nw.get('loc') if NEW else p.get('loc'),
                'moq_on_request': p.get('moq_on_request', False),
                'in_pricelist': r['sku'] in PRICES,
                'img': IMG_BY_SKU.get(r['sku']),
                'material': nw.get('material'),
                'ppwr': [d['pg'] for d in PPWR.get(r['sku'], [])],
                # every article has its own page since October 2026: its own title and SEO text (6 languages)
                'title6': nw.get('title'), 'seo6': nw.get('seo'),
                'seo_title_en': r['seo_title_en'], 'seo_desc_en': r['seo_desc_en'],
            })
        # primary: cheapest priced variant, else plain base sku, else first
        priced = [v for v in variants if v['price']]
        if priced:
            primary = min(priced, key=lambda v: v['price'])
        else:
            plain = [v for v in variants if v['sku'] == b]
            primary = plain[0] if plain else variants[0]
        pr = next(r for r in rs if r['sku'] == primary['sku'])
        sp = parse_support(pr['support_raw'])
        special = special_of(pr['sku'], pr['title'])
        cats = sorted(set(c for r in rs for c in r['cats']))
        types = []
        for c, t in [('Export pallets', 'export'), ('Nestable pallets', 'nestable'), ('Display pallets', 'display'),
                     ('Block pallets', 'block'), ('CP pallets', 'cp'), ('Hygienic pallets', 'hygienic')]:
            if c in cats:
                types.append(t)
        if special == 'h1' and 'hygienic' not in types:
            types.append('hygienic')   # the H1 Europallet is a hygienic pallet too (Noah, 27-10-2026)
        antislip = any('-AO' in v['sku'] for v in variants)
        if antislip:
            types.append('antislip')
        size = SIZE_FROM_DIM[pr['dim']]

        def rng(key):
            vals = [v[key] for v in variants if v[key] is not None]
            if not vals:
                return None
            return [min(vals), max(vals)]

        img = primary['img'] or next((v['img'] for v in variants if v['img']), None) or IMG_BY_BASE.get(b)
        # stable naming height: most common height, tie -> plain base sku, else lowest
        hs = collections.Counter(v['H'] for v in variants)
        top = max(hs.values())
        cands = sorted(h for h, c in hs.items() if c == top)
        plain_h = next((v['H'] for v in variants if v['sku'] == b), None)
        name_h = plain_h if plain_h in cands else cands[0]
        models.append({
            'id': slugify(b), 'base': b, 'kind': 'pallet', 'size': size,
            'L': pr['L'], 'W': pr['W'], 'H': name_h, 'class': pr['cls'],
            'deck': 'closed' if pr['deck'].lower().startswith('closed') else 'open', 'antislip': antislip,
            'support': sp, 'special': special, 'types': types,
            'variants': variants, 'primary': primary['sku'],
            'static': rng('static'), 'dynamic': rng('dynamic'), 'racking': rng('racking'),
            'weight': rng('weight'), 'height': rng('H'),
            'rackable': any(v['racking'] for v in variants),
            'price_from': min([v['price'] for v in priced]) if priced else None,
            'price_to': max([v['price'] for v in priced]) if priced else None,
            'moq_on_request': any(v['moq_on_request'] for v in priced) if priced else False,
            'locations': sorted(set(v['loc'] for v in variants if v['loc']), key=lambda x: 'BRMNLCV'.index(x)),
            'material': next((v['material'] for v in [primary] + variants if v.get('material')), None),
            'ppwr': sorted(set(pg for v in variants for pg in v['ppwr'])),
            'title6': NEW.get(primary['sku'], {}).get('title') or next((NEW[v['sku']]['title'] for v in variants if v['sku'] in NEW), None),
            'seo6': NEW.get(primary['sku'], {}).get('seo') or next((NEW[v['sku']]['seo'] for v in variants if v['sku'] in NEW), None),
            'in_catalog': any(v['in_pricelist'] for v in variants),
            'img': img, 'img_exact': bool(img),
            'pack': primary['pack'],
            'seo_title_en': pr['seo_title_en'], 'seo_desc_en': pr['seo_desc_en'],
        })

    # image fallbacks
    def fkey(m, lvl):
        s = m['support']
        if lvl == 0:
            return (m['size'], m['deck'], s['type'], s['n'], m['class'])
        if lvl == 1:
            return (m['special'] or '-', m['size'], m['deck']) if m['special'] else ('x', m['id'])
        if lvl == 2:
            return (m['size'], m['deck'], s['type'], s['n'])
        if lvl == 3:
            return (m['special'] or '-',) if m['special'] in ('display',) else ('x', m['id'])
        if lvl == 4:
            return (m['size'], m['deck'], s['type'], m['class'])
        if lvl == 5:
            return (m['size'], m['deck'], s['type'])
        if lvl == 6:
            return (m['deck'], s['type'], s['n'], m['class'])
        return (m['deck'], s['type'])
    for m in models:
        if m['img']:
            continue
        for lvl in range(8):
            cand = [x for x in models if x['img_exact'] and x['antislip'] == m['antislip'] and fkey(x, lvl) == fkey(m, lvl)]
            if cand:
                m['img'] = cand[0]['img']
                m['img_from'] = cand[0]['id']
                break

    # excluded articles leave only now, after the image fallback above (their images stay available to other models)
    models = [m for m in models if not any(v['sku'] in EXCLUDE for v in m['variants'])]

    # ---------- accessories ----------
    known = {r['sku'] for r in rows}
    for sku, nw in NEW.items():
        if sku not in known and acc_kind(sku):
            accs.append({'sku': sku, 'title': nw['title']['en'], 'L': num(nw['L']), 'W': num(nw['W']), 'H': num(nw['H']),
                         'weight': num(nw['weight']), 'static': kg(nw['static']), 'dynamic': kg(nw['dynamic']), 'seo_desc_en': None})
    acc = []
    for r in accs:
        p = PRICES.get(r['sku'], {})
        nw = NEW.get(r['sku'], {})
        acc.append({
            'sku': r['sku'], 'kind': acc_kind(r['sku']), 'title_en': r['title'],
            'L': r['L'], 'W': r['W'], 'H': r['H'], 'weight': r['weight'],
            'static': r['static'], 'dynamic': r['dynamic'],
            'price': p.get('price'), 'loc': (nw.get('loc') if NEW else p.get('loc')),
            'img': IMG_BY_SKU.get(r['sku']) or IMG_BY_BASE.get(base_sku(r['sku'])) or IMG_BY_SKU.get('QPRUN1212' if r['sku'].startswith('QPRUN') else ''),
            'title6': nw.get('title'), 'ppwr': [d['pg'] for d in PPWR.get(r['sku'], [])],
            'color': ('blue' if r['sku'].endswith('blue') else 'black' if r['sku'].endswith('black') else None),
            'seo_desc_en': r['seo_desc_en'],
        })
    out = {'models': models, 'accessories': acc, 'locations': LOC}
    json.dump(out, open(os.path.join(ROOT, 'data/products.json'), 'w'), indent=1, ensure_ascii=False)
    return out


if __name__ == '__main__':
    o = build()
    ms = o['models']
    print('models', len(ms), 'accessories', len(o['accessories']))
    c = collections.Counter(m['size'] for m in ms)
    print(c)
    for m in ms:
        print(f"{m['base']:22} {m['size']:9} {m['class']:6} {m['deck']:6} {m['support']['n']}{m['support']['type'][0]} sp={m['special']} t={m['types']} n={len(m['variants'])} H={m['height']} st={m['static']} dy={m['dynamic']} rk={m['racking']} €={m['price_from']} loc={m['locations']} img={m['img']}{'' if m['img_exact'] else '*'}")
