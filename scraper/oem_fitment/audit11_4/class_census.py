"""class_census.py NS RAW INVENTORY DECODES EXTRAS GROUPS_JSON REPLAY_JSON OUT_JSON

Census of the five flaw classes the 2026-11-18c nissan check found
(groups/_report/nissan_verify_2026-11-18c.json), over every shippable Likely
group of GROUPS_JSON, judged on the raw (curate.py's own indexes, curated
in-process with the given pins) and on the pinned lot as the app shows it
(REPLAY_JSON from lot_replay.mjs: which cars are plain / if equipped /
excluded per group id). round3-1119. Read-only; no fetch.

  engine  the class's product-page fitment rows for an app-year (every row
          printing an engine column) leave out a displacement the model-year
          offers (any fitment row of T in any category, or T's year page),
          and the app-year's gate carries no engine limit; plain lot cars of
          T decoded with a left-out displacement are counted
  fuel    a "gas" fuel gate where T's hybrid has a displacement the gas
          engines lack and no engine gate: plain lot cars decoded with it
  market  a km/h (Kph) or other export-market part (record name, description,
          own-page note)
  cab     every fitment trim of the class names a cab (or every own-page row
          of the class codes one, Nissan KC/CC) and the same category on T's
          pages lists a cab the class leaves out under another number, with no
          cab gate; plain lot cars of T whose listing / VIN names the left-out
          cab are counted (no decoded field holds the cab)
  body    the same for body words in the fitment trims (coupe, sedan, wagon,
          hatchback, convertible); plain lot cars decoded with the left-out body
  joined  a drive token joined to other letters (2WDSTD, 2WDHICAS) in the
          class's own-page option column or fitment trims, the app-year carrying
          no drive gate; plain lot cars decoded with the other drive family
"""
import collections
import gzip
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scraper" / "oem_fitment"))
sys.path.insert(0, str(REPO / "scraper"))
import adapters as A  # noqa: E402
import curate as C  # noqa: E402
import model_map as MM  # noqa: E402
import policy  # noqa: E402
import junkyard_scraper as js  # noqa: E402

LIT_RE = re.compile(r"(?<![0-9.])(\d{1,2}\.\d)\s*L(?![A-Za-z])", re.I)
HYB_RE = re.compile(r"HYBRID|\bFHEV\b|\bHEV\b|\bPHEV\b|PLUG-IN", re.I)
MARKET_RE = re.compile(r"\bkph\b|\bkm\s*/\s*h\b|\bkmh\b|kilomet|\bmetric\b|\bcanad|\bexport|\bmexic|\beurop|\bgcc\b|"
                       r"australia|\bjdm\b|\bright[\s-]hand[\s-]drive\b|\brhd\b|\bgeneral\s+market\b|\bnon[\s-]?us\b|"
                       r"\bexc(?:ept)?\.?\s*u\.?s\.?a?\b|\bnot\s+for\s+u\.?s", re.I)
JOINED_RE = re.compile(r"(?<![A-Z0-9-])(?:2WD|4WD|AWD|FWD|RWD|4X4|4X2)(?=[A-Z])|(?<=[A-Z])(?:2WD|4WD|AWD|FWD|RWD)(?![A-Z0-9])")
BODY_WORDS = {"coupe": "coupe", "sedan": "sedan", "notchback": "sedan", "wagon": "wagon", "hatchback": "hatchback",
              "convertible": "convertible", "liftback": "hatchback"}
BODY_RE = re.compile(r"\b(" + "|".join(BODY_WORDS) + r")\b", re.I)
SIL = {"sedan": "sedan", "coupe": "coupe", "hatchback": "hatchback", "wagon": "wagon", "convertible": "convertible"}


def lits(strings):
    out = set()
    for s in strings:
        out |= {round(float(x), 1) for x in LIT_RE.findall(str(s or ""))}
    return out


def has(xs, x):
    return any(abs(x - y) < 0.05 for y in xs)


def car_lit(ex, ei):
    # docs/app.js pfAmParseEngine's displacement
    s = str(ex[ei] if ex and len(ex) > ei and ex[ei] else "").lower()
    m = re.search(r"(\d+\.\d+)\s*l\b", s) or re.search(r"(\d+\.\d+)l", s)
    return round(float(m.group(1)), 1) if m else None


def main(argv):
    ns, raw, invp, decp, exp, gpath, rpath, outp = argv[1:9]
    mm = MM.ModelMap(MM.load(str(MM.MODEL_MAP_PATH)))
    inv = MM.load_inventory(invp)
    cur, _doc = C.curate(ns, A.RawSource(ref=raw), C.Options(
        model_map=mm, model_map_path=MM.MODEL_MAP_PATH, inventory=inv, js=js,
        model_bodies=C.model_bodies(inv, js, decp), body_counts=C.model_body_counts(inv, js, decp)))
    hold = set(js.GROUP_HOLD_CATS)
    doc = json.loads(Path(gpath).read_text())
    live = [g for g in doc["likely"] if g["cat"] not in hold]
    replay = json.loads(Path(rpath).read_text())
    exd = json.loads(Path(exp).read_text())
    extras, ef = exd["extras"], exd["extraFields"]
    ei, bi = ef.index("engine"), ef.index("body")
    V = inv["vehicles"]
    vp = inv.get("vpic") or {}
    byk = {(cat, tuple(sorted(c.pns))): c for (_k, cat), c in cur.classes.items()}

    def car(i):
        v = V[i]
        ex = extras.get(str(v[0]))
        p = vp.get(str(i)) or ["", "", "", "", ""]
        return {"i": i, "vin": v[1], "year": v[2], "make": v[3], "model": v[4], "lit": car_lit(ex, ei),
                "body": (ex[bi] if ex and len(ex) > bi else None), "drive": p[3] or "",
                "name": " ".join(x for x in (v[4], p[2], p[0] if p[1] == "usable" else "") if x)}

    _ts = {}

    def Tset(g):
        if g["id"] not in _ts:
            _ts[g["id"]] = {(mk, a[1], y) for a in g["apps"] for mk in a[0].split("|") for y in range(a[2], a[3] + 1)}
        return _ts[g["id"]]

    def gate_of(g, T):
        for x in g.get("gates") or []:
            if (x[0], x[1]) == (T[0], T[1]) and x[2] <= T[2] <= x[3]:
                return x[4]
        return {}

    def sq(s):
        return re.sub(r"[^a-z0-9]", "", str(s or "").lower())

    def sqm(model, make):
        sm, mk = sq(model), sq(make)
        if mk and sm.startswith(mk) and len(sm) > len(mk):
            sm = sm[len(mk):]
        if sm.endswith("pickup") and len(sm) > 6:
            sm = sm[:-6]
        return sm

    def matches(T, cr):
        # docs/app.js pfAppMatches for one app-year (no '*' apps in OEM groups)
        return cr["year"] == T[2] and sq(T[1]) in {sqm(cr["model"], cr["make"]), sqm(cr["model"], "")}

    def plain_cars(g, T):
        return [cr for i in (replay.get(g["id"]) or {}).get("plain", []) for cr in [car(i)] if matches(T, cr)]

    # T -> displacements the model-year offers: every fitment row of T (any
    # category) and T's year page; hybrid displacements separately
    U, UH, UG = {}, {}, {}
    for T, lst in cur.rows_by_T.items():
        es = [e for (_cat, _c, _r, f, _t) in lst for e in (f.engines or [])]
        U[T] = lits(es)
        UH[T] = lits([e for e in es if HYB_RE.search(e)])
        UG[T] = lits([e for e in es if not HYB_RE.search(e)])
    for T, yms in cur.t_years.items():
        es = [e for ym in yms for e in (ym.engines or [])]
        U.setdefault(T, set()).update(lits(es))
        UH.setdefault(T, set()).update(lits([e for e in es if HYB_RE.search(e)]))
        UG.setdefault(T, set()).update(lits([e for e in es if not HYB_RE.search(e)]))

    found = {k: [] for k in ("engine", "fuel", "market", "cab", "body", "joined")}
    for g in live:
        c = byk.get((g["cat"], tuple(sorted(g["pn"]))))
        if c is None:
            continue
        # market: once per group
        texts = []
        for r in c.records:
            texts += [r.name, r.aux, r.description, r.other_names] + list(r.note_texts or [])
        hit = sorted({m.group(0) for t in texts for m in MARKET_RE.finditer(str(t or ""))})
        if hit:
            found["market"].append({"id": g["id"], "cat": g["cat"], "pn": g["pn"], "apps": g["apps"], "hits": hit,
                                    "texts": [t for t in texts if t and MARKET_RE.search(str(t))][:4],
                                    "plain_cars": len((replay.get(g["id"]) or {}).get("plain", []))})
        for T in sorted(Tset(g)):
            gate = gate_of(g, T)
            fit = [f for (cc, _r, f, _t) in cur.t_rows.get((T, g["cat"]), []) if cc is c]
            own = cur._own_rows(c, g["cat"], T)
            pcs = None
            # ---- engine column
            L = None
            if fit and all(lits(f.engines) for f in fit):
                L = set().union(*[lits(f.engines) for f in fit])
            if L:
                miss = {x for x in U.get(T, set()) if not has(L, x)}
                if miss and not gate.get("eng"):
                    pcs = plain_cars(g, T) if pcs is None else pcs
                    bad = [cr for cr in pcs if cr["lit"] is not None and not has(L, cr["lit"])]
                    found["engine"].append({
                        "id": g["id"], "cat": g["cat"], "pn": g["pn"], "T": T, "listed": sorted(L),
                        "missing": sorted(miss), "gate": gate,
                        "plain_contra": len(bad), "plain_contra_in_U": sum(1 for cr in bad if has(U[T], cr["lit"])),
                        "cars": [[cr["vin"], cr["lit"]] for cr in bad][:12]})
            # ---- fuel: gas gate, hybrid with its own displacement, no engine gate
            if gate.get("fuel") == "gas" and not gate.get("eng"):
                hy = {x for x in UH.get(T, set()) if not has(UG.get(T, set()), x)}
                pcs = plain_cars(g, T) if pcs is None else pcs
                bad = [cr for cr in pcs if cr["lit"] is not None and has(hy, cr["lit"])]
                found["fuel"].append({"id": g["id"], "cat": g["cat"], "pn": g["pn"], "T": T, "gate": gate,
                                      "hybrid_only_disp": sorted(hy), "gas_disp": sorted(UG.get(T, set())),
                                      "plain_contra": len(bad), "cars": [[cr["vin"], cr["lit"]] for cr in bad][:12]})
            # ---- cab list
            ours, all_cab = set(), bool(fit)
            for f in fit:
                for tr in (f.trims or []):
                    m = C.Curation._CAB_RE.search(tr)
                    if m:
                        ours.add(re.sub(r"\s+", " ", m.group(1).lower()))
                    else:
                        all_cab = False
                if not f.trims:
                    all_cab = False
            page = set()
            for (cc, _r, f, _t) in cur.t_rows.get((T, g["cat"]), []):
                if cc is c:
                    continue
                for tr in (f.trims or []):
                    m = C.Curation._CAB_RE.search(tr)
                    if m:
                        page.add(re.sub(r"\s+", " ", m.group(1).lower()))
            src = "fitment trims"
            if not (all_cab and ours):
                codes = C._fvo_cab_codes([n for notes, _s, _v, _u in own for n in notes]) if own else None
                if codes:
                    ours, all_cab, src = set(codes), True, "own-page KC/CC"
                    page = set()
                    for lr in cur.t_list_rows.get((T, g["cat"]), []):
                        if policy.pn_key(ns, lr.pn) != c.key:
                            k = C._fvo_cab_codes(lr.notes)
                            page |= set(k or ())
            if all_cab and ours and (page - ours) and not gate.get("cab"):
                pcs = plain_cars(g, T) if pcs is None else pcs
                left = page - ours
                bad = [cr for cr in pcs if any(re.search(r"\b" + re.escape(x) + r"\b", cr["name"], re.I) for x in left)]
                found["cab"].append({"id": g["id"], "cat": g["cat"], "pn": g["pn"], "T": T, "src": src,
                                     "ours": sorted(ours), "page_other": sorted(left), "gate": gate,
                                     "plain_cars_T": len(pcs), "plain_contra": len(bad)})
            # ---- body list (silhouette words in fitment trims)
            ob, all_b = set(), bool(fit)
            for f in fit:
                for tr in (f.trims or []):
                    ws = {BODY_WORDS[w.lower()] for w in BODY_RE.findall(tr)}
                    if ws:
                        ob |= ws
                    else:
                        all_b = False
                if not f.trims:
                    all_b = False
            pb = set()
            for (cc, _r, f, _t) in cur.t_rows.get((T, g["cat"]), []):
                if cc is not c:
                    for tr in (f.trims or []):
                        pb |= {BODY_WORDS[w.lower()] for w in BODY_RE.findall(tr)}
            if all_b and ob and (pb - ob) and not gate.get("body"):
                pcs = plain_cars(g, T) if pcs is None else pcs
                left = pb - ob
                bad = [cr for cr in pcs if SIL.get(str(cr["body"] or "")) in left]
                found["body"].append({"id": g["id"], "cat": g["cat"], "pn": g["pn"], "T": T, "ours": sorted(ob),
                                      "page_other": sorted(left), "gate": gate, "plain_cars_T": len(pcs),
                                      "plain_contra": len(bad), "cars": [[cr["vin"], cr["body"]] for cr in bad][:8]})
            # ---- joined drive tokens
            jt = set()
            for notes, _s, _v, _u in own:
                for n in notes:
                    jt |= {m.group(0) for m in JOINED_RE.finditer(str(n).upper())}
            for f in fit:
                for tr in list(f.trims or []) + list(f.options or []):
                    jt |= {m.group(0) for m in JOINED_RE.finditer(str(tr).upper())}
            if jt and not gate.get("drive"):
                pcs = plain_cars(g, T) if pcs is None else pcs
                found["joined"].append({"id": g["id"], "cat": g["cat"], "pn": g["pn"], "T": T, "tokens": sorted(jt),
                                        "drive_of": sorted(d) if isinstance(d := cur.drive_of(c, g["cat"], T), frozenset) else d,
                                        "own_notes": [n for notes, *_ in own for n in notes][:3],
                                        "plain_cars_T": len(pcs),
                                        "drives": dict(collections.Counter(cr["drive"] for cr in pcs))})
    summ = {}
    for k, xs in found.items():
        summ[k] = {"groups": len({x["id"] for x in xs}),
                   "app_years": len({(x["id"], tuple(x["T"])) for x in xs}) if xs and "T" in xs[0] else len(xs),
                   "plain_contra": sum(x.get("plain_contra", 0) for x in xs)}
    out = {"ns": ns, "raw": raw, "groups_file": gpath, "live_groups": len(live), "summary": summ, "found": found}
    Path(outp).write_text(json.dumps(out, indent=1, default=list))
    print(ns, len(live), json.dumps(summ))


if __name__ == "__main__":
    main(sys.argv)
