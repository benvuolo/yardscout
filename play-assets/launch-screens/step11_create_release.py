import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    page.click("button:has-text('Create new release')", timeout=15000)
    page.wait_for_timeout(8000)
    print("URL:", page.url)
    shot(page, "11-release-editor")
    print("BODY_SNIPPET:\n", page.inner_text("body")[:4000])
    inputs = page.eval_on_selector_all("input[type=file]", "els => els.length")
    print("FILE_INPUTS:", inputs)
