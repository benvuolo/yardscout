#!/usr/bin/env python3
"""Tests for docs/data/junkyards.json (_write_junkyards_json), the aggregate
behind the public /junkyards pages in backend/site-proxy/src/share.js.

Covers:
  1. Per-yard car counts and last-7-days counts (same rule as landed.json).
  2. Page-city fixes: explicit store nicknames ("Chicago North" -> Chicago)
     and the "<City> <suffix>" fold ("Houston SW" -> Houston) only when the
     bare city is also in that state.
  3. newest: dated cars only, newest first, same-day ties by stock number,
     capped at JUNKYARDS_NEWEST_PER_YARD, rows [year, make, model, row, date, key].
  4. stateMakes: top makes set out this week per state.

Run:  python3 scraper/test_junkyards_json.py
"""

import json
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

failures = []


def check(name, cond, detail=""):
    print(("  ok  " if cond else "  FAIL") + f" {name}" + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        failures.append(name)


today = date.today().isoformat()
old = (date.today() - timedelta(days=30)).isoformat()
payload = {
    "scrapedAt": "2026-10-30T11:58:45Z",
    "fields": ["id", "vin", "year", "make", "model", "row", "dateAdded", "yard", "partSet", "maxValue", "premium"],
    "yardFields": ["location", "city", "state", "lat", "lng", "avgLifespanDays", "lifespanBasis"],
    "yards": [
        ["Pick Your Part - Houston SW", "Houston SW", "TX", 29.6, -95.4, 70, "yard"],
        ["Pull-A-Part - Houston", "Houston", "TX", 29.8, -95.3, 60, "yard"],
        ["Pick Your Part - Chicago North", "Chicago North", "IL", 41.9, -87.7, 66, "yard"],
        ["Lake Station U-Pull", "Lake Station", "IN", 41.5, -87.2, 50, "yard"],
    ],
    "vehicles": [
        [1, "VIN1", 2010, "Ford", "F-150", "1", today, 0, 0, 0, 0],
        ["1263-000099", "", 2011, "Honda", "Civic", "2", today, 0, 0, 0, 0],
        ["1263-000100", "", 2012, "Acura", "TL", "3", today, 0, 0, 0, 0],
        [4, "VIN4", 2003, "Ford", "Ranger", "4", old, 0, 0, 0, 0],
        [5, "VIN5", 2004, "Ford", "Focus", "5", "", 0, 0, 0, 0],
        [6, "VIN6", 2005, "Ford", "Taurus", "6", today, 1, 0, 0, 0],
        [7, "VIN7", 2006, "Chevrolet", "Malibu", "7", today, 2, 0, 0, 0],
    ] + [[100 + i, f"VINX{i}", 2000, "Kia", "Rio", "9", today, 3, 0, 0, 0] for i in range(15)],
}

with tempfile.TemporaryDirectory() as tmp:
    js.DATA_DIR = Path(tmp)
    js._write_junkyards_json(payload)
    out = json.loads((Path(tmp) / "junkyards.json").read_text())

y = out["yards"]
check("one row per payload yard, index-aligned", [r[0] for r in y] == [r[0] for r in payload["yards"]])
check("cars on lot counted", [r[5] for r in y] == [5, 1, 1, 15], [r[5] for r in y])
check("last-7-days counted (old + undated excluded)", [r[6] for r in y] == [3, 1, 1, 15], [r[6] for r in y])
check("'Houston SW' folds into Houston", y[0][1] == "Houston", y[0][1])
check("plain city untouched", y[1][1] == "Houston")
check("explicit fix: Chicago North -> Chicago", y[2][1] == "Chicago", y[2][1])
check("no fold without the bare city in the state", y[3][1] == "Lake Station", y[3][1])
check("lat/lng carried", y[0][3] == 29.6 and y[0][4] == -95.4)

n0 = out["newest"][0]
check("undated cars left out of newest", all(r[4] for r in n0) and len(n0) == 4, n0)
check("newest first, same-day ties by stock number", [r[5] for r in n0] == ["1263-000100", "1263-000099", "VIN1", "VIN4"], [r[5] for r in n0])
check("row shape [year, make, model, row, date, key]", n0[0] == [2012, "Acura", "TL", "3", today, "1263-000100"], n0[0])
check("capped per yard", len(out["newest"][3]) == js.JUNKYARDS_NEWEST_PER_YARD, len(out["newest"][3]))

sm = out["stateMakes"]
check("state makes: TX this week", sm.get("TX") == [["Ford", 2], ["Acura", 1], ["Honda", 1]], sm.get("TX"))
check("state makes: one per state", sorted(sm) == ["IL", "IN", "TX"], sorted(sm))
check("scrapedAt + days", out["scrapedAt"] == payload["scrapedAt"] and out["days"] == js.LANDED_DAYS)

print(f"\n{len(failures)} failure(s)" if failures else "\nALL PASS")
sys.exit(1 if failures else 0)
