#!/usr/bin/env python3
"""Maakt de maten leesbaar in SolidWorks-pdf's waarin Arial/Century Gothic niet is ingesloten.

Sommige tekeningen (o.a. matrijs QP22, QP24, QP25, QP26 en QP30) gebruiken Arial als 'Identity-H'-lettertype
zonder het lettertype mee te leveren: elke viewer toont dan blokjes of verkeerde tekens in plaats van de maten.
Die pdf's verwijzen naar de tekens met het glyph-nummer van Arial. Dit script bouwt Liberation Sans (vrij
lettertype, zelfde maten als Arial) om naar de tekenvolgorde van Arial en sluit dat in de pdf in. De pdf wordt
in place bijgewerkt; het origineel blijft bewaard als <pdf>.orig.

Gebruik:  python3 tools/cad_fontfix.py input/cad/pdf/<Drive-id>.pdf [...]
Daarna:   python3 tools/cad_views.py input/cad/pdf <Drive-id>
Vereist:  fontTools, pikepdf en het lettertype Liberation Sans (fonts-liberation).
"""
import os, shutil, sys, io
import pikepdf
from fontTools.ttLib import TTFont
from fontTools.ttLib.standardGlyphOrder import standardGlyphOrder

LIB = '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'


def arial_order_font():
    f = TTFont(LIB, lazy=False)
    for t in f.keys():
        f[t]                                   # decompile everything while names still match the old order
    glyf, hmtx = f['glyf'], f['hmtx']
    for n in f.getGlyphOrder():
        glyf[n].expand(glyf)
    old = f.getGlyphOrder()
    have = set(old)
    new = []
    for i, n in enumerate(standardGlyphOrder):  # Arial keeps the standard Macintosh order for its first 258 glyphs
        if n not in have:
            n = f'_ph{i}'
            glyf.glyphs[n] = glyf['.notdef']
            hmtx.metrics[n] = hmtx.metrics['.notdef']
        new.append(n)
    new += [n for n in old if n not in set(new)]
    for t in ('GSUB', 'GPOS', 'GDEF', 'kern', 'DSIG', 'hdmx', 'LTSH', 'VDMX'):
        if t in f:
            del f[t]
    f.setGlyphOrder(new)
    glyf.glyphOrder = new
    f['maxp'].numGlyphs = len(new)
    f['post'].formatType, f['post'].extraNames, f['post'].mapping = 2.0, [], {}
    buf = io.BytesIO()
    f.save(buf)
    return buf.getvalue()


def main(paths):
    font = arial_order_font()
    for path in paths:
        if not os.path.exists(path + '.orig'):
            shutil.copy(path, path + '.orig')
        pdf = pikepdf.open(path + '.orig')
        ff = pikepdf.Stream(pdf, font)
        ff.Length1 = len(font)
        n = 0
        for obj in pdf.objects:
            if isinstance(obj, pikepdf.Dictionary) and obj.get('/Subtype') == '/CIDFontType2':
                fd = obj.get('/FontDescriptor')
                if fd is not None and '/FontFile2' not in fd:
                    fd.FontFile2 = ff
                    obj.CIDToGIDMap = pikepdf.Name('/Identity')
                    n += 1
        pdf.save(path)
        print(os.path.basename(path), 'lettertypen ingesloten:', n)


if __name__ == '__main__':
    main(sys.argv[1:])
