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
| ac-compressor | unmapped | - | 103 |
| ac-compressor | no_records | - | 1027 |
| ac-compressor | not_closed | no_year_manifest | 1871 |
| alternator | unmapped | - | 103 |
| alternator | no_records | - | 2092 |
| alternator | not_closed | no_year_manifest | 806 |
| bumper-front | unmapped | - | 103 |
| bumper-front | no_records | - | 1507 |
| bumper-front | not_closed | no_year_manifest | 1391 |
| bumper-rear | unmapped | - | 103 |
| bumper-rear | no_records | - | 1676 |
| bumper-rear | not_closed | no_year_manifest | 1222 |
| climate-control | unmapped | - | 103 |
| climate-control | no_records | - | 1436 |
| climate-control | not_closed | no_year_manifest | 1462 |
| door-front | unmapped | - | 103 |
| door-front | no_records | - | 1324 |
| door-front | not_closed | no_year_manifest | 1574 |
| door-rear | unmapped | - | 103 |
| door-rear | no_records | - | 1653 |
| door-rear | not_closed | no_year_manifest | 1245 |
| fender | unmapped | - | 103 |
| fender | no_records | - | 1321 |
| fender | not_closed | no_year_manifest | 1577 |
| fuel-pump-module | unmapped | - | 103 |
| fuel-pump-module | no_records | - | 929 |
| fuel-pump-module | not_closed | no_year_manifest | 1969 |
| gauge-cluster | unmapped | - | 103 |
| gauge-cluster | no_records | - | 2392 |
| gauge-cluster | not_closed | no_year_manifest | 506 |
| grille | unmapped | - | 103 |
| grille | no_records | - | 2368 |
| grille | not_closed | no_year_manifest | 530 |
| headlights | unmapped | - | 103 |
| headlights | no_records | - | 850 |
| headlights | not_closed | no_year_manifest | 2048 |
| hood | unmapped | - | 103 |
| hood | no_records | - | 1266 |
| hood | not_closed | no_year_manifest | 1632 |
| ignition-coils | unmapped | - | 103 |
| ignition-coils | no_records | - | 399 |
| ignition-coils | not_closed | no_year_manifest | 2499 |
| liftgate | unmapped | - | 103 |
| liftgate | no_records | - | 2318 |
| liftgate | not_closed | no_year_manifest | 580 |
| power-steering-pump | unmapped | - | 103 |
| power-steering-pump | no_records | - | 1801 |
| power-steering-pump | not_closed | no_year_manifest | 1097 |
| radiator | unmapped | - | 103 |
| radiator | no_records | - | 485 |
| radiator | not_closed | no_year_manifest | 2413 |
| side-mirrors | unmapped | - | 103 |
| side-mirrors | no_records | - | 1430 |
| side-mirrors | not_closed | no_year_manifest | 1468 |
| starter | unmapped | - | 103 |
| starter | no_records | - | 1339 |
| starter | not_closed | no_year_manifest | 1559 |
| tail-lights | unmapped | - | 103 |
| tail-lights | no_records | - | 1435 |
| tail-lights | not_closed | no_year_manifest | 1463 |
| tailgate | unmapped | - | 103 |
| tailgate | no_records | - | 2728 |
| tailgate | not_closed | no_year_manifest | 170 |
| throttle-body | unmapped | - | 103 |
| throttle-body | no_records | - | 1176 |
| throttle-body | not_closed | no_year_manifest | 1722 |
| trunk-lid | unmapped | - | 103 |
| trunk-lid | no_records | - | 2045 |
| trunk-lid | not_closed | no_year_manifest | 853 |
| window-regulator | unmapped | - | 103 |
| window-regulator | no_records | - | 617 |
| window-regulator | not_closed | no_year_manifest | 2281 |
| window-switch | unmapped | - | 103 |
| window-switch | no_records | - | 1436 |
| window-switch | not_closed | no_year_manifest | 1462 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 103 |
| ac-compressor | no_records | - | 1027 |
| ac-compressor | split | option_split | 853 |
| ac-compressor | conditional | conditional:engine | 66 |
| ac-compressor | conditional | conditional:engine_unattested | 841 |
| ac-compressor | conditional | conditional:trim | 111 |
| alternator | unmapped | - | 103 |
| alternator | no_records | - | 2092 |
| alternator | split | option_split | 40 |
| alternator | conditional | conditional:colour | 57 |
| alternator | conditional | conditional:engine_unattested | 223 |
| alternator | conditional | conditional:production | 54 |
| alternator | conditional | conditional:trim | 432 |
| bumper-front | unmapped | - | 103 |
| bumper-front | no_records | - | 1507 |
| bumper-front | split | option_split | 398 |
| bumper-front | conditional | conditional:colour | 55 |
| bumper-front | conditional | conditional:engine_unattested | 136 |
| bumper-front | conditional | conditional:option | 43 |
| bumper-front | conditional | conditional:qualifier | 356 |
| bumper-front | conditional | conditional:trim | 403 |
| bumper-rear | unmapped | - | 103 |
| bumper-rear | no_records | - | 1676 |
| bumper-rear | split | option_split | 298 |
| bumper-rear | conditional | conditional:body | 14 |
| bumper-rear | conditional | conditional:engine_unattested | 161 |
| bumper-rear | conditional | conditional:qualifier | 215 |
| bumper-rear | conditional | conditional:trim | 534 |
| climate-control | unmapped | - | 103 |
| climate-control | no_records | - | 1436 |
| climate-control | split | option_split | 992 |
| climate-control | conditional | conditional:body | 66 |
| climate-control | conditional | conditional:engine | 44 |
| climate-control | conditional | conditional:engine_unattested | 33 |
| climate-control | conditional | conditional:trim | 327 |
| door-front | unmapped | - | 103 |
| door-front | no_records | - | 1324 |
| door-front | split | option_split | 183 |
| door-front | split | slot_missing | 403 |
| door-front | conditional | conditional:engine_unattested | 500 |
| door-front | conditional | conditional:trim | 488 |
| door-rear | unmapped | - | 103 |
| door-rear | no_records | - | 1653 |
| door-rear | split | option_split | 305 |
| door-rear | split | slot_missing | 312 |
| door-rear | conditional | conditional:body | 14 |
| door-rear | conditional | conditional:engine_unattested | 355 |
| door-rear | conditional | conditional:trim | 259 |
| fender | unmapped | - | 103 |
| fender | no_records | - | 1321 |
| fender | split | option_split | 166 |
| fender | split | slot_missing | 443 |
| fender | conditional | conditional:body | 14 |
| fender | conditional | conditional:engine_unattested | 191 |
| fender | conditional | conditional:production | 27 |
| fender | conditional | conditional:trim | 736 |
| fuel-pump-module | unmapped | - | 103 |
| fuel-pump-module | no_records | - | 929 |
| fuel-pump-module | split | option_split | 801 |
| fuel-pump-module | conditional | conditional:engine | 165 |
| fuel-pump-module | conditional | conditional:engine_unattested | 466 |
| fuel-pump-module | conditional | conditional:trim | 537 |
| gauge-cluster | unmapped | - | 103 |
| gauge-cluster | no_records | - | 2392 |
| gauge-cluster | split | option_split | 326 |
| gauge-cluster | conditional | conditional:trim | 180 |
| grille | unmapped | - | 103 |
| grille | no_records | - | 2368 |
| grille | split | option_split | 77 |
| grille | conditional | conditional:trim | 453 |
| headlights | unmapped | - | 103 |
| headlights | no_records | - | 850 |
| headlights | split | option_split | 1100 |
| headlights | split | position_conflict | 6 |
| headlights | split | position_missing | 18 |
| headlights | split | slot_missing | 750 |
| headlights | conditional | conditional:trim | 174 |
| hood | unmapped | - | 103 |
| hood | no_records | - | 1266 |
| hood | split | option_split | 298 |
| hood | conditional | conditional:body | 14 |
| hood | conditional | conditional:engine_unattested | 316 |
| hood | conditional | conditional:trim | 1004 |
| ignition-coils | unmapped | - | 103 |
| ignition-coils | no_records | - | 399 |
| ignition-coils | split | option_split | 780 |
| ignition-coils | conditional | conditional:engine | 125 |
| ignition-coils | conditional | conditional:engine_unattested | 720 |
| ignition-coils | conditional | conditional:trim | 874 |
| liftgate | unmapped | - | 103 |
| liftgate | no_records | - | 2318 |
| liftgate | split | option_split | 140 |
| liftgate | conditional | conditional:engine_unattested | 123 |
| liftgate | conditional | conditional:qualifier | 36 |
| liftgate | conditional | conditional:trim | 281 |
| power-steering-pump | unmapped | - | 103 |
| power-steering-pump | no_records | - | 1801 |
| power-steering-pump | split | option_split | 830 |
| power-steering-pump | conditional | conditional:engine | 55 |
| power-steering-pump | conditional | conditional:trim | 212 |
| radiator | unmapped | - | 103 |
| radiator | no_records | - | 485 |
| radiator | split | option_split | 1119 |
| radiator | conditional | conditional:engine | 232 |
| radiator | conditional | conditional:engine_unattested | 255 |
| radiator | conditional | conditional:qualifier | 9 |
| radiator | conditional | conditional:trim | 798 |
| side-mirrors | unmapped | - | 103 |
| side-mirrors | no_records | - | 1430 |
| side-mirrors | split | option_split | 692 |
| side-mirrors | split | slot_missing | 383 |
| side-mirrors | conditional | conditional:engine_unattested | 22 |
| side-mirrors | conditional | conditional:trim | 371 |
| starter | unmapped | - | 103 |
| starter | no_records | - | 1339 |
| starter | split | option_split | 247 |
| starter | conditional | conditional:colour | 43 |
| starter | conditional | conditional:engine | 120 |
| starter | conditional | conditional:engine_unattested | 243 |
| starter | conditional | conditional:trans | 5 |
| starter | conditional | conditional:trim | 901 |
| tail-lights | unmapped | - | 103 |
| tail-lights | no_records | - | 1435 |
| tail-lights | split | option_split | 823 |
| tail-lights | split | slot_missing | 263 |
| tail-lights | conditional | conditional:body | 14 |
| tail-lights | conditional | conditional:trim | 363 |
| tailgate | unmapped | - | 103 |
| tailgate | no_records | - | 2728 |
| tailgate | conditional | conditional:engine_unattested | 123 |
| tailgate | conditional | conditional:trim | 47 |
| throttle-body | unmapped | - | 103 |
| throttle-body | no_records | - | 1176 |
| throttle-body | split | option_split | 501 |
| throttle-body | conditional | conditional:colour | 43 |
| throttle-body | conditional | conditional:engine | 121 |
| throttle-body | conditional | conditional:engine_unattested | 351 |
| throttle-body | conditional | conditional:trim | 706 |
| trunk-lid | unmapped | - | 103 |
| trunk-lid | no_records | - | 2045 |
| trunk-lid | split | option_split | 401 |
| trunk-lid | conditional | conditional:option | 62 |
| trunk-lid | conditional | conditional:trim | 390 |
| window-regulator | unmapped | - | 103 |
| window-regulator | no_records | - | 617 |
| window-regulator | split | packaging_unstated | 2281 |
| window-switch | unmapped | - | 103 |
| window-switch | no_records | - | 1436 |
| window-switch | split | option_split | 812 |
| window-switch | split | position_missing | 522 |
| window-switch | conditional | conditional:colour | 57 |
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
