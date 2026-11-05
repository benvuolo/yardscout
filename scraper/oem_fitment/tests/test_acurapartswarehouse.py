#!/usr/bin/env python3
"""Offline test for sites/acurapartswarehouse.py (PartsGiant ".html" template,
Honda-family rules in sites/_honda_names.py). Pure rule checks always run;
page checks read the fetch.py cache only and are skipped when it is absent.
Run: python3 scraper/oem_fitment/tests/test_acurapartswarehouse.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _pg_cacheonly  # noqa: E402

_pg_cacheonly.install()
from sites import _honda_names as H  # noqa: E402
from sites import acurapartswarehouse as A  # noqa: E402

B = "https://www.acurapartswarehouse.com"
MODEL = f"{B}/acura-tl-parts.html"
YEAR = f"{B}/2005-acura-tl-parts.html"
BASE = f"{B}/2005-acura-tl--4dr_base-ka5at-parts.html"
NAVI = f"{B}/2005-acura-tl--4dr_base_navigation-ka5at-parts.html"
L = f"{B}/parts-list/2005-acura-tl--4dr_base-ka5at"
REG = f"{L}/body_air_conditioning/front_door_glass_door_regulator.html"   # "Regulator, R FR"
TAIL = f"{L}/electrical_exhaust_heater_fuel/taillight_license_light.html"  # "Lamp Unit, R." among marker/stop lamps
P_ALT = f"{B}/oem/acura~alternator~assy~csd69~denso~31100-rja-a02.html"  # MDX + RL + TL, Replaces x3
P_REG = f"{B}/oem/acura~regulator~r~fr~72210-sep-305.html"               # Position line, 2004-2008 TL

n = 0


def ok(cond, msg):
    global n
    n += 1
    if not cond:
        raise AssertionError(msg)


m = H.matches
ok(m("window-regulator", "Regulator, R FR") and m("window-regulator", "Regulator Assy., L. RR. Door Power"), "acura regulator names")
ok(m("fender", "Panel Set, R. FR. Fender (DOT)") and not m("fender", "Fairing, R. FR. Fender")
   and not m("fender", "Fender Assy., R. FR. (INNER)"), "fender panel set")
ok(m("climate-control", "Control Assy., Auto Air Conditioner") and not m("climate-control", "Control Assy., RR. Heater")
   and not m("climate-control", "Computer Assy., Auto Air Conditioner"), "front HVAC control only")
ok(not m("tail-lights", "Led Unit, R.") and not m("tail-lights", "Light Assy., R. RR. Side Marker")
   and not m("tail-lights", "Light Assy., High Mount Stop"), "tail-light exclusions")
ok(m("side-mirrors", "Mirror Assy., R. Door *B92P* (HEATED) (NIGHTHAWK BLACK PEARL)")
   and not m("side-mirrors", "Mirror Assy., Rearview *TBLACK* (AUTO DAY/NIGHT) (BLACK)"), "mirrors")
ok(H.pick_trims(["4dr_rl-ka5at", "4dr_rl_alaska-ka5at", "4dr_rl_hawaii-ka5at"], want_hybrid=False) == ["4dr_rl-ka5at"], "RL regional trims")
ok(H.pick_trims(["4dr_base-ka5at", "4dr_base_navigation-ka5at", "4dr_sport-ka6mt"], want_hybrid=False)
   == ["4dr_base-ka5at", "4dr_base_navigation-ka5at"], "acura slug form, automatic first")
pure = n

if not _pg_cacheonly.have([MODEL, YEAR, BASE, NAVI, REG, TAIL, P_ALT, P_REG]):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

cats = A.categories_for("Acura", "TL", 2005, ["window-regulator", "tail-lights"])
ok(REG in cats["window-regulator"] and TAIL in cats["tail-lights"], f"nav {cats}")
ok([p["pn"] for p in A.parts_on_page(REG, "window-regulator")] == ["72210-SEP-305", "72250-SEP-305"], "front regulators")
ok([p["pn"] for p in A.parts_on_page(TAIL, "tail-lights")] == ["33501-SEP-A01", "33551-SEP-A01"], "tail lamps")

a = A.product(P_ALT)
ok(a["pn"] == "31100-RJA-A02" and a["replaces"] == ["31100-RDJ-A01", "31100-RJA-A01", "31100-RGL-A01"] and a["flags"] == [], "alt fields")
ok(list(dict.fromkeys(f["model"] for f in a["fitment"])) == ["MDX", "RL", "TL"], "multi-model")
ok([f["years"] for f in a["fitment"] if f["model"] == "TL"] == [[2008, 2008], [2007, 2007], [2006, 2006], [2005, 2005], [2004, 2004]], "TL years")
tl05 = [f for f in a["fitment"] if f["model"] == "TL" and f["years"] == [2005, 2005]][0]
ok(tl05["trims"] == ["4 Door Base", "4 Door Sport"] and tl05["options"] == ["KA 5AT", "KA 6MT"]
   and tl05["raw"] == "2005 Acura TL | 4 Door Base, 4 Door Sport | KA 5AT, KA 6MT", "row cells")
ok("Replaces: 31100-RDJ-A01, 31100-RJA-A01, 31100-RGL-A01" in a["evidence_lines"], "evidence replaces")
r = A.product(P_REG)
ok(r["position"] == "Passenger Side" and "Position: Passenger Side" in r["evidence_lines"]
   and r["replaces"] == ["72210-SEP-A02", "72210-SEP-A01"], f"position {r['position']}")
ok({f["model"] for f in r["fitment"]} == {"TL"} and len(r["fitment"]) == 5, "regulator rows")
print(f"OK {n} checks ({pure} pure)")
