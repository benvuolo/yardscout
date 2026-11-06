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
| ac-compressor | unmapped | - | 215 |
| ac-compressor | no_records | - | 1330 |
| ac-compressor | not_closed | no_list_manifest | 3684 |
| ac-compressor | not_closed | no_year_manifest | 15269 |
| ac-compressor | not_closed | unattested | 19 |
| ac-compressor | not_closed | unverified_product | 25 |
| ac-compressor | not_closed | variant_unread | 1284 |
| alternator | unmapped | - | 215 |
| alternator | no_records | - | 1112 |
| alternator | not_closed | no_list_manifest | 3657 |
| alternator | not_closed | no_year_manifest | 15539 |
| alternator | not_closed | unverified_product | 19 |
| alternator | not_closed | variant_unread | 1284 |
| bumper-front | unmapped | - | 215 |
| bumper-front | no_records | - | 1986 |
| bumper-front | not_closed | no_year_manifest | 14599 |
| bumper-front | not_closed | unread_sibling_page | 3742 |
| bumper-front | not_closed | variant_unread | 1284 |
| bumper-rear | unmapped | - | 215 |
| bumper-rear | no_records | - | 2159 |
| bumper-rear | not_closed | no_year_manifest | 14426 |
| bumper-rear | not_closed | unread_sibling_page | 3742 |
| bumper-rear | not_closed | variant_unread | 1284 |
| climate-control | unmapped | - | 215 |
| climate-control | no_records | - | 2597 |
| climate-control | not_closed | no_list_manifest | 3684 |
| climate-control | not_closed | no_year_manifest | 14002 |
| climate-control | not_closed | unread_sibling_page | 44 |
| climate-control | not_closed | variant_unread | 1284 |
| door-front | unmapped | - | 215 |
| door-front | no_records | - | 2000 |
| door-front | not_closed | no_year_manifest | 14585 |
| door-front | not_closed | unread_sibling_page | 3742 |
| door-front | not_closed | variant_unread | 1284 |
| door-rear | unmapped | - | 215 |
| door-rear | no_records | - | 2588 |
| door-rear | not_closed | no_year_manifest | 14061 |
| door-rear | not_closed | unread_sibling_page | 3678 |
| door-rear | not_closed | variant_unread | 1284 |
| fender | unmapped | - | 215 |
| fender | no_records | - | 1847 |
| fender | not_closed | no_year_manifest | 14738 |
| fender | not_closed | unread_sibling_page | 3742 |
| fender | not_closed | variant_unread | 1284 |
| fuel-pump-module | unmapped | - | 215 |
| fuel-pump-module | no_records | - | 2282 |
| fuel-pump-module | not_closed | no_list_manifest | 3674 |
| fuel-pump-module | not_closed | no_year_manifest | 14327 |
| fuel-pump-module | not_closed | unread_sibling_page | 44 |
| fuel-pump-module | not_closed | variant_unread | 1284 |
| gauge-cluster | unmapped | - | 215 |
| gauge-cluster | no_records | - | 2888 |
| gauge-cluster | not_closed | no_year_manifest | 13697 |
| gauge-cluster | not_closed | suspect_variant | 85 |
| gauge-cluster | not_closed | unattested | 557 |
| gauge-cluster | not_closed | unread_sibling_page | 3100 |
| gauge-cluster | not_closed | variant_unread | 1284 |
| grille | unmapped | - | 215 |
| grille | no_records | - | 2817 |
| grille | not_closed | no_year_manifest | 13768 |
| grille | not_closed | suspect_variant | 4 |
| grille | not_closed | unattested | 2178 |
| grille | not_closed | uncrawled_chain_member | 1560 |
| grille | not_closed | variant_unread | 1284 |
| headlights | unmapped | - | 215 |
| headlights | no_records | - | 1674 |
| headlights | not_closed | no_list_manifest | 3684 |
| headlights | not_closed | no_year_manifest | 14925 |
| headlights | not_closed | unattested | 44 |
| headlights | not_closed | variant_unread | 1284 |
| hood | unmapped | - | 215 |
| hood | no_records | - | 1955 |
| hood | not_closed | no_year_manifest | 14630 |
| hood | not_closed | unread_sibling_page | 3742 |
| hood | not_closed | variant_unread | 1284 |
| ignition-coils | unmapped | - | 215 |
| ignition-coils | no_records | - | 391 |
| ignition-coils | not_closed | no_year_manifest | 16194 |
| ignition-coils | not_closed | unattested | 10 |
| ignition-coils | not_closed | uncrawled_chain_member | 1 |
| ignition-coils | not_closed | unverified_product | 3731 |
| ignition-coils | not_closed | variant_unread | 1284 |
| liftgate | unmapped | - | 215 |
| liftgate | no_records | - | 12720 |
| liftgate | not_closed | no_year_manifest | 7669 |
| liftgate | not_closed | unattested | 967 |
| liftgate | not_closed | uncrawled_chain_member | 206 |
| liftgate | not_closed | variant_unread | 49 |
| power-steering-pump | unmapped | - | 215 |
| power-steering-pump | no_records | - | 13348 |
| power-steering-pump | not_closed | no_list_manifest | 1544 |
| power-steering-pump | not_closed | no_year_manifest | 6645 |
| power-steering-pump | not_closed | unread_sibling_page | 25 |
| power-steering-pump | not_closed | variant_unread | 49 |
| radiator | unmapped | - | 215 |
| radiator | no_records | - | 3524 |
| radiator | not_closed | no_year_manifest | 13098 |
| radiator | not_closed | unread_sibling_page | 3705 |
| radiator | not_closed | variant_unread | 1284 |
| side-mirrors | unmapped | - | 215 |
| side-mirrors | no_records | - | 1299 |
| side-mirrors | not_closed | no_list_manifest | 3612 |
| side-mirrors | not_closed | no_year_manifest | 15372 |
| side-mirrors | not_closed | unattested | 44 |
| side-mirrors | not_closed | variant_unread | 1284 |
| starter | unmapped | - | 215 |
| starter | no_records | - | 402 |
| starter | not_closed | no_list_manifest | 3663 |
| starter | not_closed | no_year_manifest | 16218 |
| starter | not_closed | unverified_product | 44 |
| starter | not_closed | variant_unread | 1284 |
| tail-lights | unmapped | - | 215 |
| tail-lights | no_records | - | 2414 |
| tail-lights | not_closed | no_list_manifest | 3684 |
| tail-lights | not_closed | no_year_manifest | 14185 |
| tail-lights | not_closed | unattested | 44 |
| tail-lights | not_closed | variant_unread | 1284 |
| throttle-body | unmapped | - | 215 |
| throttle-body | no_records | - | 2331 |
| throttle-body | not_closed | no_list_manifest | 3499 |
| throttle-body | not_closed | no_year_manifest | 14453 |
| throttle-body | not_closed | unattested | 44 |
| throttle-body | not_closed | variant_unread | 1284 |
| trunk-lid | unmapped | - | 215 |
| trunk-lid | no_records | - | 9382 |
| trunk-lid | not_closed | no_year_manifest | 8239 |
| trunk-lid | not_closed | unattested | 139 |
| trunk-lid | not_closed | unread_sibling_page | 2616 |
| trunk-lid | not_closed | variant_unread | 1235 |
| window-regulator | unmapped | - | 215 |
| window-regulator | no_records | - | 1168 |
| window-regulator | not_closed | no_list_manifest | 3689 |
| window-regulator | not_closed | no_year_manifest | 15426 |
| window-regulator | not_closed | unread_sibling_page | 44 |
| window-regulator | not_closed | variant_unread | 1284 |
| window-switch | unmapped | - | 215 |
| window-switch | no_records | - | 2555 |
| window-switch | not_closed | no_list_manifest | 3652 |
| window-switch | not_closed | no_year_manifest | 14076 |
| window-switch | not_closed | unread_sibling_page | 44 |
| window-switch | not_closed | variant_unread | 1284 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 215 |
| ac-compressor | no_records | - | 1330 |
| ac-compressor | split | option_split | 16415 |
| ac-compressor | conditional | conditional:engine_unattested | 3828 |
| ac-compressor | conditional | conditional:option | 38 |
| alternator | unmapped | - | 215 |
| alternator | no_records | - | 1112 |
| alternator | split | option_split | 16655 |
| alternator | conditional | conditional:engine_unattested | 3844 |
| bumper-front | unmapped | - | 215 |
| bumper-front | no_records | - | 1986 |
| bumper-front | split | option_split | 17022 |
| bumper-front | conditional | conditional:engine_unattested | 2521 |
| bumper-front | conditional | conditional:fuel | 4 |
| bumper-front | conditional | conditional:option | 35 |
| bumper-front | conditional | conditional:package | 43 |
| bumper-rear | unmapped | - | 215 |
| bumper-rear | no_records | - | 2159 |
| bumper-rear | split | option_split | 16681 |
| bumper-rear | conditional | conditional:engine_unattested | 2211 |
| bumper-rear | conditional | conditional:option | 560 |
| climate-control | unmapped | - | 215 |
| climate-control | no_records | - | 2597 |
| climate-control | split | option_split | 18976 |
| climate-control | conditional | conditional:engine_unattested | 38 |
| door-front | unmapped | - | 215 |
| door-front | no_records | - | 2000 |
| door-front | split | option_split | 9333 |
| door-front | conditional | conditional:engine_unattested | 10278 |
| door-rear | unmapped | - | 215 |
| door-rear | no_records | - | 2588 |
| door-rear | split | option_split | 10626 |
| door-rear | split | slot_missing | 300 |
| door-rear | conditional | conditional:engine_unattested | 8097 |
| fender | unmapped | - | 215 |
| fender | no_records | - | 1847 |
| fender | split | option_split | 5417 |
| fender | split | slot_missing | 27 |
| fender | conditional | conditional:body | 264 |
| fender | conditional | conditional:engine_unattested | 14056 |
| fuel-pump-module | unmapped | - | 215 |
| fuel-pump-module | no_records | - | 2282 |
| fuel-pump-module | split | option_split | 16256 |
| fuel-pump-module | conditional | conditional:engine_unattested | 3073 |
| gauge-cluster | unmapped | - | 215 |
| gauge-cluster | no_records | - | 2888 |
| gauge-cluster | split | no_candidates | 11 |
| gauge-cluster | split | option_split | 18575 |
| gauge-cluster | conditional | conditional:engine_unattested | 137 |
| grille | unmapped | - | 215 |
| grille | no_records | - | 2817 |
| grille | split | no_candidates | 26 |
| grille | split | option_split | 17626 |
| grille | conditional | conditional:engine_unattested | 1034 |
| grille | conditional | conditional:package | 108 |
| headlights | unmapped | - | 215 |
| headlights | no_records | - | 1674 |
| headlights | split | option_split | 16663 |
| headlights | split | slot_missing | 238 |
| headlights | conditional | conditional:engine_unattested | 3001 |
| headlights | conditional | conditional:option | 35 |
| hood | unmapped | - | 215 |
| hood | no_records | - | 1955 |
| hood | split | option_split | 3550 |
| hood | conditional | conditional:engine_unattested | 16106 |
| ignition-coils | unmapped | - | 215 |
| ignition-coils | no_records | - | 391 |
| ignition-coils | split | option_split | 13791 |
| ignition-coils | conditional | conditional:engine_unattested | 6131 |
| ignition-coils | conditional | conditional:package | 1298 |
| liftgate | unmapped | - | 215 |
| liftgate | no_records | - | 12720 |
| liftgate | split | option_split | 6551 |
| liftgate | conditional | conditional:engine_unattested | 2340 |
| power-steering-pump | unmapped | - | 215 |
| power-steering-pump | no_records | - | 13348 |
| power-steering-pump | split | option_split | 6246 |
| power-steering-pump | conditional | conditional:engine_unattested | 2017 |
| radiator | unmapped | - | 215 |
| radiator | no_records | - | 3524 |
| radiator | split | no_candidates | 598 |
| radiator | split | option_split | 16378 |
| radiator | conditional | conditional:engine_unattested | 1111 |
| side-mirrors | unmapped | - | 215 |
| side-mirrors | no_records | - | 1299 |
| side-mirrors | split | option_split | 19253 |
| side-mirrors | conditional | conditional:engine_unattested | 1059 |
| starter | unmapped | - | 215 |
| starter | no_records | - | 402 |
| starter | split | option_split | 19933 |
| starter | conditional | conditional:engine_unattested | 1276 |
| tail-lights | unmapped | - | 215 |
| tail-lights | no_records | - | 2414 |
| tail-lights | split | option_split | 17930 |
| tail-lights | conditional | conditional:engine_unattested | 1267 |
| throttle-body | unmapped | - | 215 |
| throttle-body | no_records | - | 2331 |
| throttle-body | split | option_split | 14994 |
| throttle-body | conditional | conditional:engine_unattested | 4286 |
| trunk-lid | unmapped | - | 215 |
| trunk-lid | no_records | - | 9382 |
| trunk-lid | split | no_candidates | 139 |
| trunk-lid | split | option_split | 4521 |
| trunk-lid | conditional | conditional:engine_unattested | 5867 |
| trunk-lid | conditional | conditional:option | 1382 |
| trunk-lid | conditional | conditional:package | 320 |
| window-regulator | unmapped | - | 215 |
| window-regulator | no_records | - | 1168 |
| window-regulator | split | packaging_incomplete | 897 |
| window-regulator | split | packaging_split | 12203 |
| window-regulator | split | packaging_unstated | 7343 |
| window-switch | unmapped | - | 215 |
| window-switch | no_records | - | 2555 |
| window-switch | split | option_split | 17102 |
| window-switch | split | position_missing | 1650 |
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
