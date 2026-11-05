# OEM curation report: nissan

Raw: `50ac4a48cdc62d02bd819bec33a67d0f07d8a71e` @ `50ac4a48cdc6`; as of 2026-11-05T12:52:18Z.

- records 4029, classes 3925, list rows 0, year manifests 0, cells 6518
- Verified groups 0, engine vg groups 0, Likely groups 843
- blocked sites: none

## Gates standing for the whole namespace

- no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close (C1/C2); Verified is impossible by design until the crawler writes them
- no (site, category) of this namespace has passed the audit gate (CATEGORY_STATUS has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.infinitipartsdeal.com, www.nissanpartsdeal.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.infinitipartsdeal.com: only 0% of its 3381 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)
- www.nissanpartsdeal.com: only 0% of its 2820 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 1327 |
| ac-compressor | no_records | - | 2980 |
| ac-compressor | not_closed | no_year_manifest | 28885 |
| alternator | unmapped | - | 1327 |
| alternator | no_records | - | 1158 |
| alternator | not_closed | no_year_manifest | 30707 |
| bumper-front | unmapped | - | 1327 |
| bumper-front | no_records | - | 17043 |
| bumper-front | not_closed | no_year_manifest | 14822 |
| bumper-rear | unmapped | - | 1327 |
| bumper-rear | no_records | - | 16397 |
| bumper-rear | not_closed | no_year_manifest | 15468 |
| climate-control | unmapped | - | 1327 |
| climate-control | no_records | - | 6455 |
| climate-control | not_closed | no_year_manifest | 25410 |
| door-front | unmapped | - | 1327 |
| door-front | no_records | - | 15358 |
| door-front | not_closed | no_year_manifest | 16507 |
| door-rear | unmapped | - | 1327 |
| door-rear | no_records | - | 16067 |
| door-rear | not_closed | no_year_manifest | 15798 |
| fender | unmapped | - | 1327 |
| fender | no_records | - | 16807 |
| fender | not_closed | no_year_manifest | 15058 |
| fuel-pump-module | unmapped | - | 1327 |
| fuel-pump-module | no_records | - | 1795 |
| fuel-pump-module | not_closed | no_year_manifest | 30070 |
| gauge-cluster | unmapped | - | 1327 |
| gauge-cluster | no_records | - | 16806 |
| gauge-cluster | not_closed | no_year_manifest | 15059 |
| grille | unmapped | - | 1327 |
| grille | no_records | - | 22235 |
| grille | not_closed | no_year_manifest | 9630 |
| headlights | unmapped | - | 1327 |
| headlights | no_records | - | 2641 |
| headlights | not_closed | no_year_manifest | 29224 |
| hood | unmapped | - | 1327 |
| hood | no_records | - | 16480 |
| hood | not_closed | no_year_manifest | 15385 |
| ignition-coils | unmapped | - | 1327 |
| ignition-coils | no_records | - | 6036 |
| ignition-coils | not_closed | no_year_manifest | 25829 |
| liftgate | unmapped | - | 1327 |
| liftgate | no_records | - | 27666 |
| liftgate | not_closed | no_year_manifest | 4199 |
| power-steering-pump | unmapped | - | 1327 |
| power-steering-pump | no_records | - | 11067 |
| power-steering-pump | not_closed | no_year_manifest | 20798 |
| radiator | unmapped | - | 1327 |
| radiator | no_records | - | 14083 |
| radiator | not_closed | no_year_manifest | 17782 |
| side-mirrors | unmapped | - | 1327 |
| side-mirrors | no_records | - | 1209 |
| side-mirrors | not_closed | no_year_manifest | 30656 |
| starter | unmapped | - | 1327 |
| starter | no_records | - | 864 |
| starter | not_closed | no_year_manifest | 31001 |
| tail-lights | unmapped | - | 1327 |
| tail-lights | no_records | - | 2499 |
| tail-lights | not_closed | no_year_manifest | 29366 |
| throttle-body | unmapped | - | 1327 |
| throttle-body | no_records | - | 927 |
| throttle-body | not_closed | no_year_manifest | 30938 |
| trunk-lid | unmapped | - | 1327 |
| trunk-lid | no_records | - | 20187 |
| trunk-lid | not_closed | no_year_manifest | 11678 |
| window-regulator | unmapped | - | 1327 |
| window-regulator | no_records | - | 593 |
| window-regulator | not_closed | no_year_manifest | 31272 |
| window-switch | unmapped | - | 1327 |
| window-switch | no_records | - | 1659 |
| window-switch | not_closed | no_year_manifest | 30206 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 1327 |
| ac-compressor | no_records | - | 2980 |
| ac-compressor | split | option_split | 20695 |
| ac-compressor | conditional | conditional:notes_not_own_page | 7297 |
| ac-compressor | conditional | conditional:option | 30 |
| ac-compressor | conditional | conditional:option_layout | 863 |
| alternator | unmapped | - | 1327 |
| alternator | no_records | - | 1158 |
| alternator | split | option_split | 20298 |
| alternator | conditional | conditional:notes_not_own_page | 8087 |
| alternator | conditional | conditional:option_layout | 2322 |
| bumper-front | unmapped | - | 1327 |
| bumper-front | no_records | - | 17043 |
| bumper-front | split | option_split | 10319 |
| bumper-front | conditional | conditional:notes_not_own_page | 3952 |
| bumper-front | conditional | conditional:option_layout | 551 |
| bumper-rear | unmapped | - | 1327 |
| bumper-rear | no_records | - | 16397 |
| bumper-rear | split | option_split | 11366 |
| bumper-rear | conditional | conditional:notes_not_own_page | 3532 |
| bumper-rear | conditional | conditional:option_layout | 570 |
| climate-control | unmapped | - | 1327 |
| climate-control | no_records | - | 6455 |
| climate-control | split | option_split | 21049 |
| climate-control | conditional | conditional:notes_not_own_page | 3271 |
| climate-control | conditional | conditional:option_layout | 1090 |
| door-front | unmapped | - | 1327 |
| door-front | no_records | - | 15358 |
| door-front | split | option_split | 9755 |
| door-front | conditional | conditional:notes_not_own_page | 6069 |
| door-front | conditional | conditional:option_layout | 683 |
| door-rear | unmapped | - | 1327 |
| door-rear | no_records | - | 16067 |
| door-rear | split | option_split | 806 |
| door-rear | conditional | conditional:notes_not_own_page | 11428 |
| door-rear | conditional | conditional:option | 903 |
| door-rear | conditional | conditional:option_layout | 2661 |
| fender | unmapped | - | 1327 |
| fender | no_records | - | 16807 |
| fender | split | option_split | 8060 |
| fender | conditional | conditional:notes_not_own_page | 5764 |
| fender | conditional | conditional:option_layout | 1234 |
| fuel-pump-module | unmapped | - | 1327 |
| fuel-pump-module | no_records | - | 1795 |
| fuel-pump-module | split | option_split | 18453 |
| fuel-pump-module | conditional | conditional:notes_not_own_page | 10490 |
| fuel-pump-module | conditional | conditional:option | 3 |
| fuel-pump-module | conditional | conditional:option_layout | 1124 |
| gauge-cluster | unmapped | - | 1327 |
| gauge-cluster | no_records | - | 16806 |
| gauge-cluster | split | option_split | 14059 |
| gauge-cluster | conditional | conditional:notes_not_own_page | 999 |
| gauge-cluster | conditional | conditional:option | 1 |
| grille | unmapped | - | 1327 |
| grille | no_records | - | 22235 |
| grille | split | option_split | 6048 |
| grille | conditional | conditional:notes_not_own_page | 2402 |
| grille | conditional | conditional:option | 143 |
| grille | conditional | conditional:option_layout | 1037 |
| headlights | unmapped | - | 1327 |
| headlights | no_records | - | 2641 |
| headlights | split | option_split | 23314 |
| headlights | conditional | conditional:notes_not_own_page | 4351 |
| headlights | conditional | conditional:option_layout | 1559 |
| hood | unmapped | - | 1327 |
| hood | no_records | - | 16480 |
| hood | split | option_split | 3405 |
| hood | conditional | conditional:notes_not_own_page | 9259 |
| hood | conditional | conditional:option_layout | 2721 |
| ignition-coils | unmapped | - | 1327 |
| ignition-coils | no_records | - | 6036 |
| ignition-coils | split | option_split | 16142 |
| ignition-coils | conditional | conditional:notes_not_own_page | 9563 |
| ignition-coils | conditional | conditional:option_layout | 124 |
| liftgate | unmapped | - | 1327 |
| liftgate | no_records | - | 27666 |
| liftgate | split | option_split | 3679 |
| liftgate | conditional | conditional:notes_not_own_page | 482 |
| liftgate | conditional | conditional:option_layout | 38 |
| power-steering-pump | unmapped | - | 1327 |
| power-steering-pump | no_records | - | 11067 |
| power-steering-pump | split | option_split | 12067 |
| power-steering-pump | conditional | conditional:notes_not_own_page | 6936 |
| power-steering-pump | conditional | conditional:option | 75 |
| power-steering-pump | conditional | conditional:option_layout | 1720 |
| radiator | unmapped | - | 1327 |
| radiator | no_records | - | 14083 |
| radiator | split | option_split | 12771 |
| radiator | conditional | conditional:notes_not_own_page | 4469 |
| radiator | conditional | conditional:option_layout | 542 |
| side-mirrors | unmapped | - | 1327 |
| side-mirrors | no_records | - | 1209 |
| side-mirrors | split | option_split | 28169 |
| side-mirrors | split | slot_missing | 4 |
| side-mirrors | conditional | conditional:notes_not_own_page | 2232 |
| side-mirrors | conditional | conditional:option_layout | 251 |
| starter | unmapped | - | 1327 |
| starter | no_records | - | 864 |
| starter | split | option_split | 21383 |
| starter | conditional | conditional:notes_not_own_page | 8048 |
| starter | conditional | conditional:option_layout | 1570 |
| tail-lights | unmapped | - | 1327 |
| tail-lights | no_records | - | 2499 |
| tail-lights | split | option_split | 22250 |
| tail-lights | conditional | conditional:notes_not_own_page | 5896 |
| tail-lights | conditional | conditional:option_layout | 1220 |
| throttle-body | unmapped | - | 1327 |
| throttle-body | no_records | - | 927 |
| throttle-body | split | option_split | 21821 |
| throttle-body | conditional | conditional:notes_not_own_page | 8369 |
| throttle-body | conditional | conditional:option_layout | 748 |
| trunk-lid | unmapped | - | 1327 |
| trunk-lid | no_records | - | 20187 |
| trunk-lid | split | option_split | 11463 |
| trunk-lid | conditional | conditional:notes_not_own_page | 158 |
| trunk-lid | conditional | conditional:option_layout | 57 |
| window-regulator | unmapped | - | 1327 |
| window-regulator | no_records | - | 593 |
| window-regulator | split | packaging_unstated | 31272 |
| window-switch | unmapped | - | 1327 |
| window-switch | no_records | - | 1659 |
| window-switch | split | no_candidates | 9 |
| window-switch | split | option_split | 20996 |
| window-switch | split | position_missing | 9201 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- disputed_class: 104
- universal_part_suspect: 13

## Unknown note clauses (top 30)

- `Package Quantity: 1`: 64
- `NO PAINT`: 55
- `HITACHI`: 47
- `MITSUBISHI`: 37
- `W. SE`: 23
- `Require Quantity: 06`: 21
- `U/4S. GXE`: 21
- `W`: 20
- `Production Date: from 07/2001`: 19
- `ELEC`: 17
- `F/POWER WINDOW`: 16
- `PRIMER`: 16
- `Production Date: from 01/2004`: 16
- `Production Date: 04/1999-09/1999`: 15
- `Production Date: 12/1998-01/2000`: 15
- `Production Date: from 04/2003`: 15
- `SKULL CAP`: 15
- `OHI`: 14
- `Production Date: 08/2001-01/2004`: 14
- `Production Date: from 08/2004`: 14
- `*W. VQ35DE`: 13
- `Production Date: 08/2006-04/2007`: 13
- `Require Quantity: 02`: 13
- `F/AIR CONDITIONER-STD TYPE`: 12
- `NO PAINTING`: 12
- `S`: 12
- `Production Date: from 01/1986`: 11
- `Production Date: from 01/2000`: 11
- `Production Date: from 10/1998`: 11
- `Interior Color: BLACK`: 10

## Unmapped catalog models

- Nissan Hardbody Pickup (D21): feed 'Hardbody Pickup (D21)' 0 cars (excluded: catalog model with no feed cars as 'Hardbody Pickup (D21)' (inventory 2026-11-04); nothing to map)
- Nissan Hardbody Pickup (D21U): feed 'Hardbody Pickup (D21U)' 0 cars (excluded: catalog model with no feed cars as 'Hardbody Pickup (D21U)' (inventory 2026-11-04); nothing to map)
- Nissan Kicks Play: feed 'Kicks Play' 0 cars
- Nissan Rogue Sport: feed 'Rogue Sport' 35 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (35 cars, under catalog squash 'rogue'); unmapped until a reviewed entry exists)
- Nissan Van: feed 'Van' 0 cars
- Nissan Versa Note: feed 'Versa Note' 316 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (313 cars, under catalog squash 'versa'); unmapped until a reviewed entry exists)
