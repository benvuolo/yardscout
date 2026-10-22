#!/usr/bin/env python3
"""Tests for make-name normalization (owner-reported 2026-10-21: the make
dropdown showed per-chain spellings as separate entries — "MINI (756)" next
to "MINI Cooper (52)", "Alfa Romeo" next to "Alfa-Romeo", "Vw" next to
"Volkswagen" — plus a 3,046-row "General Motors" corporate blob from
Pull-N-Save / Nevada Pic-A-Part).

Covers:
  1. normalize_make — alias table merges (case/punctuation-blind) and casing.
  2. KEEP-SEPARATE cases — legitimately distinct marques must survive
     untouched: Datsun≠Nissan, Geo≠Chevrolet, GMC≠Chevrolet, Genesis≠Hyundai,
     Miles (real Miles Electric Vehicles ZX40ST), Mitsubishi Fuso (Daimler's
     truck marque, not Mitsubishi Motors), etc.
  3. General Motors resolution — VIN WMI division coding first, then
     division-named / division-exclusive models, year-gated Geo/Chevy
     nameplates; ambiguous rows KEEP "General Motors" (never guess).
  4. enrich_vehicles applies normalization end-to-end on vehicle dicts.

Run:  python3 scraper/test_make_normalization.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js

failures = []


def check(name, cond, detail=""):
    print(("  ok  " if cond else "  FAIL") + f" {name}" + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        failures.append(name)


N = js.normalize_make

# ---- 1. alias merges ---------------------------------------------------------
print("alias merges:")
check("MINI Cooper -> MINI", N("MINI Cooper") == "MINI", N("MINI Cooper"))
check("Mini Cooper (chain casing) -> MINI", N("Mini Cooper") == "MINI", N("Mini Cooper"))
check("mini -> MINI (acronym casing)", N("mini") == "MINI", N("mini"))
check("Alfa-Romeo -> Alfa Romeo", N("Alfa-Romeo") == "Alfa Romeo", N("Alfa-Romeo"))
check("ALFA ROMEO -> Alfa Romeo", N("ALFA ROMEO") == "Alfa Romeo", N("ALFA ROMEO"))
check("Fiat-Lancia -> Fiat", N("Fiat-Lancia") == "Fiat", N("Fiat-Lancia"))
check("Mercedes -> Mercedes-Benz", N("Mercedes") == "Mercedes-Benz", N("Mercedes"))
check("MERCEDES-BENZ -> Mercedes-Benz", N("MERCEDES-BENZ") == "Mercedes-Benz", N("MERCEDES-BENZ"))
check("Vw -> Volkswagen", N("Vw") == "Volkswagen", N("Vw"))
check("VW -> Volkswagen", N("VW") == "Volkswagen", N("VW"))
check("Volkswagon (misspelling) -> Volkswagen", N("Volkswagon") == "Volkswagen", N("Volkswagon"))
check("Chevy -> Chevrolet", N("Chevy") == "Chevrolet", N("Chevy"))
check("Rover -> Land Rover (all 28 audit rows were SAL*/LR models)",
      N("Rover") == "Land Rover", N("Rover"))
check("Range Rover -> Land Rover", N("Range Rover") == "Land Rover", N("Range Rover"))
check("Infinity -> Infiniti", N("Infinity") == "Infiniti", N("Infinity"))
check("whitespace collapse + trim", N("  Alfa   Romeo  ") == "Alfa Romeo", N("  Alfa   Romeo  "))
check("idempotent on canonical names", N(N("Fiat-Lancia")) == "Fiat")
check("empty stays empty", N("") == "")

# ---- 2. keep legitimately distinct marques separate --------------------------
print("keep-separate:")
for mk, canon in [
    ("Datsun", "Datsun"),            # not Nissan
    ("Geo", "Geo"),                  # not Chevrolet
    ("GMC", "GMC"),                  # not Chevrolet
    ("Hummer", "Hummer"),
    ("Eagle", "Eagle"),              # not Chrysler/Jeep
    ("Daewoo", "Daewoo"),
    ("Genesis", "Genesis"),          # not Hyundai
    ("Infiniti", "Infiniti"),        # not Nissan
    ("Scion", "Scion"),              # not Toyota
    ("Ram", "Ram"),                  # not Dodge
    ("Saturn", "Saturn"),
    ("Merkur", "Merkur"),            # not Ford/Mercury
    ("Smart", "Smart"),              # not Mercedes-Benz
    ("Miles", "Miles"),              # real Miles Electric Vehicles (ZX40ST row)
    ("Mitsubishi", "Mitsubishi"),
    ("Mitsubishi Fuso", "Mitsubishi Fuso"),  # Daimler truck marque, kept distinct
    ("Lincoln", "Lincoln"),          # not Ford
    ("Mercury", "Mercury"),          # not Ford
    ("MG", "MG"),                    # acronym casing survives
]:
    check(f"{mk} stays {canon}", N(mk) == canon, N(mk))
check("Sprinter blob left alone (feed itself is ambiguous)",
      N("Sprinter (Dodge Or Freightliner)") == "Sprinter (Dodge Or Freightliner)",
      N("Sprinter (Dodge Or Freightliner)"))

# ---- 3. General Motors resolution --------------------------------------------
print("General Motors blob:")
# VIN WMI division coding (char 3 of a [1-3|6]G? VIN names the division).
check("1G1 VIN -> Chevrolet", N("General Motors", "Malibu", "1G1ZD5ST8JF123456") == "Chevrolet")
check("2G1 (Canada) -> Chevrolet", N("General Motors", "Impala", "2G1WB58K081123456") == "Chevrolet")
check("1G2 -> Pontiac", N("General Motors", "G6", "1G2ZG57N984123456") == "Pontiac")
check("1G3 -> Oldsmobile", N("General Motors", "Alero", "1G3NL52E04C123456") == "Oldsmobile")
check("1G4 -> Buick", N("General Motors", "Lesabre", "1G4HP52K14U123456") == "Buick")
check("1G6 -> Cadillac", N("General Motors", "CTS", "1G6DM577940123456") == "Cadillac")
check("1G8 -> Saturn", N("General Motors", "ION", "1G8AJ52F13Z123456") == "Saturn")
check("1GT -> GMC", N("General Motors", "Sierra 1500 Pickup", "1GTEK19B9SE123456") == "GMC")
check("1GK -> GMC", N("General Motors", "Yukon", "1GKEK13Z12R123456") == "GMC")
check("1GC -> Chevrolet (truck)", N("General Motors", "Silverado 1500 Pickup", "1GCEK19T04E123456") == "Chevrolet")
check("1GN -> Chevrolet (SUV)", N("General Motors", "Tahoe", "1GNEK13T2YJ123456") == "Chevrolet")
check("1GY -> Cadillac (SUV)", N("General Motors", "Escalade", "1GYEK63N05R123456") == "Cadillac")
check("KL1 (GM Korea) -> Chevrolet", N("General Motors", "Aveo", "KL1TD56E09B123456") == "Chevrolet")
check("5GA (Lansing) -> Buick", N("General Motors", "Enclave", "5GAKRBED5BJ123456") == "Buick")
check("5Y2 (NUMMI) -> Pontiac", N("General Motors", "Vibe", "5Y2SL65846Z123456") == "Pontiac")
check("5GT -> Hummer", N("General Motors", "Hummer H3", "5GTDN136568123456") == "Hummer")
# VIN wins over a conflicting model string (official division coding).
check("VIN beats model string", N("General Motors", "Sierra 1500", "1GCEK19T04E123456") == "Chevrolet")
# Model evidence when the VIN is missing/foreign.
check("model-first-word division: 'Gmc Terrain' -> GMC", N("General Motors", "Gmc Terrain", "") == "GMC")
check("model-first-word division: 'Oldsmobile Bravada'", N("General Motors", "Oldsmobile Bravada", "") == "Oldsmobile")
check("model-first-word division: 'Saturn Vue'", N("General Motors", "Saturn Vue", "") == "Saturn")
check("exclusive model: Equinox -> Chevrolet (2CN CAMI VIN unmapped)",
      N("General Motors", "Equinox", "2CNDL63F066123456") == "Chevrolet")
check("exclusive model: Rendezvous -> Buick", N("General Motors", "Rendezvous", "") == "Buick")
check("exclusive model: Torrent -> Pontiac", N("General Motors", "Torrent", "") == "Pontiac")
check("exclusive model: Deville -> Cadillac", N("General Motors", "Deville", "") == "Cadillac")
# Year-gated nameplates (Geo through 1997, Chevrolet after).
check("1995 Metro -> Geo", N("General Motors", "Metro", "2C1MR2264S6123456", 1995) == "Geo")
check("1999 Metro -> Chevrolet", N("General Motors", "Metro", "", 1999) == "Chevrolet")
check("1996 Prizm -> Geo", N("General Motors", "Prizm", "", 1996) == "Geo")
check("2000 Tracker -> Chevrolet", N("General Motors", "Tracker", "", 2000) == "Chevrolet")
check("2021 Suburban -> Chevrolet", N("General Motors", "Suburban 1500", "", 2021) == "Chevrolet")
# Ambiguous rows KEEP the corporate label — never guess.
check("1988 Suburban (Chevy AND GMC era, no VIN) stays General Motors",
      N("General Motors", "Suburban 1500", "", 1988) == "General Motors")
check("unknown model + no VIN stays General Motors",
      N("General Motors", "", "") == "General Motors")
check("'Gm' casing variant resolves too", N("GM", "Malibu", "1G1ZD5ST8JF123456") == "Chevrolet")
# A real Chevrolet row never routes through the GM resolver.
check("plain Chevrolet untouched", N("Chevrolet", "Suburban 1500", "", 1988) == "Chevrolet")

# ---- 4. enrich_vehicles end-to-end -------------------------------------------
print("enrich_vehicles:")
vehicles = [
    {"make": "MINI Cooper", "model": "Mini Cooper", "vin": "WMWSV3C59BTY14620", "year": 2011, "dateAdded": ""},
    {"make": "Vw", "model": "Jetta", "vin": "3VWDP7AJ6DM395704", "year": 2013, "dateAdded": ""},
    {"make": "General Motors", "model": "Acadia", "vin": "1GKER13727J123456", "year": 2007, "dateAdded": ""},
    {"make": "Datsun", "model": "280ZX", "vin": "", "year": 1981, "dateAdded": ""},
]
out = js.enrich_vehicles(vehicles)
check("enrich: MINI Cooper -> MINI", out[0]["make"] == "MINI", out[0]["make"])
check("enrich: Vw -> Volkswagen", out[1]["make"] == "Volkswagen", out[1]["make"])
check("enrich: GM + 1GK VIN -> GMC", out[2]["make"] == "GMC", out[2]["make"])
check("enrich: Datsun untouched", out[3]["make"] == "Datsun", out[3]["make"])

print()
if failures:
    print(f"{len(failures)} FAILURE(S): {failures}")
    sys.exit(1)
print("all make-normalization tests passed")
