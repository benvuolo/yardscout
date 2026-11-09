# OEM curation report: ford

Raw: `c36da2eb98835c02f81c05e8c36b6a926634a332` @ `c36da2eb9883`; as of 2026-11-07T00:35:31Z.

- records 7173, classes 7173, list rows 77788, year manifests 313, cells 11794
- Verified groups 0, engine vg groups 0, Likely groups 59
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.fordpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.fordpartsgiant.com: only 1% of its 14302 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2243 |
| ac-compressor | no_records | - | 8840 |
| ac-compressor | not_closed | ambig_target | 410 |
| ac-compressor | not_closed | no_list_manifest | 10580 |
| ac-compressor | not_closed | no_year_manifest | 33943 |
| ac-compressor | not_closed | unattested | 81 |
| ac-compressor | not_closed | uncrawled_chain_member | 59 |
| ac-compressor | not_closed | unverified_product | 257 |
| ac-compressor | not_closed | variant_unread | 1778 |
| ac-compressor | not_closed | year_manifest_bad | 2681 |
| alternator | unmapped | - | 2243 |
| alternator | no_records | - | 7217 |
| alternator | not_closed | no_list_manifest | 10580 |
| alternator | not_closed | no_year_manifest | 35936 |
| alternator | not_closed | suspect_variant | 51 |
| alternator | not_closed | uncrawled_chain_member | 127 |
| alternator | not_closed | unverified_product | 178 |
| alternator | not_closed | variant_unread | 1778 |
| alternator | not_closed | year_manifest_bad | 2762 |
| bumper-front | unmapped | - | 2243 |
| bumper-front | no_records | - | 7316 |
| bumper-front | not_closed | ambig_target | 358 |
| bumper-front | not_closed | no_list_manifest | 319 |
| bumper-front | not_closed | no_year_manifest | 34640 |
| bumper-front | not_closed | unread_sibling_page | 10658 |
| bumper-front | not_closed | variant_unread | 1778 |
| bumper-front | not_closed | year_manifest_bad | 3560 |
| bumper-rear | unmapped | - | 2243 |
| bumper-rear | no_records | - | 3853 |
| bumper-rear | not_closed | ambig_target | 519 |
| bumper-rear | not_closed | no_list_manifest | 319 |
| bumper-rear | not_closed | no_year_manifest | 37941 |
| bumper-rear | not_closed | unread_sibling_page | 10658 |
| bumper-rear | not_closed | variant_unread | 1778 |
| bumper-rear | not_closed | year_manifest_bad | 3561 |
| climate-control | unmapped | - | 2243 |
| climate-control | no_records | - | 22993 |
| climate-control | not_closed | ambig_target | 170 |
| climate-control | not_closed | no_list_manifest | 9376 |
| climate-control | not_closed | no_year_manifest | 22326 |
| climate-control | not_closed | unread_sibling_page | 397 |
| climate-control | not_closed | variant_unread | 1778 |
| climate-control | not_closed | year_manifest_bad | 1589 |
| door-front | unmapped | - | 2243 |
| door-front | no_records | - | 21437 |
| door-front | not_closed | ambig_target | 203 |
| door-front | not_closed | no_list_manifest | 319 |
| door-front | not_closed | no_year_manifest | 20821 |
| door-front | not_closed | unread_sibling_page | 10658 |
| door-front | not_closed | variant_unread | 1778 |
| door-front | not_closed | year_manifest_bad | 3413 |
| door-rear | unmapped | - | 2243 |
| door-rear | no_records | - | 20956 |
| door-rear | not_closed | ambig_target | 203 |
| door-rear | not_closed | no_list_manifest | 248 |
| door-rear | not_closed | no_year_manifest | 22887 |
| door-rear | not_closed | unread_sibling_page | 10156 |
| door-rear | not_closed | variant_unread | 1778 |
| door-rear | not_closed | year_manifest_bad | 2401 |
| fender | unmapped | - | 2243 |
| fender | no_records | - | 10364 |
| fender | not_closed | ambig_target | 408 |
| fender | not_closed | no_list_manifest | 292 |
| fender | not_closed | no_year_manifest | 31598 |
| fender | not_closed | unattested | 4952 |
| fender | not_closed | uncrawled_chain_member | 2257 |
| fender | not_closed | unverified_product | 3449 |
| fender | not_closed | variant_unread | 1778 |
| fender | not_closed | year_manifest_bad | 3531 |
| fuel-pump-module | unmapped | - | 2243 |
| fuel-pump-module | no_records | - | 24649 |
| fuel-pump-module | not_closed | ambig_target | 92 |
| fuel-pump-module | not_closed | no_list_manifest | 9953 |
| fuel-pump-module | not_closed | no_year_manifest | 21032 |
| fuel-pump-module | not_closed | unread_sibling_page | 397 |
| fuel-pump-module | not_closed | variant_unread | 1778 |
| fuel-pump-module | not_closed | year_manifest_bad | 728 |
| gauge-cluster | unmapped | - | 2243 |
| gauge-cluster | no_records | - | 26999 |
| gauge-cluster | not_closed | ambig_target | 319 |
| gauge-cluster | not_closed | no_list_manifest | 275 |
| gauge-cluster | not_closed | no_year_manifest | 15029 |
| gauge-cluster | not_closed | unread_sibling_page | 10658 |
| gauge-cluster | not_closed | variant_unread | 1778 |
| gauge-cluster | not_closed | year_manifest_bad | 3571 |
| grille | unmapped | - | 2243 |
| grille | no_records | - | 11438 |
| grille | not_closed | ambig_target | 358 |
| grille | not_closed | no_list_manifest | 234 |
| grille | not_closed | no_year_manifest | 30586 |
| grille | not_closed | unattested | 7170 |
| grille | not_closed | uncrawled_chain_member | 936 |
| grille | not_closed | unverified_product | 2552 |
| grille | not_closed | variant_unread | 1778 |
| grille | not_closed | year_manifest_bad | 3577 |
| headlights | unmapped | - | 2243 |
| headlights | no_records | - | 14568 |
| headlights | not_closed | ambig_target | 409 |
| headlights | not_closed | no_list_manifest | 10204 |
| headlights | not_closed | no_year_manifest | 28047 |
| headlights | not_closed | unattested | 216 |
| headlights | not_closed | uncrawled_chain_member | 181 |
| headlights | not_closed | variant_unread | 1475 |
| headlights | not_closed | year_manifest_bad | 3529 |
| hood | unmapped | - | 2243 |
| hood | no_records | - | 6356 |
| hood | not_closed | ambig_target | 358 |
| hood | not_closed | no_list_manifest | 319 |
| hood | not_closed | no_year_manifest | 35627 |
| hood | not_closed | unattested | 7521 |
| hood | not_closed | uncrawled_chain_member | 744 |
| hood | not_closed | unverified_product | 2393 |
| hood | not_closed | variant_unread | 1778 |
| hood | not_closed | year_manifest_bad | 3533 |
| ignition-coils | unmapped | - | 2243 |
| ignition-coils | no_records | - | 8841 |
| ignition-coils | not_closed | ambig_target | 220 |
| ignition-coils | not_closed | no_list_manifest | 319 |
| ignition-coils | not_closed | no_year_manifest | 34624 |
| ignition-coils | not_closed | uncrawled_chain_member | 469 |
| ignition-coils | not_closed | unverified_product | 10189 |
| ignition-coils | not_closed | variant_unread | 1778 |
| ignition-coils | not_closed | year_manifest_bad | 2189 |
| liftgate | unmapped | - | 2243 |
| liftgate | no_records | - | 32400 |
| liftgate | not_closed | ambig_target | 203 |
| liftgate | not_closed | no_list_manifest | 168 |
| liftgate | not_closed | no_year_manifest | 10623 |
| liftgate | not_closed | unread_sibling_page | 10628 |
| liftgate | not_closed | variant_unread | 1778 |
| liftgate | not_closed | year_manifest_bad | 2829 |
| power-steering-pump | unmapped | - | 2243 |
| power-steering-pump | no_records | - | 32195 |
| power-steering-pump | not_closed | no_list_manifest | 6349 |
| power-steering-pump | not_closed | no_year_manifest | 17514 |
| power-steering-pump | not_closed | unread_sibling_page | 240 |
| power-steering-pump | not_closed | variant_unread | 355 |
| power-steering-pump | not_closed | year_manifest_bad | 1976 |
| radiator | unmapped | - | 2243 |
| radiator | no_records | - | 12378 |
| radiator | not_closed | ambig_target | 519 |
| radiator | not_closed | no_list_manifest | 319 |
| radiator | not_closed | no_year_manifest | 29565 |
| radiator | not_closed | unattested | 1718 |
| radiator | not_closed | uncrawled_chain_member | 6977 |
| radiator | not_closed | unverified_product | 1963 |
| radiator | not_closed | variant_unread | 1778 |
| radiator | not_closed | year_manifest_bad | 3412 |
| side-mirrors | unmapped | - | 2243 |
| side-mirrors | no_records | - | 7817 |
| side-mirrors | not_closed | ambig_target | 456 |
| side-mirrors | not_closed | no_list_manifest | 10580 |
| side-mirrors | not_closed | no_year_manifest | 34138 |
| side-mirrors | not_closed | unread_sibling_page | 397 |
| side-mirrors | not_closed | variant_unread | 1778 |
| side-mirrors | not_closed | year_manifest_bad | 3463 |
| starter | unmapped | - | 2243 |
| starter | no_records | - | 17898 |
| starter | not_closed | ambig_target | 17 |
| starter | not_closed | no_list_manifest | 10580 |
| starter | not_closed | no_year_manifest | 27804 |
| starter | not_closed | suspect_variant | 95 |
| starter | not_closed | unattested | 27 |
| starter | not_closed | uncrawled_chain_member | 30 |
| starter | not_closed | unverified_product | 204 |
| starter | not_closed | variant_unread | 1778 |
| starter | not_closed | year_manifest_bad | 196 |
| tail-lights | unmapped | - | 2243 |
| tail-lights | no_records | - | 12695 |
| tail-lights | not_closed | ambig_target | 459 |
| tail-lights | not_closed | no_list_manifest | 10503 |
| tail-lights | not_closed | no_year_manifest | 29978 |
| tail-lights | not_closed | unattested | 182 |
| tail-lights | not_closed | uncrawled_chain_member | 215 |
| tail-lights | not_closed | variant_unread | 1778 |
| tail-lights | not_closed | year_manifest_bad | 2819 |
| tailgate | unmapped | - | 2243 |
| tailgate | no_records | - | 35179 |
| tailgate | not_closed | ambig_target | 358 |
| tailgate | not_closed | no_year_manifest | 9296 |
| tailgate | not_closed | unattested | 9938 |
| tailgate | not_closed | uncrawled_chain_member | 690 |
| tailgate | not_closed | unread_sibling_page | 30 |
| tailgate | not_closed | variant_unread | 1778 |
| tailgate | not_closed | year_manifest_bad | 1360 |
| throttle-body | unmapped | - | 2243 |
| throttle-body | no_records | - | 27177 |
| throttle-body | not_closed | no_list_manifest | 6208 |
| throttle-body | not_closed | no_year_manifest | 21832 |
| throttle-body | not_closed | unattested | 48 |
| throttle-body | not_closed | uncrawled_chain_member | 178 |
| throttle-body | not_closed | variant_unread | 1778 |
| throttle-body | not_closed | year_manifest_bad | 1408 |
| tow-mirrors | unmapped | - | 2243 |
| tow-mirrors | no_records | - | 52611 |
| tow-mirrors | not_closed | ambig_target | 219 |
| tow-mirrors | not_closed | no_list_manifest | 647 |
| tow-mirrors | not_closed | no_year_manifest | 4244 |
| tow-mirrors | not_closed | variant_unread | 838 |
| tow-mirrors | not_closed | year_manifest_bad | 70 |
| trunk-lid | unmapped | - | 2243 |
| trunk-lid | no_records | - | 33373 |
| trunk-lid | not_closed | no_list_manifest | 151 |
| trunk-lid | not_closed | no_year_manifest | 12576 |
| trunk-lid | not_closed | unattested | 7374 |
| trunk-lid | not_closed | uncrawled_chain_member | 2260 |
| trunk-lid | not_closed | unverified_product | 42 |
| trunk-lid | not_closed | variant_unread | 940 |
| trunk-lid | not_closed | year_manifest_bad | 1913 |
| window-regulator | unmapped | - | 2243 |
| window-regulator | no_records | - | 17121 |
| window-regulator | not_closed | ambig_target | 17 |
| window-regulator | not_closed | no_list_manifest | 10580 |
| window-regulator | not_closed | no_year_manifest | 27774 |
| window-regulator | not_closed | unread_sibling_page | 397 |
| window-regulator | not_closed | variant_unread | 1778 |
| window-regulator | not_closed | year_manifest_bad | 962 |
| window-switch | unmapped | - | 2243 |
| window-switch | no_records | - | 11442 |
| window-switch | not_closed | ambig_target | 154 |
| window-switch | not_closed | no_list_manifest | 10580 |
| window-switch | not_closed | no_year_manifest | 32311 |
| window-switch | not_closed | unattested | 226 |
| window-switch | not_closed | uncrawled_chain_member | 100 |
| window-switch | not_closed | unverified_product | 71 |
| window-switch | not_closed | variant_unread | 1778 |
| window-switch | not_closed | year_manifest_bad | 1967 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2243 |
| ac-compressor | no_records | - | 8840 |
| ac-compressor | split | no_candidates | 90 |
| ac-compressor | split | option_split | 33962 |
| ac-compressor | conditional | conditional:engine | 1159 |
| ac-compressor | conditional | conditional:engine_unattested | 13630 |
| ac-compressor | conditional | conditional:trim | 948 |
| alternator | unmapped | - | 2243 |
| alternator | no_records | - | 7217 |
| alternator | split | no_candidates | 75 |
| alternator | split | option_split | 43309 |
| alternator | conditional | conditional:engine | 270 |
| alternator | conditional | conditional:engine_unattested | 7270 |
| alternator | conditional | conditional:production | 44 |
| alternator | conditional | conditional:trim | 444 |
| bumper-front | unmapped | - | 2243 |
| bumper-front | no_records | - | 7316 |
| bumper-front | split | no_candidates | 347 |
| bumper-front | split | option_split | 47392 |
| bumper-front | conditional | conditional:engine_unattested | 3340 |
| bumper-front | conditional | conditional:production | 14 |
| bumper-front | conditional | conditional:trim | 220 |
| bumper-rear | unmapped | - | 2243 |
| bumper-rear | no_records | - | 3853 |
| bumper-rear | split | no_candidates | 276 |
| bumper-rear | split | option_split | 50808 |
| bumper-rear | conditional | conditional:engine_unattested | 3619 |
| bumper-rear | conditional | conditional:option | 16 |
| bumper-rear | conditional | conditional:trim | 57 |
| climate-control | unmapped | - | 2243 |
| climate-control | no_records | - | 22993 |
| climate-control | split | no_candidates | 129 |
| climate-control | split | option_split | 26284 |
| climate-control | conditional | conditional:colour | 222 |
| climate-control | conditional | conditional:engine_unattested | 8774 |
| climate-control | conditional | conditional:trim | 227 |
| door-front | unmapped | - | 2243 |
| door-front | no_records | - | 21437 |
| door-front | split | no_candidates | 3205 |
| door-front | split | option_split | 15770 |
| door-front | split | slot_missing | 924 |
| door-front | conditional | conditional:body | 261 |
| door-front | conditional | conditional:engine_unattested | 10149 |
| door-front | conditional | conditional:qualifier | 4359 |
| door-front | conditional | conditional:trim | 2524 |
| door-rear | unmapped | - | 2243 |
| door-rear | no_records | - | 20956 |
| door-rear | split | no_candidates | 1856 |
| door-rear | split | option_split | 16421 |
| door-rear | split | slot_missing | 102 |
| door-rear | conditional | conditional:engine_unattested | 1214 |
| door-rear | conditional | conditional:qualifier | 17235 |
| door-rear | conditional | conditional:trim | 845 |
| fender | unmapped | - | 2243 |
| fender | no_records | - | 10364 |
| fender | split | no_candidates | 393 |
| fender | split | option_split | 24722 |
| fender | split | slot_missing | 949 |
| fender | conditional | conditional:body | 71 |
| fender | conditional | conditional:engine_unattested | 16574 |
| fender | conditional | conditional:trim | 5556 |
| fuel-pump-module | unmapped | - | 2243 |
| fuel-pump-module | no_records | - | 24649 |
| fuel-pump-module | split | no_candidates | 27 |
| fuel-pump-module | split | option_split | 26820 |
| fuel-pump-module | conditional | conditional:engine | 27 |
| fuel-pump-module | conditional | conditional:engine_unattested | 5844 |
| fuel-pump-module | conditional | conditional:trim | 1262 |
| gauge-cluster | unmapped | - | 2243 |
| gauge-cluster | no_records | - | 26999 |
| gauge-cluster | split | no_candidates | 1314 |
| gauge-cluster | split | option_split | 27645 |
| gauge-cluster | conditional | conditional:engine_unattested | 2226 |
| gauge-cluster | conditional | conditional:production | 197 |
| gauge-cluster | conditional | conditional:trim | 248 |
| grille | unmapped | - | 2243 |
| grille | no_records | - | 11438 |
| grille | split | no_candidates | 903 |
| grille | split | option_split | 42732 |
| grille | conditional | conditional:colour | 24 |
| grille | conditional | conditional:engine_unattested | 2519 |
| grille | conditional | conditional:option | 498 |
| grille | conditional | conditional:production | 44 |
| grille | conditional | conditional:trim | 471 |
| headlights | unmapped | - | 2243 |
| headlights | no_records | - | 14568 |
| headlights | split | no_candidates | 23 |
| headlights | split | option_split | 34123 |
| headlights | split | slot_missing | 441 |
| headlights | conditional | conditional:engine_unattested | 7937 |
| headlights | conditional | conditional:option | 102 |
| headlights | conditional | conditional:package | 61 |
| headlights | conditional | conditional:production | 450 |
| headlights | conditional | conditional:trim | 924 |
| hood | unmapped | - | 2243 |
| hood | no_records | - | 6356 |
| hood | split | no_candidates | 470 |
| hood | split | option_split | 7998 |
| hood | conditional | conditional:engine_unattested | 33651 |
| hood | conditional | conditional:production | 58 |
| hood | conditional | conditional:trim | 10096 |
| ignition-coils | unmapped | - | 2243 |
| ignition-coils | no_records | - | 8841 |
| ignition-coils | split | no_candidates | 156 |
| ignition-coils | split | option_split | 29226 |
| ignition-coils | conditional | conditional:engine_unattested | 16754 |
| ignition-coils | conditional | conditional:package | 3469 |
| ignition-coils | conditional | conditional:trim | 183 |
| liftgate | unmapped | - | 2243 |
| liftgate | no_records | - | 32400 |
| liftgate | split | no_candidates | 9832 |
| liftgate | split | option_split | 3592 |
| liftgate | conditional | conditional:engine_unattested | 9297 |
| liftgate | conditional | conditional:option | 1280 |
| liftgate | conditional | conditional:production | 14 |
| liftgate | conditional | conditional:trim | 2214 |
| power-steering-pump | unmapped | - | 2243 |
| power-steering-pump | no_records | - | 32195 |
| power-steering-pump | split | no_candidates | 186 |
| power-steering-pump | split | option_split | 11955 |
| power-steering-pump | conditional | conditional:colour | 444 |
| power-steering-pump | conditional | conditional:engine | 304 |
| power-steering-pump | conditional | conditional:engine_unattested | 11884 |
| power-steering-pump | conditional | conditional:option | 160 |
| power-steering-pump | conditional | conditional:trim | 1501 |
| radiator | unmapped | - | 2243 |
| radiator | no_records | - | 12378 |
| radiator | split | no_candidates | 1360 |
| radiator | split | option_split | 41339 |
| radiator | conditional | conditional:engine_unattested | 2669 |
| radiator | conditional | conditional:trim | 883 |
| side-mirrors | unmapped | - | 2243 |
| side-mirrors | no_records | - | 7817 |
| side-mirrors | split | no_candidates | 28 |
| side-mirrors | split | option_split | 45577 |
| side-mirrors | split | position_missing | 7 |
| side-mirrors | split | slot_missing | 2033 |
| side-mirrors | conditional | conditional:colour | 168 |
| side-mirrors | conditional | conditional:engine_unattested | 2423 |
| side-mirrors | conditional | conditional:option | 410 |
| side-mirrors | conditional | conditional:trim | 166 |
| starter | unmapped | - | 2243 |
| starter | no_records | - | 17898 |
| starter | split | no_candidates | 196 |
| starter | split | option_split | 34181 |
| starter | conditional | conditional:engine | 27 |
| starter | conditional | conditional:engine_unattested | 6165 |
| starter | conditional | conditional:option | 160 |
| starter | conditional | conditional:trim | 2 |
| tail-lights | unmapped | - | 2243 |
| tail-lights | no_records | - | 12695 |
| tail-lights | split | no_candidates | 49 |
| tail-lights | split | option_split | 38474 |
| tail-lights | split | slot_missing | 560 |
| tail-lights | conditional | conditional:colour | 54 |
| tail-lights | conditional | conditional:engine_unattested | 5595 |
| tail-lights | conditional | conditional:option | 2 |
| tail-lights | conditional | conditional:production | 128 |
| tail-lights | conditional | conditional:trim | 1072 |
| tailgate | unmapped | - | 2243 |
| tailgate | no_records | - | 35179 |
| tailgate | split | no_candidates | 10973 |
| tailgate | split | option_split | 9413 |
| tailgate | conditional | conditional:engine_unattested | 2471 |
| tailgate | conditional | conditional:trim | 593 |
| throttle-body | unmapped | - | 2243 |
| throttle-body | no_records | - | 27177 |
| throttle-body | split | no_candidates | 9 |
| throttle-body | split | option_split | 14517 |
| throttle-body | conditional | conditional:engine | 53 |
| throttle-body | conditional | conditional:engine_unattested | 14318 |
| throttle-body | conditional | conditional:option | 205 |
| throttle-body | conditional | conditional:trim | 2350 |
| tow-mirrors | unmapped | - | 2243 |
| tow-mirrors | no_records | - | 52611 |
| tow-mirrors | split | option_split | 2954 |
| tow-mirrors | split | position_conflict | 606 |
| tow-mirrors | split | slot_missing | 2367 |
| tow-mirrors | conditional | conditional:colour | 30 |
| tow-mirrors | conditional | conditional:engine_unattested | 61 |
| trunk-lid | unmapped | - | 2243 |
| trunk-lid | no_records | - | 33373 |
| trunk-lid | split | no_candidates | 6096 |
| trunk-lid | split | option_split | 14881 |
| trunk-lid | conditional | conditional:engine_unattested | 3806 |
| trunk-lid | conditional | conditional:option | 41 |
| trunk-lid | conditional | conditional:qualifier | 41 |
| trunk-lid | conditional | conditional:trim | 391 |
| window-regulator | unmapped | - | 2243 |
| window-regulator | no_records | - | 17121 |
| window-regulator | split | no_candidates | 101 |
| window-regulator | split | packaging_incomplete | 3983 |
| window-regulator | split | packaging_split | 13914 |
| window-regulator | split | packaging_unstated | 22164 |
| window-regulator | split | position_missing | 738 |
| window-regulator | conditional | conditional:trim | 608 |
| window-switch | unmapped | - | 2243 |
| window-switch | no_records | - | 11442 |
| window-switch | split | no_candidates | 1394 |
| window-switch | split | option_split | 23464 |
| window-switch | split | position_missing | 16460 |
| window-switch | conditional | conditional:colour | 1337 |
| window-switch | conditional | conditional:engine_unattested | 3172 |
| window-switch | conditional | conditional:trim | 1360 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 1072
- held_exterior_cross_model: 80
- recrawl_resolved: 2
- rule_drift: 68
- universal_part_suspect: 13

## Unknown note clauses (top 30)

- `Callout Name: 10849`: 1489
- `Base Number: 10849`: 1305
- `Callout Name: 17682`: 937
- `(CP) Designates Crash Part - When Ordering Please Refer To Crash Part Truckload Program Guidelines`: 888
- `Callout Name: 8200`: 685
- `Order From Instrument Cluster Online Ordering System Using The Online 1878 Form`: 603
- `Paint to match`: 598
- `For Instrument Cluster QC Issues Contact fesg@ford.com`: 578
- `With MPH/KMH Speedometer`: 548
- `With KMH/MPH Speedometer`: 531
- `Base Number: 17682`: 439
- `Callout Name: 13008`: 432
- `Export Dealers And Affiliates: Order Direct From FCSD-IDO`: 420
- `Order From Instrument Cluster Online Ordering System Using The Online Ordering System`: 405
- `Callout Name: 13404`: 329
- `Callout Name: 16005`: 328
- `Base Number: 8200`: 318
- `Fit Note: Ford Division Derivative`: 315
- `Callout Name: 19980`: 312
- `Callout Name: 17906`: 310
- `Callout Name: 17D957`: 289
- `Callout Name: 8005`: 282
- `Callout Name: 17757`: 281
- `Callout Name: 17K835`: 245
- `Callout Name: 10346`: 232
- `XLT`: 225
- `Base Number: 16005`: 213
- `Base Number: 13008`: 207
- `Callout Name: <20124`: 190
- `6 Cyl 3.0L OHC Duratec`: 182

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
