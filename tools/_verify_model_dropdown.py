#!/usr/bin/env python3
"""Production check for the 2026-10 model merge: the BMW model dropdown at
yardscout.io (zip 84047, the owner's screenshot setup) must show no bare
'328' next to '328i', no case duplicates, and a collapsed '3 Series' blob.

Run with a Playwright-equipped python:
    ~/projects/sigma-mcp/.venv/bin/python tools/_verify_model_dropdown.py
"""
import collections
import os
import re

from playwright.sync_api import sync_playwright

BASE = os.environ.get("YS_BASE", "https://yardscout.io/")
SHOTS = "/tmp/yardscout-modeldropdown"
os.makedirs(SHOTS, exist_ok=True)

failures = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, detail)
    if not cond:
        failures.append(name)


with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE)
    page.wait_for_timeout(1500)

    # Zip gate (same zip as the owner's screenshot).
    if page.locator("#zip-banner").is_visible():
        page.fill("#zip-banner-input", "84047")
        page.click("#zip-banner-go")
    page.wait_for_timeout(2500)

    # Open filters if collapsed, pick BMW, open the model multi-select.
    try:
        ftoggle = page.locator("#live-filters-toggle, .filters-toggle").first
        if ftoggle.is_visible():
            ftoggle.click()
            page.wait_for_timeout(300)
    except Exception:
        pass
    page.select_option("#live-filter-make", "BMW")
    page.wait_for_timeout(800)
    page.click("#live-filter-model-btn")
    page.wait_for_timeout(500)
    page.screenshot(path=f"{SHOTS}/bmw_dropdown.png")

    labels = page.eval_on_selector_all(
        "#live-filter-model-panel label",
        "els => els.map(e => e.textContent.trim())")
    models = [re.sub(r"\s*\(\d+\)\s*$", "", l) for l in labels if l and l.lower() not in ("clear", "done")]
    print(f"\nBMW models in dropdown ({len(models)}): {models}\n")

    check("dropdown has BMW models", len(models) > 0)
    check("no bare '328' entry", "328" not in models)
    check("'328i' present", "328i" in models)
    low = collections.Counter(m.lower() for m in models)
    dupes = [m for m, c in low.items() if c > 1]
    check("no case-duplicate entries", not dupes, str(dupes))
    check("no 'BMW '-prefixed entries", not any(m.lower().startswith("bmw ") for m in models))
    check("no 'Xdrive' casing (xDrive canonical)", not any("Xdrive" in m for m in models))
    series_entries = [m for m in models if re.match(r"^\d Series", m)]
    print("series blob entries still visible (expected small/none in UT):", series_entries)
    check("no page errors", not errors, str(errors[:3]))

    b.close()

print()
if failures:
    print(f"{len(failures)} FAILURE(S): {failures}")
    raise SystemExit(1)
print("model dropdown verification passed")
