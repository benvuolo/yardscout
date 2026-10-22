import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    page.click("button:has-text('Create subscription')", timeout=15000)
    page.wait_for_timeout(6000)
    print("URL:", page.url)
    shot(page, "34a-create-sub-form")
    print("BODY:\n", page.inner_text("body")[:3000])
    fields = [i for i in page.query_selector_all("input, textarea") if i.is_visible()]
    for f in fields:
        print("FIELD:", f.evaluate("e=>e.tagName"), repr(f.get_attribute("aria-label")))
