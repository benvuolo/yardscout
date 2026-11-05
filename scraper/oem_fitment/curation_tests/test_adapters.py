#!/usr/bin/env python3
"""Adapters (§5.1, §5.2, §5.3, §5.5): input acceptance, field mapping,
evidence re-check, engine keys, trim atoms, and the PartsGiant rule mirror
against the template itself (no network)."""
import copy
import json
import sys

from _util import FIX, check, done, real
import adapters as A
import policy

toy, jeep, nis = real("toyota_f2652c3.jsonl"), real("jeep_94f03a3.jsonl"), real("nissan_94f03a3.jsonl")

# evidence re-check on real lines: 0 mismatches (AUDIT.md found 0 E)
probs = {}
for site, ns, lines in (("www.toyotapartsnow.com", "toyota", toy), ("www.jeeppartsdeal.com", "mopar", jeep),
                        ("www.nissanpartsdeal.com", "nissan", nis)):
    for i, o in enumerate(lines, 1):
        p = A.evidence_problems(A.to_record(site, ns, i, o))
        if p:
            probs[(site, o["pn"])] = p
check("evidence re-check passes every real fixture line", not probs, str(probs))
r = copy.deepcopy(toy[0])
r["fitment"][0]["years"] = [2007, 2010]
check("a changed fitment year is caught", "fitment_years_not_printed" in
      A.evidence_problems(A.to_record("www.toyotapartsnow.com", "toyota", 1, r)))
r = copy.deepcopy(toy[1])
r["replaces"] = ["28100-99999"]
check("a replaces number not printed is caught", "replaces_not_in_evidence" in
      A.evidence_problems(A.to_record("www.toyotapartsnow.com", "toyota", 1, r)))
r = copy.deepcopy(nis[0])
r["pn"] = "23100-JA11C"
check("PartsGiant: a pn not on the 'Part Number:' line is caught", "pn_not_in_evidence" in
      A.evidence_problems(A.to_record("www.nissanpartsdeal.com", "nissan", 1, r)))
r = copy.deepcopy(toy[2])
r["fitment"][0]["engines"] = ["2.5L L4"]
check("an engine not printed is caught", "fitment_cell_not_printed" in
      A.evidence_problems(A.to_record("www.toyotapartsnow.com", "toyota", 1, r)))

# review F6: the parsed fields that drive coverage must EQUAL the printed
# cells (not be substrings of them), the printed header must be the parsed
# layout's, and printed Replaces / Replaced By / Position must be parsed
TOYS = "www.toyotapartsnow.com"
SIEN = {"site": TOYS, "category": "window-regulator", "pn": "69801-08S01", "name": "Window Regulator",
        "aux_desc": "Regulator Sub-Assembly", "product_url": f"https://{TOYS}/oem/toyota~part~69801-08s01",
        "list_section": "diagram", "position": "Passenger Side", "replaces": [], "replaced_by": [],
        "fitment": [{"years": [2004, 2010], "make": "Toyota", "model": "Sienna",
                     "trims": ["CE", "LE", "Limited", "XLE", "XLE Limited"],
                     "engines": ["6 Cyl 3.3 L GAS", "6 Cyl 3.5 L GAS"],
                     "raw": "2004-2010 Toyota Sienna | CE, LE, Limited, XLE, XLE Limited | 6 Cyl 3.3 L GAS, 6 Cyl 3.5 L GAS"}],
        "evidence_lines": ["Position", "Passenger Side", "Vehicle Fitment", "Year Make Model", "Trim", "Engine",
                           "2004-2010 Toyota Sienna", "CE, LE, Limited, XLE, XLE Limited",
                           "6 Cyl 3.3 L GAS, 6 Cyl 3.5 L GAS"], "retrieved": "2026-11-05T01:23:03Z"}


def ev_probs(mut=None):
    o = copy.deepcopy(SIEN)
    if mut:
        mut(o)
    return A.evidence_problems(A.to_record(TOYS, "toyota", 1, o))


check("F6 baseline: the Sienna regulator record is consistent", ev_probs() == [], str(ev_probs()))


def trim_cell(o):
    old = "CE, LE, Limited, XLE, XLE Limited"
    o["fitment"][0]["raw"] = o["fitment"][0]["raw"].replace(old, "CE, XLE, XLE Limited")
    o["evidence_lines"] = ["CE, XLE, XLE Limited" if x == old else x for x in o["evidence_lines"]]


check("F6 printed trim cell 'CE, XLE, XLE Limited' with parsed LE/Limited ('LE' is inside 'XLE'): caught",
      "fitment_cell_not_printed" in ev_probs(trim_cell), str(ev_probs(trim_cell)))


def fourth_col(o):
    o["fitment"][0]["raw"] += " | With Power Sliding Door"
    o["evidence_lines"].insert(o["evidence_lines"].index("Engine") + 1, "Important vehicle option details")
    o["evidence_lines"].append("With Power Sliding Door")


check("F6 a 4th printed option column the record does not carry (layout stays 'trim'): caught",
      {"fitment_cell_count", "fitment_header_not_layout"} <= set(ev_probs(fourth_col)), str(ev_probs(fourth_col)))


def solara(o):
    o["fitment"][0]["model"] = "Camry"
    o["fitment"][0]["raw"] = o["fitment"][0]["raw"].replace("Toyota Sienna", "Toyota Camry Solara")
    o["evidence_lines"] = [x.replace("Toyota Sienna", "Toyota Camry Solara") for x in o["evidence_lines"]]


check("F6 parsed model 'Camry' on a printed 'Camry Solara' row: caught",
      "fitment_model_not_printed" in ev_probs(solara), str(ev_probs(solara)))


def rb_dropped(o):
    o["evidence_lines"] = ["Replaced By", "69801-08S50"] + o["evidence_lines"]


check("F6 a printed 'Replaced By' number missing from the record: caught",
      "printed_replaced_by_not_in_record" in ev_probs(rb_dropped), str(ev_probs(rb_dropped)))


def rp_dropped(o):
    o["evidence_lines"] = ["Replaces", "69801-08S00"] + o["evidence_lines"]


check("F6 a printed 'Replaces' number missing from the record: caught",
      "printed_replaces_not_in_record" in ev_probs(rp_dropped))
check("F6 a printed Position the record lost: caught",
      "printed_position_not_in_record" in ev_probs(lambda o: o.update(position=None)))


def engine_extra(o):
    o["fitment"][0]["engines"] = ["6 Cyl 3.3 L GAS"]


check("F6 parsed engines narrower than the printed engine cell: caught",
      "fitment_cell_not_printed" in ev_probs(engine_extra))
check("F6 option layout: the printed option cell must equal other_columns",
      A.evidence_problems(A.to_record(TOYS, "toyota", 1, toy[0])) == []
      and "fitment_cell_not_printed" in A.evidence_problems(A.to_record(TOYS, "toyota", 1, {
          **copy.deepcopy(toy[0]), "fitment": [dict(f, other_columns={"Important vehicle option details": "2AZFE"})
                                               for f in toy[0]["fitment"]]})))
pg = copy.deepcopy(nis[0])
pg["fitment"] = [dict(f, trims=f["trims"][:1]) if f["trims"] else f for f in pg["fitment"]]
check("F6 PartsGiant: parsed trims narrower than the printed trim cell are caught",
      any(f["trims"] for f in nis[0]["fitment"])
      and "fitment_cell_not_printed" in A.evidence_problems(A.to_record("www.nissanpartsdeal.com", "nissan", 1, pg)))

# field mapping
rec = A.to_record("www.nissanpartsdeal.com", "nissan", 1, nis[0])
check("PartsGiant 'Replaced By:' info feeds the chain, not the notes",
      "2310M-JA11RRW" in rec.list_replaced_by and not any("Replaced" in n for n in rec.note_texts))
check("PartsGiant 'Fitting Vehicle Options' info is a note", any("Fitting Vehicle Options" in n for n in rec.note_texts))
check("PartsGiant non-trim options column is option layout", all(f.layout == "option" for f in rec.rows))
o = copy.deepcopy(nis[0])
o["replaced_by"] = "(MultiSupersession)"
check("'(MultiSupersession)' makes the record chain_unknown",
      A.to_record("www.nissanpartsdeal.com", "nissan", 1, o).chain_unknown)
o = {"site": "www.moparpartsgiant.com", "category": "headlights", "pn": "5113332AD", "list_info": ["Right"],
     "fitment": [{"years": [2008, 2010], "make": "Dodge", "model": "Grand Caravan", "trims": ["SE"],
                  "engines": [], "options": ["SE"], "raw": "x"}]}
rec = A.to_record("www.moparpartsgiant.com", "mopar", 1, o)
check("Mopar bare 'Right' list info is a position, not a note", rec.list_location == ["Right"] and rec.note_texts == [])
check("option_column_is_trims sites: options are trims (rows marked so)", rec.rows[0].layout == "trim"
      and rec.rows[0].trims_from_options)
rec = A.to_record("www.toyotapartsnow.com", "toyota", 1, toy[0])
check("SimplePart other_columns row is option layout", rec.rows[0].layout == "option")

# engine keys (§5.5 table) and trim atoms
EK = [("4 Cyl 2.4 L GAS", (4, 2.4, "gas")), ("4 Cyl 2.4 L FULL HYBRID EV-GAS (FHEV)", (4, 2.4, "hybrid")),
      ("4 Cyl 1.8 L PLUG-IN HYBRID EV-GAS (PHEV)", (4, 1.8, "phev")), ("4 Cyl 2.2 L CNG", (4, 2.2, "cng")),
      ("8 Cyl 5.7 L FLEX", (8, 5.7, "flex")), ("2.4L L4", (4, 2.4, None)), ("6 Cyl 3.5L", (6, 3.5, None))]
for printed, want in EK:
    check(f"engine key {printed!r}", A.engine_key(printed) == want, str(A.engine_key(printed)))
check("FUEL CELL EV (FCEV) is ('?', raw)", A.engine_key("FUEL CELL EV (FCEV)")[0] == "?")
check("anything else is ('?', raw)", A.engine_key("DOHC - MPI")[0] == "?" and A.engine_key("2.5L H4 Turbo")[0] == "?")
check("trim atoms 'Base (4WD, FWD)'", A.trim_atoms("Base (4WD, FWD)") == [("base", "4wd"), ("base", "fwd")])
check("trim atoms 'XLE  Limited' collapse whitespace", A.trim_atoms("XLE  Limited") == [("xle limited", "")])

# input acceptance
p = A.parse_jsonl('{"a": 1}\n{"b": 2}\n{"c": ', fixtures=False)
check("torn tail skipped", len(p.objs) == 2 and p.issues[0][0] == "torn_tail" and not p.refused)
p = A.parse_jsonl('{"a": 1}\n{oops\n{"b": 2}\n', fixtures=False)
check("corrupt middle line refuses the file", p.refused and p.objs == [])
p = A.parse_jsonl('{"a": 1, "synthetic": true}\n', fixtures=False)
check("synthetic refused without --fixtures", p.objs == [] and p.issues[0][0] == "synthetic_refused")
check("synthetic accepted with --fixtures", len(A.parse_jsonl('{"a": 1, "synthetic": true}\n', fixtures=True).objs) == 1)

# rule drift re-run offline; the PartsGiant mirror equals the template
check("rule re-run: a real Toyota record still matches its site rule",
      A.rule_matches(A.to_record("www.toyotapartsnow.com", "toyota", 1, toy[0])) is True)
bootrec = {"site": "www.jeeppartsdeal.com", "category": "headlights", "pn": "5143152AA", "name": "Headlamp",
           "aux_desc": "Boot", "product_url": "https://www.jeeppartsdeal.com/oem/mopar~boot~5143152AA",
           "list_section": "diagram", "fitment": []}
check("rule re-run: the AUDIT.md headlamp boot now fails the fixed Jeep rule (rule_drift)",
      A.rule_matches(A.to_record("www.jeeppartsdeal.com", "mopar", 1, bootrec)) is False)
check("site modules load without network (stub fetch)", A.site_module("www.nissanpartsdeal.com") is not None
      and "requests" not in sys.modules.get("fetch").__dict__)
mod = A.site_module("www.nissanpartsdeal.com")
T = sys.modules["sites._partsgiant"]
rows = [{"pn": "23100-JA11B", "group": "Generator", "main": "Generator", "remark": "", "info": [], "url": "/p/1"},
        {"pn": "23100-X", "group": "Generator", "main": "Pulley-Alternator", "remark": "", "info": [], "url": "/p/2"},
        {"pn": "23100-Y", "group": "Generator", "main": "Bolt", "remark": "", "info": [], "url": "/p/3"},
        {"pn": "26060-Z", "group": "Headlamp", "main": "Headlamp Assy-Lh", "remark": "", "info": [], "url": "/p/4"}]
saved = (T._page, T.list_parts)
T._page = lambda url: {"html": ""}
T.list_parts = lambda html: copy.deepcopy(rows)
try:
    for cat in ("alternator", "headlights"):
        tpl = {x["pn"] for x in T.parts_on_page(mod.CFG, "https://x/parts-list/a.html", cat)}
        mine = {x["pn"] for x in rows if A.pg_row_matches(T, mod.CFG, cat, x)}
        check(f"PartsGiant rule mirror equals the template ({cat})", tpl == mine, f"{tpl} vs {mine}")
finally:
    T._page, T.list_parts = saved
check("site_cat_pages reads CAT_PAGES / SUBCATS offline",
      "window-regulator" in A.site_cat_pages("www.toyotapartsnow.com")
      and "alternator" in A.site_cat_pages("www.nissanpartsdeal.com"))
done("test_adapters")
