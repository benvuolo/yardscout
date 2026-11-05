#!/usr/bin/env python3
"""Offline tests for aftermarket/dbelectrical.py and common.py.

    python3 scraper/oem_fitment/aftermarket/tests/test_dbelectrical.py

Part 1 runs everywhere: committed fixtures (trimmed copies of real pages,
retrieved 2026-11-05) and robots/brand-role logic. Part 2 reads full pages
from the local fetch.py cache only and SKIPs when they are absent (CI has no
cache). No test touches the network.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common  # noqa: E402
import dbelectrical as db  # noqa: E402

FIX = HERE / "fixtures"
fails = 0
checks = 0


def ok(cond: bool, msg: str) -> None:
    global fails, checks
    checks += 1
    if not cond:
        fails += 1
        print("FAIL", msg)


# ---------------------------------------------------------------- fixtures ---
PURL = "https://www.dbelectrical.com/products/new-alternator-3-0-3-0l-ford-escape-mazda-tribute-01-03-04-2001-2002-2003-2004.html"
r = db.parse_product(PURL, (FIX / "dbelectrical_product_400-14103.html").read_text(), "2026-11-05T00:58:00Z", "alternator")
ok(r["aftermarket_pn"] == "400-14103", f"pn {r['aftermarket_pn']}")
ok(r["title"] == "Alternator 3.0L Ford Escape Mazda Tribute 2001-2004", f"title {r['title']}")
ok(r["flags"] == [], f"flags {r['flags']}")
ok(r["specs"]["Unit Type"] == "Alternator" and r["specs"]["Amperage"] == "110", "specs")
ok(r["fits_text"] == "FORD ESCAPE 3.0L 2001-04 ,MAZDA TRIBUTE 3.0L 2001-04 ,6-GROOVE PULLEY 59mm OD ,BUT OE IS 59mm", r["fits_text"])
ok(len(r["applications"]) == 13, f"apps {len(r['applications'])}")
a0 = r["applications"][0]
ok(a0 == {"years": [2001, 2001], "make": "Ford", "type": "Auto and Light Truck", "model": "ESCAPE",
          "engine": "181cu in 3.0L V6", "notes": "", "raw": "Ford | Auto and Light Truck | ESCAPE | 2001 | 181cu in 3.0L V6"}, str(a0))
ok(r["applications"][-1]["raw"] == "Mazda | Truck | Tribute | 2004 | 3000cc 3.0L V6", r["applications"][-1]["raw"])
ok(r["multi_make"] is True, "multi_make")
spans = {(s["make"], s["model"], s["engine"]): s["years"] for s in r["application_spans"]}
ok(spans[("Mazda", "TRIBUTE", "3.0L")] == [2001, 2004], str(spans))
ok(spans[("Mazda", "Tribute", "3000cc 3.0L V6")] == [2004, 2004], "Truck-source row stays its own span")
oe = [(o["brand"], o["pn"]) for o in r["oe_numbers"]]
ok(("FORD", "1L8U-10300-CD") in oe and ("MAZDA", "AJ03-18-300A") in oe and ("MAZDA", "AJ03-18-300B") in oe, str(oe))
ok(len(oe) == 13, f"oe count {len(oe)}")
ok(r["oe_scope"] == "product", "oe_scope")
ok([(o["brand"], o["pn"]) for o in r["oe_service_numbers"]] == [("MOTORCRAFT", "GL-463"), ("MOTORCRAFT", "GL-615")], "motorcraft is a service brand")
ok({o["brand"] for o in r["oe_supplier_numbers"]} == {"VISTEON"}, str(r["oe_supplier_numbers"]))
ok(r["lester"] == ["8259"], str(r["lester"]))
ok("LESTER | 8259" in r["evidence_lines"] and "MAZDA | AJ03-18-300A, AJ03-18-300B" in r["evidence_lines"], "evidence replaces rows")
ok("MAKE | TYPE | MODEL | YEAR | ENGINE" in r["evidence_lines"], "evidence header")

# wrong category is flagged, never silently accepted
r2 = db.parse_product(PURL, (FIX / "dbelectrical_product_400-14103.html").read_text(), "x", "starter")
ok(any(f.startswith("unit_type_not_starter") for f in r2["flags"]), str(r2["flags"]))

li = db.parse_listing("https://www.dbelectrical.com/alternators/automotive/mazda/tribute/",
                      (FIX / "dbelectrical_listing_mazda_tribute.html").read_text())
ok(len(li["products"]) == 7 and all(u.startswith("https://www.dbelectrical.com/products/") for u in li["products"]), str(li["products"]))
ok(PURL in li["products"], "tribute listing has 400-14103")
ok(li["next"] is None and li["children"] == [], str(li))
pg = db.parse_listing("https://www.dbelectrical.com/alternators/automotive/ford/f-series/",
                      (FIX / "dbelectrical_listing_ford_fseries_pagination.html").read_text())
ok(pg["next"] == "https://www.dbelectrical.com/alternators/automotive/ford/f-series/?page=2", str(pg["next"]))

# robots: RFC 9309 merge of every '*' group (fetch.py's robotparser keeps only the first)
common._rules.cache_clear()
_body = """User-agent: *
Content-Signal: search=yes
Allow: /

User-agent: GPTBot
Disallow: /

User-agent: *
Disallow: /search.php
Disallow: /*?_bc_fsnf=1*
"""
_orig = common._rules
common._rules = lambda netloc: [  # type: ignore
    ("/", True), ("/search.php", False), ("/*?_bc_fsnf=1*", False)]
ok(not common.robots_allows("https://www.dbelectrical.com/search.php?search_query=x"), "search.php refused")
ok(not common.robots_allows("https://www.dbelectrical.com/alternators/?_bc_fsnf=1&brand=2"), "facet URL refused")
ok(common.robots_allows("https://www.dbelectrical.com/alternators/automotive/ford/f-series/?page=2"), "pagination allowed")
common._rules = _orig
# the parser itself on that body
import tempfile  # noqa: E402
with tempfile.TemporaryDirectory() as td:
    old_cache = common.fetch.CACHE
    common.fetch.CACHE = Path(td)
    (Path(td) / "example.test").mkdir()
    (Path(td) / "example.test" / "robots.txt").write_text(_body)
    common._rules.cache_clear()
    rules = common._rules("example.test")
    common.fetch.CACHE = old_cache
    common._rules.cache_clear()
ok(("/", True) in rules and ("/search.php", False) in rules and ("/*?_bc_fsnf=1*", False) in rules
   and all(p != "/" or allow for p, allow in rules), str(rules))

# brand roles: Mitsubishi split by documented number shapes only
cls = common.classify_replaces([{"brand": "MITSUBISHI", "numbers": ["A3TG0491", "A002TG0491", "MD192059", "1800A007", "X123"]}])
ok([x["pn"] for x in cls["oe_supplier_numbers"]] == ["A3TG0491", "A002TG0491"], str(cls))
ok([x["pn"] for x in cls["oe_numbers"]] == ["MD192059", "1800A007"], str(cls))
ok([x["pn"] for x in cls["ambiguous_numbers"]] == ["X123"], str(cls))

# ------------------------------------------------- full pages from cache ---
CACHED = [PURL,
          "https://www.dbelectrical.com/products/alternator-for-ford-escape-focus-fusion-transit-connect.html"]
for u in CACHED:
    if not common.fetch.cache_path(u).exists():
        print(f"SKIP (not in local cache): {u}")
        continue
    d = common.fetch.get(u)
    rec = db.parse_product(u, d["html"], d["retrieved"], "alternator")
    ok(rec["aftermarket_pn"] and rec["applications"] and rec["replaces"], f"cached page parses: {u}")
    ok(not [f for f in rec["flags"] if f.startswith("unparsed")], f"no unparsed rows: {rec['flags']}")
    if u == PURL:
        ok(rec["applications"] == r["applications"] and rec["replaces"] == r["replaces"], "fixture == full page")
make_url = "https://www.dbelectrical.com/alternators/automotive/mazda/"
if common.fetch.cache_path(make_url).exists():
    li = db.parse_listing(make_url, common.fetch.get(make_url)["html"])
    ok(make_url + "tribute/" in li["children"] and make_url + "cx-7/" in li["children"], "make page children")
    ok(all(c.startswith(make_url) and c.count("/") == make_url.count("/") + 1 for c in li["children"]), "children one level down")
else:
    print(f"SKIP (not in local cache): {make_url}")

print(f"{checks - fails}/{checks} checks passed")
sys.exit(1 if fails else 0)
