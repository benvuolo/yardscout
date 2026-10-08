#!/usr/bin/env python3
"""Autonomous parts-KB researcher — turns coverage gaps into overlay entries.

Runs weekly in CI (.github/workflows/parts-research.yml). The monthly coverage
miner (mine_coverage_gaps.py) ranks vehicle groups with zero/generic-only part
coverage into scraper/coverage_candidates.json; this script takes the top
unresearched groups, asks an LLM for genuinely flip-worthy parts for each
(conservative pricing, factory options flagged), validates the answer hard,
and appends the survivors to scraper/parts_overlay.json — which
junkyard_scraper.py merges into UNOBTANIUM_DB on every scan.

Guardrails (the LLM proposes, this script disposes):
  - strict JSON schema, one retry on parse failure
  - price sanity: 15 <= low < high <= 1500, pull cost < low, high <= 6x low
  - confidence gate: entries below 0.6 are dropped
  - name sanity + dedupe against the group's already-matched generic parts
  - eBay sold-median clamp when the miner captured evidence for the category
  - per-run cap (default 4 groups) so a bad run has a small blast radius
  - every part is tagged source:"auto-research" + the run date for audit

Keys: ANTHROPIC_API_KEY (preferred) or OPENAI_API_KEY. No key -> exit 0 ("not
configured" is a valid state, same convention as the scan's optional pushes).

Usage:
  python scraper/research_parts.py                 # research up to 4 groups
  python scraper/research_parts.py --groups 2
  python scraper/research_parts.py --dry-run       # print prompt + plan only
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = ROOT / "scraper" / "coverage_candidates.json"
OVERLAY = ROOT / "scraper" / "parts_overlay.json"
LOG = ROOT / "scraper" / "parts_research_log.md"

ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1")

PROMPT = """You are an expert on US self-service junkyard part flipping (eBay,
Facebook Marketplace, forums). For the vehicle group below, list the parts a
part-flipper should pull because they resell reliably for meaningful money.

Vehicle group: {year_band} {make} {model}
Parts already tracked for this group (do NOT repeat): {already}

Rules:
- 0 to 6 parts. An empty list is a GOOD answer for appliance cars with no
  resale scene — do not invent demand.
- Only parts with a real, repeatable resale market for THIS generation
  (think: what actually sells, not what exists).
- Conservative USED resale prices in USD for working, decent-condition parts.
  "low" = typical quick-sale price, "high" = patient-sale price. Never price
  above what a new aftermarket equivalent costs.
- "cost" = typical self-service yard pull price for the part category.
- Factory OPTIONS (packages, upgraded audio, special seats, tow mirrors,
  sunroof parts, limited-trim-only cosmetics) must have "option": true.
- Parts exclusive to one trim: add "trim": ["<trim substring>"].
- Parts only fitting a sub-range of years: add "yr_min"/"yr_max".
- "confidence": 0-1, your honest certainty this part flips at these prices.
- "why": one short sentence of evidence (what market, who buys it).

Respond with ONLY a JSON array, no markdown fences, no commentary:
[{{"name": "...", "low": 0, "high": 0, "cost": 0, "rarity": "Rare|Epic|Legendary",
   "option": false, "trim": [], "yr_min": 0, "yr_max": 0,
   "confidence": 0.0, "why": "..."}}]
Omit trim/yr_min/yr_max keys when not applicable."""


def _call_llm(prompt: str) -> str:
    """One LLM call via whichever API key exists. Returns raw text."""
    akey, okey = os.environ.get("ANTHROPIC_API_KEY"), os.environ.get("OPENAI_API_KEY")
    if akey:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            method="POST",
            headers={"content-type": "application/json", "x-api-key": akey,
                     "anthropic-version": "2023-06-01"},
            data=json.dumps({"model": ANTHROPIC_MODEL, "max_tokens": 2000,
                             "messages": [{"role": "user", "content": prompt}]}).encode())
        with urllib.request.urlopen(req, timeout=120) as r:
            out = json.load(r)
        return "".join(b.get("text", "") for b in out.get("content", []))
    if okey:
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            method="POST",
            headers={"content-type": "application/json",
                     "authorization": f"Bearer {okey}"},
            data=json.dumps({"model": OPENAI_MODEL, "max_tokens": 2000,
                             "messages": [{"role": "user", "content": prompt}]}).encode())
        with urllib.request.urlopen(req, timeout=120) as r:
            out = json.load(r)
        return out["choices"][0]["message"]["content"]
    raise RuntimeError("no API key")


def _parse_parts(raw: str) -> list[dict]:
    """Extract the JSON array from an LLM reply (tolerates stray prose)."""
    m = re.search(r"\[.*\]", raw, re.S)
    if not m:
        raise ValueError(f"no JSON array in reply: {raw[:200]!r}")
    parsed = json.loads(m.group(0))
    if not isinstance(parsed, list):
        raise ValueError("reply is not a list")
    return parsed


def _evidence_median(mined: list, group: dict, part_name: str) -> int | None:
    """Sold-price median from the miner's eBay evidence, when it got any."""
    for row in mined or []:
        g = row.get("group", {})
        if (g.get("make"), g.get("model"), g.get("year_band")) != (
                group.get("make"), group.get("model"), group.get("year_band")):
            continue
        for cat, ev in (row.get("evidence") or {}).items():
            if ev.get("status") == "ok" and ev.get("median") and cat.lower() in part_name.lower():
                return int(ev["median"])
    return None


def _validate(parts: list[dict], group: dict, mined: list, today: str) -> tuple[list[dict], list[str]]:
    """Hard gate on LLM output. Returns (accepted, rejection_notes)."""
    already = {p.lower() for p in group.get("matched_parts", [])}
    yb_lo, yb_hi = (int(x) for x in group["year_band"].split("-"))
    out, notes = [], []
    for p in parts[:6]:
        name = str(p.get("name", "")).strip()
        why = str(p.get("why", "")).strip()
        try:
            low, high = int(p["low"]), int(p["high"])
            cost = int(p.get("cost", 10))
            conf = float(p.get("confidence", 0))
        except (KeyError, TypeError, ValueError):
            notes.append(f"reject (bad fields): {name or p!r}")
            continue
        if not (2 <= len(name) <= 60) or name.lower() in already:
            notes.append(f"reject (name/dupe): {name}")
            continue
        if conf < 0.6:
            notes.append(f"reject (confidence {conf:.2f}): {name}")
            continue
        if not (15 <= low < high <= 1500 and high <= 6 * low and 0 <= cost < low):
            notes.append(f"reject (prices {low}-{high} cost {cost}): {name}")
            continue
        med = _evidence_median(mined, group, name)
        if med and high > int(med * 1.25):
            high = max(low + 1, int(med * 1.25))
            notes.append(f"clamped to eBay median ${med}: {name}")
        q = {"name": name, "rarity": p.get("rarity", "Rare"),
             "low": low, "high": high, "cost": cost,
             "source": "auto-research", "added": today, "why": why}
        if q["rarity"] not in ("Rare", "Epic", "Legendary"):
            q["rarity"] = "Rare"
        if p.get("option"):
            q["option"] = True
        trim = [str(t).strip() for t in (p.get("trim") or []) if str(t).strip()]
        if trim:
            q["trim"] = trim
        # Year gates: intersect whatever the LLM gave with the group band.
        q["yr_min"] = max(int(p.get("yr_min") or yb_lo), yb_lo)
        q["yr_max"] = min(int(p.get("yr_max") or yb_hi), yb_hi)
        if q["yr_min"] > q["yr_max"]:
            notes.append(f"reject (year gate empty): {name}")
            continue
        out.append(q)
    return out, notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--groups", type=int, default=4, help="max groups per run")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")):
        print("No ANTHROPIC_API_KEY / OPENAI_API_KEY — research not configured, skipping.")
        return 0
    if not CANDIDATES.exists():
        print("No coverage_candidates.json — run mine_coverage_gaps.py first. Skipping.")
        return 0

    cand = json.loads(CANDIDATES.read_text())
    overlay = json.loads(OVERLAY.read_text()) if OVERLAY.exists() else {"researched": {}, "entries": []}
    overlay.setdefault("researched", {})
    overlay.setdefault("entries", [])
    today = date.today().isoformat()

    todo = []
    for g in cand.get("gaps", []):
        gid = f"{g['make']}|{g['model']}|{g['year_band']}"
        if gid not in overlay["researched"]:
            todo.append((gid, g))
        if len(todo) >= args.groups:
            break
    if not todo:
        print("All current coverage gaps already researched — nothing to do.")
        return 0

    log_lines = [f"\n## Run {today}\n"]
    for gid, g in todo:
        prompt = PROMPT.format(year_band=g["year_band"], make=g["make"], model=g["model"],
                               already=", ".join(g.get("matched_parts", [])) or "none")
        if args.dry_run:
            print(f"--- would research: {gid}\n{prompt}\n")
            continue
        try:
            raw = _call_llm(prompt)
            try:
                parts = _parse_parts(raw)
            except ValueError:
                parts = _parse_parts(_call_llm(prompt))  # one retry
        except Exception as exc:
            print(f"[{gid}] LLM call failed: {exc} — leaving group for next run.")
            log_lines.append(f"- **{gid}**: LLM call failed ({exc}) — will retry next run\n")
            continue

        accepted, notes = _validate(parts, g, cand.get("mined", []), today)
        overlay["researched"][gid] = today  # researched even when 0 accepted: empty is an answer
        if accepted:
            overlay["entries"].append({
                "make": g["make"], "match": [g["model"].lower()],
                "display": f"{g['make']} {g['model']}", "parts": accepted})
        print(f"[{gid}] accepted {len(accepted)}/{len(parts)} parts"
              + (f" ({'; '.join(notes)})" if notes else ""))
        log_lines.append(f"- **{gid}**: accepted {len(accepted)}/{len(parts)}"
                         + "".join(f"\n  - {p['name']} ${p['low']}-{p['high']} — {p['why']}" for p in accepted)
                         + "".join(f"\n  - _{n}_" for n in notes) + "\n")

    if args.dry_run:
        return 0
    OVERLAY.write_text(json.dumps(overlay, indent=2) + "\n")
    if not LOG.exists():
        LOG.write_text("# Parts auto-research log\n\nWeekly LLM research runs "
                       "(.github/workflows/parts-research.yml). Every accepted part "
                       "is tagged in scraper/parts_overlay.json with source+date; "
                       "prune bad entries there.\n")
    LOG.write_text(LOG.read_text() + "".join(log_lines))
    print(f"Overlay now has {len(overlay['entries'])} entries; "
          f"{len(overlay['researched'])} groups researched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
