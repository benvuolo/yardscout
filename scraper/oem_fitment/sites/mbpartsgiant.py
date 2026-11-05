"""www.mbpartsgiant.com (SimplePart template, "giant" variant): Mercedes-Benz.

Variant facts (fetch.py, 2026-11-05): year page
/<year>-mercedes_benz-<badge>-parts, product pages
/genuine/mercedes-benz~<slug>~<pn>. The catalog is organized by badge
(c230, c300, ml350, sprinter_2500), slugs with underscores. List rows carry
only a short site name in mainDesc.

Class names in our feed ("C-Class", "M-Class", "SLK") do not name one badge.
For those, every badge of the class whose model page lists the year is read
(C-Class -> c230, c300, c63_amg, ...). Each product page's fitment block
names the exact badges, so nothing is inferred; the seed model stays the
feed name.

Not crawled on purpose (the pages do not print what the category needs):
  * door-front / door-rear: "Door Shell", product "Driver's Door" even for the
    passenger shell; front vs rear not printed.
  * fuel-pump-module: "Fuel Pump" rows are "Auxiliary Pump" / "Exchange
    Suction Jet Pump" on the product page, not a module.
  * side-mirrors: "Mirror Housing", product "Frame".
  * climate-control: no heater/climate control name on the HVAC or switch pages
    (generic "Switch Assembly" / "Control Module").
"""
from __future__ import annotations

import re

from ._simplepart import NavError, SimplePart, get

SITE = "www.mbpartsgiant.com"
MK = "mercedes_benz"

# feed class name -> badge slugs of that class (anchored on the slug)
CLASSES = {
    "C-Class": r"^c\d", "E-Class": r"^e\d", "S-Class": r"^s\d", "M-Class": r"^ml\d",
    "GL-Class": r"^gl\d", "GLK-Class": r"^glk\d", "R-Class": r"^r\d", "SL-Class": r"^sl\d",
    "SLK": r"^slk\d", "SLK-Class": r"^slk\d", "CL-Class": r"^cl\d", "CLA-Class": r"^cla\d",
    "CLK": r"^clk\d", "CLK-Class": r"^clk\d", "CLS-Class": r"^cls\d",
    "300": r"^300", "300-Class": r"^300", "190": r"^190",
}

CAT_PAGES = {
    "alternator": r"^charging-starting/alternator$",
    "starter": r"^charging-starting/starter$",
    "ac-compressor": r"^a-c-heating/a-c-compressor$",
    "headlights": r"^headlights-lighting/headlamps$",
    "tail-lights": r"^headlights-lighting/tail-lamps$",
    "window-regulator": r"^body-hardware/(front-door|rear-door)$",
    "window-switch": r"^body-hardware/front-door$",
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
    "liftgate": r"^body-hardware/(lift-gate|liftgate[a-z-]*|lift-gate-body)$",
}

RULES = {
    "alternator": (r"^alternator( assembly)?$", ""),
    "starter": (r"^starter( assembly| motor)?$", ""),
    "ac-compressor": (r"^(a/c )?compressor( assembly)?$", ""),
    "headlights": (r"^(composite )?head(lamp|light)( assembly)?$", ""),
    "tail-lights": (r"^tail ?(lamp|light)( assembly)?$", ""),
    "window-regulator": (r"^(window )?regulator( module| assembly)?$|^(window )?motor$", ""),
    "window-switch": (r"^(master |power )?window switch$", ""),
    "throttle-body": (r"^throttle body( assembly)?$", ""),
    "power-steering-pump": (r"^power steering pump( assembly)?$", ""),
    "gauge-cluster": (r"^(instrument cluster|cluster assembly)$", ""),
    "ignition-coils": (r"^ignition coil$", ""),
    "radiator": (r"^radiator( assembly)?$", ""),
    "hood": (r"^hood$", ""),
    "fender": (r"^fender$", ""),
    "bumper-front": (r"^bumper cover$", ""),
    "bumper-rear": (r"^bumper cover$", ""),
    "grille": (r"^grille( assembly)?$", ""),
    "trunk-lid": (r"^trunk lid$", ""),
    "liftgate": (r"^lift ?gate$", ""),
}

PRODUCT_RULES = {
    # the product page must agree with the list row: the 2005 C55 AMG alternator
    # page lists 271-155-01-15 as "Alternator", its product page reads "Pulley"
    "alternator": r"^(?!.*\b(pulley|module|control|regulator)\b).*alternator",
    "starter": r"^(?!.*\b(module|control|pinion|solenoid)\b).*start",
    # door pages: "Motor"/"Regulator Module" must be the window's ("Window Motor",
    # "Basic Carrier Rail")
    "window-regulator": r"window|regulator|carrier rail",
    "window-switch": r"Position: Driver Side",
}


def _slug(model: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", model.lower()).strip("_")


_T = SimplePart(SITE, {"Mercedes-Benz": MK}, {}, CAT_PAGES, RULES, oem_name_field="main",
                year_path="/{year}-{make}-{model}-parts", product_prefixes=("/genuine/",),
                product_rules=PRODUCT_RULES)


def badges(pattern: str, year: int) -> list[str]:
    """Badge slugs matching `pattern` whose model page links the year page."""
    home = get(f"https://{SITE}/")["html"]
    out = []
    for sl in sorted(set(re.findall(rf'href="/{MK}-([a-z0-9_]+)-parts"', home))):
        if not re.search(pattern, sl):
            continue
        page = get(f"https://{SITE}/{MK}-{sl}-parts")
        if page.get("status") == 200 and f'href="/{year}-{MK}-{sl}-parts"' in page["html"]:
            out.append(sl)
    return out


def categories_for(make: str, model: str, year: int, cats: list[str]) -> dict[str, list[str]]:
    slugs = badges(CLASSES[model], year) if model in CLASSES else [_slug(model)]
    if not slugs:
        raise NavError(f"{make} {model} {year}: no catalog badge page for this year")
    out: dict[str, list[str]] = {}
    for sl in slugs:
        for cat, urls in _T.categories_for_slug(make, sl, year, cats).items():
            out.setdefault(cat, []).extend(u for u in urls if u not in out.get(cat, []))
    return out


def parts_on_page(list_url: str, cat: str) -> list[dict]:
    return _T.parts_on_page(list_url, cat)


def product(product_url: str) -> dict:
    return _T.product(product_url)
