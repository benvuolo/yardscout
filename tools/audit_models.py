#!/usr/bin/env python3
"""One-off audit of distinct (make, model) strings in docs/data/inventory_live.json.

Finds case/punctuation collisions (same squashed key, different display), generic
blob entries, and what the VIN-decode cache would resolve blobs to.
"""
import collections
import gzip
import json
import re
import sys

d = json.load(open("docs/data/inventory_live.json"))
f = d["fields"]
IM, IMO, IV, IY = f.index("make"), f.index("model"), f.index("vin"), f.index("year")
vs = d["vehicles"]

decodes = json.load(gzip.open("docs/data/vin_decodes.json.gz"))

squash = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())

pairs = collections.Counter((v[IM], v[IMO]) for v in vs)
permake = collections.defaultdict(collections.Counter)
for (mk, mo), c in pairs.items():
    permake[mk][mo] = c

mode = sys.argv[1] if len(sys.argv) > 1 else "collisions"

if mode == "collisions":
    # Same make + same squashed model key but different display strings.
    print("=== CASE/PUNCTUATION COLLISIONS (same squashed key, different display) ===")
    for mk in sorted(permake):
        bykey = collections.defaultdict(list)
        for mo, c in permake[mk].items():
            bykey[squash(mo)].append((mo, c))
        for k, lst in sorted(bykey.items()):
            if len(lst) > 1:
                print(f"{mk}: " + " | ".join(f"{mo!r}({c})" for mo, c in sorted(lst, key=lambda x: -x[1])))

elif mode == "make":
    mk = sys.argv[2]
    for mo, c in permake[mk].most_common():
        print(f"{c:6d}  {mo!r}")

elif mode == "blob":
    # What would the decode cache resolve a generic entry to?
    mk, blob = sys.argv[2], sys.argv[3]
    res = collections.Counter()
    nvin = 0
    for v in vs:
        if v[IM] == mk and v[IMO] == blob:
            dec = decodes.get((v[IV] or "").strip().upper())
            if dec and dec.get("model"):
                res[(dec["model"], dec.get("series", ""))] += 1
            else:
                nvin += 1
    print(f"{mk} {blob!r}: {sum(res.values())} decodable, {nvin} not in cache / no model")
    for (m, s), c in res.most_common(80):
        print(f"{c:6d}  model={m!r} series={s!r}")

elif mode == "generic":
    # Candidate blob strings: 'X Series', bare 'F-Series', etc.
    print("=== GENERIC/BLOB CANDIDATES ===")
    pat = re.compile(r"(series|class)$", re.IGNORECASE)
    for (mk, mo), c in sorted(pairs.items(), key=lambda x: -x[1]):
        if pat.search(mo.strip()):
            print(f"{c:6d}  {mk}: {mo!r}")
