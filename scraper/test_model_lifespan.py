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
    def add(loc, mk, md, days, n, departed=True, spread=True):
        """n cars that sat `days` on the lot. Departures are spread over n
        distinct scan times (spread=True) like a live feed; spread=False
        drops them all in ONE scan, i.e. a feed flush."""
        global k
        for i in range(n):
            k += 1
            off = timedelta(minutes=i) if spread else timedelta(0)
            rows.append((f"t:{k}", "t", str(k), mk, md, loc, (t0 + off).strftime("%Y-%m-%dT%H:%M:%SZ"),
                         (t0 + off + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ") if departed else None))
    add("Yard A - Town", "Honda", "Civic", 20, 40)          # Civics leave in 20 d at A
    add("Yard A - Town", "Ford", "Taurus", 60, 50)          # Tauruses sit 60 d at A (yard median lands at 40)
    add("Yard A - Town", "Kia", "Rio", 15, 10)              # too few (10 < 15) for a yard+model figure
    add("Yard B - City", "Honda", "Civic", 50, 20)
    add("Yard B - City", "Honda", "Civic", 50, 5, departed=False)  # still on the lot: not counted
    # Yard F - Flush: 40 Civics really left over 40 scans (30 d), then the
    # feed dropped 60 long-listed Tauruses in ONE scan (a frozen list
    # catching up, like Prestige Houston on 2026-10-28). 60/100 >= 40%.
    add("Yard F - Flush", "Honda", "Civic", 30, 40)
    add("Yard F - Flush", "Ford", "Taurus", 300, 60, spread=False)
    add("Yard F - Flush", "Ford", "Taurus", 300, 5, departed=False)
    # Yard S - Stale: 40 departures spread over scans long ago, still listed
    # at the latest scan, no departure for 36+ scans since.
    add("Yard S - Stale", "Honda", "Civic", 10, 40)
    add("Yard S - Stale", "Kia", "Rio", 10, 3, departed=False)
    # Historical spellings frozen in the DB (pre-merge inserts): the writer
    # must fold them into today's canonical key, not count them separately.
    add("Yard A - Town", "FORD", "Taurus", 60, 5)
    add("Yard A - Town", "Ford", "Taurus.", 60, 5)
    con.executemany("INSERT INTO vehicles (key, source, vehicle_id, make, model, location, date_added, departed_at, first_seen, last_seen) "
                    "VALUES (?,?,?,?,?,?,?,?, '2026-08-01T00:00:00Z', '2026-08-02T00:00:00Z')", rows)
    # Scans: one per departure minute of the spread yards (so "scans since
    # last departure" is countable), then 40 more scans with nothing leaving.
    # Yard S's last departure is at t0+10d+39min; Yard F's spread Civics run
    # to t0+30d; the still-listed rows get last_seen = the final scan.
    scan_times = sorted({r[7] for r in rows if r[7]})
    tail_start = max(datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ") for x in scan_times)
    scan_times += [(tail_start + timedelta(hours=4 * j)).strftime("%Y-%m-%dT%H:%M:%SZ") for j in range(1, 41)]
    con.executemany("INSERT INTO scans (scraped_at, total, matches, new_arrivals, departures) VALUES (?,0,0,0,0)",
                    [(x,) for x in scan_times])
    last = scan_times[-1]
    con.execute("UPDATE vehicles SET last_seen = ? WHERE departed_at IS NULL", (last,))
    # Yard B's feed went away after its last departure (not listed at the
    # latest scan), so the stale rule does not apply to it.
    con.execute("UPDATE vehicles SET last_seen = ? WHERE departed_at IS NULL AND location = 'Yard B - City'",
                ((t0 + timedelta(days=50)).strftime("%Y-%m-%dT%H:%M:%SZ"),))
    con.commit(); con.close()

    rel = db.yard_departure_reliability(flush_share=0.4, stale_scans=36)
    check("Yard A reliable (departures spread over scans)", rel["Yard A - Town"]["reliable"], str(rel["Yard A - Town"]))
    check("Yard F unreliable: 60 of 100 departures in one scan", not rel["Yard F - Flush"]["reliable"] and "60 of 100" in rel["Yard F - Flush"]["reason"], str(rel["Yard F - Flush"]))
    check("Yard S unreliable: listed, no departure for 36+ scans", not rel["Yard S - Stale"]["reliable"] and "stopped removing" in rel["Yard S - Stale"]["reason"], str(rel["Yard S - Stale"]))
    check("Yard B reliable: its 20 departures are spread too", rel["Yard B - City"]["reliable"], str(rel["Yard B - City"]))
    excl = {k for k, v in rel.items() if not v["reliable"]}

    st_all = db.model_lifespan_stats()
    check("without exclusion the flush yard's 300 d Tauruses are in the national Taurus median",
          st_all["models"][("Ford", "Taurus")][1] == 110, str(st_all["models"].get(("Ford", "Taurus"))))
    st = db.model_lifespan_stats(exclude=excl)
    check("excluded yards drop out of national model medians (Taurus: A's 50+5+5 historical-spelling rows only)",
          st["models"][("Ford", "Taurus")][1] == 50 and ("FORD", "Taurus") in st["models"], str(st["models"].get(("Ford", "Taurus"))))
    check("excluded yards have no yard entry", "Yard F - Flush" not in st["yards"] and "Yard S - Stale" not in st["yards"])
    ls = db.lifespan_stats(exclude=excl)
    check("lifespan_stats (yard averages) excludes them too", "Yard F - Flush" not in ls["yards"] and ls["global"][1] == 130, str(ls["global"]))
    st = db.model_lifespan_stats(exclude=excl, normalize=js._lifespan_canon_factory(db))
    check("normalize callback folds 'FORD|Taurus' and 'Ford|Taurus.' into Ford|Taurus (n=60)",
          st["models"][("Ford", "Taurus")] == (60.0, 60) and ("FORD", "Taurus") not in st["models"], str(st["models"].get(("Ford", "Taurus"))))
    st = db.model_lifespan_stats(exclude=excl)
    check("global median over all departed (A 110 + B 20; F and S excluded)", st["global"][1] == 130 and 20 <= st["global"][0] <= 60, str(st["global"]))
    check("Civic national median (A 20 d x40 + B 50 d x20) = 20", st["models"][("Honda", "Civic")] == (20.0, 60), str(st["models"].get(("Honda", "Civic"))))
    check("Civic at Yard A = 20 d, n=40", st["yard_models"][("Yard A - Town", "Honda", "Civic")] == (20.0, 40))
    check("Yard A median across all its cars (10x15, 40x20, 60x60 -> 60)", st["yards"]["Yard A - Town"] == (60.0, 110), str(st["yards"]["Yard A - Town"]))
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
    check("Yard A's Taurus median counts the historical spellings (n=60)", ya["models"]["Ford|Taurus"] == [60, 60], str(ya["models"]))
    yf = out["yards"]["Yard F - Flush"]
    check("flush yard ships typical=null, no models, and the reason", yf["typical"] is None and yf["models"] == {} and "one scan" in yf["unreliable"], str(yf))
    ys = out["yards"]["Yard S - Stale"]
    check("stale yard ships typical=null, no models, and the reason", ys["typical"] is None and ys["models"] == {} and "stopped removing" in ys["unreliable"], str(ys))
    check("rule thresholds published with the file", out["unreliableRule"] == {"flushShare": js.LIFESPAN_FLUSH_SHARE, "staleScans": js.LIFESPAN_STALE_SCANS})
    check("global median excludes the flush yard (would be ~60 with 60 x 300 d in it)", out["global"] <= 60, str(out["global"]))

    # The inventory payload's per-yard crush-risk column: excluded yards get
    # null, NOT the chain/global fallback.
    look = js._yard_lifespan_lookup()
    check("lookup: flush yard -> None (no fallback)", "Yard F - Flush" in look and look["Yard F - Flush"] is None, str(look.get("Yard F - Flush")))
    check("lookup: Yard A keeps its own figure", look["Yard A - Town"] is not None and look["Yard A - Town"][1] == "yard", str(look.get("Yard A - Town")))
    payload = js.compact_inventory_v2([
        {"id": 1, "location": "Yard F - Flush", "city": "X", "state": "TX", "lat": 1, "lng": 2, "topParts": []},
        {"id": 2, "location": "Yard A - Town", "city": "Y", "state": "TX", "lat": 1, "lng": 2, "topParts": []},
        {"id": 3, "location": "Yard A - Elsewhere", "city": "Z", "state": "TX", "lat": 1, "lng": 2, "topParts": []},
    ])
    ycol = {y[0]: (y[5], y[6]) for y in payload["yards"]}
    check("payload: flush yard avgLifespanDays/basis are null", ycol["Yard F - Flush"] == (None, None), str(ycol))
    check("payload: healthy yard carries its yard figure", ycol["Yard A - Town"][1] == "yard", str(ycol))
    check("payload: an unknown yard still gets the chain fallback (Yard A chain)", ycol["Yard A - Elsewhere"][1] == "chain", str(ycol))

    # too little history -> no file
    db.DB_FILE = Path(td) / "empty.db"
    (Path(td) / "model_lifespan.json").unlink()
    js._write_model_lifespan_json("x")
    check("too little history: no file written", not (Path(td) / "model_lifespan.json").exists())

print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILURES"))
sys.exit(1 if fails else 0)
