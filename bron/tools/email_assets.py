"""Product photos for the e-mails (update 26): one small jpg per article number in root/assets/email/p/<sku>.jpg.
E-mail programs (Outlook) do not show webp, so the e-mails need jpg. Run after build.py when products or photos change:
    python3 tools/email_assets.py ../qpall-website     (then build.py again, or copy root/assets/email to the site)"""
import os, re, sys, html
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, '..', 'qpall-website')
OUT = os.path.join(ROOT, 'root', 'assets', 'email', 'p')
os.makedirs(OUT, exist_ok=True)
page = open(os.path.join(SITE, 'offerte-aanvraag', 'index.html'), encoding='utf-8').read()
n = 0
for v, a in re.findall(r'<option value="([^"]+)"([^>]*)>', page):
    m = re.search(r'data-img="([^"]+)"', a)
    if 'data-stack' not in a or not m:
        continue
    sku = html.unescape(v).split(' – ')[0].strip()
    src = os.path.join(SITE, m.group(1).lstrip('/'))
    big = src.replace('-320.webp', '-640.webp')
    im = Image.open(big if os.path.exists(big) else src).convert('RGB')
    im.thumbnail((192, 128))
    c = Image.new('RGB', (192, 128), 'white'); c.paste(im, ((192 - im.width) // 2, (128 - im.height) // 2))
    c.save(os.path.join(OUT, re.sub(r'[^a-z0-9.-]+', '-', sku.lower()) + '.jpg'), quality=85, optimize=True); n += 1
print(n, 'product photos in', OUT)

# accessories (update 37): their photo from the site as a jpg too, so the quote confirmation shows every product
sys.path.insert(0, ROOT)
os.environ.setdefault('QP_KEEP_IMAGES', '1')
_argv = sys.argv; sys.argv = ['build.py']
import build as B   # noqa: E402  (loads the data only)
sys.argv = _argv
k = 0
for a in B.ACCS:
    rel = B.acc_item(a, 'nl').get('img') or ''
    src = os.path.join(SITE, rel.lstrip('/'))
    if not rel.endswith('.webp') or not os.path.exists(src):
        continue
    im = Image.open(src).convert('RGBA')
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg.convert('RGB')
    im.thumbnail((192, 128))
    c = Image.new('RGB', (192, 128), 'white'); c.paste(im, ((192 - im.width) // 2, (128 - im.height) // 2))
    c.save(os.path.join(OUT, re.sub(r'[^a-z0-9.-]+', '-', a['sku'].lower()) + '.jpg'), quality=85, optimize=True); k += 1
print(k, 'accessory photos in', OUT)
