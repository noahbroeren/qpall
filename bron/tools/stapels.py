#!/usr/bin/env python3
"""Pallets per stack (= per pallet place) for every article number -> data/stapels.json.

Pallets are sold per full stack. The size of a stack differs per pallet (a nestable light pallet: 45, a medium: 17,
a 600 x 400: 200 ...). Source:
  input/stapels/palletmaten voor calculator.docx (Noah, October 2026)
    table 1: article, size, pallets per pallet place on a tautliner / on a combi trailer, size of the stack (pallet place)
    "Pallets met dezelfde waarde": article numbers with the same stack as the first one
  static/calc/engine.js (the load calculator): the same numbers, plus a few extra articles (e.g. QP1140MB3R-PAS)
The stack is the TAUTLINER number (the standard 13.6 m truck); the combi number is kept for reference.

Matching per article number (build.MODELS):
  1. the article itself (a production prefix like "2." or "3." does not count: 3.QP1208LB9FR = QP1208LB9FR)
  2. the "same value" list of the docx
  3. a similar article: same size, load class, base (feet / runners), deck and height within 3 mm.
     These are marked "similar" (output of this script lists them) and should be confirmed by logistics.
  4. otherwise no number: the site shows "aantal per stapel op aanvraag" and the quote form counts per piece.
  Light pallets with runners have click-on runners: delivered nested, runners loose alongside (Q-Pall, 9 Nov 2026).
  Their stack is that of the 9-feet pallet of the same size (and deck).
Run after a new docx or new articles:  python3 tools/stapels.py   (then build again; datasheets: tools/datasheets.py)
Needs: pip install python-docx
"""
import json, os, re, sys
import docx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
SRC = os.path.join(ROOT, 'input', 'stapels', 'palletmaten voor calculator.docx')
ALIAS = {'QP6080M6FR': 'QP6080MB6FR', 'RECYCPAL1210RR': 'RECYPAL1210RR'}


def norm(s):
    s = re.sub(r'\s+', '', s.upper())
    return ALIAS.get(s, s)


def base(s):
    return re.sub(r'^[0-9N]+\.', '', norm(s))


def dims(s):
    m = re.fullmatch(r'(\d+)x(\d+)x(\d+)', s.replace(' ', ''))
    return [int(x) for x in m.groups()] if m else None


def load():
    d = docx.Document(SRC)
    table = {}
    for r in d.tables[0].rows[1:]:
        c = [x.text.strip() for x in r.cells]
        if not c[0] or not c[2].isdigit():
            continue
        table[base(c[0])] = {'stack': int(c[2]), 'combi': int(c[3]), 'place': dims(c[4]), 'place_combi': dims(c[5]), 'src': c[0]}
    # extra articles in the load calculator (same numbers, a few more articles)
    eng = open(os.path.join(ROOT, 'static', 'calc', 'engine.js'), encoding='utf-8').read()
    for m in re.finditer(r'id: "([^"]+)"[^}]*?limitTautliner: (\d+), limitCombi: (\d+)', eng):
        k = base(m.group(1))
        if k not in table and not k.startswith('QP-RUN') and 'RUN' not in k and 'FOLIE' not in k:
            table[k] = {'stack': int(m.group(2)), 'combi': int(m.group(3)), 'place': None, 'place_combi': None, 'src': m.group(1) + ' (calculator)'}
    same = {}
    for p in d.paragraphs:
        if '=' in p.text:
            a, b = p.text.split('=', 1)
            for s in b.split(','):
                if s.strip():
                    same[norm(s)] = norm(a)
                    same.setdefault(base(s), base(a))
    return table, same


def main():
    import build as B
    table, same = load()
    out, found, similar, missing = {}, {}, [], []

    def direct(sku):
        if base(sku) in table:
            return table[base(sku)], 'table'
        for k in (norm(sku), base(sku)):
            if k in same and base(same[k]) in table:
                return table[base(same[k])], 'same as ' + same[k]
        return None, None

    for m in B.MODELS:
        v, how = direct(m['sku'])
        if v:
            found[m['id']] = dict(v, how=how)
    by_sku = {base(m['sku']): m for m in B.MODELS}
    for m in B.MODELS:
        if m['id'] in found:
            out[m['sku']] = found[m['id']]
            continue
        # similar article; first with the same deck, then (closed deck = same stack as open) without
        o = None
        for same_deck in (True, False):
            cands = [o for o in B.MODELS if o['id'] in found and o['size'] == m['size'] and o['class'] == m['class']
                     and o['support']['type'] == m['support']['type'] and (o['deck'] == m['deck'] or not same_deck)
                     and abs(o['H'] - m['H']) <= 3]
            if cands:
                o = min(cands, key=lambda o: (abs(o['H'] - m['H']), o['sku']))
                break
        if o:
            out[m['sku']] = dict(found[o['id']], how='similar to ' + o['sku'])
            similar.append(f"{m['sku']} -> {o['sku']} ({found[o['id']]['stack']})")
        else:
            missing.append(m['sku'])
    # "same value" entries whose first article only got a value from a similar article
    for m in B.MODELS:
        if m['sku'] in missing:
            # the closed-deck version (-CD) of a pallet has the same stack as the open version
            keys = [same.get(norm(m['sku']), ''), same.get(base(m['sku']), ''), re.sub(r'-CD$', '', base(m['sku']))]
            for k in keys:
                t = by_sku.get(base(k)) if k else None
                if t and t['sku'] in out:
                    out[m['sku']] = dict(out[t['sku']], how='same as ' + t['sku'])
                    missing.remove(m['sku'])
                    similar.append(f"{m['sku']} -> {t['sku']} (same value / open version) ({out[t['sku']]['stack']})")
                    break
    # light pallets with runners have click-on runners (Q-Pall, Daan Voets, 9 Nov 2026): they are delivered nested, with the
    # runners supplied loose alongside, so a stack is the stack of the nestable 9-feet pallet of the same size and deck
    for m in B.MODELS:
        if B.is_click_runner(m):
            cands = [o for o in B.MODELS if o['size'] == m['size'] and o['class'] == 'light' and o['support']['type'] == 'feet'
                     and o['sku'] in out]
            if cands:
                o = min(cands, key=lambda o: (o['deck'] != m['deck'], o['sku']))
                out[m['sku']] = dict(out[o['sku']], how='click-on runners, nested like ' + o['sku'])
                similar.append(f"{m['sku']} -> {o['sku']} (click-on runners: nested) ({out[o['sku']]['stack']})")
    json.dump(out, open(os.path.join(ROOT, 'data', 'stapels.json'), 'w', encoding='utf-8'), indent=1, sort_keys=True, ensure_ascii=False)
    print(f'{len(out)} of {len(B.MODELS)} articles with a stack size -> data/stapels.json')
    print('similar article used (please confirm):')
    for s in similar:
        print('  ', s)
    print('no stack size (site: on request):', ', '.join(missing))


if __name__ == '__main__':
    main()
