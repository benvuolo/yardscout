#!/usr/bin/env python3
"""GSP North America adapter (offline). Run:
    python3 scraper/oem_fitment/aftermarket/tests/test_gspnorthamerica.py

Fixtures are real pages retrieved 2026-11-09, trimmed to the parsed blocks
(verbatim): products/ncv36167xd, the sitemap index, and the head of
sitemap_products_2 (three real entries). One CV entry is added to that urlset
in this test, built from the real ncv36167xd title and URL.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent))
import gspnorthamerica as g  # noqa: E402

fails = []


def check(name, ok):
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        fails.append(name)


g._MAKE_SCORES = {"honda": 100.0, "volvo": 5.0}  # offline: no worklist read
FX = HERE / "fixtures"
PAGE = (FX / "gsp_product_ncv36167xd.html").read_text()
URL = "https://gspnorthamerica.com/products/ncv36167xd"
r = g.parse_product(URL, PAGE, "2026-11-09T20:05:00Z", "cv-axle")

check("part number", r["aftermarket_pn"] == "NCV36167XD")
check("brand label is GSP", r["aftermarket_brand"] == "GSP")
check("title verbatim without site suffix", r["title"] == "17-22 Honda CR-V (1.5, 2.4) CV Axle Assembly - Front Left")
check("title engines verbatim", r["title_engines"] == ["1.5", "2.4"])
check("title position", r["title_position"] == "Front Left")
check("four printed rows", r["application_rows_printed"] == 4 and len(r["applications"]) == 4)
a0 = r["applications"][0]
check("first row", a0["years"] == [2017, 2018] and a0["make"] == "Honda" and a0["model"] == "CR-V"
      and a0["submodel"] == "" and a0["position"] == "Front Left")
check("no engine/drive/trans inferred on rows", all(a["engine"] == "" and a["notes"] == "" for a in r["applications"]))
check("duplicate 2019 row counted and flagged", r["duplicate_rows"] == 1 and "duplicate_rows" in r["flags"])
check("spans keep position and merge 2017-2022", r["application_spans"] == [
    {"years": [2017, 2022], "make": "Honda", "model": "CR-V", "engine": "", "submodel": "", "position": "Front Left"}])
check("specs parsed", r["specs"].get("Axle Nut Thread Size") == "M26×1.5" and r["specs"].get("ABS Tone Ring Included") == "No")
check("spline/length specs present", any("Spline" in k for k in r["specs"]) and any("Length" in k for k in r["specs"]))
check("no OE numbers claimed", r["oe_numbers"] == [] and r["oe_scope"] == "none")
check("no description text stored", "description" not in r and "body_html" not in r)
check("category matches title", "title_not_category" not in r["flags"])

# failure shapes flag, never guess
nt = g.parse_product(URL, PAGE.replace("product-applications__table", "x"), "", "cv-axle")
check("missing application table -> flag, no rows", nt["applications"] == [] and "no_application_table" in nt["flags"])
hc = g.parse_product(URL, PAGE.replace("<th>Submodel</th>", "<th>Trim</th>"), "", "cv-axle")
check("changed header -> flag, no rows", hc["applications"] == [] and "application_header_changed" in hc["flags"])
np_ = g.parse_product(URL, PAGE.replace("<strong>Part Number:</strong>", "<strong>PN</strong>"), "", "cv-axle")
check("missing part number -> flag", "no_part_number" in np_["flags"])
st = g.parse_product(URL, PAGE.replace("CV Axle Assembly", "Strut Assembly"), "", "cv-axle")
check("title not the category -> flag", "title_not_category" in st["flags"])
ep = g.parse_product(URL, PAGE.replace("Front Left</td>", "-</td>", 1), "", "cv-axle")
check("missing position -> flag", "position_missing" in ep["flags"])

# sitemaps
idx = g.parse_listing(g.BASE + "/sitemap.xml", (FX / "gsp_sitemap_index.xml").read_text())
check("index -> product sitemaps only", idx["children"] and all("/sitemap_products_" in u for u in idx["children"])
      and not idx["products"])
check("index skips non-product sitemaps", not any("agentic" in u or "pages" in u for u in idx["children"]))
us = (FX / "gsp_sitemap_products_2_head.xml").read_text()
cv = ("<url><loc>https://gspnorthamerica.com/products/ncv36167xd</loc><image:image><image:title>"
      "17-22 Honda CR-V (1.5, 2.4) CV Axle Assembly  - Front Left</image:title></image:image></url>\n</urlset>")
li = g.parse_listing(g.BASE + "/sitemap_products_2.xml", us.replace("</urlset>", cv))
check("urlset: only CV axle titles picked", li["products"] == [URL])
check("urlset: ball joints skipped", g.parse_listing(g.BASE + "/sitemap_products_2.xml", us)["products"] == [])
try:
    g.parse_listing(g.BASE + "/x.xml", "<rss/>")
    check("non-sitemap XML raises", False)
except ValueError:
    check("non-sitemap XML raises", True)
check("make ordering uses lot counts", g.title_score("17-22 Honda CR-V") > g.title_score("Volvo Ball Joint"))

print(f"{'FAILED ' + str(len(fails)) if fails else 'ALL PASS'}")
sys.exit(1 if fails else 0)
