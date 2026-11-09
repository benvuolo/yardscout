# OEM curation report: nissan

Raw: `c36da2eb98835c02f81c05e8c36b6a926634a332` @ `c36da2eb9883`; as of 2026-11-05T17:56:52Z.

- records 5686, classes 5544, list rows 0, year manifests 0, cells 8377
- Verified groups 0, engine vg groups 0, Likely groups 0
- blocked sites: none

## Gates standing for the whole namespace

- no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close (C1/C2); Verified is impossible by design until the crawler writes them
- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.infinitipartsdeal.com, www.nissanpartsdeal.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.infinitipartsdeal.com: only 0% of its 3381 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)
- www.nissanpartsdeal.com: only 0% of its 4633 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 1351 |
| ac-compressor | no_records | - | 3038 |
| ac-compressor | not_closed | no_year_manifest | 29055 |
| alternator | unmapped | - | 1351 |
| alternator | no_records | - | 1177 |
| alternator | not_closed | no_year_manifest | 30916 |
| bumper-front | unmapped | - | 1351 |
| bumper-front | no_records | - | 2685 |
| bumper-front | not_closed | no_year_manifest | 29408 |
| bumper-rear | unmapped | - | 1351 |
| bumper-rear | no_records | - | 2609 |
| bumper-rear | not_closed | no_year_manifest | 29484 |
| climate-control | unmapped | - | 1351 |
| climate-control | no_records | - | 6490 |
| climate-control | not_closed | no_year_manifest | 25603 |
| door-front | unmapped | - | 1351 |
| door-front | no_records | - | 1818 |
| door-front | not_closed | no_year_manifest | 30275 |
| door-rear | unmapped | - | 1351 |
| door-rear | no_records | - | 1598 |
| door-rear | not_closed | no_year_manifest | 30495 |
| fender | unmapped | - | 1351 |
| fender | no_records | - | 1499 |
| fender | not_closed | no_year_manifest | 30594 |
| fuel-pump-module | unmapped | - | 1351 |
| fuel-pump-module | no_records | - | 1840 |
| fuel-pump-module | not_closed | no_year_manifest | 30253 |
| gauge-cluster | unmapped | - | 1351 |
| gauge-cluster | no_records | - | 2612 |
| gauge-cluster | not_closed | no_year_manifest | 29481 |
| grille | unmapped | - | 1351 |
| grille | no_records | - | 13163 |
| grille | not_closed | no_year_manifest | 18930 |
| headlights | unmapped | - | 1351 |
| headlights | no_records | - | 2691 |
| headlights | not_closed | no_year_manifest | 29402 |
| hood | unmapped | - | 1351 |
| hood | no_records | - | 1392 |
| hood | not_closed | no_year_manifest | 30701 |
| ignition-coils | unmapped | - | 1351 |
| ignition-coils | no_records | - | 2404 |
| ignition-coils | not_closed | no_year_manifest | 29689 |
| liftgate | unmapped | - | 1351 |
| liftgate | no_records | - | 20874 |
| liftgate | not_closed | no_year_manifest | 11219 |
| power-steering-pump | unmapped | - | 1351 |
| power-steering-pump | no_records | - | 11210 |
| power-steering-pump | not_closed | no_year_manifest | 20883 |
| radiator | unmapped | - | 1351 |
| radiator | no_records | - | 1103 |
| radiator | not_closed | no_year_manifest | 30990 |
| side-mirrors | unmapped | - | 1351 |
| side-mirrors | no_records | - | 1235 |
| side-mirrors | not_closed | no_year_manifest | 30858 |
| starter | unmapped | - | 1351 |
| starter | no_records | - | 883 |
| starter | not_closed | no_year_manifest | 31210 |
| tail-lights | unmapped | - | 1351 |
| tail-lights | no_records | - | 2519 |
| tail-lights | not_closed | no_year_manifest | 29574 |
| tailgate | unmapped | - | 1351 |
| tailgate | no_records | - | 30815 |
| tailgate | not_closed | no_year_manifest | 1278 |
| throttle-body | unmapped | - | 1351 |
| throttle-body | no_records | - | 944 |
| throttle-body | not_closed | no_year_manifest | 31149 |
| trunk-lid | unmapped | - | 1351 |
| trunk-lid | no_records | - | 12656 |
| trunk-lid | not_closed | no_year_manifest | 19437 |
| window-regulator | unmapped | - | 1351 |
| window-regulator | no_records | - | 599 |
| window-regulator | not_closed | no_year_manifest | 31494 |
| window-switch | unmapped | - | 1351 |
| window-switch | no_records | - | 1682 |
| window-switch | not_closed | no_year_manifest | 30411 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 1351 |
| ac-compressor | no_records | - | 3038 |
| ac-compressor | split | option_split | 20812 |
| ac-compressor | conditional | conditional:engine_unattested | 8213 |
| ac-compressor | conditional | conditional:option | 30 |
| alternator | unmapped | - | 1351 |
| alternator | no_records | - | 1177 |
| alternator | split | option_split | 20429 |
| alternator | conditional | conditional:engine_unattested | 10487 |
| bumper-front | unmapped | - | 1351 |
| bumper-front | no_records | - | 2685 |
| bumper-front | split | option_split | 21607 |
| bumper-front | conditional | conditional:colour | 102 |
| bumper-front | conditional | conditional:engine_unattested | 7699 |
| bumper-rear | unmapped | - | 1351 |
| bumper-rear | no_records | - | 2609 |
| bumper-rear | split | option_split | 22570 |
| bumper-rear | conditional | conditional:engine_unattested | 6817 |
| bumper-rear | conditional | conditional:option | 97 |
| climate-control | unmapped | - | 1351 |
| climate-control | no_records | - | 6490 |
| climate-control | split | option_split | 21183 |
| climate-control | conditional | conditional:engine_unattested | 4397 |
| climate-control | conditional | conditional:package | 23 |
| door-front | unmapped | - | 1351 |
| door-front | no_records | - | 1818 |
| door-front | split | option_split | 17683 |
| door-front | conditional | conditional:engine_unattested | 12342 |
| door-front | conditional | conditional:option | 250 |
| door-rear | unmapped | - | 1351 |
| door-rear | no_records | - | 1598 |
| door-rear | split | option_split | 7484 |
| door-rear | split | slot_missing | 35 |
| door-rear | conditional | conditional:engine_unattested | 22070 |
| door-rear | conditional | conditional:option | 906 |
| fender | unmapped | - | 1351 |
| fender | no_records | - | 1499 |
| fender | split | option_split | 15701 |
| fender | split | slot_missing | 2 |
| fender | conditional | conditional:engine_unattested | 14891 |
| fuel-pump-module | unmapped | - | 1351 |
| fuel-pump-module | no_records | - | 1840 |
| fuel-pump-module | split | option_split | 18586 |
| fuel-pump-module | conditional | conditional:engine_unattested | 11664 |
| fuel-pump-module | conditional | conditional:option | 3 |
| gauge-cluster | unmapped | - | 1351 |
| gauge-cluster | no_records | - | 2612 |
| gauge-cluster | split | option_split | 28582 |
| gauge-cluster | conditional | conditional:engine_unattested | 854 |
| gauge-cluster | conditional | conditional:option | 45 |
| grille | unmapped | - | 1351 |
| grille | no_records | - | 13163 |
| grille | split | option_split | 12978 |
| grille | conditional | conditional:engine_unattested | 5810 |
| grille | conditional | conditional:option | 142 |
| headlights | unmapped | - | 1351 |
| headlights | no_records | - | 2691 |
| headlights | split | option_split | 23464 |
| headlights | conditional | conditional:engine_unattested | 5938 |
| hood | unmapped | - | 1351 |
| hood | no_records | - | 1392 |
| hood | split | option_split | 8055 |
| hood | conditional | conditional:engine_unattested | 22641 |
| hood | conditional | conditional:option | 5 |
| ignition-coils | unmapped | - | 1351 |
| ignition-coils | no_records | - | 2404 |
| ignition-coils | split | option_split | 19281 |
| ignition-coils | conditional | conditional:engine_unattested | 9428 |
| ignition-coils | conditional | conditional:package | 980 |
| liftgate | unmapped | - | 1351 |
| liftgate | no_records | - | 20874 |
| liftgate | split | option_split | 10472 |
| liftgate | conditional | conditional:engine_unattested | 747 |
| power-steering-pump | unmapped | - | 1351 |
| power-steering-pump | no_records | - | 11210 |
| power-steering-pump | split | option_split | 12092 |
| power-steering-pump | conditional | conditional:engine_unattested | 8717 |
| power-steering-pump | conditional | conditional:option | 74 |
| radiator | unmapped | - | 1351 |
| radiator | no_records | - | 1103 |
| radiator | split | option_split | 21721 |
| radiator | conditional | conditional:engine_unattested | 9269 |
| side-mirrors | unmapped | - | 1351 |
| side-mirrors | no_records | - | 1235 |
| side-mirrors | split | option_split | 28336 |
| side-mirrors | split | slot_missing | 4 |
| side-mirrors | conditional | conditional:engine_unattested | 2518 |
| starter | unmapped | - | 1351 |
| starter | no_records | - | 883 |
| starter | split | option_split | 21522 |
| starter | conditional | conditional:engine_unattested | 9688 |
| tail-lights | unmapped | - | 1351 |
| tail-lights | no_records | - | 2519 |
| tail-lights | split | option_split | 22402 |
| tail-lights | conditional | conditional:engine_unattested | 7127 |
| tail-lights | conditional | conditional:package | 45 |
| tailgate | unmapped | - | 1351 |
| tailgate | no_records | - | 30815 |
| tailgate | split | option_split | 277 |
| tailgate | conditional | conditional:engine_unattested | 1001 |
| throttle-body | unmapped | - | 1351 |
| throttle-body | no_records | - | 944 |
| throttle-body | split | option_split | 21907 |
| throttle-body | conditional | conditional:engine_unattested | 9242 |
| trunk-lid | unmapped | - | 1351 |
| trunk-lid | no_records | - | 12656 |
| trunk-lid | split | option_split | 18893 |
| trunk-lid | conditional | conditional:engine_unattested | 544 |
| window-regulator | unmapped | - | 1351 |
| window-regulator | no_records | - | 599 |
| window-regulator | split | packaging_unstated | 31494 |
| window-switch | unmapped | - | 1351 |
| window-switch | no_records | - | 1682 |
| window-switch | split | no_candidates | 9 |
| window-switch | split | option_split | 21124 |
| window-switch | split | position_missing | 9278 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- disputed_class: 142
- universal_part_suspect: 13

## Unknown note clauses (top 30)

- `Package Quantity: 1`: 99
- `NO PAINT`: 83
- `Production Date: from 08/2005`: 50
- `HITACHI`: 47
- `MITSUBISHI`: 37
- `Production Date: from 01/1986`: 32
- `Production Date: from 01/2004`: 32
- `W`: 30
- `Require Quantity: 06`: 29
- `W. SE`: 28
- `U/4S. GXE`: 23
- `Production Date: 07/1984-01/1986`: 22
- `Require Quantity: 04`: 22
- `Production Date: 12/2004-09/2005`: 21
- `Production Date: from 07/2001`: 19
- `Production Date: from 08/2004`: 19
- `Production Date: 08/2006-04/2007`: 18
- `Require Quantity: 03`: 18
- `ELEC`: 17
- `Production Date: 08/2001-08/2002`: 17
- `F/POWER WINDOW`: 16
- `PRIMER`: 16
- `Production Date: 04/1992-09/1995`: 16
- `Production Date: 12/1998-01/2000`: 16
- `Production Date: from 04/2003`: 16
- `4S. QR25DE`: 15
- `Production Date: 04/1999-09/1999`: 15
- `Require Quantity: 02`: 15
- `SKULL CAP`: 15
- `UNDERCOATED(SILVER)`: 15

## Unmapped catalog models

- Nissan 300ZX: feed '300ZX' 54 cars
- Nissan Hardbody Pickup (D21): feed 'Hardbody Pickup (D21)' 0 cars (excluded: catalog model with no feed cars as 'Hardbody Pickup (D21)' (inventory 2026-11-04); nothing to map)
- Nissan Hardbody Pickup (D21U): feed 'Hardbody Pickup (D21U)' 0 cars (excluded: catalog model with no feed cars as 'Hardbody Pickup (D21U)' (inventory 2026-11-04); nothing to map)
- Nissan Kicks Play: feed 'Kicks Play' 0 cars
- Nissan Pulsar NX: feed 'Pulsar NX' 2 cars
- Nissan Rogue Sport: feed 'Rogue Sport' 38 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (35 cars, under catalog squash 'rogue'); unmapped until a reviewed entry exists)
- Nissan Van: feed 'Van' 0 cars
- Nissan Versa Note: feed 'Versa Note' 322 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (313 cars, under catalog squash 'versa'); unmapped until a reviewed entry exists)
