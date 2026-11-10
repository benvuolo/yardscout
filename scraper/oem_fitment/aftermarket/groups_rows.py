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
CAT_LABEL = {"headlight": "headlight", "tail-light": "tail light", "fog-light": "fog light",
             "mirror": "side mirror", "door-handle-int": "interior door handle",
             "window-regulator": "window regulator", "cv-axle": "CV axle", "strut": "strut assembly", "knuckle": "steering knuckle",
             "door-handle-ext": "exterior door handle", "door-lock-actuator": "door lock actuator",
             "wiper-motor": "wiper motor", "blower-motor": "blower motor", "maf-sensor": "mass air flow sensor",
             "throttle-body": "throttle body", "fuel-pump-module": "fuel pump module",
             "power-steering-pump": "power steering pump", "radiator": "radiator"}
SIDES = ("left", "right")
# crawl category -> the app's existing category id (hub 2026-11-09). Every
# emitted id must exist in junkyard_scraper.INTERCHANGE_PART_CATEGORIES,
# crawl.TIERS, coverage_matrix, or category breadth's pending wave (test).
CAT_OUT = {"headlight": "headlights", "tail-light": "tail-lights", "mirror": "side-mirrors",
           "fog-light": "fog-lights"}


# ------------------------------------------------------------- positions ---
def norm_position(s: str) -> str | None:
    """'Front Left' / 'Front Driver Side' -> 'front left'; 'Rear' -> 'rear';
    'Driver Side' (lamps, mirrors) -> 'left'; '' -> '' (no position, e.g. a
    radiator); anything else -> None."""
    t = re.sub(r"\s+", " ", (s or "").strip().lower())
    if not t:
        return ""
    m = re.fullmatch(r"(?:(front|rear) ?)?(left|right|driver side|passenger side)?", t)
    if not m or not (m.group(1) or m.group(2)):
        return None
    side = {"driver side": "left", "passenger side": "right"}.get(m.group(2), m.group(2))
    return " ".join(x for x in (m.group(1), side) if x)


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

    # The title's engine list covers the whole unit, not each row. On a
    # multi-model unit it puts engines on models that never had them (§11.4
    # audit 2026-11-10: TL/CL "3.0", ML320 "5.5", FX35 "3.7"). So title engines
    # go on rows only when the unit covers one make/model; otherwise no engine.
    if len(models) > 1:
        engines = [""]
    rows = []
    for a in r.get("applications", []):
        rp = norm_position(a.get("position", ""))
        if refuse is None and rp != pos:
            refuse = "row_position_differs"
        why = "submodel" if a.get("submodel") else None
        rows.append((a, rp if rp is not None else pos, engines if not why else None, why, {}))
    return refuse, pos, rows


def merged_variants(ic: list) -> bool:
    """One brand cross-referenced to several numbers (left/right pairs aside):
    a cheap sign that the unit merges variants (shakeout 2026-11-09)."""
    by = defaultdict(set)
    for x in ic:
        pn = re.sub(r"[^A-Z0-9]", "", str(x.get("pn", "")).upper())
        by[x.get("brand", "").strip().upper()].add(re.sub(r"[LR]$", "", pn))
    return any(len(v) > 1 for v in by.values())


SUSPENSION_Q = re.compile(r"suspension|adaptive|electronic|air ride|magnetic|sport susp", re.I)
_POS_IN_DESC = re.compile(r"\b(?:(?:Front|Rear) )?(?:Driver Side|Passenger Side|Left|Right)\b|\b(?:Front|Rear)\b")

# Qualifier grammar (hub 2026-11-09, CLAUDE.md rule 3 spirit). Anything a row
# says that is not in it refuses the row.
BODY_Q = re.compile(r"\b(?:(?:2|4) Door(?: (?:Sedan|Coupe|Hatchback|Wagon))?|Sedan|Coupe|Hatchback|Wagon|Convertible)\b")
BODY_CLASS = {"sedan": "sedan", "coupe": "coupe", "hatchback": "hatchback", "wagon": "wagon",
              "convertible": "convertible", "2 door coupe": "coupe", "4 door sedan": "sedan",
              "2 door hatchback": "hatchback", "4 door hatchback": "hatchback", "4 door wagon": "wagon"}
OPTION_Q = [  # (pattern, option label shown as "if equipped: <label>")
    (re.compile(r"\bwith Manual Door Locks\b"), "manual door locks"),
    (re.compile(r"\bwith Power Door Locks\b"), "power door locks"),
    (re.compile(r"\bPower Folding\b"), "power folding"),
    (re.compile(r"\bHeated\b"), "heated"),
    (re.compile(r"\bMemory\b"), "memory"),
    (re.compile(r"\b(?:with )?(?:Turn )?Signal\b"), "turn signal"),
    (re.compile(r"\bManual\b"), "manual"),
    (re.compile(r"\bPower(?! (?:Window|Door Lock|Steering))\b"), "power"),
]
COSMETIC_Q = re.compile(r"\b(?:Paint to Match|Textured|Smooth|Chrome|(?:(?:Light|Dark|Medium) )?(?:Black|Tan|Gray|"
                        r"Grey|Beige|Brown|White|Silver|Ivory|Graphite|Ebony|Parchment|Taupe))\b")
KIND_RE = re.compile(r"^(?:hvac )?blower motor(?: assembly)?|headlight(?: assembly)?|tail light(?: assembly)?|"
                     r"fog light(?: assembly)?|(?:exterior|interior|outside|inside) door handle|mirror|"
                     r"door lock actuator|power window (?:motor (?:&|and) )?regulator(?: assembly)?|"
                     r"power window motor|window regulator|strut(?: & spring)? assembly|"
                     r"shock(?: & spring)? assembly|windshield wiper motor|wiper motor$")
# On only after interchange/categories-1 (app body gate) merges AND the hub
# OKs it. Turning it on also needs: apps carrying a[5] = {"body": <class>},
# and refusal of any body outside BODY_CLASS's values ("4 door" alone is not
# a silhouette class). Until then every body-qualified row is refused.
EMIT_BODY_GATE = False
MAX_OPTIONS = 6
LAMPS = {"headlight", "tail-light", "fog-light"}


def grammar(pre: str, post: str):
    """-> (body | None, options tuple, cosmetic bool, kind, leftover).
    `pre` is the text before the position phrase, `post` the text after it."""
    body, opts, cosm = None, [], False
    parts = []
    for t in (pre, post):
        bm = list(BODY_Q.finditer(t))
        for m in bm:
            b = BODY_CLASS.get(m.group(0).lower(), m.group(0).lower())
            body = b if body in (None, b) else "conflict"
        t = BODY_Q.sub(" ", t)
        for rx, lab in OPTION_Q:
            if rx.search(t):
                opts.append(lab)
                t = rx.sub(" ", t)
        if COSMETIC_Q.search(t):
            cosm = True
            t = COSMETIC_Q.sub(" ", t)
        parts.append(re.sub(r"\s+", " ", t).strip())
    leftover_pre, kind = parts[0], parts[1].lower()
    km = KIND_RE.match(kind)
    leftover = " ".join(x for x in (leftover_pre, "" if km and km.group(0) == kind else kind) if x)
    return body, tuple(sorted(set(opts))), cosm, kind if km else "", leftover


def oneaauto_rows(r: dict):
    """-> (unit_refusal, position, [(row, position, engines | None, row_refusal, meta)])"""
    flags = [f for f in r.get("flags", []) if f != "multi_make"]
    refuse = ("flag:" + flags[0]) if flags else None
    if refuse is None and merged_variants(r.get("interchange_numbers", [])):
        refuse = "interchange_variants"
    rows = []
    positions, optsets = set(), set()
    tail = f" {r.get('house_brand', '')} {r.get('house_brand_pn', '')}".rstrip()
    for a in r.get("applications", []):
        d = a.get("description", "")
        if tail.strip() and d.endswith(tail):
            d = d[: -len(tail)]
        pre = f"{a['make']} {a['model']} "
        if not d.startswith(pre):
            rows.append((a, None, None, "description_shape", {}))
            continue
        rest = d[len(pre):]
        # the LAST position phrase: "Front Wheel Drive Front Passenger Side"
        # keeps "Front Wheel Drive" as a (refused) qualifier
        ms = [x for x in _POS_IN_DESC.finditer(rest) if not rest[x.end():].startswith(" Wheel Drive")]
        m = ms[-1] if ms else None
        q, post, rp = (rest[:m.start()], rest[m.end():], norm_position(m.group(0))) if m else ("", rest, "")
        body, opts, cosm, kind, left = grammar(q.strip(), post.strip())
        meta = {"kind": kind, "options": opts, "body": body, "cosmetic": cosm}
        if rp is not None:
            positions.add(rp)
        optsets.add(opts)
        if left:
            rows.append((a, rp, None, "qualifier:" + left, meta))
        elif not kind:
            rows.append((a, rp, None, "unknown_kind", meta))
        elif body == "conflict" or (body and not EMIT_BODY_GATE):
            rows.append((a, rp, None, "body_gate_pending" if body != "conflict" else "body_conflict", meta))
        else:
            rows.append((a, rp, [""], None, meta))
    if refuse is None and len(optsets) > 1:
        refuse = "options_differ_across_rows"
    if refuse is None and any(len(o) > MAX_OPTIONS for o in optsets):
        refuse = "too_many_options"  # app accepts <= 6 items (category breadth)
    pos = next(iter(positions)) if len(positions) == 1 else ""
    return refuse, pos, rows


# ------------------------------------------------------ donor drive gate (d) ---
# Hub 2026-11-10, rule (d). Basis (physical, not fitment): a CV axle exists
# only at a DRIVEN corner. The gate reads the DONOR's own VIN decode
# (vPIC DriveType); there is no make-level table. Tokens match docs/app.js
# PF_AM_DRIVE so the app's mirror (pfAmAxleVerdict) classes drives the same way.
DRIVE_TOKENS = {"4wd": ("4wd", "4x4", "four-wheel"), "awd": ("awd", "all-wheel"),
                "rwd": ("rwd", "rear-wheel"), "fwd": ("fwd", "front-wheel"), "2wd": ("2wd", "4x2")}


def drive_classes(drive_type: str) -> set:
    dt = (drive_type or "").lower()
    return {c for c, toks in DRIVE_TOKENS.items()
            if any(re.search(rf"(^|[^a-z0-9]){re.escape(t)}($|[^a-z0-9])", dt) for t in toks)}


def axle_donor_verdict(axle: str, drive_type: str) -> str:
    """'pass' | 'exclude' | 'check' (unknown: keep "check drive").
    front axle: exclude a donor decoded only RWD or only 4x2/2WD (a 4x2 that is
      in fact FWD is hidden too: never a wrong donor, at worst a missed one);
    rear axle: exclude a donor decoded only FWD (4x2 stays 'check');
    AWD / 4WD pass; blank, mixed or unrecognised stays 'check'."""
    cls = drive_classes(drive_type)
    if cls & {"awd", "4wd"}:
        return "pass"
    if axle == "front":
        if cls == {"fwd"}:
            return "pass"
        if cls in ({"rwd"}, {"2wd"}, {"rwd", "2wd"}):
            return "exclude"
    if axle == "rear":
        if cls == {"rwd"} or cls == {"rwd", "2wd"}:
            return "pass"
        if cls == {"fwd"}:
            return "exclude"
    return "check"


# ------------------------------------------------------------- generations ---
MAX_SPAN_NO_GEN = 6  # model years, inclusive, for a model with no generation entry


def load_generations() -> dict:
    """squash(make)|squash(model) -> [[from, to], ...] from the app's own table
    (docs/data/interchange.json modelGenerations, PART_CATALOG_SPEC §5.1)."""
    p = GA.REPO / "docs" / "data" / "interchange.json"
    try:
        rows = json.loads(p.read_text()).get("modelGenerations", [])
    except (OSError, ValueError):
        rows = []
    return {f"{GA.squash(mk)}|{GA.squash(md)}": wins for mk, md, wins in rows}


def span_ok(gens: dict, make: str, models: list, lo: int, hi: int) -> bool:
    """Hub 2026-11-09: a row whose span crosses a generation boundary is coarse
    and refused; with no generation entry, only spans <= 6 model years pass."""
    for md in models:
        wins = gens.get(f"{GA.squash(make)}|{GA.squash(md)}")
        if wins is not None:
            return any(w[0] <= lo and hi <= w[1] for w in wins)
    return hi - lo + 1 <= MAX_SPAN_NO_GEN


def load_facelifts() -> dict:
    """model (lower) -> facelift start years, from the Parts table
    (scraper/junkyard_scraper.FACELIFT_BREAKS); one source, no copy."""
    sys.path.insert(0, str(GA.REPO / "scraper"))
    try:
        import junkyard_scraper as js  # noqa: E402
        return {k.lower(): list(v) for k, v in js.FACELIFT_BREAKS.items()}
    except (ImportError, AttributeError):
        return {}


def crosses_facelift(fl: dict, models: list, lo: int, hi: int) -> bool:
    for md in models:
        for y in fl.get(str(md).lower(), []):
            if lo < y <= hi:
                return True
    return False


def split(units: dict) -> bool:
    """Units of one brand+kind+body claiming one corner-year. Not a split when
    there is one unit, or when every unit states a non-empty option set and
    the sets all differ (the option tells them apart: "if equipped")."""
    if len(units) <= 1:
        return False
    sets = list(units.values())
    return not (all(sets) and len(set(sets)) == len(sets))


# ------------------------------------------------------------------ build ---
def build(records: list, names: GA.Names, site: str, src: str = "", complete: dict | None = None,
          gens: dict | None = None, facelifts: dict | None = None) -> dict:
    gens = load_generations() if gens is None else gens
    fl = load_facelifts() if facelifts is None else facelifts
    meta = SITES[site]
    rowfn = gsp_rows if meta["short"] == "gsp" else oneaauto_rows
    refused_units, refused_rows, unmapped = Counter(), Counter(), Counter()
    claims = defaultdict(dict)           # (cat, brand, mk, md, year, pos) -> {unit: options}
    unit_meta = {}                       # (cat, unit) -> (options, cosmetic)
    accepted = defaultdict(list)         # (cat, unit, pos) -> [(mk, md, year, eng)]
    retrieved, seen = {}, set()
    # models the source ever qualifies by a suspension option (any unit, any year)
    susp_models = set()
    for r in records:
        for a in r.get("applications", []):
            if SUSPENSION_Q.search(a.get("description", "")) or SUSPENSION_Q.search(a.get("submodel", "")):
                susp_models.add((a["make"], a["model"]))
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
        # unit-level generation guard (hub 2026-11-10): a unit whose rows for one
        # make/model, taken together, span more than one generation is a coarse
        # merge (M37 + Q60, A3 8V + 8Y): refuse the unit; its rows still claim
        if refuse is None:
            by_model = defaultdict(list)
            for a, *_rest in rows:
                by_model[(a["make"], a["model"])].append(a["years"])
            for (mk0, md0), yrs in by_model.items():
                c0 = names.canon(mk0, md0)
                if c0 is None:
                    continue
                lo0, hi0 = min(y[0] for y in yrs), max(y[1] for y in yrs)
                if not span_ok(gens, c0[0], [c0[1], md0], lo0, hi0):
                    refuse = "unit_spans_generations"
                    refused_units[f"{cat}:unit_spans_generations"] += 1
                    break
        qualified_models = {(a["make"], a["model"]) for a, _rp, _e, why, mt in rows
                            if why or mt.get("options") or mt.get("body")}
        for a, rp, engines, why, mt in rows:
            # a unqualified row of a make/model this unit also lists WITH a
            # qualifier is coarse data: refuse it (shakeout 2026-11-09)
            if not why and not mt.get("options") and (a["make"], a["model"]) in qualified_models:
                why = "sibling_row_qualified"
            if not why and cat == "strut" and (a["make"], a["model"]) in susp_models:
                why = "model_has_suspension_options"
            # product kind (1A: "strut & spring assembly" vs bare "strut assembly")
            # is part of the split key: two kinds for one corner are not a split
            brand = (brand_name, mt.get("kind", ""), mt.get("body") or "")
            c = names.canon(a["make"], a["model"])
            if c is None or c[2] is False:
                unmapped[f"{a['make']} | {a['model']}"] += 1
                continue
            mk, md, _ = c
            if not why and not span_ok(gens, mk, [md, a["model"]], a["years"][0], a["years"][1]):
                why = "generation_span"
            if not why and cat in LAMPS and crosses_facelift(fl, [md, a["model"]], a["years"][0], a["years"][1]):
                why = "facelift_span"
            cpos = rp if rp is not None else (pos or "")
            for y in range(a["years"][0], a["years"][1] + 1):
                for p in claim_positions(cpos):
                    claims[(cat, brand, mk, md, y, p)][unit] = mt.get("options", ())
            if why:
                refused_rows[why if not why.startswith("qualifier:") else "qualifier"] += 1  # noqa
                if why.startswith("qualifier:"):
                    refused_rows["q: " + why.split(":", 1)[1]] += 1
                continue
            if refuse:
                continue
            for y in range(a["years"][0], a["years"][1] + 1):
                for e in engines:
                    accepted[(cat, unit, cpos)].append((mk, md, y, e, brand))
            retrieved[(cat, unit)] = r.get("retrieved", "")
            unit_meta[(cat, unit)] = (mt.get("options", ()), mt.get("cosmetic", False))
    conflicts = Counter()
    groups = []
    for (cat, unit, pos), rows in sorted(accepted.items()):
        keep = defaultdict(list)
        for mk, md, y, e, brand in rows:
            if any(split(claims[(cat, brand, mk, md, y, p)]) for p in claim_positions(pos)):
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
        opts, cosm = unit_meta.get((cat, unit), ((), False))
        note = (f"{meta['label']} {unit} ({where}{CAT_LABEL.get(cat, cat)}) is listed for each of these "
                f"vehicles in {meta['label']}'s own application list; aftermarket data, not the carmaker's "
                f"catalog. No other unit of the same brand is listed for the same {where or ''}position on these "
                f"cars. " + ("Match the engine. " if eng else "No engine is stated; check the engine. ")
                + "Drive, transmission, trim and suspension (sport / electronic) are not stated; match them."
                + (f" If equipped: {', '.join(opts)}." if opts else "")
                + (" Color or finish may differ; it may need paint." if cosm else ""))
        ocat = CAT_OUT.get(cat, cat)
        groups.append({"id": f"am:{meta['short']}:{ocat}:{unit}" + (f":{pos.replace(' ', '-')}" if pos else ""), "cat": ocat, "tier": "likely",
                       "src": "aftermarket", "label": f"{meta['label']} {where.strip()}".strip(),
                       "unit": unit, "position": pos, "apps": apps, "cross_model": len(models) > 1,
                       "body_gated": False, "retrieved": retrieved.get((cat, unit), ""),
                       "pro_gated": False, "if_equipped": list(opts), "option": bool(opts),
                       "cosmetic": bool(cosm), "note": note,
                       **({"driven_axle": pos.split(" ")[0]} if cat == "cv-axle" and pos else {})})
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
