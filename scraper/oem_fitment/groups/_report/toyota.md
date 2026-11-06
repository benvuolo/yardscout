# OEM curation report: toyota

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-06T00:06:09Z.

- records 6214, classes 6170, list rows 25651, year manifests 64, cells 8621
- Verified groups 0, engine vg groups 0, Likely groups 781
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.lexuspartsnow.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.lexuspartsnow.com: only 0% of its 4959 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 712 |
| ac-compressor | no_records | - | 2012 |
| ac-compressor | not_closed | no_list_manifest | 656 |
| ac-compressor | not_closed | no_year_manifest | 22736 |
| ac-compressor | not_closed | uncrawled_chain_member | 157 |
| ac-compressor | not_closed | unverified_product | 85 |
| alternator | unmapped | - | 712 |
| alternator | no_records | - | 2591 |
| alternator | not_closed | no_list_manifest | 656 |
| alternator | not_closed | no_year_manifest | 22180 |
| alternator | not_closed | uncrawled_chain_member | 129 |
| alternator | not_closed | unread_sibling_page | 28 |
| alternator | not_closed | unverified_product | 62 |
| bumper-front | unmapped | - | 712 |
| bumper-front | no_records | - | 4951 |
| bumper-front | not_closed | no_year_manifest | 19795 |
| bumper-front | not_closed | unread_sibling_page | 900 |
| bumper-rear | unmapped | - | 712 |
| bumper-rear | no_records | - | 2980 |
| bumper-rear | not_closed | no_year_manifest | 21766 |
| bumper-rear | not_closed | unread_sibling_page | 900 |
| climate-control | unmapped | - | 712 |
| climate-control | no_records | - | 10346 |
| climate-control | not_closed | no_list_manifest | 157 |
| climate-control | not_closed | no_year_manifest | 14901 |
| climate-control | not_closed | unread_sibling_page | 242 |
| door-front | unmapped | - | 712 |
| door-front | no_records | - | 2623 |
| door-front | not_closed | no_year_manifest | 22123 |
| door-front | not_closed | unread_sibling_page | 900 |
| door-rear | unmapped | - | 712 |
| door-rear | no_records | - | 4240 |
| door-rear | not_closed | no_year_manifest | 20516 |
| door-rear | not_closed | unread_sibling_page | 890 |
| fender | unmapped | - | 712 |
| fender | no_records | - | 6728 |
| fender | not_closed | no_year_manifest | 18018 |
| fender | not_closed | unread_sibling_page | 900 |
| fuel-pump-module | unmapped | - | 712 |
| fuel-pump-module | no_records | - | 11575 |
| fuel-pump-module | not_closed | no_list_manifest | 147 |
| fuel-pump-module | not_closed | no_year_manifest | 13682 |
| fuel-pump-module | not_closed | unread_sibling_page | 242 |
| gauge-cluster | unmapped | - | 712 |
| gauge-cluster | no_records | - | 13670 |
| gauge-cluster | not_closed | no_year_manifest | 11076 |
| gauge-cluster | not_closed | unread_sibling_page | 900 |
| grille | unmapped | - | 712 |
| grille | no_records | - | 6133 |
| grille | not_closed | no_year_manifest | 18613 |
| grille | not_closed | unattested | 473 |
| grille | not_closed | uncrawled_chain_member | 427 |
| headlights | unmapped | - | 712 |
| headlights | no_records | - | 4930 |
| headlights | not_closed | no_list_manifest | 654 |
| headlights | not_closed | no_year_manifest | 19820 |
| headlights | not_closed | unread_sibling_page | 242 |
| hood | unmapped | - | 712 |
| hood | no_records | - | 2137 |
| hood | not_closed | no_year_manifest | 22609 |
| hood | not_closed | unread_sibling_page | 900 |
| ignition-coils | unmapped | - | 712 |
| ignition-coils | no_records | - | 623 |
| ignition-coils | not_closed | no_year_manifest | 24123 |
| ignition-coils | not_closed | unattested | 50 |
| ignition-coils | not_closed | uncrawled_chain_member | 128 |
| ignition-coils | not_closed | unverified_product | 722 |
| liftgate | unmapped | - | 712 |
| liftgate | no_records | - | 24950 |
| liftgate | not_closed | no_year_manifest | 453 |
| liftgate | not_closed | unattested | 109 |
| liftgate | not_closed | uncrawled_chain_member | 134 |
| power-steering-pump | unmapped | - | 712 |
| power-steering-pump | no_records | - | 15933 |
| power-steering-pump | not_closed | no_list_manifest | 509 |
| power-steering-pump | not_closed | no_year_manifest | 9069 |
| power-steering-pump | not_closed | unread_sibling_page | 135 |
| radiator | unmapped | - | 712 |
| radiator | no_records | - | 2586 |
| radiator | not_closed | no_year_manifest | 22160 |
| radiator | not_closed | unread_sibling_page | 900 |
| side-mirrors | unmapped | - | 712 |
| side-mirrors | no_records | - | 3172 |
| side-mirrors | not_closed | no_list_manifest | 656 |
| side-mirrors | not_closed | no_year_manifest | 21576 |
| side-mirrors | not_closed | suspect_variant | 25 |
| side-mirrors | not_closed | uncrawled_chain_member | 136 |
| side-mirrors | not_closed | unread_sibling_page | 81 |
| starter | unmapped | - | 712 |
| starter | no_records | - | 2262 |
| starter | not_closed | no_list_manifest | 656 |
| starter | not_closed | no_year_manifest | 22509 |
| starter | not_closed | uncrawled_chain_member | 157 |
| starter | not_closed | unverified_product | 62 |
| tail-lights | unmapped | - | 712 |
| tail-lights | no_records | - | 7514 |
| tail-lights | not_closed | no_list_manifest | 437 |
| tail-lights | not_closed | no_year_manifest | 17453 |
| tail-lights | not_closed | unattested | 142 |
| tail-lights | not_closed | uncrawled_chain_member | 100 |
| throttle-body | unmapped | - | 712 |
| throttle-body | no_records | - | 3432 |
| throttle-body | not_closed | no_list_manifest | 569 |
| throttle-body | not_closed | no_year_manifest | 21403 |
| throttle-body | not_closed | unread_sibling_page | 219 |
| throttle-body | not_closed | unverified_product | 23 |
| tow-mirrors | unmapped | - | 712 |
| tow-mirrors | no_records | - | 25558 |
| tow-mirrors | not_closed | no_year_manifest | 88 |
| trunk-lid | unmapped | - | 712 |
| trunk-lid | no_records | - | 19681 |
| trunk-lid | not_closed | no_year_manifest | 5285 |
| trunk-lid | not_closed | unattested | 12 |
| trunk-lid | not_closed | uncrawled_chain_member | 668 |
| window-regulator | unmapped | - | 712 |
| window-regulator | no_records | - | 892 |
| window-regulator | not_closed | no_list_manifest | 656 |
| window-regulator | not_closed | no_year_manifest | 23856 |
| window-regulator | not_closed | unread_sibling_page | 242 |
| window-switch | unmapped | - | 712 |
| window-switch | no_records | - | 2390 |
| window-switch | not_closed | no_list_manifest | 574 |
| window-switch | not_closed | no_year_manifest | 22440 |
| window-switch | not_closed | unattested | 204 |
| window-switch | not_closed | uncrawled_chain_member | 38 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 712 |
| ac-compressor | no_records | - | 2012 |
| ac-compressor | split | option_split | 13819 |
| ac-compressor | conditional | conditional:body | 2 |
| ac-compressor | conditional | conditional:engine | 1191 |
| ac-compressor | conditional | conditional:engine_unattested | 1187 |
| ac-compressor | conditional | conditional:notes_not_own_page | 2648 |
| ac-compressor | conditional | conditional:option_layout | 495 |
| ac-compressor | conditional | conditional:qualifier | 1189 |
| ac-compressor | conditional | conditional:trim | 2912 |
| ac-compressor | gated | kind_not_phase1 | 191 |
| alternator | unmapped | - | 712 |
| alternator | no_records | - | 2591 |
| alternator | split | option_split | 18047 |
| alternator | conditional | conditional:engine_unattested | 771 |
| alternator | conditional | conditional:notes_not_own_page | 3329 |
| alternator | conditional | conditional:option_layout | 367 |
| alternator | conditional | conditional:production | 62 |
| alternator | conditional | conditional:trim | 189 |
| alternator | chain_member_conditional | chain_member_conditional | 151 |
| alternator | reman_only | reman_only | 139 |
| bumper-front | unmapped | - | 712 |
| bumper-front | no_records | - | 4951 |
| bumper-front | split | option_split | 14052 |
| bumper-front | conditional | conditional:engine | 263 |
| bumper-front | conditional | conditional:engine_unattested | 554 |
| bumper-front | conditional | conditional:notes_not_own_page | 1279 |
| bumper-front | conditional | conditional:option_layout | 65 |
| bumper-front | conditional | conditional:package | 43 |
| bumper-front | conditional | conditional:trim | 3571 |
| bumper-front | chain_member_conditional | chain_member_conditional | 19 |
| bumper-front | blocked | unexpected_position | 314 |
| bumper-front | eligible | - | 535 |
| bumper-rear | unmapped | - | 712 |
| bumper-rear | no_records | - | 2980 |
| bumper-rear | split | option_split | 12806 |
| bumper-rear | conditional | conditional:body | 315 |
| bumper-rear | conditional | conditional:engine | 781 |
| bumper-rear | conditional | conditional:engine_unattested | 1290 |
| bumper-rear | conditional | conditional:notes_not_own_page | 1964 |
| bumper-rear | conditional | conditional:trim | 4694 |
| bumper-rear | chain_member_conditional | chain_member_conditional | 19 |
| bumper-rear | blocked | unexpected_position | 309 |
| bumper-rear | eligible | - | 488 |
| climate-control | unmapped | - | 712 |
| climate-control | no_records | - | 10346 |
| climate-control | split | no_candidates | 230 |
| climate-control | split | option_split | 9898 |
| climate-control | conditional | conditional:engine_unattested | 280 |
| climate-control | conditional | conditional:engine_unparsed | 86 |
| climate-control | conditional | conditional:notes_not_own_page | 1064 |
| climate-control | conditional | conditional:option | 440 |
| climate-control | conditional | conditional:trim | 3011 |
| climate-control | eligible | - | 291 |
| door-front | unmapped | - | 712 |
| door-front | no_records | - | 2623 |
| door-front | split | option_split | 10712 |
| door-front | split | slot_missing | 1777 |
| door-front | conditional | conditional:engine | 388 |
| door-front | conditional | conditional:engine_unattested | 2110 |
| door-front | conditional | conditional:notes_not_own_page | 2723 |
| door-front | conditional | conditional:option_layout | 22 |
| door-front | conditional | conditional:plant | 58 |
| door-front | conditional | conditional:trim | 4237 |
| door-front | chain_member_conditional | chain_member_conditional | 139 |
| door-front | eligible | - | 857 |
| door-rear | unmapped | - | 712 |
| door-rear | no_records | - | 4240 |
| door-rear | split | option_split | 10452 |
| door-rear | split | slot_missing | 415 |
| door-rear | conditional | conditional:body | 72 |
| door-rear | conditional | conditional:engine | 560 |
| door-rear | conditional | conditional:engine_unattested | 1811 |
| door-rear | conditional | conditional:notes_not_own_page | 1805 |
| door-rear | conditional | conditional:option | 260 |
| door-rear | conditional | conditional:trim | 5552 |
| door-rear | eligible | - | 479 |
| fender | unmapped | - | 712 |
| fender | no_records | - | 6728 |
| fender | split | option_split | 6711 |
| fender | split | slot_missing | 562 |
| fender | conditional | conditional:engine | 263 |
| fender | conditional | conditional:engine_unattested | 1963 |
| fender | conditional | conditional:notes_not_own_page | 2345 |
| fender | conditional | conditional:option_layout | 356 |
| fender | conditional | conditional:package | 134 |
| fender | conditional | conditional:trim | 5903 |
| fender | chain_member_conditional | chain_member_conditional | 101 |
| fender | eligible | - | 580 |
| fuel-pump-module | unmapped | - | 712 |
| fuel-pump-module | no_records | - | 11575 |
| fuel-pump-module | split | no_candidates | 131 |
| fuel-pump-module | split | option_split | 8677 |
| fuel-pump-module | conditional | conditional:engine | 145 |
| fuel-pump-module | conditional | conditional:engine_unattested | 501 |
| fuel-pump-module | conditional | conditional:notes_not_own_page | 1962 |
| fuel-pump-module | conditional | conditional:option_layout | 314 |
| fuel-pump-module | conditional | conditional:plant | 58 |
| fuel-pump-module | conditional | conditional:qualifier | 1279 |
| fuel-pump-module | conditional | conditional:trim | 938 |
| fuel-pump-module | gated | kind_not_phase1 | 66 |
| gauge-cluster | unmapped | - | 712 |
| gauge-cluster | no_records | - | 13670 |
| gauge-cluster | split | no_candidates | 254 |
| gauge-cluster | split | option_split | 11383 |
| gauge-cluster | conditional | conditional:engine | 146 |
| gauge-cluster | conditional | conditional:notes_not_own_page | 82 |
| gauge-cluster | conditional | conditional:trim | 38 |
| gauge-cluster | eligible | - | 73 |
| grille | unmapped | - | 712 |
| grille | no_records | - | 6133 |
| grille | split | option_split | 15437 |
| grille | conditional | conditional:engine | 34 |
| grille | conditional | conditional:engine_unattested | 391 |
| grille | conditional | conditional:engine_unparsed | 86 |
| grille | conditional | conditional:notes_not_own_page | 805 |
| grille | conditional | conditional:trim | 2317 |
| grille | eligible | - | 443 |
| headlights | unmapped | - | 712 |
| headlights | no_records | - | 4930 |
| headlights | split | option_split | 13795 |
| headlights | split | slot_missing | 69 |
| headlights | conditional | conditional:engine | 326 |
| headlights | conditional | conditional:engine_unattested | 104 |
| headlights | conditional | conditional:engine_unparsed | 86 |
| headlights | conditional | conditional:notes_not_own_page | 1445 |
| headlights | conditional | conditional:option | 304 |
| headlights | conditional | conditional:plant | 133 |
| headlights | conditional | conditional:qualifier | 2 |
| headlights | conditional | conditional:trim | 3414 |
| headlights | chain_member_conditional | chain_member_conditional | 174 |
| headlights | eligible | - | 864 |
| hood | unmapped | - | 712 |
| hood | no_records | - | 2137 |
| hood | split | option_split | 4220 |
| hood | conditional | conditional:engine | 758 |
| hood | conditional | conditional:engine_unattested | 2209 |
| hood | conditional | conditional:engine_unparsed | 86 |
| hood | conditional | conditional:notes_not_own_page | 3973 |
| hood | conditional | conditional:option | 107 |
| hood | conditional | conditional:package | 134 |
| hood | conditional | conditional:plant | 249 |
| hood | conditional | conditional:trim | 10175 |
| hood | chain_member_conditional | chain_member_conditional | 224 |
| hood | eligible | - | 1374 |
| ignition-coils | unmapped | - | 712 |
| ignition-coils | no_records | - | 623 |
| ignition-coils | split | option_split | 18691 |
| ignition-coils | conditional | conditional:engine | 937 |
| ignition-coils | conditional | conditional:engine_unattested | 1029 |
| ignition-coils | conditional | conditional:notes_not_own_page | 2251 |
| ignition-coils | conditional | conditional:package | 552 |
| ignition-coils | conditional | conditional:trim | 1544 |
| ignition-coils | eligible | - | 19 |
| liftgate | unmapped | - | 712 |
| liftgate | no_records | - | 24950 |
| liftgate | split | option_split | 637 |
| liftgate | conditional | conditional:engine_unattested | 59 |
| power-steering-pump | unmapped | - | 712 |
| power-steering-pump | no_records | - | 15933 |
| power-steering-pump | split | option_split | 4419 |
| power-steering-pump | conditional | conditional:engine_unattested | 1073 |
| power-steering-pump | conditional | conditional:notes_not_own_page | 2454 |
| power-steering-pump | conditional | conditional:option_layout | 1767 |
| radiator | unmapped | - | 712 |
| radiator | no_records | - | 2586 |
| radiator | split | option_split | 21187 |
| radiator | conditional | conditional:engine | 120 |
| radiator | conditional | conditional:engine_unattested | 664 |
| radiator | conditional | conditional:notes_not_own_page | 361 |
| radiator | conditional | conditional:trans | 215 |
| radiator | conditional | conditional:trim | 513 |
| side-mirrors | unmapped | - | 712 |
| side-mirrors | no_records | - | 3172 |
| side-mirrors | split | option_split | 21712 |
| side-mirrors | split | slot_missing | 22 |
| side-mirrors | conditional | conditional:engine | 10 |
| side-mirrors | conditional | conditional:notes_not_own_page | 98 |
| side-mirrors | conditional | conditional:trim | 585 |
| side-mirrors | eligible | - | 47 |
| starter | unmapped | - | 712 |
| starter | no_records | - | 2262 |
| starter | split | option_split | 15586 |
| starter | conditional | conditional:engine | 205 |
| starter | conditional | conditional:engine_unattested | 1055 |
| starter | conditional | conditional:notes_not_own_page | 4214 |
| starter | conditional | conditional:option_layout | 1230 |
| starter | conditional | conditional:plant | 388 |
| starter | conditional | conditional:trim | 573 |
| starter | chain_member_conditional | chain_member_conditional | 47 |
| starter | reman_only | reman_only | 86 |
| tail-lights | unmapped | - | 712 |
| tail-lights | no_records | - | 7514 |
| tail-lights | split | no_candidates | 38 |
| tail-lights | split | option_split | 10450 |
| tail-lights | split | slot_missing | 343 |
| tail-lights | conditional | conditional:engine | 107 |
| tail-lights | conditional | conditional:engine_unattested | 698 |
| tail-lights | conditional | conditional:engine_unparsed | 86 |
| tail-lights | conditional | conditional:notes_not_own_page | 840 |
| tail-lights | conditional | conditional:plant | 897 |
| tail-lights | conditional | conditional:position | 112 |
| tail-lights | conditional | conditional:trim | 4152 |
| tail-lights | eligible | - | 409 |
| throttle-body | unmapped | - | 712 |
| throttle-body | no_records | - | 3432 |
| throttle-body | split | option_split | 13621 |
| throttle-body | conditional | conditional:engine | 928 |
| throttle-body | conditional | conditional:engine_unattested | 963 |
| throttle-body | conditional | conditional:notes_not_own_page | 1690 |
| throttle-body | conditional | conditional:plant | 268 |
| throttle-body | conditional | conditional:qualifier | 801 |
| throttle-body | conditional | conditional:trim | 3218 |
| throttle-body | conditional | conditional:unknown | 139 |
| throttle-body | gated | kind_not_phase1 | 586 |
| tow-mirrors | unmapped | - | 712 |
| tow-mirrors | no_records | - | 25558 |
| tow-mirrors | conditional | conditional:notes_not_own_page | 46 |
| tow-mirrors | conditional | conditional:package | 42 |
| trunk-lid | unmapped | - | 712 |
| trunk-lid | no_records | - | 19681 |
| trunk-lid | split | option_split | 4222 |
| trunk-lid | conditional | conditional:engine_unattested | 231 |
| trunk-lid | conditional | conditional:notes_not_own_page | 1159 |
| trunk-lid | conditional | conditional:option_layout | 350 |
| trunk-lid | conditional | conditional:trim | 3 |
| window-regulator | unmapped | - | 712 |
| window-regulator | no_records | - | 892 |
| window-regulator | split | packaging_incomplete | 885 |
| window-regulator | split | packaging_split | 12741 |
| window-regulator | split | packaging_unstated | 10084 |
| window-regulator | split | position_missing | 333 |
| window-regulator | conditional | conditional:engine_unattested | 383 |
| window-regulator | conditional | conditional:trim | 64 |
| window-regulator | eligible | - | 264 |
| window-switch | unmapped | - | 712 |
| window-switch | no_records | - | 2390 |
| window-switch | split | no_candidates | 104 |
| window-switch | split | option_split | 10832 |
| window-switch | split | position_missing | 3543 |
| window-switch | conditional | conditional:engine | 865 |
| window-switch | conditional | conditional:engine_unattested | 38 |
| window-switch | conditional | conditional:notes_not_own_page | 2449 |
| window-switch | conditional | conditional:option | 26 |
| window-switch | conditional | conditional:plant | 391 |
| window-switch | conditional | conditional:position | 213 |
| window-switch | conditional | conditional:trim | 4651 |
| window-switch | eligible | - | 144 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 50
- disputed_class: 44
- evidence_mismatch: 6
- recrawl_resolved: 2
- systemic_evidence_failure: 1
- universal_part_suspect: 7

## Unknown note clauses (top 30)

- `Part Name Code: 87910`: 579
- `Part Name Code: 87940`: 550
- `Part Name Code: 87901B`: 263
- `Part Name Code: 87906B`: 257
- `Part Name Code: 83100`: 191
- `PAINT REQ.`: 142
- `Part Name Code: 81175`: 135
- `Part Name Code: 81135`: 127
- `Part Name Code: 52119A`: 118
- `GYL1#.. JPP`: 106
- `UZS190`: 106
- `GSE20`: 103
- `21.. ATM`: 77
- `MERCURY GRAY MC.`: 75
- `OEM`: 75
- `Part Name Code: 64401`: 71
- `Part Name Code: 53111`: 65
- `21`: 64
- `CANADA SPEC&F PACKAGE&FRONT SEAT-F SPORTS PACKAGE (LEATHER, POWER SEAT)&EMV & NAVIGATION SYSTEM-WITH(HDD NAVIGATION)`: 64
- `DK.BLUE MC. CC.`: 64
- `PREMIUM PACKAGE&W(MEMORY MIRROR)`: 64
- `Mvp`: 63
- `STARLIGHT BLACK GF.`: 63
- `LAPIS LAZULI MC.`: 62
- `Without Double Cab`: 62
- `GSU3#.. JPP`: 60
- `GSE2#.. ATM`: 59
- `BLUISH PEARL CS.`: 58
- `SILVERY BLUE ME.`: 57
- `KOREA SPEC&LUXURY PACKAGE&FRONT SEAT-SEMIANILINE VENTILATED LEATHER`: 56

## Unmapped catalog models

- Lexus GS Turbo: feed 'GS Turbo' 0 cars
- Lexus GS200t: feed 'GS 200t' 0 cars
- Lexus GX460: feed 'GX 460' 0 cars
- Lexus IS F: feed 'IS F' 0 cars (excluded: catalog model with no feed cars as 'IS F' (inventory 2026-11-04); nothing to map)
- Lexus IS Turbo: feed 'IS Turbo' 0 cars
- Lexus LS400: feed 'LS 400' 121 cars
- Lexus LS600hL: feed 'LS 600h L' 1 cars (excluded: M6: the only feed 'LS 600h L' car decodes as another make (vPIC mismatch))
- Lexus LX470: feed 'LX 470' 4 cars
- Lexus LX570: feed 'LX 570' 0 cars
- Lexus NX200t: feed 'NX 200t' 0 cars
- Lexus NX300: feed 'NX 300' 0 cars
- Lexus NX300h: feed 'NX 300h' 0 cars
- Lexus RC Turbo: feed 'RC Turbo' 0 cars
- Lexus RC200t: feed 'RC 200t' 0 cars
- Lexus RC300: feed 'RC 300' 0 cars
- Lexus SC300: feed 'SC 300' 10 cars
- Lexus SC400: feed 'SC 400' 19 cars
- Toyota C-HR: feed 'C-HR' 12 cars
- Toyota Corolla Cross: feed 'Corolla Cross' 0 cars
- Toyota Crown: feed 'Crown' 0 cars
- Toyota Crown Signia: feed 'Crown Signia' 0 cars
- Toyota GR Corolla: feed 'GR Corolla' 0 cars
- Toyota Grand Highlander: feed 'Grand Highlander' 0 cars
- Toyota Prius AWD-e: feed 'Prius AWD-e' 0 cars (excluded: catalog model with no feed cars as 'Prius AWD-e' (inventory 2026-11-04); nothing to map)
- Toyota RAV4 Prime: feed 'RAV4 Prime' 0 cars
- Toyota T100: feed 'T100' 57 cars
