#!/usr/bin/env python3
"""Verified-fits / VIN-decoding system audit (owner request, 2026-10-26).

Replicates the client's exact tiering logic (docs/app.js pfRunSearch, engine
kind) over the live inventory to answer:

  (a) VIN publication / decode / engine-confirmation rates by chain
  (b) decode backlog vs VPIC_MAX_PER_RUN (authoritative number is the CI log;
      this reports the local approximation from the committed gz export)
  (c) Verified vs Likely fraction for the researched engine-kind categories
      (alternator, starter, engine-assembly) and WHY pairs stop at Likely
  (d) model-year distribution of Verified pairs — the 2016+ catalog cliff

Seeker population proxy: the live inventory itself (a car in a yard is as
good a proxy as any for the cars people drive). Pairs are
(seeker vehicle, donor vehicle) within one engine family, weighted by
vehicle counts. Engine-denied donors (decode contradicts the family) are
EXCLUDED rows in the app, not Likely — reported separately.

Usage: python3 scraper/_audit_verified_fits.py [--json out.json]
"""
from __future__ import annotations

import argparse
import collections
import gzip
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "docs" / "data"

_squash_cache: dict[tuple[str, str], str] = {}


def squash(model: str, make: str = "") -> str:
    key = (model, make)
    s = _squash_cache.get(key)
    if s is None:
        s = js._squash_model(model, make) if make else js._squash_model(model)
        _squash_cache[key] = s
    return s


def app_matches(app: tuple, year: int, make_lc: str, sq_strip: str, sq_raw: str) -> bool:
    """_app_matches with pre-squashed model strings (hot loop)."""
    a_make, a_model, lo, hi = app[0], app[1], app[2], app[3]
    if not (lo <= year <= hi):
        return False
    if make_lc not in (m.lower() for m in a_make.split("|")):
        return False
    am = re.sub(r"[^a-z0-9]", "", a_model.rstrip("*").lower())
    if a_model.endswith("*"):
        return sq_strip.startswith(am) or sq_raw.startswith(am)
    return am in (sq_strip, sq_raw)


def chain_of(yard_name: str) -> str:
    n = yard_name
    if "(Independent)" in n:
        return "Independents"
    if n.startswith("Pick Your Part"):
        return "LKQ Pick Your Part"
    if n.startswith("Pick-n-Pull"):
        return "Pick-n-Pull"
    if n.startswith("Pull-A-Part"):
        return "Pull-A-Part"
    if n.startswith(("Tear-A-Part", "Utah Pic-A-Part")):
        return "Tear-A-Part/UTPAP"
    return "Independents"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    inv = json.loads((DATA / "inventory_live.json").read_text())
    ex = json.loads((DATA / "vehicle_extras.json").read_text())["extras"]
    with gzip.open(DATA / "vin_decodes.json.gz") as f:
        decodes = json.load(f)

    f_idx = {k: i for i, k in enumerate(inv["fields"])}
    I_ID, I_VIN, I_Y, I_MK, I_MD, I_YD = (f_idx[k] for k in
                                          ("id", "vin", "year", "make", "model", "yard"))
    vehicles = inv["vehicles"]
    yards = inv["yards"]
    report: dict = {"scrapedAt": inv["scrapedAt"], "totalVehicles": len(vehicles)}

    # ---------------- (a) VIN / decode / engine rates by chain -------------
    chain_stats: dict[str, dict] = collections.defaultdict(
        lambda: {"vehicles": 0, "vin": 0, "decoded": 0, "engine": 0})
    yard_stats: dict[str, dict] = collections.defaultdict(
        lambda: {"vehicles": 0, "vin": 0})
    for v in vehicles:
        yname = yards[v[I_YD]][0]
        ch = chain_of(yname)
        cs, ys = chain_stats[ch], yard_stats[yname]
        cs["vehicles"] += 1
        ys["vehicles"] += 1
        vin = v[I_VIN] or ""
        has_vin = len(vin) == 17
        if has_vin:
            cs["vin"] += 1
            ys["vin"] += 1
            if vin in decodes:
                cs["decoded"] += 1
        e = ex.get(str(v[I_ID]))
        engine_str = e[2] if e and len(e) > 2 else ""
        liters, _cyl = js._parse_engine_str(engine_str)
        if liters is not None:
            cs["engine"] += 1

    print(f"inventory: {len(vehicles):,} vehicles, scrapedAt {inv['scrapedAt']}")
    print(f"decode-cache gz: {len(decodes):,} VINs "
          f"(committed export — CI cache is a few days ahead)")
    print("\n(a) VIN publication / decode / usable-engine rates by chain")
    print(f"{'chain':24s} {'vehicles':>9} {'VIN%':>7} {'decoded%':>9} {'engine%':>8}")
    for ch, s in sorted(chain_stats.items(), key=lambda t: -t[1]["vehicles"]):
        vin_pct = s["vin"] / s["vehicles"] if s["vehicles"] else 0
        dec_pct = s["decoded"] / s["vin"] if s["vin"] else 0
        eng_pct = s["engine"] / s["vehicles"] if s["vehicles"] else 0
        print(f"{ch:24s} {s['vehicles']:>9,} {vin_pct:>7.1%} {dec_pct:>9.1%} {eng_pct:>8.1%}")
    report["chains"] = dict(chain_stats)

    no_vin_yards = [(y, s) for y, s in yard_stats.items()
                    if s["vehicles"] >= 50 and s["vin"] / s["vehicles"] < 0.02]
    print(f"\nyards publishing (near-)no VINs ({len(no_vin_yards)}):")
    for y, s in sorted(no_vin_yards, key=lambda t: -t[1]["vehicles"]):
        print(f"  {y:55s} {s['vehicles']:>6,} cars, {s['vin']:,} VINs")
    report["noVinYards"] = [
        {"yard": y, "vehicles": s["vehicles"], "vins": s["vin"]}
        for y, s in sorted(no_vin_yards, key=lambda t: -t[1]["vehicles"])]

    # ---------------- (b) backlog (local approximation) --------------------
    inv_vins = {v[I_VIN] for v in vehicles if len(v[I_VIN] or "") == 17}
    backlog_local = len(inv_vins - set(decodes))
    print(f"\n(b) VINs in scan: {len(inv_vins):,}; not in committed gz: "
          f"{backlog_local:,} (CI Actions cache is the authority — see run log)")
    report["backlogVsGz"] = backlog_local
    report["uniqueVins"] = len(inv_vins)

    # ---------------- (c)+(d) pair-tier simulation -------------------------
    # Pre-squash every distinct (make, model) once.
    ymm_counts: collections.Counter = collections.Counter()
    # donor-side per (ymm, engine verdict) counts; verdict in {True, False, None}
    donor_counts: dict[tuple, collections.Counter] = collections.defaultdict(collections.Counter)
    for v in vehicles:
        y, mk, md = v[I_Y] or 0, v[I_MK] or "", v[I_MD] or ""
        ymm_counts[(y, mk, md)] += 1
    # engine verdict depends on the family, so store engine liters/cyl per ymm bucket
    eng_buckets: dict[tuple, collections.Counter] = collections.defaultdict(collections.Counter)
    for v in vehicles:
        y, mk, md = v[I_Y] or 0, v[I_MK] or "", v[I_MD] or ""
        e = ex.get(str(v[I_ID]))
        engine_str = e[2] if e and len(e) > 2 else ""
        is_diesel = bool(engine_str) and "diesel" in engine_str.lower()
        liters, cyl = js._parse_engine_str(engine_str)
        eng_buckets[(y, mk, md)][(is_diesel, liters, cyl)] += 1

    sq_cache: dict[tuple[str, str], tuple[str, str, str]] = {}
    for (y, mk, md) in ymm_counts:
        if (mk, md) not in sq_cache:
            sq_cache[(mk, md)] = (mk.lower(), squash(md, mk), squash(md))

    def verdict_for(key: tuple, fam: dict) -> collections.Counter:
        """Counter {True/False/None: n} for a ymm bucket against a family."""
        out: collections.Counter = collections.Counter()
        spec = fam["engine"]
        for (is_diesel, liters, cyl), n in eng_buckets[key].items():
            if is_diesel:
                out[False] += n
                continue
            if liters is None:
                out[None] += n
                continue
            if not any(abs(liters - want) < 0.05 for want in spec["liters"]):
                out[False] += n
                continue
            want_cyl = spec.get("cyl")
            if cyl is not None and want_cyl is not None and cyl != want_cyl:
                out[False] += n
                continue
            out[True] += n
        return out

    CATS = ["alternator", "starter", "engine-assembly"]
    cat_res: dict[str, dict] = {}
    for cat in CATS:
        tot_pairs = ver_pairs = 0
        excluded_donors = 0  # engine-denied: not shown at all
        reasons: collections.Counter = collections.Counter()
        ver_by_donor_year: collections.Counter = collections.Counter()
        likely_by_donor_year: collections.Counter = collections.Counter()
        donors_total = donors_engine_ok = 0

        for fid, fam in js.ENGINE_FAMILIES.items():
            if cat == "engine-assembly":
                p = {"note": ""}  # every family answers; no years, no vg
            else:
                p = fam["parts"].get(cat)
                if p is None:
                    continue
            years = p.get("years")
            vg = (p.get("verified") or {}).get("groups") if cat != "engine-assembly" else None

            # bucket every matching ymm once
            matches = []  # (key, app, mask) per matching ymm
            for key, n in ymm_counts.items():
                y, mk, md = key
                if years and not (years[0] <= y <= years[1]):
                    continue
                mk_lc, sq_s, sq_r = sq_cache[(mk, md)]
                app = next((a for a in fam["apps"]
                            if app_matches(a, y, mk_lc, sq_s, sq_r)), None)
                if app is None:
                    continue
                mask = 0
                if vg:
                    for gi, g in enumerate(vg):
                        if any(app_matches(sp, y, mk_lc, sq_s, sq_r) for sp in g):
                            mask |= 1 << gi
                matches.append((key, app, mask))
            if not matches:
                continue

            # seekers: (mask, ambig) -> count ; donors: (mask, ambig, engineOk/denied/off) -> count
            seekers: collections.Counter = collections.Counter()
            donors: collections.Counter = collections.Counter()
            donor_year_of: dict = {}
            for key, app, mask in matches:
                n = ymm_counts[key]
                flags = js._app_flags(app)
                ambig = bool(flags.get("ambig"))
                sole = bool(flags.get("sole"))
                seekers[(mask, ambig)] += n
                for verdict, vn in verdict_for(key, fam).items():
                    if verdict is False:
                        donors[("DENIED", key[0])] += vn
                        continue
                    engine_ok = verdict is True or (verdict is None and sole and not ambig)
                    confirmed = verdict is True
                    donors[(mask, ambig, engine_ok, confirmed, key[0])] += vn

            n_seekers = sum(seekers.values())
            for dk, dn in donors.items():
                if dk[0] == "DENIED":
                    excluded_donors += dn
                    continue
                dmask, dambig, engine_ok, confirmed, dyear = dk
                donors_total += dn
                if engine_ok:
                    donors_engine_ok += dn
                for (smask, sambig), sn in seekers.items():
                    pairs = dn * sn
                    tot_pairs += pairs
                    if cat == "engine-assembly":
                        is_ver = confirmed and not dambig and not sambig
                    else:
                        is_ver = (engine_ok and not dambig and not sambig
                                  and bool(dmask & smask))
                    if is_ver:
                        ver_pairs += pairs
                        ver_by_donor_year[dyear] += pairs
                        continue
                    likely_by_donor_year[dyear] += pairs
                    # non-exclusive reasons
                    if cat == "engine-assembly":
                        if not confirmed:
                            reasons["engine not decode-confirmed"] += pairs
                        if dambig or sambig:
                            reasons["ambiguity flag (seeker or donor)"] += pairs
                        continue
                    if not vg:
                        reasons["no published application list for family+part"] += pairs
                    else:
                        if not engine_ok:
                            reasons["engine unconfirmed (decode silent, model not sole-engine)"] += pairs
                        if dambig or sambig:
                            reasons["ambiguity flag (seeker or donor)"] += pairs
                        if engine_ok and not dambig and not sambig and not (dmask & smask):
                            reasons["published list doesn't span the pair (year/model outside group)"] += pairs

        cat_res[cat] = {
            "totalPairs": tot_pairs, "verifiedPairs": ver_pairs,
            "verifiedPct": ver_pairs / tot_pairs if tot_pairs else 0,
            "excludedDonors": excluded_donors,
            "donorsTotal": donors_total, "donorsEngineOk": donors_engine_ok,
            "reasons": dict(reasons),
            "verByDonorYear": dict(ver_by_donor_year),
            "likelyByDonorYear": dict(likely_by_donor_year),
        }
        print(f"\n(c) {cat}: {tot_pairs:,} seeker×donor pairs in-family; "
              f"Verified {ver_pairs:,} ({ver_pairs / tot_pairs:.1%}), "
              f"Likely {tot_pairs - ver_pairs:,} ({(tot_pairs - ver_pairs) / tot_pairs:.1%})")
        print(f"    donors shown {donors_total:,} (engine-OK {donors_engine_ok:,}); "
              f"engine-denied donors excluded entirely: {excluded_donors:,}")
        print("    why pairs stop at Likely (non-exclusive, share of Likely pairs):")
        lk = tot_pairs - ver_pairs
        for r, n in sorted(reasons.items(), key=lambda t: -t[1]):
            print(f"      {n / lk:>6.1%}  {r}")

    report["categories"] = cat_res

    # ---------------- (d) verified-pair year distribution -------------------
    print("\n(d) Verified-pair share by DONOR model year (alternator + starter):")
    vy: collections.Counter = collections.Counter()
    ly: collections.Counter = collections.Counter()
    for cat in ("alternator", "starter"):
        for y, n in cat_res[cat]["verByDonorYear"].items():
            vy[y] += n
        for y, n in cat_res[cat]["likelyByDonorYear"].items():
            ly[y] += n
    inv_years: collections.Counter = collections.Counter(v[I_Y] or 0 for v in vehicles)
    print(f"{'year':>6} {'ver pairs':>14} {'ver share':>10} {'inventory':>10}")
    for y in sorted(set(vy) | set(ly)):
        tot = vy[y] + ly[y]
        print(f"{y:>6} {vy[y]:>14,} {vy[y] / tot if tot else 0:>10.1%} {inv_years[y]:>10,}")
    tot_v = sum(vy.values())
    v16 = sum(n for y, n in vy.items() if y >= 2016)
    i16 = sum(n for y, n in inv_years.items() if y >= 2016)
    print(f"\n2016+ cliff: {v16 / tot_v:.1%} of Verified pairs have a 2016+ donor, "
          f"but {i16 / sum(inv_years.values()):.1%} of inventory is 2016+")
    report["verifiedPairsByYear"] = dict(vy)
    report["pairsByYearLikely"] = dict(ly)
    report["inventoryByYear"] = dict(inv_years)

    if args.json:
        args.json.write_text(json.dumps(report, indent=1, default=str))
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
