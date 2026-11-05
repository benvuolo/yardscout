# Parts workstream — status (updated 2026-11-05, §13–21 done)

Owns: parts entries and gap curation in `scraper/junkyard_scraper.py`
(`_GAP_MECH`, `_gap_rows`, `_GAP_GENERIC_KEYS`, per-model blocks),
`scraper/parts_overlay.json`, `scraper/PARTS_GAPS_2026-11.md`,
`scraper/test_parts_gaps.py`.

## Rules specific to this work

- Every row has a basis: pull cost = median of the category across the 30
  published yard price lists; band = conservative used-OEM anchor consistent
  with audited rows of the same category. Write the basis in PARTS_GAPS.
- Options are `option`-flagged. Coupe/hatch rows use `body`, AWD rows `drive`.
- No engines, transmissions, catalytic converters, key fobs, ignition coils.
- Generation-split models (Civic, Cherokee) replace the base entry: add rows
  after the split, on the generation entries.
- Match lists that share a dict must list every spelling (the "grand
  caravan" lesson: 3,240 cars went dark when one spelling was dropped).
- Run `python3 scraper/test_parts_gaps.py` and `test_vpic_fixes.py` after
  each change. Measure with `scraper/interchange_coverage.py` (cars with no
  entry; cars matching only generic rows).

## Done

- §1–10: Altima, Camry, Civic, Focus, Malibu, Escape, Equinox, Sentra,
  Corolla, Elantra (model-specific rows).
- §11 breadth: 101 mid-volume models get generic rows; feed spellings routed
  (Ram, C/K, Caravan, Malibu/Classic). No-entry share 8.9% → 3.7%.
- §12 enthusiast audit: WRX/Impreza, Miata, 4Runner, Tacoma, Cherokee XJ.
- Overlay merge is window-aware (same name skipped only when years overlap).
- §13 measured block (2026-11-04, PARTS_GAPS §13): Camry 1992–2001, Accent
  2000–17, LeSabre 1992–2005, LaCrosse 2005–16, Corolla 1993–2002, Soul
  2010–19, done in measured order. Generic-only cars 43,010 (12.9%) →
  35,451 (10.6%); no-entry unchanged 12,298 (3.7%). New rows are bounded
  per generation with `_per_gen` (the splitter skips pump/compressor/motor
  names). Rows without a stated basis were left out and listed per model.
- §14 (owner go-ahead): the 56 §1–12 gap-block rows whose "fits" crossed a
  generation (pump, compressor, fan, throttle body, sunroof, AWD units,
  crossbars, Focus/Equinox mirrors, Malibu BCM) are split per generation by
  `_bound_gap_rows_per_generation` (153 rows). Every car's matched parts
  are unchanged; coverage unchanged (3.7% / 10.6%). Test guards it.
- §15 (owner: "go on the 776 rows"): every remaining crossing row on a
  GENERATION_BREAKS model is split per generation by
  `_bound_rows_per_generation`, which runs after `_apply_platform_families`
  (running it earlier dropped interchange notes). 776 → 2,346 rows; per-car
  parts, bands and sharedWith identical; coverage unchanged. Test asserts
  no row on any GENERATION_BREAKS model crosses a break.

- §16 (owner: "start the next parts block"): Focus 2000–07, Explorer
  1991–2001, Compass 2007–16, Rio 2001–17, Century 1986–2005, Aveo 2004–11
  (new GENERATION_BREAKS 2007/2009), Passat 1998–2011, Lucerne 2006–11, done
  in measured order. Generic-only 35,451 (10.6%) → 28,433 (8.5%); no-entry
  unchanged 12,298 (3.7%). No car lost or changed an existing part.

- §17 (owner: "go on facelifts"): `FACELIFT_BREAKS` for 24 high-volume
  models, each year cited in PARTS_GAPS §17. Appearance rows (lamps, grille,
  bumpers, fog/marker lights) are cut at those years: 75 → 152 rows.
  Per-car parts, bands and interchange notes are identical; coverage
  unchanged. A test guards it.

- §18 (owner: "start the next parts block"): Forte 2010–13, Regal
  1997–2004/2011–17, Tucson 2005–21, Sportage 2005–22, Spectra
  2000–03/2005–09, Legacy 1995–2004/2010–14, MKZ 2007–20, Elantra 2001–06,
  in measured order. Generations and facelifts were researched with cited
  sources first. Generic-only 28,344 (8.5%) → 24,111 (7.3%). New breaks:
  MKZ generation 2013; facelifts for Regal, Tucson, Sportage, Spectra,
  Legacy, MKZ, Elantra 2004. No car lost or changed an existing part.

- §19 (owner: "start the next parts block"): Galant 1999–2012, Grand Am
  1996–2005, Sorento 2003–09, Santa Fe 2001–06, MKX 2007–18, Five Hundred
  2005–07, Optima 2001–05/2007–10, CC 2009–17, in measured order, each
  researched with cited sources first. Generic-only 24,111 (7.3%) → 20,699
  (6.2%). New breaks: MKX generation 2016; facelifts for Galant, Sorento,
  Santa Fe, MKX, Optima, CC. No car lost or changed an existing part.
- Breadth-pass entries (mkz, mkx, volkswagen cc …) are created after the
  §16–19 blocks; their rows go just before `_apply_consensus_evergreens()`.

- §20 (owner: "start the next parts block"): Malibu 1997–2003, Tribute
  2001–11, Uplander 2005–09, Mazda5, Lexus ES 1992–2006, Aura (overlay),
  Windstar, Savana, researched with cited sources first. Generic-only
  20,699 (6.2%) → 17,792 (5.4%). New breaks: Mazda5 2012 and Windstar 1999
  generations; facelifts for Malibu 2000, Tribute, Mazda5, ES, Windstar,
  Savana. Fixed the Chevrolet Classic routing (own N-body entry). No car
  lost or changed an existing part.
- Overlay-created entries (Aura, es 300 …) take their rows in
  `parts_overlay.json`; §20 code sits just before
  `_apply_consensus_evergreens()` so breadth-pass entries exist.

- §21 (owner: "start the next parts block"): Mariner, Fiat 500, Spark,
  Juke, Sable, Stratus, Mustang S197, Transit Connect, researched with cited
  sources first. Same-inventory generic-only 17,864 (5.4%) → 15,325 (4.6%).
  New breaks: Mariner 2008, Spark 2016, Stratus 2001 generations;
  facelifts for Spark, Juke, Sable, Stratus, Mustang 2013, Transit Connect.
  Fixed routing: Fiat 500L/500X get their own evergreen-only entries; the
  500e and Spark EV get empty entries (no gas-car rows on EVs). Stratus
  2001–05 rows are sedan-gated (the coupe is a different car).
- Empty entries are a supported "suppressor": the specificity guard drops
  the broader keyword, and an entry with no rows produces no card.
- Measuring across a mid-block scan: compare HEAD and working tree on the
  same inventory (a measure script that takes the scraper path).

- §23 (owner: "go on facelifts"; facelift follow-ups, PARTS_GAPS §23):
  23.1 Grand Caravan 1999/2005/2011, Odyssey 2002/2008/2014/2021,
  Expedition 1999/2015/2022, Town & Country 2005/2011, each year cited.
  Per car: only `fits` narrowed (1,027 Expedition cars); coverage unchanged.

## How to measure

`interchange_coverage.py` measures engine-family donors, not generic-only.
The generic-only count re-matches every distinct year/make/model in
`docs/data/inventory_live.json` with `js.match_vehicle` and applies
`mine_coverage_gaps.is_generic_only` (≈15 s). The miner is offline-only now
(no eBay page fetching).

## Open for the owner

- Models without GENERATION_BREAKS entries keep whole-entry spans; adding
  breaks for more models would let the §15 pass bound them too.
- `mine_coverage_gaps.py`: the eBay page fetcher is removed (2026-11-04);
  the script is offline-only. `--no-fetch` and `--categories` are still
  accepted as no-ops so `coverage-mine.yml` keeps working. The gap ranking
  and JSON output are identical to the old `--no-fetch` run. Hub: the
  workflow's `pip install requests beautifulsoup4` step is no longer needed
  (workflow file not touched here).

## Next

1. Next block by generic-only cars: Mercury Milan (Fusion twin) (311), Buick Encore (307), Chevrolet Captiva Sport (301), Buick Park Avenue (299), Scion xB (2nd gen) (293), Hyundai Sonata (290), Infiniti QX60 (288), Ford Escort (285).
   Research generations and facelifts with sources first. The Fiat 500L
   (2014–20) and 500X (2016–23) now have evergreen-only entries; they need
   their own lamp/mechanical research.
2. Follow-up: "ES 300"/"ES 330" listings match both `lexus es` and the
   overlay `es 300` entry (two "Lexus ES" cards). Merge the overlay rows
   into `lexus es` and drop the duplicate (§20.5).
3. Facelifts (§23, in progress): 23.1 done (Grand Caravan, Odyssey,
   Expedition, Town & Country). Next: Silverado/Sierra, Ram, BMW 3, Maxima;
   then Ranger, Suburban, Traverse, Pathfinder; then TrailBlazer, Pilot,
   Tahoe/Yukon, Liberty, Edge, Charger, Dakota, Grand Cherokee. The rule: a
   cited source for every year, and models without one are left out.
4. When the daily email's "Most searched parts / cars (7 d)" has a week of
   data, let it reorder the list. Re-measure after each model.
