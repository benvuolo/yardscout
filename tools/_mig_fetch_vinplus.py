#!/usr/bin/env python3
"""One-off: full VinPlus fetch for the chesterfield_auto_parts and go_pull_it
tenants (make x location loop with year-bisection, same as the production
adapter) so we can compare the API inventory against the current crawls
before migrating. Writes raw rows to /tmp/mig_vinplus_{tenant}.json.
Polite: 2s between requests (same as the adapter)."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))
import junkyard_scraper as js  # noqa: E402

TENANTS = {
    "chesterfield_auto_parts": ["richmond", "southside", "fort_lee"],
    "go_pull_it": ["jacksonville", "atlanta_east", "gainesville", "tallahassee"],
}

r = js.requests.get(f"{js.VINPLUS_API}/api/vehicle-groups", headers=js.HEADERS, timeout=60)
r.raise_for_status()
makes = sorted((r.json().get("data") or {}).keys())
print(f"{len(makes)} makes", flush=True)

for tenant, locs in TENANTS.items():
    out = {}
    for loc in locs:
        rows = []
        for mk in makes:
            rows.extend(js._vinplus_search(tenant, mk, loc))
        out[loc] = rows
        print(f"{tenant}/{loc}: {len(rows)} rows", flush=True)
    Path(f"/tmp/mig_vinplus_{tenant}.json").write_text(json.dumps(out))
print("done", flush=True)
