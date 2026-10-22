#!/usr/bin/env python3
"""Inventory-weighted interchange gap audit.

Which (make, model, year-range) clusters have the MOST live vehicles yet
return "no interchange data" for alternator/starter — i.e. the car matches no
ENGINE_FAMILIES application at all? Clusters are contiguous uncovered year
runs per (make, model). Also prints the headline coverage % (share of the
inventory inside >=1 engine family) so before/after can be compared.

  python3 scraper/interchange_gap_audit.py [--top 25]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "docs" / "data"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()

    inv = json.loads((DATA / "inventory_live.json").read_text())
    f_idx = {k: i for i, k in enumerate(inv["fields"])}
    vehicles = inv["vehicles"]
    total = len(vehicles)

    # (make, model) -> year -> [covered_count, uncovered_count]
    by_mm: dict[tuple[str, str], dict[int, list[int]]] = defaultdict(
        lambda: defaultdict(lambda: [0, 0]))
    covered = 0
    for row in vehicles:
        year = row[f_idx["year"]] or 0
        make = (row[f_idx["make"]] or "").strip()
        model = (row[f_idx["model"]] or "").strip()
        hit = any(
            js._app_matches(a, year, make, model)
            for fam in js.ENGINE_FAMILIES.values() for a in fam["apps"])
        if hit:
            covered += 1
        if make and model and year:
            by_mm[(make, model)][year][0 if hit else 1] += 1

    print(f"inventory vehicles: {total:,}")
    print(f"in >=1 engine family: {covered:,}  ({covered / total:.1%})")
    print()

    # Contiguous uncovered year runs per (make, model). A year belongs to a
    # gap run when NONE of its cars are covered (families match whole model
    # years, so coverage within a year is all-or-nothing anyway).
    clusters = []
    for (make, model), years in by_mm.items():
        gap_years = sorted(y for y, (cov, unc) in years.items()
                           if unc > 0 and cov == 0)
        run: list[int] = []
        for y in gap_years + [None]:
            if run and (y is None or y != run[-1] + 1):
                n = sum(years[r][1] for r in run)
                clusters.append((n, make, model, run[0], run[-1]))
                run = []
            if y is not None:
                run.append(y)
    clusters.sort(key=lambda c: (-c[0], c[1], c[2], c[3]))

    print(f"top {args.top} uncovered clusters (no alternator/starter interchange data):")
    print(f"{'rank':>4} {'vehicles':>9}  {'make':14s} {'model':22s} years")
    for i, (n, make, model, lo, hi) in enumerate(clusters[:args.top], 1):
        print(f"{i:>4} {n:>9,}  {make:14s} {model:22s} {lo}-{hi}")


if __name__ == "__main__":
    main()
