"""Production check: the 5 new VinPlus yards show on the Yards tab.

Run with a Playwright-equipped python (sync API crashes under system python):
    ~/projects/sigma-mcp/.venv/bin/python tools/_verify_prod_new_yards.py
"""
import os
import re

from playwright.sync_api import sync_playwright

BASE = "https://yardscout.io/"
SHOTS = "/tmp/yardscout-newyards"
os.makedirs(SHOTS, exist_ok=True)

CHECKS = [
    ("60433", "Joliet U-Pull-It", "joliet"),
    ("78224", "San Antonio Pick-N-Pull (Independent)", "sanantonio"),
    ("76542", "195 Used Auto Parts", "killeen"),
    ("79404", "Pick Ur Part Auto Salvage", "lubbock"),
    ("32305", "Go Pull-It - Tallahassee", "tallahassee"),
]

with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE)
    page.wait_for_timeout(1000)
    page.click('[data-tab="yards"]')
    # fresh visitor: the locate prompt appears once live data lands
    page.wait_for_selector("#yards-zip-input", timeout=30000)

    first = True
    for zip_code, yard, slug in CHECKS:
        if first:
            page.fill("#yards-zip-input", zip_code)
            page.click("#yards-zip-go")
            first = False
        else:
            # #yards-zip lives inside the (collapsed) Filters drawer — set it
            # through the DOM; the app re-centers on the 'input' event.
            page.eval_on_selector(
                "#yards-zip",
                "(el, v) => { el.value = v; el.dispatchEvent(new Event('input', {bubbles: true})); }",
                zip_code,
            )
        page.wait_for_timeout(2500)  # zip geocode + re-render
        cards = page.query_selector_all(".yard-card")
        names = [c.get_attribute("data-loc") for c in cards]
        assert yard in names, f"{yard} missing near {zip_code}; saw {names[:8]}"
        card = cards[names.index(yard)]
        text = re.sub(r"\s+", " ", card.inner_text())
        m = re.search(r"([\d,]+)\s*(?:vehicles|cars)", text, re.I)
        card.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        shot = f"{SHOTS}/{slug}.png"
        page.screenshot(path=shot)
        print(f"OK {zip_code}: {yard} | count shown: {m.group(1) if m else '?'} | {shot}")
        print(f"   card: {text[:220]}")

    assert not errors, f"page errors: {errors}"
    print("ALL 5 YARDS VERIFIED ON PRODUCTION, no page errors")
    b.close()
