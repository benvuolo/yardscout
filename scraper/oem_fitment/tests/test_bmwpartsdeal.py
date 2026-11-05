#!/usr/bin/env python3
"""Offline test for sites/bmwpartsdeal.py (PartsGiant ".html" template).
Pure rule checks always run; page checks read the fetch.py cache only and are
skipped when it is absent. Run: python3 scraper/oem_fitment/tests/test_bmwpartsdeal.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _pg_cacheonly  # noqa: E402

_pg_cacheonly.install()
from sites import bmwpartsdeal as X  # noqa: E402

B = "https://www.bmwpartsdeal.com"
MODEL = f"{B}/bmw-328i-parts.html"
N51 = f"{B}/2011-bmw-328i-sedan_n51_engine_e90-parts.html"
N52 = f"{B}/2011-bmw-328i-sedan_n52_engine_e90-parts.html"
L = f"{B}/parts-list/2011-bmw-328i-sedan_n52_engine_e90"
ALT = f"{L}/engine_electrical_system/alternator.html"
STARTER = f"{L}/engine_electrical_system/starter.html"
MIRROR = f"{L}/vehicle_trim/outside_mirror.html"
TRUNK = f"{L}/bodywork/single_components_for_trunk_lid.html"
CLIMATE = f"{L}/heater_and_air_conditioning/air_conditioning_control.html"
P_ALT = f"{B}/parts/bmw-exchange_generator-12317555926.html"                       # 9 models incl. 528i, X3
P_MIRROR = f"{B}/parts/bmw-exterior_mirror_without_glass_heated_left-51167268261.html"  # Replaces, side from lr
P_STARTER = f"{B}/parts/bmw-starter-12417616500.html"                              # 33 rows
P_CLIMATE = f"{B}/parts/bmw-air_conditioning_control-64119190922.html"             # list note "Front panel, control"

n = 0


def ok(cond, msg):
    global n
    n += 1
    if not cond:
        raise AssertionError(msg)


def match(cat, name):
    return X.PARTS[cat]({"main": name, "group": name, "remark": "", "info": [], "pn": "x", "url": "u"}, name)


# ---- pure rule checks (EPC names as printed on 2011 328i list pages)
ok(match("alternator", "Exch. alternator") and not match("alternator", "Pulley, alternator"), "alternator")
ok(match("starter", "Starter") and match("starter", "Exchange starter motor") and not match("starter", "Solenoid switch"), "starter")
ok(match("ac-compressor", "RP air con.compres.w/o magnetic coupling") and not match("ac-compressor", "Relief valve"), "compressor")
ok(match("headlights", "Headlight left") and match("headlights", "Bi-xenon headlight, left") and match("headlights", "AHL-xenon headlight, right"), "headlights")
ok(not match("headlights", "Plug"), "plug excluded")
ok(match("tail-lights", "Rear light in the side panel, left") and match("tail-lights", "Rear light in trunk lid, right"), "tail lights")
ok(match("side-mirrors", "Exterior mirror w/o glass, heated, left") and match("side-mirrors", "Outside mirror w/out glass heated right"), "mirrors sold without glass")
ok(not match("side-mirrors", "Mirror glass, heated, left") and not match("side-mirrors", "Drive, outside mirror left"), "glass/drive excluded")
ok(not match("side-mirrors", "Cover cap, painted, right"), "cap excluded")
ok(match("window-regulator", "Window lifter, electric, front left") and match("window-regulator", "Drive for window lifter, front left"), "regulator + motor")
ok(not match("window-regulator", "Cover, window frame, door front left") and not match("window-regulator", "Window guide, left front door"), "frame cover / guide excluded")
ok(match("window-switch", "Switch, Window Lifter, Driver's Side") and not match("window-switch", "Switch Window Lifter"), "driver switch only")
ok(match("climate-control", "Air Conditioning Control") and match("climate-control", "Automatic Air Conditioning Control"), "climate")
ok(not match("climate-control", "Front plate, contr. auto air conditioner"), "front plate excluded")
ok(not match("fuel-pump-module", "Repair kit, fuel pump/fuel level sensor") and not match("fuel-pump-module", "Right fuel level sensor"), "repair kit / sender excluded")
ok(match("throttle-body", "Throttle Housing Assy"), "throttle")
ok(match("power-steering-pump", "Power Steering Pump") and not match("power-steering-pump", "Pulley"), "ps pump")
ok(match("gauge-cluster", "Instruments combination uncoded"), "cluster")
ok(match("ignition-coils", "Ignition Coil") and not match("ignition-coils", "Locking mechanism"), "coil")
ok(match("radiator", "Radiator") and not match("radiator", "Drain plug radiator") and not match("radiator", "Control sleeve"), "radiator")
ok(match("door-front", "Door front left") and match("door-front", "Door, front, right") and not match("door-front", "Front door brake"), "front door")
ok(match("door-rear", "Door, rear left") and not match("door-rear", "Door reinforcement, rear left"), "rear door")
ok(match("hood", "Hood") and not match("hood", "Left engine hood hinge"), "hood")
ok(match("fender", "Side panel, front left") and not match("fender", "Support fender left"), "fender")
ok(match("bumper-front", "Panel, bumper, primed, front") and not match("bumper-front", "Set, mounting parts, bumper, front"), "front bumper")
ok(match("bumper-rear", "Panel, bumper, primed, rear"), "rear bumper")
ok(match("grille", "Grille w chrome frame, left") and match("grille", "Grille right"), "kidney grilles")
ok(match("trunk-lid", "Tailgate with hole for lock barrel") and match("trunk-lid", "Tailgate without hole for lock barrel"), "sedan trunk lid printed 'Tailgate'")
ok(not match("trunk-lid", "Left trunk lid hinge") and not match("trunk-lid", "Trunk Lid Gasket"), "hinge/gasket excluded")
ok(("BMW", "3 Series") not in X.MODELS and X.MODELS[("BMW", "328i xDrive")].slugs == "328i_xdrive", "slug map")
pure = n

if not _pg_cacheonly.have([MODEL, N51, N52, ALT, STARTER, MIRROR, TRUNK, CLIMATE, P_ALT, P_MIRROR, P_STARTER, P_CLIMATE]):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

# ---- navigation: two sedan submodel catalogs for 2011
from sites import _partsgiant as T  # noqa: E402
ok([v for v, _ in T.year_catalogs(X.CFG, "BMW", "328i", 2011)] == ["sedan_n51_engine_e90", "sedan_n52_engine_e90"], "sedan variants")
cats = X.categories_for("BMW", "328i", 2011, ["alternator", "climate-control", "trunk-lid", "liftgate"])
ok(len(cats["alternator"]) == 2 and cats["alternator"][1] == ALT, cats["alternator"])
ok(len(cats["climate-control"]) == 4, cats["climate-control"])
ok("liftgate" not in cats and cats["trunk-lid"][1] == TRUNK, cats)

# ---- list pages
alt = X.parts_on_page(ALT, "alternator")
ok([(p["pn"], p["name"]) for p in alt] == [("12-31-7-555-926", "Exch. alternator")], "exchange-only alternator kept")
st = X.parts_on_page(STARTER, "starter")
ok([p["pn"] for p in st] == ["12-41-7-616-500"], "exchange starters dropped when the new starter is listed")
mir = X.parts_on_page(MIRROR, "side-mirrors")
ok(len(mir) == 12 and all(p["pn"].startswith("51-16-7-2") for p in mir), [p["pn"] for p in mir])
tr = X.parts_on_page(TRUNK, "trunk-lid")
ok([p["pn"] for p in tr] == ["41-62-7-254-425", "41-62-7-209-701"], [p["pn"] for p in tr])

# ---- product pages
a = X.product(P_ALT)
ok(a["pn"] == "12-31-7-555-926" and a["description"] == "Exchange Generator" and a["replaced_by"] == "12317551256", a)
ok([f["model"] for f in a["fitment"]] == ["128i", "323i", "328i", "328i xDrive", "328xi", "528i", "528i xDrive", "528xi", "X3"], a["fitment"])
ok(a["fitment"][2]["years"] == [2007, 2013] and "Wagon(E91)" in a["fitment"][2]["options"], a["fitment"][2])
ok(a["fitment"][8]["raw"] == "2007-2010 BMW X3 | 3.0si(E83)", a["fitment"][8]["raw"])
ok(a["evidence_lines"][3] == "Year Make Model | Submodel" and len(a["evidence_lines"]) == 13, a["evidence_lines"])
m = X.product(P_MIRROR)
ok(m["position"] == "Driver Side" and m["replaces"] == ["51-16-7-202-937"] and m["flags"] == [], m)
ok(m["fitment"][0]["raw"] == "2009-2011 BMW 323i | Sedan(E90)", m["fitment"][0])
s = X.product(P_STARTER)
ok(len(s["fitment"]) == 33 and s["fitment"][0]["model"] == "1 Series M", (len(s["fitment"]), s["fitment"][0]))

cl = X.parts_on_page(CLIMATE, "climate-control")
ok(cl[0]["pn"] == "64-11-9-190-922" and "Front panel, control" in cl[0]["list_info"], cl[0])
c = X.product(P_CLIMATE)
ok(c["position"] is None, f"a list note is not a position: {c['position']!r}")

print(f"OK {n} checks ({pure} pure)")
