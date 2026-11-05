# OEM curation report: ford

Raw: `50ac4a48cdc62d02bd819bec33a67d0f07d8a71e` @ `50ac4a48cdc6`; as of 2026-11-05T12:52:15Z.

- records 2945, classes 2945, list rows 0, year manifests 0, cells 5429
- Verified groups 0, engine vg groups 0, Likely groups 923
- blocked sites: none

## Gates standing for the whole namespace

- no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close (C1/C2); Verified is impossible by design until the crawler writes them
- no (site, category) of this namespace has passed the audit gate (CATEGORY_STATUS has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.fordpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.fordpartsgiant.com: only 1% of its 6473 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2247 |
| ac-compressor | no_records | - | 10698 |
| ac-compressor | not_closed | ambig_target | 409 |
| ac-compressor | not_closed | no_year_manifest | 47163 |
| alternator | unmapped | - | 2247 |
| alternator | no_records | - | 7322 |
| alternator | not_closed | no_year_manifest | 50948 |
| climate-control | unmapped | - | 2247 |
| climate-control | no_records | - | 24881 |
| climate-control | not_closed | ambig_target | 166 |
| climate-control | not_closed | no_year_manifest | 33223 |
| fuel-pump-module | unmapped | - | 2247 |
| fuel-pump-module | no_records | - | 26197 |
| fuel-pump-module | not_closed | ambig_target | 89 |
| fuel-pump-module | not_closed | no_year_manifest | 31984 |
| headlights | unmapped | - | 2247 |
| headlights | no_records | - | 16065 |
| headlights | not_closed | ambig_target | 410 |
| headlights | not_closed | no_year_manifest | 41795 |
| power-steering-pump | unmapped | - | 2247 |
| power-steering-pump | no_records | - | 32651 |
| power-steering-pump | not_closed | no_year_manifest | 25619 |
| side-mirrors | unmapped | - | 2247 |
| side-mirrors | no_records | - | 9404 |
| side-mirrors | not_closed | ambig_target | 454 |
| side-mirrors | not_closed | no_year_manifest | 48412 |
| starter | unmapped | - | 2247 |
| starter | no_records | - | 18085 |
| starter | not_closed | ambig_target | 17 |
| starter | not_closed | no_year_manifest | 40168 |
| tail-lights | unmapped | - | 2247 |
| tail-lights | no_records | - | 14012 |
| tail-lights | not_closed | ambig_target | 458 |
| tail-lights | not_closed | no_year_manifest | 43800 |
| throttle-body | unmapped | - | 2247 |
| throttle-body | no_records | - | 27324 |
| throttle-body | not_closed | no_year_manifest | 30946 |
| tow-mirrors | unmapped | - | 2247 |
| tow-mirrors | no_records | - | 52379 |
| tow-mirrors | not_closed | ambig_target | 220 |
| tow-mirrors | not_closed | no_year_manifest | 5671 |
| window-regulator | unmapped | - | 2247 |
| window-regulator | no_records | - | 17356 |
| window-regulator | not_closed | ambig_target | 17 |
| window-regulator | not_closed | no_year_manifest | 40897 |
| window-switch | unmapped | - | 2247 |
| window-switch | no_records | - | 16352 |
| window-switch | not_closed | ambig_target | 151 |
| window-switch | not_closed | no_year_manifest | 41767 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2247 |
| ac-compressor | no_records | - | 10698 |
| ac-compressor | split | option_split | 32493 |
| ac-compressor | conditional | conditional:engine | 1121 |
| ac-compressor | conditional | conditional:notes_not_own_page | 12732 |
| ac-compressor | conditional | conditional:option_layout | 1226 |
| alternator | unmapped | - | 2247 |
| alternator | no_records | - | 7322 |
| alternator | split | option_split | 42716 |
| alternator | conditional | conditional:engine | 266 |
| alternator | conditional | conditional:notes_not_own_page | 7263 |
| alternator | conditional | conditional:option_layout | 703 |
| climate-control | unmapped | - | 2247 |
| climate-control | no_records | - | 24881 |
| climate-control | split | option_split | 24698 |
| climate-control | conditional | conditional:colour | 186 |
| climate-control | conditional | conditional:notes_not_own_page | 8169 |
| climate-control | conditional | conditional:option_layout | 336 |
| fuel-pump-module | unmapped | - | 2247 |
| fuel-pump-module | no_records | - | 26197 |
| fuel-pump-module | split | option_split | 25373 |
| fuel-pump-module | conditional | conditional:notes_not_own_page | 4936 |
| fuel-pump-module | conditional | conditional:option_layout | 1764 |
| headlights | unmapped | - | 2247 |
| headlights | no_records | - | 16065 |
| headlights | split | option_split | 32319 |
| headlights | split | slot_missing | 815 |
| headlights | conditional | conditional:notes_not_own_page | 7605 |
| headlights | conditional | conditional:option | 102 |
| headlights | conditional | conditional:option_layout | 1364 |
| power-steering-pump | unmapped | - | 2247 |
| power-steering-pump | no_records | - | 32651 |
| power-steering-pump | split | option_split | 11183 |
| power-steering-pump | conditional | conditional:colour | 366 |
| power-steering-pump | conditional | conditional:engine | 296 |
| power-steering-pump | conditional | conditional:notes_not_own_page | 10984 |
| power-steering-pump | conditional | conditional:option | 163 |
| power-steering-pump | conditional | conditional:option_layout | 2627 |
| side-mirrors | unmapped | - | 2247 |
| side-mirrors | no_records | - | 9404 |
| side-mirrors | split | option_split | 43860 |
| side-mirrors | split | slot_missing | 2053 |
| side-mirrors | conditional | conditional:colour | 117 |
| side-mirrors | conditional | conditional:notes_not_own_page | 2218 |
| side-mirrors | conditional | conditional:option | 399 |
| side-mirrors | conditional | conditional:option_layout | 219 |
| starter | unmapped | - | 2247 |
| starter | no_records | - | 18085 |
| starter | split | option_split | 33654 |
| starter | conditional | conditional:notes_not_own_page | 5533 |
| starter | conditional | conditional:option | 163 |
| starter | conditional | conditional:option_layout | 835 |
| tail-lights | unmapped | - | 2247 |
| tail-lights | no_records | - | 14012 |
| tail-lights | split | option_split | 37384 |
| tail-lights | split | slot_missing | 489 |
| tail-lights | conditional | conditional:notes_not_own_page | 5259 |
| tail-lights | conditional | conditional:option | 2 |
| tail-lights | conditional | conditional:option_layout | 1124 |
| throttle-body | unmapped | - | 2247 |
| throttle-body | no_records | - | 27324 |
| throttle-body | split | option_split | 14289 |
| throttle-body | conditional | conditional:engine | 57 |
| throttle-body | conditional | conditional:notes_not_own_page | 13675 |
| throttle-body | conditional | conditional:option | 154 |
| throttle-body | conditional | conditional:option_layout | 2771 |
| tow-mirrors | unmapped | - | 2247 |
| tow-mirrors | no_records | - | 52379 |
| tow-mirrors | split | option_split | 2928 |
| tow-mirrors | split | position_conflict | 607 |
| tow-mirrors | split | slot_missing | 2356 |
| window-regulator | unmapped | - | 2247 |
| window-regulator | no_records | - | 17356 |
| window-regulator | split | packaging_incomplete | 3899 |
| window-regulator | split | packaging_split | 13909 |
| window-regulator | split | packaging_unstated | 21713 |
| window-regulator | split | position_missing | 798 |
| window-regulator | conditional | conditional:option_layout | 595 |
| window-switch | unmapped | - | 2247 |
| window-switch | no_records | - | 16352 |
| window-switch | split | no_candidates | 3029 |
| window-switch | split | option_split | 20391 |
| window-switch | split | position_missing | 12403 |
| window-switch | conditional | conditional:colour | 1244 |
| window-switch | conditional | conditional:notes_not_own_page | 3612 |
| window-switch | conditional | conditional:option_layout | 1239 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 9
- rule_drift: 25
- universal_part_suspect: 9

## Unknown note clauses (top 30)

- `Callout Name: 17682`: 720
- `Callout Name: 13008`: 362
- `Base Number: 17682`: 346
- `(CP) Designates Crash Part - When Ordering Please Refer To Crash Part Truckload Program Guidelines`: 340
- `Callout Name: 13404`: 284
- `Callout Name: 19980`: 253
- `Base Number: 13008`: 181
- `Callout Name: 10346`: 177
- `Callout Name: 9H307`: 141
- `Headlamp Assy`: 135
- `Base Number: 19980`: 126
- `Lamp Assy - Rear`: 122
- `Base Number: 13404`: 116
- `Callout Name: 19703`: 115
- `Callout Name: <23394`: 108
- `Callout Name: 3A674`: 88
- `R.H.`: 86
- `Callout Name: <23200`: 84
- `L.H.`: 82
- `Paint to match`: 82
- `Excludes Cover`: 81
- `Base Number: 9H307`: 77
- `Callout Name: 11002`: 77
- `Mirror Assy`: 76
- `Fit Note: Dual Zone Auto Temp Control A/C`: 74
- `Base Number: <23394`: 72
- `With Drivers Heated Seat`: 70
- `Callout Name: <27000`: 62
- `Callout Name: 13404A`: 61
- `Less Temp Control Driver Seat`: 61

## Unmapped catalog models

- Ford E-350/E-350 Super Duty: feed 'E-350/E-350 Super Duty' 0 cars (excluded: feed has no 'E-350/E-350 Super Duty'; feed splits E-350 spellings)
- Ford E-550 Super Duty: feed 'E-550 Super Duty' 0 cars
- Ford EcoSport: feed 'EcoSport' 0 cars
- Ford Econoline Super Duty(1996-1999): feed 'Econoline Super Duty(1996-1999)' 0 cars
- Ford F Super Duty: feed 'F Super Duty' 0 cars
- Ford F53: feed 'F-53' 0 cars
- Ford F53 Stripped Chassis: feed 'F53 Stripped Chassis' 0 cars (excluded: catalog model with no feed cars as 'F53 Stripped Chassis' (inventory 2026-11-04); nothing to map)
- Ford Police Responder Hybrid: feed 'Police Responder Hybrid' 0 cars (excluded: catalog model with no feed cars as 'Police Responder Hybrid' (inventory 2026-11-04); nothing to map)
- Ford SSV Plug-In Hybrid: feed 'SSV Plug-In Hybrid' 0 cars (excluded: catalog model with no feed cars as 'SSV Plug-In Hybrid' (inventory 2026-11-04); nothing to map)
- Mercury Lynx: feed 'Lynx' 0 cars
