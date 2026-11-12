#!/usr/bin/env python3
"""Technische datasheets (PDF) per palletmodel en taal.

Schrijft data/datasheets/<lang>/q-pall-<model-id>-<lang>.pdf (build.py kopieert die map naar
/downloads/datasheets/). Gegevens komen rechtstreeks uit build.py (modellen, teksten, specificaties),
de opmaak uit templates/datasheet.html. Prijzen staan bewust niet op de datasheet.

Gebruik:  python3 tools/datasheets.py                    (alle modellen, alle talen)
          python3 tools/datasheets.py --lang nl          (één taal)
          python3 tools/datasheets.py --model qp1208lb9fr --lang en
          python3 tools/datasheets.py --html DIR         (ook de HTML per datasheet bewaren, voor controle)
Vereist: playwright (Python) met Chromium.
"""
import argparse, base64, io, json, os, re, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import build  # noqa: E402  (loads models, texts and templates)
from markupsafe import Markup, escape  # noqa: E402
from PIL import Image  # noqa: E402
from drawings import drawing  # noqa: E402

OUT = os.path.join(ROOT, 'data', 'datasheets')
PHOTO_W, PHOTO_H = 780, 520           # 3:2, ≈ 230 ppi at the printed width (≈ 87 mm)
PHOTO_FILL = (0.94, 0.86)             # max product size inside the photo (w, h)
JPEG_Q = 74
FONT_W = (400, 500, 600, 700)
# drawings.drawing() is sized for the web page; on A4 the labels are scaled up for legibility
DRAW_FONT = {'14': '19', '13': '16'}
DRAW_GREY = '#9AA0BC'


def font_css():
    out = []
    for w in FONT_W:
        data = base64.b64encode(open(os.path.join(ROOT, 'static/fonts', f'poppins-{w}.woff2'), 'rb').read()).decode()
        out.append(f"@font-face{{font-family:Poppins;font-style:normal;font-weight:{w};font-display:block;"
                   f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return Markup('\n'.join(out))


def photo_source(m, idx=1):
    """Photo idx of the article's photo set (input/photos/<photo id>/<idx>.webp); fallback: catalogue image."""
    p = os.path.join(ROOT, 'input/photos', m['photo_id'], f'{idx}.webp')
    if os.path.exists(p):
        return p
    if idx == 1 and m.get('img'):
        for ext in ('.webp', '.png', '.jpg'):
            p = os.path.join(ROOT, 'input/raw', f"x{m['img']}{ext}")
            if os.path.exists(p):
                return p
    return None


def _white_rgb(path):
    im = Image.open(path)
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA')
        bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        im = bg
    return im.convert('RGB')


def photo_uri(m, idx=1):
    """Product centred on a white 3:2 canvas, compressed JPEG as data URI."""
    src = photo_source(m, idx)
    canvas = Image.new('RGB', (PHOTO_W, PHOTO_H), (255, 255, 255))
    if src:
        im = _white_rgb(src)
        # crop to the product (anything clearly darker than the white background)
        mask = im.convert('L').point(lambda v: 255 if v < 244 else 0)
        bb = mask.getbbox()
        if bb:
            im = im.crop(bb)
        s = min(PHOTO_W * PHOTO_FILL[0] / im.width, PHOTO_H * PHOTO_FILL[1] / im.height)
        im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
        canvas.paste(im, ((PHOTO_W - im.width) // 2, (PHOTO_H - im.height) // 2))
    buf = io.BytesIO()
    canvas.save(buf, 'JPEG', quality=JPEG_Q, optimize=True, progressive=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


def edition(t):
    y, mo = int(build.BUILD_DATE[:4]), int(build.BUILD_DATE[5:7])
    months = t.get('months') or build.T['en']['months']
    return f"{t['ds_generated']} {months[mo - 1]} {y}"


def chips(m, lang):
    t = build.T[lang]
    X = m['txt'][lang]
    out = [X['deck_label'], X['support']]
    if 'nestable' in m['types']:
        out.append(t['f_nest'])
    # the deck label of anti-slip models already says so (Gesloten antislipdek, Closed anti-slip deck, ...)
    if m['antislip'] and t['f_antislip'].lower()[:8] not in X['deck_label'].lower():
        out.append(t['f_antislip'])
    return out


def spec_tables(m, lang):
    """Spec groups as on the product page, without prices. The load group is shown as the load box. Pallets are sold per
    full stack only, which is a row in the delivery group (no production location since update 53)."""
    t = build.T[lang]
    out = []
    stack_row = (t['ds_stack_h'], nobreak((t['stack_per'].format(n=build.fmt_int(m['stack'], lang)) + (' (' + m['txt'][lang]['stack_height'] + ')' if m['txt'][lang]['stack_height'] else '')) if m['stack'] else t['stack_req']))
    groups = build.spec_groups(m, lang, price=False)
    if not any(title == t['group_delivery'] for title, _ in groups):
        # update 53: without the production location some pallets have no other delivery row; the stack row keeps the group
        groups = groups + [(t['group_delivery'], [])]
    for title, rows in groups:
        if title == t['group_load']:
            continue
        rows = [(k, nobreak(v)) for k, v in rows]
        if title == t['group_delivery']:
            rows.insert(1, stack_row)
        out.append((title, rows))
    return out


def nobreak(v):
    """Keep '12 kg', '3 Kufen' and 'Balk (NL)' together when a value wraps."""
    return re.sub(r'(\d) ', '\\1\u00a0', str(v)).replace(' (', '\u00a0(')


def versions(m, lang):
    """The other articles of the same pallet (this one first), with a link to their page; empty for a single article."""
    rows = []
    for v in build.variant_rows(m, lang):
        code = v['loc_code']
        v = dict(v)
        v['loc_html'] = loc_html(code, lang) if code else None
        rows.append(v)
    return rows if len(rows) > 1 else []


def ds_drawing(m, t, uid, support):
    """Technical drawing from drawings.py, adapted for print: larger labels, no info block, side view centred.
    Grey labels become navy at 50 % opacity (same look; Chromium embeds a font copy per text colour)."""
    svg = drawing(m, t, uid)
    # bottom-view label as in the spec table (drawings.py lower-cases it, wrong for German nouns: 3 kufen)
    sp = m['support']
    lab = f"{sp['n']} {t['f_runners'].lower() if sp['type'] == 'runners' else t['f_feet'].lower()}"
    svg = svg.replace(f'>{lab}</text>', f'>{escape(support)}</text>', 1)
    # the info block (dimensions / weight / class, 12 + 16 px labels) repeats the spec tables next to it
    svg = re.sub(r'<text [^>]*font-size="(?:12|16)"[^>]*>.*?</text>', '', svg)
    svg = re.sub(r'font-size="(\d+)"', lambda mo: f'font-size="{DRAW_FONT.get(mo.group(1), mo.group(1))}"', svg)
    svg = re.sub(r'(<text [^>]*)fill="' + DRAW_GREY + '"', r'\1fill="#1D1C4C" fill-opacity=".5"', svg)
    # millimetres without thousands separator, as everywhere else on the sheet (1.200 mm -> 1200 mm)
    svg = re.sub(r'>(\d)[.,](\d{3})( mm)?<', r'>\1\2\3<', svg)
    # centre the side view under the top and bottom view (three-view layout, symmetric)
    titles = [mo for mo in re.finditer(r'<text x="([\d.]+)"[^>]*letter-spacing="1.5"', svg)]
    if len(titles) == 3:
        dx = (float(titles[1].group(1)) - float(titles[0].group(1))) / 2
        i, j = titles[2].start(), svg.rindex('</svg>')
        svg = svg[:i] + f'<g transform="translate({dx:g} 0)">' + svg[i:j] + '</g>' + svg[j:]
    return Markup(svg)


HDR_W, HDR_H = 1860, 540             # header artwork, 210 x 61 mm at 225 ppi
Q_COLOUR = {'light': 'groen', 'medium': 'blauw', 'heavy': 'paars'}
NAVY_RGB = (29, 28, 76)
CAD_DIR = os.path.join(ROOT, 'input', 'cad')
CAD_SIDES_DIR = os.path.join(ROOT, 'input', 'cad-zij')
# articles whose drawing is the 9-feet pallet plus the click-on runner below it (input/cad/runner.json, update 16)
_rj = os.path.join(ROOT, 'input', 'cad', 'runner.json')
CAD_RUNNER = set(json.load(open(_rj))) if os.path.exists(_rj) else set()
# articles whose 'drawing' is the manufacturer's dimensional sketch (photo with dimensions, update 19): JPEG, no navy palette
_sj = os.path.join(ROOT, 'input', 'cad', 'sketch.json')
CAD_SKETCH = set(json.load(open(_sj))) if os.path.exists(_sj) else set()
CAD_MAX_W = 1300                      # px; the drawing prints ≈ 170 mm wide (≈ 195 ppi)


def header_art(cls):
    """Navy band with the 3D Q of the load class on the right (same artwork as the website headers)."""
    import numpy as np
    q = Image.open(os.path.join(ROOT, 'static/img/q', f"q-{Q_COLOUR.get(cls, 'oranje')}-1800.webp")).convert('RGBA')
    c = Image.new('RGBA', (HDR_W, HDR_H), NAVY_RGB + (255,))
    s = HDR_H * 1.62 / q.height
    q = q.resize((round(q.width * s), round(q.height * s)), Image.LANCZOS)
    c.alpha_composite(q, (HDR_W - round(q.width * 0.86), -round(q.height * 0.30)))
    # soft fade into navy towards the text on the left
    x = np.arange(HDR_W)
    ramp = (np.clip((HDR_W * 0.60 - x) / (HDR_W * 0.16), 0, 1) * 255).astype(np.uint8)
    fade = Image.new('RGBA', (HDR_W, HDR_H), NAVY_RGB + (255,))
    fade.putalpha(Image.fromarray(np.tile(ramp, (HDR_H, 1))))
    c.alpha_composite(fade)
    buf = io.BytesIO()
    c.convert('RGB').save(buf, 'JPEG', quality=80, optimize=True, progressive=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


def cad_file(m):
    """The article's own drawing (input/cad/<article id>.png), else None (then the datasheet shows the schematic
    drawing with the article's own dimensions: a drawing of another mould could show other dimensions)."""
    p = os.path.join(CAD_DIR, m['id'] + '.png')
    if os.path.exists(p):
        return p
    # side and end views only (no top view), e.g. from the manufacturer's drawing (update 15)
    p = os.path.join(CAD_SIDES_DIR, m['id'] + '.png')
    return p if os.path.exists(p) else None


def cad_sides(m):
    """True when the article's drawing shows only the side and end views."""
    p = cad_file(m)
    return bool(p) and os.path.dirname(p) == CAD_SIDES_DIR


def cad_uri(m):
    """Top view + both side views from the CAD drawing, or None."""
    p = cad_file(m)
    if not p:
        return None
    # flatten onto white, ≈ 250 ppi at the printed width and a small palette: line art stays sharp,
    # the PDF stays small (no alpha mask, ~4x fewer bytes than the RGBA original)
    if m['id'] in CAD_SKETCH:      # photo with dimensions: keep the grey tones
        im = Image.open(p).convert('RGB')
        if im.width > 1700:
            im = im.resize((1700, round(im.height * 1700 / im.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, 'JPEG', quality=86, optimize=True)
        return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()
    im = Image.open(p).convert('RGBA')
    mw = 1900 if m['id'] in CAD_RUNNER else CAD_MAX_W   # the runner below has small text: keep more pixels
    if im.width > mw:
        im = im.resize((mw, round(im.height * mw / im.width)), Image.LANCZOS)
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    pal = bg.convert('RGB').quantize(colors=8, method=Image.MEDIANCUT, dither=Image.NONE)
    buf = io.BytesIO()
    pal.save(buf, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


_SPRITE = open(os.path.join(ROOT, 'templates', '_sprite.svg'), encoding='utf-8').read()
FLAG_SYMBOLS = Markup('<svg width="0" height="0" style="position:absolute" aria-hidden="true">' +
                      ''.join(re.findall(r'<symbol id="f-[a-z]{2}".*?</symbol>', _SPRITE, re.S)) + '</svg>')


def flag(cc):
    return Markup(f'<svg class="flag" viewBox="0 0 32 32" aria-hidden="true"><use href="#f-{cc.lower()}"/></svg>')


def loc_html(code, lang):
    L = build.LOCATIONS[code]
    return Markup(f'<span class="locf">{flag(L["cc"])}{escape(L["name"])}\u00a0({L["cc"]})</span>')


_PHOTOS = {}
_FONTS = None
_ART = {}


def render_html(m, lang):
    global _FONTS
    if _FONTS is None:
        _FONTS = font_css()
    ph = build.PHOTOS.get(m['photo_id'], {})
    # always two photos of the article itself when there are two (Noah, update 19): the bottom view if there is one,
    # otherwise the second photo; the labels Bovenkant/Onderkant only when the second photo is the bottom view
    if ph.get('bottom'):
        shots = [(1, 'ds_top'), (ph['bottom'], 'ds_bottom')]
    elif ph.get('n', 1) >= 2:
        shots = [(1, None), (2, None)]
    else:
        shots = [(1, 'ds_top')]
    for idx, _ in shots:
        if (m['photo_id'], idx) not in _PHOTOS:
            _PHOTOS[(m['photo_id'], idx)] = photo_uri(m, idx)
    t = build.T[lang]
    X = m['txt'][lang]
    m['name']['_cur'] = m['name'][lang]          # used by drawings.drawing()
    m['_weight_txt'] = X['weight']
    svg = ds_drawing(m, t, f"{m['id']}-{lang}-ds", X['support'])
    if m['class'] not in _ART:
        _ART[m['class']] = header_art(m['class'])
    ctx = dict(
        lang=lang, html_lang=build.HTML_LANG[lang], t=t, m=m, X=X, name=m['name'][lang],
        name_html=Markup(re.sub(r'(\d) x (\d)', '\\1\u00a0x\u00a0\\2', str(escape(m['name'][lang])))),  # 1200 x 800 x 145 stays on one line
        size_label=m['size_label'], size_nick=t['size_nick'][m['size']], chips=chips(m, lang),
        photos=[{'src': _PHOTOS[(m['photo_id'], idx)], 'label': t[key] if key and len(shots) > 1 else None} for idx, key in shots],
        drawing=svg, cad=cad_uri(m), cad_sides=cad_sides(m), cad_runner=m['id'] in CAD_RUNNER, cad_sketch=m['id'] in CAD_SKETCH, rackable=bool(m.get('rackable')), hdr_art=_ART[m['class']], flags=FLAG_SYMBOLS,
        groups=spec_tables(m, lang), variants=versions(m, lang),
        edition=edition(t), logo=build.logo_svg(white=True, cls='logo'), font_css=_FONTS,
        company=build.COMPANY, company_country=build.COUNTRY[build.COMPANY['cc']][lang],
        product_url=build.DOMAIN + m['url'][lang],
    )
    return build.env.get_template('datasheet.html').render(**ctx)


def pdf_path(m, lang):
    return os.path.join(OUT, lang, f"q-pall-{m['id']}-{lang}.pdf")


def main():
    ap = argparse.ArgumentParser(description='Q-Pall datasheets (PDF) per model and language')
    ap.add_argument('--lang', choices=build.LANGS, action='append', help='language (repeatable); default: all')
    ap.add_argument('--model', action='append', help='model id (repeatable); default: all')
    ap.add_argument('--html', metavar='DIR', help='also write the rendered HTML to DIR (for checking)')
    a = ap.parse_args()
    langs = a.lang or list(build.LANGS)
    if a.model:
        bad = [x for x in a.model if x not in build.MODEL_BY_ID]
        if bad:
            sys.exit(f'unknown model id: {", ".join(bad)}')
        models = [build.MODEL_BY_ID[x] for x in a.model]
    else:
        models = build.MODELS

    from playwright.sync_api import sync_playwright
    t0 = time.time()
    n, two, tight, problems, drawh = 0, [], [], [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.emulate_media(media='print')
        for m in models:
            for lang in langs:
                html = render_html(m, lang)
                if a.html:
                    os.makedirs(a.html, exist_ok=True)
                    open(os.path.join(a.html, f"q-pall-{m['id']}-{lang}.html"), 'w', encoding='utf-8').write(html)
                page.set_content(html, wait_until='load')
                page.evaluate('document.fonts.ready.then(() => true)')
                info = page.evaluate('window.dsLayout()')
                if info['overflow'] or info['stuck']:
                    problems.append(f"{m['id']}/{lang}: content does not fit (pages {info['overflow']})")
                if info.get('moved'):
                    two.append(f"{m['id']}/{lang}")
                drawh.append((info.get('drawH', 0), f"{m['id']}/{lang}"))
                if info['tight']:
                    tight.append(f"{m['id']}/{lang}")
                dest = pdf_path(m, lang)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                page.pdf(path=dest, prefer_css_page_size=True, print_background=True, tagged=True,
                         margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'})
                n += 1
        browser.close()
    files = [pdf_path(m, l) for m in models for l in langs]
    total = sum(os.path.getsize(f) for f in files)
    big = max(files, key=os.path.getsize)
    print(f'datasheets: {n}  total {total / 1024 / 1024:.1f} MB  largest {os.path.relpath(big, ROOT)} '
          f'({os.path.getsize(big) / 1024:.0f} KB)  versions on page 2: {len(two)}  compact: {len(tight)}  time {time.time() - t0:.0f}s')
    if drawh:
        lo = min(drawh)
        print(f'  smallest drawing area: {lo[0]} mm high ({lo[1]})')
    if two:
        print('  versions table on page 2:', ', '.join(two[:30]) + (' …' if len(two) > 30 else ''))
    if tight:
        print('  compact (one page with slightly tighter spacing):', ', '.join(tight[:30]) + (' …' if len(tight) > 30 else ''))
    for pr in problems:
        print('  WARNING', pr)


if __name__ == '__main__':
    main()
