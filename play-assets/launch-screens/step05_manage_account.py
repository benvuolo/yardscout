import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    page.goto("https://play.google.com/console/u/0/developers/9052149026359320771/manage-account",
              wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)
    print("URL:", page.url)
    shot(page, "05-manage-account")
    txt = page.inner_text("body")
    print("BODY_SNIPPET:\n", txt[:4000])
    print("\n--- LINKS with pay/merchant ---")
    links = page.eval_on_selector_all("a", "els => els.map(e => ({t: e.innerText.trim().slice(0,80), h: e.href}))")
    for l in links:
        if any(k in (l["t"]+l["h"]).lower() for k in ["pay", "merchant", "monetiz", "license"]):
            print(repr(l["t"]), "->", l["h"])
