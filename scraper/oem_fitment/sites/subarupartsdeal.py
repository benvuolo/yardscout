"""www.subarupartsdeal.com: Subaru on the PartsGiant ".html" template.

Learned through fetch.py (2026-11-05, 2001 Forester, 2003/2011 Outback,
2011 Legacy):
  * one catalog page per model-year, no trim split; Legacy and Outback share
    diagrams, and each list row carries "Fitting Vehicle Options" codes
    (S = sedan, W/OBK = wagon/Outback, engine codes 253/255/36D/EJ25#, trim
    codes 25I/25IP/36RL...). Those codes are kept verbatim in list_info.
  * Subaru prints the OEM name in mainDesc ("Lamp Assembly-Head Left",
    "Bumper Face-Front", "Panel-Rear Gate"); paint variants append
    "(COLOR NAME)" and carry their own part number.
  * Tail lamps: up to ~2009 "Lamp Assembly-Rear Combination ..."; 2010+
    "Lens & Body-Rear Combination Lamp ..." is the housing sold as the lamp
    (no separate assembly number is listed). Both are kept; the name says
    which. "Rear Finisher" lamps (liftgate-mounted inner lamps) are excluded.
  * Fuel pump: "Pump Assembly-Fuel" is the in-tank module; "Pump-Fuel" is the
    bare pump inside it (excluded).
"""
from __future__ import annotations

import re

from sites import _partsgiant as T
from sites._partsgiant import M

SITE = "www.subarupartsdeal.com"

# feed model -> catalog model slug (worklist.json names; others: T.slug(model))
MODELS = {
    ("Subaru", "B9 Tribeca"): M("tribeca"),       # /2006-subaru-b9_tribeca-parts.html is a 404; 2006 is under tribeca
    ("Subaru", "Legacy Wagon"): M("legacy"),      # one Legacy catalog per year (sedan + wagon rows)
    ("Subaru", "Impreza Wagon"): M("impreza"),
}

# our category -> regex on the <subcategory> slug of the year catalog's parts-list links
SUBCATS = {
    "alternator": r"^alternator$",
    "starter": r"^starter$",
    "ac-compressor": r"^compressor$",
    "headlights": r"^head_lamp$",
    "tail-lights": r"^lamp_rear$",
    "side-mirrors": r"^rear_view_mirror$",
    "window-regulator": r"^(front_|rear_)?door_parts_glass_regulator$",
    "window-switch": r"^switch_power_window$",
    "climate-control": r"^heater_control$",
    "fuel-pump-module": r"^fuel_tank$",
    "throttle-body": r"^(throttle_chamber|intake_manifold)$",
    "power-steering-pump": r"^oil_pump$",      # steering section; engine/AT pumps are oil_pump_filter / automatic_transmission_oil_pump
    "gauge-cluster": r"^meter$",
    "ignition-coils": r"^spark_plug_high_tension_cord$",
    "radiator": r"^engine_cooling$",
    "door-front": r"^(front_door_panel_rear_or_slide_door_panel|front_door_panel)$",
    "door-rear": r"^(front_door_panel_rear_or_slide_door_panel|rear_door_panel)$",
    "hood": r"^front_hood_front_hood_lock$",
    "fender": r"^fender$",
    "bumper-front": r"^front_bumper$",
    "bumper-rear": r"^rear_bumper$",
    "grille": r"^front_grille$",
    "trunk-lid": r"^trunk_fuel_parts$",
    "liftgate": r"^back_door_panel$",
}

A = r"(?:assembly|assy|complete)"
RULES = {
    "alternator": (rf"^alternator\s+{A}\b", r"brush|bushing|bearing|cover|diode|pulley|regulator|rotor|stator|plate|kit"),
    "starter": (rf"^starter(\s+motor)?\s+{A}\b", r"armature|housing|yoke|gear|lever|clutch|brush|switch|plate|cover|kit"),
    "ac-compressor": (rf"^compressor\s+{A}\b", r"clutch|pulley|valve|switch|sensor|kit|coil|magnet"),
    "headlights": (rf"^(lamp\s+{A}-head|head\s*lamp\s+{A})\b", r"cover|boot|lens|leveling|level|actuator|ballast|unit-|socket|bezel|garnish|holder|washer|cleaner"),
    "tail-lights": (rf"^lamp\s+{A}-rear\s+combination|^lens\s*&\s*body-rear\s+combination|^rear\s+combination\s+lamp\s+{A}",
                    r"cover|packing|spacer|finisher|reflector|socket|cap"),
    "side-mirrors": (rf"^mirror\s+{A}-(door|outer)|^door\s+mirror\s+(unit|{A})|^outer\s+mirror\s+{A}",
                     r"repair|cover|cap|glass|lamp|motor|actuator|garnish|inner|inside|switch"),
    "window-regulator": (rf"^regulator\s+(&\s*motor\s+)?{A}|^regulator\s+complete|^motor\s+{A}-(regulator|power\s+window)|^power\s+window\s+motor",
                         r"glass|weather|sash|switch|handle|cable|gear|cover|guide|slider|channel|holder"),
    "window-switch": (rf"^switch-power\s+window\s+main|^switch\s+{A}-power\s+window\s+main|^power\s+window\s+main\s+switch",
                      r"sub|bezel|panel|cover|knob|lamp"),
    "climate-control": (rf"^heater\s+control\s+{A}|^control\s+{A}-(heater|air\s+conditioner|auto\s+air)|^air\s+conditioner\s+control\s+{A}",
                        r"cable|case|circuit|knob|lamp|lens|sensor|switch|electronics|unit|panel"),
    "fuel-pump-module": (rf"^pump\s+{A}-fuel|^fuel\s+pump\s+{A}",
                         r"filter|level|sensor|sender|band|cover|plate|holder|chamber|retainer|tube|regulator|valve"),
    "throttle-body": (rf"^chamber\s+(and\s+sensor\s+)?{A}-(electric\s+)?throttle|^throttle\s+(body|chamber)\s+{A}|^chamber\s+complete-throttle",
                      r"sensor\s+{A}|sensor\s+set|gasket|spacer|valve"),
    "power-steering-pump": (rf"^pump-power\s+steering|^power\s+steering\s+pump|^(oil\s+)?pump\s+{A}-(power\s+steering|oil)|^oil\s+pump\s+{A}$",
                            r"connector|ring|pulley|reservoir|tank|cap|hose|bracket|kit"),
    "gauge-cluster": (rf"^meter-main\s+{A}|^combination\s+meter\s+{A}|^meter\s+{A}-combination",
                      r"glass|visor|case|circuit|plate|panel|knob|reflector|window"),
    "ignition-coils": (rf"^coil\s+{A}-ignition|^ignition\s+coil(\s+{A})?\b|^coil-ignition",
                       r"cord|boot|plug|sensor|hanger"),
    "radiator": (rf"^radiator\s+{A}$|^radiator$",
                 r"cap|plug|shroud|fan|motor|reserve|tank|hose|cushion|bracket"),
    "door-front": (rf"^panel\s+{A}-front\s+door|^front\s+door\s+panel\s+{A}",
                   r"pad|inner|outer|sash|hinge|checker|weather|trim|glass|seal"),
    "door-rear": (rf"^panel\s+{A}-rear\s+door|^rear\s+door\s+panel\s+{A}",
                  r"pad|inner|outer|sash|hinge|checker|weather|trim|glass|seal|partition"),
    "hood": (rf"^hood\s+{A}(-front)?\b|^panel\s+{A}-front\s+hood|^front\s+hood\s+{A}",
             r"hinge|lock|cable|buffer|stay|striker|protector|insulator|seal|cover"),
    "fender": (rf"^fender\s+{A}-front|^fender-front|^front\s+fender\s+{A}",
               r"liner|cover|protector|mudguard|seal|garnish|molding|bracket"),
    "bumper-front": (r"^bumper[-\s]+face[-,\s]+front|^face-front\s+bumper|^front\s+bumper\s+face",
                     r"beam|absorber|cover|grille|garnish|molding|bracket|lower|lip|spoiler"),
    "bumper-rear": (r"^bumper[-\s]+face[-,\s]+rear|^face-rear\s+bumper|^rear\s+bumper\s+face",
                    r"beam|absorber|cover|garnish|molding|bracket|lower|lip|spoiler|step"),
    "grille": (rf"^front\s+grille\s+{A}|^grille\s+{A}-front|^grille-front$|^front\s+grille$",
               r"emblem|ornament|molding|duct|garnish|mesh|lower|bracket"),
    "trunk-lid": (rf"^trunk\s+lid\s+{A}|^lid\s+{A}-trunk|^panel\s+{A}-trunk\s+lid",
                  r"hinge|lock|cable|stay|striker|stopper|handle|trim|spoiler|garnish|seal"),
    "liftgate": (rf"^panel(\s+{A})?-rear\s+gate|^panel(\s+{A})?-back\s+door|^rear\s+gate\s+panel|^back\s+door\s+panel",
                 r"hinge|stopper|trim|glass|garnish|spoiler|lock|handle|stay|weather|lamp|wiper"),
}


# excludes match at a word start ("ring" must not hit "steering")
RULES = {k: (re.compile(inc, re.I), re.compile(rf"\b(?:{exc})", re.I)) for k, (inc, exc) in RULES.items()}
# "With X" / "W/X" / "Less X" qualifiers describe what an assembly includes
QUALIFIER = re.compile(r"\b(?:w/o|w/|l/|with(?:out)?|less|incl(?:udes|uding)?)\s*[a-z0-9]+", re.I)


def name_of(row: dict) -> str:
    """The OEM name the catalog prints for the row (Subaru: mainDesc)."""
    return row["main"]


def head(row: dict) -> str:
    return QUALIFIER.sub(" ", name_of(row))


def _rule(cat: str):
    inc, exc = RULES[cat]
    return lambda row, text: bool(inc.search(name_of(row))) and not exc.search(head(row))


PARTS = {cat: _rule(cat) for cat in RULES}

# the "Important vehicle option details" column prints Subaru trims ("2.5i Limited")
CFG = T.Config(site=SITE, models=MODELS, subcats=SUBCATS, parts=PARTS, head_fn=head,
               option_column_is_trims=True)
categories_for, parts_on_page, product = T.bind(CFG)
