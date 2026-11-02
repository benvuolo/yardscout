#!/usr/bin/env python3
"""Tests for scraper/ebay_prices.py and the scan's use of its output.

  1. Query cleaning turns DB part labels into eBay keywords.
  2. build_queries covers every (entry, part) once, with fitment year/make/model.
  3. band(): middle half of the asking prices; thin data -> None.
  4. refresh(): stalest first, budget respected, a 429 stops the run and keeps
     what was gathered, thin results are recorded (not retried daily).
  5. match_vehicle ships the live band (src/n) when fresh and plausible, keeps
     the anchor when stale, thin, or wildly off.

Run:  python3 scraper/test_ebay_prices.py   (no network)
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ebay_prices as ep  # noqa: E402

failures = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        failures.append(name)


# 1. query cleaning
check("paren + qualifiers dropped", ep.clean_part_query("Headlights (clear, non-hazed)") == "Headlights",
      ep.clean_part_query("Headlights (clear, non-hazed)"))
check("em-dash note dropped", ep.clean_part_query("315 mm front brakes — calipers + carriers (e36 m3)") == "315 mm front brakes",
      ep.clean_part_query("315 mm front brakes — calipers + carriers (e36 m3)"))
check("slash/plus become spaces, filler dropped",
      ep.clean_part_query("2JZ-GE accessories / harness (SC300)") == "2JZ-GE harness",
      ep.clean_part_query("2JZ-GE accessories / harness (SC300)"))
check("entry_model strips make and gen suffix",
      ep.entry_model({"display": "Toyota 4Runner (3rd gen)", "make": "Toyota"}) == "4Runner")
check("entry_model: first alternative, nickname stripped",
      ep.entry_model({"display": "Audi A4 / Allroad", "make": "Audi"}) == "A4"
      and ep.entry_model({"display": "Chevrolet Chevy Suburban", "make": "Chevrolet"}) == "Suburban"
      and ep.entry_model({"display": "Ram / Dodge Ram Truck", "make": "Ram"}) == "Ram Truck",
      f"{ep.entry_model({'display': 'Ram / Dodge Ram Truck', 'make': 'Ram'})!r}")

# 2. build_queries on a tiny DB with an alias key
shared = {"display": "Toyota 4Runner", "make": "Toyota", "year_range": (1996, 2002), "top_parts": [
    {"name": "TRD Pro Grille", "low": 300, "high": 600, "cost": 40, "yr_min": 2000},
    {"name": "Headlights (clear, non-hazed)", "low": 80, "high": 200, "cost": 20},
]}
db = {"4runner": shared, "4-runner": shared,
      "mr2": {"display": "Toyota MR2", "make": "Toyota", "year_range": (1991, 1995), "top_parts": [
          {"name": "T-Top Glass", "low": 150, "high": 300, "cost": 20}]}}
qs = ep.build_queries(db)
check("one query per part, alias entry not duplicated", len(qs) == 3, str(len(qs)))
grille = next(q for q in qs if q["key"] == "4runner|trd pro grille|2000-2002")
check("key = first dict key | part | year window", grille["key"] == "4runner|trd pro grille|2000-2002")
check("keywords = make model part", grille["q"] == "Toyota 4Runner TRD Pro Grille", grille["q"])
check("fitment year = middle of the part's own range", grille["year"] == 2001 and grille["model"] == "4Runner", str(grille))

# 3. band
check("fewer than MIN_N -> None", ep.band([10, 20, 30, 40]) is None)
b = ep.band([5, 50, 60, 70, 80, 90, 100, 900])  # junk at both ends
check("band is the middle half", b["low"] == 58 and b["high"] == 92 and b["n"] == 8, str(b))
check("zero/negative prices ignored", ep.band([0, -1, 20, 30, 40, 50, 60])["n"] == 5)


# 4. refresh with a fake client
class FakeClient:
    def __init__(self, answers):
        self.answers, self.calls = answers, []

    def search_prices(self, q):
        self.calls.append(q["key"])
        a = self.answers.get(q["key"], [])
        if a == "429":
            raise RuntimeError("eBay search failed: HTTP 429")
        return a, True


now = datetime(2026, 11, 2, tzinfo=timezone.utc)
with tempfile.TemporaryDirectory() as td:
    path = Path(td) / "ebay_prices.json"
    old = (now - timedelta(days=20)).strftime("%Y-%m-%dT%H:%M:%SZ")
    fresh = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    path.write_text(json.dumps({"asOf": old, "parts": {
        "4runner|trd pro grille|2000-2002": {"low": 1, "high": 2, "n": 9, "at": fresh, "q": "x"},
        "mr2|t-top glass|1991-1995": {"low": 1, "high": 2, "n": 9, "at": old, "q": "x"},
    }}))
    fc = FakeClient({"4runner|headlights (clear, non-hazed)|1996-2002": [60, 70, 80, 90, 100, 110],
                     "mr2|t-top glass|1991-1995": [1, 2, 3]})
    data = ep.refresh(fc, qs, path, max_calls=2, now=now, pause=0)
    check("missing entry queried first, then the stalest; fresh one skipped by budget",
          fc.calls == ["4runner|headlights (clear, non-hazed)|1996-2002", "mr2|t-top glass|1991-1995"], str(fc.calls))
    hl = data["parts"]["4runner|headlights (clear, non-hazed)|1996-2002"]
    check("band recorded with count and stamp", hl["low"] == 72 and hl["high"] == 98 and hl["n"] == 6 and hl["at"].startswith("2026-11-02"), str(hl))
    tt = data["parts"]["mr2|t-top glass|1991-1995"]
    check("thin result recorded without a band (so it isn't retried daily)", "low" not in tt and tt["n"] == 3 and tt["at"].startswith("2026-11-02"), str(tt))
    check("untouched entry kept", data["parts"]["4runner|trd pro grille|2000-2002"]["at"] == fresh)
    check("file written", json.loads(path.read_text())["asOf"].startswith("2026-11-02"))

    fc2 = FakeClient({"4runner|trd pro grille|2000-2002": "429"})
    data2 = ep.refresh(fc2, qs, path, max_calls=5, now=now + timedelta(days=30), pause=0)
    check("rate limit stops the run, earlier data kept", "4runner|headlights (clear, non-hazed)|1996-2002" in data2["parts"] and len(fc2.calls) == 1)

# 5. scan integration
import junkyard_scraper as js  # noqa: E402

with tempfile.TemporaryDirectory() as td:
    path = Path(td) / "ebay_prices.json"
    os.environ["YS_EBAY_PRICES_PATH"] = str(path)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    stale = (datetime.now(timezone.utc) - timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%SZ")

    def parts_for(year=2018):
        js._ebay_prices_reset()
        ms = js.match_vehicle(year, "Toyota", "4Runner")
        return {p["name"]: p for m in ms for p in m["top_parts"]}

    # find a 4Runner part that matches a 2018 car and its canonical entry key
    base = parts_for()
    check("baseline: 4Runner parts match without any eBay file", len(base) > 0 and all("src" not in p for p in base.values()))
    name = "TRD Pro Grille" if "TRD Pro Grille" in base else next(iter(base))
    # Every dict key whose entry carries this part: the scraper keys the file
    # by the entry's first dict key, and writing all of them covers aliases.
    keys = [f"{k}|{name.lower()}|{ep.part_window(info, p)[0]}-{ep.part_window(info, p)[1]}"
            for k, info in js.UNOBTANIUM_DB.items() for p in info.get("top_parts", []) if p["name"] == name]
    check("part found in the DB under at least one entry key", len(keys) >= 1)
    def write(rec):
        path.write_text(json.dumps({"parts": {k: dict(rec) for k in keys}}))
    anchor = base[name]

    write({"low": 210, "high": 330, "n": 14, "at": stamp})
    live = parts_for()[name]
    check("fresh band ships as src=ebay with count", live.get("src") == "ebay" and live["low"] == 210 and live["high"] == 330 and live["n"] == 14, str({k: live.get(k) for k in ("src", "low", "high", "n")}))

    write({"low": 210, "high": 330, "n": 14, "at": stale})
    check("stale band ignored", "src" not in parts_for()[name])

    write({"low": 210, "high": 330, "n": 3, "at": stamp})
    check("thin band ignored", "src" not in parts_for()[name])

    write({"low": 5, "high": 9, "n": 40, "at": stamp})
    off = parts_for()[name]
    check("band far below the anchor ignored (keyword collision guard)", "src" not in off and off["low"] == anchor["low"], str(off.get("low")))

    os.environ["YS_EBAY_PRICES"] = "0"
    check("YS_EBAY_PRICES=0 disables", "src" not in parts_for()[name])
    del os.environ["YS_EBAY_PRICES"]
    del os.environ["YS_EBAY_PRICES_PATH"]
    js._ebay_prices_reset()

print("\n" + ("ALL PASS" if not failures else f"{len(failures)} FAILURES: {failures}"))
sys.exit(1 if failures else 0)
