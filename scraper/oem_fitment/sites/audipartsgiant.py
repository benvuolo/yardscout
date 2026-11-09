"""www.audipartsgiant.com (SimplePart template, PartsGiant-branded store): Audi.

Built after the fitment condition in SOURCES.md was checked (2026-11-05): 21 of 21
product pages reached from list pages (alternators, headlamps, compressors, starters,
regulators, tail lamps; 2008 A4, 2008 Q7, 2012 Q5) carry the Vehicle Fitment table in
the server HTML and in __INITIAL_STORE__ (isShowFitList true, 1-16 rows). The scout's
three fitment-less samples were numbers reached outside the catalog (one redirects to
the home page). Pages without rows are still recorded with fitment [] and the
template's `no_fitment_rows` flag.

Layout: /<year>-audi-<slug>-parts (slugs joined by "_": a4_quattro), /parts-list/...,
/genuine/audi~<name-slug>~<pn>; part numbers printed with dashes ("06E-911-023-EX").
List names are site names ("Starter", "Heater Control" with slug dash-control-unit),
so the list name AND the slug must name the assembly (sites/_sp_slugrules.py).

Model slugs: the catalog files the US A8 after 1999 and the 2001-2005 allroad only
under "a8_quattro" / "allroad_quattro"; those years navigate there. Fitment model
names are recorded exactly as printed ("A8 Quattro", "Allroad Quattro"); joining them
to feed names is curation's job. A5 navigates only where the catalog has "a5"
(2010-2014); other A5 years raise NavError instead of guessing a variant.

Not crawled on purpose:
  * door-front / door-rear: front and rear shells are both "Door Shell" on one list
    page and "Door" on the product page; neither prints front or rear.

Side mirrors: older catalogs (2008 A4) sell only mirror parts ("Mirror Housing" = cap,
"Motor & Base", "Adjust Motor") and yield no record. Newer ones (2012+ A6, 2017+ A4) list
"Mirror Assembly" (slug mirror-assembly) whose Audi name is "Mounting"; those are kept
with a category_note, since the page does not say whether glass and cap are included.

X-suffix numbers (06E-911-023-EX, 8H0-920-951-FX) are Audi exchange units, but the
product pages do not say so; nothing is inferred from the suffix. A list page that
prints "Remanufactured" sets `reman` through the template.

Window switch: driver and passenger front switches are both "Window Switch"; filter on
position (8H0-959-851-C-5PR Driver Side) before calling one a master switch.

Fuel pump: "Fuel Pump" with slug fuel-pump on the fuel-supply page is the engine
high-pressure pump (06E-127-025-AB); only slug fuel-pump-assembly / -module rows count.
"""
from __future__ import annotations

from ._sp_slugrules import SlugCheckedSimplePart

SITE = "www.audipartsgiant.com"

URL_MAKE = {"Audi": "audi"}
MODEL_SLUGS = {
    ("Audi", "A4 Quattro"): "a4_quattro",
    ("Audi", "A6 Quattro"): "a6_quattro",
    ("Audi", "A5 Quattro"): "a5_quattro",
    ("Audi", "A5"): [(2010, 2014, "a5")],
    ("Audi", "A8"): [(1997, 1999, "a8"), (2000, 2025, "a8_quattro")],
    ("Audi", "Allroad"): [(2001, 2005, "allroad_quattro"), (2013, 2016, "allroad")],
}  # A4, A6, Q5, Q7, A3, TT, S4, Q3 slugify as-is (checked against the home page)

SIDE = r"(-(front|rear|driver-side|passenger-side|left|right|upper|lower|inner|outer))*"

CAT_PAGES = {
    "alternator": r"^charging-starting/alternator$",
    "starter": r"^charging-starting/starter$",
    "ac-compressor": r"^a-c-heating/(a-c-compressor|a-c-condenser-compressor-lines)$",
    "headlights": r"^headlights-lighting/headlamps$",
    "tail-lights": r"^headlights-lighting/tail-lamps$",
    "side-mirrors": r"^body-hardware/outside-mirrors$",
    "window-regulator": r"^body-hardware/(front-door|rear-door|door)$",
    "window-switch": r"^body-hardware/(front-door|door)$",
    "climate-control": r"^a-c-heating/(a-c-heater-control-units|automatic-temperature-controls)$",
    "fuel-pump-module": r"^air-fuel-delivery/(fuel-supply|fuel-system-components)$",
    "throttle-body": r"^air-fuel-delivery/throttle-body$",
    "power-steering-pump": r"^steering/p-s-pump-hoses$",
    "gauge-cluster": r"^electrical/instruments-gauges$|^body-hardware/cluster-switches$",
    "ignition-coils": r"^electrical/ignition-system$",
    "radiator": r"^belts-cooling/radiator-components$",
    "hood": r"^body-hardware/hood-components$",
    "fender": r"^body-hardware/fender-components$",
    "bumper-front": r"^body-hardware/bumper-components-front$",
    "bumper-rear": r"^body-hardware/bumper-components-rear$",
    "grille": r"^body-hardware/grille-components$",
    "trunk-lid": r"^body-hardware/trunk-lid-components$",
    "liftgate": r"^body-hardware/(lift-gate|liftgate[a-z-]*|tail-gate[a-z-]*|tailgate|back-door[a-z-]*)$",
    # tier C (ops/interchange.md "Category breadth" §8): slugs from the R2 years manifests
    "wiper-motor": r"^(electrical/wipers|body-hardware/wiper-washer-components(-body)?)$",
    "knuckle": r"^suspension/(front-suspension|front-suspension-components|rear-suspension|rear-suspension-components|front-axle-carrier)$|^driveline-axles/(front-axle|front-axle-driveline|rear-axle)$",
    "strut": r"^suspension/(struts-components|shocks-components|struts-suspension-components-front|front-suspension|front-suspension-components|rear-suspension|rear-suspension-components|ride-control-front|ride-control-rear)$",
    # tier D wave 1 (ops/interchange.md §10): slugs from the R2 years manifests
    "sunroof": r"^(body-hardware/sunroof(-body)?|electrical/sunroof)$",
    "center-console": r"^body-hardware/(console|center-console|front-console|rear-console)$",
    "door-panel": r"^interior-exterior-trim/interior-trim-(front-door|rear-door|door)$",
    "blower-motor": r"^a-c-heating/blower-motor-fan$",
    "fog-lights": r"^headlights-lighting/fog-lamps$",
}

RULES = {
    "alternator": (r"^(alternator|alternator assembly)$",
                   r"pulley|belt|bearing|housing|rotor|stator|regulator|rectifier|brush|bracket|cover|kit|terminal|tensioner|shield|freewheel"),
    "starter": (r"^(starter|starter assembly|starter motor)$",
                r"solenoid|relay|gear|armature|yoke|lever|drive|frame|housing|brush|bearing|kit|shaft|clutch|shield"),
    "ac-compressor": (r"^(compressor|compressor assembly|a/c compressor)$",
                      r"clutch|pulley|coil|rotor|valve|switch|sensor|kit|oil|condenser|dehydrator|drier|hub|plate|sleeve"),
    "headlights": (r"^(headlamp assembly|headlight assembly|headlamp|composite headlamp)$",
                   r"bezel|cover|leveling|level|adjust|ballast|module|actuator|motor|cap|kit|socket|igniter|washer|wiper|protector|frame|housing"),
    "tail-lights": (r"^(tail lamp|tail lamp assembly|tail light|inner tail lamp|outer tail lamp|lens & housing)$",
                    r"socket|cover|reflector|kit|garnish|connector|holder|buffer|support"),
    "side-mirrors": (r"^(mirror assembly|outside mirror|outside mirror assembly)$",
                     r"glass|cover|cap|base|bezel|garnish|switch|motor|actuator|lamp|housing|drive|frame|kit|inside|inner"),
    "window-regulator": (r"^(window regulator|regulator|regulator assembly|window motor|power window motor)$",
                         r"switch|handle|channel|glass|crank|cover|guide|kit|cable|bumper|stop"),
    "window-switch": (r"^(window switch|power window switch)$",
                      r"bezel|panel|cover|base|knob|lamp|mirror|lock|trim"),
    "climate-control": (r"^(dash control unit|heater control|climate control|climate control unit|a/c control unit)$",
                        r"support|base|knob|cable|bezel|button|lever|sensor|lamp|valve|motor|damper|cover"),
    "fuel-pump-module": (r"^(fuel pump assembly|fuel pump|fuel pump module|fuel unit)$",
                         r"relay|filter|strainer|sender|gauge|sensor|level|plate|ring|cover|tank|hose|tube|regulator|resistor|controller|computer|sleeve"),
    "throttle-body": (r"^(throttle body|throttle body assembly)$",
                      r"sensor|spacer|cable|heater|hose|cover|kit"),
    "power-steering-pump": (r"^(power steering pump|power steering pump assembly)$",
                            r"sleeve|stay|kit|reservoir|pulley|hose|cap|switch|line|valve|tube|shaft|cover|bracket|tensioner|cooler"),
    "gauge-cluster": (r"^(instrument cluster|cluster assembly|combination instrument)$",
                      r"lens|glass|bezel|mask|hood|cover|circuit|plate|trim|panel|case|switch"),
    "ignition-coils": (r"^ignition coil$",
                       r"boot|cord|cover|resistor|igniter|cable|sensor|connector"),
    "radiator": (r"^(radiator|radiator assembly)$",
                 r"cap|support|hose|cushion|insulator|drain|shroud|fan|reservoir|tank|pipe|tube|sensor|switch|mount|baffle|duct|seal|frame|panel"),
    "hood": (r"^(hood|hood panel)$",
             r"hinge|lock|latch|insulator|support|cable|rod|lever|release|bumper|buffer|scoop|vent|molding|emblem|stay|striker|weatherstrip|protector|catch|stop|strut"),
    "fender": (r"^fender$",
               r"liner|protector|shield|splash|molding|flare|apron|extension|garnish|insulator|cover|support|panel|seal|stay|plate|guard"),
    "bumper-front": (r"^bumper cover$", r"pin|band|protector|molding|lower|extension|cap|reinforce|absorber|support|garnish|spoiler|lip|clip|bracket|guide"),
    "bumper-rear": (r"^bumper cover$", r"pin|band|protector|molding|lower|extension|cap|reinforce|absorber|support|garnish|spoiler|lip|step|clip|bracket|guide"),
    "grille": (r"^(grille|grille assembly|radiator grille|center grille)$",
               r"emblem|molding|insert|surround|lower|upper|outer|cover|bezel|retainer|support|mesh|screen|garnish|plate|lamp|camera|license"),
    "trunk-lid": (r"^trunk lid$", r"stop|bumper|weatherstrip|hinge|strut|damper|lamp|cover|switch|lock|latch|trim|spoiler|garnish|molding|stay|cylinder|release"),
    "liftgate": (r"^(lift gate|liftgate|tail gate|tailgate|rear hatch)$",
                 r"handle|hinge|cable|lock|latch|glass|weather|stay|strut|cylinder|motor|wiper|spoiler|lamp|trim|molding|garnish|emblem|switch|striker|link|cover|pad|finish|damper|stop"),
    # tier C, A4 trial rows (exact names, wiper pages only): "Wiper Motor" (slug
    # front-motor), "Wiper Motor Assembly", "Rear Motor" (slug wiper-motor);
    # "Knuckle"; "Strut" / "Shock Absorber" / "Shock". "Carrier" is the
    # differential (slug differential-assembly), not taken.
    "wiper-motor": (r"^((front|rear) )?(wiper )?motor( assembly)?$", ""),
    "knuckle": (r"^(steering )?knuckle( assembly)?$", ""),
    "strut": (r"^(front |rear )?(strut|shock absorber|shock)( assembly)?$", ""),
    # tier D: name rule pending (written after reading the trial's list rows)
    "sunroof": (r"(?!x)x", ""),
    "center-console": (r"(?!x)x", ""),
    "door-panel": (r"(?!x)x", ""),
    "blower-motor": (r"(?!x)x", ""),
    "fog-lights": (r"(?!x)x", ""),
}

SLUG_RULES = {
    "alternator": rf"^(remanufactured-)?alternator(-assembly)?{SIDE}$",
    "starter": rf"^(remanufactured-)?starter(-assembly|-motor)?{SIDE}$",
    "ac-compressor": r"^(a-c-)?compressor(-assembly)?$",
    "headlights": rf"^(composite-headlamp|headlamp|headlight)(-assembly)?{SIDE}$",
    "tail-lights": rf"^(tail-lamp|tail-light|lens-housing)(-assembly)?{SIDE}$",
    "side-mirrors": rf"^(outside-mirror|mirror-assembly|mirror-outside){SIDE}$",
    "window-regulator": rf"^(window-regulator|regulator|window-motor|power-window-motor){SIDE}$",
    "window-switch": rf"^(power-)?window-switch{SIDE}$",
    "climate-control": r"^(dash-control-unit|heater-control|climate-control(-unit)?|a-c-control-unit)$",
    "fuel-pump-module": r"^fuel-pump-(assembly|module)$|^fuel-unit$",
    "throttle-body": r"^throttle-body(-assembly)?$",
    "power-steering-pump": r"^power-steering-pump(-assembly)?$",
    "gauge-cluster": r"^(instrument-cluster|cluster-assembly|combination-instrument)$",
    "ignition-coils": r"^ignition-coil$",
    "radiator": r"^radiator(-assembly)?$",
    "hood": r"^hood(-panel)?$",
    "fender": rf"^fender{SIDE}$",
    "bumper-front": r"^bumper-cover$",
    "bumper-rear": r"^bumper-cover$",
    "grille": r"^(radiator-|center-)?grille(-assembly)?$",
    "trunk-lid": r"^trunk-lid$",
    "liftgate": rf"^(lift-?gate|tail-?gate|rear-hatch){SIDE}$",
    # tier C (slugs read on the A4 trial rows)
    "wiper-motor": rf"^((front|rear)-)?(wiper-)?motor(-assembly)?{SIDE}$",
    "knuckle": rf"^(steering-)?knuckle{SIDE}$",
    "strut": rf"^(strut|shock-absorber|shock)(-assembly)?{SIDE}$",
    # tier D: name rule pending (written after reading the trial's list rows)
    "sunroof": r"(?!x)x",
    "center-console": r"(?!x)x",
    "door-panel": r"(?!x)x",
    "blower-motor": r"(?!x)x",
    "fog-lights": r"(?!x)x",
}

NOTES = {
    "side-mirrors": "Audi lists 'Mirror Assembly' whose own name is 'Mounting'; mirror glass and cap "
                    "are separate numbers and the page does not say whether they are included.",
    "window-switch": "Audi prints 'Window Switch' for driver and passenger front-door switches alike; "
                     "use position to tell the driver switch.",
}

# tier C: the product page must say wiper and must not be the frame/bracket
# ("Front Motor | Motor" says neither; 8K1-955-023-E "Wiper Motor Assembly" is
# "Bracket" on its own page)
PRODUCT_RULES = {"wiper-motor": r"^(?!.*\b(washer|bracket|frame|linkage)\b).*\bwiper\b"}

_T = SlugCheckedSimplePart(SITE, URL_MAKE, MODEL_SLUGS, CAT_PAGES, RULES, oem_name_field="main",
                           year_path="/{year}-{make}-{model}-parts", product_prefixes=("/genuine/",),
                           category_notes=NOTES, slug_rules=SLUG_RULES, product_rules=PRODUCT_RULES)


def categories_for(make: str, model: str, year: int, cats: list[str]) -> dict[str, list[str]]:
    return _T.categories_for(make, model, year, cats)


def parts_on_page(list_url: str, cat: str) -> list[dict]:
    return _T.parts_on_page(list_url, cat)


def product(product_url: str) -> dict:
    return _T.product(product_url)


def year_manifest(make: str, model: str, year: int) -> list[dict]:
    return _T.year_manifest(make, model, year)


def list_manifest(list_url: str, cat: str) -> dict:
    return _T.list_manifest(list_url, cat)


def chain_links(product_url: str, pns: list[str]) -> dict[str, str]:
    return _T.chain_links(product_url, pns)
