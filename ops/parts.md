# Parts workstream — status (updated 2026-11-04, §13 done)

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

## How to measure

`interchange_coverage.py` measures engine-family donors, not generic-only.
The generic-only count re-matches every distinct year/make/model in
`docs/data/inventory_live.json` with `js.match_vehicle` and applies
`mine_coverage_gaps.is_generic_only` (≈15 s). Use the miner only with
`--no-fetch`: its default run fetches eBay sold-listing pages, which
standing rule 2 forbids (flagged for the owner; the script was not changed
here, it is outside this workstream's files).

## Open for the owner

- The §2–10 mechanical rows (e.g. Camry fuel pump "fits 2002–2017") span
  generations because `_GEN_MECH_EXCLUDE_RE` skips them in the split. Left
  as is; say if they should be bounded per generation like §13.
- `mine_coverage_gaps.py` fetches eBay pages by default (rule 2).

## Next

1. Next block by generic-only cars: Ford Focus 2000–07 (1,535), Explorer
   1st/2nd gen (1,173), Jeep Compass (911), Kia Rio (781), Buick Century
   (704), Chevrolet Aveo (674), VW Passat (652), Buick Lucerne (621).
2. When the daily email's "Most searched parts / cars (7 d)" has a week of
   data, let it reorder that list.
3. Re-measure after each model and append to PARTS_GAPS.
