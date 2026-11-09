# OEM curation report: subaru

Raw: `75dc442f0f21bff4725fe1bee2ba6f323d249079` @ `75dc442f0f21`; as of 2026-11-06T06:33:58Z.

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
| ac-compressor | unmapped | - | 255 |
| ac-compressor | no_records | - | 506 |
| ac-compressor | not_closed | no_list_manifest | 1554 |
| ac-compressor | not_closed | no_year_manifest | 3033 |
| ac-compressor | not_closed | unattested | 149 |
| ac-compressor | not_closed | uncrawled_chain_member | 122 |
| ac-compressor | not_closed | year_manifest_bad | 1 |
| alternator | unmapped | - | 255 |
| alternator | no_records | - | 665 |
| alternator | not_closed | no_list_manifest | 1554 |
| alternator | not_closed | no_year_manifest | 2874 |
| alternator | not_closed | unattested | 44 |
| alternator | not_closed | uncrawled_chain_member | 227 |
| alternator | not_closed | year_manifest_bad | 1 |
| bumper-front | unmapped | - | 255 |
| bumper-front | no_records | - | 1008 |
| bumper-front | not_closed | list_manifest_bad | 98 |
| bumper-front | not_closed | no_list_manifest | 67 |
| bumper-front | not_closed | no_year_manifest | 2523 |
| bumper-front | not_closed | unread_sibling_page | 1669 |
| bumper-rear | unmapped | - | 255 |
| bumper-rear | no_records | - | 602 |
| bumper-rear | not_closed | list_manifest_bad | 98 |
| bumper-rear | not_closed | no_list_manifest | 67 |
| bumper-rear | not_closed | no_year_manifest | 2929 |
| bumper-rear | not_closed | unread_sibling_page | 1669 |
| climate-control | unmapped | - | 255 |
| climate-control | no_records | - | 539 |
| climate-control | not_closed | no_list_manifest | 1554 |
| climate-control | not_closed | no_year_manifest | 3000 |
| climate-control | not_closed | unread_sibling_page | 271 |
| climate-control | not_closed | year_manifest_bad | 1 |
| door-front | unmapped | - | 255 |
| door-front | no_records | - | 798 |
| door-front | not_closed | list_manifest_bad | 98 |
| door-front | not_closed | no_list_manifest | 67 |
| door-front | not_closed | no_year_manifest | 2733 |
| door-front | not_closed | unread_sibling_page | 1669 |
| door-rear | unmapped | - | 255 |
| door-rear | no_records | - | 767 |
| door-rear | not_closed | list_manifest_bad | 98 |
| door-rear | not_closed | no_list_manifest | 67 |
| door-rear | not_closed | no_year_manifest | 2764 |
| door-rear | not_closed | unread_sibling_page | 1669 |
| fender | unmapped | - | 255 |
| fender | no_records | - | 918 |
| fender | not_closed | list_manifest_bad | 98 |
| fender | not_closed | no_list_manifest | 67 |
| fender | not_closed | no_year_manifest | 2613 |
| fender | not_closed | unattested | 1307 |
| fender | not_closed | uncrawled_chain_member | 362 |
| fuel-pump-module | unmapped | - | 255 |
| fuel-pump-module | no_records | - | 430 |
| fuel-pump-module | not_closed | no_list_manifest | 1554 |
| fuel-pump-module | not_closed | no_year_manifest | 3109 |
| fuel-pump-module | not_closed | unread_sibling_page | 271 |
| fuel-pump-module | not_closed | year_manifest_bad | 1 |
| gauge-cluster | unmapped | - | 255 |
| gauge-cluster | no_records | - | 3098 |
| gauge-cluster | not_closed | list_manifest_bad | 98 |
| gauge-cluster | not_closed | no_year_manifest | 500 |
| gauge-cluster | not_closed | unread_sibling_page | 1669 |
| grille | unmapped | - | 255 |
| grille | no_records | - | 1609 |
| grille | not_closed | list_manifest_bad | 98 |
| grille | not_closed | no_list_manifest | 67 |
| grille | not_closed | no_year_manifest | 1922 |
| grille | not_closed | unattested | 333 |
| grille | not_closed | uncrawled_chain_member | 223 |
| grille | not_closed | unread_sibling_page | 1113 |
| headlights | unmapped | - | 255 |
| headlights | no_records | - | 1186 |
| headlights | not_closed | no_list_manifest | 1554 |
| headlights | not_closed | no_year_manifest | 2353 |
| headlights | not_closed | unattested | 227 |
| headlights | not_closed | uncrawled_chain_member | 44 |
| headlights | not_closed | year_manifest_bad | 1 |
| hood | unmapped | - | 255 |
| hood | no_records | - | 448 |
| hood | not_closed | list_manifest_bad | 98 |
| hood | not_closed | no_list_manifest | 67 |
| hood | not_closed | no_year_manifest | 3083 |
| hood | not_closed | unread_sibling_page | 1667 |
| hood | not_closed | unverified_product | 2 |
| ignition-coils | unmapped | - | 255 |
| ignition-coils | no_records | - | 237 |
| ignition-coils | not_closed | list_manifest_bad | 98 |
| ignition-coils | not_closed | no_list_manifest | 67 |
| ignition-coils | not_closed | no_year_manifest | 3294 |
| ignition-coils | not_closed | unattested | 11 |
| ignition-coils | not_closed | uncrawled_chain_member | 1656 |
| ignition-coils | not_closed | unverified_product | 2 |
| liftgate | unmapped | - | 255 |
| liftgate | no_records | - | 715 |
| liftgate | not_closed | list_manifest_bad | 98 |
| liftgate | not_closed | no_list_manifest | 67 |
| liftgate | not_closed | no_year_manifest | 2816 |
| liftgate | not_closed | unattested | 1443 |
| liftgate | not_closed | uncrawled_chain_member | 224 |
| liftgate | not_closed | unverified_product | 2 |
| power-steering-pump | unmapped | - | 255 |
| power-steering-pump | no_records | - | 1201 |
| power-steering-pump | not_closed | no_list_manifest | 1323 |
| power-steering-pump | not_closed | no_year_manifest | 2646 |
| power-steering-pump | not_closed | unread_sibling_page | 195 |
| radiator | unmapped | - | 255 |
| radiator | no_records | - | 281 |
| radiator | not_closed | list_manifest_bad | 98 |
| radiator | not_closed | no_list_manifest | 67 |
| radiator | not_closed | no_year_manifest | 3250 |
| radiator | not_closed | unattested | 1133 |
| radiator | not_closed | uncrawled_chain_member | 411 |
| radiator | not_closed | unread_sibling_page | 125 |
| side-mirrors | unmapped | - | 255 |
| side-mirrors | no_records | - | 745 |
| side-mirrors | not_closed | no_list_manifest | 1554 |
| side-mirrors | not_closed | no_year_manifest | 2794 |
| side-mirrors | not_closed | unattested | 41 |
| side-mirrors | not_closed | uncrawled_chain_member | 230 |
| side-mirrors | not_closed | year_manifest_bad | 1 |
| starter | unmapped | - | 255 |
| starter | no_records | - | 65 |
| starter | not_closed | no_list_manifest | 1563 |
| starter | not_closed | no_year_manifest | 3465 |
| starter | not_closed | unattested | 101 |
| starter | not_closed | uncrawled_chain_member | 170 |
| starter | not_closed | year_manifest_bad | 1 |
| tail-lights | unmapped | - | 255 |
| tail-lights | no_records | - | 609 |
| tail-lights | not_closed | no_list_manifest | 1563 |
| tail-lights | not_closed | no_year_manifest | 2921 |
| tail-lights | not_closed | unattested | 178 |
| tail-lights | not_closed | uncrawled_chain_member | 93 |
| tail-lights | not_closed | year_manifest_bad | 1 |
| throttle-body | unmapped | - | 255 |
| throttle-body | no_records | - | 96 |
| throttle-body | not_closed | no_list_manifest | 1563 |
| throttle-body | not_closed | no_year_manifest | 3434 |
| throttle-body | not_closed | unattested | 128 |
| throttle-body | not_closed | uncrawled_chain_member | 143 |
| throttle-body | not_closed | year_manifest_bad | 1 |
| trunk-lid | unmapped | - | 255 |
| trunk-lid | no_records | - | 1691 |
| trunk-lid | not_closed | list_manifest_bad | 98 |
| trunk-lid | not_closed | no_list_manifest | 67 |
| trunk-lid | not_closed | no_year_manifest | 1965 |
| trunk-lid | not_closed | unread_sibling_page | 1544 |
| window-regulator | unmapped | - | 255 |
| window-regulator | no_records | - | 106 |
| window-regulator | not_closed | no_list_manifest | 1563 |
| window-regulator | not_closed | no_year_manifest | 3424 |
| window-regulator | not_closed | unread_sibling_page | 271 |
| window-regulator | not_closed | year_manifest_bad | 1 |
| window-switch | unmapped | - | 255 |
| window-switch | no_records | - | 883 |
| window-switch | not_closed | no_list_manifest | 1554 |
| window-switch | not_closed | no_year_manifest | 2656 |
| window-switch | not_closed | unread_sibling_page | 271 |
| window-switch | not_closed | year_manifest_bad | 1 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 255 |
| ac-compressor | no_records | - | 506 |
| ac-compressor | split | option_split | 2644 |
| ac-compressor | conditional | conditional:engine_unattested | 2215 |
| alternator | unmapped | - | 255 |
| alternator | no_records | - | 665 |
| alternator | split | no_candidates | 17 |
| alternator | split | option_split | 2589 |
| alternator | conditional | conditional:engine_unattested | 2094 |
| bumper-front | unmapped | - | 255 |
| bumper-front | no_records | - | 1008 |
| bumper-front | split | option_split | 3390 |
| bumper-front | conditional | conditional:engine_unattested | 956 |
| bumper-front | conditional | conditional:option | 11 |
| bumper-rear | unmapped | - | 255 |
| bumper-rear | no_records | - | 602 |
| bumper-rear | split | option_split | 3827 |
| bumper-rear | conditional | conditional:engine_unattested | 925 |
| bumper-rear | conditional | conditional:option | 11 |
| climate-control | unmapped | - | 255 |
| climate-control | no_records | - | 539 |
| climate-control | split | no_candidates | 41 |
| climate-control | split | option_split | 3466 |
| climate-control | conditional | conditional:engine_unattested | 1319 |
| door-front | unmapped | - | 255 |
| door-front | no_records | - | 798 |
| door-front | split | option_split | 3113 |
| door-front | conditional | conditional:engine_unattested | 1454 |
| door-rear | unmapped | - | 255 |
| door-rear | no_records | - | 767 |
| door-rear | split | option_split | 2986 |
| door-rear | conditional | conditional:engine_unattested | 1612 |
| fender | unmapped | - | 255 |
| fender | no_records | - | 918 |
| fender | split | option_split | 2538 |
| fender | split | slot_missing | 163 |
| fender | conditional | conditional:engine_unattested | 1746 |
| fuel-pump-module | unmapped | - | 255 |
| fuel-pump-module | no_records | - | 430 |
| fuel-pump-module | split | no_candidates | 1 |
| fuel-pump-module | split | option_split | 3663 |
| fuel-pump-module | conditional | conditional:engine_unattested | 1271 |
| gauge-cluster | unmapped | - | 255 |
| gauge-cluster | no_records | - | 3098 |
| gauge-cluster | split | no_candidates | 178 |
| gauge-cluster | split | option_split | 2089 |
| grille | unmapped | - | 255 |
| grille | no_records | - | 1609 |
| grille | split | no_candidates | 146 |
| grille | split | option_split | 3058 |
| grille | conditional | conditional:engine_unattested | 552 |
| headlights | unmapped | - | 255 |
| headlights | no_records | - | 1186 |
| headlights | split | no_candidates | 1 |
| headlights | split | option_split | 3150 |
| headlights | conditional | conditional:engine_unattested | 1028 |
| hood | unmapped | - | 255 |
| hood | no_records | - | 448 |
| hood | split | option_split | 2890 |
| hood | conditional | conditional:engine_unattested | 2027 |
| ignition-coils | unmapped | - | 255 |
| ignition-coils | no_records | - | 237 |
| ignition-coils | split | option_split | 3549 |
| ignition-coils | conditional | conditional:engine_unattested | 1364 |
| ignition-coils | conditional | conditional:package | 215 |
| liftgate | unmapped | - | 255 |
| liftgate | no_records | - | 715 |
| liftgate | split | option_split | 2305 |
| liftgate | conditional | conditional:engine_unattested | 2345 |
| power-steering-pump | unmapped | - | 255 |
| power-steering-pump | no_records | - | 1201 |
| power-steering-pump | split | option_split | 3435 |
| power-steering-pump | conditional | conditional:engine_unattested | 679 |
| power-steering-pump | conditional | conditional:option | 50 |
| radiator | unmapped | - | 255 |
| radiator | no_records | - | 281 |
| radiator | split | option_split | 4520 |
| radiator | conditional | conditional:engine_unattested | 564 |
| side-mirrors | unmapped | - | 255 |
| side-mirrors | no_records | - | 745 |
| side-mirrors | split | option_split | 4356 |
| side-mirrors | split | slot_missing | 4 |
| side-mirrors | conditional | conditional:engine_unattested | 260 |
| starter | unmapped | - | 255 |
| starter | no_records | - | 65 |
| starter | split | option_split | 5185 |
| starter | conditional | conditional:engine_unattested | 115 |
| tail-lights | unmapped | - | 255 |
| tail-lights | no_records | - | 609 |
| tail-lights | split | no_candidates | 1 |
| tail-lights | split | option_split | 3780 |
| tail-lights | conditional | conditional:engine_unattested | 975 |
| throttle-body | unmapped | - | 255 |
| throttle-body | no_records | - | 96 |
| throttle-body | split | no_candidates | 1 |
| throttle-body | split | option_split | 4477 |
| throttle-body | conditional | conditional:engine_unattested | 791 |
| trunk-lid | unmapped | - | 255 |
| trunk-lid | no_records | - | 1691 |
| trunk-lid | split | no_candidates | 415 |
| trunk-lid | split | option_split | 1489 |
| trunk-lid | conditional | conditional:engine_unattested | 1770 |
| window-regulator | unmapped | - | 255 |
| window-regulator | no_records | - | 106 |
| window-regulator | split | no_candidates | 1 |
| window-regulator | split | packaging_unstated | 5258 |
| window-switch | unmapped | - | 255 |
| window-switch | no_records | - | 883 |
| window-switch | split | no_candidates | 185 |
| window-switch | split | option_split | 2148 |
| window-switch | split | position_missing | 2149 |

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
