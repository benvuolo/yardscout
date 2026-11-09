"""www.vwpartsgiant.com (SimplePart template, "giant" variant): Volkswagen.

Variant facts (fetch.py, 2026-11-05): year page /<year>-volkswagen-<model>-parts
(no /catalog/), product pages /genuine/volkswagen~<slug>~<pn>, part numbers
printed with dashes ("06F-903-023-FX"). List rows carry only a short site
name in mainDesc ("Alternator", "Housing Assembly"); there is no
auxiliaryDesc and no catalog-only list. Rules are therefore anchored, exact
name matches, and each category reads only its own subcategory pages.

Not crawled on purpose:
  * door-front / door-rear: front and rear shells are both "Door Frame
    Assembly" ("Door Inner", position "Driver Side"/"Passenger Side") on one
    list page; neither the list nor the product page prints front or rear.
  * tailgate / trunk-lid on hatchbacks: see liftgate.
"""
from __future__ import annotations

from ._simplepart import SimplePart

SITE = "www.vwpartsgiant.com"

URL_MAKE = {"Volkswagen": "volkswagen"}
MODEL_SLUGS = {
    ("Volkswagen", "New Beetle"): "beetle",
    ("Volkswagen", "New Beetle Convertible"): "beetle",
    ("Volkswagen", "Passat Wagon"): "passat",
    ("Volkswagen", "Jetta SportWagen"): "jetta",
}

CAT_PAGES = {
    "alternator": r"^charging-starting/alternator$",
    "starter": r"^charging-starting/starter$",
    "ac-compressor": r"^a-c-heating/a-c-compressor$",
    "headlights": r"^headlights-lighting/headlamps$",
    "tail-lights": r"^headlights-lighting/tail-lamps$",
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
    "hood": r"^body-hardware/hood-components$",
    "fender": r"^body-hardware/fender-components$",
    "bumper-front": r"^body-hardware/bumper-components-front$",
    "bumper-rear": r"^body-hardware/bumper-components-rear$",
    "grille": r"^body-hardware/grille-components$",
    "trunk-lid": r"^body-hardware/trunk-lid-components$",
    "liftgate": r"^body-hardware/(lift-gate|liftgate[a-z-]*|lift-gate-body|tailgate[a-z-]*|tail-gate[a-z-]*)$",
    # tier C (ops/interchange.md "Category breadth" §8): slugs from the R2 years manifests
    "wiper-motor": r"^(electrical/wipers|body-hardware/wiper-washer-components(-body)?)$",
    "knuckle": r"^suspension/(front-suspension|front-suspension-components|rear-suspension|rear-suspension-components|front-axle-carrier)$|^driveline-axles/(front-axle|front-axle-driveline|rear-axle)$",
    "strut": r"^suspension/(struts-components|shocks-components|struts-suspension-components-front|front-suspension|front-suspension-components|rear-suspension|rear-suspension-components|ride-control-front|ride-control-rear)$",
}

RULES = {
    "alternator": (r"^alternator( assembly)?$", ""),
    "starter": (r"^starter( assembly| motor)?$", ""),
    "ac-compressor": (r"^(a/c )?compressor( assembly)?$", ""),
    "headlights": (r"^(composite )?head(lamp|light) assembly$|^head(lamp|light)$", ""),
    "tail-lights": (r"^(inner |outer )?tail ?(lamp|light)( assembly)?$", ""),
    # the outside mirror is listed as "Housing Assembly" (2006 Jetta; product page
    # "Housing") or "Mirror Housing" (2003 Jetta);
    # the page does not say whether glass and cap are included
    "side-mirrors": (r"^(outside )?mirror( assembly)?$|^housing assembly$|^mirror housing$", ""),
    "window-regulator": (r"^window regulator( assembly)?$|^regulator( assembly)?$|^window motor$|^window regulator motor$", ""),
    # front-door page only; VW prints the same name for driver and passenger switches
    "window-switch": (r"^(master )?window switch$", ""),
    "climate-control": (r"^(heater control|dash control unit|climate control( unit| module)?|temperature control|a/c control)$", ""),
    # "Fuel Pump" on the fuel-supply page can be the engine-mounted high-pressure
    # pump (06F-127-025-M); only the in-tank assembly names are taken
    "fuel-pump-module": (r"^fuel pump (assembly|module)$|^fuel unit$|^fuel pump & sender( assembly| unit)?$", ""),
    "throttle-body": (r"^throttle body( assembly)?$", ""),
    "power-steering-pump": (r"^(power )?steering pump( assembly)?$|^power steering pump$", ""),
    "gauge-cluster": (r"^(cluster assembly|instrument cluster)$", ""),
    "ignition-coils": (r"^ignition coil$", ""),
    "radiator": (r"^radiator( assembly)?$", ""),
    "hood": (r"^hood( panel)?$", ""),
    "fender": (r"^fender$", ""),
    "bumper-front": (r"^bumper cover$", ""),
    "bumper-rear": (r"^bumper cover$", ""),
    "grille": (r"^(upper |center |radiator )?grille( assembly)?$", ""),
    "trunk-lid": (r"^trunk lid$", ""),
    "liftgate": (r"^(lift ?gate|tail ?gate|hatch|rear hatch)$", ""),
    # tier C: name rule pending (written after reading the trial's list rows)
    "wiper-motor": (r"(?!x)x", ""),
    "knuckle": (r"(?!x)x", ""),
    "strut": (r"(?!x)x", ""),
}

NOTES = {
    "side-mirrors": "VW lists the outside mirror as 'Housing Assembly' or 'Mirror Housing'; product pages "
                    "call it 'Housing' or 'Repair Kit'. Mirror glass and cap are separate numbers; the page does "
                    "not say whether they are included.",
    "window-switch": "VW prints 'Window Switch' for driver and passenger front-door switches alike; "
                     "use list_notes/position to tell the driver switch.",
}

_T = SimplePart(SITE, URL_MAKE, MODEL_SLUGS, CAT_PAGES, RULES, oem_name_field="main",
                year_path="/{year}-{make}-{model}-parts", product_prefixes=("/genuine/",),
                category_notes=NOTES)


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
