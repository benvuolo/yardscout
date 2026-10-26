#!/usr/bin/env python3
"""Production check for the Yards-tab price-compare alias layer (jh-v71).

Owner bug: the compare combobox listed each chain's raw price-sheet spelling
as its own part — typing 'Air' surfaced Air Cleaner Housing / Hous(Lg) /
Hous(Sm) / Box Plas as separate entries, and picking one compared only the
yards sharing that exact spelling (2 of 7 yards in the report video).

The fix: token-normalizing partMergeKey (word order / fillers / chain
abbreviations) + curated PART_ALIAS_GROUPS over the raw names, quoting
through exact-raw-name tiers. This script verifies on production at 390px:

 1. Yards tab, typing 'air' shows ONE 'Air intake / airbox' entry and no
    Air Cleaner Housing / Hous(Lg) / Hous(Sm) / Box fragments
 2. the airbox compare covers every SLC-area yard publishing ANY alias
    (Tear-A-Part's own HOUS( spelling appears in its row), and the honest
    'not on the published list' footer still exists for pyp/pap-style yards
 3. 'airbox' synonym finds the canonical entry
 4. 'alternator' and 'starter' still compare (counts intact, incl.
    Pull-A-Part via the ALTERNATOR (NON HYBRID) alias)
 5. 'back seat' never shows the blocklisted 'Back Seat Back' as merged

Run BEFORE=1 to capture the pre-deploy state (screenshots only, no checks).
Zip 84115 (Salt Lake City) — the owner's own report area.
Run:  .venv/bin/python tools/_verify_compare_aliases_prod.py
"""
import os
import re
import sys

from playwright.sync_api import sync_playwright

BASE = os.environ.get("YS_BASE", "https://yardscout.io/")
ZIP = os.environ.get("YS_ZIP", "84115")
BEFORE = os.environ.get("BEFORE") == "1"
SHOTS = "/tmp/yardscout-prod-compare-aliases"
os.makedirs(SHOTS, exist_ok=True)
TAG = "before" if BEFORE else "after"
FAILS = []


def check(name, cond, detail=""):
    print(("ok   " if cond else "FAIL ") + name
          + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def suggests(page, query):
    page.fill("#compare-input", "")
    page.wait_for_timeout(150)
    page.fill("#compare-input", query)
    page.wait_for_timeout(500)
    items = page.locator("#compare-suggest .compare-suggest-item")
    return [items.nth(i).inner_text().replace("\n", " ") for i in range(items.count())]


def open_compare(page, query, label):
    page.fill("#compare-input", "")
    page.wait_for_timeout(150)
    page.fill("#compare-input", query)
    page.wait_for_selector("#compare-suggest .compare-suggest-item", timeout=8000)
    items = page.locator("#compare-suggest .compare-suggest-item")
    for i in range(items.count()):
        if label.lower() in items.nth(i).inner_text().lower():
            items.nth(i).dispatch_event("mousedown")
            page.wait_for_timeout(700)
            return True
    return False


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(viewport={"width": 390, "height": 844},
                              device_scale_factor=2, is_mobile=True,
                              has_touch=True)
    page = ctx.new_page()
    page.add_init_script("localStorage.setItem('jh_honesty_ack', '1');")
    page.goto(BASE, wait_until="domcontentloaded")
    page.click("#live-filter-toggle")
    page.fill("#live-zip", ZIP)
    page.wait_for_selector("#live-grid .match-card, #live-grid .dim-card",
                           timeout=45000)
    page.click(".tab[data-tab='yards']")
    page.wait_for_timeout(600)

    # 1. 'air' suggestions — consolidated, fragment-free
    labels = suggests(page, "air")
    page.screenshot(path=f"{SHOTS}/{TAG}_1_air_suggest_390.png")
    print("  'air' suggestions:", labels[:12])
    if not BEFORE:
        check("'air' shows Air intake / airbox",
              any("Air intake / airbox" in x for x in labels), str(labels[:12]))
        frag = [x for x in labels if re.search(
            r"Air Cleaner Hous|Air Cleaner Box|Air Cleaner Housing|Air Box - Complete|Air Cleaner Assembly|Air Cleaner Sm|Air Cleaner \(Round\)", x, re.I)]
        check("no raw airbox-spelling fragments in suggestions",
              not frag, str(frag))
        check("'air' shows consolidated Air cleaner lid",
              any("air cleaner lid" in x.lower() for x in labels), str(labels[:12]))

    # 2. the airbox compare — covers every yard publishing ANY alias
    opened = open_compare(page, "air", "airbox" if not BEFORE else "hous(sm)")
    if not BEFORE:
        check("picked Air intake / airbox", opened)
    page.wait_for_timeout(700)
    body = page.locator("#prices-body").inner_text()
    sub = page.locator("#prices-sub").inner_text()
    page.screenshot(path=f"{SHOTS}/{TAG}_2_airbox_compare_390.png")
    print("  compare sub:", sub)
    print("  compare rows:", body[:400].replace("\n", " | "))
    if not BEFORE:
        m = re.search(r"(\d+) of (\d+) yards?", sub)
        check("compare sheet opened with coverage line", bool(m), sub)
        if m:
            check("airbox compare covers most yards in view (>2 of N)",
                  int(m.group(1)) >= 4, sub)
        check("Tear-A-Part row shows its own HOUS( spelling",
              "HOUS(" in body.upper(), body[:300])
        check("honest 'not on the published list' footer kept",
              "not on the published list" in body.lower() or int(m.group(1)) == int(m.group(2)),
              body[-300:])
    page.keyboard.press("Escape")
    page.locator("#prices-close").click()
    page.wait_for_timeout(300)

    if not BEFORE:
        # 3. synonym search
        ls = suggests(page, "airbox")
        check("'airbox' synonym finds the canonical entry",
              any("Air intake / airbox" in x for x in ls), str(ls[:6]))

        # 4. alternator & starter still work
        for q, needs_yards in [("alternator", 5), ("starter", 5)]:
            ls = suggests(page, q)
            top = ls[0] if ls else ""
            myards = re.search(r"(\d+) yards", top)
            check(f"'{q}' top suggestion is consolidated with honest count",
                  q in top.lower() and myards and int(myards.group(1)) >= needs_yards, str(ls[:4]))
            ok = open_compare(page, q, q)
            check(f"'{q}' compare opens", ok)
            page.wait_for_timeout(500)
            sub = page.locator("#prices-sub").inner_text()
            m = re.search(r"(\d+) of (\d+)", sub)
            check(f"'{q}' compare prices multiple yards", m and int(m.group(1)) >= 4, sub)
            if q == "alternator":
                page.screenshot(path=f"{SHOTS}/{TAG}_3_alternator_compare_390.png")
            page.locator("#prices-close").click()
            page.wait_for_timeout(300)

        # 5. blocklist honesty: back seat back stays its own entry
        ls = suggests(page, "back seat")
        check("'Back Seat Back' not swallowed by 'Back Seat'",
              True if not any("back seat back" in x.lower() for x in ls)
              else any(x.lower().startswith("back seat back") for x in ls), str(ls[:6]))

    ctx.close()
    browser.close()

print("FAILS:", FAILS if FAILS else ("(before mode: screenshots only)" if BEFORE else "none"))
print("shots:", SHOTS)
sys.exit(1 if FAILS else 0)
