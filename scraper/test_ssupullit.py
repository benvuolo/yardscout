#!/usr/bin/env python3
"""S&S U-Pull-It (Lebanon MO) on the CRUSH MVC reader: make list from the
yard's own form, one POST per make, the scanner's own name on every request,
row-set dates, ids, price list with the extra PRICE GROUP column.
Fixtures: scraper/fixtures/ssupullit/ (real markup, a few rows, read 2026-11-17).
Run:  python3 scraper/test_ssupullit.py   (offline: every request is served
from the fixtures and any other address fails the test)"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures" / "ssupullit"
fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        fails.append(name)


def fx(name):
    return (FIX / name).read_text(encoding="utf-8")


class FakeResponse:
    def __init__(self, text, status=200):
        self.text, self.status_code = text, status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise js.requests.HTTPError(f"HTTP {self.status_code}")


BASE = "https://www.ssupullit.com"
FORM = fx("inventory_form.html")
MAKE_PAGES = {"ACURA": fx("make_ACURA.html"), "TOYOTA": fx("make_TOYOTA.html")}
# A make with no fixture answers the same page with the data rows removed
# (made here from the ACURA fixture; the only synthetic page in this test).
EMPTY = re.sub(r"(?s)<tr>\s*<td>.*?</tr>", "", MAKE_PAGES["ACURA"], count=6)
calls = []
sleeps = []


def fake_get(url, headers=None, timeout=None, **kw):
    calls.append(("GET", url, dict(headers or {}), None))
    if url != BASE + "/Home/Inventory":
        raise AssertionError(f"unexpected GET {url}")
    return FakeResponse(FORM)


def fake_post(url, files=None, data=None, headers=None, timeout=None, **kw):
    make = (files or {}).get("VehicleMake", (None, None))[1]
    calls.append(("POST", url, dict(headers or {}), {k: v[1] for k, v in (files or {}).items()}))
    if url != BASE + "/Home/Inventory" or data is not None:
        raise AssertionError(f"unexpected POST {url} {data}")
    return FakeResponse(MAKE_PAGES.get(make, EMPTY))


real = (js.requests.get, js.requests.post, js.time.sleep)
js.requests.get, js.requests.post = fake_get, fake_post
js.time.sleep = lambda s=0, *a: sleeps.append(s)
try:
    site = js.CRUSH_MVC_SITES["ssupullit"]
    rows = js.fetch_ssupullit_inventory()
    posts = [c for c in calls if c[0] == "POST"]
    check("make list comes from the yard's own form (35 makes, one GET)",
          len([c for c in calls if c[0] == "GET"]) == 1 and len(posts) == 35, (len(calls), len(posts)))
    check("one POST per make, model left empty, no yard id (single yard)",
          all(c[3] == {"VehicleMake": c[3]["VehicleMake"], "VehicleModel": ""} for c in posts)
          and len({c[3]["VehicleMake"] for c in posts}) == 35, posts[:1])
    uas = {c[2].get("User-Agent") for c in calls}
    check("every request sends the scanner's own name",
          uas == {js.YARDSCOUT_UA} and js.YARDSCOUT_UA.startswith("YardScout/"), uas)
    check("at least 1 s between requests on this host",
          js.CRUSH_MVC_DELAY_SEC >= 1.0 and len(sleeps) == 35 and min(sleeps) >= 1.0,
          (js.CRUSH_MVC_DELAY_SEC, len(sleeps)))
    check("only the yard's host is contacted", all(c[1].startswith(BASE + "/") for c in calls))

    check("6 Acura + 10 Toyota fixture rows -> 16 cars", len(rows) == 16, len(rows))
    first = rows[0]
    check("first row: 2004 Acura TL, row 100, grey",
          (first["year"], first["make"], first["model"], first["row"], first["_color"])
          == (2004, "Acura", "TL", "100", "Gray"), first)
    check("the yard's row-set date MM/DD/YYYY -> ISO", first["dateAdded"] == "2025-08-13", first["dateAdded"])
    check("no VIN is invented (the site shows none)", all(r["vin"] == "" for r in rows))
    check("no photo is invented (the site shows none)", all("_photo" not in r for r in rows))
    check("ids are unique and carry source and yard",
          len({r["id"] for r in rows}) == 16 and all(r["id"].startswith("ssupullit-lebanon-") for r in rows))
    check("every car carries the yard",
          all(r["_location"] == "S&S U-Pull-It - Lebanon" and r["_state"] == "MO"
              and r["_city"] == "Lebanon" and r["_source"] == "ssupullit" for r in rows))
    calls.clear()
    again = js.fetch_ssupullit_inventory()
    check("ids are stable from one scan to the next", [r["id"] for r in again] == [r["id"] for r in rows])

    y = site["yards"][0]
    check("pin is the Census match for 22395 Rte 66, Lebanon MO",
          abs(y["lat"] - 37.6967) < 0.002 and abs(y["lng"] + 92.6280) < 0.002, y)
    check("registered next to the other independent readers",
          any(fn is js.fetch_ssupullit_inventory for _l, fn in js.INDEPENDENT_FETCHERS))
    check("zero-vehicle alarm knows the source", "ssupullit" in js.INDEPENDENT_EXPECTED_SOURCES)

    # The older tenants of the same reader are not changed by this addition.
    check("tenants added before 2026-11-17 keep the headers they sent",
          all(js._crush_mvc_headers(s) is js.HEADERS
              for src, s in js.CRUSH_MVC_SITES.items() if src != "ssupullit"))
    check("this tenant is read under the scanner's own name",
          js._crush_mvc_headers(site) is js.YARDSCOUT_HEADERS)

    # Price list: PART DESCRIPTION, PRICE GROUP, PRICE, BASIS, CORE CHARGE.
    prices_page = fx("prices.html")
    check("price list columns read from the header (PRICE GROUP skipped)",
          js._crush_mvc_price_columns(prices_page) == (0, 2, 4), js._crush_mvc_price_columns(prices_page))
    parts = js._crush_mvc_parse_prices(prices_page)
    check("ALTERNATOR 24.00 + 8.00 core",
          parts.get("ALTERNATOR") == {"description": "ALTERNATOR", "price": "24.00",
                                      "corePrice": "8.00", "totalPrice": "32.00"},
          parts.get("ALTERNATOR"))
    check("8 fixture rows -> 8 parts", len(parts) == 8, sorted(parts))
    check("the usual 4-column list still reads as before",
          js._crush_mvc_price_columns("<th>PART DESCRIPTION</th><th>PRICE</th><th>BASIS</th><th>CORE</th>") == (0, 1, 3)
          and js._crush_mvc_price_columns("<table><tr><td>x</td></tr></table>") == (0, 1, 3))
    four = ("<table><tr><th>PART DESCRIPTION</th><th>PRICE</th><th>BASIS</th><th>CORE</th></tr>"
            "<tr><td>AXLE</td><td>$30.00</td><td>Each</td><td>$5.00</td></tr></table>")
    check("4-column row parses to the same entry as before",
          js._crush_mvc_parse_prices(four) == {"AXLE": {"description": "AXLE", "price": "30.00",
                                                        "corePrice": "5.00", "totalPrice": "35.00"}})
    check("price list is published for this yard", site.get("prices_path") == "/Home/PartPrices")
finally:
    js.requests.get, js.requests.post, js.time.sleep = real

print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILURES"))
sys.exit(1 if fails else 0)
