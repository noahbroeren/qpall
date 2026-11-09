"""Product export: all pallets (no accessories) to one Excel file, with photos.

    QP_KEEP_IMAGES=1 python3 tools/export_xlsx.py [out.xlsx] [site_dir]

Reads the same data as the website build (build.py is imported, nothing is written to the site) and takes the
product photos from the built site (../qpall-website/assets/img/pallets). Sheets:
  Pallets          one row per article number: photos, dimensions, loads, build, locations, stack, links
  Namen en URL's   product name and page URL in the six languages
  Omschrijvingen   the full product text per language (plain text)
  Toelichting      what the columns mean
Prices are left out (SHOW_PRICES is off on the website).
"""
import io
import os
import re
import sys
import html as H
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.argv = sys.argv[:1] + sys.argv[1:]
OUT_XLSX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, '..', 'q-pall-productexport.xlsx')
SITE = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, '..', 'qpall-website')

import build as B  # noqa: E402  (module level only loads data; main() is not run)
from PIL import Image as PILImage  # noqa: E402
from openpyxl import Workbook  # noqa: E402
from openpyxl.drawing.image import Image as XLImage  # noqa: E402
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side  # noqa: E402
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, OneCellAnchor  # noqa: E402
from openpyxl.drawing.xdr import XDRPositiveSize2D  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402
from openpyxl.utils.units import pixels_to_EMU  # noqa: E402

LANGS = ['nl', 'en', 'de', 'fr', 'it', 'es']
LANG_NAME = {'nl': 'Nederlands', 'en': 'Engels', 'de': 'Duits', 'fr': 'Frans', 'it': 'Italiaans', 'es': 'Spaans'}
T = B.T['nl']
DOMAIN = B.DOMAIN
CLASS_ORDER = {'light': 0, 'medium': 1, 'heavy': 2}

FONT = 'Arial'
NAVY = '1F1D4E'
F_HEAD = Font(name=FONT, bold=True, color='FFFFFF', size=10)
F_BODY = Font(name=FONT, size=10)
F_BOLD = Font(name=FONT, size=10, bold=True)
F_LINK = Font(name=FONT, size=10, color='1F4E9E', underline='single')
F_TITLE = Font(name=FONT, size=14, bold=True, color=NAVY)
FILL_HEAD = PatternFill('solid', fgColor=NAVY)
FILL_ZEBRA = PatternFill('solid', fgColor='F5F5F7')
THIN = Side(style='thin', color='DADAE3')
BORDER = Border(bottom=THIN)
TOP_WRAP = Alignment(vertical='top', wrap_text=True)
TOP = Alignment(vertical='top')
CENTER = Alignment(vertical='center', horizontal='center')


def size_key(m):
    a, b = (int(x) for x in m['size'].split('x'))
    return (a, b, CLASS_ORDER.get(m['class'], 9), m['height'][1], m['sku'])


def plain(html):
    """Product text (html) as plain text: headings and paragraphs on their own lines."""
    s = str(html)
    s = re.sub(r'</?(h2|h3)>', '\n', s)
    s = re.sub(r'</p>\s*', '\n', s)
    s = re.sub(r'<li>', '\n- ', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = H.unescape(s).replace('­', '')
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r'\n\s*\n+', '\n\n', s)
    return s.strip()


def yes(v):
    return 'Ja' if v else 'Nee'


def thumb(path, box=(150, 110)):
    """Webp from the site -> small JPEG on white (2x for sharp display), with the display size."""
    im = PILImage.open(path)
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA')
        bg = PILImage.new('RGB', im.size, 'white')
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert('RGB')
    scale = min(box[0] / im.width, box[1] / im.height)
    disp = (max(1, round(im.width * scale)), max(1, round(im.height * scale)))
    im = im.resize((disp[0] * 2, disp[1] * 2), PILImage.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=86, optimize=True)
    buf.seek(0)
    x = XLImage(buf)
    x.width, x.height = disp
    return x


def place(ws, img, col, row, cell_w=159, cell_h=120):
    """Put the image centred in its cell (col and row 1-based)."""
    w, h = img.width, img.height
    at = AnchorMarker(col=col - 1, colOff=pixels_to_EMU((cell_w - w) // 2), row=row - 1, rowOff=pixels_to_EMU((cell_h - h) // 2))
    img.anchor = OneCellAnchor(_from=at, ext=XDRPositiveSize2D(pixels_to_EMU(w), pixels_to_EMU(h)))
    ws.add_image(img)


def img_file(rel):
    return os.path.join(SITE, rel.lstrip('/'))


def spec(m):
    """Label -> value of the spec table on the product page (Dutch)."""
    return {k: v for _, rows in B.spec_groups(m, 'nl', price=False) for k, v in rows}


def type_names(m):
    names = T['type_name']
    return ', '.join(names.get(t, t) for t in m['types'])


models = sorted(B.MODELS, key=size_key)
wb = Workbook()

# ------------------------------------------------------------------ sheet 1: Pallets
ws = wb.active
ws.title = 'Pallets'
cols = [
    # (header, width, kind)
    ('Foto bovenkant', 22, 'img'), ('Foto onderkant', 22, 'img'),
    ('Artikelnummer', 20, 'b'), ('Productnaam', 38, 'w'), ('Formaat', 14, ''), ('Draagklasse', 11, ''),
    ('Lengte (mm)', 10, 'i'), ('Breedte (mm)', 10, 'i'), ('Hoogte (mm)', 10, 'i'), ('Gewicht (kg)', 10, 'd'),
    ('Statische belasting (kg)', 12, 'n'), ('Dynamische belasting (kg)', 12, 'n'), ('Stellingbelasting (kg)', 12, 'n'),
    ('Geschikt voor stellingen', 11, ''), ('Bovendek', 13, ''), ('Onderzijde', 14, ''), ('Nestbaar', 9, ''),
    ('Antislip', 9, ''), ('Hygiënisch', 10, ''), ('Typen', 26, 'w'), ('Materiaal', 22, 'w'), ('Kleur', 26, 'w'),
    ('ISPM 15', 22, 'w'), ('Productielocatie(s)', 22, 'w'), ('Pallets per stapel', 10, 'n'), ('Stapelmaat (mm)', 18, ''),
    ('PPWR-conformiteitsverklaring', 14, ''), ('Basisartikel (familie)', 18, ''),
    ('Andere uitvoeringen', 24, 'w'), ('Korte omschrijving', 60, 'w'),
    ('Productpagina', 40, 'link'), ('Datasheet (pdf)', 40, 'link'), ("Foto's (groot)", 60, 'w'),
]
for c, (h, w, _) in enumerate(cols, 1):
    cell = ws.cell(row=1, column=c, value=h)
    cell.font, cell.fill = F_HEAD, FILL_HEAD
    cell.alignment = Alignment(vertical='center', wrap_text=True)
    ws.column_dimensions[get_column_letter(c)].width = w
ws.row_dimensions[1].height = 42
ws.freeze_panes = 'D2'

missing = []
for r, m in enumerate(models, 2):
    S = spec(m)
    X = m['txt']['nl']
    ph = B.PHOTOS.get(m['photo_id'], {})
    fam = B.FAMILY_ITEMS[m['family']]
    anchor = next(x for x in fam if x['is_anchor'])
    others = [x['sku'] for x in fam if x['id'] != m['id']]
    gallery_lg = [DOMAIN + g['lg'] for g in m['gallery']] or [DOMAIN + m['img_lg']]
    bottom_i = ph.get('bottom')
    stack_place = ' x '.join(str(x) for x in m['stack_place']) if m['stack_place'] else ''
    vals = [
        None, None,
        m['sku'], m['name']['nl'], m['size_label'], m['class'].capitalize(),
        m['L'], m['W'], m['height'][1], m['weight'][1],
        m['static'][1], m['dynamic'][1], m['racking'][1] if m['racking'] else None,
        yes(m['racking']), X['deck_label'], X['support'], yes('nestable' in m['types']),
        yes(m['antislip']), yes(B.is_hyg(m)), type_names(m), S.get(T['material'], ''), X['colour'],
        S.get(T['ispm'], ''), X['locs_txt'], m['stack'] or m.get('pack') or None, stack_place,
        yes(m['ppwr']), anchor['sku'],
        ', '.join(others), plain(X['intro']),
        DOMAIN + m['url']['nl'], DOMAIN + X['datasheet'], '\n'.join(gallery_lg),
    ]
    for c, v in enumerate(vals, 1):
        cell = ws.cell(row=r, column=c, value=v)
        kind = cols[c - 1][2]
        cell.font = F_BOLD if kind == 'b' else F_LINK if kind == 'link' else F_BODY
        cell.alignment = TOP_WRAP if kind in ('w', 'link') else TOP
        if kind == 'n':
            cell.number_format = '#,##0'
        elif kind == 'i':
            cell.number_format = '0'
        elif kind == 'd':
            cell.number_format = '0.0'
        if kind == 'link' and v:
            cell.hyperlink = v
        if r % 2 == 1 and c > 2:
            cell.fill = FILL_ZEBRA
        cell.border = BORDER
    if m['racking'] is None:
        ws.cell(row=r, column=13, value='–').alignment = Alignment(vertical='top', horizontal='right')
    ws.row_dimensions[r].height = 90
    # photos (top = main photo, bottom = the photo marked 'bottom' in input/photos.json)
    top = img_file(m['img_sm'])
    if os.path.exists(top):
        place(ws, thumb(top), 1, r)
    else:
        missing.append((m['sku'], 'top'))
    if bottom_i and bottom_i <= len(m['gallery']):
        bot = img_file(m['gallery'][bottom_i - 1]['sm'])
        if os.path.exists(bot):
            place(ws, thumb(bot), 2, r)
        else:
            missing.append((m['sku'], 'bottom'))
    else:
        gc = ws.cell(row=r, column=2, value='geen foto')
        gc.font, gc.alignment = Font(name=FONT, size=9, italic=True, color='8A8AA0'), CENTER
ws.auto_filter.ref = f"C1:{get_column_letter(len(cols))}{len(models) + 1}"

# ------------------------------------------------------------------ sheet 2: names and URLs per language
w2 = wb.create_sheet("Namen en URL's")
hdr = ['Artikelnummer'] + [f'Naam ({LANG_NAME[l]})' for l in LANGS] + [f'URL ({LANG_NAME[l]})' for l in LANGS] + \
      [f'Datasheet ({LANG_NAME[l]})' for l in LANGS]
for c, h in enumerate(hdr, 1):
    cell = w2.cell(row=1, column=c, value=h)
    cell.font, cell.fill = F_HEAD, FILL_HEAD
    cell.alignment = Alignment(vertical='center', wrap_text=True)
    w2.column_dimensions[get_column_letter(c)].width = 20 if c == 1 else 42 if c <= 7 else 48
w2.row_dimensions[1].height = 30
w2.freeze_panes = 'B2'
for r, m in enumerate(models, 2):
    row = [m['sku']] + [m['name'][l] for l in LANGS] + [DOMAIN + m['url'][l] for l in LANGS] + \
          [DOMAIN + m['txt'][l]['datasheet'] for l in LANGS]
    for c, v in enumerate(row, 1):
        cell = w2.cell(row=r, column=c, value=v)
        cell.font = F_BOLD if c == 1 else F_LINK if c > 7 else F_BODY
        cell.alignment = TOP_WRAP
        if c > 7:
            cell.hyperlink = v
        if r % 2 == 1:
            cell.fill = FILL_ZEBRA
        cell.border = BORDER
w2.auto_filter.ref = f"A1:{get_column_letter(len(hdr))}{len(models) + 1}"

# ------------------------------------------------------------------ sheet 3: full product texts
w3 = wb.create_sheet('Omschrijvingen')
hdr = ['Artikelnummer', 'Productnaam'] + [f'Omschrijving ({LANG_NAME[l]})' for l in LANGS]
for c, h in enumerate(hdr, 1):
    cell = w3.cell(row=1, column=c, value=h)
    cell.font, cell.fill = F_HEAD, FILL_HEAD
    cell.alignment = Alignment(vertical='center', wrap_text=True)
    w3.column_dimensions[get_column_letter(c)].width = 20 if c == 1 else 34 if c == 2 else 70
w3.freeze_panes = 'C2'
for r, m in enumerate(models, 2):
    texts = [plain(m['txt'][l]['intro']) + '\n\n' + plain(m['txt'][l]['desc_html']) for l in LANGS]
    for c, v in enumerate([m['sku'], m['name']['nl']] + texts, 1):
        cell = w3.cell(row=r, column=c, value=v)
        cell.font = F_BOLD if c == 1 else F_BODY
        cell.alignment = TOP_WRAP
        cell.border = BORDER
    w3.row_dimensions[r].height = 150

# ------------------------------------------------------------------ sheet 4: notes
w4 = wb.create_sheet('Toelichting')
w4.column_dimensions['A'].width = 30
w4.column_dimensions['B'].width = 100
w4['A1'] = 'Q-Pall productexport: kunststof pallets'
w4['A1'].font = F_TITLE
notes = [
    ('Datum', date.today().strftime('%d-%m-%Y')),
    ('Aantal artikelen', f'{len(models)} pallets (één rij per artikelnummer); toebehoren zitten er niet in.'),
    ('Bron', 'Dezelfde productdata als de website (bron/data/products.json, stapels.json, input/photos.json). '
             'Opnieuw maken: python3 tools/export_xlsx.py'),
    ('Volgorde', 'Op formaat (zoals in het menu), daarna draagklasse (light, medium, heavy), hoogte en artikelnummer.'),
    ('Belastingen', 'Maximale waarden bij een gelijkmatig verdeelde last. Statisch: pallet staat op een vlakke vloer. '
                    'Dynamisch: pallet wordt met heftruck of pompwagen verplaatst. Stelling: pallet ligt alleen op de liggers. '
                    '"–" bij stellingbelasting: niet geschikt voor stellingen.'),
    ('Pallets per stapel', 'Q-Pall levert per volle stapel. Stapelmaat = afmetingen van een volle stapel (lengte x breedte x hoogte), '
                           'waar bekend.'),
    ('Foto onderkant', '"geen foto" betekent dat er voor dit artikel (nog) geen foto van de onderkant is.'),
    ('Links', f'Productpagina, datasheets en foto\'s staan op {DOMAIN}. Deze links werken vanaf de livegang van de nieuwe '
              'website; tot die tijd staat alles op staging.qpall.com met hetzelfde pad.'),
    ('Prijzen', 'Niet opgenomen: de website toont geen prijzen meer.'),
    ('Tabbladen', "Pallets: alle gegevens en foto's (Nederlands). Namen en URL's: naam, productpagina en datasheet in zes talen. "
                  'Omschrijvingen: de volledige producttekst per taal, zoals op de productpagina.'),
]
for i, (k, v) in enumerate(notes, 3):
    a, b = w4.cell(row=i, column=1, value=k), w4.cell(row=i, column=2, value=v)
    a.font, b.font = F_BOLD, F_BODY
    a.alignment, b.alignment = TOP, TOP_WRAP

for sh in wb.worksheets:
    sh.sheet_view.zoomScale = 100
wb.save(OUT_XLSX)
print('rows', len(models), 'out', OUT_XLSX, 'missing photos', missing)
