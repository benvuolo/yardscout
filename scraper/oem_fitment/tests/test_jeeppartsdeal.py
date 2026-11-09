#!/usr/bin/env python3
"""Offline test for sites/jeeppartsdeal.py (SimplePart template).
Pure parser checks always run; page checks read the fetch.py cache only
and are skipped when it is absent.
Run: python3 scraper/oem_fitment/tests/test_jeeppartsdeal.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _sp_cacheonly as _cacheonly  # noqa: E402

_cacheonly.install()
from sites import jeeppartsdeal as J  # noqa: E402

B = "https://www.jeeppartsdeal.com"
YEAR = f"{B}/catalog/2014-jeep-patriot-parts"
ALT = f"{B}/parts-list/2014-jeep-patriot/charging-starting/alternator"
HEAD = f"{B}/parts-list/2014-jeep-patriot/headlights-lighting/headlamps"
FRONT = f"{B}/parts-list/2014-jeep-patriot/body-hardware/bumper-components-front"
P_NEW = f"{B}/oem/mopar~alternatr-engine~4801477ag"
P_OLD = f"{B}/oem/mopar~alternatr-engine~4801477aa"
P_SPANS = f"{B}/oem/mopar~engine-starter~56041207ae"
P_HEAD = f"{B}/oem/mopar~drivers-halogen-headlight-replacement~5303843ae"

checks = 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        raise AssertionError(msg)


m = J._T.match
ok(m("headlights", "Headlamp", ""), "headlamp")
ok(not m("headlights", "Headlamp", "Headlamp Bulb"), "bulb named Headlamp excluded via short name")
ok(m("fuel-pump-module", "Module - Fuel Pump/Level Unit", "Fuel Pump Assembly"), "fuel module")
ok(not m("fuel-pump-module", "Level Unit - Fuel", "Sending Unit"), "sender excluded")
ok(m("bumper-front", "Fascia - Front Upper", "Upper Cover"), "fascia")
ok(not m("bumper-front", "Absorber - Front Bumper Fascia", "Absorber"), "absorber excluded")
ok(not m("door-front", "Door - Front Door Outer", "Outer Panel"), "outer skin excluded")
ok(not m("ac-compressor", "Compressor - Air Suspension", ""), "air-suspension compressor excluded")
ok(J._T.year_url("Jeep", "Grand Cherokee", 2004) == f"{B}/catalog/2004-jeep-grand-cherokee-parts", "slug")
# audit 2026-11-05: 5143152AA (2005 Grand Cherokee headlamp-components) is the headlamp boot
ok(not m("headlights", "Headlamp", "Boot") and m("headlights", "Lamp - Headlamp Parking And Turn", "Headlamp Assembly"),
   "headlamp boot excluded via short name")
# worklist v2 (2026-11-05): Dodge / Chrysler / Ram on the same catalog
from sites._simplepart import NavError  # noqa: E402
ok(J._T.year_url("Dodge", "Grand Caravan", 2010) == f"{B}/catalog/2010-dodge-grand-caravan-parts", "dodge slug")
ok(J._T.year_url("Chrysler", "PT Cruiser", 2006) == f"{B}/catalog/2006-chrysler-pt-cruiser-parts", "chrysler slug")
ok(J._T.year_url("Ram", "1500", 2012) == f"{B}/catalog/2012-ram-1500-parts", "ram make 2011+")
ok(J._T.year_url("Dodge", "Ram 1500", 2002) == f"{B}/catalog/2002-dodge-ram-1500-parts", "dodge ram 1500 1994-2010")
ok(J._T.year_url("Chrysler", "300C", 2006) == f"{B}/catalog/2006-chrysler-300-parts", "300C is printed as 300")


def nav_err(make, model, year):
    try:
        J._T.year_url(make, model, year)
    except NavError:
        return True
    return False


ok(nav_err("Dodge", "Ram 1500", 2012), "Dodge Ram 1500 2011+ is make Ram: no Dodge page requested")
ok(nav_err("Dodge", "Ram 1500", 1990), "pre-1994 D150/W150 is not one model")
ok(nav_err("Dodge", "Caravan/Grand Caravan", 2005), "combined feed name is not one model")
ok(nav_err("Dodge", "Ram Van", 2001), "1999-2003 vans are 1500/2500/3500")
_wl = json.loads((Path(__file__).resolve().parent.parent / "worklist.json").read_text())["sites"][J.SITE]
_mk = {s["make"] for s in _wl["segments"]}
# v2 added Dodge/Chrysler/Ram; later versions re-open the done site for new
# tiers only (tier C: v4, ops/interchange.md "Category breadth")
ok(_wl.get("version", 1) >= 2 and _mk == {"Jeep", "Dodge", "Chrysler", "Ram"}, f"worklist v2+ makes {_mk}")
ok(_wl.get("tierC") is True, "worklist tierC flag set (tier C rules in this module)")
ok(all(s["make"] in J.URL_MAKE for s in _wl["segments"]), "every worklist make has a URL make")
ok(all(s["site"] == J.SITE for s in _wl["segments"]), "segments name this site")
ok(_wl["segments"][0]["make"] == "Jeep", "Jeep (v1, done) segments stay first and unchanged")
pure = checks

if not _cacheonly.have([YEAR, ALT, HEAD, FRONT, P_NEW, P_OLD, P_HEAD, P_SPANS]):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

cats = J.categories_for("Jeep", "Patriot", 2014, ["alternator", "headlights", "liftgate", "trunk-lid"])
ok(cats["alternator"] == [ALT], cats)
ok(HEAD in cats["headlights"], cats["headlights"])
ok("trunk-lid" not in cats, "no trunk page on an SUV")

alt = {p["pn"]: p for p in J.parts_on_page(ALT, "alternator")}
ok(sorted(alt) == ["4801323AD", "4801323AK", "4801477AA", "4801477AG"], sorted(alt))  # R-numbers dropped: new numbers exist
ok(alt["4801477AA"]["list_section"] == "other" and alt["4801477AA"]["list_replaced_by"] == "4801477AG", alt["4801477AA"])
ok(alt["4801477AG"]["product_url"] == P_NEW, alt["4801477AG"]["product_url"])
head = {p["pn"]: p for p in J.parts_on_page(HEAD, "headlights")}
ok(sorted(head) == ["5303842AE", "5303843AE"], sorted(head))
ok(head["5303843AE"]["list_location"] == ["Driver Side"], head["5303843AE"])
fr = sorted(p["pn"] for p in J.parts_on_page(FRONT, "bumper-front"))
ok("68091521AA" in fr and "68091526AA" not in fr, fr)  # fascia yes, grille no
ok([p["pn"] for p in J.parts_on_page(FRONT, "grille")] == ["68091526AA"], "grille from bumper page")

p = J.product(P_NEW)  # multi-make block
ok(p["replaces"] == ["4801477AA"] and p["position"] is None, p)
rows = [(f["years"], f["make"], f["model"]) for f in p["fitment"]]
ok(rows == [([2011, 2014], "Chrysler", "200"), ([2008, 2010], "Chrysler", "Sebring"), ([2008, 2014], "Dodge", "Avenger"),
            ([2009, 2009], "Dodge", "Caliber"), ([2007, 2017], "Jeep", "Compass"), ([2007, 2017], "Jeep", "Patriot")], rows)
ok(p["fitment"][3]["trims"] == ["SRT-4"], p["fitment"][3])
ok(p["fitment"][5]["engines"] == ["4 Cyl 2.0 L GAS", "4 Cyl 2.4 L GAS"], p["fitment"][5])
ok(p["evidence_lines"][:3] == ["Replaces", "4801477AA", "Vehicle Fitment"] and len(p["evidence_lines"]) == 24, p["evidence_lines"])
ok("flags" not in p, p.get("flags"))

p = J.product(P_OLD)  # superseded number, catalog-style columns
ok(p["replaced_by"] == ["4801477AG"], p["replaced_by"])
ok(p["fitment"][4]["model"] == "Compass" and p["fitment"][4]["years"] == [2007, 2015], p["fitment"][4])
ok(p["fitment"][4]["other_columns"]["Important vehicle option details"].startswith("Base (4WD, FWD), Latitude (4WD, FWD)"), p["fitment"][4])
ok("flags" not in p, p.get("flags"))

p = J.product(P_HEAD)
ok(p["position"] == "Front Driver Side" and p["replaces"] == ["5303843AA", "5303843AB", "5303843AD", "5303843AC"], p)
ok("flags" not in p, p.get("flags"))

p = J.product(P_SPANS)  # "2003-2004, 1999-2000 Jeep Grand Cherokee"
ok([f["years"] for f in p["fitment"]] == [[2003, 2004], [1999, 2000]], p["fitment"])
ok(p["fitment"][0]["year_spans"] == [[2003, 2004], [1999, 2000]] and "flags" not in p, p.get("flags"))

print(f"OK {checks} checks ({pure} pure, {checks - pure} on cached pages)")
