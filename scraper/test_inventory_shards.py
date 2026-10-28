#!/usr/bin/env python3
"""Tests for the radius-first inventory shards (inventory_shards.py ->
docs/data/inv/, read by loadShardedInventory in docs/app.js).

Covers:
  1. fnv1a32 matches the published FNV-1a test vectors (app.js mirrors it).
  2. Round trip on a synthetic payload: re-assembling the shards by their
     delta-coded positions gives back the exact vehicles array, vpic side
     table and extras; every yard sits in exactly one shard; every key (VIN
     and String(id)) is findable in its bucket under the right shard.
  3. Stale files from another layout are removed; the manifest is written
     last and describes the shards.
  4. With --real: the same round trip against docs/data/inventory_live.json
     + vehicle_extras.json (written to a temp dir, never into docs/).

Run:  python3 scraper/test_inventory_shards.py [--real]
"""

import json
import random
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inventory_shards as inv  # noqa: E402

failures = []


def check(name, cond, detail=""):
    print(("  ok  " if cond else "  FAIL") + f" {name}" + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def roundtrip(payload, extras, out_root, k=None, buckets=None, label=""):
    kw = {}
    if k:
        kw["shard_count"] = k
    if buckets:
        kw["key_buckets"] = buckets
    info = inv.write_inventory_shards(payload, extras, out_root, **kw)
    d = out_root / "inv"
    m = json.loads((d / "manifest.json").read_text())
    n_sh = len(m["shards"])
    check(f"{label}manifest scan stamp + counts", m["scrapedAt"] == payload["scrapedAt"]
          and m["vehicles"] == len(payload["vehicles"]) and sum(m["shards"]) == m["vehicles"])
    check(f"{label}yards table identical", m["yards"] == payload["yards"])
    ps = json.loads((d / "partsets.json").read_text())
    check(f"{label}partSets identical", ps["partSets"] == payload["partSets"] and ps["scrapedAt"] == payload["scrapedAt"])

    rebuilt = [None] * m["vehicles"]
    vpic, ex = {}, {}
    yard_seen = {}
    ok_ids = True
    for s in range(n_sh):
        sh = json.loads((d / f"shard-{s:02d}.json").read_text())
        ok_ids &= sh["shard"] == s and sh["scrapedAt"] == payload["scrapedAt"] and len(sh["vehicles"]) == m["shards"][s]
        g = 0
        for j, row in enumerate(sh["vehicles"]):
            g += sh["pos"][j]
            rebuilt[g] = row
            if str(j) in sh["vpic"]:
                vpic[str(g)] = sh["vpic"][str(j)]
            if str(j) in sh["extras"]:
                ex[str(row[0])] = sh["extras"][str(j)]
            yard_seen.setdefault(row[7], set()).add(s)
            ok_ids &= m["yardShard"][row[7]] == s
    check(f"{label}shard headers + yardShard agree", ok_ids)
    check(f"{label}vehicles rebuilt in original order", rebuilt == payload["vehicles"])
    check(f"{label}vpic rebuilt", vpic == payload["vpic"])
    want_ex = {str(r[0]): extras[str(r[0])] for r in payload["vehicles"] if str(r[0]) in extras}
    check(f"{label}extras rebuilt", ex == want_ex)
    check(f"{label}each yard in exactly one shard", all(len(v) == 1 for v in yard_seen.values()))

    fi = {n: i for i, n in enumerate(payload["fields"])}
    nb = m["keyBuckets"]
    bucket_cache = {}
    missing = 0
    for row in payload["vehicles"]:
        s = m["yardShard"][row[7]]
        for key in inv.vehicle_keys(row, fi):
            h = inv.fnv1a32(key)
            b = h % nb
            if b not in bucket_cache:
                bucket_cache[b] = json.loads((d / f"keys-{b:02d}.json").read_text())
            lst = " " + bucket_cache[b]["s"].get(str(s), "") + " "
            if f" {inv._b36(h)} " not in lst:
                missing += 1
    check(f"{label}every VIN / id key indexed under its shard", missing == 0, f"{missing} missing")
    return m, info


# ---- 1. hash vectors ----------------------------------------------------------
print("fnv1a32:")
check("'' -> 0x811c9dc5", inv.fnv1a32("") == 0x811C9DC5)
check("'a' -> 0xe40c292c", inv.fnv1a32("a") == 0xE40C292C)
check("'foobar' -> 0xbf9cf968", inv.fnv1a32("foobar") == 0xBF9CF968)
check("base36", inv._b36(0) == "0" and inv._b36(35) == "z" and inv._b36(36) == "10")

# ---- 2. synthetic round trip ----------------------------------------------------
print("synthetic payload:")
rng = random.Random(7)
yards = []
for i in range(37):
    yards.append([f"Yard {i}", f"City {i}", "UT", round(rng.uniform(25, 49), 4), round(rng.uniform(-124, -67), 4),
                  rng.choice([None, 40, 55]), rng.choice([None, "yard", "chain", "all"])])
yards.append(["No Coords Yard", "", "", None, None, None, None])
part_sets = [[{"name": f"Part {p}", "low": p, "high": p * 2}] for p in range(9)]
vehicles, vpic, extras = [], {}, {}
for g in range(2500):
    yi = rng.randrange(len(yards))
    vid = rng.choice([g * 7 + 1000, f"pyp-{g}"])
    vin = rng.choice(["", f"1HGCM82633A{g:06d}"])
    vehicles.append([vid, vin, 2000 + g % 20, "Honda", "Accord", str(g % 50), "2026-10-01", yi,
                     rng.choice([-1] + list(range(len(part_sets)))), g % 300, g % 2])
    if g % 3 == 0:
        vpic[str(g)] = ["EX", "usable", "", "FWD", ""]
    if g % 4 == 0:
        extras[str(vid)] = ["", "Blue", "2.4L 4-cyl"]
payload = {"schemaVersion": 2, "scrapedAt": "2026-10-28T19:06:50Z", "pricesLastReviewed": "2026-10-22",
           "fields": ["id", "vin", "year", "make", "model", "row", "dateAdded", "yard", "partSet", "maxValue", "premium"],
           "yardFields": ["location", "city", "state", "lat", "lng", "avgLifespanDays", "lifespanBasis"],
           "yards": yards, "partSets": part_sets, "vpic": vpic, "vehicles": vehicles}
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "inv").mkdir()
    (root / "inv" / "shard-77.json").write_text("{}")   # leftover from an older layout
    m, info = roundtrip(payload, extras, root, k=8, buckets=16)
    check("old-layout leftovers removed", not (root / "inv" / "shard-77.json").exists())
    check("8 shards written", len(m["shards"]) == 8 and (root / "inv" / "shard-07.json").exists())
    check("16 key buckets written", (root / "inv" / "keys-15.json").exists() and not (root / "inv" / "keys-16.json").exists())
    sizes = [n for n in m["shards"]]
    check("shards roughly balanced", max(sizes) < 3 * (sum(sizes) / len(sizes)), str(sizes))
    nc = len(yards) - 1
    check("coordless yard assigned to some shard", 0 <= m["yardShard"][nc] < 8)
    # Re-running with fewer shards drops the now-unused files.
    roundtrip(payload, extras, root, k=4, buckets=8, label="re-run k=4: ")
    check("re-run removes shard-04..07", not (root / "inv" / "shard-04.json").exists())

# Determinism: same input -> same assignment.
counts = [1] * len(yards)
check("shard_yards deterministic", inv.shard_yards(yards, counts, 8) == inv.shard_yards(yards, counts, 8))
few = inv.shard_yards(yards[:3], [1, 1, 1], 8)
check("shard_yards with more leaves than yards", len(few) == 3 and set(few) <= set(range(8)) and len(set(few)) == 3, str(few))

# ---- 4. real data ---------------------------------------------------------------
if "--real" in sys.argv:
    print("real docs/data payload:")
    data_dir = Path(__file__).resolve().parent.parent / "docs" / "data"
    real = json.loads((data_dir / "inventory_live.json").read_text())
    try:
        real_ex = json.loads((data_dir / "vehicle_extras.json").read_text()).get("extras", {})
    except FileNotFoundError:
        real_ex = {}
    with tempfile.TemporaryDirectory() as tmp:
        m, info = roundtrip(real, real_ex, Path(tmp), label="real: ")
        print(f"  {info}")
        check("real: 24-40 shards of ~5-15k vehicles",
              24 <= len(m["shards"]) <= 40 and min(m["shards"]) >= 4000 and max(m["shards"]) <= 15000,
              str(sorted(m["shards"])))

print()
if failures:
    print(f"{len(failures)} FAILURE(S): {failures}")
    sys.exit(1)
print("All inventory-shard tests passed.")
