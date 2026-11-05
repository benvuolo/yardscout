#!/usr/bin/env python3
"""Manual-transmission detection, step 1: the baseline.

Builds, offline, from the files the scraper publishes:

  ground_truth.jsonl     one line per car on the lots whose transmission is
                         KNOWN (published extras trans non-empty), with the
                         fields a rule needs and the cache-only vPIC fields.
  baseline_summary.json  per-make counts: cars, known transmission (by source
                         and class), confirmed manuals, and the opportunity
                         (cars with NO transmission info) split by why.

Inputs (all committed in docs/data/):
  inventory_live.json    333k cars (schema v2 rows + vpic side table)
  vehicle_extras.json    {id: [photo, color, engine, trans, transSrc]}
  vin_decodes.json.gz    the vPIC decode cache backup (compact payloads)

"Known" means exactly what the app's isConfirmedManual reads: the extras
`trans` text, from the yard listing (transSrc "listing") or the VIN decode
("vin"). Class "manual" is the app's own test: /manual/i and not
/automated/i. Nothing here infers a transmission.

Run:  python3 -I scraper/manual_detect/build_baseline.py
"""

import gzip
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DATA = REPO / "docs" / "data"
sys.path.insert(0, str(HERE.parent))
import junkyard_scraper as js  # noqa: E402  (_correct_vpic, normalize_make)


def trans_class(t: str) -> str:
    """Bucket a transmission text. 'manual' matches app.js isConfirmedManual."""
    s = (t or "").strip()
    if not s:
        return ""
    if re.search(r"manual", s, re.I) and not re.search(r"automated", s, re.I):
        return "manual"
    if re.search(r"automated manual|\bAMT\b", s, re.I):
        return "amt"
    if re.search(r"dual.clutch|\bDCT\b", s, re.I):
        return "dct"
    if re.search(r"continuously variable|\bcvt\b", s, re.I):
        return "cvt"
    if re.search(r"automatic", s, re.I):
        return "automatic"
    return "other"


_SPD = re.compile(r"(\d+)-spd")
_ENG = re.compile(r"(?:(\d+(?:\.\d+)?)L)?\s*(?:(\d+)-cyl)?\s*(.*)$")


def parse_engine(e: str) -> tuple[float | None, int | None, str]:
    """'3.5L 6-cyl' / '2.0L 4-cyl Diesel' -> (3.5, 6, 'Diesel')."""
    m = _ENG.match((e or "").strip())
    if not m:
        return None, None, ""
    d = float(m.group(1)) if m.group(1) else None
    c = int(m.group(2)) if m.group(2) else None
    return d, c, (m.group(3) or "").strip()


def main() -> int:
    inv = json.loads((DATA / "inventory_live.json").read_text())
    extras_doc = json.loads((DATA / "vehicle_extras.json").read_text())
    extras = extras_doc["extras"]
    cache = json.loads(gzip.decompress((DATA / "vin_decodes.json.gz").read_bytes()))
    cache_exported = cache.pop("_exportedAt", "")
    cache = {k: v for k, v in cache.items() if isinstance(v, dict)}

    fields = inv["fields"]
    fi = {f: i for i, f in enumerate(fields)}
    yards = inv["yards"]
    vpic_side = inv.get("vpic") or {}

    per_make: dict[str, Counter] = defaultdict(Counter)
    totals = Counter()
    vin_vs_listing = Counter()          # listing-sourced cars that ALSO have a vPIC trans
    vin_vs_listing_disagree = []
    extras_vs_cache = Counter()         # published vin-sourced trans vs corrected cache
    gt_lines = []
    seen_vins_gt = Counter()

    for ri, row in enumerate(inv["vehicles"]):
        vid = str(row[fi["id"]])
        vin = (row[fi["vin"]] or "").strip().upper()
        year = row[fi["year"]]
        make = row[fi["make"]] or ""
        model = row[fi["model"]] or ""
        yard = yards[row[fi["yard"]]][0] if isinstance(row[fi["yard"]], int) else ""
        ex = extras.get(vid) or []
        ex = list(ex) + [""] * (5 - len(ex))
        trans = ex[3] or ""
        src = (ex[4] or ("vin" if trans else "")) if trans else ""
        engine_pub = ex[2] or ""

        raw = cache.get(vin) if vin else None
        dec = js._correct_vpic(raw, vin) if raw else None
        side = vpic_side.get(str(ri)) or ["", "", "", "", ""]

        c = per_make[make]
        c["cars"] += 1
        totals["cars"] += 1
        if vin:
            c["with_vin"] += 1
        tc = trans_class(trans)

        cache_trans = (dec or {}).get("transmission", "") if dec else ""
        if trans:
            c["known"] += 1
            c[f"known_{src}"] += 1
            c[f"class_{tc}"] += 1
            if tc == "manual":
                c[f"manual_{src}"] += 1
            totals["known"] += 1
            totals[f"known_{src}"] += 1
            totals[f"class_{tc}"] += 1
            if tc == "manual":
                totals[f"manual_{src}"] += 1
            if src == "vin" and dec is not None:
                extras_vs_cache["agree" if cache_trans == trans else "differ"] += 1
            elif src == "vin":
                extras_vs_cache["not_in_cache_backup"] += 1
            if src == "listing" and cache_trans:
                same = trans_class(cache_trans) == tc
                vin_vs_listing["agree" if same else "disagree"] += 1
                if not same:
                    vin_vs_listing_disagree.append(
                        {"vin": vin, "year": year, "make": make, "model": model,
                         "listing": trans, "vin_trans": cache_trans, "yard": yard})
        else:
            # Opportunity: no transmission text at all. Why?
            if not vin:
                why = "no_vin"
            elif raw is None:
                why = "vin_not_in_cache"
            elif "transmission" not in raw:
                why = "cache_old_schema"      # payload predates engine/trans fields
            else:
                why = "vpic_blank"            # vPIC decoded; TransmissionStyle empty
            c["unknown"] += 1
            c[f"unknown_{why}"] += 1
            totals["unknown"] += 1
            totals[f"unknown_{why}"] += 1
            continue

        disp, cyl, fuel = parse_engine((dec or {}).get("engine", "") or engine_pub)
        spd = _SPD.search(trans)
        line = {
            "id": vid,
            "vin": vin,
            "year": year,
            "make": make,
            "model": model,
            "trim": (dec or {}).get("trim", "") if dec else side[0],
            "series": (dec or {}).get("series", "") if dec else side[2],
            "trimQuality": (dec or {}).get("trimQuality", "") if dec else side[1],
            "body": (dec or {}).get("bodyClass", "") if dec else "",
            "engine": engine_pub,
            "displL": disp,
            "cyl": cyl,
            "fuel": fuel,
            "drive": (dec or {}).get("driveType", "") if dec else side[3],
            "trans": trans,
            "transClass": tc,
            "speeds": int(spd.group(1)) if spd else None,
            "source": src,
            "vinTrans": cache_trans,
            "vpicMake": (dec or {}).get("make", "") if dec else "",
            "vpicModel": (dec or {}).get("model", "") if dec else "",
            "vpicYear": (dec or {}).get("modelYear", "") if dec else "",
            "inCache": dec is not None,
            "yard": yard,
        }
        if vin:
            seen_vins_gt[vin] += 1
        gt_lines.append(line)

    gt_lines.sort(key=lambda d: (d["make"], d["model"], d["year"] or 0, d["vin"], d["id"]))
    with open(HERE / "ground_truth.jsonl", "w") as f:
        for d in gt_lines:
            f.write(json.dumps(d, separators=(",", ":")) + "\n")

    def mk_row(m: str, c: Counter) -> dict:
        return {
            "make": m,
            "cars": c["cars"],
            "with_vin": c["with_vin"],
            "known": c["known"],
            "known_vin": c["known_vin"],
            "known_listing": c["known_listing"],
            "manual": c["class_manual"],
            "manual_vin": c["manual_vin"],
            "manual_listing": c["manual_listing"],
            "automatic": c["class_automatic"],
            "cvt": c["class_cvt"],
            "dct": c["class_dct"],
            "amt": c["class_amt"],
            "other": c["class_other"],
            "unknown": c["unknown"],
            "unknown_vpic_blank": c["unknown_vpic_blank"],
            "unknown_cache_old_schema": c["unknown_cache_old_schema"],
            "unknown_vin_not_in_cache": c["unknown_vin_not_in_cache"],
            "unknown_no_vin": c["unknown_no_vin"],
        }

    rows = [mk_row(m, c) for m, c in per_make.items()]
    rows.sort(key=lambda r: -r["cars"])
    # Old-schema cache payloads among live VINs: a fresh vPIC decode of the
    # same VIN would carry TransmissionStyle where vPIC has one.
    live_vins = {(r[fi["vin"]] or "").strip().upper() for r in inv["vehicles"]} - {""}
    summary = {
        "inputs": {
            "inventory_live.json": inv.get("scrapedAt"),
            "vehicle_extras.json": extras_doc.get("scrapedAt"),
            "vin_decodes.json.gz": {"exportedAt": cache_exported, "entries": len(cache),
                                    "with_transmission_key": sum(1 for v in cache.values() if "transmission" in v),
                                    "with_nonempty_transmission": sum(1 for v in cache.values() if v.get("transmission"))},
        },
        "totals": dict(totals),
        "live_unique_vins": len(live_vins),
        "live_vins_in_cache_backup": sum(1 for v in live_vins if v in cache),
        "ground_truth_lines": len(gt_lines),
        "ground_truth_unique_vins": len(seen_vins_gt),
        "ground_truth_duplicate_vins": sum(1 for n in seen_vins_gt.values() if n > 1),
        "published_vin_trans_vs_cache": dict(extras_vs_cache),
        "listing_vs_vin_where_both": dict(vin_vs_listing),
        "listing_vs_vin_disagreements": vin_vs_listing_disagree[:50],
        "per_make": rows,
    }
    (HERE / "baseline_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("per_make", "listing_vs_vin_disagreements")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
