#!/usr/bin/env python3
"""Coverage before/after for the OEM layer (CURATION_SPEC.md §10). Offline.

    python3 scraper/oem_fitment/measure.py [--groups DIR] [--reports DIR] [--out FILE]
                                           [--before interchange.json] [--parity]

Every lot car stands in as a seeker for its own (make, model, year), and on
engine kinds for its decoded engine family; donors are every other lot car.
Tiers come from a Python port of the client (docs/app.js pfRunSearch):

- view "old": the client as shipped on main today (the platform loop fails
  open: any tier but "likely" counts Verified; no OEM keys; no identity
  guard);
- view "new": the Phase 0 guards (§7.2: platform tier must be exactly
  "verified"; pfDonorIdentity on every row that would be Verified, mirrored
  from the P0 branch's app.js) plus the Phase 1 reading of oemGroups /
  oemVg (§7.4; that client is not written yet, so this view is the spec's).

Payloads: "before" = HEAD's docs/data/interchange.json (or --before);
"after" = build_interchange_payload() with --groups as the OEM groups
directory (default scraper/oem_fitment/groups).

Per category (§10.2): M-car (share of cars with at least one Verified
donor, nationwide), M-local (within 100 mi of the car's own yard), M-pairs
(Verified ordered car pairs / Verified + Likely), flip counts with 50 random
key pairs each, lever attribution, blocked-by. The OEM funnel (§10.3) and
the completion worklist (§10.4) come from curate.py's reports
(--reports, default groups/_report). Output: groups/_report/coverage-
YYYY-MM-DD.json (§10.5) and a markdown table on stdout.

Same-model generation donors are always Likely; combo and exact kinds have
no Verified tier and are listed with M-car 0 without pair counts. Makes and
models are read as the inventory ships them (already canonical), so the
client's alias tables are not applied. --parity re-counts three seekers car
by car with a literal transcription of the client loop and compares.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DATA = REPO / "docs" / "data"
LOCAL_MI = 100
SAMPLE_N = 50


# ===================================================== client ports (app.js)
def squash(s) -> str:                                     # pfSquash
    return re.sub(r"[^a-z0-9]", "", str(s or "").lower())


def squash_model(model, make="") -> str:                  # pfSquashModel
    sm, mk = squash(model), squash(make)
    if mk and sm.startswith(mk) and len(sm) > len(mk):
        sm = sm[len(mk):]
    if sm.endswith("pickup") and len(sm) > len("pickup"):
        sm = sm[: -len("pickup")]
    return sm


def app_matches(app, year, make, model) -> bool:          # pfAppMatches
    if not (app[2] <= year <= app[3]):
        return False
    if str(make or "").lower() not in app[0].lower().split("|"):
        return False
    cands = (squash_model(model, make), squash_model(model, ""))
    prefix = app[1].endswith("*")
    am = squash(app[1][:-1] if prefix else app[1])
    return any(c.startswith(am) for c in cands) if prefix else am in cands


def parse_engine(s):                                      # pfParseEngine
    if not s:
        return None, None
    sl = str(s).lower()
    lm = re.search(r"(\d+\.\d+)\s*l", sl)
    cm = re.search(r"(\d+)[\s-]*cyl", sl)
    return (float(lm.group(1)) if lm else None), (int(cm.group(1)) if cm else None)


def engine_verdict(engine_str, fam) -> bool | None:       # pfEngineVerdict
    if engine_str and re.search(r"diesel", engine_str, re.I):
        return False
    lit, cyl = parse_engine(engine_str)
    if lit is None:
        return None
    if not any(abs(lit - w) < 0.05 for w in fam["liters"]):
        return False
    if cyl is not None and fam.get("cyl") is not None and cyl != fam["cyl"]:
        return False
    return True


def parse_fits(fits):                                     # pfParseFits
    m = re.search(r"(\d{4})\s*[–-]\s*(\d{4})", str(fits or ""))
    return (int(m.group(1)), int(m.group(2))) if m else None


def part_row(top_parts, tokens):                          # pfPartRow
    for p in top_parts or []:
        nl = str(p.get("name") or "").lower()
        if any(t in nl for t in tokens):
            return p
    return None


# P0 branch app.js: pfVinModelYear / pfVinValid / pfDonorIdentity
_VIN_YEAR = "ABCDEFGHJKLMNPRSTVWXY123456789"
_VIN_TRANSLIT = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8, "J": 1, "K": 2, "L": 3, "M": 4,
                 "N": 5, "P": 7, "R": 9, "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9}
_VIN_W = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]


def _norm_vin(vin) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(vin or "").strip().upper()) if isinstance(vin, str) else ""


def vin_model_year(vin, year):
    s = _norm_vin(vin)
    if len(s) != 17:
        return None
    i = _VIN_YEAR.find(s[9])
    if i < 0:
        return None
    y = int(year or 0)
    best = None
    for k in range(-1, 4):
        c = 1980 + i + 30 * k
        if best is None or abs(c - y) < abs(best - y) or (abs(c - y) == abs(best - y) and c > best):
            best = c
    return best


def vin_valid(vin) -> bool:
    s = _norm_vin(vin)
    if not re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", s) or vin_model_year(s, 0) is None:
        return False
    tot = sum((int(ch) if ch.isdigit() else _VIN_TRANSLIT[ch]) * _VIN_W[i] for i, ch in enumerate(s))
    r = tot % 11
    return s[8] == ("X" if r == 10 else str(r))


def donor_identity_ok(mismatch, vin, year, oem=False) -> bool:
    if mismatch:
        return False
    y = int(year or 0)
    vy = vin_model_year(vin, y) if y else None
    if vy is not None and vy != y:
        return False
    if oem and not vin_valid(vin):
        return False
    return True


# ===================================================================== fleet
def _haversine_mi(a, b) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(h))


class Fleet:
    """The lot cars, indexed for the client loops. Car = (id, vin, year,
    make, model, yard, partset, engine, mismatch, guard, guard_oem)."""

    def __init__(self, inv: dict, extras: dict | None):
        F = {k: i for i, k in enumerate(inv["fields"])}
        ex = (extras or {}).get("extras") or {}
        vp = inv.get("vpic") or {}
        self.part_sets = inv.get("partSets") or []
        self.cars = []
        self.by_key: dict = defaultdict(list)
        for i, r in enumerate(inv["vehicles"]):
            e = ex.get(str(r[F["id"]]))
            eng = e[2] if e and len(e) > 2 else ""
            v = vp.get(str(i))
            mism = bool(v and len(v) > 4 and v[4])
            key = (r[F["make"]] or "", r[F["model"]] or "", int(r[F["year"]] or 0))
            vin = r[F["vin"]] or ""
            car = (r[F["id"]], vin, key[2], key[0], key[1], r[F["yard"]], r[F["partSet"]], eng, mism,
                   donor_identity_ok(mism, vin, key[2]), donor_identity_ok(mism, vin, key[2], oem=True))
            self.by_key[key].append(len(self.cars))
            self.cars.append(car)
        self.keys = sorted(self.by_key)
        self.n = Counter({k: len(v) for k, v in self.by_key.items()})
        self.keys_by_make: dict = defaultdict(list)
        self._sq = {}
        for k in self.keys:
            self.keys_by_make[k[0].lower()].append(k)
            if (k[0], k[1]) not in self._sq:
                self._sq[(k[0], k[1])] = (squash_model(k[1], k[0]), squash_model(k[1], ""))
        yards = inv.get("yards") or []
        yf = {k: i for i, k in enumerate(inv.get("yardFields") or ["location", "city", "state", "lat", "lng"])}
        coords = [(y[yf["lat"]], y[yf["lng"]]) if len(y) > yf["lng"] and isinstance(y[yf["lat"]], (int, float))
                  and isinstance(y[yf["lng"]], (int, float)) else None for y in yards]
        self.near = {}
        for i, a in enumerate(coords):
            self.near[i] = [] if a is None else [j for j, b in enumerate(coords)
                                                 if b is not None and _haversine_mi(a, b) <= LOCAL_MI]
        self._match_cache: dict = {}

    def app_match_key(self, app, key) -> bool:
        if not (app[2] <= key[2] <= app[3]):
            return False
        if key[0].lower() not in app[0].lower().split("|"):
            return False
        prefix = app[1].endswith("*")
        am = squash(app[1][:-1] if prefix else app[1])
        cands = self._sq[(key[0], key[1])]
        return any(c.startswith(am) for c in cands) if prefix else am in cands

    def keys_matching(self, apps) -> frozenset:
        ck = json.dumps(apps, sort_keys=True)
        hit = self._match_cache.get(ck)
        if hit is None:
            out = set()
            for a in apps:
                for mk in a[0].lower().split("|"):
                    for k in self.keys_by_make.get(mk, ()):
                        if self.app_match_key(a, k):
                            out.add(k)
            hit = self._match_cache[ck] = frozenset(out)
        return hit

    def first_app(self, apps, key):
        for a in apps:
            if self.app_match_key(a, key):
                return a
        return None


def _gen_map(payload):
    m = {}
    for gmk, gmd, wins in payload.get("modelGenerations") or []:
        m[squash(gmk) + "|" + squash_model(gmd, gmk)] = wins
    return m


def gen_window(gm, make, model, year):                    # pfGenWindow
    mk = squash(make)
    wins = gm.get(mk + "|" + squash_model(model, make)) or gm.get(mk + "|" + squash_model(model, ""))
    for w in wins or []:
        if w[0] <= year <= w[1]:
            return w
    return None


# ================================================================= measures
def _cat(payload, cid):
    return next((c for c in payload.get("categories") or [] if c["id"] == cid), None)


def _tier(g, view, oem=False):
    if view == "old" and not oem:
        return "likely" if g.get("tier") == "likely" else "verified"     # shipped app.js
    return "verified" if g.get("tier") == "verified" else "likely"       # P0.1


class Result:
    """Per category and view: seeker tallies and per-seeker donor maps for
    the flip analysis."""

    def __init__(self):
        self.cars = 0
        self.seekers = 0
        self.m_car = 0
        self.m_local = 0
        self.pairs_v = 0
        self.pairs_l = 0
        self.ver_keys: dict = {}      # seeker key (or (key, fam)) -> {donor key: verified cars}
        self.lik_keys: dict = {}      # seeker key -> set of group-Likely donor keys
        self.per_seeker: dict = {}    # seeker key -> (verified donors, likely donors) incl. its own cars

    def out(self, kind) -> dict:
        d = {"kind": kind, "cars": self.cars, "seekers": self.seekers, "m_car": self.m_car,
             "m_car_share": round(self.m_car / self.cars, 4) if self.cars else 0.0,
             "m_local": self.m_local, "m_local_share": round(self.m_local / self.cars, 4) if self.cars else 0.0,
             "pairs_verified": self.pairs_v, "pairs_likely": self.pairs_l,
             "m_pairs": round(self.pairs_v / (self.pairs_v + self.pairs_l), 4) if (self.pairs_v + self.pairs_l) else 0.0}
        return d


def _local_hits(fleet, seeker_cars, vyard, self_v):
    """Cars among seeker_cars with a Verified donor (other than itself)
    within LOCAL_MI of their own yard. vyard: Counter yard -> verified cars;
    self_v(car index) -> 1 when that car is itself a Verified donor."""
    by_yard = defaultdict(list)
    for ci in seeker_cars:
        by_yard[fleet.cars[ci][5]].append(ci)
    hits = 0
    for y, cis in by_yard.items():
        local = sum(vyard.get(j, 0) for j in fleet.near.get(y, ()))
        for ci in cis:
            if local - self_v(ci) >= 1:
                hits += 1
    return hits


def measure_body(fleet, payload, cat, view) -> Result:
    res = Result()
    c = _cat(payload, cat) or {"tokens": []}
    tokens = [t.lower() for t in c.get("tokens") or []]
    groups = []
    for g in payload.get("platformGroups") or []:
        if g.get("cat") == cat:
            groups.append((_tier(g, view), "platform", g["id"], fleet.keys_matching(g["apps"])))
    if view == "new":
        for g in payload.get("oemGroups") or []:
            if g.get("cat") == cat:
                groups.append((_tier(g, view, oem=True), "oem", g["id"], fleet.keys_matching(g["apps"])))
    in_groups = defaultdict(list)
    for i, g in enumerate(groups):
        for k in g[3]:
            in_groups[k].append(i)
    # same-model generation donors: (make, squash) -> Counter((key, year, window))
    win_of_set: dict = {}
    bucket = defaultdict(Counter)
    for ci, car in enumerate(fleet.cars):
        ps = car[6]
        if ps not in win_of_set:
            row = part_row(fleet.part_sets[ps] if isinstance(ps, int) and 0 <= ps < len(fleet.part_sets) else [],
                           tokens)
            win_of_set[ps] = parse_fits(row.get("fits")) if row else None
        key = (car[3], car[4], car[2])
        bucket[(car[3], squash_model(car[4], car[3]))][(key, car[2], win_of_set[ps])] += 1
    gm = _gen_map(payload)
    sig_cache: dict = {}

    def tally(sig):
        if sig in sig_cache:
            return sig_cache[sig]
        vp, vo, lk = set(), set(), set()
        for i in sig:
            tier, kind, _gid, mem = groups[i]
            (lk if tier != "verified" else vp if kind == "platform" else vo).update(mem)
        ver, nv, nlg, vyard = {}, 0, 0, Counter()
        for d in vp | vo | lk:
            cis = fleet.by_key[d]
            if d in vp:
                ok = [ci for ci in cis if view == "old" or fleet.cars[ci][9]]
            elif d in vo:
                ok = [ci for ci in cis if fleet.cars[ci][10]]
            else:
                ok = []
            if ok:
                ver[d] = len(ok)
                for ci in ok:
                    vyard[fleet.cars[ci][5]] += 1
            nv += len(ok)
            nlg += len(cis) - len(ok)
        t = sig_cache[sig] = (ver, nv, nlg, vyard, frozenset(vp | vo | lk), frozenset(lk), frozenset(vp),
                              frozenset(vo))
        return t

    def self_verified(S, ci, vp, vo) -> bool:
        """Is lot car ci (key S) itself a Verified donor for seeker key S?"""
        car = fleet.cars[ci]
        if S in vp:
            return view == "old" or car[9]
        if S in vo:
            return car[10]
        return False

    for S in fleet.keys:
        cis = fleet.by_key[S]
        res.cars += len(cis)
        res.seekers += len(cis)
        sig = tuple(in_groups.get(S, ()))
        ver, nv, nlg, vyard, in_results, lk, vp, vo = tally(sig)
        sw = gen_window(gm, S[0], S[1], S[2])
        ngen = gen_self = 0
        for (d, y, win), n in bucket.get((S[0], squash_model(S[1], S[0])), {}).items():
            if d in in_results:
                continue
            if (win and win[0] <= S[2] <= win[1]) or (sw and sw[0] <= y <= sw[1]):
                ngen += n
                if d == S:
                    gen_self += n
        verified_self = {ci for ci in cis if self_verified(S, ci, vp, vo)}
        gself = len(verified_self)
        nl = nlg + ngen
        lself = (len(cis) - gself if S in in_results else 0) + gen_self
        res.pairs_v += len(cis) * nv - gself
        res.pairs_l += len(cis) * nl - lself
        if nv:
            res.m_car += (len(cis) - gself) * (nv >= 1) + gself * (nv >= 2)
            res.m_local += _local_hits(fleet, cis, vyard, lambda ci: 1 if ci in verified_self else 0)
            res.ver_keys[S] = ver
        if lk:
            res.lik_keys[S] = lk
        res.per_seeker[S] = (nv, nl)
    return res


def _family_choice(fleet, payload, cat):
    """seeker car index -> chosen family id (the decoded engine family): the
    only offered family the decode confirms, else the only one it does not
    deny. Cars with none are not engine seekers ("engine_unknown")."""
    fams = payload.get("engineFamilies") or []
    offered = defaultdict(list)          # key -> [(fam, app)]
    for f in fams:
        p = (f.get("parts") or {}).get(cat)
        if p is None:
            continue
        yrs = p.get("years")
        for k in fleet.keys_matching(f["apps"]):
            if yrs and not (yrs[0] <= k[2] <= yrs[1]):
                continue
            offered[k].append(f)
    choice, unknown = {}, 0
    for k, fl in offered.items():
        for ci in fleet.by_key[k]:
            eng = fleet.cars[ci][7]
            cands = [f for f in fl if engine_verdict(eng, f) is not False]
            trues = [f for f in cands if engine_verdict(eng, f) is True]
            if len(trues) == 1:
                choice[ci] = trues[0]["id"]
            elif len(cands) == 1 and not trues:
                choice[ci] = cands[0]["id"]
            else:
                unknown += 1
    return choice, unknown


def measure_engine(fleet, payload, cat, view) -> Result:
    res = Result()
    res.cars = len(fleet.cars)
    choice, unknown = _family_choice(fleet, payload, cat)
    res.engine_unknown = unknown
    oem_vg = payload.get("oemVg") or {} if view == "new" else {}
    by_fam_seekers = defaultdict(lambda: defaultdict(list))
    for ci, fid in choice.items():
        car = fleet.cars[ci]
        by_fam_seekers[fid][(car[3], car[4], car[2])].append(ci)
    for f in payload.get("engineFamilies") or []:
        seek = by_fam_seekers.get(f["id"])
        if not seek:
            continue
        p = f["parts"][cat]
        yrs = p.get("years")
        groups = [("hand", g) for g in p.get("vg") or []] + \
                 [("oem", g) for g in ((oem_vg.get(f["id"]) or {}).get(cat) or [])]
        gmem = [(kind, fleet.keys_matching(g)) for kind, g in groups]
        # donors: key -> [(car index, engineOk, confirmed, app ambig)]
        donors = {}
        for k in fleet.keys_matching(f["apps"]):
            if yrs and not (yrs[0] <= k[2] <= yrs[1]):
                continue
            app = fleet.first_app(f["apps"], k)
            row = []
            for ci in fleet.by_key[k]:
                vd = engine_verdict(fleet.cars[ci][7], f)
                if vd is False:
                    continue
                ok = vd is True or (vd is None and bool(app[4]) and not app[5])
                row.append((ci, ok, vd is True, bool(app[5])))
            if row:
                donors[k] = row
        cache: dict = {}
        for S, scis in seek.items():
            sapp = fleet.first_app(f["apps"], S)
            s_ambig = bool(sapp and sapp[5])
            sig = (tuple(i for i, (_k, m) in enumerate(gmem) if S in m), s_ambig)
            if sig not in cache:
                in_hand = set().union(*[gmem[i][1] for i in sig[0] if gmem[i][0] == "hand"])
                in_oem = set().union(*[gmem[i][1] for i in sig[0] if gmem[i][0] == "oem"])
                ver, nv, nl, vyard, vself = {}, 0, 0, Counter(), set()
                for d, row in donors.items():
                    for ci, ok, conf, a_ambig in row:
                        car = fleet.cars[ci]
                        if cat == "engine-assembly":
                            v = conf and not a_ambig and not s_ambig
                            guard = car[9]
                        else:
                            v = ok and not a_ambig and not s_ambig and (d in in_hand or d in in_oem)
                            guard = car[9] if d in in_hand else car[10]
                        if v and view == "new" and not guard:
                            v = False
                        if v:
                            nv += 1
                            ver[d] = ver.get(d, 0) + 1
                            vyard[car[5]] += 1
                            vself.add(ci)
                        else:
                            nl += 1
                cache[sig] = (ver, nv, nl, vyard, vself)
            ver, nv, nl, vyard, vself = cache[sig]
            res.seekers += len(scis)
            own = [ci for ci in scis if ci in vself]
            # the seeker car is itself a donor (verdict not False: it chose f)
            res.pairs_v += len(scis) * nv - len(own)
            res.pairs_l += len(scis) * nl - (len(scis) - len(own))
            if nv:
                res.m_car += sum(1 for ci in scis if nv - (1 if ci in vself else 0) >= 1)
                res.m_local += _local_hits(fleet, scis, vyard, lambda ci: 1 if ci in vself else 0)
                res.ver_keys[(S, f["id"])] = ver
            res.per_seeker[(S, f["id"])] = (nv, nl)
    return res


def measure(fleet, payload, view) -> dict:
    out = {}
    for c in payload.get("categories") or []:
        kind = c.get("kind")
        if kind == "body":
            out[c["id"]] = measure_body(fleet, payload, c["id"], view)
        elif kind == "engine":
            out[c["id"]] = measure_engine(fleet, payload, c["id"], view)
        else:
            r = Result()
            r.cars = len(fleet.cars)
            r.note = f"{kind} kind: no Verified tier in the client (same-model generation only, Likely)"
            out[c["id"]] = r
    return out


# ============================================================== comparisons
def _lever(s, d) -> str:
    s, d = (s[0] if isinstance(s[0], tuple) else s), (d[0] if isinstance(d[0], tuple) else d)
    if s[0] != d[0]:
        return "cross-make"
    if s[1] != d[1]:
        return "cross-model"
    return "single-model"


def flips(fleet, before: dict, after: dict, seed: int = 7) -> dict:
    """Likely -> Verified, Verified -> Likely (key level, weighted by cars)
    and new cross-model Likely pairs, with SAMPLE_N random key pairs each."""
    out = {}
    rnd = random.Random(seed)
    for cat in sorted(set(before) | set(after)):
        b, a = before.get(cat), after.get(cat)
        if not hasattr(b, "ver_keys") or not hasattr(a, "ver_keys"):
            continue
        up, down, newx = Counter(), Counter(), Counter()
        lever = Counter()
        for S in set(b.ver_keys) | set(a.ver_keys):
            bv, av = b.ver_keys.get(S, {}), a.ver_keys.get(S, {})
            key = S[0] if isinstance(S[0], tuple) else S
            n_s = fleet.n[key]
            for d in set(bv) | set(av):
                delta = av.get(d, 0) - bv.get(d, 0)
                # same key: each Verified car of S pairs with the other n_s - 1
                # seekers of S (a car is never its own donor)
                w = (n_s - 1 if d == key else n_s) * abs(delta)
                if not w:
                    continue
                if delta > 0:
                    up[(S, d)] += w
                    lever[_lever(S, d)] += w
                else:
                    down[(S, d)] += w
        for S, lk in a.lik_keys.items():
            before_any = set(b.lik_keys.get(S, ())) | set(b.ver_keys.get(S, {}))
            for d in lk - before_any:
                if (d[0], d[1]) != (S[0], S[1]):
                    newx[(S, d)] += fleet.n[S] * fleet.n[d]

        def pack(c):
            keys = sorted(c, key=lambda x: json.dumps(x, default=str))
            smp = rnd.sample(keys, min(SAMPLE_N, len(keys)))
            return {"key_pairs": len(c), "car_pairs": sum(c.values()),
                    "sample": [[list(s) if not isinstance(s[0], tuple) else [list(s[0]), s[1]], list(d)]
                               for s, d in sorted(smp, key=lambda x: json.dumps(x, default=str))]}
        out[cat] = {"likely_to_verified": pack(up), "verified_to_likely": pack(down),
                    "new_cross_model_likely": pack(newx),
                    "lever_attribution": {**{k: lever.get(k, 0) for k in ("single-model", "cross-model",
                                                                          "cross-make")},
                                          "directional": 0, "conditional": 0,
                                          "note": "directional and conditional pairs are Phase 2 (not shipped)"}}
    return out


def funnel_from_reports(report_dir: Path) -> dict:
    """§10.3: cars per (ns, cat) per stage, summed from curate.py's
    _report/<ns>.json; plus the hypothetical-if-closed funnel, the
    namespace gates and the top of each completion worklist."""
    out = {"by_ns": {}, "by_cat": defaultdict(lambda: defaultdict(Counter)),
           "hypothetical_by_cat": defaultdict(lambda: defaultdict(Counter)), "blocked_by": Counter()}
    for p in sorted(report_dir.glob("*.json")):
        if p.name.count(".") > 1 or p.stem.startswith("coverage") or p.stem.startswith("cross_ns"):
            continue
        rep = json.loads(p.read_text())
        if "funnel_cars" not in rep:
            continue
        ns = rep["ns"]
        comp = report_dir / f"{ns}.completion.json"
        top = json.loads(comp.read_text())["rows"][:10] if comp.exists() else []
        out["by_ns"][ns] = {"raw": rep["raw"]["commit"], "as_of": rep["as_of"],
                            "gates": rep["summary"].get("gates") or [rep["summary"].get("why_no_verified")],
                            "verified_groups": rep["summary"]["verified_groups"],
                            "vg_groups": rep["summary"]["vg_groups"],
                            "likely_groups": rep["summary"]["likely_groups"],
                            "funnel_cars": rep["funnel_cars"], "completion_top": top}
        for cat, stages in rep["funnel_cars"].items():
            for st, rs in stages.items():
                for r, n in rs.items():
                    out["by_cat"][cat][st][r] += n
                    if st not in ("eligible", "grouped"):
                        out["blocked_by"][f"{st}:{r}" if r else st] += n
        for cat, stages in rep["funnel_cars_hypothetical_if_every_year_closed"]["by_cat"].items():
            for st, rs in stages.items():
                for r, n in rs.items():
                    out["hypothetical_by_cat"][cat][st][r] += n
    out["by_cat"] = {c: {s: dict(r) for s, r in v.items()} for c, v in sorted(out["by_cat"].items())}
    out["hypothetical_by_cat"] = {
        "label": "HYPOTHETICAL: closure and the audit gate assumed with the current candidate state; "
                 "ranks crawler work, never shipped",
        "by_cat": {c: {s: dict(r) for s, r in v.items()} for c, v in sorted(out["hypothetical_by_cat"].items())}}
    out["blocked_by"] = dict(out["blocked_by"].most_common())
    return out


# =================================================================== parity
def client_loop(fleet, payload, cat, seeker, view, fam_id=None, detail=False):
    """A literal, car-by-car transcription of pfRunSearch (radius: none)
    for one seeker; returns (verified, likely) donor counts, or with
    detail=True the {car index: tier} map. Slow; used only to check the
    aggregated counts."""
    s_y, s_mk, s_md = seeker[2], seeker[0], seeker[1]
    c = _cat(payload, cat)
    results = {}
    if c["kind"] == "engine":
        fam = next(f for f in payload["engineFamilies"] if f["id"] == fam_id)
        part = fam["parts"][cat]
        sapp = next((a for a in fam["apps"] if app_matches(a, s_y, s_mk, s_md)), None)
        s_ambig = sapp and sapp[5]
        vgs = [("hand", g) for g in part.get("vg") or []]
        if view == "new":
            vgs += [("oem", g) for g in (((payload.get("oemVg") or {}).get(fam["id"]) or {}).get(cat) or [])]
        for ci, car in enumerate(fleet.cars):
            vy, vmk, vmd = car[2], car[3], car[4]
            if part.get("years") and (vy < part["years"][0] or vy > part["years"][1]):
                continue
            app = next((a for a in fam["apps"] if app_matches(a, vy, vmk, vmd)), None)
            if not app:
                continue
            verdict = engine_verdict(car[7], fam)
            if verdict is False:
                continue
            engine_ok = verdict is True or (verdict is None and bool(app[4]) and not app[5])
            tier, how = "likely", None
            if engine_ok and not app[5] and not s_ambig:
                for kind, g in vgs:
                    if any(app_matches(sp, s_y, s_mk, s_md) for sp in g) and \
                            any(app_matches(sp, vy, vmk, vmd) for sp in g):
                        tier, how = "verified", kind
                        break
            if cat == "engine-assembly":
                tier = "verified" if (verdict is True and not app[5] and not s_ambig) else "likely"
                how = "hand"
            if tier == "verified" and view == "new" and not donor_identity_ok(car[8], car[1], vy, oem=(how == "oem")):
                tier = "likely"
            results[ci] = tier
    else:
        gs = [(g, False) for g in payload.get("platformGroups") or []]
        if view == "new":
            gs += [(g, True) for g in payload.get("oemGroups") or []]
        for g, oem in gs:
            if g["cat"] != cat or not any(app_matches(a, s_y, s_mk, s_md) for a in g["apps"]):
                continue
            g_tier = _tier(g, view, oem)
            for ci, car in enumerate(fleet.cars):
                if not any(app_matches(a, car[2], car[3], car[4]) for a in g["apps"]):
                    continue
                if results.get(ci) == "verified":
                    continue
                tier = g_tier
                if tier == "verified" and view == "new" and not donor_identity_ok(car[8], car[1], car[2], oem=oem):
                    tier = "likely"
                results[ci] = tier
        s_key = squash_model(s_md, s_mk)
        sw = gen_window(_gen_map(payload), s_mk, s_md, s_y)
        tokens = [t.lower() for t in c.get("tokens") or []]
        for ci, car in enumerate(fleet.cars):
            if ci in results or car[3] != s_mk or squash_model(car[4], car[3]) != s_key:
                continue
            ps = car[6]
            row = part_row(fleet.part_sets[ps] if isinstance(ps, int) and 0 <= ps < len(fleet.part_sets) else [],
                           tokens)
            win = parse_fits(row.get("fits")) if row else None
            if win and win[0] <= s_y <= win[1]:
                results[ci] = "likely"
            elif sw and sw[0] <= car[2] <= sw[1]:
                results[ci] = "likely"
    if detail:
        return results
    nv = sum(1 for t in results.values() if t == "verified")
    return nv, len(results) - nv


def parity(fleet, payload, views: dict, seekers) -> list:
    out = []
    for cat, S, fam in seekers:
        for view, res in views.items():
            got = res[cat].per_seeker.get((S, fam) if fam else S)
            want = client_loop(fleet, payload, cat, S, view, fam)
            out.append({"cat": cat, "seeker": list(S), "family": fam, "view": view,
                        "aggregated": list(got) if got else None, "client_loop": list(want),
                        "ok": got is not None and tuple(got) == want})
    return out


# ===================================================================== main
def load_payloads(before_path, groups_dir):
    if before_path:
        before = json.loads(Path(before_path).read_text())
    else:
        before = json.loads(subprocess.run(["git", "-C", str(REPO), "show", "HEAD:docs/data/interchange.json"],
                                           check=True, capture_output=True, text=True).stdout)
    sys.path.insert(0, str(HERE.parent))
    import junkyard_scraper as js  # noqa: E402
    saved = js.OEM_GROUPS_DIR
    js.OEM_GROUPS_DIR = Path(groups_dir)
    try:
        after = js.build_interchange_payload()
    finally:
        js.OEM_GROUPS_DIR = saved
    return before, after


def table_md(cov: dict) -> str:
    lines = ["| category | kind | M-car before (old) | before (new) | after (new) | M-local after | M-pairs after |",
             "|---|---|---|---|---|---|---|"]
    for cat, row in cov["categories"].items():
        bo, bn, an = row["before_old"], row["before_new"], row["after_new"]
        lines.append(f"| {cat} | {an['kind']} | {bo['m_car']:,} ({bo['m_car_share']:.1%}) | {bn['m_car']:,} | "
                     f"{an['m_car']:,} ({an['m_car_share']:.1%}) | {an['m_local']:,} | {an['m_pairs']:.3f} |")
    return "\n".join(lines) + "\n"


def run(inv, extras, before, after, report_dir: Path | None, with_parity: bool = False,
        parity_seekers=None) -> dict:
    fleet = Fleet(inv, extras)
    res = {"before_old": measure(fleet, before, "old"), "before_new": measure(fleet, before, "new"),
           "after_old": measure(fleet, after, "old"), "after_new": measure(fleet, after, "new")}
    cats = {}
    for c in after.get("categories") or []:
        cid = c["id"]
        row = {}
        for k, r in res.items():
            d = r[cid].out(c.get("kind"))
            if getattr(r[cid], "note", None):
                d["note"] = r[cid].note
            if hasattr(r[cid], "engine_unknown"):
                d["engine_unknown_seekers"] = r[cid].engine_unknown
            row[k] = d
        cats[cid] = row
    cov = {"inventory_scraped_at": inv.get("scrapedAt"), "cars": len(fleet.cars),
           "method": "CURATION_SPEC.md §10.1: every lot car is a seeker for its own (make, model, year) "
                     "and, on engine kinds, its decoded engine family; donors are the other lot cars; tiers "
                     "from a Python port of docs/app.js pfRunSearch (view old = main today, view new = P0 "
                     "guards + Phase 1 OEM keys)",
           "views": {"before": "HEAD docs/data/interchange.json", "after": "build_interchange_payload() with groups/",
                     "old": "client on main (platform tier fails open, no OEM keys, no identity guard)",
                     "new": "P0.1 tier guard + P0.4 pfDonorIdentity + oemGroups/oemVg (spec 7.4)"},
           "after_oem_status": after.get("oemStatus") or {},
           "categories": cats,
           "flips_before_new_to_after_new": flips(fleet, res["before_new"], res["after_new"]),
           "flips_before_old_to_after_old": {c: {k: {"key_pairs": v["key_pairs"], "car_pairs": v["car_pairs"]}
                                                 for k, v in d.items() if k != "lever_attribution"}
                                             for c, d in flips(fleet, res["before_old"], res["after_old"]).items()}}
    if report_dir is not None and Path(report_dir).is_dir():
        cov["oem_funnel"] = funnel_from_reports(Path(report_dir))
    else:
        cov["oem_funnel"] = {"skipped": f"no report directory {report_dir} (run curate.py first)"}
    if with_parity:
        cov["parity"] = parity(fleet, after, {"old": res["after_old"], "new": res["after_new"]},
                               parity_seekers or DEFAULT_PARITY)
    return cov


# the backend e2e's three alternator seekers (backend/test/part_finder_e2e.py)
# plus one body seeker
DEFAULT_PARITY = [("alternator", ("Toyota", "Camry", 2005), "toyota-2az"),
                  ("alternator", ("Ford", "F-150", 1999), None),
                  ("side-mirrors", ("Toyota", "Camry", 2009), None)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--groups", default=str(HERE / "groups"))
    ap.add_argument("--reports", default=None, help="curate.py report dir (default <groups>/_report)")
    ap.add_argument("--before", default=None, help="interchange.json (default: git show HEAD:...)")
    ap.add_argument("--inventory", default=str(DATA / "inventory_live.json"))
    ap.add_argument("--extras", default=str(DATA / "vehicle_extras.json"))
    ap.add_argument("--out", default=None, help="coverage json (default <reports>/coverage-YYYY-MM-DD.json)")
    ap.add_argument("--parity", action="store_true")
    a = ap.parse_args(argv)
    inv_p = Path(a.inventory)
    if not inv_p.exists():
        print(f"SKIP measure: {inv_p} absent (rule 8: nothing measured)", file=sys.stderr)
        return 3
    inv = json.loads(inv_p.read_text())
    extras = json.loads(Path(a.extras).read_text()) if Path(a.extras).exists() else None
    if extras is None:
        print(f"note: {a.extras} absent; every engine verdict is 'no data'", file=sys.stderr)
    before, after = load_payloads(a.before, a.groups)
    reports = Path(a.reports) if a.reports else Path(a.groups) / "_report"
    seekers = DEFAULT_PARITY
    if a.parity:
        # F-150 1999 alternator: pick its family from the payload (the first offered)
        f150 = next((f["id"] for f in after["engineFamilies"] if "alternator" in f["parts"] and any(
            app_matches(x, 1999, "Ford", "F-150") for x in f["apps"])), None)
        seekers = [(c, s, f150 if (c, s) == ("alternator", ("Ford", "F-150", 1999)) else fam)
                   for c, s, fam in DEFAULT_PARITY]
    cov = run(inv, extras, before, after, reports, a.parity, seekers)
    day = str(inv.get("scrapedAt") or "")[:10] or "undated"
    out = Path(a.out) if a.out else reports / f"coverage-{day}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cov, sort_keys=True, indent=1, ensure_ascii=False, default=str) + "\n")
    print(table_md(cov))
    if a.parity:
        bad = [p for p in cov["parity"] if not p["ok"]]
        for p in cov["parity"]:
            print(f"parity {'ok  ' if p['ok'] else 'FAIL'} {p['cat']} {p['seeker']} {p['family']} {p['view']}: "
                  f"aggregated {p['aggregated']} client loop {p['client_loop']}")
        if bad:
            return 1
    print(f"wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
