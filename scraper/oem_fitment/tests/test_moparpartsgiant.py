#!/usr/bin/env python3
"""Offline test for sites/moparpartsgiant.py (PartsGiant ".html" template).
Pure rule checks always run; page checks read the fetch.py cache only and are
skipped when it is absent. Run: python3 scraper/oem_fitment/tests/test_moparpartsgiant.py"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _pg_cacheonly  # noqa: E402

_pg_cacheonly.install()
from sites import moparpartsgiant as P  # noqa: E402
from sites import _partsgiant as T  # noqa: E402

B = "https://www.moparpartsgiant.com"
MODEL = f"{B}/dodge-grand_caravan-parts.html"
YEAR = f"{B}/2010-dodge-grand_caravan-parts.html"
L = f"{B}/parts-list/2010-dodge-grand_caravan"
MIRRORS = f"{L}/doors_door_mirrors_and_related_parts/mirror_exterior.html"
LAMPS = f"{L}/electrical/lamps_front.html"
ALT = f"{L}/electrical/generator_alternator_related_parts.html"
P_HEAD = f"{B}/parts/mopar-headlamp-headlamp-park-and-turn~5113332ad.html"
P_MIRROR = f"{B}/parts/mopar-mirror-outside-rearview-electric~1an401bgad.html"   # list says Right, page says Driver Side
P_STARTER = f"{B}/parts/mopar-starter~56027702ac.html"                         # 7 rows, Dodge + Jeep models

n = 0


def ok(cond, msg):
    global n
    n += 1
    if not cond:
        raise AssertionError(msg)


def match(cat, group, info=""):
    inc, exc_head, exc_full = (tuple(P.PARTS[cat]) + (None, None))[:3]
    text = f"{group} | {group} |  | {info}"
    head = f"{group} | {group} | "
    return bool(re.search(inc, text, re.I) and not (exc_head and re.search(exc_head, head, re.I))
                and not (exc_full and re.search(exc_full, text, re.I)))


ok(match("alternator", "GENERATOR Engine", "[BAE]"), "generator")
ok(match("headlights", "LAMP Headlamp Park And Turn", "Right") and not match("headlights", "LAMP Front Fog"), "headlamp vs fog")
ok(match("side-mirrors", "MIRROR Outside, Rearview, Electric, Heated") and not match("side-mirrors", "GLASS Mirror Replacement"), "mirror")
ok(match("fuel-pump-module", "MODULE KIT Fuel Pump/Level Unit"), "pump module")
ok(not match("liftgate", "PANEL Liftgate Opening"), "liftgate opening panel is body structure")
ok(match("window-switch", "SWITCH Power Window", "10 gang [JP5]") and not match("window-switch", "SWITCH Power Window", "Right"), "switch")
m = T._mapping(P.CFG, "Dodge", "Ram 1500", 2002)
ok(m.slugs == "ram_1500" and T._mapping(P.CFG, "Dodge", "Ram 1500", 2012).make == "ram"
   and T._mapping(P.CFG, "Dodge", "Ram 1500", 1990).slugs == ["d150", "w150"], "ram by year")
ok(T._side("Right") == "R" and T._side("Driver Side") == "L" and T._side("Passenger Side/Driver Side") is None, "side")


def sub(cat, tail):
    """Does the category select this parts-list page slug (last URL segment)?"""
    rx, ex = P.SUBCATS.get(cat), P.SUBCAT_EXCL.get(cat)
    return bool(rx and not T.SUBCAT_COMMON_EXCLUDE.search(tail) and re.search(rx, tail, re.I)
                and not (ex and re.search(ex, tail, re.I)))


# regressions from the 2026-11-05 audit (AUDIT.md), pages seen on the site
ok(not match("headlights", "LAMP Headlamp Park And Turn", "Light Bulb Kit (Assorted Bulbs and Fuses)")
   and not match("tail-lights", "LAMP Tail Stop Turn", "Light Bulb Kit (Assorted Bulbs and Fuses)")
   and match("tail-lights", "LAMP Tail Stop Turn", "Left"), "LBK13001 bulb kit is not a lamp")
ok(not match("trunk-lid", "PANEL Deck Lid Opening") and match("trunk-lid", "DECKLID"), "5065744AD deck lid opening panel")
ok(not match("hood", "HOOD KIT Vehicle") and match("hood", "HOOD") and not match("grille", "GRILLE KIT")
   and match("grille", "GRILLE Radiator"), "82211065AD accessory hood kit")
ok(sub("door-front", "door_front_shell_hinges") and sub("door-rear", "door_rear_shell_hinges")
   and sub("door-front", "front_door_shell_hinges"), "2002 Ram / 2006 300 door shell pages")
ok(sub("fender", "front_fenders_shields") and sub("fender", "front_fender"), "2015 200 fender page")
ok(sub("ignition-coils", "spark_plugs_cables_coils") and sub("ignition-coils", "spark_plugs_ignition_coil")
   and not sub("ignition-coils", "a_c_compressor"), "2006 300 coil page")
ok(sub("liftgate", "decklid_liftgate_panel") and not sub("liftgate", "switches_doors_decklid_liftgate")
   and sub("trunk-lid", "decklid_liftgate_panel"), "300/Magnum decklid_liftgate_panel")
pure = n

if not _pg_cacheonly.have([MODEL, YEAR, MIRRORS, LAMPS, ALT, P_HEAD, P_MIRROR, P_STARTER]):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

cats = P.categories_for("Dodge", "Grand Caravan", 2010, ["headlights", "side-mirrors", "alternator"])
ok(cats == {"headlights": [LAMPS], "side-mirrors": [MIRRORS], "alternator": [ALT]}, f"nav {cats}")
alts = [p["pn"] for p in P.parts_on_page(ALT, "alternator")]
ok("4727865AB" in alts and "R4727865AB" not in alts and "RL801304AC" not in alts, f"reman/core-return dropped {alts}")
heads = P.parts_on_page(LAMPS, "headlights")
ok([(p["pn"], p["list_info"][0]) for p in heads] == [("5113332AD", "Right"), ("5113333AD", "Left")], f"headlamps {heads}")
mirrors = [p["pn"] for p in P.parts_on_page(MIRRORS, "side-mirrors")]
ok(len(mirrors) == 80 and "68026176AB" not in mirrors and "1BR42DX9AC" not in mirrors, f"mirrors {len(mirrors)}")

h = P.product(P_HEAD)
ok(h["position"] == "Right" and h["flags"] == [] and "Position: Passenger Side" in h["evidence_lines"], f"head side {h['position']}")
ok(h["replaces"] == ["5113332AB", "5113332AC"] and h["fitment"][0]["years"] == [2008, 2010]
   and h["fitment"][0]["trims"] == ["C/V", "Crew", "Hero", "SE", "SXT"], "head fitment")
mi = P.product(P_MIRROR)
ok(mi["position"] is None and mi["flags"] == ["position conflict: parts list says 'Right', product page says 'Driver Side'"], f"conflict {mi['flags']}")
ok({f["model"] for f in mi["fitment"]} == {"Grand Caravan", "Town & Country"}, "mirror shared by GC and T&C")
st = P.product(P_STARTER)
ok(st["replaced_by"] == "R6027702AC" and len(st["fitment"]) == 7, "starter")
ok(st["fitment"][0]["raw"].startswith("2000-2003 Dodge Dakota | 6 Cyl 3.9L, 8 Cyl 4.7L, 8 Cyl 5.9L | Club Cab 2WD"), "raw row")
ok(any(f["model"] == "Ram 1500" and f["years"] == [1999, 2003] for f in st["fitment"]), "ram row")
print(f"OK {n} checks ({pure} pure)")
