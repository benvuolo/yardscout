#!/usr/bin/env python3
"""Manual-transmission detection, step 1: profile the EPA fueleconomy.gov
vehicles data against our feed's make/model names.

Reads   scraper/manual_detect/epa/vehicles.csv   (raw download, gitignored;
        source https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip)
        docs/data/inventory_live.json
        docs/data/vin_decodes.json.gz (vPIC model names, engine, drive)
        scraper/manual_detect/ground_truth.jsonl (preview cross-check)
Writes  scraper/manual_detect/epa_profile.json

What it measures (nothing here is a rule):
  * the transmission-relevant columns and their value vocabularies;
  * how our feed make names map to EPA make names;
  * how far our feed model names (and vPIC model names) match EPA model /
    baseModel names, car-weighted, and by which kind of name match;
  * the largest unmatched feed models;
  * a SIZE PREVIEW ONLY of the EPA "sole offering" track: cars whose
    year/make/model + displacement/cylinders (+ drive when vPIC has it) EPA
    lists with manual transmissions only, and how those cells look against
    the known-transmission cars. Name matching here is heuristic and
    unvalidated; a real rule needs its own scope, citation and validation.

Run:  python3 -I scraper/manual_detect/epa_profile.py
"""

import csv
import gzip
import json
import re
import sys
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
EPA_CSV = HERE / "epa" / "vehicles.csv"

RELEVANT = ["id", "year", "make", "model", "baseModel", "trany", "trans_dscr",
            "displ", "cylinders", "drive", "eng_dscr", "VClass", "atvType",
            "fuelType", "fuelType1", "tCharger", "sCharger", "startStop",
            "mfrCode", "engId", "evMotor", "createdOn", "modifiedOn"]

# EPA model names carry drive/body suffixes our feed never has.
_EPA_STRIP = re.compile(
    r"\b(2wd|4wd|awd|fwd|rwd|4x4|4x2|pickup|cab\s*chassis|chassis\s*cab|"
    r"wagon|van|ffv|cng|lpg|conversion)\b", re.I)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower().replace("&", "and"))


def epa_stripped(s: str) -> str:
    return norm(_EPA_STRIP.sub(" ", s or ""))


def trany_class(t: str) -> str:
    t = t or ""
    if t.startswith("Manual"):
        return "manual"
    if "(AM" in t:
        return "amt"            # automated manual (EPA puts DCTs here too)
    if "(AV" in t or "variable gear" in t:
        return "cvt"
    if t.startswith("Automatic"):
        return "automatic"
    return "unknown" if not t else "other"


# vPIC DriveType -> the EPA drive values it can correspond to.
_DRIVE_MAP = {
    "fwd": {"Front-Wheel Drive", "2-Wheel Drive"},
    "rwd": {"Rear-Wheel Drive", "2-Wheel Drive"},
    "4x2": {"Front-Wheel Drive", "Rear-Wheel Drive", "2-Wheel Drive"},
    "awd": {"All-Wheel Drive", "4-Wheel or All-Wheel Drive", "4-Wheel Drive",
            "Part-time 4-Wheel Drive"},
    "4wd": {"4-Wheel Drive", "4-Wheel or All-Wheel Drive", "Part-time 4-Wheel Drive",
            "All-Wheel Drive"},
}


def vpic_drive_key(d: str) -> str:
    d = (d or "").lower()
    if not d or "," in d:
        return ""                       # blank, or a list of options
    for k in ("fwd", "rwd", "awd", "4wd", "4x2"):
        if d.startswith(k):
            return k
    return ""


def epa_keys(r: dict) -> list[tuple[str, str]]:
    """(level, key) pairs an EPA row answers to, strongest first."""
    out = [("exact", r["model"].strip().lower()),
           ("norm", norm(r["model"])),
           ("stripped", epa_stripped(r["model"])),
           ("baseModel", norm(r["baseModel"]))]
    # "Caravan/Grand Caravan 2WD", "Liberty/Cherokee 4WD", "Legacy/Outback".
    for part in re.split(r"/", r["model"]):
        out.append(("slash", epa_stripped(part)))
    for part in re.split(r"/", r["baseModel"]):
        out.append(("slash", norm(part)))
    # "Legacy AWD (incl. Outback)": drop the parenthetical.
    out.append(("paren", epa_stripped(re.sub(r"\(.*?\)", " ", r["model"]))))
    return [(lv, k) for lv, k in out if k]


def feed_keys(make: str, model: str) -> list[tuple[str, str]]:
    keys = [("exact", model.strip().lower()), ("norm", norm(model))]
    n = norm(model)
    mk = norm(make)
    if mk and n.startswith(mk) and len(n) > len(mk):
        keys.append(("alias", n[len(mk):]))          # Mazda3 -> 3, Mazda6 -> 6
    m = re.match(r"^(.*?)(1500|2500|3500)$", n)
    if m and m.group(1):                              # GM: Silverado 1500 -> Silverado C15/K15
        base, cls = m.group(1), m.group(2)[:2]
        keys += [("alias", base + "c" + cls), ("alias", base + "k" + cls), ("alias", base + cls)]
    return [(lv, k) for lv, k in keys if k]


LEVEL_ORDER = ["exact", "norm", "stripped", "baseModel", "slash", "paren", "alias"]


def main() -> int:
    if not EPA_CSV.exists():
        print(f"missing {EPA_CSV}; download vehicles.csv.zip first", file=sys.stderr)
        return 2
    with open(EPA_CSV, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        all_cols = list(rdr.fieldnames or [])
        epa = list(rdr)

    vocab = {}
    for col in ["trany", "trans_dscr", "drive", "VClass", "atvType", "fuelType",
                "tCharger", "sCharger", "startStop"]:
        c = Counter(r[col] for r in epa)
        vocab[col] = {"distinct": len(c), "top": c.most_common(45)}
    vocab["trany_class"] = Counter(trany_class(r["trany"]) for r in epa).most_common()
    vocab["eng_dscr"] = {"distinct": len({r["eng_dscr"] for r in epa}),
                         "top": Counter(r["eng_dscr"] for r in epa).most_common(30)}
    years = Counter(r["year"] for r in epa)

    # --- indexes ---------------------------------------------------------
    epa_makes = {}
    for r in epa:
        epa_makes.setdefault(r["make"].lower(), r["make"])
    MAKE_ALIAS = {"amc": "american motors corporation"}
    # (year, make_lower, key) -> {row index: best level}
    idx: dict[tuple[int, str, str], dict[int, str]] = defaultdict(dict)
    ym_seen = set()
    for i, r in enumerate(epa):
        try:
            y = int(r["year"])
        except ValueError:
            continue
        mk = r["make"].lower()
        ym_seen.add((y, mk))
        for lv, k in epa_keys(r):
            slot = idx[(y, mk, k)]
            if i not in slot or LEVEL_ORDER.index(lv) < LEVEL_ORDER.index(slot[i]):
                slot[i] = lv

    @lru_cache(maxsize=None)
    def epa_rows_for(year: int, make: str, model: str) -> tuple[str, tuple[int, ...]]:
        """(best match level, indexes of ALL EPA rows matching by any key).
        The union matters: 2004 Xterra is 'Xterra 2WD' (4-cyl, manual only)
        AND 'Xterra V6 2WD'; 2007 G6 3.9 is 'G6' (manual) AND 'G6 GT/GTP
        Convertible' (automatic). Taking only the strongest name would
        manufacture false 'manual only' cells."""
        mk = MAKE_ALIAS.get(make.lower(), make.lower())
        if (year, mk) not in ym_seen:
            return ("no_make_year", ())
        hits: dict[int, str] = {}
        for flv, k in feed_keys(make, model):
            for i, elv in idx.get((year, mk, k), {}).items():
                lv = flv if flv == "alias" else elv
                if i not in hits or LEVEL_ORDER.index(lv) < LEVEL_ORDER.index(hits[i]):
                    hits[i] = lv
        if not hits:
            return ("none", ())
        best = min(hits.values(), key=LEVEL_ORDER.index)
        return (best, tuple(sorted(hits)))

    inv = json.loads((REPO / "docs" / "data" / "inventory_live.json").read_text())
    fi = {f: i for i, f in enumerate(inv["fields"])}
    cache = json.loads(gzip.decompress((REPO / "docs" / "data" / "vin_decodes.json.gz").read_bytes()))

    def year_of(v) -> int:
        return int(v) if str(v).isdigit() else 0

    groups = Counter()
    vgroups = Counter()
    for row in inv["vehicles"]:
        groups[(year_of(row[fi["year"]]), row[fi["make"]] or "", row[fi["model"]] or "")] += 1
        vin = (row[fi["vin"]] or "").upper()
        d = cache.get(vin) if vin else None
        if isinstance(d, dict) and d.get("make") and str(d.get("modelYear", "")).isdigit():
            vgroups[(int(d["modelYear"]), d["make"].title(), d.get("model", ""))] += 1

    def coverage(gs: Counter) -> tuple[dict, list]:
        lvl = Counter()
        unmatched = Counter()
        pre84 = 0
        for (y, mk, md), n in gs.items():
            if y < 1984:
                pre84 += n
                continue
            level, _ = epa_rows_for(y, mk, md)
            lvl[level] += n
            if level in ("none", "no_make_year"):
                unmatched[(mk, md)] += n
        tot = sum(lvl.values())
        matched = sum(v for k, v in lvl.items() if k not in ("none", "no_make_year"))
        out = {"cars_1984_plus": tot, "cars_pre_1984": pre84,
               "by_level": dict(lvl.most_common()),
               "matched": matched,
               "matched_share": round(matched / tot, 4) if tot else 0}
        return out, [{"make": a, "model": b, "cars": n} for (a, b), n in unmatched.most_common(60)]

    feed_cov, feed_unmatched = coverage(groups)
    vpic_cov, vpic_unmatched = coverage(vgroups)

    feed_makes = Counter()
    for (y, mk, md), n in groups.items():
        feed_makes[mk] += n
    make_map = []
    for mk, n in feed_makes.most_common():
        k = MAKE_ALIAS.get(mk.lower(), mk.lower())
        make_map.append({"feed": mk, "epa": epa_makes.get(k, ""), "cars": n})

    top_models = Counter()
    years_of: dict[tuple[str, str], list[int]] = defaultdict(list)
    for (y, mk, md), n in groups.items():
        top_models[(mk, md)] += n
        if y >= 1984:
            years_of[(mk, md)].append(y)
    examples = []
    for (mk, md), n in top_models.most_common(60):
        yrs = sorted(years_of[(mk, md)])
        probe_year = yrs[len(yrs) // 2] if yrs else 0
        level, hit = epa_rows_for(probe_year, mk, md)
        examples.append({"feed": f"{mk} | {md}", "cars": n, "probe_year": probe_year,
                         "level": level,
                         "epa_models": sorted({epa[i]["model"] for i in hit})[:8],
                         "epa_baseModels": sorted({epa[i]["baseModel"] for i in hit})[:4]})

    # --- size preview of the sole-offering track (NOT a rule) ------------
    eng_re = re.compile(r"(\d+(?:\.\d+)?)L(?:\s+(\d+)-cyl)?")

    def cell_for(year: int, make: str, model: str, vin: str) -> tuple[str, str]:
        """(state, cell label). state: manual_only | mixed | no_manual |
        no_engine | engine_not_in_epa | unmatched."""
        level, hit = epa_rows_for(year, make, model)
        if not hit:
            return ("unmatched", "")
        d = cache.get(vin) if vin else None
        m = eng_re.match((d or {}).get("engine", "")) if isinstance(d, dict) else None
        if not m:
            return ("no_engine", "")
        displ = float(m.group(1))
        cyl = m.group(2)
        sub = [epa[i] for i in hit if epa[i]["displ"]
               and abs(float(epa[i]["displ"]) - displ) < 0.051
               and (not cyl or epa[i]["cylinders"] == cyl)]
        dk = vpic_drive_key((d or {}).get("driveType", ""))
        if dk:
            sub = [r for r in sub if not r["drive"] or r["drive"] in _DRIVE_MAP[dk]]
        if not sub:
            return ("engine_not_in_epa", "")
        sc = {trany_class(r["trany"]) for r in sub}
        label = f"{year} {make} {model} {displ}L/{cyl or '?'}cyl{('/' + dk) if dk else ''}"
        if sc == {"manual"}:
            return ("manual_only", label)
        if "manual" in sc:
            return ("mixed", label)
        return ("no_manual", label)

    preview = Counter()
    preview_cells = Counter()
    preview_cells_unknown = Counter()
    per_make_manual_only = Counter()
    for row in inv["vehicles"]:
        y = year_of(row[fi["year"]])
        if y < 1984:
            preview["pre_1984"] += 1
            continue
        mk, md = row[fi["make"]] or "", row[fi["model"]] or ""
        vin = (row[fi["vin"]] or "").upper()
        state, label = cell_for(y, mk, md, vin)
        preview[state] += 1
        if state == "manual_only":
            preview_cells[label] += 1
            per_make_manual_only[mk] += 1

    # Cross-check the preview cells against the known-transmission cars.
    gt_check = Counter()
    gt_disagree = Counter()
    gt_path = HERE / "ground_truth.jsonl"
    if gt_path.exists():
        with open(gt_path) as f:
            for line in f:
                g = json.loads(line)
                if g["transClass"] not in ("manual", "automatic", "cvt", "dct", "amt"):
                    continue
                y = year_of(g["year"])
                if y < 1984:
                    continue
                state, label = cell_for(y, g["make"], g["model"], g["vin"])
                is_man = g["transClass"] == "manual"
                gt_check[f"{state}|{'manual' if is_man else 'not_manual'}"] += 1
                if state == "manual_only" and not is_man:
                    gt_disagree[f"{label} -> {g['trans']}"] += 1

    hd_re = re.compile(r"(\b[FE]-?[2-5]50\b|\b(2500|3500|4500)\b|super duty|\bHD\b)", re.I)
    hd = Counter()
    for (y, mk, md), n in groups.items():
        if hd_re.search(md):
            hd[(mk, md)] += n

    out = {
        "source": {"url": "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip",
                   "rows": len(epa), "columns": len(all_cols),
                   "years": [min(years), max(years)], "rows_per_year": dict(sorted(years.items()))},
        "all_columns": all_cols,
        "relevant_columns": RELEVANT,
        "vocab": vocab,
        "make_map": make_map,
        "feed_model_match": feed_cov,
        "feed_unmatched_top": feed_unmatched,
        "vpic_model_match": vpic_cov,
        "vpic_unmatched_top": vpic_unmatched,
        "name_examples": examples,
        "sole_offering_size_preview": dict(preview),
        "sole_offering_preview_by_make": dict(per_make_manual_only.most_common()),
        "sole_offering_preview_top_cells": [{"cell": k, "cars": n} for k, n in preview_cells.most_common(60)],
        "sole_offering_preview_vs_ground_truth": dict(sorted(gt_check.items())),
        "sole_offering_preview_gt_disagreements": [{"cell": k, "cars": n} for k, n in gt_disagree.most_common(40)],
        "heavy_duty_feed_models": [{"make": a, "model": b, "cars": n} for (a, b), n in hd.most_common(25)],
        "heavy_duty_cars": sum(hd.values()),
    }
    (HERE / "epa_profile.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in ("feed_model_match", "vpic_model_match",
                                          "sole_offering_size_preview",
                                          "sole_offering_preview_vs_ground_truth",
                                          "heavy_duty_cars")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
