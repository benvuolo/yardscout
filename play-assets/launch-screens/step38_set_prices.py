import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    page.click("button:has-text('Set prices')", timeout=15000)
    page.wait_for_timeout(5000)
    shot(page, "38-set-prices-dialog")
    print("BODY TAIL:\n", page.inner_text("body")[-3000:])
    fields = [i for i in page.query_selector_all("input") if i.is_visible()]
    for f in fields:
        print("FIELD:", repr(f.get_attribute("aria-label")), repr(f.input_value()))
