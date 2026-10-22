#!/usr/bin/env python3
"""One-off targeted publish for the 2026-10-22 VinPlus expansion/migration:
fetch ONLY the VinPlus adapter (now 20 locations incl. the 4 new tenants and
the migrated Chesterfield + Go Pull-It chains), enrich, build a payload from
those vehicles, then carry forward every OTHER yard from the last published
payload via merge_carryforward_yards. Writes LIVE_FILE + EXTRAS_FILE.

VPIC_MAX_PER_RUN=0 is set so the incremental decode reuses cached decodes
only (zero NHTSA calls); fresh VINs get decoded by the next scheduled scan."""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("VPIC_MAX_PER_RUN", "0")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))
import junkyard_scraper as js  # noqa: E402

vehicles = js.fetch_vinplus_inventory()
print(f"fetched {len(vehicles)} VinPlus vehicles", flush=True)
by_loc = {}
for v in vehicles:
    by_loc[v["_location"]] = by_loc.get(v["_location"], 0) + 1
for n, c in sorted(by_loc.items()):
    print(f"  {n}: {c}", flush=True)

vehicles = js.enrich_vehicles(vehicles, decode_vins=False,
                              decode_vins_profit_top=0,
                              decode_vins_incremental=True)
payload = js.build_inventory_json_payload(vehicles, only_matches=False)
extras = payload.pop("_extras", {})

prev = json.loads(js.LIVE_FILE.read_text())
prev_extras = json.loads(js.EXTRAS_FILE.read_text()).get("extras", {})
ours = {y[0] for y in payload["yards"]}
carry = [y[0] for y in prev["yards"] if y[0] not in ours]
print(f"fresh yards: {len(ours)}; carrying forward {len(carry)} yards from the "
      f"last published payload ({prev['scrapedAt']})", flush=True)
js.merge_carryforward_yards(payload, prev, carry,
                            new_extras=extras, prev_extras=prev_extras)

js.LIVE_FILE.write_text(json.dumps(payload, separators=(",", ":")))
js.EXTRAS_FILE.write_text(json.dumps(
    {"version": 1, "scrapedAt": payload["scrapedAt"],
     "extraFields": ["photo", "color", "engine", "trans", "transSrc"],
     "extras": extras}, separators=(",", ":")))
print(f"saved {len(payload['vehicles'])} vehicles across "
      f"{len(payload['yards'])} yards -> {js.LIVE_FILE}", flush=True)
print(f"saved {len(extras)} extras entries -> {js.EXTRAS_FILE}", flush=True)
