#!/usr/bin/env python3
"""Spectra Premium vehicle records -> aftermarket Likely groups. Offline.

    python3 scraper/oem_fitment/aftermarket/groups_spectra.py \
        [--raw FILE | --raw-ref origin/oem-raw] [--out FILE] [--report FILE]

Input: aftermarket/raw/ecat.spectrapremium.com.jsonl, one record per vehicle
page (spectrapremium.py): year, make, model, submodel ("LX L4 1.8L"),
motorization (Fuel, ASP., Eng. Desg.), and every part card (pn, line,
application note).

A group is one Spectra unit (line + part number). Its apps are the lot
vehicles whose OWN vehicle page lists that unit, by observed year only (no
year is filled in between crawled years). Tier is always "likely", src
"aftermarket": never Verified (CURATION_SPEC §12).

Tightening (ops/interchange.md "Aftermarket tightening" + hub 2026-11-09):
- Notes are split on ";" and each clause is classified:
  "Body Type: X"   -> body gate (the puller can see the body style);
  install-only clauses on an allowlist (INSTALL_RE) -> no condition;
  ANY other clause (plant "USA Built", emissions "California", trans,
  options, "w/", "exc.", unknown wording) -> the card is refused.
- Per vehicle and line, every card must be accepted, and the cards must
  be told apart by body alone (one card, or one card per stated body). If
  not, all cards of that line on that vehicle are dropped (ambiguous).
- Per (make, model, year, engine label) the resolution (body -> unit) must
  be the same on every crawled submodel / motorization. A trim, turbo or
  engine-code split under the same liters/cylinders drops that key.
- Fuel must be GAS or DIESEL (CNG, electric, hybrid-only rows are refused).
- Make/model go through the scraper's normalizers (groups_am.Names); names
  that match no lot model are reported, never guessed.
Notes in the output are our own words; no page text is published.
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

SITE = "ecat.spectrapremium.com"
RAW_PATH = f"aftermarket/raw/{SITE}.jsonl"
SCHEMA = 1

# Spectra line -> our category slug (coverage_matrix names where they exist)
LINES = {
    "Automotive Radiator": "radiator",
    "Compressor": "ac-compressor",
    "Condenser": "ac-condenser",
    "Evaporator": "evaporator",
    "Heater": "heater-core",
    "Fuel Tank": "fuel-tank",
    "Fuel Module": "fuel-pump-module",
    "Ignition Coil": "ignition-coils",
    "Electronic Throttle Body": "throttle-body",
}
LABEL = {"radiator": "radiator", "ac-compressor": "A/C compressor", "ac-condenser": "A/C condenser",
         "evaporator": "A/C evaporator", "heater-core": "heater core", "fuel-tank": "fuel tank",
         "fuel-pump-module": "fuel pump module", "ignition-coils": "ignition coil",
         "throttle-body": "electronic throttle body"}

BODY_RE = re.compile(r"^Body Type:\s*([A-Za-z ]+)$")
BODIES = {"sedan", "coupe", "hatchback", "wagon", "convertible", "van", "minivan", "pickup", "suv",
          "sport utility", "cab chassis", "standard cab pickup", "extended cab pickup",
          "crew cab pickup"}
# install / packaging / description clauses that do not limit which car it fits
INSTALL_RE = re.compile(
    r"^(?:New|Remanufactured|with Clutch|without Clutch|Sensor Only|Complete Assembly|Desiccant Kit"
    r"|with Receiver Drier|Includes? (?:Drier|Receiver Drier|Gasket|Seal|Lock Ring)[A-Za-z ,]*"
    r"|Qty\.? Req\.?:\s*\d+|Ignition Coil Mounts to Cylinder Head"
    r"|May Require Use Of Original [A-Za-z ]+"
    r"|Replacement of Stretch Fit Belt Required"
    r"|Gasket And/Or Sealant Not Included"
    r"|Contains \d+ Units?|Pack|Radiator Cap Is Required"
    r"|Hoist May Be Required for Radiator Installation Underneath the Vehicle"
    r"|Module has \d+ Electrical Connector\(s\)"
    r"|Transmission Control Type: Manual OR Transmission Control Type: Automatic"
    r"|Transmission Control Type: Automatic OR Transmission Control Type: Manual"
    r"|Failure [Tt]o [A-Za-z ,/]+ (?:Will )?[Vv]oid(?: [Tt]he)? [Ww]arranty\.?)$")


def clauses(note: str) -> list[str]:
    return [c.strip().rstrip(".").strip() for c in (note or "").split(";") if c.strip()]


OE_RE = re.compile(r"^Services OE #\s*([A-Z0-9-]+)$")


def oe_refs(note: str) -> list[str]:
    return [m.group(1) for m in (OE_RE.match(c) for c in clauses(note)) if m]


DRIVE_RE = re.compile(r"^Drive Type:\s*(AWD|4WD|FWD|RWD)$")
FUEL_LINES = {"fuel-pump-module", "fuel-tank"}


def classify(note: str):
    """-> ("ok", gates) | ("refuse", clause). gates is a sorted tuple of
    (gate, value) pairs, () for no condition. Gates: "body" (Body Type, as
    printed, title case) and "drive" (Drive Type, lower case like the parts
    table's drive gate: awd / 4wd / fwd / rwd). Never inferred."""
    gates: dict = {}
    for c in clauses(note):
        if OE_RE.match(c):
            continue                        # an OE reference, kept as data, not a limit
        m = BODY_RE.match(c)
        if m and m.group(1).strip().lower() in BODIES:
            if "body" in gates:
                return "refuse", c          # two body clauses
            gates["body"] = m.group(1).strip().title()
            continue
        m = DRIVE_RE.match(c)
        if m:
            if "drive" in gates:
                return "refuse", c
            gates["drive"] = m.group(1).lower()
            continue
        if INSTALL_RE.match(c):
            continue
        return "refuse", c
    return "ok", tuple(sorted(gates.items()))


def engine_label(rec: dict) -> str | None:
    """'1.8L 4-cyl' from the submodel's engine ('LX L4 1.8L'); None if absent."""
    m = re.search(r"\b([LVHW])(\d{1,2})\s+(\d\.\d)L\b", rec.get("submodel", ""))
    if not m:
        return None
    fuel = (rec.get("motorization") or {}).get("Fuel", "").upper()
    return f"{float(m.group(3)):.1f}L {int(m.group(2))}-cyl" + (" diesel" if fuel == "DIESEL" else "")


def resolve(cards: list) -> tuple[dict | None, str]:
    """Cards of ONE line on ONE vehicle -> ({gates: pn}, "") or (None, why).
    The cards must be told apart by their gates alone: one card, or one card
    per distinct gate value over the SAME gate dimensions."""
    res: dict = {}
    for c in cards:
        st, v = classify(c.get("note", ""))
        if st == "refuse":
            return None, f"note:{v}"
        if v in res and res[v] != c["pn"]:
            return None, "two_units_same_gates"
        res[v] = c["pn"]
    if len(res) > 1 and len({tuple(k for k, _ in g) for g in res}) != 1:
        return None, "units_on_different_gate_dimensions"   # also covers () with a gated one
    return res, ""


def load_raw(raw: str | None, raw_ref: str | None) -> tuple[list, str]:
    if raw_ref:
        txt = subprocess.run(["git", "show", f"{raw_ref}:scraper/oem_fitment/{RAW_PATH}"], cwd=GA.REPO,
                             capture_output=True, text=True, check=True).stdout
        sha = subprocess.run(["git", "rev-parse", raw_ref], cwd=GA.REPO, capture_output=True,
                             text=True, check=True).stdout.strip()
        src = f"{raw_ref}@{sha[:8]}"
    else:
        p = Path(raw) if raw else HERE / "raw" / f"{SITE}.jsonl"
        txt, src = p.read_text(), str(p)
    return [json.loads(x) for x in txt.splitlines() if x.strip()], src


def build(records: list, names: GA.Names, src: str = "") -> dict:
    refused = Counter()
    refused_clause = Counter()
    unmapped = Counter()
    lines_seen = Counter()
    # (cat, mk, md, year, eng) -> list of resolutions (one per vehicle record)
    reso: dict = defaultdict(list)
    retrieved: dict = {}
    oe_by_unit: dict = defaultdict(set)
    seen_vid = set()
    for r in records:
        if r.get("vehicle_id") in seen_vid:
            continue
        seen_vid.add(r.get("vehicle_id"))
        if any(f.startswith("card_count_mismatch") or f == "pn_differs_from_link" for f in r.get("flags", [])):
            refused["vehicle_flagged"] += 1
            continue
        fuel = (r.get("motorization") or {}).get("Fuel", "").upper()
        if fuel not in ("GAS", "DIESEL", "FLEX"):
            refused[f"fuel:{fuel or 'none'}"] += 1
            continue
        eng = engine_label(r)
        if not eng:
            refused["no_engine_in_submodel"] += 1
            continue
        c = names.canon(r["make"], r["model"])
        if c is None:
            unmapped[f"{r['make']} | {r['model']}"] += 1
            continue
        mk, md, on_lot = c
        if on_lot is False:
            unmapped[f"{mk} | {r['model']}"] += 1
            continue
        by_line = defaultdict(list)
        for card in r.get("cards", []):
            lines_seen[card.get("line", "")] += 1
            cat = LINES.get(card.get("line", ""))
            if cat:
                by_line[cat].append(card)
        for cat, cards in by_line.items():
            if fuel == "FLEX" and cat in FUEL_LINES:
                refused[f"{cat}:fuel_FLEX"] += 1
                continue
            for card in cards:
                oe_by_unit[(cat, card["pn"])].update(oe_refs(card.get("note", "")))
            res, why = resolve(cards)
            key = (cat, mk, md, int(r["year"]), eng)
            if res is None:
                refused[f"{cat}:{why.split(':')[0]}"] += 1
                if why.startswith("note:"):
                    refused_clause[why[5:]] += 1
                reso[key].append((fuel, None))
            else:
                reso[key].append((fuel, tuple(sorted(res.items()))))
            retrieved[key] = max(retrieved.get(key, ""), r.get("retrieved", ""))
    # consistency across submodels / motorizations
    units: dict = defaultdict(lambda: defaultdict(list))   # (cat, pn) -> (mk, md, eng, body) -> years
    unit_ret: dict = defaultdict(str)
    split = Counter()
    for key, rs in reso.items():
        cat, mk, md, y, eng = key
        fuels = {f for f, _ in rs}
        rs = [x for _, x in rs]
        if any(x is None for x in rs):
            continue
        if "FLEX" in fuels and "GAS" not in fuels:
            split[f"{cat}:flex_without_gas"] += 1   # FLEX rows count only beside the same GAS unit
            continue
        if len(set(rs)) != 1:
            split[cat if fuels != {"GAS", "FLEX"} else f"{cat}:flex_gas_differ"] += 1
            continue
        for gates, pn in rs[0]:
            units[(cat, pn)][(mk, md, eng, gates)].append(y)
            unit_ret[(cat, pn)] = max(unit_ret[(cat, pn)], retrieved[key])
    groups = []
    for (cat, pn), rows in sorted(units.items()):
        apps = []
        for (mk, md, eng, gates), ys in sorted(rows.items()):
            for lo, hi in GA._runs(ys):
                apps.append([mk, md, lo, hi, eng] + ([dict(gates)] if gates else []))
        models = {(a[0], a[1]) for a in apps}
        bodies = sorted({a[5]["body"] for a in apps if len(a) > 5 and "body" in a[5]})
        drives = sorted({a[5]["drive"] for a in apps if len(a) > 5 and "drive" in a[5]})
        note = (f"Spectra Premium {pn} ({LABEL[cat]}) is listed for each of these vehicles on that "
                f"vehicle's own catalog page; aftermarket application data, not the carmaker's catalog. "
                "Match the engine" + (" and the body style" if bodies else "") +
                (" and the drivetrain (" + "/".join(d.upper() for d in drives) + ")" if drives else "") +
                ". Only the years shown were checked.")
        groups.append({"id": f"am:spp:{cat}:{pn}", "cat": cat, "tier": "likely", "src": "aftermarket",
                       "label": "Spectra Premium application list", "unit": pn, "apps": apps,
                       "cross_model": len(models) > 1, "body_gated": bool(bodies), "drive_gated": bool(drives),
                       "oe_refs": sorted(oe_by_unit[(cat, pn)]),
                       "retrieved": unit_ret[(cat, pn)], "note": note})
    doc = {"schema": SCHEMA, "src": "aftermarket", "site": SITE, "raw": src, "tier": "likely",
           "groups": groups,
           "summary": {"vehicle_records": len(seen_vid), "groups": len(groups),
                       "cross_model_groups": sum(g["cross_model"] for g in groups),
                       "apps": sum(len(g["apps"]) for g in groups),
                       "by_cat": dict(Counter(g["cat"] for g in groups)),
                       "cross_model_by_cat": dict(Counter(g["cat"] for g in groups if g["cross_model"])),
                       "refused": dict(sorted(refused.items())),
                       "split_keys_dropped": dict(split)},
           "refused_clauses": dict(refused_clause.most_common(60)),
           "unmapped_models": dict(unmapped.most_common()),
           "lines_seen": dict(lines_seen.most_common())}
    doc["sha256"] = hashlib.sha256(json.dumps(groups, sort_keys=True).encode()).hexdigest()
    return doc


def report_md(doc: dict) -> str:
    s = doc["summary"]
    out = [f"# Spectra Premium aftermarket groups (not shipped)", "", f"raw: {doc['raw']}", "",
           f"- vehicle records: {s['vehicle_records']}", f"- groups: {s['groups']} "
           f"(cross-model {s['cross_model_groups']}), app rows {s['apps']}",
           f"- by category: {s['by_cat']}", f"- cross-model by category: {s['cross_model_by_cat']}",
           f"- refused: {s['refused']}", f"- split keys dropped: {s['split_keys_dropped']}", "",
           "## Refused note clauses (top)", ""]
    out += [f"- {n} x {c}" for c, n in doc["refused_clauses"].items()]
    out += ["", "## Unmapped models (top 40)", ""]
    out += [f"- {n} x {m}" for m, n in list(doc["unmapped_models"].items())[:40]]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw")
    ap.add_argument("--raw-ref")
    ap.add_argument("--out", default=str(HERE / "curated" / "spectrapremium.json"))
    ap.add_argument("--report", default=str(HERE / "curated" / "spectrapremium.md"))
    a = ap.parse_args(argv)
    recs, src = load_raw(a.raw, a.raw_ref)
    lot = None
    inv_p = GA.REPO / "docs" / "data" / "inventory_live.json"
    if inv_p.exists():
        inv = json.loads(inv_p.read_text())
        F = {k: i for i, k in enumerate(inv["fields"])}
        lot = {(v[F["make"]] or "", v[F["model"]] or "") for v in inv["vehicles"]}
    doc = build(recs, GA.Names(lot), src)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    Path(a.report).write_text(report_md(doc))
    print(json.dumps(doc["summary"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
