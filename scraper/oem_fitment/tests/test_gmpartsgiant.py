#!/usr/bin/env python3
"""Offline test for sites/gmpartsgiant.py (PartsGiant ".html" template).
Pure rule checks always run; page checks read the fetch.py cache only and are
skipped when it is absent. Run: python3 scraper/oem_fitment/tests/test_gmpartsgiant.py"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _pg_cacheonly  # noqa: E402

_pg_cacheonly.install()
from sites import gmpartsgiant as G  # noqa: E402
from sites import _partsgiant as T  # noqa: E402

B = "https://www.gmpartsgiant.com"
MODEL = f"{B}/chevrolet-malibu-parts.html"
YEAR = f"{B}/2012-chevrolet-malibu-parts.html"
L = f"{B}/parts-list/2012-chevrolet-malibu"
STARTER = f"{L}/starter_generator_ignition_electrical_lamps/starter_motor_and_mounting.html"
DOORS = f"{L}/windshield_wiper_mirrors_instrument_panel_console_doors/door_hardware_front.html"
MIRRORS = f"{L}/windshield_wiper_mirrors_instrument_panel_console_doors/mirror_rear_view.html"
LAMPS = f"{L}/starter_generator_ignition_electrical_lamps/lamps_front.html"
P_STARTER = f"{B}/parts/gm-starter-12645298.html"      # 19 rows, View More, Replaced By + Replaces
P_GEN = f"{B}/parts/gm-generator-15755900.html"        # "2002, 1999-2000 Chevrolet Silverado"
P_HEAD = f"{B}/parts/gm-headlamp-19433006.html"        # one model, side only on the list page

n = 0


def ok(cond, msg):
    global n
    n += 1
    if not cond:
        raise AssertionError(msg)


def row(group, main, remark="", info=""):
    return f"{group} | {main} | {remark} | {info}"


def match(cat, group, main, remark="", info=""):
    inc, exc_head, exc_full = (tuple(G.PARTS[cat]) + (None, None))[:3]
    head = f"{group} | {main} | {remark.split('(')[0]}"
    text = row(group, main, remark, info)
    return bool(re.search(inc, text, re.I) and not (exc_head and re.search(exc_head, head, re.I))
                and not (exc_full and re.search(exc_full, text, re.I)))


# ---- pure rule checks
ok(match("alternator", "GENERATOR, Engine Electrical", "GENERATOR, Engine Electrical", "GENERATOR"), "generator")
ok(not match("alternator", "PULLEY, Fan and Coolant Pump", "PULLEY", "PULLEY,BELT IDLER"), "pulley")
ok(match("side-mirrors", "MIRROR, Inside/Outside Rear View", "MIRROR", "OUTSIDE REAR VIEW(INCLUDES 1,2,4,7)(BLACK)"), "mirror assy")
ok(not match("side-mirrors", "MIRROR, Inside/Outside Rear View", "MIRROR", "OUTSIDE REAR VIEW (REFLECTOR GLASS & BACKING PLATE)(PART OF 3)"), "mirror glass")
ok(match("fuel-pump-module", "MODULE KIT, Fuel Tank Meter/Pump", "MODULE KIT, Fuel Tank Meter/Pump",
         "MODULE KIT,FUEL TANK FUEL PUMP (W/O FUEL LEVEL SENSOR)(INCLUDES 28,30)"), "pump module, note not excluded")
ok(not match("fuel-pump-module", "SENSOR KIT, Fuel Tank Meter/Pump", "SENSOR KIT", "SENSOR KIT,FUEL LEVEL(KAFUS)"), "level sensor")
ok(match("window-switch", "SWITCH, Door Window", "SWITCH", "FRONT SIDE DOOR WINDOW & REAR SIDE DOOR WINDOW", "Location: Driver Side"), "master")
ok(not match("window-switch", "SWITCH, Door Window", "SWITCH", "FRONT SIDE DOOR WINDOW", "Location: Passenger Side"), "passenger")
ok(match("tail-lights", "LAMP, Tail Lamp", "LAMP", "TAIL(INCLUDES 18,19)", "Location: Driver Side"), "tail")
ok(not match("tail-lights", "LAMP, Tail Lamp", "LAMP, Tail Lamp", "LAMP,HIGH MOUNT STOP(MATING CONNECT USE 12085535)"), "chmsl")
ok(not match("headlights", "LAMP, Capsule/Headlamp/Fog Lamp", "LAMP, Capsule/Headlamp/Fog Lamp", "LAMP,FRONT FOG(INCLUDES 11)"), "fog")
ok(re.search(G.MODELS[("Chevrolet", "Silverado 1500")].inc, "1500_4wd")
   and not re.search(G.MODELS[("Chevrolet", "Silverado 1500")].inc, "1500_classic_4wd")
   and not re.search(G.MODELS[("Chevrolet", "Silverado 1500")].inc, "1500_hd_4wd"), "silverado variants")
pure = n

if not _pg_cacheonly.have([MODEL, YEAR, STARTER, DOORS, MIRRORS, LAMPS, P_STARTER, P_GEN, P_HEAD]):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

# ---- navigation
cats = G.categories_for("Chevrolet", "Malibu", 2012, ["starter", "side-mirrors", "window-regulator", "headlights"])
ok(cats["starter"] == [STARTER], f"starter list {cats.get('starter')}")
ok(cats["side-mirrors"] == [MIRRORS], "mirror list")
ok(DOORS in cats["window-regulator"], "regulator list")
ok(not any("wiring_harness" in u for u in cats["headlights"]), "wiring pages excluded")

# ---- list pages
st = G.parts_on_page(STARTER, "starter")
ok([p["pn"] for p in st] == ["12645298", "12609317"], f"starters {st}")
ok(st[0]["list_info"] == ["Fitting Vehicle Options: Z(LY7)", "Replaced By: 12745819"], "list info")
ok(st[0]["product_url"] == P_STARTER, "product url")
mir = [p["pn"] for p in G.parts_on_page(MIRRORS, "side-mirrors")]
ok("20893752" in mir and "15902389" not in mir and "20893856" not in mir, f"mirrors {mir}")
reg = {p["pn"]: p for p in G.parts_on_page(DOORS, "window-regulator")}
ok({"20803610", "25943967", "25943968", "15781322", "15781323", "20915991"} <= set(reg), f"regulators {sorted(reg)}")
ok("22865520" not in reg and "23114169" not in reg, "lock / glass excluded")
heads = G.parts_on_page(LAMPS, "headlights")
ok(sorted(p["pn"] for p in heads) == ["19432243", "19433006"], f"headlamps {heads}")

# ---- product pages
p = G.product(P_STARTER)
ok(p["pn"] == "12645298" and p["description"] == "Starter; Starter, Starter Motor", "starter desc")
ok(p["replaced_by"] == "12745819" and p["replaces"] == ["12598756", "12601721"], "supersession")
ok(len(p["fitment"]) == 19, f"19 rows (10 shown + View More): {len(p['fitment'])}")
f0 = p["fitment"][0]
ok(f0["years"] == [2010, 2015] and f0["make"] == "Buick" and f0["model"] == "Allure"
   and f0["engines"] == ["6 Cyl 3.0L", "6 Cyl 3.6L"] and f0["trims"][0] == "CX 4 DOOR SEDAN", f"row0 {f0}")
mal = [f for f in p["fitment"] if f["model"] == "Malibu"]
ok(len(mal) == 1 and mal[0]["years"] == [2008, 2012] and mal[0]["engines"] == ["6 Cyl 3.6L"], "malibu row")
ok(any(f["make"] == "Saturn" and f["model"] == "Vue" and f["years"] == [2008, 2010] for f in p["fitment"]), "vue row")
ok(p["evidence_lines"][:4] == ["Part Number: 12645298", "Part Description: Starter; Starter, Starter Motor",
                               "Replaced By: 12745819", "Replaces: 12598756, 12601721"], f"evidence head {p['evidence_lines'][:4]}")
ok(p["evidence_lines"][4] == "Year Make Model | Engine | Important vehicle option details", "evidence header")
ok(len(p["evidence_lines"]) == 5 + 19, "evidence rows")

g = G.product(P_GEN)
sil = [f for f in g["fitment"] if f["model"] == "Silverado"]
ok([f["years"] for f in sil] == [[2002, 2002], [1999, 2000]] and sil[0]["raw"] == sil[1]["raw"]
   and sil[0]["raw"].startswith("2002, 1999-2000 Chevrolet Silverado | "), f"multi-span {sil}")

T._LIST_POSITION.clear()
G.parts_on_page(LAMPS, "headlights")
h = G.product(P_HEAD)
ok(h["position"] == "Location: Driver Side", f"position from list {h['position']}")
ok(f"Parts list {LAMPS}: Location: Driver Side" in h["evidence_lines"], "position evidence")
ok([(f["years"], f["make"], f["model"]) for f in h["fitment"]] == [([2008, 2012], "Chevrolet", "Malibu")], "headlamp fitment")
ok(h["replaces"] == ["19432244", "22897127", "25872862", "25984638", "25950074"], "headlamp replaces")
print(f"OK {n} checks ({pure} pure)")
