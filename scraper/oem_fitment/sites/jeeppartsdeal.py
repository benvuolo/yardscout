"""www.jeeppartsdeal.com (SimplePart template, same as toyotapartsnow): Jeep,
and since worklist version 2 (2026-11-05) Dodge, Chrysler and Ram.

Dodge/Chrysler/Ram basis: the site's own product pages print them as full
fitment rows (on oem-raw@2026-11-05, 959 records: Dodge 340, Chrysler 113,
Ram 50 rows, with trims and engines), so the catalog is the whole Mopar
dealer catalog, and the template's year-page path is make-parameterised
(/catalog/<year>-<make>-<model>-parts, as Toyota/Scion on toyotapartsnow).
No page cache was available to confirm a Dodge year page before the crawl:
a wrong guess is a navigation miss (HTTP 404 / redirect / no parts-list
links -> NavError, written to the R2 year manifest), never a refusal and
never a record. The year splits below are the year ranges the catalog
itself prints for each model name.

Mopar list rows print the OEM part name in mainDesc ("Compressor - A/C",
catalog-only rows "COMPRESSOR Air Conditioning") and a short site name in
auxiliaryDesc ("Compressor", "Headlamp Bulb"). Rules match the OEM name;
exclusions are checked against both (a "Headlamp" row whose short name is
"Headlamp Bulb" is a bulb). Product fitment blocks routinely list other
Chrysler-group vehicles (Dodge, Chrysler, Ram); they are recorded as printed.
"""
from __future__ import annotations

from ._simplepart import SimplePart

SITE = "www.jeeppartsdeal.com"

URL_MAKE = {"Jeep": "jeep", "Dodge": "dodge", "Chrysler": "chrysler", "Ram": "ram"}
# feed (make, model) -> catalog slug; others slugify ("Cherokee" -> "cherokee",
# "Grand Caravan" -> "grand-caravan"). None: the feed name does not name one
# catalog model. A year list: only those years have a catalog model of that
# name under this make (ranges as printed in the catalog's fitment rows).
MODEL_SLUGS = {
    ("Jeep", "Grand Cherokee"): "grand-cherokee",
    # Dodge Ram 1500/2500 1994-2010; 2011+ the catalog files them under make Ram
    # ("Ram 1500"); before 1994 they are D150/W150 etc. (2WD/4WD: not one model)
    ("Dodge", "Ram 1500"): [(1994, 2010, "ram-1500")],
    ("Dodge", "Ram 2500"): [(1994, 2010, "ram-2500")],
    ("Dodge", "Ram Van"): [(1994, 1997, "ram-van")],          # 1999-2003: Ram 1500/2500/3500 Van
    ("Dodge", "Ram Van 1500"): [(1999, 2003, "ram-1500-van")],
    ("Dodge", "Ram Wagon"): [(1994, 1997, "ram-wagon")],
    ("Dodge", "Ram"): None, ("Dodge", "Ram Pickup"): None, ("Dodge", "1500 Pickup"): None,
    ("Dodge", "D1500"): None, ("Dodge", "Caravan/Grand Caravan"): None,
    ("Chrysler", "300C"): "300",  # the catalog prints 300C as Chrysler 300 (trim)
}

CAT_PAGES = {
    # tier W (ops/interchange.md "Wheels"): the years manifest lists suspension/wheels
    "wheels": r"^suspension/wheels$",
    "alternator": r"^charging-starting/alternator$",
    "starter": r"^charging-starting/starter$",
    "ac-compressor": r"^a-c-heating/(a-c-compressor|a-c-condenser-compressor-lines)$",
    "headlights": r"^headlights-lighting/(headlamps|headlamp-components[a-z-]*)$",
    "tail-lights": r"^headlights-lighting/(combination-lamps|tail-lamps[a-z-]*)$",
    "side-mirrors": r"^body-hardware/outside-mirrors$",
    "window-regulator": r"^body-hardware/(front-door|rear-door|door)$",
    "window-switch": r"^body-hardware/(front-door|mirrors|door)$|^electrical/switches$",
    "climate-control": r"^a-c-heating/a-c-heater-control-units$",
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
    "grille": r"^body-hardware/(grille-components|bumper-components-front)$",
    "tailgate": r"^body-hardware/(tailgate|tail-gate[a-z-]*|swing-gate[a-z-]*)$",
    "liftgate": r"^body-hardware/(lift-gate|liftgate[a-z-]*|lift-gate-body)$",
}

D = r"\W+"  # Mopar "Noun - Qualifier" / "NOUN Qualifier"
RULES = {
    "alternator": (r"^(alternator|generator)\b",
                   r"pulley|belt|decoupler|cover|shield|regulator|brush|bearing|kit|cable"),
    "starter": (r"^starter\b(?!\W+(solenoid|relay|shield|heat))",
                r"solenoid|relay|shield|heat|cable|kit|drive|cover"),
    "ac-compressor": (rf"^compressor{D}(a/?c|air\s+cond)",
                      r"clutch|valve|switch|sensor|hose|line|kit|oil|coil|pulley|relay|suspension|leveling"),
    "headlights": (rf"^headlamp\b|^lamp{D}head",
                   # boot: 5143152AA "Headlamp" / short name "Boot" (headlight bulb cap), audit 2026-11-05
                   r"bezel|adjust|level|module|ballast|motor|switch|lens|cover|cap|\bboot\b|mount|igniter|washer|wash|protector|filler|shield"),
    "tail-lights": (rf"^lamp{D}tail|^tail\s*lamp|^tail\s*light",
                    r"bezel|lens|cover|cap|mount|reflector|guard|gasket"),
    "side-mirrors": (rf"^mirror{D}(outside|exterior|side\s+view)",
                     r"glass|cover|cap|bezel|switch|motor|actuator|scalp|skull|lamp|housing|inside|kit"),
    "window-regulator": (rf"^regulator\b|^motor{D}(power\s+)?window",
                         r"handle|switch|channel|run|glass|crank|pressure|fuel|voltage|knob|cable\s+guide|cover|gear\b"),
    "window-switch": (rf"^switch{D}(window\s+and\s+door\s+lock|.*\bmaster\b|power\s+window\s+master)",
                      r"bezel|panel|cover|base|knob|lamp|mirror"),
    "climate-control": (rf"^control{D}(a/?c|heater|air\s+cond|climate|temperature|hvac|atc|automatic\s+temp)",
                        r"cable|knob|bezel|button|lever|sensor|lamp|valve|motor|actuator|door|vacuum"),
    "fuel-pump-module": (rf"^module(\s+kit)?{D}fuel\s+pump|^fuel\s+pump\s+module|^pump{D}fuel\b",
                         r"control|relay|driver|o\s*ring|lock|strainer|filter|tube|line|hose|sender|resistor|wiring"),
    "throttle-body": (rf"^throttle\s+body\b|^body{D}throttle",
                      r"sensor|spacer|cable|heater|hose|cover|kit|elbow|adapter"),
    "power-steering-pump": (rf"^pump{D}power\s+steering",
                            r"reservoir|pulley|kit|hose|cap|line|valve|cooler|bracket"),
    "gauge-cluster": (rf"^cluster{D}instrument",
                      r"mask|lens|lid|bezel|cover|trim|circuit|hood"),
    "ignition-coils": (rf"^coil{D}ignition|^ignition\s+coil",
                       r"capacitor|boot|cable|cover|condenser"),
    "radiator": (r"^radiator\b",
                 r"cap|support|hose|isolator|insulator|shroud|fan|drain|mount|baffle|deflector|duct|closure|filler|tank|bottle|cooler|pressure|valve|grille|cover|pad"),
    "door-front": (rf"^door{D}front\b",
                   r"outer|skin|handle|hinge|glass|weather|panel|trim|lock|latch|check|bumper|strip|insulator|silencer|shield|cover|frame|bezel"),
    "door-rear": (rf"^door{D}rear\b",
                  r"outer|skin|handle|hinge|glass|weather|panel|trim|lock|latch|check|bumper|strip|insulator|silencer|shield|cover|frame|bezel"),
    "hood": (r"^hood\b",
             r"adjust|bumper|weather|silencer|insulator|latch|release|hinge|propeller|bushing|scoop|vent|decal|ornament|emblem|nozzle|lock|cable|rod|support|reinforce|stop|striker|molding|deflector|louver|pad|protector|garnish|insert|blanket|catch"),
    "fender": (rf"^fender{D}front\b|^fender$",
               r"liner|flare|shield|splash|molding|extension|apron|vent|mud|guard|insulator|reinforce|support|panel|filler|applique|inner|rear|stone|lamp|marker"),
    "bumper-front": (rf"^fascia{D}front|^bumper{D}front",
                     r"absorber|reinforce|applique|panel|step|tow|hook|cap|bezel|insert|grille|pad|guard|skid|plate|isolator|support|beam|end\b|extension|shield|spoiler|deflector|air\s+dam|license"),
    "bumper-rear": (rf"^fascia{D}rear|^bumper{D}rear",
                    r"absorber|reinforce|applique|panel|step|tow|hook|cap|bezel|insert|pad|guard|skid|plate|isolator|support|beam|end\b|extension|shield|spoiler|license|hitch"),
    "grille": (rf"^grille{D}(radiator|front)\b|^grille$",
               r"insert|speaker|defroster|vent|cowl|emblem|lamp|bezel|screen|molding|applique|lower|mesh|shutter|camera|nameplate|seal"),
    "tailgate": (rf"^(tailgate|tail\s+gate|gate{D}tail|door{D}tailgate)\b",
                 r"hinge|latch|glass|handle|bumper|strap|check|support|cable|link|lock|striker|weather|carrier|trim|panel|cylinder|stop|actuator|module|switch|lamp|emblem|nameplate|molding|applique|cover|bar"),
    "liftgate": (rf"^(liftgate|lift\s+gate|door{D}liftgate)\b",
                 r"handle|bar|striker|latch|cylinder|link|weather|propeller|gas|hinge|glass|motor|wiper|spoiler|lamp|trim|molding|applique|switch|strut|cable|support|module|panel|actuator|lock|bumper|emblem|nameplate|camera|release|check|cover|shield|silencer|insulator|pad|garnish"),
    # tier W: road wheels only (Mopar "Wheel - Aluminum", "Wheel, Steel");
    # no spare / temporary / compact wheel, cap, cover, nut, lock or sensor
    "wheels": (rf"^wheel(\s+assembly)?({D}(aluminum|alloy|steel|chrome|painted|polished|forged|cast)\b|$|{D}front|{D}rear)",
               r"cap|cover|nut|bolt|stud|lock|weight|valve|sensor|ornament|emblem|insert|spare|temporary|compact|carrier|bearing|hub|kit|liner|flare|opening|molding|trim|balance|tire"),
}

NOTES = {
    "window-switch": "Mopar 'Switch - Window And Door Lock' rows include passenger-door switches; "
                     "use position to tell the driver switch.",
}

_T = SimplePart(SITE, URL_MAKE, MODEL_SLUGS, CAT_PAGES, RULES, oem_name_field="main", category_notes=NOTES)


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
