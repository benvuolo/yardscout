#!/usr/bin/env python3
"""Round 11 (interchange 2026-11-20, branch interchange/round11-1120): packaging
words on the live makes, read from every naming or describing field the raw
prints (curate.ROUND11_NS, _kind11, Curation._wide_names11, _r11_words).
- bumper covers: "bumper cover", "bumper cover only" when every own page lists
  a reinforcement as a separate number; tail lamps "lens and body unit";
  regulators named with their motor "regulator with motor".
- 11b: a bumper number whose values name a part other than the bumper cover or
  the bumper (guard cover, tow-hook cover, grille, moulding, reinforcement,
  bracket, absorber) is held.
- 11c (after the independent check found 4 WRONG): the fields include the list
  group, remark (read with the name), notes, list_info and 'Part Description:'
  lines, on every page of every raw part whatever the page's category; 'less
  motor' beside 'with motor' holds; a value saying less motor gives "regulator
  without motor", and that phrase stays on a note only with such a value or
  every own page listing the motor separately; a bare "Bumper" whose own page
  lists a separate cover is held (unless chrome / face bar / bar only); lamp
  assembly and lens and body are one unit: mixed values, no words, not held."""
import json
import re
from types import SimpleNamespace

from _util import OEM, check, done
import adapters as A
import curate as C
import policy

TPN = "www.toyotapartsnow.com"


def lr(ns, pn, main, cat, url="https://x/page", aux="", line=1, site=TPN, group="", remark="", notes=()):
    return A.ListRow(site=site, seed=("Toyota", "Camry", 2010), cat=cat, list_url=url, pn=pn, section="diagram",
                     main=main, aux=aux, notes=list(notes), locations=[], replace=None, matched=True, excluded_by=None,
                     product=None, retrieved="", line=line, status=200, group=group, remark=remark)


class _K:
    def __init__(self, ns, pn, name="", description="", other_names="", site=TPN, raw=None):
        self.key, self.pns = policy.pn_key(ns, pn), {pn}
        self.records = [SimpleNamespace(site=site, name=name, aux="", description=description, other_names=other_names,
                                        oem_names=[name], pointer=f"{site}:records:L9", raw=raw or {})] if name else []


class _Cur:
    for _m in ("_r11_words", "_wide_names11", "_r11c_rows", "_r11c_page", "_r11c_page_has"):
        locals()[_m] = getattr(C.Curation, _m)

    def __init__(self, ns, rows, more=()):
        self.ns, self.list_rows, self.list_rows_more = ns, list(rows), list(more)


NOTE = "Toyota catalog lists #X for both — fits some configurations; verify the number on the part"
NOTE_LESS = "Toyota catalog lists #X for both — regulator without motor; fits some configurations; verify the number on the part"


def words(ns, cat, pn, mains, k, others=(), note=NOTE, more=()):
    rows = [lr(ns, pn, m, cat, line=i + 1) for i, m in enumerate(mains)] + list(others)
    return _Cur(ns, rows, more)._r11_words(k, cat, note, "C")


# ------------------------------------------------------------ the kinds
for cat, name, want in (("bumper-front", "Cover, Front Bumper", "cover"), ("bumper-front", "Fascia - Front", "cover"),
                        ("bumper-front", "Cover, Front Bumper Guard, RH", "guard cover"),
                        ("bumper-front", "Cover, Tow Hook", "tow-hook cover"), ("bumper-front", "Grille, Front Bumper", "grille"),
                        ("bumper-front", "Moulding, Front Bumper", "moulding"), ("bumper-front", "Stay, Front Bumper", "bracket"),
                        ("bumper-front", "Absorber, Front Bumper Energy", "absorber"), ("bumper-rear", "Beam Asy", "reinforcement"),
                        ("bumper-front", "Impact Bar - Steel", "reinforcement"), ("bumper-front", "Bumper Assy - Front", "bumper"),
                        ("bumper-front", "Face Bar", "bar"), ("bumper-front", "Chrome", "bar"), ("bumper-front", "W/O CHROME", ""),
                        ("tail-lights", "Lens & Body, Rear Combination Lamp, RH", "lens-body"),
                        ("tail-lights", "Lens & Housing", "lens-body"), ("tail-lights", "Tail Light Assembly, Rear Right", "assembly"),
                        ("tail-lights", "Socket & Wire Sub-Assy, Rear Combination Lamp", "socket"), ("tail-lights", "Tail Lamps", ""),
                        ("window-regulator", "REGULATOR, FRONT SIDE DOOR WINDOW(INCLUDES 13)(INCLUDES MOTOR)", "regulator+motor"),
                        ("window-regulator", "Regulator & Motor Assembly-Front Right", "regulator+motor"),
                        ("window-regulator", "Regulator - Window - Less Motor", "regulator-less"),
                        ("window-regulator", "REGULATOR ASY. (FRONT DOOR WINDOW) ELECTRIC - LESS MOTOR AND DRIVE", "regulator-less"),
                        ("window-regulator", "Window Motor", "motor")):
    check(f"kind: {cat} {name!r} -> {want or 'neither'}", C._kind11(cat, name) == want, C._kind11(cat, name))

# ------------------------------------------------------------ 11c: the fields read
K = _K("ford", "5G1Z-5423208-AA", "Regulator And Motor Assy - Window",
       raw={"list_group": "Regulator - Window - Less Motor", "list_info": ["Regulator - Window - Less Motor",
                                                                           "Location: Passenger Side"],
            "evidence_lines": ["Part Description: Regulator And Motor Assy - Window"]})
row = lr("ford", "5G1Z-5423208-AA", "Regulator And Motor Assy - Window", "window-regulator",
         group="Regulator - Window - Less Motor", notes=["Regulator - Window - Less Motor", "Callout Name: <23208"])
vals = _Cur("ford", [row])._wide_names11(K, "window-regulator")
check("11c fields: list group, list notes, record list_group, list_info and 'Part Description:' are read; keyed callout "
      "and location lines are not",
      {f for f, _n, _p in vals} >= {"list.group", "list.notes", "record.list_group", "record.list_info",
                                    "record.part_description"}
      and not any(n.startswith(("Callout", "Location")) for _f, n, _p in vals), vals)
r = _Cur("ford", [row])._r11_words(K, "window-regulator", NOTE, "C")
check("11c: the Montego pair ('Regulator And Motor Assy' named, list group 'Less Motor') is held, no phrase",
      r and r.get("hold") and r["hold"][0] == "held_name_disagree" and not r.get("phrase"), r)
gmrow = lr("gm", "13265066", "MOTOR", "window-regulator", remark="REAR SIDE DOOR WINDOW REGULATOR(*KIT1)",
           group="MOTOR, Rear Door Window Regulator")
kg = _K("gm", "13265066", "MOTOR, REAR SIDE DOOR WINDOW REGULATOR(PART OF 4)",
        raw={"list_remark": "REAR SIDE DOOR WINDOW REGULATOR(PART OF 4)"})
check("11c: GM's remark is read with its name ('MOTOR' + 'REAR SIDE DOOR WINDOW REGULATOR'), never alone: no disagreement",
      _Cur("gm", [gmrow])._r11_words(kg, "window-regulator", NOTE, "C") is None
      and not any(f == "list.remark" for f, _n, _p in _Cur("gm", [gmrow])._wide_names11(kg, "window-regulator")))
door = lr("ford", "F67Z-7823208-AA", "Regulator Assy", "door-front", url="https://x/door",
          group="REGULATOR ASY. (FRONT DOOR WINDOW) ELECTRIC - LESS MOTOR AND DRIVE - AND 23209", line=940)
kf = _K("ford", "F67Z-7823208-AA", "Regulator Assy")
r = words("ford", "window-regulator", "F67Z-7823208-AA", ["Regulator Assy"], kf, [door])
check("11c: a row on a page read for another category counts (F67Z-7823208-AA's door page): 'regulator without motor'",
      r and r.get("phrase") == "regulator without motor", r)
part2 = lr("ford", "F67Z-7823208-AA", "Regulator Assy", "door-front", url="https://x/door2", line=3122,
           group="ELECTRIC - LESS MOTOR AND DRIVE")
r = _Cur("ford", [lr("ford", "F67Z-7823208-AA", "Regulator Assy", "window-regulator")], [part2])._r11_words(
    kf, "window-regulator", NOTE, "C")
check("11c: rows of a continuation part (lists.2) are read", r and r.get("phrase") == "regulator without motor", r)

# ------------------------------------------------------------ 11c: 'regulator without motor' needs a basis
kt = _K("toyota", "69801-06070", "Regulator Sub-Assy, Front Door Window, Rh")
motor_row = lr("toyota", "85710-06070", "Motor Assy, Power Window Regulator", "window-regulator")
check("11c: 'regulator without motor' with every own page listing the motor separately is kept",
      words("toyota", "window-regulator", "69801-06070", ["Regulator Sub-Assy, Front Door Window, Rh"], kt,
            [motor_row], note=NOTE_LESS) is None)
r = words("toyota", "window-regulator", "69801-06070", ["Regulator Sub-Assy, Front Door Window, Rh"], kt, note=NOTE_LESS)
check("11c: with no value saying so and a page without the motor, the phrase is removed (the note says less)",
      r and r.get("remove") == "regulator without motor", r)
r = _Cur("toyota", [])._r11_words(kt, "window-regulator", NOTE_LESS, "C")
check("11c: with no own page at all, the phrase is removed", r and r.get("remove") == "regulator without motor", r)
kw = _K("gm", "15074553", "REGULATOR, FRONT SIDE DOOR WINDOW(W/O MOTOR)")
check("11c: a value saying '(W/O MOTOR)' is the basis: kept",
      words("gm", "window-regulator", "15074553", ["REGULATOR"], kw, note=NOTE_LESS) is None)

# ------------------------------------------------------------ bumpers
reinf = lr("toyota", "52021-06900", "Reinforcement, Front Bumper", "bumper-front", line=7)
k = _K("toyota", "52119-06919", "Cover, Front Bumper", "Cover, Front Bumper")
r = words("toyota", "bumper-front", "52119-06919", ["Cover, Front Bumper"], k, [reinf])
check("bumper: a cover whose own page lists a reinforcement as a separate number -> 'bumper cover only'",
      r and r.get("phrase") == "bumper cover only", r)
r = words("toyota", "bumper-front", "52119-06919", ["Cover, Front Bumper"], k)
check("bumper: no reinforcement on the page -> 'bumper cover'", r and r.get("phrase") == "bumper cover", r)
r = words("toyota", "bumper-front", "52437-53010", ["Cover, Front Bumper Guard, RH"],
          _K("toyota", "52437-53010", "Cover, Front Bumper Guard, RH"))
check("11b: a bumper guard cover is held", r and r.get("hold") and r["hold"][0] == "held_part_other", r)
kcp = _K("ford", "AE5Z-17757-ACP", "Bumper Assy - Front", "Bumper Assembly - Front")
r = words("ford", "bumper-front", "AE5Z-17757-ACP", ["Bumper Assy - Front"], kcp,
          [lr("ford", "AE5Z-17757-ACP", "Bumper Assy - Front", "bumper-front", notes=["Impact Bar - Steel"], line=5)])
check("11c: the -CP sibling whose list note says 'Impact Bar - Steel' is held", r and r.get("hold")
      and r["hold"][0] == "held_part_other", r)
cover_row = lr("ford", "7L1Z-17D957-A", "Bumper Cover", "bumper-front", line=8)
kb = _K("ford", "7L1Z-17757-A", "Bumper", "Front Bumper Assembly")
r = words("ford", "bumper-front", "7L1Z-17757-A", ["Bumper"], kb, [cover_row])
check("11c: a number named only 'Bumper' whose own page lists a separate bumper cover is held",
      r and r.get("hold") and r["hold"][0] == "held_bumper_bar", r)
check("11c: the same with a value saying chrome is the bar itself: left",
      words("ford", "bumper-front", "7L1Z-17757-A", ["Bumper"], _K("ford", "7L1Z-17757-A", "Bumper", "Chrome Bumper"),
            [cover_row]) is None)
check("11c: a bare 'Bumper' with no cover on its pages is left",
      words("ford", "bumper-front", "XL3Z-17757-AA", ["Bumper"], _K("ford", "XL3Z-17757-AA", "Bumper")) is None)

# ------------------------------------------------------------ tail lamps (hub ruling 11c)
r = words("toyota", "tail-lights", "81551-0E010", ["Lens & Body, Rear Combination Lamp, RH"],
          _K("toyota", "81551-0E010", "Lens & Body, Rear Combination Lamp, RH", other_names="Tail Lamps; Brake Light"))
check("tail lamp: 'Lens & Body' alone (generic aliases aside) -> 'lens and body unit'",
      r and r.get("phrase") == "lens and body unit", r)
check("11c tail lamp: lens and body beside 'Tail Light Assembly' is one unit: no words, not held",
      words("toyota", "tail-lights", "81551-33530", ["Lens&Body, Rear Combination Lamp"],
            _K("toyota", "81551-33530", "Lens & Housing", other_names="Tail Light Assembly, Rear Right")) is None)
r = words("toyota", "tail-lights", "81551-0E010", ["Lens & Body, Rear Combination Lamp, RH"],
          _K("toyota", "81551-0E010", "Lens & Body, Rear Combination Lamp, RH", other_names="Lens, Rear Combination Lamp"))
check("11c tail lamp: a lens alone beside the unit is a different kind: held", r and r.get("hold"), r)

# ------------------------------------------------------------ window regulators
NOTE_S = "Subaru catalog lists #X for both — fits some configurations; verify the number on the part"
r = words("subaru", "window-regulator", "61041AL00A", ["Regulator & Motor Assembly-Front Right"],
          _K("subaru", "61041AL00A", "Regulator & Motor Assembly-Front Right", "Regulator & Motor Assembly-Front Right"),
          note=NOTE_S)
check("regulator: every name 'Regulator & Motor Assembly' -> 'regulator with motor'", r and r.get("phrase") == "regulator with motor", r)
r = words("gm", "window-regulator", "10334396", ["REGULATOR"],
          _K("gm", "10334396", "REGULATOR, FRONT SIDE DOOR WINDOW(INCLUDES MOTOR)", "Regulator; Regulator, Front Door Window Regulator"))
check("regulator: GM's record name '(INCLUDES MOTOR)' beside a bare 'REGULATOR' -> 'regulator with motor'",
      r and r.get("phrase") == "regulator with motor", r)
check("regulator: a regulator name with one alias naming the motor (mopar 68079286AA) is left",
      words("mopar", "window-regulator", "68079286AA", ["Regulator - Front Door Window"],
            _K("mopar", "68079286AA", "Regulator - Front Door Window", "Window Regulator, Front Right",
               "Power Window Motor and Regulator Assembly, Front Right")) is None)
r = words("gm", "window-regulator", "20914715", ["REGULATOR"],
          _K("gm", "20914715", "REGULATOR, FRONT SIDE DOOR WINDOW(INCLUDES 8)(W/O MOTOR)", "Regulator; Window Motor"))
check("regulator: a motor value beside a regulator disagrees: held", r and r.get("hold"), r)
check("round 11 lives in curate.py, every live namespace, nothing in policy.py or positions.py",
      C.ROUND11_NS == frozenset({"gm", "mopar", "toyota", "ford", "hmg", "subaru", "vag", "mb", "nissan"})
      and "ROUND11" not in (OEM / "policy.py").read_text() and "ROUND11" not in (OEM / "positions.py").read_text())

# ------------------------------------------------------------ committed files
REP = OEM / "groups" / "_report"
cen = json.loads((REP / "round11_names_2026-11-20.json").read_text())
docs = {p.stem: json.loads(p.read_text()) for p in (OEM / "groups").glob("*.json")}
by = {(ns, g["cat"], tuple(g["pn"])): g for ns, d in docs.items() for g in d["likely"]}
want = {("toyota", "bumper-front"): (24, 2, 0), ("toyota", "bumper-rear"): (15, 0, 0), ("toyota", "tail-lights"): (14, 0, 0),
        ("toyota", "window-regulator"): (0, 0, 12), ("mopar", "bumper-front"): (1, 0, 0), ("vag", "bumper-front"): (1, 0, 0),
        ("subaru", "window-regulator"): (5, 0, 0), ("ford", "window-regulator"): (1, 2, 0),
        ("ford", "bumper-front"): (0, 6, 0), ("ford", "bumper-rear"): (0, 6, 0), ("gm", "window-regulator"): (10, 5, 0)}
got = {(ns, cat): (v["changed"], v["held"], v["removed"]) for ns, c in cen["summary"].items() for cat, v in c.items()}
check("census: changed / held / phrase removed per make and category", got == want, got)
ok = [r for r in cen["changed"] if by[(r["ns"], r["cat"], tuple(r["pn"]))]["note"] == r["new_note"]
      and r["new_note"] == r["old_note"].replace(" for both — ", f" for both — {r['phrase']}; ", 1)
      and len(r["new_note"]) <= policy.NOTE_MAX_LEN
      and all(re.match(r"^www\.\w+\.com:(lists|records):L\d+$", n["ref"]) and n["field"] for n in r["names"])]
check("every changed group ships the census note: the old note plus '<phrase>; ', within 160, every value with its "
      "field and raw line", len(ok) == len(cen["changed"]) == 71, len(ok))
okr = [r for r in cen["phrases_removed"] if by[(r["ns"], r["cat"], tuple(r["pn"]))]["note"] == r["new_note"]
       == r["old_note"].replace(" for both — regulator without motor; ", " for both — ", 1)]
check("11c: the 12 toyota notes lose 'regulator without motor' and nothing else",
      len(okr) == len(cen["phrases_removed"]) == 12, len(okr))
check("11c: 'regulator without motor' left on 12 gm (a value says W/O MOTOR), 10 toyota (motor on every own page), "
      "1 ford (F67Z-7823208-AA)",
      {ns: v["now"] for ns, v in cen["regulator_without_motor_basis"]["by_ns"].items() if v["now"]}
      == {"gm": 12, "toyota": 10, "ford": 1})
HELD = ["20914715", "20945138", "20945139", "25719488", "25719489", "52437-53010", "52438-53010", "2L1Z-17757-BA",
        "AE5Z-17757-A", "6E5Z-17906-AA", "AE5Z-17906-A", "BT4Z-17906-A", "DG9Z-17906-A", "5G1Z-5423208-AA",
        "5G1Z-5423209-AA", "AE5Z-17757-ACP", "AE5Z-17906-ACP", "2L1Z-17757-BACP", "7L1Z-17757-A", "8A8Z-17757-A",
        "BT4Z-17906-ACP"]
check("held: the 21 groups, none shipped, each with its values and lot rows",
      sorted(h["pn"][0] for h in cen["held"]) == sorted(HELD)
      and not any((h["ns"], h["cat"], tuple(h["pn"])) in by for h in cen["held"])
      and all(h["names"] and h["lot_rows"] for h in cen["held"]))
check("11c: the two Camry lamps are back with origin/main's notes (no words)",
      sorted(r["pn"][0] for r in cen["restored"]) == ["81551-33530", "81561-33530"]
      and all(by[("toyota", "tail-lights", tuple(r["pn"]))]["note"] == r["note"] and "lens and body" not in r["note"]
              for r in cen["restored"]))
check("11c: what is left under ford bumpers is XL3Z-17757-AA and XL3Z-17757-AACP",
      sorted(g["pn"][0] for g in cen["ford_bumpers_left"]) == ["XL3Z-17757-AA", "XL3Z-17757-AACP"])
pair = {g["pn"][0]: g for g in cen["mopar_68079286AA_68079287AA"]["groups"]}
check("mopar 68079286AA / 68079287AA are left with their notes",
      all(by[("mopar", "window-regulator", (p_,))]["note"] == pair[p_]["note"] for p_ in ("68079286AA", "68079287AA")))
shas = {d["policy_sha256"] for d in docs.values()}
check("policy_sha256 is one value across the groups files and is the tree's", shas == {C.policy_sha256()}, shas)
ld = (REP / "live_diff_2026-11-20_round11.txt").read_text()
summ = dict(re.findall(r"^# (\w+) LIVE: (.*)$", ld, re.M))
check("live diff vs origin/main: hmg, mb, nissan unchanged",
      all(summ[ns].startswith("removed 0 groups, added 0 groups, changed 0;") for ns in ("hmg", "mb", "nissan")))
check("live diff: 0 added groups, 0 gained, 0 widened, 0 added claims; removals are the holds (gm 5, toyota 2, ford 14)",
      all(re.search(r"added 0 groups, .*gained 0; .*widened 0; added claims 0$", s) for s in summ.values())
      and summ["gm"].startswith("removed 5 groups") and summ["toyota"].startswith("removed 2 groups")
      and summ["ford"].startswith("removed 14 groups"), summ)
lazy = {}
for p in (OEM.parents[1] / "docs" / "data" / "oem").glob("*.json"):
    for g in json.loads(p.read_text()).get("oemGroups") or []:
        lazy[g["id"]] = g["note"]
check("payload: the lazy files carry the 71 new notes, the 12 shorter notes, the 2 restored lamps, none of the 21 held",
      all(lazy.get(r["group"]) == r["new_note"] for r in cen["changed"] + cen["phrases_removed"])
      and all(lazy.get(r["group"]) == r["note"] for r in cen["restored"])
      and not any(h["group"] in lazy for h in cen["held"]))
done("test_round11_1120")
