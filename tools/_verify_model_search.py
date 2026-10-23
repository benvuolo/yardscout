#!/usr/bin/env python3
"""Regression check: alphanumeric model search (owner's MR2 report, 2026-10).

The model search box must be space/punctuation-insensitive — the 2026-10
normalization ships hyphenated canonical names (F-150, S-10) and people type
'f150', 'mr 2', 's10'. Setup mirrors _verify_model_dropdown.py: yardscout.io,
zip 92501 (Riverside CA — MR2, F-150, 328i and S-10 all within radius).

Run with a Playwright-equipped python:
    ~/projects/sigma-mcp/.venv/bin/python tools/_verify_model_search.py
Override target (e.g. a local server) with YS_BASE.
"""
import os
import re

from playwright.sync_api import sync_playwright

BASE = os.environ.get("YS_BASE", "https://yardscout.io/")
SHOTS = "/tmp/yardscout-modelsearch"
os.makedirs(SHOTS, exist_ok=True)

# (make, canonical display name, queries that must all find it)
CASES = [
    ("Toyota",    "MR2",   ["mr2", "MR2", "MR 2", "mr-2"]),
    ("Ford",      "F-150", ["f150", "F-150", "f 150"]),
    ("BMW",       "328i",  ["328i", "328I", "328 i"]),
    ("Chevrolet", "S-10",  ["s10", "S-10", "s 10"]),
]

failures = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, detail)
    if not cond:
        failures.append(name)


def panel_models(page):
    labels = page.eval_on_selector_all(
        "#live-filter-model-panel label",
        "els => els.map(e => e.textContent.trim())")
    return [re.sub(r"\s*\(\d+\)\s*$", "", l) for l in labels
            if l and l.lower() not in ("clear", "done")]


with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE)
    page.wait_for_timeout(1500)

    if page.locator("#zip-banner").is_visible():
        page.fill("#zip-banner-input", "92501")
        page.click("#zip-banner-go")
    page.wait_for_timeout(2500)

    if not page.locator("#live-filter-make").is_visible():
        page.click("#live-filter-toggle")
        page.wait_for_timeout(500)

    for make, canonical, queries in CASES:
        page.select_option("#live-filter-make", make)
        page.wait_for_timeout(800)
        page.click("#live-filter-model-btn")
        page.wait_for_timeout(400)

        browse = panel_models(page)
        check(f"{make}: '{canonical}' listed when browsing",
              canonical in browse, f"({len(browse)} models)")

        for q in queries:
            page.fill("#live-filter-model-search", "")
            page.type("#live-filter-model-search", q, delay=40)
            page.wait_for_timeout(300)
            shown = panel_models(page)
            check(f"{make}: search {q!r} finds '{canonical}'",
                  canonical in shown, f"shown={shown}")

        page.screenshot(path=f"{SHOTS}/{make.lower()}_search.png")
        page.keyboard.press("Escape")
        page.click("body", position={"x": 5, "y": 5})  # close the panel
        page.wait_for_timeout(300)

    check("no page errors", not errors, str(errors[:3]))
    b.close()

print()
if failures:
    print(f"{len(failures)} FAILURE(S): {failures}")
    raise SystemExit(1)
print("alphanumeric model search verification passed")
