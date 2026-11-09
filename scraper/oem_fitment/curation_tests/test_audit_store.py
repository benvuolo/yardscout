#!/usr/bin/env python3
"""The audit store (review finding V7, 2026-11-05): an audit record written
into the real store must let a document curated afterwards pass V7 and ship,
with no OEM_STATUS_OVERRIDE and no status table injected anywhere.

Before the fix CATEGORY_STATUS lived in policy.py, which policy_sha256
hashes: writing a record changed the tree hash, so no document curated after
it could match it, and before the record existed V7 said 'not confirmed'.
The store is now audits.json (not hashed). This test writes its record into
a copy of that store (OEM_AUDITS_PATH, set before any import, so curate.py,
validate.py and the payload builder all read the same file the same way)."""
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OEM = HERE.parent
TOY = "www.toyotapartsnow.com"

# the tree hash as the spec defines it, computed here independently
h = hashlib.sha256()
for name in ("policy.py", "notes.py", "positions.py", "model_map.json", "release_allowlist.json"):
    h.update((OEM / name).read_bytes())
S0 = h.hexdigest()

store = Path(tempfile.mkdtemp(prefix="oem_audits_")) / "audits.json"
shutil.copy(OEM / "audits.json", store)
doc = json.loads(store.read_text())
committed_empty = doc.get("category_status") == {}
doc["category_status"] = {TOY: {"window-regulator": {
    "status": "confirmed", "errors": 0, "sample_n": 60, "date": "2026-11-05",
    "auditor_session": "test_audit_store", "policy_sha256": S0, "raw_commit": "fixtures"}}}
store.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
os.environ["OEM_AUDITS_PATH"] = str(store)

from _util import check, done, js, model_map, run, sienna_fixture  # noqa: E402
import curate as C  # noqa: E402
import policy  # noqa: E402
import validate as V  # noqa: E402

check("the committed audits.json holds no record (no audit has run)", committed_empty)
check("audits.json is not a policy_sha256 input: writing a record leaves the tree hash unchanged",
      C.policy_sha256() == S0 and V.tree_policy_sha256() == S0 and "audits.json" not in policy.POLICY_INPUTS)
check("the production table reads the store", policy.category_status(TOY, "window-regulator") is not None
      and V.policy.category_status(TOY, "window-regulator") is not None)

cur, d = run("toyota", sienna_fixture())          # production status table: no status_table passed
check("curated after the audit with the production table: one Verified group",
      len(d["groups"]) == 1 and d["policy_sha256"] == S0, str(cur.cells_info[(("Toyota", "Sienna", 2004),
                                                                              "window-regulator")]["elig"]))
probs = V.structural(d, V.context_from(js(), model_map(), policy_sha=V.tree_policy_sha256()))
check("curate.py main()'s check (model map + tree hash, production table) passes: V7 matches", probs == [], str(probs[:3]))

J = js()
gd = Path(tempfile.mkdtemp(prefix="oem_store_groups_"))
(gd / "toyota.json").write_text(json.dumps(d))
J.OEM_GROUPS_DIR, J.OEM_STATUS_OVERRIDE = gd, None
try:
    p = J.build_interchange_payload()
finally:
    J.OEM_GROUPS_DIR = J.SCRIPT_DIR / "oem_fitment" / "groups"
check("the payload builder, with no override, ships the Verified group",
      p["oemStatus"].get("toyota", "").startswith("ok fixtures 1 groups (1 verified")
      and [g["apps"] for g in p["oemGroups"] if g["tier"] == "verified"] == [[["Toyota", "Sienna", 2004, 2005]]],
      str(p.get("oemStatus")))

# a record for another policy hash never matches (re-audit after any policy edit)
doc["category_status"][TOY]["window-regulator"]["policy_sha256"] = "0" * 64
store.write_text(json.dumps(doc))
fresh = V._load_policy()
probs = V.structural(d, V.context_from(js(), model_map(), status_table=fresh.CATEGORY_STATUS,
                                       policy_sha=V.tree_policy_sha256()))
check("an audit record for another policy hash fails V7", any(x.startswith("V7") for x in probs), str(probs[:2]))
done("test_audit_store")
