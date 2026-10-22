"""Edge cases: 250mi radius footnotes, keyword-map part, state filter."""
import asyncio, sys
from playwright.async_api import async_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://yardscout.io"


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1280, "height": 800})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(BASE, wait_until="domcontentloaded")
        await pg.evaluate(
            "localStorage.setItem('jh_zip','45202'); localStorage.setItem('jh_radius','250')")
        await pg.reload(wait_until="domcontentloaded")
        await pg.wait_for_timeout(6000)
        await pg.click('.tab[data-tab="yards"]')
        await pg.wait_for_timeout(1000)

        # keyword-map canonical part that no chain spells literally
        await pg.click('#compare-input')
        await pg.type('#compare-input', 'hid head', delay=30)
        await pg.wait_for_timeout(600)
        sugg = await pg.eval_on_selector_all(
            '.compare-suggest-item', "els => els.map(e => e.textContent.trim().replace(/\\s+/g,' '))")
        print("suggestions for 'hid head':", sugg)
        if sugg:
            await pg.locator('.compare-suggest-item').first.dispatch_event('mousedown')
            await pg.wait_for_timeout(1200)
            rows = await pg.locator('#prices-body .compare-row').count()
            missing = await pg.eval_on_selector_all(
                '.compare-missing', "els => els.map(e => e.textContent.trim())")
            print(f"hid-headlight rows={rows}")
            for m in missing: print("  footnote:", m[:160])
            await pg.screenshot(path="/tmp/ys_prod_edge_1_kwpart.png")
            await pg.click('#prices-close')
            await pg.wait_for_timeout(400)

        # state filter narrows (NV vs UT at 250mi from SLC)
        states = await pg.eval_on_selector_all(
            '#yards-filter-state option', "els => els.map(e => e.textContent).filter(t => !t.startsWith('All'))")
        print("state options:", states)
        vals = await pg.eval_on_selector_all(
            '#yards-filter-state option', "els => els.map(e => e.value).filter(Boolean)")
        if vals and len(vals) > 1:
            await pg.select_option('#yards-filter-state', vals[1])
            await pg.wait_for_timeout(800)
            cards = await pg.eval_on_selector_all(
                '.yard-card .car-name', "els => els.map(e => e.textContent)")
            print("NV yards shown:", cards)
            await pg.fill('#compare-input', 'alternator')
            await pg.click('#compare-go')
            await pg.wait_for_timeout(1200)
            yards = await pg.eval_on_selector_all(
                '#prices-body .compare-row strong', "els => els.map(e => e.textContent)")
            print("NV-filtered compare yards:", yards)
            await pg.screenshot(path="/tmp/ys_prod_edge_2_statefilter.png")
        print("page errors:", errs or "none")
        await b.close()

asyncio.run(main())
