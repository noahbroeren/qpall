#!/usr/bin/env python3
"""Koppel oude productpagina-URL's van qpall.com aan de nieuwe modelpagina's.

Gebruik:
  1. Exporteer alle oude product-URL's (bijv. uit Google Search Console > Pagina's,
     of uit de oude sitemap) naar een tekstbestand, één URL of pad per regel.
  2. python3 tools/redirects-maken.py oude-urls.txt >> data/redirects-extra.txt
  3. python3 build.py   (de regels komen bovenaan in _redirects)

Het script herkent NL-slugs ("kunststof-pallet-1200-x-800-x-150-open-dek-9-pootjes-light-143")
en EN-slugs ("plastic-pallet-1200-x-800-x-150-open-deck-9-feet-light-143").
Niet-herkende URL's worden naar de juiste maatpagina gestuurd, of als commentaar uitgevoerd.
"""
import re
import sys
import os

WORDS = {
    'open': 'open', 'gesloten': 'closed', 'closed': 'closed',
    'onderlatten': 'runners', 'runners': 'runners', 'pootjes': 'feet', 'poten': 'feet', 'feet': 'feet',
}


def parse(path):
    slug = path.strip().rstrip('/').split('/')[-1].lower()
    m = re.search(r'(\d{3,4})-x-(\d{3,4})(?:-x-(\d{2,3}))?', slug)
    if not m:
        return None
    L, W, H = int(m.group(1)), int(m.group(2)), int(m.group(3)) if m.group(3) else None
    deck = 'closed' if ('gesloten' in slug or 'closed' in slug) else ('open' if 'open' in slug else None)
    sm = re.search(r'-(\d)-(onderlatten|runners|pootjes|poten|feet)', slug)
    sup = (WORDS[sm.group(2)], int(sm.group(1))) if sm else None
    cls = next((c for c in ('light', 'medium', 'heavy') if re.search(r'\b' + c + r'\b', slug.replace('-', ' '))), None)
    lang = 'en' if slug.startswith(('plastic', 'display', 'hygienic', 'cp', 'h1-euro', 'industrial', 'cleanroom')) or '/en/' in path else 'nl'
    special = None
    for key, pat in (('hygienic', 'hygien'), ('cleanroom', 'cleanroom'), ('h1', 'h1-'), ('pool', 'pool'), ('display', 'display'), ('industrial', 'industri')):
        if pat in slug:
            special = key
    cp = re.search(r'\bcp(\d)\b', slug.replace('-', ' '))
    if cp:
        special = 'cp' + cp.group(1)
    return dict(L=L, W=W, H=H, deck=deck, sup=sup, cls=cls, lang=lang, special=special, antislip=('antislip' in slug or 'anti-slip' in slug))


def match(path, models):
    p = parse(path)
    if not p:
        return None
    dims = {(p['L'], p['W']), (p['W'], p['L'])}
    cands = [m for m in models if (m['L'], m['W']) in dims or (
        # 1220 x 1020 belongs to 1200 x 1000 page
        False)]
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
        if (m['special'] or None) == p['special']:
            s += 3
        if m['antislip'] == p['antislip']:
            s += 1
        return s
    best = max(cands, key=score)
    if score(best) < 10:
        return None
    return best['url'][p['lang']]


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import build  # noqa: loads models + urls
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for line in open(sys.argv[1], encoding='utf-8'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        path = re.sub(r'^https?://[^/]+', '', line)
        tgt = match(path, build.MODELS)
        if tgt:
            print(f'{path}  {tgt}  301')
        else:
            p = parse(path)
            if p:
                size = f"{max(p['L'], p['W']) if (p['L'], p['W']) != (760, 1140) else 760}"
            print(f'# GEEN MATCH: {path}')
