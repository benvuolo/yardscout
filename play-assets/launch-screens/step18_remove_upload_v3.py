import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

AAB = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/android/app/build/outputs/bundle/release/app-release.aab"

with sync_playwright() as p:
    browser, page = get_page(p)
    # Click 'Remove app bundle' in open menu
    page.click("text=Remove app bundle", timeout=10000)
    page.wait_for_timeout(2500)
    shot(page, "18a-remove-confirm")
    # confirmation dialog
    for sel in ["button:has-text('Remove')", "button:has-text('Confirm')", "button:has-text('OK')"]:
        b = page.query_selector(sel)
        if b and b.is_visible():
            b.click(); print("CONFIRM:", sel); break
    page.wait_for_timeout(4000)
    txt = page.inner_text("body")
    print("V2 STILL PRESENT:", "2 (1.1)" in txt)
    shot(page, "18b-after-remove")
    # upload new bundle
    page.set_input_files("input[type=file]", AAB, timeout=15000)
    print("UPLOAD STARTED")
    for i in range(60):
        page.wait_for_timeout(10000)
        txt = page.inner_text("body")
        if "optimized for distribution" in txt or "Uploading" in txt:
            if i % 6 == 0: print(f"[{i*10}s] processing...")
            continue
        break
    shot(page, "18c-v3-uploaded")
    print("BODY:\n", page.inner_text("body")[:3000])
