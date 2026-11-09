#!/usr/bin/env python3
"""Path E (engine-gated Likely, ops/interchange.md "Category breadth"):
curate._gated_engines and the model_engine_conflict lint, both ways. The
Lexus case is lexuspartsnow 22030-31040, whose page prints the GS200t (a
2.0T) and the GS430 (a 4.3 V8) as "6 Cyl 3.5L | 2GRFSE"."""
from collections import Counter
from types import SimpleNamespace

from _util import check, done
import adapters as A
import curate as C
import policy

CAT = "ac-compressor"


def row(engines, model="GS350"):
    return A.FitRow(idx=0, lo=2016, hi=2016, make="Lexus", model=model, trims=[], engines=engines,
                    options=[], layout="trim", raw="")


def cur_for(T, engines, decoded=None, universe=None, model="GS350"):
    c = SimpleNamespace(pns={"22030-31040"}, records=[])
    cur = SimpleNamespace(t_rows={(T, CAT): [(c, None, row(engines, model), None)]},
                          engineu={T: frozenset(universe or ())}, decoded={T: Counter(decoded or {})},
                          engine_gated_lint=Counter(), refusals=[])
    cur.refuse = lambda reason, **kw: cur.refusals.append(reason)
    return cur, c


V6 = "6 Cyl 3.5L"
# GS200t: three decoded 2.0L 4-cyl cars on the lot, the row says 3.5 V6 -> dropped
T = ("Lexus", "GS200t", 2016)
cur, c = cur_for(T, [V6], decoded={(4, 2.0): 3}, model="GS200t")
check("GS200t printed as 3.5L V6 with 3 decoded 2.0T cars: dropped (model_engine_conflict)",
      C._gated_engines(cur, T, CAT, c) is None and cur.engine_gated_lint["model_engine_conflict"] == 1
      and cur.refusals == ["model_engine_conflict"])
# GS430: decoded 4.3 V8 -> dropped
T = ("Lexus", "GS430", 2006)
cur, c = cur_for(T, [V6], decoded={(8, 4.3): 5}, model="GS430")
check("GS430 printed as 3.5L V6 with decoded 4.3 V8 cars: dropped", C._gated_engines(cur, T, CAT, c) is None)
# GS350 decoded 3.5 V6 -> kept, labelled for the client's engine parse
T = ("Lexus", "GS350", 2016)
cur, c = cur_for(T, [V6], decoded={(6, 3.5): 4})
check("GS350 3.5L V6 with matching decodes: kept as '3.5L 6-cyl'",
      C._gated_engines(cur, T, CAT, c) == ["3.5L 6-cyl"] and not cur.refusals)
# below the decoded minimum: kept (the client's engine gate still applies)
cur, c = cur_for(("Lexus", "GS200t", 2016), [V6], decoded={(4, 2.0): policy.MODEL_ENGINE_CONFLICT_MIN - 1},
                 model="GS200t")
check("fewer than MODEL_ENGINE_CONFLICT_MIN decodes: not dropped by the lint",
      C._gated_engines(cur, ("Lexus", "GS200t", 2016), CAT, c) == ["3.5L 6-cyl"])
# mixed decodes with one listed engine present: kept
T = ("Lexus", "GS350", 2016)
cur, c = cur_for(T, [V6], decoded={(6, 3.5): 1, (8, 4.6): 5})
check("one decoded car carries the listed engine: kept", C._gated_engines(cur, T, CAT, c) == ["3.5L 6-cyl"])
# hybrid engine never claimed
cur, c = cur_for(T, ["6 Cyl 3.5L Hybrid"])
check("hybrid engine cell: never claimed", C._gated_engines(cur, T, CAT, c) is None
      and cur.engine_gated_lint["engine_fuel_excluded"] == 1)
# gas engine whose hybrid twin is in T's universe but not listed: dropped
cur, c = cur_for(T, ["6 Cyl 3.5L Gas"], universe=[(6, 3.5, "gas"), (6, 3.5, "hybrid")])
check("unlisted same-displacement fuel twin in the universe: dropped (engine_fuel_twin)",
      C._gated_engines(cur, T, CAT, c) is None and cur.engine_gated_lint["engine_fuel_twin"] == 1)
# unparsed engine cell: whole vehicle-year dropped
cur, c = cur_for(T, ["2GRFSE"])
check("unparsed engine cell: dropped (engine_unparsed)", C._gated_engines(cur, T, CAT, c) is None
      and cur.engine_gated_lint["engine_unparsed"] == 1)
# Toyota 'L' layout parses too
cur, c = cur_for(("Toyota", "Camry", 2008), ["2.4L L4", "3.5L V6"])
check("Toyota '2.4L L4' / '3.5L V6' cells parse",
      C._gated_engines(cur, ("Toyota", "Camry", 2008), CAT, c) == ["2.4L 4-cyl", "3.5L 6-cyl"])
check("decoded-engine parse matches the client ('3.7L 6-cyl')",
      C._decoded_engines({"fields": ["id", "a", "year", "make", "model"],
                          "vehicles": [[1, 0, 2007, "Jeep", "Liberty"]]},
                         {"extras": {"1": ["x", "", "3.7L 6-cyl"]}})[("Jeep", "Liberty", 2007)] == Counter({(6, 3.7): 1}))
src = (C.HERE / "policy.py").read_text() if hasattr(C, "HERE") else open(policy.__file__).read()
check("path E constants live in policy.py (hashed into policy_sha256)",
      all(x in src for x in ("ENGINE_GATED_CATS", "ENGINE_GATED_NEVER_FUELS", "MODEL_ENGINE_CONFLICT_MIN")))
check("path E categories are never body kinds handled by the body Likely loop",
      policy.ENGINE_GATED_CATS <= policy.PHASE3_CATS and not (policy.ENGINE_GATED_CATS & policy.EXTERIOR_HOLD_CATS))
check("rule 4: no engine/transmission/converter category is engine-gated",
      not any(policy.RULE4_RE.search(c.replace("-", " ")) for c in policy.ENGINE_GATED_CATS))
done("test_engine_gated")
