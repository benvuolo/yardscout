#!/usr/bin/env python3
"""CURATION_SPEC.md §9 test_oracle (V13): over 200 seeded random catalogs,
- soundness: every shipped Verified pair is a pair of a deliberately naive
  oracle that evaluates §2 (Phase 1) straight from the generated catalog;
- removing any manifest, record or manifest row never adds a Verified pair;
- adding a candidate that is not in an existing chain never adds one;
- adding a restricting note clause never adds one;
- adding a record never removes a supersession edge, so a number whose
  printed successor is known only in another category stays blocked
  (review F5: a cross-category edge was dropped, unblocking the cell).
N_CATALOGS can be lowered for a quick run: python3 test_oracle.py 40"""
import copy
import random
import sys

from _util import TOY, check, confirmed, done, list_manifest, run, toyota_record, year_manifest
import curate as C

N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
PSHA = C.policy_sha256()
ST = confirmed((TOY, "headlights"), policy_sha=PSHA)
MODELS = {"Camry": (["CE", "LE", "SE"], ["4 Cyl 2.4 L GAS"]),
          "Corolla": (["CE", "LE", "S"], ["4 Cyl 1.8 L GAS"]),
          "Avalon": (["XL", "XLS"], ["6 Cyl 3.0 L GAS"])}
YEARS = [2005, 2006, 2007]
UNIV = [(md, y) for md in MODELS for y in YEARS]
SUB = "headlights-lighting/headlamps"


def gen(rnd):
    """A random catalog as plain data (the oracle reads this, curate reads raw)."""
    parts = []
    # headlamps come in L/R pairs that share their fitment rows; a few noise
    # parts (one side, partial trims) make splits and conditions
    for d in range(rnd.randint(1, 3)):
        rows = []
        for md in rnd.sample(list(MODELS), rnd.randint(1, 2)):
            lo = rnd.choice(YEARS)
            hi = rnd.choice([y for y in YEARS if y >= lo])
            trims = MODELS[md][0] if rnd.random() < 0.85 else rnd.sample(MODELS[md][0], len(MODELS[md][0]) - 1)
            rows.append((lo, hi, md, sorted(trims)))
        for side in ("L", "R"):
            parts.append({"pn": f"8{1 if side == 'L' else 2}{110 + d}-0R{rnd.randint(100, 999)}", "side": side,
                          "rows": list(rows), "replaces": []})
    for i in range(rnd.choice([0, 0, 1, 2])):
        md = rnd.choice(list(MODELS))
        y = rnd.choice(YEARS)
        trims = MODELS[md][0] if rnd.random() < 0.5 else MODELS[md][0][:1]
        parts.append({"pn": f"81{150 + i}-0N{rnd.randint(100, 999)}", "side": rnd.choice(["L", "R"]),
                      "rows": [(y, y, md, sorted(trims))], "replaces": []})
    seen = set()
    for p in parts:      # unique pns
        while p["pn"] in seen:
            p["pn"] = p["pn"][:-1] + str(rnd.randint(0, 9))
        seen.add(p["pn"])
    for i, p in enumerate(parts):
        same = [q for q in parts[:i] if q["side"] == p["side"]]
        if same and rnd.random() < 0.15:
            p["replaces"] = [rnd.choice(same)["pn"]]
    closed = [T for T in UNIV if rnd.random() < 0.85]
    listed, notes = {}, {}
    for T in closed:
        md, y = T
        lst = [p["pn"] for p in parts if covers(p, T) and rnd.random() < 0.97]
        if rnd.random() < 0.05:
            lst.append(rnd.choice(parts)["pn"])
        listed[T] = sorted(set(lst))
        for pn in listed[T]:
            if rnd.random() < 0.06:
                notes[(T, pn)] = ["US Built"]
    recorded = {p["pn"] for p in parts if rnd.random() < 0.98}
    return {"parts": parts, "closed": closed, "listed": listed, "notes": notes, "recorded": recorded}


def covers(p, T):
    return any(md == T[0] and lo <= T[1] <= hi for lo, hi, md, _t in p["rows"])


def full_row(p, T):
    return any(md == T[0] and lo <= T[1] <= hi and tr == sorted(MODELS[md][0]) for lo, hi, md, tr in p["rows"])


def to_raw(w):
    recs, lists, years = [], [], []
    for p in w["parts"]:
        if p["pn"] not in w["recorded"]:
            continue
        seed = next(((md, y) for lo, hi, md, _t in p["rows"] for y in range(lo, hi + 1)), ("Camry", 2005))
        side = "Driver Side" if p["side"] == "L" else "Passenger Side"
        fit = [(lo, hi, "Toyota", md, tr, MODELS[md][1]) for lo, hi, md, tr in p["rows"]]
        recs.append(toyota_record(p["pn"], "headlights", ("Toyota", seed[0], seed[1]), SUB, "Headlamp",
                                  "Headlamp Assembly", side, fit, location=[side], replaces=p["replaces"],
                                  replaced_by=p.get("replaced_by")))
    recs += copy.deepcopy(w.get("extra_records") or [])
    by_pn = {p["pn"]: p for p in w["parts"]}
    for T in w["closed"]:
        md, y = T
        seed = ("Toyota", md, y)
        years.append(year_manifest(TOY, seed, f"{y} Toyota {md} Parts", [SUB], MODELS[md][0], MODELS[md][1]))
        rows = []
        for pn in w["listed"].get(T, []):
            side = "Driver Side" if by_pn[pn]["side"] == "L" else "Passenger Side"
            rows.append((pn, "Headlamp", "Headlamp Assembly", w["notes"].get((T, pn), []), [side], True, None))
        lists.append(list_manifest(TOY, seed, "headlights", SUB, rows))
    return {f"raw/{TOY}.jsonl": recs, f"raw/{TOY}.lists.jsonl": lists, f"raw/{TOY}.years.jsonl": years}


def oracle_pairs(w):
    """Naive §2 Phase 1 over every pair of feed vehicle-years."""
    by_pn = {p["pn"]: p for p in w["parts"]}
    succ = {p["pn"]: set() for p in w["parts"]}
    for p in w["parts"]:
        for a in p["replaces"]:
            succ.setdefault(a, set()).add(p["pn"])

    def reach(a):
        seen, st = set(), [a]
        while st:
            x = st.pop()
            for y in succ.get(x, ()):
                if y not in seen:
                    seen.add(y)
                    st.append(y)
        return seen

    def chain_members(pn):
        anc = {q for q in succ if pn in reach(q)}
        return reach(pn) | anc

    def elig(T):
        if T not in w["closed"]:
            return None
        listed = set(w["listed"].get(T, []))
        K = {pn for pn, p in by_pn.items() if covers(p, T)} | listed
        if not K or any(pn not in w["recorded"] for pn in K | listed):
            return None
        if any(m not in w["recorded"] for pn in K for m in chain_members(pn)):
            return None
        sig = {}
        for side in ("L", "R"):
            ks = sorted(pn for pn in K if by_pn[pn]["side"] == side)
            if not ks:
                return None
            if any(not (b in reach(a) or a in reach(b)) for i, a in enumerate(ks) for b in ks[i + 1:]):
                return None
            for pn in ks:
                if pn not in listed or not full_row(by_pn[pn], T) or w["notes"].get((T, pn)):
                    return None
            sig[side] = ks
        return sig
    sigs = {T: elig(T) for T in UNIV}
    return {(a, b) for a in UNIV for b in UNIV if a != b and sigs[a] is not None and sigs[a] == sigs[b]}


def shipped(w, with_cur=False):
    cur, doc = run("toyota", to_raw(w), status_table=ST)
    out = set()
    for g in doc["groups"]:
        ts = [(y["t"][1], y["t"][2]) for y in g["years"]]
        out |= {(a, b) for a in ts for b in ts if a != b}
    return (out, cur) if with_cur else out


def edges_of(cur):
    return {(c, e) for c, es in cur.edges.items() for e in es}


rnd = random.Random(20261105)
rnd5 = random.Random(5)
unsound, grow_rm, grow_add, grow_note, edge_lost, grow_xcat = [], [], [], [], [], []
nonempty = tot_s = tot_o = 0
for i in range(N):
    w = gen(rnd)
    s = shipped(w)
    o = oracle_pairs(w)
    tot_s += len(s)
    tot_o += len(o)
    if s:
        nonempty += 1
    if not s <= o:
        unsound.append((i, sorted(s - o)[:3]))
    # removals
    w2 = copy.deepcopy(w)
    kind = rnd.choice(["manifest", "record", "row"])
    if kind == "manifest" and w2["closed"]:
        w2["closed"].remove(rnd.choice(w2["closed"]))
    elif kind == "record" and w2["recorded"]:
        w2["recorded"].discard(rnd.choice(sorted(w2["recorded"])))
    else:
        ts = [T for T in w2["closed"] if w2["listed"].get(T)]
        if ts:
            T = rnd.choice(ts)
            w2["listed"][T] = w2["listed"][T][1:]
    if not shipped(w2) <= s:
        grow_rm.append((i, kind))
    # an added candidate outside every chain
    w3 = copy.deepcopy(w)
    T = rnd.choice(UNIV)
    newp = {"pn": "81999-0Z999", "side": rnd.choice(["L", "R"]),
            "rows": [(T[1], T[1], T[0], sorted(MODELS[T[0]][0]))], "replaces": []}
    w3["parts"].append(newp)
    w3["recorded"].add(newp["pn"])
    if T in w3["closed"]:
        w3["listed"][T] = sorted(set(w3["listed"].get(T, [])) | {newp["pn"]})
    if not shipped(w3) <= s:
        grow_add.append(i)
    # an added restricting note
    w4 = copy.deepcopy(w)
    ts = [T for T in w4["closed"] if w4["listed"].get(T)]
    if ts:
        T = rnd.choice(ts)
        w4["notes"][(T, rnd.choice(w4["listed"][T]))] = ["Japan Built"]
        if not shipped(w4) <= s:
            grow_note.append(i)
    # a printed successor known only in another category (review F5); its own
    # random stream, so the catalogs above stay the ones this test always ran
    if i % 2 == 0:
        w5 = copy.deepcopy(w)
        p = rnd5.choice(w5["parts"])
        p["replaced_by"] = ["81888-0X888"]
        s5, c5 = shipped(w5, with_cur=True)
        w6 = copy.deepcopy(w5)
        T = rnd5.choice(UNIV)
        cat = rnd5.choice(["side-mirrors", "headlights", "tail-lights"])
        nm = {"side-mirrors": ("Mirror Assembly", "Mirror Assy, Outer Rear View, LH"),
              "headlights": ("Headlamp", "Headlamp Assembly"), "tail-lights": ("Tail Lamp", "Lamp Assy, Rear Combination")}[cat]
        w6["extra_records"] = [toyota_record("81888-0X888", cat, ("Toyota", T[0], T[1]), SUB, nm[0], nm[1],
                                             "Driver Side", [(T[1], T[1], "Toyota", T[0], sorted(MODELS[T[0]][0]),
                                                              MODELS[T[0]][1])], location=["Driver Side"])]
        s6, c6 = shipped(w6, with_cur=True)
        if not edges_of(c5) <= edges_of(c6):
            edge_lost.append((i, cat))
        if cat != "headlights" and not s6 <= s5:
            grow_xcat.append((i, cat))

check(f"soundness: shipped pairs are a subset of the naive oracle's on {N} catalogs", not unsound, str(unsound[:3]))
check("removing a manifest, record or manifest row never adds a Verified pair", not grow_rm, str(grow_rm[:5]))
check("adding a candidate outside every chain never adds a Verified pair", not grow_add, str(grow_add[:5]))
check("adding a restricting note clause never adds a Verified pair", not grow_note, str(grow_note[:5]))
check("adding a record never removes a supersession edge (any category)", not edge_lost, str(edge_lost[:5]))
check("a successor recorded only in another category never adds a Verified pair", not grow_xcat, str(grow_xcat[:5]))
check(f"the property test is not vacuous: catalogs ship Verified groups ({nonempty}/{N})", nonempty >= N // 4,
      str(nonempty))
print(f"     shipped something on {nonempty}/{N} catalogs; shipped/oracle pairs {tot_s}/{tot_o}")
done("test_oracle")
