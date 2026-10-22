import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    btns = page.eval_on_selector_all("button",
        "els => els.filter(e=>e.offsetParent).map(e => ({t:(e.innerText||'').trim().slice(0,40), dis: e.disabled}))")
    for b in btns: print(b)
