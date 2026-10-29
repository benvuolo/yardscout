#!/usr/bin/env python3
"""Browser e2e for part-first interchange search v2.

Flows the task demands: an alternator search for a 2005 Toyota Camry, a
1999 Ford F-150, and a 2016 Subaru WRX — each must return donor rows with
honest two-tier confidence chips. Starts its own static server over docs/
and drives Chromium at an iPhone viewport.

    ~/projects/sigma-mcp/.venv/bin/python backend/test/part_finder_e2e.py

Screenshots land in /tmp/yardscout_shots/.
"""
import http.server
import pathlib
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
SHOTS = pathlib.Path("/tmp/yardscout_shots")
SHOTS.mkdir(exist_ok=True)
PORT = 8619
FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = ""):
    print(("ok   " if cond else "FAIL ") + name
          + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(DOCS), **kw)

    def log_message(self, *a):
        pass


threading.Thread(
    target=http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    .serve_forever, daemon=True).start()

IPHONE = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 3,
          "is_mobile": True, "has_touch": True}
PRO_BOOT = """
  localStorage.setItem('jh_pro', '1');
  localStorage.setItem('jh_pro_source', 'account');
  localStorage.setItem('jh_honesty_ack', '1');
"""

CARS = [
    # (slug, year, make, model-option candidates, engine-chip substring,
    #  expect_verified)
    ("camry05", "2005", "Toyota", ["Camry"], "2AZ", True),
    ("f150_99", "1999", "Ford", ["F-150", "F150 Pickup", "F150"], "5.4", True),
    ("wrx16", "2016", "Subaru", ["WRX"], None, True),
    # The owner's preview repro: a 1998 4Runner used to answer "no
    # interchange data" — the 3RZ/5VZ truck families now cover it. The
    # 3.4 chip exercises toyota-5vz (2.4/2.7 chip is toyota-rz).
    ("runner98", "1998", "Toyota", ["4Runner"], "3.4", True),
]


def pf_search(page, year, make, model_candidates, engine_chip,
              part="alternator"):
    page.fill("#pf-part", part)
    page.wait_for_selector("#pf-part-suggest .compare-suggest-item",
                           timeout=5000)
    page.locator("#pf-part-suggest .compare-suggest-item").first.dispatch_event(
        "mousedown")
    page.select_option("#pf-year", year)
    page.select_option("#pf-make", make)
    page.wait_for_timeout(200)
    opts = page.eval_on_selector_all(
        "#pf-model option", "os => os.map(o => o.value)")
    model = next((m for m in model_candidates if m in opts), None)
    if model is None:
        model = next((o for o in opts
                      for m in model_candidates if m.lower() in o.lower()), None)
    if model is None:
        return None
    page.select_option("#pf-model", model)
    page.click("#pf-go")
    page.wait_for_timeout(600)
    # Multi-engine models ask "which engine is in YOUR car?" — answer it.
    if engine_chip and page.locator("#pf-engine .pf-chip").count():
        chips = page.locator("#pf-engine .pf-chip")
        for i in range(chips.count()):
            if engine_chip.lower() in chips.nth(i).inner_text().lower():
                chips.nth(i).click()
                break
        page.wait_for_timeout(600)
    return model


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(**IPHONE)
    page = ctx.new_page()
    page.add_init_script(PRO_BOOT)
    page.goto(f"http://127.0.0.1:{PORT}/index.html",
              wait_until="domcontentloaded")
    page.click("#live-filter-toggle")
    page.fill("#live-zip", "85003")   # Phoenix — Pull-N-Save holds
    # verified-span WRX donors (2016/2018 at Phoenix South, 2015 Gilbert)
    page.wait_for_selector("#live-grid .match-card, #live-grid .dim-card",
                           timeout=30000)
    page.click("#live-filter-toggle")

    # The finder lives on its own Parts tab now (Live / Yards / Parts /
    # Alerts) — enter the way a user does.
    page.click(".tab[data-tab='parts']")
    page.wait_for_selector("#tab-parts.active #pf-body", state="visible")
    check("Parts tab activates and shows the finder",
          page.locator("#tab-parts.active").count() == 1)

    for slug, year, make, models, engine_chip, expect_verified in CARS:
        model = pf_search(page, year, make, models, engine_chip)
        check(f"{slug}: model option found", model is not None, str(models))
        if model is None:
            continue
        rows = page.locator("#pf-results .pf-row-card")
        check(f"{slug}: donor rows render", rows.count() > 0,
              page.locator("#pf-results").inner_text()[:120])
        if not rows.count():
            continue
        # Since 2026-10-23 the split sits in the always-visible toggle row
        # right under the head (counts + "Verified fits only").
        head = page.locator("#pf-results .pf-tier-counts").inner_text()
        check(f"{slug}: head reports verified/likely split",
              "verified" in head and "likely" in head, head[:120])
        n_ver = page.locator("#pf-results .pf-row-card.pf-verified").count()
        n_lik = page.locator("#pf-results .pf-row-card.pf-likely").count()
        if expect_verified:
            check(f"{slug}: at least one Verified-fit donor", n_ver > 0,
                  f"ver={n_ver} lik={n_lik}")
        chips = page.locator("#pf-results .pf-tier").count()
        check(f"{slug}: every row carries a tier chip",
              chips == rows.count(), f"{chips} chips / {rows.count()} rows")
        # Sorted by distance then confidence — distances must be
        # non-decreasing down the list.
        dists = page.eval_on_selector_all(
            "#pf-results .pf-row-card .dist",
            "els => els.map(e => parseInt(e.textContent))")
        check(f"{slug}: rows sorted by distance",
              all(a <= b for a, b in zip(dists, dists[1:])), str(dists[:8]))
        page.evaluate("document.getElementById('pf-results')"
                      ".scrollIntoView({block:'start'})")
        page.wait_for_timeout(250)
        page.screenshot(path=str(SHOTS / f"pf_{slug}_alternator.png"))
        print(f"     ver={n_ver} lik={n_lik} — "
              f"shot pf_{slug}_alternator.png")

    # ---- tab bar + cross-link + regression sweep --------------------------
    # Four tabs must fit the dock; labels must not wrap or clip.
    tabs = page.eval_on_selector_all(
        ".tabs .tab", """els => els.map(e => ({
          label: e.querySelector('.tab-label').textContent,
          w: e.getBoundingClientRect().width,
          clipped: e.scrollWidth > e.clientWidth + 1}))""")
    check("tab bar has 4 tabs (Cars/Yards/Parts/Alerts)",
          [t["label"] for t in tabs] == ["Cars", "Yards", "Parts", "Alerts"],
          str(tabs))
    check("no tab label clips at 390px", not any(t["clipped"] for t in tabs),
          str(tabs))
    page.screenshot(path=str(SHOTS / "parts_tab_mobile_390.png"))

    # Quiet cross-link hands off to the Yards price comparison with the
    # selected part prefilled.
    page.click("#pf-compare-link")
    page.wait_for_timeout(600)
    check("compare link lands on the Yards tab",
          page.locator("#tab-yards.active").count() == 1)
    cmp_val = page.input_value("#compare-input")
    check("compare combobox prefilled with the part",
          "alternator" in cmp_val.lower(), cmp_val)
    check("compare sheet opened from the hand-off",
          page.locator("#prices-sheet.open").count() == 1)
    page.screenshot(path=str(SHOTS / "parts_compare_handoff.png"))
    page.click("#prices-close")
    page.wait_for_timeout(300)

    # Other tabs still render (no layout/JS regressions from the move).
    for t in ("live", "alerts", "parts"):
        page.click(f".tab[data-tab='{t}']")
        page.wait_for_timeout(300)
        check(f"{t} tab renders after the move",
              page.locator(f"#tab-{t}.active").count() == 1)
    check("Cars tab carries no leftover finder markup",
          page.locator("#tab-live .part-finder").count() == 0)
    ctx.close()

    def boot(viewport, mobile, zip_code="85003"):
        c = browser.new_context(
            viewport=viewport, device_scale_factor=3 if mobile else 1,
            is_mobile=mobile, has_touch=mobile)
        p = c.new_page()
        p.add_init_script(PRO_BOOT)
        p.goto(f"http://127.0.0.1:{PORT}/index.html",
               wait_until="domcontentloaded")
        p.click("#live-filter-toggle")
        p.fill("#live-zip", zip_code)
        p.wait_for_selector("#live-grid .match-card, #live-grid .dim-card",
                            timeout=30000)
        p.click("#live-filter-toggle")
        p.click(".tab[data-tab='parts']")
        p.wait_for_timeout(400)
        return c, p

    # ---- 360px: the narrowest supported phone ----------------------------
    ctx, page = boot({"width": 360, "height": 780}, True)
    tabs = page.eval_on_selector_all(
        ".tabs .tab", "els => els.map(e => e.scrollWidth > e.clientWidth + 1)")
    check("no tab label clips at 360px", not any(tabs), str(tabs))
    page.screenshot(path=str(SHOTS / "parts_tab_mobile_360.png"))
    ctx.close()

    # ---- enthusiast checks (Phase A/B regression fixtures) -----------------
    # Run from Santa Fe Springs, CA (90670) — a 1999 Miata donor sits at that
    # yard, inside mazda-miata-18's verified 1999-2000 alternator group
    # (Denso 210-3155). Phoenix has no 99-00 Miata within the default radius,
    # so the honest app shows zero verified donors there.
    ctx, page = boot({"width": 390, "height": 844}, True, zip_code="90670")
    model = pf_search(page, "1999", "Mazda", ["Miata", "MX-5 Miata", "MX5"],
                      None)
    check("miata99: model option found", model is not None)
    if model is not None:
        rows = page.locator("#pf-results .pf-row-card")
        n_ver = page.locator("#pf-results .pf-row-card.pf-verified").count()
        check("miata99: donor rows render", rows.count() > 0)
        check("miata99: at least one Verified-fit donor (210-3155 group)",
              n_ver > 0, f"ver={n_ver} of {rows.count()}")
        page.screenshot(path=str(SHOTS / "pf_miata99_alternator.png"))
        print(f"     miata99 ver={n_ver} of {rows.count()} — "
              f"shot pf_miata99_alternator.png")

    # Body-part flow: 99 Corolla window regulator (standing in for the
    # suggested 95 Civic — no 92-95 Civic in the payload ships a window-
    # regulator row, so that search honestly returns zero donors; the
    # Corolla row's published window is 1995-2013 with dozens of donors).
    # Every row must carry an honest tier chip.
    model = pf_search(page, "1999", "Toyota", ["Corolla"], None,
                      part="window regulator")
    check("corolla99: model option found", model is not None)
    if model is not None:
        rows = page.locator("#pf-results .pf-row-card")
        check("corolla99: donor rows render for a body part", rows.count() > 0,
              page.locator("#pf-results").inner_text()[:120])
        chips = page.locator("#pf-results .pf-tier").count()
        check("corolla99: every row carries a tier chip",
              rows.count() > 0 and chips == rows.count(),
              f"{chips} chips / {rows.count()} rows")
        page.screenshot(path=str(SHOTS / "pf_corolla99_window_regulator.png"))
        print(f"     corolla99 rows={rows.count()} — "
              f"shot pf_corolla99_window_regulator.png")

    # ---- E46 M3: the performance-trim platform fix -------------------------
    # Body part: the M3 maps into the E46 platform group, so a window-
    # regulator search must surface regular E46 donors (112 within 100 mi of
    # 90670 in the current snapshot) at the honest "likely" tier.
    model = pf_search(page, "2002", "BMW", ["M3"], None,
                      part="window regulator")
    check("m3: model option found", model is not None)
    if model is not None:
        rows = page.locator("#pf-results .pf-row-card")
        check("m3 window regulator: E46 platform donors render",
              rows.count() > 0,
              page.locator("#pf-results").inner_text()[:120])
        n_ver = page.locator("#pf-results .pf-row-card.pf-verified").count()
        check("m3 window regulator: trim platform rows are likely, not verified",
              rows.count() > 0 and n_ver == 0,
              f"ver={n_ver} of {rows.count()}")
        chips = page.locator("#pf-results .pf-tier").count()
        check("m3 window regulator: every row carries a tier chip",
              rows.count() > 0 and chips == rows.count(),
              f"{chips} chips / {rows.count()} rows")
        body = page.locator("#pf-results").inner_text()
        check("m3 window regulator: coupe/convertible caveat shipped",
              "coupe/convertible" in body, body[:200])
        page.screenshot(path=str(SHOTS / "pf_m3_window_regulator.png"))
        print(f"     m3 regulator rows={rows.count()} — "
              f"shot pf_m3_window_regulator.png")

    # Engine part: the S54 is unpublished, so the alternator search must show
    # the honest trim-specific message (with the live M3 count) instead of a
    # bare "no data", and point at the body-part search.
    model = pf_search(page, "2002", "BMW", ["M3"], None, part="alternator")
    check("m3 alternator: model option found", model is not None)
    if model is not None:
        empty = page.locator("#pf-results .pf-empty")
        check("m3 alternator: honest empty state renders",
              empty.count() == 1 and
              page.locator("#pf-results .pf-row-card").count() == 0)
        txt = empty.inner_text() if empty.count() else ""
        check("m3 alternator: message names the S54 as M3-specific",
              "S54" in txt and "M3-specific" in txt, txt[:200])
        check("m3 alternator: message counts tracked M3 donors",
              "1 in tracked yards" in txt, txt[:200])
        check("m3 alternator: message points at the body-part search",
              "window regulator" in txt.lower(), txt[:200])
        page.screenshot(path=str(SHOTS / "pf_m3_alternator_honest.png"))
        print("     m3 alternator honest message — "
              "shot pf_m3_alternator_honest.png")
    ctx.close()

    # ---- P0 catalog flows (PART_CATALOG_SPEC, 2026-10) ---------------------
    # Engine assembly: 5.3 Vortec truck engine near Phoenix. The family
    # answers the search; the three §4 honesty notes must show, and no
    # resale band appears (you can't carry an engine out).
    ctx, page = boot({"width": 390, "height": 844}, True)
    model = pf_search(page, "2004", "Chevrolet", ["Tahoe"], "5.3",
                      part="engine assembly")
    check("tahoe04 engine: model option found", model is not None)
    if model is not None:
        rows = page.locator("#pf-results .pf-row-card")
        check("tahoe04 engine: Vortec donors render", rows.count() > 0,
              page.locator("#pf-results").inner_text()[:120])
        body = page.locator("#pf-results").inner_text()
        check("tahoe04 engine: long-block honesty note shows",
              "long block" in body, body[:200])
        check("tahoe04 engine: unknown-mileage note shows",
              "Mileage and internal condition are unknown" in body)
        check("tahoe04 engine: pull-reality note shows (hours, call ahead)",
              "call ahead" in body and "hours" in body)
        check("tahoe04 engine: no resale band on engine rows",
              "worth" not in body, body[:200])
        chips = page.locator("#pf-results .pf-tier").count()
        check("tahoe04 engine: every row carries a tier chip",
              rows.count() > 0 and chips == rows.count(),
              f"{chips} chips / {rows.count()} rows")
        n_ver = page.locator("#pf-results .pf-row-card.pf-verified").count()
        page.evaluate("document.getElementById('pf-results')"
                      ".scrollIntoView({block:'start'})")
        page.wait_for_timeout(250)
        page.screenshot(path=str(SHOTS / "pf_tahoe04_engine_assembly.png"))
        print(f"     tahoe04 engine ver={n_ver} of {rows.count()} — "
              f"shot pf_tahoe04_engine_assembly.png")

    # Front door: class B — generation-window donors of the seeker's own
    # model, always Likely, paint-code warning on every row.
    model = pf_search(page, "2009", "Honda", ["Accord"], None,
                      part="front door")
    check("accord09 door: model option found", model is not None)
    if model is not None:
        rows = page.locator("#pf-results .pf-row-card")
        check("accord09 door: same-generation donors render", rows.count() > 0,
              page.locator("#pf-results").inner_text()[:120])
        n_ver = page.locator("#pf-results .pf-row-card.pf-verified").count()
        check("accord09 door: generation rows are Likely, never Verified",
              rows.count() > 0 and n_ver == 0,
              f"ver={n_ver} of {rows.count()}")
        body = page.locator("#pf-results").inner_text()
        check("accord09 door: paint-code warning on rows",
              "paint code" in body, body[:200])
        check("accord09 door: generation window named in the warns",
              "generation" in body, body[:200])
        page.screenshot(path=str(SHOTS / "pf_accord09_door_front.png"))
        print(f"     accord09 door rows={rows.count()} — "
              f"shot pf_accord09_door_front.png")

    # Automatic transmission: class C (combo) — generation x engine chip,
    # always Likely, with the verify-the-trans-code note visible.
    model = pf_search(page, "2015", "Nissan", ["Altima"], "2.5",
                      part="automatic transmission")
    check("altima15 trans: model option found", model is not None)
    if model is not None:
        rows = page.locator("#pf-results .pf-row-card")
        check("altima15 trans: same-gen donors render", rows.count() > 0,
              page.locator("#pf-results").inner_text()[:120])
        n_ver = page.locator("#pf-results .pf-row-card.pf-verified").count()
        check("altima15 trans: combo rows are Likely, never Verified",
              rows.count() > 0 and n_ver == 0,
              f"ver={n_ver} of {rows.count()}")
        body = page.locator("#pf-results").inner_text()
        check("altima15 trans: verify-code note visible (head)",
              "verify the transmission code" in body
              or "ALWAYS verify" in body, body[:300])
        check("altima15 trans: verify-code warn on each row",
              "verify the trans code" in body, body[:300])
        check("altima15 trans: no resale band on transmission rows",
              "worth" not in body, body[:200])
        page.screenshot(path=str(SHOTS / "pf_altima15_transmission.png"))
        print(f"     altima15 trans rows={rows.count()} — "
              f"shot pf_altima15_transmission.png")
    ctx.close()

    # ---- desktop: tab active with a real search on screen -----------------
    ctx, page = boot({"width": 1280, "height": 900}, False)
    model = pf_search(page, "2005", "Toyota", ["Camry"], "2AZ")
    check("desktop: Camry search renders on the Parts tab",
          model is not None
          and page.locator("#pf-results .pf-row-card").count() > 0)
    page.screenshot(path=str(SHOTS / "parts_tab_desktop.png"))
    ctx.close()
    browser.close()

print()
if FAILS:
    print(f"{len(FAILS)} FAILURE(S):", *FAILS, sep="\n  - ")
    sys.exit(1)
print(f"all part-finder e2e tests passed — screenshots in {SHOTS}/")
