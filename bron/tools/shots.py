import sys, asyncio
from playwright.async_api import async_playwright
BASE='http://localhost:8765'
async def main(pages, w, h, prefix, full=True):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1)
        pg = await ctx.new_page()
        errs=[]
        pg.on('console', lambda m: errs.append(m.text) if m.type=='error' else None)
        pg.on('pageerror', lambda e: errs.append(str(e)))
        for name, path in pages:
            await pg.goto(BASE+path, wait_until='networkidle')
            await pg.evaluate("document.querySelectorAll('.reveal').forEach(e=>e.classList.add('is-in'))")
            await pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
            await pg.evaluate("async()=>{for(let y=0;y<document.body.scrollHeight;y+=600){window.scrollTo(0,y);await new Promise(r=>setTimeout(r,60));}window.scrollTo(0,0);}")
            await pg.wait_for_timeout(500)
            await pg.wait_for_timeout(300)
            await pg.screenshot(path=f'/home/claude/shots/{prefix}-{name}.png', full_page=full)
        print('errors:', errs)
        await b.close()
if __name__=='__main__':
    import json
    pages=json.loads(sys.argv[1]); w=int(sys.argv[2]); h=int(sys.argv[3]); prefix=sys.argv[4]; full=sys.argv[5]=='1' if len(sys.argv)>5 else True
    asyncio.run(main(pages,w,h,prefix,full))
