# OEM curation report: subaru

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-06T06:33:58Z.

- records 2101, classes 2101, list rows 21183, year manifests 62, cells 2640
- Verified groups 0, engine vg groups 0, Likely groups 379
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.subarupartsdeal.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.subarupartsdeal.com: only 0% of its 4217 fitment rows can be coverage: its option column holds trims (option_column_is_trims), which count only after a namespace audit (spec 5.2)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 263 |
| ac-compressor | no_records | - | 494 |
| ac-compressor | not_closed | no_list_manifest | 1533 |
| ac-compressor | not_closed | no_year_manifest | 2989 |
| ac-compressor | not_closed | unattested | 148 |
| ac-compressor | not_closed | uncrawled_chain_member | 125 |
| ac-compressor | not_closed | year_manifest_bad | 1 |
| alternator | unmapped | - | 263 |
| alternator | no_records | - | 649 |
| alternator | not_closed | no_list_manifest | 1533 |
| alternator | not_closed | no_year_manifest | 2834 |
| alternator | not_closed | unattested | 44 |
| alternator | not_closed | uncrawled_chain_member | 229 |
| alternator | not_closed | year_manifest_bad | 1 |
| bumper-front | unmapped | - | 263 |
| bumper-front | no_records | - | 981 |
| bumper-front | not_closed | list_manifest_bad | 93 |
| bumper-front | not_closed | no_list_manifest | 67 |
| bumper-front | not_closed | no_year_manifest | 2496 |
| bumper-front | not_closed | unread_sibling_page | 1653 |
| bumper-rear | unmapped | - | 263 |
| bumper-rear | no_records | - | 590 |
| bumper-rear | not_closed | list_manifest_bad | 93 |
| bumper-rear | not_closed | no_list_manifest | 67 |
| bumper-rear | not_closed | no_year_manifest | 2887 |
| bumper-rear | not_closed | unread_sibling_page | 1653 |
| climate-control | unmapped | - | 263 |
| climate-control | no_records | - | 520 |
| climate-control | not_closed | no_list_manifest | 1533 |
| climate-control | not_closed | no_year_manifest | 2963 |
| climate-control | not_closed | unread_sibling_page | 273 |
| climate-control | not_closed | year_manifest_bad | 1 |
| door-front | unmapped | - | 263 |
| door-front | no_records | - | 789 |
| door-front | not_closed | list_manifest_bad | 93 |
| door-front | not_closed | no_list_manifest | 67 |
| door-front | not_closed | no_year_manifest | 2688 |
| door-front | not_closed | unread_sibling_page | 1653 |
| door-rear | unmapped | - | 263 |
| door-rear | no_records | - | 747 |
| door-rear | not_closed | list_manifest_bad | 93 |
| door-rear | not_closed | no_list_manifest | 67 |
| door-rear | not_closed | no_year_manifest | 2730 |
| door-rear | not_closed | unread_sibling_page | 1653 |
| fender | unmapped | - | 263 |
| fender | no_records | - | 905 |
| fender | not_closed | list_manifest_bad | 93 |
| fender | not_closed | no_list_manifest | 67 |
| fender | not_closed | no_year_manifest | 2572 |
| fender | not_closed | unattested | 1289 |
| fender | not_closed | uncrawled_chain_member | 364 |
| fuel-pump-module | unmapped | - | 263 |
| fuel-pump-module | no_records | - | 415 |
| fuel-pump-module | not_closed | no_list_manifest | 1533 |
| fuel-pump-module | not_closed | no_year_manifest | 3068 |
| fuel-pump-module | not_closed | unread_sibling_page | 273 |
| fuel-pump-module | not_closed | year_manifest_bad | 1 |
| gauge-cluster | unmapped | - | 263 |
| gauge-cluster | no_records | - | 3047 |
| gauge-cluster | not_closed | list_manifest_bad | 93 |
| gauge-cluster | not_closed | no_year_manifest | 497 |
| gauge-cluster | not_closed | unread_sibling_page | 1653 |
| grille | unmapped | - | 263 |
| grille | no_records | - | 1573 |
| grille | not_closed | list_manifest_bad | 93 |
| grille | not_closed | no_list_manifest | 67 |
| grille | not_closed | no_year_manifest | 1904 |
| grille | not_closed | unattested | 332 |
| grille | not_closed | uncrawled_chain_member | 218 |
| grille | not_closed | unread_sibling_page | 1103 |
| headlights | unmapped | - | 263 |
| headlights | no_records | - | 1171 |
| headlights | not_closed | no_list_manifest | 1533 |
| headlights | not_closed | no_year_manifest | 2312 |
| headlights | not_closed | unattested | 229 |
| headlights | not_closed | uncrawled_chain_member | 44 |
| headlights | not_closed | year_manifest_bad | 1 |
| hood | unmapped | - | 263 |
| hood | no_records | - | 444 |
| hood | not_closed | list_manifest_bad | 93 |
| hood | not_closed | no_list_manifest | 67 |
| hood | not_closed | no_year_manifest | 3033 |
| hood | not_closed | unread_sibling_page | 1651 |
| hood | not_closed | unverified_product | 2 |
| ignition-coils | unmapped | - | 263 |
| ignition-coils | no_records | - | 232 |
| ignition-coils | not_closed | list_manifest_bad | 93 |
| ignition-coils | not_closed | no_list_manifest | 67 |
| ignition-coils | not_closed | no_year_manifest | 3245 |
| ignition-coils | not_closed | unattested | 12 |
| ignition-coils | not_closed | uncrawled_chain_member | 1639 |
| ignition-coils | not_closed | unverified_product | 2 |
| liftgate | unmapped | - | 263 |
| liftgate | no_records | - | 701 |
| liftgate | not_closed | list_manifest_bad | 93 |
| liftgate | not_closed | no_list_manifest | 67 |
| liftgate | not_closed | no_year_manifest | 2776 |
| liftgate | not_closed | unattested | 1426 |
| liftgate | not_closed | uncrawled_chain_member | 225 |
| liftgate | not_closed | unverified_product | 2 |
| power-steering-pump | unmapped | - | 263 |
| power-steering-pump | no_records | - | 1164 |
| power-steering-pump | not_closed | no_list_manifest | 1313 |
| power-steering-pump | not_closed | no_year_manifest | 2615 |
| power-steering-pump | not_closed | unread_sibling_page | 198 |
| radiator | unmapped | - | 263 |
| radiator | no_records | - | 278 |
| radiator | not_closed | list_manifest_bad | 93 |
| radiator | not_closed | no_list_manifest | 67 |
| radiator | not_closed | no_year_manifest | 3199 |
| radiator | not_closed | unattested | 1120 |
| radiator | not_closed | uncrawled_chain_member | 408 |
| radiator | not_closed | unread_sibling_page | 125 |
| side-mirrors | unmapped | - | 263 |
| side-mirrors | no_records | - | 731 |
| side-mirrors | not_closed | no_list_manifest | 1533 |
| side-mirrors | not_closed | no_year_manifest | 2752 |
| side-mirrors | not_closed | unattested | 43 |
| side-mirrors | not_closed | uncrawled_chain_member | 230 |
| side-mirrors | not_closed | year_manifest_bad | 1 |
| starter | unmapped | - | 263 |
| starter | no_records | - | 66 |
| starter | not_closed | no_list_manifest | 1540 |
| starter | not_closed | no_year_manifest | 3410 |
| starter | not_closed | unattested | 101 |
| starter | not_closed | uncrawled_chain_member | 172 |
| starter | not_closed | year_manifest_bad | 1 |
| tail-lights | unmapped | - | 263 |
| tail-lights | no_records | - | 600 |
| tail-lights | not_closed | no_list_manifest | 1540 |
| tail-lights | not_closed | no_year_manifest | 2876 |
| tail-lights | not_closed | unattested | 179 |
| tail-lights | not_closed | uncrawled_chain_member | 94 |
| tail-lights | not_closed | year_manifest_bad | 1 |
| throttle-body | unmapped | - | 263 |
| throttle-body | no_records | - | 95 |
| throttle-body | not_closed | no_list_manifest | 1540 |
| throttle-body | not_closed | no_year_manifest | 3381 |
| throttle-body | not_closed | unattested | 130 |
| throttle-body | not_closed | uncrawled_chain_member | 143 |
| throttle-body | not_closed | year_manifest_bad | 1 |
| trunk-lid | unmapped | - | 263 |
| trunk-lid | no_records | - | 1663 |
| trunk-lid | not_closed | list_manifest_bad | 93 |
| trunk-lid | not_closed | no_list_manifest | 67 |
| trunk-lid | not_closed | no_year_manifest | 1939 |
| trunk-lid | not_closed | unread_sibling_page | 1528 |
| window-regulator | unmapped | - | 263 |
| window-regulator | no_records | - | 106 |
| window-regulator | not_closed | no_list_manifest | 1540 |
| window-regulator | not_closed | no_year_manifest | 3370 |
| window-regulator | not_closed | unread_sibling_page | 273 |
| window-regulator | not_closed | year_manifest_bad | 1 |
| window-switch | unmapped | - | 263 |
| window-switch | no_records | - | 865 |
| window-switch | not_closed | no_list_manifest | 1533 |
| window-switch | not_closed | no_year_manifest | 2618 |
| window-switch | not_closed | unread_sibling_page | 273 |
| window-switch | not_closed | year_manifest_bad | 1 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 263 |
| ac-compressor | no_records | - | 494 |
| ac-compressor | split | option_split | 2618 |
| ac-compressor | conditional | conditional:engine_unattested | 2178 |
| alternator | unmapped | - | 263 |
| alternator | no_records | - | 649 |
| alternator | split | no_candidates | 18 |
| alternator | split | option_split | 2560 |
| alternator | conditional | conditional:engine_unattested | 2063 |
| bumper-front | unmapped | - | 263 |
| bumper-front | no_records | - | 981 |
| bumper-front | split | option_split | 3355 |
| bumper-front | conditional | conditional:engine_unattested | 942 |
| bumper-front | conditional | conditional:option | 12 |
| bumper-rear | unmapped | - | 263 |
| bumper-rear | no_records | - | 590 |
| bumper-rear | split | option_split | 3788 |
| bumper-rear | conditional | conditional:engine_unattested | 900 |
| bumper-rear | conditional | conditional:option | 12 |
| climate-control | unmapped | - | 263 |
| climate-control | no_records | - | 520 |
| climate-control | split | no_candidates | 43 |
| climate-control | split | option_split | 3420 |
| climate-control | conditional | conditional:engine_unattested | 1307 |
| door-front | unmapped | - | 263 |
| door-front | no_records | - | 789 |
| door-front | split | option_split | 3070 |
| door-front | conditional | conditional:engine_unattested | 1431 |
| door-rear | unmapped | - | 263 |
| door-rear | no_records | - | 747 |
| door-rear | split | option_split | 2956 |
| door-rear | conditional | conditional:engine_unattested | 1587 |
| fender | unmapped | - | 263 |
| fender | no_records | - | 905 |
| fender | split | option_split | 2509 |
| fender | split | slot_missing | 159 |
| fender | conditional | conditional:engine_unattested | 1717 |
| fuel-pump-module | unmapped | - | 263 |
| fuel-pump-module | no_records | - | 415 |
| fuel-pump-module | split | no_candidates | 1 |
| fuel-pump-module | split | option_split | 3611 |
| fuel-pump-module | conditional | conditional:engine_unattested | 1263 |
| gauge-cluster | unmapped | - | 263 |
| gauge-cluster | no_records | - | 3047 |
| gauge-cluster | split | no_candidates | 181 |
| gauge-cluster | split | option_split | 2062 |
| grille | unmapped | - | 263 |
| grille | no_records | - | 1573 |
| grille | split | no_candidates | 141 |
| grille | split | option_split | 3028 |
| grille | conditional | conditional:engine_unattested | 548 |
| headlights | unmapped | - | 263 |
| headlights | no_records | - | 1171 |
| headlights | split | no_candidates | 1 |
| headlights | split | option_split | 3091 |
| headlights | conditional | conditional:engine_unattested | 1027 |
| hood | unmapped | - | 263 |
| hood | no_records | - | 444 |
| hood | split | option_split | 2850 |
| hood | conditional | conditional:engine_unattested | 1996 |
| ignition-coils | unmapped | - | 263 |
| ignition-coils | no_records | - | 232 |
| ignition-coils | split | option_split | 3497 |
| ignition-coils | conditional | conditional:engine_unattested | 1350 |
| ignition-coils | conditional | conditional:package | 211 |
| liftgate | unmapped | - | 263 |
| liftgate | no_records | - | 701 |
| liftgate | split | option_split | 2264 |
| liftgate | conditional | conditional:engine_unattested | 2325 |
| power-steering-pump | unmapped | - | 263 |
| power-steering-pump | no_records | - | 1164 |
| power-steering-pump | split | option_split | 3397 |
| power-steering-pump | conditional | conditional:engine_unattested | 680 |
| power-steering-pump | conditional | conditional:option | 49 |
| radiator | unmapped | - | 263 |
| radiator | no_records | - | 278 |
| radiator | split | option_split | 4465 |
| radiator | conditional | conditional:engine_unattested | 547 |
| side-mirrors | unmapped | - | 263 |
| side-mirrors | no_records | - | 731 |
| side-mirrors | split | option_split | 4299 |
| side-mirrors | split | slot_missing | 3 |
| side-mirrors | conditional | conditional:engine_unattested | 257 |
| starter | unmapped | - | 263 |
| starter | no_records | - | 66 |
| starter | split | option_split | 5111 |
| starter | conditional | conditional:engine_unattested | 113 |
| tail-lights | unmapped | - | 263 |
| tail-lights | no_records | - | 600 |
| tail-lights | split | no_candidates | 1 |
| tail-lights | split | option_split | 3739 |
| tail-lights | conditional | conditional:engine_unattested | 950 |
| throttle-body | unmapped | - | 263 |
| throttle-body | no_records | - | 95 |
| throttle-body | split | no_candidates | 1 |
| throttle-body | split | option_split | 4420 |
| throttle-body | conditional | conditional:engine_unattested | 774 |
| trunk-lid | unmapped | - | 263 |
| trunk-lid | no_records | - | 1663 |
| trunk-lid | split | no_candidates | 410 |
| trunk-lid | split | option_split | 1470 |
| trunk-lid | conditional | conditional:engine_unattested | 1747 |
| window-regulator | unmapped | - | 263 |
| window-regulator | no_records | - | 106 |
| window-regulator | split | no_candidates | 1 |
| window-regulator | split | packaging_unstated | 5183 |
| window-switch | unmapped | - | 263 |
| window-switch | no_records | - | 865 |
| window-switch | split | no_candidates | 187 |
| window-switch | split | option_split | 2121 |
| window-switch | split | position_missing | 2117 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 226
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
