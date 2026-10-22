#!/usr/bin/env python3
"""Engine-family coverage report against the published inventory.

For each ENGINE_FAMILIES entry: how many live vehicles are an application of
the family, how many of those have a VIN-decode engine string that CONFIRMS
the family engine, how many are denied (other engine), and how many have no
usable engine data. The headline number is the share of the whole inventory
reachable as a DONOR through at least one family — the owner's "what % of the
250k vehicles are covered" metric.

    python3 scraper/interchange_coverage.py [--csv out.csv]
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "docs" / "data"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path)
    args = ap.parse_args()

    inv = json.loads((DATA / "inventory_live.json").read_text())
    with gzip.open(DATA / "vin_decodes.json.gz") as f:
        decodes = json.load(f)

    f_idx = {k: i for i, k in enumerate(inv["fields"])}
    vehicles = inv["vehicles"]
    total = len(vehicles)

    per_fam: dict[str, dict] = {
        fid: {"display": fam["display"], "app_hits": 0, "confirmed": 0,
              "denied": 0, "no_data": 0}
        for fid, fam in js.ENGINE_FAMILIES.items()
    }
    covered_rows = 0          # vehicle matches >=1 family app (engine not denied)
    confirmed_rows = 0        # vehicle engine-confirmed for >=1 family

    for row in vehicles:
        year = row[f_idx["year"]] or 0
        make = row[f_idx["make"]] or ""
        model = row[f_idx["model"]] or ""
        vin = row[f_idx["vin"]] or ""
        dec = decodes.get(vin)
        engine = dec.get("engine", "") if isinstance(dec, dict) else ""
        row_covered = row_confirmed = False
        for fid, fam in js.ENGINE_FAMILIES.items():
            hit = any(js._app_matches(a, year, make, model) for a in fam["apps"])
            if not hit:
                continue
            st = per_fam[fid]
            st["app_hits"] += 1
            verdict = js.engine_matches_family(engine, fam)
            if verdict is True:
                st["confirmed"] += 1
                row_confirmed = True
                row_covered = True
            elif verdict is False:
                st["denied"] += 1
            else:
                st["no_data"] += 1
                row_covered = True
        if row_covered:
            covered_rows += 1
        if row_confirmed:
            confirmed_rows += 1

    ranked = sorted(per_fam.items(),
                    key=lambda t: -(t[1]["confirmed"] + t[1]["no_data"]))
    print(f"inventory vehicles: {total:,}")
    print(f"donor-covered (>=1 family, engine not denied): {covered_rows:,}"
          f"  ({covered_rows / total:.1%})")
    print(f"engine-CONFIRMED donors: {confirmed_rows:,}"
          f"  ({confirmed_rows / total:.1%})")
    print()
    print(f"{'rank':>4} {'family':28s} {'conf':>7} {'nodata':>7} "
          f"{'denied':>7} {'display'}")
    for i, (fid, st) in enumerate(ranked, 1):
        print(f"{i:>4} {fid:28s} {st['confirmed']:>7,} {st['no_data']:>7,} "
              f"{st['denied']:>7,} {st['display']}")

    if args.csv:
        import csv
        with args.csv.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["family", "display", "confirmed", "no_data", "denied"])
            for fid, st in ranked:
                w.writerow([fid, st["display"], st["confirmed"],
                            st["no_data"], st["denied"]])
        print(f"\nwrote {args.csv}")


if __name__ == "__main__":
    main()
