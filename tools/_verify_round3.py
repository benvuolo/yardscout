"""Round 3 verify: cleaned coverage-sorted dropdown, yards zip input, 500mi tier.
Pro checks use the jh_pro localStorage entitlement toggle (source=account)."""
import asyncio, sys
from playwright.async_api import async_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8777"
TAG = sys.argv[2] if len(sys.argv) > 2 else "local"


async def boot(pg, zipc='84101', pro=False):
    await pg.goto(BASE, wait_until="domcontentloaded")
    s = f"localStorage.setItem('jh_zip','{zipc}');"
    if pro:
        s += "localStorage.setItem('jh_pro','1');localStorage.setItem('jh_pro_source','account');"
    await pg.evaluate(s)
    await pg.reload(wait_until="domcontentloaded")
    await pg.wait_for_timeout(6000)
    await pg.click('.tab[data-tab="yards"]')
    await pg.wait_for_timeout(1000)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        errs = []

        # ---- FREE desktop: dropdown cleanliness + coverage sort, zip, 500 gate
        pg = await b.new_page(viewport={"width": 1280, "height": 800})
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await boot(pg, pro=False)

        # 1. dropdown: top of browse list + no numeric junk anywhere
        await pg.click('#compare-input')
        await pg.wait_for_timeout(800)
        tops = await pg.eval_on_selector_all('.compare-suggest-item',
            "els => els.slice(0,10).map(e => e.textContent.trim().replace(/\\s+/g,' '))")
        allnames = await pg.eval_on_selector_all('.compare-suggest-item .csi-name',
            "els => els.map(e => e.textContent.trim())")
        junk = [n for n in allnames if n.replace('.', '').replace(',', '').replace('$', '').replace('-', '').replace(' ', '').isdigit()]
        counts = await pg.eval_on_selector_all('.compare-suggest-item .csi-count',
            "els => els.map(e => parseInt(e.textContent))")
        sorted_desc = all(counts[i] >= counts[i+1] for i in range(min(len(counts), 200) - 1))
        print(f"[{TAG}] dropdown: total={len(allnames)} numeric_junk={junk[:5] or 'NONE'} "
              f"coverage_sorted={sorted_desc}")
        print(f"[{TAG}] top10: {tops}")
        await pg.screenshot(path=f"/tmp/ys3_{TAG}_dropdown_top.png")
        await pg.keyboard.press('Escape')

        # merged-variant sanity: 'tail light' still finds and compares yards
        await pg.fill('#compare-input', 'tail light')
        await pg.wait_for_timeout(500)
        tl = await pg.eval_on_selector_all('.compare-suggest-item',
            "els => els.slice(0,3).map(e => e.textContent.trim().replace(/\\s+/g,' '))")
        await pg.locator('.compare-suggest-item').first.dispatch_event('mousedown')
        await pg.wait_for_timeout(1200)
        tl_rows = await pg.locator('#prices-body .compare-row').count()
        print(f"[{TAG}] 'tail light' suggestions={tl} compare_rows={tl_rows}")
        await pg.click('#prices-close')
        await pg.wait_for_timeout(300)

        # 2. zip input re-centers: SLC -> Cincinnati
        await pg.fill('#yards-zip', '45202')
        await pg.wait_for_timeout(2500)
        state = await pg.evaluate("""() => ({
            liveZip: document.getElementById('live-zip').value,
            storedZip: localStorage.getItem('jh_zip'),
            firstYard: document.querySelector('.yard-card .car-name')?.textContent,
            firstDist: document.querySelector('.yard-card .dist')?.textContent,
        })""")
        print(f"[{TAG}] zip recenter 45202: {state}")
        await pg.screenshot(path=f"/tmp/ys3_{TAG}_zip_recenter.png")

        # 3. free 500mi gate on Yards select
        await pg.select_option('#yards-radius', '500')
        await pg.wait_for_timeout(800)
        g1 = await pg.evaluate("""() => ({
            upgradeOpen: document.getElementById('upgrade-sheet').classList.contains('open'),
            yardsRadius: document.getElementById('yards-radius').value,
        })""")
        print(f"[{TAG}] FREE yards 500mi gate: {g1}")
        await pg.screenshot(path=f"/tmp/ys3_{TAG}_500_gate.png")
        await pg.click('#upgrade-close')
        await pg.wait_for_timeout(300)
        # free 500mi gate on Live select too
        await pg.click('.tab[data-tab="live"]')
        await pg.wait_for_timeout(600)
        await pg.evaluate("document.querySelector('.filter-toggle')?.click()")
        await pg.wait_for_timeout(400)
        await pg.select_option('#live-radius', '500')
        await pg.wait_for_timeout(800)
        g2 = await pg.evaluate("""() => ({
            upgradeOpen: document.getElementById('upgrade-sheet').classList.contains('open'),
            liveRadius: document.getElementById('live-radius').value,
        })""")
        print(f"[{TAG}] FREE live 500mi gate: {g2}")
        await pg.close()

        # ---- PRO: 500mi works on both tabs
        pg = await b.new_page(viewport={"width": 1280, "height": 800})
        pg.on("pageerror", lambda e: errs.append("pro:" + str(e)))
        await boot(pg, zipc='45202', pro=True)
        await pg.select_option('#yards-radius', '500')
        await pg.wait_for_timeout(1000)
        pro1 = await pg.evaluate("""() => ({
            upgradeOpen: document.getElementById('upgrade-sheet').classList.contains('open'),
            yardsRadius: document.getElementById('yards-radius').value,
            liveRadius: document.getElementById('live-radius').value,
            statWithin: document.querySelector('#yards-stats-bar .stat-card:nth-child(2) .value-sm')?.textContent,
            yardCards: document.querySelectorAll('.yard-card').length,
        })""")
        await pg.fill('#compare-input', 'alternator')
        await pg.click('#compare-go')
        await pg.wait_for_timeout(1500)
        rows500 = await pg.locator('#prices-body .compare-row').count()
        await pg.screenshot(path=f"/tmp/ys3_{TAG}_pro_500.png")
        print(f"[{TAG}] PRO 500mi: {pro1} compare_rows={rows500}")
        await pg.close()

        # ---- narrow 390px: dropdown + new toolbar layout
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errs.append("narrow:" + str(e)))
        await boot(pg, pro=False)
        await pg.click('#compare-input')
        await pg.wait_for_timeout(800)
        n = await pg.locator('.compare-suggest-item').count()
        await pg.screenshot(path=f"/tmp/ys3_{TAG}_narrow_dropdown.png")
        await pg.keyboard.press('Escape')
        await pg.screenshot(path=f"/tmp/ys3_{TAG}_narrow_toolbar.png")
        print(f"[{TAG}] narrow dropdown entries={n}")
        print(f"[{TAG}] page errors: {errs or 'none'}")
        await b.close()

asyncio.run(main())
