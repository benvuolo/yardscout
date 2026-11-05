#!/usr/bin/env python3
"""measure.py (CURATION_SPEC.md §10): the client-logic port, the aggregated
metrics against a car-by-car derivation from the literal client loop, the
identity guard, the old/new views, flips and the funnel roll-up. Offline,
synthetic fleet; the real-data parity runs with `measure.py --parity`."""
import json
import tempfile
from pathlib import Path

from _util import check, done, skip
import measure as M

# §9 Phase 2 parity: node evaluates the app's OEM-TIER block against
# measure.py. Phase 2 has no client code yet, so there is nothing to compare.
_app = (M.REPO / "docs" / "app.js")
if not _app.exists() or "/* OEM-TIER BEGIN */" not in _app.read_text():
    skip("Phase 2 parity (spec 9, node vs measure.py)",
         "docs/app.js has no /* OEM-TIER BEGIN */ block: the Phase 2 client is not written")
else:
    check("Phase 2 parity is implemented once the OEM-TIER block exists", False,
          "docs/app.js now has OEM-TIER: write the node parity test (spec 9)")

# ------------------------------------------------------------- port units
check("pfSquashModel drops the make and a trailing 'pickup'",
      M.squash_model("Toyota Tacoma Pickup", "Toyota") == "tacoma" and M.squash_model("Pickup", "") == "pickup")
check("pfAppMatches: prefix pattern, make list, year window",
      M.app_matches(["Dodge|Ram", "Ram*", 2010, 2012], 2011, "Ram", "Ram 2500")
      and not M.app_matches(["Dodge", "Ram*", 2010, 2012], 2011, "Ram", "Ram 2500")
      and not M.app_matches(["Toyota", "Camry", 2007, 2011], 2012, "Toyota", "Camry")
      and not M.app_matches(["Toyota", "Camry", 2007, 2011], 2009, "Toyota", "Camry Hybrid"))
check("pfEngineVerdict: diesel denies, liters within 0.05, cylinders must agree",
      M.engine_verdict("2.8L 4-cyl Diesel", {"liters": [2.8], "cyl": 4}) is False
      and M.engine_verdict("2.4L 4-cyl", {"liters": [2.4], "cyl": 4}) is True
      and M.engine_verdict("2.4L 6-cyl", {"liters": [2.4], "cyl": 4}) is False
      and M.engine_verdict("", {"liters": [2.4], "cyl": 4}) is None)
check("pfParseFits reads en dash and hyphen windows", M.parse_fits("2007–2011") == (2007, 2011)
      and M.parse_fits("2002-2006") == (2002, 2006) and M.parse_fits("") is None)
check("pfVinValid: the check digit decides", M.vin_valid("1HGCM82633A004352")
      and not M.vin_valid("1HGCM82643A004352") and not M.vin_valid("1HGCM8263"))
check("pfVinModelYear resolves the 30-year cycle toward the listed year",
      M.vin_model_year("1HGCM82633A004352", 2003) == 2003 and M.vin_model_year("1HGCM8263AA004352", 2012) == 2010
      and M.vin_model_year("1HGCM8263AA004352", 1983) == 1980 and M.vin_model_year("1HGCM8263UA004352", 2010) is None)


def vin(year: int) -> str:
    """A VIN with a correct check digit and the model-year code for `year`."""
    s = list("1HGCM82600A004352")
    s[9] = M._VIN_YEAR[(year - 1980) % 30]
    for d in "0123456789X":
        s[8] = d
        if M.vin_valid("".join(s)):
            return "".join(s)
    raise AssertionError(year)


check("pfDonorIdentity: vPIC mismatch, VIN year disagreement, OEM rows need a valid VIN",
      not M.donor_identity_ok(True, vin(2009), 2009) and not M.donor_identity_ok(False, vin(2008), 2009)
      and M.donor_identity_ok(False, "", 2009) and not M.donor_identity_ok(False, "", 2009, oem=True)
      and M.donor_identity_ok(False, vin(2009), 2009, oem=True))

# ------------------------------------------------------------ synthetic fleet
CARS = [  # id, vin, year, make, model, yard, partSet, engine, vpic mismatch
    (1, vin(2009), 2009, "Toyota", "Camry", 0, 1, "2.4L 4-cyl", ""),
    (2, vin(2009), 2009, "Toyota", "Camry", 2, 0, "", ""),
    (3, vin(2010), 2010, "Toyota", "Camry Hybrid", 1, 0, "2.4L 4-cyl", ""),
    (4, vin(2009), 2009, "Toyota", "Corolla", 0, 0, "", "VIN decodes as Pontiac Vibe"),
    (5, vin(2005), 2005, "Toyota", "Camry", 0, 2, "2.4L 4-cyl", ""),
    (6, "", 2009, "Lexus", "ES 350", 1, 0, "", ""),
    (7, vin(2008), 2009, "Toyota", "Camry", 1, 0, "3.5L 6-cyl", ""),
    (8, vin(2011), 2011, "Toyota", "Camry", 0, 1, "2.5L 4-cyl", ""),
    (9, vin(2009), 2009, "Toyota", "Matrix", 1, 0, "", ""),
    (10, vin(2004), 2004, "Toyota", "Camry", 2, 2, "2.4L 4-cyl", ""),
]
INV = {"scrapedAt": "2026-11-05T00:00:00Z",
       "fields": ["id", "vin", "year", "make", "model", "row", "dateAdded", "yard", "partSet", "maxValue", "premium"],
       "yardFields": ["location", "city", "state", "lat", "lng", "avgLifespanDays", "lifespanBasis"],
       "yards": [["Y0", "Los Angeles", "CA", 34.05, -118.24, 90, "yard"],
                 ["Y1", "Pasadena", "CA", 34.15, -118.14, 90, "yard"],
                 ["Y2", "Philadelphia", "PA", 39.95, -75.16, 90, "yard"]],
       "partSets": [[], [{"name": "Side Mirror (power)", "fits": "2007–2011"}],
                    [{"name": "Side Mirror", "fits": "2002–2006"}]],
       "vpic": {str(i): ["", "usable", "", "", c[8]] for i, c in enumerate(CARS) if c[8]},
       "vehicles": [[c[0], c[1], c[2], c[3], c[4], "", "", c[5], c[6], 0, 0] for c in CARS]}
EXTRAS = {"extras": {str(c[0]): ["", "", c[7], "", "vin"] for c in CARS}}
CATS = [{"id": "side-mirrors", "kind": "body", "tokens": ["side mirror"]},
        {"id": "headlights", "kind": "body", "tokens": ["headlight"]},
        {"id": "alternator", "kind": "engine", "tokens": ["alternator"]},
        {"id": "radio", "kind": "exact", "tokens": ["radio"]}]
FAMS = [{"id": "toyota-2az", "label": "2AZ", "liters": [2.4], "cyl": 4,
         "apps": [["Toyota", "Camry", 2002, 2009, 1, ""], ["Toyota", "Camry Hybrid", 2007, 2009, 0, "hybrid: no belt"]],
         "parts": {"alternator": {"note": "n", "vg": [[["Toyota", "Camry", 2002, 2006]]]}}},
        {"id": "toyota-2gr", "label": "2GR", "liters": [3.5], "cyl": 6,
         "apps": [["Toyota", "Camry", 2007, 2011, 0, ""]], "parts": {"alternator": {"note": "n"}}}]
BEFORE = {"categories": CATS, "engineFamilies": FAMS,
          "platformGroups": [
              {"id": "camry#0", "cat": "side-mirrors", "tier": "verified", "label": "L", "note": "n",
               "apps": [["Toyota", "Camry", 2007, 2011], ["Toyota", "Camry Hybrid", 2007, 2011]]},
              {"id": "bogus#0", "cat": "headlights", "tier": "bogus", "label": "L", "note": "n",
               "apps": [["Toyota", "Corolla", 2009, 2009], ["Toyota", "Matrix", 2009, 2009]]}],
          "modelGenerations": [["Toyota", "Camry", [[2002, 2006], [2007, 2011]]]]}
AFTER = json.loads(json.dumps(BEFORE))
AFTER["oemGroups"] = [
    {"id": "oem:toyota:side-mirrors:aaaaaaaaaa", "ns": "toyota", "cat": "side-mirrors", "tier": "verified",
     "apps": [["Toyota", "Corolla", 2009, 2009], ["Toyota", "Matrix", 2009, 2009]], "pn": ["x"], "src": "oem"},
    {"id": "oem:toyota:side-mirrors:L:bbbbbbbbbb", "ns": "toyota", "cat": "side-mirrors", "tier": "likely",
     "apps": [["Lexus", "ES 350", 2009, 2009], ["Toyota", "Camry", 2009, 2009]], "pn": ["y"], "src": "oem"},
    {"id": "oem:toyota:headlights:cccccccccc", "ns": "toyota", "cat": "headlights", "tier": "verified",
     "apps": [["Lexus", "ES 350", 2009, 2009], ["Toyota", "Matrix", 2009, 2009]], "pn": ["z"], "src": "oem"}]
AFTER["oemVg"] = {"toyota-2az": {"alternator": [[["Toyota", "Camry", 2007, 2009]]]}}

fleet = M.Fleet(INV, EXTRAS)
check("fleet: yards within 100 mi are near, across the country are not",
      1 in fleet.near[0] and 2 not in fleet.near[0] and fleet.near[2] == [2])
choice, unknown = M._family_choice(fleet, BEFORE, "alternator")
idx = {c[0]: i for i, c in enumerate(CARS)}
check("engine seeker = its decoded family: 2.4 -> 2AZ, 3.5 -> 2GR, silent with two offers -> unknown",
      choice.get(idx[1]) == "toyota-2az" and choice.get(idx[7]) == "toyota-2gr" and idx[2] not in choice
      and choice.get(idx[5]) == "toyota-2az" and idx[8] not in choice, str(choice))


def brute(payload, cat, view, kind):
    """M-car / M-local / pairs derived car by car from the literal client loop."""
    m_car = m_local = pv = pl = 0
    fam_of = M._family_choice(fleet, payload, cat)[0] if kind == "engine" else {}
    for ci, car in enumerate(fleet.cars):
        if kind == "engine" and ci not in fam_of:
            continue
        S = (car[3], car[4], car[2])
        res = M.client_loop(fleet, payload, cat, S, view, fam_of.get(ci), detail=True)
        others = {d: t for d, t in res.items() if d != ci}
        ver = [d for d, t in others.items() if t == "verified"]
        m_car += bool(ver)
        m_local += any(fleet.cars[d][5] in fleet.near[car[5]] for d in ver)
        pv += len(ver)
        pl += len(others) - len(ver)
    return m_car, m_local, pv, pl


views = {}
for pname, payload in (("before", BEFORE), ("after", AFTER)):
    for view in ("old", "new"):
        views[(pname, view)] = M.measure(fleet, payload, view)
        for cat, kind in (("side-mirrors", "body"), ("headlights", "body"), ("alternator", "engine")):
            r = views[(pname, view)][cat]
            got = (r.m_car, r.m_local, r.pairs_v, r.pairs_l)
            want = brute(payload, cat, view, kind)
            check(f"aggregated == car-by-car client loop: {pname}/{view} {cat}", got == want, f"{got} != {want}")

mir = {k: v["side-mirrors"] for k, v in views.items()}
c0 = ("Toyota", "Camry", 2009)
check("old view: the VIN-year mismatch donor (id 7) counts Verified; new view demotes it",
      mir[("before", "old")].per_seeker[c0][0] == mir[("before", "new")].per_seeker[c0][0] + 1)
hl = {k: v["headlights"] for k, v in views.items()}
check("old view fails open: tier 'bogus' counts Verified; the P0.1 guard makes it Likely",
      hl[("before", "old")].m_car == 2 and hl[("before", "new")].m_car == 0
      and hl[("before", "old")].per_seeker[("Toyota", "Corolla", 2009)] == (2, 0)
      and hl[("before", "new")].per_seeker[("Toyota", "Corolla", 2009)] == (0, 2))


def tiers(payload, cat, seeker, view):
    return {fleet.cars[ci][0]: t for ci, t in M.client_loop(fleet, payload, cat, seeker, view, detail=True).items()}
check("OEM keys are read only by the new view (old view identical before/after)",
      all((views[("before", "old")][c].m_car, views[("before", "old")][c].pairs_v, views[("before", "old")][c].pairs_l)
          == (views[("after", "old")][c].m_car, views[("after", "old")][c].pairs_v, views[("after", "old")][c].pairs_l)
          for c in ("side-mirrors", "headlights", "alternator")))
t = tiers(AFTER, "side-mirrors", ("Toyota", "Matrix", 2009), "new")
check("an OEM Verified donor with a vPIC mismatch is Likely; its clean partner is Verified",
      t.get(4) == "likely" and t.get(9) == "verified", str(t))
check("so the Corolla lot car has a Verified donor and the Matrix lot car does not",
      mir[("after", "new")].m_car - mir[("before", "new")].m_car == 1)
t = tiers(AFTER, "headlights", ("Toyota", "Matrix", 2009), "new")
check("an OEM Verified donor with no VIN is Likely (OEM rows need a VIN to confirm the year)",
      t.get(6) == "likely" and t.get(9) == "verified", str(t))
alt = {k: v["alternator"] for k, v in views.items()}
check("oemVg adds Verified engine pairs in the new view only",
      alt[("after", "new")].pairs_v > alt[("before", "new")].pairs_v
      and alt[("after", "old")].pairs_v == alt[("before", "old")].pairs_v)
check("an exact-kind category has no Verified tier", views[("after", "new")]["radio"].m_car == 0
      and "no Verified tier" in views[("after", "new")]["radio"].note)

fl = M.flips(fleet, views[("before", "new")], views[("after", "new")])
sm = fl["side-mirrors"]
check("flips: Likely -> Verified for Corolla / Matrix, attributed cross-model",
      sm["likely_to_verified"]["key_pairs"] == 1 and sm["lever_attribution"]["cross-model"] == 1
      and sm["likely_to_verified"]["sample"] == [[["Toyota", "Corolla", 2009], ["Toyota", "Matrix", 2009]]],
      json.dumps(sm["likely_to_verified"]))
check("flips: the OEM Likely group adds new cross-model Likely pairs (Lexus ES 350 <-> Camry)",
      sm["new_cross_model_likely"]["key_pairs"] >= 1
      and any(s == ["Lexus", "ES 350", 2009] for s, _d in sm["new_cross_model_likely"]["sample"]))
check("flips: nothing goes Verified -> Likely when no demotion happened", sm["verified_to_likely"]["key_pairs"] == 0)

# ------------------------------------------------------------ funnel roll-up
d = Path(tempfile.mkdtemp())
for ns, n in (("toyota", 10), ("mopar", 5)):
    (d / f"{ns}.json").write_text(json.dumps({
        "ns": ns, "as_of": "x", "raw": {"commit": "abc"},
        "summary": {"gates": ["no R1"], "verified_groups": 0, "vg_groups": 0, "likely_groups": 1},
        "funnel_cars": {"side-mirrors": {"not_closed": {"no_year_manifest": n}, "unmapped": {"": 1}}},
        "funnel_cars_hypothetical_if_every_year_closed": {"by_cat": {"side-mirrors": {"split": {"option_split": n}}}}}))
    (d / f"{ns}.completion.json").write_text(json.dumps({"rows": [{"make": "Toyota", "gain_pairs": 3}]}))
(d / "coverage-2026-11-05.json").write_text("{}")
(d / "toyota.map-proposals.json").write_text("{}")
f = M.funnel_from_reports(d)
check("funnel: cars summed per stage across namespaces; other report files skipped",
      f["by_cat"]["side-mirrors"]["not_closed"]["no_year_manifest"] == 15 and sorted(f["by_ns"]) == ["mopar", "toyota"])
check("funnel: blocked-by and the labelled hypothetical funnel",
      f["blocked_by"]["not_closed:no_year_manifest"] == 15
      and f["hypothetical_by_cat"]["by_cat"]["side-mirrors"]["split"]["option_split"] == 15
      and f["hypothetical_by_cat"]["label"].startswith("HYPOTHETICAL"))
check("measure.py skips with a printed reason when the inventory is absent (rule 8)",
      M.main(["--inventory", str(d / "nope.json"), "--groups", str(d)]) == 3)
done("test_measure")
