#!/usr/bin/env python3
"""Intermountain Auto iPull (Idaho Falls ID): the CRUSH static-table reader on
this yard's page, its price list, registration, name and pin.
Fixtures: scraper/fixtures/ifipull/ (real markup, a few rows, read 2026-11-17).
Run:  python3 scraper/test_ifipull.py   (offline: every request is served from
the fixtures and any other address fails the test)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures" / "ifipull"
fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        fails.append(name)


class FakeResponse:
    def __init__(self, text, status=200):
        self.text, self.status_code, self.content = text, status, text.encode()

    def raise_for_status(self):
        if self.status_code >= 400:
            raise js.requests.HTTPError(f"HTTP {self.status_code}")


calls = []
PAGES = {
    "https://ifipull.com/inventory/": (FIX / "inventory.html").read_text(encoding="utf-8"),
    "https://ifipull.com/pricelist/": (FIX / "pricelist.html").read_text(encoding="utf-8"),
}
status = {"code": 200}


def fake_get(url, headers=None, timeout=None, **kw):
    calls.append((url, dict(headers or {})))
    if url not in PAGES:
        raise AssertionError(f"unexpected request to {url}")
    return FakeResponse(PAGES[url], status["code"])


def refuse(*a, **k):
    raise AssertionError(f"unexpected request {a[:1]}")


real = (js.requests.get, js.requests.post, js._indep_cache_raw)
js.requests.get, js.requests.post = fake_get, refuse
js._indep_cache_raw = lambda *a, **k: None
try:
    site = js.CRUSH_TABLE_SITES["ifipull"]
    rows = js.fetch_ifipull_inventory()
    check("one request, to the yard's inventory page only",
          [c[0] for c in calls] == ["https://ifipull.com/inventory/"], [c[0] for c in calls])
    ua = calls[0][1].get("User-Agent", "")
    check("the reader sends the scanner's own name",
          ua == js.YARDSCOUT_UA and ua.startswith("YardScout/") and "Mozilla" not in ua, ua)
    check("no curl_cffi / snapshot fallbacks configured",
          not site.get("cffi_fallback") and not site.get("snapshot") and "headers" not in site, site)
    check("12 fixture rows -> 12 cars", len(rows) == 12, len(rows))
    first = rows[0]
    check("first row: id from the stock number", first["id"] == "ifipull-stk015489", first["id"])
    check("first row: year / make / model",
          (first["year"], first["make"], first["model"]) == (2008, "Chevrolet", "Express"),
          (first["year"], first["make"], first["model"]))
    check("first row: VIN, row, colour",
          (first["vin"], first["row"], first["_color"]) == ("1GBJG31K581198313", "53", "Green"),
          (first["vin"], first["row"], first["_color"]))
    check("arrival date MM/DD/YY -> ISO", first["dateAdded"] == "2026-03-30", first["dateAdded"])
    check("newest arrival in the fixture is 2026-11-16",
          max(r["dateAdded"] for r in rows) == "2026-11-16", max(r["dateAdded"] for r in rows))
    check("every car has a 17-character VIN and a unique id",
          all(len(r["vin"]) == 17 for r in rows) and len({r["id"] for r in rows}) == 12)
    check("every car carries the yard and source",
          all(r["_location"] == "Intermountain Auto iPull - Idaho Falls" and r["_state"] == "ID"
              and r["_city"] == "Idaho Falls" and r["_source"] == "ifipull" for r in rows))
    check("no photo is invented (the page has none)", all("_photo" not in r for r in rows))

    # The name must not fall into the app's "^ipull" site-link rule, which
    # points at iPull-uPull (California), a different company.
    name = site["yard"]["name"]
    check("display name does not start with 'ipull'", not name.lower().startswith("ipull"), name)
    check("pin is the Census match for 3015 N 15th E, Idaho Falls",
          abs(site["yard"]["lat"] - 43.5230) < 0.002 and abs(site["yard"]["lng"] + 112.0038) < 0.002,
          site["yard"])
    check("registered next to the other independent readers",
          any(fn is js.fetch_ifipull_inventory for _l, fn in js.INDEPENDENT_FETCHERS))
    check("zero-vehicle alarm knows the source", "ifipull" in js.INDEPENDENT_EXPECTED_SOURCES)

    # A refusal is a refusal: no cars, no second attempt, no other route.
    calls.clear()
    status["code"] = 500
    check("HTTP 500 (what the host answered on 2026-10-28) -> no cars",
          js.fetch_ifipull_inventory() == [])
    check("and exactly one request was made", len(calls) == 1, len(calls))
    status["code"] = 200

    # Price list.
    parts = js._ifipull_parse_pricing_rows(PAGES["https://ifipull.com/pricelist/"])
    by = {p["description"]: p for p in parts}
    check("price list: car HOOD price and core",
          by.get("HOOD") == {"description": "HOOD", "price": "45.00", "corePrice": "8.00",
                             "totalPrice": "53.00"}, by.get("HOOD"))
    check("price list: ALTERNATOR 22.00 + 8.00 core",
          by.get("ALTERNATOR", {}).get("totalPrice") == "30.00", by.get("ALTERNATOR"))
    check("price list: the ATV/MOWER 'STEERING WHEEL' does not replace the car one",
          by.get("STEERING WHEEL", {}).get("price") == "20.00", by.get("STEERING WHEEL"))
    check("price list: drinks and the carry-out programme are not parts",
          "JARRITOS" not in by and "ALL YOU CAN CARRY" not in by and "IC ALTERNATOR" not in by,
          sorted(by))
    check("price list: one row per name", len(parts) == len(by))
    check("price list: a page without the table gives nothing", js._ifipull_parse_pricing_rows("<html></html>") == [])
    check("price list is in the refresh set (sends the scanner's own name)",
          "YARDSCOUT_HEADERS" in __import__("inspect").getsource(js.refresh_ifipull_pricing_file))
finally:
    js.requests.get, js.requests.post, js._indep_cache_raw = real

print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILURES"))
sys.exit(1 if fails else 0)
