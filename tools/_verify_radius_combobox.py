"""Verify: (a) free-tier Within gate in Yards tab + compare respecting radius,
(b) Pro 'any distance' via the entitlement localStorage toggle (jh_pro=1 +
jh_pro_source=account — the same local-state path the boot entitlement check
re-grants through), (c) parts combobox browse/filter/select, desktop + 390px."""
import asyncio, sys
from playwright.async_api import async_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8777"
TAG = sys.argv[2] if len(sys.argv) > 2 else "local"


async def boot(pg, pro=False):
    await pg.goto(BASE, wait_until="domcontentloaded")
    script = "localStorage.setItem('jh_zip','84101');"
    if pro:
        script += "localStorage.setItem('jh_pro','1');localStorage.setItem('jh_pro_source','account');"
    await pg.evaluate(script)
    await pg.reload(wait_until="domcontentloaded")
    await pg.wait_for_timeout(6000)
    await pg.click('.tab[data-tab="yards"]')
    await pg.wait_for_timeout(1000)


async def compare_rows(pg, term):
    await pg.fill('#compare-input', term)
    await pg.click('#compare-go')
    await pg.wait_for_timeout(1200)
    n = await pg.locator('#prices-body .compare-row').count()
    sub = await pg.text_content('#prices-sub')
    await pg.click('#prices-close')
    await pg.wait_for_timeout(400)
    return n, sub


async def run(viewport, label):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        errs = []

        # ---------- FREE TIER ----------
        pg = await b.new_page(viewport=viewport)
        pg.on("pageerror", lambda e: errs.append("free:" + str(e)))
        await boot(pg, pro=False)

        # gate: choosing 'any distance' snaps back + upgrade sheet
        await pg.select_option('#yards-radius', '')
        await pg.wait_for_timeout(800)
        gate = await pg.evaluate("""() => ({
            upgradeOpen: document.getElementById('upgrade-sheet').classList.contains('open'),
            yardsRadius: document.getElementById('yards-radius').value,
            liveRadius: document.getElementById('live-radius').value,
        })""")
        await pg.screenshot(path=f"/tmp/ys2_{TAG}_{label}_free_gate.png")
        print(f"[{label}] FREE gate: {gate}")
        await pg.click('#upgrade-close')
        await pg.wait_for_timeout(400)

        # compare respects radius: 100 mi vs 250 mi row counts
        await pg.select_option('#yards-radius', '100')
        await pg.wait_for_timeout(600)
        n100, _ = await compare_rows(pg, 'alternator')
        await pg.select_option('#yards-radius', '250')
        await pg.wait_for_timeout(600)
        n250, sub250 = await compare_rows(pg, 'alternator')
        print(f"[{label}] FREE compare rows: 100mi={n100} 250mi={n250} ({sub250!r})")

        # stat card radius + live select stayed synced
        sync = await pg.evaluate("""() => ({
            yards: document.getElementById('yards-radius').value,
            live: document.getElementById('live-radius').value,
            stored: localStorage.getItem('jh_radius'),
        })""")
        print(f"[{label}] FREE sync after changes: {sync}")

        # combobox: tap-to-browse full list
        await pg.fill('#compare-input', '')
        await pg.click('#compare-input')
        await pg.wait_for_timeout(700)
        browse_n = await pg.locator('.compare-suggest-item').count()
        first = await pg.locator('.compare-suggest-item').first.text_content() if browse_n else None
        await pg.screenshot(path=f"/tmp/ys2_{TAG}_{label}_combobox_browse.png")
        # type to filter
        await pg.type('#compare-input', 'alt', delay=40)
        await pg.wait_for_timeout(500)
        filt_n = await pg.locator('.compare-suggest-item').count()
        filt = await pg.eval_on_selector_all('.compare-suggest-item .csi-name',
            "els => els.slice(0,5).map(e => e.textContent)")
        await pg.screenshot(path=f"/tmp/ys2_{TAG}_{label}_combobox_filter.png")
        # select -> comparison opens
        await pg.locator('.compare-suggest-item').first.dispatch_event('mousedown')
        await pg.wait_for_timeout(1000)
        picked_rows = await pg.locator('#prices-body .compare-row').count()
        await pg.click('#prices-close')
        await pg.wait_for_timeout(300)
        # garbage text: no dead-end sheet
        await pg.fill('#compare-input', 'zzzzqq')
        await pg.wait_for_timeout(400)
        nomatch = await pg.locator('.compare-suggest-empty').count()
        await pg.click('#compare-go')
        await pg.wait_for_timeout(700)
        sheet_after_garbage = await pg.evaluate(
            "document.getElementById('prices-sheet').classList.contains('open')")
        print(f"[{label}] combobox: browse={browse_n} (first={first and first.strip()!r}) "
              f"filter'alt'={filt_n} {filt} picked_rows={picked_rows} "
              f"nomatch_row={nomatch} sheet_after_garbage={sheet_after_garbage}")
        await pg.close()

        # ---------- PRO (localStorage entitlement toggle) ----------
        pg = await b.new_page(viewport=viewport)
        pg.on("pageerror", lambda e: errs.append("pro:" + str(e)))
        await boot(pg, pro=True)
        await pg.select_option('#yards-radius', '')
        await pg.wait_for_timeout(1000)
        pro_state = await pg.evaluate("""() => ({
            upgradeOpen: document.getElementById('upgrade-sheet').classList.contains('open'),
            yardsRadius: document.getElementById('yards-radius').value,
            statWithin: document.querySelector('#yards-stats-bar .stat-card:nth-child(2) .value-sm')?.textContent,
            yardCards: document.querySelectorAll('.yard-card').length,
        })""")
        n_any, sub_any = await compare_rows(pg, 'alternator')
        await pg.screenshot(path=f"/tmp/ys2_{TAG}_{label}_pro_anydistance.png")
        print(f"[{label}] PRO any-distance: {pro_state} compare_rows={n_any} ({sub_any!r})")
        print(f"[{label}] page errors: {errs or 'none'}")
        await b.close()


asyncio.run(run({"width": 1280, "height": 800}, "desktop"))
asyncio.run(run({"width": 390, "height": 844}, "narrow"))
