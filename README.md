# Q-Pall website

Statische website voor Q-Pall (kunststof pallets, Veghel) in zes talen, gehost op Netlify.

| Map | Inhoud |
| --- | --- |
| `qpall-website/` | De gebouwde site. Dit is de map die Netlify publiceert (bevat `netlify.toml`, `_redirects` en de sitemap). |
| `bron/` | De generator (Python/Jinja2): teksten, productdata, templates, foto's en tools. Zie `bron/LEESMIJ.txt`. |

## Bouwen

Vanuit `bron/` (Python 3.10+, `pip install -r requirements.txt`, Playwright Chromium, Node.js voor Pagefind):

```
./bouwen.sh
```

De build schrijft standaard naar `../qpall-website`, dus naar de map `qpall-website/` in deze repository.

## Netlify

Bij koppelen aan deze repository: base directory `qpall-website`, geen build command.
Tot livegang staat `NOINDEX_ALL = True` in `bron/site_config.py` (noindex op elke pagina en een X-Robots-Tag-header).

Stand: update 22 (28 oktober 2026). Wijzigingen per update staan in `bron/LEESMIJ.txt`.
