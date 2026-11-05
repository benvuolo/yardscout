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
    Nissan, Infiniti
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
