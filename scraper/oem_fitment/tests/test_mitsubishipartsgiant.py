#!/usr/bin/env python3
"""Offline test for sites/mitsubishipartsgiant.py (SimplePart template, /genuine/ store).
Pure checks always run; page checks read the fetch.py cache only and are skipped
when it is absent (CI has no cache).
Run: python3 scraper/oem_fitment/tests/test_mitsubishipartsgiant.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _sp_cacheonly as _cacheonly  # noqa: E402

_cacheonly.install()
from sites import mitsubishipartsgiant as M  # noqa: E402

B = "https://www.mitsubishipartsgiant.com"
YEAR = f"{B}/2008-mitsubishi-lancer-parts"
PL = f"{B}/parts-list/2008-mitsubishi-lancer"
MIRRORS = f"{PL}/body-hardware/outside-mirrors"
FRONT_DOOR = f"{PL}/body-hardware/front-door"
AC = f"{PL}/a-c-heating/a-c-compressor"
ALT = f"{PL}/charging-starting/alternator"
DOORS = f"{PL}/body-hardware/door-components"
GALANT_STARTER = f"{B}/parts-list/2004-mitsubishi-galant/charging-starting/starter"
P_MIRROR = f"{B}/genuine/mitsubishi~mirror-assembly-driver-side~7632a093"
P_AC = f"{B}/genuine/mitsubishi~compressor~7813a328"
P_SWITCH = f"{B}/genuine/mitsubishi~window-switch-passenger-side~mr587946"
P_REMAN_ALT = f"{B}/genuine/mitsubishi~alternator~m984944d"
DOOR_PRODUCTS = [f"{B}/genuine/mitsubishi~door-shell-{s}~{pn}" for s, pn in (
    ("driver-side", "5700a479"), ("passenger-side", "5700a480"), ("driver-side", "5730a529"),
    ("passenger-side", "5730a530"), ("driver-side", "5730a673"), ("passenger-side", "5730a674"))]

checks = 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        raise AssertionError(msg)


# ---- pure checks
T = M._T
ok(T.year_url("Mitsubishi", "Outlander Sport", 2015) == f"{B}/2015-mitsubishi-outlander_sport-parts", "underscore slug")
ok(all(s == s.lower() and " " not in s for s in M.MODEL_SLUGS.values()), "slugs")
ok(T.year_url("Mitsubishi", "3000GT", 1995) == f"{B}/1995-mitsubishi-3000gt-parts", "3000gt")
ok(T.year_url("Mitsubishi", "Mirage G4", 2017) == f"{B}/2017-mitsubishi-mirage_g4-parts", "mirage g4")
m = T.match
ok(m("side-mirrors", "Mirror Assembly", "", "mirror-assembly-driver-side"), "mirror")
ok(not m("side-mirrors", "Mirror Glass", "", "mirror-glass-driver-side"), "mirror glass")
ok(not m("side-mirrors", "Mirror Assembly Nut", "", "high-mount-lamp-nut"), "mirror nut")
ok(not m("ac-compressor", "Dehydrator", "", "bolt-a-c-condenser"), "loose list name, slug says bolt")
ok(not m("ac-compressor", "Compressor", "", "power-steering-pump"), "slug must agree")
ok(m("ac-compressor", "Compressor", "", "compressor"), "bare compressor")
ok(m("window-regulator", "Motor", "", "window-motor"), "window motor printed as Motor")
ok(m("window-regulator", "Regulator", "", "window-regulator-driver-side"), "older Regulator name")
ok(not m("window-regulator", "Motor", "", "fan-motor-driver-side"), "fan motor")
ok(m("starter", "Starter", "", "remanufactured-starter"), "reman starter kept")
ok(not m("starter", "Starter Solenoid", "", "starter-solenoid"), "solenoid")
ok(not m("power-steering-pump", "Power Steering", "", "power-steering-pump-seal-kit"), "seal kit")
ok(not m("climate-control", "Heater Control Support", "", "heater-control-support"), "support")
ok(not m("grille", "Outer Grille", "", "outer-grille-driver-side"), "outer grille")
ok(m("headlights", "Lens & Housing", "", "lens-housing-driver-side"), "headlamp body")
pure = checks

if not _cacheonly.have([YEAR, MIRRORS, FRONT_DOOR, AC, ALT, DOORS, GALANT_STARTER, P_MIRROR, P_AC, P_SWITCH, P_REMAN_ALT] + DOOR_PRODUCTS):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

# ---- navigation
cats = M.categories_for("Mitsubishi", "Lancer", 2008, ["side-mirrors", "window-regulator", "alternator", "liftgate"])
ok(cats["side-mirrors"] == [MIRRORS], cats.get("side-mirrors"))
ok(cats["window-regulator"] == [FRONT_DOOR, f"{PL}/body-hardware/rear-door"], cats.get("window-regulator"))
ok(cats["alternator"] == [ALT], cats.get("alternator"))
ok("liftgate" not in cats, "sedan has no liftgate page")

# ---- list pages
mir = {p["pn"]: p for p in M.parts_on_page(MIRRORS, "side-mirrors")}
ok(sorted(mir) == ["7632A093", "7632A094"], sorted(mir))
ok(mir["7632A093"]["product_url"] == P_MIRROR and mir["7632A093"]["list_location"] == ["Driver Side"], mir["7632A093"])
ac = sorted(p["pn"] for p in M.parts_on_page(AC, "ac-compressor"))
ok(ac == ["7813A321", "7813A322", "7813A328"], ac)  # no clutch, coil, rotor, dehydrator, bolts
ok(M.parts_on_page(ALT, "alternator") == [], "2008 Lancer alternator page embeds components only")
reg = sorted((p["pn"], p["name"]) for p in M.parts_on_page(FRONT_DOOR, "window-regulator"))
ok(reg == [("5713A085", "Window Motor"), ("5713A089", "Motor"), ("5713A090", "Window Motor"),
           ("5713A125", "Window Regulator"), ("5713A126", "Window Regulator")], reg)
sw = sorted(p["pn"] for p in M.parts_on_page(FRONT_DOOR, "window-switch"))
ok(sw == ["8608A068", "MR587942", "MR587944", "MR587946"], sw)
front = {p["pn"]: p["product_check"] for p in M.parts_on_page(DOORS, "door-front")}
rear = {p["pn"]: p["product_check"] for p in M.parts_on_page(DOORS, "door-rear")}
ok(sorted(front) == ["5700A479", "5700A480"] and "Panel Assembly, Front Door, Left-Hand" in front["5700A479"], front)
ok(sorted(rear) == ["5730A529", "5730A530", "5730A673", "5730A674"], rear)
st = M.parts_on_page(GALANT_STARTER, "starter")
ok([(p["pn"], p["reman"]) for p in st] == [("M1810A001D", True)], st)

# ---- product pages
p = M.product(P_MIRROR)
ok(p["pn"] == "7632A093" and p["position"] == "Driver Side" and p["replaces"] == [], p)
ok(len(p["fitment"]) == 1 and p["fitment"][0]["years"] == [2008, 2015] and p["fitment"][0]["model"] == "Lancer", p["fitment"])
ok(p["fitment"][0]["engines"] == ["4 Cyl 2.0 L GAS", "4 Cyl 2.4 L GAS"] and "Ralliart Sportback" in p["fitment"][0]["trims"], p["fitment"])
ok(p["evidence_lines"][:2] == ["Position", "Driver Side"] and "2008-2015 Mitsubishi Lancer" in p["evidence_lines"], p["evidence_lines"])
ok("flags" not in p and "reman" not in p, p.get("flags"))

p = M.product(P_AC)  # one number, two models
ok([(f["years"], f["model"]) for f in p["fitment"]] == [([2008, 2010], "Lancer"), ([2007, 2008], "Outlander")], p["fitment"])
ok(p["other_names"] == "Compressor Assembly, Air Conditioner; A/C Compressor", p["other_names"])
ok("flags" not in p, p.get("flags"))

p = M.product(P_SWITCH)  # multi-span cell, seven models
end = [f for f in p["fitment"] if f["model"] == "Endeavor"]
ok([f["years"] for f in end] == [[2010, 2011], [2007, 2008]] and end[0]["raw"] == end[1]["raw"], end)
ok(end[0]["year_spans"] == [[2010, 2011], [2007, 2008]], end[0])
ok(sorted({f["model"] for f in p["fitment"]}) == ["Endeavor", "Galant", "Lancer", "Montero", "Outlander", "Outlander Sport"], p["fitment"])
ok(p["position"] == "Passenger Side" and "flags" not in p, p)

p = M.product(P_REMAN_ALT)  # list says "Alternator"; product says remanufactured
ok(p["reman"] is True and p["other_names"] == "Remanufactured Alternat", p)
ok([(f["years"], f["model"]) for f in p["fitment"]] == [([2004, 2004], "Endeavor"), ([2004, 2004], "Galant")], p["fitment"])

print(f"OK {checks} checks ({pure} pure, {checks - pure} on cached pages)")
