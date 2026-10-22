import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    links = page.eval_on_selector_all("a", "els => els.map(e => ({t: e.innerText.trim().slice(0,60), h: e.href}))")
    for l in links:
        if l["h"] and "console" in l["h"]:
            print(repr(l["t"]), "->", l["h"])
