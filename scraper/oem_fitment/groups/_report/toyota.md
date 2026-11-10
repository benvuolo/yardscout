# OEM curation report: toyota

Raw: `dca9cd845f26` @ `dca9cd845f26`; as of 2026-11-09T18:24:28Z.

- records 6446, classes 6402, list rows 27712, year manifests 113, cells 9002
- Verified groups 0, engine vg groups 0, Likely groups 583
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.lexuspartsnow.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.lexuspartsnow.com: only 0% of its 5423 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 561 |
| ac-compressor | no_records | - | 2107 |
| ac-compressor | not_closed | no_list_manifest | 738 |
| ac-compressor | not_closed | no_year_manifest | 22727 |
| ac-compressor | not_closed | uncrawled_chain_member | 172 |
| ac-compressor | not_closed | unverified_product | 83 |
| alternator | unmapped | - | 561 |
| alternator | no_records | - | 2670 |
| alternator | not_closed | no_list_manifest | 755 |
| alternator | not_closed | no_year_manifest | 22169 |
| alternator | not_closed | uncrawled_chain_member | 144 |
| alternator | not_closed | unread_sibling_page | 28 |
| alternator | not_closed | unverified_product | 61 |
| bumper-front | unmapped | - | 561 |
| bumper-front | no_records | - | 5015 |
| bumper-front | not_closed | no_list_manifest | 77 |
| bumper-front | not_closed | no_year_manifest | 19821 |
| bumper-front | not_closed | unread_sibling_page | 914 |
| bumper-rear | unmapped | - | 561 |
| bumper-rear | no_records | - | 3027 |
| bumper-rear | not_closed | no_list_manifest | 88 |
| bumper-rear | not_closed | no_year_manifest | 21798 |
| bumper-rear | not_closed | unread_sibling_page | 914 |
| climate-control | unmapped | - | 561 |
| climate-control | no_records | - | 10455 |
| climate-control | not_closed | no_list_manifest | 234 |
| climate-control | not_closed | no_year_manifest | 14883 |
| climate-control | not_closed | unread_sibling_page | 255 |
| door-front | unmapped | - | 561 |
| door-front | no_records | - | 2692 |
| door-front | not_closed | no_list_manifest | 89 |
| door-front | not_closed | no_year_manifest | 22132 |
| door-front | not_closed | unread_sibling_page | 914 |
| door-rear | unmapped | - | 561 |
| door-rear | no_records | - | 4334 |
| door-rear | not_closed | no_list_manifest | 81 |
| door-rear | not_closed | no_year_manifest | 20513 |
| door-rear | not_closed | unread_sibling_page | 899 |
| fender | unmapped | - | 561 |
| fender | no_records | - | 6792 |
| fender | not_closed | no_list_manifest | 77 |
| fender | not_closed | no_year_manifest | 18044 |
| fender | not_closed | unread_sibling_page | 914 |
| fuel-pump-module | unmapped | - | 561 |
| fuel-pump-module | no_records | - | 11699 |
| fuel-pump-module | not_closed | no_list_manifest | 148 |
| fuel-pump-module | not_closed | no_year_manifest | 13725 |
| fuel-pump-module | not_closed | unread_sibling_page | 255 |
| gauge-cluster | unmapped | - | 561 |
| gauge-cluster | no_records | - | 13796 |
| gauge-cluster | not_closed | no_list_manifest | 1 |
| gauge-cluster | not_closed | no_year_manifest | 11116 |
| gauge-cluster | not_closed | unread_sibling_page | 914 |
| grille | unmapped | - | 561 |
| grille | no_records | - | 6225 |
| grille | not_closed | no_list_manifest | 77 |
| grille | not_closed | no_year_manifest | 18616 |
| grille | not_closed | unattested | 480 |
| grille | not_closed | uncrawled_chain_member | 429 |
| headlights | unmapped | - | 561 |
| headlights | no_records | - | 5013 |
| headlights | not_closed | no_list_manifest | 736 |
| headlights | not_closed | no_year_manifest | 19823 |
| headlights | not_closed | unattested | 13 |
| headlights | not_closed | uncrawled_chain_member | 5 |
| headlights | not_closed | unread_sibling_page | 237 |
| hood | unmapped | - | 561 |
| hood | no_records | - | 2207 |
| hood | not_closed | no_list_manifest | 77 |
| hood | not_closed | no_year_manifest | 22629 |
| hood | not_closed | unread_sibling_page | 914 |
| ignition-coils | unmapped | - | 561 |
| ignition-coils | no_records | - | 627 |
| ignition-coils | not_closed | no_list_manifest | 95 |
| ignition-coils | not_closed | no_year_manifest | 24191 |
| ignition-coils | not_closed | unattested | 48 |
| ignition-coils | not_closed | uncrawled_chain_member | 128 |
| ignition-coils | not_closed | unverified_product | 738 |
| liftgate | unmapped | - | 561 |
| liftgate | no_records | - | 25133 |
| liftgate | not_closed | no_year_manifest | 454 |
| liftgate | not_closed | unattested | 108 |
| liftgate | not_closed | uncrawled_chain_member | 132 |
| power-steering-pump | unmapped | - | 561 |
| power-steering-pump | no_records | - | 15971 |
| power-steering-pump | not_closed | no_list_manifest | 591 |
| power-steering-pump | not_closed | no_year_manifest | 9114 |
| power-steering-pump | not_closed | unread_sibling_page | 151 |
| radiator | unmapped | - | 561 |
| radiator | no_records | - | 2646 |
| radiator | not_closed | no_list_manifest | 88 |
| radiator | not_closed | no_year_manifest | 22179 |
| radiator | not_closed | uncrawled_chain_member | 5 |
| radiator | not_closed | unread_sibling_page | 909 |
| side-mirrors | unmapped | - | 561 |
| side-mirrors | no_records | - | 3269 |
| side-mirrors | not_closed | no_list_manifest | 745 |
| side-mirrors | not_closed | no_year_manifest | 21558 |
| side-mirrors | not_closed | suspect_variant | 30 |
| side-mirrors | not_closed | unattested | 13 |
| side-mirrors | not_closed | uncrawled_chain_member | 134 |
| side-mirrors | not_closed | unread_sibling_page | 78 |
| starter | unmapped | - | 561 |
| starter | no_records | - | 2287 |
| starter | not_closed | no_list_manifest | 756 |
| starter | not_closed | no_year_manifest | 22551 |
| starter | not_closed | unattested | 1 |
| starter | not_closed | uncrawled_chain_member | 171 |
| starter | not_closed | unverified_product | 61 |
| tail-lights | unmapped | - | 561 |
| tail-lights | no_records | - | 7599 |
| tail-lights | not_closed | no_list_manifest | 519 |
| tail-lights | not_closed | no_year_manifest | 17454 |
| tail-lights | not_closed | unattested | 151 |
| tail-lights | not_closed | uncrawled_chain_member | 104 |
| throttle-body | unmapped | - | 561 |
| throttle-body | no_records | - | 3424 |
| throttle-body | not_closed | no_list_manifest | 660 |
| throttle-body | not_closed | no_year_manifest | 21488 |
| throttle-body | not_closed | unread_sibling_page | 233 |
| throttle-body | not_closed | unverified_product | 22 |
| tow-mirrors | unmapped | - | 561 |
| tow-mirrors | no_records | - | 25738 |
| tow-mirrors | not_closed | no_year_manifest | 89 |
| trunk-lid | unmapped | - | 561 |
| trunk-lid | no_records | - | 19779 |
| trunk-lid | not_closed | no_list_manifest | 78 |
| trunk-lid | not_closed | no_year_manifest | 5273 |
| trunk-lid | not_closed | unattested | 30 |
| trunk-lid | not_closed | uncrawled_chain_member | 667 |
| wheels | unmapped | - | 561 |
| wheels | no_records | - | 23274 |
| wheels | not_closed | no_list_manifest | 77 |
| wheels | not_closed | no_year_manifest | 1540 |
| wheels | not_closed | unattested | 157 |
| wheels | not_closed | uncrawled_chain_member | 779 |
| window-regulator | unmapped | - | 561 |
| window-regulator | no_records | - | 953 |
| window-regulator | not_closed | no_list_manifest | 751 |
| window-regulator | not_closed | no_year_manifest | 23868 |
| window-regulator | not_closed | unread_sibling_page | 255 |
| window-switch | unmapped | - | 561 |
| window-switch | no_records | - | 2482 |
| window-switch | not_closed | no_list_manifest | 625 |
| window-switch | not_closed | no_year_manifest | 22465 |
| window-switch | not_closed | unattested | 212 |
| window-switch | not_closed | uncrawled_chain_member | 43 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 561 |
| ac-compressor | no_records | - | 2107 |
| ac-compressor | split | option_split | 13860 |
| ac-compressor | conditional | conditional:body | 2 |
| ac-compressor | conditional | conditional:engine | 1194 |
| ac-compressor | conditional | conditional:engine_unattested | 1223 |
| ac-compressor | conditional | conditional:notes_not_own_page | 2656 |
| ac-compressor | conditional | conditional:option_layout | 481 |
| ac-compressor | conditional | conditional:qualifier | 1198 |
| ac-compressor | conditional | conditional:trim | 2916 |
| ac-compressor | gated | kind_not_phase1 | 190 |
| alternator | unmapped | - | 561 |
| alternator | no_records | - | 2670 |
| alternator | split | option_split | 18150 |
| alternator | conditional | conditional:engine_unattested | 805 |
| alternator | conditional | conditional:notes_not_own_page | 3302 |
| alternator | conditional | conditional:option_layout | 362 |
| alternator | conditional | conditional:production | 62 |
| alternator | conditional | conditional:trim | 195 |
| alternator | chain_member_conditional | chain_member_conditional | 146 |
| alternator | reman_only | reman_only | 135 |
| bumper-front | unmapped | - | 561 |
| bumper-front | no_records | - | 5015 |
| bumper-front | split | option_split | 14144 |
| bumper-front | conditional | conditional:engine | 270 |
| bumper-front | conditional | conditional:engine_unattested | 592 |
| bumper-front | conditional | conditional:notes_not_own_page | 1277 |
| bumper-front | conditional | conditional:option_layout | 66 |
| bumper-front | conditional | conditional:package | 44 |
| bumper-front | conditional | conditional:trim | 3572 |
| bumper-front | chain_member_conditional | chain_member_conditional | 19 |
| bumper-front | blocked | unexpected_position | 306 |
| bumper-front | eligible | - | 522 |
| bumper-rear | unmapped | - | 561 |
| bumper-rear | no_records | - | 3027 |
| bumper-rear | split | option_split | 12869 |
| bumper-rear | conditional | conditional:body | 305 |
| bumper-rear | conditional | conditional:engine | 786 |
| bumper-rear | conditional | conditional:engine_unattested | 1365 |
| bumper-rear | conditional | conditional:notes_not_own_page | 1965 |
| bumper-rear | conditional | conditional:trim | 4711 |
| bumper-rear | chain_member_conditional | chain_member_conditional | 19 |
| bumper-rear | blocked | unexpected_position | 305 |
| bumper-rear | eligible | - | 475 |
| climate-control | unmapped | - | 561 |
| climate-control | no_records | - | 10455 |
| climate-control | split | no_candidates | 226 |
| climate-control | split | option_split | 9905 |
| climate-control | conditional | conditional:engine_unattested | 339 |
| climate-control | conditional | conditional:engine_unparsed | 90 |
| climate-control | conditional | conditional:notes_not_own_page | 1057 |
| climate-control | conditional | conditional:option | 448 |
| climate-control | conditional | conditional:trim | 3024 |
| climate-control | eligible | - | 283 |
| door-front | unmapped | - | 561 |
| door-front | no_records | - | 2692 |
| door-front | split | option_split | 10752 |
| door-front | split | slot_missing | 1780 |
| door-front | conditional | conditional:engine | 395 |
| door-front | conditional | conditional:engine_unattested | 2174 |
| door-front | conditional | conditional:notes_not_own_page | 2728 |
| door-front | conditional | conditional:option_layout | 20 |
| door-front | conditional | conditional:plant | 59 |
| door-front | conditional | conditional:trim | 4252 |
| door-front | chain_member_conditional | chain_member_conditional | 135 |
| door-front | eligible | - | 840 |
| door-rear | unmapped | - | 561 |
| door-rear | no_records | - | 4334 |
| door-rear | split | option_split | 10477 |
| door-rear | split | slot_missing | 411 |
| door-rear | conditional | conditional:body | 70 |
| door-rear | conditional | conditional:engine | 557 |
| door-rear | conditional | conditional:engine_unattested | 1843 |
| door-rear | conditional | conditional:notes_not_own_page | 1817 |
| door-rear | conditional | conditional:option | 259 |
| door-rear | conditional | conditional:trim | 5588 |
| door-rear | eligible | - | 471 |
| fender | unmapped | - | 561 |
| fender | no_records | - | 6792 |
| fender | split | option_split | 6713 |
| fender | split | slot_missing | 554 |
| fender | conditional | conditional:engine | 270 |
| fender | conditional | conditional:engine_unattested | 2009 |
| fender | conditional | conditional:notes_not_own_page | 2358 |
| fender | conditional | conditional:option_layout | 366 |
| fender | conditional | conditional:package | 132 |
| fender | conditional | conditional:trim | 5965 |
| fender | chain_member_conditional | chain_member_conditional | 96 |
| fender | eligible | - | 572 |
| fuel-pump-module | unmapped | - | 561 |
| fuel-pump-module | no_records | - | 11699 |
| fuel-pump-module | split | no_candidates | 145 |
| fuel-pump-module | split | option_split | 8720 |
| fuel-pump-module | conditional | conditional:engine | 146 |
| fuel-pump-module | conditional | conditional:engine_unattested | 498 |
| fuel-pump-module | conditional | conditional:notes_not_own_page | 1975 |
| fuel-pump-module | conditional | conditional:option_layout | 307 |
| fuel-pump-module | conditional | conditional:plant | 59 |
| fuel-pump-module | conditional | conditional:qualifier | 1264 |
| fuel-pump-module | conditional | conditional:trim | 948 |
| fuel-pump-module | gated | kind_not_phase1 | 66 |
| gauge-cluster | unmapped | - | 561 |
| gauge-cluster | no_records | - | 13796 |
| gauge-cluster | split | no_candidates | 265 |
| gauge-cluster | split | option_split | 11417 |
| gauge-cluster | conditional | conditional:engine | 154 |
| gauge-cluster | conditional | conditional:notes_not_own_page | 86 |
| gauge-cluster | conditional | conditional:trim | 35 |
| gauge-cluster | eligible | - | 74 |
| grille | unmapped | - | 561 |
| grille | no_records | - | 6225 |
| grille | split | option_split | 15463 |
| grille | conditional | conditional:engine | 33 |
| grille | conditional | conditional:engine_unattested | 433 |
| grille | conditional | conditional:engine_unparsed | 90 |
| grille | conditional | conditional:notes_not_own_page | 809 |
| grille | conditional | conditional:trim | 2338 |
| grille | eligible | - | 436 |
| headlights | unmapped | - | 561 |
| headlights | no_records | - | 5013 |
| headlights | split | option_split | 13891 |
| headlights | split | slot_missing | 71 |
| headlights | conditional | conditional:engine | 321 |
| headlights | conditional | conditional:engine_unattested | 104 |
| headlights | conditional | conditional:engine_unparsed | 90 |
| headlights | conditional | conditional:notes_not_own_page | 1458 |
| headlights | conditional | conditional:option | 305 |
| headlights | conditional | conditional:plant | 129 |
| headlights | conditional | conditional:qualifier | 3 |
| headlights | conditional | conditional:trim | 3427 |
| headlights | chain_member_conditional | chain_member_conditional | 174 |
| headlights | eligible | - | 841 |
| hood | unmapped | - | 561 |
| hood | no_records | - | 2207 |
| hood | split | option_split | 4229 |
| hood | conditional | conditional:engine | 764 |
| hood | conditional | conditional:engine_unattested | 2236 |
| hood | conditional | conditional:engine_unparsed | 90 |
| hood | conditional | conditional:notes_not_own_page | 3983 |
| hood | conditional | conditional:option | 105 |
| hood | conditional | conditional:package | 132 |
| hood | conditional | conditional:plant | 253 |
| hood | conditional | conditional:trim | 10256 |
| hood | chain_member_conditional | chain_member_conditional | 225 |
| hood | eligible | - | 1347 |
| ignition-coils | unmapped | - | 561 |
| ignition-coils | no_records | - | 627 |
| ignition-coils | split | option_split | 18772 |
| ignition-coils | conditional | conditional:engine | 946 |
| ignition-coils | conditional | conditional:engine_unattested | 1094 |
| ignition-coils | conditional | conditional:notes_not_own_page | 2235 |
| ignition-coils | conditional | conditional:package | 568 |
| ignition-coils | conditional | conditional:trim | 1566 |
| ignition-coils | eligible | - | 19 |
| liftgate | unmapped | - | 561 |
| liftgate | no_records | - | 25133 |
| liftgate | split | option_split | 635 |
| liftgate | conditional | conditional:engine_unattested | 59 |
| power-steering-pump | unmapped | - | 561 |
| power-steering-pump | no_records | - | 15971 |
| power-steering-pump | split | option_split | 4461 |
| power-steering-pump | conditional | conditional:engine_unattested | 1142 |
| power-steering-pump | conditional | conditional:notes_not_own_page | 2468 |
| power-steering-pump | conditional | conditional:option_layout | 1785 |
| radiator | unmapped | - | 561 |
| radiator | no_records | - | 2646 |
| radiator | split | option_split | 21325 |
| radiator | conditional | conditional:engine | 120 |
| radiator | conditional | conditional:engine_unattested | 649 |
| radiator | conditional | conditional:notes_not_own_page | 359 |
| radiator | conditional | conditional:trans | 219 |
| radiator | conditional | conditional:trim | 509 |
| side-mirrors | unmapped | - | 561 |
| side-mirrors | no_records | - | 3269 |
| side-mirrors | split | option_split | 21787 |
| side-mirrors | split | slot_missing | 21 |
| side-mirrors | conditional | conditional:engine | 10 |
| side-mirrors | conditional | conditional:engine_unattested | 6 |
| side-mirrors | conditional | conditional:notes_not_own_page | 97 |
| side-mirrors | conditional | conditional:trim | 590 |
| side-mirrors | eligible | - | 47 |
| starter | unmapped | - | 561 |
| starter | no_records | - | 2287 |
| starter | split | option_split | 15652 |
| starter | conditional | conditional:engine | 205 |
| starter | conditional | conditional:engine_unattested | 1143 |
| starter | conditional | conditional:notes_not_own_page | 4204 |
| starter | conditional | conditional:option_layout | 1241 |
| starter | conditional | conditional:plant | 386 |
| starter | conditional | conditional:trim | 577 |
| starter | chain_member_conditional | chain_member_conditional | 47 |
| starter | reman_only | reman_only | 85 |
| tail-lights | unmapped | - | 561 |
| tail-lights | no_records | - | 7599 |
| tail-lights | split | no_candidates | 38 |
| tail-lights | split | option_split | 10470 |
| tail-lights | split | slot_missing | 345 |
| tail-lights | conditional | conditional:engine | 107 |
| tail-lights | conditional | conditional:engine_unattested | 733 |
| tail-lights | conditional | conditional:engine_unparsed | 90 |
| tail-lights | conditional | conditional:notes_not_own_page | 858 |
| tail-lights | conditional | conditional:plant | 908 |
| tail-lights | conditional | conditional:position | 112 |
| tail-lights | conditional | conditional:trim | 4169 |
| tail-lights | eligible | - | 398 |
| throttle-body | unmapped | - | 561 |
| throttle-body | no_records | - | 3424 |
| throttle-body | split | option_split | 13767 |
| throttle-body | conditional | conditional:engine | 933 |
| throttle-body | conditional | conditional:engine_unattested | 983 |
| throttle-body | conditional | conditional:notes_not_own_page | 1687 |
| throttle-body | conditional | conditional:plant | 274 |
| throttle-body | conditional | conditional:qualifier | 809 |
| throttle-body | conditional | conditional:trim | 3244 |
| throttle-body | conditional | conditional:unknown | 135 |
| throttle-body | gated | kind_not_phase1 | 571 |
| tow-mirrors | unmapped | - | 561 |
| tow-mirrors | no_records | - | 25738 |
| tow-mirrors | conditional | conditional:notes_not_own_page | 45 |
| tow-mirrors | conditional | conditional:package | 44 |
| trunk-lid | unmapped | - | 561 |
| trunk-lid | no_records | - | 19779 |
| trunk-lid | split | option_split | 4241 |
| trunk-lid | conditional | conditional:engine_unattested | 275 |
| trunk-lid | conditional | conditional:notes_not_own_page | 1180 |
| trunk-lid | conditional | conditional:option_layout | 349 |
| trunk-lid | conditional | conditional:trim | 3 |
| wheels | unmapped | - | 561 |
| wheels | no_records | - | 23274 |
| wheels | split | option_split | 2458 |
| wheels | conditional | conditional:engine_unattested | 95 |
| window-regulator | unmapped | - | 561 |
| window-regulator | no_records | - | 953 |
| window-regulator | split | packaging_incomplete | 973 |
| window-regulator | split | packaging_split | 12762 |
| window-regulator | split | packaging_unstated | 10102 |
| window-regulator | split | position_missing | 330 |
| window-regulator | conditional | conditional:engine_unattested | 386 |
| window-regulator | conditional | conditional:trim | 65 |
| window-regulator | eligible | - | 256 |
| window-switch | unmapped | - | 561 |
| window-switch | no_records | - | 2482 |
| window-switch | split | no_candidates | 113 |
| window-switch | split | option_split | 10888 |
| window-switch | split | position_missing | 3538 |
| window-switch | conditional | conditional:engine | 871 |
| window-switch | conditional | conditional:engine_unattested | 39 |
| window-switch | conditional | conditional:notes_not_own_page | 2457 |
| window-switch | conditional | conditional:option | 25 |
| window-switch | conditional | conditional:plant | 390 |
| window-switch | conditional | conditional:position | 208 |
| window-switch | conditional | conditional:trim | 4673 |
| window-switch | eligible | - | 143 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 50
- disputed_class: 44
- evidence_mismatch: 6
- recrawl_resolved: 3
- systemic_evidence_failure: 1
- universal_part_suspect: 7
- wheels_not_audited: 52

## Unknown note clauses (top 30)

- `#`: 685
- `Part Name Code: 87910`: 567
- `Part Name Code: 87940`: 533
- `Package Quantity: 1`: 385
- `Part Name Code: 42601`: 302
- `Part Name Code: 87901B`: 237
- `Part Name Code: 87906B`: 231
- `Require Quantity: 4`: 228
- `Part Name Code: 83100`: 191
- `Part Name Code: 42601A`: 154
- `SUMMER TIRE`: 149
- `PAINT REQ.`: 132
- `Part Name Code: 52119A`: 123
- `Part Name Code: 81175`: 122
- `GYL1#.. JPP`: 116
- `Require Quantity: 2`: 116
- `Part Name Code: 81135`: 115
- `FR`: 114
- `RR`: 114
- `GSE20`: 107
- `UZS190`: 101
- `ALUMI`: 93
- `21`: 83
- `21.. ATM`: 81
- `F-SPORTS`: 80
- `W(MEMORY ADJUST SYSTEM)`: 78
- `18X7JJ`: 74
- `OEM`: 74
- `Part Name Code: 64401`: 74
- `Part Name Code: 53111`: 66

## Unmapped catalog models

- Lexus GS Turbo: feed 'GS Turbo' 0 cars
- Lexus GS200t: feed 'GS 200t' 0 cars
- Lexus GX460: feed 'GX 460' 0 cars
- Lexus IS F: feed 'IS F' 0 cars (excluded: catalog model with no feed cars as 'IS F' (inventory 2026-11-04); nothing to map)
- Lexus IS Turbo: feed 'IS Turbo' 0 cars
- Lexus LS600hL: feed 'LS 600h L' 0 cars (excluded: M6: the only feed 'LS 600h L' car decodes as another make (vPIC mismatch))
- Lexus LX470: feed 'LX 470' 5 cars
- Lexus LX570: feed 'LX 570' 0 cars
- Lexus NX200t: feed 'NX 200t' 0 cars
- Lexus NX300: feed 'NX 300' 0 cars
- Lexus NX300h: feed 'NX 300h' 0 cars
- Lexus RC Turbo: feed 'RC Turbo' 0 cars
- Lexus RC200t: feed 'RC 200t' 0 cars
- Lexus RC300: feed 'RC 300' 0 cars
- Lexus SC300: feed 'SC 300' 10 cars
- Toyota C-HR: feed 'C-HR' 12 cars
- Toyota Corolla Cross: feed 'Corolla Cross' 0 cars
- Toyota Crown: feed 'Crown' 0 cars
- Toyota Crown Signia: feed 'Crown Signia' 0 cars
- Toyota GR Corolla: feed 'GR Corolla' 0 cars
- Toyota Grand Highlander: feed 'Grand Highlander' 0 cars
- Toyota Prius AWD-e: feed 'Prius' 1564 cars (excluded: catalog model with no feed cars as 'Prius AWD-e' (inventory 2026-11-04); nothing to map)
- Toyota RAV4 Prime: feed 'RAV4 Prime' 0 cars
- Toyota T100: feed 'T100' 55 cars
