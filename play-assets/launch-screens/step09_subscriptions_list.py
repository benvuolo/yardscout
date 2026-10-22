import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

APP = "https://play.google.com/console/u/0/developers/9052149026359320771/app/4975171430765358175"

with sync_playwright() as p:
    browser, page = get_page(p)
    page.goto(APP + "/subscriptions", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)
    print("URL:", page.url)
    shot(page, "09-subscriptions-list")
    print("BODY_SNIPPET:\n", page.inner_text("body")[:4000])
