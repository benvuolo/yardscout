#!/usr/bin/env python3
"""2026-11 parts-gap curation: the model-specific rows for the most common
cars on the lots, and the body-style gate they introduced.

  1. Body gate: a part with "body": ["coupe"] is VIN-confirmed on a Coupe
     decode, excluded on a Sedan decode, listing-confirmed when the yard's
     own model text says Coupe, and "if equipped" with no decode.
  2. Nissan Altima: a 2008 sedan gets the L32 rows (ESCL, fuel pump, throttle
     body, A/C compressor, fan) and not the coupe lamps; 2017 gets the
     facelift headlights and not the generic pre-2016 row; 2014 the reverse;
     2004 gets the mechanical rows but no ESCL.
  3. Every curated row: 0 < cost < low < high and high <= 6x low (the same
     guard research_parts.py applies), and the gate lint stays clean.

Run:  python3 scraper/test_parts_gaps.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

failures = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        failures.append(name)


def parts(year, make, model, decode=None):
    out = {}
    for m in js.match_vehicle(year, make, model, vin_decode=decode):
        for p in m["top_parts"]:
            out[p["name"]] = p
    return out


SEDAN = {"trim": "", "series": "", "trimQuality": "empty", "bodyClass": "Sedan/Saloon", "driveType": "", "transmission": "CVT"}
COUPE = {**SEDAN, "bodyClass": "Coupe"}

# 1. body gate
p = parts(2010, "Nissan", "Altima", COUPE)
check("coupe decode: coupe tail lights VIN-confirmed", p.get("Coupe Tail Lights (pair, uncracked)", {}).get("trim_status") == "vin", str(p.get("Coupe Tail Lights (pair, uncracked)")))
p = parts(2010, "Nissan", "Altima", SEDAN)
check("sedan decode: coupe lamps excluded", not any(n.startswith("Coupe ") for n in p), str([n for n in p if n.startswith("Coupe ")]))
p = parts(2010, "Nissan", "Altima Coupe")
check("listing says Coupe, no decode: listing-confirmed", p.get("Coupe Headlights (pair, clear)", {}).get("trim_status") == "listing", str(p.get("Coupe Headlights (pair, clear)")))
p = parts(2010, "Nissan", "Altima")
check("no decode, plain listing: coupe lamps are 'if equipped'", p.get("Coupe Tail Lights (pair, uncracked)", {}).get("trim_status") == "unconfirmed", str(p.get("Coupe Tail Lights (pair, uncracked)")))
check("no decode: unconfirmed coupe lamps add $0 to the ranking value",
      max(m["max_value"] for m in js.match_vehicle(2010, "Nissan", "Altima")) == max(m["max_value"] for m in js.match_vehicle(2010, "Nissan", "Altima", vin_decode=SEDAN)))

# 2. Altima rows by year
p08 = parts(2008, "Nissan", "Altima", SEDAN)
for n in ("Electronic Steering Column Lock (ESCL)", "Fuel Pump Module (in-tank, test before listing)",
          "Electronic Throttle Body (match part #)", "A/C Compressor (clutch spins free)", "Radiator Fan Assembly (dual fan)"):
    check(f"2008: {n}", n in p08 and p08[n].get("trim_status") is None, str(p08.get(n)))
check("2008: ESCL fits the whole L32", p08["Electronic Steering Column Lock (ESCL)"]["fits"] == "2007–2012", p08["Electronic Steering Column Lock (ESCL)"]["fits"])
check("2008: Bose (option) still unconfirmed", p08.get("Bose Amp + Speakers", {}).get("trim_status") == "unconfirmed")
check("2008: no facelift or LED headlight rows", not any("LED" in n or "HID" in n for n in p08), str([n for n in p08 if "LED" in n or "HID" in n]))
p11 = parts(2011, "Nissan", "Altima", SEDAN)
check("2011: HID row present as an option", p11.get("HID Xenon Headlights (pair)", {}).get("trim_status") == "unconfirmed")
p17 = parts(2017, "Nissan", "Altima", SEDAN)
check("2017: facelift headlights, not the generic row", "Headlights w/ LED Signature (2016+ facelift, pair)" in p17 and "Headlights (clear, non-hazed)" not in p17, str([n for n in p17 if "eadlight" in n]))
p14 = parts(2014, "Nissan", "Altima", SEDAN)
check("2014: generic headlights, not the facelift row", "Headlights (clear, non-hazed)" in p14 and "Headlights w/ LED Signature (2016+ facelift, pair)" not in p14, str([n for n in p14 if "eadlight" in n]))
check("2014: no coupe rows (coupe ended 2013)", not any(n.startswith("Coupe ") for n in p14))
p04 = parts(2004, "Nissan", "Altima", SEDAN)
check("2004: mechanical rows yes, ESCL no", "Fuel Pump Module (in-tank, test before listing)" in p04 and "Electronic Steering Column Lock (ESCL)" not in p04)
check("2020: none of the 2002-2018 rows", not any(n in parts(2020, "Nissan", "Altima", SEDAN) for n in ("Fuel Pump Module (in-tank, test before listing)", "Rear Spoiler (factory)")))

# 2b. the other nine models
FWD = {**SEDAN, "driveType": "FWD/Front-Wheel Drive"}
AWD = {**SEDAN, "bodyClass": "Sport Utility Vehicle (SUV)/Multipurpose Vehicle (MPV)", "driveType": "AWD/All-Wheel Drive"}
HATCH = {**SEDAN, "bodyClass": "Hatchback/Liftback/Notchback"}
def names(year, make, model, decode):
    return set(parts(year, make, model, decode))
check("Camry 2007: mechanical rows + XLE seat option", {"Fuel Pump Module (in-tank, test before listing)", "A/C Compressor (clutch spins free)"} <= names(2007, "Toyota", "Camry", FWD)
      and parts(2007, "Toyota", "Camry", FWD)["Leather Power Driver Seat (XLE)"]["trim_status"] == "unconfirmed")
check("Camry 2014: Entune row, 2019: Entune 3 row (not both)", "Entune / Touchscreen Head Unit" in names(2014, "Toyota", "Camry", FWD)
      and "Entune 3 Touchscreen Head Unit" in names(2019, "Toyota", "Camry", FWD) and "Entune / Touchscreen Head Unit" not in names(2019, "Toyota", "Camry", FWD))
check("Civic 2008: gen entry got the rows + Navi option; Civic 1998 did not", "A/C Compressor (clutch spins free)" in names(2008, "Honda", "Civic", FWD)
      and "Navigation Head Unit (EX-L w/ Navi)" in names(2008, "Honda", "Civic", FWD) and "A/C Compressor (clutch spins free)" not in names(1998, "Honda", "Civic", FWD))
check("Focus 2013 hatch: hatch tail lights VIN-confirmed; sedan excluded; no decode 'if equipped'",
      parts(2013, "Ford", "Focus", HATCH)["Hatchback Tail Lights (pair, uncracked)"]["trim_status"] == "vin"
      and "Hatchback Tail Lights (pair, uncracked)" not in names(2013, "Ford", "Focus", FWD)
      and parts(2013, "Ford", "Focus")["Hatchback Tail Lights (pair, uncracked)"]["trim_status"] == "unconfirmed")
check("Focus 2013: TCM row; Focus 2010: none", "DCT Transmission Control Module (TCM, match part #)" in names(2013, "Ford", "Focus", FWD)
      and "DCT Transmission Control Module (TCM, match part #)" not in names(2010, "Ford", "Focus", FWD))
check("Escape 2014 AWD: PTU VIN-confirmed; FWD decode: excluded", parts(2014, "Ford", "Escape", AWD)["AWD Power Transfer Unit (PTU)"]["trim_status"] == "vin"
      and "AWD Power Transfer Unit (PTU)" not in names(2014, "Ford", "Escape", FWD))
check("Escape 2014: turbo is 'if equipped'", parts(2014, "Ford", "Escape", FWD)["EcoBoost Turbocharger (1.6/2.0, match part #)"]["trim_status"] == "unconfirmed")
check("Equinox 2012: tail lights now exist, gen-bounded", parts(2012, "Chevrolet", "Equinox", FWD)["Tail Lights (pair, uncracked)"]["fits"] == "2010–2017")
check("Sentra 2015 listed as SR: spoiler listing-confirmed", parts(2015, "Nissan", "Sentra SR")["SR Rear Spoiler"]["trim_status"] == "listing")
check("Elantra 2013: headlights/mirrors/tails now exist", {"Headlights (clear, non-hazed)", "Side Mirrors (power, pair)", "Tail Lights (pair, uncracked)"} <= names(2013, "Hyundai", "Elantra", FWD))
check("Elantra 2008: still has the 2005-10 overlay lamp rows (merge is window-aware)",
      parts(2008, "Hyundai", "Elantra", FWD).get("Headlights (clear, non-hazed)", {}).get("fits") == "2005–2010", str(parts(2008, "Hyundai", "Elantra", FWD).get("Headlights (clear, non-hazed)")))
check("Elantra 2013: lamp row is the 2011-16 one", parts(2013, "Hyundai", "Elantra", FWD)["Headlights (clear, non-hazed)"]["fits"] == "2011–2016")
check("Camry 2010: overlay JBL (2002-14) survives next to the 2015-17 row", parts(2010, "Toyota", "Camry", FWD).get("JBL Amp + Speakers", {}).get("fits") == "2002–2014", str(parts(2010, "Toyota", "Camry", FWD).get("JBL Amp + Speakers")))
check("Camry 2016: JBL row is the 2015-17 one", parts(2016, "Toyota", "Camry", FWD).get("JBL Amp + Speakers", {}).get("fits") == "2015–2017")
check("Corolla 2010 / Malibu 2011: mechanical rows", "Radiator Fan Assembly" in names(2010, "Toyota", "Corolla", FWD) and "Radiator Fan Assembly" in names(2011, "Chevrolet", "Malibu", FWD))

# 3. band sanity + lint
bad = []
for key in ("altima", "camry", "civic 2001-2005", "civic 2006-2011", "civic 2012-2015", "focus", "malibu", "escape", "equinox", "sentra", "corolla", "elantra"):
    for q in js.UNOBTANIUM_DB[key]["top_parts"]:
        if not (0 < q["cost"] < q["low"] < q["high"] <= 6 * q["low"]):
            bad.append((key, q["name"], q["cost"], q["low"], q["high"]))
check("bands sane: 0 < cost < low < high <= 6x low", not bad, str(bad))
check("gate lint clean (body tokens included)", js.lint_gate_tokens() == [], str(js.lint_gate_tokens()))

print("\n" + ("ALL PASS" if not failures else f"{len(failures)} FAILURES: {failures}"))
sys.exit(1 if failures else 0)
