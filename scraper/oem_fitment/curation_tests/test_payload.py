#!/usr/bin/env python3
"""CURATION_SPEC.md §9 scraper/test_interchange additions (fixture
OEM_GROUPS_DIR), kept here so the interchange suite itself stays untouched:
- oemGroups and oemVg are present; entries carry src 'oem' and a label;
- old keys are byte-identical to a build without OEM, apart from demotions;
- categories ids are unchanged;
- a failing namespace file is dropped and recorded in oemStatus, not raised;
- interchange_tier is symmetric; no groups files -> payload unchanged."""
import copy
import json
import tempfile
from pathlib import Path

from _util import TOY, check, confirmed, done, js, run, sienna_fixture
import curate as C

J = js()
PSHA = C.policy_sha256()
ST = confirmed((TOY, "window-regulator"), policy_sha=PSHA)
OLD = ("categories", "platformGroups", "engineFamilies", "trimEngineNotes", "modelGenerations", "schemaVersion")


def build(groups_dir, status=None):
    J.OEM_GROUPS_DIR, J.OEM_STATUS_OVERRIDE = groups_dir, status
    try:
        return J.build_interchange_payload()
    finally:
        J.OEM_GROUPS_DIR, J.OEM_STATUS_OVERRIDE = J.SCRIPT_DIR / "oem_fitment" / "groups", None


def canon(p):
    return json.dumps({k: p[k] for k in OLD}, sort_keys=True)


empty = Path(tempfile.mkdtemp(prefix="oem_none_"))
base = build(empty)
check("no groups files: the payload has no OEM keys at all",
      not any(k in base for k in ("oemGroups", "oemVg", "oemStatus")))
check("the repo ships no groups/<ns>.json yet (first merge waits for owner review)",
      not list((J.SCRIPT_DIR / "oem_fitment" / "groups").glob("*.json")))
real_default = J.build_interchange_payload()
check("the default build equals the no-OEM build on the old keys", canon(real_default) == canon(base))

cur, doc = run("toyota", sienna_fixture(), status_table=ST)
gd = Path(tempfile.mkdtemp(prefix="oem_fix_"))
(gd / "toyota.json").write_text(json.dumps(doc))
(gd / "_report").mkdir()
(gd / "_report" / "toyota.json").write_text("{not json")       # reports are never read
p = build(gd, ST)
check("oemGroups / oemVg / oemStatus are present", all(k in p for k in ("oemGroups", "oemVg", "oemStatus")))
og = [g for g in p["oemGroups"] if g["tier"] == "verified"]
check("the fixture's Verified body group ships in oemGroups with src 'oem' and the brand label",
      len(og) == 1 and og[0]["src"] == "oem" and og[0]["label"] == "Toyota catalog" and og[0]["ns"] == "toyota"
      and og[0]["apps"] == [["Toyota", "Sienna", 2004, 2005]], json.dumps(og)[:300])
check("oemStatus says ok with the raw commit and group count", p["oemStatus"].get("toyota", "").startswith("ok fixtures 1 groups"),
      str(p["oemStatus"]))
check("old keys are byte-identical to a build without OEM (no contradiction here)", canon(p) == canon(base))
check("categories ids are unchanged", [c["id"] for c in p["categories"]] == [c["id"] for c in base["categories"]])
check("_report/ is skipped by the loader", "toyota" in p["oemStatus"] and len(p["oemStatus"]) == 1)
check("no OEM claim reaches platformGroups or engineFamilies",
      not any(str(g.get("id", "")).startswith("oem:") for g in p["platformGroups"])
      and "oem:" not in json.dumps(p["engineFamilies"]))

# a failing namespace file is dropped and recorded, never raised
bad = copy.deepcopy(doc)
bad["ns"] = "mopar"
bad["groups"][0]["tier"] = "bogus"
(gd / "mopar.json").write_text(json.dumps(bad))
(gd / "ford.json").write_text("{truncated")
p = build(gd, ST)
check("an invalid namespace file is dropped: oemStatus records why",
      p["oemStatus"]["mopar"].startswith("dropped: V") and p["oemStatus"]["ford"].startswith("dropped: unreadable"),
      str(p["oemStatus"]))
check("the valid namespace still ships beside the dropped ones",
      p["oemStatus"]["toyota"].startswith("ok") and any(g["ns"] == "toyota" for g in p["oemGroups"])
      and not any(g["ns"] in ("mopar", "ford") for g in p["oemGroups"]))
check("old keys stay byte-identical with dropped namespaces", canon(p) == canon(base))
(gd / "mopar.json").unlink()
(gd / "ford.json").unlink()

# without the audit record (production CATEGORY_STATUS is empty) the
# Verified file is refused at build time: nothing unvalidated ships
p = build(gd, None)
check("a Verified group without its audit record drops the namespace (V7)",
      p["oemStatus"]["toyota"].startswith("dropped: V7") and p["oemGroups"] == [], str(p["oemStatus"]))

# a file under the wrong name is refused
(gd / "nissan.json").write_text(json.dumps(doc))
p = build(gd, ST)
check("a file whose ns differs from its name is dropped", p["oemStatus"]["nissan"].startswith("dropped"))
(gd / "nissan.json").unlink()

# build-time expiry
old = copy.deepcopy(doc)
for y in old["groups"][0]["years"]:
    y["closure"]["oldest_retrieved"] = "2026-01-01T00:00:00Z"
old["as_of"] = "2026-01-01T00:00:00Z"
ge = Path(tempfile.mkdtemp(prefix="oem_old_"))
(ge / "toyota.json").write_text(json.dumps(old))
p = build(ge, ST)
check("groups whose evidence is over 120 days old are dropped at build time",
      not any(g["tier"] == "verified" for g in p.get("oemGroups", [])), str(p.get("oemStatus")))

# a missing validator never crashes the scan
J.OEM_VALIDATOR, keep = Path("/nonexistent/validate.py"), J.OEM_VALIDATOR
try:
    p = build(gd, ST)
finally:
    J.OEM_VALIDATOR = keep
check("a missing validator drops every namespace and the scan keeps building",
      p["oemStatus"]["toyota"].startswith("dropped: validator unavailable") and canon(p) == canon(base))

# interchange_tier is still symmetric
fams = J.ENGINE_FAMILIES
asym = []
for fid, fam in list(fams.items())[:60]:
    for cat in fam["parts"]:
        apps = fam["apps"][:4]
        for a in apps:
            for b in apps:
                s, d = (a[2], a[0], a[1]), (b[3], b[0], b[1])
                if J.interchange_tier(fam, cat, s, d) != J.interchange_tier(fam, cat, d, s):
                    asym.append((fid, cat))
check("interchange_tier is symmetric (60 families)", not asym, str(asym[:3]))
p = build(gd, ST)
check("schemaVersion stays 2", p["schemaVersion"] == 2)
check("payload stays within the V11 budget", len(json.dumps(p, separators=(",", ":"))) <= 1_300_000)
done("test_payload")
