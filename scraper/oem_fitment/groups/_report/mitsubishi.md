# OEM curation report: mitsubishi

Raw: `c36da2eb98835c02f81c05e8c36b6a926634a332` @ `c36da2eb9883`; as of 2026-11-05T09:25:16Z.

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
| ac-compressor | no_records | - | 1027 |
| ac-compressor | not_closed | no_year_manifest | 1855 |
| alternator | unmapped | - | 102 |
| alternator | no_records | - | 2074 |
| alternator | not_closed | no_year_manifest | 808 |
| bumper-front | unmapped | - | 102 |
| bumper-front | no_records | - | 1500 |
| bumper-front | not_closed | no_year_manifest | 1382 |
| bumper-rear | unmapped | - | 102 |
| bumper-rear | no_records | - | 1662 |
| bumper-rear | not_closed | no_year_manifest | 1220 |
| climate-control | unmapped | - | 102 |
| climate-control | no_records | - | 1433 |
| climate-control | not_closed | no_year_manifest | 1449 |
| door-front | unmapped | - | 102 |
| door-front | no_records | - | 1310 |
| door-front | not_closed | no_year_manifest | 1572 |
| door-rear | unmapped | - | 102 |
| door-rear | no_records | - | 1643 |
| door-rear | not_closed | no_year_manifest | 1239 |
| fender | unmapped | - | 102 |
| fender | no_records | - | 1311 |
| fender | not_closed | no_year_manifest | 1571 |
| fuel-pump-module | unmapped | - | 102 |
| fuel-pump-module | no_records | - | 924 |
| fuel-pump-module | not_closed | no_year_manifest | 1958 |
| gauge-cluster | unmapped | - | 102 |
| gauge-cluster | no_records | - | 2376 |
| gauge-cluster | not_closed | no_year_manifest | 506 |
| grille | unmapped | - | 102 |
| grille | no_records | - | 2356 |
| grille | not_closed | no_year_manifest | 526 |
| headlights | unmapped | - | 102 |
| headlights | no_records | - | 852 |
| headlights | not_closed | no_year_manifest | 2030 |
| hood | unmapped | - | 102 |
| hood | no_records | - | 1262 |
| hood | not_closed | no_year_manifest | 1620 |
| ignition-coils | unmapped | - | 102 |
| ignition-coils | no_records | - | 395 |
| ignition-coils | not_closed | no_year_manifest | 2487 |
| liftgate | unmapped | - | 102 |
| liftgate | no_records | - | 2298 |
| liftgate | not_closed | no_year_manifest | 584 |
| power-steering-pump | unmapped | - | 102 |
| power-steering-pump | no_records | - | 1797 |
| power-steering-pump | not_closed | no_year_manifest | 1085 |
| radiator | unmapped | - | 102 |
| radiator | no_records | - | 480 |
| radiator | not_closed | no_year_manifest | 2402 |
| side-mirrors | unmapped | - | 102 |
| side-mirrors | no_records | - | 1425 |
| side-mirrors | not_closed | no_year_manifest | 1457 |
| starter | unmapped | - | 102 |
| starter | no_records | - | 1322 |
| starter | not_closed | no_year_manifest | 1560 |
| tail-lights | unmapped | - | 102 |
| tail-lights | no_records | - | 1420 |
| tail-lights | not_closed | no_year_manifest | 1462 |
| tailgate | unmapped | - | 102 |
| tailgate | no_records | - | 2711 |
| tailgate | not_closed | no_year_manifest | 171 |
| throttle-body | unmapped | - | 102 |
| throttle-body | no_records | - | 1162 |
| throttle-body | not_closed | no_year_manifest | 1720 |
| trunk-lid | unmapped | - | 102 |
| trunk-lid | no_records | - | 2035 |
| trunk-lid | not_closed | no_year_manifest | 847 |
| window-regulator | unmapped | - | 102 |
| window-regulator | no_records | - | 609 |
| window-regulator | not_closed | no_year_manifest | 2273 |
| window-switch | unmapped | - | 102 |
| window-switch | no_records | - | 1421 |
| window-switch | not_closed | no_year_manifest | 1461 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 102 |
| ac-compressor | no_records | - | 1027 |
| ac-compressor | split | option_split | 850 |
| ac-compressor | conditional | conditional:engine | 65 |
| ac-compressor | conditional | conditional:engine_unattested | 829 |
| ac-compressor | conditional | conditional:trim | 111 |
| alternator | unmapped | - | 102 |
| alternator | no_records | - | 2074 |
| alternator | split | option_split | 39 |
| alternator | conditional | conditional:colour | 57 |
| alternator | conditional | conditional:engine_unattested | 225 |
| alternator | conditional | conditional:production | 54 |
| alternator | conditional | conditional:trim | 433 |
| bumper-front | unmapped | - | 102 |
| bumper-front | no_records | - | 1500 |
| bumper-front | split | option_split | 396 |
| bumper-front | conditional | conditional:colour | 57 |
| bumper-front | conditional | conditional:engine_unattested | 132 |
| bumper-front | conditional | conditional:option | 43 |
| bumper-front | conditional | conditional:qualifier | 359 |
| bumper-front | conditional | conditional:trim | 395 |
| bumper-rear | unmapped | - | 102 |
| bumper-rear | no_records | - | 1662 |
| bumper-rear | split | option_split | 294 |
| bumper-rear | conditional | conditional:body | 14 |
| bumper-rear | conditional | conditional:engine_unattested | 158 |
| bumper-rear | conditional | conditional:qualifier | 216 |
| bumper-rear | conditional | conditional:trim | 538 |
| climate-control | unmapped | - | 102 |
| climate-control | no_records | - | 1433 |
| climate-control | split | option_split | 980 |
| climate-control | conditional | conditional:body | 65 |
| climate-control | conditional | conditional:engine | 43 |
| climate-control | conditional | conditional:engine_unattested | 34 |
| climate-control | conditional | conditional:trim | 327 |
| door-front | unmapped | - | 102 |
| door-front | no_records | - | 1310 |
| door-front | split | option_split | 187 |
| door-front | split | slot_missing | 402 |
| door-front | conditional | conditional:engine_unattested | 498 |
| door-front | conditional | conditional:trim | 485 |
| door-rear | unmapped | - | 102 |
| door-rear | no_records | - | 1643 |
| door-rear | split | option_split | 299 |
| door-rear | split | slot_missing | 310 |
| door-rear | conditional | conditional:body | 14 |
| door-rear | conditional | conditional:engine_unattested | 358 |
| door-rear | conditional | conditional:trim | 258 |
| fender | unmapped | - | 102 |
| fender | no_records | - | 1311 |
| fender | split | option_split | 163 |
| fender | split | slot_missing | 440 |
| fender | conditional | conditional:body | 14 |
| fender | conditional | conditional:engine_unattested | 190 |
| fender | conditional | conditional:production | 26 |
| fender | conditional | conditional:trim | 738 |
| fuel-pump-module | unmapped | - | 102 |
| fuel-pump-module | no_records | - | 924 |
| fuel-pump-module | split | option_split | 799 |
| fuel-pump-module | conditional | conditional:engine | 163 |
| fuel-pump-module | conditional | conditional:engine_unattested | 472 |
| fuel-pump-module | conditional | conditional:trim | 524 |
| gauge-cluster | unmapped | - | 102 |
| gauge-cluster | no_records | - | 2376 |
| gauge-cluster | split | option_split | 328 |
| gauge-cluster | conditional | conditional:trim | 178 |
| grille | unmapped | - | 102 |
| grille | no_records | - | 2356 |
| grille | split | option_split | 73 |
| grille | conditional | conditional:trim | 453 |
| headlights | unmapped | - | 102 |
| headlights | no_records | - | 852 |
| headlights | split | option_split | 1085 |
| headlights | split | position_conflict | 6 |
| headlights | split | position_missing | 17 |
| headlights | split | slot_missing | 741 |
| headlights | conditional | conditional:trim | 181 |
| hood | unmapped | - | 102 |
| hood | no_records | - | 1262 |
| hood | split | option_split | 292 |
| hood | conditional | conditional:body | 14 |
| hood | conditional | conditional:engine_unattested | 311 |
| hood | conditional | conditional:trim | 1003 |
| ignition-coils | unmapped | - | 102 |
| ignition-coils | no_records | - | 395 |
| ignition-coils | split | option_split | 774 |
| ignition-coils | conditional | conditional:engine | 124 |
| ignition-coils | conditional | conditional:engine_unattested | 723 |
| ignition-coils | conditional | conditional:trim | 866 |
| liftgate | unmapped | - | 102 |
| liftgate | no_records | - | 2298 |
| liftgate | split | option_split | 140 |
| liftgate | conditional | conditional:engine_unattested | 123 |
| liftgate | conditional | conditional:qualifier | 37 |
| liftgate | conditional | conditional:trim | 284 |
| power-steering-pump | unmapped | - | 102 |
| power-steering-pump | no_records | - | 1797 |
| power-steering-pump | split | option_split | 816 |
| power-steering-pump | conditional | conditional:engine | 57 |
| power-steering-pump | conditional | conditional:trim | 212 |
| radiator | unmapped | - | 102 |
| radiator | no_records | - | 480 |
| radiator | split | option_split | 1107 |
| radiator | conditional | conditional:engine | 230 |
| radiator | conditional | conditional:engine_unattested | 250 |
| radiator | conditional | conditional:qualifier | 9 |
| radiator | conditional | conditional:trim | 806 |
| side-mirrors | unmapped | - | 102 |
| side-mirrors | no_records | - | 1425 |
| side-mirrors | split | option_split | 687 |
| side-mirrors | split | slot_missing | 378 |
| side-mirrors | conditional | conditional:engine_unattested | 25 |
| side-mirrors | conditional | conditional:trim | 367 |
| starter | unmapped | - | 102 |
| starter | no_records | - | 1322 |
| starter | split | option_split | 252 |
| starter | conditional | conditional:colour | 43 |
| starter | conditional | conditional:engine | 119 |
| starter | conditional | conditional:engine_unattested | 249 |
| starter | conditional | conditional:trans | 5 |
| starter | conditional | conditional:trim | 892 |
| tail-lights | unmapped | - | 102 |
| tail-lights | no_records | - | 1420 |
| tail-lights | split | option_split | 816 |
| tail-lights | split | slot_missing | 262 |
| tail-lights | conditional | conditional:body | 14 |
| tail-lights | conditional | conditional:trim | 370 |
| tailgate | unmapped | - | 102 |
| tailgate | no_records | - | 2711 |
| tailgate | conditional | conditional:engine_unattested | 123 |
| tailgate | conditional | conditional:trim | 48 |
| throttle-body | unmapped | - | 102 |
| throttle-body | no_records | - | 1162 |
| throttle-body | split | option_split | 494 |
| throttle-body | conditional | conditional:colour | 43 |
| throttle-body | conditional | conditional:engine | 122 |
| throttle-body | conditional | conditional:engine_unattested | 358 |
| throttle-body | conditional | conditional:trim | 703 |
| trunk-lid | unmapped | - | 102 |
| trunk-lid | no_records | - | 2035 |
| trunk-lid | split | option_split | 396 |
| trunk-lid | conditional | conditional:option | 59 |
| trunk-lid | conditional | conditional:trim | 392 |
| window-regulator | unmapped | - | 102 |
| window-regulator | no_records | - | 609 |
| window-regulator | split | packaging_unstated | 2273 |
| window-switch | unmapped | - | 102 |
| window-switch | no_records | - | 1421 |
| window-switch | split | option_split | 818 |
| window-switch | split | position_missing | 518 |
| window-switch | conditional | conditional:colour | 57 |
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
