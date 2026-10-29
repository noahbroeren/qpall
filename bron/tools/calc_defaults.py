"""Standard loads for the product pages: how many pallets fit in a truck / container.

Runs the calculator's own engine (static/calc/engine.js, unchanged) in headless Chromium, exactly as
the calculator on the site does for "Zoveel mogelijk" (fill) with one pallet type, no runners and
100 % of the space. Writes data/calc-defaults.json: {calc id: {vehicle: pallets}}.

Run after a change in engine.js:  python3 tools/calc_defaults.py
"""
import json, os, re
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = open(os.path.join(ROOT, 'static/calc/engine.js'), encoding='utf-8').read()
VEHICLES = ['tautliner', 'mega', 'container20', 'container40hc']

HIDDEN = """<div>
<select id="trailerSelect">""" + ''.join(f'<option value="{v}"></option>' for v in
    ['tautliner', 'mega', 'combi77', 'combi78', 'container20', 'container20hc', 'container40', 'container40hc',
     'container45', 'container45hc', 'container45pw']) + """</select>
<input type="number" id="trailerPercentage" value="100">
<select id="strategySelect"><option value="fair_split"></option></select>
<div id="palletRowsContainer"></div><section class="qpc-config"></section>
<section id="runnersSection"><div id="dynamicRunnerSelections"></div></section>
<section id="resultsSection"><pre id="outputResult"></pre><div id="altPlanSection"><pre id="altOutputResult"></pre></div></section>
</div>"""

HARNESS = """
window.QPCT = {
  ids: pallets.filter(p => !p.isRunner).map(p => p.id),
  fill: function (sku, veh) {
    const q = id => document.getElementById(id);
    q('trailerSelect').value = veh; q('trailerPercentage').value = 100;
    q('palletRowsContainer').innerHTML = '';
    addPalletRow();
    const row = q('palletRowsContainer').lastElementChild;
    row.querySelector('.pallet-select').value = pallets.find(p => p.id === sku).name;
    row.querySelector('.pallet-amount').value = 'fill';
    checkRunnersVisibility();
    const sel = q('runnerSelect_0'); if (sel) sel.value = 'none';
    lastResult = null; calculateLoad();
    return lastResult ? (lastResult.totals[sku] || 0) : null;
  }
};"""


def main():
    html = f'<!doctype html><meta charset="utf-8"><body>{HIDDEN}<script>window.alert=function(m){{console.log("ALERT",m)}};(function(){{{ENGINE}\n{HARNESS}}})();</script></body>'
    out = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.on('console', lambda m: print('console:', m.text))
        pg.set_content(html)
        ids = pg.evaluate('QPCT.ids')
        for sku in ids:
            out[sku] = {v: pg.evaluate('([s, v]) => QPCT.fill(s, v)', [sku, v]) for v in VEHICLES}
            print(sku, out[sku])
        b.close()
    json.dump(out, open(os.path.join(ROOT, 'data/calc-defaults.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
