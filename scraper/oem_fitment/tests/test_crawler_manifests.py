#!/usr/bin/env python3
"""Offline tests for the crawler requirements in CURATION_SPEC.md §3.2, at the
template level (crawl.py end to end: test_crawl_manifests.py):

  R1  list_manifest: every row of every list page, matched / excluded_by,
      notes verbatim, section, replace; matched == what parts_on_page returns
  R2  year_manifest: status, title, every sub slug; PartsGiant: every offered
      variant and option catalog, read or not
  R4  chain_links: only numbers the product page links
  R5  (a) qualifier phrase removal, (b) reman drop only next to a current new
      number, (c) Toyota -84 reman
  no manifest makes a request (only cache re-reads)
  record output on real fixture pages equals the pre-change snapshot
  (golden_records_v0.json) except the listed R5 changes

Fixture pages: tests/fixtures/crawler/real_pages.json (trimmed real pages,
fetched through fetch.py) and tests/_synthetic_pages.py.
Run: python3 scraper/oem_fitment/tests/test_crawler_manifests.py
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _crawler_fixtures as F  # noqa: E402
import _synthetic_pages as S  # noqa: E402

PAGES = F.Pages(F.real_pages(), S.toyota_pages(), S.gm_pages(), S.ford_split_pages(), S.volvo_pages(), S.mb_pages())
F.install(PAGES)

from sites import _partsgiant as PG  # noqa: E402
from sites import _qualifier, fordpartsgiant, gmpartsgiant, toyotapartsnow  # noqa: E402
from sites._simplepart import store as sp_store  # noqa: E402

fails: list[str] = []
n = 0


def check(name: str, ok, detail="") -> None:
    global n
    n += 1
    if not ok:
        fails.append(name)
        print(f"FAIL  {name} — {detail}")


def rows_by_pn(man: dict) -> dict:
    out: dict = {}
    for r in man["rows"]:
        out.setdefault(r["pn"], []).append(r)
    return out


def no_gets(fn, *args):
    """Run fn and assert it read pages only through the cache (no get)."""
    before = len(PAGES.gets())
    out = fn(*args)
    check(f"no request from {getattr(fn, '__name__', fn)}{args[:2]}", len(PAGES.gets()) == before,
          PAGES.gets()[before:])
    return out


# ------------------------------------------------------------- R5a qualifier
q = _qualifier.strip_qualifiers
check("R5a phrase to the comma", q("Mirror Assy, Outer Rear View, W/Turn Signal Lamp").strip(" ,")
      == "Mirror Assy, Outer Rear View", q("Mirror Assy, Outer Rear View, W/Turn Signal Lamp"))
check("R5a W/O phrase", "Bulb" not in q("Lens & Body, Rear Combination Lamp, W/O Socket & Bulb"))
check("R5a stops at ;", q("Pump Assy, Fuel W/Filter & Gage; Fuel Pump").endswith("; Fuel Pump"))
check("R5a less / L/", "Cap" not in q("Radiator Assy, L/Cap") and "Pulley" not in q("Pump Assy, Less Pulley"))
check("R5a whole words only", q("Wireless Charger") == "Wireless Charger" and q("Lessor Bracket") == "Lessor Bracket"
      and q("Inclinometer") == "Inclinometer")
check("R5a includes", "Gasket" not in q("Throttle Body Assy (Includes Gasket)"), q("Throttle Body Assy (Includes Gasket)"))
ty = toyotapartsnow._T
check("R5a Toyota mirror W/Turn Signal Lamp kept",
      ty.match("side-mirrors", "Mirror Assembly", "Mirror Assy, Outer Rear View, W/Turn Signal Lamp"))
check("R5a Toyota headlamp W/Auto Leveling kept",  # EPC form; "Headlamp Unit Assy" misses the include rule
      ty.match("headlights", "Headlamp Assembly", "Unit Assy, Headlamp, W/Auto Leveling")
      and ty.excluded_by("headlights", "Headlamp Assembly", "Headlamp Unit Assy, W/Auto Leveling") == "include_miss")
check("R5a Toyota fuel suction W/Pump & Gage kept",
      ty.match("fuel-pump-module", "Fuel Pump Assembly", "Tube Assy, Fuel Suction W/Pump & Gage"))
check("R5a junk noun before the qualifier still excluded",
      ty.excluded_by("side-mirrors", "Mirror Glass", "Mirror Assy, Outer Rear View, Glass W/Heater") == "rule:glass"
      and ty.excluded_by("alternator", "Alternator", "Alternator Bracket, W/Bolt") == "global:bracket")
check("R5a include still on the full name", ty.excluded_by("starter", "Bolt", "Bolt, W/Starter") == "include_miss")
from sites import bmwpartsdeal, lexuspartsnow, subarupartsdeal  # noqa: E402
check("R5a shared by Subaru/Lexus/BMW", subarupartsdeal.QUALIFIER is lexuspartsnow.QUALIFIER is bmwpartsdeal.QUALIFIER
      is _qualifier.QUALIFIER)
check("R5a Lexus mirror W/Turn Signal Lamp kept",
      lexuspartsnow.PARTS["side-mirrors"]({"main": "Mirror Sub-Assy, Outer Rear View, W/Turn Signal Lamp"}, ""))
check("name_rule .why", lexuspartsnow.PARTS["side-mirrors"].why({"main": "Bulb"}, "") == "include_miss")

# ------------------------------------------------------------- SimplePart R1
L = f"{S.T}/parts-list/{S.TSTEM}"
alt = no_gets(toyotapartsnow.list_manifest, f"{L}/charging-starting/alternator", "alternator")
parts = toyotapartsnow.parts_on_page(f"{L}/charging-starting/alternator", "alternator")
by = rows_by_pn(alt)
check("R1 every row (7 diagram + 2 other)", len(alt["rows"]) == 9, len(alt["rows"]))
check("R1 sections", [r["section"] for r in alt["rows"]] == ["diagram"] * 7 + ["other"] * 2)
check("R1 matched == parts_on_page", {r["pn"] for r in alt["rows"] if r["matched"]} == {p["pn"] for p in parts},
      ({r["pn"] for r in alt["rows"] if r["matched"]}, [p["pn"] for p in parts]))
why = {pn: rs[0]["excluded_by"] for pn, rs in by.items()}
check("R1 reasons", why == {"27060-90010": None, "27060-90010-84": "reman_dropped", "27415-90010": "include_miss",
                            "12511-90010": "global:bracket", "90119-90010": "include_miss",
                            "27060-90020": "url_pn_mismatch", "27060-90030": "no_product_url",
                            "27060-90005": None, "27060-89990": "rule:kit"}, why)
check("R5c -84 is reman on the row", by["27060-90010-84"][0]["reman"] is True and by["27060-90010"][0]["reman"] is False)
check("R1 extra verbatim, structured", by["27060-90005"][0]["extra"] == [
    {"name": "Production Date", "desc": "01/2030-06/2030"}, {"name": "Replaced By", "desc": "27060-90010"}],
    by["27060-90005"][0]["extra"])
check("R1 replace and url", by["27060-90005"][0]["replace"] == "27060-90010"
      and by["27060-90005"][0]["url"] == "/oem/toyota~alternator-assy~27060-90005")
check("R1 line fields", alt["status"] == 200 and alt["catalog"] == S.TSTEM and alt["variant"] == ""
      and alt["final_url"] == f"{L}/charging-starting/alternator" and alt["retrieved"])
check("R5b a new diagram number drops its reman", [p["pn"] for p in parts] == ["27060-90010", "27060-90005"],
      [p["pn"] for p in parts])

st_parts = toyotapartsnow.parts_on_page(f"{L}/charging-starting/starter", "starter")
check("R5b remans stay next to a superseded catalog-only number",
      [(p["pn"], p["reman"]) for p in st_parts] == [("28100-90010-84", True), ("28100-90020-84", True),
                                                    ("28100-90010", False)], [(p["pn"], p["reman"]) for p in st_parts])
st = no_gets(toyotapartsnow.list_manifest, f"{L}/charging-starting/starter", "starter")
check("R5b no reman_dropped on that page", not any(r["excluded_by"] == "reman_dropped" for r in st["rows"]))

mir = toyotapartsnow.parts_on_page(f"{L}/body-hardware/outside-mirrors", "side-mirrors")
check("R5a mirror with turn signal lamp listed", [p["pn"] for p in mir] == ["87910-90010", "87940-90010"], [p["pn"] for p in mir])
check("list_notes keep the ; structure", mir[0]["list_notes"] == ["US Built, With Heated;Japan Built, With Heated"])
hl = toyotapartsnow.parts_on_page(f"{L}/headlights-lighting/headlamps", "headlights")
check("R5a headlamp with auto leveling listed", [p["pn"] for p in hl] == ["81110-90010"])

missing = toyotapartsnow.list_manifest(f"{L}/charging-starting/never-read", "alternator")
check("R1 unread page: status None, not_fetched, no request", missing["status"] is None and missing["error"] == "not_fetched"
      and missing["rows"] == [] and f"{L}/charging-starting/never-read" not in PAGES.gets())
check("R1 category without rules", toyotapartsnow.list_manifest(f"{L}/charging-starting/alternator", "no-such-cat")["error"])

# real page: every row of the 2009 Camry mirror page, and the 2007 alternator R5b case
R = "https://www.toyotapartsnow.com/parts-list"
real = F.real_pages()
for url, cat in [(f"{R}/2009-toyota-camry/body-hardware/outside-mirrors", "side-mirrors"),
                 (f"{R}/2007-toyota-camry/charging-starting/alternator", "alternator"),
                 (f"{R}/1999-toyota-camry/charging-starting/starter", "starter")]:
    man = no_gets(toyotapartsnow.list_manifest, url, cat)
    pl = sp_store(real[url]["html"])["partList"]
    n_rows = sum(len(g) for g in pl.get("partList") or []) + sum(len(g) for g in pl.get("gpgOnlyPartList") or [])
    got = toyotapartsnow.parts_on_page(url, cat)
    check(f"R1 real {url.rsplit('/', 3)[1]} {cat}: every row", len(man["rows"]) == n_rows, (len(man["rows"]), n_rows))
    check(f"R1 real {cat}: matched == parts", {r["pn"] for r in man["rows"] if r["matched"]} == {p["pn"] for p in got})
a07 = rows_by_pn(toyotapartsnow.list_manifest(f"{R}/2007-toyota-camry/charging-starting/alternator", "alternator"))
check("R5b real 2007 Camry: remans kept beside 27060-28320 (other, replaced by -84)",
      all(a07[p][0]["matched"] for p in ("27060-0H111-84", "27060-28321-84", "27060-28320"))
      and a07["27060-28320"][0]["section"] == "other" and a07["27060-28320"][0]["replace"] == "27060-28321-84")
s99 = rows_by_pn(toyotapartsnow.list_manifest(f"{R}/1999-toyota-camry/charging-starting/starter", "starter"))
check("R5c real 1999 Camry: 28100-74270-84 'Starter Assembly' is reman", s99["28100-74270-84"][0]["reman"] is True)

# ------------------------------------------------------------- SimplePart R2
yl = no_gets(toyotapartsnow.year_manifest, "Toyota", "Camry", 2030)
check("R2 one line", len(yl) == 1)
y = yl[0]
check("R2 fields", y["status"] == 200 and y["redirected"] is False and y["title"].startswith("2030 Toyota Camry")
      and y["catalog"] == S.TSTEM and y["variants"] == [""] and "error" not in y, y)
check("R2 every sub", y["subs"] == sorted(["charging-starting/alternator", "charging-starting/starter",
                                           "body-hardware/outside-mirrors", "headlights-lighting/headlamps",
                                           "engine/oil-pan"]), y["subs"])
yr = no_gets(toyotapartsnow.year_manifest, "Toyota", "Camry", 2009)[0]
check("R2 real 2009 Camry: 190 subs and title", len(yr["subs"]) == 190 and yr["title"] == "2009 Toyota Camry Parts - ToyotaPartsNow.com")
check("R2 subs = what navigation chooses from", set(u.split("/parts-list/2009-toyota-camry/")[1]
      for us in toyotapartsnow.categories_for("Toyota", "Camry", 2009, F.ALL_CATS).values() for u in us) <= set(yr["subs"]))
ny = no_gets(toyotapartsnow.year_manifest, "Toyota", "Camry", 2031)[0]
check("R2 year not fetched", ny["status"] is None and ny["error"] == "not_fetched")
PAGES.pages[f"{S.T}/catalog/2032-toyota-camry-parts"] = F.page("<html></html>", status=404)
PAGES.pages[f"{S.T}/catalog/2033-toyota-camry-parts"] = F.page(
    "<html><title>Camry</title></html>", final_url=f"{S.T}/toyota-camry-parts")
check("R2 HTTP 404 kept", toyotapartsnow.year_manifest("Toyota", "Camry", 2032)[0]["error"] == "HTTP 404")
r33 = toyotapartsnow.year_manifest("Toyota", "Camry", 2033)[0]
check("R2 redirect flagged", r33["redirected"] is True and r33["error"] == "redirected", r33)

# ------------------------------------------------------------- SimplePart R4
cl = no_gets(toyotapartsnow.chain_links, f"{S.T}/oem/toyota~starter~28100-90010-84", ["28100-90030", "28100-90010", "90119-90099"])
check("R4 product-page links only", cl == {"28100-90030": f"{S.T}/oem/toyota~starter~28100-90030",
                                           "90119-90099": f"{S.T}/oem/toyota~bolt~90119-90099"}, cl)
check("R4 nothing for an unlinked number", toyotapartsnow.chain_links(f"{S.T}/oem/toyota~alternator~27060-90010",
                                                                     ["27060-89990"]) == {})

# ------------------------------------------------------------- PartsGiant R1
sec = "starter_generator_ignition_electrical_lamps"
gen_url = f"{S.G}/parts-list/2030-chevrolet-malibu/{sec}/generator_mounting.html"
gm = no_gets(gmpartsgiant.list_manifest, gen_url, "alternator")
gparts = gmpartsgiant.parts_on_page(gen_url, "alternator")
gb = rows_by_pn(gm)
check("R1 PG every row incl. gpgOnly and Standard Parts", [(r["pn"], r["section"]) for r in gm["rows"]] == [
    ("19000001", "diagram"), ("19000003", "diagram"), ("11589999", "diagram"), ("19000009", "other"),
    ("11589280", "standard")], [(r["pn"], r["section"]) for r in gm["rows"]])
check("R1 PG reasons", {pn: rs[0]["excluded_by"] for pn, rs in gb.items()} == {
    "19000001": None, "19000003": None, "11589999": "include_miss", "19000009": "section_not_read",
    "11589280": "section_not_read"}, {pn: rs[0]["excluded_by"] for pn, rs in gb.items()})
check("R1 PG matched == parts_on_page", {r["pn"] for r in gm["rows"] if r["matched"]} == {p["pn"] for p in gparts})
check("R1 PG row fields", gb["19000001"][0]["group"] == "GENERATOR, Engine Electrical"
      and gb["19000001"][0]["remark"] == "(INCLUDES 3-5)" and gb["19000001"][0]["replace"] == "19000002"
      and gb["19000001"][0]["extra"][1] == {"name": "Replaced By", "desc": "19000002"})
check("R5b PG reman kept beside a superseded number, marked",
      [(p["pn"], p["reman"]) for p in gparts] == [("19000001", False), ("19000003", True)], [(p["pn"], p["reman"]) for p in gparts])
new_url = f"{S.G}/parts-list/2030-chevrolet-malibu-new_model/{sec}/generator_mounting.html"
nm = rows_by_pn(gmpartsgiant.list_manifest(new_url, "alternator"))
check("R5b PG reman dropped beside a current new number", nm["19000004"][0]["excluded_by"] == "reman_dropped"
      and [p["pn"] for p in gmpartsgiant.parts_on_page(new_url, "alternator")] == ["19000002"])
check("R1 PG variant from the URL", gmpartsgiant.list_manifest(new_url, "alternator")["variant"] == "new_model")
# real GM page with a Standard Parts row
lf = f"{S.G}/parts-list/2014-chevrolet-cruze/{sec}/lamps_front.html"
lm = no_gets(gmpartsgiant.list_manifest, lf, "headlights")
check("R1 real GM lamps_front: 26 rows, one standard", len(lm["rows"]) == 26 and [r["section"] for r in lm["rows"]].count("standard") == 1,
      len(lm["rows"]))
check("R1 real GM: matched == parts", {r["pn"] for r in lm["rows"] if r["matched"]} == {"95291963", "95291964"})
ff = f"{S.F}/parts-list/2001-ford-f_150--8_cyl_5_4l-4at_4r100/alternator_battery_distributor_starter/alternator.html"
fm = no_gets(fordpartsgiant.list_manifest, ff, "alternator")
check("R1 Ford trim from the URL", fm["variant"] == "" and fm["trim"] == "8_cyl_5_4l-4at_4r100")
check("R1 Ford .why reasons", {r["pn"]: r["excluded_by"] for r in fm["rows"]}["F65Z-10344-AA"] == "include_miss")
check("R1 Ford reman rows marked and kept (all reman)", all(r["reman"] and r["matched"] for r in fm["rows"]
                                                            if "10346" in r["pn"]))
for p in fordpartsgiant.parts_on_page(ff, "alternator"):
    check(f"PG parts carry reman {p['pn']}", p["reman"] is True)

# ------------------------------------------------------------- PartsGiant R2
gy = no_gets(gmpartsgiant.year_manifest, "Chevrolet", "Malibu", 2030)
check("R2 PG one line per catalog read", [(x["variant"], x["trim"]) for x in gy] == [("", None), ("new_model", None)], gy)
check("R2 PG every offered variant", gy[0]["variants"] == ["new_model", "", "eco", "limited_carryover_model",
                                                         "classic_carryover_model", "hybrid"], gy[0]["variants"])
check("R2 PG variants read (MAX_CATALOGS=2)", gy[0]["variants_read"] == ["", "new_model"]
      and [o["read"] for o in gy[0]["offered"]] == [True, True, False, False, False, False])
check("R2 PG subs", gy[0]["subs"] == [f"{sec}/generator_mounting", f"{sec}/lamps_front"] and gy[1]["subs"] == [f"{sec}/generator_mounting"])
check("R2 PG title/status", gy[0]["title"] == "2030 Chevrolet Malibu Parts - GMPartsGiant.com" and gy[0]["status"] == 200)
nav = gmpartsgiant.categories_for("Chevrolet", "Malibu", 2030, ["alternator", "headlights"])
check("R2 PG agrees with navigation", [v for v, _ in PG.year_catalogs(gmpartsgiant.CFG, "Chevrolet", "Malibu", 2030)]
      == gy[0]["variants_read"] and len(nav["alternator"]) == 2)
fy = no_gets(fordpartsgiant.year_manifest, "Ford", "Ranger", 2030)
check("R2 split catalog: every option catalog, first + last read",
      fy[0]["trims"] == ["4_cyl_2_3l-5mt", "6_cyl_3_0l-4at", "6_cyl_4_0l-5at"]
      and fy[0]["trims_read"] == ["4_cyl_2_3l-5mt", "6_cyl_4_0l-5at"] and fy[0]["subs"] == [], fy[0])
check("R2 split catalog: a line per option catalog read", [(x["trim"], x["subs"]) for x in fy[1:]] == [
    ("4_cyl_2_3l-5mt", ["electrical/alternator_and_mountings", "electrical/starter_motor"]),
    ("6_cyl_4_0l-5at", ["electrical/alternator_and_mountings", "electrical/starter_motor"])])
r01 = no_gets(fordpartsgiant.year_manifest, "Ford", "F-150", 2001)
check("R2 real Ford 2001: 9 engine catalogs, unread ones not_fetched", len(r01[0]["trims"]) == 9
      and [x["error"] for x in r01[1:]] == ["not_fetched", "not_fetched"])
r04 = no_gets(fordpartsgiant.year_manifest, "Ford", "F-150", 2004)
check("R2 real Ford 2004: heritage offered, not read", r04[0]["variants"] == ["f_150_new_style", "f_150_heritage_old_style"]
      and r04[0]["variants_read"] == ["f_150_new_style"] and len(r04) == 1 and len(r04[0]["subs"]) == 189)
sv = no_gets(gmpartsgiant.year_manifest, "Chevrolet", "Silverado 1500", 2004)
check("R2 real GM Silverado 2004: 11 offered, 2 read", len(sv[0]["variants"]) == 11 and sv[0]["variants_read"] == ["1500_2wd", "1500_4wd"]
      and sv[1]["error"] == "not_fetched")
none = no_gets(gmpartsgiant.year_manifest, "Chevrolet", "Malibu", 2031)
check("R2 PG no catalog for the year: one line with error", len(none) == 1 and none[0]["error"] == "no 2031 catalog"
      and none[0]["variants"] == [], none)
nomp = gmpartsgiant.year_manifest("Chevrolet", "Nonesuch", 2030)
check("R2 PG model page not fetched", nomp[0]["error"] == "no model page" and nomp[0]["model_pages"][0]["status"] is None)

# ------------------------------------------------------------- PartsGiant R4
gl = no_gets(gmpartsgiant.chain_links, f"{S.G}/parts/gm-generator-19000002.html", ["19000000", "19000001", "900"])
check("R4 PG product-page link", gl == {"19000000": f"{S.G}/parts/gm-generator-asm-19000000.html"}, gl)

# ------------------------------------------------- SlugCheckedSimplePart (Volvo, Mitsubishi, Audi)
from sites import mitsubishipartsgiant, volvopartsgiant  # noqa: E402
from sites._sp_slugrules import SlugCheckedSimplePart  # noqa: E402
check("Mitsubishi and Volvo run on SlugCheckedSimplePart",
      isinstance(mitsubishipartsgiant._T, SlugCheckedSimplePart) and isinstance(volvopartsgiant._T, SlugCheckedSimplePart))
vt = volvopartsgiant._T
check("slug miss is an excluded_by reason", vt.excluded_by("door-front", "Door Shell", "", "door-assembly") == "rule:slug_miss"
      and not vt.match("door-front", "Door Shell", "", "door-assembly")
      and vt.excluded_by("door-front", "Door Shell", "", "door-shell") is None
      and vt.excluded_by("alternator", "Alternator", "", "alternator-pulley") == "rule:pulley"
      and vt.excluded_by("door-front", "Weatherstrip", "", "door-shell") == "include_miss")
VD = f"{S.V}/parts-list/2030-volvo-xc90/body-hardware/door-components"
vparts = volvopartsgiant.parts_on_page(VD, "door-front")
vman = no_gets(volvopartsgiant.list_manifest, VD, "door-front")  # product_rules category: product() re-read via the cache
vwhy = {r["pn"]: (r["matched"], r["excluded_by"]) for r in vman["rows"]}
check("Volvo door-front parts (product rule decides front)", [p["pn"] for p in vparts] == ["31335409"]
      and vparts[0]["product_check"].startswith("'Front Door'"), vparts)
check("Volvo door-front manifest has every row, no error", "error" not in vman and vwhy == {
    "31335409": (True, None), "31335410": (False, "product_rule"), "31335411": (False, "rule:slug_miss"),
    "31335412": (False, "include_miss")}, (vman.get("error"), vwhy))
vrear = no_gets(volvopartsgiant.list_manifest, VD, "door-rear")
check("Volvo door-rear manifest", {r["pn"]: r["excluded_by"] for r in vrear["rows"]}["31335410"] is None
      and {r["pn"] for r in vrear["rows"] if r["matched"]} == {p["pn"] for p in volvopartsgiant.parts_on_page(VD, "door-rear")}
      == {"31335410"})
check("SlugChecked product() takes the cache-only reader", volvopartsgiant._T.product(
    f"{S.V}/genuine/volvo~door-shell~31335409", _get=PAGES.cached)["pn"] == "31335409")
vy = no_gets(volvopartsgiant.year_manifest, "Volvo", "XC90", 2030)
check("Volvo year manifest", len(vy) == 1 and vy[0]["status"] == 200 and vy[0]["catalog"] == "2030-volvo-xc90"
      and vy[0]["subs"] == ["body-hardware/door-components", "charging-starting/alternator"], vy)

# ------------------------------------------------- Mercedes: feed class names read through badges
from sites import mbpartsgiant  # noqa: E402
ML = f"{S.M}/parts-list/2030-mercedes_benz"
mbc = mbpartsgiant.categories_for("Mercedes-Benz", "C-Class", 2030, ["alternator"])
check("MB C-Class 2030 reads the c300 and c63_amg badges", mbc == {"alternator": [
    f"{ML}-c300/charging-starting/alternator", f"{ML}-c63_amg/charging-starting/alternator"]}, mbc)
my = no_gets(mbpartsgiant.year_manifest, "Mercedes-Benz", "C-Class", 2030)
check("MB year manifest: one line per badge page read", [(x["variant"], x["catalog"], x["status"], x["subs"]) for x in my] == [
    ("c300", "2030-mercedes_benz-c300", 200, ["charging-starting/alternator"]),
    ("c63_amg", "2030-mercedes_benz-c63_amg", 200, ["charging-starting/alternator"])]
    and all(x["variants"] == ["c300", "c63_amg"] == x["variants_read"] and "error" not in x for x in my), my)
check("MB year manifest names the model pages", [p["url"].rsplit("/", 1)[1] for p in my[0]["model_pages"]]
      == ["", "mercedes_benz-c230-parts", "mercedes_benz-c300-parts", "mercedes_benz-c63_amg-parts"], my[0]["model_pages"])
mby = no_gets(mbpartsgiant.year_manifest, "Mercedes-Benz", "C300", 2030)
check("MB badge model reads its underscore slug page", [(x["catalog"], x["status"]) for x in mby]
      == [("2030-mercedes_benz-c300", 200)], mby)
mbn = no_gets(mbpartsgiant.year_manifest, "Mercedes-Benz", "E-Class", 2030)
check("MB class with no badge for the year", mbn[0]["error"] == "no catalog badge page for this year"
      and mbn[0]["variants"] == [], mbn)
_c230 = PAGES.pages.pop(f"{S.M}/mercedes_benz-c230-parts")  # a class model page not read: badges may be missing
mbu = no_gets(mbpartsgiant.year_manifest, "Mercedes-Benz", "C-Class", 2030)
PAGES.pages[f"{S.M}/mercedes_benz-c230-parts"] = _c230
check("MB year lines fail closed when a class model page was not read",
      len(mbu) == 2 and all(x.get("error") == f"model page not read: {S.M}/mercedes_benz-c230-parts" for x in mbu), mbu)
mbl = no_gets(mbpartsgiant.list_manifest, f"{ML}-c300/charging-starting/alternator", "alternator")
check("MB list manifest: rows, badge variant, product rule read from the cache", mbl["variant"] == "c300"
      and "error" not in mbl and {r["pn"]: r["excluded_by"] for r in mbl["rows"]}
      == {"272-154-00-02": None, "272-150-00-15": "product_rule"}, mbl)

# ------------------------------------------------------------- contract
SITES = sorted(p.stem for p in (HERE.parent / "sites").glob("*.py") if not p.stem.startswith("_"))
for name in SITES:
    mod = importlib.import_module(f"sites.{name}")
    check(f"{name} exports the manifest contract",
          all(callable(getattr(mod, f, None)) for f in ("categories_for", "parts_on_page", "product",
                                                        "year_manifest", "list_manifest", "chain_links")))

# ------------------------------------------------------------- unchanged records
golden = json.loads((F.FIX / "golden_records_v0.json").read_text())
now = json.loads(json.dumps(F.record_outputs()))
TL = "https://www.toyotapartsnow.com/parts-list"
EXPECTED = {  # R5 deltas: list call -> (pns before, pns after)
    f"alternator {TL}/2007-toyota-camry/charging-starting/alternator":
        (["27060-28320"], ["27060-0H111-84", "27060-0P141-84", "27060-28321-84", "27060-31081-84", "27060-28320"]),
    f"starter {TL}/1999-toyota-camry/charging-starting/starter":
        (["28100-74270-84", "28100-03100", "28100-74260"],
         ["28100-74260-84", "28100-74270-84", "28100-03100", "28100-74260"]),
}
check("golden: navigation unchanged", now["nav"] == golden["nav"])
check("golden: product records unchanged", now["products"] == golden["products"],
      [k for k in golden["products"] if now["products"].get(k) != golden["products"][k]])
for k, before in golden["lists"].items():
    after = now["lists"].get(k)
    if "gmpartsgiant" in k or "fordpartsgiant" in k:  # PartsGiant parts gained `reman` (R5b)
        check(f"golden: PG reman is a bool {k[:60]}", all(isinstance(p.get("reman"), bool) for p in after))
        after = [{x: y for x, y in p.items() if x != "reman"} for p in after]
    if k in EXPECTED:
        old, new = EXPECTED[k]
        check(f"golden: R5 delta was {k[:70]}", [p["pn"] for p in before] == old)
        check(f"golden: R5 delta now {k[:70]}", [p["pn"] for p in after] == new, [p["pn"] for p in after])
        common = {p["pn"]: p for p in after}
        for p in before:  # rows kept before keep every field, except reman on -84 (R5c)
            q2 = dict(common[p["pn"]])
            if p["pn"].endswith("-84"):
                check(f"R5c {p['pn']} reman now true", q2["reman"] is True and p["reman"] is False)
                q2["reman"] = p["reman"]
            check(f"golden: {p['pn']} otherwise unchanged", q2 == p)
    else:
        check(f"golden: unchanged {k[:90]}", after == before)

print(f"\n{'OK' if not fails else 'FAILED'}: {n - len(fails)}/{n} checks" + (f"; failing: {fails}" if fails else ""))
sys.exit(1 if fails else 0)
