#!/usr/bin/env python3
"""PDF of the general terms and conditions (data/terms-en.md) -> root/files/q-pall-bv-terms-and-conditions.pdf

Same path as on the old qpall.com, so existing links keep working. Rendered with Playwright/Chromium
(A4, Poppins). Replace the file with the original PDF if you prefer; the website text comes from
data/terms-en.md either way.   Run:  python3 tools/terms_pdf.py
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from playwright.sync_api import sync_playwright   # noqa: E402
import build                                      # noqa: E402

DEST = os.path.join(ROOT, 'root/files/q-pall-bv-terms-and-conditions.pdf')
FONTS = os.path.join(ROOT, 'static/fonts')


def main():
    logo = open(os.path.join(ROOT, 'static/img/brand/logo-qpall.svg'), encoding='utf-8').read()
    css = f'''
@font-face{{font-family:P;font-weight:400;src:url(file://{FONTS}/poppins-400.woff2)}}
@font-face{{font-family:P;font-weight:600;src:url(file://{FONTS}/poppins-600.woff2)}}
@font-face{{font-family:P;font-weight:700;src:url(file://{FONTS}/poppins-700.woff2)}}
@page{{size:A4;margin:18mm 18mm 18mm 18mm}}
body{{margin:0;font-family:P,sans-serif;font-size:8.6pt;line-height:1.5;color:#2c2b45}}
.top{{display:flex;align-items:center;justify-content:space-between;padding-bottom:8mm;margin-bottom:6mm;border-bottom:1.5pt solid #F37321}}
.top svg{{height:15mm;width:auto}}
.top small{{font-size:7.5pt;color:#74738A;text-align:right;line-height:1.5}}
h1{{margin:0 0 2mm;font-size:17pt;font-weight:700;color:#1D1C4C;letter-spacing:-.01em}}
.terms-head{{margin:0 0 6mm;font-size:7.6pt;font-weight:600;letter-spacing:.04em;color:#74738A}}
.cols{{columns:2;column-gap:9mm}}
h2{{break-after:avoid;margin:4.5mm 0 1.5mm;font-size:9.6pt;font-weight:700;color:#1D1C4C}}
h2 span{{color:#F37321}}
p,li{{margin:0 0 1.6mm;break-inside:avoid-column}}
p.tc b,li b{{color:#1D1C4C}}
ul,ol{{margin:0 0 1.6mm;padding-left:4mm}}
ol{{list-style:none;padding-left:0}}
.terms-head{{display:none}}
'''
    body = build.terms_html().replace('<div class="terms" lang="en">', '').rsplit('</div>', 1)[0]
    head_txt = build.TERMS_SRC[0]
    c = build.COMPANY
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><style>{css}</style></head><body>
<div class="top">{logo}<small>{c['legal']} · {c['street']} · {c['zip']} {c['city']} · NL<br>{c['phone']} · {c['email']} · www.qpall.com</small></div>
<h1>General terms and conditions</h1>
<p style="margin:0 0 6mm;font-size:7.6pt;font-weight:600;letter-spacing:.03em;color:#74738A">{head_txt}</p>
<div class="cols">{body}</div>
</body></html>'''
    tmp = os.path.join(ROOT, 'data', '_terms_print.html')
    open(tmp, 'w', encoding='utf-8').write(html)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto('file://' + tmp)
        pg.wait_for_timeout(400)
        pg.pdf(path=DEST, format='A4', print_background=True, display_header_footer=True,
               header_template='<span></span>',
               footer_template='<div style="width:100%;font-size:7pt;color:#74738A;padding:0 18mm;display:flex;justify-content:space-between">'
                               '<span>Q-Pall B.V. – General terms and conditions</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>',
               margin={'top': '16mm', 'bottom': '16mm', 'left': '18mm', 'right': '18mm'})
        b.close()
    os.remove(tmp)
    print(DEST, os.path.getsize(DEST) // 1024, 'KB')


if __name__ == '__main__':
    main()
