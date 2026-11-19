#!/usr/bin/env python3
"""Round 10 (interchange 2026-11-19, branch interchange/round10-1119): after
round 9's A5 measure, mopar and subaru window-regulator numbers whose catalog
part name is a motor say 'window motor only' (curate.ROUND10_NS). Live claims
only say less: the finished note gains the phrase and nothing else changes; a
note the words take past the cap, names mixing a motor and a regulator, or no
name in the raw, hold the group. positions.py (policy_sha256) is unchanged, so
the other seven groups files stay byte-identical.

Round 10b (after the independent check found mopar 68079283AB named a motor
while its record's description says "Window Regulator, Front Driver Side"):
the kind is read from every naming field the raw prints (list rows main, aux;
records name, aux, description, other_names); names that disagree in kind
hold the group and carry no phrase, on mopar, subaru and nissan."""
import json
import re
from types import SimpleNamespace

from _util import OEM, check, done
import adapters as A
import curate as C
import policy
import positions

JPD = "www.jeeppartsdeal.com"
SPD = "www.subarupartsdeal.com"


def lr(pn, main, site=JPD, line=1):
    return A.ListRow(site=site, seed=("Jeep", "Liberty", 2008), cat="window-regulator", list_url="https://x/y",
                     pn=pn, section="diagram", main=main, aux="", notes=[], locations=["Front"], replace=None,
                     matched=True, excluded_by=None, product=None, retrieved="", line=line, status=200)


class _K:
    def __init__(self, ns, pn, names=(), site=JPD, description="", other_names=""):
        self.key, self.pns = policy.pn_key(ns, pn), {pn}
        self.records = [SimpleNamespace(site=site, oem_names=[n], name=n, aux="", description=description,
                                        other_names=other_names, pointer=f"{site}:records:L{i + 1}")
                        for i, n in enumerate(names)]


class _Cur:
    for _m in ("_r10_class", "_class_names", "_wide_names", "_name_disagree"):
        locals()[_m] = getattr(C.Curation, _m)

    def __init__(self, ns, rows):
        self.ns, self.rows = ns, list(rows)

    def _pn_list_rows(self, key, cat):
        return [x for x in self.rows if policy.pn_key(self.ns, x.pn) == key and x.cat == cat]


def cls(ns, mains, records=(), site=JPD):
    pn = "68004590AC"
    return _Cur(ns, [lr(pn, m, site, i + 1) for i, m in enumerate(mains)])._r10_class(_K(ns, pn, records, site),
                                                                                       "window-regulator")


# ------------------------------------------------------------ the reading
for names, want in ((["Motor - Window Regulator"], "motor"), (["MOTOR Window Regulator"], "motor"),
                    (["MOTOR WINDOW REGULATOR 6 Pin Front"], "motor"), (["Window Motor"], "motor"),
                    (["Regulator - Front Door Window"], "regulator"), (["REGULATOR Rear Door Window"], "regulator"),
                    (["Power Regulator"], "regulator"), (["Regulator & Motor Assembly-Front Right"], "regulator")):
    check(f"reading: {names[0]!r} -> {want}", cls("mopar", names)["class"] == want, cls("mopar", names))
check("reading: subaru 'Motor Assembly-Regulator' -> motor",
      cls("subaru", ["Motor Assembly-Regulator"], site=SPD)["class"] == "motor")
check("reading: every name the raw prints counts (a product record naming a regulator beside a motor list row: mixed, "
      "held)", cls("mopar", ["Motor - Window Regulator"], records=["Regulator - Front Door Window"])["class"] == "mixed"
      and cls("mopar", ["Motor - Window Regulator"], records=["Regulator - Front Door Window"])["hold"])
check("reading: a name that is neither (Glass) holds; no name holds",
      cls("mopar", ["Glass - Door"])["hold"] and cls("mopar", [])["hold"])
check("reading: each name keeps its place in the raw",
      cls("mopar", ["Window Motor"])["names"] == [{"name": "Window Motor", "ref": f"{JPD}:lists:L1"}])
_t = "trim-limited; " + "x" * (policy.NOTE_MAX_LEN - len("Mopar catalog lists #68004590AC for both — trim-limited; "
                                                         "; verify the number on the part") - 1)
check("cap: a reason that fits alone but not with 'window motor only' is caught by the hold test (never cut)",
      C._likely_note_fits("Mopar", "68004590AC", _t) and not C._likely_note_fits("Mopar", "68004590AC", _t,
                                                                                    C.PACK_TEXT["motor"]))
check("cause: positions.packaging reads these motor names as 'reg?' (unchanged: it feeds policy_sha256)",
      all(positions.packaging("window-regulator", ns, "x", [n]) == "reg?"
          for ns, n in (("mopar", "Motor - Window Regulator"), ("subaru", "Motor Assembly-Regulator"))))
# ------------------------------------------------------------ round 10b: every naming field
for name, want in (("Window Regulator, Front Driver Side", "regulator"), ("Power Window Motor, Front Left", "motor"),
                   ("Motor; Motor Window Regulator", "motor"), ("Window Motor, Rear Passenger Side", "motor"),
                   ("Power Window Motor and Regulator Assembly, Front Right", "regulator+motor"),
                   ("Regulator & Motor Assembly-Front Right", "regulator+motor"),
                   ("Regulator Driver Side Motor Assembly", "motor"), ("Regulator Assy-Door Window,Rh", "regulator"),
                   ("REGULATOR, Electric", "regulator"), ("Front Left", "")):
    check(f"10b kind: {name!r} -> {want or 'neither'}", C._kind10b(name) == want, C._kind10b(name))
pn = "68079283AB"
cur = _Cur("mopar", [lr(pn, "Motor - Window Regulator", line=521)])
k = _K("mopar", pn, ["Motor - Window Regulator"], description="Window Regulator, Front Driver Side",
       other_names="Motor - Window Regulator; Power Window Motor, Front Left")
dis = cur._name_disagree(k, "window-regulator")
check("10b: a motor-named number whose record description says 'Window Regulator' disagrees in kind (held)",
      dis and dis["kinds"] == ["motor", "regulator"]
      and {"field": "record.description", "name": "Window Regulator, Front Driver Side", "ref": f"{JPD}:records:L1",
           "kind": "regulator"} in dis["names"], dis)
check("10b: its other_names are read one by one (';')",
      {(n["field"], n["name"]) for n in dis["names"]} >= {("record.other_names", "Power Window Motor, Front Left"),
                                                           ("record.other_names", "Motor - Window Regulator")})
k2 = _K("mopar", pn, ["Motor - Window Regulator"], description="Window Motor, Front Driver Side",
        other_names="Power Window Motor, Front Left")
check("10b: the same number with a motor description agrees (not held)", cur._name_disagree(k2, "window-regulator") is None)
k3 = _K("subaru", "61041AL00A", ["Regulator & Motor Assembly-Front Right"], site=SPD,
        description="Regulator & Motor Assembly-Front Right")
check("10b: 'Regulator & Motor Assembly' alone is one kind (regulator with motor): not held, no phrase",
      _Cur("subaru", [])._name_disagree(k3, "window-regulator") is None)
check("10b: the rule covers mopar, subaru and nissan", C.ROUND10B_NS == frozenset({"mopar", "subaru", "nissan"}))
check("round 10 is mopar and subaru only, kept out of policy.py and positions.py",
      C.ROUND10_NS == frozenset({"mopar", "subaru"})
      and "ROUND10" not in (OEM / "policy.py").read_text() and "ROUND10" not in (OEM / "positions.py").read_text())

# ------------------------------------------------------------ committed files
REP = OEM / "groups" / "_report"
cen = json.loads((REP / "round10_names_2026-11-19.json").read_text())
docs = {ns: json.loads((OEM / "groups" / f"{ns}.json").read_text()) for ns in ("mopar", "subaru")}
by = {(ns, tuple(g["pn"])): g for ns, d in docs.items() for g in d["likely"]}
HELD = {"68079283AB", "68037296AA", "68037297AA"}
check("census (10b): 20 mopar and 8 subaru groups changed; mopar 68079283AB, 68037296AA, 68037297AA held "
      "(names disagree in kind); nissan none",
      cen["summary"]["mopar"]["changed"] == 20 and cen["summary"]["subaru"]["changed"] == 8
      and {h["pn"][0] for h in cen["held"]} == HELD and all(h["reason"] == "held_name_disagree" for h in cen["held"])
      and cen["summary"]["nissan"]["held"] == 0 and cen["summary"]["nissan"]["changed"] == 0)
check("10b: the held groups are not shipped and carry no phrase anywhere",
      not any(("mopar", (p_,)) in by for p_ in HELD))
check("10b: every held row lists its names with field, kind and raw line, and its lot rows",
      all(h["names"] and all(re.match(r"^www\.\w+\.com:(lists|records):L\d+$", n["ref"]) and "field" in n
                             for n in h["names"]) and h["lot_rows"] for h in cen["held"]))
ok_rows = [r for r in cen["changed"]
           if by[(r["ns"], tuple(r["pn"]))]["note"] == r["new_note"]
           and r["new_note"] == r["old_note"].replace(" for both — ", " for both — window motor only; ", 1)
           and len(r["new_note"]) <= policy.NOTE_MAX_LEN and r["names"]
           and all(re.match(r"^www\.\w+\.com:(lists|records):L\d+$", n["ref"]) for n in r["names"])]
check("every changed group ships the census new note: the old note plus 'window motor only; ', within 160, names "
      "with their raw lines", len(ok_rows) == len(cen["changed"]) == 28, len(ok_rows))
check("no other mopar / subaru group says 'window motor only' (mopar 20, subaru 8)",
      sum("window motor only" in g["note"] for g in by.values()) == 28)
shas = {json.loads(p.read_text())["policy_sha256"] for p in (OEM / "groups").glob("*.json")}
check("policy_sha256 is one value across the nine groups files and is the tree's",
      shas == {C.policy_sha256()}, shas)
ld = (REP / "live_diff_2026-11-19_round10.txt").read_text()
summ = dict(re.findall(r"^# (\w+) LIVE: (.*)$", ld, re.M))
same = [ns for ns, s in summ.items() if s.startswith("removed 0 groups, added 0 groups, changed 0;")]
check("live diff: gm, toyota, ford, hmg, vag, mb, nissan unchanged",
      sorted(same) == ["ford", "gm", "hmg", "mb", "nissan", "toyota", "vag"], sorted(same))
check("live diff: mopar 3 removed / 20 changed, subaru 8 changed (notes); 0 added, 0 gained, 0 widened, 0 added claims",
      all(re.match(r"removed %d groups, added 0 groups, changed %d; app-years lost 0, gained 0; gates narrowed 0, "
                   r"widened 0; added claims 0" % (r_, n), summ.get(ns, ""))
          for ns, r_, n in (("mopar", 3, 20), ("subaru", 0, 8))),
      {k: summ.get(k) for k in ("mopar", "subaru")})
lazy = json.loads((OEM.parents[1] / "docs" / "data" / "oem" / "window-regulator.json").read_text())
ship = {g["id"]: g["note"] for g in lazy["oemGroups"]}
check("payload: the window-regulator lazy file carries the 28 new notes and none of the 3 held groups",
      all(ship.get(r["group"]) == r["new_note"] for r in cen["changed"])
      and not any(h["group"] in ship for h in cen["held"]))
done("test_round10_1119")
