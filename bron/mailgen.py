"""Quote confirmation e-mail (update 37): templates for the Netlify function that sends it through Brevo.

build.py calls write() at the end of a build. For every language it renders mail/quote.j2 (the design chosen on
29 Oct 2026) with tokens for the parts that depend on the request, plus the small building blocks the function
repeats (product rows, detail rows), and writes everything to
    <site>/netlify/functions/submission-created/quote-mail.json
next to a copy of functions/submission-created.js. Netlify runs that function after every form submission; it fills
in the template in the language of the form (hidden field 'taal') and sends it with the Brevo API.
Texts come from the site itself (thank-you page content/<lang>/thanks-quote.md, i18n/<lang>.json) and mail/texts.json,
so the e-mail and the website say the same thing. Product names, links and photos come from the quote form's list."""
import json, os, re, shutil, html as H
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

ROOT = os.path.dirname(os.path.abspath(__file__))
LOCALE = {'nl': 'nl-NL', 'en': 'en-GB', 'de': 'de-DE', 'fr': 'fr-FR', 'it': 'it-IT', 'es': 'es-ES'}
DOTS = ['#94C24A', '#F37321', '#2DAFE6', '#A7328A']     # step colours of the website (light, orange, medium, heavy)
ACCENT, WHEN = '#F37321', '#E0610F'


def bold(s):
    return Markup(re.sub(r'\*\*(.+?)\*\*', r'<strong style="font-weight:bold;">\1</strong>', str(H.escape(s))))


def plain(s):
    return re.sub(r'\*\*(.+?)\*\*', r'\1', s)


def fr_spaces(s):
    """French: a non-breaking space before ? ! : ; so they never start a line."""
    return re.sub(r' ([?!:;])(?=[\s<&]|$)', '&nbsp;\\1', s)


def write(B, OUT):
    env = Environment(loader=FileSystemLoader(os.path.join(ROOT, 'mail')), autoescape=True)
    tpl = env.get_template('quote.j2')
    P = env.get_template('_parts.j2').make_module({})
    texts = json.load(open(os.path.join(ROOT, 'mail', 'texts.json'), encoding='utf-8'))
    photos = set(os.listdir(os.path.join(ROOT, 'root', 'assets', 'email', 'p')))
    out = {}
    for l in B.LANGS:
        t, tn, x = B.T[l], B.T['nl'], texts[l]
        fm = B.CONTENT[l]['thanks-quote']['fm']
        a, b = (re.split(r'(?<=[.!?])\s+', fm['contact']['t'], maxsplit=1) + [''])[:2]
        cards = [dict(c, href=B.url(c['page'], l)) for c in x['cards']]
        page = tpl.render(lang=l, subject=x['subject'], preheader=fm['lead'].split('. ')[0].rstrip('.') + '.', fm=fm, x=x,
                          accent=ACCENT, contact_a=a, contact_b=b, hours=t['hours_1'] + ' · ' + t['hours_2'],
                          more_h=bold(fm['more']['h']), cards=cards, footer_about=t['footer_about'], home=B.url('home', l))
        # steps: delivered by Q-Pall, or collected by the customer (own transport)
        fm_self = json.loads(json.dumps(fm))
        for s in fm_self['next']['steps']:
            for k in ('t', 'd'):
                if s.get(k + '_self'):
                    s[k] = s[k + '_self']
        Sm = fm['sum']
        frag = {
            'row': str(P.product_row(Markup('[[THUMB]]'), Markup('[[NAME]]'), Markup('[[SKU]]'), Markup('[[QTY]]'), Markup('[[STACKS]]'))),
            'thumb': str(P.thumb_img('[[SRC]]')), 'thumb_empty': str(P.thumb_empty()),
            'name_link': str(P.pname({'url': '[[URL]]', 'name': Markup('[[TEXT]]')})), 'name_plain': str(P.pname({'url': '', 'name': Markup('[[TEXT]]')})),
            'sku': str(P.sku_line(Markup('[[TEXT]]'))), 'stacks': str(P.stacks_line(Markup('[[TEXT]]'))),
            'products_open': '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">', 'products_close': '</table>',
            'facts_open': str(P.facts_table([])).split('</table>')[0], 'facts_close': '</table>',
            'message': str(P.message_box(x['message'], Markup('[[TEXT]]'))),
            'steps_deliver': str(P.steps_vertical(fm, DOTS, WHEN)), 'steps_self': str(P.steps_vertical(fm_self, DOTS, WHEN)),
        }
        labels = {'company': Sm['company'], 'transport': Sm['transport'], 'country': Sm['country'], 'zip': Sm['zip'],
                  'date': Sm['date'], 'date_self': t['form_date_self'], 'freq': Sm['freq'], 'email': Sm['email']}
        frag['facts'] = {k: str(P.fact_row(v, Markup('[[TEXT]]'))) for k, v in labels.items()}
        if l == 'fr':
            page = fr_spaces(page)
            frag = {k: ({kk: fr_spaces(vv) for kk, vv in v.items()} if isinstance(v, dict) else fr_spaces(v)) for k, v in frag.items()}
        # products of the quote form: article number -> name, page, e-mail photo, stack size, accessory
        prods = {}
        for o in B.quote_options(l):
            sku, name = o['v'].split(' – ', 1)
            name = re.sub(r'\s+–\s+' + re.escape(sku) + r'$', '', name)   # the article number is shown on its own line
            ph = re.sub(r'[^a-z0-9.-]+', '-', sku.lower()) + '.jpg'
            prods[sku.upper()] = {'n': name.replace('\xa0', ' '), 'u': o['url'], 'i': ('/assets/email/p/' + ph) if ph in photos else '',
                                  's': o['stack'], 'a': o['acc']}
        steps_txt = lambda f: [[s['when'], s['t'], s['d']] for s in f['next']['steps']]
        out[l] = {
            'subject': x['subject'], 'locale': LOCALE[l], 'html': page, 'frag': frag,
            'h1': str(bold(fm['h1'])), 'h1_named': str(bold(fm['h1_named'])).replace('{name}', '[[NAME]]'),
            'units': {'pallets': t['stack_unit'], 'pcs': Sm['pcs'], 'pcs_1': Sm['pcs_1'], 'stack_1': Sm['stack_1'], 'stack_n': Sm['stack_n']},
            # the form sends transport and frequency in Dutch (for sales); the e-mail shows the customer's language
            'transport': {tn['tr_deliver']: [t['tr_deliver'], 'deliver'], tn['tr_self']: [t['tr_self'], 'self']},
            'freq': {tn['freq_once']: t['freq_once'], tn['freq_regular']: t['freq_regular'], tn['freq_year']: t['freq_year']},
            'products': prods,
            'text': {'h1': plain(fm['h1']), 'h1_named': plain(fm['h1_named']), 'lead': fm['lead'], 'sum_h': Sm['h'], 'labels': labels,
                     'message': x['message'], 'change': Sm['change'] + ' info@qpall.com.', 'next_h': fm['next']['h'],
                     'steps_deliver': steps_txt(fm), 'steps_self': steps_txt(fm_self), 'contact_h': fm['contact']['h'], 'contact_t': fm['contact']['t'],
                     'hours': t['hours_1'] + ' · ' + t['hours_2'], 'regards': x['regards'], 'team': x['team'], 'reason': x['reason'],
                     'address': f"Q-Pall B.V. · Edisonweg 9 · 5466 AR Veghel · {x['country_name']}"},
        }
    d = os.path.join(OUT, 'netlify', 'functions', 'submission-created')
    os.makedirs(d, exist_ok=True)
    json.dump(out, open(os.path.join(d, 'quote-mail.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    shutil.copy(os.path.join(ROOT, 'functions', 'submission-created.js'), os.path.join(d, 'submission-created.js'))
    return out
