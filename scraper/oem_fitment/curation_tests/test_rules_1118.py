#!/usr/bin/env python3
"""Rules for flaws 2-6 of the independent nissan check (interchange 2026-11-18,
groups/_report/nissan_verify_2026-11-18.json, removals_verify_2026-11-18.json).

2. Body from a fixed table, not the lot decodes (B14 200SX = coupe).
3. Engine / transmission limits named in the note ("Q70: 3.7L only",
   "manual only"), including the sibling rule (another number of the slot is
   listed for an engine ours never names).
4. Gas / hybrid catalog pages ("QX60: gas only").
5. Body codes read as bodies (Subaru S./W./WOBK, GM 37/69/67, Nissan C./4S.),
   PartsGiant quantity / callout fields neutral, and unparsed feature notes
   neutral when the page never splits by body (the 5 true claims R02-R04, R07,
   R21 come back; R01 and R20 stay held).
6. Rear-door window parts on Titan/Frontier: crew cab only."""
from _util import check, done
import adapters as A
import curate as C
import notes as N
import policy

F = "Fitting Vehicle Options: "
SPD, GM, NPD, IPD, FPG = ("www.subarupartsdeal.com", "www.gmpartsgiant.com", "www.nissanpartsdeal.com",
                          "www.infinitipartsdeal.com", "www.fordpartsgiant.com")
CTX = N.NoteContext(2012, frozenset({"focus"}), frozenset())

# ------------------------------------------------------------ 2. body table
check("body table: the B14 200SX is a coupe; models not listed fall back to lot + pages",
      policy.model_body_table("Nissan", "200SX", 1998) == {"coupe"}
      and policy.model_body_table("Nissan", "200SX", 1999) == {"coupe"}
      and policy.model_body_table("Infiniti", "G37", 2008) == {"coupe"}
      and policy.model_body_table("Infiniti", "G37", 2010) == {"sedan", "coupe", "convertible"}
      and policy.model_body_table("Nissan", "Frontier", 2005) is None
      and policy.model_body_table("Chevrolet", "Cobalt", 2007) is None)


class _BN:
    body_need = C.Curation.body_need
    t_body_variants = {}
    body_counts = {("Nissan", "200SX", 1998): {"sedan": 12}, ("Chevrolet", "Cobalt", 2007): {"sedan": 155, "coupe": 119}}


bn = _BN()
check("body need: a table model ignores a wrong lot decode (1998 200SX decoded sedan)",
      bn.body_need(("Nissan", "200SX", 1998)) == {"coupe"})
check("body need: other models keep the lot decodes", bn.body_need(("Chevrolet", "Cobalt", 2007)) == {"sedan", "coupe"})

# ------------------------------------------------------------ 5. body codes
check("subaru codes: S. sedan, W./WOBK wagon (R21 57229AG04A9P covers both 2005 Legacy bodies)",
      C._fvo_bodies("S.(25GT+25GTLTD) +W.(25GT+25GTLTD) +WOBK.25GTLTD, S.25GLI +W.25GLI +WOBK.(25GT+25GLI)", SPD)
      == {"sedan", "wagon"}
      and C._fvo_bodies("(S+W).25GT", SPD) == {"sedan", "wagon"} and C._fvo_bodies("OBK6.AT", SPD) == {"wagon"})
check("subaru codes: a head that is no body (trim, engine) decodes nothing",
      C._fvo_bodies("S.L +GT", SPD) is None and C._fvo_bodies("EZ30D.AT", SPD) is None)
check("gm body styles: 37 coupe, 69 sedan, 67 convertible; truck cab codes stay undecoded",
      C._fvo_bodies("AP(37)", GM) == {"coupe"} and C._fvo_bodies("J(69)(DG7)", GM) == {"sedan"}
      and C._fvo_bodies("J(37,69)", GM) == {"coupe", "sedan"} and C._fvo_bodies("J(67)", GM) == {"convertible"}
      and C._fvo_bodies("CK1(53-03)", GM) is None and C._fvo_bodies("U1(DL6,DR5)", GM) is None)
check("nissan body codes: every part must carry one",
      C._fvo_bodies("C. GA16DE", NPD) == {"coupe"} and C._fvo_bodies("4S. (E + XE + GXE)", NPD) == {"sedan"}
      and C._fvo_bodies("KC. S", NPD) is None and C._fvo_bodies("C. GA16DE, GA16DE", NPD) is None)
check("body cover: a decoded code names its bodies; an undecoded column still covers none",
      C._row_body_cover([F + "S.25GLI +W.25GLI"], CTX, SPD) == {"sedan", "wagon"}
      and C._row_body_cover([F + "AJ(37)(DC8)"], CTX, GM) == {"coupe"}
      and C._row_body_cover([F + "CK1(53-03)"], CTX, GM) == set())
check("body cover: quantity / callout / colour fields restrict nothing (R07 88960088 Camaro row)",
      C._row_body_cover(["Require Quantity: 02", "Package Quantity: 1"], CTX, GM) is None
      and C._row_body_cover(["Callout Name: 14553", "Interior Color: CHARCOAL"], CTX, FPG) is None)
FORD = ["Motor Assy", "Fit Note: Power Front Windows One Touch Up/Do", "Callout Name: 14553"]
check("body cover: an unparsed feature note restricts only when the page splits by body (R02 CV6Z-5423394-B)",
      C._row_body_cover(FORD, CTX, FPG, page_body=False) is None
      and C._row_body_cover(FORD, CTX, FPG, page_body=True) == set()
      and C._row_body_cover(["Fit Note: 4 door"], CTX, FPG, page_body=False) == set()
      and C._row_body_cover(["FRONT SIDE DOOR WINDOW(MANUAL), Sedan"], CTX, GM, page_body=False) == {"sedan"})
check("page names a body: words, door counts, decoded codes",
      C._row_names_body(["Fit Note: 4-Door Sedan"], FPG) and C._row_names_body([F + "J(37)"], GM)
      and C._row_names_body(["5 door"], FPG) and not C._row_names_body(FORD, FPG))


def fr(trims):
    return A.FitRow(idx=0, lo=2005, hi=2010, make="Chevrolet", model="Cobalt", trims=list(trims), engines=[],
                    options=[], layout="trim", raw="")


class _K:
    pass


class _FB:
    fit_bodies_plausible = C.Curation.fit_bodies_plausible

    def __init__(self, trims, k):
        self.t_rows = {(("Chevrolet", "Cobalt", 2007), "window-regulator"): [(k, None, fr(trims), None)]}


k = _K()
T = ("Chevrolet", "Cobalt", 2007)
check("fitment trims '4 DOOR' only make a coupe implausible (Cobalt regulator 15899051 stays out)",
      not _FB(["4 DOOR", "LEVEL ONE (LS) 4 DOOR"], k).fit_bodies_plausible(T, "window-regulator", k, {"coupe", "sedan"}))
check("fitment trims '2 DOOR, 4 DOOR' or none keep both bodies plausible",
      _FB(["2 DOOR", "4 DOOR"], k).fit_bodies_plausible(T, "window-regulator", k, {"coupe", "sedan"})
      and _FB(["LS", "LT"], k).fit_bodies_plausible(T, "window-regulator", k, {"coupe", "sedan"})
      and _FB(["2 DOOR", "CONVERTIBLE"], k).fit_bodies_plausible(T, "window-regulator", k, {"coupe", "convertible"}))
check("removals check: R01 / R20 are held with their basis (wrong for a reason other than body)",
      ("ford", "climate-control", "F8XZ-19980-AA") in policy.GROUP_HOLDS
      and ("subaru", "climate-control", "72311AE06B") in policy.GROUP_HOLDS)

# ------------------------------------------------------------ 3. engine / transmission
check("engine codes: Nissan families, Subaru, Hyundai/Kia litres",
      C._engine_terms("SEDAN. VQ37VHR. PREMIUM") == {3.7} and C._engine_terms("KC. KA24DE") == {2.4}
      and C._engine_terms("W. VG33E. XE") == {3.3} and C._engine_terms("EZ30D") == {3.0}
      and C._engine_terms("2.0L Theta 2.. DOHC") == {2.0} and C._engine_terms("[1.6L - GAMMA]") == {1.6}
      and C._engine_terms("*KC. 4WD. LE") == set())
check("transmissions: 6MT manual, AT/CVT/[Auto automatic; 'AUTO AC' is no transmission",
      C._trans_terms("KC. PRO-4X. 6MT") == {"manual"} and C._trans_terms("SE. AT") == {"auto"}
      and C._trans_terms("[Auto - 6 Speed 2WD]") == {"auto"} and C._trans_terms("CVT") == {"auto"}
      and C._trans_terms("AUTO AC") == set())
check("row engine/trans: every configuration must name it",
      C._row_engine_trans([F + "SEDAN. VQ37VHR. (TECHNOLO + SPORTTEC)"], IPD) == ({3.7}, None)
      and C._row_engine_trans([F + "KC. 4WD. SE. 6MT + CC. 4WD. 6MT"], NPD) == (None, "manual")
      and C._row_engine_trans([F + "SEDAN. VQ37VHR. PREMIUM + SEDAN. (BASE+ SPORTPRE)"], IPD) == (None, None)
      and C._row_engine_trans([F + "VQ37VHR"], GM) == (None, None))
check("row engine names: any configuration", C._row_engine_names([F + "W. SE, W. VG33E. XE"], NPD) == {3.3})
check("policy: engine/transmission and fuel rules are on",
      policy.LIKELY_ENGINE_TRANS_RULE and policy.LIKELY_FUEL_RULE)


class _Y:
    def __init__(self, variants):
        self.variant, self.variants = "gas", list(variants)


class _FU:
    fuel_of = C.Curation.fuel_of

    def __init__(self, T, variants, rows):
        self.t_years = {T: [_Y(variants)]}
        self._rows = rows

    def _own_rows(self, c, cat, T):
        return self._rows


QX = ("Infiniti", "QX60", 2014)
GAS = [([], IPD, "gas", "https://x/parts-list/2014-infiniti-qx60-gas/a/b.html")]
HYB = [([], IPD, "hybrid", "https://x/parts-list/2014-infiniti-qx60-hybrid/a/b.html")]
check("fuel: a gas-page-only number on a model-year with a hybrid catalog is 'gas only' (P08 24810-3JA1B)",
      _FU(QX, ["gas", "hybrid"], GAS).fuel_of(None, "gauge-cluster", QX) == "gas"
      and _FU(QX, ["gas", "hybrid"], HYB).fuel_of(None, "gauge-cluster", QX) == "hybrid"
      and _FU(QX, ["gas", "hybrid"], GAS + HYB).fuel_of(None, "gauge-cluster", QX) == ""
      and _FU(QX, ["gas"], GAS).fuel_of(None, "gauge-cluster", QX) == "")
QH = ("Infiniti", "QX60 Hybrid", 2014)
check("fuel: a feed name saying Hybrid with gas-page evidence only is a conflict",
      _FU(QH, ["gas", "hybrid"], GAS).fuel_of(None, "gauge-cluster", QH) == C.DRIVE_AMBIGUOUS)


def lr(T, pn, notes, url):
    return A.ListRow(site=NPD, seed=T, cat="window-regulator", list_url=url, pn=pn, section="d", main="m", aux="",
                     notes=list(notes), locations=[], replace=None, matched=True, excluded_by=None, product=None,
                     retrieved="2026-11-10T00:00:00Z", line=1, status=200)


REAR = "https://www.nissanpartsdeal.com/parts-list/2010-nissan-titan/body_side_rear/rear_door_window_regulator.html"
T10, T04 = ("Nissan", "Titan", 2010), ("Nissan", "Titan", 2004)


class _RC:
    rear_cab_of = C.Curation.rear_cab_of
    _model_rear_cabs = C.Curation._model_rear_cabs
    ns = "nissan"

    def __init__(self):
        self.t_list_rows = {(T10, "window-regulator"): [
            lr(T10, "82300-7S200", [F + "KC. S, KC. XE"], REAR), lr(T10, "82300-8S500", [F + "CC"], REAR),
            lr(T10, "82731-7S000", [], REAR)]}

    def _own_rows(self, c, cat, T):
        return [([], NPD, "", REAR)]


rc = _RC()
check("rear cab: a rear-door window part without a cab code on a KC/CC-split rear-door page is crew cab only",
      rc.rear_cab_of(None, "window-regulator", T10, ("RL",)) == "crew cab"
      and rc.rear_cab_of(None, "window-regulator", T04, ("RL",)) == "crew cab"
      and rc.rear_cab_of(None, "window-regulator", T10, ("FL",)) == ""
      and rc.rear_cab_of(None, "window-regulator", T10, ("FR", "RR")) == "")


class _Cur:
    _limit_note = C.Curation._limit_note


cur = _Cur()
check("limit note: labels combine per model ('Frontier: 2WD, automatic only; Xterra: 2WD only')",
      cur._limit_note({("Nissan", "Frontier", 2010): "2WD, automatic", ("Nissan", "Xterra", 2010): "2WD"})
      == "Frontier: 2WD, automatic only; Xterra: 2WD only"
      and cur._limit_note({("Infiniti", "M37", 2013): "", ("Infiniti", "Q70", 2014): "3.7L, gas"})
      == "Q70: 3.7L, gas only"
      and cur._limit_note({("Nissan", "Titan", 2004): "crew cab", ("Nissan", "Titan", 2005): "crew cab",
                           ("Nissan", "Armada", 2004): ""}) == "Titan: crew cab only")
done("test_rules_1118")
