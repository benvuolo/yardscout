#!/usr/bin/env python3
"""Tests for dateAdded sanity clamping (owner-reported 2026-10-21: Fenix
epoch-placeholder rows shipped as dateAdded 2070-01-01 and the app showed
them as 'Set out Jan 1 · fresh' + NEW at Moultrie).

Covers:
  1. _fenix_parse_date — MM/DD/YY windowing: 70 -> 1970 (epoch placeholder),
     not 2070; 4-digit years pass through; garbage -> "".
  2. _sanitize_date_added — the global clamp every adapter funnels through in
     enrich_vehicles: future beyond UTC-tomorrow or older than ~15 years ->
     "" (the schema's unknown-date convention); legit dates untouched,
     including UTC-tomorrow (East Coast yards date in UTC).
  3. enrich_vehicles applies the clamp end-to-end on a vehicle dict.

Run:  python3 scraper/test_date_sanity.py
"""

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js

failures = []


def check(name, cond, detail=""):
    print(("  ok  " if cond else "  FAIL") + f" {name}" + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        failures.append(name)


# ---- 1. Fenix MM/DD/YY windowing --------------------------------------------
print("_fenix_parse_date:")
F = js._fenix_parse_date
check("epoch placeholder 01/01/70 -> 1970 (not 2070)", F("01/01/70") == "1970-01-01", F("01/01/70"))
check("normal date 10/15/26 -> 2026", F("10/15/26") == "2026-10-15", F("10/15/26"))
check("boundary 69 -> 1969", F("06/01/69") == "1969-06-01", F("06/01/69"))
check("boundary 68 -> 2068", F("06/01/68") == "2068-06-01", F("06/01/68"))
check("4-digit year passthrough", F("01/25/2017") == "2017-01-25", F("01/25/2017"))
check("garbage -> ''", F("yesterday") == "", F("yesterday"))
check("empty -> ''", F("") == "")

# ---- 2. global clamp ---------------------------------------------------------
print("_sanitize_date_added:")
S = js._sanitize_date_added
TODAY = date(2026, 10, 21)  # fixed 'UTC today' so the cases never rot


def iso(d):
    return d.strftime("%Y-%m-%d")


check("2070-01-01 (the production bug) -> unknown", S("2070-01-01", TODAY) == "")
check("0000-00-00 (Pull-N-Save placeholder) -> unknown", S("0000-00-00", TODAY) == "")
check("1970-01-01 (windowed epoch) -> unknown", S("1970-01-01", TODAY) == "")
check("today kept", S(iso(TODAY), TODAY) == iso(TODAY))
check("UTC-tomorrow kept (East Coast yards date in UTC)",
      S(iso(TODAY + timedelta(days=1)), TODAY) == iso(TODAY + timedelta(days=1)))
check("+2 days -> unknown", S(iso(TODAY + timedelta(days=2)), TODAY) == "")
check("14 years ago kept",
      S(iso(TODAY - timedelta(days=14 * 365)), TODAY) == iso(TODAY - timedelta(days=14 * 365)))
check("16 years ago -> unknown", S(iso(TODAY - timedelta(days=16 * 365)), TODAY) == "")
check("empty stays empty", S("", TODAY) == "")
check("None-ish stays empty", S(None, TODAY) == "")
check("non-date garbage -> unknown", S("not-a-date", TODAY) == "")
check("invalid calendar date -> unknown", S("2026-02-30", TODAY) == "")
check("ISO timestamp truncated to date and kept",
      S(iso(TODAY) + "T14:02:00Z", TODAY) == iso(TODAY))
check("default today (no arg) accepts a current date", S(iso(TODAY), None) in ("", iso(TODAY)))

# ---- 3. end-to-end through enrich_vehicles -----------------------------------
print("enrich_vehicles applies the clamp:")
vehicles = [
    {"id": "fenix-306060864", "vin": "", "year": 1986, "make": "Ford",
     "model": "Mustang", "row": "0", "dateAdded": "2070-01-01",
     "_location": "Fenix U-Pull - Moultrie", "_source": "fenix"},
    {"id": "ok-1", "vin": "", "year": 2003, "make": "Ford",
     "model": "Windstar", "row": "24", "dateAdded": "2017-01-25",
     "_location": "Fenix U-Pull - Moultrie", "_source": "fenix"},
]
out = js.enrich_vehicles(vehicles)
check("2070 vehicle -> unknown date", out[0]["dateAdded"] == "", out[0]["dateAdded"])
check("legit 2017 vehicle untouched", out[1]["dateAdded"] == "2017-01-25", out[1]["dateAdded"])

# ------------------------------------------------------------------------------
print()
if failures:
    print(f"{len(failures)} FAILURE(S): {failures}")
    sys.exit(1)
print("All date-sanity tests passed.")
