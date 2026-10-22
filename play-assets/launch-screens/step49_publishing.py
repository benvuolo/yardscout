import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p, prefer="releases/2/review")
    btn = page.query_selector(".acx-overlay-container .modal button:has-text('Go to overview')")
    print("GO TO OVERVIEW:", bool(btn))
    btn.click()
    page.wait_for_timeout(9000)
    print("URL:", page.url)
    shot(page, "49-publishing-overview")
    print("BODY:\n", page.inner_text("body")[:4500])
