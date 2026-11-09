#!/usr/bin/env python3
"""1A Auto adapter (offline). Run:
    python3 scraper/oem_fitment/aftermarket/tests/test_oneaauto.py

Fixtures: real pages retrieved 2026-11-09, trimmed to the parsed blocks (verbatim).
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent))
import oneaauto as a  # noqa: E402

fails = []


def check(name, ok):
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        fails.append(name)


a._SCORES = ({"honda": 100.0, "acura": 10.0}, {("honda", "crv"): 50.0, ("honda", "civic"): 80.0})
FX = HERE / "fixtures"
B = a.BASE
URL = B + "/2016-22-honda-pilot-front-passenger-side-strut-and-spring-assembly-trq-sca27339/i/1asts01815"
r = a.parse_product(URL, (FX / "oneaauto_product_1asts01815.html").read_text(), "2026-11-09T20:30:00Z", "strut")

check("sku / house brand / brand pn", r["aftermarket_pn"] == "1ASTS01815" and r["house_brand"] == "TRQ"
      and r["house_brand_pn"] == "SCA27339")
check("label is 1A Auto", r["aftermarket_brand"] == "1A Auto")
check("title", r["title"] == "2016-22 Honda Pilot Front Passenger Side Strut & Spring Assembly TRQ SCA27339")
check("one fitment row, unclosed year cell parsed", len(r["applications"]) == 1 and r["applications"][0]["years"] == [2016, 2022]
      and r["applications"][0]["make"] == "Honda" and r["applications"][0]["model"] == "Pilot")
check("description kept verbatim for curation, no engine/drive inferred",
      r["applications"][0]["description"].startswith("Honda Pilot Front Passenger Side Strut")
      and r["applications"][0]["engine"] == "" and r["applications"][0]["notes"] == "")
check("interchange numbers", r["interchange_numbers"] == [
    {"brand": "Unity Automotive", "pn": "13432"}, {"brand": "FCS", "pn": "2337077R"}, {"brand": "PRT", "pn": "920574"}])
check("no OE numbers claimed", r["oe_numbers"] == [] and r["oe_scope"] == "none")
check("no flags on a clean page", r["flags"] == [])
P = (FX / "oneaauto_product_1asts01815.html").read_text()
check("missing fitment table -> flag", "no_fitment_table" in a.parse_product(URL, P.replace("fitTable", "x"), "", "strut")["flags"])
check("missing structured data -> flag", "no_structured_data" in a.parse_product(URL, P.replace('id="sc"', 'id="q"'), "", "strut")["flags"])
row = P[P.find('<tr class="sortable_row'):P.find("</tr>", P.find('<tr class="sortable_row')) + 5]
check("duplicate rows counted", a.parse_product(URL, P.replace(row, row + row), "", "strut")["duplicate_rows"] == 1)
check("slug not of the category -> flag", "slug_not_category" in a.parse_product(URL, P, "", "wiper-motor")["flags"])

# listings
c = a.parse_listing(B + "/shocks-and-struts/c/64", (FX / "oneaauto_category_64.html").read_text(), "strut")
check("category -> make pages", B + "/honda-shocks-and-struts/ma-c/17-64" in c["children"] and not c["products"])
m = a.parse_listing(B + "/honda-shocks-and-struts/ma-c/17-64", (FX / "oneaauto_make_honda_64.html").read_text(), "strut")
check("make -> model pages", B + "/honda-cr-v-shocks-and-struts/mo-c/373-64" in m["children"])
mo = a.parse_listing(B + "/honda-cr-v-shocks-and-struts/mo-c/373-64", (FX / "oneaauto_model_crv_64.html").read_text(), "strut")
check("model page: single struts only (sets, kits, mounts skipped)",
      mo["products"] == [B + "/honda-cr-v-front-passenger-side-strut-and-spring-assembly-trq-sca36376/i/1asts02362"])
check("model page: next page", mo["next"] == B + "/honda-cr-v-shocks-and-struts/mo-c/373-64?page=2")
check("category inferred from url", a.category_of(B + "/honda-cr-v-shocks-and-struts/mo-c/373-64?page=2") == "strut"
      and a.category_of(B + "/windshield-wiper-motors/c/24") == "wiper-motor")
check("no search/sort/pageSize URLs built", not any(x in u for u in c["children"] + m["children"] + mo["products"]
                                                     for x in ("/search", "sort=", "pageSize=")))
check("scores: make pages above models; models by lot count",
      a.score(B + "/honda-shocks-and-struts/ma-c/17-64") > a.score(B + "/honda-civic-shocks-and-struts/mo-c/375-64")
      > a.score(B + "/honda-cr-v-shocks-and-struts/mo-c/373-64") > 0)
check("every category root has a unique id", len({v["root"].rsplit("/", 1)[1] for v in a.CATEGORIES.values()}) == len(a.CATEGORIES))

print(f"{'FAILED ' + str(len(fails)) if fails else 'ALL PASS'}")
sys.exit(1 if fails else 0)
