#!/usr/bin/env python3
"""Run the LIVE Ario adapter on its own and print a per-yard table — the
verification step for ARIO_CHAINS changes (counts vs the scouting pass, VIN
coverage, freshness). Uses the history DB next to this script (the ario_vins
cache), so in CI it must run after the scan-state cache restore.

    ARIO_VIN_MAX_PER_RUN=50 python3 scraper/_probe_ario_live.py
"""
from __future__ import annotations

import collections
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402


def main() -> None:
    t0 = time.time()
    vs = js.fetch_ario_inventory()
    by: dict[str, list[dict]] = collections.defaultdict(list)
    for v in vs:
        by[v["_location"]].append(v)
    print(f"\n{len(vs)} vehicles / {len(by)} yards in {time.time() - t0:.0f}s\n")
    print(f"{'yard':42s} {'cars':>5} {'VIN%':>5} {'oldest':>10} {'newest':>10} {'noDate':>6}")
    for loc, rows in sorted(by.items()):
        dates = sorted(v["dateAdded"] for v in rows if v["dateAdded"])
        vin = sum(1 for v in rows if v["vin"]) / len(rows)
        print(f"{loc:42s} {len(rows):>5} {vin:>5.0%} {dates[0] if dates else '-':>10} "
              f"{dates[-1] if dates else '-':>10} {len(rows) - len(dates):>6}")


if __name__ == "__main__":
    main()
