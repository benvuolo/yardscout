import sys, time
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

AAB = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/android/app/build/outputs/bundle/release/app-release.aab"

with sync_playwright() as p:
    browser, page = get_page(p)
    # wait for editor to render
    for i in range(12):
        txt = page.inner_text("body")
        if "App bundles" in txt or "Upload" in txt:
            break
        page.wait_for_timeout(5000)
    print("URL:", page.url)
    shot(page, "12a-release-editor-loaded")
    print("BODY:\n", page.inner_text("body")[:3500])
    n = page.eval_on_selector_all("input[type=file]", "els => els.length")
    print("FILE_INPUTS:", n)
    if n:
        page.set_input_files("input[type=file]", AAB, timeout=15000)
        print("UPLOAD STARTED")
        # poll for processing completion up to 5 min
        for i in range(30):
            page.wait_for_timeout(10000)
            txt = page.inner_text("body")
            for kw in ["Uploading", "%", "version code", "Version code", "1.1", "Error", "error"]:
                pass
            if "app-release.aab" in txt or "1.1 (2)" in txt or "Version code" in txt or "2" in txt:
                # heuristic; take status snapshot each loop
                pass
            if "Uploading" not in txt and "Processing" not in txt and i > 1:
                break
        shot(page, "12b-after-upload")
        print("BODY AFTER:\n", page.inner_text("body")[:4000])
