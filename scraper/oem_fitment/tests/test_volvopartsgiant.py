#!/usr/bin/env python3
"""Offline test for sites/volvopartsgiant.py (SimplePart template, /genuine/ store).
Pure checks always run; page checks read the fetch.py cache only and are skipped
when it is absent (CI has no cache).
Run: python3 scraper/oem_fitment/tests/test_volvopartsgiant.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _sp_cacheonly as _cacheonly  # noqa: E402

_cacheonly.install()
from sites import volvopartsgiant as V  # noqa: E402
from sites._simplepart import NavError  # noqa: E402

B = "https://www.volvopartsgiant.com"
YEAR = f"{B}/2006-volvo-xc90-parts"
PL = f"{B}/parts-list/2006-volvo-xc90"
MIRRORS = f"{PL}/body-hardware/outside-mirrors"
BUMPER_F = f"{PL}/body-hardware/bumper-components-front"
DOORS = f"{PL}/body-hardware/door-components"
INSTR_850 = f"{B}/parts-list/1995-volvo-850/electrical/instruments-gauges"
TRUNK_850 = f"{B}/parts-list/1995-volvo-850/body-hardware/trunk-lid-components"
P_ALT = f"{B}/genuine/volvo~alternator~36012358"
P_STARTER = f"{B}/genuine/volvo~starter~8251551"
P_MIRROR = f"{B}/genuine/volvo~mirror-outside-rear~30745220"
P_LID = f"{B}/genuine/volvo~lid~9152416"
P_DOORS = [f"{B}/genuine/volvo~door-shell-{e}~{pn}" for e, pn in (
    ("front", "31385356"), ("front", "31385357"), ("rear", "31385358"), ("rear", "31385359"))]

checks = 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        raise AssertionError(msg)


# ---- pure checks
T = V._T
ok(T.year_url("Volvo", "XC90", 2006) == YEAR, "year url")
ok(T.year_url("Volvo", "240", 1992) == f"{B}/1992-volvo-240-parts", "numeric model")
try:
    T.year_url("Volvo", "60 Series", 2012)
    ok(False, "60 Series must not navigate")
except NavError:
    ok(True, "")
m = T.match
ok(m("side-mirrors", "Mirror Outside", "", "mirror-outside-rear"), "mirror outside")
ok(not m("side-mirrors", "Housing", "", "housing-driver-side"), "mirror housing")
ok(not m("side-mirrors", "Drive Assembly", "", "drive-assembly-driver-side"), "mirror drive")
ok(m("bumper-front", "Bumper Cover", "", "bumper-cover-willow-green"), "painted cover")
ok(not m("bumper-front", "Bumper Cover Band", "", "bumper-cover-band"), "cover band")
ok(not m("bumper-front", "Bumper Cover Clip", "", "fender-liner-rivet"), "clip")
ok(not m("bumper-front", "Cover", "", "cover-driver-side"), "side cover")
ok(not m("gauge-cluster", "Cluster", "", "fuel-gauge"), "850 'Cluster' is a fuel gauge by slug")
ok(m("door-front", "Door Shell", "", "door-shell-front"), "door shell")
ok(not m("power-steering-pump", "Power Steering Pump Sleeve", "", "power-steering-pump-sleeve"), "sleeve")
ok(not m("starter", "Solenoid", "", "brush-holder"), "solenoid")
ok("tailgate" not in V.CAT_PAGES and V._T.cat_pages["liftgate"].search("body-hardware/tail-gate"), "tail gate -> liftgate")
pure = checks

if not _cacheonly.have([YEAR, MIRRORS, BUMPER_F, DOORS, INSTR_850, TRUNK_850, P_ALT, P_STARTER, P_MIRROR, P_LID] + P_DOORS):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

# ---- navigation
cats = V.categories_for("Volvo", "XC90", 2006, ["side-mirrors", "window-regulator", "liftgate", "trunk-lid"])
ok(cats["side-mirrors"] == [MIRRORS], cats.get("side-mirrors"))
ok(cats["window-regulator"] == [f"{PL}/body-hardware/front-door", f"{PL}/body-hardware/rear-door"], cats.get("window-regulator"))
ok(cats["liftgate"] == [f"{PL}/body-hardware/lift-gate"], cats.get("liftgate"))
ok("trunk-lid" not in cats, "SUV has no trunk lid page")

# ---- list pages
mir = V.parts_on_page(MIRRORS, "side-mirrors")
ok(len(mir) == 9 and all(p["name"] == "Mirror Outside" for p in mir), [p["pn"] for p in mir])
bf = V.parts_on_page(BUMPER_F, "bumper-front")
ok(len(bf) == 24 and all(p["name"] == "Bumper Cover" for p in bf), [p["pn"] for p in bf])
ok("30698208" not in {p["pn"] for p in bf}, "side cover excluded")
front = {p["pn"] for p in V.parts_on_page(DOORS, "door-front")}
rear = {p["pn"] for p in V.parts_on_page(DOORS, "door-rear")}
ok(front == {"31385356", "31385357"} and rear == {"31385358", "31385359"}, (front, rear))
ok(V.parts_on_page(INSTR_850, "gauge-cluster") == [], "850 instrument page has no cluster assembly")
lid = V.parts_on_page(TRUNK_850, "trunk-lid")
ok([p["pn"] for p in lid] == ["9152416"] and "Trunk Lid" in lid[0]["product_check"], lid)

# ---- product pages
p = V.product(P_ALT)  # five models under one number, a supersession, an exchange unit
ok(p["replaces"] == ["36050266"] and p.get("exchange_unit") is True, p)
ok([(f["years"], f["model"]) for f in p["fitment"]] ==
   [([2005, 2009], "S60"), ([2005, 2006], "S80"), ([2005, 2007], "V70"), ([2005, 2007], "XC70"), ([2005, 2006], "XC90")], p["fitment"])
ok("flags" not in p, p.get("flags"))
p = V.product(P_STARTER)  # "Reman Starter" in Volvo's names; ten models
ok(p.get("reman") is True and len(p["fitment"]) == 10, p)
ok(p["fitment"][0]["raw"] == "1997 Volvo 850 | Base, GLT, R, T-5 | 5 Cyl 2.3 L GAS, 5 Cyl 2.4 L GAS", p["fitment"][0])
p = V.product(P_MIRROR)
ok(p["position"] == "Driver Side" and p["description"] == "Mirror Outside, Rear", p)
ok(p["evidence_lines"][:2] == ["Position", "Driver Side"] and "flags" not in p, p)

print(f"OK {checks} checks ({pure} pure, {checks - pure} on cached pages)")
