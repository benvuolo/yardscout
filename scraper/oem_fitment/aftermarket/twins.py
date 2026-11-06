#!/usr/bin/env python3
"""Badge twins from evidence already held. Offline.

    python3 scraper/oem_fitment/aftermarket/twins.py [--groups FILE] [--out FILE]

A twin pair gets a claim only where a part-number-level basis exists:
here, the same DB Electrical unit printing both vehicles in its own
Applications List (aftermarket/groups_am.py groups; Likely, src
aftermarket). Platform knowledge is never a basis: TWINS below is only the
list of pairs the owner asked about, used to select what to report. A pair
on the list with no shared unit gets nothing. Pairs the OEM catalogs already
join inside one namespace (Ford/Mercury, GM/Pontiac/Saturn) are counted by
curate.py, not here.

Output: per twin pair and category, the shared units and the lot cars of
each side that have at least one engine-compatible lot car of the OTHER
make in a shared unit (cross-make donors only).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import groups_am as GA  # noqa: E402

# (label, side A (make, model), side B (make, model)). Selection only, not a basis.
TWINS = [
    ("Geo Prizm / Toyota Corolla", ("Geo", "Prizm"), ("Toyota", "Corolla")),
    ("Geo Metro / Suzuki Swift", ("Geo", "Metro"), ("Suzuki", "Swift")),
    ("Geo Tracker / Suzuki Sidekick", ("Geo", "Tracker"), ("Suzuki", "Sidekick")),
    ("Geo Tracker / Chevrolet Tracker", ("Geo", "Tracker"), ("Chevrolet", "Tracker")),
    ("Saab 9-7X / Chevrolet TrailBlazer", ("Saab", "9-7X"), ("Chevrolet", "Trailblazer")),
    ("Saab 9-7X / GMC Envoy", ("Saab", "9-7X"), ("GMC", "Envoy")),
    ("Saab 9-2X / Subaru Impreza", ("Saab", "9-2X"), ("Subaru", "Impreza")),
    ("Isuzu Ascender / GMC Envoy", ("Isuzu", "Ascender"), ("GMC", "Envoy")),
    ("Isuzu Ascender / Chevrolet TrailBlazer", ("Isuzu", "Ascender"), ("Chevrolet", "Trailblazer")),
    ("Isuzu i-Series / Chevrolet Colorado", ("Isuzu", "i-*"), ("Chevrolet", "Colorado")),
    ("Isuzu i-Series / GMC Canyon", ("Isuzu", "i-*"), ("GMC", "Canyon")),
    ("Isuzu Rodeo / Honda Passport", ("Isuzu", "Rodeo"), ("Honda", "Passport")),
    ("Isuzu Amigo / Isuzu Rodeo", ("Isuzu", "Amigo"), ("Isuzu", "Rodeo")),
    ("Isuzu Hombre / Chevrolet S10", ("Isuzu", "Hombre"), ("Chevrolet", "S10")),
    ("Suzuki XL-7 / Chevrolet Equinox", ("Suzuki", "XL-7"), ("Chevrolet", "Equinox")),
    ("Suzuki Equator / Nissan Frontier", ("Suzuki", "Equator"), ("Nissan", "Frontier")),
    ("Mazda B-Series / Ford Ranger", ("Mazda", "B*"), ("Ford", "Ranger")),
    ("Mitsubishi Raider / Dodge Dakota", ("Mitsubishi", "Raider"), ("Dodge", "Dakota")),
    ("Plymouth Voyager / Dodge Caravan", ("Plymouth", "Voyager"), ("Dodge", "Caravan")),
    ("Plymouth Grand Voyager / Dodge Grand Caravan", ("Plymouth", "Grand Voyager"), ("Dodge", "Grand Caravan")),
    ("Plymouth Neon / Dodge Neon", ("Plymouth", "Neon"), ("Dodge", "Neon")),
    ("Plymouth Breeze / Dodge Stratus", ("Plymouth", "Breeze"), ("Dodge", "Stratus")),
    ("Pontiac Vibe / Toyota Matrix", ("Pontiac", "Vibe"), ("Toyota", "Matrix")),
    ("Mercury Grand Marquis / Ford Crown Victoria", ("Mercury", "Grand Marquis"), ("Ford", "Crown Victoria")),
    ("Mercury Mountaineer / Ford Explorer", ("Mercury", "Mountaineer"), ("Ford", "Explorer")),
    ("Mercury Mariner / Ford Escape", ("Mercury", "Mariner"), ("Ford", "Escape")),
    ("Mercury Milan / Ford Fusion", ("Mercury", "Milan"), ("Ford", "Fusion")),
    ("Mercury Sable / Ford Taurus", ("Mercury", "Sable"), ("Ford", "Taurus")),
    ("Mercury Villager / Nissan Quest", ("Mercury", "Villager"), ("Nissan", "Quest")),
    ("Mercury Tracer / Ford Escort", ("Mercury", "Tracer"), ("Ford", "Escort")),
]


def _side_match(side, mk, md) -> bool:
    smk, smd = side
    if mk != smk:
        return False
    if smd.endswith("*"):
        return GA.squash(md).startswith(GA.squash(smd[:-1]))
    return GA.squash(md) == GA.squash(smd)


def twins(doc: dict, cars: list) -> dict:
    """cars: (index, make, model, year, engine, trans) as in GA.members."""
    mem = GA.members(doc, cars)
    cat_of = {g["id"]: g["cat"] for g in doc["groups"]}
    info = {i: (c[1], c[2]) for i, c in enumerate(cars)}
    out = {}
    for label, A, B in TWINS:
        row = {}
        for cat in GA.CATS:
            units, a_cov, b_cov = [], set(), set()
            a_conf, b_conf = set(), set()
            for gid, ms in mem.items():
                if cat_of[gid] != cat:
                    continue
                sa = [(ci, cond) for ci, cond in ms if _side_match(A, *info[ci])]
                sb = [(ci, cond) for ci, cond in ms if _side_match(B, *info[ci])]
                if not sa or not sb:
                    continue
                units.append(gid.split(":", 3)[3])
                a_cov.update(ci for ci, _ in sa)
                b_cov.update(ci for ci, _ in sb)
                if any(not c for _, c in sb):
                    a_conf.update(ci for ci, c in sa if not c)
                if any(not c for _, c in sa):
                    b_conf.update(ci for ci, c in sb if not c)
            row[cat] = {"units": sorted(units), "a_cars": len(a_cov), "b_cars": len(b_cov),
                        "a_cars_engine_confirmed": len(a_conf), "b_cars_engine_confirmed": len(b_conf)}
        lot_a = sum(1 for c in cars if _side_match(A, c[1], c[2]))
        lot_b = sum(1 for c in cars if _side_match(B, c[1], c[2]))
        out[label] = {"a": list(A), "b": list(B), "lot_a": lot_a, "lot_b": lot_b, "by_cat": row}
    return out


def gap_make_gain(doc: dict, cars: list, makes) -> dict:
    """Lot cars of `makes` that have at least one cross-make donor in a
    shared unit (any make other than their own), per category."""
    mem = GA.members(doc, cars)
    cat_of = {g["id"]: g["cat"] for g in doc["groups"]}
    hit = {cat: set() for cat in GA.CATS}
    for gid, ms in mem.items():
        mks = {cars[ci][1] for ci, _ in ms}
        if len(mks) < 2:
            continue
        for ci, _ in ms:
            if cars[ci][1] in makes:
                hit[cat_of[gid]].add(ci)
    out = {}
    for mk in makes:
        n = sum(1 for c in cars if c[1] == mk)
        a = {ci for ci in hit["alternator"] if cars[ci][1] == mk}
        s = {ci for ci in hit["starter"] if cars[ci][1] == mk}
        out[mk] = {"cars": n, "alternator": len(a), "starter": len(s), "either": len(a | s)}
    return out


def load_cars(inv_p: Path, ex_p: Path) -> list:
    inv = json.loads(inv_p.read_text())
    F = {k: i for i, k in enumerate(inv["fields"])}
    ex = json.loads(ex_p.read_text()).get("extras", {}) if ex_p.exists() else {}
    cars = []
    for i, v in enumerate(inv["vehicles"]):
        e = ex.get(str(v[F["id"]])) or []
        cars.append((i, v[F["make"]] or "", v[F["model"]] or "", int(v[F["year"]] or 0),
                     e[2] if len(e) > 2 else "", e[3] if len(e) > 3 else ""))
    return cars


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--groups", default=str(HERE.parent / "groups" / "_report" / "aftermarket-dbelectrical.json"))
    ap.add_argument("--inventory", default=str(GA.REPO / "docs" / "data" / "inventory_live.json"))
    ap.add_argument("--extras", default=str(GA.REPO / "docs" / "data" / "vehicle_extras.json"))
    ap.add_argument("--out", default=str(HERE.parent / "groups" / "_report" / "aftermarket-twins.json"))
    a = ap.parse_args(argv)
    doc = json.loads(Path(a.groups).read_text())
    cars = load_cars(Path(a.inventory), Path(a.extras))
    tw = twins(doc, cars)
    gain = gap_make_gain(doc, cars, ("MINI", "Land Rover", "Suzuki", "Jaguar", "Isuzu", "Saab", "Fiat",
                                     "Plymouth", "Porsche", "Geo", "Smart", "Mercury", "Pontiac", "Mazda",
                                     "Mitsubishi"))
    res = {"raw": doc.get("raw"), "groups_sha256": doc.get("sha256"), "twins": tw, "cross_make_gain": gain}
    Path(a.out).write_text(json.dumps(res, sort_keys=True, indent=1) + "\n")
    print("| twin pair | lot A / B | alternator units | alt A / B cars | starter units | str A / B cars |")
    print("|---|---|---:|---|---:|---|")
    for label, t in tw.items():
        al, st = t["by_cat"]["alternator"], t["by_cat"]["starter"]
        print(f"| {label} | {t['lot_a']} / {t['lot_b']} | {len(al['units'])} | {al['a_cars']} / {al['b_cars']} | "
              f"{len(st['units'])} | {st['a_cars']} / {st['b_cars']} |")
    print("\n| make | lot cars | cross-make alt | cross-make starter | either |\n|---|---:|---:|---:|---:|")
    for mk, g in gain.items():
        print(f"| {mk} | {g['cars']} | {g['alternator']} | {g['starter']} | {g['either']} |")
    print(f"wrote {a.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
