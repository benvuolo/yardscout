#!/usr/bin/env python3
"""Offline test for sites/toyotapartsnow.py (SimplePart template).
Pure parser checks always run; page checks read the fetch.py cache only
(scraper/oem_fitment/cache, gitignored) and are skipped when it is absent.
Run: python3 scraper/oem_fitment/tests/test_toyotapartsnow.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _sp_cacheonly as _cacheonly  # noqa: E402

_cacheonly.install()
from sites import toyotapartsnow as T  # noqa: E402
from sites._simplepart import SimplePart, _strip_undefined, split_list  # noqa: E402

B = "https://www.toyotapartsnow.com"
YEAR = f"{B}/catalog/2009-toyota-camry-parts"
MIRRORS = f"{B}/parts-list/2009-toyota-camry/body-hardware/outside-mirrors"
ALT = f"{B}/parts-list/2009-toyota-camry/charging-starting/alternator"
TRUNK = f"{B}/parts-list/2009-toyota-camry/body-hardware/trunk-lid-components"
P_MIRROR = f"{B}/oem/toyota~mirror-assembly-outer-r~87910-06925"
P_REMAN = f"{B}/oem/toyota~reman-alternator~27060-0h111-84"
P_SUPERSEDED = f"{B}/oem/toyota~passenger-side-mirror-assembly-outside-rear-view~87910-33660-c0"

checks = 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        raise AssertionError(msg)


# ---- pure parser checks
ok(_strip_undefined('{"a":undefined,"b":"undefined","c":[undefined]}') == '{"a":null,"b":"undefined","c":[null]}', "undefined")
ok(split_list("Base (4WD, FWD), Latitude (4WD, FWD), Sport") == ["Base (4WD, FWD)", "Latitude (4WD, FWD)", "Sport"], "split")
ok(SimplePart.parse_ymm("2019-2025 Toyota RAV4") == {"years": [2019, 2025], "make": "Toyota", "model": "RAV4"}, "ymm span")
ok(SimplePart.parse_ymm("2009 Scion xB") == {"years": [2009, 2009], "make": "Scion", "model": "xB"}, "ymm single")
m = T._T.match
ok(m("side-mirrors", "Mirror Assembly", "Mirror Assembly Outer Rearview"), "mirror assy")
ok(not m("side-mirrors", "Mirror Glass", "Mirror Outer, Rear View"), "mirror glass excluded")
ok(not m("trunk-lid", "Trunk Lid", "Panel Sub-Assembly, Luggage Door Finish"), "trunk finish panel excluded")
ok(m("trunk-lid", "Panel Sub-Assy, Luggage Compartment Door", ""), "trunk lid")
ok(m("ac-compressor", "Compressor Assembly", "Compressor Assembly, With Pulley"), "with-qualifier kept")
ok(not m("ac-compressor", "Clutch Assembly", "Clutch Assy, Magnet"), "clutch excluded")
ok(not m("window-switch", "Switch Assy,  Power Window Regulator", ""), "non-master switch excluded")
ok(m("radiator", "Radiator Assembly", "Radiator Assembly, L/Cap"), "radiator less cap")
ok(T._T.year_url("Toyota", "Camry Solara", 2003) == f"{B}/catalog/2003-toyota-solara-parts", "slug map")
ok(T._T.year_url("Scion", "xB", 2005) == f"{B}/catalog/2005-scion-xb-parts", "scion url")
pure = checks

if not _cacheonly.have([YEAR, MIRRORS, ALT, TRUNK, P_MIRROR, P_REMAN, P_SUPERSEDED]):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

# ---- navigation
cats = T.categories_for("Toyota", "Camry", 2009, ["side-mirrors", "alternator", "window-regulator", "liftgate"])
ok(cats["side-mirrors"] == [MIRRORS], cats.get("side-mirrors"))
ok(cats["alternator"] == [ALT], cats.get("alternator"))
ok(len(cats["window-regulator"]) == 2, cats.get("window-regulator"))
ok("liftgate" not in cats, "sedan has no back door page")

# ---- list pages
mir = {p["pn"]: p for p in T.parts_on_page(MIRRORS, "side-mirrors")}
ok("87910-06925" in mir and "87940-06924" in mir, "mirror assemblies listed")
ok(not any(pn.startswith(("87961", "87931", "90467", "90178", "6749")) for pn in mir), "glass/clip/nut/garnish excluded")
ok(mir["87910-06925"]["product_url"] == P_MIRROR, mir["87910-06925"]["product_url"])
ok(mir["87910-06925"]["list_location"] == ["Passenger Side"], "location as printed")
ok(mir["87910-33660-C0"]["list_section"] == "other" and mir["87910-33660-C0"]["list_replaced_by"] == "87910-33670-C0", "catalog-only row")
alt = T.parts_on_page(ALT, "alternator")
ok(sorted(p["pn"] for p in alt) == ["27060-0H111-84", "27060-0P141-84", "27060-28321-84", "27060-31081-84"], [p["pn"] for p in alt])
ok(all(p["reman"] for p in alt), "only reman listed -> kept and flagged")
tr = [p["pn"] for p in T.parts_on_page(TRUNK, "trunk-lid")]
ok(tr and all(pn.startswith("64401-") for pn in tr), tr)

# ---- product pages
p = T.product(P_MIRROR)
ok(p["pn"] == "87910-06925" and p["position"] == "Rear Outer Passenger Side", p["position"])
ok(len(p["replaces"]) == 14 and p["replaces"][0] == "87910-06190-B2", p["replaces"])
ok(len(p["fitment"]) == 1, p["fitment"])
f = p["fitment"][0]
ok(f["years"] == [2007, 2011] and f["make"] == "Toyota" and f["model"] == "Camry", f)
ok(f["trims"] == ["Base", "CE", "Hybrid", "LE", "SE", "XLE"], f["trims"])
ok(f["engines"] == ["4 Cyl 2.4 L FULL HYBRID EV-GAS (FHEV)", "4 Cyl 2.4 L GAS", "4 Cyl 2.5 L GAS", "6 Cyl 3.5 L GAS"], f["engines"])
ok(p["evidence_lines"][:2] == ["Position", "Rear Outer Passenger Side"] and "2007-2011 Toyota Camry" in p["evidence_lines"], p["evidence_lines"])
ok("flags" not in p, p.get("flags"))

p = T.product(P_REMAN)  # multi-model, multi-year block
ok(p["replaces"] == ["27060-0H110", "27060-0H111"], p["replaces"])
rows = [(f["years"], f["model"]) for f in p["fitment"]]
ok(rows == [([2007, 2009], "Camry"), ([2009, 2010], "Corolla"), ([2009, 2013], "Matrix"), ([2007, 2008], "Solara")], rows)
ok(p["fitment"][1]["trims"] == ["XRS"] and p["fitment"][1]["raw"] == "2009-2010 Toyota Corolla | XRS | 4 Cyl 2.4 L GAS", p["fitment"][1])
ok("flags" not in p, p.get("flags"))

p = T.product(P_SUPERSEDED)  # catalog-style block: Engine + option details columns
ok(p["replaced_by"] == ["87910-33670-C0"] and p["replaces"] == [], p["replaced_by"])
f = p["fitment"][0]
ok(f["trims"] == [] and f["engines"] == ["2.4L L4", "2.5L L4", "3.5L V6"], f)
ok(f["other_columns"] == {"Important vehicle option details": "2ARFE, 2AZFE, 2AZFXE, 2GRFE; ACV40, AHV40, ASV40, GSV40"}, f)
ok("flags" not in p, p.get("flags"))

print(f"OK {checks} checks ({pure} pure, {checks - pure} on cached pages)")
