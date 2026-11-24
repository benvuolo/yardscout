#!/usr/bin/env python3
"""VinPlus reader when the service refuses (2026-11-23). From the 11-22 21:33
UTC scan the search endpoint answered 429 to every request and each scan
still sent all ~1,124 searches. The reader now stops asking after
VINPLUS_STOP_AFTER refusals in a row, and a yard with any unanswered make is
left out whole (its last copy stands) instead of published short.
2026-11-24: a yard is asked at most about twice a day and a few yards a scan
(the last full read is reused in between), and iPull-uPull photo codes the
search gave once are kept for a scan in which it gives no answer. Offline.
Run:  python3 scraper/test_vinplus_stop.py"""
import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db  # noqa: E402
import junkyard_scraper as js  # noqa: E402

TMP = Path(tempfile.mkdtemp())
T0 = datetime(2026, 11, 24, 6, 0, tzinfo=timezone.utc)
_n = [0]


def fresh_db():
    """An empty history DB: nothing kept from an earlier read."""
    _n[0] += 1
    db.DB_FILE = TMP / f"h{_n[0]}.db"

fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        fails.append(name)


class Resp:
    def __init__(self, status=200, body=None, headers=None):
        self.status_code, self._body, self.headers = status, body or {}, headers or {}

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise js.requests.HTTPError(f"{self.status_code} Client Error")


def yard(code, name):
    return {"code": code, "name": name, "city": "X", "state": "TX", "lat": 1.0, "lng": 2.0}


TENANTS = {"t1": {"a": yard("a", "Yard A"), "b": yard("b", "Yard B")}, "t2": {"": yard("c", "Yard C")}}
MAKES = ["ACURA", "BMW", "FORD", "HONDA", "TOYOTA"]
GROUPS = Resp(body={"data": {m: [] for m in MAKES}})


def row(stock, make="FORD", year=2005):
    return {"stock": stock, "make": make, "model": "F150", "year": year, "vin": "", "dateAdded": "2026-11-20"}


def run(post, now=T0, keep_db=False, per_scan=8, gets=None):
    """fetch_vinplus_inventory with fake HTTP: (cars, posts sent, cache files written)."""
    js._vinplus_stop_reset()
    if not keep_db:
        fresh_db()
    sent, cached = [], []

    def fake_post(url, json=None, **kw):
        sent.append(json)
        return post(json, len(sent))

    def fake_get(url, **kw):
        if gets is not None:
            gets.append(url)
        return GROUPS

    with mock.patch.object(js, "VINPLUS_TENANTS", TENANTS), mock.patch.object(js, "VINPLUS_DELAY_SEC", 0), \
            mock.patch.object(js, "VINPLUS_YARDS_PER_SCAN", per_scan), \
            mock.patch.object(js.requests, "get", side_effect=fake_get), \
            mock.patch.object(js.requests, "post", side_effect=fake_post), \
            mock.patch.object(js, "_indep_cache_raw", side_effect=lambda n, c: cached.append(n)):
        cars = js.fetch_vinplus_inventory(now=now)
    return cars, sent, cached


# --- every search refused: three are sent, then nothing ---
cars, sent, cached = run(lambda q, n: Resp(429, headers={"Retry-After": "3600"}))
total = len(MAKES) * 3
check("all refused: only VINPLUS_STOP_AFTER searches are sent", len(sent) == js.VINPLUS_STOP_AFTER == 3, len(sent))
check("all refused: the rest are counted as not sent", js._VINPLUS_STOP["not_sent"] == total - 3, js._VINPLUS_STOP)
check("all refused: no cars, no raw cache written (the last copy stands)", cars == [] and cached == [], (len(cars), cached))
check("all refused: Retry-After is noted", js._VINPLUS_STOP["retry_after"] == "3600")

# --- after the stop, the other caller (iPull-uPull photos) sends nothing either ---
with mock.patch.object(js.requests, "post", side_effect=AssertionError("a search was sent after the stop")), \
        mock.patch.object(js, "IPULL_PHOTO_SEED", TMP / "none.json"), mock.patch.object(js, "VINPLUS_DELAY_SEC", 0):
    cars_i = [{"id": "ipull-sac1", "make": "Honda"}]
    try:
        js._ipull_apply_api_photos(cars_i)
        ok = "_photo" not in cars_i[0]
    except AssertionError as e:
        ok = False
check("after the stop: the iPull-uPull photo lookup sends nothing", ok)

# --- all answered: every yard is published and cached ---
cars, sent, cached = run(lambda q, n: Resp(body={"matches": [row(f"S{n}", q["make"])]}))
check("all answered: one search per make per yard", len(sent) == total, len(sent))
check("all answered: all three yards published", {c["_location"] for c in cars} == {"Yard A", "Yard B", "Yard C"} and len(cars) == total, len(cars))
check("all answered: raw cache written per yard", sorted(cached) == ["vinplus_a.json", "vinplus_b.json", "vinplus_c.json"], cached)
check("all answered: nothing counted as refused", js._VINPLUS_STOP == {"refused": 0, "stopped": False, "not_sent": 0, "retry_after": ""}, js._VINPLUS_STOP)

# --- one make of one yard fails (a 500): that yard is left out whole, the others publish ---
cars, sent, cached = run(lambda q, n: Resp(500) if (q["location_id"] == "b" and q["make"] == "FORD")
                         else Resp(body={"matches": [row(f"S{n}", q["make"])]}))
check("one failed make: that yard is left out whole", {c["_location"] for c in cars} == {"Yard A", "Yard C"}, {c["_location"] for c in cars})
check("one failed make: its raw cache is not overwritten", sorted(cached) == ["vinplus_a.json", "vinplus_c.json"], cached)
check("one failed make: every search was still sent (a 500 is not a refusal)", len(sent) == total and not js._VINPLUS_STOP["stopped"], len(sent))

# --- refusals that are not in a row do not stop the scan ---
cars, sent, cached = run(lambda q, n: Resp(429) if n in (1, 2, 4, 5) else Resp(body={"matches": [row(f"S{n}", q["make"])]}))
check("two refusals, an answer, two refusals: not stopped", not js._VINPLUS_STOP["stopped"] and len(sent) == total, (js._VINPLUS_STOP, len(sent)))
check("...and the yard with refused makes keeps its last copy", {c["_location"] for c in cars} == {"Yard B", "Yard C"}, {c["_location"] for c in cars})

# --- a refusal inside a year-range split marks the yard too ---


def split_post(q, n):
    if q["location_id"] == "a" and q["make"] == "FORD":
        if q["year_min"] is None:
            return Resp(body={"matches": [row(f"F{i}") for i in range(100)]})   # capped: the reader splits by year
        return Resp(429) if q["year_min"] > 1960 else Resp(body={"matches": [row("OLD1", year=1955)]})
    return Resp(body={"matches": [row(f"S{n}", q["make"])]})


cars, sent, cached = run(split_post)
check("a failed half of a year split: the yard is left out whole", "Yard A" not in {c["_location"] for c in cars}
      and {c["_location"] for c in cars} == {"Yard B", "Yard C"}, {c["_location"] for c in cars})

# --- the make list itself failing is unchanged: nothing published, nothing sent ---
js._vinplus_stop_reset()
fresh_db()
with mock.patch.object(js, "VINPLUS_TENANTS", TENANTS), mock.patch.object(js.requests, "get", return_value=Resp(503)), \
        mock.patch.object(js.requests, "post", side_effect=AssertionError("sent")):
    check("make list fails: no searches, no cars", js.fetch_vinplus_inventory(now=T0) == [])

# --- asking less: a yard is asked at most every VINPLUS_MIN_HOURS, a few yards a scan ---
ok_post = lambda q, n: Resp(body={"matches": [row(f"{q['location_id'] or 'c'}-{q['make']}", q["make"])]})  # noqa: E731
cars0, sent, _ = run(ok_post)
gets = []
cars1, sent, cached = run(lambda q, n: Resp(500), now=T0 + timedelta(hours=4), keep_db=True, gets=gets)
check("4 h after a full read: nothing is asked, not even the make list", sent == [] and gets == [], (len(sent), gets))
check("4 h after: every yard publishes its last full read, unchanged",
      sorted(c["id"] for c in cars1) == sorted(c["id"] for c in cars0) and len(cars1) == total, len(cars1))
cars2, sent, _ = run(ok_post, now=T0 + timedelta(hours=11, minutes=30), keep_db=True)
check("11.5 h after: every yard is asked again", len(sent) == total and len(cars2) == total, len(sent))

cars, sent, _ = run(ok_post, per_scan=2)
check("at most 2 yards a scan, nothing kept: two are asked, the third waits (left out)",
      len(sent) == 2 * len(MAKES) and {c["_location"] for c in cars} == {"Yard A", "Yard B"}, (len(sent), {c["_location"] for c in cars}))
cars, sent, _ = run(ok_post, per_scan=2, now=T0 + timedelta(hours=4), keep_db=True)
check("next scan: only the third is asked, the first two reuse their read",
      len(sent) == len(MAKES) and {q["yard_id"] for q in sent} == {"t2"} and {c["_location"] for c in cars} == {"Yard A", "Yard B", "Yard C"},
      (len(sent), {c["_location"] for c in cars}))

run(ok_post)
cars, sent, _ = run(lambda q, n: Resp(429), now=T0 + timedelta(hours=12), keep_db=True)
check("refused 12 h after a read: 3 searches; the yards asked are left out, a waiting yard would reuse (none here)",
      len(sent) == 3 and cars == [], (len(sent), len(cars)))
cars, sent, _ = run(lambda q, n: Resp(429), now=T0 + timedelta(hours=12), keep_db=True, per_scan=1)
check("refused, 1 yard a scan: the two not asked still publish their 12 h old read",
      {c["_location"] for c in cars} == {"Yard B", "Yard C"}, {c["_location"] for c in cars})
cars, sent, _ = run(lambda q, n: Resp(429), now=T0 + timedelta(hours=30), keep_db=True, per_scan=1)
check("refused, 30 h after the read: nothing that old is reused (STALE-KEEP and its cap decide)", cars == [], len(cars))

K = {"a": ("2026-11-24T05:00:00Z", []), "b": ("2026-11-23T10:00:00Z", []), "c": ("bad", [])}
with mock.patch.object(js, "VINPLUS_YARDS_PER_SCAN", 2):
    ask, reuse = js._vinplus_plan(["a", "b", "c", "d"], K, T0)
check("plan: longest-unread first (never read, unreadable time, then oldest), read 1 h ago is reused",
      set(ask) <= {"b", "c", "d"} and len(ask) == 2 and "b" not in ask and "a" in reuse, (ask, reuse))
check("plan: a 20 h old read not asked this scan is reused; nothing kept is not", "b" in reuse and "d" not in reuse and "c" not in reuse, (ask, reuse))

# --- iPull-uPull photos: a code the search gave once is kept for a scan with no answer ---
IC = "https://ipullupull.com/wp-content/uploads/ipullupull-catalog/"
fresh_db()
seed = TMP / "seed.json"
seed.write_text(json.dumps({"codes": {"SAC0003": "iSAC0003/SAC0003_1", "SAC0004": "iSAC0009/other-cars-file"}}))


def ipull(post_fn):
    js._vinplus_stop_reset()
    cars = [{"id": "ipull-sac0001", "make": "Honda"}, {"id": "ipull-sac0002", "make": "Honda"},
            {"id": "ipull-sac0003", "make": "Ford"}, {"id": "ipull-sac0004", "make": "Ford"}, {"id": "ipull-sac0005", "make": "Ford"}]
    with mock.patch.object(js, "VINPLUS_DELAY_SEC", 0), mock.patch.object(js, "IPULL_PHOTO_SEED", seed), \
            mock.patch.object(js.requests, "post", side_effect=lambda url, json=None, **kw: post_fn(json)):
        js._ipull_apply_api_photos(cars)
    return {c["id"]: c.get("_photo", "") for c in cars}


answered = lambda q: Resp(body={"matches": (  # noqa: E731
    [{"stock": "SAC0001", "imageUrl": IC + "SAC0001/SAC0001-1.jpg"}, {"stock": "SAC0002", "imageUrl": ""}] if q["make"] == "HONDA"
    else [{"stock": "SAC0005", "imageUrl": IC + "SAC0005/IMG_4097.jpg"}])})
got = ipull(answered)
check("iPull answered: photos are the search's own answer; the seed is not used for an answered make",
      got == {"ipull-sac0001": "iSAC0001/SAC0001-1", "ipull-sac0002": "", "ipull-sac0003": "", "ipull-sac0004": "", "ipull-sac0005": "iSAC0005/IMG_4097"}, got)
got = ipull(lambda q: Resp(429))
check("iPull refused: codes learned earlier (DB) and the seed are kept; a car never seen with a photo has none",
      got["ipull-sac0001"] == "iSAC0001/SAC0001-1" and got["ipull-sac0005"] == "iSAC0005/IMG_4097" and got["ipull-sac0003"] == "iSAC0003/SAC0003_1" and got["ipull-sac0002"] == "", got)
check("iPull refused: a kept code that is not this car's own folder is not used", got["ipull-sac0004"] == "", got)
got = ipull(lambda q: Resp(429) if q["make"] == "FORD" else answered(q))
check("iPull: one make unanswered: only that make's cars use kept codes",
      got == {"ipull-sac0001": "iSAC0001/SAC0001-1", "ipull-sac0002": "", "ipull-sac0003": "iSAC0003/SAC0003_1", "ipull-sac0004": "", "ipull-sac0005": "iSAC0005/IMG_4097"}, got)
real = json.loads(js.IPULL_PHOTO_SEED.read_text(encoding="utf8"))["codes"]
check("the committed seed: every code is a file in that car's own folder",
      len(real) > 3000 and all(js._ipull_photo_code(f"{IC}{c[1:]}.jpg", st) == c for st, c in real.items()), len(real))

js._vinplus_stop_reset()
print("ALL PASS" if not fails else f"{len(fails)} FAILURE(S): {fails}")
sys.exit(1 if fails else 0)
