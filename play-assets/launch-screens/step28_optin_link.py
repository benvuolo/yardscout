import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    hrefs = page.eval_on_selector_all("a", "els => els.map(e=>e.href).filter(h=>h && (h.includes('internaltest')||h.includes('apps/test')))")
    print("OPTIN LINKS:", hrefs)
    vals = page.eval_on_selector_all("input", "els => els.map(e=>e.value).filter(v=>v && v.includes('play.google.com'))")
    print("INPUT VALUES:", vals)
    txt = page.inner_text("body")
    import re
    m = re.findall(r"https://play\.google\.com/\S+", txt)
    print("TEXT URLS:", m)
