"""Playwright check of the confirmed-value honesty changes.

Serve docs/ first, e.g.:
    cd docs && python3 -m http.server 8613 & ... ; kill $SRV
Run with a Playwright-equipped python (sync API crashes under system python):
    ~/projects/sigma-mcp/.venv/bin/python scraper/_verify_ui.py
"""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8613/"
SHOTS = "/tmp/yardscout-honesty"
os.makedirs(SHOTS, exist_ok=True)

# --- pick target vehicles straight from the shipped data ---------------------
d = json.loads((Path(__file__).resolve().parent.parent / "docs/data/inventory_live.json").read_text())
f = d["fields"]
yi, mki, mdi, psi, mvi, vini = (f.index(k) for k in ("year", "make", "model", "partSet", "maxValue", "vin"))

def find(pred):
    return next(r for r in d["vehicles"]
                if r[psi] is not None and r[psi] >= 0 and r[vini] and pred(r, d["partSets"][r[psi]]))

focus = find(lambda r, ps: r[mki].lower() == "ford" and "focus" in r[mdi].lower()
             and any("Recaro" in p["name"] and p.get("trim_status") == "unconfirmed" for p in ps))
f150 = find(lambda r, ps: r[mki].lower() == "ford" and "f-150" in r[mdi].lower().replace("f150", "f-150")
            and any("Tow Mirrors" in p["name"] and p.get("trim_status") == "unconfirmed" for p in ps))
print(f"targets: Focus {focus[yi]} vin={focus[vini]} maxValue={focus[mvi]} | "
      f"F-150 {f150[yi]} vin={f150[vini]} maxValue={f150[mvi]}")
assert focus[mvi] < 500, "base Focus still ranks off unconfirmed Recaro dollars"
assert f150[mvi] < 500, "F-150 still ranks off unconfirmed tow-mirror dollars"

with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE + "?pro=1")
    page.wait_for_selector(".car-card", timeout=30000)
    page.wait_for_timeout(6000)  # let the full inventory land (fallback renders first)

    def card_for_vin(vin):
        page.fill("#live-search", vin)
        page.wait_for_timeout(800)
        c = page.query_selector(".car-card")
        assert c, f"no card for vin {vin}"
        return c

    # 1) Base Focus: headline range excludes Recaro dollars, extra line shown
    c = card_for_vin(focus[vini])
    rt = c.query_selector(".range-text")
    rex = c.query_selector(".range-extra")
    print("FOCUS card:", c.query_selector(".car-name").inner_text())
    print("  headline:", rt.inner_text() if rt else "(none)")
    print("  extra   :", rex.inner_text() if rex else "(MISSING)")
    assert rex and "if equipped" in rex.inner_text(), "missing '+ up to $X if equipped' line"
    if rt:
        import re as _re
        hi = max(int(x.replace(",", "")) for x in _re.findall(r"\$([\d,]+)", rt.inner_text()))
        assert hi < 600, f"headline still includes unconfirmed dollars: {rt.inner_text()}"
    c.screenshot(path=f"{SHOTS}/focus-card.png")

    # 2) F-150: tow mirrors badged unconfirmed, excluded from headline
    c = card_for_vin(f150[vini])
    det = c.query_selector(".parts-details summary")
    if det:
        det.click()
        page.wait_for_timeout(400)
    rt = c.query_selector(".range-text")
    rex = c.query_selector(".range-extra")
    badges = [e.inner_text() for e in c.query_selector_all(".trim-badge")]
    print("F-150 card:", c.query_selector(".car-name").inner_text())
    print("  headline:", rt.inner_text() if rt else "(none)")
    print("  extra   :", rex.inner_text() if rex else "(MISSING)")
    print("  badges  :", badges)
    assert rex, "F-150 missing extra line"
    assert any("unconfirmed" in b for b in badges), "tow mirrors not badged unconfirmed"
    c.screenshot(path=f"{SHOTS}/f150-card.png")

    # 3) Most-valuable sort: top cards must carry confirmed (non-zero) headline
    # value. The select is disabled until a zip is set (pre-existing gating),
    # so drive it programmatically — we're testing the sort, not the gate.
    page.fill("#live-search", "")
    page.evaluate("""() => {
      const s = document.getElementById('live-sort');
      s.disabled = false; s.value = 'gold-first';
      s.dispatchEvent(new Event('change'));
    }""")
    page.wait_for_timeout(1500)
    page.screenshot(path=f"{SHOTS}/most-valuable-top.png")
    print("TOP OF 'MOST VALUABLE FIRST':")
    for c in page.query_selector_all(".car-card")[:8]:
        name = c.query_selector(".car-name").inner_text()
        rt = c.query_selector(".range-text")
        print(f"  {name} | {rt.inner_text() if rt else '(no confirmed range!)'}")
        assert rt, f"unconfirmed-only car ranked at top: {name}"

    # 4) Free tier: lock chip unchanged on a car with only unconfirmed upside.
    # Free users can't browse nationwide (gate-nationwide) — pre-seed the zip
    # coords cache with the target F-150's own yard coords so it's in radius.
    yard = d["yards"][f150[f.index("yard")]]
    page.evaluate("""([lat, lng]) => {
      localStorage.setItem('jh_zip_coords',
        JSON.stringify({'84101': {lat, lng}}));
      localStorage.setItem('jh_zip', '84101');
    }""", [yard[3], yard[4]])
    page.goto(BASE + "?pro=0")
    page.wait_for_timeout(8000)
    if not page.query_selector(".car-card"):
        # zip banner still up — enter the cached zip through the UI
        page.fill("#zip-banner-input", "84101")
        page.click("#zip-banner-go")
        page.wait_for_selector(".car-card", timeout=30000)
        page.wait_for_timeout(1000)
    c = card_for_vin(f150[vini])
    assert c.query_selector(".lock-chip"), "free-tier lock chip disappeared"
    assert not c.query_selector(".range-extra"), "unconfirmed dollars leaked to free tier"
    print("free tier: lock chip present, no dollar leak")

    print("console errors:", errors or "none")
    assert not errors, errors
    b.close()

print(f"UI verification PASSED. Screenshots in {SHOTS}")
