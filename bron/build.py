#!/usr/bin/env python3
"""Q-Pall static site generator → ../qpall-website (Netlify package), six languages.

Usage:  python3 build.py            (QP_KEEP_IMAGES=1 skips regenerating images)
Sources: data/products.json, input/photos/, content/<lang>/*.md, i18n/<lang>.json, templates/, static/
Extra steps (see bouwen.sh): tools/datasheets.py (PDF's), tools/og.py (OG-afbeeldingen), pagefind (zoekindex)
"""
import os, re, json, math, shutil, glob, hashlib, datetime, subprocess
import yaml, markdown
from urllib.parse import quote_plus
from jinja2 import Environment, FileSystemLoader, select_autoescape, pass_context
from markupsafe import Markup, escape

from site_config import (SHOW_PRICES, NOINDEX_ALL, GTM_ID, PROD_HOSTS, HUBSPOT_HOSTS, HUBSPOT_ID, HUBSPOT_REGION, HUBSPOT_FORMS, SKU_COLOUR, SB_CROP, ARTICLE_RECOMMEND, LANG_REGION, KB_ITEMS, KB_CATS, DOMAIN, LANGS, X_DEFAULT, PAGES, SIZES, SIZE_BY_KEY, TYPES, TYPE_BY_KEY, CLASSES, SECTORS, COMPANY,
                         LOCATIONS, FACTORIES, COUNTRY, REDIRECTS, CATALOG_FILES, catalog_size, PRICE_VALID_UNTIL, BUILD_DATE,
                         LOCALE, HTML_LANG, LANG_NAME, TRANSPORT_SITES, OG_PAGES, GUIDES, PREFIX, NEWS_ITEMS, TEAM, TEAM_BY, TEAM_BY_NAME, AUTHORS, KB_SIDE_EXTRA, LAUNCH_DATE, DEALERS)
from i18n import T, MISSING
import productcopy as PC
from productcopy import fmt_int, fmt_dec, fmt_price, rng_txt
from drawings import drawing, ACC_ILLU
from build_util import slugify
from build_assets import HEAVY_COVERS

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('QP_OUT', os.path.join(os.path.dirname(ROOT), 'qpall-website'))
INPUT = os.path.join(ROOT, 'input')
RAW = os.path.join(INPUT, 'raw')
VERSION = hashlib.md5(open(os.path.join(ROOT, 'static/css/site.css'), 'rb').read() + open(os.path.join(ROOT, 'static/js/site.js'), 'rb').read()).hexdigest()[:8]
WARN = []

# ------------------------------------------------------------------------------------------------ data
DATA = json.load(open(os.path.join(ROOT, 'data/products.json')))
MODELS = DATA['models']
ACCS = DATA['accessories']
PHOTOS = json.load(open(os.path.join(INPUT, 'photos.json')))
# pallets per stack (= per pallet place on a tautliner) per article number: tools/stapels.py -> data/stapels.json
STACKS = json.load(open(os.path.join(ROOT, 'data/stapels.json'), encoding='utf-8'))
# EUROPAL800RR and RECYPAL1210RR (update 43, Q-Pall via Noah 10 Nov 2026): stacked alternately, upside down into each
# other, 23 per stack, 2050 mm high, on a place of 1200 x 1000 / 1200 x 1200 (no longer 'on request')
ALT_STACK = {'EUROPAL800RR', 'RECYPAL1210RR'}
LOGO = json.load(open(os.path.join(ROOT, 'data/logo_paths.json')))
PPWR_FILES = {re.search(r'PG-(\d+)', f).group(1): os.path.basename(f) for f in glob.glob(os.path.join(INPUT, 'ppwr/*.pdf'))}

SIZE_ORDER = {s['key']: i for i, s in enumerate(SIZES)}
CLASS_ORDER = {'light': 0, 'medium': 1, 'heavy': 2}


def model_sort_key(m):
    sp_rank = {None: 0, 'display': 0, 'us': 1, 'pool': 2, 'h1': 3, 'cp1': 4, 'cp3': 4, 'cp6': 4, 'cp9': 4,
               'industrial': 5, 'hygienic': 6, 'cleanroom': 7}[m['special']]
    return (SIZE_ORDER[m['size']], CLASS_ORDER[m['class']], sp_rank, m['deck'] != 'open', m['antislip'],
            m['support']['type'] != 'feet', m['support']['n'], m['H'])


# update 45: draft and removed articles (site_config.DRAFT_SKUS / REMOVED_SKUS) leave before anything else; a family
# without articles disappears. The family's ranges and locations are recalculated from the articles that remain.
from site_config import DRAFT_SKUS, REMOVED_SKUS
HIDDEN_SKUS = DRAFT_SKUS | REMOVED_SKUS


def _refamily(fam):
    vs = fam['variants']
    def rng(k):
        vals = [v[k] for v in vs if v[k] is not None]
        return [min(vals), max(vals)] if vals else None
    if fam['primary'] not in {v['sku'] for v in vs}:
        fam['primary'] = sorted(vs, key=lambda v: (v['loc'] is None, v['price'] or 1e9, v['sku']))[0]['sku']
    priced = [v['price'] for v in vs if v['price']]
    fam.update({'static': rng('static'), 'dynamic': rng('dynamic'), 'racking': rng('racking'), 'weight': rng('weight'),
                'height': rng('H'), 'rackable': any(v['racking'] for v in vs),
                'price_from': min(priced) if priced else None, 'price_to': max(priced) if priced else None,
                'locations': [c for c in 'BRMNLV' if any(v['loc'] == c for v in vs)],
                'ppwr': sorted(set(pg for v in vs for pg in v['ppwr']))})


for _fam in MODELS:
    if any(v['sku'] in HIDDEN_SKUS for v in _fam['variants']):
        _fam['variants'] = [v for v in _fam['variants'] if v['sku'] not in HIDDEN_SKUS]
        if _fam['variants']:
            _refamily(_fam)
MODELS = [f for f in MODELS if f['variants']]
DATA['models'] = MODELS
assert not any(v['loc'] == 'C' for f in MODELS for v in f['variants']), 'an article with production location Chesterfield is on the site'

MODELS.sort(key=model_sort_key)
PC.assign_names(MODELS)          # names and slugs per model family (the family's own URL stays the same)

# ---- one product per article number (October 2026) --------------------------------------------------------------
# products.json groups the versions of a pallet (production location, height, ...) into one family. Every article
# number now gets its own page, datasheet and card. The family keeps its id and URL for the "anchor" article (the
# article whose height matches the family name, normally the cheapest one); the other articles get their own id
# (slug of the article number) and URL. Photos and drawings are shared within the family unless an article has its
# own set (input/photos/<item id>/, input/cad/<item id>.png).
FAMILIES = MODELS
FAMILY_ITEMS = {}


def _anchor(fam):
    vs = fam['variants']
    if len(vs) == 1:
        return vs[0]['sku']
    prim = next(v for v in vs if v['sku'] == fam['primary'])
    if prim['H'] == fam['H']:
        return prim['sku']
    same_h = [v for v in vs if v['H'] == fam['H']]
    priced = [v for v in same_h if v['price']]
    pick = min(priced, key=lambda v: v['price']) if priced else sorted(same_h, key=lambda v: (v['loc'] is None, v['sku']))[0]
    return pick['sku']


_FAMILY_IDS = {f['id'] for f in MODELS}


def _item_id(sku):
    i = slugify(sku)
    return i + '-art' if i in _FAMILY_IDS else i     # a plain base article next to its numbered versions


def _items(fam):
    anchor = _anchor(fam)
    order = sorted(fam['variants'], key=lambda v: (v['sku'] != anchor, v['loc'] is None, v['price'] or 1e9, v['sku']))
    out = []
    for i, v in enumerate(order):
        it = {k: val for k, val in fam.items() if k not in ('name', 'slug')}
        one = lambda x: [x, x] if x is not None else None
        it.update({
            'id': fam['id'] if v['sku'] == anchor else _item_id(v['sku']), 'sku': v['sku'], 'family': fam['id'],
            'is_anchor': v['sku'] == anchor, 'sib_order': i, 'variants': [v], 'primary': v['sku'],
            'L': v['L'] or fam['L'], 'W': v['W'] or fam['W'], 'H': v['H'] or fam['H'],
            'static': one(v['static']), 'dynamic': one(v['dynamic']), 'racking': one(v['racking']),
            'weight': one(v['weight']), 'height': one(v['H'] or fam['H']), 'rackable': bool(v['racking']),
            'price_from': v['price'], 'price_to': v['price'], 'moq_on_request': bool(v['price']) and v['moq_on_request'],
            'locations': [v['loc']] if v['loc'] else [], 'material': v.get('material') or fam.get('material'),
            'ppwr': v['ppwr'], 'pack': v['pack'], 'img': v['img'] or fam['img'],
            'title6': v.get('title6') or fam.get('title6'), 'seo6': v.get('seo6') or fam.get('seo6'),
            'seo_title_en': v.get('seo_title_en') or fam.get('seo_title_en'), 'seo_desc_en': v.get('seo_desc_en') or fam.get('seo_desc_en'),
        })
        out.append(it)
    for it in out:
        it['sku_title'] = len(out) > 1 and not it['is_anchor']     # meta title/description carry the article number
        for l in LANGS:
            if it['is_anchor']:
                name, slug = fam['name'][l], fam['slug'][l]
            else:
                q = ''
                if ', ' in fam['name'][l]:      # family name disambiguated with its racking load: same rule per article
                    q = f", {PC.RACK_WORD[l]} {fmt_int(it['racking'][1], l)} kg" if it['racking'] else ''
                name = PC.base_name(it, l) + q
                slug = slugify(name) + '-' + slugify(it['sku'])
            it.setdefault('name', {})[l] = name
            it.setdefault('slug', {})[l] = slug
    FAMILY_ITEMS[fam['id']] = out
    return out


MODELS = [it for fam in FAMILIES for it in _items(fam)]
for _l in LANGS:
    PC.assign_titles(MODELS, _l)


def _fix_names():
    """Update 28. (1) Sizes in the order of their category (760 x 1140, 600 x 800), also in the meta title and text, so a
    product never reads '1140 x 760' under the heading '760 x 1140 mm'. URLs (slugs) stay as they are.
    (2) Every product name (= H1) unique: articles that shared a name get what tells them apart: the colour (hygienic
    pallets), else the factory when that is unique within the group, else the article number."""
    import re as _re
    for m in MODELS:
        sz = SIZE_BY_KEY[m['size']]
        if sz['L'] == m['W'] and sz['W'] == m['L'] and m['L'] != m['W']:
            a, b = m['L'], m['W']
            m['disp_LW'] = (b, a)
            for l in LANGS:
                m['name'][l] = m['name'][l].replace(f"{a} x {b}", f"{b} x {a}", 1)
                m['meta_title'][l] = m['meta_title'][l].replace(f"{a}x{b}", f"{b}x{a}", 1).replace(f"{a} x {b}", f"{b} x {a}", 1)
                if m.get('seo6') and m['seo6'].get(l):
                    m['seo6'][l] = m['seo6'][l].replace(f"{a}x{b}", f"{b}x{a}").replace(f"{a} x {b}", f"{b} x {a}")
    groups = {}
    for m in MODELS:
        groups.setdefault(m['name']['nl'], []).append(m)
    for nm, ms in groups.items():
        if len(ms) < 2:
            continue
        cols = [SKU_COLOUR.get(m['sku']) for m in ms]
        locs = [m['locations'][0] if len(m['locations']) == 1 else None for m in ms]
        for m, c, lc in zip(ms, cols, locs):
            if all(cols) and len(set(cols)) == len(cols):
                suf = {l: T[l]['col_' + c] for l in LANGS}
            else:
                suf = {l: m['sku'] for l in LANGS}
            for l in LANGS:
                m['name'][l] = f"{m['name'][l]} – {suf[l]}"
            if suf['nl'] == m['sku']:
                # cards show the article number on its own line right below the title: the card title leaves that suffix
                # out (QA update 47); the H1, title tag and alt text keep the full unique name. Since update 53 the
                # factory is no longer a suffix (no production location per product on the site)
                m['card_name'] = {l: m['name'][l][:-(len(suf[l]) + 3)] for l in LANGS}
    for l in LANGS:      # safety net: anything still double gets its article number
        seen = {}
        for m in MODELS:
            seen.setdefault(m['name'][l], []).append(m)
        for nm, ms in seen.items():
            if len(ms) > 1:
                for m in ms:
                    if m['sku'] not in m['name'][l]:
                        m['name'][l] = f"{m['name'][l]} – {m['sku']}"


_fix_names()
FAMILY_BY_ID = {f['id']: f for f in FAMILIES}

# No prices on the site (SHOW_PRICES, update 34). Removed only now: the choice of the anchor article (URL) and the order
# of the versions were made with the price list above and must stay the same, with or without prices.
for _m in MODELS:
    _m['had_price'] = bool(_m['price_from'])          # keeps the 'recommended' order and the similar pallets as they were
    if not SHOW_PRICES:
        _m['price_from'] = _m['price_to'] = None
        _m['moq_on_request'] = False
        for _v in _m['variants']:
            _v['price'] = None
if not SHOW_PRICES:
    for _a in ACCS:
        _a['price'] = None


def is_click_runner(m):
    """Light pallets with 3 runners: the runners are click-on runners (Q-Pall, Daan Voets, 9 Nov 2026). The pallets are
    delivered nested like the 9-feet pallet, with the runners supplied loose alongside (update 38)."""
    return m['class'] == 'light' and m['support']['type'] == 'runners' and 'display' not in m['types']


for _m in MODELS:
    if is_click_runner(_m) and 'nestable' not in _m['types']:
        _m['types'] = _m['types'] + ['nestable']


def loc_label(code, lang, long=False):
    L = LOCATIONS[code]
    return f"{L['name']}, {COUNTRY[L['cc']][lang]}" if long else f"{L['name']} ({L['cc']})"


for m in MODELS:
    s = SIZE_BY_KEY[m['size']]
    m['size_label'] = f"{s['L']} x {s['W']} mm"
    m['is_new'] = m['antislip'] and m['class'] == 'medium'
    m['sku_txt'] = m['sku']   # cards and hero
    # photos: the article's own set, else the set of its family (one set of image files per family)
    m['photo_id'] = m['id'] if m['id'] in PHOTOS else m['family']
    ph = PHOTOS.get(m['photo_id'], {'n': 0, 'exact': False})
    m['n_photos'] = ph['n']
    # a set shows the article exactly only when it is the article's own set, or when the set lists the article in 'for'
    # (articles of one family can come from different moulds and look different; see input/photos.json)
    if 'for' in ph:
        m['img_exact'] = m['id'] in ph['for']
    else:
        m['img_exact'] = bool(ph.get('exact', m.get('img_exact'))) and m['photo_id'] == m['id']
    owner = m if m['photo_id'] == m['id'] else next(x for x in FAMILY_ITEMS[m['family']] if x['id'] == m['family'])
    m['photo_slug'] = owner['slug']['en']
    base = '/assets/img/pallets/' + m['photo_slug']
    m['img_url'] = base + '-640.webp'
    m['img_sm'] = base + '-320.webp'
    m['img_lg'] = base + '-1200.webp'
    m['gallery'] = [{'sm': f"{base}-{i}-320.webp", 'md': f"{base}-{i}-960.webp", 'lg': f"{base}-{i}-1600.webp"} for i in range(1, ph['n'] + 1)]
    m['url'] = {}
    m['txt'] = {}
    m['cmp'] = {}
    pid = 'p:' + m['id']
    PAGES[pid] = dict(id=pid, path={l: PAGES['size-' + m['size']]['path'][l] + m['slug'][l] + '/' for l in LANGS},
                      tpl='product', parent='size-' + m['size'], priority=0.8, model=m['id'])
    for l in LANGS:
        m['url'][l] = '/' + PAGES[pid]['path'][l]
MODEL_BY_ID = {m['id']: m for m in MODELS}
MAXV = {'static': max(m['static'][1] for m in MODELS), 'dynamic': max(m['dynamic'][1] for m in MODELS),
        'racking': max((m['racking'][1] for m in MODELS if m['racking']), default=1)}


def url(pid, lang, anchor=''):
    p = PAGES[pid]['path'][lang]
    return '/' + p + (('#' + anchor) if anchor else '')


def abs_url(path):
    return DOMAIN + path


def mcount(n, lang):
    return T[lang]['model_count_1'] if n == 1 else T[lang]['models_count'].format(n=n)


def short_rng(r, lang=None):
    if not r:
        return '–'
    # no-break space before "kg": a range that is too wide for its card column wraps after the dash, never before the unit
    return f"{fmt_int(r[0], lang)}\u00a0kg" if r[0] == r[1] else f"{fmt_int(r[0], lang)}–{fmt_int(r[1], lang)}\u00a0kg"


def datasheet_path(m, lang):
    return f"/downloads/datasheets/{lang}/q-pall-{m['id']}-{lang}.pdf"


for m in MODELS:
    _st = STACKS.get(m['sku'])
    m['stack'] = _st['stack'] if _st else None          # pallets per full stack (sold per stack only)
    m['stack_place'] = _st['place'] if _st else None    # L x W x H of the stack (pallet place), mm
    for l in LANGS:
        t = T[l]
        w = rng_txt(m['weight'], l, 'kg', dec=True)
        h = m['height']
        _L, _W = m.get('disp_LW') or (m['L'], m['W'])     # same order as the name (600 x 800, 760 x 1140), QA update 47
        dims = f"{_L} x {_W} x {h[0] if h[0] == h[1] else str(h[0]) + '–' + str(h[1])} mm"
        intro, desc_html = PC.seo_parts(m, l)
        if is_click_runner(m):     # delivered nested, runners loose (update 38)
            desc_html += f"<h3>{t['click_h']}</h3><p>{t['click_p']}</p>"
        locs = [loc_label(c, l) for c in m['locations']]
        cols = [SKU_COLOUR.get(v['sku']) for v in m['variants']]
        ucols = list(dict.fromkeys(cols))
        if all(cols):        # known colour(s): hygienic, cleanroom, H1 ...
            names = [t['col_' + c] for c in ucols]
            col_txt = names[0] if len(names) == 1 else ', '.join(names[:-1]) + f" {t['col_or']} " + names[-1] + f" ({t['col_per_version']})"
            col_txt = col_txt[:1].upper() + col_txt[1:]
        else:
            col_txt = t['colour_v']
        fcols = [SKU_COLOUR.get(x['sku']) for x in FAMILY_ITEMS[m['family']]]
        m['multicol'] = all(fcols) and len(set(fcols)) > 1      # colour column in the "similar versions" table
        X = {
            'static': rng_txt(m['static'], l), 'dynamic': rng_txt(m['dynamic'], l),
            'racking': rng_txt(m['racking'], l) if m['racking'] else None,
            'static_big': fmt_int(m['static'][1], l), 'dynamic_big': fmt_int(m['dynamic'][1], l),
            'racking_big': fmt_int(m['racking'][1], l) if m['racking'] else None,
            'static_short': short_rng(m['static'], l), 'dynamic_short': short_rng(m['dynamic'], l),
            'racking_short': short_rng(m['racking'], l) if m['racking'] else '–',
            'weight': w, 'dims': dims,
            'deck_label': PC.deck_words(m, l)[:1].upper() + PC.deck_words(m, l)[1:],
            'support': PC.support_words(m, l),
            'price': fmt_price(m['price_from'], l) if m['price_from'] else None,
            'sub': PC.subtitle(m, l, T), 'intro': intro, 'desc_html': Markup(desc_html),
            'loc_items': [{'label': loc_label(c, l), 'cc': LOCATIONS[c]['cc'].lower()} for c in m['locations']],
            'locs': locs, 'locs_txt': ', '.join(locs) if locs else t['loc_req'],
            'datasheet': datasheet_path(m, l), 'colour': col_txt,
            # sold per full stack only; the stack height is only given for pallets that are stacked, not nested
            'stack_per': t['stack_per'].format(n=fmt_int(m['stack'], l)) if m['stack'] else t['stack_req'],
            'stack_height': (t['stack_place'].format(d=' x '.join(str(x) for x in m['stack_place'])) if m['stack_place']
                             else None if not m['stack'] or 'nestable' in m['types'] else t['stack_height'].format(h=str(round(m['stack'] * h[1])))),
        }
        m['txt'][l] = X
        m['cmp'][l] = {'id': m['id'], 'name': m['name'][l], 'url': m['url'][l], 'img': m['img_sm'], 'dims': dims, 'weight': w,
                       'cls': m['class'].capitalize(), 'deck': X['deck_label'], 'base': X['support'],
                       'static': m['static'][1], 'dyn': m['dynamic'][1], 'rack': m['racking'][1] if m['racking'] else 0} | ({'price': (t['from_cap'] + ' ' + X['price']) if X['price'] else None} if SHOW_PRICES else {})

# ------------------------------------------------------------------------------------------------ content
CONTENT = {l: {} for l in LANGS}
for l in LANGS:
    for f in glob.glob(os.path.join(ROOT, 'content', l, '*.md')):
        raw = open(f, encoding='utf-8').read()
        _, fm, body = raw.split('---', 2)
        d = yaml.safe_load(fm)
        CONTENT[l][d['id']] = {'fm': d, 'body': body.strip()}
FALLBACK = []
for l in LANGS:
    for p in PAGES:
        if p.startswith('p:') or p in CONTENT[l]:
            continue
        src = CONTENT['en'].get(p) or CONTENT['nl'].get(p)
        if src:
            CONTENT[l][p] = src
            FALLBACK.append((l, p))
        else:
            WARN.append(f'MISSING CONTENT {l} {p}')


def listing_models(spec):
    out = MODELS
    if 'size' in spec:
        out = [m for m in out if m['size'] == spec['size']]
    if 'type' in spec:
        out = [m for m in out if spec['type'] in m['types']]
    if 'class' in spec:
        out = [m for m in out if m['class'] == spec['class']]
    return out


def min_price(ms):
    ps = [m['price_from'] for m in ms if m['price_from']]
    return min(ps) if ps else None


def meta_price(lang):
    """Lowest 'from' price of all pallets for titles and meta descriptions ([[from_price]] in the front matter):
    nl/it '€ 3,41', en '€3.41', de/fr/es '3,41 €'. Updates itself when data/prijzen.csv changes."""
    if not SHOW_PRICES:          # update 34: a text with a price placeholder while prices are off
        WARN.append(f'[[from_price]] used without prices ({lang})')
        return ''
    p = fmt_price(min_price(MODELS), lang).replace('\xa0', ' ')
    return p.replace('€ ', '€') if lang == 'en' else p


for _l in LANGS:
    for _c in CONTENT[_l].values():
        for _k in ('title', 'description'):
            if '[[from_price]]' in str(_c['fm'].get(_k, '')):
                _c['fm'][_k] = _c['fm'][_k].replace('[[from_price]]', meta_price(_l))


LINK_RE = re.compile(r'\(@([a-z0-9:\-]+)(?:#([a-z0-9\-]+))?\)')


def resolve_links(text, lang):
    def rep(mo):
        pid, anchor = mo.group(1), mo.group(2) or ''
        if pid.startswith('p:'):
            m = MODEL_BY_ID.get(pid[2:])
            if not m:
                WARN.append('bad product link ' + pid)
                return '(#)'
            return '(' + m['url'][lang] + ')'
        if pid not in PAGES:
            WARN.append(f'bad link @{pid}')
            return '(#)'
        return '(' + url(pid, lang, anchor) + ')'
    return LINK_RE.sub(rep, text)


def price_for(lang, **flt):
    ms = MODELS
    for k, v in flt.items():
        if k == 'size':
            ms = [m for m in ms if m['size'] == v]
        elif k == 'class':
            ms = [m for m in ms if m['class'] == v]
        elif k == 'type':
            ms = [m for m in ms if v in m['types']]
    p = min_price(ms)
    return fmt_price(p, lang) if p else (T[lang]['on_request'] if lang == 'de' else T[lang]['on_request'].lower())


def pricetable_html(lang):
    t = T[lang]
    rows = []
    head = f"<tr><th>{t['pricetable_size']}</th><th>Light</th><th>Medium</th><th>Heavy</th></tr>"
    for s in SIZES:
        cells = []
        for c in ('light', 'medium', 'heavy'):
            ms = [m for m in MODELS if m['size'] == s['key'] and m['class'] == c]
            p = min_price(ms)
            if p:
                cells.append(f'<td class="p"><a href="{url("size-" + s["key"], lang)}?cls={c}">{fmt_price(p, lang)}</a></td>')
            else:
                cells.append('<td class="na">–</td>')
        rows.append(f'<tr><td><a href="{url("size-" + s["key"], lang)}">{s["L"]} x {s["W"]} mm</a> <small class="muted">{t["size_nick"][s["key"]]}</small></td>' + ''.join(cells) + '</tr>')
    return (f'<div class="table-scroll"><table class="ptable"><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table></div>'
            f'<p class="small muted">{t["pricetable_note"]}</p>')


def sizetable_html(lang):
    t = T[lang]
    head = f"<tr><th>{t['sizetable_size']}</th><th>{t['sizetable_name']}</th><th>{t['sizetable_use']}</th><th>{t['sizetable_models']}</th></tr>"
    rows = []
    for s in SIZES:
        n = len([m for m in MODELS if m['size'] == s['key']])
        rows.append(f'<tr><td><a href="{url("size-" + s["key"], lang)}"><b>{s["L"]} x {s["W"]} mm</b></a></td><td>{t["size_nick"][s["key"]]}</td><td>{t["size_use"][s["key"]]}</td><td>{n}</td></tr>')
    return f'<div class="table-scroll"><table><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table></div>'


def ext_embed(src, title, lang, cls='dealer-frame'):
    t = T[lang]
    return (f'<div class="ext-embed {cls}" data-ext-src="{src}" data-ext-title="{escape(title)}">'
            f'<div class="ext-ph"><p>{t["ext_blocked"]}</p><button class="btn btn-navy btn-sm" type="button" data-ext-load>{t["ext_load"]}</button></div></div>')


def placeholders(text, lang, ctx):
    t = T[lang]

    def rep(mo):
        key = mo.group(1)
        if not SHOW_PRICES and (key in ('price_from', 'pricetable', 'pricelist') or key.startswith('price:')):
            WARN.append(f'price placeholder [[{key}]] used without prices ({lang})')     # update 34
            return ''
        if key == 'count':
            return str(ctx.get('count', ''))
        if key == 'price_from':
            p = ctx.get('price_from')
            return fmt_price(p, lang) if p else (t['on_request'] if lang == 'de' else t['on_request'].lower())
        if key == 'pricetable':
            return '\n\n' + pricetable_html(lang) + '\n\n'
        if key == 'sizetable':
            return '\n\n' + sizetable_html(lang) + '\n\n'
        if key == 'pricelist':
            return ''
        if key == 'dealermap':
            return ('\n\n' + ext_embed(COMPANY['dealer_locator'], t['dealer_frame'], lang) +
                    f'\n\n<p class="small"><a class="link-arrow" href="{COMPANY["dealer_locator"]}" target="_blank" rel="noopener">{t["dealer_open_new"]}'
                    '<svg class="ico" aria-hidden="true" focusable="false"><use href="#i-external"/></svg></a></p>\n\n')
        if key == 'termsdownload':
            if os.path.exists(os.path.join(ROOT, 'root', COMPANY['terms_pdf'].lstrip('/'))):
                return f'\n\n<a class="dl" href="{COMPANY["terms_pdf"]}" download><span class="dl-ico">PDF</span><span><b>{t["terms_pdf"]}</b><small>PDF</small></span></a>\n\n'
            return '\n\n' + t['terms_request'].format(email=f'<a href="mailto:{COMPANY["email"]}">{COMPANY["email"]}</a>') + '\n\n'
        if key == 'terms':
            return '\n\n' + terms_html() + '\n\n'
        if key == 'factories':
            return ', '.join(loc_label(c, lang, long=True) for c in FACTORIES)
        if key.startswith('loadill:'):          # illustration in the article on pallet loads (templates/_load_ill.html)
            svg = str(env.get_template('_load_ill.html').module.load_ill(key[8:], t['load_ill']))
            return '\n\n' + re.sub(r'\s*\n\s*', ' ', svg).strip() + '\n\n'      # one line: Markdown keeps the block as raw HTML
        if key.startswith('price:'):
            args = dict(kv.split('=') for kv in key[6:].split(','))
            return price_for(lang, **args)
        WARN.append('unknown placeholder ' + key)
        return ''
    return re.sub(r'\[\[([^\]]+)\]\]', rep, text)


# General terms and conditions: the official (filed) English text, data/terms-en.md, shown in full on every language version
TERMS_SRC = open(os.path.join(ROOT, 'data', 'terms-en.md'), encoding='utf-8').read().strip().split('\n')


def terms_articles():
    """[(number, title)] of the terms (table of contents)."""
    return [tuple(re.match(r'## (\d+)\. (.+)', l).groups()) for l in TERMS_SRC if l.startswith('## ')]


def terms_html():
    out, lst = [f'<div class="terms" lang="en" data-pagefind-ignore><p class="terms-head">{escape(TERMS_SRC[0])}</p>'], None
    def close():
        nonlocal lst
        if lst:
            out.append(f'</{lst}>')
            lst = None
    for l in TERMS_SRC[1:]:
        l = l.strip()
        if not l:
            close(); continue
        m = re.match(r'## (\d+)\. (.+)', l)
        if m:
            close()
            out.append(f'<h2 id="article-{m.group(1)}"><span>{m.group(1)}.</span> {escape(m.group(2))}</h2>')
            continue
        m = re.match(r'(\d+\.\d+) (.+)', l)
        if m:
            close()
            out.append(f'<p class="tc"><b>{m.group(1)}</b> {escape(m.group(2))}</p>')
            continue
        if l.startswith('- '):
            if lst != 'ul':
                close(); out.append('<ul>'); lst = 'ul'
            out.append(f'<li>{escape(l[2:])}</li>')
            continue
        m = re.match(r'([a-h])\. (.+)', l)
        if m:
            if lst != 'ol':
                close(); out.append('<ol class="tc-alpha">'); lst = 'ol'
            out.append(f'<li><b>{m.group(1)}.</b> {escape(m.group(2))}</li>')
            continue
        close()
        out.append(f'<p>{escape(l)}</p>')
    close()
    out.append('</div>')
    return '\n'.join(out)


MD = markdown.Markdown(extensions=['tables', 'sane_lists', 'attr_list'])


def md_html(text, lang, ctx=None, inline=False):
    text = placeholders(resolve_links(text or '', lang), lang, ctx or {})
    MD.reset()
    h = MD.convert(text)
    h = re.sub(r'<table>(.*?)</table>', r'<div class="table-scroll"><table>\1</table></div>', h, flags=re.S)
    h = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', h)
    if inline:
        h = re.sub(r'^<p>(.*)</p>$', r'\1', h.strip(), flags=re.S)
    return Markup(h)


def bold_filter(s):
    s = str(escape(s))
    return Markup(shy(re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)))


def plain(s):
    return re.sub(r'\*\*', '', str(s or '')).strip()


env = Environment(loader=FileSystemLoader(os.path.join(ROOT, 'templates')), autoescape=select_autoescape(['html', 'svg']),
                  trim_blocks=True, lstrip_blocks=True)
env.globals['site_noindex'] = NOINDEX_ALL
env.globals['show_prices'] = SHOW_PRICES      # update 34
env.globals['gtm_id'] = GTM_ID
env.globals['prod_hosts'] = ' '.join(PROD_HOSTS)
env.globals['hubspot'] = {'id': HUBSPOT_ID, 'region': HUBSPOT_REGION, 'hosts': ' '.join(HUBSPOT_HOSTS),
                         'forms': {k: v for k, v in HUBSPOT_FORMS.items() if v}}
env.filters['bold'] = bold_filter
# update 35: section titles without their own ** get the house style (light text, last word bold), e.g. "Veelgestelde **vragen**"
env.filters['boldlast'] = lambda s: s if (not s or '**' in s or ' ' not in s.strip()) else '{} **{}**'.format(*s.strip().rsplit(' ', 1))
# soft hyphens at the compound boundary for the few long words that sit in narrow boxes on a phone
SHY = {k: v.replace('|', '\u00ad') for k, v in {
    # first letter left off, so capitalised and lower-case forms both match
    'tellingbelasting': 'telling|belasting', 'egalbelastung': 'egal|belastung',
    'onformiteitsverklaring': 'onformiteits|verklaring', 'onformitätserklärung': 'onformitäts|erklärung',
    'oedingsmiddelenindustrie': 'oedings|middelen|industrie', 'ebensmittelindustrie': 'ebensmittel|industrie',
    'roductielocaties': 'roductie|locaties', 'roduktionsstandorte': 'roduktions|standorte',
    'erpackungseinheit': 'erpackungs|einheit', 'eschäftsbedingungen': 'eschäfts|bedingungen',
    'atenschutzerklärung': 'atenschutz|erklärung', 'atenschutz<strong>': 'atenschutz|<strong>', 'alettenaufsatzrahmen': 'aletten|aufsatz|rahmen'}.items()}
SHY_RE = re.compile('|'.join(SHY))


def shy(s):
    """Soft hyphens (search-safe: Pagefind ignores them) for the few long compounds that sit in narrow boxes."""
    out = SHY_RE.sub(lambda m: SHY[m.group(0)], str(s))
    return Markup(out) if isinstance(s, Markup) else out


env.filters['shy'] = shy


def grouplink(s):
    """'Onderdeel van de AVK Group' (homepage, about block): link the group name to the group's website."""
    s = str(escape(s))
    return Markup(re.sub(r'(AVK Group|groupe AVK)', lambda m: f'<a href="{COMPANY["group_url"]}" target="_blank" rel="noopener">{m.group(1)}</a>', s, count=1))


env.filters['grouplink'] = grouplink
env.filters['plain'] = plain
env.filters['kg'] = pass_context(lambda ctx, v: f"{fmt_int(v, ctx.get('lang'))} kg")
env.filters['fint'] = fmt_int


def logo_svg(white=False, cls='logo-svg'):
    dark = '#fff' if white else '#1F1E21'
    paths = ''.join(f'<path d="{d}"/>' for d in LOGO['pall'] + [LOGO['reg']] + LOGO['text'])
    return Markup(f'<svg class="{cls}" viewBox="{LOGO["vb"]}" role="img" aria-label="Q-Pall plastic pallets"><path fill="#F37321" d="{LOGO["q"]}"/><g fill="{dark}">{paths}</g></svg>')


# ------------------------------------------------------------------------------------------------ nav
SECTOR_IMG = {'chemical': None, 'food': None, 'pharma': None, 'beverage': '/assets/img/photos/beverage',
              'retail': '/assets/img/photos/retail', 'logistics': '/assets/img/photos/robot', 'pooling': '/assets/img/photos/pooling'}
# a photo for every sector (header mega menu and homepage tiles); chemie, voeding, farma: sector-<key> photos
NAV_SECTOR_IMG = {k: v or f'/assets/img/photos/sector-{k}' for k, v in SECTOR_IMG.items()}
# free-standing hero pallets (input/hero/<class>.png, see tools/hero_cutouts.py): size of the 960 px version
HERO_SIZE = {}
for _c in ('light', 'medium', 'heavy'):
    _f = os.path.join(INPUT, 'hero', _c + '.png')
    if os.path.exists(_f):
        from PIL import Image as _Im
        with _Im.open(_f) as _i:
            HERO_SIZE[_c] = (960, round(_i.height * 960 / _i.width))
ICON_TYPE = {'export': 'globe', 'nestable': 'nest', 'hygienic': 'drop', 'cp': 'flask', 'display': 'cart', 'block': 'box', 'antislip': 'grip'}
SIZE_IMG = {'600x400': 'qp6040mb4f', '600x800': 'qp6080hb6fr', '760x1140': 'qp76114lb3rr', '1100x1100': 'qp1111hb3rr', '1140x1140': 'qp1140mb3rr',
            '1200x800': 'qp1208mb3rr', '1200x1000': 'qp1210hb3rr-cd', '1200x1200': 'qp1212hb3rr', '1300x1100': 'qp1311hb3r-as'}
TYPE_IMG = {'export': 'qp1208lb9fr', 'nestable': 'qp1210lb9fr', 'hygienic': 'qp1208hb3rr-cd', 'cp': 'qp1140mb3r-pas-cp3', 'display': 'qp6080mb6fr',
            'block': 'qp1210hb6rr', 'antislip': 'qp1208mb3r-cd-ao', 'ultra': 'qp1210hp6r-ao'}
ACC_DEF = [('acc-collars', 'box'), ('acc-lids', 'layers'), ('acc-freezer', 'snow'), ('acc-drip', 'drop'), ('acc-runners', 'runner')]
ABOUT_DEF = [('about', 'users'), ('about-sustainability', 'leaf'), ('about-local', 'factory'), ('about-custom', 'tool'), ('about-team', 'users'), ('dealers', 'globe'), ('careers', 'users')]
KNOW_DEF = ['about-load', 'about-glossary']


def short_title(pid, lang):
    nl = T[lang]['nav_label']
    if pid in nl:
        return nl[pid]
    fm = CONTENT[lang][pid]['fm']
    return plain(fm.get('nav') or fm['h1'])


def build_nav(lang):
    t = T[lang]
    sizes = []
    for s in SIZES:
        ms = listing_models({'size': s['key']})
        mi = MODEL_BY_ID.get(SIZE_IMG[s['key']]) or ms[0]
        sizes.append({'key': s['key'], 'label': f"{s['L']} x {s['W']} mm", 'nick': t['size_nick'][s['key']], 'url': url('size-' + s['key'], lang),
                      'img': mi['img_sm'], 'alt': mi['name'][lang], 'count': len(ms), 'count_txt': mcount(len(ms), lang), 'price': min_price(ms)})
    types = []
    for ty in TYPES:
        ms = listing_models({'type': ty['key']})
        mi = MODEL_BY_ID.get(TYPE_IMG[ty['key']]) or ms[0]
        types.append({'key': ty['key'], 'label': t['type_name'][ty['key']], 'sub': t['type_sub'][ty['key']], 'url': url('type-' + ty['key'], lang),
                      'icon': ICON_TYPE[ty['key']], 'img': mi['img_sm'], 'alt': mi['name'][lang], 'new': ty.get('new'), 'count': len(ms), 'count_txt': mcount(len(ms), lang)})
    classes = []
    for i, c in enumerate(CLASSES):
        ms = listing_models({'class': c['key']})
        rk = [m['racking'][1] for m in ms if m['racking']]
        classes.append({'key': c['key'], 'name': c['name'], 'title': t['class_title'][c['key']], 'sub': t['class_sub'][c['key']],
                        'text': t['class_text'][c['key']], 'url': url('class-' + c['key'], lang), 'level': i + 1,
                        # from-price of the europallet 1200 x 800 in this class: the lowest price of a class was a small
                        # display pallet (medium 'from € 3,41'), which made medium look cheaper than light (update 28)
                        'count': len(ms), 'count_txt': mcount(len(ms), lang), 'price': min_price([m for m in ms if m['size'] == '1200x800']),
                        'price_txt': fmt_price(min_price([m for m in ms if m['size'] == '1200x800']), lang) if min_price([m for m in ms if m['size'] == '1200x800']) else None,
                        'price_lbl': t['size_nick']['1200x800'],
                        'static': fmt_int(max(m['static'][1] for m in ms), lang), 'dynamic': fmt_int(max(m['dynamic'][1] for m in ms), lang),
                        'racking': fmt_int(max(rk), lang) if rk else None,
                        'img_h': round(HERO_SIZE.get(c['key'], (960, 450))[1] * 640 / 960),
                        'n': {'static': max(m['static'][1] for m in ms), 'dynamic': max(m['dynamic'][1] for m in ms), 'racking': max(rk) if rk else 0}})
    for k in ('static', 'dynamic', 'racking'):          # bar length in the homepage class cards: share of the highest class value
        top = max(c['n'][k] for c in classes) or 1
        for c in classes:
            c.setdefault('pct', {})[k] = round(100 * c['n'][k] / top)
    acc = [{'id': pid, 'label': short_title(pid, lang), 'url': url(pid, lang), 'icon': ic, 'sub': t['nav_sub'][pid]} for pid, ic in ACC_DEF]
    acc.append({'id': 'used', 'label': short_title('used', lang), 'url': url('used', lang), 'icon': 'recycle', 'sub': t['nav_sub']['used']})
    about = [{'id': pid, 'label': short_title(pid, lang), 'url': url(pid, lang), 'icon': ic, 'sub': t['nav_sub'][pid]} for pid, ic in ABOUT_DEF]
    tiles = CONTENT[lang]['home']['fm']['sectors']['tiles']
    sectors = [{'key': s['key'], 'label': t['sector_name'][s['key']], 'url': url('sector-' + s['key'], lang), 'icon': s['icon'],
                'sub': t['sector_sub'][s['key']], 'img': NAV_SECTOR_IMG[s['key']], 'alt': t['sector_alt'][s['key']], 'big': tiles[s['key']].get('big')} for s in SECTORS]
    guides = [{'id': g, 'label': plain(CONTENT[lang][g]['fm'].get('nav') or CONTENT[lang][g]['fm']['h1']), 'url': url(g, lang)} for g in GUIDES]
    know_extra = [{'id': k, 'label': short_title(k, lang), 'url': url(k, lang), 'sub': t['nav_sub'][k]} for k in KNOW_DEF]
    um = MODEL_BY_ID[TYPE_IMG['ultra']]
    ultra = {'label': 'Ultra pallet', 'sub': t['type_sub']['ultra'], 'url': url('ultra', lang), 'img': um['img_sm'], 'alt': um['name'][lang]}
    return {'sizes': sizes, 'types': types, 'classes': classes, 'ultra': ultra, 'acc': acc, 'about': about, 'sectors': sectors, 'guides': guides,
            'know_extra': know_extra, 'factories': [{'code': c, 'name': LOCATIONS[c]['name'], 'cc': LOCATIONS[c]['cc'], 'country': COUNTRY[LOCATIONS[c]['cc']][lang]} for c in FACTORIES]}


NAV = {l: build_nav(l) for l in LANGS}
URLS = {l: {pid: url(pid, l) for pid in PAGES if not pid.startswith('p:')} for l in LANGS}

# ------------------------------------------------------------------------------------------------ JSON-LD
ORG_ID = DOMAIN + '/#organization'


def is_hyg(m):
    """Hygienic article (virgin plastic, own colour): hygienic, cleanroom and H1 pallets, plus every article on the
    hygienic type page (e.g. QPH1210HP3RR, which the PIM calls an industrial pallet)."""
    return m['special'] in ('hygienic', 'cleanroom', 'h1') or 'hygienic' in (m.get('types') or [])


# Hygienic, H1 and cleanroom pallets are made of virgin plastic. The shared product copy says
# "like all Q-Pall pallets it is made of recycled plastic"; correct that sentence for those models (update 28).
_HYG_MATERIAL = {
    'nl': ("Zoals al onze standaardpallets is hij gemaakt van bijna 100% gerecycled kunststof, neemt hij geen vocht op en heeft hij geen",
           "Anders dan onze standaardpallets is hij gemaakt van virgin (nieuw) kunststof in een eigen kleur. Hij neemt geen vocht op en heeft geen"),
    'en': ("Like all our standard pallets, it is made of nearly 100% recycled plastic, does not absorb moisture",
           "Unlike our standard pallets, it is made of virgin plastic in its own colour. It does not absorb moisture"),
    'de': ("Wie alle unsere Standardpaletten besteht sie aus fast 100 % recyceltem Kunststoff, nimmt keine Feuchtigkeit auf",
           "Anders als unsere Standardpaletten besteht sie aus Neuware in einer eigenen Farbe. Sie nimmt keine Feuchtigkeit auf"),
    'fr': ("Comme toutes nos palettes standard, elle est fabriquée en plastique recyclé à près de 100 %.",
           "Contrairement à nos palettes standard, elle est fabriquée en plastique vierge, dans une couleur propre."),
    'it': ("Come tutti i nostri pallet standard, è realizzato in plastica riciclata quasi al 100%, non assorbe umidità",
           "A differenza dei nostri pallet standard, è realizzato in plastica vergine in un colore proprio. Non assorbe umidità"),
    'es': ("Como todos nuestros palets estándar, está fabricado con plástico casi 100% reciclado, no absorbe humedad",
           "A diferencia de nuestros palets estándar, está fabricado con plástico virgen en un color propio. No absorbe humedad"),
}
for _m in MODELS:
    if is_hyg(_m) and _m.get('seo6'):
        _m['seo6'] = dict(_m['seo6'])
        for _l, (_old, _new) in _HYG_MATERIAL.items():
            if _m['seo6'].get(_l):
                if _old not in _m['seo6'][_l]:      # update 33: a hygienic page must never keep the recycled sentence
                    WARN.append(f"HYG material sentence not found: {_m['id']} {_l}")
                _m['seo6'][_l] = _m['seo6'][_l].replace(_old, _new)
            _tx = (_m.get('txt') or {}).get(_l)       # the page texts were already made from seo6
            if isinstance(_tx, dict):
                for _k, _v in list(_tx.items()):
                    if isinstance(_v, str) and _old in _v:
                        _tx[_k] = _v.replace(_old, _new)


# Organization (every page, via the same @id) and ContactPage texts per language, as supplied by iClicks (23-10-2026):
# data/schema-organization.json. Five production sites (update 45, decision Q-Pall/Noah 10-11-2026: Chesterfield
# is no longer on the site; between 27 Oct and 10 Nov 2026 it was listed as the sixth).
ORG_TXT = json.load(open(os.path.join(ROOT, 'data/schema-organization.json'), encoding='utf-8'))
ORG_SITES = [('Balk', 'NL'), ('Ribe', 'DK'), ('Marktoberdorf', 'DE'), ('Nantes', 'FR'), ('Lleida', 'ES')]   # five production sites (update 45)


def org_ld(lang):
    o = ORG_TXT[lang]
    hq = {'@type': 'PostalAddress', 'streetAddress': COMPANY['street'], 'postalCode': COMPANY['zip'], 'addressLocality': COMPANY['city'], 'addressCountry': 'NL'}
    days = ['https://schema.org/' + d for d in ('Monday', 'Tuesday', 'Wednesday', 'Thursday')]
    return {
        '@context': 'https://schema.org', '@type': 'Organization', '@id': ORG_ID, 'name': 'Q-Pall', 'legalName': COMPANY['legal'],
        'alternateName': 'Q-Pall Plastic Pallets', 'url': DOMAIN + '/',
        'logo': {'@type': 'ImageObject', 'url': DOMAIN + '/assets/img/brand/q-pall-logo.png'},
        'description': o['description'], 'slogan': 'Pallets with a purpose', 'foundingDate': str(COMPANY['founded']),
        'identifier': {'@type': 'PropertyValue', 'propertyID': 'KvK', 'value': COMPANY['coc']}, 'vatID': COMPANY['vat'],
        'address': hq, 'telephone': COMPANY['phone_href'], 'email': COMPANY['email'],
        'contactPoint': [{'@type': 'ContactPoint', 'contactType': 'sales', 'telephone': COMPANY['phone_href'], 'email': COMPANY['email'],
                          'areaServed': 'Europe', 'availableLanguage': ['nl', 'en', 'de', 'fr', 'it', 'es'],
                          'hoursAvailable': [{'@type': 'OpeningHoursSpecification', 'dayOfWeek': days, 'opens': '07:30', 'closes': '16:30'},
                                             {'@type': 'OpeningHoursSpecification', 'dayOfWeek': 'https://schema.org/Friday', 'opens': '07:30', 'closes': '15:30'}]}],
        'location': [{'@type': 'Place', 'name': o['locations'][0], 'address': hq}] +
                    [{'@type': 'Place', 'name': o['locations'][k + 1], 'address': {'@type': 'PostalAddress', 'addressLocality': city, 'addressCountry': cc}}
                     for k, (city, cc) in enumerate(ORG_SITES)],
        'areaServed': 'Europe', 'knowsAbout': o['knowsAbout'], 'award': COMPANY['award'],
        'parentOrganization': {'@type': 'Organization', 'name': COMPANY['group_name'], 'url': COMPANY['group_url']},
        'sameAs': [COMPANY['linkedin'], COMPANY['youtube']],
    }


def person_id(key):
    """Same @id in every language (iClicks author template): the Dutch team page + #first-last."""
    return abs_url(url('about-team', 'nl')) + '#' + key


def job_ld(pid, lang, fm, body):
    """JobPosting (Google for Jobs) for a vacancy page: front matter 'job' (title, posted, employment, hours, ...)."""
    j = fm['job']
    d = {'@context': 'https://schema.org', '@type': 'JobPosting', 'title': j['title'],
         'description': re.sub(r'<p class="btn-row">.*?</p>', '', str(body), flags=re.S), 'datePosted': j['posted'], 'employmentType': j.get('employment', ['FULL_TIME']),
         'hiringOrganization': {'@type': 'Organization', '@id': ORG_ID, 'name': 'Q-Pall', 'sameAs': DOMAIN + '/',
                                'logo': DOMAIN + '/assets/img/brand/q-pall-logo.png'},
         'jobLocation': {'@type': 'Place', 'address': {'@type': 'PostalAddress', 'streetAddress': COMPANY['street'],
                         'postalCode': COMPANY['zip'], 'addressLocality': COMPANY['city'], 'addressRegion': 'Noord-Brabant',
                         'addressCountry': COMPANY['cc']}},
         'directApply': bool(j.get('direct_apply')), 'url': abs_url(url(pid, lang)), 'inLanguage': lang}
    for k_src, k_ld in (('valid_through', 'validThrough'), ('hours', 'workHours'), ('education', 'educationRequirements'),
                        ('qualifications', 'qualifications'), ('skills', 'skills'), ('industry', 'industry')):
        if j.get(k_src):
            d[k_ld] = j[k_src]
    return d


def person_ld(key, lang, context=True):
    p = TEAM_BY[key]
    d = {'@type': 'Person', '@id': person_id(key), 'name': p['name'], 'jobTitle': p['role'][lang], 'description': p['bio'][lang],
         'image': abs_url(p['photo']), 'url': abs_url(url('about-team', lang)), 'worksFor': {'@id': ORG_ID}, 'knowsAbout': p['knows'][lang]}
    if p.get('linkedin'):
        d['sameAs'] = [p['linkedin']]
    return {'@context': 'https://schema.org', **d} if context else d


def team_ctx(lang):
    return [{'key': p['key'], 'name': p['name'], 'photo': p['photo'], 'linkedin': p.get('linkedin'), 'role': p['role'][lang], 'bio': p['bio'][lang],
             'url': url('about-team', lang) + '#' + p['key']} for p in TEAM]


def author_of(pid, fm, lang):
    """Team member who wrote this article (AUTHORS, or a TEAM name in the front matter), else None."""
    key = AUTHORS.get(pid) or (TEAM_BY_NAME[fm['author']]['key'] if fm.get('author') in TEAM_BY_NAME else None)
    return next((p for p in team_ctx(lang) if p['key'] == key), None) if key else None


def contactpage_ld(lang):
    o = ORG_TXT[lang]['contact']
    u = abs_url(url('contact', lang))
    return {'@context': 'https://schema.org', '@type': 'ContactPage', '@id': u + '#webpage', 'url': u, 'name': o['name'], 'description': o['description'],
            'inLanguage': lang, 'isPartOf': {'@id': DOMAIN + '/#website'}, 'about': {'@id': ORG_ID}, 'mainEntity': {'@id': ORG_ID}}


def website_ld(lang):
    return {'@context': 'https://schema.org', '@type': 'WebSite', '@id': DOMAIN + '/#website', 'url': DOMAIN + '/', 'name': 'Q-Pall',
            'inLanguage': [HTML_LANG[l] for l in LANGS], 'publisher': {'@id': ORG_ID}}


def crumbs_ld(items):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList',
            'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': c['label'], 'item': abs_url(c['url'])} for i, c in enumerate(items)]}


def faq_ld(items):
    return {'@context': 'https://schema.org', '@type': 'FAQPage',
            'mainEntity': [{'@type': 'Question', 'name': f['q'], 'acceptedAnswer': {'@type': 'Answer', 'text': re.sub(r'<[^>]+>', '', str(f['a_html'])).strip()}} for f in items]}


def itemlist_ld(models, lang, name):
    return {'@context': 'https://schema.org', '@type': 'ItemList', 'name': name, 'numberOfItems': len(models),
            'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': abs_url(m['url'][lang]), 'name': m['name'][lang]} for i, m in enumerate(models)]}


def mat_label(m, t):
    """Material of a standard (recycled) pallet in the page language; light pallets also contain LDPE (update 33)."""
    return t['mat_recycled_ldpe'] if 'LDPE' in (m.get('material') or '') else t['mat_recycled']


def product_ld(m, lang):
    t = T[lang]
    X = m['txt'][lang]
    props = [
        {'@type': 'PropertyValue', 'name': t['static_l'], 'value': m['static'][1], 'unitCode': 'KGM', 'unitText': 'kg'},
        {'@type': 'PropertyValue', 'name': t['dynamic_l'], 'value': m['dynamic'][1], 'unitCode': 'KGM', 'unitText': 'kg'},
    ]
    if m['racking']:
        props.append({'@type': 'PropertyValue', 'name': t['racking_l'], 'value': m['racking'][1], 'unitCode': 'KGM', 'unitText': 'kg'})
    props += [{'@type': 'PropertyValue', 'name': t['deck'], 'value': X['deck_label']},
              {'@type': 'PropertyValue', 'name': t['bottom'], 'value': X['support']},
              {'@type': 'PropertyValue', 'name': t['class'], 'value': m['class'].capitalize()}]
    hyg = is_hyg(m)
    d = {
        '@context': 'https://schema.org', '@type': 'Product', '@id': abs_url(m['url'][lang]) + '#product',
        'name': m['name'][lang], 'description': X['intro'] or m['name'][lang],
        'image': [abs_url(g['lg']) for g in m['gallery']] or [abs_url(m['img_url'])],
        'sku': m['primary'], 'mpn': m['primary'], 'brand': {'@type': 'Brand', 'name': 'Q-Pall'}, 'manufacturer': {'@id': ORG_ID},
        'category': T[lang]['nav_pallets'] + ' > ' + m['size_label'],
        'material': t['mat_hyg'] if hyg else mat_label(m, t),
        'depth': {'@type': 'QuantitativeValue', 'value': m['L'], 'unitCode': 'MMT'},
        'width': {'@type': 'QuantitativeValue', 'value': m['W'], 'unitCode': 'MMT'},
        'height': {'@type': 'QuantitativeValue', 'value': m['H'], 'unitCode': 'MMT'},
        'weight': {'@type': 'QuantitativeValue', 'value': m['weight'][0], 'unitCode': 'KGM'},
        'additionalProperty': props,
    }
    if m['price_from']:
        d['offers'] = {
            '@type': 'Offer', 'url': abs_url(m['url'][lang]), 'priceCurrency': 'EUR', 'price': f"{m['price_from']:.2f}",
            'priceValidUntil': PRICE_VALID_UNTIL, 'itemCondition': 'https://schema.org/NewCondition', 'seller': {'@id': ORG_ID},
            'availability': 'https://schema.org/InStock',
            'priceSpecification': {'@type': 'UnitPriceSpecification', 'price': f"{m['price_from']:.2f}", 'priceCurrency': 'EUR',
                                   'valueAddedTaxIncluded': False, 'referenceQuantity': {'@type': 'QuantitativeValue', 'value': 1, 'unitCode': 'C62'}},
        }
    return d


ULTRA_SKU = 'QP1210H'          # article group of the Ultra pallet (QP1210HP3R-AO and QP1210HP6R-AO); quote link ?sku=QP1210H
ULTRA_MODELS = ['qp1210hp3r-ao', 'qp1210hp6r-ao']


def ultra_ld(lang, fm):
    """Product schema for the Ultra pallet page (both versions, 3 and 6 runners, as one product)."""
    t = T[lang]
    ms = [MODEL_BY_ID[i] for i in ULTRA_MODELS]
    m = ms[0]
    u = abs_url(url('ultra', lang))
    props = [{'@type': 'PropertyValue', 'name': t['static_l'], 'value': m['static'][1], 'unitCode': 'KGM', 'unitText': 'kg'},
             {'@type': 'PropertyValue', 'name': t['dynamic_l'], 'value': m['dynamic'][1], 'unitCode': 'KGM', 'unitText': 'kg'},
             {'@type': 'PropertyValue', 'name': t['racking_l'], 'minValue': min(x['racking'][1] for x in ms), 'maxValue': max(x['racking'][1] for x in ms),
              'unitCode': 'KGM', 'unitText': 'kg'},
             {'@type': 'PropertyValue', 'name': t['class'], 'value': m['class'].capitalize()},
             {'@type': 'PropertyValue', 'name': t['f_antislip'], 'value': t['yes']}]
    d = {'@context': 'https://schema.org', '@type': 'Product', '@id': u + '#product', 'name': 'Ultra pallet', 'description': fm['description'],
         'url': u, 'image': [abs_url(x['gallery'][0]['lg'] if x['gallery'] else x['img_url']) for x in ms],
         'sku': ULTRA_SKU, 'mpn': ULTRA_SKU, 'brand': {'@type': 'Brand', 'name': 'Q-Pall'}, 'manufacturer': {'@id': ORG_ID},
         'category': t['nav_pallets'] + ' > ' + m['size_label'], 'material': mat_label(m, t),
         'depth': {'@type': 'QuantitativeValue', 'value': m['L'], 'unitCode': 'MMT'},
         'width': {'@type': 'QuantitativeValue', 'value': m['W'], 'unitCode': 'MMT'},
         'height': {'@type': 'QuantitativeValue', 'value': m['H'], 'unitCode': 'MMT'},
         'additionalProperty': props,
         'isRelatedTo': [{'@id': abs_url(x['url'][lang]) + '#product'} for x in ms]}
    prices = [x['price_from'] for x in ms if x['price_from']]
    if prices:
        d['offers'] = {'@type': 'AggregateOffer', 'url': u, 'priceCurrency': 'EUR', 'lowPrice': f"{min(prices):.2f}", 'highPrice': f"{max(prices):.2f}",
                       'offerCount': len(prices), 'itemCondition': 'https://schema.org/NewCondition', 'availability': 'https://schema.org/InStock',
                       'seller': {'@id': ORG_ID}}
    return d


# ------------------------------------------------------------------------------------------------ helpers
def crumbs_for(pid, lang):
    t = T[lang]
    items = []
    cur = pid
    while cur:
        p = PAGES[cur]
        if cur == 'home':
            items.append({'label': t['breadcrumb_home'], 'url': url('home', lang)})
        elif cur.startswith('p:'):
            items.append({'label': MODEL_BY_ID[p['model']]['name'][lang], 'url': '/' + p['path'][lang]})
        else:
            fm = CONTENT[lang][cur]['fm']
            lab = fm.get('crumb') or t['nav_label'].get(cur) or plain(fm['h1'])
            if cur.startswith('type-'):
                lab = t['type_name'][cur[5:]]
            if cur.startswith('class-'):
                lab = t['class_title'][cur[6:]]
            if cur.startswith('sector-'):
                lab = t['sector_name'][cur[7:]]
            if cur.startswith('size-'):
                s = SIZE_BY_KEY[cur[5:]]
                lab = f"{s['L']} x {s['W']} mm"
            items.append({'label': lab, 'url': url(cur, lang)})
        cur = p['parent']
    return list(reversed(items))


def faq_items(fm, lang, ctx=None):
    return [{'q': f['q'], 'a_html': md_html(f['a'], lang, ctx)} for f in fm.get('faq', []) or []]


def alternates(pid):
    out = [{'hreflang': HTML_LANG[l], 'href': abs_url('/' + PAGES[pid]['path'][l])} for l in LANGS]
    out.append({'hreflang': 'x-default', 'href': abs_url('/' + PAGES[pid]['path'][X_DEFAULT])})
    return out


OG_DIR = os.path.join(ROOT, 'data/og')


def og_for(pid, lang):
    """Share image of a page (tools/og.py makes one per page and language; product pages: p-<model id>)."""
    key = 'p-' + pid[2:] if pid.startswith('p:') else pid
    if not os.path.exists(os.path.join(OG_DIR, lang, key + '.jpg')) and pid.startswith('p:') and pid[2:] in MODEL_BY_ID:
        key = 'p-' + MODEL_BY_ID[pid[2:]]['family']          # an article without its own image: the image of its family
    if not os.path.exists(os.path.join(OG_DIR, lang, key + '.jpg')):
        key = 'home'
    return f'/assets/og/{lang}/{key}.jpg'


JS_I18N = {l: {k: T[l][k] for k in ('results', 'result', 'search_none', 'search_loading', 'search_g_cat', 'search_g_prod', 'search_g_page', 'compare_max', 'on_request', 'close', 'filter_reset',
                                     'f_any', 'from_cap', 'compare_title', 'show_more', 'tr_unavailable', 'tr_open_new', 'tr_loading')}
           | {'cmp_rows': {'name': T[l]['model'], 'dims': T[l]['dims'], 'weight': T[l]['weight'], 'cls': T[l]['class'], 'deck': T[l]['deck'],
                           'base': T[l]['bottom'], 'static': T[l]['static_l'], 'dyn': T[l]['dynamic_l'], 'rack': T[l]['racking_l']} | ({'price': T[l]['price']} if SHOW_PRICES else {})}
           for l in LANGS}


_FR_COLON = re.compile(r'(?<=[^\s\d:/])[ \u00a0\u202f]?:(?=\s|$)')


def fr_colon(txt):
    """French typography (update 50): a non-breaking space before the colon (« Prix : sur devis »)."""
    return _FR_COLON.sub('\u00a0:', txt) if txt else txt


def _first_sentence(txt):
    """Card text on the accessories overview: the first sentence of the lead, whole (it was cut off mid-sentence, update 50)."""
    return re.split(r'(?<=[.!?])\s+', (txt or '').strip())[0]


def base_ctx(pid, lang, meta_title, meta_desc, section=None, noindex=False, og_image=None, jsonld=None, preload=None, tpl='page'):
    t = T[lang]
    if lang == 'fr':
        meta_title, meta_desc = fr_colon(meta_title), fr_colon(meta_desc)
    return {
        'lang': lang, 'html_lang': HTML_LANG[lang], 't': t, 'company': COMPANY, 'team': team_ctx(lang), 'urls': URLS[lang], 'nav': NAV[lang], 'page_id': pid,
        'section': section, 'tpl': tpl, 'logo_svg': logo_svg(), 'logo_white_svg': logo_svg(True), 'v': VERSION, 'year': BUILD_DATE[:4],
        'langs': [{'code': l, 'name': LANG_NAME[l], 'region': LANG_REGION[l], 'url': '/' + PAGES[pid]['path'][l], 'current': l == lang} for l in LANGS],
        'catalog': {'url': '/' + CATALOG_FILES[lang], 'meta': t['catalog_meta'].format(size=catalog_size(lang))},
        'js_i18n': JS_I18N[lang],
        'meta': {'title': meta_title, 'description': meta_desc, 'canonical': abs_url('/' + PAGES[pid]['path'][lang]),
                 'alternates': alternates(pid), 'noindex': noindex, 'og_image': abs_url(og_image or og_for(pid, lang)),
                 'og_locale': LOCALE[lang], 'og_locale_alt': [LOCALE[l] for l in LANGS if l != lang], 'preload_img': preload,
                 'og_alt': re.sub(r'\s+[–|-]\s+Q-Pall$', '', meta_title)},
        'jsonld': [org_ld(lang)] + [x for x in (jsonld or []) if x.get('@type') != 'Organization'],   # Organization on every page (iClicks)
    }


def section_of(pid):
    if pid.startswith('p:') or pid in ('pallets', 'ultra') or pid.split('-')[0] in ('size', 'type', 'class'):
        return 'pallets'
    if pid.startswith('acc') or pid == 'used':
        return 'pallets'
    if pid.startswith('sector'):
        return 'sectors'
    if pid.startswith('about-load') or pid.startswith('about-glossary') or pid.startswith('guide') or pid == 'knowledge':
        return 'knowledge'
    if pid.startswith('about') or pid in ('dealers', 'careers') or pid.startswith('job-'):
        return 'about'
    if pid == 'contact':
        return 'contact'
    if pid == 'news' or pid in NEWS_ITEMS:
        return 'news'
    return None


_TYPO_SKIP = {'script', 'style', 'textarea', 'option', 'select', 'datalist', 'svg', 'pre', 'code', 'title', 'head'}
_TYPO_TAG = re.compile(r'(<[^>]+>)')
_TYPO_NAME = re.compile(r'<\s*(/?)\s*([a-zA-Z][\w:-]*)')
_TYPO_RULES = [
    (re.compile(r'(\d) ([x×]) (?=\d)'), '\\1\u00a0\\2\u00a0'),                                  # 1200 x 800
    (re.compile(r'(\d) (?=(?:mm|cm|km|kg|MB|KB|°C|m|t|mln|millions?|Mio\.?|milioni|millones|uur|min)\b)'), '\\1\u00a0'),   # 800 mm, 9 MB, 4 mln
    (re.compile(r'\b(Q-Pall|Q-Used|Pays-Bas)\b'), '<span class="nw">\\1</span>'),                  # never "Q-" / "Pall"
]


def typo(htmlstr):
    """QA round (update 47): body text never breaks inside a size (1200 x 800), between a number and its unit, or at the
    hyphen of the brand name. Text only: tags, attributes, scripts, SVG, form options and the head stay untouched."""
    out, skip = [], []
    is_fr = '<html lang="fr' in htmlstr[:300]
    for part in _TYPO_TAG.split(htmlstr):
        if part.startswith('<'):
            m = _TYPO_NAME.match(part)
            if m and not part.startswith('<!'):
                name = m.group(2).lower()
                if name in _TYPO_SKIP:
                    if m.group(1):
                        if name in skip:
                            while skip and skip.pop() != name:
                                pass
                    elif not part.rstrip().endswith('/>'):
                        skip.append(name)
            out.append(part)
        elif skip or not part.strip():
            out.append(part)
        else:
            for rx, rep in _TYPO_RULES:
                part = rx.sub(rep, part)
            if is_fr:
                part = fr_colon(part)
            out.append(part)
    return ''.join(out)


def write(path, htmlstr):
    full = os.path.join(OUT, path)
    if path.endswith('/') or path == '':
        full = os.path.join(full, 'index.html')
    os.makedirs(os.path.dirname(full), exist_ok=True)
    htmlstr = re.sub(r'\n\s*\n+', '\n', htmlstr)
    # wide tables scroll sideways: make the scroll box reachable by keyboard and name it (update 33, accessibility)
    _m = re.search(r'<html lang="([a-z]{2})', htmlstr)
    _lab = T[_m.group(1)]['tbl_scroll'] if _m and _m.group(1) in T else 'Tabel'
    htmlstr = htmlstr.replace('<div class="table-scroll">', f'<div class="table-scroll" tabindex="0" role="region" aria-label="{_lab}">')
    if full.endswith('.html'):
        htmlstr = typo(htmlstr)
    open(full, 'w', encoding='utf-8').write(htmlstr)


def check_meta(pid, lang, title, desc):
    if len(title) > 65:
        WARN.append(f'title>65 {lang} {pid} ({len(title)}): {title}')
    if not (110 <= len(desc) <= 160):
        WARN.append(f'desc len {len(desc)} {lang} {pid}: {desc}')


def page_obj(pid, lang, ctx=None):
    c = CONTENT[lang][pid]
    fm = c['fm']
    return {'fm': fm, 'eyebrow': fm.get('eyebrow'), 'h1': placeholders(fm.get('h1') or fm.get('hero', {}).get('h1', ''), lang, ctx or {}),
            'tagline': fm.get('tagline'), 'lead': fm.get('lead'), 'lead_html': md_html(fm.get('lead', ''), lang, ctx, inline=True),
            'faq': faq_items(fm, lang, ctx)}


# ------------------------------------------------------------------------------------------------ renderers
def facets_for(ms, lang):
    t = T[lang]
    f = {}
    sizes = [s for s in SIZES if any(m['size'] == s['key'] for m in ms)]
    f['size'] = [{'v': s['key'], 'l': f"{s['L']} x {s['W']}"} for s in sizes]
    f['class'] = [{'v': c, 'l': c.capitalize()} for c in ('light', 'medium', 'heavy') if any(m['class'] == c for m in ms)]
    f['deck'] = [{'v': d, 'l': t['f_open'] if d == 'open' else t['f_closed']} for d in ('open', 'closed') if any(m['deck'] == d for m in ms)]
    f['base'] = [{'v': b, 'l': t['f_feet'] if b == 'feet' else t['f_runners']} for b in ('feet', 'runners') if any(m['support']['type'] == b for m in ms)]
    feats = []
    for key, lab, test in [('nest', t['f_nest'], lambda m: 'nestable' in m['types']), ('rack', t['f_rack'], lambda m: m['rackable']),
                           ('export', t['f_export'], lambda m: 'export' in m['types']), ('hyg', t['f_hyg'], lambda m: 'hygienic' in m['types']),
                           ('antislip', t['f_antislip'], lambda m: m['antislip']), ('price', t['f_price'], lambda m: bool(m['price_from']))]:
        n = sum(1 for m in ms if test(m))
        if 0 < n < len(ms):
            feats.append({'v': key, 'l': lab})
    f['f'] = feats
    smax = max(m['static'][1] for m in ms)
    f['static'] = [v for v in (1000, 2500, 5000, 6000, 7500) if v <= smax]
    if len(f['static']) < 2:
        f['static'] = []
    dmax = max(m['dynamic'][1] for m in ms)
    f['dyn'] = [v for v in (500, 1000, 1250, 1500, 1750, 2000) if v <= dmax]
    if len(f['dyn']) < 2:
        f['dyn'] = []
    rmax = max((m['racking'][1] for m in ms if m['racking']), default=0)
    f['rack'] = [v for v in (250, 500, 750, 1000, 1250, 1500, 1750, 2000) if v <= rmax] if rmax else []
    if len(f['rack']) < 2:
        f['rack'] = []
    return f


def rec_sort_key(m):
    """'Recommended' order of the product overviews (update 28): what most visitors come for first.
    Standard europallets 1200 x 800 (light, medium, heavy), then standard 1200 x 1000, then the special versions of
    those two sizes (hygienic, H1, CP, Ultra, US), then the other sizes from small to large."""
    std = m['special'] in (None, 'industrial')
    if m['size'] == '1200x800':
        tier = 0 if std else 2
    elif m['size'] == '1200x1000':
        tier = 1 if std else 3
    else:
        tier = 4 + SIZE_ORDER[m['size']]
    # One card per family first (the anchor article); the other factories/versions of that pallet follow after the
    # whole range, so the first rows show the choice between light, medium and heavy instead of six near-identical cards.
    return (0 if m.get('is_anchor', True) else 1, tier, CLASS_ORDER[m['class']]) + model_sort_key(m)[2:] + (m.get('sib_order', 0),)


def render_listing(pid, lang):
    t = T[lang]
    spec = PAGES[pid]['listing']
    ms = sorted(listing_models(spec), key=rec_sort_key)
    p = min_price(ms)
    ctx = {'count': len(ms), 'price_from': p}
    page = page_obj(pid, lang, ctx)
    fm = page['fm']
    crumbs = crumbs_for(pid, lang)
    nav = NAV[lang]
    rk = [m['racking'][1] for m in ms if m['racking']]
    stats = [(t['lh_models'], fmt_int(len(ms), lang)),   # no price in the header card (Noah, Oct 2026)
             (t['static_l'] + ' max.', f"{fmt_int(max(m['static'][1] for m in ms), lang)} kg"),
             # nothing in this listing goes in a rack (nestable, 600 x 400): show the dynamic load instead of a dash (QA update 47)
             (t['racking_l'] + ' max.', f"{fmt_int(max(rk), lang)} kg") if rk else
             (t['dynamic_l'] + ' max.', f"{fmt_int(max(m['dynamic'][1] for m in ms), lang)} kg")]
    groups = [
        {'key': 'size', 'title': t['mm_by_size'], 'links': [{'label': s['label'].replace(' mm', ''), 'url': s['url'], 'current': pid == 'size-' + s['key']} for s in nav['sizes']]},
        {'key': 'type', 'title': t['mm_types'], 'links': [{'label': ty['label'], 'url': ty['url'], 'current': pid == 'type-' + ty['key']} for ty in nav['types']]},
        {'key': 'class', 'title': t['mm_by_class'], 'links': [{'label': c['name'], 'url': c['url'], 'current': pid == 'class-' + c['key'], 'cls': c['key']} for c in nav['classes']]},
    ]
    body = md_html(CONTENT[lang][pid]['body'], lang, ctx)
    jl = [crumbs_ld(crumbs), {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': plain(page['h1']), 'url': abs_url(url(pid, lang)),
                             'description': fm['description'], 'inLanguage': HTML_LANG[lang], 'isPartOf': {'@id': DOMAIN + '/#website'}, 'publisher': {'@id': ORG_ID}},
          itemlist_ld(ms, lang, plain(page['h1']))]
    if page['faq']:
        jl.append(faq_ld(page['faq']))
    check_meta(pid, lang, fm['title'], fm['description'])
    ctx2 = base_ctx(pid, lang, fm['title'], fm['description'], section='pallets', jsonld=jl, tpl='listing')
    ctx2.update(page=page, crumbs=crumbs, models=ms, hero_stats=stats, groups=groups, body=body, facets=facets_for(ms, lang),
                news_rel=related_news(pid, lang), is_main=(pid == 'pallets'), listing_key=next(iter(spec), None), listing_val=next(iter(spec.values()), None),
                qcolor={'class-light': 'groen', 'class-medium': 'blauw', 'class-heavy': 'paars'}.get(pid, 'oranje'))
    return env.get_template('listing.html').render(**ctx2)


RUNNER_SIZES = {'1200x800', '1200x1000', '760x1140', '1100x1100', '1140x1140', '1200x1200'}
COLLAR_SIZES = {'600x800', '1200x800', '1200x1000', '1200x1200'}


def spec_groups(m, lang, price=True):
    """Spec tables per group: [(group title, [(label, value), ...]), ...] (product page and datasheet)."""
    t = T[lang]
    X = m['txt'][lang]
    hyg = is_hyg(m)
    g1 = [(t['art_nr'], m['variants'][0]['sku'])] if len(m['variants']) == 1 else []
    g1 += [(t['length'], f"{m['L']} mm"), (t['width'], f"{m['W']} mm"),
          (t['height'], f"{m['height'][0]} mm" if m['height'][0] == m['height'][1] else f"{m['height'][0]}–{m['height'][1]} mm"),
          (t['weight'], X['weight'])]
    g2 = [(t['deck'], X['deck_label']), (t['bottom'], X['support']), (t['class'], m['class'].capitalize()),
          (t['nestable'], t['yes'] if 'nestable' in m['types'] else t['no'])]
    if m['antislip']:
        g2.append((t['f_antislip'], t['yes']))
    mat = t['mat_hyg'] if hyg else mat_label(m, t)
    g2 += [(t['material'], mat), (t['colour'], X['colour']), (t['ispm'], t['ispm_v'])]
    g3 = [(t['static_l'], X['static']), (t['dynamic_l'], X['dynamic']), (t['racking_l'], X['racking'] or t['not_rackable'])]
    g4 = []      # no production location per product any more (Q-Pall, 12 Nov 2026, update 53)
    if is_click_runner(m):
        g4.append((t['click_spec_l'], t['click_spec_v']))
    if m['sku'] in ALT_STACK:
        g4.append((t['alt_stack_l'], t['alt_stack_v']))
    if m.get('pack'):
        g4.append((t['packed'], f"{m['pack']} {t['pcs']}"))
    if m['ppwr']:
        g4.append((t['ppwr'], t['ppwr_v']))
    if price:
        g4.append((t['price'], (t['from_cap'] + ' ' + X['price'] + ' ' + t['excl_vat']) if X['price'] else t['on_request']))
    return [(h, g) for h, g in zip([t['group_dims'], t['group_build'], t['group_load'], t['group_delivery']], [g1, g2, g3, g4]) if g]


def variant_rows(m, lang):
    """The articles of the same pallet family (this one first): product page section "similar versions" and datasheet."""
    t = T[lang]
    rows = []
    for x in FAMILY_ITEMS[m['family']]:
        v = x['variants'][0]
        rows.append({'sku': v['sku'], 'id': x['id'], 'url': x['url'][lang], 'abs_url': abs_url(x['url'][lang]), 'current': x['id'] == m['id'],
                     'dims': ' x '.join(str(n) for n in (x.get('disp_LW') or (v['L'], v['W']))) + f" x {v['H']}", 'weight': f"{fmt_dec(v['weight'], lang)} kg",
                     'static': f"{fmt_int(v['static'], lang)} kg", 'dynamic': f"{fmt_int(v['dynamic'], lang)} kg",
                     'racking': f"{fmt_int(v['racking'], lang)} kg" if v['racking'] else '–',
                     'loc': loc_label(v['loc'], lang) if v['loc'] else None, 'cc': LOCATIONS[v['loc']]['cc'] if v['loc'] else None,
                     'loc_code': v['loc'], 'colour': (t['col_' + SKU_COLOUR[v['sku']]].capitalize() if v['sku'] in SKU_COLOUR else None),
                     'price': fmt_price(v['price'], lang) if v['price'] else t['on_request']})
    rows.sort(key=lambda r: not r['current'])
    return rows


def similar_models(m, n=10):
    """Pallets that resemble m: same size first, then same class, shared types, deck and underside."""
    def score(x):
        sc = 0.0
        sc += 6 if x['size'] == m['size'] else 0
        sc += 3 if x['class'] == m['class'] else 0
        sc += 1.5 * len(set(x['types']) & set(m['types']))
        sc += 1 if x['deck'] == m['deck'] else 0
        sc += 1 if x['support']['type'] == m['support']['type'] else 0
        sc += .5 if x['support']['n'] == m['support']['n'] else 0
        sc -= abs(math.log((x['static'][1] or 1) / (m['static'][1] or 1)))
        sc += .3 if x.get('had_price') else 0
        return sc
    pool = [x for x in MODELS if x['family'] != m['family']]     # the family's own articles have their own section
    return sorted(pool, key=lambda x: (-score(x), x['id']))[:n]


def desc_sections(html):
    """Split the product description (h3 + paragraphs) into numbered blocks for the product page."""
    parts = re.split(r'<h3>(.*?)</h3>', str(html))
    secs = []
    if parts[0].strip():
        secs.append({'title': None, 'html': Markup(parts[0].strip())})
    for i in range(1, len(parts), 2):
        secs.append({'title': Markup(parts[i]), 'html': Markup(parts[i + 1].strip())})
    return secs


# ---- load calculator (static/calc: Noah's engine, unchanged + ui.js; standard loads in data/calc-defaults.json) ----
CALC_ENGINE = open(os.path.join(ROOT, 'static/calc/engine.js'), encoding='utf-8').read()
CALC_P = {mm.group(1): {'l': int(mm.group(2)), 'w': int(mm.group(3)), 'h': int(mm.group(4)), 'fixed': 'palletH' in mm.group(5) or 'useFixedLimit' in mm.group(5)}
          for mm in re.finditer(r'\{ id: "([^"]+)", name: "[^"]*", l: (\d+), w: (\d+), h: (\d+)([^}]*)\}', CALC_ENGINE.split('const pallets = [', 1)[1].split('];', 1)[0])
          if 'isRunner' not in mm.group(5)}
CALC_STD = json.load(open(os.path.join(ROOT, 'data/calc-defaults.json'), encoding='utf-8'))
# pallets per truck position in the calculator (tautliner, mega/combi): compared with the stack table (data/stapels.json)
CALC_LIM = {mm.group(1): (int(mm.group(2)), int(mm.group(3))) for mm in re.finditer(r'\{ id: "([^"]+)",[^}]*?limitTautliner: (\d+), limitCombi: (\d+)', CALC_ENGINE)}
CALC_ALIAS = {'QP6080MB6FR': 'QP6080M6FR', 'RECYPAL1210RR': 'RECYCPAL1210RR'}     # same product, other spelling in the calculator
CALC_SHIPPING = {'EUROPAL800RR', 'RECYCPAL1210RR'}     # l/w in the calculator = the shipping pallet, not the pallet itself
CALC_SIZE = {(1200, 800): '1208', (1200, 1000): '1210', (1200, 1200): '1212', (1140, 1140): '1140', (1100, 1100): '1111', (760, 1140): '76114',
             (1220, 1020): '4048', (1300, 1100): '1311', (600, 800): '6080', (600, 400): '6040'}
CALC_VEH = [('taut', 'tautliner', 'taut'), ('mega', 'mega', 'mega'), ('c20', 'container20', 'c20'), ('c40hc', 'container40hc', 'cont')]
CALC_V = hashlib.md5((CALC_ENGINE + open(os.path.join(ROOT, 'static/calc/ui.js'), encoding='utf-8').read()).encode()).hexdigest()[:8]


CALC_CLICK = set(re.findall(r'id: "([^"]+)"[^}]*clickRunner: true', CALC_ENGINE))   # nested, runners loose (update 38)


def calc_nestable(i):
    return re.search(r'LB\d+F', i) is not None or i in CALC_CLICK     # same test as the engine (isNestableLBF / isNeverOnSide)


def calc_for_model(m):
    """(calculator id, exact) for a model: its own article, or a comparable one with the same footprint and height."""
    for s_ in [m['base']] + [re.sub(r'^\w\.', '', v['sku']) for v in m['variants']]:
        s_ = CALC_ALIAS.get(s_, s_)
        if s_ in CALC_P:
            return s_, True
    # closed-deck version (-CD) of a pallet the calculator knows: same footprint, legs and nesting, so the open-deck
    # article is a fair comparison (update 28: the truck block of these pallets was empty)
    for s_ in [m['base']] + [re.sub(r'^\w\.', '', v['sku']) for v in m['variants']]:
        s2 = re.sub(r'-CD$', '', s_)
        if s2 != s_ and s2 in CALC_P and abs(CALC_P[s2]['h'] - m['H']) <= 10:
            return s2, False
    if 'nestable' in m['types']:
        return None, False
    # a comparable article: same footprint, preferably the same stack per truck position as this article in the stack
    # table (update 38: the 6-runner PAS pallets stack 16 high, like QP1140MB3RR, not 17 like QP1140MB3R-PAS), then
    # the same load class and the nearest height
    cl, best = m['class'][0].upper(), None
    st = STACKS.get(m['sku']) or {}
    for i, p in CALC_P.items():
        if p['fixed'] or i in CALC_SHIPPING or calc_nestable(i) or sorted((p['l'], p['w'])) != sorted((m['L'], m['W'])) or abs(p['h'] - m['H']) > 10:
            continue
        mm = re.match(r'QP\d+([LMH])', i)
        lim = CALC_LIM.get(i, (0, 0))
        same_stack = st.get('stack') == lim[0] and (st.get('combi') or lim[1]) == lim[1]
        key = (0 if same_stack else 1, 0 if mm and mm.group(1) == cl else 1, abs(p['h'] - m['H']), i)
        if best is None or key < best:
            best = key
    return (best[-1], False) if best else (None, False)


def calc_data(lang):
    """Calculator catalogue per language: the site name of each calculator article ('n') and the site article number
    ('s') that the result's quote button puts in the quote form (update 28; the anchor article of the family first)."""
    names = {}
    for x in sorted(MODELS, key=lambda x: (0 if x.get('is_anchor', True) else 1, model_sort_key(x))):
        c, exact = calc_for_model(x)
        if c and exact and c not in names:
            names[c] = {'n': (x.get('card_name') or x['name'])[lang], 's': x['sku']}
    return {'t': T[lang]['calc_ui'], 'nick': T[lang]['size_nick'], 'cat': names}


CALC_NAME_SIZE = {i: (int(a), int(b)) for i, a, b in re.findall(r'id: "([^"]+)", name: "[^"(]*\((\d+)x(\d+)\)"', CALC_ENGINE)}
CALC_TBL_SIZES = [(1200, 800), (1200, 1000), (1220, 1020), (1200, 1200), (1140, 1140), (1100, 1100), (1300, 1100), (760, 1140), (600, 800), (600, 400)]


def calc_table(lang):
    """Standard loads per pallet size for the calculator page: the range over the calculator articles that are pallets on
    this site (same numbers as on the product pages), split into nestable and stackable. Cells: 'n' or 'min–max'."""
    t = T[lang]
    on_site = {c for c, ex in (calc_for_model(m) for m in MODELS) if c and ex}
    rows = []
    for L, W in CALC_TBL_SIZES:
        ids = [i for i in sorted(on_site) if i in CALC_STD and CALC_NAME_SIZE.get(i) in ((L, W), (W, L))]
        for kind in ('nest', 'stack'):
            grp = [i for i in ids if (calc_nestable(i) or i.startswith('QP60')) == (kind == 'nest')]   # display pallets nest (update 33)
            if not grp:
                continue
            cells = []
            for k, veh, ic in CALC_VEH:
                vals = [CALC_STD[i][veh] for i in grp if CALC_STD[i][veh]]
                if not vals:
                    cells.append(None)
                elif min(vals) == max(vals):
                    cells.append(fmt_int(vals[0], lang))
                else:
                    cells.append(f'{fmt_int(min(vals), lang)}\u2013{fmt_int(max(vals), lang)}')
            key = f'{L}x{W}'
            rows.append({'size': f'{L}\u00a0x\u00a0{W}\u00a0mm', 'nick': t['size_nick'].get(key) or t['size_nick'].get(f'{W}x{L}') or '',
                         'kind': t['calc_tbl'][kind], 'n': len(grp), 'cells': cells})
    for i, r in enumerate(rows):      # the size cell spans the nestable + stackable rows of that size
        r['span'] = 0 if i and rows[i - 1]['size'] == r['size'] else sum(1 for x in rows if x['size'] == r['size'])
    return {'cols': [t['calc_v'][k] for k, veh, ic in CALC_VEH], 'rows': rows}


def calc_ctx(lang, m=None):
    t = T[lang]
    out = {'sku': '', 'site': '', 'size': '', 'std': [], 'note': '', 'data': calc_data(lang), 'v': CALC_V}
    if m is None:
        return out
    c, exact = calc_for_model(m)
    out['site'] = m['sku']     # the quote button of the calculator on this product page uses this article number
    out['size'] = CALC_SIZE.get((m['L'], m['W'])) or CALC_SIZE.get((m['W'], m['L'])) or ''
    if c:
        out['sku'] = c
        if c in CALC_STD:
            out['std'] = [{'key': k, 'icon': ic, 'label': t['calc_v'][k], 'n': fmt_int(CALC_STD[c][veh], lang) if CALC_STD[c][veh] else None} for k, veh, ic in CALC_VEH]
            note = t['calc_note'].format(nest='' if c in CALC_CLICK else (t['calc_note_nest'] if calc_nestable(c) else ''))
            if c in CALC_CLICK:     # nested, the loose runners on their own pallets are part of the load (update 38)
                note += ' ' + t['calc_note_click']
            out['note'] = note + ('' if exact else ' ' + t['calc_note_like'].format(sku=c))
    return out


_TWINS = {}


def _meta_twins(lang):
    """Articles whose meta description would be the same as another one's (without prices the price no longer tells
    them apart, update 34): they get their height in the description."""
    if lang not in _TWINS:
        seen = {}
        for x in MODELS:
            seen.setdefault(PC.meta_desc(x, lang), []).append(x['id'])
        _TWINS[lang] = {i for ids in seen.values() if len(ids) > 1 for i in ids}
    return _TWINS[lang]


def render_product(m, lang):
    t = T[lang]
    pid = 'p:' + m['id']
    X = m['txt'][lang]
    crumbs = crumbs_for(pid, lang)
    m['name']['_cur'] = m['name'][lang]
    m['_weight_txt'] = X['weight']
    svg = Markup(drawing(m, t, m['id'] + lang + '-s'))
    hyg = is_hyg(m)
    spec_rows = spec_groups(m, lang, price=False)
    variants = variant_rows(m, lang)
    same = [x for x in MODELS if x['size'] == m['size']]
    downloads = [{'url': X['datasheet'], 'label': t['dl_datasheet'], 'meta': t['dl_datasheet_meta'], 'ico': 'PDF', 'kind': 'ds'}]
    for pg in m['ppwr']:
        if pg in PPWR_FILES:
            downloads.append({'url': '/downloads/ppwr/' + PPWR_FILES[pg], 'label': t['dl_ppwr'], 'meta': t['dl_ppwr_meta'].format(doc='PG-' + pg), 'ico': 'DoC', 'kind': 'ppwr'})
    downloads.append({'url': '/' + CATALOG_FILES[lang], 'label': t['dl_catalog'], 'meta': t['catalog_meta'].format(size=catalog_size(lang)), 'ico': '2026', 'kind': 'cat'})
    see = [{'label': t['class_title'][m['class']], 'url': url('class-' + m['class'], lang)}]
    for ty in m['types']:
        see.append({'label': t['type_name'][ty], 'url': url('type-' + ty, lang)})
    if m['special'] == 'pool':
        see.append({'label': 'Ultra pallet', 'url': url('ultra', lang)})
    if m['support']['type'] == 'feet' and m['size'] in RUNNER_SIZES and 'display' not in m['types']:
        see.append({'label': short_title('acc-runners', lang), 'url': url('acc-runners', lang)})
    if m['size'] in COLLAR_SIZES:
        see.append({'label': short_title('acc-collars', lang), 'url': url('acc-collars', lang)})
    see.append({'label': short_title('about-load', lang), 'url': url('about-load', lang)})
    title = PC.meta_title(m, lang)
    desc = PC.meta_desc(m, lang, with_h=m['id'] in _meta_twins(lang))   # height in when two articles would share the text
    check_meta(pid, lang, title, desc)
    jl = [product_ld(m, lang), crumbs_ld(crumbs)]
    ctx = base_ctx(pid, lang, title, desc, section='pallets', jsonld=jl, preload=m['gallery'][0]['md'] if m['gallery'] else m['img_url'], tpl='product')
    ctx['meta']['og_type'] = 'product'
    ctx['meta']['og_title'] = m['name'][lang]
    ctx.update(m=m, X=X, crumbs=crumbs, drawing=svg, spec_rows=spec_rows, variants=variants, same=same, downloads=downloads,
               size_url=url('size-' + m['size'], lang), all_in_size=t['all_in_size'].format(size=m['size_label']),
               cmp_title=t['compare_same_size'].format(size=m['size_label']), see_also=see, size_nick=t['size_nick'][m['size']],
               anchors=t['anchor'], hyg=hyg, similar=similar_models(m), desc_secs=desc_sections(X['desc_html']), load=calc_ctx(lang, m),
               news_rel=related_news(pid, lang, m))
    return env.get_template('product.html').render(**ctx)


def side_nav_for(pid, lang):
    t = T[lang]
    if pid.startswith('about') and pid not in ('about-load', 'about-glossary') or pid in ('dealers', 'careers') or pid.startswith('job-'):
        cur = 'careers' if pid.startswith('job-') else pid      # a vacancy belongs under 'Vacatures'
        return {'title': t['nav_about'], 'links': [{'label': a['label'], 'url': a['url'], 'current': a['id'] == cur} for a in NAV[lang]['about']]}
    if pid.startswith('sector'):
        return {'title': t['nav_sectors'], 'links': [{'label': s['label'], 'url': s['url'], 'current': pid == 'sector-' + s['key']} for s in NAV[lang]['sectors']]}
    if pid.startswith('acc') or pid == 'used':
        return {'title': t['nav_acc'], 'links': [{'label': a['label'], 'url': a['url'], 'current': a['id'] == pid} for a in NAV[lang]['acc']]}
    if pid in ('about-load', 'about-glossary'):
        return {'title': t['nav_knowledge'], 'links': [{'label': g['label'], 'url': g['url'], 'current': False} for g in NAV[lang]['guides']] +
                [{'label': plain(CONTENT[lang]['news-hdpe']['fm']['h1']), 'url': url('news-hdpe', lang), 'current': False}] +
                [{'label': k['label'], 'url': k['url'], 'current': k['id'] == pid} for k in NAV[lang]['know_extra']]}
    if pid == 'ultra':
        return {'title': t['mm_types'], 'links': [{'label': ty['label'], 'url': ty['url'], 'current': False} for ty in NAV[lang]['types']]}
    if pid in ('privacy', 'cookies', 'terms'):
        return {'title': 'Q-Pall', 'links': [{'label': short_title(p, lang), 'url': url(p, lang), 'current': p == pid} for p in ('terms', 'privacy', 'cookies')]}
    return None


def guides_list(lang):
    """Knowledge-base items in /kennisbank/ order, with filter category."""
    t = T[lang]
    out = []
    for gid, cat in KB_ITEMS:
        fm = CONTENT[lang][gid]['fm']
        out.append({'id': gid, 'url': url(gid, lang), 'title': plain(fm['h1']), 'lead': fm['lead'], 'reading': fm.get('reading'),
                    'tag': fm.get('tag', ''), 'cat': cat, 'cat_label': t['kb_cat'][cat], 'guide': gid.startswith('guide-')})
    return out


def kb_side_extra(lang):
    """Items under the guides in the 'Kennisbank' sidebar: the PE-HD 2 article and the glossary (KB_SIDE_EXTRA)."""
    out = []
    for k in KB_SIDE_EXTRA:
        title = T[lang]['kb_side_glossary'] if k == 'about-glossary' else plain(CONTENT[lang][k]['fm']['h1'])
        out.append({'id': k, 'url': url(k, lang), 'title': title})
    return out


def news_img(pid, w=640):
    """Cover image of a news item: (src, srcset or None)."""
    img = PAGES[pid]['img']
    if img.startswith('photos/'):
        n = img.split('/', 1)[1]
        mid = f'/assets/img/{img}-960.webp 960w, ' if n in HEAVY_COVERS else ''
        return f'/assets/img/{img}-640.webp', f'/assets/img/{img}-640.webp 640w, {mid}/assets/img/{img}-1200.webp 1200w' if NEWS_WIDE.get(n, True) else None
    return '/assets/img/' + img, None


NEWS_WIDE = {'stackup': False, 'warehouse': False, 'beverage': False}   # source photos smaller than 1200 px: no 1200w candidate
for _f in glob.glob(os.path.join(ROOT, 'input/brand/photo-n-*.webp')):         # migrated news covers (update 11)
    from PIL import Image as _Im2
    NEWS_WIDE[os.path.basename(_f)[6:-5]] = _Im2.open(_f).width >= 1200


def news_list(lang):
    """News items in NEWS_ITEMS order (newest first, as on the old qpall.com overview). Most migrated articles have no date."""
    t = T[lang]
    out = []
    for pid in NEWS_ITEMS:
        fm = CONTENT[lang][pid]['fm']
        d = datetime.date.fromisoformat(str(fm['published'])) if fm.get('published') else None
        src, srcset = news_img(pid)
        out.append({'id': pid, 'url': url(pid, lang), 'title': plain(fm['h1']), 'lead': fm['lead'], 'tag': fm.get('tag', ''),
                    'date': d.isoformat() if d else None, 'date_txt': fmt_date(d, lang) if d else None, 'img': src, 'srcset': srcset,
                    'img_alt': fm.get('img_alt', ''), 'reading': fm.get('reading'), 'author': fm.get('author')})
    # newest first by publication date (update 28: the old dates are back); an undated article keeps its place in the
    # old overview, i.e. it takes the date of the article above it
    prev = '9999'
    for n in out:
        n['_eff'] = n['date'] or prev
        prev = n['_eff']
    out.sort(key=lambda n: n['_eff'], reverse=True)
    return out


# Related news per page (update 28): guides, sectors, product categories and about pages link to the stories that
# belong with them. Products get theirs from their type and class (related_news()).
RELATED_NEWS = {
    'pallets': ['news-which-pallet', 'news-choosing-pallet', 'news-hdpe'],
    'guide-ppwr': ['news-ppwr', 'news-recycling', 'news-economical'],
    'guide-ispm': ['news-regulations', 'news-euro-export', 'news-price-wood'],
    'guide-wood': ['news-price-wood', 'news-why-plastic', 'news-environment'],
    'guide-prices': ['news-price-wood', 'news-economical', 'news-which-pallet'],
    'guide-sizes': ['news-choosing-size', 'news-euro-export', 'news-which-pallet'],
    'guide-choose': ['news-which-pallet', 'news-choosing-pallet', 'news-hdpe'],
    'guide-automation': ['news-process', 'news-stackup', 'news-choosing-size'],
    'sector-food': ['news-haccp', 'news-h1', 'news-cleaning'],
    'sector-beverage': ['news-mega-order', 'news-horeca', 'news-poolpallet'],
    'sector-chemical': ['news-esd', 'news-antistatic', 'news-regulations'],
    'sector-pharma': ['news-covid', 'news-cleaning', 'news-esd'],
    'sector-logistics': ['news-logistics-update', 'news-future-logistics', 'news-green-logistics'],
    'sector-pooling': ['news-poolpallet', 'news-mega-order', 'news-durability'],
    'sector-retail': ['news-auchan', 'news-industries', 'news-bestpal-mpackaging'],
    'type-hygienic': ['news-h1', 'news-haccp', 'news-cleaning'],
    'type-export': ['news-euro-export', 'news-brexit', 'news-regulations'],
    'type-nestable': ['news-stacking', 'news-euro-export', 'news-which-pallet'],
    'type-antislip': ['news-antislip-grip', 'news-antislip-mandatory', 'news-damage'],
    'type-cp': ['news-regulations', 'news-esd', 'news-industries'],
    'type-display': ['news-industries', 'news-auchan', 'news-choosing-size'],
    'type-block': ['news-heavy-range', 'news-stacking', 'news-damage'],
    'class-light': ['news-euro-export', 'news-stacking', 'news-which-pallet'],
    'class-medium': ['news-medium-gen3', 'news-antislip-grip', 'news-choosing-pallet'],
    'class-heavy': ['news-heavy-range', 'news-heavy-family', 'news-poolpallet'],
    'size-1200x800': ['news-medium-gen3', 'news-euro-export', 'news-choosing-size'],
    'size-1200x1000': ['news-poolpallet', 'news-choosing-size', 'news-which-pallet'],
    'about-sustainability': ['news-ecovadis-silver', 'news-recycling', 'news-scopac'],
    'about-local': ['news-local', 'news-local-resilience', 'news-local-sustainability'],
    'about-custom': ['news-stackup', 'news-process', 'news-which-pallet'],
    'about-load': ['news-stacking', 'news-damage', 'news-heavy-range'],
    'used': ['news-qused', 'news-used-types', 'news-recycling'],
    'ultra': ['news-poolpallet', 'news-heavy-range', 'news-mega-order'],
}


def related_news(pid, lang, m=None):
    """Up to three news items that belong with a page (RELATED_NEWS, or for a product its type and class).
    A news article gets articles with the same tag first."""
    allnews = news_list(lang)
    by_id = {n['id']: n for n in allnews}
    if m is not None:
        ids = []
        if is_hyg(m):
            ids += ['news-h1', 'news-haccp', 'news-cleaning']
        if m['antislip']:
            ids += ['news-antislip-grip', 'news-antislip-mandatory']
        if m['special'] == 'us':
            ids += ['news-medium-4840']
        if m['special'] == 'pool':
            ids += ['news-poolpallet']
        if 'export' in m['types'] or 'nestable' in m['types']:
            ids += ['news-euro-export', 'news-stacking']
        ids += {'light': ['news-which-pallet'], 'medium': ['news-medium-gen3'], 'heavy': ['news-heavy-range']}[m['class']]
        ids += ['news-hdpe', 'news-choosing-pallet']
    elif pid in RELATED_NEWS:
        ids = RELATED_NEWS[pid]
    elif pid.startswith('size-'):
        ids = ['news-choosing-size', 'news-which-pallet', 'news-hdpe']
    elif pid in by_id:
        tag = by_id[pid]['tag']
        ids = [n['id'] for n in allnews if n['tag'] == tag and n['id'] != pid] + [n['id'] for n in allnews]
    else:
        return []
    # QA round (update 47): never the page's own photo again as a news cover right below it, and always a full row of
    # three (a draft or hidden article in the list no longer leaves a gap): filled up with the newest articles
    own = PAGE_PHOTO.get(pid)
    skip_img = f"photos/{own}" if own else None
    ids = list(ids) + [n['id'] for n in allnews]
    out, seen = [], {pid}
    for i in ids:
        if i in by_id and i not in seen and PAGES[i].get('img') != skip_img:
            seen.add(i)
            out.append(by_id[i])
    return sorted(out[:3], key=lambda n: n['_eff'], reverse=True)     # the three cards newest first


def add_toc(html):
    """Give every <h2> an id and return (html, [(id, text), ...]) for the 'on this page' list."""
    toc, seen = [], set()

    def rep(mo):
        txt = re.sub(r'<[^>]+>', '', mo.group(1)).strip()
        hid = slugify(txt)[:60] or 'sectie'
        while hid in seen:
            hid += '-2'
        seen.add(hid)
        toc.append((hid, txt))
        return f'<h2 id="{hid}">{mo.group(1)}</h2>'
    return Markup(re.sub(r'<h2>(.*?)</h2>', rep, str(html))), toc


def fmt_date(d, lang):
    months = T[lang]['months']
    if lang == 'en':
        return f"{d.day} {months[d.month - 1]} {d.year}"
    if lang == 'de':
        return f"{d.day}. {months[d.month - 1]} {d.year}"
    if lang == 'es':
        return f"{d.day} de {months[d.month - 1]} de {d.year}"
    return f"{d.day} {months[d.month - 1]} {d.year}"




# ---- careers + vacancy pages (update 20) ----
# every country in the six languages for the quote form (data/countries.json, made by tools/countries.py; update 23)
_cpath = os.path.join(ROOT, 'data', 'countries.json')
COUNTRIES_ALL = json.load(open(_cpath, encoding='utf-8')) if os.path.exists(_cpath) else None
CAREERS_CONTACT = 'sabine-oudshoorn'          # contact person for applications (TEAM key)
CAREERS_EMAIL = 'oudshoorn@qpall.com'
JOB_HERO = 'office-sales'                     # vacancy page: hero photo (Noah's office photo) + photo strip below the tasks
JOB_PHOTOS = [('office-desk', 'photos_alt', 1), ('careers-coffee', 'gallery_alt', 2), ('careers-lunch', 'photos_alt', 2), ('careers-swing', 'photos_alt', 3)]   # (photo, alt list, index)
CAREERS_HERO = 'careers-talk'
CAREERS_GALLERY = [('careers-lunch', 1), ('careers-coffee', 2), ('careers-swing', 3), ('careers-lounge', 0)]   # (photo, index in apply.gallery_alt); mosaic: big, small, small, wide
CV_MAX_MB = 5                                 # Netlify Forms: max. 8 MB per submission


def job_pages(lang):
    """Open vacancies (pages with tpl 'job' whose front matter 'job' is not closed), for the careers page."""
    out = []
    for pid, p in PAGES.items():
        if p['tpl'] != 'job' or pid not in CONTENT[lang]:
            continue
        fm = CONTENT[lang][pid]['fm']
        if fm.get('job', {}).get('closed'):
            continue
        out.append({'id': pid, 'title': fm['job']['title'], 'url': url(pid, lang), 'lead': fm['lead'], 'facts': fm.get('hero', {}).get('facts', [])})
    return out


def careers_ctx(pid, lang, fm):
    t = T[lang]
    person = next(p for p in team_ctx(lang) if p['key'] == CAREERS_CONTACT)
    home = CONTENT[lang]['home']['fm']['stats']
    d = {'contact': dict(person, email=CAREERS_EMAIL), 'stats': [home[i] for i in (0, 1, 2, 4)],
         'apply_url': url('thanks-apply', lang), 'cv_max': CV_MAX_MB, 'ui': t['apply']}
    if pid == 'careers':
        d['jobs'] = job_pages(lang)
        d['hero_photo'] = CAREERS_HERO
        d['gallery'] = [{'src': n, 'alt': t['apply']['gallery_alt'][i]} for n, i in CAREERS_GALLERY]
        d['job_value'] = T['nl']['apply']['open_job']   # HR reads Dutch, whatever the page language (update 23)
    else:
        d['photos'] = [{'src': n, 'alt': t['apply'][k][i]} for n, k, i in JOB_PHOTOS]
        d['hero_photo'] = JOB_HERO
        d['job_value'] = CONTENT['nl'].get(pid, {}).get('fm', {}).get('job', {}).get('title') or fm['job']['title']
        d['job_title'] = fm['job']['title']      # shown above the form in the page language (update 33)
    return d


def job_description_html(fm):
    """JobPosting description: the vacancy text as simple HTML (Google for Jobs wants the full description)."""
    e = lambda x: escape(plain(x))
    h = [f"<p>{e(fm['lead'])}</p>", f"<h3>{e(fm['tasks']['title'])}</h3>", f"<p>{e(fm['tasks']['lead'])}</p><ul>"]
    h += [f"<li><strong>{e(i['title'])}</strong>: {e(i['text'])}</li>" for i in fm['tasks']['items']]
    h += ['</ul>', f"<h3>{e(fm['profile']['title'])}</h3><ul>"] + [f"<li>{e(i)}</li>" for i in fm['profile']['items']]
    h += ['</ul>', f"<p>{e(fm['profile']['note'])}</p>", f"<h3>{e(fm['offer']['title'])}</h3><ul>"]
    h += [f"<li><strong>{e(i['title'])}</strong>: {e(i['text'])}</li>" for i in fm['offer']['items']] + ['</ul>']
    h += [f"<h3>{e(fm['why']['title'])}</h3>", f"<p>{e(fm['why']['text'])}</p>"]
    return ''.join(str(x) for x in h)


def render_page(pid, lang):
    t = T[lang]
    p = PAGES[pid]
    tpl = p['tpl']
    if pid == 'home':
        return render_home(lang)
    if tpl == 'acc':
        return render_acc(pid, lang)
    if tpl == 'transport':
        return render_transport(lang)
    page = page_obj(pid, lang)
    fm = page['fm']
    crumbs = crumbs_for(pid, lang)
    body = md_html(CONTENT[lang][pid]['body'], lang)
    jl = [crumbs_ld(crumbs)] + ([contactpage_ld(lang)] if pid == 'contact' else [])
    if page['faq']:
        jl.append(faq_ld(page['faq']))
    extra = {}
    noindex = p.get('noindex', False)
    if tpl == 'article':
        is_news = bool(p.get('news'))
        dated = bool(fm.get('published')) or not is_news          # migrated news without a known date show none
        pub = str(fm.get('published', '2026-10-05'))
        upd = str(fm.get('updated', pub))
        if pid in GUIDES:          # the guides are new on this site: published on the go-live date (LAUNCH_DATE)
            pub = LAUNCH_DATE or BUILD_DATE
            upd = max(upd, pub)
        who = author_of(pid, fm, lang)
        extra['author'] = who
        if who:
            author = person_ld(who['key'], lang, context=False)
        else:
            author = {'@type': 'Person', 'name': fm['author'], 'worksFor': {'@id': ORG_ID}} if fm.get('author') else {'@id': ORG_ID}
        if is_news:
            src, srcset = news_img(pid)
            extra['cover'] = {'src': src, 'srcset': srcset, 'alt': fm.get('img_alt', ''), 'caption': fm.get('img_caption'), 'svg': src.endswith('.svg')}
        jl.insert(0, {'@context': 'https://schema.org', '@type': 'NewsArticle' if is_news else 'Article', 'headline': plain(fm['h1']),
                      'description': fm['description'], 'inLanguage': HTML_LANG[lang],
                      **({'datePublished': pub, 'dateModified': upd} if dated else {}),
                      'mainEntityOfPage': abs_url(url(pid, lang)), 'author': author, 'publisher': {'@id': ORG_ID}, 'image': abs_url(og_for(pid, lang))})
        extra['updated_txt'] = fmt_date(datetime.date.fromisoformat(upd), lang)
        extra['published_txt'] = fmt_date(datetime.date.fromisoformat(pub), lang) if dated else None
        extra['show_updated'] = dated and upd != pub
        extra['news'] = is_news
        body, extra['toc'] = add_toc(body)
        if is_news:
            allnews = news_list(lang)
            # sidebar: the 8 newest articles (the current one stays in the list when it is older)
            side = allnews[:8]
            if pid not in [n['id'] for n in side]:
                side = side[:7] + [n for n in allnews if n['id'] == pid]
            extra['news_side'] = side
            extra['news_more'] = related_news(pid, lang)
        else:
            extra['news_more'] = related_news(pid, lang)
            extra['kb_list'] = [g for g in guides_list(lang) if g['guide']] + kb_side_extra(lang)
            extra['guides'] = [g for g in guides_list(lang) if g['id'] != pid][:3]
    if fm.get('job') and not fm['job'].get('closed'):
        jl.append(job_ld(pid, lang, fm, body))
    if pid == 'about-team':
        extra['team_cards'] = team_ctx(lang)
        jl += [person_ld(p['key'], lang) for p in TEAM]
    if tpl == 'news':
        extra['news_items'] = news_list(lang)
    if tpl == 'knowledge':
        extra['guides'] = guides_list(lang)
        extra['kb_cats'] = [(c, t['kb_cat'][c]) for c in KB_CATS]
    if tpl == 'sectors':
        extra['sector_cards'] = [{'key': s['key'], 'url': url('sector-' + s['key'], lang), 'label': t['sector_name'][s['key']],
                                  'lead': CONTENT[lang]['sector-' + s['key']]['fm']['lead'], 'img': SECTOR_IMG[s['key']] or f"/assets/img/photos/sector-{s['key']}",
                                  'sub': t['sector_sub'][s['key']], 'icon': s['icon']} for s in SECTORS]
        hs = CONTENT[lang]['home']['fm']['sectors']
        extra['sector_ask'] = {'big': hs['ask_big'], 'title': hs['ask'], 'sub': hs['ask_sub'], 'url': url('contact', lang)}
    if fm.get('recommend'):
        rec = [MODEL_BY_ID[r] for r in fm['recommend'] if r in MODEL_BY_ID]
        bad = [r for r in fm['recommend'] if r not in MODEL_BY_ID]
        if bad:
            WARN.append(f'bad recommend {pid}: {bad}')
        extra['recommend'] = rec
        extra['recommend_title'] = t['recommended_for'] if pid.startswith('sector') else t['recommended']
        jl.append(itemlist_ld(rec, lang, t['recommended']))
    elif tpl == 'article' and pid in ARTICLE_RECOMMEND:
        extra['recommend'] = [MODEL_BY_ID[r] for r in ARTICLE_RECOMMEND[pid]]
        extra['recommend_title'] = t['rec_topic']
    if pid == 'ultra':
        jl.insert(0, ultra_ld(lang, fm))
        extra['ultra_sku'] = ULTRA_SKU
        extra['recommend'] = [MODEL_BY_ID[i] for i in ULTRA_MODELS]
        extra['recommend_title'] = 'Ultra pallet'
        um = MODEL_BY_ID[ULTRA_MODELS[-1]]
        extra['ultra_img'] = {'lg': um['img_lg'], 'md': um['img_url'], 'alt': um['name'][lang]}
        extra['ultra_txt'] = ULTRA_TXT[lang]
    if pid in PAGE_PHOTO:
        extra['page_photo'] = {'src': '/assets/img/photos/' + PAGE_PHOTO[pid], 'alt': t['photo_alt'].get(PAGE_PHOTO[pid]) or plain(page['h1'])}
    if pid == 'about-sustainability':   # EcoVadis badge next to the EcoVadis paragraph (Noah, update 19)
        badge = (f'<img class="eco-badge" src="/assets/img/brand/badge-ecovadis-bronze-2026-320.webp" alt="{escape(t["ecovadis"])}" '
                 f'title="{escape(t["ecovadis"])}" width="160" height="160" loading="lazy" decoding="async">')
        body, n_badge = re.subn(r'(<h2[^>]*>[^<]*EcoVadis[^<]*</h2>)', lambda mm: mm.group(1) + badge, str(body), count=1)
        body = Markup(body)
        if not n_badge:
            WARN.append(f'EcoVadis heading not found on {pid}/{lang}')
    if pid in PAGE_DUO:   # two extra photos after the first list in the text (about: the head office)
        *duo, k_alt, k_cap = PAGE_DUO[pid]
        imgs = ''.join(f'<img src="/assets/img/photos/{n}-640.webp" srcset="/assets/img/photos/{n}-640.webp 640w, /assets/img/photos/{n}-1200.webp 1200w" '
                       f'sizes="(min-width:1000px) 380px, 46vw" alt="{escape(t[k_alt])}" width="640" height="480" loading="lazy" decoding="async">' for n in duo)
        fig = f'<figure class="photo-duo">{imgs}<figcaption>{escape(t[k_cap])}</figcaption></figure>'
        if PAGE_DUO_AT.get(pid) == 'h2:2':
            hs = [mo.start() for mo in re.finditer(r'<h2[ >]', str(body))]
            b = str(body)
            body = Markup(b[:hs[1]] + fig + b[hs[1]:]) if len(hs) > 1 else Markup(b + fig)
        else:
            body = Markup(str(body).replace('</ul>', '</ul>' + fig, 1))
    if pid == 'dealers':   # dealers per country below the map (update 27), sorted by the country name in this language
        import unicodedata
        cn = lambda cc: (COUNTRIES_ALL or {}).get(lang, {}).get(cc) or cc
        key = lambda x: unicodedata.normalize('NFKD', x).encode('ascii', 'ignore').decode().lower()
        groups = {}
        for cc, name, city in DEALERS:
            groups.setdefault(cc, []).append({'name': name, 'city': city})
        extra['dealer_list'] = [{'cc': cc, 'flag': 'uk' if cc == 'GB' else cc.lower(), 'country': cn(cc),
                                 'dealers': sorted(ds, key=lambda d: key(d['name']))}
                                for cc, ds in sorted(groups.items(), key=lambda kv: key(cn(kv[0])))]
    if pid == 'contact':   # head office block below the form (update 27): route link like on the transport page
        extra['hq_route'] = ('https://www.google.com/maps/dir/?api=1&destination=' +
                             quote_plus(f"Q-Pall, {COMPANY['street']}, {COMPANY['zip']} {COMPANY['city']}, Netherlands"))
    if pid == 'terms':
        extra['toc'] = [(f'article-{n}', f'{n}. {title}') for n, title in terms_articles()]
    if tpl == 'calc':
        extra['calc'] = calc_ctx(lang)
        extra['calc_table'] = calc_table(lang)
    if tpl == 'form':
        extra['form'] = p['form']
        extra['product_names'] = [m['name'][lang] for m in MODELS]
        # quote form: choose by article number (every version of every pallet, then the accessories)
        # every option carries its stack size (data-stack: pallets per full stack) and its page (for the thank-you page)
        opts = quote_options(lang)
        extra['product_opts'] = opts
        extra['stack'] = 1
        extra['t_nl'] = T['nl']   # radio values in Dutch for sales; the visitor sees the own language (update 23)
        extra['countries'] = list(COUNTRIES_ALL[lang].values()) if COUNTRIES_ALL else sorted({COUNTRY[c][lang] for c in COUNTRY})
    if tpl == 'thanks' and pid == 'thanks-apply':     # application: Sabine instead of the sales team (update 23)
        extra['ty_people'] = [p for p in team_ctx(lang) if p['key'] == CAREERS_CONTACT]
        extra['ty_email'] = CAREERS_EMAIL
    if tpl in ('careers', 'job'):
        extra.update(careers_ctx(pid, lang, fm))
        if tpl == 'job' and fm.get('job') and not fm['job'].get('closed'):
            jl = [x for x in jl if x.get('@type') != 'JobPosting'] + [job_ld(pid, lang, fm, job_description_html(fm))]
    if tpl == 'page':
        extra['news_rel'] = related_news(pid, lang) if (pid in RELATED_NEWS or pid.startswith('sector-')) else []
    check_meta(pid, lang, fm['title'], fm['description'])
    ctx = base_ctx(pid, lang, fm['title'], fm['description'], section=section_of(pid), noindex=noindex, jsonld=jl, tpl=tpl)
    ctx.update(page=page, crumbs=crumbs, body=body, side_nav=side_nav_for(pid, lang), **extra)
    tplname = {'careers': 'careers.html', 'job': 'job.html', 'page': 'page.html', 'article': 'article.html', 'knowledge': 'knowledge.html', 'sectors': 'sectors.html', 'form': 'form.html', 'news': 'news.html', 'calc': 'calc.html', 'thanks': 'thanks.html'}[tpl]
    return env.get_template(tplname).render(**ctx)


def render_transport(lang):
    t = T[lang]
    pid = 'transport'
    page = page_obj(pid, lang)
    fm = page['fm']
    crumbs = crumbs_for(pid, lang)
    body = md_html(CONTENT[lang][pid]['body'], lang)
    sites = []
    days = t['days_short']
    def dmy(v):
        dd, mm, yy = (int(x) for x in v.split('-'))
        return fmt_date(datetime.date(yy, mm, dd), lang)
    for s in TRANSPORT_SITES:
        hol = None
        if s['hol']:
            hol = {'name': t['tr_' + s['hol'][0]], 'period': f"{dmy(s['hol'][1])} – {dmy(s['hol'][2])}", 'status': t['tr_' + (s['hol'][3] if len(s['hol']) > 3 else 'limited')]}
        hours = [{'days': days[a - 1] if a == b else f"{days[a - 1]}–{days[b - 1]}", 'times': ', '.join(tt)} for a, b, tt in s['hours']]
        route = 'https://www.google.com/maps/dir/?api=1&destination=' + quote_plus(', '.join(s['addr'][1:]) + ', ' + COUNTRY[s['cc']]['en'])
        direct = f"{COMPANY['simplybook']}/v2/#book/location/{s['loc']}/category/{s['cat']}"
        sites.append(dict(s, country=COUNTRY[s['cc']][lang], hol=hol, hours_rows=hours, route=route, direct=direct))
    jl = [crumbs_ld(crumbs)]
    if page['faq']:
        jl.append(faq_ld(page['faq']))
    check_meta(pid, lang, fm['title'], fm['description'])
    ctx = base_ctx(pid, lang, fm['title'], fm['description'], jsonld=jl, tpl='transport')
    ctx.update(page=page, crumbs=crumbs, body=body, sites=sites, sb_url=COMPANY['simplybook'], sb_crop=SB_CROP, calc=calc_ctx(lang))
    return env.get_template('transport.html').render(**ctx)


def acc_tile(src):
    """Overview card image for an accessory (update 50): the product cropped to its outline and fitted in 640 x 400 with
    the same margin, so all cards show their product at a comparable size. Made from the built image."""
    if not src:
        return src
    from PIL import Image, ImageChops
    path = os.path.join(OUT, src.lstrip('/').split('?')[0])
    name = 'tile-' + os.path.splitext(os.path.basename(path))[0] + '.webp'
    dst = os.path.join(OUT, 'assets', 'img', 'acc', name)
    if not os.path.exists(dst):
        im = Image.open(path).convert('RGBA')
        bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg.convert('RGB')
        mask = ImageChops.difference(im, Image.new('RGB', im.size, (255, 255, 255))).convert('L').point(lambda v: 255 if v > 18 else 0)
        box = mask.getbbox() or (0, 0, im.width, im.height)
        obj = im.crop(box)
        W, H, pad = 640, 400, 0.13
        sc = min(W * (1 - 2 * pad) / obj.width, H * (1 - 2 * pad) / obj.height)
        obj = obj.resize((max(1, round(obj.width * sc)), max(1, round(obj.height * sc))), Image.LANCZOS)
        tile = Image.new('RGB', (W, H), (255, 255, 255))
        tile.paste(obj, ((W - obj.width) // 2, (H - obj.height) // 2))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        tile.save(dst, 'WEBP', quality=84, method=6)
    return '/assets/img/acc/' + name


ACC_PHOTO = {'collar': '/assets/img/acc/photo-collar.webp', 'lid': '/assets/img/acc/photo-lid.webp',
             'freezer': '/assets/img/acc/photo-freezer.webp', 'driptray': '/assets/img/acc/photo-drip.webp',
             'grating': '/assets/img/acc/photo-grating.webp', 'grid': '/assets/img/acc/photo-grid.webp'}
# per-article photo: input/acc-photos/<sku in lower case>.png|webp (e.g. qpfsi1208-blue.webp) wins over the kind photo
ACC_SKU_PHOTO = {os.path.splitext(os.path.basename(f))[0] for f in glob.glob(os.path.join(INPUT, 'acc-photos', '*.*'))}


def quote_options(lang):
    """The quote form's product list: every version of every pallet, the Ultra pallet as one line, then the accessories.
    Each option carries its stack size (pallets per full stack), its page and photo. Also used by the confirmation e-mail."""
    sku2m = {x['sku']: x for x in MODELS}
    opts, seen = [], set()
    for m in sorted(MODELS, key=model_sort_key):
        for v in sorted(m['variants'], key=lambda v: v['sku']):
            if v['sku'] in seen:
                continue
            seen.add(v['sku'])
            st = STACKS.get(v['sku'])
            a = sku2m.get(v['sku'], m)
            nm = a.get('card_name') or a['name']      # the article number leads the option, so not again at the end (update 53)
            opts.append({'v': f"{v['sku']} – {nm[lang]}", 'nl': f"{v['sku']} – {nm['nl']}", 'acc': False, 'stack': st['stack'] if st else 1,
                         'url': a['url'][lang], 'img': a['img_sm']})
    um = MODEL_BY_ID[ULTRA_MODELS[0]]     # Ultra pallet as one line (QP1210H), so ?sku=QP1210H from the Ultra page is recognised
    opts.append({'v': f"{ULTRA_SKU} – Ultra pallet", 'acc': False, 'stack': (STACKS.get(um['variants'][0]['sku']) or {}).get('stack', 1),
                 'url': url('ultra', lang), 'img': um['img_sm']})
    opts += [{'v': f"{a['sku']} – {acc_item(a, lang)['name']}", 'nl': f"{a['sku']} – {acc_item(a, 'nl')['name']}", 'acc': True, 'stack': 1, 'url': acc_item(a, lang).get('url', ''), 'img': ''}
             for a in ACCS]   # accessories: per piece
    return opts


def acc_item(a, lang):
    t = T[lang]
    N = t['acc_name']
    w = t['acc_words']
    k = a['kind']
    dims = f"{a['L']} x {a['W']}" + (f" x {fmt_dec(a['H'], lang)}" if a['H'] else '') + ' mm'
    rows = [(t['art_nr'], a['sku']), (t['dims'], dims)]
    if a['weight']:
        rows.append((t['weight'], f"{fmt_dec(a['weight'], lang)} kg"))
    if a['static']:
        rows.append((t['static_l'], f"{fmt_int(a['static'], lang)} kg"))
    if a['dynamic']:
        rows.append((t['dynamic_l'], f"{fmt_int(a['dynamic'], lang)} kg"))
    name = f"{N[k]} {dims}"
    if k == 'freezer':
        typ = re.match(r'QPFS(I+)', a['sku']).group(1)
        col = w[a['color']] if a.get('color') else ''
        name = f"{N[k]} {w['type']} {typ} {a['L']} x {a['W']} x {fmt_dec(a['H'], lang)} mm, {col}"
        rows.append((w['colour'], col))
    if k == 'runner':
        if a['sku'].startswith('QP-RUN'):
            hl = w['low'] if a['sku'].endswith('L') else w['high']
            name = f"{N['click']} {dims} ({hl})"
            fits = '1200 x 800 / 1200 x 1000' + (' / 760 x 1140' if a['sku'].endswith('L') else '')
        else:
            name = f"{N['runner']} {dims}"
            fits = f"{a['L']} x {a['L']}" if a['sku'] != 'QPRUN6080M' else '600 x 800'
        rows.append((w['fits'], fits + ' mm'))
    if k == 'lid':
        name = f"{N[k]} {a['L']} x {a['W']} mm, {fmt_dec(a['H'], lang)} mm {w['thick']}"
    if k in ('driptray', 'grating'):
        name += ' ' + w['on3runners']
    if k == 'grid':
        name += ' ' + w['on9feet']
    img = ACC_PHOTO.get(k)
    if a.get('img'):
        img = '/assets/img/acc/' + slugify(T['en']['acc_name'][k if not a['sku'].startswith('QP-RUN') else 'click'] + ' ' + a['sku']) + '.webp'
        a['_img_file'] = img
    if a['sku'].lower() in ACC_SKU_PHOTO:
        img = f"/assets/img/acc/photo-{a['sku'].lower()}.webp"
    name = name.replace(' mm', '\u00a0mm')   # keep the unit with its number
    return {'anchor': slugify(a['sku']), 'sku': a['sku'], 'name': name, 'rows': rows, 'img': img, 'ph': Markup(ACC_ILLU[k]),
            'price': fmt_price(a['price'], lang) if a.get('price') else None, 'per_piece': k == 'runner'}


def render_acc(pid, lang):
    t = T[lang]
    page = page_obj(pid, lang)
    fm = page['fm']
    crumbs = crumbs_for(pid, lang)
    body = md_html(CONTENT[lang][pid]['body'], lang)
    jl = [crumbs_ld(crumbs)]
    if page['faq']:
        jl.append(faq_ld(page['faq']))
    kinds = PAGES[pid].get('acc')
    items, cats = [], []
    if kinds:
        order = {'driptray': 0, 'grating': 1, 'grid': 2}
        sel = [a for a in ACCS if a['kind'] in kinds]
        sel.sort(key=lambda a: (order.get(a['kind'], 0), a['L'], a['W'], a['sku']))
        items = [acc_item(a, lang) for a in sel]
    else:
        imgs = {'acc-runners': '/assets/img/acc/' + slugify('Click-on runner QP-RUN-L') + '.webp', 'acc-collars': ACC_PHOTO['collar'],
                'acc-lids': ACC_PHOTO['lid'], 'acc-freezer': ACC_PHOTO['freezer'], 'acc-drip': ACC_PHOTO['driptray']}
        for p_, ic in ACC_DEF:
            kind = PAGES[p_]['acc'][0]
            cats.append({'url': url(p_, lang), 'label': short_title(p_, lang), 'sub': _first_sentence(CONTENT[lang][p_]['fm']['lead']), 'icon': ic,
                         'img': acc_tile(imgs.get(p_)), 'ph': Markup(ACC_ILLU[kind])})
        cats.append({'url': url('used', lang), 'label': short_title('used', lang), 'sub': (re.split(r'(?<=[.!?])\s+', CONTENT[lang]['used']['fm']['lead'].strip()) + [''])[1] or _first_sentence(CONTENT[lang]['used']['fm']['lead']), 'icon': 'recycle',
                     'img': acc_tile(MODEL_BY_ID['qp1210hb3rr']['img_url']), 'ph': None})
    check_meta(pid, lang, fm['title'], fm['description'])
    ctx = base_ctx(pid, lang, fm['title'], fm['description'], section='pallets', jsonld=jl, tpl='acc')
    ctx.update(page=page, crumbs=crumbs, body=body, items=items, acc_cats=cats, side_nav=side_nav_for(pid, lang))
    return env.get_template('acc.html').render(**ctx)


# photos from the Q-Pall shoot (Noah, update 19): office-open, team, custom-logo, recycled-input, pallet-detail
# Ultra page: the two versions next to a short explanation (update 30, second analysis: 2 cards in a 4-column grid)
ULTRA_TXT = {
    'nl': {'h': 'Twee **uitvoeringen**', 'p': 'Beide uitvoeringen meten 1200 x 1000 x 165 mm en dragen 7.500 kg statisch en 1.500 kg dynamisch. Met 6 onderlatten draagt de Ultra pallet 1.375 kg in de stelling, met 3 onderlatten 1.250 kg.'},
    'en': {'h': 'Two **versions**', 'p': 'Both versions measure 1200 x 1000 x 165 mm and carry 7,500 kg static and 1,500 kg dynamic. With 6 runners the Ultra pallet carries 1,375 kg in racking, with 3 runners 1,250 kg.'},
    'de': {'h': 'Zwei **Ausführungen**', 'p': 'Beide Ausführungen messen 1200 x 1000 x 165 mm und tragen 7.500 kg statisch und 1.500 kg dynamisch. Mit 6 Kufen trägt die Ultra-Palette 1.375 kg im Regal, mit 3 Kufen 1.250 kg.'},
    'fr': {'h': 'Deux **versions**', 'p': 'Les deux versions mesurent 1200 x 1000 x 165 mm et supportent 7.500 kg en statique et 1.500 kg en dynamique. Avec 6 semelles, la palette Ultra supporte 1.375 kg en rayonnage, avec 3 semelles 1.250 kg.'},
    'it': {'h': 'Due **versioni**', 'p': 'Entrambe le versioni misurano 1200 x 1000 x 165 mm e sopportano 7.500 kg in statica e 1.500 kg in dinamica. Con 6 slitte il pallet Ultra sopporta 1.375 kg su scaffale, con 3 slitte 1.250 kg.'},
    'es': {'h': 'Dos **versiones**', 'p': 'Ambas versiones miden 1200 x 1000 x 165 mm y soportan 7.500 kg en estática y 1.500 kg en dinámica. Con 6 patines, el palet Ultra soporta 1.375 kg en estantería; con 3 patines, 1.250 kg.'},
}
PAGE_PHOTO = {'about': 'hq-corner', 'about-local': 'local', 'about-sustainability': 'seaturtle', 'careers': 'team', 'about-custom': 'custom-logo',
              'job-inside-sales': 'office-open'}
# two photos after the first list: (photo, photo, i18n key of the alt text, i18n key of the caption)
PAGE_DUO = {'about': ('hq-aerial', 'hq-terrace', 'hq_photo_alt', 'hq_photo_caption'),
            'job-inside-sales': ('office-sales', 'office-desk', 'job_photo_alt', 'job_photo_caption'),   # kantoorfoto's van Noah (update 19)
            'about-sustainability': ('recycled-input', 'pallet-detail', 'recycle_photo_alt', 'recycle_photo_caption')}
# where the two photos go: after the first list (default) or at the end of the first section ('h2:2' = before the 2nd heading)
PAGE_DUO_AT = {'about-sustainability': 'h2:2'}
HERO_MODELS = {'light': 'qp1208lb9fr', 'medium': 'qp1208mb3r-cd-ao', 'heavy': 'qp1208hb3rr'}
HERO_PHOTO = {'light': 0, 'medium': 0, 'heavy': 3}   # gallery index of the photo shown in the homepage hero card
EU_MAP = Markup(open(os.path.join(ROOT, 'data', 'europe-map-light.svg'), encoding='utf-8').read()) if os.path.exists(os.path.join(ROOT, 'data', 'europe-map-light.svg')) else ''


def eu_map(lang):
    """The factory map with the texts of this language (see tools/map_light.py)."""
    t = T[lang]
    s = str(EU_MAP).replace('__TITLE__', str(escape(t['map_title'])))
    for c in FACTORIES + ['V']:
        L = LOCATIONS[c]
        s = s.replace(f'__L_{c}__', str(escape(f"{L['name']}, {COUNTRY[L['cc']][lang]}{chr(160) if lang == 'fr' else ''}: {t['map_show'] if c != 'V' else t['footer_hq']}")))
    return Markup(s)


def render_home(lang):
    t = T[lang]
    pid = 'home'
    page = page_obj(pid, lang)
    fm = page['fm']
    hero = []
    for c in CLASSES:
        m = MODEL_BY_ID[HERO_MODELS[c['key']]]
        gi = HERO_PHOTO.get(c['key'], 0)
        g = m['gallery'][min(gi, len(m['gallery']) - 1)] if m['gallery'] else {'md': m['img_url'], 'lg': m['img_url']}
        hw, hh = HERO_SIZE.get(c['key'], (960, 450))
        hero.append({'key': c['key'], 'name': c['name'], 'model': m, 'url': m['url'][lang],
                     'md': g['md'], 'lg': g['lg'], 'img': f"/assets/img/hero/{c['key']}", 'w': hw, 'h': hh,
                     'title': m['name'][lang], 'static': fmt_int(m['static'][1], lang), 'dynamic': fmt_int(m['dynamic'][1], lang),
                     'racking': fmt_int(m['racking'][1], lang) if m['racking'] else None, 'new': m['is_new'],
                     'sku': m['sku_txt'], 'price': m['txt'][lang]['price']})
    jl = [org_ld(lang), website_ld(lang)]
    if page['faq']:
        jl.append(faq_ld(page['faq']))
    check_meta(pid, lang, fm['title'], fm['description'])
    ctx = base_ctx(pid, lang, fm['title'], fm['description'], jsonld=jl, preload=hero[1]['img'] + '-960.avif', tpl='home')
    hi = hero[1]['img']
    ctx['meta']['preload_srcset'] = f'{hi}-640.avif 640w, {hi}-960.avif 960w, {hi}-1280.avif 1280w'
    ctx['meta']['preload_type'] = 'image/avif'   # browsers without AVIF skip the preload and use the WebP in <picture>
    ctx['meta']['preload_sizes'] = '(min-width:1100px) 620px, 94vw'
    sec = []
    order = ['logistics', 'chemical', 'food', 'pharma', 'beverage', 'pooling', 'retail']
    for s in sorted(SECTORS, key=lambda x: order.index(x['key']) if x['key'] in order else 99):
        sec.append({'key': s['key'], 'label': t['sector_name'][s['key']], 'url': url('sector-' + s['key'], lang), 'img': NAV_SECTOR_IMG[s['key']],
                    'sub': fm['sectors']['tiles'][s['key']]['sub'], 'big': fm['sectors']['tiles'][s['key']].get('big')})
    # customer cases (update 19): each card links to its news article; the client name replaces the news tag
    nl_by_id = {n['id']: n for n in news_list(lang)}
    cases = [dict(nl_by_id[c['id']], tag=c['client'], title=c['title'], lead=c['text'], date=None)
             for c in fm.get('cases', {}).get('items', []) if c['id'] in nl_by_id]
    if len(cases) != len(fm.get('cases', {}).get('items', [])):
        WARN.append(f'home/{lang}: case without news article')
    ctx.update(cases=cases, page=page, hero=hero, promo_img=MODEL_BY_ID['qp1210mb3r-cd-ao']['gallery'][0], guides=[g for g in guides_list(lang) if g['id'] != 'guide-ppwr'], sector_tiles=sec, eu_map=eu_map(lang),
               factories=[{'code': c, 'name': LOCATIONS[c]['name'], 'cc': LOCATIONS[c]['cc'], 'country': COUNTRY[LOCATIONS[c]['cc']][lang]}
                          for c in FACTORIES])
    return env.get_template('home.html').render(**ctx)


def render_404(lang):
    t = T[lang]
    ctx = base_ctx('home', lang, t['notfound_title'] + ' – Q-Pall', t['notfound_text'], noindex=True, tpl='404')
    ctx['meta']['canonical'] = None       # a 404 page has no canonical and no language versions (iClicks, update 13)
    ctx['meta']['alternates'] = []
    ctx.update(page={'h1': t['notfound_title']})
    return env.get_template('404.html').render(**ctx)


# update 33: extra search words per language, so the instant search also finds adjectives ("nestbaar", "zware"),
# synonyms ("europallet" = 1200 x 800), sizes in cm ("120x80") and the service pages (quote, contact, calculator ...).
# 'stop' words are ignored, 'gen' words (pallet, kunststof ...) only count when nothing else is typed.
SEARCH_X = {
 'nl': {'stop': 'voor met van een de het en in op of naar die dat', 'gen': 'pallet pallets kunststof kunststoffen plastic',
        'type': {'nestable': 'nestbaar nestbare', 'hygienic': 'hygiënisch hygiënische haccp', 'export': 'export eenmalig wegwerp',
                 'antislip': 'antislip anti-slip slipvrij', 'cp': 'cp chemie chemisch', 'display': 'display winkel', 'block': 'blok'},
        'class': {'light': 'licht lichte lichtgewicht', 'medium': 'middelzwaar', 'heavy': 'zwaar zware'},
        'rack': 'stelling stellingen stellingpallet',
        'svc': {'quote': 'offerte prijsopgave aanvragen prijs', 'contact': 'contact telefoon bellen e-mail adres', 'calc': 'calculator laadcalculator berekenen container vrachtwagen',
                'used': 'gebruikt gebruikte tweedehands', 'dealers': 'dealer dealers', 'careers': 'vacature vacatures werken baan solliciteren',
                'acc': 'accessoires toebehoren', 'transport': 'transport ophalen vervoerder'}},
 'en': {'stop': 'for with of a an the and in on or to', 'gen': 'pallet pallets plastic',
        'type': {'nestable': 'nestable nesting', 'hygienic': 'hygienic haccp', 'export': 'export one-way',
                 'antislip': 'anti-slip antislip non-slip', 'cp': 'cp chemical', 'display': 'display retail', 'block': 'block'},
        'class': {'light': 'light lightweight', 'medium': 'medium', 'heavy': 'heavy heavy-duty'},
        'rack': 'racking rackable rack',
        'svc': {'quote': 'quote quotation request price', 'contact': 'contact phone call email address', 'calc': 'calculator load container truck',
                'used': 'used second-hand', 'dealers': 'dealer dealers distributor', 'careers': 'jobs job vacancy vacancies careers',
                'acc': 'accessories', 'transport': 'transport collection pickup carrier'}},
 'de': {'stop': 'für mit von ein eine einen der die das und in auf oder zu', 'gen': 'palette paletten kunststoff kunststoffpalette kunststoffpaletten plastik',
        'type': {'nestable': 'nestbar nestbare', 'hygienic': 'hygienisch hygiene haccp', 'export': 'einweg export',
                 'antislip': 'antirutsch rutschfest', 'cp': 'cp chemie chemisch', 'display': 'display', 'block': 'block'},
        'class': {'light': 'leicht leichte', 'medium': 'mittelschwer', 'heavy': 'schwer schwere schwerlast'},
        'rack': 'regal regale regalfähig',
        'svc': {'quote': 'angebot anfrage preis', 'contact': 'kontakt telefon anrufen e-mail adresse', 'calc': 'rechner ladungsrechner berechnen container lkw',
                'used': 'gebraucht gebrauchte', 'dealers': 'händler vertrieb', 'careers': 'stellen stellenangebote jobs karriere bewerbung',
                'acc': 'zubehör', 'transport': 'transport abholung spedition'}},
 'fr': {'stop': 'pour avec de des du un une le la les et en à au aux ou', 'gen': 'palette palettes plastique plastiques',
        'type': {'nestable': 'emboîtable emboîtables', 'hygienic': 'hygiénique hygiéniques haccp', 'export': 'export perdue',
                 'antislip': 'antidérapant antidérapante antidérapantes', 'cp': 'cp chimie chimique', 'display': 'display présentoir', 'block': 'bloc blocs'},
        'class': {'light': 'légère léger', 'medium': 'moyenne', 'heavy': 'lourde lourd'},
        'rack': 'rayonnage rack',
        'svc': {'quote': 'devis demande prix', 'contact': 'contact téléphone appeler e-mail adresse', 'calc': 'calculateur calcul conteneur camion',
                'used': 'occasion usagée usagées', 'dealers': 'revendeur revendeurs distributeur', 'careers': 'emploi emplois offres carrière recrutement',
                'acc': 'accessoires', 'transport': 'transport enlèvement transporteur'}},
 'it': {'stop': 'per con di da un una il lo la le i gli e in o al', 'gen': 'pallet bancale bancali plastica',
        'type': {'nestable': 'incastrabile incastrabili', 'hygienic': 'igienico igienici igienica haccp', 'export': 'esportazione export',
                 'antislip': 'antiscivolo', 'cp': 'cp chimico chimica', 'display': 'espositore espositori display', 'block': 'blocco blocchi'},
        'class': {'light': 'leggero leggera leggeri', 'medium': 'medio', 'heavy': 'pesante pesanti'},
        'rack': 'scaffale scaffali scaffalatura',
        'svc': {'quote': 'preventivo richiesta prezzo', 'contact': 'contatto contatti telefono email indirizzo', 'calc': 'calcolatore calcolo container camion',
                'used': 'usato usati', 'dealers': 'rivenditore rivenditori distributore', 'careers': 'lavoro offerte carriera candidatura',
                'acc': 'accessori', 'transport': 'trasporto ritiro vettore'}},
 'es': {'stop': 'para con de del un una el la los las y en o al', 'gen': 'palet palets paleta paletas plástico',
        'type': {'nestable': 'encajable encajables', 'hygienic': 'higiénico higiénicos haccp', 'export': 'exportación export',
                 'antislip': 'antideslizante antideslizantes', 'cp': 'cp químico química', 'display': 'expositor expositores display', 'block': 'bloque bloques'},
        'class': {'light': 'ligero ligera ligeros', 'medium': 'medio', 'heavy': 'pesado pesada pesados'},
        'rack': 'estantería estanterías rack',
        'svc': {'quote': 'presupuesto solicitud precio', 'contact': 'contacto teléfono llamar email dirección', 'calc': 'calculadora cálculo contenedor camión',
                'used': 'usado usados segunda mano', 'dealers': 'distribuidor distribuidores', 'careers': 'empleo empleos ofertas trabajo',
                'acc': 'accesorios', 'transport': 'transporte recogida transportista'}},
}


def _size_words(key, lang):
    L, W = key.split('x')
    cm = lambda v: str(int(v) // 10) if int(v) % 10 == 0 else str(int(v) / 10).rstrip('0')
    return ' '.join([f'{L}x{W}', f'{W}x{L}', f'{cm(L)}x{cm(W)}', f'{cm(W)}x{cm(L)}', T[lang]['size_nick'][key]])


def search_records():
    """Light-weight data per language for the instant search (before the Pagefind index answers):
    p = products, c = categories and service pages, stop/gen = words the search ignores (update 33)."""
    for lang in LANGS:
        t, X = T[lang], SEARCH_X[lang]
        out = []
        for m in MODELS:
            words = [m['size_label'], _size_words(m['size'], lang), m['class'], X['class'][m['class']],
                     ' '.join(t['type_name'][ty] + ' ' + X['type'].get(ty, '') for ty in m['types']),
                     X['rack'] if m['rackable'] else '', ' '.join(v['sku'] for v in m['variants'])]
            out.append({'t': re.sub(' – ' + re.escape(m['sku']) + '$', '', m['name'][lang]), 'u': m['url'][lang], 'i': m['img_sm'],
                        's': f"{t['art_nr_short']} {m['sku_txt']} · {m['size_label']} · {m['class'].capitalize()} · {t['static']} {m['txt'][lang]['static_short']}",
                        'k': re.sub(r'\s+', ' ', ' '.join(words)).strip(), 'x': [v['sku'].lower() for v in m['variants']], 'n': t['size_nick'][m['size']]})
        # accessories by article number too (update 53): a search for QPRUN1111 lands on that runner on its page
        acc_page = {k: pid for pid, pg in PAGES.items() if pg.get('tpl') == 'acc' and pg.get('acc') for k in pg['acc']}
        for a in ACCS:
            pid = acc_page.get(a['kind'])
            if not pid:
                continue
            it = acc_item(a, lang)
            out.append({'t': str(it['name']).replace('\u00a0', ' '), 'u': url(pid, lang) + '#' + it['anchor'], 'i': it.get('img') or '',
                        's': f"{t['art_nr_short']} {a['sku']} · {short_title(pid, lang)}",
                        'k': f"{short_title(pid, lang)} {a['sku']}", 'x': [a['sku'].lower()], 'n': ''})
        cats = []
        for pid, pg in PAGES.items():
            if pg.get('tpl') != 'listing' or pid not in CONTENT[lang]:
                continue
            spec = pg['listing']
            ms = listing_models(spec)
            if not ms:
                continue
            k = [plain(CONTENT[lang][pid]['fm'].get('h1', ''))]
            if 'size' in spec:
                k.append(_size_words(spec['size'], lang))
            if 'type' in spec:
                k.append(X['type'].get(spec['type'], ''))
            if 'class' in spec:
                k.append(X['class'][spec['class']])
            nick = t['size_nick'][spec['size']] if 'size' in spec else ''
            cats.append({'t': short_title(pid, lang), 'u': url(pid, lang), 's': mcount(len(ms), lang), 'k': ' '.join(k), 'n': nick, 'all': not spec})
        for pid, words in X['svc'].items():
            if pid in PAGES and pid in CONTENT[lang]:
                cats.append({'t': short_title(pid, lang), 'u': url(pid, lang), 's': plain(CONTENT[lang][pid]['fm'].get('h1', '')), 'k': words, 'svc': True})
        json.dump({'p': out, 'c': cats, 'stop': X['stop'].split(), 'gen': X['gen'].split()},
                  open(os.path.join(OUT, f'assets/search-{lang}.json'), 'w'), ensure_ascii=False, separators=(',', ':'))


# ------------------------------------------------------------------------------------------------ main
def main():
    import build_assets as BA
    keep = os.environ.get('QP_KEEP_IMAGES') == '1'
    BA.clean_out(OUT, keep)
    BA.copy_static(ROOT, OUT)
    if not keep:
        BA.build_images(ROOT, OUT, MODELS, ACCS, acc_item, LANGS, HERO_MODELS)
    BA.copy_downloads(ROOT, OUT)
    # Datasheets of articles that left the site (EXCLUDE_VARIANTS) stay in data/datasheets until someone deletes them.
    # Published, such a file would win from its 301 in _redirects (Netlify serves an existing file first): leave them out.
    want = {datasheet_path(m, l).lstrip('/') for m in MODELS for l in LANGS}
    stale = [f for f in glob.glob(os.path.join(OUT, 'downloads', 'datasheets', '*', '*.pdf'))
             if os.path.relpath(f, OUT).replace(os.sep, '/') not in want]
    for f in stale:
        os.remove(f)
    if stale:
        print(f'stale datasheets left out of the site: {len(stale)} (delete them from data/datasheets)')
    count = 0
    page_order = []
    for pid, p in PAGES.items():
        page_order.append(pid)
        for lang in LANGS:
            if p['tpl'] == 'product':
                h = render_product(MODEL_BY_ID[p['model']], lang)
            elif p['tpl'] == 'listing':
                h = render_listing(pid, lang)
            else:
                h = render_page(pid, lang)
            write(p['path'][lang], h)
            count += 1
    for lang in LANGS:
        h = re.sub(r'\n\s*\n+', '\n', render_404(lang))
        dest = os.path.join(OUT, PREFIX[lang], '404.html')
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, 'w').write(h)
    search_records()
    BA.write_seo_files(OUT, page_order, PAGES, MODEL_BY_ID, abs_url)
    BA.write_netlify(OUT)
    import mailgen, sys
    mailgen.write(sys.modules[__name__], OUT)     # quote confirmation e-mail: templates + Netlify function (update 37)
    json.dump({'models': [{'id': m['id'], 'sku': m['sku'], 'family': m['family'], 'name': m['name'], 'url': m['url'], 'txt': {l: {k: v for k, v in m['txt'][l].items() if k not in ('desc_html',)} for l in LANGS}}
                          for m in MODELS]}, open(os.path.join(ROOT, 'data/_build_models.json'), 'w'), ensure_ascii=False, default=str)
    print(f'pages written: {count}  models: {len(MODELS)}  languages: {len(LANGS)}  out: {OUT}  v={VERSION}')
    if FALLBACK:
        fl = {}
        for l, p in FALLBACK:
            fl.setdefault(l, []).append(p)
        print('CONTENT FALLBACK (EN used):', {k: len(v) for k, v in fl.items()})
    if MISSING:
        ml = {}
        for l, k in MISSING:
            ml.setdefault(l, 0)
            ml[l] += 1
        print('UI STRINGS MISSING (EN used):', ml)
    if WARN:
        print('WARNINGS (%d):' % len(WARN))
        for w in WARN[:80]:
            print('  -', w)


if __name__ == '__main__':
    main()
