#!/usr/bin/env python3
"""Check the final redirect file of iClicks (9 Nov 2026) against a built site.

Every old URL (data/oude-site/iclicks-redirects-2026-11-09.tsv) must end, through the rules in <out>/_redirects, on
exactly the new page iClicks lists, and that page must exist. Simulates Netlify like tools/redirects_check.py.
Usage: python3 tools/redirects_iclicks_check.py [out-dir]
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('QP_OUT') or os.path.join(os.path.dirname(ROOT), 'qpall-website')


def exists(path):
    f = os.path.join(OUT, path.split('?')[0].lstrip('/'))
    return os.path.isfile(f) or os.path.isfile(os.path.join(f, 'index.html'))


rules = []
for line in open(os.path.join(OUT, '_redirects'), encoding='utf-8'):
    parts = line.split()
    if parts and not parts[0].startswith('#') and not parts[0].startswith('http'):
        rules.append((parts[0], parts[1], parts[2] if len(parts) > 2 else '301'))


def match(path):
    p = path.rstrip('/') or '/'
    for src, dst, st in rules:
        force = st.endswith('!')
        if src.endswith('/*'):
            base = src[:-2]
            if not force and dst.startswith(base):
                continue      # ignored by Netlify (destination under its own pattern)
            if p == base or p.startswith(base + '/'):
                if not force and exists(path):
                    continue
                return dst.replace(':splat', p[len(base) + 1:]), st
        elif (src.rstrip('/') or '/') == p:
            if not force and exists(path):
                continue
            return dst, st
    return None


def resolve(old):
    cur = old.split('?')[0]
    for n in range(6):
        if exists(cur):
            cur = cur.split('?')[0]           # a query string (?locatie=...) is not part of the page
            return cur.rstrip('/') + ('/' if not os.path.splitext(cur)[1] else ''), n + (0 if cur.endswith('/') or os.path.splitext(cur)[1] else 1)
        m = match(cur)
        if not m or not m[1].startswith('30'):
            return None, n
        cur = m[0]
    return None, 6


# update 45: an expected page that is no longer on the site (draft or removed article) is replaced by the page that
# data/redirects-removed.txt sends it to
REMAP = {}
for line in open(os.path.join(ROOT, 'data/redirects-removed.txt'), encoding='utf-8'):
    p = line.split()
    if len(p) >= 2 and not p[0].startswith('#'):
        REMAP[p[0]] = p[1]
ok, bad, hops = 0, [], {}
for line in open(os.path.join(ROOT, 'data/oude-site/iclicks-redirects-2026-11-09.tsv'), encoding='utf-8'):
    if line.startswith('#') or not line.strip():
        continue
    old, new = line.rstrip('\n').split('\t')[:2]
    new = REMAP.get(new, new)
    final, n = resolve(old)
    if final and final == new and exists(new):
        ok += 1
        hops[n] = hops.get(n, 0) + 1
    else:
        bad.append((old, new, final))
print(f'iClicks redirects: {ok + len(bad)}  ok: {ok}  failing: {len(bad)}  hops: {dict(sorted(hops.items()))}')
for b in bad[:40]:
    print('  FAIL', b[0], '->', b[1], '| now:', b[2])
sys.exit(1 if bad else 0)
