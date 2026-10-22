import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p, prefer="releases/2/prepare")
    print("PAGE:", page.url)
    page.click("button:has-text('Next')", timeout=15000)
    page.wait_for_timeout(9000)
    print("URL:", page.url)
    for el in page.query_selector_all("text=Show more"):
        try: el.click(); page.wait_for_timeout(1200)
        except Exception: pass
    page.wait_for_timeout(2000)
    shot(page, "47-prod-review")
    print("BODY:\n", page.inner_text("body")[:6000])
