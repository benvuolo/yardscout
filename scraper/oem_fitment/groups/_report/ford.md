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
| ac-compressor | unmapped | - | 2251 |
| ac-compressor | no_records | - | 8795 |
| ac-compressor | not_closed | ambig_target | 403 |
| ac-compressor | not_closed | no_list_manifest | 9068 |
| ac-compressor | not_closed | no_year_manifest | 35608 |
| ac-compressor | not_closed | unattested | 82 |
| ac-compressor | not_closed | uncrawled_chain_member | 60 |
| ac-compressor | not_closed | unverified_product | 257 |
| ac-compressor | not_closed | variant_unread | 1761 |
| ac-compressor | not_closed | year_manifest_bad | 2185 |
| alternator | unmapped | - | 2251 |
| alternator | no_records | - | 7161 |
| alternator | not_closed | no_list_manifest | 9068 |
| alternator | not_closed | no_year_manifest | 37430 |
| alternator | not_closed | suspect_variant | 52 |
| alternator | not_closed | uncrawled_chain_member | 132 |
| alternator | not_closed | unverified_product | 177 |
| alternator | not_closed | variant_unread | 1761 |
| alternator | not_closed | year_manifest_bad | 2438 |
| bumper-front | unmapped | - | 2251 |
| bumper-front | no_records | - | 11911 |
| bumper-front | not_closed | ambig_target | 291 |
| bumper-front | not_closed | no_list_manifest | 151 |
| bumper-front | not_closed | no_year_manifest | 32434 |
| bumper-front | not_closed | unread_sibling_page | 9068 |
| bumper-front | not_closed | variant_unread | 1761 |
| bumper-front | not_closed | year_manifest_bad | 2603 |
| bumper-rear | unmapped | - | 2251 |
| bumper-rear | no_records | - | 9743 |
| bumper-rear | not_closed | ambig_target | 408 |
| bumper-rear | not_closed | no_list_manifest | 173 |
| bumper-rear | not_closed | no_year_manifest | 34429 |
| bumper-rear | not_closed | unread_sibling_page | 9068 |
| bumper-rear | not_closed | variant_unread | 1761 |
| bumper-rear | not_closed | year_manifest_bad | 2637 |
| climate-control | unmapped | - | 2251 |
| climate-control | no_records | - | 22838 |
| climate-control | not_closed | ambig_target | 165 |
| climate-control | not_closed | no_list_manifest | 8154 |
| climate-control | not_closed | no_year_manifest | 23610 |
| climate-control | not_closed | unread_sibling_page | 399 |
| climate-control | not_closed | variant_unread | 1761 |
| climate-control | not_closed | year_manifest_bad | 1292 |
| door-front | unmapped | - | 2251 |
| door-front | no_records | - | 25807 |
| door-front | not_closed | ambig_target | 139 |
| door-front | not_closed | no_list_manifest | 112 |
| door-front | not_closed | no_year_manifest | 18715 |
| door-front | not_closed | unread_sibling_page | 9068 |
| door-front | not_closed | variant_unread | 1761 |
| door-front | not_closed | year_manifest_bad | 2617 |
| door-rear | unmapped | - | 2251 |
| door-rear | no_records | - | 25021 |
| door-rear | not_closed | ambig_target | 139 |
| door-rear | not_closed | no_list_manifest | 52 |
| door-rear | not_closed | no_year_manifest | 20684 |
| door-rear | not_closed | unread_sibling_page | 8805 |
| door-rear | not_closed | variant_unread | 1761 |
| door-rear | not_closed | year_manifest_bad | 1757 |
| fender | unmapped | - | 2251 |
| fender | no_records | - | 15870 |
| fender | not_closed | ambig_target | 291 |
| fender | not_closed | no_list_manifest | 96 |
| fender | not_closed | no_year_manifest | 28451 |
| fender | not_closed | unattested | 3864 |
| fender | not_closed | uncrawled_chain_member | 1999 |
| fender | not_closed | unverified_product | 3205 |
| fender | not_closed | variant_unread | 1761 |
| fender | not_closed | year_manifest_bad | 2682 |
| fuel-pump-module | unmapped | - | 2251 |
| fuel-pump-module | no_records | - | 24489 |
| fuel-pump-module | not_closed | ambig_target | 89 |
| fuel-pump-module | not_closed | no_list_manifest | 8442 |
| fuel-pump-module | not_closed | no_year_manifest | 22431 |
| fuel-pump-module | not_closed | unread_sibling_page | 399 |
| fuel-pump-module | not_closed | variant_unread | 1761 |
| fuel-pump-module | not_closed | year_manifest_bad | 608 |
| gauge-cluster | unmapped | - | 2251 |
| gauge-cluster | no_records | - | 31635 |
| gauge-cluster | not_closed | ambig_target | 251 |
| gauge-cluster | not_closed | no_list_manifest | 52 |
| gauge-cluster | not_closed | no_year_manifest | 12795 |
| gauge-cluster | not_closed | unread_sibling_page | 9068 |
| gauge-cluster | not_closed | variant_unread | 1761 |
| gauge-cluster | not_closed | year_manifest_bad | 2657 |
| grille | unmapped | - | 2251 |
| grille | no_records | - | 16769 |
| grille | not_closed | ambig_target | 291 |
| grille | not_closed | no_list_manifest | 52 |
| grille | not_closed | no_year_manifest | 27661 |
| grille | not_closed | unattested | 6097 |
| grille | not_closed | uncrawled_chain_member | 749 |
| grille | not_closed | unverified_product | 2222 |
| grille | not_closed | variant_unread | 1761 |
| grille | not_closed | year_manifest_bad | 2617 |
| headlights | unmapped | - | 2251 |
| headlights | no_records | - | 14459 |
| headlights | not_closed | ambig_target | 403 |
| headlights | not_closed | no_list_manifest | 8805 |
| headlights | not_closed | no_year_manifest | 29903 |
| headlights | not_closed | unattested | 212 |
| headlights | not_closed | uncrawled_chain_member | 187 |
| headlights | not_closed | variant_unread | 1460 |
| headlights | not_closed | year_manifest_bad | 2790 |
| hood | unmapped | - | 2251 |
| hood | no_records | - | 12830 |
| hood | not_closed | ambig_target | 291 |
| hood | not_closed | no_list_manifest | 96 |
| hood | not_closed | no_year_manifest | 31531 |
| hood | not_closed | unattested | 5712 |
| hood | not_closed | uncrawled_chain_member | 1207 |
| hood | not_closed | unverified_product | 2149 |
| hood | not_closed | variant_unread | 1761 |
| hood | not_closed | year_manifest_bad | 2642 |
| ignition-coils | unmapped | - | 2251 |
| ignition-coils | no_records | - | 11420 |
| ignition-coils | not_closed | ambig_target | 156 |
| ignition-coils | not_closed | no_list_manifest | 354 |
| ignition-coils | not_closed | no_year_manifest | 33742 |
| ignition-coils | not_closed | uncrawled_chain_member | 339 |
| ignition-coils | not_closed | unverified_product | 8729 |
| ignition-coils | not_closed | variant_unread | 1761 |
| ignition-coils | not_closed | year_manifest_bad | 1718 |
| liftgate | unmapped | - | 2251 |
| liftgate | no_records | - | 35527 |
| liftgate | not_closed | ambig_target | 139 |
| liftgate | not_closed | no_year_manifest | 9514 |
| liftgate | not_closed | unread_sibling_page | 9068 |
| liftgate | not_closed | variant_unread | 1761 |
| liftgate | not_closed | year_manifest_bad | 2210 |
| power-steering-pump | unmapped | - | 2251 |
| power-steering-pump | no_records | - | 32027 |
| power-steering-pump | not_closed | no_list_manifest | 5249 |
| power-steering-pump | not_closed | no_year_manifest | 18816 |
| power-steering-pump | not_closed | unread_sibling_page | 243 |
| power-steering-pump | not_closed | variant_unread | 351 |
| power-steering-pump | not_closed | year_manifest_bad | 1533 |
| radiator | unmapped | - | 2251 |
| radiator | no_records | - | 15020 |
| radiator | not_closed | ambig_target | 452 |
| radiator | not_closed | no_list_manifest | 269 |
| radiator | not_closed | no_year_manifest | 29052 |
| radiator | not_closed | unattested | 1520 |
| radiator | not_closed | uncrawled_chain_member | 5782 |
| radiator | not_closed | unverified_product | 1766 |
| radiator | not_closed | variant_unread | 1761 |
| radiator | not_closed | year_manifest_bad | 2597 |
| side-mirrors | unmapped | - | 2251 |
| side-mirrors | no_records | - | 7754 |
| side-mirrors | not_closed | ambig_target | 449 |
| side-mirrors | not_closed | no_list_manifest | 9068 |
| side-mirrors | not_closed | no_year_manifest | 36102 |
| side-mirrors | not_closed | unread_sibling_page | 399 |
| side-mirrors | not_closed | variant_unread | 1761 |
| side-mirrors | not_closed | year_manifest_bad | 2686 |
| starter | unmapped | - | 2251 |
| starter | no_records | - | 17767 |
| starter | not_closed | ambig_target | 17 |
| starter | not_closed | no_list_manifest | 9068 |
| starter | not_closed | no_year_manifest | 29051 |
| starter | not_closed | suspect_variant | 96 |
| starter | not_closed | unattested | 28 |
| starter | not_closed | uncrawled_chain_member | 30 |
| starter | not_closed | unverified_product | 207 |
| starter | not_closed | variant_unread | 1761 |
| starter | not_closed | year_manifest_bad | 194 |
| tail-lights | unmapped | - | 2251 |
| tail-lights | no_records | - | 12601 |
| tail-lights | not_closed | ambig_target | 452 |
| tail-lights | not_closed | no_list_manifest | 9068 |
| tail-lights | not_closed | no_year_manifest | 31615 |
| tail-lights | not_closed | unattested | 184 |
| tail-lights | not_closed | uncrawled_chain_member | 215 |
| tail-lights | not_closed | variant_unread | 1761 |
| tail-lights | not_closed | year_manifest_bad | 2323 |
| tailgate | unmapped | - | 2251 |
| tailgate | no_records | - | 36688 |
| tailgate | not_closed | ambig_target | 291 |
| tailgate | not_closed | no_year_manifest | 9235 |
| tailgate | not_closed | unattested | 8378 |
| tailgate | not_closed | uncrawled_chain_member | 690 |
| tailgate | not_closed | variant_unread | 1761 |
| tailgate | not_closed | year_manifest_bad | 1176 |
| throttle-body | unmapped | - | 2251 |
| throttle-body | no_records | - | 26994 |
| throttle-body | not_closed | no_list_manifest | 5052 |
| throttle-body | not_closed | no_year_manifest | 22848 |
| throttle-body | not_closed | unattested | 45 |
| throttle-body | not_closed | uncrawled_chain_member | 181 |
| throttle-body | not_closed | variant_unread | 1761 |
| throttle-body | not_closed | year_manifest_bad | 1338 |
| tow-mirrors | unmapped | - | 2251 |
| tow-mirrors | no_records | - | 52223 |
| tow-mirrors | not_closed | ambig_target | 217 |
| tow-mirrors | not_closed | no_list_manifest | 648 |
| tow-mirrors | not_closed | no_year_manifest | 4298 |
| tow-mirrors | not_closed | variant_unread | 833 |
| trunk-lid | unmapped | - | 2251 |
| trunk-lid | no_records | - | 35428 |
| trunk-lid | not_closed | no_list_manifest | 52 |
| trunk-lid | not_closed | no_year_manifest | 12211 |
| trunk-lid | not_closed | unattested | 5807 |
| trunk-lid | not_closed | uncrawled_chain_member | 2389 |
| trunk-lid | not_closed | variant_unread | 928 |
| trunk-lid | not_closed | year_manifest_bad | 1404 |
| window-regulator | unmapped | - | 2251 |
| window-regulator | no_records | - | 17046 |
| window-regulator | not_closed | ambig_target | 17 |
| window-regulator | not_closed | no_list_manifest | 9068 |
| window-regulator | not_closed | no_year_manifest | 29208 |
| window-regulator | not_closed | unread_sibling_page | 399 |
| window-regulator | not_closed | variant_unread | 1761 |
| window-regulator | not_closed | year_manifest_bad | 720 |
| window-switch | unmapped | - | 2251 |
| window-switch | no_records | - | 11405 |
| window-switch | not_closed | ambig_target | 149 |
| window-switch | not_closed | no_list_manifest | 9068 |
| window-switch | not_closed | no_year_manifest | 34097 |
| window-switch | not_closed | unattested | 226 |
| window-switch | not_closed | uncrawled_chain_member | 105 |
| window-switch | not_closed | unverified_product | 68 |
| window-switch | not_closed | variant_unread | 1761 |
| window-switch | not_closed | year_manifest_bad | 1340 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2251 |
| ac-compressor | no_records | - | 8795 |
| ac-compressor | split | no_candidates | 88 |
| ac-compressor | split | option_split | 33709 |
| ac-compressor | conditional | conditional:engine | 1161 |
| ac-compressor | conditional | conditional:engine_unattested | 13522 |
| ac-compressor | conditional | conditional:trim | 944 |
| alternator | unmapped | - | 2251 |
| alternator | no_records | - | 7161 |
| alternator | split | no_candidates | 74 |
| alternator | split | option_split | 43026 |
| alternator | conditional | conditional:engine | 265 |
| alternator | conditional | conditional:engine_unattested | 7200 |
| alternator | conditional | conditional:production | 43 |
| alternator | conditional | conditional:trim | 450 |
| bumper-front | unmapped | - | 2251 |
| bumper-front | no_records | - | 11911 |
| bumper-front | split | no_candidates | 127 |
| bumper-front | split | option_split | 42197 |
| bumper-front | conditional | conditional:engine_unattested | 3984 |
| bumper-rear | unmapped | - | 2251 |
| bumper-rear | no_records | - | 9743 |
| bumper-rear | split | no_candidates | 81 |
| bumper-rear | split | option_split | 43924 |
| bumper-rear | conditional | conditional:engine_unattested | 4471 |
| climate-control | unmapped | - | 2251 |
| climate-control | no_records | - | 22838 |
| climate-control | split | no_candidates | 130 |
| climate-control | split | option_split | 26062 |
| climate-control | conditional | conditional:colour | 222 |
| climate-control | conditional | conditional:engine_unattested | 8743 |
| climate-control | conditional | conditional:trim | 224 |
| door-front | unmapped | - | 2251 |
| door-front | no_records | - | 25807 |
| door-front | split | no_candidates | 2410 |
| door-front | split | option_split | 13327 |
| door-front | split | slot_missing | 2308 |
| door-front | conditional | conditional:body | 177 |
| door-front | conditional | conditional:engine_unattested | 8224 |
| door-front | conditional | conditional:qualifier | 4319 |
| door-front | conditional | conditional:trim | 1647 |
| door-rear | unmapped | - | 2251 |
| door-rear | no_records | - | 25021 |
| door-rear | split | no_candidates | 1336 |
| door-rear | split | option_split | 16076 |
| door-rear | split | slot_missing | 103 |
| door-rear | conditional | conditional:engine_unattested | 1147 |
| door-rear | conditional | conditional:qualifier | 13745 |
| door-rear | conditional | conditional:trim | 791 |
| fender | unmapped | - | 2251 |
| fender | no_records | - | 15870 |
| fender | split | no_candidates | 186 |
| fender | split | option_split | 23438 |
| fender | split | slot_missing | 603 |
| fender | conditional | conditional:engine_unattested | 13577 |
| fender | conditional | conditional:trim | 4545 |
| fuel-pump-module | unmapped | - | 2251 |
| fuel-pump-module | no_records | - | 24489 |
| fuel-pump-module | split | no_candidates | 25 |
| fuel-pump-module | split | option_split | 26636 |
| fuel-pump-module | conditional | conditional:engine | 28 |
| fuel-pump-module | conditional | conditional:engine_unattested | 5790 |
| fuel-pump-module | conditional | conditional:trim | 1251 |
| gauge-cluster | unmapped | - | 2251 |
| gauge-cluster | no_records | - | 31635 |
| gauge-cluster | split | no_candidates | 899 |
| gauge-cluster | split | option_split | 23833 |
| gauge-cluster | conditional | conditional:engine_unattested | 1547 |
| gauge-cluster | conditional | conditional:production | 195 |
| gauge-cluster | conditional | conditional:trim | 110 |
| grille | unmapped | - | 2251 |
| grille | no_records | - | 16769 |
| grille | split | no_candidates | 700 |
| grille | split | option_split | 39476 |
| grille | conditional | conditional:engine_unattested | 1156 |
| grille | conditional | conditional:option | 118 |
| headlights | unmapped | - | 2251 |
| headlights | no_records | - | 14459 |
| headlights | split | no_candidates | 21 |
| headlights | split | option_split | 33907 |
| headlights | split | slot_missing | 437 |
| headlights | conditional | conditional:engine_unattested | 7884 |
| headlights | conditional | conditional:option | 100 |
| headlights | conditional | conditional:package | 63 |
| headlights | conditional | conditional:production | 443 |
| headlights | conditional | conditional:trim | 905 |
| hood | unmapped | - | 2251 |
| hood | no_records | - | 12830 |
| hood | split | no_candidates | 272 |
| hood | split | option_split | 7443 |
| hood | conditional | conditional:engine_unattested | 28848 |
| hood | conditional | conditional:trim | 8826 |
| ignition-coils | unmapped | - | 2251 |
| ignition-coils | no_records | - | 11420 |
| ignition-coils | split | no_candidates | 139 |
| ignition-coils | split | option_split | 25347 |
| ignition-coils | conditional | conditional:engine_unattested | 18283 |
| ignition-coils | conditional | conditional:package | 2848 |
| ignition-coils | conditional | conditional:trim | 182 |
| liftgate | unmapped | - | 2251 |
| liftgate | no_records | - | 35527 |
| liftgate | split | no_candidates | 8352 |
| liftgate | split | option_split | 2718 |
| liftgate | conditional | conditional:engine_unattested | 8622 |
| liftgate | conditional | conditional:option | 1131 |
| liftgate | conditional | conditional:trim | 1869 |
| power-steering-pump | unmapped | - | 2251 |
| power-steering-pump | no_records | - | 32027 |
| power-steering-pump | split | no_candidates | 185 |
| power-steering-pump | split | option_split | 11829 |
| power-steering-pump | conditional | conditional:colour | 447 |
| power-steering-pump | conditional | conditional:engine | 296 |
| power-steering-pump | conditional | conditional:engine_unattested | 11764 |
| power-steering-pump | conditional | conditional:option | 162 |
| power-steering-pump | conditional | conditional:trim | 1509 |
| radiator | unmapped | - | 2251 |
| radiator | no_records | - | 15020 |
| radiator | split | no_candidates | 900 |
| radiator | split | option_split | 38901 |
| radiator | conditional | conditional:engine_unattested | 2789 |
| radiator | conditional | conditional:trim | 609 |
| side-mirrors | unmapped | - | 2251 |
| side-mirrors | no_records | - | 7754 |
| side-mirrors | split | no_candidates | 28 |
| side-mirrors | split | option_split | 45306 |
| side-mirrors | split | position_missing | 6 |
| side-mirrors | split | slot_missing | 2027 |
| side-mirrors | conditional | conditional:colour | 161 |
| side-mirrors | conditional | conditional:engine_unattested | 2371 |
| side-mirrors | conditional | conditional:option | 410 |
| side-mirrors | conditional | conditional:trim | 156 |
| starter | unmapped | - | 2251 |
| starter | no_records | - | 17767 |
| starter | split | no_candidates | 194 |
| starter | split | option_split | 33926 |
| starter | conditional | conditional:engine | 28 |
| starter | conditional | conditional:engine_unattested | 6140 |
| starter | conditional | conditional:option | 162 |
| starter | conditional | conditional:trim | 2 |
| tail-lights | unmapped | - | 2251 |
| tail-lights | no_records | - | 12601 |
| tail-lights | split | no_candidates | 48 |
| tail-lights | split | option_split | 38223 |
| tail-lights | split | slot_missing | 548 |
| tail-lights | conditional | conditional:colour | 55 |
| tail-lights | conditional | conditional:engine_unattested | 5552 |
| tail-lights | conditional | conditional:option | 2 |
| tail-lights | conditional | conditional:production | 127 |
| tail-lights | conditional | conditional:trim | 1063 |
| tailgate | unmapped | - | 2251 |
| tailgate | no_records | - | 36688 |
| tailgate | split | no_candidates | 9289 |
| tailgate | split | option_split | 9225 |
| tailgate | conditional | conditional:engine_unattested | 2558 |
| tailgate | conditional | conditional:trim | 459 |
| throttle-body | unmapped | - | 2251 |
| throttle-body | no_records | - | 26994 |
| throttle-body | split | no_candidates | 8 |
| throttle-body | split | option_split | 14432 |
| throttle-body | conditional | conditional:engine | 55 |
| throttle-body | conditional | conditional:engine_unattested | 14183 |
| throttle-body | conditional | conditional:option | 205 |
| throttle-body | conditional | conditional:trim | 2342 |
| tow-mirrors | unmapped | - | 2251 |
| tow-mirrors | no_records | - | 52223 |
| tow-mirrors | split | option_split | 2947 |
| tow-mirrors | split | position_conflict | 602 |
| tow-mirrors | split | slot_missing | 2358 |
| tow-mirrors | conditional | conditional:colour | 30 |
| tow-mirrors | conditional | conditional:engine_unattested | 59 |
| trunk-lid | unmapped | - | 2251 |
| trunk-lid | no_records | - | 35428 |
| trunk-lid | split | no_candidates | 5075 |
| trunk-lid | split | option_split | 13991 |
| trunk-lid | conditional | conditional:engine_unattested | 3485 |
| trunk-lid | conditional | conditional:trim | 240 |
| window-regulator | unmapped | - | 2251 |
| window-regulator | no_records | - | 17046 |
| window-regulator | split | no_candidates | 101 |
| window-regulator | split | packaging_incomplete | 3956 |
| window-regulator | split | packaging_split | 13771 |
| window-regulator | split | packaging_unstated | 22005 |
| window-regulator | split | position_missing | 736 |
| window-regulator | conditional | conditional:trim | 604 |
| window-switch | unmapped | - | 2251 |
| window-switch | no_records | - | 11405 |
| window-switch | split | no_candidates | 1381 |
| window-switch | split | option_split | 23306 |
| window-switch | split | position_missing | 16302 |
| window-switch | conditional | conditional:colour | 1333 |
| window-switch | conditional | conditional:engine_unattested | 3140 |
| window-switch | conditional | conditional:trim | 1352 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 804
- held_exterior_cross_model: 40
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
- Ford Pinto: feed 'Pinto' 6 cars
- Ford Police Responder Hybrid: feed 'Police Responder Hybrid' 0 cars (excluded: catalog model with no feed cars as 'Police Responder Hybrid' (inventory 2026-11-04); nothing to map)
- Ford SSV Plug-In Hybrid: feed 'SSV Plug-In Hybrid' 0 cars (excluded: catalog model with no feed cars as 'SSV Plug-In Hybrid' (inventory 2026-11-04); nothing to map)
- Lincoln Mark VI: feed 'Mark VI' 4 cars
- Mercury Bobcat: feed 'Bobcat' 0 cars
- Mercury LN7: feed 'LN7' 0 cars
- Mercury Lynx: feed 'Lynx' 0 cars
- Mercury Marquis: feed 'Marquis' 30 cars
- Mercury Villager: feed 'Villager' 80 cars
- Mercury Zephyr: feed 'Zephyr' 3 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (3 cars, under catalog squash 'zephyr'); unmapped until a reviewed entry exists)
