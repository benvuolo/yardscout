import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    page.click("button:has-text('Save and publish')", timeout=15000)
    page.wait_for_timeout(3000)
    shot(page, "20a-publish-dialog")
    # confirmation dialog
    for sel in ["button:has-text('Save and publish')", "button:has-text('Publish')", "button:has-text('Confirm')"]:
        bs = [b for b in page.query_selector_all(sel) if b.is_visible()]
        if bs:
            bs[-1].click(); print("CONFIRM:", sel); break
    page.wait_for_timeout(9000)
    print("URL:", page.url)
    shot(page, "20b-after-publish")
    print("BODY:\n", page.inner_text("body")[:4000])
