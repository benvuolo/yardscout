#!/usr/bin/env python3
"""§5.16 drive rule (policy.LIKELY_DRIVE_RULE, interchange 2026-11-18).

The independent nissan check (groups/_report/nissan_verify_2026-11-18.json)
found 4WD-only and 2WD-only gauge clusters claimed for every car of
model-years built in both drives (24810-EA101: 2005 Frontier "*KC. 4WD. LE",
2005 Xterra "*W. 4WD. SE"). The live census found the same class on GM
(the number on the 1500_2wd / 2wd catalog page only, or a single-series code
K1 / T1) and Mopar ("6 - Lt. Duty DODGE 4WD"). OEM Likely apps carry no drive
gate in the app, so the note names the limit ("Frontier: 4WD only"), and
ambiguous drive evidence leaves the vehicle-year out. Only narrows."""
from _util import check, done
import adapters as A
import curate as C
import policy

F = "Fitting Vehicle Options: "
NPD, GM, JPD, MPG, FPG, VW, SPD = ("www.nissanpartsdeal.com", "www.gmpartsgiant.com", "www.jeeppartsdeal.com",
                                   "www.moparpartsgiant.com", "www.fordpartsgiant.com", "www.vwpartsgiant.com",
                                   "www.subarupartsdeal.com")
FOUR, TWO = frozenset({"4wd"}), frozenset({"2wd"})

check("policy: the rule is on; config-tuple option columns are listed per site",
      policy.LIKELY_DRIVE_RULE and NPD in policy.DRIVE_CONFIG_FVO_SITES and SPD in policy.DRIVE_CONFIG_FVO_SITES
      and GM not in policy.DRIVE_CONFIG_FVO_SITES)

# ------------------------------------------------------------ drive words
check("drive words: codes and phrases",
      C._drive_terms("*KC. 4WD. LE")[0] == {"4wd"} and C._drive_terms("2WD")[0] == {"2wd"}
      and C._drive_terms("Four-Wheel Drive")[0] == {"4wd"} and C._drive_terms("Front-Wheel Drive")[0] == {"fwd"}
      and C._drive_terms("4x2")[0] == {"2wd"} and C._drive_terms("VR6 4Motion")[0] == {"awd"}
      and C._drive_terms("4 Motion")[0] == {"awd"} and C._drive_terms("a4_quattro".replace("_", " "))[0] == {"awd"}
      and C._drive_terms("1500_4wd".replace("_", " "))[0] == {"4wd"})
check("drive words: '2 or 4 wheel drive' and '4x2 or 4x4' name both families",
      C._drive_terms("W/2 OR 4 WHEEL DRIVE")[0] == {"2wd", "4wd"} and C._drive_terms("4x2 or 4x4")[0] == {"2wd", "4wd"})
check("drive words: not a drive (glass size 6-1/4x4-3/4, 4 wheel disc / ABS, model names)",
      C._drive_terms("(6-1/4x4-3/4)")[0] == set() and C._drive_terms("With 4 Wheel Disc")[0] == set()
      and C._drive_terms("with 4-wheel ABS")[0] == set() and C._drive_terms("Frontier")[0] == set())
check("drive words: negation", C._drive_terms("Without AWD")[1] == {"awd"} and not C._drive_terms("Without AWD")[0])
check("allowed: one family is a limit, both families are none",
      C._drive_allowed({"4wd"}, set()) == FOUR and C._drive_allowed({"2wd", "4wd"}, set()) is None
      and C._drive_allowed(set(), {"awd"}) == C._TWO and C._drive_allowed(set(), set()) is None)
check("labels", C._drive_label(FOUR) == "4WD" and C._drive_label(TWO) == "2WD"
      and C._drive_label({"awd"}) == "AWD" and C._drive_label({"4wd", "awd"}) == "4WD/AWD"
      and C._drive_label(C._TWO) == "2WD" and C._drive_label({"fwd"}) == "FWD")

# ------------------------------------------------------------ rows
check("nissan: every configuration 4WD -> 4WD (the verifier's G07 24810-EA101)",
      C._row_drive([F + "*KC. 4WD. LE + *CC. 4WD. LE"], NPD) == FOUR
      and C._row_drive([F + "*W. 4WD. SE"], NPD) == FOUR and C._row_drive([F + "*KC. 2WD. XE, *CC. 2WD. SE"], NPD) == TWO)
check("nissan: a configuration without a drive code fits any drive; both drives are no limit",
      C._row_drive([F + "*KC. 4WD. LE, *CC. LE"], NPD) is None
      and C._row_drive([F + "*KC. 4WD. LE + *KC. 2WD. LE"], NPD) is None and C._row_drive([], NPD) is None)
check("subaru: S.2WD.(L+LS) +SW.2WD.(L+LS) -> 2WD; S.L +S.4WD.TURBO -> none",
      C._row_drive([F + "S.2WD.(L+LS) +SW.2WD.(L+LS)"], SPD) == TWO
      and C._row_drive([F + "S.L +S.4WD.TURBO +SW"], SPD) is None)
check("mopar: a 4WD line code with body codes -> 4WD; 2WD + 4WD line codes -> none",
      C._row_drive([F + "41 - SEDAN/QUAD CAB SWB, 6 - Lt. Duty DODGE 4WD, 61 - REG CAB 6.5 FT BOX"], JPD) == FOUR
      and C._row_drive([F + "1 - Lt. Duty DODGE 2WD, 31 - CLUB CAB 2-DR, 5 - Lt. Duty DODGE 4WD"], JPD) is None)
check("mopar: a brand code without a drive word leaves the drive open; an AWD brand code alone limits",
      C._row_drive([F + "48 - SEDAN TYPE #8, C - CHRYSLER, F - BRAND AWD"], MPG) is None
      and C._row_drive([F + "D - DODGE, E - DODGE AWD"], MPG) is None
      and C._row_drive([F + "49 - HATCHBACK TYPE #2, E - DODGE AWD"], MPG) == frozenset({"awd"}))
check("mopar: a mirror glass size is no drive",
      C._row_drive(["MIRROR ASSEMBLY, Black, (6-1/4x4-3/4) , Right"], MPG) is None)
check("ford: option values name the drive",
      C._row_drive([F + "4 Cyl 2.3L TIVCT DI TC, 6 Cyl 3.5L Cyclone Petrol TIVCT, Front-Wheel Drive (Left Hand Drive)"],
                   FPG) == frozenset({"fwd"})
      and C._row_drive([F + "Four-Wheel Drive"], FPG) == FOUR)
check("free text: 'Sedan, FWD' -> FWD; 'Without AWD' -> 2WD; alternatives without a drive -> none",
      C._row_drive(["Sedan, FWD"], VW) == frozenset({"fwd"}) and C._row_drive(["2009-2012, Without AWD"], VW) == C._TWO
      and C._row_drive(["Sedan, FWD;Wagon"], VW) is None)
check("free text: a drive inside other words is ambiguous (Ford indicator list)",
      C._row_drive(["4x4 Hi & Lo - IND#194 / Antitheft warning - IND#194"], FPG) == C.DRIVE_AMBIGUOUS)
check("page variant: the 1500_4wd page limits a bare row; a conflicting note is ambiguous",
      C._row_drive([], GM, frozenset(), "1500_4wd") == FOUR
      and C._row_drive(["Sedan, FWD"], VW, None, "awd") == C.DRIVE_AMBIGUOUS)

# ------------------------------------------------------------ GM series
check("gm series letters: truck heads only",
      C._gm_series_letters("CK1,2,3(LM7,LQ4)") == frozenset("CK") and C._gm_series_letters("K107(06)(DR4,Z75)") == {"K"}
      and C._gm_series_letters("K207(53)(L29), CK209(03-53)(L29)") == frozenset("CK")
      and C._gm_series_letters("UM,UT") is None and C._gm_series_letters("U(DR5)") is None)
check("gm: one series of a pair limits (T1 = 4WD, C1 = 2WD, M1 = RWD); both series fit both",
      C._row_drive([F + "T1(06-16)(EXC T89)"], GM, frozenset("ST")) == FOUR
      and C._row_drive([F + "C1(03-53)(JC5)"], GM, frozenset("CK")) == TWO
      and C._row_drive([F + "M1"], GM, frozenset("LM")) == frozenset({"rwd"})
      and C._row_drive([F + "CK1,2(53-03)(LM7)"], GM, frozenset("CK")) is None)
check("gm: a both-series code overrides the drive the page is filed under (ST1 on the 2wd page)",
      C._row_drive([F + "ST1(06-36)(CJ2)(EXC EC0)"], GM, frozenset("ST"), "2wd") is None
      and C._row_drive([F + "LM1(6L8)"], GM, frozenset("LM"), "2wd") is None
      and C._row_drive([F + "U(DR5)"], GM, frozenset(), "awd") == frozenset({"awd"}))
check("gm: an unknown letter split narrower than the page leaves the year out (Savana H1 beside G1)",
      C._row_drive([F + "H1(KG3)"], GM, frozenset("GH")) == C.DRIVE_AMBIGUOUS
      and C._row_drive([F + "GH1,2(LM7,K68)"], GM, frozenset("GH")) is None)


# ------------------------------------------------------------ fitment rows
def fr(trims, layout="trim", options=(), tfo=False):
    return A.FitRow(idx=0, lo=2005, hi=2009, make="Chevrolet", model="Equinox", trims=list(trims), engines=[],
                    options=list(options), layout=layout, raw="", trims_from_options=tfo)


check("fitment: every trim naming one drive limits; a trim without a drive or both drives does not",
      C._fit_drive(fr(["SUV AWD", "SUV LT AWD"])) == frozenset({"awd"})
      and C._fit_drive(fr(["SUV AWD", "SUV FWD"])) is None
      and C._fit_drive(fr(["CROSSOVER SPORT VAN EXTENDED", "CROSSOVER SPORT VAN EXTENDED AWD"], tfo=True)) is None
      and C._fit_drive(fr(["4Matic", "Base"])) is None)
check("fitment: option-layout values (Ford) name the drive",
      C._fit_drive(fr([], "option", ["5-Speed Automatic", "Four-Wheel Drive"])) == FOUR
      and C._fit_drive(fr([], "option", ["Four-Wheel Drive", "Rear-Wheel Drive"])) is None
      and C._fit_drive(fr([], "option", ["5-Speed Automatic"])) is None)

# ------------------------------------------------------------ union + note
check("union: an unrestricted row wins; an ambiguous row (none unrestricted) is ambiguous; families merge",
      C._drive_union([FOUR, None]) is None and C._drive_union([FOUR, C.DRIVE_AMBIGUOUS]) == C.DRIVE_AMBIGUOUS
      and C._drive_union([FOUR, FOUR]) == FOUR and C._drive_union([FOUR, TWO]) is None)


class _Cur:
    _drive_note = C.Curation._drive_note


cur = _Cur()
check("note: one limit for every app -> '4WD only'",
      cur._drive_note({("Nissan", "Frontier", 2005): FOUR, ("Nissan", "Xterra", 2005): FOUR}) == "4WD only")
check("note: per model, with years when only some are limited",
      cur._drive_note({("Nissan", "Frontier", 2005): FOUR, ("Nissan", "Frontier", 2006): FOUR,
                       ("Nissan", "Xterra", 2005): None}) == "Frontier: 4WD only"
      and cur._drive_note({("Nissan", "Frontier", 2005): FOUR, ("Nissan", "Frontier", 2006): None,
                           ("Nissan", "Xterra", 2005): None}) == "Frontier 2005: 4WD only"
      and cur._drive_note({("Nissan", "Frontier", 2005): None, ("Nissan", "Xterra", 2005): None}) == "")
check("note length: the uncut note must fit, or the group is refused (the old test compared the cut note)",
      not C._likely_note_fits("Nissan", "24810-EA101", "x" * 200)
      and C._likely_note_fits("Nissan", "24810-EA101", "option: fits some option packages; 4WD only"))
done("test_drive")
