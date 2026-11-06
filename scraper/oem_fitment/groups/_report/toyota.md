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
| ac-compressor | unmapped | - | 710 |
| ac-compressor | no_records | - | 2007 |
| ac-compressor | not_closed | no_list_manifest | 657 |
| ac-compressor | not_closed | no_year_manifest | 22684 |
| ac-compressor | not_closed | uncrawled_chain_member | 157 |
| ac-compressor | not_closed | unverified_product | 83 |
| alternator | unmapped | - | 710 |
| alternator | no_records | - | 2578 |
| alternator | not_closed | no_list_manifest | 657 |
| alternator | not_closed | no_year_manifest | 22136 |
| alternator | not_closed | uncrawled_chain_member | 129 |
| alternator | not_closed | unread_sibling_page | 28 |
| alternator | not_closed | unverified_product | 60 |
| bumper-front | unmapped | - | 710 |
| bumper-front | no_records | - | 4946 |
| bumper-front | not_closed | no_year_manifest | 19743 |
| bumper-front | not_closed | unread_sibling_page | 899 |
| bumper-rear | unmapped | - | 710 |
| bumper-rear | no_records | - | 2975 |
| bumper-rear | not_closed | no_year_manifest | 21714 |
| bumper-rear | not_closed | unread_sibling_page | 899 |
| climate-control | unmapped | - | 710 |
| climate-control | no_records | - | 10337 |
| climate-control | not_closed | no_list_manifest | 156 |
| climate-control | not_closed | no_year_manifest | 14855 |
| climate-control | not_closed | unread_sibling_page | 240 |
| door-front | unmapped | - | 710 |
| door-front | no_records | - | 2618 |
| door-front | not_closed | no_year_manifest | 22071 |
| door-front | not_closed | unread_sibling_page | 899 |
| door-rear | unmapped | - | 710 |
| door-rear | no_records | - | 4234 |
| door-rear | not_closed | no_year_manifest | 20465 |
| door-rear | not_closed | unread_sibling_page | 889 |
| fender | unmapped | - | 710 |
| fender | no_records | - | 6724 |
| fender | not_closed | no_year_manifest | 17965 |
| fender | not_closed | unread_sibling_page | 899 |
| fuel-pump-module | unmapped | - | 710 |
| fuel-pump-module | no_records | - | 11549 |
| fuel-pump-module | not_closed | no_list_manifest | 148 |
| fuel-pump-module | not_closed | no_year_manifest | 13651 |
| fuel-pump-module | not_closed | unread_sibling_page | 240 |
| gauge-cluster | unmapped | - | 710 |
| gauge-cluster | no_records | - | 13647 |
| gauge-cluster | not_closed | no_year_manifest | 11042 |
| gauge-cluster | not_closed | unread_sibling_page | 899 |
| grille | unmapped | - | 710 |
| grille | no_records | - | 6123 |
| grille | not_closed | no_year_manifest | 18566 |
| grille | not_closed | unattested | 471 |
| grille | not_closed | uncrawled_chain_member | 428 |
| headlights | unmapped | - | 710 |
| headlights | no_records | - | 4927 |
| headlights | not_closed | no_list_manifest | 655 |
| headlights | not_closed | no_year_manifest | 19766 |
| headlights | not_closed | unread_sibling_page | 240 |
| hood | unmapped | - | 710 |
| hood | no_records | - | 2136 |
| hood | not_closed | no_year_manifest | 22553 |
| hood | not_closed | unread_sibling_page | 899 |
| ignition-coils | unmapped | - | 710 |
| ignition-coils | no_records | - | 627 |
| ignition-coils | not_closed | no_year_manifest | 24062 |
| ignition-coils | not_closed | unattested | 49 |
| ignition-coils | not_closed | uncrawled_chain_member | 129 |
| ignition-coils | not_closed | unverified_product | 721 |
| liftgate | unmapped | - | 710 |
| liftgate | no_records | - | 24896 |
| liftgate | not_closed | no_year_manifest | 452 |
| liftgate | not_closed | unattested | 108 |
| liftgate | not_closed | uncrawled_chain_member | 132 |
| power-steering-pump | unmapped | - | 710 |
| power-steering-pump | no_records | - | 15907 |
| power-steering-pump | not_closed | no_list_manifest | 509 |
| power-steering-pump | not_closed | no_year_manifest | 9040 |
| power-steering-pump | not_closed | unread_sibling_page | 132 |
| radiator | unmapped | - | 710 |
| radiator | no_records | - | 2580 |
| radiator | not_closed | no_year_manifest | 22109 |
| radiator | not_closed | unread_sibling_page | 899 |
| side-mirrors | unmapped | - | 710 |
| side-mirrors | no_records | - | 3164 |
| side-mirrors | not_closed | no_list_manifest | 657 |
| side-mirrors | not_closed | no_year_manifest | 21527 |
| side-mirrors | not_closed | suspect_variant | 26 |
| side-mirrors | not_closed | uncrawled_chain_member | 133 |
| side-mirrors | not_closed | unread_sibling_page | 81 |
| starter | unmapped | - | 710 |
| starter | no_records | - | 2251 |
| starter | not_closed | no_list_manifest | 657 |
| starter | not_closed | no_year_manifest | 22463 |
| starter | not_closed | uncrawled_chain_member | 157 |
| starter | not_closed | unverified_product | 60 |
| tail-lights | unmapped | - | 710 |
| tail-lights | no_records | - | 7496 |
| tail-lights | not_closed | no_list_manifest | 437 |
| tail-lights | not_closed | no_year_manifest | 17415 |
| tail-lights | not_closed | unattested | 142 |
| tail-lights | not_closed | uncrawled_chain_member | 98 |
| throttle-body | unmapped | - | 710 |
| throttle-body | no_records | - | 3431 |
| throttle-body | not_closed | no_list_manifest | 570 |
| throttle-body | not_closed | no_year_manifest | 21347 |
| throttle-body | not_closed | unread_sibling_page | 217 |
| throttle-body | not_closed | unverified_product | 23 |
| tow-mirrors | unmapped | - | 710 |
| tow-mirrors | no_records | - | 25502 |
| tow-mirrors | not_closed | no_year_manifest | 86 |
| trunk-lid | unmapped | - | 710 |
| trunk-lid | no_records | - | 19647 |
| trunk-lid | not_closed | no_year_manifest | 5260 |
| trunk-lid | not_closed | unattested | 12 |
| trunk-lid | not_closed | uncrawled_chain_member | 669 |
| window-regulator | unmapped | - | 710 |
| window-regulator | no_records | - | 890 |
| window-regulator | not_closed | no_list_manifest | 657 |
| window-regulator | not_closed | no_year_manifest | 23801 |
| window-regulator | not_closed | unread_sibling_page | 240 |
| window-switch | unmapped | - | 710 |
| window-switch | no_records | - | 2377 |
| window-switch | not_closed | no_list_manifest | 574 |
| window-switch | not_closed | no_year_manifest | 22397 |
| window-switch | not_closed | unattested | 202 |
| window-switch | not_closed | uncrawled_chain_member | 38 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 710 |
| ac-compressor | no_records | - | 2007 |
| ac-compressor | split | option_split | 13788 |
| ac-compressor | conditional | conditional:body | 2 |
| ac-compressor | conditional | conditional:engine | 1191 |
| ac-compressor | conditional | conditional:engine_unattested | 1187 |
| ac-compressor | conditional | conditional:notes_not_own_page | 2648 |
| ac-compressor | conditional | conditional:option_layout | 496 |
| ac-compressor | conditional | conditional:qualifier | 1181 |
| ac-compressor | conditional | conditional:trim | 2898 |
| ac-compressor | gated | kind_not_phase1 | 190 |
| alternator | unmapped | - | 710 |
| alternator | no_records | - | 2578 |
| alternator | split | option_split | 17996 |
| alternator | conditional | conditional:engine_unattested | 770 |
| alternator | conditional | conditional:notes_not_own_page | 3338 |
| alternator | conditional | conditional:option_layout | 368 |
| alternator | conditional | conditional:production | 62 |
| alternator | conditional | conditional:trim | 189 |
| alternator | chain_member_conditional | chain_member_conditional | 149 |
| alternator | reman_only | reman_only | 138 |
| bumper-front | unmapped | - | 710 |
| bumper-front | no_records | - | 4946 |
| bumper-front | split | option_split | 14012 |
| bumper-front | conditional | conditional:engine | 262 |
| bumper-front | conditional | conditional:engine_unattested | 551 |
| bumper-front | conditional | conditional:notes_not_own_page | 1279 |
| bumper-front | conditional | conditional:option_layout | 65 |
| bumper-front | conditional | conditional:package | 42 |
| bumper-front | conditional | conditional:trim | 3565 |
| bumper-front | chain_member_conditional | chain_member_conditional | 19 |
| bumper-front | blocked | unexpected_position | 313 |
| bumper-front | eligible | - | 534 |
| bumper-rear | unmapped | - | 710 |
| bumper-rear | no_records | - | 2975 |
| bumper-rear | split | option_split | 12774 |
| bumper-rear | conditional | conditional:body | 318 |
| bumper-rear | conditional | conditional:engine | 777 |
| bumper-rear | conditional | conditional:engine_unattested | 1286 |
| bumper-rear | conditional | conditional:notes_not_own_page | 1963 |
| bumper-rear | conditional | conditional:trim | 4682 |
| bumper-rear | chain_member_conditional | chain_member_conditional | 19 |
| bumper-rear | blocked | unexpected_position | 307 |
| bumper-rear | eligible | - | 487 |
| climate-control | unmapped | - | 710 |
| climate-control | no_records | - | 10337 |
| climate-control | split | no_candidates | 228 |
| climate-control | split | option_split | 9871 |
| climate-control | conditional | conditional:engine_unattested | 277 |
| climate-control | conditional | conditional:engine_unparsed | 87 |
| climate-control | conditional | conditional:notes_not_own_page | 1062 |
| climate-control | conditional | conditional:option | 434 |
| climate-control | conditional | conditional:trim | 3002 |
| climate-control | eligible | - | 290 |
| door-front | unmapped | - | 710 |
| door-front | no_records | - | 2618 |
| door-front | split | option_split | 10680 |
| door-front | split | slot_missing | 1779 |
| door-front | conditional | conditional:engine | 385 |
| door-front | conditional | conditional:engine_unattested | 2108 |
| door-front | conditional | conditional:notes_not_own_page | 2723 |
| door-front | conditional | conditional:option_layout | 22 |
| door-front | conditional | conditional:plant | 58 |
| door-front | conditional | conditional:trim | 4221 |
| door-front | chain_member_conditional | chain_member_conditional | 138 |
| door-front | eligible | - | 856 |
| door-rear | unmapped | - | 710 |
| door-rear | no_records | - | 4234 |
| door-rear | split | option_split | 10424 |
| door-rear | split | slot_missing | 416 |
| door-rear | conditional | conditional:body | 71 |
| door-rear | conditional | conditional:engine | 557 |
| door-rear | conditional | conditional:engine_unattested | 1810 |
| door-rear | conditional | conditional:notes_not_own_page | 1807 |
| door-rear | conditional | conditional:option | 260 |
| door-rear | conditional | conditional:trim | 5531 |
| door-rear | eligible | - | 478 |
| fender | unmapped | - | 710 |
| fender | no_records | - | 6724 |
| fender | split | option_split | 6701 |
| fender | split | slot_missing | 563 |
| fender | conditional | conditional:engine | 262 |
| fender | conditional | conditional:engine_unattested | 1960 |
| fender | conditional | conditional:notes_not_own_page | 2340 |
| fender | conditional | conditional:option_layout | 351 |
| fender | conditional | conditional:package | 132 |
| fender | conditional | conditional:trim | 5877 |
| fender | chain_member_conditional | chain_member_conditional | 101 |
| fender | eligible | - | 577 |
| fuel-pump-module | unmapped | - | 710 |
| fuel-pump-module | no_records | - | 11549 |
| fuel-pump-module | split | no_candidates | 130 |
| fuel-pump-module | split | option_split | 8656 |
| fuel-pump-module | conditional | conditional:engine | 142 |
| fuel-pump-module | conditional | conditional:engine_unattested | 501 |
| fuel-pump-module | conditional | conditional:notes_not_own_page | 1964 |
| fuel-pump-module | conditional | conditional:option_layout | 315 |
| fuel-pump-module | conditional | conditional:plant | 58 |
| fuel-pump-module | conditional | conditional:qualifier | 1279 |
| fuel-pump-module | conditional | conditional:trim | 928 |
| fuel-pump-module | gated | kind_not_phase1 | 66 |
| gauge-cluster | unmapped | - | 710 |
| gauge-cluster | no_records | - | 13647 |
| gauge-cluster | split | no_candidates | 252 |
| gauge-cluster | split | option_split | 11352 |
| gauge-cluster | conditional | conditional:engine | 145 |
| gauge-cluster | conditional | conditional:notes_not_own_page | 80 |
| gauge-cluster | conditional | conditional:trim | 39 |
| gauge-cluster | eligible | - | 73 |
| grille | unmapped | - | 710 |
| grille | no_records | - | 6123 |
| grille | split | option_split | 15398 |
| grille | conditional | conditional:engine | 34 |
| grille | conditional | conditional:engine_unattested | 390 |
| grille | conditional | conditional:engine_unparsed | 87 |
| grille | conditional | conditional:notes_not_own_page | 802 |
| grille | conditional | conditional:trim | 2312 |
| grille | eligible | - | 442 |
| headlights | unmapped | - | 710 |
| headlights | no_records | - | 4927 |
| headlights | split | option_split | 13753 |
| headlights | split | slot_missing | 69 |
| headlights | conditional | conditional:engine | 322 |
| headlights | conditional | conditional:engine_unattested | 104 |
| headlights | conditional | conditional:engine_unparsed | 87 |
| headlights | conditional | conditional:notes_not_own_page | 1444 |
| headlights | conditional | conditional:option | 300 |
| headlights | conditional | conditional:plant | 135 |
| headlights | conditional | conditional:qualifier | 1 |
| headlights | conditional | conditional:trim | 3407 |
| headlights | chain_member_conditional | chain_member_conditional | 175 |
| headlights | eligible | - | 864 |
| hood | unmapped | - | 710 |
| hood | no_records | - | 2136 |
| hood | split | option_split | 4206 |
| hood | conditional | conditional:engine | 755 |
| hood | conditional | conditional:engine_unattested | 2206 |
| hood | conditional | conditional:engine_unparsed | 87 |
| hood | conditional | conditional:notes_not_own_page | 3973 |
| hood | conditional | conditional:option | 107 |
| hood | conditional | conditional:package | 132 |
| hood | conditional | conditional:plant | 247 |
| hood | conditional | conditional:trim | 10141 |
| hood | chain_member_conditional | chain_member_conditional | 225 |
| hood | eligible | - | 1373 |
| ignition-coils | unmapped | - | 710 |
| ignition-coils | no_records | - | 627 |
| ignition-coils | split | option_split | 18636 |
| ignition-coils | conditional | conditional:engine | 937 |
| ignition-coils | conditional | conditional:engine_unattested | 1028 |
| ignition-coils | conditional | conditional:notes_not_own_page | 2248 |
| ignition-coils | conditional | conditional:package | 552 |
| ignition-coils | conditional | conditional:trim | 1541 |
| ignition-coils | eligible | - | 19 |
| liftgate | unmapped | - | 710 |
| liftgate | no_records | - | 24896 |
| liftgate | split | option_split | 634 |
| liftgate | conditional | conditional:engine_unattested | 58 |
| power-steering-pump | unmapped | - | 710 |
| power-steering-pump | no_records | - | 15907 |
| power-steering-pump | split | option_split | 4402 |
| power-steering-pump | conditional | conditional:engine_unattested | 1070 |
| power-steering-pump | conditional | conditional:notes_not_own_page | 2452 |
| power-steering-pump | conditional | conditional:option_layout | 1757 |
| radiator | unmapped | - | 710 |
| radiator | no_records | - | 2580 |
| radiator | split | option_split | 21134 |
| radiator | conditional | conditional:engine | 120 |
| radiator | conditional | conditional:engine_unattested | 661 |
| radiator | conditional | conditional:notes_not_own_page | 364 |
| radiator | conditional | conditional:trans | 213 |
| radiator | conditional | conditional:trim | 516 |
| side-mirrors | unmapped | - | 710 |
| side-mirrors | no_records | - | 3164 |
| side-mirrors | split | option_split | 21663 |
| side-mirrors | split | slot_missing | 22 |
| side-mirrors | conditional | conditional:engine | 10 |
| side-mirrors | conditional | conditional:notes_not_own_page | 98 |
| side-mirrors | conditional | conditional:trim | 584 |
| side-mirrors | eligible | - | 47 |
| starter | unmapped | - | 710 |
| starter | no_records | - | 2251 |
| starter | split | option_split | 15534 |
| starter | conditional | conditional:engine | 205 |
| starter | conditional | conditional:engine_unattested | 1055 |
| starter | conditional | conditional:notes_not_own_page | 4225 |
| starter | conditional | conditional:option_layout | 1225 |
| starter | conditional | conditional:plant | 385 |
| starter | conditional | conditional:trim | 573 |
| starter | chain_member_conditional | chain_member_conditional | 47 |
| starter | reman_only | reman_only | 88 |
| tail-lights | unmapped | - | 710 |
| tail-lights | no_records | - | 7496 |
| tail-lights | split | no_candidates | 38 |
| tail-lights | split | option_split | 10430 |
| tail-lights | split | slot_missing | 344 |
| tail-lights | conditional | conditional:engine | 105 |
| tail-lights | conditional | conditional:engine_unattested | 696 |
| tail-lights | conditional | conditional:engine_unparsed | 87 |
| tail-lights | conditional | conditional:notes_not_own_page | 839 |
| tail-lights | conditional | conditional:plant | 892 |
| tail-lights | conditional | conditional:position | 113 |
| tail-lights | conditional | conditional:trim | 4143 |
| tail-lights | eligible | - | 405 |
| throttle-body | unmapped | - | 710 |
| throttle-body | no_records | - | 3431 |
| throttle-body | split | option_split | 13581 |
| throttle-body | conditional | conditional:engine | 930 |
| throttle-body | conditional | conditional:engine_unattested | 963 |
| throttle-body | conditional | conditional:notes_not_own_page | 1688 |
| throttle-body | conditional | conditional:plant | 265 |
| throttle-body | conditional | conditional:qualifier | 801 |
| throttle-body | conditional | conditional:trim | 3205 |
| throttle-body | conditional | conditional:unknown | 138 |
| throttle-body | gated | kind_not_phase1 | 586 |
| tow-mirrors | unmapped | - | 710 |
| tow-mirrors | no_records | - | 25502 |
| tow-mirrors | conditional | conditional:notes_not_own_page | 46 |
| tow-mirrors | conditional | conditional:package | 40 |
| trunk-lid | unmapped | - | 710 |
| trunk-lid | no_records | - | 19647 |
| trunk-lid | split | option_split | 4211 |
| trunk-lid | conditional | conditional:engine_unattested | 229 |
| trunk-lid | conditional | conditional:notes_not_own_page | 1150 |
| trunk-lid | conditional | conditional:option_layout | 348 |
| trunk-lid | conditional | conditional:trim | 3 |
| window-regulator | unmapped | - | 710 |
| window-regulator | no_records | - | 890 |
| window-regulator | split | packaging_incomplete | 884 |
| window-regulator | split | packaging_split | 12708 |
| window-regulator | split | packaging_unstated | 10064 |
| window-regulator | split | position_missing | 333 |
| window-regulator | conditional | conditional:engine_unattested | 383 |
| window-regulator | conditional | conditional:trim | 64 |
| window-regulator | eligible | - | 262 |
| window-switch | unmapped | - | 710 |
| window-switch | no_records | - | 2377 |
| window-switch | split | no_candidates | 103 |
| window-switch | split | option_split | 10794 |
| window-switch | split | position_missing | 3542 |
| window-switch | conditional | conditional:engine | 860 |
| window-switch | conditional | conditional:engine_unattested | 37 |
| window-switch | conditional | conditional:notes_not_own_page | 2456 |
| window-switch | conditional | conditional:option | 26 |
| window-switch | conditional | conditional:plant | 388 |
| window-switch | conditional | conditional:position | 214 |
| window-switch | conditional | conditional:trim | 4648 |
| window-switch | eligible | - | 143 |

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
- Lexus LS400: feed 'LS 400' 123 cars
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
