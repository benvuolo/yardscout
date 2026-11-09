"""www.mitsubishipartsgiant.com (SimplePart template, PartsGiant-branded store): Mitsubishi.

Layout (learned through fetch.py, 2026-11-05):
  * model page  /mitsubishi-<slug>-parts         slug words joined by "_" (outlander_sport, mirage_g4)
  * year page   /<year>-mitsubishi-<slug>-parts  links /parts-list/<year>-mitsubishi-<slug>/<group>/<sub>
  * list page   /parts-list/...  same embedded store as toyotapartsnow (partList.partList rows)
  * product     /genuine/mitsubishi~<name-slug>~<pn>  same partNumber store (fitVehicleList, Position,
                replaces / replacedBy, partDescription = Mitsubishi's own part name list)

Naming: list rows print a site name in mainDesc ("Window Regulator", older catalogs
"Regulator"; "Window Motor" or just "Motor"); auxiliaryDesc is empty. The names are
loose: a bolt can be listed as "Dehydrator" (7812A133, slug bolt-a-c-condenser) and a
reman unit only says so in its slug (M1810A001D "Starter", slug remanufactured-starter).
So a row is kept only when BOTH the list name (RULES) and the product URL's name slug
(SLUG_RULES) say it is the assembly, and the exclusions are applied to the slug too.

Door shells (door-front / door-rear) are listed as "Door Shell" on one page for both
doors; only the product page's Mitsubishi name says which ("Panel Assembly, Front Door,
Left-Hand" vs "Panel Assembly, Rear Door, ..."). For those two categories the template's
product_rules read the product page (cached, re-used by product()) and keep the row only
when that name says the right door; the matched text is kept in `product_check`.

List pages for multi-trim years say "Select your vehicle options to narrow down results"
and some of them do not embed every diagram's rows (2008 Lancer alternator page: the
assembly is absent, only its components). Missing rows are a coverage gap, never a guess.

Window switch: Mitsubishi names do not say "master". Every "Window Switch" row on the
front-door page is kept (driver master and passenger single switches); filter on
`position` / `list_location` before calling one a driver master switch.

Headlights / tail lights: "Lens & Housing" rows are kept with the assemblies; their
Mitsubishi names are "Body, Headlamp, ..." and "Lamp Unit, Tail, ..." (the lamp unit
without bulbs/sockets). `name` keeps the printed list name so curators can tell them apart.
"""
from __future__ import annotations

from ._sp_slugrules import SlugCheckedSimplePart

SITE = "www.mitsubishipartsgiant.com"

URL_MAKE = {"Mitsubishi": "mitsubishi"}
# worklist model -> catalog slug (words joined by "_"; checked against the model pages)
MODEL_SLUGS = {
    ("Mitsubishi", "3000GT"): "3000gt",
    ("Mitsubishi", "Diamante"): "diamante",
    ("Mitsubishi", "Eclipse"): "eclipse",
    ("Mitsubishi", "Endeavor"): "endeavor",
    ("Mitsubishi", "Galant"): "galant",
    ("Mitsubishi", "Lancer"): "lancer",
    ("Mitsubishi", "Mighty Max"): "mighty_max",
    ("Mitsubishi", "Mirage"): "mirage",
    ("Mitsubishi", "Mirage G4"): "mirage_g4",
    ("Mitsubishi", "Montero"): "montero",
    ("Mitsubishi", "Montero Sport"): "montero_sport",
    ("Mitsubishi", "Outlander"): "outlander",
    ("Mitsubishi", "Outlander Sport"): "outlander_sport",
    ("Mitsubishi", "Raider"): "raider",
}

CAT_PAGES = {
    "alternator": r"^charging-starting/alternator$",
    "starter": r"^charging-starting/starter$",
    "ac-compressor": r"^a-c-heating/(a-c-compressor|a-c-condenser-compressor-lines)$",
    "headlights": r"^headlights-lighting/headlamps$",
    "tail-lights": r"^headlights-lighting/(combination-lamps|tail-lamps)$",
    "side-mirrors": r"^body-hardware/outside-mirrors$",
    "window-regulator": r"^body-hardware/(front-door|rear-door)$",
    "window-switch": r"^body-hardware/front-door$",
    "climate-control": r"^a-c-heating/(a-c-heater-control-units|automatic-temperature-controls)$|^body-hardware/cluster-switches$",
    "fuel-pump-module": r"^air-fuel-delivery/(fuel-supply|fuel-system-components)$",
    "throttle-body": r"^air-fuel-delivery/throttle-body$",
    "power-steering-pump": r"^steering/p-s-pump-hoses$",
    "gauge-cluster": r"^electrical/instruments-gauges$|^body-hardware/cluster-switches$",
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
    "tailgate": r"^body-hardware/(tailgate|tail-gate[a-z-]*)$",
    "liftgate": r"^body-hardware/(lift-gate[a-z-]*|liftgate[a-z-]*|back-door[a-z-]*)$",
    # tier C (ops/interchange.md "Category breadth" §8): slugs from the R2 years manifests
    "wiper-motor": r"^(electrical/wipers|body-hardware/wiper-washer-components(-body)?)$",
    "knuckle": r"^suspension/(front-suspension|front-suspension-components|rear-suspension|rear-suspension-components|front-axle-carrier)$|^driveline-axles/(front-axle|front-axle-driveline|rear-axle)$",
    "strut": r"^suspension/(struts-components|shocks-components|struts-suspension-components-front|front-suspension|front-suspension-components|rear-suspension|rear-suspension-components|ride-control-front|ride-control-rear)$",
}

# (include on the printed list name, exclude on list name AND name slug)
RULES = {
    "alternator": (r"^(alternator|alternator assembly)$",
                   r"pulley|belt|bearing|housing|rotor|stator|regulator|rectifier|brush|bracket|cover|kit|terminal|tensioner"),
    "starter": (r"^(starter|starter assembly|starter motor)$",
                r"solenoid|relay|gear|armature|yoke|lever|drive|frame|housing|brush|bearing|kit|shaft|clutch"),
    "ac-compressor": (r"^(compressor|compressor assembly|a/c compressor)$",
                      r"clutch|pulley|coil|rotor|valve|switch|sensor|kit|oil|stay|condenser|dehydrator|drier|hub|plate"),
    "headlights": (r"^(headlamp assembly|headlight assembly|lens & housing)$",
                   r"bezel|cover|leveling|level|adjust|ballast|module|actuator|cap|kit|socket|igniter|washer|protector"),
    "tail-lights": (r"^(combination lamp assembly|tail lamp assembly|tail lamp|tail light|lens & housing)$",
                    r"socket|cover|reflector|kit|garnish"),
    "side-mirrors": (r"^(mirror assembly|outside mirror|outside mirror assembly)$",
                     r"glass|cover|cap|base|bezel|garnish|switch|motor|actuator|lamp|housing|visor|kit|inside|inner"),
    "window-regulator": (r"^(window regulator|regulator|regulator assembly|window motor|motor|power window motor)$",
                         r"switch|handle|channel|glass|crank|cover|guide|kit|cable"),
    "window-switch": (r"^(window switch|power window switch|window main switch|main switch)$",
                      r"bezel|panel|cover|base|knob|lamp|mirror|lock"),
    "climate-control": (r"^(dash control unit|heater control|heater control assembly|climate control|a/c control unit|control assembly)$",
                        r"support|base|knob|panel|cable|bezel|button|lever|sensor|lamp|valve|motor|damper|cover"),
    "fuel-pump-module": (r"^(fuel pump assembly|fuel pump|fuel pump module)$",
                         r"relay|filter|strainer|sender|gauge|sensor|level|plate|ring|cover|tank|hose|tube|regulator|resistor|controller|computer"),
    "throttle-body": (r"^(throttle body|throttle body assembly)$",
                      r"sensor|spacer|cable|heater|hose|cover|kit"),
    "power-steering-pump": (r"^(power steering pump|power steering pump assembly|oil pump assembly)$",
                            r"stay|kit|reservoir|pulley|hose|cap|switch|line|valve|tube|shaft|cover|bracket|tensioner"),
    "gauge-cluster": (r"^(cluster|cluster assembly|instrument cluster|meter assembly|combination meter)$",
                      r"lens|glass|bezel|mask|hood|cover|circuit|plate|trim|panel|case|switch"),
    "ignition-coils": (r"^(ignition coil|coil)$",
                       r"boot|cord|cover|resistor|igniter|clutch|cable|sensor"),
    "radiator": (r"^(radiator|radiator assembly)$",
                 r"cap|support|hose|cushion|insulator|drain|cock|shroud|fan|reservoir|tank|pipe|tube|sensor|switch|mount|baffle|duct|seal"),
    "door-front": (r"^door shell$", r"outer|panel|weatherstrip|shield|hinge|check"),
    "door-rear": (r"^door shell$", r"outer|panel|weatherstrip|shield|hinge|check"),
    "hood": (r"^(hood|hood panel)$",
             r"hinge|lock|latch|insulator|support|cable|rod|lever|release|bumper|scoop|vent|molding|emblem|stay|striker|weatherstrip|protector"),
    "fender": (r"^fender$",
               r"liner|protector|shield|splash|molding|flare|apron|extension|garnish|insulator|cover|support|panel|seal"),
    "bumper-front": (r"^bumper cover$", r"protector|molding|lower|extension|cap|reinforce|absorber|support|garnish|spoiler|lip"),
    "bumper-rear": (r"^bumper cover$", r"protector|molding|lower|extension|cap|reinforce|absorber|support|garnish|spoiler|lip|step"),
    "grille": (r"^(grille|grille assembly|radiator grille)$",
               r"emblem|molding|insert|surround|lower|upper|outer|cover|bezel|retainer|support|mesh|screen|garnish|plate|lamp|camera"),
    "trunk-lid": (r"^trunk lid$", r"bumper|weatherstrip|hinge|strut|damper|lamp|cover|switch|lock|latch|trim|spoiler|garnish|molding|stay"),
    "tailgate": (r"^(tailgate|tail gate|tailgate assembly)$",
                 r"handle|hinge|cable|lock|latch|protector|molding|garnish|cushion|stopper|chain|link|support|cover|emblem|lamp|trim|strap|bumper"),
    "liftgate": (r"^(liftgate|lift gate|back door|back door panel|tailgate)$",
                 r"handle|hinge|cable|lock|latch|glass|weather|stay|strut|cylinder|motor|wiper|spoiler|lamp|trim|molding|garnish|emblem|switch|striker|link|cover|pad|finish|damper"),
    # tier C, Lancer/Outlander trial rows (exact names, name AND slug):
    # "Wiper Motor" / "Motor" (slugs wiper-motor, front-motor), "Knuckle",
    # "Strut", "Shock Absorber". "Damper" rows are strut bumpers / dust covers
    # (their slugs say so) and "Carrier" is the differential: not taken.
    "wiper-motor": (r"^((front|rear) )?(wiper )?motor( assembly)?$", ""),
    "knuckle": (r"^(steering )?knuckle( assembly)?$", ""),
    "strut": (r"^(front |rear )?(strut|shock absorber|shock)( assembly)?$", ""),
}

# the product URL's name slug must also name the assembly
SLUG_RULES = {
    "alternator": r"^(remanufactured-)?alternator(-assembly)?$",
    "starter": r"^(remanufactured-)?starter(-assembly|-motor)?$",
    "ac-compressor": r"^(a-c-)?compressor(-assembly)?$",
    "headlights": r"^(headlamp-assembly|headlight-assembly|composite-assembly|composite-headlamp|lens-housing)(-driver-side|-passenger-side)?$",
    "tail-lights": r"^(combination-lamp-assembly|tail-lamp-assembly|tail-lamp|tail-light|lens-housing)(-driver-side|-passenger-side)?$",
    "side-mirrors": r"^(outside-)?mirror(-assembly)?(-driver-side|-passenger-side)?$",
    "window-regulator": r"^(window-regulator|regulator|window-motor|power-window-motor)(-driver-side|-passenger-side)?$",
    "window-switch": r"^(power-)?window-switch(-driver-side|-passenger-side)?$",
    "climate-control": r"^(dash-control-unit|heater-control|climate-control|a-c-control-unit)$",
    "fuel-pump-module": r"^fuel-pump(-assembly|-module)?$",
    "throttle-body": r"^throttle-body(-assembly)?$",
    "power-steering-pump": r"^power-steering-pump(-assembly)?$",
    "gauge-cluster": r"^(instrument-cluster|cluster-assembly|cluster|combination-meter)$",
    "ignition-coils": r"^ignition-coil$",
    "radiator": r"^radiator(-assembly)?$",
    "door-front": r"^door-shell(-driver-side|-passenger-side)?$",
    "door-rear": r"^door-shell(-driver-side|-passenger-side)?$",
    "hood": r"^hood(-panel)?$",
    "fender": r"^fender(-driver-side|-passenger-side)?$",
    "bumper-front": r"^bumper-cover$",
    "bumper-rear": r"^bumper-cover$",
    "grille": r"^(radiator-)?grille(-assembly)?$",
    "trunk-lid": r"^trunk-lid$",
    "tailgate": r"^tail-?gate(-assembly)?$",
    "liftgate": r"^(lift-?gate|back-door|tail-?gate)(-panel|-assembly)?$",
    # tier C (slugs read on the trial rows)
    "wiper-motor": r"^((front|rear)-)?(wiper-)?motor(-assembly)?(-driver-side|-passenger-side|-front|-rear)?$",
    "knuckle": r"^(steering-)?knuckle(-driver-side|-passenger-side|-front|-rear)?$",
    "strut": r"^(strut|shock-absorber|shock)(-assembly)?(-driver-side|-passenger-side|-front|-rear)?$",
}

# door shells: the product page's Mitsubishi name decides front vs rear
# ("Panel Assembly, Front Door, Left-Hand"); kept in `product_check`
PRODUCT_RULES = {"door-front": r"\bfront\s+door\b", "door-rear": r"\brear\s+door\b",
                 # tier C: a "Motor" / "Front Motor" product page that does not say
                 # wiper is not taken (as on mazdapartsnow)
                 "wiper-motor": r"^(?!.*\bwasher\b).*\bwiper\b"}


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
