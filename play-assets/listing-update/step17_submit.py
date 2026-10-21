"""Publishing overview: verify ONLY our store-listing change is queued, then
send for review."""
from playwright.sync_api import sync_playwright
from _cdp import shot

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages if "store-listings/default/edit" in pg.url), None)

    btn = page.get_by_role("button", name="Go to overview")
    if btn.count():
        btn.first.click()
    else:
        page.goto("https://play.google.com/console/u/0/developers/9052149026359320771"
                  "/app/4975171430765358175/publishing", wait_until="domcontentloaded",
                  timeout=90000)
    page.wait_for_timeout(7000)
    print("URL:", page.url)
    body = page.evaluate("() => document.body.innerText")
    print("PAGE TEXT:\n", body[:2500])
    shot(page, "17-publishing-overview")
