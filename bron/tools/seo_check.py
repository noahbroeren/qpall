"""Controleert de getallen in de SEO-teksten (input/producten-6-talen.xlsx, via data/products.json)
tegen de productdata. Draai na elke PIM-wijziging: python3 tools/seo_check.py

Meldt:
  - eigen gewicht/maten in de tekst die niet kloppen met het artikel;
  - verwijzingen naar een andere uitvoering ("die weegt X kg en draagt ...") waarvoor geen
    artikel met precies die waarden bestaat;
  - vertalingen waarvan de getallen afwijken van de Nederlandse tekst.
Zie update 17 in LEESMIJ.txt voor hoe verouderde getallen zijn rechtgezet.
"""
import collections, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOK = re.compile(r'(?<![\w.,])(\d{1,3}(?:[., \xa0 ]\d{3})+|\d+(?:[.,]\d+)?)(?=\s*(?:kg|mm|%))')
SIB = re.compile(r'weegt (?:slechts )?([\d,]+) kg en draagt ([\d.]+) kg statisch(?:,| en) ([\d.]+) kg dynamisch'
                 r'(?: en ([\d.]+) kg in de stelling)?')


def val(raw):
    if re.fullmatch(r'\d{1,3}(?:[., \xa0 ]\d{3})+', raw):
        return float(re.sub(r'\D', '', raw))
    return float(raw.replace(',', '.'))


def plain(html):
    return re.sub(r'<[^>]+>', ' ', html or '')


def main():
    models = json.load(open(os.path.join(ROOT, 'data/products.json')))['models']
    allv = [v for m in models for v in m['variants']]
    problems = collections.defaultdict(list)
    for v in allv:
        seo = v.get('seo6') or {}
        nl = plain(seo.get('nl'))
        if not nl:
            continue
        w = re.search(r'weegt (?:slechts )?([\d,]+) kg', nl)
        if w and float(w.group(1).replace(',', '.')) != v['weight']:
            problems[v['sku']].append(f'gewicht in tekst {w.group(1)} kg, data {v["weight"]} kg')
        d = re.search(r'meet (\d+) x (\d+) x (\d+) mm', nl)
        if d and tuple(map(int, d.groups())) != (v['L'], v['W'], v['H']):
            problems[v['sku']].append(f'maten in tekst {d.group(0)}, data {v["L"]} x {v["W"]} x {v["H"]}')
        for g in SIB.finditer(nl):
            wt = float(g.group(1).replace(',', '.'))
            st, dy = (int(x.replace('.', '')) for x in g.groups()[1:3])
            rk = int(g.group(4).replace('.', '')) if g.group(4) else None
            if not any(o['weight'] == wt and o['static'] == st and o['dynamic'] == dy and (rk is None or o['racking'] == rk)
                       for o in allv):
                problems[v['sku']].append(f'verwijzing zonder artikel: {g.group(0)}')
        base = [val(t.group(1)) for t in TOK.finditer(nl)]
        for lang, txt in seo.items():
            if lang != 'nl' and txt and [val(t.group(1)) for t in TOK.finditer(plain(txt))] != base:
                problems[v['sku']].append(f'{lang}: getallen wijken af van de Nederlandse tekst')
    for sku, items in problems.items():
        print(sku)
        for x in items:
            print('  ', x)
    print(f'{len(problems)} artikel(en) met afwijkingen')


if __name__ == '__main__':
    main()
