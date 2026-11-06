#!/usr/bin/env python3
"""Coverage miner — finds UNOBTANIUM_DB blind spots and PROPOSES groups to
curate. Zero LLM tokens, fully deterministic, offline.

Pipeline (monthly via .github/workflows/coverage-mine.yml, or run by hand):

  1. Inventory gap analysis: reads the live inventory
     (docs/data/inventory_live.json) and ranks (make, model, year-band) groups
     by vehicle count where the match rate is zero OR the matched parts are
     only generic commuter parts (headlights/mirrors/tail lights tier). Known
     enthusiast platforms (static pattern list below) present in inventory
     with thin part sets are flagged and boosted.
  2. Output: scraper/coverage_candidates.md (human review report) +
     scraper/coverage_candidates.json (machine-readable).

No eBay page fetching. CLAUDE.md rule 2: eBay data comes only through its
APIs (ebay_prices.py), never from scraped pages (robots.txt disallows /sch/).
The old sold-listing page fetcher was removed on 2026-11-04. Price evidence
for curated rows comes from the yard price lists and the eBay API feed.
`--no-fetch` is still accepted (it is now the only behaviour).

IMPORTANT: this script proposes, it never edits UNOBTANIUM_DB. Curation stays
a human/agent review step.

Usage:
  python scraper/mine_coverage_gaps.py                 # top 15 groups
  python scraper/mine_coverage_gaps.py --top 10 --min-count 40
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "docs" / "data" / "inventory_live.json"
OUT_MD = ROOT / "scraper" / "coverage_candidates.md"
OUT_JSON = ROOT / "scraper" / "coverage_candidates.json"


# Parts whose presence alone doesn't count as real coverage — every commuter
# car gets these. A group whose matched parts are ALL from this tier is still
# a coverage gap.
GENERIC_PART_TOKENS = (
    "headlight", "tail light", "taillight", "side mirror", "window regulator",
    "alternator", "wiper", "cargo cover", "door handle", "power window master",
    "spare tire cover", "corner/marker",
    # 2026-10 consensus evergreens — near-universal commodity sellers; their
    # presence alone must not make a group look richly covered.
    "starter", "gauge cluster", "climate control", "control module",
    # §24 federal-mandate rows (FMVSS 126 ESC, FMVSS 111 camera) ride on
    # every light vehicle — they never make a group look specifically covered.
    "abs / esc pump", "backup camera (match part #)",
)

# Known enthusiast platforms: (label, make substring, model regex, optional
# (yr_min, yr_max)). Matched case-insensitively against inventory make/model.
# Presence with a thin part set (zero match, generic-only, or < 4 distinct
# parts) flags the group and boosts its rank. Extend sensibly over time.
ENTHUSIAST_PLATFORMS: list[tuple[str, str, str, tuple | None]] = [
    ("Miata (NA/NB/NC/ND)",      "mazda",      r"\b(mx-?5|miata)\b", None),
    ("RX-7",                     "mazda",      r"\brx-?7\b", None),
    ("RX-8",                     "mazda",      r"\brx-?8\b", None),
    ("240SX (S13/S14)",          "nissan",     r"\b240 ?sx\b", None),
    ("300ZX",                    "nissan",     r"\b300 ?zx\b", None),
    ("Supra",                    "toyota",     r"\bsupra\b", None),
    ("MR2",                      "toyota",     r"\bmr-?2\b", None),
    ("Celica All-Trac / GT-S",   "toyota",     r"\bcelica\b", None),
    ("Land Cruiser",             "toyota",     r"\bland ?cruiser\b|\bfj\d{2}\b", None),
    ("FJ Cruiser",               "toyota",     r"\bfj cruiser\b", None),
    ("WRX/STI",                  "subaru",     r"\bwrx\b|\bsti\b|impreza", (2002, 2024)),
    ("Lancer Evo",               "mitsubishi", r"lancer.*(evo|evolution)|\bevolution\b", None),
    ("Montero/Pajero",           "mitsubishi", r"\bmontero\b|\bpajero\b", None),
    ("3000GT / Stealth",         "",           r"\b3000 ?gt\b|\bstealth\b", None),
    ("Integra/RSX",              "acura",      r"\bintegra\b|\brsx\b", None),
    ("S2000",                    "honda",      r"\bs2000\b", None),
    ("CRX / del Sol",            "honda",      r"\bcrx\b|\bdel sol\b", None),
    ("Prelude",                  "honda",      r"\bprelude\b", None),
    ("E30/E36/E46 3-Series",     "bmw",        r"\b3\d{2}i?s?\b|3-series|3 series", (1984, 2006)),
    ("Volvo 240/740/940",        "volvo",      r"\b[279]40\b|\b[27]45\b", None),
    ("W123/W124 Mercedes",       "mercedes",   r"\b(240d|300d|300e|260e|e300|e320|400e|500e)\b", (1977, 1995)),
    ("Old Bronco",               "ford",       r"\bbronco\b", (1966, 1996)),
    ("Square-body Blazer/K5",    "chevrolet",  r"\bblazer\b|\bk5\b", (1969, 1994)),
    ("Scout",                    "internation", r"\bscout\b", None),
    ("Defender",                 "land rover", r"\bdefender\b", None),
    ("Xterra",                   "nissan",     r"\bxterra\b", None),
    ("Firebird/Trans Am",        "pontiac",    r"\bfirebird\b|\btrans am\b", None),
    ("Corvette (C4/C5)",         "chevrolet",  r"\bcorvette\b", (1984, 2004)),
    ("Golf GTI / R",             "volkswagen", r"\bgti\b|\bgolf r\b", None),
    ("Tacoma (solid resale)",    "toyota",     r"\btacoma\b", None),
    ("22RE Pickup / Hilux",      "toyota",     r"\bpickup\b|\bhilux\b", (1979, 1995)),
]


# ------------------------------------------------------------ gap analysis --

def year_band(year: int) -> str:
    if not year:
        return "unknown"
    if year < 1990:
        return "pre-1990"
    lo = (year // 5) * 5
    return f"{lo}-{lo + 4}"


def band_years(band: str) -> tuple[int, int]:
    if band == "pre-1990":
        return (1960, 1989)
    if band == "unknown":
        return (0, 0)
    lo, hi = band.split("-")
    return int(lo), int(hi)


def is_generic_only(part_names: set[str]) -> bool:
    if not part_names:
        return False
    return all(any(tok in n.lower() for tok in GENERIC_PART_TOKENS) for n in part_names)


def enthusiast_match(make: str, model: str, band: str) -> str | None:
    m, mo = make.lower(), model.lower()
    b_lo, b_hi = band_years(band)
    for label, mk, rx, yrs in ENTHUSIAST_PLATFORMS:
        if mk and mk not in m:
            continue
        if not re.search(rx, mo):
            continue
        if yrs and b_lo and (b_hi < yrs[0] or b_lo > yrs[1]):
            continue
        return label
    return None


def analyze_gaps(min_count: int) -> list[dict]:
    data = json.loads(INVENTORY.read_text())
    fields = data["fields"]
    yi, mki, mdi = fields.index("year"), fields.index("make"), fields.index("model")
    psi = fields.index("partSet")
    part_sets = data["partSets"]

    groups: dict[tuple, dict] = {}
    for row in data["vehicles"]:
        make, model, year = (row[mki] or "").strip(), (row[mdi] or "").strip(), row[yi] or 0
        if not make or not model:
            continue
        key = (make, model, year_band(year))
        g = groups.setdefault(key, {"count": 0, "matched": 0, "part_names": set()})
        g["count"] += 1
        si = row[psi]
        if si is not None and si >= 0:
            g["matched"] += 1
            g["part_names"].update(p["name"] for p in part_sets[si])

    out = []
    for (make, model, band), g in groups.items():
        if g["count"] < min_count:
            continue
        match_rate = g["matched"] / g["count"]
        generic_only = g["matched"] > 0 and is_generic_only(g["part_names"])
        enth = enthusiast_match(make, model, band)
        thin = match_rate == 0 or generic_only or (enth and len(g["part_names"]) < 4)
        if not thin:
            continue
        if match_rate == 0:
            gap_kind, weight = "zero-match", 1.0
        elif generic_only:
            gap_kind, weight = "generic-only", 0.6
        else:
            gap_kind, weight = "thin-enthusiast", 0.5
        score = g["count"] * weight * (2.0 if enth else 1.0)
        out.append({
            "make": make, "model": model, "year_band": band,
            "vehicle_count": g["count"],
            "match_rate": round(match_rate, 3),
            "gap_kind": gap_kind,
            "enthusiast": enth,
            "matched_parts": sorted(g["part_names"]),
            "score": round(score, 1),
        })
    out.sort(key=lambda r: (-r["score"], r["make"], r["model"], r["year_band"]))
    return out


# ----------------------------------------------------------------- output --

def rarity_for(median: int) -> str:
    if median >= 300:
        return "Epic"
    if median >= 150:
        return "Rare"
    return "Uncommon"


def skeleton_for(group: dict, evidence: dict) -> dict:
    """Suggested UNOBTANIUM_DB entry skeleton — a human verifies before use."""
    b_lo, b_hi = band_years(group["year_band"])
    ok = [(term, ev) for term, ev in evidence.items() if ev.get("status") == "ok" and ev["count"] >= 5]
    ok.sort(key=lambda kv: -kv[1]["median"])
    parts = [{
        "name": term.title(),
        "rarity": rarity_for(ev["median"]),
        "low": max(10, ev["p25"]),
        "high": ev["p75"],
        "evidence": f"eBay sold n={ev['count']} median ${ev['median']}",
    } for term, ev in ok[:5]]
    return {
        "key": group["model"].lower(),
        "display": f"{group['make']} {group['model']}",
        "make": group["make"],
        "year_range": [b_lo or None, b_hi or None],
        "top_parts": parts,
    }


def write_outputs(gaps: list[dict], mined: list[dict], top_n: int,
                  out_md: Path, out_json: Path) -> None:
    today = date.today().isoformat()
    lines = [
        "# Coverage Candidates — automated gap mining",
        "",
        f"**Date:** {today}",
        "**Generated by:** `scraper/mine_coverage_gaps.py` (deterministic, zero LLM tokens).",
        f"**Inventory groups analyzed:** {len(gaps)} thin-coverage (make, model, year-band) "
        f"groups; the top {len(mined)} are listed in detail.",
        "",
        "**This report PROPOSES entries — nothing edits `UNOBTANIUM_DB` automatically.** "
        "Review the evidence, spot-check the sample sold titles, then hand-curate the "
        "skeletons you accept into `scraper/junkyard_scraper.py` (with the usual price "
        "audit discipline: bands calibrated to sold prices, ceiling rule vs. new parts).",
        "",
    ]
    lines += ["> Inventory-side gap ranking only. No eBay pages are fetched (CLAUDE.md "
              "rule 2); price evidence for curated rows comes from the yard price "
              "lists and the eBay API feed.", ""]
    lines += [
        "## Top coverage gaps (all thin groups, ranked)",
        "",
        "| # | Make | Model | Years | Vehicles | Match rate | Gap kind | Enthusiast platform |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for i, g in enumerate(gaps[:max(top_n * 3, 40)], 1):
        lines.append(
            f"| {i} | {g['make']} | {g['model']} | {g['year_band']} | {g['vehicle_count']:,} "
            f"| {int(g['match_rate'] * 100)}% | {g['gap_kind']} | {g['enthusiast'] or '—'} |")
    lines += ["", "## Top groups", ""]
    for m in mined:
        g = m["group"]
        lines += [
            f"### {g['make']} {g['model']} ({g['year_band']}) — {g['vehicle_count']:,} in yards",
            "",
            f"- Gap: **{g['gap_kind']}**, match rate {int(g['match_rate'] * 100)}%"
            + (f", enthusiast platform: **{g['enthusiast']}**" if g["enthusiast"] else ""),
        ]
        if g["matched_parts"]:
            lines.append(f"- Currently matched parts: {', '.join(g['matched_parts'][:8])}")
        ok_cats = {t: ev for t, ev in m["evidence"].items() if ev.get("status") == "ok"}
        failed = [t for t, ev in m["evidence"].items() if ev.get("status") != "ok"]
        if ok_cats:
            lines += ["", "| Category | Sold count | Median | P25–P75 |", "|---|---|---|---|"]
            for t, ev in sorted(ok_cats.items(), key=lambda kv: -kv[1]["median"]):
                lines.append(f"| {t} | {ev['count']} | ${ev['median']:,} | ${ev['p25']:,}–{ev['p75']:,} |")
            samples = next(iter(sorted(ok_cats.values(), key=lambda e: -e["median"])))["sample_titles"]
            if samples:
                lines += ["", "Sample sold titles (top category):"]
                lines += [f"- {t}" for t in samples[:3]]
            sk = m["skeleton"]
            if sk["top_parts"]:
                lines += ["", "Suggested entry skeleton:", "", "```python",
                          f'"{sk["key"]}": {{',
                          f'    "display": "{sk["display"]}", "make": "{sk["make"]}",',
                          f'    "year_range": ({sk["year_range"][0]}, {sk["year_range"][1]}),',
                          '    "top_parts": [']
                for p in sk["top_parts"]:
                    lines.append(
                        f'        {{"name": "{p["name"]}", "rarity": "{p["rarity"]}", '
                        f'"low": {p["low"]}, "high": {p["high"]}, "cost": 20}},  # {p["evidence"]}')
                lines += ["    ],", "},", "```"]
        if failed:
            lines.append(f"\n- No sold data for: {', '.join(failed)}")
        lines.append("")
    out_md.write_text("\n".join(lines))
    out_json.write_text(json.dumps({
        "date": today,
        "gaps": gaps,
        "mined": mined,
    }, indent=1))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top", type=int, default=15, help="groups to list in detail")
    ap.add_argument("--min-count", type=int, default=25, help="min vehicles for a group to rank")
    ap.add_argument("--out-md", type=Path, default=OUT_MD)
    ap.add_argument("--out-json", type=Path, default=OUT_JSON)
    # Accepted for older command lines (coverage-mine.yml passes them);
    # both are no-ops now that the page fetcher is gone.
    ap.add_argument("--no-fetch", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--categories", type=int, help=argparse.SUPPRESS)
    args = ap.parse_args()

    gaps = analyze_gaps(args.min_count)
    print(f"Thin-coverage groups (>= {args.min_count} vehicles): {len(gaps)}")

    mined = []
    for g in gaps[:args.top]:
        mined.append({"group": g, "evidence": {}, "skeleton": skeleton_for(g, {})})
        print(f"  {g['make']} {g['model']} ({g['year_band']}): {g['vehicle_count']:,} vehicles, "
              f"{g['gap_kind']}")

    write_outputs(gaps, mined, args.top, args.out_md, args.out_json)
    print(f"Wrote {args.out_md} and {args.out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
