#!/usr/bin/env python3
"""Make data/countries.json: every country (ISO 3166-1) with its name in the six site languages.
Used for the 'Land van levering' field on the quote form (update 23: Q-Pall delivers to every country).
Needs Babel (pip install babel) only when you run this script; build.py just reads the json."""
import json, os, unicodedata
from babel import Locale

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ['nl', 'en', 'de', 'fr', 'it', 'es']
SKIP = {'AQ', 'BV', 'HM', 'UM', 'TF', 'GS'}          # uninhabited territories
iso = json.load(open('/usr/share/iso-codes/json/iso_3166-1.json', encoding='utf-8'))['3166-1'] \
    if os.path.exists('/usr/share/iso-codes/json/iso_3166-1.json') else None
codes = sorted(c['alpha_2'] for c in iso) if iso else sorted(k for k in Locale('en').territories if len(k) == 2 and k.isalpha())
codes = [c for c in codes if c not in SKIP]


def key(s):
    return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower()


out = {}
for lang in LANGS:
    terr = Locale(lang).territories
    names = {c: terr[c] for c in codes if c in terr}
    out[lang] = dict(sorted(names.items(), key=lambda kv: key(kv[1])))
json.dump(out, open(os.path.join(ROOT, 'data/countries.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print({l: len(v) for l, v in out.items()})
