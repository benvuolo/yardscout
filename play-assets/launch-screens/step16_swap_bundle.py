import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

APP = "https://play.google.com/console/u/0/developers/9052149026359320771/app/4975171430765358175"
AAB = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/android/app/build/outputs/bundle/release/app-release.aab"

with sync_playwright() as p:
    browser, page = get_page(p)
    page.goto(APP + "/tracks/4701692045663309270/releases/1/prepare",
              wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(10000)
    txt = page.inner_text("body")
    print("HAS OLD BUNDLE:", "app-release.aab" in txt)
    shot(page, "16a-prepare-before-swap")
    # Delete the old bundle (trash icon in bundle row)
    del_btns = page.query_selector_all("button:has-text('delete')")
    print("DELETE BUTTONS:", len(del_btns))
    if del_btns:
        del_btns[0].click()
        page.wait_for_timeout(3000)
        # confirm dialog if present
        for sel in ["button:has-text('Delete')", "button:has-text('Remove')", "button:has-text('Confirm')"]:
            b = page.query_selector(sel)
            if b and b.is_visible():
                b.click(); print("CONFIRMED via", sel); break
        page.wait_for_timeout(4000)
    shot(page, "16b-after-delete")
    print("BODY AFTER DELETE:\n", page.inner_text("body")[:1500])
