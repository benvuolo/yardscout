#!/usr/bin/env python3
"""Browser e2e for the Parts tab's two modes + the retired Live filter.

Browse mode (owner decision 2026-10-23): part chosen with NO car lists every
nearby car CARRYING the part — engine-class categories browse by engine
family ("any 5.3 Vortec near me"), platform parts by spotted-part keywords.
Part + car still runs the unchanged fitment flow. The old Live-tab
'Part spotted on car' filter is gone; its drawer slot keeps only a pointer.

    ~/projects/sigma-mcp/.venv/bin/python backend/test/interchange_e2e.py

Screenshots land in /tmp/yardscout_shots/.
"""
import http.server
import os
import pathlib
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
OVERRIDE = os.environ.get("INVENTORY_OVERRIDE", "")
SHOTS = pathlib.Path("/tmp/yardscout_shots")
SHOTS.mkdir(exist_ok=True)
PORT = 8613
FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = ""):
    print(("ok   " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(DOCS), **kw)

    def translate_path(self, path):
        # Overlay: serve a freshly rebuilt inventory without touching the
        # committed data file (the scan workflow owns it on main).
        if OVERRIDE and path.split("?")[0] == "/data/inventory_live.json":
            return OVERRIDE
        return super().translate_path(path)

    def log_message(self, *a):
        pass


def serve():
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


threading.Thread(target=serve, daemon=True).start()

IPHONE = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 3,
          "is_mobile": True, "has_touch": True}
PRO_BOOT = """
  localStorage.setItem('jh_pro', '1');
  localStorage.setItem('jh_pro_source', 'account');
  localStorage.setItem('jh_honesty_ack', '1');
"""
FREE_BOOT = "localStorage.setItem('jh_honesty_ack', '1');"


def boot(ctx, init_js):
    page = ctx.new_page()
    page.add_init_script(init_js)
    page.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="domcontentloaded")
    # Zip via the filters panel; geocoding uses zippopotam (network).
    page.click("#live-filter-toggle")
    page.fill("#live-zip", "30310")   # Atlanta — dense Pull-A-Part coverage
    page.wait_for_selector("#live-grid .match-card, #live-grid .dim-card",
                           timeout=30000)
    page.click("#live-filter-toggle")  # collapse so screenshots show the grid
    return page


def pf_pick_part(page, label):
    """Open the Parts tab and choose a part from the combobox (no car)."""
    page.click(".tab[data-tab='parts']")
    page.wait_for_timeout(400)
    page.fill("#pf-part", label)
    page.wait_for_selector("#pf-part-suggest .compare-suggest-item",
                           timeout=5000)
    page.locator("#pf-part-suggest .compare-suggest-item").first.dispatch_event(
        "mousedown")
    page.wait_for_timeout(700)   # browse renders immediately on part pick


with sync_playwright() as pw:
    browser = pw.chromium.launch()

    # ---------------- Pro: browse mode, both rule classes -----------------
    ctx = browser.new_context(**IPHONE)
    page = boot(ctx, PRO_BOOT)

    # Platform part, no car -> spotted-part browse with values.
    pf_pick_part(page, "tailgate")
    rows = page.locator("#pf-results .pf-row-card.pf-browse")
    check("tailgate browse: cards render without a car", rows.count() > 0,
          page.locator("#pf-results").inner_text()[:120])
    head = page.locator("#pf-results .pf-results-head").inner_text()
    check("tailgate browse: honest header (all cars + add your car)",
          "Showing all cars with this part near you" in head
          and "add your car" in head, head[:160])
    check("tailgate browse: no fit-tier chips (no claims without a car)",
          page.locator("#pf-results .pf-tier").count() == 0)
    body = page.locator("#pf-results").inner_text()
    check("tailgate browse: resale value shown per row (pro)",
          "Used online: ~$" in body, body[:200])
    dists = page.eval_on_selector_all(
        "#pf-results .pf-row-card .dist",
        "els => els.map(e => parseInt(e.textContent))")
    check("tailgate browse: rows sorted by distance",
          all(a <= b for a, b in zip(dists, dists[1:])), str(dists[:8]))
    page.evaluate("document.getElementById('pf-results')"
                  ".scrollIntoView({block:'start'})")
    page.wait_for_timeout(250)
    page.screenshot(path=str(SHOTS / "1_browse_tailgate.png"))

    # Engine-class part, no car -> FAMILY browse (the 'any 5.3 near me' flow),
    # never keyword matching.
    pf_pick_part(page, "engine assembly")
    check("engine browse: family picker renders",
          page.locator("#pf-browse-fam").count() == 1)
    prompt = page.locator("#pf-results .pf-empty")
    check("engine browse: pick-an-engine prompt (not a broken state)",
          prompt.count() == 1 and "pick the engine" in prompt.inner_text(),
          prompt.inner_text()[:120] if prompt.count() else "no prompt")
    fam_val = page.evaluate("""() => {
      const os = [...document.querySelectorAll('#pf-browse-fam option')];
      const o = os.find(o => o.textContent.includes('5.3'));
      return o ? o.value : '';
    }""")
    check("engine browse: a 5.3 family exists in the picker", bool(fam_val))
    page.select_option("#pf-browse-fam", fam_val)
    page.wait_for_timeout(700)
    rows = page.locator("#pf-results .pf-row-card.pf-browse")
    check("engine browse: 5.3 donors render by family data", rows.count() > 0,
          page.locator("#pf-results").inner_text()[:120])
    body = page.locator("#pf-results").inner_text()
    check("engine browse: header counts cars + add-your-car pointer",
          "carrying a" in body and "add your car" in body, body[:200])
    check("engine browse: VIN-confirmed badge on decoded donors",
          page.locator("#pf-results .pf-tier-verified").count() > 0)
    check("engine browse: no resale band on engines", "worth" not in body,
          body[:200])
    page.evaluate("document.getElementById('pf-results')"
                  ".scrollIntoView({block:'start'})")
    page.wait_for_timeout(250)
    page.screenshot(path=str(SHOTS / "2_browse_engine_53.png"))

    # Add the car -> the unchanged fitment flow takes over (mode switch).
    page.select_option("#pf-year", "2004")
    page.select_option("#pf-make", "Chevrolet")
    page.wait_for_timeout(300)
    page.select_option("#pf-model", "Tahoe")
    page.click("#pf-go")
    page.wait_for_timeout(700)
    if (not page.locator("#pf-results .pf-row-card").count()
            and page.locator("#pf-engine .pf-chip").count()):
        chips = page.locator("#pf-engine .pf-chip")
        for i in range(chips.count()):
            if "5.3" in chips.nth(i).inner_text():
                chips.nth(i).click()
                break
        page.wait_for_timeout(700)
    rows = page.locator("#pf-results .pf-row-card")
    tiers = page.locator("#pf-results .pf-tier")
    check("fitment unchanged: car added -> tiered donor rows",
          rows.count() > 0 and tiers.count() >= rows.count(),
          f"{rows.count()} rows / {tiers.count()} tiers")
    fit_head = page.locator("#pf-results .pf-tier-counts").inner_text()   # toggle row under the head
    check("fitment unchanged: verified/likely split in head",
          "verified" in fit_head and "likely" in fit_head, fit_head[:140])
    page.screenshot(path=str(SHOTS / "3_fitment_unchanged.png"))

    # ---- Filters drawer: old field gone, single pointer remains ----------
    page.click(".tab[data-tab='live']")
    page.wait_for_timeout(300)
    if not page.locator("#live-controls.open").count():
        page.click("#live-filter-toggle")
        page.wait_for_timeout(300)
    check("drawer: 'Part spotted on car' field removed",
          page.locator("#live-part-search").count() == 0)
    pointer = page.locator("#live-parts-pointer")
    check("drawer: single pointer remains",
          pointer.count() == 1 and pointer.is_visible()
          and "Parts" in pointer.inner_text())
    badge_probe = page.evaluate(
        "() => typeof updateLiveFilterCount === 'function'")
    check("drawer: filter-count fn intact after revert", badge_probe)
    pointer.scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    page.screenshot(path=str(SHOTS / "4_drawer_pointer_only.png"))
    pointer.click()
    page.wait_for_timeout(400)
    check("drawer pointer lands on the Parts tab",
          page.locator("#tab-parts.active").count() == 1)

    # Yards drawer regression — same handle/panel mechanics, own state.
    page.click(".tab[data-tab='yards']")
    page.wait_for_timeout(300)
    if not page.locator("#yards-controls.open").count():
        page.click("#yards-filter-toggle")
        page.wait_for_timeout(300)
    check("yards drawer still opens",
          page.locator("#yards-controls.open").count() == 1)
    page.fill("#yards-search", "pull")
    page.wait_for_timeout(400)
    check("yards keyword search still filters",
          page.locator("#yards-grid .yard-card").count() > 0)
    ctx.close()

    # ---------------- desktop width: engine browse ------------------------
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = boot(ctx, PRO_BOOT)
    pf_pick_part(page, "engine assembly")
    fam_val = page.evaluate("""() => {
      const os = [...document.querySelectorAll('#pf-browse-fam option')];
      const o = os.find(o => o.textContent.includes('5.3'));
      return o ? o.value : '';
    }""")
    page.select_option("#pf-browse-fam", fam_val)
    page.wait_for_timeout(700)
    check("desktop: 5.3 engine browse renders",
          page.locator("#pf-results .pf-row-card.pf-browse").count() > 0)
    page.screenshot(path=str(SHOTS / "5_browse_engine_desktop.png"))
    ctx.close()

    # ---------------- Free tier: browse values stay blurred ---------------
    ctx = browser.new_context(**IPHONE)
    page = boot(ctx, FREE_BOOT)
    pf_pick_part(page, "tailgate")
    rows = page.locator("#pf-results .pf-row-card.pf-browse")
    check("free: browse still lists cars", rows.count() > 0)
    # Since 2026-10-26 free rows carry no value at all (no per-row blur);
    # one honest "Pro adds…" line in the head says what's missing.
    check("free: browse resale values blurred",
          page.locator("#pf-results .pf-results-head .lock-text").count() == 1)
    import re as _re
    check("free: no real value strings leak",
          not _re.search(r"(Used online: ~|worth )\$\d", page.locator("#pf-results").inner_text()))
    page.screenshot(path=str(SHOTS / "6_browse_free_blur.png"))

    # Live cards' free blur unaffected by the filter's removal.
    page.click(".tab[data-tab='live']")
    page.wait_for_timeout(300)
    leak = page.evaluate("""() => {
      document.querySelectorAll('#live-grid .parts-details summary')
        .forEach(s => s.click());
      return document.querySelectorAll('#live-grid .locked-blur').length;
    }""")
    check("free: live-card blur unaffected", leak > 0, str(leak))
    ctx.close()
    browser.close()

print()
if FAILS:
    print(f"{len(FAILS)} FAILURE(S):", *FAILS, sep="\n  - ")
    sys.exit(1)
print(f"all interchange e2e tests passed — screenshots in {SHOTS}/")
