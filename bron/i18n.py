"""UI strings for all languages, loaded from i18n/<lang>.json (fallback: English)."""
import json, os
from site_config import LANGS

_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'i18n')
MISSING = []


def _load(lang):
    p = os.path.join(_DIR, lang + '.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}


_EN = _load('en')
T = {}
for _l in LANGS:
    d = _load(_l)
    for k, v in _EN.items():
        if k not in d:
            MISSING.append((_l, k))
            d[k] = v
        elif isinstance(v, dict) and isinstance(d[k], dict):
            for k2, v2 in v.items():
                if k2 not in d[k]:
                    MISSING.append((_l, k + '.' + k2))
                    d[k][k2] = v2
    T[_l] = d

SIZE_USE = {l: T[l]['size_use'] for l in LANGS}
