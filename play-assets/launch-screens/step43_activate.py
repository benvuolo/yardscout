import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p, prefer="base-plans/b/monthly")
    print("PAGE:", page.url)
    btns = page.eval_on_selector_all("button",
        "els => els.filter(e=>e.offsetParent).map(e=>(e.innerText||'').trim()).filter(Boolean)")
    print("BUTTONS:", btns)
    act = [b for b in page.query_selector_all("button:has-text('Activate')") if b.is_visible()]
    print("ACTIVATE BTNS:", len(act))
    if act:
        act[0].click()
        page.wait_for_timeout(4000)
        shot(page, "43a-activate-dialog")
        print("TAIL:\n", page.inner_text("body")[-1200:])
        conf = page.query_selector(".acx-overlay-container .modal button:has-text('Activate')")
        if conf:
            conf.click(); print("CONFIRMED")
        page.wait_for_timeout(6000)
    shot(page, "43b-baseplan-activated")
    txt = page.inner_text("body")
    print("STATUS ACTIVE:", "Active" in txt[:1500])
    print("HEAD:\n", txt[:1200])
