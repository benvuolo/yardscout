#!/usr/bin/env python3
"""Regression checks for fail-open paths found in review (2026-11-05, after
the first real-data run on oem-raw@d1108d0). Each check fails on the code
before the fix and passes after it; ambiguity may only remove claims.

1. A regulator name's "W/Motor" phrase is packaging (§5.8), but a phrase
   that says more than packaging still conditions the car (§5.6).
2. An unparsed engine key ("?", raw) fails every universe test (§5.5),
   even when the universe and the row print the same text.
3. Notes feed position resolution through POSITION clauses only (§5.8): a
   colour ("Lt Gray") is not a side, while "Left" on a passenger part is
   still a conflict.
"""
import copy

from _util import TOY, check, confirmed, done, run, sienna_fixture
import curate as C
import notes as N

PSHA = C.policy_sha256()
ST = confirmed((TOY, "window-regulator"), policy_sha=PSHA)
S04 = ("Toyota", "Sienna", 2004)

# ------------------------------------------------------------------ 1
q = lambda s: N.qualifier_phrases(s, (), "window-regulator")  # noqa: E731
check("1 'W/Motor' on a regulator is packaging, not a qualifier",
      q("Regulator Assy, Front Door Window, W/Motor") == [])
check("1 'W/O Power Window Motor' is packaging", q("Regulator Sub-Assy W/O Power Window Motor") == [])
check("1 'W/Motor For Models With Jam Protection' still conditions the car",
      q("Regulator Assy W/Motor For Models With Jam Protection") != [],
      str(q("Regulator Assy W/Motor For Models With Jam Protection")))
check("1 'W/Motor & Auto Up' still conditions the car", q("Regulator Assy W/Motor & Auto Up") != [])
check("1 the exemption is regulator-only: 'W/Motor' on a mirror is a qualifier",
      N.qualifier_phrases("Mirror Assy W/Motor", (), "side-mirrors") != [])

# ------------------------------------------------------------------ 2
base_cur, base_doc = run("toyota", sienna_fixture(), status_table=ST)
check("2 control: the Sienna positive control ships one Verified group",
      len([g for g in base_doc["groups"] if g["cat"] == "window-regulator"]) == 1)

OLD = "6 Cyl 3.3 L GAS, 6 Cyl 3.5 L GAS"
NEW = "FUEL CELL EV (FCEV)"
files = sienna_fixture()
for rec in files[f"raw/{TOY}.jsonl"]:
    for f in rec["fitment"]:
        f["engines"] = [NEW]
        f["raw"] = f["raw"].replace(OLD, NEW)
    rec["evidence_lines"] = [NEW if x == OLD else x for x in rec["evidence_lines"]]
cur, doc = run("toyota", files, status_table=ST)
I = cur.cells_info[(S04, "window-regulator")]
check("2 every record still passes the evidence re-check",
      all(not r.problems for r in cur.records), str([(r.pn, r.problems) for r in cur.records if r.problems][:3]))
check("2 EngineU holds only the unparsed key", cur.engineu.get(S04) == frozenset({("?", NEW)}),
      str(cur.engineu.get(S04)))
check("2 an unparsed engine key on both sides is conditional_engines, never cover yes",
      all(m["cover"] == "maybe" and "conditional_engines" in m["why"] for m in I["members"].values()),
      str([(k, m["why"]) for k, m in I["members"].items()][:2]))
check("2 no Verified group from an unparsed engine universe",
      not [g for g in doc["groups"] if g["cat"] == "window-regulator"])

# ------------------------------------------------------------------ 3
PASS_REG = "69801-08S01"      # passenger front regulator in the fixture
files = sienna_fixture(extra_notes={(2004, PASS_REG): ["Lt Gray"], (2005, PASS_REG): ["Lt Gray"]})
cur, doc = run("toyota", files, status_table=ST)
m = cur.cells_info[(S04, "window-regulator")]["members"]["toyota:6980108S01"]
check("3 a colour note ('Lt Gray') is not a side: the passenger regulator stays in FR",
      m["slot"].slots == ("FR",) and m["slot"].reason is None, f"{m['slot']}")
check("3 the colour note still restricts the row (cover maybe, colour)",
      m["cover"] == "maybe" and "conditional_notes:colour" in m["why"], str(m["why"]))
check("3 and the restricted cell ships no Verified group", doc["groups"] == [])

files = sienna_fixture(extra_notes={(2004, PASS_REG): ["Left"], (2005, PASS_REG): ["Left"]})
cur, doc = run("toyota", files, status_table=ST)
m = cur.cells_info[(S04, "window-regulator")]["members"]["toyota:6980108S01"]
check("3 'Left' on a passenger part is still a position conflict (blocks every slot)",
      m["slot"].reason == "position_conflict" and set(m["slot"].slots) >= {"FL", "FR"}, f"{m['slot']}")

files = sienna_fixture(extra_notes={(2004, PASS_REG): ["Lt"], (2005, PASS_REG): ["Lt"]})
cur, doc = run("toyota", files, status_table=ST)
m = cur.cells_info[(S04, "window-regulator")]["members"]["toyota:6980108S01"]
check("3 an UNKNOWN clause ('Lt' alone) is read whole and may add a conflict",
      m["slot"].reason == "position_conflict", f"{m['slot']}")
del copy
done("test_regressions")
