# Translation brief: Q-Pall website EN → DE / FR / IT / ES

Q-Pall (Veghel, the Netherlands) manufactures plastic pallets from nearly 100% recycled plastic in five European factories (Balk NL, Ribe DK, Marktoberdorf DE, Nantes FR, Lleida ES; head office and storage in Veghel). The site targets B2B buyers: procurement, logistics and warehouse managers, quality managers.

Project root: `/home/claude/qpall/bron`

- **Source**: `content/en/<file>.md` (primary). The Dutch original `content/nl/<file>.md` is the reference when the English is ambiguous.
- **Target**: `content/<lang>/<file>.md`, same file name.
- **UI strings**: `i18n/en.json` → `i18n/<lang>.json` (same keys, translated values).

Write every file with the Write tool (not with shell heredocs). Write natural, idiomatic copy for a native B2B reader in that market. This is localisation, not word-for-word translation, but **do not add or drop facts, numbers, claims or sections**.

## Format rules (critical, the build parses these files)

1. Each file = YAML frontmatter between `---` lines, then a Markdown body. Keep every frontmatter key EXACTLY (no renaming, adding or dropping). Translate string VALUES only.
2. Never change these values: `id`, `recommend`, `reading`, `noindex`, `published`, `updated`, `icon`, timeline years `y`, and mapping keys such as `chemical:` / `food:` under `tiles`.
3. Put every translated string value in **double quotes**. Never put a raw `"` inside a value: use the typographic quotes of the language („…“ DE, « … » FR, «…» IT, «…» ES). Use the typographic apostrophe ’ (l’industrie, dell’azienda) everywhere.
4. Link syntax `[anchor text](@page-id)` and `(@p:model-id)`: translate the anchor text, keep the `(@...)` target EXACTLY. External `https://` links stay unchanged.
5. Placeholders in double square brackets (`[[count]]`, `[[price_from]]`, `[[pricetable]]`, `[[sizetable]]`, `[[dealermap]]`, `[[termsdownload]]`, `[[factories]]`, `[[price:size=1200x800,class=light]]` …) stay EXACTLY as they are, in a sensible position in the sentence.
6. Keep the Markdown structure: same headings (`##`, `###`), lists, tables (same columns/rows), bold `**...**`. In `h1`, `hero.h1` and the `title` fields of home.md sections keep the `**...**` emphasis around the corresponding words (shown heavier on the page). Keep lists (e.g. `strike`, `docs`, `bullets`, `steps`, `faq`, `timeline`) the same length.
7. `title` (SEO title): **max 60 characters**, no `|`. Pattern: "… – Q-Pall" (en dash with spaces); drop " – Q-Pall" if it would exceed 60. Put the main keyword first.
8. `description` (meta description): **120–156 characters**. Contains the language’s main keyword where natural.
9. Validate after each batch: `python3 tools/check_translation.py <lang> <file.md ...>` (and `python3 tools/check_translation.py <lang> --i18n` for the JSON). Fix until clean. Finish with a run over all your files and report the output.

## Numbers and units

- Thousands separator is a **period** in all languages (client house style): `7.500 kg`, `1.750 kg`, `34.500 t`.
- Decimals use a **comma**: `2,7 kg`, `13,6 m`, `5,1 kg`.
- Prices: DE `ab 6,10 €`, FR `à partir de 6,10 €`, IT `da € 6,10`, ES `desde 6,10 €`. VAT: DE `zzgl. MwSt.`, FR `HT`, IT `IVA esclusa`, ES `IVA no incluido`.
- Dimensions stay `1200 x 800 mm`. "4 million" → `4 Mio.` (DE), `4 millions` (FR), `4 milioni` (IT), `4 millones` (ES).
- Dates: write them the local way (DE 12. August 2026, FR 12 août 2026, IT 12 agosto 2026, ES 12 de agosto de 2026).

## Never translate

Q-Pall, Q-PALL BV, Q-Used, Ultra pallet (DE Ultra-Palette is fine), AVK Group, Anker Pallets, #yourbestpal, “pallets with a purpose” (keep English as slogan), “Act global, produce local” (keep English), EcoVadis, HACCP, GMP, ISPM 15, IPPC, PPWR, EU 2025/40, AGV, TPE, HDPE, PP, CP1–CP9, H1, EPAL, ISO 6780, SimplyBook, Mach3, place names (Veghel, Balk, Ribe, Marktoberdorf, Nantes, Lleida, Chesterfield, Aigrefeuille-sur-Maine, Les Borges Blanques…). The load classes **Light, Medium, Heavy** are product class names: keep them in English, capitalised as labels (“Medium-Palette”, “palette Medium”, “pallet Medium”, “palet Medium”).

## Tone per language

- **DE** (Germany, Austria, Switzerland): formal “Sie”. Nouns compounded correctly (Kunststoffpalette, Palettenregal). Main keyword: **Kunststoffpaletten**.
- **FR** (France, Belgium): “vous”. Non-breaking-space rules are not needed. Main keyword: **palettes plastique** (also “palettes en plastique” in running text).
- **IT**: address the reader with the polite plural “voi” in running text (potete, contattateci); short buttons/labels may use the usual imperative (Richiedi un preventivo, Scarica il catalogo). “pallet” is invariable (i pallet). Main keyword: **pallet in plastica**.
- **ES** (Spain): “usted”. Use **palet / palets** (not palé). Main keyword: **palets de plástico**.

## Glossary (use consistently, also in i18n JSON)

| English | DE | FR | IT | ES |
|---|---|---|---|---|
| plastic pallet(s) | Kunststoffpalette(n) | palette(s) plastique | pallet in plastica | palet(s) de plástico |
| runners / 3 runners | Kufen / 3 Kufen | semelles / 3 semelles | slitte / 3 slitte | patines / 3 patines |
| feet / 9 feet | Füße / 9 Füße | pieds / 9 pieds | piedi / 9 piedi | pies / 9 pies |
| open deck / closed deck | offenes / geschlossenes Deck | plateau ajouré / fermé | piano aperto / chiuso | superficie abierta / cerrada |
| top deck | Oberdeck | plateau supérieur | piano superiore | superficie superior |
| static load | statische Belastung | charge statique | portata statica | carga estática |
| dynamic load | dynamische Belastung | charge dynamique | portata dinamica | carga dinámica |
| racking load / in racking | Regalbelastung / im Regal | charge en rayonnage / en rayonnage | portata su scaffale / su scaffale | carga en estantería / en estantería |
| pallet racking | Palettenregal | rayonnage à palettes | scaffalatura porta-pallet | estantería para palets |
| load capacity | Tragfähigkeit | capacité de charge | portata | capacidad de carga |
| load class | Lastklasse | classe de charge | classe di portata | clase de carga |
| nestable | nestbar | emboîtable | incastrabile | encajable |
| Euro pallet | Europalette | palette Europe | europallet | europalet |
| half / quarter Euro pallet | Halbpalette / Viertelpalette | demi-palette / quart de palette | mezzo pallet / quarto di pallet | medio palet / cuarto de palet |
| industrial pallet | Industriepalette | palette industrielle | pallet industriale | palet industrial |
| block pallet | Blockpalette | palette à blocs | pallet a blocchi | palet de bloques |
| display pallet | Displaypalette | palette display | pallet espositore | palet expositor |
| export pallet | Exportpalette | palette export | pallet da esportazione | palet de exportación |
| hygienic pallet | Hygienepalette | palette hygiénique | pallet igienico | palet higiénico |
| cleanroom pallet | Reinraumpalette | palette salle blanche | pallet per camera bianca | palet para sala blanca |
| pool pallet / pooling | Poolpalette / Pooling | palette de pooling / pooling | pallet per pooling / pooling | palet para pooling / pooling |
| anti-slip | Antirutsch- | antidérapant | antiscivolo | antideslizante |
| pallet collar | Palettenaufsatzrahmen | rehausse de palette | sponda per pallet | collarín para palet |
| lid | Deckel | couvercle | coperchio | tapa |
| drip tray | Auffangwanne | bac de rétention | vasca di raccolta | cubeto de retención |
| grating (galvanised) | Gitterrost (verzinkt) | caillebotis (galvanisé) | grigliato (zincato) | rejilla (galvanizada) |
| plastic grid | Kunststoffgitter | grille plastique | griglia in plastica | rejilla de plástico |
| click-on runners | Klick-Kufen | semelles clipsables | slitte a incastro | patines de clic |
| freezer spacer | Gefrier-Abstandshalter | espaceur de congélation | distanziatore per congelamento | separador de congelación |
| from-price | Ab-Preis | prix de départ | prezzo di partenza | precio desde |
| quote / request a quote | Angebot / Angebot anfordern | devis / demander un devis | preventivo / richiedere un preventivo | presupuesto / solicitar presupuesto |
| forklift / pallet truck | Gabelstapler / Hubwagen | chariot élévateur / transpalette | carrello elevatore / transpallet | carretilla elevadora / transpaleta |
| roller conveyor | Rollenbahn | convoyeur à rouleaux | rulliera | transportador de rodillos |
| block stacking | Blockstapelung | gerbage | stoccaggio a catasta | apilado en bloque |
| recycled plastic | recycelter Kunststoff (Rezyklat) | plastique recyclé | plastica riciclata | plástico reciclado |
| virgin plastic | Neuware | plastique vierge | plastica vergine | plástico virgen |
| injection moulding | Spritzguss | moulage par injection | stampaggio a iniezione | moldeo por inyección |
| mould | Werkzeug (Form) | moule | stampo | molde |
| technical datasheet | technisches Datenblatt | fiche technique | scheda tecnica | ficha técnica |
| product catalogue | Produktkatalog | catalogue produits | catalogo prodotti | catálogo de productos |
| declaration of conformity | Konformitätserklärung | déclaration de conformité | dichiarazione di conformità | declaración de conformidad |
| head office | Hauptsitz | siège | sede centrale | sede central |
| working day | Werktag | jour ouvré | giorno lavorativo | día laborable |
| GDPR | DSGVO | RGPD | GDPR | RGPD |
| the Netherlands / Denmark / Germany / France / Spain / United Kingdom | Niederlande / Dänemark / Deutschland / Frankreich / Spanien / Vereinigtes Königreich | Pays-Bas / Danemark / Allemagne / France / Espagne / Royaume-Uni | Paesi Bassi / Danimarca / Germania / Francia / Spagna / Regno Unito | Países Bajos / Dinamarca / Alemania / Francia / España / Reino Unido |
| food / beverage / pharmaceutical / chemical industry | Lebensmittel- / Getränke- / Pharma- / Chemieindustrie | industrie agroalimentaire / des boissons / pharmaceutique / chimique | industria alimentare / delle bevande / farmaceutica / chimica | industria alimentaria / de bebidas / farmacéutica / química |
| retail / logistics | Handel / Logistik | grande distribution / logistique | grande distribuzione / logistica | distribución / logística |

## i18n JSON specifics

- Same keys and nesting as `en.json`; arrays the same length. Translate values only; keep `{placeholders}` such as `{size}`, `{n}`, `{doc}`, `{name}` exactly.
- `lang_name`: the language’s own name (Deutsch, Français, Italiano, Español).
- `catalog_meta` = "PDF, {size}, <this language’s name>"; `dl_ppwr_meta`: the declarations are only available in English, so write the word for “English” in the target language (Englisch / anglais / inglese / inglés).
- `months`: local month names. `anchor` values are URL fragments: translate to short lowercase ASCII slugs with hyphens (e.g. DE `beschreibung`, `technische-daten`).
- Values that are names (Light, Medium, Heavy, Q-Pall, PPWR, EcoVadis…) stay as they are.
- Keep UI labels short: they sit in buttons, chips, table headers and menus.
