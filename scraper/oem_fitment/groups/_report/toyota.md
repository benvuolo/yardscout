# OEM curation report: toyota

Raw: `ceccc800d7ba22c0291121baabb0a9292eb8f271` @ `ceccc800d7ba`; as of 2026-11-05T22:28:21Z.

- records 5729, classes 5692, list rows 13739, year manifests 31, cells 7793
- Verified groups 0, engine vg groups 0, Likely groups 1506
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.lexuspartsnow.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.lexuspartsnow.com: only 0% of its 3984 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 708 |
| ac-compressor | no_records | - | 2002 |
| ac-compressor | not_closed | no_list_manifest | 405 |
| ac-compressor | not_closed | no_year_manifest | 22948 |
| ac-compressor | not_closed | uncrawled_chain_member | 156 |
| ac-compressor | not_closed | unverified_product | 87 |
| alternator | unmapped | - | 708 |
| alternator | no_records | - | 2577 |
| alternator | not_closed | no_list_manifest | 405 |
| alternator | not_closed | no_year_manifest | 22398 |
| alternator | not_closed | uncrawled_chain_member | 128 |
| alternator | not_closed | unread_sibling_page | 28 |
| alternator | not_closed | unverified_product | 62 |
| bumper-front | unmapped | - | 708 |
| bumper-front | no_records | - | 5898 |
| bumper-front | not_closed | no_list_manifest | 16 |
| bumper-front | not_closed | no_year_manifest | 19279 |
| bumper-front | not_closed | unread_sibling_page | 405 |
| bumper-rear | unmapped | - | 708 |
| bumper-rear | no_records | - | 3876 |
| bumper-rear | not_closed | no_list_manifest | 16 |
| bumper-rear | not_closed | no_year_manifest | 21301 |
| bumper-rear | not_closed | unread_sibling_page | 405 |
| climate-control | unmapped | - | 708 |
| climate-control | no_records | - | 10346 |
| climate-control | not_closed | no_list_manifest | 139 |
| climate-control | not_closed | no_year_manifest | 14870 |
| climate-control | not_closed | unread_sibling_page | 243 |
| door-front | unmapped | - | 708 |
| door-front | no_records | - | 3457 |
| door-front | not_closed | no_list_manifest | 16 |
| door-front | not_closed | no_year_manifest | 21720 |
| door-front | not_closed | unread_sibling_page | 405 |
| door-rear | unmapped | - | 708 |
| door-rear | no_records | - | 5146 |
| door-rear | not_closed | no_list_manifest | 16 |
| door-rear | not_closed | no_year_manifest | 20031 |
| door-rear | not_closed | unread_sibling_page | 405 |
| fender | unmapped | - | 708 |
| fender | no_records | - | 7577 |
| fender | not_closed | no_list_manifest | 16 |
| fender | not_closed | no_year_manifest | 17600 |
| fender | not_closed | unread_sibling_page | 405 |
| fuel-pump-module | unmapped | - | 708 |
| fuel-pump-module | no_records | - | 11544 |
| fuel-pump-module | not_closed | no_list_manifest | 68 |
| fuel-pump-module | not_closed | no_year_manifest | 13743 |
| fuel-pump-module | not_closed | unread_sibling_page | 243 |
| gauge-cluster | unmapped | - | 708 |
| gauge-cluster | no_records | - | 14369 |
| gauge-cluster | not_closed | no_list_manifest | 16 |
| gauge-cluster | not_closed | no_year_manifest | 10808 |
| gauge-cluster | not_closed | unread_sibling_page | 405 |
| grille | unmapped | - | 708 |
| grille | no_records | - | 7080 |
| grille | not_closed | no_list_manifest | 16 |
| grille | not_closed | no_year_manifest | 18097 |
| grille | not_closed | unattested | 140 |
| grille | not_closed | uncrawled_chain_member | 265 |
| headlights | unmapped | - | 708 |
| headlights | no_records | - | 4928 |
| headlights | not_closed | no_list_manifest | 405 |
| headlights | not_closed | no_year_manifest | 20022 |
| headlights | not_closed | unread_sibling_page | 243 |
| hood | unmapped | - | 708 |
| hood | no_records | - | 3127 |
| hood | not_closed | no_list_manifest | 16 |
| hood | not_closed | no_year_manifest | 22050 |
| hood | not_closed | unread_sibling_page | 405 |
| ignition-coils | unmapped | - | 708 |
| ignition-coils | no_records | - | 1384 |
| ignition-coils | not_closed | no_list_manifest | 85 |
| ignition-coils | not_closed | no_year_manifest | 23724 |
| ignition-coils | not_closed | uncrawled_chain_member | 68 |
| ignition-coils | not_closed | unverified_product | 337 |
| liftgate | unmapped | - | 708 |
| liftgate | no_records | - | 25250 |
| liftgate | not_closed | no_year_manifest | 261 |
| liftgate | not_closed | unattested | 87 |
| power-steering-pump | unmapped | - | 708 |
| power-steering-pump | no_records | - | 15921 |
| power-steering-pump | not_closed | no_list_manifest | 337 |
| power-steering-pump | not_closed | no_year_manifest | 9207 |
| power-steering-pump | not_closed | unread_sibling_page | 133 |
| radiator | unmapped | - | 708 |
| radiator | no_records | - | 3593 |
| radiator | not_closed | no_list_manifest | 16 |
| radiator | not_closed | no_year_manifest | 21584 |
| radiator | not_closed | unread_sibling_page | 405 |
| side-mirrors | unmapped | - | 708 |
| side-mirrors | no_records | - | 3159 |
| side-mirrors | not_closed | no_list_manifest | 405 |
| side-mirrors | not_closed | no_year_manifest | 21791 |
| side-mirrors | not_closed | suspect_variant | 26 |
| side-mirrors | not_closed | uncrawled_chain_member | 136 |
| side-mirrors | not_closed | unread_sibling_page | 81 |
| starter | unmapped | - | 708 |
| starter | no_records | - | 2247 |
| starter | not_closed | no_list_manifest | 405 |
| starter | not_closed | no_year_manifest | 22728 |
| starter | not_closed | uncrawled_chain_member | 156 |
| starter | not_closed | unverified_product | 62 |
| tail-lights | unmapped | - | 708 |
| tail-lights | no_records | - | 7490 |
| tail-lights | not_closed | no_list_manifest | 294 |
| tail-lights | not_closed | no_year_manifest | 17571 |
| tail-lights | not_closed | unattested | 144 |
| tail-lights | not_closed | uncrawled_chain_member | 99 |
| throttle-body | unmapped | - | 708 |
| throttle-body | no_records | - | 3427 |
| throttle-body | not_closed | no_list_manifest | 319 |
| throttle-body | not_closed | no_year_manifest | 21609 |
| throttle-body | not_closed | unread_sibling_page | 218 |
| throttle-body | not_closed | unverified_product | 25 |
| tow-mirrors | unmapped | - | 708 |
| tow-mirrors | no_records | - | 25512 |
| tow-mirrors | not_closed | no_year_manifest | 86 |
| trunk-lid | unmapped | - | 708 |
| trunk-lid | no_records | - | 20312 |
| trunk-lid | not_closed | no_list_manifest | 16 |
| trunk-lid | not_closed | no_year_manifest | 4952 |
| trunk-lid | not_closed | uncrawled_chain_member | 318 |
| window-regulator | unmapped | - | 708 |
| window-regulator | no_records | - | 888 |
| window-regulator | not_closed | no_list_manifest | 405 |
| window-regulator | not_closed | no_year_manifest | 24062 |
| window-regulator | not_closed | unread_sibling_page | 243 |
| window-switch | unmapped | - | 708 |
| window-switch | no_records | - | 2390 |
| window-switch | not_closed | no_list_manifest | 405 |
| window-switch | not_closed | no_year_manifest | 22560 |
| window-switch | not_closed | unattested | 205 |
| window-switch | not_closed | uncrawled_chain_member | 38 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 708 |
| ac-compressor | no_records | - | 2002 |
| ac-compressor | split | option_split | 13803 |
| ac-compressor | conditional | conditional:body | 2 |
| ac-compressor | conditional | conditional:engine | 1194 |
| ac-compressor | conditional | conditional:engine_unattested | 1185 |
| ac-compressor | conditional | conditional:notes_not_own_page | 2646 |
| ac-compressor | conditional | conditional:option_layout | 493 |
| ac-compressor | conditional | conditional:qualifier | 1185 |
| ac-compressor | conditional | conditional:trim | 2899 |
| ac-compressor | gated | kind_not_phase1 | 189 |
| alternator | unmapped | - | 708 |
| alternator | no_records | - | 2577 |
| alternator | split | option_split | 18009 |
| alternator | conditional | conditional:engine_unattested | 769 |
| alternator | conditional | conditional:notes_not_own_page | 3336 |
| alternator | conditional | conditional:option_layout | 367 |
| alternator | conditional | conditional:production | 63 |
| alternator | conditional | conditional:trim | 193 |
| alternator | chain_member_conditional | chain_member_conditional | 148 |
| alternator | reman_only | reman_only | 136 |
| bumper-front | unmapped | - | 708 |
| bumper-front | no_records | - | 5898 |
| bumper-front | split | option_split | 13081 |
| bumper-front | conditional | conditional:engine | 261 |
| bumper-front | conditional | conditional:engine_unattested | 547 |
| bumper-front | conditional | conditional:notes_not_own_page | 1275 |
| bumper-front | conditional | conditional:option_layout | 64 |
| bumper-front | conditional | conditional:package | 42 |
| bumper-front | conditional | conditional:trim | 3565 |
| bumper-front | chain_member_conditional | chain_member_conditional | 19 |
| bumper-front | blocked | unexpected_position | 314 |
| bumper-front | eligible | - | 532 |
| bumper-rear | unmapped | - | 708 |
| bumper-rear | no_records | - | 3876 |
| bumper-rear | split | option_split | 12132 |
| bumper-rear | conditional | conditional:body | 316 |
| bumper-rear | conditional | conditional:engine | 777 |
| bumper-rear | conditional | conditional:engine_unattested | 1042 |
| bumper-rear | conditional | conditional:notes_not_own_page | 1969 |
| bumper-rear | conditional | conditional:trim | 4672 |
| bumper-rear | chain_member_conditional | chain_member_conditional | 19 |
| bumper-rear | blocked | unexpected_position | 310 |
| bumper-rear | eligible | - | 485 |
| climate-control | unmapped | - | 708 |
| climate-control | no_records | - | 10346 |
| climate-control | split | no_candidates | 231 |
| climate-control | split | option_split | 9867 |
| climate-control | conditional | conditional:engine_unattested | 279 |
| climate-control | conditional | conditional:engine_unparsed | 89 |
| climate-control | conditional | conditional:notes_not_own_page | 1063 |
| climate-control | conditional | conditional:option | 438 |
| climate-control | conditional | conditional:trim | 2996 |
| climate-control | eligible | - | 289 |
| door-front | unmapped | - | 708 |
| door-front | no_records | - | 3457 |
| door-front | split | option_split | 10369 |
| door-front | split | slot_missing | 1793 |
| door-front | conditional | conditional:engine | 384 |
| door-front | conditional | conditional:engine_unattested | 1588 |
| door-front | conditional | conditional:notes_not_own_page | 2723 |
| door-front | conditional | conditional:option_layout | 22 |
| door-front | conditional | conditional:plant | 58 |
| door-front | conditional | conditional:trim | 4210 |
| door-front | chain_member_conditional | chain_member_conditional | 136 |
| door-front | eligible | - | 858 |
| door-rear | unmapped | - | 708 |
| door-rear | no_records | - | 5146 |
| door-rear | split | option_split | 9955 |
| door-rear | split | slot_missing | 417 |
| door-rear | conditional | conditional:body | 71 |
| door-rear | conditional | conditional:engine | 558 |
| door-rear | conditional | conditional:engine_unattested | 1375 |
| door-rear | conditional | conditional:notes_not_own_page | 1811 |
| door-rear | conditional | conditional:option | 266 |
| door-rear | conditional | conditional:trim | 5518 |
| door-rear | eligible | - | 481 |
| fender | unmapped | - | 708 |
| fender | no_records | - | 7577 |
| fender | split | option_split | 6573 |
| fender | split | slot_missing | 563 |
| fender | conditional | conditional:engine | 261 |
| fender | conditional | conditional:engine_unattested | 1370 |
| fender | conditional | conditional:notes_not_own_page | 2346 |
| fender | conditional | conditional:option_layout | 354 |
| fender | conditional | conditional:trim | 5876 |
| fender | chain_member_conditional | chain_member_conditional | 99 |
| fender | eligible | - | 579 |
| fuel-pump-module | unmapped | - | 708 |
| fuel-pump-module | no_records | - | 11544 |
| fuel-pump-module | split | no_candidates | 132 |
| fuel-pump-module | split | option_split | 8658 |
| fuel-pump-module | conditional | conditional:engine | 141 |
| fuel-pump-module | conditional | conditional:engine_unattested | 504 |
| fuel-pump-module | conditional | conditional:notes_not_own_page | 1974 |
| fuel-pump-module | conditional | conditional:option_layout | 315 |
| fuel-pump-module | conditional | conditional:plant | 58 |
| fuel-pump-module | conditional | conditional:qualifier | 1277 |
| fuel-pump-module | conditional | conditional:trim | 929 |
| fuel-pump-module | gated | kind_not_phase1 | 66 |
| gauge-cluster | unmapped | - | 708 |
| gauge-cluster | no_records | - | 14369 |
| gauge-cluster | split | no_candidates | 140 |
| gauge-cluster | split | option_split | 10754 |
| gauge-cluster | conditional | conditional:engine | 144 |
| gauge-cluster | conditional | conditional:notes_not_own_page | 79 |
| gauge-cluster | conditional | conditional:trim | 39 |
| gauge-cluster | eligible | - | 73 |
| grille | unmapped | - | 708 |
| grille | no_records | - | 7080 |
| grille | split | option_split | 14673 |
| grille | conditional | conditional:engine | 34 |
| grille | conditional | conditional:engine_unattested | 180 |
| grille | conditional | conditional:engine_unparsed | 89 |
| grille | conditional | conditional:notes_not_own_page | 800 |
| grille | conditional | conditional:trim | 2303 |
| grille | eligible | - | 439 |
| headlights | unmapped | - | 708 |
| headlights | no_records | - | 4928 |
| headlights | split | option_split | 13760 |
| headlights | split | slot_missing | 70 |
| headlights | conditional | conditional:engine | 321 |
| headlights | conditional | conditional:engine_unattested | 105 |
| headlights | conditional | conditional:engine_unparsed | 89 |
| headlights | conditional | conditional:notes_not_own_page | 1447 |
| headlights | conditional | conditional:option | 298 |
| headlights | conditional | conditional:plant | 135 |
| headlights | conditional | conditional:qualifier | 3 |
| headlights | conditional | conditional:trim | 3406 |
| headlights | chain_member_conditional | chain_member_conditional | 175 |
| headlights | eligible | - | 861 |
| hood | unmapped | - | 708 |
| hood | no_records | - | 3127 |
| hood | split | option_split | 4205 |
| hood | conditional | conditional:engine | 754 |
| hood | conditional | conditional:engine_unattested | 1455 |
| hood | conditional | conditional:engine_unparsed | 89 |
| hood | conditional | conditional:notes_not_own_page | 3982 |
| hood | conditional | conditional:plant | 248 |
| hood | conditional | conditional:trim | 10138 |
| hood | chain_member_conditional | chain_member_conditional | 223 |
| hood | eligible | - | 1377 |
| ignition-coils | unmapped | - | 708 |
| ignition-coils | no_records | - | 1384 |
| ignition-coils | split | option_split | 17800 |
| ignition-coils | conditional | conditional:engine | 942 |
| ignition-coils | conditional | conditional:engine_unattested | 1270 |
| ignition-coils | conditional | conditional:notes_not_own_page | 2238 |
| ignition-coils | conditional | conditional:package | 405 |
| ignition-coils | conditional | conditional:trim | 1540 |
| ignition-coils | eligible | - | 19 |
| liftgate | unmapped | - | 708 |
| liftgate | no_records | - | 25250 |
| liftgate | split | option_split | 348 |
| power-steering-pump | unmapped | - | 708 |
| power-steering-pump | no_records | - | 15921 |
| power-steering-pump | split | option_split | 4403 |
| power-steering-pump | conditional | conditional:engine_unattested | 1069 |
| power-steering-pump | conditional | conditional:notes_not_own_page | 2449 |
| power-steering-pump | conditional | conditional:option_layout | 1756 |
| radiator | unmapped | - | 708 |
| radiator | no_records | - | 3593 |
| radiator | split | option_split | 20319 |
| radiator | conditional | conditional:engine | 121 |
| radiator | conditional | conditional:engine_unattested | 472 |
| radiator | conditional | conditional:notes_not_own_page | 363 |
| radiator | conditional | conditional:trans | 213 |
| radiator | conditional | conditional:trim | 517 |
| side-mirrors | unmapped | - | 708 |
| side-mirrors | no_records | - | 3159 |
| side-mirrors | split | option_split | 21676 |
| side-mirrors | split | slot_missing | 22 |
| side-mirrors | conditional | conditional:engine | 10 |
| side-mirrors | conditional | conditional:notes_not_own_page | 99 |
| side-mirrors | conditional | conditional:trim | 585 |
| side-mirrors | eligible | - | 47 |
| starter | unmapped | - | 708 |
| starter | no_records | - | 2247 |
| starter | split | option_split | 15541 |
| starter | conditional | conditional:engine | 204 |
| starter | conditional | conditional:engine_unattested | 1052 |
| starter | conditional | conditional:notes_not_own_page | 4229 |
| starter | conditional | conditional:option_layout | 1234 |
| starter | conditional | conditional:plant | 387 |
| starter | conditional | conditional:trim | 570 |
| starter | chain_member_conditional | chain_member_conditional | 47 |
| starter | reman_only | reman_only | 87 |
| tail-lights | unmapped | - | 708 |
| tail-lights | no_records | - | 7490 |
| tail-lights | split | no_candidates | 38 |
| tail-lights | split | option_split | 10433 |
| tail-lights | split | slot_missing | 349 |
| tail-lights | conditional | conditional:engine | 105 |
| tail-lights | conditional | conditional:engine_unattested | 697 |
| tail-lights | conditional | conditional:engine_unparsed | 89 |
| tail-lights | conditional | conditional:notes_not_own_page | 843 |
| tail-lights | conditional | conditional:plant | 887 |
| tail-lights | conditional | conditional:position | 112 |
| tail-lights | conditional | conditional:trim | 4150 |
| tail-lights | eligible | - | 405 |
| throttle-body | unmapped | - | 708 |
| throttle-body | no_records | - | 3427 |
| throttle-body | split | option_split | 13588 |
| throttle-body | conditional | conditional:engine | 939 |
| throttle-body | conditional | conditional:engine_unattested | 969 |
| throttle-body | conditional | conditional:notes_not_own_page | 1697 |
| throttle-body | conditional | conditional:plant | 263 |
| throttle-body | conditional | conditional:qualifier | 797 |
| throttle-body | conditional | conditional:trim | 3196 |
| throttle-body | conditional | conditional:unknown | 136 |
| throttle-body | gated | kind_not_phase1 | 586 |
| tow-mirrors | unmapped | - | 708 |
| tow-mirrors | no_records | - | 25512 |
| tow-mirrors | conditional | conditional:notes_not_own_page | 45 |
| tow-mirrors | conditional | conditional:package | 41 |
| trunk-lid | unmapped | - | 708 |
| trunk-lid | no_records | - | 20312 |
| trunk-lid | split | option_split | 3651 |
| trunk-lid | conditional | conditional:engine_unattested | 133 |
| trunk-lid | conditional | conditional:notes_not_own_page | 1152 |
| trunk-lid | conditional | conditional:option_layout | 347 |
| trunk-lid | conditional | conditional:trim | 3 |
| window-regulator | unmapped | - | 708 |
| window-regulator | no_records | - | 888 |
| window-regulator | split | packaging_incomplete | 885 |
| window-regulator | split | packaging_split | 12717 |
| window-regulator | split | packaging_unstated | 10070 |
| window-regulator | split | position_missing | 330 |
| window-regulator | conditional | conditional:engine_unattested | 381 |
| window-regulator | conditional | conditional:trim | 65 |
| window-regulator | eligible | - | 262 |
| window-switch | unmapped | - | 708 |
| window-switch | no_records | - | 2390 |
| window-switch | split | no_candidates | 102 |
| window-switch | split | option_split | 10793 |
| window-switch | split | position_missing | 3539 |
| window-switch | conditional | conditional:engine | 859 |
| window-switch | conditional | conditional:engine_unattested | 38 |
| window-switch | conditional | conditional:notes_not_own_page | 2461 |
| window-switch | conditional | conditional:option | 26 |
| window-switch | conditional | conditional:plant | 390 |
| window-switch | conditional | conditional:position | 211 |
| window-switch | conditional | conditional:trim | 4647 |
| window-switch | eligible | - | 142 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 14
- disputed_class: 37
- evidence_mismatch: 6
- systemic_evidence_failure: 1
- universal_part_suspect: 6

## Unknown note clauses (top 30)

- `Part Name Code: 87910`: 579
- `Part Name Code: 87940`: 550
- `Part Name Code: 87901B`: 263
- `Part Name Code: 87906B`: 257
- `Part Name Code: 81175`: 135
- `Part Name Code: 81135`: 127
- `GYL1#.. JPP`: 106
- `GSE20`: 103
- `MERCURY GRAY MC.`: 75
- `OEM`: 75
- `UZS190`: 74
- `21.. ATM`: 70
- `21`: 64
- `CANADA SPEC&F PACKAGE&FRONT SEAT-F SPORTS PACKAGE (LEATHER, POWER SEAT)&EMV & NAVIGATION SYSTEM-WITH(HDD NAVIGATION)`: 64
- `DK.BLUE MC. CC.`: 64
- `PREMIUM PACKAGE&W(MEMORY MIRROR)`: 64
- `Mvp`: 63
- `STARLIGHT BLACK GF.`: 63
- `LAPIS LAZULI MC.`: 62
- `Without Double Cab`: 62
- `BLUISH PEARL CS.`: 58
- `GSE2#.. ATM`: 58
- `SILVERY BLUE ME.`: 57
- `KOREA SPEC&LUXURY PACKAGE&FRONT SEAT-SEMIANILINE VENTILATED LEATHER`: 56
- `LUXURY PACKAGE&FRONT SEAT-SEMIANILINE VENTILATED LEATHER`: 56
- `W(MEMORY ADJUST SYSTEM)`: 56
- `MD.GREEN M.M.`: 52
- `GSU3#.. JPP`: 48
- `KOREA SPEC&F PACKAGE&FRONT SEAT-F SPORTS PACKAGE (LEATHER, POWER SEAT)`: 48
- `Part Name Code: 27020`: 48

## Unmapped catalog models

- Lexus GS200t: feed 'GS 200t' 0 cars
- Lexus IS F: feed 'IS F' 0 cars (excluded: catalog model with no feed cars as 'IS F' (inventory 2026-11-04); nothing to map)
- Lexus IS Turbo: feed 'IS Turbo' 0 cars
- Lexus LS400: feed 'LS 400' 118 cars
- Lexus LS600hL: feed 'LS 600h L' 1 cars (excluded: M6: the only feed 'LS 600h L' car decodes as another make (vPIC mismatch))
- Lexus LX570: feed 'LX 570' 0 cars
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
