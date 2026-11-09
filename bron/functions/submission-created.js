// Netlify function "submission-created" (update 37): Netlify runs it after every verified form submission.
// For the quote form ("offerte") it sends the customer a confirmation e-mail in the language of the form, through the
// Brevo API. The design and texts come from the build (quote-mail.json, made by bron/mailgen.py from the website texts).
//
// Settings (Netlify > Site configuration > Environment variables):
//   BREVO_API_KEY   required. Without it nothing is sent (the submission itself still arrives in Netlify as before).
//   MAIL_FROM       sender address, default info@qpall.com (must be a verified sender/domain in Brevo)
//   MAIL_FROM_NAME  sender name, default Q-Pall
//   MAIL_REPLY_TO   address the customer's reply goes to, default info@qpall.com
//   MAIL_BCC        optional: a copy of every confirmation (for example to sales)
//   MAIL_BASE_URL   optional: site address for links and images; default the site's own address (Netlify URL)
'use strict';
const MAIL = require('./quote-mail.json');

const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fill = (tpl, map) => tpl.replace(/\[\[([A-Z0-9_]+)\]\]/g, (m, k) => (k in map ? map[k] : m));
const clean = (s, max) => String(s || '').replace(/\r\n?/g, '\n').trim().slice(0, max || 200);
const EMAIL_RE = /^[^\s@<>"]+@[^\s@<>"]+\.[a-z]{2,}$/i;

// one line of the form field "producten": "1. QP1208LB3RR – Kunststof pallet ... – 450 pallets" (names in Dutch, for sales)
function parseLine(line) {
  const m = line.match(/^\s*\d+\.\s*(.+?)(?:\s+–\s+(\d+)\s+(?:pallets?|stuks?))?\s*$/i);
  if (!m) return null;
  const first = m[1].split(' – ')[0].trim();
  return { sku: first.toUpperCase(), raw: m[1].trim(), qty: m[2] ? parseInt(m[2], 10) : 0 };
}

function build(lang, data, base) {
  const L = MAIL[lang], F = L.frag;
  const nf = new Intl.NumberFormat(L.locale);
  const name = clean(data.naam, 120), first = name.split(/\s+/)[0] || '';
  const tr = L.transport[clean(data.transport)] || null, self = tr && tr[1] === 'self';

  // products
  const items = String(data.producten || '').split('\n').map(parseLine).filter(Boolean).slice(0, 20).map((p) => {
    const o = L.products[p.sku];
    const it = { sku: o ? p.sku : '', name: o ? o.n : p.raw, url: o && o.u ? base + o.u : '', img: o && o.i ? base + o.i : '', qty: '', stacks: '' };
    if (p.qty) {
      if (o && o.a) it.qty = nf.format(p.qty) + ' ' + (p.qty === 1 ? L.units.pcs_1 : L.units.pcs);
      else {
        it.qty = nf.format(p.qty) + ' ' + L.units.pallets;
        const per = o ? o.s : 0, n = per > 1 ? p.qty / per : 0;
        if (n && Number.isInteger(n)) it.stacks = (n === 1 ? L.units.stack_1 : L.units.stack_n).replace('{n}', nf.format(n)).replace('{per}', nf.format(per));
      }
    }
    return it;
  });
  const rows = items.map((it) => fill(F.row, {
    THUMB: it.img ? fill(F.thumb, { SRC: esc(it.img) }) : F.thumb_empty,
    NAME: it.url ? fill(F.name_link, { URL: esc(it.url), TEXT: esc(it.name) }) : fill(F.name_plain, { TEXT: esc(it.name) }),
    SKU: it.sku ? fill(F.sku, { TEXT: esc(it.sku) }) : '',
    QTY: esc(it.qty), STACKS: it.stacks ? fill(F.stacks, { TEXT: esc(it.stacks) }) : '',
  })).join('');

  // details: only what the customer filled in
  let date = clean(data.leverdatum, 20);
  if (/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    date = new Intl.DateTimeFormat(L.locale, { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(date + 'T12:00:00Z'));
  }
  const facts = [
    ['company', clean(data.bedrijf)],
    ['transport', tr ? tr[0] : clean(data.transport)],
    ['country', self ? '' : clean(data.land)],
    ['zip', self ? '' : [clean(data.postcode, 20), clean(data.plaats, 80)].filter(Boolean).join(' ')],
    [self ? 'date_self' : 'date', date],
    ['freq', L.freq[clean(data.frequentie)] || clean(data.frequentie)],
    ['email', clean(data.email)],
  ].filter((f) => f[1]);
  const message = clean(data.bericht, 2000);

  const html = fill(L.html, {
    BASE: base,
    H1: first ? fill(L.h1_named, { NAME: esc(first) }) : L.h1,
    PRODUCTS: rows ? F.products_open + rows + F.products_close : '',
    FACTS: F.facts_open + facts.map((f) => fill(F.facts[f[0]], { TEXT: esc(f[1]) })).join('') + F.facts_close,
    MESSAGE: message ? fill(F.message, { TEXT: esc(message).replace(/\n/g, '<br>') }) : '',
    STEPS: self ? F.steps_self : F.steps_deliver,
  });

  // plain-text version (mail programs that do not show HTML, and spam filters like it)
  const T = L.text, lines = [];
  lines.push(first ? T.h1_named.replace('{name}', first) : T.h1, '', T.lead, '', T.sum_h.toUpperCase());
  items.forEach((it) => lines.push('- ' + it.name + (it.sku ? ' (' + it.sku + ')' : '') + (it.qty ? ': ' + it.qty : '') + (it.stacks ? ', ' + it.stacks : '')));
  facts.forEach((f) => lines.push(T.labels[f[0]] + ': ' + f[1]));
  if (message) lines.push('', T.message + ':', message);
  lines.push('', T.change, '', T.next_h.toUpperCase());
  (self ? T.steps_self : T.steps_deliver).forEach((s) => lines.push(s[0] + ' - ' + s[1] + ': ' + s[2]));
  lines.push('', T.contact_h, T.contact_t, '+31 (0)413 353 111 | info@qpall.com', T.hours, '', T.regards, T.team, '', T.address, base.replace(/^https?:\/\//, ''), '', T.reason);

  return { subject: L.subject, html, text: lines.join('\n'), name };
}

exports.build = build;   // used by the local test (bron/tools/mail_test.js)

exports.handler = async (event) => {
  let payload;
  try { payload = JSON.parse(event.body).payload; } catch (e) { return { statusCode: 400, body: 'bad payload' }; }
  if (!payload || payload.form_name !== 'offerte') return { statusCode: 200, body: 'not a quote' };
  const data = payload.data || {};
  if (data['bot-field']) return { statusCode: 200, body: 'spam' };
  const to = clean(data.email, 200);
  if (!EMAIL_RE.test(to)) return { statusCode: 200, body: 'no valid e-mail address' };
  let lang = clean(data.taal, 5).toLowerCase();
  if (!MAIL[lang]) {   // older pages without the field: the language from the page address
    const m = String(data.referrer || '').match(/^https?:\/\/[^/]+\/(en|de|fr|it|es)\//);
    lang = m ? m[1] : 'nl';
  }
  const key = process.env.BREVO_API_KEY;
  if (!key) { console.log('BREVO_API_KEY not set: no confirmation sent'); return { statusCode: 200, body: 'no key' }; }

  const base = (process.env.MAIL_BASE_URL || process.env.URL || 'https://qpall.com').replace(/\/$/, '');
  const mail = build(lang, data, base);
  const body = {
    sender: { name: process.env.MAIL_FROM_NAME || 'Q-Pall', email: process.env.MAIL_FROM || 'info@qpall.com' },
    to: [{ email: to, name: mail.name || undefined }],
    replyTo: { email: process.env.MAIL_REPLY_TO || 'info@qpall.com', name: process.env.MAIL_FROM_NAME || 'Q-Pall' },
    subject: mail.subject, htmlContent: mail.html, textContent: mail.text, tags: ['offerte', 'offerte-' + lang],
  };
  if (process.env.MAIL_BCC) body.bcc = [{ email: process.env.MAIL_BCC }];
  try {
    const r = await fetch('https://api.brevo.com/v3/smtp/email', {
      method: 'POST', headers: { 'api-key': key, 'content-type': 'application/json', accept: 'application/json' }, body: JSON.stringify(body),
    });
    const res = await r.text();
    if (!r.ok) { console.error('Brevo', r.status, res); return { statusCode: 502, body: 'brevo error' }; }
    console.log('confirmation sent', lang, res);
  } catch (e) {
    console.error('Brevo request failed', e && e.message);
    return { statusCode: 502, body: 'brevo request failed' };
  }
  return { statusCode: 200, body: 'sent' };
};
