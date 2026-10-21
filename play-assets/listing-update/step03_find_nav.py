"""Load a known-good app page and dump left-nav links to find the real
store-listing route."""
from playwright.sync_api import sync_playwright
from _cdp import shot

APP = "https://play.google.com/console/u/0/developers/9052149026359320771/app/4975171430765358175"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages
                 if "play.google.com/console" in pg.url
                 and "submission-activity" not in pg.url), None)
    page.goto(APP + "/publishing", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(7000)
    print("URL:", page.url)
    links = page.evaluate("""() =>
        [...document.querySelectorAll('a[href]')]
        .map(a => ({t: a.textContent.replace(/\\s+/g,' ').trim(), h: a.getAttribute('href')}))
        .filter(x => x.t)""")
    for l in links:
        print(f"{l['t'][:60]} => {l['h'][:120]}")
    shot(page, "03-publishing-nav")
