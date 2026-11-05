#!/usr/bin/env python3
"""CURATION_SPEC.md §9 test_notes: the list-note classifier (§5.6)."""
import json
import random

from _util import FIX, check, done
import notes as N

T = json.loads((FIX / "notes_expected_f2652c3.json").read_text())
NSM = frozenset(T["ns_models"])
OWN = {"Camry Solara": "solara", "Camry Hybrid": "camry"}


def ctx(model, year):
    return N.NoteContext(year, frozenset([OWN.get(model, model.lower())]), NSM)


# 1. every one of the 152 real clauses classifies as committed (spec §5.6 table)
rows = T["rows"]
check("table holds the 152 distinct clauses of oem-raw@f2652c3", len({r[0] for r in rows}) == 152,
      str(len({r[0] for r in rows})))
bad = [(c, m, y, want, N.classify_clause(c, ctx(m, y)).cls) for c, m, y, want, _s in rows
       if N.classify_clause(c, ctx(m, y)).cls != want]
check("every real clause classifies into its committed class", not bad, str(bad[:5]))

# the spec's own examples, explicitly
SPEC = {
    "NEUTRAL_SPEC": ["12V 100A", "12V 1.7KW", "1.2 KW"],
    "PLANT": ["US Built", "USA Built", "US Built Only", "Japan Built", "Japan Build"],
    "ENGINE": ["2.4L", "3.0L", "3.5L"],
    "FUEL": ["Camry Hybrid"],
    "TRANS": ["Manual Transmission", "Auto Transmission"],
    "OPTION": ["With Heated", "Without Heated", "Power With Heater", "Without Auto Dimmer", "Without Memory",
               "With Signal Lamp", "Without HID", "With High Intensity Discharge", "Without Auto Level",
               "With Auto High Beam", "With Blind Spot", "With Auto A/C Control", "Without Atc",
               'Without 11.6" Display', "Power", "Manual"],
    "TRIM": ["With XLE", "Without SE", "SE", "LE & XLE", "CE PACKAGE CE PACKAGE&SEAT COVER MATERIAL-FABRIC",
             "Without Prime", "With Solara"],
    "BODY": ["Coupe", "Convertible"],
    "EMISSIONS": ["California Emissions", "Federal Emissions"],
    "PRODUCTION": ["From 4/97"],
    "PACKAGE": ["USA VALUE PACKAGE", "KOREA SPEC&KOREA UPPER PACKAGE KOREA SPEC&PRE-COLLISION SYSTEM-WITHOUT",
                "20TH ANNIVERSARY(USA)", "TOWING PACKAGE-FOR 3500LBS 12V 150A"],
    "COLOUR": ["White", "Blue Ribbon", "Jasper Pearl", "SUPER WHITE 2", "1D7", "3Q3", "040", "Red (3P5)"],
    "POSITION": ["Left", "Right", "Front", "On Body", "On Side Panel"],
    "UNKNOWN": ["Fki", "Nal", "(L)", "(J)", "All", "Control Panel", "NO PAINT REQ.",
                "OUTSIDE RR VIEW MIRROR-HEATED(EC)"],
}
for cls, xs in SPEC.items():
    got = {x: N.classify_clause(x, ctx("Camry", 2007)).cls for x in xs}
    check(f"spec examples classify as {cls}", all(v == cls for v in got.values()),
          str({k: v for k, v in got.items() if v != cls}))
check("NEUTRAL_MODEL: 'Camry' on a Camry cell", N.classify_clause("Camry", ctx("Camry", 2007)).cls == "NEUTRAL_MODEL")
check("MODEL_OTHER: 'Camry' on a Solara cell",
      N.classify_clause("Camry", ctx("Camry Solara", 2004)).cls == "MODEL_OTHER")
check("MODEL_OTHER: 'Prius', 'Sienna' on a Camry cell",
      all(N.classify_clause(x, ctx("Camry", 2007)).cls == "MODEL_OTHER" for x in ("Prius", "Sienna")))
y = N.classify_clause("2007-09", ctx("Camry", 2008))
check("YEARS inside the cell's year is satisfied (clean)", y.cls == "YEARS" and y.satisfied and y.neutral)
y = N.classify_clause("2007-09", ctx("Camry", 2010))
check("YEARS outside the cell's year restricts (listed_not_fitted)", y.cls == "YEARS" and not y.neutral)
check("'2016-18' resolves the century", N.classify_clause("2016-18", ctx("Prius", 2017)).satisfied is True)

# 2. safety invariant: nothing outside NEUTRAL_SPEC / NEUTRAL_MODEL /
# satisfied YEARS is ever neutral, and a neutral clause holds only neutral atoms
viol = []
for c, m, yy, want, _s in rows:
    cl = N.classify_clause(c, ctx(m, yy))
    if cl.neutral and not (cl.cls in N.NEUTRAL_CLASSES or (cl.cls == "YEARS" and cl.satisfied)):
        viol.append(c)
    if cl.neutral and any(a.cls not in N.NEUTRAL_CLASSES and a.cls != "YEARS" for a in cl.atoms):
        viol.append(c)
    if want not in ("NEUTRAL_SPEC", "NEUTRAL_MODEL", "YEARS") and cl.neutral:
        viol.append(c)
check("safety: no restricting clause is ever neutral (152 real clauses)", not viol, str(viol[:5]))
rnd = random.Random(7)
neutral_seeds = ["12V 100A", "Camry", "2007-09", "1.2 KW", "140 AMP", "New"]
words = ["Fki", "With", "US", "Built", "Heated", "XLE", "Red", "Left", "(J)", "SE", "Hybrid", "From", "4/97",
         "California", "Emissions", "Only", "All", "Coupe", "x", "&", "PACKAGE", "2.4L", "Gas"]
fuzz_bad = []
for _ in range(3000):
    base = rnd.choice(neutral_seeds)
    extra = " ".join(rnd.choice(words) for _ in range(rnd.randint(1, 3)))
    s = rnd.choice([f"{base} {extra}", f"{extra} {base}"])
    cl = N.classify_clause(s, ctx("Camry", 2008))
    if cl.neutral and any(a.cls not in N.NEUTRAL_CLASSES and a.cls != "YEARS" for a in cl.atoms):
        fuzz_bad.append(s)
    if cl.neutral and cl.leftover:
        fuzz_bad.append(s)
check("safety fuzz: a neutral clause plus any other word never stays neutral with a restricting atom",
      not fuzz_bad, str(fuzz_bad[:5]))
grow = [s for s in ("12V 100A Fki", "Camry Fki", "2007-09 Fki", "Camry XLE", "12V 100A US Built")
        if N.classify_clause(s, ctx("Camry", 2008)).neutral]
check("safety: known neutral clauses with appended text restrict", not grow, str(grow))

# 3. unknown text inside a known clause is UNKNOWN
c = N.classify_clause("US Built Fki", ctx("Camry", 2007))
check("'US Built Fki' is UNKNOWN (leftover)", c.cls == "UNKNOWN" and c.leftover == "Fki", f"{c.cls} {c.leftover!r}")

# 4. ';' segments are parsed
segs = N.split_note("Camry; Japan Built;Japan Build")
check("';' separates segments, ',' clauses", segs == [["Camry"], ["Japan Built"], ["Japan Build"]], str(segs))
v = N.classify(["US Built, Without Heated, Black;Without Heated, US Built, Black"], ctx("Camry", 2007))
check("two segments, three clauses each; restricting classes collected",
      len(v.segments) == 2 and all(len(s) == 3 for s in v.segments) and not v.clean
      and {"PLANT", "OPTION", "COLOUR"} <= v.classes, str(v.classes))
check("commas inside parentheses stay in one clause",
      N.split_clauses("Base (4WD, FWD), Latitude (4WD, FWD)") == ["Base (4WD, FWD)", "Latitude (4WD, FWD)"])

# 5. "SUPER WHITE 2,040" is COLOUR and does not crash
v = N.classify(["SUPER WHITE 2,040"], ctx("Camry", 2007))
check("'SUPER WHITE 2,040' classifies as COLOUR (two clauses)",
      [c.cls for s in v.segments for c in s] == ["COLOUR", "COLOUR"] and v.classes == {"COLOUR"})

# clean notes
v = N.classify(["12V 100A", "Camry; 2007-09"], ctx("Camry", 2008))
check("neutral spec + own model + satisfied years is clean", v.clean)
v = N.classify(["Patriot; 140 AMP", "140 AMP, New"], N.NoteContext(2014, frozenset(["patriot"]), frozenset()))
check("Jeep '140 AMP, New' on its own Patriot page is clean", v.clean)
check("empty notes are clean", N.classify([], ctx("Camry", 2007)).clean)

# Phase 2 DNF (§5.18): translatable atoms only
v = N.classify(["US Built, 2007-09"], ctx("Camry", 2007))
check("cond DNF of 'US Built, 2007-09' is plant=US", N.cond_dnf(v) == [{"plant": "US"}], str(N.cond_dnf(v)))
v = N.classify(["Japan Built, With XLE"], ctx("Camry", 2007))
check("TRIM is not translatable (Q3): no DNF", N.cond_dnf(v) is None)
v = N.classify(["Japan Built;US Built, 2.4L"], ctx("Camry", 2007))
check("segments are alternatives in the DNF",
      N.cond_dnf(v) == [{"plant": "JP"}, {"plant": "US", "engine": 2.4}], str(N.cond_dnf(v)))

# name qualifiers (§5.6): content tokens exempt
q = N.qualifier_phrases("Mirror Assy, Outer Rear View, W/Turn Signal Lamp", ["glass"], "side-mirrors")
check("qualifier 'W/Turn Signal Lamp' found", q and "Turn Signal Lamp" in q[0], str(q))
check("'Alternator Assembly, With Regulator' exempt (content token)",
      N.qualifier_phrases("Alternator Assembly, With Regulator", ["regulator", "pulley"], "alternator") == [])
check("'with motor' on regulators is packaging, not a qualifier",
      N.qualifier_phrases("Regulator Assy, W/Motor", [], "window-regulator") == [])
done("test_notes")
