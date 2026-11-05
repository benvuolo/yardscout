#!/usr/bin/env python3
"""Manual-transmission detection, step 1: profile the EPA fueleconomy.gov
vehicles data against our feed's make/model names.

Reads   scraper/manual_detect/epa/vehicles.csv   (raw download, gitignored;
        source https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip)
        docs/data/inventory_live.json
        docs/data/vin_decodes.json.gz (vPIC model names, engine text)
Writes  scraper/manual_detect/epa_profile.json

What it measures (nothing here is a rule):
  * the transmission-relevant columns and their value vocabularies;
  * how our feed make names map to EPA make names;
  * how far our feed model names (and vPIC model names) match EPA model /
    baseModel names, by successively looser normalizations, car-weighted;
  * the largest unmatched feed models;
  * a SIZE PREVIEW ONLY of the EPA "sole offering" track: cars whose
    year/make/model(+displacement/cylinders) EPA lists with manual
    transmissions only. Matching here is name-level and unvalidated.

Run:  python3 -I scraper/manual_detect/epa_profile.py
"""

import csv
import gzip
import json
import re
import sys
from collections import Counter, defaultdict
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
    r"wagon|van|ffv|cng|lpg|conversion|long\s*range|ld|hd)\b", re.I)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def epa_stripped(s: str) -> str:
    return norm(_EPA_STRIP.sub(" ", s or ""))


def trany_class(t: str) -> str:
    t = t or ""
    if t.startswith("Manual"):
        return "manual"
    if "(AM" in t:
        return "amt"            # automated manual (incl. DCTs; EPA lumps them)
    if "(AV" in t or "variable gear" in t:
        return "cvt"
    if t.startswith("Automatic"):
        return "automatic"
    return "unknown" if not t else "other"


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
    # (year, make_lower) -> list of rows
    by_ym: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for r in epa:
        try:
            by_ym[(int(r["year"]), r["make"].lower())].append(r)
        except ValueError:
            pass
    MAKE_ALIAS = {"amc": "american motors corporation"}

    def epa_rows_for(year: int, make: str, model: str) -> tuple[str, list[dict]]:
        """(match level, matching EPA rows) for one feed year/make/model."""
        mk = make.lower()
        mk = MAKE_ALIAS.get(mk, mk)
        pool = by_ym.get((year, mk), [])
        if not pool and mk == "mini":
            pool = by_ym.get((year, "mini"), [])
        if not pool:
            return ("no_make_year", [])
        m_ci = model.strip().lower()
        hit = [r for r in pool if r["model"].strip().lower() == m_ci]
        if hit:
            return ("exact", hit)
        n = norm(model)
        if not n:
            return ("none", [])
        hit = [r for r in pool if norm(r["model"]) == n]
        if hit:
            return ("norm", hit)
        hit = [r for r in pool if epa_stripped(r["model"]) == n]
        if hit:
            return ("stripped", hit)
        hit = [r for r in pool if norm(r["baseModel"]) == n]
        if hit:
            return ("baseModel", hit)
        hit = [r for r in pool if epa_stripped(r["model"]).startswith(n) and len(n) >= 3]
        if hit:
            return ("prefix", hit)
        return ("none", [])

    inv = json.loads((REPO / "docs" / "data" / "inventory_live.json").read_text())
    fi = {f: i for i, f in enumerate(inv["fields"])}
    groups = Counter()
    for row in inv["vehicles"]:
        y = row[fi["year"]] or 0
        groups[(int(y) if str(y).isdigit() else 0, row[fi["make"]] or "", row[fi["model"]] or "")] += 1

    # vPIC model names, for the same comparison (from the decode cache).
    cache = json.loads(gzip.decompress((REPO / "docs" / "data" / "vin_decodes.json.gz").read_bytes()))
    vgroups = Counter()
    for row in inv["vehicles"]:
        vin = (row[fi["vin"]] or "").upper()
        d = cache.get(vin) if vin else None
        if isinstance(d, dict) and d.get("make") and d.get("modelYear", "").isdigit():
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
        out = {"cars_1984_plus": tot, "cars_pre_1984": pre84,
               "by_level": {k: v for k, v in lvl.most_common()},
               "matched_share": round(sum(v for k, v in lvl.items() if k not in ("none", "no_make_year")) / tot, 4) if tot else 0}
        return out, [{"make": a, "model": b, "cars": n} for (a, b), n in unmatched.most_common(60)]

    feed_cov, feed_unmatched = coverage(groups)
    vpic_cov, vpic_unmatched = coverage(vgroups)

    # Make-name map, feed -> EPA.
    feed_makes = Counter()
    for (y, mk, md), n in groups.items():
        feed_makes[mk] += n
    make_map = []
    for mk, n in feed_makes.most_common():
        k = MAKE_ALIAS.get(mk.lower(), mk.lower())
        make_map.append({"feed": mk, "epa": epa_makes.get(k, ""), "cars": n})

    # Examples of how names differ, for the top feed models.
    examples = []
    top_models = Counter()
    for (y, mk, md), n in groups.items():
        top_models[(mk, md)] += n
    for (mk, md), n in top_models.most_common(40):
        yrs = sorted({y for (y, a, b) in groups if a == mk and b == md and y >= 1984})
        probe_year = yrs[len(yrs) // 2] if yrs else 0
        level, hit = epa_rows_for(probe_year, mk, md)
        examples.append({"feed": f"{mk} {md}", "cars": n, "probe_year": probe_year,
                         "level": level,
                         "epa_models": sorted({r["model"] for r in hit})[:8],
                         "epa_baseModels": sorted({r["baseModel"] for r in hit})[:4]})

    # --- size preview of the sole-offering track (NOT a rule) ------------
    # Engine displacement/cylinders come from the vPIC cache engine text.
    eng_re = re.compile(r"(\d+(?:\.\d+)?)L(?:\s+(\d+)-cyl)?")
    preview = Counter()
    preview_models = Counter()
    for row in inv["vehicles"]:
        y = row[fi["year"]] or 0
        if not str(y).isdigit() or int(y) < 1984:
            continue
        y = int(y)
        mk, md = row[fi["make"]] or "", row[fi["model"]] or ""
        level, hit = epa_rows_for(y, mk, md)
        if not hit:
            continue
        classes = {trany_class(r["trany"]) for r in hit}
        preview["matched"] += 1
        if classes == {"manual"}:
            preview["model_level_manual_only"] += 1
            preview_models[(y, mk, md, "model")] += 1
            continue
        vin = (row[fi["vin"]] or "").upper()
        d = cache.get(vin) if vin else None
        m = eng_re.match((d or {}).get("engine", "")) if isinstance(d, dict) else None
        if not m:
            continue
        displ = float(m.group(1))
        cyl = m.group(2)
        sub = [r for r in hit if r["displ"] and abs(float(r["displ"]) - displ) < 0.051
               and (not cyl or r["cylinders"] == cyl)]
        if not sub:
            preview["engine_not_in_epa_rows"] += 1
            continue
        preview["engine_matched"] += 1
        sc = {trany_class(r["trany"]) for r in sub}
        if sc == {"manual"}:
            preview["engine_level_manual_only"] += 1
            preview_models[(y, mk, md, f"{displ}L/{cyl}")] += 1
        elif "manual" in sc:
            preview["engine_level_mixed"] += 1
        else:
            preview["engine_level_no_manual"] += 1

    # Heavy-duty models EPA does not list (GVWR > 8,500 lb / 10,000 lb MDPV).
    hd_re = re.compile(r"(\b[FE]-?[2-5]50\b|\b(2500|3500|4500)\b|super duty|\bHD\b|express 3500|savana 3500)", re.I)
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
        "sole_offering_preview_top": [
            {"year": a, "make": b, "model": c, "level": d, "cars": n}
            for (a, b, c, d), n in preview_models.most_common(40)],
        "heavy_duty_feed_models": [{"make": a, "model": b, "cars": n} for (a, b), n in hd.most_common(25)],
        "heavy_duty_cars": sum(hd.values()),
    }
    (HERE / "epa_profile.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in ("feed_model_match", "vpic_model_match",
                                          "sole_offering_size_preview", "heavy_duty_cars")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
