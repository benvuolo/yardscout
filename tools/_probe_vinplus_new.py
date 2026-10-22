#!/usr/bin/env python3
"""One-off probe: searchVehicleHttp against the new VinPlus tenants.
Checks which location_id form works for single-location tenants and samples
row fields. Polite: 2s between requests."""
import json
import sys
import time

import requests

API = "https://inventory-search-api-581547763015.us-central1.run.app"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"}

CASES = [
    # (tenant, location_id, make)
    ("joliet_u_pull_it", None, "Toyota"),
    ("pick_n_pull_san_antonio", None, "Toyota"),
    ("195_used_auto_parts", None, "Toyota"),
    ("pick_ur_part", None, "Toyota"),
    ("go_pull_it", "tallahassee", "Toyota"),
    ("chesterfield_auto_parts", "richmond", "Toyota"),
]

for tenant, loc, make in CASES:
    time.sleep(2)
    r = requests.post(f"{API}/searchVehicleHttp",
                      json={"yard_id": tenant, "make": make, "model": None,
                            "year_min": None, "year_max": None,
                            "location_id": loc},
                      headers=UA, timeout=60)
    try:
        d = r.json()
    except Exception:
        print(f"{tenant}/{loc}: HTTP {r.status_code}, non-JSON: {r.text[:200]}")
        continue
    rows = d.get("matches") or []
    print(f"{tenant}/{loc} make={make}: status={r.status_code} "
          f"match_count={d.get('match_count')} rows={len(rows)}")
    if rows:
        sample = rows[0]
        print("  keys:", sorted(sample.keys()))
        print("  sample:", json.dumps(sample)[:400])
        locs = {str(x.get("yardLocation")) for x in rows}
        srcs = {str(x.get("sourceSystem")) for x in rows}
        print(f"  yardLocation values: {sorted(locs)[:6]}  sourceSystem: {sorted(srcs)}")
    sys.stdout.flush()
