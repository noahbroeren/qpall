"""Assets, images, downloads, SEO files and Netlify config for build.py."""
import os, re, json, shutil, glob, subprocess, tempfile
import numpy as np
from PIL import Image, ImageFilter
from site_config import (LANGS, X_DEFAULT, CATALOG_FILES, BUILD_DATE, DOMAIN, REDIRECTS, PREFIX, PAGES as _P, COMPANY)
from build_util import slugify

IMG_Q = 84


def clean_out(OUT, keep):
    if os.path.exists(OUT):
        for item in os.listdir(OUT):
            pth = os.path.join(OUT, item)
            if keep and item == 'assets':
                for sub in os.listdir(pth):
                    if sub not in ('img', 'og'):
                        shutil.rmtree(os.path.join(pth, sub), ignore_errors=True)
                continue
            if keep and item in ('og-image.jpg', 'favicon.svg', 'favicon-48.png', 'apple-touch-icon.png', 'icon-192.png', 'icon-512.png',
                                 'favicon.ico', 'downloads', 'pagefind'):
                continue
            shutil.rmtree(pth) if os.path.isdir(pth) else os.remove(pth)
    os.makedirs(OUT, exist_ok=True)


def copy_static(ROOT, OUT):
    rootdir = os.path.join(ROOT, 'root')
    if os.path.isdir(rootdir):
        shutil.copytree(rootdir, OUT, dirs_exist_ok=True, ignore=shutil.ignore_patterns('LEESMIJ-*', '.DS_Store'))
    dst = os.path.join(OUT, 'assets')
    for sub in ('css', 'js', 'fonts', 'sb'):
        shutil.copytree(os.path.join(ROOT, 'static', sub), os.path.join(dst, sub), dirs_exist_ok=True)
    # load calculator: Noah's engine (static/calc/engine.js, unchanged) + the site UI (ui.js) as one file;
    # only pages with the calculator load it (product pages, transport)
    eng = open(os.path.join(ROOT, 'static/calc/engine.js'), encoding='utf-8').read()
    ui = open(os.path.join(ROOT, 'static/calc/ui.js'), encoding='utf-8').read()
    with open(os.path.join(dst, 'js', 'calc.js'), 'w', encoding='utf-8') as fh:
        fh.write("/* Q-Pall laadcalculator */\n(function () {\nif (!document.getElementById('qpc')) return;\n" + eng + "\n" + ui + "\n})();\n")
    # the SimplyBook frame loads sb-frame.js; /assets/js is cached for a year, so give it a version
    import hashlib
    sbv = hashlib.md5(open(os.path.join(ROOT, 'static/js/sb-frame.js'), 'rb').read()).hexdigest()[:8]
    fp = os.path.join(dst, 'sb', 'frame.html')
    html = open(fp, encoding='utf-8').read().replace('/assets/js/sb-frame.js"', f'/assets/js/sb-frame.js?v={sbv}"')
    open(fp, 'w', encoding='utf-8').write(html)
    os.makedirs(os.path.join(dst, 'img/brand'), exist_ok=True)
    for f in glob.glob(os.path.join(ROOT, 'static/img/brand/*.svg')) + glob.glob(os.path.join(ROOT, 'static/img/brand/badge-*.webp')):
        shutil.copy(f, os.path.join(dst, 'img/brand', os.path.basename(f)))
    # contact person photos (homepage 'Praat met een specialist'), see SPECIALIST in site_config.py
    shutil.copytree(os.path.join(ROOT, 'static/img/team'), os.path.join(dst, 'img/team'), dirs_exist_ok=True)
    # Q-op-ondergrond backgrounds (made by tools/q_backgrounds.py)
    shutil.copytree(os.path.join(ROOT, 'static/img/q'), os.path.join(dst, 'img/q'), dirs_exist_ok=True)
    shutil.copy(os.path.join(ROOT, 'input/logo/logo-qpall-2025-RGB_kleur.png'), os.path.join(dst, 'img/brand/q-pall-logo.png'))


# Covers with a dense granule texture that weighed 260-330 KB at 1200w (second analysis, 2-11-2026): blur radius, quality.
HEAVY_COVERS = {'regrind': (0.8, 65), 'n-green-logistics': (0.8, 65)}


def _save(im, full, width, quality=IMG_Q):
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(full, 'WEBP', quality=quality, method=6)


def _open_rgb(path, bg=(255, 255, 255)):
    im = Image.open(path)
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA')
        b = Image.new('RGBA', im.size, bg + (255,))
        b.alpha_composite(im)
        im = b
    return im.convert('RGB')


def cutout(path):
    """Dark product photo on white -> RGBA: pallet opaque, photo shadow becomes a soft dark shadow (no white halo)."""
    im = Image.open(path).convert('RGB')
    a = np.asarray(im).astype(np.float32)
    L = a.mean(axis=2)
    t = np.clip((L - 110) / 140, 0, 1)
    alpha = np.where(L < 110, 1.0, np.clip((252 - L) / 142, 0, 1))
    col = a * (1 - t[..., None] * 0.85)
    out = np.dstack([np.clip(col, 0, 255), alpha * 255]).astype(np.uint8)
    img = Image.fromarray(out, 'RGBA')
    bb = img.getbbox()
    return img.crop(bb) if bb else img


def build_hero(ROOT, OUT):
    d = os.path.join(OUT, 'assets/img/hero')
    os.makedirs(d, exist_ok=True)
    for f in glob.glob(os.path.join(ROOT, 'input/hero/*.png')):
        name = os.path.splitext(os.path.basename(f))[0]
        im = Image.open(f).convert('RGBA')
        for w in (640, 960, 1280):
            r = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS) if im.width > w else im
            r.save(os.path.join(d, f'{name}-{w}.webp'), 'WEBP', quality=84, alpha_quality=90, method=6)
            # AVIF: same look at about a third of the size (homepage hero + promo, <picture> with WebP fallback)
            r.save(os.path.join(d, f'{name}-{w}.avif'), 'AVIF', quality=60, speed=6)


def build_images(ROOT, OUT, MODELS, ACCS, acc_item, LANGS, HERO_MODELS):
    P = os.path.join(ROOT, 'input/photos')
    A = os.path.join(OUT, 'assets/img')
    done = set()
    for m in MODELS:
        if m['photo_id'] in done:          # articles of one family share one set of image files
            continue
        done.add(m['photo_id'])
        d = os.path.join(P, m['photo_id'])
        base = os.path.join(A, 'pallets', m['photo_slug'])
        for i in range(1, m['n_photos'] + 1):
            src = _open_rgb(os.path.join(d, f'{i}.webp'))
            if i == 1:
                for w in (320, 640, 1200):
                    _save(src, f'{base}-{w}.webp', w)
            for w in (320, 960, 1600):
                _save(src, f'{base}-{i}-{w}.webp', w)
    # accessories (catalogue images)
    raw = os.path.join(ROOT, 'input/raw')
    for a in ACCS:
        for l in LANGS:
            acc_item(a, l)
        if a.get('_img_file') and a.get('img'):
            src = next((os.path.join(raw, f"x{a['img']}{e}") for e in ('.webp', '.png', '.jpg') if os.path.exists(os.path.join(raw, f"x{a['img']}{e}"))), None)
            if src:
                _save(_open_rgb(src), os.path.join(OUT, a['_img_file'].lstrip('/')), 640)
    # brand photos
    for f in glob.glob(os.path.join(ROOT, 'input/brand/photo-*.webp')):
        name = os.path.basename(f).replace('photo-', '').replace('.webp', '')
        im = _open_rgb(f)
        if name in HEAVY_COVERS:     # granule texture: mild blur + lower quality + a 960w step (update 30)
            for w in (640, 960, 1200):
                r = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS) if im.width > w else im
                r = r.filter(ImageFilter.GaussianBlur(HEAVY_COVERS[name][0] if w > 640 else HEAVY_COVERS[name][0] * 0.6))
                r.save(os.path.join(A, 'photos', f'{name}-{w}.webp'), 'WEBP', quality=HEAVY_COVERS[name][1], method=6)
            continue
        for w in ((640, 1200, 1600) if name == 'seaturtle' else (640, 1200)):
            _save(im, os.path.join(A, 'photos', f'{name}-{w}.webp'), w, 82)
    # free-standing hero pallets (input/hero/<class>.png, made by tools/hero_cutouts.py), transparent WebP
    build_hero(ROOT, OUT)
    # the sea turtle comes from input/brand/photo-seaturtle.webp (cropped from the original artwork)
    # brochure images (made by tools/booklets.py): catalogue, PPWR declaration, technical datasheet
    os.makedirs(os.path.join(A, 'booklets'), exist_ok=True)
    for key, name in (('catalogus', 'catalogus'), ('ppwr', 'ppwr'), ('technische-datasheet', 'datasheet')):
        f = os.path.join(ROOT, 'input/mockups', f'q-pall-boekje-{key}.png')
        if not os.path.exists(f):
            continue
        im = Image.open(f).convert('RGBA')
        im = im.crop(im.getbbox())
        for w in (120, 240, 480, 800):
            c = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
            c.save(os.path.join(A, 'booklets', f'{name}-{w}.webp'), 'WEBP', quality=88, method=6)
    # accessory photos (input/acc-photos/<name>.png|jpg|webp, white background)
    for f in sorted(glob.glob(os.path.join(ROOT, 'input/acc-photos/*.*'))):
        name = os.path.splitext(os.path.basename(f))[0]
        im = Image.open(f).convert('RGBA')
        bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
        im = bg.convert('RGB')
        if im.width > 800:
            im = im.resize((800, round(im.height * 800 / im.width)), Image.LANCZOS)
        os.makedirs(os.path.join(A, 'acc'), exist_ok=True)
        im.save(os.path.join(A, 'acc', f'photo-{name}.webp'), 'WEBP', quality=84, method=6)
    make_icons(ROOT, OUT)


def make_icons(ROOT, OUT):
    q = os.path.join(ROOT, 'static/img/brand/q-mark.svg')
    shutil.copy(q, os.path.join(OUT, 'favicon.svg'))
    qpng = os.path.join(ROOT, 'static/img/brand/png/q-mark-480.png')
    qm = Image.open(qpng).convert('RGBA')

    def on(size, bg, pad):
        im = Image.new('RGBA', (size, size), bg)
        inner = qm.copy()
        inner.thumbnail((int(size * (1 - 2 * pad)), int(size * (1 - 2 * pad))), Image.BOX)  # BOX: no colour overshoot at the edges
        im.alpha_composite(inner, ((size - inner.width) // 2, (size - inner.height) // 2))
        return im
    on(48, (0, 0, 0, 0), .04).save(os.path.join(OUT, 'favicon-48.png'))
    on(180, (29, 28, 76, 255), .18).convert('RGB').save(os.path.join(OUT, 'apple-touch-icon.png'))
    on(192, (29, 28, 76, 255), .2).save(os.path.join(OUT, 'icon-192.png'))
    on(512, (29, 28, 76, 255), .22).save(os.path.join(OUT, 'icon-512.png'))
    on(64, (0, 0, 0, 0), .04).save(os.path.join(OUT, 'favicon.ico'), sizes=[(16, 16), (32, 32), (48, 48)])


def copy_downloads(ROOT, OUT):
    for l, rel in CATALOG_FILES.items():
        src = os.path.join(ROOT, 'input/catalogus', l + '.pdf')
        dst = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(src) and (not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(src)):
            shutil.copy(src, dst)
            os.chmod(dst, 0o644)
    pd = os.path.join(OUT, 'downloads/ppwr')
    os.makedirs(pd, exist_ok=True)
    for f in glob.glob(os.path.join(ROOT, 'input/ppwr/*.pdf')):
        shutil.copy(f, os.path.join(pd, os.path.basename(f)))
    # datasheets are generated by tools/datasheets.py into data/datasheets/<lang>/
    ds = os.path.join(ROOT, 'data/datasheets')
    if os.path.isdir(ds):
        shutil.copytree(ds, os.path.join(OUT, 'downloads/datasheets'), dirs_exist_ok=True)
    og = os.path.join(ROOT, 'data/og')
    if os.path.isdir(og):
        shutil.copytree(og, os.path.join(OUT, 'assets/og'), dirs_exist_ok=True)
        dflt = os.path.join(og, 'en', 'home.jpg')
        if os.path.exists(dflt):
            shutil.copy(dflt, os.path.join(OUT, 'og-image.jpg'))


def page_lastmod(OUT, rel, man, today):
    """<lastmod> = the date the page's content last changed (title, description or <main>), kept in data/lastmod.json.
    Header, footer, menu and share images do not count, so a site-wide template change leaves the dates alone."""
    import hashlib
    f = os.path.join(OUT, rel)
    if rel == '' or rel.endswith('/'):
        f = os.path.join(f, 'index.html')
    s = open(f, encoding='utf-8').read()
    parts = [re.search(r'<title>.*?</title>', s, re.S), re.search(r'<meta name="description"[^>]*>', s), re.search(r'<main\b.*?</main>', s, re.S)]
    h = hashlib.sha1(''.join(x.group(0) for x in parts if x).encode('utf-8')).hexdigest()[:16]
    key = '/' + rel
    if man.get(key, {}).get('h') != h:
        man[key] = {'h': h, 'd': today}
    return man[key]['d']


def write_seo_files(OUT, page_list, PAGES, MODEL_BY_ID, abs_url):
    from site_config import HTML_LANG
    import datetime
    man_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/lastmod.json')
    man = json.load(open(man_path)) if os.path.exists(man_path) else {}
    today = os.environ.get('QP_DATE') or datetime.date.today().isoformat()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for pid in page_list:
        p = PAGES[pid]
        if p.get('noindex'):
            continue
        for l in LANGS:
            lines.append('  <url>')
            lines.append(f'    <loc>{abs_url("/" + p["path"][l])}</loc>')
            for l2 in LANGS:
                lines.append(f'    <xhtml:link rel="alternate" hreflang="{HTML_LANG[l2]}" href="{abs_url("/" + p["path"][l2])}"/>')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{abs_url("/" + p["path"][X_DEFAULT])}"/>')
            lines.append(f'    <lastmod>{page_lastmod(OUT, p["path"][l], man, today)}</lastmod>')
            if pid.startswith('p:'):
                m = MODEL_BY_ID[p['model']]
                for g in m['gallery'][:3]:
                    lines.append(f'    <image:image><image:loc>{abs_url(g["lg"])}</image:loc></image:image>')
            lines.append('  </url>')
    lines.append('</urlset>')
    open(os.path.join(OUT, 'sitemap.xml'), 'w').write('\n'.join(lines) + '\n')
    json.dump(dict(sorted(man.items())), open(man_path, 'w'), indent=0)
    # robots.txt: one group for all crawlers, the AI assistants named explicitly in the same group (a crawler
    # with a group of its own would ignore the '*' rules). The thank-you pages are NOT disallowed: they carry
    # <meta name="robots" content="noindex, follow">, which Google can only see when it may fetch the page.
    open(os.path.join(OUT, 'robots.txt'), 'w').write(
        "# Alle zoekmachines en AI-assistenten (GPTBot, ClaudeBot, PerplexityBot, Google-Extended) mogen de site lezen\n"
        "User-agent: *\nUser-agent: GPTBot\nUser-agent: ClaudeBot\nUser-agent: PerplexityBot\nUser-agent: Google-Extended\n"
        "Allow: /\nDisallow: /pagefind/\n\n"
        "Sitemap: " + DOMAIN + "/sitemap.xml\n")
    manifest = {'name': 'Q-Pall – plastic pallets', 'short_name': 'Q-Pall', 'start_url': '/', 'display': 'standalone',
                'background_color': '#ffffff', 'theme_color': '#1D1C4C', 'lang': 'nl',
                'icons': [{'src': '/icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any maskable'},
                          {'src': '/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any maskable'}]}
    open(os.path.join(OUT, 'site.webmanifest'), 'w').write(json.dumps(manifest, indent=2))
    ROOT = os.path.dirname(os.path.abspath(__file__))
    rd = ['# Q-Pall redirects (Netlify). Format: from  to  status. De eerste regel die past wint.',
          '/LEESMIJ.txt  /404.html  404!',
          '/netlify/*  /404.html  404!']   # source of the Netlify function (mail templates) is not a page
    # final redirect file of iClicks (9 Nov 2026): the old URLs that still gave a 404 (data/redirects-iclicks.txt).
    # The whole file is checked with tools/redirects_iclicks_check.py (data/oude-site/iclicks-redirects-2026-11-09.tsv).
    _icl = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/redirects-iclicks.txt')
    if os.path.exists(_icl):
        rd += [l.rstrip() for l in open(_icl, encoding='utf-8') if l.strip()]
    # update 45: pages and datasheets of articles that are not on the site (draft or removed) and draft articles
    _rem = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/redirects-removed.txt')
    if os.path.exists(_rem):
        rd += [l.rstrip() for l in open(_rem, encoding='utf-8') if l.strip()]
    # old country domains -> category page in their language, in one step (site_config.COUNTRY_DOMAINS)
    from site_config import COUNTRY_DOMAINS
    rd.append('# Oude landendomeinen (ook als domain alias in Netlify toevoegen)')
    for dom, l in COUNTRY_DOMAINS:
        target = DOMAIN + '/' + PAGES['pallets']['path'][l]
        for host in (dom, 'www.' + dom):
            for scheme in ('https', 'http'):
                rd.append(f'{scheme}://{host}/*  {target}  301!')
    extra = os.path.join(ROOT, 'data/redirects-extra.txt')
    if os.path.exists(extra):
        rd += ['# Eigen redirects (data/redirects-extra.txt)'] + [l.rstrip() for l in open(extra, encoding='utf-8') if l.strip()]
    gsc = os.path.join(ROOT, 'data/redirects-gsc.txt')       # older URLs from Search Console (tools/redirects_gsc.py)
    if os.path.exists(gsc):
        rd += [l.rstrip() for l in open(gsc, encoding='utf-8') if l.strip()]
    rd.append("# Oude losse pagina's")
    for a, b in REDIRECTS:
        rd.append(f'{a}  {b}  301')
    # no '/vacatures/*  /vacatures/' or '/nieuws/*  /nieuws/': Netlify ignores a splat rule whose destination falls under
    # its own pattern (tested 10 Nov 2026: 404). Known old vacancy and news URLs have their own rule instead.
    rd += ['/offerte-aanvraag/bevestigen  /bedankt/  301', '/en/vacancies/*  /en/careers/  301']
    # news: the articles keep their old URL (Netlify adds the slash); every other old news URL goes to the news overview
    from site_config import NEWS_ITEMS, LANGS as _LANGS
    rd.append('# Nieuws')
    for pid in NEWS_ITEMS:
        for l in _LANGS:
            p = '/' + PAGES[pid]['path'][l]
            rd.append(f'{p.rstrip("/")}  {p}  301')
    rd.append('# Foutpagina per taal')
    for l in ('en', 'de', 'fr', 'it', 'es'):
        rd.append(f'/{l}/*  /{l}/404.html  404')
    rd = _flatten(rd, OUT)
    open(os.path.join(OUT, '_redirects'), 'w').write('\n'.join(rd) + '\n')


def _flatten(rd, OUT):
    """Redirects in one step (update 45): when the destination of a 301 rule is itself the source of an exact 301 rule
    (for example an old qpall.com URL that pointed to a pallet that is now off the site), the rule gets the final
    destination. A destination that exists as a page is never followed (Netlify serves the page there)."""
    def norm(p):
        return p.rstrip('/') or '/'
    def is_page(p):
        f = os.path.join(OUT, p.split('?')[0].lstrip('/'))
        return os.path.isfile(f) or os.path.isfile(os.path.join(f, 'index.html'))
    exact = {}
    for line in rd:
        parts = line.split()
        if len(parts) >= 3 and not line.startswith('#') and '*' not in parts[0] and not parts[0].startswith('http') \
                and parts[2].startswith('30') and not parts[1].startswith('http'):
            exact.setdefault(norm(parts[0]), parts[1])
    out = []
    for line in rd:
        parts = line.split()
        if len(parts) >= 3 and not line.startswith('#') and parts[2].startswith('30') and not parts[1].startswith('http'):
            dst, n = parts[1], 0
            while norm(dst.split('?')[0]) in exact and not is_page(dst) and n < 6:
                dst, n = exact[norm(dst.split('?')[0])], n + 1
            if n:
                line = f'{parts[0]}  {dst}  {parts[2]}'
        out.append(line)
    return out


def write_netlify(OUT):
    # The Content-Security-Policy lives in a <meta> tag: strict on every page (templates/base.html),
    # looser only inside the SimplyBook frame (static/sb/frame.html). A site-wide CSP header would
    # also apply to that frame and cannot be relaxed per path on Netlify (matching rules are merged).
    from site_config import NOINDEX_ALL
    robots_hdr = '    X-Robots-Tag = "noindex, nofollow"\n' if NOINDEX_ALL else ''
    toml = f'''# Netlify configuratie voor qpall.com
[build]
  publish = "."

# Functie submission-created: stuurt na elke offerteaanvraag de bevestigingsmail via Brevo (update 37).
# Zet in Netlify de omgevingsvariabele BREVO_API_KEY; zonder sleutel verstuurt de functie niets.
[functions]
  directory = "netlify/functions"

[[headers]]
  for = "/*"
  [headers.values]
    X-Content-Type-Options = "nosniff"
    X-Frame-Options = "SAMEORIGIN"
    Referrer-Policy = "strict-origin-when-cross-origin"
    Permissions-Policy = "camera=(), microphone=(), geolocation=()"
    Strict-Transport-Security = "max-age=31536000; includeSubDomains"
{robots_hdr}
[[headers]]
  for = "/assets/fonts/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"
    Access-Control-Allow-Origin = "*"

[[headers]]
  for = "/assets/css/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"

[[headers]]
  for = "/assets/js/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"

[[headers]]
  for = "/assets/img/*"
  [headers.values]
    Cache-Control = "public, max-age=86400"

[[headers]]
  for = "/assets/og/*"
  [headers.values]
    Cache-Control = "public, max-age=86400"

[[headers]]
  for = "/pagefind/*"
  [headers.values]
    Cache-Control = "public, max-age=3600"

[[headers]]
  for = "/downloads/*"
  [headers.values]
    Cache-Control = "public, max-age=86400"
    X-Robots-Tag = "noindex"

# Canonieke host: www.qpall.com, zoals de huidige site (update 42; zet in Netlify www.qpall.com als primair domein)
[[redirects]]
  from = "https://qpall.com/*"
  to = "https://www.qpall.com/:splat"
  status = 301
  force = true
'''
    open(os.path.join(OUT, 'netlify.toml'), 'w').write(toml)
