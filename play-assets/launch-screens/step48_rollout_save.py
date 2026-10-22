import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p, prefer="releases/2/review")
    pct = page.query_selector("input[aria-label*='Roll-out'], input[aria-label*='percentage']")
    if not pct:
        cands = [i for i in page.query_selector_all("input") if i.is_visible()]
        for c in cands:
            print("INPUT:", repr(c.get_attribute("aria-label")))
        pct = next((c for c in cands if "roll" in (c.get_attribute("aria-label") or "").lower()), None)
    print("PCT FIELD:", bool(pct))
    pct.fill("100")
    print("PCT VALUE:", pct.input_value())
    page.wait_for_timeout(1500)
    shot(page, "48a-rollout-100")
    sv = [b for b in page.query_selector_all("button") if b.is_visible() and (b.inner_text() or "").strip() == "Save"]
    print("SAVE BTNS:", len(sv))
    sv[-1].click()
    page.wait_for_timeout(5000)
    shot(page, "48b-saved")
    print("TAIL:\n", page.inner_text("body")[-1500:])
