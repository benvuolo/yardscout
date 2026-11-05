# OEM curation report: toyota

Raw: `50ac4a48cdc62d02bd819bec33a67d0f07d8a71e` @ `50ac4a48cdc6`; as of 2026-11-05T12:36:38Z.

- records 3225, classes 3194, list rows 0, year manifests 0, cells 3968
- Verified groups 0, engine vg groups 0, Likely groups 1057
- blocked sites: www.lexuspartsnow.com

## Gates standing for the whole namespace

- no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close (C1/C2); Verified is impossible by design until the crawler writes them
- no (site, category) of this namespace has passed the audit gate (CATEGORY_STATUS has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.lexuspartsnow.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.lexuspartsnow.com: only 0% of its 2535 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)
- blocked by the crawl breaker: www.lexuspartsnow.com (their cells never close, C9)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 707 |
| ac-compressor | no_records | - | 2726 |
| ac-compressor | not_closed | no_year_manifest | 22902 |
| alternator | unmapped | - | 707 |
| alternator | no_records | - | 3105 |
| alternator | not_closed | no_year_manifest | 22523 |
| climate-control | unmapped | - | 707 |
| climate-control | no_records | - | 11133 |
| climate-control | not_closed | no_year_manifest | 14495 |
| fuel-pump-module | unmapped | - | 707 |
| fuel-pump-module | no_records | - | 12691 |
| fuel-pump-module | not_closed | no_year_manifest | 12937 |
| headlights | unmapped | - | 707 |
| headlights | no_records | - | 5748 |
| headlights | not_closed | no_year_manifest | 19880 |
| power-steering-pump | unmapped | - | 707 |
| power-steering-pump | no_records | - | 16324 |
| power-steering-pump | not_closed | no_year_manifest | 9304 |
| side-mirrors | unmapped | - | 707 |
| side-mirrors | no_records | - | 3788 |
| side-mirrors | not_closed | no_year_manifest | 21840 |
| starter | unmapped | - | 707 |
| starter | no_records | - | 2852 |
| starter | not_closed | no_year_manifest | 22776 |
| tail-lights | unmapped | - | 707 |
| tail-lights | no_records | - | 8258 |
| tail-lights | not_closed | no_year_manifest | 17370 |
| throttle-body | unmapped | - | 707 |
| throttle-body | no_records | - | 4243 |
| throttle-body | not_closed | no_year_manifest | 21385 |
| tow-mirrors | unmapped | - | 707 |
| tow-mirrors | no_records | - | 25542 |
| tow-mirrors | not_closed | no_year_manifest | 86 |
| window-regulator | unmapped | - | 707 |
| window-regulator | no_records | - | 1420 |
| window-regulator | not_closed | no_year_manifest | 24208 |
| window-switch | unmapped | - | 707 |
| window-switch | no_records | - | 3094 |
| window-switch | not_closed | no_year_manifest | 22534 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 707 |
| ac-compressor | no_records | - | 2726 |
| ac-compressor | split | option_split | 13428 |
| ac-compressor | conditional | conditional:engine | 1190 |
| ac-compressor | conditional | conditional:notes_not_own_page | 6544 |
| ac-compressor | conditional | conditional:option_layout | 691 |
| ac-compressor | conditional | conditional:qualifier | 254 |
| ac-compressor | conditional | conditional:trim | 157 |
| ac-compressor | reman_only | reman_only | 201 |
| ac-compressor | gated | kind_not_phase1 | 437 |
| alternator | unmapped | - | 707 |
| alternator | no_records | - | 3105 |
| alternator | split | option_split | 16898 |
| alternator | conditional | conditional:notes_not_own_page | 4391 |
| alternator | conditional | conditional:option_layout | 744 |
| alternator | conditional | conditional:plant | 134 |
| alternator | conditional | conditional:production | 62 |
| alternator | conditional | conditional:trim | 10 |
| alternator | chain_member_conditional | chain_member_conditional | 147 |
| alternator | reman_only | reman_only | 137 |
| climate-control | unmapped | - | 707 |
| climate-control | no_records | - | 11133 |
| climate-control | split | option_split | 9782 |
| climate-control | conditional | conditional:notes_not_own_page | 3680 |
| climate-control | conditional | conditional:option | 442 |
| climate-control | conditional | conditional:option_layout | 135 |
| climate-control | conditional | conditional:trim | 132 |
| climate-control | eligible | - | 324 |
| fuel-pump-module | unmapped | - | 707 |
| fuel-pump-module | no_records | - | 12691 |
| fuel-pump-module | split | option_split | 8396 |
| fuel-pump-module | conditional | conditional:engine | 9 |
| fuel-pump-module | conditional | conditional:notes_not_own_page | 3503 |
| fuel-pump-module | conditional | conditional:option_layout | 452 |
| fuel-pump-module | conditional | conditional:plant | 57 |
| fuel-pump-module | conditional | conditional:qualifier | 182 |
| fuel-pump-module | gated | kind_not_phase1 | 338 |
| headlights | unmapped | - | 707 |
| headlights | no_records | - | 5748 |
| headlights | split | option_split | 13245 |
| headlights | split | slot_missing | 51 |
| headlights | conditional | conditional:engine | 133 |
| headlights | conditional | conditional:notes_not_own_page | 4434 |
| headlights | conditional | conditional:option | 298 |
| headlights | conditional | conditional:option_layout | 135 |
| headlights | conditional | conditional:trim | 523 |
| headlights | chain_member_conditional | chain_member_conditional | 174 |
| headlights | eligible | - | 887 |
| power-steering-pump | unmapped | - | 707 |
| power-steering-pump | no_records | - | 16324 |
| power-steering-pump | split | option_split | 4243 |
| power-steering-pump | conditional | conditional:notes_not_own_page | 3094 |
| power-steering-pump | conditional | conditional:option_layout | 1967 |
| side-mirrors | unmapped | - | 707 |
| side-mirrors | no_records | - | 3788 |
| side-mirrors | split | option_split | 21077 |
| side-mirrors | split | slot_missing | 22 |
| side-mirrors | conditional | conditional:engine | 10 |
| side-mirrors | conditional | conditional:notes_not_own_page | 674 |
| side-mirrors | conditional | conditional:trim | 10 |
| side-mirrors | eligible | - | 47 |
| starter | unmapped | - | 707 |
| starter | no_records | - | 2852 |
| starter | split | option_split | 15075 |
| starter | conditional | conditional:engine | 205 |
| starter | conditional | conditional:notes_not_own_page | 5453 |
| starter | conditional | conditional:option_layout | 1519 |
| starter | conditional | conditional:plant | 390 |
| starter | chain_member_conditional | chain_member_conditional | 47 |
| starter | reman_only | reman_only | 87 |
| tail-lights | unmapped | - | 707 |
| tail-lights | no_records | - | 8258 |
| tail-lights | split | option_split | 10137 |
| tail-lights | split | slot_missing | 380 |
| tail-lights | conditional | conditional:notes_not_own_page | 4278 |
| tail-lights | conditional | conditional:option_layout | 125 |
| tail-lights | conditional | conditional:plant | 892 |
| tail-lights | conditional | conditional:position | 477 |
| tail-lights | conditional | conditional:trim | 650 |
| tail-lights | eligible | - | 431 |
| throttle-body | unmapped | - | 707 |
| throttle-body | no_records | - | 4243 |
| throttle-body | split | option_split | 12221 |
| throttle-body | conditional | conditional:engine | 1264 |
| throttle-body | conditional | conditional:notes_not_own_page | 6420 |
| throttle-body | conditional | conditional:option_layout | 267 |
| throttle-body | conditional | conditional:plant | 263 |
| throttle-body | conditional | conditional:trim | 250 |
| throttle-body | conditional | conditional:unknown | 137 |
| throttle-body | gated | kind_not_phase1 | 563 |
| tow-mirrors | unmapped | - | 707 |
| tow-mirrors | no_records | - | 25542 |
| tow-mirrors | conditional | conditional:notes_not_own_page | 45 |
| tow-mirrors | conditional | conditional:option_layout | 41 |
| window-regulator | unmapped | - | 707 |
| window-regulator | no_records | - | 1420 |
| window-regulator | split | packaging_incomplete | 978 |
| window-regulator | split | packaging_split | 12225 |
| window-regulator | split | packaging_unstated | 9880 |
| window-regulator | split | position_missing | 401 |
| window-regulator | conditional | conditional:notes_not_own_page | 111 |
| window-regulator | conditional | conditional:option_layout | 173 |
| window-regulator | conditional | conditional:trim | 65 |
| window-regulator | eligible | - | 375 |
| window-switch | unmapped | - | 707 |
| window-switch | no_records | - | 3094 |
| window-switch | split | option_split | 10279 |
| window-switch | split | position_missing | 3271 |
| window-switch | conditional | conditional:engine | 822 |
| window-switch | conditional | conditional:notes_not_own_page | 6660 |
| window-switch | conditional | conditional:option | 25 |
| window-switch | conditional | conditional:plant | 393 |
| window-switch | conditional | conditional:position | 347 |
| window-switch | conditional | conditional:trim | 552 |
| window-switch | eligible | - | 185 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 6
- disputed_class: 31
- universal_part_suspect: 4

## Unknown note clauses (top 30)

- `Part Name Code: 87910`: 318
- `Part Name Code: 87940`: 287
- `Part Name Code: 87901B`: 144
- `Part Name Code: 87906B`: 139
- `GYL1#.. JPP`: 106
- `Part Name Code: 81175`: 64
- `Part Name Code: 81135`: 60
- `GSU3#.. JPP`: 48
- `GSE20`: 47
- `MERCURY GRAY MC.`: 45
- `PREMIUM PACKAGE&W(MEMORY MIRROR)`: 44
- `STARLIGHT BLACK GF.`: 41
- `W(MEMORY ADJUST SYSTEM)`: 39
- `W(AUTOMATIC DIMMING MIRROR)`: 38
- `Without Double Cab`: 37
- `DK.BLUE MC. CC.`: 36
- `GYL1#.. NAP`: 33
- `Production Date: from 07/2000`: 33
- `LAPIS LAZULI MC.`: 32
- `MD.GREEN M.M.`: 32
- `21`: 31
- `OUTSIDE REAR VIEW MIRROR-*AREM & AUTOMATIC ANTI-GLARE & MEMORY`: 30
- `OUTSIDE REAR VIEW MIRROR-*AREM & MEMORY & BLIND SPOT DETECTION`: 30
- `SILVERY BLUE ME.`: 29
- `KOREA SPEC&LUXURY PACKAGE&FRONT SEAT-SEMIANILINE VENTILATED LEATHER`: 28
- `LUXURY PACKAGE&FRONT SEAT-SEMIANILINE VENTILATED LEATHER`: 28
- `With Heated Glass`: 28
- `Part Name Code: 27020`: 26
- `All`: 25
- `GYL15.. JPP`: 24

## Unmapped catalog models

- Lexus GS200t: feed 'GS 200t' 0 cars
- Lexus IS F: feed 'IS F' 0 cars (excluded: catalog model with no feed cars as 'IS F' (inventory 2026-11-04); nothing to map)
- Lexus IS Turbo: feed 'IS Turbo' 0 cars
- Lexus LS600hL: feed 'LS 600h L' 1 cars (excluded: M6: the only feed 'LS 600h L' car decodes as another make (vPIC mismatch))
- Lexus RC Turbo: feed 'RC Turbo' 0 cars
- Lexus RC200t: feed 'RC 200t' 0 cars
- Lexus RC300: feed 'RC 300' 0 cars
- Toyota C-HR: feed 'C-HR' 12 cars
- Toyota Corolla Cross: feed 'Corolla Cross' 0 cars
- Toyota Crown: feed 'Crown' 0 cars
- Toyota Crown Signia: feed 'Crown Signia' 0 cars
- Toyota Grand Highlander: feed 'Grand Highlander' 0 cars
- Toyota Prius AWD-e: feed 'Prius AWD-e' 0 cars (excluded: catalog model with no feed cars as 'Prius AWD-e' (inventory 2026-11-04); nothing to map)
- Toyota RAV4 Prime: feed 'RAV4 Prime' 0 cars
- Toyota T100: feed 'T100' 57 cars
