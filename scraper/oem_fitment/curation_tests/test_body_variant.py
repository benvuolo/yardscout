#!/usr/bin/env python3
"""§5.16 body-variant rule (policy.LIKELY_BODY_GATE, interchange 2026-11-18).

One feed model name can cover several bodies (Infiniti "G37" = sedan, coupe,
convertible; "Versa" sedan/hatchback). A vehicle-year that comes in 2+
bodies joins a Likely group only when its own pages show the number for
every one of them. Real cases from oem-raw@57e8b5b9 (nissan §11.4 trap
check): 82721-JK000, a rear-door regulator, sits on the 2008 G37 SEDAN page
while every decoded 2008 G37 on the lots is a coupe; 80720-AM811 sits on the
2007 G35 sedan page with "Fitting Vehicle Options: C" (coupe). The rule only
removes claims."""
from collections import Counter

from _util import check, done
import adapters as A
import curate as C
import policy

check("policy: the rule is on, wheels keep their own rules",
      policy.LIKELY_BODY_GATE and "wheels" in policy.LIKELY_BODY_SKIP_CATS)

# ---------------------------------------------------------------- helpers
check("body words: catalog variants and notes",
      C._body_words("2009-infiniti-g37-sedan") == {"sedan"} and C._body_words("coupe") == {"coupe"}
      and C._body_words("Convertible") == {"convertible"} and C._body_words("Roadster") == {"convertible"}
      and C._body_words("hatchback") == {"hatchback"} and C._body_words("Liftback") == {"hatchback"})
check("body words: none in neutral variants or model names (Grand Caravan is not a van word)",
      C._body_words("gas") == set() and C._body_words("b14u") == set() and C._body_words("") == set()
      and C._body_words("2010-dodge-grand-caravan") == set())
check("catalog segment of a parts-list URL",
      C._catalog_of("https://www.infinitipartsdeal.com/parts-list/2008-infiniti-g35-sedan/body_side_rear/x.html")
      == "2008-infiniti-g35-sedan" and C._catalog_of("") == "")

import notes as N  # noqa: E402
CTX = N.NoteContext(2009, frozenset({"g37"}), frozenset())
check("row cover: no notes / colour / position / production date cover every body",
      C._row_body_cover([], CTX) is None and C._row_body_cover(["Lt Gray"], CTX) is None
      and C._row_body_cover(["Production Date: 08/2010-07/2011"], CTX) is None)
check("row cover: an option-column code may be a body code (S sedan / C coupe): covers no body",
      C._row_body_cover(["Fitting Vehicle Options: C"], CTX) == set()
      and C._row_body_cover(["Fitting Vehicle Options: S. LEATHER"], CTX) == set())
check("row cover: a body word covers that body only",
      C._row_body_cover(["Sedan"], CTX) == {"sedan"} and C._row_body_cover(["Hatchback; Japan Built"], CTX) == {"hatchback"})
check("row cover: an unparsed clause covers no body",
      C._row_body_cover(["(KC+ SC). XD. VK56VD + 4WD/LWB"], CTX) == set())


# ---------------------------------------------------------------- body_ok
def lr(variant, pn="82721-JK000", notes=(), line=1, matched=True):
    return A.ListRow(site="www.infinitipartsdeal.com", seed=("Infiniti", "G37", 2010), cat="window-regulator",
                     list_url=f"https://x/parts-list/2010-infiniti-g37-{variant}/b/c.html", pn=pn, section="diagram",
                     main="Regulator", aux="", notes=list(notes), locations=[], replace=None, matched=matched,
                     excluded_by=None, product=None, retrieved="2026-11-10T00:00:00Z", line=line, status=200,
                     variant=variant)


class K:
    key = policy.pn_key("nissan", "82721-JK000")


def cur_with(rows, variants=(), counts=None):
    c = C.Curation.__new__(C.Curation)
    c.ns = "nissan"
    c.t_list_rows = {(T, "window-regulator"): rows} if rows else {}
    c.t_seed_records = {}
    c.t_body_variants = {T: set(variants)}
    c.body_counts = {T: counts} if counts else {}
    c.t_sources = {T: {("Infiniti", "G37")}}
    c.ns_models_f = frozenset()
    c.note_excludes = lambda notes, t, market=True: False
    return c


T = ("Infiniti", "G37", 2010)
c = cur_with([lr("sedan")], variants={"sedan", "coupe", "convertible"})
check("G37 2010: listed on the sedan page only, catalog also offers coupe/convertible -> left out",
      not c.body_ok(T, "window-regulator", K()))
c = cur_with([lr("sedan"), lr("coupe", line=2), lr("convertible", line=3)], variants={"sedan", "coupe", "convertible"})
check("G37 2010: listed on every body page -> joins", c.body_ok(T, "window-regulator", K()))
c = cur_with([lr("sedan"), lr("coupe", line=2)], variants={"sedan", "coupe", "convertible"})
check("G37 2010: convertible page not showing it (or not read) -> left out", not c.body_ok(T, "window-regulator", K()))
c = cur_with([lr("sedan", notes=["Fitting Vehicle Options: C"]), lr("coupe", line=2)], variants={"sedan", "coupe"})
check("a sedan page row coded C (coupe) does not cover the sedan", not c.body_ok(T, "window-regulator", K()))
c = cur_with([lr("sedan")], variants={"sedan"}, counts={"coupe": 40})
check("2008 G37: only a sedan page in the catalog, but the lot's cars are coupes -> left out",
      not c.body_ok(T, "window-regulator", K()))
c = cur_with([lr("sedan")], variants={"sedan"}, counts={"sedan": 200, "coupe": 2})
check("lot noise under 5% does not make a body (Sentra 'coupe' 2 of 3,764)", c.body_ok(T, "window-regulator", K()))
c = cur_with([lr("")], variants=set(), counts={"sedan": 50, "coupe": 30})
check("combined page, row without notes: covers every body -> joins", c.body_ok(T, "window-regulator", K()))
c = cur_with([lr("", notes=["Coupe"])], variants=set(), counts={"sedan": 50, "coupe": 30})
check("combined page, row noted 'Coupe' on a sedan/coupe car -> left out", not c.body_ok(T, "window-regulator", K()))
c = cur_with([lr("", notes=["Sedan"]), lr("", notes=["Coupe"], line=2)], variants=set(), counts={"sedan": 50, "coupe": 30})
check("combined page, rows noted 'Sedan' and 'Coupe' for the same number -> joins", c.body_ok(T, "window-regulator", K()))
c = cur_with([lr("sedan")], variants={"sedan", "coupe"})
check("wheels are skipped (their own whole-group rules)", c.body_ok(T, "wheels", K()))
c = cur_with([lr("sedan")], variants={"sedan"}, counts={"sedan": 90})
check("single-body car: no change", c.body_ok(T, "window-regulator", K()))


# ---------------------------------------------------------------- lot counts
class JS:
    @staticmethod
    def body_style_from_vpic(vp, make):
        return {"Sedan/Saloon": "sedan", "Sport Utility Vehicle (SUV)/Multi-Purpose Vehicle (MPV)": "suv",
                "Wagon": "wagon"}.get((vp or {}).get("bodyClass"), "")


import gzip, json, tempfile, os  # noqa: E401,E402
inv = {"fields": ["id", "vin", "year", "make", "model"], "vehicles": [
    [1, "A", 2015, "Subaru", "Legacy"], [2, "B", 2015, "Subaru", "Legacy"], [3, "C", 2015, "Subaru", "Legacy"],
    [4, "D", 2012, "Subaru", "Impreza"], [5, "E", 2012, "Subaru", "Impreza"]]}
dec = {"A": {"bodyClass": "Sedan/Saloon", "model": "Legacy"},
       "B": {"bodyClass": "Sport Utility Vehicle (SUV)/Multi-Purpose Vehicle (MPV)", "model": "Outback"},
       "C": {"bodyClass": "Sedan/Saloon", "model": ""},
       "D": {"bodyClass": "Wagon", "model": "Impreza"},
       "E": {"bodyClass": "Sport Utility Vehicle (SUV)/Multi-Purpose Vehicle (MPV)", "model": "Impreza Wagon"}}
fd, p = tempfile.mkstemp(suffix=".json.gz")
os.close(fd)
with gzip.open(p, "wt") as f:
    json.dump(dec, f)
bc = C.model_body_counts(inv, JS, p)
check("lot counts: a 'Legacy' whose decode names the Outback is not a Legacy body",
      bc.get(("Subaru", "Legacy", 2015)) == {"sedan": 2}, str(bc.get(("Subaru", "Legacy", 2015))))
check("lot counts: wagon and SUV are one silhouette", bc.get(("Subaru", "Impreza", 2012)) == {"wagon": 2},
      str(bc.get(("Subaru", "Impreza", 2012))))
check("lot counts: no decodes file -> {} (catalog pages only)", C.model_body_counts(inv, JS, p + ".missing") == {})
os.unlink(p)

# ---------------------------------------------------------------- Nissan cab codes (note only)
check("nissan cab codes: one cab per row (2010 Frontier 27510-9CA0A 'CC. S'; 'KC. S, KC. XE')",
      C._fvo_cab_codes(["Fitting Vehicle Options: CC. S"]) == {"CC"}
      and C._fvo_cab_codes(["Fitting Vehicle Options: *KC. S, *KC. XE, KC. QR25DE. SE"]) == {"KC"}
      and C._fvo_cab_codes(["Production Date: 07/2008-08/2009", "Fitting Vehicle Options: CC"]) == {"CC"})
check("nissan cab codes: both cabs, a non-cab alternative, a mixed code or no option column -> no single cab",
      C._fvo_cab_codes(["Fitting Vehicle Options: CC, KC. VQ40DE"]) == {"CC", "KC"}
      and C._fvo_cab_codes(["Fitting Vehicle Options: W. X"]) is None
      and C._fvo_cab_codes(["Fitting Vehicle Options: (KC+ SC). XD"]) is None
      and C._fvo_cab_codes([]) is None and C._fvo_cab_codes(["Fitting Vehicle Options: CCX"]) is None)
check("nissan cab codes: '+' joins cabs inside one alternative (24810-ZS42D '*KC. 4WD. LE + *CC. 4WD. LE')",
      C._fvo_cab_codes(["Fitting Vehicle Options: *KC. 4WD. LE + *CC. 4WD. LE"]) == {"KC", "CC"}
      and C._fvo_cab_codes(["Fitting Vehicle Options: KC. 4WD. SV. 6MT + CC. 4WD. (S+ SV). 6MT"]) == {"KC", "CC"}
      and C._fvo_cab_codes(["Fitting Vehicle Options: CC. STD/BED. (SV+ SL) + CC. LONG/BED"]) == {"CC"})
cc = C.Curation.__new__(C.Curation)
cc.ns = "nissan"
FT = ("Nissan", "Frontier", 2010)
XT = ("Nissan", "Xterra", 2010)


def nrow(T, notes, line):
    r = lr("", pn="27510-9CA0A", notes=notes, line=line)
    r.seed = T
    return r


class K2:
    key = policy.pn_key("nissan", "27510-9CA0A")


cc.t_list_rows = {(FT, "climate-control"): [nrow(FT, ["Fitting Vehicle Options: CC. S"], 1)],
                  (XT, "climate-control"): [nrow(XT, ["Fitting Vehicle Options: W. X"], 2)]}
cc.t_rows = {}
check("nissan cab note: the Frontier's rows all code CC -> 'Frontier: crew cab only'; the Xterra gets none",
      cc._cab_only(K2(), "climate-control", [FT, XT]) == "Frontier: crew cab only",
      cc._cab_only(K2(), "climate-control", [FT, XT]))
cc.ns = "gm"
check("the Nissan cab note never runs for another namespace", cc._cab_only(K2(), "climate-control", [FT, XT]) == "")

# ---------------------------------------------------------------- Nissan body codes (nissan §11.4 round 4)
F0 = "Fitting Vehicle Options: "
check("nissan body codes: a coupe-coded row is not a Sentra sedan's, a 4-door-sedan row not a 200SX coupe's",
      C._nissan_body_code_excludes([F0 + "C. GA16DE"], {"sedan"})
      and C._nissan_body_code_excludes([F0 + "4S. (E + XE + GXE)"], {"coupe"})
      and C._nissan_body_code_excludes([F0 + "S. LEATHER"], {"coupe"}))
check("nissan body codes: own body, region/plant prefixes, cab codes, trims and unknown bodies keep the row",
      not C._nissan_body_code_excludes([F0 + "C, C. GA16DE"], {"coupe"})
      and not C._nissan_body_code_excludes([F0 + "J/4S. GXE, U/2S. CAL. SE"], {"sedan"})
      and not C._nissan_body_code_excludes([F0 + "FED. S. XE + CAL. S. XE"], {"sedan"})
      and not C._nissan_body_code_excludes([F0 + "CC. S"], {"pickup"})
      and not C._nissan_body_code_excludes([F0 + "W. X"], set())
      and not C._nissan_body_code_excludes(["PRIMER"], {"sedan"}))

# ---------------------------------------------------------------- production 'from' windows (nissan §11.4 round 3)
check("production: an open 'from MM/YYYY' window after the model year excludes it (Xterra 2002 'from 12/2002')",
      C._production_excludes(["Production Date: from 12/2002"], 2002)
      and C._production_excludes(["Production Date: 02/2005-08/2006,from 08/2010"], 2008))
check("production: a 'from' window that reaches the model year keeps it; 'from' outside a production note is ignored",
      not C._production_excludes(["Production Date: from 12/2002"], 2003)
      and not C._production_excludes(["Production Date: 02/2009-08/2010,from 08/2010"], 2011)
      and not C._production_excludes(["Fit Note: from 12/2002"], 2002))

# ---------------------------------------------------------------- Infiniti engine codes (nissan §11.4 round 1)
F = "Fitting Vehicle Options: "
check("infiniti engine: a V6-only cluster row is not listed for the M56, a V8-only row not for the M37",
      C._infiniti_engine_excludes([F + "SEDAN. VQ37VHR. (TECHNOLO + SPORTTEC)"], ("Infiniti", "M56", 2013))
      and C._infiniti_engine_excludes([F + "SEDAN. VK56VD. PREMIUM"], ("Infiniti", "M37", 2013))
      and C._infiniti_engine_excludes([F + "*S. VQ35HR. (BASE + TEC + SPORT + SPORTEC)"], ("Infiniti", "M45", 2009))
      and C._infiniti_engine_excludes([F + "*S. VK45DE. (BASE + TEC + SPORT + SPORTEC)"], ("Infiniti", "M35", 2009)))
check("infiniti engine: own engine, an alternative without an engine, post-2014 names and Nissans keep the row",
      not C._infiniti_engine_excludes([F + "SEDAN. VQ37VHR. (TECHNOLO + SPORTTEC)"], ("Infiniti", "M37", 2013))
      and not C._infiniti_engine_excludes([F + "*SEDAN. 2WDSTD. SPORTPRE, *SEDAN. 2WDSTD. VQ37VHR. PREMIUM"],
                                          ("Infiniti", "M56", 2013))
      and not C._infiniti_engine_excludes([F + "S. VQ37VHR"], ("Infiniti", "Q40", 2015))
      and not C._infiniti_engine_excludes([F + "VK56VD"], ("Nissan", "Titan", 2010))
      and not C._infiniti_engine_excludes([], ("Infiniti", "M56", 2013)))
check("infiniti engine: '+' joins configurations inside one alternative (G25 VQ25HR + VQ37VHR is not a G35 row)",
      C._infiniti_engine_excludes([F + "S. 2WD/STD. VQ25HR. (JOURNEY+ PREMIUM) + S. AWD. VQ25HR + S. VQ37VHR"],
                                  ("Infiniti", "G35", 2008))
      and not C._infiniti_engine_excludes([F + "S. 2WD/STD. VQ25HR. (JOURNEY+ PREMIUM) + S. AWD. VQ25HR"],
                                          ("Infiniti", "G25", 2011)))
done("test_body_variant")
