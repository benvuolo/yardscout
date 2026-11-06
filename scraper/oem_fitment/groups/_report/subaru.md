# OEM curation report: subaru

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-06T06:33:58Z.

- records 2101, classes 2101, list rows 21183, year manifests 62, cells 2640
- Verified groups 0, engine vg groups 0, Likely groups 223
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.subarupartsdeal.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.subarupartsdeal.com: only 0% of its 4217 fitment rows can be coverage: its option column holds trims (option_column_is_trims), which count only after a namespace audit (spec 5.2)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 263 |
| ac-compressor | no_records | - | 500 |
| ac-compressor | not_closed | no_list_manifest | 1553 |
| ac-compressor | not_closed | no_year_manifest | 2990 |
| ac-compressor | not_closed | unattested | 149 |
| ac-compressor | not_closed | uncrawled_chain_member | 125 |
| ac-compressor | not_closed | year_manifest_bad | 1 |
| alternator | unmapped | - | 263 |
| alternator | no_records | - | 649 |
| alternator | not_closed | no_list_manifest | 1553 |
| alternator | not_closed | no_year_manifest | 2841 |
| alternator | not_closed | unattested | 44 |
| alternator | not_closed | uncrawled_chain_member | 230 |
| alternator | not_closed | year_manifest_bad | 1 |
| bumper-front | unmapped | - | 263 |
| bumper-front | no_records | - | 987 |
| bumper-front | not_closed | list_manifest_bad | 94 |
| bumper-front | not_closed | no_list_manifest | 67 |
| bumper-front | not_closed | no_year_manifest | 2496 |
| bumper-front | not_closed | unread_sibling_page | 1674 |
| bumper-rear | unmapped | - | 263 |
| bumper-rear | no_records | - | 595 |
| bumper-rear | not_closed | list_manifest_bad | 94 |
| bumper-rear | not_closed | no_list_manifest | 67 |
| bumper-rear | not_closed | no_year_manifest | 2888 |
| bumper-rear | not_closed | unread_sibling_page | 1674 |
| climate-control | unmapped | - | 263 |
| climate-control | no_records | - | 523 |
| climate-control | not_closed | no_list_manifest | 1553 |
| climate-control | not_closed | no_year_manifest | 2967 |
| climate-control | not_closed | unread_sibling_page | 274 |
| climate-control | not_closed | year_manifest_bad | 1 |
| door-front | unmapped | - | 263 |
| door-front | no_records | - | 786 |
| door-front | not_closed | list_manifest_bad | 94 |
| door-front | not_closed | no_list_manifest | 67 |
| door-front | not_closed | no_year_manifest | 2697 |
| door-front | not_closed | unread_sibling_page | 1674 |
| door-rear | unmapped | - | 263 |
| door-rear | no_records | - | 750 |
| door-rear | not_closed | list_manifest_bad | 94 |
| door-rear | not_closed | no_list_manifest | 67 |
| door-rear | not_closed | no_year_manifest | 2733 |
| door-rear | not_closed | unread_sibling_page | 1674 |
| fender | unmapped | - | 263 |
| fender | no_records | - | 909 |
| fender | not_closed | list_manifest_bad | 94 |
| fender | not_closed | no_list_manifest | 67 |
| fender | not_closed | no_year_manifest | 2574 |
| fender | not_closed | unattested | 1309 |
| fender | not_closed | uncrawled_chain_member | 365 |
| fuel-pump-module | unmapped | - | 263 |
| fuel-pump-module | no_records | - | 418 |
| fuel-pump-module | not_closed | no_list_manifest | 1553 |
| fuel-pump-module | not_closed | no_year_manifest | 3072 |
| fuel-pump-module | not_closed | unread_sibling_page | 274 |
| fuel-pump-module | not_closed | year_manifest_bad | 1 |
| gauge-cluster | unmapped | - | 263 |
| gauge-cluster | no_records | - | 3055 |
| gauge-cluster | not_closed | list_manifest_bad | 94 |
| gauge-cluster | not_closed | no_year_manifest | 495 |
| gauge-cluster | not_closed | unread_sibling_page | 1674 |
| grille | unmapped | - | 263 |
| grille | no_records | - | 1579 |
| grille | not_closed | list_manifest_bad | 94 |
| grille | not_closed | no_list_manifest | 67 |
| grille | not_closed | no_year_manifest | 1904 |
| grille | not_closed | unattested | 336 |
| grille | not_closed | uncrawled_chain_member | 221 |
| grille | not_closed | unread_sibling_page | 1117 |
| headlights | unmapped | - | 263 |
| headlights | no_records | - | 1176 |
| headlights | not_closed | no_list_manifest | 1553 |
| headlights | not_closed | no_year_manifest | 2314 |
| headlights | not_closed | unattested | 230 |
| headlights | not_closed | uncrawled_chain_member | 44 |
| headlights | not_closed | year_manifest_bad | 1 |
| hood | unmapped | - | 263 |
| hood | no_records | - | 447 |
| hood | not_closed | list_manifest_bad | 94 |
| hood | not_closed | no_list_manifest | 67 |
| hood | not_closed | no_year_manifest | 3036 |
| hood | not_closed | unread_sibling_page | 1672 |
| hood | not_closed | unverified_product | 2 |
| ignition-coils | unmapped | - | 263 |
| ignition-coils | no_records | - | 232 |
| ignition-coils | not_closed | list_manifest_bad | 94 |
| ignition-coils | not_closed | no_list_manifest | 67 |
| ignition-coils | not_closed | no_year_manifest | 3251 |
| ignition-coils | not_closed | unattested | 12 |
| ignition-coils | not_closed | uncrawled_chain_member | 1660 |
| ignition-coils | not_closed | unverified_product | 2 |
| liftgate | unmapped | - | 263 |
| liftgate | no_records | - | 705 |
| liftgate | not_closed | list_manifest_bad | 94 |
| liftgate | not_closed | no_list_manifest | 67 |
| liftgate | not_closed | no_year_manifest | 2778 |
| liftgate | not_closed | unattested | 1445 |
| liftgate | not_closed | uncrawled_chain_member | 227 |
| liftgate | not_closed | unverified_product | 2 |
| power-steering-pump | unmapped | - | 263 |
| power-steering-pump | no_records | - | 1175 |
| power-steering-pump | not_closed | no_list_manifest | 1330 |
| power-steering-pump | not_closed | no_year_manifest | 2614 |
| power-steering-pump | not_closed | unread_sibling_page | 199 |
| radiator | unmapped | - | 263 |
| radiator | no_records | - | 279 |
| radiator | not_closed | list_manifest_bad | 94 |
| radiator | not_closed | no_list_manifest | 67 |
| radiator | not_closed | no_year_manifest | 3204 |
| radiator | not_closed | unattested | 1133 |
| radiator | not_closed | uncrawled_chain_member | 412 |
| radiator | not_closed | unread_sibling_page | 129 |
| side-mirrors | unmapped | - | 263 |
| side-mirrors | no_records | - | 733 |
| side-mirrors | not_closed | no_list_manifest | 1553 |
| side-mirrors | not_closed | no_year_manifest | 2757 |
| side-mirrors | not_closed | unattested | 43 |
| side-mirrors | not_closed | uncrawled_chain_member | 231 |
| side-mirrors | not_closed | year_manifest_bad | 1 |
| starter | unmapped | - | 263 |
| starter | no_records | - | 66 |
| starter | not_closed | no_list_manifest | 1561 |
| starter | not_closed | no_year_manifest | 3416 |
| starter | not_closed | unattested | 101 |
| starter | not_closed | uncrawled_chain_member | 173 |
| starter | not_closed | year_manifest_bad | 1 |
| tail-lights | unmapped | - | 263 |
| tail-lights | no_records | - | 603 |
| tail-lights | not_closed | no_list_manifest | 1561 |
| tail-lights | not_closed | no_year_manifest | 2879 |
| tail-lights | not_closed | unattested | 180 |
| tail-lights | not_closed | uncrawled_chain_member | 94 |
| tail-lights | not_closed | year_manifest_bad | 1 |
| throttle-body | unmapped | - | 263 |
| throttle-body | no_records | - | 97 |
| throttle-body | not_closed | no_list_manifest | 1561 |
| throttle-body | not_closed | no_year_manifest | 3385 |
| throttle-body | not_closed | unattested | 130 |
| throttle-body | not_closed | uncrawled_chain_member | 144 |
| throttle-body | not_closed | year_manifest_bad | 1 |
| trunk-lid | unmapped | - | 263 |
| trunk-lid | no_records | - | 1671 |
| trunk-lid | not_closed | list_manifest_bad | 94 |
| trunk-lid | not_closed | no_list_manifest | 67 |
| trunk-lid | not_closed | no_year_manifest | 1941 |
| trunk-lid | not_closed | unread_sibling_page | 1545 |
| window-regulator | unmapped | - | 263 |
| window-regulator | no_records | - | 107 |
| window-regulator | not_closed | no_list_manifest | 1561 |
| window-regulator | not_closed | no_year_manifest | 3375 |
| window-regulator | not_closed | unread_sibling_page | 274 |
| window-regulator | not_closed | year_manifest_bad | 1 |
| window-switch | unmapped | - | 263 |
| window-switch | no_records | - | 869 |
| window-switch | not_closed | no_list_manifest | 1553 |
| window-switch | not_closed | no_year_manifest | 2621 |
| window-switch | not_closed | unread_sibling_page | 274 |
| window-switch | not_closed | year_manifest_bad | 1 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 263 |
| ac-compressor | no_records | - | 500 |
| ac-compressor | split | option_split | 2635 |
| ac-compressor | conditional | conditional:engine_unattested | 2183 |
| alternator | unmapped | - | 263 |
| alternator | no_records | - | 649 |
| alternator | split | no_candidates | 18 |
| alternator | split | option_split | 2571 |
| alternator | conditional | conditional:engine_unattested | 2080 |
| bumper-front | unmapped | - | 263 |
| bumper-front | no_records | - | 987 |
| bumper-front | split | option_split | 3374 |
| bumper-front | conditional | conditional:engine_unattested | 945 |
| bumper-front | conditional | conditional:option | 12 |
| bumper-rear | unmapped | - | 263 |
| bumper-rear | no_records | - | 595 |
| bumper-rear | split | option_split | 3807 |
| bumper-rear | conditional | conditional:engine_unattested | 904 |
| bumper-rear | conditional | conditional:option | 12 |
| climate-control | unmapped | - | 263 |
| climate-control | no_records | - | 523 |
| climate-control | split | no_candidates | 43 |
| climate-control | split | option_split | 3440 |
| climate-control | conditional | conditional:engine_unattested | 1312 |
| door-front | unmapped | - | 263 |
| door-front | no_records | - | 786 |
| door-front | split | option_split | 3090 |
| door-front | conditional | conditional:engine_unattested | 1442 |
| door-rear | unmapped | - | 263 |
| door-rear | no_records | - | 750 |
| door-rear | split | option_split | 2973 |
| door-rear | conditional | conditional:engine_unattested | 1595 |
| fender | unmapped | - | 263 |
| fender | no_records | - | 909 |
| fender | split | option_split | 2523 |
| fender | split | slot_missing | 159 |
| fender | conditional | conditional:engine_unattested | 1727 |
| fuel-pump-module | unmapped | - | 263 |
| fuel-pump-module | no_records | - | 418 |
| fuel-pump-module | split | no_candidates | 1 |
| fuel-pump-module | split | option_split | 3633 |
| fuel-pump-module | conditional | conditional:engine_unattested | 1266 |
| gauge-cluster | unmapped | - | 263 |
| gauge-cluster | no_records | - | 3055 |
| gauge-cluster | split | no_candidates | 182 |
| gauge-cluster | split | option_split | 2081 |
| grille | unmapped | - | 263 |
| grille | no_records | - | 1579 |
| grille | split | no_candidates | 142 |
| grille | split | option_split | 3045 |
| grille | conditional | conditional:engine_unattested | 552 |
| headlights | unmapped | - | 263 |
| headlights | no_records | - | 1176 |
| headlights | split | no_candidates | 1 |
| headlights | split | option_split | 3104 |
| headlights | conditional | conditional:engine_unattested | 1037 |
| hood | unmapped | - | 263 |
| hood | no_records | - | 447 |
| hood | split | option_split | 2867 |
| hood | conditional | conditional:engine_unattested | 2004 |
| ignition-coils | unmapped | - | 263 |
| ignition-coils | no_records | - | 232 |
| ignition-coils | split | option_split | 3518 |
| ignition-coils | conditional | conditional:engine_unattested | 1356 |
| ignition-coils | conditional | conditional:package | 212 |
| liftgate | unmapped | - | 263 |
| liftgate | no_records | - | 705 |
| liftgate | split | option_split | 2277 |
| liftgate | conditional | conditional:engine_unattested | 2336 |
| power-steering-pump | unmapped | - | 263 |
| power-steering-pump | no_records | - | 1175 |
| power-steering-pump | split | option_split | 3414 |
| power-steering-pump | conditional | conditional:engine_unattested | 678 |
| power-steering-pump | conditional | conditional:option | 51 |
| radiator | unmapped | - | 263 |
| radiator | no_records | - | 279 |
| radiator | split | option_split | 4488 |
| radiator | conditional | conditional:engine_unattested | 551 |
| side-mirrors | unmapped | - | 263 |
| side-mirrors | no_records | - | 733 |
| side-mirrors | split | option_split | 4325 |
| side-mirrors | split | slot_missing | 3 |
| side-mirrors | conditional | conditional:engine_unattested | 257 |
| starter | unmapped | - | 263 |
| starter | no_records | - | 66 |
| starter | split | option_split | 5138 |
| starter | conditional | conditional:engine_unattested | 114 |
| tail-lights | unmapped | - | 263 |
| tail-lights | no_records | - | 603 |
| tail-lights | split | no_candidates | 1 |
| tail-lights | split | option_split | 3758 |
| tail-lights | conditional | conditional:engine_unattested | 956 |
| throttle-body | unmapped | - | 263 |
| throttle-body | no_records | - | 97 |
| throttle-body | split | no_candidates | 1 |
| throttle-body | split | option_split | 4442 |
| throttle-body | conditional | conditional:engine_unattested | 778 |
| trunk-lid | unmapped | - | 263 |
| trunk-lid | no_records | - | 1671 |
| trunk-lid | split | no_candidates | 413 |
| trunk-lid | split | option_split | 1477 |
| trunk-lid | conditional | conditional:engine_unattested | 1757 |
| window-regulator | unmapped | - | 263 |
| window-regulator | no_records | - | 107 |
| window-regulator | split | no_candidates | 1 |
| window-regulator | split | packaging_unstated | 5210 |
| window-switch | unmapped | - | 263 |
| window-switch | no_records | - | 869 |
| window-switch | split | no_candidates | 187 |
| window-switch | split | option_split | 2134 |
| window-switch | split | position_missing | 2128 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 226
- held_exterior_cross_model: 156
- recrawl_resolved: 1

## Unknown note clauses (top 30)

- `Production Date: 200201 - 200306`: 122
- `NO PAINTED`: 90
- `Production Date: 199105 - 199204`: 86
- `Production Date: 200311 - 200505`: 76
- `Production Date: 199912 - 200105`: 74
- `Production Date: 200301 - 200402`: 66
- `PAINT FOR USAGE`: 59
- `Package Quantity: 1`: 59
- `Production Date: 200102 - 200204`: 42
- `S.GTLTD.AT`: 40
- `Production Date: 200204 - 200205`: 38
- `Production Date: 200610 - 200804`: 38
- `Require Quantity: 04`: 37
- `Production Date: 199710 - 199905`: 32
- `Production Date: 199909 - 200102`: 28
- `Production Date: 200606 - 200706`: 28
- `PAINTED FOR USAGE`: 26
- `W/O SD TURN-LAMP`: 26
- `WOBK.(25GT+25GLI)`: 26
- `Production Date: 201210 - 201401`: 22
- `S.25GLI +W.25GLI`: 22
- `Require Quantity: 06`: 21
- `S.36R`: 21
- `S.GTLTD.MT`: 20
- `C0`: 19
- `Notes: C0`: 16
- `Production Date: 201006 - 201108`: 16
- `Production Date: 201402 - 201507`: 16
- `S.25GLI +W.25GLI +WOBK.(25GT+25GLI)`: 16
- `S.25I +W.4AT`: 16

## Unmapped catalog models

- Subaru Impreza STI: feed 'Impreza STI' 0 cars
- Subaru WRX STI: feed 'WRX STI' 0 cars
