#!/usr/bin/env python3
"""Offline test for sites/subarupartsdeal.py (PartsGiant ".html" template).
Pure rule checks always run; page checks read the fetch.py cache only and are
skipped when it is absent. Run: python3 scraper/oem_fitment/tests/test_subarupartsdeal.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _pg_cacheonly  # noqa: E402

_pg_cacheonly.install()
from sites import subarupartsdeal as S  # noqa: E402

B = "https://www.subarupartsdeal.com"
MODEL = f"{B}/subaru-outback-parts.html"
YEAR = f"{B}/2011-subaru-outback-parts.html"
L = f"{B}/parts-list/2011-subaru-outback"
ALT = f"{L}/engine_electronics/alternator.html"
HEAD = f"{L}/body_electronics/head_lamp.html"
MIRROR = f"{L}/outer_accessories/rear_view_mirror.html"
FUEL = f"{L}/engine_mounting_cooling/fuel_tank.html"
P_ALT = f"{B}/parts/subaru-alternator-assembly~23700aa620.html"      # Legacy + Outback + Tribeca
P_HEAD = f"{B}/parts/subaru-lamp-assembly-head-left~84001aj01b.html"  # side from list, Replaced By
P_PSP = f"{B}/parts/subaru-pump-power-steering~34430aj020.html"

n = 0


def ok(cond, msg):
    global n
    n += 1
    if not cond:
        raise AssertionError(msg)


def match(cat, name):
    return S.PARTS[cat]({"main": name, "group": name, "remark": "", "info": [], "pn": "x", "url": "u"}, name)


# ---- pure rule checks (names as printed on 2001-2011 catalog pages)
ok(match("alternator", "Alternator Assembly"), "alternator")
ok(not match("alternator", "Rear Cover Assembly-Alternator"), "alternator cover")
ok(match("starter", "Starter Motor Assembly") and not match("starter", "Housing Assembly-Starter"), "starter")
ok(match("ac-compressor", "Compressor Assembly") and not match("ac-compressor", "Clutch Assembly-Compressor"), "compressor")
ok(match("headlights", "Lamp Assembly-Head Left") and not match("headlights", "Lens & Body-Head Lamp Left"), "headlamp vs lens")
ok(match("tail-lights", "Lens & Body-Rear Combination Lamp Left"), "2010+ tail lamp housing")
ok(match("tail-lights", "Lamp Assembly-Rear Combination Right(BLACK MICA)"), "painted tail lamp")
ok(not match("tail-lights", "Lamp Assembly-Rear Finisher,Left(BLACK MICA)"), "finisher lamp excluded")
ok(not match("tail-lights", "Cover-Rear Combination Lamp,Left"), "lamp cover excluded")
ok(match("side-mirrors", "Door Mirror Unit-Left") and match("side-mirrors", "Mirror Assembly-Door,Right(BLACK MICA)"), "mirrors")
ok(not match("side-mirrors", "Mirror-Repair,Left") and not match("side-mirrors", "Cover-Cap Out Mirror,Left"), "mirror glass/cap excluded")
ok(match("window-regulator", "Regulator & Motor Assembly-Front Left") and match("window-regulator", "Motor Assembly-Regulator,Front Left"), "regulators")
ok(not match("window-regulator", "Glass Assembly-Front Door,Left"), "door glass excluded")
ok(match("window-switch", "Switch-Power Window Main") and not match("window-switch", "Switch-Power Window Sub"), "master switch only")
ok(match("climate-control", "Heater Control Assembly") and not match("climate-control", "Knob-Mode"), "climate")
ok(match("fuel-pump-module", "Pump Assembly-Fuel") and not match("fuel-pump-module", "Pump-Fuel"), "module, not bare pump")
ok(match("throttle-body", "Chamber Assembly-Electric Throttle") and match("throttle-body", "Chamber And Sensor Assembly-Throttle"), "throttle")
ok(not match("throttle-body", "Sensor Assembly-Throttle"), "TPS excluded")
ok(match("power-steering-pump", "Pump-Power Steering"), "'ring' exclude must not hit 'steering'")
ok(not match("power-steering-pump", "Connector-Pump Assembly"), "pump connector excluded")
ok(match("gauge-cluster", "Meter-Main Assembly") and not match("gauge-cluster", "Meter Assembly-Fuel"), "cluster vs fuel gauge")
ok(match("ignition-coils", "Coil Assembly-Ignition"), "coil")
ok(match("radiator", "Radiator Complete") and not match("radiator", "Shroud-Radiator"), "radiator")
ok(match("door-front", "Panel Assembly-Front Door,Left") and not match("door-front", "Pad-Front Door Inner,Left"), "front door")
ok(match("door-rear", "Panel Assembly-Rear Door,Right") and not match("door-front", "Panel Assembly-Rear Door,Right"), "rear door")
ok(match("hood", "Hood Complete-Front") and not match("hood", "Hinge Complete-Front Hood,Left"), "hood")
ok(match("fender", "Fender Complete-Front,Left") and not match("fender", "Cover-Front Fender,Left"), "fender")
ok(match("bumper-front", "Bumper Face-Front") and not match("bumper-front", "Cover-Front Bumper"), "front bumper face")
ok(match("bumper-rear", "Bumper-Face,Rear") and not match("bumper-rear", "Energy Absorber-Rear Bumper"), "rear bumper face")
ok(match("grille", "Front Grille Assembly"), "grille")
ok(match("trunk-lid", "Trunk Lid Complete") and not match("trunk-lid", "Hinge Assembly-Trunk Lid,Left"), "trunk")
ok(match("liftgate", "Panel-Rear Gate") and not match("liftgate", "Hinge-Back Door"), "liftgate")
pure = n

if not _pg_cacheonly.have([MODEL, YEAR, ALT, HEAD, MIRROR, FUEL, P_ALT, P_HEAD, P_PSP]):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

# ---- navigation
cats = S.categories_for("Subaru", "Outback", 2011, ["alternator", "headlights", "door-front", "door-rear", "power-steering-pump", "fuel-pump-module"])
ok(cats["alternator"] == [ALT] and cats["headlights"] == [HEAD], cats)
ok(cats["door-front"] == cats["door-rear"] == [f"{L}/door/front_door_panel_rear_or_slide_door_panel.html"], "shared door page")
ok(cats["power-steering-pump"] == [f"{L}/steering_system_cable/oil_pump.html"], cats["power-steering-pump"])
ok(cats["fuel-pump-module"] == [FUEL], cats["fuel-pump-module"])

# ---- list pages
alt = S.parts_on_page(ALT, "alternator")
ok([p["pn"] for p in alt] == ["23700AA620", "23700AA621"], [p["pn"] for p in alt])
ok(alt[0]["product_url"] == P_ALT and "Replaced By: 23700AA831" in alt[0]["list_info"], alt[0])
head = {p["pn"]: p for p in S.parts_on_page(HEAD, "headlights")}
ok(sorted(head) == ["84001AJ00B", "84001AJ00D", "84001AJ01B", "84001AJ01D"], sorted(head))
ok(head["84001AJ01B"]["list_info"][0] == "Location: Driver Side", head["84001AJ01B"]["list_info"])
mir = [p["pn"] for p in S.parts_on_page(MIRROR, "side-mirrors")]
ok(len(mir) == 10 and all(p.startswith("91036AJ") for p in mir), mir)
fuel = [p["pn"] for p in S.parts_on_page(FUEL, "fuel-pump-module")]
ok(sorted(fuel) == ["42021AJ060", "42021AJ061", "42021AJ070", "42021AJ071", "42021AJ090", "42021AJ091"], fuel)

# ---- product pages
a = S.product(P_ALT)
ok(a["pn"] == "23700AA620" and a["replaced_by"] == "23700AA831" and a["replaces"] == [], a)
ok([(f["years"], f["make"], f["model"]) for f in a["fitment"]] ==
   [([2010, 2011], "Subaru", "Legacy"), ([2010, 2011], "Subaru", "Outback"), ([2010, 2011], "Subaru", "Tribeca")], a["fitment"])
ok(a["fitment"][2]["engines"] == ["3.6L H6"] and a["fitment"][2]["trims"] == ["5ST", "Base"], a["fitment"][2])
ok(a["fitment"][0]["raw"] == "2010-2011 Subaru Legacy | 3.6L H6 | 3.6R, 3.6R Limited, 3.6R Premium", a["fitment"][0]["raw"])
ok(a["evidence_lines"][-4:] == ["Year Make Model | Engine | Important vehicle option details",
                                "2010-2011 Subaru Legacy | 3.6L H6 | 3.6R, 3.6R Limited, 3.6R Premium",
                                "2010-2011 Subaru Outback | 3.6L H6 | 3.6R, 3.6R Limited, 3.6R Premium",
                                "2010-2011 Subaru Tribeca | 3.6L H6 | 5ST, Base"], a["evidence_lines"])
ok(a["position"] is None and a["flags"] == [], a)
S.parts_on_page(HEAD, "headlights")  # list position is read by product()
h = S.product(P_HEAD)
ok(h["position"] == "Location: Driver Side" and h["replaced_by"] == "84001AJ01G", h)
ok([f["model"] for f in h["fitment"]] == ["Legacy", "Outback"] and len(h["fitment"][1]["trims"]) == 8, h["fitment"])
p = S.product(P_PSP)
ok(p["description"] == "Power Steering Pump Assy", p["description"])  # the page's "Part Description"
ok(p["fitment"][1]["engines"] == ["2.5L H4 Turbo", "3.6L H6"], p["fitment"][1])

print(f"OK {n} checks ({pure} pure)")
