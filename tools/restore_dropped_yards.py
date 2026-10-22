#!/usr/bin/env python3
"""One-off production restore, 2026-10-21 incident.

The 22:56Z scan hit transient source failures (Pull-N-Save makes API down ×3
attempts, Budget Winter Garden serving an unparseable inventory page) and
published inventory_live.json without 9 yards / ~13k vehicles. This driver
carries those yards forward from the last good commit (888ee39, 19:44Z) into
the current working-tree data files using the scraper's stale-keep merge.

Usage: python3 tools/restore_dropped_yards.py <good-git-ref>
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scraper"))
import junkyard_scraper as js  # noqa: E402

LIVE = ROOT / "docs/data/inventory_live.json"
EXTRAS = ROOT / "docs/data/vehicle_extras.json"


def git_show(ref: str, path: str) -> dict:
    out = subprocess.run(["git", "-C", str(ROOT), "show", f"{ref}:{path}"],
                         capture_output=True, check=True).stdout
    return json.loads(out)


def counts(p: dict) -> dict[str, int]:
    i_yard = p["fields"].index("yard")
    names = [y[0] for y in p["yards"]]
    c: dict[str, int] = {}
    for row in p["vehicles"]:
        c[names[row[i_yard]]] = c.get(names[row[i_yard]], 0) + 1
    return c


def main() -> None:
    good_ref = sys.argv[1] if len(sys.argv) > 1 else "888ee39"
    prev = git_show(good_ref, "docs/data/inventory_live.json")
    prev_extras = git_show(good_ref, "docs/data/vehicle_extras.json").get("extras", {})
    cur = json.loads(LIVE.read_text())
    cur_extras_doc = json.loads(EXTRAS.read_text())
    cur_extras = cur_extras_doc.get("extras", {})

    pc, cc = counts(prev), counts(cur)
    dropped = sorted(n for n, k in pc.items() if k >= 25 and cc.get(n, 0) < 0.4 * k)
    if not dropped:
        print("nothing to restore")
        return
    print(f"restoring {len(dropped)} yards from {good_ref}:")
    carried = js.merge_carryforward_yards(cur, prev, dropped,
                                          new_extras=cur_extras,
                                          prev_extras=prev_extras)
    for n in dropped:
        print(f"  {n}: {cc.get(n, 0)} -> {carried.get(n, 0)}")

    # Validate invariants before touching production files.
    i_yard = cur["fields"].index("yard")
    i_pset = cur["fields"].index("partSet")
    ny, np_, nv = len(cur["yards"]), len(cur["partSets"]), len(cur["vehicles"])
    assert all(0 <= r[i_yard] < ny for r in cur["vehicles"]), "yard idx out of range"
    assert all(r[i_pset] < np_ for r in cur["vehicles"]), "partSet idx out of range"
    assert all(0 <= int(k) < nv for k in cur["vpic"]), "vpic key out of range"
    ids = [r[0] for r in cur["vehicles"]]
    assert len(ids) == len(set(ids)), "duplicate vehicle ids after merge"
    final = counts(cur)
    for n in dropped:
        assert final.get(n) == pc[n], f"{n}: expected {pc[n]}, got {final.get(n)}"

    LIVE.write_text(json.dumps(cur, separators=(",", ":")))
    cur_extras_doc["extras"] = cur_extras
    EXTRAS.write_text(json.dumps(cur_extras_doc, separators=(",", ":")))
    print(f"OK: {ny} yards, {nv} vehicles, {len(cur_extras)} extras entries")


if __name__ == "__main__":
    main()
