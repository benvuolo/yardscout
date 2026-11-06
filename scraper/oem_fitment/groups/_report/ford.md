# OEM curation report: ford

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-06T07:12:44Z.

- records 5893, classes 5893, list rows 49651, year manifests 163, cells 10035
- Verified groups 0, engine vg groups 0, Likely groups 88
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.fordpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.fordpartsgiant.com: only 1% of its 12046 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2260 |
| ac-compressor | no_records | - | 8798 |
| ac-compressor | not_closed | ambig_target | 407 |
| ac-compressor | not_closed | no_list_manifest | 9068 |
| ac-compressor | not_closed | no_year_manifest | 35603 |
| ac-compressor | not_closed | unattested | 82 |
| ac-compressor | not_closed | uncrawled_chain_member | 60 |
| ac-compressor | not_closed | unverified_product | 261 |
| ac-compressor | not_closed | variant_unread | 1758 |
| ac-compressor | not_closed | year_manifest_bad | 2187 |
| alternator | unmapped | - | 2260 |
| alternator | no_records | - | 7163 |
| alternator | not_closed | no_list_manifest | 9068 |
| alternator | not_closed | no_year_manifest | 37431 |
| alternator | not_closed | suspect_variant | 52 |
| alternator | not_closed | uncrawled_chain_member | 134 |
| alternator | not_closed | unverified_product | 177 |
| alternator | not_closed | variant_unread | 1758 |
| alternator | not_closed | year_manifest_bad | 2441 |
| bumper-front | unmapped | - | 2260 |
| bumper-front | no_records | - | 11920 |
| bumper-front | not_closed | ambig_target | 293 |
| bumper-front | not_closed | no_list_manifest | 154 |
| bumper-front | not_closed | no_year_manifest | 32427 |
| bumper-front | not_closed | unread_sibling_page | 9068 |
| bumper-front | not_closed | variant_unread | 1758 |
| bumper-front | not_closed | year_manifest_bad | 2604 |
| bumper-rear | unmapped | - | 2260 |
| bumper-rear | no_records | - | 9734 |
| bumper-rear | not_closed | ambig_target | 410 |
| bumper-rear | not_closed | no_list_manifest | 174 |
| bumper-rear | not_closed | no_year_manifest | 34442 |
| bumper-rear | not_closed | unread_sibling_page | 9068 |
| bumper-rear | not_closed | variant_unread | 1758 |
| bumper-rear | not_closed | year_manifest_bad | 2638 |
| climate-control | unmapped | - | 2260 |
| climate-control | no_records | - | 22840 |
| climate-control | not_closed | ambig_target | 166 |
| climate-control | not_closed | no_list_manifest | 8153 |
| climate-control | not_closed | no_year_manifest | 23608 |
| climate-control | not_closed | unread_sibling_page | 403 |
| climate-control | not_closed | variant_unread | 1758 |
| climate-control | not_closed | year_manifest_bad | 1296 |
| door-front | unmapped | - | 2260 |
| door-front | no_records | - | 25822 |
| door-front | not_closed | ambig_target | 140 |
| door-front | not_closed | no_list_manifest | 112 |
| door-front | not_closed | no_year_manifest | 18706 |
| door-front | not_closed | unread_sibling_page | 9068 |
| door-front | not_closed | variant_unread | 1758 |
| door-front | not_closed | year_manifest_bad | 2618 |
| door-rear | unmapped | - | 2260 |
| door-rear | no_records | - | 25032 |
| door-rear | not_closed | ambig_target | 140 |
| door-rear | not_closed | no_list_manifest | 52 |
| door-rear | not_closed | no_year_manifest | 20676 |
| door-rear | not_closed | unread_sibling_page | 8804 |
| door-rear | not_closed | variant_unread | 1758 |
| door-rear | not_closed | year_manifest_bad | 1762 |
| fender | unmapped | - | 2260 |
| fender | no_records | - | 15878 |
| fender | not_closed | ambig_target | 293 |
| fender | not_closed | no_list_manifest | 96 |
| fender | not_closed | no_year_manifest | 28447 |
| fender | not_closed | unattested | 3867 |
| fender | not_closed | uncrawled_chain_member | 1991 |
| fender | not_closed | unverified_product | 3210 |
| fender | not_closed | variant_unread | 1758 |
| fender | not_closed | year_manifest_bad | 2684 |
| fuel-pump-module | unmapped | - | 2260 |
| fuel-pump-module | no_records | - | 24514 |
| fuel-pump-module | not_closed | ambig_target | 89 |
| fuel-pump-module | not_closed | no_list_manifest | 8443 |
| fuel-pump-module | not_closed | no_year_manifest | 22412 |
| fuel-pump-module | not_closed | unread_sibling_page | 403 |
| fuel-pump-module | not_closed | variant_unread | 1758 |
| fuel-pump-module | not_closed | year_manifest_bad | 605 |
| gauge-cluster | unmapped | - | 2260 |
| gauge-cluster | no_records | - | 31627 |
| gauge-cluster | not_closed | ambig_target | 253 |
| gauge-cluster | not_closed | no_list_manifest | 52 |
| gauge-cluster | not_closed | no_year_manifest | 12807 |
| gauge-cluster | not_closed | unread_sibling_page | 9068 |
| gauge-cluster | not_closed | variant_unread | 1758 |
| gauge-cluster | not_closed | year_manifest_bad | 2659 |
| grille | unmapped | - | 2260 |
| grille | no_records | - | 16764 |
| grille | not_closed | ambig_target | 293 |
| grille | not_closed | no_list_manifest | 52 |
| grille | not_closed | no_year_manifest | 27671 |
| grille | not_closed | unattested | 6095 |
| grille | not_closed | uncrawled_chain_member | 750 |
| grille | not_closed | unverified_product | 2223 |
| grille | not_closed | variant_unread | 1758 |
| grille | not_closed | year_manifest_bad | 2618 |
| headlights | unmapped | - | 2260 |
| headlights | no_records | - | 14456 |
| headlights | not_closed | ambig_target | 407 |
| headlights | not_closed | no_list_manifest | 8804 |
| headlights | not_closed | no_year_manifest | 29904 |
| headlights | not_closed | unattested | 215 |
| headlights | not_closed | uncrawled_chain_member | 188 |
| headlights | not_closed | variant_unread | 1458 |
| headlights | not_closed | year_manifest_bad | 2792 |
| hood | unmapped | - | 2260 |
| hood | no_records | - | 12835 |
| hood | not_closed | ambig_target | 293 |
| hood | not_closed | no_list_manifest | 96 |
| hood | not_closed | no_year_manifest | 31531 |
| hood | not_closed | unattested | 5708 |
| hood | not_closed | uncrawled_chain_member | 1206 |
| hood | not_closed | unverified_product | 2154 |
| hood | not_closed | variant_unread | 1758 |
| hood | not_closed | year_manifest_bad | 2643 |
| ignition-coils | unmapped | - | 2260 |
| ignition-coils | no_records | - | 11435 |
| ignition-coils | not_closed | ambig_target | 157 |
| ignition-coils | not_closed | no_list_manifest | 358 |
| ignition-coils | not_closed | no_year_manifest | 33737 |
| ignition-coils | not_closed | uncrawled_chain_member | 338 |
| ignition-coils | not_closed | unverified_product | 8730 |
| ignition-coils | not_closed | variant_unread | 1758 |
| ignition-coils | not_closed | year_manifest_bad | 1711 |
| liftgate | unmapped | - | 2260 |
| liftgate | no_records | - | 35536 |
| liftgate | not_closed | ambig_target | 140 |
| liftgate | not_closed | no_year_manifest | 9512 |
| liftgate | not_closed | unread_sibling_page | 9068 |
| liftgate | not_closed | variant_unread | 1758 |
| liftgate | not_closed | year_manifest_bad | 2210 |
| power-steering-pump | unmapped | - | 2260 |
| power-steering-pump | no_records | - | 32051 |
| power-steering-pump | not_closed | no_list_manifest | 5240 |
| power-steering-pump | not_closed | no_year_manifest | 18807 |
| power-steering-pump | not_closed | unread_sibling_page | 245 |
| power-steering-pump | not_closed | variant_unread | 350 |
| power-steering-pump | not_closed | year_manifest_bad | 1531 |
| radiator | unmapped | - | 2260 |
| radiator | no_records | - | 15028 |
| radiator | not_closed | ambig_target | 456 |
| radiator | not_closed | no_list_manifest | 270 |
| radiator | not_closed | no_year_manifest | 29047 |
| radiator | not_closed | unattested | 1518 |
| radiator | not_closed | uncrawled_chain_member | 5780 |
| radiator | not_closed | unverified_product | 1770 |
| radiator | not_closed | variant_unread | 1758 |
| radiator | not_closed | year_manifest_bad | 2597 |
| side-mirrors | unmapped | - | 2260 |
| side-mirrors | no_records | - | 7745 |
| side-mirrors | not_closed | ambig_target | 453 |
| side-mirrors | not_closed | no_list_manifest | 9068 |
| side-mirrors | not_closed | no_year_manifest | 36111 |
| side-mirrors | not_closed | unread_sibling_page | 403 |
| side-mirrors | not_closed | variant_unread | 1758 |
| side-mirrors | not_closed | year_manifest_bad | 2686 |
| starter | unmapped | - | 2260 |
| starter | no_records | - | 17789 |
| starter | not_closed | ambig_target | 17 |
| starter | not_closed | no_list_manifest | 9068 |
| starter | not_closed | no_year_manifest | 29034 |
| starter | not_closed | suspect_variant | 96 |
| starter | not_closed | unattested | 28 |
| starter | not_closed | uncrawled_chain_member | 30 |
| starter | not_closed | unverified_product | 209 |
| starter | not_closed | variant_unread | 1758 |
| starter | not_closed | year_manifest_bad | 195 |
| tail-lights | unmapped | - | 2260 |
| tail-lights | no_records | - | 12594 |
| tail-lights | not_closed | ambig_target | 456 |
| tail-lights | not_closed | no_list_manifest | 9068 |
| tail-lights | not_closed | no_year_manifest | 31623 |
| tail-lights | not_closed | unattested | 188 |
| tail-lights | not_closed | uncrawled_chain_member | 215 |
| tail-lights | not_closed | variant_unread | 1758 |
| tail-lights | not_closed | year_manifest_bad | 2322 |
| tailgate | unmapped | - | 2260 |
| tailgate | no_records | - | 36686 |
| tailgate | not_closed | ambig_target | 293 |
| tailgate | not_closed | no_year_manifest | 9244 |
| tailgate | not_closed | unattested | 8380 |
| tailgate | not_closed | uncrawled_chain_member | 688 |
| tailgate | not_closed | variant_unread | 1758 |
| tailgate | not_closed | year_manifest_bad | 1175 |
| throttle-body | unmapped | - | 2260 |
| throttle-body | no_records | - | 27013 |
| throttle-body | not_closed | no_list_manifest | 5050 |
| throttle-body | not_closed | no_year_manifest | 22839 |
| throttle-body | not_closed | unattested | 45 |
| throttle-body | not_closed | uncrawled_chain_member | 182 |
| throttle-body | not_closed | variant_unread | 1758 |
| throttle-body | not_closed | year_manifest_bad | 1337 |
| tow-mirrors | unmapped | - | 2260 |
| tow-mirrors | no_records | - | 52222 |
| tow-mirrors | not_closed | ambig_target | 218 |
| tow-mirrors | not_closed | no_list_manifest | 646 |
| tow-mirrors | not_closed | no_year_manifest | 4305 |
| tow-mirrors | not_closed | variant_unread | 833 |
| trunk-lid | unmapped | - | 2260 |
| trunk-lid | no_records | - | 35447 |
| trunk-lid | not_closed | no_list_manifest | 52 |
| trunk-lid | not_closed | no_year_manifest | 12204 |
| trunk-lid | not_closed | unattested | 5805 |
| trunk-lid | not_closed | uncrawled_chain_member | 2390 |
| trunk-lid | not_closed | variant_unread | 925 |
| trunk-lid | not_closed | year_manifest_bad | 1401 |
| window-regulator | unmapped | - | 2260 |
| window-regulator | no_records | - | 17067 |
| window-regulator | not_closed | ambig_target | 17 |
| window-regulator | not_closed | no_list_manifest | 9068 |
| window-regulator | not_closed | no_year_manifest | 29191 |
| window-regulator | not_closed | unread_sibling_page | 403 |
| window-regulator | not_closed | variant_unread | 1758 |
| window-regulator | not_closed | year_manifest_bad | 720 |
| window-switch | unmapped | - | 2260 |
| window-switch | no_records | - | 11410 |
| window-switch | not_closed | ambig_target | 150 |
| window-switch | not_closed | no_list_manifest | 9068 |
| window-switch | not_closed | no_year_manifest | 34092 |
| window-switch | not_closed | unattested | 227 |
| window-switch | not_closed | uncrawled_chain_member | 106 |
| window-switch | not_closed | unverified_product | 70 |
| window-switch | not_closed | variant_unread | 1758 |
| window-switch | not_closed | year_manifest_bad | 1343 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2260 |
| ac-compressor | no_records | - | 8798 |
| ac-compressor | split | no_candidates | 89 |
| ac-compressor | split | option_split | 33706 |
| ac-compressor | conditional | conditional:engine | 1161 |
| ac-compressor | conditional | conditional:engine_unattested | 13529 |
| ac-compressor | conditional | conditional:trim | 941 |
| alternator | unmapped | - | 2260 |
| alternator | no_records | - | 7163 |
| alternator | split | no_candidates | 73 |
| alternator | split | option_split | 43033 |
| alternator | conditional | conditional:engine | 264 |
| alternator | conditional | conditional:engine_unattested | 7200 |
| alternator | conditional | conditional:production | 43 |
| alternator | conditional | conditional:trim | 448 |
| bumper-front | unmapped | - | 2260 |
| bumper-front | no_records | - | 11920 |
| bumper-front | split | no_candidates | 127 |
| bumper-front | split | option_split | 42202 |
| bumper-front | conditional | conditional:engine_unattested | 3975 |
| bumper-rear | unmapped | - | 2260 |
| bumper-rear | no_records | - | 9734 |
| bumper-rear | split | no_candidates | 81 |
| bumper-rear | split | option_split | 43945 |
| bumper-rear | conditional | conditional:engine_unattested | 4464 |
| climate-control | unmapped | - | 2260 |
| climate-control | no_records | - | 22840 |
| climate-control | split | no_candidates | 131 |
| climate-control | split | option_split | 26049 |
| climate-control | conditional | conditional:colour | 221 |
| climate-control | conditional | conditional:engine_unattested | 8757 |
| climate-control | conditional | conditional:trim | 226 |
| door-front | unmapped | - | 2260 |
| door-front | no_records | - | 25822 |
| door-front | split | no_candidates | 2414 |
| door-front | split | option_split | 13315 |
| door-front | split | slot_missing | 2295 |
| door-front | conditional | conditional:body | 177 |
| door-front | conditional | conditional:engine_unattested | 8230 |
| door-front | conditional | conditional:qualifier | 4325 |
| door-front | conditional | conditional:trim | 1646 |
| door-rear | unmapped | - | 2260 |
| door-rear | no_records | - | 25032 |
| door-rear | split | no_candidates | 1342 |
| door-rear | split | option_split | 16062 |
| door-rear | split | slot_missing | 102 |
| door-rear | conditional | conditional:engine_unattested | 1150 |
| door-rear | conditional | conditional:qualifier | 13741 |
| door-rear | conditional | conditional:trim | 795 |
| fender | unmapped | - | 2260 |
| fender | no_records | - | 15878 |
| fender | split | no_candidates | 186 |
| fender | split | option_split | 23441 |
| fender | split | slot_missing | 601 |
| fender | conditional | conditional:engine_unattested | 13573 |
| fender | conditional | conditional:trim | 4545 |
| fuel-pump-module | unmapped | - | 2260 |
| fuel-pump-module | no_records | - | 24514 |
| fuel-pump-module | split | no_candidates | 25 |
| fuel-pump-module | split | option_split | 26624 |
| fuel-pump-module | conditional | conditional:engine | 28 |
| fuel-pump-module | conditional | conditional:engine_unattested | 5782 |
| fuel-pump-module | conditional | conditional:trim | 1251 |
| gauge-cluster | unmapped | - | 2260 |
| gauge-cluster | no_records | - | 31627 |
| gauge-cluster | split | no_candidates | 904 |
| gauge-cluster | split | option_split | 23838 |
| gauge-cluster | conditional | conditional:engine_unattested | 1552 |
| gauge-cluster | conditional | conditional:production | 193 |
| gauge-cluster | conditional | conditional:trim | 110 |
| grille | unmapped | - | 2260 |
| grille | no_records | - | 16764 |
| grille | split | no_candidates | 701 |
| grille | split | option_split | 39487 |
| grille | conditional | conditional:engine_unattested | 1152 |
| grille | conditional | conditional:option | 120 |
| headlights | unmapped | - | 2260 |
| headlights | no_records | - | 14456 |
| headlights | split | no_candidates | 20 |
| headlights | split | option_split | 33907 |
| headlights | split | slot_missing | 435 |
| headlights | conditional | conditional:engine_unattested | 7896 |
| headlights | conditional | conditional:option | 100 |
| headlights | conditional | conditional:package | 63 |
| headlights | conditional | conditional:production | 441 |
| headlights | conditional | conditional:trim | 906 |
| hood | unmapped | - | 2260 |
| hood | no_records | - | 12835 |
| hood | split | no_candidates | 273 |
| hood | split | option_split | 7442 |
| hood | conditional | conditional:engine_unattested | 28852 |
| hood | conditional | conditional:trim | 8822 |
| ignition-coils | unmapped | - | 2260 |
| ignition-coils | no_records | - | 11435 |
| ignition-coils | split | no_candidates | 140 |
| ignition-coils | split | option_split | 25344 |
| ignition-coils | conditional | conditional:engine_unattested | 18276 |
| ignition-coils | conditional | conditional:package | 2844 |
| ignition-coils | conditional | conditional:trim | 185 |
| liftgate | unmapped | - | 2260 |
| liftgate | no_records | - | 35536 |
| liftgate | split | no_candidates | 8349 |
| liftgate | split | option_split | 2722 |
| liftgate | conditional | conditional:engine_unattested | 8617 |
| liftgate | conditional | conditional:option | 1131 |
| liftgate | conditional | conditional:trim | 1869 |
| power-steering-pump | unmapped | - | 2260 |
| power-steering-pump | no_records | - | 32051 |
| power-steering-pump | split | no_candidates | 186 |
| power-steering-pump | split | option_split | 11815 |
| power-steering-pump | conditional | conditional:colour | 450 |
| power-steering-pump | conditional | conditional:engine | 296 |
| power-steering-pump | conditional | conditional:engine_unattested | 11753 |
| power-steering-pump | conditional | conditional:option | 163 |
| power-steering-pump | conditional | conditional:trim | 1510 |
| radiator | unmapped | - | 2260 |
| radiator | no_records | - | 15028 |
| radiator | split | no_candidates | 894 |
| radiator | split | option_split | 38909 |
| radiator | conditional | conditional:engine_unattested | 2785 |
| radiator | conditional | conditional:trim | 608 |
| side-mirrors | unmapped | - | 2260 |
| side-mirrors | no_records | - | 7745 |
| side-mirrors | split | no_candidates | 28 |
| side-mirrors | split | option_split | 45324 |
| side-mirrors | split | position_missing | 5 |
| side-mirrors | split | slot_missing | 2022 |
| side-mirrors | conditional | conditional:colour | 162 |
| side-mirrors | conditional | conditional:engine_unattested | 2369 |
| side-mirrors | conditional | conditional:option | 412 |
| side-mirrors | conditional | conditional:trim | 157 |
| starter | unmapped | - | 2260 |
| starter | no_records | - | 17789 |
| starter | split | no_candidates | 195 |
| starter | split | option_split | 33910 |
| starter | conditional | conditional:engine | 28 |
| starter | conditional | conditional:engine_unattested | 6137 |
| starter | conditional | conditional:option | 163 |
| starter | conditional | conditional:trim | 2 |
| tail-lights | unmapped | - | 2260 |
| tail-lights | no_records | - | 12594 |
| tail-lights | split | no_candidates | 49 |
| tail-lights | split | option_split | 38216 |
| tail-lights | split | slot_missing | 548 |
| tail-lights | conditional | conditional:colour | 56 |
| tail-lights | conditional | conditional:engine_unattested | 5560 |
| tail-lights | conditional | conditional:option | 2 |
| tail-lights | conditional | conditional:production | 128 |
| tail-lights | conditional | conditional:trim | 1071 |
| tailgate | unmapped | - | 2260 |
| tailgate | no_records | - | 36686 |
| tailgate | split | no_candidates | 9286 |
| tailgate | split | option_split | 9236 |
| tailgate | conditional | conditional:engine_unattested | 2555 |
| tailgate | conditional | conditional:trim | 461 |
| throttle-body | unmapped | - | 2260 |
| throttle-body | no_records | - | 27013 |
| throttle-body | split | no_candidates | 8 |
| throttle-body | split | option_split | 14430 |
| throttle-body | conditional | conditional:engine | 55 |
| throttle-body | conditional | conditional:engine_unattested | 14172 |
| throttle-body | conditional | conditional:option | 206 |
| throttle-body | conditional | conditional:trim | 2340 |
| tow-mirrors | unmapped | - | 2260 |
| tow-mirrors | no_records | - | 52222 |
| tow-mirrors | split | option_split | 2949 |
| tow-mirrors | split | position_conflict | 604 |
| tow-mirrors | split | slot_missing | 2360 |
| tow-mirrors | conditional | conditional:colour | 30 |
| tow-mirrors | conditional | conditional:engine_unattested | 59 |
| trunk-lid | unmapped | - | 2260 |
| trunk-lid | no_records | - | 35447 |
| trunk-lid | split | no_candidates | 5067 |
| trunk-lid | split | option_split | 13983 |
| trunk-lid | conditional | conditional:engine_unattested | 3487 |
| trunk-lid | conditional | conditional:trim | 240 |
| window-regulator | unmapped | - | 2260 |
| window-regulator | no_records | - | 17067 |
| window-regulator | split | no_candidates | 101 |
| window-regulator | split | packaging_incomplete | 3962 |
| window-regulator | split | packaging_split | 13766 |
| window-regulator | split | packaging_unstated | 21993 |
| window-regulator | split | position_missing | 735 |
| window-regulator | conditional | conditional:trim | 600 |
| window-switch | unmapped | - | 2260 |
| window-switch | no_records | - | 11410 |
| window-switch | split | no_candidates | 1389 |
| window-switch | split | option_split | 23308 |
| window-switch | split | position_missing | 16287 |
| window-switch | conditional | conditional:colour | 1327 |
| window-switch | conditional | conditional:engine_unattested | 3145 |
| window-switch | conditional | conditional:trim | 1358 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 804
- recrawl_resolved: 2
- rule_drift: 47
- universal_part_suspect: 12

## Unknown note clauses (top 30)

- `Callout Name: 17682`: 975
- `Callout Name: 10849`: 734
- `(CP) Designates Crash Part - When Ordering Please Refer To Crash Part Truckload Program Guidelines`: 710
- `Base Number: 10849`: 701
- `Base Number: 17682`: 453
- `Paint to match`: 440
- `Callout Name: 13008`: 432
- `Callout Name: 8200`: 410
- `Callout Name: 13404`: 329
- `Order From Instrument Cluster Online Ordering System Using The Online 1878 Form`: 326
- `Callout Name: 19980`: 312
- `For Instrument Cluster QC Issues Contact fesg@ford.com`: 288
- `With MPH/KMH Speedometer`: 286
- `With KMH/MPH Speedometer`: 273
- `Callout Name: 10346`: 232
- `Order From Instrument Cluster Online Ordering System Using The Online Ordering System`: 210
- `Base Number: 13008`: 207
- `Callout Name: 16005`: 207
- `XLT`: 200
- `Callout Name: 17906`: 187
- `Base Number: 8200`: 184
- `Export Dealers And Affiliates: Order Direct From FCSD-IDO`: 178
- `Callout Name: 17757`: 177
- `Headlamp Assy`: 173
- `Callout Name: 9H307`: 172
- `Fit Note: Ford Division Derivative`: 168
- `R.H.`: 166
- `Callout Name: 17D957`: 162
- `Callout Name: 17K835`: 153
- `Callout Name: 19703`: 153

## Unmapped catalog models

- Ford E-350/E-350 Super Duty: feed 'E-350/E-350 Super Duty' 0 cars (excluded: feed has no 'E-350/E-350 Super Duty'; feed splits E-350 spellings)
- Ford E-550 Super Duty: feed 'E-550 Super Duty' 0 cars
- Ford EXP: feed 'EXP' 1 cars
- Ford EcoSport: feed 'EcoSport' 0 cars
- Ford Econoline Super Duty(1996-1999): feed 'Econoline Super Duty(1996-1999)' 0 cars
- Ford F Super Duty: feed 'F Super Duty' 0 cars
- Ford F53: feed 'F-53' 0 cars
- Ford F53 Stripped Chassis: feed 'F53 Stripped Chassis' 0 cars (excluded: catalog model with no feed cars as 'F53 Stripped Chassis' (inventory 2026-11-04); nothing to map)
- Ford F59: feed 'F-59' 0 cars
- Ford Fairmont: feed 'Fairmont' 4 cars
- Ford GT: feed 'GT' 2 cars
- Ford Granada: feed 'Granada' 2 cars
- Ford Maverick: feed 'Maverick' 11 cars
- Ford Pinto: feed 'Pinto' 5 cars
- Ford Police Responder Hybrid: feed 'Police Responder Hybrid' 0 cars (excluded: catalog model with no feed cars as 'Police Responder Hybrid' (inventory 2026-11-04); nothing to map)
- Ford SSV Plug-In Hybrid: feed 'SSV Plug-In Hybrid' 0 cars (excluded: catalog model with no feed cars as 'SSV Plug-In Hybrid' (inventory 2026-11-04); nothing to map)
- Lincoln Mark VI: feed 'Mark VI' 4 cars
- Mercury Bobcat: feed 'Bobcat' 0 cars
- Mercury LN7: feed 'LN7' 0 cars
- Mercury Lynx: feed 'Lynx' 0 cars
- Mercury Marquis: feed 'Marquis' 30 cars
- Mercury Villager: feed 'Villager' 80 cars
- Mercury Zephyr: feed 'Zephyr' 3 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (3 cars, under catalog squash 'zephyr'); unmapped until a reviewed entry exists)
