"""www.lexuspartsnow.com: Lexus on the PartsGiant ".html" template.

Learned through fetch.py (2026-11-05, 2002 ES300, 2000 RX300):
  * one catalog page per model-year (/<year>-lexus-<model>-parts.html), no
    trim split. Model slugs drop the space: "ES 300" -> es300, "GS F" -> gs_f.
    The feed's bare series names ("IS", "GS", "ES", "RX", "LS") name no
    catalog model (/2007-lexus-is-parts.html is a 404) and are not guessed.
  * list rows print the Toyota EPC name in mainDesc ("Unit Assy, Headlamp,
    RH", "Mirror Sub-Assy, Outer Rear View, LH"). Product pages put an SEO
    name in mainDesc ("Alternator Compatible") and the EPC name in subDesc,
    so classification uses the list name only.
  * COMMON_EXCLUDE has TUBES?: "Tube Assy, Fuel Suction" (Toyota's in-tank pump
    module) is shown to it as "Fuel suction module" (head()), nothing else.
  * fitment columns: Year Make Model | Trim & Engine | Important vehicle
    option details (the "Trim & Engine" cell holds the engine, e.g.
    "6 Cyl 3.0L"; option details hold engine code; model code).
  * paint variants carry their own part number suffix (87901-33070-A0 ...);
    each is its own record.
  * Outside mirrors on Lexus are sold as "Mirror Sub-Assy, Outer Rear View"
    (the painted head with glass and motor); kept. "Outer Mirror"/"Mirror
    Outer" (glass) is excluded.
  * Tail lamps: "Lens, Rear Combination Lamp" alone is excluded (README: lens
    only); "Lamp Assy, Rear Combination" and "Lens & Body" are kept.
"""
from __future__ import annotations

import re

from sites import _partsgiant as T
from sites._partsgiant import M

SITE = "www.lexuspartsnow.com"

# worklist.json model -> catalog slug ("ES 300" -> es300). The bare series names
# in the worklist ("ES", "GS", "IS", "LS", "RX") name no catalog model
# (/2007-lexus-is-parts.html is a 404); they are left unmapped, so navigation
# fails for them and crawl.py logs a nav-fail. Nothing is guessed.
MODELS = {
    ("Lexus", "ES 300"): M("es300"),
    ("Lexus", "ES 330"): M("es330"),
    ("Lexus", "ES 350"): M("es350"),
    ("Lexus", "GS 300"): M("gs300"),
    ("Lexus", "GS 350"): M("gs350"),
    ("Lexus", "GS 400"): M("gs400"),
    ("Lexus", "GS 430"): M("gs430"),
    ("Lexus", "IS 250"): M("is250"),
    ("Lexus", "IS 300"): M("is300"),
    ("Lexus", "IS 350"): M("is350"),
    ("Lexus", "LS 400"): M("ls400"),
    ("Lexus", "LS 430"): M("ls430"),
    ("Lexus", "LS 460"): M("ls460"),
    ("Lexus", "RX 300"): M("rx300"),
    ("Lexus", "RX 330"): M("rx330"),
    ("Lexus", "RX 350"): M("rx350"),
    ("Lexus", "RX 400h"): M("rx400h"),
    ("Lexus", "SC 400"): M("sc400"),
    ("Lexus", "SC 430"): M("sc430"),
}

# our category -> regex on the <subcategory> slug of the year catalog's parts-list links
SUBCATS = {
    "alternator": r"^alternator$",
    "starter": r"^starter$",
    "ac-compressor": r"^heating_air_conditioning_compressor$",
    "headlights": r"^headlamp$",
    "tail-lights": r"^rear_combination_lamp$",
    "side-mirrors": r"^mirror$",
    "window-regulator": r"^(front|rear)_door_window_regulator_hinge$",
    "window-switch": r"^switch_relay_computer$",
    "climate-control": r"^heating_air_conditioning_control_air_duct$",
    "fuel-pump-module": r"^fuel_tank_tube$",
    "throttle-body": r"^fuel_injection_system$",
    "power-steering-pump": r"^vane_pump_reservoir_power_steering$",
    "gauge-cluster": r"^meter$",
    "ignition-coils": r"^ignition_coil_spark_plug_glow_plug$",
    "radiator": r"^radiator_water_outlet$",
    "door-front": r"^front_door_panel_glass$",
    "door-rear": r"^rear_door_panel_glass$",
    "hood": r"^hood_front_fender$",
    "fender": r"^hood_front_fender$",
    "bumper-front": r"^front_bumper_bumper_stay$",
    "bumper-rear": r"^rear_bumper_bumper_stay$",
    "grille": r"^radiator_grille$",
    "trunk-lid": r"^luggage_compartment_door_lock$",
    "liftgate": r"^back_door_panel_glass$",
    # tier W (ops/interchange.md "Wheels"): the years manifest lists it
    "wheels": r"^disc_wheel_wheel_cap$",
}

A = r"(?:assy|assembly)"
RULES = {
    "alternator": (rf"^alternator\s+{A}\b", r"pulley|brush|bearing|frame|cover|rotor|coil|stator|plate|holder|rectifier|terminal|kit"),
    "starter": (rf"^starter\s+{A}\b", r"kit|frame|yoke|armature|gear|clutch|lever|holder|brush|plate|cover|switch|bearing"),
    "ac-compressor": (rf"^compressor\s+{A}\b", r"clutch|valve|switch|sensor|kit|coil|magnet|pulley|head"),
    "headlights": (rf"^unit\s+{A},?\s*headlamp|^headlamp\s+(unit\s+)?{A}|^lamp\s+{A},?\s*headlamp",
                   r"protector|retainer|cover|leveling|level|adjust|lens|ballast|computer|module|actuator|bezel|garnish|cleaner|washer|igniter|bulb"),
    "tail-lights": (rf"^lamp\s+{A},?\s*(rear\s+combination|tail)|^lens\s*(&|and)\s*body,?\s*rear\s+combination|^rear\s+combination\s+lamp\s+{A}",
                    r"cord|guide|cover|gasket|reflector|socket"),
    "side-mirrors": (rf"^mirror\s+(sub-)?{A},?\s*outer\s+rear\s*view|^outer\s+rear\s*view\s+mirror\s+(sub-)?{A}",
                     r"glass|cover|cap|switch|computer|motor|actuator|lamp|heater|visor"),
    "window-regulator": (rf"^regulator\s+(sub-)?{A},?\s*(front|rear|fr|rr)\s+door\s+window|^regulator\s+{A},?\s*(front|rear|fr|rr)\s+door,?\s*power|^motor\s+{A},?\s*power\s+window",
                         r"switch|handle|channel|run|glass|cable|cover|gear|guide|stopper|hinge"),
    "window-switch": (rf"^master\s+switch\s+{A},?\s*power\s+window|^switch\s+{A},?\s*power\s+window\s+regulator\s+master",
                      r"bezel|panel|cover|base|knob|lamp"),
    "climate-control": (rf"^control\s+{A},?\s*(air\s+conditioner|heater)|^control\s+sub-{A},?\s*heater|^switch\s+{A},?\s*air\s+conditioner\s+control",
                        r"base|knob|cable|amplifier|bezel|button|lever|sensor|lamp|valve|motor|servo|damper|housing|duct"),
    "fuel-pump-module": (rf"^tube\s+{A},?\s*fuel\s+suction|^pump\s+{A},?\s*fuel\b|^fuel\s+suction\s+tube\s+{A}",
                         r"plate|support|filter|gage|gauge|sender|band|protector|regulator|cushion"),
    "throttle-body": (rf"^body\s+{A},?\s*throttle|^throttle\s+body\s+{A}",
                      r"hose|cable|cover|sensor|spacer|gasket"),
    "power-steering-pump": (rf"^pump\s+{A},?\s*vane|^vane\s+pump\s+{A}",
                            r"kit|reservoir|pulley|cap|shaft|housing|ring|cover"),
    "gauge-cluster": (rf"^meter\s+{A},?\s*combination|^combination\s+meter\s+{A}",
                      r"glass|lens|bezel|mask|hood|cover|circuit|plate|panel|case"),
    "ignition-coils": (rf"^coil\s+{A},?\s*ignition|^coil,?\s*ignition|^ignition\s+coil\s+{A}",
                       r"boot|cord|cover|resistor|igniter"),
    "radiator": (rf"^radiator\s+{A}\b",
                 r"cap|support|hose|cushion|shroud|fan|reserve|tank|drain|cock"),
    "door-front": (rf"^panel\s+sub-{A},?\s*front\s+door,?\s*(lh|rh)\b",
                   r"outer|outside|trim|frame|board|silencer|service"),
    "door-rear": (rf"^panel\s+sub-{A},?\s*rear\s+door,?\s*(lh|rh)\b",
                  r"outer|outside|trim|frame|board|silencer|service"),
    "hood": (rf"^hood\s+(sub-)?{A}\b|^hood$",
             r"hinge|lock|latch|insulator|support|cable|protector|seal|cushion|garnish|molding|moulding"),
    "fender": (rf"^fender\s+sub-{A},?\s*front|^fender,\s*front\b",
               r"liner|protector|shield|splash|molding|moulding|flare|apron|extension|garnish|emblem|pad|cover|inner"),
    "bumper-front": (r"^cover,?\s*front\s+bumper\b",
                     r"hole|lower|extension|tow|hook|cap|grille|molding|moulding|absorber|reinforce|support|pad|spoiler|lip|strip|bezel|garnish|side|end\b"),
    "bumper-rear": (r"^cover,?\s*rear\s+bumper\b",
                    r"hole|lower|extension|tow|hook|cap|molding|moulding|absorber|reinforce|support|pad|spoiler|lip|strip|bezel|garnish|side|end\b|plate|step"),
    "grille": (rf"^grille,?\s*radiator\b|^grille\s+sub-{A},?\s*radiator|^radiator\s+grille\b",
               r"emblem|molding|moulding|lower|insert|bezel|retainer|support|garnish|plate|ornament|sensor|camera"),
    "trunk-lid": (rf"^panel\s+sub-{A},?\s*luggage\s+compartment\s+door|^door\s+sub-{A},?\s*luggage",
                  r"trim|cushion|weatherstrip|lock|hinge|torsion|garnish|spoiler|lamp|emblem|stay|molding|moulding|inner|outer"),
    "liftgate": (rf"^panel\s+sub-{A},?\s*back\s+door|^door\s+sub-{A},?\s*back|^back\s+door\s+(panel\s+)?sub-{A}",
                 r"handle|hinge|lock|glass|weather|stay|motor|spoiler|lamp|trim|garnish|emblem|outer|outside|inner|board|cover"),
    # tier W: Toyota naming "WHEEL, DISC" / "DISC WHEEL"; the same page also
    # carries caps, nuts and ornaments, and spare wheels are excluded
    "wheels": (rf"^wheel,?\s*disc\b|^disc\s+wheel\b|^wheel,?\s*(aluminum|alloy|steel)\b",
               r"cap|cover|nut|bolt|stud|lock|weight|valve|sensor|ornament|emblem|insert|spare|temporary|compact|carrier|bearing|hub|kit|balance|tire"),
}
# excludes match at a word start ("ring" must not hit "steering")
RULES = {k: (re.compile(inc, re.I), re.compile(rf"\b(?:{exc})", re.I)) for k, (inc, exc) in RULES.items()}
# "W/Cap" / "W/O Pulley" / "Less X" qualifiers describe what an assembly includes
# R5a (CURATION_SPEC §3.2): the whole qualifier phrase, to the next "," or ";",
# is removed before the exclusion checks (sites/_qualifier.py)
from sites._qualifier import QUALIFIER  # noqa: E402
FUEL_SUCTION = re.compile(r"^tube\s+(sub-)?(assy|assembly),?\s*fuel\s+suction", re.I)


def name_of(row: dict) -> str:
    """The EPC name the catalog prints for the row (mainDesc)."""
    return row["main"]


def head(row: dict) -> str:
    return FUEL_SUCTION.sub("Fuel suction module", QUALIFIER.sub(" ", name_of(row)))


def _rule(cat: str):
    inc, exc = RULES[cat]
    # include on the OEM name, exclusions on head(); .why gives the manifest reason
    return T.name_rule(inc, exc, name_of, head)


PARTS = {cat: _rule(cat) for cat in RULES}

# the "Important vehicle option details" column holds engine and model codes
# ("1MZFE; MCV30L-BEAGKA"), not trims: kept in fitment[].options only
CFG = T.Config(site=SITE, models=MODELS, subcats=SUBCATS, parts=PARTS, head_fn=head)
categories_for, parts_on_page, product = T.bind(CFG)
# R1/R2/R4 manifests (README "Site module contract"), re-read from the cache
year_manifest, list_manifest, chain_links = T.bind_manifests(CFG)
