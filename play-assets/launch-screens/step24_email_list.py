import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    page.click("button:has-text('Create email list')", timeout=10000)
    page.wait_for_timeout(4000)
    shot(page, "24a-email-list-dialog")
    print("BODY:\n", page.inner_text("body")[-2500:])
    # Dialog fields
    inputs = [i for i in page.query_selector_all("input, textarea") if i.is_visible()]
    for i in inputs:
        print("FIELD:", i.evaluate("e=>e.tagName"), repr(i.get_attribute("aria-label")), repr(i.get_attribute("placeholder")))
