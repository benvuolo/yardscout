import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    f = page.query_selector("input[aria-label='New price in USD']")
    f.fill("8.99")
    print("PRICE VALUE:", repr(f.input_value()))
    shot(page, "40a-price-entered")
    btn = page.query_selector(".acx-overlay-container .modal button:has-text('Update')")
    print("UPDATE BTN:", bool(btn))
    btn.click()
    page.wait_for_timeout(6000)
    shot(page, "40b-price-applied")
    txt = page.inner_text("body")
    import re
    us = re.search(r"United States\n([^\n]*)", txt)
    print("US ROW PRICE:", us.group(1) if us else "?")
    print("HAS 8.99:", "$8.99" in txt)
