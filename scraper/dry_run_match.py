#!/usr/bin/env python3
"""Offline matcher dry-run over the cached inventory JSON.

Replays every vehicle in docs/data/inventory_live.json (schema v2) through
match_vehicle() with the CURRENT UNOBTANIUM_DB — no network calls — and
reports coverage: how many vehicles match, which make/models have zero
coverage, and which vehicles match more than one DB entry (double-match /
shadowing risk, e.g. one entry's keyword being a substring of another's).

Used to verify generation-split refactors don't regress coverage:
    python scraper/dry_run_match.py            # summary
    python scraper/dry_run_match.py --json out.json   # machine-readable
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

INVENTORY = Path(__file__).resolve().parent.parent / "docs" / "data" / "inventory_live.json"


def load_vehicles() -> list[dict]:
    data = json.loads(INVENTORY.read_text())
    if data.get("schemaVersion") != 2:
        raise SystemExit("expected schema v2 inventory_live.json")
    fields = data["fields"]
    yi, mi, moi = fields.index("year"), fields.index("make"), fields.index("model")
    vpic = data.get("vpic", {})
    out = []
    for i, r in enumerate(data["vehicles"]):
        dec = None
        vp = vpic.get(str(i))
        if vp:
            # [trim, trimQuality, series, driveType, mismatch]
            dec = {"trim": vp[0], "trimQuality": vp[1], "series": vp[2],
                   "driveType": vp[3]}
        out.append({"year": r[yi] or 0, "make": r[mi] or "", "model": r[moi] or "",
                    "vpic": dec})
    return out


def run(vehicles: list[dict]) -> dict:
    matched = 0
    unmatched: Counter = Counter()
    per_entry: Counter = Counter()
    multi: Counter = Counter()
    for v in vehicles:
        m = js.match_vehicle(v["year"], v["make"], v["model"], vin_decode=v["vpic"])
        if m:
            matched += 1
            for e in m:
                per_entry[e["display"]] += 1
            if len(m) > 1:
                multi[" + ".join(sorted(e["display"] for e in m))] += 1
        else:
            unmatched[f"{v['make']} {v['model']}".strip()] += 1
    return {
        "total": len(vehicles),
        "matched": matched,
        "unmatched_models": unmatched,
        "per_entry": per_entry,
        "multi_match": multi,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path, default=None, help="write full stats JSON")
    ap.add_argument("--top", type=int, default=40, help="rows to print per section")
    args = ap.parse_args()

    vehicles = load_vehicles()
    r = run(vehicles)
    pct = 100.0 * r["matched"] / max(1, r["total"])
    print(f"vehicles: {r['total']:,}  matched: {r['matched']:,} ({pct:.1f}%)  "
          f"unmatched: {r['total'] - r['matched']:,}")
    print(f"distinct DB entries hit: {len(r['per_entry'])}")

    print(f"\n-- top {args.top} unmatched make/models --")
    for name, n in r["unmatched_models"].most_common(args.top):
        print(f"{n:6,}  {name}")

    print(f"\n-- top {args.top} multi-match combos (shadowing check) --")
    for combo, n in r["multi_match"].most_common(args.top):
        print(f"{n:6,}  {combo}")

    if args.json:
        args.json.write_text(json.dumps({
            "total": r["total"], "matched": r["matched"],
            "unmatched_models": dict(r["unmatched_models"].most_common()),
            "per_entry": dict(r["per_entry"].most_common()),
            "multi_match": dict(r["multi_match"].most_common()),
        }, indent=1))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
