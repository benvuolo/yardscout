"""live_diff.py OLD_DIR NEW_DIR NS [NS...]: claim diff of groups/<ns>.json between
two directories, per (category, pn): REMOVED / ADDED / CHANGED (app-years lost
and gained, old and new note). Held categories (junkyard_scraper.GROUP_HOLD_CATS)
are marked HELD (never shipped). Read-only; no fetch.

Per-app gates (round3-1119): a gate narrows a claim (the app hides donors it
rules out), so an app-year kept in both files is compared gate to gate:
GATE-NARROWED when the new gate holds every old limit at least as tightly and
adds or tightens one, GATE-WIDENED when it drops or loosens one (an added
claim, like a gained app-year). A NS given as OLD=NEW reads OLD_DIR/OLD.json
against NEW_DIR/NEW.json (the nissan candidate). The last lines are a
per-namespace summary of LIVE groups; "added claims" counts added groups'
app-years, gained app-years and widened gates, and must be 0 for a
claims-only-down change."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scraper"))
import junkyard_scraper as js  # noqa: E402

HOLD = set(js.GROUP_HOLD_CATS)


def yrs(g):
    return {(a[0], a[1], y) for a in g["apps"] for y in range(a[2], a[3] + 1)}


def gates_by_year(g):
    out = {}
    for mk, md, lo, hi, gate in g.get("gates") or []:
        for y in range(lo, hi + 1):
            out[(mk, md, y)] = gate
    return out


def _as_set(v):
    return set(v) if isinstance(v, list) else {v}


def _drive_set(d):
    """The classes a drive gate lets through ('2wd' is FWD or RWD)."""
    s = set(str(d).split("/"))
    if "2wd" in s:
        s |= {"fwd", "rwd"}
    return s


def gate_cmp(old, new):
    """'same' | 'narrowed' | 'widened' for one app-year's gates (None = no gate)."""
    old, new = old or {}, new or {}
    if old == new:
        return "same"
    for k, v in old.items():
        if k == "drive_basis":
            continue
        if k not in new:
            return "widened"
        w = new[k]
        if k == "drive":
            if not _drive_set(w) <= _drive_set(v):
                return "widened"
        elif k == "eng":
            if not all(any(abs(float(x[:-1]) - float(y[:-1])) < 0.05 for y in v) for x in w):
                return "widened"
        elif k in ("cab", "body"):
            if not _as_set(w) <= _as_set(v):
                return "widened"
        elif v != w:
            return "widened"
    return "narrowed"


def main(argv):
    old, new = Path(argv[1]), Path(argv[2])
    summary = []
    for spec in argv[3:]:
        ons, nns = spec.split("=") if "=" in spec else (spec, spec)
        ns = nns
        a = {(g["cat"], tuple(g["pn"])): g for g in json.loads((old / f"{ons}.json").read_text())["likely"]}
        b = {(g["cat"], tuple(g["pn"])): g for g in json.loads((new / f"{nns}.json").read_text())["likely"]}
        s = {"removed": 0, "added": 0, "changed": 0, "lost_years": 0, "gained_years": 0,
             "narrowed": 0, "widened": 0, "added_years": 0}
        for k in sorted(set(a) | set(b)):
            ga, gb = a.get(k), b.get(k)
            st = "HELD" if k[0] in HOLD else "LIVE"
            if ga and not gb:
                print(f"{ns} REMOVED {st} {k} {ga['apps']}")
                if st == "LIVE":
                    s["removed"] += 1
                continue
            if gb and not ga:
                print(f"{ns} ADDED {st} {k} {gb['apps']} | {gb['note']}")
                if st == "LIVE":
                    s["added"] += 1
                    s["added_years"] += len(yrs(gb))
                continue
            lost, gained = sorted(yrs(ga) - yrs(gb)), sorted(yrs(gb) - yrs(ga))
            oa, ob = gates_by_year(ga), gates_by_year(gb)
            cmp = {T: gate_cmp(oa.get(T), ob.get(T)) for T in yrs(ga) & yrs(gb)}
            nar = sorted(T for T, v in cmp.items() if v == "narrowed")
            wid = sorted(T for T, v in cmp.items() if v == "widened")
            if lost or gained or ga["note"] != gb["note"] or nar or wid:
                print(f"{ns} CHANGED {st} {k} {gb['apps']} lost {lost} gained {gained}")
                if ga["note"] != gb["note"]:
                    print(f"    old: {ga['note']}")
                    print(f"    new: {gb['note']}")
                for T in nar:
                    print(f"    GATE-NARROWED {T}: {oa.get(T)} -> {ob.get(T)}")
                for T in wid:
                    print(f"    GATE-WIDENED {T}: {oa.get(T)} -> {ob.get(T)}")
                if st == "LIVE":
                    s["changed"] += 1
                    s["lost_years"] += len(lost)
                    s["gained_years"] += len(gained)
                    s["narrowed"] += len(nar)
                    s["widened"] += len(wid)
        s["added_claims"] = s["added_years"] + s["gained_years"] + s["widened"]
        summary.append((ns, s))
    for ns, s in summary:
        print(f"# {ns} LIVE: removed {s['removed']} groups, added {s['added']} groups, changed {s['changed']}; "
              f"app-years lost {s['lost_years']}, gained {s['gained_years']}; gates narrowed {s['narrowed']}, "
              f"widened {s['widened']}; added claims {s['added_claims']}")


if __name__ == "__main__":
    main(sys.argv)
