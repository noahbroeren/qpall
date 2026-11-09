"""Global configuration: company data, taxonomy (sizes / types / classes) and the page registry (6 languages)."""
import os as _os

DOMAIN = 'https://qpall.com'          # primair domein zonder www (besluit Noah, 28-10-2026); www.qpall.com stuurt hierheen
LANGS = ['nl', 'en', 'de', 'fr', 'it', 'es']
DEFAULT_LANG = 'nl'
X_DEFAULT = 'en'          # hreflang x-default -> English version
LOCALE = {'nl': 'nl_NL', 'en': 'en_GB', 'de': 'de_DE', 'fr': 'fr_FR', 'it': 'it_IT', 'es': 'es_ES'}
HTML_LANG = {'nl': 'nl', 'en': 'en', 'de': 'de', 'fr': 'fr', 'it': 'it', 'es': 'es'}
LANG_REGION = {'nl': 'Nederland', 'en': 'International', 'de': 'Deutschland', 'fr': 'France', 'it': 'Italia', 'es': 'España'}
LANG_NAME = {'nl': 'Nederlands', 'en': 'English', 'de': 'Deutsch', 'fr': 'Français', 'it': 'Italiano', 'es': 'Español'}
PRICE_VALID_UNTIL = '2026-12-31'
BUILD_DATE = _os.environ.get('QP_DATE', '2026-10-15')   # <lastmod> in sitemap.xml
# Go-live date of the new site: datePublished of the seven knowledge-base guides (new on this site, 6 languages).
# SET THIS ON THE DAY OF GOING LIVE (e.g. '2026-11-16'), then build. Until then the guides use BUILD_DATE.
LAUNCH_DATE = _os.environ.get('QP_LAUNCH') or None
# Google Tag Manager container (set up by iClicks), e.g. 'GTM-ABC1234'. Empty = no GTM. GTM loads only after the visitor
# accepts statistics cookies. The site always pushes these dataLayer events (no cookies, nothing sent without GTM):
#   generate_lead  lead_type 'offerte' (quote form) or 'contact' (contact form): on the thank-you page after sending
#   phone_click / email_click: click on a tel: / mailto: link.   PDF downloads: GA4's own file_download (not a conversion).
GTM_ID = 'GTM-MNRQ33'            # container van iClicks (update 19); bevat o.a. Cookiebot, GA4 via sst.qpall.com, Google Ads,
                                 # LinkedIn Insight, Leadinfo en HubSpot
# GTM en HubSpot draaien ALLEEN op de productiesite (hostnamen hieronder), niet op de Netlify-testsite: de container is
# voor qpall.com ingericht (Cookiebot controleert het domein). Op productie vraagt Cookiebot (uit de container) om
# toestemming en verbergt de site de eigen cookiemelding; komt Cookiebot niet binnen 5 s, dan toont de site toch de eigen melding.
PROD_HOSTS = ['qpall.com', 'www.qpall.com']
# HubSpot (portal 25981072, EU): de trackingcode (embed code van HubSpot) staat op elke pagina net voor </body>, eerst als
# type="text/plain". site.js zet hem aan na toestemming voor marketing, op de hostnamen in HUBSPOT_HOSTS (update 24: ook
# de testsites, zodat bezoeken en formulieren daar te testen zijn). Op productie laadt de GTM-container dezelfde code al
# (tag 122): site.js laadt hem dan alleen zelf als hij er na de toestemming nog niet is.
HUBSPOT_HOSTS = PROD_HOSTS + ['qpall.netlify.app', 'staging.qpall.com']
HUBSPOT_ID = '25981072'
HUBSPOT_REGION = 'eu1'
# Offerte- en contactformulier ook naar HubSpot (Forms API v3, naast Netlify). Vul de form-GUID's in van twee formulieren in
# HubSpot (Marketing > Formulieren). Leeg = niet doorsturen. Velden: zie LEESMIJ.txt (update 19).
HUBSPOT_FORMS = {'offerte': '', 'contact': ''}

# productcatalogus per taal (input/catalogus/<taal>.pdf  ->  /downloads/<naam>)
CATALOG_EDITION = '2026-11'
CATALOG_FILES = {
    'nl': 'downloads/q-pall-productcatalogus-2026-nl.pdf',
    'en': 'downloads/q-pall-product-catalogue-2026-en.pdf',
    'de': 'downloads/q-pall-produktkatalog-2026-de.pdf',
    'fr': 'downloads/q-pall-catalogue-produits-2026-fr.pdf',
    'it': 'downloads/q-pall-catalogo-prodotti-2026-it.pdf',
    'es': 'downloads/q-pall-catalogo-productos-2026-es.pdf',
}
_ROOT = _os.path.dirname(_os.path.abspath(__file__))


def catalog_size(lang):
    p = _os.path.join(_ROOT, 'input/catalogus', lang + '.pdf')
    mb = _os.path.getsize(p) / 1048576 if _os.path.exists(p) else 13.0
    s = f"{mb:.0f} Mo" if lang == 'fr' else f"{mb:.0f} MB"     # French: mégaoctet (update 33)
    return s


COMPANY = {
    'name': 'Q-Pall',
    'legal': 'Q-PALL BV',
    'street': 'Edisonweg 9',
    'zip': '5466 AR',
    'city': 'Veghel',
    'cc': 'NL',
    'phone': '+31 (0)413 353 111',
    'phone_href': '+31413353111',
    'email': 'info@qpall.com',
    'linkedin': 'https://www.linkedin.com/company/q-pall-bv/',
    'youtube': 'https://www.youtube.com/@QPallBV',
    'award': 'EcoVadis Bronze 2026',      # schema.org 'award' (EcoVadis Bronze, October 2026, top 35%)
    'founded': 2005,
    # registration numbers (footer, under the Veghel address, and Organization JSON-LD)
    'coc': '55410715',            # KvK (Kamer van Koophandel 's-Hertogenbosch)
    'vat': 'NL851696144B01',      # btw-identificatienummer
    # parent company: 'Onderdeel van de AVK Group' (homepage) and /over-q-pall/ link here
    'group_name': 'AVK Group',
    'group_url': 'https://www.avkvalves.com/',
    'geo': (51.6161, 5.5486),
    'hours': [('Mo-Th', '07:30', '16:30'), ('Fr', '07:30', '15:30')],
    'dealer_locator': 'https://app.mach3locator.io/l/Vgkn1twgwN',
    'terms_pdf': '/files/q-pall-bv-terms-and-conditions.pdf',
    'simplybook': 'https://avkplasticsbv.simplybook.it',
}

# International dealers (update 27): copy of the dealer map (COMPANY['dealer_locator'], mach3locator) on 02-11-2026,
# independent dealers only (the Q-Pall / AVK-Q-Pall locations on that map are left out). Shown per country below the
# map on /internationale-dealers/, so the page shows the network without loading the map (cookies).
# (ISO country code, name, city). When a dealer is added or leaves the map: change this list and rebuild.
DEALERS = [
    ('GB', 'All Pallets', 'Eastbourne'),
    ('FR', 'Bac-Land Pack', 'Balma'),
    ('PT', 'Carepack', 'Leiria'),
    ('DE', 'Cargo Plast', 'Salem'),
    ('IT', 'CMP', 'Saluzzo'),
    ('DK', 'Dansk Transport Emballage', 'Vojens'),
    ('CH', 'Dynamex', 'Ossingen'),
    ('DE', 'GFH Kunststofftechnik', 'Rosenheim'),
    ('BE', 'Indupack', 'Lommel'),
    ('BE', 'M-Packaging', 'Wuustwezel'),
    ('ES', 'Osona Industrial Plastics', 'Sant Miquel de Balenyà'),
    ('AT', 'Rumpl', 'Graz'),
    ('NO', 'Strombergs Plast', 'Rælingen'),
    ('US', 'The Nelson Company', 'Baltimore, MD'),
    ('SE', 'Tofo Trading', 'Nybro'),
    ('US', 'Tranpak', 'Madera, CA'),
    ('SI', 'Tricor', 'Selca'),
    ('FI', 'Zymotec', 'Riihimäki'),
]

# contact persons (update 13): shown at 'Praat met een specialist' (homepage), on the thank-you page, on the team page
# (/over-q-pall/team/) and as author of the knowledge-base articles (Person schema, same @id in every language).
# Photos: input/team/ (originals + cut-outs) -> static/img/team/<key>.webp (transparent cut-out, square, same framing).
# 'linkedin': personal LinkedIn URL (sameAs in the Person schema) - leave empty until known.
BD_ROLE = {l: 'Business Development' for l in ('nl', 'en', 'de', 'fr', 'it', 'es')}
TEAM = [
    {'key': 'sabine-oudshoorn', 'name': 'Sabine Oudshoorn', 'photo': '/assets/img/team/sabine-oudshoorn.webp', 'linkedin': '',
     'role': BD_ROLE,
     'bio': {'nl': 'Sabine Oudshoorn werkt bij Q-Pall op Business Development. Ze helpt bedrijven in heel Europa bij de keuze van de juiste kunststof pallet: van maat en draagklasse tot de inzet in stellingen, bij export of in hygiënische omgevingen.',
             'en': 'Sabine Oudshoorn works in Business Development at Q-Pall. She helps companies across Europe choose the right plastic pallet: from size and load class to use in racking, for export or in hygienic environments.',
             'de': 'Sabine Oudshoorn arbeitet bei Q-Pall im Business Development. Sie hilft Unternehmen in ganz Europa, die passende Kunststoffpalette zu finden: von Größe und Lastklasse bis zum Einsatz im Regal, im Export oder in hygienischen Bereichen.',
             'fr': "Sabine Oudshoorn travaille au Business Development de Q-Pall. Elle aide les entreprises de toute l'Europe à choisir la bonne palette plastique : dimensions, classe de charge, utilisation en rayonnage, à l'export ou en environnement hygiénique.",
             'it': "Sabine Oudshoorn lavora nel Business Development di Q-Pall. Aiuta le aziende di tutta Europa a scegliere il pallet in plastica giusto: dalle dimensioni alla classe di carico, fino all'uso su scaffalature, per l'export o in ambienti igienici.",
             'es': 'Sabine Oudshoorn trabaja en Business Development en Q-Pall. Ayuda a empresas de toda Europa a elegir el palet de plástico adecuado: desde el tamaño y la clase de carga hasta su uso en estanterías, en exportación o en entornos higiénicos.'},
     'knows': {'nl': ['Kunststof pallets', 'Palletmaten', 'Draagvermogen van pallets', 'Hygiënische pallets', 'Exportpallets'],
               'en': ['Plastic pallets', 'Pallet sizes', 'Pallet load capacity', 'Hygienic pallets', 'Export pallets'],
               'de': ['Kunststoffpaletten', 'Palettenmaße', 'Tragfähigkeit von Paletten', 'Hygienepaletten', 'Exportpaletten'],
               'fr': ['Palettes plastique', 'Dimensions de palettes', 'Capacité de charge des palettes', 'Palettes hygiéniques', "Palettes d'export"],
               'it': ['Pallet in plastica', 'Dimensioni dei pallet', 'Portata dei pallet', 'Pallet igienici', 'Pallet da export'],
               'es': ['Palets de plástico', 'Medidas de palets', 'Capacidad de carga de palets', 'Palets higiénicos', 'Palets de exportación']}},
    {'key': 'john-van-boesschoten', 'name': 'John van Boesschoten', 'photo': '/assets/img/team/john-van-boesschoten.webp', 'linkedin': '',
     'role': BD_ROLE,
     'bio': {'nl': 'John van Boesschoten werkt bij Q-Pall op Business Development. Hij denkt met klanten mee over hun palletstromen, de kosten per omloop en de overstap van houten naar kunststof pallets.',
             'en': 'John van Boesschoten works in Business Development at Q-Pall. He works with customers on their pallet flows, the cost per trip and the switch from wooden to plastic pallets.',
             'de': 'John van Boesschoten arbeitet bei Q-Pall im Business Development. Er berät Kunden zu ihren Palettenkreisläufen, den Kosten pro Umlauf und dem Umstieg von Holz- auf Kunststoffpaletten.',
             'fr': 'John van Boesschoten travaille au Business Development de Q-Pall. Il accompagne les clients sur leurs flux de palettes, le coût par rotation et le passage des palettes bois aux palettes plastique.',
             'it': 'John van Boesschoten lavora nel Business Development di Q-Pall. Affianca i clienti sui loro flussi di pallet, sul costo per ciclo e sul passaggio dai pallet in legno a quelli in plastica.',
             'es': 'John van Boesschoten trabaja en Business Development en Q-Pall. Asesora a los clientes sobre sus flujos de palets, el coste por rotación y el cambio de palets de madera a palets de plástico.'},
     'knows': {'nl': ['Kunststof pallets', 'Kunststof versus houten pallets', 'Palletprijzen en kosten per omloop', 'PPWR', 'Gerecycled kunststof'],
               'en': ['Plastic pallets', 'Plastic versus wooden pallets', 'Pallet prices and cost per trip', 'PPWR', 'Recycled plastic'],
               'de': ['Kunststoffpaletten', 'Kunststoff- versus Holzpaletten', 'Palettenpreise und Kosten pro Umlauf', 'PPWR', 'Recycelter Kunststoff'],
               'fr': ['Palettes plastique', 'Palettes plastique ou bois', 'Prix des palettes et coût par rotation', 'PPWR', 'Plastique recyclé'],
               'it': ['Pallet in plastica', 'Pallet in plastica o in legno', 'Prezzi dei pallet e costo per ciclo', 'PPWR', 'Plastica riciclata'],
               'es': ['Palets de plástico', 'Palets de plástico o de madera', 'Precios de palets y coste por rotación', 'PPWR', 'Plástico reciclado']}},
]
TEAM_BY = {p['key']: p for p in TEAM}
TEAM_BY_NAME = {p['name']: p for p in TEAM}
# author per knowledge-base article (alternating); news articles use their 'author' front matter when it is a TEAM name
AUTHORS = {'guide-choose': 'sabine-oudshoorn', 'guide-prices': 'john-van-boesschoten', 'guide-sizes': 'sabine-oudshoorn',
           'guide-wood': 'john-van-boesschoten', 'guide-ispm': 'sabine-oudshoorn', 'guide-ppwr': 'john-van-boesschoten',
           'guide-automation': 'sabine-oudshoorn', 'news-hdpe': 'john-van-boesschoten'}

# old country domains (update 13): every URL on these domains goes in one 301 straight to the plastic pallets category page
# in that language (no extra hop via qpall.com/). The domains must be added in Netlify as domain aliases of this site.
COUNTRY_DOMAINS = [('qpall-kunststof-pallets.nl', 'nl'), ('qpall-kunststoff-paletten.de', 'de'), ('qpall-palettes-plastique.fr', 'fr'),
                   ('qpall-paletas-de-plastico.es', 'es'), ('qpall-plastic-pallets.com', 'en'), ('qpall-pallet-in-plastica.it', 'it')]

# country names per language (ISO code -> name)
COUNTRY = {
    'NL': {'nl': 'Nederland', 'en': 'the Netherlands', 'de': 'Niederlande', 'fr': 'Pays-Bas', 'it': 'Paesi Bassi', 'es': 'Países Bajos'},
    'DK': {'nl': 'Denemarken', 'en': 'Denmark', 'de': 'Dänemark', 'fr': 'Danemark', 'it': 'Danimarca', 'es': 'Dinamarca'},
    'DE': {'nl': 'Duitsland', 'en': 'Germany', 'de': 'Deutschland', 'fr': 'Allemagne', 'it': 'Germania', 'es': 'Alemania'},
    'FR': {'nl': 'Frankrijk', 'en': 'France', 'de': 'Frankreich', 'fr': 'France', 'it': 'Francia', 'es': 'Francia'},
    'ES': {'nl': 'Spanje', 'en': 'Spain', 'de': 'Spanien', 'fr': 'Espagne', 'it': 'Spagna', 'es': 'España'},
    'UK': {'nl': 'Verenigd Koninkrijk', 'en': 'United Kingdom', 'de': 'Vereinigtes Königreich', 'fr': 'Royaume-Uni', 'it': 'Regno Unito', 'es': 'Reino Unido'},
}

# production locations. 'V' Veghel = headquarters and storage (no production).
LOCATIONS = {
    'B': {'name': 'Balk', 'cc': 'NL'},
    'R': {'name': 'Ribe', 'cc': 'DK'},
    'M': {'name': 'Marktoberdorf', 'cc': 'DE'},
    'N': {'name': 'Nantes', 'cc': 'FR'},
    'L': {'name': 'Lleida', 'cc': 'ES'},
    'C': {'name': 'Chesterfield', 'cc': 'UK'},
    'V': {'name': 'Veghel', 'cc': 'NL', 'hq': True},
}
FACTORIES = ['B', 'R', 'M', 'N', 'L', 'C']     # 6 productielocaties
FLAG = {'NL': '🇳🇱', 'DK': '🇩🇰', 'DE': '🇩🇪', 'FR': '🇫🇷', 'ES': '🇪🇸', 'UK': '🇬🇧'}

# Transport aanmelden (SimplyBook, account avkplasticsbv). location/category = predefined ids.
# PRICES (update 34, Noah 9-11-2026): no prices on the site. True brings every price back in one go: product cards,
# product pages (price box, versions table, sticky bar), Product/Offer schema, meta descriptions, the "with price"
# filter, sorting by price, the comparison, the accessory cards and the series cards on the homepage. The price list
# (data/prijzen.csv -> products.json) stays in the source. Texts that mentioned a price were rewritten without one;
# the last version with prices is the GitHub branch 'met-prijzen' (see LEESMIJ.txt, update 34).
SHOW_PRICES = False

# Search engines: while NOINDEX_ALL is True every page gets <meta name="robots" content="noindex, nofollow">
# and Netlify sends "X-Robots-Tag: noindex, nofollow" for every file (pages, PDFs), so nothing (prices
# included) ends up in Google. Set to False when the site goes live on qpall.com and the prices
# have been approved, then rebuild.
NOINDEX_ALL = True

# Pallets worden alleen per volle stapel verkocht. Het aantal per stapel verschilt per pallet (update 12):
# data/stapels.json, gemaakt door tools/stapels.py uit input/stapels/palletmaten voor calculator.docx.

# Kleur per artikelnummer (afgeleid van de productfoto's en de code: CDB = blauw, CDG = grijs, ECO = zwart).
# Niet genoemd = zwart (standaard), andere kleuren op aanvraag.
SKU_COLOUR = {
    'QPH1208HP3RR-CDB': 'blue', 'QPH1208HP3RR-CDG': 'grey', 'QPH1208HR3RR-ECO': 'black',
    'QPH1208HP3RR-CDGR': 'grey', 'QPH1208HR3R-ECOR': 'black_blue',
    'QPH1210HP3R-CDG': 'grey', 'QPH1210HP3RR': 'grey', 'QPH1210HP3RR-CDG': 'grey', 'QPH1210HR5RR-CD': 'black',
    'QPW1208HP3RR-CD': 'lightgrey', 'QPW1210HP3RR-CD': 'lightgrey', 'QPW1210HP5RR-CD': 'lightgrey',
    'H1-Europallet': 'grey',
}

# SimplyBook shows a Google Translate language picker and a cart above the booking steps
# (features switched on in the SimplyBook account). The site hides that strip by moving the
# booking frame up by this many pixels. Set to 0 once both features are switched off in
# SimplyBook (Custom features: Google Translate / Multiple bookings).
SB_CROP = 160

# Transport booking (SimplyBook location / category ids). addr = company line, street, postcode + place;
# hours = loading and unloading times as (first day, last day, [time ranges]) with 1 = Monday.
# Source: the register-transport pages on the old qpall.com (October 2026).
TRANSPORT_SITES = [
    {'id': 'veghel', 'name': 'Q-Pall Veghel', 'cc': 'NL', 'loc': 4, 'cat': 8, 'hol': None,
     'addr': ('Q-Pall BV', 'Edisonweg 9', '5466 AR Veghel'),
     'hours': [(2, 4, ['07:30–12:00', '12:30–16:00']), (5, 5, ['07:30–12:00', '12:30–15:00'])]},
    {'id': 'balk', 'name': 'Q-Pall Balk', 'cc': 'NL', 'loc': 3, 'cat': 5, 'hol': ('christmas', '24-12-2026', '03-01-2027'),
     'addr': ('Q-Pall | AVK Plastics', 'Eigen Haard 11', '8561 EX Balk'), 'hours': [(1, 5, ['07:00–16:30'])]},
    {'id': 'balk-paques', 'name': 'Q-Pall Balk (Paques)', 'cc': 'NL', 'loc': 8, 'cat': 5, 'hol': ('christmas', '24-12-2026', '03-01-2027'),
     'addr': ('Q-Pall | AVK Plastics', 'Tjalke de Boerstrjitte 13', '8561 EL Balk'), 'hours': [(1, 4, ['07:00–16:00']), (5, 5, ['07:00–12:00'])]},
    {'id': 'idskenhuizen', 'name': 'Q-Pall Idskenhuizen', 'cc': 'NL', 'loc': 9, 'cat': 14, 'hol': ('christmas', '24-12-2026', '03-01-2027'),
     'addr': ('Q-Pall BV', 'Stripedyk 2a', '8523 NB Idskenhuizen'), 'hours': [(1, 5, ['07:00–16:30'])]},
    {'id': 'heerenveen', 'name': 'Q-Pall Heerenveen', 'cc': 'NL', 'loc': 10, 'cat': 15, 'hol': ('christmas', '24-12-2026', '03-01-2027'),
     'addr': ('Q-Pall B.V.', 'Venus 3', '8448 CE Heerenveen'), 'hours': [(1, 4, ['07:00–12:00', '12:30–15:30']), (5, 5, ['07:00–12:00', '12:30–15:00'])]},
    {'id': 'nijemirdum', 'name': 'Q-Pall Nijemirdum', 'cc': 'NL', 'loc': 1, 'cat': 6, 'hol': ('christmas', '24-12-2026', '03-01-2027'),
     'addr': ('Q-Pall | Runia', 'Wytlânsdijkje 17', '8566 JG Nijemirdum'), 'hours': [(1, 5, ['07:00–16:30'])]},
    {'id': 'rijen', 'name': 'Q-Pall Rijen', 'cc': 'NL', 'loc': 7, 'cat': 11, 'hol': None,
     'addr': ('Q-Pall BV', 'Ericssonstraat 17', '5121 MK Rijen'), 'hours': [(1, 5, ['08:00–15:00'])]},
    {'id': 'scharsterbrug', 'name': 'Q-Pall Scharsterbrug', 'cc': 'NL', 'loc': 12, 'cat': 17, 'hol': ('christmas', '24-12-2026', '03-01-2027'),
     'addr': ('Q-Pall B.V.', 'Hollandiastraat 62', '8517 HH Scharsterbrug'), 'hours': [(1, 5, ['08:00–12:00', '12:30–16:00'])]},
    {'id': 'marktoberdorf', 'name': 'Q-Pall Marktoberdorf', 'cc': 'DE', 'loc': 5, 'cat': 10, 'hol': ('christmas', '21-12-2026', '06-01-2027'),
     'addr': ('Q-Pall | MBS', 'Wertachstraße 25', '87616 Marktoberdorf'), 'hours': [(1, 4, ['08:00–11:30', '12:30–14:30'])]},
    {'id': 'ribe', 'name': 'Q-Pall Ribe', 'cc': 'DK', 'loc': 6, 'cat': 9, 'hol': ('christmas', '19-12-2026', '03-01-2027', 'closed'),   # laatste werkdag 18-12, eerste werkdag 4-1
     'addr': ('Q-Pall | AVK Plast', 'Øster Vedsted Vej 26 A', '6760 Ribe'),
     'hours': [(1, 3, ['07:00–15:30']), (4, 4, ['07:00–15:00']), (5, 5, ['07:00–12:00'])]},
    {'id': 'aigrefeuille', 'name': 'Q-Pall Aigrefeuille-sur-Maine', 'cc': 'FR', 'loc': 13, 'cat': 18, 'hol': None,
     'addr': ('Q-Pall | France', '1 Rue de l’Industrie', '44140 Aigrefeuille-sur-Maine'),
     'hours': [(1, 4, ['07:00–11:30', '12:30–14:30']), (5, 5, ['07:00–12:30'])]},
    {'id': 'borges-blanques', 'name': 'Q-Pall Les Borges Blanques', 'cc': 'ES', 'loc': 11, 'cat': 16, 'hol': None,
     'addr': ('Q-Pall | Spain', 'Carrer les Verdunes, 33', '25400 Les Borges Blanques (Lleida)'), 'hours': [(1, 5, ['09:00–17:00'])]},
]

# ----------------------------------------------------------------------------------
# Taxonomy
# ----------------------------------------------------------------------------------
SIZES = [
    {'key': '600x400', 'L': 600, 'W': 400, 'slug': '600-x-400-mm'},
    {'key': '600x800', 'L': 600, 'W': 800, 'slug': '600-x-800-mm'},
    {'key': '760x1140', 'L': 760, 'W': 1140, 'slug': '760-x-1140-mm'},
    {'key': '1100x1100', 'L': 1100, 'W': 1100, 'slug': '1100-x-1100-mm'},
    {'key': '1140x1140', 'L': 1140, 'W': 1140, 'slug': '1140-x-1140-mm'},
    {'key': '1200x800', 'L': 1200, 'W': 800, 'slug': '1200-x-800-mm'},
    {'key': '1200x1000', 'L': 1200, 'W': 1000, 'slug': '1200-x-1000-mm'},
    {'key': '1200x1200', 'L': 1200, 'W': 1200, 'slug': '1200-x-1200-mm'},
    {'key': '1300x1100', 'L': 1300, 'W': 1100, 'slug': '1300-x-1100-mm'},
]
SIZE_BY_KEY = {s['key']: s for s in SIZES}

TYPES = [
    {'key': 'export', 'slug': {'nl': 'export-pallets', 'en': 'export-pallets', 'de': 'einwegpaletten', 'fr': 'palettes-export', 'it': 'pallet-export', 'es': 'palets-exportacion'}},
    {'key': 'nestable', 'slug': {'nl': 'nestbare-pallets', 'en': 'nestable-pallets', 'de': 'nestbare-paletten', 'fr': 'palettes-emboitables', 'it': 'pallet-incastrabili', 'es': 'palets-encajables'}},
    {'key': 'hygienic', 'slug': {'nl': 'hygienische-pallets', 'en': 'hygienic-pallets', 'de': 'hygienepaletten', 'fr': 'palettes-hygieniques', 'it': 'pallet-igienici', 'es': 'palets-higienicos'}},
    {'key': 'cp', 'slug': {'nl': 'cp-pallets', 'en': 'cp-pallets', 'de': 'cp-paletten', 'fr': 'palettes-cp', 'it': 'pallet-cp', 'es': 'palets-cp'}},
    {'key': 'display', 'slug': {'nl': 'display-pallets', 'en': 'display-pallets', 'de': 'displaypaletten', 'fr': 'palettes-display', 'it': 'pallet-espositori', 'es': 'palets-expositores'}},
    {'key': 'block', 'slug': {'nl': 'blokpallets', 'en': 'block-pallets', 'de': 'blockpaletten', 'fr': 'palettes-blocs', 'it': 'pallet-a-blocchi', 'es': 'palets-de-bloques'}},
    {'key': 'antislip', 'slug': {'nl': 'antislip-pallets', 'en': 'anti-slip-pallets', 'de': 'antirutsch-paletten', 'fr': 'palettes-antiderapantes', 'it': 'pallet-antiscivolo', 'es': 'palets-antideslizantes'}, 'new': True},
]
TYPE_BY_KEY = {t['key']: t for t in TYPES}

CLASSES = [
    {'key': 'light', 'slug': 'light', 'name': 'Light'},
    {'key': 'medium', 'slug': 'medium', 'name': 'Medium'},
    {'key': 'heavy', 'slug': 'heavy', 'name': 'Heavy'},
]

SECTORS = [
    {'key': 'chemical', 'icon': 'flask', 'slug': {'nl': 'chemische-industrie', 'en': 'chemical-industry', 'de': 'chemische-industrie', 'fr': 'industrie-chimique', 'it': 'industria-chimica', 'es': 'industria-quimica'}},
    {'key': 'food', 'icon': 'food', 'slug': {'nl': 'voedingsmiddelen-industrie', 'en': 'food-industry', 'de': 'lebensmittelindustrie', 'fr': 'industrie-agroalimentaire', 'it': 'industria-alimentare', 'es': 'industria-alimentaria'}},
    {'key': 'pharma', 'icon': 'pill', 'slug': {'nl': 'farmaceutische-industrie', 'en': 'pharmaceutical-industry', 'de': 'pharmaindustrie', 'fr': 'industrie-pharmaceutique', 'it': 'industria-farmaceutica', 'es': 'industria-farmaceutica'}},
    {'key': 'beverage', 'icon': 'bottle', 'slug': {'nl': 'drankenindustrie', 'en': 'beverage-industry', 'de': 'getraenkeindustrie', 'fr': 'industrie-des-boissons', 'it': 'industria-delle-bevande', 'es': 'industria-de-bebidas'}},
    {'key': 'retail', 'icon': 'cart', 'slug': {'nl': 'retail', 'en': 'retail', 'de': 'handel', 'fr': 'grande-distribution', 'it': 'grande-distribuzione', 'es': 'distribucion'}},
    {'key': 'logistics', 'icon': 'truck', 'slug': {'nl': 'logistiek', 'en': 'logistics', 'de': 'logistik', 'fr': 'logistique', 'it': 'logistica', 'es': 'logistica'}},
    {'key': 'pooling', 'icon': 'cycle', 'slug': {'nl': 'pooling', 'en': 'pooling', 'de': 'pooling', 'fr': 'pooling', 'it': 'pooling', 'es': 'pooling'}},
]

# ----------------------------------------------------------------------------------
# Page registry. path = URL path without leading slash (directory style, trailing slash)
# ----------------------------------------------------------------------------------
PAGES = {}
PREFIX = {'nl': '', 'en': 'en/', 'de': 'de/', 'fr': 'fr/', 'it': 'it/', 'es': 'es/'}


def page(pid, paths, tpl='page', parent='home', **kw):
    """paths: dict lang -> path WITHOUT language prefix (or a single string used for every language)."""
    if isinstance(paths, str):
        paths = {l: paths for l in LANGS}
    PAGES[pid] = dict(id=pid, path={l: PREFIX[l] + paths[l] for l in LANGS}, tpl=tpl, parent=parent, **kw)


PALLETS_SLUG = {'nl': 'kunststof-pallets/', 'en': 'plastic-pallets/', 'de': 'kunststoffpaletten/', 'fr': 'palettes-plastique/',
                'it': 'pallet-in-plastica/', 'es': 'palets-de-plastico/'}
ACC_SLUG = {'nl': 'logistieke-hulpmiddelen/', 'en': 'pallet-related-products/', 'de': 'palettenzubehoer/', 'fr': 'accessoires-palettes/',
            'it': 'accessori-pallet/', 'es': 'accesorios-palets/'}
ABOUT_SLUG = {'nl': 'over-q-pall/', 'en': 'about-q-pall/', 'de': 'ueber-q-pall/', 'fr': 'a-propos-de-q-pall/', 'it': 'chi-siamo/', 'es': 'sobre-q-pall/'}
SECTORS_SLUG = {'nl': 'sectoren/', 'en': 'sectors/', 'de': 'branchen/', 'fr': 'secteurs/', 'it': 'settori/', 'es': 'sectores/'}
KB_SLUG = {'nl': 'kennisbank/', 'en': 'knowledge-base/', 'de': 'wissen/', 'fr': 'guides/', 'it': 'guide/', 'es': 'guias/'}


def sub(base, d):
    return {l: base[l] + d[l] for l in LANGS}


page('home', {l: '' for l in LANGS}, tpl='home', parent=None, priority=1.0)
page('pallets', PALLETS_SLUG, tpl='listing', priority=0.95, listing={})
for s in SIZES:
    page('size-' + s['key'], {l: PALLETS_SLUG[l] + s['slug'] + '/' for l in LANGS}, tpl='listing', parent='pallets', priority=0.9, listing={'size': s['key']})
for t in TYPES:
    page('type-' + t['key'], {l: PALLETS_SLUG[l] + t['slug'][l] + '/' for l in LANGS}, tpl='listing', parent='pallets', priority=0.85, listing={'type': t['key']})
for c in CLASSES:
    page('class-' + c['key'], {l: PALLETS_SLUG[l] + c['slug'] + '/' for l in LANGS}, tpl='listing', parent='pallets', priority=0.85, listing={'class': c['key']})
page('ultra', 'ultra-pallet-qp1210h/', tpl='page', parent='pallets', priority=0.7)

page('acc', ACC_SLUG, tpl='acc', priority=0.7, acc=None)
page('acc-collars', {'nl': 'palletranden/', 'en': 'pallet-collar/', 'de': ACC_SLUG['de'] + 'aufsatzrahmen/', 'fr': ACC_SLUG['fr'] + 'rehausses/',
                     'it': ACC_SLUG['it'] + 'sponde/', 'es': ACC_SLUG['es'] + 'collarines/'}, tpl='acc', parent='acc', priority=0.6, acc=['collar'])
page('acc-lids', sub(ACC_SLUG, {'nl': 'kunststof-deksels/', 'en': 'plastic-lids/', 'de': 'deckel/', 'fr': 'couvercles/', 'it': 'coperchi/', 'es': 'tapas/'}),
     tpl='acc', parent='acc', priority=0.6, acc=['lid'])
page('acc-freezer', sub(ACC_SLUG, {'nl': 'vriesmat-freezerspacers/', 'en': 'freezer-spacers/', 'de': 'gefrier-abstandshalter/', 'fr': 'espaceurs-de-congelation/',
                                   'it': 'distanziatori-congelamento/', 'es': 'separadores-de-congelacion/'}), tpl='acc', parent='acc', priority=0.6, acc=['freezer'])
page('acc-drip', sub(ACC_SLUG, {'nl': 'kunststof-lekbakken/', 'en': 'drip-trays/', 'de': 'auffangwannen/', 'fr': 'bacs-de-retention/', 'it': 'vasche-di-raccolta/',
                                'es': 'cubetos-de-retencion/'}), tpl='acc', parent='acc', priority=0.6, acc=['driptray', 'grating', 'grid'])
page('acc-runners', sub(ACC_SLUG, {'nl': 'onderlatten/', 'en': 'pallet-runners/', 'de': 'kufen/', 'fr': 'semelles/', 'it': 'slitte/', 'es': 'patines/'}),
     tpl='acc', parent='acc', priority=0.6, acc=['runner'])
page('used', {'nl': 'gebruikte-kunststof-pallets/', 'en': 'used-plastic-pallet/', 'de': 'gebrauchte-kunststoffpaletten/', 'fr': 'palettes-plastique-occasion/',
              'it': 'pallet-in-plastica-usati/', 'es': 'palets-de-plastico-usados/'}, tpl='page', priority=0.6)

page('about', ABOUT_SLUG, tpl='page', priority=0.7)
page('about-sustainability', sub(ABOUT_SLUG, {'nl': 'duurzaamheid/', 'en': 'sustainability/', 'de': 'nachhaltigkeit/', 'fr': 'durabilite/', 'it': 'sostenibilita/', 'es': 'sostenibilidad/'}),
     tpl='page', parent='about', priority=0.7)
page('about-local', sub(ABOUT_SLUG, {'nl': 'lokaal-produceren/', 'en': 'produce-local/', 'de': 'lokal-produzieren/', 'fr': 'production-locale/', 'it': 'produzione-locale/', 'es': 'produccion-local/'}),
     tpl='page', parent='about', priority=0.7)
page('about-custom', sub(ABOUT_SLUG, {'nl': 'customized-solutions/', 'en': 'customized-solutions/', 'de': 'massgeschneiderte-loesungen/', 'fr': 'solutions-sur-mesure/',
                                      'it': 'soluzioni-personalizzate/', 'es': 'soluciones-a-medida/'}), tpl='page', parent='about', priority=0.6)
page('about-team', sub(ABOUT_SLUG, {'nl': 'team/', 'en': 'team/', 'de': 'team/', 'fr': 'equipe/', 'it': 'team/', 'es': 'equipo/'}),
     tpl='page', parent='about', priority=0.5)
page('about-load', sub(ABOUT_SLUG, {'nl': 'belasting-van-kunststof-pallets/', 'en': 'load-of-pallets/', 'de': 'belastbarkeit-von-paletten/', 'fr': 'charge-des-palettes/',
                                    'it': 'portata-dei-pallet/', 'es': 'capacidad-de-carga/'}), tpl='page', parent='knowledge', priority=0.7)
page('about-glossary', sub(ABOUT_SLUG, {'nl': 'kunststof-pallet-begrippenlijst/', 'en': 'pallet-terminology-faq/', 'de': 'paletten-glossar/', 'fr': 'glossaire-palettes/',
                                        'it': 'glossario-pallet/', 'es': 'glosario-de-palets/'}), tpl='page', parent='knowledge', priority=0.6)

page('sectors', SECTORS_SLUG, tpl='sectors', priority=0.7)
for s in SECTORS:
    page('sector-' + s['key'], {l: SECTORS_SLUG[l] + s['slug'][l] + '/' for l in LANGS}, tpl='page', parent='sectors', priority=0.65, sector=s['key'])

page('knowledge', KB_SLUG, tpl='knowledge', priority=0.6)
# knowledge base: order on /kennisbank/ (first = featured) and filter category per item
KB_ITEMS = [('guide-ppwr', 'reg'), ('guide-prices', 'buy'), ('guide-choose', 'buy'), ('guide-sizes', 'tech'), ('guide-automation', 'tech'),
            ('guide-wood', 'sus'), ('guide-ispm', 'export'), ('about-load', 'tech'), ('about-glossary', 'tech'), ('about-sustainability', 'sus'),
            ('news-hdpe', 'sus')]
# extra items at the bottom of the 'Kennisbank' sidebar of the knowledge-base articles (after the guides)
KB_SIDE_EXTRA = ['news-hdpe', 'about-glossary']
# products shown under each knowledge-base article ("Pallets bij dit onderwerp")
ARTICLE_RECOMMEND = {
    'guide-ppwr': ['qp6040mb4f', 'qp6080mb6fr', 'qp1208lb9fr', 'qp1208lb9fr-cd'],
    'guide-prices': ['qp1208lb9fr', 'qp1208mb3rr', 'qp1210mb3rr', 'qp1208hb3rr'],
    'guide-choose': ['qp1208lb9fr', 'qp1208mb3rr-cd', 'qp1210mb3r-cd-ao', 'qp1210hb3rr'],
    'guide-sizes': ['qp1208mb3rr', 'qp1210mb3rr', 'qp1111mb3r-as', 'qp1140mb3rr'],
    'guide-automation': ['qp1210hb3rr-cd', 'qp1208hb3rr', 'qp1210hp3r-ao', 'qp1311hb5r'],
    'guide-wood': ['qp1208lb9fr', 'qp1210lb3rr', 'qp1208hb3rr', 'qp1210hb5rr'],
    'guide-ispm': ['qp1208lb9fr', 'qp1210lb9fr', 'qp1140lb9fr', 'qp76114lb9fr'],
}
KB_CATS = ['buy', 'tech', 'export', 'reg', 'sus']
GUIDES = ['guide-choose', 'guide-prices', 'guide-sizes', 'guide-wood', 'guide-ispm', 'guide-ppwr', 'guide-automation']
page('guide-choose', sub(KB_SLUG, {'nl': 'kunststof-pallet-kiezen/', 'en': 'choosing-a-plastic-pallet/', 'de': 'kunststoffpalette-waehlen/', 'fr': 'choisir-une-palette-plastique/',
                                   'it': 'scegliere-un-pallet-in-plastica/', 'es': 'elegir-un-palet-de-plastico/'}), tpl='article', parent='knowledge', priority=0.6)
page('guide-prices', sub(KB_SLUG, {'nl': 'kunststof-pallet-prijs/', 'en': 'plastic-pallet-prices/', 'de': 'kunststoffpalette-preis/', 'fr': 'prix-palette-plastique/',
                                   'it': 'prezzo-pallet-in-plastica/', 'es': 'precio-palet-de-plastico/'}), tpl='article', parent='knowledge', priority=0.7)
page('guide-wood', sub(KB_SLUG, {'nl': 'kunststof-of-houten-pallets/', 'en': 'plastic-vs-wooden-pallets/', 'de': 'kunststoff-oder-holzpaletten/', 'fr': 'palettes-plastique-ou-bois/',
                                 'it': 'pallet-in-plastica-o-legno/', 'es': 'palets-de-plastico-o-madera/'}), tpl='article', parent='knowledge', priority=0.6)
page('guide-sizes', sub(KB_SLUG, {'nl': 'palletmaten/', 'en': 'pallet-sizes/', 'de': 'palettenmasse/', 'fr': 'dimensions-des-palettes/', 'it': 'misure-dei-pallet/', 'es': 'medidas-de-palets/'}),
     tpl='article', parent='knowledge', priority=0.6)
page('guide-ispm', sub(KB_SLUG, {'nl': 'ispm-15-export-pallets/', 'en': 'ispm-15-export-pallets/', 'de': 'ispm-15-exportpaletten/', 'fr': 'ispm-15-palettes-export/',
                                 'it': 'ispm-15-pallet-export/', 'es': 'ispm-15-palets-exportacion/'}), tpl='article', parent='knowledge', priority=0.6)
page('guide-ppwr', sub(KB_SLUG, {'nl': 'ppwr-kunststof-pallets/', 'en': 'ppwr-plastic-pallets/', 'de': 'ppwr-kunststoffpaletten/', 'fr': 'ppwr-palettes-plastique/',
                                 'it': 'ppwr-pallet-in-plastica/', 'es': 'ppwr-palets-de-plastico/'}), tpl='article', parent='knowledge', priority=0.6)
page('guide-automation', sub(KB_SLUG, {'nl': 'pallets-voor-automatisering/', 'en': 'pallets-for-automation/', 'de': 'paletten-fuer-automatisierung/', 'fr': 'palettes-pour-automatisation/',
                                       'it': 'pallet-per-automazione/', 'es': 'palets-para-automatizacion/'}), tpl='article', parent='knowledge', priority=0.6)

# News. The articles keep their qpall.com URL (same path, so links and rankings stay; Netlify adds the slash).
NEWS_SLUG = {'nl': 'nieuws/', 'en': 'news/', 'de': 'aktuelles/', 'fr': 'actualites/', 'it': 'notizie/', 'es': 'noticias/'}
page('news', NEWS_SLUG, tpl='news', priority=0.6)
# pid -> path per language (below NEWS_SLUG) and the cover image: 'photos/<name>' (brand photo, -640/-1200.webp) or a file in /assets/img/
NEWS_ITEMS = {
    # order = order on the news overview (newest first) = the order of the old qpall.com overview (update 12: PE-HD 2 back in its place).
    # From news-vally on, most articles were migrated from qpall.com in October 2026 (update 11); covers: input/brand/photo-n-<name>.webp.
    'news-stackup': ({'nl': 'hoe-de-stack-up-pallet-loopbewegingen-met-70-vermindert-q-pall/', 'en': 'how-the-stack-up-pallet-cuts-walking-movements-by-70-q-pall/', 'de': 'stack-up-palette-reduziert-gehwege-um-70-q-pall/', 'fr': 'comment-la-stack-up-pallet-reduit-les-deplacements-de-70-q-pall/', 'it': 'come-lo-stack-up-pallet-riduce-gli-spostamenti-del-70-q-pall/', 'es': 'como-el-stack-up-pallet-reduce-desplazamientos-un-70-q-pall/'},
        'photos/stackup'),
    'news-process': ({'nl': 'een-pallet-is-geen-ladingdrager-het-is-een-procesvariabele/', 'en': 'a-pallet-is-not-a-load-carrier-it-is-a-process-variable/', 'de': 'eine-palette-ist-kein-ladungstrager-sie-ist-eine-prozessvariable/', 'fr': 'une-palette-nest-pas-un-support-de-charge-cest-une-variable-de-processus/', 'it': 'un-pallet-non-e-un-supporto-di-carico-e-una-variabile-di-processo/', 'es': 'un-pale-no-es-un-soporte-de-carga-es-una-variable-de-proceso/'},
        'photos/warehouse'),
    'news-vally': ({'nl': 'welkom-vally-kunststof-pallets-zitten-in-zijn-dna/', 'en': 'welcome-vally-plastic-pallets-are-in-his-dna/', 'de': 'willkommen-vally-kunststoffpaletten-liegen-in-seiner-dna/', 'fr': 'bienvenue-vally-les-palettes-en-plastique-sont-dans-son-adn/', 'it': 'benvenuto-vally-i-pallet-in-plastica-sono-nel-suo-dna/', 'es': 'bienvenido-vally-los-palets-de-plastico-estan-en-su-adn/'},
        'photos/n-vally'),
    'news-logistics-update': ({'nl': 'update-over-wereldwijde-logistiek-en-q-pall-plastic-pallets/', 'en': 'update-on-global-logistics-and-q-pall-plastic-pallets/', 'de': 'update-zur-globalen-logistik-und-q-pall-kunststoffpaletten/', 'fr': 'mise-a-jour-sur-la-logistique-mondiale-et-les-palettes-en-plastique-q-pall/', 'it': 'actualizacion-sobre-logistica-global-y-pales-de-plastico-q-pall/', 'es': 'actualizacion-logistica-global-y-pales-q-pall/'},
        'photos/stacks'),
    'news-local': ({'nl': 'lokale-productie-als-pijler/', 'en': 'from-trend-to-necessity-local-production-as-a-pillar-for-supply-chain-resilience/', 'de': 'vom-trend-zur-notwendigkeit-lokale-produktion-als-saule-der-lieferkettenresilienz/', 'fr': 'de-la-tendance-a-la-necessite-la-production-locale-comme-pilier-de-la-resilience-de-la-supply-chain/', 'it': 'da-tendenza-a-necessita-la-produzione-locale-come-pilastro-della-resilienza-della-supply-chain/', 'es': 'de-tendencia-a-necesidad-la-produccion-local-como-pilar-de-la-resiliencia-de-la-cadena-de-suministro/'},
        'photos/local'),
    'news-auchan': ({'nl': 'auchan-zet-slimme-pallets-in/', 'en': 'auchan-deploys-smart-pallets/', 'de': 'auchan-setzt-smarte-paletten-ein/', 'fr': 'auchan-deploie-palettes-intelligentes/', 'it': 'auchan-impiega-pallet-intelligenti/', 'es': 'auchan-despliega-palets-inteligentes/'},
        'photos/retail'),
    'news-antislip-grip': ({'nl': 'anti-slip-pallets-voor-meer-veiligheid-magazijn/', 'en': 'anti-slip-pallets-for-better-warehouse-safety/', 'de': 'antirutsch-paletten-fuer-mehr-lagersicherheit/', 'fr': 'innovation-en-matiere-dadherence-la-nouvelle-generation-de-palettes-medium-antiderapantes/', 'it': 'pallet-antiscivolo-per-maggiore-sicurezza-in-magazzino/', 'es': 'innovacion-en-agarre-la-nueva-generacion-de-pallets-medianos-antideslizantes/'},
        'photos/n-antislip-grip'),
    'news-bestpal-mpackaging': ({'nl': 'yourbestpal-in-the-spotlight-m-packaging-belgie/', 'en': 'yourbestpal-in-the-spotlight-m-packaging-belgium/', 'de': 'yourbestpal-im-rampenlicht-m-packaging-belgien/', 'fr': 'yourbestpal-sous-les-projecteurs-m-packaging-belgique/', 'it': 'yourbestpal-sotto-i-riflettori-m-packaging-belgio/', 'es': 'yourbestpal-bajo-los-focos-m-packaging-belgica/'},
        'photos/n-bestpal-mpackaging'),
    'news-ppwr': ({'nl': 'de-ppwr-komt-eraan-hoe-voorbereid-is-jouw-transportverpakking/', 'en': 'the-ppwr-is-coming-how-ready-is-your-transport-packaging/', 'de': 'die-ppwr-kommt-wie-gut-ist-ihre-transportverpackung-vorbereitet/', 'fr': 'la-ppwr-arrive-votre-emballage-de-transport-est-il-pret/', 'it': 'sta-arrivando-il-ppwr-quanto-e-pronta-la-tua-confezione-da-trasporto/', 'es': 'llega-el-ppwr-que-tan-preparada-esta-tu-solucion-de-embalaje-de-transporte/'},
        'photos/n-ppwr'),
    'news-euro-export': ({'nl': 'wat-is-het-verschil-tussen-europallets-en-export-pallets/', 'en': 'what-is-the-difference-between-euro-pallets-and-export-pallets/', 'de': 'was-ist-der-unterschied-zwischen-europaletten-und-einwegpaletten/', 'fr': 'quelle-est-la-difference-entre-les-palettes-europe-et-le-palette-dexportation/', 'it': 'qual-e-la-differenza-tra-gli-europallet-e-i-pallet-da-esportazione/', 'es': 'cual-es-la-diferencia-entre-los-europalets-y-pale-de-exportacion/'},
        'photos/n-euro-export'),
    'news-future-logistics': ({'nl': 'waarom-kunststof-pallets-de-toekomst-van-logistiek-zijn/', 'en': 'why-plastic-pallets-are-the-future-of-logistics/', 'de': 'warum-kunststoffpaletten-die-zukunft-der-logistik-sind/', 'fr': 'pourquoi-les-palettes-en-plastique-sont-lavenir-de-la-logistique/', 'it': 'perche-i-pallet-in-plastica-sono-il-futuro-della-logistica/', 'es': 'por-que-los-palets-de-plastico-son-el-futuro-de-la-logistica/'},
        'photos/n-future-logistics'),
    'news-scopac': ({'nl': 'q-pall-partner-in-scopac-project-van-restafval-naar-duurzame-pallets/', 'en': 'q-pall-partner-in-scopac-project-from-residual-waste-to-sustainable-pallets/', 'de': 'q-pall-partner-im-scopac-projekt-von-restabfall-zu-nachhaltigen-paletten/', 'fr': 'q-pall-partenaire-du-projet-scopac-des-dechets-residuels-aux-palettes-durables/', 'it': 'q-pall-partner-del-progetto-scopac-dai-rifiuti-residui-a-pallet-sostenibili/', 'es': 'q-pall-socio-del-proyecto-scopac-de-residuos-a-palets-sostenibles/'},
        'photos/n-scopac'),
    'news-local-resilience': ({'nl': 'van-globale-afhankelijkheid-naar-lokale-veerkracht/', 'en': 'from-global-dependence-to-local-resilience/', 'de': 'von-globaler-abhangigkeit-zu-lokaler-resilienz/', 'fr': 'de-la-dependance-mondiale-a-la-resilience-locale/', 'it': 'dalla-dipendenza-globale-alla-resilienza-locale/', 'es': 'de-la-dependencia-global-a-la-resiliencia-local/'},
        'photos/mould'),
    'news-sitl-2025': ({'nl': 'q-pall-op-sitl-2025-samen-bouwen-aan-de-toekomst-van-logistiek/', 'en': 'q-pall-at-sitl-2025-shaping-the-future-of-logistics-together/', 'de': 'q-pall-auf-der-sitl-2025-gemeinsam-die-zukunft-der-logistik-gestalten/', 'fr': 'q-pall-au-sitl-2025-co-creons-lavenir-de-la-logistique/', 'it': 'q-pall-a-sitl-2025-insieme-per-plasmare-il-futuro-della-logistica/', 'es': 'q-pall-en-sitl-2025-construyendo-juntos-el-futuro-de-la-logistica/'},
        'photos/n-sitl-2025'),
    'news-poolpallet': ({'nl': 'waarom-de-categorie-poolpallet-eigenlijk-overbodig-is/', 'en': 'why-is-the-category-pool-pallet-actually-redundant/', 'de': 'warum-die-kategorie-poolpallet-eigentlich-uberflussig-ist/', 'fr': 'pourquoi-la-categorie-poolpallet-est-en-fait-superflue/', 'it': 'perche-la-categoria-poolpallet-e-in-realta-superflua/', 'es': 'por-que-la-categoria-poolpallet-es-realmente-redundante/'},
        'photos/n-poolpallet'),
    'news-local-sustainability': ({'nl': 'duurzaamheid-q-palls-lokale-productie-van-pallets/', 'en': 'beyond-sustainability-q-palls-localized-production-of-pallets/', 'de': 'nachhaltigkeit-q-palls-lokalisierte-produktion-von-kunststoffpaletten/', 'fr': 'durabilite-la-production-localisee-de-palettes-eco-responsables/', 'it': 'la-sostenibilita-la-produzione-localizzata-di-pallet/', 'es': 'la-sostenibilidad-la-produccion-localizada-de-palets/'},
        'photos/n-local-sustainability'),
    'news-economical': ({'nl': 'economisch-vandaag-morgen-duur-kies-de-juiste-pallets/', 'en': 'economical-today-expensive-tomorrow-the-right-pallets/', 'de': 'okonomisch-heute-teuer-morgen-die-richtige-kunststoffpalet/', 'fr': 'economique-aujourdhui-cher-demain-choisir-les-bonnes-palettes/', 'it': 'economico-oggi-costoso-domani-scegliere-i-pallet-giusti/', 'es': 'economico-hoy-caro-manana-elegir-los-pallets-adecuados/'},
        'photos/n-economical'),
    'news-ric': ({'nl': 'ric-van-kunststoffen-de-sleutel-tot-betere-kunststofrecycling/', 'en': 'resin-identification-codes-the-key-to-better-plastic-recycling/', 'de': 'harz-identifikation-schlussel-zu-besserem-kunststoffrecycling/', 'fr': 'codes-des-resines-la-cle-pour-un-meilleur-recyclage/', 'it': 'codici-identificazione-una-chiave-un-migliore-riciclo/', 'es': 'codigos-de-resina-la-clave-para-un-mejor-reciclaje/'},
        'photos/n-ric'),
    'news-green-logistics': ({'nl': 'ontgrendelen-de-toekomst-van-groene-logistiek/', 'en': 'unlocking-the-future-of-green-logistics/', 'de': 'die-zukunft-der-green-logistics-aufschliessen/', 'fr': 'deverrouiller-lavenir-de-la-logistique-verte/', 'it': 'sbloccare-il-futuro-della-logistica-verde/', 'es': 'desbloqueando-el-futuro-de-la-logistica-verde/'},
        'photos/n-green-logistics'),
    'news-mega-order': ({'nl': 'mega-order-q-pall-uitlevering-miljoen-duurzame-pallets/', 'en': 'mega-order-q-pall-delivery-of-one-million-sustainable-pallets/', 'de': 'mega-auftrag-lieferung-von-einer-million-nachhaltiger-paletten/', 'fr': 'mega-commande-q-pall-livraison-dun-million-de-palettes/', 'it': 'mega-ordine-q-pall-inizia-la-consegna-di-un-milione-di-pallet/', 'es': 'mega-pedido-q-pall-comienza-la-entrega-de-un-millon-de-pallets/'},
        'photos/n-mega-order'),
    'news-ecovadis-silver': ({'nl': 'q-pall-behaalt-ecovadis-zilveren-medaille/', 'en': 'q-pall-achieves-ecovadis-silver-medal/', 'de': 'q-pall-erhalt-ecovadis-silbermedaille/', 'fr': 'q-pall-obtient-la-medaille-dargent-ecovadis/', 'it': 'q-pall-ottiene-la-medaglia-dargento-ecovadis/', 'es': 'q-pall-obtiene-la-medalla-de-plata-ecovadis/'},
        'photos/n-ecovadis-silver'),
    'news-choosing-pallet': ({'nl': 'het-kiezen-van-de-juiste-kunststof-pallet/', 'en': 'choosing-the-right-plastic-pallet/', 'de': 'die-wahl-der-richtigen-kunststoffpalette/', 'fr': 'choisir-la-bonne-palette-en-plastique/', 'it': 'scegliere-il-giusto-pallet-di-plastica/', 'es': 'elegir-la-paleta-de-plastico-adecuada/'},
        'photos/n-choosing-pallet'),
    'news-medium-gen3': ({'nl': 'nieuw-3e-generatie-medium-1200-x-800-kunststof-pallet/', 'en': 'new-3rd-generation-medium-1200-x-800-plastic-pallet/', 'de': 'neu-3-generation-mittelgrosse-1200-x-800-kunststoffpalette/', 'fr': 'nouveau-3eme-generation-de-palettes-plastiques-medium-1200-x-800/', 'it': 'nuovo-pallet-medio-di-terza-generazione-1200-x-800-in-plastica/', 'es': 'nueva-palet-plastico-mediana-de-1200-x-800-de-3a-generacion/'},
        'photos/n-medium-gen3'),
    'news-hdpe': ({'nl': 'gerecycled-pe-hd-2-wat-is-het-precies/', 'en': 'recycled-pe-hd-2-what-is-it-exactly/', 'de': 'recyceltes-pe-hd-2-was-ist-es-genau/', 'fr': 'pe-hd-2-recycle-quest-ce-que-cest-exactement/', 'it': 'pe-hd-2-riciclato-cose-esattamente/', 'es': 'pe-hd-2-reciclado-que-es-exactamente/'},
        'photos/regrind'),
    'news-price-wood': ({'nl': 'kunststof-wint-het-nu-ook-op-prijs-van-hout/', 'en': 'plastic-still-tops-wood-when-it-comes-to-price/', 'de': 'plastik-ubertrifft-holz-weiterhin-beim-preis/', 'fr': 'le-plastique-reste-plus-competitif-que-le-bois-en-termes-de-prix/', 'it': 'la-plastica-continua-a-superare-il-legno-in-termini-di-prezzo/', 'es': 'el-plastico-sigue-superando-a-la-madera-en-precio/'},
        'photos/n-price-wood'),
    'news-haccp': ({'nl': 'plastic-pallets-voor-de-haccp-branche/', 'en': 'pallets-for-the-haccp-industry/', 'de': 'paletten-fur-die-haccp-branche/', 'fr': 'palettes-pour-le-secteur-haccp/', 'it': 'pallet-per-il-settore-haccp/', 'es': 'palets-para-el-sector-haccp/'},
        'photos/n-haccp'),
    'news-durability': ({'nl': 'zo-bewaken-wij-de-duurzaamheid-van-onze-kunststof-pallets/', 'en': 'how-we-ensure-the-sustainability-of-our-plastic-pallets/', 'de': 'so-uberwachen-wir-die-nachhaltigkeit-unserer-kunststoffpaletten/', 'fr': 'comment-nous-assurons-la-durabilite-de-nos-palettes-en-plastique/', 'it': 'come-garantiamo-la-sostenibilita-dei-nostri-pallet-in-plastica/', 'es': 'asi-garantizamos-la-sostenibilidad-de-nuestros-palets-de-plastico/'},
        'photos/n-durability'),
    'news-choosing-size': ({'nl': 'het-kiezen-van-de-juiste-palletafmeting-hierop-dient-u-te-letten/', 'en': 'choosing-the-right-pallet-size-what-should-you-look-for/', 'de': 'die-wahl-der-richtigen-palettengrosse-dies-sollten-sie-beachten/', 'fr': 'choisir-la-bonne-taille-de-palette-a-quoi-devez-vous-faire-attention/', 'it': 'scegliere-la-giusta-dimensione-del-pallet-cosa-bisogna-cercare/', 'es': 'elegir-el-tamano-de-pale-correcto-que-deberia-mirar/'},
        'photos/n-choosing-size'),
    'news-heavy-range': ({'nl': 'vorm-volgt-functie-ons-nieuwe-assortiment-heavy-duty-pallets/', 'en': 'form-follows-function-our-new-range-of-heavy-duty-pallets/', 'de': 'form-folgt-funktion-unser-neues-sortiment-an-hochleistungspaletten/', 'fr': 'la-forme-suit-la-fonction-notre-nouvelle-gamme-de-palettes/', 'it': 'la-forma-segue-la-funzione-la-nostra-nuova-gamma-di-pallets/', 'es': 'la-forma-sigue-la-funcion-nuestra-nueva-gama-de-paletas/'},
        'photos/n-heavy-range'),
    'news-qused': ({'nl': 'kunststof-pallets-zijn-vanaf-nu-nog-duurzamer-met-q-used/', 'en': 'used-plastic-pallets-are-now-even-more-sustainable-q-used/', 'de': 'gebrauchte-kunststoffpaletten-jetzt-noch-nachhaltiger-q-used/', 'fr': 'acheter-des-palettes-en-plastique-doccasion-q-used/', 'it': 'acquista-pallet-di-plastica-usati-q-used/', 'es': 'compra-palets-de-plastico-usados-q-used/'},
        'photos/n-qused'),
    'news-medium-4840': ({'nl': 'medium-48-x-40-kunststof-pallets-voor-amerikaanse-markt/', 'en': 'medium-48-x-40-plastic-pallets-for-the-us-market/', 'de': 'kunststoffpaletten-48-x-40-fur-den-us-markt/', 'fr': 'palettes-en-plastique-48-x-40-pour-le-marche-usa/', 'it': 'pallet-in-plastica-48-x-40-per-il-mercato-usa/', 'es': 'palets-de-plastico-48-x-40-para-el-mercado-usa/'},
        'photos/n-medium-4840'),
    'news-covid': ({'nl': 'de-bijdrage-van-q-pall-kunststof-pallets-aan-het-covid-vaccin/', 'en': 'the-contribution-of-q-pall-plastic-pallets-to-the-covid-vaccine/', 'de': 'q-pall-paletten-unterstutzen-covid-impfstofflieferungen/', 'fr': 'palettes-q-pall-soutiennent-la-livraison-de-vaccins-covid/', 'it': 'le-pallet-q-pall-supportano-la-consegna-dei-vaccini-covid/', 'es': 'palets-q-pall-apoyan-la-entrega-de-vacunas-covid/'},
        'photos/n-covid'),
    'news-goplastic': ({'nl': 'al-10-jaar-een-zeer-succesvolle-samenwerking/', 'en': 'plastic-pallet-partnership-celebrates-a-decade/', 'de': 'plastikpaletten-partnerschaft-feiert-ein-jahrzehnt/', 'fr': 'un-partenariat-de-palettes-en-plastique-celebre-une-decennie/', 'it': 'una-partnership-di-pallet-in-plastica-celebra-un-decennio/', 'es': 'una-colaboracion-con-palets-de-plastico-celebra-una-decada/'},
        'photos/n-goplastic'),
    'news-hq': ({'nl': 'nieuw-europees-hoofdkantoor-q-pall-kunststof-pallets/', 'en': 'new-european-headquarters-q-pall-plastic-pallets/', 'de': 'neuer-europaischer-hauptsitz-q-pall-kunststoffpaletten/', 'fr': 'nouveau-siege-europeen-q-pall-palettes-plastique/', 'it': 'nuova-sede-europea-di-q-pall-pallet-in-plastica/', 'es': 'nueva-oficina-principal-europea-q-pall-palets-plastico/'},
        'photos/hq-corner'),
    'news-brexit': ({'nl': 'kunststof-pallets-een-oplossing-voor-im-en-export-na-brexit/', 'en': 'plastic-pallets-a-solution-for-import-and-export-after-brexit/', 'de': 'kunststoffpaletten-eine-losung-fur-im-und-export-nach-brexit/', 'fr': 'palettes-plastique-une-solution-pour-dimportation-et-dexportation/', 'it': 'pallet-di-plastica-una-soluzione-per-importazione-e-di-esportazione/', 'es': 'palets-de-plastico-una-solucion-para-importacion-y-exportacion/'},
        'photos/n-brexit'),
    'news-which-pallet': ({'nl': 'welke-kunststof-pallet-past-het-best-bij-uw-wensen/', 'en': 'which-plastic-pallets-best-suits-your-wishes/', 'de': 'welche-kunststoffpaletten-entsprechen-ihren-wunschen/', 'fr': 'quelles-palettes-plastique-repondent-le-mieux-a-vos-besoins/', 'it': 'quale-pallet-di-plastica-soddisfa-le-vostre-esigenze/', 'es': 'cuales-son-los-palets-de-plastico-que-mejor-se-adaptan-a-sus-deseos/'},
        'photos/n-which-pallet'),
    'news-recycling': ({'nl': 'het-recyclen-van-kunststof-pallets-hoe-gaat-dit-in-zijn-werk/', 'en': 'recycling-plastic-pallets-how-does-it-work/', 'de': 'wie-funktioniert-das-recycling-von-kunststoffpaletten/', 'fr': 'comment-fonctionne-le-recyclage-des-palettes-plastique/', 'it': 'pallet-di-plastica-riciclata-cosa-sono/', 'es': 'reciclaje-de-palets-plastico-como-funciona/'},
        'photos/n-recycling'),
    'news-damage': ({'nl': '9-fouten-die-leiden-tot-schade-aan-kunststof-pallets/', 'en': '9-common-mistakes-that-can-damage-plastic-pallets/', 'de': '9-fehler-die-kunststoffpaletten-beschadigen-konnen/', 'fr': '9-erreurs-qui-peuvent-endommager-les-palettes-en-plastique/', 'it': '9-errori-che-possono-danneggiare-i-pallet-in-plastica/', 'es': '9-errores-que-pueden-danar-los-palets-de-plastico/'},
        'photos/n-damage'),
    'news-industries': ({'nl': 'welke-pallets-passen-bij-uw-branche/', 'en': 'what-plastic-pallets-fit-your-industry/', 'de': 'welche-paletten-passen-zu-ihrer-branche/', 'fr': 'en-quoi-les-palettes-plastique-sont-elles-adaptees-a-votre-secteur/', 'it': 'qual-e-il-miglior-pallet-di-plastica-per-il-tuo-settore/', 'es': 'que-palets-de-plastico-se-adaptan-a-su-sector/'},
        'photos/n-industries'),
    'news-cleaning': ({'nl': 'reinigen-van-kunststof-pallets-hoe-doet-u-het-goed/', 'en': 'this-is-how-you-properly-clean-plastic-pallets/', 'de': 'so-reinigen-sie-kunststoffpaletten-auf-grundliche-art-und-weise/', 'fr': 'voici-comment-nettoyer-proprement-vos-palettes-plastique/', 'it': 'come-pulire-in-maniera-corretta-dei-pallet-di-plastica/', 'es': 'asi-es-como-se-limpian-correctamente-los-palets-plastico/'},
        'photos/n-cleaning'),
    'news-regulations': ({'nl': 'de-regelgeving-rondom-kunststof-pallets/', 'en': 'the-regulations-surrounding-plastic-pallets/', 'de': 'die-gesetze-rundum-kunststoffpaletten/', 'fr': 'la-reglementation-relative-aux-palettes-en-plastique/', 'it': 'le-regolamentazioni-riguardo-i-pallet-di-plastica/', 'es': 'las-regulaciones-aplicables-a-los-pallets-de-plastico/'},
        'photos/n-regulations'),
    'news-horeca': ({'nl': 'pallets-voor-in-de-horeca/', 'en': 'pallets-for-the-catering-industry/', 'de': 'paletten-fur-das-gaststattengewerbe/', 'fr': 'palettes-pour-lindustrie-hoteliere/', 'it': 'pallet-per-il-settore-dei-catering/', 'es': 'pallets-para-la-industria-de-la-hosteleria/'},
        'photos/beverage'),
    'news-esd': ({'nl': 'wat-zijn-esd-veilige-pallets/', 'en': 'what-are-esd-safe-pallets/', 'de': 'was-sind-esd-sichere-paletten/', 'fr': 'que-sont-les-palettes-securisees-esd/', 'it': 'cosa-sono-i-pallet-esd/', 'es': 'que-son-los-palets-seguros-esd/'},
        'photos/n-esd'),
    'news-h1': ({'nl': 'h1-pallets-wat-zijn-dat-voor-pallets/', 'en': 'what-exactly-are-h1-pallets/', 'de': 'h1-paletten-was-sind-dies-fur-paletten/', 'fr': 'que-sont-les-palettes-h1-exactement/', 'it': 'cosa-sono-esattamente-i-pallet-h1/', 'es': 'que-son-exactamente-los-palets-h1/'},
        'photos/n-h1'),
    'news-antislip-mandatory': ({'nl': 'anti-slip-pallets-is-dat-verplicht/', 'en': 'anti-slip-pallets-are-they-mandatory/', 'de': 'sind-rutschfeste-paletten-obligatorisch/', 'fr': 'palettes-antiderapantes-est-ce-obligatoire/', 'it': 'pallet-antiscivolo-sono-obbligatori/', 'es': 'palets-antideslizantes-son-obligatorios/'},
        'photos/n-antislip-mandatory'),
    'news-antistatic': ({'nl': 'het-gemak-en-de-voordelen-van-anti-statische-pallets/', 'en': 'the-ease-and-advantages-of-anti-static-pallets/', 'de': 'der-komfort-und-die-vorteile-antistatischer-paletten/', 'fr': 'la-facilite-et-les-avantages-des-palettes-antistatiques/', 'it': 'i-vantaggi-e-la-facilita-dei-pallet-antistatici/', 'es': 'la-facilidad-y-las-ventajas-de-los-palets-antiestaticos/'},
        'photos/n-antistatic'),
    'news-environment': ({'nl': 'kunststof-pallets-en-milieubewustzijn-wat-u-moet-weten/', 'en': 'plastic-pallets-and-environmental-awareness/', 'de': 'kunststoffpaletten-und-umweltbewusstsein/', 'fr': 'palettes-plastique-et-preoccupations-environnementales/', 'it': 'pallet-di-plastica-e-consapevolezza-ambientale/', 'es': 'palets-de-plastico-y-conciencia-medioambiental/'},
        'photos/n-environment'),
    'news-used-types': ({'nl': '3-veel-voorkomende-soorten-gebruikte-pallets/', 'en': '3-common-types-of-used-pallets/', 'de': '3-haufig-vorkommende-arten-von-gebrauchten-kunststoffpaletten/', 'fr': '3-types-de-palettes-reutilisees-que-lon-retrouve-souvent/', 'it': '3-tipologie-comuni-di-pallet-usati/', 'es': '3-tipos-de-palets-usados-muy-habituales/'},
        'photos/n-used-types'),
    'news-why-plastic': ({'nl': 'waarom-bedrijven-voor-kunststof-pallets-kiezen/', 'en': 'why-companies-opt-for-plastic-pallets/', 'de': 'warum-sich-unternehmen-fur-kunststoffpaletten-entscheiden/', 'fr': 'pourquoi-les-entreprises-choisissent-les-palettes-en-plastique/', 'it': 'ecco-perche-le-aziende-scelgono-i-pallet-in-plastica/', 'es': 'por-que-las-empresas-eligen-pales-plastico/'},
        'photos/n-why-plastic'),
    'news-stacking': ({'nl': 'kunststof-pallets-stapelen-kan-dat/', 'en': 'can-plastic-pallets-be-stacked/', 'de': 'paletten-stapeln-wie-hoch-wie-schwer-und-worauf-sollten-sie-achten/', 'fr': 'empiler-des-palettes-plastique-est-ce-possible/', 'it': 'impilare-usando-pallet-in-plastica-si-puo-fare/', 'es': 'apilar-palets-usando-palets-de-plastico-es-posible/'},
        'photos/n-stacking'),
    'news-goodwood': ({'nl': 'pole-position-op-goodwood-festival-of-speed/', 'en': 'plastic-pallets-in-pole-position-at-goodwood-festival/', 'de': 'kunststoffpaletten-auf-der-pole-beim-goodwood-festival/', 'fr': 'palettes-plastiques-en-pole-position-au-goodwood-festival/', 'it': 'pallet-di-plastica-in-pole-position-al-goodwood-festival/', 'es': 'palets-de-plastico-en-la-pole-position-de-goodwood/'},
        'photos/n-goodwood'),
    'news-heavy-family': ({'nl': 'q-pall-breidt-zijn-familie-van-heavy-duty-pallets-uit/', 'en': 'q-pall-grows-its-family-of-heavy-duty-pallets/', 'de': 'q-pall-erweitert-seine-familie-von-schwerlastpaletten/', 'fr': 'q-pall-developpe-sa-gamme-de-palettes-lourdes/', 'it': 'q-pall-amplia-la-sua-famiglia-di-pallet-heavy-duty/', 'es': 'q-pall-amplia-su-familia-de-heavy-duty-palets/'},
        'photos/n-heavy-family'),
}
for _pid, (_paths, _img) in NEWS_ITEMS.items():
    page(_pid, sub(NEWS_SLUG, _paths), tpl='article', parent='news', priority=0.6, news=True, img=_img)

page('catalog', {'nl': 'productcatalogus/', 'en': 'product-catalogue/', 'de': 'produktkatalog/', 'fr': 'catalogue-produits/', 'it': 'catalogo-prodotti/', 'es': 'catalogo-de-productos/'},
     tpl='page', priority=0.6)
page('dealers', {'nl': 'internationale-dealers/', 'en': 'international-dealers/', 'de': 'internationale-haendler/', 'fr': 'revendeurs-internationaux/',
                 'it': 'rivenditori-internazionali/', 'es': 'distribuidores-internacionales/'}, tpl='page', priority=0.5)
# update 20: eigen opmaak (templates/careers.html, templates/job.html) met sollicitatieformulier (Netlify-formulier 'sollicitatie', met cv)
page('careers', {'nl': 'vacatures/', 'en': 'careers/', 'de': 'karriere/', 'fr': 'carrieres/', 'it': 'lavora-con-noi/', 'es': 'empleo/'}, tpl='careers', priority=0.4)
# update 19: vacature als eigen pagina (JobPosting voor Google for Jobs); front matter 'job' in content/<taal>/job-inside-sales.md.
# Vacature vervuld? Haal de pagina weg (en zet een 301 naar /vacatures/) of zet 'job: closed: true'.
page('job-inside-sales', {'nl': 'vacatures/commercieel-medewerker-binnendienst/', 'en': 'careers/inside-sales-representative/',
                          'de': 'karriere/mitarbeiter-vertriebsinnendienst/', 'fr': 'carrieres/commercial-sedentaire/',
                          'it': 'lavora-con-noi/addetto-commerciale-interno/', 'es': 'empleo/comercial-ventas-internas/'}, tpl='job', parent='careers', priority=0.5)
# thank-you page after the application form (update 20)
page('thanks-apply', {'nl': 'vacatures/bedankt/', 'en': 'careers/thank-you/', 'de': 'karriere/danke/', 'fr': 'carrieres/merci/',
                      'it': 'lavora-con-noi/grazie/', 'es': 'empleo/gracias/'}, tpl='thanks', parent='careers', noindex=True)
page('calc', {'nl': 'laadcalculator/', 'en': 'load-calculator/', 'de': 'ladungsrechner/', 'fr': 'calculateur-de-chargement/',
              'it': 'calcolatore-di-carico/', 'es': 'calculadora-de-carga/'}, tpl='calc', priority=0.6)
page('transport', {'nl': 'transport-aanmelden/', 'en': 'register-a-transport/', 'de': 'transport-anmelden/', 'fr': 'enregistrer-un-transport/',
                   'it': 'registrare-un-trasporto/', 'es': 'registrar-un-transporte/'}, tpl='transport', priority=0.4)
page('contact', {'nl': 'contact/', 'en': 'get-in-touch/', 'de': 'kontakt/', 'fr': 'contact/', 'it': 'contatti/', 'es': 'contacto/'}, tpl='form', priority=0.6, form='contact')
page('quote', {'nl': 'offerte-aanvraag/', 'en': 'request-for-quotation/', 'de': 'angebot-anfordern/', 'fr': 'demande-de-devis/', 'it': 'richiesta-di-preventivo/',
               'es': 'solicitar-presupuesto/'}, tpl='form', priority=0.6, form='quote')
page('thanks', {'nl': 'bedankt/', 'en': 'thank-you/', 'de': 'danke/', 'fr': 'merci/', 'it': 'grazie/', 'es': 'gracias/'}, tpl='thanks', noindex=True)
# thank-you page after the quote form (update 12): summary of the request, next steps, contact person
page('thanks-quote', {'nl': 'offerte-aanvraag/bedankt/', 'en': 'request-for-quotation/thank-you/', 'de': 'angebot-anfordern/danke/',
                      'fr': 'demande-de-devis/merci/', 'it': 'richiesta-di-preventivo/grazie/', 'es': 'solicitar-presupuesto/gracias/'},
     tpl='thanks', noindex=True)
page('privacy', {'nl': 'privacyverklaring/', 'en': 'privacy-statement/', 'de': 'datenschutz/', 'fr': 'politique-de-confidentialite/', 'it': 'informativa-privacy/',
                 'es': 'politica-de-privacidad/'}, tpl='page', priority=0.2)
page('cookies', {'nl': 'cookieverklaring/', 'en': 'cookie-statement/', 'de': 'cookie-richtlinie/', 'fr': 'politique-cookies/', 'it': 'cookie-policy/',
                 'es': 'politica-de-cookies/'}, tpl='page', priority=0.2)
page('terms', {'nl': 'algemene-voorwaarden/', 'en': 'terms-and-conditions/', 'de': 'agb/', 'fr': 'conditions-generales/', 'it': 'termini-e-condizioni/',
               'es': 'condiciones-generales/'}, tpl='page', priority=0.2)

# Product pages are added dynamically by build.py (id 'p:<model-id>').

# Oude lijst (tot update 8): pagina's met een eigen OG-afbeelding. Sinds update 9 maakt tools/og.py een eigen
# beeld voor ELKE pagina en elk product in alle talen; deze lijst wordt niet meer gebruikt.
OG_PAGES = ['home', 'pallets', 'size-1200x800', 'size-1200x1000', 'size-1200x1200', 'size-1100x1100', 'size-1140x1140',
            'class-light', 'class-medium', 'class-heavy', 'type-export', 'type-nestable', 'type-hygienic', 'type-cp', 'type-antislip',
            'about', 'about-sustainability', 'about-local', 'sectors', 'quote', 'news', 'news-hdpe']

# ----------------------------------------------------------------------------------
# Redirects from the current qpall.com URLs (301)
# ----------------------------------------------------------------------------------
REDIRECTS = [
    # update 22: QP4048MB6RR-CD van de site (Noah 28-10-2026) -> QP4048MB3RR-CD (zelfde maat, gesloten dek)
    ('/kunststof-pallets/1200-x-1000-mm/kunststof-pallet-1220-x-1020-x-150-gesloten-dek-6-onderlatten-medium/', '/kunststof-pallets/1200-x-1000-mm/kunststof-pallet-1220-x-1020-x-150-gesloten-dek-3-onderlatten-medium/'),
    ('/downloads/datasheets/nl/q-pall-qp4048mb6rr-cd-nl.pdf', '/downloads/datasheets/nl/q-pall-qp4048mb3rr-cd-nl.pdf'),
    ('/en/plastic-pallets/1200-x-1000-mm/plastic-pallet-1220-x-1020-x-150-closed-deck-6-runners-medium/', '/en/plastic-pallets/1200-x-1000-mm/plastic-pallet-1220-x-1020-x-150-closed-deck-3-runners-medium/'),
    ('/downloads/datasheets/en/q-pall-qp4048mb6rr-cd-en.pdf', '/downloads/datasheets/en/q-pall-qp4048mb3rr-cd-en.pdf'),
    ('/de/kunststoffpaletten/1200-x-1000-mm/kunststoffpalette-1220-x-1020-x-150-geschlossenes-deck-6-kufen-medium/', '/de/kunststoffpaletten/1200-x-1000-mm/kunststoffpalette-1220-x-1020-x-150-geschlossenes-deck-3-kufen-medium/'),
    ('/downloads/datasheets/de/q-pall-qp4048mb6rr-cd-de.pdf', '/downloads/datasheets/de/q-pall-qp4048mb3rr-cd-de.pdf'),
    ('/fr/palettes-plastique/1200-x-1000-mm/palette-plastique-1220-x-1020-x-150-plateau-ferme-6-semelles-medium/', '/fr/palettes-plastique/1200-x-1000-mm/palette-plastique-1220-x-1020-x-150-plateau-ferme-3-semelles-medium/'),
    ('/downloads/datasheets/fr/q-pall-qp4048mb6rr-cd-fr.pdf', '/downloads/datasheets/fr/q-pall-qp4048mb3rr-cd-fr.pdf'),
    ('/it/pallet-in-plastica/1200-x-1000-mm/pallet-in-plastica-1220-x-1020-x-150-piano-chiuso-6-slitte-medium/', '/it/pallet-in-plastica/1200-x-1000-mm/pallet-in-plastica-1220-x-1020-x-150-piano-chiuso-3-slitte-medium/'),
    ('/downloads/datasheets/it/q-pall-qp4048mb6rr-cd-it.pdf', '/downloads/datasheets/it/q-pall-qp4048mb3rr-cd-it.pdf'),
    ('/es/palets-de-plastico/1200-x-1000-mm/palet-de-plastico-1220-x-1020-x-150-superficie-cerrada-6-patines-medium/', '/es/palets-de-plastico/1200-x-1000-mm/palet-de-plastico-1220-x-1020-x-150-superficie-cerrada-3-patines-medium/'),
    ('/downloads/datasheets/es/q-pall-qp4048mb6rr-cd-es.pdf', '/downloads/datasheets/es/q-pall-qp4048mb3rr-cd-es.pdf'),
    # update 19: N.QP1210LB9FR, N.QP1210LB3RR en N.QP1210LB9FR-CD van de site (Noah 28-10-2026) -> 2.QP1210LB9FR, 2.QP1210LB3RR, 2.QP1210LB9FR-CD
    ('/kunststof-pallets/1200-x-1000-mm/kunststof-pallet-1200-x-1000-x-150-open-dek-9-pootjes-light-n-qp1210lb9fr/', '/kunststof-pallets/1200-x-1000-mm/kunststof-pallet-1200-x-1000-x-150-open-dek-9-pootjes-light/'),
    ('/downloads/datasheets/nl/q-pall-n-qp1210lb9fr-nl.pdf', '/downloads/datasheets/nl/q-pall-qp1210lb9fr-nl.pdf'),
    ('/en/plastic-pallets/1200-x-1000-mm/plastic-pallet-1200-x-1000-x-150-open-deck-9-feet-light-n-qp1210lb9fr/', '/en/plastic-pallets/1200-x-1000-mm/plastic-pallet-1200-x-1000-x-150-open-deck-9-feet-light/'),
    ('/downloads/datasheets/en/q-pall-n-qp1210lb9fr-en.pdf', '/downloads/datasheets/en/q-pall-qp1210lb9fr-en.pdf'),
    ('/de/kunststoffpaletten/1200-x-1000-mm/kunststoffpalette-1200-x-1000-x-150-offenes-deck-9-fusse-light-n-qp1210lb9fr/', '/de/kunststoffpaletten/1200-x-1000-mm/kunststoffpalette-1200-x-1000-x-150-offenes-deck-9-fusse-light/'),
    ('/downloads/datasheets/de/q-pall-n-qp1210lb9fr-de.pdf', '/downloads/datasheets/de/q-pall-qp1210lb9fr-de.pdf'),
    ('/fr/palettes-plastique/1200-x-1000-mm/palette-plastique-1200-x-1000-x-150-plateau-ajoure-9-pieds-light-n-qp1210lb9fr/', '/fr/palettes-plastique/1200-x-1000-mm/palette-plastique-1200-x-1000-x-150-plateau-ajoure-9-pieds-light/'),
    ('/downloads/datasheets/fr/q-pall-n-qp1210lb9fr-fr.pdf', '/downloads/datasheets/fr/q-pall-qp1210lb9fr-fr.pdf'),
    ('/it/pallet-in-plastica/1200-x-1000-mm/pallet-in-plastica-1200-x-1000-x-150-piano-aperto-9-piedi-light-n-qp1210lb9fr/', '/it/pallet-in-plastica/1200-x-1000-mm/pallet-in-plastica-1200-x-1000-x-150-piano-aperto-9-piedi-light/'),
    ('/downloads/datasheets/it/q-pall-n-qp1210lb9fr-it.pdf', '/downloads/datasheets/it/q-pall-qp1210lb9fr-it.pdf'),
    ('/es/palets-de-plastico/1200-x-1000-mm/palet-de-plastico-1200-x-1000-x-150-superficie-abierta-9-pies-light-n-qp1210lb9fr/', '/es/palets-de-plastico/1200-x-1000-mm/palet-de-plastico-1200-x-1000-x-150-superficie-abierta-9-pies-light/'),
    ('/downloads/datasheets/es/q-pall-n-qp1210lb9fr-es.pdf', '/downloads/datasheets/es/q-pall-qp1210lb9fr-es.pdf'),
    ('/kunststof-pallets/1200-x-1000-mm/kunststof-pallet-1200-x-1000-x-150-open-dek-3-onderlatten-light-n-qp1210lb3rr/', '/kunststof-pallets/1200-x-1000-mm/kunststof-pallet-1200-x-1000-x-150-open-dek-3-onderlatten-light/'),
    ('/downloads/datasheets/nl/q-pall-n-qp1210lb3rr-nl.pdf', '/downloads/datasheets/nl/q-pall-qp1210lb3rr-nl.pdf'),
    ('/en/plastic-pallets/1200-x-1000-mm/plastic-pallet-1200-x-1000-x-150-open-deck-3-runners-light-n-qp1210lb3rr/', '/en/plastic-pallets/1200-x-1000-mm/plastic-pallet-1200-x-1000-x-150-open-deck-3-runners-light/'),
    ('/downloads/datasheets/en/q-pall-n-qp1210lb3rr-en.pdf', '/downloads/datasheets/en/q-pall-qp1210lb3rr-en.pdf'),
    ('/de/kunststoffpaletten/1200-x-1000-mm/kunststoffpalette-1200-x-1000-x-150-offenes-deck-3-kufen-light-n-qp1210lb3rr/', '/de/kunststoffpaletten/1200-x-1000-mm/kunststoffpalette-1200-x-1000-x-150-offenes-deck-3-kufen-light/'),
    ('/downloads/datasheets/de/q-pall-n-qp1210lb3rr-de.pdf', '/downloads/datasheets/de/q-pall-qp1210lb3rr-de.pdf'),
    ('/fr/palettes-plastique/1200-x-1000-mm/palette-plastique-1200-x-1000-x-150-plateau-ajoure-3-semelles-light-n-qp1210lb3rr/', '/fr/palettes-plastique/1200-x-1000-mm/palette-plastique-1200-x-1000-x-150-plateau-ajoure-3-semelles-light/'),
    ('/downloads/datasheets/fr/q-pall-n-qp1210lb3rr-fr.pdf', '/downloads/datasheets/fr/q-pall-qp1210lb3rr-fr.pdf'),
    ('/it/pallet-in-plastica/1200-x-1000-mm/pallet-in-plastica-1200-x-1000-x-150-piano-aperto-3-slitte-light-n-qp1210lb3rr/', '/it/pallet-in-plastica/1200-x-1000-mm/pallet-in-plastica-1200-x-1000-x-150-piano-aperto-3-slitte-light/'),
    ('/downloads/datasheets/it/q-pall-n-qp1210lb3rr-it.pdf', '/downloads/datasheets/it/q-pall-qp1210lb3rr-it.pdf'),
    ('/es/palets-de-plastico/1200-x-1000-mm/palet-de-plastico-1200-x-1000-x-150-superficie-abierta-3-patines-light-n-qp1210lb3rr/', '/es/palets-de-plastico/1200-x-1000-mm/palet-de-plastico-1200-x-1000-x-150-superficie-abierta-3-patines-light/'),
    ('/downloads/datasheets/es/q-pall-n-qp1210lb3rr-es.pdf', '/downloads/datasheets/es/q-pall-qp1210lb3rr-es.pdf'),
    ('/kunststof-pallets/1200-x-1000-mm/kunststof-pallet-1200-x-1000-x-150-gesloten-dek-9-pootjes-light-n-qp1210lb9fr-cd/', '/kunststof-pallets/1200-x-1000-mm/kunststof-pallet-1200-x-1000-x-150-gesloten-dek-9-pootjes-light/'),
    ('/downloads/datasheets/nl/q-pall-n-qp1210lb9fr-cd-nl.pdf', '/downloads/datasheets/nl/q-pall-qp1210lb9fr-cd-nl.pdf'),
    ('/en/plastic-pallets/1200-x-1000-mm/plastic-pallet-1200-x-1000-x-150-closed-deck-9-feet-light-n-qp1210lb9fr-cd/', '/en/plastic-pallets/1200-x-1000-mm/plastic-pallet-1200-x-1000-x-150-closed-deck-9-feet-light/'),
    ('/downloads/datasheets/en/q-pall-n-qp1210lb9fr-cd-en.pdf', '/downloads/datasheets/en/q-pall-qp1210lb9fr-cd-en.pdf'),
    ('/de/kunststoffpaletten/1200-x-1000-mm/kunststoffpalette-1200-x-1000-x-150-geschlossenes-deck-9-fusse-light-n-qp1210lb9fr-cd/', '/de/kunststoffpaletten/1200-x-1000-mm/kunststoffpalette-1200-x-1000-x-150-geschlossenes-deck-9-fusse-light/'),
    ('/downloads/datasheets/de/q-pall-n-qp1210lb9fr-cd-de.pdf', '/downloads/datasheets/de/q-pall-qp1210lb9fr-cd-de.pdf'),
    ('/fr/palettes-plastique/1200-x-1000-mm/palette-plastique-1200-x-1000-x-150-plateau-ferme-9-pieds-light-n-qp1210lb9fr-cd/', '/fr/palettes-plastique/1200-x-1000-mm/palette-plastique-1200-x-1000-x-150-plateau-ferme-9-pieds-light/'),
    ('/downloads/datasheets/fr/q-pall-n-qp1210lb9fr-cd-fr.pdf', '/downloads/datasheets/fr/q-pall-qp1210lb9fr-cd-fr.pdf'),
    ('/it/pallet-in-plastica/1200-x-1000-mm/pallet-in-plastica-1200-x-1000-x-150-piano-chiuso-9-piedi-light-n-qp1210lb9fr-cd/', '/it/pallet-in-plastica/1200-x-1000-mm/pallet-in-plastica-1200-x-1000-x-150-piano-chiuso-9-piedi-light/'),
    ('/downloads/datasheets/it/q-pall-n-qp1210lb9fr-cd-it.pdf', '/downloads/datasheets/it/q-pall-qp1210lb9fr-cd-it.pdf'),
    ('/es/palets-de-plastico/1200-x-1000-mm/palet-de-plastico-1200-x-1000-x-150-superficie-cerrada-9-pies-light-n-qp1210lb9fr-cd/', '/es/palets-de-plastico/1200-x-1000-mm/palet-de-plastico-1200-x-1000-x-150-superficie-cerrada-9-pies-light/'),
    ('/downloads/datasheets/es/q-pall-n-qp1210lb9fr-cd-es.pdf', '/downloads/datasheets/es/q-pall-qp1210lb9fr-cd-es.pdf'),
    # update 15: QPW1210HP5RR-CDG van de site (Noah 27-10-2026) -> QPW1210HP5RR-CD
    ('/kunststof-pallets/1200-x-1000-mm/cleanroompallet-1200-x-1000-x-160-gesloten-dek-5-onderlatten-heavy-qpw1210hp5rr-cdg/', '/kunststof-pallets/1200-x-1000-mm/cleanroompallet-1200-x-1000-x-160-gesloten-dek-5-onderlatten-heavy/'),
    ('/downloads/datasheets/nl/q-pall-qpw1210hp5rr-cdg-nl.pdf', '/downloads/datasheets/nl/q-pall-qpw1210hp5rr-cd-nl.pdf'),
    ('/en/plastic-pallets/1200-x-1000-mm/cleanroom-pallet-1200-x-1000-x-160-closed-deck-5-runners-heavy-qpw1210hp5rr-cdg/', '/en/plastic-pallets/1200-x-1000-mm/cleanroom-pallet-1200-x-1000-x-160-closed-deck-5-runners-heavy/'),
    ('/downloads/datasheets/en/q-pall-qpw1210hp5rr-cdg-en.pdf', '/downloads/datasheets/en/q-pall-qpw1210hp5rr-cd-en.pdf'),
    ('/de/kunststoffpaletten/1200-x-1000-mm/reinraumpalette-1200-x-1000-x-160-geschlossenes-deck-5-kufen-heavy-qpw1210hp5rr-cdg/', '/de/kunststoffpaletten/1200-x-1000-mm/reinraumpalette-1200-x-1000-x-160-geschlossenes-deck-5-kufen-heavy/'),
    ('/downloads/datasheets/de/q-pall-qpw1210hp5rr-cdg-de.pdf', '/downloads/datasheets/de/q-pall-qpw1210hp5rr-cd-de.pdf'),
    ('/fr/palettes-plastique/1200-x-1000-mm/palette-salle-blanche-1200-x-1000-x-160-plateau-ferme-5-semelles-heavy-qpw1210hp5rr-cdg/', '/fr/palettes-plastique/1200-x-1000-mm/palette-salle-blanche-1200-x-1000-x-160-plateau-ferme-5-semelles-heavy/'),
    ('/downloads/datasheets/fr/q-pall-qpw1210hp5rr-cdg-fr.pdf', '/downloads/datasheets/fr/q-pall-qpw1210hp5rr-cd-fr.pdf'),
    ('/it/pallet-in-plastica/1200-x-1000-mm/pallet-per-camera-bianca-1200-x-1000-x-160-piano-chiuso-5-slitte-heavy-qpw1210hp5rr-cdg/', '/it/pallet-in-plastica/1200-x-1000-mm/pallet-per-camera-bianca-1200-x-1000-x-160-piano-chiuso-5-slitte-heavy/'),
    ('/downloads/datasheets/it/q-pall-qpw1210hp5rr-cdg-it.pdf', '/downloads/datasheets/it/q-pall-qpw1210hp5rr-cd-it.pdf'),
    ('/es/palets-de-plastico/1200-x-1000-mm/palet-para-sala-blanca-1200-x-1000-x-160-superficie-cerrada-5-patines-heavy-qpw1210hp5rr-cdg/', '/es/palets-de-plastico/1200-x-1000-mm/palet-para-sala-blanca-1200-x-1000-x-160-superficie-cerrada-5-patines-heavy/'),
    ('/downloads/datasheets/es/q-pall-qpw1210hp5rr-cdg-es.pdf', '/downloads/datasheets/es/q-pall-qpw1210hp5rr-cd-es.pdf'),
    # update 14: QP76114LB9RR(-CD) removed (not on qpall.com, no mould number) -> QP76114LB3RR(-CD), pages and datasheets
    ('/kunststof-pallets/760-x-1140-mm/kunststof-pallet-760-x-1140-x-158-open-dek-3-onderlatten-light/', '/kunststof-pallets/760-x-1140-mm/kunststof-pallet-1140-x-760-x-158-open-dek-3-onderlatten-light/'), ('/kunststof-pallets/760-x-1140-mm/kunststof-pallet-760-x-1140-x-158-gesloten-dek-3-onderlatten-light/', '/kunststof-pallets/760-x-1140-mm/kunststof-pallet-1140-x-760-x-150-gesloten-dek-3-onderlatten-light/'),
    ('/downloads/datasheets/nl/q-pall-qp76114lb9rr-nl.pdf', '/downloads/datasheets/nl/q-pall-qp76114lb3rr-nl.pdf'), ('/downloads/datasheets/nl/q-pall-qp76114lb9rr-cd-nl.pdf', '/downloads/datasheets/nl/q-pall-qp76114lb3rr-cd-nl.pdf'),
    ('/en/plastic-pallets/760-x-1140-mm/plastic-pallet-760-x-1140-x-158-open-deck-3-runners-light/', '/en/plastic-pallets/760-x-1140-mm/plastic-pallet-1140-x-760-x-158-open-deck-3-runners-light/'), ('/en/plastic-pallets/760-x-1140-mm/plastic-pallet-760-x-1140-x-158-closed-deck-3-runners-light/', '/en/plastic-pallets/760-x-1140-mm/plastic-pallet-1140-x-760-x-150-closed-deck-3-runners-light/'),
    ('/downloads/datasheets/en/q-pall-qp76114lb9rr-en.pdf', '/downloads/datasheets/en/q-pall-qp76114lb3rr-en.pdf'), ('/downloads/datasheets/en/q-pall-qp76114lb9rr-cd-en.pdf', '/downloads/datasheets/en/q-pall-qp76114lb3rr-cd-en.pdf'),
    ('/de/kunststoffpaletten/760-x-1140-mm/kunststoffpalette-760-x-1140-x-158-offenes-deck-3-kufen-light/', '/de/kunststoffpaletten/760-x-1140-mm/kunststoffpalette-1140-x-760-x-158-offenes-deck-3-kufen-light/'), ('/de/kunststoffpaletten/760-x-1140-mm/kunststoffpalette-760-x-1140-x-158-geschlossenes-deck-3-kufen-light/', '/de/kunststoffpaletten/760-x-1140-mm/kunststoffpalette-1140-x-760-x-150-geschlossenes-deck-3-kufen-light/'),
    ('/downloads/datasheets/de/q-pall-qp76114lb9rr-de.pdf', '/downloads/datasheets/de/q-pall-qp76114lb3rr-de.pdf'), ('/downloads/datasheets/de/q-pall-qp76114lb9rr-cd-de.pdf', '/downloads/datasheets/de/q-pall-qp76114lb3rr-cd-de.pdf'),
    ('/fr/palettes-plastique/760-x-1140-mm/palette-plastique-760-x-1140-x-158-plateau-ajoure-3-semelles-light/', '/fr/palettes-plastique/760-x-1140-mm/palette-plastique-1140-x-760-x-158-plateau-ajoure-3-semelles-light/'), ('/fr/palettes-plastique/760-x-1140-mm/palette-plastique-760-x-1140-x-158-plateau-ferme-3-semelles-light/', '/fr/palettes-plastique/760-x-1140-mm/palette-plastique-1140-x-760-x-150-plateau-ferme-3-semelles-light/'),
    ('/downloads/datasheets/fr/q-pall-qp76114lb9rr-fr.pdf', '/downloads/datasheets/fr/q-pall-qp76114lb3rr-fr.pdf'), ('/downloads/datasheets/fr/q-pall-qp76114lb9rr-cd-fr.pdf', '/downloads/datasheets/fr/q-pall-qp76114lb3rr-cd-fr.pdf'),
    ('/it/pallet-in-plastica/760-x-1140-mm/pallet-in-plastica-760-x-1140-x-158-piano-aperto-3-slitte-light/', '/it/pallet-in-plastica/760-x-1140-mm/pallet-in-plastica-1140-x-760-x-158-piano-aperto-3-slitte-light/'), ('/it/pallet-in-plastica/760-x-1140-mm/pallet-in-plastica-760-x-1140-x-158-piano-chiuso-3-slitte-light/', '/it/pallet-in-plastica/760-x-1140-mm/pallet-in-plastica-1140-x-760-x-150-piano-chiuso-3-slitte-light/'),
    ('/downloads/datasheets/it/q-pall-qp76114lb9rr-it.pdf', '/downloads/datasheets/it/q-pall-qp76114lb3rr-it.pdf'), ('/downloads/datasheets/it/q-pall-qp76114lb9rr-cd-it.pdf', '/downloads/datasheets/it/q-pall-qp76114lb3rr-cd-it.pdf'),
    ('/es/palets-de-plastico/760-x-1140-mm/palet-de-plastico-760-x-1140-x-158-superficie-abierta-3-patines-light/', '/es/palets-de-plastico/760-x-1140-mm/palet-de-plastico-1140-x-760-x-158-superficie-abierta-3-patines-light/'), ('/es/palets-de-plastico/760-x-1140-mm/palet-de-plastico-760-x-1140-x-158-superficie-cerrada-3-patines-light/', '/es/palets-de-plastico/760-x-1140-mm/palet-de-plastico-1140-x-760-x-150-superficie-cerrada-3-patines-light/'),
    ('/downloads/datasheets/es/q-pall-qp76114lb9rr-es.pdf', '/downloads/datasheets/es/q-pall-qp76114lb3rr-es.pdf'), ('/downloads/datasheets/es/q-pall-qp76114lb9rr-cd-es.pdf', '/downloads/datasheets/es/q-pall-qp76114lb3rr-cd-es.pdf'),
    ('/prijsaanvraag', '/offerte-aanvraag/'),
    ('/en/quotation-request', '/en/request-for-quotation/'),
    ('/kunststof-pallets/europallets', '/kunststof-pallets/1200-x-800-mm/'),
    ('/en/vacancies', '/en/careers/'),
    ('/en/contact', '/en/get-in-touch/'),
    ('/beurzen', '/over-q-pall/'),
    ('/en/trade-fairs', '/en/about-q-pall/'),
    ('/downloads/q-pall-productcatalogus-2026-en.pdf', '/downloads/q-pall-product-catalogue-2026-en.pdf'),
]
