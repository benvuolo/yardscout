#!/usr/bin/env python3
"""Frequency-weighted pull-cost coverage audit.

Replicates the app.js lookupYardCost() logic offline:
  - parses PART_KEYWORD_MAP out of docs/app.js with a regex,
  - walks every vehicle in docs/data/inventory_live.json,
  - for each part in the vehicle's partSet, routes to the vehicle's chain
    (by yard display-name prefix, same rules as _lookupYardCostUncached)
    and checks whether the keyword-mapped item actually exists on that
    chain's published price list.

An instance counts as MAPPED only when a real price would be shown in the
UI (no estimated fallbacks — same strict honesty rule as the app).

Usage: python3 scraper/_audit_pullcost_map.py [--top N]
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DATA = DOCS / "data"


def parse_keyword_map(app_js_text: str) -> list[dict]:
    """Extract PART_KEYWORD_MAP entries from app.js source."""
    m = re.search(r"const PART_KEYWORD_MAP = \[(.*?)\n\];", app_js_text, re.S)
    if not m:
        raise SystemExit("PART_KEYWORD_MAP not found in app.js")
    body = m.group(1)
    entries = []
    for em in re.finditer(r"\{([^{}]*)\}", body):
        entry = {}
        for fm in re.finditer(r"(\w+):\s*'((?:[^'\\]|\\.)*)'", em.group(1)):
            entry[fm.group(1)] = fm.group(2).replace("\\'", "'")
        if "kw" in entry:
            entries.append(entry)
    return entries


def best_match(part_lower: str, keyword_map: list[dict]) -> dict | None:
    """Longest matching keyword wins — mirrors _lookupYardCostUncached."""
    best, best_len = None, 0
    for entry in keyword_map:
        kw = entry["kw"]
        if kw in part_lower and len(kw) > best_len:
            best, best_len = entry, len(kw)
    return best


def load_pricing() -> dict:
    def items_by_desc(path: Path) -> dict:
        if not path.exists():
            return {}
        return {row["description"]: row for row in json.loads(path.read_text())}

    def per_yard(path: Path) -> dict:
        if not path.exists():
            return {}
        return json.loads(path.read_text())

    return {
        "pnp": items_by_desc(DATA / "picknpull_pricing.json"),
        "tap": items_by_desc(DATA / "tearapart_pricing.json"),
        "utpap": items_by_desc(DATA / "utpap_pricing.json"),
        "upullr": items_by_desc(DATA / "upullr_pricing.json"),
        "pyp": per_yard(DATA / "pyp_pricing.json"),      # keyed by yard name
        "pap": per_yard(DATA / "pap_pricing.json"),      # keyed by yard name
        "wap": per_yard(DATA / "wap_pricing.json"),      # keyed by yard name
    }


def chain_for_location(loc_lower: str) -> str | None:
    """Same prefix routing as _lookupYardCostUncached in app.js."""
    if loc_lower.startswith("tear-a-part"):
        return "tap"
    if loc_lower.startswith("pick-n-pull"):
        return "pnp"
    if loc_lower.startswith("utah pic-a-part"):
        return "utpap"
    if loc_lower.startswith("pick your part"):
        return "pyp"
    if loc_lower.startswith("pull-a-part"):
        return "pap"
    if "wrench-a-part" in loc_lower:  # Primo/Roosevelt prefixes vary
        return "wap"
    if loc_lower.startswith("u-pull-r"):
        return "upullr"
    return None


def is_mapped(entry: dict | None, chain: str | None, location: str,
              pricing: dict) -> bool:
    if not entry or not chain:
        return False
    item = entry.get(chain)
    if not item:
        return False
    if chain in ("pyp", "pap", "wap"):
        yard = pricing[chain].get(location)
        return bool(yard and item in yard)
    return item in pricing[chain]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=40,
                    help="how many top unmapped parts to list")
    args = ap.parse_args()

    keyword_map = parse_keyword_map((DOCS / "app.js").read_text())
    pricing = load_pricing()
    inv = json.loads((DATA / "inventory_live.json").read_text())

    yard_names = [y[0] for y in inv["yards"]]
    fields = inv["fields"]
    yard_idx = fields.index("yard")
    partset_idx = fields.index("partSet")
    part_sets = inv["partSets"]

    total = mapped = 0
    unmapped = Counter()            # part name -> instances (all chains)
    unmapped_no_kw = Counter()      # subset: no keyword matched at all
    per_chain = Counter()
    per_chain_mapped = Counter()

    # memoize per (partSet index, yard index) — vehicles repeat these heavily
    memo: dict[tuple[int, int], tuple[int, int, list[str]]] = {}

    for v in inv["vehicles"]:
        yi, pi = v[yard_idx], v[partset_idx]
        key = (pi, yi)
        if key not in memo:
            location = yard_names[yi]
            loc_lower = location.lower()
            chain = chain_for_location(loc_lower)
            t = m = 0
            misses: list[str] = []
            for part in part_sets[pi]:
                name = part["name"]
                t += 1
                entry = best_match(name.lower(), keyword_map)
                if is_mapped(entry, chain, location, pricing):
                    m += 1
                else:
                    misses.append(name if entry else name + "\x00")
            memo[key] = (t, m, misses)
        t, m, misses = memo[key]
        total += t
        mapped += m
        loc_lower = yard_names[yi].lower()
        chain = chain_for_location(loc_lower) or "other"
        per_chain[chain] += t
        per_chain_mapped[chain] += m
        for miss in misses:
            if miss.endswith("\x00"):
                unmapped_no_kw[miss[:-1]] += 1
                unmapped[miss[:-1]] += 1
            else:
                unmapped[miss] += 1

    pct = 100.0 * mapped / total if total else 0.0
    print(f"Instances (part x vehicle): {total:,}")
    print(f"Mapped to a real price-list item: {mapped:,} ({pct:.1f}%)")
    print()
    print("Per chain:")
    for chain in sorted(per_chain, key=lambda c: -per_chain[c]):
        t, m = per_chain[chain], per_chain_mapped[chain]
        print(f"  {chain:6s} {m:>9,}/{t:>9,}  ({100.0*m/t:5.1f}%)")
    print()
    print(f"Top {args.top} unmapped parts (by instance count):")
    for name, n in unmapped.most_common(args.top):
        nk = " [no keyword]" if unmapped_no_kw.get(name) else ""
        print(f"  {n:>7,}  {name}{nk}")


if __name__ == "__main__":
    main()
