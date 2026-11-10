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

### 2026-11-09 round 2 (hub: Subaru rules, release allowlist, fresh raw)

1. **Subaru rules (98f09c6).** Outback-family option codes (OBK*, SUS*, SOBK,
   WOBK; AT/MT/engine codes ignored) credit only the Outback in every
   generation, including the 2000-04 "Legacy Outback" years. A row whose
   every note alternative names only foreign markets (FOR CANADA, CANADA /
   KOREA / TAIWAN SPEC ...) is not listed for US feed cars. This applies per
   row and is not pooled class-wide. The research sample's 4 WRONG
   (72311AE06A, 72311AE08D, 91031AE41AFR, 91031AE43BGA) are unit-tested.
   Subaru re-curated: 97 -> 65 groups (392 -> 242 pairs); still withheld, the
   research session re-samples first.
2. **Release allowlist (05a2598): built, shipped EMPTY.**
   `release_allowlist.json` is hashed into policy_sha256. An entry releases
   a held group only on an exact (ns, cat, pn, apps) match after every
   other rule; withheld namespaces never release. It is tested: an exact
   entry releases, apps off by one year stay held, subaru is refused.
   **Not populated:** the 96 groups in `_report/held_exterior_release.json`
   are agent-verified and advisory, and this file's earlier plan says "release
   only on the owner's go". ops/hub.md has no owner decision after
   2026-11-06, and the agent's Subaru sample just failed at 4/20. Filling it
   is one commit (copy the 96 entries, set `owner_go`, re-curate) once the
   owner's go is recorded in ops/hub.md.
3. **Fresh raw (groups committed, curated on oem-raw@c36da2e).** Same rules
   on old vs new raw separate the causes. The fresh data only adds; every
   removal comes from today's rules:
   | ns | shipped -> new rules (old raw) -> fresh raw | pair claims |
   |---|---|---|
   | toyota | 779 -> 583 -> 583 | 2408 -> 1860 (-548, all market notes: CANADA/KOREA/TAIWAN SPEC, mostly Lexus mirrors) |
   | mopar | 140 -> 140 -> 245 | 732 -> 1146 (+414 fresh) |
   | ford | 48 -> 48 -> 59 | 144 -> 174 (+30 fresh) |
   | gm, vag, hmg, mb | unchanged (289, 6, 6, 0) | unchanged |
   New Mopar coverage (jeeppartsdeal v2 finished, `.v2.done`, its Dodge
   pages navigated): apps Dodge 199 -> 305, Chrysler 125 -> 216, Ram 0 -> 53;
   cars covered 78,309 -> 100,359.
   Gates: V12-V15 reproducible across two curate runs; measure parity 6/6;
   V9 0 old-client flips; payload "ok" for all 7, 0 Verified;
   curation_tests 15/15 (test_audit_store's independent hash list now
   includes release_allowlist.json); tests 29/29; scraper/test_*.py all
   pass; pf_guards_unit ALL PASS. `_report/*` regenerated, including
   held_exterior.json.
- 2026-11-09 ~03:30 UTC, held exterior release (owner go, ops/hub.md 30723df):
  release_allowlist.json holds the 96 entries of
  `_report/held_exterior_release.json` minus 8 subaru (withheld) = 88.
  Re-curated on oem-raw@c36da2e: **all 88 released** on an exact (ns, cat,
  pn, apps) match after every rule (gm 20, mopar 36, ford 22, vag 10). Groups
  now: toyota 583, gm 309, mopar 281, ford 81, vag 16, hmg 6, mb 0. The only
  change against bc5e228 is the 88 released groups: no removals, nothing
  added outside the allowlist. The 8 subaru entries release only if subaru is
  re-shipped and they still match. Gates: V12-V15, parity 6/6, V9 0 flips,
  payload ok x7 (0 Verified), curation_tests 15/15, tests 29/29,
  scraper/test_*.py, pf_guards_unit.

## Category breadth (session_016ZzJfKdkBXaVYDDQb9cy2J, 2026-11-09)

Owner (2026-11-09 ~17:30 UTC): "we're going for breadth here and data
quality ... We will create the better version, with no external or third
party costs". Scope: new Parts-tab categories. Not touched: wheels, Honda/
Nissan, other makes, release workflows, fetch.py.

### 1. Coverage matrix (the breadth scoreboard)

- Script `scraper/oem_fitment/coverage_matrix.py` (about 1 min), report
  `groups/_report/coverage_matrix.json`. Inputs: today's
  docs/data/inventory_live.json (338,797 cars), docs/data/interchange.json and
  docs/data/oem/*.json as users get them now.
- **beyond** = car has a lot donor through a part-number group (hand
  platform group, OEM group, aftermarket unit) or an engine-family vg that is
  NOT the same model in the same generation. **same-gen only** = no such donor,
  but another car of its model and generation is on a lot. Key-level, VIN
  guards not applied (upper bound). Engine kinds also report
  `engine_family_likely_pct` (same engine, other model; no part number): 63%
  for every engine category.
- **Demand** = how many of the 30 chain price lists (docs/data/*_pricing.json)
  sell the part. Gap score = cars not "beyond" x that share. The ops email's
  "Most searched parts (7 d)" on 2026-11-09 was hood 3, gauge-cluster 2,
  alternator 1 (6 searches; recorded, too few to weigh). Coverage requests
  were not read: the admin endpoint needs the secret, and no digest email
  exists.
- Read the table with care. Demand ties are close (22-28 of 30 for most
  candidates), so ranks 8-24 are within noise of the token choices. Existing
  categories use their shipped priceTokens, and some are broad ("mirror",
  "radio" match glass and speakers), so their demand is overstated.

| # | category | kind | beyond % | same-gen only % | price lists | gap score | Ford | Chevr | Nissa | Honda | Dodge | Toyot |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | radio | exact | 0.0 | 99.0 | 30/30 | 338k | 0 | 0 | 0 | 0 | 0 | 0 |
| 2 | tow-mirrors | body | 0.6 | 98.4 | 30/30 | 336k | 0 | 1 | 5 | 0 | 0 | 0 |
| 3 | gauge-cluster | body | 1.5 | 97.5 | 30/30 | 333k | 3 | 0 | 0 | 0 | 2 | 7 |
| 4 | tail-lights | body | 2.2 | 96.8 | 30/30 | 331k | 1 | 1 | 0 | 0 | 8 | 3 |
| 5 | intake-manifold | engine | 0.0 | 99.0 | 29/30 | 327k | 0 | 0 | 0 | 0 | 0 | 0 |
| 6 | side-mirrors | body | 3.8 | 95.2 | 30/30 | 325k | 6 | 4 | 0 | 0 | 10 | 6 |
| 7 | headlights | body | 4.0 | 95.0 | 30/30 | 325k | 10 | 2 | 0 | 0 | 3 | 7 |
| 8 | wiper-motor | candidate | 0.0 | 99.0 | 28/30 | 315k | 0 | 0 | 0 | 0 | 0 | 0 |
| 9 | ac-compressor | candidate | 0.0 | 99.0 | 27/30 | 304k | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 | knuckle | candidate | 0.0 | 99.0 | 27/30 | 304k | 0 | 0 | 0 | 0 | 0 | 0 |
| 11 | bumper-rear | body | 1.4 | 97.6 | 27/30 | 300k | 4 | 0 | 0 | 0 | 2 | 6 |
| 12 | bumper-front | body | 1.6 | 97.4 | 27/30 | 299k | 4 | 0 | 0 | 0 | 2 | 7 |
| 13 | ignition-coils | engine | 0.0 | 99.0 | 26/30 | 293k | 0 | 0 | 0 | 0 | 0 | 0 |
| 14 | airbox | body | 0.0 | 99.0 | 26/30 | 293k | 0 | 0 | 0 | 0 | 0 | 0 |
| 15 | fuel-pump-module | candidate | 0.0 | 99.0 | 26/30 | 293k | 0 | 0 | 0 | 0 | 0 | 0 |
| 16 | strut | candidate | 0.0 | 99.0 | 26/30 | 293k | 0 | 0 | 0 | 0 | 0 | 0 |
| 17 | hood | body | 1.1 | 97.9 | 26/30 | 290k | 0 | 0 | 0 | 0 | 5 | 7 |
| 18 | fender | body | 1.3 | 97.7 | 26/30 | 289k | 1 | 0 | 0 | 0 | 6 | 6 |
| 19 | power-steering-pump | candidate | 0.0 | 99.0 | 25/30 | 282k | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | abs-module | candidate | 0.0 | 99.0 | 25/30 | 282k | 0 | 0 | 0 | 0 | 0 | 0 |
| 21 | throttle-body | candidate | 0.0 | 99.0 | 24/30 | 270k | 0 | 0 | 0 | 0 | 0 | 0 |
| 22 | blower-motor | candidate | 0.0 | 99.0 | 24/30 | 270k | 0 | 0 | 0 | 0 | 0 | 0 |
| 23 | maf-sensor | candidate | 0.0 | 99.0 | 24/30 | 270k | 0 | 0 | 0 | 0 | 0 | 0 |
| 24 | steering-column | candidate | 0.0 | 99.0 | 24/30 | 270k | 0 | 0 | 0 | 0 | 0 | 0 |
| 25 | window-regulator | body | 6.0 | 92.9 | 25/30 | 265k | 6 | 7 | 0 | 0 | 13 | 7 |
| 26 | door-lock-actuator | candidate | 0.0 | 99.0 | 23/30 | 259k | 0 | 0 | 0 | 0 | 0 | 0 |
| 27 | door-rear | body | 0.6 | 98.4 | 23/30 | 258k | 0 | 0 | 0 | 0 | 0 | 6 |
| 28 | door-front | body | 0.9 | 98.1 | 23/30 | 257k | 0 | 0 | 0 | 0 | 2 | 7 |
| 29 | third-row-seat | body | 3.5 | 95.5 | 23/30 | 250k | 5 | 9 | 0 | 0 | 0 | 0 |
| 30 | radiator | candidate | 0.0 | 99.0 | 22/30 | 248k | 0 | 0 | 0 | 0 | 0 | 0 |
| 31 | starter | engine | 20.5 | 78.5 | 27/30 | 242k | 5 | 7 | 65 | 5 | 72 | 0 |
| 32 | alternator | engine | 30.5 | 68.5 | 30/30 | 235k | 19 | 31 | 26 | 44 | 56 | 48 |
| 33 | transmission-auto | combo | 0.0 | 99.0 | 20/30 | 225k | 0 | 0 | 0 | 0 | 0 | 0 |
| 34 | ecm | combo | 0.0 | 99.0 | 19/30 | 214k | 0 | 0 | 0 | 0 | 0 | 0 |
| 35 | tailgate | body | 0.8 | 98.2 | 19/30 | 212k | 0 | 4 | 0 | 0 | 0 | 0 |
| 36 | climate-control | body | 3.8 | 95.2 | 19/30 | 206k | 2 | 3 | 0 | 0 | 10 | 8 |
| 37 | front-seats | body | 0.0 | 99.0 | 18/30 | 203k | 0 | 0 | 0 | 0 | 0 | 0 |
| 38 | door-handle-ext | candidate | 0.0 | 99.0 | 17/30 | 191k | 0 | 0 | 0 | 0 | 0 | 0 |
| 39 | cv-axle | candidate | 0.0 | 99.0 | 17/30 | 191k | 0 | 0 | 0 | 0 | 0 | 0 |
| 40 | window-switch | body | 3.4 | 95.6 | 17/30 | 185k | 2 | 4 | 0 | 0 | 3 | 6 |
| 41 | engine-assembly | engine | 0.0 | 99.0 | 16/30 | 180k | 0 | 0 | 0 | 0 | 0 | 0 |
| 42 | trunk-lid | body | 0.5 | 98.5 | 16/30 | 179k | 0 | 0 | 0 | 0 | 0 | 6 |
| 43 | grille | body | 0.9 | 98.1 | 16/30 | 178k | 0 | 0 | 0 | 0 | 3 | 7 |
| 44 | center-console | candidate | 0.0 | 99.0 | 15/30 | 169k | 0 | 0 | 0 | 0 | 0 | 0 |
| 45 | liftgate | body | 1.6 | 97.4 | 7/30 | 77k | 0 | 4 | 0 | 0 | 0 | 0 |
| 46 | rear-seat | candidate | 0.0 | 99.0 | 6/30 | 67k | 0 | 0 | 0 | 0 | 0 | 0 |

(Make columns: beyond % for the six largest makes; per-make same-gen and
every make are in the JSON.)

Findings:
- **Every category is under 7% beyond except alternator (30.5%) and starter
  (20.5%).** Those two come from hand vg and aftermarket units. Body OEM
  Likely groups add 1-6% per category.
- **OEM Likely groups exist only for body kinds** (curate.py skips non-body
  in the Likely loop, and `kind_not_phase1` for PHASE3_CATS). Verified needs
  closed cells, and none are closed (no_year_manifest dominates the funnel).
  So OEM data adds nothing to engine categories today. ignition-coils and
  intake-manifold are 0% beyond, though raw holds 532 coil records, 404 of
  them listing two or more models.
- **Five candidates are already crawled on all 20 sites** (tier A/B, never
  curated: CURATION_SPEC §7.7 Phase 3): ac-compressor 1,328 records (741
  listing 2+ models), fuel-pump-module 1,501 (885), radiator 1,511 (741),
  power-steering-pump 840 (509), throttle-body 820 (562).

### 2. Batch 1 proposal (top 5 candidates by matrix rank). Nothing shipped.

Ranks 8, 9, 10, 15 and 16: wiper-motor, ac-compressor, knuckle,
fuel-pump-module, strut. They need two different paths.

**Path E (engine-gated Likely; ac-compressor, fuel-pump-module): raw
exists, so no crawl is needed. Needs a hub decision.** The Likely loop is
body-only. For these parts a same-model, same-generation donor is not safe
either: V6 and I4 compressors differ. Proposal: a Likely group is built
from one number's own fitment rows, and a car belongs to it only when (a)
its key matches a row and (b) its decoded engine (liters + cylinders)
agrees with that row's engine cell. Undecoded cars get "match your engine",
the same as aftermarket units. Same-gen donors also need the engine to
agree. The example that shows why: the Lexus throttle body 22030-31040
page prints "2016 Lexus GS200t | 6 Cyl 3.5L | 2GRFSE" and "GS430 | 6 Cyl
3.5L". Those model names come from the chassis code; the GS200t is a 2.0T
and the GS430 a V8. So the engine cell, not the model name, has to decide,
and a model whose decoded engines never include the row's engine is
dropped (a new lint: `model_engine_conflict`).
- ac-compressor. Include: the compressor assembly, with clutch if it is
  sold that way. Exclude: clutch, pulley, coil, valves, lines, switches, and
  kits without a compressor. Reman: kept as its own identity (Toyota -84,
  Hyundai "Reman Compressor", R-prefix); new and reman never merge, and the
  existing `reman_dropped` rule applies. Hybrids and EVs (electric
  compressors) are not engine-decoded, so they are excluded unless the
  decode says hybrid on both cars. rowWarn: "Match the engine and the
  compressor's part number on its label; rear-A/C and towing packages can
  use another unit." At the yard: "Bring a line wrench. Pull only from a
  system that is already empty; never open a charged one (venting
  refrigerant is illegal)."
  priceTokens: a/c compressor, ac compressor, compressor (a/c, compressor,
  a/c; never clutch. Raw example: Mopar 5264371 lists 1991-93
  Imperial/LeBaron/New Yorker/T&C/Caravan 3.0/3.3/3.8. Under path E each
  donor's engine must match.
- fuel-pump-module. Include: the in-tank module or pump assembly (GM
  "MODULE ASM, FUEL PUMP", Mopar "Module, Fuel Pump" / "Level Unit" package).
  Exclude: strainer, filter, sender-only, lock ring, seal. Conditionals: tank
  size, FFV, AWD saddle tanks, and wheelbase notes, through the existing
  note classifier. Gate: drive. rowWarn: "Match tank size, flex-fuel and
  the module's plug; check the strainer." priceTokens: fuel pump, fuel
  sending, fuel sender.
- The other three already crawled (power-steering-pump 509, throttle-body
  562, radiator 741 multi-model numbers) follow on the same path once batch
  1 passes. ignition-coils too: it is already a Parts-tab engine category
  with 0% beyond.

**Path B (body Likely path as built; wiper-motor, knuckle, strut): needs a
new crawl tier C.** That means navigation patterns plus include/exclude
rules in all 20 site modules, a trial `--max-segments 2` per site, then the
6-hourly Actions crawl. That is about 3-5 runs before raw is complete.
- wiper-motor. Include: front windshield wiper motor, with or without
  linkage where the catalog sells them as one (packaging motor vs
  motor+linkage, never mixed). Slots F and R; a rear liftgate motor is its
  own slot. Exclude: arms, blades, linkage only, switches, washer pumps,
  headlamp wiper motors. rowWarn: "Front motor; some years sell it with the
  linkage. Match the plug and the crank arm." priceTokens: wiper motor,
  windshield wiper motor, never headlamp, switch, arm, blade or transmission.
- knuckle. Include: a bare steering knuckle/spindle (front L/R; rear
  knuckle/carrier is its own slot). Exclude: hub/bearing, ABS sensor, ball
  joints, bolts. With hub: its own packaging. Gates: drive (AWD), and
  brake-size qualifiers as conditionals. rowWarn: "Match the drive and the
  brake size; most yards price it with the hub, so check what you are
  paying for." priceTokens: knuckle, spindle (never bearing).
- strut. Include: the strut assembly (bare, or complete with spring, as
  separate packaging), front and rear L/R. Exclude: mounts, springs alone,
  boots, bump stops. Sport, air and electronic-damping suspensions are
  flagged option, or the body gate. rowWarn: "Struts wear out; check for
  leaks. Sport and air suspensions use different units." priceTokens: strut
  and spring, strut assembly, =strut, strut (, loaded strut.

Each category gets the §11.4 sample (30 closures + 30 pairs, independent
verification) before it is ship-eligible with 0 WRONG; then the hub
confirms; app changes go on branch interchange/categories-<n>.

### Next (not started; waiting on the hub)
1. Hub decision on path E (engine-gated Likely, plus the
   `model_engine_conflict` lint).
2. Hub approval to add tier C = [wiper-motor, knuckle, strut] to crawl.py
   TIERS and the site-module rules (shared code).

## Honda/Nissan (session_016ZzJfMtLKpUFu8TiEFMrkF, 2026-11-09; replaces session_016ZzJfK5RFgko9f1gx7qjEa)

Owner, 2026-11-09: "start on Honda/Nissan and wheels"; "we're going for breadth
here and data quality". Ship bar: CURATION_SPEC §11.4 sample with 0 WRONG per
namespace, then hub confirmation, then groups/<ns>.json.

- **R3 own-page completion, site-agnostic (main a31d3f6).** README "Own-page
  completion, any site" has the 3 steps to enable a site.
  - `curate.py` writes `_report/<ns>.own_page_completion.json`: the
    vehicle-years the §5.16 own-page rule left out of a Likely candidate class
    that spans 2+ feed models, per category, routed to the site seeded on that
    make, ranked by cars x classes.
  - `worklist.json` `"complete": {file, version}` + `markers.mode`: the
    workflow runs `crawl.py --complete auto` once the site's worklist marker
    exists, and the pass ends with `raw/<site>.cN.done`. Rows of other sites
    are skipped. No new request types: the same navigation, fetch.py
    allowlist, robots, pacing and permanent stop as the worklist crawl.
  - Tests: tests/test_crawl_manifests.py 94/94 (auto mode, site filter,
    marker, markers.mode table); curation_tests test_curate 103 (case 12:
    unrouted vs routed row, ranking).
- **Enabled:** hondapartsnow + acurapartswarehouse ->
  `completion/honda.own_page.json` (25 rows, all Honda; 5,061 lot cars),
  nissanpartsdeal + infinitipartsdeal -> `completion/nissan.own_page.json`
  (320 rows: Nissan 201, Infiniti 119; 22,492 lot cars; 38 rows with 0 cars,
  ranked last). Built on oem-raw@75dc442.
- **Why Honda is only 25 rows:** of the 4,605 Honda app-year x category drops,
  almost all belong to single-model classes (Accord-only across years and so
  on). Those never make a Likely group (the same-model generation loop covers
  them), so their pages are not queued. Acura has 0 rows for the same reason.
- **Crawl:** not dispatched. At 17:45 UTC run 42666726212 (ford, lexus, jeep;
  dispatched 17:39 from 7f1d535) was in progress. The next scheduled run
  queues behind it, and its plan step selects the four sites in `complete`
  mode.
- **Next:** once `.c1.done` lands for the 4 sites, re-curate on the pinned sha,
  run the §11.4 sample for honda and nissan (independent verifier), report to
  the hub, and ship only after 0 WRONG and the hub's confirmation.

## Make breadth (session_016ZzJfKqBWhtUcqYMMseVgn, 2026-11-09)

Owner, 2026-11-09: "start on Honda/Nissan and wheels"; "we're going for breadth
here and data quality". Scope: every make except Honda/Acura/Nissan/Infiniti.
Ship bar: §11.4 sample with 0 WRONG, then hub confirmation.

### Diagnosis (oem-raw@75dc442, main curate rules; scratch funnel script, not committed)

Body classes (one OEM number in one category) by the step where they stop.
"single" = the fitment table names one feed model only (the same-model loop
covers these; not a defect). "own page" = 2+ feed models in fitment, but
fewer than 2 have their own catalog page reading the number (§5.16). Groups
counted before the allowlist release.

| ns | body classes | single | own page | unverified | cover no | note-restricted | held ext. | groups |
|---|---|---|---|---|---|---|---|---|
| toyota | 5330 | 3551 | 1166 | 16 | 14 | 0 | 0 | 583 |
| gm | 5393 | 3004 | 1594 | 397 | 58 | 1 | 50 | 289 |
| mopar | 5751 | 3613 | 1168 | 537 | 67 | 22 | 99 | 245 |
| ford | 6109 | 3194 | 2113 | 621 | 34 | 8 | 80 | 59 |
| hmg | 5574 | 5084 | 439 | 14 | 31 | 0 | 0 | 6 |
| vag | 1873 | 1025 | 758 | 9 | 37 | 24 | 14 | 6 |
| mb | 1354 | 363 | 939 | 5 | 28 | 1 | 18 | 0 |
| bmw | 1541 | 419 | 957 | 144 | 21 | 0 | 0 | 0 |
| volvo | 865 | 572 | 271 | 4 | 18 | 0 | 0 | 0 |
| mazda | 1150 | 1090 | 58 | 1 | 1 | 0 | 0 | 0 |
| mitsubishi | 359 | 320 | 32 | 1 | 6 | 0 | 0 | 0 |
| subaru | 1784 | 620 | 1014 | 32 | 21 | 6 | 26 | 65 |

Findings:
1. **The own-page rule is the main limit for every low namespace.** The crawl
   reads 1-3 seed years per segment, so a twin's own page is rarely read.
   bmw/volvo/mazda/mitsubishi/kia/audi/toyotapartsnow have no list manifests;
   their own-page proxy is only the seed. Fix: R3 completion (below).
2. **hmg, mazda, mitsubishi are mostly single-model** (91%, 95%, 89%):
   Hyundai/Kia/Mazda parts rarely cross models. Their ceiling is low
   whatever the crawl does.
3. **Unverified** classes are mostly correct refusals: ford RHD 538, gm
   kit/set pairs 193 + RHD 113, mopar disputed duplicate records 502, bmw
   universal-part cap 144 (BMW fitment tables list many badges).
4. **Model-map gaps (feed cars that never get a claim):**
   - gm: feed "Silverado 1500" (3,267 cars), "Sierra 1500" (1,247),
     "Silverado 2500"/"2500HD", "Express 2500" (571) are excluded. The
     catalog prints "Silverado"/"Sierra"/"Express", with the series only in
     the option column. Mapping them needs a row-level series filter
     (1500 vs 2500HD); not done, an identity map would over-claim. Chevrolet
     Aveo (606 cars) has neither a target nor an exclude.
   - mb: the feed holds class names, "C-Class" 955, "E-Class" 620, "M-Class"
     381, "S-Class" 269, ... (~2,500 cars). Catalog models are badges (C300).
     A class name can be any badge, so a map would be ambiguous (Likely only
     with every badge agreeing). Not done.
   - vag: "New Beetle" 360 cars (catalog "Beetle"), unmapped; subaru: "B9
     Tribeca" 88 (catalog "Tribeca"); toyota: Lexus "LS 400" 120, "SC 400" 20.
   These need reviewed model_map entries (M1-M10).
   - Done: Chevrolet Aveo (606 cars), Lexus LS 400 (120), SC 400 (20):
     identity entries, with Aveo5 excluded (M5). Validator clean, no change
     to today's groups; they gain claims once the completion pages are read.

### Subaru §11.4 resample on the fixed rules

- Round 1 (30 stratified of 65 Likely groups + the 8 held-release entries; 4
  independent verifiers, second source outside the dealer network): RIGHT 32,
  **WRONG 1**, UNSURE 5. WRONG: 85002AL06A gauge cluster, option code
  `(S+OBK).25I.6MT`. The 2015 Legacy/Outback 6MT was Canada-only.
- Rule fix (a5d81da): `_subaru_manual_only`. A row whose every option
  alternative requires MT/5MT/6MT is not credited, per row, like a market
  note. Removes 4 groups: 85002AL06A, 85002AL07A, 85021AJ13A, 85021AJ18A
  (65 -> 61). Unit-tested in test_regressions.
- Round 2 (fresh seed, 30 of 61 + 8 held): 29 items are unchanged groups and
  keep their round-1 verdicts (28 RIGHT, 1 UNSURE). The 9 new ones were
  verified independently: RIGHT 4, **WRONG 1**, UNSURE 4. Total RIGHT 32 /
  WRONG 1 / UNSURE 5. **Subaru is not ship-eligible; it stays withheld.**
  - WRONG: 91036FJ100, RH mirror for the 2012 Impreza / 2013 XV Crosstrek. It
    is the non-heated unit (Partslink SU1321128), but the 2013 US XV
    Crosstrek had heated mirrors standard (Subaru US brochure). The XV page
    lists it under `*XV.20IP`, a configuration not sold in the US.
  - The same pattern applies to round-1 RIGHT 91036FJ110 (the LH non-heated
    mirror, also `*XV.20IP`). Its verifier found one aftermarket snippet; by
    the round-2 reasoning it is also suspect.
  - No catalog field marks non-US configurations. The `*` prefix does not
    predict them: starred XV climate controls and headlamps verified RIGHT.
    So there is no per-row rule like the manual-only one. **Hub decision
    needed:** e.g. hold Subaru cross-model side-mirror groups (Impreza/XV
    heated, signal and non-heated variants differ by market), then resample.
  - UNSURE (no source outside the dealer network): 85002AL02A, 85003AL03A,
    85021AG64A, 85021AJ14A (gauge clusters); 61041AL02A; 61188KG000 (bare
    motor, no position); 91036FJ160, 91036FJ170 (signal mirrors, XV only
    per Partslink).
  - Notes for the 8 held-release groups: the turbo hood 57229AG04A9P and the
    non-turbo hood 57229AJ00A9P carry no trim note. Both verified RIGHT for
    both models, but a GT/XT owner gets no warning.
  - Verdicts with sources: scratch only (this container). Summary here.

### R3 own-page completion enabled (0995702)

The Honda/Nissan session's mechanism (a31d3f6), reused unchanged:
`completion/<ns>.own_page.json` from curate on oem-raw@75dc442, plus a
`complete` entry in worklist.json for 15 sites. moparpartsgiant (403,
stopped) is not enabled; its 487 Dodge/Chrysler rows are routed to
jeeppartsdeal (`rerouted_from` on each row).

| ns | rows (vehicle-years) | lot cars | sites |
|---|---|---|---|
| gm | 1446 | 52,822 | gmpartsgiant (starts after its worklist .done) |
| ford | 695 | 43,572 | fordpartsgiant |
| mopar | 657 | 30,107 | jeeppartsdeal |
| toyota | 507 | 21,305 | toyotapartsnow 401, lexuspartsnow 106 |
| hmg | 112 | 7,558 | kia 65, hyundai 47 |
| vag | 537 | 6,699 | audi 366, vw 171 |
| bmw | 507 | 4,107 | bmwpartsdeal |
| mazda | 114 | 4,252 | mazdapartsnow |
| subaru | 110 | 3,835 | subarupartsdeal |
| volvo | 170 | 1,686 | volvopartsgiant |
| mb | 524 | 1,640 | mbpartsgiant |
| mitsubishi | 70 | 857 | mitsubishipartsgiant |

Not dispatched by me; the 6-hourly schedule picks sites up in `complete`
mode once each has its worklist marker. Next: once `.c1.done` lands per site,
re-curate on a pinned sha, run the §11.4 sample per namespace, report to the
hub, ship only on 0 WRONG plus hub confirmation.

### 5. Path E audit: FAILED, 34 WRONG of 60. Not shipped, not on main.

- Sample: 30 per category, 20 of each cross-model, from the c36da2e run.
  Verified by an independent subagent: every product page re-read through
  fetch.py (all 200), 56 list pages re-read, WebSearch only to check
  which engines a model had. Result file:
  `groups/_report/pathE_audit_2026-11-09.json`.
- ac-compressor: RIGHT 15, WRONG 13, UNSURE 2. fuel-pump-module: RIGHT 7,
  WRONG 21, UNSURE 2.
- Root causes. Each one breaks a design assumption, so none is fixed by a
  patch:
  1. **The engine cells in product-page fitment rows belong to the model,
     not to the part.** They list every engine of the year span: the 2002
     RAV4 "2.0, 2.4" (the 2.4 came in 2004), 2008 Mazda5 2.5, 2013 Avenger
     2.7, Tribeca 3.0 after 2007, a 1999 Silverado 8.1. The list-page notes
     then restrict the engine ("3.2L/3.5L only", "Federal, 2.4L", "Primary,
     3.6L", "2.0L With Turbo"). This is why ENGINE_CELLS_RELIABLE is false
     for PartsGiant. Path E trusted the cells anyway.
  2. **List-page notes name invisible options**, and the Likely reason
     machinery let them through as "conditional": rear A/C or rear heat
     (6 Mopar compressors); tank size or side (18/22/24 gal); emissions
     (PZEV, Federal); plant (Mexico built); production breaks (To 3/12);
     drive (FWD, without quattro); body (convertible/sedan); GM option
     codes (C69, L43 flex, L56 diesel; H6 vs 10PA17 compressor design).
     For a mechanical part, any such note means a puller can't tell which
     number the car has.
  3. **Name rules:** sender-only units passed ("W/O PUMP", "SENDER,FUEL
     (*KIT1)"), along with a dealer A/C retrofit kit (F87Z-19703-BA) and a
     bare compressor without clutch.
- What it would take: claim a (vehicle-year, engine) only when that
  vehicle's own list-page row for the number carries no note other than
  one naming that exact engine, and the engine comes from that note or a
  single-engine fitment row (never a multi-engine cell); refuse every
  option/tank/emission/plant/date/drive/body note; tighten the names; then
  draw a fresh 60-item sample. That may leave little yield. I'm not
  building it without a hub decision.
- The code stays on branch `interchange/path-e` (`likely_engine`, the
  lint, 13 tests). No group from it is committed anywhere.
- Side effect: fetch.py marked en.wikipedia.org blocked (a 200 page it
  read as a bot check). That's in this container's gitignored .state/ only,
  and it was left in place (permanent-stop rule).

### 6. V8 fix (hub request, 18:07 UTC, ef6f340)
- Main@1fe9425 would have dropped all 7 shipped namespaces (V8 hash
  mismatch after model_map/curate edits). They were re-curated on main's
  tree, same raw.
- Payload identical to the pre-break build; oemStatus ok x7.
- New `curation_tests/test_groups_hash.py` fails on any stale hash. Checked
  both ways.
- **Tier C for the 4 Honda/Nissan sites (category-breadth request, 2026-11-09).**
  Rules in d7c236e + 0fdaf09 (dict entries only; Infiniti reuses Nissan's).
  Local trial `--tier C --max-segments 2`, scratch root, nothing on oem-raw:
  0 errors, no refusals, all list pages read. Records: honda 43, acura 53,
  nissan 23, infiniti 79. Curation notes:
  - Nissan "Drive Assy-Windshield Wiper" is motor+linkage (its product page
    says "Motor & Drive").
  - Honda "Shock Absorber Assy." vs bare "Unit" is kept verbatim.
  - Honda rear knuckles marked (2WD)/(4WD) need the drive gate.
  - "N/A FOR USA" strut assemblies are dropped.
  - Nissan rear axle housings are not knuckles.
- 2026-11-09 18:00: ack of the hub rule. Any change to curate.py, policy.py,
  notes.py, positions.py, markers.py, model_map.json or
  release_allowlist.json ships in the same push as re-curated groups for
  every shipped namespace. (a31d3f6 did not change the policy hash: it
  touched no POLICY_INPUTS file.)

### 7. Tier C: Honda/Acura/Nissan/Infiniti rules are in (session_016ZzJfMtLKpUFu8TiEFMrkF, d7c236e + 0fdaf09)
- Trial runs (`--tier C --max-segments 2`, local scratch, nothing on
  oem-raw): 0 errors, no refusals. Records: honda 43, acura 53, nissan 23,
  infiniti 79.
- For curation:
  - Nissan "Drive Assy-Windshield Wiper" is motor plus linkage; "Motor
    Assy" is the motor only.
  - Honda sells "Shock Absorber Assy." and "Shock Absorber Unit"
    separately; they must be split by packaging.
  - Honda and Acura knuckle names carry (2WD)/(4WD): use the drive gate.
  - Acura MDX "RR. Windshield Wiper" is the rear motor (slot R).
  - "N/A FOR USA" rows are dropped.
- Still open: crawl.py TIERS["C"] and the `all` tier list (both wait on the
  wheels merge); rules for the other 12 sites; any dispatch. Knuckle and
  strut curation must refuse option, drive, body and other notes the way
  the path E audit showed (§5).

### Make breadth, update 2026-11-09 ~18:25 UTC

- **V8 near-miss (mine).** 1fe9425 (model_map.json) and fdc98da (policy.py)
  changed the policy hash without re-curating the shipped groups, so the next
  scan would have dropped all 7 OEM namespaces. No scan published in
  between. Fixed by ef6f340 (category session; my identical fix was dropped
  on rebase). I follow the standing rule from now on (ops/README.md).
- **Subaru, hub rulings and rounds 3-4.**
  - Round 3 (after the mirror hold, fdc98da: `policy.OPTION_HOLD_CATS`,
    refusal `held_option_cross_model`): 2 WRONG. 85021AJ19A and 85002AL05A
    are Canada-market km/h clusters (Hollander 257-54290 / 257-66945),
    printed under US years with no market note.
  - Gauge clusters held too (580692f, shipped groups re-curated, only the
    hash differs). Subaru: 49 -> 34 groups (25 window regulators/motors,
    9 climate controls; 4,449 lot cars).
  - Round 4 (fresh seed, 30 of 34 + 8 held-release): **RIGHT 35, WRONG 0,
    UNSURE 3** (61041AL00A, 61041AL02A: no outside source names them;
    61188KG000: bare motor, no position). Ship-eligible; sent to the hub
    for confirmation. Nothing committed for subaru yet.
  - Lesson for every namespace (hub): a category where an unseen option
    (heated, power-fold, turbo scoop, km/h vs mph) or an unmarked
    non-US configuration splits the part needs a visible option note or a
    hold. Check this in each namespace's sample.
- **GM Silverado/Sierra 1500 series filter: branch `make-breadth-gm-series`,
  not main.**
  - model_map `series` (regexes on the option column; a row with no series
    never maps). Feed "Silverado 1500" / "Sierra 1500" =
    `^(?!.*CLASSIC)1500(?!\s*HD)` or `1/2 TON`; years 1999-2006 and
    2008-2026 (2007 left out, both bodies sold).
  - `_drop_catchall_twins`: the unknown-series feed "Silverado"/"Sierra"
    leaves a group that holds the 1500 twin of the same catalog model and
    year. Without it, 174 Silverado + Silverado 1500 groups appeared.
  - On c36da2e: 0 new, 0 removed, 34 shipped GM groups change ("Silverado"
    apps become "Silverado 1500"). §11.4 sample of 20 is with independent
    verifiers. Ships only on 0 WRONG plus hub go, with re-curated groups in
    the same push. The large gain (4.5k lot cars) comes when the GM
    completion pages are read.

### 8. HANDOVER: category breadth, tier C (2026-11-09 ~18:25 UTC, session_016ZzJfKdkBXaVYDDQb9cy2J)

Hub decisions (18:20 UTC):
- Path E is shelved. Branch `interchange/path-e` stays unshipped, with its
  root causes in §5.
- Tier C runs on the body path, in this order: (1) wiper-motor, (2) knuckle
  and strut.
- Strict refusal applies: any option, tank, emissions, plant,
  production-date, drive or body note on the vehicle's own list-page row
  means no claim. Drive splits are never crossed.
- Each category needs a §11.4 sample with 0 WRONG and the hub's confirm.
  App changes go on `interchange/categories-<n>`.

State:
- Done: Honda, Acura, Nissan and Infiniti modules (d7c236e, 0fdaf09,
  session_016ZzJfMtLKpUFu8TiEFMrkF). Their trial was clean (§7).
- Not done:
  - crawl.py `TIERS["C"] = ["wiper-motor", "knuckle", "strut"]`, plus a
    per-site worklist gate. Copy the wheels pattern on
    `interchange/wheels`: a `"tierC": true` flag and a version bump, so a
    `.done` site re-opens for tier C only. Done keys are per tier.
  - The `tiers = [...]` line for `all`. Wait for the wheels merge or
    rebase on it; the line conflicts.
  - policy.NOUN entries: wiper-motor `wiper`, knuckle
    `knuckle|spindle|axle-hub|front-axle|suspension`, strut
    `strut|shock|suspension`. Check them against SIBLING_IGNORE (the
    unread_sibling_page rule).
- Remaining sites (14): fordpartsgiant, gmpartsgiant, toyotapartsnow,
  lexuspartsnow, hyundaipartsdeal, kiapartsnow, jeeppartsdeal,
  vwpartsgiant, audipartsgiant, mbpartsgiant, mazdapartsnow,
  mitsubishipartsgiant, volvopartsgiant, bmwpartsdeal. Skip
  moparpartsgiant (blocked; jeeppartsdeal carries Dodge/Chrysler) and
  subarupartsdeal (withheld).
  - Page slugs are in the R2 year manifests (`raw/<site>.years.jsonl`,
    field `subs`) on oem-raw. They can be grepped with no requests.
    Found so far:
    - Ford: `body_and_paint/windshield_wiper`, `rear_window_wiper_and_washer`,
      `chassis/front_knuckle_and_hub`, `rear_knuckle_and_suspension_arms`,
      `front_suspension_struts_and_springs`, `rear_springs_and_shock_absorbers`.
    - GM: `.../wiper_system_windshield`, `front_axle_front_suspension_steering/suspension_front`,
      `frames_springs_shocks_bumpers_fascias/suspension_rear`. Some years
      have `strut_assembly_front`.
    - Hyundai/Kia: `electrical/windshield_wiper(_rear)`, `chassis/front_spring_strut`,
      `rear_spring_strut`, `rear_shock_absorber_spring`.
    - Lexus (and likely Toyota): `electrical/windshield_wiper`, `rear_wiper`,
      `power_train_chassis/front_axle_arm_steering_knuckle`,
      `front_spring_shock_absorber`, `rear_spring_shock_absorber`.
    - Jeep/VW/MB SimplePart: `electrical/wipers`, `body-hardware/wiper-washer-components`,
      `suspension/struts-components`, `shocks-components`,
      `front-suspension-components`, `front-suspension`.
  - Row text must be read before the name rules are written. Ford's
    existing NAME_EXCL drops "Absorber", so strut needs its own rule. Ford
    base numbers for the new parts are unverified: read them from real
    rows, never guess.
  - Two GM list pages were fetched for 2007 Impala; they returned 200 but
    the subs were wrong for that year. Pick a year whose manifest lists
    the sub.
- Trial per site: `crawl.py --site <s> --tier C --max-segments 2` against a
  scratch root. Then let the 6-hourly schedule crawl; never dispatch while a
  run is active.

Other outputs of this session:
- Coverage matrix: `coverage_matrix.py`, run in about 1 min (§1). Re-run it
  after each category ships; it is the scoreboard.
- V8 fix (ef6f340) and `curation_tests/test_groups_hash.py`: any edit to
  policy.py, notes.py, positions.py or model_map.json must ship with
  re-curated groups/<ns>.json.
- Path E audit file: `groups/_report/pathE_audit_2026-11-09.json`. The
  per-item reasons are a good checklist of notes that knuckle and strut
  curation must refuse.

### 9. Tier C crawl plumbing and rules (session_016ZzJfHdWViThcgyPbNG4i7, 2026-11-09 ~19:20 UTC)
- crawl.py (ffe62f5): `TIERS["C"] = wiper-motor, knuckle, strut`. `TIER_FLAG = {"C": "tierC"}`:
  a site crawls tier C only if its worklist entry has `"tierC": true`. `all` = A, B, C.
  When interchange/wheels merges: `tiers = ["A","B","W","C"]`. Add `"W": "wheels"` to
  TIER_FLAG (or keep wheels' own check). The version must be one above both
  (the hub has the rule).
- Method per site:
  1. Slugs come from the R2 years manifest, or from year pages read in a local trial for
     the 7 sites with no manifest (toyota, kia, audi, mazda, mitsubishi, volvo, bmw).
  2. Placeholder rules that match nothing go in first. The trial lists every row.
  3. Name rules are written from those rows.
  4. A `--tier C --max-segments 2` trial runs against a scratch root, then `ci_audit`.
  5. The flag goes in last (`tierC_note`; version one past main and wheels for done sites).
- Flagged on main, trial clean (0 evidence mismatches, 0 category suspects):

| site | version | trial records | notes for curation |
|---|---|---|---|
| honda, acura, nissan, infiniti | 2 | §7 | §7 |
| toyota | 2 | 45 | 85110 motor; 43211/2 knuckle + 42304/5 rear carrier; 485x0 shocks |
| ford | 3 | 48 | bases 17508; 3K185/6, 3105/6 (spindle); 18124/5, 18A092. Packages: "Shock Absorber Assy" vs "Shock Absorber Kit" (product page) vs "Strut - Loaded Assembly" |
| bmw | 2 | 18 | E90 front wiper only as "Wiper System, Complete" (not taken). "spring strut" kept past the shared Springs exclusion via head() |
| jeep | 4 | 26 | 68088535AC "Knuckle And Hub" superseded by AD "Knuckle - Front" (packaging differs across chain). 2AMST022AA = Mopar accessory shock series: never group. Motor rows whose aux says "Wiper Linkage" dropped |
| vw | 3 | 28 | exact names. 1K0-505-435/436-AE are "Spindle" on their product pages: group as knuckle only if stated |
| kia, hyundai | 2, 3 | 59, 47 | "Motor & Link Assy" not taken. Sonata "Wiper Motor, LH" (two motors) |
| lexus | 3 | 46 | rear carrier read on rear_spring_shock_absorber |
| gm | (not done, no bump) | 128 | MODULE (motor + transmission) not taken. Shocks carry RPO codes and "W/UPPER MOUNT" / "EXCEPT CIRCUIT BOARD" qualifiers |
| volvo | 2 | 58 | "Wiper Motor, Driver/Passenger Side" (two motors) |

| mb | 3 | 67 | exact names; W204 sells no bare wiper motor ("Linkage Assembly"). "Carrier"/"Housing Support" not taken. Slow: ~10 min/segment |
| mazda | 2 | 26 | exact names; bare wiper-page "Motor" (BBN9-67-450A, BP4K-67-450A) dropped: product pages say only "Motor" |
| mitsubishi | 2 | 22 | name AND slug; "Damper" = strut bumper/dust cover, "Carrier" = differential (slugs) |
| audi | 2 | 86 | name AND slug; "Carrier" = differential. 8K1-955-023-E "Wiper Motor Assembly" is "Bracket" on its page: dropped |

- **All 18 crawlable sites are flagged (2026-11-09 ~19:50 UTC, 0f37c7e).** moparpartsgiant (blocked)
  and subarupartsdeal (withheld) are not flagged. The wheels merge (56dfae8) re-raised
  versions one above both (jeep 5, kia 3). TIER_FLAG = {"C": "tierC", "W": "wheels"}.
  No .vN.done exists for any raised version yet, so the next scheduled run (cron :23
  every 6 h) crawls W and C. Nothing was dispatched from this session.
- Wiper product check on audi, mazda and mitsubishi (`PRODUCT_RULES["wiper-motor"]`):
  the product page must say "wiper" and must not name a washer, bracket, frame or
  linkage. A list-page "Motor" alone is never enough.
- Known suite state: curation_tests test_model_map fails on the live Cr-Z feed row
  (hub: it clears after the rescan). Every other suite passes: tests 31/31,
  scraper/test_*.py 26/26.
- Next (whoever continues):
  - Watch the crawl logs on oem-raw for `.blocked`/`.paused`. MB and GM are the slow ones.
  - Hub 19:47 UTC: let the schedule crawl W+C. Runs 42666726212 (wheels: ford/jeep/lexus)
    and 42684614492 (gm/vw/mb/hyundai/kia) are queued or running. Never dispatch alongside them.
  - The policy/positions change ships in ONE push with all 9 namespaces re-curated
    (identical or explained) and test_groups_hash green. interchange/wheels-curation also has a
    pending policy.py change: whoever pushes second rebases and re-curates.
  - Queued for the categories app branch, NOT to be added yet (session_016ZzJfMnemMEFN88kPnYgxs,
    20:41 UTC): 4 new INTERCHANGE_PART_CATEGORIES entries, all kind "engine": radiator,
    ac-compressor, ac-condenser, fuel-pump-module. They ship ONLY with Spectra aftermarket groups
    and same-generation donors, never path E. They wait for the Spectra §11.4 sample (0 WRONG)
    and the hub's confirm. Before adding:
    - ac-condenser has no coverage_matrix candidate list. Validate its proposed tokens against
      the yards' price lists.
    - ac-compressor and fuel-pump-module have no CAND_EXCL. Add the proposed exclusions
      (clutch/line/hose/mech; relay/filter/driver module/line) and check them on the lists.
    - App (format per main 51417c4): a gated Spectra row is [make, model, lo, hi, engine, gates]
      with gates a DICT, {"body": "Sedan"|"Coupe"|...} and/or {"drive": "awd"|"4wd"|"fwd"|"rwd"}
      (the same values as the parts-table drive gate). Ungated rows stay 5 elements.
      `_am_group_entry` unpacks 5 today: add gates support or gated rows get dropped. Hub rule:
      the drive gate never infers drive. A confirmed drivetrain matches; otherwise the row
      shows "if equipped", as today.
  - Audit integrity (hub, 20:55 UTC): `fetch.py --text` silently cuts output at 400 lines.
    Until the truncation-marker fix lands, every §11.4 verifier brief must say: pass
    `--max-lines 100000`, or read the cached HTML directly. Strut and knuckle list pages are long.
  - **Branch interchange/categories-1 (e4d6373, NOT merged; hub request 21:18 UTC).**
    - Gated aftermarket rows in pfAmRows (AM-GATE block, parts-table semantics).
    - 9 categories: radiator, ac-compressor, throttle-body, fuel-pump-module, cv-axle (combo);
      ac-condenser, heater-core, evaporator (exact); strut (body). Price tokens are exact rows.
    - _am_group_entry accepts gates. Test: scraper/test_am_gates.py.
    - Merges only after the Spectra and GSP/1A §11.4 samples pass and the hub confirms. When
      merging, re-check the test_interchange category count. sw: the branch is jh-v174
      (rebased on main ac8de08, 5efdc7e). design/phoenix-cluster also takes jh-v174 and will
      likely merge first, so on the next rebase set the branch to jh-v175 (hub 22:27 UTC).
    - Tier C wiper-motor/knuckle categories are not on it yet; they follow the OEM curation.
    - Checked with both sessions (21:20 UTC):
      - Spectra emits radiator, ac-compressor, ac-condenser, evaporator (renamed from
        ac-evaporator, bde30ea), heater-core, throttle-body, fuel-pump-module and ignition-coils.
      - fuel-tank (2 groups) is NOT on the branch: small. Add later if wanted.
      - Body values: Sedan, Coupe, Hatchback, Wagon, Convertible, Van, Minivan, Pickup, Suv,
        Sport Utility, Cab Chassis, Standard/Extended/Crew Cab Pickup.
        - Cab styles: the decode can rule them out but only the listing confirms them.
        - "Cab Chassis": always "if equipped", never excluded (cutaway vans decode as vans).
      - GSP/1A emit cv-axle, plus 1A strut, throttle-body, fuel-pump-module and radiator.
        1A also has knuckle, wiper-motor, door-handle-ext, door-lock-actuator, blower-motor,
        maf-sensor and power-steering-pump. These need their own app categories later.
      - 1A groups carry `position` (front/rear, left/right) only in label and note.
      - 1A is never Pro-gated (owner). test_groups_rows checks pfAmRows and friends have no
        Pro branch; it passes on the branch.
  - Then the curation build (design above). Per category, a §11.4 sample (60, independent
    session, 0 WRONG) and the hub's confirm before any app change on
    `interchange/categories-<n>`.
- Curation design (not started, needs the crawl): new CATEGORY_POLICY entries.
  - knuckle/strut: slots FL/FR/RL/RR, axes side+door, front pair required.
  - wiper-motor: front/rear slot. Needs a new "end" axis in positions.py, plus a
    left/right sub-slot for twin motors.
  - packaging(): strut assy/unit/kit/loaded; wiper motor vs module/linkage; knuckle vs knuckle+hub.
  - NOUN entries + SIBLING_IGNORE.
  - All of this is hashed (policy.py, positions.py), so re-curate all shipped
    namespaces in the same push. Use `--inventory` from 7192563 until the CR-Z rescan.
  - Strict note refusal per the hub's 18:20 decision. Path E audit file is the checklist.
- **2026-11-09 ~18:45 UTC: subaru re-shipped (hub confirmed ~18:20).**
  - groups/subaru.json: 42 Likely, curated on **oem-raw@75dc442** (where its
    §11.4 sample was drawn). The other 7 namespaces stay on **c36da2e**.
    Per-file raw refs are on purpose (hub): oemStatus shows each one's ref.
  - The 42 = 34 rule-passing groups (25 window regulators/motors, 9 climate
    controls) + the 8 held-release entries, now in release_allowlist.json
    (`owner_go_subaru`). Sources are outside the dealer network; /p/ dealer
    URLs were dropped.
  - Allowlist entries can carry a `note` (policy.release_notes) that
    replaces the generic reason. The hoods name the split their verifier's
    source states: 57229AG04A9P "Turbo hood (scoop cutout): Legacy GT /
    Outback XT only"; 57229AJ00A9P "Non-turbo hood (no scoop); the 2011-12
    Legacy 2.5GT turbo uses a different hood".
  - policy.WITHHELD_NS is empty. The withheld test now sets it explicitly.
    test_payload / test_lazy_payload approve subaru.
  - The 7 other files were re-curated in the same push; only policy_sha256
    differs.
  - Gates: curation_tests 16/16, tests 29/29, scraper/test_*.py all pass,
    pf_guards_unit ALL PASS, measure parity ok, payload oemStatus ok x8
    (0 Verified), second subaru curate byte-identical, test_groups_hash
    passes.

### 10. Tier D — junkyard-demand categories (owner 2026-11-09 ~23:00 UTC; hub plan ack 22:54)
- Owner: "think of parts people go to junkyards for. It wont be brake pads, its more likely other items."
- Ranking (yard price lists: chains pricing it out of 30 x median low price):
  1. rear-seat 21/$40
  2. sunroof 22/$31.8
  3. center-console 26/$19.5
  4. door-panel 25/$18
  5. blower-motor 25/$18
  6. backup-camera 14/$22.5
  7. fog-lights 27/$11
  8. door-handle-ext 19/$12
  9. door-lock-actuator 18/$11.5
  10. door-handle-int 14/$8.7
  11. tailgate-handle 5/$10.5

  pf/ search counts are too thin to weigh.
- Wave 1 (TIERS["D"], 8dbbe67): sunroof, center-console, door-panel (interior trim), blower-motor,
  fog-lights. Wave 2: door handles, lock actuator, backup camera, tailgate handle.
- rear-seat waits for an airbag rule. Seats can carry side airbags, and anything with an airbag is never included.
- Honda/Acura/Nissan/Infiniti tier D: left to session_016ZzJfMtLKpUFu8TiEFMrkF after its R3 work (hub).
  Ids, Honda slugs and method sent 22:57 UTC.
- Rules: interior categories keep colour/trim words in the name. A row naming an airbag is excluded.
  Worklist version = one above every tier already flagged.
- 22:55 UTC: local tier D list trials STOPPED after ~2 min. Run 42684614492 was crawling
  gm/mb/hyundai/kia, and local lanes on the same domains double the paced rate. No refusal was
  logged. Every site has CI work pending (markers.mode crawl/complete), so local trials wait
  for the hub's choice: (a) per site once its mode is None, (b) between runs, or
  (c) placeholder flags so CI reads the rows.
- Branch interchange/categories-2 (a6e5b04, stacked on categories-1, sw jh-v175, NOT merged):
  wave 1 app categories, body kind. Price tokens are exact rows (25-27/30 chains); notes cover
  colour, trim and option fitment.
- Hub 22:58/23:04 UTC: option (c) APPROVED, and ship the 14 new categories now with same-gen donors only.
  - main aee4fdc: tierD=1 placeholder flags on 14 sites (list pages only, confirmed in code).
    crawl.local_guard refuses local runs while CI work is pending; --scratch-offline = cache only.
  - crawl.tier_key: set "tierD": 2 together with the real rules, so the seeds are re-read
    (done keys and list lines "D2"). Tier D curation reads only the "D2" lines.
  - Branch interchange/categories-ship (380da21, sw jh-v176): categories-1 + categories-2 plus the
    GROUP_HOLD_CATS hold (no OEM/aftermarket group for the 14 until each §11.4), 1A if_equipped/
    cosmetic render, and kind wording. Sent to the hub for regression 23:50 UTC.
  - Not run here (no Python playwright): interchange_e2e, pf_ux_e2e, part_finder_e2e.
    Passed: ui_no_truncation (1296/0), pf_guards_unit, pf_new_cats_e2e, all unit suites.
  - 2026-11-10 00:56 UTC: categories-ship merged by the hub (ef5d52e6, sw jh-v176; interchange.json
    has 44 categories). Tiles unchanged (hub): propose tile changes with the next batch.
  - Crawl state 00:58 UTC: run 24 (dispatched 19:34, head b71585b) is still in progress (GM).
    Run 25 is pending (scheduled 22:32, head 435f911) and predates the tierD flags (aee4fdc), so
    it crawls tier C only. The tier D placeholder pass starts with the first scheduled run after
    25. Tier C data so far: vw, hyundai, kia.
  - Hub 01:15 UTC: from run 26, markers.mode runs own-page completion (c1) FIRST on any site with
    a previous-version marker and no c1.done. Category passes (tier C, tier D placeholder) resume
    after c1.done. Owner priority is depth on the existing categories first. Expect tier C/D rows
    later, site by site; don't edit markers.py (make breadth owns the change).
  - Next per site, once the CI placeholder pass has written its tier D list rows on oem-raw:
    write rules from raw/<site>.lists.jsonl, set tierD 2, raise the version, then ci_audit.
- Tier C priority: wiper-motor curation and §11.4 next, once honda/toyota/nissan have C data.
  Knuckle and strut audits are last.

## Aftermarket breadth (session_016ZzJfMnemMEFN88kPnYgxs, 2026-11-09)

Scope: more aftermarket application catalogs (owner: breadth + data
quality, no third-party costs). Verdicts in `scraper/oem_fitment/SOURCES.md`
"Aftermarket catalogs, probe 2026-11-09".

**Probe results.** Depo OUT (challenge). Four Seasons OUT (403 challenge).
SMP e-catalog OUT (403); ACI is an SMP brand, so OUT with it. Cardone OUT /
unreachable (product grid client-side; sitemaps and terms robots-disallowed
for us). Dorman, TYC, Denso stay out as decided. **Spectra Premium passes**
(ecat.spectrapremium.com: robots allow all, no challenge on catalog pages,
no anti-automation clause; Legal Notice has a no-reproduction clause for the
hub to weigh).

**Adapter (dde132d).** `aftermarket/spectrapremium.py`, vehicle-driven:
worklist (year, make) -> get-models.json -> exact-normalized model match ->
get-submodels.json (-> get-motorizations.json on comma ids) ->
`/en/vehicles/<id>/parts?limit=50`. One record per vehicle: year, make,
model, submodel, motorization (engine code), every part card (pn, line,
application note, specs). Seed year per worklist segment first, then the
other segment years >= 1995. Uses run.py (new `SITE_MODULES` map and an
optional per-module `score` hook) and common.get, so pacing, cache, RFC 9309
robots and the permanent stop are unchanged. Tests:
`aftermarket/tests/test_spectrapremium.py` (20 checks, offline fixtures).

Why vehicle pages: the part page prints applications without notes; the
note lives only on the vehicle page. Real notes seen on 2012 Civic LX:
radiator CU13221 "USA Built; Canadian Built" vs CU13257 "Japan Built"; fuel
module SP8054M Federal vs SP8965M California emissions; A/C accumulator,
evaporator and condenser split "Body Type: Coupe/Sedan". So curation will
refuse plant / emissions / option / trans notes, map "Body Type" to the body
gate, and pass only an allowlist of install-only clauses ("New", "with
Clutch", "Sensor Only", "Qty Req.", "Failure to ... void warranty", ...).
Unknown clauses refuse. Pages print no OE numbers, so no dealer OE join.

**Blocked on the hub (asked 2026-11-09):**
1. add `ecat.spectrapremium.com` to `fetch.ALLOWED`;
2. `fetch.CHALLENGE_RE` matches "captcha" in the reCAPTCHA `<script src>`
   tag on every ecat page (VIN form only); proposed narrow fix: ignore that
   exact tag, every other marker still stops. Not changed by this session.
3. then dispatch `oem-aftermarket-crawl.yml` with site
   `ecat.spectrapremium.com`.

**Hub, 2026-11-09 ~18:48 UTC: HOLD on Spectra.** Both points (captcha marker,
no-reproduction clause) go to the owner; the hub relays the answer. Nothing
allowlisted, fetch.py unchanged, no crawl. Second probe pass (CSF, OSC,
Eagle Eye, Koyorad, Nissens): none usable (SOURCES.md). Session stopped
here.

**Owner decision (relayed by the hub, ~19:41 UTC): "no email needed".**
Spectra stays OUT and gets no outreach. fetch.py and fetch.ALLOWED are
unchanged. The adapter stays on main, unused. No aftermarket source passed
this round. Session closed.

**REOPENED ~19:45 UTC.** Owner, verbatim, relayed by the hub: "use
spectra if it doesnt break anything". The hub approved detector rule
(a)-(e), scoped to the site (SOURCES.md has the rule and the evidence).
ecat.spectrapremium.com is now in fetch.ALLOWED. `fetch.challenged()` keeps
the old rule for every other host. Tests: `tests/test_fetch_challenge.py`,
real pages pass and 25 variants stop. All suites pass except
test_model_map, which fails identically on main: the known Honda "Cr-Z"
feed row, which clears after the rescan (ops/hub.md).

**Next:** the hub checks for running crawls and dispatches the crawl -> `groups_spectra` curation (one Likely group per Spectra
pn x line; engine gate on Eng. Desg./liters; body gate on Body Type; refuse
other notes) -> §11.4 sample per line -> hub -> branch
interchange/aftermarket-1 for any app change. Nothing shipped.
- **2026-11-09 ~19:00 UTC: three removal rules (hub-approved after the GM
  series sample found live WRONGs).** curate.py; claims only go down.
  1. Generation cut (`_generation_cut`): a Likely group of a superseding
     number (product page Replaces / replaced-by / list replaced-by / chain)
     may not cross a GENERATION_BREAKS break of any of its base models. The
     vehicle-years before the newest break crossed are left out, twins
     included. 20945139/38 (GMT900 front regulators that "Replace" the
     GMT800 numbers) lose Silverado 1999-2000 and Sierra 2004.
  2. EXPORT (`_export_only`, per row like the market rule): a row whose
     every option alternative names EXPORT (GM Z5X/DE2 export mirrors) is
     not listed for US feed cars. 27 GM groups go: DeVille/Seville, Astro/
     Safari, S-10/Sonoma, Tahoe/Yukon 1999, Rainier/Trailblazer and
     GMT900 export mirrors, a DeVille/Seville switch and a Rainier HVAC
     panel, plus 25876716.
  3. Cab note (`_cab_only`): when every fitment row crediting a model names
     one cab type, the group says "<model>: <cab> only". It is held
     (`held_cab_qualifier`) if the note would pass 160 characters; none is.
     11 GM notes gain it (15844876/77 "Silverado: extended cab only";
     Colorado/Canyon and Silverado rear doors "crew cab only").
  - Result: gm 309 -> 279 (30 removed, 3 lose apps, 11 notes). The other 7
    files are byte-identical. Full list:
    `groups/_report/rules_2026-11-09_generation_export_cab.txt`.
  - Tests for each rule both ways (test_curate). Gates: curation_tests
    16/16, tests 29/29, scraper tests, pf_guards ALL PASS, measure parity
    6/6, gm curate byte-identical twice, payload ok x8, test_groups_hash.
  - The GM series branch stays off main until a resample on these rules has
    0 WRONG.
## 2026-11-09 Same-engine relabel + Honda/Nissan start (session_016ZzJfK5RFgko9f1gx7qjEa)

Owner go via hub ("Yes relabel those, and start on Honda/Nissan").

### Task A: "Same engine — part may differ" (branch interchange/same-engine-label)
- `docs/app.js` engine path: a donor whose ONLY link to the seeker is the
  hand engine family (no hand/OEM vg names both cars, no aftermarket unit
  list names both) and that is a different base model (make or squashed
  model differs) gets `src: 'same-engine'`. Chip "Same engine — part may
  differ", tooltip: same engine, different model, accessories often differ,
  match the number on both cars. Engine assemblies are excluded.
- vg-joined donors that can't be Verified (engine unconfirmed, ambig) stay
  part-number-backed Likely. An aftermarket list naming both cars lifts a
  same-engine row to the aftermarket chip.
- Sort: same-engine rows after all others in both sort orders. Counts row:
  "N verified · N likely · N same engine". Cards keep `pf-likely` (+
  `pf-same-engine`), so "Verified fits only" hides them.
- Plain hand Likely tooltip reworded; "very likely fits" is gone.
- No gate, data or free/Pro change. sw jh-v169. Neutral `.pf-tier-same` chip.
- Tests: pf_guards_unit ALL PASS (+17 same-engine checks; 10 of them fail on
  the old app.js); part_finder_e2e 1 failure, the known E46 M3 data case
  (its sort check now allows the same-engine group last); pf_ux_e2e pass
  (counts parser takes the optional third count); interchange_e2e pass;
  ui_no_truncation: see below.
- GX 470 2005 alternator near 78744 (Austin): 0 verified · 0 likely · 64
  same engine (all Tundra/Sequoia; no GX/LX donor in range). No overflow at
  390 px. Shots: backend/test/shots_same_engine/ (light/dark × free/Pro).

### Task B: Honda/Acura, Nissan/Infiniti, step 1 (read-only)
oem-raw@75dc442. All four sites `.done`; honda also `.retried503`.
| site | records | list rows (R1) | year manifests | errors |
|---|---|---|---|---|
| hondapartsnow | 1465 | 342 lines | 50 | 3 |
| acurapartswarehouse | 748 | none | none | 3 |
| nissanpartsdeal | 3911 | none | none | 9 |
| infinitipartsdeal | 1775 | none | none | 27 |
Local curate (`curate.py --ns honda --ns nissan --raw-ref origin/oem-raw`):
honda 0 Likely (8,746 list rows, but they cover seed years only:
likely_app_years_without_own_page e.g. side-mirrors 1,411, window-regulator
924); nissan 0 Likely (no manifests at all; side-mirrors 2,203,
window-regulator 2,981 app-years without own page). Also: no audit record in
audits.json for any of the four sites, and all four print an option column
(never coverage, spec 5.5), so Verified stays impossible there.
Next: R3 completion run over the completion worklists (honda.completion.json /
nissan.completion.json), plus R1 manifests on acura/nissan/infiniti.

### Blocked (this session)
- `git push` refused by the git proxy: benvuolo/yardscout is not in this
  session's authorized repo set; the add_repo call was denied. The `gh` token
  is invalid, so no workflow dispatch either. The branch and this note exist
  only in this container until access is fixed.
- **2026-11-09 ~19:00 UTC, state when this session paused:**
  - **Curate is blocked for everyone** by inventory 77423a1: one feed car is
    spelled "Honda Cr-Z", so model_map M3 fails. Fix:
    `"crz": "CR-Z"` in junkyard_scraper `_MODEL_CANON` + rescan
    (Data-quality, ops/data.md). The scan payload is unaffected.
  - **GM series filter** (branch `make-breadth-gm-series`, c1f13ec, rules
    1-3 merged, all 8 re-curated under the branch hash). Fresh resample of
    20 of the 32 changed groups: **RIGHT 16, WRONG 0, UNSURE 4**
    (15844876/77 rear-door motors, 20862099 towing mirror for the 2007
    Avalanche, 20787113). Sent to the hub; ships on its confirmation once
    curate runs again (re-curate all 8 in the same push).
  - **Live note bug, fix on branch `make-breadth-pack-note` (8f16996):** 69
    shipped climate-control groups say "regulator with motor" (gm 24,
    mopar 24, subaru 9, ford 7, toyota 5). `_pack_text` limits packaging
    words to their category. Claims unchanged. Needs a re-curate of all 8
    and then a push.
  - **Next:** when `.c1.done` lands per site: re-curate, then a §11.4
    sample per namespace (bmw, mb, vag, volvo, mazda, mitsubishi, hmg,
    toyota/lexus, ford, mopar), checking unseen-option splits (heated,
    power-fold, turbo, km/h, export) in each sample.
- **2026-11-09 ~19:25 UTC: both pending pushes shipped (hub confirmed).**
  - 661d537 note fix: 69 climate-control notes no longer say "regulator
    with motor". Claims unchanged.
  - c5d7f44 (+ merge f9423ed) GM series filter: 32 groups now name
    "Silverado 1500"/"Sierra 1500"; 20862099 carries the towing/standard
    note (`policy.GROUP_NOTES`). Diff: `_report/gm_series_2026-11-09_diff.txt`.
  - Both curated with `--inventory` = inventory_live.json at 7192563
    (pre-Cr-Z; hub allowed). From the next re-curate on, use the live
    inventory once the scan republishes with "CR-Z" (hub 1cf5dd0).
  - Failing on plain main as well, not from these pushes:
    test_model_map (live Cr-Z row; clears after the rescan) and
    test_jeeppartsdeal (asserts worklist version 2; the tier C session
    raised it to 4).

## Wheels (session_016ZzJfL4wG1wgpyYymW2Z28, 2026-11-09; branch interchange/wheels, applied and pushed by the hub)

Owner: "Yes relabel those, and start on Honda/Nissan and wheels". The hub approved the proposal on these bases:
- (b) Shipped on this branch.
  - What: a `wheels` body category, same model + same generation donors only, always Likely.
  - Row check: "count the lugs; read the size on the back (e.g. 17x7J), offset and hub bore". 2WD/4WD and HD versions can differ in bolt pattern within a generation.
  - Notes: TPMS ("most 2008+ cars have one"), lug nuts and lock key, no compact spares, curb rash, and tire size gives the diameter.
  - Price: one ALLOY wheel, rim only. It reads "Yard: $X each (YARD ROW NAME)" so the size tier is visible. There's no savings line, because online values are for a set of 4.
  - Price-token coverage: 24 of 30 yard lists. Combos, sets, steel, dually and scrap rows never match.
  - Wheels stay an `option` row in the car-card parts table: $0 to ranking.
  - Example: 2009 Camry near 85003 → 27 Likely donors.
- (a) OEM wheel part numbers: crawl tier "W" (crawl.py TIERS["W"]=["wheels"]). It runs only for worklist sites with "wheels": true.
  - Rules exist for fordpartsgiant (base 1007, subcats wheels/wheels_related_parts), jeeppartsdeal (suspension/wheels; worklist v3) and lexuspartsnow (disc_wheel_wheel_cap, "WHEEL, DISC").
  - Spare, temporary, compact wheels, caps, nuts, locks, weights, valves and TPMS sensors are excluded.
  - Audit risk: Toyota/Lexus spares are also "WHEEL, DISC". Curation must check remarks or own pages for T-type spares.
  - Groups publish only after a §11.4 sample with 0 WRONG and hub confirmation.
- (c) Spec matching (bolt pattern / bore / offset): NO. No source passes rule 2 with a stated basis. vPIC has no bolt pattern.
- Not yet covered: GM, VW, MB, Hyundai rules, the no-manifest makes, and Honda/Acura/Nissan/Infiniti (another session). Mopar's moparpartsgiant is blocked, and Subaru is withheld.
- Tests: pf_guards_unit ALL PASS; test_interchange pass (30 categories); oem_fitment tests 30/30; curation_tests pass; scraper/test_*.py pass.
- Patch transfer: the originating session couldn't push. The hub applied its diff on 533b3c1. Unicode escapes in app.js were restored, and the wheels entry in interchange.json was regenerated with build_interchange_payload().

### Wheels, continued (session_016ZzJfKi8ND3Ey2g66qhiZT, 2026-11-09)

- (b) merge fixes, commit 52d9aa2:
  - Header reads "carrying fitting wheels" (no "a" before a plural label). The browse note no longer doubles a plural ("wheelss").
  - The online value on a wheel row reads "for a set of 4", because the yard price is per wheel.
  - Size-tiered yard lists show the full per-wheel range with both row names, e.g. "Yard: $28.99–$37.99 each by size (WHEEL ALUM UNDER 16" … WHEEL ALUM OVER 17")". The old code quoted only the cheapest tier, which is the wrong price for a 16–17" Camry wheel.
  - Seven lists price wheels by size: ace, chesterfield, chuckeddies, p195, pnpsa, pns, usauto. Every row the wheel tokens match there is an alloy-wheel size tier (checked against all `*_pricing.json`).
  - pf_guards_unit has a check for each of the three changes.
  - Screenshots: `ops/screens/wheels_2009_camry_85003_390_{light,dark}{,_row,_priced}.png`. 2009 Camry near 85003: 27 Likely donors, 22 of them with a yard price.
- (a) tier W rules for GM, VW, MB and Hyundai, commit 3177cbb. Each was checked on one real wheels list page, read through fetch.py on 2026-11-09; all four answered 200.
  - gmpartsgiant: subs `wheels`, `wheels_wheel_covers`, `wheels_hub_caps`. Noun WHEEL.
    - The 2016 Trax row "WHEEL, Rear or Spare" (18X7) is kept: it is a full-size road wheel, and the group text is the illustration heading.
    - Dropped: a "WHEEL, Spare…" heading, or a remark (including inside parentheses) that says spare, temporary or compact.
  - vwpartsgiant / mbpartsgiant: `suspension/wheels`, anchored names. "Wheel, Alloy" and "Wheel Alloy" are kept. "Spare Wheel", "Wheel, Spare", bolts, bolt caps, lock kits, center caps, hub caps, covers and valve stems miss the include. MB lists accessory wheels (6-6-03-xxxx) as "Wheel, Alloy": their product pages decide fitment.
  - hyundaipartsdeal: `chassis/wheel_cap`. "Wheel Assy-Aluminium" / "-Steel" are kept. "Wheel Assy-Temporary", caps, hub nuts and spare-tire clamps/pads are dropped, as is any row that says spare, temporary or compact.
  - Worklist: `wheels: true` on all four. VW, MB and Hyundai go to version 2 to re-open their done sites. GM is not done, so tier W follows its A/B crawl.
  - Kia reuses Hyundai's PARTS and SUBCATS, so its rules exist, but it is not flagged: not asked yet. It is a one-line worklist change if the hub wants it.
  - Tests: test_wheels_rules covers the real row names and the subcat/page regexes. oem_fitment tests 30/30; curation_tests all PASS.
- Main merged in twice (e0e6c90, then again for d2a54d6). Resolution, as the hub asked:
  - crawl.py: tiers A, B, W, C, with TIER_FLAG `W: wheels`.
  - Site modules: tier C and wheels entries side by side.
  - Worklist: `complete` and `wheels` keys side by side. No wheels site has tierC, so the versions don't collide.
  - pf_guards_unit: main's same-engine block, closed, then the wheels block.
  - interchange.json: main's file plus the regenerated wheels entry (verified identical apart from wheels).
  - sw.js: jh-v172.
- Kia on tier W (worklist version 2). It uses Hyundai's rules: the 2013 Optima chassis/wheel_cap page, read through fetch.py, uses the same names.
- Fix found on that page: every road wheel's Fit Note lists the car's options, including "TEMPORARY - STEEL WHEEL & TIRE (MINI)". The first Hyundai rule searched the whole row for spare words, so it dropped all 5 Optima road wheels. The spare check now reads only the part's own name and remark. Optima: 4 alloy + 1 steel kept; 2 "Wheel Assy-Temporary" dropped.
- Curation note: the PartsGiant Fit Note is car options, not the part's identity. Don't read spare words in it as a spare.
- test_model_map (curation_tests) fails identically on origin/main: Honda "Cr-Z" feed spelling, M3/M5. It belongs to the Honda/Nissan session; I haven't touched it.

## Source scout 2 (session_016ZzJfKZ49mzzQhu4KT7HkU, 2026-11-09)

Verdicts in `scraper/oem_fitment/SOURCES.md` "Source scout 2 (2026-11-09)".
About 28 hosts probed gently (robots read first, 5-6 s apart, a few GETs
each); nothing allowlisted or crawled.

- **Passes, pending hub:** GSP North America (gspnorthamerica.com). It has
  server-rendered per-part "Applications" tables (cv-axle first, strut
  second), specs, and no published terms ("Coming soon...").
  - Needs a site-scoped rule for Shopify's form `captcha-bootstrap` script.
  - Data caveat: the tables drop engine, drive and trans qualifiers.
  - Adapter plan written; not built.
- **Owner decision:** 1A Auto. Its licence is personal and non-commercial,
  with a no-reproduction clause; no anti-automation clause was found;
  fitment rendering not confirmed.
- **OUT:**
  - anti-automation clause: Monroe and Moog (DRiV/Tenneco), Mevotech;
  - robots `Disallow: /`: TRW/ZF;
  - challenge or 403: KYB, Bilstein, ACDelco/gmparts, ShowMeTheParts,
    Opticat (Walker), BBB;
  - lookup on a refused platform: FCS.
  RockAuto is out because a captcha marker is on every page and its terms
  sit under robots-disallowed `/info/`.
- **Not qualified:** UAC (POST-only AJAX; no POST sent), LKQ Online (JS
  shell), GPD (stub).
- **Unreachable:** Gabriel, fordparts.com, parts.toyota.com, WAI.
- **Unresolved:** Delphi (catalog probably client-side).
- **Next:** the hub confirms the GSP rule and the allowlist, and sends 1A
  Auto to the owner. Then build `aftermarket/gspnorthamerica.py` with
  offline fixtures and crawl cv-axle.
- 2026-11-09 ~20:13 UTC, the hub: HOLD. GSP (detector rule) and 1A Auto
  (licence) go to the owner. The hub recommends GSP yes (Likely-only, strict
  refusals, drive/trans never inferred) and 1A Auto no. UAC skipped
  (POST-only). Until the owner answers: ALLOWED and fetch.py stay unchanged,
  and nothing is built or crawled. Scout session stopped.
- 2026-11-09 ~20:15 UTC, owner (via the hub): GSP "Yes, use GSP" and 1A Auto
  "Yes, use 1A Auto anyway".
  - GSP: the approved "no other marker" rule fails on real pages. There are 68
    "captcha" matches per page, all inside `<script>` elements (Globo Form
    Builder config, translation strings). A corrected rule went to the hub at
    ~20:16. Adapter `aftermarket/gspnorthamerica.py` is on main (159f5634).
    Not allowlisted.
  - 1A Auto: confirmed server-rendered GET (fitment table + Part
    Interchange). Adapter `aftermarket/oneaauto.py` (358b0785, 12 categories,
    strut first). Allowlisted (e5cda1a9). Dispatch body
    `{"ref":"main","inputs":{"site":"www.1aauto.com"}}` sent to the hub.
  - test_model_map fails on clean main (feed "Cr-Z" spelling, M3/M5). Reported
    to the hub; not ours.
  - Next: the hub dispatches 1A; GSP after the rule answer. Then curate,
    then the §11.4 sample per source × category.
- ~20:35 UTC: GSP rule approved by the hub, implemented (`fetch.gsp_challenged`)
  and allowlisted (e35d16ae); tests in `tests/test_fetch_gsp.py`. The owner
  added for 1A: "im not selling the part fitment portion". So 1A fits are never
  behind Pro and 1A prices/descriptions/images are never shown. The free = Pro
  render test is a ship blocker, to be written at integration. Part
  Interchange numbers are brand equivalence only, never vehicle fitment.
  Dispatch bodies for GSP and 1A sent to the hub. Waiting for the hub to
  dispatch them; then curate and run the §11.4 sample.
- ~20:45 UTC: `oem-aftermarket-crawl.yml` is now a plan + matrix (33655227):
  every `STATUS = "ok"` adapter not .done/.blocked, max-parallel 3, one run at
  a time, schedule = all. The hub dispatched 1A (queued behind Spectra). Test
  dispatch of "all" waits for the current runs to finish and for the hub's
  word. CR-Z model_map failure: fixed upstream in 1cf5dd03; it clears after
  the next scan.
- **2026-11-09 ~21:05 UTC, fetch.py --text truncation (hub audit item).**
  `--text` used to clip silently at 400 lines. It now defaults to
  5000 (`fetch.TEXT_MAX_LINES`). A clipped page ends with
  "[TRUNCATED at N of M lines]" and carries `text_truncated` /
  `text_lines_total`. Test: tests/test_fetch_text.py (9 checks).
  Audit of my §11.4 rounds (Subaru R1-R4, GM rules 1-3 sample, GM series
  resample; 13 verifier transcripts): none ran fetch.py. They read
  the sample files plus outside sources (WebSearch/WebFetch). The sample
  builder passed own-page manifest rows whole and capped each record's
  evidence_lines at 60. None of the 86 sampled items (Subaru 60, GM 26) has
  a record over 60 lines, so nothing was hidden. No verdict changes; no
  group pulled.
- §11.4 verifier brief, Honda/Nissan (hub note, 2026-11-09 20:55): until
  make breadth's truncation marker lands, `fetch.py --text` stops at 400 lines
  without warning. Verifiers must pass `--max-lines 100000` or read the cached
  HTML directly, so long list pages are not cut.
- Audit note from the hub (~20:55 UTC), for the GSP and 1A §11.4 runs:
  `fetch.py --text` cuts output at 400 lines unless `--max-lines` is passed.
  Verifiers pass `--max-lines 100000` or read the cached pages directly.
- 21:10 UTC, first checkpoints of run 42694329196:
  - GSP passed the detector: 200 cv-axle records, 209 requests, no .blocked.
    20% have duplicate_rows (they refuse). Half the rows name a submodel.
    88 titles list no engine.
  - 1A Auto passed: 113 strut records, no flags, all with Part Interchange.
    The Description column carries trim and body qualifiers (Sedan, Sport,
    Coupe, "without …"); curation must gate or refuse on them.
  - Spectra: no new checkpoint after the 20:20Z run (records=0); flagged to
    the hub.
  - Next: curation (`groups_gsp` / `groups_1a`) once the hub says go, then
    §11.4.
- ~21:45 UTC: curation is on main (a9f551c7, `aftermarket/groups_rows.py`).
  - Rules: Likely only. Every row is a claim, and a corner-year is dropped
    when the same brand and kind has more than one unit for it. Qualified
    rows refuse, except a 1A engine qualifier, which becomes the engine. GSP
    title rules as listed in the hub message. No body gating, because
    `pfAmRows` ignores a[5].
  - Tests: 33 checks, including the free = Pro render guard and the
    facts-only check.
  - First slice: GSP 200 units → 15 groups; 1A 113 → 69. Neither crawl is
    complete.
  - §11.4: proposed to run per (site, category) once its crawl completes,
    with an independent verifier and `--max-lines 100000`. Waiting for the
    hub.
- ~22:10 UTC: 1A strut shakeout. Independent verifier, 29 fetches, 10
  groups: 1 WRONG, 7 RISK, 2 CORRECT.
  - The WRONG was 1ASTS01913: "Front Wheel Drive Front Passenger Side" was
    parsed as a bare front, which lost the side and the drive qualifier.
  - Fixes (d2cc68da): use the last position phrase; every qualifier
    refuses, engine included; refuse unqualified rows that have qualified
    siblings; refuse plain strut rows on suspension-option models; refuse a
    1A unit with several same-brand interchange numbers.
  - 1A strut 69 → 8 groups; GSP 15 → 13. Rule 5 strictness and
    generation-boundary handling are with the hub. The full §11.4 sample
    still waits for crawl completion.
- ~22:30 UTC, hub decisions applied (942c2481):
  - Rule 5 stays strict.
  - Rows crossing a generation boundary in the app's `modelGenerations` are
    refused; a model with no entry passes only spans of 6 years or fewer.
  - Notes say to match trim and suspension.
  - First slice: GSP 12 groups, 1A strut 8.
  - Waiting for crawl completion per (site, category) before the full §11.4
    sample. The hub pings this session.
### Wheels curation, first pass (session_016ZzJfKi8ND3Ey2g66qhiZT, 2026-11-09 ~20:00 UTC; branch interchange/wheels-curation)

- Raw used: oem-raw@4a733550 (tier W partly crawled for Ford, the Jeep site and Lexus; run 42666726212 still going). Records: Ford 435, Jeep site 541, Lexus 233.
- Scratch curate run. It isn't committed: the committed model_map fails M3/M5 on the new "Cr-Z" feed spelling, so I passed `--inventory` an inventory_live.json from fba7905 (13:38 UTC, before the spelling appeared).
- Real list manifests vs the crawl rules:
  - Lexus is clean: 177 "(For Spare)" rows dropped.
  - Ford's crawl rule kept designated spares: the "Wheel Assy - Spare" / "17\" Mini Steel Spare Wheel" text is in the row's extra field, which the rule doesn't read.
  - Mopar's crawl rule kept "[TBK] Compact Spare" rows.
- Curation fix (a210d2e): `wheel_compact_spare` refusal.
  - A compact / mini / temporary / T-type mention refuses every record of that (site, pn).
  - Notes aren't read where they list the car's options: Hyundai/Kia Fit Note, Toyota/Lexus info. "&SPARE TIRE-REINFORCED TEMPORARY(T165/90D18)" sits on 19\" RX road wheels.
  - Full-size spares that are the road-wheel number stay. Lexus "Wheel, Disc" and "(For Spare)" print the same number on the same page; Mopar "Spare Wheel, 16x6.5" next to "Steel Wheels, 16x6.5\"".
  - Refused: Mopar 6 numbers, Ford 15, Toyota 0. Only one of them had formed a group: 4721567AB, 2010 T&C / Grand Caravan, WRONG without the fix.
- Scratch result after the fix:
  - mopar: 83 Likely wheels groups, 31,674 lot cars.
  - toyota: 52 groups, 3,048 cars.
  - ford: 0 (its option column means its fitment rows are never coverage).
  - Every group is `reason: option`, Likely.
- The policy.py change moves the policy hash, so every committed namespace fails V8 until re-curated. It should land together with the re-curate that ships wheels.
- §11.4 audit: not started. It needs ~100 fetch.py reads on the Jeep site and Lexus, which run 42666726212 is crawling now. Fetching in parallel would double the request rate on those sites (503 risk, which stops a site for good). It starts when that run ends.
- §11.4 round 1 (30 groups, separate verifier, fetch.py sequential, 0 refusals): 19 OK / 10 WRONG / 1 UNSURE. Fixes in eaff7ef:
  - Toyota namespace: wheels groups stay within one exact model, because sibling-chassis codes limit the row.
  - Mopar: every own page must state the diameter, all equal; a note mentioning a spare or another numbered model refuses the group.
- §11.4 round 2 (census of all 32 Mopar groups): 29 OK / 2 WRONG / 1 UNSURE.
  - The 2 WRONG had equal diameters but different widths: 1SZ98PAKAA 15x6 vs 15x7; 1DP88SZ0AB "20x9, Code WP2" vs "20x8, Code WP2".
  - The UNSURE was 5105665AA, whose product title is "Spare Wheel, Steel".
  - Fix: stated widths must agree too, and a record description naming a spare refuses the group (19 of 541 Mopar wheel records).
- Result (scratch, raw f2078e0a): mopar 29 groups, 9,613 lot cars, every one OK in the census, with no new group. toyota 0, ford 0.
- Still to do: one push with policy + all 8 shipped namespaces re-curated on the republished inventory (after the Cr-Z map fix) + test_groups_hash green, after the hub confirms.
- Verifier note: `fetch.py --text` prints only 400 lines unless --max-lines is given (hub is fixing it).
- 2026-11-09 ~23:00 UTC, single push (hub-confirmed):
  - All 14 namespaces curated `--ns all` on oem-raw@3b4677ae with the republished inventory (scan 435f911; model_map check clean). The 8 shipped group files are committed; the 6 unshipped namespaces' new group files and own_page_completion reports are not.
  - Diff vs main: the only additions are mopar +29 wheels groups (all OK in the census, 5105665AA absent, 9,610 lot cars). No group removed anywhere. Every other changed field is `cars` (new inventory).
  - held_exterior.json reflects current code: Subaru option holds (gauge-cluster, side-mirrors) added; allowlist-released GM/Subaru entries gone. Shipped groups unaffected.
  - New WHEELS_AUDITED_NS = {mopar}. hmg (17), mb (14) and vag (5) wheels groups from today's tier W crawl are refused `wheels_not_audited` until their own §11.4 round.
  - Payload: new lazy file docs/data/oem/wheels.json (29 groups). interchange.json changes only builtAt, oemStatus and the oemLazy index.
  - pf_guards_unit: the wheels block now loads an empty wheels lazy file. New check: a shipped wheels group adds the cross-model donor as Likely.
- ~23:10 UTC: owner priority, junkyard-demand lines. Probed 1A (18 fetches,
  no refusals). All lines are server-rendered.
  - Viable now: headlights, tail lights (plain rows; "Sedan" rows wait for
    a[5]), blower motors. They need side-only positions plus a
    FACELIFT_BREAKS guard on lamps.
  - Mirrors and door handles need a qualifier grammar (body / option /
    cosmetic).
  - Regulators need a rule-5 change for alternate spellings.
  - Lock actuators: trim-qualified, so low yield.
  - Wiper motors and fog lights: not sampled yet.
  - 1A interchange tables carry OE numbers (a possible OE join). All of this
    is with the hub; nothing added to the crawl yet.
- 2026-11-09 22:56: R3 has not crawled yet. Run 42684614492 (19:34) was
  dispatched with an explicit site list (gm, vw, mb, hyundai, kia) and left
  out these 4. Scheduled run 42712787314 (22:32, sites=all) is pending
  behind it; its plan step picks the 4 up in complete mode.
- Tier D (category-breadth request, plumbing 8dbbe67) is held until R3
  finishes on these sites. A local trial overlapping a CI crawl doubles the
  request rate per site, and hondapartsnow has already used its one 503 retry.
  Order after R3: slug map, scratch `--tier D --max-segments 2` trial, every
  row read, strict rules (colour words kept, airbag rows excluded), product
  trial, ci_audit, flag one version above every flagged tier.
- ~23:45 UTC, hub items 1-3 done (3561c95f):
  - 1A crawl order now starts with the junkyard-demand lines: headlight,
    tail/fog light, blower, mirror, door handles, regulator. Strut is
    paused, with its progress kept.
  - Lamp guard on FACELIFT_BREAKS; side-only positions.
  - Rule 5 normalizes separators and case only.
  - Qualifier grammar: body gate held behind EMIT_BODY_GATE; options become
    "if equipped"; colour/finish is a cosmetic note; anything else refuses.
  - Data so far: GSP 833 units → 30 groups; 1A strut 494 → 105.
  - Item 4 (OE corroboration) waits for the new lines' data.
- ~00:05 UTC: GSP/1A output now uses the app's category ids: headlights,
  tail-lights, side-mirrors, fog-lights; the rest are unchanged (b672c437).
  A test checks that every emitted id exists (app list, crawl.TIERS,
  coverage_matrix, or the wave-2 pending list). Category breadth was asked
  to confirm `door-handle-int` and that pfAmRows renders `if_equipped`.
- 2026-11-09 ~23:20 UTC, MB + VW wheels §11.4 census (separate verifier, 37 reads via fetch.py --max-lines 20000, 0 refusals; raw cdc18a67): 19 groups, 17 OK / 1 WRONG / 1 UNSURE.
  - WRONG: 1J0-601-025-AB-Z31. Jetta 2003 "Wagon, ... 17X7" vs Beetle 2003 "Coupe"; the Jetta row is wagon-only.
  - UNSURE: 5K0-601-025-AN-8Z8. GTI "17\", 10 Spoke" vs Golf "17\", 8 Spoke, Porto".
  - Also flagged: front-only / rear-only staggered W204 C-Class wheels.
  - Fix (group rules; they only remove claims):
    - body words in the own-page notes must be identical on every app page (wheel_body_conflict);
    - stated spoke counts must agree (wheel_design_conflict);
    - a Front/Rear axle note refuses the group (wheel_axle_limited): the finder has no axle field for wheels.
  - Result: mb 10 groups / 243 cars, vag 3 / 117, all census OK, no new groups. Mopar 29 -> 28: 5105691AB (Sebring 2008 note adds "Convertible", Avenger 2013 doesn't) is refused by the body rule. Conservative.
  - Not shipped yet: WHEELS_AUDITED_NS still {mopar}; needs hub confirmation, then one push (policy + all namespaces re-curated + payload).
  - hmg (Hyundai/Kia) waits for its crawl (run 42684614492) to finish.
- 2026-11-09 ~23:40 UTC, MB + VW single push (hub-confirmed): WHEELS_AUDITED_NS = {mopar, mb, vag}.
  - Re-curated `--ns all` on oem-raw@1351c33f with the current inventory.
  - Diff vs main: mb +10 wheels, vag +3 wheels, mopar -1 wheels (5105691AB, body rule). Every other namespace's groups identical.
  - All 41 shipped wheels groups are census OK.
  - Payload: only data/oem/wheels.json changes in content (41 groups); oemStatus mb 10, mopar 309, vag 19.
  - Gates: curation_tests 17/17 (incl. test_groups_hash), oem_fitment tests 39/39, pf_guards_unit ALL PASS, scraper/test_*.py pass, pf_ux_e2e + interchange_e2e pass, part_finder_e2e only the E46 M3 case.
- ~00:20 UTC, category breadth: the render for `if_equipped` and `cosmetic`
  is on interchange/categories-ship. Nothing is merged yet. GROUP_HOLD_CATS
  holds every new category's groups until its §11.4 passes and the hub
  confirms. At clearance, headlights, tail-lights, side-mirrors and
  window-regulator must be added to `_AM_CATS`; that's a category-breadth
  change.
- 23:30 UTC check-in: GSP cv-axle 1,043 units → 40 groups (9 sitemaps pending); 1A strut 616 → 141 (lamp lines start on the next run). Nothing finished or blocked.
- 2026-11-10 00:08 check-in: R3 has still not crawled. Run 42684614492 has
  one job left (gmpartsgiant, cap about 02:16). Scheduled run 42712787314
  (sites=all) is pending behind it. No .c1.done, .blocked or .paused for the
  4 sites. Next check about 03:28.
- 2026-11-10 ~01:10 UTC, Hyundai/Kia (hmg) wheels §11.4 census (separate verifier, 24 reads, 0 refusals; raw 112c4593): 17 groups, 9 OK / 8 WRONG, all 8 on 2010-13 Forte / Forte Koup.
  - Root causes: the shared catalog's row "Fitting Vehicle Options" body code ([Coupe - 2Door 5P] / [Sedan - 4Door 5P] / [Sedan - 5Door 5P]) separates the models (7 groups); a row "Production Date" range excluded the app year (2 groups).
  - Fix:
    - wheel_body_option: in a cross-model group, a row or product page whose body codes are fewer than its own page's body codes refuses the group;
    - wheel_production_date: the row dates must cover the app model year (first .. last + 1).
  - Result: hmg 9 groups / 1,784 lot cars, exactly the census-OK set. mopar / mb / vag unchanged (28 / 10 / 3).
  - hmg is not in WHEELS_AUDITED_NS until the hub confirms.
- 2026-11-10 ~01:40 UTC, hmg single push (hub-confirmed), based on ef5d52e:
  - WHEELS_AUDITED_NS adds hmg. Re-curated `--ns all` on oem-raw@dca9cd84.
  - Group diff vs main: hmg +9 wheels (all census OK, 1,784 lot cars) and +39 strut. The struts are tier C output already on raw before the hmg wheels round, with no pinnable raw without them. strut is in GROUP_HOLD_CATS, so none ship. Other namespaces identical.
  - Payload: only data/oem/wheels.json changes in content (50 groups: mopar 28, mb 10, hmg 9, vag 3) plus the oemLazy index. oemStatus hmg reads "54 groups", counting the held struts.

### Aftermarket breadth: Spectra crawl, curation, §11.4 (2026-11-09/10)

- **Crawl.** oem-aftermarket-crawl matrix (hub), Spectra depth-first by lot
  value (518b146). No detector stop. 1,505 vehicle records on oem-raw by
  ~02:00 UTC 11-10.
- **Curation.** `aftermarket/groups_spectra.py` writes to
  `aftermarket/curated/spectrapremium.json`; not shipped, not under groups/.
  Rules:
  - notes are classified clause by clause; refused: plant, region,
    emissions, single transmission, duty, position, sizes, body codes and
    anything unknown;
  - "Body Type" -> body gate; "Drive Type" -> drive gate (hub);
  - FLEX: only beside the same GAS unit, never on fuel lines (hub);
  - every config of a key must agree (see round 1).
  Tests: `tests/test_groups_spectra.py` (58).
- **§11.4 round 1: FAILED, 10 WRONG of 347 page checks** (independent
  agent, 106 groups).
  - One real wrong part: 2014 Fusion 2.0L fuel module, gas SP2500M vs
    hybrid SP2515M.
  - Root cause: non-gas configs were dropped before the consistency check.
    They share the gas car's key, which a lot decode can't split.
  - Fix 98e5997: every config of the key, whatever its fuel, must list the
    same unit; fuel lines drop keys that have any non-gas config.
  - Of the rest: 3 hybrid and 1 FLEX row are covered by the same fix;
    3 diesel rows were my brief's mistake.
- **After the fix:** 628 groups, 151 cross-model (1,505 vehicles).
- **Coverage (upper bound, 1,002-vehicle build, % of 338k lot cars with
  a donor beyond same model + generation; baseline 0%):** coils 7.9,
  throttle 5.5, compressor 3.1, heater 3.1, radiator 2.3, evaporator 2.1,
  condenser 1.7, fuel module 1.0, tank 0.5.
- **App side:** category-breadth branch `interchange/categories-1`
  (e4d6373), not merged; gates as a dict in a[5].
- **Next:** §11.4 round 2 (fresh seed, all configs of one row per group)
  -> hub.
- **2026-11-10 01:15 UTC check-in.** No `raw/*.c1.done` yet. Completion has
  read pages only on hyundai (48), kia (59) and vw (50), before their tier C
  bump. All 15 completion sites wait behind re-opened worklist passes: the
  tier C vN flags and the tier D placeholder pass (aee4fdc). markers.mode
  runs completion only after the current worklist marker. Asked the hub
  whether completion should go first on gm/ford/mopar/toyota (that would be
  a markers.py change; not touched). The live inventory has been rescanned:
  test_model_map OK, so curate uses inventory_live.json again (no
  `--inventory` workaround). Next check-in ~07:15 UTC.
- **2026-11-10 ~01:40 UTC, completion first (hub plan, owner priority:
  depth on existing categories before new ones).** markers.mode: a site
  whose worklist was re-opened (no current-version marker, but an earlier
  version's marker) runs its own-page completion before the re-opened tier
  C/D pass. Once `raw/<site>.cN.done` is on oem-raw it goes back to the
  current pass. First-pass sites (gm) and .blocked/.paused are unchanged.
  Same rate and limits, CI only. Test: tests/test_markers_mode.py (12
  cases). `--ns all` re-curated on dca9cd845f26 (the raw ref of main's
  groups): all 8 shipped files byte-identical, so the groups diff is empty.
  Applies from crawl run 26.
- 01:30 UTC check-in: GSP cv-axle 2,097 units → 90 groups (8 sitemaps pending); 1A strut 1,042 → 232 (the old-order run is still going; lamp lines start on the next run). Nothing finished or blocked.
- **§11.4 round 2: PASSED, 0 WRONG** (2026-11-10).
  - Fresh seed, new independent agent, 108 groups (66 cross-model),
    597 vehicle pages incl. every config of one row per group.
  - Per category OK/WRONG: compressor 65/0, condenser 81/0,
    evaporator 59/0, fuel module 62/0, tank 63/0, heater 74/0, coils 71/0,
    radiator 51/0, throttle 71/0.
  - Part pages: 104 agree, 1 partial, 3 inconclusive (coil lists longer
    than the 12-page cap), 0 disagree.
  - The 1 diesel row is OK.
- **Gated coverage** (fixed build, 1,505 vehicles, 628 groups; % of
  338k lot cars beyond the same model + generation; baseline 0): coils
  11.05, throttle 7.56, heater 5.65, compressor 4.88, condenser 3.95,
  evaporator 3.38, radiator 3.34, fuel module 1.29, tank 0.53.
- **Hold:** no Spectra group file is committed (aftermarket/curated/ is
  git-ignored, d27588c). Coils and tank aren't in _AM_CATS; the 7 others
  are in GROUP_HOLD_CATS.
- **Next:** the hub's confirm, then branch interchange/aftermarket-1
  (spectrapremium.json + _AM_LABELS + coils in _AM_CATS). The category
  release is category-breadth's. Each re-curation needs a fresh sample.
- 2026-11-10 02:45 UTC, GM wheels: no tier W records yet. GM's job in run 42684614492 ended with tier A done (344 seeds) and tier B at 257. Run 42712787314 continues it at about 15 B seeds per 70 min, so B finishes in ~7 h and W (~344 seeds) then takes more than a day at that pace. The GM wheels round starts when tier W output lands; check-in scheduled.
- Live check 01:49 UTC: yardscout.io data/oem/wheels.json serves 50 groups, interchange.json 44 categories (after the 01:12 scan revert was repaired by ec59413 / 838ca47).
- **Hub CONFIRMED (2026-11-10 02:38 UTC)** radiator, ac-compressor,
  ac-condenser, heater-core, evaporator, throttle-body, fuel-pump-module,
  ignition-coils. fuel-tank stays out.
- **Ship branch `interchange/aftermarket-1`, head 723ec40 (not merged; the
  hub runs its regression):**
  - groups/aftermarket/spectrapremium.json, 613 groups, pinned
    oem-raw@ac4d1f0d (byte-identical to the round-2 sampled raw).
  - Per-source release AM_RELEASED; GROUP_HOLD_CATS unchanged.
  - ignition-coils added to _AM_CATS; "Spectra Premium" label.
  - Tests: test_am_gates, pf_new_cats_e2e, test_lazy_payload guard.
  - Payload diff: only Spectra amGroups added; OEM unchanged (ok ×8).
- **Rule:** any later re-curation (oem-raw had 1,998 vehicles at ship
  time) gets a fresh §11.4 sample before it replaces the shipped file.
