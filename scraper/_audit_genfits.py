#!/usr/bin/env python3
"""One-shot audit for the generation-fits PR (scratch tooling, not shipped).

Verifies the invariant: for every model with known GENERATION_BREAKS, no
interchange-sensitive part's effective fits span crosses a breakpoint.
Also lists wide sensitive spans on models NOT in the breaks table so a human
can judge whether they need coverage.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js

violations = 0
uncovered = []
seen = set()
for key, e in js.UNOBTANIUM_DB.items():
    if id(e) in seen:
        continue
    seen.add(id(e))
    base = re.sub(r" \d{4}-\d{4}$", "", key)
    breaks = js.GENERATION_BREAKS.get(base)
    lo, hi = e["year_range"]
    for p in e["top_parts"]:
        plo = max(lo, p.get("yr_min", lo))
        phi = min(hi, p.get("yr_max", hi))
        if plo > phi:
            continue
        name = p["name"]
        if not js._GEN_SENSITIVE_RE.search(name) or js._GEN_MECH_EXCLUDE_RE.search(name):
            continue
        if breaks:
            cuts = [b for b in breaks if plo < b <= phi]
            if cuts:
                violations += 1
                print(f"VIOLATION {key}: {name} spans {plo}-{phi}, crosses {cuts}")
        elif phi - plo + 1 >= 9:
            uncovered.append(f"  {key} ({lo}-{hi}): {name} {plo}-{phi}")

print(f"\n{violations} violations in covered models")
print(f"\n{len(uncovered)} wide sensitive spans on models without breaks:")
print("\n".join(uncovered))
