#!/usr/bin/env python3
"""301 redirects for old qpall.com paths that Google still knows but that were not in the old sitemap.

Input : data/oude-site/gsc-16-maanden.txt  one path per line (Search Console > Performance > Pages, 16 months, and the
        Internal links report, export 21-10-2026): older product URLs, the old Spanish category /es/palet-plastico/...,
        FAQ pages, catalogue PDFs, job ads, pick-up addresses ...
Output: data/redirects-gsc.txt   (build_assets.py puts these rules right after data/redirects-extra.txt)

Rules, in order: a fixed list for one-off pages; the product id at the end of an old product URL (-217) via
data/oude-site/producten.txt; the product described in the slug (size, deck, runners/feet, class) in any of the
six languages; then the category, FAQ topic or size named in the path. Every target is a page of the new site.
Run:  python3 tools/redirects_gsc.py  &&  python3 tools/redirects_check.py
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from site_config import PAGES, LANGS, CATALOG_FILES   # noqa: E402
import redirects_qpall as RQ                           # noqa: E402  (helpers + data only; its main() is not run)

D = os.path.join(ROOT, 'data', 'oude-site')


def url(pid, lang):
    return '/' + PAGES[pid]['path'][lang]


# old product id (number at the end of the old URL) -> article number, from the old sitemap
IDS = {}
for line in open(os.path.join(D, 'producten.txt'), encoding='utf-8'):
    if line.startswith('#') or not line.strip():
        continue
    gid, path, sku = line.split()[:3]
    m = re.search(r'-(\d+)$', path.split(':')[-1])
    if m:
        IDS[m.group(1)] = sku

# fixed targets (path without trailing slash -> page id, or a full path)
FIXED = {
    '/files/qpa18219-catalogus-en-d2.pdf': '/' + CATALOG_FILES['en'],
    '/files/qpa18219-catalogus-nl-d2.pdf': '/' + CATALOG_FILES['nl'],
    '/files/qpa18079-catalogus-du-d2.pdf': '/' + CATALOG_FILES['de'],
    '/files/catalogus-qpall-french.pdf': '/' + CATALOG_FILES['fr'],
    '/files/qpa24119-handout-2024-d1-web.pdf': ('catalog', 'nl'),
    '/files/hrplasticrecyclingsymbols-1.jpg': ('news-ric', 'nl'),
    '/plastic-pallets': ('pallets', 'en'),
    '/pooling': ('sector-pooling', 'nl'),
    '/retail': ('sector-retail', 'nl'),
    '/hoe-worden-kunststof-pallets-gemaakt-': ('about-local', 'nl'),
    '/de/contact/internationale-handler': ('dealers', 'de'),
    '/de/cookie-erkla-rung': ('cookies', 'de'),
}

LANG_PREFIX = ('en', 'de', 'fr', 'it', 'es', 'nl')

# topic words in old category / FAQ paths -> page id (first match wins)
TOPICS = [
    (r'gebruikt|used|usad|occasion|usati|gebraucht|zijn-gebruikte', 'used'),
    (r'meermalige', 'pallets'),
    (r'vacature', 'careers'),
    (r'afhaaladressen', 'transport'),
    (r'gemaakt|made-of|bestehen|hechos|fatti|faites', 'about-sustainability'),
    (r'esd|antista|antiestat', 'about-glossary'),
    (r'belasting', 'about-load'),
    (r'klickbare|clickable|encajables', 'acc-runners'),
    (r'customized', 'about-custom'),
    (r'quimico|chimi|chemie|/cp\d|cp-pallet', 'type-cp'),
    (r'expositor|display', 'type-display'),
    (r'higienic|hygien|igienic', 'type-hygienic'),
    (r'exportacion|export', 'type-export'),
    (r'blokpallet|block', 'type-block'),
    (r'apilables', 'pallets'),
]
SIZES = {'600-x-400': 'size-600x400', '600-x-800': 'size-600x800', '800-x-600': 'size-600x800', '760-x-1140': 'size-760x1140',
         '1100-x-1100': 'size-1100x1100', '1140-x-1140': 'size-1140x1140', '1200-x-800': 'size-1200x800', '1200-x-1000': 'size-1200x1000',
         '1220-x-1020': 'size-1200x1000', '40-x-48-inch': 'size-1200x1000', '1200-x-1200': 'size-1200x1200', '1300-x-1100': 'size-1300x1100'}
CATEGORY_ROOTS = ('palet-plastico', 'pallets-in-plastica', 'pallete-plastique', 'palette-plastique', 'plastic-pallets', 'kunststoffpaletten',
                  'kunststof-pallets')

# product slug words in all six languages
DECK = {'closed': r'gesloten|geschlossen|ferme|chiuso|cerrad|closed', 'open': r'open|offen|ouvert|ajoure|aperto|abiert'}
SUPPORT = {'runners': r'onderlat|runners|kufen|semelles|listelli|slitte|patines', 'feet': r'pootjes|feet|fusse|pieds|plots|piedi|pies'}
CLASS = {'light': r'light|legere|ligero', 'medium': r'medium|medio', 'heavy': r'heavy|lourde|pesado'}
ACC = [(r'congel|freezer|vries|gefrier', 'acc-freezer'), (r'retencion|retention|lekbak|auffang|raccolta|drip', 'acc-drip'),
       (r'vouwrand|rehausse|collar|aufsatz|collare|collarin', 'acc-collars'), (r'deksel|lid|couvercle|deckel|coperchio|tapa', 'acc-lids')]


def lang_of(path):
    seg = path.strip('/').split('/')[0]
    return seg if seg in LANG_PREFIX else 'nl'


def parse_product(slug):
    m = re.search(r'(\d{3,4})-x-(\d{3,4})(?:-x-(\d{2,3}))?', slug)
    if not m:
        return None
    L, W, H = int(m.group(1)), int(m.group(2)), int(m.group(3)) if m.group(3) else None
    words = slug.replace('-', ' ')

    def pick(table):
        return next((k for k, pat in table.items() if re.search(pat, words)), None)
    sup = None
    sm = re.search(r'(\d)-(?:' + '|'.join(SUPPORT.values()) + ')', slug)
    if sm:
        sup = (pick(SUPPORT), int(sm.group(1)))
    special = next((k for k, pat in (('hygienic', r'hygien|higien|igienic'), ('cleanroom', 'cleanroom'), ('display', r'display|exposi'),
                                    ('pool', 'pool')) if re.search(pat, words)), None)
    cp = re.search(r'\bcp(\d)\b', words)
    if cp:
        special = 'cp' + cp.group(1)
    return dict(L=L, W=W, H=H, deck=pick(DECK), sup=sup, cls=pick(CLASS), special=special,
                antislip=bool(re.search(r'anti ?slip|anti ?rutsch|antiderap|antidesliz|antisciv', words)))


def match_product(p, lang):
    dims = {(p['L'], p['W']), (p['W'], p['L'])}
    cands = [m for m in RQ.DATA['models'] if (m['L'], m['W']) in dims]
    if not cands:
        return None

    def score(m):
        s = 0
        if p['deck'] and m['deck'] == p['deck']:
            s += 4
        if p['sup'] and m['support']['type'] == p['sup'][0]:
            s += 3
            if m['support']['n'] == p['sup'][1]:
                s += 3
        if p['cls'] and m['class'] == p['cls']:
            s += 4
        if p['H'] and p['H'] in [v['H'] for v in m['variants']]:
            s += 2
        sp = m.get('special')
        if (p['special'] or None) == (sp or None) or (p['special'] or '').startswith('cp') and 'cp' in m['types']:
            s += 3
        if m['antislip'] == p['antislip']:
            s += 1
        return s
    best = max(cands, key=score)
    return RQ.MURL[best['id']][lang] if score(best) >= 10 else None


def target(path):
    key = path.rstrip('/') or '/'
    if key in FIXED:
        v = FIXED[key]
        return v if isinstance(v, str) else url(*v)
    lang = lang_of(key)
    rest = key[len('/' + lang):] if key.startswith('/' + lang + '/') else key
    slug = rest.strip('/').split('/')[-1]
    # thumbnails: /files/thumbnails/<article>.<size>.png -> the product page of that article
    m = re.match(r'/files/thumbnails/([a-z0-9-]+)\.', key)
    if m:
        t = RQ.product_target(m.group(1).upper(), 'nl')
        if t:
            return t
    # old product pages with a known id (number at the end of the slug)
    m = re.search(r'-(\d+)$', slug)
    if m and m.group(1) in IDS:
        t = RQ.product_target(IDS[m.group(1)], lang)
        if t:
            return t
    # FAQ pages, job ads, pick-up addresses, used pallets ...
    for pat, pid in TOPICS:
        if pid in ('type-cp', 'type-display', 'type-hygienic', 'type-export', 'type-block', 'pallets') and not any(r in rest for r in CATEGORY_ROOTS):
            continue          # category words only count inside an old category path
        if re.search(pat, rest):
            return url(pid, lang)
    # old product pages without a known id: the product described in the slug
    if re.search(r'\d{3,4}-x-\d{3,4}', slug) and not slug.endswith('-mm'):
        for pat, pid in ACC:
            if re.search(pat, slug):
                return url(pid, lang)
        p = parse_product(slug)
        t = match_product(p, lang) if p else None
        if t:
            return t
    # sizes inside an old category path, then the category itself
    for k, pid in SIZES.items():
        if k in rest:
            return url(pid, lang)
    if any(rest.strip('/') == r for r in CATEGORY_ROOTS):
        return url('pallets', lang)
    return None


def main():
    rules, miss = [], []
    for line in open(os.path.join(D, 'gsc-16-maanden.txt'), encoding='utf-8'):
        p = line.strip()
        if not p or p.startswith('#'):
            continue
        t = target(p)
        if t:
            if (t.rstrip('/') or '/') != (p.rstrip('/') or '/'):
                rules.append((p.rstrip('/') or '/', t))
        else:
            miss.append(p)
    out = ['# 301-redirects voor oude qpall.com-paden uit Search Console (16 maanden) en Interne links, export 21-10-2026',
           '# Gemaakt door tools/redirects_gsc.py uit data/oude-site/gsc-16-maanden.txt, niet met de hand wijzigen.']
    out += [f'{a}  {b}  301' for a, b in rules]
    open(os.path.join(ROOT, 'data', 'redirects-gsc.txt'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print(f'{len(rules)} rules -> data/redirects-gsc.txt')
    for p in miss:
        print('  NO TARGET', p)
    return 1 if miss else 0


if __name__ == '__main__':
    sys.exit(main())
