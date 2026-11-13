/* Q-Pall · site.js — geen frameworks */
(function () {
  'use strict';
  var d = document, html = d.documentElement;
  html.classList.remove('no-js'); html.classList.add('js');
  var I18N = {};
  try { I18N = JSON.parse(d.getElementById('i18n').textContent); } catch (e) {}
  var LANG = html.lang || 'nl';
  var w = window;
  /* ---------- measurement: dataLayer events for the conversions (GA4 key events via GTM, see site_config GTM_ID) ---------- */
  var DL = w.dataLayer = w.dataLayer || [];
  var sget = function (k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } };
  var sset = function (k, v) { try { if (v === null) sessionStorage.removeItem(k); else sessionStorage.setItem(k, v); } catch (e) {} };
  d.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="tel:"], a[href^="mailto:"]');
    if (!a) return;
    var tel = a.getAttribute('href').indexOf('tel:') === 0;
    DL.push({ event: tel ? 'phone_click' : 'email_click', link_url: a.getAttribute('href'), page_path: location.pathname });
  });
  // a sent form is counted once, on the thank-you page it lands on
  var PID = d.body.getAttribute('data-pid') || '';
  if (PID === 'thanks-apply' && sget('qp-lead') === 'apply') {   // update 20: application sent
    DL.push({ event: 'job_application', form_name: 'sollicitatie', language: LANG });
    sset('qp-lead', null);
  }
  if (PID === 'thanks' || PID === 'thanks-quote') {
    var lead = sget('qp-lead');
    if (lead) {
      DL.push({ event: 'generate_lead', lead_type: lead === 'quote' ? 'offerte' : 'contact', form_name: lead === 'quote' ? 'offerte' : 'contact', language: LANG });
      sset('qp-lead', null);
    }
  }
  d.addEventListener('submit', function (e) {
    var f = e.target;
    if (f && (f.name === 'offerte' || f.name === 'contact')) {
      sset('qp-lead', f.name === 'offerte' ? 'quote' : 'contact');
    }
    if (f && f.name === 'sollicitatie') sset('qp-lead', 'apply');
    if (f && (f.name === 'contact' || f.name === 'sollicitatie')) {   // update 25: first name for the thank-you heading
      var nf = f.elements[f.name === 'contact' ? 'naam' : 'voornaam'];
      var fn = nf && nf.value ? nf.value.trim().split(/\s+/)[0] : '';
      sset('qp-name', fn ? JSON.stringify({ f: f.name, n: fn, ts: Date.now() }) : null);
    }
  }, true);
  d.addEventListener('submit', function (e) {   // bubble phase: after the quote form has filled in its product list
    var f = e.target;
    if (f && (f.name === 'offerte' || f.name === 'contact') && !e.defaultPrevented) toHubSpot(f);
  });
  // Send the three forms to Netlify in the background, then open the thank-you page in the visitor's language (update 23).
  // Netlify knows each form once, from the Dutch page (only that page carries data-netlify): its Dutch labels head the
  // e-mails. A normal post would get the thank-you page of that Dutch form back, whatever the page language was.
  d.addEventListener('submit', function (e) {
    var f = e.target, nm = f && f.getAttribute && f.getAttribute('name');
    if (e.defaultPrevented || ['offerte', 'contact', 'sollicitatie'].indexOf(nm) < 0 || !w.fetch || !w.FormData) return;
    e.preventDefault();
    var btn = f.querySelector('button[type=submit]');
    if (btn) btn.disabled = true;
    var fd = new FormData(f), multi = (f.getAttribute('enctype') || '').indexOf('multipart') === 0;
    var opts = multi ? { method: 'POST', body: fd }
      : { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams(fd).toString() };
    fetch('/', opts).then(function (r) {
      if (!r.ok) throw new Error('form ' + r.status);
      location.href = f.getAttribute('action');
    }).catch(function () {
      HTMLFormElement.prototype.submit.call(f);   // fallback: the normal post (thank-you page in Dutch)
    });
  });
  // HubSpot (update 19): the quote and contact form also go to a HubSpot form via the Forms API (v3), next to Netlify.
  // Only when HUBSPOT_FORMS in site_config.py has a form GUID. Sent fields: firstname, lastname, email, company, phone,
  // country, zip, city (quote form) and message (everything else as text). The HubSpot form must contain exactly these.
  function toHubSpot(f) {
    var H = d.documentElement, forms = {};
    try { forms = JSON.parse(H.getAttribute('data-hs-forms') || '{}'); } catch (x) {}
    var guid = forms[f.name], portal = H.getAttribute('data-hs');
    if (!guid || !portal || !window.fetch) return;
    var get = function (n) { var el = f.elements[n]; if (!el) return ''; if (el.length && !el.tagName) { var c = [].filter.call(el, function (x) { return x.checked; })[0]; return c ? c.value : ''; } return el.disabled ? '' : (el.type === 'checkbox' ? (el.checked ? 'ja' : '') : (el.value || '').trim()); };
    if (get('bot-field')) return;
    var name = get('naam').split(/\s+/), lines = [];
    var fields = [['firstname', name.shift() || ''], ['lastname', name.join(' ')], ['email', get('email')], ['company', get('bedrijf')], ['phone', get('telefoon')]];
    if (f.name === 'offerte') {
      fields.push(['country', get('land')], ['zip', get('postcode')], ['city', get('plaats')]);
      if (get('producten')) lines.push(get('producten'));
      [['Transport', 'transport'], ['Leverdatum', 'leverdatum'], ['Frequentie', 'frequentie']].forEach(function (k) { var v = get(k[1]); if (v) lines.push(k[0] + ': ' + v); });
    }
    var msg = get('bericht'); if (msg) lines.push((lines.length ? '\n' : '') + msg);
    lines.push('Taal: ' + (get('taal') || LANG) + ' | Formulier: ' + f.name);
    fields.push(['message', lines.join('\n')]);
    var m = d.cookie.match(/(?:^|; )hubspotutk=([^;]+)/);
    var body = { fields: fields.filter(function (x) { return x[1]; }).map(function (x) { return { objectTypeId: '0-1', name: x[0], value: x[1] }; }),
                 context: { pageUri: location.href, pageName: d.title } };
    if (m) body.context.hutk = m[1];
    var host = 'https://api' + (H.getAttribute('data-hs-region') ? '-' + H.getAttribute('data-hs-region') : '') + '.hsforms.com';
    try {
      fetch(host + '/submissions/v3/integration/submit/' + encodeURIComponent(portal) + '/' + encodeURIComponent(guid),
            { method: 'POST', keepalive: true, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).catch(function () {});
    } catch (x) {}
  }
  var $ = function (s, c) { return (c || d).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || d).querySelectorAll(s)); };
  var store = {
    get: function (k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  };
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var fmtInt = function (n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, (document.documentElement.lang === 'en') ? ',' : '.'); };
  var lockScroll = function (on) { d.body.style.overflow = on ? 'hidden' : ''; };

  /* ---------- language modal ---------- */
  var lmodal = $('#langmodal'), lastFocus = null;
  var setLang = function (open) {
    if (!lmodal) return;
    lmodal.hidden = !open; lockScroll(open);
    if (open) { lastFocus = d.activeElement; var cur = $('.lcard.is-current', lmodal) || $('.lcard', lmodal); if (cur) cur.focus(); }
    else if (lastFocus) { lastFocus.focus(); }
  };
  $$('[data-open-lang]').forEach(function (b) { b.addEventListener('click', function () { if (typeof setDrawer === 'function') setDrawer(false); setLang(true); }); });
  $$('[data-close-lang]').forEach(function (b) { b.addEventListener('click', function () { setLang(false); }); });
  d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && lmodal && !lmodal.hidden) setLang(false); });

  /* ---------- mega menus ---------- */
  var hdr = $('.hdr');
  var navBtns = $$('.nav-btn[aria-controls]');
  var hoverTimer = null;
  function closeMegas(except) {
    navBtns.forEach(function (b) {
      if (b === except) return;
      b.setAttribute('aria-expanded', 'false');
      var m = d.getElementById(b.getAttribute('aria-controls')); if (m) m.classList.remove('is-open');
    });
    if (!except && hdr) hdr.classList.remove('has-mega');
  }
  function openMega(b) {
    closeMegas(b);
    b.setAttribute('aria-expanded', 'true');
    var m = d.getElementById(b.getAttribute('aria-controls')); if (m) m.classList.add('is-open');
    if (hdr) hdr.classList.add('has-mega');
  }
  var finePointer = window.matchMedia && window.matchMedia('(hover:hover) and (pointer:fine)').matches;
  navBtns.forEach(function (b) {
    var item = b.parentElement;
    b.addEventListener('click', function (e) {
      e.stopPropagation();
      if (b.getAttribute('aria-expanded') === 'true') return;   /* already open: follow the link to the overview page */
      e.preventDefault(); openMega(b);
    });
    if (finePointer) {
      item.addEventListener('mouseenter', function () { clearTimeout(hoverTimer); hoverTimer = setTimeout(function () { openMega(b); }, 120); });
      item.addEventListener('mouseleave', function () { clearTimeout(hoverTimer); hoverTimer = setTimeout(function () { closeMegas(); }, 180); });
    }
  });
  $$('.mega').forEach(function (m) {
    m.addEventListener('mouseenter', function () { clearTimeout(hoverTimer); });
  });
  d.addEventListener('click', function (e) { if (hdr && !hdr.contains(e.target)) closeMegas(); });
  d.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeMegas(); });
  var scrim = $('.mega-scrim'); if (scrim) scrim.addEventListener('click', function () { closeMegas(); });

  /* ---------- drawer ---------- */
  var drawer = $('#drawer');
  function setDrawer(open) {
    if (!drawer) return;
    drawer.classList.toggle('is-open', open);
    drawer.setAttribute('aria-hidden', open ? 'false' : 'true');
    $$('[data-open-drawer]').forEach(function (b) { b.setAttribute('aria-expanded', open); });
    lockScroll(open);
    if (open) { var c = $('[data-close-drawer].icon-btn', drawer); if (c) c.focus(); }
  }
  $$('[data-open-drawer]').forEach(function (b) { b.addEventListener('click', function () { setDrawer(true); }); });
  $$('[data-close-drawer]').forEach(function (b) { b.addEventListener('click', function () { setDrawer(false); }); });
  d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && drawer && drawer.classList.contains('is-open')) setDrawer(false); });

  /* ---------- search (instant products + Pagefind) ---------- */
  var search = $('#search');
  if (search) {
    var input = $('input', search), res = $('.search-res', search), hint = $('.search-hint', search);
    var products = null, pf = null, seq = 0;
    // update 33: the index holds products (p), category and service pages (c) and the words to ignore (stop, gen)
    var loadProducts = function () {
      if (products) return Promise.resolve(products);
      return fetch('/assets/search-' + LANG + '.json').then(function (r) { return r.json(); }).then(function (j) {
        products = Array.isArray(j) ? { p: j, c: [], stop: [], gen: [] } : j;
        var prepAll = function (list) { list.forEach(function (x) { x._h = prep(x.t + ' ' + x.k + ' ' + (x.s || '')); }); };
        prepAll(products.p); prepAll(products.c);
        products._stop = {}; products.stop.forEach(function (w) { products._stop[prep(w)] = 1; });
        products._gen = {}; products.gen.forEach(function (w) { products._gen[prep(w)] = 1; });
        return products;
      }).catch(function () { products = { p: [], c: [], _stop: {}, _gen: {} }; return products; });
    };
    var loadPf = function () {
      if (pf) return Promise.resolve(pf);
      return import('/pagefind/pagefind.js').then(function (m) { pf = m; try { m.options({ excerptLength: 22 }); } catch (e) {} return m; }).catch(function () { pf = false; return false; });
    };
    var openSearch = function () { search.classList.add('is-open'); lockScroll(true); setTimeout(function () { input.focus(); }, 20); loadProducts(); loadPf(); };
    var closeSearch = function () { search.classList.remove('is-open'); lockScroll(false); };
    $$('[data-open-search]').forEach(function (b) { b.addEventListener('click', function () { closeMegas(); setDrawer(false); openSearch(); }); });
    $$('[data-close-search]').forEach(function (b) { b.addEventListener('click', closeSearch); });
    d.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && search.classList.contains('is-open')) closeSearch();
      if (e.key === '/' && !/input|textarea|select/i.test((e.target.tagName || '')) && !search.classList.contains('is-open')) { e.preventDefault(); openSearch(); }
    });
    var norm = function (s) { return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[×*]/g, 'x').replace(/\s+/g, ' '); };
    // sizes "1200 x 800" -> "1200x800"; double letters count as one, so "palet" finds "pallet" and "nestbaar" finds "nestbare"
    var prep = function (s) { return norm(s).replace(/(\d)\s*x\s*(\d)/g, '$1x$2').replace(/([a-z])\1+/g, '$1'); };
    var li = function (it) {
      var img = it.i ? '<img src="' + esc(it.i) + '" alt="" loading="lazy">' : '<span class="sr-ico"><svg class="ico" aria-hidden="true"><use href="#i-' + (it.c ? 'grid' : it.v ? 'arrow' : 'doc') + '"/></svg></span>';
      return '<li><a href="' + esc(it.u) + '">' + img + '<span><b>' + esc(it.t) + '</b><small>' + (it.h ? it.s : esc(it.s)) + '</small></span></a></li>';
    };
    var head = function (txt) { return '<li class="sr-head" role="presentation">' + esc(txt) + '</li>'; };
    var render = function (groups) {
      var used = groups.filter(function (g) { return g.items.length; });
      if (!used.length) {
        res.innerHTML = '<li class="sr-empty">' + esc(I18N.search_none) + (search.dataset.quote ? ' <a class="sr-help" href="' + esc(search.dataset.quote) + '">' + esc(search.dataset.quoteTxt) + '</a>' : '') + '</li>';
        return;
      }
      res.innerHTML = used.map(function (g) { return (used.length > 1 ? head(g.label) : '') + g.items.map(li).join(''); }).join('');
    };
    var run = function () {
      var q = input.value.trim(), my = ++seq;
      hint.hidden = !!q;
      if (q.length < 2) { res.innerHTML = ''; return; }
      loadProducts().then(function (P) {
        var all = prep(q).replace(/[,;:!?()"]/g, ' ').split(' ').filter(Boolean).filter(function (w) { return !P._stop[w]; });
        var terms = all.filter(function (w) { return !P._gen[w]; });
        var onlyGen = !terms.length;
        if (onlyGen) terms = all;
        var has = function (x) { return terms.every(function (t) { return x._h.indexOf(t) > -1; }); };
        var whole = prep(q).replace(/[,;:!?()"]/g, ' ').replace(/\s+/g, ' ').trim();
        // ranking: an exact article number first, then items whose nickname is the whole query ("europallet" -> 1200 x 800)
        // update 50: also while typing ("europal" -> Europallet before "Kwart europallet"), and a word that starts with
        // the query counts more than one that only contains it somewhere in the middle
        var wordStart = function (x) { return terms.every(function (t) { return (' ' + x._h).indexOf(' ' + t) > -1; }); };
        // article numbers (update 53): compared in the same prepared form as the query (double letters count as one, so
        // 'QP1208MB3RR' did not match before); the exact number first, then the same number in another version
        // (3.QP1208LB9FR for QP1208LB9FR), then numbers that start with what was typed
        var skuScore = function (x) {
          var best = 0;
          (x.x || []).forEach(function (s) {
            var p = prep(s), base = p.replace(/^[0-9n]+\./, '');
            terms.forEach(function (t) {
              if (t.length < 3) return;
              var tb = t.replace(/^[0-9n]+\./, '');
              var v = p === t ? 10 : base === tb ? 8 : (p.indexOf(t) === 0 || base.indexOf(tb) === 0) && /\d/.test(t) ? 6 : 0;
              if (v > best) best = v;
            });
          });
          // tie-break on the number as typed (QPKVOUWR before QPKKVOUWR, which the double-letter rule makes equal)
          var raw = norm(q).trim();
          if (best && raw.length > 2 && (x.x || []).some(function (s) { return norm(s).replace(/^[0-9n]+\./, '').indexOf(raw.replace(/^[0-9n]+\./, '')) === 0; })) best += 1;
          return best;
        };
        var score = function (x) {
          var n = x.n ? prep(x.n) : '';
          return skuScore(x) +
            (n && n === whole ? 2 : n && whole.length > 2 && n.indexOf(whole) === 0 ? 1.5 : 0) + (wordStart(x) ? 0.5 : 0);
        };
        var rank = function (list) { return list.map(function (x, n) { return { x: x, n: n, e: score(x) }; }).sort(function (a, b) { return b.e - a.e || a.n - b.n; }).map(function (h) { return h.x; }); };
        var cats = (onlyGen ? P.c.filter(function (c) { return c.all; }) : rank(P.c.filter(has))).slice(0, 2)
          .map(function (c) { return { t: c.t, u: c.u, s: c.s, c: !c.svc, v: !!c.svc }; });
        var hits = onlyGen ? [] : rank(P.p.filter(has)).slice(0, 6).map(function (p) { return { t: p.t, u: p.u, s: p.s, i: p.i }; });
        if (my !== seq) return;
        var G = [{ label: I18N.search_g_cat, items: cats }, { label: I18N.search_g_prod, items: hits }, { label: I18N.search_g_page, items: [] }];
        render(G);
        loadPf().then(function (m) {
          if (!m || my !== seq) return;
          m.debouncedSearch(q, {}, 160).then(function (r) {
            if (!r || my !== seq) return;
            return Promise.all(r.results.slice(0, 10).map(function (x) { return x.data(); })).then(function (data) {
              if (my !== seq) return;
              var seen = {}; cats.concat(hits).forEach(function (h) { seen[h.u] = 1; });
              // Pagefind also answers nonsense with pages that only match a single letter ("x" in sizes): drop those
              var minLen = Math.min(3, Math.max.apply(null, all.map(function (w) { return w.length; })));
              var real = function (x) { var mk = (x.excerpt || '').match(/<mark>[^<]*<\/mark>/g); return !mk || mk.some(function (m) { return m.replace(/<\/?mark>/g, '').length >= minLen; }); };
              G[2].items = data.filter(real).filter(function (x) { var u = x.url.replace(/index\.html$/, ''); if (seen[u]) return false; seen[u] = 1; return true; })
                .map(function (x) { return { t: (x.meta && x.meta.title || '').replace(/ – Q-Pall$/, ''), u: x.url.replace(/index\.html$/, ''), s: x.excerpt, h: true, i: x.meta && x.meta.image }; })
                .slice(0, Math.max(3, 10 - cats.length - hits.length));
              render(G);
            });
          });
        });
      });
    };
    $$('[data-q]', search).forEach(function (b) { b.addEventListener('click', function () { input.value = b.getAttribute('data-q'); input.focus(); run(); }); });
    input.addEventListener('input', run);
    input.addEventListener('keydown', function (e) {
      var links = $$('a', res); if (!links.length) return;
      var i = links.indexOf(d.activeElement);
      if (e.key === 'ArrowDown') { e.preventDefault(); links[Math.min(links.length - 1, i + 1)].focus(); }
      if (e.key === 'Enter' && i < 0) { e.preventDefault(); links[0].click(); }
    });
    res.addEventListener('keydown', function (e) {
      var links = $$('a', res), i = links.indexOf(d.activeElement);
      if (e.key === 'ArrowDown') { e.preventDefault(); if (links[i + 1]) links[i + 1].focus(); }
      if (e.key === 'ArrowUp') { e.preventDefault(); if (i <= 0) input.focus(); else links[i - 1].focus(); }
    });
  }

  /* ---------- deferred images (data-defer): hidden hero slides and Q colours, fetched once the page
     has loaded so they never compete with what is on screen (PageSpeed: LCP / Speed Index) ---------- */
  var loadDeferred = function (els) {
    els.forEach(function (im) {
      if (!im || !im.hasAttribute('data-defer')) return;
      var pic = im.parentNode;
      if (pic && pic.tagName === 'PICTURE') $$('source[data-srcset]', pic).forEach(function (so) { so.srcset = so.getAttribute('data-srcset'); so.removeAttribute('data-srcset'); });
      if (im.getAttribute('data-srcset')) { im.srcset = im.getAttribute('data-srcset'); im.removeAttribute('data-srcset'); }
      if (im.getAttribute('data-src')) { im.src = im.getAttribute('data-src'); im.removeAttribute('data-src'); }
      im.removeAttribute('data-defer');
    });
  };
  var deferred = $$('img[data-defer]');
  if (deferred.length) {
    var loadAll = function () { loadDeferred(deferred); };
    var later = function () { setTimeout(function () { if ('requestIdleCallback' in window) requestIdleCallback(loadAll, { timeout: 2000 }); else loadAll(); }, 1200); };
    if (d.readyState === 'complete') later(); else window.addEventListener('load', later);
    // any interaction (menu hover, drawer tap, keyboard) before that: fetch them right away
    ['pointerover', 'pointerdown', 'keydown'].forEach(function (ev) { d.addEventListener(ev, loadAll, { once: true, passive: true }); });
  }

  /* ---------- hero: light / medium / heavy ---------- */
  var hero = $('[data-hero]');
  if (hero) {
    var slides = $$('[data-slide]', hero), tabs = $$('.hsw', hero), order = ['medium', 'heavy', 'light'], idx = 0, timer = null, stopped = false;
    var heroSec = hero.closest('.hero'), heroQ = heroSec ? $$('.hero-q', heroSec) : [];
    var show = function (cls) {
      // images of the class that is about to show (normally already fetched after page load)
      loadDeferred($$('[data-cls="' + cls + '"] img[data-defer]', hero).concat(heroQ.filter(function (q) { return q.classList.contains('hero-q-' + cls); })));
      slides.forEach(function (s) { var on = s.dataset.cls === cls; s.classList.toggle('is-active', on); if (s.tagName === 'A') s.tabIndex = on ? 0 : -1; });
      if (heroSec) heroSec.setAttribute('data-hc', cls);   // background gradient + Q follow the class colour
      heroQ.forEach(function (q) { q.classList.toggle('is-on', q.classList.contains('hero-q-' + cls)); });
      tabs.forEach(function (t) { t.setAttribute('aria-pressed', t.dataset.cls === cls ? 'true' : 'false'); });
      idx = order.indexOf(cls);
    };
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var start = function () { if (stopped || reduce) return; clearInterval(timer); timer = setInterval(function () { show(order[(idx + 1) % order.length]); }, 6000); };
    tabs.forEach(function (t) { t.addEventListener('click', function () { stopped = true; clearInterval(timer); show(t.dataset.cls); }); });
    hero.addEventListener('mouseenter', function () { clearInterval(timer); loadDeferred(deferred); });
    hero.addEventListener('focusin', function () { loadDeferred(deferred); });
    hero.addEventListener('touchstart', function () { loadDeferred(deferred); }, { passive: true });
    hero.addEventListener('mouseleave', start);
    start();
  }

  /* ---------- factory map (homepage): hover / click a factory to show its 600 km radius ---------- */
  var mapc = $('[data-map]');
  if (mapc) {
    var mroot = mapc.closest('.local') || d, sticky = null;
    var mark = function (code) {
      mapc.classList.toggle('has-sel', !!code);
      $$('.m-r', mapc).forEach(function (c) { c.classList.toggle('is-on', c.getAttribute('data-fac') === code); });
      $$('.m-fac, .plant-btn', mroot).forEach(function (g) { var on = g.getAttribute('data-fac') === code; g.classList.toggle('is-on', on); g.setAttribute('aria-pressed', on ? 'true' : 'false'); });
    };
    $$('.m-fac, .plant-btn', mroot).forEach(function (g) {
      var code = g.getAttribute('data-fac');
      g.addEventListener('mouseenter', function () { if (!sticky) mark(code); });
      g.addEventListener('mouseleave', function () { mark(sticky); });
      g.addEventListener('click', function (e) { e.stopPropagation(); sticky = sticky === code ? null : code; mark(sticky); });
      if (g.tagName.toLowerCase() === 'g') g.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); g.dispatchEvent(new MouseEvent('click')); } });
    });
    d.addEventListener('click', function (e) { if (sticky) { sticky = null; mark(null); } });
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && sticky) { sticky = null; mark(null); } });
  }

  /* ---------- segmented tabs (home range) ---------- */
  $$('.seg').forEach(function (seg) {
    var btns = $$('button', seg);
    btns.forEach(function (b) {
      b.addEventListener('click', function () {
        btns.forEach(function (x) { var on = x === b; x.setAttribute('aria-selected', on); x.tabIndex = on ? 0 : -1; var p = d.getElementById(x.getAttribute('aria-controls')); if (p) p.hidden = !on; });
      });
    });
  });

  /* ---------- knowledge base filter ---------- */
  // news overview: the first 12 articles in the grid, the rest after 'Meer nieuws tonen' (all links are in the HTML)
  $$('[data-news-more]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var grid = document.querySelector('[data-news-grid]');
      if (!grid) return;
      var first = grid.querySelector('li.is-more a');
      grid.classList.add('is-open');
      btn.parentNode.parentNode.removeChild(btn.parentNode);
      if (first) first.focus({ preventScroll: true });
    });
  });
  $$('[data-kb-filter]').forEach(function (bar) {
    var cards = $$('.kb-index .kc');
    $$('button', bar).forEach(function (b) {
      b.addEventListener('click', function () {
        var cat = b.dataset.cat;
        $$('button', bar).forEach(function (x) { var on = x === b; x.classList.toggle('is-on', on); x.setAttribute('aria-pressed', on); });
        cards.forEach(function (c) { c.hidden = !(cat === 'all' || c.dataset.cat === cat); });
        var grid = $('.kb-index'); if (grid) grid.classList.toggle('is-filtered', cat !== 'all');
      });
    });
  });

  /* ---------- no scroll animations: the hero L/M/H switch is the only animation ---------- */
  $$('.intro').forEach(function (el) { el.classList.add('is-in'); });

  /* ---------- listing filters ---------- */
  var listing = $('[data-listing]');
  if (listing) {
    var form = $('#filterform'), cards = $$('.pcard', listing), grid = $('.grid-products', listing);
    var countEl = $('[data-count]', listing), active = $('.active-filters', listing), none = $('.no-results', listing), sortSel = $('#sortsel');
    var filtersEl = $('.filters', listing);
    var PAGE = cards.length > 30 ? 24 : 1e6, limit = PAGE, moreWrap = $('.more-wrap', listing), moreN = $('[data-more-n]', listing);
    var params = new URLSearchParams(location.search);
    var mapUse = { rack: 'rack', export: 'export', hyg: 'hyg', nest: 'nest' };
    var setBox = function (name, val) { var el = form.querySelector('input[name="' + name + '"][value="' + val + '"]'); if (el) el.checked = true; };
    (params.get('size') || '').split(',').filter(Boolean).forEach(function (v) { setBox('size', v); });
    (params.get('cls') || params.get('class') || '').split(',').filter(Boolean).forEach(function (v) { setBox('class', v); });
    (params.get('deck') || '').split(',').filter(Boolean).forEach(function (v) { setBox('deck', v); });
    (params.get('base') || '').split(',').filter(Boolean).forEach(function (v) { setBox('base', v); });
    (params.get('f') || '').split(',').filter(Boolean).forEach(function (v) { setBox('f', v); });
    if (params.get('use') && mapUse[params.get('use')]) setBox('f', mapUse[params.get('use')]);
    ['static', 'dyn', 'rack'].forEach(function (k) {
      var v = params.get(k); var sel = form.querySelector('select[name="' + k + '"]');
      if (v && sel) { var best = '0'; $$('option', sel).forEach(function (o) { if (+o.value <= +v && +o.value > +best) best = o.value; }); sel.value = best; }
    });
    if (params.get('sort') && sortSel) sortSel.value = params.get('sort');
    var state = function () {
      var s = { size: [], class: [], deck: [], base: [], f: [], static: 0, dyn: 0, rack: 0 };
      $$('input:checked', form).forEach(function (i) { s[i.name].push(i.value); });
      ['static', 'dyn', 'rack'].forEach(function (k) { var sel = form.querySelector('select[name="' + k + '"]'); s[k] = sel ? +sel.value : 0; });
      return s;
    };
    var apply = function (push) {
      var s = state(), n = 0;
      cards.forEach(function (c) {
        var ok = (!s.size.length || s.size.indexOf(c.dataset.size) > -1) &&
          (!s.class.length || s.class.indexOf(c.dataset.cls) > -1) &&
          (!s.deck.length || s.deck.indexOf(c.dataset.deck) > -1) &&
          (!s.base.length || s.base.indexOf(c.dataset.base) > -1) &&
          s.f.every(function (f) { return c.dataset['f' + f] === '1'; }) &&
          (+c.dataset.static >= s.static) && (+c.dataset.dyn >= s.dyn) && (+c.dataset.rack >= s.rack);
        c.classList.toggle('is-hidden', !ok);
        c.classList.remove('pre-more');
      });
      $$('.pcard', grid).forEach(function (c) {
        if (c.classList.contains('is-hidden')) { c.classList.remove('is-more'); return; }
        n++; c.classList.toggle('is-more', n > limit);
      });
      if (moreWrap) { moreWrap.hidden = n <= limit; if (moreN) moreN.textContent = '(' + (n - limit) + ')'; }
      countEl.innerHTML = '<b>' + n + '</b> ' + (n === 1 ? I18N.result : I18N.results);
      if (none) none.hidden = n > 0;
      var chips = [];
      $$('input:checked', form).forEach(function (i) { chips.push('<button type="button" data-rm="' + i.name + ':' + i.value + '">' + esc(i.dataset.label) + '</button>'); });
      ['static', 'dyn', 'rack'].forEach(function (k) {
        var sel = form.querySelector('select[name="' + k + '"]');
        if (sel && +sel.value) { var lab = sel.closest('label').querySelector('span').textContent; chips.push('<button type="button" data-rm="' + k + ':0">' + esc(lab) + ' ≥ ' + fmtInt(sel.value) + ' kg</button>'); }
      });
      active.innerHTML = chips.join('');
      if (push !== false) {
        var p = new URLSearchParams();
        ['size', 'class', 'deck', 'base', 'f'].forEach(function (k) { if (s[k].length) p.set(k === 'class' ? 'cls' : k, s[k].join(',')); });
        ['static', 'dyn', 'rack'].forEach(function (k) { if (s[k]) p.set(k, s[k]); });
        if (sortSel && sortSel.value !== 'pop') p.set('sort', sortSel.value);
        var qs = p.toString();
        try { history.replaceState(null, '', location.pathname + (qs ? '?' + qs : '') + location.hash); } catch (e) {}
      }
    };
    var sort = function () {
      var v = sortSel ? sortSel.value : 'pop';
      var key = { pop: function (c) { return +c.dataset.order; }, price: function (c) { return c.dataset.price ? +c.dataset.price : 1e9; },
        static: function (c) { return -c.dataset.static; }, rack: function (c) { return -c.dataset.rack; }, weight: function (c) { return +c.dataset.weight; } }[v];
      var sorted = cards.slice().sort(function (a, b) { return key(a) - key(b) || (+a.dataset.order - +b.dataset.order); });
      var cur = $$('.pcard', grid);
      if (sorted.every(function (c, i) { return cur[i] === c; })) return;     // already in this order: no DOM moves (update 33)
      sorted.forEach(function (c) { grid.appendChild(c); });
    };
    form.addEventListener('change', function () { limit = PAGE; apply(); });
    if (sortSel) sortSel.addEventListener('change', function () { limit = PAGE; sort(); apply(); });
    var moreBtn = $('[data-more]', listing);
    if (moreBtn) moreBtn.addEventListener('click', function () {
      var first = $('.pcard.is-more', grid); limit += PAGE; apply(false);
      if (first) { var a = $('a', first); if (a) a.focus({ preventScroll: true }); }
    });
    active.addEventListener('click', function (e) {
      var b = e.target.closest('[data-rm]'); if (!b) return;
      var p = b.dataset.rm.split(':');
      if (['static', 'dyn', 'rack'].indexOf(p[0]) > -1) { form.querySelector('select[name="' + p[0] + '"]').value = '0'; }
      else { var el = form.querySelector('input[name="' + p[0] + '"][value="' + p[1] + '"]'); if (el) el.checked = false; }
      limit = PAGE; apply();
    });
    $$('[data-reset]', listing).forEach(function (b) { b.addEventListener('click', function () { form.reset(); limit = PAGE; apply(); }); });
    $$('[data-open-filters]').forEach(function (b) { b.addEventListener('click', function () { filtersEl.classList.add('is-open'); lockScroll(true); }); });
    $$('[data-close-filters]').forEach(function (b) { b.addEventListener('click', function () { filtersEl.classList.remove('is-open'); lockScroll(false); }); });
    sort(); apply(false);
  }

  /* ---------- product page: the sticky quote bar only appears once the page's own quote button has scrolled out
     of view above (update 35) ---------- */
  var stickyBar = $('.sticky-cta'), mainCta = $('.pricebox .btn');
  if (stickyBar && mainCta && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (es) {
      var e = es[es.length - 1], past = !e.isIntersecting && e.boundingClientRect.top < 0;
      stickyBar.classList.toggle('is-on', past); d.body.classList.toggle('has-sticky', past);
    }).observe(mainCta);
  } else if (stickyBar) { stickyBar.classList.add('is-on'); d.body.classList.add('has-sticky'); }

  /* ---------- compare ---------- */
  var CK = 'qp-compare';
  var cmpList = store.get(CK) || [];
  var bar = $('#cmpbar'), modal = $('#cmpmodal');
  var syncCmp = function () {
    store.set(CK, cmpList);
    $$('input[data-cmp]').forEach(function (i) { i.checked = cmpList.some(function (x) { return x.id === i.value; }); });
    if (!bar) return;
    bar.classList.toggle('is-on', cmpList.length > 0);
    document.body.classList.toggle('has-cmp', cmpList.length > 0);
    $('[data-cmp-count]', bar).textContent = cmpList.length;
    $('.thumbs', bar).innerHTML = cmpList.map(function (x) { return '<img src="' + esc(x.img) + '" alt="' + esc(x.name) + '">'; }).join('');
  };
  d.addEventListener('change', function (e) {
    var i = e.target; if (!i.matches || !i.matches('input[data-cmp]')) return;
    var data; try { data = JSON.parse(i.dataset.cmp); } catch (er) { return; }
    if (i.checked) {
      if (cmpList.length >= 4) { i.checked = false; alert(I18N.compare_max); return; }
      if (!cmpList.some(function (x) { return x.id === data.id; })) cmpList.push(data);
    } else { cmpList = cmpList.filter(function (x) { return x.id !== data.id; }); }
    syncCmp();
  });
  var openModal = function () {
    if (!modal || !cmpList.length) return;
    var R = I18N.cmp_rows || {};
    var rows = [['', function (x) { return '<a href="' + esc(x.url) + '"><img src="' + esc(x.img) + '" alt="' + esc(x.name) + '"></a>'; }],
      [R.name, function (x) { return '<a href="' + esc(x.url) + '">' + esc(x.name) + '</a>'; }],
      [R.dims, 'dims'], [R.weight, 'weight'], [R.cls, 'cls'], [R.deck, 'deck'], [R.base, 'base'],
      [R.static, function (x) { return fmtInt(x.static) + ' kg'; }], [R.dyn, function (x) { return fmtInt(x.dyn) + ' kg'; }],
      [R.rack, function (x) { return x.rack ? fmtInt(x.rack) + ' kg' : '–'; }]].concat(R.price ? [[R.price, function (x) { return esc(x.price || I18N.on_request); }]] : []);   // no price row without prices (update 34)
    $('.cmp-table tbody', modal).innerHTML = rows.map(function (r) {
      return '<tr><th scope="row">' + esc(r[0]) + '</th>' + cmpList.map(function (x) { return '<td>' + (typeof r[1] === 'function' ? r[1](x) : esc(x[r[1]])) + '</td>'; }).join('') + '</tr>';
    }).join('');
    modal.classList.add('is-open'); lockScroll(true);
  };
  var closeModal = function () { if (modal) { modal.classList.remove('is-open'); lockScroll(false); } };
  $$('[data-cmp-open]').forEach(function (b) { b.addEventListener('click', openModal); });
  $$('[data-close-modal]').forEach(function (b) { b.addEventListener('click', closeModal); });
  $$('[data-cmp-clear]').forEach(function (b) { b.addEventListener('click', function () { cmpList = []; syncCmp(); }); });
  d.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeModal(); });
  syncCmp();

  /* ---------- product gallery ---------- */
  $$('[data-gallery]').forEach(function (g) {
    var thumbs = $$('.g-thumb', g);
    thumbs.forEach(function (t) {
      t.addEventListener('click', function () {
        thumbs.forEach(function (x) { x.setAttribute('aria-selected', x === t ? 'true' : 'false'); });
        $$('.g-slide', g).forEach(function (s) { s.classList.toggle('is-active', s.id === t.getAttribute('aria-controls')); });
      });
    });
  });

  /* ---------- product photo lightbox: click a photo (or the zoom button) to enlarge it ---------- */
  var lb = $('#lightbox'), gal = $('[data-gallery]');
  if (lb && gal) {
    var pics = $$('.g-slide:not(.g-draw) img', gal), lbImg = $('.lb-fig img', lb), lbFig = $('.lb-fig', lb), lbCap = $('.lb-cap', lb), lbCur = 0, lbBack = null;
    var lbShow = function (i) {
      lbCur = (i + pics.length) % pics.length;
      var im = pics[lbCur];
      lb.classList.remove('is-zoom');
      lbImg.src = im.getAttribute('data-lg') || im.currentSrc || im.src;
      lbImg.alt = im.alt;
      lbCap.textContent = pics.length > 1 ? (lbCur + 1) + ' / ' + pics.length : '';
    };
    var lbOpen = function (i) { lbBack = d.activeElement; lbShow(i); lb.hidden = false; lockScroll(true); $('[data-lb-close]', lb).focus(); };
    var lbClose = function () { lb.hidden = true; lb.classList.remove('is-zoom'); lockScroll(false); if (lbBack && lbBack.focus) lbBack.focus(); };
    var lbActive = function () { var a = $('.g-slide.is-active img', gal), i = pics.indexOf(a); return i < 0 ? 0 : i; };
    pics.forEach(function (im, i) { im.addEventListener('click', function () { lbOpen(i); }); });
    $$('[data-lb-open]').forEach(function (b) { b.addEventListener('click', function () { lbOpen(lbActive()); }); });
    $('[data-lb-close]', lb).addEventListener('click', lbClose);
    $('[data-lb-prev]', lb).addEventListener('click', function () { lbShow(lbCur - 1); });
    $('[data-lb-next]', lb).addEventListener('click', function () { lbShow(lbCur + 1); });
    if (pics.length < 2) $$('.lb-nav', lb).forEach(function (b) { b.hidden = true; });
    lb.addEventListener('click', function (e) { if (e.target === lb || e.target === lbFig) lbClose(); });
    // desktop: click the photo to see it at full size, click again to fit; phones: pinch to zoom
    lbImg.addEventListener('click', function (e) {
      if (!finePointer) return;
      var r = lbImg.getBoundingClientRect(), fx = (e.clientX - r.left) / r.width, fy = (e.clientY - r.top) / r.height;
      lb.classList.toggle('is-zoom');
      if (lb.classList.contains('is-zoom')) {
        requestAnimationFrame(function () { lbFig.scrollLeft = fx * lbFig.scrollWidth - lbFig.clientWidth / 2; lbFig.scrollTop = fy * lbFig.scrollHeight - lbFig.clientHeight / 2; });
      }
    });
    d.addEventListener('keydown', function (e) {
      if (lb.hidden) return;
      if (e.key === 'Escape') lbClose();
      else if (e.key === 'ArrowLeft') lbShow(lbCur - 1);
      else if (e.key === 'ArrowRight') lbShow(lbCur + 1);
      else if (e.key === 'Tab') {   // keep the focus inside the lightbox
        var f = $$('button:not([hidden])', lb), first = f[0], last = f[f.length - 1];
        if (e.shiftKey && d.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && d.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });
    var lbX = null;
    lb.addEventListener('touchstart', function (e) { lbX = e.touches.length === 1 ? e.touches[0].clientX : null; }, { passive: true });
    lb.addEventListener('touchend', function (e) {
      if (lbX === null || pics.length < 2) return;
      var dx = e.changedTouches[0].clientX - lbX; lbX = null;
      if (Math.abs(dx) > 50 && (!window.visualViewport || window.visualViewport.scale <= 1.01)) lbShow(lbCur + (dx < 0 ? 1 : -1));
    });
  }

  /* ---------- product subnav ---------- */
  // QA round (update 47): the current section is the last one whose top has passed just below the subnav; at the
  // very bottom of the page the last section whose top is on screen wins (short last sections never reach the top).
  // The active pill is scrolled into view horizontally on narrow screens.
  var subnav = $('.subnav');
  if (subnav) {
    var links = $$('a[href^="#"]', subnav), snIn = $('.subnav-in', subnav) || subnav;
    var secs = links.map(function (a) { return d.getElementById(a.getAttribute('href').slice(1)); });
    var curIx = -1, spyQueued = false;
    var spy = function () {
      spyQueued = false;
      var line = subnav.getBoundingClientRect().bottom + 40, ix = -1;
      secs.forEach(function (s, i) { if (s && s.getBoundingClientRect().top <= line) ix = i; });
      if (window.innerHeight + window.pageYOffset >= d.documentElement.scrollHeight - 8) {
        secs.forEach(function (s, i) { if (s && s.getBoundingClientRect().top < window.innerHeight * 0.85) ix = Math.max(ix, i); });
      }
      if (ix === curIx) return;
      curIx = ix;
      links.forEach(function (a, i) { a.classList.toggle('is-current', i === ix); });
      var a = links[ix];
      if (a && snIn.scrollWidth > snIn.clientWidth) {
        var r = a.getBoundingClientRect(), wr = snIn.getBoundingClientRect();
        snIn.scrollTo({ left: snIn.scrollLeft + (r.left - wr.left) - (wr.width - r.width) / 2, behavior: 'smooth' });
      }
    };
    var queueSpy = function () { if (!spyQueued) { spyQueued = true; requestAnimationFrame(spy); } };
    window.addEventListener('scroll', queueSpy, { passive: true });
    window.addEventListener('resize', queueSpy);
    spy();
  }

  /* ---------- quote form ---------- */
  var qf = $('#quoteform');
  if (qf) {
    var lines = $$('.line', qf), addBtn = $('.add-line', qf);
    var visible = function () { return lines.filter(function (l) { return !l.hidden; }).length; };
    addBtn.addEventListener('click', function () {
      var next = lines.filter(function (l) { return l.hidden; })[0];
      if (next) { next.hidden = false; $('input', next).focus(); }
      if (visible() >= lines.length) addBtn.hidden = true;
    });
    lines.forEach(function (l) {
      var rm = $('.rm', l);
      if (rm) rm.addEventListener('click', function () { $$('input', l).forEach(function (i) { i.value = ''; }); var c = $('.qty-n', l); if (c) c.textContent = ''; var pk = $('.pick', l); if (pk) pk.hidden = true; l.hidden = true; addBtn.hidden = false; });
    });
    var qs = new URLSearchParams(location.search), prod = qs.get('product'), sku = (qs.get('sku') || '').trim();
    if (sku) {   // ?sku=5.QP1208MB3RR -> the matching 'SKU – name' option of the list
      var opts = $$('#productlist option').map(function (o) { return o.value; }), SKU = sku.toUpperCase() + ' – ';
      var opt = opts.filter(function (v) { return v.toUpperCase().indexOf(SKU) === 0; })[0]
        // a bare article number of a pallet that only exists in numbered versions (QP1208MB3RR -> 1.QP1208MB3RR)
        || opts.filter(function (v) { return /^\d+\./.test(v) && v.toUpperCase().replace(/^\d+\./, '').indexOf(SKU) === 0; })[0];
      prod = opt || sku;
    }
    // quantity: pallets go per full stack; the stack size differs per pallet (data-stack on the option, from
    // data/stapels.json: 15, 17, 45, 200 ...). Accessories and unknown products per piece.
    var accs = $$('#productlist option[data-acc]').map(function (o) { return o.value; });
    var OPT = {};
    $$('#productlist option').forEach(function (o) { OPT[o.value] = o; });
    var stackOf = function (v) { var o = OPT[v]; return o && !o.hasAttribute('data-acc') ? (parseInt(o.dataset.stack, 10) || 1) : 1; };
    lines.forEach(function (l) {
      var box = $('[data-qty]', l);
      if (!box) return;
      var inp = $('input', box), prodIn = $('input[list]', l), cap = $('.qty-n', l), per = $('.qty-per', l);
      // the chosen pallet in full under the field: photo, name, article number, stack size (update 30: the field cut the name off)
      var pick = $('.pick', l);
      var showPick = function () {
        if (!pick) return;
        var o = OPT[prodIn.value];
        if (!o) { pick.hidden = true; return; }
        var v = o.value, i = v.indexOf(' – '), s = stackOf(v), img = $('img', pick), code = i > 0 ? v.slice(0, i) : '', nm = i > 0 ? v.slice(i + 3) : v;
        if (code && nm.slice(-(code.length + 3)) === ' – ' + code) nm = nm.slice(0, -(code.length + 3));   // the name repeats the article number as its variant
        $('b', pick).textContent = nm;
        $('small', pick).textContent = (i > 0 ? pick.dataset.art + ' ' + v.slice(0, i) : '') + (s > 1 ? ' · ' + pick.dataset.per.replace('{n}', s) : '');
        if (o.dataset.img) { img.src = o.dataset.img; img.hidden = false; } else { img.hidden = true; img.removeAttribute('src'); }
        pick.hidden = false;
      };
      prodIn.addEventListener('input', showPick);
      prodIn.addEventListener('change', showPick);
      var stepOf = function () { return stackOf(prodIn.value); };
      var show = function () {
        var s = stepOf(), v = parseInt(inp.value, 10) || 0, n = v / s;
        cap.textContent = s > 1 && v >= s ? (n === 1 ? cap.dataset.one : cap.dataset.many.replace('{n}', n)) : '';
        if (per) per.textContent = s > 1 ? per.dataset.t.replace('{n}', s) : '';
      };
      var fix = function () {
        var s = stepOf(), v = parseInt(inp.value, 10) || 0;
        inp.step = s; inp.min = s; inp.placeholder = s;
        if (!v && prodIn.value.trim()) inp.value = s;   // a chosen product starts at one full stack (was only a placeholder)
        else if (v > 0 && v % s) inp.value = Math.ceil(v / s) * s;
        show();
      };
      $$('.qty-b', box).forEach(function (b) {
        b.addEventListener('click', function () {
          var s = stepOf(), v = parseInt(inp.value, 10) || 0;
          v = +b.dataset.d > 0 ? (v < s ? s : Math.floor(v / s) * s + s) : Math.max(s, Math.ceil(v / s) * s - s);
          inp.value = v; show();
        });
      });
      inp.addEventListener('input', show);
      inp.addEventListener('change', fix);
      prodIn.addEventListener('change', fix);
      fix();
    });
    // from the load calculator (update 28): ?items=SKU:qty,SKU:qty fills the lines (rounded up to full stacks) and
    // ?note= puts the calculated load in the message field
    var findOpt = function (code) {
      code = code.toUpperCase();
      return $$('#productlist option').map(function (o) { return o.value; }).filter(function (v) { return v.toUpperCase().indexOf(code + ' – ') === 0; })[0];
    };
    var calcItems = (qs.get('items') || '').split(',').map(function (x) { var p = x.split(':'); return { o: findOpt((p[0] || '').trim()), n: parseInt(p[1], 10) || 0 }; })
      .filter(function (x) { return x.o; }).slice(0, lines.length);
    if (calcItems.length) {
      calcItems.forEach(function (x, i) {
        var l = lines[i], pin = $('input[list]', l), qin = $('[data-qty] input', l);
        l.hidden = false; pin.value = x.o; pin.dispatchEvent(new Event('change'));
        if (qin && x.n) { qin.value = x.n; qin.dispatchEvent(new Event('change')); }
      });
      if (visible() >= lines.length) addBtn.hidden = true;
      prod = null;
    }
    var note = qs.get('note'), msg = $('#q-msg');
    if (note && msg && !msg.value) msg.value = note.slice(0, 1500);
    if (prod) {
      $('#prod-1').value = prod;
      $('#prod-1').dispatchEvent(new Event('change'));
      var q1 = $('#qty-1');
      if (q1) { q1.value = stackOf(prod); q1.dispatchEvent(new Event('change')); q1.focus(); }
    }
    // transport: delivered by Q-Pall or own transport (collection) - then no delivery address is needed
    var trMode = function () { var c = $('[data-transport] input:checked', qf); return c ? c.dataset.mode : 'deliver'; };
    var trSync = function () {
      var self = trMode() === 'self';
      $$('[data-deliver-only]', qf).forEach(function (f) { f.hidden = self; $$('input', f).forEach(function (i) { i.disabled = self; }); });
      var n = $('[data-self-note]', qf); if (n) n.hidden = !self;
      var dl = $('label[for="q-date"]', qf); if (dl) dl.textContent = self ? dl.dataset.self : dl.dataset.deliver;
    };
    $$('[data-transport] input', qf).forEach(function (r) { r.addEventListener('change', trSync); });
    trSync();
    // on sending: the stack count per line for sales, and a summary for the thank-you page (this browser tab only)
    qf.addEventListener('submit', function () {
      var items = [], out = [];
      lines.forEach(function (l) {
        var p = $('input[list]', l), q = $('[data-qty] input', l);
        if (!p || !p.value.trim()) return;
        var s = stackOf(p.value), v = parseInt(q.value, 10) || 0, o = OPT[p.value];
        var acc = !(o && !o.hasAttribute('data-acc'));
        var unit = acc ? (v === 1 ? 'stuk' : 'stuks') : (v === 1 ? 'pallet' : 'pallets');   // sales reads Dutch, whatever the page language
        out.push((out.length + 1) + '. ' + (o && o.dataset.nl ? o.dataset.nl : p.value.trim()) + (v ? ' – ' + v + ' ' + unit : ''));
        items.push({ p: p.value, q: v, st: s > 1 && v ? v / s : 0, per: s, acc: acc, url: o ? o.dataset.url || '' : '', img: o ? o.dataset.img || '' : '' });
      });
      if (qf.elements.producten) qf.elements.producten.value = out.join('\n');
      var val = function (n) { var e = qf.elements[n]; return e && e.value || ''; };
      var lab = function (n) {   // a chosen option as the visitor read it (the sent value is Dutch, for sales)
        var c = qf.querySelector('input[name="' + n + '"]:checked'), sp = c && c.nextElementSibling;
        return c ? (sp ? sp.textContent.trim() : c.value) : '';
      };
      try {
        sessionStorage.setItem('qp-quote', JSON.stringify({ items: items, name: val('naam'), company: val('bedrijf'), email: val('email'), country: val('land'),
          zip: trMode() === 'self' ? '' : [val('postcode'), val('plaats')].filter(Boolean).join(' '), date: val('leverdatum'), freq: lab('frequentie'), transport: lab('transport'), mode: trMode(), ts: Date.now() }));
      } catch (e) {}
    });
  }

  /* ---------- thank-you page after the quote form: summary of what this tab sent ---------- */
  var tySum = $('[data-ty-sum]');
  if (tySum) {
    var q = null;
    try { q = JSON.parse(sget('qp-quote') || 'null'); } catch (e) {}
    if (q && Date.now() - (q.ts || 0) < 6 * 3600 * 1000) {
      var h1 = $('[data-ty-h1]');
      if (h1 && q.name) {
        var first = q.name.trim().split(/\s+/)[0];
        h1.innerHTML = esc(h1.dataset.named).replace('{name}', esc(first)).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      }
      var nf = function (n) { try { return n.toLocaleString(LANG); } catch (e) { return n; } };
      var ul = $('[data-ty-items]', tySum), D = tySum.dataset;
      (q.items || []).forEach(function (it) {
        var parts = it.p.split(' – '), sku = parts[0], name = parts.slice(1).join(' – ') || '';
        var stacks = it.st ? (it.st === 1 ? D.lStack1 : D.lStackn).replace('{n}', nf(it.st)).replace('{per}', nf(it.per)) : '';
        var pcs = it.acc != null ? it.acc : it.per <= 1;
        var qty = it.q ? nf(it.q) + ' ' + (pcs ? (it.q === 1 ? D.lPcs1 || D.lPcs : D.lPcs) : D.lPallets) : '';
        var title = it.url ? '<a href="' + esc(it.url) + '">' + esc(name || sku) + '</a>' : esc(name || sku);
        ul.insertAdjacentHTML('beforeend', '<li>' + (it.img ? '<img src="' + esc(it.img) + '" alt="" width="96" height="64" loading="lazy" decoding="async">' : '<span class="ty-noimg"></span>') +
          '<span class="ty-it"><b>' + title + '</b><small>' + esc(name ? sku : '') + '</small></span><span class="ty-qty"><b>' + esc(qty) + '</b><small>' + esc(stacks) + '</small></span></li>');
      });
      var dateTxt = q.date;
      try { if (q.date) dateTxt = new Date(q.date + 'T12:00:00').toLocaleDateString(LANG, { day: 'numeric', month: 'long', year: 'numeric' }); } catch (e) {}
      var facts = { company: q.company, transport: q.transport, country: q.mode === 'self' ? '' : q.country, zip: q.zip, date: dateTxt, freq: q.freq, email: q.email };
      if (q.mode === 'self') {   // own transport: collection texts in the facts and in 'what happens next'
        $$('[data-self]').forEach(function (e) { e.textContent = e.dataset.self; });
      }
      $$('[data-ty-facts] > div', tySum).forEach(function (row) {
        var v = facts[row.dataset.k];
        if (v) $('dd', row).textContent = v; else row.hidden = true;
      });
      if (!(q.items || []).length) ul.hidden = true;
      tySum.hidden = false;
    }
  }

  /* ---------- thank-you page after the contact or application form: first name in the heading (update 25) ---------- */
  var tyH1 = $('[data-ty-h1]');
  if (tyH1 && !tySum) {
    var tyName = null;
    try { tyName = JSON.parse(sget('qp-name') || 'null'); } catch (e) {}
    var tyForm = { 'thanks': 'contact', 'thanks-apply': 'sollicitatie' }[PID];
    if (tyName && tyName.n && tyName.f === tyForm && Date.now() - (tyName.ts || 0) < 6 * 3600 * 1000) {
      tyH1.innerHTML = esc(tyH1.dataset.named).replace('{name}', esc(tyName.n)).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    }
  }

  /* ---------- cookie consent + external content ---------- */
  // Test site: the site's own cookie notice (localStorage 'qp-consent'), no GTM, no HubSpot.
  // Production (data-prod-hosts, update 19): GTM is loaded in <head> and its Cookiebot CMP asks for consent. The site's own
  // notice stays hidden and reads Cookiebot's choice; if Cookiebot does not show up within 5 s, the own notice is used.
  var CONSENT = 'qp-consent', cookie = $('#cookie');
  var consent = store.get(CONSENT);
  var PROD = (html.getAttribute('data-prod-hosts') || '').split(' ').indexOf(location.hostname) > -1;
  var CB = function () { return PROD && w.Cookiebot && w.Cookiebot.consent ? w.Cookiebot : null; };
  var gtag = function () { DL.push(arguments); };
  var loadExternal = function () {
    $$('[data-ext-src]').forEach(function (box) {
      if (box.classList.contains('is-loaded')) return;
      var f = d.createElement('iframe');
      f.src = box.dataset.extSrc; f.title = box.dataset.extTitle || ''; f.loading = 'lazy'; f.referrerPolicy = 'no-referrer-when-downgrade';
      box.appendChild(f); box.classList.add('is-loaded');
    });
    d.dispatchEvent(new CustomEvent('qp:external'));
  };
  // HubSpot tracking code (update 24): the embed code stands on every page before </body> as type="text/plain" (#hs-script-loader).
  // After consent for marketing it is switched on, on the hosts in its data-hs-hosts (site_config HUBSPOT_HOSTS: qpall.com and
  // the test sites). On production the GTM container may load the same code (its HubSpot tag); then this one is skipped.
  var loadHubSpot = function () {
    var ph = d.getElementById('hs-script-loader');
    if (w.__qpHs || !ph || ph.type !== 'text/plain') return;
    if ((ph.getAttribute('data-hs-hosts') || '').split(' ').indexOf(location.hostname) < 0) return;
    w.__qpHs = true;
    var on = function () {
      var other = [].some.call(d.querySelectorAll('script[src*="hs-scripts.com/"]'), function (s) { return s !== ph && s.type !== 'text/plain'; });
      if (other || !ph.parentNode) return;
      var sc = d.createElement('script'); sc.async = true; sc.defer = true; sc.src = ph.src;
      ph.parentNode.replaceChild(sc, ph); sc.id = 'hs-script-loader';
    };
    if (PROD && html.getAttribute('data-gtm')) setTimeout(on, 2500); else on();   // production: GTM first
  };
  var applyConsent = function () {
    if (consent && consent.external) loadExternal();
    if (consent && consent.marketing) loadHubSpot();
  };
  // consent from Cookiebot: preferences -> external content, statistics -> statistics, marketing -> marketing (HubSpot)
  var fromCookiebot = function () {
    var c = CB(); if (!c) return;
    consent = { v: 2, external: !!c.consent.preferences, analytics: !!c.consent.statistics, marketing: !!c.consent.marketing, cb: true };
    applyConsent();
  };
  var saveConsent = function (ext, an) {
    var c = CB();
    if (c) { c.submitCustomConsent(!!ext, c.consent.statistics, c.consent.marketing); return; }   // Cookiebot fires its events
    consent = { v: 2, external: !!ext, analytics: !!an, marketing: !!an, ts: Date.now() };
    store.set(CONSENT, consent);
    if (cookie) cookie.hidden = true;
    if (PROD) gtag('consent', 'update', { analytics_storage: an ? 'granted' : 'denied', ad_storage: an ? 'granted' : 'denied',
                                           ad_user_data: an ? 'granted' : 'denied', ad_personalization: an ? 'granted' : 'denied' });
    applyConsent();
  };
  if (cookie) {
    var set = $('.cookie-set', cookie), saveBtn = $('[data-ck="save"]', cookie);
    var showOwn = function () { if (!CB() && !(consent && !consent.cb)) cookie.hidden = false; };
    if (PROD && html.getAttribute('data-gtm')) {
      ['CookiebotOnConsentReady', 'CookiebotOnAccept', 'CookiebotOnDecline'].forEach(function (ev) { w.addEventListener(ev, fromCookiebot); });
      setTimeout(function () { if (!CB()) { showOwn(); if (consent && !consent.cb) applyConsent(); } }, 5000);   // fallback: no Cookiebot
    } else if (!consent) cookie.hidden = false;
    $('[data-ck="all"]', cookie).addEventListener('click', function () { saveConsent(true, true); });
    $('[data-ck="necessary"]', cookie).addEventListener('click', function () { saveConsent(false, false); });
    $('[data-ck="settings"]', cookie).addEventListener('click', function () {
      set.hidden = !set.hidden; saveBtn.hidden = set.hidden; this.hidden = !set.hidden;
      var c = store.get(CONSENT) || {};
      $('input[name="external"]', set).checked = !!c.external; $('input[name="analytics"]', set).checked = !!c.analytics;
    });
    saveBtn.addEventListener('click', function () { saveConsent($('input[name="external"]', set).checked, $('input[name="analytics"]', set).checked); });
    $$('[data-cookie-settings]').forEach(function (b) { b.addEventListener('click', function () {
      var c = CB(); if (c && c.renew) { c.renew(); return; }
      cookie.hidden = false; set.hidden = false; saveBtn.hidden = false; $('[data-ck="settings"]', cookie).hidden = true; var o = store.get(CONSENT) || {}; $('input[name="external"]', set).checked = !!o.external; $('input[name="analytics"]', set).checked = !!o.analytics; }); });
  }
  $$('[data-ext-load]').forEach(function (b) { b.addEventListener('click', function () { saveConsent(true, consent && consent.analytics); }); });
  if (!(PROD && html.getAttribute('data-gtm'))) applyConsent(); else if (CB()) fromCookiebot();

  /* ---------- Cookiebot cookie declaration on the cookie statement page (update 54) ---------- */
  // Cookiebot only works on the registered domain (qpall.com), so the list loads on the production hosts only; elsewhere
  // the short note in the box stays.
  var decl = $('[data-cookie-decl]');
  if (decl && PROD) {
    decl.innerHTML = '';
    var cd = d.createElement('script');
    cd.id = 'CookieDeclaration'; cd.async = true; cd.type = 'text/javascript';
    cd.setAttribute('data-culture', decl.getAttribute('data-culture') || 'NL');
    cd.src = 'https://consent.cookiebot.com/' + decl.getAttribute('data-cookie-decl') + '/cd.js';
    decl.appendChild(cd);
  }

  /* ---------- carrousel vergelijkbare pallets ---------- */
  $$('[data-carousel]').forEach(function (car) {
    var track = $('.car-track', car), sec = car.closest('section') || car;
    var prev = $('[data-car-prev]', sec), next = $('[data-car-next]', sec);
    if (!track) return;
    var step = function () { var c = track.firstElementChild; return c ? c.getBoundingClientRect().width + parseFloat(getComputedStyle(track).columnGap || 18) : track.clientWidth; };
    var upd = function () {
      var max = track.scrollWidth - track.clientWidth - 2;
      if (prev) prev.disabled = track.scrollLeft <= 2;
      if (next) next.disabled = track.scrollLeft >= max;
    };
    if (prev) prev.addEventListener('click', function () { track.scrollBy({ left: -step(), behavior: 'smooth' }); });
    if (next) next.addEventListener('click', function () { track.scrollBy({ left: step(), behavior: 'smooth' }); });
    track.addEventListener('scroll', function () { window.requestAnimationFrame(upd); }, { passive: true });
    window.addEventListener('resize', upd);
    upd();
  });

  /* ---------- application form (update 20): cv max. size, 'sending' state ---------- */
  $$('form[data-apply]').forEach(function (f) {
    var cv = $('input[type=file]', f), max = (parseFloat(f.dataset.cvMax) || 5) * 1048576;
    if (cv) cv.addEventListener('change', function () {
      var big = cv.files && cv.files[0] && cv.files[0].size > max;
      cv.setCustomValidity(big ? f.dataset.cvBig : '');
      if (big) cv.reportValidity();
    });
    f.addEventListener('submit', function (e) {
      if (e.defaultPrevented) return;
      var b = $('button[type=submit]', f);
      if (b) { b.disabled = true; b.textContent = f.dataset.sending; }
    });
  });

  /* ---------- transport: SimplyBook per locatie ---------- */
  var tr = $('.transport');
  if (tr) {
    var sites = $$('.tr-site', tr), wrap = $('#sb-wrap'), frameBox = $('#sb-frame'), cur = sites[0];
    var mount = function () {
      if (!(consent && consent.external) || !cur) return;
      frameBox.innerHTML = '';
      var f = d.createElement('iframe');
      f.title = 'SimplyBook – ' + cur.textContent.trim();
      f.src = '/assets/sb/frame.html?loc=' + cur.dataset.loc + '&cat=' + cur.dataset.cat + '&crop=' + (parseInt(tr.dataset.sbCrop, 10) || 0);
      f.style.height = '760px';
      frameBox.appendChild(f); wrap.classList.add('is-loaded');
      /* loading state until the booking frame reports it is ready (update 20); fallback after 12 s */
      var ld = d.createElement('div'); ld.className = 'sb-loading'; ld.setAttribute('role', 'status');
      ld.innerHTML = '<span class="sb-spin" aria-hidden="true"></span><span>' + esc(I18N.tr_loading || '') + '</span>';
      frameBox.appendChild(ld); frameBox.classList.add('is-loading');
      clearTimeout(sbTimer); sbTimer = setTimeout(sbReady, 12000);
    };
    var sbTimer = 0;
    var sbReady = function () { clearTimeout(sbTimer); frameBox.classList.remove('is-loading'); var l = $('.sb-loading', frameBox); if (l) l.parentNode.removeChild(l); };
    window.addEventListener('message', function (e) {
      if (e.origin !== location.origin || !e.data) return;
      if (e.data.qpSbReady) { sbReady(); return; }
      if (e.data.qpSbError) {
        frameBox.innerHTML = '<div class="ext-ph"><p>' + esc(I18N.tr_unavailable) + '</p><a class="btn btn-outline btn-sm" href="' + esc((cur && cur.dataset.direct) || tr.dataset.sb) + '" target="_blank" rel="noopener">' + esc(I18N.tr_open_new) + '</a></div>';
        return;
      }
      if (!e.data.qpSbHeight) return;
      var f = $('iframe', frameBox); if (f) f.style.height = Math.max(640, e.data.qpSbHeight) + 'px';
    });
    var select = function (b) {
      cur = b;
      sites.forEach(function (x) { var on = x === b; x.setAttribute('aria-selected', on); x.tabIndex = on ? 0 : -1; });
      $$('[data-site-info]', tr).forEach(function (p) { p.hidden = p.dataset.siteInfo !== b.dataset.site; });
      $$('[data-sb-direct]', tr).forEach(function (a) { if (b.dataset.direct) a.href = b.dataset.direct; });
      try { history.replaceState(null, '', '#' + b.dataset.site); } catch (e) {}
      mount();
    };
    sites.forEach(function (b, i) {
      b.addEventListener('click', function () { select(b); });
      b.addEventListener('keydown', function (e) {
        var k = e.key === 'ArrowDown' || e.key === 'ArrowRight' ? 1 : e.key === 'ArrowUp' || e.key === 'ArrowLeft' ? -1 : 0;
        if (k) { e.preventDefault(); var n = sites[(i + k + sites.length) % sites.length]; n.focus(); select(n); }
      });
    });
    var want = (new URLSearchParams(location.search).get('locatie') || location.hash.slice(1) || '').toLowerCase();   // ?locatie=balk (redirects from the old site) or #balk
    var initial = want && sites.filter(function (b) { return b.dataset.site === want; })[0];
    if (initial) select(initial); else mount();
    $$('[data-sb-load]', tr).forEach(function (b) { b.addEventListener('click', function () { saveConsent(true, consent && consent.analytics); }); });
    d.addEventListener('qp:external', mount);
  }

  /* homepage: "Kratten. Bakken. Boxen." are struck through one by one, then "Pallets." appears */
  var words = $('.intro-words');
  if (words && 'IntersectionObserver' in window && !(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches)) {
    words.classList.add('wait');   // start state without transitions; .anim adds them only when it plays
    var wIo = new IntersectionObserver(function (ents) {
      if (ents.some(function (e) { return e.isIntersecting; })) { words.classList.add('anim'); words.classList.remove('wait'); wIo.disconnect(); }
    }, { threshold: .6 });
    wIo.observe(words);
  }
})();
