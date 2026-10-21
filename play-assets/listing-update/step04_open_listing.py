"""Open Store listings, then click into the main store listing editor."""
from playwright.sync_api import sync_playwright
from _cdp import shot

APP = "https://play.google.com/console/u/0/developers/9052149026359320771/app/4975171430765358175"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages
                 if "play.google.com/console" in pg.url
                 and "submission-activity" not in pg.url), None)
    page.goto(APP + "/store-listings", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(6000)
    print("URL:", page.url)
    shot(page, "04-store-listings")
    links = page.evaluate("""() =>
        [...document.querySelectorAll('a[href]')]
        .map(a => ({t: a.textContent.replace(/\\s+/g,' ').trim(), h: a.getAttribute('href')}))
        .filter(x => /listing/i.test(x.h) && !/store-listings$/.test(x.h))""")
    for l in links:
        print(f"{l['t'][:60]} => {l['h'][:140]}")
