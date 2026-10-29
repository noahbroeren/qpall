"""Build templates/_sprite.svg: Google Material Symbols (Outlined, 400, 24px) + round flags + LinkedIn logo.

The icon path data lives in data/material-icons.json (extracted once from
github.com/google/material-design-icons, folder symbols/web/<name>/materialsymbolsoutlined/<name>_24px.svg).
To add an icon: add {"key": {"name": ..., "vb": "0 -960 960 960", "d": [...]}} to that file,
then run:  python3 tools/icons.py
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS = json.load(open(os.path.join(ROOT, 'data', 'material-icons.json'), encoding='utf-8'))

# Official LinkedIn "bug" (square with "in"), single colour: white in the footer (the letters are cut out)
LINKEDIN = ('<symbol id="i-linkedin" viewBox="0 0 24 24">'
            '<path fill="currentColor" fill-rule="evenodd" d="M22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z'
            'M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286z'
            'M5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452z"/>'
            '</symbol>')


def flag(code, body):
    """Round flag: 32x32, clipped to a circle, with a hairline ring so white flags stay visible."""
    cid = f'fc-{code}'
    return (f'<symbol id="f-{code}" viewBox="0 0 32 32"><clipPath id="{cid}"><circle cx="16" cy="16" r="16"/></clipPath>'
            f'<g clip-path="url(#{cid})">{body}</g><circle cx="16" cy="16" r="15.5" fill="none" stroke="#1D1C4C" stroke-opacity=".12"/></symbol>')


UNION = ('<rect width="32" height="32" fill="#012169"/>'
         '<path d="M-2 -2L34 34M34 -2L-2 34" stroke="#fff" stroke-width="6.4"/>'
         '<path d="M-2 -2L34 34M34 -2L-2 34" stroke="#C8102E" stroke-width="2.4"/>'
         '<path d="M16 0v32M0 16h32" stroke="#fff" stroke-width="9"/>'
         '<path d="M16 0v32M0 16h32" stroke="#C8102E" stroke-width="5"/>')
FLAGS = {
    'nl': '<rect width="32" height="32" fill="#21468B"/><rect width="32" height="21.33" fill="#fff"/><rect width="32" height="10.67" fill="#AE1C28"/>',
    'de': '<rect width="32" height="32" fill="#FFCE00"/><rect width="32" height="21.33" fill="#DD0000"/><rect width="32" height="10.67" fill="#000"/>',
    'fr': '<rect width="32" height="32" fill="#EF4135"/><rect width="21.33" height="32" fill="#fff"/><rect width="10.67" height="32" fill="#0055A4"/>',
    'it': '<rect width="32" height="32" fill="#CE2B37"/><rect width="21.33" height="32" fill="#fff"/><rect width="10.67" height="32" fill="#009246"/>',
    'es': '<rect width="32" height="32" fill="#AA151B"/><rect y="8" width="32" height="16" fill="#F1BF00"/>',
    'dk': '<rect width="32" height="32" fill="#C8102E"/><rect x="9.5" width="5" height="32" fill="#fff"/><rect y="13.5" width="32" height="5" fill="#fff"/>',
    'en': UNION,
    'uk': UNION,
}


def main():
    out = ['<svg xmlns="http://www.w3.org/2000/svg" style="position:absolute;width:0;height:0;overflow:hidden" aria-hidden="true">', '<defs>']
    for key, ic in ICONS.items():
        paths = ''.join(f'<path d="{d}"/>' for d in ic['d'])
        out.append(f'<symbol id="i-{key}" viewBox="{ic["vb"]}" fill="currentColor">{paths}</symbol>')
    out.append(LINKEDIN)
    for code, body in FLAGS.items():
        out.append(flag(code, body))
    out += ['</defs>', '</svg>']
    open(os.path.join(ROOT, 'templates', '_sprite.svg'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print(f'sprite: {len(ICONS)} Material Symbols + linkedin + {len(FLAGS)} round flags')


if __name__ == '__main__':
    main()
