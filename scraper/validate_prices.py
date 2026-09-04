#!/usr/bin/env python3
"""Quarterly price re-validation for UNOBTANIUM_DB resale ranges.

Ranks the highest-exposure parts in the live inventory (frequency x claimed
high), compares each displayed (calibrated) range against market evidence, and
regenerates scraper/price_validation_report.md. It NEVER edits prices — the
output is a review artifact for a human decision.

Evidence sources, in order of preference:
  1. Fresh eBay sold-listing prices — attempted politely, but eBay bot-blocks
     datacenter IPs (documented in the 2026-09 audit). Two consecutive
     failures disable the source for the rest of the run.
  2. The committed baseline (scraper/price_baseline.json) — machine-readable
     evidence from the most recent MANUAL audit. This is the workhorse: the
     quarterly run detects *drift* (DB values edited past reviewed evidence)
     and *new entrants* (parts that rose into the top-50 with no reviewed
     evidence -> UNVERIFIABLE, i.e. "needs a manual look").

Classification vs. an evidence range [obs_low, obs_high]:
  INFLATED     displayed low above the observed ceiling, or displayed high
               more than 1.5x the observed ceiling
  UNDERSTATED  displayed high below the observed floor
  ACCURATE     ranges overlap (includes deliberately conservative bands)
  UNVERIFIABLE no evidence available for this part

Usage:
  python scraper/validate_prices.py [--top 50] [--report PATH] [--summary PATH]
                                    [--no-fresh]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from datetime import date
from pathlib import Path

try:
    import requests
except ImportError:  # keep the script importable without deps for --help
    requests = None

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "docs" / "data" / "inventory_live.json"
BASELINE = ROOT / "scraper" / "price_baseline.json"
DEFAULT_REPORT = ROOT / "scraper" / "price_validation_report.md"

UA = {"User-Agent": "junkyard-hunter price validator (github.com/benvuolo/junkyard-hunter)"}
INFLATION_TOLERANCE = 1.5  # displayed high may sit up to 1.5x the observed ceiling


# ---------------------------------------------------------------- exposure --

def top_exposure_parts(top_n: int) -> list[dict]:
    """Top parts by (live-inventory frequency x displayed high).

    Part identity = (name, displayed low, displayed high): the same part name
    can carry different bands on different models. Each part is annotated with
    the models it appears on so baseline matching can disambiguate.
    """
    data = json.loads(INVENTORY.read_text())
    part_sets = data["partSets"]
    freq: Counter = Counter()          # set-index level
    models: dict[int, Counter] = {}
    for row in data["vehicles"]:
        si = row[8]
        if si is None or si < 0:
            continue
        freq[si] += 1
        models.setdefault(si, Counter())[f"{row[3]} {row[4]}".strip()] += 1

    groups: dict[tuple, dict] = {}
    for si, n in freq.items():
        for p in part_sets[si]:
            key = (p["name"], p["low"], p["high"])
            g = groups.setdefault(key, {
                "name": p["name"], "low": p["low"], "high": p["high"],
                "freq": 0, "models": Counter(),
            })
            g["freq"] += n
            g["models"] += models[si]

    parts = sorted(groups.values(), key=lambda g: g["freq"] * g["high"], reverse=True)
    return parts[:top_n]


# ---------------------------------------------------------------- baseline --

def load_baseline() -> dict:
    if not BASELINE.exists():
        return {"audit_date": None, "entries": []}
    return json.loads(BASELINE.read_text())


def _tokens(s: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", s.lower()) if len(t) > 2}


def _norm_name(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def match_baseline(part: dict, entries: list[dict]) -> dict | None:
    """Match a live part to a baseline entry. Exact name matches may be
    disambiguated by model tokens or nearest displayed range; fuzzy name-prefix
    matches (e.g. "Headlights (clear, non-hazed)" vs audited "Headlights
    (clear)") additionally REQUIRE a model-token overlap — evidence is never
    borrowed across both a different name and a different vehicle."""
    model_toks = _tokens(" ".join(part["models"]))
    pn = _norm_name(part["name"])
    exact = [e for e in entries if e["part"].lower() == part["name"].lower()]
    if not exact:
        name_toks = _tokens(part["name"])
        def name_close(e):
            en = _norm_name(e["part"])
            if en.startswith(pn) or pn.startswith(en):
                return True
            et = _tokens(e["part"])
            if not et or not name_toks:
                return False
            return len(et & name_toks) / min(len(et), len(name_toks)) >= 0.75
        fuzzy = [e for e in entries if name_close(e) and _tokens(e["vehicle"]) & model_toks]
        if not fuzzy:
            return None
        exact = fuzzy
    if len(exact) == 1:
        return exact[0]
    by_model = [e for e in exact if _tokens(e["vehicle"]) & model_toks]
    if len(by_model) == 1:
        return by_model[0]
    pool = by_model or exact
    def dist(e):
        if e.get("displayed_low") is None:
            return 1e9
        return abs(e["displayed_low"] - part["low"]) + abs(e["displayed_high"] - part["high"])
    return min(pool, key=dist)


# ---------------------------------------------------------- fresh evidence --

class FreshSource:
    """Best-effort eBay sold-listing fetch. Backs off permanently after two
    consecutive failures — a blocked or down source must not crash or stall
    the run (affected parts fall back to baseline / UNVERIFIABLE)."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled and requests is not None
        self.failures = 0

    def prices(self, query: str) -> list[int]:
        if not self.enabled or self.failures >= 2:
            return []
        try:
            r = requests.get(
                "https://www.ebay.com/sch/i.html",
                params={"_nkw": query, "LH_Sold": "1", "LH_Complete": "1"},
                headers=UA, timeout=20,
            )
            body = r.text
            if r.status_code != 200 or "captcha" in body.lower():
                self.failures += 1
                return []
            self.failures = 0
            time.sleep(1.0)  # be polite
            vals = [int(v.replace(",", "").split(".")[0])
                    for v in re.findall(r'\$([\d,]+\.?\d*)', body)]
            return [v for v in vals if 10 <= v <= 20000]
        except Exception:
            self.failures += 1
            return []


# ----------------------------------------------------------- classification --

def classify(low: int, high: int, obs_low: int, obs_high: int) -> str:
    if low > obs_high or high > obs_high * INFLATION_TOLERANCE:
        return "INFLATED"
    if high < obs_low:
        return "UNDERSTATED"
    return "ACCURATE"


def validate(top_n: int, use_fresh: bool) -> dict:
    parts = top_exposure_parts(top_n)
    baseline = load_baseline()
    fresh = FreshSource(enabled=use_fresh)
    fresh_used = 0

    results = []
    for part in parts:
        top_models = [m for m, _ in part["models"].most_common(2)]
        evidence, source, note, b = None, None, "", None

        prices = fresh.prices(f"{top_models[0]} {part['name']} OEM used" if top_models else part["name"])
        if len(prices) >= 5:
            prices.sort()
            # trim outliers: middle 80%
            k = max(1, len(prices) // 10)
            body = prices[k:-k] or prices
            evidence = (body[0], body[-1])
            source = "fresh (eBay sold)"
            fresh_used += 1
        else:
            b = match_baseline(part, baseline["entries"])
            if b and b.get("obs_low") is not None:
                evidence = (b["obs_low"], b["obs_high"])
                source = f"audit {baseline['audit_date']}"
                note = b.get("note", "")

        if evidence:
            verdict = classify(part["low"], part["high"], *evidence)
            if source and source.startswith("audit") and b:
                note = b.get("note", "")
        else:
            verdict, note = "UNVERIFIABLE", "no reviewed evidence — new high-exposure entrant, needs a manual look"
        results.append({
            "name": part["name"],
            "models": ", ".join(top_models),
            "freq_bucket": max(500, round(part["freq"] / 500) * 500),
            "low": part["low"], "high": part["high"],
            "evidence": evidence, "source": source,
            "verdict": verdict,
            "note": note,
        })

    counts = Counter(r["verdict"] for r in results)
    return {
        "results": results,
        "counts": dict(counts),
        "baseline_date": baseline["audit_date"],
        "fresh_used": fresh_used,
        "fresh_blocked": fresh.enabled and fresh.failures >= 2,
    }


# ------------------------------------------------------------------ report --

def write_report(v: dict, path: Path) -> None:
    c = v["counts"]
    fresh_note = ("blocked from this network — expected on CI" if v["fresh_blocked"]
                  else f"{v['fresh_used']} part(s) used fresh data")
    lines = [
        "# Price Validation Report — UNOBTANIUM_DB vs. market evidence",
        "",
        f"**Date:** {date.today().isoformat()}",
        "**Generated by:** `scraper/validate_prices.py` (quarterly automated re-validation)",
        f"**Scope:** top {len(v['results'])} parts by live-inventory exposure (frequency × displayed high).",
        f"**Evidence baseline:** manual audit of {v['baseline_date']} "
        f"(`scraper/price_baseline.json`); fresh eBay sold prices attempted per run ({fresh_note}).",
        "",
        "## Verdict counts",
        "",
        "| Classification | Count |",
        "|---|---|",
    ]
    for k in ("ACCURATE", "UNDERSTATED", "INFLATED", "UNVERIFIABLE"):
        lines.append(f"| {k} | {c.get(k, 0)} |")
    lines += [
        "",
        "**Rules:** displayed (calibrated) range vs. observed evidence range. "
        "INFLATED = displayed low above the observed ceiling, or displayed high > "
        f"{INFLATION_TOLERANCE}x it. UNDERSTATED = displayed high below the observed floor. "
        "UNVERIFIABLE = a part rose into the top exposure list with no reviewed evidence.",
        "",
        "Prices are never edited automatically. INFLATED and UNVERIFIABLE rows need a "
        "human decision; when corrections are accepted, bump `PRICES_LAST_REVIEWED` in "
        "`scraper/junkyard_scraper.py` and refresh `scraper/price_baseline.json`.",
        "",
        "## Results (alphabetical — stable ordering for diffs)",
        "",
        "| Part | Models | ~Freq | Displayed | Evidence | Source | Verdict |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in sorted(v["results"], key=lambda r: (r["name"].lower(), r["models"].lower())):
        ev = f"${r['evidence'][0]:,}–{r['evidence'][1]:,}" if r["evidence"] else "—"
        flag = f" **{r['verdict']}**" if r["verdict"] in ("INFLATED", "UNVERIFIABLE") else f" {r['verdict']}"
        lines.append(
            f"| {r['name']} | {r['models']} | {r['freq_bucket']:,} | "
            f"${r['low']:,}–{r['high']:,} | {ev} | {r['source'] or '—'} |{flag} |")
    notes = [r for r in sorted(v["results"], key=lambda r: r["name"].lower())
             if r["verdict"] in ("INFLATED", "UNVERIFIABLE") and r["note"]]
    if notes:
        lines += ["", "## Flagged rows — detail", ""]
        for r in notes:
            lines.append(f"- **{r['name']}** ({r['models']}): {r['verdict']} — {r['note']}")
    lines.append("")
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--top", type=int, default=50)
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    ap.add_argument("--summary", type=Path, default=None)
    ap.add_argument("--no-fresh", action="store_true", help="skip fresh-source attempts")
    args = ap.parse_args()

    v = validate(args.top, use_fresh=not args.no_fresh)
    write_report(v, args.report)
    c = v["counts"]
    print(f"Validated top {len(v['results'])} parts: "
          + ", ".join(f"{k.lower()} {c.get(k, 0)}" for k in ("ACCURATE", "UNDERSTATED", "INFLATED", "UNVERIFIABLE")))
    print(f"Report written to {args.report}")
    if args.summary:
        args.summary.write_text(json.dumps({
            "total": len(v["results"]),
            "accurate": c.get("ACCURATE", 0),
            "understated": c.get("UNDERSTATED", 0),
            "inflated": c.get("INFLATED", 0),
            "unverifiable": c.get("UNVERIFIABLE", 0),
            "fresh_used": v["fresh_used"],
            "baseline_date": v["baseline_date"],
        }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
