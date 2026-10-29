"""Onderlat voor de 760 x 1140-pallets (CP5, klikbare onderlat, 1163 mm) -> input/cad/runner-views/runner_cp5.png.

De bron is een pdf met alleen een ingesloten afbeelding (geen vectortekening). Het script haalt die
afbeelding eruit, knipt zij- en bovenaanzicht met maten uit, haalt merknamen, logo's, het
bestelnummer en de hulplijnen weg, vergroot 3x en maakt de lijnen navy (zelfde stijl als de andere
onderlatten). Daarna: python3 tools/cad_runner_compose.py.
Gebruik: python3 tools/cad_runner_cp5.py <onderlat.pdf>
Vereist: pdfimages (poppler), numpy, Pillow.
"""
import os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cad_runner_crop import rgba

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'input/cad/runner-views/runner_cp5.png')
CROP = (40, 0, 879, 215)          # pixels of the embedded image (972 x 322)
# areas to blank, in pixels of the embedded image: merknaam (2x), logo (2x), tekstjes, bestelnummer, hulplijnen
BLANK = [(264, 17, 362, 23), (591, 17, 618, 23), (455, 30, 490, 40), (470, 62, 492, 90),
         (472, 152, 492, 164), (552, 92, 658, 107), (262, 136, 366, 150), (589, 135, 618, 150),
         (115, 172, 375, 206), (865, 165, 879, 176)]
SCALE = 3


def main(pdf):
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(['pdfimages', '-png', '-f', '1', '-l', '1', pdf, os.path.join(d, 'i')], check=True)
        src = sorted(f for f in os.listdir(d) if f.endswith('.png'))[0]
        im = Image.open(os.path.join(d, src)).convert('L')
    if im.size != (972, 322):
        sys.exit(f'onverwachte afbeelding {im.size}: vakken in BLANK opnieuw bepalen')
    a = np.array(im).astype(np.float32)
    for x0, y0, x1, y1 in BLANK:
        a[y0:y1, x0:x1] = 255
    c = Image.fromarray(a.astype(np.uint8)).crop(CROP)
    c = c.resize((c.width * SCALE, c.height * SCALE), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
    g = np.array(c).astype(np.float32)
    g = np.where(g < 150, np.clip((g - 40) * 0.6, 0, 255), 255.0)    # crisp dark lines, white paper
    ys, xs = np.where(g < 200)
    g = g[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    rgba(g).save(OUT, optimize=True)
    print(OUT, g.shape)


if __name__ == '__main__':
    main(sys.argv[1])
