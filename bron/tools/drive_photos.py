"""Losse productfoto's (bijv. uit Google Drive) toevoegen aan een model.

Zet de originele foto's in input/drive-photos/<id>/1.webp, 2.webp, ... (1 = hoofdfoto,
vrijstaand op wit of transparant; volgende = extra aanzichten/details). <id> is het id van een
artikel (de URL-naam van het artikelnummer, bijv. 2-qp1208mb3rr) of van een model (dan geldt de set
voor elk artikel van dat model zonder eigen foto's). Een bestand met "onder" of "bottom" in de naam
is de foto van de onderkant (die komt ook op de datasheet). Dit script maakt daar de
genormaliseerde fotoset van in input/photos/<id>/ (3:2, 1800 px, zelfde opmaak als de rest)
en zet het id in input/photos.json op "exact" (dus zonder het label "ter illustratie").

Draaien:  python3 tools/drive_photos.py            (alle mappen in input/drive-photos)
          python3 tools/drive_photos.py qph1208hp3rr-cdb   (één model)
Daarna gewoon opnieuw bouwen.
"""
import glob, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from photos import normalise  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'input/drive-photos')
OUT = os.path.join(ROOT, 'input/photos')
META = os.path.join(ROOT, 'input/photos.json')


def main(only):
    meta = json.load(open(META))
    models = {m['id'] for m in json.load(open(os.path.join(ROOT, 'data/products.json')))['models']}
    bm = os.path.join(ROOT, 'data/_build_models.json')      # article ids (written by build.py)
    if os.path.exists(bm):
        models |= {m['id'] for m in json.load(open(bm))['models']}
    for d in sorted(glob.glob(os.path.join(SRC, '*'))):
        mid = os.path.basename(d)
        if only and mid not in only:
            continue
        if mid not in models:
            print('onbekend model/artikel, overgeslagen:', mid)
            continue
        files = sorted(f for f in glob.glob(os.path.join(d, '*')) if f.lower().endswith(('.webp', '.png', '.jpg', '.jpeg')))
        if not files:
            continue
        od = os.path.join(OUT, mid)
        os.makedirs(od, exist_ok=True)
        for old in glob.glob(os.path.join(od, '*.webp')):
            os.remove(old)
        for i, f in enumerate(files, 1):
            normalise(f, allow_cover=i > 1).save(os.path.join(od, f'{i}.webp'), 'WEBP', quality=90, method=6)
        prev = meta.get(mid, {})
        meta[mid] = {'n': len(files), 'src': ['drive'] * len(files), 'exact': True}
        if prev.get('bottom') and prev.get('n') == len(files):
            meta[mid]['bottom'] = prev['bottom']                    # keep the bottom photo set before
        bottom = [i for i, f in enumerate(files, 1) if any(w in os.path.basename(f).lower() for w in ('onder', 'bottom'))]
        if bottom:
            meta[mid]['bottom'] = bottom[0]
        print(mid, len(files), 'foto(s)')
    json.dump(meta, open(META, 'w'), indent=1)


if __name__ == '__main__':
    main(set(sys.argv[1:]))
