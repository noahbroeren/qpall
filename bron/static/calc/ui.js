/* ===== Q-Pall laadcalculator: weergave in de huisstijl van de site =====
   Draait bovenop de ongewijzigde rekenmotor (engine.js): vult diens verborgen invoervelden en roept
   calculateLoad() aan. Teksten, productnamen en de voorinstelling komen uit de pagina (#qpc-data). */
(function () {
  var root = document.getElementById('qpc'), main = document.getElementById('qpc-main'), stepsEl = document.getElementById('qpc-steps');
  var D = {}; try { D = JSON.parse(document.getElementById('qpc-data').textContent); } catch (e) {}
  var TX = D.t || {}, NICK = D.nick || {}, CAT = D.cat || {};
  window.QPC_T = TX;     // translated alert texts for engine.js (update 33)
  var t = function (k) { return TX[k] || k; };
  var nf = function (n) { return String(Math.round(Number(n) || 0)).replace(/\B(?=(\d{3})+(?!\d))/g, '.'); };   // 7.500 in every language, like the rest of the site
  var esc = function (x) { return String(x).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  var ICON = {
    arrow: '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    back: '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5M11 6l-6 6 6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    check: '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    plus: '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    x: '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    copy: '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><rect x="8" y="8" width="12" height="12" rx="2.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M16 8V6.5A2.5 2.5 0 0 0 13.5 4h-7A2.5 2.5 0 0 0 4 6.5v7A2.5 2.5 0 0 0 6.5 16H8" fill="none" stroke="currentColor" stroke-width="2"/></svg>',
    redo: '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12a8 8 0 1 0 2.4-5.7M4 4v4.5h4.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
  };
  var veh = function (k) { return '<svg class="qv" viewBox="0 0 168 76" aria-hidden="true"><use href="#qv-' + k + '"/></svg>'; };

  /* ---- catalogue (same sizes and versions as the original calculator) ---- */
  var SIZES = [
    { id: '1208', key: '1200x800', v: [['QP1208LB9FR', 'nest'], ['QP1208LB9FR-FOLIE', 'nest', 'foil'], ['QP1208LB3RR', 'light'], ['QP1208MB3RR', 'medium'], ['QP1208HB3RR', 'heavy'], ['EUROPAL800RR', 'heavy']] },
    { id: '1210', key: '1200x1000', v: [['QP1210LB9FR', 'nest'], ['QP1210LB9FR-FOLIE', 'nest', 'foil'], ['QP1210LB3RR', 'light'], ['QP1210MB3RR', 'medium'], ['QP1210HB3RR', 'heavy'], ['QP1210HP3R-AO', 'heavy'], ['RECYCPAL1210RR', 'heavy']] },
    { id: '1212', key: '1200x1200', v: [['QP1212LB9FR', 'nest'], ['QP1212LB3RR', 'light'], ['QP1212MB3RR', 'medium'], ['QP1212HB3RR', 'heavy']] },
    { id: '1140', key: '1140x1140', v: [['QP1140LB9FR', 'nest'], ['QP1140LB3RR', 'light'], ['QP1140MB3RR', 'medium'], ['QP1140MB3R-PAS', 'medium'], ['QP1140HB3RR', 'heavy']] },
    { id: '1111', key: '1100x1100', v: [['QP1111LB9FR', 'nest'], ['QP1111LB3RR', 'light'], ['QP1111MB3R-AS', 'medium'], ['QP1111HB3RR', 'heavy']] },
    { id: '76114', key: '760x1140', v: [['QP76114LB9FR', 'nest'], ['QP76114LB3RR', 'light']] },
    { id: '1311', key: '1300x1100', v: [['QP1311MB3R-AS', 'medium'], ['QP1311HB3R-AS', 'heavy'], ['QP1311HB3R', 'heavy']] },
    { id: '6080', key: '600x800', v: [['QP6080LR3RR', 'light'], ['QP6080M6FR', 'medium'], ['QP6080HB6FR', 'heavy']] },
    { id: '6040', key: '600x400', v: [['QP6040MB4F', 'medium'], ['QP6040HB4F', 'heavy']] }
  ];
  var dim = function (z) { return z.key.replace('x', ' x '); };
  var sub = function (z) { return NICK[z.key] || ''; };
  var sizeOf = function (sku) { return SIZES.filter(function (z) { return z.v.some(function (v) { return v[0] === sku; }); })[0]; };
  var varOf = function (sku) { return sizeOf(sku).v.filter(function (v) { return v[0] === sku; })[0]; };
  var isNest = function (sku) { return varOf(sku)[1] === 'nest'; };
  var clsOf = function (sku) { var c = varOf(sku)[1]; return c === 'nest' ? 'light' : c; };
  var img = function (sku) { return SKUIMG[sku] ? '/assets/img/pallets/' + SKUIMG[sku] + '-320.webp' : ''; };
  var RUNNER_IMG = '/assets/img/acc/click-on-runner-qp-run-l.webp';
  var NEST_RUNNER = function (sku) { return defaultRunners[sku] || 'QP-RUN-L'; };
  var badges = function (sku) {
    var v = varOf(sku), c = clsOf(sku);
    return '<span class="badge badge-' + c + '">' + t(c) + '</span>' + (v[1] === 'nest' ? '<span class="qpc-tag">' + t('nest') + '</span>' : '') + (v[2] ? '<span class="qpc-tag">' + t(v[2]) + '</span>' : '');
  };
  var label = function (sku) { var v = varOf(sku); return dim(sizeOf(sku)) + ' · ' + t(clsOf(sku)) + (v[1] === 'nest' ? ', ' + t('nest').toLowerCase() : '') + (v[2] ? ', ' + t(v[2]) : ''); };
  var siteName = function (sku) { return CAT[sku] && CAT[sku].n; };

  /* ---- state ---- */
  var PRE = root.getAttribute('data-sku') || '', PRESIZE = root.getAttribute('data-size') || '';
  // load calculator page opened from a product page: ?pallet=<calculator article number> preselects that pallet
  if (!PRE) {
    var qpal = (new URLSearchParams(location.search).get('pallet') || '').toUpperCase();
    if (qpal && sizeOf(qpal)) {
      PRE = qpal; PRESIZE = sizeOf(qpal).id;
      var art = new URLSearchParams(location.search).get('art');   // the product page's own article number, for the quote button
      if (art && /^[\w.\-]+$/.test(art)) root.setAttribute('data-site', art);
    }
  }
  if (PRE && !sizeOf(PRE)) PRE = '';
  var s = { step: 'veh', cat: null, veh: null, vehLabel: '', clen: null, ctype: 'std', size: PRESIZE || null, sku: null, mode: 'fill', qty: '', runners: true, items: [], usable: 100 };
  var STEPNO = { veh: 1, size: 2, type: 2, amt: 3, order: 3, res: 4 };

  function vehLabel() {
    if (s.cat === 'cont') return t('cont') + ' ' + s.clen + ' ' + t('ft') + (s.ctype === 'hc' ? ' high cube' : s.ctype === 'pw' ? ' pallet-wide' : '');
    return s.vehLabel;
  }
  function steps() {
    var n = STEPNO[s.step], palDone = !!(s.sku || s.items.length);
    stepsEl.innerHTML = ['s1', 's2', 's3', 's4'].map(function (k, i) {
      var st = i + 1 === n ? 'is-on' : (i + 1 < n || (i === 1 && palDone && n > 2)) ? 'is-done' : '';
      return '<li class="' + st + '"' + (i + 1 === n ? ' aria-current="step"' : '') + '><span class="qpc-n">' + (st === 'is-done' ? ICON.check : i + 1) + '</span><span class="qpc-sl">' + t(k) + '</span></li>';
    }).join('');
  }
  var head = function (title, hint) { return '<div class="qpc-head"><h3 class="qpc-h" tabindex="-1">' + title + '</h3>' + (hint ? '<p class="qpc-hint">' + hint + '</p>' : '') + '</div>'; };
  var backBtn = function (to) { return '<button type="button" class="qpc-back" data-go="' + to + '">' + ICON.back + t('back') + '</button>'; };
  var opt = function (act, val, inner, sel, tag, extra) {
    return '<button type="button" class="qpc-opt' + (sel ? ' is-sel' : '') + '" data-act="' + act + '" data-v="' + val + '" aria-pressed="' + (sel ? 'true' : 'false') + '"' + (extra || '') + '>' + (tag ? '<span class="qpc-pop">' + tag + '</span>' : '') + inner + '</button>';
  };
  var pic = function (sku) { var u = img(sku); return u ? '<img src="' + u + '" alt="" width="320" height="213" loading="lazy" decoding="async">' : ''; };
  var chip = function (act, val, txt, sel, dis) { return '<button type="button" class="qpc-chip' + (sel ? ' is-sel' : '') + '" data-act="' + act + '" data-v="' + val + '" aria-pressed="' + (sel ? 'true' : 'false') + '"' + (dis ? ' disabled' : '') + '>' + txt + '</button>'; };

  var VIEW = {
    veh: function () {
      var more = '';
      if (s.cat === 'combi') more = '<div class="qpc-more"><p class="qpc-ml">' + t('combi') + '</p><div class="qpc-chips">' + chip('veh', 'combi77', t('c77'), s.veh === 'combi77') + chip('veh', 'combi78', t('c78'), s.veh === 'combi78') + '</div></div>';
      if (s.cat === 'cont') more = '<div class="qpc-more"><p class="qpc-ml">' + t('len') + '</p><div class="qpc-chips">' + ['20', '40', '45'].map(function (l) { return chip('clen', l, l + ' ' + t('ft'), s.clen === l); }).join('') + '</div>' +
        '<p class="qpc-ml">' + t('type') + '</p><div class="qpc-chips">' + ['std', 'hc', 'pw'].map(function (k) { return chip('ctype', k, t(k), s.ctype === k, k === 'pw' && s.clen !== '45'); }).join('') + '</div>' +
        '<button type="button" class="btn btn-primary btn-sm" data-act="contgo"' + (s.clen ? '' : ' disabled') + '>' + t('next') + ICON.arrow + '</button></div>';
      var card = function (k, sel) { return opt('cat', k, veh(k) + '<span class="qpc-ot"><b>' + t(k) + '</b><small>' + t(k + '_s') + '</small></span>', sel); };
      return head(t('t_veh'), t('h_veh')) + '<div class="qpc-grid qpc-c4">' + card('taut', s.cat === 'taut') + card('mega', s.cat === 'mega') + card('combi', s.cat === 'combi') + card('cont', s.cat === 'cont') + '</div>' + more +
        '<details class="qpc-space"' + (s.usable < 100 ? ' open' : '') + '><summary>' + t('space') + '</summary><label class="qpc-range"><span>' + t('space_s') + '</span><input type="range" min="10" max="100" step="5" value="' + s.usable + '" data-act="usable" aria-label="' + esc(t('space_s')) + '"><b id="qpc-uv">' + s.usable + '%</b></label></details>';
    },
    size: function () {
      return head(t('t_size'), t('h_size')) + '<div class="qpc-grid qpc-c5">' + SIZES.map(function (z) {
        return opt('size', z.id, pic(z.v[0][0]) + '<span class="qpc-ot"><b>' + dim(z) + '</b><small>' + sub(z) + '</small></span>', s.size === z.id);
      }).join('') + '</div><div class="qpc-nav">' + backBtn('veh') + '</div>';
    },
    type: function () {
      var z = SIZES.filter(function (x) { return x.id === s.size; })[0];
      return head(t('t_type') + ' <span class="qpc-dim">' + dim(z) + ' mm</span>', t('h_type')) + '<div class="qpc-grid qpc-c' + (z.v.length === 4 || z.v.length > 6 ? 4 : 3) + '">' + z.v.map(function (v) {
        return opt('sku', v[0], pic(v[0]) + '<span class="qpc-badges">' + badges(v[0]) + '</span><span class="qpc-ot"><b>' + t('b_' + v[1]) + '</b><small>' + (siteName(v[0]) ? esc(siteName(v[0])) : v[0]) + '</small></span>', s.sku === v[0]);
      }).join('') + '</div><div class="qpc-nav">' + backBtn('size') + '</div>';
    },
    amt: function () {
      var radio = function (v, title, body) {
        return '<label class="qpc-radio' + (s.mode === v ? ' is-sel' : '') + '"><input type="radio" name="qpc-m" data-act="mode" data-v="' + v + '"' + (s.mode === v ? ' checked' : '') + '><span class="qpc-rt"><b>' + title + '</b>' + body + '</span></label>';
      };
      return head(t('t_amt'), t('h_amt')) +
        '<div class="qpc-item">' + pic(s.sku) + '<div class="qpc-it"><span class="qpc-badges">' + badges(s.sku) + '</span><b>' + label(s.sku) + '</b><small>' + (siteName(s.sku) ? esc(siteName(s.sku)) + ' · ' : '') + s.sku + '</small></div><button type="button" class="qpc-link" data-go="size">' + t('other') + '</button></div>' +
        '<div class="qpc-radios">' + radio('fill', t('fill'), '<small>' + t('fill_s') + '</small>') +
        radio('num', t('num'), '<span class="qpc-qty"><input type="number" id="qpc-qty" min="1" inputmode="numeric" value="' + esc(s.qty) + '" aria-label="' + esc(t('num')) + '"' + (s.mode === 'num' ? '' : ' disabled') + '><span>' + t('pcs') + '</span></span>') + '</div>' +
        (isNest(s.sku) ? '<label class="qpc-check' + (s.runners ? ' is-sel' : '') + '"><input type="checkbox" data-act="runners"' + (s.runners ? ' checked' : '') + '><img src="' + RUNNER_IMG + '" alt="" width="96" height="64" loading="lazy"><span class="qpc-rt"><b>' + t('runners') + '</b><small>' + t('runners_s') + '</small></span></label>' : '') +
        '<div class="qpc-nav">' + backBtn(PRE && s.sku === PRE && !s.items.length ? 'veh' : 'type') + '<button type="button" class="btn btn-primary" data-act="add">' + t('add') + ICON.arrow + '</button></div>';
    },
    order: function () {
      return head(t('t_ord'), t('h_ord')) +
        '<div class="qpc-sum"><div class="qpc-sum-veh">' + veh(s.cat || 'taut') + '<span><small>' + t('vehicle') + '</small><b>' + vehLabel() + (s.usable < 100 ? ' · ' + s.usable + '%' : '') + '</b></span><button type="button" class="qpc-link" data-go="veh">' + t('change') + '</button></div>' +
        s.items.map(function (it, i) {
          return '<div class="qpc-item">' + pic(it.sku) + '<div class="qpc-it"><span class="qpc-badges">' + badges(it.sku) + '</span><b>' + label(it.sku) + '</b><small>' + it.sku + ' · ' + (it.mode === 'fill' ? t('asmany') : nf(it.qty) + ' ' + t('pcs')) + (isNest(it.sku) ? ' · ' + t(it.runners ? 'with_r' : 'no_r') : '') + '</small></div><button type="button" class="qpc-x" data-act="del" data-v="' + i + '" aria-label="' + esc(t('remove')) + '">' + ICON.x + '</button></div>';
        }).join('') + '</div>' +
        '<div class="qpc-nav"><button type="button" class="btn btn-outline btn-sm" data-go="size">' + ICON.plus + t('addmore') + '</button><button type="button" class="btn btn-primary" data-act="calc"' + (s.items.length ? '' : ' disabled') + '>' + t('calc') + ICON.arrow + '</button></div>';
    },
    res: function () {
      var r = lastResult, isC = s.cat === 'cont', tot = r ? r.totals : {}, rows = [];
      s.items.forEach(function (it) { var got = tot[it.sku] || 0, want = it.mode === 'num' ? it.qty : null; rows.push({ sku: it.sku, n: got, short: want !== null && got < want ? want : 0 }); });
      var rn = {}; Object.keys(tot).forEach(function (k) { if (runnerPallets[k]) rn[k] = tot[k]; });
      var unit = function (n) { return n === 1 ? t(isC ? 'container' : 'truck') : t(isC ? 'containers' : 'trucks'); };
      var placed = rows.some(function (x) { return x.n > 0; });
      var anyShort = rows.some(function (x) { return x.short; }) || !placed || (r && r.failed);
      var fixedAll = s.items.every(function (i) { return i.mode === 'num'; });
      var big = !r || !placed ? '<p class="qpc-big">–</p>' : fixedAll && r.trailerCount >= 1 && !anyShort
        ? '<p class="qpc-kicker">' + t('need') + '</p><p class="qpc-big">' + r.trailerCount + ' ' + unit(r.trailerCount) + '</p>'
        : rows.length === 1 ? '<p class="qpc-kicker">' + t('fits') + '</p><p class="qpc-big">' + nf(rows[0].n) + ' <span>' + t('pallets') + '</span></p>'
        : '<p class="qpc-kicker">' + t('fits') + '</p>';
      var list = rows.map(function (x) {
        return '<li>' + pic(x.sku) + '<b class="qpc-cnt">' + nf(x.n) + '<small>×</small></b><span class="qpc-it"><b>' + label(x.sku) + '</b><small>' + x.sku + (x.short ? ' · ' + t('onlyfit').replace('{n}', nf(x.n)).replace('{m}', nf(x.short)) : '') + '</small></span></li>';
      }).join('') + Object.keys(rn).map(function (k) {
        return '<li><img src="' + RUNNER_IMG + '" alt="" width="96" height="64" loading="lazy"><b class="qpc-cnt">' + nf(rn[k]) + '<small>×</small></b><span class="qpc-it"><b>' + t('runner_l') + '</b><small>' + runnerPallets[k].name + '</small></span></li>';
      }).join('');
      var quote = quoteHref(rows, isC);
      return '<div class="qpc-res"><div class="qpc-res-top"><div><p class="qpc-res-veh">' + veh(s.cat || 'taut') + '<span>' + vehLabel() + (s.usable < 100 ? ' · ' + s.usable + '%' : '') + '</span></p>' + big + '</div></div>' +
        (anyShort ? '<p class="qpc-warn">' + (placed ? t('warn_fit') : t('warn_none')) + '</p>' : '') +
        '<ul class="qpc-list">' + list + '</ul><p class="qpc-note">' + t('note') + '</p>' +
        '<div class="qpc-actions"><a class="btn btn-primary" href="' + quote + '">' + t('contact') + ICON.arrow + '</a><button type="button" class="btn btn-ghost-light btn-sm" data-act="copy">' + ICON.copy + '<span>' + t('copy') + '</span></button><button type="button" class="btn btn-ghost-light btn-sm" data-act="again">' + ICON.redo + t('again') + '</button></div>' +
        (r && r.plan ? '<details class="qpc-plan"><summary>' + t('plan') + '</summary><pre>' + esc(r.plan) + (r.alt ? '\n\n' + esc(r.alt) : '') + '</pre></details>' : '') + '</div>' +
        '<div class="qpc-nav">' + backBtn('order') + '</div>';
    }
  };

  /* quote button: the calculated load goes along to the quote form (update 28).
     ?items=SKU:qty,SKU:qty (site article numbers; the form rounds up to full stacks) and ?note=<summary for the message field> */
  function quoteHref(rows, isC) {
    var base = root.getAttribute('data-quote') || '#', items = [], lines = [];
    rows.forEach(function (x) {
      var it = s.items.filter(function (i) { return i.sku === x.sku; })[0], n = it && it.mode === 'num' ? it.qty : x.n;
      if (!n) return;
      var site = (x.sku === PRE && root.getAttribute('data-site')) || (CAT[x.sku] && CAT[x.sku].s) || x.sku;
      items.push(site + ':' + n);
      lines.push(nf(n) + ' x ' + label(x.sku) + ' (' + site + ')');
      if (it && isNest(x.sku) && it.runners) { var rs = NEST_RUNNER(x.sku); items.push(rs + ':' + n * 3); lines.push(nf(n * 3) + ' x ' + t('runner_l') + ' (' + rs + ')'); }
    });
    if (!items.length || base === '#') return base;
    var note = t('q_note').replace('{v}', vehLabel() + (s.usable < 100 ? ' (' + s.usable + '%)' : '')) + '\n' + lines.join('\n');
    return base + (base.indexOf('?') < 0 ? '?' : '&') + 'items=' + encodeURIComponent(items.slice(0, 6).join(',')) + '&note=' + encodeURIComponent(note);
  }

  function render() { steps(); main.innerHTML = VIEW[s.step](); }
  function go(step) {
    s.step = step; render();
    var h = main.querySelector('.qpc-h, .qpc-res'); if (h) { h.setAttribute('tabindex', '-1'); h.focus({ preventScroll: true }); }
    var top = root.getBoundingClientRect().top;
    if (top < 70 || top > window.innerHeight * .6) root.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  function afterVehicle() {
    if (s.items.length) return go('order');
    if (PRE) { s.sku = PRE; s.mode = 'fill'; s.qty = ''; s.runners = true; return go('amt'); }
    go(s.size ? 'type' : 'size');
  }

  /* ---- calculate: fill the engine's hidden inputs and run it (exactly like the original calculator) ---- */
  function runCalc() {
    var q = function (id) { return document.getElementById(id); };
    q('trailerSelect').value = s.veh;
    q('trailerPercentage').value = s.usable;
    q('palletRowsContainer').innerHTML = '';
    s.items.forEach(function (it) {
      addPalletRow();
      var row = q('palletRowsContainer').lastElementChild;
      row.querySelector('.pallet-select').value = pallets.filter(function (p) { return p.id === it.sku; })[0].name;
      row.querySelector('.pallet-amount').value = it.mode === 'fill' ? 'fill' : it.qty;
    });
    checkRunnersVisibility();
    s.items.forEach(function (it, i) { var sel = q('runnerSelect_' + i); if (sel) sel.value = it.runners ? NEST_RUNNER(it.sku) : 'none'; });
    lastResult = null;
    calculateLoad();
  }

  root.addEventListener('click', function (e) {
    var g = e.target.closest('[data-go]'); if (g) { go(g.getAttribute('data-go')); return; }
    var b = e.target.closest('[data-act]'); if (!b || b.disabled) return;
    var a = b.getAttribute('data-act'), v = b.getAttribute('data-v');
    if (a === 'cat') {
      s.cat = v; s.veh = null;
      if (v === 'taut' || v === 'mega') { s.veh = v === 'taut' ? 'tautliner' : v; s.vehLabel = t(v); afterVehicle(); }
      else { render(); var m = main.querySelector('.qpc-more'); if (m) m.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }
    }
    else if (a === 'veh') { s.veh = v; s.vehLabel = t('combi') + ' ' + b.textContent; afterVehicle(); }
    else if (a === 'clen') { s.clen = v; if (v !== '45' && s.ctype === 'pw') s.ctype = 'std'; render(); }
    else if (a === 'ctype') { s.ctype = v; render(); }
    else if (a === 'contgo') { s.veh = 'container' + s.clen + (s.ctype === 'hc' ? 'hc' : s.ctype === 'pw' ? 'pw' : ''); afterVehicle(); }
    else if (a === 'size') { s.size = v; go('type'); }
    else if (a === 'sku') { s.sku = v; s.mode = 'fill'; s.qty = ''; s.runners = true; go('amt'); }
    else if (a === 'add') {
      var qi = document.getElementById('qpc-qty'), n = parseInt(qi.value, 10);
      if (s.mode === 'num' && !(n > 0)) { qi.focus(); qi.classList.add('is-err'); return; }
      s.items.push({ sku: s.sku, mode: s.mode, qty: s.mode === 'num' ? n : 0, runners: isNest(s.sku) && s.runners }); go('order');
    }
    else if (a === 'del') { s.items.splice(+v, 1); render(); }
    else if (a === 'calc') { runCalc(); go('res'); }
    else if (a === 'again') { s.items = []; s.cat = s.veh = null; s.clen = null; s.sku = null; s.size = PRESIZE || null; go('veh'); }
    else if (a === 'copy') {
      var txt = [vehLabel()].concat([].slice.call(main.querySelectorAll('.qpc-list li')).map(function (li) { return li.innerText.replace(/\s*\n+\s*/g, ' '); })).join('\n');
      var done = function () { var sp = b.querySelector('span'); if (sp) sp.textContent = t('copied'); };
      try { navigator.clipboard.writeText(txt).then(done, function () {}); } catch (err) {}
    }
  });
  root.addEventListener('change', function (e) {
    var el = e.target, a = el.getAttribute('data-act'); if (!a) return;
    if (a === 'mode') { var q = document.getElementById('qpc-qty'); if (q) s.qty = q.value; s.mode = el.getAttribute('data-v'); render(); if (s.mode === 'num') document.getElementById('qpc-qty').focus(); }
    else if (a === 'runners') { s.runners = el.checked; render(); }
  });
  root.addEventListener('input', function (e) {
    if (e.target.getAttribute('data-act') === 'usable') { s.usable = +e.target.value; document.getElementById('qpc-uv').textContent = s.usable + '%'; }
    if (e.target.id === 'qpc-qty') { s.qty = e.target.value; e.target.classList.remove('is-err'); }
  });
  root.classList.add('is-ready');
  render();
})();
