# OEM curation report: nissan

Raw: `ceccc800d7ba22c0291121baabb0a9292eb8f271` @ `ceccc800d7ba`; as of 2026-11-05T17:56:52Z.

- records 5686, classes 5544, list rows 0, year manifests 0, cells 8377
- Verified groups 0, engine vg groups 0, Likely groups 905
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
| ac-compressor | unmapped | - | 1328 |
| ac-compressor | no_records | - | 2993 |
| ac-compressor | not_closed | no_year_manifest | 28814 |
| alternator | unmapped | - | 1328 |
| alternator | no_records | - | 1156 |
| alternator | not_closed | no_year_manifest | 30651 |
| bumper-front | unmapped | - | 1328 |
| bumper-front | no_records | - | 2637 |
| bumper-front | not_closed | no_year_manifest | 29170 |
| bumper-rear | unmapped | - | 1328 |
| bumper-rear | no_records | - | 2558 |
| bumper-rear | not_closed | no_year_manifest | 29249 |
| climate-control | unmapped | - | 1328 |
| climate-control | no_records | - | 6446 |
| climate-control | not_closed | no_year_manifest | 25361 |
| door-front | unmapped | - | 1328 |
| door-front | no_records | - | 1773 |
| door-front | not_closed | no_year_manifest | 30034 |
| door-rear | unmapped | - | 1328 |
| door-rear | no_records | - | 1566 |
| door-rear | not_closed | no_year_manifest | 30241 |
| fender | unmapped | - | 1328 |
| fender | no_records | - | 1467 |
| fender | not_closed | no_year_manifest | 30340 |
| fuel-pump-module | unmapped | - | 1328 |
| fuel-pump-module | no_records | - | 1802 |
| fuel-pump-module | not_closed | no_year_manifest | 30005 |
| gauge-cluster | unmapped | - | 1328 |
| gauge-cluster | no_records | - | 2559 |
| gauge-cluster | not_closed | no_year_manifest | 29248 |
| grille | unmapped | - | 1328 |
| grille | no_records | - | 13011 |
| grille | not_closed | no_year_manifest | 18796 |
| headlights | unmapped | - | 1328 |
| headlights | no_records | - | 2641 |
| headlights | not_closed | no_year_manifest | 29166 |
| hood | unmapped | - | 1328 |
| hood | no_records | - | 1384 |
| hood | not_closed | no_year_manifest | 30423 |
| ignition-coils | unmapped | - | 1328 |
| ignition-coils | no_records | - | 2368 |
| ignition-coils | not_closed | no_year_manifest | 29439 |
| liftgate | unmapped | - | 1328 |
| liftgate | no_records | - | 20702 |
| liftgate | not_closed | no_year_manifest | 11105 |
| power-steering-pump | unmapped | - | 1328 |
| power-steering-pump | no_records | - | 11063 |
| power-steering-pump | not_closed | no_year_manifest | 20744 |
| radiator | unmapped | - | 1328 |
| radiator | no_records | - | 1076 |
| radiator | not_closed | no_year_manifest | 30731 |
| side-mirrors | unmapped | - | 1328 |
| side-mirrors | no_records | - | 1209 |
| side-mirrors | not_closed | no_year_manifest | 30598 |
| starter | unmapped | - | 1328 |
| starter | no_records | - | 866 |
| starter | not_closed | no_year_manifest | 30941 |
| tail-lights | unmapped | - | 1328 |
| tail-lights | no_records | - | 2496 |
| tail-lights | not_closed | no_year_manifest | 29311 |
| tailgate | unmapped | - | 1328 |
| tailgate | no_records | - | 30556 |
| tailgate | not_closed | no_year_manifest | 1251 |
| throttle-body | unmapped | - | 1328 |
| throttle-body | no_records | - | 927 |
| throttle-body | not_closed | no_year_manifest | 30880 |
| trunk-lid | unmapped | - | 1328 |
| trunk-lid | no_records | - | 12497 |
| trunk-lid | not_closed | no_year_manifest | 19310 |
| window-regulator | unmapped | - | 1328 |
| window-regulator | no_records | - | 598 |
| window-regulator | not_closed | no_year_manifest | 31209 |
| window-switch | unmapped | - | 1328 |
| window-switch | no_records | - | 1663 |
| window-switch | not_closed | no_year_manifest | 30144 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 1328 |
| ac-compressor | no_records | - | 2993 |
| ac-compressor | split | option_split | 20648 |
| ac-compressor | conditional | conditional:engine_unattested | 8136 |
| ac-compressor | conditional | conditional:option | 30 |
| alternator | unmapped | - | 1328 |
| alternator | no_records | - | 1156 |
| alternator | split | option_split | 20259 |
| alternator | conditional | conditional:engine_unattested | 10392 |
| bumper-front | unmapped | - | 1328 |
| bumper-front | no_records | - | 2637 |
| bumper-front | split | option_split | 21426 |
| bumper-front | conditional | conditional:colour | 102 |
| bumper-front | conditional | conditional:engine_unattested | 7642 |
| bumper-rear | unmapped | - | 1328 |
| bumper-rear | no_records | - | 2558 |
| bumper-rear | split | option_split | 22383 |
| bumper-rear | conditional | conditional:engine_unattested | 6769 |
| bumper-rear | conditional | conditional:option | 97 |
| climate-control | unmapped | - | 1328 |
| climate-control | no_records | - | 6446 |
| climate-control | split | option_split | 21002 |
| climate-control | conditional | conditional:engine_unattested | 4336 |
| climate-control | conditional | conditional:package | 23 |
| door-front | unmapped | - | 1328 |
| door-front | no_records | - | 1773 |
| door-front | split | option_split | 17528 |
| door-front | conditional | conditional:engine_unattested | 12260 |
| door-front | conditional | conditional:option | 246 |
| door-rear | unmapped | - | 1328 |
| door-rear | no_records | - | 1566 |
| door-rear | split | option_split | 7387 |
| door-rear | split | slot_missing | 33 |
| door-rear | conditional | conditional:engine_unattested | 21919 |
| door-rear | conditional | conditional:option | 902 |
| fender | unmapped | - | 1328 |
| fender | no_records | - | 1467 |
| fender | split | option_split | 15582 |
| fender | split | slot_missing | 2 |
| fender | conditional | conditional:engine_unattested | 14756 |
| fuel-pump-module | unmapped | - | 1328 |
| fuel-pump-module | no_records | - | 1802 |
| fuel-pump-module | split | option_split | 18408 |
| fuel-pump-module | conditional | conditional:engine_unattested | 11594 |
| fuel-pump-module | conditional | conditional:option | 3 |
| gauge-cluster | unmapped | - | 1328 |
| gauge-cluster | no_records | - | 2559 |
| gauge-cluster | split | option_split | 28369 |
| gauge-cluster | conditional | conditional:engine_unattested | 835 |
| gauge-cluster | conditional | conditional:option | 44 |
| grille | unmapped | - | 1328 |
| grille | no_records | - | 13011 |
| grille | split | option_split | 12869 |
| grille | conditional | conditional:engine_unattested | 5786 |
| grille | conditional | conditional:option | 141 |
| headlights | unmapped | - | 1328 |
| headlights | no_records | - | 2641 |
| headlights | split | option_split | 23261 |
| headlights | conditional | conditional:engine_unattested | 5905 |
| hood | unmapped | - | 1328 |
| hood | no_records | - | 1384 |
| hood | split | option_split | 8015 |
| hood | conditional | conditional:engine_unattested | 22403 |
| hood | conditional | conditional:option | 5 |
| ignition-coils | unmapped | - | 1328 |
| ignition-coils | no_records | - | 2368 |
| ignition-coils | split | option_split | 19179 |
| ignition-coils | conditional | conditional:engine_unattested | 9300 |
| ignition-coils | conditional | conditional:package | 960 |
| liftgate | unmapped | - | 1328 |
| liftgate | no_records | - | 20702 |
| liftgate | split | option_split | 10368 |
| liftgate | conditional | conditional:engine_unattested | 737 |
| power-steering-pump | unmapped | - | 1328 |
| power-steering-pump | no_records | - | 11063 |
| power-steering-pump | split | option_split | 12037 |
| power-steering-pump | conditional | conditional:engine_unattested | 8632 |
| power-steering-pump | conditional | conditional:option | 75 |
| radiator | unmapped | - | 1328 |
| radiator | no_records | - | 1076 |
| radiator | split | option_split | 21551 |
| radiator | conditional | conditional:engine_unattested | 9180 |
| side-mirrors | unmapped | - | 1328 |
| side-mirrors | no_records | - | 1209 |
| side-mirrors | split | option_split | 28112 |
| side-mirrors | split | slot_missing | 4 |
| side-mirrors | conditional | conditional:engine_unattested | 2482 |
| starter | unmapped | - | 1328 |
| starter | no_records | - | 866 |
| starter | split | option_split | 21349 |
| starter | conditional | conditional:engine_unattested | 9592 |
| tail-lights | unmapped | - | 1328 |
| tail-lights | no_records | - | 2496 |
| tail-lights | split | option_split | 22208 |
| tail-lights | conditional | conditional:engine_unattested | 7062 |
| tail-lights | conditional | conditional:package | 41 |
| tailgate | unmapped | - | 1328 |
| tailgate | no_records | - | 30556 |
| tailgate | split | option_split | 271 |
| tailgate | conditional | conditional:engine_unattested | 980 |
| throttle-body | unmapped | - | 1328 |
| throttle-body | no_records | - | 927 |
| throttle-body | split | option_split | 21762 |
| throttle-body | conditional | conditional:engine_unattested | 9118 |
| trunk-lid | unmapped | - | 1328 |
| trunk-lid | no_records | - | 12497 |
| trunk-lid | split | option_split | 18765 |
| trunk-lid | conditional | conditional:engine_unattested | 545 |
| window-regulator | unmapped | - | 1328 |
| window-regulator | no_records | - | 598 |
| window-regulator | split | packaging_unstated | 31209 |
| window-switch | unmapped | - | 1328 |
| window-switch | no_records | - | 1663 |
| window-switch | split | no_candidates | 9 |
| window-switch | split | option_split | 20935 |
| window-switch | split | position_missing | 9200 |

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
- Nissan Rogue Sport: feed 'Rogue Sport' 35 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (35 cars, under catalog squash 'rogue'); unmapped until a reviewed entry exists)
- Nissan Van: feed 'Van' 0 cars
- Nissan Versa Note: feed 'Versa Note' 317 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (313 cars, under catalog squash 'versa'); unmapped until a reviewed entry exists)
