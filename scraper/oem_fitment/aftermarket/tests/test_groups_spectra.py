#!/usr/bin/env python3
"""Offline tests for aftermarket/groups_spectra.py.

    python3 scraper/oem_fitment/aftermarket/tests/test_groups_spectra.py
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import groups_spectra as GS  # noqa: E402
import groups_am as GA  # noqa: E402
import spectrapremium as sp  # noqa: E402

fails = checks = 0


def ok(cond, msg):
    global fails, checks
    checks += 1
    if not cond:
        fails += 1
        print("FAIL", msg)


# clause classification
ok(GS.classify("") == ("ok", "*"), "empty note")
ok(GS.classify("Body Type: Sedan") == ("ok", "Sedan"), "body gate")
ok(GS.classify("Body Type: Coupe; Desiccant Kit; May Require Use Of Original Drier Plug") == ("ok", "Coupe"),
   "body + install clauses")
ok(GS.classify("New; with Clutch; Replacement of Stretch Fit Belt Required") == ("ok", "*"), "compressor install")
ok(GS.classify("Ignition Coil Mounts to Cylinder Head; Qty Req.: 4") == ("ok", "*"), "coil install")
ok(GS.classify("Failure to use the vehicle OEM approved sealing method will void the warranty.; "
               "Gasket And/Or Sealant Not Included") == ("ok", "*"), "warranty install")
for n in ("USA Built; Canadian Built", "Japan Built", "with California Emissions System",
          "with Federal Emissions System; Failure To Replace The Fuel Tank Lock Ring And Seal Will Void Warranty",
          "with Manual Trans", "w/ Towing Package", "exc. Hybrid", "Body Type: Spaceship", "Some new wording"):
    ok(GS.classify(n)[0] == "refuse", f"refuse {n!r}")

# real vehicle page -> records
html = (HERE / "fixtures" / "spectra_vehicle_23745_2012_civic_lx.html").read_text()
sp.get = lambda u: {"status": 200, "retrieved": "2026-11-09T20:00:00Z", "html": html}
base = sp.product(sp.vehicle_url("23745"), "vehicle")
names = GA.Names({("Honda", "Civic"), ("Acura", "ILX")})
doc = GS.build([base], names, "test")
g = {gr["id"]: gr for gr in doc["groups"]}
ok("am:spp:radiator:CU13221" not in g and "am:spp:radiator:CU13257" not in g, "plant-noted radiators refused")
ok("am:spp:fuel-pump-module:SP8054M" not in g, "emissions-noted fuel modules refused")
ok(g.get("am:spp:ac-compressor:0610360", {}).get("apps") == [["Honda", "Civic", 2012, 2012, "1.8L 4-cyl"]],
   f"compressor group {g.get('am:spp:ac-compressor:0610360')}")
ok(g.get("am:spp:ac-condenser:7-3965", {}).get("apps") == [["Honda", "Civic", 2012, 2012, "1.8L 4-cyl", "Sedan"]],
   "condenser sedan body-gated")
ok(g["am:spp:ac-condenser:7-3976"]["apps"][0][5] == "Coupe", "condenser coupe body-gated")
ok(g["am:spp:ignition-coils:C-900"]["apps"][0][:4] == ["Honda", "Civic", 2012, 2012], "coil group")
ok(doc["summary"]["refused"].get("radiator:note") == 1, f"refused {doc['summary']['refused']}")
ok(all("<" not in x["note"] and "Spectra Premium" in x["note"] for x in doc["groups"]), "notes in our words")

# cross-model + consistency across submodels
ilx = copy.deepcopy(base)
ilx.update(vehicle_id="270016", make="Acura", model="ILX", year=2013, submodel="Base L4 2.4L")
ilx["cards"] = [c for c in ilx["cards"] if c["pn"] == "C-900"]
civ13 = copy.deepcopy(base)
civ13.update(vehicle_id="1", year=2013, submodel="Si L4 2.4L")
civ13["cards"] = [c for c in civ13["cards"] if c["pn"] == "C-900"]
doc = GS.build([base, ilx, civ13], names, "test")
coil = {x["id"]: x for x in doc["groups"]}["am:spp:ignition-coils:C-900"]
ok(coil["cross_model"] and len(coil["apps"]) == 3, f"cross-model coil {coil['apps']}")
# a second Civic 2012 1.8 submodel listing a DIFFERENT compressor -> key dropped
alt = copy.deepcopy(base)
alt.update(vehicle_id="2", submodel="EX L4 1.8L")
for c in alt["cards"]:
    if c["pn"] == "0610360":
        c["pn"] = c["href_pn"] = "0699999"
doc = GS.build([base, alt], names, "test")
ids = {x["id"] for x in doc["groups"]}
ok("am:spp:ac-compressor:0610360" not in ids and "am:spp:ac-compressor:0699999" not in ids, "trim split dropped")
ok(doc["summary"]["split_keys_dropped"].get("ac-compressor") == 1, "split counted")
# two units, no distinguishing note -> ambiguous
amb = copy.deepcopy(base)
amb["cards"].append(dict(next(c for c in amb["cards"] if c["pn"] == "C-900"), pn="C-901", href_pn="C-901"))
doc = GS.build([amb], names, "test")
ok(not any(x["cat"] == "ignition-coils" for x in doc["groups"]), "ambiguous coils dropped")
# non-gas fuel refused; unmapped model reported
cng = copy.deepcopy(base)
cng["motorization"]["Fuel"] = "CNG"
odd = copy.deepcopy(base)
odd.update(vehicle_id="9", model="Civic Del Sol Whatever")
doc = GS.build([cng, odd], names, "test")
ok(doc["groups"] == [] and doc["summary"]["refused"].get("fuel:CNG") == 1 and doc["unmapped_models"], "fuel/unmapped")

print(f"{checks - fails}/{checks} checks passed")
sys.exit(1 if fails else 0)
