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

Manifests (R2): year_manifest reads, from the cache, the same badge year
pages categories_for fetched, one line per badge (`variant` = badge slug).

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

from . import _simplepart as _sp
from ._simplepart import NavError, SimplePart

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


def _badges(pattern: str, year: int, fetch) -> tuple[list[str], list[dict]]:
    """(badge slugs matching `pattern` whose model page links the year page,
    [{url, status}] for the home page and every model page of the class read).
    fetch(url) -> page or None (the cache-only re-read gives None for a page
    never fetched)."""
    home_url = f"https://{SITE}/"
    home = fetch(home_url)
    pages = [{"url": home_url, "status": home.get("status") if home else None}]
    if not home:
        return [], pages
    out = []
    for sl in sorted(set(re.findall(rf'href="/{MK}-([a-z0-9_]+)-parts"', home.get("html", "")))):
        if not re.search(pattern, sl):
            continue
        url = f"https://{SITE}/{MK}-{sl}-parts"
        page = fetch(url)
        pages.append({"url": url, "status": page.get("status") if page else None})
        if page and page.get("status") == 200 and f'href="/{year}-{MK}-{sl}-parts"' in page.get("html", ""):
            out.append(sl)
    return out, pages


def badges(pattern: str, year: int) -> list[str]:
    """Badge slugs matching `pattern` whose model page links the year page."""
    return _badges(pattern, year, _sp.get)[0]


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


def year_manifest(make: str, model: str, year: int) -> list[dict]:
    """R2, cache only: one line per badge year page that categories_for read.
    A feed class name ("C-Class") reads every badge of the class whose model
    page lists the year, so each line's `variants` lists them all (the badges
    offered) and `variants_read` the same; `model_pages` names the home and
    model pages the badge list came from. When one of those pages was not read
    (not in the cache, or not HTTP 200) the badge list may be incomplete, so
    every line carries an error (C1 then fails closed). A plain model reads
    _slug(model), the page categories_for reads (not the template's hyphen slug)."""
    if model not in CLASSES:
        return [_T.year_manifest_slug(make, _slug(model), year)]
    slugs, pages = _badges(CLASSES[model], year, _sp.cached)
    unread = [p["url"] for p in pages if p["status"] != 200]
    if not slugs:
        line = _T._year_line()
        line.update(variants=[], variants_read=[], model_pages=pages,
                    error="not_fetched" if any(p["status"] is None for p in pages)
                    else f"model page not read: {unread[0]}" if unread
                    else "no catalog badge page for this year")
        return [line]
    out = []
    for sl in slugs:
        line = _T.year_manifest_slug(make, sl, year, variant=sl)
        line.update(variants=list(slugs), variants_read=list(slugs), model_pages=pages)
        if unread and "error" not in line:
            line["error"] = f"model page not read: {unread[0]}"  # a badge offering the year may be missing
        out.append(line)
    return out


def list_manifest(list_url: str, cat: str) -> dict:
    out = _T.list_manifest(list_url, cat)
    stem = out.get("catalog") or ""
    out["variant"] = stem.split(f"-{MK}-", 1)[1] if f"-{MK}-" in stem else ""  # the badge
    return out


def chain_links(product_url: str, pns: list[str]) -> dict[str, str]:
    return _T.chain_links(product_url, pns)
