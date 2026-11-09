#!/usr/bin/env python3
"""Offline tests for aftermarket/spectrapremium.py (no network).

    python3 scraper/oem_fitment/aftermarket/tests/test_spectrapremium.py

Fixtures: trimmed copies (scripts, styles, footer, year list removed) of real
pages retrieved 2026-11-09 during the probe.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import spectrapremium as sp  # noqa: E402
import run  # noqa: E402

FIX = HERE / "fixtures"
fails = checks = 0


def ok(cond: bool, msg: str) -> None:
    global fails, checks
    checks += 1
    if not cond:
        fails += 1
        print("FAIL", msg)


# vehicle page
V = sp.vehicle_url("23745")
r = sp.parse_vehicle_page(V, (FIX / "spectra_vehicle_23745_2012_civic_lx.html").read_text())
ok((r["year"], r["make"], r["model"], r["submodel"]) == (2012, "Honda", "Civic", "LX L4 1.8L"), f"vehicle {r}")
ok(r["motorization"].get("Eng. Desg.") == "R18Z1" and r["motorization"].get("Fuel") == "GAS", "motorization")
ok(r["count"] == [1, 20, 20] and len(r["cards"]) == 20 and r["next"] is None, "card count / pagination")
by = {c["pn"]: c for c in r["cards"]}
ok(by["CU13221"]["line"] == "Automotive Radiator" and by["CU13221"]["note"] == "USA Built; Canadian Built", "radiator note")
ok(by["CU13257"]["note"] == "Japan Built", "second radiator note")
ok(by["0210128"]["note"].startswith("Body Type: Coupe;"), "body note")
ok(by["98131"]["note"] == "" and by["98131"]["line"] == "Heater", "empty note")
ok(by["SP8965M"]["note"].startswith("with California Emissions System"), "emissions note")
ok(by["CU13221"]["specs"].get("Core Width") == "26.125 in", "specs")
ok(r["flags"] == [], f"flags {r['flags']}")

# product() merges pages and checks the count
sp.get = lambda u: {"status": 200, "retrieved": "2026-11-09T20:00:00Z",
                    "html": (FIX / "spectra_vehicle_23745_2012_civic_lx.html").read_text()}
rec = sp.product(V, "vehicle")
ok(rec["vehicle_id"] == "23745" and len(rec["cards"]) == 20 and rec["flags"] == [], "product record")

# listing: models -> only worklist models; submodels -> vehicle pages / motorizations
sp._TARGETS = {(2012, "Honda"): {"civic": 900.0, "crv": 10.0}}
li = sp.parse_listing(sp.models_url(2012, "Honda"), (FIX / "spectra_models_2012_honda.json").read_text())
ok(len(li["children"]) == 2 and all("get-submodels.json" in c for c in li["children"]), f"models {li}")
ok(any("model=CR-V" in c for c in li["children"]), "CR-V matched by normalized name only")
li = sp.parse_listing(sp.submodels_url(2012, "Honda", "Civic") + "&_score=900",
                      (FIX / "spectra_submodels_2012_honda_civic.json").read_text())
ok(len(li["products"]) == 11 and sp.vehicle_url("23745") in li["products"], "submodels -> vehicles")
li = sp.parse_listing(sp.submodels_url(2012, "Honda", "Accord") + "&_score=5",
                      '[{"vehiculeIds":"1,2","submodel":"EX"}]')
ok(li["children"] and "get-motorizations.json?vehiculeIds=1,2" in li["children"][0], "comma ids -> motorizations")
ok(sp.fetch_url(li["children"][0]).endswith("vehiculeIds=1,2"), "private _score stripped before fetch")
li = sp.parse_listing(li["children"][0], '[{"vehicule_id":7},{"vehicule_id":8}]')
ok(li["products"] == [sp.vehicle_url("7"), sp.vehicle_url("8")], "motorizations -> vehicles")
root = sp.parse_listing(sp.BASE + "/en", "")
ok(root["children"] == [sp.models_url(2012, "Honda")], "root -> worklist (year, make)")
ok(sp.score(sp.models_url(2012, "Honda")) > sp.score(sp.submodels_url(2012, "Honda", "Civic") + "&_score=900"),
   "a (year, make) page just outranks its best model's submodel page")
ok(sp.score(sp.submodels_url(2012, "Honda", "Civic") + "&_score=900") > sp.score(sp.models_url(2099, "Nobody")),
   "a valuable submodel page outranks a low-value (year, make) page (depth-first by value)")

# run.py maps the domain to this module
ok(run.module_for("ecat.spectrapremium.com") is sp, "run.module_for")

print(f"{checks - fails}/{checks} checks passed")
sys.exit(1 if fails else 0)
