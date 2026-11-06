# OEM curation report: nissan

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-05T17:56:52Z.

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
| ac-compressor | unmapped | - | 1336 |
| ac-compressor | no_records | - | 3004 |
| ac-compressor | not_closed | no_year_manifest | 28921 |
| alternator | unmapped | - | 1336 |
| alternator | no_records | - | 1162 |
| alternator | not_closed | no_year_manifest | 30763 |
| bumper-front | unmapped | - | 1336 |
| bumper-front | no_records | - | 2647 |
| bumper-front | not_closed | no_year_manifest | 29278 |
| bumper-rear | unmapped | - | 1336 |
| bumper-rear | no_records | - | 2579 |
| bumper-rear | not_closed | no_year_manifest | 29346 |
| climate-control | unmapped | - | 1336 |
| climate-control | no_records | - | 6465 |
| climate-control | not_closed | no_year_manifest | 25460 |
| door-front | unmapped | - | 1336 |
| door-front | no_records | - | 1784 |
| door-front | not_closed | no_year_manifest | 30141 |
| door-rear | unmapped | - | 1336 |
| door-rear | no_records | - | 1579 |
| door-rear | not_closed | no_year_manifest | 30346 |
| fender | unmapped | - | 1336 |
| fender | no_records | - | 1475 |
| fender | not_closed | no_year_manifest | 30450 |
| fuel-pump-module | unmapped | - | 1336 |
| fuel-pump-module | no_records | - | 1809 |
| fuel-pump-module | not_closed | no_year_manifest | 30116 |
| gauge-cluster | unmapped | - | 1336 |
| gauge-cluster | no_records | - | 2571 |
| gauge-cluster | not_closed | no_year_manifest | 29354 |
| grille | unmapped | - | 1336 |
| grille | no_records | - | 13070 |
| grille | not_closed | no_year_manifest | 18855 |
| headlights | unmapped | - | 1336 |
| headlights | no_records | - | 2654 |
| headlights | not_closed | no_year_manifest | 29271 |
| hood | unmapped | - | 1336 |
| hood | no_records | - | 1387 |
| hood | not_closed | no_year_manifest | 30538 |
| ignition-coils | unmapped | - | 1336 |
| ignition-coils | no_records | - | 2379 |
| ignition-coils | not_closed | no_year_manifest | 29546 |
| liftgate | unmapped | - | 1336 |
| liftgate | no_records | - | 20785 |
| liftgate | not_closed | no_year_manifest | 11140 |
| power-steering-pump | unmapped | - | 1336 |
| power-steering-pump | no_records | - | 11105 |
| power-steering-pump | not_closed | no_year_manifest | 20820 |
| radiator | unmapped | - | 1336 |
| radiator | no_records | - | 1084 |
| radiator | not_closed | no_year_manifest | 30841 |
| side-mirrors | unmapped | - | 1336 |
| side-mirrors | no_records | - | 1215 |
| side-mirrors | not_closed | no_year_manifest | 30710 |
| starter | unmapped | - | 1336 |
| starter | no_records | - | 868 |
| starter | not_closed | no_year_manifest | 31057 |
| tail-lights | unmapped | - | 1336 |
| tail-lights | no_records | - | 2506 |
| tail-lights | not_closed | no_year_manifest | 29419 |
| tailgate | unmapped | - | 1336 |
| tailgate | no_records | - | 30658 |
| tailgate | not_closed | no_year_manifest | 1267 |
| throttle-body | unmapped | - | 1336 |
| throttle-body | no_records | - | 931 |
| throttle-body | not_closed | no_year_manifest | 30994 |
| trunk-lid | unmapped | - | 1336 |
| trunk-lid | no_records | - | 12550 |
| trunk-lid | not_closed | no_year_manifest | 19375 |
| window-regulator | unmapped | - | 1336 |
| window-regulator | no_records | - | 595 |
| window-regulator | not_closed | no_year_manifest | 31330 |
| window-switch | unmapped | - | 1336 |
| window-switch | no_records | - | 1669 |
| window-switch | not_closed | no_year_manifest | 30256 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 1336 |
| ac-compressor | no_records | - | 3004 |
| ac-compressor | split | option_split | 20730 |
| ac-compressor | conditional | conditional:engine_unattested | 8161 |
| ac-compressor | conditional | conditional:option | 30 |
| alternator | unmapped | - | 1336 |
| alternator | no_records | - | 1162 |
| alternator | split | option_split | 20331 |
| alternator | conditional | conditional:engine_unattested | 10432 |
| bumper-front | unmapped | - | 1336 |
| bumper-front | no_records | - | 2647 |
| bumper-front | split | option_split | 21510 |
| bumper-front | conditional | conditional:colour | 101 |
| bumper-front | conditional | conditional:engine_unattested | 7667 |
| bumper-rear | unmapped | - | 1336 |
| bumper-rear | no_records | - | 2579 |
| bumper-rear | split | option_split | 22467 |
| bumper-rear | conditional | conditional:engine_unattested | 6783 |
| bumper-rear | conditional | conditional:option | 96 |
| climate-control | unmapped | - | 1336 |
| climate-control | no_records | - | 6465 |
| climate-control | split | option_split | 21097 |
| climate-control | conditional | conditional:engine_unattested | 4340 |
| climate-control | conditional | conditional:package | 23 |
| door-front | unmapped | - | 1336 |
| door-front | no_records | - | 1784 |
| door-front | split | option_split | 17603 |
| door-front | conditional | conditional:engine_unattested | 12294 |
| door-front | conditional | conditional:option | 244 |
| door-rear | unmapped | - | 1336 |
| door-rear | no_records | - | 1579 |
| door-rear | split | option_split | 7427 |
| door-rear | split | slot_missing | 34 |
| door-rear | conditional | conditional:engine_unattested | 21979 |
| door-rear | conditional | conditional:option | 906 |
| fender | unmapped | - | 1336 |
| fender | no_records | - | 1475 |
| fender | split | option_split | 15647 |
| fender | split | slot_missing | 2 |
| fender | conditional | conditional:engine_unattested | 14801 |
| fuel-pump-module | unmapped | - | 1336 |
| fuel-pump-module | no_records | - | 1809 |
| fuel-pump-module | split | option_split | 18479 |
| fuel-pump-module | conditional | conditional:engine_unattested | 11634 |
| fuel-pump-module | conditional | conditional:option | 3 |
| gauge-cluster | unmapped | - | 1336 |
| gauge-cluster | no_records | - | 2571 |
| gauge-cluster | split | option_split | 28463 |
| gauge-cluster | conditional | conditional:engine_unattested | 847 |
| gauge-cluster | conditional | conditional:option | 44 |
| grille | unmapped | - | 1336 |
| grille | no_records | - | 13070 |
| grille | split | option_split | 12922 |
| grille | conditional | conditional:engine_unattested | 5791 |
| grille | conditional | conditional:option | 142 |
| headlights | unmapped | - | 1336 |
| headlights | no_records | - | 2654 |
| headlights | split | option_split | 23355 |
| headlights | conditional | conditional:engine_unattested | 5916 |
| hood | unmapped | - | 1336 |
| hood | no_records | - | 1387 |
| hood | split | option_split | 8027 |
| hood | conditional | conditional:engine_unattested | 22506 |
| hood | conditional | conditional:option | 5 |
| ignition-coils | unmapped | - | 1336 |
| ignition-coils | no_records | - | 2379 |
| ignition-coils | split | option_split | 19219 |
| ignition-coils | conditional | conditional:engine_unattested | 9360 |
| ignition-coils | conditional | conditional:package | 967 |
| liftgate | unmapped | - | 1336 |
| liftgate | no_records | - | 20785 |
| liftgate | split | option_split | 10401 |
| liftgate | conditional | conditional:engine_unattested | 739 |
| power-steering-pump | unmapped | - | 1336 |
| power-steering-pump | no_records | - | 11105 |
| power-steering-pump | split | option_split | 12079 |
| power-steering-pump | conditional | conditional:engine_unattested | 8667 |
| power-steering-pump | conditional | conditional:option | 74 |
| radiator | unmapped | - | 1336 |
| radiator | no_records | - | 1084 |
| radiator | split | option_split | 21635 |
| radiator | conditional | conditional:engine_unattested | 9206 |
| side-mirrors | unmapped | - | 1336 |
| side-mirrors | no_records | - | 1215 |
| side-mirrors | split | option_split | 28211 |
| side-mirrors | split | slot_missing | 4 |
| side-mirrors | conditional | conditional:engine_unattested | 2495 |
| starter | unmapped | - | 1336 |
| starter | no_records | - | 868 |
| starter | split | option_split | 21435 |
| starter | conditional | conditional:engine_unattested | 9622 |
| tail-lights | unmapped | - | 1336 |
| tail-lights | no_records | - | 2506 |
| tail-lights | split | option_split | 22293 |
| tail-lights | conditional | conditional:engine_unattested | 7084 |
| tail-lights | conditional | conditional:package | 42 |
| tailgate | unmapped | - | 1336 |
| tailgate | no_records | - | 30658 |
| tailgate | split | option_split | 272 |
| tailgate | conditional | conditional:engine_unattested | 995 |
| throttle-body | unmapped | - | 1336 |
| throttle-body | no_records | - | 931 |
| throttle-body | split | option_split | 21837 |
| throttle-body | conditional | conditional:engine_unattested | 9157 |
| trunk-lid | unmapped | - | 1336 |
| trunk-lid | no_records | - | 12550 |
| trunk-lid | split | option_split | 18833 |
| trunk-lid | conditional | conditional:engine_unattested | 542 |
| window-regulator | unmapped | - | 1336 |
| window-regulator | no_records | - | 595 |
| window-regulator | split | packaging_unstated | 31330 |
| window-switch | unmapped | - | 1336 |
| window-switch | no_records | - | 1669 |
| window-switch | split | no_candidates | 9 |
| window-switch | split | option_split | 21019 |
| window-switch | split | position_missing | 9228 |

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
- Nissan Pulsar NX: feed 'Pulsar NX' 3 cars
- Nissan Rogue Sport: feed 'Rogue Sport' 36 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (35 cars, under catalog squash 'rogue'); unmapped until a reviewed entry exists)
- Nissan Van: feed 'Van' 0 cars
- Nissan Versa Note: feed 'Versa Note' 320 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (313 cars, under catalog squash 'versa'); unmapped until a reviewed entry exists)
