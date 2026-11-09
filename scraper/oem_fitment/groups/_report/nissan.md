# OEM curation report: nissan

Raw: `1351c33fcfbb` @ `1351c33fcfbb`; as of 2026-11-05T17:56:52Z.

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
| ac-compressor | unmapped | - | 1355 |
| ac-compressor | no_records | - | 3059 |
| ac-compressor | not_closed | no_year_manifest | 29012 |
| alternator | unmapped | - | 1355 |
| alternator | no_records | - | 1186 |
| alternator | not_closed | no_year_manifest | 30885 |
| bumper-front | unmapped | - | 1355 |
| bumper-front | no_records | - | 2681 |
| bumper-front | not_closed | no_year_manifest | 29390 |
| bumper-rear | unmapped | - | 1355 |
| bumper-rear | no_records | - | 2611 |
| bumper-rear | not_closed | no_year_manifest | 29460 |
| climate-control | unmapped | - | 1355 |
| climate-control | no_records | - | 6493 |
| climate-control | not_closed | no_year_manifest | 25578 |
| door-front | unmapped | - | 1355 |
| door-front | no_records | - | 1816 |
| door-front | not_closed | no_year_manifest | 30255 |
| door-rear | unmapped | - | 1355 |
| door-rear | no_records | - | 1596 |
| door-rear | not_closed | no_year_manifest | 30475 |
| fender | unmapped | - | 1355 |
| fender | no_records | - | 1495 |
| fender | not_closed | no_year_manifest | 30576 |
| fuel-pump-module | unmapped | - | 1355 |
| fuel-pump-module | no_records | - | 1845 |
| fuel-pump-module | not_closed | no_year_manifest | 30226 |
| gauge-cluster | unmapped | - | 1355 |
| gauge-cluster | no_records | - | 2610 |
| gauge-cluster | not_closed | no_year_manifest | 29461 |
| grille | unmapped | - | 1355 |
| grille | no_records | - | 13142 |
| grille | not_closed | no_year_manifest | 18929 |
| headlights | unmapped | - | 1355 |
| headlights | no_records | - | 2693 |
| headlights | not_closed | no_year_manifest | 29378 |
| hood | unmapped | - | 1355 |
| hood | no_records | - | 1396 |
| hood | not_closed | no_year_manifest | 30675 |
| ignition-coils | unmapped | - | 1355 |
| ignition-coils | no_records | - | 2415 |
| ignition-coils | not_closed | no_year_manifest | 29656 |
| liftgate | unmapped | - | 1355 |
| liftgate | no_records | - | 20869 |
| liftgate | not_closed | no_year_manifest | 11202 |
| power-steering-pump | unmapped | - | 1355 |
| power-steering-pump | no_records | - | 11215 |
| power-steering-pump | not_closed | no_year_manifest | 20856 |
| radiator | unmapped | - | 1355 |
| radiator | no_records | - | 1099 |
| radiator | not_closed | no_year_manifest | 30972 |
| side-mirrors | unmapped | - | 1355 |
| side-mirrors | no_records | - | 1240 |
| side-mirrors | not_closed | no_year_manifest | 30831 |
| starter | unmapped | - | 1355 |
| starter | no_records | - | 887 |
| starter | not_closed | no_year_manifest | 31184 |
| tail-lights | unmapped | - | 1355 |
| tail-lights | no_records | - | 2528 |
| tail-lights | not_closed | no_year_manifest | 29543 |
| tailgate | unmapped | - | 1355 |
| tailgate | no_records | - | 30794 |
| tailgate | not_closed | no_year_manifest | 1277 |
| throttle-body | unmapped | - | 1355 |
| throttle-body | no_records | - | 950 |
| throttle-body | not_closed | no_year_manifest | 31121 |
| trunk-lid | unmapped | - | 1355 |
| trunk-lid | no_records | - | 12650 |
| trunk-lid | not_closed | no_year_manifest | 19421 |
| window-regulator | unmapped | - | 1355 |
| window-regulator | no_records | - | 606 |
| window-regulator | not_closed | no_year_manifest | 31465 |
| window-switch | unmapped | - | 1355 |
| window-switch | no_records | - | 1683 |
| window-switch | not_closed | no_year_manifest | 30388 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 1355 |
| ac-compressor | no_records | - | 3059 |
| ac-compressor | split | option_split | 20787 |
| ac-compressor | conditional | conditional:engine_unattested | 8195 |
| ac-compressor | conditional | conditional:option | 30 |
| alternator | unmapped | - | 1355 |
| alternator | no_records | - | 1186 |
| alternator | split | option_split | 20403 |
| alternator | conditional | conditional:engine_unattested | 10482 |
| bumper-front | unmapped | - | 1355 |
| bumper-front | no_records | - | 2681 |
| bumper-front | split | option_split | 21573 |
| bumper-front | conditional | conditional:colour | 101 |
| bumper-front | conditional | conditional:engine_unattested | 7716 |
| bumper-rear | unmapped | - | 1355 |
| bumper-rear | no_records | - | 2611 |
| bumper-rear | split | option_split | 22538 |
| bumper-rear | conditional | conditional:engine_unattested | 6826 |
| bumper-rear | conditional | conditional:option | 96 |
| climate-control | unmapped | - | 1355 |
| climate-control | no_records | - | 6493 |
| climate-control | split | option_split | 21154 |
| climate-control | conditional | conditional:engine_unattested | 4401 |
| climate-control | conditional | conditional:package | 23 |
| door-front | unmapped | - | 1355 |
| door-front | no_records | - | 1816 |
| door-front | split | option_split | 17667 |
| door-front | conditional | conditional:engine_unattested | 12335 |
| door-front | conditional | conditional:option | 253 |
| door-rear | unmapped | - | 1355 |
| door-rear | no_records | - | 1596 |
| door-rear | split | option_split | 7491 |
| door-rear | split | slot_missing | 35 |
| door-rear | conditional | conditional:engine_unattested | 22045 |
| door-rear | conditional | conditional:option | 904 |
| fender | unmapped | - | 1355 |
| fender | no_records | - | 1495 |
| fender | split | option_split | 15691 |
| fender | split | slot_missing | 2 |
| fender | conditional | conditional:engine_unattested | 14883 |
| fuel-pump-module | unmapped | - | 1355 |
| fuel-pump-module | no_records | - | 1845 |
| fuel-pump-module | split | option_split | 18549 |
| fuel-pump-module | conditional | conditional:engine_unattested | 11674 |
| fuel-pump-module | conditional | conditional:option | 3 |
| gauge-cluster | unmapped | - | 1355 |
| gauge-cluster | no_records | - | 2610 |
| gauge-cluster | split | option_split | 28562 |
| gauge-cluster | conditional | conditional:engine_unattested | 853 |
| gauge-cluster | conditional | conditional:option | 46 |
| grille | unmapped | - | 1355 |
| grille | no_records | - | 13142 |
| grille | split | option_split | 12983 |
| grille | conditional | conditional:engine_unattested | 5804 |
| grille | conditional | conditional:option | 142 |
| headlights | unmapped | - | 1355 |
| headlights | no_records | - | 2693 |
| headlights | split | option_split | 23431 |
| headlights | conditional | conditional:engine_unattested | 5947 |
| hood | unmapped | - | 1355 |
| hood | no_records | - | 1396 |
| hood | split | option_split | 8055 |
| hood | conditional | conditional:engine_unattested | 22615 |
| hood | conditional | conditional:option | 5 |
| ignition-coils | unmapped | - | 1355 |
| ignition-coils | no_records | - | 2415 |
| ignition-coils | split | option_split | 19256 |
| ignition-coils | conditional | conditional:engine_unattested | 9424 |
| ignition-coils | conditional | conditional:package | 976 |
| liftgate | unmapped | - | 1355 |
| liftgate | no_records | - | 20869 |
| liftgate | split | option_split | 10457 |
| liftgate | conditional | conditional:engine_unattested | 745 |
| power-steering-pump | unmapped | - | 1355 |
| power-steering-pump | no_records | - | 11215 |
| power-steering-pump | split | option_split | 12085 |
| power-steering-pump | conditional | conditional:engine_unattested | 8696 |
| power-steering-pump | conditional | conditional:option | 75 |
| radiator | unmapped | - | 1355 |
| radiator | no_records | - | 1099 |
| radiator | split | option_split | 21716 |
| radiator | conditional | conditional:engine_unattested | 9256 |
| side-mirrors | unmapped | - | 1355 |
| side-mirrors | no_records | - | 1240 |
| side-mirrors | split | option_split | 28309 |
| side-mirrors | split | slot_missing | 4 |
| side-mirrors | conditional | conditional:engine_unattested | 2518 |
| starter | unmapped | - | 1355 |
| starter | no_records | - | 887 |
| starter | split | option_split | 21524 |
| starter | conditional | conditional:engine_unattested | 9660 |
| tail-lights | unmapped | - | 1355 |
| tail-lights | no_records | - | 2528 |
| tail-lights | split | option_split | 22364 |
| tail-lights | conditional | conditional:engine_unattested | 7134 |
| tail-lights | conditional | conditional:package | 45 |
| tailgate | unmapped | - | 1355 |
| tailgate | no_records | - | 30794 |
| tailgate | split | option_split | 283 |
| tailgate | conditional | conditional:engine_unattested | 994 |
| throttle-body | unmapped | - | 1355 |
| throttle-body | no_records | - | 950 |
| throttle-body | split | option_split | 21888 |
| throttle-body | conditional | conditional:engine_unattested | 9233 |
| trunk-lid | unmapped | - | 1355 |
| trunk-lid | no_records | - | 12650 |
| trunk-lid | split | option_split | 18874 |
| trunk-lid | conditional | conditional:engine_unattested | 547 |
| window-regulator | unmapped | - | 1355 |
| window-regulator | no_records | - | 606 |
| window-regulator | split | packaging_unstated | 31465 |
| window-switch | unmapped | - | 1355 |
| window-switch | no_records | - | 1683 |
| window-switch | split | no_candidates | 8 |
| window-switch | split | option_split | 21100 |
| window-switch | split | position_missing | 9280 |

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
- Nissan Rogue Sport: feed 'Rogue Sport' 40 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (35 cars, under catalog squash 'rogue'); unmapped until a reviewed entry exists)
- Nissan Van: feed 'Van' 0 cars
- Nissan Versa Note: feed 'Versa Note' 323 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (313 cars, under catalog squash 'versa'); unmapped until a reviewed entry exists)
