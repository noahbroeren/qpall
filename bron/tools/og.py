#!/usr/bin/env python3
"""Open Graph share images (1200 x 630 JPEG) for EVERY page of the site, in every language.

Usage:   python3 tools/og.py                      all pages and all product pages, all languages
         python3 tools/og.py --lang nl --page home --page p:qp1208mb3rr
         python3 tools/og.py --only pages|products
Output:  data/og/<lang>/<key>.jpg   key = page id ('home', 'sector-food' ...) or 'p-<model id>' for a product page
         data/og/og-image.jpg       (= the English home image, the site-wide fallback)
         build.py copies data/og to /assets/og/ and gives every page its own image (build.og_for()).

Look: the same visual language as the website hero. Navy gradient, the 3D Q in a brand colour (the load class
colour for pallets), Poppins, an orange eyebrow with a line, the headline in light + bold, and on the right the
same elements as on the site: the free-standing hero pallet, a white product card with the class badge, or a
photo with the Q corner (10/56 px radius). Product pages also show the three loads like the product page.
Texts come straight from the site sources (content/<lang>/*.md, i18n/<lang>.json, product data), so after new
translations simply run this script again. Rendering: Playwright/Chromium at 2x, downscaled with Lanczos.
"""
import argparse, html, io, os, re, shutil, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PIL import Image, ImageChops, ImageFilter       # noqa: E402
from playwright.sync_api import sync_playwright      # noqa: E402

import site_config as SC                             # noqa: E402
import build                                         # noqa: E402  (data only; build.main() is not run)

OUT = os.path.join(ROOT, 'data/og')
BRAND_DIR = os.path.join(ROOT, 'input/brand')        # brand photos: photo-<name>.webp
HERO_DIR = os.path.join(ROOT, 'input/hero')          # free-standing pallets light/medium/heavy.png (tools/hero_cutouts.py)
PRODUCT_DIR = os.path.join(ROOT, 'input/photos')     # product photo per model: <id>/1.webp (white background)
ACC_DIR = os.path.join(ROOT, 'input/acc-photos')
RAW_DIR = os.path.join(ROOT, 'input/raw')
MOCKUP_DIR = os.path.join(ROOT, 'input/mockups')
Q_DIR = os.path.join(ROOT, 'static/img/q')           # transparent 3D Q artwork (tools/q_backgrounds.py)
FONT_DIR = os.path.join(ROOT, 'static/fonts')

W, H = 1200, 630
DSF = 2                        # render at 2x, downscale to 1x
MAX_KB = 150
COL = {'orange': '#F37321', 'navy': '#1D1C4C', 'light': '#94C24A', 'medium': '#2DAFE6', 'heavy': '#A7328A'}
Q_OF_CLASS = {'light': 'groen', 'medium': 'blauw', 'heavy': 'paars'}
Q_RGB = {'groen': '148,194,74', 'blauw': '45,175,230', 'paars': '167,50,138', 'oranje': '243,115,33'}

# ----------------------------------------------------------------------------------------- per-page choices
# visual: ('cutout', class) | ('cutouts',) | ('card', model id) | ('acc', kind) | ('photo', stem, object-position) | ('booklet', name)
PAGE_VISUAL = {
    'home': ('cutout', 'medium'), 'pallets': ('cutouts',), 'quote': ('cutout', 'medium'), 'calc': ('cutouts',),
    'class-light': ('cutout', 'light'), 'class-medium': ('cutout', 'medium'), 'class-heavy': ('cutout', 'heavy'),
    'about-load': ('cutout', 'heavy'), 'guide-choose': ('cutouts',), 'guide-sizes': ('cutouts',),
    'ultra': ('card', 'qp1210hp6r-ao'), 'guide-prices': ('card', 'qp1208lb9fr'), 'guide-ispm': ('card', 'qp1208lb9fr'),
    'guide-wood': ('card', 'europal800rr'),
    'about': ('photo', 'hq-corner', '50% 50%'), 'about-local': ('photo', 'local', '40% 50%'),
    'about-sustainability': ('photo', 'seaturtle', '55% 50%'), 'about-custom': ('photo', 'custom-logo', '50% 50%'),
    'about-glossary': ('photo', 'mould', '50% 40%'), 'careers': ('photo', 'team', '50% 45%'), 'job-inside-sales': ('photo', 'office-sales', '50% 40%'), 'about-team': ('photo', 'office', '50% 50%'),
    'dealers': ('photo', 'handshake', '58% 50%'), 'contact': ('photo', 'hq-terrace', '50% 50%'),
    'transport': ('photo', 'hq-aerial', '50% 50%'), 'thanks': ('photo', 'handshake', '58% 50%'), 'thanks-quote': ('photo', 'handshake', '58% 50%'),
    'used': ('photo', 'pooling', '50% 50%'), 'sectors': ('photo', 'beverage', '50% 50%'),
    'sector-chemical': ('photo', 'sector-chemical', '50% 50%'), 'sector-food': ('photo', 'sector-food', '50% 50%'),
    'sector-pharma': ('photo', 'sector-pharma', '50% 50%'), 'sector-beverage': ('photo', 'beverage', '50% 50%'),
    'sector-retail': ('photo', 'retail', '50% 50%'), 'sector-logistics': ('photo', 'robot', '50% 50%'),
    'sector-pooling': ('photo', 'pooling', '50% 50%'), 'knowledge': ('photo', 'warehouse', '50% 40%'),
    'guide-automation': ('photo', 'robot', '40% 50%'), 'guide-ppwr': ('booklet', 'ppwr'),
    'news': ('photo', 'local', '50% 50%'), 'news-hdpe': ('photo', 'regrind', '50% 50%'), 'news-stackup': ('photo', 'stackup', '50% 50%'),
    'news-process': ('photo', 'warehouse', '50% 50%'), 'news-local': ('photo', 'local', '50% 50%'),
    'news-auchan': ('photo', 'retail', '50% 50%'), 'catalog': ('booklet', 'catalogus'),
    'privacy': ('cutout', 'medium'), 'cookies': ('cutout', 'medium'), 'terms': ('cutout', 'medium'),
    'acc': ('acc', 'collar'), 'acc-collars': ('acc', 'collar'), 'acc-lids': ('acc', 'lid'), 'acc-freezer': ('acc', 'freezer'),
    'acc-drip': ('acc', 'drip'), 'acc-runners': ('acc', 'runner'),
}
# Q colour per page (default by section); pallets and pallet listings use the load class colour
PAGE_Q = {'home': 'blauw', 'pallets': 'oranje', 'quote': 'oranje', 'calc': 'blauw', 'catalog': 'oranje', 'guide-ppwr': 'paars',
          'about-sustainability': 'groen', 'used': 'groen', 'news-hdpe': 'groen', 'about-load': 'paars', 'guide-choose': 'oranje',
          'guide-sizes': 'blauw', 'thanks': 'oranje', 'contact': 'oranje', 'transport': 'blauw', 'dealers': 'blauw', 'careers': 'oranje', 'job-inside-sales': 'oranje'}
# footer USPs (i18n keys); the second one is dropped automatically when the line does not fit
USPS = {
    'home': ('usp_recycled', 'usp_factories'), 'pallets': ('usp_direct', 'usp_factories'), 'type-export': ('usp_ispm', 'usp_direct'),
    'guide-ispm': ('usp_ispm', 'usp_direct'), 'about': ('usp_factories', 'usp_recycled'), 'about-sustainability': ('usp_recycled', 'usp_factories'),
    'about-local': ('usp_factories', 'usp_direct'), 'quote': ('usp_reply', 'usp_direct'), 'contact': ('usp_reply', 'usp_direct'),
}
USPS_DEFAULT = ('usp_direct', 'usp_recycled')


def usps_for(pid):
    if pid in USPS:
        return USPS[pid]
    if pid.startswith(('size-', 'class-', 'p:')):
        return ('usp_direct', 'usp_factories')
    return USPS_DEFAULT


def listing_model(pid):
    """Product shown on a size / type listing: the model the navigation shows for it (exact photo), else the first one."""
    key = pid.split('-', 1)[1]
    pref = (build.SIZE_IMG if pid.startswith('size-') else build.TYPE_IMG).get(key)
    ms = build.listing_models(SC.PAGES[pid]['listing'])
    ids = [m['id'] for m in ms]
    if pref in ids:
        return pref
    exact = [i for i in ids if build.PHOTOS.get(i, {}).get('exact')]
    return (exact or ids)[0]


def visual_of(pid):
    if pid.startswith('p:'):
        return ('card', pid[2:])
    if pid in PAGE_VISUAL:
        return PAGE_VISUAL[pid]
    if pid in SC.NEWS_ITEMS and SC.NEWS_ITEMS[pid][1].startswith('photos/'):     # news: the article's cover photo
        return ('photo', SC.NEWS_ITEMS[pid][1][7:], '50% 50%')
    if pid.startswith(('size-', 'type-')):
        return ('card', listing_model(pid))
    raise SystemExit(f'og.py: no image rule for page {pid!r}')


def q_of(pid, vis):
    if pid.startswith('class-'):
        return Q_OF_CLASS[pid.split('-', 1)[1]]
    if vis[0] == 'card':
        return Q_OF_CLASS[build.MODEL_BY_ID[vis[1]]['class']]
    if vis[0] == 'cutout' and pid not in PAGE_Q:
        return Q_OF_CLASS[vis[1]] if vis[1] != 'medium' else 'blauw'
    if pid in PAGE_Q:
        return PAGE_Q[pid]
    if pid.startswith(('sector', 'knowledge', 'guide')):
        return 'blauw'
    if pid.startswith('news'):
        return 'paars'
    if pid.startswith(('about', 'acc')):
        return 'oranje'
    return 'blauw'


# ----------------------------------------------------------------------------------------- images
class Assets:
    """Prepares images once, scaled to the exact device-pixel size they are drawn at."""

    def __init__(self, tmp):
        self.tmp = tmp
        self.cache = {}

    def _save(self, key, im):
        fn = os.path.join(self.tmp, key + '.png')
        im.save(fn, compress_level=1)
        return fn

    def _object(self, key, path):
        """(image, bbox of the object). Cutouts (RGBA): bbox of the opaque pallet; photos on white: bbox of the dark part."""
        if key in self.cache:
            return self.cache[key]
        im = Image.open(path)
        if im.mode in ('RGBA', 'LA', 'P'):
            im = im.convert('RGBA')
            body = im.getchannel('A').point(lambda a: 255 if a > 200 else 0)
        else:
            im = im.convert('RGB')
            body = im.convert('L').point(lambda v: 255 if v < 236 else 0)
        bbox = body.getbbox() or (0, 0, im.width, im.height)
        self.cache[key] = (im, bbox)
        return self.cache[key]

    def place(self, key, path, cx, cy, max_w, max_h):
        """Scale so the object fits max_w x max_h and centre the OBJECT (not the canvas) on (cx, cy) - CSS px."""
        im, (x0, y0, x1, y1) = self._object(key, path)
        bw, bh = x1 - x0, y1 - y0
        s = min(max_w / bw, max_h / bh)
        w, h = im.width * s, im.height * s
        left, top = cx - (x0 + bw / 2) * s, cy - (y0 + bh / 2) * s
        k = f'{key}-{round(w)}x{round(h)}'
        fn = os.path.join(self.tmp, k + '.png')
        if not os.path.exists(fn):
            im.resize((max(1, round(w * DSF)), max(1, round(h * DSF))), Image.LANCZOS).save(fn, compress_level=1)
        return {'src': fn, 'left': left, 'top': top, 'w': w, 'h': h}

    def cover(self, key, path, w, h):
        """Photo cropped later by CSS (object-fit: cover), pre-scaled to just cover w x h at render resolution."""
        k = f'cover-{key}-{w}x{h}'
        if k not in self.cache:
            im = Image.open(path)
            if im.mode in ('RGBA', 'LA', 'P'):
                im = im.convert('RGBA')
                bg = Image.new('RGBA', im.size, COL['navy'])
                bg.alpha_composite(im)
                im = bg
            im = im.convert('RGB')
            s = max(w * DSF / im.width, h * DSF / im.height)
            if s < 1:
                im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
            self.cache[k] = self._save(k, im)
        return self.cache[k]

    def q(self, colour):
        k = 'q-' + colour
        if k not in self.cache:
            self.cache[k] = os.path.join(Q_DIR, f'q-{colour}-1800.webp')
        return self.cache[k]


def img_tag(p, cls=''):
    return (f'<img class="{cls}" src="file://{p["src"]}" style="left:{p["left"]:.2f}px;top:{p["top"]:.2f}px;'
            f'width:{p["w"]:.2f}px;height:{p["h"]:.2f}px" alt="">')


def acc_source(kind):
    if kind == 'runner':
        a = next(a for a in build.ACCS if a['kind'] == 'runner' and 'RUN-L' in a['sku']) if any('RUN-L' in a['sku'] for a in build.ACCS) else None
        for cand in ([a] if a else []) + [x for x in build.ACCS if x['kind'] == 'runner']:
            for e in ('.webp', '.png', '.jpg'):
                f = os.path.join(RAW_DIR, f"x{cand.get('img')}{e}")
                if cand.get('img') and os.path.exists(f):
                    return f
    for e in ('.png', '.webp', '.jpg'):
        f = os.path.join(ACC_DIR, kind + e)
        if os.path.exists(f):
            return f
    raise SystemExit(f'og.py: no accessory photo for {kind}')


# right-hand visual zone (CSS px): card / photo box
CARD = {'x': 676, 'y': 130, 'w': 464, 'h': 356}
PHOTO = {'x': 668, 'y': 120, 'w': 484, 'h': 376}


def badge_html(cls, label, extra=''):
    return f'<span class="badge b-{cls}">{html.escape(label)}</span>{extra}'


def right_panel(pid, vis, lang, A):
    t = build.T[lang]
    k = vis[0]
    if k == 'cutout':
        c = vis[1]
        p = A.place('hero-' + c, os.path.join(HERO_DIR, c + '.png'), 932, 350, 470, 290)
        return img_tag(p, 'cut')
    if k == 'cutouts':
        out = []
        for c, cx, cy, mw in (('light', 820, 236, 330), ('heavy', 1000, 300, 330), ('medium', 890, 430, 400)):
            p = A.place('hero-' + c, os.path.join(HERO_DIR, c + '.png'), cx, cy, mw, 200)
            out.append(img_tag(p, 'cut'))
        return ''.join(out)
    if k in ('card', 'acc'):
        if k == 'card':
            m = build.MODEL_BY_ID[vis[1]]
            src, key = os.path.join(PRODUCT_DIR, m['photo_id'], '1.webp'), 'p-' + m['photo_id']
            badges = badge_html(m['class'], m['class'])
            if m.get('is_new'):
                badges += badge_html('new', t['mm_new'])
        else:
            src, key, badges = acc_source(vis[1]), 'acc-' + vis[1], ''
        c = CARD
        p = A.place(key, src, c['w'] / 2, c['h'] / 2 + 14, c['w'] - 76, c['h'] - 110)
        return (f'<div class="card" style="left:{c["x"]}px;top:{c["y"]}px;width:{c["w"]}px;height:{c["h"]}px">'
                f'{img_tag(p, "mul")}<div class="badges">{badges}</div></div>')
    if k == 'photo':
        stem, pos = vis[1], vis[2]
        b = PHOTO
        src = A.cover(stem, os.path.join(BRAND_DIR, f'photo-{stem}.webp'), b['w'], b['h'])
        return (f'<div class="photo" style="left:{b["x"]}px;top:{b["y"]}px;width:{b["w"]}px;height:{b["h"]}px">'
                f'<img src="file://{src}" style="object-position:{pos}" alt=""></div>')
    if k == 'booklet':
        f = os.path.join(MOCKUP_DIR, f'q-pall-boekje-{"catalogus" if vis[1] == "catalogus" else vis[1]}.png')
        p = A.place('booklet-' + vis[1], f, 902, 330, 420, 400)
        return img_tag(p, 'cut')
    raise ValueError(k)


# ----------------------------------------------------------------------------------------- texts
NBSP = ' '


def tidy(s):
    """Collapse whitespace and keep measurements together ("1200 x 800 mm", "100 %") with non-breaking spaces."""
    s = re.sub(r'\s+', ' ', str(s)).strip()
    s = re.sub(r'(\d)( ?[x×] ?)(\d)', lambda m: m.group(1) + m.group(2).replace(' ', NBSP) + m.group(3), s)
    s = re.sub(r'(\d)( ?[x×] ?)(\d)', lambda m: m.group(1) + m.group(2).replace(' ', NBSP) + m.group(3), s)
    s = re.sub(r'(\d) (mm|cm|kg|%)', lambda m: m.group(1) + NBSP + m.group(2), s)
    return re.sub(r'(?<![\d.,])(\d{1,2}) (?=\w)', lambda m: m.group(1) + NBSP, s)     # "3 onderlatten", "6 Kufen" stay together


def headline_html(s):
    s = html.escape(tidy(s), quote=False)
    s = re.sub(r'(?<![\w-])([A-Z]{1,4}-[A-Z]{1,4}(?: \d)?)(?![\w-])', r'<span style="white-space:nowrap">\1</span>', s)   # PE-HD 2 stays together
    s = re.sub(r'\b([A-Z]{3,5}) (\d)\b', '\\1' + NBSP + '\\2', s)                                                          # HDPE 2, PEHD 2
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)


def texts(pid, lang):
    """eyebrow, headline (with **bold**), product stats or None, usps"""
    t = build.T[lang]
    usps = [t[k] for k in usps_for(pid) if t.get(k)]
    if pid.startswith('p:'):
        m = build.MODEL_BY_ID[pid[2:]]
        X = m['txt'][lang]
        eyebrow = f"{m['size_label']} · {m['sku']}"      # one page per article number: the share image names it
        stats = [(X['static_big'], t['static']), (X['dynamic_big'], t['dynamic'])]
        if m.get('racking') and X.get('racking_big'):
            stats.append((X['racking_big'], t['racking']))
        return eyebrow, m['name'][lang], stats, usps
    fm = build.CONTENT[lang][pid]['fm']
    if pid == 'home':
        h1, eyebrow = fm['hero']['h1'], fm['hero'].get('eyebrow')
    else:
        h1, eyebrow = fm.get('h1', ''), fm.get('eyebrow')
    h1 = build.placeholders(h1, lang, {}) if '{' in str(h1) else h1
    if not eyebrow:
        eyebrow = build.short_title(pid, lang)
    return eyebrow, h1, None, usps


def font_faces():
    return ''.join(f"@font-face{{font-family:'Poppins';font-style:normal;font-weight:{w};font-display:block;"
                   f"src:url('file://{FONT_DIR}/poppins-{w}.woff2') format('woff2')}}" for w in (300, 400, 500, 600, 700))


CSS = """
:root{ROOTVARS}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1200px;height:630px;overflow:hidden;background:var(--navy)}
body{font-family:'Poppins',sans-serif;-webkit-font-smoothing:antialiased;text-rendering:geometricPrecision;font-kerning:normal}
.og{position:relative;width:1200px;height:630px;overflow:hidden;color:#fff;isolation:isolate;
    background:radial-gradient(620px 440px at 80% 48%,rgba(var(--acc),.14),transparent 64%),linear-gradient(170deg,#2B2A68 0%,#1D1C4C 72%)}
.q{position:absolute;z-index:-1;width:820px;height:auto;left:548px;top:50%;transform:translateY(-50%);opacity:.92}
.logo{position:absolute;left:64px;top:54px;height:48px;width:auto}
.logo svg{height:48px;width:auto;display:block}
.txt{position:absolute;left:64px;width:WTXTpx;top:136px;bottom:134px;display:flex;flex-direction:column;justify-content:center}
.eb{display:flex;align-items:center;gap:14px;color:var(--orange);font-weight:600;font-size:15px;letter-spacing:.16em;text-transform:uppercase;
    white-space:nowrap;line-height:1.3;margin-bottom:22px}
.eb::before{content:"";flex:0 0 28px;height:2px;background:var(--orange)}
.eb span{min-width:0}
.eb.wrap{white-space:normal}
h1{font-weight:300;font-size:60px;line-height:1.06;letter-spacing:-.015em;color:#fff;text-wrap:balance;hyphens:manual;overflow-wrap:normal;word-break:normal}
h1 strong{font-weight:700}
h1.prod{font-weight:600;line-height:1.12;letter-spacing:-.01em}
.stats{display:flex;margin-top:28px}
.stat{padding:0 26px;border-left:1px solid rgba(255,255,255,.18)}
.stat:first-child{padding-left:0;border-left:0}
.stat b{display:block;font-weight:600;font-size:36px;line-height:1;letter-spacing:-.01em;white-space:nowrap}
.stat b i{font-style:normal;font-size:21px;color:var(--orange);margin-left:3px}
.stat small{display:block;margin-top:8px;font-size:14px;line-height:1.2;color:rgba(255,255,255,.72);white-space:nowrap}
.ft{position:absolute;left:64px;width:WTXTpx;bottom:52px;height:58px;border-top:1px solid rgba(255,255,255,.16);display:flex;align-items:flex-end;
    white-space:nowrap;font-size:15px;line-height:1;color:rgba(255,255,255,.74);font-weight:400}
.ft b{font-weight:600;color:#fff;letter-spacing:.01em}
.ft i{display:inline-block;width:5px;height:5px;border-radius:50%;background:var(--orange);margin:0 12px;transform:translateY(-4px)}
.ft .bar{display:inline-block;width:1px;height:16px;background:rgba(255,255,255,.28);margin:0 18px;transform:translateY(1px)}
img.cut{position:absolute;display:block;filter:drop-shadow(0 26px 30px rgba(0,0,0,.28))}
.card{position:absolute;background:#fff;border-radius:10px 56px 10px 10px;box-shadow:0 34px 70px -28px rgba(0,0,0,.6);overflow:hidden}
.card img{position:absolute;display:block}
.card img.mul{mix-blend-mode:multiply}
.badges{position:absolute;left:22px;top:22px;display:flex;gap:8px}
.badge{display:inline-flex;align-items:center;height:28px;padding:2px 13px 0;border-radius:999px;font-size:13px;font-weight:700;
       text-transform:uppercase;letter-spacing:.06em;color:#fff;line-height:1}
.b-light{background:var(--light)}.b-medium{background:var(--medium)}.b-heavy{background:var(--heavy)}.b-new{background:var(--orange)}
.photo{position:absolute;border-radius:10px 56px 10px 10px;overflow:hidden;box-shadow:0 34px 70px -28px rgba(0,0,0,.6);background:var(--navy)}
.photo img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}
""".replace('ROOTVARS', ''.join(f'--{k}:{v};' for k, v in COL.items()))

FIT_JS = """
async () => {
  await document.fonts.ready;
  await Promise.all([...document.images].map(i => i.complete ? 0 : new Promise(r => { i.onload = i.onerror = r; })));
  const col = document.querySelector('.txt'), h = document.querySelector('h1'), eb = document.querySelector('.eb'), ft = document.querySelector('.ft');
  const st = document.querySelector('.stats');
  const colR = col.getBoundingClientRect();
  const lineInfo = el => {
    const r = document.createRange(); r.selectNodeContents(el);
    const tops = new Set(); let right = -1e9;
    for (const q of r.getClientRects()) { if (q.width < 1) continue; tops.add(Math.round(q.top / 4)); right = Math.max(right, q.right); }
    return {lines: tops.size, right};
  };
  let es = 15;
  const ebFits = () => eb.scrollWidth <= eb.clientWidth + .5;
  while (!ebFits() && es > 12) { es -= .5; eb.style.fontSize = es + 'px'; }
  if (!ebFits()) eb.classList.add('wrap');
  // headline: largest size that fits; first with max MAXL lines, then (very long titles) one line more
  let s = MAXS, maxl = MAXL;
  const ok = () => { const li = lineInfo(h); return li.lines <= maxl && li.right <= colR.right + .5 && col.scrollHeight <= col.clientHeight + .5; };
  h.style.fontSize = s + 'px';
  while (!ok() && s > MINS) { s -= 1; h.style.fontSize = s + 'px'; }
  if (!ok()) { maxl = MAXL + 1; s = MAXS; h.style.fontSize = s + 'px'; while (!ok() && s > MINS) { s -= 1; h.style.fontSize = s + 'px'; } }
  let dropped = 0;
  const ftFits = () => ft.scrollWidth <= ft.clientWidth + .5;
  while (!ftFits() && ft.querySelectorAll('.u').length > 1) { const u = ft.querySelectorAll('.u'); u[u.length - 1].remove(); ft.querySelectorAll('i')[ft.querySelectorAll('i').length - 1].remove(); dropped++; }
  const li = lineInfo(h);
  const ebR = eb.getBoundingClientRect(), hR = h.getBoundingClientRect(), ftR = ft.getBoundingClientRect(), lg = document.querySelector('.logo').getBoundingClientRect();
  const vis = [...document.querySelectorAll('.card,.photo,img.cut')].map(e => e.getBoundingClientRect());
  const txtRight = Math.max(li.right, ebR.right, st ? st.getBoundingClientRect().right : 0);
  const visLeft = Math.min(...vis.map(r => r.left));
  return {size: s, lines: li.lines, ebSize: es, ebWrap: eb.classList.contains('wrap'), dropped,
          problems: [
            li.right > colR.right + .5 ? 'headline wider than column' : null,
            li.lines > maxl ? 'headline too many lines' : null,
            col.scrollHeight > col.clientHeight + .5 ? 'text block taller than zone' : null,
            !ebFits() && !eb.classList.contains('wrap') ? 'eyebrow overflow' : null,
            ebR.right > colR.right + .5 ? 'eyebrow wider than column' : null,
            st && st.scrollWidth > st.clientWidth + .5 ? 'stats overflow' : null,
            !ftFits() ? 'footer overflow' : null,
            ebR.top < lg.bottom + 8 ? 'text touches logo' : null,
            hR.bottom > ftR.top - 8 ? 'text touches footer' : null,
            txtRight > visLeft - 12 ? 'text touches image' : null,
            vis.some(r => r.top < 8 || r.bottom > 622) ? 'image too close to edge' : null,
          ].filter(Boolean)};
}
"""


def page_html(pid, lang, A):
    vis = visual_of(pid)
    q = q_of(pid, vis)
    eyebrow, h1, stats, usps = texts(pid, lang)
    prod = stats is not None
    wtxt = 560
    rhtml = right_panel(pid, vis, lang, A)
    usp_html = ''.join(('<i></i>' if i else '') + f'<span class="u">{html.escape(tidy(u))}</span>' for i, u in enumerate(usps))
    stats_html = ''
    if prod:
        stats_html = '<div class="stats">' + ''.join(f'<div class="stat"><b>{html.escape(v)}<i>kg</i></b><small>{html.escape(lbl)}</small></div>'
                                                     for v, lbl in stats) + '</div>'
    css = CSS.replace('WTXTpx', f'{wtxt}px')
    doc = f"""<!doctype html><html lang="{SC.HTML_LANG[lang]}"><head><meta charset="utf-8"><style>{font_faces()}{css}</style></head>
<body><div class="og" style="--acc:{Q_RGB[q]}">
<img class="q" src="file://{A.q(q)}" alt="">
<div class="logo">{build.logo_svg(white=True)}</div>
<div class="txt"><p class="eb"><span>{html.escape(tidy(eyebrow))}</span></p><h1{' class="prod"' if prod else ''}>{headline_html(h1)}</h1>{stats_html}</div>
{rhtml}
<div class="ft"><b>qpall.com</b><span class="bar"></span>{usp_html}</div>
</div></body></html>"""
    maxs, mins, maxl = (48, 30, 3) if prod else (60, 34, 3)
    return doc, FIT_JS.replace('MAXS', str(maxs)).replace('MINS', str(mins)).replace('MAXL', str(maxl))


def save_jpeg(png_bytes, dest):
    im = Image.open(io.BytesIO(png_bytes)).convert('RGB')
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    for q, sub in ((84, 0), (84, 2), (80, 2), (76, 2), (70, 2)):
        buf = io.BytesIO()
        im.save(buf, 'JPEG', quality=q, subsampling=sub, optimize=True, progressive=True)
        if buf.tell() <= MAX_KB * 1024:
            break
    open(dest, 'wb').write(buf.getvalue())
    return buf.tell(), q, sub


def og_key(pid):
    return 'p-' + pid[2:] if pid.startswith('p:') else pid


def all_pids(only=None):
    pages = [pid for pid in SC.PAGES if not pid.startswith('p:')]
    prods = ['p:' + m['id'] for m in build.MODELS]
    return {'pages': pages, 'products': prods}.get(only, pages + prods)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--lang', choices=SC.LANGS, action='append', help='language (repeatable); default: all')
    ap.add_argument('--page', action='append', help="page id or 'p:<model id>' (repeatable); default: every page")
    ap.add_argument('--only', choices=('pages', 'products'), help='only the content pages or only the product pages')
    ap.add_argument('--out', default=OUT, help='output folder (default data/og)')
    a = ap.parse_args()
    langs = a.lang or SC.LANGS
    pids = a.page or all_pids(a.only)
    tmp = tempfile.mkdtemp(prefix='qp-og-')
    A = Assets(tmp)
    report, problems = [], []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            pg = browser.new_page(viewport={'width': W, 'height': H}, device_scale_factor=DSF)
            for lang in langs:
                for pid in pids:
                    doc, js = page_html(pid, lang, A)
                    fn = os.path.join(tmp, 'og.html')
                    open(fn, 'w', encoding='utf-8').write(doc)
                    pg.goto('file://' + fn, wait_until='load')
                    info = pg.evaluate(js)
                    png = pg.screenshot(type='png', clip={'x': 0, 'y': 0, 'width': W, 'height': H})
                    dest = os.path.join(a.out, lang, og_key(pid) + '.jpg')
                    size, q, sub = save_jpeg(png, dest)
                    report.append((lang, pid, size, info))
                    if info['problems'] or size > MAX_KB * 1024:
                        problems.append((lang, pid, info['problems'] + ([f'{size // 1024} KB'] if size > MAX_KB * 1024 else [])))
                    if len(pids) * len(langs) <= 40 or info['problems']:
                        print(f"{lang} {pid:28s} {size / 1024:6.1f} KB  q{q}  h1 {info['size']}px/{info['lines']} lines"
                              f"{'  eyebrow ' + str(info['ebSize']) + 'px' if info['ebSize'] != 15 else ''}{'  (wrapped)' if info['ebWrap'] else ''}"
                              f"{'  usp dropped' if info['dropped'] else ''}{'  PROBLEM: ' + ', '.join(info['problems']) if info['problems'] else ''}", flush=True)
            browser.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    en_home = os.path.join(a.out, 'en', 'home.jpg')
    if os.path.exists(en_home):
        shutil.copy(en_home, os.path.join(a.out, 'og-image.jpg'))
    tot = sum(r[2] for r in report)
    if report:
        big = max(report, key=lambda r: r[2])
        print(f'{len(report)} images, total {tot / 1048576:.1f} MB, largest {big[0]}/{og_key(big[1])}.jpg {big[2] / 1024:.1f} KB')
    if problems:
        print('PROBLEMS:')
        for pr in problems:
            print('  ', *pr)
        sys.exit(1)


if __name__ == '__main__':
    main()
