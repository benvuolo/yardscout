#!/usr/bin/env python3
"""Browser e2e for the interchange feature: part-first search, part-hit
highlight, 'swaps with' provenance notes, free-tier blur. Starts its own
static server over docs/ (optionally overlaying a rebuilt inventory file) and
drives Chromium at an iPhone viewport.

    INVENTORY_OVERRIDE=/tmp/inv_interchange.json \
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
        # Overlay: serve the freshly rebuilt inventory without touching the
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


with sync_playwright() as pw:
    browser = pw.chromium.launch()

    # ---------------- Pro: search, highlight, provenance ----------------
    ctx = browser.new_context(**IPHONE)
    page = boot(ctx, PRO_BOOT)

    page.fill("#live-part-search", "tailgate")
    page.wait_for_timeout(600)   # debounce + render
    cards = page.locator("#live-grid .match-card")
    check("part search returns cards", cards.count() > 0, str(cards.count()))

    # Open the first card's parts and check the highlight + provenance.
    page.locator("#live-grid .parts-details summary").first.click()
    page.wait_for_timeout(200)
    hits = page.locator(".part-item.part-hit")
    check("matching part row is highlighted", hits.count() > 0)
    hit_text = hits.first.inner_text().lower()
    check("highlighted row matches the query",
          "tailgate" in hit_text, hit_text[:80])
    page.screenshot(path=str(SHOTS / "1_part_search_tailgate.png"))

    # Find a card whose matched row carries interchange provenance.
    found_shared = page.evaluate("""() => {
      const notes = document.querySelectorAll('#live-grid .shared-note');
      return notes.length ? notes[0].textContent : '';
    }""")
    if not found_shared:
        # Tailgate hits may all be originals in this radius — search a family
        # part that always carries provenance.
        page.fill("#live-part-search", "3rd row seat")
        page.wait_for_timeout(600)
        for i in range(min(6, page.locator("#live-grid .parts-details summary").count())):
            page.locator("#live-grid .parts-details summary").nth(i).click()
        page.wait_for_timeout(300)
        found_shared = page.evaluate("""() => {
          const notes = document.querySelectorAll('#live-grid .shared-note');
          return notes.length ? notes[0].textContent : '';
        }""")
    check("'swaps with' provenance renders on a part row",
          "swaps with" in (found_shared or ""), repr(found_shared)[:100])
    if found_shared:
        page.evaluate("""() => {
          const n = document.querySelector('#live-grid .shared-note');
          n.closest('.match-card, .dim-card').scrollIntoView({block:'center'});
        }""")
        page.wait_for_timeout(300)
        page.screenshot(path=str(SHOTS / "2_interchange_note.png"))

    # Clear button restores the unfiltered grid.
    before = page.locator("#live-grid .match-card, #live-grid .dim-card").count()
    page.click("#live-part-search-clear")
    page.wait_for_timeout(400)
    after = page.locator("#live-grid .match-card, #live-grid .dim-card").count()
    check("clear restores the grid", after >= before, f"{before} -> {after}")

    # Nonsense query shows the dedicated empty state.
    page.fill("#live-part-search", "zzzznotapart")
    page.wait_for_timeout(600)
    empty = page.locator("#live-grid .empty-state").inner_text()
    check("empty state names the query", "zzzznotapart" in empty, empty[:80])
    page.screenshot(path=str(SHOTS / "3_empty_state.png"))
    ctx.close()

    # ---------------- Free tier: search filters, values stay blurred ------
    ctx = browser.new_context(**IPHONE)
    page = boot(ctx, FREE_BOOT)
    page.fill("#live-part-search", "tailgate")
    page.wait_for_timeout(600)
    check("free: search still filters",
          page.locator("#live-grid .match-card").count() > 0)
    # Open parts on a NON-sample locked card and confirm nothing leaked.
    leak = page.evaluate("""() => {
      document.querySelectorAll('#live-grid .parts-details summary')
        .forEach(s => s.click());
      const locked = document.querySelectorAll('#live-grid .locked-blur');
      const shared = document.querySelectorAll('#live-grid .shared-note');
      // shared-notes may appear ONLY within the single free sample card
      const sample = document.querySelector('#live-grid .sample-note');
      const sampleCard = sample ? sample.closest('.match-card') : null;
      const leaked = [...shared].some(n =>
        !sampleCard || !sampleCard.contains(n));
      return {lockedCount: locked.length, leaked};
    }""")
    check("free: blurred rows still blurred", leak["lockedCount"] > 0,
          str(leak))
    check("free: provenance only on the sample card", not leak["leaked"],
          str(leak))
    page.screenshot(path=str(SHOTS / "4_free_tier_search.png"))
    ctx.close()
    browser.close()

print()
if FAILS:
    print(f"{len(FAILS)} FAILURE(S):", *FAILS, sep="\n  - ")
    sys.exit(1)
print(f"all interchange e2e tests passed — screenshots in {SHOTS}/")
