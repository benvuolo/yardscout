#!/usr/bin/env python3
"""Round 11 (interchange 2026-11-20, branch interchange/round11-1120): the
wording gaps round 10's item-4 measure found, on the live makes. Only
packaging words, read from every naming field the raw prints (round 10b):
bumper covers ("bumper cover", "bumper cover only" when each own page lists a
reinforcement separately, "bumper guard cover"), Toyota "Lens & Body" tail
lamps ("lens and body unit"), regulators named with their motor ("regulator
with motor"). Values that disagree in kind hold the group, as does a note
past 160 or a note already carrying other packaging words; nothing else
changes (curate.ROUND11_NS, _kind11, Curation._r11_words)."""
import json
import re
from types import SimpleNamespace

from _util import OEM, check, done
import adapters as A
import curate as C
import policy

TPN = "www.toyotapartsnow.com"


def lr(ns, pn, main, cat, url="https://x/page", aux="", line=1, site=TPN):
    return A.ListRow(site=site, seed=("Toyota", "Camry", 2010), cat=cat, list_url=url, pn=pn, section="diagram",
                     main=main, aux=aux, notes=[], locations=[], replace=None, matched=True, excluded_by=None,
                     product=None, retrieved="", line=line, status=200)


class _K:
    def __init__(self, ns, pn, name="", description="", other_names="", site=TPN):
        self.key, self.pns = policy.pn_key(ns, pn), {pn}
        self.records = [SimpleNamespace(site=site, name=name, aux="", description=description, other_names=other_names,
                                        oem_names=[name], pointer=f"{site}:records:L9")] if name else []


class _Cur:
    for _m in ("_r11_words", "_wide_names"):
        locals()[_m] = getattr(C.Curation, _m)

    def __init__(self, ns, rows):
        self.ns, self.list_rows = ns, list(rows)

    def _pn_list_rows(self, key, cat):
        return [x for x in self.list_rows if policy.pn_key(self.ns, x.pn) == key and x.cat == cat]


NOTE = "Toyota catalog lists #X for both — fits some configurations; verify the number on the part"


def words(ns, cat, pn, mains, k, others=(), note=NOTE):
    rows = [lr(ns, pn, m, cat, line=i + 1) for i, m in enumerate(mains)] + list(others)
    return _Cur(ns, rows)._r11_words(k, cat, note, "C")


# ------------------------------------------------------------ the kinds
for cat, name, want in (("bumper-front", "Cover, Front Bumper", "cover"), ("bumper-front", "Bumper Cover, Front", "cover"),
                        ("bumper-front", "Fascia - Front", "cover"), ("bumper-front", "Cover, Front Bumper Guard, RH", "guard"),
                        ("bumper-front", "Bumper Assy - Front", "bumper"), ("bumper-rear", "Reinforcement, Rear Bumper", "reinforcement"),
                        ("bumper-rear", "Impact Bar", "reinforcement"), ("tail-lights", "Lens & Body, Rear Combination Lamp, RH", "lens-body"),
                        ("tail-lights", "Lens & Housing", "lens-body"), ("tail-lights", "Tail Light Assembly, Rear Right", "assembly"),
                        ("tail-lights", "Socket & Wire Sub-Assy, Rear Combination Lamp", "socket"), ("tail-lights", "Tail Lamps", ""),
                        ("window-regulator", "REGULATOR, FRONT SIDE DOOR WINDOW(INCLUDES 13)(INCLUDES MOTOR)", "regulator+motor"),
                        ("window-regulator", "Regulator & Motor Assembly-Front Right", "regulator+motor"),
                        ("window-regulator", "Window Motor", "motor")):
    check(f"kind: {cat} {name!r} -> {want or 'neither'}", C._kind11(cat, name) == want, C._kind11(cat, name))

# ------------------------------------------------------------ the words
reinf = lr("toyota", "52021-06900", "Reinforcement, Front Bumper", "bumper-front", line=7)
k = _K("toyota", "52119-06919", "Cover, Front Bumper", "Cover, Front Bumper")
r = words("toyota", "bumper-front", "52119-06919", ["Cover, Front Bumper"], k, [reinf])
check("bumper: a cover whose own page lists a reinforcement as a separate number -> 'bumper cover only'",
      r and r.get("phrase") == "bumper cover only" and not r.get("hold"), r)
r = words("toyota", "bumper-front", "52119-06919", ["Cover, Front Bumper"], k)
check("bumper: no reinforcement on the page -> 'bumper cover' (nothing about the reinforcement)",
      r and r.get("phrase") == "bumper cover", r)
k2 = _K("toyota", "52119-06919", "Cover, Front Bumper", other_names="Bumper Assembly, Front")
r = words("toyota", "bumper-front", "52119-06919", ["Cover, Front Bumper"], k2)
check("bumper: a cover beside a bumper assembly name disagrees in kind: held, no phrase",
      r and r.get("hold") and r["hold"][0] == "held_name_disagree" and not r.get("phrase"), r)
r = words("toyota", "bumper-front", "52437-53010", ["Cover, Front Bumper Guard, RH"],
          _K("toyota", "52437-53010", "Cover, Front Bumper Guard, RH"))
check("bumper: a bumper guard cover says 'bumper guard cover'", r and r.get("phrase") == "bumper guard cover", r)
check("bumper: a bumper assembly gets nothing", words("ford", "bumper-front", "X1", ["Bumper Assy - Front"],
                                                      _K("ford", "X1", "Bumper Assy - Front")) is None)
r = words("toyota", "tail-lights", "81551-0E010", ["Lens & Body, Rear Combination Lamp, RH"],
          _K("toyota", "81551-0E010", "Lens & Body, Rear Combination Lamp, RH", other_names="Tail Lamps; Brake Light"))
check("tail lamp: 'Lens & Body' (generic aliases aside) -> 'lens and body unit'", r and r.get("phrase") == "lens and body unit", r)
r = words("toyota", "tail-lights", "81551-33530", ["Lens&Body, Rear Combination Lamp"],
          _K("toyota", "81551-33530", "Lens & Housing", other_names="Tail Light Assembly, Rear Right"))
check("tail lamp: lens and body beside 'Tail Light Assembly' disagrees: held", r and r.get("hold"), r)
check("tail lamp: a lamp assembly gets nothing", words("toyota", "tail-lights", "81550-06350", ["Lamp Assembly, Rear Combination"],
                                                     _K("toyota", "81550-06350", "Tail Lamp Assembly")) is None)
NOTE_S = "Subaru catalog lists #X for both — fits some configurations; verify the number on the part"
r = words("subaru", "window-regulator", "61041AL00A", ["Regulator & Motor Assembly-Front Right"],
          _K("subaru", "61041AL00A", "Regulator & Motor Assembly-Front Right", "Regulator & Motor Assembly-Front Right"),
          note=NOTE_S)
check("regulator: every name 'Regulator & Motor Assembly' -> 'regulator with motor'", r and r.get("phrase") == "regulator with motor", r)
r = words("gm", "window-regulator", "10334396", ["REGULATOR"],
          _K("gm", "10334396", "REGULATOR, FRONT SIDE DOOR WINDOW(INCLUDES MOTOR)", "Regulator; Regulator, Front Door Window Regulator"))
check("regulator: GM's record name '(INCLUDES MOTOR)' beside its list row's bare 'REGULATOR' -> 'regulator with motor'",
      r and r.get("phrase") == "regulator with motor", r)
r = words("mopar", "window-regulator", "68079286AA", ["Regulator - Front Door Window"],
          _K("mopar", "68079286AA", "Regulator - Front Door Window", "Window Regulator, Front Right",
             "Power Window Motor and Regulator Assembly, Front Right"))
check("regulator: a regulator name with one alias naming the motor (mopar 68079286AA) is left: no phrase, no hold", r is None, r)
r = words("gm", "window-regulator", "20914715", ["REGULATOR"],
          _K("gm", "20914715", "REGULATOR, FRONT SIDE DOOR WINDOW(INCLUDES 8)(W/O MOTOR)", "Regulator; Window Motor"))
check("regulator: a motor value beside a regulator disagrees: held", r and r.get("hold"), r)
r = words("gm", "window-regulator", "Y1", ["REGULATOR"], _K("gm", "Y1", "REGULATOR (INCLUDES MOTOR)", "Regulator (W/O MOTOR)"))
check("regulator: 'includes motor' beside 'w/o motor' disagrees: held", r and r.get("hold"), r)
check("regulator: a note already saying 'regulator with motor' is left as it is",
      words("gm", "window-regulator", "10305685", ["REGULATOR"],
            _K("gm", "10305685", "REGULATOR, FRONT SIDE DOOR WINDOW(W/MOTOR)"),
            note="GM catalog lists #X for both — regulator with motor; fits some configurations; verify the number on the part") is None)
check("round 11 lives in curate.py: every live namespace, nothing in policy.py or positions.py",
      C.ROUND11_NS == frozenset({"gm", "mopar", "toyota", "ford", "hmg", "subaru", "vag", "mb", "nissan"})
      and "ROUND11" not in (OEM / "policy.py").read_text() and "ROUND11" not in (OEM / "positions.py").read_text())

# ------------------------------------------------------------ committed files
REP = OEM / "groups" / "_report"
cen = json.loads((REP / "round11_names_2026-11-20.json").read_text())
docs = {p.stem: json.loads(p.read_text()) for p in (OEM / "groups").glob("*.json")}
by = {(ns, g["cat"], tuple(g["pn"])): g for ns, d in docs.items() for g in d["likely"]}
want = {("toyota", "bumper-front"): (26, 0), ("toyota", "bumper-rear"): (15, 0), ("toyota", "tail-lights"): (14, 2),
        ("mopar", "bumper-front"): (1, 0), ("vag", "bumper-front"): (1, 0), ("subaru", "window-regulator"): (5, 0),
        ("ford", "window-regulator"): (2, 0), ("gm", "window-regulator"): (10, 5)}
got = {(ns, cat): (v["changed"], v["held"]) for ns, c in cen["summary"].items() for cat, v in c.items()}
check("census: changed / held per make and category", got == want, got)
ok = [r for r in cen["changed"] if by[(r["ns"], r["cat"], tuple(r["pn"]))]["note"] == r["new_note"]
      and r["new_note"] == r["old_note"].replace(" for both — ", f" for both — {r['phrase']}; ", 1)
      and len(r["new_note"]) <= policy.NOTE_MAX_LEN
      and all(re.match(r"^www\.\w+\.com:(lists|records):L\d+$", n["ref"]) and n["field"] for n in r["names"])]
check("every changed group ships the census note: the old note plus '<phrase>; ', within 160, every naming value with "
      "its field and raw line", len(ok) == len(cen["changed"]) == 74, len(ok))
check("the held groups are not shipped; each lists its values and lot rows",
      not any((h["ns"], h["cat"], tuple(h["pn"])) in by for h in cen["held"])
      and all(h["names"] and h["lot_rows"] for h in cen["held"]) and len(cen["held"]) == 7)
check("held: gm 20914715, 20945138, 20945139, 25719488, 25719489; toyota 81551-33530, 81561-33530",
      sorted(h["pn"][0] for h in cen["held"]) == sorted(["20914715", "20945138", "20945139", "25719488", "25719489",
                                                         "81551-33530", "81561-33530"]))
pair = {g["pn"][0]: g for g in cen["mopar_68079286AA_68079287AA"]["groups"]}
check("mopar 68079286AA / 68079287AA are left: shipped with their notes unchanged",
      all(by[("mopar", "window-regulator", (p_,))]["note"] == pair[p_]["note"] for p_ in ("68079286AA", "68079287AA")))
check("the eight other Toyota tail-light numbers are lamp assemblies, unchanged",
      len(cen["toyota_tail_lights_other_8"]["groups"]) == 8
      and all(by[("toyota", "tail-lights", tuple(g["pn"]))]["note"] == g["note"]
              for g in cen["toyota_tail_lights_other_8"]["groups"]))
shas = {d["policy_sha256"] for d in docs.values()}
check("policy_sha256 is one value across the groups files and is the tree's", shas == {C.policy_sha256()}, shas)
ld = (REP / "live_diff_2026-11-20_round11.txt").read_text()
summ = dict(re.findall(r"^# (\w+) LIVE: (.*)$", ld, re.M))
check("live diff: hmg, mb, nissan unchanged",
      all(summ[ns].startswith("removed 0 groups, added 0 groups, changed 0;") for ns in ("hmg", "mb", "nissan")))
check("live diff: 0 added groups, 0 gained app-years, 0 widened gates, 0 added claims on every make; removals are the holds",
      all(re.search(r"added 0 groups, .*gained 0; .*widened 0; added claims 0$", s) for s in summ.values())
      and summ["gm"].startswith("removed 5 groups") and summ["toyota"].startswith("removed 2 groups"), summ)
lazy = {}
for p in (OEM.parents[1] / "docs" / "data" / "oem").glob("*.json"):
    for g in json.loads(p.read_text()).get("oemGroups") or []:
        lazy[g["id"]] = g["note"]
check("payload: the lazy files carry the 74 new notes and none of the 7 held groups",
      all(lazy.get(r["group"]) == r["new_note"] for r in cen["changed"]) and not any(h["group"] in lazy for h in cen["held"]))
done("test_round11_1120")
