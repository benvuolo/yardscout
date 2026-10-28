"""Radius-first inventory shards: docs/data/inv/.

The app's cold start used to download the whole inventory_live.json (~44 MB
raw, ~9 MB gzipped) before it could draw a single car. This module writes the
SAME scan a second time, cut into geographic shards, so the app can fetch the
few shards around the user first, render, and load the rest in the
background. inventory_live.json itself is still written unchanged by the
scraper (the site Worker's share pages, push_inventory.py and the audit
scripts all read it) — this is an additional, derived copy.

Layout (all files carry the scan's scrapedAt; the app rejects any file whose
scrapedAt differs from the manifest it is loading against):

  inv/manifest.json   scan metadata + the yards table (same rows and order as
                      inventory_live.json) + yardShard[i] (which shard holds
                      yard i) + yardCount[i] + per-shard vehicle counts.
  inv/partsets.json   the partSets table, unchanged (rows keep their global
                      partSet index, so identical part lists stay shared).
  inv/shard-NN.json   vehicles of the yards in shard NN, rows byte-identical
                      to inventory_live.json (global yard / partSet indices),
                      in their original relative order. `pos` delta-codes
                      each row's global position (first entry absolute) so
                      the app can rebuild the exact global order. vpic and
                      extras (vehicle_extras.json) are keyed by LOCAL row
                      index within the shard.
  inv/keys-BB.json    share-link / alert lookup: FNV-1a-32 hashes (base 36)
                      of every vehicle's keys (VIN when present, and the id
                      as a string — the app's #car= / #alert= forms), grouped
                      by the shard that holds the car; bucket BB = hash %
                      KEY_BUCKETS. Lets a deep link fetch the right shard
                      first instead of downloading everything.

Shards are a k-d split of the yards on (lat, lng·cos lat), weighted by
vehicle count, into a FIXED number of leaves — so the set of file names never
changes between scans (git stages modifications, never add/delete churn).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

SHARD_LAYOUT = 1
SHARD_COUNT = 40
KEY_BUCKETS = 64
INV_DIRNAME = "inv"


def fnv1a32(s: str) -> int:
    """32-bit FNV-1a over UTF-8 bytes (mirrored by _invHash in docs/app.js)."""
    h = 0x811C9DC5
    for b in s.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def _b36(n: int) -> str:
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    if n == 0:
        return "0"
    out = []
    while n:
        n, r = divmod(n, 36)
        out.append(digits[r])
    return "".join(reversed(out))


def _js_string(x) -> str | None:
    """String(x) as the app computes it for vehicle ids (ints and strings)."""
    if x is None:
        return None
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x)


def vehicle_keys(row: list, fi: dict[str, int]) -> list[str]:
    """Every string a deep link may carry for this car: vehicleKey() is
    vin || String(id), and focus matching also accepts the bare id."""
    keys = []
    vin = row[fi["vin"]]
    if vin:
        keys.append(str(vin))
    sid = _js_string(row[fi["id"]])
    if sid is not None and sid not in keys:
        keys.append(sid)
    return keys


def shard_yards(yards: list[list], counts: list[int], k: int,
                lat_i: int = 3, lng_i: int = 4) -> list[int]:
    """Assign each yard index to one of k shards (returns yard -> shard).

    Recursive bisection along the longer axis of the group's extent, cut at
    the vehicle-weighted split closest to the leaf-count ratio, so shards are
    compact regions of roughly equal vehicle counts. Deterministic: same yards
    and counts -> same assignment. Yards without coordinates go to the
    smallest shard (distance math can't place them anyway)."""
    located = [i for i, y in enumerate(yards) if y[lat_i] is not None and y[lng_i] is not None]
    groups: list[list[int]] = []

    def split(idx: list[int], leaves: int) -> None:
        if leaves <= 1 or len(idx) <= 1:
            groups.append(idx)
            # Pad with empty groups if a branch ran out of yards to split.
            for _ in range(leaves - 1):
                groups.append([])
            return
        lat0 = sum(yards[i][lat_i] for i in idx) / len(idx)
        c = math.cos(math.radians(lat0))
        lats = [yards[i][lat_i] for i in idx]
        lngs = [yards[i][lng_i] * c for i in idx]
        by_lat = (max(lats) - min(lats)) >= (max(lngs) - min(lngs))
        a, b = (lat_i, lng_i) if by_lat else (lng_i, lat_i)
        idx = sorted(idx, key=lambda i: (yards[i][a], yards[i][b], str(yards[i][0])))
        left = leaves // 2
        total = sum(counts[i] for i in idx)
        target = total * left / leaves
        acc, cut, best = 0, 1, None
        for j in range(1, len(idx)):
            acc += counts[idx[j - 1]]
            d = abs(acc - target)
            if best is None or d < best:
                best, cut = d, j
        split(idx[:cut], left)
        split(idx[cut:], leaves - left)

    split(located, k)
    out = [0] * len(yards)
    for s, g in enumerate(groups):
        for i in g:
            out[i] = s
    sizes = [sum(counts[i] for i in g) for g in groups]
    smallest = min(range(len(groups)), key=lambda s: sizes[s]) if groups else 0
    for i, y in enumerate(yards):
        if y[lat_i] is None or y[lng_i] is None:
            out[i] = smallest
    return out


def _dump(path: Path, obj) -> int:
    data = json.dumps(obj, separators=(",", ":"))
    path.write_text(data)
    return len(data)


def write_inventory_shards(payload: dict, extras: dict | None, data_dir: Path,
                           shard_count: int = SHARD_COUNT,
                           key_buckets: int = KEY_BUCKETS) -> dict:
    """Write docs/data/inv/ for one scan payload (schema v2, exactly what was
    written to inventory_live.json) plus its extras map (vehicle id -> list,
    exactly what was written to vehicle_extras.json). Returns a summary."""
    if payload.get("schemaVersion") != 2:
        raise ValueError("inventory shards need a schema v2 payload")
    fields = payload["fields"]
    fi = {n: i for i, n in enumerate(fields)}
    yf = payload.get("yardFields") or []
    yi = {n: i for i, n in enumerate(yf)}
    yards = payload.get("yards") or []
    vehicles = payload.get("vehicles") or []
    vpic = payload.get("vpic") or {}
    extras = extras or {}
    scraped_at = payload.get("scrapedAt")
    i_yard = fi["yard"]

    counts = [0] * len(yards)
    for r in vehicles:
        counts[r[i_yard]] += 1
    yard_shard = shard_yards(yards, counts, shard_count,
                             lat_i=yi.get("lat", 3), lng_i=yi.get("lng", 4))

    rows_by: list[list] = [[] for _ in range(shard_count)]
    gpos_by: list[list[int]] = [[] for _ in range(shard_count)]
    vpic_by: list[dict] = [{} for _ in range(shard_count)]
    extras_by: list[dict] = [{} for _ in range(shard_count)]
    keys_by: list[list[dict[int, list[int]]]] = [[{} for _ in range(shard_count)]
                                                 for _ in range(key_buckets)]
    for g, r in enumerate(vehicles):
        s = yard_shard[r[i_yard]]
        li = len(rows_by[s])
        rows_by[s].append(r)
        gpos_by[s].append(g)
        vp = vpic.get(str(g))
        if vp is not None:
            vpic_by[s][str(li)] = vp
        ex = extras.get(_js_string(r[fi["id"]]) or "")
        if ex is not None:
            extras_by[s][str(li)] = ex
        for key in vehicle_keys(r, fi):
            h = fnv1a32(key)
            keys_by[h % key_buckets][s].setdefault(h, None)

    out_dir = data_dir / INV_DIRNAME
    out_dir.mkdir(parents=True, exist_ok=True)
    # The manifest goes last and is removed first: a half-written directory
    # must never be advertised (the app falls back to the full file when the
    # manifest is missing).
    manifest_path = out_dir / "manifest.json"
    if manifest_path.exists():
        manifest_path.unlink()

    sizes: list[int] = []
    for s in range(shard_count):
        gp = gpos_by[s]
        deltas = [gp[0]] + [gp[j] - gp[j - 1] for j in range(1, len(gp))] if gp else []
        sizes.append(_dump(out_dir / f"shard-{s:02d}.json", {
            "scrapedAt": scraped_at, "shard": s, "pos": deltas, "vehicles": rows_by[s],
            "vpic": vpic_by[s], "extras": extras_by[s],
        }))
    for b in range(key_buckets):
        _dump(out_dir / f"keys-{b:02d}.json", {
            "scrapedAt": scraped_at,
            "s": {str(s): " ".join(_b36(h) for h in sorted(keys_by[b][s]))
                  for s in range(shard_count) if keys_by[b][s]},
        })
    _dump(out_dir / "partsets.json", {"scrapedAt": scraped_at, "partSets": payload.get("partSets") or []})

    # Files from an older layout (different shard/bucket count) must not
    # linger next to the new ones.
    keep = {f"shard-{s:02d}.json" for s in range(shard_count)}
    keep |= {f"keys-{b:02d}.json" for b in range(key_buckets)}
    keep |= {"partsets.json", "manifest.json"}
    for p in out_dir.glob("*.json"):
        if p.name not in keep:
            p.unlink()

    _dump(manifest_path, {
        "schemaVersion": 2,
        "shardLayout": SHARD_LAYOUT,
        "scrapedAt": scraped_at,
        "pricesLastReviewed": payload.get("pricesLastReviewed"),
        "fields": fields,
        "yardFields": yf,
        "yards": yards,
        "yardShard": yard_shard,
        "yardCount": counts,
        "vehicles": len(vehicles),
        "shards": [len(rows_by[s]) for s in range(shard_count)],
        "keyBuckets": key_buckets,
    })
    return {"shards": shard_count, "vehicles": len(vehicles),
            "minShard": min(len(r) for r in rows_by), "maxShard": max(len(r) for r in rows_by),
            "shardBytes": sum(sizes)}


def remove_inventory_shards(data_dir: Path) -> None:
    """Un-advertise the shards (the app then loads the full file). Used when
    writing them failed, so a stale set from an older scan is never served
    next to a fresh inventory_live.json."""
    try:
        (data_dir / INV_DIRNAME / "manifest.json").unlink()
    except FileNotFoundError:
        pass


def main() -> None:
    """Rebuild docs/data/inv/ from the committed inventory_live.json +
    vehicle_extras.json (no network): python scraper/inventory_shards.py"""
    data_dir = Path(__file__).resolve().parent.parent / "docs" / "data"
    payload = json.loads((data_dir / "inventory_live.json").read_text())
    try:
        extras = json.loads((data_dir / "vehicle_extras.json").read_text()).get("extras", {})
    except FileNotFoundError:
        extras = {}
    print(write_inventory_shards(payload, extras, data_dir))


if __name__ == "__main__":
    main()
