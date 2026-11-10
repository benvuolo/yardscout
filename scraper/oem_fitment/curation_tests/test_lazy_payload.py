#!/usr/bin/env python3
"""CURATION_SPEC.md §12 lazy per-category files and the aftermarket key
(ops/interchange.md, 2026-11-06 Phase 1 client):
- the writer's build (build_interchange_files) keeps Verified OEM groups and
  oemVg in interchange.json and moves every Likely OEM group to
  docs/data/oem/<cat>.json instead of dropping it for size (V11);
- oemLazy indexes the files; old keys are byte-identical to a no-OEM build;
- aftermarket groups ship only in the lazy files under amGroups, src
  "aftermarket", tier "likely"; never in oemGroups; a group claiming
  Verified, carrying markup, or with a bad app is refused; too many refusals
  or a non-aftermarket file drop the whole file; evidence over 120 days
  expires;
- write_interchange_payload writes the files and removes stale ones;
- a lazy file over budget is trimmed (OEM by V11 order, then aftermarket);
- the repo ships groups files only for the owner-approved namespaces (2026-11-06)."""
import json
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from _util import TOY, check, confirmed, done, js, run, sienna_fixture
import curate as C

J = js()
PSHA = C.policy_sha256()
ST = confirmed((TOY, "window-regulator"), policy_sha=PSHA)
OLD = ("categories", "platformGroups", "engineFamilies", "trimEngineNotes", "modelGenerations", "schemaVersion")
DEFAULT_DIR = J.SCRIPT_DIR / "oem_fitment" / "groups"


def canon(p):
    return json.dumps({k: p[k] for k in OLD}, sort_keys=True)


def files_build(groups_dir, status=None):
    J.OEM_GROUPS_DIR, J.OEM_STATUS_OVERRIDE = groups_dir, status
    try:
        return J.build_interchange_files()
    finally:
        J.OEM_GROUPS_DIR, J.OEM_STATUS_OVERRIDE = DEFAULT_DIR, None


def plain_build(groups_dir, status=None):
    J.OEM_GROUPS_DIR, J.OEM_STATUS_OVERRIDE = groups_dir, status
    try:
        return J.build_interchange_payload()
    finally:
        J.OEM_GROUPS_DIR, J.OEM_STATUS_OVERRIDE = DEFAULT_DIR, None


NOW = datetime.now(timezone.utc)
FRESH = (NOW - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
STALE = (NOW - timedelta(days=200)).strftime("%Y-%m-%dT%H:%M:%SZ")


def am_group(i, **over):
    g = {"id": f"am:dbe:alternator:400-{i:05d}", "cat": "alternator", "tier": "likely", "src": "aftermarket",
         "unit": f"400-{i:05d}", "amps": 110, "trans": None, "retrieved": FRESH,
         "label": "DB Electrical application list",
         "note": f"DB Electrical 400-{i:05d} (110A unit) lists these vehicles; aftermarket application data, "
                 "not the carmaker's catalog. Match the engine and the amperage on the tag.",
         "apps": [["MINI", "Cooper", 2002, 2008, "1.6L 4-cyl"], ["MINI", "Cooper", 2002, 2008, "1.6L 4-cyl"]],
         "oe": ["BMW 12-31-7-523-897"], "conditions": [], "fits_text": "x", "url": "https://example.invalid/"}
    g.update(over)
    return g


def am_doc(groups, **over):
    d = {"schema": 1, "src": "aftermarket", "tier": "likely", "raw": "origin/oem-raw@fixture", "site": "x",
         "groups": groups}
    d.update(over)
    return d


# ---------------------------------------------------------------- nothing
empty = Path(tempfile.mkdtemp(prefix="oem_none_"))
p0, f0 = files_build(empty)
base = plain_build(empty)
check("no groups and no aftermarket files: no lazy files, no new keys, payload as before",
      f0 == {} and not any(k in p0 for k in ("oemGroups", "oemVg", "oemStatus", "oemLazy", "amStatus"))
      and canon(p0) == canon(base))
# owner decision 2026-11-06 (ops/hub.md): OEM Likely groups on for these
# namespaces only (§11.5 review satisfied by that approval)
# subaru withheld 2026-11-09: subarupartsdeal's "Fitting Vehicle Options" column
# encodes model/body (S/W/OBK/P), which curation ignored (ops/interchange.md)
# re-shipped 2026-11-09 after the make-breadth §11.4 round 4 (0 WRONG) and hub confirmation
APPROVED_NS = {"toyota", "gm", "mopar", "ford", "vag", "hmg", "mb", "subaru"}
_shipped = {p.stem for p in DEFAULT_DIR.glob("*.json")}
check("the repo ships groups/<ns>.json only for the owner-approved namespaces (§11.5)",
      _shipped <= APPROVED_NS, str(sorted(_shipped - APPROVED_NS)))
check("the shipped groups files hold no Verified group (Likely only)",
      all(not json.loads((DEFAULT_DIR / f"{ns}.json").read_text()).get("groups")
          and not json.loads((DEFAULT_DIR / f"{ns}.json").read_text()).get("vg") for ns in _shipped))
# aftermarket: owner decision 2026-11-06 (ops/hub.md): dbelectrical.json only,
# only the six approved (namespace, category) pairs, never a gap make
import sys as _sys  # noqa: E402
_sys.path.insert(0, str(J.SCRIPT_DIR / "oem_fitment" / "aftermarket"))
import groups_am as _GA  # noqa: E402
_am = sorted(p.name for p in (DEFAULT_DIR / "aftermarket").glob("*.json"))
_mns = _GA._make_ns()
# + hub 2026-11-10: spectrapremium.json (§11.4 round 2, 0 WRONG), only the
# categories released for that source (AM_RELEASED), pinned raw, no gap make
_bad = []
for _p in (DEFAULT_DIR / "aftermarket").glob("*.json"):
    _doc = json.loads(_p.read_text())
    if _p.stem == "spectrapremium":
        if not re.match(r"oem-raw@[0-9a-f]{8}:", str(_doc.get("raw") or "")):
            _bad.append(("spectrapremium raw not pinned", _doc.get("raw")))
    # + hub 2026-11-10: gspnorthamerica.json (cv-axle, §11.4 round 4, 0 WRONG):
    # raw and lot snapshot pinned to full commits, lot files' sha256 recorded
    if _p.stem == "gspnorthamerica":
        _ls = _doc.get("lot_snapshot") or {}
        if not re.match(r"[0-9a-f]{40}@", str(_doc.get("raw") or "")) or not re.fullmatch(
                r"[0-9a-f]{40}", str(_ls.get("ref") or "")) or len((_ls.get("sha256") or {})) != 2:
            _bad.append(("gspnorthamerica raw/lot snapshot not pinned", _doc.get("raw")))
    for _g in _doc["groups"]:
        for _a in _g["apps"]:
            if _a[0] in _GA.SHIP_OFF_MAKES:
                _bad.append((_g["id"], _a[0]))
            elif _p.stem in ("spectrapremium", "gspnorthamerica"):
                if _g["cat"] not in J.AM_RELEASED.get(_p.stem, ()):
                    _bad.append((_g["id"], _g["cat"]))
            elif (_mns.get(_a[0]), _g["cat"]) not in _GA.SHIP_PAIRS:
                _bad.append((_g["id"], _a[0]))
check("groups/aftermarket ships only dbelectrical.json (owner-approved pairs), spectrapremium.json and "
      "gspnorthamerica.json (their released categories, pinned inputs); never a gap make",
      set(_am) <= {"dbelectrical.json", "spectrapremium.json", "gspnorthamerica.json"} and not _bad, str((_am, _bad[:3])))

# ---------------------------------------------------------------- OEM split
def likely_entry(i, cat="headlights"):
    p0 = "81110-0L%03d" % i
    return {"id": f"oem:toyota:{cat}:L:{i:010d}", "cat": cat, "tier": "likely", "kind": "body",
            "apps": [["Toyota", "Camry", 2004, 2005], ["Toyota", "Sienna", 2004, 2005]], "pn": [p0],
            "reason": "conditional", "cars": i + 2, "oldest_retrieved": FRESH,
            "note": f"Toyota catalog lists #{p0} for both — fits some configurations; verify the number on the part"}


cur, doc = run("toyota", sienna_fixture(), status_table=ST)
doc["likely"] = list(doc.get("likely") or []) + [likely_entry(i) for i in range(4)] + [likely_entry(9, "tail-lights")]
gd = Path(tempfile.mkdtemp(prefix="oem_lazy_"))
(gd / "toyota.json").write_text(json.dumps(doc))
full = plain_build(gd, ST)
p, files = files_build(gd, ST)
likely_ids = sorted(g["id"] for g in full["oemGroups"] if g["tier"] == "likely")
lazy_ids = sorted(g["id"] for d in files.values() for g in d["oemGroups"])
check("fixture has Verified and Likely groups", likely_ids and any(g["tier"] == "verified" for g in full["oemGroups"]),
      str(len(likely_ids)))
check("main file keeps only the Verified OEM groups",
      p["oemGroups"] and all(g["tier"] == "verified" for g in p["oemGroups"])
      and sorted(g["id"] for g in p["oemGroups"]) == sorted(g["id"] for g in full["oemGroups"] if g["tier"] == "verified"))
check("every Likely group is in a lazy file (none lost)", lazy_ids == likely_ids, f"{lazy_ids[:3]} vs {likely_ids[:3]}")
check("lazy files hold Likely OEM groups only, each in its own category's file",
      all(g["tier"] == "likely" and g["src"] == "oem" and g["cat"] == c for c, d in files.items() for g in d["oemGroups"]))
check("oemLazy indexes exactly the files, with counts and the data/oem/ path",
      p.get("oemLazy", {}).get("path") == "data/oem/"
      and p["oemLazy"]["cats"] == {c: {"oem": len(d["oemGroups"]), "am": len(d["amGroups"])} for c, d in files.items()},
      json.dumps(p.get("oemLazy")))
check("each lazy file names its category, schema and the main file's builtAt",
      all(d["cat"] == c and d["schemaVersion"] == 1 and d["builtAt"] == p["builtAt"] for c, d in files.items()))
check("old keys byte-identical to a no-OEM build (V9 view)", canon(p) == canon(base))
check("oemVg and oemStatus stay in the main file", "oemVg" in p and p["oemStatus"]["toyota"].startswith("ok"))
check("no V11 drop when the groups fit the lazy files", "dropped for size" not in p["oemStatus"]["toyota"],
      p["oemStatus"]["toyota"])
check("tests' plain build is unchanged (Likely groups still in oemGroups)",
      any(g["tier"] == "likely" for g in full["oemGroups"]) and "oemLazy" not in full)

# ---------------------------------------------------------------- aftermarket
ad = Path(tempfile.mkdtemp(prefix="oem_am_"))
(ad / "aftermarket").mkdir()
good = [am_group(i) for i in range(1, 30)]
mixed = good + [am_group(90, tier="verified"), am_group(91, note="fit notes <br."),
                am_group(92, apps=[["MINI", "Cooper", 2008, 2002, "1.6L"]]), am_group(93, retrieved=STALE),
                am_group(94, cat="starter", id="am:dbe:starter:410-00094", unit="410-00094")]
(ad / "aftermarket" / "dbelectrical.json").write_text(json.dumps(am_doc(mixed)))
pa, fa = files_build(ad)
am = fa.get("alternator", {}).get("amGroups", [])
check("aftermarket groups ship under amGroups in the alternator / starter files",
      len(am) == 29 and [g["id"] for g in fa.get("starter", {}).get("amGroups", [])] == ["am:dbe:starter:410-00094"],
      f"{len(am)} {list(fa)}")
check("aftermarket groups: src aftermarket, tier likely, unit and amperage kept, apps deduplicated",
      all(g["src"] == "aftermarket" and g["tier"] == "likely" and g["unit"] and g["amps"] == 110 and len(g["apps"]) == 1
          and g["label"] == "DB Electrical" for g in am), json.dumps(am[:1]))
check("aftermarket groups never reach oemGroups or the old keys",
      not pa.get("oemGroups") and not any(g.get("src") == "aftermarket" for d in fa.values() for g in d["oemGroups"])
      and canon(pa) == canon(base))
check("refused singly: a group claiming verified, one with markup in its note, one with a bad year span",
      not any(g["id"].endswith(("00090", "00091", "00092")) for g in am))
check("expired (evidence over 120 days) groups are dropped", not any(g["id"].endswith("00093") for g in am)
      and "1 expired" in pa["amStatus"]["dbelectrical"], pa["amStatus"]["dbelectrical"])
check("amStatus reports ok, the count and the refusals", pa["amStatus"]["dbelectrical"].startswith("ok origin/oem-raw@fixture 30 groups")
      and "3 refused (malformed)" in pa["amStatus"]["dbelectrical"], pa["amStatus"]["dbelectrical"])
check("payload copy drops crawl-only fields (oe, url, conditions, fits_text, retrieved)",
      not any(k in am[0] for k in ("oe", "url", "conditions", "fits_text", "retrieved")), str(sorted(am[0])))

(ad / "aftermarket" / "dbelectrical.json").write_text(json.dumps(am_doc(good + [am_group(100 + i, tier="verified") for i in range(8)])))
pb, fb = files_build(ad)
check("more than 5% (min 5) refused: the whole file is dropped and reported",
      fb == {} and pb["amStatus"]["dbelectrical"].startswith("dropped:") and "oemLazy" not in pb, str(pb.get("amStatus")))
(ad / "aftermarket" / "dbelectrical.json").write_text(json.dumps(am_doc(good, tier="verified")))
pc, fc = files_build(ad)
check("a file that is not an aftermarket Likely doc is dropped", fc == {} and pc["amStatus"]["dbelectrical"].startswith("dropped"))
(ad / "aftermarket" / "dbelectrical.json").write_text("{not json")
pd, fd = files_build(ad)
check("an unreadable file is dropped, the build goes on", fd == {} and pd["amStatus"]["dbelectrical"].startswith("dropped")
      and canon(pd) == canon(base))

# ---------------------------------------------------------------- writer
(gd / "aftermarket").mkdir()
(gd / "aftermarket" / "dbelectrical.json").write_text(json.dumps(am_doc(good)))
out = Path(tempfile.mkdtemp(prefix="oem_out_"))
(out / "oem").mkdir()
(out / "oem" / "stale-cat.json").write_text("{}")
saved = J.DATA_DIR
J.DATA_DIR, J.OEM_GROUPS_DIR, J.OEM_STATUS_OVERRIDE = out, gd, ST
try:
    J.write_interchange_payload()
finally:
    J.DATA_DIR, J.OEM_GROUPS_DIR, J.OEM_STATUS_OVERRIDE = saved, DEFAULT_DIR, None
main = json.loads((out / "interchange.json").read_text())
written = sorted(x.stem for x in (out / "oem").glob("*.json"))
check("writer: one file per indexed category, the stale file removed",
      written == sorted(main["oemLazy"]["cats"]) and "stale-cat" not in written and "alternator" in written, str(written))
check("writer: files end with a newline and parse; the alternator file carries the aftermarket groups",
      all((out / "oem" / f"{c}.json").read_text().endswith("}\n") for c in written)
      and len(json.loads((out / "oem" / "alternator.json").read_text())["amGroups"]) == 29)
check("writer: main file within the V11 budget", len((out / "interchange.json").read_text()) <= J._oem_validator().policy.PAYLOAD_BYTE_BUDGET)

# ---------------------------------------------------------------- lazy trim
big = {"schemaVersion": 1, "cat": "alternator", "oemGroups": [],
       "amGroups": [J._am_group_entry(am_group(i, apps=[["MINI", "Cooper", 2002, 2002 + (i % 6), "1.6L"]]), "dbelectrical")
                    for i in range(200)]}
size = len(json.dumps(big, separators=(",", ":"))) + 1
dropped, n_am = J._lazy_trim(big, size // 2)
check("lazy trim: an aftermarket file over budget drops groups until it fits",
      n_am > 0 and len(json.dumps(big, separators=(",", ":"))) + 1 <= size // 2 and dropped == [], f"{n_am}")
o = {"schemaVersion": 1, "cat": "hood", "amGroups": [],
     "oemGroups": [{"id": f"oem:toyota:hood:L:{i}", "tier": "likely", "cars": i, "note": "x" * 200, "cat": "hood"}
                   for i in range(100)]}
osz = len(json.dumps(o, separators=(",", ":"))) + 1
d2, _ = J._lazy_trim(o, osz // 2)
check("lazy trim: an OEM file over budget drops lowest value first (V11 order)",
      d2[:2] == ["oem:toyota:hood:L:0", "oem:toyota:hood:L:1"] and len(json.dumps(o, separators=(",", ":"))) + 1 <= osz // 2)
done("test_lazy_payload")
