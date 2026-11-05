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
check("Equinox 2012/2016: tail lights exist, bounded at the 2016 facelift (§17)", parts(2012, "Chevrolet", "Equinox", FWD)["Tail Lights (pair, uncracked)"]["fits"] == "2010–2015"
      and parts(2016, "Chevrolet", "Equinox", FWD)["Tail Lights (pair, uncracked)"]["fits"] == "2016–2017")
check("Sentra 2015 listed as SR: spoiler listing-confirmed", parts(2015, "Nissan", "Sentra SR")["SR Rear Spoiler"]["trim_status"] == "listing")
check("Elantra 2013: headlights/mirrors/tails now exist", {"Headlights (clear, non-hazed)", "Side Mirrors (power, pair)", "Tail Lights (pair, uncracked)"} <= names(2013, "Hyundai", "Elantra", FWD))
# §15: the 2005-10 overlay row is now bounded at the 2007 break (2005-06 / 2007-10).
check("Elantra 2005 + 2008: still have the 2005-10 overlay lamp rows (merge is window-aware), per generation",
      parts(2005, "Hyundai", "Elantra", FWD).get("Headlights (clear, non-hazed)", {}).get("fits") == "2005–2006"
      and parts(2008, "Hyundai", "Elantra", FWD).get("Headlights (clear, non-hazed)", {}).get("fits") == "2007–2010", str(parts(2008, "Hyundai", "Elantra", FWD).get("Headlights (clear, non-hazed)")))
check("Elantra 2013/2015: lamp row is the 2011-16 one, bounded at the 2014 facelift (§17)", parts(2013, "Hyundai", "Elantra", FWD)["Headlights (clear, non-hazed)"]["fits"] == "2011–2013"
      and parts(2015, "Hyundai", "Elantra", FWD)["Headlights (clear, non-hazed)"]["fits"] == "2014–2016")
check("Camry 2010/2013: overlay JBL (2002-14) survives next to the 2015-17 row, per generation",
      parts(2010, "Toyota", "Camry", FWD).get("JBL Amp + Speakers", {}).get("fits") == "2007–2011"
      and parts(2013, "Toyota", "Camry", FWD).get("JBL Amp + Speakers", {}).get("fits") == "2012–2014", str(parts(2010, "Toyota", "Camry", FWD).get("JBL Amp + Speakers")))
check("Camry 2016: JBL row is the 2015-17 one", parts(2016, "Toyota", "Camry", FWD).get("JBL Amp + Speakers", {}).get("fits") == "2015–2017")
check("Corolla 2010 / Malibu 2011: mechanical rows", "Radiator Fan Assembly" in names(2010, "Toyota", "Corolla", FWD) and "Radiator Fan Assembly" in names(2011, "Chevrolet", "Malibu", FWD))

# 2c. breadth pass: uncovered models get the commuter rows; feed spellings route to their entries
def disp(year, make, model):
    return [m.get("display") for m in js.match_vehicle(year, make, model)]
check("Lincoln MKZ 2012 now has rows (lamps + evergreens)", len(parts(2012, "Lincoln", "MKZ", FWD)) >= 8)
check("Lincoln LS does not steal Lexus LS", disp(2004, "Lexus", "LS") == ["Lexus LS400 / LS430"] and disp(2003, "Lincoln", "LS") == ["Lincoln LS"])
check("'Dodge 1500 Pickup' routes to the Ram entry", any("Ram" in d for d in disp(2005, "Dodge", "1500 Pickup")))
check("Grand Caravan still matches (shared entry kept both keywords)", disp(2010, "Dodge", "Grand Caravan") == ["Dodge Grand Caravan"] and disp(2008, "Chrysler", "Caravan") == ["Dodge Grand Caravan"], str(disp(2010, "Dodge", "Grand Caravan")))
check("1997 Sentra now matches with lamp rows", "Headlights (clear, non-hazed)" in names(1997, "Nissan", "Sentra", FWD))
check("'Chevrolet Classic' routes to its own N-body entry (§20), not the Epsilon Malibu", disp(2005, "Chevrolet", "Classic") == ["Chevrolet Classic (N-body Malibu)"])
check("'Chevrolet K2500' routes to the C/K entry", any("C/K" in d for d in disp(1995, "Chevrolet", "K2500")))
check("Saturn SL2 and Mazda 5 spellings match", disp(1999, "Saturn", "SL2") == ["Saturn SL"] and disp(2010, "Mazda", "Mazda5") == ["Mazda Mazda5"] and disp(2010, "Mazda", "Mazda 5") == ["Mazda Mazda5"])
check("every breadth key exists and carries the evergreens", all(k in js.UNOBTANIUM_DB and any("Alternator" in q["name"] for q in js.UNOBTANIUM_DB[k]["top_parts"]) for k in js._GAP_GENERIC_KEYS))
check("Rogue 2010: headlights + AWD coupling gated", "Headlights (clear, non-hazed)" in names(2010, "Nissan", "Rogue", FWD) and "AWD Rear Differential / Coupling" not in names(2010, "Nissan", "Rogue", FWD)
      and parts(2010, "Nissan", "Rogue", AWD)["AWD Rear Differential / Coupling"]["trim_status"] == "vin")
check("CR-V 2005: compressor + headlights; 2019 keeps LED row only", "A/C Compressor (clutch spins free)" in names(2005, "Honda", "CR-V", FWD) and "Headlights (clear, non-hazed)" in names(2005, "Honda", "CR-V", FWD)
      and "Headlights (clear, non-hazed)" not in names(2019, "Honda", "CR-V", FWD))
check("RAV4 2015: Entune row; 2008: none", "Entune / Touchscreen Head Unit" in names(2015, "Toyota", "RAV4", FWD) and "Entune / Touchscreen Head Unit" not in names(2008, "Toyota", "RAV4", FWD))
check("Explorer 2014 AWD: PTU confirmed; 2008: no PTU row", parts(2014, "Ford", "Explorer", AWD)["AWD Power Transfer Unit (PTU)"]["trim_status"] == "vin" and "AWD Power Transfer Unit (PTU)" not in names(2008, "Ford", "Explorer", AWD))

# 2d. §13 block (measured order)
MECH3 = {"Fuel Pump Module (in-tank, test before listing)", "A/C Compressor (clutch spins free)", "Radiator Fan Assembly"}
check("Camry 1992/1997/2001: mechanical rows", all(MECH3 <= names(y, "Toyota", "Camry", FWD) for y in (1992, 1997, 2001)))
check("Camry 1998: XLE seat, sunroof, alloys are 'if equipped'",
      all(parts(1998, "Toyota", "Camry", FWD)[n]["trim_status"] == "unconfirmed" for n in ("Leather Power Driver Seat (XLE)", "Sunroof Glass + Motor", "Alloy Wheels (set of 4, straight)")))
check("Camry 1998: no 2002+ rows (Entune, 17\"/18\" wheels)", not ({"Entune / Touchscreen Head Unit", "17\"/18\" Alloy Wheels (set of 4, straight)"} & names(1998, "Toyota", "Camry", FWD)))
check("Camry 2004: one fuel pump row, fits 2002+ window", parts(2004, "Toyota", "Camry", FWD)["Fuel Pump Module (in-tank, test before listing)"]["fits"].startswith("2002"),
      parts(2004, "Toyota", "Camry", FWD)["Fuel Pump Module (in-tank, test before listing)"]["fits"])
check("Camry 1995 / 1999: mechanical rows bounded to their own generation",
      parts(1995, "Toyota", "Camry", FWD)["A/C Compressor (clutch spins free)"]["fits"] == "1992–1996"
      and parts(1999, "Toyota", "Camry", FWD)["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "1997–2001"
      and parts(1999, "Toyota", "Camry", FWD)["Sunroof Glass + Motor"]["fits"] == "1997–2001")
check("Camry 1991: still outside the entry", not names(1991, "Toyota", "Camry", FWD))
a09, a14 = parts(2009, "Hyundai", "Accent", FWD), parts(2014, "Hyundai", "Accent", FWD)
check("Accent 2009/2014: pump, fan, tail lights in their generation", MECH3 <= set(a09) and MECH3 <= set(a14)
      and a09["Tail Lights (pair, uncracked)"]["fits"] == "2006–2011" and a14["Radiator Fan Assembly"]["fits"] == "2012–2017")
check("Accent: A/C 'if equipped' 2006-11, plain 2012-17", a09["A/C Compressor (clutch spins free)"]["trim_status"] == "unconfirmed"
      and a14["A/C Compressor (clutch spins free)"].get("trim_status") is None)
check("Accent 2014 hatch decode: hatch lamps VIN-confirmed; sedan decode excludes them",
      parts(2014, "Hyundai", "Accent", HATCH)["Hatchback Tail Lights (pair, uncracked)"]["trim_status"] == "vin"
      and "Hatchback Tail Lights (pair, uncracked)" not in names(2014, "Hyundai", "Accent", SEDAN))
check("Accent 2003: no hatch/sunroof/wheel rows; 2019: none of the new rows",
      not ({"Hatchback Tail Lights (pair, uncracked)", "Sunroof Glass + Motor"} & names(2003, "Hyundai", "Accent", FWD))
      and not (MECH3 & names(2019, "Hyundai", "Accent", FWD)))
check("Accent 2010: one row per name", len(js.match_vehicle(2010, "Hyundai", "Accent")) == 1
      and len([p for p in js.match_vehicle(2010, "Hyundai", "Accent")[0]["top_parts"] if p["name"] == "Tail Lights (pair, uncracked)"]) == 1)

l97, l03 = parts(1997, "Buick", "LeSabre", FWD), parts(2003, "Buick", "LeSabre", FWD)
check("LeSabre 1997/2003: mechanical rows in their generation", MECH3 <= set(l97) and MECH3 <= set(l03)
      and l97["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "1992–1999" and l03["A/C Compressor (clutch spins free)"]["fits"] == "2000–2005")
check("LeSabre 2003: tail lights + sunroof; 1997: neither", {"Tail Lights (pair, uncracked)", "Sunroof Glass + Motor"} <= set(l03)
      and not ({"Tail Lights (pair, uncracked)", "Sunroof Glass + Motor"} & set(l97)))
check("LeSabre: Limited seat and wheels are 'if equipped'", all(l03[n]["trim_status"] == "unconfirmed" for n in ("Leather Power Driver Seat (Limited)", "Alloy Wheels (set of 4, straight)", "Sunroof Glass + Motor")))

c07, c12 = parts(2007, "Buick", "LaCrosse", FWD), parts(2012, "Buick", "LaCrosse", FWD)
check("LaCrosse 2007/2012: mechanical rows + tail lights in their generation", MECH3 <= set(c07) and MECH3 <= set(c12)
      and c07["Tail Lights (pair, uncracked)"]["fits"] == "2005–2009" and c12["Radiator Fan Assembly"]["fits"] == "2010–2016")
check("LaCrosse 2007: halogen lamp row, not HID; 2012: HID row, not halogen", "Headlights (clear, non-hazed)" in c07 and "OEM HID/LED Headlights" not in c07
      and "OEM HID/LED Headlights" in c12 and "Headlights (clear, non-hazed)" not in c12)
check("LaCrosse 2012: AWD decode confirms the rear unit; FWD decode excludes; 2007 has none",
      parts(2012, "Buick", "LaCrosse", AWD)["AWD Rear Differential / Transfer Unit"]["trim_status"] == "vin"
      and "AWD Rear Differential / Transfer Unit" not in c12 and "AWD Rear Differential / Transfer Unit" not in names(2007, "Buick", "LaCrosse", AWD))
check("LaCrosse 2012: Harman Kardon 'if equipped'; 2018: none of the new rows", c12["Harman Kardon Amp + Speakers"]["trim_status"] == "unconfirmed"
      and not (MECH3 & names(2018, "Buick", "LaCrosse", FWD)))

r95, r02 = parts(1995, "Toyota", "Corolla", FWD), parts(2002, "Toyota", "Corolla", FWD)
check("Corolla 1995/2002: pump + fan in their generation; A/C and sunroof 'if equipped'", MECH3 <= set(r95) and MECH3 <= set(r02)
      and r95["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "1993–1997" and r02["Radiator Fan Assembly"]["fits"] == "1998–2002"
      and r02["A/C Compressor (clutch spins free)"]["trim_status"] == "unconfirmed" and r95["Sunroof Glass + Motor"]["trim_status"] == "unconfirmed")
check("Corolla 2005: A/C is the plain 2003+ row (one row, not 'if equipped')",
      parts(2005, "Toyota", "Corolla", FWD)["A/C Compressor (clutch spins free)"].get("trim_status") is None)
check("Corolla 1991: still outside the entry", not names(1991, "Toyota", "Corolla", FWD))

k12, k16 = parts(2012, "Kia", "Soul", FWD), parts(2016, "Kia", "Soul", FWD)
check("Soul 2012/2016: mechanical rows, tail lights, mirrors in their generation", MECH3 <= set(k12) and MECH3 <= set(k16)
      and k12["Tail Lights (pair, uncracked)"]["fits"] == "2010–2013" and k16["Side Mirrors (pair)"]["fits"] == "2014–2019")
check("Soul 2012: sunroof + wheels 'if equipped'; 2016 keeps the panoramic row, not the plain sunroof",
      k12["Sunroof Glass + Motor"]["trim_status"] == "unconfirmed" and "Panoramic Sunroof Assembly" in k16 and "Sunroof Glass + Motor" not in k16)
check("Soul 2021: none of the new rows", not (MECH3 & names(2021, "Kia", "Soul", FWD)))


# 2e. §14: no gap-block row crosses a generation break (the part finder reads
# "fits" as the same-generation donor window)
import re as _re
def _breaks(key):
    return js.GENERATION_BREAKS.get(_re.sub(r" \d{4}-\d{4}$", "", key), [])
crossing = [r for r in js._GAP_BLOCK_ROWS if any(r[2] < b <= r[3] for b in _breaks(r[0]))]
check("§14: no gap-block row on a GENERATION_BREAKS model crosses a break", not crossing, str(crossing[:10]))
check("§14: registry covers the gap models (Altima, Camry, Malibu, RAV4, Soul ...)",
      {"altima", "camry", "malibu", "rav4", "soul", "lacrosse"} <= {r[0] for r in js._GAP_BLOCK_ROWS})
check("§14: only gap-block entries are registered (no id reuse leaks)",
      {r[0] for r in js._GAP_BLOCK_ROWS} <= {"altima", "camry", "focus", "malibu", "escape", "equinox", "sentra", "corolla", "elantra",
       "civic 2001-2005", "civic 2006-2011", "civic 2012-2015", "rogue", "cr-v", "rav4", "explorer 2011-2019", "wrx", "impreza", "mx-5",
       "4runner 2003-2009", "4runner 2010-2024", "tacoma 2005-2015", "tacoma 2016-2024", "accent", "lesabre", "lacrosse", "soul",
       # §16
       "explorer 1991-2001", "compass", "kia rio", "century", "aveo", "passat", "lucerne",
       # §18
       "forte", "regal", "tucson", "sportage", "spectra", "legacy", "mkz", "elantra",
       # §19
       "galant", "grand am", "sorento", "santa fe", "mkx", "five hundred", "optima", "volkswagen cc",
       # §20
       "tribute", "uplander", "mazda5", "lexus es", "windstar", "savana", "chevrolet classic",
       # §21
       "mariner", "fiat 500", "spark", "juke", "sable", "stratus", "mustang 2005-2014", "transit connect",
       # §22
       "milan", "encore", "captiva sport", "park avenue", "scion xb 2008-2015", "sonata", "infiniti qx60", "escort", "ford zx2", "encore gx"},
      str(sorted({r[0] for r in js._GAP_BLOCK_ROWS})))
c04, c15 = parts(2004, "Toyota", "Camry", FWD), parts(2015, "Toyota", "Camry", FWD)
check("§14: Camry 2004 pump fits 2002–2006, 2015 fits 2012–2017",
      c04["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2002–2006" and c15["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2012–2017")
check("§14: Malibu 2010 compressor fits 2008–2012; Altima 2010 throttle body 2007–2012; Equinox 2012 AWD unit 2010–2017",
      parts(2010, "Chevrolet", "Malibu", FWD)["A/C Compressor (clutch spins free)"]["fits"] == "2008–2012"
      and parts(2010, "Nissan", "Altima", SEDAN)["Electronic Throttle Body (match part #)"]["fits"] == "2007–2012"
      and parts(2012, "Chevrolet", "Equinox", AWD)["AWD Rear Differential / Transfer Unit"]["fits"] == "2010–2017")
# §15 widened the bound to every row: the shared alternator row is now per generation too.
check("§15: shared evergreen rows bounded too (Camry 2004 alternator fits 2002–2006)",
      parts(2004, "Toyota", "Camry", FWD)["Alternator (spin-test at yard)"]["fits"] == "2002–2006")
crossing_all = []
_seen = set()
for _k, _e in js.UNOBTANIUM_DB.items():
    if id(_e) in _seen:
        continue
    _seen.add(id(_e))
    _lo, _hi = _e["year_range"]
    for _p in _e["top_parts"]:
        _a, _b = max(_lo, _p.get("yr_min", _lo)), min(_hi, _p.get("yr_max", _hi))
        if any(_a < b <= _b for b in _breaks(_k)):
            crossing_all.append((_k, _p["name"], _a, _b))
check("§15: no row on any GENERATION_BREAKS model crosses a break", not crossing_all, str(crossing_all[:10]))
check("§15: interchange notes survive the split (2010 Escape mirrors still share with Tribute/Mariner; 2002 Camry alternator keeps the 1MZ note)",
      "Tribute" in parts(2010, "Ford", "Escape", FWD)["Side Mirrors (power, pair)"].get("sharedWith", "")
      and "1MZ" in parts(2002, "Toyota", "Camry", FWD)["Alternator (spin-test at yard)"].get("sharedWith", ""))


# 2f. §16 block (measured order)
f03, f06 = parts(2003, "Ford", "Focus", FWD), parts(2006, "Ford", "Focus", FWD)
check("§16 Focus 2003/2006: pump, fan in their window; A/C and sunroof 'if equipped'", MECH3 <= set(f03) and MECH3 <= set(f06)
      and f03["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2000–2004" and f06["Radiator Fan Assembly"]["fits"] == "2005–2007"
      and f03["A/C Compressor (clutch spins free)"]["trim_status"] == "unconfirmed")
check("§16 Focus SVT: seats listing-confirmed on 'Focus SVT', 'if equipped' on plain Focus 2003, absent 2006",
      parts(2003, "Ford", "Focus SVT")["SVT Front Seats (pair)"]["trim_status"] == "listing"
      and f03["SVT Front Seats (pair)"]["trim_status"] == "unconfirmed" and "SVT Front Seats (pair)" not in f06)
check("§16 Focus 2010: still the 2008-11 rows, not the 2005-07 ones", parts(2010, "Ford", "Focus", FWD)["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2008–2011")

FOUR = {**SEDAN, "bodyClass": "Sport Utility Vehicle (SUV)/Multipurpose Vehicle (MPV)", "driveType": "4WD/4-Wheel Drive/4x4"}
RWD = {**FOUR, "driveType": "RWD/Rear-Wheel Drive"}
e93, e99 = parts(1993, "Ford", "Explorer", FOUR), parts(1999, "Ford", "Explorer", FOUR)
check("§16 Explorer 1993/1999: pump in its generation, no electric-fan row", e93["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "1991–1994"
      and e99["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "1995–2001" and "Radiator Fan Assembly" not in e99)
check("§16 Explorer 1999: 4WD decode confirms the shift motor; RWD decode excludes it",
      e99["Transfer Case Shift Motor (match part #)"]["trim_status"] == "vin" and "Transfer Case Shift Motor (match part #)" not in names(1999, "Ford", "Explorer", RWD))
check("§16 Explorer 2004: none of the 1991-2001 rows", "Leather Power Driver Seat (Eddie Bauer/Limited)" not in names(2004, "Ford", "Explorer", FOUR))

j09, j14 = parts(2009, "Jeep", "Compass", AWD), parts(2014, "Jeep", "Compass", FWD)
check("§16 Compass: pump/fan/A-C 2007-16; tail lights split at the 2011 facelift", MECH3 <= set(j09) and MECH3 <= set(j14)
      and j14["Radiator Fan Assembly"]["fits"] == "2007–2016" and j09["Tail Lights (pair, uncracked)"]["fits"] == "2007–2010"
      and j14["Tail Lights (pair, uncracked)"]["fits"] == "2011–2016")
check("§16 Compass: AWD decode confirms rear unit, FWD excludes; 2018 none", j09["AWD Rear Differential / Transfer Unit"]["trim_status"] == "vin"
      and "AWD Rear Differential / Transfer Unit" not in j14 and not (MECH3 & names(2018, "Jeep", "Compass", FWD)))

k09, k13 = parts(2009, "Kia", "Rio", FWD), parts(2013, "Kia", "Rio", FWD)
check("§16 Rio 2009/2013: pump, fan, tail lights per generation; A/C 'if equipped' 2009, plain 2013", MECH3 <= set(k09) and MECH3 <= set(k13)
      and k09["Tail Lights (pair, uncracked)"]["fits"] == "2006–2011" and k13["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2012–2017"
      and k09["A/C Compressor (clutch spins free)"]["trim_status"] == "unconfirmed" and k13["A/C Compressor (clutch spins free)"].get("trim_status") is None)
check("§16 Rio 2013 hatch decode: hatch lamps VIN-confirmed; sedan excluded", parts(2013, "Kia", "Rio", HATCH)["Hatchback Tail Lights (pair, uncracked)"]["trim_status"] == "vin"
      and "Hatchback Tail Lights (pair, uncracked)" not in names(2013, "Kia", "Rio", SEDAN))

b92, b02 = parts(1992, "Buick", "Century", FWD), parts(2002, "Buick", "Century", FWD)
check("§16 Century 1992/2002: pump in its generation; A/C 'if equipped' 1992, plain 2002; 1984 none",
      b92["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "1986–1996" and b02["A/C Compressor (clutch spins free)"]["fits"] == "1997–2005"
      and b92["A/C Compressor (clutch spins free)"]["trim_status"] == "unconfirmed" and b02["A/C Compressor (clutch spins free)"].get("trim_status") is None
      and "Fuel Pump Module (in-tank, test before listing)" not in names(1984, "Buick", "Century", FWD))
check("§16 Century 2002: mirrors + Limited seat 'if equipped'", "Side Mirrors (pair)" in b02 and b02["Leather Power Driver Seat (Limited)"]["trim_status"] == "unconfirmed")

check("§16 Aveo: pump per window (2005 -> 2004-06, 2008 -> 2007-08, 2010 -> 2009-11); existing headlight row now bounded too",
      parts(2005, "Chevrolet", "Aveo", FWD)["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2004–2006"
      and parts(2008, "Chevrolet", "Aveo", FWD)["Radiator Fan Assembly"]["fits"] == "2007–2008"
      and parts(2010, "Chevrolet", "Aveo", FWD)["A/C Compressor (clutch spins free)"]["trim_status"] == "unconfirmed"
      and parts(2010, "Chevrolet", "Aveo", FWD)["Headlights (clear pair)"]["fits"] == "2009–2011")

v03, v08 = parts(2003, "Volkswagen", "Passat", FWD), parts(2008, "Volkswagen", "Passat", AWD)
check("§16 Passat 2003/2008: mechanical rows per generation; Monsoon 'if equipped' on B5 only", MECH3 <= set(v03) and MECH3 <= set(v08)
      and v03["A/C Compressor (clutch spins free)"]["fits"] == "1998–2005" and v08["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2006–2011"
      and v03["Monsoon Amp + Speakers"]["trim_status"] == "unconfirmed" and "Monsoon Amp + Speakers" not in v08)
check("§16 Passat 2008: AWD decode confirms 4Motion diff; FWD decode excludes", v08["4Motion Rear Differential (match part #)"]["trim_status"] == "vin"
      and "4Motion Rear Differential (match part #)" not in names(2008, "Volkswagen", "Passat", FWD))

u07 = parts(2007, "Buick", "Lucerne", FWD)
check("§16 Lucerne 2007: mechanical rows + tail lights 2006-11; options 'if equipped'", MECH3 <= set(u07)
      and u07["Tail Lights (pair, uncracked)"]["fits"] == "2006–2011" and u07["Harman Kardon Amp + Speakers"]["trim_status"] == "unconfirmed")


# 2g. §17: appearance rows (lamps, grille, bumpers, fog/marker lights) do not
# cross a listed facelift year; other rows are not cut at facelifts.
fl_cross, fl_mech_cut = [], []
_seen = set()
for _k, _e in js.UNOBTANIUM_DB.items():
    if id(_e) in _seen:
        continue
    _seen.add(id(_e))
    _fl = js.FACELIFT_BREAKS.get(_re.sub(r" \d{4}-\d{4}$", "", _k), [])
    _lo, _hi = _e["year_range"]
    for _p in _e["top_parts"]:
        _a, _b = max(_lo, _p.get("yr_min", _lo)), min(_hi, _p.get("yr_max", _hi))
        if js._FACELIFT_SENSITIVE_RE.search(_p["name"]) and any(_a < y <= _b for y in _fl):
            fl_cross.append((_k, _p["name"], _a, _b))
check("§17: no facelift-sensitive row crosses a listed facelift year", not fl_cross, str(fl_cross[:10]))
check("§17: every FACELIFT_BREAKS key is a real entry base and its years fall inside the entry",
      all(any(_re.sub(r" \d{4}-\d{4}$", "", k) == base and any(e["year_range"][0] < y <= e["year_range"][1] for y in ys)
              for k, e in js.UNOBTANIUM_DB.items()) for base, ys in js.FACELIFT_BREAKS.items()))

check("§17: Focus 2003 lamps fit 2000–2004, Compass 2013 headlights 2011–2016; Focus 2003 fuel pump not cut (mechanical)",
      parts(2003, "Ford", "Focus", FWD)["Headlights (clear, non-hazed)"]["fits"] == "2000–2004"
      and parts(2013, "Jeep", "Compass", FWD)["Headlights (clear pair)"]["fits"] == "2011–2016"
      and parts(2008, "Jeep", "Compass", FWD)["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2007–2016")

# §18
COUPE_D = {**SEDAN, "bodyClass": "Coupe"}
t10, t12 = parts(2010, "Kia", "Forte", FWD), parts(2012, "Kia", "Forte", FWD)
check("§18 Forte: pump/fan/tails 2010-13; A/C 'if equipped' 2010, plain 2012", MECH3 <= set(t10) and MECH3 <= set(t12)
      and t10["Tail Lights (pair, uncracked)"]["fits"] == "2010–2013" and t10["A/C Compressor (clutch spins free)"]["trim_status"] == "unconfirmed"
      and t12["A/C Compressor (clutch spins free)"].get("trim_status") is None)
check("§18 Forte: Koup lamps VIN-confirmed on a coupe decode, excluded on a sedan; 2015 none",
      parts(2011, "Kia", "Forte", COUPE_D)["Koup Tail Lights (pair, uncracked)"]["trim_status"] == "vin"
      and "Koup Tail Lights (pair, uncracked)" not in names(2011, "Kia", "Forte", SEDAN) and not (MECH3 & names(2015, "Kia", "Forte", FWD)))

g01, g12, g15 = parts(2001, "Buick", "Regal", FWD), parts(2012, "Buick", "Regal", FWD), parts(2015, "Buick", "Regal", AWD)
check("§18 Regal: mechanical rows per generation; tail lights cut at the 2014 facelift", MECH3 <= set(g01) and MECH3 <= set(g12)
      and g01["Tail Lights (pair, uncracked)"]["fits"] == "1997–2004" and g12["Tail Lights (pair, uncracked)"]["fits"] == "2011–2013"
      and g15["Tail Lights (pair, uncracked)"]["fits"] == "2014–2017" and g12["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2011–2017")
check("§18 Regal: AWD unit 2014-17 only (AWD decode confirms 2015; no row 2012)", g15["AWD Rear Differential / Transfer Unit"]["trim_status"] == "vin"
      and "AWD Rear Differential / Transfer Unit" not in names(2012, "Buick", "Regal", AWD))

h06, h12 = parts(2006, "Hyundai", "Tucson", AWD), parts(2012, "Hyundai", "Tucson", FWD)
check("§18 Tucson: pump/fan per generation; A/C plain 2006, 'if equipped' 2012; AWD decode confirms coupling", MECH3 <= set(h06) and MECH3 <= set(h12)
      and h06["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2005–2009" and h12["Radiator Fan Assembly"]["fits"] == "2010–2015"
      and h06["A/C Compressor (clutch spins free)"].get("trim_status") is None and h12["A/C Compressor (clutch spins free)"]["trim_status"] == "unconfirmed"
      and h06["AWD Rear Differential / Coupling"]["trim_status"] == "vin" and "AWD Rear Differential / Coupling" not in h12)

s07, s13 = parts(2007, "Kia", "Sportage", AWD), parts(2013, "Kia", "Sportage", FWD)
check("§18 Sportage: pump/fan per generation, AWD coupling gated, SL panoramic roof 'if equipped'; tails cut at the 2009 facelift",
      MECH3 <= set(s07) and MECH3 <= set(s13) and s07["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2005–2010"
      and s07["AWD Rear Differential / Coupling"]["trim_status"] == "vin" and "AWD Rear Differential / Coupling" not in s13
      and s13["Panoramic Sunroof Assembly"]["trim_status"] == "unconfirmed" and s07["Tail Lights (pair, uncracked)"]["fits"] == "2005–2008")

p03, p06, p08 = parts(2003, "Kia", "Spectra", FWD), parts(2006, "Kia", "Spectra", FWD), parts(2008, "Kia", "Spectra", HATCH)
check("§18 Spectra: pump per generation, none for ambiguous 2004; tails cut at the 2007 facelift; hatch lamps VIN-confirmed",
      p03["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2000–2003" and p06["Radiator Fan Assembly"]["fits"] == "2005–2009"
      and "Fuel Pump Module (in-tank, test before listing)" not in names(2004, "Kia", "Spectra", FWD)
      and p06["Tail Lights (pair, uncracked)"]["fits"] == "2005–2006" and p08["Hatchback Tail Lights (pair, uncracked)"]["fits"] == "2007–2009"
      and p08["Hatchback Tail Lights (pair, uncracked)"]["trim_status"] == "vin")

l97, l02, l13 = parts(1997, "Subaru", "Legacy", AWD), parts(2002, "Subaru", "Legacy", FWD), parts(2013, "Subaru", "Legacy", FWD)
check("§18 Legacy: pump per generation; rear diff gated 1995-99 (AWD decode confirms), ungated 2000-04/2010-14",
      l97["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "1995–1999" and l02["Radiator Fan Assembly"]["fits"] == "2000–2004"
      and l97["Rear Differential (match final-drive ratio)"]["trim_status"] == "vin"
      and "Rear Differential (match final-drive ratio)" not in names(1997, "Subaru", "Legacy", FWD)
      and l02["Rear Differential (match final-drive ratio)"].get("trim_status") is None and l13["Rear Differential (match final-drive ratio)"]["fits"] == "2010–2014")

z08, z15 = parts(2008, "Lincoln", "MKZ", AWD), parts(2015, "Lincoln", "MKZ", FWD)
check("§18 MKZ: rows per generation (new 2013 break); AWD gated; existing lamp rows cut at the 2010/2017 facelifts",
      z08["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2007–2012" and z15["Radiator Fan Assembly"]["fits"] == "2013–2020"
      and z08["AWD Rear Differential / Transfer Unit"]["trim_status"] == "vin" and "AWD Rear Differential / Transfer Unit" not in z15
      and z08["Headlights (clear, non-hazed)"]["fits"] == "2007–2009" and z15["Tail Lights (pair, uncracked)"]["fits"] == "2013–2016")

x02, x05, x09 = parts(2002, "Hyundai", "Elantra", FWD), parts(2005, "Hyundai", "Elantra", HATCH), parts(2009, "Hyundai", "Elantra", FWD)
check("§18 Elantra XD: mech 2001-06; lamps 2001-03 (2004 facelift cut); hatch lamps VIN-confirmed 2004-06; overlay 2007-10 lamps kept",
      MECH3 <= set(x02) and x02["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2001–2006"
      and x02["Headlights (clear, non-hazed)"]["fits"] == "2001–2003" and x02["Tail Lights (pair, uncracked)"]["fits"] == "2001–2003"
      and x05["Hatchback Tail Lights (pair, uncracked)"]["fits"] == "2004–2006" and x05["Hatchback Tail Lights (pair, uncracked)"]["trim_status"] == "vin"
      and x09["Headlights (clear, non-hazed)"]["fits"] == "2007–2010")

# §19
m01, m08 = parts(2001, "Mitsubishi", "Galant", FWD), parts(2008, "Mitsubishi", "Galant", FWD)
check("§19 Galant: mech per generation, A/C plain; tail lights cut at the 2002/2007/2009 facelifts",
      MECH3 <= set(m01) and MECH3 <= set(m08) and m08["A/C Compressor (clutch spins free)"].get("trim_status") is None
      and m01["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "1999–2003" and m01["Tail Lights (pair, uncracked)"]["fits"] == "1999–2001"
      and m08["Tail Lights (pair, uncracked)"]["fits"] == "2007–2008")

a97, a03 = parts(1997, "Pontiac", "Grand Am", FWD), parts(2003, "Pontiac", "Grand Am", FWD)
check("§19 Grand Am: mech per generation; A/C plain 1997/2003, 'if equipped' 1999; GT lamps listing-confirmed on 'Grand Am GT'",
      MECH3 <= set(a97) and MECH3 <= set(a03) and a97["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "1996–1998"
      and a03["A/C Compressor (clutch spins free)"].get("trim_status") is None
      and parts(1999, "Pontiac", "Grand Am", FWD)["A/C Compressor (clutch spins free)"]["trim_status"] == "unconfirmed"
      and parts(2003, "Pontiac", "Grand Am GT")["GT Tail Lights (pair, uncracked)"]["trim_status"] == "listing"
      and "GT Tail Lights (pair, uncracked)" not in a97)

r05, r08 = parts(2005, "Kia", "Sorento", FWD), parts(2008, "Kia", "Sorento", FWD)
check("§19 Sorento: mech 2003-09; tails cut at the 2007 facelift; A/C plain 2005, 'if equipped' 2008",
      MECH3 <= set(r05) and MECH3 <= set(r08) and r05["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2003–2009"
      and r05["Tail Lights (pair, uncracked)"]["fits"] == "2003–2006" and r08["Tail Lights (pair, uncracked)"]["fits"] == "2007–2009"
      and r05["A/C Compressor (clutch spins free)"].get("trim_status") is None and r08["A/C Compressor (clutch spins free)"]["trim_status"] == "unconfirmed")

q03, q06 = parts(2003, "Hyundai", "Santa Fe", AWD), parts(2006, "Hyundai", "Santa Fe", FWD)
check("§19 Santa Fe: mech 2001-06; tails cut at the 2005 facelift; AWD coupling gated; no sunroof row 2001",
      MECH3 <= set(q03) and q03["Tail Lights (pair, uncracked)"]["fits"] == "2001–2004" and q06["Tail Lights (pair, uncracked)"]["fits"] == "2005–2006"
      and q03["AWD Rear Differential / Coupling"]["trim_status"] == "vin" and "AWD Rear Differential / Coupling" not in q06
      and "Sunroof Glass + Motor" not in names(2001, "Hyundai", "Santa Fe", FWD))

k09, k13 = parts(2009, "Lincoln", "MKX", AWD), parts(2013, "Lincoln", "MKX", FWD)
check("§19 MKX: rows per generation (new 2016 break); PTU gated; THX 'if equipped'; lamps cut at the 2011 facelift",
      MECH3 <= set(k09) and k09["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2007–2015"
      and k09["AWD Power Transfer Unit (PTU)"]["trim_status"] == "vin" and "AWD Power Transfer Unit (PTU)" not in k13
      and k13["THX II Amp + Speakers"]["trim_status"] == "unconfirmed" and "Revel Amp + Speakers" not in k13
      and k09["Tail Lights (pair, uncracked)"]["fits"] == "2007–2010" and k13["Headlights (clear, non-hazed)"]["fits"] == "2011–2015")

v06 = parts(2006, "Ford", "Five Hundred", AWD)
check("§19 Five Hundred: mech 2005-07, AWD decode confirms the rear unit, moonroof 'if equipped'",
      MECH3 <= set(v06) and v06["AWD Rear Differential / Transfer Unit"]["trim_status"] == "vin"
      and "AWD Rear Differential / Transfer Unit" not in names(2006, "Ford", "Five Hundred", FWD) and v06["Sunroof Glass + Motor"]["trim_status"] == "unconfirmed")

o02, o08 = parts(2002, "Kia", "Optima", FWD), parts(2008, "Kia", "Optima", FWD)
check("§19 Optima: mech per generation, none for 2006; tails cut at the MS (2003/04/05) and MG (2009) facelifts",
      MECH3 <= set(o02) and MECH3 <= set(o08) and o02["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2001–2005"
      and "Fuel Pump Module (in-tank, test before listing)" not in names(2006, "Kia", "Optima", FWD)
      and o02["Tail Lights (pair, uncracked)"]["fits"] == "2001–2002" and o08["Tail Lights (pair, uncracked)"]["fits"] == "2007–2008")

w11, w15 = parts(2011, "Volkswagen", "CC", AWD), parts(2015, "Volkswagen", "CC", FWD)
check("§19 CC: mech 2009-17; 4Motion diff gated 2009-16; lamps cut at the 2013 facelift",
      MECH3 <= set(w11) and w11["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2009–2017"
      and w11["4Motion Rear Differential (match part #)"]["trim_status"] == "vin" and "4Motion Rear Differential (match part #)" not in w15
      and "4Motion Rear Differential (match part #)" not in names(2017, "Volkswagen", "CC", AWD)
      and w11["Tail Lights (pair, uncracked)"]["fits"] == "2009–2012" and w15["Tail Lights (pair, uncracked)"]["fits"] == "2013–2017")

# §20
c99, c02 = parts(1999, "Chevrolet", "Malibu", FWD), parts(2002, "Chevrolet", "Malibu", FWD)
check("§20 Malibu 1997-2003: mech rows (A/C plain); sunroof/spoiler 'if equipped' 2000-03 only; 2005 keeps the Epsilon rows",
      MECH3 <= set(c99) and c99["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "1997–2003"
      and c02["Sunroof Glass + Motor"]["trim_status"] == "unconfirmed" and "LS Rear Spoiler" not in c99
      and parts(2005, "Chevrolet", "Malibu", FWD)["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2004–2007")

cl = js.match_vehicle(2005, "Chevrolet", "Classic")
check("§20 Chevrolet Classic 2005: own N-body entry, rows bounded 2004-05, evergreens kept, no Epsilon Malibu rows",
      [m["display"] for m in cl] == ["Chevrolet Classic (N-body Malibu)"]
      and parts(2005, "Chevrolet", "Classic")["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2004–2005"
      and "Alternator (spin-test at yard)" in parts(2005, "Chevrolet", "Classic") and "Headlights (clear, non-hazed)" in parts(2005, "Chevrolet", "Classic")
      and "MyLink / Infotainment Screen" not in parts(2005, "Chevrolet", "Classic"), str([m["display"] for m in cl]))

b03, b09 = parts(2003, "Mazda", "Tribute", FOUR), parts(2009, "Mazda", "Tribute", FWD)
check("§20 Tribute: mech per generation; PTU on 4WD decodes only; tails cut at the 2005 facelift",
      MECH3 <= set(b03) and b03["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2001–2006"
      and b09["Radiator Fan Assembly"]["fits"] == "2008–2011" and b03["AWD Power Transfer Unit (PTU)"]["trim_status"] == "vin"
      and "AWD Power Transfer Unit (PTU)" not in b09 and b03["Tail Lights (pair, uncracked)"]["fits"] == "2001–2004")

VAN_AWD = {**AWD, "bodyClass": "Minivan"}
u06, u08 = parts(2006, "Chevrolet", "Uplander", VAN_AWD), parts(2008, "Chevrolet", "Uplander", VAN_AWD)
check("§20 Uplander: mech 2005-09; AWD unit 2005-06 only; sliding-door motor 'if equipped'",
      MECH3 <= set(u08) and u06["AWD Rear Differential / Transfer Unit"]["trim_status"] == "vin" and "AWD Rear Differential / Transfer Unit" not in u08
      and u08["Power Sliding Door Motor"]["trim_status"] == "unconfirmed")

d07, d13 = parts(2007, "Mazda", "Mazda5", FWD), parts(2013, "Mazda", "Mazda5", FWD)
check("§20 Mazda5: rows per generation (new 2012 break); A/C plain gen 1, 'if equipped' gen 2; tails cut at the 2008 facelift",
      MECH3 <= set(d07) and MECH3 <= set(d13) and d07["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2006–2010"
      and d13["Radiator Fan Assembly"]["fits"] == "2012–2015" and d07["A/C Compressor (clutch spins free)"].get("trim_status") is None
      and d13["A/C Compressor (clutch spins free)"]["trim_status"] == "unconfirmed" and "Sunroof Glass + Motor" not in d13
      and d07["Tail Lights (pair, uncracked)"]["fits"] == "2006–2007")

e98, e04 = parts(1998, "Lexus", "ES 300", FWD), parts(2004, "Lexus", "ES 330", FWD)
check("§20 Lexus ES: mech per generation; moonroof 'if equipped' 1998, plain 2004; Nakamichi option 1998; tails cut at the 2000 facelift",
      MECH3 <= set(e98) and MECH3 <= set(e04) and e98["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "1997–2001"
      and e98["Sunroof Glass + Motor"]["trim_status"] == "unconfirmed" and e04["Sunroof Glass + Motor"].get("trim_status") is None
      and e98["Nakamichi Amp + Speakers"]["trim_status"] == "unconfirmed" and "Nakamichi Amp + Speakers" not in e04
      and e98["Headlights (clear, non-hazed)"]["fits"] == "1997–1999")

n08 = parts(2008, "Saturn", "Aura", FWD)
check("§20 Aura (overlay rows): mech 2007-09; sunroof 'if equipped'; XR wheels listing-confirmed on 'Aura XR'",
      MECH3 <= set(n08) and n08["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2007–2009"
      and n08["Sunroof Glass + Motor"]["trim_status"] == "unconfirmed"
      and parts(2008, "Saturn", "Aura XR")['XR 18" Alloy Wheels (set of 4, straight)']["trim_status"] == "listing")

VAN = {**FWD, "bodyClass": "Minivan"}
s96, s02 = parts(1996, "Ford", "Windstar", VAN), parts(2002, "Ford", "Windstar", VAN)
check("§20 Windstar: rows per generation (new 1999 break); sliding-door motor gen 2 only; tails cut at the 2001 facelift",
      MECH3 <= set(s96) and MECH3 <= set(s02) and s96["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "1995–1998"
      and s02["A/C Compressor (clutch spins free)"].get("trim_status") is None and "Power Sliding Door Motor" not in s96
      and s02["Power Sliding Door Motor"]["trim_status"] == "unconfirmed" and s02["Tail Lights (pair, uncracked)"]["fits"] == "2001–2003")

g00, g10 = parts(2000, "GMC", "Savana", FWD), parts(2010, "GMC", "Savana", FWD)
check("§20 Savana: pump bounded at the 2003 revision; A/C 'if equipped'; no electric-fan row; lamps cut at the 2003 facelift",
      g00["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "1996–2002" and g10["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2003–2024"
      and g10["A/C Compressor (clutch spins free)"]["trim_status"] == "unconfirmed" and "Radiator Fan Assembly" not in g10
      and g00["Headlights (clear, non-hazed)"]["fits"] == "1996–2002")

# §21
r06, r09 = parts(2006, "Mercury", "Mariner", AWD), parts(2009, "Mercury", "Mariner", FWD)
check("§21 Mariner: rows per generation (new 2008 break); PTU on AWD decodes; sunroof gen 1 only; lamps bounded by generation",
      MECH3 <= set(r06) and MECH3 <= set(r09) and r06["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2005–2007"
      and r09["A/C Compressor (clutch spins free)"]["fits"] == "2008–2011" and r06["AWD Power Transfer Unit (PTU)"]["trim_status"] == "vin"
      and "AWD Power Transfer Unit (PTU)" not in r09 and "Sunroof Glass + Motor" not in r09 and r06["Tail Lights (pair, uncracked)"]["fits"] == "2005–2007")

check("§21 Fiat: 500L/500X get their own entries (evergreens only, own runs); 500e matches nothing; 500/Abarth/500C stay on the 500",
      [m["display"] for m in js.match_vehicle(2015, "Fiat", "500L")] == ["Fiat 500L"]
      and [m["display"] for m in js.match_vehicle(2017, "Fiat", "500X")] == ["Fiat 500X"]
      and js.match_vehicle(2014, "Fiat", "500E") == []
      and [m["display"] for m in js.match_vehicle(2014, "Fiat", "500 Abarth")] == ["Fiat 500"]
      and [m["display"] for m in js.match_vehicle(2013, "Fiat", "500C")] == ["Fiat 500"]
      and parts(2015, "Fiat", "500L")["Alternator (spin-test at yard)"]["fits"] == "2014–2020"
      and "Headlights (clear, non-hazed)" not in parts(2015, "Fiat", "500L"))
f12, f16 = parts(2012, "Fiat", "500", FWD), parts(2016, "Fiat", "500", FWD)
check("§21 Fiat 500: pump/fan 2012-19; A/C plain 2012, 'if equipped' 2016; list-parts ceiling safe on empty entries",
      MECH3 <= set(f12) and f12["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2012–2019"
      and f12["A/C Compressor (clutch spins free)"].get("trim_status") is None and f16["A/C Compressor (clutch spins free)"]["trim_status"] == "unconfirmed"
      and js._max_entry_calibrated_high(js.UNOBTANIUM_DB["fiat 500e"]) == 0)

k14, k18 = parts(2014, "Chevrolet", "Spark", FWD), parts(2018, "Chevrolet", "Spark", FWD)
check("§21 Spark: rows per generation (new 2016 break); A/C plain 2014, 'if equipped' 2018; lamps cut at the 2019 facelift; Spark EV matches nothing",
      MECH3 <= set(k14) and MECH3 <= set(k18) and k14["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2013–2015"
      and k18["Radiator Fan Assembly"]["fits"] == "2016–2022" and k14["A/C Compressor (clutch spins free)"].get("trim_status") is None
      and k18["A/C Compressor (clutch spins free)"]["trim_status"] == "unconfirmed" and k18["Headlights (clear, non-hazed)"]["fits"] == "2016–2018"
      and js.match_vehicle(2015, "Chevrolet", "Spark EV") == [])

j12, j16 = parts(2012, "Nissan", "Juke", AWD), parts(2016, "Nissan", "Juke", FWD)
check("§21 Juke: mech 2011-17; AWD coupling gated; moonroof 'if equipped'; lamps cut at the 2015 facelift",
      MECH3 <= set(j12) and j12["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2011–2017"
      and j12["AWD Rear Differential / Coupling"]["trim_status"] == "vin" and "AWD Rear Differential / Coupling" not in j16
      and j16["Sunroof Glass + Motor"]["trim_status"] == "unconfirmed" and j12["Tail Lights (pair, uncracked)"]["fits"] == "2011–2014")

m97, m02, m08 = parts(1997, "Mercury", "Sable", FWD), parts(2002, "Mercury", "Sable", FWD), parts(2008, "Mercury", "Sable", AWD)
check("§21 Sable: mech per generation; A/C 'if equipped' 1997, plain 2002; AWD unit 2008-09 only; tails cut at the 2004 facelift",
      MECH3 <= set(m97) and MECH3 <= set(m02) and m97["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "1996–1999"
      and m97["A/C Compressor (clutch spins free)"]["trim_status"] == "unconfirmed" and m02["A/C Compressor (clutch spins free)"].get("trim_status") is None
      and m08["AWD Rear Differential / Transfer Unit"]["trim_status"] == "vin" and "AWD Rear Differential / Transfer Unit" not in m02
      and m02["Tail Lights (pair, uncracked)"]["fits"] == "2000–2003")

COUPE_D2 = {**SEDAN, "bodyClass": "Coupe"}
t98, t03s, t03c = parts(1998, "Dodge", "Stratus", FWD), parts(2003, "Dodge", "Stratus", SEDAN), parts(2003, "Dodge", "Stratus", COUPE_D2)
check("§21 Stratus: JA rows 1995-2000; JR rows sedan-gated (sedan decode confirms, coupe decode excludes, no decode 'if equipped'); lamps cut at 2003/2004",
      t98["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "1995–2000" and t98["A/C Compressor (clutch spins free)"]["trim_status"] == "unconfirmed"
      and t03s["Fuel Pump Module (in-tank, test before listing)"]["trim_status"] == "vin" and t03s["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2001–2006"
      and "Fuel Pump Module (in-tank, test before listing)" not in t03c
      and parts(2003, "Dodge", "Stratus")["Fuel Pump Module (in-tank, test before listing)"]["trim_status"] == "unconfirmed"
      and t03s["Tail Lights (pair, uncracked)"]["fits"] == "2003–2003")

s05, s12 = parts(2005, "Ford", "Mustang", FWD), parts(2012, "Ford", "Mustang", FWD)
check("§21 Mustang S197: pump + A/C per generation; Shaker 'if equipped' 2005-09; no fan row; lamps cut at the 2013 facelift",
      s05["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2005–2009" and s12["A/C Compressor (clutch spins free)"]["fits"] == "2010–2014"
      and s05["Shaker 500/1000 Amp + Subwoofer"]["trim_status"] == "unconfirmed" and "Shaker 500/1000 Amp + Subwoofer" not in s12
      and "Radiator Fan Assembly" not in s05 and s12["Headlights (clear, non-hazed)"]["fits"] == "2010–2012")

VAN2 = {**FWD, "bodyClass": "Van"}
c11, c16, c20 = parts(2011, "Ford", "Transit Connect", VAN2), parts(2016, "Ford", "Transit Connect", VAN2), parts(2020, "Ford", "Transit Connect", VAN2)
check("§21 Transit Connect: pump/fan per generation; A/C plain 2011 and 2020, 'if equipped' 2016; lamps cut at the 2019 facelift",
      MECH3 <= set(c11) and MECH3 <= set(c16) and c11["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2010–2013"
      and c16["Radiator Fan Assembly"]["fits"] == "2014–2023" and c11["A/C Compressor (clutch spins free)"].get("trim_status") is None
      and c16["A/C Compressor (clutch spins free)"]["trim_status"] == "unconfirmed" and c20["A/C Compressor (clutch spins free)"].get("trim_status") is None
      and c16["Headlights (clear pair)"]["fits"] == "2014–2018")

# §23 facelift follow-ups: FACELIFT_BREAKS years for further models (cited in PARTS_GAPS §23)
ex98, ex00 = parts(1998, "Ford", "Expedition"), parts(2000, "Ford", "Expedition")
check("§23.1 Expedition: headlights cut at the 1999 facelift; minivan/Odyssey keys present",
      ex98["Headlights (clear, non-hazed)"]["fits"] == "1997–1998" and ex00["Headlights (clear, non-hazed)"]["fits"] == "1999–2002"
      and js.FACELIFT_BREAKS["grand caravan"] == [1999, 2005, 2011] and js.FACELIFT_BREAKS["odyssey"] == [2002, 2008, 2014, 2021]
      and js.FACELIFT_BREAKS["town & country"] == [2005, 2011] and js.FACELIFT_BREAKS["expedition"] == [1999, 2015, 2022])

def _fits(y, mk, mo, name):
    return parts(y, mk, mo)[name]["fits"]
check("§23.2 Silverado/Sierra/Ram/BMW 3/Maxima: lamp rows cut at the cited facelifts; Ram tail-only 2007 not a cut",
      _fits(2002, "Chevrolet", "Silverado 1500", "Headlights (clear, non-hazed)") == "1999–2002"
      and _fits(2016, "Chevrolet", "Silverado 1500", "Headlights (clear, non-hazed)") == "2016–2018"
      and _fits(2003, "GMC", "Sierra 1500", "Headlights (clear, non-hazed)") == "2003–2006"
      and _fits(2006, "Dodge", "Ram 1500", "Headlights (clear, non-hazed)") == "2006–2008"
      and _fits(2003, "BMW", "325i", "OEM Headlight Assembly (E46 halogen/xenon, pair)") == "2002–2003"
      and _fits(1997, "Nissan", "Maxima", "Headlights (clear pair)") == "1997–1999"
      and _fits(2019, "Nissan", "Maxima", "OEM LED Headlights") == "2019–2024")

check("§23.3 Ranger/Traverse/Pathfinder: lamp rows cut at the cited facelifts; grille-only years are not cuts",
      _fits(1990, "Ford", "Ranger", "Headlights (clear, non-hazed)") == "1989–1992"
      and _fits(1995, "Ford", "Ranger", "Headlights (clear, non-hazed)") == "1993–1997"
      and _fits(2004, "Ford", "Ranger", "Headlights (clear, non-hazed)") == "2001–2005"
      and _fits(2020, "Chevrolet", "Traverse", "OEM LED Headlights") == "2018–2021"
      and js.FACELIFT_BREAKS["pathfinder"] == [2002, 2008, 2017] and "suburban" not in js.FACELIFT_BREAKS)

check("§23.4 TrailBlazer/Liberty/Pilot: lamp rows cut at the cited facelifts; Tahoe/Yukon left out",
      _fits(2004, "Chevrolet", "Trailblazer", "Headlights (clear, non-hazed)") == "2002–2005"
      and _fits(2007, "Chevrolet", "Trailblazer", "Headlights (clear, non-hazed)").startswith("2006–")
      and _fits(2003, "Jeep", "Liberty", "Headlights (clear, non-hazed)") == "2002–2004"
      and _fits(2006, "Jeep", "Liberty", "Headlights (clear, non-hazed)") == "2005–2007"
      and js.FACELIFT_BREAKS["pilot"] == [2006, 2012, 2019] and "tahoe" not in js.FACELIFT_BREAKS and "yukon" not in js.FACELIFT_BREAKS)

check("§23.5 Edge/Charger/Dakota/Grand Cherokee: Edge LED headlights cut at the 2019 facelift; tail-only Charger 2009 not a cut",
      _fits(2017, "Ford", "Edge", "OEM LED Headlights") == "2015–2018" and _fits(2020, "Ford", "Edge", "OEM LED Headlights") == "2019–2024"
      and js.FACELIFT_BREAKS["charger"] == [2015] and js.FACELIFT_BREAKS["dakota"] == [1991, 2008]
      and js.FACELIFT_BREAKS["grand cherokee"] == [1996, 2004, 2008, 2014, 2017])

# §22
n08, n06 = parts(2008, "Mercury", "Milan", AWD), parts(2006, "Mercury", "Milan", AWD)
check("§22 Milan: mech 2006-11; AWD unit 2007-11 only (AWD decode confirms 2008); lamps cut at the 2010 facelift",
      MECH3 <= set(n08) and n08["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2006–2011"
      and n08["AWD Rear Differential / Transfer Unit"]["trim_status"] == "vin" and "AWD Rear Differential / Transfer Unit" not in n06
      and n08["Tail Lights (pair, uncracked)"]["fits"] == "2006–2009")

b14, b19 = parts(2014, "Buick", "Encore", AWD), parts(2019, "Buick", "Encore", FWD)
check("§22 Encore: mech 2013-22; AWD coupling gated; lamps cut at the 2017 facelift; Encore GX has its own entry",
      MECH3 <= set(b14) and b14["Fuel Pump Module (in-tank, test before listing)"]["fits"] == "2013–2022"
      and b14["AWD Rear Differential / Coupling"]["trim_status"] == "vin" and "AWD Rear Differential / Coupling" not in b19
      and b14["Tail Lights (pair, uncracked)"]["fits"] == "2013–2016" and b19["Tail Lights (pair, uncracked)"]["fits"] == "2017–2022"
      and [m["display"] for m in js.match_vehicle(2021, "Buick", "Encore GX")] == ["Buick Encore GX"]
      and "Fuel Pump Module (in-tank, test before listing)" not in parts(2021, "Buick", "Encore GX"))

# 3. band sanity + lint
bad = []
for key in ("altima", "accent", "lesabre", "lacrosse", "soul", "milan", "encore", "captiva sport", "park avenue", "scion xb 2008-2015", "sonata", "infiniti qx60", "escort", "mariner", "fiat 500", "spark", "juke", "sable", "stratus", "mustang 2005-2014", "transit connect", "tribute", "uplander", "mazda5", "lexus es", "windstar", "savana", "galant", "grand am", "sorento", "santa fe", "mkx", "five hundred", "optima", "volkswagen cc", "forte", "regal", "tucson", "sportage", "spectra", "legacy", "mkz", "compass", "kia rio", "century", "aveo", "passat", "lucerne", "explorer 1991-2001", "rogue", "cr-v", "rav4", "explorer 2011-2019", *js._GAP_GENERIC_KEYS, "camry", "civic 2001-2005", "civic 2006-2011", "civic 2012-2015", "focus", "malibu", "escape", "equinox", "sentra", "corolla", "elantra"):
    for q in js.UNOBTANIUM_DB[key]["top_parts"]:
        if not (0 < q["cost"] < q["low"] < q["high"] <= 6 * q["low"]):
            bad.append((key, q["name"], q["cost"], q["low"], q["high"]))
check("bands sane: 0 < cost < low < high <= 6x low", not bad, str(bad))
check("gate lint clean (body tokens included)", js.lint_gate_tokens() == [], str(js.lint_gate_tokens()))

print("\n" + ("ALL PASS" if not failures else f"{len(failures)} FAILURES: {failures}"))
sys.exit(1 if failures else 0)
