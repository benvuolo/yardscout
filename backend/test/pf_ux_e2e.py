#!/usr/bin/env python3
"""Browser e2e for the 2026-10-23 Parts tab UX pair (owner requests):

1. 'Verified fits only' toggle — counts always visible, filtering is a view
   change (no refetch), applies in fitment mode and engine-browse mode.
2. Try-example chips greeting the empty tab — each one prefills AND runs a
   search that returns results near the zip; one engine-hunt hint line.

Phone-first: runs the whole pass at 390px and re-checks layout at 360px.

    ~/projects/sigma-mcp/.venv/bin/python backend/test/pf_ux_e2e.py [base_url]

With no argument it serves docs/ locally; pass a production URL to verify
the deployed site. Screenshots land in /tmp/yardscout_shots/.
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
PORT = 8631
FAILS: list[str] = []

BASE = sys.argv[1].rstrip("/") + "/" if len(sys.argv) > 1 else None
if not BASE:
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(DOCS), **kw)

        def log_message(self, *a):
            pass

    threading.Thread(
        target=http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
        .serve_forever, daemon=True).start()
    BASE = f"http://127.0.0.1:{PORT}/"
TAG = "prod" if BASE.startswith("https") else "local"


def check(name: str, cond: bool, detail: str = ""):
    print(("ok   " if cond else "FAIL ") + name
          + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


BOOT = """
  localStorage.setItem('jh_pro', '1');
  localStorage.setItem('jh_pro_source', 'account');
  localStorage.setItem('jh_honesty_ack', '1');
"""


def fresh_parts_tab(page, zip_code="85003"):
    page.goto(BASE + "index.html", wait_until="domcontentloaded")
    page.click("#live-filter-toggle")
    page.fill("#live-zip", zip_code)
    page.wait_for_selector("#live-grid .match-card, #live-grid .dim-card",
                           timeout=30000)
    page.click("#live-filter-toggle")
    page.click(".tab[data-tab='parts']")
    page.wait_for_selector("#tab-parts.active #pf-body", state="visible")
    page.wait_for_selector("#pf-results .pf-try-chip", timeout=10000)


def visible_cards(page):
    return page.eval_on_selector_all(
        "#pf-results .pf-row-card",
        "els => els.filter(e => getComputedStyle(e).display !== 'none').length")


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for width in (390, 360):
        ctx = browser.new_context(
            viewport={"width": width, "height": 844}, device_scale_factor=2,
            is_mobile=True, has_touch=True)
        page = ctx.new_page()
        page.add_init_script(BOOT)
        w = f"@{width}"

        # ---- empty-tab greeting --------------------------------------
        fresh_parts_tab(page)
        chips = page.locator("#pf-results .pf-try-chip")
        n_chips = chips.count()
        check(f"{w} 2-3 try chips greet the empty tab", 2 <= n_chips <= 3,
              str(n_chips))
        labels = [chips.nth(i).inner_text() for i in range(n_chips)]
        check(f"{w} 'Try:' label present",
              page.locator("#pf-results .pf-try-label").inner_text() == "Try:")
        check(f"{w} engine-hunt hint line present",
              "Engine assembly" in
              page.locator("#pf-results .pf-hint").inner_text())
        check(f"{w} old instruction paragraph trimmed",
              "published part-number application list" not in
              page.locator("#tab-parts .info-box").inner_text())
        # No horizontal overflow at phone widths.
        over = page.evaluate(
            "document.documentElement.scrollWidth"
            " - document.documentElement.clientWidth")
        check(f"{w} no horizontal overflow on empty tab", over <= 0, str(over))
        if width == 390:
            page.screenshot(path=str(SHOTS / f"after_parts_empty_{TAG}.png"))
        else:
            page.screenshot(path=str(SHOTS / f"after_parts_empty_360_{TAG}.png"))

        # ---- every chip runs and lands on results --------------------
        for i in range(n_chips):
            fresh_parts_tab(page)
            page.locator("#pf-results .pf-try-chip").nth(i).click()
            page.wait_for_timeout(900)
            n = page.locator("#pf-results .pf-row-card").count()
            check(f"{w} chip {i + 1} ('{labels[i][:40]}') returns results",
                  n > 0, page.locator("#pf-results").inner_text()[:120])

        # ---- verified-only toggle: fitment mode ----------------------
        fresh_parts_tab(page)
        page.locator("#pf-results .pf-try-chip").first.click()  # fitment chip
        page.wait_for_timeout(900)
        counts = page.locator("#pf-results .pf-tier-counts")
        check(f"{w} tier counts render beside the toggle", counts.count() == 1)
        txt = counts.inner_text() if counts.count() else ""
        check(f"{w} counts use tier vocabulary",
              "verified" in txt and "likely" in txt, txt)
        # The 'what verified means' line must be VISIBLE text, not a hover
        # tooltip phone users never see (honesty audit, 2026-10-23).
        defs = page.locator("#pf-results .pf-hint",
                            has_text="published catalog fitment data")
        check(f"{w} visible Verified definition under the header",
              defs.count() == 1 and defs.first.is_visible())
        n_all = page.locator("#pf-results .pf-row-card").count()
        n_ver = page.locator("#pf-results .pf-row-card.pf-verified").count()
        # Rendering caps at the 120 nearest; the counts speak for the FULL
        # donor list (that's their whole point), so check against the head's
        # total, not the capped DOM.
        head_total = int(page.locator("#pf-results .pf-results-head strong")
                         .inner_text().split()[0].replace(",", ""))
        c_ver, c_lik = (int(x.replace(",", "")) for x in
                        txt.replace(" verified", "").replace(" likely", "")
                        .split(" · "))
        check(f"{w} counts sum to the head's donor total",
              c_ver + c_lik == head_total,
              f"txt='{txt}' head={head_total}")
        check(f"{w} the showcase fitment chip carries verified rows",
              c_ver > 0 and n_ver > 0, f"c_ver={c_ver} rendered={n_ver}")
        req_before = []
        page.on("request", lambda r: req_before.append(r.url))
        page.check("#pf-vonly-cb")
        page.wait_for_timeout(300)
        check(f"{w} toggle ON hides likely rows, keeps verified",
              visible_cards(page) == n_ver,
              f"visible={visible_cards(page)} ver={n_ver}")
        check(f"{w} counts still visible while filtered",
              counts.is_visible() and "likely" in counts.inner_text())
        data_fetches = [u for u in req_before if "/data/" in u or ".json" in u]
        check(f"{w} toggling made no refetch", not data_fetches,
              str(data_fetches[:2]))
        if width == 390:
            page.screenshot(path=str(SHOTS / f"after_toggle_on_{TAG}.png"))
        page.uncheck("#pf-vonly-cb")
        page.wait_for_timeout(300)
        check(f"{w} toggle OFF restores all {n_all} rows",
              visible_cards(page) == n_all, str(visible_cards(page)))

        # ---- toggle in engine-browse mode (VIN-confirmed vocabulary) --
        hunt_i = next((j for j, l in enumerate(labels) if l.startswith("Hunt")),
                      None)
        if hunt_i is not None:
            fresh_parts_tab(page)
            page.locator("#pf-results .pf-try-chip").nth(hunt_i).click()
            page.wait_for_timeout(900)
            bt = page.locator("#pf-results .pf-tier-counts")
            check(f"{w} browse mode: VIN-confirmed counts beside toggle",
                  bt.count() == 1 and "VIN-confirmed" in bt.inner_text(),
                  bt.inner_text() if bt.count() else "no counts")
            n_vin = page.locator("#pf-results .pf-row-card.pf-vin").count()
            page.check("#pf-vonly-cb")
            page.wait_for_timeout(300)
            vis = visible_cards(page)
            none_note = page.locator("#pf-results .pf-vonly-none")
            honest = (vis == n_vin if n_vin
                      else (vis == 0 and none_note.is_visible()))
            check(f"{w} browse toggle filters to VIN-confirmed (or honest "
                  "zero-state)", honest, f"vis={vis} vin={n_vin}")
            if width == 390:
                page.screenshot(path=str(SHOTS / f"after_browse_toggle_{TAG}.png"))
        ctx.close()
    browser.close()

print()
if FAILS:
    print(f"{len(FAILS)} FAILURE(S):", *FAILS, sep="\n  - ")
    sys.exit(1)
print(f"parts-tab UX e2e passed against {BASE}")
