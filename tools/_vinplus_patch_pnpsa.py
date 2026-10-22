#!/usr/bin/env python3
"""Final patch pass: San Antonio Pick-N-Pull only, with connection retries
(the dev Mac's network dropped twice mid-run; the API itself is healthy).
Monkeypatches requests.post with up to 5 attempts + 15s backoff so a brief
DNS blip can't hole a make again, then rebuilds just this yard in the
payload the way tools/_vinplus_patch_merge.py did."""
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("VPIC_MAX_PER_RUN", "0")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))
import junkyard_scraper as js  # noqa: E402

_orig_post = js.requests.post


def _retrying_post(*a, **kw):
    last = None
    for attempt in range(5):
        try:
            return _orig_post(*a, **kw)
        except Exception as e:  # noqa: BLE001 — connection-level only in practice
            last = e
            print(f"    retry {attempt + 1}/5 after {e.__class__.__name__}", flush=True)
            time.sleep(15)
    raise last


js.requests.post = _retrying_post

tenant, loc_id = "pick_n_pull_san_antonio", ""
yard = js.VINPLUS_TENANTS[tenant][loc_id]

r = js.requests.get(f"{js.VINPLUS_API}/api/vehicle-groups", headers=js.HEADERS, timeout=60)
r.raise_for_status()
makes = sorted((r.json().get("data") or {}).keys())

loc_rows = []
for mk in makes:
    loc_rows.extend(js._vinplus_search(tenant, mk, None))
print(f"fetched {len(loc_rows)} raw rows", flush=True)

vehicles = []
for row in loc_rows:
    stock = str(row.get("stock") or "").strip()
    if not stock:
        continue
    vin = str(row.get("vin") or "").strip().upper()
    date_s = str(row.get("dateAdded") or "")[:10]
    try:
        year_i = int(row.get("year") or 0)
    except (TypeError, ValueError):
        year_i = 0
    engine = str(row.get("engine") or "").strip()
    vehicles.append({
        "id": f"vinplus-{yard['code']}-{stock.lower()}",
        "vin": vin if len(vin) == 17 else "",
        "year": year_i,
        "make": js._utpap_format_label(str(row.get("make") or "")),
        "model": js._utpap_format_label(str(row.get("model") or "")),
        "row": str(row.get("vehicleRow") or "").strip(),
        "dateAdded": date_s,
        "_color": str(row.get("color") or "").strip().title(),
        **({"_engine": engine} if engine else {}),
        "_location": yard["name"],
        "_city": yard["city"],
        "_state": yard["state"],
        "_lat": yard["lat"],
        "_lng": yard["lng"],
        "_source": "vinplus",
    })
seen = set()
vehicles = [v for v in vehicles if not (v["id"] in seen or seen.add(v["id"]))]
print(f"{yard['name']}: {len(vehicles)} vehicles", flush=True)

vehicles = js.enrich_vehicles(vehicles, decode_vins=False,
                              decode_vins_profit_top=0,
                              decode_vins_incremental=True)
payload = js.build_inventory_json_payload(vehicles, only_matches=False)
extras = payload.pop("_extras", {})

prev = json.loads(js.LIVE_FILE.read_text())
prev_extras = json.loads(js.EXTRAS_FILE.read_text()).get("extras", {})
ours = {y[0] for y in payload["yards"]}
carry = [y[0] for y in prev["yards"] if y[0] not in ours]
js.merge_carryforward_yards(payload, prev, carry,
                            new_extras=extras, prev_extras=prev_extras)
js.LIVE_FILE.write_text(json.dumps(payload, separators=(",", ":")))
js.EXTRAS_FILE.write_text(json.dumps(
    {"version": 1, "scrapedAt": payload["scrapedAt"],
     "extraFields": ["photo", "color", "engine", "trans", "transSrc"],
     "extras": extras}, separators=(",", ":")))
print(f"saved {len(payload['vehicles'])} vehicles across "
      f"{len(payload['yards'])} yards", flush=True)
