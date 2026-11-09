// Local test of the confirmation e-mail (update 37): runs the Netlify function with example submissions in six
// languages, without sending anything (fetch is replaced). Writes the e-mails as HTML files to look at.
//   node tools/mail_test.js <site dir> <out dir> [base url]
const path = require('path'), fs = require('fs');
const [site, outDir, base] = process.argv.slice(2);
const fn = require(path.resolve(site, 'netlify/functions/submission-created/submission-created.js'));
fs.mkdirSync(outDir, { recursive: true });
const EX = {
  nl: { naam: 'Jan de Vries', bedrijf: 'De Vries Logistiek B.V.', land: 'Nederland', postcode: '3011 AB', plaats: 'Rotterdam', bericht: 'Graag ook een prijs bij afname per kwartaal.' },
  en: { naam: 'James Carter', bedrijf: 'Carter Distribution Ltd', land: 'United Kingdom', postcode: 'LS1 4AP', plaats: 'Leeds', bericht: 'Could you also quote for quarterly deliveries?' },
  de: { naam: 'Anna Becker', bedrijf: 'Becker Logistik GmbH', land: 'Deutschland', postcode: '40210', plaats: 'Düsseldorf', bericht: 'Bitte auch einen Preis für eine vierteljährliche Abnahme.' },
  fr: { naam: 'Julien Moreau', bedrijf: 'Moreau Logistique SAS', land: 'France', postcode: '69002', plaats: 'Lyon', bericht: 'Merci de chiffrer également une livraison trimestrielle.' },
  it: { naam: 'Marco Rossi', bedrijf: 'Rossi Logistica S.r.l.', land: 'Italia', postcode: '20121', plaats: 'Milano', bericht: 'Vorremmo anche un prezzo per forniture trimestrali.' },
  es: { naam: 'Lucía García', bedrijf: 'García Logística S.L.', land: 'España', postcode: '28001', plaats: 'Madrid', bericht: 'Por favor, incluyan también un precio para entregas trimestrales.' },
};
const products = '1. QP1208LB3RR – Kunststof pallet 1200 x 800 x 150 open dek 3 onderlatten light – 450 pallets\n' +
                 '2. QP1210LB9FR – Kunststof pallet 1200 x 1000 x 150 open dek 9 pootjes light – 90 pallets\n' +
                 '3. QPHKVOUWR1208-6 – Kunststof palletrand 1200 x 800 x 200 mm – 40 stuks';
const sent = [];
global.fetch = async (url, opt) => { sent.push(JSON.parse(opt.body)); return { ok: true, status: 201, text: async () => '{"messageId":"<test@brevo>"}' }; };
process.env.BREVO_API_KEY = 'test-only';
process.env.URL = base || 'https://staging.qpall.com';
(async () => {
  for (const [lang, c] of Object.entries(EX)) {
    const data = Object.assign({ taal: lang, email: c.naam.split(' ')[0].toLowerCase().normalize('NFD').replace(/[^a-z]/g, '') + '@example.com',
      producten: products, transport: 'Bezorgen door Q-Pall', leverdatum: '2026-11-16', frequentie: 'Regelmatig', akkoord: 'ja' }, c);
    const r = await fn.handler({ body: JSON.stringify({ payload: { form_name: 'offerte', data } }) });
    const m = sent[sent.length - 1];
    fs.writeFileSync(path.join(outDir, `quote-${lang}.html`), m.htmlContent);
    fs.writeFileSync(path.join(outDir, `quote-${lang}.txt`), m.textContent);
    console.log(lang, r.statusCode, '|', m.subject, '|', m.to[0].email, '|', m.htmlContent.length, 'chars');
  }
  // own transport (collection), no name, no message, free-text product, Ultra line
  await fn.handler({ body: JSON.stringify({ payload: { form_name: 'offerte', data: { taal: 'de', email: 'test@example.com', naam: '', bedrijf: 'Test GmbH',
    producten: '1. QP1210H – Ultra pallet – 34 pallets\n2. Eigen maat 1150 x 950 – 200 pallets', transport: 'Zelf transport regelen (ophalen)', land: 'Deutschland', leverdatum: '2026-12-01' } } }) });
  fs.writeFileSync(path.join(outDir, 'quote-de-ophalen.html'), sent[sent.length - 1].htmlContent);
  // language from the page address when the field is missing; other forms and bad addresses are skipped
  await fn.handler({ body: JSON.stringify({ payload: { form_name: 'offerte', data: { email: 'x@example.com', naam: 'X Y', producten: '1. QP1208LB3RR – x – 15 pallets', referrer: 'https://qpall.com/fr/demande-de-devis/' } } }) });
  console.log('referrer ->', sent[sent.length - 1].subject);
  const before = sent.length;
  console.log('contact form:', (await fn.handler({ body: JSON.stringify({ payload: { form_name: 'contact', data: { email: 'a@example.com' } } }) })).body,
              '| bad address:', (await fn.handler({ body: JSON.stringify({ payload: { form_name: 'offerte', data: { email: 'nope' } } }) })).body,
              '| sent extra:', sent.length - before);
  delete process.env.BREVO_API_KEY;
  console.log('without key:', (await fn.handler({ body: JSON.stringify({ payload: { form_name: 'offerte', data: { email: 'a@example.com' } } }) })).body);
})();
