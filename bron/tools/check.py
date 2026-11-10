"""Quality checks over the built site (6 languages): links, tags, meta, hreflang, JSON-LD, images, ids, og:image."""
import os, re, json, sys, glob
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote

OUT = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('QP_OUT') or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'qpall-website')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from site_config import NOINDEX_ALL, DOMAIN  # site-wide noindex (pre-launch): pages are still checked as if indexable
LANGS = {'nl', 'en', 'de', 'fr', 'it', 'es'}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr', 'use', 'path', 'circle', 'rect', 'line', 'stop'}


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors, self.links, self.ids, self.imgs, self.ld = [], [], [], [], [], []
        self.meta = {}
        self.in_ld = False
        self.buf = ''
        self.title = ''
        self.in_title = False
        self.alts = []
        self.h1 = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.append(a['id'])
        if tag == 'a' and 'href' in a:
            self.links.append(a['href'])
        if tag == 'link' and a.get('rel') in ('canonical', 'alternate', 'stylesheet', 'icon', 'manifest', 'apple-touch-icon', 'preload'):
            self.links.append(a.get('href'))
            if a.get('rel') == 'canonical':
                self.meta['canonical'] = a['href']
            if a.get('rel') == 'alternate':
                self.meta.setdefault('alt', []).append((a.get('hreflang'), a['href']))
        if tag == 'img':
            self.imgs.append(a.get('src'))
            if 'alt' not in a:
                self.errors.append('img without alt ' + str(a.get('src')))
        if tag == 'script' and a.get('src'):
            self.links.append(a['src'])
        if tag == 'meta' and a.get('name') == 'description':
            self.meta['description'] = a.get('content', '')
        if tag == 'meta' and a.get('name') == 'robots':
            self.meta['robots'] = a.get('content', '')
        if tag == 'html':
            self.meta['lang'] = a.get('lang')
        if tag == 'meta' and a.get('property') == 'og:image':
            self.meta['og'] = a.get('content')
        if tag == 'title' and 'head' in self.stack and 'svg' not in self.stack:
            self.in_title = True
        if tag == 'h1':
            self.h1 += 1
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.in_ld = True
            self.buf = ''
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.stack and self.stack[-1] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag == 'title':
            self.in_title = False
        if tag == 'script' and self.in_ld:
            self.in_ld = False
            try:
                self.ld.append(json.loads(self.buf))
            except Exception as e:
                self.errors.append('bad json-ld ' + str(e))
        if not self.stack:
            self.errors.append('extra close ' + tag)
            return
        if self.stack[-1] == tag:
            self.stack.pop()
        else:
            # find
            if tag in self.stack:
                while self.stack and self.stack[-1] != tag:
                    t = self.stack.pop()
                    if t not in ('p', 'li', 'option', 'td', 'th', 'tr', 'dt', 'dd'):
                        self.errors.append(f'unclosed {t} before </{tag}>')
                self.stack.pop()
            else:
                self.errors.append('stray close ' + tag)

    def handle_data(self, data):
        if self.in_ld:
            self.buf += data
        if self.in_title:
            self.title += data


def resolve(path):
    p = unquote(urlparse(path).path)
    full = os.path.join(OUT, p.lstrip('/'))
    if p.endswith('/'):
        full = os.path.join(full, 'index.html')
    return os.path.exists(full)


pages = sorted(f for f in glob.glob(os.path.join(OUT, '**/*.html'), recursive=True) if '/assets/' not in f and '/pagefind/' not in f)
ALT = {}
problems = []
all_alts = {}
titles = {}
descs = {}
broken = {}
ld_types = {}
for f in pages:
    rel = '/' + os.path.relpath(f, OUT).replace('index.html', '')
    h = open(f, encoding='utf-8').read()
    p = P()
    p.feed(h)
    for e in p.errors:
        problems.append((rel, e))
    if p.stack and p.stack != []:
        problems.append((rel, 'unclosed at end: ' + ','.join(p.stack[-5:])))
    dup = {i for i in p.ids if p.ids.count(i) > 1}
    if dup:
        problems.append((rel, 'duplicate ids ' + ','.join(sorted(dup))))
    if p.h1 != 1:
        problems.append((rel, f'h1 count {p.h1}'))
    for l in p.links:
        if not l or l.startswith(('mailto:', 'tel:', '#', 'https://app.mach3locator', 'https://nl.linkedin', 'https://www.ippc')):
            continue
        if l.startswith(DOMAIN):
            l2 = l[len(DOMAIN):]
        elif l.startswith('http'):
            continue
        else:
            l2 = l
        if not resolve(l2):
            broken.setdefault(l2, set()).add(rel)
    for i in p.imgs:
        if i and not resolve(i):
            broken.setdefault(i, set()).add(rel)
    robots = p.meta.get('robots', '')
    if NOINDEX_ALL and robots == 'noindex, nofollow':
        robots = 'index, follow'
    seg = rel.strip('/').split('/')[0]
    exp_lang = seg if seg in LANGS - {'nl'} else 'nl'
    if p.meta.get('lang') != exp_lang:
        problems.append((rel, f"html lang {p.meta.get('lang')} expected {exp_lang}"))
    og = p.meta.get('og')
    if not og or not resolve(og[len(DOMAIN):] if og.startswith(DOMAIN) else og):
        problems.append((rel, f'og:image missing {og}'))
    if 'noindex' not in robots and not rel.endswith('/404.html'):
        titles.setdefault(p.title, []).append(rel)
        descs.setdefault(p.meta.get('description'), []).append(rel)
        t, d = p.title, p.meta.get('description', '')
        if len(t) > 60:
            problems.append((rel, f'title {len(t)}'))
        # the category pages carry the exact meta descriptions from the SEO action list (October 2026), up to 160 characters
        if not 120 <= len(d) <= (160 if rel in ('/kunststof-pallets/', '/en/plastic-pallets/', '/de/kunststoffpaletten/', '/fr/palettes-plastique/',
                                                  '/it/pallet-in-plastica/', '/es/palets-de-plastico/') else 156):
            problems.append((rel, f'desc {len(d)}'))
        can = p.meta.get('canonical')
        if can != DOMAIN + rel:
            problems.append((rel, f'canonical mismatch {can}'))
        alts = dict(p.meta.get('alt', []))
        ALT[DOMAIN + rel] = alts
        if set(alts) != LANGS | {'x-default'}:
            problems.append((rel, 'hreflang set ' + str(alts.keys())))
        # reciprocity
        for lg, href in alts.items():
            if not resolve(href[len(DOMAIN):]):
                problems.append((rel, 'hreflang target missing ' + href))
    for j in p.ld:
        ld_types[j.get('@type')] = ld_types.get(j.get('@type'), 0) + 1
        if j.get('@type') == 'Product':
            o = j.get('offers', {})
            if o and (not o.get('price') or o.get('priceCurrency') != 'EUR'):
                problems.append((rel, 'product offer incomplete'))

for u, alts in ALT.items():
    for lg, href in alts.items():
        back = ALT.get(href)
        if back is not None and back != alts:
            problems.append((u, 'hreflang not reciprocal with ' + href))
            break
for t, ps in titles.items():
    if len(ps) > 1:
        problems.append((','.join(ps[:3]), f'duplicate title: {t}'))
for d, ps in descs.items():
    if len(ps) > 1:
        problems.append((','.join(ps[:3]), f'duplicate description: {d}'))

print('pages:', len(pages))
print('json-ld types:', ld_types)
print('broken links/assets:', len(broken))
for k, v in list(broken.items())[:40]:
    print('  BROKEN', k, '<-', list(v)[:3])
print('problems:', len(problems))
for pr in problems[:80]:
    print('  ', pr)
