"""round4_census.py NS RAW INVENTORY DECODES EXTRAS GROUPS_JSON REPLAY_JSON OUT_JSON

Census of the hub's round-4 classes (ops/interchange.md, 2026-11-19; the
independent nissan check groups/_report/nissan_verify_2026-11-19d.json) over
every shippable Likely group of GROUPS_JSON, judged on the raw with curate.py's
own detectors (curated in-process with the given pins; the detectors run with
their policy flags on whatever GROUPS_JSON was built with) and on the pinned
lot as the app shows it (REPLAY_JSON from lot_replay.mjs). Read-only; no fetch.

  1 sibling  T's page lists another number of the same part and position for
             the same option clause plus a drive word (Curation.drive_sibling):
             the app-year's gate does not rule that drive out; plain lot cars
             of T decoded in the excluded family are counted
  2 window   this number's own rows on T's page print a window that leaves
             part of the model year out and a dated row of the same part that
             is not its predecessor/successor carries the rest
             (Curation.build_window kind 'unlinked', src 'page'); the gate has
             no 'built'; plain lot cars of T are counted (no decode gives the
             build month). 'edge' = 1-2 months at a model-year edge
  3 pages    T's page prints no date and another model-year page of the same
             catalog model prints a window (src 'other_page'): 'drop' (under
             5 months of the model year) or 'unlinked'; plain cars counted
  4 vin      (lot side, every group) plain rows of cars whose VIN decode names
             another make or model year than the listing (vpicMismatch, the
             vpic side table's 5th field)
"""
import collections
import json
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

FOUR = {"4wd", "awd", "a4wd"}


def car_drive(s):
    s = str(s or "").lower()
    four = any(w in s for w in ("4wd", "4x4", "awd", "all-wheel", "4-wheel", "all wheel"))
    two = any(w in s for w in ("2wd", "4x2", "fwd", "rwd", "front-wheel", "rear-wheel", "front wheel", "rear wheel"))
    return "4" if four and not two else "2" if two and not four else ""


def main(argv):
    ns, raw, invp, decp, exp, gpath, rpath, outp = argv[1:9]
    mm = MM.ModelMap(MM.load(str(MM.MODEL_MAP_PATH)))
    inv = MM.load_inventory(invp)
    cur, _doc = C.curate(ns, A.RawSource(ref=raw), C.Options(
        model_map=mm, model_map_path=MM.MODEL_MAP_PATH, inventory=inv, js=js,
        lot_engines=C.lot_engines(inv, exp), model_bodies=C.model_bodies(inv, js, decp),
        body_counts=C.model_body_counts(inv, js, decp)))
    policy.LIKELY_DRIVE_SIBLING_RULE = True
    policy.LIKELY_BUILD_WINDOW_RULE = True
    hold = set(js.GROUP_HOLD_CATS)
    doc = json.loads(Path(gpath).read_text())
    live = [g for g in doc["likely"] if g["cat"] not in hold]
    replay = json.loads(Path(rpath).read_text())
    V = inv["vehicles"]
    vp = inv.get("vpic") or {}
    byk = {(cat, tuple(sorted(c.pns))): c for (_k, cat), c in cur.classes.items()}

    def gate_of(g, T):
        for x in g.get("gates") or []:
            if (x[0], x[1]) == (T[0], T[1]) and x[2] <= T[2] <= x[3]:
                return x[4]
        return {}

    def sq(s):
        return "".join(ch for ch in str(s or "").lower() if ch.isalnum())

    def matches(T, i):
        v = V[i]
        mk, md = js.canonical_make(v[3]) if hasattr(js, "canonical_make") else v[3], v[4]
        sm = sq(md)
        smk = sq(v[3])
        if smk and sm.startswith(smk) and len(sm) > len(smk):
            sm = sm[len(smk):]
        if sm.endswith("pickup") and len(sm) > 6:
            sm = sm[:-6]
        return v[2] == T[2] and sq(T[1]) in {sm, sq(md)}

    def plain(g, T):
        return [i for i in (replay.get(g["id"]) or {}).get("plain", []) if matches(T, i)]

    found = {k: [] for k in ("sibling", "window", "pages", "window_linked", "window_no_other_row")}
    for g in live:
        c = byk.get((g["cat"], tuple(sorted(g["pn"]))))
        if c is None:
            continue
        Ts = sorted({(mk, a[1], y) for a in g["apps"] for mk in a[0].split("|") for y in range(a[2], a[3] + 1)})
        for T in Ts:
            gate = gate_of(g, T)
            lim = cur.drive_sibling_limit(c, g["cat"], T)
            if lim:
                _u, hits = cur.drive_sibling(c, g["cat"], T)
                kind, cls = lim
                gd = set((gate.get("drive") or "").split("/")) - {""}
                handled = bool(gd) and (kind == "drive" and gd <= set(cls or ())) or \
                    (kind == "drive_not" and set(cls or ()) <= set((gate.get("drive_not") or "").split("/")))
                ps = plain(g, T)
                excl_fam = "4" if (kind == "drive" and cls and not (set(cls) & FOUR)) or kind == "drive_not" else "2"
                bad = [i for i in ps if car_drive((vp.get(str(i)) or ["", "", "", ""])[3]) == excl_fam]
                found["sibling"].append({
                    "id": g["id"], "cat": g["cat"], "pn": g["pn"], "T": T, "limit": [kind, sorted(cls or [])],
                    "gate": gate, "handled": handled, "plain_cars_T": len(ps), "plain_contra": 0 if handled else len(bad),
                    "hits": sorted({f"{h[0].pn} '{' '.join(h[0].notes)[:80]}' vs {h[1].pn} '{' '.join(h[1].notes)[:80]}'"
                                    for h in hits})[:4]})
            w = cur.build_window(c, g["cat"], T)
            if w and w.get("kind") not in (None, "full"):
                ps = plain(g, T)
                rec = {"id": g["id"], "cat": g["cat"], "pn": g["pn"], "T": T, "kind": w["kind"], "src": w["src"],
                       "window": C._win_label(w["wins"]), "gap_months": sum(b - a + 1 for a, b in w["gap"]),
                       "edge": w["edge"], "others": [[p, C._win_label(list(ws)), lk] for p, ws, lk in w["others"]][:6],
                       "gate": gate, "handled": "built" in gate, "plain_cars_T": len(ps),
                       "plain_contra": 0 if "built" in gate else len(ps)}
                if w["src"] == "other_page" and w["kind"] in ("drop", "unlinked"):
                    found["pages"].append(rec)
                elif w["kind"] == "unlinked":
                    found["window"].append(rec)
                elif w["kind"] == "linked":
                    found["window_linked"].append(rec)
                else:
                    found["window_no_other_row"].append(rec)
    # class 4, lot side: every replayed group of this ns
    mism = {i for i in range(len(V)) if (vp.get(str(i)) or ["", "", "", "", ""])[4:5] and (vp.get(str(i)) or [""] * 5)[4]}
    gids = {g["id"] for g in live}
    vin_pairs = [(gid, i) for gid, r in replay.items() if gid in gids for i in r.get("plain", []) if i in mism]
    summ = {}
    for k, xs in found.items():
        summ[k] = {"groups": len({x["id"] for x in xs}), "app_years": len(xs),
                   "unhandled_app_years": sum(1 for x in xs if not x["handled"]),
                   "plain_contra": sum(x["plain_contra"] for x in xs)}
        if k in ("window", "pages"):
            summ[k]["edge_app_years"] = sum(1 for x in xs if x.get("edge"))
            summ[k]["by_kind"] = dict(collections.Counter(x["kind"] for x in xs))
    summ["vin"] = {"plain_pairs": len(vin_pairs), "cars": len({i for _g, i in vin_pairs}),
                   "groups": len({g for g, _i in vin_pairs})}
    out = {"ns": ns, "raw": raw, "groups_file": gpath, "live_groups": len(live), "summary": summ, "found": found,
           "vin_cars": sorted({(V[i][1], V[i][2], V[i][3], V[i][4], (vp.get(str(i)) or [""] * 5)[4]) for _g, i in vin_pairs})}
    Path(outp).write_text(json.dumps(out, indent=1, default=list))
    print(ns, len(live), json.dumps(summ))


if __name__ == "__main__":
    main(sys.argv)
