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
  (e) vPIC-hybrid column (CURATION_SPEC §7.2 P0.5, 2026-11-05): every
      ENGINE_FAMILIES app that hybrid/EV cars on the lots fall into, and
      whether they pass the family's engine gate (decode agrees, or no
      decode on a "sole" app) — those are the over-claims P0.5 removes
  (f) Verified donors per family and category (a donor car counts when it
      shows Verified for at least one seeker in the inventory), with the
      hybrid-flagged share and the P0.4 donor-identity share
      (pfDonorIdentity: vpicMismatch, or the VIN's model-year character
      disagrees with the listed year). --compare prints before/after deltas.

Seeker population proxy: the live inventory itself (a car in a yard is as
good a proxy as any for the cars people drive). Pairs are
(seeker vehicle, donor vehicle) within one engine family, weighted by
vehicle counts. Engine-denied donors (decode contradicts the family) are
EXCLUDED rows in the app, not Likely — reported separately.

Hybrid signals (any one flags the car; an audit heuristic, never shipped):
  vpic  the VIN decode (after _correct_vpic, so VIN_TRIM_PATTERNS' Camry
        "Hybrid" applies) or the inventory's vpic side-table says hybrid /
        HEV / PHEV / Energi / BAS / Green Line / Electric, or a narrow
        make/model/year trim rule (HYBRID_TRIM_RULES: Malibu "ECO" =
        eAssist); vPIC's model-level strings ("Base/Hybrid") count too —
        they mean vPIC itself cannot tell the hybrid from the gas car
  name  the yard's own model name says so ("Camry Hybrid", "RX 400h")
  vin   the car shares make + VIN positions 4-8 with >= 2 cars whose yard
        name says hybrid (catches Altima/Highlander hybrids whose decode
        has no trim at all)

Usage: python3 scraper/_audit_verified_fits.py [--json out.json]
                                               [--compare before.json]
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


HYBRID_RE = re.compile(
    r"hybrid|\bhev\b|\bphev\b|\bfhev\b|\bmhev\b|energi|plug-?in|e-?assist"
    r"|\bbas\b|green ?line|electric|e-?tron|\b\d{3}h\b", re.I)
# Trim words that mean "hybrid" only on one model line (feed make, model
# prefix, first year, last year, regex on the vPIC trim).
HYBRID_TRIM_RULES: list[tuple[str, str, int, int, re.Pattern]] = [
    # 2013-14 Malibu Eco = the 2.4 eAssist mild hybrid (vPIC "1LT ECO")
    ("Chevrolet", "malibu", 2013, 2014, re.compile(r"\beco\b", re.I)),
]

# North American VIN model-year character (49 CFR 565.15, position 10):
# a 30-year cycle starting 1980; I, O, Q, U, Z and 0 are never used.
_VIN_YEAR_CHARS = "ABCDEFGHJKLMNPRSTVWXY123456789"


def vin_model_year(vin: str, listed_year: int) -> int | None:
    """Model year from a 17-character VIN's 10th character, resolving the
    30-year cycle toward the listed year (ties go to the later year). None
    when the VIN is not 17 characters or the character is not a year code.
    Python mirror of docs/app.js pfVinModelYear."""
    v = re.sub(r"[^A-Z0-9]", "", str(vin or "").upper())
    if len(v) != 17:
        return None
    i = _VIN_YEAR_CHARS.find(v[9])
    if i < 0:
        return None
    base = 1980 + i
    best = None
    for k in range(-1, 4):
        cand = base + 30 * k
        if best is None or abs(cand - listed_year) < abs(best - listed_year) \
                or (abs(cand - listed_year) == abs(best - listed_year) and cand > best):
            best = cand
    return best


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
    ap.add_argument("--compare", type=Path,
                    help="an earlier --json output: print per-family Verified donor deltas")
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
    vpic_side = inv.get("vpic") or {}
    report: dict = {"scrapedAt": inv["scrapedAt"], "totalVehicles": len(vehicles)}

    # ---------------- per-car hybrid signals + P0.4 identity -------------
    name_vds: collections.Counter = collections.Counter()
    for v in vehicles:
        vin = (v[I_VIN] or "").upper()
        if len(vin) == 17 and HYBRID_RE.search(v[I_MD] or ""):
            name_vds[(v[I_MK] or "", vin[3:8])] += 1
    hyb_src: dict[int, str] = {}   # row index -> "vpic+name+vin" (only hybrids)
    ident_bad: set[int] = set()    # row index -> P0.4 would demote a Verified row
    for i, v in enumerate(vehicles):
        vin = (v[I_VIN] or "").upper()
        y, mk, md = v[I_Y] or 0, v[I_MK] or "", v[I_MD] or ""
        side = vpic_side.get(str(i)) or []
        dec = decodes.get(vin) if len(vin) == 17 else None
        if isinstance(dec, dict):
            dec = js._correct_vpic(dec, vin)
        else:
            dec = None
        vtext = " ".join(str(x or "") for x in side[:3])
        if dec:
            vtext += " " + " ".join(str(dec.get(k) or "") for k in
                                    ("trim", "series", "model", "engine"))
        trims = " ".join([str(side[0] if side else ""), str((dec or {}).get("trim") or "")])
        srcs = []
        if HYBRID_RE.search(vtext) or any(
                mk == r_mk and md.lower().startswith(r_md) and lo <= y <= hi
                and rx.search(trims)
                for r_mk, r_md, lo, hi, rx in HYBRID_TRIM_RULES):
            srcs.append("vpic")
        if HYBRID_RE.search(md):
            srcs.append("name")
        if len(vin) == 17 and "name" not in srcs and name_vds.get((mk, vin[3:8]), 0) >= 2:
            srcs.append("vin")
        if srcs:
            hyb_src[i] = "+".join(srcs)
        if len(side) > 4 and side[4]:
            ident_bad.add(i)
        else:
            vy = vin_model_year(vin, y)
            if vy is not None and y and vy != y:
                ident_bad.add(i)
    print(f"hybrid/EV-flagged cars: {len(hyb_src):,}; P0.4 identity-flagged "
          f"(vpicMismatch or VIN year char != listed year): {len(ident_bad):,}")
    report["hybridFlagged"] = len(hyb_src)
    report["identityFlagged"] = len(ident_bad)

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
    for i, v in enumerate(vehicles):
        y, mk, md = v[I_Y] or 0, v[I_MK] or "", v[I_MD] or ""
        e = ex.get(str(v[I_ID]))
        engine_str = e[2] if e and len(e) > 2 else ""
        is_diesel = bool(engine_str) and "diesel" in engine_str.lower()
        liters, cyl = js._parse_engine_str(engine_str)
        eng_buckets[(y, mk, md)][(is_diesel, liters, cyl,
                                  i in hyb_src, i in ident_bad)] += 1

    sq_cache: dict[tuple[str, str], tuple[str, str, str]] = {}
    for (y, mk, md) in ymm_counts:
        if (mk, md) not in sq_cache:
            sq_cache[(mk, md)] = (mk.lower(), squash(md, mk), squash(md))

    def engine_verdict(is_diesel, liters, cyl, spec) -> bool | None:
        """docs/app.js pfEngineVerdict: True confirms, False denies, None = no data."""
        if is_diesel:
            return False
        if liters is None:
            return None
        if not any(abs(liters - want) < 0.05 for want in spec["liters"]):
            return False
        want_cyl = spec.get("cyl")
        if cyl is not None and want_cyl is not None and cyl != want_cyl:
            return False
        return True

    def verdict_for(key: tuple, fam: dict) -> collections.Counter:
        """Counter {(True/False/None, hybrid, identityBad): n} for a ymm
        bucket against a family."""
        out: collections.Counter = collections.Counter()
        spec = fam["engine"]
        for (is_diesel, liters, cyl, hyb, ibad), n in eng_buckets[key].items():
            out[(engine_verdict(is_diesel, liters, cyl, spec), hyb, ibad)] += n
        return out

    CATS = ["alternator", "starter", "engine-assembly"]
    cat_res: dict[str, dict] = {}
    # fam_ver[fid][cat] = Verified donors / pairs, with hybrid and P0.4 shares
    fam_ver: dict[str, dict] = collections.defaultdict(dict)
    for cat in CATS:
        tot_pairs = ver_pairs = ver_pairs_p04 = 0
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
                for (verdict, hyb, ibad), vn in verdict_for(key, fam).items():
                    if verdict is False:
                        donors[("DENIED", key[0])] += vn
                        continue
                    engine_ok = verdict is True or (verdict is None and sole and not ambig)
                    confirmed = verdict is True
                    donors[(mask, ambig, engine_ok, confirmed, key[0], hyb, ibad)] += vn

            fv = fam_ver[fid].setdefault(cat, {"donors": 0, "hybridDonors": 0,
                                               "identityDonors": 0, "pairs": 0,
                                               "pairsP04": 0})
            for dk, dn in donors.items():
                if dk[0] == "DENIED":
                    excluded_donors += dn
                    continue
                dmask, dambig, engine_ok, confirmed, dyear, dhyb, dibad = dk
                donors_total += dn
                if engine_ok:
                    donors_engine_ok += dn
                donor_ver = False
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
                        donor_ver = True
                        fv["pairs"] += pairs
                        if not dibad:
                            ver_pairs_p04 += pairs
                            fv["pairsP04"] += pairs
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
                if donor_ver:
                    fv["donors"] += dn
                    if dhyb:
                        fv["hybridDonors"] += dn
                    if dibad:
                        fv["identityDonors"] += dn

        cat_res[cat] = {
            "totalPairs": tot_pairs, "verifiedPairs": ver_pairs,
            "verifiedPairsP04": ver_pairs_p04,
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
        print(f"    with the P0.4 donor-identity guard: Verified {ver_pairs_p04:,} "
              f"({ver_pairs_p04 / tot_pairs:.1%})")
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

    # ---------------- (e) vPIC-hybrid column -------------------------------
    # Each hybrid/EV-flagged car against every family, attributed to the
    # FIRST matching app (the client's fam.apps.find). "gate" = passes the
    # engine gate (decode agrees, or decode silent on a sole app); "exposed"
    # = gate AND app not ambig AND (the car sits in a verified group of some
    # part of that family, or its decode confirms the engine, which is what
    # an engine-assembly Verified needs), i.e. it can show "Verified" today.
    hyb_apps: dict[tuple, dict] = {}
    for i, src in hyb_src.items():
        v = vehicles[i]
        y, mk, md = v[I_Y] or 0, v[I_MK] or "", v[I_MD] or ""
        mk_lc, sq_s, sq_r = mk.lower(), squash(md, mk), squash(md)
        e = ex.get(str(v[I_ID]))
        engine_str = e[2] if e and len(e) > 2 else ""
        is_diesel = bool(engine_str) and "diesel" in engine_str.lower()
        liters, cyl = js._parse_engine_str(engine_str)
        for fid, fam in js.ENGINE_FAMILIES.items():
            ai = next((k for k, a in enumerate(fam["apps"])
                       if app_matches(a, y, mk_lc, sq_s, sq_r)), None)
            if ai is None:
                continue
            app = fam["apps"][ai]
            flags = js._app_flags(app)
            verdict = engine_verdict(is_diesel, liters, cyl, fam["engine"])
            gate = verdict is True or (verdict is None and bool(flags.get("sole"))
                                       and not flags.get("ambig"))
            in_vg = any(app_matches(sp, y, mk_lc, sq_s, sq_r)
                        for p in fam["parts"].values()
                        for g in ((p.get("verified") or {}).get("groups") or [])
                        for sp in g)
            row = hyb_apps.setdefault((fid, ai), {
                "family": fid, "app": list(app[:4]),
                "sole": bool(flags.get("sole")), "ambig": bool(flags.get("ambig")),
                "hybrids": 0, "verdict": collections.Counter(),
                "gate": 0, "exposed": 0, "sources": collections.Counter(),
                "years": collections.Counter()})
            row["hybrids"] += 1
            row["verdict"][str(verdict)] += 1
            row["sources"][src] += 1
            row["years"][y] += 1
            if gate:
                row["gate"] += 1
                # engine-assembly is Verified on a confirming decode alone
                if not flags.get("ambig") and (in_vg or verdict is True):
                    row["exposed"] += 1
    print("\n(e) vPIC-hybrid column: family apps that hybrid/EV cars fall into "
          "(first matching app), rows where any pass the engine gate")
    print(f"{'family':18s} {'app':34s} {'flag':5s} {'hyb':>4} {'gate':>4} "
          f"{'expo':>4}  verdicts / years / sources")
    for (fid, ai), r in sorted(hyb_apps.items()):
        if not r["gate"]:
            continue
        a = r["app"]
        flag = "ambig" if r["ambig"] else ("sole" if r["sole"] else "")
        yrs = sorted(r["years"])
        print(f"{fid:18s} {a[0] + ' ' + a[1] + f' {a[2]}-{a[3]}':34s} {flag:5s} "
              f"{r['hybrids']:>4} {r['gate']:>4} {r['exposed']:>4}  "
              f"{dict(r['verdict'])} {yrs[0]}-{yrs[-1]} {dict(r['sources'])}")
    report["hybridApps"] = [
        {**{k: (dict(v) if isinstance(v, collections.Counter) else v)
            for k, v in r.items()}, "appIndex": ai}
        for (fid, ai), r in sorted(hyb_apps.items())]

    # ---------------- (f) Verified donors per family -----------------------
    print("\n(f) Verified donors per family (cars showing Verified for >= 1 "
          "seeker): all / hybrid-flagged / P0.4 identity-flagged")
    print(f"{'family':22s} {'category':16s} {'donors':>7} {'hybrid':>7} {'ident':>6}")
    for fid in sorted(fam_ver):
        for cat, fv in fam_ver[fid].items():
            if fv["donors"]:
                print(f"{fid:22s} {cat:16s} {fv['donors']:>7,} "
                      f"{fv['hybridDonors']:>7,} {fv['identityDonors']:>6,}")
    report["verifiedDonors"] = {fid: d for fid, d in fam_ver.items()}

    if args.compare:
        before = json.loads(args.compare.read_text()).get("verifiedDonors", {})
        print(f"\nVerified donors, {args.compare} -> now "
              "(families that changed; donors / hybrid-flagged donors / pairs)")
        tot_b = collections.Counter()
        tot_a = collections.Counter()
        for fid in sorted(set(before) | set(fam_ver)):
            for cat in CATS:
                b = (before.get(fid) or {}).get(cat) or {}
                a = (fam_ver.get(fid) or {}).get(cat) or {}
                for k in ("donors", "hybridDonors", "pairs"):
                    tot_b[(cat, k)] += b.get(k, 0)
                    tot_a[(cat, k)] += a.get(k, 0)
                if any(b.get(k, 0) != a.get(k, 0) for k in ("donors", "hybridDonors", "pairs")):
                    print(f"  {fid:22s} {cat:16s} donors {b.get('donors', 0):>6,} -> "
                          f"{a.get('donors', 0):>6,}   hybrid {b.get('hybridDonors', 0):>4,} -> "
                          f"{a.get('hybridDonors', 0):>4,}   pairs {b.get('pairs', 0):>12,} -> "
                          f"{a.get('pairs', 0):>12,}")
        for cat in CATS:
            print(f"  TOTAL {cat:16s} donors {tot_b[(cat, 'donors')]:>7,} -> "
                  f"{tot_a[(cat, 'donors')]:>7,}   hybrid {tot_b[(cat, 'hybridDonors')]:>5,} -> "
                  f"{tot_a[(cat, 'hybridDonors')]:>5,}")

    if args.json:
        args.json.write_text(json.dumps(report, indent=1, default=str))
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
