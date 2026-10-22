import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    # Release name input
    inp = page.query_selector("input[aria-label*='Release name'], input")
    name_inputs = [i for i in page.query_selector_all("input") if i.is_visible() and (i.get_attribute("type") or "text") == "text"]
    print("TEXT INPUTS:", len(name_inputs))
    for i in name_inputs:
        print(" value:", repr(i.input_value()), "aria:", i.get_attribute("aria-label"))
    if name_inputs:
        name_inputs[0].fill("3 (1.1)")
        print("RENAMED to 3 (1.1)")
    page.wait_for_timeout(1500)
    page.click("button:has-text('Next')", timeout=15000)
    page.wait_for_timeout(9000)
    print("URL:", page.url)
    # expand errors/warnings
    for el in page.query_selector_all("text=Show more"):
        try: el.click(); page.wait_for_timeout(1200)
        except Exception: pass
    page.wait_for_timeout(2000)
    shot(page, "19-review-v3")
    print("BODY:\n", page.inner_text("body")[:6000])
