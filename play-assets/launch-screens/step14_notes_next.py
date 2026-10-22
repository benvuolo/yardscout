import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

NOTES = "<en-US>\nYardScout Pro is now available on Android — part values, instant arrival alerts, and cross-device Pro. Plus 210+ yards nationwide.\n</en-US>"

with sync_playwright() as p:
    browser, page = get_page(p)
    # Find the release notes textarea (second textarea usually; release name is an input)
    tareas = page.query_selector_all("textarea")
    print("TEXTAREAS:", len(tareas))
    for t in tareas:
        ph = (t.get_attribute("aria-label") or "") + (t.get_attribute("placeholder") or "")
        print(" -", repr(ph[:80]))
    # fill the one that's for release notes: typically the large one
    filled = False
    for t in tareas:
        ph = ((t.get_attribute("aria-label") or "") + (t.get_attribute("placeholder") or "")).lower()
        if "note" in ph or "release notes" in ph:
            t.fill(NOTES); filled = True; break
    if not filled and tareas:
        tareas[-1].fill(NOTES); filled = True
    print("NOTES FILLED:", filled)
    page.wait_for_timeout(2000)
    shot(page, "14a-notes-filled")
    page.click("button:has-text('Next')", timeout=15000)
    page.wait_for_timeout(8000)
    print("URL:", page.url)
    shot(page, "14b-preview-confirm")
    print("BODY:\n", page.inner_text("body")[:4500])
