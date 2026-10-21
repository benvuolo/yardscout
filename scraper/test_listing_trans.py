#!/usr/bin/env python3
"""Tests for listing-sourced transmission capture + provenance.

Covers:
  1. _normalize_listing_trans — yard shorthand -> VIN-decode display format,
     with unknowns returning "" (never guessed).
  2. output_json — transSrc provenance: "listing" beats the vpic fallback,
     "vin" when only the decode knows, "" when nobody does.
  3. compact_inventory_v2 — the extras shard carries [photo, color, engine,
     trans, transSrc] with the trailing-empty trim never stranding transSrc.
  4. App-regex compatibility — every normalized value must behave correctly
     under the exact /manual/i, /automated/i, /automatic/i checks app.js uses.

Run:  python3 scraper/test_listing_trans.py
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js

failures = []


def check(name, cond, detail=""):
    print(("  ok  " if cond else "  FAIL") + f" {name}" + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        failures.append(name)


# ---- 1. normalizer ----------------------------------------------------------
CASES = {
    "MANUAL 5SP": "5-spd Manual",
    "MANUAL": "Manual",
    "AUTO 4SP": "4-spd Automatic",
    "AUTO 6SP": "6-spd Automatic",
    "AUTO": "Automatic",
    "AUTO CVT": "Automatic (CVT)",
    "UNKNOWN": "",
    "": "",
    "  ": "",
    "N/A": "",
    "manual 5sp": "5-spd Manual",     # case-insensitive
    "5 SPEED MANUAL": "5-spd Manual",
    "GLITTER": "",                     # unparseable -> unknown, not guessed
}
for raw, want in CASES.items():
    got = js._normalize_listing_trans(raw)
    check(f"normalize {raw!r} -> {want!r}", got == want, f"got {got!r}")

# ---- 2. output_json provenance ---------------------------------------------
def mk(vid, **kw):
    base = {"id": vid, "vin": "", "year": 2005, "make": "Honda", "model": "Civic",
            "row": "1", "dateAdded": "2026-10-01", "_location": "Test Yard",
            "_city": "Testville", "_state": "UT", "_lat": 40.0, "_lng": -111.0}
    base.update(kw)
    return base

vehicles = [
    mk("t-listing", _trans="5-spd Manual",
       _vpic={"transmission": "6-spd Automatic", "trim": "", "series": "",
              "driveType": "", "trimQuality": "", "bodyClass": "", "engine": "",
              "modelYear": "", "make": "", "model": ""}),
    mk("t-vin", _vpic={"transmission": "Manual", "trim": "", "series": "",
                       "driveType": "", "trimQuality": "", "bodyClass": "",
                       "engine": "", "modelYear": "", "make": "", "model": ""}),
    mk("t-none"),
]
entries = {e["id"]: e for e in js.output_json(vehicles, only_matches=False)}
check("listing trans wins over vpic fallback",
      entries["t-listing"]["trans"] == "5-spd Manual")
check("listing provenance", entries["t-listing"]["transSrc"] == "listing")
check("vpic fallback trans", entries["t-vin"]["trans"] == "Manual")
check("vin provenance", entries["t-vin"]["transSrc"] == "vin")
check("no data -> empty trans", entries["t-none"]["trans"] == "")
check("no data -> empty provenance", entries["t-none"]["transSrc"] == "")

# ---- 3. compact extras shard ------------------------------------------------
payload = js.compact_inventory_v2(list(entries.values()))
extras = payload["_extras"]
ex_listing = extras.get("t-listing")
check("extras row exists for trans-bearing car", ex_listing is not None)
check("extras trans at index 3", ex_listing and ex_listing[3] == "5-spd Manual")
check("extras transSrc at index 4", ex_listing and len(ex_listing) == 5 and ex_listing[4] == "listing")
ex_vin = extras.get("t-vin")
check("vin-sourced extras transSrc", ex_vin and len(ex_vin) == 5 and ex_vin[4] == "vin")
check("car with no enrichment gets no extras row", "t-none" not in extras)

# ---- 4. app.js regex compatibility ------------------------------------------
# Mirror the exact checks in docs/app.js: isConfirmedManual and confirmedAuto.
def is_confirmed_manual(t):
    return bool(re.search(r"manual", t, re.I)) and not re.search(r"automated", t, re.I)

def confirmed_auto(t):
    return bool(re.search(r"automatic", t, re.I)) and not re.search(r"manual", t, re.I)

for raw, norm in CASES.items():
    if not norm:
        continue
    if "Manual" in norm:
        check(f"app sees {norm!r} as manual", is_confirmed_manual(norm) and not confirmed_auto(norm))
    else:
        check(f"app sees {norm!r} as automatic", confirmed_auto(norm) and not is_confirmed_manual(norm))
# vPIC's automated-manual strings must never count as manual (pre-existing rule).
check("AMT is not manual", not is_confirmed_manual("6-spd Automated Manual Transmission (AMT)"))

print()
if failures:
    print(f"{len(failures)} FAILURE(S): {failures}")
    sys.exit(1)
print("all listing-trans tests passed")
