import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p, prefer="releases/2/review")
    loc = page.locator("xpath=//*[contains(text(),'Roll-out percentage')]/following::input[1]")
    print("FOUND:", loc.count())
    loc.first.fill("100")
    print("VALUE:", loc.first.input_value())
    page.wait_for_timeout(1500)
    shot(page, "48c-rollout-100")
    sv = [b for b in page.query_selector_all("button") if b.is_visible() and (b.inner_text() or "").strip() == "Save"]
    print("SAVE BTNS:", len(sv))
    sv[-1].click()
    page.wait_for_timeout(6000)
    shot(page, "48d-saved")
    print("URL:", page.url)
    print("TAIL:\n", page.inner_text("body")[-1800:])
