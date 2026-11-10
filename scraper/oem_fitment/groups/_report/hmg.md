# OEM curation report: hmg

Raw: `dca9cd845f26` @ `dca9cd845f26`; as of 2026-11-09T23:14:56Z.

- records 7906, classes 7673, list rows 37438, year manifests 307, cells 8810
- Verified groups 0, engine vg groups 0, Likely groups 52
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.hyundaipartsdeal.com, www.kiapartsnow.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.hyundaipartsdeal.com: only 0% of its 4762 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)
- www.kiapartsnow.com: only 0% of its 4468 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 210 |
| ac-compressor | no_records | - | 1319 |
| ac-compressor | not_closed | no_list_manifest | 7935 |
| ac-compressor | not_closed | no_year_manifest | 11051 |
| ac-compressor | not_closed | unattested | 19 |
| ac-compressor | not_closed | unverified_product | 25 |
| ac-compressor | not_closed | variant_unread | 1435 |
| alternator | unmapped | - | 210 |
| alternator | no_records | - | 1116 |
| alternator | not_closed | no_list_manifest | 7931 |
| alternator | not_closed | no_year_manifest | 11283 |
| alternator | not_closed | unverified_product | 19 |
| alternator | not_closed | variant_unread | 1435 |
| bumper-front | unmapped | - | 210 |
| bumper-front | no_records | - | 1987 |
| bumper-front | not_closed | no_list_manifest | 4153 |
| bumper-front | not_closed | no_year_manifest | 10456 |
| bumper-front | not_closed | unread_sibling_page | 3753 |
| bumper-front | not_closed | variant_unread | 1435 |
| bumper-rear | unmapped | - | 210 |
| bumper-rear | no_records | - | 2162 |
| bumper-rear | not_closed | no_list_manifest | 4014 |
| bumper-rear | not_closed | no_year_manifest | 10420 |
| bumper-rear | not_closed | unread_sibling_page | 3753 |
| bumper-rear | not_closed | variant_unread | 1435 |
| climate-control | unmapped | - | 210 |
| climate-control | no_records | - | 2598 |
| climate-control | not_closed | no_list_manifest | 7830 |
| climate-control | not_closed | no_year_manifest | 9877 |
| climate-control | not_closed | unread_sibling_page | 44 |
| climate-control | not_closed | variant_unread | 1435 |
| door-front | unmapped | - | 210 |
| door-front | no_records | - | 2005 |
| door-front | not_closed | no_list_manifest | 3776 |
| door-front | not_closed | no_year_manifest | 10815 |
| door-front | not_closed | unread_sibling_page | 3753 |
| door-front | not_closed | variant_unread | 1435 |
| door-rear | unmapped | - | 210 |
| door-rear | no_records | - | 2594 |
| door-rear | not_closed | no_list_manifest | 3672 |
| door-rear | not_closed | no_year_manifest | 10393 |
| door-rear | not_closed | unread_sibling_page | 3690 |
| door-rear | not_closed | variant_unread | 1435 |
| fender | unmapped | - | 210 |
| fender | no_records | - | 1855 |
| fender | not_closed | no_list_manifest | 3776 |
| fender | not_closed | no_year_manifest | 10965 |
| fender | not_closed | unread_sibling_page | 3753 |
| fender | not_closed | variant_unread | 1435 |
| fuel-pump-module | unmapped | - | 210 |
| fuel-pump-module | no_records | - | 2287 |
| fuel-pump-module | not_closed | no_list_manifest | 7518 |
| fuel-pump-module | not_closed | no_year_manifest | 10535 |
| fuel-pump-module | not_closed | unread_sibling_page | 44 |
| fuel-pump-module | not_closed | variant_unread | 1400 |
| gauge-cluster | unmapped | - | 210 |
| gauge-cluster | no_records | - | 2897 |
| gauge-cluster | not_closed | no_list_manifest | 3960 |
| gauge-cluster | not_closed | no_year_manifest | 9739 |
| gauge-cluster | not_closed | suspect_variant | 84 |
| gauge-cluster | not_closed | unattested | 558 |
| gauge-cluster | not_closed | unread_sibling_page | 3111 |
| gauge-cluster | not_closed | variant_unread | 1435 |
| grille | unmapped | - | 210 |
| grille | no_records | - | 2820 |
| grille | not_closed | no_list_manifest | 4153 |
| grille | not_closed | no_year_manifest | 9623 |
| grille | not_closed | suspect_variant | 4 |
| grille | not_closed | unattested | 2184 |
| grille | not_closed | uncrawled_chain_member | 1565 |
| grille | not_closed | variant_unread | 1435 |
| headlights | unmapped | - | 210 |
| headlights | no_records | - | 1677 |
| headlights | not_closed | no_list_manifest | 7830 |
| headlights | not_closed | no_year_manifest | 10798 |
| headlights | not_closed | unattested | 44 |
| headlights | not_closed | variant_unread | 1435 |
| hood | unmapped | - | 210 |
| hood | no_records | - | 1962 |
| hood | not_closed | no_list_manifest | 3722 |
| hood | not_closed | no_year_manifest | 10912 |
| hood | not_closed | unread_sibling_page | 3753 |
| hood | not_closed | variant_unread | 1435 |
| ignition-coils | unmapped | - | 210 |
| ignition-coils | no_records | - | 389 |
| ignition-coils | not_closed | no_list_manifest | 4175 |
| ignition-coils | not_closed | no_year_manifest | 12032 |
| ignition-coils | not_closed | unattested | 10 |
| ignition-coils | not_closed | unverified_product | 3743 |
| ignition-coils | not_closed | variant_unread | 1435 |
| knuckle | unmapped | - | 210 |
| knuckle | no_records | - | 4377 |
| knuckle | not_closed | no_list_manifest | 156 |
| knuckle | not_closed | no_year_manifest | 9018 |
| knuckle | not_closed | suspect_variant | 4 |
| knuckle | not_closed | unattested | 2835 |
| knuckle | not_closed | uncrawled_chain_member | 846 |
| knuckle | not_closed | unverified_product | 3113 |
| knuckle | not_closed | variant_unread | 1435 |
| liftgate | unmapped | - | 210 |
| liftgate | no_records | - | 12826 |
| liftgate | not_closed | no_list_manifest | 2377 |
| liftgate | not_closed | no_year_manifest | 5226 |
| liftgate | not_closed | unattested | 975 |
| liftgate | not_closed | uncrawled_chain_member | 202 |
| liftgate | not_closed | variant_unread | 178 |
| power-steering-pump | unmapped | - | 210 |
| power-steering-pump | no_records | - | 13517 |
| power-steering-pump | not_closed | no_list_manifest | 3227 |
| power-steering-pump | not_closed | no_year_manifest | 4837 |
| power-steering-pump | not_closed | unread_sibling_page | 25 |
| power-steering-pump | not_closed | variant_unread | 178 |
| radiator | unmapped | - | 210 |
| radiator | no_records | - | 3525 |
| radiator | not_closed | no_list_manifest | 3596 |
| radiator | not_closed | no_year_manifest | 9547 |
| radiator | not_closed | unread_sibling_page | 3716 |
| radiator | not_closed | variant_unread | 1400 |
| side-mirrors | unmapped | - | 210 |
| side-mirrors | no_records | - | 1302 |
| side-mirrors | not_closed | no_list_manifest | 7798 |
| side-mirrors | not_closed | no_year_manifest | 11205 |
| side-mirrors | not_closed | unattested | 44 |
| side-mirrors | not_closed | variant_unread | 1435 |
| starter | unmapped | - | 210 |
| starter | no_records | - | 403 |
| starter | not_closed | no_list_manifest | 7970 |
| starter | not_closed | no_year_manifest | 11932 |
| starter | not_closed | unverified_product | 44 |
| starter | not_closed | variant_unread | 1435 |
| strut | unmapped | - | 210 |
| strut | no_records | - | 1833 |
| strut | not_closed | no_list_manifest | 68 |
| strut | not_closed | no_year_manifest | 10753 |
| strut | not_closed | suspect_variant | 294 |
| strut | not_closed | unattested | 3181 |
| strut | not_closed | uncrawled_chain_member | 3729 |
| strut | not_closed | unverified_product | 491 |
| strut | not_closed | variant_unread | 1435 |
| tail-lights | unmapped | - | 210 |
| tail-lights | no_records | - | 2421 |
| tail-lights | not_closed | no_list_manifest | 7525 |
| tail-lights | not_closed | no_year_manifest | 10359 |
| tail-lights | not_closed | unattested | 44 |
| tail-lights | not_closed | variant_unread | 1435 |
| throttle-body | unmapped | - | 210 |
| throttle-body | no_records | - | 2335 |
| throttle-body | not_closed | no_list_manifest | 7348 |
| throttle-body | not_closed | no_year_manifest | 10622 |
| throttle-body | not_closed | unattested | 44 |
| throttle-body | not_closed | variant_unread | 1435 |
| trunk-lid | unmapped | - | 210 |
| trunk-lid | no_records | - | 9414 |
| trunk-lid | not_closed | no_list_manifest | 1950 |
| trunk-lid | not_closed | no_year_manifest | 6352 |
| trunk-lid | not_closed | unattested | 141 |
| trunk-lid | not_closed | unread_sibling_page | 2635 |
| trunk-lid | not_closed | variant_unread | 1292 |
| wheels | unmapped | - | 210 |
| wheels | no_records | - | 815 |
| wheels | not_closed | no_list_manifest | 55 |
| wheels | not_closed | no_year_manifest | 11611 |
| wheels | not_closed | suspect_variant | 163 |
| wheels | not_closed | unattested | 5975 |
| wheels | not_closed | uncrawled_chain_member | 1191 |
| wheels | not_closed | unverified_product | 539 |
| wheels | not_closed | variant_unread | 1435 |
| window-regulator | unmapped | - | 210 |
| window-regulator | no_records | - | 1169 |
| window-regulator | not_closed | no_list_manifest | 7554 |
| window-regulator | not_closed | no_year_manifest | 11582 |
| window-regulator | not_closed | unread_sibling_page | 44 |
| window-regulator | not_closed | variant_unread | 1435 |
| window-switch | unmapped | - | 210 |
| window-switch | no_records | - | 2557 |
| window-switch | not_closed | no_list_manifest | 7482 |
| window-switch | not_closed | no_year_manifest | 10266 |
| window-switch | not_closed | unread_sibling_page | 44 |
| window-switch | not_closed | variant_unread | 1435 |
| wiper-motor | unmapped | - | 210 |
| wiper-motor | no_records | - | 931 |
| wiper-motor | not_closed | no_list_manifest | 227 |
| wiper-motor | not_closed | no_year_manifest | 11370 |
| wiper-motor | not_closed | unattested | 5479 |
| wiper-motor | not_closed | uncrawled_chain_member | 448 |
| wiper-motor | not_closed | unverified_product | 1894 |
| wiper-motor | not_closed | variant_unread | 1435 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 210 |
| ac-compressor | no_records | - | 1319 |
| ac-compressor | split | option_split | 16558 |
| ac-compressor | conditional | conditional:engine_unattested | 3869 |
| ac-compressor | conditional | conditional:option | 38 |
| alternator | unmapped | - | 210 |
| alternator | no_records | - | 1116 |
| alternator | split | option_split | 16814 |
| alternator | conditional | conditional:engine_unattested | 3854 |
| bumper-front | unmapped | - | 210 |
| bumper-front | no_records | - | 1987 |
| bumper-front | split | option_split | 17183 |
| bumper-front | conditional | conditional:engine_unattested | 2531 |
| bumper-front | conditional | conditional:fuel | 4 |
| bumper-front | conditional | conditional:option | 36 |
| bumper-front | conditional | conditional:package | 43 |
| bumper-rear | unmapped | - | 210 |
| bumper-rear | no_records | - | 2162 |
| bumper-rear | split | option_split | 16831 |
| bumper-rear | conditional | conditional:engine_unattested | 2221 |
| bumper-rear | conditional | conditional:option | 570 |
| climate-control | unmapped | - | 210 |
| climate-control | no_records | - | 2598 |
| climate-control | split | option_split | 19152 |
| climate-control | conditional | conditional:engine_unattested | 34 |
| door-front | unmapped | - | 210 |
| door-front | no_records | - | 2005 |
| door-front | split | option_split | 9437 |
| door-front | conditional | conditional:engine_unattested | 10342 |
| door-rear | unmapped | - | 210 |
| door-rear | no_records | - | 2594 |
| door-rear | split | option_split | 10740 |
| door-rear | split | slot_missing | 303 |
| door-rear | conditional | conditional:engine_unattested | 8147 |
| fender | unmapped | - | 210 |
| fender | no_records | - | 1855 |
| fender | split | option_split | 5449 |
| fender | split | slot_missing | 29 |
| fender | conditional | conditional:body | 272 |
| fender | conditional | conditional:engine_unattested | 14179 |
| fuel-pump-module | unmapped | - | 210 |
| fuel-pump-module | no_records | - | 2287 |
| fuel-pump-module | split | option_split | 16427 |
| fuel-pump-module | conditional | conditional:engine_unattested | 3070 |
| gauge-cluster | unmapped | - | 210 |
| gauge-cluster | no_records | - | 2897 |
| gauge-cluster | split | no_candidates | 10 |
| gauge-cluster | split | option_split | 18741 |
| gauge-cluster | conditional | conditional:engine_unattested | 136 |
| grille | unmapped | - | 210 |
| grille | no_records | - | 2820 |
| grille | split | no_candidates | 26 |
| grille | split | option_split | 17798 |
| grille | conditional | conditional:engine_unattested | 1031 |
| grille | conditional | conditional:package | 109 |
| headlights | unmapped | - | 210 |
| headlights | no_records | - | 1677 |
| headlights | split | option_split | 16830 |
| headlights | split | slot_missing | 239 |
| headlights | conditional | conditional:engine_unattested | 3002 |
| headlights | conditional | conditional:option | 36 |
| hood | unmapped | - | 210 |
| hood | no_records | - | 1962 |
| hood | split | option_split | 3583 |
| hood | conditional | conditional:engine_unattested | 16239 |
| ignition-coils | unmapped | - | 210 |
| ignition-coils | no_records | - | 389 |
| ignition-coils | split | option_split | 13890 |
| ignition-coils | conditional | conditional:engine_unattested | 6197 |
| ignition-coils | conditional | conditional:package | 1308 |
| knuckle | unmapped | - | 210 |
| knuckle | no_records | - | 4377 |
| knuckle | split | no_candidates | 701 |
| knuckle | split | option_split | 16706 |
| liftgate | unmapped | - | 210 |
| liftgate | no_records | - | 12826 |
| liftgate | split | option_split | 6600 |
| liftgate | conditional | conditional:engine_unattested | 2358 |
| power-steering-pump | unmapped | - | 210 |
| power-steering-pump | no_records | - | 13517 |
| power-steering-pump | split | option_split | 6248 |
| power-steering-pump | conditional | conditional:engine_unattested | 2019 |
| radiator | unmapped | - | 210 |
| radiator | no_records | - | 3525 |
| radiator | split | no_candidates | 602 |
| radiator | split | option_split | 16551 |
| radiator | conditional | conditional:engine_unattested | 1106 |
| side-mirrors | unmapped | - | 210 |
| side-mirrors | no_records | - | 1302 |
| side-mirrors | split | option_split | 19416 |
| side-mirrors | conditional | conditional:engine_unattested | 1066 |
| starter | unmapped | - | 210 |
| starter | no_records | - | 403 |
| starter | split | option_split | 20088 |
| starter | conditional | conditional:engine_unattested | 1293 |
| strut | unmapped | - | 210 |
| strut | no_records | - | 1833 |
| strut | split | option_split | 19190 |
| strut | conditional | conditional:engine_unattested | 761 |
| tail-lights | unmapped | - | 210 |
| tail-lights | no_records | - | 2421 |
| tail-lights | split | option_split | 18108 |
| tail-lights | conditional | conditional:engine_unattested | 1255 |
| throttle-body | unmapped | - | 210 |
| throttle-body | no_records | - | 2335 |
| throttle-body | split | option_split | 15131 |
| throttle-body | conditional | conditional:engine_unattested | 4318 |
| trunk-lid | unmapped | - | 210 |
| trunk-lid | no_records | - | 9414 |
| trunk-lid | split | no_candidates | 141 |
| trunk-lid | split | option_split | 4560 |
| trunk-lid | conditional | conditional:engine_unattested | 5941 |
| trunk-lid | conditional | conditional:option | 1405 |
| trunk-lid | conditional | conditional:package | 323 |
| wheels | unmapped | - | 210 |
| wheels | no_records | - | 815 |
| wheels | split | option_split | 20280 |
| wheels | conditional | conditional:engine_unattested | 664 |
| wheels | conditional | conditional:package | 25 |
| window-regulator | unmapped | - | 210 |
| window-regulator | no_records | - | 1169 |
| window-regulator | split | packaging_incomplete | 899 |
| window-regulator | split | packaging_split | 12350 |
| window-regulator | split | packaging_unstated | 7366 |
| window-switch | unmapped | - | 210 |
| window-switch | no_records | - | 2557 |
| window-switch | split | option_split | 17270 |
| window-switch | split | position_missing | 1652 |
| window-switch | conditional | conditional:engine_unattested | 305 |
| wiper-motor | unmapped | - | 210 |
| wiper-motor | no_records | - | 931 |
| wiper-motor | split | no_candidates | 239 |
| wiper-motor | split | option_split | 8483 |
| wiper-motor | conditional | conditional:engine_unattested | 12131 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 124
- disputed_class: 233
- rule_drift: 10
- universal_part_suspect: 3
- wheel_body_option: 7
- wheel_compact_spare: 3
- wheel_production_date: 3

## Unknown note clauses (top 30)

- `Package Quantity: 1`: 899
- `SPEEDOMETER TYPE - MPH(KMPH)`: 571
- `Require Quantity: 4`: 566
- `TIRE PRESSURE MONITORG SYS - HIGH LINE`: 449
- `ESC (ELECTRONIC STABILITY CONTROL)`: 440
- `VEHICLE PACKAGE - SPORTS`: 313
- `ABS (ANTI LOCK BRK SYS)`: 303
- `MODEL YEAR PACKAGE - 16MY`: 266
- `Require Quantity: 2`: 265
- `TIRE PRESSURE MONITORG SYS - LOW LINE`: 246
- `AUTO CRUISE CONTROL - CONVENTIONAL`: 233
- `PARKG BRK CONTROL-EPB`: 218
- `AUTO CRUISE CONTROL - SMART`: 210
- `FOB KEY`: 204
- `SMART KEY-FR DR`: 204
- `P/WINDOW DR'S - AUTO UP/DOWN & SAFETY`: 196
- `BLIND SPOT DETECTION SYSTEM - RADAR TYPE`: 184
- `TEMPORARY - STEEL WHEEL & TIRE (MINI)`: 184
- `MODEL YEAR PACKAGE - 14MY`: 180
- `SIDE REPEATER LAMP (O/S MRR)`: 174
- `RR PARK'G ASSIST SYSTEM(RPAS)`: 173
- `TYPE - SEPARATED TYPE`: 168
- `CLUSTER TYPE - SUPER VISION 4.2" TFT LCD INFO`: 162
- `DRL - DEDICATED LED TYPE`: 159
- `AUTONOMOUS EMERGENCY BRAKING - PEDESTRIAN`: 157
- `Fit Note: HIGH GRADE`: 157
- `TUN'G MODE - SPORTY SUSPENSION`: 155
- `MDPS-BLAC-COLUMN`: 154
- `I.M.S`: 151
- `AUTONOMOUS EMERGENCY BRAKING - URBAN`: 146

## Unmapped catalog models

- Hyundai Elantra N: feed 'Elantra N' 0 cars
- Hyundai Genesis G70: feed 'Genesis G70' 0 cars
- Hyundai Genesis G80: feed 'Genesis G80' 0 cars
- Hyundai Genesis G90: feed 'Genesis G90' 0 cars
- Hyundai Kona N: feed 'Kona N' 0 cars
- Hyundai Santa Cruz: feed 'Santa Cruz' 0 cars
- Kia Carnival: feed 'Carnival' 0 cars
- Kia EV6: feed 'EV6' 0 cars
- Kia EV9: feed 'EV9' 0 cars
- Kia Niro EV: feed 'Niro EV' 0 cars
- Kia Spectra SX: feed 'Spectra SX' 0 cars
- Kia Spectra5 SX: feed 'Spectra5 SX' 0 cars
