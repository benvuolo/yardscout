# OEM curation report: mitsubishi

Raw: `dca9cd845f26` @ `dca9cd845f26`; as of 2026-11-05T09:25:16Z.

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
| ac-compressor | unmapped | - | 101 |
| ac-compressor | no_records | - | 1032 |
| ac-compressor | not_closed | no_year_manifest | 1856 |
| alternator | unmapped | - | 101 |
| alternator | no_records | - | 2077 |
| alternator | not_closed | no_year_manifest | 811 |
| bumper-front | unmapped | - | 101 |
| bumper-front | no_records | - | 1508 |
| bumper-front | not_closed | no_year_manifest | 1380 |
| bumper-rear | unmapped | - | 101 |
| bumper-rear | no_records | - | 1670 |
| bumper-rear | not_closed | no_year_manifest | 1218 |
| climate-control | unmapped | - | 101 |
| climate-control | no_records | - | 1439 |
| climate-control | not_closed | no_year_manifest | 1449 |
| door-front | unmapped | - | 101 |
| door-front | no_records | - | 1315 |
| door-front | not_closed | no_year_manifest | 1573 |
| door-rear | unmapped | - | 101 |
| door-rear | no_records | - | 1643 |
| door-rear | not_closed | no_year_manifest | 1245 |
| fender | unmapped | - | 101 |
| fender | no_records | - | 1317 |
| fender | not_closed | no_year_manifest | 1571 |
| fuel-pump-module | unmapped | - | 101 |
| fuel-pump-module | no_records | - | 929 |
| fuel-pump-module | not_closed | no_year_manifest | 1959 |
| gauge-cluster | unmapped | - | 101 |
| gauge-cluster | no_records | - | 2380 |
| gauge-cluster | not_closed | no_year_manifest | 508 |
| grille | unmapped | - | 101 |
| grille | no_records | - | 2364 |
| grille | not_closed | no_year_manifest | 524 |
| headlights | unmapped | - | 101 |
| headlights | no_records | - | 855 |
| headlights | not_closed | no_year_manifest | 2033 |
| hood | unmapped | - | 101 |
| hood | no_records | - | 1268 |
| hood | not_closed | no_year_manifest | 1620 |
| ignition-coils | unmapped | - | 101 |
| ignition-coils | no_records | - | 399 |
| ignition-coils | not_closed | no_year_manifest | 2489 |
| liftgate | unmapped | - | 101 |
| liftgate | no_records | - | 2300 |
| liftgate | not_closed | no_year_manifest | 588 |
| power-steering-pump | unmapped | - | 101 |
| power-steering-pump | no_records | - | 1805 |
| power-steering-pump | not_closed | no_year_manifest | 1083 |
| radiator | unmapped | - | 101 |
| radiator | no_records | - | 480 |
| radiator | not_closed | no_year_manifest | 2408 |
| side-mirrors | unmapped | - | 101 |
| side-mirrors | no_records | - | 1430 |
| side-mirrors | not_closed | no_year_manifest | 1458 |
| starter | unmapped | - | 101 |
| starter | no_records | - | 1325 |
| starter | not_closed | no_year_manifest | 1563 |
| tail-lights | unmapped | - | 101 |
| tail-lights | no_records | - | 1427 |
| tail-lights | not_closed | no_year_manifest | 1461 |
| tailgate | unmapped | - | 101 |
| tailgate | no_records | - | 2715 |
| tailgate | not_closed | no_year_manifest | 173 |
| throttle-body | unmapped | - | 101 |
| throttle-body | no_records | - | 1168 |
| throttle-body | not_closed | no_year_manifest | 1720 |
| trunk-lid | unmapped | - | 101 |
| trunk-lid | no_records | - | 2042 |
| trunk-lid | not_closed | no_year_manifest | 846 |
| window-regulator | unmapped | - | 101 |
| window-regulator | no_records | - | 609 |
| window-regulator | not_closed | no_year_manifest | 2279 |
| window-switch | unmapped | - | 101 |
| window-switch | no_records | - | 1426 |
| window-switch | not_closed | no_year_manifest | 1462 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 101 |
| ac-compressor | no_records | - | 1032 |
| ac-compressor | split | option_split | 851 |
| ac-compressor | conditional | conditional:engine | 64 |
| ac-compressor | conditional | conditional:engine_unattested | 830 |
| ac-compressor | conditional | conditional:trim | 111 |
| alternator | unmapped | - | 101 |
| alternator | no_records | - | 2077 |
| alternator | split | option_split | 40 |
| alternator | conditional | conditional:colour | 58 |
| alternator | conditional | conditional:engine_unattested | 225 |
| alternator | conditional | conditional:production | 54 |
| alternator | conditional | conditional:trim | 434 |
| bumper-front | unmapped | - | 101 |
| bumper-front | no_records | - | 1508 |
| bumper-front | split | option_split | 395 |
| bumper-front | conditional | conditional:colour | 57 |
| bumper-front | conditional | conditional:engine_unattested | 131 |
| bumper-front | conditional | conditional:option | 44 |
| bumper-front | conditional | conditional:qualifier | 360 |
| bumper-front | conditional | conditional:trim | 393 |
| bumper-rear | unmapped | - | 101 |
| bumper-rear | no_records | - | 1670 |
| bumper-rear | split | option_split | 293 |
| bumper-rear | conditional | conditional:body | 14 |
| bumper-rear | conditional | conditional:engine_unattested | 160 |
| bumper-rear | conditional | conditional:qualifier | 215 |
| bumper-rear | conditional | conditional:trim | 536 |
| climate-control | unmapped | - | 101 |
| climate-control | no_records | - | 1439 |
| climate-control | split | option_split | 980 |
| climate-control | conditional | conditional:body | 64 |
| climate-control | conditional | conditional:engine | 43 |
| climate-control | conditional | conditional:engine_unattested | 36 |
| climate-control | conditional | conditional:trim | 326 |
| door-front | unmapped | - | 101 |
| door-front | no_records | - | 1315 |
| door-front | split | option_split | 189 |
| door-front | split | slot_missing | 401 |
| door-front | conditional | conditional:engine_unattested | 500 |
| door-front | conditional | conditional:trim | 483 |
| door-rear | unmapped | - | 101 |
| door-rear | no_records | - | 1643 |
| door-rear | split | option_split | 301 |
| door-rear | split | slot_missing | 313 |
| door-rear | conditional | conditional:body | 14 |
| door-rear | conditional | conditional:engine_unattested | 360 |
| door-rear | conditional | conditional:trim | 257 |
| fender | unmapped | - | 101 |
| fender | no_records | - | 1317 |
| fender | split | option_split | 163 |
| fender | split | slot_missing | 439 |
| fender | conditional | conditional:body | 14 |
| fender | conditional | conditional:engine_unattested | 190 |
| fender | conditional | conditional:production | 26 |
| fender | conditional | conditional:trim | 739 |
| fuel-pump-module | unmapped | - | 101 |
| fuel-pump-module | no_records | - | 929 |
| fuel-pump-module | split | option_split | 800 |
| fuel-pump-module | conditional | conditional:engine | 162 |
| fuel-pump-module | conditional | conditional:engine_unattested | 473 |
| fuel-pump-module | conditional | conditional:trim | 524 |
| gauge-cluster | unmapped | - | 101 |
| gauge-cluster | no_records | - | 2380 |
| gauge-cluster | split | option_split | 330 |
| gauge-cluster | conditional | conditional:trim | 178 |
| grille | unmapped | - | 101 |
| grille | no_records | - | 2364 |
| grille | split | option_split | 73 |
| grille | conditional | conditional:trim | 451 |
| headlights | unmapped | - | 101 |
| headlights | no_records | - | 855 |
| headlights | split | option_split | 1085 |
| headlights | split | position_conflict | 6 |
| headlights | split | position_missing | 16 |
| headlights | split | slot_missing | 745 |
| headlights | conditional | conditional:trim | 181 |
| hood | unmapped | - | 101 |
| hood | no_records | - | 1268 |
| hood | split | option_split | 291 |
| hood | conditional | conditional:body | 14 |
| hood | conditional | conditional:engine_unattested | 311 |
| hood | conditional | conditional:trim | 1004 |
| ignition-coils | unmapped | - | 101 |
| ignition-coils | no_records | - | 399 |
| ignition-coils | split | option_split | 773 |
| ignition-coils | conditional | conditional:engine | 125 |
| ignition-coils | conditional | conditional:engine_unattested | 728 |
| ignition-coils | conditional | conditional:trim | 863 |
| liftgate | unmapped | - | 101 |
| liftgate | no_records | - | 2300 |
| liftgate | split | option_split | 142 |
| liftgate | conditional | conditional:engine_unattested | 125 |
| liftgate | conditional | conditional:qualifier | 37 |
| liftgate | conditional | conditional:trim | 284 |
| power-steering-pump | unmapped | - | 101 |
| power-steering-pump | no_records | - | 1805 |
| power-steering-pump | split | option_split | 816 |
| power-steering-pump | conditional | conditional:engine | 57 |
| power-steering-pump | conditional | conditional:trim | 210 |
| radiator | unmapped | - | 101 |
| radiator | no_records | - | 480 |
| radiator | split | option_split | 1111 |
| radiator | conditional | conditional:engine | 231 |
| radiator | conditional | conditional:engine_unattested | 252 |
| radiator | conditional | conditional:qualifier | 9 |
| radiator | conditional | conditional:trim | 805 |
| side-mirrors | unmapped | - | 101 |
| side-mirrors | no_records | - | 1430 |
| side-mirrors | split | option_split | 688 |
| side-mirrors | split | slot_missing | 379 |
| side-mirrors | conditional | conditional:engine_unattested | 25 |
| side-mirrors | conditional | conditional:trim | 366 |
| starter | unmapped | - | 101 |
| starter | no_records | - | 1325 |
| starter | split | option_split | 252 |
| starter | conditional | conditional:colour | 44 |
| starter | conditional | conditional:engine | 120 |
| starter | conditional | conditional:engine_unattested | 250 |
| starter | conditional | conditional:trans | 5 |
| starter | conditional | conditional:trim | 892 |
| tail-lights | unmapped | - | 101 |
| tail-lights | no_records | - | 1427 |
| tail-lights | split | option_split | 817 |
| tail-lights | split | slot_missing | 259 |
| tail-lights | conditional | conditional:body | 14 |
| tail-lights | conditional | conditional:trim | 371 |
| tailgate | unmapped | - | 101 |
| tailgate | no_records | - | 2715 |
| tailgate | conditional | conditional:engine_unattested | 125 |
| tailgate | conditional | conditional:trim | 48 |
| throttle-body | unmapped | - | 101 |
| throttle-body | no_records | - | 1168 |
| throttle-body | split | option_split | 494 |
| throttle-body | conditional | conditional:colour | 44 |
| throttle-body | conditional | conditional:engine | 121 |
| throttle-body | conditional | conditional:engine_unattested | 359 |
| throttle-body | conditional | conditional:trim | 702 |
| trunk-lid | unmapped | - | 101 |
| trunk-lid | no_records | - | 2042 |
| trunk-lid | split | option_split | 395 |
| trunk-lid | conditional | conditional:option | 59 |
| trunk-lid | conditional | conditional:trim | 392 |
| window-regulator | unmapped | - | 101 |
| window-regulator | no_records | - | 609 |
| window-regulator | split | packaging_unstated | 2279 |
| window-switch | unmapped | - | 101 |
| window-switch | no_records | - | 1426 |
| window-switch | split | option_split | 817 |
| window-switch | split | position_missing | 519 |
| window-switch | conditional | conditional:colour | 58 |
| window-switch | conditional | conditional:production | 9 |
| window-switch | conditional | conditional:trim | 59 |

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
