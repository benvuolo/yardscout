#!/usr/bin/env python3
"""Arrivals history: db.arrival_history + _write_arrivals_json / _safe.
Run:  python3 scraper/test_arrivals.py   (temp DB and temp data dir, offline)

Scan time 2026-11-19T07:00:00Z -> window 2026-09-24 .. 2026-11-18,
week 1 = 09-24..09-30, week 8 = 11-12..11-18."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db  # noqa: E402
import junkyard_scraper as js  # noqa: E402

fails = []
passes = 0


def check(name, ok, detail=""):
    global passes
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if ok:
        passes += 1
    else:
        fails.append(name)


NOW = "2026-11-19T07:00:00Z"
rows = []
k = 0


def car(loc, fs, da="", mk="Honda", md="Civic", year=2005, departed=None, vin=""):
    global k
    k += 1
    rows.append((f"t:{k}", "t", str(k), vin, year, mk, md, loc, da, fs, fs, departed))


def scan(day, hour=10):
    return f"2026-{day}T{hour:02d}:00:00Z"


# Yard A: seen since 09-01 (cold-start cars that day), fully covered.
for _ in range(5):
    car("Yard A - Town", scan("09-01"), "2026-06-01")
# _arrival_day rules (Civic 2005 unless noted)
car("Yard A - Town", scan("10-01"), "2026-10-01")                 # same day -> w2
car("Yard A - Town", scan("10-01"), "2026-10-02")                 # fs+1 -> used: 10-02 w2
car("Yard A - Town", scan("10-07"), "2026-10-09")                 # fs+2 -> fs 10-07 w2
car("Yard A - Town", scan("10-18"), "2026-10-08")                 # fs-10 -> used 10-08 w3
car("Yard A - Town", scan("10-19"), "2026-10-08")                 # fs-11 -> relist, not counted
car("Yard A - Town", scan("10-15"), "")                           # none -> fs 10-15 w4
car("Yard A - Town", scan("10-16"), "N/A")                        # garbage -> fs 10-16 w4
car("Yard A - Town", scan("10-17"), "2026-02-30")                 # impossible date -> fs 10-17 w4
# window edges
car("Yard A - Town", scan("09-24"), "2026-09-24")                 # first day -> w1
car("Yard A - Town", scan("09-24"), "2026-09-23")                 # day before window: out
car("Yard A - Town", scan("11-18", 22), "2026-11-18")             # last day -> w8
car("Yard A - Town", scan("11-19", 3), "2026-11-19")              # scan day: out
car("Yard A - Town", scan("11-18", 22), "2026-11-19")             # fs+1 = 11-19: out
car("Yard A - Town", scan("09-23", 23), "2026-09-24")             # fs 09-23 but dated 09-24: in, w1
# normalization: historical spellings fold into today's keys; years kept
car("Yard A - Town", scan("11-13"), "2026-11-13", mk="FORD", md="Taurus", year=2001)
car("Yard A - Town", scan("11-13"), "2026-11-13", mk="Ford", md="Taurus.", year=2001)
car("Yard A - Town", scan("11-13"), "2026-11-13", mk="Ford", md="Taurus", year=2003)
car("Yard A - Town", scan("11-14"), "2026-11-14", mk="Ford", md="Taurus", year=2003, departed=scan("11-16"))  # departed still counts

# Yard P: first scan 10-21 -> coverage from 10-22: weeks 5..8 (4 covered).
for _ in range(3):
    car("Yard P - Partial", scan("10-21"), "2026-10-20")         # cold start
car("Yard P - Partial", scan("10-21", 18), "2026-10-21")          # later scan, same day: before coverage
car("Yard P - Partial", scan("10-23"), "2026-10-23")              # w5, inside coverage... w5 starts 10-22
car("Yard P - Partial", scan("10-23"), "2026-10-15")              # arrival 10-15 is w4: outside coverage
car("Yard P - Partial", scan("11-12"), "2026-11-12")              # w8

# Yard F: 100 on the lot from 09-01; a 60-car scan on 11-05 (list after = 160,
# 35% = 56 -> flush, none count); a 45-car scan on 11-06 (list 205 -> 71.75: counts).
for _ in range(100):
    car("Yard F - Flush", scan("09-01"), "2026-08-01")
for _ in range(60):
    car("Yard F - Flush", scan("11-05"), "2026-11-05", md="Accord")
for _ in range(45):
    car("Yard F - Flush", scan("11-06"), "2026-11-06", md="Fit")
# Small yard: 41 new cars on a list of 10 -> 41 > max(40, 17.9): flush.
for _ in range(10):
    car("Yard G - Small", scan("09-01"), "2026-08-01")
for _ in range(41):
    car("Yard G - Small", scan("10-02"), "2026-10-02", md="Pilot")
# ... and exactly 40 new cars on a small list: not more than 40, counts.
for _ in range(40):
    car("Yard G - Small", scan("10-09"), "2026-10-09", md="Odyssey")

# Yard Z: frozen list (payload listState) -> stale = 1, rows still written.
car("Yard Z - Frozen", scan("09-01"), "2026-08-01")
car("Yard Z - Frozen", scan("10-05"), "2026-10-05")
# Yard J: listFlushAt names the 11-10 scan (a list jump): those cars do not count.
car("Yard J - Jump", scan("09-01"), "2026-08-01")
car("Yard J - Jump", scan("11-10"), "2026-11-10", md="CR-V")
car("Yard J - Jump", scan("11-11"), "2026-11-11", md="CR-V")
# Yard N: first seen 11-10 -> coverage 11-11 -> only week 8.
car("Yard N - New", scan("11-10"), "2026-11-10")
car("Yard N - New", scan("11-13"), "2026-11-13")
# Yard X: in the DB but not in this scan's inventory: not written.
car("Yard X - Gone", scan("09-01"), "2026-08-01")
car("Yard X - Gone", scan("10-10"), "2026-10-10")

YF = ["location", "city", "state", "lat", "lng", "avgLifespanDays", "lifespanBasis",
      "listChangedAt", "listState", "listReadAt", "listFlushAt"]


def yard(loc, lat, lng, state="", flush=None):
    return [loc, "C", "UT", lat, lng, 60, "yard", "2026-11-18T10:00:00Z", state, None, flush]


payload = {"scrapedAt": NOW, "yardFields": YF, "yards": [
    yard("Yard A - Town", 40.7, -111.9),
    yard("Yard P - Partial", 40.8, -111.9),
    yard("Yard F - Flush", 41.0, -112.0),
    yard("Yard G - Small", 41.1, -112.0),
    yard("Yard Z - Frozen", 41.2, -112.0, state="frozen"),
    yard("Yard J - Jump", 41.3, -112.0, flush=scan("11-10")),
    yard("Yard N - New", 41.4, -112.0),
    yard("Yard Q - No history", None, None),
]}

with tempfile.TemporaryDirectory() as td:
    db.DB_FILE = Path(td) / "h.db"
    js.DATA_DIR = Path(td) / "data"
    js.DATA_DIR.mkdir()
    con = db._connect()
    con.executemany("INSERT INTO vehicles (key, source, vehicle_id, vin, year, make, model, location, "
                    "date_added, first_seen, last_seen, departed_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    con.commit()
    con.close()

    # ---- _arrival_day unit ----
    from datetime import date
    ad = js._arrival_day
    check("arrival day: date_added same day", ad("2026-10-01", "2026-10-01T10:00:00Z") == date(2026, 10, 1))
    check("arrival day: fs+1 used", ad("2026-10-02", "2026-10-01T23:00:00Z") == date(2026, 10, 2))
    check("arrival day: fs+2 -> first_seen", ad("2026-10-03", "2026-10-01T10:00:00Z") == date(2026, 10, 1))
    check("arrival day: fs-10 used", ad("2026-09-21", "2026-10-01T10:00:00Z") == date(2026, 9, 21))
    check("arrival day: fs-11 is a relist (None)", ad("2026-09-20", "2026-10-01T10:00:00Z") is None)
    check("arrival day: blank -> first_seen", ad("", "2026-10-01T10:00:00Z") == date(2026, 10, 1))
    check("arrival day: None -> first_seen", ad(None, "2026-10-01T10:00:00Z") == date(2026, 10, 1))
    check("arrival day: timestamp date_added uses its day", ad("2026-09-30T18:00:00", "2026-10-01T10:00:00Z") == date(2026, 9, 30))

    # ---- db.arrival_history ----
    h = db.arrival_history("2026-09-23", scan_group_floor=40)
    check("history: first scan per yard", h["first_scan"]["Yard P - Partial"] == scan("10-21")
          and h["first_scan"]["Yard A - Town"] == scan("09-01"), str(h["first_scan"]))
    check("history: rows start at first_seen_from", all(r[6] >= "2026-09-23" for r in h["rows"]))
    check("history: flush group sized (60 new, 160 listed)", h["scan_groups"].get(("Yard F - Flush", scan("11-05"))) == (60, 160),
          str(h["scan_groups"]))
    check("history: 45-car group sized (listed 205)", h["scan_groups"].get(("Yard F - Flush", scan("11-06"))) == (45, 205))
    check("history: groups at or under the floor are not sized", ("Yard G - Small", scan("10-09")) not in h["scan_groups"])

    # ---- full writer ----
    info = js._write_arrivals_json(payload, now=NOW)
    out = js.DATA_DIR / "arrivals"
    idx = json.loads((out / "index.json").read_text())
    honda = json.loads((out / "honda.json").read_text())
    ford = json.loads((out / "ford.json").read_text())
    check("index: window", idx["windowStart"] == "2026-09-24" and idx["windowEnd"] == "2026-11-18" and idx["weeks"] == 8, str(idx)[:200])
    check("index: builtAt is the scan time", idx["builtAt"] == NOW)
    Y = {y[0]: (i, y) for i, y in enumerate(idx["yards"])}
    check("index: every inventory yard, payload order", [y[0] for y in idx["yards"]] == [y[0] for y in payload["yards"]])
    check("index: yard row shape [name, lat, lng, covered, stale]", Y["Yard A - Town"][1] == ["Yard A - Town", 40.7, -111.9, 8, 0], str(Y["Yard A - Town"]))
    check("coverage: partial yard covers weeks 5..8", Y["Yard P - Partial"][1][3] == 4, str(Y["Yard P - Partial"]))
    check("coverage: yard first seen 11-10 covers 1 week", Y["Yard N - New"][1][3] == 1, str(Y["Yard N - New"]))
    check("coverage: yard with no history covers 0", Y["Yard Q - No history"][1][3] == 0 and Y["Yard Q - No history"][1][1] is None)
    check("stale: frozen yard marked", Y["Yard Z - Frozen"][1][4] == 1 and Y["Yard A - Town"][1][4] == 0)
    check("index: gone yard not listed", "Yard X - Gone" not in Y)
    check("index: makes with slugs", idx["makes"].get("Honda", [None])[0] == "honda" and idx["makes"].get("Ford", [None])[0] == "ford", str(idx["makes"]))

    def rowsof(f, model, yname):
        yi = Y[yname][0]
        return {r[1]: r[2:] for r in f["models"].get(model, []) if r[0] == yi}

    a = rowsof(honda, "Civic", "Yard A - Town")
    # w1: 09-24 + 09-24(fs 09-23) = 2; w2: 10-01, 10-02, 10-07 = 3; w3: 10-08 = 1;
    # w4: 10-15, 10-16, 10-17 = 3; w8: 11-18 = 1. Relist, 09-23, 11-19 x2 out.
    check("Yard A Civic weekly counts (date rules, relist, both edges)", a.get(2005) == [2, 3, 1, 3, 0, 0, 0, 1], str(a))
    p = rowsof(honda, "Civic", "Yard P - Partial")
    check("partial coverage: only covered-week arrivals written", p.get(2005) == [0, 0, 0, 0, 1, 0, 0, 1], str(p))
    check("flush scan excluded (60 Accords in one scan)", not rowsof(honda, "Accord", "Yard F - Flush"), str(rowsof(honda, "Accord", "Yard F - Flush")))
    check("non-flush big scan counted (45 Fits, w7)", rowsof(honda, "Fit", "Yard F - Flush").get(2005) == [0, 0, 0, 0, 0, 0, 45, 0])
    check("small list: 41 new on 10 is a flush", not rowsof(honda, "Pilot", "Yard G - Small"))
    check("small list: exactly 40 new counts (floor)", rowsof(honda, "Odyssey", "Yard G - Small").get(2005) == [0, 0, 40, 0, 0, 0, 0, 0])
    check("cold-start cars never count", sum(sum(v) for v in rowsof(honda, "Civic", "Yard F - Flush").values()) == 0)
    check("frozen yard's rows still written (client skips)", rowsof(honda, "Civic", "Yard Z - Frozen").get(2005) == [0, 1, 0, 0, 0, 0, 0, 0])
    j = rowsof(honda, "CR-V", "Yard J - Jump")
    check("listFlushAt scan excluded, next scan counted (w7)", j.get(2005) == [0, 0, 0, 0, 0, 0, 1, 0], str(j))
    n = rowsof(honda, "Civic", "Yard N - New")
    check("new yard: first-scan car out, week-8 car in", n.get(2005) == [0, 0, 0, 0, 0, 0, 0, 1], str(n))
    t = rowsof(ford, "Taurus", "Yard A - Town")
    check("normalization: FORD / Taurus. fold into Ford|Taurus", "FORD" not in idx["makes"] and set(ford["models"]) == {"Taurus"}, str(ford["models"].keys()))
    check("model year kept; departed car counts", t.get(2001) == [0] * 7 + [2] and t.get(2003) == [0] * 7 + [2], str(t))
    check("make file shape", honda["make"] == "Honda" and honda["slug"] == "honda" and honda["windowEnd"] == "2026-11-18")
    check("index make arrivals = make file sum", idx["makes"]["Ford"][1] == 4, str(idx["makes"]))
    check("summary counts", info["stats"]["relist"] == 1 and info["stats"]["flush scan"] == 60 + 41 + 1
          and info["stats"]["yard not in this scan"] == 1, str(info["stats"]))
    check("no temp files left", not list(out.glob("*.tmp")))

    # ---- 20-hour rule ----
    before = {f.name: f.read_bytes() for f in out.glob("*.json")}
    r19 = js._write_arrivals_json(payload, now="2026-11-20T02:00:00Z")  # 19 h later
    check("20-hour rule: 19 h later keeps files", r19 is None and before == {f.name: f.read_bytes() for f in out.glob("*.json")})
    r21 = js._write_arrivals_json(payload, now="2026-11-20T04:00:00Z")  # 21 h later
    idx2 = json.loads((out / "index.json").read_text())
    check("20-hour rule: 21 h later rebuilds", r21 is not None and idx2["builtAt"] == "2026-11-20T04:00:00Z"
          and idx2["windowEnd"] == "2026-11-19", str(idx2.get("windowEnd")))
    check("rebuild: 11-19 arrival now counted in w8", rowsof(json.loads((out / "honda.json").read_text()), "Civic", "Yard A - Town").get(2005)[-1] == 3)

    # stale make file removed when the make has no arrival anymore
    (out / "oldmake.json").write_text("{}")
    js._write_arrivals_json(payload, now=NOW, force=True)
    check("files for makes no longer written are removed", not (out / "oldmake.json").exists())

    # ---- never fails the scan ----
    import io
    import contextlib
    before = {f.name: f.read_bytes() for f in out.glob("*.json")}
    real = db.arrival_history

    def boom(*a, **kw):
        raise RuntimeError("db exploded")
    db.arrival_history = boom
    err = io.StringIO()
    raised = None
    try:
        with contextlib.redirect_stderr(err):
            js._write_arrivals_safe(dict(payload, scrapedAt="2026-11-25T07:00:00Z"))
    except Exception as e:  # noqa: BLE001
        raised = e
    db.arrival_history = real
    check("exception inside the writer does not raise", raised is None, repr(raised))
    check("…logs a warning", "[arrivals] WARNING" in err.getvalue() and "db exploded" in err.getvalue(), err.getvalue())
    check("…and leaves the previous files", before == {f.name: f.read_bytes() for f in out.glob("*.json")})

    # failure while building (normalizer throws): nothing half-written
    real_cf = js._lifespan_canon_factory
    js._lifespan_canon_factory = lambda _db: (lambda *a: (_ for _ in ()).throw(ValueError("canon broke")))
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        js._write_arrivals_safe(dict(payload, scrapedAt="2026-11-25T07:00:00Z"))
    js._lifespan_canon_factory = real_cf
    check("mid-build failure leaves every previous file", before == {f.name: f.read_bytes() for f in out.glob("*.json")}
          and "canon broke" in err.getvalue())

    # no history DB at all
    db.DB_FILE = Path(td) / "missing" / "nope.db"
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        js._write_arrivals_safe(dict(payload, scrapedAt="2026-11-25T07:00:00Z"))
    check("missing DB: warning, files kept", "[arrivals] WARNING" in err.getvalue()
          and before == {f.name: f.read_bytes() for f in out.glob("*.json")}, err.getvalue())

    # the log line names counts and bytes
    db.DB_FILE = Path(td) / "h.db"
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        js._write_arrivals_safe(dict(payload, scrapedAt="2026-11-25T07:00:00Z"))
    line = err.getvalue()
    check("log line: one line with arrivals, rows, bytes", line.count("\n") == 1 and "arrivals" in line and "bytes total" in line, line)
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        js._write_arrivals_safe(dict(payload, scrapedAt="2026-11-25T11:00:00Z"))
    check("log line: kept within 20 h", "kept" in err.getvalue(), err.getvalue())

print(f"\n{passes} passed, {len(fails)} failed")
if fails:
    print("FAILED:", ", ".join(fails))
    sys.exit(1)
