import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    sv = [b for b in page.query_selector_all("button:has-text('Save')") if b.is_visible() and b.inner_text().strip() == "Save"]
    print("SAVE BTNS:", len(sv))
    sv[-1].click()
    page.wait_for_timeout(8000)
    print("URL:", page.url)
    shot(page, "41-baseplan-saved")
    print("BODY:\n", page.inner_text("body")[:4000])
