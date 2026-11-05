# OEM fitment program (interchange from OEM part numbers)

Goal: verified interchange built from the carmakers' own part numbers. Two
vehicles share a part when the OEM catalog lists both under ONE part number
(or a stated supersession of it). Nothing else counts as "verified".

## Hard rules (CLAUDE.md rules 2, 3, 8)

- All catalog traffic goes through `fetch.py` (`get()` or the CLI). Never
  curl, requests, WebFetch or a browser against a catalog site. fetch.py
  enforces the allowlist, robots.txt, 4 s per site / 0.5 s global spacing,
  the cache, and a permanent stop on any bot check, 403, 429 or 503.
- Only build URLs from the site's own catalog patterns. Never follow links
  blindly (catalogs carry honeypot links). Never touch /online/, cart,
  account, search or any path robots.txt disallows (fetch.py refuses them).
- If fetch.py raises `Refused` for a domain stop, the site is done. Report
  it; do not work around it.
- Record exactly what the page says. Never infer fitment. If a page is
  ambiguous, keep the raw text and flag it.

## Site module contract (`sites/<name>.py`, name = domain minus www. and TLD)

```python
SITE = "www.example.com"
def categories_for(make: str, model: str, year: int, cats: list[str]) -> dict[str, list[str]]:
    """Our category id -> list of catalog list/diagram URLs for this vehicle-year
    that contain that category's parts. Raise on navigation failure."""
def parts_on_page(list_url: str, cat: str) -> list[dict]:
    """Parts on that page that belong to `cat`: [{"pn": "69802-06070",
    "name": "REGULATOR SUB-ASSY, FR DOOR WINDOW, LH", "product_url": "https://..."}]"""
def product(product_url: str) -> dict:
    """{"pn", "description", "position" (raw text or None), "replaces": [pn...],
       "fitment": [{"years": [lo, hi], "make": "Toyota", "model": "Camry",
                    "trims": ["LE", "XLE"] or [], "engines": ["4 Cyl 2.5L"] or [],
                    "raw": "<the row text exactly as shown>"}],
       "retrieved": "<from fetch.get>"}"""
```

Model names in `fitment` stay exactly as the catalog prints them; mapping to
our feed's names happens later, in curation. Year spans are inclusive.

## Categories (crawl tiers in crawl.py)

Tier A: alternator, starter, ac-compressor, headlights, tail-lights,
side-mirrors (outside door mirror assemblies), window-regulator (regulator,
with or without motor; also the window motor alone), window-switch (driver
master switch), climate-control (HVAC control panel/head), fuel-pump-module
(in-tank module/pump assembly), throttle-body, power-steering-pump.

Tier B: gauge-cluster, ignition-coils, radiator, door-front, door-rear
(door shells/panels), hood, fender, bumper-front, bumper-rear (covers),
grille, trunk-lid, tailgate, liftgate.

Exclude from every category: bulbs, sockets, gaskets, bolts, clips, brackets,
seals, wiring, labels, mirror glass only, covers/caps only, lens only,
remanufactured cores when a new number exists (keep "reman" as its own row
if it is the only listing), and anything not the assembly a puller removes.

## Raw record (crawl.py writes raw/<site>.jsonl)

One line per (category, part number): site, category, seed {make, model,
year}, list_url, pn, name, product_url, description, position, replaces,
fitment[], retrieved.

## Tests

Each site module ships `tests/test_<name>.py`, offline, reading cached pages
through fetch.get (cache hits only), asserting the parser on at least one
list page and two product pages, including a multi-model or multi-year
fitment block.
