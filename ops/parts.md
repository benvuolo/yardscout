# Parts workstream — status (updated 2026-11-05, §13–22 done; §23 facelifts and §23.6 routing in a second session)

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
  23.2 Silverado/Sierra 2003/2016/2022, Ram 1500 and HD 2006/2013, BMW 3
  2002/2004/2009/2011/2016/2023 (sedan and coupe LCIs), Maxima
  1997/2002/2007/2012/2019. Per car: only `fits` narrowed (1,027 + 7,537
  cars); coverage unchanged. Tail-only revisions (Ram 2007) are not cuts.
  Found, not fixed: Dodge "Ram Van"/"Ram Wagon" listings match the Ram
  pickup entry (PARTS_GAPS §23.2).
  23.3 Ranger 1989/2001/2006, Traverse 2013/2022, Pathfinder 2002/2008/2017
  (1,665 cars narrowed). Suburban: no confirmed year, left out.
  Single-component years (grille-only, tail-only) are not cuts.
  23.4 TrailBlazer 2006/2024, Pilot 2006/2012/2019, Liberty 2005 (3,544
  cars narrowed). Tahoe and Yukon: no line-wide year confirmed, left out.
  23.5 Edge 2011/2019, Charger 2015, Dakota 1991/2008, Grand Cherokee
  1996/2004/2008/2014/2017 (120 cars narrowed). §23 total: 21 keys, 13,893
  cars with a narrowed lamp window, no other per-car change, coverage
  unchanged.

- §22 (owner via hub: "Ensure everything is at speed"): Milan, Encore,
  Captiva Sport, Park Avenue, Scion xB 2nd gen, Sonata EF, JX35/QX60, Escort,
  researched with cited sources first. Same-inventory generic-only 15,399
  (4.6%) → 13,030 (3.9%); no entry 12,409 → 12,375. New breaks: Park Avenue
  and Escort generations 1997; appearance cuts for Milan, Encore, Park
  Avenue, xB, Sonata 2002, QX60, Escort. Routing: Encore GX own entry;
  Captiva, JX and ZX2 listings now match (ZX2 has its own entry).
- §22.10 hybrid gate (owner go 14:28): alternator, starter and belt A/C
  rows dropped on hybrid listings (86 combos, 0 gas cars changed). Cited
  exceptions: Civic/Accord Hybrid and Vue Hybrid keep the starter; gm-gen4-truck still
  catches Yukon/Escalade Hybrid (reported to the hub Phase 0).

- §23.6 (hub, accuracy fix, rule 3; PARTS_GAPS §23.6): routing.
  Ram Van / Ram Wagon / B-vans get their own 1994–97 / 1998–2003 entries
  (no pickup rows; lamps, mirrors, fuel pump, A/C option, evergreens with
  power windows option); Ram C/V (cargo Grand Caravan) off the pickup
  entry (evergreens only). Silverado/Sierra 2500/3500/HD get per-HD-
  generation entries (1999–2000, 2001–06, 2007–14, 2015–19, 2020–24):
  evergreens plus headlights only where a GM part number lists the HD
  (GMT800 2003–06, Sierra 2001–06, GMT900 2007–14). 2007 Classic → GMT800
  rows. `gm-gen3-truck`/`gm-gen4-truck` apps and verified groups use
  explicit light-duty spellings (no `Silverado*`/`Sierra*` prefix).
  1,140 cars changed, all 1500s unchanged. Generic-only 13,893 (4.2%) →
  14,634 (4.4%) after §22.1–22.5 (HD/C/V now show generic rows instead
  of unsupported 1500/pickup rows); no entry 12,396 → 12,358. Open: HD tailgate / tow
  mirror / K2XX–T1XX HD rows need part-number bases; plain "Silverado" /
  "Sierra" listings can be unnamed HDs (528 cars, unchanged).

## For the parts session: 41 hand vg groups to re-check (from interchange, 2026-11-05)

Hub decision: nothing is hand-withdrawn. CURATION_SPEC §7.6 already withholds
these groups automatically from the payload once their cells are OEM-closed
(R1/R2 manifests); today no cell is closed, so nothing changes in the app.
Please re-check each against its stated basis (`scraper/PARTS_GAPS_2026-11.md`,
ENGINE_FAMILIES evidence) and decide whether the hand group itself should be
narrowed. The interchange session does not edit the parts table.

Source: toyota + mopar curation on oem-raw@50ac4a48 with every cell assumed
closed (hypothetical, never shipped), `_oem_contradictions` on main's hand
payload (467 hand vg groups; the hub run counted 468). Reproduced
2026-11-05 by the interchange session: 41 vg groups, 0 platform groups.
The last column counts member cells by the real split the OEM catalog prints
there (option_split = two or more numbers for the family's own engine, e.g.
4Runner/Tacoma 1996 alternators 27060-62180 and 27060-75170, both listing 2.7
and 3.4; conditional:trim/engine/plant/production = a printed condition).
Evidence gaps are not counted. Totals: option_split 240, conditional:trim 44,
conditional:engine 5, conditional:plant 1, conditional:production 1.

| group | apps | split cells |
|---|---|---|
| `mopar-pentastar/alternator#0` | Dodge Grand Caravan 2011-2020; Chrysler Town & Country 2011-2016; Chrysler Town And Country 2011-2016; Dodge Journey 2011-2019; Dodge Avenger 2011-2014; Chrysler 200 2011-2014 | option_split 13 |
| `mopar-pentastar/starter#0` | Dodge Avenger 2011-2014; Dodge Journey 2011-2014 | option_split 3 |
| `mopar-world24/alternator#0` | Chrysler Sebring 2007-2010; Chrysler 200 2011-2013; Dodge Avenger 2008-2013; Dodge Caliber 2007-2012; Jeep Compass 2007-2017; Jeep Patriot 2007-2017 | option_split 38 |
| `mopar-world24/starter#0` | Dodge Caliber 2007-2011; Jeep Compass 2008-2011; Jeep Compass 2015-2015; Jeep Patriot 2008-2011; Jeep Patriot 2015-2015; Chrysler Sebring 2007-2010; Dodge Avenger 2008-2010; Dodge Journey 2009-2010; Dodge Journey 2015-2015 | conditional:trim 3, option_split 8 |
| `mopar-47/alternator#0` | Dodge Durango 2001-2007; Jeep Grand Cherokee 2005-2006; Jeep Commander 2006-2009 | conditional:engine 4, conditional:trim 1, option_split 2 |
| `mopar-47/alternator#1` | Dodge\|Ram Ram* 2002-2008 | conditional:trim 4, option_split 2 |
| `mopar-37/alternator#0` | Jeep Liberty 2002-2005; Jeep Grand Cherokee 2005-2006; Jeep Commander 2006-2010 | conditional:trim 1, option_split 7 |
| `mopar-37/alternator#1` | Dodge\|Ram Ram* 2002-2008 | conditional:trim 4, option_split 2 |
| `jeep-40/alternator#0` | Jeep Cherokee 1991-1998; Jeep Comanche 1991-1992; Jeep Wrangler 1991-1998; Jeep Grand Cherokee 1993-1998 | conditional:engine 1, conditional:trim 15, option_split 7 |
| `jeep-40/alternator#1` | Jeep Wrangler 2001-2006 | conditional:trim 2 |
| `jeep-kl-24/alternator#0` | Jeep Cherokee 2014-2019; Jeep Cherokee Kl 2014-2019 | option_split 5 |
| `jeep-kl-24/starter#0` | Jeep Cherokee 2014-2018; Jeep Cherokee Kl 2014-2018 | conditional:trim 1, option_split 4 |
| `jeep-kl-32/alternator#0` | Jeep Cherokee 2014-2014; Jeep Cherokee 2017-2019; Jeep Cherokee Kl 2014-2014; Jeep Cherokee Kl 2017-2019 | option_split 4 |
| `mopar-magnum/alternator#0` | Dodge\|Ram Ram* 1994-1998; Dodge Dakota 1992-1998; Dodge Durango 1998-1998; Jeep Grand Cherokee 1993-1998 | conditional:trim 4 |
| `toyota-rz/alternator#0` | Toyota Tacoma 1995-1996; Toyota T100 1994-1996 | option_split 1 |
| `toyota-rz/alternator#1` | Toyota Tacoma 1997-1999; Toyota T100 1997-1998; Toyota 4Runner 1996-1999 | option_split 5 |
| `toyota-5vz/alternator#0` | Toyota Tacoma 1995-1996; Toyota Tacoma 1998-1999; Toyota T100 1995-1998; Toyota 4Runner 1998-1998; Toyota Tundra 2000-2000 | option_split 4 |
| `toyota-5vz/alternator#1` | Toyota 4Runner 1996-1998; Toyota T100 1997-1998; Toyota Tacoma 1997-1999; Toyota Tundra 2000-2002 | option_split 8 |
| `toyota-5vz/alternator#2` | Toyota 4Runner 1999-2002; Toyota Tacoma 2000-2004; Toyota Tundra 2000-2002 | option_split 3 |
| `toyota-5vz/alternator#3` | Toyota Tundra 2003-2004 | option_split 2 |
| `toyota-5s/alternator#0` | Toyota Camry 1997-2001; Toyota Solara 1999-2001; Toyota Camry Solara 1999-2001 | option_split 8 |
| `toyota-1mz/alternator#0` | Toyota Camry 1997-2001; Lexus ES 300 1997-2001 | option_split 5 |
| `toyota-3mz/alternator#0` | Lexus ES 330 2004-2006; Lexus RX 330 2004-2006; Toyota Camry 2004-2004; Toyota Highlander 2004-2007 | option_split 5 |
| `toyota-3mz/alternator#1` | Lexus RX 330 2004-2006; Toyota Sienna 2004-2006 | option_split 3 |
| `toyota-2gr/alternator#0` | Toyota Camry 2007-2017; Toyota Avalon 2005-2018; Toyota Highlander 2008-2013; Toyota RAV4 2009-2010; Toyota Venza 2009-2015; Lexus ES 350 2007-2018; Lexus RX 350 2007-2009 | option_split 26 |
| `toyota-2az/alternator#0` | Toyota Camry 2004-2006; Toyota Highlander 2004-2007; Toyota RAV4 2004-2005; Toyota Solara 2004-2008; Toyota Camry Solara 2004-2008; Scion tC 2005-2010; Toyota Scion tC 2005-2010 | option_split 15 |
| `toyota-2az/alternator#1` | Toyota Camry 2007-2009; Toyota Matrix 2009-2013; Toyota Corolla 2009-2010 | conditional:plant 1, option_split 4 |
| `toyota-2az/starter#0` | Toyota RAV4 2004-2005 | option_split 2 |
| `toyota-2az/starter#1` | Toyota RAV4 2006-2008 | conditional:trim 2, option_split 1 |
| `toyota-2ar/alternator#0` | Scion tC 2011-2016; Toyota Scion tC 2011-2016; Toyota Camry 2012-2015; Toyota RAV4 2009-2012 | conditional:trim 6, option_split 4 |
| `toyota-1zz/alternator#0` | Toyota Corolla 2003-2008; Toyota Matrix 2003-2008; Pontiac Vibe 2003-2008; Toyota Celica 2000-2005; Toyota MR2 Spyder 2000-2005 | option_split 17 |
| `toyota-2zr/alternator#0` | Scion xD 2008-2009; Toyota Scion xD 2008-2009; Toyota Corolla 2009-2009 | option_split 1 |
| `toyota-2uz/alternator#0` | Toyota Tundra 2003-2009; Toyota Sequoia 2003-2009 | option_split 12 |
| `toyota-1gr/alternator#0` | Toyota Tacoma 2005-2015; Toyota 4Runner 2003-2009; Toyota FJ Cruiser 2007-2010; Toyota Tundra 2006-2010 | option_split 8 |
| `toyota-4a/alternator#0` | Toyota Corolla 1993-1997 | option_split 5 |
| `toyota-4a/starter#2` | Toyota Corolla 1997-1997 | option_split 1 |
| `toyota-3s/alternator#1` | Toyota Celica 1987-1987 | conditional:trim 1 |
| `toyota-1nz/alternator#3` | Scion xB 2004-2006; Toyota Scion xB 2004-2006 | option_split 3 |
| `toyota-1nz/alternator#4` | Scion xA 2005-2006; Toyota Scion xA 2005-2006 | conditional:production 1 |
| `toyota-rav4-1/alternator#0` | Toyota RAV4 1996-1997 | option_split 1 |
| `toyota-rav4-1/alternator#1` | Toyota RAV4 1998-2000 | option_split 1 |

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

1. Next block by generic-only cars: Volvo S40 (276), Saturn SL (267), Chevrolet Trax (266), Chevrolet Sonic (261), Ford Freestar (254), Ford Freestyle (252), Mitsubishi Mirage (233), Chevrolet Venture (226).
   Research generations and facelifts with sources first. The Fiat 500L/500X
   and Encore GX have evergreen-only entries awaiting their own research.
2. Follow-up: "ES 300"/"ES 330" listings match both `lexus es` and the
   overlay `es 300` entry (two "Lexus ES" cards). Merge the overlay rows
   into `lexus es` and drop the duplicate (§20.5).
3. Facelifts: §23 done (21 keys; Suburban/Tahoe/Yukon have no confirmed
   year). Next by cars: CR-V, Murano, Acadia, Durango, Chrysler 300,
   Sienna, Outback, C-Class, F-250, Acura TL, Express, Forester, S10,
   Journey, Chrysler 200 (Journey/200 have no GENERATION_BREAKS; fine for
   FACELIFT_BREAKS). Same rule: a cited source per year; single-component
   years (grille-only, tail-only) and mid-year changes are not cuts.
   Routing follow-up (§23.2): done in §23.6 (below).
4. When the daily email's "Most searched parts / cars (7 d)" has a week of
   data, let it reorder the list. Re-measure after each model.
