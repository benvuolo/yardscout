#!/usr/bin/env python3
"""Tier C wiper-motor rules (ops/interchange.md §10 wiper handover): the end
axis (F windshield / R rear), twin-motor sides, packaging and the slot sets."""
from _util import check, done
import policy
import positions as P

W = "wiper-motor"
for text, want in [("Motor Assy-Windshield Wiper", "F"), ("Motor, FR. Wiper", "F"), ("Front Motor", "F"),
                   ("Motor Assy-Rear Wiper", "R"), ("Motor, RR. Windshield Wiper", "R"),
                   ("Motor Assy., RR. Windshield Wiper", "R"), ("MOTOR Liftgate Wiper", "R"),
                   ("Motor Assy-Back Door Wiper", "R"), ("Drive Assy-Rear Window Wiper", "R"),
                   ("Wiper Motor", None), ("Motor", None), ("Front and Rear", "X")]:
    check(f"end {text!r} -> {want}", P.end_of_text(text) == want, str(P.end_of_text(text)))
for url, want in [("https://x/parts-list/2011-hyundai-tucson/electrical/windshield_wiper_rear.html", "R"),
                  ("https://x/parts-list/2005-honda-accord/front_windshield_wiper.html", None),
                  ("https://x/ford/windshield_wiper.html", None),
                  ("https://x/ford/rear_liftgate_wiper_washer.html", "R"),
                  ("https://x/oem-parts/a/b/front-motor", None),
                  ("https://x/oem-parts/a/b/rear-motor", "R"),
                  ("https://x/v/2012-vw-jetta/electrical/wipers", None),
                  ("https://x/v/2012-vw-jetta/body-hardware/wiper-washer-components", None)]:
    check(f"end slug {url.rsplit('/', 1)[-1]} -> {want}", P.end_of_slug(url) == want, str(P.end_of_slug(url)))

r = P.resolve(W, [("name", "Motor Assy-Windshield Wiper")])
check("windshield motor -> F", r.slots == ("F",) and r.reason is None, str(r))
r = P.resolve(W, [("name", "Motor Assy-Windshield Wiper, LH"), ("location", "Driver Side")])
check("twin motor LH -> FL", r.slots == ("FL",) and r.reason is None, str(r))
r = P.resolve(W, [("name", "Wiper Motor"), ("position", "Passenger Side"), ("slug", "https://x/front-motor")])
check("front slug is no evidence (windshield pages carry rear motors) -> position_missing",
      r.reason == "position_missing", str(r))
r = P.resolve(W, [("name", "Wiper Motor"), ("slug", "https://x/rear_window_wiper.html")])
check("rear slug fallback -> R", r.slots == ("R",) and r.reason is None, str(r))
r = P.resolve(W, [("name", "Motor, RR. Windshield Wiper"), ("position", "Rear")])
check("Honda rear-glass motor -> R", r.slots == ("R",) and r.reason is None, str(r))
r = P.resolve(W, [("name", "Wiper Motor"), ("slug", "https://x/wipers")])
check("no end anywhere -> position_missing, blocks every slot",
      r.reason == "position_missing" and set(r.slots) == {"F", "FL", "FR", "R"}, str(r))
r = P.resolve(W, [("name", "Motor Assy - Wiper"), ("position", "Rear"), ("slug", "https://x/windshield_front_wiper.html")])
check("slug only a fallback: position Rear on a front page -> R", r.slots == ("R",), str(r))
r = P.resolve(W, [("name", "Motor Assy-Rear Wiper"), ("note", "Front wiper")])
check("rear name + front note -> position_conflict", r.reason == "position_conflict", str(r))
r = P.resolve(W, [("name", "Motor Assy-Rear Wiper"), ("location", "Driver Side")])
check("rear motor with a side -> position_conflict", r.reason == "position_conflict", str(r))
r = P.resolve(W, [("name", "Motor Assy-Windshield Wiper"), ("location", "Left or Right")])
check("one number both sides -> position_conflict", r.reason == "position_conflict", str(r))

for names, want in [(["Motor Assy-Windshield Wiper"], "motor"), (["Drive Assy-Windshield Wiper"], "drive"),
                    (["Motor And Linkage Assy"], "drive"), (["MOTOR KIT Windshield Wiper"], "kit"),
                    (["MOTOR PACKAGE Front Wiper"], "kit"), (["Linkage Assy - Wiper"], "linkage"),
                    (["MOTOR, WIPER (EXCEPT CIRCUIT BOARD)"], "motor-ecb"),
                    (["MODULE ASM, WSW (W/ TRANSMISSION)"], "module"), (["Motor & Link Assy-Wiper"], "module")]:
    check(f"wiper packaging {names[0]!r} -> {want}", P.packaging(W, "x", "x", names) == want,
          P.packaging(W, "x", "x", names))

req = [set(x) for x in policy.cat_policy(W)["required"]]
check("F alone closes", {"F"} in req)
check("F + R closes", {"F", "R"} in req)
check("twin pair closes", {"FL", "FR"} in req and {"FL", "FR", "R"} in req)
check("a lone sided front motor closes nothing", {"FL"} not in req and {"FL", "R"} not in req)
check("rear alone closes nothing", {"R"} not in req)
check("F with a twin half is not a configuration", not any({"F", "FL"} <= s for s in req))
check("NOUN wiper-motor", policy.NOUN.get(W) == r"wiper")
# Likely-group strict refusal (hub 2026-11-09 18:20) and the note words
import curate as CU


class _K:
    def __init__(self, packaging):
        self.packaging = packaging


def _stub(cells, notes):
    cur = object.__new__(CU.Curation)
    cur.cells_info = cells
    cur.t_sources = {}
    cur.ns_models_f = frozenset()
    cur.own_page = lambda T, cat, c: (True, notes.get(T, []), [], [], "manifest")
    return cur


TA, TB = ("Kia", "Forte", 2012), ("Kia", "Soul", 2012)
m_ok = {"slot": P.Resolution(("F",), None, None, "F")}
m_miss = {"slot": P.Resolution(("F", "FL", "FR", "R"), "position_missing")}
m_fl = {"slot": P.Resolution(("FL",), None, "L", "F")}
cells_f = {(T, W): {"slots": {"F": []}} for T in (TA, TB)}
cur = _stub(cells_f, {})
check("clean motor, one slot, no notes -> group allowed",
      cur._strict_refusal(_K("motor"), W, [(TA, m_ok), (TB, m_ok)], {"F"}) is None)
check("module packaging -> refused", cur._strict_refusal(_K("module"), W, [(TA, m_ok), (TB, m_ok)], {"F"})[0]
      == "packaging_unstated")
check("unresolved position on one app -> refused",
      cur._strict_refusal(_K("motor"), W, [(TA, m_ok), (TB, m_miss)], {"F"})[0] == "strict_position")
check("two slots in one group -> refused",
      cur._strict_refusal(_K("motor"), W, [(TA, m_ok), (TB, m_ok)], {"F", "R"})[0] == "strict_position")
check("lone FL (single motor printed 'Front Driver Side') -> refused",
      cur._strict_refusal(_K("motor"), W, [(TA, m_fl), (TB, m_fl)], {"FL"})[0] == "strict_position")
cur2 = _stub({(T, W): {"slots": {"FL": [], "FR": []}} for T in (TA, TB)}, {})
check("FL with FR on every app's page -> allowed",
      cur2._strict_refusal(_K("motor"), W, [(TA, m_fl), (TB, m_fl)], {"FL"}) is None)
for note in ["Production Date: 09/1996-07/2001", "Sedan", "Fitting Vehicle Options: VQ35DE", "Japan Built"]:
    cur3 = _stub(cells_f, {TB: [note]})
    r = cur3._strict_refusal(_K("motor"), W, [(TA, m_ok), (TB, m_ok)], {"F"})
    check(f"own-page note {note!r} -> strict_note", bool(r) and r[0] == "strict_note", str(r))
check("note words: rear motor with linkage",
      CU._pack_text(W, "drive", "R") == "rear wiper motor with linkage")
check("note words: windshield motor", CU._pack_text(W, "motor", "F") == "windshield wiper motor")
check("note words: no words for an unknown slot", CU._pack_text(W, "motor", "F+R") == "")
check("other categories keep their words",
      CU._pack_text("window-regulator", "motor") == "window motor only" and CU._pack_text("radiator", "") == "")
done("test_wiper_motor")
