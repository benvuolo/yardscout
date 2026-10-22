import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    page.goto("https://play.google.com/console/u/0/developers/9052149026359320771/license-tester",
              wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(9000)
    print("URL:", page.url)
    shot(page, "30-license-testing")
    print("BODY:\n", page.inner_text("body")[:4000])
