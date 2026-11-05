# OEM curation report: hmg

Raw: `ceccc800d7ba22c0291121baabb0a9292eb8f271` @ `ceccc800d7ba`; as of 2026-11-05T22:27:13Z.

- records 5763, classes 5590, list rows 8168, year manifests 22, cells 6510
- Verified groups 0, engine vg groups 0, Likely groups 413
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.hyundaipartsdeal.com, www.kiapartsnow.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.hyundaipartsdeal.com: only 0% of its 3066 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)
- www.kiapartsnow.com: only 0% of its 3733 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 216 |
| ac-compressor | no_records | - | 1324 |
| ac-compressor | not_closed | no_list_manifest | 2636 |
| ac-compressor | not_closed | no_year_manifest | 16392 |
| ac-compressor | not_closed | unattested | 19 |
| ac-compressor | not_closed | unverified_product | 25 |
| ac-compressor | not_closed | variant_unread | 1198 |
| alternator | unmapped | - | 216 |
| alternator | no_records | - | 1113 |
| alternator | not_closed | no_list_manifest | 2639 |
| alternator | not_closed | no_year_manifest | 16625 |
| alternator | not_closed | unverified_product | 19 |
| alternator | not_closed | variant_unread | 1198 |
| bumper-front | unmapped | - | 216 |
| bumper-front | no_records | - | 3766 |
| bumper-front | not_closed | no_year_manifest | 13990 |
| bumper-front | not_closed | unread_sibling_page | 2640 |
| bumper-front | not_closed | variant_unread | 1198 |
| bumper-rear | unmapped | - | 216 |
| bumper-rear | no_records | - | 3983 |
| bumper-rear | not_closed | no_year_manifest | 13773 |
| bumper-rear | not_closed | unread_sibling_page | 2640 |
| bumper-rear | not_closed | variant_unread | 1198 |
| climate-control | unmapped | - | 216 |
| climate-control | no_records | - | 2596 |
| climate-control | not_closed | no_list_manifest | 2636 |
| climate-control | not_closed | no_year_manifest | 15120 |
| climate-control | not_closed | unread_sibling_page | 44 |
| climate-control | not_closed | variant_unread | 1198 |
| door-front | unmapped | - | 216 |
| door-front | no_records | - | 3795 |
| door-front | not_closed | no_year_manifest | 13961 |
| door-front | not_closed | unread_sibling_page | 2640 |
| door-front | not_closed | variant_unread | 1198 |
| door-rear | unmapped | - | 216 |
| door-rear | no_records | - | 4098 |
| door-rear | not_closed | no_year_manifest | 13658 |
| door-rear | not_closed | unread_sibling_page | 2640 |
| door-rear | not_closed | variant_unread | 1198 |
| fender | unmapped | - | 216 |
| fender | no_records | - | 3784 |
| fender | not_closed | no_year_manifest | 13972 |
| fender | not_closed | unread_sibling_page | 2640 |
| fender | not_closed | variant_unread | 1198 |
| fuel-pump-module | unmapped | - | 216 |
| fuel-pump-module | no_records | - | 2281 |
| fuel-pump-module | not_closed | no_list_manifest | 2636 |
| fuel-pump-module | not_closed | no_year_manifest | 15435 |
| fuel-pump-module | not_closed | unread_sibling_page | 44 |
| fuel-pump-module | not_closed | variant_unread | 1198 |
| gauge-cluster | unmapped | - | 216 |
| gauge-cluster | no_records | - | 4619 |
| gauge-cluster | not_closed | no_year_manifest | 13137 |
| gauge-cluster | not_closed | unattested | 393 |
| gauge-cluster | not_closed | unread_sibling_page | 2247 |
| gauge-cluster | not_closed | variant_unread | 1198 |
| grille | unmapped | - | 216 |
| grille | no_records | - | 4416 |
| grille | not_closed | no_year_manifest | 13340 |
| grille | not_closed | suspect_variant | 3 |
| grille | not_closed | unattested | 1488 |
| grille | not_closed | uncrawled_chain_member | 1149 |
| grille | not_closed | variant_unread | 1198 |
| headlights | unmapped | - | 216 |
| headlights | no_records | - | 1672 |
| headlights | not_closed | no_list_manifest | 2636 |
| headlights | not_closed | no_year_manifest | 16044 |
| headlights | not_closed | unattested | 44 |
| headlights | not_closed | variant_unread | 1198 |
| hood | unmapped | - | 216 |
| hood | no_records | - | 3849 |
| hood | not_closed | no_year_manifest | 13907 |
| hood | not_closed | unread_sibling_page | 2640 |
| hood | not_closed | variant_unread | 1198 |
| ignition-coils | unmapped | - | 216 |
| ignition-coils | no_records | - | 532 |
| ignition-coils | not_closed | no_list_manifest | 44 |
| ignition-coils | not_closed | no_year_manifest | 17180 |
| ignition-coils | not_closed | uncrawled_chain_member | 1 |
| ignition-coils | not_closed | unverified_product | 2639 |
| ignition-coils | not_closed | variant_unread | 1198 |
| liftgate | unmapped | - | 216 |
| liftgate | no_records | - | 13747 |
| liftgate | not_closed | no_year_manifest | 7153 |
| liftgate | not_closed | unattested | 487 |
| liftgate | not_closed | uncrawled_chain_member | 207 |
| power-steering-pump | unmapped | - | 216 |
| power-steering-pump | no_records | - | 13330 |
| power-steering-pump | not_closed | no_list_manifest | 1055 |
| power-steering-pump | not_closed | no_year_manifest | 7184 |
| power-steering-pump | not_closed | unread_sibling_page | 25 |
| radiator | unmapped | - | 216 |
| radiator | no_records | - | 5414 |
| radiator | not_closed | no_list_manifest | 19 |
| radiator | not_closed | no_year_manifest | 12323 |
| radiator | not_closed | unread_sibling_page | 2640 |
| radiator | not_closed | variant_unread | 1198 |
| side-mirrors | unmapped | - | 216 |
| side-mirrors | no_records | - | 1298 |
| side-mirrors | not_closed | no_list_manifest | 2636 |
| side-mirrors | not_closed | no_year_manifest | 16418 |
| side-mirrors | not_closed | unattested | 44 |
| side-mirrors | not_closed | variant_unread | 1198 |
| starter | unmapped | - | 216 |
| starter | no_records | - | 401 |
| starter | not_closed | no_list_manifest | 2636 |
| starter | not_closed | no_year_manifest | 17315 |
| starter | not_closed | unverified_product | 44 |
| starter | not_closed | variant_unread | 1198 |
| tail-lights | unmapped | - | 216 |
| tail-lights | no_records | - | 2414 |
| tail-lights | not_closed | no_list_manifest | 2636 |
| tail-lights | not_closed | no_year_manifest | 15302 |
| tail-lights | not_closed | unattested | 44 |
| tail-lights | not_closed | variant_unread | 1198 |
| throttle-body | unmapped | - | 216 |
| throttle-body | no_records | - | 2333 |
| throttle-body | not_closed | no_list_manifest | 2566 |
| throttle-body | not_closed | no_year_manifest | 15453 |
| throttle-body | not_closed | unattested | 44 |
| throttle-body | not_closed | variant_unread | 1198 |
| trunk-lid | unmapped | - | 216 |
| trunk-lid | no_records | - | 9829 |
| trunk-lid | not_closed | no_year_manifest | 8425 |
| trunk-lid | not_closed | unattested | 100 |
| trunk-lid | not_closed | unread_sibling_page | 2042 |
| trunk-lid | not_closed | variant_unread | 1198 |
| window-regulator | unmapped | - | 216 |
| window-regulator | no_records | - | 1167 |
| window-regulator | not_closed | no_list_manifest | 2637 |
| window-regulator | not_closed | no_year_manifest | 16548 |
| window-regulator | not_closed | unread_sibling_page | 44 |
| window-regulator | not_closed | variant_unread | 1198 |
| window-switch | unmapped | - | 216 |
| window-switch | no_records | - | 2555 |
| window-switch | not_closed | no_list_manifest | 2636 |
| window-switch | not_closed | no_year_manifest | 15161 |
| window-switch | not_closed | unread_sibling_page | 44 |
| window-switch | not_closed | variant_unread | 1198 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 216 |
| ac-compressor | no_records | - | 1324 |
| ac-compressor | split | option_split | 16402 |
| ac-compressor | conditional | conditional:engine_unattested | 3830 |
| ac-compressor | conditional | conditional:option | 38 |
| alternator | unmapped | - | 216 |
| alternator | no_records | - | 1113 |
| alternator | split | option_split | 16640 |
| alternator | conditional | conditional:engine_unattested | 3841 |
| bumper-front | unmapped | - | 216 |
| bumper-front | no_records | - | 3766 |
| bumper-front | split | option_split | 15640 |
| bumper-front | conditional | conditional:engine_unattested | 2188 |
| bumper-rear | unmapped | - | 216 |
| bumper-rear | no_records | - | 3983 |
| bumper-rear | split | option_split | 15145 |
| bumper-rear | conditional | conditional:engine_unattested | 1932 |
| bumper-rear | conditional | conditional:option | 534 |
| climate-control | unmapped | - | 216 |
| climate-control | no_records | - | 2596 |
| climate-control | split | option_split | 18960 |
| climate-control | conditional | conditional:engine_unattested | 38 |
| door-front | unmapped | - | 216 |
| door-front | no_records | - | 3795 |
| door-front | split | option_split | 8552 |
| door-front | conditional | conditional:engine_unattested | 9247 |
| door-rear | unmapped | - | 216 |
| door-rear | no_records | - | 4098 |
| door-rear | split | option_split | 9774 |
| door-rear | split | slot_missing | 296 |
| door-rear | conditional | conditional:engine_unattested | 7426 |
| fender | unmapped | - | 216 |
| fender | no_records | - | 3784 |
| fender | split | option_split | 4742 |
| fender | split | slot_missing | 27 |
| fender | conditional | conditional:body | 130 |
| fender | conditional | conditional:engine_unattested | 12911 |
| fuel-pump-module | unmapped | - | 216 |
| fuel-pump-module | no_records | - | 2281 |
| fuel-pump-module | split | option_split | 16243 |
| fuel-pump-module | conditional | conditional:engine_unattested | 3070 |
| gauge-cluster | unmapped | - | 216 |
| gauge-cluster | no_records | - | 4619 |
| gauge-cluster | split | no_candidates | 1 |
| gauge-cluster | split | option_split | 16899 |
| gauge-cluster | conditional | conditional:engine_unattested | 75 |
| grille | unmapped | - | 216 |
| grille | no_records | - | 4416 |
| grille | split | option_split | 16473 |
| grille | conditional | conditional:engine_unattested | 605 |
| grille | conditional | conditional:package | 100 |
| headlights | unmapped | - | 216 |
| headlights | no_records | - | 1672 |
| headlights | split | option_split | 16643 |
| headlights | split | slot_missing | 237 |
| headlights | conditional | conditional:engine_unattested | 3007 |
| headlights | conditional | conditional:option | 35 |
| hood | unmapped | - | 216 |
| hood | no_records | - | 3849 |
| hood | split | option_split | 3174 |
| hood | conditional | conditional:engine_unattested | 14571 |
| ignition-coils | unmapped | - | 216 |
| ignition-coils | no_records | - | 532 |
| ignition-coils | split | option_split | 13265 |
| ignition-coils | conditional | conditional:engine_unattested | 6724 |
| ignition-coils | conditional | conditional:package | 1073 |
| liftgate | unmapped | - | 216 |
| liftgate | no_records | - | 13747 |
| liftgate | split | option_split | 5851 |
| liftgate | conditional | conditional:engine_unattested | 1996 |
| power-steering-pump | unmapped | - | 216 |
| power-steering-pump | no_records | - | 13330 |
| power-steering-pump | split | option_split | 6252 |
| power-steering-pump | conditional | conditional:engine_unattested | 2012 |
| radiator | unmapped | - | 216 |
| radiator | no_records | - | 5414 |
| radiator | split | no_candidates | 351 |
| radiator | split | option_split | 15260 |
| radiator | conditional | conditional:engine_unattested | 569 |
| side-mirrors | unmapped | - | 216 |
| side-mirrors | no_records | - | 1298 |
| side-mirrors | split | option_split | 19239 |
| side-mirrors | conditional | conditional:engine_unattested | 1057 |
| starter | unmapped | - | 216 |
| starter | no_records | - | 401 |
| starter | split | option_split | 19912 |
| starter | conditional | conditional:engine_unattested | 1281 |
| tail-lights | unmapped | - | 216 |
| tail-lights | no_records | - | 2414 |
| tail-lights | split | option_split | 17911 |
| tail-lights | conditional | conditional:engine_unattested | 1269 |
| throttle-body | unmapped | - | 216 |
| throttle-body | no_records | - | 2333 |
| throttle-body | split | option_split | 14977 |
| throttle-body | conditional | conditional:engine_unattested | 4284 |
| trunk-lid | unmapped | - | 216 |
| trunk-lid | no_records | - | 9829 |
| trunk-lid | split | no_candidates | 100 |
| trunk-lid | split | option_split | 4392 |
| trunk-lid | conditional | conditional:engine_unattested | 5608 |
| trunk-lid | conditional | conditional:option | 1345 |
| trunk-lid | conditional | conditional:package | 320 |
| window-regulator | unmapped | - | 216 |
| window-regulator | no_records | - | 1167 |
| window-regulator | split | packaging_incomplete | 900 |
| window-regulator | split | packaging_split | 12178 |
| window-regulator | split | packaging_unstated | 7349 |
| window-switch | unmapped | - | 216 |
| window-switch | no_records | - | 2555 |
| window-switch | split | option_split | 17089 |
| window-switch | split | position_missing | 1643 |
| window-switch | conditional | conditional:engine_unattested | 307 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 63
- disputed_class: 173
- rule_drift: 1
- universal_part_suspect: 3

## Unknown note clauses (top 30)

- `I.M.S`: 345
- `SPEEDOMETER TYPE - MPH(KMPH)`: 339
- `SIDE REPEATER LAMP (O/S MRR)`: 258
- `P/WINDOW DR'S - AUTO UP/DOWN & SAFETY`: 249
- `VEHICLE PACKAGE - SPORTS`: 220
- `ESC (ELECTRONIC STABILITY CONTROL)`: 199
- `MODEL YEAR PACKAGE - 16MY`: 188
- `FOB KEY`: 182
- `AUTO CRUISE CONTROL - CONVENTIONAL`: 177
- `TIRE PRESSURE MONITORG SYS - HIGH LINE`: 174
- `COLOR - BODY COLOR`: 172
- `MODEL YEAR PACKAGE - 14MY`: 149
- `AIR VENTILATION SEAT`: 148
- `ABS (ANTI LOCK BRK SYS)`: 147
- `AUTO CRUISE CONTROL - SMART`: 145
- `MANUAL FOLD'G`: 137
- `SMART KEY-FR DR`: 135
- `KEYLESS ENTRY-B/ALARM`: 132
- `SPEAKER BRAND - PREMIUM`: 132
- `ELECTRIC FOLD'G CONTROL`: 129
- `BLIND SPOT DETECTION SYSTEM - RADAR TYPE`: 124
- `Fit Note: RR COMBI LAMP - LED TYPE`: 116
- `FR COOLER - DUAL FULL AUTO A/CON`: 112
- `FR COOLER - MANUAL A/CON`: 110
- `SMART CRUISE CONTROL`: 109
- `INSIDE HNDL OVER RIDE - DR'S & PA'S SIDE`: 106
- `SAFETY WINDOW - FR DR(DRIVER'S)`: 106
- `P/WINDOW PA'S - AUTO UP/DOWN & SAFETY`: 103
- `RR PARK'G ASSIST SYSTEM(RPAS)`: 103
- `Fit Note: HIGH GRADE`: 102

## Unmapped catalog models

- Hyundai Elantra N: feed 'Elantra N' 0 cars
- Hyundai Genesis G70: feed 'Genesis G70' 0 cars
- Hyundai Genesis G80: feed 'Genesis G80' 0 cars
- Hyundai Genesis G90: feed 'Genesis G90' 0 cars
- Hyundai Kona N: feed 'Kona N' 0 cars
- Hyundai Santa Cruz: feed 'Santa Cruz' 0 cars
- Kia Carnival: feed 'Carnival' 0 cars
- Kia Spectra SX: feed 'Spectra SX' 0 cars
- Kia Spectra5 SX: feed 'Spectra5 SX' 0 cars
