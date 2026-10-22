#!/usr/bin/env python3
"""Tests for the 2026-10 consensus-evergreens taxonomy expansion.

Covers:
  1. Every _EVERGREEN_TARGET_KEYS entry exists (rename guard — the apply loop
     fails loud, this test names the key).
  2. Token dedupe worked: no entry carries two parts of the same evergreen
     category (hand-tuned bands must win, not duplicate).
  3. Price sanity on every evergreen part: 0 < cost < low < high.
  4. Airbag ban: NO part name anywhere in the merged DB mentions an airbag
     (eBay sitewide ban 2026-09-24 + 49 U.S.C. 30122). Steering wheels are
     pre-airbag-era year-gated.
  5. match_vehicle spot checks: a base commuter now matches the evergreens
     and its max_value reflects a confirmed (un-gated) part; option-flagged
     manual tow mirrors stay "unconfirmed" and contribute $0.
  6. SELL_GUIDE coverage: each new category resolves to its honesty note,
     not the generic fallback.

Run:  python3 scraper/test_consensus_parts.py
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


# ---- 1. target keys exist ------------------------------------------------
print("target keys:")
missing = [k for k in js._EVERGREEN_TARGET_KEYS if k not in js.UNOBTANIUM_DB]
check("all evergreen target keys exist", not missing, str(missing))

# ---- 2. no duplicate category per entry ----------------------------------
# An EVERGREEN part must never coexist with another part of its category in
# the same entry (the token dedupe should have skipped it). Entries that were
# hand-split per generation BEFORE this expansion (e.g. BMW per-gen clusters)
# legitimately carry several distinct names of one category — only flag when
# one of them is the evergreen name itself.
print("category dedupe:")
dupes = []
seen_ids = set()
for key, info in js.UNOBTANIUM_DB.items():
    if id(info) in seen_ids:
        continue
    seen_ids.add(id(info))
    names = {p["name"].lower() for p in info["top_parts"]}
    for part, tokens in js._EVERGREEN_PARTS:
        ev = part["name"].lower()
        if ev not in names:
            continue
        others = [n for n in names if n != ev and any(t in n for t in tokens)]
        if others:
            dupes.append(f"{key}: {ev!r} + {sorted(others)}")
check("evergreen part never coexists with a hand-tuned same-category part",
      not dupes, "; ".join(dupes[:5]))

# ---- 3. price sanity -----------------------------------------------------
print("price sanity:")
bad = []
for part, _tokens in js._EVERGREEN_PARTS:
    if not (0 < part["cost"] < part["low"] < part["high"]):
        bad.append(part["name"])
check("evergreen bands sane (0 < cost < low < high)", not bad, str(bad))

# ---- 4. airbag ban -------------------------------------------------------
print("airbag ban:")
rx_bag = re.compile(r"air\s*bag", re.IGNORECASE)
offenders = []
seen_ids = set()
for key, info in js.UNOBTANIUM_DB.items():
    if id(info) in seen_ids:
        continue
    seen_ids.add(id(info))
    for p in info["top_parts"]:
        # Air *suspension* bags are chassis springs, not SRS, and "pre-airbag"
        # explicitly denotes the wheel ships WITHOUT one — both allowed.
        scrub = p["name"].lower().replace("pre-airbag", "")
        if rx_bag.search(scrub) and "suspension" not in scrub:
            offenders.append(f"{key}: {p['name']}")
check("no SRS airbag part anywhere in the DB", not offenders, "; ".join(offenders[:5]))
sw = [p for p in js.UNOBTANIUM_DB["f-150 1980-1996"]["top_parts"]
      if "pre-airbag" in p["name"].lower()]
check("pre-airbag steering wheel is year-gated", bool(sw) and sw[0].get("yr_max", 9999) <= 1993,
      str(sw))

# ---- 5. match_vehicle spot checks ----------------------------------------
print("match spot checks:")


def names_for(year, make, model):
    ms = js.match_vehicle(year, make, model)
    return ms, sorted({p["name"] for m in ms for p in m["top_parts"]})


ms, names = names_for(2012, "Ford", "Focus")
check("2012 Focus gets alternator", any("Alternator" in n for n in names), str(names))
check("2012 Focus gets gauge cluster", any("Gauge Cluster" in n for n in names), str(names))
mv = max((m["max_value"] for m in ms), default=0)
check("2012 Focus max_value rose past headlight-only ($70)", mv > 70, f"max_value={mv}")

ms, names = names_for(1999, "Ford", "F-150")
tow = [p for m in ms for p in m["top_parts"] if "Tow Mirrors (manual" in p["name"]]
check("1999 F-150 offers manual tow mirrors", bool(tow), str(names))
check("manual tow mirrors are 'if equipped' (option gate)",
      all(p.get("trim_status") == "unconfirmed" for p in tow), str(tow[:1]))

ms, _ = names_for(2015, "Toyota", "Camry")
alts = [p["name"] for m in ms for p in m["top_parts"] if "alternator" in p["name"].lower()]
check("Camry alternator not duplicated by evergreens", len(alts) == 1, str(alts))

ms, names = names_for(2001, "Dodge", "Ram 1500")
clus = [p["name"] for m in ms for p in m["top_parts"] if "gauge cluster" in p["name"].lower()]
check("Ram keeps its hand-tuned Gauge Cluster only", len(set(clus)) == 1, str(set(clus)))

ms, names = names_for(1990, "Ford", "F-150")
check("1990 F-150 gets pre-airbag steering wheel",
      any("Steering Wheel (pre-airbag" in n for n in names), str(names))
ms, names = names_for(1996, "Ford", "F-150")
check("1996 F-150 (airbag era) does NOT get the wheel",
      not any("Steering Wheel (pre-airbag" in n for n in names), str(names))

# ---- 6. sell-guide coverage ----------------------------------------------
print("sell guide:")
for pname, frag in [
    ("Starter (verify part number)", "battery"),
    ("Gauge Cluster", "mileage"),
    ("Climate Control Panel (works, knobs intact)", "button"),
    ("Power Window Master Switch", "window"),
    ("Engine/Body Control Module (match part #)", "part number"),
    ("Steering Wheel (pre-airbag era)", "airbag"),
]:
    info = js._lookup_sell_info(pname)
    check(f"sell note for {pname!r}", frag in info["sell_notes"].lower(),
          str(info))
    check(f"speed set for {pname!r}", info["sell_speed"] in ("Fast", "Medium", "Slow"))

# ---------------------------------------------------------------------------
print()
if failures:
    print(f"{len(failures)} FAILURE(S): {failures}")
    sys.exit(1)
print("All consensus-parts tests passed.")
