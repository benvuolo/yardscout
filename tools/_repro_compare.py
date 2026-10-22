"""Reproduce the owner's 'alternator compare does nothing' report on production."""
import asyncio, sys
from playwright.async_api import async_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://yardscout.io"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/repro"
VIEW = {"width": 1280, "height": 800}
if len(sys.argv) > 3 and sys.argv[3] == "narrow":
    VIEW = {"width": 390, "height": 844}


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport=VIEW)
        msgs = []
        pg.on("console", lambda m: msgs.append(f"[{m.type}] {m.text}"))
        pg.on("pageerror", lambda e: msgs.append(f"[pageerror] {e}"))
        await pg.goto(BASE, wait_until="domcontentloaded")
        # set a zip like a real user (SLC per the screenshot: 211 yards near)
        await pg.evaluate("localStorage.setItem('jh_zip','84101')")
        await pg.reload(wait_until="domcontentloaded")
        await pg.wait_for_timeout(6000)
        await pg.click('.tab[data-tab="yards"]')
        await pg.wait_for_timeout(1000)
        await pg.fill('#compare-input', 'alternator')
        await pg.wait_for_timeout(500)
        await pg.screenshot(path=f"{OUT}_typed.png")
        await pg.click('#compare-go')
        await pg.wait_for_timeout(1500)
        await pg.screenshot(path=f"{OUT}_after_click.png")
        state = await pg.evaluate("""() => ({
            pricesSheetOpen: document.getElementById('prices-sheet')?.classList.contains('open'),
            openSheets: [...document.querySelectorAll('.open')].map(e => e.id || e.className).slice(0,10),
            isPro: localStorage.getItem('jh_pro'),
            pricesTitle: document.getElementById('prices-title')?.textContent,
            upgradeTitle: document.getElementById('upgrade-title')?.textContent,
        })""")
        print("STATE:", state)
        print("CONSOLE:", *msgs[-20:], sep="\n  ")
        await b.close()

asyncio.run(main())
