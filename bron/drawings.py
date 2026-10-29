"""Inline SVG technical drawings (schematic) and small illustrations."""
from productcopy import fmt_int

NAVY = '#1D1C4C'
OR = '#F37321'
LINE = '#9AA0BC'


def _dim_h(x1, x2, y, label, up=False):
    a = 6
    ty = y - 8 if up else y + 18
    return (f'<g class="dim"><line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{NAVY}" stroke-width="1.2"/>'
            f'<path d="M{x1} {y}l{a} -{a/2}v{a}z M{x2} {y}l-{a} -{a/2}v{a}z" fill="{NAVY}"/>'
            f'<line x1="{x1}" y1="{y-7}" x2="{x1}" y2="{y+7}" stroke="{NAVY}" stroke-width="1"/>'
            f'<line x1="{x2}" y1="{y-7}" x2="{x2}" y2="{y+7}" stroke="{NAVY}" stroke-width="1"/>'
            f'<text x="{(x1+x2)/2}" y="{ty}" text-anchor="middle" font-size="14" font-weight="700" fill="{NAVY}">{label}</text></g>')


def _dim_v(x, y1, y2, label, left=True):
    a = 6
    tx = x - 10 if left else x + 10
    anchor = 'end' if left else 'start'
    return (f'<g class="dim"><line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{NAVY}" stroke-width="1.2"/>'
            f'<path d="M{x} {y1}l-{a/2} {a}h{a}z M{x} {y2}l-{a/2} -{a}h{a}z" fill="{NAVY}"/>'
            f'<line x1="{x-7}" y1="{y1}" x2="{x+7}" y2="{y1}" stroke="{NAVY}" stroke-width="1"/>'
            f'<line x1="{x-7}" y1="{y2}" x2="{x+7}" y2="{y2}" stroke="{NAVY}" stroke-width="1"/>'
            f'<text x="{tx}" y="{(y1+y2)/2+5}" text-anchor="{anchor}" font-size="14" font-weight="700" fill="{NAVY}">{label}</text></g>')


def drawing(m, t, uid):
    """Return an SVG string with top view, bottom view and side view."""
    L, W, H = m['L'], m['W'], m['H']
    # orientation: draw the longer side horizontally
    Lx, Wy = (L, W) if L >= W else (W, L)
    maxw, maxh = 300, 200
    s = min(maxw / Lx, maxh / Wy)
    w, h = Lx * s, Wy * s
    ox1, oy = 70, 50
    ox2 = ox1 + maxw + 110
    parts = []
    pid = f'hatch-{uid}'
    parts.append(f'<defs><pattern id="{pid}" width="10" height="10" patternUnits="userSpaceOnUse"><rect width="10" height="10" fill="#F4F5FA"/><rect x="1.5" y="1.5" width="7" height="7" rx="1.2" fill="#fff" stroke="#C9CDDD" stroke-width=".8"/></pattern></defs>')
    # titles
    parts.append(f'<text x="{ox1}" y="{oy-18}" font-size="13" font-weight="600" fill="{LINE}" letter-spacing="1.5">{t["top_view"].upper()}</text>')
    parts.append(f'<text x="{ox2}" y="{oy-18}" font-size="13" font-weight="600" fill="{LINE}" letter-spacing="1.5">{t["bottom_view"].upper()}</text>')
    # ---- top view
    fill = f'url(#{pid})' if m['deck'] == 'open' else '#E9EBF3'
    parts.append(f'<rect x="{ox1}" y="{oy}" width="{w:.1f}" height="{h:.1f}" rx="6" fill="{fill}" stroke="{NAVY}" stroke-width="2"/>')
    if m['deck'] == 'closed':
        parts.append(f'<rect x="{ox1+8}" y="{oy+8}" width="{w-16:.1f}" height="{h-16:.1f}" rx="3" fill="none" stroke="#C9CDDD" stroke-width="1"/>')
    if m['antislip']:
        n = 5 if h > 120 else 4
        for i in range(n):
            yy = oy + h * (i + 1) / (n + 1)
            parts.append(f'<rect x="{ox1+14}" y="{yy-2.5:.1f}" width="{w-28:.1f}" height="5" rx="2.5" fill="{OR}"/>')
    parts.append(_dim_h(ox1, ox1 + w, oy + h + 22, f'{Lx} mm'))
    parts.append(_dim_v(ox1 - 22, oy, oy + h, f'{Wy}'))
    # ---- bottom view
    parts.append(f'<rect x="{ox2}" y="{oy}" width="{w:.1f}" height="{h:.1f}" rx="6" fill="#fff" stroke="{LINE}" stroke-width="1.5" stroke-dasharray="5 4"/>')
    sp = m['support']
    sup = []
    if sp['type'] == 'feet':
        n = sp['n']
        cols, rows = {9: (3, 3), 4: (2, 2), 6: (3, 2)}.get(n, (3, 3))
        fw, fh = w * 0.16, h * 0.18
        for r in range(rows):
            for c in range(cols):
                cx = ox2 + (fw / 2 + 4) + c * ((w - fw - 8) / (cols - 1)) if cols > 1 else ox2 + w / 2
                cy = oy + (fh / 2 + 4) + r * ((h - fh - 8) / (rows - 1)) if rows > 1 else oy + h / 2
                sup.append(f'<rect x="{cx-fw/2:.1f}" y="{cy-fh/2:.1f}" width="{fw:.1f}" height="{fh:.1f}" rx="4" fill="{NAVY}"/>')
    else:
        n = sp['n']
        rw = max(10, h * 0.13)
        ys = [oy + 4, oy + h / 2 - rw / 2, oy + h - rw - 4]
        for y in ys:
            sup.append(f'<rect x="{ox2+4}" y="{y:.1f}" width="{w-8:.1f}" height="{rw:.1f}" rx="3" fill="{NAVY}"/>')
        if n >= 5:
            cw = max(10, w * 0.07)
            xs = [ox2 + 4, ox2 + w - cw - 4] + ([ox2 + w / 2 - cw / 2] if n >= 6 else [])
            for x in xs:
                sup.append(f'<rect x="{x:.1f}" y="{oy+4}" width="{cw:.1f}" height="{h-8:.1f}" rx="3" fill="{NAVY}" opacity=".78"/>')
    parts += sup
    _w = t['f_runners'] if sp['type'] == 'runners' else t['f_feet']
    lab = f"{sp['n']} {_w if t.get('lang_name') == 'Deutsch' else _w.lower()}"
    parts.append(f'<text x="{ox2 + w/2}" y="{oy + h + 40}" text-anchor="middle" font-size="14" font-weight="700" fill="{NAVY}">{lab}</text>')
    # ---- side view
    sy = oy + max(h, 120) + 92
    parts.append(f'<text x="{ox1}" y="{sy-18}" font-size="13" font-weight="600" fill="{LINE}" letter-spacing="1.5">{t["side_view"].upper()}</text>')
    hs = max(H * s * 1.6, 28)
    deck_h = hs * 0.36
    parts.append(f'<rect x="{ox1}" y="{sy}" width="{w:.1f}" height="{deck_h:.1f}" rx="3" fill="{NAVY}"/>')
    if m['antislip']:
        parts.append(f'<rect x="{ox1+6}" y="{sy-3}" width="{w-12:.1f}" height="3" rx="1.5" fill="{OR}"/>')
    if sp['type'] == 'feet':
        cols = {9: 3, 4: 2, 6: 3}.get(sp['n'], 3)
        fw = w * 0.16
        for c in range(cols):
            cx = ox1 + fw / 2 + 4 + c * ((w - fw - 8) / (cols - 1))
            parts.append(f'<path d="M{cx-fw/2:.1f} {sy+deck_h:.1f}h{fw:.1f}l-{fw*0.08:.1f} {hs-deck_h:.1f}h-{fw*0.84:.1f}z" fill="{NAVY}" opacity=".85"/>')
    else:
        bw = w * 0.15
        cols = 3
        for c in range(cols):
            cx = ox1 + bw / 2 + 4 + c * ((w - bw - 8) / (cols - 1))
            parts.append(f'<rect x="{cx-bw/2:.1f}" y="{sy+deck_h:.1f}" width="{bw:.1f}" height="{hs-deck_h-8:.1f}" fill="{NAVY}" opacity=".85"/>')
        parts.append(f'<rect x="{ox1}" y="{sy+hs-8:.1f}" width="{w:.1f}" height="8" rx="2" fill="{NAVY}"/>')
    parts.append(f'<line x1="{ox1-30}" y1="{sy+hs:.1f}" x2="{ox1+w+30:.1f}" y2="{sy+hs:.1f}" stroke="{LINE}" stroke-width="1"/>')
    parts.append(_dim_v(ox1 + w + 22, sy, sy + hs, f'{H} mm', left=False))
    parts.append(_dim_h(ox1, ox1 + w, sy + hs + 22, f'{Lx} mm'))
    # side info block
    bx, by = ox2, sy - 6
    info = [(t['dims'], f"{L} x {W} x {H} mm"), (t['weight'], m['_weight_txt']), (t['class'], m['class'].capitalize())]
    for i, (k, v) in enumerate(info):
        parts.append(f'<text x="{bx}" y="{by + i*34}" font-size="12" fill="{LINE}" font-weight="600" letter-spacing="1">{k.upper()}</text>')
        parts.append(f'<text x="{bx}" y="{by + i*34 + 18}" font-size="16" fill="{NAVY}" font-weight="700">{v}</text>')
    total_h = sy + hs + 60
    vb_w = ox2 + maxw + 40
    title = t['drawing_alt'].format(name=m['name']['_cur'])
    return (f'<svg viewBox="0 0 {vb_w:.0f} {total_h:.0f}" role="img" aria-label="{title}" font-family="Poppins, Arial, sans-serif" xmlns="http://www.w3.org/2000/svg">'
            f'<title>{title}</title>' + ''.join(parts) + '</svg>')


LOAD_ICONS = {
    'static': f'<svg viewBox="0 0 200 90" aria-hidden="true"><rect x="40" y="10" width="40" height="30" rx="3" fill="{NAVY}"/><rect x="82" y="10" width="40" height="30" rx="3" fill="{NAVY}" opacity=".8"/><rect x="124" y="10" width="36" height="30" rx="3" fill="{NAVY}" opacity=".65"/><rect x="34" y="42" width="132" height="10" rx="2" fill="{OR}"/><rect x="40" y="52" width="20" height="14" fill="{OR}" opacity=".7"/><rect x="90" y="52" width="20" height="14" fill="{OR}" opacity=".7"/><rect x="140" y="52" width="20" height="14" fill="{OR}" opacity=".7"/><line x1="10" y1="67" x2="190" y2="67" stroke="#9AA0BC" stroke-width="2"/><path d="M10 72h180" stroke="#C9CDDD" stroke-width="6" stroke-dasharray="2 6"/></svg>',
    'dynamic': f'<svg viewBox="0 0 200 90" aria-hidden="true"><rect x="70" y="14" width="70" height="30" rx="3" fill="{NAVY}"/><rect x="64" y="46" width="82" height="8" rx="2" fill="{OR}"/><rect x="66" y="56" width="90" height="4" fill="#9AA0BC"/><path d="M156 20v40" stroke="#9AA0BC" stroke-width="4"/><circle cx="170" cy="72" r="8" fill="#9AA0BC"/><path d="M20 30h30M14 40h36M24 50h26" stroke="{OR}" stroke-width="3" stroke-linecap="round" opacity=".6"/><line x1="10" y1="82" x2="190" y2="82" stroke="#9AA0BC" stroke-width="2"/></svg>',
    'racking': f'<svg viewBox="0 0 200 90" aria-hidden="true"><rect x="18" y="6" width="8" height="80" fill="#9AA0BC"/><rect x="174" y="6" width="8" height="80" fill="#9AA0BC"/><rect x="26" y="50" width="148" height="7" fill="{NAVY}" opacity=".35"/><rect x="60" y="14" width="80" height="26" rx="3" fill="{NAVY}"/><rect x="40" y="40" width="120" height="8" rx="2" fill="{OR}"/><rect x="44" y="48" width="14" height="6" fill="{OR}" opacity=".7"/><rect x="142" y="48" width="14" height="6" fill="{OR}" opacity=".7"/><path d="M100 62v14" stroke="{OR}" stroke-width="2" stroke-dasharray="3 3"/></svg>',
}

ACC_ILLU = {
    'collar': f'<svg class="ph" viewBox="0 0 240 140" aria-hidden="true"><path d="M30 60l90-30 90 30v40l-90 30-90-30z" fill="#E9EBF3" stroke="{NAVY}" stroke-width="3"/><path d="M30 60l90 30 90-30M120 90v40" fill="none" stroke="{NAVY}" stroke-width="3"/><path d="M30 80l90 30 90-30" fill="none" stroke="{OR}" stroke-width="2" stroke-dasharray="6 5"/><rect x="58" y="74" width="10" height="16" rx="2" fill="{OR}"/><rect x="172" y="74" width="10" height="16" rx="2" fill="{OR}"/></svg>',
    'lid': f'<svg class="ph" viewBox="0 0 240 140" aria-hidden="true"><path d="M20 70l100-35 100 35-100 35z" fill="#E9EBF3" stroke="{NAVY}" stroke-width="3"/><path d="M20 70v8l100 35 100-35v-8" fill="none" stroke="{NAVY}" stroke-width="3"/><path d="M60 70l60 21 60-21" stroke="{OR}" stroke-width="2" fill="none"/></svg>',
    'freezer': f'<svg class="ph" viewBox="0 0 240 140" aria-hidden="true"><path d="M20 70l100-35 100 35-100 35z" fill="#fff" stroke="{NAVY}" stroke-width="3"/><g stroke="{NAVY}" stroke-width="1.6" opacity=".6"><path d="M45 61l100 35M70 52l100 35M95 44l100 35M45 79l100-35M70 88l100-35M95 96l100-35"/></g><path d="M20 70v10l100 35 100-35v-10" fill="none" stroke="{NAVY}" stroke-width="3"/><path d="M190 30c-6 6-6 12 0 18M206 26c-6 6-6 12 0 18" stroke="{OR}" stroke-width="3" fill="none" stroke-linecap="round"/></svg>',
    'driptray': f'<svg class="ph" viewBox="0 0 240 140" aria-hidden="true"><path d="M30 50l90-28 90 28v38l-90 28-90-28z" fill="#E9EBF3" stroke="{NAVY}" stroke-width="3"/><path d="M30 50l90 28 90-28M120 78v38" fill="none" stroke="{NAVY}" stroke-width="3"/><path d="M60 52l60 18 60-18-60-16z" fill="{OR}" opacity=".35"/><path d="M120 14c-6 8-8 12-8 15a8 8 0 0 0 16 0c0-3-2-7-8-15z" fill="{OR}"/></svg>',
    'grating': f'<svg class="ph" viewBox="0 0 240 140" aria-hidden="true"><path d="M20 66l100-34 100 34-100 34z" fill="#fff" stroke="{NAVY}" stroke-width="3"/><g stroke="#8A8DA6" stroke-width="1.6"><path d="M40 59l100 34M60 52l100 34M80 45l100 34M100 39l100 34M40 73l100-34M60 80l100-34M80 87l100-34"/></g><path d="M20 66v14l100 34 100-34V66" fill="none" stroke="{NAVY}" stroke-width="3"/></svg>',
    'grid': f'<svg class="ph" viewBox="0 0 240 140" aria-hidden="true"><path d="M20 66l100-34 100 34-100 34z" fill="#E9EBF3" stroke="{NAVY}" stroke-width="3"/><g fill="{NAVY}" opacity=".5"><rect x="60" y="58" width="14" height="8"/><rect x="113" y="40" width="14" height="8"/><rect x="166" y="58" width="14" height="8"/><rect x="113" y="76" width="14" height="8"/></g><path d="M20 66v10l100 34 100-34V66" fill="none" stroke="{NAVY}" stroke-width="3"/></svg>',
    'runner': f'<svg class="ph" viewBox="0 0 240 140" aria-hidden="true"><g fill="{NAVY}"><rect x="20" y="40" width="200" height="14" rx="4"/><rect x="20" y="64" width="200" height="14" rx="4" opacity=".8"/><rect x="20" y="88" width="200" height="14" rx="4" opacity=".6"/></g></svg>',
}
