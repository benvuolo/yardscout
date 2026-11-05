#!/usr/bin/env python3
"""CURATION_SPEC.md §9 test_positions: positions, slots, packaging (§5.8)."""
from _util import by_pn, check, done, real, run, TOY
import positions as P

# token table
for text, want in [("Driver Side", "L"), ("Left", "L"), ("LH", "L"), ("L/H", "L"), ("LT", "L"),
                   ("Passenger Side", "R"), ("Right", "R"), ("RH", "R"), ("R/H", "R"), ("RT", "R"),
                   ("Left or Right", "B"), ("LH/RH", "B"), ("both sides", "B"), ("either side", "B"),
                   ("Driver Side Passenger Side", "X"), ("Front", None), ("", None)]:
    check(f"side token {text!r} -> {want}", P.side_of(text, "headlights") == want, str(P.side_of(text, "headlights")))
for text, want in [("Front", "F"), ("FR", "F"), ("Frt", "F"), ("Rear", "R"), ("RR", "R"), ("Sliding", "S"),
                   ("Front Rear", "X"), ("Driver Side", None)]:
    check(f"door token {text!r} -> {want}", P.door_of_text(text) == want, str(P.door_of_text(text)))
for url, want in [("https://x/parts-list/2004-toyota-sienna/body-hardware/front-door-body", "F"),
                  ("https://x/parts-list/2004-toyota-sienna/body-hardware/rear-door-body", "R"),
                  ("https://x/parts-list/2004-toyota-sienna/body-hardware/sliding-door-body", "S"),
                  ("https://x/parts-list/2004-toyota-sienna/body-hardware/door-body", None),
                  ("https://x/parts-list/2014-jeep-patriot/body-hardware/front-door", "F"),
                  ("https://x/parts-list/2014-jeep-patriot/body-hardware/door", None)]:
    check(f"door slug {url.rsplit('/', 1)[-1]} -> {want}", P.door_of_slug(url) == want)

# mirrors ignore Rear/Outer; lamps ignore Front
r = P.resolve("side-mirrors", [("position", "Rear Outer Driver Side")])
check("mirror 'Rear Outer Driver Side' -> L", r.slots == ("L",) and r.reason is None, str(r))
r = P.resolve("side-mirrors", [("position", "Rear Outer Passenger Side"), ("location", "Passenger Side")])
check("mirror 'Rear Outer Passenger Side' -> R", r.slots == ("R",) and r.reason is None, str(r))
r = P.resolve("headlights", [("position", "Front Driver Side")])
check("Jeep headlamp 'Front Driver Side' -> L", r.slots == ("L",) and r.reason is None, str(r))

# Toyota "Driver Side" + door slug
r = P.resolve("window-regulator", [("position", "Driver Side"),
                                   ("slug", "https://x/parts-list/2007-toyota-camry/body-hardware/front-door-body")])
check("Toyota 'Driver Side' with front-door-body -> FL", r.slots == ("FL",) and r.reason is None, str(r))
r = P.resolve("window-regulator", [("position", "Driver Side"),
                                   ("slug", "https://x/parts-list/1999-toyota-camry/body-hardware/rear-door-body")])
check("Toyota 'Driver Side' with rear-door-body -> RL", r.slots == ("RL",) and r.reason is None, str(r))

# 87940 records with other_names "Door Mirror, Front Right" still resolve to L
toy = real("toyota_f2652c3.jsonl")
rec = by_pn(toy, "87940-33630-B1")
check("fixture 87940-33630-B1 is a real driver mirror whose other_names name the wrong side",
      "Front Left" in rec["other_names"] or "Front Right" in rec["other_names"], rec["other_names"])
rec["other_names"] = "Mirror Assembly, Outer Rear View; Door Mirror, Front Right"
cur, doc = run("toyota", {f"raw/{TOY}.jsonl": [rec]})
cl = cur.classes[(rec_key := "toyota:8794033630B1", "side-mirrors")]
mem = cur.cell(("Toyota", "Camry", 2007), "side-mirrors")
check("87940 with other_names 'Front Right' still resolves to L (other_names never a source)",
      mem[rec_key]["slot"].slots == ("L",) and mem[rec_key]["slot"].reason is None, str(mem[rec_key]["slot"]))

# a source conflict blocks both slots
r = P.resolve("side-mirrors", [("position", "Driver Side"), ("location", "Passenger Side")])
check("position vs location conflict -> position_conflict in both slots",
      r.reason == "position_conflict" and set(r.slots) == {"L", "R"}, str(r))
r = P.resolve("side-mirrors", [("position", "Driver Side Passenger Side")])
check("L and R in one source without a both-sides pattern -> conflict", r.reason == "position_conflict")
r = P.resolve("side-mirrors", [("name", "Mirror Assembly")])
check("no side anywhere -> position_missing in both slots", r.reason == "position_missing" and set(r.slots) == {"L", "R"})
r = P.resolve("window-regulator", [("position", "Driver Side")])
check("regulator without a door -> position_missing in every left door slot",
      r.reason == "position_missing" and set(r.slots) == {"FL", "RL", "SL"}, str(r))
r = P.resolve("alternator", [("position", "Right Bank")])
check("a side token on a no-axis category -> unexpected_position", r.reason == "unexpected_position")

# window switch: Mopar passenger switch is out of the category; Toyota master -> DM
r = P.resolve("window-switch", [("position", "Front Passenger Side")])
check("Mopar 4602785AD Front Right -> out_of_category",
      P.window_switch_slot("Switch - Window And Door Lock", "Window Switch", r.side, r.door)[1] == "out_of_category")
r = P.resolve("window-switch", [("position", "Front Driver Side")])
check("Mopar Front Driver Side -> DM", P.window_switch_slot("Switch - Window And Door Lock", "", r.side, r.door) == ("DM", None))
check("Toyota Master Switch -> DM", P.window_switch_slot("Window Switch", "Master Switch Assembly", "L", None) == ("DM", None))
check("switch without a side -> position_missing",
      P.window_switch_slot("Switch - Window", "", None, None) == ("DM", "position_missing"))

# packaging
cases = [(["Window Regulator", "Regulator Sub-Assembly"], "reg"), (["Motor", "Motor Assembly, Power Window"], "motor"),
         (["Regulator Assy, Front Door Window, W/Motor"], "assy"), (["Regulator, Rear Door, W/O Motor"], "reg"),
         (["Regulator", "Regulator Assembly, Rear Door Window"], "reg?"), (["Panel Assy-Front Door Module"], "door-module")]
for names, want in cases:
    check(f"packaging {names[-1]!r} -> {want}", P.packaging("window-regulator", "toyota", "x", names) == want)
ch = {"a": "a", "b": "b", "c": "c", "d": "d"}
check("P1: one chain of assy is eligible", P.regulator_slot_ok([("a", "assy")], ch) is None)
check("P2: reg + motor is eligible", P.regulator_slot_ok([("a", "reg"), ("b", "motor")], ch) is None)
check("reg? present -> packaging_unstated", P.regulator_slot_ok([("a", "reg?"), ("b", "motor")], ch) == "packaging_unstated")
check("P1 and P2 together -> packaging_split",
      P.regulator_slot_ok([("a", "assy"), ("b", "reg"), ("c", "motor")], ch) == "packaging_split")
check("two chains of one packaging -> packaging_split",
      P.regulator_slot_ok([("a", "reg"), ("b", "reg"), ("c", "motor")], ch) == "packaging_split")
check("one chain of reg + reg (superseded) + motor is P2",
      P.regulator_slot_ok([("a", "reg"), ("b", "reg"), ("c", "motor")], {"a": "a", "b": "a", "c": "c"}) is None)
check("regulator alone without its motor -> packaging_incomplete", P.regulator_slot_ok([("a", "reg")], ch) == "packaging_incomplete")
check("hub T1: Toyota 55903 climate sub-assembly is switch-module",
      P.packaging("climate-control", "toyota", "55903-12100", ["Control Sub-Assembly, Heater"]) == "switch-module")
done("test_positions")
