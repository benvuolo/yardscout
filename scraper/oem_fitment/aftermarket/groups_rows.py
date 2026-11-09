#!/usr/bin/env python3
"""Per-unit application rows (GSP, 1A Auto) -> aftermarket Likely groups. Offline.

    python3 scraper/oem_fitment/aftermarket/groups_rows.py --site gspnorthamerica.com|www.1aauto.com \
        [--raw FILE | --raw-ref origin/oem-raw] [--out FILE] [--report FILE]

A group is one unit (GSP part number / 1A Auto item number) in one category
and position. Tier is always "likely", src "aftermarket"; never Verified.

Strict rules (hub 2026-11-09; SOURCES.md "Source scout 2"):
- Every printed row is a CLAIM: (category, make, model, year, position). A
  vehicle-position claimed by more than one unit (refused rows and refused
  units included) is dropped from every unit. This is what keeps invisible
  drive / trim / trans splits out: when GSP or 1A sell two units for one
  car's front-left corner, we publish neither.
- Only an unqualified row becomes an app. A row qualified by a trim, body,
  option, production date, hybrid, "without …" or anything else is refused
  (it still claims). 1A rows qualified by exactly an engine ("V6 3.0L") are
  accepted with that engine. Body gating is NOT emitted yet: docs/app.js
  pfAmRows does not read a body element (a[5]).
- GSP: a unit is refused on any parser flag (duplicate rows, missing
  position, header change, ...), on a title with no engine, on any title
  token that is not a displacement ("AWD", "2.4i"), on a position that
  differs from the title's, and on several engines across several models
  (the engine list is then not per row). The title's engines go on every
  app ("match the engine"); drive and transmission are never inferred.
- 1A Auto: a unit is refused on any parser flag. Its "Part Interchange"
  numbers are brand equivalence only and are never used for fitment.
- Facts only: no price, description, image or page text is read into the
  output. Notes are our own words. 1A Auto rows are never Pro-gated (owner:
  "1A im not selling the part fitment portion").
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import groups_am as GA  # noqa: E402

SCHEMA = 1
SITES = {
    "gspnorthamerica.com": {"short": "gsp", "label": "GSP", "file": "gspnorthamerica"},
    "www.1aauto.com": {"short": "1a", "label": "1A Auto", "file": "oneaauto"},
}
CAT_LABEL = {"cv-axle": "CV axle", "strut": "strut assembly", "knuckle": "steering knuckle",
             "door-handle-ext": "exterior door handle", "door-lock-actuator": "door lock actuator",
             "wiper-motor": "wiper motor", "blower-motor": "blower motor", "maf-sensor": "mass air flow sensor",
             "throttle-body": "throttle body", "fuel-pump-module": "fuel pump module",
             "power-steering-pump": "power steering pump", "radiator": "radiator"}
SIDES = ("left", "right")


# ------------------------------------------------------------- positions ---
def norm_position(s: str) -> str | None:
    """'Front Left' / 'Front Driver Side' -> 'front left'; 'Rear' -> 'rear';
    '' -> '' (no position, e.g. a radiator); anything else -> None."""
    t = re.sub(r"\s+", " ", (s or "").strip().lower())
    if not t:
        return ""
    m = re.fullmatch(r"(front|rear)(?: (left|right|driver side|passenger side))?", t)
    if not m:
        return None
    side = {"driver side": "left", "passenger side": "right"}.get(m.group(2), m.group(2))
    return m.group(1) + (f" {side}" if side else "")


def claim_positions(pos: str) -> list[str]:
    """Corners a position covers: a bare 'front' covers both front corners;
    'front left' only itself. Units conflict when they cover a common corner."""
    if pos in ("front", "rear"):
        return [f"{pos} {s}" for s in SIDES]
    return [pos]


# ---------------------------------------------------------------- per site ---
LITERS_RE = re.compile(r"^\d\.\d$")


def gsp_rows(r: dict):
    """-> (unit_refusal or None, position, [(row, accepted_engines or None, row_refusal)])"""
    flags = [f for f in r.get("flags", []) if f != "multi_make"]
    pos = norm_position(r.get("title_position", ""))
    refuse = None
    if flags:
        refuse = "flag:" + flags[0]
    elif pos is None or pos == "":
        refuse = "title_position"
    toks = r.get("title_engines", [])
    if refuse is None:
        bad = [t for t in toks if not LITERS_RE.match(t)]
        if not toks:
            refuse = "no_title_engine"
        elif bad:
            refuse = "title_token:" + bad[0]
    engines = [f"{float(t):.1f}L" for t in toks if LITERS_RE.match(t)]
    models = {(a["make"], a["model"]) for a in r.get("applications", [])}
    if refuse is None and len(engines) > 1 and len(models) > 1:
        refuse = "multi_engine_multi_model"
    rows = []
    for a in r.get("applications", []):
        rp = norm_position(a.get("position", ""))
        if refuse is None and rp != pos:
            refuse = "row_position_differs"
        why = "submodel" if a.get("submodel") else None
        rows.append((a, rp if rp is not None else pos, engines if not why else None, why))
    return refuse, pos, rows


_POS_IN_DESC = re.compile(r"\b(Front|Rear)(?: (Driver Side|Passenger Side|Left|Right))?\b")
_ENG_Q = re.compile(r"^([VLHIW])(\d{1,2}) (\d\.\d)L$")


def oneaauto_rows(r: dict):
    flags = [f for f in r.get("flags", []) if f != "multi_make"]
    refuse = ("flag:" + flags[0]) if flags else None
    rows = []
    positions = set()
    tail = f" {r.get('house_brand', '')} {r.get('house_brand_pn', '')}".rstrip()
    for a in r.get("applications", []):
        d = a.get("description", "")
        if tail.strip() and d.endswith(tail):
            d = d[: -len(tail)]
        pre = f"{a['make']} {a['model']} "
        if not d.startswith(pre):
            rows.append((a, None, None, "description_shape"))
            continue
        rest = d[len(pre):]
        m = _POS_IN_DESC.search(rest)
        if not m:
            q, rp = rest, ""
        else:
            q, rp = rest[:m.start()].strip(), norm_position(m.group(0))
            a = {**a, "kind": rest[m.end():].strip().lower()}
        if rp is not None:
            positions.add(rp)
        if not q:
            rows.append((a, rp, [""], None))
        elif _ENG_Q.match(q):
            e = _ENG_Q.match(q)
            rows.append((a, rp, [f"{float(e.group(3)):.1f}L {int(e.group(2))}-cyl"], None))
        else:
            rows.append((a, rp, None, "qualifier:" + q))
    # per-row positions: one unit may be listed for the left corner of one car
    # and the right corner of another; groups are per (unit, position)
    pos = next(iter(positions)) if len(positions) == 1 else ""
    return refuse, pos, rows


# ------------------------------------------------------------------ build ---
def build(records: list, names: GA.Names, site: str, src: str = "", complete: dict | None = None) -> dict:
    meta = SITES[site]
    rowfn = gsp_rows if meta["short"] == "gsp" else oneaauto_rows
    refused_units, refused_rows, unmapped = Counter(), Counter(), Counter()
    claims = defaultdict(set)            # (cat, brand, mk, md, year, pos) -> {unit}
    accepted = defaultdict(list)         # (cat, unit, pos) -> [(mk, md, year, eng)]
    retrieved, seen = {}, set()
    for r in records:
        unit, cat = r.get("aftermarket_pn", ""), r.get("category", "")
        if not unit or (cat, unit) in seen:
            continue
        seen.add((cat, unit))
        refuse, pos, rows = rowfn(r)
        # one brand's line is the split evidence: equivalent units of OTHER
        # brands (a retailer's TRQ / KYB / Monroe for one corner) do not conflict
        brand_name = r.get("house_brand") or meta["label"]
        if refuse:
            refused_units[f"{cat}:{refuse.split(':')[0]}"] += 1
            if refuse.startswith("title_token:"):
                refused_rows["title_token " + refuse.split(":", 1)[1]] += 1
        for a, rp, engines, why in rows:
            # product kind (1A: "strut & spring assembly" vs bare "strut assembly")
            # is part of the split key: two kinds for one corner are not a split
            brand = (brand_name, a.get("kind", ""))
            c = names.canon(a["make"], a["model"])
            if c is None or c[2] is False:
                unmapped[f"{a['make']} | {a['model']}"] += 1
                continue
            mk, md, _ = c
            cpos = rp if rp is not None else (pos or "")
            for y in range(a["years"][0], a["years"][1] + 1):
                for p in claim_positions(cpos):
                    claims[(cat, brand, mk, md, y, p)].add(unit)
            if why:
                refused_rows[why if not why.startswith("qualifier:") else "qualifier"] += 1
                if why.startswith("qualifier:"):
                    refused_rows["q: " + why.split(":", 1)[1]] += 1
                continue
            if refuse:
                continue
            for y in range(a["years"][0], a["years"][1] + 1):
                for e in engines:
                    accepted[(cat, unit, cpos)].append((mk, md, y, e, brand))
            retrieved[(cat, unit)] = r.get("retrieved", "")
    conflicts = Counter()
    groups = []
    for (cat, unit, pos), rows in sorted(accepted.items()):
        keep = defaultdict(list)
        for mk, md, y, e, brand in rows:
            if any(len(claims[(cat, brand, mk, md, y, p)]) > 1 for p in claim_positions(pos)):
                conflicts[cat] += 1
                continue
            keep[(mk, md, e)].append(y)
        apps = [[mk, md, lo, hi, e] for (mk, md, e), ys in sorted(keep.items()) for lo, hi in GA._runs(ys)]
        if not apps:
            refused_units[f"{cat}:all_rows_conflict"] += 1  # per (unit, position)
            continue
        models = {(a[0], a[1]) for a in apps}
        where = f"{pos} " if pos else ""
        eng = any(a[4] for a in apps)
        note = (f"{meta['label']} {unit} ({where}{CAT_LABEL.get(cat, cat)}) is listed for each of these "
                f"vehicles in {meta['label']}'s own application list; aftermarket data, not the carmaker's "
                f"catalog. No other unit of the same brand is listed for the same {where or ''}position on these "
                f"cars. " + ("Match the engine. " if eng else "No engine is stated; check the engine. ")
                + "Drive and transmission are not stated; check them.")
        groups.append({"id": f"am:{meta['short']}:{cat}:{unit}" + (f":{pos.replace(' ', '-')}" if pos else ""), "cat": cat, "tier": "likely",
                       "src": "aftermarket", "label": f"{meta['label']} {where.strip()}".strip(),
                       "unit": unit, "position": pos, "apps": apps, "cross_model": len(models) > 1,
                       "body_gated": False, "retrieved": retrieved.get((cat, unit), ""),
                       "pro_gated": False, "note": note})
    doc = {"schema": SCHEMA, "src": "aftermarket", "site": site, "raw": src, "tier": "likely",
           "crawl_complete": complete or {}, "groups": groups,
           "summary": {"unit_records": len(seen), "groups": len(groups),
                       "cross_model_groups": sum(g["cross_model"] for g in groups),
                       "apps": sum(len(g["apps"]) for g in groups),
                       "by_cat": dict(Counter(g["cat"] for g in groups)),
                       "cross_model_by_cat": dict(Counter(g["cat"] for g in groups if g["cross_model"])),
                       "refused_units": dict(sorted(refused_units.items())),
                       "conflict_rows_dropped": dict(conflicts)},
           "refused_rows": dict(refused_rows.most_common(60)),
           "unmapped_models": dict(unmapped.most_common())}
    doc["sha256"] = hashlib.sha256(json.dumps(groups, sort_keys=True).encode()).hexdigest()
    return doc


def load(site: str, raw: str | None, raw_ref: str | None):
    path = f"aftermarket/raw/{site}"
    if raw_ref:
        def show(p):
            res = subprocess.run(["git", "show", f"{raw_ref}:{p}"], cwd=GA.REPO, capture_output=True, text=True)
            return res.stdout if res.returncode == 0 else ""
        txt = show(f"{path}.jsonl")
        prog = show(f"{path}.progress.json")
        sha = subprocess.run(["git", "rev-parse", raw_ref], cwd=GA.REPO, capture_output=True, text=True).stdout.strip()
        src = f"{raw_ref}@{sha[:8]}"
    else:
        p = Path(raw) if raw else HERE / "raw" / f"{site}.jsonl"
        txt, src = p.read_text(), str(p)
        pp = p.with_name(f"{site}.progress.json")
        prog = pp.read_text() if pp.exists() else ""
    complete = {}
    if prog:
        try:
            complete = {c: bool(v.get("finished")) for c, v in json.loads(prog).get("cats", {}).items()}
        except ValueError:
            complete = {}
    return [json.loads(x) for x in txt.splitlines() if x.strip()], src, complete


def report_md(doc: dict) -> str:
    s = doc["summary"]
    out = [f"# {SITES[doc['site']]['label']} aftermarket groups (not shipped)", "", f"raw: {doc['raw']}",
           f"crawl complete by category: {doc['crawl_complete']}", "",
           f"- unit records: {s['unit_records']}", f"- groups: {s['groups']} (cross-model "
           f"{s['cross_model_groups']}), app rows {s['apps']}", f"- by category: {s['by_cat']}",
           f"- refused units: {s['refused_units']}", f"- conflict rows dropped: {s['conflict_rows_dropped']}",
           "", "## Refused rows (top)", ""]
    out += [f"- {n} x {c}" for c, n in doc["refused_rows"].items()]
    out += ["", "## Unmapped models (top 40)", ""]
    out += [f"- {n} x {m}" for m, n in list(doc["unmapped_models"].items())[:40]]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, choices=sorted(SITES))
    ap.add_argument("--raw")
    ap.add_argument("--raw-ref")
    ap.add_argument("--out")
    ap.add_argument("--report")
    a = ap.parse_args(argv)
    recs, src, complete = load(a.site, a.raw, a.raw_ref)
    lot = None
    inv_p = GA.REPO / "docs" / "data" / "inventory_live.json"
    if inv_p.exists():
        inv = json.loads(inv_p.read_text())
        F = {k: i for i, k in enumerate(inv["fields"])}
        lot = {(v[F["make"]] or "", v[F["model"]] or "") for v in inv["vehicles"]}
    doc = build(recs, GA.Names(lot), a.site, src, complete)
    f = SITES[a.site]["file"]
    out = Path(a.out or HERE / "curated" / f"{f}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    Path(a.report or HERE / "curated" / f"{f}.md").write_text(report_md(doc))
    print(json.dumps(doc["summary"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
