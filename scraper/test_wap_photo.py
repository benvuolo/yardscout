#!/usr/bin/env python3
"""Wrench-A-Part photo capture: compact "w" codes from the feed's own
Google Cloud Storage URLs, strict shape matching, no code for anything else,
and the code rides into the extras shard's photo column.
Run:  python3 scraper/test_wap_photo.py   (offline)"""
import json
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


B = "https://storage.googleapis.com/wrench-car-photos/v1%2F"
THUMB = B + "2%2F1C3CCCAB3FN712637%2F1793896869292-front_driver-thumb.jpg"
FULL = B + "2%2F1C3CCCAB3FN712637%2F1793896869292-front_driver.jpg"
PNG = B + "3%2F1GC4KXBG8AF136387%2F1788281660820.png"

# --- code shapes -----------------------------------------------------------
check("thumb shape -> .j code",
      js._wap_photo_code({"photo": FULL, "photoThumb": THUMB})
      == "w2/1C3CCCAB3FN712637/1793896869292.j")
check("png-only shape -> .p code",
      js._wap_photo_code({"photo": PNG}) == "w3/1GC4KXBG8AF136387/1788281660820.p")
check("no photo -> empty", js._wap_photo_code({}) == "")
check("null photo -> empty", js._wap_photo_code({"photo": None, "photoThumb": None}) == "")
check("full jpg without thumb is not guessed",
      js._wap_photo_code({"photo": FULL}) == "")
for bad in (
    "http://storage.googleapis.com/wrench-car-photos/v1%2F2%2F1C3CCCAB3FN712637%2F1793896869292-front_driver-thumb.jpg",
    "https://storage.googleapis.com/other-bucket/v1%2F2%2F1C3CCCAB3FN712637%2F1793896869292-front_driver-thumb.jpg",
    "https://cdn.row52.com/x.jpg",
    B + "2%2F1C3CCCAB3FN712637%2F1793896869292-rear_passenger-thumb.jpg",
    B + "2%2F1C3CCCAB3FN712637%2F1793896869292-front_driver-thumb.jpg?x=1",
):
    check(f"foreign/odd URL rejected: {bad[-45:]}",
          js._wap_photo_code({"photo": bad, "photoThumb": bad}) == "")

# Round trip: the URL the app rebuilds from the code (see the hand-off in
# ops/yards.md) is exactly the feed's URL.
def rebuild(code, large=False):
    body, suf = code[1:-2], code[-2:]
    yard, vin, ms = body.split("/")
    stem = f"{js.WAP_PHOTO_BASE}{yard}%2F{vin}%2F{ms}"
    if suf == ".p":
        return stem + ".png"
    return stem + ("-front_driver.jpg" if large else "-front_driver-thumb.jpg")

check("round trip thumb", rebuild("w2/1C3CCCAB3FN712637/1793896869292.j") == THUMB)
check("round trip full", rebuild("w2/1C3CCCAB3FN712637/1793896869292.j", True) == FULL)
check("round trip png", rebuild("w3/1GC4KXBG8AF136387/1788281660820.p") == PNG)

# --- fetcher wiring --------------------------------------------------------
FEED = [
    {"yard": 2, "modelYear": "2015", "make": {"name": "CHRYSLER"},
     "model": {"name": "200"}, "photo": FULL, "photoThumb": THUMB,
     "vin": "1C3CCCAB3FN712637", "color": "MAROON", "stockNumber": "AWAP085686",
     "dateAdded": "2026-11-06T09:18:04Z", "row": {"id": 41}},
    {"yard": 2, "modelYear": "2010", "make": {"name": "HONDA"},
     "model": {"name": "CIVIC"}, "photo": None, "photoThumb": None,
     "vin": "", "color": "", "stockNumber": "AWAP000001",
     "dateAdded": "2026-11-05T09:00:00Z", "row": {"id": 3}},
]


class Resp:
    status_code = 200
    content = json.dumps(FEED).encode()

    def raise_for_status(self):
        pass

    def json(self):
        return FEED


with mock.patch.object(js.requests, "get", return_value=Resp()), \
        mock.patch.object(js, "_indep_cache_raw", lambda *a, **k: None):
    rows = {v["id"]: v for v in js.fetch_wrenchapart_inventory()}
check("fetcher returns both cars", set(rows) == {"wap-AWAP085686", "wap-AWAP000001"}, rows.keys())
check("photo code captured",
      rows.get("wap-AWAP085686", {}).get("_photo") == "w2/1C3CCCAB3FN712637/1793896869292.j")
check("no photo -> empty _photo", rows.get("wap-AWAP000001", {}).get("_photo") == "")

if fails:
    print(f"\n{len(fails)} FAILED")
    sys.exit(1)
print("\nall passed")
