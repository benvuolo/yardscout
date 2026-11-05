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
