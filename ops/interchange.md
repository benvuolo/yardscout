# Interchange workstream — status (opened 2026-11-05)

Goal (owner, 2026-11-04): car-part.com-level cross-compatibility, accuracy
first. Owner approved multi-agent ("ultra") scale.

## Decision record

- car-part.com is Hollander Interchange (licensed, proprietary). Its
  robots.txt blocks its search (/cgi-bin) and /Services/Hollander. Not
  scraped, not reverse-engineered. Licensing Hollander remains an owner
  option (quote-based).
- Verified interchange = the carmaker's own catalog lists both vehicles
  under one OEM part number (or a stated supersession).
- Sources that pass rule 2 (robots allows the pages, no bot check, no
  anti-scraping terms found): the SimplePart/PartsGiant dealer catalogs
  listed in `scraper/oem_fitment/fetch.py` ALLOWED. Refused or out:
  gmpartsdirect.com, parts.nissanusa.com, store.mopar.com,
  hondapartsonline.net (Cloudflare bot check); dormanproducts.com (robots
  blocks all); olathetoyotaparts.com (domain hijacked by spam);
  car-part.com; rockauto.com (not used).
- Coverage ceiling of this source: the 13 catalogs cover 297k of 333k cars
  on the lots (89%). VW, Mazda, Mitsubishi, BMW, Mercedes, Volvo are not
  reachable this way.

## Pipeline

1. `scraper/oem_fitment/fetch.py`: allowlist, robots, 4 s/site, 0.5 s global,
   cache, permanent stop on any bot check/403/429/503.
2. `scraper/oem_fitment/sites/`: two shared template parsers
   (`_partsgiant.py` for the .html catalogs, `_simplepart.py` for Toyota and
   Jeep) plus a thin module per site.
3. `.github/workflows/oem-fitment-crawl.yml`: one Actions job per site with a
   module, `crawl.py` in 30-minute slices, checkpoints committed to the
   `oem-raw` branch (`raw/<site>.jsonl` etc.). Worklist order (cars on lots),
   tier A categories first. Runs every 6 h until each site is done.
4. Next (not started): curation into interchange groups with an
   independent adversarial verification per site, then integration into
   `interchange.json` as verified platform groups and engine-family groups.

## Status

- 2026-11-05 00:05 UTC: harness committed (8ea96df).
- 00:11 UTC: container restart killed the in-session navigator workflow
  (wf_7d045075-e05) a few minutes in; nothing lost but cached pages. Moved
  crawls to GitHub Actions (9203003) and navigator builds to two sessions:
  - session_016ZzJfK5C7Cm4qZpC4QjSVs: .html template + GM, Ford, Mopar,
    Nissan, Infiniti (done 01:20 UTC, 4c9a9b2; see "PartsGiant" below)
  - session_016ZzJfHbzhf7ZAm4Xt8ok79: SimplePart template + Toyota, Jeep
  - 00:49 UTC: Toyota + Jeep modules on main (2010da8, dc5c1d3); Actions
    crawl run 41944219436 started for both.
  - 00:51 UTC (owner: maximum breadth this hour), more builder sessions:
    - session_016ZzJfHdymdThBbtJ5HYPnQ Honda + Acura
    - session_016ZzJfHkeNBsfhhGE3jys2o Hyundai + Kia
    - session_016ZzJfJPMiqWBVeGP97xHiL Subaru + Lexus
    - session_016ZzJfLtcR8MerD7PWDQVoN Mopar + Nissan + Infiniti (the
      .html session now does GM + Ford only)
    - session_016ZzJfJ6BcW6cQfYXpnSYuV aftermarket application catalogs
      (Denso, DB Electrical, TYC) under oem_fitment/aftermarket/
    - session_016ZzJfHmQkMfzb6xBaKcrnG source scout for uncovered makes
      (writes oem_fitment/SOURCES.md; probe.py only)
  - Hub workflow wf_a05aed60-f20: curation + integration spec (two designs,
    judge), build, adversarial review, fix -> CURATION_SPEC.md, curate.py.
- 00:55 UTC: SimplePart navigators done (session_016ZzJfHbzhf7ZAm4Xt8ok79):
  `sites/_simplepart.py`, `sites/toyotapartsnow.py` (Toyota + Scion),
  `sites/jeeppartsdeal.py` (Jeep; jeeppartsdeal.com is the same template).
  Tests `tests/test_toyotapartsnow.py` (49 checks) and
  `tests/test_jeeppartsdeal.py` (33) pass; page checks read the local cache
  only and skip when it is absent (CI has no cache). Trials (tier A, 2
  segments): Toyota 163 records, Jeep 79, 0 errors, no refusals; every
  record was checked field by field against the cached page text (pn,
  position, replaces, replaced-by, every fitment cell): 242/242 match.

### SimplePart: what a curator must know

- Structured fields come from the page's embedded store
  (`window.__INITIAL_STORE__`); each is checked against the rendered text.
  Any disagreement goes to `flags` (`fitment_text_differs_from_store`,
  `unparsed_fitment_row:...`, `no_fitment_rows`, `pn_differs_from_url:...`,
  `evidence_truncated:N`). Treat flagged records as unverified.
- Long fitment tables render 10 rows and then "View More". The rest of the
  rows are in the same page's store. `evidence_lines` holds the rendered rows,
  then a literal "View More", then the store rows. `fitment_rows_rendered` /
  `fitment_rows_total` say where the switch happens.
- A year cell can carry several spans ("2011-2013, 2007-2008 Scion tC").
  These are emitted as one fitment entry per span, sharing `raw`, with
  `year_spans` listing all of them. Spans are never merged.
- Two table layouts. Current numbers use Year Make Model | Trim | Engine.
  Superseded or catalog-only numbers use Year Make Model | Engine |
  Important vehicle option details: `trims` is empty and the third column is
  kept verbatim in `other_columns`. The two layouts can give different year
  spans for the same part family (e.g. 4801477AA vs 4801477AG Patriot
  2007-2015 vs 2007-2017). Record both, do not reconcile.
- `name` is the list page's OEM-ish name. `description` is the product
  page's display name, which can be wrong (55111610AC "Compressor - A/C"
  displays as "Dash Control Unit"). Classify by `name`/`aux_desc`, never by
  `description`.
- Reman: an R-number / "Reman" row is dropped only when a new number in the
  same category is on the same list page. Otherwise it is kept and marked
  `reman: true` (2009 Camry alternators are reman-only).
- Position: `position` is the product page's Position line, verbatim. Toyota
  often prints only "Driver Side", so front vs rear comes from `list_url`
  (front-door-body / rear-door-body). `list_location` holds the list page's
  Location values.
- Jeep window-switch: Mopar names do not say "master". "Switch - Window And
  Door Lock" rows are kept, and that includes the passenger-door switch
  (4602785AD, Front Right). Filter on position before calling one a driver
  master switch. Toyota window-switch is "Master Switch" rows only.
- WJ Grand Cherokee headlamps are named "Headlamp - Headlamp Parking And
  Turn" by Mopar. They are the headlamp assemblies and are kept.
- Fitment blocks list sister vehicles across makes (Dodge/Chrysler on Jeep
  parts; Scion/Toyota on Toyota). Model names stay as printed ("Solara", not
  "Camry Solara"). "Camry Hybrid" is crawled through the Camry pages (trim
  "Hybrid"), so crawl.py's coverage check never marks those years covered.
- Local trials need `mkdir -p scraper/oem_fitment/raw`: crawl.py does not
  create it. The Actions workflow does.

- 01:05 UTC: source survey (session_016ZzJfHmQkMfzb6xBaKcrnG) in
  `scraper/oem_fitment/SOURCES.md`. Seven same-network catalogs qualify for
  uncovered makes: vwpartsgiant, mazdapartsnow, bmwpartsdeal, mbpartsgiant,
  mitsubishipartsgiant, volvopartsgiant, audipartsgiant (conditional). Together
  they cover 30.9k of the 36.1k uncovered cars. Two second sources:
  toyotapartsdeal, chevypartsdeal (same network, not independent). Terms pages
  are client-rendered, so a human must read them before ALLOWED changes.
  ALLOWED not edited.

- 01:06 UTC: source scout (a9800c4, SOURCES.md) found 7 more catalogs; hub
  read both template families' sales-policy terms (no automation clause) and
  allowed them (e50b9b0): vwpartsgiant, mazdapartsnow, bmwpartsdeal,
  mbpartsgiant, mitsubishipartsgiant, volvopartsgiant, audipartsgiant
  (conditional). Coverage ceiling 89% -> 98.4% of lot cars. Builders:
  SimplePart session -> VW, Mazda, Mercedes; session_016ZzJfL2a85N1tgt5nnonXc
  -> Mitsubishi, Volvo, Audi; Subaru/Lexus session -> + BMW. Second-source
  catalogs (toyotapartsdeal, chevypartsdeal) not used: same network, load only.
  Crawl matrix capped at 8 sites at once (network-wide ~2 req/s).

## Aftermarket application-table track (session_016ZzJfJ6BcW6cQfYXpnSYuV, 2026-11-05)

Code: `scraper/oem_fitment/aftermarket/` (README there). Part-driven runner
`run.py` (separate from crawl.py; fetch.get via `common.get`), site modules,
`verify_records.py` (re-checks records against cached page text), offline
tests `tests/test_dbelectrical.py` (38 checks, committed trimmed fixtures +
cache-only part) and `tests/test_run.py`. `aftermarket/raw/` is git-ignored.

- **www.dbelectrical.com: works.** Alternators + starters
  (`/alternators/automotive/`, `/starters/automotive/` -> make -> model ->
  `?page=N`; `/products/*.html`). Each product page: DB item number, specs
  (amps, pulley, "Fits" free text), Applications List (one row per year:
  Make | Type | Model | Year | Engine, from two feeds), and "Replaces These
  Part Numbers" by brand: carmaker OE numbers (FORD, MAZDA, CHRYSLER,
  VOLKSWAGEN, PORSCHE...), Motorcraft/ACDelco, OE suppliers (Denso,
  Visteon, Bosch, Mitsubishi Electric), Lester, DENSO First Time Fit, ~20
  rebuilder brands. Trial: 47 records (32 alternator, 15 starter; incl. 9
  targeted Mazda/VW/Mitsubishi), 0 fetch errors, no refusals;
  verify_records: 47/47 match the page text field by field (item number,
  every spec, every application row in order, every replaces row, OE
  classification). Cross-make seen: Ford/Mazda/Mercury (400-14103,
  400-14112, 400-48167 with FORD+MAZDA OE numbers), Dodge/Ram/Mitsubishi
  (410-52233, CHRYSLER OE + DENSO 428000-3050), VW/Porsche (420-24000).
- **Caveat for curators: the OE list is product-level**, not per
  application row. Same DB item = same aftermarket unit, which is weaker
  than one OEM number (400-14106 lists Explorer/Ranger/Aerostar 4.0 while
  its Ford OE numbers are Mustang-only 4R3T/6R3T). Use OE numbers to join
  this track to the dealer-catalog track; never call a pair verified from
  this track alone. Pulley/plug differences live in `fits_text`.
- **www.densoautoparts.com: unreachable here.** PDF catalogs withdrawn; the
  part finder is POST-only `wp-admin/admin-ajax.php` with a WordPress nonce
  (dpf_opticat_* actions); no GET product/application pages. fetch.get is
  GET-only. Needs a hub/owner decision (POST + nonce, a search endpoint).
- **www.tycamericas.com: unreachable here.** D365 Commerce: category pages
  (`/all/lighting/head-lamps/5637149891.c` etc.) render "Loading..."; the
  product list comes client-side from the retail-server API on another
  domain; no product URLs in any server page or sitemap; Download Center
  has only order/returns forms; search URLs are robots-disallowed.
- fetch.py note for the hub: `urllib.robotparser` keeps only the first
  `User-agent: *` group and ignores `*` wildcards. On dbelectrical.com the
  first `*` group is "Allow: /", so fetch.py alone would allow /search.php.
  `aftermarket/common.get` re-checks with RFC 9309 semantics; crawl.py
  sites may want the same check in fetch.py.

## PartsGiant .html template (session_016ZzJfK5C7Cm4qZpC4QjSVs, 2026-11-05)

Built (commit 4c9a9b2): `sites/_partsgiant.py` (template, layout and record
format documented in its docstring), `gmpartsgiant.py`, `fordpartsgiant.py`,
`moparpartsgiant.py`, `nissanpartsdeal.py`, `infinitipartsdeal.py` (reuses the
Nissan rules), offline tests `tests/test_partsgiant_template.py` and
`tests/test_<site>.py` (pure checks always; page checks cache-only, skipped
without the local cache), helper `tests/_pg_cacheonly.py`.

Trials (`crawl.py --tier A --max-segments 2`, final code, raw/ not committed):
GM 176 records (Cruze 2014; Silverado 1500 2000/2012/2011), Ford 97 (F-150
2001 via engine/transmission catalogs, 2004), Mopar 142 (Ram 1500 2002/1988;
Grand Caravan 2010), Nissan 118 (Altima 2013, 2012), Infiniti 169 (G35
2004/2008, G37 2009). 0 product/list errors; nav-fails only for seed years
the site has no catalog for (Cruze 1998, Grand Caravan 2023). Checked field
by field against cached page text: 7 records per site (pn, description,
Replaced By, Replaces, every fitment row in order incl. the rows behind
"View More", year spans, make/model split, position source): all match.

### PartsGiant: what a curator must know

- Fitment comes from the page's `window.__INITIAL_STORE__` (same response)
  because the rendered table stops at 10 rows; product() refuses a page whose
  rendered rows are not exactly the first stored rows. evidence_lines hold
  every stored row as "cell | cell | cell".
- Year cells can list spans ("2002, 1999-2000 Chevrolet Silverado",
  "2016-2018, 2009-2014 Nissan Maxima"): one fitment row per span, same raw.
- Model names are as printed and coarser than our feed: GM trucks print
  "Silverado"/"Sierra" (1500/2500/3500 only in the option column), Ford
  "E-350/E-350 Super Duty". crawl.py's coverage check compares names, so GM
  truck segments spend their extra seeds; harmless, costs time.
- Column meaning differs by make: `options` is GM trims+body, Mopar trims,
  Ford transmissions/drive, Nissan/Infiniti engine codes. `trims` = options
  on GM/Mopar, empty on Ford, the "Trim" half of "Trim & Engine" on Nissan.
- Engine/trim cells are the site's per-row aggregates and are sometimes
  wrong: Infiniti 16119-8J103 lists FX45 as "6 Cyl 3.5L"; 23100-JK01A lists
  2011 G25 as "6 Cyl 3.7L". Treat engines as hints; split engine-specific
  parts (alternators, starters, throttle bodies) by the list page's
  "Fitting Vehicle Options" codes, not by these cells.
- Position: the parts-list row's side wins ("Location: Driver Side", Mopar
  bare "Right"/"Left", Infiniti "RIGHT BANK" = engine bank), then the
  product page's own side. Mopar product pages contradict the catalog row
  (1AN401BGAD: list "Right", product page "Driver Side"/"Door Mirror Left");
  such records get position None and a "position conflict" flag. GM product
  pages carry no side at all. The side is the seed vehicle's list row.
- Reman rows are dropped only when the page says so (Remanufactured,
  Refurbished, Core Return) and a new number is on the same page. Mopar
  R-prefixed numbers listed without that text (R5233006) are kept, as are
  Ford Motorcraft service numbers ("High Level Aftermarket Spec / Non
  Warranty Repair", G2MZ-...) and Ford crash-part duplicates (-ACP, -PTM
  suffixes): each is its own number with its own fitment.
- `replaced_by` is raw: it can be a reman number (Mopar R6027702AC) or
  Nissan's "(MultiSupersession)" marker, which is not a part number.
- Window regulators include motor-only rows (README). Nissan door modules
  that carry the regulator ("Module Assy-Front Door", 2012 Altima front) are
  NOT included; only rows named Regulator / Motor Assy-Regulator.
- Window switch: GM rows without a printed side are kept unless they say
  passenger/rear, so some aux switches appear; names keep "MASTER", "2 BUTTON".
- Catalog choice: at most 2 catalogs per model-year. Variant maps per module
  (GM 1500_2wd/4wd, classic/new_style, carryover/new_model; Nissan
  sedan/coupe; Ford gas/hybrid). Ford splits some years by engine +
  transmission (/2001-ford-f_150--6_cyl_4_2l-4at_4r100-parts.html): first and
  last option catalogs are read (smallest and largest engine).
- Coverage gaps seen: no HVAC control head on 2000 Silverado catalog pages;
  Plymouth is not on moparpartsgiant (404), Plymouth segments nav-fail;
  infinitipartsdeal has no G35 sedan catalog for 2003-2006; Nissan "Pickup"
  maps to hardbody_pickup_d21 (1986-1994 only); Ford F-100 and Chrysler
  "Caravan" have no site model. Worklist segments that start before the
  model existed (Cruze 1986, Ram 1500 1971) nav-fail on those seeds.
- Tier B rules exist for all five sites but only tier A was trial-crawled;
  tier B rules were checked offline on one vehicle per site (2012 Malibu,
  2010 Escape, 2010 Grand Caravan, 2012 Altima). Grille rules found no grille
  on the 2012 Altima pages.
- For the Honda/Acura/Hyundai/Kia/Subaru/Lexus modules: the template already
  follows per-trim catalogs (first + last trim), takes callable rules
  (rule(row, text)) and a head_fn hook for sites whose group text is an
  illustration label (GM).
