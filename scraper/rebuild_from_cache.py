#!/usr/bin/env python3
"""Rebuild docs/data/inventory_live.json part data after an UNOBTANIUM_DB edit
— no network calls.

Replays every cached vehicle row through the CURRENT match_vehicle() and
rewrites the deduplicated partSets table, each row's partSet index, and its
maxValue. Yard rows, lifespan columns, VIN-decode side table, photo extras,
and scrapedAt are preserved untouched — only match-derived data changes.

    python scraper/rebuild_from_cache.py            # in-place rewrite
    python scraper/rebuild_from_cache.py --out x.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

INVENTORY = Path(__file__).resolve().parent.parent / "docs" / "data" / "inventory_live.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=INVENTORY)
    args = ap.parse_args()

    data = json.loads(INVENTORY.read_text())
    if data.get("schemaVersion") != 2:
        raise SystemExit("expected schema v2 inventory_live.json")

    fields = data["fields"]
    yi, mki, mdi = fields.index("year"), fields.index("make"), fields.index("model")
    psi, mvi = fields.index("partSet"), fields.index("maxValue")
    vpic = data.get("vpic", {})

    part_sets: list[list[dict]] = []
    part_set_idx: dict[str, int] = {}
    was_matched = now_matched = 0

    for i, row in enumerate(data["vehicles"]):
        if row[psi] is not None and row[psi] >= 0:
            was_matched += 1
        dec = None
        vp = vpic.get(str(i))
        if vp:
            # side table: [trim, trimQuality, series, driveType, mismatch]
            dec = {"trim": vp[0], "trimQuality": vp[1], "series": vp[2],
                   "driveType": vp[3]}
        matches = js.match_vehicle(row[yi] or 0, row[mki] or "", row[mdi] or "",
                                   vin_decode=dec)
        if not matches:
            row[psi], row[mvi] = -1, 0
            continue
        now_matched += 1
        parts = [
            {
                "name": p["name"], "rarity": p["rarity"],
                "low": p["low"], "high": p["high"], "cost": p["cost"],
                "sell_at": p.get("sell_at", ""),
                "sell_speed": p.get("sell_speed", ""),
                "sell_notes": p.get("sell_notes", ""),
                **({"fits": p["fits"]} if p.get("fits") else {}),
                **({"trim_status": p["trim_status"]} if p.get("trim_status") else {}),
            }
            for p in matches[0]["top_parts"]
        ]
        pi = -1
        if parts:
            pkey = json.dumps(parts, sort_keys=True)
            pi = part_set_idx.get(pkey, -1)
            if pi < 0:
                pi = len(part_sets)
                part_set_idx[pkey] = pi
                part_sets.append(parts)
        row[psi] = pi
        row[mvi] = max(m["max_value"] for m in matches)

    data["partSets"] = part_sets
    data["pricesLastReviewed"] = js.PRICES_LAST_REVIEWED
    args.out.write_text(json.dumps(data, separators=(",", ":")) + "\n")
    print(f"rows: {len(data['vehicles'])}  matched before: {was_matched}  "
          f"after: {now_matched}  partSets: {len(part_sets)}  -> {args.out}")


if __name__ == "__main__":
    main()
