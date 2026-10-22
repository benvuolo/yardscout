"""Verify the Yards-tab part compare: type-ahead, free compare sheet,
chain/state filters narrowing the comparison. Desktop + narrow viewports."""
import asyncio, sys
from playwright.async_api import async_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8777"
TAG = sys.argv[2] if len(sys.argv) > 2 else "local"


async def settle(pg, ms=1200):
    await pg.wait_for_timeout(ms)


async def run(viewport, label):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport=viewport)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(BASE, wait_until="domcontentloaded")
        await pg.evaluate("localStorage.setItem('jh_zip','84101')")
        await pg.reload(wait_until="domcontentloaded")
        await pg.wait_for_timeout(6000)  # inventory + price lists load
        await pg.click('.tab[data-tab="yards"]')
        await settle(pg)

        # 1. type-ahead appears while typing
        await pg.click('#compare-input')
        await pg.type('#compare-input', 'alternator', delay=40)
        await settle(pg, 800)
        suggest_visible = await pg.is_visible('#compare-suggest')
        n_suggestions = await pg.locator('.compare-suggest-item').count()
        await pg.screenshot(path=f"/tmp/ys_{TAG}_{label}_1_typeahead.png")

        # 2. pick the first suggestion -> compare sheet opens, multi-yard
        if n_suggestions:
            await pg.locator('.compare-suggest-item').first.dispatch_event('mousedown')
        else:
            await pg.click('#compare-go')
        await settle(pg)
        sheet_open = await pg.evaluate(
            "document.getElementById('prices-sheet').classList.contains('open')")
        upgrade_open = await pg.evaluate(
            "document.getElementById('upgrade-sheet').classList.contains('open')")
        rows = await pg.locator('#prices-body .compare-row').count()
        title = await pg.text_content('#prices-title')
        sub = await pg.text_content('#prices-sub')
        prices = await pg.eval_on_selector_all(
            '#prices-body .compare-row',
            "els => els.slice(0,5).map(e => e.textContent.trim().replace(/\\s+/g,' '))")
        await pg.screenshot(path=f"/tmp/ys_{TAG}_{label}_2_compare.png")

        # 3. nearest-first toggle
        if rows > 1:
            await pg.click('#prices-sort-dist')
            await settle(pg, 400)
            await pg.screenshot(path=f"/tmp/ys_{TAG}_{label}_3_nearest.png")
        await pg.click('#prices-close')
        await settle(pg, 400)

        # 4. chain filter narrows comparison
        chains = await pg.eval_on_selector_all(
            '#yards-filter-chain option', "els => els.map(e => e.value).filter(Boolean)")
        chain_rows = None
        chain_used = None
        bad_chain_rows = []
        if chains:
            chain_used = next((c for c in chains if c.lower().startswith('pick-n-pull')), chains[0])
            await pg.select_option('#yards-filter-chain', chain_used)
            await settle(pg, 800)
            await pg.screenshot(path=f"/tmp/ys_{TAG}_{label}_4_chainfilter.png")
            await pg.fill('#compare-input', 'alternator')
            await pg.click('#compare-go')
            await settle(pg)
            chain_rows = await pg.locator('#prices-body .compare-row').count()
            yard_names = await pg.eval_on_selector_all(
                '#prices-body .compare-row strong', "els => els.map(e => e.textContent)")
            bad_chain_rows = [y for y in yard_names if not y.lower().startswith(chain_used.split(' ')[0].lower())]
            await pg.screenshot(path=f"/tmp/ys_{TAG}_{label}_5_chaincompare.png")
            await pg.click('#prices-close')
            await settle(pg, 300)
            await pg.select_option('#yards-filter-chain', '')

        print(f"--- {label} @ {BASE} ---")
        print(f"typeahead visible={suggest_visible} suggestions={n_suggestions}")
        print(f"sheet_open={sheet_open} upgrade_open={upgrade_open} rows={rows}")
        print(f"title={title!r}")
        print(f"sub={sub!r}")
        for pr in prices: print("  row:", pr)
        print(f"chain filter: {chain_used!r} -> rows={chain_rows} wrong-chain={bad_chain_rows}")
        print(f"page errors: {errs or 'none'}")
        await b.close()


asyncio.run(run({"width": 1280, "height": 800}, "desktop"))
asyncio.run(run({"width": 390, "height": 844}, "narrow"))
