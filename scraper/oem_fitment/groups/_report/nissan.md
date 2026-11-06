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
| ac-compressor | unmapped | - | 1330 |
| ac-compressor | no_records | - | 2992 |
| ac-compressor | not_closed | no_year_manifest | 28804 |
| alternator | unmapped | - | 1330 |
| alternator | no_records | - | 1151 |
| alternator | not_closed | no_year_manifest | 30645 |
| bumper-front | unmapped | - | 1330 |
| bumper-front | no_records | - | 2632 |
| bumper-front | not_closed | no_year_manifest | 29164 |
| bumper-rear | unmapped | - | 1330 |
| bumper-rear | no_records | - | 2565 |
| bumper-rear | not_closed | no_year_manifest | 29231 |
| climate-control | unmapped | - | 1330 |
| climate-control | no_records | - | 6438 |
| climate-control | not_closed | no_year_manifest | 25358 |
| door-front | unmapped | - | 1330 |
| door-front | no_records | - | 1772 |
| door-front | not_closed | no_year_manifest | 30024 |
| door-rear | unmapped | - | 1330 |
| door-rear | no_records | - | 1567 |
| door-rear | not_closed | no_year_manifest | 30229 |
| fender | unmapped | - | 1330 |
| fender | no_records | - | 1466 |
| fender | not_closed | no_year_manifest | 30330 |
| fuel-pump-module | unmapped | - | 1330 |
| fuel-pump-module | no_records | - | 1796 |
| fuel-pump-module | not_closed | no_year_manifest | 30000 |
| gauge-cluster | unmapped | - | 1330 |
| gauge-cluster | no_records | - | 2561 |
| gauge-cluster | not_closed | no_year_manifest | 29235 |
| grille | unmapped | - | 1330 |
| grille | no_records | - | 13017 |
| grille | not_closed | no_year_manifest | 18779 |
| headlights | unmapped | - | 1330 |
| headlights | no_records | - | 2640 |
| headlights | not_closed | no_year_manifest | 29156 |
| hood | unmapped | - | 1330 |
| hood | no_records | - | 1380 |
| hood | not_closed | no_year_manifest | 30416 |
| ignition-coils | unmapped | - | 1330 |
| ignition-coils | no_records | - | 2372 |
| ignition-coils | not_closed | no_year_manifest | 29424 |
| liftgate | unmapped | - | 1330 |
| liftgate | no_records | - | 20701 |
| liftgate | not_closed | no_year_manifest | 11095 |
| power-steering-pump | unmapped | - | 1330 |
| power-steering-pump | no_records | - | 11058 |
| power-steering-pump | not_closed | no_year_manifest | 20738 |
| radiator | unmapped | - | 1330 |
| radiator | no_records | - | 1073 |
| radiator | not_closed | no_year_manifest | 30723 |
| side-mirrors | unmapped | - | 1330 |
| side-mirrors | no_records | - | 1204 |
| side-mirrors | not_closed | no_year_manifest | 30592 |
| starter | unmapped | - | 1330 |
| starter | no_records | - | 861 |
| starter | not_closed | no_year_manifest | 30935 |
| tail-lights | unmapped | - | 1330 |
| tail-lights | no_records | - | 2495 |
| tail-lights | not_closed | no_year_manifest | 29301 |
| tailgate | unmapped | - | 1330 |
| tailgate | no_records | - | 30537 |
| tailgate | not_closed | no_year_manifest | 1259 |
| throttle-body | unmapped | - | 1330 |
| throttle-body | no_records | - | 925 |
| throttle-body | not_closed | no_year_manifest | 30871 |
| trunk-lid | unmapped | - | 1330 |
| trunk-lid | no_records | - | 12494 |
| trunk-lid | not_closed | no_year_manifest | 19302 |
| window-regulator | unmapped | - | 1330 |
| window-regulator | no_records | - | 592 |
| window-regulator | not_closed | no_year_manifest | 31204 |
| window-switch | unmapped | - | 1330 |
| window-switch | no_records | - | 1659 |
| window-switch | not_closed | no_year_manifest | 30137 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 1330 |
| ac-compressor | no_records | - | 2992 |
| ac-compressor | split | option_split | 20644 |
| ac-compressor | conditional | conditional:engine_unattested | 8130 |
| ac-compressor | conditional | conditional:option | 30 |
| alternator | unmapped | - | 1330 |
| alternator | no_records | - | 1151 |
| alternator | split | option_split | 20250 |
| alternator | conditional | conditional:engine_unattested | 10395 |
| bumper-front | unmapped | - | 1330 |
| bumper-front | no_records | - | 2632 |
| bumper-front | split | option_split | 21430 |
| bumper-front | conditional | conditional:colour | 102 |
| bumper-front | conditional | conditional:engine_unattested | 7632 |
| bumper-rear | unmapped | - | 1330 |
| bumper-rear | no_records | - | 2565 |
| bumper-rear | split | option_split | 22379 |
| bumper-rear | conditional | conditional:engine_unattested | 6755 |
| bumper-rear | conditional | conditional:option | 97 |
| climate-control | unmapped | - | 1330 |
| climate-control | no_records | - | 6438 |
| climate-control | split | option_split | 21007 |
| climate-control | conditional | conditional:engine_unattested | 4327 |
| climate-control | conditional | conditional:package | 24 |
| door-front | unmapped | - | 1330 |
| door-front | no_records | - | 1772 |
| door-front | split | option_split | 17531 |
| door-front | conditional | conditional:engine_unattested | 12246 |
| door-front | conditional | conditional:option | 247 |
| door-rear | unmapped | - | 1330 |
| door-rear | no_records | - | 1567 |
| door-rear | split | option_split | 7388 |
| door-rear | split | slot_missing | 34 |
| door-rear | conditional | conditional:engine_unattested | 21906 |
| door-rear | conditional | conditional:option | 901 |
| fender | unmapped | - | 1330 |
| fender | no_records | - | 1466 |
| fender | split | option_split | 15588 |
| fender | split | slot_missing | 2 |
| fender | conditional | conditional:engine_unattested | 14740 |
| fuel-pump-module | unmapped | - | 1330 |
| fuel-pump-module | no_records | - | 1796 |
| fuel-pump-module | split | option_split | 18401 |
| fuel-pump-module | conditional | conditional:engine_unattested | 11596 |
| fuel-pump-module | conditional | conditional:option | 3 |
| gauge-cluster | unmapped | - | 1330 |
| gauge-cluster | no_records | - | 2561 |
| gauge-cluster | split | option_split | 28353 |
| gauge-cluster | conditional | conditional:engine_unattested | 838 |
| gauge-cluster | conditional | conditional:option | 44 |
| grille | unmapped | - | 1330 |
| grille | no_records | - | 13017 |
| grille | split | option_split | 12872 |
| grille | conditional | conditional:engine_unattested | 5768 |
| grille | conditional | conditional:option | 139 |
| headlights | unmapped | - | 1330 |
| headlights | no_records | - | 2640 |
| headlights | split | option_split | 23273 |
| headlights | conditional | conditional:engine_unattested | 5883 |
| hood | unmapped | - | 1330 |
| hood | no_records | - | 1380 |
| hood | split | option_split | 8014 |
| hood | conditional | conditional:engine_unattested | 22397 |
| hood | conditional | conditional:option | 5 |
| ignition-coils | unmapped | - | 1330 |
| ignition-coils | no_records | - | 2372 |
| ignition-coils | split | option_split | 19160 |
| ignition-coils | conditional | conditional:engine_unattested | 9300 |
| ignition-coils | conditional | conditional:package | 964 |
| liftgate | unmapped | - | 1330 |
| liftgate | no_records | - | 20701 |
| liftgate | split | option_split | 10360 |
| liftgate | conditional | conditional:engine_unattested | 735 |
| power-steering-pump | unmapped | - | 1330 |
| power-steering-pump | no_records | - | 11058 |
| power-steering-pump | split | option_split | 12026 |
| power-steering-pump | conditional | conditional:engine_unattested | 8635 |
| power-steering-pump | conditional | conditional:option | 77 |
| radiator | unmapped | - | 1330 |
| radiator | no_records | - | 1073 |
| radiator | split | option_split | 21559 |
| radiator | conditional | conditional:engine_unattested | 9164 |
| side-mirrors | unmapped | - | 1330 |
| side-mirrors | no_records | - | 1204 |
| side-mirrors | split | option_split | 28102 |
| side-mirrors | split | slot_missing | 4 |
| side-mirrors | conditional | conditional:engine_unattested | 2486 |
| starter | unmapped | - | 1330 |
| starter | no_records | - | 861 |
| starter | split | option_split | 21354 |
| starter | conditional | conditional:engine_unattested | 9581 |
| tail-lights | unmapped | - | 1330 |
| tail-lights | no_records | - | 2495 |
| tail-lights | split | option_split | 22204 |
| tail-lights | conditional | conditional:engine_unattested | 7056 |
| tail-lights | conditional | conditional:package | 41 |
| tailgate | unmapped | - | 1330 |
| tailgate | no_records | - | 30537 |
| tailgate | split | option_split | 269 |
| tailgate | conditional | conditional:engine_unattested | 990 |
| throttle-body | unmapped | - | 1330 |
| throttle-body | no_records | - | 925 |
| throttle-body | split | option_split | 21749 |
| throttle-body | conditional | conditional:engine_unattested | 9122 |
| trunk-lid | unmapped | - | 1330 |
| trunk-lid | no_records | - | 12494 |
| trunk-lid | split | option_split | 18759 |
| trunk-lid | conditional | conditional:engine_unattested | 543 |
| window-regulator | unmapped | - | 1330 |
| window-regulator | no_records | - | 592 |
| window-regulator | split | packaging_unstated | 31204 |
| window-switch | unmapped | - | 1330 |
| window-switch | no_records | - | 1659 |
| window-switch | split | no_candidates | 9 |
| window-switch | split | option_split | 20949 |
| window-switch | split | position_missing | 9179 |

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

- Nissan 300ZX: feed '300ZX' 55 cars
- Nissan Hardbody Pickup (D21): feed 'Hardbody Pickup (D21)' 0 cars (excluded: catalog model with no feed cars as 'Hardbody Pickup (D21)' (inventory 2026-11-04); nothing to map)
- Nissan Hardbody Pickup (D21U): feed 'Hardbody Pickup (D21U)' 0 cars (excluded: catalog model with no feed cars as 'Hardbody Pickup (D21U)' (inventory 2026-11-04); nothing to map)
- Nissan Kicks Play: feed 'Kicks Play' 0 cars
- Nissan Pulsar NX: feed 'Pulsar NX' 3 cars
- Nissan Rogue Sport: feed 'Rogue Sport' 36 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (35 cars, under catalog squash 'rogue'); unmapped until a reviewed entry exists)
- Nissan Van: feed 'Van' 0 cars
- Nissan Versa Note: feed 'Versa Note' 318 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (313 cars, under catalog squash 'versa'); unmapped until a reviewed entry exists)
