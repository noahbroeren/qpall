#!/usr/bin/env python3
"""Validate translated content and UI strings against the English source.

Usage:
  python3 tools/check_translation.py <lang> [file.md ...]   # content files (default: all EN files)
  python3 tools/check_translation.py <lang> --i18n          # i18n/<lang>.json

Checks: YAML parses, identical key structure and list lengths, fixed values unchanged,
id == file name, title <= 60, description 120-156, same number of (@ links, [[ placeholders,
** bold markers, headings and table rows; for i18n the same {placeholders} per string.
"""
import json, os, re, sys, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEEP = {'id', 'recommend', 'reading', 'noindex', 'published', 'updated', 'icon', 'y', 'num'}


def split(path):
    raw = open(path, encoding='utf-8').read()
    if not raw.startswith('---'):
        raise ValueError('no frontmatter')
    _, fm, body = raw.split('---', 2)
    return yaml.safe_load(fm), body, raw


def struct(a, b, path, errs, keep=True):
    if isinstance(a, dict):
        if not isinstance(b, dict):
            errs.append(f'{path}: expected mapping'); return
        if set(a) != set(b):
            errs.append(f'{path}: keys differ, missing {sorted(set(a) - set(b))}, extra {sorted(set(b) - set(a))}')
        for k in a:
            if k in b:
                if keep and k in KEEP and k != 'num' and a[k] != b[k]:
                    errs.append(f'{path}.{k}: must stay {a[k]!r}')
                struct(a[k], b[k], f'{path}.{k}', errs, keep)
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            errs.append(f'{path}: list length {len(a)} expected, got {len(b) if isinstance(b, list) else type(b).__name__}'); return
        for i, (x, y) in enumerate(zip(a, b)):
            struct(x, y, f'{path}[{i}]', errs, keep)
    else:
        if isinstance(a, str) and not isinstance(b, str):
            errs.append(f'{path}: expected a string, got {type(b).__name__} (quote it)')


def counts(s):
    return {
        '(@ links': len(re.findall(r'\(@', s)),
        '[[ placeholders': len(re.findall(r'\[\[', s)),
        '** markers': s.count('**'),
        'headings': len(re.findall(r'(?m)^#{2,4} ', s)),
        'table rows': len(re.findall(r'(?m)^\|', s)),
    }


def check_md(lang, name):
    errs = []
    src = os.path.join(ROOT, 'content', 'en', name)
    dst = os.path.join(ROOT, 'content', lang, name)
    if not os.path.exists(dst):
        return ['missing file']
    try:
        a, abody, araw = split(src)
        b, bbody, braw = split(dst)
    except Exception as e:  # noqa
        return [f'YAML/frontmatter error: {e}']
    struct(a, b, 'fm', errs)
    if b.get('id') != name[:-3]:
        errs.append('id must equal file name')
    t, d = b.get('title', ''), b.get('description', '')
    if len(t) > 60:
        errs.append(f'title {len(t)} chars (max 60): {t}')
    if '|' in t:
        errs.append('title contains |')
    if not 120 <= len(d) <= 156:
        errs.append(f'description {len(d)} chars (120-156): {d}')
    ca, cb = counts(araw), counts(braw)
    for k in ca:
        if ca[k] != cb[k]:
            errs.append(f'{k}: EN {ca[k]} vs {lang} {cb[k]}')
    la = re.findall(r'\(@([^)]+)\)', araw)
    lb = re.findall(r'\(@([^)]+)\)', braw)
    if sorted(la) != sorted(lb):
        errs.append(f'link targets differ: {sorted(set(la) ^ set(lb))}')
    pa = re.findall(r'\[\[[^\]]+\]\]', araw)
    pb = re.findall(r'\[\[[^\]]+\]\]', braw)
    if sorted(pa) != sorted(pb):
        errs.append(f'placeholders differ: {sorted(set(pa) ^ set(pb))}')
    if bool(abody.strip()) != bool(bbody.strip()):
        errs.append('body presence differs')
    return errs


def walk(x, p=''):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from walk(v, f'{p}.{k}')
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from walk(v, f'{p}[{i}]')
    else:
        yield p, x


def check_i18n(lang):
    errs = []
    a = json.load(open(os.path.join(ROOT, 'i18n', 'en.json'), encoding='utf-8'))
    try:
        b = json.load(open(os.path.join(ROOT, 'i18n', lang + '.json'), encoding='utf-8'))
    except Exception as e:  # noqa
        return [f'JSON error: {e}']
    struct(a, b, '', errs, keep=False)
    bb = dict(walk(b))
    same = 0
    for p, v in walk(a):
        if p not in bb or not isinstance(v, str):
            continue
        w = bb[p]
        if sorted(re.findall(r'\{\w+\}', v)) != sorted(re.findall(r'\{\w+\}', str(w))):
            errs.append(f'{p}: placeholders differ ({v!r} -> {w!r})')
        if v.count('**') != str(w).count('**'):
            errs.append(f'{p}: ** markers differ')
        if v == w and re.search(r'[a-z]{4,}', v):
            same += 1
    return errs, same


if __name__ == '__main__':
    lang = sys.argv[1]
    if '--i18n' in sys.argv:
        errs, same = check_i18n(lang)
        for e in errs:
            print('i18n:', e)
        print(f'i18n {lang}: {len(errs)} problem(s); {same} values identical to English (check these are names/brands)')
        sys.exit(1 if errs else 0)
    files = [f for f in sys.argv[2:] if f.endswith('.md')] or sorted(os.listdir(os.path.join(ROOT, 'content', 'en')))
    bad = 0
    for f in files:
        f = os.path.basename(f)
        errs = check_md(lang, f)
        if errs:
            bad += 1
            for e in errs:
                print(f'{f}: {e}')
    print(f'{lang}: {len(files) - bad}/{len(files)} files OK')
    sys.exit(1 if bad else 0)
