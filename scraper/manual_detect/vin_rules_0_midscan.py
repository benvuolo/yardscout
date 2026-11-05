#!/usr/bin/env python3
"""Verification aid for vin_rules_0 (Honda/Acura): scan American Honda's Part 565
VIN filings in NHTSA's Manufacturer Information Database (MID) for every
(model code, transmission) row they print, and test the character-7 rule on
each row:

  * digit era (filings for MY1987-2009): character 7 odd = manual, even = automatic
  * letter era (MY2010 on): A/C/E/G = manual, B/D/F/H = automatic (CVT, DCT included)

Filings for MY1984-1986 (character 6 = transmission) are skipped here; those
few tables were checked by hand (see vin_rules_0.json, rule verified blocks).

Input: directories of per-filing text files named
       <YYYY-MM-DD>_<doc no>_<first 8 hex of the MID file id>.txt or
       <YYYY-MM-DD>_<first 8 hex>.txt, made with `pdftotext -layout` when the
       PDF has a text layer and with tesseract otherwise (most filings before
       2009 are scans), plus the MID listing JSON for American Honda (to turn
       the file id into its public URL). The PDFs and text stay outside the
       repo; this script records only what each filing says.
Output: scraper/manual_detect/vin_rules_0_mid_scan.json

Rows the parser reads but that disagree with the rule are listed for a human
to read in the filing image. MANUAL_REVIEW below records what that reading
found (OCR misreads, parser mistakes, or a real exception).

Run: python3 -I scraper/manual_detect/vin_rules_0_midscan.py LISTING.json DIR [DIR ...]
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "vin_rules_0_mid_scan.json"
MID = "https://vpic.nhtsa.dot.gov/mid/home/displayfile/"

WMI = {"JHM", "JHL", "JH1", "1HG", "5J6", "5J7", "5KB", "5FN", "5FP", "19X", "7FA", "2HG", "2HK", "2HJ",
       "3HG", "3CZ", "SHH", "SHS", "JH4", "19U", "5J8", "5J0", "5KC", "5FR", "5FS", "19V", "2HH", "2HN", "2HU"}

# (file stem, model code) -> finding after reading the filing image.
MANUAL_REVIEW: dict[tuple[str, str], str] = {}

TRANS = [
    (re.compile(r"\b(?:[4-9]|10)\s?-?\s?(?:SPEED\s+)?(?:M/?T|MT|M)\b(?!\+)"), "manual"),
    (re.compile(r"\b[4-9]\s?M\+SL\b"), "manual"),
    (re.compile(r"\bS\s?M/?T\b|\bSM\b"), "manual"),        # OCR of 5MT / 5M
    (re.compile(r"\bM\s?[4-6]\b|\bMS\b"), "manual"),        # "M5" style; OCR "MS"
    (re.compile(r"\b(?:[2-9]|10)\s?-?\s?(?:SPEED\s+)?(?:A/?T|AT|A)\b"), "automatic"),
    (re.compile(r"\bL\s?[34]\b"), "automatic"),             # "L4" style
    (re.compile(r"\b(?:E-?)?CVT\b|\b\d*DCT\b"), "automatic"),
]
CODE_AT_START = re.compile(r"^\s*(?:ROT270\s+)?(?:\d{1,3}[.\s|]+)?\|?\s*([A-Z]{2}[0-9A-Z]{3})\b")
VIN_EXAMPLE = re.compile(r"([0-9A-Z]{3})([A-Z]{2}[0-9A-Z]{3})[*'\"°]")


def fix(code: str) -> str:
    """Characters 6-8 of a model code: undo the usual OCR letter-for-digit slips."""
    head, tail = code[:3], code[3:]
    tail = tail.replace("O", "0").replace("S", "5").replace("I", "1").replace("L", "1").replace("Z", "2")
    return head[:2] + head[2].replace("O", "0").replace("S", "5").replace("I", "1") + tail


def trans_on(line: str) -> str | None:
    hits = {c for rx, c in TRANS if rx.search(line)}
    return hits.pop() if len(hits) == 1 else None


def rule_claim(code: str) -> str | None:
    c7 = code[3]
    if c7.isdigit():
        return "manual" if c7 in "1357" else ("automatic" if c7 in "2468" else None)
    return "manual" if c7 in "ACEG" else ("automatic" if c7 in "BDFH" else None)


def main() -> int:
    listing = json.loads(Path(sys.argv[1]).read_text())
    by8 = {r[-1][:8]: r for r in listing}
    filings = []
    totals = Counter()
    seen_ids: set[str] = set()
    for d in sys.argv[2:]:
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".txt") or fn.endswith(".layer.txt"):
                continue
            stem = fn[:-4]
            id8 = stem.split("_")[-1][:8]
            meta = by8.get(id8)
            if not meta or id8 in seen_ids:
                continue
            seen_ids.add(id8)
            fy = int(stem[:4])
            if fy <= 1985:          # MY1984-1986 layout, checked by hand
                continue
            rows = {}
            for line in open(os.path.join(d, fn), errors="replace"):
                u = line.upper()
                t = trans_on(u)
                if not t:
                    continue
                codes = [fix(m.group(2)) for m in VIN_EXAMPLE.finditer(u.replace(" ", "")) if m.group(1) in WMI]
                m = CODE_AT_START.match(u)
                if m and m.group(1) not in ("HONDA", "ACURA", "CIVIC", "OASIS"):
                    codes.append(fix(m.group(1)))
                for code in codes:
                    # characters 4-5 letters, 6 a digit, 7 the body/transmission
                    # character, 8 a digit (grade) in every Honda/Acura table
                    if not re.fullmatch(r"[A-Z]{2}[0-9][0-9A-H][0-9]", code):
                        continue
                    # submissions up to 2008 are digit-era model years, from 2010 letter-era;
                    # a letter in a 2008 table is an OCR misread of a digit (6 -> E ...)
                    if (fy <= 2008 and not code[3].isdigit()) or (fy >= 2010 and code[3].isdigit()):
                        continue
                    claim = rule_claim(code)
                    if claim is None:
                        continue
                    k = (code, t)
                    if k not in rows:
                        rows[k] = {"code": code, "filing_says": t, "rule_says": claim,
                                   "agree": claim == t, "line": line.strip()[:120]}
            if not rows:
                continue
            rs = list(rows.values())
            for r in rs:
                rev = MANUAL_REVIEW.get((stem, r["code"]))
                if rev:
                    r["manual_review"] = rev
                totals["rows"] += 1
                totals["agree" if r["agree"] else ("mismatch_reviewed" if rev else "MISMATCH")] += 1
                totals[f"{'letter' if r['code'][3].isalpha() else 'digit'}_{r['rule_says']}_{'agree' if r['agree'] else 'mismatch'}"] += 1
            filings.append({
                "file": stem, "date": meta[1], "doc": meta[0], "url": MID + meta[-1],
                "codes": len(rs), "manual_codes": sum(r["filing_says"] == "manual" for r in rs),
                "mismatches": [r for r in rs if not r["agree"]],
                "rows": [{k: r[k] for k in ("code", "filing_says")} for r in rs],
            })
    per_year = defaultdict(lambda: Counter())
    for f in filings:
        per_year[f["date"].split("/")[-1]]["filings"] += 1
        per_year[f["date"].split("/")[-1]]["codes"] += f["codes"]
    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "generator": "scraper/manual_detect/vin_rules_0_midscan.py",
        "what": ("Every model-code row (MY1987 on) the parser could read in American Honda's MID filings, with the "
                 "transmission the filing prints for it and what vin_rules_0's character-7 rule says. Filing date "
                 "year is the submission year (filings go in ~6-18 months before the model year)."),
        "totals": dict(totals),
        "per_submission_year": {y: dict(c) for y, c in sorted(per_year.items())},
        "filings": filings,
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({"totals": out["totals"], "per_submission_year": out["per_submission_year"]}, indent=1))
    for f in filings:
        for r in f["mismatches"]:
            print("MISMATCH", f["file"], r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
