# OEM curation report: toyota

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-06T00:06:09Z.

- records 6214, classes 6170, list rows 25651, year manifests 64, cells 8621
- Verified groups 0, engine vg groups 0, Likely groups 779
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.lexuspartsnow.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.lexuspartsnow.com: only 0% of its 4959 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 699 |
| ac-compressor | no_records | - | 2029 |
| ac-compressor | not_closed | no_list_manifest | 651 |
| ac-compressor | not_closed | no_year_manifest | 22750 |
| ac-compressor | not_closed | uncrawled_chain_member | 157 |
| ac-compressor | not_closed | unverified_product | 83 |
| alternator | unmapped | - | 699 |
| alternator | no_records | - | 2613 |
| alternator | not_closed | no_list_manifest | 651 |
| alternator | not_closed | no_year_manifest | 22188 |
| alternator | not_closed | uncrawled_chain_member | 129 |
| alternator | not_closed | unread_sibling_page | 28 |
| alternator | not_closed | unverified_product | 61 |
| bumper-front | unmapped | - | 699 |
| bumper-front | no_records | - | 4943 |
| bumper-front | not_closed | no_list_manifest | 1 |
| bumper-front | not_closed | no_year_manifest | 19834 |
| bumper-front | not_closed | unread_sibling_page | 892 |
| bumper-rear | unmapped | - | 699 |
| bumper-rear | no_records | - | 2972 |
| bumper-rear | not_closed | no_list_manifest | 1 |
| bumper-rear | not_closed | no_year_manifest | 21805 |
| bumper-rear | not_closed | unread_sibling_page | 892 |
| climate-control | unmapped | - | 699 |
| climate-control | no_records | - | 10371 |
| climate-control | not_closed | no_list_manifest | 153 |
| climate-control | not_closed | no_year_manifest | 14906 |
| climate-control | not_closed | unread_sibling_page | 240 |
| door-front | unmapped | - | 699 |
| door-front | no_records | - | 2642 |
| door-front | not_closed | no_list_manifest | 1 |
| door-front | not_closed | no_year_manifest | 22135 |
| door-front | not_closed | unread_sibling_page | 892 |
| door-rear | unmapped | - | 699 |
| door-rear | no_records | - | 4242 |
| door-rear | not_closed | no_list_manifest | 1 |
| door-rear | not_closed | no_year_manifest | 20545 |
| door-rear | not_closed | unread_sibling_page | 882 |
| fender | unmapped | - | 699 |
| fender | no_records | - | 6726 |
| fender | not_closed | no_list_manifest | 1 |
| fender | not_closed | no_year_manifest | 18051 |
| fender | not_closed | unread_sibling_page | 892 |
| fuel-pump-module | unmapped | - | 699 |
| fuel-pump-module | no_records | - | 11598 |
| fuel-pump-module | not_closed | no_list_manifest | 146 |
| fuel-pump-module | not_closed | no_year_manifest | 13686 |
| fuel-pump-module | not_closed | unread_sibling_page | 240 |
| gauge-cluster | unmapped | - | 699 |
| gauge-cluster | no_records | - | 13673 |
| gauge-cluster | not_closed | no_list_manifest | 1 |
| gauge-cluster | not_closed | no_year_manifest | 11104 |
| gauge-cluster | not_closed | unread_sibling_page | 892 |
| grille | unmapped | - | 699 |
| grille | no_records | - | 6134 |
| grille | not_closed | no_list_manifest | 1 |
| grille | not_closed | no_year_manifest | 18643 |
| grille | not_closed | unattested | 467 |
| grille | not_closed | uncrawled_chain_member | 425 |
| headlights | unmapped | - | 699 |
| headlights | no_records | - | 4931 |
| headlights | not_closed | no_list_manifest | 649 |
| headlights | not_closed | no_year_manifest | 19850 |
| headlights | not_closed | unread_sibling_page | 240 |
| hood | unmapped | - | 699 |
| hood | no_records | - | 2132 |
| hood | not_closed | no_list_manifest | 1 |
| hood | not_closed | no_year_manifest | 22645 |
| hood | not_closed | unread_sibling_page | 892 |
| ignition-coils | unmapped | - | 699 |
| ignition-coils | no_records | - | 625 |
| ignition-coils | not_closed | no_list_manifest | 1 |
| ignition-coils | not_closed | no_year_manifest | 24152 |
| ignition-coils | not_closed | unattested | 48 |
| ignition-coils | not_closed | uncrawled_chain_member | 126 |
| ignition-coils | not_closed | unverified_product | 718 |
| liftgate | unmapped | - | 699 |
| liftgate | no_records | - | 24974 |
| liftgate | not_closed | no_year_manifest | 455 |
| liftgate | not_closed | unattested | 109 |
| liftgate | not_closed | uncrawled_chain_member | 132 |
| power-steering-pump | unmapped | - | 699 |
| power-steering-pump | no_records | - | 15928 |
| power-steering-pump | not_closed | no_list_manifest | 505 |
| power-steering-pump | not_closed | no_year_manifest | 9104 |
| power-steering-pump | not_closed | unread_sibling_page | 133 |
| radiator | unmapped | - | 699 |
| radiator | no_records | - | 2598 |
| radiator | not_closed | no_list_manifest | 1 |
| radiator | not_closed | no_year_manifest | 22179 |
| radiator | not_closed | unread_sibling_page | 892 |
| side-mirrors | unmapped | - | 699 |
| side-mirrors | no_records | - | 3193 |
| side-mirrors | not_closed | no_list_manifest | 651 |
| side-mirrors | not_closed | no_year_manifest | 21586 |
| side-mirrors | not_closed | suspect_variant | 26 |
| side-mirrors | not_closed | uncrawled_chain_member | 134 |
| side-mirrors | not_closed | unread_sibling_page | 80 |
| starter | unmapped | - | 699 |
| starter | no_records | - | 2287 |
| starter | not_closed | no_list_manifest | 651 |
| starter | not_closed | no_year_manifest | 22514 |
| starter | not_closed | unattested | 1 |
| starter | not_closed | uncrawled_chain_member | 156 |
| starter | not_closed | unverified_product | 61 |
| tail-lights | unmapped | - | 699 |
| tail-lights | no_records | - | 7519 |
| tail-lights | not_closed | no_list_manifest | 432 |
| tail-lights | not_closed | no_year_manifest | 17479 |
| tail-lights | not_closed | unattested | 140 |
| tail-lights | not_closed | uncrawled_chain_member | 100 |
| throttle-body | unmapped | - | 699 |
| throttle-body | no_records | - | 3408 |
| throttle-body | not_closed | no_list_manifest | 564 |
| throttle-body | not_closed | no_year_manifest | 21458 |
| throttle-body | not_closed | unread_sibling_page | 218 |
| throttle-body | not_closed | unverified_product | 22 |
| tow-mirrors | unmapped | - | 699 |
| tow-mirrors | no_records | - | 25583 |
| tow-mirrors | not_closed | no_year_manifest | 87 |
| trunk-lid | unmapped | - | 699 |
| trunk-lid | no_records | - | 19702 |
| trunk-lid | not_closed | no_list_manifest | 1 |
| trunk-lid | not_closed | no_year_manifest | 5293 |
| trunk-lid | not_closed | unattested | 12 |
| trunk-lid | not_closed | uncrawled_chain_member | 662 |
| window-regulator | unmapped | - | 699 |
| window-regulator | no_records | - | 894 |
| window-regulator | not_closed | no_list_manifest | 651 |
| window-regulator | not_closed | no_year_manifest | 23885 |
| window-regulator | not_closed | unread_sibling_page | 240 |
| window-switch | unmapped | - | 699 |
| window-switch | no_records | - | 2384 |
| window-switch | not_closed | no_list_manifest | 570 |
| window-switch | not_closed | no_year_manifest | 22476 |
| window-switch | not_closed | unattested | 202 |
| window-switch | not_closed | uncrawled_chain_member | 38 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 699 |
| ac-compressor | no_records | - | 2029 |
| ac-compressor | split | option_split | 13836 |
| ac-compressor | conditional | conditional:body | 2 |
| ac-compressor | conditional | conditional:engine | 1187 |
| ac-compressor | conditional | conditional:engine_unattested | 1178 |
| ac-compressor | conditional | conditional:notes_not_own_page | 2655 |
| ac-compressor | conditional | conditional:option_layout | 482 |
| ac-compressor | conditional | conditional:qualifier | 1200 |
| ac-compressor | conditional | conditional:trim | 2910 |
| ac-compressor | gated | kind_not_phase1 | 191 |
| alternator | unmapped | - | 699 |
| alternator | no_records | - | 2613 |
| alternator | split | option_split | 18089 |
| alternator | conditional | conditional:engine_unattested | 764 |
| alternator | conditional | conditional:notes_not_own_page | 3310 |
| alternator | conditional | conditional:option_layout | 360 |
| alternator | conditional | conditional:production | 62 |
| alternator | conditional | conditional:trim | 191 |
| alternator | chain_member_conditional | chain_member_conditional | 146 |
| alternator | reman_only | reman_only | 135 |
| bumper-front | unmapped | - | 699 |
| bumper-front | no_records | - | 4943 |
| bumper-front | split | option_split | 14105 |
| bumper-front | conditional | conditional:engine | 266 |
| bumper-front | conditional | conditional:engine_unattested | 547 |
| bumper-front | conditional | conditional:notes_not_own_page | 1276 |
| bumper-front | conditional | conditional:option_layout | 67 |
| bumper-front | conditional | conditional:package | 44 |
| bumper-front | conditional | conditional:trim | 3573 |
| bumper-front | chain_member_conditional | chain_member_conditional | 18 |
| bumper-front | blocked | unexpected_position | 304 |
| bumper-front | eligible | - | 527 |
| bumper-rear | unmapped | - | 699 |
| bumper-rear | no_records | - | 2972 |
| bumper-rear | split | option_split | 12838 |
| bumper-rear | conditional | conditional:body | 306 |
| bumper-rear | conditional | conditional:engine | 786 |
| bumper-rear | conditional | conditional:engine_unattested | 1280 |
| bumper-rear | conditional | conditional:notes_not_own_page | 1967 |
| bumper-rear | conditional | conditional:trim | 4719 |
| bumper-rear | chain_member_conditional | chain_member_conditional | 18 |
| bumper-rear | blocked | unexpected_position | 305 |
| bumper-rear | eligible | - | 479 |
| climate-control | unmapped | - | 699 |
| climate-control | no_records | - | 10371 |
| climate-control | split | no_candidates | 229 |
| climate-control | split | option_split | 9903 |
| climate-control | conditional | conditional:engine_unattested | 272 |
| climate-control | conditional | conditional:engine_unparsed | 90 |
| climate-control | conditional | conditional:notes_not_own_page | 1053 |
| climate-control | conditional | conditional:option | 446 |
| climate-control | conditional | conditional:trim | 3023 |
| climate-control | eligible | - | 283 |
| door-front | unmapped | - | 699 |
| door-front | no_records | - | 2642 |
| door-front | split | option_split | 10742 |
| door-front | split | slot_missing | 1783 |
| door-front | conditional | conditional:engine | 391 |
| door-front | conditional | conditional:engine_unattested | 2085 |
| door-front | conditional | conditional:notes_not_own_page | 2720 |
| door-front | conditional | conditional:option_layout | 21 |
| door-front | conditional | conditional:plant | 57 |
| door-front | conditional | conditional:trim | 4251 |
| door-front | chain_member_conditional | chain_member_conditional | 135 |
| door-front | eligible | - | 843 |
| door-rear | unmapped | - | 699 |
| door-rear | no_records | - | 4242 |
| door-rear | split | option_split | 10451 |
| door-rear | split | slot_missing | 415 |
| door-rear | conditional | conditional:body | 71 |
| door-rear | conditional | conditional:engine | 561 |
| door-rear | conditional | conditional:engine_unattested | 1794 |
| door-rear | conditional | conditional:notes_not_own_page | 1810 |
| door-rear | conditional | conditional:option | 258 |
| door-rear | conditional | conditional:trim | 5595 |
| door-rear | eligible | - | 473 |
| fender | unmapped | - | 699 |
| fender | no_records | - | 6726 |
| fender | split | option_split | 6709 |
| fender | split | slot_missing | 558 |
| fender | conditional | conditional:engine | 266 |
| fender | conditional | conditional:engine_unattested | 1947 |
| fender | conditional | conditional:notes_not_own_page | 2344 |
| fender | conditional | conditional:option_layout | 362 |
| fender | conditional | conditional:package | 132 |
| fender | conditional | conditional:trim | 5958 |
| fender | chain_member_conditional | chain_member_conditional | 95 |
| fender | eligible | - | 573 |
| fuel-pump-module | unmapped | - | 699 |
| fuel-pump-module | no_records | - | 11598 |
| fuel-pump-module | split | no_candidates | 127 |
| fuel-pump-module | split | option_split | 8705 |
| fuel-pump-module | conditional | conditional:engine | 146 |
| fuel-pump-module | conditional | conditional:engine_unattested | 496 |
| fuel-pump-module | conditional | conditional:notes_not_own_page | 1960 |
| fuel-pump-module | conditional | conditional:option_layout | 306 |
| fuel-pump-module | conditional | conditional:plant | 57 |
| fuel-pump-module | conditional | conditional:qualifier | 1265 |
| fuel-pump-module | conditional | conditional:trim | 944 |
| fuel-pump-module | gated | kind_not_phase1 | 66 |
| gauge-cluster | unmapped | - | 699 |
| gauge-cluster | no_records | - | 13673 |
| gauge-cluster | split | no_candidates | 247 |
| gauge-cluster | split | option_split | 11405 |
| gauge-cluster | conditional | conditional:engine | 150 |
| gauge-cluster | conditional | conditional:notes_not_own_page | 85 |
| gauge-cluster | conditional | conditional:trim | 36 |
| gauge-cluster | eligible | - | 74 |
| grille | unmapped | - | 699 |
| grille | no_records | - | 6134 |
| grille | split | option_split | 15449 |
| grille | conditional | conditional:engine | 34 |
| grille | conditional | conditional:engine_unattested | 389 |
| grille | conditional | conditional:engine_unparsed | 90 |
| grille | conditional | conditional:notes_not_own_page | 804 |
| grille | conditional | conditional:trim | 2334 |
| grille | eligible | - | 436 |
| headlights | unmapped | - | 699 |
| headlights | no_records | - | 4931 |
| headlights | split | option_split | 13808 |
| headlights | split | slot_missing | 71 |
| headlights | conditional | conditional:engine | 323 |
| headlights | conditional | conditional:engine_unattested | 104 |
| headlights | conditional | conditional:engine_unparsed | 90 |
| headlights | conditional | conditional:notes_not_own_page | 1455 |
| headlights | conditional | conditional:option | 306 |
| headlights | conditional | conditional:plant | 130 |
| headlights | conditional | conditional:qualifier | 3 |
| headlights | conditional | conditional:trim | 3431 |
| headlights | chain_member_conditional | chain_member_conditional | 172 |
| headlights | eligible | - | 846 |
| hood | unmapped | - | 699 |
| hood | no_records | - | 2132 |
| hood | split | option_split | 4206 |
| hood | conditional | conditional:engine | 764 |
| hood | conditional | conditional:engine_unattested | 2186 |
| hood | conditional | conditional:engine_unparsed | 90 |
| hood | conditional | conditional:notes_not_own_page | 3973 |
| hood | conditional | conditional:option | 106 |
| hood | conditional | conditional:package | 132 |
| hood | conditional | conditional:plant | 252 |
| hood | conditional | conditional:trim | 10255 |
| hood | chain_member_conditional | chain_member_conditional | 225 |
| hood | eligible | - | 1349 |
| ignition-coils | unmapped | - | 699 |
| ignition-coils | no_records | - | 625 |
| ignition-coils | split | option_split | 18716 |
| ignition-coils | conditional | conditional:engine | 941 |
| ignition-coils | conditional | conditional:engine_unattested | 1017 |
| ignition-coils | conditional | conditional:notes_not_own_page | 2239 |
| ignition-coils | conditional | conditional:package | 547 |
| ignition-coils | conditional | conditional:trim | 1567 |
| ignition-coils | eligible | - | 18 |
| liftgate | unmapped | - | 699 |
| liftgate | no_records | - | 24974 |
| liftgate | split | option_split | 636 |
| liftgate | conditional | conditional:engine_unattested | 60 |
| power-steering-pump | unmapped | - | 699 |
| power-steering-pump | no_records | - | 15928 |
| power-steering-pump | split | option_split | 4440 |
| power-steering-pump | conditional | conditional:engine_unattested | 1060 |
| power-steering-pump | conditional | conditional:notes_not_own_page | 2459 |
| power-steering-pump | conditional | conditional:option_layout | 1783 |
| radiator | unmapped | - | 699 |
| radiator | no_records | - | 2598 |
| radiator | split | option_split | 21224 |
| radiator | conditional | conditional:engine | 121 |
| radiator | conditional | conditional:engine_unattested | 640 |
| radiator | conditional | conditional:notes_not_own_page | 362 |
| radiator | conditional | conditional:trans | 217 |
| radiator | conditional | conditional:trim | 508 |
| side-mirrors | unmapped | - | 699 |
| side-mirrors | no_records | - | 3193 |
| side-mirrors | split | option_split | 21711 |
| side-mirrors | split | slot_missing | 22 |
| side-mirrors | conditional | conditional:engine | 10 |
| side-mirrors | conditional | conditional:notes_not_own_page | 99 |
| side-mirrors | conditional | conditional:trim | 587 |
| side-mirrors | eligible | - | 48 |
| starter | unmapped | - | 699 |
| starter | no_records | - | 2287 |
| starter | split | option_split | 15588 |
| starter | conditional | conditional:engine | 205 |
| starter | conditional | conditional:engine_unattested | 1045 |
| starter | conditional | conditional:notes_not_own_page | 4217 |
| starter | conditional | conditional:option_layout | 1235 |
| starter | conditional | conditional:plant | 387 |
| starter | conditional | conditional:trim | 574 |
| starter | chain_member_conditional | chain_member_conditional | 48 |
| starter | reman_only | reman_only | 84 |
| tail-lights | unmapped | - | 699 |
| tail-lights | no_records | - | 7519 |
| tail-lights | split | no_candidates | 38 |
| tail-lights | split | option_split | 10461 |
| tail-lights | split | slot_missing | 341 |
| tail-lights | conditional | conditional:engine | 107 |
| tail-lights | conditional | conditional:engine_unattested | 672 |
| tail-lights | conditional | conditional:engine_unparsed | 90 |
| tail-lights | conditional | conditional:notes_not_own_page | 851 |
| tail-lights | conditional | conditional:plant | 908 |
| tail-lights | conditional | conditional:position | 110 |
| tail-lights | conditional | conditional:trim | 4174 |
| tail-lights | eligible | - | 399 |
| throttle-body | unmapped | - | 699 |
| throttle-body | no_records | - | 3408 |
| throttle-body | split | option_split | 13648 |
| throttle-body | conditional | conditional:engine | 932 |
| throttle-body | conditional | conditional:engine_unattested | 961 |
| throttle-body | conditional | conditional:notes_not_own_page | 1687 |
| throttle-body | conditional | conditional:plant | 272 |
| throttle-body | conditional | conditional:qualifier | 801 |
| throttle-body | conditional | conditional:trim | 3255 |
| throttle-body | conditional | conditional:unknown | 135 |
| throttle-body | gated | kind_not_phase1 | 571 |
| tow-mirrors | unmapped | - | 699 |
| tow-mirrors | no_records | - | 25583 |
| tow-mirrors | conditional | conditional:notes_not_own_page | 45 |
| tow-mirrors | conditional | conditional:package | 42 |
| trunk-lid | unmapped | - | 699 |
| trunk-lid | no_records | - | 19702 |
| trunk-lid | split | option_split | 4220 |
| trunk-lid | conditional | conditional:engine_unattested | 227 |
| trunk-lid | conditional | conditional:notes_not_own_page | 1171 |
| trunk-lid | conditional | conditional:option_layout | 347 |
| trunk-lid | conditional | conditional:trim | 3 |
| window-regulator | unmapped | - | 699 |
| window-regulator | no_records | - | 894 |
| window-regulator | split | packaging_incomplete | 908 |
| window-regulator | split | packaging_split | 12765 |
| window-regulator | split | packaging_unstated | 10072 |
| window-regulator | split | position_missing | 330 |
| window-regulator | conditional | conditional:engine_unattested | 381 |
| window-regulator | conditional | conditional:trim | 64 |
| window-regulator | eligible | - | 256 |
| window-switch | unmapped | - | 699 |
| window-switch | no_records | - | 2384 |
| window-switch | split | no_candidates | 102 |
| window-switch | split | option_split | 10855 |
| window-switch | split | position_missing | 3520 |
| window-switch | conditional | conditional:engine | 871 |
| window-switch | conditional | conditional:engine_unattested | 38 |
| window-switch | conditional | conditional:notes_not_own_page | 2454 |
| window-switch | conditional | conditional:option | 25 |
| window-switch | conditional | conditional:plant | 391 |
| window-switch | conditional | conditional:position | 205 |
| window-switch | conditional | conditional:trim | 4682 |
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
- `OEM`: 74
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
- Lexus LS400: feed 'LS 400' 119 cars
- Lexus LS600hL: feed 'LS 600h L' 0 cars (excluded: M6: the only feed 'LS 600h L' car decodes as another make (vPIC mismatch))
- Lexus LX470: feed 'LX 470' 5 cars
- Lexus LX570: feed 'LX 570' 0 cars
- Lexus NX200t: feed 'NX 200t' 0 cars
- Lexus NX300: feed 'NX 300' 0 cars
- Lexus NX300h: feed 'NX 300h' 0 cars
- Lexus RC Turbo: feed 'RC Turbo' 0 cars
- Lexus RC200t: feed 'RC 200t' 0 cars
- Lexus RC300: feed 'RC 300' 0 cars
- Lexus SC300: feed 'SC 300' 9 cars
- Lexus SC400: feed 'SC 400' 20 cars
- Toyota C-HR: feed 'C-HR' 12 cars
- Toyota Corolla Cross: feed 'Corolla Cross' 0 cars
- Toyota Crown: feed 'Crown' 0 cars
- Toyota Crown Signia: feed 'Crown Signia' 0 cars
- Toyota GR Corolla: feed 'GR Corolla' 0 cars
- Toyota Grand Highlander: feed 'Grand Highlander' 0 cars
- Toyota Prius AWD-e: feed 'Prius' 1568 cars (excluded: catalog model with no feed cars as 'Prius AWD-e' (inventory 2026-11-04); nothing to map)
- Toyota RAV4 Prime: feed 'RAV4 Prime' 0 cars
- Toyota T100: feed 'T100' 56 cars
