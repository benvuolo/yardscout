#!/usr/bin/env python3
"""Tests for price-list part-name sanity (owner-reported 2026-10-21: the
Yards-tab parts picker showed part 'names' that were actually prices — '5.00',
'6.00', '7.00'. Culprit: Barry's U Pull It's /part-pricing/ table ships a few
TOOLS-section rows with the price in the description cell, e.g.
<td>5.00</td><td>5.00</td><td>Each</td><td>0.00</td> — a data-entry hole in
the SOURCE table. The frontend filtered them display-side (535c604); the
parser must drop them so the published data itself is clean).

Covers:
  1. _PRICE_AS_NAME_RE — classifies price-like strings vs real part names
     (including names that merely START with digits, like 16" wheels).
  2. _barrys_parse_pricing_rows — end-to-end on a synthetic table: price-named
     rows dropped, real rows kept with correct price/core/total, dupes folded,
     short/garbage rows skipped.

Run:  python3 scraper/test_price_name_sanity.py
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


# ---- 1. price-like-name classifier -------------------------------------------
print("_PRICE_AS_NAME_RE:")
R = js._PRICE_AS_NAME_RE
for junk in ("5.00", "7.00", "4.00", "6.00", "3.00", "191.00", "$12.50",
             "1,234.00", "12", ".50", "5.00 - 7.00"):
    check(f"price-like {junk!r} matches", bool(R.match(junk)))
for real in ("TIMING GEAR", "ENGINE (NO ACC)", '16"- WHEEL STEEL',
             "3RD BRAKE LAMP", "A/C COMPRESSOR", "4X4 ACTUATOR",
             "2 DR WINDOW REGULATOR", "V8 ENGINE"):
    check(f"real name {real!r} passes", not R.match(real))

# ---- 2. end-to-end table parse ------------------------------------------------
print("_barrys_parse_pricing_rows:")


def tr(*cells):
    return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"


page = "<table>" + "".join([
    "<tr><th>Description</th><th>Price</th><th>Unit</th><th>Core</th></tr>",
    tr('<span style="font-weight:bold">TIMING GEAR</span>', "7.00", "Each", "0.00"),
    tr("BLUE TOOLS", "7.00", "Each", "0.00"),
    tr("5.00", "5.00", "Each", "0.00"),        # the production bug rows
    tr("7.00", "7.00", "Each", "0.00"),
    tr("$4.00", "4.00", "Each", "0.00"),
    tr("ENGINE (NO ACC)", "191.00", "Each", "46.00"),
    tr("TIMING GEAR", "9.99", "Each", "0.00"),  # dupe name — first row wins
    tr("A/C COMPRESSOR", "not-a-price", "Each", "0.00"),  # unparseable price
    tr("ONLY TWO CELLS", "1.00"),               # short row
    tr('16"- WHEEL STEEL', "23.99", "Each", "5.00"),
]) + "</table>"

parts = js._barrys_parse_pricing_rows(page)
by_name = {p["description"]: p for p in parts}

check("price-named rows dropped",
      not any(js._PRICE_AS_NAME_RE.match(p["description"]) for p in parts),
      str(sorted(by_name)))
check("4 real parts kept", len(parts) == 4, str(sorted(by_name)))
check("markup stripped from description", "TIMING GEAR" in by_name, str(sorted(by_name)))
check("dupe folded to first price", by_name.get("TIMING GEAR", {}).get("price") == "7.00")
check("engine price + core -> total",
      by_name.get("ENGINE (NO ACC)", {}).get("totalPrice") == "237.00",
      str(by_name.get("ENGINE (NO ACC)")))
check("digit-leading real name kept", '16"- WHEEL STEEL' in by_name)
check("wheel core parsed", by_name.get('16"- WHEEL STEEL', {}).get("corePrice") == "5.00")
check("unparseable price row skipped", "A/C COMPRESSOR" not in by_name)

# ------------------------------------------------------------------------------
print()
if failures:
    print(f"{len(failures)} FAILURE(S): {failures}")
    sys.exit(1)
print("All price-name sanity tests passed.")
