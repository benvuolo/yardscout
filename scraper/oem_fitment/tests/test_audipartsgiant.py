#!/usr/bin/env python3
"""Offline test for sites/audipartsgiant.py (SimplePart template, /genuine/ store).
Pure checks always run; page checks read the fetch.py cache only and are skipped
when it is absent (CI has no cache).
Run: python3 scraper/oem_fitment/tests/test_audipartsgiant.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _sp_cacheonly as _cacheonly  # noqa: E402

_cacheonly.install()
from sites import audipartsgiant as A  # noqa: E402
from sites._simplepart import NavError  # noqa: E402

B = "https://www.audipartsgiant.com"
YEAR = f"{B}/2008-audi-a4-parts"
PL = f"{B}/parts-list/2008-audi-a4"
ALT = f"{PL}/charging-starting/alternator"
STARTER = f"{PL}/charging-starting/starter"
MIRRORS = f"{PL}/body-hardware/outside-mirrors"
FUEL = f"{PL}/air-fuel-delivery/fuel-supply"
GRILLE = f"{PL}/body-hardware/grille-components"
P_ALT = f"{B}/genuine/audi~alternator~06b903016ab"
P_STARTER = f"{B}/genuine/audi~starter~06e911023e"
P_FUEL = f"{B}/genuine/audi~fuel-pump-assembly~8e0919051ak"
P_SWITCH = f"{B}/genuine/audi~window-switch~8h0959851c5pr"

checks = 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        raise AssertionError(msg)


# ---- pure checks
T = A._T
ok(T.year_url("Audi", "A4 Quattro", 2009) == f"{B}/2009-audi-a4_quattro-parts", "quattro slug")
ok(T.year_url("Audi", "A8", 1998) == f"{B}/1998-audi-a8-parts", "A8 early")
ok(T.year_url("Audi", "A8", 2006) == f"{B}/2006-audi-a8_quattro-parts", "A8 after 1999")
ok(T.year_url("Audi", "Allroad", 2003) == f"{B}/2003-audi-allroad_quattro-parts", "allroad 2001-05")
ok(T.year_url("Audi", "Allroad", 2014) == f"{B}/2014-audi-allroad-parts", "allroad 2013-16")
for model, year in (("Allroad", 2009), ("A5", 2018)):
    try:
        T.year_url("Audi", model, year)
        ok(False, f"{model} {year} must not navigate")
    except NavError:
        ok(True, "")
ok("door-front" not in A.CAT_PAGES and "door-rear" not in A.CAT_PAGES, "doors not crawled")
m = T.match
ok(m("headlights", "Headlamp Assembly", "", "composite-headlamp"), "composite headlamp")
ok(m("climate-control", "Heater Control", "", "dash-control-unit"), "heater control")
ok(not m("side-mirrors", "Mirror Housing", "", "mirror-housing"), "mirror cap")
ok(not m("side-mirrors", "Motor & Base", "", "motor-base"), "motor & base")
ok(not m("fuel-pump-module", "Fuel Pump", "", "fuel-pump"), "high-pressure pump")
ok(m("fuel-pump-module", "Fuel Pump", "", "fuel-pump-assembly"), "in-tank assembly by slug")
ok(not m("alternator", "Alternator", "", "voltage-regulator"), "regulator listed as Alternator")
ok(not m("ac-compressor", "Compressor Sleeve", "", "compressor-assembly-sleeve"), "sleeve")
ok(not m("bumper-front", "Bumper Cover Pin", "", "bumper-cover-pin"), "pin")
ok(m("grille", "Center Grille", "", "center-grille"), "center grille")
ok(not m("grille", "Lower Grille", "", "outer-grille"), "lower grille")
pure = checks

if not _cacheonly.have([YEAR, ALT, STARTER, MIRRORS, FUEL, GRILLE, P_ALT, P_STARTER, P_FUEL, P_SWITCH]):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

# ---- navigation
cats = A.categories_for("Audi", "A4", 2008, ["alternator", "window-regulator", "window-switch", "liftgate"])
ok(cats["alternator"] == [ALT], cats.get("alternator"))
ok(cats["window-regulator"] == [f"{PL}/body-hardware/door"], cats.get("window-regulator"))
ok("liftgate" not in cats, "sedan")

# ---- list pages
ok([p["pn"] for p in A.parts_on_page(ALT, "alternator")] == ["06B-903-016-AB"], "only the new alternator (X rows are reman)")
ok([p["pn"] for p in A.parts_on_page(STARTER, "starter")] == ["06E-911-023-E"], "only the new starter")
ok(A.parts_on_page(MIRRORS, "side-mirrors") == [], "no mirror assembly sold")
fuel = sorted(p["pn"] for p in A.parts_on_page(FUEL, "fuel-pump-module"))
ok(fuel == ["8E0-919-051-AK", "8E0-919-051-CN", "8E0-919-051-CQ"], fuel)
gr = {p["pn"] for p in A.parts_on_page(GRILLE, "grille")}
ok(len(gr) == 6 and not any(pn.startswith("8E0-807") for pn in gr), gr)

# ---- product pages
p = A.product(P_ALT)
ok(p["pn"] == "06B-903-016-AB" and len(p["fitment"]) == 8 and "flags" not in p, p)
p = A.product(P_STARTER)  # A4, A4 Quattro, A6 under one number; supersession
ok(p["replaces"] == ["06E-911-023-C"], p["replaces"])
ok([(f["years"], f["model"]) for f in p["fitment"]][:3] == [([2006, 2009], "A4"), ([2005, 2009], "A4 Quattro"), ([2006, 2011], "A6")], p["fitment"])
p = A.product(P_FUEL)  # multi-span cell "2008, 2005-2006 Audi A4"
a4 = [f for f in p["fitment"] if f["model"] == "A4"]
ok([f["years"] for f in a4] == [[2008, 2008], [2005, 2006]] and a4[0]["raw"] == a4[1]["raw"], a4)
p = A.product(P_SWITCH)
ok(p["position"] == "Driver Side" and p["other_names"] == "Switch", p)

print(f"OK {checks} checks ({pure} pure, {checks - pure} on cached pages)")
