# OEM curation report: ford

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-06T07:12:44Z.

- records 5893, classes 5893, list rows 49651, year manifests 163, cells 10035
- Verified groups 0, engine vg groups 0, Likely groups 48
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.fordpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.fordpartsgiant.com: only 1% of its 12046 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2243 |
| ac-compressor | no_records | - | 8844 |
| ac-compressor | not_closed | ambig_target | 410 |
| ac-compressor | not_closed | no_list_manifest | 9095 |
| ac-compressor | not_closed | no_year_manifest | 35915 |
| ac-compressor | not_closed | unattested | 81 |
| ac-compressor | not_closed | uncrawled_chain_member | 59 |
| ac-compressor | not_closed | unverified_product | 257 |
| ac-compressor | not_closed | variant_unread | 1778 |
| ac-compressor | not_closed | year_manifest_bad | 2191 |
| alternator | unmapped | - | 2243 |
| alternator | no_records | - | 7218 |
| alternator | not_closed | no_list_manifest | 9095 |
| alternator | not_closed | no_year_manifest | 37740 |
| alternator | not_closed | suspect_variant | 51 |
| alternator | not_closed | uncrawled_chain_member | 127 |
| alternator | not_closed | unverified_product | 178 |
| alternator | not_closed | variant_unread | 1778 |
| alternator | not_closed | year_manifest_bad | 2443 |
| bumper-front | unmapped | - | 2243 |
| bumper-front | no_records | - | 12031 |
| bumper-front | not_closed | ambig_target | 298 |
| bumper-front | not_closed | no_list_manifest | 150 |
| bumper-front | not_closed | no_year_manifest | 32668 |
| bumper-front | not_closed | unread_sibling_page | 9095 |
| bumper-front | not_closed | variant_unread | 1778 |
| bumper-front | not_closed | year_manifest_bad | 2610 |
| bumper-rear | unmapped | - | 2243 |
| bumper-rear | no_records | - | 9846 |
| bumper-rear | not_closed | ambig_target | 414 |
| bumper-rear | not_closed | no_list_manifest | 168 |
| bumper-rear | not_closed | no_year_manifest | 34684 |
| bumper-rear | not_closed | unread_sibling_page | 9095 |
| bumper-rear | not_closed | variant_unread | 1778 |
| bumper-rear | not_closed | year_manifest_bad | 2645 |
| climate-control | unmapped | - | 2243 |
| climate-control | no_records | - | 22999 |
| climate-control | not_closed | ambig_target | 170 |
| climate-control | not_closed | no_list_manifest | 8178 |
| climate-control | not_closed | no_year_manifest | 23823 |
| climate-control | not_closed | unread_sibling_page | 397 |
| climate-control | not_closed | variant_unread | 1778 |
| climate-control | not_closed | year_manifest_bad | 1285 |
| door-front | unmapped | - | 2243 |
| door-front | no_records | - | 26016 |
| door-front | not_closed | ambig_target | 143 |
| door-front | not_closed | no_list_manifest | 110 |
| door-front | not_closed | no_year_manifest | 18865 |
| door-front | not_closed | unread_sibling_page | 9095 |
| door-front | not_closed | variant_unread | 1778 |
| door-front | not_closed | year_manifest_bad | 2623 |
| door-rear | unmapped | - | 2243 |
| door-rear | no_records | - | 25199 |
| door-rear | not_closed | ambig_target | 143 |
| door-rear | not_closed | no_list_manifest | 51 |
| door-rear | not_closed | no_year_manifest | 20861 |
| door-rear | not_closed | unread_sibling_page | 8839 |
| door-rear | not_closed | variant_unread | 1778 |
| door-rear | not_closed | year_manifest_bad | 1759 |
| fender | unmapped | - | 2243 |
| fender | no_records | - | 16041 |
| fender | not_closed | ambig_target | 298 |
| fender | not_closed | no_list_manifest | 95 |
| fender | not_closed | no_year_manifest | 28633 |
| fender | not_closed | unattested | 3872 |
| fender | not_closed | uncrawled_chain_member | 2004 |
| fender | not_closed | unverified_product | 3219 |
| fender | not_closed | variant_unread | 1778 |
| fender | not_closed | year_manifest_bad | 2690 |
| fuel-pump-module | unmapped | - | 2243 |
| fuel-pump-module | no_records | - | 24653 |
| fuel-pump-module | not_closed | ambig_target | 92 |
| fuel-pump-module | not_closed | no_list_manifest | 8468 |
| fuel-pump-module | not_closed | no_year_manifest | 22629 |
| fuel-pump-module | not_closed | unread_sibling_page | 397 |
| fuel-pump-module | not_closed | variant_unread | 1778 |
| fuel-pump-module | not_closed | year_manifest_bad | 613 |
| gauge-cluster | unmapped | - | 2243 |
| gauge-cluster | no_records | - | 31892 |
| gauge-cluster | not_closed | ambig_target | 259 |
| gauge-cluster | not_closed | no_list_manifest | 51 |
| gauge-cluster | not_closed | no_year_manifest | 12892 |
| gauge-cluster | not_closed | unread_sibling_page | 9095 |
| gauge-cluster | not_closed | variant_unread | 1778 |
| gauge-cluster | not_closed | year_manifest_bad | 2663 |
| grille | unmapped | - | 2243 |
| grille | no_records | - | 16977 |
| grille | not_closed | ambig_target | 298 |
| grille | not_closed | no_list_manifest | 51 |
| grille | not_closed | no_year_manifest | 27808 |
| grille | not_closed | unattested | 6113 |
| grille | not_closed | uncrawled_chain_member | 750 |
| grille | not_closed | unverified_product | 2232 |
| grille | not_closed | variant_unread | 1778 |
| grille | not_closed | year_manifest_bad | 2623 |
| headlights | unmapped | - | 2243 |
| headlights | no_records | - | 14573 |
| headlights | not_closed | ambig_target | 409 |
| headlights | not_closed | no_list_manifest | 8830 |
| headlights | not_closed | no_year_manifest | 30147 |
| headlights | not_closed | unattested | 216 |
| headlights | not_closed | uncrawled_chain_member | 181 |
| headlights | not_closed | variant_unread | 1475 |
| headlights | not_closed | year_manifest_bad | 2799 |
| hood | unmapped | - | 2243 |
| hood | no_records | - | 13006 |
| hood | not_closed | ambig_target | 298 |
| hood | not_closed | no_list_manifest | 95 |
| hood | not_closed | no_year_manifest | 31708 |
| hood | not_closed | unattested | 5718 |
| hood | not_closed | uncrawled_chain_member | 1214 |
| hood | not_closed | unverified_product | 2163 |
| hood | not_closed | variant_unread | 1778 |
| hood | not_closed | year_manifest_bad | 2650 |
| ignition-coils | unmapped | - | 2243 |
| ignition-coils | no_records | - | 11511 |
| ignition-coils | not_closed | ambig_target | 160 |
| ignition-coils | not_closed | no_list_manifest | 349 |
| ignition-coils | not_closed | no_year_manifest | 34011 |
| ignition-coils | not_closed | uncrawled_chain_member | 344 |
| ignition-coils | not_closed | unverified_product | 8751 |
| ignition-coils | not_closed | variant_unread | 1778 |
| ignition-coils | not_closed | year_manifest_bad | 1726 |
| liftgate | unmapped | - | 2243 |
| liftgate | no_records | - | 35805 |
| liftgate | not_closed | ambig_target | 143 |
| liftgate | not_closed | no_year_manifest | 9598 |
| liftgate | not_closed | unread_sibling_page | 9095 |
| liftgate | not_closed | variant_unread | 1778 |
| liftgate | not_closed | year_manifest_bad | 2211 |
| power-steering-pump | unmapped | - | 2243 |
| power-steering-pump | no_records | - | 32196 |
| power-steering-pump | not_closed | no_list_manifest | 5256 |
| power-steering-pump | not_closed | no_year_manifest | 19039 |
| power-steering-pump | not_closed | unread_sibling_page | 240 |
| power-steering-pump | not_closed | variant_unread | 355 |
| power-steering-pump | not_closed | year_manifest_bad | 1544 |
| radiator | unmapped | - | 2243 |
| radiator | no_records | - | 15117 |
| radiator | not_closed | ambig_target | 459 |
| radiator | not_closed | no_list_manifest | 264 |
| radiator | not_closed | no_year_manifest | 29312 |
| radiator | not_closed | unattested | 1523 |
| radiator | not_closed | uncrawled_chain_member | 5797 |
| radiator | not_closed | unverified_product | 1775 |
| radiator | not_closed | variant_unread | 1778 |
| radiator | not_closed | year_manifest_bad | 2605 |
| side-mirrors | unmapped | - | 2243 |
| side-mirrors | no_records | - | 7818 |
| side-mirrors | not_closed | ambig_target | 456 |
| side-mirrors | not_closed | no_list_manifest | 9095 |
| side-mirrors | not_closed | no_year_manifest | 36395 |
| side-mirrors | not_closed | unread_sibling_page | 397 |
| side-mirrors | not_closed | variant_unread | 1778 |
| side-mirrors | not_closed | year_manifest_bad | 2691 |
| starter | unmapped | - | 2243 |
| starter | no_records | - | 17899 |
| starter | not_closed | ambig_target | 17 |
| starter | not_closed | no_list_manifest | 9095 |
| starter | not_closed | no_year_manifest | 29289 |
| starter | not_closed | suspect_variant | 95 |
| starter | not_closed | unattested | 27 |
| starter | not_closed | uncrawled_chain_member | 30 |
| starter | not_closed | unverified_product | 204 |
| starter | not_closed | variant_unread | 1778 |
| starter | not_closed | year_manifest_bad | 196 |
| tail-lights | unmapped | - | 2243 |
| tail-lights | no_records | - | 12700 |
| tail-lights | not_closed | ambig_target | 459 |
| tail-lights | not_closed | no_list_manifest | 9095 |
| tail-lights | not_closed | no_year_manifest | 31867 |
| tail-lights | not_closed | unattested | 182 |
| tail-lights | not_closed | uncrawled_chain_member | 215 |
| tail-lights | not_closed | variant_unread | 1778 |
| tail-lights | not_closed | year_manifest_bad | 2334 |
| tailgate | unmapped | - | 2243 |
| tailgate | no_records | - | 37036 |
| tailgate | not_closed | ambig_target | 298 |
| tailgate | not_closed | no_year_manifest | 9247 |
| tailgate | not_closed | unattested | 8405 |
| tailgate | not_closed | uncrawled_chain_member | 690 |
| tailgate | not_closed | variant_unread | 1778 |
| tailgate | not_closed | year_manifest_bad | 1176 |
| throttle-body | unmapped | - | 2243 |
| throttle-body | no_records | - | 27179 |
| throttle-body | not_closed | no_list_manifest | 5048 |
| throttle-body | not_closed | no_year_manifest | 23061 |
| throttle-body | not_closed | unattested | 48 |
| throttle-body | not_closed | uncrawled_chain_member | 178 |
| throttle-body | not_closed | variant_unread | 1778 |
| throttle-body | not_closed | year_manifest_bad | 1338 |
| tow-mirrors | unmapped | - | 2243 |
| tow-mirrors | no_records | - | 52612 |
| tow-mirrors | not_closed | ambig_target | 219 |
| tow-mirrors | not_closed | no_list_manifest | 647 |
| tow-mirrors | not_closed | no_year_manifest | 4314 |
| tow-mirrors | not_closed | variant_unread | 838 |
| trunk-lid | unmapped | - | 2243 |
| trunk-lid | no_records | - | 35698 |
| trunk-lid | not_closed | no_list_manifest | 51 |
| trunk-lid | not_closed | no_year_manifest | 12304 |
| trunk-lid | not_closed | unattested | 5831 |
| trunk-lid | not_closed | uncrawled_chain_member | 2391 |
| trunk-lid | not_closed | variant_unread | 940 |
| trunk-lid | not_closed | year_manifest_bad | 1415 |
| window-regulator | unmapped | - | 2243 |
| window-regulator | no_records | - | 17123 |
| window-regulator | not_closed | ambig_target | 17 |
| window-regulator | not_closed | no_list_manifest | 9095 |
| window-regulator | not_closed | no_year_manifest | 29492 |
| window-regulator | not_closed | unread_sibling_page | 397 |
| window-regulator | not_closed | variant_unread | 1778 |
| window-regulator | not_closed | year_manifest_bad | 728 |
| window-switch | unmapped | - | 2243 |
| window-switch | no_records | - | 11445 |
| window-switch | not_closed | ambig_target | 154 |
| window-switch | not_closed | no_list_manifest | 9095 |
| window-switch | not_closed | no_year_manifest | 34415 |
| window-switch | not_closed | unattested | 226 |
| window-switch | not_closed | uncrawled_chain_member | 100 |
| window-switch | not_closed | unverified_product | 71 |
| window-switch | not_closed | variant_unread | 1778 |
| window-switch | not_closed | year_manifest_bad | 1346 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2243 |
| ac-compressor | no_records | - | 8844 |
| ac-compressor | split | no_candidates | 90 |
| ac-compressor | split | option_split | 33960 |
| ac-compressor | conditional | conditional:engine | 1159 |
| ac-compressor | conditional | conditional:engine_unattested | 13630 |
| ac-compressor | conditional | conditional:trim | 947 |
| alternator | unmapped | - | 2243 |
| alternator | no_records | - | 7218 |
| alternator | split | no_candidates | 75 |
| alternator | split | option_split | 43305 |
| alternator | conditional | conditional:engine | 270 |
| alternator | conditional | conditional:engine_unattested | 7274 |
| alternator | conditional | conditional:production | 44 |
| alternator | conditional | conditional:trim | 444 |
| bumper-front | unmapped | - | 2243 |
| bumper-front | no_records | - | 12031 |
| bumper-front | split | no_candidates | 127 |
| bumper-front | split | option_split | 42422 |
| bumper-front | conditional | conditional:engine_unattested | 4050 |
| bumper-rear | unmapped | - | 2243 |
| bumper-rear | no_records | - | 9846 |
| bumper-rear | split | no_candidates | 82 |
| bumper-rear | split | option_split | 44206 |
| bumper-rear | conditional | conditional:engine_unattested | 4496 |
| climate-control | unmapped | - | 2243 |
| climate-control | no_records | - | 22999 |
| climate-control | split | no_candidates | 129 |
| climate-control | split | option_split | 26279 |
| climate-control | conditional | conditional:colour | 222 |
| climate-control | conditional | conditional:engine_unattested | 8774 |
| climate-control | conditional | conditional:trim | 227 |
| door-front | unmapped | - | 2243 |
| door-front | no_records | - | 26016 |
| door-front | split | no_candidates | 2415 |
| door-front | split | option_split | 13429 |
| door-front | split | slot_missing | 2326 |
| door-front | conditional | conditional:body | 171 |
| door-front | conditional | conditional:engine_unattested | 8261 |
| door-front | conditional | conditional:qualifier | 4358 |
| door-front | conditional | conditional:trim | 1654 |
| door-rear | unmapped | - | 2243 |
| door-rear | no_records | - | 25199 |
| door-rear | split | no_candidates | 1338 |
| door-rear | split | option_split | 16177 |
| door-rear | split | slot_missing | 102 |
| door-rear | conditional | conditional:engine_unattested | 1166 |
| door-rear | conditional | conditional:qualifier | 13843 |
| door-rear | conditional | conditional:trim | 805 |
| fender | unmapped | - | 2243 |
| fender | no_records | - | 16041 |
| fender | split | no_candidates | 189 |
| fender | split | option_split | 23514 |
| fender | split | slot_missing | 595 |
| fender | conditional | conditional:engine_unattested | 13698 |
| fender | conditional | conditional:trim | 4593 |
| fuel-pump-module | unmapped | - | 2243 |
| fuel-pump-module | no_records | - | 24653 |
| fuel-pump-module | split | no_candidates | 27 |
| fuel-pump-module | split | option_split | 26818 |
| fuel-pump-module | conditional | conditional:engine | 27 |
| fuel-pump-module | conditional | conditional:engine_unattested | 5844 |
| fuel-pump-module | conditional | conditional:trim | 1261 |
| gauge-cluster | unmapped | - | 2243 |
| gauge-cluster | no_records | - | 31892 |
| gauge-cluster | split | no_candidates | 907 |
| gauge-cluster | split | option_split | 23964 |
| gauge-cluster | conditional | conditional:engine_unattested | 1561 |
| gauge-cluster | conditional | conditional:production | 197 |
| gauge-cluster | conditional | conditional:trim | 109 |
| grille | unmapped | - | 2243 |
| grille | no_records | - | 16977 |
| grille | split | no_candidates | 703 |
| grille | split | option_split | 39654 |
| grille | conditional | conditional:engine_unattested | 1175 |
| grille | conditional | conditional:option | 121 |
| headlights | unmapped | - | 2243 |
| headlights | no_records | - | 14573 |
| headlights | split | no_candidates | 23 |
| headlights | split | option_split | 34119 |
| headlights | split | slot_missing | 441 |
| headlights | conditional | conditional:engine_unattested | 7937 |
| headlights | conditional | conditional:option | 102 |
| headlights | conditional | conditional:package | 61 |
| headlights | conditional | conditional:production | 450 |
| headlights | conditional | conditional:trim | 924 |
| hood | unmapped | - | 2243 |
| hood | no_records | - | 13006 |
| hood | split | no_candidates | 274 |
| hood | split | option_split | 7514 |
| hood | conditional | conditional:engine_unattested | 28977 |
| hood | conditional | conditional:trim | 8859 |
| ignition-coils | unmapped | - | 2243 |
| ignition-coils | no_records | - | 11511 |
| ignition-coils | split | no_candidates | 143 |
| ignition-coils | split | option_split | 25535 |
| ignition-coils | conditional | conditional:engine_unattested | 18407 |
| ignition-coils | conditional | conditional:package | 2851 |
| ignition-coils | conditional | conditional:trim | 183 |
| liftgate | unmapped | - | 2243 |
| liftgate | no_records | - | 35805 |
| liftgate | split | no_candidates | 8375 |
| liftgate | split | option_split | 2718 |
| liftgate | conditional | conditional:engine_unattested | 8706 |
| liftgate | conditional | conditional:option | 1152 |
| liftgate | conditional | conditional:trim | 1874 |
| power-steering-pump | unmapped | - | 2243 |
| power-steering-pump | no_records | - | 32196 |
| power-steering-pump | split | no_candidates | 186 |
| power-steering-pump | split | option_split | 11953 |
| power-steering-pump | conditional | conditional:colour | 444 |
| power-steering-pump | conditional | conditional:engine | 304 |
| power-steering-pump | conditional | conditional:engine_unattested | 11887 |
| power-steering-pump | conditional | conditional:option | 160 |
| power-steering-pump | conditional | conditional:trim | 1500 |
| radiator | unmapped | - | 2243 |
| radiator | no_records | - | 15117 |
| radiator | split | no_candidates | 906 |
| radiator | split | option_split | 39189 |
| radiator | conditional | conditional:engine_unattested | 2803 |
| radiator | conditional | conditional:trim | 615 |
| side-mirrors | unmapped | - | 2243 |
| side-mirrors | no_records | - | 7818 |
| side-mirrors | split | no_candidates | 28 |
| side-mirrors | split | option_split | 45575 |
| side-mirrors | split | position_missing | 7 |
| side-mirrors | split | slot_missing | 2034 |
| side-mirrors | conditional | conditional:colour | 168 |
| side-mirrors | conditional | conditional:engine_unattested | 2424 |
| side-mirrors | conditional | conditional:option | 410 |
| side-mirrors | conditional | conditional:trim | 166 |
| starter | unmapped | - | 2243 |
| starter | no_records | - | 17899 |
| starter | split | no_candidates | 196 |
| starter | split | option_split | 34180 |
| starter | conditional | conditional:engine | 27 |
| starter | conditional | conditional:engine_unattested | 6166 |
| starter | conditional | conditional:option | 160 |
| starter | conditional | conditional:trim | 2 |
| tail-lights | unmapped | - | 2243 |
| tail-lights | no_records | - | 12700 |
| tail-lights | split | no_candidates | 49 |
| tail-lights | split | option_split | 38470 |
| tail-lights | split | slot_missing | 560 |
| tail-lights | conditional | conditional:colour | 54 |
| tail-lights | conditional | conditional:engine_unattested | 5595 |
| tail-lights | conditional | conditional:option | 2 |
| tail-lights | conditional | conditional:production | 128 |
| tail-lights | conditional | conditional:trim | 1072 |
| tailgate | unmapped | - | 2243 |
| tailgate | no_records | - | 37036 |
| tailgate | split | no_candidates | 9327 |
| tailgate | split | option_split | 9249 |
| tailgate | conditional | conditional:engine_unattested | 2553 |
| tailgate | conditional | conditional:trim | 465 |
| throttle-body | unmapped | - | 2243 |
| throttle-body | no_records | - | 27179 |
| throttle-body | split | no_candidates | 9 |
| throttle-body | split | option_split | 14515 |
| throttle-body | conditional | conditional:engine | 53 |
| throttle-body | conditional | conditional:engine_unattested | 14321 |
| throttle-body | conditional | conditional:option | 205 |
| throttle-body | conditional | conditional:trim | 2348 |
| tow-mirrors | unmapped | - | 2243 |
| tow-mirrors | no_records | - | 52612 |
| tow-mirrors | split | option_split | 2954 |
| tow-mirrors | split | position_conflict | 606 |
| tow-mirrors | split | slot_missing | 2367 |
| tow-mirrors | conditional | conditional:colour | 30 |
| tow-mirrors | conditional | conditional:engine_unattested | 61 |
| trunk-lid | unmapped | - | 2243 |
| trunk-lid | no_records | - | 35698 |
| trunk-lid | split | no_candidates | 5111 |
| trunk-lid | split | option_split | 14067 |
| trunk-lid | conditional | conditional:engine_unattested | 3522 |
| trunk-lid | conditional | conditional:trim | 232 |
| window-regulator | unmapped | - | 2243 |
| window-regulator | no_records | - | 17123 |
| window-regulator | split | no_candidates | 101 |
| window-regulator | split | packaging_incomplete | 3982 |
| window-regulator | split | packaging_split | 13916 |
| window-regulator | split | packaging_unstated | 22162 |
| window-regulator | split | position_missing | 738 |
| window-regulator | conditional | conditional:trim | 608 |
| window-switch | unmapped | - | 2243 |
| window-switch | no_records | - | 11445 |
| window-switch | split | no_candidates | 1394 |
| window-switch | split | option_split | 23460 |
| window-switch | split | position_missing | 16463 |
| window-switch | conditional | conditional:colour | 1337 |
| window-switch | conditional | conditional:engine_unattested | 3172 |
| window-switch | conditional | conditional:trim | 1359 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 804
- held_exterior_cross_model: 40
- recrawl_resolved: 2
- rule_drift: 47
- universal_part_suspect: 12

## Unknown note clauses (top 30)

- `Callout Name: 17682`: 971
- `Callout Name: 10849`: 734
- `(CP) Designates Crash Part - When Ordering Please Refer To Crash Part Truckload Program Guidelines`: 710
- `Base Number: 10849`: 701
- `Base Number: 17682`: 449
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
- `Callout Name: 9H307`: 171
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
- Ford GT: feed 'GT' 3 cars
- Ford Granada: feed 'Granada' 2 cars
- Ford Maverick: feed 'Maverick' 11 cars
- Ford Pinto: feed 'Pinto' 8 cars
- Ford Police Responder Hybrid: feed 'Police Responder Hybrid' 0 cars (excluded: catalog model with no feed cars as 'Police Responder Hybrid' (inventory 2026-11-04); nothing to map)
- Ford SSV Plug-In Hybrid: feed 'SSV Plug-In Hybrid' 0 cars (excluded: catalog model with no feed cars as 'SSV Plug-In Hybrid' (inventory 2026-11-04); nothing to map)
- Lincoln Mark VI: feed 'Mark VI' 4 cars
- Mercury Bobcat: feed 'Bobcat' 0 cars
- Mercury LN7: feed 'LN7' 0 cars
- Mercury Lynx: feed 'Lynx' 0 cars
- Mercury Marquis: feed 'Marquis' 30 cars
- Mercury Villager: feed 'Villager' 83 cars
- Mercury Zephyr: feed 'Zephyr' 3 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (3 cars, under catalog squash 'zephyr'); unmapped until a reviewed entry exists)
