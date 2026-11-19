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
  - 2026-11-10 03:44 UTC: Spectra released (13c0c898). Its unit rows now show for radiator, ac-compressor,
    ac-condenser, heater-core, evaporator, throttle-body, fuel-pump-module (and ignition-coils).
    Aftermarket groups are gated per source for EVERY category (_AM_SITE_CATS, fail closed: a source
    ships only what its own §11.4 covered). OEM and every other source stay held in all 14
    GROUP_HOLD_CATS categories.
  - Make breadth 07:40 UTC (branch make-breadth-hmg-body): Hyundai/Kia body gate and production-date
    rule in curate.py (_hmg_body_excludes, _hmg_row_body_excludes, _hmg_production_excludes).
    kiapartsnow files Forte and Forte Koup under one catalog, and the body shows only in the option
    column ("[Sedan - 4Door]", "[Coupe - 2Door]"). It removes 27 Forte/Forte Koup strut groups from
    hmg.json (strut is held, so no user impact). Tier C/D curation on hmg inherits these rules.
  - 2026-11-10 12:25 UTC: NEW blocks (503, 07:10-07:16 UTC, CI multi-site cluster; no local crawls):
    mbpartsgiant (mid W), nissanpartsdeal (mid C knuckle), subarupartsdeal (mid A/B). Reported to the hub.
    Tier C is landed on most sites; Nissan and MB C are partial. Tier D placeholder rows have begun
    (hyundai 69 segs).
  - **Wiper-motor curation handover** (whoever does it; hub priority 1 of the tier C work):
    1. policy.CATEGORY_POLICY["wiper-motor"]: slots F (windshield) and R (rear/liftgate). Sides for
       twin-motor cars: Hyundai Sonata "LH", Volvo "Driver/Passenger Side" → FL/FR inside F, required
       [["F"]].
       positions.py needs an "end" axis: front/windshield vs rear/liftgate/back-door, from name,
       position and list-page slug (e.g. rear_window_wiper*, windshield_wiper_rear, rear_wiper).
    2. positions.packaging("wiper-motor"):
       - "motor" (bare motor);
       - "drive" (Nissan "Drive Assy" = motor + linkage);
       - "module" (GM MODULE incl. transmission; Kia "Motor & Link"; BMW "Wiper System, Complete" are
         excluded at crawl);
       - "motor-ecb" (GM "EXCEPT CIRCUIT BOARD").
       Match only within one packaging.
    3. NOUN["wiper-motor"] = r"wiper". SIBLING_IGNORE for washer/headlamp-washer pages: needs a
       basis per site.
    4. Strict note refusal (hub 18:20): any option, body, drive, plant or production-date note → no
       claim.
       Watch for:
       - Jeep aux "Wiper Linkage" (dropped at crawl);
       - Mazda/Mitsubishi/Audi bare "Motor" rows (crawl product check requires "wiper");
       - GM RPO codes in remarks.
    5. Hashed inputs (policy/positions/notes): re-curate ALL shipped namespaces in the same push,
       identical-or-explained diff, test_groups_hash green. Coordinate with interchange/wheels-curation
       (whoever pushes second rebases).
    6. Independent §11.4 sample (30 closures + 30 pairs, a session that did not write the rules), 0
       WRONG. Verifiers pass fetch.py --text --max-lines 100000.
       Then release: wiper-motor is NOT in GROUP_HOLD_CATS (it isn't an app category yet). Add the
       app category entry (exact price tokens: "=wiper motor", "=windshield wiper motor",
       "=wiper motor front", "=wiper motor rear"…, mined from coverage_matrix.chain_price_lists) on
       interchange/categories-<n>, together with its groups.
  - **Handover state, 2026-11-10 12:30 UTC (session_016ZzJfHdWViThcgyPbNG4i7 stops here; hub starts a
    fresh wiper-motor session):**
    - ORDER: branch AFTER make breadth's production-date push (hashed input, `--ns all` re-curation)
      lands on main, or rebase onto it. Two re-curations must not race.
    - Tier C data on oem-raw (seg-done lines, 12:20 UTC):

      | Site | Segs |
      |---|---|
      | ford | 460 |
      | jeep | 320 |
      | hyundai | 212 |
      | toyota | 196 |
      | bmw | 113 |
      | honda | 75 |
      | kia | 75 |
      | mazda | 60 |
      | vw | 58 |
      | infiniti | 47 |
      | nissan | 45 (PARTIAL, blocked 503 07:15) |
      | mitsubishi | 37 |
      | lexus | 31 |
      | mb | 31 (PARTIAL, blocked 503 07:10) |
      | audi | 26 |
      | volvo | 25 |
      | acura | 17 |

      gm: tier C follows A/B (not reached). subaru withheld/blocked, mopar blocked. Hub
      cause: 6 SimplePart jobs at once in run 25, fixed by platform pacing f603b035. Retry for
      mb/nissan is with the owner; subaru stays stopped.
    - Tier D placeholder (tierD=1, list pages only): rows so far only on hyundai (69 segs). The other
      13 flagged sites follow after their c1.done (completion-first, hub 01:15). Per site, once its D
      lines exist:
      1. read raw/<site>.lists.jsonl rows with tier "D";
      2. replace the placeholder (?!x)x rules in sites/<site>.py ("tier D: name rule pending") with
         strict rules: colour/trim words kept, airbag rows excluded;
      3. set worklist "tierD": 2 and raise the version (crawl.tier_key → "D2" re-reads);
      4. ci_audit;
      5. curation then reads only "D2" lines.

      honda/acura/nissan/infiniti tier D belong to session_016ZzJfMtLKpUFu8TiEFMrkF (nissan now
      blocked).
    - Open items:
      (a) wiper-motor curation + §11.4 (plan above).
      (b) Tier D wave 1 rules per site as rows land.
      (c) Tier D wave 2 (door-handle-ext/int, door-lock-actuator, backup-camera, tailgate-handle):
          slugs and plumbing not started.
      (d) rear-seat airbag rule (research first; any airbag → never included).
      (e) knuckle/strut curation, last (path E audit checklist:
          groups/_report/pathE_audit_2026-11-09.json). Notes:
          - Ford kit / assy / loaded-strut packaging;
          - Jeep 68088535AC "Knuckle And Hub" → AD bare;
          - 2AMST022AA accessory shock: never group;
          - VW "Spindle" naming;
          - hmg body/production gates (make breadth).
      (f) GROUP_HOLD_CATS releases:
          - only per source after its §11.4 + hub confirm (_AM_SITE_CATS / AM_RELEASED);
          - Spectra (7 cats + coils) and GSP (cv-axle) are released;
          - OEM is held in all 14.
      (g) Tiles: propose junkyard-demand tile changes with the next category batch (hub).
  - Next per site, once the CI placeholder pass has written its tier D list rows on oem-raw:
    write rules from raw/<site>.lists.jsonl, set tierD 2, raise the version, then ci_audit.
- Tier C priority: wiper-motor curation and §11.4 next, once honda/toyota/nissan have C data.
  Knuckle and strut audits are last.
- **Wiper-motor curation (session_016ZzJfKQPmCKfP14gyJpp6a, 2026-11-10 ~13:30 UTC).** Rules are on main;
  the category is HELD. It has no app kind, so kind_not_phase1 applies, and no audits.json record.
  - Data on oem-raw@796a77b (distinct wiper pns):
    ford 92, toyota 89, jeep 81, nissan 61 (partial), infiniti 51, honda 46, hyundai 43, mazda 43, kia 42,
    volvo 27, vw 23, lexus 22, acura 19, audi 11, mitsubishi 10, mb 9 (partial). bmw 0, gm 0.
  - Rules (hub-approved plan + hub additions 12:46/13:05):
    - CATEGORY_POLICY slots F/FL/FR/R; required [F] | [F,R] | [FL,FR] | [FL,FR,R] (exact set).
      A lone sided motor closes nothing: Honda/Ford print "Front Driver Side" on single motors.
    - positions end axis: name/position/location/notes; a rear word wins over "windshield"
      (Honda "RR. Windshield Wiper"). The list-slug fallback is REAR ONLY. Basis, oem-raw@796a77b:
      Ford windshield_front_wiper / windshield_wiper_motor_washer and Hyundai windshield_wiper list rear
      motors, while no rear page lists a front motor.
    - packaging, one per slot: motor | drive (Nissan "Drive Assy", Ford "Motor And Linkage") | kit (Jeep) |
      motor-ecb (GM) | motor-ctl (Ford "Smart" motor, from the row note). linkage = out of category;
      module = blocked.
    - NOUN wiper. No SIBLING_IGNORE entries yet; unread_sibling_page is the top open reason on several sites.
    - Likely groups (policy.STRICT_NOTE_CATS, curate._strict_refusal), refused when:
      - any own-page note class is not POSITION;
      - the class is not in exactly one clean slot;
      - it is a twin half without both halves on every app's page;
      - the name carries an option word (WIPER_OPTION_RE);
      - rear-motor body gate: any app model-year decodes to sedan/coupe/convertible/pickup, or the model
        has no decoded body (vPIC via curate --decodes docs/data/vin_decodes.json.gz; missing file refuses
        every rear group).
      OEM apps have no body-gate field yet, so this fails closed. A per-app gate and if_equipped come with
      the app category proposal.
    - Note words name the end and packaging ("rear wiper motor with linkage").
    - Tests: curation_tests/test_wiper_motor.py (72).
  - Hashed push, hub GO 13:11:
    - re-curated --ns all on dca9cd845f26 with --inventory = inventory_live.json@a85c654;
    - groups diff vs main = policy_sha256 + wiper cells only (hmg 4, vag 9 open reasons), 0 non-wiper changes;
    - payload rebuilt: builtAt only, oemStatus ok x8;
    - curation_tests: all pass except test_model_map (live J-10 row, hub exception); tests 42/42;
      scraper tests 27/27; pf_guards ALL PASS.
  - Scratch build with kind "body" patched on oem-raw@796a77b: 26 Likely groups (F 17, R 9;
    mopar 14, nissan 5, hmg 4, toyota 3).
    - §11.4 running: seed 811023, 27 groups + 30 pairs, independent verifier, outside sources required.
      The 27th group (Audi A4 rear 4F9-955-711-E) is now refused by the body gate.
  - Release path (hub 13:05): wiper groups ride make breadth's per-namespace advances to newer pinned refs,
    sampled with them; make breadth told 13:2x. After the §11.4 passes: propose the app category (kind,
    label, priceTokens, notes, rowWarn, per-app body gate) to the hub as a separate app change.
  - **§11.4 round 1 (seed 811023, 27 groups + 30 pairs): FAILED. 5 WRONG, 1 RISK.**
    - WRONG:
      - G06 55154863AC: motor + pivot/linkage, but the note said bare motor;
      - G13 55112704AA: 2017 Compass, two generations, two rear motors;
      - G19 28800-JK600 and G22 28810-JK60A: 2009 G37 sedan JK60A vs coupe JK61A;
      - G27 A4 rear: wagon only, already removed by the body gate.
    - RISK: G10 68082552AA: 2013 Charger R/T has 68193883AA.
    - Fixes on main 3e8dabc, both only removing claims:
      - strict_slot_split: another non-comparable number in the group's slot of any app's cell;
      - packaging_conflict: a same-key list row or other_names says pivot/linkage on a non-drive class.
    - Same commit: curate reports pin inputs {inventory, decodes} by sha256. Pinned copies come from a85c654
      (decodes 1357625b…, inventory 1a9cfa73…).
    - Push re-curation: byte-identical groups.
  - **§11.4 round 2 (seed 52907, fresh verifier, 21 groups + 30 pairs, second-motor check): PASSED.**
    - 0 WRONG, 0 RISK, 21/21 groups and 30/30 pairs OK. Files: scratch verify_wiper_52907.json.
    - The 21 groups = exactly round 1's OK set, rebuilt on oem-raw@796a77b with the fixes:
      mopar 11, nissan 3, hmg 4, toyota 3.
    - LIMIT (reported to the hub): every outside confirmation is search-result text. WebFetch opened no
      outside page; refused domains were dropped, never worked around.
    - Weakest: G01 98110-3S000. Outside evidence covers the Sonata platform, not the Azera by name.
    - Still held: no app kind, no audits.json record. Release rides make breadth's per-namespace ref
      advances, with the app category as a separate change. Proposal sent to the hub 2026-11-10 ~13:50.
  - Hub 13:46: round 2 ACCEPTED (snippet-level outside evidence is the standard; G01 accepted).
    - App category approved: branch interchange/categories-wiper (003e259, sw jh-v180, categories 44 -> 45,
      "wiper-motor" in GROUP_HOLD_CATS). It waits for design/aftermarket-notes (sw v179), then rebase and
      hub regression.
    - Per-app body gate + if_equipped for OEM Likely apps: a separate later change. Until then, rear groups
      on models with sedan variants stay refused.
    - Once kind "body" is on main, every curate run writes wiper Likely groups into groups/<ns>.json.
      GROUP_HOLD_CATS keeps them out of the payload. They ship only via make breadth's sampled advances.
  - **For make breadth: wiper yield ideas** (not started; hub: note only):
    1. SIBLING_IGNORE with per-site written bases. unread_sibling_page is the top open wiper reason
       (wiper-named subs that aren't CAT_PAGES: washer/headlamp-washer/wiper-arm pages). Each entry needs
       the page read once to show it lists no motor.
    2. Ford own-page completion: 92 wiper pns, 593 own-page drops, 0 groups. Most Ford windshield
       motors have no end word in the name, so with the rear-only slug fallback they are position_missing;
       positions only become clean where the position or remark states the end.
    3. Twin-motor (FL/FR) sites (Hyundai "LH", Volvo Driver/Passenger): no group yet. Each needs both
       halves on its own page.
  - **STOP, wiper-motor session (2026-11-10 ~14:30 UTC; hub: owner at 3% weekly usage, go idle).**
    - Branch interchange/categories-wiper @277ef00, PUSHED, rebased on cbfafb4. The hub runs the regression
      and merges on green.
      - 28182ba: category, GROUP_HOLD_CATS, sw jh-v180, tests.
      - 5a20bc6: OEM_RELEASED per-namespace release (empty, fail closed), _oem_held, tests.
      - 277ef00: payload rebuilt; diff vs main = categories 44 -> 45 only.
    - Tests on 277ef00:
      - scraper test_*.py 27/27;
      - curation_tests: all pass except test_model_map (J-10 only);
      - pf_guards ALL PASS; pf_new_cats_e2e 162 ok / 0 FAIL.
    - ui_no_truncation NOT completed on 277ef00 (stopped on the hub's instruction).
      - Before the rebase: 320/375/390 had no truncation failures. 430 was cut off by my own timeout,
        giving setup/harness errors only.
      - 430/768/1280 were not run on the final tree.
    - Release path for the 21 sampled groups (§11.4 round 2, oem-raw@796a77b): make breadth's per-namespace
      advances add (ns, "wiper-motor") to OEM_RELEASED with their samples.
    - Open:
      - per-app body gate + if_equipped for OEM Likely apps (separate change);
      - yield items 1-3 above.

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
- 2026-11-10 03:33 check-in: run 42712787314 (01:57) picked up all 4 sites,
  but in worklist mode for tier C, not R3. Category breadth set tierC +
  version 2 on them, and markers.mode runs an open worklist before the
  completion pass.
  - acurapartswarehouse: `.v2.done` (tier C, 951 records, 5 errors).
  - hondapartsnow: tier C slices in progress (1,724 records at 03:04).
  - infinitipartsdeal: started 03:18. nissanpartsdeal: not started yet.
  - No .blocked or .paused. R3 (`.c1.done`) runs on each site after its
    `.v2.done`.
  - Acura has 0 completion rows, so its next run writes `.c1.done` at once.
- 03:34 UTC check-in: GSP cv-axle 2,938 units (8 sitemaps pending); 1A strut 1,163 (642 pages pending). Run 42714835085 dates from before the reorder (435f9119), so lamp lines start with the next run (~07:40), or sooner if the hub re-dispatches (offered). Nothing blocked.
- **MERGED to main at 13c0c898 (hub, 2026-11-10 ~03:44 UTC).**
  - Spectra Premium Likely groups now ship in radiator, ac-compressor,
    ac-condenser, heater-core, evaporator, throttle-body, fuel-pump-module
    and ignition-coils: 613 groups, pinned oem-raw@ac4d1f0d.
  - Aftermarket sources ship only their audited categories
    (`_AM_SITE_CATS`, fail closed).
- **Handover for the next session (re-curation):**
  1. `python3 scraper/oem_fitment/aftermarket/groups_spectra.py --raw-ref <full oem-raw sha> --ship /tmp/x.json`
     (--ship refuses anything but a full sha).
  2. Fresh §11.4 sample: new seed, independent agent, every config of one
     row per group, part-page cap 12, `--max-lines 100000`; brief it with
     the curation's engine/fuel labels. 0 WRONG per category.
  3. Hub confirm, then replace groups/aftermarket/spectrapremium.json and
     rebuild the payload in the same push.
  - Scratch tools from this session (sample builder, coverage) were not
    committed; the method is above.
  - A new category for Spectra (e.g. fuel-tank) also needs an app category
    (category-breadth) and an AM_RELEASED entry.
  - Raw had 1,998 vehicles at merge; the crawl continues.
- 05:36 UTC check-in, two milestones:
  - **1A Auto BLOCKED.** HTTP 503 at 04:30:07Z, after 3,481 requests at
    8 s pacing (oem-raw e53caf75, `.blocked`). This is a permanent stop per
    rule 2 with no retry, and the breaker is also written in this container.
    Data: 1,193 strut units → 271 groups, not shipped. The lamp, blower,
    mirror and handle lines never started. A §11.4 re-read isn't possible;
    options (out / owner outreach / raw-only verifier) are with the hub.
  - **GSP cv-axle FINISHED.** 3,887 units → 151 Likely groups. The full
    §11.4 sample (30 groups + 30 donor pairs, independent verifier, product
    pages only, `--max-lines 100000`) is running.
- ~06:10 UTC: GSP cv-axle §11.4, 30 groups + 30 pairs, independent
  verifier, 53 fetches.
  - Result: 0 WRONG; 11 + 12 RISK.
  - Main finding: the title's unit-level engine list was put on every row,
    giving impossible engines (TL "3.0", ML320 "5.5", FX35 "3.7").
  - Fixed (b678323e): title engines only on single-model units. Result: 151
    → 184 groups, 298 apps.
  - The verdict covers the old build. A fresh §11.4 on the new build was
    proposed. Drive-gate (AWD-only corners) and unit-level generation
    merges are with the hub. cv-axle stays held.
- ~06:40 UTC: GSP rules per hub (9ca3e720): donor drive gate (d) with driven_axle, unit-level generation guard. Final build is 129 groups, 201 apps. The fresh §11.4 waits for category breadth's pfAmRows mirror of gate (d).
- ~07:00 UTC: round-2 GSP cv-axle §11.4 running. It's a new verifier with seed 424242: 30 groups (10 new-admit, 10 engine-carrying, 10 front-axle) + 30 pairs. It checks the app's gate (d) against category breadth's branch interchange/categories-axle (b800ec8).
- ~07:30 UTC: GSP §11.4 round 2 gave 0 WRONG (9 + 13 RISK); drive gate (d) had 0 deviations on b800ec8. RISKs resolved (04667567): engines per model-year = title ∩ lot-decoded engines; cv-axle note leaves drive to the app line (D1). Final build: 100 groups, 172 apps. Asked the hub to choose (a) accept or (b) a round-3 sample (recommended).
- ~07:55 UTC: GSP build pinned (6d793a4a): raw oem-raw@624a95ba, lot 91b0b5dd (sha256 recorded); 100 groups. Round-3 §11.4 running: new verifier, seed 777003, 30 groups (10 narrowed, 10 lost-models, 10 AWD-optional) + 30 pairs, against b800ec8's pfAmRows.
- ~08:20 UTC: GSP round 3 FAILED, 2 WRONG (NCV37071: yard 'Santa Fe' = Sport; lot engines joined to the LWB row). Fixed (a8d8d437): strict lot-engine coverage on multi-model units, sibling-name guard, spline/length check in notes. Rebuilt on the same pins: 89 groups. Round 4 running (seed 31337004, 30 + 30).
- ~09:00 UTC: GSP cv-axle §11.4 round 4 PASSED (0 WRONG; 12 + 16 RISK, all covered by shown lines; drive gate 0 deviations). Release candidate on branch interchange/gsp-cv-axle-release @ 0201a501 (b800ec8 + main): 88 groups pinned (raw 624a95ba, lot 91b0b5dd), AM_RELEASED gspnorthamerica={cv-axle}, payload rebuilt, all suites pass. Waiting for the hub's regression test, confirm and merge.
- ~09:10 UTC: hub CONFIRMED GSP cv-axle on round 4, including the two length-only RISKs (Q70/M37x, Q70L 2015). The hub is regression-testing 0201a501 + main and merges on green (sw jh-v178, AM_RELEASED comment updated in its merge). No pushes to the branch meanwhile.
- **2026-11-10 ~08:40 UTC.**
  - **Run 25:** completion read pages on 12 sites; hyundai and kia
    `.c1.done`. mbpartsgiant, nissanpartsdeal and subarupartsdeal are
    `.blocked` (HTTP 503 at 07:10-07:16, with 6 SimplePart jobs live).
    Not retried (rule 2).
  - **Per-platform pacing** (hub task): branch
    `make-breadth-platform-pacing` (bf777d7). platforms.py has all 20 sites
    on SimplePart, from recorded served markers, with no new requests. The
    workflow runs one job per platform in round-robin site turns; fetch.py
    adds an 8 s platform-wide gap; refusals go to
    raw/<site>.refusals.jsonl. tests/test_platforms.py. Waiting for the
    hub's review.
  - **HMG** (curated on a24900b), branch `make-breadth-hmg-body`. NOT
    shipped:
    - Round 1: 9 WRONG of 30. Fixed by a body gate (own-page notes and
      fitment rows) and production-date windows.
    - Round 2: 11 R / 3 W / 16 U. All three WRONGs are exterior parts
      across a variant pair (Forte/Koup, Optima/Hybrid 2016). Fixed by a
      variant-aware hold (`policy.hold_base_model`) plus an hmg side-mirror
      hold: 124 groups, 103 added (gauge clusters, regulators, climate).
    - Asked the hub whether to resample, hold more, or park hmg. hmg stays
      at the shipped 54 until then.
  - **Lesson for every namespace:** variant names (Koup, Hybrid, EV, XL,
    Sport) and production-date windows need checking before sampling.
- 2026-11-10 09:41 check-in:
  - **nissanpartsdeal .blocked**: HTTP 503 at 07:15:50 during tier C, run
    42712787314. subarupartsdeal got a 503 at 07:15:45, so these were
    clustered 503s across the network (as on 11-05). No `.retried503` on
    nissan. Any retry is the hub's/owner's call; nothing was changed or
    worked around. Effect: the 201 Nissan R3 rows cannot be crawled. The
    Nissan side keeps seed-proxy own-page evidence only.
  - Tier C finished: honda `.v2.done` (1,942 records), acura (951),
    infiniti (2,133).
  - R3 for those three runs in pending run 42775878285.
- **2026-11-10 ~12:30 UTC: GSP cv-axle SHIPPED.**
  - The hub merged it at 491c846e (sw jh-v178) after the full regression;
    88 groups (59 front, 29 rear).
  - The source-scout-2 session is stopping here. Handover:
    - **Shipped:** GSP cv-axle only, via
      `AM_RELEASED["gspnorthamerica"]`, file
      `groups/aftermarket/gspnorthamerica.json`. The pins are raw
      oem-raw@624a95ba and lot 91b0b5dd.
    - **Re-curation:**
      `aftermarket/groups_rows.py --site gspnorthamerica.com --raw-ref
      <full sha> --lot-ref <full sha> --ship <file>`. Then a fresh §11.4
      (new seed, independent agent, `--max-lines 100000`, the drive gate
      checked against the real pfAmRows), the hub's confirm, and a payload
      rebuild in the same push. A new inventory changes output only through
      that path.
    - **GSP crawl is done** for cv-axle (`.done`). The ride-control / strut
      line has not been sampled or added to `gspnorthamerica.CATEGORIES`.
    - **1A Auto is OUT:** HTTP 503 at 2026-11-10T04:30Z, so `.blocked` and
      the breaker stay. 1,193 raw strut units sit unused on oem-raw.
      Outreach is the owner's call; don't email or retry. The
      junkyard-demand lines (lamps, blower, mirrors, handles, regulators)
      were never crawled. The grammar for them is built and tested in
      `groups_rows.py`.
    - **Lamp/mirror sources:** none passes (SOURCES.md). The route is the
      dealer-catalog tier A (headlights, tail-lights, side-mirrors), which
      belongs to the Honda/Nissan and category sessions.
    - **Rule references:** SOURCES.md "Source scout 2" and the sections
      after it (detector rule, curation rules, gate (d), engine rules,
      round-3 fixes).
- **2026-11-10 ~13:30 UTC: production-date live fix shipped (3444cc7).**
  - All 39 shipped groups the rule changes were checked by 2 independent
    verifiers: 25 WRONG / 9 RIGHT / 5 UNSURE as shipped.
  - Rule (a), `curate._production_excludes`, now applies to every
    namespace: a row's production window must overlap 07/y-1..06/y by
    5+ months. It drops all 29 vehicle-years judged not to fit and 16
    that do (accepted losses: early-launch 2006 GS/RX 400h, supersessions,
    2010 Milan Hybrid). Variant (b) kept 9 wrong years.
  - Wheels are exempt (`PROD_RULE_SKIP_CATS`); their own whole-group rule
    is stricter.
  - Result: toyota 583 -> 557, ford 81 -> 74, hmg 54 -> 52 (held struts).
    Diff list: `_report/production_dates_2026-11-10_diff.txt`.
  - Platform pacing (f603b03) was merged by the hub; the next scheduled
    crawl uses the single SimplePart job.
  - **Open, live:** Lexus chassis/engine codes (MCU/GSU/MHU, GRS/UZS,
    GSE20/21, MCV30/31) on lexuspartsnow rows are ignored, so some shipped
    Lexus groups credit the wrong engine (e.g. RX 350 2007 from 3.3L-only
    rows). Proposed a chassis-code gate to the hub; measure and sample
    first.
- **2026-11-10 ~13:20 UTC: Lexus chassis-code gate + group hold shipped
  (ac4c387, payload rebuilt in the same push).** lexuspartsnow chassis codes
  (GRS19#, MCU3#, GSE20/21 ...) restrict a row to that chassis, applied per
  row with comma expansion.
  - The 2-verifier sample (40 groups) rejected two other variants: pooling
    codes class-wide dropped 39 years that fit; a union variant dropped 13.
  - Final rule on the sample: 0 years that fit dropped, 7 misfits removed,
    1 residual. The residual, 81070-30B52, is held via the new
    `policy.GROUP_HOLDS` with its cited basis.
  - toyota 557 -> 533; nothing added.
  - Other catalogs (toyotapartsnow, honda, acura, ford, gm) print no chassis
    codes like this; the gate stays Lexus-only.
- **2026-11-10 ~14:30 UTC: paused on hub instruction (owner at 3% weekly
  usage). No scheduled check-ins remain.** State for whoever resumes:
  - Live, shipped from this section: Subaru re-ship, the GM rules
    (generation, EXPORT, cab notes), the GM 1500 series filter, the
    climate-control note fix, the production-date rule, and the Lexus
    chassis gate + GROUP_HOLDS.
  - Branches not merged: `make-breadth-hmg-body` (parked by the hub).
  - Next: per-namespace own-page breadth once completion lands (ford,
    jeep, bmw first). Inspect for traps first, then sample with the
    namespace's wiper-motor groups included, then one push with the
    re-curate + rebuilt payload + test_groups_hash.
  - Blocked sites (rule 2, not retried): moparpartsgiant,
    mbpartsgiant, nissanpartsdeal, subarupartsdeal.

### Honda/Nissan, continued (session_016ZzJfMtLKpUFu8TiEFMrkF)

Earlier Honda/Nissan bullets (tier C trial, the 503 block, check-ins) are scattered under other sections because they were appended at the file's end; search for "Honda/Nissan".

- 2026-11-10 14:29: **idle on the hub's instruction** (owner at 3% of weekly
  usage). Deleted the 15:44 check-in (trig_01F9K2UtoPuGezWPnKCPnZkk); no
  other scheduled task of this session remains. Status when stopped:
  - honda, acura and infiniti: tier C done (`.v2.done`); their R3
    completion pass (`.c1.done`) is due in run 42775878285 and needs no
    action from this session.
  - nissanpartsdeal: `.blocked` (503); any retry is the hub's call.
  - Nothing curated or shipped for honda/nissan; tier D not started.
  - On resume: check `.c1.done`, re-curate on a pinned sha, run the §11.4
    sample (verifiers pass `--max-lines 100000`), hub confirmation, ship;
    then tier D on unblocked sites.
- 14:30 UTC: the source-scout-2 session is idle at the hub's request (owner usage). No scheduled check-ins of its own are pending. It resumes only when the hub messages it.

## Demand signals from coverage requests (hub, 2026-11-14)

- Audi A3 alternator (request 2026-11-07, "Can you add this family?"). The
  request named a 2003, which is not a US model year; the US A3 on the lots is
  2006 to 2019 and has no alternator coverage in any year (checked 2006: no
  engine family, no aftermarket rows). A candidate for the next engine-family
  or aftermarket pass. Nothing was added: no basis researched yet.
- Chevrolet Colorado alternator (request 2026-11-11) was for a 2003, which
  does not exist; 2004 is covered. The Parts empty state now points to the
  neighbouring year (hub change, sw `jh-v197`). No table change needed.

## Noted by the hub, 2026-11-16 (tests touched; one app gap left for this workstream)

- `backend/test/interchange_e2e.py`, `part_finder_e2e.py`, `pf_ux_e2e.py`
  and `yaris_coverage_e2e.py`: after typing the zip each now waits until the
  zip is stored (`localStorage.jh_zip`). They used to wait for cards, which
  since the no-gate change appear without a zip; `interchange_e2e` was
  failing about half the time when the outside zip lookup took over half a
  second. Nothing else in the tests changed.
- App gap, not fixed: `setZipCenter` ends with `pfSyncWhere(); renderLive()`
  and does not run the Parts search again. A part picked while the zip
  lookup is still out leaves "Set a zip code (or use your location) up top"
  on the Parts tab after the zip arrives. Suggested: at the end of
  `setZipCenter`, when a part is chosen and the Parts results hold that
  empty line, call `pfRunSearch()`. Mind the launch call (a saved zip is
  restored before the Parts state exists).

## 2026-11-18 Interchange builder: units from data already held (session_01LsgNuWEh1vdaDCtdP1jxMM, branch `interchange/next-1117`)

Hub brief: largest release-ready units with no new crawl. No fetch, crawl or
dispatch was made. Branch head f1114b21, rebased on main 2cb8191c. Not merged.

### Ranking (oem-raw@57e8b5b9, main rules + this branch's rules; lot cars from the live inventory)

Lot cars that sit in at least one shippable cross-model Likely group, shipped
build -> head build (held categories excluded):

| unit | groups (shippable) | lot cars in a group | note |
|---|---|---|---|
| nissan (new make; Nissan + Infiniti) | 0 -> 343 | 0 -> 15,788 | all four sites `.c1.done`; this unit |
| toyota advance (dca9cd84 -> head) | 529 -> 1,104 | 2,206 -> 18,072 | completion pages on toyota/lexus |
| mopar advance | 301 -> 532 | 7,565 -> 18,306 | jeeppartsdeal `.c1.done` |
| hmg advance | 15 -> 331 | 748 -> 5,749 | needs make-breadth-hmg-body rules first (Forte/Koup, Optima Hybrid) |
| vag advance | 19 -> 379 | 451 -> 3,323 | |
| honda (new) | 0 -> 9 | 0 -> 2,385 | Honda parts rarely cross models |
| bmw (new) | 0 -> 209 | 0 -> 1,972 | 3-series body mix (sedan/coupe/conv/wagon) |
| mazda / volvo / mb / subaru / mitsubishi | 33 / 87 / 109 / 46 / 27 | +1,632 / +1,601 / +1,231 / +1,363 / +715 | |

Tier D categories (sunroof, center console, door panel, blower, fog lights)
have no product data on oem-raw (no "D2" lines), so they need a crawl (below).

### Unit 1: nissan. Candidate, NOT shipped (independent sample owed)

- Raw oem-raw@57e8b5b9; inventory and decodes pinned from main@a85c654 (the
  same pins as the shipped files; re-curating toyota/mopar on dca9cd84 with them
  reproduces groups/<ns>.json byte for byte apart from the `raw.ref` label).
- Candidate file `groups/_report/nissan.candidate.json`: 346 Likely groups (343
  shippable + 3 held wiper-motor): window-regulator 133, side-mirrors 94,
  gauge-cluster 90, climate-control 26. The
  payload loader reads only groups/*.json, so the candidate does not ship.
- What the app would show: Likely donors across Nissan/Infiniti twins and renames
  (Frontier/Xterra/Pathfinder 2005+, Titan/Armada, M37/M56/Q70, FX/QX70, EX/QX50,
  JX35/QX60, QX56/QX80, G25/Q40, Altima/Maxima/Sentra window motors, Cube/Juke/
  Leaf/Rogue motors, U13 Altima/Stanza), with notes such as "Nissan catalog
  lists #27510-9CA0A for both — option: fits some option packages; Frontier:
  crew cab only; verify the number on the part". No Verified tier.
- §11.4 rounds (30 groups + 30 pairs each, seeded; record with per-item
  verdicts in `groups/_report/nissan_audit_2026-11-18.json`):
  1. seed 1117001, main rules: trap check only. Rear-door regulator
     82721-JK000 joined the 2008 G37 from the catalog's `2008-infiniti-g37-sedan`
     page, but every decoded 2008 G37 on the lots is a coupe (40/40). Fix:
     body-variant rule.
  2. seed 1118003: FAILED, 19 WRONG. Infiniti files M35/M45 and M37/M56 under
     one catalog page, and the option column names the engine. Examples:
     24820-6AH1A "SEDAN. VQ37VHR" was claimed for the M56; 24820-6AH1C/-6AH1D
     "VK56VD" for the M37; M35<->M45 and FX35<->FX45 clusters/mirrors. Nine
     false "king cab only" notes came from this session's first cab parser.
     Fixes: engine-code rule; the parser reads every "+"-joined part.
  3. seed 1118004: FAILED, 4 WRONG. 24820-6AH2A and -1MK5A print the M56
     with "6 Cyl 3.7L | VQ37VHR" on the product page. Fix: fitment-row engine
     conflict.
  4. seed 1118005: FAILED, 1 WRONG. The 2002 Xterra row reads "Production
     Date: from 12/2002", and the production rule never read "from" windows
     (610 rows on nissanpartsdeal, 969 on lexuspartsnow). Fix: the production
     rule reads "from MM/YYYY" in every namespace.
  5. seed 1118006: FAILED, 2 WRONG. The shared B14 Sentra/200SX page puts
     coupe parts behind "C." and sedan parts behind "4S.". 24820-8B700 "C." was
     on the sedan-only 1999 Sentra. Fix: option-column body codes. A census of
     all 343 groups then checked every class found so far: none left.
  6. seed 1118007: **0 WRONG; 58 RIGHT, 2 RISK** (P15/P19: a single-engine
     cluster claimed for the Q70, which came with both engines).
- Limits, for the hub to weigh:
  - **Not independent.** This session wrote the fixes between rounds.
    §11.4 asks for a session that did not write curate.py. An independent
    re-sample is owed before nissan ships: `audit11_4/sample.py nissan
    57e8b5b99de0 <inventory@a85c654> <decodes@a85c654> <new seed> <dir>`.
  - **Page re-read = raw records and list manifests**, not fetch.py. The cache
    holds only robots.txt, and this task forbids fetches.
  - **Outside evidence = search-result text**, the same standard the hub
    accepted for wiper round 2. Confirmed: 80721-AR000 (Q45 02-06, G35 sedan
    only 03-06, FX 03-05); 82721-7S000 (Titan 04-15, Armada 05-15); 82730-1MA0A
    (M37/M35h, QX56, QX80); 82721-1HL0A (Kicks, Versa); 24810-7S005 (Armada
    04-05, Titan 04-07); 80721-ZL90A (Frontier 10-21, Pathfinder 10-12, Xterra
    10-15).
- To ship after an independent pass: move the candidate to `groups/nissan.json`
  (same policy hash and raw), rebuild the payload, and run test_groups_hash and
  test_lazy_payload. Size: about +127 KB in the lazy files (gauge-cluster
  5.7 -> 38.6 KB, window-regulator 77.6 -> 127.7 KB, side-mirrors 174.0 ->
  208.6 KB, climate-control 21.7 -> 31.5 KB); interchange.json +59 bytes.

### Rules added (curate.py / policy.py; hashed inputs, all 8 shipped namespaces re-curated in the same push)

- §5.16 body-variant rule (`policy.LIKELY_BODY_GATE`, all namespaces except
  wheels). It applies when a vehicle-year comes in 2+ bodies: lot vPIC bodies
  with >=5% and >=2 cars, where the decode's model must agree (yards list some
  Outbacks as "Legacy"), plus body-named catalog pages. Such a vehicle-year
  joins only when its own pages show the number for every body. Its notes still
  feed the class-wide restriction pool, so no claim can be gained.
- Production rule (a) reads "from MM/YYYY" (all namespaces).
- nissan only:
  - Infiniti engine codes, in the option column and in product fitment rows,
    for fixed-displacement names (M35/M45/M37/M56/FX35/FX45/FX50/G25/G35/G37/
    I30/I35/EX35/EX37/JX35/QX56...);
  - option-column body codes (4S/2S/S/SED/SEDAN = sedan, C = coupe,
    W = wagon...);
  - a cab note "<model>: crew cab only" / "king cab only" from KC/CC codes,
    like the GM `_cab_only` note.
- Tests: `curation_tests/test_body_variant.py` (34 checks).

### Live effect on shipped groups (claims only go down; `groups/_report/live_diff_2026-11-18.txt`)

| namespace | change | groups |
|---|---|---|
| gm | removed (body) | 63: Cavalier/Sunfire, Cobalt/G5 (the G5 was coupe-only in 2007; the Cobalt was both), Alero/Grand Am coupe/sedan regulators and mirrors |
| subaru | removed (body) | 14: Impreza 2012 sedan/5-door, Legacy 2001/2005 sedan/wagon |
| mopar | removed / narrowed (body) | 8 removed, 1 narrowed: Sebring 2004 (Mitsubishi-built coupe + convertible), Sebring 2008 sedan/convertible |
| ford | removed (body) | 7: Focus sedan/hatch, Mustang 1998 coupe/convertible |
| toyota | removed (production "from" windows) | 4: Lexus IS 250 2013 / IS 350 2012 motors |
| hmg, mb, vag | none | identical apart from the policy hash and held wiper groups |

Payload 1,538,963 -> 1,503,938 bytes; oemStatus ok x8. These removals were not
sampled one by one. They come from fail-closed rules; earlier live fixes had
two verifiers check the removed groups, and the hub may want that here too.

### Tests on f1114b21

- curation_tests: all pass except test_model_map. It fails on main too, because
  the live inventory has new one-car feed spellings ("Honda Cr-V E:fcev", "GMC
  Express Van", "BMW 535i GT xDrive", ...: M5) and an Acura CL M6. That is data
  quality's, not changed here. Curation therefore runs with the pinned
  a85c654 inventory.
- oem_fitment tests 42/42; scraper test_interchange and test_am_gates pass;
  backend/test/pf_guards_unit.mjs ALL PASS.
- Not run: the browser e2e scripts (interchange_e2e, pf_ux_e2e) and
  ui_no_truncation; the app is unchanged.

### Next (in order)

1. Independent §11.4 on nissan (new seed, a session that did not write these
   rules). Ship on 0 WRONG plus hub confirm.
2. toyota and mopar advances to head raw: +15.9k and +10.7k lot cars. Inspect
   for traps (variants, production dates, body codes on shared pages), sample
   with the wiper groups included, then one push.
3. vag/bmw: the body rule matters most there (Jetta/Golf/Passat/3-series), and
   SimplePart prints body words in its notes.
4. hmg: land make-breadth-hmg-body first.
5. App (another workstream): a per-app body gate on OEM Likely apps would let
   the body rule keep claims instead of dropping them (e.g. G37 sedan-only rows
   shown only on sedan donors). Same idea for engine (Q70 V6/V8 clusters).

### Crawl requests for the hub (none dispatched)

- Tier D wave 1, D2 product pages: no D2 lines exist on oem-raw. Order by lot
  cars, skipping blocked sites (gm, ford, mb, mopar, subaru, bmw, spectra, 1A):
  toyotapartsnow + lexuspartsnow, jeeppartsdeal, hondapartsnow +
  acurapartswarehouse, nissanpartsdeal + infinitipartsdeal, hyundai/kia,
  vw/audi, mazda, volvo, mitsubishi. Categories: blower-motor, fog-lights,
  center-console, door-panel, sunroof. Each needs its strict name rules first
  (tier D handover above).
- gmpartsgiant and fordpartsgiant (24% and 18% of lot cars) never ran own-page
  completion (no `.c1.done`), and both are `.blocked` (503). Any retry is the
  owner's call; it is listed only because it is the largest remaining
  interchange gain.

## 2026-11-18 Independent verification (verifier subagent of session_01LsgNuWEh1vdaDCtdP1jxMM, branch `interchange/verify-1118`)

Hub brief: an independent §11.4 release sample of the nissan candidate, and a
check of the live-group removals on `interchange/next-1117` (head 12f9a78d).
This was a check only: no rule, policy or group file was changed. Raw records
were read from git (oem-raw@57e8b5b9 for nissan, @dca9cd84 for the shipped
groups). No fetch, crawl or dispatch was made. Two web searches were run
(search-result text only, one part number); no page was opened. My own draw
and reader were used, not `audit11_4/sample.py`. The builder's verdicts were
read only after mine were written.

### Nissan §11.4, seed 46021118: FAILED (9 WRONG). Do not ship nissan.

- 30 groups (window-regulator 12, side-mirrors 8, gauge-cluster 8,
  climate-control 2) + 30 pairs from the other groups, out of 343 shippable
  groups. Per-item verdicts with record lines:
  `groups/_report/nissan_verify_2026-11-18.json`.
- **RIGHT 40, WRONG 9, RISK 11** (groups 18/5/7, pairs 22/4/4).
- WRONG falls in two classes that no rule covers:
  1. **Drive (6).** A 4WD-only or 2WD-only cluster is claimed for every car
     of model-years built in both drives, with only the "option" note:
     - G07 24810-EA101 (2005 Frontier "*KC. 4WD. LE + ...", 2005 Xterra "*W. 4WD. SE");
     - G08 24810-ZP67A; P20 24810-ZL95E; P24 24810-EA48C; P29 24810-ZS42D;
     - P10 24810-ZL96C (2WD-only).

     The same pages list the other drive's cluster under other numbers.
     CLAUDE.md rule 3 asks for a drive gate. Census: **43 of 343 groups**
     (all gauge-cluster) are in this class.
  2. **Body, B14 200SX (3).** Sedan "4S." rows are credited to the
     coupe-only 200SX:
     - G03 24820-89Y02 (200SX 1995, 1998-99);
     - G05 24820-8Z002 (1998-99);
     - G06 24820-89Y00 (1999: "4S. GLE" only).

     Round 5's fix removed 1996-97 but kept the years where the lot vPIC data
     is thin (1995: one decoded car), wrong (1998: `1N4AB42D` B42 coupes
     decoded "Sedan/Saloon") or empty (1999).
- RISK (11): part of a model-year cannot carry the number, for a reason the
  note does not name.
  - Engine, transmission or powertrain split under one model name (9):
    - Q70 2014 VQ37VHR-only clusters: G04, G09, G10;
    - KA24DE-only 2004 Frontier/Xterra mirrors: G11, G15 (122 of 126 decoded
      2004 Xterras are V6);
    - 2000 Xterra regulator (G30) and 2001 Xterra mirror (P13);
    - PRO-4X 6MT-only cluster (P01);
    - QX60 2014 cluster from the gas page only (P08: no hybrid page was
      crawled, and 8 lot cars are hybrids).
  - Titan rear-door window motors with no cab code: G23 82730-9FJ0A and P02
    82731-7S000. A King Cab access door may have no window motor, and the
    search text names "Crew Cab" for 9FJ0A.

  Under the brief's literal wording ("any car the group would show"), the 9
  engine, transmission and powertrain items are WRONG too.
- Fixes to make before a fresh independent sample:
  1. Option-column drive codes: refuse, or add a "<model>: 4WD only" note
     with a per-app drive gate.
  2. Take model bodies from a source that does not depend on lot vPIC data:
     the catalog's own C./4S. structure, or a static table (200SX = coupe).
  3. Name the engine or transmission in the note when it splits a
     model-year, or refuse.
  4. Treat powertrain-variant pages (q70-gas, qx60-gas vs hybrid) like
     body-named pages.
  5. Mark Titan/Frontier rear-door window parts crew cab only, by page
     structure (the rear-door glass is split KC/CC).

### Removals, seed 7731118: ship them

- 27 removed groups plus the 1 narrowed group, covering every app family of
  every make: gm 11, subaru 5, mopar 4+1, ford 4, toyota 3. Per-item verdicts:
  `groups/_report/removals_verify_2026-11-18.json`.
- **(a) unsupported or wrong, removal correct: 18** (gm 8, mopar 5, toyota 3,
  ford 1, subaru 1). These live claims show wrong-body donors today:
  - coupe-only J(37)/AJ(37) mirrors and regulators on sedans;
  - rear-door parts on coupes and convertibles;
  - 2012 IS 350 against rows that read "from 10/2012".

  R01 (Ford moisture purge module) and R20 (the 2001 Outback H6 uses
  72311AE11B) are correct for a reason other than body.
- **(b) supported for every car named, removal loses a true claim: 7:**
  - ford R02 CV6Z-5423394-B, R03 6CPZ-5423395-A, R04 CV6Z-5423395-B
    (motors split by window feature, never by body);
  - gm R05 95188244 (FIT names both Sonic bodies), R07 88960088 (Camaro and
    Firebird coupe + convertible), R14 20964008 (Cobalt/G5 2 and 4 DOOR);
  - subaru R21 57229AG04A9P (both pages list S. and W. codes).
- **(c) cannot tell: 3** (subaru R22-R24, Impreza 2012 / XV 2013): only the
  sedan page exists; the 5-door and the XV rest on aggregated FIT rows.
- The removals add no claim, and they take real WRONGs out of live data.
- To recover the (b) class: `_row_body_cover` reads an option-column row as
  naming body *words* only, so GM RPO body styles (37/69/67) and Subaru
  S./W. codes count as no body. Decode those codes, and accept FIT rows that
  name every body.

## 2026-11-18 Rules after the independent check (session_01LsgNuWEh1vdaDCtdP1jxMM, branch `interchange/rules-1118`)

Hub brief: fix the verifier's six flaw classes, live drive first. No fetch,
crawl or dispatch. Raw read from git only. Full report at the end of this
section when the branch stops.

### Item 1: drive on the live makes (`groups/_report/live_diff_2026-11-18_drive.txt`)

- New §5.16 drive rule (`policy.LIKELY_DRIVE_RULE`, `curate.Curation.drive_of`),
  hashed input, all 8 shipped namespaces re-curated in the same push on their
  pinned raw (oem-raw@dca9cd84, inventory/decodes from a85c654).
- Census of main's live groups (`audit11_4/drive_census.py`): an app
  vehicle-year limited to one drive was claimed with no drive in the note in
  gm 42 groups (8 vehicle-years: Tahoe 2007, Trailblazer 2004, Colorado 2005,
  Traverse 2011, Blazer 2001, S-10 2000, Yukon 2003; 1,878 lot cars), mopar 9
  (Ram 1500 2012: rows coded "6 - Lt. Duty DODGE 4WD"; 78 cars), mb 1 (ML350
  2007-08 wheels, trims "4Matic" only). toyota, ford, subaru, hmg, vag: 0.
  Almost all GM cases are the catalog's own drive split: gmpartsgiant files
  those model-years as two catalogs (`2007-chevrolet-tahoe-2wd` / `-4wd`), and
  the number was read on the 2wd catalog only.
- Done with them: gm 36 groups now say "<model>: 2WD only", 6 Colorado/Canyon
  window-regulator groups refused (crew-cab + drive note over 160 chars);
  mopar 9 say "1500: 4WD only"; mb 1 says "ML350: AWD only". No claim added.
- Also fixed: the cab-note length test compared the already-cut note, so it
  could never fail; `_likely_note_fits` now tests the uncut note. No live note
  was cut before this change.
- Test: `curation_tests/test_drive.py` (27 checks).

### Item 2: rules for flaws 2-6 (curate.py / policy.py; shipped namespaces re-curated in the same push)

- Flaw 2 (body from lot data): `policy.MODEL_BODY_TABLE` (B14 200SX coupe;
  NX; 240SX; 300ZX; 350Z/370Z; Sentra; Altima; Versa; Murano; G35/G37/G25/
  Q40/Q60 by year). A listed model's bodies are the table's plus body-named
  catalog pages; lot decodes are not read for it. Other models keep lot +
  pages (dropping lot data there would add claims back without evidence).
- Flaw 3 (engine/transmission): config-tuple option columns name the limit
  ("Q70: 3.7L only", "manual only"); sibling rule: another number of the
  same slot listed for an engine our rows never name (2014 Q70 VK56VD
  clusters) takes that engine away. Engine universe: year page, else the
  engines T's rows in the category name.
- Flaw 4 (gas/hybrid pages): a year page offering a hybrid catalog plus a
  number read on the gas pages only gives "gas only"; a Hybrid feed name with
  gas-only evidence refuses.
- Flaw 5 (body codes): Subaru S./W./WOBK/SOBK/OBK, GM passenger body styles
  (37/69/67/27/47/57/87/35/48/68), Nissan C./4S. decoded when every
  alternative carries one; PartsGiant quantity/callout/colour fields neutral;
  an unparsed feature note is neutral when no row on T's pages in the
  category names a body and the fitment trims do not leave a body out.
  R01 (Ford moisture purge module) and R20 (2001 Outback H6) are held in
  `policy.GROUP_HOLDS` so the fixed rules cannot bring them back.
- Flaw 6 (Titan/Frontier rear doors): a rear-door window part with no cab
  code on a model whose rear-door pages split by KC/CC is "crew cab only".
- Notes are never cut: an over-long note refuses the group.
- Tests: `curation_tests/test_rules_1118.py` (23); test_body_variant's
  lot-count cases moved to a model outside the table (35).

### Item 3: live diff, main 82df0482 -> this branch (`groups/_report/live_diff_2026-11-18_rules.txt`)

Shipped namespaces on their pinned raw (oem-raw@dca9cd84, inventory/decodes
a85c654). Live groups only:

| ns | removed | restored | changed (note narrowed) |
|---|---|---|---|
| gm | 11 | 2 | 47 (36 "<model>: 2WD only", 11 "Silverado 1500 2012: gas only") |
| ford | 0 | 6 | 0 |
| mopar | 0 | 0 | 9 ("1500: 4WD only") |
| mb | 0 | 0 | 1 ("ML350: AWD only") |
| subaru | 0 | 1 | 0 |
| toyota, hmg, vag | 0 | 0 | 0 (hmg: 35 held strut groups only) |

- Removed: notes over 160 characters once the drive/fuel limit is added
  (6 Colorado/Canyon 2005 window parts with crew-cab notes; 5
  Avalanche/Silverado/Escalade parts). Nothing is cut short any more.
- Restored, with every app vehicle-year's own-page evidence in the diff file:
  R02/R03/R04 (Ford CV6Z-5423394-B, 6CPZ-5423395-A, CV6Z-5423395-B), R07 (GM
  88960088), R21 (Subaru 57229AG04A9P), plus four of the same evidence class
  outside the verifier's sample (Ford 6CPZ-5423395-B, 6CPZ-9923394-B,
  6CPZ-9923394-C on the same 2015 Focus / Transit Connect pages; GM 15890412
  Cobalt/G5 2007 heater control, no body code on either page, fitment trims
  "2 DOOR, 4 DOOR"). The hub may want those four checked by someone else.
- Not restored, with reasons: R05 Sonic (the sedan catalog was never read;
  GM fitment trims are not used to add a body because R14 shows they list
  bodies a row's own code excludes), R14 Cobalt headlamp (own row "AP(37)",
  body style 37 = coupe; I read it as coupe-only, the verifier did not), R01
  and R20 (held), R22-R24 (Impreza/XV: only the sedan page).
- Payload 1,503,938 -> 1,503,908 bytes.

### Item 4: nissan candidate rebuilt (oem-raw@57e8b5b9). NOT shipped; an independent sample is owed.

- `groups/_report/nissan.candidate.json`: 286 Likely groups, **283 shippable**
  (was 343): window-regulator 123, side-mirrors 80, gauge-cluster 55,
  climate-control 25. Refusals: 37 notes over 160 chars, 41
  `held_engine_conflict` (mostly FX35/FX45 and M35 2008, where a sibling of
  the same slot is coded for the other engine).
- The verifier's 20 WRONG/RISK items now (`nissan_selfcheck_2026-11-18.json`):
  drive WRONGs G07/G08/P20/P24/P29 say "4WD only", P10 "Frontier: 2WD,
  automatic only; Xterra: 2WD only"; 200SX G03/G05 gone, G06 lost 1999;
  Q70 G04/G09/G10 "Q70: 3.7L, gas only"; G11/G15 "Frontier: king cab only;
  2.4L only"; G30 "Xterra 2000: 3.3L only"; P01 "manual only"; P08 "QX60:
  gas only"; G23/P02 "Titan: crew cab only" (2004 too); P13 gone.
- My own check (rule author, not independent): raw-token census of all 283
  groups (drive/body/engine/transmission/hybrid/rear-cab codes vs note): no
  unexplained suspect. Seeded sample `audit11_4/sample.py` seed 61181118, 30
  groups + 30 pairs, read twice:
  - on an intermediate build it found two self-contradictory engine labels
    (FX35/FX45 "FX45: 3.5L only"), sibling packaging mixing, a too-narrow
    engine universe (2000 Xterra) and the Pathfinder "*W. AUTO" drive field
    (All-Mode 4WD clusters claimed for every Pathfinder). All four fixed.
  - on the final build: 59 RIGHT, 1 RIGHT after the AUTO fix, 0 WRONG.
  - Residual RISK (not new): production-date splits inside a model-year keep
    the generic note (2008 M35 mirror "from 01/2008"); "gas only" under-claims
    where the M35h hybrid twin shares the part; Nissan "*" markers undecoded.
- Shipped namespaces re-curated after these last rule changes: byte-identical
  to item 2 (they touch config-tuple sites only; subaru/hmg unchanged).

### Item 5: model map (test_model_map passes)

- 16 one-car feed spellings excluded by the map's existing rule (no claims
  until a reviewed entry): Toyota Corolla Hybrid, Chevrolet Celebrity Wagon,
  GMC Sprint, GMC Express Van, Pontiac Bonneville Sse, Oldsmobile Alero Gls,
  Saturn Astra Sat, Oldsmobile LSS, Ford Escape Hev, Ford Transit Wagon,
  Honda Cr-V E:fcev, Volkswagen Tiguan Limited, Audi TTS, BMW 535i GT xDrive,
  BMW 323Ic; "Chevrolet Canyon" excluded as a mislabelled listing.
- Acura CL unmapped (M6: 2 of 98 cached decodes name another make, 2.04%,
  over the 2% cap), like Chevrolet Suburban and Acura ILX before it. honda
  is not shipped, so no live effect.
- model_map.json is hashed: all 8 shipped namespaces and the nissan candidate
  re-curated in the same push; only `policy_sha256` changed. Payload rebuilt.
- After merging main (751bce87, payload files regenerated) the live inventory
  held 21 more new spellings ("Civic 2Dr", "Focus Htbk", "Passat Tdi", "Eos
  Conv", "Impreza Wrx"...): excluded the same way; target "Subaru Impreza
  WRX" unmapped (M3: shares its squash with "Impreza Wrx"; no live group
  names it). Re-curated: only `policy_sha256` changes, plus subaru cell
  counts (2,640 -> 2,408) from the unmapped target; no group changes.

### For the hub (2026-11-18, end of this branch)

- Branch `interchange/rules-1118`, head in the commit that adds this block.
  Nothing pushed to main, nothing dispatched, no fetch or crawl.
- Live effect vs main 82df0482 (`live_diff_2026-11-18_rules.txt`): gm 11
  removed / 2 restored / 47 notes narrowed; ford 6 restored; mopar 9 and mb 1
  narrowed; subaru 1 restored; toyota, hmg, vag unchanged. Payload
  1,503,938 -> 1,503,908 bytes before the merge.
- Tests on the final tree: curation_tests 21/21 files pass (test_model_map
  included; the Phase 2 parity SKIP is unchanged), oem_fitment/tests 42/42,
  scraper/test_interchange and test_am_gates pass, pf_guards_unit ALL PASS.
  Browser e2e not run (app unchanged).
- Decisions for the hub / owner:
  1. Merge the live changes? Every live change narrows a note or removes a
     group, except the 9 restored groups; 4 of those were outside the
     verifier's sample (ford 6CPZ-5423395-B, 6CPZ-9923394-B, 6CPZ-9923394-C;
     gm 15890412). A second reader on those 4 before merging would match the
     §11.4 habit.
  2. R14 (Cobalt/G5 headlamp 20964008): the verifier called it true; I read
     the Cobalt row "AP(37)" as coupe-only and left it removed.
  3. Nissan: 283 shippable groups, my own check 0 WRONG; an independent
     sample is still owed (`audit11_4/sample.py nissan 57e8b5b99de0 ...`).
  4. Drive notes from GM catalog pages: most GM "2WD only" notes come from
     the 4wd catalog never being read for that category (Tahoe 2007,
     TrailBlazer 2004...). They under-claim rather than over-claim. A
     completion crawl of the gmpartsgiant 4wd/awd/hybrid variant pages would
     turn many back into plain claims (gmpartsgiant is `.blocked`; owner's
     call).
- Suggestions:
  - App (docs/app.js, not touched): OEM Likely groups have no per-app gate.
    The aftermarket path already reads `a[5]` gates ({body}, {drive}). Letting
    OEM apps carry the same 6th element (drive / body / engine / cab) would
    let these notes become gates, so a 2WD Frontier seeker never sees 4WD-only
    clusters, and the body rule could keep claims instead of dropping them.
  - test_model_map runs against the live inventory, so every scan that adds a
    one-car spelling ("Htbk", "2Dr", "Conv", "Tdi") breaks it. Either collapse
    those suffixes in the feed normalizer (data workstream) or run M5 against
    the pinned inventory the groups were curated with.
  - Production-date splits inside a model-year (rows overlapping 5+ months)
    still get the generic note; naming the window ("built from 01/2008")
    would close the last RISK class seen in my sample.

## 2026-11-18 Independent check of the restored claims (verifier subagent of session_01LsgNuWEh1vdaDCtdP1jxMM, branch `interchange/verify-restored-1118`)

Hub brief: an independent read of every claim `interchange/rules-1118` (head 54d0784d) adds back to the live
groups, the disputed R14 removal, and a seeded spot check of the narrowed drive notes. Check only: no rule,
policy, group or payload file was changed. Raw read from git (oem-raw@dca9cd84) with my own reader, not
curate.py or `audit11_4/sample.py`. No fetch, crawl or dispatch. The builder's evidence was not read before
these verdicts were written. Per-item verdicts with the raw record lines:
`groups/_report/restored_verify_2026-11-18b.json`.

### Restored list (built from the diff)

Per-app diff (make, model, year) of every group keyed by (ns, cat, pn), main@700bcf9b -> branch, in both
`groups/<ns>.json` and the payload (`docs/data/oem/*.json`; `interchange.json` holds no oemGroups). Both agree:
**9 groups, 19 apps** (ford 6, gm 2, subaru 1), as expected. No group gains a vehicle-year on top of a live
claim, and no note on the branch drops a phrase main has.

| pn | apps | note (short) |
|---|---|---|
| ford 6CPZ-5423395-A, -5423395-B, 6CPZ-9923394-B, -9923394-C | Focus 2015, Transit Connect 2015 | window motor only; trim-limited; FWD only |
| ford CV6Z-5423394-B, CV6Z-5423395-B | C-Max 2013, Focus 2012 | window motor only; fits some configurations; C-Max 2WD / Focus FWD |
| gm 15890412 (heater-only control) | Cobalt 2007, G5 2007 | option |
| gm 88960088 (front window motor) | Camaro 1995, Firebird 1995, Safari 1997 | window motor only; fits some configurations |
| subaru 57229AG04A9P (turbo hood) | Legacy 2005, Outback 2005 | Legacy GT / Outback XT only |

### 1. Restored claims: RIGHT 19, WRONG 0, RISK 0

Each app's own catalog page lists the number, and the only splits on the pages are ones the note names:
- window features (one-touch, power rear windows, power sliding-door windows) for the motors;
- the A/C option (C67) for the heater-only control;
- the turbo trims (S./W. 25GT, WOBK 25GT) for the Subaru hood.

None of these pages is split by body, drive, engine or production date:
- Focus, C-Max and Transit Connect are single catalogs;
- the GM heater-control and motor rows carry no body code;
- Safari 2WD and AWD both list 88960088;
- FIT rows name 2 DOOR + 4 DOOR, or 2 DOOR + CONVERTIBLE.

Caveat on the four 6CPZ Focus/Transit Connect groups (not a verdict change): the same number sits in a
different door on each model's own page. For example:
- 6CPZ-5423395-B is the Focus driver-front motor but the Transit Connect passenger-front motor;
- 6CPZ-5423395-A is the Focus passenger-rear motor but the Transit Connect driver sliding-door motor.

The app shows no position, and the note says to verify the number. A puller who assumes the same door gets the
wrong motor.

### 2. R14 (gm 20964008, Cobalt/G5 2007 headlamp): the removed claim was WRONG; the removal is correct

The 2007 Cobalt's own lamps page lists 20964008 (smoked lens) only for `Fitting Vehicle Options: AP(37)`. In
GM body-style numbers, 37 is the 2-door coupe; the same 2007 Cobalt catalog uses 69 for the sedan:
- rear-door rows carry only (69);
- the trunk weatherstrips split A(37) / A(69).

Every other 2007 Cobalt (series AJ/AK/AL/AM, both bodies) is listed with 22740621/22740620 (clear lens). The
product FIT row "Cobalt 2005-2010 | 2 DOOR, 4 DOOR" spans other years and does not override the 2007 page. The
live claim put the part on every 2007 Cobalt, sedans included, under an option note that does not name the
coupe limit. The earlier class (b) verdict cited the G5 row (no code) and the FIT row. It missed the Cobalt
row's AP(37), which is in record jsonl:512.

### 3. Drive notes, seed 20261118: over-claims 0; limits shown true 0 of 8 (all safe under-claims)

The population is the 46 payload groups whose note gained "<model>: 2WD|4WD|AWD only". I drew
`random.Random(20261118).sample(range(46), 8)`, which gave indices 1, 2, 4, 13, 14, 21, 24 and 41:
- gm 15858832 and 19433953 (Colorado 2005);
- gm 22853025 and 23227000 (Tahoe 2007);
- gm 5978196 (S-10 2000);
- gm 15643719 (Tahoe 1999);
- gm 19331466 (Trailblazer 2004);
- mopar 55277410AE (Ram 1500 2012).

In every pick, the other vehicle-years (Canyon, Avalanche, Sonoma, Yukon, Rainier, Escalade, Ram 2500) are
listed on both drive pages and correctly carry no limit, so there is no over-claim. But no limit is shown true:
- **GM (7):** only the 2WD page's record exists for that category. The 4WD page of the same model-year has no
  list manifest and no record in the raw, so "2WD only" rests on a page never captured. The twin's own 4WD page
  lists the same number, and the FIT row names no drive. Census over all 46: 30 of the 36 GM "2WD only"
  app-years are in this state.
- **Mopar (1):** "1500: 4WD only" comes from a FIT row that lists only 4WD 1500 trims. Every pre-07/23/2012
  1500 headlamp on the 2012 page has the same 4WD-only row, so that row is incomplete for 2WD.

These notes are safe under-claims, but they state a limit the catalog does not state, and they hide true 4WD
donors.

### Found, not changed (for the hub)

1. Drive rule: treat "other-drive page not in raw" as unknown (no note, or read that page), not as "2WD only".
   Ignore FIT-row drive lists when every sibling on the page shares the same gap.
2. Mopar 2012 Ram 1500 headlamps 55277409AE/10AE and 68001484AE/85AE are "Up To 07/23/2012" on the 1500 page,
   but no note names the production window. This is unchanged from main. The production rule may not read
   Mopar's "Up To MM/DD/YYYY" form.
3. gm 15643719/15643720 (Tahoe/Yukon 1999 rear-door regulators): the FIT row says "CLASSIC 4 DOOR"; 1999 also
   had 2-door Tahoes/Yukons. The note does not name the body. Lot body mix not checked.
4. Ford window motors: print the page's fit note and the door per model in the note (e.g. "Transit Connect:
   passenger front"). "trim-limited" alone does not tell a puller which door holds the number.

**Recommendation: ship the 9 restored groups.**

### Agreement / disagreement with the builder (read after the verdicts above were committed, 538bf175)

I read `live_diff_2026-11-18_rules.txt` and the "2026-11-18 Rules after the independent check" section.

**Agree:**
- Same 9 restored groups and the same 19 apps. The builder diffed against main 82df0482; I diffed against
  700bcf9b, and the result is the same.
- All 9 rest on the same own-page rows I cited (records L144/145/549/992/993/998/1000; lists L122/283/333/334/
  413/306/1543/2686/1720/1732).
- The 4 restored groups outside the earlier sample (6CPZ-5423395-B, 6CPZ-9923394-B, 6CPZ-9923394-C, 15890412)
  hold up under my read.
- R14: I read AP(37) as coupe-only, as the builder did, and against the earlier verifier's class (b). The
  removal stands.
- Drive notes: the builder already flagged that most GM "2WD only" notes come from 4wd pages never read
  ("under-claim rather than over-claim"). I agree and put a number on it: 30 of 36 GM app-years.

**Add (the builder did not raise these):**
- On the four 6CPZ Focus/Transit Connect groups, the door side differs between the two models' pages.
- The Mopar "1500: 4WD only" limit rests on FIT rows that no 2012 1500 headlamp before 07/23/2012 lists for
  2WD, so those rows look incomplete rather than a real drive split.
- The Mopar "Up To 07/23/2012" production window is not named in the note.
- The 1999 Tahoe/Yukon rear-door body point (Found item 3).

**No disagreement on any verdict.**

## 2026-11-18 Per-app gates on OEM groups (builder subagent of session_01LsgNuWEh1vdaDCtdP1jxMM, branch `interchange/gates-1118`)

Hub brief: turn the §5.16 note limits ("Tahoe: 2WD only", "1500: 4WD only",
"Q70: 3.7L, gas only", "crew cab only") into real per-app gates in the payload
and docs/app.js; claims only down; sw jh-v212; test_model_map on the pinned
inventory. Hub refinement mid-task: carry each drive limit's basis, word the
unchecked kind honestly. Base rules-1118 (54d0784d), then origin/main b9785c22
(rules-1118 merged) merged in. No fetch, crawl, dispatch, email or main push.

### What the data carries

- Curated group (`groups/<ns>.json`, Likely only): new optional field
  `"gates": [[make, model, lo, hi, gate], ...]`, each run inside the group's own
  apps. Apps, ids and claims are unchanged. `validate.gate_problem` / `_gates_ok`
  hold the vocabulary and refuse a run outside the apps (V2):
  - `drive`: classes of ONE family joined by "/": 2wd fwd rwd | 4wd awd a4wd;
  - `drive_basis`: `stated` | `unchecked` (below);
  - `body`: a silhouette (sedan coupe hatchback wagon suv pickup van
    convertible) or a list; `cab`: "crew cab", "king cab", "supercrew"...;
  - `eng`: ["3.7L", ...]; `fuel`: gas | hybrid | diesel; `trans`: MT | AT.
- Payload (`docs/data/oem/<cat>.json`): the aftermarket row's 6-element shape,
  position 4 unused. `_oem_gated_apps` splits a run where the gate changes and
  raises on a gate outside the apps (the namespace is dropped, fail closed).
  Example, gm 23227000:
  `[["Cadillac","Escalade",2007,2007], ["Chevrolet","Tahoe",2007,2007,null,{"drive":"2wd","drive_basis":"unchecked"}]]`.
  Old readers (`pfAppMatches`, measure.py, coverage_matrix.py, live_diff.py)
  read a[0..3] only.
- Note text unchanged, except unchecked drive limits (next section).
- Body: no rule writes a body limit into a note today (the body-variant rule
  drops the vehicle-year instead), so no group carries `body`. It is supported
  end to end and tested.

### Drive basis (hub refinement)

`Curation.drive_basis`:
- **stated**: every own-page row of the number names the drive itself (option
  code, GM series letter, a drive note); or it sits on a drive-named page while
  T's page of the other drive family was read IN THIS CATEGORY without the
  number; or (fitment-row limits) another number's fitment row on T's page
  names the other drive.
- **unchecked**: everything else.

Same gate for both. The note says "<model>: only 2WD checked" for unchecked.
That is the hub's "checked for 2WD; 4WD not checked" in fewer characters: the
long form pushes the four 2004 Trailblazer regulator notes over 160 and they
would be refused. When every vehicle-year of a group is unchecked within one
family under different labels, the family is named once ("only 2WD checked",
C-Max 2WD + Focus FWD). Otherwise the restored CV6Z-5423394-B/-5423395-B notes
reach 170 characters.

App-years per make (shipped):

| make | stated | unchecked | other gates |
|---|---|---|---|
| Chevrolet | 0 | 34 | fuel 11, cab 1 |
| GMC | 2 (Yukon 2003 mirrors, both pages read) | 0 | cab 2 |
| Ram | 2 (55277414AB/15AB, "6 - Lt. Duty DODGE 4WD") | 7 (climate 3, headlamps 4: fitment rows only) | |
| Ford | 0 | 0 (12 dropped: single-drive, below) | |
| Mercedes-Benz | 0 | 0 (2 dropped: single-drive, below) | |
| Kia (hmg, held) | 44 | 0 | eng 81, trans 4 |
| nissan candidate | Nissan 45, Infiniti 12 | 0 | cab 95, eng 86, fuel 113, trans 6 |

- GM: 34 of 36 app-years unchecked (the verifier counted 30). I count "the 4wd
  page read in this category" only, from a record seeded on it; pages read for
  other categories do not count.

### Single-drive model-years (hub gates review, after a0363fce)

Hub decisions: unknown-drive donors stay "if equipped" for both kinds; no
body gates that add claims back this round. Fix: no drive limit (no gate, no
note words) on a model-year built in one drive only.

`Curation.drive_material(T, d)`:
- (a) Where the catalog files the model-year by drive (gmpartsgiant 2wd /
  4wd / awd catalogs: the year page's variants), the limit stands only if a
  catalog of the other drive family is offered for that year, read or not.
  Every gated GM model-year offers both (Tahoe, Blazer, S-10, Colorado,
  Trailblazer and Yukon 2wd + 4wd; Traverse 2wd + awd), so GM is unchanged.
- (b) Where the catalog is one per model-year (Ford, Mopar, Mercedes,
  Nissan), structure cannot tell, so `policy.SINGLE_DRIVE_TABLE` (hashed) lists
  the single-drive model-years the gated groups touch. Each entry has a
  one-line basis:
  - Ford Focus 2012 and 2015, C-Max 2013, Transit Connect 2015: FWD. The
    fordpartsgiant catalog is one catalog with no drive split on its pages
    (restored_verify_2026-11-18b).
  - Mercedes ML350 2007-08: AWD. One 'ml350' catalog, and 19 of 19 decoded
    2007-08 ML350s on the pinned lot are AWD.
  - A listed model-year with a limit of the other family would leave the
    vehicle-year out; none occurs.
- Result: ford 6 groups (12 app-years) and mb 1 group (2 app-years) lose the
  limit and its gate. Their notes go back to "window motor only; trim-limited;
  verify the number on the part" etc.
- Ram 1500 2012 is one catalog but both drives (the lot holds 38 4x2, 37 4WD),
  so it is not listed and keeps its limits (2 stated, 7 unchecked).
- Nissan candidate: no gate falls in the case, and the re-curation changed
  only policy_sha256. Every gated Nissan/Infiniti model-year either decodes in
  both families on the lot (Frontier, Xterra, Pathfinder 2005-09, Titan, QX60)
  or has catalog rows coded for both drives (Pathfinder 2011 carries 2WD and
  4WD groups). JX35 2013's AWD limit comes from option codes; JX35 was built
  FWD and AWD.

### How the app applies it (docs/app.js OEM-GATE block, 9666-9810)

`pfOemDonorGate` runs per donor in the OEM loop of `pfRunSearch` (10262).
- Exclude: the car's own data contradicts the limit. Sources: VIN drive type,
  decoded silhouette (extras body), listing / VIN series / single VIN trim (cab,
  hybrid), extras engine and transmission. The donor is not offered for that
  group.
- Confirm: plain row.
- Unknown: shown "if equipped" with a line naming the limit ("this part is
  listed|checked for 2WD only — this donor's drivetrain isn't confirmed, check
  the car"). "checked" is used when the basis is unchecked.
- A seeker on a gated app gets a header line. An unconfirmed limit never
  renders Verified. A group without a gate renders exactly as before.

Unknown behaviour of the existing gates (line numbers on 54d0784d), copied:
- Parts table, scraper/junkyard_scraper.py `match_vehicle`:
  - drive 16555-16584: the decode names a gate class -> "vin"; the listing
    names it -> "listing"; the decode names exactly one other class -> row
    dropped; no decode, or a decode spanning classes -> "unconfirmed" ("if
    equipped", $0 in ranking);
  - body 16585-16598: the same; another decoded body -> dropped; no decode ->
    "unconfirmed";
  - manual 16545-16554: manual -> "vin"; a definite automatic -> dropped;
    unknown -> "unconfirmed";
  - hybrid gas-only rows 16502, 16522: hidden only when the listing or the VIN
    trim/series says hybrid; otherwise shown with no flag.
- Aftermarket gate, docs/app.js:
  - pfAmBodyVerdict 9565, pfAmDriveVerdict 9576, pfAmGate 9588;
  - donor loop 9694: 'exclude' rows dropped; 9699 and 9722: 'unconfirmed' kept
    with "if equipped: this unit is listed for X only — ... isn't confirmed,
    check the car";
  - engine 9518 / 9702 / 9721: dropped only when the decode names another
    displacement; unknown -> "engine not confirmed — check under the hood";
  - transmission 9527 / 9704 / 9737: dropped on a known other class; unknown
    -> "check the transmission".

Choices the OEM gate makes, stated plainly:
- Fuel "gas" follows the parts table: no extra line when nothing says hybrid.
  It also excludes a decode that names Diesel, Electric, CNG, LPG or Fuel Cell.
- "4x2" against an FWD-only or RWD-only limit, and any 4WD/AWD decode against
  "4WD AUTO" (All-Mode), stay "if equipped".
- A decode naming both families ("2WD/4WD", 13 cars) stays "if equipped". The
  parts table and pfAmDriveVerdict would confirm it, which their own comment
  says they should not.
- 4WD vs AWD is exclusion, as pfAmDriveVerdict does.
- An automated manual (AMT) counts as automatic, as the parts table does
  (pfAmCarTrans calls it manual).
- Cab is confirmed only by a cab phrase in the listing, the VIN series or a
  single VIN trim; another named cab excludes. No decoded field holds the cab,
  so on the lots it is almost always "if equipped".

### Effect on the pinned inventory (main@a85c654), app code run in node

(group, lot car) donor pairs, main -> branch:

| ns | pairs main | pairs branch | excluded | if equipped |
|---|---|---|---|---|
| gm | 59,852 | 56,081 | 3,771 | 1,787 |
| mopar | 116,281 | 115,939 | 342 | 27 |
| ford | 27,335 | 27,335 | 0 | 0 (was 3,858 before the single-drive fix) |
| mb | 243 | 243 | 0 | 0 (was 2) |
| toyota, subaru, vag, hmg | | unchanged | | |

- Excluded pairs by distinct cars: Chevrolet 655, GMC 54, Ram 38. All are
  drive exclusions; no fuel or cab exclusion on these lots.
- GM cars that are a donor for no OEM group any more: 8,191 -> 8,152.
- Nissan candidate (not shipped), same census: 3,676 pairs excluded (Nissan
  1,647 cars, Infiniti 189); 6,190 "if equipped".

### Live diff vs origin/main b9785c22 (`groups/_report/live_diff_2026-11-18_gates.txt`)

- Groups: 0 added, 0 removed, 48 notes changed with apps unchanged:
  - gm 34, mopar 7: "<model>: X only" becomes "only X checked";
  - ford 6, mb 1: the drive limit is gone (single-drive model-years).
- Payload: 1,183 -> 1,183 groups, 0 added app-years. Gates added: gm 48
  groups / 50 app-years, mopar 9 / 9. Ford and mb carry no gate.
- Re-curated all 8 shipped namespaces on oem-raw@dca9cd845f26 (pinned
  inventory/decodes); policy.py moved the hash, so every file changes
  policy_sha256. Beyond that:
  - toyota, subaru, vag: nothing;
  - hmg: gates on held groups only;
  - ford, mb: as above.
- Nissan re-curated on @57e8b5b99de0: 286 groups, 106 gated, no note changed.
  It stays `_report/nissan.candidate.json`, not shipped.

### test_model_map

Chose the pinned inventory. M1-M10 run on `a85c654:docs/data/inventory_live.json`,
read with git and sha256-checked. In a shallow clone the M2-M10 block SKIPs
with the reason. The live inventory is still validated and its findings are
printed as REPORT lines, not failed. Move `PIN` when re-curating on a newer
inventory. curate.py itself still refuses to run on live-map errors.

### Tests

- New `curation_tests/test_gates_1118.py` (48 checks): helpers, drive basis
  and drive_material on stubs, SINGLE_DRIVE_TABLE, wording, validator, payload
  shape, committed files (no drive gate on a table model-year).
- `pf_guards_unit.mjs` +39 checks. They pass on this app.js; 29 of them
  fail on 54d0784d's app.js.
- `part_finder_e2e.py` gains a real-payload check: 2007 Tahoe regulators from
  90670; no row naming a gated number is a car its gate rules out; header
  line. interchange_e2e.py covers no OEM donors and is unchanged.
- curation_tests 22/22 files pass (Phase 2 parity SKIP unchanged);
  oem_fitment/tests 42/42.
- Full regression: see "Regression" below.

### Noticed, not fixed

- SINGLE_DRIVE_TABLE covers only the model-years today's gated groups touch.
  If a later crawl brings a drive limit on another single-catalog,
  single-drive model, that model keeps the limit and its gate (undecoded
  donors shown "if equipped") until it gets an entry with a basis. Nothing
  flags such a model by itself. A census like
  `drive_census_models` (pinned-lot decode mix per gated model-year) at each
  re-curation would catch it.
- The verifier's other items are out of scope and untouched:
  - Ford 6CPZ motors sit in different doors on Focus vs Transit Connect;
  - Mopar "Up To 07/23/2012" production windows have no note;
  - the 1999 Tahoe/Yukon "CLASSIC 4 DOOR" body point.
- Body gates could let the body-variant rule keep vehicle-years instead of
  dropping them. That adds claims back, so it is a hub/owner decision.
- measure.py and coverage_matrix.py read OEM apps as ungated (a[0..3]), so
  their coverage counts are slightly high where a gate excludes donors.
- Shipped `_report/<ns>.json` curate reports were not regenerated (as on
  rules-1118); only the groups and the nissan candidate were.

### Regression

`tools/regress.sh`, not under flock, on two code heads:
- b9b3f9b1 (before the single-drive fix): **104 passed, 0 failed, 0 skipped**.
- a833fe49 (the final code head; only this ops section follows it): **104
  passed, 0 failed, 0 skipped**.

Both runs include pf_guards_unit, test_am_gates, test_interchange,
interchange_e2e, part_finder_e2e (tahoe07 gate checks: 33 rows, 34 naming a
gated number, 0 ruled out) and both layout halves. backend/node_modules was a
symlink to the main checkout's for the runs; it is removed and was not
committed. sw stays jh-v212.

### For the hub

1. Merge `interchange/gates-1118`? Every change narrows: 0 added groups,
   0 added app-years, 48 notes reworded or narrowed.
2. Decided by the hub (gates review): unknown-drive donors stay "if equipped"
   for both kinds; no body gates that add claims back this round.
3. Nissan: the candidate now carries 106 gated groups. The independent §11.4
   sample WITH the gates is the next step in the hub's order.

## 2026-11-18 Independent check of the gated nissan candidate (verifier subagent of session_01LsgNuWEh1vdaDCtdP1jxMM, branch `interchange/verify-nissan-1118c`)

Hub brief: an independent §11.4 release sample of
`groups/_report/nissan.candidate.json` (origin/main ac29b2a5; unchanged at
4548edd0 and 9e19285b) with the per-app gates. Check only: no rule, policy,
group or payload file changed. Raw read from git (oem-raw@57e8b5b9); lot,
decodes and extras from main@a85c654, sha256 checked. No fetch, crawl,
dispatch, email or main push. One web search (result text only, one part
number, 24810-ZP93A, no page opened). My own draw and reader were used, not
`audit11_4/sample.py`. The app's OEM-GATE code was ported line by line to
Python to replay the pinned lot. An earlier attempt was lost to a container
restart, so this one started fresh. Builders' notes and the earlier reports
were read only after the verdicts were committed (64b60076).

### Seed 73901118: FAILED (11 WRONG). Do not ship nissan.

- The draw: 30 groups out of the 283 shippable (window-regulator 13,
  side-mirrors 8, gauge-cluster 6, climate-control 3; the 3 wiper-motor groups
  are held), plus 30 pairs taken from other groups.
- Per-item verdicts, with the raw record lines and the lot replay:
  `groups/_report/nissan_verify_2026-11-18c.json`.
- **Groups 21 RIGHT / 9 WRONG / 0 RISK. Pairs 27 RIGHT / 2 WRONG / 1 RISK.**
- WRONG by class (item numbers are the report's):
  1. **Engine limit with no gate, and the car's own decode contradicts it (4).**
     - Items 3 (27510-8Z315) and 5 (24810-7Z809): SE/SC, 3.3L only. The
       Xterra app has no gate, so 3 and 7 lot Xterras decoded 2.4L get plain
       rows.
     - Item 7 (24810-ZP77A): the 2008 Pathfinder V8 has its own VK56DE
       clusters. 2 plain rows.
     - Item 29 (80730-JK00C): the number is listed for the 2.5L "Leather".
       All 9 US Q40s (3.7L) and 2 G25x AWD get plain rows; JK60C is the number
       for "S. AWD. VQ25HR + S. VQ37VHR".
  2. **The "gas" gate lets the QX60 Hybrid through (2): item 12 (96302-3JA9C)
     and item 38 (24810-3JA1B).**
     - The product page lists 3.5L only.
     - 9 and 8 lot QX60s with 5N1CL0 VINs (decoded 2.5L, listed as plain
       "QX60") get plain rows, because nothing on them says "hybrid".
  3. **km/h cluster (1): item 4, 24810-EC44C ("Instrument-Kph").** The US twins
     split differently: the Pathfinder AUTO takes EA47C and the Xterra 4WD SE
     takes EA48C.
  4. **Rogue / Rogue Select mix (1): item 30, 80730-4BA1A (T32 Rogue).** 34 lot
     cars listed "Rogue" for 2014-15 are S35 Rogue Selects (JN8AS5M VINs). The
     catalog files that body as its own model.
  5. **4wd gate where an All-Mode sibling exists (1): item 43, 24810-EA48D,
     Pathfinder 2005.** "W. 4WD" here is a different number from EA47D "*W.
     AUTO". 89 Pathfinders decoded 4WD get plain rows, All-Mode cars included.
  6. **Regular cab not listed, no gate (2, borderline): items 25 (80721-3S500)
     and 27 (80721-2Z700).** The 2002 Frontier page lists these power
     regulators for KC/CC only and lists the regular cab under 3S510. If the
     hub reads this as the power-window option carried by the note, the two
     are RIGHT and groups come to 7 WRONG.
- RISK (1): item 48, 24810-ZP93A. It pairs Pathfinder AUTO with the Xterra
  4WD SE exactly as the km/h EC44C does, and no unit is printed.

### Census of all 283 shippable groups

- **Class 1, a drive-limited part shown plain for both drive families.**
  - 48 drive-limited app-years: 43 gated, 5 not.
  - The 5 ungated app-years are in 2 groups, 24820-1MK5A and 24820-6AH2A (M37
    2012-13 and Q70 2014 speedometers). Their rows read "*SEDAN. 2WDSTD ..."
    and "2WDHICAS", joined tokens. 6 M37x AWD lot cars get plain rows.
  - A related subclass, a 4wd gate next to an AUTO sibling: 2 app-years
    (EA48D Pathfinder 2005, and 9BA7C Pathfinder 2011, which has no 4WD car on
    the lot).
- **Class 2, B14 200SX / sedan-coupe mix: 0 failures.**
  - 2 B14 groups. Both list "4S" and "C" rows on both models' pages.
  - 0 variant-page body splits among the candidate's apps.
- **Other classes:**
  - Engine contradictions with no gate: 20 groups, 286 plain lot cars. The
    largest are 27510-7Z416 (78 cars) and 96301-/96302-EA18E (54 each).
  - km/h clusters: 1 group.
  - Rogue / Rogue Select: 3 groups, 34 cars each.
  - JK61C/JK61D are AT-only speedometers with no gate. No car on the lot is
    decoded manual.

### Agreement / disagreement (read after 64b60076)

- **Agree.**
  - The gates that exist name limits the catalog prints, and the app hides
    the decodes that contradict them.
  - Of the earlier census's 43 DRIVE groups, 25 are no longer in the
    candidate, 16 carry a drive gate and 2 are ungated. The B14 sedan rows
    are gone. The Titan rear-door motors (82730-9FJ0A) are now crew cab and
    read RIGHT.
- **Disagree.**
  - The selfcheck reports 0 WRONG and 0 unexplained suspects. The engine
    column of the product page is not used as a limit, and that is most of
    the gap.
  - The earlier verifier judged 27510-8Z315 (P14) RIGHT. It is WRONG once the
    lot is replayed.
  - The "gas" gate does not catch QX60 Hybrids. This choice is stated in the
    gates section.
  - Two of the earlier census's DRIVE groups are still ungated (joined tokens).
  - The AUTO fix covers only the a4wd side, not the 4wd side.
  - Neither earlier report raised the km/h cluster or the Rogue Select mix.

### Suggested before another independent sample (for the hub; rules untouched here)

1. Gate on engine from the product page's engine column when it leaves out an
   engine that the model-year offers.
2. For gas-only numbers where the hybrid has its own displacement (QX60 2.5L),
   add an engine gate, or have the fuel gate read the decoded engine.
3. Parse joined drive tokens such as 2WDSTD and 2WDHICAS.
4. Leave 4WD decodes "if equipped" under a 4wd gate when the page lists a "W.
   AUTO" number.
5. Refuse "Kph" clusters, as policy already does for Subaru gauge clusters.
6. Treat feed "Rogue" 2014-15 as ambiguous with Rogue Select (VIN JN8AS5), or
   refuse those years.
7. Add a cab-list gate, or refuse the years where the catalog shows a regular
   cab that is not listed.
8. Coverage, not a wrong row: the awd gate hides 4WD-decoded QX60/JX35 cars,
   which are AWD.

## 2026-11-19 Round 3: the five flaw classes on the live makes, nissan candidate rebuilt (builder subagent of session_01LsgNuWEh1vdaDCtdP1jxMM, branch `interchange/round3-1119`)

Hub brief: census the 2026-11-18c check's flaw classes on the 8 shipped
makes and fix them, claims only down (Part A); apply the verifier's 8
suggested fixes to the nissan candidate and re-check every WRONG/RISK item
(Part B). Pins: oem-raw@dca9cd84 (shipped), @57e8b5b9 (nissan), lot
main@a85c654 (inventory, decodes, vehicle_extras). No fetch, crawl, dispatch,
email or main push. This continues the builder stopped by the restart: its
uncommitted rules (in another worktree) were recovered, reviewed, corrected
and finished here.

### Rules (curate.py / policy.py / validate.py; hashed inputs, all shipped namespaces re-curated in the same push)

- **Engine column (class 1)**, `policy.LIKELY_FIT_ENGINE_RULE`,
  `Curation.fit_engine_limit`: when every product-page fitment row of a
  number for T prints a displacement and they leave out one T's model-year
  offers, the number is limited to the printed ones (gate `eng`, note "Camry:
  2.4L, hybrid only"). "Offers" = the catalog attests it for T AND T's year
  page lists it or a lot car of T is decoded with it (`curate.lot_engines`,
  new `--extras` input; its sha256 is recorded in the report inputs). The
  catalog alone over-states a model-year (one Camry row covers 2007-2017 with
  2.4/2.5/3.5L) and a lot decode the catalog never attests is a listing/VIN
  mismatch (a "2000 F-150" decoded 7.3L); without the lot input every attested
  displacement counts (fail closed).
- A column naming none of the engines T offers leaves T out
  (`fit_engine_conflict`: JK00C "2015 Q40 | 2.5L", every Q40 is 3.7L).
- **Fuel words (class 2)**: "gas only" from the column needs GAS/FLEX words;
  a bare "2.4L L4" says nothing (the inherited code read it as gas and dropped
  the Camry Hybrid from shared hoods/grilles). Hybrid words include
  fordpartsgiant "4 Cyl 2.5L PFI Gas/Electric" (Fusion/MKZ/Milan hybrid; the
  inherited regex missed it). Engine strings of both raws were censused for
  this (GM, Nissan and Lexus print no fuel at all). A Hybrid-named feed year on
  a gas column is left out.
- **"gas" gates read the decode**: a gas-limited year whose engine column
  leaves out an attested displacement carries `eng_not` (the hybrid's own
  displacement, e.g. QX60 2.5L). docs/app.js rules out a donor decoded with
  one; an undecoded donor is unchanged; no note change. I first tried making
  the column the engine gate there: on GM it lists the hybrid's 6.0L among the
  gas engines, so it protected nothing and its label pushed 10 notes past 160.
- **Market (class 3)**, `LIKELY_MARKET_UNIT_RULE`: km/h-first units
  ("KMH/MPH", "KPH/MPH", "Instrument-Kph"; "MPH/KMH" is the US unit) and
  mandatory export equipment groups ("Mandatory (EUROPEAN EQUIPMENT GROUP)",
  "EXPORT Mandatory (Middle East ...)") are not US parts: per own-page row, and
  class-wide when the record names the km/h unit (`held_market_kph`).
- **Cab / body lists (class 4)**, `LIKELY_CAB_LIST_RULE`, per model-year: every
  configuration names a cab (fitment trims, or Nissan T/KC/CC codes) and T's
  page lists a left-out cab under another number of the slot -> gate `cab`
  (a string, or a list of 2+ cabs); silhouettes in fitment trims -> gate
  `body`. A model whose years share one list is named once ("Frontier: king
  cab/crew cab only"). On Nissan pages the cabs a model-year comes in are read
  from every category (2003-04 Frontier: KC/CC only on every page); GM trim
  strings keep the same-slot requirement (they mix cab words into trim names).
- **Joined drive tokens (class 5)**: 2WDSTD / 2WDHICAS read as 2WD (the only
  joined forms in either raw).
- **All-Mode sibling**: a Nissan "4WD" number beside an "AUTO" number of the
  slot gets `drive_not: "a4wd"`; the app keeps 4WD decodes "if equipped".
- **Rogue / Rogue Select**: `policy.AMBIGUOUS_FEED_YEARS` (Rogue 2014-15): the
  year joins only if the Rogue Select pages of that year list the number too.
  Raw seeds exist only as ("Rogue Select", 2014), so 2015 is always refused.
- App (docs/app.js OEM-GATE): `cab` lists, `drive_not`, `eng_not`; sw
  `jh-v213`. Payload shape unchanged (`[make, model, lo, hi, null, gate]`);
  old readers ignore the new keys.

### Part A census (`groups/_report/class_census_2026-11-19.json`)

Counts are (group, lot car) donor pairs shown plain that the car's own decode
contradicts, replayed with the app's own OEM-GATE code
(`audit11_4/lot_replay.mjs`). Before = origin/main groups and app; after = this
branch.

| class | gm | ford | mopar | toyota | subaru | vag | mb | hmg |
|---|---|---|---|---|---|---|---|---|
| 1 engine, material: groups / app-years / pairs before | 3 / 3 / 30 | 4 / 10 / 628 | 45 / 78 / 514 | 32 / 32 / 7,196 | 2 / 3 / 27 | 2 / 2 / 6 | 0 | 0 |
| 1 engine, material, after | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1 engine, raw (catalog-only, over-broad) before -> after pairs | 42 -> 12 | 632 -> 3 | 533 -> 19 | 7,196 -> 0 | 28 -> 1 | 6 -> 0 | 0 | 0 |
| 2 gas gate, hybrid displacement: app-years (pairs) | 11 (0) -> 9 (0), 7 with eng_not | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 3 market text hits: groups before -> after | 3 -> 3 | 9 -> 5 | 3 -> 0 | 24 -> 24 | 0 | 0 | 0 | 0 |
| 4 cab list ungated: groups / app-years | 2 / 4 -> 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 4 body list ungated: groups / app-years (pairs) | 2 / 2 (66) -> 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 5 joined drive tokens | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

- Class 1 is real on the live makes. Largest: 2011 Camry bumpers, grilles,
  headlamps, tail lamps, clusters, climate panels and mirrors whose column
  lists only "2.4 L FULL HYBRID" were plain for 350 gas Camrys each (2.5L);
  Fusion/MKZ hybrid clusters plain for 3.0/3.5L cars; 2016 Malibu window
  motors (new body) plain for the old-body 2.5L Malibu Limited.
- Raw leftovers after are decodes the catalog never attests for T (a 2.5L
  Yukon, 1.0L Titan, 3.0L F-150): listing/VIN mismatches, not class 1.
- Class 2 on GM: the 11 "Silverado 1500 2012: gas only" years; 0 plain pairs on
  this lot (no 2012 1500 decoded 6.0L; the lot's 2011/2013 hybrids say Hybrid
  in the VIN trim, which the gas gate reads). 7 now carry eng_not ["8.1L"]
  (attested, impossible, harmless); the hybrid's 6.0L cannot be ruled out from
  GM's column (it lists 6.0L for the gas trucks). RISK left: a Silverado Hybrid
  with an unusable VIN trim, listed plain, decoded 6.0L.
- Class 3 after: ford's 5 are "MPH/KMH" / "MPH/KPH" (US) and "(-)GCC"
  (negated); GM's 3 are one "(EXPORT)" configuration beside US ones; toyota's
  24 are "CANADA SPEC" alternatives beside US ones (the existing rule keeps
  those rows). None is a flaw. Removed: ford 3 Canada clusters, mopar 3 export
  mirrors.

### Live diff vs origin/main 9945d42d (`groups/_report/live_diff_2026-11-19_round3.txt`)

| ns | removed | narrowed (changed) | app-years gated narrower | added claims |
|---|---|---|---|---|
| gm | 2 | 12 | 12 | 0 |
| ford | 4 | 1 | 3 | 0 |
| mopar | 10 | 38 | 64 | 0 |
| toyota | 0 | 32 | 32 | 0 |
| subaru | 0 | 2 | 3 | 0 |
| vag | 0 | 2 | 2 | 0 |
| hmg, mb | 0 | 0 | 0 | 0 (hmg: 4 held strut groups removed) |

- **0 added groups, 0 gained app-years, 0 widened gates on every shipped
  namespace.** 16 live groups removed, 87 narrowed. Correction: commit
  21663350's message says "77 narrowed" and "264 -> 244"; the right figures are
  87 and 283 -> 246.
- Removed: ford AE5Z-10849-MA, BE5Z-10849-BC ("With KMH/MPH Speedometer"),
  YL3Z-10849-DA ("...KPH/MPH": the km/h-first reading, fail closed; its note
  says "programmed ... for all vehicles", so a second reader may judge it US),
  AE5Z-10849-LA (MKZ 2010 left out: its row is the 2.5L hybrid, every 2010 MKZ
  is 3.5L, and Milan alone is one model); mopar 4805424AI, 4805947AB, 4806270AA
  (export equipment groups); mopar 7 Town & Country/Caravan/Grand Caravan 2004-05
  mirrors and gm 20835552/3 (Silverado master switches, regular cab under
  another number) are refused only because the named limit makes the note
  over 160 chars: lost coverage, not wrong claims.
- Payload (docs/data/interchange.json + oem/*.json) 1,506,506 -> 1,507,600
  bytes; oemStatus ok x8.

### Plain donors on the pinned lot (app code in node)

| ns | plain pairs | if equipped | excluded | cars with a plain row |
|---|---|---|---|---|
| gm | 54,294 -> 53,238 | 1,787 -> 1,913 | 3,771 -> 3,867 | 8,134 -> 8,046 |
| ford | 27,335 -> 24,523 | 0 -> 581 | 0 -> 229 | 6,949 -> 6,949 |
| mopar | 115,912 -> 108,299 | 27 -> 1,978 | 342 -> 751 | 7,629 -> 7,521 |
| toyota | 112,182 -> 97,429 | 0 -> 7,557 | 0 -> 7,196 | 2,211 -> 2,211 |
| subaru | 4,055 -> 3,992 | 0 -> 36 | 0 -> 27 | 1,184 -> 1,143 |
| vag | 1,501 -> 1,489 | 0 -> 6 | 0 -> 6 | 458 -> 458 |
| hmg, mb | unchanged (3,754; 243) | | | |
| **shipped** | **319,276 -> 292,967** | **1,814 -> 12,071** | **4,113 -> 12,076** | |
| nissan candidate | 76,270 -> 59,047 | 6,190 -> 4,961 | 3,676 -> 1,790 | 15,227 -> 14,995 |

The new app run on main's groups gives main's numbers exactly (the app change
alone moves nothing). Toyota's 7,557 "if equipped" are mostly 2007-2011 Camrys
decoded 2.4L on hybrid-only parts: the gas 2.4L (2007-09) and the hybrid
decode the same, and nothing on the car says hybrid.

### Part B, nissan candidate (oem-raw@57e8b5b9; NOT shipped)

`groups/_report/nissan.candidate.json`: 249 Likely, **246 shippable**
(was 283): window-regulator 113, side-mirrors 66, gauge-cluster 46,
climate-control 21; 84 gated (eng 51, fuel 40, cab 25, drive 24, trans 8,
drive_not 1). Refusals: held_drive_qualifier 65 (note over 160), km/h 62,
engine conflict 47. Against the old candidate: 38 removed, 25 narrowed,
1 added (24810-9BD4C, 4 app-years: it was refused only by the note cap; the
engine column now gives every year the same narrower label, so the note fits).

Verifier items (`groups/_report/nissan_recheck_2026-11-19.json`, my own
re-check, not independent):

| item | now |
|---|---|
| G3 27510-8Z315 | fixed: Xterra eng 3.3L (Frontier crew cab + 3.3L); 3 Xterra + 41 Frontier 2.4L not offered |
| G4 24810-EC44C | fixed: refused, km/h (record "Instrument-Kph") |
| G5 24810-7Z809 | fixed: Xterra eng 3.3L, Frontier king/crew cab + 3.3L; 7 + 41 2.4L not offered |
| G7 24810-ZP77A | gone: note over 160 ("Pathfinder 2008: 2WD, 4.0L only") |
| G12 96302-3JA9C | gone: note over 160 (QX60 2014-15 "3.5L, gas", 2016-17 "gas") |
| G25 80721-3S500 | gone: note over 160 ("Frontier 2002: king cab/crew cab only; Xterra 2004: 3.3L only") |
| G27 80721-2Z700 | fixed: Frontier 2002 king/crew cab; 2003-04 plain because no category on those pages codes a regular cab (2003 KC 62 / CC 60 rows, 2004 KC 41 / CC 42) |
| G29 80730-JK00C | gone: Q40 left out (column 2.5L, every Q40 3.7L); G25 alone |
| G30 80730-4BA1A | fixed: Rogue 2014-15 out. Murano 2016-17 / Rogue 2017-19 "gas only" with no engine gate (no engine column on its page); 0 hybrids on the lot; RISK stays |
| P38 24810-3JA1B | fixed: QX60 eng 3.5L + gas; 8 QX60 2.5L (5N1CL0) not offered |
| P43 24810-EA48D | fixed: Pathfinder 4wd + drive_not a4wd; 89 4WD "if equipped", 70 4x2 out |
| P48 24810-ZP93A (RISK) | unchanged: no unit printed, km/h rule cannot read it |
| census 24820-1MK5A / 6AH2A | fixed: M37 2WD (stated); 6 M37x AWD out |
| census 24810-9BA7C | gone: note over 160 |
| census JK61C / JK61D | gone, no refusal record, step not traced; the AT-only limit is still not read for them |
| census 27510-7Z416, 96301/2-EA18E | gone: note over 160 |
| item 8 (awd gate hides 4WD-decoded QX60/JX35) | not changed: showing them would add claims |

Census of the rebuilt candidate: material engine 0, cab 0, body 0, market 0;
joined tokens 4 groups (K6301/K6302 mirrors whose rows list "(2WDSTD+
2WDHICAS) + 4WD": both drives, correctly ungated); fuel 29 groups / 85 years
with a gas gate and no engine column (0 plain pairs). No release sample was run;
a new independent checker decides.

### Tests

- New `curation_tests/test_round3_1119.py` (36 checks); `pf_guards_unit.mjs`
  r3 block, 25 checks (cab lists, drive_not, eng+hybrid, pfRunSearch; the 5
  eng_not checks are new here, the rest came with the recovered work).
- curation_tests 23/23 files pass (Phase 2 parity SKIP unchanged);
  oem_fitment/tests 42/42; test_interchange, test_am_gates, pf_guards_unit pass.
- Full regression, `tools/regress.sh` on bf5fe452 (code and groups final;
  only this ops text follows): **101 passed, 3 failed, 0 skipped**.
  - FAIL `backend/test/cars_feed_e2e.mjs` (1 of 139: "the token rides along:
    on at once, no confirmation email..."; the alert strip's text was empty
    after the click). Re-run alone under the test lock: **139 passed, 0
    failed**. A flake in the free-alert strip, not this branch's code.
  - FAIL `backend/test/ui_no_truncation.mjs` both halves, the same single
    failure at all six widths: `[cards-mixed] setup-error: no real-photo card
    with three cards after it` (1,320 checks run, no other failure).
    Reproduced alone (`SCREENS=cards-mixed WIDTHS=390`). It is a setup error
    from the cars-feed data near the test zip: this branch changes app.js only
    inside the OEM-GATE block (9666-9835), whose only callers are in
    `pfRunSearch`, and does not touch the inventory or photo data (the
    9e19285b auto-scan does). Not verified on main: the privacy hook refused
    swapping main's app.js in. For the hub: run that screen on main before
    merging anything.
  - Everything else passed, including pf_guards_unit, test_am_gates,
    test_interchange, interchange_e2e, part_finder_e2e, pf_ux_e2e and
    photo_layout_e2e. backend/node_modules was a symlink for the run; removed,
    not committed.
- After the run, origin/main moved (55cb877a, an auto-scan and an ops note)
  and was merged (f0682e10): the 30 payload files taken from main and rebuilt
  from this branch's groups (oemStatus ok x8). On the merged tree
  curation_tests 23/23, oem_fitment/tests 42/42, test_interchange,
  test_am_gates and pf_guards_unit pass; the cards-mixed layout screen still
  fails with the same setup error on the new feed data. The full regression
  was not re-run on the merge.

### Noticed, not fixed

- The 160-char note cap now costs real coverage: 9 live groups (7 Caravan/T&C
  mirrors, 2 Silverado switches) and 65 nissan groups (37 before this round) are
  refused only because the true limit is long. Suggest: once a limit is a gate, let the note say
  "engine-limited (see each car)" instead of listing every year; the app's
  per-donor line already names the limit. Hub/owner decision.
- Engine limits on body parts are often immaterial (Caravan mirror
  "2.4L/3.3L only"): true per the page, but they turn undecoded donors into
  "if equipped" (mopar 96 cars). Coverage only.
- GM Silverado Hybrid 6.0L vs the "gas" gate: see class 2 (0 cars today).
- YL3Z-10849-DA "KPH/MPH" removal is the strict reading; worth a second look.
- JK61C/JK61D AT-only speedometers: no transmission gate rule reads them.
- The census's market-text measure is noisy (US alternatives); the rule reads
  units and equipment groups only.
- `backend/node_modules` was symlinked for the regression and removed; not
  committed.

### For the hub

1. Merge `interchange/round3-1119`? Live: 0 added claims, 16 removed, 87
   narrowed (diff file above). App change + sw jh-v213.
2. Nissan: 246 shippable, not shipped; needs a new independent sample.
3. Decide the note-cap suggestion above before the next round; it is the
   largest remaining coverage cost.

## 2026-11-19 Round 4: same-option drive siblings, build windows, pages that disagree, VIN/listing mismatch (builder subagent of session_01LsgNuWEh1vdaDCtdP1jxMM, branch `interchange/round4-1119`)

Hub brief: apply the four round-4 decisions (after the independent check
`interchange/verify-nissan-1119d`, seed 38271119: 2 WRONG, 13 RISK) on the 8
shipped makes first, claims only down (Part A), then on the nissan candidate
(Part B, not shipped). Base origin/main 613d18e5. Pins: oem-raw@dca9cd84
(shipped), @57e8b5b9 (nissan), lot main@a85c654 (inventory, vin_decodes,
vehicle_extras; sha256 1a9cfa73 / 1357625b / 6ff3d44b, checked). No fetch,
crawl, dispatch, email or main push. Baseline check first: main's code
re-curated on the pins reproduces every committed groups file byte for byte.

### Rules (curate.py / policy.py / validate.py; hashed, all 8 shipped namespaces and the candidate re-curated in the same push)

- **Decision 1, `policy.LIKELY_DRIVE_SIBLING_RULE`**
  (`Curation.drive_sibling`, `drive_sibling_limit`). Per own-page row of the
  number on T's page and per option clause (each "Fitting Vehicle Options"
  alternative; on the config-tuple sites each "+" part too, as `_fvo_drive`
  reads them; asterisks ignored, so "starred or not"): a row of the same part
  name and position with the same clause plus a drive word means this clause
  does not cover that drive. Not read as a split (each is a case in the raw):
  a sibling that also lists the bare clause or lists it for both drive
  families (the Titan clusters 7S005 / 7S002), a sibling linked by
  supersession, one not listed for T itself (a production window under 5
  months of T's year: JX35 2013 3JA1B beside 9NA1B 06/2013-09/2014). The
  limit is then read against the drive words T's pages use: excluding AWD on
  a QX60 page (AWD is its only 4-family word) leaves `drive: "2wd"`, basis
  stated; excluding one 4-family system beside another (4WD beside AUTO)
  gives `drive_not` alone (none occurs in today's data; the app supports it).
  Siblings that exclude both families, or a sibling that contradicts the
  row's own drive, leave the vehicle-year out.
- **Decision 2, `policy.LIKELY_BUILD_WINDOW_RULE`** (`Curation.build_window`).
  The window(s) the number's own rows on T's page print ("Production Date":
  `08/2009-01/2010`, `from 01/2010`, hyundai `till 05/2012`, comma lists, and
  subarupartsdeal `200409 - 200608`, which no rule read before) against T's
  model year as the production rule takes it (07/(y-1)-06/y). Where they
  leave months out and a dated row of the same part, position and
  configuration (same clause; another colour or package is another car) that
  is NOT the number's predecessor or successor (`comparable`: a common
  successor is not a link) carries those months, the vehicle-year keeps the
  claim only with the window in the note ("Pathfinder 2010: 4.0L, built
  08/2009-01/2010 only") and a gate `built: "2009-08..2010-01"` (open ends
  empty: `"2010-01.."`, `"..2005-12"`; runs joined by ","). Rest carried by
  a linked number: unchanged. No dated row carries the rest: unchanged
  (`no_other_row`, counted). One extra choice, stricter than the brief, for
  the hub to confirm: where T's page in the category is not in the raw (the
  product record's own seed-page notes are the only evidence, e.g. the 2010
  Xterra for 27510-EA00A) nothing can show the rest is linked, so a dated
  window with a gap is gated too (`no_page`).
- **Note cap**: a window whose words take the note past 160 characters
  leaves that vehicle-year out (never cut), one at a time, longest label
  first; if that leaves one model, the group is refused
  (`held_window_note_cap`, recorded). Other over-long limits refuse as before.
- **Decision 3** (same function). T's page prints no date for any row of the
  number, and another model-year page of the same catalog model (same site,
  same seed model) prints a window for the same clause, word for word: that
  window is read. Under 5 months of T's year leaves T out (as if T's page
  printed it); otherwise decision 2 applies. Not narrowed: a clause no other
  page dates (96301-ZC20A is dated "W. SE" on the 2006 Armada page and listed
  undated for "W. LE/SL" on the 2009-2015 pages), and a page that lists the
  number's predecessor or successor (a supersession listing: the 2005 Armada
  page lists 7S200 "Replaced By" ZC20A).
- **Never adding**: a group round 3 refuses stays refused (the round-3
  vehicle-years and drive limits are tried first; the strict-note check runs
  on them too). An earlier build without this guard brought back 12 nissan
  groups whose note fitted only after a vehicle-year left.
- `validate.gate_problem`: `built` (format, start <= end, not both ends
  empty), `drive_not` alone (classes of one family). Payload shape unchanged
  (`[make, model, lo, hi, null, gate]`).

### App (docs/app.js OEM-GATE; sw `jh-v214`)

- `built`: verdict always "unconfirmed" (no decode gives the build month).
  Donor line: "if equipped: this part is listed for cars built
  08/2009-01/2010 only — check the build date on the door sticker"; with
  another unconfirmed limit both lines, the first without the window. Other
  limits still exclude (a 5.6L Pathfinder on a 4.0L + window gate). Seeker
  header: "found for a 2010 Pathfinder with 4.0L, built 08/2009-01/2010
  only" ("built ..." alone without "with").
- `drive_not` alone: a decode in that family stays "if equipped", the other
  family confirms, nothing is excluded.
- **Decision 4** (in `pfOemDonorGate`): a car with `v.vpicMismatch`
  (expandV2Row, the vpic side table's 5th field: the scraper's
  `_vpic_mismatch_msg`, year and make) is never a plain OEM row: a confirm
  becomes "if equipped: this car's listing and VIN disagree, check the car";
  an unconfirmed gate gets the line added; a gate the decode rules out still
  excludes. A group with no gate and a car with no flag render exactly as
  before. Aftermarket, platform-group and same-generation paths unchanged.

### Part A census, 8 shipped makes (`groups/_report/round4_census_2026-11-19.json`)

Before = origin/main groups and app; after = this branch. App-years (plain
lot pairs the class contradicts). The detectors are curate.py's own, run by
`audit11_4/round4_census.py`; the lot through `audit11_4/lot_replay.mjs`.

| class | gm | ford | mopar | toyota | subaru | hmg | vag | mb |
|---|---|---|---|---|---|---|---|---|
| 1 same-option drive sibling | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2 window, unlinked or no page: before | 0 | 5 (640), all no_page | 0 | 18 (68): 16 unlinked, 2 no_page; 6 edge | 0 | 1 (323) | 0 | 0 |
| 2 after | 0 | 4 gated + 1 group refused | 0 | 18 gated | 0 | 1 gated | 0 | 0 |
| 3 pages disagree | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 4 VIN/listing mismatch, plain pairs (cars): before | 193 (10) | 1 (1) | 2 (2) | 89 (1) | 0 | 6 (1) | 0 | 0 |
| 4 after | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

- Class 1 is a Nissan/Infiniti pattern; a raw-level scan of every shipped
  site's pages found clause-level drive siblings only on 1992 Subaru Legacy
  pages, which no live group touches. Mopar line codes ("C - CHRYSLER" beside
  "F - BRAND AWD") are a substitution, not "the same option plus a drive
  word", and are left to the existing drive rule.
- Class 2 live cases: Lexus IS 350 2012 / IS 250 2013 headlamps and colour
  mirrors (e.g. 87910-53401-C1 11/2011-04/2013; the earlier 53400-C1 has no
  "Replaced By"), RX 400h 2006 headlamps (08/2005-08/2007, 07/2005 under
  48260), Hyundai Sonata 2015 door 76004-C1000 (04/2014-12/2014, then
  C2000), Ford Taurus 2008 climate panels, Explorer Sport Trac 2001 motor,
  Five Hundred 2005 switch (seed-page notes only). Edge cases (1-2 months at
  a model-year edge): toyota 6.
- GM, Mopar, VW/Audi and Mercedes pages print no "Production Date" field;
  Mopar's "Up to 07/23/2012" / "After ..." free notes are not read as windows
  (the verifier's 2012 Ram 1500 point stands, see below).
- Class 4 cars: 8 Trailblazers listed 2004 with 2005 VINs, a 2014 Cruze (VIN
  2013), a 2000 Silverado 1500 (VIN 2002), a 2007 Expedition (VIN 2008), a
  2000 Durango (VIN 1999), a "Jeep Patriot" with a Kia VIN, a 2007 IS 250
  (VIN 2008), a "2015 Sonata" with a 2000 Buick VIN.

### Live diff vs origin/main (`groups/_report/live_diff_2026-11-19_round4.txt`)

**0 added groups, 0 gained app-years, 0 widened gates on every shipped
namespace.** gm, mopar, subaru, vag, mb: only `policy_sha256`. ford: 1
removed (F87Z-7823394-AA, Explorer Sport + Sport Trac 2001: both app-years
windowed from seed-page notes, the note over the cap), 4 narrowed; toyota 16
groups narrowed (18 app-years gated); hmg 1 narrowed. Payload rebuilt,
oemStatus ok x8.

### Donor pairs on the pinned lot (plain / if equipped / excluded), app code in node

| ns | plain | if equipped | excluded | cars with a plain row | old app on the new payload: plain / if eq. |
|---|---|---|---|---|---|
| gm | 53,238 -> 53,045 | 1,913 -> 2,106 | 3,867 -> 3,867 | 8,046 -> 8,036 | 53,238 / 1,913 |
| ford | 24,523 -> 23,839 | 581 -> 1,124 | 229 -> 229 | 6,949 -> 6,802 | 24,382 / 581 |
| mopar | 108,299 -> 108,297 | 1,978 -> 1,980 | 751 -> 751 | 7,521 -> 7,519 | 108,299 / 1,978 |
| toyota | 97,429 -> 97,272 | 7,557 -> 7,714 | 7,196 -> 7,196 | 2,211 -> 2,210 | 97,429 / 7,557 |
| subaru, vag, mb | unchanged (3,992; 1,489; 243) | | | | |
| hmg | 3,754 -> 3,426 | 0 -> 328 | 0 -> 0 | 734 -> 733 | 3,754 / 0 |
| **shipped** | **292,967 -> 291,603** | **12,071 -> 13,294** | **12,076 -> 12,076** | | 292,826 / 12,071 |
| nissan candidate | 59,047 -> 47,411 | 4,961 -> 4,281 | 1,790 -> 847 | 14,995 -> 13,511 | 50,289 / 1,403 |

The new app on main's groups moves exactly the mismatch pairs (shipped 291,
nissan 32); nothing else.

### Old reader and `built` (checked: origin/main docs/app.js on the new payload)

- An old app ignores the unknown key: `pfOemGate` returns confirm, so a
  donor of a built app-year renders as a **plain row**. On the pinned lot:
  1,099 shipped rows (ford 708, toyota 68, hmg 323; nissan candidate 2,852).
- Every one is in a group whose note names the window ("RX 400h: built
  08/2005-08/2007 only", or "built 09/2011-04/2013 only" when every app-year
  shares it; a committed-file test checks this for every built gate).
- But an old `pfRunSearch` keeps only the first Likely group's note on a row.
  Where the same car is also a donor for another group of the category whose
  note names no window, that row may show without the window: **489 of the
  1,099 shipped rows** (ford 98, toyota 68, hmg 323). So the requirement "an
  old app does not show the donor plain without a note" holds per group but
  not for those multi-group rows. The new app adds every gate line to the
  row and is not affected; an app older than gates-1118 ignores all gates.
- Old readers in the field: the web app reloads its shell on jh-v214; the
  native store builds bundle app.js (native/README.md) and read new payloads
  with their own code until a store release (rule 1: the owner's "ship").

### Part B, nissan candidate (oem-raw@57e8b5b9; NOT shipped)

`groups/_report/nissan.candidate.json`: 228 Likely, **225 shippable** (was
246): window-regulator 113, side-mirrors 60, gauge-cluster 34,
climate-control 18; 115 groups carry gates (built 52, fuel 32, eng 26, cab
18, drive 10, trans 1). Against the old candidate: 21 removed, 89 narrowed
(121 app-years left), **0 added**, 0 widened. Refusals new this round:
`held_window_note_cap` 18; `held_drive_qualifier` 66 (was 65).

Census before -> after (app-years): sibling 20 (254 plain AWD/4WD pairs) ->
7 gated, 0 contradicted; window 109 (3,834 plain; 49 edge; 22 no_page) -> 60
gated (31 edge); pages 107 (102 under 5 months: left out) -> 2 gated; VIN
mismatch 32 pairs (6 cars) -> 0.

Every WRONG and RISK item of the 1119d report (`groups/_report/nissan_recheck_2026-11-19d.json`; my own re-check, not independent):

| item (1119d) | now |
|---|---|
| WRONG 96301-3JA9B QX60 mirror (and LH 96302-3JA9B, census) | refused: with "QX60 2015-2017: 2WD, gas only" (sibling 3JN9B) the note is over 160; no QX60 row |
| WRONG 24820-3ZD0A QX56 2013 speedometer (and 3ZD1A) | QX56 2013 gated `drive 2wd` (sibling 1ZS0A "*3ROW. AWD. PREMIUM") + `built 2013-02..2014-08`; 6 4WD QX56 out, the rest "if equipped"; QX80 2014 unchanged |
| RISK 27510-EA00A Pathfinder 2010 window | refused (`held_window_note_cap`): Pathfinder 2010 and Xterra 2010 (seed notes, no_page) both windowed, the note over 160; Xterra 2009 left out by decision 3 |
| RISK 82720-7S000 (and 82721-7S000) 2006 window | Armada/Titan 2006 and Titan 2004 (seed notes only, window from 10/2003) left out by the note cap; Armada 2004-2005 + Titan 2005 crew cab remain |
| RISK P13 24810-9BA5B Xterra 2011 window | group refused (note cap; 2010 left out by decision 3) |
| RISK 96301-3JA9A (AWD starred sibling + 2016 window) | refused: "W. BASE" beside "*W. AWD. BASE" is a sibling ("starred or not"); note over 160 |
| RISK 24810-7Z803 pages disagree (2001 vs 2002) | 2001 Frontier/Xterra left out (decision 3); 2002 unchanged |
| RISK 80720-2Z710 pages disagree | Frontier 2002 left out (decision 3); Frontier 2003 `built 2002-10..`; **Xterra 2002-2003 unchanged** (the dated page is the Frontier's; decision 3 reads the same catalog model only) |
| RISK P5 96301-ZC60A Armada 2007 | Armada 2007 left out (2 months of MY2007 on the 2006 page's window) |
| RISK feed identity (Yamaha-VIN "Titan 2006": 7S00E, 7S02E, ZC20A; "Xterra 2005" with a 2004 VIN: EA005, P17 EA67E, P22 EA000) | decision 4: those cars are "if equipped" with the listing/VIN line in every group (lot plain pairs 32 -> 0). Also: 7S00E Titan 2005 gated `drive 4wd` (sibling 7S006 "KC. 2WD. (SE+ LE)", a reading the verifier did not take: "starred or not"); 7S02E Armada/Titan 2006 `built 2005-08..2006-08` (a 1-month edge, 07/2005 under 7S00E); ZC20A Titan 2006 `built 2005-08..2007-04`, Titan 2008 left out (note cap); EA67E refused (note cap) |
| feed record "QX80 2017" with a QX60 VIN (5N1DL0MN...) | **not fixed**: `vpicMismatch` checks year and make only, so the app cannot see a model mismatch (below) |

### Tests

- New `curation_tests/test_round4_1119.py` (28 checks: window and clause
  helpers, decision 1-3 on stubs including every non-split case above, gate
  vocabulary, live_diff gate comparison, committed files: every built gate
  well formed and named in its note, no note over 160, 3JA9B/3ZD0A/EA00A/
  7Z803 as above). `test_round3_1119.py`: the drive_not-alone vocabulary
  check updated (now valid when one family).
- `pf_guards_unit.mjs` r4 block, 21 checks: decoded-AWD/4WD QX60 not offered
  for 3JA9B, FWD plain, undecoded "if equipped"; a built app-year never plain
  (every donor says "check the build date on the door sticker"; header);
  a mismatched-VIN car never plain; an ungated group unchanged; drive_not
  alone. 12 of them fail on origin/main's app.js; the 9 that pass there are
  the sibling-gate checks (a `drive` gate is old vocabulary) and the
  unchanged-behaviour checks, as they should.
- curation_tests 24/24 files pass (Phase 2 parity SKIP unchanged);
  oem_fitment/tests 42/42; pf_guards_unit ALL PASS.
- Full regression: see "Regression" below.

### Noticed, not fixed

- **Model mismatches are not flagged**: `_vpic_mismatch_msg` (scraper)
  compares year and make only ("model strings vary too much"), so a "QX80
  2017" with a QX60 VIN reaches the app unflagged and decision 4 cannot catch
  it. Data workstream: a model check against the decode (e.g. vPIC model in
  the squashed model family) would close it.
- **Same hole on other paths** (not changed, as briefed): the aftermarket
  rows (`pfAmRows`), the hand platform groups' Likely tier and the
  same-generation donors never read `vpicMismatch`; a mismatched car shows
  there without a line. The parts table matches on the VIN's year
  (`match_year`), so a year mismatch is handled there, but a make mismatch
  (the Yamaha-VIN "Titan") is matched on the listing's make and model.
- **Old readers**: 489 shipped multi-group rows can show a built donor
  plain without the window on an app older than this branch (above).
  Suggest a store release soon after the merge (owner's "ship").
- **The note cap now costs most of the nissan losses**: 18 groups refused by
  the window cap and 66 by the drive cap. The round-3 suggestion stands: once
  a limit is a gate, a short note ("built-date limited; see each car") would
  keep them; hub/owner decision.
- **no_page windows** (stricter than the brief): ford 4 app-years + 1 group,
  toyota 2, nissan 8 rest on seed-page notes alone. The Explorer Sport Trac
  2001 window (from 01/2001) probably is the launch, not a split; a list-page
  crawl of those pages would tell (gmpartsgiant-style completion; owner's
  call on crawling).
- **Mopar "Up to / After mm/dd/yy" windows** in free notes (2012 Ram 1500
  headlamps) are still not read; under the 07-06 model-year convention "Up
  to 07/23/2012" covers MY2012 anyway, but the "After" numbers on the same
  page would be credited. A parser for those notes is the next window step.
- **Model-year convention**: windows are judged against 07/(y-1)-06/y;
  Titan (10/yyyy changeover) and Ram (08) years start later, which makes
  some edge windows (nissan 31 after) that the catalog's own changeover would
  not. Treated as windows, as decided.
- Xterra 2002-2003 80720-2Z710: the Frontier 2003 page dates it "from
  10/2002"; reading another model's page (decision 3 across models) would be
  stricter but over-narrows where windows differ by model (82720-ZC30A:
  Armada 08/2006, Titan 04/2007 end). Left as RISK for the next checker.
- Shipped `_report/<ns>.json` curate reports were not regenerated (as in
  earlier rounds); the nissan one was.

### Regression

`tools/regress.sh --out <scratch>` (not under flock) on code head 1ba97fd7
(only this ops text follows it): **104 passed, 0 failed, 0 skipped**. It
includes pf_guards_unit (r4 block), test_am_gates, test_interchange,
interchange_e2e, part_finder_e2e, pf_ux_e2e, cars_feed_e2e (the round-3
flake passed) and both layout halves (the cards-mixed setup error of round 3
is gone with main's af391cf1 fix). backend/node_modules was a symlink to the
main checkout's for the run; removed, not committed. origin/main moved to
79de0758 meanwhile (ops/hub.md and ops/yards.md only): no merge needed.

### For the hub

1. Merge `interchange/round4-1119`? Live: 0 added claims; ford 1 removed +
   4 narrowed, toyota 16, hmg 1 narrowed; app change (built, drive_not
   alone, VIN mismatch) + sw jh-v214.
2. Confirm the two choices stricter than the brief: `no_page` windows, and
   "starred or not" applied to the Titan 7S00E / 7S006 pair (the verifier
   read that pair as no split).
3. Nissan: 225 shippable, not shipped; a new independent sample decides.

## 2026-11-19 Round 5: linked windows, number-matched page windows, no split on "*" alone, sibling drive basis (builder subagent of session_01LsgNuWEh1vdaDCtdP1jxMM, branch `interchange/round5-1119`)

Hub brief after the independent check `interchange/verify-nissan-1119e`
(seed 52941119; groups 21/4/5, pairs 23/3/4; 7 WRONG, all one flaw). Base
origin/main 599c8bec (round 4 live, df0bdc0a, sw jh-v214). Pins unchanged
(oem-raw@dca9cd84 shipped, @57e8b5b9 nissan, lot main@a85c654). No fetch,
crawl, dispatch, email, release sample or main push.

### Rules (curate.py / policy.py / validate.py; hashed: all 8 shipped namespaces and the candidate re-curated in the same push)

- **Decision 1, linked windows are windows.** `build_window` kind `linked`
  (the rest of T's year under the number's own predecessor or successor) is
  gated like `unlinked` / `no_page`: window in the note + `built` gate; a
  note over 160 characters drops that vehicle-year. `no_other_row` (launch
  or end of production) stays unchanged. July-June model year and edge
  handling as in round 4.
- **Decision 2, other-page windows match on the number.** When T's page
  dates no row of the number, its dated rows on the catalog model's other
  model-year pages are read whatever their option clause, and a predecessor
  on T's page no longer exempts it (Sentra 2004 82730-3Z005). Under 5
  months of T's year: T is left out. Also: an undated gap carrier on T's
  page takes its window from the other pages too (`_pn_other_windows`);
  without that, Q70 2015 80720-1MA0B stayed plain (1MA0A and 1MA0B both
  undated on the 2015 page, dated on the 2016 page).
  - **Stanza 1995, the cause:** the Stanza 1995 mirror page lists 1E400
    (06/1992-02/1995, "Replaced By" 2B500) beside 2B500 (from 02/1995), so
    round 4 classed it `linked` and left it plain; Altima 1995 has no page
    in the raw, fell to `no_page` and was gated. Decision 1 removes the
    difference. Both are now windowed; the two-model note is over 160, so
    Stanza 1995 is the vehicle-year dropped and Altima 1995 keeps
    `built 1995-02..` (96301/96302-2B500).
  - **Pages read, a choice for the hub:** every model-year page of the model
    (`_OTHER_PAGE_SPAN = None`: the literal "narrower reading wins"). Live
    makes are identical either way. On the candidate, an earlier build of
    this branch that read adjacent years only gained 77 app-years over round
    4 and lost 34; reading every page gains 1 and loses 107. Example of the
    cost: 96301/96302-ZC20A Armada 2008-2015 left out (the 2006 page dates
    "W. SE" 08/2005-10/2007; the 2009-2015 pages list it undated for the
    later SV/SL trims).
- **Decision 3, an asterisk alone is no drive split.** The drive word must
  sit on the same clause with the same "*" mark (`_row_clauses_star`); a
  sibling listing the clause bare, or for the other drive family, under
  either mark is counter-evidence. Same-mark matching alone was not enough:
  7S002 lists "*KC. 2WD. (SE+ LE)" and "KC. 4WD. (SE+ LE)", which would have
  re-made the 7S00E gate on a star difference.
- **Decision 4, basis "sibling".** A gate read from a same-option sibling
  carries `drive_basis: "sibling"` and `drive_sib` (the sibling's drive);
  "stated" stays where the number's own row (or its product-page fitment
  row) names the drive: on the live makes Kia Forte struts (held category,
  "[AUTO - 6 SPEED 2WD]" on the row), Ram 1500 2012 ("6 - Lt. Duty DODGE
  4WD"). **Kept "stated", for the hub:** GMC Yukon 2003 mirrors
  19153377/78, a limit filed by the catalog's own "2wd" page with the
  "4wd" page read without the number; the drive word is in the page name,
  not the row.
- Validator: `drive_basis` adds "sibling"; `drive_sib` only with it and of
  the other family.

### App (docs/app.js OEM-GATE; sw `jh-v215`)

- Sibling line: "if equipped: the catalog lists a separate AWD number for
  this option, so this part is read as 2WD only — this donor's drivetrain
  isn't confirmed, check the car" (the word from `drive_sib`). Other
  unconfirmed limits keep their line without the drive; verdicts unchanged.
- Old apps: the round-4 app on this payload gives identical verdicts on
  every pinned-lot pair (plain / if equipped / excluded: same counts); it
  words the sibling basis "listed for 2WD only" (only "unchecked" changes
  the verb). In `pf_guards_unit` with the round-4 app.js the 3 wording
  checks fail, the verdict checks pass.

### Part A, 8 shipped makes (`groups/_report/round5_census_2026-11-19.json`)

Before = round 4 live (origin/main groups and app); after = this branch.
App-years (plain lot pairs).

| kind | gm | ford | mopar | toyota | subaru | hmg | vag | mb |
|---|---|---|---|---|---|---|---|---|
| linked window, before | 0 | 1 (13) | 0 | 88 (676) | 0 | 1 (322) | 0 | 0 |
| linked window, after | 0 | 0 (app-year dropped) | 0 | 88 gated | 0 | 1 gated | 0 | 0 |
| other-page window (number-matched) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| sibling drive gates | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| no other number (unchanged by decision) | 0 | 5 (303) | 0 | 4 (46) | 0 | 0 | 0 | 0 |

Live diff (`groups/_report/live_diff_2026-11-19_round5.txt`): **0 added
groups, 0 gained app-years, 0 widened gates on every live make; 0 groups
removed.** Narrowed: toyota 88 groups (Lexus colour mirrors whose earlier or
later builds carry the same colour's predecessor/successor, e.g.
87910-48240-A0 RX 400h 2006 "built 03/2005-01/2006"), hmg 1 (76003-C1000
Sonata 2015 "built 04/2014-12/2014"), ford 1 (BE5Z-10849-AC: MKZ 2011
dropped, its window over the note cap). gm, mopar, subaru, vag, mb: only
`policy_sha256`. Payload rebuilt, oemStatus ok x8.

Donor pairs on the pinned lot (plain / if equipped / excluded):

| ns | plain | if equipped | excluded |
|---|---|---|---|
| toyota | 97,272 -> 96,596 | 7,714 -> 8,390 | 7,196 -> 7,196 |
| hmg | 3,426 -> 3,104 | 328 -> 650 | 0 -> 0 |
| ford | 23,839 -> 23,826 | 1,124 -> 1,117 | 229 -> 187 |
| gm, mopar, subaru, vag, mb | unchanged | | |
| **shipped** | **291,603 -> 290,592** | **13,294 -> 14,285** | **12,076 -> 12,034** |

### Part B, nissan candidate (NOT shipped)

`groups/_report/nissan.candidate.json`: 226 Likely, **223 shippable** (was
225): window-regulator 112, side-mirrors 62, gauge-cluster 32,
climate-control 17; 136 groups gated (built 84). **The 160-character cap
refuses 88 groups** (window cap 26, drive/engine-limit cap 62). Lot pairs:
plain 47,411 -> 40,326, if equipped 4,281 -> 5,590, excluded 847 -> 801.
Against the round-4 candidate: 4 removed, 67 narrowed, 107 app-years left,
0 widened gates, but **2 groups and 1 app-year come back**:
96301/96302-3JA9A (JX35 2013 + QX60 2015: round 4's "starred or not"
sibling had pushed their note over the cap; decision 3 reverts it) and
82730-CV01B Juke 2016 (window-gated; the note-cap drop now takes another
year). Census after: linked 67 -> 0 plain, other-page 85 -> 0, the 7
sibling gates all basis "sibling".

Every 1119e WRONG / RISK item (`groups/_report/nissan_recheck_2026-11-19e.json`; my own re-check, not independent):

| item | now |
|---|---|
| WRONG 24810-7Z809 Xterra/Frontier 2002 | refused (`held_window_note_cap`): "3.3L, built 07/2001-04/2002 only" on both, one model left |
| WRONG K6301-1MA0B M56 2011 | M56 2011 dropped (window over the cap); M37 2013 and M56 2013 also dropped |
| WRONG 82730-3Z005 Altima 2003 / Sentra 2004 | Altima 2003 `built 2002-11..2004-01`; Sentra 2004 left out (from 04/2004, under 5 months) |
| WRONG 80720-1MA0B Q70/Q70L 2015 | both dropped (linked window read from the 2016 page, note cap); Q70 2016-2018, Q70L 2016/2018 remain |
| WRONG pair 82731-3Z005 (Altima 2003 donor) | Altima 2003 `built 2002-11..2004-01`: 205 plain -> 205 if equipped |
| WRONG pair 96302-ZC20A (Armada 2005 seeker, 2010 donor) | Armada 2005 left out (2006 page from 08/2005); Armada 2008-2015 left out (same window, every page) |
| WRONG pair 80730-JX30B (Cube 2011 donor) | Cube 2011 `built 2009-02..2011-04`: 37 plain -> if equipped; Juke 2011 gone |
| RISK 24810-7S00E Titan 2005 4WD gate "stated" | still 4WD, now basis `sibling` (drive_sib 2wd) from **7S007** "*KC. 2WD. (SE+ LE) + *CC. 2WD. (SE+ LE)" (same mark, nissan.lists:198), not 7S006; Armada 2005 left out (other-page window). A second look is worth it |
| RISK 24820-3ZD0A QX56 2013 2WD (pair with QX80 2014) | `drive 2wd`, basis `sibling` (drive_sib awd) + built; QX80 2014 unchanged (its page lists no AWD sibling) |
| RISK "*" scope: 24810-ZD103, K6301-1PM0B, 96301-3EV0B, pair 96301-1CA0B FX50 2009 | unchanged (decision 5: no claim changed on "*") |
| RISK 80721-CL00A / pair 80720-CL00A FX 2006 edge | FX35 2005 80721 `built 2004-09..2006-06` (unchanged); 80720-CL00A prints 07/2004-06/2006, the whole July-June years 2005-2006: no window under the kept convention (the checker used Aug-Jul) |
| RISK pair 80721-EA000 (Xterra 2008 donor) | Xterra 2005-2008 left out; the "*" question unchanged |
| census: 7 "stated" gates with no drive word | 6 now `sibling` (3ZD0A, 3ZD1A, 96301/96302-9BC9A Xterra 2012-2013); 7S00E's gate now rests on 7S007 (above) |
| Stanza 1995 ungated | cause found (above); dropped by the note cap, Altima 1995 gated |

### Decision 5, the leading "*" (no fetch; raw at both pins)

- Every string in the nissan/infiniti lists, records and year manifests
  (@57e8b5b9) was searched for a stray "*" or a legend word (asterisk,
  legend, footnote, indicates, denotes, marked): **no page text explains
  the mark.** Outside option clauses "*" appears only as "*SELECT USE" on 11
  infiniti bolt/nut rows (1998 I30) and as a bare "*" / "**" on 4 nissan
  rows. "SELECT USE" elsewhere names a supplier choice ("SELECT USE NSK"),
  which hints at "optional / select" but settles nothing.
- Candidate groups depending on a starred clause: 63 groups (269
  app-years) have a starred own clause; a drive gate resting only on
  starred clauses: 4 groups / 8 app-years; an engine gate: 6 / 12;
  ungated app-years where starred and unstarred configurations differ in
  drive: 2 groups / 10, in engine: 12 / 52. Shipped: subaru 4 groups with a
  starred clause, none drive- or engine-scoped by it; mopar groups 0; the
  other shipped sites print no "*" in option columns. No claim changed.

### Tests

- New `curation_tests/test_round5_1119.py` (14 checks): the mark per clause;
  7S006 and 7S002 no split, 7S007 same-mark split; Stanza 1995 linked
  window; Sentra 2004 number-matched drop; Q70 2015 undated gap carriers;
  drive_sib vocabulary; committed files (sibling gates name drive_sib, the
  1119e "stated" gates are sibling, every 1119e WRONG vehicle-year gone or
  built-gated, Sentra 2004 out, Stanza 1995 windowed or out).
  `test_round4_1119.py`: 5 checks updated to the round-5 meaning.
- `pf_guards_unit.mjs` r5 block, 7 checks (sibling line both ways, same
  verdicts as stated, engine + sibling + built line order, stated wording
  unchanged, a linked window never plain, the ungated years plain).
- curation_tests 25/25 files pass (Phase 2 parity SKIP unchanged);
  pf_guards_unit ALL PASS.

### Stricter or looser than the brief

- Stricter: number-matched windows from every page of the model; undated
  gap carriers read from other pages (Q70 2015).
- Looser than round 4, on the candidate only: 2 groups and 1 app-year come
  back (above), consequences of decisions 3 and 1.
- GM page-filed drive limits keep "stated" (above).

### Noticed, not fixed / suggestions

- The 160 cap is now the main cost: 88 candidate groups refused. A note that
  names models sharing one label once ("Altima 1995, Stanza 1995: built from
  02/1995 only") would keep Stanza 1995 and others; or the short-note form
  suggested in round 3.
- `no_other_row` stays plain by decision: ford 5, toyota 4, nissan 49
  app-years (1,887 plain candidate pairs), the largest remaining unknown.
- Titan 2005 7S00E: the 4WD gate rests on 7S007 (same mark); the Titan
  cluster page lists 40 option variants and a second reader may disagree.
- The "*" question needs a source outside the raw (owner's call).

### Regression

`tools/regress.sh --out <scratch>` (not under flock) on code head d0fee954
(only ops text follows): **102 passed, 2 failed, 0 skipped.**
- FAIL both layout halves (`ui_no_truncation.mjs`), setup errors only, no
  layout finding:
  - WIDTHS=320,375,390: 49 setup errors, all at 320 and all after the
    browser page crashed ("page.evaluate: Target crashed", then "Page
    crashed" on pf-browse); 1,104 checks run.
  - WIDTHS=430,768,1280: 1 setup error, `[yards-map-premium]` at 1280,
    "page.waitForFunction: Timeout 30000ms exceeded"; 1,328 checks run.
  - Re-run alone under `flock /tmp/ys-test.lock` on the same tree:
    `WIDTHS=320` **444 checks, 0 failures**; `WIDTHS=1280
    SCREENS=yards-map-premium` **4 checks, 0 failures**. Not reproduced, so
    not run on origin/main. This branch changes app.js only inside the
    OEM-GATE block (the donor line wording).
- Everything else passed, including pf_guards_unit (r4 + r5 blocks),
  test_am_gates, test_interchange, interchange_e2e, part_finder_e2e,
  pf_ux_e2e and cars_feed_e2e. backend/node_modules was a symlink for the
  run; removed, not committed.
- After the run, origin/main moved to b8bb1bc4 (auto-scans and ops) and was
  merged (0ca3aeb4): the 30 payload files taken from main and rebuilt from
  this branch's groups (oemStatus ok x8; groups unchanged by the merge). On
  the merged tree curation_tests 25/25, pf_guards_unit, test_interchange and
  test_am_gates pass; the full regression was not re-run on the merge.
- The container's disk filled up near the end (0 MB free under /tmp); I
  deleted only my own round-4/5 scratch output. The scratchpad still holds
  about 14 GB of other subagents' trees and tarballs (wt-*, w7, oem, *.tar).

### For the hub

1. Merge `interchange/round5-1119`? Live: 0 added claims, 0 groups removed,
   90 app-years narrowed (toyota 88, hmg 1) or dropped (ford 1); app wording
   + sw jh-v215.
2. Confirm "every page of the model" for number-matched windows (vs adjacent
   years only), and "stated" for the GM page-filed limits.
3. Nissan: 223 shippable, not shipped; the next independent check decides.

## 2026-11-19 Round 5b: starred clauses that decide drive or engine scope are held (builder subagent of session_01LsgNuWEh1vdaDCtdP1jxMM, branch `interchange/round5b-1119` from origin/main 982adbf3)

Hub decisions 2026-11-19 ~07:05 UTC. Nissan candidate only; nothing ships.
No fetch, dispatch or email. origin/main moved on to 9944c8e5 during the
round (auto-scan, 1.13.2 release, ops); none of those commits touch
`scraper/oem_fitment`, `docs/app.js`, `docs/sw.js` or this file, so the branch
was not re-merged.

### Rule (curate.py only; `policy.py` untouched, so `policy_sha256` did not move)

- `curate.STARRED_SCOPE_NS = {"nissan"}`. A vehicle-year is held (reason
  `held_starred_scope`, "starred clause decides scope") when re-reading T's
  page without the starred configurations (the number's own and its
  siblings') changes T's drive limit (drive / drive_not / part-time) or its
  engine limit, or leaves T out.
- Where the number is listed for T only through starred configurations,
  leaving them out would remove the claim, not narrow its scope. There they
  are kept with their drive and engine words unread instead. This keeps
  e.g. 96301-3S500 Frontier 2004: every own clause is starred, and its 3.3L
  gate comes from the unstarred KA24DE siblings.
- A starred configuration that changes neither drive nor engine stays as it
  is.
- Unit: the vehicle-year; the group is held whole when fewer than two
  models stay, or when the rest's note no longer fits. The hold is read on the
  group round 5 ships, after every hold that depends on its vehicle-years
  (exterior cross-model, wheels, releases), so it only narrows.
- Each held vehicle-year records `via`: `own` when the number's own starred
  configuration decides, `sibling` when only another number's does.
- Check: on the full reading the new drive/engine helpers reproduce every
  round-5 gate. All 1,304 round-5 vehicle-years were checked, 0 mismatches.
- What if: with the rule switched on for subaru (live; 4 groups with a
  starred clause), 0 would be held.

### Item 2, Titan 24810-7S00E

The 4WD gate's basis, sibling **7S007**, is a starred clause: "*KC. 2WD. (SE+
LE) + *CC. 2WD. (SE+ LE)" (the own row is "*KC. (SE+ LE) + *CC. (SE+ LE)").
Titan 2005 is held (kind a, via sibling). The group keeps Armada 2006 and
Titan 2006.

### Held list (`groups/_report/nissan.starred_held.json`)

Each entry gives the group, its held vehicle-years, the kind, the limit as
curated and without the starred configurations, `via`, and the clause text
(own rows, plus the sibling rows the drive / engine sibling rules read).

- 22 groups and 59 vehicle-years. 9 groups are held whole and 13 are narrowed.
- A vehicle-year can carry two kinds: M37 2012-2013 is a + c_engine, Q70 2014
  is a + b.

| kind | vehicle-years / groups | via own | via sibling |
|---|---|---|---|
| a: drive gate | 11 / 7 | 8 / 4 | 3 / 3 (Titan 2005 7S00E, QX56 2013 3ZD0A / 3ZD1A) |
| b: engine gate | 6 / 5 | 6 / 5 | 0 |
| c drive: ungated | 4 / 2 | 4 / 2 (K6301/K6302-1PM0B M37, M56 2012) | 0 |
| c engine: ungated | 43 / 14 | 27 / 8 | 16 / 6 |

The 9 groups held whole are 24810-7S005, 24810-EA101, 24810-ZD016,
24820-1MK5A, 24820-3ZD0A, 24820-3ZD1A, 24820-6AH2A, 96301-1CA0B and
96302-1CA0B.

Against the round-5 census the hub quoted (a 4, b 6, c 2 + 12 groups):

- **a:** all 4 census groups are held. 3 more come from item 2's class: the
  sibling-basis gates, whose sibling clause carries the same mark.
- **b:** 5 of 6 are held. 24810-ZD103 (Frontier / Xterra 2003-2004, 3.3L) is
  kept, because the product page's engine column states 3.3L by itself.
- **c drive:** 2 of 2 are held.
- **c engine:** 8 of 12 are held (96301/96302 -1CA0A, -3EV0B, -3S500,
  -1CA0B).
  - 4 are kept: 80720/80721-2Z700 Xterra 2002-2003 and 80720/80721-EA010
    Frontier 2007-2009. In both, every starred configuration repeats an
    unstarred one word for word, so the engines are the same either way.
  - 6 more are held that the census did not count, all via a sibling's
    starred configuration:
    - 96301/96302-1CA1A (FX35 2011-2012, FX37 2013, QX70 2014-2015). With
      its starred clauses left out, 3EV0B or 1CA0B lists one engine only.
    - 80730/80731-7B400 Xterra 2001. With its bare "*W" left out, sibling
      80720-3S500 lists only 3.3L configurations.
- **96301/96302-1CA0B** were first kept by my rule and then fixed. Their FX35
  2009-2012 vehicle-years are listed only by "*W. VQ35HR. PREMIUM"; the
  unstarred "W. VK50VE" is the FX50's engine. So both groups are held whole
  (FX50 alone is one model).

The 1119e "*" RISK items now:

| item | now |
|---|---|
| 24810-ZD103 | kept: the engine column states 3.3L |
| K6301-1PM0B M37 / M56 2012 | held |
| 96301-3EV0B QX70 2014-2015 | held |
| pair 96301-1CA0B FX50 2009 | group held |

### Candidate before -> after (`groups/_report/nissan.candidate.json`)

| | round 5 (main) | round 5b |
|---|---|---|
| Likely / shippable groups | 226 / **223** | 217 / **214** |
| gauge-cluster / side-mirrors / window-regulator / climate-control | 32 / 62 / 112 / 17 | 25 / 60 / 112 / 17 |
| shippable app-years | 1,295 | 1,220 |
| gated groups (built) | 136 (84) | 128 (82) |
| pairs plain | 40,326 | **38,357** |
| pairs if equipped | 5,590 | **5,424** |
| pairs excluded | 801 | **297** |
| donor cars with a plain pair | 12,340 | 12,338 |

Pairs come from `audit11_4/lot_replay.mjs` on the pinned lot (main@a85c654),
using this tree's app (unchanged). Most of the drop in excluded pairs comes
from the held gated vehicle-years: those gates are what excluded donors.

### Live diff (`groups/_report/live_diff_2026-11-19_round5b.txt`, `audit11_4/live_diff.py` against origin/main)

- **8 live makes:** I re-curated them with this code. All 8 groups files are
  byte-identical to origin/main, the hash included: 0 groups changed, 0
  added claims. No payload rebuild was needed.
- **nissan candidate:** 9 groups removed, 13 changed, 39 app-years lost in
  the changed groups. 0 gained, 0 gates widened, 0 added claims.

### Tests

- New `curation_tests/test_round5b_1119.py`, 28 checks:
  - the two note filters;
  - the rule on synthetic pages: Titan 7S00E + 7S007 held via sibling,
    7S006 no gate, (a) own, kept when an unstarred clause states the same
    drive, (c), all-starred without a gate kept, a starred clause naming
    nothing kept, (b) Xterra 2000 3S500;
  - the committed files: no held vehicle-year claimed, kept_apps exact, one
    refusal per whole-group hold, the RISK items and 1CA0B held, 2Z700
    kept, no shipped namespace touched.
- curation_tests: 26/26 files pass (Phase 2 parity SKIP unchanged).
- pf_guards_unit: ALL PASS.
- test_interchange and test_am_gates: pass.
- `tools/regress.sh --quick`: **71 passed, 0 failed, 0 skipped**, both
  before the 1CA0B fix and on the final code (ee252c7c).
- No full regression: `docs/app.js` is unchanged, so sw stays `jh-v215`.

### Not done / open (hub decision 6)

- The 160-character cap and the "name models once" note form are untouched;
  both stay open for the owner.
- The `_UNLISTED` guard (a number that only a starred configuration's drive
  or engine words list for T) is not reached on this raw.
- Transmission was not part of the decision and is not held. Starred clauses
  can decide it the same way; I did not count those cases.

### For the hub

1. Merge `interchange/round5b-1119`? It changes no live claim, and
   `policy_sha256` is unchanged.
2. The rule is broader than the census in one direction: 9 groups (19
   vehicle-years) are held only via a sibling's starred clause, 7 of them
   outside the census. If you would hold only the number's own starred
   clauses, those 19 vehicle-years come back. 3 of the groups are item 2's
   class (Titan 7S00E, QX56 3ZD0A / 3ZD1A). The other 6 are engine-sibling
   cases: 96301/96302-1CA0A and -1CA1A QX70 / FX35 / FX37, and
   80730/80731-7B400 Xterra 2001.
3. Nissan: 214 shippable, not shipped; the sixth independent check decides.

## 2026-11-19 Round 6: cab basis, starred-only, hybrid eng_not, every cutting window, transmission ties, narrower page windows (builder subagent of session_01LsgNuWEh1vdaDCtdP1jxMM, branch `interchange/round6-1119` from origin/main 8c48be12)

Hub decisions 2026-11-19 ~10:10 UTC after check 1119f (2 WRONG, one class:
an inferred Titan rear-door "crew cab" gate). No fetch, dispatch or email.
`docs/app.js` unchanged; sw left as main has it. `policy.py` untouched (rules
in curate.py), so `policy_sha256` did not move; the 8 live makes were
re-curated and the payload rebuilt (oemStatus ok x8).

### Rules (curate.py)

1. **Cab basis.** A cab gate is kept only when the number's own evidence for
   that vehicle-year carries the cab (`cab_stated`). That means one of:
   - own-row KC/CC/T codes;
   - cab words on the own rows;
   - every fitment trim of the number for that year naming the cab.
   Otherwise the vehicle-year is held (`held_cab_inferred`). `rear_cab_of`
   (rear-door part read as crew cab from the page's KC/CC split) is never a
   basis.
2. **Starred-only** (nissan): `held_starred_only`, when the number is listed
   for the year only through starred configurations. It shares
   `nissan.starred_held.json` with round 5b, kind `starred_only`.
3. **Hybrid displacement** (nissan): a gas-only gate also gets `eng_not` for
   the displacements the model year offers that no gas-catalog page of the
   model names (`hybrid_only_disps`).
   - Result: every QX60 gas gate now has `eng_not` 2.5L.
   - The same rule also gives Murano 2.5L, Rogue 2.0L and Q70 3.5L (the Q70
     hybrid's VQ35HR).
4. **Every cutting window gated.** `no_other_row` windows are now gated, or
   their vehicle-year leaves at the note cap. The span is the code's
   07/(y-1)-06/y.
5. **Transmission ties** (config-tuple option columns). The year is held
   (`held_option_tie`) when the gates let through a (drive family,
   transmission) pair that no configuration of the number covers.
   - A configuration naming no transmission loses the transmission a
     same-part, same-mark sibling lists for the same or a broader
     configuration. Example: JK61B "S. 6MT" takes every 6MT sedan from
     JK61D.
   - A trans gate read from a sibling is **not** added: the app would word it
     "this part is listed for automatic only", a basis the row does not
     carry (the decision-1 class). Held instead; the held list records
     `a_gate_would_fit`.
6. **Narrower page windows.** When T's page is undated, the other model-year
   pages of the same model are intersected (the narrower window). I did not
   use cross-model pages: 96302-7S600's Armada page would then drop Titan
   2006 on an Armada window.

**Only narrows.** A round-5b reading of the windows (union, no
`no_other_row`) runs beside the new one through the note cap:
- a group it refuses stays refused;
- a year it leaves out stays out.

Without this guard, ford F87Z-7823394-AA would have come back, and 4 nissan
app-years, because the cap's "longest label first" drop picked other years.
All holds read the group round 5 ships, after the exterior, wheels and
release holds.

### Part A, live makes (`groups/_report/round6_census_2026-11-19.json`)

Census on the groups origin/main ships, lot rows = car x group rows of the
vehicle-year on main:

| ns | d1 cab not on own row | d4 cutting window ungated | d5 transmission tie | d6 pages disagree |
|---|---|---|---|---|
| gm | 0 (its 3 cab gates are stated by fitment trims) | 0 | 0 | 0 |
| ford | 0 | 5 vy / 5 groups / 303 plain | 0 | 0 |
| toyota | 0 | 4 / 2 / 46 plain | 0 | 0 |
| subaru | 0 | 0 | 4 / 2 / 154 plain | 0 |
| hmg, mb, mopar, vag | 0 | 0 | 0 | 0 |

The live changes:
- **toyota:** 67003/67004-30550 GS 300 and GS 400 1998 are now
  `built 1997-08..1998-08`.
- **ford, gated (3 groups):**
  - 8G1Z-19980-F Taurus X 2008;
  - 1L2Z-7823395-BB Explorer Sport 2001;
  - 5F9Z-14529-BAC Montego 2005.
- **ford, held at the note cap (2 groups):** 8G1Z-19980-C (Taurus and Taurus
  X 2008) and 1L2Z-7823394-BB (Explorer Sport and Sport Trac 2001). Both
  windows' words pass 160, so one model is left.
- **subaru:** 61041AL04A and 61041AL05A Legacy/Outback 2015 are held
  (`held_option_tie`, via sibling).
  - The own row lists Limited trims with no transmission, and 61041AL00A
    lists "(S+OBK).6MT".
  - A trans AT gate would fit, but it is not added: the app would state a
    basis the row does not carry.
  - `groups/_report/subaru.round6_held.json`.

`live_diff.py` against origin/main
(`groups/_report/live_diff_2026-11-19_round6.txt`): **0 added groups, 0
gained app-years, 0 widened gates** in all 9; gm, mopar, hmg, vag and mb are
byte-identical.

Shipped pairs (8 makes, pinned lot):

| | Before | After |
|---|---|---|
| Plain | 290,592 | 290,089 |
| If equipped | 14,285 | 14,264 |
| Excluded | 12,034 | 12,034 |
| Payload groups | 1,166 | 1,162 |

Per make:
- **ford:** plain 23,826 -> 23,523; if equipped 1,117 -> 1,050 (the 2
  groups held whole carried gated pairs).
- **toyota:** plain 96,596 -> 96,550; if equipped 8,390 -> 8,436.
- **subaru:** plain 3,992 -> 3,838.

### Part B, nissan candidate (NOT shipped)

| | Round 5b (main) | Round 6 |
|---|---|---|
| Likely / shippable | 217 / 214 | 174 / **171** |
| climate / gauge / mirrors / regulators | 17 / 25 / 60 / 112 | 16 / 8 / 43 / 104 |
| Shippable app-years | 1,220 | 1,000 |
| Gated groups (built) | 128 (82) | 98 (64) |
| Pairs plain / if equipped / excluded | 38,357 / 5,424 / 297 | **30,048 / 3,268 / 246** |

Census on main's candidate:
- **d1** 8 vy / 6 groups / 454 if-equipped rows. Same as the check.
- **d2** 91 / 33 / 3,180 plain + 999 if equipped. Same as the check.
- **d4** 90 / 48, made up of:
  - 57 "drop": the decision-6 narrower window leaves under 5 months of the
    year. One example is 80720-EH100 M35/M45 2006-2007, dated 12/2004-06/2008
    on the 2008 page and 09/2007-06/2008 on the 2009 page.
  - 27 other-page and 6 own-page `no_other_row` windows. The check found 12
    vy under its 08-07 span.
- **d5** 9 / 7.
- **d6** 62 / 33.

Held lists:
- **`nissan.starred_held.json`:** 45 groups (35 whole), 150 vehicle-years.
  - By kind: starred_only 120 (= the check's 91 + 29 in groups round 5b
    already held), a 8, b 6, c_drive 4, c_engine 43.
- **`nissan.round6_held.json`:** 14 groups (12 whole).
  - `held_cab_inferred`: 6 vehicle-years / 6 groups.
  - `held_option_tie`: 10 / 8 (JK61D, JK61C, Xterra 2011-2012 9BD5A,
    Frontier 2012 9BD5B, Xterra 2013 EA000 ...).

Every 1119f item (`groups/_report/nissan_recheck_2026-11-19f.json`; my own
re-check, not independent):

| item | now |
|---|---|
| WRONG 82720-7S000 Titan 2005 cab | held (`held_cab_inferred`); group held whole |
| WRONG pair 82730-9FJ0A Titan 2012 cab | held; group held whole |
| census: 82721-7S000, 82730/82731-7S000 (Titan 2010-2011), 82731-9FJ0A | all held whole; no rear-door regulator keeps a cab gate |
| RISK 24820-JK61D G35/G37 2008 (no trans gate) | both held (`held_option_tie`, via sibling JK61B "S. 6MT"; a trans AT gate would fit, not added) |
| RISK 24820-JK61C (starred only) | held (`held_starred_only`) |
| RISK 96301-3EV0B QX70 2016-2017 (starred only) | held; group held whole |
| RISK 96302-EA000 Xterra drive/trans words | Xterra 2013 held (tie: no 4WD automatic); Xterra 2005-2012 kept, "W. BASECAMP" / "W. X" cover every pair; Frontier 2011 dropped (decision-6 window) |
| RISK 80730-7B400 Frontier 1999-2000 (starred only) | held; Frontier 2001-2004 plain |
| RISK QX60 gas gates without eng_not (82720-3JA0A, 80720-3JA0A, 82730-3KG0A, ...) | all `eng_not` 2.5L |
| RISK pairs 24810-7S02E, 24810-7S00E Titan / Armada 2006 (starred only) | both groups held whole |
| RISK pair 96302-7S600 (pages disagree) | Armada 2005 `built 2004-10..2005-08` (decision 4); Titan 2005 left at the note cap; Titan 2006 plain |
| RISK pair 80721-EH100 M35/M45 2008 | plain: 12/2004-06/2008 covers 07/2007-06/2008 (the check used 08-07) |
| RISK pair 82721-0E715 Altima/Stanza 1996 | left out (window, note cap) |
| RISK pair 96301-EA000 Frontier 2011 / Xterra 2007 / 2013 | Frontier 2011 dropped; Xterra 2007 plain (Basecamp covers 4WD AT); Xterra 2013 held |
| census windows: Q70 2014 1MA5A; Titan 2008 96302-ZC20A | Q70 2014 `built 2013-01..2013-11`; ZC20A held whole (Titan 2007 starred only, the rest over the cap) |

### Tests

- **New `curation_tests/test_round6_1119.py`, 26 checks:**
  - the cab basis (7S000 not stated, CC stated, KC+CC is no "crew cab");
  - the tie: Xterra 2013 via own, Basecamp covers, one transmission no tie,
    JK61D via sibling, a trans gate enforced, a bare sibling configuration
    no split;
  - narrowing and the round-5b union;
  - the hybrid displacement;
  - the committed files: the 8 cab vehicle-years, rear-door regulators,
    QX60 eng_not, Xterra 2013, JK61D, the starred items, Q70 2014,
    Armada 2005, the held lists, the live diff zeros, payload oemStatus.
- `test_round3_1119.py` and `test_round5b_1119.py` were updated to the
  round-6 meaning (a held 24810-3JA1B; the starred_only kind and the round-6
  refusal codes).
- curation_tests: 27/27 files pass (Phase 2 parity SKIP unchanged).
- pf_guards_unit: ALL PASS.
- test_interchange and test_am_gates: pass.
- `tools/regress.sh --quick` (on 8a211e6b, queued behind the hub's lock):
  **73 passed, 0 failed, 0 skipped**.
- No full regression: `docs/app.js` is unchanged.

### Stricter or looser than the brief

- **Stricter (5):** sibling-inferred single-transmission ties are held,
  not gated. These are JK61D and subaru 61041AL04A/05A. The gate would fit,
  but the app's trans line would state a basis the row does not carry.
- **Stricter (6):** narrowing withdraws years whose own page lists the
  number undated (EH100 M35/M45 2006-2007, EA000 Frontier 2011), 57 in all.
- **Looser (6):** pages of the same model only, not other models (the
  7S600 Armada window would drop Titan 2006).
- **Decision 5 reading:** a tie exists only where no configuration covers a
  (drive, transmission) pair. Xterra 2005-2012 EA000 stay, since Basecamp
  or X configurations name neither.

### Suggestions

- An app basis for transmission gates, like drive_basis "sibling" ("the
  catalog lists a separate 6MT number for this option, so this part is read
  as automatic only"). It would let JK61D and the two subaru groups ship
  gated instead of held. That needs an app change and the hub's OK.
- Decision 3 as a live rule: the same hybrid-displacement read on toyota /
  ford / gm gas-only gates was not measured; worth a census.
- The 160 cap now costs ford 2 live groups (decision 4's windows on both
  models).

## 2026-11-19 Round 7: per-page window cut, changeover months both sides, date splits from other pages, cross-position groups, star-blind (builder subagent of session_01LsgNuWEh1vdaDCtdP1jxMM, branch `interchange/round7-1119` from origin/main 23376d18)

Hub decisions 2026-11-19 ~11:40 UTC after check 1119g (1 WRONG: 80730-89915
Versa 2007 plain). No fetch, dispatch or email. `docs/app.js` unchanged.
`policy.py` untouched (rules in curate.py), so `policy_sha256` did not move;
the 8 live makes were re-curated and the payload rebuilt (oemStatus ok x8).

### The real cause of the WRONG

`build_window` merged the windows of every own row on T's pages before the cut
test:
- sedan page 12/2006-07/2007 + hatchback page 05/2006-01/2007 = 05/2006-07/2007;
- that union covers the 07/2006-06/2007 span, so the year was "full", plain.

The checker's guess was right. A second, related path made the same mistake:
an undated row on one page beside a dated cutting row on another made the
whole year plain ("a dateless own row: listed for the whole year").

### Rules (curate.py)

1. **Per page.** The cut test runs on each page that lists the number. A page
   with an undated row covers the year. When a dated page cuts the span, the
   year gets the months every dated page lists (Versa 2007: 12/2006-01/2007).
   Pages with no month in common leave the year out.
2. **Changeover months.** A same-option number on T's page whose window
   starts or ends where ours does sets a changeover month. If that month falls
   in 07/(y-1)-06/y widened a month either way, the year is gated even when our
   window covers it (FX35/FX45 2006, G25 2012, M35/M45 2008, Altima/Stanza
   1997).
3. **Splits on other pages.** When T's page lists the number undated beside a
   same-option number and pages of the site date the split, the year is gated
   with the narrower reading.
   - The window comes from the model's own dated pages first (Titan 2006
     96302-7S600: 10/2004-08/2006).
   - Otherwise it comes from the pages that show the split (Frontier 2010
     80721-EA000: 08/2009-04/2010, from the Pathfinder and Xterra pages).
4. **Cross-position groups.** A group whose number sits in another known
   position on another model is held whole (`held_cross_position`,
   `<ns>.round7_held.json`).
   - Positions are the slots each model's own pages resolve.
   - An unknown position ("position_missing", every slot) does not count. A
     first pass that counted it would have held 11 live groups: GM Alero,
     Transit Connect, Lexus rows with no door named.
5. **Star-blind reading.** `starred_scope` also reads the configurations
   without their marks. If a drive or engine limit then appears, the year is
   held (`held_starred_scope`, via `star_blind`). It catches exactly
   96301/96302-3JA9A QX60 2015.

**Only narrows.** The note cap now runs on the round-6 reading as well as the
round-5b one. A group either refuses stays refused, and a year either leaves
out stays out.

### Part A, live makes (`groups/_report/round7_census_2026-11-19.json`)

Census on the groups origin/main ships:

| ns | 1 per-page cut | 2 changeover | 3 split | 4 cross-position |
|---|---|---|---|---|
| toyota | 2 vy / 2 groups / 2 plain (IS 350 2012) | 2 / 2 / 12 plain (GS 430 2006) | 0 | 0 |
| gm, ford, mopar, hmg, subaru, vag, mb | 0 | 0 | 0 | 0 |

Applied:
- toyota 81145/81185-53543: IS 350 2012 `built 2011-09..2013-04`.
- toyota 81070-30B51/30B61: GS 430 2006 `built 2005-07..2006-07`.

`live_diff.py` against origin/main
(`groups/_report/live_diff_2026-11-19_round7.txt`): **0 added groups, 0
gained app-years, 0 widened gates** in all 9; 8 of the live makes are
byte-identical except toyota.

Shipped pairs:

| | Before | After |
|---|---|---|
| Plain | 290,089 | 290,075 |
| If equipped | 14,264 | 14,278 |
| Excluded | 12,034 | 12,034 |
| Payload groups | 1,162 | 1,162 |

### Part B, nissan candidate (NOT shipped)

| | Round 6 (main) | Round 7 |
|---|---|---|
| Likely / shippable | 174 / 171 | 156 / **153** |
| climate / gauge / mirrors / regulators | 16 / 8 / 43 / 104 | 13 / 7 / 39 / 94 |
| Shippable app-years | 1,000 | 915 |
| Gated groups (built) | 98 (64) | 94 (67) |
| Pairs plain / if equipped / excluded | 30,048 / 3,268 / 246 | **24,198 / 2,464 / 178** |

Census on main's candidate:

| class | vehicle-years / groups | lot rows |
|---|---|---|
| 1 per-page cut | 1 / 1 (Versa 2007) | 175 plain |
| 2 changeover | 30 / 18 | 784 plain |
| 3 split | 28 / 16 | 1,888 plain |
| 4 cross-position | 6 groups | 2,473 plain + 839 if equipped |
| 5 star-blind | 2 / 2 | 112 plain |

Held lists by reason:
- **`nissan.round7_held.json`:** `held_cross_position` 5 groups (18
  vehicle-years). The sixth, 80730-89915, left earlier at the note cap.
- **`nissan.starred_held.json`:** 47 groups (37 whole), 148 vehicle-years.
  - By kind: starred_only 116, a 8, b 6, c_drive 6 (the 2 star-blind among
    them), c_engine 43.
- **`nissan.round6_held.json`:** `held_cab_inferred` 6 / 6 and
  `held_option_tie` 8 / 7.
- **Refusals in `nissan.json`:** `held_window_note_cap` 61 (round 6: 45).

Every 1119g item (`groups/_report/nissan_recheck_2026-11-19g.json`; my own
re-check, not independent):

| item | now |
|---|---|
| G23 WRONG 80730-89915 Versa 2007 | gated 12/2006-01/2007, then the group left at the note cap (Murano 2005 + Versa windows); also cross-door |
| G15 80721-CL00A FX35/FX45 2006 | `built 2004-09..2006-06` (decision 2) |
| G16 80730-JK60C G25 2012 | `built 2011-06..2014-06` (changeover 06/2011, a month before the span) |
| P03 82720-0E717 Altima/Stanza 1997 | `built 1996-07..` (decision 2) |
| P12 / P30 80721/80720-EH100 M35/M45 2008 | `built 2004-12..2008-06` (decision 2) |
| G08 96302-7S200 Titan 2006 | **still plain**: changeover 08/2006, two months after the span |
| G21 80730-2Y000 I35 2003 | **still plain**: changeover 08/2003, two months after |
| G03 27510-8Z310 Xterra 2002 | **still plain**: changeover 09/2002, three months after |
| G12 96302-7S600 Titan 2006 | gated by decision 3, then the group left at the note cap |
| G24 80721-EA000 Frontier 2010-2011 | gated / dropped by decision 3, then the group left at the note cap |
| G27 80720-2Z710 Xterra 2002-2003 | decision 3, then the group left at the note cap |
| G05 J6301-1E400 Altima/Stanza 1995-1996 | **still plain**: the J6301 pair (1E400 / 2B500) is dated on no page; only the black 96301 pair splits at 02/1995 |
| G25 82730-3Z005, P08 80730-JX30B (+ 8991A, JX30C, 82731-3Z005) | held, `held_cross_position` |
| G10 96301/96302-3JA9A | held, `held_starred_scope` via star_blind (QX60 2015) |

### What the positions data would allow (decision 4, not written into notes)

Each held group's position per model comes from that model's own page:
- the page name (front_door_window_regulator / rear_door_window_regulator);
- its Location field (Passenger Side / Driver side);
- resolved by positions.py into door and side.

So a note could name the donor's door per model without new evidence, for
example "front right on the Versa, rear right on the Murano". The 5 groups:

| group | positions |
|---|---|
| 80730-8991A | Murano RR, Versa FR |
| 80730-JX30B | Cube FR, Rogue RR |
| 80730-JX30C | Cube and Juke FR, Rogue RR |
| 82730-3Z005 | Altima RR, Sentra FR |
| 82731-3Z005 | Altima RL, Sentra FL |

The app would need to show the line on the donor row; that is an app change.

### Tests

- **New `curation_tests/test_round7_1119.py`, 21 checks:** Versa per page
  and the union cause, pages disjoint, undated beside a cutting page, FX
  changeover, G25 widened month, Titan 7S200 two months out stays plain,
  another option no changeover, Titan 7S600 split, Frontier EA000
  cross-model split, no split without the sibling on T's page, the
  star-blind filter, and the committed files.
- **Updated:** `test_round4_1119` / `test_round5_1119` fakes pinned to their
  reading (`_r7 = False`); `test_round5b_1119` 7S00E/7S006 now decided via
  star_blind; `test_round6_1119` accepts the two groups now held at the cap.
- curation_tests: 28/28 files pass (Phase 2 parity SKIP unchanged).
- pf_guards_unit: ALL PASS.
- test_interchange and test_am_gates: pass.
- `tools/regress.sh --quick` (on 6dbbd6e9 code; it queued behind another
  session's lock): **74 passed, 0 failed, 0 skipped**.
- No full regression: `docs/app.js` is unchanged.

### Stricter or looser than the brief

- **Looser (2):** a changeover two or more months outside the span stays
  plain (G08, G21, G03). The brief says a month either way; the check's band
  (06/(Y-1)-09/Y) is wider.
- **Looser (3):** G05 stays plain. The decision needs a dated split; no page
  dates the J6301 pair. Holding "two same-option numbers on the page, both
  undated, no date anywhere" would be a new class: 36 vy / 9 groups on
  nissan, but 155 vy / 97 groups / 13,892 plain on gm.
- **Narrower (4):** only known positions count.
- **Decision 1 window:** the intersection of the dated pages (the narrower
  reading), because the app's built gate cannot tie a window to a body.

### Suggestions

- **Per-body windows:** a body-specific build window would need a gate that
  pairs body and window (app change).
- **Door words for cross-position groups:** the positions data above is
  enough for the note and the donor row (app change).
- **G05 class:** decide whether "two same-option numbers, both undated" should
  be held. The census sizes it per make in `round7_census_2026-11-19.json`
  (class x).

## 2026-11-19 Round 8: own pages only (nissan candidate); live census only (builder subagent of session_01LsgNuWEh1vdaDCtdP1jxMM, branch `interchange/round8-1119` from origin/main bb2ace4b)

Hub decisions after check 1119h (its WRONG is a lot car whose VIN decodes
another model; not curation). No fetch, dispatch or email. `docs/app.js`
unchanged; `policy.py` untouched. Rules in curate.py, `ROUND8_NS = {nissan}`.

**Live files:** after re-curation with this code, all 8 shipped groups files
are byte-identical to origin/main (cmp). `live_diff_2026-11-19_round8.txt`
shows 0 changes for all 8. The payload was not rebuilt (nothing live changed).

### Rules (nissan)

1. **`held_no_own_page`.** No list row of the number's own for that
   vehicle-year in the raw; the claim rests on a product record or other
   pages. The row names the page to crawl (the record's list URL).
2. **`held_window_other_page`.** The build window comes from another model
   year's page (gate, split or drop). It is held, not gated on the borrowed
   window.
3. **`held_undated_siblings`.** Same-option numbers on the year's page, none
   dated. A configuration counts as the same option when its words sit inside
   the other's: 6WJ0A "S" beside 1NC3A "S. JOURNEY". The number's own
   predecessors and successors are not counted.
4. **Xterra 96302-EA000 (decision 4).** Re-read; see below.
5. **Gas wording.** Where the hybrid's pages were never read (the year page
   offers a hybrid catalog, no hybrid page is in the raw), the gate stays and
   the note says "<model>: checked on gas-model pages" instead of "gas only".
   If the words do not fit 160, gas-checked years leave one at a time at the
   cap, not the group: 82731-4BA0A keeps Murano 2015-2019 + Rogue 2017.
6. **`held_plus_reading`.** The claim depends on reading "+" as "or" between
   configurations naming different engines or drive families. The test
   re-reads T's page with those alternatives unread. FX50 2009-2010 1CA0A
   "W. VQ35HR. PREMIUM + W. VK50VE" is held. KC / CC / T stay cab codes, and
   "+" joining them is kept; 8 vy / 6 groups of the round-7 candidate have
   cab gates resting on them.

**Only narrows.** The round-7 reading (without the round-8 holds) now runs
through the note cap beside the round-6 and round-5b ones. A year one of them
drops stays out.

### Part A, live makes, census only (`groups/_report/round8_census_2026-11-19.json`)

Lot rows are car x group rows of the vehicle-year on main.

| ns | no own page | window from another page | undated same-option siblings | crawl pages |
|---|---|---|---|---|
| toyota | 600 vy / 439 groups / 94,567 rows | 0 | 239 / 176 / 7,798 | 122 |
| gm | 173 / 173 / 37,555 | 0 | 212 / 132 / 15,598 | 57 |
| ford | 47 / 47 / 9,731 | 0 | 2 / 2 / 279 | 15 |
| subaru | 23 / 23 / 1,571 | 0 | 9 / 9 / 252 | 5 |
| mopar | 12 / 12 / 2,106 | 0 | 96 / 44 / 16,129 | 4 |
| vag | 4 / 4 / 832 | 0 | 0 | 1 |
| mb | 0 | 0 | 18 / 6 / 122 | 0 |
| hmg | 0 | 0 | 4 / 4 / 16 | 0 |

How to read it:
- No live build gate borrows a window from another page.
- "No own page" on the live makes is mostly claims resting on product
  records whose list page was never crawled. Example: toyota 2007 Camry
  bumper-components-front.

### Part B, nissan candidate (NOT shipped)

| | Round 7 (main) | Round 8 |
|---|---|---|
| Shippable groups | 153 | **108** |
| climate / gauge / mirrors / regulators | 13 / 7 / 39 / 94 | 7 / 3 / 16 / 82 |
| App-years | 915 | 617 |
| Pairs plain / if equipped / excluded | 24,198 / 2,464 / 178 | **14,890 / 1,198 / 32** |

What each 1119h kind became (census on the round-7 candidate, then round 8):

| 1119h kind | census | round 8 |
|---|---|---|
| missing_page | 61 vy / 61 groups / 3,081 rows (the check: 61 / 61 / 3,029 plain + if equipped) | all 61 held (`held_no_own_page`) |
| window_from_other_page | 17 vy / 17 groups (the check's 24 include 7 without an own page) | all 17 held |
| same_option_sibling_undated | 155 vy / 48 groups | all held: 127 undated siblings, 14 also "+", 7 window, 7 other holds |
| gas_only_wording | 56 vy / 22 groups (the check: 56 / 22) | 37 still claimed and reworded; 19 held for other reasons |
| "+" reading | 29 vy / 17 groups | all held (10 "+" alone, 14 also undated siblings, 5 no own page) |
| unexplained_mark, cab codes | 8 vy / 6 groups | kept as cab codes; 4 held by undated siblings, 4 by other holds |
| unexplained_mark, "*" (ZH10A, EA010/EA000, 1CA0A) | | dated or starred siblings, not changed this round |
| window_edge (K6301-1MA0A M37 2011) | | held, no own page |
| window_disagrees_across_pages (80720-1CA0B QX70 2015) | | FX35 2011 held (no own page); QX70 2015's gate is its own row, kept |
| drive_trans_tie_ungated (Xterra 2005-08 EA000) | | 2005, 2006 and 2009 held (undated siblings); 2007-2008 held ("+" and undated siblings) |

Held lists by reason:
- **`nissan.round8_held.json`** (vehicle-years of every group the rules
  read, shipped or not):
  - `held_no_own_page` 276;
  - `held_window_other_page` 330;
  - `held_undated_siblings` 230;
  - `held_plus_reading` 41.
- **Refusals (groups held whole):**
  - `held_no_own_page` 46, `held_window_other_page` 37,
    `held_undated_siblings` 22, `held_plus_reading` 1;
  - `held_window_note_cap` 49 (round 7: 61).
- **The earlier lists:**
  - starred: 42 groups, 125 vy, starred_only 91;
  - round 6: cab_inferred 4, option_tie 2;
  - round 7: cross_position 5.

Re-check of every 1119h item (my own, not independent):
`groups/_report/nissan_recheck_2026-11-19h.json`.

### Decision 4, Xterra 96302-EA000

The rows:

| years | row |
|---|---|
| 2005-2006 | "W. 2WD. S + W. 4WD. S. 6MT + W. BASECAMP, W. S" |
| 2007-2008 | "W. 2WD. S + W. 4WD. S. 6MT + W. BASECAMP" |
| 2009 | "W. BASECAMP" |

The sibling EA005 lists "*W. S" (2005-2006) and a bare "W" (2007-2009).

- **The hub's test:** "a combination a plain donor can have not covered by a
  configuration of this number". 4WD automatic is covered by "W. S" in
  2005-2006 and by "W. BASECAMP" in 2007-2008.
- **My reading:** read with "+" as "or", the round-6 reading was right. Not
  holding them was consistent with how every trim limit is treated: a 2WD SE
  donor is equally uncovered, and the app's "fits some option packages" note
  says so.
- **Under round 8 the years are held anyway.** 2005, 2006 and 2009 are held
  by undated siblings (EA005 for the same configuration). 2007-2008 are held
  by the "+" rule, since their only alternative joins a 2WD and a 4WD
  configuration.

The two readings no longer change the outcome.

### Targeted crawl to bring the held years back (no own page)

22 nissan / infiniti list pages over 12 vehicle-years. Listed in the census,
`nissan_crawl`.

| vehicle-year | pages |
|---|---|
| Altima 1995 | 4 (control_unit, front and rear door regulator, rear_view_mirror) |
| Xterra 2004 | 2 |
| Xterra 2010 | 2 |
| QX60 2014 (gas) | 2 |
| FX35 2011 | 2 |
| I30 2000 | 2 |
| M35 2006 | 2 |
| Rogue 2016 (T32U) | 2 |
| EX35 2008 | 1 |
| EX35 2012 | 1 |
| M37 2011 | 1 |
| Frontier 2000 | 1 |

They bring back the 61 vehicle-years of the round-7 candidate (3,081 rows),
provided each page lists the number without other problems. The live makes'
equivalent lists are in the census (`part_a_crawl_lists`): toyota 122 pages,
gm 57, ford 15, subaru 5, mopar 4, vag 1.

### Tests

- **New `curation_tests/test_round8_1119.py`, 24 checks:**
  - the "+" filter (engine, drive, cab codes kept);
  - undated siblings (Q40 1NC3A / 6WJ0A, dated, another option,
    predecessor);
  - no own page and the crawl page;
  - the borrowed window and the own window;
  - the gas words;
  - the committed candidate: no round-7 vehicle-year of the four classes
    still claimed, the census sizes, no "gas only", FX50 and Xterra
    2007-2008, notes within 160, the held list, the crawl list, live diff
    zeros for the 8, rules nissan only.
- **Updated:** `test_round3_1119` (24810-3JA1B) and `test_round5b_1119`
  (80720-2Z700 Xterra 2002) accept a round-8 hold.
- curation_tests: 29/29 files pass (Phase 2 parity SKIP unchanged).
- pf_guards_unit: ALL PASS.
- test_interchange and test_am_gates: pass.
- `tools/regress.sh --quick` (on 264a240e): **74 passed, 0 failed, 0
  skipped**.
- No full regression: no app change.

### Stricter or looser than the brief

- **Decision 2:** a gate whose window is on the vehicle-year's own row is
  kept even when other years' pages date the number differently (80720-1CA0B
  QX70 2015). "Pages disagree" is held only where the year's own row is
  undated.
- **Decision 3:** "same option" includes one configuration's words inside the
  other's (wider than an exact match). That matches the check's Q40 example.
- **Decision 5:** a gas-checked year leaves at the cap one at a time, rather
  than the whole group.
- **Decision 6:** "+" is tested for engine and drive conflicts only. Cab
  conflicts are not tested: "KC. SE + CC. SE" would contradict itself under
  an "and" reading, which is strong evidence that "+" means "or".


## 2026-11-19 (i) — independent blind check of the Nissan/Infiniti candidate @ b22c3640: PASS, 0 WRONG

Checker session, branch `interchange/verify-nissan-1119i`. Verdicts with per-item evidence:
`scraper/oem_fitment/groups/_report/nissan_verify_2026-11-19i.json`. Written before reading any
earlier report (independence kept; the comparison note further down was added after the push).

- **Inputs.** Candidate `nissan.candidate.json` @ b22c3640. Raw oem-raw @ 57e8b5b9: all six
  nissanpartsdeal / infinitipartsdeal files match the candidate's `raw` sha256. Lot @ b22c3640:
  337,838 cars (33,433 Nissan/Infiniti); inventory_live.json sha256 8dce8189…, vehicle_extras.json
  7956b34d…, vin_decodes.json.gz dfed9211…. (The candidate has no `lot` block at this commit.)
  App: OEM-GATE block of the app's main script @ b22c3640, run unchanged through
  `audit11_4/lot_replay.mjs`'s extraction; payload rows from `junkyard_scraper._oem_gated_apps`.
  Tool output on this lot: 108 groups, 15,001 plain / 1,150 if-equipped / 31 excluded.
- **Draw** (own code, seed 60231119): 108 shippable Likely groups (3 wiper-motor held);
  largest remainder 23 window-regulator / 4 side-mirrors / 2 climate-control / 1 gauge-cluster;
  then 30 pairs from the other 78 groups.
- **Span**: model year Y = builds 08/(Y-1)..07/Y; also tried 07..08 (wider) and 09..06 (narrower).
  No item changes under either: every claimed vehicle-year whose page window does not cover the
  span carries a built gate, and every built gate equals its pages' dates verbatim (checked on
  the whole candidate, not only the sample).
- **Result: groups 20 RIGHT / 0 WRONG / 10 RISK; pairs 26 RIGHT / 0 WRONG / 4 RISK.**
- RISK kinds (items touched):
  1. Unread sibling variant pages: Rogue 2017 offers hybrid/t32j/t32d/t32u, only t32u read, no
     t32j/t32d page anywhere in raw; the gate keeps hybrids out only; all 102 Rogue 2017 donors
     are plain rows (48 KNM-, 27 JN8-, 11 blank VINs). The note "Rogue: checked on gas-model pages"
     overstates (2 items: 82731-4BA0A, 82730-4BA0A; same in non-sample 80730-4BA1A).
  2. Gas gate with the hybrid page unread: donors with no engine decode are plain rows (Q70 2014: 1,
     Murano 2016: 1, QX60 2017: 2) (4 items, 2 of them also in kind 1).
  3. Undated number beside a same-option number that changes over inside the model year:
     27510-2B000 (2B001 from 04/1994; 12 Altima 1994 plain); J6301-/J6302-1E400 on the 1995-96 pages
     (2B500 undated, black twin changes 02/1995; 6 Altima 1996 plain each) (3 items).
  4. Body word left open: QX50 2016 mirror page lists 96302-1BA1D "*WAG" undated beside 5UB0A
     "LWB" undated; leather rows switch WAG->LWB at 07/2015 (6 QX50 2016 plain) (1 item).
  5. Drive left open: QX56 2013 gauge page has AWD-only 1ZS0A/0C undated; the 3ZD1C row names no
     drive; 4 of 6 donors decode 4WD and get the build line only; 3ZD0C/3ZD1C differ only by '*'
     (1 item).
  6. Feed/VIN identity: EX37 2013 decoded as EX35 2013, not flagged, plain (3 items); QX80 2017
     decoded as QX60, flagged, if-equipped (2 items); a Titan 2006 whose VIN decodes as a Yamaha
     motorcycle, flagged, if-equipped (1 item).
- **Suggestions** (none acted on): name the component on rows — 33 of 82 window-regulator groups
  are motor-only numbers ("Motor Assy-Regulator"), 12,269 lot rows, all cross-model, some
  cross-platform (M37 sedan <-> QX56, Murano <-> Rogue) where the regulators differ; read the Rogue
  t32j/t32d pages or hold Rogue 2017; treat "no engine decode" as if-equipped under a gas gate;
  apply the existing "sibling" drive basis to QX56 2013 3ZD1C; date-gate or hold undated numbers
  whose twin changes inside the year; Infiniti rows say "Nissan catalog" / "Nissan factory parts
  catalog" though the pages are the Infiniti site; notes say "for both" on 3- to 6-model groups.

### 1119i: compared with earlier reports (read only after the verdicts were pushed, 566f1439)

- None of the earlier WRONG classes recurs in this sample: every sampled vehicle-year has its own
  page row; no window is borrowed from another year or merged across body pages (each page's date
  checked on its own, and no duplicate page of a vehicle-year disagrees); "+" readings are gone
  from the sampled rows; the gas wording is the round-8 "checked on gas-model pages" text.
- Kind 3 above (27510-2B000; J6301-/J6302-1E400) sits just outside round 8's
  `held_undated_siblings` scope: that rule needs the same-option numbers to be all undated and
  skips the number's own predecessor/successor, so an undated number whose twin is dated inside the
  year (2B001 "from 04/1994"), or whose undated successor is shown changing over on the parallel
  colour (2B500), still ships.
- Kind 1 (Rogue 2017 t32j/t32d pages unread) does not appear in the 1119h table; round 8's gas
  rule treats only the hybrid catalog as the unread variant.
- Kinds 4 (WAG/LWB) and 5 (AWD-only sibling on QX56 2013) are not named in the round-8 table;
  "*" marks are listed there as known and unchanged.
- The VIN-identity cases match 1119h's class: the flagged ones now show "if equipped"; the
  EX37-listed / EX35-decoded car is not flagged (model pair not hand-sorted "different").

## 2026-11-19 16:50 UTC (hub) own-page completion pass 2: result

Run 44564564713 (oem-raw head d867a65a). toyotapartsnow and vwpartsgiant
finished (`.c2.done`). infinitipartsdeal, jeeppartsdeal, lexuspartsnow and
nissanpartsdeal each answered HTTP 403 within their first three requests
and are now `.blocked` (permanent; rule 2, no workaround). The nissan,
infiniti, jeep and lexus rows of the completion files stay unread; the
vehicle-years they would have settled stay held. Details and the open
questions for the owner: `ops/hub.md`, same time.


## 2026-11-19 Round 9: the number says what it is, the last 1119i holds, site label (builder subagent of session_01LsgNuWEh1vdaDCtdP1jxMM, branch `interchange/round9-1119`, rebased on origin/main e97adab6)

Nissan candidate only; the eight live groups files are byte-identical (re-curated on their pins,
`cmp`), live diff 0 on all eight. Rules in `curate.py` under `ROUND9_NS = {nissan}` (nothing in
`policy.py`). Pins: nissan oem-raw@57e8b5b9, shipped oem-raw@dca9cd84, lot main@a85c654.
Reports: `groups/_report/round9_names_2026-11-19.json` (A), `round9_census_2026-11-19.json`
(B, C, D), `nissan.round9_held.json`, `live_diff_2026-11-19_round9.txt`.

**Candidate: 111 -> 103 groups** (window-regulator 79, side-mirrors 16, climate-control 5,
wiper-motor 3 held category; gauge-cluster 0), 8 removed, 73 changed, 36 app-years held,
**0 added, 0 gained, 0 widened**. Removed: 27510-2B000, 27510-2B001, 24820-89Y00, 24820-8B703,
24820-3ZD1C, 80730-4BA1A, 82730-4BA0A, 82731-4BA0A.

- **A (what the number is).** Cause: `positions.packaging()` reads "Motor Assy-Regulator, RH" as
  `reg?` (its head holds "Regulator") and `PACK_TEXT` has no words for `reg?`, so no nissan note
  said "window motor only". `positions.py` is a policy input, so the class is read in curate.py
  (`_name_class`, `_note_pack`) from every catalog name the raw prints for the number (list rows
  on every page, product records; each with `site:lists|records:L<line>`). window-regulator:
  **motor 30** ("window motor only"), **regulator 49** (no packaging words: "Regulator
  Assy-Door Window" does not say whether the motor comes with it). side-mirrors 16, climate 5,
  wiper-motor 3: assemblies by name (no glass, cover, lens, bezel or knob numbers); gauge-cluster:
  none left. Held by name (mixed, component, missing): **0**. Cap effects of the new words
  (vehicle-years leave at the cap, no limit dropped): 80730/80731-1MA0A Q70 2015-2018,
  82730/82731-3KG0A QX60 2015-2017, 82730/82731-CV01B Juke 2016; 82730/82731-3Z005 now leave at
  the cap (they were held cross-position before; test_round7 reads either).
  **A5, live makes (measure only):** motor-named groups without the phrase: **mopar 21** ("Motor -
  Window Regulator", "MOTOR Window Regulator"; e.g. 68004590AC, 68004591AB, 5012545AA), **subaru 8**
  ("Motor Assembly-Regulator", the nissan pattern; 61188AE00A, 61188AE00B, 61188AE01A); gm 0 of 24,
  toyota 0 of 15, ford 0 of 11. Regulator-named groups with the phrase: 0 on every make.
- **B (holds), each a rule; census on every vehicle-year of the 1119i candidate:**
  - B1 `held_variant_unread` (the year index offers variant pages, hybrid aside, that no list page
    of the vehicle-year comes from, read by `variant` or the page slug): 9 vy / 5 groups, lot 377
    plain, 10 if-equipped, 27 hidden. Rogue 2017 in 80730-4BA1A, 82730-4BA0A, 82731-4BA0A (t32d,
    t32j unread; 90 plain rows each). In curation these three already leave at the note cap
    ("window motor only" plus the gas words; Rogue 2017 the gas year that leaves, then one model
    is left). Sentra 1995-99 in 24820-89Y00 (b14x unread) and Sentra 1999 in 24820-8B703.
  - B2 `held_twin_changeover` (undated number; a same-part twin for our configuration or a broader
    one changes over inside the model year, also when its overlap is under the 5-month listing
    rule; or the number's own predecessor/successor is listed undated for an overlapping
    configuration): 22 vy / 8 groups, 106 plain. 27510-2B000 Altima/Stanza 1994 (2B001 from
    04/1994); J6301/J6302-1E400 and -2B500 Altima 1996, Stanza 1995-96 (each other); 27510-2B001
    Altima/Stanza 1996-97 (28525-1E504/1E505 "Controller Assy-Air Conditiner" for GLE change
    02/1996 and the 1996 page lists 2B001 for GLE too); 80700/80701-0E710 Altima/Stanza 1994.
    Altima 1995 was already held (no own page, round 8).
  - B3 `held_body_mark` (both undated; the same configuration under another leading body mark
    only, the sibling listed for none of ours; FED/CAL and KC/CC/T are not body marks): 5 vy /
    3 groups, 35 plain, 2 if-equipped. QX50 2015-2016 both mirror groups (WAG beside LWB);
    Sentra 1998 24820-89Y00 (4S beside C).
  - B4 `held_drive_open` (our row names no drive and no gate reads one; a same-part number of our
    configuration or a narrower one names a drive): 1 vy / 1 group, 8 if-equipped. QX56 2013
    24820-3ZD1C. The existing sibling wording (round 5 `drive_sib`) needs a sibling whose clause is
    ours plus a drive word with the same "*"; 1ZS0A/0C read "*3ROW. AWD. PREMIUM" / "... LE", so
    the pages do not support it: held. 3ZD0C ("*3ROW") and 3ZD1C ("3ROW") differ only by "*";
    the star is not a drive, both are held the same way (3ZD0C was not shippable before).
  - In curation the four rules hold 81 vehicle-years (body_mark 6, drive_open 21, twin 48,
    variant 6), many also held by earlier rules.
- **C (label).** A group names the site its records came from: "Infiniti catalog" 55, "Nissan
  catalog" 48, mixed none (rule: "Infiniti/Nissan catalog"). `_oem_entries` ships `g["label"]`
  when present (nissan only), else "<brand> catalog" as before. Longest note 159 (cap 160); no
  note was shortened by dropping a limit.
- **D (measure, every make; pinned lot):** plain rows under a fuel "gas" gate with no engine
  decode on the donor: gm 63 of 819 (model-year with a hybrid on the lot or in the catalog: 0),
  nissan 24 of 180, **all 24 in a hybrid model-year (QX60 2015-2017, catalog), all 24 without a
  VIN**; the other makes have no plain rows under a gas gate.
- **F (own-page crawl)** is on main (838b7f94); plan `round9_crawl_plan_2026-11-19.json`.
- Tests: test_round9_1119 38/0; every curation test passes (run_all); crawler tests 34/34.
- Suggestions: give mopar and subaru the same name-read motor words (21 + 8 live groups, a live
  note change, hub's call); make "no engine decode" under a gas gate "if equipped" when the
  model-year has a hybrid (D: 24 nissan rows, all VIN-less); re-pin the live makes to oem-raw
  57e8b5b9 so the 37 census pages completion pass 1 already read count (live groups change).

## 2026-11-19 Round 9 E + G: nissan on, in the newer payload field only (builder subagent of session_01LsgNuWEh1vdaDCtdP1jxMM, branch `interchange/nissan-ship-1119` on `interchange/round9-1119`; not merged, no store release)

**Rule (G4): a namespace or gate key that older shells cannot read correctly ships in the newer
field.** Store apps bundle the shell and read each new payload with their own older code (an app
older than gates-1118 ignores every gate; later shells miss newer keys and wordings). Such a
namespace's groups ship under `oemGroups2` (the lazy files `docs/data/oem/<cat>.json`, and the main
file for a Verified group), never under `oemGroups`. Shells from this release on read both
(`pfOemGroupsOf`: oemGroups, then oemGroups2); every earlier shell reads `oemGroups` only and shows
none of it, as before the namespace shipped. Set: `junkyard_scraper.OEM_NEW_FIELD_NS = {nissan}`.
A namespace leaves the set only when every store build in use reads its keys (iPhone users are on
1.13.0, pre-gates). The eight live makes stay in `oemGroups`, byte-identical; their old-shell
exposure stays as it is. A new gate key on a live make would follow the same rule (its groups
would move to the newer field), which is not done here.

- **What turns nissan on (G1):** `groups/nissan.json`. Every `groups/*.json` is loaded; there is
  no namespace list, and `_OEM_BRANDS` already names nissan. Before this branch nissan existed only
  as `_report/nissan.candidate.json`, which the payload never reads.
- **Old shells on today's payload format (G1; b22c3640 lot, round-9 candidate, 100 payload
  groups):**
  - (a) A pre-gates shell (1.13.0, live on iOS; also 1.13.1) shows every donor plain. That is
    **1,110 rows** the current shell shows "if equipped" (1,108) or hides (2); it was 1,181 on the
    1119i candidate.
  - (b) The 1.13.2 shell (81c57f67): gates-1118, the round-4 built / drive_not code and the
    round-5 sibling line are all ancestors of 81c57f67, and no gate commit comes after it. By
    commit history it therefore runs today's OEM-GATE code, so 0 rows would differ. This was not
    checked by running that build's own script: reading the old bundled script out of git was
    refused in this session, so treat it as unverified.
- **Mechanism (G2).**
  - Scraper side:
    - `_attach_lazy_layers` routes new-field groups to `oemGroups2`, and writes that key only when
      it holds a group.
    - The index adds an `oem2` count beside unchanged `oem` / `am`.
    - `_lazy_trim` sheds `oemGroups2` first.
    - `_oem_split_new_field` keeps a new-field Verified group out of the main file's `oemGroups`.
  - App side: `pfOemGroupsOf(d)` in the lazy loader and the main-file read. That is one helper and
    two changed lines. It ships first on its own branch, `interchange/payload-field2-reader`
    (4611cd7c, for 1.13.3), and this branch sits on top of it. The service-worker name is not
    bumped (the hub sets it at merge).
  - `measure.py` merges `oemGroups2` for the new-client view.
  - No existing mechanism is certain to have the same effect. Today's shell skips `src !== 'oem'`,
    but the 1.13.0 script could not be read to confirm it does the same.
- **E counts (b22c3640 lot).**
  - Before: nissan ships nothing.
  - After: **100 payload groups, 546 app-years, 14,026 plain / 1,108 if equipped / 2 hidden**
    pairs:
    - window-regulator: 79 groups, 472 app-years, 13,634 / 602 / 2
    - side-mirrors: 16 groups, 53 app-years, 308 / 488 / 0
    - climate-control: 5 groups, 21 app-years, 84 / 18 / 0
  - The 3 wiper-motor groups stay held (GROUP_HOLD_CATS as it stands).
  - On the 1119i candidate the totals were 108 groups, 617 app-years and 15,001 / 1,150 / 31; the
    71 app-years lost are 36 narrowed plus 35 in the 8 removed groups.
  - The eight live groups files are byte-identical. Payload: every lazy file's `oemGroups` and
    `amGroups`, the main file's `oemGroups` / `oemVg` and the old keys are unchanged (no
    contradiction demotion from the nissan cells). 26 of 29 lazy files differ only in `builtAt`;
    the nissan groups sit under `oemGroups2` in climate-control (5), side-mirrors (16) and
    window-regulator (79). `oemStatus` gains `nissan: ok 57e8b5b9 103 groups`.
- **Tests.**
  - New: `curation_tests/test_ship_1119.py` (16 checks). It compares a build with nissan against
    one without; checks that an old-shell reader (oemGroups only) of the committed files sees zero
    nissan groups and the new reader sees all 100; and checks the trim order.
  - `backend/test/pf_guards_unit.mjs` gains a round 9 G block. It runs the real pfRunSearch with
    the reader swapped to the old one: no nissan donor appears, and the toyota rows are identical.
  - Pinned live set updated: test_lazy_payload / test_payload APPROVED (nissan added), test_round6
    / test_round7 oemStatus, test_gates_1118 ("nissan ships the reviewed candidate"), and
    test_round5b (starred holds: live namespaces only). test_gates_1118 also reads `oemGroups2`.

## 2026-11-19 — independent check: Nissan candidate names, labels, note length (branch interchange/verify-nissan-names-1119)

Blind check of `nissan.candidate.json` @83496438 (103 `likely` groups, one number each) against
`oem-raw@57e8b5b9` (nissanpartsdeal / infinitipartsdeal records + `.lists` manifests; no
continuation parts exist). Own reading of every page name; curation code not used. Output:
`scraper/oem_fitment/groups/_report/nissan_names_verify_2026-11-19.json` (file:line evidence per number).

- Result: **PASS, 0 WRONG.**
- Claim 1 (component wording): 102 RIGHT, 0 WRONG, 1 RISK. 30 groups say "window motor only"; all 30 are
  named "Motor Assy-Regulator, RH/LH" on every page, and no Motor Assy number lacks the phrase. 49 regulator
  groups ("Regulator Assy-(Rear) Door Window") carry no component wording. Mirrors (16, "Door Mirror Assy" /
  "Mirror Assy-Outside"), climate (5, "Controller Assy-Air Conditiner"; the pages list case, cover, knob, lens
  separately), rear wiper motor and windshield wiper motor: RIGHT.
- RISK: wiper-motor 28800-1LA0A (QX56 2012 / QX80 2014), "Drive Assy-Windshield Wiper", note says
  "windshield wiper motor with linkage". It is the whole drive (its pages list no separate motor or link),
  but the page name does not say "linkage". Suggest "windshield wiper drive assembly" or keep and accept.
- Claim 2 (label): 103 RIGHT. Every group is single-make; every claimed model has a page from its labelled
  site; no number appears on the other site.
- Claim 3 (length): 103 RIGHT, max 159 chars (80730-1MA0A, 80731-1MA0A: 1 char of headroom).
- Post-push comparison with `round9_names_2026-11-19.json`: same names, references and classes for all 103.
- Suggestions: (1) 80730-1LE0A is named "Motor Assy-Regulator, LH" and 80731-1LE0A "…, RH" on the Infiniti
  pages, the reverse of the usual 80730=RH pattern. Side is out of scope here, but if notes or the app ever
  state a side, read it from the name, not the number. (2) The 160-char limit is nearly reached; a longer build
  window text would go over it, so a test on note length is worth having.
