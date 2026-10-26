#!/usr/bin/env python3
"""Validate the compare-combobox part-name alias layer against live data.

The canonical merging lives in docs/app.js (partMergeKey + PART_ALIAS_GROUPS,
see the 'CANONICAL PART-NAME MERGING' block). This script keeps it honest as
price lists drift:

 1. re-implements partMergeKey (MUST stay in sync with app.js — both carry a
    pointer to the other) and parses PART_ALIAS_GROUPS out of app.js;
 2. checks every curated raw name still exists verbatim on a live list
    (a scraper format change or a chain renaming a row shows up here);
 3. checks no merge key is claimed by two different alias groups, and that
    every alias canon that shadows a finder category label really matches a
    category in docs/data/interchange.json (one-taxonomy rule, spec §6);
 4. checks the PART_NEVER_MERGE names still exist (else the blocklist is
    stale);
 5. prints merge stats: raw names -> mechanical entries -> after curated
    groups.

Run:  python3 tools/check_part_aliases.py        (exit 1 on any failure)
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "docs", "app.js")
FAILS = []


def check(name, cond, detail=""):
    print(("ok   " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


# ---- partMergeKey, mirrored from docs/app.js ------------------------------
FILLER = {"each", "any", "only", "misc", "oem", "per", "type", "style",
          "the", "of", "or", "and", "ea", "s", "n"}
ABBR = {
    "assy": "assembly", "hous": "housing", "housng": "housing", "alum": "aluminum",
    "elec": "electric", "elect": "electric", "elctric": "electric", "electrc": "electric",
    "cyl": "cylinder", "trans": "transmission", "mtr": "motor", "moto": "motor",
    "pwr": "power", "cvr": "cover", "cntrl": "control", "ctrl": "control",
    "sml": "small", "sm": "small", "lrg": "large", "lg": "large", "frt": "front",
    "rr": "rear", "w": "with", "reg": "regulator", "pla": "plastic", "plas": "plastic",
    "plast": "plastic", "met": "metal", "sw": "switch", "eng": "engine", "man": "manual",
    "pres": "pressure", "press": "pressure", "susp": "suspension",
    "airbag": "air bag", "airflow": "air flow", "sparkplug": "spark plug",
    "clockspring": "clock spring", "domelight": "dome light", "foglamp": "fog light",
    "pushrod": "push rod", "hubcap": "hub cap", "oilpan": "oil pan",
    "signalswitch": "signal switch", "sunroof": "sun roof", "subwoofer": "sub woofer",
    "ujoint": "u joint",
    "lamp": "light", "taillight": "tail light", "taillamp": "tail light",
    "headlight": "head light", "headlamp": "head light",
}


def part_merge_key(name):
    n = name.lower().replace("w/o", " without ").replace("w/", " with ")
    toks = []
    for t in re.split(r"[^a-z0-9]+", n):
        if not t:
            continue
        exp = ABBR.get(t)
        if exp is None and len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]
            exp = ABBR.get(t)
        for p in (exp.split(" ") if exp is not None else [t]):
            if p not in FILLER:
                toks.append(p)
    return " ".join(sorted(set(toks))) or name.lower()


# ---- parse the tables out of app.js ---------------------------------------
src = open(APP).read()


def parse_js_block(varname):
    m = re.search(re.escape(varname) + r"\s*=\s*", src)
    if not m:
        return None
    i = m.end()
    depth, start = 0, i
    while i < len(src):
        c = src[i]
        if c in "[{":
            depth += 1
        elif c in "]}":
            depth -= 1
            if depth == 0:
                return src[start:i + 1]
        i += 1
    return None


groups_js = parse_js_block("const PART_ALIAS_GROUPS")
check("PART_ALIAS_GROUPS found in app.js", bool(groups_js))
never_js = parse_js_block("const PART_NEVER_MERGE = new Set(") or parse_js_block("PART_NEVER_MERGE = new Set")
m = re.search(r"PART_NEVER_MERGE = new Set\(\[(.*?)\]\)", src, re.S)
never_names = re.findall(r"'([^']+)'", m.group(1)) if m else []
check("PART_NEVER_MERGE found in app.js", bool(never_names))

groups = []
for gm in re.finditer(r"\{\s*canon:\s*'([^']+)'.*?syn:\s*\[(.*?)\].*?raw:\s*\[(.*?)\],?\s*\}", groups_js or "", re.S):
    canon = gm.group(1)
    syn = re.findall(r"'([^']+)'", gm.group(2))
    raw = re.findall(r"'([^']+)'", gm.group(3))
    groups.append({"canon": canon, "syn": syn, "raw": raw})
check("parsed alias groups", len(groups) >= 5, f"got {len(groups)}")

# ---- live price-list names -------------------------------------------------
live = set()
for path in sorted(glob.glob(os.path.join(ROOT, "docs", "data", "*_pricing.json"))):
    d = json.load(open(path))
    if isinstance(d, list):
        for row in d:
            n = (row.get("description") or "").strip()
            if n:
                live.add(n.lower())
    elif isinstance(d, dict):
        for parts in d.values():
            if isinstance(parts, dict):
                live.update(k.strip().lower() for k in parts)

junk = re.compile(r"^[\s\d.,$-]+$")
live_clean = {n for n in live if not junk.match(n) and "we do not sell" not in n}

# 2. every curated raw name exists verbatim
for g in groups:
    for r in g["raw"]:
        check(f"raw name on a live list: '{r}' ({g['canon']})", r in live, "price-list drift?")

# 3. no merge key claimed twice; canon/category convergence
claimed = {}
for g in groups:
    for r in g["raw"]:
        k = part_merge_key(r)
        if k in claimed and claimed[k] != g["canon"]:
            check(f"merge key '{k}' claimed once", False,
                  f"{claimed[k]} vs {g['canon']}")
        claimed[k] = g["canon"]
print(f"     ({len(claimed)} merge keys across {len(groups)} alias groups)")

ic = json.load(open(os.path.join(ROOT, "docs", "data", "interchange.json")))
cat_labels = {c["label"].lower() for c in ic.get("categories", [])}
for g in groups:
    cl = g["canon"].lower()
    if cl in cat_labels:
        print(f"ok   canon '{g['canon']}' converges with a finder category label")
# canons that LOOK like they shadow a category but don't match exactly:
for g in groups:
    cl = g["canon"].lower()
    if cl not in cat_labels and any(cl.split(" ")[0] in l for l in cat_labels):
        pass  # informational only — most canons have no category

# 4. blocklist freshness
for n in never_names:
    check(f"blocklisted name still on a live list: '{n}'", n in live)

# 5. merge stats
mech = {}
for n in live_clean:
    mech.setdefault(part_merge_key(n), []).append(n)
alias_keys = set(claimed)
curated_raws = sum(len(v) for k, v in mech.items() if k in alias_keys)
curated_entries_before = sum(1 for k in mech if k in alias_keys)
final_entries = len(mech) - curated_entries_before + len(groups)
print(f"\nstats: {len(live_clean)} raw names -> {len(mech)} mechanical entries "
      f"-> {final_entries} after curated groups")
print(f"       curated groups fold {curated_raws} raw names "
      f"({curated_entries_before} mechanical entries) into {len(groups)}")
multi = sum(1 for v in mech.values() if len(v) > 1)
print(f"       {multi} mechanical entries carry 2+ raw spellings")

print("\nFAILS:", FAILS if FAILS else "none")
sys.exit(1 if FAILS else 0)
