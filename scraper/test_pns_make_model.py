#!/usr/bin/env python3
"""Pull-N-Save make/model from the VIN, not the queried make (2026-11-07):
the 4Runner-listed-as-Audi-A3 and MDX-that-is-a-Grand-Caravan cases,
model-owner fallback, not-pickable flag, one row per stock.
Run:  python3 scraper/test_pns_make_model.py   (offline)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        fails.append(name)


OWNERS = {"a3": {"Audi"}, "4runner": {"Toyota"}, "mdx": {"Acura"}, "grandcaravan": {"Dodge"},
          "odyssey": {"Honda"}, "pickup": {"Toyota", "Nissan", "Mazda"}}
DEC = {
    "JTEBU5JR0D5116438": {"make": "TOYOTA", "model": "4Runner", "modelYear": "2013"},
    "2D4RN4DG0BR000001": {"make": "DODGE", "model": "Grand Caravan", "modelYear": "2011"},
    "5FNRL38655B406292": {"make": "HONDA", "model": "Odyssey", "modelYear": "2005"},
    "WAUAAAAA0DA000001": {"make": "AUDI", "model": "A3", "modelYear": "2013"},
}

R = js.pns_resolve_make_model
check("4Runner VIN listed as 'AUDI A3' -> Toyota 4Runner",
      R("Audi", "AUDI A3", DEC["JTEBU5JR0D5116438"], OWNERS) == ("Toyota", "4Runner", True, "vin"),
      R("Audi", "AUDI A3", DEC["JTEBU5JR0D5116438"], OWNERS))
check("Grand Caravan VIN listed as Acura 'MDX' -> Dodge Grand Caravan",
      R("Acura", "MDX", DEC["2D4RN4DG0BR000001"], OWNERS) == ("Dodge", "Grand Caravan", True, "vin"),
      R("Acura", "MDX", DEC["2D4RN4DG0BR000001"], OWNERS))
check("agreeing VIN keeps the row's own model text",
      R("Honda", "ODYSSEY", DEC["5FNRL38655B406292"], OWNERS) == ("Honda", "Odyssey", True, "vin_agrees"))
check("agreeing VIN, make prefix stripped",
      R("Audi", "AUDI A3", DEC["WAUAAAAA0DA000001"], OWNERS) == ("Audi", "A3", True, "vin_agrees"))
check("no decode, model owned by one make -> that make",
      R("Acura", "4RUNNER", None, OWNERS) == ("Toyota", "4Runner", True, "model"),
      R("Acura", "4RUNNER", None, OWNERS))
check("no decode, shared model -> queried make, not pickable",
      R("Mazda", "PICKUP", None, OWNERS) == ("Mazda", "Pickup", False, "nopick"))
check("no decode, unknown model -> queried make, not pickable",
      R("Audi", "AUDI ZZZ", None, OWNERS) == ("Audi", "ZZZ", False, "nopick"))
check("unconfident decode (comma model) falls back to the model rule",
      R("Acura", "MDX", {"make": "DODGE", "model": "Caravan, Grand Caravan"}, OWNERS)[3] == "model")

check("all-caps decoded model is title-cased",
      R("Audi", "AUDI 4000", {"make": "CHRYSLER", "model": "FIFTH AVENUE", "modelYear": "1985"}, OWNERS)[:2]
      == ("Chrysler", "Fifth Avenue"), R("Audi", "AUDI 4000", {"make": "CHRYSLER", "model": "FIFTH AVENUE"}, OWNERS))

# Whole adapter post-pass: flags and published noPick.
rows = [
    {"id": "pns-stk079583", "vin": "JTEBU5JR0D5116438", "make": "Audi", "model": "Audi A3", "_pns_query_make": "Audi"},
    {"id": "pns-stk1", "vin": "2D4RN4DG0BR000001", "make": "Acura", "model": "Mdx", "_pns_query_make": "Acura"},
    {"id": "pns-stk2", "vin": "", "make": "Mazda", "model": "Pickup", "_pns_query_make": "Mazda"},
]
js._pns_resolve_makes(rows, lookup=DEC.get, owners=OWNERS)
check("post-pass: 4Runner row fixed", (rows[0]["make"], rows[0]["model"]) == ("Toyota", "4Runner"), rows[0])
check("post-pass: MDX row fixed", (rows[1]["make"], rows[1]["model"]) == ("Dodge", "Grand Caravan"), rows[1])
check("post-pass: ambiguous row flagged", rows[2].get("_noPickAdapter") is True and "_noPickAdapter" not in rows[0])
check("stats counted", js.PNS_MAKE_STATS == {"vin": 2, "nopick": 1}, js.PNS_MAKE_STATS)

# models.json owner index honours the minimum count.
import json, tempfile  # noqa: E401,E402
with tempfile.TemporaryDirectory() as td:
    p = Path(td) / "models.json"
    p.write_text(json.dumps({"makes": {"Toyota": {"4Runner": 50, "A3": 1}, "Audi": {"A3": 40}}}))
    own = js._pns_model_owners(p)
check("owner index: noise below the minimum ignored", own.get("a3") == {"Audi"} and own.get("4runner") == {"Toyota"}, own)

if fails:
    print(f"\n{len(fails)} FAILED")
    sys.exit(1)
print("\nall passed")
