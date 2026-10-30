#!/usr/bin/env python3
"""Web-layer e2e for the alert-freshness fixes (docs/app.js):

  1. resume self-heal — loaded scrapedAt >1h old + visibilitychange→visible
     triggers a background refetch and swaps the new scan in place; a fresh
     scrapedAt does NOT refetch (threshold respected).
  2. alert entry, warm — openFromAlert(id) (what the native notification-tap
     listener and the SW 'open-alert' message call) bypasses the cache,
     refetches, and focuses the alerted car's card even when that car is
     missing from the stale in-memory copy (the 19:44 4Runner incident).
  3. alert entry, cold — launching on #alert=<id> normalizes to #car=<id>,
     fetches past the cache, and lands on the card.

The static server serves docs/ as-is but owns the inventory: the full
inventory_live.json AND the radius-first shards under /data/inv/ (built from
the same payload with scraper/inventory_shards.py — exactly what the scan
publishes). Tests swap the payload ("a new scan published") and count hits on
the two entry points the app revalidates: inv/manifest.json and
inventory_live.json.

Run from backend/:  ../.venv/bin/python test/alert_freshness_e2e.py
"""

import http.server
import json
import sys
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

BACKEND = Path(__file__).resolve().parent.parent
DOCS = BACKEND.parent / "docs"
sys.path.insert(0, str(BACKEND.parent / "scraper"))
from inventory_shards import write_inventory_shards  # noqa: E402

SHARD_ROOT = Path(tempfile.mkdtemp(prefix="ys-alert-fresh-"))
WEB_PORT = 8793
WEB = f"http://127.0.0.1:{WEB_PORT}"

passed, failed = [], []


def check(name, cond, detail=""):
    (passed if cond else failed).append(name)
    print(("  ✓ " if cond else "  ✗ ") + name + (f"  [{detail}]" if detail and not cond else ""))


def iso_ago(minutes):
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


FIELDS = ["id", "vin", "year", "make", "model", "row", "dateAdded", "yard", "partSet", "maxValue", "premium"]
YARD_FIELDS = ["location", "city", "state", "lat", "lng", "avgLifespanDays", "lifespanBasis"]


def vehicle(vid, model="4Runner", date_added=None):
    # A schema-v2 row (what the scraper publishes), all at one Ogden yard.
    return [vid, "", 1999, "Toyota", model, "42",
            date_added or datetime.now(timezone.utc).strftime("%Y-%m-%d"), 0, 0, 0, 0]


def payload(scraped_at, vehicles):
    return {
        "schemaVersion": 2, "scrapedAt": scraped_at, "pricesLastReviewed": "2026-10-01",
        "fields": FIELDS, "yardFields": YARD_FIELDS,
        "yards": [["Pick-n-Pull - Ogden", "Ogden", "UT", 41.2, -111.97, 90, "yard"]],
        "partSets": [[]], "vpic": {}, "vehicles": vehicles,
    }


def shard_dir(inv):
    """The /data/inv/ tree for this payload, built once per scan."""
    d = SHARD_ROOT / inv["scrapedAt"].replace(":", "-")
    if not (d / "inv" / "manifest.json").exists():
        write_inventory_shards(inv, None, d)
    return d / "inv"


class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True


class Handler(http.server.SimpleHTTPRequestHandler):
    # swapped by tests
    inventory = payload(iso_ago(10), [vehicle(101)])
    hits = []

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(DOCS), **kw)

    def log_message(self, *a):
        pass

    def _json(self, body):
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path.endswith("/data/inventory_live.json"):
            Handler.hits.append(self.path)
            return self._json(json.dumps(Handler.inventory).encode())
        if "/data/inv/" in path:
            name = path.rsplit("/", 1)[1]
            if name == "manifest.json":
                Handler.hits.append(self.path)   # the revalidation entry point
            f = shard_dir(Handler.inventory) / name
            if not f.exists():
                self.send_error(404)
                return
            return self._json(f.read_bytes())
        super().do_GET()


def wait_for(page, expr, timeout_s=15):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if page.evaluate(expr):
            return True
        time.sleep(0.25)
    return False


def new_page(browser):
    ctx = browser.new_context()  # fresh storage: scenarios stay independent
    # A saved zip (Ogden, where the test yard is): since 2026-10-30 a free
    # visitor with no zip/watch/link doesn't load inventory in the background
    # at all, and alert users always have one of those.
    ctx.add_init_script("try { localStorage.setItem('jh_honesty_ack','1');"
                        " localStorage.setItem('ys_install_hint','1');"
                        " if (!localStorage.getItem('jh_zip')) localStorage.setItem('jh_zip','84401'); } catch(e) {}")
    return ctx, ctx.new_page()


def main():
    server = Server(("127.0.0.1", WEB_PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ── 1a. fresh data + resume → NO refetch ─────────────────────────────
        Handler.inventory = payload(iso_ago(10), [vehicle(101)])
        Handler.hits = []
        ctx, page = new_page(browser)
        page.goto(WEB + "/")
        check("app loads inventory at boot", wait_for(page, "typeof liveLoaded !== 'undefined' && liveLoaded"))
        boot_hits = len(Handler.hits)
        page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
        time.sleep(2)
        check("resume with fresh scan (10 min old) does not refetch",
              len(Handler.hits) == boot_hits, f"hits {boot_hits}→{len(Handler.hits)}")
        ctx.close()

        # ── 1b. stale data + resume → background refetch, in-place update ────
        Handler.inventory = payload(iso_ago(180), [vehicle(101)])
        Handler.hits = []
        ctx, page = new_page(browser)
        page.goto(WEB + "/")
        wait_for(page, "typeof liveLoaded !== 'undefined' && liveLoaded")
        # Let the radius-first background load finish first: a scan that
        # publishes MID-load is caught by the shard scrapedAt check and
        # re-fetched fresh (one extra manifest hit, by design).
        wait_for(page, "typeof liveComplete !== 'undefined' && liveComplete", 30)
        boot_hits = len(Handler.hits)
        # a new scan publishes while the app sits in the background
        Handler.inventory = payload(iso_ago(1), [vehicle(101), vehicle(202, model="Tacoma")])
        page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
        check("resume with stale scan (3 h old) refetches",
              wait_for(page, f"liveScrapedAt === '{Handler.inventory['scrapedAt']}'"),
              f"hits {boot_hits}→{len(Handler.hits)}")
        check("new scan swapped in place (new car present)",
              wait_for(page, "liveInventory.some(v => String(v.id) === '202')", 10),
              f"ids={page.evaluate('liveInventory.map(v => v.id)')} complete={page.evaluate('liveComplete')}")
        check("resume refetch hit the network exactly once",
              len(Handler.hits) == boot_hits + 1, f"hits {boot_hits}→{len(Handler.hits)}")
        # immediate second resume: throttled, no extra fetch
        page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
        time.sleep(2)
        check("second resume right after is throttled",
              len(Handler.hits) == boot_hits + 1, f"hits {len(Handler.hits)}")
        ctx.close()

        # ── 2. warm alert entry: stale copy lacks the car; openFromAlert
        #      refetches fresh and lands on the card ───────────────────────────
        Handler.inventory = payload(iso_ago(180), [vehicle(101)])
        Handler.hits = []
        ctx, page = new_page(browser)
        page.goto(WEB + "/")
        wait_for(page, "typeof liveLoaded !== 'undefined' && liveLoaded")
        boot_hits = len(Handler.hits)
        check("alerted car absent from the stale copy",
              page.evaluate("!liveInventory.some(v => String(v.id) === '777')"))
        # scan commits; push fires; user taps it
        Handler.inventory = payload(iso_ago(1), [vehicle(101), vehicle(777)])
        page.evaluate("openFromAlert('777')")
        check("alert entry refetches fresh inventory",
              wait_for(page, "liveInventory.some(v => String(v.id) === '777')"),
              f"hits {boot_hits}→{len(Handler.hits)}")
        check("alert entry hit the network", len(Handler.hits) > boot_hits)
        check("hash normalized to the #car= focus form",
              page.evaluate("location.hash") == "#car=777", page.evaluate("location.hash"))
        check("focused view shows exactly the alerted car",
              wait_for(page, "document.querySelectorAll('#live-grid .car-card').length === 1"
                             " && !!document.querySelector('#live-grid .car-card[data-eid=\"777\"]')"))
        ctx.close()

        # ── 3. cold alert entry: launch on #alert=<id> ───────────────────────
        Handler.inventory = payload(iso_ago(1), [vehicle(101), vehicle(777)])
        Handler.hits = []
        ctx, page = new_page(browser)
        page.goto(WEB + "/#alert=777")
        check("cold #alert= launch loads inventory",
              wait_for(page, "typeof liveLoaded !== 'undefined' && liveLoaded"))
        check("cold launch normalized hash to #car=",
              page.evaluate("location.hash") == "#car=777", page.evaluate("location.hash"))
        check("cold launch lands on the alerted car's card",
              wait_for(page, "!!document.querySelector('#live-grid .car-card[data-eid=\"777\"]')"))
        check("cold launch fetched from the network", len(Handler.hits) >= 1)
        ctx.close()

        browser.close()
    server.shutdown()

    print(f"\n════ RESULT: {len(passed)} passed, {len(failed)} failed ════")
    if failed:
        for f in failed:
            print("  FAILED:", f)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
