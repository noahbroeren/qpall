#!/usr/bin/env python3
"""301 redirects from every URL of the old qpall.com (sitemap 19-10-2026) to the best page of the new site.

Input : data/oude-site/producten.txt  product pages (group, NL path, article number on the old page)
        data/oude-site/paginas.txt    other pages per language (group | nl | en | de | fr | it | es), files,
                                      PPWR declarations (P lines) and the old transport pages (T line)
Output: data/redirects-extra.txt      (build.py puts these rules at the top of _redirects)

Product pages: the other languages are derived from the NL slug with the word list below (checked against
the old sitemap: 670 of 670 URLs). The article number decides the new model page; accessories go to their
accessory page. Old paths that still exist on the new site (same path) get no rule.
Run after changing the page structure:  python3 tools/redirects_qpall.py  &&  python3 tools/redirects_check.py
"""
import os, re, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from site_config import PAGES, PREFIX, LANGS, CATALOG_FILES, NEWS_ITEMS   # noqa: E402

D = os.path.join(ROOT, 'data', 'oude-site')
OTHER = ['en', 'de', 'fr', 'it', 'es']

# ---------------------------------------------------------------- old product slugs NL -> other languages
HEADS = [  # order matters: longest first
    ('gebruikte-kunststof-pallet', ['gebruikte-kunststof-pallet'] * 5),
    ('kunststof-poolpallet', ['plastic-pool-pallet', 'kunststoff-poolpalette', 'palette-de-pooling-en-plastique', 'pallet-in-plastica-per-pooling', 'pale-de-plastico-para-pooling']),
    ('kunststof-vouwrand', ['plastic-pallet-collar', 'kunststoff-faltaufsatzrahmen', 'rehausse-pliable-en-plastique', 'collare-pieghevole-in-plastica', 'collarin-plegable-de-plastico']),
    ('kunststof-deksel', ['plastic-lid', 'kunststoffdeckel', 'couvercle-en-plastique', 'coperchio-in-plastica', 'tapa-de-plastico']),
    ('kunststof-rooster', ['plastic-grid', 'kunststoffrost', 'grille-en-plastique', 'griglia-in-plastica', 'rejilla-de-plastico']),
    ('kunststof-pallet', ['plastic-pallet', 'kunststoffpalette', 'palette-en-plastique', 'pallet-in-plastica', 'pale-de-plastico']),
    ('display-pallet', ['display-pallet', 'displaypalette', 'palette-de-presentation', 'pallet-display', 'pale-de-exposicion']),
    ('hygienische-pallet', ['hygienic-pallet', 'hygienische-palette', 'palette-hygienique', 'pallet-igienico', 'pale-higienico']),
    ('industrie-pallet', ['industrial-pallet', 'industriepalette', 'palette-industrielle', 'pallet-industriale', 'pale-industrial']),
    ('freezer-spacer', ['freezer-spacer', 'gefrierabstandhalter', 'entretoise-de-congelation', 'distanziatore-per-congelatore', 'separador-de-congelador']),
    ('lekbak', ['drip-tray', 'auffangwanne', 'bac-de-retention', 'vasca-di-raccolta', 'bandeja-de-retencion']),
    ('gegalvaniseerd-rooster', ['galvanized-grating', 'verzinktes-gitter', 'caillebotis-galvanise', 'griglia-zincata', 'rejilla-galvanizada']),
    ('onderlat', ['bottom-runner', 'unterkufe', 'semelle-inferieure', 'listello-inferiore', 'patin-inferior']),
    ('kliklat', ['click-runner', 'klickleiste', 'latte-a-clipser', 'listello-a-scatto', 'liston-de-fijacion']),
    ('h1-europallet', ['h1-euro-pallet', 'h1-europalette', 'palette-europe-h1', 'europallet-h1', 'pale-europeo-h1']),
]
TOKENS = [
    ('open-dek', ['open-deck', 'offenes-deck', 'plateau-ajoure', 'piano-aperto', 'cubierta-abierta']),
    ('gesloten-dek', ['closed-deck', 'geschlossenes-deck', 'plateau-ferme', 'piano-chiuso', 'cubierta-cerrada']),
    ('intern-gebruik', ['multiple-use', 'wiederholte-verwendung', 'utilisation-repetee', 'uso-ripetuto', 'uso-repetido']),
    ('pootjes', ['feet', 'fusse', 'plots', 'piedi', 'pies']),
    ('onderlatten', ['runners', 'kufen', 'semelles', 'listelli', 'patines']),
    ('light', ['light', 'light', 'legere', 'light', 'ligero']),
    ('medium', ['medium', 'medium', 'medium', 'medium', 'medio']),
    ('heavy', ['heavy', 'heavy', 'lourde', 'heavy', 'pesado']),
    ('export', ['single-use', 'einmalige-verwendung', 'usage-unique', 'uso-unico', 'uso-unico']),
]
CP_HEAD = ['cp{n}-pallet', 'cp{n}-palette', 'palette-cp{n}', 'pallet-cp{n}', 'pale-cp{n}']


def translate(nl_slug, li):
    """NL product slug -> slug in OTHER[li]."""
    s = nl_slug
    m = re.match(r'cp(\d)-pallet-(.*)', s)
    if m:
        head, rest = CP_HEAD[li].format(n=m.group(1)), m.group(2)
    else:
        for h, tr in HEADS:
            if s.startswith(h + '-'):
                head, rest = tr[li], s[len(h) + 1:]
                break
        else:
            raise ValueError('no head for ' + s)
    for tok, tr in TOKENS:
        rest = re.sub(r'(^|-)' + tok + r'(?=-|$)', lambda mo: mo.group(1) + tr[li], rest)
    return head + '-' + rest


# ---------------------------------------------------------------- targets
def url(pid, lang):
    return '/' + PAGES[pid]['path'][lang]


MODELS = json.load(open(os.path.join(ROOT, 'data', '_build_models.json')))['models']
DATA = json.load(open(os.path.join(ROOT, 'data', 'products.json')))
SKU = {}
for m in DATA['models']:
    for v in m['variants']:
        SKU[v['sku']] = m['id']
# every article number has its own page since round 9: send an old product URL to the page of exactly that article
SKU.update({m['sku']: m['id'] for m in MODELS if m.get('sku')})
BASE = {}
FAMILY_IDS = {m['id'] for m in DATA['models']}
for s, mid in SKU.items():
    b = re.sub(r'^[0-9N]+\.', '', s)
    if b not in BASE or (mid in FAMILY_IDS and BASE[b] not in FAMILY_IDS):   # prefer the main article of a family
        BASE[b] = mid
MURL = {m['id']: m['url'] for m in MODELS}
ACC_KIND = {a['sku']: a['kind'] for a in DATA['accessories']}
ACC_PAGE = {'collar': 'acc-collars', 'lid': 'acc-lids', 'freezer': 'acc-freezer', 'driptray': 'acc-drip', 'grating': 'acc-drip',
            'grid': 'acc-drip', 'runner': 'acc-runners'}
SPECIAL_SKU = {'QPFSIII1210-black': 'acc-freezer', 'QPRUN1111L': 'acc-runners', 'QPRUN1212L': 'acc-runners', 'QPRUN-L': 'acc-runners',
               'QPRUN-H': 'acc-runners', 'GKSP6040M4F': 'used', 'Bottleguard': 'sector-beverage'}
H1_MODEL = next((m['id'] for m in DATA['models'] if m.get('special') == 'h1'), None)


def product_target(sku, lang):
    if sku in SKU:
        return MURL[SKU[sku]][lang]
    b = re.sub(r'^[0-9N]+\.', '', sku)
    if b in BASE:
        return MURL[BASE[b]][lang]
    if sku in ACC_KIND:
        return url(ACC_PAGE[ACC_KIND[sku]], lang)
    if sku in SPECIAL_SKU:
        return url(SPECIAL_SKU[sku], lang)
    if sku == 'H1':
        return MURL[H1_MODEL][lang] if H1_MODEL else url('type-hygienic', lang)
    return None


# old non-product pages (group id) -> new page id ('news' items keep their path)
GROUP = {
    # news (update 11): every old news article now exists on the new site under its own URL (NEWS_ITEMS), so no redirect
    0: 'home', 1: 'dealers', 2: 'careers', 3: 'careers', 4: 'ultra', 5: 'pallets', 6: 'size-600x400', 7: 'size-1200x800', 8: 'type-cp',
    9: 'size-600x800', 10: 'size-1200x1000', 11: 'type-display', 12: 'size-760x1140', 13: 'size-1200x1200', 14: 'type-export',
    15: 'size-1100x1100', 16: 'size-1140x1140', 17: 'type-hygienic', 18: 'size-1300x1100', 19: 'type-nestable', 20: 'type-block',
    21: 'about', 22: 'about-sustainability', 23: 'about-local', 24: 'about-custom', 25: 'about-glossary', 26: 'about-load', 27: 'sectors',
    28: 'sector-chemical', 29: 'sector-retail', 30: 'sector-pharma', 31: 'sector-beverage', 32: 'sector-food', 33: 'sector-logistics',
    34: 'sector-pooling', 35: 'news', 36: 'contact', 37: 'quote', 38: 'news-economical', 39: 'class-light', 40: 'class-medium',
    41: 'class-heavy', 42: 'acc-collars', 43: 'acc-freezer', 44: 'acc-lids', 45: 'acc', 46: 'acc-drip', 47: 'acc-runners', 48: 'used',
    49: 'size-1200x800', 50: 'pallets', 51: 'used', 52: 'used', 53: 'used', 54: 'used', 126: 'sector-beverage', 127: 'news-stackup',
    128: 'news-process', 129: 'news-vally', 130: 'news-logistics-update', 131: 'news-local', 132: 'news-auchan', 133: 'news-antislip-grip',
    134: 'news-bestpal-mpackaging', 135: 'news-ppwr', 136: 'news-euro-export', 137: 'news-future-logistics', 138: 'news-scopac',
    139: 'news-local-resilience', 140: 'news-sitl-2025', 141: 'news-poolpallet', 142: 'news-local-sustainability', 143: 'news-ric',
    144: 'news-green-logistics', 145: 'news-mega-order', 146: 'news-ecovadis-silver', 147: 'news-choosing-pallet', 148: 'news-medium-gen3',
    149: 'news-hdpe', 150: 'news-price-wood', 151: 'news-haccp', 152: 'news-durability', 153: 'news-choosing-size', 154: 'news-heavy-range',
    155: 'news-qused', 156: 'news-medium-4840', 157: 'news-covid', 158: 'news-goplastic', 159: 'news-hq', 160: 'news-brexit',
    161: 'news-which-pallet', 162: 'news-recycling', 163: 'news-damage', 164: 'news-industries', 165: 'news-cleaning',
    166: 'news-regulations', 167: 'news-horeca', 168: 'news-esd', 169: 'news-h1', 170: 'news-antislip-mandatory', 171: 'news-antistatic',
    172: 'news-environment', 173: 'news-used-types', 174: 'news-why-plastic', 175: 'news-stacking', 176: 'news-goodwood',
    177: 'news-heavy-family', 208: 'used', 212: 'sector-food', 213: 'guide-sizes', 220: 'sector-food', 221: 'guide-sizes',
    230: 'sector-food', 231: 'guide-sizes', 232: 'sector-food', 233: 'guide-sizes', 234: 'sector-food', 235: 'guide-sizes', 251: 'type-cp',
    252: 'type-cp', 253: 'type-cp',
}
TRANSPORT_ID = {'aigrefeuille-sur-maine': 'aigrefeuille', 'les-borges-blanques': 'borges-blanques'}


def norm(p):
    return p.rstrip('/') or '/'


def main():
    rules, seen, old_urls = [], set(), []

    def add(src, dst, note=None):
        src = norm(src)
        old_urls.append(src)
        if src in seen:
            return
        seen.add(src)
        if norm(dst.split('?')[0]) == src:      # same path on the new site: no rule needed
            return
        rules.append((src, dst))

    # products
    for line in open(os.path.join(D, 'producten.txt'), encoding='utf-8'):
        if line.startswith('#') or not line.strip():
            continue
        gid, path, sku = line.split()[:3]
        if ':' in path:                          # only in one language: "de:/de/bottleguard-...-239"
            lang, p = path.split(':', 1)
            add(p, product_target('Bottleguard' if 'bottleguard' in p else sku, lang))
            continue
        tgt = {l: product_target(sku, l) for l in LANGS}
        if tgt['nl'] is None:
            print('NO TARGET', gid, path, sku)
            continue
        add(path, tgt['nl'])
        slug = path.strip('/')
        for i, l in enumerate(OTHER):
            add(f'/{l}/' + translate(slug, i), tgt[l])
    # other pages, files, PPWR, transport
    for line in open(os.path.join(D, 'paginas.txt'), encoding='utf-8'):
        line = line.rstrip('\n')
        if line.startswith('#') or not line.strip():
            continue
        parts = line.split('|')
        if parts[0] == 'F':
            p = parts[1]
            if 'terms-and-conditions' in p:
                add(p, p)                        # same file is published again (root/files/)
            else:
                lang = re.search(r'-(nl|en|de|fr|it|es)\.pdf$', p).group(1)
                add(p, '/' + CATALOG_FILES[lang])
            continue
        if parts[0] == 'P':
            nnn = parts[1]
            for suf in parts[2].split(','):
                add(f'/files/qpall-ppwr-eu-doc-pg-{nnn}-v02{suf}.pdf', f'/downloads/ppwr/QPALL_PPWR_EU_DoC_PG-{nnn}_V02.pdf')
            continue
        if parts[0] == 'X':
            nnn = re.search(r'pg-(\d{3})', parts[1]).group(1)
            add(parts[1], f'/downloads/ppwr/QPALL_PPWR_EU_DoC_PG-{nnn}_V02.pdf')
            continue
        if parts[0] == 'T':
            for site in parts[1].split(','):
                sid = TRANSPORT_ID.get(site, site)
                add('/register-transport-' + site, url('transport', 'nl') + '?locatie=' + sid)
                for l in OTHER:
                    add(f'/{l}/register-transport-' + site, url('transport', l) + '?locatie=' + sid)
            add('/register-transportation', url('transport', 'nl'))
            for l in OTHER:
                add(f'/{l}/register-transportation', url('transport', l))
            continue
        gid = int(parts[0])
        pid = GROUP.get(gid)
        if not pid:
            print('NO GROUP', gid, parts[1])
            continue
        for l, p in zip(LANGS, parts[1:7]):
            for one in p.split():                # "/contactanos /contacte": two old paths
                if one == '~':
                    continue
                add(('' if l == 'nl' else '/' + l) + one, url(pid, l))
    # pages of this site that were renamed later (round 8: DE 'Exportpaletten' became 'Einwegpaletten')
    if not any(a == '/de/kunststoffpaletten/exportpaletten' for a, b in rules):
        rules.append(('/de/kunststoffpaletten/exportpaletten', url('type-export', 'de')))
    out = ['# 301-redirects van de oude qpall.com naar de nieuwe site (gemaakt door tools/redirects_qpall.py, niet met de hand wijzigen)',
           f'# {len(rules)} regels; {len(set(old_urls))} oude URL\'s gecontroleerd']
    for a, b in rules:
        out.append(f'{a}  {b}  301')
    open(os.path.join(ROOT, 'data', 'redirects-extra.txt'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    open(os.path.join(D, '_alle-oude-urls.txt'), 'w', encoding='utf-8').write('\n'.join(sorted(set(old_urls))) + '\n')
    print(f'{len(rules)} rules, {len(set(old_urls))} old URLs -> data/redirects-extra.txt')


if __name__ == '__main__':
    main()
