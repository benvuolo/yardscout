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
| ac-compressor | unmapped | - | 405 |
| ac-compressor | no_records | - | 557 |
| ac-compressor | not_closed | no_year_manifest | 5280 |
| alternator | unmapped | - | 405 |
| alternator | no_records | - | 180 |
| alternator | not_closed | no_year_manifest | 5657 |
| bumper-front | unmapped | - | 405 |
| bumper-front | no_records | - | 1537 |
| bumper-front | not_closed | no_year_manifest | 4300 |
| bumper-rear | unmapped | - | 405 |
| bumper-rear | no_records | - | 1094 |
| bumper-rear | not_closed | no_year_manifest | 4743 |
| climate-control | unmapped | - | 405 |
| climate-control | no_records | - | 1262 |
| climate-control | not_closed | no_year_manifest | 4575 |
| door-front | unmapped | - | 405 |
| door-front | no_records | - | 563 |
| door-front | not_closed | no_year_manifest | 5274 |
| door-rear | unmapped | - | 405 |
| door-rear | no_records | - | 198 |
| door-rear | not_closed | no_year_manifest | 5639 |
| fender | unmapped | - | 405 |
| fender | no_records | - | 364 |
| fender | not_closed | no_year_manifest | 5473 |
| fuel-pump-module | unmapped | - | 405 |
| fuel-pump-module | no_records | - | 862 |
| fuel-pump-module | not_closed | no_year_manifest | 4975 |
| gauge-cluster | unmapped | - | 405 |
| gauge-cluster | no_records | - | 2762 |
| gauge-cluster | not_closed | no_year_manifest | 3075 |
| grille | unmapped | - | 405 |
| grille | no_records | - | 2699 |
| grille | not_closed | no_year_manifest | 3138 |
| headlights | unmapped | - | 405 |
| headlights | no_records | - | 1431 |
| headlights | not_closed | no_year_manifest | 4406 |
| hood | unmapped | - | 405 |
| hood | no_records | - | 370 |
| hood | not_closed | no_year_manifest | 5467 |
| ignition-coils | unmapped | - | 405 |
| ignition-coils | no_records | - | 481 |
| ignition-coils | not_closed | no_year_manifest | 5356 |
| liftgate | unmapped | - | 405 |
| liftgate | no_records | - | 2049 |
| liftgate | not_closed | no_year_manifest | 3788 |
| power-steering-pump | unmapped | - | 405 |
| power-steering-pump | no_records | - | 2326 |
| power-steering-pump | not_closed | no_year_manifest | 3511 |
| radiator | unmapped | - | 405 |
| radiator | no_records | - | 694 |
| radiator | not_closed | no_year_manifest | 5143 |
| side-mirrors | unmapped | - | 405 |
| side-mirrors | no_records | - | 975 |
| side-mirrors | not_closed | no_year_manifest | 4862 |
| starter | unmapped | - | 405 |
| starter | no_records | - | 318 |
| starter | not_closed | no_year_manifest | 5519 |
| tail-lights | unmapped | - | 405 |
| tail-lights | no_records | - | 2691 |
| tail-lights | not_closed | no_year_manifest | 3146 |
| tailgate | unmapped | - | 405 |
| tailgate | no_records | - | 5833 |
| tailgate | not_closed | no_year_manifest | 4 |
| throttle-body | unmapped | - | 405 |
| throttle-body | no_records | - | 503 |
| throttle-body | not_closed | no_year_manifest | 5334 |
| trunk-lid | unmapped | - | 405 |
| trunk-lid | no_records | - | 2205 |
| trunk-lid | not_closed | no_year_manifest | 3632 |
| window-regulator | unmapped | - | 405 |
| window-regulator | no_records | - | 106 |
| window-regulator | not_closed | no_year_manifest | 5731 |
| window-switch | unmapped | - | 405 |
| window-switch | no_records | - | 1317 |
| window-switch | not_closed | no_year_manifest | 4520 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 405 |
| ac-compressor | no_records | - | 557 |
| ac-compressor | split | option_split | 3380 |
| ac-compressor | conditional | conditional:engine | 80 |
| ac-compressor | conditional | conditional:engine_unattested | 1407 |
| ac-compressor | conditional | conditional:trim | 413 |
| alternator | unmapped | - | 405 |
| alternator | no_records | - | 180 |
| alternator | split | option_split | 2950 |
| alternator | conditional | conditional:engine | 157 |
| alternator | conditional | conditional:engine_unattested | 1463 |
| alternator | conditional | conditional:trim | 1087 |
| bumper-front | unmapped | - | 405 |
| bumper-front | no_records | - | 1537 |
| bumper-front | split | option_split | 2515 |
| bumper-front | conditional | conditional:body | 29 |
| bumper-front | conditional | conditional:engine_unattested | 748 |
| bumper-front | conditional | conditional:option | 161 |
| bumper-front | conditional | conditional:plant | 17 |
| bumper-front | conditional | conditional:qualifier | 79 |
| bumper-front | conditional | conditional:trim | 751 |
| bumper-rear | unmapped | - | 405 |
| bumper-rear | no_records | - | 1094 |
| bumper-rear | split | option_split | 2452 |
| bumper-rear | conditional | conditional:body | 86 |
| bumper-rear | conditional | conditional:engine | 111 |
| bumper-rear | conditional | conditional:engine_unattested | 1362 |
| bumper-rear | conditional | conditional:qualifier | 94 |
| bumper-rear | conditional | conditional:trim | 638 |
| climate-control | unmapped | - | 405 |
| climate-control | no_records | - | 1262 |
| climate-control | split | option_split | 3831 |
| climate-control | conditional | conditional:colour | 16 |
| climate-control | conditional | conditional:engine_unattested | 203 |
| climate-control | conditional | conditional:trim | 525 |
| door-front | unmapped | - | 405 |
| door-front | no_records | - | 563 |
| door-front | split | option_split | 2312 |
| door-front | split | slot_missing | 385 |
| door-front | conditional | conditional:engine_unattested | 1783 |
| door-front | conditional | conditional:trim | 794 |
| door-rear | unmapped | - | 405 |
| door-rear | no_records | - | 198 |
| door-rear | split | option_split | 2570 |
| door-rear | split | slot_missing | 94 |
| door-rear | conditional | conditional:body | 86 |
| door-rear | conditional | conditional:engine_unattested | 1599 |
| door-rear | conditional | conditional:trim | 1290 |
| fender | unmapped | - | 405 |
| fender | no_records | - | 364 |
| fender | split | option_split | 3154 |
| fender | split | slot_missing | 317 |
| fender | conditional | conditional:body | 29 |
| fender | conditional | conditional:engine_unattested | 1001 |
| fender | conditional | conditional:trim | 972 |
| fuel-pump-module | unmapped | - | 405 |
| fuel-pump-module | no_records | - | 862 |
| fuel-pump-module | split | option_split | 3079 |
| fuel-pump-module | conditional | conditional:emissions | 14 |
| fuel-pump-module | conditional | conditional:engine | 57 |
| fuel-pump-module | conditional | conditional:engine_unattested | 699 |
| fuel-pump-module | conditional | conditional:model_other | 86 |
| fuel-pump-module | conditional | conditional:trim | 1040 |
| gauge-cluster | unmapped | - | 405 |
| gauge-cluster | no_records | - | 2762 |
| gauge-cluster | split | option_split | 1694 |
| gauge-cluster | conditional | conditional:body | 57 |
| gauge-cluster | conditional | conditional:engine | 360 |
| gauge-cluster | conditional | conditional:engine_unattested | 183 |
| gauge-cluster | conditional | conditional:production | 92 |
| gauge-cluster | conditional | conditional:trim | 689 |
| grille | unmapped | - | 405 |
| grille | no_records | - | 2699 |
| grille | split | option_split | 1829 |
| grille | conditional | conditional:body | 29 |
| grille | conditional | conditional:colour | 14 |
| grille | conditional | conditional:engine_unattested | 359 |
| grille | conditional | conditional:option | 44 |
| grille | conditional | conditional:trim | 863 |
| headlights | unmapped | - | 405 |
| headlights | no_records | - | 1431 |
| headlights | split | option_split | 3849 |
| headlights | conditional | conditional:engine_unattested | 136 |
| headlights | conditional | conditional:trim | 421 |
| hood | unmapped | - | 405 |
| hood | no_records | - | 370 |
| hood | split | option_split | 2312 |
| hood | conditional | conditional:engine_unattested | 1761 |
| hood | conditional | conditional:trim | 1394 |
| ignition-coils | unmapped | - | 405 |
| ignition-coils | no_records | - | 481 |
| ignition-coils | split | option_split | 2154 |
| ignition-coils | conditional | conditional:colour | 3 |
| ignition-coils | conditional | conditional:engine | 73 |
| ignition-coils | conditional | conditional:engine_unattested | 1316 |
| ignition-coils | conditional | conditional:trim | 1810 |
| liftgate | unmapped | - | 405 |
| liftgate | no_records | - | 2049 |
| liftgate | split | option_split | 2659 |
| liftgate | conditional | conditional:engine_unattested | 389 |
| liftgate | conditional | conditional:trim | 740 |
| power-steering-pump | unmapped | - | 405 |
| power-steering-pump | no_records | - | 2326 |
| power-steering-pump | split | option_split | 1933 |
| power-steering-pump | conditional | conditional:engine | 122 |
| power-steering-pump | conditional | conditional:engine_unattested | 1125 |
| power-steering-pump | conditional | conditional:trim | 331 |
| radiator | unmapped | - | 405 |
| radiator | no_records | - | 694 |
| radiator | split | option_split | 3158 |
| radiator | conditional | conditional:colour | 1 |
| radiator | conditional | conditional:engine | 449 |
| radiator | conditional | conditional:engine_unattested | 872 |
| radiator | conditional | conditional:trans | 34 |
| radiator | conditional | conditional:trim | 629 |
| side-mirrors | unmapped | - | 405 |
| side-mirrors | no_records | - | 975 |
| side-mirrors | split | option_split | 4093 |
| side-mirrors | split | slot_missing | 169 |
| side-mirrors | conditional | conditional:colour | 23 |
| side-mirrors | conditional | conditional:engine_unattested | 307 |
| side-mirrors | conditional | conditional:option | 91 |
| side-mirrors | conditional | conditional:trim | 179 |
| starter | unmapped | - | 405 |
| starter | no_records | - | 318 |
| starter | split | option_split | 4224 |
| starter | conditional | conditional:engine_unattested | 849 |
| starter | conditional | conditional:trim | 446 |
| tail-lights | unmapped | - | 405 |
| tail-lights | no_records | - | 2691 |
| tail-lights | split | option_split | 2351 |
| tail-lights | split | position_missing | 432 |
| tail-lights | split | slot_missing | 65 |
| tail-lights | conditional | conditional:engine_unattested | 298 |
| tailgate | unmapped | - | 405 |
| tailgate | no_records | - | 5833 |
| tailgate | conditional | conditional:engine_unattested | 4 |
| throttle-body | unmapped | - | 405 |
| throttle-body | no_records | - | 503 |
| throttle-body | split | option_split | 3498 |
| throttle-body | conditional | conditional:colour | 23 |
| throttle-body | conditional | conditional:engine_unattested | 1041 |
| throttle-body | conditional | conditional:trim | 772 |
| trunk-lid | unmapped | - | 405 |
| trunk-lid | no_records | - | 2205 |
| trunk-lid | split | option_split | 1487 |
| trunk-lid | conditional | conditional:engine_unattested | 180 |
| trunk-lid | conditional | conditional:option | 35 |
| trunk-lid | conditional | conditional:trim | 1930 |
| window-regulator | unmapped | - | 405 |
| window-regulator | no_records | - | 106 |
| window-regulator | split | packaging_incomplete | 348 |
| window-regulator | split | packaging_split | 370 |
| window-regulator | split | packaging_unstated | 5013 |
| window-switch | unmapped | - | 405 |
| window-switch | no_records | - | 1317 |
| window-switch | split | option_split | 299 |
| window-switch | split | position_missing | 2836 |
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
- Mazda B3000: feed 'B3000' 19 cars
- Mazda B4000: feed 'B4000' 10 cars
- Mazda CX-70: feed 'CX-70' 0 cars
- Mazda CX-90: feed 'CX-90' 0 cars
- Mazda MX-30 EV: feed 'MX-30 EV' 0 cars
- Mazda MX-5 Miata: feed 'MX-5 Miata' 108 cars
- Mazda Miata: feed 'MX-5 Miata' 108 cars
