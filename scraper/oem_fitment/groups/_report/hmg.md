# OEM curation report: hmg

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-06T00:42:44Z.

- records 6450, classes 6266, list rows 18066, year manifests 55, cells 7444
- Verified groups 0, engine vg groups 0, Likely groups 6
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.hyundaipartsdeal.com, www.kiapartsnow.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.hyundaipartsdeal.com: only 0% of its 3795 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)
- www.kiapartsnow.com: only 0% of its 3733 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 211 |
| ac-compressor | no_records | - | 1326 |
| ac-compressor | not_closed | no_list_manifest | 3701 |
| ac-compressor | not_closed | no_year_manifest | 15369 |
| ac-compressor | not_closed | unattested | 19 |
| ac-compressor | not_closed | unverified_product | 26 |
| ac-compressor | not_closed | variant_unread | 1309 |
| alternator | unmapped | - | 211 |
| alternator | no_records | - | 1115 |
| alternator | not_closed | no_list_manifest | 3675 |
| alternator | not_closed | no_year_manifest | 15632 |
| alternator | not_closed | unverified_product | 19 |
| alternator | not_closed | variant_unread | 1309 |
| bumper-front | unmapped | - | 211 |
| bumper-front | no_records | - | 1991 |
| bumper-front | not_closed | no_year_manifest | 14691 |
| bumper-front | not_closed | unread_sibling_page | 3759 |
| bumper-front | not_closed | variant_unread | 1309 |
| bumper-rear | unmapped | - | 211 |
| bumper-rear | no_records | - | 2167 |
| bumper-rear | not_closed | no_year_manifest | 14515 |
| bumper-rear | not_closed | unread_sibling_page | 3759 |
| bumper-rear | not_closed | variant_unread | 1309 |
| climate-control | unmapped | - | 211 |
| climate-control | no_records | - | 2600 |
| climate-control | not_closed | no_list_manifest | 3701 |
| climate-control | not_closed | no_year_manifest | 14095 |
| climate-control | not_closed | unread_sibling_page | 45 |
| climate-control | not_closed | variant_unread | 1309 |
| door-front | unmapped | - | 211 |
| door-front | no_records | - | 2003 |
| door-front | not_closed | no_year_manifest | 14679 |
| door-front | not_closed | unread_sibling_page | 3759 |
| door-front | not_closed | variant_unread | 1309 |
| door-rear | unmapped | - | 211 |
| door-rear | no_records | - | 2594 |
| door-rear | not_closed | no_year_manifest | 14152 |
| door-rear | not_closed | unread_sibling_page | 3695 |
| door-rear | not_closed | variant_unread | 1309 |
| fender | unmapped | - | 211 |
| fender | no_records | - | 1849 |
| fender | not_closed | no_year_manifest | 14833 |
| fender | not_closed | unread_sibling_page | 3759 |
| fender | not_closed | variant_unread | 1309 |
| fuel-pump-module | unmapped | - | 211 |
| fuel-pump-module | no_records | - | 2293 |
| fuel-pump-module | not_closed | no_list_manifest | 3691 |
| fuel-pump-module | not_closed | no_year_manifest | 14412 |
| fuel-pump-module | not_closed | unread_sibling_page | 45 |
| fuel-pump-module | not_closed | variant_unread | 1309 |
| gauge-cluster | unmapped | - | 211 |
| gauge-cluster | no_records | - | 2898 |
| gauge-cluster | not_closed | no_year_manifest | 13784 |
| gauge-cluster | not_closed | suspect_variant | 85 |
| gauge-cluster | not_closed | unattested | 560 |
| gauge-cluster | not_closed | unread_sibling_page | 3114 |
| gauge-cluster | not_closed | variant_unread | 1309 |
| grille | unmapped | - | 211 |
| grille | no_records | - | 2825 |
| grille | not_closed | no_year_manifest | 13857 |
| grille | not_closed | suspect_variant | 4 |
| grille | not_closed | unattested | 2185 |
| grille | not_closed | uncrawled_chain_member | 1570 |
| grille | not_closed | variant_unread | 1309 |
| headlights | unmapped | - | 211 |
| headlights | no_records | - | 1679 |
| headlights | not_closed | no_list_manifest | 3701 |
| headlights | not_closed | no_year_manifest | 15016 |
| headlights | not_closed | unattested | 45 |
| headlights | not_closed | variant_unread | 1309 |
| hood | unmapped | - | 211 |
| hood | no_records | - | 1960 |
| hood | not_closed | no_year_manifest | 14722 |
| hood | not_closed | unread_sibling_page | 3759 |
| hood | not_closed | variant_unread | 1309 |
| ignition-coils | unmapped | - | 211 |
| ignition-coils | no_records | - | 392 |
| ignition-coils | not_closed | no_year_manifest | 16290 |
| ignition-coils | not_closed | unattested | 10 |
| ignition-coils | not_closed | unverified_product | 3749 |
| ignition-coils | not_closed | variant_unread | 1309 |
| liftgate | unmapped | - | 211 |
| liftgate | no_records | - | 12805 |
| liftgate | not_closed | no_year_manifest | 7711 |
| liftgate | not_closed | unattested | 973 |
| liftgate | not_closed | uncrawled_chain_member | 204 |
| liftgate | not_closed | variant_unread | 57 |
| power-steering-pump | unmapped | - | 211 |
| power-steering-pump | no_records | - | 13482 |
| power-steering-pump | not_closed | no_list_manifest | 1536 |
| power-steering-pump | not_closed | no_year_manifest | 6649 |
| power-steering-pump | not_closed | unread_sibling_page | 26 |
| power-steering-pump | not_closed | variant_unread | 57 |
| radiator | unmapped | - | 211 |
| radiator | no_records | - | 3526 |
| radiator | not_closed | no_year_manifest | 13193 |
| radiator | not_closed | unread_sibling_page | 3722 |
| radiator | not_closed | variant_unread | 1309 |
| side-mirrors | unmapped | - | 211 |
| side-mirrors | no_records | - | 1307 |
| side-mirrors | not_closed | no_list_manifest | 3628 |
| side-mirrors | not_closed | no_year_manifest | 15461 |
| side-mirrors | not_closed | unattested | 45 |
| side-mirrors | not_closed | variant_unread | 1309 |
| starter | unmapped | - | 211 |
| starter | no_records | - | 404 |
| starter | not_closed | no_list_manifest | 3681 |
| starter | not_closed | no_year_manifest | 16311 |
| starter | not_closed | unverified_product | 45 |
| starter | not_closed | variant_unread | 1309 |
| tail-lights | unmapped | - | 211 |
| tail-lights | no_records | - | 2419 |
| tail-lights | not_closed | no_list_manifest | 3701 |
| tail-lights | not_closed | no_year_manifest | 14276 |
| tail-lights | not_closed | unattested | 45 |
| tail-lights | not_closed | variant_unread | 1309 |
| throttle-body | unmapped | - | 211 |
| throttle-body | no_records | - | 2333 |
| throttle-body | not_closed | no_list_manifest | 3524 |
| throttle-body | not_closed | no_year_manifest | 14539 |
| throttle-body | not_closed | unattested | 45 |
| throttle-body | not_closed | variant_unread | 1309 |
| trunk-lid | unmapped | - | 211 |
| trunk-lid | no_records | - | 9425 |
| trunk-lid | not_closed | no_year_manifest | 8294 |
| trunk-lid | not_closed | unattested | 142 |
| trunk-lid | not_closed | unread_sibling_page | 2637 |
| trunk-lid | not_closed | variant_unread | 1252 |
| window-regulator | unmapped | - | 211 |
| window-regulator | no_records | - | 1169 |
| window-regulator | not_closed | no_list_manifest | 3705 |
| window-regulator | not_closed | no_year_manifest | 15522 |
| window-regulator | not_closed | unread_sibling_page | 45 |
| window-regulator | not_closed | variant_unread | 1309 |
| window-switch | unmapped | - | 211 |
| window-switch | no_records | - | 2553 |
| window-switch | not_closed | no_list_manifest | 3668 |
| window-switch | not_closed | no_year_manifest | 14175 |
| window-switch | not_closed | unread_sibling_page | 45 |
| window-switch | not_closed | variant_unread | 1309 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 211 |
| ac-compressor | no_records | - | 1326 |
| ac-compressor | split | option_split | 16530 |
| ac-compressor | conditional | conditional:engine_unattested | 3856 |
| ac-compressor | conditional | conditional:option | 38 |
| alternator | unmapped | - | 211 |
| alternator | no_records | - | 1115 |
| alternator | split | option_split | 16782 |
| alternator | conditional | conditional:engine_unattested | 3853 |
| bumper-front | unmapped | - | 211 |
| bumper-front | no_records | - | 1991 |
| bumper-front | split | option_split | 17152 |
| bumper-front | conditional | conditional:engine_unattested | 2524 |
| bumper-front | conditional | conditional:fuel | 4 |
| bumper-front | conditional | conditional:option | 36 |
| bumper-front | conditional | conditional:package | 43 |
| bumper-rear | unmapped | - | 211 |
| bumper-rear | no_records | - | 2167 |
| bumper-rear | split | option_split | 16803 |
| bumper-rear | conditional | conditional:engine_unattested | 2212 |
| bumper-rear | conditional | conditional:option | 568 |
| climate-control | unmapped | - | 211 |
| climate-control | no_records | - | 2600 |
| climate-control | split | option_split | 19115 |
| climate-control | conditional | conditional:engine_unattested | 35 |
| door-front | unmapped | - | 211 |
| door-front | no_records | - | 2003 |
| door-front | split | option_split | 9427 |
| door-front | conditional | conditional:engine_unattested | 10320 |
| door-rear | unmapped | - | 211 |
| door-rear | no_records | - | 2594 |
| door-rear | split | option_split | 10714 |
| door-rear | split | slot_missing | 308 |
| door-rear | conditional | conditional:engine_unattested | 8134 |
| fender | unmapped | - | 211 |
| fender | no_records | - | 1849 |
| fender | split | option_split | 5455 |
| fender | split | slot_missing | 28 |
| fender | conditional | conditional:body | 271 |
| fender | conditional | conditional:engine_unattested | 14147 |
| fuel-pump-module | unmapped | - | 211 |
| fuel-pump-module | no_records | - | 2293 |
| fuel-pump-module | split | option_split | 16395 |
| fuel-pump-module | conditional | conditional:engine_unattested | 3062 |
| gauge-cluster | unmapped | - | 211 |
| gauge-cluster | no_records | - | 2898 |
| gauge-cluster | split | no_candidates | 10 |
| gauge-cluster | split | option_split | 18703 |
| gauge-cluster | conditional | conditional:engine_unattested | 139 |
| grille | unmapped | - | 211 |
| grille | no_records | - | 2825 |
| grille | split | no_candidates | 25 |
| grille | split | option_split | 17754 |
| grille | conditional | conditional:engine_unattested | 1036 |
| grille | conditional | conditional:package | 110 |
| headlights | unmapped | - | 211 |
| headlights | no_records | - | 1679 |
| headlights | split | option_split | 16798 |
| headlights | split | slot_missing | 239 |
| headlights | conditional | conditional:engine_unattested | 2998 |
| headlights | conditional | conditional:option | 36 |
| hood | unmapped | - | 211 |
| hood | no_records | - | 1960 |
| hood | split | option_split | 3586 |
| hood | conditional | conditional:engine_unattested | 16204 |
| ignition-coils | unmapped | - | 211 |
| ignition-coils | no_records | - | 392 |
| ignition-coils | split | option_split | 13880 |
| ignition-coils | conditional | conditional:engine_unattested | 6175 |
| ignition-coils | conditional | conditional:package | 1303 |
| liftgate | unmapped | - | 211 |
| liftgate | no_records | - | 12805 |
| liftgate | split | option_split | 6585 |
| liftgate | conditional | conditional:engine_unattested | 2360 |
| power-steering-pump | unmapped | - | 211 |
| power-steering-pump | no_records | - | 13482 |
| power-steering-pump | split | option_split | 6255 |
| power-steering-pump | conditional | conditional:engine_unattested | 2013 |
| radiator | unmapped | - | 211 |
| radiator | no_records | - | 3526 |
| radiator | split | no_candidates | 602 |
| radiator | split | option_split | 16515 |
| radiator | conditional | conditional:engine_unattested | 1107 |
| side-mirrors | unmapped | - | 211 |
| side-mirrors | no_records | - | 1307 |
| side-mirrors | split | option_split | 19375 |
| side-mirrors | conditional | conditional:engine_unattested | 1068 |
| starter | unmapped | - | 211 |
| starter | no_records | - | 404 |
| starter | split | option_split | 20055 |
| starter | conditional | conditional:engine_unattested | 1291 |
| tail-lights | unmapped | - | 211 |
| tail-lights | no_records | - | 2419 |
| tail-lights | split | option_split | 18074 |
| tail-lights | conditional | conditional:engine_unattested | 1257 |
| throttle-body | unmapped | - | 211 |
| throttle-body | no_records | - | 2333 |
| throttle-body | split | option_split | 15106 |
| throttle-body | conditional | conditional:engine_unattested | 4311 |
| trunk-lid | unmapped | - | 211 |
| trunk-lid | no_records | - | 9425 |
| trunk-lid | split | no_candidates | 142 |
| trunk-lid | split | option_split | 4538 |
| trunk-lid | conditional | conditional:engine_unattested | 5919 |
| trunk-lid | conditional | conditional:option | 1399 |
| trunk-lid | conditional | conditional:package | 327 |
| window-regulator | unmapped | - | 211 |
| window-regulator | no_records | - | 1169 |
| window-regulator | split | packaging_incomplete | 897 |
| window-regulator | split | packaging_split | 12325 |
| window-regulator | split | packaging_unstated | 7359 |
| window-switch | unmapped | - | 211 |
| window-switch | no_records | - | 2553 |
| window-switch | split | option_split | 17241 |
| window-switch | split | position_missing | 1657 |
| window-switch | conditional | conditional:engine_unattested | 299 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 124
- disputed_class: 184
- rule_drift: 1
- universal_part_suspect: 3

## Unknown note clauses (top 30)

- `SPEEDOMETER TYPE - MPH(KMPH)`: 571
- `ESC (ELECTRONIC STABILITY CONTROL)`: 410
- `I.M.S`: 345
- `TIRE PRESSURE MONITORG SYS - HIGH LINE`: 338
- `VEHICLE PACKAGE - SPORTS`: 300
- `ABS (ANTI LOCK BRK SYS)`: 276
- `SIDE REPEATER LAMP (O/S MRR)`: 258
- `P/WINDOW DR'S - AUTO UP/DOWN & SAFETY`: 249
- `AUTO CRUISE CONTROL - CONVENTIONAL`: 235
- `SMART KEY-FR DR`: 219
- `MODEL YEAR PACKAGE - 16MY`: 212
- `AUTO CRUISE CONTROL - SMART`: 210
- `FOB KEY`: 204
- `BLIND SPOT DETECTION SYSTEM - RADAR TYPE`: 194
- `MODEL YEAR PACKAGE - 14MY`: 189
- `PARKG BRK CONTROL-EPB`: 183
- `COLOR - BODY COLOR`: 175
- `RR PARK'G ASSIST SYSTEM(RPAS)`: 173
- `TYPE - SEPARATED TYPE`: 168
- `Fit Note: HIGH GRADE`: 167
- `DRL - DEDICATED LED TYPE`: 163
- `CLUSTER TYPE - SUPER VISION 4.2" TFT LCD INFO`: 162
- `AUTONOMOUS EMERGENCY BRAKING - PEDESTRIAN`: 157
- `MDPS-BLAC-COLUMN`: 154
- `AIR VENTILATION SEAT`: 148
- `AUTONOMOUS EMERGENCY BRAKING - URBAN`: 146
- `AUTONOMOUS EMERGENCY BRAKING - CITY`: 143
- `MANUAL FOLD'G`: 137
- `SPEAKER BRAND - PREMIUM`: 135
- `KEYLESS ENTRY-B/ALARM`: 132

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
