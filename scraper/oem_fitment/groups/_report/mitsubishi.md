# OEM curation report: mitsubishi

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-05T09:25:16Z.

- records 452, classes 452, list rows 0, year manifests 0, cells 1474
- Verified groups 0, engine vg groups 0, Likely groups 0
- blocked sites: none

## Gates standing for the whole namespace

- no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close (C1/C2); Verified is impossible by design until the crawler writes them
- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.mitsubishipartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 102 |
| ac-compressor | no_records | - | 1025 |
| ac-compressor | not_closed | no_year_manifest | 1868 |
| alternator | unmapped | - | 102 |
| alternator | no_records | - | 2089 |
| alternator | not_closed | no_year_manifest | 804 |
| bumper-front | unmapped | - | 102 |
| bumper-front | no_records | - | 1508 |
| bumper-front | not_closed | no_year_manifest | 1385 |
| bumper-rear | unmapped | - | 102 |
| bumper-rear | no_records | - | 1677 |
| bumper-rear | not_closed | no_year_manifest | 1216 |
| climate-control | unmapped | - | 102 |
| climate-control | no_records | - | 1434 |
| climate-control | not_closed | no_year_manifest | 1459 |
| door-front | unmapped | - | 102 |
| door-front | no_records | - | 1323 |
| door-front | not_closed | no_year_manifest | 1570 |
| door-rear | unmapped | - | 102 |
| door-rear | no_records | - | 1652 |
| door-rear | not_closed | no_year_manifest | 1241 |
| fender | unmapped | - | 102 |
| fender | no_records | - | 1322 |
| fender | not_closed | no_year_manifest | 1571 |
| fuel-pump-module | unmapped | - | 102 |
| fuel-pump-module | no_records | - | 929 |
| fuel-pump-module | not_closed | no_year_manifest | 1964 |
| gauge-cluster | unmapped | - | 102 |
| gauge-cluster | no_records | - | 2391 |
| gauge-cluster | not_closed | no_year_manifest | 502 |
| grille | unmapped | - | 102 |
| grille | no_records | - | 2365 |
| grille | not_closed | no_year_manifest | 528 |
| headlights | unmapped | - | 102 |
| headlights | no_records | - | 853 |
| headlights | not_closed | no_year_manifest | 2040 |
| hood | unmapped | - | 102 |
| hood | no_records | - | 1267 |
| hood | not_closed | no_year_manifest | 1626 |
| ignition-coils | unmapped | - | 102 |
| ignition-coils | no_records | - | 399 |
| ignition-coils | not_closed | no_year_manifest | 2494 |
| liftgate | unmapped | - | 102 |
| liftgate | no_records | - | 2313 |
| liftgate | not_closed | no_year_manifest | 580 |
| power-steering-pump | unmapped | - | 102 |
| power-steering-pump | no_records | - | 1798 |
| power-steering-pump | not_closed | no_year_manifest | 1095 |
| radiator | unmapped | - | 102 |
| radiator | no_records | - | 486 |
| radiator | not_closed | no_year_manifest | 2407 |
| side-mirrors | unmapped | - | 102 |
| side-mirrors | no_records | - | 1431 |
| side-mirrors | not_closed | no_year_manifest | 1462 |
| starter | unmapped | - | 102 |
| starter | no_records | - | 1333 |
| starter | not_closed | no_year_manifest | 1560 |
| tail-lights | unmapped | - | 102 |
| tail-lights | no_records | - | 1435 |
| tail-lights | not_closed | no_year_manifest | 1458 |
| tailgate | unmapped | - | 102 |
| tailgate | no_records | - | 2722 |
| tailgate | not_closed | no_year_manifest | 171 |
| throttle-body | unmapped | - | 102 |
| throttle-body | no_records | - | 1173 |
| throttle-body | not_closed | no_year_manifest | 1720 |
| trunk-lid | unmapped | - | 102 |
| trunk-lid | no_records | - | 2045 |
| trunk-lid | not_closed | no_year_manifest | 848 |
| window-regulator | unmapped | - | 102 |
| window-regulator | no_records | - | 620 |
| window-regulator | not_closed | no_year_manifest | 2273 |
| window-switch | unmapped | - | 102 |
| window-switch | no_records | - | 1430 |
| window-switch | not_closed | no_year_manifest | 1463 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 102 |
| ac-compressor | no_records | - | 1025 |
| ac-compressor | split | option_split | 849 |
| ac-compressor | conditional | conditional:engine | 66 |
| ac-compressor | conditional | conditional:engine_unattested | 842 |
| ac-compressor | conditional | conditional:trim | 111 |
| alternator | unmapped | - | 102 |
| alternator | no_records | - | 2089 |
| alternator | split | option_split | 41 |
| alternator | conditional | conditional:colour | 56 |
| alternator | conditional | conditional:engine_unattested | 222 |
| alternator | conditional | conditional:production | 53 |
| alternator | conditional | conditional:trim | 432 |
| bumper-front | unmapped | - | 102 |
| bumper-front | no_records | - | 1508 |
| bumper-front | split | option_split | 396 |
| bumper-front | conditional | conditional:colour | 55 |
| bumper-front | conditional | conditional:engine_unattested | 137 |
| bumper-front | conditional | conditional:option | 43 |
| bumper-front | conditional | conditional:qualifier | 353 |
| bumper-front | conditional | conditional:trim | 401 |
| bumper-rear | unmapped | - | 102 |
| bumper-rear | no_records | - | 1677 |
| bumper-rear | split | option_split | 296 |
| bumper-rear | conditional | conditional:body | 13 |
| bumper-rear | conditional | conditional:engine_unattested | 160 |
| bumper-rear | conditional | conditional:qualifier | 213 |
| bumper-rear | conditional | conditional:trim | 534 |
| climate-control | unmapped | - | 102 |
| climate-control | no_records | - | 1434 |
| climate-control | split | option_split | 988 |
| climate-control | conditional | conditional:body | 66 |
| climate-control | conditional | conditional:engine | 44 |
| climate-control | conditional | conditional:engine_unattested | 34 |
| climate-control | conditional | conditional:trim | 327 |
| door-front | unmapped | - | 102 |
| door-front | no_records | - | 1323 |
| door-front | split | option_split | 182 |
| door-front | split | slot_missing | 402 |
| door-front | conditional | conditional:engine_unattested | 501 |
| door-front | conditional | conditional:trim | 485 |
| door-rear | unmapped | - | 102 |
| door-rear | no_records | - | 1652 |
| door-rear | split | option_split | 301 |
| door-rear | split | slot_missing | 314 |
| door-rear | conditional | conditional:body | 13 |
| door-rear | conditional | conditional:engine_unattested | 354 |
| door-rear | conditional | conditional:trim | 259 |
| fender | unmapped | - | 102 |
| fender | no_records | - | 1322 |
| fender | split | option_split | 163 |
| fender | split | slot_missing | 442 |
| fender | conditional | conditional:body | 13 |
| fender | conditional | conditional:engine_unattested | 192 |
| fender | conditional | conditional:production | 27 |
| fender | conditional | conditional:trim | 734 |
| fuel-pump-module | unmapped | - | 102 |
| fuel-pump-module | no_records | - | 929 |
| fuel-pump-module | split | option_split | 798 |
| fuel-pump-module | conditional | conditional:engine | 165 |
| fuel-pump-module | conditional | conditional:engine_unattested | 463 |
| fuel-pump-module | conditional | conditional:trim | 538 |
| gauge-cluster | unmapped | - | 102 |
| gauge-cluster | no_records | - | 2391 |
| gauge-cluster | split | option_split | 323 |
| gauge-cluster | conditional | conditional:trim | 179 |
| grille | unmapped | - | 102 |
| grille | no_records | - | 2365 |
| grille | split | option_split | 76 |
| grille | conditional | conditional:trim | 452 |
| headlights | unmapped | - | 102 |
| headlights | no_records | - | 853 |
| headlights | split | option_split | 1098 |
| headlights | split | position_conflict | 6 |
| headlights | split | position_missing | 18 |
| headlights | split | slot_missing | 745 |
| headlights | conditional | conditional:trim | 173 |
| hood | unmapped | - | 102 |
| hood | no_records | - | 1267 |
| hood | split | option_split | 294 |
| hood | conditional | conditional:body | 13 |
| hood | conditional | conditional:engine_unattested | 315 |
| hood | conditional | conditional:trim | 1004 |
| ignition-coils | unmapped | - | 102 |
| ignition-coils | no_records | - | 399 |
| ignition-coils | split | option_split | 780 |
| ignition-coils | conditional | conditional:engine | 125 |
| ignition-coils | conditional | conditional:engine_unattested | 720 |
| ignition-coils | conditional | conditional:trim | 869 |
| liftgate | unmapped | - | 102 |
| liftgate | no_records | - | 2313 |
| liftgate | split | option_split | 140 |
| liftgate | conditional | conditional:engine_unattested | 124 |
| liftgate | conditional | conditional:qualifier | 36 |
| liftgate | conditional | conditional:trim | 280 |
| power-steering-pump | unmapped | - | 102 |
| power-steering-pump | no_records | - | 1798 |
| power-steering-pump | split | option_split | 830 |
| power-steering-pump | conditional | conditional:engine | 55 |
| power-steering-pump | conditional | conditional:trim | 210 |
| radiator | unmapped | - | 102 |
| radiator | no_records | - | 486 |
| radiator | split | option_split | 1111 |
| radiator | conditional | conditional:engine | 232 |
| radiator | conditional | conditional:engine_unattested | 254 |
| radiator | conditional | conditional:qualifier | 9 |
| radiator | conditional | conditional:trim | 801 |
| side-mirrors | unmapped | - | 102 |
| side-mirrors | no_records | - | 1431 |
| side-mirrors | split | option_split | 691 |
| side-mirrors | split | slot_missing | 381 |
| side-mirrors | conditional | conditional:engine_unattested | 22 |
| side-mirrors | conditional | conditional:trim | 368 |
| starter | unmapped | - | 102 |
| starter | no_records | - | 1333 |
| starter | split | option_split | 249 |
| starter | conditional | conditional:colour | 43 |
| starter | conditional | conditional:engine | 120 |
| starter | conditional | conditional:engine_unattested | 242 |
| starter | conditional | conditional:trans | 5 |
| starter | conditional | conditional:trim | 901 |
| tail-lights | unmapped | - | 102 |
| tail-lights | no_records | - | 1435 |
| tail-lights | split | option_split | 822 |
| tail-lights | split | slot_missing | 261 |
| tail-lights | conditional | conditional:body | 13 |
| tail-lights | conditional | conditional:trim | 362 |
| tailgate | unmapped | - | 102 |
| tailgate | no_records | - | 2722 |
| tailgate | conditional | conditional:engine_unattested | 124 |
| tailgate | conditional | conditional:trim | 47 |
| throttle-body | unmapped | - | 102 |
| throttle-body | no_records | - | 1173 |
| throttle-body | split | option_split | 499 |
| throttle-body | conditional | conditional:colour | 43 |
| throttle-body | conditional | conditional:engine | 121 |
| throttle-body | conditional | conditional:engine_unattested | 349 |
| throttle-body | conditional | conditional:trim | 708 |
| trunk-lid | unmapped | - | 102 |
| trunk-lid | no_records | - | 2045 |
| trunk-lid | split | option_split | 397 |
| trunk-lid | conditional | conditional:option | 62 |
| trunk-lid | conditional | conditional:trim | 389 |
| window-regulator | unmapped | - | 102 |
| window-regulator | no_records | - | 620 |
| window-regulator | split | packaging_unstated | 2273 |
| window-switch | unmapped | - | 102 |
| window-switch | no_records | - | 1430 |
| window-switch | split | option_split | 811 |
| window-switch | split | position_missing | 525 |
| window-switch | conditional | conditional:colour | 56 |
| window-switch | conditional | conditional:production | 9 |
| window-switch | conditional | conditional:trim | 62 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- evidence_mismatch: 1
- systemic_evidence_failure: 1

## Unknown note clauses (top 30)

- `Without Hybrid`: 25
- `With Power Mirror`: 17
- `Without Ralliart`: 16
- `ES`: 13
- `All`: 10
- `With Heated Glass`: 9
- `With Turn Lamp`: 8
- `Without Heated Glass`: 8
- `Limited & SE Without Defog`: 7
- `DE`: 6
- `Without Surround View`: 6
- `California`: 5
- `FWD`: 4
- `LED Without LED High Beam`: 4
- `LS`: 4
- `Lift Gate Lamps`: 4
- `With One Touch`: 4
- `Without Black/Clear`: 4
- `Without Turn Lamp`: 4
- `3000 GT`: 3
- `AWD`: 3
- `GTS`: 3
- `With Projector Type`: 3
- `With Turbo`: 3
- `Without One Touch`: 3
- `Without Projector Type`: 3
- `Without Turbo`: 3
- `3.0 & 3.5L`: 2
- `Fr 10/03/2013`: 2
- `GTS & Ralliart`: 2

## Unmapped catalog models

- Mitsubishi Outlander PHEV: feed 'Outlander PHEV' 0 cars
- Mitsubishi Tredia: feed 'Tredia' 0 cars
