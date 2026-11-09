"""www.mazdapartsnow.com (SimplePart template, "giant" variant): Mazda.

Variant facts (fetch.py, 2026-11-05): year page /<year>-mazda-<model>-parts,
product pages /genuine/mazda~<slug>~<pn>. Model slugs drop the "Mazda"
prefix ("Mazda3" -> 3) and write hyphens as underscores (cx_9, rx_8); the
MX-5 is /miata through 2005 and /mx_5_miata from 2006. List rows carry only
a short site name in mainDesc, so rules are anchored, exact name matches on
each category's own pages.

Facts the list page does not print are read from the product page
(product_rules): front vs rear door shell ("Body(Right), Rear Door") and
driver vs passenger window switch (Position).

Not navigable on purpose: feed models "B-Series" and "Truck" do not name one
catalog model (the catalog splits b2300 / b3000 / b4000 by engine), so they
fail navigation instead of guessing.
"""
from __future__ import annotations

from ._simplepart import SimplePart

SITE = "www.mazdapartsnow.com"

URL_MAKE = {"Mazda": "mazda"}
MODEL_SLUGS = {
    ("Mazda", "Mazda2"): "2", ("Mazda", "Mazda3"): "3", ("Mazda", "Mazda5"): "5", ("Mazda", "Mazda6"): "6",
    ("Mazda", "CX-5"): "cx_5", ("Mazda", "CX-7"): "cx_7", ("Mazda", "CX-9"): "cx_9",
    ("Mazda", "RX-8"): "rx_8",
    ("Mazda", "MX-5 Miata"): [(1990, 2005, "miata"), (2006, 2100, "mx_5_miata")],
    ("Mazda", "B-Series"): None,
    ("Mazda", "Truck"): None,
}

CAT_PAGES = {
    "alternator": r"^charging-starting/alternator$",
    "starter": r"^charging-starting/starter$",
    "ac-compressor": r"^a-c-heating/a-c-compressor$",
    "headlights": r"^headlights-lighting/headlamps$",
    "tail-lights": r"^headlights-lighting/(tail-lamps|combination-lamps)$",
    "side-mirrors": r"^body-hardware/outside-mirrors$",
    "window-regulator": r"^body-hardware/(front-door|rear-door)$",
    "window-switch": r"^body-hardware/front-door$",
    "climate-control": r"^a-c-heating/a-c-heater-control-units$",
    "fuel-pump-module": r"^air-fuel-delivery/fuel-supply$",
    "throttle-body": r"^air-fuel-delivery/throttle-body$",
    "power-steering-pump": r"^steering/p-s-pump-hoses$",
    "gauge-cluster": r"^electrical/instruments-gauges$",
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
    "liftgate": r"^body-hardware/(lift-gate|liftgate[a-z-]*|lift-gate-body)$",
    # tier C (ops/interchange.md "Category breadth" §8): slugs from the R2 years manifests
    "wiper-motor": r"^(electrical/wipers|body-hardware/wiper-washer-components(-body)?)$",
    "knuckle": r"^suspension/(front-suspension|front-suspension-components|rear-suspension|rear-suspension-components|front-axle-carrier)$|^driveline-axles/(front-axle|front-axle-driveline|rear-axle)$",
    "strut": r"^suspension/(struts-components|shocks-components|struts-suspension-components-front|front-suspension|front-suspension-components|rear-suspension|rear-suspension-components|ride-control-front|ride-control-rear)$",
}

RULES = {
    "alternator": (r"^alternator( assembly)?$", ""),
    "starter": (r"^starter( assembly| motor)?$", ""),
    "ac-compressor": (r"^(a/c )?compressor( assembly)?$", ""),
    "headlights": (r"^(composite )?head(lamp|light)( assembly)?$", ""),
    "tail-lights": (r"^tail ?(lamp|light)( assembly)?$|^lens & housing$", ""),
    "side-mirrors": (r"^(outside )?mirror( assembly)?$", ""),
    "window-regulator": (r"^(window )?regulator( assembly)?$|^(window )?motor$", ""),
    "window-switch": (r"^(master |power )?window switch$", ""),
    "climate-control": (r"^(heater control|dash control unit|climate control( unit| module)?|a/c control)$", ""),
    # "Fuel Pump" on this page can be the high-pressure pump (L3K9-13-35ZC, Mazdaspeed3)
    "fuel-pump-module": (r"^fuel pump (assembly|module)$", ""),
    "throttle-body": (r"^throttle body( assembly)?$", ""),
    "power-steering-pump": (r"^power steering pump( assembly)?$", ""),
    "gauge-cluster": (r"^(instrument cluster|cluster assembly)$", ""),
    "ignition-coils": (r"^ignition coil$", ""),
    "radiator": (r"^radiator( assembly)?$", ""),
    "door-front": (r"^door shell$", ""),
    "door-rear": (r"^door shell$", ""),
    "hood": (r"^hood$", ""),
    "fender": (r"^fender$", ""),
    "bumper-front": (r"^bumper cover$", ""),
    "bumper-rear": (r"^bumper cover$", ""),
    "grille": (r"^(upper )?grille( assembly)?$", ""),
    "trunk-lid": (r"^trunk lid$", ""),
    "tailgate": (r"^tail ?gate$", ""),
    "liftgate": (r"^lift ?gate$", ""),
    # tier C, Mazda3/Mazda6 trial rows (exact names): "Wiper Motor", and a bare
    # "Motor" on the wiper pages (the product page must say wiper, below);
    # "Knuckle"; "Strut", "Shock Absorber", "Shock". "Damper" / "Dynamic Damper"
    # are not struts.
    "wiper-motor": (r"^((front|rear) )?(wiper )?motor( assembly)?$", ""),
    "knuckle": (r"^(steering )?knuckle( assembly)?$", ""),
    "strut": (r"^(front |rear )?(strut|shock absorber|shock)( assembly)?$", ""),
}

PRODUCT_RULES = {
    # the product page must call it what the list row says: the 2010 Mazda3
    # alternator page lists L39C-18-881J as "Alternator", but its product page
    # reads "Module, Powertrain Control"
    "alternator": r"^(?!.*\b(module|control)\b).*alternator",
    "starter": r"^(?!.*\b(module|control)\b).*starter",
    "window-regulator": r"window|regulator",
    "door-front": r"\bfront door\b",
    "door-rear": r"\brear door\b",
    "window-switch": r"Position: Driver Side",
    # tier C: a bare "Motor" on a wiper page must be the wiper's, not the washer's
    "wiper-motor": r"^(?!.*\b(washer|bracket|frame|linkage)\b).*\bwiper\b",
}

NOTES = {
    "side-mirrors": "Mazda lists these as 'Mirror Assembly'; some product pages read "
                    "'Sub Mirror(Left/Right), Door' (other_names). The page does not say what a sub mirror includes.",
}

_T = SimplePart(SITE, URL_MAKE, MODEL_SLUGS, CAT_PAGES, RULES, oem_name_field="main",
                year_path="/{year}-{make}-{model}-parts", product_prefixes=("/genuine/",),
                product_rules=PRODUCT_RULES, category_notes=NOTES)


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
