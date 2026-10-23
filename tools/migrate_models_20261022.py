#!/usr/bin/env python3
"""One-time pass: apply the 2026-10 model normalization + VIN blob resolution
to the already-published docs/data/inventory_live.json, so the dropdowns fix
immediately instead of waiting for the next scan. The next scan runs the same
normalize_model/resolve_model_blob at enrich time and must agree.

Only the model field of each vehicle row is rewritten — ids, yard/partSet
indices, and the index-keyed vpic map all stay untouched. Match data
(maxValue/partSet) is refreshed by the next scan.

Run from the repo root:  python3 tools/migrate_models_20261022.py
"""
import collections
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))
import junkyard_scraper as js

LIVE = Path("docs/data/inventory_live.json")
raw = LIVE.read_text()
d = json.loads(raw)
f = d["fields"]
IM, IMO, IV = f.index("make"), f.index("model"), f.index("vin")

decodes = json.load(gzip.open("docs/data/vin_decodes.json.gz"))

before = collections.defaultdict(set)
after = collections.defaultdict(set)
case_merges = collections.Counter()     # (make, old, new) lowercase-equal
renames = collections.Counter()         # (make, old, new) wording changed
blob_hits = collections.Counter()       # (make, blob, resolved)
blob_misses = collections.Counter()     # (make, blob) kept

for v in d["vehicles"]:
    mk, old = v[IM], v[IMO]
    before[mk].add(old)
    new = js.normalize_model(old, mk)
    kind = None
    if new != old:
        kind = "case" if new.lower() == old.lower() else "rename"
    dec = decodes.get((v[IV] or "").strip().upper())
    resolved = js.resolve_model_blob(new, mk, dec)
    if resolved != new:
        blob_hits[(mk, new, resolved)] += 1
        new = resolved
    elif js._squash_model_key(new) in js._MODEL_BLOBS.get(js._make_key(mk), ()):
        blob_misses[(mk, new)] += 1
    if kind == "case":
        case_merges[(mk, old, new)] += 1
    elif kind == "rename":
        renames[(mk, old, new)] += 1
    v[IMO] = new
    after[mk].add(new)

print(f"case-fix rows:      {sum(case_merges.values()):6d}  ({len(case_merges)} distinct)")
print(f"rename/merge rows:  {sum(renames.values()):6d}  ({len(renames)} distinct)")
print(f"blob-resolved rows: {sum(blob_hits.values()):6d}  ({len(blob_hits)} distinct)")
print(f"blob kept rows:     {sum(blob_misses.values()):6d}  ({len(blob_misses)} distinct)")
print()
print("distinct models per make (top 15 by car count):")
by_cars = collections.Counter(v[IM] for v in d["vehicles"])
for mk, _ in by_cars.most_common(15):
    print(f"  {mk:15s} {len(before[mk]):4d} -> {len(after[mk]):4d}")
print()
print("top blob resolutions:")
for (mk, blob, res), c in blob_hits.most_common(25):
    print(f"  {c:5d}  {mk} {blob!r} -> {res!r}")
print()
print("top renames:")
for (mk, old, new), c in renames.most_common(30):
    print(f"  {c:5d}  {mk} {old!r} -> {new!r}")

if "--write" in sys.argv:
    LIVE.write_text(json.dumps(d, separators=(",", ":")))
    print(f"\nwrote {LIVE}")
else:
    print("\nDRY RUN (pass --write to persist)")
