"""One-off Playwright check of the confirmed-value honesty changes."""
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8613/?pro=1"
SHOTS = "/tmp/yardscout-honesty"

import os
os.makedirs(SHOTS, exist_ok=True)

with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE)
    page.wait_for_selector(".car-card", timeout=30000)

    # 1) Search for a base Focus and inspect its card
    page.fill("#live-search", "ford focus")
    page.wait_for_timeout(1200)
    cards = page.query_selector_all(".car-card")
    base_card = None
    for c in cards[:30]:
        name = c.query_selector(".car-name").inner_text()
        if "Focus" in name and "ST" not in name and "RS" not in name:
            txt = c.inner_text()
            if "if equipped" in txt:
                base_card = c
                break
    assert base_card, "no base Focus card with unconfirmed parts found"
    print("BASE FOCUS CARD:")
    print("  name:", base_card.query_selector(".car-name").inner_text())
    rt = base_card.query_selector(".range-text")
    print("  headline range:", rt.inner_text() if rt else "(none)")
    re_ = base_card.query_selector(".range-extra")
    print("  extra line:", re_.inner_text() if re_ else "(MISSING)")
    assert re_, "range-extra line missing"
    hl = (rt.inner_text() if rt else "")
    assert "1,9" not in hl and "2,0" not in hl, f"Recaro dollars leaked into headline: {hl}"
    base_card.scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    base_card.screenshot(path=f"{SHOTS}/focus-card.png")

    # 2) Sort by most valuable, confirm top cards are not unconfirmed-only
    page.fill("#live-search", "")
    page.select_option("#live-sort", "gold-first")
    page.wait_for_timeout(1500)
    page.screenshot(path=f"{SHOTS}/most-valuable-top.png")
    top = page.query_selector_all(".car-card")[:8]
    print("\nTOP OF 'MOST VALUABLE FIRST':")
    for c in top:
        name = c.query_selector(".car-name").inner_text()
        rt = c.query_selector(".range-text")
        badges = [e.inner_text() for e in c.query_selector_all(".trim-badge")]
        print(f"  {name} | range: {rt.inner_text() if rt else '(none)'}")
        # A top-sorted card must have a confirmed (non-zero) headline range.
        assert rt and "$0–$0" not in rt.inner_text(), f"unconfirmed-only car at top: {name}"

    # 3) F-150 card shows tow mirrors as unconfirmed and out of headline
    page.select_option("#live-sort", "date-desc")
    page.fill("#live-search", "ford f-150")
    page.wait_for_timeout(1200)
    for c in page.query_selector_all(".car-card")[:20]:
        txt = c.inner_text()
        if "Tow Mirrors" in txt or "if equipped" in txt:
            det = c.query_selector(".parts-details summary")
            if det:
                det.click()
                page.wait_for_timeout(300)
            print("\nF-150 CARD:", c.query_selector(".car-name").inner_text())
            rt = c.query_selector(".range-text")
            rex = c.query_selector(".range-extra")
            print("  headline:", rt.inner_text() if rt else "(none)")
            print("  extra:", rex.inner_text() if rex else "(none)")
            c.screenshot(path=f"{SHOTS}/f150-card.png")
            break

    print("\nconsole errors:", errors or "none")
    assert not errors, errors
    b.close()
print("UI verification passed. Screenshots in", SHOTS)
