"""Pre-flight for the interchange listing update: read-only look at the
Publishing overview in OUR OWN tab (never the release worker's tabs) to
confirm the vc9 submission state and that no unsent change bucket exists
before we edit the listing."""
from playwright.sync_api import sync_playwright
from _cdp import shot

PUB = ("https://play.google.com/console/u/0/developers/9052149026359320771"
       "/app/4975171430765358175/publishing")

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = ctx.new_page()
    page.goto(PUB, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(8000)
    body = page.evaluate("() => document.body.innerText")
    print("PUBLISHING OVERVIEW:\n", body[:3500])
    shot(page, "45-preflight-publishing")
