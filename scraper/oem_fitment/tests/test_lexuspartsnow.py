#!/usr/bin/env python3
"""Offline test for sites/lexuspartsnow.py (PartsGiant ".html" template).
Pure rule checks always run; page checks read the fetch.py cache only and are
skipped when it is absent. Run: python3 scraper/oem_fitment/tests/test_lexuspartsnow.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _pg_cacheonly  # noqa: E402

_pg_cacheonly.install()
from sites import lexuspartsnow as X  # noqa: E402

B = "https://www.lexuspartsnow.com"
MODEL = f"{B}/lexus-es300-parts.html"
YEAR = f"{B}/2002-lexus-es300-parts.html"
L = f"{B}/parts-list/2002-lexus-es300"
ALT = f"{L}/engine_fuel_tool/alternator.html"
MIRROR = f"{L}/electrical/mirror.html"
SWITCH = f"{L}/electrical/switch_relay_computer.html"
P_ALT = f"{B}/parts/lexus-alternator-assy~27060-20230.html"                       # ES300 + ES330
P_MIRROR = f"{B}/parts/lexus-mirror-sub-assy-outer-rear-view-rh~87901-33070-a0.html"  # 2 rows, 2 engines

n = 0


def ok(cond, msg):
    global n
    n += 1
    if not cond:
        raise AssertionError(msg)


def match(cat, name):
    return X.PARTS[cat]({"main": name, "group": name, "remark": "", "info": [], "pn": "x", "url": "u"}, name)


# ---- pure rule checks (EPC names as printed on lexuspartsnow list pages)
ok(match("alternator", "Alternator Assy") and not match("alternator", "Holder Assy, Alternator Brush"), "alternator")
ok(match("starter", "Starter Assy") and not match("starter", "Starter Kit, Repair Service"), "starter")
ok(match("ac-compressor", "Compressor Assy, Cooler") and not match("ac-compressor", "Clutch Assy, Magnet"), "compressor")
ok(match("headlights", "Unit Assy, Headlamp, RH") and not match("headlights", "Retainer, Headlamp Protector, Lower LH"), "headlamp")
ok(not match("tail-lights", "Lens, Rear Combination Lamp, LH"), "lens only excluded")
ok(match("tail-lights", "Lamp Assy, Rear Combination, RH") and match("tail-lights", "Lens & Body, Rear Combination Lamp, LH"), "tail lamp")
ok(match("side-mirrors", "Mirror Sub-Assy, Outer Rear View, RH") and match("side-mirrors", "Mirror Assy, Outer Rear View, LH"), "mirror")
ok(not match("side-mirrors", "Outer Mirror, RH") and not match("side-mirrors", "Mirror Assy, Inner Rear View"), "glass / inner mirror excluded")
ok(not match("side-mirrors", "Switch Assy, Outer Mirror"), "mirror switch excluded")
ok(match("window-regulator", "Regulator Sub-Assy, Front Door Window, RH") and match("window-regulator", "Motor Assy, Power Window Regulator, LH"), "regulator + motor")
ok(not match("window-regulator", "Hinge Assy, Front Door, Upper RH"), "hinge excluded")
ok(match("window-switch", "Master Switch Assy, Power Window Regulator"), "master switch")
ok(not match("window-switch", "Switch Assy, Power Window Regulator, Rear"), "rear switch excluded")
ok(not match("climate-control", "Panel Sub-Assy, Air Conditioner") and not match("climate-control", "Housing Sub-Assy, Heater Control"), "faceplate/housing excluded")
ok(match("climate-control", "Control Assy, Air Conditioner"), "A/C control")
ok(match("fuel-pump-module", "Tube Assy, Fuel Suction") and not match("fuel-pump-module", "Pump, Fuel"), "module kept despite TUBES; bare pump out")
ok(not match("fuel-pump-module", "Tube Sub-Assy, Fuel Pump"), "pump bracket tube excluded")
ok(match("throttle-body", "Body Assy, Throttle"), "throttle")
ok(match("power-steering-pump", "Pump Assy, Vane") and not match("power-steering-pump", "Reservoir Assy, Vane Pump Oil"), "vane pump")
ok(match("gauge-cluster", "Meter Assy, Combination") and not match("gauge-cluster", "Glass, Speedometer"), "cluster")
ok(match("ignition-coils", "Coil Assy, Ignition"), "coil")
ok(match("radiator", "Radiator Assy") and match("radiator", "Radiator Assy, W/Cap") and not match("radiator", "Tank Assy, Radiator Reserve"), "radiator")
ok(match("door-front", "Panel Sub-Assy, Front Door, LH") and not match("door-front", "Panel, Front Door, Outer LH"), "door shell vs outer skin")
ok(match("hood", "Hood Sub-Assy") and not match("hood", "Protector, Hood"), "hood")
ok(match("fender", "Fender Sub-Assy, Front RH") and not match("fender", "Liner, Front Fender, RH"), "fender")
ok(match("bumper-front", "Cover, Front Bumper") and not match("bumper-front", "Cover, Front Bumper Hole, RH"), "bumper cover vs hole cover")
ok(match("bumper-rear", "Cover, Rear Bumper"), "rear bumper")
ok(match("grille", "Grille, Radiator"), "grille")
ok(match("trunk-lid", "Panel Sub-Assy, Luggage Compartment Door") and not match("trunk-lid", "Striker Assy, Luggage Compartment Door"), "trunk")
ok(match("liftgate", "Panel Sub-Assy, Back Door"), "back door")
ok(("Lexus", "IS") not in X.MODELS and X.MODELS[("Lexus", "RX 400h")].slugs == "rx400h", "slug map")
pure = n

if not _pg_cacheonly.have([MODEL, YEAR, ALT, MIRROR, SWITCH, P_ALT, P_MIRROR]):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

# ---- navigation
cats = X.categories_for("Lexus", "ES 300", 2002, ["alternator", "side-mirrors", "window-regulator", "hood", "fender", "liftgate"])
ok(cats["alternator"] == [ALT] and cats["side-mirrors"] == [MIRROR], cats)
ok([u.rsplit("/", 1)[1] for u in cats["window-regulator"]] == ["front_door_window_regulator_hinge.html", "rear_door_window_regulator_hinge.html"], cats["window-regulator"])
ok(cats["hood"] == cats["fender"] == [f"{L}/body/hood_front_fender.html"], "shared hood/fender page")
ok("liftgate" not in cats, "sedan has no back door page")

# ---- list pages
alt = X.parts_on_page(ALT, "alternator")
ok([p["pn"] for p in alt] == ["27060-20230"] and alt[0]["product_url"] == P_ALT, alt)
mir = X.parts_on_page(MIRROR, "side-mirrors")
ok(len(mir) == 36 and {p["pn"][:5] for p in mir} == {"87901", "87906"}, [p["pn"] for p in mir])
ok(mir[0]["list_info"] == ["W(MEMORY ADJUST SYSTEM),WHITE PEARL CS.,062", "Location: Passenger Side", "Part Name Code: 87901B"], mir[0]["list_info"])
sw = X.parts_on_page(SWITCH, "window-switch")
ok([p["pn"] for p in sw] == ["84040-33030"], [p["pn"] for p in sw])

# ---- product pages
a = X.product(P_ALT)
ok(a["pn"] == "27060-20230" and a["replaced_by"] == "27060-20240" and a["description"] == "ALTERNATOR Assembly", a)
ok([(f["years"], f["model"]) for f in a["fitment"]] == [([2002, 2003], "ES300"), ([2004, 2004], "ES330")], a["fitment"])
ok(a["fitment"][0]["engines"] == ["6 Cyl 3.0L"] and a["fitment"][0]["trims"] == [] and a["fitment"][0]["options"] == ["1MZFE; MCV30L-BEAGKA"], a["fitment"][0])
ok(a["evidence_lines"] == ["Part Number: 27060-20230", "Part Description: ALTERNATOR Assembly", "Replaced By: 27060-20240",
                           "Year Make Model | Trim & Engine | Important vehicle option details",
                           "2002-2003 Lexus ES300 | 6 Cyl 3.0L | 1MZFE; MCV30L-BEAGKA",
                           "2004 Lexus ES330 | 6 Cyl 3.0L | 1MZFE; MCV30L-BEAGKA"], a["evidence_lines"])
m = X.product(P_MIRROR)
ok(m["position"] == "Location: Passenger Side" and m["flags"] == [], m)
ok(m["fitment"][1]["raw"] == "2004-2005 Lexus ES330 | 6 Cyl 3.0L, 6 Cyl 3.3L | 1MZFE, 3MZFE; MCV30L-BEAGKA, MCV31L-BEAGKA", m["fitment"][1]["raw"])
ok(m["fitment"][1]["engines"] == ["6 Cyl 3.0L", "6 Cyl 3.3L"], m["fitment"][1])

print(f"OK {n} checks ({pure} pure)")
