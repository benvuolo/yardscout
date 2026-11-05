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
       "evidence_lines": ["<the page's fitment block and Replaces lines, verbatim,
                          in page order, capped at 120 lines>"],
       "retrieved": "<from fetch.get>"}"""
```

`evidence_lines` is what verifiers check the structured fields against, since
the HTML cache does not leave the machine that crawled it.

Manifest functions (CURATION_SPEC.md §3.2 R1, R2, R4). Every site module
exports them; they re-read the pages navigation and `parts_on_page` just
fetched through the template's `cached(url)` and never make a request (a page
not in the cache gives `status: null, error: "not_fetched"`):

```python
def year_manifest(make: str, model: str, year: int) -> list[dict]:
    """One dict per year-catalog page read (R2): variant, trim, year_url,
    catalog (URL stem), status, final_url, redirected, title, subs (every
    "<group>/<sub>" parts-list slug on the page), variants (every catalog the
    model page offers for the year), variants_read, retrieved; PartsGiant also
    offered [{variant, url, read}], model_pages [{url, status}] and, on a page
    split into option catalogs, trims (every one listed) and trims_read;
    error when navigation found no catalog or a page did not read."""
def list_manifest(list_url: str, cat: str) -> dict:
    """R1: list_url, catalog, variant, (trim), status, final_url, retrieved,
    rows: EVERY row of the page, each {pn, section ("diagram" | "other" |
    "standard"), main, aux (SimplePart) or group + remark (PartsGiant),
    extra: [{name, desc}] (allExtraInfoList verbatim), replace, url, reman,
    matched, excluded_by}."""
def chain_links(product_url: str, pns: list[str]) -> dict[str, str]:
    """R4: {pn: url} for those numbers the product page itself links."""
```

`excluded_by` values: `include_miss` (the category's include rule does not
match the name), `global:<word>` (README exclusions), `rule:<word>` (the
category's exclusions; `rule:site` when a site's callable rule gives no
reason), `reman_dropped` (a reman row next to a current new number),
`url_pn_mismatch`, `no_pn`, `no_product_url`, `product_rule` /
`product_rule_unchecked` (Mitsubishi door shells), `section_not_read`
(PartsGiant gpgOnly / Standard Parts rows, never candidates), `site_module`
(a module wrapper dropped a row the template kept). crawl.py adds `product`
per matched row: `ok` (record written now), `seen` (recorded earlier),
`fail`, `not_attempted` (the run stopped on that page); null when not matched.
A module wrapper that adds a row (Honda's bare "Switch Assy.") shows as
`matched: true, matched_by: "site_module"`: crawl.py sets `matched` from what
`parts_on_page` returned.

Parser rules both templates share (R5):
- Qualifier phrases ("W/Turn Signal Lamp", "W/O Socket & Bulb", "L/Cap",
  "With Pulley") are removed up to the next "," or ";" before the exclusion
  checks (`sites/_qualifier.py`; also used by the Subaru, Lexus and BMW
  rules). Include rules still read the full name.
- Reman rows are dropped only when the page lists, for the category, a
  non-reman row in the diagram section with no `replace` value (a current
  new number). A superseded or catalog-only number does not count, so remans
  next to it are kept and marked `reman: true`. PartsGiant part dicts now
  carry `reman` too.
- Toyota numbers ending `-84` are reman (`toyotapartsnow.REMAN_PN`).

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

## Shared template code

Two catalog templates cover all 13 sites:
- `sites/_simplepart.py`: toyotapartsnow.com, jeeppartsdeal.com
  (`/catalog/<year>-<make>-<model>-parts`, `/parts-list/...`, `/oem/<make>~<slug>~<pn>`).
- `sites/_partsgiant.py`: every `.html` site (gmpartsgiant, fordpartsgiant,
  moparpartsgiant, nissanpartsdeal, infinitipartsdeal, hondapartsnow,
  acurapartswarehouse, hyundaipartsdeal, kiapartsnow, subarupartsdeal,
  lexuspartsnow).
Per-site modules stay thin: SITE, slug maps, per-make category rules (OEM part
naming differs by make), then the three contract functions from the template.

## Where crawls run

GitHub Actions (`.github/workflows/oem-fitment-crawl.yml`), one job per site
with a module, 30-minute checkpoints committed to the `oem-raw` branch
(`raw/<site>.jsonl`, `.lists.jsonl`, `.years.jsonl`, continuation parts,
`.progress.json`, `.log`, `.done`, `.blocked`: the workflow copies
`raw/<site>.*`). Crawl locally only for trials (`--max-segments 2`).

Completion mode (R3): `crawl.py --site S --complete <worklist.json>
[--minutes 28]` visits rows `[{make, model, year, cats}]` (feed names, a list
or `{"rows": [...]}`) in order: year page, the categories' list pages, both
manifests, then `product()` for every matched number not yet seen. Progress
keys are `C|make|model|year|cat`; lines carry `tier: "C"`. It never writes
`.done`. Use it to backfill manifests for seeds crawled before the manifests
existed (products already seen are not fetched again).

## Raw files (crawl.py writes raw/)

Each `.jsonl` is append-only. When a file reaches `crawl.PART_BYTES` (40 MB)
it continues in `<name>.2.jsonl`, `<name>.3.jsonl` ...: one logical file,
read in that order, and line numbers (`recrawl_of`, proof pointers) count
across the parts. A torn last line left by a killed run is cut at the next
start (its seed was not saved as done, so it is redone).

`raw/<site>.jsonl`, records. One line per (category, part number): site,
category, seed {make, model, year}, segment, list_url, pn, name,
product_url, description, position, replaces, fitment[], retrieved, plus the
template's list-level fields (SimplePart list_section, list_notes,
list_location, list_replaced_by, reman; PartsGiant list_group, list_remark,
list_info, reman). Also:
- `via`, `via_depth`, `via_root`, `via_link` (R4 chain records): reached
  through the `replaces` / `replaced_by` field of the record named in `via`
  ("replaces:27060-90010"), depth 1-4 from a listed record, by a link the
  catalog printed (`list_row`: a list row for that number on any page read;
  `product_page`: a link on the referring product page). URLs are never
  built. Chain records take the root's category, seed and list_url, have
  `name: null` and no list-level fields; their list rows, if any, are in the
  list manifest of the page that printed them. A number with no link is
  counted in progress `chain_unlinked` and logged. A hop whose fetch hits a
  network error waits in progress `chain_retry` and is fetched at the next
  start (its seed is still marked done: chains do not change what the list
  pages say).
- `recrawl_of` (R6): the line number (string, 1-based, across parts) of the
  newest earlier record for the same (category, pn), when one is written
  again (a progress reset or a completion run). The curator uses the newer one.

`raw/<site>.lists.jsonl`, R1. One line per list page read, written whether or
not its numbers were already seen (R7: notes for a vehicle come only from its
own pages): `{kind: "list", site, tier, seed, segment, cat, list_url,
catalog, variant, (trim), status, final_url, retrieved, rows, (error)}` with
`rows` as `list_manifest` above plus `product`. A page that failed to parse
keeps its line with `error` ("list-fail: ..."). A page whose fetch hit a
network error has no line; its seed is retried, so a retried seed writes its
lines again (the rows are re-read from the same page; any line with status
200 counts as read).

`raw/<site>.years.jsonl`, R2. One line per year-catalog page read per seed
visit: `{kind: "year", site, tier, seed, segment, cats, nav: "ok" | "fail",
(nav_error), ...year_manifest fields, pages: {cat: [list urls read from
this catalog page]}}`. A navigation miss (no catalog for the year) writes
the lines too, with `nav: "fail"`.

## Tests

Each site module ships `tests/test_<name>.py`, offline, reading cached pages
through fetch.get (cache hits only), asserting the parser on at least one
list page and two product pages, including a multi-model or multi-year
fitment block.

Crawler requirements (R1-R7), fully offline, no cache needed:
- `tests/test_crawler_manifests.py`: both templates' manifests, R4 links and
  R5 fixes on synthetic pages (`tests/_synthetic_pages.py`) and trimmed real
  pages (`tests/fixtures/crawler/real_pages.json`, rebuilt from the cache by
  `make_fixtures.py`); every site module exports the contract; and record
  output on the real pages equals `golden_records_v0.json` (snapshot of the
  code before these changes, `snapshot.py`) except the listed R5 changes.
- `tests/test_crawl_manifests.py`: crawl.py end to end (manifest lines, chain
  records, recrawl_of, file parts, torn-tail heal, completion mode, no extra
  requests).
- `tests/run_all.py` runs every test file and prints one line each.
