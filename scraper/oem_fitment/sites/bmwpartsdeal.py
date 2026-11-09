"""www.bmwpartsdeal.com: BMW on the PartsGiant ".html" template (MINI not in scope).

Learned through fetch.py (2026-11-05, 2011 328i):
  * the model-year is split by submodel: /<year>-bmw-<model>-<variant>-parts.html,
    variant like sedan_n52_engine_e90, coupe_n51_engine_e92, wagon_e91,
    n20_engine_f30 (no body word). /<year>-bmw-<model>-parts.html is a 404;
    variants are read from the model page /bmw-<model>-parts.html.
    Picked (README "at most two trims per year"): sedan variants first (2011
    328i: sedan_n51_engine_e90 + sedan_n52_engine_e90, whose engine parts
    differ), else the template order (plain catalog, then page order);
    at most two per model-year.
  * list rows print BMW's English EPC name in mainDesc ("Exch. alternator",
    "Headlight left", "Exterior mirror w/o glass, heated, left").
    "Exch."/"Exchange" parts are BMW's remanufactured exchange units: marked
    reman. Product pages put a retail name in mainDesc ("Exchange Alternator")
    and the EPC name in subDesc.
  * product URL /parts/bmw-<slug>-<pn digits>.html; the page prints the pn
    with dashes (12-31-7-555-926). Fitment columns: Year Make Model | Submodel
    ("Sedan N52 Engine(E90), Wagon(E91)").
  * the sedan trunk lid is printed "Tailgate with hole for lock barrel" on the
    trunk-lid page; classification of trunk-lid vs liftgate is by page.
  * side mirrors are sold without glass ("w/o glass"); kept. Mirror glass,
    drives, cover caps and wiring are excluded.
"""
from __future__ import annotations

import re

from sites import _partsgiant as T
from sites._partsgiant import M

SITE = "www.bmwpartsdeal.com"

# Year catalogs are per submodel (body + engine + chassis code). Sedan variants
# first; then the template's order (plain catalog, then page order), e.g. 2015
# 328i has only "n20_engine_f30" / "n26_engine_f30". T.MAX_CATALOGS (2) caps
# the count per model-year.
SEDAN = r"^sedan"
# worklist.json model -> catalog slug. "3 Series", "5 Series", "7 Series" name no
# catalog model (no /bmw-3_series-parts.html); left unmapped, so navigation
# fails for them and crawl.py logs a nav-fail. Nothing is guessed.
MODELS = {
    ("BMW", "X1"): M("x1", pref=SEDAN),
    ("BMW", "X3"): M("x3", pref=SEDAN),
    ("BMW", "X5"): M("x5", pref=SEDAN),
    ("BMW", "Z3"): M("z3", pref=SEDAN),
    ("BMW", "Z4"): M("z4", pref=SEDAN),
    ("BMW", "128i"): M("128i", pref=SEDAN),
    ("BMW", "318i"): M("318i", pref=SEDAN),
    ("BMW", "320i"): M("320i", pref=SEDAN),
    ("BMW", "323i"): M("323i", pref=SEDAN),
    ("BMW", "325i"): M("325i", pref=SEDAN),
    ("BMW", "328i"): M("328i", pref=SEDAN),
    ("BMW", "328i xDrive"): M("328i_xdrive", pref=SEDAN),
    ("BMW", "330i"): M("330i", pref=SEDAN),
    ("BMW", "335i"): M("335i", pref=SEDAN),
    ("BMW", "525i"): M("525i", pref=SEDAN),
    ("BMW", "528i"): M("528i", pref=SEDAN),
    ("BMW", "530i"): M("530i", pref=SEDAN),
    ("BMW", "535i"): M("535i", pref=SEDAN),
    ("BMW", "535i xDrive"): M("535i_xdrive", pref=SEDAN),
    ("BMW", "540i"): M("540i", pref=SEDAN),
    ("BMW", "545i"): M("545i", pref=SEDAN),
    ("BMW", "550i"): M("550i", pref=SEDAN),
    ("BMW", "650i"): M("650i", pref=SEDAN),
    ("BMW", "740i"): M("740i", pref=SEDAN),
    ("BMW", "745i"): M("745i", pref=SEDAN),
    ("BMW", "750i"): M("750i", pref=SEDAN),
    ("BMW", "325ci"): M("325ci", pref=SEDAN),
    ("BMW", "325xi"): M("325xi", pref=SEDAN),
    ("BMW", "328xi"): M("328xi", pref=SEDAN),
    ("BMW", "330ci"): M("330ci", pref=SEDAN),
    ("BMW", "330xi"): M("330xi", pref=SEDAN),
    ("BMW", "525xi"): M("525xi", pref=SEDAN),
    ("BMW", "528xi"): M("528xi", pref=SEDAN),
    ("BMW", "530xi"): M("530xi", pref=SEDAN),
    ("BMW", "535xi"): M("535xi", pref=SEDAN),
    ("BMW", "645ci"): M("645ci", pref=SEDAN),
    ("BMW", "740iL"): M("740il", pref=SEDAN),
    ("BMW", "745Li"): M("745li", pref=SEDAN),
    ("BMW", "750Li"): M("750li", pref=SEDAN),
}

# our category -> regex on the <subcategory> slug of the year catalog's parts-list links
SUBCATS = {
    "alternator": r"^alternator$",
    "starter": r"^starter$",
    "ac-compressor": r"^(rp_)?air_conditioning_compressor[a-z_]*$",
    "headlights": r"^headlight$",
    "tail-lights": r"^rear_light$",
    "side-mirrors": r"^outside_mirror$",
    "window-regulator": r"^door_window_lifting_mechanism[a-z_]*$",
    "window-switch": r"^switch_window_lifter$",
    "climate-control": r"^(automatic_)?air_conditioning_control$",
    "fuel-pump-module": r"^fuel_(filter_)?pump[a-z_]*$",
    "throttle-body": r"^throttle_housing_assy$",
    "power-steering-pump": r"^power_steering_pump$",
    "gauge-cluster": r"^instrument_cluster$",
    "ignition-coils": r"^ignition_coil[a-z_]*$",
    "radiator": r"^(mounting_parts_for_radiator|radiator[a-z_]*)$",
    "door-front": r"^front_door_hinge_door_brake$",
    "door-rear": r"^rear_door_hinge_door_brake$",
    "hood": r"^(engine_mood_mounting_parts|engine_hood_mounting_parts)$",
    "fender": r"^side_panel_front$",
    "bumper-front": r"^trim_panel_front$",
    "bumper-rear": r"^trim_panel_rear$",
    "grille": r"^exterior_trim_grille_seals$",
    "trunk-lid": r"^single_components_for_trunk_lid$",
    "liftgate": r"^single_components_for_tailgate$",
    # tier C (§8): subs read on the 2006 325i / 2011 328i (E90) year pages. The
    # front strut page also holds the wheel carrier; repair-kit pages are kits.
    "wiper-motor": r"^wiper_system(_complete)?$|wiper_motor|^(single_parts_)?(windscreen|rear_window)_(wiper|cleaning)",
    "knuckle": r"^front_spring_strut_carrier_wheel_bearing$|^rear_axle_support_wheel_suspension$|^(?!repair)[a-z_]*wheel_carrier",
    "strut": r"^front_spring_strut_carrier_wheel_bearing$|^rear_spring_strut_mounting_parts$|^(?!repair)[a-z_]*(spring_strut|shock_absorber)[a-z_]*$",
}

RULES = {
    "alternator": (r"^(exch\.?|exchange)?\s*(alternator|generator)\b", r"pulley|regulator|bearing|rectifier|kit|individual|cover|cable|bracket"),
    "starter": (r"^(exch\.?|exchange)?\s*starter(\s+motor)?\b", r"solenoid|switch|cable|bracket|kit|cover|bearing"),
    "ac-compressor": (r"^(rp|exch\.?|exchange)?\s*(air\s+con(d|ditioning)?\.?\s*)?compres", r"valve|clutch|coupling\s+only|switch|sensor|bracket|kit|pulley|magnetic\s+clutch"),
    "headlights": (r"^((bi-|ahl-)?xenon\s+|halogen\s+|led\s+)?head(light|lamp)\b", r"cover|lens|bracket|module|ballast|bulb|cap|plug|drive|motor|repair|seal|holder|wiring|control"),
    "tail-lights": (r"^rear\s+light\b|^tail\s*light\b|^(led\s+)?rear\s+lamp\b", r"bulb|carrier|socket|seal|holder|cover|wiring|cable|gasket|nut"),
    "side-mirrors": (r"^(exterior|outside)\s+mirror\b", r"^mirror\s+glass|cover|cap|drive|wiring|cable|ring|baseplate|trim|frame"),
    "window-regulator": (r"^window\s+lifter\b|^(drive|motor)(,| for)\s+window\s+lifter", r"switch|cover|guide|cable\s+set|repair|bracket|seal"),
    "window-switch": (r"^switch,?\s+window\s+lifter,?\s+driver|^driver'?s?\s+side\s+switch\s+(cluster|block)|^switch\s+block,?\s+driver", r"cover|trim|panel|bezel"),
    "climate-control": (r"^(automatic\s+)?air\s+conditioning\s+control\b|^(heating|heater)\s+control\b|^control\s+panel,?\s+(automatic\s+)?air\s+con", r"front\s+plate|caps|knob|button|bulb|cover|trim|sensor"),
    "fuel-pump-module": (r"^fuel\s+pump\b|^(electric\s+)?fuel\s+feed\s+unit|^fuel\s+delivery\s+module|^in-tank\s+fuel\s+pump", r"repair|filter|relay|control\s+unit|fuse|cable|seal|ring|sender|level"),
    "throttle-body": (r"^throttle\s+housing\b|^throttle\s+body\b", r"seal|gasket|cable|bracket|sensor"),
    "power-steering-pump": (r"^(exch\.?|exchange)?\s*power\s+steering\s+pump|^(exch\.?|exchange)?\s*tandem\s+pump|^(exch\.?|exchange)?\s*vane\s+pump", r"pulley|reservoir|hose|pipe|bracket|seal|kit|plug|cable"),
    "gauge-cluster": (r"^instrument(s)?\s+(cluster|combination)\b|^instrument\s+panel\s+cluster|^kombi", r"glass|cover|trim|bulb|screw|lens|holder"),
    "ignition-coils": (r"^ignition\s+coil\b", r"boot|connector|cable|plug|locking|holder|bracket|cover"),
    "radiator": (r"^radiator$|^radiator,?\s+(engine|coolant)", r"drain|plug|cap|mount|bracket|sleeve|carrier|hose|seal|fan|shroud"),
    "door-front": (r"^door,?\s+front\b|^front\s+door\b", r"hinge|brake|check|lock|handle|seal|weatherstrip|trim|cover|reinforce|cable|bracket"),
    "door-rear": (r"^door,?\s+rear\b|^rear\s+door\b", r"hinge|brake|check|lock|handle|seal|weatherstrip|trim|cover|reinforce|cable|bracket"),
    "hood": (r"^(engine\s+)?hood$|^bonnet$|^engine\s+hood\s*,?\s*primed", r"hinge|lock|cable|lever|catch|buffer|stop|seal|insul|foil|strut|spring|support"),
    "fender": (r"^side\s+panel,?\s+front\b|^fender\b|^front\s+side\s+panel\b", r"support|bracket|trim|liner|cover|seal|reinforce|moulding"),
    "bumper-front": (r"^(panel|trim\s+cover|trim\s+panel|cover),?\s+bumper,?\s+(primed,?\s+)?front|^front\s+bumper\s+(panel|cover|trim)", r"mount|insert|grid|grille|finisher|flap|support|guide|bracket|lip|spoiler|strip|moulding|set"),
    "bumper-rear": (r"^(panel|trim\s+cover|trim\s+panel|cover),?\s+bumper,?\s+(primed,?\s+)?rear|^rear\s+bumper\s+(panel|cover|trim)", r"mount|insert|guide|bracket|lip|spoiler|strip|moulding|set|breather|diffuser"),
    "grille": (r"^(kidney\s+)?grille\b|^front\s+grille\b", r"seal|bracket|moulding|trim|insert|frame\s+only|emblem|badge"),
    "trunk-lid": (r"^(trunk\s+lid|tailgate)\b|^boot\s+lid\b", r"hinge|(lid|tailgate)\s+lock|lock\s+(cylinder|actuator|drive)|stop|buffer|seal|gasket|cap|strut|spring|holder|handle|trim|cable|light|lamp|spoiler"),
    "liftgate": (r"^tailgate\b|^rear\s+lid\b", r"hinge|(lid|tailgate)\s+lock|lock\s+(cylinder|actuator|drive)|stop|buffer|seal|gasket|cap|strut|spring|holder|handle|trim|cable|light|lamp|spoiler|glass|wiper"),
    # tier C: name rule pending (written after reading the trial's list rows)
    "wiper-motor": (r"(?!x)x", r"x^"),
    "knuckle": (r"(?!x)x", r"x^"),
    "strut": (r"(?!x)x", r"x^"),
}
# excludes match at a word start ("ring" must not hit "steering")
RULES = {k: (re.compile(inc, re.I), re.compile(rf"\b(?:{exc})", re.I)) for k, (inc, exc) in RULES.items()}
# R5a (CURATION_SPEC §3.2): the whole qualifier phrase, to the next "," or ";",
# is removed before the exclusion checks (sites/_qualifier.py)
from sites._qualifier import QUALIFIER  # noqa: E402
# BMW "Exch." / "Exchange" units are remanufactured exchange parts (template:
# dropped when the page also lists a new part for the category, else kept)
REMAN = r"(^|\|\s*)(exch\.?|exchange)\b"


def name_of(row: dict) -> str:
    """The EPC name the catalog prints for the row (mainDesc)."""
    return row["main"]


def head(row: dict) -> str:
    return QUALIFIER.sub(" ", name_of(row))


def _rule(cat: str):
    inc, exc = RULES[cat]
    # include on the OEM name, exclusions on head(); .why gives the manifest reason
    return T.name_rule(inc, exc, name_of, head)


PARTS = {cat: _rule(cat) for cat in RULES}

# "Submodel" ("Sedan N52 Engine(E90), Wagon(E91)") is kept as fitment[].options
CFG = T.Config(site=SITE, models=MODELS, subcats=SUBCATS, parts=PARTS, head_fn=head,
               reman_re=REMAN, option_col=r"option|detail|submodel",
               bare_list_position=False)  # list notes such as "Front panel, control" are not sides
categories_for, parts_on_page, product = T.bind(CFG)
# R1/R2/R4 manifests (README "Site module contract"), re-read from the cache
year_manifest, list_manifest, chain_links = T.bind_manifests(CFG)
