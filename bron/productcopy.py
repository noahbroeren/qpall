"""Product naming, slugs, meta titles/descriptions and short copy in six languages.

All facts come from data/products.json (PIM export + price list + new 6-language product data).
The long product description is Q-Pall's own SEO text per article (input/producten-6-talen.xlsx).
"""
import re
from site_config import SIZE_BY_KEY, LANGS

COMMA_LANGS = {'nl', 'de', 'fr', 'it', 'es'}


def fmt_int(n, lang=None):
    """Thousands separator: period (client rule) in nl/de/fr/it/es; comma in English,
    where the decimal separator is a point (so 1,375 kg can never read as 1.375 kg)."""
    s = f"{int(n):,}"
    return s if lang == 'en' else s.replace(',', '.')


def fmt_dec(x, lang):
    if x is None:
        return ''
    if float(x).is_integer():
        s = str(int(x))
    else:
        s = f"{x:.2f}".rstrip('0').rstrip('.') if abs(x * 10 - round(x * 10)) > 1e-9 else f"{x:.1f}"
    return s.replace('.', ',') if lang in COMMA_LANGS else s


def fmt_price(p, lang):
    s = f"{p:.2f}"
    if lang in COMMA_LANGS:
        s = s.replace('.', ',')
    if lang in ('de', 'fr', 'es'):
        return s + ' €'
    return '€ ' + s


def rng_txt(r, lang, unit='kg', dec=False):
    if not r:
        return None
    a, b = r
    f = (lambda v: fmt_dec(v, lang)) if dec else (lambda v: fmt_int(v, lang))
    if a == b:
        return f"{f(a)} {unit}"
    return f"{f(a)}–{f(b)} {unit}"


# --------------------------------------------------------------------------- vocabulary
TYPEWORD = {
    'nl': {None: 'Kunststof pallet', 'display': 'Displaypallet', 'hygienic': 'Hygiënische pallet', 'cleanroom': 'Cleanroompallet',
           'pool': 'Kunststof poolpallet', 'h1': 'H1 europallet', 'industrial': 'Industriële pallet', 'us': 'Kunststof pallet',
           'cp1': 'CP1-pallet', 'cp3': 'CP3-pallet', 'cp6': 'CP6-pallet', 'cp9': 'CP9-pallet'},
    'en': {None: 'Plastic pallet', 'display': 'Display pallet', 'hygienic': 'Hygienic pallet', 'cleanroom': 'Cleanroom pallet',
           'pool': 'Plastic pool pallet', 'h1': 'H1 Euro pallet', 'industrial': 'Industrial pallet', 'us': 'Plastic pallet',
           'cp1': 'CP1 pallet', 'cp3': 'CP3 pallet', 'cp6': 'CP6 pallet', 'cp9': 'CP9 pallet'},
    'de': {None: 'Kunststoffpalette', 'display': 'Displaypalette', 'hygienic': 'Hygienepalette', 'cleanroom': 'Reinraumpalette',
           'pool': 'Kunststoff-Poolpalette', 'h1': 'H1-Europalette', 'industrial': 'Industriepalette', 'us': 'Kunststoffpalette',
           'cp1': 'CP1-Palette', 'cp3': 'CP3-Palette', 'cp6': 'CP6-Palette', 'cp9': 'CP9-Palette'},
    'fr': {None: 'Palette plastique', 'display': 'Palette display', 'hygienic': 'Palette hygiénique', 'cleanroom': 'Palette salle blanche',
           'pool': 'Palette plastique de pooling', 'h1': 'Palette Europe H1', 'industrial': 'Palette industrielle', 'us': 'Palette plastique',
           'cp1': 'Palette CP1', 'cp3': 'Palette CP3', 'cp6': 'Palette CP6', 'cp9': 'Palette CP9'},
    'it': {None: 'Pallet in plastica', 'display': 'Pallet espositore', 'hygienic': 'Pallet igienico', 'cleanroom': 'Pallet per camera bianca',
           'pool': 'Pallet in plastica per pooling', 'h1': 'Europallet H1', 'industrial': 'Pallet industriale', 'us': 'Pallet in plastica',
           'cp1': 'Pallet CP1', 'cp3': 'Pallet CP3', 'cp6': 'Pallet CP6', 'cp9': 'Pallet CP9'},
    'es': {None: 'Palet de plástico', 'display': 'Palet expositor', 'hygienic': 'Palet higiénico', 'cleanroom': 'Palet para sala blanca',
           'pool': 'Palet de plástico para pooling', 'h1': 'Europalet H1', 'industrial': 'Palet industrial', 'us': 'Palet de plástico',
           'cp1': 'Palet CP1', 'cp3': 'Palet CP3', 'cp6': 'Palet CP6', 'cp9': 'Palet CP9'},
}
DECK = {
    'nl': {('open', False): 'open dek', ('closed', False): 'gesloten dek', ('open', True): 'open antislipdek', ('closed', True): 'gesloten antislipdek'},
    'en': {('open', False): 'open deck', ('closed', False): 'closed deck', ('open', True): 'open anti-slip deck', ('closed', True): 'closed anti-slip deck'},
    'de': {('open', False): 'offenes Deck', ('closed', False): 'geschlossenes Deck', ('open', True): 'offenes Antirutschdeck', ('closed', True): 'geschlossenes Antirutschdeck'},
    'fr': {('open', False): 'plateau ajouré', ('closed', False): 'plateau fermé', ('open', True): 'plateau ajouré antidérapant', ('closed', True): 'plateau fermé antidérapant'},
    'it': {('open', False): 'piano aperto', ('closed', False): 'piano chiuso', ('open', True): 'piano aperto antiscivolo', ('closed', True): 'piano chiuso antiscivolo'},
    'es': {('open', False): 'superficie abierta', ('closed', False): 'superficie cerrada', ('open', True): 'superficie abierta antideslizante', ('closed', True): 'superficie cerrada antideslizante'},
}
DECK_SHORT = {
    'nl': {'open': 'open', 'closed': 'gesloten'}, 'en': {'open': 'open', 'closed': 'closed'}, 'de': {'open': 'offen', 'closed': 'geschlossen'},
    'fr': {'open': 'ajourée', 'closed': 'fermée'}, 'it': {'open': 'aperto', 'closed': 'chiuso'}, 'es': {'open': 'abierto', 'closed': 'cerrado'},
}
SUPPORT = {
    'nl': {'runners': 'onderlatten', 'feet': 'pootjes'}, 'en': {'runners': 'runners', 'feet': 'feet'}, 'de': {'runners': 'Kufen', 'feet': 'Füße'},
    'fr': {'runners': 'semelles', 'feet': 'pieds'}, 'it': {'runners': 'slitte', 'feet': 'piedi'}, 'es': {'runners': 'patines', 'feet': 'pies'},
}
RACK_WORD = {'nl': 'stelling', 'en': 'racking', 'de': 'Regal', 'fr': 'rayonnage', 'it': 'scaffale', 'es': 'estantería'}
ON = {'nl': 'op', 'en': 'on', 'de': 'auf', 'fr': 'sur', 'it': 'su', 'es': 'sobre'}
LOAD_WORDS = {
    'nl': ('statisch', 'dynamisch', 'in de stelling', 'en'), 'en': ('static', 'dynamic', 'racking', 'and'),
    'de': ('statisch', 'dynamisch', 'im Regal', 'und'), 'fr': ('statique', 'dynamique', 'en rayonnage', 'et'),
    'it': ('in statica', 'in dinamica', 'su scaffale', 'e'), 'es': ('estática', 'dinámica', 'en estantería', 'y'),
}
TAILS = {
    'nl': ('Vanaf {p} excl. btw.', 'Vraag een offerte aan.', 'Bekijk alle specificaties.'),
    'en': ('From {p} excl. VAT.', 'Request a quote.', 'View all specifications.'),
    'de': ('Ab {p} zzgl. MwSt.', 'Jetzt Angebot anfordern.', 'Alle technischen Daten.'),
    'fr': ('À partir de {p} HT.', 'Demandez un devis.', 'Voir toutes les caractéristiques.'),
    'it': ('Da {p} IVA esclusa.', 'Richiedi un preventivo.', 'Vedi tutte le specifiche.'),
    'es': ('Desde {p} sin IVA.', 'Solicite un presupuesto.', 'Vea todas las especificaciones.'),
}


def deck_words(m, lang):
    return DECK[lang][(m['deck'], bool(m['antislip']))]


def support_words(m, lang, n=True):
    s = m['support']
    w = SUPPORT[lang][s['type']]
    return f"{s['n']} {w}" if n else w


def dims(m, sep=' x '):
    return f"{m['L']}{sep}{m['W']}{sep}{m['H']}"


def base_name(m, lang):
    tw = TYPEWORD[lang][m['special']]
    return f"{tw} {dims(m)} {deck_words(m, lang)} {support_words(m, lang)} {m['class']}"


def assign_names(models):
    """Set m['name'][lang] and m['slug'][lang]; disambiguate identical names."""
    from collections import defaultdict
    from build_util import slugify
    for lang in LANGS:
        groups = defaultdict(list)
        for m in models:
            groups[base_name(m, lang)].append(m)
        for nm, ms in groups.items():
            for m in ms:
                name = nm
                if len(ms) > 1:
                    rk = m['racking'][1] if m['racking'] else None
                    name = f"{nm}, {RACK_WORD[lang]} {fmt_int(rk, lang)} kg" if rk else nm
                m.setdefault('name', {})[lang] = name
        seen = {}
        for m in models:
            s = slugify(m['name'][lang])
            if s in seen:
                s = s + '-' + m['id']
            seen[s] = m
            m.setdefault('slug', {})[lang] = s


# --------------------------------------------------------------------------- short copy
def subtitle(m, lang, T):
    tags = T[lang]['tags']
    bits = []
    if 'nestable' in m['types']:
        bits.append(tags['nestable'])
    if 'export' in m['types']:
        bits.append(tags['export'])
    if m['antislip']:
        bits.append(tags['antislip'])
    if m['rackable']:
        bits.append(tags['rackable'])
    return bits


_P_RE = re.compile(r'^\s*<p>(.*?)</p>', re.S)


def seo_parts(m, lang):
    """(intro_text, rest_html) from Q-Pall's SEO text for this model."""
    html = (m.get('seo6') or {}).get(lang) or (m.get('seo6') or {}).get('en') or ''
    if lang == 'en':   # English: comma as thousands separator (decimals use a point)
        html = re.sub(r'(?<![\d.,/])(\d{1,3})\.(\d{3})(?!\d)', r'\1,\2', html)
    mo = _P_RE.match(html)
    if not mo:
        return '', html
    intro = re.sub(r'<[^>]+>', '', mo.group(1)).strip()
    rest = html[mo.end():].strip()
    # model pages group several articles: drop the article-specific weight sentence variations is not needed;
    # demote h2 -> h3 inside the description block
    rest = rest.replace('<h2>', '<h3>').replace('</h2>', '</h3>')
    return intro, rest


# --------------------------------------------------------------------------- meta
def meta_title_candidates(m, lang):
    tw = TYPEWORD[lang][m['special']]
    d3 = f"{m['L']}x{m['W']}x{m['H']}"
    d2 = f"{m['L']}x{m['W']}"
    dk = deck_words(m, lang)
    dks = DECK_SHORT[lang][m['deck']] if not m['antislip'] else dk
    sp = support_words(m, lang)
    q = (' ' + m['name'][lang].split(', ', 1)[1]) if ', ' in m['name'][lang] else ''
    c = m['class']
    if m.get('sku_title'):      # one of several articles of the same pallet: the article number makes the title unique
        k = m['sku']
        cands = [f"{tw} {d3} {dks} {sp} {c} – {k}", f"{tw} {d2} {dks} {sp} {c} – {k}", f"{tw} {d2} {sp} {c} – {k}",
                 f"{tw} {d2} {c} – {k}", f"{tw} {d2} – {k}", f"{d2} {c} – {k}", f"{tw} {k}"]
        return [re.sub(r'\s+', ' ', x).strip() for x in cands]
    cands = [
        f"{tw} {d3} {dk} {sp} {c}{q} – Q-Pall",
        f"{tw} {d2} {dk} {sp} {c}{q} – Q-Pall",
        f"{tw} {d3} {dk} {sp} {c}{q}",
        f"{tw} {d2} {dk} {sp} {c}{q}",
        f"{tw} {d2} {dks} {sp} {c}{q}",
        f"{tw} {d2} {dks} {sp}{q}",
        f"{tw} {d2} {sp} {c}{q}",
        f"{tw} {d2} {sp}{q}",
    ]
    return [re.sub(r'\s+', ' ', x).strip() for x in cands]


# Approximate width of a title in Google's results (Arial 20 px, metrics of Liberation Sans). Google cuts titles
# at roughly 580 px; titles are kept at max. 570 px so they are never truncated (SEO audit 4.5, October 2026).
_PX = {}
for _chars, _w in (('iljí\u00ed\u00ee\u00ef\u2019', 4.44), ("'", 3.81), (' ,./:fItí\u00cd', 5.56), ('()-r\u00b7', 6.66), ('"', 7.09),
                   ('cksvxyzJ\u00e7\u00ff', 10.0), ('0123456789?abdeghnopqu\u00e0\u00e1\u00e2\u00e4\u00e8\u00e9\u00ea\u00eb\u00f1\u00f3\u00f4\u00f6\u00f9\u00fa\u00fb\u00fcL\u2013', 11.12),
                   ('\u00d7', 11.69), ('FTZ\u00df\u00bf', 12.22), ('&ABEKPSVXY\u00c0\u00c4\u00c8\u00c9', 13.34), ('CDHNRU\u00dc w', 14.44),
                   ('GOQ\u00d6', 15.56), ('Mm', 16.66), ('%', 17.78), ('W\u0153', 18.88)):
    for _c in _chars:
        _PX.setdefault(_c, _w)
_PX[' '] = 5.56


def title_px(s):
    return sum(_PX.get(c, 11.12) for c in s)


def title_ok(s):
    return len(s) <= 60 and title_px(s) <= 570


def assign_titles(models, lang):
    used = set()
    for m in models:
        cands = meta_title_candidates(m, lang)
        pick_ = next((x for x in cands if title_ok(x) and x not in used), None)
        if not pick_:
            pick_ = next((x for x in cands if title_ok(x)), cands[-1][:60])
        used.add(pick_)
        m.setdefault('meta_title', {})[lang] = pick_


def meta_title(m, lang):
    return m['meta_title'][lang]


def meta_desc(m, lang):
    st = rng_txt(m['static'], lang).replace('–', '-')
    dy = rng_txt(m['dynamic'], lang).replace('–', '-')
    rk = rng_txt(m['racking'], lang).replace('–', '-') if m['racking'] else None
    tw = TYPEWORD[lang][m['special']]
    ws, wd, wr, wand = LOAD_WORDS[lang]
    dl, dw = m.get('disp_LW') or (m['L'], m['W'])   # size in category order (760 x 1140, 600 x 800)
    head = f"{tw} {dl} x {dw} mm, {deck_words(m, lang)} {ON[lang]} {support_words(m, lang)}, {m['class']}"
    if m.get('sku_title'):
        head = f"{m['sku']}: {head}"
    loads = f"{st} {ws}, {dy} {wd}" + (f" {wand} {rk} {wr}" if rk else "")
    t_price, t_quote, t_specs = TAILS[lang]
    tails = []
    if m['price_from']:
        tails.append(t_price.format(p=fmt_price(m['price_from'], lang)))
    tails += [t_quote, t_specs]
    cands = []
    for i in range(len(tails), -1, -1):
        cands.append(f"{head}: {loads}. " + ' '.join(tails[:i]))
        cands.append(f"{head}: {loads}, {rng_txt(m['weight'], lang, 'kg', True)}. " + ' '.join(tails[:i]))
    cands = [c.strip() for c in cands]
    ok = [c for c in cands if 120 <= len(c) <= 156]
    if ok:
        ok.sort(key=lambda c: (('€' in c), len(c)), reverse=True)
        return ok[0]
    best = min(cands, key=lambda c: abs(len(c) - 150))
    if len(best) > 156:
        best = best[:153].rsplit(' ', 1)[0] + '…'
    return best
