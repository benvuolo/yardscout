import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    page.wait_for_timeout(5000)
    print("FRAMES:")
    for f in page.frames:
        print(" -", f.url[:140])
    for f in page.frames:
        if "payments" in f.url and f != page.main_frame:
            try:
                txt = f.inner_text("body")
                print("\n=== FRAME", f.url[:100], "===")
                print(txt[:5000])
            except Exception as e:
                print("frame read error:", e)
    shot(page, "07-payments-profile-full")
