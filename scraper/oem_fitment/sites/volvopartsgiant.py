"""www.volvopartsgiant.com (SimplePart template, PartsGiant-branded store): Volvo.

Layout (learned through fetch.py, 2026-11-05), same store as mitsubishipartsgiant:
  * model page  /volvo-<slug>-parts            (s60_cross_country style slugs; worklist models are one word)
  * year page   /<year>-volvo-<slug>-parts     links /parts-list/<year>-volvo-<slug>/<group>/<sub>
  * product     /genuine/volvo~<name-slug>~<pn>  partNumber store (fitVehicleList, Position, replaces)

Naming: list rows print a site name in mainDesc ("Mirror Outside", "Tail Lamp", "Lens &
Housing", "Door Shell", "Lid", "Cover"); auxiliaryDesc is empty; the slug often adds a
side/end word (mirror-outside-rear, door-shell-front, bumper-cover-willow-green). As on
mitsubishipartsgiant, a row is kept only when list name AND slug name the assembly
(sites/_sp_slugrules.py).

Product-page checks (template product_rules) where the list name cannot decide:
  * door-front / door-rear: list "Door Shell" for both; product name "Front Door" /
    "Rear Door" (31385356 "Door Shell, Front | Front Door").
  * trunk-lid: list "Lid"; product other name "Trunk Lid" (9152416).

No fitment rows: some numbers print no Vehicle Fitment table (scout: radiator 31368221).
They are recorded with fitment [] and the template's `no_fitment_rows` flag; nothing is
inferred from the list page they were found on.

Exchange units: Volvo sells factory exchange (remanufactured) units; product names say
"Alternator, Exchange" / "Compressor, Exchange". These get `exchange_unit: true`; a name
that says "Reman" gets `reman: true` (8251551 "Reman Starter").

Window switch: names never say "master"; all front-door "Window Switch" rows are kept
(31334466 driver side, 31334467 passenger). Filter on position before calling one a
driver master switch.

Mirrors: "Mirror Outside" is the mirror Volvo sells (many numbers are paint variants);
"Housing", "Drive Assembly", "Frame" and glass are excluded.

Tail gate: Volvo's "Tail Gate" pages are the wagon/SUV hatch and feed `liftgate`; the
pickup `tailgate` category has no Volvo pages.

"60 Series" in the worklist names no single catalog model (S60/V60); navigation refuses it.
"""
from __future__ import annotations

from ._sp_slugrules import SlugCheckedSimplePart

SITE = "www.volvopartsgiant.com"

URL_MAKE = {"Volvo": "volvo"}
MODEL_SLUGS = {
    ("Volvo", "60 Series"): None,  # feed bucket, not a catalog model
}  # all other worklist models slugify as-is (xc90, s60, 240, ...); checked against the home page

SIDE = r"(-(front|rear|driver-side|passenger-side|left|right|upper|lower|inner|outer))*"

CAT_PAGES = {
    "alternator": r"^charging-starting/alternator$",
    "starter": r"^charging-starting/starter$",
    "ac-compressor": r"^a-c-heating/(a-c-compressor|a-c-condenser-compressor-lines)$",
    "headlights": r"^headlights-lighting/headlamps$",
    "tail-lights": r"^headlights-lighting/(tail-lamps|combination-lamps)$",
    "side-mirrors": r"^body-hardware/outside-mirrors$",
    "window-regulator": r"^body-hardware/(front-door|rear-door)$",
    "window-switch": r"^body-hardware/front-door$",
    "climate-control": r"^a-c-heating/(a-c-heater-control-units|automatic-temperature-controls)$|^electrical/switches$",
    "fuel-pump-module": r"^air-fuel-delivery/(fuel-supply|fuel-system-components)$",
    "throttle-body": r"^air-fuel-delivery/throttle-body$",
    "power-steering-pump": r"^steering/p-s-pump-hoses$",
    "gauge-cluster": r"^electrical/(instruments-gauges|switches)$|^body-hardware/cluster-switches$",
    "ignition-coils": r"^electrical/ignition-system$",
    "radiator": r"^belts-cooling/radiator-components$",
    "door-front": r"^body-hardware/door-components$",
    "door-rear": r"^body-hardware/door-components$",
    "hood": r"^body-hardware/hood-components$",
    "fender": r"^body-hardware/fender-components$",
    "bumper-front": r"^body-hardware/bumper-components-front$",
    "bumper-rear": r"^body-hardware/bumper-components-rear$",
    "grille": r"^body-hardware/grille-components$",
    "trunk-lid": r"^body-hardware/trunk-lid-components$",
    # Volvo builds no pickups: its "Tail Gate" pages are the wagon/SUV hatch
    # (1995 850 body-hardware/tail-gate holds "Lift Gate" 9203493), so they feed liftgate
    "liftgate": r"^body-hardware/(lift-gate|liftgate[a-z-]*|tail-gate[a-z-]*|tailgate|back-door[a-z-]*)$",
    # tier C (ops/interchange.md "Category breadth" §8): slugs from the R2 years manifests
    "wiper-motor": r"^(electrical/wipers|body-hardware/wiper-washer-components(-body)?)$",
    "knuckle": r"^suspension/(front-suspension|front-suspension-components|rear-suspension|rear-suspension-components|front-axle-carrier)$|^driveline-axles/(front-axle|front-axle-driveline|rear-axle)$",
    "strut": r"^suspension/(struts-components|shocks-components|struts-suspension-components-front|front-suspension|front-suspension-components|rear-suspension|rear-suspension-components|ride-control-front|ride-control-rear)$",
}

RULES = {
    "alternator": (r"^(alternator|alternator assembly)$",
                   r"pulley|belt|bearing|housing|rotor|stator|regulator|rectifier|brush|bracket|cover|kit|terminal|tensioner|shield"),
    "starter": (r"^(starter|starter assembly|starter motor)$",
                r"solenoid|relay|gear|armature|yoke|lever|drive|frame|housing|brush|bearing|kit|shaft|clutch|shield"),
    "ac-compressor": (r"^(compressor|compressor assembly|a/c compressor)$",
                      r"clutch|pulley|coil|rotor|valve|switch|sensor|kit|oil|condenser|dehydrator|drier|hub|plate"),
    "headlights": (r"^(headlamp assembly|headlight assembly|headlamp)$",
                   r"bezel|cover|leveling|level|adjust|ballast|module|actuator|motor|cap|kit|socket|igniter|washer|wiper|protector|frame"),
    "tail-lights": (r"^(tail lamp|tail lamp assembly|tail light|combination lamp assembly|lens & housing)$",
                    r"socket|cover|reflector|kit|garnish|connector"),
    "side-mirrors": (r"^(mirror outside|mirror assembly|outside mirror|outside mirror assembly)$",
                     r"glass|cover|cap|base|bezel|garnish|switch|motor|actuator|lamp|housing|drive|frame|kit|inside|inner"),
    "window-regulator": (r"^(window regulator|regulator|regulator assembly|window motor|motor|power window motor)$",
                         r"switch|handle|channel|glass|crank|cover|guide|kit|cable"),
    "window-switch": (r"^(window switch|power window switch|window main switch|main switch)$",
                      r"bezel|panel|cover|base|knob|lamp|mirror|lock"),
    "climate-control": (r"^(dash control unit|heater control|heater control assembly|climate control|control panel|a/c control unit)$",
                        r"support|base|knob|cable|bezel|button|lever|sensor|lamp|valve|motor|damper|cover"),
    "fuel-pump-module": (r"^(fuel pump assembly|fuel pump|fuel pump module)$",
                         r"relay|filter|strainer|sender|gauge|sensor|level|plate|ring|cover|tank|hose|tube|regulator|resistor|controller|computer|sleeve"),
    "throttle-body": (r"^(throttle body|throttle body assembly)$",
                      r"sensor|spacer|cable|heater|hose|cover|kit"),
    "power-steering-pump": (r"^(power steering pump|power steering pump assembly)$",
                            r"sleeve|stay|kit|reservoir|pulley|hose|cap|switch|line|valve|tube|shaft|cover|bracket|tensioner"),
    "gauge-cluster": (r"^(instrument cluster|cluster|cluster assembly|combined instrument)$",
                      r"lens|glass|bezel|mask|hood|cover|circuit|plate|trim|panel|case|switch"),
    "ignition-coils": (r"^(ignition coil|coil)$",
                       r"boot|cord|cover|resistor|igniter|cable|sensor"),
    "radiator": (r"^(radiator|radiator assembly)$",
                 r"cap|support|hose|cushion|insulator|drain|shroud|fan|reservoir|tank|pipe|tube|sensor|switch|mount|baffle|duct|seal|frame|panel"),
    "door-front": (r"^door shell$", r"outer|panel|weatherstrip|shield|hinge|check"),
    "door-rear": (r"^door shell$", r"outer|panel|weatherstrip|shield|hinge|check"),
    "hood": (r"^(hood|hood panel)$",
             r"hinge|lock|latch|insulator|support|cable|rod|lever|release|bumper|scoop|vent|molding|emblem|stay|striker|weatherstrip|protector|catch"),
    "fender": (r"^fender$",
               r"liner|protector|shield|splash|molding|flare|apron|extension|garnish|insulator|cover|support|panel|seal|stay|plate"),
    "bumper-front": (r"^bumper cover$", r"band|protector|molding|lower|extension|cap|reinforce|absorber|support|garnish|spoiler|lip|clip|bracket"),
    "bumper-rear": (r"^bumper cover$", r"band|protector|molding|lower|extension|cap|reinforce|absorber|support|garnish|spoiler|lip|step|clip|bracket"),
    "grille": (r"^(grille|grille assembly|radiator grille)$",
               r"emblem|molding|insert|surround|lower|upper|outer|cover|bezel|retainer|support|mesh|screen|garnish|plate|lamp|camera"),
    "trunk-lid": (r"^(trunk lid|lid)$", r"bumper|weatherstrip|hinge|strut|damper|lamp|cover|switch|lock|latch|trim|spoiler|garnish|molding|stay|cylinder"),
    "tailgate": (r"^(tailgate|tail gate)$",
                 r"handle|hinge|cable|lock|latch|protector|molding|garnish|cushion|stopper|chain|link|support|cover|emblem|lamp|trim|strap|bumper"),
    "liftgate": (r"^(lift gate|liftgate|tail gate|tailgate|back door)$",
                 r"handle|hinge|cable|lock|latch|glass|weather|stay|strut|cylinder|motor|wiper|spoiler|lamp|trim|molding|garnish|emblem|switch|striker|link|cover|pad|finish|damper|stop"),
    # tier C, XC90/S60 trial rows: exact names "Wiper Motor", "Knuckle", "Strut",
    # "Shock Absorber", "Shock" (product slugs wiper-motor, knuckle-driver-side,
    # strut-passenger-side, shock-absorber-rear). "Carrier" and "Knuckle Arm"
    # are not taken.
    "wiper-motor": (r"^((front|rear|windshield|rear window) )?wiper motor( assembly)?$", ""),
    "knuckle": (r"^(steering )?knuckle( assembly)?$", ""),
    "strut": (r"^(front |rear )?(strut|shock absorber|shock)( assembly)?$", ""),
}

PAINT = r"(-[a-z]+)*"  # paint names in bumper-cover slugs (bumper-cover-willow-green, bumper-cover-red-rear)
SLUG_RULES = {
    "alternator": rf"^(remanufactured-)?alternator(-assembly)?{SIDE}$",
    "starter": rf"^(remanufactured-)?starter(-assembly|-motor)?{SIDE}$",
    "ac-compressor": r"^(a-c-)?compressor(-assembly)?$",
    "headlights": rf"^(headlamp|headlight)(-assembly)?{SIDE}$",
    "tail-lights": rf"^(tail-lamp|tail-light|combination-lamp|lens-housing)(-assembly)?{SIDE}$",
    "side-mirrors": rf"^(mirror-outside|outside-mirror|mirror-assembly|mirror){SIDE}$",
    "window-regulator": rf"^(window-regulator|regulator|window-motor|power-window-motor){SIDE}$",
    "window-switch": rf"^(power-)?window-switch{SIDE}$",
    "climate-control": r"^(dash-control-unit|heater-control|climate-control|control-panel|a-c-control-unit)$",
    "fuel-pump-module": r"^fuel-pump(-assembly|-module)?$",
    "throttle-body": r"^throttle-body(-assembly)?$",
    "power-steering-pump": r"^power-steering-pump(-assembly)?$",
    "gauge-cluster": r"^(instrument-cluster|cluster-assembly|cluster|combined-instrument)$",
    "ignition-coils": r"^ignition-coil$",
    "radiator": r"^radiator(-assembly)?$",
    "door-front": rf"^door-shell{SIDE}$",
    "door-rear": rf"^door-shell{SIDE}$",
    "hood": r"^hood(-panel)?$",
    "fender": rf"^fender{SIDE}$",
    "bumper-front": rf"^bumper-cover{PAINT}$",
    "bumper-rear": rf"^bumper-cover{PAINT}$",
    "grille": r"^(radiator-)?grille(-assembly)?$",
    "trunk-lid": r"^(trunk-)?lid$",
    "tailgate": rf"^tail-?gate(-assembly)?{SIDE}$",
    "liftgate": rf"^(lift-?gate|tail-?gate|back-door){SIDE}$",
    # tier C (slugs read on the trial's list rows)
    "wiper-motor": rf"^(rear-)?wiper-motor(-assembly)?{SIDE}$",
    "knuckle": rf"^(steering-)?knuckle{SIDE}$",
    "strut": rf"^(strut|shock-absorber|shock)(-assembly)?{SIDE}$",
}

PRODUCT_RULES = {
    "door-front": r"\bfront\s+door\b",
    "door-rear": r"\brear\s+door\b",
    "trunk-lid": r"\btrunk\s+lid\b",
}

_T = SlugCheckedSimplePart(SITE, URL_MAKE, MODEL_SLUGS, CAT_PAGES, RULES, oem_name_field="main",
                           year_path="/{year}-{make}-{model}-parts", product_prefixes=("/genuine/",),
                           product_rules=PRODUCT_RULES, slug_rules=SLUG_RULES)


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
