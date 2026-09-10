#!/usr/bin/env python3
"""Self-expanding coverage miner — finds UNOBTANIUM_DB blind spots, gathers
sold-price evidence, and PROPOSES entries. Zero LLM tokens, fully deterministic.

Pipeline (monthly via .github/workflows/coverage-mine.yml, or run by hand):

  1. Inventory gap analysis (always works, offline): reads the live inventory
     (docs/data/inventory_live.json) and ranks (make, model, year-band) groups
     by vehicle count where the match rate is zero OR the matched parts are
     only generic commuter parts (headlights/mirrors/tail lights tier). Known
     enthusiast platforms (static pattern list below) present in inventory
     with thin part sets are flagged and boosted.
  2. Evidence gathering (best-effort): for the top N groups, politely fetches
     eBay sold/completed-listing search pages per part-category search term
     (~1 request / 2s, UA set, responses cached to scraper/.cache/ebay/).
     Parses sold prices -> median/count per category plus sample titles.
     eBay's official sold-data API (Marketplace Insights) is gated, so this is
     public-page HTML parsing: if the markup changes or the network blocks us,
     the run FAILS SOFT — the report says which groups got no data and the
     inventory-side analysis still ships.
  3. Output: scraper/coverage_candidates.md (human review report with entry
     skeletons) + scraper/coverage_candidates.json (machine-readable).

IMPORTANT: this script proposes, it never edits UNOBTANIUM_DB. Curation stays
a human/agent review step.

Usage:
  python scraper/mine_coverage_gaps.py                 # top 15 groups, fetch
  python scraper/mine_coverage_gaps.py --top 10 --categories 5
  python scraper/mine_coverage_gaps.py --no-fetch      # inventory analysis only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "docs" / "data" / "inventory_live.json"
CACHE_DIR = ROOT / "scraper" / ".cache" / "ebay"
OUT_MD = ROOT / "scraper" / "coverage_candidates.md"
OUT_JSON = ROOT / "scraper" / "coverage_candidates.json"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
FETCH_DELAY_SEC = 2.0
CACHE_MAX_AGE_DAYS = 20  # a monthly schedule always refetches; reruns are free

# Parts whose presence alone doesn't count as real coverage — every commuter
# car gets these. A group whose matched parts are ALL from this tier is still
# a coverage gap.
GENERIC_PART_TOKENS = (
    "headlight", "tail light", "taillight", "side mirror", "window regulator",
    "alternator", "wiper", "cargo cover", "door handle", "power window master",
    "spare tire cover", "corner/marker",
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

# Fixed part-category search terms tried per group (order = priority; a run's
# --categories cap trims from the end). Deterministic — no model-specific
# cleverness, the search term is "<year-band mid> <make> <model> <term>".
PART_CATEGORY_TERMS = [
    "seats",
    "tail lights",
    "headlights",
    "grille",
    "gauge cluster",
    "front bumper",
    "doors",
    "engine",
    "transmission",
    "center console",
    "steering wheel",
    "wheels oem",
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


# ------------------------------------------------------ eBay sold evidence --

class SoldFetcher:
    """Polite, cached eBay sold-listings page fetcher. Fails soft: after 3
    consecutive failures the source is disabled for the rest of the run."""

    def __init__(self, enabled: bool = True, cache_days: int = CACHE_MAX_AGE_DAYS):
        self.enabled = enabled and requests is not None
        self.failures = 0
        self.cache_days = cache_days
        self.last_fetch = 0.0
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, query: str) -> Path:
        return CACHE_DIR / (hashlib.sha1(query.encode()).hexdigest()[:16] + ".html")

    def fetch(self, query: str) -> str | None:
        cache = self._cache_path(query)
        if cache.exists() and (time.time() - cache.stat().st_mtime) < self.cache_days * 86400:
            return cache.read_text(errors="replace")
        if not self.enabled or self.failures >= 3:
            return None
        wait = FETCH_DELAY_SEC - (time.time() - self.last_fetch)
        if wait > 0:
            time.sleep(wait)
        try:
            r = requests.get(
                "https://www.ebay.com/sch/i.html",
                params={"_nkw": query, "LH_Sold": "1", "LH_Complete": "1", "_ipg": "60"},
                headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"},
                timeout=25,
            )
            self.last_fetch = time.time()
            body = r.text
            if r.status_code != 200 or "captcha" in body.lower() or "Pardon Our Interruption" in body:
                self.failures += 1
                return None
            self.failures = 0
            cache.write_text(body)
            return body
        except Exception:
            self.failures += 1
            return None


ITEM_RE = re.compile(
    r'<(?:li|div)[^>]*class="[^"]*s-(?:item|card)[^"]*"[^>]*>(.*?)</(?:li|div)>',
    re.S)
TITLE_RE = re.compile(
    r'class="[^"]*s-(?:item|card)__title[^"]*"[^>]*>(?:<[^>]+>)*([^<]{10,200})')
PRICE_RE = re.compile(
    r'class="[^"]*s-(?:item|card)__price[^"]*"[^>]*>(?:<[^>]+>)*\$([\d,]+)(?:\.\d\d)?')


def parse_sold(body: str) -> list[tuple[str, int]]:
    """(title, sold price) pairs. Tries BeautifulSoup when available, falls
    back to regex over item blocks. Empty result = markup changed/blocked."""
    results: list[tuple[str, int]] = []
    try:
        from bs4 import BeautifulSoup  # optional dep, present in CI
        soup = BeautifulSoup(body, "html.parser")
        for item in soup.select("li.s-item, li.s-card, div.s-item"):
            t = item.select_one(".s-item__title, .s-card__title")
            p = item.select_one(".s-item__price, .s-card__price")
            if not t or not p:
                continue
            m = re.search(r"\$([\d,]+)", p.get_text())
            if not m:
                continue
            title = t.get_text(" ", strip=True)
            if title.lower().startswith("shop on ebay"):
                continue  # eBay's placeholder first tile
            results.append((title, int(m.group(1).replace(",", ""))))
    except ImportError:
        for block in ITEM_RE.findall(body):
            tm, pm = TITLE_RE.search(block), PRICE_RE.search(block)
            if tm and pm:
                results.append((tm.group(1).strip(), int(pm.group(1).replace(",", ""))))
    return [(t, v) for t, v in results if 10 <= v <= 20000]


def gather_evidence(group: dict, fetcher: SoldFetcher, categories: list[str]) -> dict:
    b_lo, b_hi = band_years(group["year_band"])
    mid_year = (b_lo + b_hi) // 2 if b_lo else ""
    cats = {}
    for term in categories:
        query = f"{mid_year} {group['make']} {group['model']} {term}".strip()
        body = fetcher.fetch(query)
        if body is None:
            cats[term] = {"status": "fetch-failed", "query": query}
            continue
        sold = parse_sold(body)
        if not sold:
            cats[term] = {"status": "no-parse", "query": query}
            continue
        prices = sorted(v for _, v in sold)
        cats[term] = {
            "status": "ok",
            "query": query,
            "count": len(prices),
            "median": int(statistics.median(prices)),
            "p25": prices[len(prices) // 4],
            "p75": prices[(3 * len(prices)) // 4],
            "sample_titles": [t for t, _ in sold[:4]],
        }
    return cats


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
                  fetch_enabled: bool, out_md: Path, out_json: Path) -> None:
    today = date.today().isoformat()
    fetched_ok = sum(1 for m in mined
                     if any(ev.get("status") == "ok" for ev in m["evidence"].values()))
    lines = [
        "# Coverage Candidates — automated gap mining",
        "",
        f"**Date:** {today}",
        "**Generated by:** `scraper/mine_coverage_gaps.py` (deterministic, zero LLM tokens).",
        f"**Inventory groups analyzed:** {len(gaps)} thin-coverage (make, model, year-band) "
        f"groups; evidence gathered for the top {len(mined)}.",
        "",
        "**This report PROPOSES entries — nothing edits `UNOBTANIUM_DB` automatically.** "
        "Review the evidence, spot-check the sample sold titles, then hand-curate the "
        "skeletons you accept into `scraper/junkyard_scraper.py` (with the usual price "
        "audit discipline: bands calibrated to sold prices, ceiling rule vs. new parts).",
        "",
    ]
    if not fetch_enabled:
        lines += ["> eBay fetching was disabled for this run (`--no-fetch` or requests "
                  "missing) — inventory-side gap ranking only.", ""]
    elif fetched_ok == 0:
        lines += ["> **eBay sold-data collection got no usable data this run** (bot-block "
                  "or markup change — see per-category statuses). The gap ranking below "
                  "still stands; re-run locally or fix the parser.", ""]
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
    lines += ["", "## Mined groups — evidence + entry skeletons", ""]
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
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--top", type=int, default=15, help="groups to gather evidence for")
    ap.add_argument("--categories", type=int, default=8, help="part-category searches per group")
    ap.add_argument("--min-count", type=int, default=25, help="min vehicles for a group to rank")
    ap.add_argument("--no-fetch", action="store_true", help="skip eBay fetches entirely")
    ap.add_argument("--out-md", type=Path, default=OUT_MD)
    ap.add_argument("--out-json", type=Path, default=OUT_JSON)
    ap.add_argument("--cache-days", type=int, default=CACHE_MAX_AGE_DAYS)
    args = ap.parse_args()

    gaps = analyze_gaps(args.min_count)
    print(f"Thin-coverage groups (>= {args.min_count} vehicles): {len(gaps)}")

    fetcher = SoldFetcher(enabled=not args.no_fetch, cache_days=args.cache_days)
    categories = PART_CATEGORY_TERMS[:max(1, args.categories)]
    mined = []
    for g in gaps[:args.top]:
        evidence = gather_evidence(g, fetcher, categories) if not args.no_fetch else {}
        mined.append({"group": g, "evidence": evidence,
                      "skeleton": skeleton_for(g, evidence)})
        ok = sum(1 for ev in evidence.values() if ev.get("status") == "ok")
        print(f"  {g['make']} {g['model']} ({g['year_band']}): {g['vehicle_count']:,} vehicles, "
              f"{g['gap_kind']}, evidence {ok}/{len(categories) if not args.no_fetch else 0} categories")

    write_outputs(gaps, mined, args.top, not args.no_fetch, args.out_md, args.out_json)
    print(f"Wrote {args.out_md} and {args.out_json}")
    if not args.no_fetch and fetcher.failures >= 3:
        print("WARNING: eBay fetches disabled after repeated failures — evidence is partial.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
