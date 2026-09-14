#!/usr/bin/env python3
"""Push an inventory build to the YardScout API backend (Cloudflare Worker).

Runs in the scan workflow right after the scraper (and works identically
against a local `wrangler dev` server for testing). Splits the big
inventory_live.json into small per-yard shards in TWO tier variants, so the
Worker can serve radius queries by streaming pre-built blobs without ever
parsing the 22MB file (the Workers free plan allows ~10ms CPU per request):

  free — vehicles + arrival dates + part NAMES; dollar values (maxValue,
         part low/high/cost, sell-channel/demand data) stripped
  pro  — everything the scraper produced

Also builds:
  partsets/all/{free,pro} — the shared partSets lookup table
  vindex/{0..63}/all      — id/VIN → yard index, for /v1/vehicles/:id deep links

Only shards whose content hash changed since the last push are uploaded
(the API keeps the manifest), then a commit finalizes the new directory.

Usage:
  python scraper/push_inventory.py [--file docs/data/inventory_live.json]
      [--api https://yardscout-api.<acct>.workers.dev] [--token <UPLOAD_TOKEN>]
      [--max-yards N] [--dry-run]

--api / --token default to the YS_API_URL / YS_UPLOAD_TOKEN env vars.
Standard library only — no pip installs in CI.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

VINDEX_MOD = 64  # must match vindexBucket() in backend/src/util.js

# Vehicle row layout (schema v2 "fields"):
#   0=id 1=vin 2=year 3=make 4=model 5=row 6=dateAdded 7=yard 8=partSet
#   9=maxValue 10=premium
IDX_ID, IDX_VIN, IDX_YARD, IDX_PARTSET, IDX_MAXVALUE, IDX_PREMIUM = 0, 1, 7, 8, 9, 10

# Free tier matches the app's existing free contract (see the card renderer in
# docs/app.js): part names, rarity, trim caveat, and sell channel stay visible;
# dollar values (low/high resale, pull cost) and demand speed are Pro-only.
FREE_PART_KEYS = ("name", "rarity", "trim_status", "sell_at")


def vindex_bucket(token: str, mod: int = VINDEX_MOD) -> int:
    """Sum of UTF-8 bytes mod N — mirrored in backend/src/util.js."""
    return sum(token.encode("utf-8")) % mod


def canonical(obj) -> bytes:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def pack(obj) -> tuple[bytes, str]:
    """(gzipped bytes, sha256-of-uncompressed). mtime=0 keeps gzip deterministic
    so unchanged shards hash identically across runs."""
    raw = canonical(obj)
    return gzip.compress(raw, 9, mtime=0), hashlib.sha256(raw).hexdigest()


def build_shards(data: dict, max_yards: int | None = None) -> tuple[dict, dict]:
    """Returns (directory, shards) where shards maps "kind/key/variant" →
    (gzipped_body, sha256)."""
    yards = data["yards"]
    vehicles = data["vehicles"]
    vpic = data.get("vpic", {})
    partsets = data["partSets"]

    yard_cap = len(yards) if max_yards is None else min(max_yards, len(yards))
    kept_yards = set(range(yard_cap))

    per_yard: dict[int, dict] = {i: {"vehicles": [], "vpic": {}} for i in kept_yards}
    vindex: dict[int, dict] = {b: {} for b in range(VINDEX_MOD)}
    n_vehicles = 0

    for i, row in enumerate(vehicles):
        y = row[IDX_YARD]
        if y not in kept_yards:
            continue
        n_vehicles += 1
        per_yard[y]["vehicles"].append(row)
        vp = vpic.get(str(i))
        if vp:
            # Re-key vpic by vehicle id: global positions don't survive sharding.
            per_yard[y]["vpic"][str(row[IDX_ID])] = vp
        vid = str(row[IDX_ID])
        vindex[vindex_bucket(vid)][vid] = [y, row[IDX_ID]]
        vin = str(row[IDX_VIN] or "").strip().upper()
        if len(vin) >= 11:
            vindex[vindex_bucket(vin)][vin] = [y, row[IDX_ID]]

    shards: dict[str, tuple[bytes, str]] = {}

    for y, shard in per_yard.items():
        shards[f"yard/{y}/pro"] = pack(shard)
        free_rows = []
        for r in shard["vehicles"]:
            fr = list(r)
            fr[IDX_MAXVALUE] = 0   # dollar value — Pro only
            fr[IDX_PREMIUM] = 0    # premium price-row flag — pricing data
            free_rows.append(fr)
        shards[f"yard/{y}/free"] = pack({"vehicles": free_rows, "vpic": shard["vpic"]})

    shards["partsets/all/pro"] = pack(partsets)
    shards["partsets/all/free"] = pack([
        [{k: p[k] for k in FREE_PART_KEYS if k in p} for p in ps]
        for ps in partsets
    ])

    for b, entries in vindex.items():
        if entries:
            shards[f"vindex/{b}/all"] = pack(entries)

    directory = {
        "schemaVersion": data.get("schemaVersion", 2),
        "scrapedAt": data.get("scrapedAt"),
        "pricesLastReviewed": data.get("pricesLastReviewed"),
        "fields": data["fields"],
        "yardFields": data.get("yardFields", []),
        "yards": [yards[i] for i in sorted(kept_yards)],
        "vindexMod": VINDEX_MOD,
        "counts": {"yards": yard_cap, "vehicles": n_vehicles},
    }
    return directory, shards


def _request(url: str, method: str, headers: dict, body: bytes | None, attempts: int = 4):
    last = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, data=body, method=method, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if e.code in (429, 500, 502, 503, 504) and attempt < attempts - 1:
                last = f"HTTP {e.code}: {detail}"
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f"FATAL {method} {url} → HTTP {e.code}: {detail}")
        except (urllib.error.URLError, TimeoutError) as e:
            last = str(e)
            if attempt < attempts - 1:
                time.sleep(2 ** attempt)
                continue
    raise SystemExit(f"FATAL {method} {url} → {last}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", default="docs/data/inventory_live.json")
    ap.add_argument("--api", default=os.environ.get("YS_API_URL", ""))
    ap.add_argument("--token", default=os.environ.get("YS_UPLOAD_TOKEN", ""))
    ap.add_argument("--max-yards", type=int, default=None,
                    help="only push the first N yards (local testing)")
    ap.add_argument("--dry-run", action="store_true",
                    help="build shards and report sizes; no network")
    args = ap.parse_args()

    with open(args.file, encoding="utf-8") as f:
        data = json.load(f)
    if data.get("schemaVersion") != 2:
        raise SystemExit(f"FATAL: expected schemaVersion 2, got {data.get('schemaVersion')!r}")

    directory, shards = build_shards(data, args.max_yards)
    total_gz = sum(len(b) for b, _ in shards.values())
    print(f"Built {len(shards)} shards ({directory['counts']['vehicles']} vehicles, "
          f"{directory['counts']['yards']} yards, {total_gz / 1e6:.1f}MB gzipped)")

    if args.dry_run:
        biggest = sorted(shards.items(), key=lambda kv: -len(kv[1][0]))[:5]
        for k, (b, sha) in biggest:
            print(f"  {k:22s} {len(b):>8,} bytes gz  sha {sha[:12]}")
        return 0

    api = args.api.rstrip("/")
    if not api or not args.token:
        raise SystemExit("FATAL: --api/--token (or YS_API_URL / YS_UPLOAD_TOKEN) required")
    auth = {"x-upload-token": args.token}

    remote = _request(f"{api}/v1/admin/inventory/manifest", "GET", auth, None)
    remote_manifest = remote.get("manifest", {})

    manifest = {key: sha for key, (_, sha) in shards.items()}
    changed = [key for key, sha in manifest.items() if remote_manifest.get(key) != sha]
    print(f"{len(changed)} of {len(shards)} shards changed since last push")

    def put(key: str):
        body, sha = shards[key]
        _request(
            f"{api}/v1/admin/inventory/shard/{key}", "PUT",
            {**auth, "content-type": "application/octet-stream", "x-content-sha256": sha},
            body,
        )
        return key

    failed = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(put, key): key for key in changed}
        done = 0
        for fut in as_completed(futures):
            try:
                fut.result()
                done += 1
                if done % 50 == 0:
                    print(f"  uploaded {done}/{len(changed)}")
            except SystemExit as e:
                failed.append((futures[fut], str(e)))
    if failed:
        for key, msg in failed[:5]:
            print(f"  FAILED {key}: {msg}", file=sys.stderr)
        raise SystemExit(f"FATAL: {len(failed)} shard uploads failed — not committing")

    result = _request(
        f"{api}/v1/admin/inventory/commit", "POST",
        {**auth, "content-type": "application/json"},
        canonical({"directory": directory, "manifest": manifest}),
    )
    print(f"Committed: {result.get('shards')} shards live, {result.get('pruned', 0)} pruned, "
          f"scrapedAt {result.get('scrapedAt')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
