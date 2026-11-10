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
ok(GS.classify("") == ("ok", ()), "empty note")
ok(GS.classify("Body Type: Sedan") == ("ok", (("body", "Sedan"),)), "body gate")
ok(GS.classify("Body Type: Coupe; Desiccant Kit; May Require Use Of Original Drier Plug") == ("ok", (("body", "Coupe"),)),
   "body + install clauses")
ok(GS.classify("New; with Clutch; Replacement of Stretch Fit Belt Required") == ("ok", ()), "compressor install")
ok(GS.classify("Ignition Coil Mounts to Cylinder Head; Qty Req.: 4") == ("ok", ()), "coil install")
ok(GS.classify("Failure to use the vehicle OEM approved sealing method will void the warranty.; "
               "Gasket And/Or Sealant Not Included") == ("ok", ()), "warranty install")
for n in ("USA Built; Canadian Built", "Japan Built", "with California Emissions System",
          "with Federal Emissions System; Failure To Replace The Fuel Tank Lock Ring And Seal Will Void Warranty",
          "with Manual Trans", "w/ Towing Package", "exc. Hybrid", "Body Type: Spaceship", "Some new wording"):
    ok(GS.classify(n)[0] == "refuse", f"refuse {n!r}")

ok(GS.classify("Contains 1 Units; Pack; Radiator Cap Is Required") == ("ok", ()), "packaging clauses")
ok(GS.classify("Transmission Control Type: Manual OR Transmission Control Type: Automatic") == ("ok", ()),
   "either transmission = no limit")
ok(GS.classify("Body Type: Standard Cab Pickup") == ("ok", (("body", "Standard Cab Pickup"),)), "cab style is a body gate")
ok(GS.classify("Services OE # 20824314") == ("ok", ()) and GS.oe_refs("Services OE # 20824314") == ["20824314"],
   "OE reference kept as data")
for n in ("Region: USA", "Light Duty", "Position: Front", "Drive Type: Quattro", "Transmission Control Type: Automatic",
          "with 28.25in x 17.25in x 1in Core", "Partial Zero Emissions Vehicle (PZEV)", "Body Num Doors: 4",
          "Mfr Body Code: CL32"):
    ok(GS.classify(n)[0] == "refuse", f"still refused {n!r}")

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
ok(g.get("am:spp:ac-condenser:7-3965", {}).get("apps") == [["Honda", "Civic", 2012, 2012, "1.8L 4-cyl", {"body": "Sedan"}]],
   "condenser sedan body-gated")
ok(g["am:spp:ac-condenser:7-3976"]["apps"][0][5] == {"body": "Coupe"}, "condenser coupe body-gated")
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
ok(doc["groups"] == [] and doc["summary"]["refused"].get("config_fuel:CNG") == 1 and doc["unmapped_models"],
   "CNG-only key gives no group; unmapped model reported")

# drive gate (hub 2026-11-09): mapped, never inferred
ok(GS.classify("Drive Type: AWD") == ("ok", (("drive", "awd"),)), "AWD -> drive gate")
ok(GS.classify("Drive Type: 4WD; Body Type: Crew Cab Pickup") == ("ok", (("body", "Crew Cab Pickup"), ("drive", "4wd"))),
   "drive + body")
ok(GS.classify("Drive Type: AWD; Drive Type: FWD")[0] == "refuse", "two drive clauses refused")
d2 = copy.deepcopy(base)
for c in d2["cards"]:
    if c["pn"] == "0610360":
        c["note"] = "Drive Type: AWD"
d2["cards"].append(dict(next(c for c in d2["cards"] if c["pn"] == "0610360"), pn="0610361", href_pn="0610361",
                        note="Drive Type: FWD"))
doc = GS.build([d2], names, "test")
g = {x["id"]: x for x in doc["groups"]}
ok(g["am:spp:ac-compressor:0610360"]["apps"][0][5] == {"drive": "awd"} and
   g["am:spp:ac-compressor:0610361"]["apps"][0][5] == {"drive": "fwd"} and
   "drivetrain" in g["am:spp:ac-compressor:0610360"]["note"], "AWD/FWD units split by drive gate")
d3 = copy.deepcopy(d2)
for c in d3["cards"]:
    if c["pn"] == "0610361":
        c["note"] = ""
doc = GS.build([d3], names, "test")
ok(not any(x["cat"] == "ac-compressor" for x in doc["groups"]), "one drive-gated + one ungated unit -> ambiguous, dropped")
d4 = copy.deepcopy(d2)
for c in d4["cards"]:
    if c["pn"] == "0610361":
        c["note"] = "Body Type: Sedan"
doc = GS.build([d4], names, "test")
ok(not any(x["cat"] == "ac-compressor" for x in doc["groups"]), "units gated on different dimensions -> dropped")

# FLEX (hub 2026-11-09): non-fuel lines only, and only beside the same GAS unit
def clean_fuel(rec):
    rec = copy.deepcopy(rec)
    rec["cards"] = [c for c in rec["cards"] if c["pn"] != "SP8965M"]
    for c in rec["cards"]:
        if c["pn"] == "SP8054M":
            c["note"] = ""
    return rec


base_f = clean_fuel(base)
ok("am:spp:fuel-pump-module:SP8054M" in {x["id"] for x in GS.build([base_f], names, "t")["groups"]},
   "clean GAS-only fuel module key gives a group (control)")
flex = copy.deepcopy(base)
flex.update(vehicle_id="77")
flex["motorization"]["Fuel"] = "FLEX"
doc = GS.build([base_f, clean_fuel(flex)], names, "test")
ids = {x["id"] for x in doc["groups"]}
ok("am:spp:ac-compressor:0610360" in ids and "am:spp:ignition-coils:C-900" in ids, "FLEX + same GAS unit kept")
ok(not any(x["cat"] == "fuel-pump-module" for x in doc["groups"]) and
   doc["summary"]["split_keys_dropped"].get("fuel-pump-module:non_gas_config_on_fuel_line") == 1,
   "fuel lines: a FLEX config of the key drops the key, even when the GAS config lists a unit")
doc = GS.build([flex], names, "test")
ok(doc["groups"] == [] and any("no_gas_config" in k for k in doc["summary"]["split_keys_dropped"]),
   "FLEX alone (no GAS config that year) -> dropped")
flex2 = copy.deepcopy(flex)
for c in flex2["cards"]:
    if c["pn"] == "C-900":
        c["pn"] = c["href_pn"] = "C-999"
doc = GS.build([base, flex2], names, "test")
ids = {x["id"] for x in doc["groups"]}
ok("am:spp:ignition-coils:C-900" not in ids and "am:spp:ignition-coils:C-999" not in ids,
   "FLEX and GAS on different units -> both refused for that year")
ok("am:spp:ac-compressor:0610360" in ids, "other lines of that year unaffected")
cng = copy.deepcopy(base)
cng["motorization"]["Fuel"] = "BI-FUEL"
ok(GS.build([cng], names, "t")["groups"] == [], "BI-FUEL-only key gives no group")

# §11.4 audit regression (2026-11-10): a hybrid config shares the gas car's key
hyb = copy.deepcopy(base)
hyb.update(vehicle_id="88", submodel="Hybrid L4 1.8L")
hyb["motorization"]["Fuel"] = "FULL HYBRID EV-GAS (FHEV)"
for c in hyb["cards"]:
    if c["pn"] == "TB1242":
        c["pn"] = c["href_pn"] = "TB1030"       # the hybrid takes a different throttle body
doc = GS.build([base, hyb], names, "test")
ids = {x["id"] for x in doc["groups"]}
ok("am:spp:throttle-body:TB1242" not in ids and "am:spp:throttle-body:TB1030" not in ids,
   "gas and hybrid configs on different units -> key dropped (Fusion 2014 case)")
ok("am:spp:ac-compressor:0610360" in ids, "lines where the hybrid config lists the same unit are kept")
hyb2 = copy.deepcopy(hyb)
hyb2["cards"] = [c for c in hyb2["cards"] if c["line"] != "Compressor"]
doc = GS.build([base, hyb2], names, "test")
ok("am:spp:ac-compressor:0610360" not in {x["id"] for x in doc["groups"]} and
   doc["summary"]["split_keys_dropped"].get("ac-compressor:config_without_line") == 1,
   "a config of the key with no unit in the line -> key dropped (Fusion Energi case)")
# Focus 2012 case: FLEX config on a different fuel module than GAS -> dropped (fuel line)
fx = copy.deepcopy(base_f)
fx.update(vehicle_id="99")
fx["motorization"]["Fuel"] = "FLEX"
for c in fx["cards"]:
    if c["pn"] == "SP8054M":
        c["pn"] = c["href_pn"] = "SP8999M"
doc = GS.build([base_f, fx], names, "test")
ok(not any(x["cat"] == "fuel-pump-module" for x in doc["groups"]), "FLEX config drops the fuel-module key")

print(f"{checks - fails}/{checks} checks passed")
sys.exit(1 if fails else 0)
