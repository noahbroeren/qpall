#!/bin/sh
# Bouwt de complete website in ../qpall-website en controleert het resultaat.
# Vereist: Python 3.10+, pip install -r requirements.txt, Node.js (voor Pagefind) en
# Playwright met Chromium (voor datasheets en OG-afbeeldingen).
set -e
cd "$(dirname "$0")"
python3 tools/products.py > /dev/null
# Datasheets (PDF per model per taal) en OG-afbeeldingen: alleen opnieuw maken als
# productdata of teksten zijn gewijzigd. Zet QP_SKIP_MEDIA=1 om ze over te slaan.
if [ -z "$QP_SKIP_MEDIA" ]; then
  python3 tools/datasheets.py
  python3 tools/og.py
fi
python3 build.py
OUT="${QP_OUT:-../qpall-website}"
npx -y pagefind@1.3.0 --site "$OUT" --output-subdir pagefind
python3 tools/check.py
