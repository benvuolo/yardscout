#!/usr/bin/env python3
"""Offline test for sites/hondapartsnow.py (PartsGiant ".html" template, Honda
rules in sites/_honda_names.py). Pure rule checks always run; page checks read
the fetch.py cache only and are skipped when it is absent.
Run: python3 scraper/oem_fitment/tests/test_hondapartsnow.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _pg_cacheonly  # noqa: E402

_pg_cacheonly.install()
from sites import _honda_names as H  # noqa: E402
from sites import hondapartsnow as HN  # noqa: E402

B = "https://www.hondapartsnow.com"
MODEL = f"{B}/honda-accord-parts.html"
YEAR = f"{B}/2008-honda-accord-parts.html"
LX = f"{B}/2008-honda-accord--4dr_lx-ka_5at-parts.html"
V6 = f"{B}/2008-honda-accord--4dr_exl_v6_navi-ka_5at-parts.html"
L = f"{B}/parts-list/2008-honda-accord--4dr_lx-ka_5at"
ALT = f"{L}/engine/alternator_denso_l4.html"            # new + reman (RMD) rows
REG = f"{L}/body_air_conditioning/front_door_glass_regulator.html"
PS = f"{L}/engine/p_s_pump_l4.html"                     # "Steering" must not hit exclusion "ring"
P_ALT = f"{B}/genuine/honda~alternator~assy~31100-r40-a01.html"   # 2008-2012 Accord, one row per year
P_RAD = f"{B}/genuine/honda~radiator~19010-r40-a52.html"          # Replaced By
P_COIL = f"{B}/genuine/honda~coil~plug~hole~30520-r70-s01.html"   # Accord + Crosstour + Odyssey, Replaces

n = 0


def ok(cond, msg):
    global n
    n += 1
    if not cond:
        raise AssertionError(msg)


m = H.matches
ok(m("alternator", "Alternator Assy. (CSF89) (DENSO)") and not m("alternator", "Holder Assy., Brush"), "alternator")
ok(m("ac-compressor", "Compressor, A/C (RMD) (DENSO) (INCLUDES CLUTCH & COIL)") and not m("ac-compressor", "Clutch Set"), "compressor incl. note")
ok(m("headlights", "[Freight Parts] Headlight Assy., R.") and not m("headlights", "Bracket Kit, R. Headlight Mounting (A) (SERVICE)"), "headlight")
ok(m("tail-lights", "Lamp Unit, R.") and m("tail-lights", "Taillight Assy., L.") and not m("tail-lights", "Lamp, R.")
   and not m("tail-lights", "Lamp Unit *G38L* (JADE GREEN)"), "tail light vs trunk/high-mount lamps")
ok(m("side-mirrors", "Mirror Assy., R. (R1400) (R.C.)") and not m("side-mirrors", "Mirror Assy., Rearview (DAY/NIGHT)")
   and not m("side-mirrors", "Mirror, R. (R1400)"), "door mirror vs rearview / glass")
ok(m("window-switch", "Switch Assy., Power Window Master") and not m("window-switch", "Switch Assy., Power Window Passenger"), "master switch")
ok(m("window-regulator", "Regulator Assy., R. FR. Door (MANUAL)") and not m("window-regulator", "Handle Assy., Regulator *YR169L*"), "regulator")
ok(m("power-steering-pump", "Pump Assy., Power Steering (L4)") and not m("power-steering-pump", "Pulley, Power Steering Pump"), "ps pump")
ok(m("ignition-coils", "Coil, Plug Hole") and "Plug" not in H.head({"main": "Coil, Plug Hole"}), "coil kept past COMMON_EXCLUDE")
ok(m("fender", "Fender, R. FR. (DOT)") and not m("fender", "Fender, R. FR. (INNER)"), "fender vs inner fender")
ok(m("bumper-front", "[Freight Parts] Face, FR. Bumper (DOT)") and not m("bumper-front", "Spoiler, FR. Bumper Lip"), "bumper")
ok(m("grille", "Grille, FR.") and not m("grille", "Base, FR. Grille *B92P*"), "grille")
ok(H.is_reman("06311-R40-505RM", "Alternator, Core Id (104210-5890) (RMD)") and not H.is_reman("31100-R40-A01", "Alternator Assy."), "reman")
ok(H.pick_trims(["2dr_lx-ka_5at", "4dr_lx-ka_5at", "4dr_lx-kl_5mt", "4dr_exl_v6_navi-ka_5at", "4dr_gx-ka_5at",
                 "4dr_mx_hybrid-ka_cvt", "4dr_ex_l_pzev-kl_5at"], want_hybrid=False) == ["4dr_lx-ka_5at", "4dr_exl_v6_navi-ka_5at"], "trims")
ok(H.pick_trims(["4dr_lx-ka_5at", "4dr_mx_hybrid-ka_cvt", "4dr_mx_hybrid_navi-ka_cvt"], want_hybrid=True)
   == ["4dr_mx_hybrid-ka_cvt", "4dr_mx_hybrid_navi-ka_cvt"], "hybrid trims")
pure = n

if not _pg_cacheonly.have([MODEL, YEAR, LX, V6, ALT, REG, PS, P_ALT, P_RAD, P_COIL]):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

cats = HN.categories_for("Honda", "Accord", 2008, ["alternator", "window-regulator", "liftgate", "tailgate"])
ok(ALT in cats["alternator"] and any("4dr_exl_v6_navi-ka_5at" in u for u in cats["alternator"]), f"nav {cats}")
ok(REG in cats["window-regulator"] and "liftgate" not in cats and "tailgate" not in cats, "regulator pages, no gate on a sedan")
alt = HN.parts_on_page(ALT, "alternator")
ok([p["pn"] for p in alt] == ["31100-R40-A01"] and alt[0]["name"] == "Alternator Assy. (CSF89) (DENSO)", f"reman dropped {alt}")
ok([p["pn"] for p in HN.parts_on_page(REG, "window-regulator")] == ["72210-TA0-A02", "72250-TA0-A12"], "regulators")
ok([p["pn"] for p in HN.parts_on_page(PS, "power-steering-pump")] == ["56100-R40-P05", "56100-R40-315"], "ps pumps (RMD dropped)")

a = HN.product(P_ALT)
ok(a["pn"] == "31100-R40-A01" and a["description"] == "Alternator" and a["position"] is None and a["flags"] == [], "alt fields")
ok([f["years"] for f in a["fitment"]] == [[2012, 2012], [2011, 2011], [2010, 2010], [2009, 2009], [2008, 2008]]
   and {f["model"] for f in a["fitment"]} == {"Accord"}, "one row per year")
f8 = a["fitment"][-1]
ok(f8["trims"] == ["2 Door EX", "2 Door EX-L", "2 Door LX", "4 Door EX", "4 Door EX (PZEV)", "4 Door EX-L",
                   "4 Door EX-L (PZEV)", "4 Door LX", "4 Door LX (PZEV)"]
   and f8["options"] == ["KA 5AT", "KA 5MT", "KL 5AT", "KL 5MT"] and f8["engines"] == [], "Body & Trim / Emission & Transmission")
ok(a["evidence_lines"][2] == "Year Make Model | Body & Trim | Emission & Transmission"
   and a["evidence_lines"][-1] == f8["raw"], "evidence")
r = HN.product(P_RAD)
ok(r["replaced_by"] == "19010-R40-305" and "Replaced By: 19010-R40-305" in r["evidence_lines"], "replaced by")
c = HN.product(P_COIL)
ok(c["replaces"] == ["30520-R70-A01"] and [m_ for m_ in dict.fromkeys(f["model"] for f in c["fitment"])] == ["Accord", "Crosstour", "Odyssey"], "multi-model")
ok(c["fitment"][0]["raw"] == "2012 Honda Accord | 2 Door EX-L V6, 4 Door EX-L V6, 4 Door EX-V6 | KA 5AT, KA 6MT", "raw row")
print(f"OK {n} checks ({pure} pure)")
