#!/usr/bin/env python3
"""Tests for manual-transmission evidence (scraper/trans_evidence.py and the
compiled scraper/manual_detect/trans_rules.json).

Covers:
  1. Each rule type: VIN code (Honda char 7, a generic code table, a per-year
     table, year-limited codes, check digit, US-market only, Honda's
     filed-code condition), manual-only trim (vPIC trim, feed model, VIN
     pattern, year guard), EPA sole offering (identity, engine, drive, year).
  2. Precedence: vPIC > listing > VIN code > trim > EPA.
  3. Conflicts: any disagreement records nothing; automatic and
     conflict_only claims never publish; output_json skips rule claims when
     the VIN's make contradicts the yard's.
  4. The compiled table is current (source hashes match the worklists).
  5. Real data (docs/data, cached decodes only, no network):
     - ground-truth precision of every rule claim against cars whose
       transmission the vPIC decode or the yard listing states; FAILS below
       99.5% (manual claims and all claims separately);
     - the verified worklists' newly confirmed cars still on the lots get
       their manual claim.

Run:  python3 scraper/test_manual_detect.py
"""
import gzip
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import junkyard_scraper as js  # noqa: E402
import trans_evidence as te  # noqa: E402

MD = HERE / "manual_detect"
DATA = HERE.parent / "docs" / "data"
MIN_PRECISION = 0.995
failures = []


def check(name, cond, detail=""):
    print(("  ok  " if cond else "  FAIL") + f" {name}" + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def with_check(v: str) -> str:
    """Put a valid check digit in position 9 of a 17-char VIN."""
    v = v.upper()
    s = sum(te._TRANSLIT[c] * w for c, w in zip(v[:8] + "0" + v[9:], te._WEIGHTS)) % 11
    return v[:8] + ("X" if s == 10 else str(s)) + v[9:]


def bad_check(v: str) -> str:
    v = with_check(v)
    return v[:8] + ("1" if v[8] != "1" else "2") + v[9:]


R = te.load_rules()


def claims(vin, year, make="", model="", dec=None, state="CA"):
    return R.infer(vin=vin, listing_year=year, make=make, model=model, dec=dec, state=state)


def rules_of(cs, claim=None):
    return {c["rule"] for c in cs if claim is None or c["claim"] == claim}


def dec(make, model, year, **kw):
    d = {"make": make, "model": model, "modelYear": str(year), "trim": "", "series": "",
         "engine": "", "driveType": "", "transmission": ""}
    d.update(kw)
    return d


# ---- 1a. VIN code rules ------------------------------------------------------
print("VIN code rules")
v = "JH4DB755XVS001675"            # 1997 Integra sedan, char 7 = 5 (manual), on a worklist
cs = claims(v, 1997, "Acura", "Integra")
check("Honda char 7 odd -> manual (filed code, no decode needed)",
      "acura_vin7_digit_1986_2009_manual" in rules_of(cs, "manual"), cs)
v6 = with_check("JH4DB7650VS001675")   # same line, char 7 = 6 (automatic)
cs = claims(v6, 1997, "Acura", "Integra", dec("ACURA", "Integra", 1997))
check("Honda char 7 even -> automatic claim", rules_of(cs) == {"acura_vin7_digit_1986_2009_automatic"}, cs)
vu = with_check("JH4ZZ7550VS001675")   # code ZZ75 never filed, no decoded model
check("Honda code not filed and not decoded -> no claim", claims(vu, 1997, "Acura", "Integra") == [])
check("Honda code not filed but VIN decodes to a model -> claim",
      "acura_vin7_digit_1986_2009_manual" in rules_of(claims(vu, 1997, "Acura", "Integra",
                                                             dec("ACURA", "Integra", 1997))))
check("bad check digit -> no claim", claims(bad_check(v), 1997, "Acura", "Integra") == [])
check("listing year far from VIN year -> no claim", claims(v, 2003, "Acura", "Integra") == [])
acc96 = with_check("1HGCD5530TA149236")   # 1996 Accord sedan manual: NOT the 1997 carve-out
check("1996 Accord (CD line) keeps the general char-7 rule",
      "honda_vin7_digit_1987_2009_manual" in rules_of(claims(acc96, 1996, "Honda", "Accord",
                                                             dec("HONDA", "Accord", 1996))))
acc97 = with_check("1HGCD5630VA000001")   # 1997 Accord char 7 = 6
cs = claims(acc97, 1997, "Honda", "Accord", dec("HONDA", "Accord", 1997))
check("1997 Accord: only the conflict-only rule speaks",
      {c["rule"] for c in cs} == {"honda_accord_1997_vin7_automatic"} and all(c["conflict_only"] for c in cs), cs)

focus = "1FADP3FE4FL281587"          # 2015 Focus 1.0 EcoBoost, Ford char 8 = E
check("Ford engine-code rule -> manual",
      "ford_focus_10_2015_char8_E" in rules_of(claims(focus, 2015, "Ford", "Focus"), "manual"))
check("Ford engine-code rule is year-limited (2016 Focus 1.0 -> no claim)",
      "ford_focus_10_2015_char8_E" not in rules_of(claims(with_check(focus[:9] + "G" + focus[10:]), 2016)))
metro = "2C1MR2262Y6721697"          # 2000 Metro 1.0 (GM table rule)
check("GM table rule -> manual",
      "chevrolet_metro_10_1999_2000_char8_6" in rules_of(claims(metro, 2000, "Chevrolet", "Metro"), "manual"))
sub_b95 = with_check("JF1GC4350SB000001")   # 1995 Gunma, pos 11 = B (FWD 5MT, 1995-96 only)
sub_b05 = with_check("JF1GD67005B000001")   # 2005 Gunma, pos 11 = B (not defined after 1996)
check("Subaru code B in 1995 -> manual",
      "subaru_fhi_G_H_1995_2025_char11" in rules_of(claims(sub_b95, 1995, "Subaru", "Impreza"), "manual"))
check("Subaru code B in 2005 -> no claim (code years respected, not the union regex)",
      "subaru_fhi_G_H_1995_2025_char11" not in rules_of(claims(sub_b05, 2005, "Subaru", "Impreza")))
sub_h = with_check("JF1GD67005H000001")
check("Subaru code H -> automatic claim",
      rules_of(claims(sub_h, 2005, "Subaru", "Impreza"), "automatic") == {"subaru_fhi_G_H_1995_2025_char11"})
matrix = "2T1KY32EX4C809836"         # 2004 Matrix XRS (US-market rule)
check("US-market rule applies at a US yard",
      "toyota_matrix_xrs_2zzge_2004_2006" in rules_of(claims(matrix, 2004, "Toyota", "Matrix", state="WA")))
check("US-market rule skipped at a Canadian yard",
      "toyota_matrix_xrs_2zzge_2004_2006" not in rules_of(claims(matrix, 2004, "Toyota", "Matrix", state="BC")))
check("unknown WMI -> no claim", claims(with_check("ZZZAA11110A000001"), 2010) == [])

# ---- 1b. trim rules -------------------------------------------------------------
print("trim rules")
civ = dec("HONDA", "Civic", 2000, trim="Si")
check("vPIC trim (Civic Si 2000) -> trim claim",
      "honda_civic_si_1999_2000" in rules_of(claims("", 2000, "Honda", "Civic", civ)))
check("vPIC trim outside the rule years -> no claim",
      "honda_civic_si_1999_2000" not in rules_of(claims("", 1996, "Honda", "Civic",
                                                         dec("HONDA", "Civic", 1996, trim="Si"))))
check("feed model (S2000, no VIN) -> trim claim",
      "honda_s2000_2000_2009" in rules_of(claims("", 2004, "Honda", "S2000")))
spec_v = with_check("3N1CB61E07L722914")
check("VIN pattern (Sentra Spec V) -> trim claim",
      "nissan_sentra_se_r_spec_v_2007_2012" in rules_of(claims(spec_v, 2007, "Nissan", "Sentra")))
sho = dec("FORD", "Taurus", 1992, trim="SHO")
check("listing year far from decoded year -> no trim claim",
      "ford_taurus_sho_30_1989_1995" not in rules_of(claims("", 1997, "Ford", "Taurus", sho)))
check("trim claims are US-market (Canadian yard -> none)",
      "honda_civic_si_1999_2000" not in rules_of(claims("", 2000, "Honda", "Civic", civ, state="ON")))

# ---- 1c. EPA rules --------------------------------------------------------------
print("EPA sole-offering rules")
cal_vin = "1B3HB28C58D769753"        # 2008 Caliber 1.8 (also a VIN-code rule)
cal = dec("DODGE", "Caliber", 2008, engine="1.8L 4-cyl")
cs = claims(cal_vin, 2008, "Dodge", "Caliber", cal)
check("EPA engine rule -> engine claim", any(c["src"] == "engine" and c["rule"] == "epa_dodge_caliber_1.8l_4cyl_anydrive" for c in cs), cs)
check("EPA rule: other displacement -> no claim",
      not any(c["src"] == "engine" for c in claims(cal_vin, 2008, "Dodge", "Caliber",
                                                   dec("DODGE", "Caliber", 2008, engine="2.0L 4-cyl"))))
check("EPA rule: listing year != decoded year -> no claim",
      not any(c["src"] == "engine" for c in claims(cal_vin, 2009, "Dodge", "Caliber", cal)))
check("EPA rule: unseen make/model identity -> no claim",
      not any(c["src"] == "engine" for c in claims(cal_vin, 2008, "Dodge", "Caliber SXT", cal)))
spt_vin = with_check("KNDJE723X97000001")
spt4 = dec("KIA", "Sportage", 2009, engine="2.0L", driveType="4WD/4-Wheel Drive/4x4")
spt2 = dec("KIA", "Sportage", 2009, engine="2.0L", driveType="FWD/Front-Wheel Drive")
check("EPA 4WD rule: decoded 4WD -> claim",
      "epa_kia_sportage_2.0l_xcyl_4wd" in rules_of(claims(spt_vin, 2009, "Kia", "Sportage", spt4)))
check("EPA 4WD rule: decoded FWD -> no claim",
      "epa_kia_sportage_2.0l_xcyl_4wd" not in rules_of(claims(spt_vin, 2009, "Kia", "Sportage", spt2)))
check("EPA rule: bad check digit -> no claim",
      not any(c["src"] == "engine" for c in claims(bad_check(cal_vin), 2008, "Dodge", "Caliber", cal)))

# ---- 2. precedence ----------------------------------------------------------------
print("precedence")
M = lambda src, rule="r", co=False: {"src": src, "claim": "manual", "rule": rule, "conflict_only": co, "label": ""}  # noqa: E731
A = lambda src, rule="r", co=False: {"src": src, "claim": "automatic", "rule": rule, "conflict_only": co, "label": ""}  # noqa: E731
check("vPIC beats everything", te.resolve("6-spd Manual", "Manual", [M("vin_code"), M("trim"), M("engine")])[:2] == ("6-spd Manual", "vin"))
check("listing beats rules", te.resolve("", "5-spd Manual", [M("vin_code")])[:2] == ("5-spd Manual", "listing"))
check("VIN code beats trim", te.resolve("", "", [M("vin_code"), M("trim"), M("engine")])[:2] == ("Manual", "vin_code"))
check("trim beats EPA", te.resolve("", "", [M("trim"), M("engine")])[:2] == ("Manual", "trim"))
check("EPA engine alone", te.resolve("", "", [M("engine")])[:2] == ("Manual", "engine"))
check("EPA model-year alone", te.resolve("", "", [M("model")])[:2] == ("Manual", "model"))
check("speeds-only vPIC text + manual rule -> rule fills the class",
      te.resolve("5-spd", "", [M("vin_code")])[:2] == ("Manual", "vin_code"))
check("no evidence -> nothing", te.resolve("", "", [])[:2] == ("", ""))
check("real claims keep precedence order (VIN code before EPA)",
      [c["src"] for c in claims(cal_vin, 2008, "Dodge", "Caliber", cal)][:1] == ["vin_code"])

# ---- 3. conflicts -------------------------------------------------------------------
print("conflicts")
check("vPIC automatic vs VIN-code manual -> nothing", te.resolve("4-spd Automatic", "", [M("vin_code")])[:2] == ("", ""))
check("listing manual vs vPIC automatic -> nothing", te.resolve("Automatic", "5-spd Manual", [])[:2] == ("", ""))
check("VIN-code automatic vs EPA manual -> nothing", te.resolve("", "", [A("vin_code"), M("engine")])[:2] == ("", ""))
check("trim manual vs listing CVT -> nothing", te.resolve("", "Automatic (CVT)", [M("trim")])[:2] == ("", ""))
check("conflict-only automatic withholds a vPIC manual", te.resolve("5-spd Manual", "", [A("vin_code", co=True)])[:2] == ("", ""))
check("conflict-only manual never publishes", te.resolve("", "", [M("vin_code", co=True)])[:2] == ("", ""))
check("automatic rule claim never publishes text", te.resolve("", "", [A("vin_code")])[:2] == ("", ""))
check("automatic rule agreeing with vPIC keeps vPIC", te.resolve("5-spd Automatic", "", [A("vin_code")])[:2] == ("5-spd Automatic", "vin"))
check("automated manual (AMT) is not manual", te.trans_class("6-spd Automated Manual Transmission (AMT)") == te.NOT_MANUAL)
check("conflict info names the sources", "vin:not_manual" in te.resolve("Automatic", "", [M("trim")])[2].get("conflict", []))


def row(vid, **kw):
    b = {"id": vid, "vin": "", "year": 2015, "make": "Ford", "model": "Focus", "row": "1",
         "dateAdded": "2026-10-01", "_location": "Test Yard", "_city": "X", "_state": "CA", "_lat": 1.0, "_lng": 1.0}
    b.update(kw)
    return b


focus_dec = dec("FORD", "Focus", 2015, engine="1.0L 3-cyl", trimQuality="empty", bodyClass="")
vs = [row("ok", vin=focus, _vpic=dict(focus_dec)),
      row("mm", vin=focus, make="Acura", model="ILX", _vpic=dict(focus_dec)),
      row("cf", vin=focus, _vpic={**focus_dec, "transmission": "6-spd Automatic"}),
      row("nodec", vin=focus),
      row("grp", vin=focus, make="Mercury", _vpic=dict(focus_dec))]
E = {e["id"]: e for e in js.output_json(vs, only_matches=False)}
check("output_json: VIN-code manual published with transSrc vin_code",
      (E["ok"]["trans"], E["ok"]["transSrc"]) == ("Manual", "vin_code"), (E["ok"]["trans"], E["ok"]["transSrc"]))
check("output_json: VIN make contradicts the yard -> no rule claim", (E["mm"]["trans"], E["mm"]["transSrc"]) == ("", ""))
check("output_json: decode says automatic, rule says manual -> nothing", (E["cf"]["trans"], E["cf"]["transSrc"]) == ("", ""))
check("output_json: rule applies without a cached decode", E["nodec"]["transSrc"] == "vin_code")
check("output_json: same maker group (yard says Mercury, VIN says Ford) keeps the claim",
      E["grp"]["transSrc"] == "vin_code")
ex = js.compact_inventory_v2(list(E.values()))["_extras"]
check("extras shard carries the new transSrc", ex.get("ok", [])[3:5] == ["Manual", "vin_code"], ex.get("ok"))

# ---- 4. compiled table is current ----------------------------------------------------
print("compiled table")
for f, h in R.doc.get("sources", {}).items():
    cur = hashlib.sha256((MD / f).read_bytes()).hexdigest()[:16]
    check(f"trans_rules.json compiled from current {f}", cur == h,
          "worklist changed: rerun python3 -I scraper/manual_detect/compile_trans_rules.py")
check("compiled table has every track", bool(R.doc.get("vin_rules")) and bool(R.trims) and bool(R.epa))

# ---- 5. real data: precision + worklist reproduction ---------------------------------
print("real data (docs/data, cached decodes only)")
inv = json.loads((DATA / "inventory_live.json").read_text())
fi = {f: i for i, f in enumerate(inv["fields"])}
yards = inv["yards"]
extras = json.loads((DATA / "vehicle_extras.json").read_text())["extras"]
cache = json.loads(gzip.decompress((DATA / "vin_decodes.json.gz").read_bytes()))

counted_vin = {}
for i in range(8):
    for r in json.loads((MD / f"vin_rules_{i}.json").read_text())["rules"]:
        counted_vin[r["id"]] = r["status"] in ("keep", "keep_low_sample", "low_sample")
expected = {}                                   # car id -> (vin, rule)
for i in range(8):
    for c in json.loads((MD / f"vin_rules_{i}.json").read_text())["newly_confirmed_manual_cars"]:
        if counted_vin.get(c["rule"]):
            expected[str(c["id"])] = (c["vin"], c["rule"])
for c in json.loads((MD / "manual_trims.json").read_text())["newly_confirmed_manual_cars"]:
    if c.get("counted"):
        expected[str(c["id"])] = (c["vin"], c["rule"])
epa_ok = {(e["id"], y) for e in R.epa for y in e["years"]}
for c in json.loads((MD / "epa_sole.json").read_text())["newly_confirmed_manual_cars"]:
    if (c["rule"], c["year"]) in epa_ok:
        expected.setdefault(str(c["id"]), (c["vin"], c["rule"]))

cars, cell = [], defaultdict(Counter)
for rw in inv["vehicles"]:
    vid = str(rw[fi["id"]]); vin = (rw[fi["vin"]] or "").strip().upper()
    y = yards[rw[fi["yard"]]] if isinstance(rw[fi["yard"]], int) else ["", "", ""]
    e = list(extras.get(vid) or []) + [""] * 5
    listing = e[3] if e[4] == "listing" else ""
    vn = js._normalize_vin(vin)
    raw = cache.get(vn) if vn else None
    d = js._correct_vpic(raw, vn) if isinstance(raw, dict) else None
    vc = te.trans_class((d or {}).get("transmission"))
    if vc:
        cell[(d.get("make"), d.get("model"), d.get("modelYear"))][vc] += 1
    cars.append((vid, vin, rw[fi["year"]], rw[fi["make"]] or "", rw[fi["model"]] or "", y[2], listing, d, vc))
# vPIC cells that answer one class for every decoded lot car are model-level
# defaults, not evidence about each car (BASELINE.md section 2): unlabelled.
uniform = {k for k, c in cell.items() if len(c) == 1 and sum(c.values()) >= 5}

res, by_src, misses = Counter(), defaultdict(Counter), []
repro = Counter(); repro_miss = []
for vid, vin, yr, mk, md, st, listing, d, vc in cars:
    lc = te.trans_class(listing)
    if js._trans_make_conflict({"make": mk}, d):
        cs = []
    else:
        cs = R.infer(vin=vin, listing_year=yr, make=mk, model=md, dec=d, state=st)
    if vid in expected and expected[vid][0] == vin and not lc and not vc:
        repro["checked"] += 1
        if expected[vid][1] in rules_of(cs, "manual"):
            repro["ok"] += 1
        else:
            repro_miss.append((vid, vin, expected[vid][1]))
    truth = lc or vc
    if not truth or (not lc and d and (d.get("make"), d.get("model"), d.get("modelYear")) in uniform):
        continue
    for c in cs:
        if c["conflict_only"]:
            continue
        ok = (te.MANUAL if c["claim"] == "manual" else te.NOT_MANUAL) == truth
        res[(c["claim"], ok)] += 1
        by_src[c["src"]][ok] += 1
        if not ok and len(misses) < 10:
            misses.append((vid, vin, yr, mk, md, c["rule"], (d or {}).get("transmission"), listing))

man_n = res[("manual", True)] + res[("manual", False)]
all_n = sum(res.values())
man_p = res[("manual", True)] / man_n if man_n else 0.0
all_p = (res[("manual", True)] + res[("automatic", True)]) / all_n if all_n else 0.0
print(f"  ground truth: manual claims {res[('manual', True)]}/{man_n} = {man_p:.5f}; "
      f"all claims {res[('manual', True)] + res[('automatic', True)]}/{all_n} = {all_p:.5f}")
print("  by source: " + ", ".join(f"{s} {c[True]}/{c[True] + c[False]}" for s, c in sorted(by_src.items())))
for m in misses:
    print("  disagreement:", m)
check(f"manual-claim precision >= {MIN_PRECISION}", man_n >= 100 and man_p >= MIN_PRECISION, f"{man_p:.5f} on {man_n}")
check(f"all-claim precision >= {MIN_PRECISION}", all_n >= 1000 and all_p >= MIN_PRECISION, f"{all_p:.5f} on {all_n}")
print(f"  worklist cars still on the lots without a decoded/listed transmission: {repro['checked']}, "
      f"reproduced {repro['ok']}")
check("every verified worklist car still on the lots gets its manual claim",
      repro["checked"] >= 100 and not repro_miss, repro_miss[:5])

print()
if failures:
    print(f"{len(failures)} FAILURE(S): {failures}")
    sys.exit(1)
print("all manual-detect tests passed")
