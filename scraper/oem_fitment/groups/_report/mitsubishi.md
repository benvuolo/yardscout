# OEM curation report: mitsubishi

Raw: `ceccc800d7ba22c0291121baabb0a9292eb8f271` @ `ceccc800d7ba`; as of 2026-11-05T09:25:16Z.

- records 452, classes 452, list rows 0, year manifests 0, cells 1474
- Verified groups 0, engine vg groups 0, Likely groups 32
- blocked sites: none

## Gates standing for the whole namespace

- no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close (C1/C2); Verified is impossible by design until the crawler writes them
- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.mitsubishipartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 102 |
| ac-compressor | no_records | - | 1026 |
| ac-compressor | not_closed | no_year_manifest | 1866 |
| alternator | unmapped | - | 102 |
| alternator | no_records | - | 2090 |
| alternator | not_closed | no_year_manifest | 802 |
| bumper-front | unmapped | - | 102 |
| bumper-front | no_records | - | 1509 |
| bumper-front | not_closed | no_year_manifest | 1383 |
| bumper-rear | unmapped | - | 102 |
| bumper-rear | no_records | - | 1681 |
| bumper-rear | not_closed | no_year_manifest | 1211 |
| climate-control | unmapped | - | 102 |
| climate-control | no_records | - | 1439 |
| climate-control | not_closed | no_year_manifest | 1453 |
| door-front | unmapped | - | 102 |
| door-front | no_records | - | 1322 |
| door-front | not_closed | no_year_manifest | 1570 |
| door-rear | unmapped | - | 102 |
| door-rear | no_records | - | 1647 |
| door-rear | not_closed | no_year_manifest | 1245 |
| fender | unmapped | - | 102 |
| fender | no_records | - | 1325 |
| fender | not_closed | no_year_manifest | 1567 |
| fuel-pump-module | unmapped | - | 102 |
| fuel-pump-module | no_records | - | 936 |
| fuel-pump-module | not_closed | no_year_manifest | 1956 |
| gauge-cluster | unmapped | - | 102 |
| gauge-cluster | no_records | - | 2386 |
| gauge-cluster | not_closed | no_year_manifest | 506 |
| grille | unmapped | - | 102 |
| grille | no_records | - | 2367 |
| grille | not_closed | no_year_manifest | 525 |
| headlights | unmapped | - | 102 |
| headlights | no_records | - | 855 |
| headlights | not_closed | no_year_manifest | 2037 |
| hood | unmapped | - | 102 |
| hood | no_records | - | 1270 |
| hood | not_closed | no_year_manifest | 1622 |
| ignition-coils | unmapped | - | 102 |
| ignition-coils | no_records | - | 403 |
| ignition-coils | not_closed | no_year_manifest | 2489 |
| liftgate | unmapped | - | 102 |
| liftgate | no_records | - | 2308 |
| liftgate | not_closed | no_year_manifest | 584 |
| power-steering-pump | unmapped | - | 102 |
| power-steering-pump | no_records | - | 1802 |
| power-steering-pump | not_closed | no_year_manifest | 1090 |
| radiator | unmapped | - | 102 |
| radiator | no_records | - | 484 |
| radiator | not_closed | no_year_manifest | 2408 |
| side-mirrors | unmapped | - | 102 |
| side-mirrors | no_records | - | 1432 |
| side-mirrors | not_closed | no_year_manifest | 1460 |
| starter | unmapped | - | 102 |
| starter | no_records | - | 1335 |
| starter | not_closed | no_year_manifest | 1557 |
| tail-lights | unmapped | - | 102 |
| tail-lights | no_records | - | 1435 |
| tail-lights | not_closed | no_year_manifest | 1457 |
| tailgate | unmapped | - | 102 |
| tailgate | no_records | - | 2719 |
| tailgate | not_closed | no_year_manifest | 173 |
| throttle-body | unmapped | - | 102 |
| throttle-body | no_records | - | 1174 |
| throttle-body | not_closed | no_year_manifest | 1718 |
| trunk-lid | unmapped | - | 102 |
| trunk-lid | no_records | - | 2047 |
| trunk-lid | not_closed | no_year_manifest | 845 |
| window-regulator | unmapped | - | 102 |
| window-regulator | no_records | - | 618 |
| window-regulator | not_closed | no_year_manifest | 2274 |
| window-switch | unmapped | - | 102 |
| window-switch | no_records | - | 1427 |
| window-switch | not_closed | no_year_manifest | 1465 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 102 |
| ac-compressor | no_records | - | 1026 |
| ac-compressor | split | option_split | 849 |
| ac-compressor | conditional | conditional:engine | 65 |
| ac-compressor | conditional | conditional:engine_unattested | 841 |
| ac-compressor | conditional | conditional:trim | 111 |
| alternator | unmapped | - | 102 |
| alternator | no_records | - | 2090 |
| alternator | split | option_split | 41 |
| alternator | conditional | conditional:colour | 58 |
| alternator | conditional | conditional:engine_unattested | 221 |
| alternator | conditional | conditional:production | 51 |
| alternator | conditional | conditional:trim | 431 |
| bumper-front | unmapped | - | 102 |
| bumper-front | no_records | - | 1509 |
| bumper-front | split | option_split | 392 |
| bumper-front | conditional | conditional:colour | 56 |
| bumper-front | conditional | conditional:engine_unattested | 137 |
| bumper-front | conditional | conditional:option | 44 |
| bumper-front | conditional | conditional:qualifier | 355 |
| bumper-front | conditional | conditional:trim | 399 |
| bumper-rear | unmapped | - | 102 |
| bumper-rear | no_records | - | 1681 |
| bumper-rear | split | option_split | 292 |
| bumper-rear | conditional | conditional:body | 14 |
| bumper-rear | conditional | conditional:engine_unattested | 162 |
| bumper-rear | conditional | conditional:qualifier | 213 |
| bumper-rear | conditional | conditional:trim | 530 |
| climate-control | unmapped | - | 102 |
| climate-control | no_records | - | 1439 |
| climate-control | split | option_split | 984 |
| climate-control | conditional | conditional:body | 65 |
| climate-control | conditional | conditional:engine | 45 |
| climate-control | conditional | conditional:engine_unattested | 34 |
| climate-control | conditional | conditional:trim | 325 |
| door-front | unmapped | - | 102 |
| door-front | no_records | - | 1322 |
| door-front | split | option_split | 186 |
| door-front | split | slot_missing | 402 |
| door-front | conditional | conditional:engine_unattested | 500 |
| door-front | conditional | conditional:trim | 482 |
| door-rear | unmapped | - | 102 |
| door-rear | no_records | - | 1647 |
| door-rear | split | option_split | 300 |
| door-rear | split | slot_missing | 316 |
| door-rear | conditional | conditional:body | 14 |
| door-rear | conditional | conditional:engine_unattested | 356 |
| door-rear | conditional | conditional:trim | 259 |
| fender | unmapped | - | 102 |
| fender | no_records | - | 1325 |
| fender | split | option_split | 162 |
| fender | split | slot_missing | 439 |
| fender | conditional | conditional:body | 14 |
| fender | conditional | conditional:engine_unattested | 191 |
| fender | conditional | conditional:production | 27 |
| fender | conditional | conditional:trim | 734 |
| fuel-pump-module | unmapped | - | 102 |
| fuel-pump-module | no_records | - | 936 |
| fuel-pump-module | split | option_split | 795 |
| fuel-pump-module | conditional | conditional:engine | 164 |
| fuel-pump-module | conditional | conditional:engine_unattested | 466 |
| fuel-pump-module | conditional | conditional:trim | 531 |
| gauge-cluster | unmapped | - | 102 |
| gauge-cluster | no_records | - | 2386 |
| gauge-cluster | split | option_split | 326 |
| gauge-cluster | conditional | conditional:trim | 180 |
| grille | unmapped | - | 102 |
| grille | no_records | - | 2367 |
| grille | split | option_split | 76 |
| grille | conditional | conditional:trim | 449 |
| headlights | unmapped | - | 102 |
| headlights | no_records | - | 855 |
| headlights | split | option_split | 1093 |
| headlights | split | position_conflict | 6 |
| headlights | split | position_missing | 19 |
| headlights | split | slot_missing | 744 |
| headlights | conditional | conditional:trim | 175 |
| hood | unmapped | - | 102 |
| hood | no_records | - | 1270 |
| hood | split | option_split | 293 |
| hood | conditional | conditional:body | 14 |
| hood | conditional | conditional:engine_unattested | 313 |
| hood | conditional | conditional:trim | 1002 |
| ignition-coils | unmapped | - | 102 |
| ignition-coils | no_records | - | 403 |
| ignition-coils | split | option_split | 776 |
| ignition-coils | conditional | conditional:engine | 124 |
| ignition-coils | conditional | conditional:engine_unattested | 721 |
| ignition-coils | conditional | conditional:trim | 868 |
| liftgate | unmapped | - | 102 |
| liftgate | no_records | - | 2308 |
| liftgate | split | option_split | 142 |
| liftgate | conditional | conditional:engine_unattested | 125 |
| liftgate | conditional | conditional:qualifier | 37 |
| liftgate | conditional | conditional:trim | 280 |
| power-steering-pump | unmapped | - | 102 |
| power-steering-pump | no_records | - | 1802 |
| power-steering-pump | split | option_split | 823 |
| power-steering-pump | conditional | conditional:engine | 56 |
| power-steering-pump | conditional | conditional:trim | 211 |
| radiator | unmapped | - | 102 |
| radiator | no_records | - | 484 |
| radiator | split | option_split | 1108 |
| radiator | conditional | conditional:engine | 229 |
| radiator | conditional | conditional:engine_unattested | 259 |
| radiator | conditional | conditional:qualifier | 9 |
| radiator | conditional | conditional:trim | 803 |
| side-mirrors | unmapped | - | 102 |
| side-mirrors | no_records | - | 1432 |
| side-mirrors | split | option_split | 692 |
| side-mirrors | split | slot_missing | 381 |
| side-mirrors | conditional | conditional:engine_unattested | 22 |
| side-mirrors | conditional | conditional:trim | 365 |
| starter | unmapped | - | 102 |
| starter | no_records | - | 1335 |
| starter | split | option_split | 251 |
| starter | conditional | conditional:colour | 44 |
| starter | conditional | conditional:engine | 119 |
| starter | conditional | conditional:engine_unattested | 244 |
| starter | conditional | conditional:trans | 5 |
| starter | conditional | conditional:trim | 894 |
| tail-lights | unmapped | - | 102 |
| tail-lights | no_records | - | 1435 |
| tail-lights | split | option_split | 822 |
| tail-lights | split | slot_missing | 259 |
| tail-lights | conditional | conditional:body | 14 |
| tail-lights | conditional | conditional:trim | 362 |
| tailgate | unmapped | - | 102 |
| tailgate | no_records | - | 2719 |
| tailgate | conditional | conditional:engine_unattested | 125 |
| tailgate | conditional | conditional:trim | 48 |
| throttle-body | unmapped | - | 102 |
| throttle-body | no_records | - | 1174 |
| throttle-body | split | option_split | 496 |
| throttle-body | conditional | conditional:colour | 44 |
| throttle-body | conditional | conditional:engine | 121 |
| throttle-body | conditional | conditional:engine_unattested | 351 |
| throttle-body | conditional | conditional:trim | 706 |
| trunk-lid | unmapped | - | 102 |
| trunk-lid | no_records | - | 2047 |
| trunk-lid | split | option_split | 395 |
| trunk-lid | conditional | conditional:option | 61 |
| trunk-lid | conditional | conditional:trim | 389 |
| window-regulator | unmapped | - | 102 |
| window-regulator | no_records | - | 618 |
| window-regulator | split | packaging_unstated | 2274 |
| window-switch | unmapped | - | 102 |
| window-switch | no_records | - | 1427 |
| window-switch | split | option_split | 809 |
| window-switch | split | position_missing | 528 |
| window-switch | conditional | conditional:colour | 58 |
| window-switch | conditional | conditional:production | 9 |
| window-switch | conditional | conditional:trim | 61 |

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
