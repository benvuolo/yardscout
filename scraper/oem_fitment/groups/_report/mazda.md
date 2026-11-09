# OEM curation report: mazda

Raw: `1351c33fcfbb` @ `1351c33fcfbb`; as of 2026-11-05T12:14:17Z.

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
| ac-compressor | unmapped | - | 405 |
| ac-compressor | no_records | - | 552 |
| ac-compressor | not_closed | no_year_manifest | 5294 |
| alternator | unmapped | - | 405 |
| alternator | no_records | - | 179 |
| alternator | not_closed | no_year_manifest | 5667 |
| bumper-front | unmapped | - | 405 |
| bumper-front | no_records | - | 1535 |
| bumper-front | not_closed | no_year_manifest | 4311 |
| bumper-rear | unmapped | - | 405 |
| bumper-rear | no_records | - | 1091 |
| bumper-rear | not_closed | no_year_manifest | 4755 |
| climate-control | unmapped | - | 405 |
| climate-control | no_records | - | 1266 |
| climate-control | not_closed | no_year_manifest | 4580 |
| door-front | unmapped | - | 405 |
| door-front | no_records | - | 565 |
| door-front | not_closed | no_year_manifest | 5281 |
| door-rear | unmapped | - | 405 |
| door-rear | no_records | - | 199 |
| door-rear | not_closed | no_year_manifest | 5647 |
| fender | unmapped | - | 405 |
| fender | no_records | - | 360 |
| fender | not_closed | no_year_manifest | 5486 |
| fuel-pump-module | unmapped | - | 405 |
| fuel-pump-module | no_records | - | 869 |
| fuel-pump-module | not_closed | no_year_manifest | 4977 |
| gauge-cluster | unmapped | - | 405 |
| gauge-cluster | no_records | - | 2769 |
| gauge-cluster | not_closed | no_year_manifest | 3077 |
| grille | unmapped | - | 405 |
| grille | no_records | - | 2696 |
| grille | not_closed | no_year_manifest | 3150 |
| headlights | unmapped | - | 405 |
| headlights | no_records | - | 1420 |
| headlights | not_closed | no_year_manifest | 4426 |
| hood | unmapped | - | 405 |
| hood | no_records | - | 369 |
| hood | not_closed | no_year_manifest | 5477 |
| ignition-coils | unmapped | - | 405 |
| ignition-coils | no_records | - | 477 |
| ignition-coils | not_closed | no_year_manifest | 5369 |
| liftgate | unmapped | - | 405 |
| liftgate | no_records | - | 2048 |
| liftgate | not_closed | no_year_manifest | 3798 |
| power-steering-pump | unmapped | - | 405 |
| power-steering-pump | no_records | - | 2326 |
| power-steering-pump | not_closed | no_year_manifest | 3520 |
| radiator | unmapped | - | 405 |
| radiator | no_records | - | 685 |
| radiator | not_closed | no_year_manifest | 5161 |
| side-mirrors | unmapped | - | 405 |
| side-mirrors | no_records | - | 980 |
| side-mirrors | not_closed | no_year_manifest | 4866 |
| starter | unmapped | - | 405 |
| starter | no_records | - | 320 |
| starter | not_closed | no_year_manifest | 5526 |
| tail-lights | unmapped | - | 405 |
| tail-lights | no_records | - | 2689 |
| tail-lights | not_closed | no_year_manifest | 3157 |
| tailgate | unmapped | - | 405 |
| tailgate | no_records | - | 5842 |
| tailgate | not_closed | no_year_manifest | 4 |
| throttle-body | unmapped | - | 405 |
| throttle-body | no_records | - | 495 |
| throttle-body | not_closed | no_year_manifest | 5351 |
| trunk-lid | unmapped | - | 405 |
| trunk-lid | no_records | - | 2207 |
| trunk-lid | not_closed | no_year_manifest | 3639 |
| window-regulator | unmapped | - | 405 |
| window-regulator | no_records | - | 109 |
| window-regulator | not_closed | no_year_manifest | 5737 |
| window-switch | unmapped | - | 405 |
| window-switch | no_records | - | 1317 |
| window-switch | not_closed | no_year_manifest | 4529 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 405 |
| ac-compressor | no_records | - | 552 |
| ac-compressor | split | option_split | 3389 |
| ac-compressor | conditional | conditional:engine | 79 |
| ac-compressor | conditional | conditional:engine_unattested | 1412 |
| ac-compressor | conditional | conditional:trim | 414 |
| alternator | unmapped | - | 405 |
| alternator | no_records | - | 179 |
| alternator | split | option_split | 2954 |
| alternator | conditional | conditional:engine | 150 |
| alternator | conditional | conditional:engine_unattested | 1472 |
| alternator | conditional | conditional:trim | 1091 |
| bumper-front | unmapped | - | 405 |
| bumper-front | no_records | - | 1535 |
| bumper-front | split | option_split | 2511 |
| bumper-front | conditional | conditional:body | 30 |
| bumper-front | conditional | conditional:engine_unattested | 756 |
| bumper-front | conditional | conditional:option | 160 |
| bumper-front | conditional | conditional:plant | 17 |
| bumper-front | conditional | conditional:qualifier | 81 |
| bumper-front | conditional | conditional:trim | 756 |
| bumper-rear | unmapped | - | 405 |
| bumper-rear | no_records | - | 1091 |
| bumper-rear | split | option_split | 2449 |
| bumper-rear | conditional | conditional:body | 86 |
| bumper-rear | conditional | conditional:engine | 113 |
| bumper-rear | conditional | conditional:engine_unattested | 1370 |
| bumper-rear | conditional | conditional:qualifier | 95 |
| bumper-rear | conditional | conditional:trim | 642 |
| climate-control | unmapped | - | 405 |
| climate-control | no_records | - | 1266 |
| climate-control | split | option_split | 3839 |
| climate-control | conditional | conditional:colour | 16 |
| climate-control | conditional | conditional:engine_unattested | 211 |
| climate-control | conditional | conditional:trim | 514 |
| door-front | unmapped | - | 405 |
| door-front | no_records | - | 565 |
| door-front | split | option_split | 2316 |
| door-front | split | slot_missing | 384 |
| door-front | conditional | conditional:engine_unattested | 1782 |
| door-front | conditional | conditional:trim | 799 |
| door-rear | unmapped | - | 405 |
| door-rear | no_records | - | 199 |
| door-rear | split | option_split | 2581 |
| door-rear | split | slot_missing | 91 |
| door-rear | conditional | conditional:body | 86 |
| door-rear | conditional | conditional:engine_unattested | 1605 |
| door-rear | conditional | conditional:trim | 1284 |
| fender | unmapped | - | 405 |
| fender | no_records | - | 360 |
| fender | split | option_split | 3170 |
| fender | split | slot_missing | 314 |
| fender | conditional | conditional:body | 30 |
| fender | conditional | conditional:engine_unattested | 998 |
| fender | conditional | conditional:trim | 974 |
| fuel-pump-module | unmapped | - | 405 |
| fuel-pump-module | no_records | - | 869 |
| fuel-pump-module | split | option_split | 3089 |
| fuel-pump-module | conditional | conditional:emissions | 13 |
| fuel-pump-module | conditional | conditional:engine | 56 |
| fuel-pump-module | conditional | conditional:engine_unattested | 707 |
| fuel-pump-module | conditional | conditional:model_other | 81 |
| fuel-pump-module | conditional | conditional:trim | 1031 |
| gauge-cluster | unmapped | - | 405 |
| gauge-cluster | no_records | - | 2769 |
| gauge-cluster | split | option_split | 1702 |
| gauge-cluster | conditional | conditional:body | 56 |
| gauge-cluster | conditional | conditional:engine | 364 |
| gauge-cluster | conditional | conditional:engine_unattested | 190 |
| gauge-cluster | conditional | conditional:production | 91 |
| gauge-cluster | conditional | conditional:trim | 674 |
| grille | unmapped | - | 405 |
| grille | no_records | - | 2696 |
| grille | split | option_split | 1842 |
| grille | conditional | conditional:body | 30 |
| grille | conditional | conditional:colour | 13 |
| grille | conditional | conditional:engine_unattested | 359 |
| grille | conditional | conditional:option | 44 |
| grille | conditional | conditional:trim | 862 |
| headlights | unmapped | - | 405 |
| headlights | no_records | - | 1420 |
| headlights | split | option_split | 3865 |
| headlights | conditional | conditional:engine_unattested | 141 |
| headlights | conditional | conditional:trim | 420 |
| hood | unmapped | - | 405 |
| hood | no_records | - | 369 |
| hood | split | option_split | 2316 |
| hood | conditional | conditional:engine_unattested | 1773 |
| hood | conditional | conditional:trim | 1388 |
| ignition-coils | unmapped | - | 405 |
| ignition-coils | no_records | - | 477 |
| ignition-coils | split | option_split | 2158 |
| ignition-coils | conditional | conditional:engine | 72 |
| ignition-coils | conditional | conditional:engine_unattested | 1320 |
| ignition-coils | conditional | conditional:trim | 1819 |
| liftgate | unmapped | - | 405 |
| liftgate | no_records | - | 2048 |
| liftgate | split | option_split | 2671 |
| liftgate | conditional | conditional:engine_unattested | 389 |
| liftgate | conditional | conditional:trim | 738 |
| power-steering-pump | unmapped | - | 405 |
| power-steering-pump | no_records | - | 2326 |
| power-steering-pump | split | option_split | 1940 |
| power-steering-pump | conditional | conditional:engine | 122 |
| power-steering-pump | conditional | conditional:engine_unattested | 1129 |
| power-steering-pump | conditional | conditional:trim | 329 |
| radiator | unmapped | - | 405 |
| radiator | no_records | - | 685 |
| radiator | split | option_split | 3165 |
| radiator | conditional | conditional:engine | 452 |
| radiator | conditional | conditional:engine_unattested | 880 |
| radiator | conditional | conditional:trans | 36 |
| radiator | conditional | conditional:trim | 628 |
| side-mirrors | unmapped | - | 405 |
| side-mirrors | no_records | - | 980 |
| side-mirrors | split | option_split | 4087 |
| side-mirrors | split | slot_missing | 174 |
| side-mirrors | conditional | conditional:colour | 23 |
| side-mirrors | conditional | conditional:engine_unattested | 316 |
| side-mirrors | conditional | conditional:option | 92 |
| side-mirrors | conditional | conditional:trim | 174 |
| starter | unmapped | - | 405 |
| starter | no_records | - | 320 |
| starter | split | option_split | 4232 |
| starter | conditional | conditional:engine_unattested | 855 |
| starter | conditional | conditional:trim | 439 |
| tail-lights | unmapped | - | 405 |
| tail-lights | no_records | - | 2689 |
| tail-lights | split | option_split | 2355 |
| tail-lights | split | position_missing | 428 |
| tail-lights | split | slot_missing | 67 |
| tail-lights | conditional | conditional:engine_unattested | 307 |
| tailgate | unmapped | - | 405 |
| tailgate | no_records | - | 5842 |
| tailgate | conditional | conditional:engine_unattested | 4 |
| throttle-body | unmapped | - | 405 |
| throttle-body | no_records | - | 495 |
| throttle-body | split | option_split | 3500 |
| throttle-body | conditional | conditional:engine_unattested | 1081 |
| throttle-body | conditional | conditional:trim | 770 |
| trunk-lid | unmapped | - | 405 |
| trunk-lid | no_records | - | 2207 |
| trunk-lid | split | option_split | 1484 |
| trunk-lid | conditional | conditional:engine_unattested | 181 |
| trunk-lid | conditional | conditional:option | 35 |
| trunk-lid | conditional | conditional:trim | 1939 |
| window-regulator | unmapped | - | 405 |
| window-regulator | no_records | - | 109 |
| window-regulator | split | packaging_incomplete | 342 |
| window-regulator | split | packaging_split | 368 |
| window-regulator | split | packaging_unstated | 5027 |
| window-switch | unmapped | - | 405 |
| window-switch | no_records | - | 1317 |
| window-switch | split | option_split | 296 |
| window-switch | split | position_missing | 2842 |
| window-switch | conditional | conditional:engine_unattested | 1152 |
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
- Mazda B2300: feed 'B2300' 29 cars
- Mazda B2600: feed 'B2600' 4 cars
- Mazda B3000: feed 'B3000' 21 cars
- Mazda B4000: feed 'B4000' 10 cars
- Mazda CX-70: feed 'CX-70' 0 cars
- Mazda CX-90: feed 'CX-90' 0 cars
- Mazda MX-30 EV: feed 'MX-30 EV' 0 cars
- Mazda MX-5 Miata: feed 'MX-5 Miata' 107 cars
- Mazda Miata: feed 'MX-5 Miata' 107 cars
