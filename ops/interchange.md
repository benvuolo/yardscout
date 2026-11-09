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
### Aftermarket track (cont., session_016ZzJfJ6BcW6cQfYXpnSYuV)

- Full-pass size (listing-only count, 2026-11-05 01:25 UTC): alternators 56
  make pages + 715 model pages; starters 69 make + 802 model pages. Make-page
  pagination tops out at 6 pages (72 items) for the biggest makes, so the
  model pages are what reach the full catalog. Product pages: est. 1-3k per
  category (de-duplicated by URL). Total est. 3.5k-7.5k requests; observed
  ~8-10 s per new request (4 s gap + server time), so ~8-20 h, i.e. ~16-40
  thirty-minute slices. Run: `run.py --site www.dbelectrical.com --minutes 28`
  (exit 10 = resume, 11 = network pause, 3 = blocked, final). Persist
  `aftermarket/raw/` between slices (like `raw/` on oem-raw).
- Stopped 2026-11-05 ~01:30 UTC. Waiting on the hub for the Actions job.
- 01:15-01:20 UTC: GM, Ford, Mopar, Nissan, Infiniti crawling (run
  41946917524). Aftermarket: DB Electrical crawling (oem-aftermarket-crawl.yml,
  run 41947368495); Denso (POST to a nonce-protected search endpoint) and TYC
  (client-side API on another domain) stay out. fetch.py robots fix
  (1a769a1): urllib.robotparser kept only the first `User-agent: *` group;
  now an RFC 9309 reading also applies, stricter wins; no allowed site's
  URL patterns were affected. dbelectrical robots.txt carries Cloudflare
  Content-Signal "ai-train=no": we do not train on it (owner informed).
  Mopar/Nissan/Infiniti session re-tasked as raw-output auditor (AUDIT.md)
  + tier B rule review (proposals to the hub before edits).

### Hyundai + Kia (session_016ZzJfHkeNBsfhhGE3jys2o, 2026-11-05 01:40 UTC)

- Modules on main: `sites/hyundaipartsdeal.py` (ee0f155) and
  `sites/kiapartsnow.py` (4ddc927), with tests `test_hyundaipartsdeal.py`
  (38 checks) and `test_kiapartsnow.py` (14). Kia reuses Hyundai's SUBCATS,
  PARTS, ENGINE_RX and reman_fn (same Hyundai-group part names and PNC codes).
  Template addition (additive): `Config.engine_rx`. Reman uses the upstream
  `reman_fn`.
- Trials (tier A, 2 segments, through fetch.py, no refusals): Hyundai 119
  records (Sonata 2011-13, 2006-10), Kia 131 (Soul 2010-13, Optima 2011-13),
  0 errors, 0 flags. Every record was checked field by field against the
  cached page's visible text (pn, description, position, replaces,
  replaced-by, every fitment row and cell): 250/250 match. Records were also
  re-derived after rebasing onto the Honda/BMW template changes: 0 differences.
  Rules were also checked offline on 2004 Santa Fe and 2007 Sportage names.
- Not crawled yet: everything beyond the 2 trial segments per site, and all
  of tier B (tier B rules only checked offline on the 2011 Sonata).

Curator notes
- Part numbers: Hyundai prints "37300-2G600", Kia "373002G600" (same
  number). Strip "-" before matching Sonata/Optima, Tucson/Sportage,
  Elantra/Forte, Santa Fe/Sorento twins. Each catalog lists only its own
  make (no cross-make rows seen), so twins are found only this way.
- Reman: list rows never say reman; only the pn suffix does (Hyundai
  "-RM", Kia "RU"). The product page names it ("Reman Compressor"). Reman rows
  are dropped when a new number is on the same page. Kia often supersedes a
  new number to its reman twin ("Replaced By: 373002E300RU"); that is the
  same part family, not a different part.
- "Trim & Engine" cells are usually engine-only ("DOHC - TCI/GDI",
  "2.0L - Theta 2") and go to `engines`. Older catalogs add trims
  ("High Grade, Middle Grade|DOHC - MPI"), which go to `trims`. The option
  column is body style ("Sedan - 4Door 5P") in `options`, verbatim, including
  odd rows (a Forte Koup row lists "Sedan - 4Door 5P").
- Year spans can be wider than US model years: YF Sonata parts print
  "2009-2014 Hyundai Sonata". Recorded as printed.
- Window regulator: on door-module cars (2011+ Sonata/Optima, 2001-06 Santa Fe)
  the catalog has no separate regulator number. The regulator is sold as
  "Panel Assy-Front Door Module" / "Panel Assy-Front DR Module" / "Module
  Panel & Reg Assy-Front Door". Those rows are KEPT under window-regulator,
  names as printed (unlike Nissan, where modules are excluded because
  separate regulators exist). Motors are their own rows.
- Fuel pump: "Fuel Pump & Sender Module Assy" / "Complete-Fuel Pump" (31110)
  are kept. "Sender Assy-Fuel Pump" (94460) is the level sender and is not
  kept.
- Position: the list row's "Location: Driver Side" wins. Kia product pages
  sometimes print another word for the same part ("Rear Driver Side" on
  outside mirrors, from "RR View"; "Front" on window motors); both lines are
  in evidence_lines. Master switches have no list Location, so position is
  the product page's "Driver Side".
- Liftgate: SUV/hatch rear doors are "Tail Gate" in these catalogs and are
  mapped to `liftgate`; no `tailgate` rule (no pickups in the worklist).
- Variants (max 2 catalogs/year): Hyundai Sonata/Elantra/Accent exclude
  "korean" market catalogs (Sonata 2005 has new_body_style_korean / _us /
  old_body_style). Kia Optima 2011-15 crawls korean_made + us_georgia_made
  (both US-sold); Sorento 2006 prefers old_body_style; Spectra prefers sedan.
  Rio5 and Forte5 have no catalog of their own and map to rio and forte. The
  coverage check compares model names, so those segments use all 3 seeds.
- Electric-steering cars have no P/S pump page (2011 Sonata): no record, not
  an error.

### Subaru, Lexus, BMW navigators (session_016ZzJfJPMiqWBVeGP97xHiL, 2026-11-05)

- Modules on the .html template: `sites/subarupartsdeal.py`,
  `sites/lexuspartsnow.py`, `sites/bmwpartsdeal.py`; offline tests
  `tests/test_subarupartsdeal.py` (52 checks), `test_lexuspartsnow.py` (46),
  `test_bmwpartsdeal.py` (48). lexuspartsnow is the .html template, not
  SimplePart. Template additions (defaults unchanged): `Config.reman_re`,
  `Config.option_col`, `Config.bare_list_position`.
- Trials (tier A, 2 segments), every record checked field by field against
  the cached pages' rendered text by an independent checker (pn, description,
  position, replaced-by, replaces, fitment header, each rendered row, and
  years/make/model/engines/trims/options against raw; it caught 4/4 planted
  corruptions): Subaru 137/137 (Outback 2011, 2005; 0 errors), Lexus 274/274
  (ES 300 2002/1999, RX 300 2000; 2 nav-fails = ES 300 2004 and RX 300 2006
  do not exist), BMW 99/99 (328i 2011, 325i 2006; 2 nav-fails = 328i 1955
  and 325i 1997, pre-clamp worklist bounds). The BMW check first found 32
  climate records with position "Front" from a list note ("Front panel,
  control"); fixed (`bare_list_position=False`) and re-verified.
- crawl.py dedupes (category, pn) across segments, so a later segment that
  shares parts with an earlier one shows few records (2006 325i E90 shared
  every starter/regulator/switch/P/S pump pn with 2011 328i; RX 300 2000
  shares its starters with ES 300). That is interchange, not a miss.

What a curator must know:
- Subaru: one catalog per model-year; Legacy and Outback share diagrams and
  each list row carries "Fitting Vehicle Options" (S / W / OBK body codes,
  engine 253/255/36D/EJ25#, trim codes) verbatim in `list_info`. The option
  column holds trims (`option_column_is_trims=True`). Paint variants are
  separate pns ("Mirror Assembly-Door,Left(BLACK MICA)"; 50 mirror records
  for 2005 Outback). Tail lamps: up to ~2009 "Lamp Assembly-Rear
  Combination"; 2010+ only "Lens & Body-Rear Combination Lamp" is listed
  (the lamp housing; kept, name as printed). "Rear Finisher" liftgate lamps
  excluded. Fuel module = "Pump Assembly-Fuel"; bare "Pump-Fuel" excluded.
  Throttle bodies sit on the intake_manifold page (2010+) or throttle_chamber.
  Some Subaru product pages print fitment the parser keeps as is even when
  odd (2010-11 Outback "2.5GT" trims on shared Legacy/Outback numbers).
- Lexus: Toyota EPC names in the list ("Unit Assy, Headlamp, RH" and
  "Headlamp Assy, RH" are both listed, different pns; both kept). Product
  pages: mainDesc is an SEO name ("Alternator Compatible"); `description` is
  the page's Part Description ("ALTERNATOR Assembly"). Fitment "Trim &
  Engine" holds the engine only; options = engine code; model code
  ("1MZFE; MCV30L-BEAGKA"). Models print without a space ("ES300").
  Mirrors are "Mirror Sub-Assy, Outer Rear View" (painted head; kept).
  "Lens, Rear Combination Lamp" alone is excluded (README lens only), so
  2002 ES 300 has no tail-light record. No fuel-pump module on ES/RX pages
  (only "Pump, Fuel" bare pump and "Tube Sub-Assy, Fuel Pump" bracket; both
  excluded). Open question: 2002 ES 300 "Panel Sub-Assy, Air Conditioner"
  (55902, has a seat-heater variant) may be the climate head; excluded until
  someone confirms. Worklist bare series ("IS", "GS", "ES", "RX", "LS") have
  no catalog model and nav-fail.
- BMW: year catalogs per submodel (sedan_n52_engine_e90, wagon_e91,
  n20_engine_f30); sedan variants first, at most 2 per year. Submodel column
  ("Sedan N52 Engine(E90), Wagon(E91)") is in `fitment[].options`. "Exch."
  / "Exchange" = BMW reman: dropped when a new pn is on the page (starter),
  kept when it is the only listing (2011 328i alternator 12-31-7-555-926).
  Mirrors are sold "w/o glass" (kept). Sedan trunk lids print "Tailgate
  with/without hole for lock barrel" (trunk-lid page). Both tail lamps (side
  panel and trunk lid) are tail-lights. E90 fuel page lists only repair kits
  and senders: no fuel-pump module record. List pages print pns without
  dashes, product pages with dashes. "3/5/7 Series" have no catalog model.
  Not in evidence_lines: the product page's "Manufacturer's Notes" ("This
  part is discontinued."); template owner may want it.

### Honda + Acura (session_016ZzJfHdymdThBbtJ5HYPnQ, 2026-11-05 01:45 UTC)

- Modules: `sites/hondapartsnow.py`, `sites/acurapartswarehouse.py` (thin), shared
  rules in `sites/_honda_names.py` (both catalogs print American Honda's part
  names). Tests: `tests/test_hondapartsnow.py` (29 checks), `tests/test_acurapartswarehouse.py` (18).
- Template: opt-in `Config` fields `trim_pick`, `trim_col`, `reman_fn` (all None by
  default). GM and Ford parsed output was compared old vs new on 3 pages per site:
  identical.
- Trials (tier A, 2 segments): Honda 81 records (Accord 1998-2002 seed 2002,
  2003-2005 seed 2003), Acura 153 (TL seeds 2005/2003/2010, MDX seed 2005), 0
  errors, no refusals. Every record was checked field by field against the cached
  pages by an independent checker (pn, name, description, Position, Replaces /
  Replaced By, every fitment row and cell incl. the store rows behind "View More",
  evidence lines): 234/234 match.

#### Honda family: what a curator must know

- Navigation is per trim catalog (`--4dr_exl_v6_navi-ka_5at`). The crawler reads two
  per year: base and best-equipped. Both come from one body style (4dr when the year
  has one), 49-state (KA) and automatic when available. CNG (GX), Alaska/Hawaii,
  PZEV/SULEV/ULEV and plant sub-builds are skipped. So a 4dr-only pick can miss parts
  that only the coupe carries, such as coupe headlamps.
- Fitment columns: "Year Make Model | Body & Trim | Emission & Transmission". Body &
  Trim goes to `trims` ("4 Door EX-L (PZEV)"); Emission & Transmission goes to `options`
  ("KA 5AT"). There is no engine column. V6 shows up only in trim names ("4 Door EX-L
  V6", "4 Door EX-V6"). Honda prints one row per year.
- Position: Acura product pages and many Honda ones print "Position: Driver Side /
  Passenger Side / Front Passenger Side", and the record keeps it verbatim. The name
  always carries side and position too ("R." / "L.", "FR." / "RR."). Some pages print
  "Driver Side Passenger Side" on a left mirror (76250-S84-A31ZJ). Those records get
  the flag `position names both sides`, or `position ... contradicts name` when
  Position and the name's side disagree. Trial records predate the flag.
- `name` is the list row. `description` is the product page's Part Description
  ("Turn & Stop Lamp", "Window Switch", "Dash Control Unit"). Classify by `name`.
- Reman: "(RMD)", "Core Id", or a pn ending in RM. Dropped when a new number is on
  the same list page, kept otherwise. 2005 MDX power-steering pump: only the reman
  06561-RDJ-505RM is listed.
- Coils are "Coil, Plug Hole". The module removes "Plug Hole"/"Plug Top" before the
  template's COMMON_EXCLUDE (which would drop "plug").
- Window switch: "Switch Assy., Power Window Master". The 2003-07 Accord prints its
  driver switch as a bare "Switch Assy." (35754-SDA-306; product page: Window Switch,
  Driver Side, replaces 35750-SDA-A12). It is kept only from a front door lining
  diagram and carries `list_flags` for curation.
- Tail lights: "Taillight Assy.", "Lamp Unit, R./L. (Tail)". The 2003-07 Accord has
  two per side: 33501 "Turn & Stop Lamp" and 34151 "Tail Lamp" (likely the trunk-lid
  section; the page doesn't say). Both are kept.
- Climate control: "Control Assy., Heater / Auto Air Conditioner"; 2009-14 TL splits it
  into "Switch Assy., L./R. Auto Air Conditioner" (both kept). Rear controls, knobs and
  the A/C computer are excluded.
- Honda's "Tailgate" diagram: Ridgeline goes to tailgate, every other model to
  liftgate.
- Civic Hybrid (and Accord Hybrid, if added to the worklist) is crawled through the
  Civic catalog's hybrid trims. Its fitment prints "Civic", so crawl.py's coverage
  check never marks those years covered.
- Fitment blocks list sister models: Accord coils also fit Crosstour/Odyssey, Acura
  alternator 31100-RJA-A02 fits MDX/RL/TL. Model names are as printed.

#### Known gaps (nothing invented)

- 2003-07 Accord climate control is part of the combined radio/HVAC "Module Assy.,
  Center"; the 2005 TL's is part of its center display module. Neither is filed as
  climate-control.
- No single grille assembly in several catalogs (2008 Accord, 2007 Odyssey "Base,
  FR. Grille", 2005 TL mesh only).
- 2010 TL has no power-steering-pump diagram. 1997 Accord DX has no starter diagram.
- Distributor-era ignition (pre-1998 Accord, 2002 Accord DX): no coil diagram.

### SimplePart "giant" variant: VW, Mazda, Mercedes-Benz (session_016ZzJfHbzhf7ZAm4Xt8ok79, 2026-11-05)

Modules: `sites/vwpartsgiant.py`, `sites/mazdapartsnow.py`, `sites/mbpartsgiant.py`,
all on `_simplepart.py`. These stores use `/<year>-<make>-<model>-parts` year pages
and `/genuine/` product pages, and print only a short site name per list row. So
rules are anchored exact names on each category's own pages. Where the list page
cannot tell, a product-page check decides (`product_rules`, matched text kept in
`product_check`).

Trials (tier A, 2 segments). Every record was checked field by field against
the cached page:

| site | records | match | notes |
|---|---|---|---|
| vwpartsgiant | 108 | 108/108 | |
| mazdapartsnow | 128 | 128/128 | |
| mbpartsgiant | 117 | 117/117 fields | 1 record `evidence_truncated:158` (a 54-row table; fitment complete, evidence capped at 120 lines) |

Curator notes:
- **Site mislabels caught by product checks.** Mazda L39C-18-881J is listed as
  "Alternator" but its product page says "Module, Powertrain Control". MB
  271-155-01-15 is listed as "Alternator (5.5L)" but its product page says
  "Pulley" and its fitment is the C230 1.8L. Both are now excluded:
  alternator/starter rows must agree with their product page.
- **Not crawled, because the page does not print what the category needs:**
  - VW door shells ("Door Frame Assembly" / "Door Inner"; front vs rear never
    printed).
  - MB door shells (even the passenger shell reads "Driver's Door").
  - MB fuel pump ("Auxiliary Pump" / "Exchange Suction Jet Pump").
  - MB mirrors ("Mirror Housing" = "Frame").
  - MB climate control (only generic "Switch Assembly" / "Control Module").
- **Mazda door shells are crawled.** The product page prints "Body(Right),
  Rear Door", and that text decides door-front vs door-rear.
- **Mirrors carry a `category_note`.** VW lists the mirror as "Housing
  Assembly" / "Mirror Housing" (product "Housing" or "Repair Kit"). Mazda
  "Mirror Assembly" rows can read "Sub Mirror(Left/Right), Door". Neither page
  says whether glass and cap are included.
- **Fuel pumps.** A plain "Fuel Pump" row can be the engine's high-pressure pump
  (VW 06F-127-025-M, Mazda L3K9-13-35ZC), so only "Fuel Pump Assembly" is taken.
- **Window switch.** Mazda and MB keep only switches whose product Position is
  "Driver Side". VW and Jeep keep both sides, with a `category_note` saying so.
- **Reman.** A number is reman only if every list row for it says so. VW prints
  06F-903-023-FX on a "New" row and on a "Remanufactured" row. Mazda and MB mark
  reman only on the product page (`other_names` "Reman Alternator"), so those
  rows carry `reman: false` from the list page.
- **Mazda model slugs.** "Mazda3" maps to `3`, CX-9 to `cx_9`. MX-5 Miata is
  `miata` through 2005 and `mx_5_miata` from 2006. The feed's "B-Series" and
  "Truck" map to no single catalog model (b2300/b3000/b4000 by engine), so they
  fail navigation instead of guessing (156 cars).
- **MB class names are expanded to badges.** A feed class name ("C-Class",
  "SLK", "300") is crawled through every badge of that class whose model page
  lists the year. Fitment prints badges ("C300", "C63 AMG"), and the seed model
  stays the class name. crawl.py's coverage check cannot match class to badge,
  so these segments use all 3 seeds.
- 02:03-02:18 UTC incident: with ~14 separate Actions runs (one per site,
  4 s per site, ~3.5 req/s across the dealer network), Toyota, Jeep and
  Mopar timed out at 02:03-02:05, vwpartsgiant answered HTTP 503 (02:04) and
  moparpartsgiant HTTP 403 (02:18). The breaker stopped both; their .blocked
  markers on oem-raw stay (no retries without an owner decision). Response
  (b23fd65): 8 s per site, ONE capped run for all sites (max-parallel 8,
  ~1 req/s network-wide), all separate runs cancelled (<= 1 slice lost per
  site), 15-minute cool-down, then a single "all" dispatch. Records on
  oem-raw at 02:30: 8,084 across 17 files.
- 02:25 UTC: CURATION_SPEC.md landed (24c031b; build/review stopped on the
  account's 5-hour usage limit). Hub workflow wf_9b3745bc-31f now builds three
  tracks on branches: Phase 0 guards + hybrid fix, crawler R1/R2/R4/R5/R6,
  offline curation pipeline. Owner questions are in CURATION_SPEC.md §13.

### Mitsubishi, Volvo, Audi (session_016ZzJfL2a85N1tgt5nnonXc, 2026-11-05)

Modules `sites/mitsubishipartsgiant.py` (d4b38a8), `sites/volvopartsgiant.py`
(fbfddf7), `sites/audipartsgiant.py` (4c57cb7 + side-mirror note), shared subclass
`sites/_sp_slugrules.py` (SlugCheckedSimplePart), template option
`slug_checks` (additive, default off). Tests `tests/test_mitsubishipartsgiant.py`
(46 checks), `tests/test_volvopartsgiant.py` (32), `tests/test_audipartsgiant.py`
(32); page checks are cache-only and skip in CI.

Trials (tier A, 2 segments). An independent checker re-read each cached page
(rendered text + embedded store): pn, list name, position, replaces /
replaced-by, every fitment cell, year spans incl. multi-span cells, evidence
lines.
- Mitsubishi (Lancer 2008-17, 2002-07): 47 records, 0 errors, 47/47 match.
- Volvo (XC90, S60): 100 records, 1 nav miss (the catalog has no 2010 S60
  page, HTTP 404), 100/100 match.
- Audi (A4 seeds 2008/2001/2018, A6 seeds 2008/2004/2014): 183 records,
  0 errors, no refusals (8 s/site pace), 183/183 match.

What a curator must know (all three are the "giant" SimplePart variant):
- **Strict selection.** List names are site names and they are loose
  (Mitsubishi lists bolt 7812A133 as "Dehydrator"; Volvo 850 lists a fuel
  gauge as "Cluster"). A row is kept only when the list name AND the
  product URL's name slug both name the assembly. Exclusions and the reman
  test also read the slug.
- **Reman / exchange.** `reman: true` comes from the list page (notes, name,
  slug "remanufactured-starter") or the product page's own names
  (Mitsubishi M984944D "Remanufactured Alternat", Volvo 8251551 "Reman
  Starter"). Volvo "Alternator, Exchange" gets `exchange_unit: true`. Audi
  X-suffix numbers are exchange units, but their product pages do not say
  so; nothing is inferred from the suffix. Their list rows print
  "Remanufactured", so they drop when a new number is on the same page.
- **Window switches** never say "master" on any of the three. All
  front-door "Window Switch" rows are kept; filter on `position` /
  `list_location`.
- **Doors.** Mitsubishi and Volvo: door-front / door-rear are decided by the
  product page's own name ("Panel Assembly, Front Door, Left-Hand"; Volvo
  "Front Door"), kept in `product_check`. Audi: not crawled; list "Door
  Shell" and product "Door" never say front or rear.
- **Lamps.** Mitsubishi and Volvo "Lens & Housing" rows are kept with the
  assemblies. Their OEM names are "Body, Headlamp" and "Lamp Unit, Tail" (the
  unit without bulbs/sockets). `name` keeps the printed list name.
- **Mirrors.** Volvo "Mirror Outside" numbers are mostly paint variants.
  Older Audi catalogs (2008 A4) sell only mirror parts ("Mirror Housing" =
  cap, "Motor & Base") and give no record. Newer ones (2012+ A6, 2017+ A4)
  list "Mirror Assembly", whose Audi name is "Mounting". Those are kept with a
  `category_note`: whether glass and cap are included is not printed.
- **Mitsubishi coverage gap.** Multi-trim list pages ("Select your vehicle
  options") do not always embed every diagram's rows. The 2008 Lancer
  alternator page has only the components, not the assembly. Missing rows
  are a coverage gap, never a guess.
- **Volvo.** "Tail Gate" pages are the wagon/SUV hatch and go to `liftgate`.
  Trunk lids ("Lid" on the list) are confirmed by the product name "Trunk
  Lid". "60 Series" (15 cars) names no catalog model, so navigation refuses
  it. Numbers without fitment rows get fitment [] and `no_fitment_rows`.
- **Audi navigation.** The catalog files the A8 after 1999 and the 2001-05
  allroad only as `a8_quattro` / `allroad_quattro`, so those feed years
  navigate there. Fitment model names stay as printed ("A8 Quattro"). A5
  navigates only for 2010-14, where the catalog has `a5`. The Audi
  condition (SOURCES.md) was checked before building: 21/21 list-linked
  product pages carry fitment in the server HTML. The scout's 3
  fitment-less samples were reached outside the catalog (one redirects to
  the home page).
- **Audi fuel pump.** "Fuel Pump" with slug `fuel-pump` is the engine
  high-pressure pump (06E-127-025-AB) and is excluded. Only in-tank
  assembly slugs are kept.
- **Audi rendered tables** can drop an empty cell (2013-2018 A6 Quattro
  with no Engine on 06F-133-062-AG) and print double spaces ("2020,  2015-2017").
  The fitment entry keeps the empty cell (`engines: []`, raw ends "| ").
- **Cross-make**: none in these catalogs. Cross-model is common (Mitsubishi
  Lancer/Outlander/Outlander Sport; Volvo P2/P3 platform S60/S80/V70/XC70/XC90;
  Audi A4/A5/A6/Q3/Q5 2.0T throttle body, A4/A6 starters).
- Status: all three modules are on main and the trials are checked. Mitsubishi
  and Volvo are in the hub's capped Actions run. Audi is ready for it.

### Raw-output audit (session_016ZzJfLtcR8MerD7PWDQVoN, 2026-11-05 01:14-03:45 UTC)

- `scraper/oem_fitment/audit.py`: an offline auditor with its own parser. It
  re-reads each record's evidence_lines (PartsGiant, SimplePart, DB
  Electrical) and reads only the sites' declared CFG conventions. Run it at
  each checkpoint: `git show origin/oem-raw:raw/<site>.jsonl > x.jsonl;
  python3 scraper/oem_fitment/audit.py --table x.jsonl`. Tests:
  `tests/test_audit.py` (44 checks, single-field corruptions on 4 fixtures).
  Its category check (C) is a heuristic: read hits by hand. Only E
  (evidence) is a hard failure. Results and every hand-read pattern are in
  `scraper/oem_fitment/AUDIT.md`.
- Result through 03:43: 17 sites, about 11,500 records, 0 evidence
  mismatches. Two wrong-category records, both on AUDIT.md's "Exclude at
  curation" list with their rules fixed: LBK13001 (Mopar bulb kit) and
  5143152AA (Jeep headlamp boot).
- Rule fixes that came out of the audit and tier B review, hub-approved, in
  site modules only, each with a regression check:
  - 695b378: Mopar bulb kit, door shells, fender, coils, deck-lid opening,
    accessory kits, Magnum liftgate; Infiniti/Nissan G35 "Meter Assy-Analog"
    cluster.
  - 3947d2e: GM Equinox cluster and coils, Silverado door shells; Jeep boot.
- Not done: the manifest check (every pn in a lists/years manifest row with
  matched=true). R1/R2 manifests had not reached oem-raw by 03:43; add it
  to audit.py when they do.

### Crawler requirements R1-R7 (CURATION_SPEC §3.2; workflow subagent, 2026-11-05 ~03:15 UTC)

On branch `worktree-wf_9b3745bc-31f-2` (not merged, not pushed): 23d37e0,
519dd0b, 9acadec. Everything is in `scraper/oem_fitment/README.md` ("Site
module contract", "Raw files"). Once on main, the next scheduled crawl runs
pick it up.

- R1 `raw/<site>.lists.jsonl`: one line per list page read (not subject to
  the products_seen dedup, so R7 holds), every partList/gpgOnly row (and
  PartsGiant Standard Parts rows, `section_not_read`), notes as structured
  `extra`, `matched` / `excluded_by` / `product`. Re-read from the cache:
  0 extra requests (tested).
- R2 `raw/<site>.years.jsonl`: one line per year-catalog page read, every
  sub slug, title, status, redirect; PartsGiant lines list every offered
  variant and option catalog, read or not, plus the list pages read from each.
- R3 completion mode is implemented (`crawl.py --complete <worklist>`), not a
  stub. The workflow does not call it yet.
- R4: chains followed to depth 4 only through catalog links: a list row for
  that number on any page this crawl read (`via_link: "list_row"`), or a link
  on the referring product page (`"product_page"`). This goes one step past
  the spec's "gpgOnly rows" by using rows from every page read (URLs are
  pn-specific product pages; never built). Real product pages (Toyota, GM,
  Ford) do not link their Replaces / Replaced By numbers, so most chain
  members stay `chain_unlinked` (2009 Camry mirror 87910-06925 names 14
  predecessors, none linked). C5 keeps those cells open, as designed.
- R5a qualifier phrase removal applies to SimplePart (Toyota, Jeep, VW,
  Mitsubishi) and to the Subaru, Lexus and BMW rules (same `QUALIFIER` copy,
  now shared). It can only add rows whose include rule already matched.
- R5b on BOTH templates. PartsGiant part dicts now carry `reman`. Effect:
  remans next to a superseded number are kept, e.g. Kia pages that supersede
  a new number to its RU twin now keep the RU row (marked reman).
- R5c Toyota `-84` is reman (basis in toyotapartsnow.py).
- R6 `recrawl_of` (string line number) on any record for a (category, pn)
  already in raw. `.jsonl` files continue in `.2.jsonl` etc. at 40 MB (GitHub
  limit; real list lines are 10-19 KB, so GM would pass 100 MB); a torn last
  line is cut at start. The workflow's `raw/<site>.*` copy already covers all
  of it (checked; header comment updated).
- Record output check: the old and new code on 30 trimmed real pages
  (Toyota, GM, Ford; `tests/fixtures/crawler/golden_records_v0.json`) differ
  only in the two R5 cases (2007 Camry alternator: 4 remans kept beside
  27060-28320; 1999 Camry starter: 28100-74260-84 kept, 28100-74270-84
  reman) and the new PartsGiant `reman` key.
- Live fetches for fixtures: 10 toyotapartsnow pages via fetch.py, 10.5 s apart.

Open, for the hub:
- Seeds crawled before this lands have no manifests and no chains. Backfill
  with `--complete` rows for the done seeds (cost: year + list pages, plus
  the catalog-linked chain hops of their matched numbers; products already
  seen are not re-fetched). Resetting progress also works but re-fetches
  every product (R6 marks them).
- Lexus (lexuspartsnow, PartsGiant template) uses Toyota numbering but has no
  `-84` reman rule; Ford `...RM` numbers ("Ford Retail Spec", 4L3Z-10V346-BBRM)
  are not flagged reman. Both outside R5c; §5.4 syntax covers neither.
- The spec's example "Headlamp Unit Assy, W/Auto Leveling" fails Toyota's
  headlights include rule itself (R5a cannot help); the EPC form "Unit Assy,
  Headlamp, W/Auto Leveling" is kept now. Whether that wording occurs is for
  the Toyota builder to check.
- A seed retried after a list-page network failure writes its manifest lines
  again (same rows). A list line counts as read only when `read` is true
  (status 200, no `error`, no `rows_missing`); a status-200 line with an
  error (an error page, a failed product-rule fetch) is `read: false`.

#### Review fixes (workflow subagent, 2026-11-05; same branch, merged with main 793eff6)

Commits 5859af9, 7e6e300, aa8e5f6 and the docs commit after them. Tests:
`tests/run_all.py` 28/28 files (cached-page checks skipped: no local cache).
- Merge with main: Mitsubishi keeps main's SlugCheckedSimplePart plus the
  manifest exports. audipartsgiant, mazdapartsnow, mbpartsgiant and
  volvopartsgiant now export year_manifest / list_manifest / chain_links
  (before: every list line from them had `rows: []`; Mercedes is crawling).
  SlugCheckedSimplePart.product takes `_get`, so product-rule categories
  (Volvo / Mitsubishi doors, Volvo trunk lid) no longer fail with TypeError
  in list_manifest; the slug test is `excluded_by: "rule:slug_miss"`.
  Mercedes year lines are per badge page actually read (C-Class -> c300,
  c63_amg ...), not the slug of the class name.
- A number first reached as a chain record is no longer "seen" for list
  pages: when a later page lists it, its listed record is written with that
  page's seed / list_url / list fields (`recrawl_of` -> the chain record).
  Before, the only record was the chain record (name null, no reman flag,
  another vehicle's seed and list_url).
- `read` flag on list lines (above); list-fail rows keep the template's
  verdict (no `site_module` relabel); progress `list_fail` names the pages
  for a later `--complete` row. Seeds are still marked done on list-fail:
  fetch.py caches the error page, so an in-job retry re-reads it.
- R4 chain work is persisted (`chain_pending`) and resumes after exit 11 /
  Refused; listed rows recorded before R4 get their chains followed when a
  page lists them again (both modes, incl. `--complete` backfill);
  `chain_failed` / `chain_given_up` count dropped hops. `.done` is written
  only when no chain work is owed (exit 10 otherwise; a hop is given up after
  3 network failures).
- `rawparts.py` is the one reader for size-capped parts. ci_audit.py (now
  `--site`, the workflow's call) and audit.py read every records part, so
  the >0.5% pause gate keeps covering records past 40 MB.

Open, for the hub:
- The curation adapters (branch `worktree-wf_9b3745bc-31f-3`, `curate.load`)
  read only `raw/<site>{.jsonl,.lists.jsonl,.years.jsonl}`. They should read
  through `rawparts.site_rows(raw_dir, site, kind)` and count a list line as
  read only when `read` is true. Not changed here (other workstream).
- AUDIT.md "Open for the auditor session": the C heuristic does not strip
  qualifier phrases, so R5a keeps show as category suspects (count only).
- A seed left open after a network failure is still orphaned once `.done` is
  written (unchanged from main).
## Curation pipeline (hub workflow wf_9b3745bc-31f, track 3; branch worktree-wf_9b3745bc-31f-3)

Offline, deterministic: `curate.py` (spec 4-6, 8-10), `adapters.py`,
`notes.py`, `positions.py`, `policy.py`, `model_map.json` + `model_map.py`,
`validate.py`, `measure.py`, payload hook `_attach_oem_layer` in
`build_interchange_payload` (new keys `oemGroups` / `oemVg` / `oemStatus`
only; no groups files -> payload unchanged; an invalid file drops its
namespace and says why in `oemStatus`). Tests:
`python3 scraper/oem_fitment/curation_tests/run_all.py` (12 files, one block
per spec 9 rule; the Phase 2 node parity prints SKIP: no OEM-TIER block yet).

Run: `curate.py --ns all --raw-ref <sha> [--propose-map] [--write-groups
--out DIR]`, then `measure.py --groups DIR --reports <_report> --parity`.

Result on oem-raw@50ac4a48 (2026-11-05 13:10 UTC, 25,164 records), reports
committed in `scraper/oem_fitment/groups/_report/` (no `groups/<ns>.json`
committed: the first merge per namespace waits for the owner's review of
`_report/<ns>.md`, spec 11.5):

| ns | Verified | Likely | gates (each alone blocks Verified) |
|---|---|---|---|
| toyota | 0 | 1,057 | no R1/R2 manifests; no audit; lexuspartsnow blocked, option layout, engines unaudited |
| mopar | 0 | 320 | no R1/R2; no audit; moparpartsgiant blocked, trims-in-options unaudited |
| gm | 0 | 842 | no R1/R2; no audit; options-as-trims unaudited; engines unaudited |
| ford, nissan, hmg, honda, subaru | 0 | 923 / 843 / 404 / 29 / 553 | no R1/R2; no audit; option column on ~every row; engines unaudited |

- Funnel (lot car x category cells): not closed (no year manifest) 2.96M,
  no records 1.80M, unmapped 324k, ambig target 79k. With closure assumed
  (labelled hypothetical, never shipped) the next stops are option_split and
  packaging_*, as spec 1 predicted. Completion worklists rank only Toyota
  and Jeep cells, because PartsGiant cells cannot become eligible (item 1
  below).
- measure.py (`coverage-2026-11-05.json`): M-car before == after in every
  category, the old-client view is unchanged (V9). The Likely groups add
  ~450M cross-model Likely car pairs. V11 drops 2,180 of 4,971 Likely groups
  to keep interchange.json under 1.3 MB. Body M-car matches spec 10.5
  (headlights 5,043, third-row 11,685, liftgate 5,001). Engine figures use the
  seeker's decoded family (alternator 121,971 = 36.4%). Parity: 6/6
  seeker/view counts equal a car-by-car transcription of pfRunSearch.

Needs a decision (hub / owner):
1. **Only toyotapartsnow and jeeppartsdeal can ever yield Verified under the
   spec as written.** Every PartsGiant site prints an option column on
   (nearly) every fitment row (Ford transmission/drive, Nissan/Infiniti engine
   codes, HMG body style, Honda/Acura emission + transmission; GM/Mopar/Subaru
   trims), and spec 5.5 never counts option-layout rows. Also, with
   ENGINE_CELLS_RELIABLE false (spec 4), every engine test there is maybe, so
   no PartsGiant record is cover yes in any category. Honda/Acura print no
   engine column at all. Unlocking any of them needs a per-site spec rule
   (which option values are not conditions) plus an audit.
2. **Payload size.** Shipping every Likely group overflows V11. Either lazy
   per-category OEM files (spec 12) or a Likely policy (e.g. only where no
   hand group exists).
3. Crawler R1/R2 manifests (crawler track) and the spec 11.4 audits are
   prerequisites for any Verified group. Until branch
   worktree-wf_9b3745bc-31f-3 (second review) the audit store
   (CATEGORY_STATUS) sat inside policy.py, which policy_sha256 hashes, so an
   audit record could never match a doc curated after it and V7 could not
   pass at all in production; tests got past it only by injecting a status
   table. The records now live in `scraper/oem_fitment/audits.json`, outside
   the hash (test_audit_store.py records one, re-curates and ships with no
   override). The payload loader now also enforces V8 (tree hash) and the
   model-map V2 check, so a groups file goes stale (namespace dropped) the
   moment policy.py / notes.py / positions.py / model_map.json change: every
   policy edit needs a re-curate before the next build ships OEM groups.
4. Ops alert on `oemStatus` "dropped" belongs to the backend ops workstream
   (`backend/src/ops_monitor.js`, spec 7.3); not filed there yet.

Fixed in review of the earlier commits (each with a test that fails on the
old code, `curation_tests/test_regressions.py`):
- An unparsed engine ("?", raw) printed on both sides passed the universe
  test and could ship Verified.
- A regulator name "W/Motor <anything>" was exempt from the qualifier check.
- Colour notes ("Lt Gray") were read as a side.
- Likely groups were emitted for classes outside the cell: the passenger
  switches 4602785AD and 4602540AF, and the "1 gang" 4602531AD, as Likely
  window switches.
- The evidence re-check refused doubled spaces, which AUDIT.md accepts.

Second review (21 findings, branch worktree-wf_9b3745bc-31f-3, tests in
`curation_tests/test_review2.py` and `test_review2_payload.py`, each failing
on be7a774): closure needs every merged catalog model (Wrangler JK 2018,
Grand Cherokee WK 2022 now have explicit years), a parsed year page and T's
own list stems; C4 re-runs the rule on every unmatched row; TrimU_f never
drops a year-page trim without proof; EngineU takes the year page's engines;
own-page notes come from every row of the number; a cross-category
supersession edge keeps blocking; chain records count toward evidence age;
the evidence re-check is exact (cells, header, both-way replaces, position);
audits.json (above); payload: OEM vg groups are withheld by a contradicted
hand vg, the engine-category §7.6 trigger reads family-narrowed
`engine_cells` and only real conditions (policy.SPLIT_CONDITIONS). On
oem-raw@50ac4a48 (toyota + mopar, every cell assumed closed, hypothetical)
the old trigger removed 55 of 468 hand vg groups, firing on evidence gaps
and on other engines' numbers; the new one removes 41, on option_split 240
member cells, conditional:trim 44, engine 5, plant 1, production 1. Most of
those option_splits are two numbers each printed for the family's own
engine (e.g. 4Runner/Tacoma 1996 alternators 27060-62180 and 27060-75170,
both rows listing 2.7 and 3.4), which is what §7.6 means. Like every
§7.6 demotion these fire only on closed cells (none today: no R1/R2
manifests). A withheld group takes the Likely note, V11 holds as
written, size_trim is linear, Likely groups and stale files expire, one
malformed file drops only its namespace, and a file without sigs / cells /
engine_cells is refused. Not re-run on oem-raw after these fixes: the
`_report/*.md` files still describe the pre-review curation.

AUDIT.md "Exclude at curation" (LBK13001, 5143152AA) is applied (refusal
`exclude_at_curation` in the reports). Hub decisions T1 and P1 are applied:
packaging switch-module / door-module, and the Likely notes say so.

Model map: drafted for every namespace with one identity rule
(`model_map.draft_identity`, merged with `model_map.py merge`; 227 -> 526
entries). gm/honda/hmg/subaru now map 81-99% of their lot cars. GM
series-split truck names (Silverado/Sierra/Suburban/Yukon/Express...) are
`ambig` (Likely only) and their feed sub-models are excluded. Acura ILX is
unmapped (M6: 3.1% of decodes name another make). VW, Audi, BMW, MB,
Mazda, Mitsubishi and Volvo have no namespace in spec 4 yet: reported as
`sites_without_namespace`, no claims.

## Hub decisions (curation policy)

- 2026-11-05 T1 (Toyota climate-control sub-assemblies 55901/55902/55903,
  e.g. 55903-12100 "Temp Control", 55901-12170 "Air Mode Control"): keep them
  in raw exactly as crawled; curation files them under climate-control with
  packaging "switch-module", a separate slot from full control assemblies
  (55900/55910). They can only ever match the same packaging, never a full
  panel.
- 2026-11-05 P1 (door modules): classify by what the puller removes. Where a
  catalog sells the regulator ONLY inside the door module (Hyundai/Kia
  "Panel Assy-Front/Rear Door Module"), keep it under window-regulator with
  packaging "door-module", matching only other door-module packages and
  carrying a note that it is the whole module panel. Where a catalog sells a
  separate regulator (Nissan), door modules stay excluded. Both rules give
  one answer: a seeker never gets a module offered as a bare regulator, or
  the reverse.
- Being listed on a vehicle's catalog page is not fitment; only the part's
  own fitment rows count (AUDIT.md: Ford DG1Z-10346-E, FJ7Z-10346-A, Mopar
  R5233006).
- 2026-11-05 12:20 UTC status: 29,242 records on oem-raw. Done (.done):
  Acura, Audi, BMW, Infiniti, Jeep, Mazda, Mitsubishi, Volvo, DB Electrical.
  Crawling: Toyota, GM, Ford, Nissan, Kia, Mercedes. Stopped by the breaker
  (.blocked): Mopar 403 (02:18), VW 503 (02:04), Hyundai 503 (07:40), Lexus
  503 (07:40), Honda 503 (07:44), Subaru 403 (10:26). Cause of the 07:40
  cluster: the 07:02 scheduled run overlapped the 02:43 manual run (~14
  sites at once). Fix e262ace: workflow-level concurrency (one run at a
  time) and max-parallel 6 (~0.75 req/s). Owner decision pending: whether a
  503 (service unavailable, clustered across sites) may be retried once
  after a cool-down at the slower pace; 403s stay stopped.
- 2026-11-05 14:35 UTC, owner: "do everything you think" (and keep token use
  lower: 25% of the week used). Hub decisions taken under it:
  - 503 sites get one retry: .blocked removed and .retried503 added on oem-raw
    for VW, Hyundai, Lexus, Honda (a2a83bd). A second refusal re-blocks them
    for good. Mopar and Subaru (403) stay stopped.
  - CURATION_SPEC §13 answers: (1) option splits stay Likely; (2) plant
    ("US/Japan built") may be matched to the VIN's first character, but only
    after its own audit sample passes (Phase 2); (3) vPIC trim may confirm
    trim-limited rows, Phase 2 with its own audit; (4) donors the catalog
    contradicts are hidden, with a count shown; (5) no OEM claims in the old
    keys before store apps ship the P0 guards.
  - No new multi-agent workflows; the two running ones finish.

## Phase 0 claim removals, CURATION_SPEC §7.2 P0.1-P0.6 (branch worktree-wf_9b3745bc-31f-1, 2026-11-05)

Not merged or pushed. Four commits (audit, data, app, this note), then a
review round: a merge of main (§23.6) and four fix commits. Nothing here adds
a claim.

- **P0.5 data** (`scraper/junkyard_scraper.py` ENGINE_FAMILIES, own commits).
  `scraper/_audit_verified_fits.py` gained (e) a vPIC-hybrid column (vPIC
  decode after `_correct_vpic` / vpic side-table, the yard's model name, a
  VIN-pattern sibling of yard-named hybrids, or the GM eAssist VIN engine
  code "R" on 2012-16 Malibu/Regal/LaCrosse/Impala) and (f) Verified donors
  per family, with `--compare before.json`. Every app where hybrids pass the
  engine gate is split at the hybrid years and flagged ambig; `sole` dropped
  where a decode-less hybrid passed (Avalon 13-18, RAV4 13-14, MKZ 11-12,
  Malibu 2013); gm-ecotec-lcv's starter group withdrawn and its alternator
  group's 2.4 row withheld (210-0255 names the 2.4 eAssist, which has a belt
  motor-generator, not an alternator; the group spans only the now-ambig
  2013 Malibu, so it verifies no pair). Full list and basis:
  `scraper/interchange_research.md` "Hybrid over-claim fix 2026-11-05".
  All spec-listed apps confirmed from data; data added toyota-3mz
  Highlander 06-07, Optima (both Theta families), nissan-qr25 Altima 07-11,
  the gm-ecotec24 Saturns and Regal 12-13 (eAssist), gm-ecotec-lcv Malibu 13
  (Eco eAssist) and Impala 14 (eAssist, decode cache), Mercury Milan/Mariner
  + Mazda Tribute, gm-gen4-truck (2-mode), mopar-hemi57 Aspen 09.
  Each ambig note now reads "..., but their engine parts can differ and they
  <hardware fact> — check for ...", because the flag shows on every
  engine-kind category (coils, intake manifolds, engine assemblies), not
  only alternators and starters.
  Verified donors, main -> branch (2026-11-05 11:55 scan, 334,759 cars, same
  audit signal both sides): alternator 124,707 -> 117,159; starter 37,214 ->
  35,019; engine-assembly 227,319 -> 209,181. Hybrid-flagged Verified donors
  (alternator/starter/engine-assembly) 764/175/1,326 -> 0/0/0. The first
  pass reported "86/0/86 (Malibu Eco: its alternator is published, kept)";
  that was wrong twice over: the 86 engine-assembly donors had nothing to do
  with the alternator listing (engine assembly needs only a confirming
  decode), and the 5 Regal eAssists were missed (ordinary vPIC trims). Both
  apps are now split. Reaches every client when the next scan.yml run
  rewrites `docs/data/interchange.json` (not regenerated on the branch, to
  avoid colliding with the scan commits).
- **Merge with main (§23.6)**: main replaced the gm-gen4-truck prefix apps
  with explicit light-duty spellings; the 2-mode splits are re-applied to
  them (Silverado, Silverado 1500, Sierra, Sierra 1500, Sierra Denali 1500
  09-13; Tahoe, Yukon* 08-13; Escalade* 09-13). The yard name "Sierra
  Hybrid" is no longer a family app (no claim); "Yukon Hybrid" still is,
  capped. Both the §23.6 and P0.5 test blocks pass.
- **P0.1-P0.4 app** (`docs/app.js`): platform tier fails closed; header
  notes escaped; rowWarn on platform rows; `pfDonorIdentity(v, {oem})` +
  `pfVinModelYear` + `pfVinValid` (check digit) on platform, vg and
  engine-assembly Verified rows. Review: engine browse (`pfRunBrowse`) now
  gives the green "VIN-confirmed" chip only on a confirming decode, a
  non-ambig app and `pfDonorIdentity(v).ok`, so hybrids and identity-flagged
  donors no longer count as VIN-confirmed; the engine-assembly fit search's
  hint says its Verified is a VIN decode in the family (no catalog lists
  engine assemblies) and to match the displacement, instead of "published
  catalog fitment data". 556 lot cars are identity-flagged; 99.5% of
  17-character lot VINs pass the check digit (1,279 fail, 119 bad chars),
  which bounds the OEM no-valid-VIN rule. **P0.6** `docs/sw.js` jh-v142 (one
  bump over main's jh-v141 covers every app.js change on this branch). Web
  on deploy; native only after the owner's "ship".
- **Tests**: `backend/test/pf_guards_unit.mjs` (node; loads the real
  pfRunSearch, pfRunBrowse and pfVonlyRowHtml from app.js; 81 checks: 34 of
  the first pass's 63 fail on the pre-P0 app.js, 10 of the review's 18 fail
  on the pre-review app.js) instead of the §9 part_finder_e2e.py additions;
  `scraper/test_interchange.py` P0.5 section (217 checks in the file; 14
  fail on the pre-review data; the first pass reported 16 failing on the
  pre-P0.5 data). All 18 `scraper/test_*.py`, 24 oem_fitment, 2 aftermarket
  and 3 node unit test files pass (oem_fitment site tests ran their pure
  checks; cached-page checks skip without the page cache). Browser e2e:
  interchange, pf_ux, yaris pass; part_finder has one failure, "m3
  alternator: message counts tracked M3 donors", identical on main's
  app.js (the test hard-codes "1 in tracked yards"; the lot now has 0).
  browser_e2e.py not run (needs wrangler dev + D1; billing flows).

### For the hub (found, not changed here)

1. **Engine-assembly Verified across displacements.** The client's
   engine-assembly tier is Verified whenever the donor's decode is any of the
   family's liters, so a 4.8 GMT900 donor is "Verified" for a 6.2 seeker,
   a 2.0 for a 2.5 in ford-mzr, a 2.0T for a 2.5 in gm-ecotec-lcv. The
   family note says "any donor in this family carries the same long block",
   which multi-displacement families contradict. Needs a per-displacement
   rule. Considered on review and not done here: failing closed in the
   client for `fam.liters.length > 1` (web only; a demotion type outside
   P0.4/P0.5/§7.6, which §10.2 measure.py would flag). The hybrid part of it
   (2.4 eAssist for a 2.5 Malibu) is fixed by the data split; the hint now
   tells engine-assembly users to match the displacement.
2. **App-level ambig is blunt.** It caps every engine of the flagged years:
   hk-theta-gdi alternator Verified donors 2,024 -> 0, ford-fusion-cd4 701 ->
   0, gm-gen4-truck 764 -> 459, gm-ecotec-lcv 545 -> 0. Restoring them
   honestly needs the app to tell hybrids apart per car (the vpic side-table
   already carries Camry "Hybrid"/"Gas" from VIN_TRIM_PATTERNS; Sonata/
   Optima/Altima/Highlander hybrids are separable by VIN positions 4-8, GM
   eAssist by VIN position 8 "R"), and for vg groups also the seeker's
   engine.
3. **Yard-named hybrids reach prefix apps** ("Yukon Hybrid" under `Yukon*`,
   "Escalade Hybrid" under `Escalade*`; "Sierra Hybrid" no longer, after
   §23.6): capped at Likely with the note, but they should not be
   alternator/starter donors at all.
4. **Known hybrids not seen in the lot data or decode cache** (not acted on):
   RAV4 Hybrid 2016-18 (toyota-2ar RAV4 15-18 still sole; no RAV4 13+
   group), Fit EV 2013-14 (honda-l15 Fit sole; starter group 2010-13), Rogue
   Hybrid 2017-19 (nissan-qr25 Rogue sole), 2004-07 GM PHT Silverado/Sierra
   hybrids (gm-gen3-truck). Correction: the first pass also listed "Regal
   eAssist 2012-13 (gm-ecotec24, no group)" here; 5 are on the lots and
   showed Verified engine assembly, which needs no group. Now split.
5. The audit's hybrid signal is a heuristic for finding apps, never shipped;
   vPIC model-level strings ("Base/Hybrid" on every 2011-16 Highlander)
   inflate the counts for those rows.

## Owner decisions 2026-11-05 ~22:40 UTC (hub)

1. Oct 27 grant-pro runs (pre-masking, emails in logs) deleted: runs 40528784800, 40529156919, 40529630960, 40529784249. The Nov 5 runs are on the masked workflow (882cf96).
2. Mopar/Subaru: owner asked for "a workaround". No bypass (CLAUDE.md rule 2). Instead: one same-identity retry (`.retried403` on oem-raw; a second refusal is final), Dodge/Chrysler/Ram seeds through jeeppartsdeal (a full Mopar dealer catalog that has not refused us), and a Subaru source scout under the usual robots/terms survey. Euro sites get curation namespaces. Session: session_016ZzJfMapNmKpMbuoJzVupB.
3. The 41 hand vg groups the §7.6 trigger would withhold (hypothetical closure run): no hand withdrawal; the rule withholds them automatically once cells are OEM-closed. The list goes to ops/parts.md for a basis re-check.
4. U-Pull-R / Harry's: no captcha work. Harry's scans fine (4,230 cars; their site has served an unchanged list since 2026-11-04, newest car 11-03). U-Pull-R stays "waiting on the yard"; follow-up call/email to jessef@ if no reply by 11-07.

## Interchange session status, 2026-11-05 ~23:30 UTC

Merged to main:
- **50c9243 jeeppartsdeal v2 (Dodge / Chrysler / Ram).** worklist.json
  `sites[jeeppartsdeal]` has `version: 2` and 62 Dodge/Chrysler/Ram segments
  (copied from the moparpartsgiant worklist, same feed segments and seed
  years; Plymouth left out because this site prints no Plymouth rows). New
  `markers.py`: a vN worklist finishes as `raw/<site>.vN.done`. The v1
  `raw/www.jeeppartsdeal.com.done` stays on oem-raw as evidence, the plan
  step looks for `.v2.done`, and progress.json done keys skip the Jeep
  seeds. fetch.py, identity, robots, the 8 s gap and the breaker are
  unchanged. The plan step, dry-run against oem-raw, now lists jeeppartsdeal.
  - Basis: on oem-raw the site's own product pages print full fitment rows
    for Dodge (340), Chrysler (113) and Ram (50), with trims and engines. The
    template's year path is make-parameterised (the toyotapartsnow Scion
    pages work the same way). **Not confirmed from a cached page:** there is
    no page cache in this container or on oem-raw, so whether
    `/catalog/<year>-dodge-<model>-parts` exists is unverified until the
    first slice runs. A miss is HTTP 404, a redirect or no parts-list links
    (NavError, recorded in the R2 year manifest). It never counts as a
    refusal and never creates a record. Check the first slice's
    `raw/www.jeeppartsdeal.com.log` and `.years.jsonl`. If every Dodge
    seed misses, the slug guess is wrong, not the source.
  - Slugs: year splits are taken from the catalog's own printed ranges
    (Dodge Ram 1500/2500 1994-2010, then make Ram; Ram Van/Wagon 1994-97;
    Ram 1500 Van 1999-2003). Combined feed names (Caravan/Grand Caravan,
    Dodge "Ram", "Ram Pickup", "1500 Pickup", D1500) navigate nowhere.
    `Town & Country` -> `town-country` and Ram `C/V` -> `c-v` are the
    default slugify and unverified.
  - Tests: test_crawl_runner (versioned marker; v2 navigates only the new
    segment and re-fetches no product), test_jeeppartsdeal (+15 pure
    checks). `tests/run_all.py` 28/28.
- **390c5fd ops/parts.md**: the 41 hand vg groups for a basis re-check
  (task 4). Reproduced from toyota + mopar on oem-raw@50ac4a48, every cell
  assumed closed: 41 vg, 0 platform; splits option_split 240, trim 44,
  engine 5, plant 1, production 1 (the hub's totals). Main now has 467
  hand vg groups (the hub counted 468). Nothing withdrawn, parts table not
  touched.
- **2d0b9cd namespaces vag (VW + Audi; 06B-903-016-AB is on both
  catalogs), bmw, mb, mazda, mitsubishi, volvo**, in policy.py and
  CURATION_SPEC §4. model_map.json gets +281 identity-draft entries (every
  existing entry unchanged). The mb note brand is "Mercedes" because V5's
  note charset refuses the hyphen. All 14 `_report/*` were re-curated on
  oem-raw@ceccc80, plus `coverage-2026-11-05.json`. No `groups/<ns>.json`
  committed (spec 11.5).
  - Likely / Verified: bmw 957/0, mb 958/0, vag 704/0, volvo 271/0, mazda 58/0,
    mitsubishi 32/0; old ones toyota 1506, ford 1033, gm 930, nissan 905,
    subaru 553, hmg 413, mopar 320, honda 35, all 0 Verified. bmw, mazda,
    mitsubishi and volvo have no R1/R2 manifests on oem-raw. vag and mb
    have some (18 year manifests for vag), but no audits and engine cells
    unaudited, so Likely only.
  - measure.py: parity 6/6. V11 drops 5,972 Likely groups for size (the
    payload-size decision is still open, item 2 above). Every §7.6
    contradiction count is 0. Alternator, starter and engine-assembly
    "after" are below "before" (121,837 -> 117,601; 225,773 -> 213,637).
    That is not the OEM layer: the committed docs/data/interchange.json
    (17:20 scan) predates main's P0.5 hybrid splits (15 hand engine
    families differ). It settles at the next scan.
  - Tests: curation_tests 14/14 files (Phase 2 parity SKIP: no OEM-TIER
    block in app.js), all 19 `scraper/test_*.py` pass.
  - MINI: no source. bmwpartsdeal is not a MINI catalog (1,746 records, 0
    MINI fitment rows). SOURCES.md found no allowed MINI catalog
    (fcpeuro is rejected by its terms; mini*partsgiant/deal/now did not
    resolve). MINI has 1,004 lot cars.
  - Open for audit: VAG numbers with an `X` suffix (e.g. 06F-903-023-FX)
    look like reman exchange units. No reman rule exists for them (policy
    has Toyota `-84` only). Check before any vag audit.

What the next crawl does: run 12 (scheduled 20:08 UTC, still running) was
planned before the retry markers (22:46) and before the v2 worklist. The
next scheduled run (cron :23 every 6 h, so 00:23 UTC; it waits for run 12)
plans moparpartsgiant and subarupartsdeal (one same-identity retry each:
a 403 writes `.blocked`, final) and jeeppartsdeal v2 (Dodge/Chrysler/Ram
only), plus the unfinished ford, gm, hyundai, lexus and vw. max-parallel 6.

Blocked / not done:
- Task 3 (Subaru source scout) not started: subarupartsdeal's retry has
  not run yet. Method for when it is needed: SOURCES.md survey (probe.py:
  robots + home page only; terms read for an anti-automation clause;
  RFC 9309 robots reading). **A sister site on the same dealer network as
  subarupartsdeal (SimplePart / PartsGiant family) is excluded:** after a
  403 from that network, using it would be routing around the refusal. A
  candidate needs a different operator, and the basis goes here before any
  fetch.py ALLOWED change.
- 41 hand groups: waiting on the parts session (ops/parts.md).

- 2026-11-06 (hub route from parts, d6e059c): `toyota-2az/alternator#1`
  checked against oem-raw and the lots. The 27060-37041 "Japan Built" split is
  1.8L (its predecessor 37040 prints ZRE142 only; every 2AZ number prints
  AZE141; every Japan-built 2009-10 Corolla on the lots decodes 1.8L).
  No change to ENGINE_FAMILIES or test_interchange P0.5. Evidence is in
  ops/parts.md under the item.

## Interchange session status, 2026-11-06 ~03:10 UTC (session_016ZzJfLB9KQDQ64RoN6T9sX)

Did not touch: crawler worklists, fetch.py ALLOWED, jeeppartsdeal v2, sites/,
the payload (junkyard_scraper.py) or app.js. Nothing was fetched from a
catalog. Reads: oem-raw files via `git show`, plus web docs (NHTSA field
spec, eBay search results).

**1. Aftermarket layer (merged ae57806, beba873).** `aftermarket/groups_am.py`
turns DB Electrical (oem-raw@9d2c3b76) into one **Likely** group per unit
(`am:dbe:<cat>:<item>`, src aftermarket, never Verified). Before this,
curation did not read the track at all (policy AFTERMARKET_SITES; spec §12).
- Amperages are never merged. When one vehicle-year and engine appears on
  units of different amperage, each unit carries `amperage_split:105A/120A…`.
- Membership: a car joins a row only when its decoded engine agrees (liters
  ±0.05, cylinders, diesel both ways; diesel is harmonised across the two
  feeds). Undecoded engine → `engine_unconfirmed`; row without an engine →
  `engine_unlisted`. Starter AT/MT gate comes from the unit's own Fits text
  (MINI 410-24071 w/AT vs 410-24074 w/MT list the same cars).
- Refused: 155 crawler-flagged records. Also dropped: 9,501 application rows
  whose engine size is absent from the unit's own Fits text. That source
  error is real: Fiat 500 1.4L is printed on 410-52066 "CHRYSLER 3.3L
  1990-91" and on 410-52033. The guard is fail-closed, so many dropped rows
  are probably correct. Combined makes ("Chevrolet / GMC") and model names
  matching no lot model are reported, never guessed.
- `measure.py --aftermarket FILE [--aftermarket-only]`: client-tier views
  are unchanged, Verified pairs added 0. Tests:
  `aftermarket/tests/test_groups_am.py`, 26 checks, including 200 sampled
  pairs re-checked against raw rows. Report:
  `groups/_report/aftermarket-dbelectrical.md`. Groups JSON (4 MB)
  git-ignored, rebuilds from the pinned raw.
- Lot cars with an aftermarket Likely alternator/starter donor (either /
  engine-confirmed): MINI 846/528 of 1,011; Land Rover 729/653 of 827;
  Suzuki 585/474 of 750; Jaguar 363/310 of 704; Isuzu 419/328 of 501;
  Saab 53/49 of 387; Fiat 316/247 of 372; Plymouth 137/108 of 222;
  Porsche 125/103 of 183; Smart 62/49 of 77; **Geo 0 of 182** (DB has no
  Geo rows). All makes: 300,275 of 334,293.
- **Not shipped.** Shipping needs a payload key (e.g. `amGroups`), client
  display as "Likely (aftermarket)", owner review, and an independent audit
  sample per spec §11.4. That is the hub's call.

**2. Badge twins (beba873, `aftermarket/twins.py`,
`groups/_report/aftermarket-twins.json`).** The only basis used: one DB
Electrical unit printing both vehicles. The OEM catalogs on oem-raw print
no Geo/Saab/Isuzu/Suzuki/Plymouth rows. Mercury and Pontiac/Saturn already
sit inside the ford/gm namespaces. Shared units found for: Saab 9-7X /
TrailBlazer / Envoy (26 of 28 Saab cars), 9-2X / Impreza (11/11), Ascender
/ Envoy / TrailBlazer (41/42), i-Series / Colorado / Canyon (10/14), Rodeo
/ Passport (207/222), Hombre / S10, XL-7 / Equinox (70/149), Equator /
Frontier (3/3), B-Series / Ranger, Raider / Dakota (43/43), Plymouth
Voyager / Grand Voyager / Neon / Breeze ↔ Dodge, Vibe / Matrix (387/408),
Mercury twins, and Villager / Quest (starter only). **Geo Prizm, Metro and
Tracker: no basis (0 cars).** Cross-make donor gain by make: Isuzu 413,
Suzuki 281, Jaguar 230, Fiat 166, Plymouth 137, Land Rover 59, Saab 37,
Porsche 32; MINI 0 and Smart 0 (single-make units only).

**3. Second sources (proposal for session_016ZzJfMapNmKpMbuoJzVupB or the
hub; not applied).** That session is idle, not archived, so I did not race
it.
- Add www.toyotapartsdeal.com (`.html` PartsGiant template →
  `_partsgiant.py`, `/oem/toyota~<slug>~<pn>.html`) and
  www.chevypartsdeal.com (SimplePart, `/oem/gm~<slug>~<pn>`) to ALLOWED,
  with a site module each and worklist seeds limited to the numbers the
  primary already holds (cross-check), then to cells the primary left open
  (completeness).
- Same operator as the sites that refused us (Mopar 403, Subaru 403), so:
  (a) run only after the primary's `.done`, or count it inside the same
  max-parallel budget, so the operator's total request rate does not rise;
  (b) a refusal on either stops it for good;
  (c) never use them for Mopar, Subaru or other refused makes;
  (d) agreement with the primary is not independent verification.
- Value is low (Toyota and GM are already covered makes). Priority below
  everything above.

**4. NHTSA (finding; nothing built).** The manufacturer-communications flat
file (static.nhtsa.gov/odi/ffdd/tsbs/, field spec TSBS.txt) has Make,
Model, Model Year, NHTSA Components, Mfr Component System/Subsystem and a
4,000-character Summary. **It has no part-number field.** Part numbers
appear only inside free-text summaries or the bulletin PDFs. Yield is
unmeasured. Measuring it means downloading the bulk file (one file per
5-year chunk, government public data), which belongs on Actions with
static.nhtsa.gov allowlisted after a robots read. Proposed spike: count
summaries in our categories that carry part-number-shaped tokens plus
model-year lists. Build only if that yield is real. TSB numbers are
usually superseding parts ("use new P/N"), so even when parsed they are
supersession evidence, not fitment lists.

**5. eBay (finding; nothing built; no eBay calls made).** Correction from
the hub (02:42 UTC): there are **no eBay credentials**. The Developers
Program registration was rejected and EBAY_CLIENT_ID / EBAY_CLIENT_SECRET
are not set (ops/ebay.md). scraper/ebay_prices.py is written for Browse with
an application token, but it has no keyset to run with. As far as I can tell, Browse
has no full item compatibility list, only a one-vehicle compatibility
check per item. The full list (Trading GetItem compatibility list) needs a
user token. I could not read the API License Agreement: developer.ebay.com
answers 403 to our fetch tool. Community reports describe cache-refresh
limits (about 6 h) and a recent revision restricting Restricted APIs and
AI use. That is not "clearly allows storing derived fitment", so no build.
Owner option: read the agreement in a browser or ask eBay developer
support.

**6. Real-browser rendering: not needed.** All 1,098 audipartsgiant
records on oem-raw carry fitment from the server HTML (0 `no_fitment_rows`).
No allowlisted catalog currently needs a render path. Nothing built.

**7. More aftermarket catalogs: not surveyed past a desk search.** The one
hit, 7zap's LIFT-TEK brand pages, is a diagram EPC already rejected in
SOURCES.md (no per-part fit list). Candidates for a probe.py pass (robots
RFC 9309, terms read for an anti-automation clause, no challenge, not a
SimplePart/PartsGiant sister), none checked yet: Four Seasons / SMP (AC
compressors, switches), Spectra Premium (radiators), Depo (lamps), ACI /
Cardone (window regulators). Dorman stays out (robots). TYC and Denso stay
out (client-side / POST).

**Found, not mine:** `curation_tests/test_model_map.py` fails on main
(pre-existing, inventory-driven): M5 Ford "F150 Raptor" (1 car) and Toyota
"Camry Solara" (545 cars) / M1 "Solara" need model_map entries.
- 2026-11-06 (hub): model_map.json failed M5 on the new scan's feed name
  "Ford F150 Raptor" (1 car). It is now excluded with a basis (the Raptor
  shares only some parts with the F-150), so it gives no claims. The
  "M1 Solara" / "M5 Camry Solara" lines in test_model_map's output come from
  its negative sub-test, not from the committed map. The Solara entry
  already targets feed "Camry Solara" (its own catalog model, not Camry);
  unchanged. curation_tests 14/14, tests 29/29, scraper/test_*.py all pass.
  One M2 warning (a target with no cars) is a warning, not an error.

## Phase 1 client + lazy files + aftermarket key, 2026-11-06 (session_016ZzJfMA669Yvjhjdfqndck)

Owner direction 2026-11-06 ("do what you think"): build the display so
curated matches reach users, web first. Did not touch crawler worklists,
fetch.py, sites/, release workflows, store metadata or other workstreams.

**Merged to main (web deploys via Pages; native waits for "ship"):**
- `scraper/junkyard_scraper.py`: **§12 lazy per-category files, adopted.**
  §12 allows them "only if V11's budget binds". It does. On oem-raw@cb5fa28f
  (curate --write-groups into a scratch dir, all 14 namespaces) there are
  11,049 Likely groups and 0 Verified. The single-file build is 1,299,746
  bytes and drops **8,306** Likely groups for V11. The lazy build drops
  **0**. interchange.json is 259,185 bytes. 20 files go in
  `docs/data/oem/<cat>.json`, 5.5 MB in total. Largest: side-mirrors
  1,153,850, alternator 768,461 (aftermarket), window-regulator 587,288,
  starter 565,537. Each file has its own 1.3 MB budget and trim: OEM groups
  go in V11 order, then aftermarket groups with the fewest rows. Drops are
  reported in oemStatus/amStatus.
  - interchange.json keeps Verified oemGroups, oemVg and oemStatus. It adds
    `oemLazy {schema, path, cats: {cat: {oem, am}}}` and `amStatus`.
  - `build_interchange_payload()` with no args is unchanged (tests,
    V11-trimmed). `build_interchange_files()` is what the writer ships, and
    measure.py now measures that, with lazy groups merged back as Likely.
  - `_OEM_BRANDS` gains bmw/mb/vag/mazda/mitsubishi/volvo (labels read
    "bmw catalog" before).
- **Aftermarket key.** `groups/aftermarket/<site>.json` (the groups_am.py
  doc) ships only in the lazy files under `amGroups`, with src
  "aftermarket" and tier "likely". It is never in oemGroups or the old keys.
  Each group is refused alone if it has tier ≠ likely, a note with markup or
  "verified", or a malformed app. If more than 5% (min 5) are refused, the
  whole file drops. Evidence expires after 120 days. One real refusal:
  410-46009, whose fit notes carry "<br." from the page. 1,297 groups ship.
- `docs/app.js` (§7.4):
  - The category file is fetched on the first search of that category.
    "Loading catalog matches…" shows meanwhile. A failed or mismatched file
    is treated as empty and not retried.
  - Body branch: OEM rows come after the hand platform groups. Only
    main-file oemGroups with tier "verified" can be Verified, with
    pfDonorIdentity({oem:true}). Every lazy-file group is Likely.
  - Labels: chip "Likely fits — check the part number". Row line "Source:
    Toyota factory parts catalog #A, #B +N more". The group note stays as
    the row warning. One header per search: "Catalog part numbers shared
    on some configurations — verify the number".
  - Engine branch: `vgs = part.vg + oemVg[fam][cat]`; an OEM vg pair needs a
    valid VIN. Aftermarket rows say "Source: aftermarket unit: DB Electrical
    400-24098 (110 A unit)" plus the unit note and "lists your <yr> <model>
    with the <engine> — match your engine".
  - Aftermarket membership mirrors groups_am: the decode must not
    contradict the engine, and the AT/MT gate applies. They answer cars no
    family covers (MINI N-series, Land Rover). With a family, its rows win
    and the unit adds the donors it doesn't list.
  - Hand rows render exactly as before (byte-identical when there is no OEM
    data for the category). sw.js jh-v145.
- Tests:
  - pf_guards_unit.mjs: 130 checks, 36 of which fail on main's app.js. They
    cover lazy load, labels, fail-closed tiers, the VIN rule, oemVg,
    aftermarket engine/trans gates, the empty state, the V9 byte-identity,
    and JS↔Python parity of engine_agrees/car_trans.
  - New curation_tests/test_lazy_payload.py: 27 checks.
  - Also passing: curation_tests 15/15 (Phase 2 parity is a SKIP because
    app.js has no OEM-TIER block; Phase 2 is not written), all 19
    scraper/test_*.py, oem_fitment/tests 29/29, the aftermarket tests, the
    other node unit tests and node --check.

**Playwright (local static server of docs/ with the scratch-built data, zip
22401, 100 mi, 430 px wide, SW blocked):**
- (a) 2005 Camry window regulator: 124 donors, all "LIKELY FITS — CHECK THE
  PART NUMBER", "Source: Toyota factory parts catalog #85710-AA050,
  #85720-AA050". The header has the one catalog caveat; the row warning
  carries the group note ("window motor only; plant-specific").
- (b) 2011 MINI Cooper alternator: 47 donors, all Likely, "Source:
  aftermarket unit: DB Electrical 400-24253 (150 A unit)", with the
  aftermarket header. 2015 Coopers that decode 1.5L/2.0L are correctly left
  out.
- (b2) 2008 Land Rover LR2 starter: 6 Likely, DB Electrical 410-24293.
- (b3) 2005 MINI Cooper alternator: 2 "Verified fit" rows from the existing
  hand MINI W10 family (main's app.js shows the same 2), and the units are
  added to the Likely rows.
- (c) 1995 Geo Metro alternator: the existing "No interchange data yet"
  empty state.
- No page errors. No OEM or aftermarket row or label says Verified. The
  pre-existing "0 verified · N likely" counter and the "Verified fits only"
  filter still show, as on every search.

**What users see on web now: no change yet.** The code is inert until data
is committed. The repo has no `groups/<ns>.json` and no
`groups/aftermarket/*.json`, by design (§11.5: the owner reviews
`_report/<ns>.md` before the first merge per namespace; the aftermarket
layer also wants an independent audit sample, §11.4). To turn it on:
1. The owner reviews the reports and says which namespaces ship.
2. Run `curate.py --ns <ns> --raw-ref origin/oem-raw --write-groups`.
3. Run `aftermarket/groups_am.py --out scraper/oem_fitment/groups/aftermarket/dbelectrical.json`.
4. Commit. The next scan.yml run writes docs/data/oem/ (scan.yml already
   `git add docs/data/`).

**For the audit (data, not code):** DB Electrical's application rows can
outrun its own fit notes. 400-24253 prints "MINI COOPER 1.6L 2006-10" but
lists Cooper 2007-2015 and Countryman 2011-16 (1.6L). The engine guard
passes those rows; the year span is not checked against the fit text. The
note is shown on every row, so the user sees "2006-10".

**Next native release (after "ship"):** this app.js (lazy files, labels,
oemVg). Old native clients ignore oemLazy/amStatus.

**For backend ops (not done here):** ops_monitor.js should also alert on
`amStatus` values starting "dropped" (same as oemStatus, §7.3).

- 2026-11-06 07:30 UTC (hub FYI from session_01LsgNuWEh1vdaDCtdP1jxMM:
  should the `verify` hint show on every row that has one?). **Not done.**
  - The hint is in `docs/app.js` at the vehicle-card part rows (~3711):
    `ifEquipped && p.verify` renders "Spot it: …".
  - That copy is a physical tell for whether an option is fitted. On a
    standard-equipment row it would mislabel "match part #; needs
    calibration after install".
  - A correct change needs a second label for confirmed rows (e.g. "Check:
    …"). No unit test loads the card renderer, so it is not a one-line
    tested change.
  - The scraper only fills a default hint for `trim_status == "unconfirmed"`.
    An entry's own `verify` text can sit on confirmed rows, so a change
    there would surface every such text.
  - The parts session's row-name workaround already shows the ADAS caveat.
  - It belongs to the vehicle-card / parts workstream; noted there for
    whoever next ships app.js.

## Hub follow-ups on the aftermarket layer, 2026-11-06 ~07:50 UTC (session_016ZzJfLB9KQDQ64RoN6T9sX)

**1. Year span vs Fits text (c900d09).** `row_outside_fits_years`: where the
unit's own Fits text gives an explicit year range ("2006-10", "2004-07",
"2007-ON") on a line naming the row's make AND model, rows outside every such
range are dropped and counted. Models the Fits text does not name keep their
rows; for 400-24253, Countryman 2011-16 stays. Dropped: **2,595 rows**
(sample in the report). Tests: 30/30. Coverage now (lot cars with a Likely
donor, either / engine-confirmed): MINI 846/528 of 1,011 (unchanged);
Land Rover 674/600; Suzuki 577/461; Jaguar 332/279; Isuzu 417/326;
Saab 53/49; Fiat 313/245; Plymouth 137/108; Porsche 119/96; Smart 62/49;
Geo 0. All makes: 295,112 of 334,293.

**2. Agreement audit (`aftermarket/audit_am.py`,
`groups/_report/aftermarket-audit.json`).** Basis change, stated plainly:
on current oem-raw curate.py emits **no alternator/starter Likely or vg
group in any namespace**. Likely is body-only (§5.16), and vg needs closed
cells, which no namespace has. So the OEM side is each catalog's raw
fitment rows: lot key (make, model, year, engine size) → OEM numbers.
Classes merge replaces / replaced-by / reman links; rows with no single
engine size are skipped. For lot-key pairs that share a DB unit, with both
keys in one namespace: agree = OEM classes intersect, contradict =
disjoint. Reverse check: OEM-joined pairs that DB never puts in one unit.
To run curate.py at all I added one fail-closed model_map exclusion,
`ford|Ford|F150 Raptor` (no claims; test_model_map 33/33). No groups/*.json
committed.

| ns/cat | keys in both | DB pairs | contradict | rate | lot-weighted | same-size pairs | same-size rate | OEM pairs | DB splits | split rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ford/alternator | 363 | 3204 | 1441 | 0.4498 | 0.3962 | 2313 | 0.3065 | 1930 | 167 | 0.0865 |
| ford/starter | 254 | 2254 | 662 | 0.2937 | 0.3239 | 1802 | 0.1587 | 1830 | 238 | 0.1301 |
| gm/alternator | 545 | 3775 | 879 | 0.2328 | 0.0438 | 3359 | 0.1801 | 2981 | 85 | 0.0285 |
| gm/starter | 644 | 13028 | 5164 | 0.3964 | 0.1995 | 11390 | 0.3848 | 8381 | 517 | 0.0617 |
| hmg/alternator | 91 | 300 | 28 | 0.0933 | 0.1337 | 268 | 0.1045 | 338 | 66 | 0.1953 |
| hmg/starter | 127 | 679 | 186 | 0.2739 | 0.3348 | 571 | 0.2452 | 539 | 46 | 0.0853 |
| mazda/alternator | 58 | 136 | 44 | 0.3235 | 0.0942 | 89 | 0.1011 | 92 | 0 | 0.0 |
| mazda/starter | 82 | 424 | 121 | 0.2854 | 0.1875 | 309 | 0.0194 | 320 | 17 | 0.0531 |
| mb/alternator | 160 | 1049 | 326 | 0.3108 | 0.1784 | 587 | 0.2504 | 1092 | 369 | 0.3379 |
| mb/starter | 156 | 2100 | 674 | 0.321 | 0.1489 | 929 | 0.0732 | 2011 | 585 | 0.2909 |
| mitsubishi/alternator | 2 | 1 | 0 | 0.0 | 0.0 | 1 | 0.0 | 1 | 0 | 0.0 |
| mitsubishi/starter | 38 | 248 | 0 | 0.0 | 0.0 | 248 | 0.0 | 252 | 4 | 0.0159 |
| mopar/alternator | 104 | 843 | 37 | 0.0439 | 0.0923 | 817 | 0.0355 | 839 | 33 | 0.0393 |
| mopar/starter | 271 | 2721 | 108 | 0.0397 | 0.0221 | 2558 | 0.0109 | 2985 | 372 | 0.1246 |
| nissan/alternator | 285 | 1924 | 547 | 0.2843 | 0.3037 | 1457 | 0.2203 | 1596 | 219 | 0.1372 |
| nissan/starter | 267 | 1601 | 116 | 0.0725 | 0.0068 | 1556 | 0.0617 | 1821 | 336 | 0.1845 |
| subaru/alternator | 67 | 574 | 223 | 0.3885 | 0.4243 | 574 | 0.3885 | 353 | 2 | 0.0057 |
| subaru/starter | 77 | 1100 | 800 | 0.7273 | 0.6196 | 750 | 0.624 | 310 | 10 | 0.0323 |
| toyota/alternator | 133 | 585 | 189 | 0.3231 | 0.2282 | 552 | 0.3098 | 416 | 20 | 0.0481 |
| toyota/starter | 181 | 1317 | 445 | 0.3379 | 0.152 | 962 | 0.1216 | 968 | 96 | 0.0992 |
| vag/alternator | 155 | 2090 | 544 | 0.2603 | 0.1496 | 1870 | 0.1733 | 1924 | 378 | 0.1965 |
| vag/starter | 197 | 3098 | 732 | 0.2363 | 0.1829 | 2935 | 0.2034 | 2594 | 228 | 0.0879 |
| volvo/alternator | 32 | 131 | 10 | 0.0763 | 0.0048 | 121 | 0.0 | 125 | 4 | 0.032 |
| volvo/starter | 18 | 66 | 10 | 0.1515 | 0.0217 | 56 | 0.1607 | 66 | 10 | 0.1515 |

(rate = contradicting / DB-shared pairs; same-size = pairs restricted to equal engine size.)

Worst examples (DB-shared, OEM-disjoint):
- gm/starter 410-12175: 2,671 pairs, e.g. 2005 Allure 3.8 (89017715) vs
  1998 LeSabre 3.8 (10465421).
- ford/alternator 400-14020: 1997 E-150 4.2 vs 1998 Escort 2.0. Also
  400-16034: Excursion 7.3 vs 6.0 diesel.
- subaru/starter 410-48231: 2003 Baja 2.5 (23300AA40A) vs 2003 Forester 2.5
  (23300AA450/460).
- toyota/alternator 400-52054: ES300 1997 (27060-20070) vs 2001
  (27060-20120/20160).

Reading:
- Some contradictions are probably catalog numbers that do interchange but
  whose link the crawl didn't record. I cannot separate those here.
- Even so, DB "multi-fit" units clearly span vehicles whose OEM parts
  differ, sometimes different engines. Same-size pairing cuts the rate a
  lot for Mazda starter (2%), MB starter (7%) and Ford starter (16%). It
  does little for GM starter (38%), Subaru (39-62%) and Toyota/Ford
  alternator (31%).
- Low everywhere: Mopar (1-4%), Mitsubishi (0%), Nissan starter (6%),
  Volvo alternator (0%).
- The gap makes (MINI, Land Rover, Jaguar, Suzuki, Isuzu, Saab...) cannot
  be audited this way: no OEM catalog.

Recommendation for the owner review:
- Do not ship DB unit pairs as-is.
- If shipped at all: same engine size required for every pair, label
  "aftermarket unit, check the OEM number on the tag", and only after a
  hand audit (§11.4) of a sample of pairs from the gap makes.
- Where an OEM catalog exists, the OEM numbers should override a DB pairing
  they contradict.

## Aftermarket tightening (hub rule after the audit), 2026-11-06 ~08:10 UTC (session_016ZzJfLB9KQDQ64RoN6T9sX)

`groups_am.refine()` now runs by default. Unit-wide groups still go to
`aftermarket-dbelectrical.unit.json`; both JSONs are git-ignored, and no
groups/aftermarket/*.json was committed.
- **Rule 1.** A donor pair needs the same make, or an owner-listed twin pair
  printed on that same unit; the same displacement; the same fuel; plus the
  existing AT/MT and year guards.
- **Splitting.** Each unit splits into sub-groups on those keys. 1,298 unit
  groups become 5,668 sub-groups. 1,634 rows have no engine size and are
  dropped, since they can't meet rule 1.
- **OEM override.** Where keys carry OEM numbers (lot key → OEM classes,
  merged over supersession/reman), a sub-group is split once more per OEM
  class. Keys with disjoint numbers never pair; a key without numbers pairs
  on rule 1 alone.
- **Size.** The refined JSON is 23 MB (notes, OE lists and Fits text are
  copied into every sub-group). The payload builder (cf7dcda) will need to
  slim it if it ever ships.
- **Tests.** test_groups_am.py: 37/37 (+7 refine checks).

**Residual disagreement** (`audit_am.py --compare`,
`groups/_report/aftermarket-audit-refined.json`). "after" is 0 everywhere
by construction: the same OEM numbers removed those pairs. So eligibility
is judged on the **rule-1** rate, which estimates the error on pairs
without OEM numbers. Rule: ≤ 5% on ≥ 30 measurable pairs.

| ns/cat | before pairs | before rate | rule-1 pairs | rule-1 rate | after pairs | after rate | eligible |
|---|---:|---:|---:|---:|---:|---:|---|
| ford/alternator | 3204 | 0.4498 | 1700 | 0.2606 | 1257 | 0.0 | no |
| ford/starter | 2254 | 0.2937 | 1324 | 0.1548 | 1119 | 0.0 | no |
| gm/alternator | 3775 | 0.2328 | 1478 | 0.1746 | 1220 | 0.0 | no |
| gm/starter | 13028 | 0.3964 | 4041 | 0.3672 | 2557 | 0.0 | no |
| hmg/alternator | 300 | 0.0933 | 268 | 0.1045 | 240 | 0.0 | no |
| hmg/starter | 679 | 0.2739 | 571 | 0.2452 | 431 | 0.0 | no |
| mazda/alternator | 136 | 0.3235 | 89 | 0.1011 | 80 | 0.0 | no |
| mazda/starter | 424 | 0.2854 | 309 | 0.0194 | 303 | 0.0 | yes |
| mb/alternator | 1049 | 0.3108 | 587 | 0.2504 | 440 | 0.0 | no |
| mb/starter | 2116 | 0.3185 | 945 | 0.072 | 877 | 0.0 | no |
| mitsubishi/alternator | 1 | 0.0 | 1 | 0.0 | 1 | 0.0 | no |
| mitsubishi/starter | 248 | 0.0 | 248 | 0.0 | 248 | 0.0 | yes |
| mopar/alternator | 843 | 0.0439 | 319 | 0.0439 | 305 | 0.0 | yes |
| mopar/starter | 2721 | 0.0397 | 1172 | 0.006 | 1165 | 0.0 | yes |
| nissan/alternator | 1924 | 0.2843 | 1324 | 0.2137 | 1041 | 0.0 | no |
| nissan/starter | 1601 | 0.0725 | 1183 | 0.0304 | 1147 | 0.0 | yes |
| subaru/alternator | 574 | 0.3885 | 574 | 0.3885 | 351 | 0.0 | no |
| subaru/starter | 1100 | 0.7273 | 750 | 0.624 | 282 | 0.0 | no |
| toyota/alternator | 585 | 0.3231 | 467 | 0.2227 | 363 | 0.0 | no |
| toyota/starter | 1317 | 0.3379 | 807 | 0.1425 | 692 | 0.0 | no |
| vag/alternator | 2090 | 0.2603 | 1130 | 0.1354 | 977 | 0.0 | no |
| vag/starter | 3098 | 0.2363 | 2012 | 0.1779 | 1654 | 0.0 | no |
| volvo/alternator | 131 | 0.0763 | 121 | 0.0 | 121 | 0.0 | yes |
| volvo/starter | 66 | 0.1515 | 56 | 0.1607 | 47 | 0.0 | no |

**Eligible (rule-1 ≤ 5%):** mazda/starter (1.9%), mitsubishi/starter
(0%), mopar/alternator (4.4%, borderline), mopar/starter (0.6%),
nissan/starter (3.0%), volvo/alternator (0%). mitsubishi/alternator has
only 1 pair, so it is not judged. **Not eligible:** every ford, gm, hmg,
subaru, toyota and vag category; mazda/alternator; mb (starter 7.2%);
nissan/alternator; volvo/starter.

**Gap makes: unaudited** (no OEM catalog to check against). Coverage
under rule 1 (lot cars with a donor, either category). Inventory scan
2026-11-06, so car counts differ slightly from earlier tables:

| make | lot cars | before either | rule 1 either | after either | status |
|---|---:|---:|---:|---:|---|
| MINI | 1013 | 847 | 847 | 847 | unaudited (no OEM catalog) |
| Land Rover | 830 | 677 | 677 | 677 | unaudited (no OEM catalog) |
| Jaguar | 704 | 332 | 332 | 332 | unaudited (no OEM catalog) |
| Suzuki | 750 | 578 | 571 | 571 | unaudited (no OEM catalog) |
| Isuzu | 500 | 416 | 411 | 411 | unaudited (no OEM catalog) |
| Fiat | 372 | 313 | 313 | 313 | unaudited (no OEM catalog) |
| Porsche | 182 | 118 | 116 | 116 | unaudited (no OEM catalog) |
| Smart | 77 | 62 | 62 | 62 | unaudited (no OEM catalog) |
| Saab | 385 | 53 | 53 | 53 | unaudited (no OEM catalog) |
| Plymouth | 221 | 136 | 136 | 136 | unaudited (no OEM catalog) |
| Geo | 183 | 0 | 0 | 0 | unaudited (no OEM catalog) |
| all makes | 334432 | 295184 | 293352 | 293351 |  |

They stay off until a hand sample is done. Note how little rule 1 removes
for them: their units are mostly single-make already, so it is not
evidence that they are accurate. The disagreement within rule 1 elsewhere
(e.g. gm/starter 37%, subaru 39-62%) is the best available warning for them.

## 2026-11-06 accuracy audit: own-page rule for Likely body groups (hub request)

Cause found by the hub: Ford AH6Z-8200-ACP, an MKZ grille, appeared as a Likely
group for Fusion 2010-12, MKZ 2010-12 and Milan 2010-11. The product page's
fitment table repeats the whole platform's engine/trans union (it lists the
2.5L and the manual for the MKZ, which never had them), so it is a platform
rollup.

Measured on oem-raw@42683f9 (every Likely group is body-only; scratch
script, not committed). App vehicle-years of Likely groups, by their own
list page:
- 80-95% have **no own-page evidence** (product page only), because the crawl
  reads 1-3 seed years per segment.
- Where the own page was crawled (R1 manifest), it **did not list the number**
  for this share of exterior app-years (lamps, panels, mirrors, gates): mopar
  136/733 (19%), ford 91/811 (11%), hmg 8/71 (11%), gm 42/563 (7%), subaru 54/856 (6%),
  toyota 34/1193 (3%), mb 1/391, vag 0/94. Interior/other body categories:
  mopar 33/284, gm 21/441, subaru 15/260, toyota 7/203, ford 4/397.
- Even the own list pages share platform rows on Ford: the 2010 Milan and
  2012 Fusion pages print AH6Z-8200-ACP with the Fit Note "Lincoln Division
  Derivative". There are 1,706 such "<Make> Division Derivative" rows on
  fordpartsgiant.

Rules (merged):
- 7747152 §5.16 own-page rule (`policy.LIKELY_REQUIRES_OWN_PAGE`): a
  vehicle-year joins a Likely group only when `own_page` says its own page
  lists the number (a matched R1 manifest row, or for a site without
  manifests a record seeded there). The class still needs 2 models. Left-out
  years are counted per category in each report's
  `summary.likely_app_years_without_own_page`. A completion crawl (R3) of
  those pages brings them back.
- 2e21ae0 `own_page` leaves out a row whose note names another make's
  division ("Lincoln Division Derivative" is not listed for a Ford or
  Mercury T). This applies to Verified closure and to Likely.
- Engine categories never form Likely groups, so they are unchanged.

Likely groups, before -> after (both on oem-raw@42683f9): toyota 1749 -> 781,
gm 1110 -> 357, subaru 1111 -> 379, mopar 756 -> 169, ford 1935 -> 88, vag 802 -> 46,
mb 958 -> 22, hmg 445 -> 6; bmw 957, nissan 905, volvo 271, mazda 58, honda 35,
mitsubishi 32 -> 0 (no R1 manifests, and a record is written once per site,
so the seed proxy gives one model only). Total 11,124 -> 1,848. AH6Z-8200-ACP
now makes no group. measure.py: parity 6/6, M-car before == after in every
category, no V11 size drops. Verified 0 everywhere. All `_report/*`
re-curated; no groups/<ns>.json committed.

Tests: curation_tests 15/15 (case 12 now asserts the rule both ways;
regressions 5 and F18 fixtures gained own-page manifests; 4 division unit
checks), tests 29/29, scraper/test_*.py 19/19.

Open:
- Sites with no list manifests (bmw, nissan, volvo, mazda, honda,
  mitsubishi) now yield no Likely groups until the crawler writes R1
  manifests there or an R3 completion run reads the apps' own pages.
- Survivors to include in the audit sample: Ford Expedition 2003 / Navigator
  2004 bumper assemblies 2L1Z-17757-BA / -BACP / 2L1Z-17906-BA. Both own pages
  list them; plausibly the shared frame-mounted bar, but unaudited.
- Own-page listing still cannot tell a platform-wide diagram from real
  fitment on a site that prints every twin's rows without a division note.
  The spec 11.4 audit sample should check visually distinct twins first.

## Aftermarket shipped for the six approved pairs, 2026-11-06 ~14:50 UTC (session_016ZzJfLB9KQDQ64RoN6T9sX)

- **Approval:** owner decision recorded by the hub in ops/hub.md (7ae3af1).
  Aftermarket on only for mazda/starter, mitsubishi/starter,
  mopar/alternator, mopar/starter, nissan/starter, volvo/alternator. Every
  gap make stays off, including mopar's Plymouth and Fiat.
- **File:** `groups/aftermarket/dbelectrical.json`, built by
  `groups_am.py --ship …` (`ship()`; constants `SHIP_PAIRS`,
  `SHIP_OFF_MAKES`). A refined sub-group ships only if every car's make
  maps (policy.NAMESPACES) to an approved pair and none is a gap make.
- **Slimmed:** id, cat, tier, src, label, unit, amps, trans, note (max 485
  chars), apps, retrieved. 747 groups, 483 KB. Skipped: 4,500 not
  eligible, 379 gap make, 42 single vehicle-year.
- **Payload** (`build_interchange_files`): amStatus "ok … 747 groups
  (likely only)", 0 refused. Lazy files: alternator 190 KB (289 am
  groups), starter 254 KB (458), both under the 1.3 MB budget.
- **Application rows by make:**
  - alternator: Dodge 622, Chrysler 389, Volvo 136, Jeep 73, Ram 9, Eagle 8.
  - starter: Dodge 550, Nissan 526, Mitsubishi 185, Chrysler 168, Jeep 153,
    Mazda 111, Infiniti 82, Eagle 38, Ram 21.
- **Lot cars with a shipped donor:**
  - alternator: Dodge 11,022, Chrysler 3,821, Jeep 3,783, Volvo 1,632,
    Ram 181, Eagle 4.
  - starter: Nissan 20,518, Dodge 19,802, Jeep 9,254, Chrysler 9,233,
    Mazda 4,647, Infiniti 2,346, Mitsubishi 2,231, Ram 469, Eagle 9.
- **Tests:** test_groups_am 42/42 (+5 ship checks), test_dbelectrical
  31/31, curation_tests 15/15 files, oem_fitment tests 29/29, scraper tests
  19/19, backend/test/pf_guards_unit.mjs all pass.
- **test_lazy_payload change:** its gate check is split. The aftermarket
  half now asserts "only dbelectrical.json, only approved pairs, no gap
  make". The `groups/<ns>.json` half is unchanged, for
  session_016ZzJfMapNmKpMbuoJzVupB to update with its own commit. I did not
  touch its files.

## 2026-11-06 OEM Likely groups committed (owner decision ~12:30 UTC, ops/hub.md)

Owner approval ("do everything you think"; the hub recorded it in ops/hub.md
7ae3af1 and relayed it) satisfies the spec 11.5 review for toyota, gm,
subaru, mopar, ford, vag, hmg and mb, with an extra hold rule:
- e4ff17c exterior hold: in exterior styling categories
  (`policy.EXTERIOR_HOLD_CATS`), a Likely group spanning more than one base
  model (`policy.base_model`) is refused as `held_exterior_cross_model`.
  Held groups are listed in `groups/_report/held_exterior.json` with apps,
  category, number, note and record URLs, for the owner checklist.
- Groups curated on oem-raw@42683f9 (the hub's reviewed ref, not newer crawl
  data). Kept: toyota 781, gm 301, subaru 223, mopar 150, ford 48, vag 31,
  hmg 6, mb 1 = 1,541. Held: 307 (subaru 156, gm 56, ford 40, mb 21,
  mopar 19, vag 15). The hub counted 1,543 / 308; the 2-group mopar gap
  is on the strict side. All 19 held mopar groups span two makes or base
  models (Town & Country / Caravan / Durango, Dakota / Durango).
- Committed: `groups/<ns>.json` for those 8 only (bmw, honda, mazda,
  mitsubishi, nissan and volvo have 0 Likely groups and no file).
- Gates, all passed before the commit:
  - validate: structural at curate time, and V12-V15 against a second
    independent curate run for all 8.
  - measure.py: parity 6/6; old-client view 0 flipped pairs (V9); the
    payload builder's V9 check accepts all 8 files ("ok", 0 Verified).
  - Tests: curation_tests 15/15 (test_lazy_payload and test_payload now
    assert that only the approved namespaces ship, with no Verified), tests
    29/29, scraper/test_*.py 19/19, backend/test/pf_guards_unit.mjs ALL PASS.
- Next: the next scan.yml run writes docs/data/interchange.json /
  docs/data/oem/. Then live check at phone width: a Camry window regulator
  search shows "Likely fits — check the part number" with the Toyota number
  and nothing Verified; Cadillac DeVille headlights show no OEM row. If
  anything fails, revert the groups commit.
- 2026-11-06 ~17:55 UTC live check: PASS (no revert).
  - Scan 3ded246 (16:51) published the groups: interchange.json oemStatus
    "ok" for all 8, lazy per-category files under docs/data/oem/;
    yardscout.io serves both (oem/window-regulator.json 200).
  - Method: Playwright, iPhone 13 emulation, zip 75201, default 100 mi
    radius. No horizontal overflow on either page.
  - 2007 Toyota Camry, window regulator + motor: "0 verified · 51 likely",
    rows labelled "Likely fits — check the part number" with "Source: Toyota
    factory parts catalog #69801-06070 ..." and the note "Toyota catalog
    lists #69801-06070 for both — regulator without motor; plant-specific
    (US / Japan built); verify the number on the part". 19 OEM-source rows,
    0 rows labelled Verified (the only "Verified" text is the filter toggle
    and the explainer).
  - 2004 Cadillac DeVille, headlights (held: 19208051 DeVille/Seville): 0 OEM
    rows, no Seville donor; only the existing same-generation hand rows
    ("Likely fit — verify part #").
  - Seen in passing (app copy, not this workstream): the headlights hint reads
    "headlightss rarely cross model lines" (pluralisation typo in app.js).

## 2026-11-09 Held exterior checklist published (owner decision 2026-11-09)

- **Artifact:** "Held Parts Checklist", private,
  https://claude.ai/artifact/5VTFUU3DrM5nWemcK11Mpr (phone-first).
- **Source:** `scraper/oem_fitment/groups/_report/held_exterior.json` on
  main@5ab4786, 307 groups (subaru 156, gm 56, ford 40, mb 21, mopar 19,
  vag 15). Data built by `tools/held_exterior_checklist_data.py` (run from
  the repo root): one card per group with category, part number, vehicles and
  years, catalog note, catalog flag (option/trim/conditional/older) and both
  record URLs. Sections are base-model pairings, most groups first
  (Legacy/Outback 146, DeVille/Seville 21, Town & Country/Caravan 14,
  F-150/F-250 14, C280/C320 12, ...).
- **Answers (artifact db):** collection `held_exterior_review`, one document
  per group, doc id `<ns>~<cat>~<pn>` (e.g. `ford~bumper-front~2L1Z-17757-BA`).
  Fields: `answer` ("right" | "wrong" | "unsure" | null), `note`, `ns`,
  `cat`, `pn` [..], `at` (ISO time), `by` (viewer id). Access rule: read
  "view", write "admin" (owner/editors only; verified that an `interact`
  write is refused). Read back with
  `ArtifactData list url=<above> collection=held_exterior_review`.
- **Verified at publish:** collection empty; no answers applied.
- **Plan, not done yet:** a later step reads only `answer == "right"`
  documents, maps each id back to its held_exterior.json group (ns, cat,
  pn), and releases exactly those groups through the existing curate path
  (an explicit owner-approved allowlist consulted by the exterior hold in
  `curate.py`, not a policy relaxation), with a curation test that asserts
  only listed groups pass the hold and all others stay held. Wrong / Not sure
  / unanswered stay held. Same gates as 2026-11-06 (validate, measure.py,
  curation_tests, tests, scraper tests, pf_guards) before commit.
- Housekeeping: this container's local `main` had 50 commits not on origin
  (tip 387774d "ops: Terapeak part list and outreach drafts into the repo");
  kept as local branch `backup/local-main-387774d`, not pushed. Origin main
  was used for everything here. Whoever owns that work should check whether
  it was pushed elsewhere.

## 2026-11-09 Held parts research agent, phase 1 (session_016ZzJfLpnys4vyFfk33LoW3)

Owner request (via hub): research whether each held exterior part really fits
both vehicles. Verdicts are ADVISORY. Nothing was released; curation and the
exterior hold are untouched.

- **Scope:** top 5 pairings, 207 of 307 groups (Legacy/Outback 146,
  DeVille/Seville 21, T&C/Caravan 14, F-150/F-250 14, C280/C320 12), collapsed
  into 86 questions (pairing, years, category, side). Researched by 4 parallel
  agents; I spot-checked the outliers myself and overrode per group where a
  question mixed numbers.
- **Result per group:** WRONG 147, UNSURE 43, RIGHT 17.
  Legacy/Outback 120 / 18 / 8; DeVille/Seville 21 / 0 / 0; T&C/Caravan 0 / 8 / 6;
  F-150/F-250 0 / 14 / 0; C280/C320 6 / 3 / 3 (W / U / R).
- **Root cause (important for the pipeline):** the subarupartsdeal diagram
  pages carry a "Fitting Vehicle Options" column that already separates the
  models: S = Legacy sedan, W = Legacy wagon, OBK/SOBK/WOBK = Outback, P = Baja,
  plus trim codes (e.g. `S.25I`). Our match treated every number on the page as
  fitting every model on it. Verified directly on
  2011 Outback fender (AJ00/01 = S, AJ06/07 = OBK) and 2015 Legacy head lamp
  (84001AL00A/01A = `S.25I` only; AL02A/03A and 84002AL00A/01A = S+OBK). Any
  Subaru group, held or shipped, built from these pages without reading
  that column is suspect. (Needs a pipeline follow-up; not done here.)
- **Other WRONG classes:** Baja parts rolled onto Legacy/Outback (84201AE30A/31A
  colour-suffix tail lamps, 57704AE20A/21A bumpers, 57120AE08A/09A fenders,
  91121AE36A/39A grilles); body styles that never existed (2010+ Outback trunk
  lid, 2010+ US Legacy liftgate); DeVille vs Seville are different bodies (all 21);
  W203 front bumper / grille changed at the 2005 facelift.
- **RIGHT (17):** Subaru hoods 57220AE00B, 57229AG04A9P, 57229AJ00A9P,
  57229AL00B9P; head lamps 84001AE14A/15A (Legacy GT trim only) and
  84001AL02A/03A; Mopar head lamps 4857040/41AB; tail lamps 4857954/55AA and
  68241334/35AA; W203 fenders 203-880-01/02-18-67 and hood 203-880-01-57-28.
- **F-150/F-250:** all UNSURE. Every number fits one of the two 1997 F-250 bodies
  (old-body HD vs new-body LD), and the yard data cannot tell them apart.
- **Where:** artifact db `held_exterior_review`, fields `agent_verdict`,
  `agent_reason`, `agent_sources`, `agent_at` (plus ns/cat/pn); no `answer` or
  `note` field was written. Repo mirror:
  `scraper/oem_fitment/groups/_report/held_exterior_agent_verdicts.json`.
- **Artifact page (version 2):** each card shows the agent verdict, reason and links
  (marked advisory), with an "Agent verdict" filter. Owner taps now use
  `update()` when the doc exists (version 1 used a full `set()`, which would
  have wiped the agent fields). Checked against a stubbed db in Chromium: 207
  agent boxes, filter right = 17, not researched = 100, and a tap sends update.
  Real db readback at view level: 207 docs, only agent fields + ns/cat/pn.
- **Access limits honoured:** amayama/megazip 403, paintedautoparts/go-parts/
  others 403 or robots disallowing ClaudeBot, RevolutionParts dealer sites
  disallow ClaudeBot: cited from search snippets only, never fetched or
  bypassed. Many sources are snippet-level; reasons say so where it matters.
- **Remaining:** 100 groups / 50 questions over 27 pairings. Estimate about 1
  agent-hour (4 parallel agents, about 10 minutes wall time) plus spot-checks.
  Not started; awaiting hub/owner.

## 2026-11-09 subaru withheld (hub, urgent accuracy)

subarupartsdeal's diagram pages have a "Fitting Vehicle Options" column that
encodes model/body: S = Legacy sedan, W = wagon, OBK/SOBK/WOBK = Outback,
P = Baja, plus trim codes such as S.25I. Curation ignored it, so every number
on a shared page was credited to every model on that page (the held-parts
research found it: 2011 Outback fender AJ00/01 = S only, AJ06/07 = OBK only).
groups/subaru.json is removed, so the next scan drops all 223 live subaru
Likely groups. Tests now pin the 7 remaining namespaces.

### 2026-11-09 option-column audit and fix (hub steps 2-3)

Rule (curate.py `note_excludes`, used by `own_page` and, pooled class-wide,
by Likely groups): a row whose own-page note restricts the number to another
model, body or make does not count as listed for T. Cases:
- another make's division;
- Mopar brand codes ("C - CHRYSLER", "D - DODGE", "E - DODGE AWD"; 1,418 on
  moparpartsgiant);
- catalog or feed model names in notes, longest first ("Jetta; Sedan" on VW
  pages shared with Golf; "Camry Hybrid; SE" on a Camry page);
- subarupartsdeal "Fitting Vehicle Options" body codes on the
  Legacy/Outback/Baja pages: S/W = Legacy, OBK/SOBK/WOBK = Outback, P/BAJA =
  Baja. W.(OBK...) qualifiers count for the Outback; engine and transmission
  codes stay unrestricted.

One own page restricting a number now drops the twin that lists it bare: the
2006 300 page says C - CHRYSLER for mirror 1BY421R3AA, the 2007 Charger page
lists it plainly, so the Charger is dropped. This only removes claims. Model
map: GMC Sierra HD, Ford Topaz, VW Golf R and Fiat 2000 are excluded (new
feed names), and Chevrolet Suburban is unmapped (M6: 1 of 4 decodes is a GMC,
a mislabelled listing).

Shipped groups, re-curated on the same raw (oem-raw@42683f9). Every
namespace's new claims are a subset of the shipped claims:
| ns | groups | pair claims | cause |
|---|---|---|---|
| toyota | 781 -> 779 | 2412 -> 2408 | hybrid-only cluster notes (83800-0X850, 83800-33B50) |
| gm | 301 -> 289 | 1292 -> 1170 | Suburban unmap (M6) and 3 note-restricted app-years |
| mopar | 150 -> 140 | 756 -> 732 | Chrysler-only brand codes on 300/Charger mirrors etc. |
| vag | 31 -> 6 | 92 -> 12 | notes naming Jetta, or Golf/GTI/R32, on shared pages |
| mb | 1 -> 0 | 6 -> 0 | the one GLK/C-class cluster note-restricted |
| ford, hmg | unchanged | unchanged | body/cab values are conditions inside one model (Ford "Passenger Power Mirror", HMG "Sedan - 4Door") |

Subaru (withheld, not re-shipped): 223 -> 97 groups, 1126 -> 392 pair claims.
Waiting for the hub.

Gates passed: V12-V15 reproducible across two curate runs; measure parity
6/6; V9 0 old-client flips; payload status "ok" for all 7 (mb 0 groups);
curation_tests 15/15 (+18 regression checks); tests 29/29;
scraper/test_*.py all pass; pf_guards_unit ALL PASS.

## 2026-11-09 Held parts research agent, phase 2 (session_016ZzJfLpnys4vyFfk33LoW3)

Hub request (owner approval quoted by the hub: "Yes do everything you think").
All verdicts are ADVISORY. Nothing was shipped and nothing reads the allowlist yet.

- **Curation used:** `curate.py --ns all --raw-ref origin/oem-raw --write-groups`
  on main f0a4b5f into a scratch folder. origin/oem-raw was **16ecb3d**, 76 commits
  newer than the 42683f9 behind main's committed reports. That run holds 288
  exterior groups: mopar 99, ford 80, gm 50, subaru 27, mb 18, vag 14. Main's
  committed `_report/held_exterior.json` (42683f9) holds 160, and all 160 are among
  the 288. I did not commit the regenerated reports; the curation session owns them.
- **1. Subaru spot-check (20 of the 97 re-curated Likely groups):**
  RIGHT 15, WRONG 4, UNSURE 1. **Fails the 0-WRONG bar.** All four WRONGs are
  2000-04 (BE/BH) numbers where the option column lists only Outback codes:
  72311AE06A (`W.OBKLTD.AT`), 72311AE08D (`S.SUS6 +W.OBK6`, plus the note
  "FOR CANADA,CHILE"), 91031AE41AFR (`W.OBKLTD.AT`) and 91031AE43BGA
  (`OBK6 +SUS6 +OBK6S +OBK6LB +OBKLTD +SUSLTD`). For 2000-04 the "Legacy" and
  "Outback" pages are one catalog, and the product page lists "Legacy" with
  Outback trims, because the Outback was sold then as "Legacy Outback".
  Fixable rules: (a) a 2000-04 number whose option codes are all OBK*/SUS*/
  WOBK/SOBK is Outback-only; (b) a market note (FOR CANADA, CHILE, EUROPE, ...)
  should drop or flag the number for US cars. I verified 72311AE08D against the
  raw record on oem-raw. UNSURE: 85021AG59A, where the option column covers both
  but outside evidence names only the Outback.
  Caveats on RIGHTs: 61188KG000 is the LH motor only (the group's side setting is
  too broad); gauge clusters need VIN/key programming.
- **2. Remaining held groups:** 217 not covered by phase 1, 107 questions, 4
  agents. Per group: RIGHT 87, WRONG 32, UNSURE 98 (after my overrides). A RIGHT
  needs a cited source outside the PartsGiant/SimplePart network, and eBay alone
  does not count. Trim, wheelbase or body splits YardScout cannot see are UNSURE
  (q1019, 1062, 1067, 1099, 1100 and 1105 were downgraded; phase-1 84001AE14A/15A
  were downgraded for the same reason). Seven carried-over groups had their
  vehicle list changed; they keep UNSURE with a note. The 136 phase-1 docs that
  are no longer held are flagged `agent_superseded`.
  The 288 held groups now stand at RIGHT 96, WRONG 63, UNSURE 129.
  Main WRONGs: Concorde/Intrepid head lamps, the 119-inch-only T&C rear covers,
  Edge vs MKX front cover and grille (MKX parts), Century vs Regal tail lamps,
  Cobalt sedan lamps against the G5 coupe, Escalade/Denali lamps against Tahoe/Yukon,
  and the C300 "Without AMG" covers against the C350.
- **3. Allowlist:** `scraper/oem_fitment/groups/_report/held_exterior_release.json`
  has 96 groups (still held, agent RIGHT, at least one independent source); 63 of
  them are also in main's committed held list. Not consumed by anything. Release
  only on the owner's go, via the curate allowlist plan in the 2026-11-09 section
  above.
- **Repo mirror:** `_report/held_exterior_agent_verdicts_phase2.json`, which also
  holds the Subaru sample.
  `tools/held_exterior_checklist_data.py` now takes a held-list path plus the
  previous data file and keeps superseded groups (`sup`).
- **Artifact version 3** (same URL): page data rebuilt from the 288-group list.
  Superseded groups sit in a collapsed "No longer held" section with no answer
  buttons. Checked against a stubbed db in Chromium: 288 live cards, 143
  superseded, 424 agent boxes, and a tap sends update. Db readback at view level:
  424 docs, 0 owner answers, all 288 held groups covered.
