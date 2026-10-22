#!/usr/bin/env python3
"""Patch pass for the 2026-10-22 targeted publish: a local network outage
mid-run left three locations incomplete (San Antonio Pick-N-Pull: 22 failed
makes, 195 Used Auto Parts: 17, Chesterfield Southside: one year leaf).
Re-fetch JUST those three locations and merge them into the payload written
by tools/_vinplus_targeted_merge.py, carrying every other yard forward."""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("VPIC_MAX_PER_RUN", "0")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))
import junkyard_scraper as js  # noqa: E402

TARGETS = [
    ("pick_n_pull_san_antonio", ""),
    ("195_used_auto_parts", ""),
    ("chesterfield_auto_parts", "southside"),
]

r = js.requests.get(f"{js.VINPLUS_API}/api/vehicle-groups", headers=js.HEADERS, timeout=60)
r.raise_for_status()
makes = sorted((r.json().get("data") or {}).keys())

vehicles = []
for tenant, loc_id in TARGETS:
    yard = js.VINPLUS_TENANTS[tenant][loc_id]
    loc_rows = []
    for mk in makes:
        loc_rows.extend(js._vinplus_search(tenant, mk, loc_id or None))
    id_prefix = yard.get("id_prefix") or f"vinplus-{yard['code']}-"
    n0 = len(vehicles)
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
            "id": f"{id_prefix}{stock.lower()}",
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
            "_source": yard.get("source", "vinplus"),
        })
    print(f"{yard['name']}: {len(vehicles) - n0} vehicles", flush=True)

seen = set()
vehicles = [v for v in vehicles if not (v["id"] in seen or seen.add(v["id"]))]
vehicles = js.enrich_vehicles(vehicles, decode_vins=False,
                              decode_vins_profit_top=0,
                              decode_vins_incremental=True)
payload = js.build_inventory_json_payload(vehicles, only_matches=False)
extras = payload.pop("_extras", {})

prev = json.loads(js.LIVE_FILE.read_text())
prev_extras = json.loads(js.EXTRAS_FILE.read_text()).get("extras", {})
ours = {y[0] for y in payload["yards"]}
carry = [y[0] for y in prev["yards"] if y[0] not in ours]
print(f"fresh yards: {sorted(ours)}; carrying {len(carry)}", flush=True)
js.merge_carryforward_yards(payload, prev, carry,
                            new_extras=extras, prev_extras=prev_extras)

js.LIVE_FILE.write_text(json.dumps(payload, separators=(",", ":")))
js.EXTRAS_FILE.write_text(json.dumps(
    {"version": 1, "scrapedAt": payload["scrapedAt"],
     "extraFields": ["photo", "color", "engine", "trans", "transSrc"],
     "extras": extras}, separators=(",", ":")))
print(f"saved {len(payload['vehicles'])} vehicles across "
      f"{len(payload['yards'])} yards", flush=True)
