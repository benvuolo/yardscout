"""live_diff.py OLD_DIR NEW_DIR NS [NS...]: claim diff of groups/<ns>.json between
two directories, per (category, pn): REMOVED / ADDED / CHANGED (app-years lost
and gained, old and new note). Held categories (junkyard_scraper.GROUP_HOLD_CATS)
are marked HELD (never shipped). Read-only; no fetch."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scraper"))
import junkyard_scraper as js  # noqa: E402

HOLD = set(js.GROUP_HOLD_CATS)


def yrs(g):
    return {(a[0], a[1], y) for a in g["apps"] for y in range(a[2], a[3] + 1)}


def main(argv):
    old, new = Path(argv[1]), Path(argv[2])
    for ns in argv[3:]:
        a = {(g["cat"], tuple(g["pn"])): g for g in json.loads((old / f"{ns}.json").read_text())["likely"]}
        b = {(g["cat"], tuple(g["pn"])): g for g in json.loads((new / f"{ns}.json").read_text())["likely"]}
        for k in sorted(set(a) | set(b)):
            ga, gb = a.get(k), b.get(k)
            st = "HELD" if k[0] in HOLD else "LIVE"
            if ga and not gb:
                print(f"{ns} REMOVED {st} {k} {ga['apps']}")
            elif gb and not ga:
                print(f"{ns} ADDED {st} {k} {gb['apps']} | {gb['note']}")
            elif ga["apps"] != gb["apps"] or ga["note"] != gb["note"]:
                print(f"{ns} CHANGED {st} {k} {gb['apps']} lost {sorted(yrs(ga) - yrs(gb))} "
                      f"gained {sorted(yrs(gb) - yrs(ga))}")
                if ga["note"] != gb["note"]:
                    print(f"    old: {ga['note']}")
                    print(f"    new: {gb['note']}")


if __name__ == "__main__":
    main(sys.argv)
