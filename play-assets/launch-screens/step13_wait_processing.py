import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    done = False
    for i in range(60):  # up to 10 min
        page.wait_for_timeout(10000)
        txt = page.inner_text("body")
        if "optimized for distribution" in txt or "Uploading" in txt:
            if i % 6 == 0:
                print(f"[{i*10}s] still processing...")
            continue
        done = True
        break
    shot(page, "13-bundle-processed")
    txt = page.inner_text("body")
    print("DONE:", done)
    print("BODY:\n", txt[:4500])
