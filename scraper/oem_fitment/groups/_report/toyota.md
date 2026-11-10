# OEM curation report: toyota

Raw: `dca9cd845f26` @ `dca9cd845f26`; as of 2026-11-09T18:24:28Z.

- records 6446, classes 6402, list rows 27712, year manifests 113, cells 9002
- Verified groups 0, engine vg groups 0, Likely groups 557
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.lexuspartsnow.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.lexuspartsnow.com: only 0% of its 5423 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 561 |
| ac-compressor | no_records | - | 2114 |
| ac-compressor | not_closed | no_list_manifest | 743 |
| ac-compressor | not_closed | no_year_manifest | 22759 |
| ac-compressor | not_closed | uncrawled_chain_member | 172 |
| ac-compressor | not_closed | unverified_product | 83 |
| alternator | unmapped | - | 561 |
| alternator | no_records | - | 2669 |
| alternator | not_closed | no_list_manifest | 760 |
| alternator | not_closed | no_year_manifest | 22209 |
| alternator | not_closed | uncrawled_chain_member | 144 |
| alternator | not_closed | unread_sibling_page | 28 |
| alternator | not_closed | unverified_product | 61 |
| bumper-front | unmapped | - | 561 |
| bumper-front | no_records | - | 5036 |
| bumper-front | not_closed | no_list_manifest | 78 |
| bumper-front | not_closed | no_year_manifest | 19839 |
| bumper-front | not_closed | unread_sibling_page | 918 |
| bumper-rear | unmapped | - | 561 |
| bumper-rear | no_records | - | 3033 |
| bumper-rear | not_closed | no_list_manifest | 89 |
| bumper-rear | not_closed | no_year_manifest | 21831 |
| bumper-rear | not_closed | unread_sibling_page | 918 |
| climate-control | unmapped | - | 561 |
| climate-control | no_records | - | 10478 |
| climate-control | not_closed | no_list_manifest | 235 |
| climate-control | not_closed | no_year_manifest | 14903 |
| climate-control | not_closed | unread_sibling_page | 255 |
| door-front | unmapped | - | 561 |
| door-front | no_records | - | 2698 |
| door-front | not_closed | no_list_manifest | 90 |
| door-front | not_closed | no_year_manifest | 22165 |
| door-front | not_closed | unread_sibling_page | 918 |
| door-rear | unmapped | - | 561 |
| door-rear | no_records | - | 4344 |
| door-rear | not_closed | no_list_manifest | 82 |
| door-rear | not_closed | no_year_manifest | 20542 |
| door-rear | not_closed | unread_sibling_page | 903 |
| fender | unmapped | - | 561 |
| fender | no_records | - | 6806 |
| fender | not_closed | no_list_manifest | 78 |
| fender | not_closed | no_year_manifest | 18069 |
| fender | not_closed | unread_sibling_page | 918 |
| fuel-pump-module | unmapped | - | 561 |
| fuel-pump-module | no_records | - | 11717 |
| fuel-pump-module | not_closed | no_list_manifest | 151 |
| fuel-pump-module | not_closed | no_year_manifest | 13748 |
| fuel-pump-module | not_closed | unread_sibling_page | 255 |
| gauge-cluster | unmapped | - | 561 |
| gauge-cluster | no_records | - | 13821 |
| gauge-cluster | not_closed | no_list_manifest | 1 |
| gauge-cluster | not_closed | no_year_manifest | 11131 |
| gauge-cluster | not_closed | unread_sibling_page | 918 |
| grille | unmapped | - | 561 |
| grille | no_records | - | 6235 |
| grille | not_closed | no_list_manifest | 78 |
| grille | not_closed | no_year_manifest | 18645 |
| grille | not_closed | unattested | 481 |
| grille | not_closed | uncrawled_chain_member | 432 |
| headlights | unmapped | - | 561 |
| headlights | no_records | - | 5025 |
| headlights | not_closed | no_list_manifest | 741 |
| headlights | not_closed | no_year_manifest | 19850 |
| headlights | not_closed | unattested | 13 |
| headlights | not_closed | uncrawled_chain_member | 5 |
| headlights | not_closed | unread_sibling_page | 237 |
| hood | unmapped | - | 561 |
| hood | no_records | - | 2209 |
| hood | not_closed | no_list_manifest | 78 |
| hood | not_closed | no_year_manifest | 22666 |
| hood | not_closed | unread_sibling_page | 918 |
| ignition-coils | unmapped | - | 561 |
| ignition-coils | no_records | - | 625 |
| ignition-coils | not_closed | no_list_manifest | 96 |
| ignition-coils | not_closed | no_year_manifest | 24232 |
| ignition-coils | not_closed | unattested | 47 |
| ignition-coils | not_closed | uncrawled_chain_member | 128 |
| ignition-coils | not_closed | unverified_product | 743 |
| liftgate | unmapped | - | 561 |
| liftgate | no_records | - | 25176 |
| liftgate | not_closed | no_year_manifest | 455 |
| liftgate | not_closed | unattested | 108 |
| liftgate | not_closed | uncrawled_chain_member | 132 |
| power-steering-pump | unmapped | - | 561 |
| power-steering-pump | no_records | - | 16007 |
| power-steering-pump | not_closed | no_list_manifest | 593 |
| power-steering-pump | not_closed | no_year_manifest | 9121 |
| power-steering-pump | not_closed | unread_sibling_page | 150 |
| radiator | unmapped | - | 561 |
| radiator | no_records | - | 2653 |
| radiator | not_closed | no_list_manifest | 89 |
| radiator | not_closed | no_year_manifest | 22211 |
| radiator | not_closed | uncrawled_chain_member | 5 |
| radiator | not_closed | unread_sibling_page | 913 |
| side-mirrors | unmapped | - | 561 |
| side-mirrors | no_records | - | 3270 |
| side-mirrors | not_closed | no_list_manifest | 750 |
| side-mirrors | not_closed | no_year_manifest | 21596 |
| side-mirrors | not_closed | suspect_variant | 30 |
| side-mirrors | not_closed | unattested | 13 |
| side-mirrors | not_closed | uncrawled_chain_member | 133 |
| side-mirrors | not_closed | unread_sibling_page | 79 |
| starter | unmapped | - | 561 |
| starter | no_records | - | 2288 |
| starter | not_closed | no_list_manifest | 761 |
| starter | not_closed | no_year_manifest | 22589 |
| starter | not_closed | unattested | 1 |
| starter | not_closed | uncrawled_chain_member | 171 |
| starter | not_closed | unverified_product | 61 |
| tail-lights | unmapped | - | 561 |
| tail-lights | no_records | - | 7614 |
| tail-lights | not_closed | no_list_manifest | 524 |
| tail-lights | not_closed | no_year_manifest | 17478 |
| tail-lights | not_closed | unattested | 152 |
| tail-lights | not_closed | uncrawled_chain_member | 103 |
| throttle-body | unmapped | - | 561 |
| throttle-body | no_records | - | 3430 |
| throttle-body | not_closed | no_list_manifest | 665 |
| throttle-body | not_closed | no_year_manifest | 21521 |
| throttle-body | not_closed | unread_sibling_page | 233 |
| throttle-body | not_closed | unverified_product | 22 |
| tow-mirrors | unmapped | - | 561 |
| tow-mirrors | no_records | - | 25781 |
| tow-mirrors | not_closed | no_year_manifest | 90 |
| trunk-lid | unmapped | - | 561 |
| trunk-lid | no_records | - | 19807 |
| trunk-lid | not_closed | no_list_manifest | 79 |
| trunk-lid | not_closed | no_year_manifest | 5285 |
| trunk-lid | not_closed | unattested | 30 |
| trunk-lid | not_closed | uncrawled_chain_member | 670 |
| wheels | unmapped | - | 561 |
| wheels | no_records | - | 23309 |
| wheels | not_closed | no_list_manifest | 77 |
| wheels | not_closed | no_year_manifest | 1544 |
| wheels | not_closed | unattested | 157 |
| wheels | not_closed | uncrawled_chain_member | 784 |
| window-regulator | unmapped | - | 561 |
| window-regulator | no_records | - | 955 |
| window-regulator | not_closed | no_list_manifest | 756 |
| window-regulator | not_closed | no_year_manifest | 23905 |
| window-regulator | not_closed | unread_sibling_page | 255 |
| window-switch | unmapped | - | 561 |
| window-switch | no_records | - | 2493 |
| window-switch | not_closed | no_list_manifest | 628 |
| window-switch | not_closed | no_year_manifest | 22495 |
| window-switch | not_closed | unattested | 212 |
| window-switch | not_closed | uncrawled_chain_member | 43 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 561 |
| ac-compressor | no_records | - | 2114 |
| ac-compressor | split | option_split | 13877 |
| ac-compressor | conditional | conditional:body | 2 |
| ac-compressor | conditional | conditional:engine | 1195 |
| ac-compressor | conditional | conditional:engine_unattested | 1225 |
| ac-compressor | conditional | conditional:notes_not_own_page | 2665 |
| ac-compressor | conditional | conditional:option_layout | 481 |
| ac-compressor | conditional | conditional:qualifier | 1198 |
| ac-compressor | conditional | conditional:trim | 2925 |
| ac-compressor | gated | kind_not_phase1 | 189 |
| alternator | unmapped | - | 561 |
| alternator | no_records | - | 2669 |
| alternator | split | option_split | 18182 |
| alternator | conditional | conditional:engine_unattested | 807 |
| alternator | conditional | conditional:notes_not_own_page | 3313 |
| alternator | conditional | conditional:option_layout | 362 |
| alternator | conditional | conditional:production | 62 |
| alternator | conditional | conditional:trim | 195 |
| alternator | chain_member_conditional | chain_member_conditional | 146 |
| alternator | reman_only | reman_only | 135 |
| bumper-front | unmapped | - | 561 |
| bumper-front | no_records | - | 5036 |
| bumper-front | split | option_split | 14165 |
| bumper-front | conditional | conditional:engine | 270 |
| bumper-front | conditional | conditional:engine_unattested | 597 |
| bumper-front | conditional | conditional:notes_not_own_page | 1280 |
| bumper-front | conditional | conditional:option_layout | 65 |
| bumper-front | conditional | conditional:package | 44 |
| bumper-front | conditional | conditional:trim | 3566 |
| bumper-front | chain_member_conditional | chain_member_conditional | 19 |
| bumper-front | blocked | unexpected_position | 308 |
| bumper-front | eligible | - | 521 |
| bumper-rear | unmapped | - | 561 |
| bumper-rear | no_records | - | 3033 |
| bumper-rear | split | option_split | 12896 |
| bumper-rear | conditional | conditional:body | 306 |
| bumper-rear | conditional | conditional:engine | 784 |
| bumper-rear | conditional | conditional:engine_unattested | 1370 |
| bumper-rear | conditional | conditional:notes_not_own_page | 1970 |
| bumper-rear | conditional | conditional:trim | 4714 |
| bumper-rear | chain_member_conditional | chain_member_conditional | 19 |
| bumper-rear | blocked | unexpected_position | 305 |
| bumper-rear | eligible | - | 474 |
| climate-control | unmapped | - | 561 |
| climate-control | no_records | - | 10478 |
| climate-control | split | no_candidates | 226 |
| climate-control | split | option_split | 9922 |
| climate-control | conditional | conditional:engine_unattested | 340 |
| climate-control | conditional | conditional:engine_unparsed | 90 |
| climate-control | conditional | conditional:notes_not_own_page | 1061 |
| climate-control | conditional | conditional:option | 448 |
| climate-control | conditional | conditional:trim | 3022 |
| climate-control | eligible | - | 284 |
| door-front | unmapped | - | 561 |
| door-front | no_records | - | 2698 |
| door-front | split | option_split | 10759 |
| door-front | split | slot_missing | 1784 |
| door-front | conditional | conditional:engine | 394 |
| door-front | conditional | conditional:engine_unattested | 2184 |
| door-front | conditional | conditional:notes_not_own_page | 2740 |
| door-front | conditional | conditional:option_layout | 20 |
| door-front | conditional | conditional:plant | 59 |
| door-front | conditional | conditional:trim | 4261 |
| door-front | chain_member_conditional | chain_member_conditional | 135 |
| door-front | eligible | - | 837 |
| door-rear | unmapped | - | 561 |
| door-rear | no_records | - | 4344 |
| door-rear | split | option_split | 10486 |
| door-rear | split | slot_missing | 414 |
| door-rear | conditional | conditional:body | 70 |
| door-rear | conditional | conditional:engine | 555 |
| door-rear | conditional | conditional:engine_unattested | 1851 |
| door-rear | conditional | conditional:notes_not_own_page | 1825 |
| door-rear | conditional | conditional:option | 261 |
| door-rear | conditional | conditional:trim | 5594 |
| door-rear | eligible | - | 471 |
| fender | unmapped | - | 561 |
| fender | no_records | - | 6806 |
| fender | split | option_split | 6726 |
| fender | split | slot_missing | 557 |
| fender | conditional | conditional:engine | 270 |
| fender | conditional | conditional:engine_unattested | 2016 |
| fender | conditional | conditional:notes_not_own_page | 2361 |
| fender | conditional | conditional:option_layout | 366 |
| fender | conditional | conditional:package | 132 |
| fender | conditional | conditional:trim | 5970 |
| fender | chain_member_conditional | chain_member_conditional | 97 |
| fender | eligible | - | 570 |
| fuel-pump-module | unmapped | - | 561 |
| fuel-pump-module | no_records | - | 11717 |
| fuel-pump-module | split | no_candidates | 144 |
| fuel-pump-module | split | option_split | 8738 |
| fuel-pump-module | conditional | conditional:engine | 145 |
| fuel-pump-module | conditional | conditional:engine_unattested | 499 |
| fuel-pump-module | conditional | conditional:notes_not_own_page | 1976 |
| fuel-pump-module | conditional | conditional:option_layout | 307 |
| fuel-pump-module | conditional | conditional:plant | 59 |
| fuel-pump-module | conditional | conditional:qualifier | 1269 |
| fuel-pump-module | conditional | conditional:trim | 951 |
| fuel-pump-module | gated | kind_not_phase1 | 66 |
| gauge-cluster | unmapped | - | 561 |
| gauge-cluster | no_records | - | 13821 |
| gauge-cluster | split | no_candidates | 265 |
| gauge-cluster | split | option_split | 11436 |
| gauge-cluster | conditional | conditional:engine | 154 |
| gauge-cluster | conditional | conditional:notes_not_own_page | 86 |
| gauge-cluster | conditional | conditional:trim | 35 |
| gauge-cluster | eligible | - | 74 |
| grille | unmapped | - | 561 |
| grille | no_records | - | 6235 |
| grille | split | option_split | 15491 |
| grille | conditional | conditional:engine | 33 |
| grille | conditional | conditional:engine_unattested | 436 |
| grille | conditional | conditional:engine_unparsed | 90 |
| grille | conditional | conditional:notes_not_own_page | 814 |
| grille | conditional | conditional:trim | 2338 |
| grille | eligible | - | 434 |
| headlights | unmapped | - | 561 |
| headlights | no_records | - | 5025 |
| headlights | split | option_split | 13918 |
| headlights | split | slot_missing | 72 |
| headlights | conditional | conditional:engine | 320 |
| headlights | conditional | conditional:engine_unattested | 104 |
| headlights | conditional | conditional:engine_unparsed | 90 |
| headlights | conditional | conditional:notes_not_own_page | 1464 |
| headlights | conditional | conditional:option | 305 |
| headlights | conditional | conditional:plant | 129 |
| headlights | conditional | conditional:qualifier | 3 |
| headlights | conditional | conditional:trim | 3427 |
| headlights | chain_member_conditional | chain_member_conditional | 173 |
| headlights | eligible | - | 841 |
| hood | unmapped | - | 561 |
| hood | no_records | - | 2209 |
| hood | split | option_split | 4233 |
| hood | conditional | conditional:engine | 764 |
| hood | conditional | conditional:engine_unattested | 2245 |
| hood | conditional | conditional:engine_unparsed | 90 |
| hood | conditional | conditional:notes_not_own_page | 3997 |
| hood | conditional | conditional:option | 105 |
| hood | conditional | conditional:package | 132 |
| hood | conditional | conditional:plant | 252 |
| hood | conditional | conditional:trim | 10273 |
| hood | chain_member_conditional | chain_member_conditional | 223 |
| hood | eligible | - | 1348 |
| ignition-coils | unmapped | - | 561 |
| ignition-coils | no_records | - | 625 |
| ignition-coils | split | option_split | 18794 |
| ignition-coils | conditional | conditional:engine | 949 |
| ignition-coils | conditional | conditional:engine_unattested | 1101 |
| ignition-coils | conditional | conditional:notes_not_own_page | 2245 |
| ignition-coils | conditional | conditional:package | 569 |
| ignition-coils | conditional | conditional:trim | 1569 |
| ignition-coils | eligible | - | 19 |
| liftgate | unmapped | - | 561 |
| liftgate | no_records | - | 25176 |
| liftgate | split | option_split | 637 |
| liftgate | conditional | conditional:engine_unattested | 58 |
| power-steering-pump | unmapped | - | 561 |
| power-steering-pump | no_records | - | 16007 |
| power-steering-pump | split | option_split | 4460 |
| power-steering-pump | conditional | conditional:engine_unattested | 1147 |
| power-steering-pump | conditional | conditional:notes_not_own_page | 2467 |
| power-steering-pump | conditional | conditional:option_layout | 1790 |
| radiator | unmapped | - | 561 |
| radiator | no_records | - | 2653 |
| radiator | split | option_split | 21359 |
| radiator | conditional | conditional:engine | 121 |
| radiator | conditional | conditional:engine_unattested | 651 |
| radiator | conditional | conditional:notes_not_own_page | 358 |
| radiator | conditional | conditional:trans | 219 |
| radiator | conditional | conditional:trim | 510 |
| side-mirrors | unmapped | - | 561 |
| side-mirrors | no_records | - | 3270 |
| side-mirrors | split | option_split | 21832 |
| side-mirrors | split | slot_missing | 21 |
| side-mirrors | conditional | conditional:engine | 10 |
| side-mirrors | conditional | conditional:engine_unattested | 6 |
| side-mirrors | conditional | conditional:notes_not_own_page | 97 |
| side-mirrors | conditional | conditional:trim | 588 |
| side-mirrors | eligible | - | 47 |
| starter | unmapped | - | 561 |
| starter | no_records | - | 2288 |
| starter | split | option_split | 15669 |
| starter | conditional | conditional:engine | 205 |
| starter | conditional | conditional:engine_unattested | 1146 |
| starter | conditional | conditional:notes_not_own_page | 4221 |
| starter | conditional | conditional:option_layout | 1244 |
| starter | conditional | conditional:plant | 388 |
| starter | conditional | conditional:trim | 578 |
| starter | chain_member_conditional | chain_member_conditional | 47 |
| starter | reman_only | reman_only | 85 |
| tail-lights | unmapped | - | 561 |
| tail-lights | no_records | - | 7614 |
| tail-lights | split | no_candidates | 38 |
| tail-lights | split | option_split | 10483 |
| tail-lights | split | slot_missing | 347 |
| tail-lights | conditional | conditional:engine | 106 |
| tail-lights | conditional | conditional:engine_unattested | 736 |
| tail-lights | conditional | conditional:engine_unparsed | 90 |
| tail-lights | conditional | conditional:notes_not_own_page | 861 |
| tail-lights | conditional | conditional:plant | 911 |
| tail-lights | conditional | conditional:position | 111 |
| tail-lights | conditional | conditional:trim | 4177 |
| tail-lights | eligible | - | 397 |
| throttle-body | unmapped | - | 561 |
| throttle-body | no_records | - | 3430 |
| throttle-body | split | option_split | 13780 |
| throttle-body | conditional | conditional:engine | 938 |
| throttle-body | conditional | conditional:engine_unattested | 986 |
| throttle-body | conditional | conditional:notes_not_own_page | 1693 |
| throttle-body | conditional | conditional:plant | 275 |
| throttle-body | conditional | conditional:qualifier | 810 |
| throttle-body | conditional | conditional:trim | 3253 |
| throttle-body | conditional | conditional:unknown | 135 |
| throttle-body | gated | kind_not_phase1 | 571 |
| tow-mirrors | unmapped | - | 561 |
| tow-mirrors | no_records | - | 25781 |
| tow-mirrors | conditional | conditional:notes_not_own_page | 45 |
| tow-mirrors | conditional | conditional:package | 45 |
| trunk-lid | unmapped | - | 561 |
| trunk-lid | no_records | - | 19807 |
| trunk-lid | split | option_split | 4250 |
| trunk-lid | conditional | conditional:engine_unattested | 277 |
| trunk-lid | conditional | conditional:notes_not_own_page | 1185 |
| trunk-lid | conditional | conditional:option_layout | 349 |
| trunk-lid | conditional | conditional:trim | 3 |
| wheels | unmapped | - | 561 |
| wheels | no_records | - | 23309 |
| wheels | split | option_split | 2465 |
| wheels | conditional | conditional:engine_unattested | 97 |
| window-regulator | unmapped | - | 561 |
| window-regulator | no_records | - | 955 |
| window-regulator | split | packaging_incomplete | 974 |
| window-regulator | split | packaging_split | 12879 |
| window-regulator | split | packaging_unstated | 10117 |
| window-regulator | split | position_missing | 331 |
| window-regulator | conditional | conditional:engine_unattested | 292 |
| window-regulator | conditional | conditional:trim | 66 |
| window-regulator | eligible | - | 257 |
| window-switch | unmapped | - | 561 |
| window-switch | no_records | - | 2493 |
| window-switch | split | no_candidates | 113 |
| window-switch | split | option_split | 10901 |
| window-switch | split | position_missing | 3547 |
| window-switch | conditional | conditional:engine | 870 |
| window-switch | conditional | conditional:engine_unattested | 38 |
| window-switch | conditional | conditional:notes_not_own_page | 2462 |
| window-switch | conditional | conditional:option | 25 |
| window-switch | conditional | conditional:plant | 392 |
| window-switch | conditional | conditional:position | 208 |
| window-switch | conditional | conditional:trim | 4680 |
| window-switch | eligible | - | 142 |

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
- `Part Name Code: 87910`: 562
- `Part Name Code: 87940`: 524
- `Package Quantity: 1`: 385
- `Part Name Code: 42601`: 302
- `Require Quantity: 4`: 228
- `Part Name Code: 87901B`: 227
- `Part Name Code: 87906B`: 221
- `Part Name Code: 83100`: 191
- `Part Name Code: 42601A`: 154
- `SUMMER TIRE`: 149
- `PAINT REQ.`: 132
- `Part Name Code: 52119A`: 123
- `Require Quantity: 2`: 116
- `FR`: 114
- `Part Name Code: 81175`: 114
- `RR`: 114
- `Part Name Code: 81135`: 110
- `GSE20`: 107
- `GYL1#.. JPP`: 106
- `UZS190`: 100
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
- Toyota T100: feed 'T100' 56 cars
