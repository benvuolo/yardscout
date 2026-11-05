"""www.toyotapartsnow.com (SimplePart template): Toyota and Scion.

Toyota list rows print a short site name in mainDesc ("Mirror Assembly") and
the OEM part name in auxiliaryDesc ("Mirror Assembly Outer Rearview"); rows
without auxiliaryDesc (catalog-only rows) print the OEM name in mainDesc.
Rules below match the OEM name; exclusions are checked against both.
"""
from __future__ import annotations

from ._simplepart import SimplePart

SITE = "www.toyotapartsnow.com"

URL_MAKE = {"Toyota": "toyota", "Scion": "scion"}
# feed model -> catalog slug (others: lower-case, non-alnum -> "-")
MODEL_SLUGS = {
    ("Toyota", "Camry Hybrid"): "camry",      # catalog files the hybrid under Camry (trim "Hybrid")
    ("Toyota", "Camry Solara"): "solara",
    ("Toyota", "4Runner"): "4runner",
    ("Toyota", "Prius C"): "prius-c",
    ("Toyota", "RAV4"): "rav4",
    ("Toyota", "T100"): "t100",
    ("Scion", "tC"): "tc", ("Scion", "xA"): "xa", ("Scion", "xB"): "xb", ("Scion", "xD"): "xd",
}

# our category -> year-page subcategory paths ("<group>/<sub>") to read
CAT_PAGES = {
    "alternator": r"^charging-starting/alternator$",
    "starter": r"^charging-starting/starter$",
    "ac-compressor": r"^a-c-heating/(a-c-compressor|a-c-condenser-compressor-lines)$",
    "headlights": r"^headlights-lighting/(headlamps|headlamp-components[a-z-]*)$",
    "tail-lights": r"^headlights-lighting/(combination-lamps|tail-lamps[a-z-]*)$",
    "side-mirrors": r"^body-hardware/outside-mirrors$",
    "window-regulator": r"^body-hardware/(front-door-body|rear-door-body|door-body|sliding-door-body)$",
    "window-switch": r"^electrical/(front-door|door|switches-electrical)$",
    "climate-control": r"^a-c-heating/(a-c-heater-control-units|heater-components-a-c)$",
    "fuel-pump-module": r"^air-fuel-delivery/(fuel-supply|fuel-system-components)$",
    "throttle-body": r"^air-fuel-delivery/throttle-body$",
    "power-steering-pump": r"^steering/p-s-pump-hoses$",
    "gauge-cluster": r"^electrical/(instruments-gauges|gauges)$",
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
    "tailgate": r"^body-hardware/tail-gate-body$",
    "liftgate": r"^body-hardware/(back-door-body|lift-gate-body)$",
}

ASSY = r"(?:assy|assembly)"
RULES = {
    "alternator": (rf"^(reman\s+)?alternator(\s+{ASSY})?\b",
                   r"pulley|belt|brush|bearing|frame|cover|rotor|coil|stator|plate|holder|regulator\s+ass|rectifier|terminal|insulator|fuse|kit"),
    "starter": (rf"^(reman\s+)?starter(\s+{ASSY})?\b",
                r"yoke|armature|commutator|planet|gear|kit|frame|clutch|lever|holder|brush|plate|cover|relay|switch|solenoid|drive|bearing|spring"),
    "ac-compressor": (rf"^compressor(\s+{ASSY}|\b)|reman compress",
                      r"clutch|valve|switch|sensor|hose|line|tube|kit|oil|magnet|coil|relay|condenser|amplifier|stator|pulley"),
    "headlights": (rf"headlamp\s+{ASSY}|^unit\s+{ASSY},?\s*headlamp|^headlight\s+{ASSY}",
                   r"protector|cover|leveling|level|adjust|lens|ballast|computer|module|actuator|bezel|garnish|cleaner|washer|igniter"),
    "tail-lights": (rf"^lamp\s+{ASSY},?\s*(rear\s+combination|tail)|^rear combination lamp|^lens\s*(&|and)\s*body,?\s*rear\s+combination|^tail\s*lamp\s+{ASSY}",
                    r"cord|guide|cover|gasket|reflector"),
    "side-mirrors": (rf"mirror\s+{ASSY},?\s*(outer|outside|rear outer|door)|^outer\s+(rear\s*view\s+)?mirror\s+{ASSY}|^mirror\s+{ASSY}\s+outer",
                     r"glass|cover|cap|bezel|garnish|switch|motor|actuator|pad|lamp|sub-ass|inner|inside|heater|housing|visor"),
    "window-regulator": (rf"^regulator\s+(sub-)?{ASSY}|window\s+regulator|regulator.*window|^motor\s+{ASSY},?\s*power\s+window|^power\s+window\s+(regulator\s+)?motor",
                         r"switch|handle|channel|run|glass|crank|cable|pressure|fuel|voltage|knob|cover|gear|bracket|guide|stopper"),
    "window-switch": (r"master\s+switch|switch\s+(assy|assembly),?\s*power\s+window\s+regulator\s+master|power\s+window.*master",
                      r"bezel|panel|cover|base|knob|lamp"),
    "climate-control": (rf"^control\s+{ASSY},?\s*(air\s+conditioner|heater|air\s+conditioning)|^heater\s+control\s+{ASSY}|^control\s+sub-{ASSY},?\s*heater",
                        r"base|knob|panel|cable|amplifier|bezel|button|lever|sensor|lamp|valve|motor|servo|damper"),
    "fuel-pump-module": (rf"^pump\s+{ASSY},?\s*fuel|^tube\s+{ASSY},?\s*fuel\s+suction|^fuel\s+pump\s+(module|{ASSY})|^fuel\s+suction\s+tube\s+{ASSY}",
                         r"ring|plate|band|case|support|cover|filter|screen|sender|gage|gauge|lock|hose|relay|resistor|regulator|cushion|computer|controller"),
    "throttle-body": (rf"^body\s+{ASSY},?\s*throttle|^throttle\s+body\s+{ASSY}",
                      r"hose|cable|heater|cover|sensor\s+ass|spacer"),
    "power-steering-pump": (rf"^pump\s+{ASSY},?\s*vane|^vane\s+pump\s+{ASSY}|^power\s+steering\s+pump\s+{ASSY}",
                            r"kit|reservoir|pulley|hose|cap|switch|line|valve|tube|shaft|cover|housing|ring"),
    "gauge-cluster": (rf"^meter\s+{ASSY},?\s*combination|^combination\s+meter\s+{ASSY}|^instrument\s+cluster\s+{ASSY}",
                      r"glass|lens|bezel|mask|hood|cover|circuit|plate|trim|panel|case"),
    "ignition-coils": (rf"^coil\s+{ASSY},?\s*ignition|^coil,\s*ignition|^ignition\s+coil(\s+{ASSY})?\b",
                       r"boot|cord|cover|resistor|igniter"),
    "radiator": (rf"^radiator\s+{ASSY}|^radiator$",
                 r"cap|support|hose|cushion|insulator|drain|cock|grille|shroud|fan|reservoir|tank|baffle|deflector|duct|mount|valve|sensor|switch|pipe|tube|cover|pad|reserve"),
    "door-front": (rf"^panel\s+sub-{ASSY},?\s*(fr|front)\s+door\b",
                   r"trim|outside|outer|silencer|armrest|finish|lower|garnish|pad|board|frame|rear\s+door"),
    "door-rear": (rf"^panel\s+sub-{ASSY},?\s*(rr|rear)\s+door\b",
                  r"trim|outside|outer|silencer|armrest|finish|lower|garnish|pad|board|frame"),
    "hood": (rf"^hood\s+(sub-)?{ASSY}|^hood$|^hood\s+panel\b",
             r"hinge|lock|latch|insulator|support|cable|rod|lever|release|cushion|scoop|vent|molding|emblem|nozzle|stop|striker|pad|deflector|protector|silencer|garnish|louver|ornament|stripe"),
    "fender": (rf"^fender\s+sub-{ASSY},?\s*(fr|front)|^fender,\s*front\b|^front\s+fender\s+{ASSY}|^fender\s+sub-{ASSY}$",
               r"liner|protector|shield|splash|molding|flare|apron|extension|garnish|emblem|nameplate|mud|guard|insulator|pad|cover|support|brace|gusset|inner|ornament|vent"),
    "bumper-front": (r"^cover,?\s*(fr|front)\s+bumper\b|^front\s+bumper\s+cover\b",
                     r"hole|lower|extension|tow|hook|cap|grille|molding|absorber|reinforce|support|guard|step|pad|spoiler|lip|strip|insert|bezel|trim|skid|side|corner|end\b|garnish"),
    "bumper-rear": (r"^cover,?\s*(rr|rear)\s+bumper\b|^rear\s+bumper\s+cover\b",
                    r"hole|lower|extension|tow|hook|cap|molding|absorber|reinforce|support|guard|step|pad|spoiler|lip|strip|insert|bezel|trim|skid|side|corner|end\b|garnish|plate"),
    "grille": (rf"^grille\s+sub-{ASSY},?\s*radiator|^grille,?\s*radiator\b|^radiator\s+grille\b|^grille\s+{ASSY}",
               r"emblem|molding|lower|insert|bezel|retainer|support|mesh|screen|garnish|plate|lamp|camera|shutter|absorber|reinforce|sensor|ornament"),
    "trunk-lid": (rf"^panel\s+sub-{ASSY},?\s*luggage\s+compartment\s+door|^luggage\s+compartment\s+door\s+panel|^door\s+sub-{ASSY},?\s*luggage",
                  r"finish|trim|cushion|weatherstrip|lock|support|hinge|torsion|garnish|spoiler|lamp|emblem|stay|molding|inner|outer"),
    "tailgate": (rf"^panel\s+sub-{ASSY},?\s*tail\s*gate|^tail\s*gate\s+(sub-)?{ASSY}|^gate\s+sub-{ASSY},?\s*tail",
                 r"handle|hinge|cable|lock|latch|protector|molding|garnish|cushion|stopper|chain|link|support|cover|emblem|nameplate|spoiler|lamp|inner|trim"),
    "liftgate": (rf"^panel\s+sub-{ASSY},?\s*back\s+door|^back\s+door\s+(panel\s+)?sub-{ASSY}|^door\s+sub-{ASSY},?\s*back",
                 r"handle|hinge|cable|lock|latch|glass|weather|stay|cylinder|motor|wiper|spoiler|lamp|trim|molding|garnish|emblem|switch|striker|link|outside|outer|inner|board|cover|pad|finish"),
}

_T = SimplePart(SITE, URL_MAKE, MODEL_SLUGS, CAT_PAGES, RULES, oem_name_field="aux")


def categories_for(make: str, model: str, year: int, cats: list[str]) -> dict[str, list[str]]:
    return _T.categories_for(make, model, year, cats)


def parts_on_page(list_url: str, cat: str) -> list[dict]:
    return _T.parts_on_page(list_url, cat)


def product(product_url: str) -> dict:
    return _T.product(product_url)
