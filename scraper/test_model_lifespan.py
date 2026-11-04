#!/usr/bin/env python3
"""Per-model lot lifespans: db.model_lifespan_stats + _write_model_lifespan_json.
Run:  python3 scraper/test_model_lifespan.py   (temp DB, offline)"""
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db  # noqa: E402
import junkyard_scraper as js  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        fails.append(name)


with tempfile.TemporaryDirectory() as td:
    db.DB_FILE = Path(td) / "h.db"
    con = db._connect()
    rows = []
    k = 0
    from datetime import datetime, timedelta
    t0 = datetime(2026, 8, 1, 12, 0)
    def add(loc, mk, md, days, n, departed=True):
        global k
        for i in range(n):
            k += 1
            rows.append((f"t:{k}", "t", str(k), mk, md, loc, t0.strftime("%Y-%m-%dT%H:%M:%SZ"),
                         (t0 + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ") if departed else None))
    add("Yard A - Town", "Honda", "Civic", 20, 40)          # Civics leave in 20 d at A
    add("Yard A - Town", "Ford", "Taurus", 60, 50)          # Tauruses sit 60 d at A (yard median lands at 40)
    add("Yard A - Town", "Kia", "Rio", 15, 10)              # too few (10 < 15) for a yard+model figure
    add("Yard B - City", "Honda", "Civic", 50, 20)
    add("Yard B - City", "Honda", "Civic", 50, 5, departed=False)  # still on the lot: not counted
    con.executemany("INSERT INTO vehicles (key, source, vehicle_id, make, model, location, date_added, departed_at, first_seen, last_seen) "
                    "VALUES (?,?,?,?,?,?,?,?, '2026-08-01T00:00:00Z', '2026-08-02T00:00:00Z')", rows)
    con.commit(); con.close()

    st = db.model_lifespan_stats()
    check("global median over all departed", st["global"][1] == 120 and 20 <= st["global"][0] <= 60, str(st["global"]))
    check("Civic national median (A 20 d x40 + B 50 d x20) = 20", st["models"][("Honda", "Civic")] == (20.0, 60), str(st["models"].get(("Honda", "Civic"))))
    check("Civic at Yard A = 20 d, n=40", st["yard_models"][("Yard A - Town", "Honda", "Civic")] == (20.0, 40))
    check("Yard A median across all its cars", st["yards"]["Yard A - Town"] == (40.0, 100))
    check("undeparted cars are not counted", st["yard_models"][("Yard B - City", "Honda", "Civic")][1] == 20)

    js.DATA_DIR = Path(td)
    js._write_model_lifespan_json("2026-11-04T00:00:00Z")
    out = json.loads((Path(td) / "model_lifespan.json").read_text())
    check("file written with scrapedAt + global", out["scrapedAt"].startswith("2026-11-04") and out["global"] > 0)
    check("national model needs 25+: Civic in, Rio (10) out", "Honda|Civic" in out["models"] and "Kia|Rio" not in out["models"])
    ya = out["yards"]["Yard A - Town"]
    check("yard+model needs 15+: Civic and Taurus in, Rio out", set(ya["models"]) == {"Honda|Civic", "Ford|Taurus"}, str(ya["models"]))
    check("yard typical (median) present when the yard has 30+ departures", ya["typical"] is not None and 20 <= ya["typical"] <= 60, str(ya["typical"]))
    check("Civic at A: 20 d, 40 departures", ya["models"]["Honda|Civic"] == [20, 40])
    check("Civic at A leaves fast (<= 0.7 x yard typical)", ya["models"]["Honda|Civic"][0] <= 0.7 * ya["typical"])
    check("Yard B typical None (only 20 departures)", out["yards"]["Yard B - City"]["typical"] is None)

    # too little history -> no file
    db.DB_FILE = Path(td) / "empty.db"
    (Path(td) / "model_lifespan.json").unlink()
    js._write_model_lifespan_json("x")
    check("too little history: no file written", not (Path(td) / "model_lifespan.json").exists())

print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILURES"))
sys.exit(1 if fails else 0)
