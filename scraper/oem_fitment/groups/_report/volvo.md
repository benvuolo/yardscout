# OEM curation report: volvo

Raw: `3b4677ae1df7` @ `3b4677ae1df7`; as of 2026-11-05T12:14:35Z.

- records 964, classes 964, list rows 0, year manifests 0, cells 2606
- Verified groups 0, engine vg groups 0, Likely groups 0
- blocked sites: none

## Gates standing for the whole namespace

- no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close (C1/C2); Verified is impossible by design until the crawler writes them
- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.volvopartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 147 |
| ac-compressor | no_records | - | 381 |
| ac-compressor | not_closed | no_year_manifest | 1935 |
| alternator | unmapped | - | 147 |
| alternator | no_records | - | 168 |
| alternator | not_closed | no_year_manifest | 2148 |
| bumper-front | unmapped | - | 147 |
| bumper-front | no_records | - | 854 |
| bumper-front | not_closed | no_year_manifest | 1462 |
| bumper-rear | unmapped | - | 147 |
| bumper-rear | no_records | - | 785 |
| bumper-rear | not_closed | no_year_manifest | 1531 |
| climate-control | unmapped | - | 147 |
| climate-control | no_records | - | 592 |
| climate-control | not_closed | no_year_manifest | 1724 |
| door-front | unmapped | - | 147 |
| door-front | no_records | - | 535 |
| door-front | not_closed | no_year_manifest | 1781 |
| door-rear | unmapped | - | 147 |
| door-rear | no_records | - | 650 |
| door-rear | not_closed | no_year_manifest | 1666 |
| fender | unmapped | - | 147 |
| fender | no_records | - | 273 |
| fender | not_closed | no_year_manifest | 2043 |
| fuel-pump-module | unmapped | - | 147 |
| fuel-pump-module | no_records | - | 84 |
| fuel-pump-module | not_closed | no_year_manifest | 2232 |
| gauge-cluster | unmapped | - | 147 |
| gauge-cluster | no_records | - | 1133 |
| gauge-cluster | not_closed | no_year_manifest | 1183 |
| grille | unmapped | - | 147 |
| grille | no_records | - | 1375 |
| grille | not_closed | no_year_manifest | 941 |
| headlights | unmapped | - | 147 |
| headlights | no_records | - | 449 |
| headlights | not_closed | no_year_manifest | 1867 |
| hood | unmapped | - | 147 |
| hood | no_records | - | 354 |
| hood | not_closed | no_year_manifest | 1962 |
| ignition-coils | unmapped | - | 147 |
| ignition-coils | no_records | - | 391 |
| ignition-coils | not_closed | no_year_manifest | 1925 |
| liftgate | unmapped | - | 147 |
| liftgate | no_records | - | 1296 |
| liftgate | not_closed | no_year_manifest | 1020 |
| power-steering-pump | unmapped | - | 147 |
| power-steering-pump | no_records | - | 335 |
| power-steering-pump | not_closed | no_year_manifest | 1981 |
| radiator | unmapped | - | 147 |
| radiator | no_records | - | 219 |
| radiator | not_closed | no_year_manifest | 2097 |
| side-mirrors | unmapped | - | 147 |
| side-mirrors | no_records | - | 962 |
| side-mirrors | not_closed | no_year_manifest | 1354 |
| starter | unmapped | - | 147 |
| starter | no_records | - | 202 |
| starter | not_closed | no_year_manifest | 2114 |
| tail-lights | unmapped | - | 147 |
| tail-lights | no_records | - | 848 |
| tail-lights | not_closed | no_year_manifest | 1468 |
| throttle-body | unmapped | - | 147 |
| throttle-body | no_records | - | 285 |
| throttle-body | not_closed | no_year_manifest | 2031 |
| trunk-lid | unmapped | - | 147 |
| trunk-lid | no_records | - | 1314 |
| trunk-lid | not_closed | no_year_manifest | 1002 |
| window-regulator | unmapped | - | 147 |
| window-regulator | no_records | - | 92 |
| window-regulator | not_closed | no_year_manifest | 2224 |
| window-switch | unmapped | - | 147 |
| window-switch | no_records | - | 454 |
| window-switch | not_closed | no_year_manifest | 1862 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 147 |
| ac-compressor | no_records | - | 381 |
| ac-compressor | split | option_split | 613 |
| ac-compressor | conditional | conditional:colour | 1 |
| ac-compressor | conditional | conditional:qualifier | 1318 |
| ac-compressor | conditional | conditional:trim | 3 |
| alternator | unmapped | - | 147 |
| alternator | no_records | - | 168 |
| alternator | split | option_split | 1210 |
| alternator | conditional | conditional:colour | 5 |
| alternator | conditional | conditional:engine | 95 |
| alternator | conditional | conditional:qualifier | 838 |
| bumper-front | unmapped | - | 147 |
| bumper-front | no_records | - | 854 |
| bumper-front | split | option_split | 1411 |
| bumper-front | conditional | conditional:colour | 17 |
| bumper-front | conditional | conditional:engine_unattested | 31 |
| bumper-front | conditional | conditional:trim | 3 |
| bumper-rear | unmapped | - | 147 |
| bumper-rear | no_records | - | 785 |
| bumper-rear | split | option_split | 1369 |
| bumper-rear | conditional | conditional:body | 29 |
| bumper-rear | conditional | conditional:engine_unattested | 52 |
| bumper-rear | conditional | conditional:trim | 81 |
| climate-control | unmapped | - | 147 |
| climate-control | no_records | - | 592 |
| climate-control | split | option_split | 1181 |
| climate-control | conditional | conditional:engine_unattested | 183 |
| climate-control | conditional | conditional:option | 51 |
| climate-control | conditional | conditional:trim | 309 |
| door-front | unmapped | - | 147 |
| door-front | no_records | - | 535 |
| door-front | conditional | conditional:engine_unattested | 1108 |
| door-front | conditional | conditional:trim | 673 |
| door-rear | unmapped | - | 147 |
| door-rear | no_records | - | 650 |
| door-rear | split | slot_missing | 8 |
| door-rear | conditional | conditional:engine_unattested | 1016 |
| door-rear | conditional | conditional:trim | 642 |
| fender | unmapped | - | 147 |
| fender | no_records | - | 273 |
| fender | split | option_split | 121 |
| fender | split | slot_missing | 13 |
| fender | conditional | conditional:engine_unattested | 1390 |
| fender | conditional | conditional:trim | 519 |
| fuel-pump-module | unmapped | - | 147 |
| fuel-pump-module | no_records | - | 84 |
| fuel-pump-module | split | option_split | 1357 |
| fuel-pump-module | conditional | conditional:engine_unattested | 255 |
| fuel-pump-module | conditional | conditional:trim | 620 |
| gauge-cluster | unmapped | - | 147 |
| gauge-cluster | no_records | - | 1133 |
| gauge-cluster | split | option_split | 670 |
| gauge-cluster | conditional | conditional:engine_unattested | 28 |
| gauge-cluster | conditional | conditional:trim | 485 |
| grille | unmapped | - | 147 |
| grille | no_records | - | 1375 |
| grille | split | option_split | 608 |
| grille | conditional | conditional:colour | 10 |
| grille | conditional | conditional:engine_unattested | 44 |
| grille | conditional | conditional:trim | 279 |
| headlights | unmapped | - | 147 |
| headlights | no_records | - | 449 |
| headlights | split | option_split | 1174 |
| headlights | split | slot_missing | 108 |
| headlights | conditional | conditional:engine_unattested | 293 |
| headlights | conditional | conditional:option | 64 |
| headlights | conditional | conditional:trim | 228 |
| hood | unmapped | - | 147 |
| hood | no_records | - | 354 |
| hood | split | option_split | 20 |
| hood | conditional | conditional:engine_unattested | 1243 |
| hood | conditional | conditional:trim | 699 |
| ignition-coils | unmapped | - | 147 |
| ignition-coils | no_records | - | 391 |
| ignition-coils | split | option_split | 996 |
| ignition-coils | conditional | conditional:engine_unattested | 461 |
| ignition-coils | conditional | conditional:trim | 468 |
| liftgate | unmapped | - | 147 |
| liftgate | no_records | - | 1296 |
| liftgate | split | option_split | 23 |
| liftgate | conditional | conditional:engine_unattested | 619 |
| liftgate | conditional | conditional:trim | 378 |
| power-steering-pump | unmapped | - | 147 |
| power-steering-pump | no_records | - | 335 |
| power-steering-pump | split | option_split | 439 |
| power-steering-pump | conditional | conditional:engine_unattested | 566 |
| power-steering-pump | conditional | conditional:trim | 976 |
| radiator | unmapped | - | 147 |
| radiator | no_records | - | 219 |
| radiator | split | option_split | 471 |
| radiator | conditional | conditional:colour | 15 |
| radiator | conditional | conditional:engine | 177 |
| radiator | conditional | conditional:engine_unattested | 436 |
| radiator | conditional | conditional:model_other | 46 |
| radiator | conditional | conditional:trans | 21 |
| radiator | conditional | conditional:trim | 931 |
| side-mirrors | unmapped | - | 147 |
| side-mirrors | no_records | - | 962 |
| side-mirrors | split | option_split | 1256 |
| side-mirrors | split | slot_missing | 68 |
| side-mirrors | conditional | conditional:engine_unattested | 30 |
| starter | unmapped | - | 147 |
| starter | no_records | - | 202 |
| starter | split | option_split | 829 |
| starter | conditional | conditional:engine_unattested | 546 |
| starter | conditional | conditional:trim | 739 |
| tail-lights | unmapped | - | 147 |
| tail-lights | no_records | - | 848 |
| tail-lights | split | option_split | 427 |
| tail-lights | split | slot_missing | 140 |
| tail-lights | conditional | conditional:engine_unattested | 225 |
| tail-lights | conditional | conditional:trim | 676 |
| throttle-body | unmapped | - | 147 |
| throttle-body | no_records | - | 285 |
| throttle-body | split | option_split | 1443 |
| throttle-body | conditional | conditional:engine | 2 |
| throttle-body | conditional | conditional:engine_unattested | 270 |
| throttle-body | conditional | conditional:trim | 316 |
| trunk-lid | unmapped | - | 147 |
| trunk-lid | no_records | - | 1314 |
| trunk-lid | conditional | conditional:engine_unattested | 582 |
| trunk-lid | conditional | conditional:trim | 420 |
| window-regulator | unmapped | - | 147 |
| window-regulator | no_records | - | 92 |
| window-regulator | split | packaging_incomplete | 46 |
| window-regulator | split | packaging_unstated | 2178 |
| window-switch | unmapped | - | 147 |
| window-switch | no_records | - | 454 |
| window-switch | split | option_split | 777 |
| window-switch | split | position_missing | 859 |
| window-switch | conditional | conditional:body | 1 |
| window-switch | conditional | conditional:model_other | 79 |
| window-switch | conditional | conditional:trim | 146 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_pn: 2

## Unknown note clauses (top 30)

- `Without Park Assist`: 61
- `With Park Assist`: 59
- `With Headlamp Washer`: 32
- `2001-04 Without S60R`: 31
- `Without Headlamp Washer`: 31
- `Primed`: 29
- `With Illumination`: 28
- `From Ch# 184399`: 23
- `Ice White`: 23
- `From Ch# 190000`: 22
- `Electric Silver`: 21
- `Without V70R`: 21
- `With Lamp Washer With Fog Lamps`: 20
- `With Lamp Washer Without Fog Lamps`: 20
- `Without Lamp Washer With Fog Lamps`: 20
- `Without Lamp Washer Without Fog Lamps`: 20
- `Painted With Lamp Washer`: 18
- `Painted Without Lamp Washer`: 18
- `Without Headlamp Washers`: 17
- `Without Upper Molding`: 17
- `Mistral Green`: 16
- `With Headlamp Washers`: 16
- `Caspian Blue`: 14
- `With Reverse Sensor`: 14
- `Without Reverse Sensor`: 14
- `Without Turbo`: 14
- `Black Stone`: 13
- `Black Sapphire`: 12
- `With Turbo`: 12
- `With XC`: 12

## Unmapped catalog models

- Volvo 240: feed '240' 51 cars
- Volvo 242: feed '242' 0 cars
