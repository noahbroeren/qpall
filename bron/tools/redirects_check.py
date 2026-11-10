#!/usr/bin/env python3
"""Check that every old qpall.com URL ends on an existing page of the built site.

Simulates Netlify: rules from <out>/_redirects in order, first match wins, trailing slash ignored,
'/x/*' splats, a non-forced rule is skipped when the path exists as a file ('shadowing'),
'/path' and '/path/' serve '/path/index.html'. Follows up to 5 redirects.
Usage: python3 tools/redirects_check.py [out-dir]     (old URLs: data/oude-site/_alle-oude-urls.txt + gsc-16-maanden.txt)
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('QP_OUT') or os.path.join(os.path.dirname(ROOT), 'qpall-website')


def exists(path):
    p = path.split('?')[0].split('#')[0]
    f = os.path.join(OUT, p.lstrip('/'))
    return os.path.isfile(f) or os.path.isfile(os.path.join(f, 'index.html'))


rules = []
for line in open(os.path.join(OUT, '_redirects'), encoding='utf-8'):
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    parts = line.split()
    rules.append((parts[0], parts[1], parts[2] if len(parts) > 2 else '301'))


def match(path):
    p = path.rstrip('/') or '/'
    for src, dst, st in rules:
        force = st.endswith('!')
        if src.endswith('/*'):
            base = src[:-2]
            if not force and dst.startswith(base):
                continue      # Netlify ignores a splat rule whose destination falls under its own pattern
            if p == base or p.startswith(base + '/'):
                if not force and exists(path):
                    continue
                return dst.replace(':splat', p[len(base) + 1:]), st
        elif (src.rstrip('/') or '/') == p:
            if not force and exists(path):
                continue
            return dst, st
    return None


bad, ok, hops = [], 0, {}
LISTS = [os.path.join(ROOT, 'data/oude-site/_alle-oude-urls.txt'), os.path.join(ROOT, 'data/oude-site/gsc-16-maanden.txt')]
for old in (l for f in LISTS if os.path.exists(f) for l in open(f, encoding='utf-8')):
    old = old.strip()
    if not old or old.startswith('#'):
        continue
    cur, n = old, 0
    while n < 6:
        if exists(cur):
            break
        m = match(cur)
        if not m:
            break
        dst, st = m
        if not st.startswith('30'):
            cur = None
            break
        cur, n = dst, n + 1
    if cur and exists(cur):
        ok += 1
        hops[n] = hops.get(n, 0) + 1
    else:
        bad.append(old)
print(f'old URLs: {ok + len(bad)}  ok: {ok}  failing: {len(bad)}  hops: {dict(sorted(hops.items()))}')
for b in bad[:40]:
    print('  FAIL', b)
sys.exit(1 if bad else 0)
