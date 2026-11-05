# OEM curation report: hmg

Raw: `50ac4a48cdc62d02bd819bec33a67d0f07d8a71e` @ `50ac4a48cdc6`; as of 2026-11-05T12:41:53Z.

- records 4851, classes 4706, list rows 0, year manifests 0, cells 5293
- Verified groups 0, engine vg groups 0, Likely groups 404
- blocked sites: www.hyundaipartsdeal.com

## Gates standing for the whole namespace

- no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close (C1/C2); Verified is impossible by design until the crawler writes them
- no (site, category) of this namespace has passed the audit gate (CATEGORY_STATUS has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.hyundaipartsdeal.com, www.kiapartsnow.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.hyundaipartsdeal.com: only 0% of its 2180 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)
- www.kiapartsnow.com: only 0% of its 3615 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)
- blocked by the crawl breaker: www.hyundaipartsdeal.com (their cells never close, C9)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 215 |
| ac-compressor | no_records | - | 1330 |
| ac-compressor | not_closed | no_year_manifest | 20297 |
| alternator | unmapped | - | 215 |
| alternator | no_records | - | 1114 |
| alternator | not_closed | no_year_manifest | 20513 |
| bumper-front | unmapped | - | 215 |
| bumper-front | no_records | - | 13584 |
| bumper-front | not_closed | no_year_manifest | 8043 |
| bumper-rear | unmapped | - | 215 |
| bumper-rear | no_records | - | 13762 |
| bumper-rear | not_closed | no_year_manifest | 7865 |
| climate-control | unmapped | - | 215 |
| climate-control | no_records | - | 2649 |
| climate-control | not_closed | no_year_manifest | 18978 |
| door-front | unmapped | - | 215 |
| door-front | no_records | - | 13979 |
| door-front | not_closed | no_year_manifest | 7648 |
| door-rear | unmapped | - | 215 |
| door-rear | no_records | - | 14270 |
| door-rear | not_closed | no_year_manifest | 7357 |
| fender | unmapped | - | 215 |
| fender | no_records | - | 13633 |
| fender | not_closed | no_year_manifest | 7994 |
| fuel-pump-module | unmapped | - | 215 |
| fuel-pump-module | no_records | - | 2282 |
| fuel-pump-module | not_closed | no_year_manifest | 19345 |
| gauge-cluster | unmapped | - | 215 |
| gauge-cluster | no_records | - | 14114 |
| gauge-cluster | not_closed | no_year_manifest | 7513 |
| grille | unmapped | - | 215 |
| grille | no_records | - | 13557 |
| grille | not_closed | no_year_manifest | 8070 |
| headlights | unmapped | - | 215 |
| headlights | no_records | - | 1725 |
| headlights | not_closed | no_year_manifest | 19902 |
| hood | unmapped | - | 215 |
| hood | no_records | - | 14004 |
| hood | not_closed | no_year_manifest | 7623 |
| ignition-coils | unmapped | - | 215 |
| ignition-coils | no_records | - | 12579 |
| ignition-coils | not_closed | no_year_manifest | 9048 |
| liftgate | unmapped | - | 215 |
| liftgate | no_records | - | 16186 |
| liftgate | not_closed | no_year_manifest | 5441 |
| power-steering-pump | unmapped | - | 215 |
| power-steering-pump | no_records | - | 13417 |
| power-steering-pump | not_closed | no_year_manifest | 8210 |
| radiator | unmapped | - | 215 |
| radiator | no_records | - | 14712 |
| radiator | not_closed | no_year_manifest | 6915 |
| side-mirrors | unmapped | - | 215 |
| side-mirrors | no_records | - | 1354 |
| side-mirrors | not_closed | no_year_manifest | 20273 |
| starter | unmapped | - | 215 |
| starter | no_records | - | 401 |
| starter | not_closed | no_year_manifest | 21226 |
| tail-lights | unmapped | - | 215 |
| tail-lights | no_records | - | 2471 |
| tail-lights | not_closed | no_year_manifest | 19156 |
| throttle-body | unmapped | - | 215 |
| throttle-body | no_records | - | 2401 |
| throttle-body | not_closed | no_year_manifest | 19226 |
| trunk-lid | unmapped | - | 215 |
| trunk-lid | no_records | - | 17464 |
| trunk-lid | not_closed | no_year_manifest | 4163 |
| window-regulator | unmapped | - | 215 |
| window-regulator | no_records | - | 1168 |
| window-regulator | not_closed | no_year_manifest | 20459 |
| window-switch | unmapped | - | 215 |
| window-switch | no_records | - | 2613 |
| window-switch | not_closed | no_year_manifest | 19014 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 215 |
| ac-compressor | no_records | - | 1330 |
| ac-compressor | split | option_split | 16364 |
| ac-compressor | conditional | conditional:notes_not_own_page | 2956 |
| ac-compressor | conditional | conditional:option | 38 |
| ac-compressor | conditional | conditional:option_layout | 939 |
| alternator | unmapped | - | 215 |
| alternator | no_records | - | 1114 |
| alternator | split | option_split | 16663 |
| alternator | conditional | conditional:notes_not_own_page | 3541 |
| alternator | conditional | conditional:option_layout | 309 |
| bumper-front | unmapped | - | 215 |
| bumper-front | no_records | - | 13584 |
| bumper-front | split | option_split | 6699 |
| bumper-front | conditional | conditional:notes_not_own_page | 988 |
| bumper-front | conditional | conditional:option_layout | 356 |
| bumper-rear | unmapped | - | 215 |
| bumper-rear | no_records | - | 13762 |
| bumper-rear | split | option_split | 7479 |
| bumper-rear | conditional | conditional:notes_not_own_page | 265 |
| bumper-rear | conditional | conditional:option_layout | 121 |
| climate-control | unmapped | - | 215 |
| climate-control | no_records | - | 2649 |
| climate-control | split | option_split | 18940 |
| climate-control | conditional | conditional:notes_not_own_page | 38 |
| door-front | unmapped | - | 215 |
| door-front | no_records | - | 13979 |
| door-front | split | option_split | 4010 |
| door-front | conditional | conditional:notes_not_own_page | 2566 |
| door-front | conditional | conditional:option_layout | 1072 |
| door-rear | unmapped | - | 215 |
| door-rear | no_records | - | 14270 |
| door-rear | split | option_split | 5826 |
| door-rear | conditional | conditional:notes_not_own_page | 1138 |
| door-rear | conditional | conditional:option_layout | 393 |
| fender | unmapped | - | 215 |
| fender | no_records | - | 13633 |
| fender | split | option_split | 2984 |
| fender | split | slot_missing | 27 |
| fender | conditional | conditional:notes_not_own_page | 3440 |
| fender | conditional | conditional:option_layout | 1543 |
| fuel-pump-module | unmapped | - | 215 |
| fuel-pump-module | no_records | - | 2282 |
| fuel-pump-module | split | option_split | 16201 |
| fuel-pump-module | conditional | conditional:notes_not_own_page | 2314 |
| fuel-pump-module | conditional | conditional:option_layout | 830 |
| gauge-cluster | unmapped | - | 215 |
| gauge-cluster | no_records | - | 14114 |
| gauge-cluster | split | option_split | 7513 |
| grille | unmapped | - | 215 |
| grille | no_records | - | 13557 |
| grille | split | option_split | 8043 |
| grille | conditional | conditional:notes_not_own_page | 27 |
| headlights | unmapped | - | 215 |
| headlights | no_records | - | 1725 |
| headlights | split | option_split | 16623 |
| headlights | split | slot_missing | 238 |
| headlights | conditional | conditional:notes_not_own_page | 2142 |
| headlights | conditional | conditional:option | 35 |
| headlights | conditional | conditional:option_layout | 864 |
| hood | unmapped | - | 215 |
| hood | no_records | - | 14004 |
| hood | split | option_split | 260 |
| hood | conditional | conditional:notes_not_own_page | 4974 |
| hood | conditional | conditional:option_layout | 2389 |
| ignition-coils | unmapped | - | 215 |
| ignition-coils | no_records | - | 12579 |
| ignition-coils | split | option_split | 5873 |
| ignition-coils | conditional | conditional:notes_not_own_page | 3110 |
| ignition-coils | conditional | conditional:option_layout | 65 |
| liftgate | unmapped | - | 215 |
| liftgate | no_records | - | 16186 |
| liftgate | split | option_split | 3618 |
| liftgate | conditional | conditional:notes_not_own_page | 1268 |
| liftgate | conditional | conditional:option_layout | 555 |
| power-steering-pump | unmapped | - | 215 |
| power-steering-pump | no_records | - | 13417 |
| power-steering-pump | split | option_split | 6252 |
| power-steering-pump | conditional | conditional:notes_not_own_page | 1400 |
| power-steering-pump | conditional | conditional:option_layout | 558 |
| radiator | unmapped | - | 215 |
| radiator | no_records | - | 14712 |
| radiator | split | option_split | 6437 |
| radiator | conditional | conditional:notes_not_own_page | 323 |
| radiator | conditional | conditional:option_layout | 155 |
| side-mirrors | unmapped | - | 215 |
| side-mirrors | no_records | - | 1354 |
| side-mirrors | split | option_split | 19221 |
| side-mirrors | conditional | conditional:notes_not_own_page | 1052 |
| starter | unmapped | - | 215 |
| starter | no_records | - | 401 |
| starter | split | option_split | 19946 |
| starter | conditional | conditional:notes_not_own_page | 1256 |
| starter | conditional | conditional:option_layout | 24 |
| tail-lights | unmapped | - | 215 |
| tail-lights | no_records | - | 2471 |
| tail-lights | split | option_split | 17936 |
| tail-lights | conditional | conditional:notes_not_own_page | 1005 |
| tail-lights | conditional | conditional:option_layout | 215 |
| throttle-body | unmapped | - | 215 |
| throttle-body | no_records | - | 2401 |
| throttle-body | split | option_split | 14998 |
| throttle-body | conditional | conditional:notes_not_own_page | 3454 |
| throttle-body | conditional | conditional:option_layout | 774 |
| trunk-lid | unmapped | - | 215 |
| trunk-lid | no_records | - | 17464 |
| trunk-lid | split | option_split | 3723 |
| trunk-lid | conditional | conditional:notes_not_own_page | 306 |
| trunk-lid | conditional | conditional:option_layout | 134 |
| window-regulator | unmapped | - | 215 |
| window-regulator | no_records | - | 1168 |
| window-regulator | split | packaging_incomplete | 957 |
| window-regulator | split | packaging_split | 12135 |
| window-regulator | split | packaging_unstated | 7367 |
| window-switch | unmapped | - | 215 |
| window-switch | no_records | - | 2613 |
| window-switch | split | option_split | 17065 |
| window-switch | split | position_missing | 1639 |
| window-switch | conditional | conditional:option_layout | 310 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- disputed_class: 145
- universal_part_suspect: 1

## Unknown note clauses (top 30)

- `I.M.S`: 345
- `P/WINDOW DR'S - AUTO UP/DOWN & SAFETY`: 249
- `SIDE REPEATER LAMP (O/S MRR)`: 248
- `COLOR - BODY COLOR`: 158
- `AIR VENTILATION SEAT`: 148
- `MANUAL FOLD'G`: 137
- `SPEAKER BRAND - PREMIUM`: 132
- `ELECTRIC FOLD'G CONTROL`: 129
- `Fit Note: RR COMBI LAMP - LED TYPE`: 116
- `KEYLESS ENTRY-B/ALARM`: 116
- `FR COOLER - DUAL FULL AUTO A/CON`: 112
- `SMART KEY-FR DR`: 108
- `INSIDE HNDL OVER RIDE - DR'S & PA'S SIDE`: 106
- `FR COOLER - MANUAL A/CON`: 104
- `P/WINDOW PA'S - AUTO UP/DOWN & SAFETY`: 103
- `SAFETY WINDOW - FR DR(DRIVER'S)`: 102
- `GRIP HANDLE`: 96
- `LEVER FINISH'G - METAL PAINT`: 94
- `COLOR PACKAGE - TYPE 1`: 88
- `Fit Note: PASS'S SIDE - ELECTRIC HTD-CONV`: 83
- `CLUSTER IONIZER`: 82
- `LEVER FINISH'G - CR COAT'G`: 80
- `EXTERNAL AMP - JBL AMP`: 75
- `Fit Note: RR COMBI LAMP - NON LED TYPE`: 74
- `AUTO DEFOG SYSTEM`: 73
- `Fit Note: DRIVER'S SIDE - ELECTRIC HTD-FLAT`: 70
- `HID (ADAPTIVE FR LIGHT SYSTEM)`: 68
- `SEAT WARMER (HEATER) - 3-STEPS (BUTTON)`: 67
- `Fit Note: CENTRAL DR LOCK/UNLOCK - DR'S & PA'S CTRL`: 66
- `[Sedan - 5Door 5P]`: 64

## Unmapped catalog models

- Hyundai Elantra N: feed 'Elantra N' 0 cars
- Hyundai Kona N: feed 'Kona N' 0 cars
- Hyundai Santa Cruz: feed 'Santa Cruz' 0 cars
- Kia Carnival: feed 'Carnival' 0 cars
- Kia Spectra SX: feed 'Spectra SX' 0 cars
- Kia Spectra5 SX: feed 'Spectra5 SX' 0 cars
