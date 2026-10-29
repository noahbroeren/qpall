import asyncio
from playwright.async_api import async_playwright
B='http://localhost:8765'
P='/kunststof-pallets/1200-x-800-mm/kunststof-pallet-1200-x-800-x-145-open-dek-3-onderlatten-medium/'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        errs=[]
        c = await b.new_context(viewport={'width':1440,'height':900})
        pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'/', wait_until='networkidle')
        await pg.hover('button[aria-controls=mm-pallets]'); await pg.wait_for_timeout(600)
        await pg.screenshot(path='/home/claude/shots/mega.png')
        await pg.mouse.move(700,600); await pg.wait_for_timeout(400)
        await pg.hover('button[aria-controls=mm-about]'); await pg.wait_for_timeout(600)
        await pg.screenshot(path='/home/claude/shots/mega-about.png', clip={'x':0,'y':0,'width':1440,'height':520})
        await pg.goto(B+P+'#specificaties', wait_until='networkidle'); await pg.wait_for_timeout(500)
        el = await pg.query_selector('#details'); await el.screenshot(path='/home/claude/shots/specs.png')
        await pg.click('#t-uitvoeringen'); await pg.wait_for_timeout(300)
        await el.screenshot(path='/home/claude/shots/variants.png')
        await pg.click('#t-draagvermogen'); await pg.wait_for_timeout(300)
        await el.screenshot(path='/home/claude/shots/load.png')
        # search
        await pg.keyboard.press('/'); await pg.wait_for_timeout(200); await pg.keyboard.type('1200x1000 heavy'); await pg.wait_for_timeout(800)
        await pg.screenshot(path='/home/claude/shots/search.png')
        await pg.keyboard.press('Escape')
        # compare
        await pg.goto(B+'/kunststof-pallets/1200-x-1000-mm/?class=heavy&f=rack', wait_until='networkidle'); await pg.wait_for_timeout(400)
        cbs = await pg.query_selector_all('.pcard:not([hidden]) input[data-cmp]')
        for cb in cbs[:3]: await cb.check()
        await pg.wait_for_timeout(300)
        await pg.screenshot(path='/home/claude/shots/filter.png')
        await pg.click('[data-cmp-open]'); await pg.wait_for_timeout(400)
        await pg.screenshot(path='/home/claude/shots/compare.png')
        # mobile
        m = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        mp = await m.new_page(); mp.on('pageerror', lambda e: errs.append(str(e)))
        await mp.goto(B+'/', wait_until='networkidle')
        await mp.evaluate("document.querySelectorAll('.reveal').forEach(e=>e.classList.add('is-in'));document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
        await mp.wait_for_timeout(800)
        await mp.screenshot(path='/home/claude/shots/m-home.png', full_page=True)
        await mp.click('.burger'); await mp.wait_for_timeout(500)
        await mp.screenshot(path='/home/claude/shots/m-menu.png')
        await mp.goto(B+P, wait_until='networkidle'); await mp.wait_for_timeout(500)
        await mp.screenshot(path='/home/claude/shots/m-prod.png', full_page=True)
        await mp.goto(B+'/kunststof-pallets/', wait_until='networkidle'); await mp.wait_for_timeout(500)
        await mp.click('.f-toggle'); await mp.wait_for_timeout(300)
        await mp.screenshot(path='/home/claude/shots/m-filters.png')
        # overflow check
        for path in ['/', P, '/kunststof-pallets/', '/over-q-pall/', '/en/', '/offerte-aanvraag/', '/kennisbank/kunststof-pallet-prijs/']:
            await mp.goto(B+path, wait_until='networkidle')
            sw = await mp.evaluate('document.documentElement.scrollWidth')
            print('mobile scrollWidth', path, sw)
        print('errors', errs)
        await b.close()
asyncio.run(main())
