import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

EXPECTED = "yardscout_pro_monthly"

with sync_playwright() as p:
    browser, page = get_page(p)
    pid = page.query_selector("input[aria-label='Product ID']")
    name = page.query_selector("input[aria-label='Name']")
    pid.fill(EXPECTED)
    name.fill("YardScout Pro")
    page.wait_for_timeout(1500)
    val = pid.input_value()
    print("PRODUCT_ID VALUE:", repr(val))
    print("MATCHES EXPECTED:", val == EXPECTED)
    print("NAME VALUE:", repr(name.input_value()))
    shot(page, "35a-sub-filled-PRE-SUBMIT")
    if val != EXPECTED:
        print("ABORT: mismatch"); sys.exit(1)
    btn = page.query_selector(".acx-overlay-container .modal button:has-text('Create')")
    print("MODAL CREATE:", bool(btn))
    btn.click()
    page.wait_for_timeout(8000)
    print("URL:", page.url)
    shot(page, "35b-sub-created")
    print("BODY:\n", page.inner_text("body")[:4000])
