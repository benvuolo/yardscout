#!/usr/bin/env python3
"""VinPlus reader when the service refuses (2026-11-23). From the 11-22 21:33
UTC scan the search endpoint answered 429 to every request and each scan
still sent all ~1,124 searches. The reader now stops asking after
VINPLUS_STOP_AFTER refusals in a row, and a yard with any unanswered make is
left out whole (its last copy stands) instead of published short. Offline.
Run:  python3 scraper/test_vinplus_stop.py"""
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

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


def run(post):
    """fetch_vinplus_inventory with fake HTTP: (cars, posts sent, cache files written)."""
    js._vinplus_stop_reset()
    sent, cached = [], []

    def fake_post(url, json=None, **kw):
        sent.append(json)
        return post(json, len(sent))

    with mock.patch.object(js, "VINPLUS_TENANTS", TENANTS), mock.patch.object(js, "VINPLUS_DELAY_SEC", 0), \
            mock.patch.object(js.requests, "get", return_value=GROUPS), \
            mock.patch.object(js.requests, "post", side_effect=fake_post), \
            mock.patch.object(js, "_indep_cache_raw", side_effect=lambda n, c: cached.append(n)):
        cars = js.fetch_vinplus_inventory()
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
        mock.patch.object(js, "VINPLUS_DELAY_SEC", 0):
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
with mock.patch.object(js.requests, "get", return_value=Resp(503)), \
        mock.patch.object(js.requests, "post", side_effect=AssertionError("sent")):
    check("make list fails: no searches, no cars", js.fetch_vinplus_inventory() == [])

js._vinplus_stop_reset()
print("ALL PASS" if not fails else f"{len(fails)} FAILURE(S): {fails}")
sys.exit(1 if fails else 0)
