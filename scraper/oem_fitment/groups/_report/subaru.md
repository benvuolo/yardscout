# OEM curation report: subaru

Raw: `1351c33fcfbb` @ `1351c33fcfbb`; as of 2026-11-06T06:33:58Z.

- records 2101, classes 2101, list rows 21183, year manifests 62, cells 2640
- Verified groups 0, engine vg groups 0, Likely groups 42
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.subarupartsdeal.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.subarupartsdeal.com: only 0% of its 4217 fitment rows can be coverage: its option column holds trims (option_column_is_trims), which count only after a namespace audit (spec 5.2)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 253 |
| ac-compressor | no_records | - | 503 |
| ac-compressor | not_closed | no_list_manifest | 1551 |
| ac-compressor | not_closed | no_year_manifest | 3028 |
| ac-compressor | not_closed | unattested | 148 |
| ac-compressor | not_closed | uncrawled_chain_member | 121 |
| ac-compressor | not_closed | year_manifest_bad | 1 |
| alternator | unmapped | - | 253 |
| alternator | no_records | - | 664 |
| alternator | not_closed | no_list_manifest | 1551 |
| alternator | not_closed | no_year_manifest | 2867 |
| alternator | not_closed | unattested | 44 |
| alternator | not_closed | uncrawled_chain_member | 225 |
| alternator | not_closed | year_manifest_bad | 1 |
| bumper-front | unmapped | - | 253 |
| bumper-front | no_records | - | 1008 |
| bumper-front | not_closed | list_manifest_bad | 99 |
| bumper-front | not_closed | no_list_manifest | 67 |
| bumper-front | not_closed | no_year_manifest | 2515 |
| bumper-front | not_closed | unread_sibling_page | 1663 |
| bumper-rear | unmapped | - | 253 |
| bumper-rear | no_records | - | 605 |
| bumper-rear | not_closed | list_manifest_bad | 99 |
| bumper-rear | not_closed | no_list_manifest | 67 |
| bumper-rear | not_closed | no_year_manifest | 2918 |
| bumper-rear | not_closed | unread_sibling_page | 1663 |
| climate-control | unmapped | - | 253 |
| climate-control | no_records | - | 538 |
| climate-control | not_closed | no_list_manifest | 1551 |
| climate-control | not_closed | no_year_manifest | 2993 |
| climate-control | not_closed | unread_sibling_page | 269 |
| climate-control | not_closed | year_manifest_bad | 1 |
| door-front | unmapped | - | 253 |
| door-front | no_records | - | 792 |
| door-front | not_closed | list_manifest_bad | 99 |
| door-front | not_closed | no_list_manifest | 67 |
| door-front | not_closed | no_year_manifest | 2731 |
| door-front | not_closed | unread_sibling_page | 1663 |
| door-rear | unmapped | - | 253 |
| door-rear | no_records | - | 761 |
| door-rear | not_closed | list_manifest_bad | 99 |
| door-rear | not_closed | no_list_manifest | 67 |
| door-rear | not_closed | no_year_manifest | 2762 |
| door-rear | not_closed | unread_sibling_page | 1663 |
| fender | unmapped | - | 253 |
| fender | no_records | - | 915 |
| fender | not_closed | list_manifest_bad | 99 |
| fender | not_closed | no_list_manifest | 67 |
| fender | not_closed | no_year_manifest | 2608 |
| fender | not_closed | unattested | 1301 |
| fender | not_closed | uncrawled_chain_member | 362 |
| fuel-pump-module | unmapped | - | 253 |
| fuel-pump-module | no_records | - | 430 |
| fuel-pump-module | not_closed | no_list_manifest | 1551 |
| fuel-pump-module | not_closed | no_year_manifest | 3101 |
| fuel-pump-module | not_closed | unread_sibling_page | 269 |
| fuel-pump-module | not_closed | year_manifest_bad | 1 |
| gauge-cluster | unmapped | - | 253 |
| gauge-cluster | no_records | - | 3091 |
| gauge-cluster | not_closed | list_manifest_bad | 99 |
| gauge-cluster | not_closed | no_year_manifest | 499 |
| gauge-cluster | not_closed | unread_sibling_page | 1663 |
| grille | unmapped | - | 253 |
| grille | no_records | - | 1608 |
| grille | not_closed | list_manifest_bad | 99 |
| grille | not_closed | no_list_manifest | 67 |
| grille | not_closed | no_year_manifest | 1915 |
| grille | not_closed | unattested | 331 |
| grille | not_closed | uncrawled_chain_member | 221 |
| grille | not_closed | unread_sibling_page | 1111 |
| headlights | unmapped | - | 253 |
| headlights | no_records | - | 1190 |
| headlights | not_closed | no_list_manifest | 1551 |
| headlights | not_closed | no_year_manifest | 2341 |
| headlights | not_closed | unattested | 225 |
| headlights | not_closed | uncrawled_chain_member | 44 |
| headlights | not_closed | year_manifest_bad | 1 |
| hood | unmapped | - | 253 |
| hood | no_records | - | 449 |
| hood | not_closed | list_manifest_bad | 99 |
| hood | not_closed | no_list_manifest | 67 |
| hood | not_closed | no_year_manifest | 3074 |
| hood | not_closed | unread_sibling_page | 1661 |
| hood | not_closed | unverified_product | 2 |
| ignition-coils | unmapped | - | 253 |
| ignition-coils | no_records | - | 240 |
| ignition-coils | not_closed | list_manifest_bad | 99 |
| ignition-coils | not_closed | no_list_manifest | 67 |
| ignition-coils | not_closed | no_year_manifest | 3283 |
| ignition-coils | not_closed | unattested | 10 |
| ignition-coils | not_closed | uncrawled_chain_member | 1651 |
| ignition-coils | not_closed | unverified_product | 2 |
| liftgate | unmapped | - | 253 |
| liftgate | no_records | - | 713 |
| liftgate | not_closed | list_manifest_bad | 99 |
| liftgate | not_closed | no_list_manifest | 67 |
| liftgate | not_closed | no_year_manifest | 2810 |
| liftgate | not_closed | unattested | 1438 |
| liftgate | not_closed | uncrawled_chain_member | 223 |
| liftgate | not_closed | unverified_product | 2 |
| power-steering-pump | unmapped | - | 253 |
| power-steering-pump | no_records | - | 1203 |
| power-steering-pump | not_closed | no_list_manifest | 1321 |
| power-steering-pump | not_closed | no_year_manifest | 2635 |
| power-steering-pump | not_closed | unread_sibling_page | 193 |
| radiator | unmapped | - | 253 |
| radiator | no_records | - | 280 |
| radiator | not_closed | list_manifest_bad | 99 |
| radiator | not_closed | no_list_manifest | 67 |
| radiator | not_closed | no_year_manifest | 3243 |
| radiator | not_closed | unattested | 1130 |
| radiator | not_closed | uncrawled_chain_member | 410 |
| radiator | not_closed | unread_sibling_page | 123 |
| side-mirrors | unmapped | - | 253 |
| side-mirrors | no_records | - | 743 |
| side-mirrors | not_closed | no_list_manifest | 1551 |
| side-mirrors | not_closed | no_year_manifest | 2788 |
| side-mirrors | not_closed | unattested | 41 |
| side-mirrors | not_closed | uncrawled_chain_member | 228 |
| side-mirrors | not_closed | year_manifest_bad | 1 |
| starter | unmapped | - | 253 |
| starter | no_records | - | 65 |
| starter | not_closed | no_list_manifest | 1560 |
| starter | not_closed | no_year_manifest | 3457 |
| starter | not_closed | unattested | 101 |
| starter | not_closed | uncrawled_chain_member | 168 |
| starter | not_closed | year_manifest_bad | 1 |
| tail-lights | unmapped | - | 253 |
| tail-lights | no_records | - | 610 |
| tail-lights | not_closed | no_list_manifest | 1560 |
| tail-lights | not_closed | no_year_manifest | 2912 |
| tail-lights | not_closed | unattested | 176 |
| tail-lights | not_closed | uncrawled_chain_member | 93 |
| tail-lights | not_closed | year_manifest_bad | 1 |
| throttle-body | unmapped | - | 253 |
| throttle-body | no_records | - | 97 |
| throttle-body | not_closed | no_list_manifest | 1560 |
| throttle-body | not_closed | no_year_manifest | 3425 |
| throttle-body | not_closed | unattested | 127 |
| throttle-body | not_closed | uncrawled_chain_member | 142 |
| throttle-body | not_closed | year_manifest_bad | 1 |
| trunk-lid | unmapped | - | 253 |
| trunk-lid | no_records | - | 1687 |
| trunk-lid | not_closed | list_manifest_bad | 99 |
| trunk-lid | not_closed | no_list_manifest | 67 |
| trunk-lid | not_closed | no_year_manifest | 1959 |
| trunk-lid | not_closed | unread_sibling_page | 1540 |
| window-regulator | unmapped | - | 253 |
| window-regulator | no_records | - | 106 |
| window-regulator | not_closed | no_list_manifest | 1560 |
| window-regulator | not_closed | no_year_manifest | 3416 |
| window-regulator | not_closed | unread_sibling_page | 269 |
| window-regulator | not_closed | year_manifest_bad | 1 |
| window-switch | unmapped | - | 253 |
| window-switch | no_records | - | 883 |
| window-switch | not_closed | no_list_manifest | 1551 |
| window-switch | not_closed | no_year_manifest | 2648 |
| window-switch | not_closed | unread_sibling_page | 269 |
| window-switch | not_closed | year_manifest_bad | 1 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 253 |
| ac-compressor | no_records | - | 503 |
| ac-compressor | split | option_split | 2636 |
| ac-compressor | conditional | conditional:engine_unattested | 2213 |
| alternator | unmapped | - | 253 |
| alternator | no_records | - | 664 |
| alternator | split | no_candidates | 17 |
| alternator | split | option_split | 2577 |
| alternator | conditional | conditional:engine_unattested | 2094 |
| bumper-front | unmapped | - | 253 |
| bumper-front | no_records | - | 1008 |
| bumper-front | split | option_split | 3382 |
| bumper-front | conditional | conditional:engine_unattested | 952 |
| bumper-front | conditional | conditional:option | 10 |
| bumper-rear | unmapped | - | 253 |
| bumper-rear | no_records | - | 605 |
| bumper-rear | split | option_split | 3820 |
| bumper-rear | conditional | conditional:engine_unattested | 917 |
| bumper-rear | conditional | conditional:option | 10 |
| climate-control | unmapped | - | 253 |
| climate-control | no_records | - | 538 |
| climate-control | split | no_candidates | 41 |
| climate-control | split | option_split | 3456 |
| climate-control | conditional | conditional:engine_unattested | 1317 |
| door-front | unmapped | - | 253 |
| door-front | no_records | - | 792 |
| door-front | split | option_split | 3104 |
| door-front | conditional | conditional:engine_unattested | 1456 |
| door-rear | unmapped | - | 253 |
| door-rear | no_records | - | 761 |
| door-rear | split | option_split | 2978 |
| door-rear | conditional | conditional:engine_unattested | 1613 |
| fender | unmapped | - | 253 |
| fender | no_records | - | 915 |
| fender | split | option_split | 2528 |
| fender | split | slot_missing | 168 |
| fender | conditional | conditional:engine_unattested | 1741 |
| fuel-pump-module | unmapped | - | 253 |
| fuel-pump-module | no_records | - | 430 |
| fuel-pump-module | split | no_candidates | 1 |
| fuel-pump-module | split | option_split | 3647 |
| fuel-pump-module | conditional | conditional:engine_unattested | 1274 |
| gauge-cluster | unmapped | - | 253 |
| gauge-cluster | no_records | - | 3091 |
| gauge-cluster | split | no_candidates | 177 |
| gauge-cluster | split | option_split | 2084 |
| grille | unmapped | - | 253 |
| grille | no_records | - | 1608 |
| grille | split | no_candidates | 147 |
| grille | split | option_split | 3048 |
| grille | conditional | conditional:engine_unattested | 549 |
| headlights | unmapped | - | 253 |
| headlights | no_records | - | 1190 |
| headlights | split | no_candidates | 1 |
| headlights | split | option_split | 3136 |
| headlights | conditional | conditional:engine_unattested | 1025 |
| hood | unmapped | - | 253 |
| hood | no_records | - | 449 |
| hood | split | option_split | 2875 |
| hood | conditional | conditional:engine_unattested | 2028 |
| ignition-coils | unmapped | - | 253 |
| ignition-coils | no_records | - | 240 |
| ignition-coils | split | option_split | 3537 |
| ignition-coils | conditional | conditional:engine_unattested | 1359 |
| ignition-coils | conditional | conditional:package | 216 |
| liftgate | unmapped | - | 253 |
| liftgate | no_records | - | 713 |
| liftgate | split | option_split | 2296 |
| liftgate | conditional | conditional:engine_unattested | 2343 |
| power-steering-pump | unmapped | - | 253 |
| power-steering-pump | no_records | - | 1203 |
| power-steering-pump | split | option_split | 3422 |
| power-steering-pump | conditional | conditional:engine_unattested | 677 |
| power-steering-pump | conditional | conditional:option | 50 |
| radiator | unmapped | - | 253 |
| radiator | no_records | - | 280 |
| radiator | split | option_split | 4501 |
| radiator | conditional | conditional:engine_unattested | 571 |
| side-mirrors | unmapped | - | 253 |
| side-mirrors | no_records | - | 743 |
| side-mirrors | split | option_split | 4346 |
| side-mirrors | split | slot_missing | 4 |
| side-mirrors | conditional | conditional:engine_unattested | 259 |
| starter | unmapped | - | 253 |
| starter | no_records | - | 65 |
| starter | split | option_split | 5172 |
| starter | conditional | conditional:engine_unattested | 115 |
| tail-lights | unmapped | - | 253 |
| tail-lights | no_records | - | 610 |
| tail-lights | split | no_candidates | 1 |
| tail-lights | split | option_split | 3770 |
| tail-lights | conditional | conditional:engine_unattested | 971 |
| throttle-body | unmapped | - | 253 |
| throttle-body | no_records | - | 97 |
| throttle-body | split | no_candidates | 1 |
| throttle-body | split | option_split | 4455 |
| throttle-body | conditional | conditional:engine_unattested | 799 |
| trunk-lid | unmapped | - | 253 |
| trunk-lid | no_records | - | 1687 |
| trunk-lid | split | no_candidates | 413 |
| trunk-lid | split | option_split | 1487 |
| trunk-lid | conditional | conditional:engine_unattested | 1765 |
| window-regulator | unmapped | - | 253 |
| window-regulator | no_records | - | 106 |
| window-regulator | split | no_candidates | 1 |
| window-regulator | split | packaging_unstated | 5245 |
| window-switch | unmapped | - | 253 |
| window-switch | no_records | - | 883 |
| window-switch | split | no_candidates | 185 |
| window-switch | split | option_split | 2136 |
| window-switch | split | position_missing | 2148 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 226
- held_exterior_cross_model: 18
- held_option_cross_model: 27
- recrawl_resolved: 1

## Unknown note clauses (top 30)

- `Production Date: 199105 - 199204`: 86
- `NO PAINTED`: 80
- `Production Date: 200201 - 200306`: 68
- `Production Date: 200311 - 200505`: 66
- `Production Date: 200301 - 200402`: 60
- `PAINT FOR USAGE`: 59
- `Package Quantity: 1`: 59
- `Production Date: 199912 - 200105`: 54
- `Production Date: 200102 - 200204`: 42
- `S.GTLTD.AT`: 40
- `Production Date: 200204 - 200205`: 38
- `Production Date: 200610 - 200804`: 38
- `Require Quantity: 04`: 37
- `Production Date: 199710 - 199905`: 32
- `Production Date: 199909 - 200102`: 28
- `PAINTED FOR USAGE`: 26
- `WOBK.(25GT+25GLI)`: 26
- `Production Date: 201210 - 201401`: 22
- `Require Quantity: 06`: 21
- `S.36R`: 21
- `S.25GLI +W.25GLI`: 20
- `S.GTLTD.MT`: 20
- `C0`: 19
- `Production Date: 201006 - 201108`: 16
- `Production Date: 201402 - 201507`: 16
- `S.25GLI +W.25GLI +WOBK.(25GT+25GLI)`: 16
- `S.25I +W.4AT`: 16
- `S.25I.4AT +W.25I.4AT +WOBK.25I.4AT`: 16
- `*S.25GTL`: 14
- `CO`: 14

## Unmapped catalog models

- Subaru Impreza STI: feed 'Impreza STI' 0 cars
- Subaru WRX STI: feed 'WRX STI' 0 cars
