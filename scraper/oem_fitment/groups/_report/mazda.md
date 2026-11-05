# OEM curation report: mazda

Raw: `ceccc800d7ba22c0291121baabb0a9292eb8f271` @ `ceccc800d7ba`; as of 2026-11-05T12:14:17Z.

- records 1391, classes 1391, list rows 0, year manifests 0, cells 2463
- Verified groups 0, engine vg groups 0, Likely groups 58
- blocked sites: none

## Gates standing for the whole namespace

- no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close (C1/C2); Verified is impossible by design until the crawler writes them
- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.mazdapartsnow.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 403 |
| ac-compressor | no_records | - | 553 |
| ac-compressor | not_closed | no_year_manifest | 5274 |
| alternator | unmapped | - | 403 |
| alternator | no_records | - | 183 |
| alternator | not_closed | no_year_manifest | 5644 |
| bumper-front | unmapped | - | 403 |
| bumper-front | no_records | - | 1531 |
| bumper-front | not_closed | no_year_manifest | 4296 |
| bumper-rear | unmapped | - | 403 |
| bumper-rear | no_records | - | 1085 |
| bumper-rear | not_closed | no_year_manifest | 4742 |
| climate-control | unmapped | - | 403 |
| climate-control | no_records | - | 1252 |
| climate-control | not_closed | no_year_manifest | 4575 |
| door-front | unmapped | - | 403 |
| door-front | no_records | - | 563 |
| door-front | not_closed | no_year_manifest | 5264 |
| door-rear | unmapped | - | 403 |
| door-rear | no_records | - | 198 |
| door-rear | not_closed | no_year_manifest | 5629 |
| fender | unmapped | - | 403 |
| fender | no_records | - | 368 |
| fender | not_closed | no_year_manifest | 5459 |
| fuel-pump-module | unmapped | - | 403 |
| fuel-pump-module | no_records | - | 858 |
| fuel-pump-module | not_closed | no_year_manifest | 4969 |
| gauge-cluster | unmapped | - | 403 |
| gauge-cluster | no_records | - | 2755 |
| gauge-cluster | not_closed | no_year_manifest | 3072 |
| grille | unmapped | - | 403 |
| grille | no_records | - | 2689 |
| grille | not_closed | no_year_manifest | 3138 |
| headlights | unmapped | - | 403 |
| headlights | no_records | - | 1433 |
| headlights | not_closed | no_year_manifest | 4394 |
| hood | unmapped | - | 403 |
| hood | no_records | - | 372 |
| hood | not_closed | no_year_manifest | 5455 |
| ignition-coils | unmapped | - | 403 |
| ignition-coils | no_records | - | 482 |
| ignition-coils | not_closed | no_year_manifest | 5345 |
| liftgate | unmapped | - | 403 |
| liftgate | no_records | - | 2050 |
| liftgate | not_closed | no_year_manifest | 3777 |
| power-steering-pump | unmapped | - | 403 |
| power-steering-pump | no_records | - | 2312 |
| power-steering-pump | not_closed | no_year_manifest | 3515 |
| radiator | unmapped | - | 403 |
| radiator | no_records | - | 689 |
| radiator | not_closed | no_year_manifest | 5138 |
| side-mirrors | unmapped | - | 403 |
| side-mirrors | no_records | - | 978 |
| side-mirrors | not_closed | no_year_manifest | 4849 |
| starter | unmapped | - | 403 |
| starter | no_records | - | 320 |
| starter | not_closed | no_year_manifest | 5507 |
| tail-lights | unmapped | - | 403 |
| tail-lights | no_records | - | 2678 |
| tail-lights | not_closed | no_year_manifest | 3149 |
| tailgate | unmapped | - | 403 |
| tailgate | no_records | - | 5823 |
| tailgate | not_closed | no_year_manifest | 4 |
| throttle-body | unmapped | - | 403 |
| throttle-body | no_records | - | 507 |
| throttle-body | not_closed | no_year_manifest | 5320 |
| trunk-lid | unmapped | - | 403 |
| trunk-lid | no_records | - | 2214 |
| trunk-lid | not_closed | no_year_manifest | 3613 |
| window-regulator | unmapped | - | 403 |
| window-regulator | no_records | - | 106 |
| window-regulator | not_closed | no_year_manifest | 5721 |
| window-switch | unmapped | - | 403 |
| window-switch | no_records | - | 1319 |
| window-switch | not_closed | no_year_manifest | 4508 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 403 |
| ac-compressor | no_records | - | 553 |
| ac-compressor | split | option_split | 3368 |
| ac-compressor | conditional | conditional:engine | 79 |
| ac-compressor | conditional | conditional:engine_unattested | 1416 |
| ac-compressor | conditional | conditional:trim | 411 |
| alternator | unmapped | - | 403 |
| alternator | no_records | - | 183 |
| alternator | split | option_split | 2940 |
| alternator | conditional | conditional:engine | 154 |
| alternator | conditional | conditional:engine_unattested | 1468 |
| alternator | conditional | conditional:trim | 1082 |
| bumper-front | unmapped | - | 403 |
| bumper-front | no_records | - | 1531 |
| bumper-front | split | option_split | 2505 |
| bumper-front | conditional | conditional:body | 29 |
| bumper-front | conditional | conditional:engine_unattested | 756 |
| bumper-front | conditional | conditional:option | 162 |
| bumper-front | conditional | conditional:plant | 17 |
| bumper-front | conditional | conditional:qualifier | 78 |
| bumper-front | conditional | conditional:trim | 749 |
| bumper-rear | unmapped | - | 403 |
| bumper-rear | no_records | - | 1085 |
| bumper-rear | split | option_split | 2444 |
| bumper-rear | conditional | conditional:body | 85 |
| bumper-rear | conditional | conditional:engine | 112 |
| bumper-rear | conditional | conditional:engine_unattested | 1371 |
| bumper-rear | conditional | conditional:qualifier | 93 |
| bumper-rear | conditional | conditional:trim | 637 |
| climate-control | unmapped | - | 403 |
| climate-control | no_records | - | 1252 |
| climate-control | split | option_split | 3831 |
| climate-control | conditional | conditional:colour | 15 |
| climate-control | conditional | conditional:engine_unattested | 207 |
| climate-control | conditional | conditional:trim | 522 |
| door-front | unmapped | - | 403 |
| door-front | no_records | - | 563 |
| door-front | split | option_split | 2295 |
| door-front | split | slot_missing | 383 |
| door-front | conditional | conditional:engine_unattested | 1790 |
| door-front | conditional | conditional:trim | 796 |
| door-rear | unmapped | - | 403 |
| door-rear | no_records | - | 198 |
| door-rear | split | option_split | 2552 |
| door-rear | split | slot_missing | 95 |
| door-rear | conditional | conditional:body | 85 |
| door-rear | conditional | conditional:engine_unattested | 1604 |
| door-rear | conditional | conditional:trim | 1293 |
| fender | unmapped | - | 403 |
| fender | no_records | - | 368 |
| fender | split | option_split | 3137 |
| fender | split | slot_missing | 317 |
| fender | conditional | conditional:body | 29 |
| fender | conditional | conditional:engine_unattested | 1001 |
| fender | conditional | conditional:trim | 975 |
| fuel-pump-module | unmapped | - | 403 |
| fuel-pump-module | no_records | - | 858 |
| fuel-pump-module | split | option_split | 3065 |
| fuel-pump-module | conditional | conditional:emissions | 14 |
| fuel-pump-module | conditional | conditional:engine | 57 |
| fuel-pump-module | conditional | conditional:engine_unattested | 703 |
| fuel-pump-module | conditional | conditional:model_other | 84 |
| fuel-pump-module | conditional | conditional:trim | 1046 |
| gauge-cluster | unmapped | - | 403 |
| gauge-cluster | no_records | - | 2755 |
| gauge-cluster | split | option_split | 1696 |
| gauge-cluster | conditional | conditional:body | 56 |
| gauge-cluster | conditional | conditional:engine | 358 |
| gauge-cluster | conditional | conditional:engine_unattested | 186 |
| gauge-cluster | conditional | conditional:production | 92 |
| gauge-cluster | conditional | conditional:trim | 684 |
| grille | unmapped | - | 403 |
| grille | no_records | - | 2689 |
| grille | split | option_split | 1827 |
| grille | conditional | conditional:body | 29 |
| grille | conditional | conditional:colour | 14 |
| grille | conditional | conditional:engine_unattested | 362 |
| grille | conditional | conditional:option | 44 |
| grille | conditional | conditional:trim | 862 |
| headlights | unmapped | - | 403 |
| headlights | no_records | - | 1433 |
| headlights | split | option_split | 3838 |
| headlights | conditional | conditional:engine_unattested | 135 |
| headlights | conditional | conditional:trim | 421 |
| hood | unmapped | - | 403 |
| hood | no_records | - | 372 |
| hood | split | option_split | 2295 |
| hood | conditional | conditional:engine_unattested | 1766 |
| hood | conditional | conditional:trim | 1394 |
| ignition-coils | unmapped | - | 403 |
| ignition-coils | no_records | - | 482 |
| ignition-coils | split | option_split | 2146 |
| ignition-coils | conditional | conditional:colour | 3 |
| ignition-coils | conditional | conditional:engine | 72 |
| ignition-coils | conditional | conditional:engine_unattested | 1324 |
| ignition-coils | conditional | conditional:trim | 1800 |
| liftgate | unmapped | - | 403 |
| liftgate | no_records | - | 2050 |
| liftgate | split | option_split | 2653 |
| liftgate | conditional | conditional:engine_unattested | 393 |
| liftgate | conditional | conditional:trim | 731 |
| power-steering-pump | unmapped | - | 403 |
| power-steering-pump | no_records | - | 2312 |
| power-steering-pump | split | option_split | 1928 |
| power-steering-pump | conditional | conditional:engine | 123 |
| power-steering-pump | conditional | conditional:engine_unattested | 1130 |
| power-steering-pump | conditional | conditional:trim | 334 |
| radiator | unmapped | - | 403 |
| radiator | no_records | - | 689 |
| radiator | split | option_split | 3155 |
| radiator | conditional | conditional:colour | 1 |
| radiator | conditional | conditional:engine | 447 |
| radiator | conditional | conditional:engine_unattested | 874 |
| radiator | conditional | conditional:trans | 34 |
| radiator | conditional | conditional:trim | 627 |
| side-mirrors | unmapped | - | 403 |
| side-mirrors | no_records | - | 978 |
| side-mirrors | split | option_split | 4079 |
| side-mirrors | split | slot_missing | 171 |
| side-mirrors | conditional | conditional:colour | 23 |
| side-mirrors | conditional | conditional:engine_unattested | 309 |
| side-mirrors | conditional | conditional:option | 91 |
| side-mirrors | conditional | conditional:trim | 176 |
| starter | unmapped | - | 403 |
| starter | no_records | - | 320 |
| starter | split | option_split | 4198 |
| starter | conditional | conditional:engine_unattested | 857 |
| starter | conditional | conditional:trim | 452 |
| tail-lights | unmapped | - | 403 |
| tail-lights | no_records | - | 2678 |
| tail-lights | split | option_split | 2352 |
| tail-lights | split | position_missing | 430 |
| tail-lights | split | slot_missing | 64 |
| tail-lights | conditional | conditional:engine_unattested | 303 |
| tailgate | unmapped | - | 403 |
| tailgate | no_records | - | 5823 |
| tailgate | conditional | conditional:engine_unattested | 4 |
| throttle-body | unmapped | - | 403 |
| throttle-body | no_records | - | 507 |
| throttle-body | split | option_split | 3489 |
| throttle-body | conditional | conditional:colour | 23 |
| throttle-body | conditional | conditional:engine_unattested | 1047 |
| throttle-body | conditional | conditional:trim | 761 |
| trunk-lid | unmapped | - | 403 |
| trunk-lid | no_records | - | 2214 |
| trunk-lid | split | option_split | 1481 |
| trunk-lid | conditional | conditional:engine_unattested | 181 |
| trunk-lid | conditional | conditional:option | 35 |
| trunk-lid | conditional | conditional:trim | 1916 |
| window-regulator | unmapped | - | 403 |
| window-regulator | no_records | - | 106 |
| window-regulator | split | packaging_incomplete | 350 |
| window-regulator | split | packaging_split | 370 |
| window-regulator | split | packaging_unstated | 5001 |
| window-switch | unmapped | - | 403 |
| window-switch | no_records | - | 1319 |
| window-switch | split | option_split | 299 |
| window-switch | split | position_missing | 2821 |
| window-switch | conditional | conditional:engine_unattested | 1149 |
| window-switch | conditional | conditional:trim | 239 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- universal_part_suspect: 1

## Unknown note clauses (top 30)

- `Without Mazdaspeed6`: 73
- `Mazda3`: 64
- `With Defogger`: 41
- `With Mazdaspeed6`: 40
- `Mazda6`: 37
- `Without Defogger`: 37
- `Without Mazdaspeed`: 28
- `All`: 27
- `Standard Type`: 25
- `Mazdaspeed3`: 20
- `With Side Molding`: 20
- `With Mazdaspeed`: 18
- `Without MPS Option`: 18
- `With Body Color`: 17
- `Without Spoiler`: 15
- `With Spoiler`: 14
- `With AC`: 13
- `With Body Color Bar`: 12
- `Mazda5`: 11
- `Sporty Type 2006-08`: 11
- `Black Bezel`: 10
- `Standard Bezel`: 9
- `Electric`: 8
- `Mazda2`: 8
- `Without Side Molding`: 8
- `Without Special Tuned Suspension`: 8
- `Without Turbo`: 8
- `With Adaptive Cruise`: 7
- `Without Power Fold`: 7
- `Mazdaspeed6`: 6

## Unmapped catalog models

- Mazda B2200: feed 'B2200' 30 cars
- Mazda B2300: feed 'B2300' 27 cars
- Mazda B2600: feed 'B2600' 4 cars
- Mazda B3000: feed 'B3000' 18 cars
- Mazda B4000: feed 'B4000' 10 cars
- Mazda CX-70: feed 'CX-70' 0 cars
- Mazda CX-90: feed 'CX-90' 0 cars
- Mazda MX-30 EV: feed 'MX-30 EV' 0 cars
- Mazda MX-5 Miata: feed 'MX-5 Miata' 109 cars
- Mazda Miata: feed 'MX-5 Miata' 109 cars
