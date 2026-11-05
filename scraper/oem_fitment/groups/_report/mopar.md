# OEM curation report: mopar

Raw: `ceccc800d7ba22c0291121baabb0a9292eb8f271` @ `ceccc800d7ba`; as of 2026-11-05T03:26:17Z.

- records 1716, classes 1700, list rows 0, year manifests 0, cells 3980
- Verified groups 0, engine vg groups 0, Likely groups 320
- blocked sites: none

## Gates standing for the whole namespace

- no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close (C1/C2); Verified is impossible by design until the crawler writes them
- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.moparpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.moparpartsgiant.com: only 2% of its 1522 fitment rows can be coverage: its option column holds trims (option_column_is_trims), which count only after a namespace audit (spec 5.2)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2337 |
| ac-compressor | no_records | - | 20555 |
| ac-compressor | not_closed | no_year_manifest | 21223 |
| alternator | unmapped | - | 2337 |
| alternator | no_records | - | 12915 |
| alternator | not_closed | no_year_manifest | 28863 |
| bumper-front | unmapped | - | 2337 |
| bumper-front | no_records | - | 35045 |
| bumper-front | not_closed | no_year_manifest | 6733 |
| bumper-rear | unmapped | - | 2337 |
| bumper-rear | no_records | - | 33037 |
| bumper-rear | not_closed | no_year_manifest | 8741 |
| climate-control | unmapped | - | 2337 |
| climate-control | no_records | - | 29480 |
| climate-control | not_closed | no_year_manifest | 12298 |
| door-front | unmapped | - | 2337 |
| door-front | no_records | - | 33958 |
| door-front | not_closed | no_year_manifest | 7820 |
| door-rear | unmapped | - | 2337 |
| door-rear | no_records | - | 33536 |
| door-rear | not_closed | no_year_manifest | 8242 |
| fender | unmapped | - | 2337 |
| fender | no_records | - | 33896 |
| fender | not_closed | no_year_manifest | 7882 |
| fuel-pump-module | unmapped | - | 2337 |
| fuel-pump-module | no_records | - | 21852 |
| fuel-pump-module | not_closed | no_year_manifest | 19926 |
| gauge-cluster | unmapped | - | 2337 |
| gauge-cluster | no_records | - | 39486 |
| gauge-cluster | not_closed | no_year_manifest | 2292 |
| grille | unmapped | - | 2337 |
| grille | no_records | - | 36369 |
| grille | not_closed | no_year_manifest | 5409 |
| headlights | unmapped | - | 2337 |
| headlights | no_records | - | 27263 |
| headlights | not_closed | no_year_manifest | 14515 |
| hood | unmapped | - | 2337 |
| hood | no_records | - | 33571 |
| hood | not_closed | no_year_manifest | 8207 |
| ignition-coils | unmapped | - | 2337 |
| ignition-coils | no_records | - | 5044 |
| ignition-coils | not_closed | no_year_manifest | 36734 |
| liftgate | unmapped | - | 2337 |
| liftgate | no_records | - | 34921 |
| liftgate | not_closed | no_year_manifest | 6857 |
| power-steering-pump | unmapped | - | 2337 |
| power-steering-pump | no_records | - | 17990 |
| power-steering-pump | not_closed | no_year_manifest | 23788 |
| radiator | unmapped | - | 2337 |
| radiator | no_records | - | 26622 |
| radiator | not_closed | no_year_manifest | 15156 |
| side-mirrors | unmapped | - | 2337 |
| side-mirrors | no_records | - | 26257 |
| side-mirrors | not_closed | no_year_manifest | 15521 |
| starter | unmapped | - | 2337 |
| starter | no_records | - | 10413 |
| starter | not_closed | no_year_manifest | 31365 |
| tail-lights | unmapped | - | 2337 |
| tail-lights | no_records | - | 30875 |
| tail-lights | not_closed | no_year_manifest | 10903 |
| throttle-body | unmapped | - | 2337 |
| throttle-body | no_records | - | 10812 |
| throttle-body | not_closed | no_year_manifest | 30966 |
| window-regulator | unmapped | - | 2337 |
| window-regulator | no_records | - | 23300 |
| window-regulator | not_closed | no_year_manifest | 18478 |
| window-switch | unmapped | - | 2337 |
| window-switch | no_records | - | 21850 |
| window-switch | not_closed | no_year_manifest | 19928 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2337 |
| ac-compressor | no_records | - | 20555 |
| ac-compressor | split | option_split | 14363 |
| ac-compressor | conditional | conditional:engine_unattested | 617 |
| ac-compressor | conditional | conditional:notes_not_own_page | 3065 |
| ac-compressor | conditional | conditional:trim | 2947 |
| ac-compressor | conditional | conditional:unknown | 231 |
| alternator | unmapped | - | 2337 |
| alternator | no_records | - | 12915 |
| alternator | split | option_split | 20938 |
| alternator | conditional | conditional:engine | 259 |
| alternator | conditional | conditional:engine_unattested | 2273 |
| alternator | conditional | conditional:notes_not_own_page | 1207 |
| alternator | conditional | conditional:trim | 4186 |
| bumper-front | unmapped | - | 2337 |
| bumper-front | no_records | - | 35045 |
| bumper-front | split | option_split | 6201 |
| bumper-front | conditional | conditional:notes_not_own_page | 62 |
| bumper-front | conditional | conditional:trim | 470 |
| bumper-rear | unmapped | - | 2337 |
| bumper-rear | no_records | - | 33037 |
| bumper-rear | split | option_split | 7648 |
| bumper-rear | conditional | conditional:notes_not_own_page | 664 |
| bumper-rear | conditional | conditional:trim | 429 |
| climate-control | unmapped | - | 2337 |
| climate-control | no_records | - | 29480 |
| climate-control | split | option_split | 8029 |
| climate-control | conditional | conditional:engine_unattested | 1540 |
| climate-control | conditional | conditional:notes_not_own_page | 1147 |
| climate-control | conditional | conditional:trim | 1582 |
| door-front | unmapped | - | 2337 |
| door-front | no_records | - | 33958 |
| door-front | split | option_split | 1859 |
| door-front | conditional | conditional:notes_not_own_page | 877 |
| door-front | conditional | conditional:production | 46 |
| door-front | conditional | conditional:trim | 4690 |
| door-front | eligible | - | 348 |
| door-rear | unmapped | - | 2337 |
| door-rear | no_records | - | 33536 |
| door-rear | split | option_split | 1573 |
| door-rear | conditional | conditional:notes_not_own_page | 1978 |
| door-rear | conditional | conditional:trim | 3631 |
| door-rear | eligible | - | 1060 |
| fender | unmapped | - | 2337 |
| fender | no_records | - | 33896 |
| fender | split | option_split | 2589 |
| fender | conditional | conditional:notes_not_own_page | 1045 |
| fender | conditional | conditional:trim | 3603 |
| fender | chain_member_conditional | chain_member_conditional | 268 |
| fender | eligible | - | 377 |
| fuel-pump-module | unmapped | - | 2337 |
| fuel-pump-module | no_records | - | 21852 |
| fuel-pump-module | split | option_split | 11761 |
| fuel-pump-module | conditional | conditional:engine_unattested | 2711 |
| fuel-pump-module | conditional | conditional:notes_not_own_page | 1356 |
| fuel-pump-module | conditional | conditional:trim | 4098 |
| gauge-cluster | unmapped | - | 2337 |
| gauge-cluster | no_records | - | 39486 |
| gauge-cluster | split | option_split | 1992 |
| gauge-cluster | conditional | conditional:trim | 300 |
| grille | unmapped | - | 2337 |
| grille | no_records | - | 36369 |
| grille | split | option_split | 3860 |
| grille | conditional | conditional:notes_not_own_page | 1058 |
| grille | conditional | conditional:trim | 260 |
| grille | eligible | - | 231 |
| headlights | unmapped | - | 2337 |
| headlights | no_records | - | 27263 |
| headlights | split | option_split | 5233 |
| headlights | split | position_missing | 494 |
| headlights | conditional | conditional:engine_unattested | 4215 |
| headlights | conditional | conditional:notes_not_own_page | 1372 |
| headlights | conditional | conditional:option | 201 |
| headlights | conditional | conditional:trim | 2286 |
| headlights | conditional | conditional:unknown | 268 |
| headlights | chain_member_conditional | chain_member_conditional | 215 |
| headlights | eligible | - | 231 |
| hood | unmapped | - | 2337 |
| hood | no_records | - | 33571 |
| hood | split | option_split | 558 |
| hood | conditional | conditional:notes_not_own_page | 1883 |
| hood | conditional | conditional:trim | 5273 |
| hood | chain_member_conditional | chain_member_conditional | 167 |
| hood | eligible | - | 326 |
| ignition-coils | unmapped | - | 2337 |
| ignition-coils | no_records | - | 5044 |
| ignition-coils | split | option_split | 17620 |
| ignition-coils | conditional | conditional:engine | 993 |
| ignition-coils | conditional | conditional:engine_unattested | 10238 |
| ignition-coils | conditional | conditional:notes_not_own_page | 3296 |
| ignition-coils | conditional | conditional:trim | 4356 |
| ignition-coils | eligible | - | 231 |
| liftgate | unmapped | - | 2337 |
| liftgate | no_records | - | 34921 |
| liftgate | split | option_split | 503 |
| liftgate | conditional | conditional:notes_not_own_page | 2817 |
| liftgate | conditional | conditional:trim | 2924 |
| liftgate | eligible | - | 613 |
| power-steering-pump | unmapped | - | 2337 |
| power-steering-pump | no_records | - | 17990 |
| power-steering-pump | split | option_split | 6624 |
| power-steering-pump | conditional | conditional:engine | 25 |
| power-steering-pump | conditional | conditional:engine_unattested | 7304 |
| power-steering-pump | conditional | conditional:notes_not_own_page | 6897 |
| power-steering-pump | conditional | conditional:option | 121 |
| power-steering-pump | conditional | conditional:qualifier | 472 |
| power-steering-pump | conditional | conditional:trim | 1998 |
| power-steering-pump | conditional | conditional:unknown | 347 |
| radiator | unmapped | - | 2337 |
| radiator | no_records | - | 26622 |
| radiator | split | option_split | 10107 |
| radiator | conditional | conditional:engine | 79 |
| radiator | conditional | conditional:engine_unattested | 416 |
| radiator | conditional | conditional:notes_not_own_page | 1904 |
| radiator | conditional | conditional:trim | 2650 |
| side-mirrors | unmapped | - | 2337 |
| side-mirrors | no_records | - | 26257 |
| side-mirrors | split | option_split | 15011 |
| side-mirrors | split | position_missing | 126 |
| side-mirrors | split | slot_missing | 1 |
| side-mirrors | conditional | conditional:trim | 383 |
| starter | unmapped | - | 2337 |
| starter | no_records | - | 10413 |
| starter | split | option_split | 18303 |
| starter | conditional | conditional:engine | 1227 |
| starter | conditional | conditional:engine_unattested | 6139 |
| starter | conditional | conditional:notes_not_own_page | 4119 |
| starter | conditional | conditional:trim | 1577 |
| tail-lights | unmapped | - | 2337 |
| tail-lights | no_records | - | 30875 |
| tail-lights | split | option_split | 6127 |
| tail-lights | conditional | conditional:engine_unattested | 1226 |
| tail-lights | conditional | conditional:notes_not_own_page | 1460 |
| tail-lights | conditional | conditional:trim | 1759 |
| tail-lights | eligible | - | 331 |
| throttle-body | unmapped | - | 2337 |
| throttle-body | no_records | - | 10812 |
| throttle-body | split | option_split | 20176 |
| throttle-body | conditional | conditional:engine | 331 |
| throttle-body | conditional | conditional:engine_unattested | 3763 |
| throttle-body | conditional | conditional:notes_not_own_page | 3818 |
| throttle-body | conditional | conditional:trim | 2647 |
| throttle-body | chain_member_conditional | chain_member_conditional | 231 |
| window-regulator | unmapped | - | 2337 |
| window-regulator | no_records | - | 23300 |
| window-regulator | split | packaging_unstated | 18478 |
| window-switch | unmapped | - | 2337 |
| window-switch | no_records | - | 21850 |
| window-switch | split | no_candidates | 427 |
| window-switch | split | option_split | 8622 |
| window-switch | split | position_missing | 4972 |
| window-switch | conditional | conditional:engine_unattested | 196 |
| window-switch | conditional | conditional:notes_not_own_page | 932 |
| window-switch | conditional | conditional:option | 121 |
| window-switch | conditional | conditional:position | 215 |
| window-switch | conditional | conditional:trim | 4443 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- disputed_class: 16
- exclude_at_curation: 2
- universal_part_suspect: 11

## Unknown note clauses (top 30)

- `D - DODGE`: 104
- `E - DODGE AWD`: 88
- `Y - CHRYSLER`: 79
- `F - BRAND AWD`: 47
- `C - CHRYSLER`: 46
- `Sales Code [GUK]`: 22
- `All`: 20
- `P - PREMIUM`: 20
- `With Sales Code [GTL]`: 18
- `With Sales Codes [GUL] & [LEP]`: 18
- `Bumper Cover & Components`: 17
- `K - DODGE`: 16
- `Power Fold Away`: 16
- `Power Multi Function`: 16
- `Without Tow Hooks`: 16
- `EGV - 6 Cyl 3.3L OHV`: 14
- `Without Hitch`: 14
- `ERB - 6 Cyl 3.6L VVT`: 13
- `With Hitch`: 13
- `With Tow Hooks`: 13
- `EGL - 6 Cyl 3.8L OHV`: 12
- `Left [GTR`: 12
- `Primed`: 12
- `Right [GTR`: 12
- `All Models`: 11
- `With Park Sensors`: 11
- `Left [GTS`: 10
- `Right [GTS`: 10
- `T - TOURING`: 10
- `With Sales Codes [GTS] and [JSC] and [LEP]`: 10

## Unmapped catalog models

- Chrysler Prowler: feed 'Prowler' 0 cars (excluded: catalog model with no feed cars as 'Prowler' (inventory 2026-11-04); nothing to map)
- Dodge D250: feed 'D250' 10 cars (excluded: M3: the feed spells this truck 'D250', 'D-250' and 'D250 Pickup' (one squash key); not mapped until the feed normalizes them)
- Dodge Omni: feed 'Omni' 1 cars (excluded: catalog model with no feed cars as 'Omni' (inventory 2026-11-04); nothing to map)
- Dodge Ram 4500: feed 'Ram 4500' 0 cars (excluded: catalog model with no feed cars as 'Ram 4500' (inventory 2026-11-04); nothing to map)
- Dodge Ram 5500: feed 'Ram 5500' 0 cars (excluded: catalog model with no feed cars as 'Ram 5500' (inventory 2026-11-04); nothing to map)
- Dodge Viper: feed 'Viper' 0 cars (excluded: catalog model with no feed cars as 'Viper' (inventory 2026-11-04); nothing to map)
- Jeep J20: feed 'J20' 0 cars (excluded: catalog model with no feed cars as 'J20' (inventory 2026-11-04); nothing to map)
