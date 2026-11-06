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
| ac-compressor | unmapped | - | 409 |
| ac-compressor | no_records | - | 553 |
| ac-compressor | not_closed | no_year_manifest | 5267 |
| alternator | unmapped | - | 409 |
| alternator | no_records | - | 180 |
| alternator | not_closed | no_year_manifest | 5640 |
| bumper-front | unmapped | - | 409 |
| bumper-front | no_records | - | 1529 |
| bumper-front | not_closed | no_year_manifest | 4291 |
| bumper-rear | unmapped | - | 409 |
| bumper-rear | no_records | - | 1089 |
| bumper-rear | not_closed | no_year_manifest | 4731 |
| climate-control | unmapped | - | 409 |
| climate-control | no_records | - | 1255 |
| climate-control | not_closed | no_year_manifest | 4565 |
| door-front | unmapped | - | 409 |
| door-front | no_records | - | 561 |
| door-front | not_closed | no_year_manifest | 5259 |
| door-rear | unmapped | - | 409 |
| door-rear | no_records | - | 195 |
| door-rear | not_closed | no_year_manifest | 5625 |
| fender | unmapped | - | 409 |
| fender | no_records | - | 362 |
| fender | not_closed | no_year_manifest | 5458 |
| fuel-pump-module | unmapped | - | 409 |
| fuel-pump-module | no_records | - | 858 |
| fuel-pump-module | not_closed | no_year_manifest | 4962 |
| gauge-cluster | unmapped | - | 409 |
| gauge-cluster | no_records | - | 2754 |
| gauge-cluster | not_closed | no_year_manifest | 3066 |
| grille | unmapped | - | 409 |
| grille | no_records | - | 2689 |
| grille | not_closed | no_year_manifest | 3131 |
| headlights | unmapped | - | 409 |
| headlights | no_records | - | 1433 |
| headlights | not_closed | no_year_manifest | 4387 |
| hood | unmapped | - | 409 |
| hood | no_records | - | 367 |
| hood | not_closed | no_year_manifest | 5453 |
| ignition-coils | unmapped | - | 409 |
| ignition-coils | no_records | - | 477 |
| ignition-coils | not_closed | no_year_manifest | 5343 |
| liftgate | unmapped | - | 409 |
| liftgate | no_records | - | 2048 |
| liftgate | not_closed | no_year_manifest | 3772 |
| power-steering-pump | unmapped | - | 409 |
| power-steering-pump | no_records | - | 2317 |
| power-steering-pump | not_closed | no_year_manifest | 3503 |
| radiator | unmapped | - | 409 |
| radiator | no_records | - | 693 |
| radiator | not_closed | no_year_manifest | 5127 |
| side-mirrors | unmapped | - | 409 |
| side-mirrors | no_records | - | 978 |
| side-mirrors | not_closed | no_year_manifest | 4842 |
| starter | unmapped | - | 409 |
| starter | no_records | - | 319 |
| starter | not_closed | no_year_manifest | 5501 |
| tail-lights | unmapped | - | 409 |
| tail-lights | no_records | - | 2680 |
| tail-lights | not_closed | no_year_manifest | 3140 |
| tailgate | unmapped | - | 409 |
| tailgate | no_records | - | 5816 |
| tailgate | not_closed | no_year_manifest | 4 |
| throttle-body | unmapped | - | 409 |
| throttle-body | no_records | - | 502 |
| throttle-body | not_closed | no_year_manifest | 5318 |
| trunk-lid | unmapped | - | 409 |
| trunk-lid | no_records | - | 2203 |
| trunk-lid | not_closed | no_year_manifest | 3617 |
| window-regulator | unmapped | - | 409 |
| window-regulator | no_records | - | 105 |
| window-regulator | not_closed | no_year_manifest | 5715 |
| window-switch | unmapped | - | 409 |
| window-switch | no_records | - | 1319 |
| window-switch | not_closed | no_year_manifest | 4501 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 409 |
| ac-compressor | no_records | - | 553 |
| ac-compressor | split | option_split | 3366 |
| ac-compressor | conditional | conditional:engine | 80 |
| ac-compressor | conditional | conditional:engine_unattested | 1408 |
| ac-compressor | conditional | conditional:trim | 413 |
| alternator | unmapped | - | 409 |
| alternator | no_records | - | 180 |
| alternator | split | option_split | 2939 |
| alternator | conditional | conditional:engine | 155 |
| alternator | conditional | conditional:engine_unattested | 1463 |
| alternator | conditional | conditional:trim | 1083 |
| bumper-front | unmapped | - | 409 |
| bumper-front | no_records | - | 1529 |
| bumper-front | split | option_split | 2504 |
| bumper-front | conditional | conditional:body | 29 |
| bumper-front | conditional | conditional:engine_unattested | 750 |
| bumper-front | conditional | conditional:option | 160 |
| bumper-front | conditional | conditional:plant | 17 |
| bumper-front | conditional | conditional:qualifier | 79 |
| bumper-front | conditional | conditional:trim | 752 |
| bumper-rear | unmapped | - | 409 |
| bumper-rear | no_records | - | 1089 |
| bumper-rear | split | option_split | 2441 |
| bumper-rear | conditional | conditional:body | 86 |
| bumper-rear | conditional | conditional:engine | 110 |
| bumper-rear | conditional | conditional:engine_unattested | 1360 |
| bumper-rear | conditional | conditional:qualifier | 94 |
| bumper-rear | conditional | conditional:trim | 640 |
| climate-control | unmapped | - | 409 |
| climate-control | no_records | - | 1255 |
| climate-control | split | option_split | 3820 |
| climate-control | conditional | conditional:colour | 16 |
| climate-control | conditional | conditional:engine_unattested | 207 |
| climate-control | conditional | conditional:trim | 522 |
| door-front | unmapped | - | 409 |
| door-front | no_records | - | 561 |
| door-front | split | option_split | 2296 |
| door-front | split | slot_missing | 384 |
| door-front | conditional | conditional:engine_unattested | 1782 |
| door-front | conditional | conditional:trim | 797 |
| door-rear | unmapped | - | 409 |
| door-rear | no_records | - | 195 |
| door-rear | split | option_split | 2553 |
| door-rear | split | slot_missing | 95 |
| door-rear | conditional | conditional:body | 86 |
| door-rear | conditional | conditional:engine_unattested | 1600 |
| door-rear | conditional | conditional:trim | 1291 |
| fender | unmapped | - | 409 |
| fender | no_records | - | 362 |
| fender | split | option_split | 3138 |
| fender | split | slot_missing | 316 |
| fender | conditional | conditional:body | 29 |
| fender | conditional | conditional:engine_unattested | 999 |
| fender | conditional | conditional:trim | 976 |
| fuel-pump-module | unmapped | - | 409 |
| fuel-pump-module | no_records | - | 858 |
| fuel-pump-module | split | option_split | 3061 |
| fuel-pump-module | conditional | conditional:emissions | 14 |
| fuel-pump-module | conditional | conditional:engine | 56 |
| fuel-pump-module | conditional | conditional:engine_unattested | 700 |
| fuel-pump-module | conditional | conditional:model_other | 84 |
| fuel-pump-module | conditional | conditional:trim | 1047 |
| gauge-cluster | unmapped | - | 409 |
| gauge-cluster | no_records | - | 2754 |
| gauge-cluster | split | option_split | 1690 |
| gauge-cluster | conditional | conditional:body | 57 |
| gauge-cluster | conditional | conditional:engine | 359 |
| gauge-cluster | conditional | conditional:engine_unattested | 186 |
| gauge-cluster | conditional | conditional:production | 91 |
| gauge-cluster | conditional | conditional:trim | 683 |
| grille | unmapped | - | 409 |
| grille | no_records | - | 2689 |
| grille | split | option_split | 1821 |
| grille | conditional | conditional:body | 29 |
| grille | conditional | conditional:colour | 14 |
| grille | conditional | conditional:engine_unattested | 358 |
| grille | conditional | conditional:option | 44 |
| grille | conditional | conditional:trim | 865 |
| headlights | unmapped | - | 409 |
| headlights | no_records | - | 1433 |
| headlights | split | option_split | 3833 |
| headlights | conditional | conditional:engine_unattested | 134 |
| headlights | conditional | conditional:trim | 420 |
| hood | unmapped | - | 409 |
| hood | no_records | - | 367 |
| hood | split | option_split | 2296 |
| hood | conditional | conditional:engine_unattested | 1763 |
| hood | conditional | conditional:trim | 1394 |
| ignition-coils | unmapped | - | 409 |
| ignition-coils | no_records | - | 477 |
| ignition-coils | split | option_split | 2145 |
| ignition-coils | conditional | conditional:colour | 3 |
| ignition-coils | conditional | conditional:engine | 72 |
| ignition-coils | conditional | conditional:engine_unattested | 1321 |
| ignition-coils | conditional | conditional:trim | 1802 |
| liftgate | unmapped | - | 409 |
| liftgate | no_records | - | 2048 |
| liftgate | split | option_split | 2652 |
| liftgate | conditional | conditional:engine_unattested | 388 |
| liftgate | conditional | conditional:trim | 732 |
| power-steering-pump | unmapped | - | 409 |
| power-steering-pump | no_records | - | 2317 |
| power-steering-pump | split | option_split | 1925 |
| power-steering-pump | conditional | conditional:engine | 121 |
| power-steering-pump | conditional | conditional:engine_unattested | 1128 |
| power-steering-pump | conditional | conditional:trim | 329 |
| radiator | unmapped | - | 409 |
| radiator | no_records | - | 693 |
| radiator | split | option_split | 3146 |
| radiator | conditional | conditional:colour | 1 |
| radiator | conditional | conditional:engine | 447 |
| radiator | conditional | conditional:engine_unattested | 872 |
| radiator | conditional | conditional:trans | 33 |
| radiator | conditional | conditional:trim | 628 |
| side-mirrors | unmapped | - | 409 |
| side-mirrors | no_records | - | 978 |
| side-mirrors | split | option_split | 4074 |
| side-mirrors | split | slot_missing | 171 |
| side-mirrors | conditional | conditional:colour | 23 |
| side-mirrors | conditional | conditional:engine_unattested | 308 |
| side-mirrors | conditional | conditional:option | 89 |
| side-mirrors | conditional | conditional:trim | 177 |
| starter | unmapped | - | 409 |
| starter | no_records | - | 319 |
| starter | split | option_split | 4202 |
| starter | conditional | conditional:engine_unattested | 849 |
| starter | conditional | conditional:trim | 450 |
| tail-lights | unmapped | - | 409 |
| tail-lights | no_records | - | 2680 |
| tail-lights | split | option_split | 2344 |
| tail-lights | split | position_missing | 430 |
| tail-lights | split | slot_missing | 65 |
| tail-lights | conditional | conditional:engine_unattested | 301 |
| tailgate | unmapped | - | 409 |
| tailgate | no_records | - | 5816 |
| tailgate | conditional | conditional:engine_unattested | 4 |
| throttle-body | unmapped | - | 409 |
| throttle-body | no_records | - | 502 |
| throttle-body | split | option_split | 3485 |
| throttle-body | conditional | conditional:colour | 23 |
| throttle-body | conditional | conditional:engine_unattested | 1043 |
| throttle-body | conditional | conditional:trim | 767 |
| trunk-lid | unmapped | - | 409 |
| trunk-lid | no_records | - | 2203 |
| trunk-lid | split | option_split | 1482 |
| trunk-lid | conditional | conditional:engine_unattested | 181 |
| trunk-lid | conditional | conditional:option | 35 |
| trunk-lid | conditional | conditional:trim | 1919 |
| window-regulator | unmapped | - | 409 |
| window-regulator | no_records | - | 105 |
| window-regulator | split | packaging_incomplete | 347 |
| window-regulator | split | packaging_split | 368 |
| window-regulator | split | packaging_unstated | 5000 |
| window-switch | unmapped | - | 409 |
| window-switch | no_records | - | 1319 |
| window-switch | split | option_split | 299 |
| window-switch | split | position_missing | 2823 |
| window-switch | conditional | conditional:engine_unattested | 1143 |
| window-switch | conditional | conditional:trim | 236 |

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
- Mazda B2300: feed 'B2300' 29 cars
- Mazda B2600: feed 'B2600' 4 cars
- Mazda B3000: feed 'B3000' 18 cars
- Mazda B4000: feed 'B4000' 10 cars
- Mazda CX-70: feed 'CX-70' 0 cars
- Mazda CX-90: feed 'CX-90' 0 cars
- Mazda MX-30 EV: feed 'MX-30 EV' 0 cars
- Mazda MX-5 Miata: feed 'MX-5 Miata' 112 cars
- Mazda Miata: feed 'MX-5 Miata' 112 cars
