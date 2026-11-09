#!/usr/bin/env python3
"""No two different chains' yards share exact coordinates (2026-11-09:
Tear-A-Part Ogden was stacked on Utah Pic-A-Part Ogden at Ogden's city
centroid). Walks every yard definition in junkyard_scraper (any dict with
name + lat + lng, plus YARD_COORDS). Same-chain sharing (Utah Pic-A-Part
Premium lots on their parent yard's address) is allowed.
Run:  python3 scraper/test_yard_coords.py   (offline)"""
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        fails.append(name)


yards: dict[str, tuple[float, float]] = {}


def walk(obj, depth=0):
    if depth > 6:
        return
    if isinstance(obj, dict):
        name, lat, lng = obj.get("name"), obj.get("lat"), obj.get("lng")
        if isinstance(name, str) and isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
            yards.setdefault(name, (round(float(lat), 4), round(float(lng), 4)))
        for v in obj.values():
            walk(v, depth + 1)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            walk(v, depth + 1)


for attr in dir(js):
    if attr.isupper():
        walk(getattr(js, attr))
for name, (lat, lng) in js.YARD_COORDS.items():
    yards.setdefault(name, (round(lat, 4), round(lng, 4)))

check("found the yard definitions", len(yards) > 150, len(yards))

by_point = defaultdict(set)
for name, pt in yards.items():
    by_point[pt].add(name)


def chain(n):
    return n.split(" - ")[0].strip().lower()


clashes = {pt: sorted(ns) for pt, ns in by_point.items() if len({chain(n) for n in ns}) > 1}
check("no two chains share exact coordinates", not clashes, clashes)
check("Tear-A-Part Ogden is not on Utah Pic-A-Part Ogden",
      js.YARD_COORDS["Tear-A-Part - Ogden"] != js.YARD_COORDS["Utah Pic-A-Part - Ogden"])

if fails:
    print(f"\n{len(fails)} FAILED")
    sys.exit(1)
print("\nall passed")
