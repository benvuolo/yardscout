#!/usr/bin/env python3
"""Dump the Ario (app.autorecycler.io) organization table — the config
oracle for ARIO_CHAINS (read-only, ~2 POSTs; --counts adds one n=1 probe
per org plus paged counts for orgs with visible rows, at ARIO_DELAY_SEC).

    python3 scraper/_probe_ario_orgs.py                 # id | slug | name | pin
    python3 scraper/_probe_ario_orgs.py --counts        # + live visible rows
    python3 scraper/_probe_ario_orgs.py --grep "foss"   # filter by name/slug
    python3 scraper/_probe_ario_orgs.py --json out.json # raw org records

Pins print from the org record's own geocode (what the scan prefers), so a
yard's config fallback lat/lng can be copied straight from here.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402
import requests  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--counts", action="store_true")
    ap.add_argument("--grep", default="")
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    session = requests.Session()
    orgs = js._ario_search_all(session, "custom.organization", [], max_pages=5)
    if not orgs:
        sys.exit("organization table fetch failed (network policy? API change?)")
    if args.json:
        args.json.write_text(json.dumps(orgs, indent=1, default=str))
    ref_prefix = next((p for p in (js._ario_ref_prefix(o) for o in orgs) if p), "")
    q = args.grep.lower()
    rows = []
    for org in orgs:
        src = org.get("_source") or {}
        name = str(src.get("name_text") or src.get("name1_text") or "").strip()
        slug = str(src.get("id_text") or "").strip()
        if q and q not in name.lower() and q not in slug.lower():
            continue
        pin = js._ario_org_pin(org)
        count = ""
        if args.counts:
            org_ref = f"{ref_prefix}{org['_id']}" if ref_prefix else org["_id"]
            cons = [{"key": "organization_custom_organization",
                     "constraint_type": "equals", "value": org_ref},
                    {"key": "visible_boolean", "constraint_type": "equals", "value": True}]
            probe = js._ario_search(session, "custom.inventorysearch", cons, 0, 1)
            hits = ((probe or {}).get("hits") or {}).get("hits") or []
            if hits:
                allh = js._ario_search_all(session, "custom.inventorysearch", cons)
                count = str(sum(1 for h in allh
                                if not (h.get("_source") or {}).get("deleted_boolean")))
            else:
                count = "0"
        rows.append((org["_id"], slug, name, pin, count))
    rows.sort(key=lambda r: (r[2].lower(), r[1]))
    print(f"{len(rows)} orgs (ref prefix {ref_prefix!r})")
    for oid, slug, name, pin, count in rows:
        pin_s = f"{pin[0]},{pin[1]}" if pin else "-"
        print(f"{oid} | {slug or '-'} | {name} | {pin_s}" + (f" | {count}" if args.counts else ""))


if __name__ == "__main__":
    main()
