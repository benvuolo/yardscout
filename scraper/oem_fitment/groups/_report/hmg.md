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
| ac-compressor | unmapped | - | 217 |
| ac-compressor | no_records | - | 1325 |
| ac-compressor | not_closed | no_list_manifest | 3674 |
| ac-compressor | not_closed | no_year_manifest | 15268 |
| ac-compressor | not_closed | unattested | 19 |
| ac-compressor | not_closed | unverified_product | 24 |
| ac-compressor | not_closed | variant_unread | 1286 |
| alternator | unmapped | - | 217 |
| alternator | no_records | - | 1107 |
| alternator | not_closed | no_list_manifest | 3648 |
| alternator | not_closed | no_year_manifest | 15536 |
| alternator | not_closed | unverified_product | 19 |
| alternator | not_closed | variant_unread | 1286 |
| bumper-front | unmapped | - | 217 |
| bumper-front | no_records | - | 1981 |
| bumper-front | not_closed | no_year_manifest | 14598 |
| bumper-front | not_closed | unread_sibling_page | 3731 |
| bumper-front | not_closed | variant_unread | 1286 |
| bumper-rear | unmapped | - | 217 |
| bumper-rear | no_records | - | 2154 |
| bumper-rear | not_closed | no_year_manifest | 14425 |
| bumper-rear | not_closed | unread_sibling_page | 3731 |
| bumper-rear | not_closed | variant_unread | 1286 |
| climate-control | unmapped | - | 217 |
| climate-control | no_records | - | 2589 |
| climate-control | not_closed | no_list_manifest | 3674 |
| climate-control | not_closed | no_year_manifest | 14004 |
| climate-control | not_closed | unread_sibling_page | 43 |
| climate-control | not_closed | variant_unread | 1286 |
| door-front | unmapped | - | 217 |
| door-front | no_records | - | 1999 |
| door-front | not_closed | no_year_manifest | 14580 |
| door-front | not_closed | unread_sibling_page | 3731 |
| door-front | not_closed | variant_unread | 1286 |
| door-rear | unmapped | - | 217 |
| door-rear | no_records | - | 2588 |
| door-rear | not_closed | no_year_manifest | 14056 |
| door-rear | not_closed | unread_sibling_page | 3666 |
| door-rear | not_closed | variant_unread | 1286 |
| fender | unmapped | - | 217 |
| fender | no_records | - | 1847 |
| fender | not_closed | no_year_manifest | 14732 |
| fender | not_closed | unread_sibling_page | 3731 |
| fender | not_closed | variant_unread | 1286 |
| fuel-pump-module | unmapped | - | 217 |
| fuel-pump-module | no_records | - | 2277 |
| fuel-pump-module | not_closed | no_list_manifest | 3664 |
| fuel-pump-module | not_closed | no_year_manifest | 14326 |
| fuel-pump-module | not_closed | unread_sibling_page | 43 |
| fuel-pump-module | not_closed | variant_unread | 1286 |
| gauge-cluster | unmapped | - | 217 |
| gauge-cluster | no_records | - | 2881 |
| gauge-cluster | not_closed | no_year_manifest | 13698 |
| gauge-cluster | not_closed | suspect_variant | 86 |
| gauge-cluster | not_closed | unattested | 553 |
| gauge-cluster | not_closed | unread_sibling_page | 3092 |
| gauge-cluster | not_closed | variant_unread | 1286 |
| grille | unmapped | - | 217 |
| grille | no_records | - | 2812 |
| grille | not_closed | no_year_manifest | 13767 |
| grille | not_closed | suspect_variant | 4 |
| grille | not_closed | unattested | 2177 |
| grille | not_closed | uncrawled_chain_member | 1550 |
| grille | not_closed | variant_unread | 1286 |
| headlights | unmapped | - | 217 |
| headlights | no_records | - | 1671 |
| headlights | not_closed | no_list_manifest | 3674 |
| headlights | not_closed | no_year_manifest | 14922 |
| headlights | not_closed | unattested | 43 |
| headlights | not_closed | variant_unread | 1286 |
| hood | unmapped | - | 217 |
| hood | no_records | - | 1955 |
| hood | not_closed | no_year_manifest | 14624 |
| hood | not_closed | unread_sibling_page | 3731 |
| hood | not_closed | variant_unread | 1286 |
| ignition-coils | unmapped | - | 217 |
| ignition-coils | no_records | - | 391 |
| ignition-coils | not_closed | no_year_manifest | 16188 |
| ignition-coils | not_closed | unattested | 10 |
| ignition-coils | not_closed | uncrawled_chain_member | 1 |
| ignition-coils | not_closed | unverified_product | 3720 |
| ignition-coils | not_closed | variant_unread | 1286 |
| liftgate | unmapped | - | 217 |
| liftgate | no_records | - | 12725 |
| liftgate | not_closed | no_year_manifest | 7650 |
| liftgate | not_closed | unattested | 965 |
| liftgate | not_closed | uncrawled_chain_member | 206 |
| liftgate | not_closed | variant_unread | 50 |
| power-steering-pump | unmapped | - | 217 |
| power-steering-pump | no_records | - | 13349 |
| power-steering-pump | not_closed | no_list_manifest | 1540 |
| power-steering-pump | not_closed | no_year_manifest | 6633 |
| power-steering-pump | not_closed | unread_sibling_page | 24 |
| power-steering-pump | not_closed | variant_unread | 50 |
| radiator | unmapped | - | 217 |
| radiator | no_records | - | 3518 |
| radiator | not_closed | no_year_manifest | 13098 |
| radiator | not_closed | unread_sibling_page | 3694 |
| radiator | not_closed | variant_unread | 1286 |
| side-mirrors | unmapped | - | 217 |
| side-mirrors | no_records | - | 1295 |
| side-mirrors | not_closed | no_list_manifest | 3604 |
| side-mirrors | not_closed | no_year_manifest | 15368 |
| side-mirrors | not_closed | unattested | 43 |
| side-mirrors | not_closed | variant_unread | 1286 |
| starter | unmapped | - | 217 |
| starter | no_records | - | 401 |
| starter | not_closed | no_list_manifest | 3654 |
| starter | not_closed | no_year_manifest | 16212 |
| starter | not_closed | unverified_product | 43 |
| starter | not_closed | variant_unread | 1286 |
| tail-lights | unmapped | - | 217 |
| tail-lights | no_records | - | 2410 |
| tail-lights | not_closed | no_list_manifest | 3674 |
| tail-lights | not_closed | no_year_manifest | 14183 |
| tail-lights | not_closed | unattested | 43 |
| tail-lights | not_closed | variant_unread | 1286 |
| throttle-body | unmapped | - | 217 |
| throttle-body | no_records | - | 2328 |
| throttle-body | not_closed | no_list_manifest | 3489 |
| throttle-body | not_closed | no_year_manifest | 14450 |
| throttle-body | not_closed | unattested | 43 |
| throttle-body | not_closed | variant_unread | 1286 |
| trunk-lid | unmapped | - | 217 |
| trunk-lid | no_records | - | 9370 |
| trunk-lid | not_closed | no_year_manifest | 8243 |
| trunk-lid | not_closed | unattested | 139 |
| trunk-lid | not_closed | unread_sibling_page | 2608 |
| trunk-lid | not_closed | variant_unread | 1236 |
| window-regulator | unmapped | - | 217 |
| window-regulator | no_records | - | 1169 |
| window-regulator | not_closed | no_list_manifest | 3679 |
| window-regulator | not_closed | no_year_manifest | 15419 |
| window-regulator | not_closed | unread_sibling_page | 43 |
| window-regulator | not_closed | variant_unread | 1286 |
| window-switch | unmapped | - | 217 |
| window-switch | no_records | - | 2549 |
| window-switch | not_closed | no_list_manifest | 3642 |
| window-switch | not_closed | no_year_manifest | 14076 |
| window-switch | not_closed | unread_sibling_page | 43 |
| window-switch | not_closed | variant_unread | 1286 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 217 |
| ac-compressor | no_records | - | 1325 |
| ac-compressor | split | option_split | 16399 |
| ac-compressor | conditional | conditional:engine_unattested | 3835 |
| ac-compressor | conditional | conditional:option | 37 |
| alternator | unmapped | - | 217 |
| alternator | no_records | - | 1107 |
| alternator | split | option_split | 16645 |
| alternator | conditional | conditional:engine_unattested | 3844 |
| bumper-front | unmapped | - | 217 |
| bumper-front | no_records | - | 1981 |
| bumper-front | split | option_split | 17011 |
| bumper-front | conditional | conditional:engine_unattested | 2523 |
| bumper-front | conditional | conditional:fuel | 4 |
| bumper-front | conditional | conditional:option | 35 |
| bumper-front | conditional | conditional:package | 42 |
| bumper-rear | unmapped | - | 217 |
| bumper-rear | no_records | - | 2154 |
| bumper-rear | split | option_split | 16668 |
| bumper-rear | conditional | conditional:engine_unattested | 2214 |
| bumper-rear | conditional | conditional:option | 560 |
| climate-control | unmapped | - | 217 |
| climate-control | no_records | - | 2589 |
| climate-control | split | option_split | 18971 |
| climate-control | conditional | conditional:engine_unattested | 36 |
| door-front | unmapped | - | 217 |
| door-front | no_records | - | 1999 |
| door-front | split | option_split | 9321 |
| door-front | conditional | conditional:engine_unattested | 10276 |
| door-rear | unmapped | - | 217 |
| door-rear | no_records | - | 2588 |
| door-rear | split | option_split | 10626 |
| door-rear | split | slot_missing | 301 |
| door-rear | conditional | conditional:engine_unattested | 8081 |
| fender | unmapped | - | 217 |
| fender | no_records | - | 1847 |
| fender | split | option_split | 5402 |
| fender | split | slot_missing | 27 |
| fender | conditional | conditional:body | 266 |
| fender | conditional | conditional:engine_unattested | 14054 |
| fuel-pump-module | unmapped | - | 217 |
| fuel-pump-module | no_records | - | 2277 |
| fuel-pump-module | split | option_split | 16248 |
| fuel-pump-module | conditional | conditional:engine_unattested | 3071 |
| gauge-cluster | unmapped | - | 217 |
| gauge-cluster | no_records | - | 2881 |
| gauge-cluster | split | no_candidates | 11 |
| gauge-cluster | split | option_split | 18567 |
| gauge-cluster | conditional | conditional:engine_unattested | 137 |
| grille | unmapped | - | 217 |
| grille | no_records | - | 2812 |
| grille | split | no_candidates | 25 |
| grille | split | option_split | 17616 |
| grille | conditional | conditional:engine_unattested | 1035 |
| grille | conditional | conditional:package | 108 |
| headlights | unmapped | - | 217 |
| headlights | no_records | - | 1671 |
| headlights | split | option_split | 16666 |
| headlights | split | slot_missing | 239 |
| headlights | conditional | conditional:engine_unattested | 2985 |
| headlights | conditional | conditional:option | 35 |
| hood | unmapped | - | 217 |
| hood | no_records | - | 1955 |
| hood | split | option_split | 3554 |
| hood | conditional | conditional:engine_unattested | 16087 |
| ignition-coils | unmapped | - | 217 |
| ignition-coils | no_records | - | 391 |
| ignition-coils | split | option_split | 13772 |
| ignition-coils | conditional | conditional:engine_unattested | 6136 |
| ignition-coils | conditional | conditional:package | 1297 |
| liftgate | unmapped | - | 217 |
| liftgate | no_records | - | 12725 |
| liftgate | split | option_split | 6546 |
| liftgate | conditional | conditional:engine_unattested | 2325 |
| power-steering-pump | unmapped | - | 217 |
| power-steering-pump | no_records | - | 13349 |
| power-steering-pump | split | option_split | 6234 |
| power-steering-pump | conditional | conditional:engine_unattested | 2013 |
| radiator | unmapped | - | 217 |
| radiator | no_records | - | 3518 |
| radiator | split | no_candidates | 597 |
| radiator | split | option_split | 16367 |
| radiator | conditional | conditional:engine_unattested | 1114 |
| side-mirrors | unmapped | - | 217 |
| side-mirrors | no_records | - | 1295 |
| side-mirrors | split | option_split | 19241 |
| side-mirrors | conditional | conditional:engine_unattested | 1060 |
| starter | unmapped | - | 217 |
| starter | no_records | - | 401 |
| starter | split | option_split | 19915 |
| starter | conditional | conditional:engine_unattested | 1280 |
| tail-lights | unmapped | - | 217 |
| tail-lights | no_records | - | 2410 |
| tail-lights | split | option_split | 17925 |
| tail-lights | conditional | conditional:engine_unattested | 1261 |
| throttle-body | unmapped | - | 217 |
| throttle-body | no_records | - | 2328 |
| throttle-body | split | option_split | 14982 |
| throttle-body | conditional | conditional:engine_unattested | 4286 |
| trunk-lid | unmapped | - | 217 |
| trunk-lid | no_records | - | 9370 |
| trunk-lid | split | no_candidates | 139 |
| trunk-lid | split | option_split | 4526 |
| trunk-lid | conditional | conditional:engine_unattested | 5861 |
| trunk-lid | conditional | conditional:option | 1383 |
| trunk-lid | conditional | conditional:package | 317 |
| window-regulator | unmapped | - | 217 |
| window-regulator | no_records | - | 1169 |
| window-regulator | split | packaging_incomplete | 898 |
| window-regulator | split | packaging_split | 12199 |
| window-regulator | split | packaging_unstated | 7330 |
| window-switch | unmapped | - | 217 |
| window-switch | no_records | - | 2549 |
| window-switch | split | option_split | 17094 |
| window-switch | split | position_missing | 1649 |
| window-switch | conditional | conditional:engine_unattested | 304 |

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
