"""www.fordpartsgiant.com: Ford, Lincoln, Mercury on the PartsGiant ".html"
template.

Ford part numbers are PREFIX-BASE-SUFFIX (9L8Z-10346-A); body parts carry a
two-digit body code before the base (8L8Z-7823201-A = 78 + 23201). The base
number is Ford's own part-type code, so the category rules match on it
(BASE below, verified on 2010 Escape list pages 2026-11-05) and use names only
to drop sub-assemblies. Service/reman numbers put a V in the base (10V346);
those rows are matched too and then dropped by the template whenever the page
also lists a new number. List-page info carries the description
(": 150 AMP , Motorcraft , New"), "Location: Driver Side", "Fit Note",
"Production Date". The product page's option column holds drivetrain options,
not trims, so fitment[].trims stays empty and fitment[].options keeps them.

Ford's catalog splits some years by variant: escape/mariner "gas"/"hybrid"
(2005-2012), f_150 2004 "f_150_new_style"/"f_150_heritage_old_style", focus
2016-2018 "front_wheel_drive"/"all_wheel_drive_rs".
"""
import re

from sites import _partsgiant as T
from sites._partsgiant import M

SITE = "www.fordpartsgiant.com"

MODELS = {
    ("Ford", "F-150"): M("f_150", exc=r"heritage", pref=r"new_style"),
    ("Ford", "F-150 Heritage"): M("f_150", inc=r"heritage|^$"),
    ("Ford", "F-250"): [M("f_250", years=(1980, 1998)), M("f_250_super_duty", years=(1999, 2030))],
    ("Ford", "F-350"): [M("f_350", years=(1980, 1998)), M("f_350_super_duty", years=(1999, 2030))],
    ("Ford", "E-350"): M("e_350_e_350_super_duty"),
    ("Ford", "E-350 Super Duty"): M("e_350_e_350_super_duty"),
    ("Ford", "Econoline"): M("e_150"),
    ("Ford", "Escape Hybrid"): M("escape", inc=r"hybrid|^$"),
    ("Ford", "Fusion Hybrid"): M("fusion"),
    ("Ford", "Expedition EL"): M("expedition"),
    ("Ford", "Focus"): M("focus", exc=r"_rs$"),
    ("Mercury", "Mariner"): M("mariner", exc=r"hybrid"),
}

# Parts-list subcategory slugs that hold each category.
SUBCATS = {
    "alternator": r"alternator",
    "starter": r"starter",
    "ac-compressor": r"compressor",
    "headlights": r"headlamp",
    "tail-lights": r"rear_lamp|tail_?lamp|rear_combination",
    "side-mirrors": r"mirror",
    "window-regulator": r"door_glass|window_control|window_regulator",
    "window-switch": r"front_door_glass|window_control|^switches$",
    "climate-control": r"heater.*controls?|air_cond.*controls?|climate_control",
    "fuel-pump-module": r"fuel_pump|fuel_tank|sender",
    "throttle-body": r"throttle",
    "power-steering-pump": r"power_steering|steering_pump",
    "gauge-cluster": r"instrument_cluster|cluster",
    "ignition-coils": r"ignition",
    "radiator": r"radiator",
    "door-front": r"front_door",
    "door-rear": r"rear_door|cargo_door|side_door",
    "hood": r"hood",
    "fender": r"fender",
    "bumper-front": r"front_bumper|bumper_front|grille_and_front",
    "bumper-rear": r"rear_bumper|bumper_rear",
    "grille": r"grille",
    "trunk-lid": r"luggage_compartment|deck_lid|trunk",
    "tailgate": r"tail_?gate|pick_up_box|pickup_box",
    "liftgate": r"luggage_compartment_door|lift_?gate|back_door|tail_?gate",
    # tier C (§8): subs from the R2 years manifest (sedans: front_knuckle_and_hub,
    # front_suspension_struts_and_springs; trucks/older: front_suspension, rear_suspension)
    "wiper-motor": r"wiper",
    "knuckle": r"knuckle|spindle|^(front|rear)_suspension$|^front_rear_suspension$",
    "strut": r"strut|shock|^(front|rear)_suspension$|^front_rear_suspension$",
    # tier W (ops/interchange.md "Wheels"): chassis/wheels and
    # wheels_brakes/wheels_related_parts, as the oem-raw years manifest lists them
    "wheels": r"^wheels(_related_parts)?$",
}
SUBCAT_EXCL = {
    "side-mirrors": r"inside",
    "door-front": r"trim|glass|lock|handle|speaker|weather_?strip_only",
    "door-rear": r"trim|glass|lock|handle|speaker",
    "trunk-lid": r"trim|lock",
    "liftgate": r"trim|lock",
    "wiper-motor": r"switch|control",
    "strut": r"hood|lift_?gate|tail_?gate|luggage|trunk|engine|motion|transmission|damper_control",
}

# Ford base numbers per category (regex on the base after any body code).
BASE = {
    "alternator": r"10V?346",
    "starter": r"11V?002",
    "ac-compressor": r"19V?703",
    "headlights": r"13008|13W029|13W030",
    "tail-lights": r"13404|13405|13B504|13B505",
    "side-mirrors": r"17682|17683",
    "window-regulator": r"23200|23201|27000|27001|23394|23395|23208|23209",
    "window-switch": r"14529|14540",
    "climate-control": r"19980",
    "fuel-pump-module": r"9H307",
    "throttle-body": r"9E926",
    "power-steering-pump": r"3A674|3A696",
    "gauge-cluster": r"10849",
    "ignition-coils": r"12029|12A366",
    "radiator": r"8005",
    "door-front": r"20124|20125",
    "door-rear": r"24630|24631",
    "hood": r"16612",
    "fender": r"16005|16006",
    "bumper-front": r"17D957|17757",
    "bumper-rear": r"17K835|17906",
    "grille": r"8200|8150",
    "trunk-lid": r"40110",
    "tailgate": r"40700",
    "liftgate": r"40010",
    # tier C, bases read on the 2026-11-09 trial pages (F-150, F-250 Super Duty):
    # 17508 "Motor Assy - Wiper"; 3K185/3K186 "Knuckle - Front Wheel", 3105/3106
    # "Spindle" (truck knuckles); 18124 front / 18125 rear "Shock Absorber Assy",
    # 18A092 "Strut - Loaded Assembly". No rear knuckle base was seen: none taken.
    "wiper-motor": r"17508",
    "knuckle": r"3K185|3K186|3105|3106",
    "strut": r"18V?124|18V?125|18A092",
    "wheels": r"1007",
}
# Names that are never the assembly even when the base matches.
NAME_EXCL = re.compile(r"\b(Glass|Lens|Bulb|Bezel|Cover - Mirror|Gasket|Seal|Kit - Seal|Pulley|Clutch|"
                       r"Bracket|Moulding|Applique|Emblem|Reinforcement|Support|Absorber|Isolator)\b", re.I)

# strut rows are "Shock Absorber Assy" (NAME_EXCL drops "Absorber"); mounts,
# insulators, brackets and bushing kits share the page
STRUT_EXCL = re.compile(r"\b(Insulator|Bracket|Bushing|Mount|Mounting|Repair|Boot|Bumper|Seat|Spring - |Nut|Bolt)\b", re.I)
WHEEL_EXCL = re.compile(r"\b(?:cap|cover|nut|bolt|stud|lock|weight|valve|sensor|ornament|emblem|insert|spare|temporary|compact|carrier|bearing|hub|kit|liner|flare|opening|molding|moulding|trim|balance|tire)", re.I)


def _base(pn: str) -> str:
    parts = pn.strip("-").split("-")
    return parts[1] if len(parts) >= 3 else ""


def _rule(cat: str):
    rx = re.compile(r"^(?:\d{2})?(?:%s)$" % BASE[cat], re.I)

    def rule(r: dict, text: str) -> bool:
        return why(r, text) is None

    def why(r: dict, text: str) -> str | None:
        """None when kept, else the manifest reason (template `.why` hook)."""
        if not rx.match(_base(r["pn"])):
            return "include_miss"
        m = (STRUT_EXCL if cat == "strut" else NAME_EXCL).search(f"{r['group']} | {r['main']}")
        if m:
            return f"rule:{m.group(0).lower()}"
        if cat == "wheels":
            # wheel assemblies only: no spare / temporary / compact wheel,
            # cap, cover, nut, lock, weight, valve or TPMS sensor
            m = WHEEL_EXCL.search(f"{r['group']} | {r['main']} | {r.get('remark') or ''}")
            if m:
                return f"rule:{m.group(0).lower()}"
        if cat == "window-switch":
            # driver master switch only: not the passenger/rear single switch
            m = re.search(r"Single|Location: Passenger Side(?!/)|Location: Rear|\bRear\b", text)
            if m:
                return f"rule:{m.group(0).lower()}"
        return None
    rule.why = why
    return rule


PARTS = {cat: _rule(cat) for cat in BASE}

CFG = T.Config(site=SITE, models=MODELS, subcats=SUBCATS, subcat_excl=SUBCAT_EXCL, parts=PARTS,
               option_column_is_trims=False)
categories_for, parts_on_page, product = T.bind(CFG)
# R1/R2/R4 manifests (README "Site module contract"), re-read from the cache
year_manifest, list_manifest, chain_links = T.bind_manifests(CFG)
