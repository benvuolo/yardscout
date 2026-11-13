#!/usr/bin/env python3
"""Tests for notableTrims (notable_trims_from_spans), the per-model trim words
the app badges and filters on (design/notable-trims, 2026-11-13).

Covers:
  1. Words come only from non-option "trim" gates of the entries
     match_vehicle uses for that make/model over its modelYears span, with
     each row's yr_min/yr_max respected.
  2. Left out: option rows, words the model name already says, words with no
     letters, body styles; spelling variants collapse; lowercase match
     tokens get a display spelling.
  3. compact_inventory_v2 publishes it, merge_carryforward_yards recomputes
     it from the merged spans, the shard manifest carries it.
  4. The match_vehicle refactor (_keyword_hits/_matched_entries) keeps the
     specificity guard.

Run:  python3 scraper/test_notable_trims.py
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402
import inventory_shards as shards  # noqa: E402

failures = []


def check(name, cond, detail=""):
    print(("  ok  " if cond else "  FAIL") + f" {name}" + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        failures.append(name)


NT = js.notable_trims_from_spans


def words(make, model, lo, hi):
    return NT({make: {model: [lo, hi]}}).get(make, {}).get(model)


def gate_words(make, model, lo, hi):
    """Gate-derived words only (NOTABLE_TRIM_LABELS emptied for the call)."""
    saved = dict(js.NOTABLE_TRIM_LABELS)
    js.NOTABLE_TRIM_LABELS.clear()
    try:
        return words(make, model, lo, hi)
    finally:
        js.NOTABLE_TRIM_LABELS.update(saved)


print("derived from gates:")
check("Forester 1998-2024 -> ['XT']", words("Subaru", "Forester", 1998, 2024) == ["XT"],
      str(words("Subaru", "Forester", 1998, 2024)))
check("Ford F-150 -> Raptor", "Raptor" in (words("Ford", "F-150", 2010, 2020) or []))
check("Toyota 4Runner 2010-2024 has TRD Pro", "TRD Pro" in (words("Toyota", "4Runner", 2010, 2024) or []))
check("Nissan Frontier has PRO-4X", "PRO-4X" in (words("Nissan", "Frontier", 2005, 2020) or []),
      str(words("Nissan", "Frontier", 2005, 2020)))
# Outback: Wilderness row has yr_min 2022, so a span ending 2021 lists nothing.
check("Outback gates 2000-2021 -> none (Wilderness is 2022+)", gate_words("Subaru", "Outback", 2000, 2021) is None,
      str(gate_words("Subaru", "Outback", 2000, 2021)))
check("Outback gates 2000-2024 -> ['Wilderness']", gate_words("Subaru", "Outback", 2000, 2024) == ["Wilderness"])
check("unknown model -> omitted", NT({"Subaru": {"Nonesuch": [2000, 2010]}}) == {})
check("bad span skipped", NT({"Subaru": {"Forester": ["x", None]}}) == {})

print("left out / spelling:")
mus = words("Ford", "Mustang", 1990, 2020) or []
check("Mustang: GT kept, option-only GT350/Shelby left out",
      "GT" in mus and "GT350" not in mus and "Shelby" not in mus, str(mus))
check("Focus SVT: 'SVT' left out (model name says it)", "SVT" not in (words("Ford", "Focus SVT", 2002, 2004) or []))
isw = words("Lexus", "IS 250", 2006, 2015) or []
check("Lexus IS: no number-only words ('350', '500')", "350" not in isw and "500" not in isw, str(isw))
check("Lexus IS: F Sport and F-Sport collapse to one", sum(1 for w in isw if w.replace("-", " ") == "F Sport") == 1, str(isw))
check("Lexus IS: 'is f' shown as 'IS F'", "IS F" in isw, str(isw))
a5 = words("Audi", "A5", 2008, 2017)
check("Audi A5: body styles never a trim", not a5 or not ({"Cabriolet", "Convertible"} & set(a5)), str(a5))
imp = words("Subaru", "Impreza", 1993, 2014) or []
check("Impreza: 'wrx'/'sti' shown as 'WRX'/'STI'", "WRX" in imp and "STI" in imp, str(imp))
check("Impreza: '2.5RS' and '2.5 RS' collapse", sum(1 for w in imp if w.replace(" ", "") == "2.5RS") == 1, str(imp))
check("_trim_display keeps mixed case", js._trim_display("tS") == "tS" and js._trim_display("TRD Pro") == "TRD Pro")
check("_trim_display capitalises long lowercase", js._trim_display("hybrid") == "Hybrid")
check("_trim_word_key", js._trim_word_key("PRO-4X") == js._trim_word_key("Pro 4x") == "pro4x")

print("labels (NOTABLE_TRIM_LABELS, labels only):")
check("Outback 2000-2024 -> gate word first, then the label: ['Wilderness', 'XT']",
      words("Subaru", "Outback", 2000, 2024) == ["Wilderness", "XT"], str(words("Subaru", "Outback", 2000, 2024)))
check("Outback 2000-2021 -> label only: ['XT']", words("Subaru", "Outback", 2000, 2021) == ["XT"],
      str(words("Subaru", "Outback", 2000, 2021)))
check("Jeep Liberty (no trim gate) -> ['Renegade']", words("Jeep", "Liberty", 2002, 2012) == ["Renegade"],
      str(words("Jeep", "Liberty", 2002, 2012)))
check("labels key by the exact model: 'Legacy Outback' gets no XT label",
      "XT" not in (words("Subaru", "Legacy Outback", 2000, 2004) or []))
check("every label is a non-empty word with letters",
      all(w and any(c.isalpha() for c in w) for ws in js.NOTABLE_TRIM_LABELS.values() for w in ws))
# A label never reaches match_vehicle: same output with the table emptied.
_saved = dict(js.NOTABLE_TRIM_LABELS)
_cases = [(2008, "Subaru", "Outback", {"trim": "OBK 2.5XT LTD", "trimQuality": "usable"}),
          (2007, "Subaru", "Outback", {"trim": "XT Limited", "trimQuality": "usable"}),
          (2016, "Jeep", "Cherokee", {"trim": "Trailhawk", "trimQuality": "usable", "series": "KL"}),
          (2005, "Jeep", "Liberty", {"trim": "Renegade", "trimQuality": "usable", "series": "KJ"}),
          (2021, "Chevrolet", "Silverado 1500", {"trim": "Trail Boss - LT", "trimQuality": "usable", "series": "1500"})]
_with = [json.dumps(js.match_vehicle(y, mk, md, vin_decode=d), sort_keys=True, default=str) for y, mk, md, d in _cases]
js.NOTABLE_TRIM_LABELS.clear()
_without = [json.dumps(js.match_vehicle(y, mk, md, vin_decode=d), sort_keys=True, default=str) for y, mk, md, d in _cases]
js.NOTABLE_TRIM_LABELS.update(_saved)
check("labels change no match_vehicle output (5 label cars)", _with == _without)

print("specificity guard (refactor):")
gc = js._matched_entries(1998, js._keyword_hits("jeep grand cherokee"))
check("1998 Jeep Grand Cherokee: no plain 'cherokee' entry", all(kw != "cherokee" for kw, _ in gc), str([k for k, _ in gc]))
gw = gate_words("Jeep", "Grand Cherokee", 1993, 2024) or []
xj = gate_words("Jeep", "Cherokee", 1984, 2001) or []
check("Grand Cherokee words are not the XJ's (guard applies)", gw != xj or not xj, f"{gw} {xj}")

print("payload:")


def _ent(i, make, model, year):
    return {"id": i, "vin": "", "year": year, "make": make, "model": model, "row": "", "dateAdded": "",
            "location": "Y", "city": "C", "state": "AZ", "lat": 1.0, "lng": 2.0, "maxValue": 0, "topParts": []}


pl = js.compact_inventory_v2([_ent(1, "Subaru", "Forester", 2006), _ent(2, "Honda", "Fit", 2010)])
check("compact_inventory_v2 publishes notableTrims", pl.get("notableTrims") == {"Subaru": {"Forester": ["XT"]}},
      str(pl.get("notableTrims")))
_y2 = lambda name: dict(location=name, city="C", state="AZ", lat=1.0, lng=2.0)
newp = js.compact_inventory_v2([dict(_ent(1, "Subaru", "Forester", 2006), **_y2("A"))])
prevp = js.compact_inventory_v2([dict(_ent(7, "Ford", "F-150", 2012), **_y2("B"))])
js.merge_carryforward_yards(newp, prevp, ["B"])
check("carry-forward recomputes notableTrims", newp["notableTrims"].get("Ford", {}).get("F-150") == ["Raptor"]
      and newp["notableTrims"].get("Subaru", {}).get("Forester") == ["XT"], str(newp["notableTrims"]))
with tempfile.TemporaryDirectory() as td:
    pl.pop("_extras", None)
    shards.write_inventory_shards(pl, {}, Path(td))
    man = json.loads((Path(td) / "inv" / "manifest.json").read_text())
check("shard manifest carries notableTrims", man.get("notableTrims") == pl["notableTrims"], str(man.get("notableTrims")))

print()
if failures:
    print(f"{len(failures)} FAILED")
    sys.exit(1)
print("all passed")
