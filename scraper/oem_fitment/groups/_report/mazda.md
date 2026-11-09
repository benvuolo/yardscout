# OEM curation report: mazda

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-05T12:14:17Z.

- records 1391, classes 1391, list rows 0, year manifests 0, cells 2463
- Verified groups 0, engine vg groups 0, Likely groups 0
- blocked sites: none

## Gates standing for the whole namespace

- no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close (C1/C2); Verified is impossible by design until the crawler writes them
- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.mazdapartsnow.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 402 |
| ac-compressor | no_records | - | 552 |
| ac-compressor | not_closed | no_year_manifest | 5292 |
| alternator | unmapped | - | 402 |
| alternator | no_records | - | 182 |
| alternator | not_closed | no_year_manifest | 5662 |
| bumper-front | unmapped | - | 402 |
| bumper-front | no_records | - | 1541 |
| bumper-front | not_closed | no_year_manifest | 4303 |
| bumper-rear | unmapped | - | 402 |
| bumper-rear | no_records | - | 1095 |
| bumper-rear | not_closed | no_year_manifest | 4749 |
| climate-control | unmapped | - | 402 |
| climate-control | no_records | - | 1273 |
| climate-control | not_closed | no_year_manifest | 4571 |
| door-front | unmapped | - | 402 |
| door-front | no_records | - | 568 |
| door-front | not_closed | no_year_manifest | 5276 |
| door-rear | unmapped | - | 402 |
| door-rear | no_records | - | 200 |
| door-rear | not_closed | no_year_manifest | 5644 |
| fender | unmapped | - | 402 |
| fender | no_records | - | 366 |
| fender | not_closed | no_year_manifest | 5478 |
| fuel-pump-module | unmapped | - | 402 |
| fuel-pump-module | no_records | - | 871 |
| fuel-pump-module | not_closed | no_year_manifest | 4973 |
| gauge-cluster | unmapped | - | 402 |
| gauge-cluster | no_records | - | 2772 |
| gauge-cluster | not_closed | no_year_manifest | 3072 |
| grille | unmapped | - | 402 |
| grille | no_records | - | 2704 |
| grille | not_closed | no_year_manifest | 3140 |
| headlights | unmapped | - | 402 |
| headlights | no_records | - | 1427 |
| headlights | not_closed | no_year_manifest | 4417 |
| hood | unmapped | - | 402 |
| hood | no_records | - | 373 |
| hood | not_closed | no_year_manifest | 5471 |
| ignition-coils | unmapped | - | 402 |
| ignition-coils | no_records | - | 481 |
| ignition-coils | not_closed | no_year_manifest | 5363 |
| liftgate | unmapped | - | 402 |
| liftgate | no_records | - | 2051 |
| liftgate | not_closed | no_year_manifest | 3793 |
| power-steering-pump | unmapped | - | 402 |
| power-steering-pump | no_records | - | 2330 |
| power-steering-pump | not_closed | no_year_manifest | 3514 |
| radiator | unmapped | - | 402 |
| radiator | no_records | - | 687 |
| radiator | not_closed | no_year_manifest | 5157 |
| side-mirrors | unmapped | - | 402 |
| side-mirrors | no_records | - | 977 |
| side-mirrors | not_closed | no_year_manifest | 4867 |
| starter | unmapped | - | 402 |
| starter | no_records | - | 320 |
| starter | not_closed | no_year_manifest | 5524 |
| tail-lights | unmapped | - | 402 |
| tail-lights | no_records | - | 2695 |
| tail-lights | not_closed | no_year_manifest | 3149 |
| tailgate | unmapped | - | 402 |
| tailgate | no_records | - | 5840 |
| tailgate | not_closed | no_year_manifest | 4 |
| throttle-body | unmapped | - | 402 |
| throttle-body | no_records | - | 500 |
| throttle-body | not_closed | no_year_manifest | 5344 |
| trunk-lid | unmapped | - | 402 |
| trunk-lid | no_records | - | 2208 |
| trunk-lid | not_closed | no_year_manifest | 3636 |
| window-regulator | unmapped | - | 402 |
| window-regulator | no_records | - | 110 |
| window-regulator | not_closed | no_year_manifest | 5734 |
| window-switch | unmapped | - | 402 |
| window-switch | no_records | - | 1320 |
| window-switch | not_closed | no_year_manifest | 4524 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 402 |
| ac-compressor | no_records | - | 552 |
| ac-compressor | split | option_split | 3383 |
| ac-compressor | conditional | conditional:engine | 79 |
| ac-compressor | conditional | conditional:engine_unattested | 1412 |
| ac-compressor | conditional | conditional:trim | 418 |
| alternator | unmapped | - | 402 |
| alternator | no_records | - | 182 |
| alternator | split | option_split | 2950 |
| alternator | conditional | conditional:engine | 152 |
| alternator | conditional | conditional:engine_unattested | 1468 |
| alternator | conditional | conditional:trim | 1092 |
| bumper-front | unmapped | - | 402 |
| bumper-front | no_records | - | 1541 |
| bumper-front | split | option_split | 2511 |
| bumper-front | conditional | conditional:body | 30 |
| bumper-front | conditional | conditional:engine_unattested | 754 |
| bumper-front | conditional | conditional:option | 160 |
| bumper-front | conditional | conditional:plant | 17 |
| bumper-front | conditional | conditional:qualifier | 80 |
| bumper-front | conditional | conditional:trim | 751 |
| bumper-rear | unmapped | - | 402 |
| bumper-rear | no_records | - | 1095 |
| bumper-rear | split | option_split | 2447 |
| bumper-rear | conditional | conditional:body | 86 |
| bumper-rear | conditional | conditional:engine | 111 |
| bumper-rear | conditional | conditional:engine_unattested | 1369 |
| bumper-rear | conditional | conditional:qualifier | 94 |
| bumper-rear | conditional | conditional:trim | 642 |
| climate-control | unmapped | - | 402 |
| climate-control | no_records | - | 1273 |
| climate-control | split | option_split | 3831 |
| climate-control | conditional | conditional:colour | 16 |
| climate-control | conditional | conditional:engine_unattested | 208 |
| climate-control | conditional | conditional:trim | 516 |
| door-front | unmapped | - | 402 |
| door-front | no_records | - | 568 |
| door-front | split | option_split | 2318 |
| door-front | split | slot_missing | 385 |
| door-front | conditional | conditional:engine_unattested | 1781 |
| door-front | conditional | conditional:trim | 792 |
| door-rear | unmapped | - | 402 |
| door-rear | no_records | - | 200 |
| door-rear | split | option_split | 2582 |
| door-rear | split | slot_missing | 94 |
| door-rear | conditional | conditional:body | 86 |
| door-rear | conditional | conditional:engine_unattested | 1605 |
| door-rear | conditional | conditional:trim | 1277 |
| fender | unmapped | - | 402 |
| fender | no_records | - | 366 |
| fender | split | option_split | 3165 |
| fender | split | slot_missing | 315 |
| fender | conditional | conditional:body | 30 |
| fender | conditional | conditional:engine_unattested | 999 |
| fender | conditional | conditional:trim | 969 |
| fuel-pump-module | unmapped | - | 402 |
| fuel-pump-module | no_records | - | 871 |
| fuel-pump-module | split | option_split | 3084 |
| fuel-pump-module | conditional | conditional:emissions | 14 |
| fuel-pump-module | conditional | conditional:engine | 57 |
| fuel-pump-module | conditional | conditional:engine_unattested | 703 |
| fuel-pump-module | conditional | conditional:model_other | 82 |
| fuel-pump-module | conditional | conditional:trim | 1033 |
| gauge-cluster | unmapped | - | 402 |
| gauge-cluster | no_records | - | 2772 |
| gauge-cluster | split | option_split | 1695 |
| gauge-cluster | conditional | conditional:body | 56 |
| gauge-cluster | conditional | conditional:engine | 367 |
| gauge-cluster | conditional | conditional:engine_unattested | 189 |
| gauge-cluster | conditional | conditional:production | 92 |
| gauge-cluster | conditional | conditional:trim | 673 |
| grille | unmapped | - | 402 |
| grille | no_records | - | 2704 |
| grille | split | option_split | 1831 |
| grille | conditional | conditional:body | 30 |
| grille | conditional | conditional:colour | 14 |
| grille | conditional | conditional:engine_unattested | 361 |
| grille | conditional | conditional:option | 44 |
| grille | conditional | conditional:trim | 860 |
| headlights | unmapped | - | 402 |
| headlights | no_records | - | 1427 |
| headlights | split | option_split | 3857 |
| headlights | conditional | conditional:engine_unattested | 139 |
| headlights | conditional | conditional:trim | 421 |
| hood | unmapped | - | 402 |
| hood | no_records | - | 373 |
| hood | split | option_split | 2318 |
| hood | conditional | conditional:engine_unattested | 1771 |
| hood | conditional | conditional:trim | 1382 |
| ignition-coils | unmapped | - | 402 |
| ignition-coils | no_records | - | 481 |
| ignition-coils | split | option_split | 2156 |
| ignition-coils | conditional | conditional:engine | 73 |
| ignition-coils | conditional | conditional:engine_unattested | 1319 |
| ignition-coils | conditional | conditional:trim | 1815 |
| liftgate | unmapped | - | 402 |
| liftgate | no_records | - | 2051 |
| liftgate | split | option_split | 2663 |
| liftgate | conditional | conditional:engine_unattested | 391 |
| liftgate | conditional | conditional:trim | 739 |
| power-steering-pump | unmapped | - | 402 |
| power-steering-pump | no_records | - | 2330 |
| power-steering-pump | split | option_split | 1933 |
| power-steering-pump | conditional | conditional:engine | 121 |
| power-steering-pump | conditional | conditional:engine_unattested | 1127 |
| power-steering-pump | conditional | conditional:trim | 333 |
| radiator | unmapped | - | 402 |
| radiator | no_records | - | 687 |
| radiator | split | option_split | 3158 |
| radiator | conditional | conditional:engine | 455 |
| radiator | conditional | conditional:engine_unattested | 878 |
| radiator | conditional | conditional:trans | 35 |
| radiator | conditional | conditional:trim | 631 |
| side-mirrors | unmapped | - | 402 |
| side-mirrors | no_records | - | 977 |
| side-mirrors | split | option_split | 4091 |
| side-mirrors | split | slot_missing | 172 |
| side-mirrors | conditional | conditional:colour | 23 |
| side-mirrors | conditional | conditional:engine_unattested | 313 |
| side-mirrors | conditional | conditional:option | 92 |
| side-mirrors | conditional | conditional:trim | 176 |
| starter | unmapped | - | 402 |
| starter | no_records | - | 320 |
| starter | split | option_split | 4231 |
| starter | conditional | conditional:engine_unattested | 854 |
| starter | conditional | conditional:trim | 439 |
| tail-lights | unmapped | - | 402 |
| tail-lights | no_records | - | 2695 |
| tail-lights | split | option_split | 2350 |
| tail-lights | split | position_missing | 429 |
| tail-lights | split | slot_missing | 68 |
| tail-lights | conditional | conditional:engine_unattested | 302 |
| tailgate | unmapped | - | 402 |
| tailgate | no_records | - | 5840 |
| tailgate | conditional | conditional:engine_unattested | 4 |
| throttle-body | unmapped | - | 402 |
| throttle-body | no_records | - | 500 |
| throttle-body | split | option_split | 3491 |
| throttle-body | conditional | conditional:engine_unattested | 1080 |
| throttle-body | conditional | conditional:trim | 773 |
| trunk-lid | unmapped | - | 402 |
| trunk-lid | no_records | - | 2208 |
| trunk-lid | split | option_split | 1482 |
| trunk-lid | conditional | conditional:engine_unattested | 185 |
| trunk-lid | conditional | conditional:option | 35 |
| trunk-lid | conditional | conditional:trim | 1934 |
| window-regulator | unmapped | - | 402 |
| window-regulator | no_records | - | 110 |
| window-regulator | split | packaging_incomplete | 342 |
| window-regulator | split | packaging_split | 368 |
| window-regulator | split | packaging_unstated | 5024 |
| window-switch | unmapped | - | 402 |
| window-switch | no_records | - | 1320 |
| window-switch | split | option_split | 297 |
| window-switch | split | position_missing | 2842 |
| window-switch | conditional | conditional:engine_unattested | 1148 |
| window-switch | conditional | conditional:trim | 237 |

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
- `All`: 26
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
- `With Adaptive Cruise`: 7
- `Without Power Fold`: 7
- `Mazdaspeed6`: 6
- `Nordic Green`: 6

## Unmapped catalog models

- Mazda B2200: feed 'B2200' 31 cars
- Mazda B2300: feed 'B2300' 28 cars
- Mazda B2600: feed 'B2600' 4 cars
- Mazda B3000: feed 'B3000' 20 cars
- Mazda B4000: feed 'B4000' 11 cars
- Mazda CX-70: feed 'CX-70' 0 cars
- Mazda CX-90: feed 'CX-90' 0 cars
- Mazda MX-30 EV: feed 'MX-30 EV' 0 cars
- Mazda MX-5 Miata: feed 'MX-5 Miata' 105 cars
- Mazda Miata: feed 'MX-5 Miata' 105 cars
