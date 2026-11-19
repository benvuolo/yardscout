#!/usr/bin/env python3
"""Round 9 E + G (2026-11-19, branch interchange/nissan-ship-1119, on round 9):
nissan ships, in the newer payload field only.

E. groups/nissan.json is the round-9 candidate (groups/_report/nissan.candidate.json)
   byte for byte; GROUP_HOLD_CATS as it stands (its wiper-motor groups stay held).
G. Store apps read new payloads with their own older shell code, so a namespace
   an older shell cannot read correctly ships under oemGroups2
   (junkyard_scraper.OEM_NEW_FIELD_NS = {nissan}); docs/app.js pfOemGroupsOf reads
   oemGroups then oemGroups2, every older shell reads oemGroups only.
   - a build with nissan and one without: every lazy file's oemGroups and amGroups,
     the main file's oemGroups / oemVg and the old keys are identical; a category
     with no nissan group gets the same file; nissan groups only under oemGroups2;
   - the committed payload files (docs/data/interchange.json, docs/data/oem/*.json):
     an old-shell reader (oemGroups only) sees zero nissan groups, the new reader
     sees every shippable nissan group;
   - a lazy file over budget sheds oemGroups2 groups before any oemGroups group."""
import json
import tempfile
from pathlib import Path

from _util import OEM, check, done, js

J = js()
DOCS = OEM.parents[1] / "docs" / "data"
GROUPS = OEM / "groups"
LIVE = ["ford", "gm", "hmg", "mb", "mopar", "subaru", "toyota", "vag"]


def old_reader(d):
    """What every shell before this release reads (pfOemLazyLoad / pfRunSearch)."""
    return d.get("oemGroups") if isinstance(d.get("oemGroups"), list) else []


def new_reader(d):
    """docs/app.js pfOemGroupsOf."""
    return old_reader(d) + (d.get("oemGroups2") if isinstance(d.get("oemGroups2"), list) else [])


def build(groups_dir):
    J.OEM_GROUPS_DIR = groups_dir
    try:
        return J.build_interchange_files()
    finally:
        J.OEM_GROUPS_DIR = GROUPS


def strip(d):
    return {k: v for k, v in d.items() if k != "builtAt"}


# ------------------------------------------------------------ E: the files
nis = GROUPS / "nissan.json"
check("E: groups/nissan.json is the round-9 candidate byte for byte",
      nis.exists() and nis.read_bytes() == (GROUPS / "_report" / "nissan.candidate.json").read_bytes())
check("E: groups/ holds the eight live namespaces and nissan",
      sorted(p.stem for p in GROUPS.glob("*.json")) == sorted(LIVE + ["nissan"]))
check("G: nissan is the one new-field namespace", J.OEM_NEW_FIELD_NS == frozenset({"nissan"})
      and J.OEM_NEW_FIELD == "oemGroups2")
check("E: wiper-motor stays a held category", "wiper-motor" in J.GROUP_HOLD_CATS)

# ------------------------------------------------------------ G: with vs without nissan
with tempfile.TemporaryDirectory() as tmp:
    t = Path(tmp)
    for ns in LIVE:
        (t / f"{ns}.json").write_bytes((GROUPS / f"{ns}.json").read_bytes())
    (t / "aftermarket").symlink_to(GROUPS / "aftermarket")
    p0, f0 = build(t)
p1, f1 = build(GROUPS)
nissan_ok = [g for g in json.loads(nis.read_text())["likely"] if not J._oem_held(g["cat"], "nissan")]
check("G: the old keys and the main file's oemGroups / oemVg are the same with nissan on",
      all(p0.get(k) == p1.get(k) for k in ("categories", "platformGroups", "engineFamilies", "trimEngineNotes",
                                            "modelGenerations", "oemGroups", "oemVg")))
check("G: no nissan group in the main file's oemGroups; oemGroups2 absent from the main file (nissan ships Likely only)",
      not [g for g in p1.get("oemGroups") or [] if g["ns"] == "nissan"] and "oemGroups2" not in p1)
check("G: the lazy index keeps every category and its old counts; nissan's count is 'oem2'",
      sorted(p1["oemLazy"]["cats"]) == sorted(p0["oemLazy"]["cats"])
      and all({k: v for k, v in p1["oemLazy"]["cats"][c].items() if k != "oem2"} == p0["oemLazy"]["cats"][c]
              for c in p0["oemLazy"]["cats"])
      and sum(v.get("oem2", 0) for v in p1["oemLazy"]["cats"].values()) == len(nissan_ok))
check("G: every lazy file's oemGroups and amGroups are the same with nissan on",
      sorted(f1) == sorted(f0) and all(f1[c]["oemGroups"] == f0[c]["oemGroups"] and f1[c]["amGroups"] == f0[c]["amGroups"]
                                       for c in f0))
same = [c for c in f0 if "oemGroups2" not in f1[c]]
check(f"G: a category without a nissan group gets the same file ({len(same)} of {len(f0)}, builtAt aside)",
      all(strip(f1[c]) == strip(f0[c]) for c in same) and len(same) == len(f0) - len({g["cat"] for g in nissan_ok}),
      len(same))
n2 = [g for c in f1 for g in f1[c].get("oemGroups2") or []]
check(f"G: nissan ships only under oemGroups2: {len(n2)} groups, every shippable one",
      len(n2) == len(nissan_ok) and all(g["ns"] == "nissan" for g in n2)
      and {g["id"] for g in n2} == {g["id"] for g in nissan_ok})
check("G: no live group under oemGroups2", not [g for c in f1 for g in f1[c].get("oemGroups2") or [] if g["ns"] != "nissan"])

# ------------------------------------------------------------ G: the committed payload files
main = json.loads((DOCS / "interchange.json").read_text())
lazy = {p.stem: json.loads(p.read_text()) for p in sorted((DOCS / "oem").glob("*.json"))}
old_n = [g for d in [main, *lazy.values()] for g in old_reader(d) if g.get("ns") == "nissan"]
new_n = [g for d in [main, *lazy.values()] for g in new_reader(d) if g.get("ns") == "nissan"]
check("G: an old shell reading the committed payload sees zero nissan groups", old_n == [], len(old_n))
check(f"G: the new shell sees every shippable nissan group ({len(new_n)})",
      {g["id"] for g in new_n} == {g["id"] for g in nissan_ok})
check("G: the committed files are this build (oemGroups, oemGroups2, amGroups of every lazy file; main oemGroups)",
      sorted(lazy) == sorted(f1) and all(lazy[c].get(k) == f1[c].get(k) for c in f1
                                         for k in ("oemGroups", "oemGroups2", "amGroups"))
      and main.get("oemGroups") == p1.get("oemGroups"))
live_old = {g["id"] for d in lazy.values() for g in old_reader(d)}
live_new = {g["id"] for d in lazy.values() for g in new_reader(d) if g.get("ns") != "nissan"}
check("G: the live groups an old shell sees are the ones the new shell sees", live_old == live_new)

# ------------------------------------------------------------ G: the size trim order
big = {"schemaVersion": 1, "cat": "x", "amGroups": [],
       "oemGroups": [{"id": f"oem:toyota:x:L:{i}", "ns": "toyota", "tier": "likely", "cars": 5, "note": "a" * 400}
                     for i in range(3)],
       "oemGroups2": [{"id": f"oem:nissan:x:L:{i}", "ns": "nissan", "tier": "likely", "cars": 9, "note": "b" * 400}
                      for i in range(3)]}
size = len(json.dumps(big, separators=(",", ":"))) + 1
dropped, _n = J._lazy_trim(big, size - 300)
check("G: a lazy file over budget sheds oemGroups2 groups first; oemGroups keeps all three",
      dropped and all(d.startswith("oem:nissan:") for d in dropped) and len(big["oemGroups"]) == 3, dropped)
done("test_ship_1119")
