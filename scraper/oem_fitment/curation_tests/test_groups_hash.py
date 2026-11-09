#!/usr/bin/env python3
"""Every committed groups/<ns>.json must carry the policy hash of this tree
(policy.tree_sha256). Otherwise the payload loader drops the namespace (V8)
and the next scan removes its OEM groups from users. Edit policy.py,
notes.py, positions.py or model_map.json -> re-curate the shipped
namespaces in the same push (2026-11-09: main@1fe9425 would have dropped
all 7)."""
import json

from _util import OEM, check, done
import model_map as MM
import policy

want = policy.tree_sha256(MM.MODEL_MAP_PATH)
files = sorted((OEM / "groups").glob("*.json"))
check("groups/ has committed namespace files", bool(files))
for p in files:
    got = json.loads(p.read_text()).get("policy_sha256")
    check(f"groups/{p.name} policy_sha256 matches this tree (V8)", got == want,
          f"{(got or '')[:12]} != {want[:12]}: re-curate this namespace")
done("test_groups_hash")
