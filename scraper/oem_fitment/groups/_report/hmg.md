# OEM curation report: hmg

Raw: `3b4677ae1df7` @ `3b4677ae1df7`; as of 2026-11-09T22:33:32Z.

- records 7681, classes 7470, list rows 30960, year manifests 260, cells 8620
- Verified groups 0, engine vg groups 0, Likely groups 6
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.hyundaipartsdeal.com, www.kiapartsnow.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.hyundaipartsdeal.com: only 0% of its 4544 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)
- www.kiapartsnow.com: only 0% of its 4426 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 211 |
| ac-compressor | no_records | - | 1316 |
| ac-compressor | not_closed | no_list_manifest | 7867 |
| ac-compressor | not_closed | no_year_manifest | 11089 |
| ac-compressor | not_closed | unattested | 19 |
| ac-compressor | not_closed | unverified_product | 25 |
| ac-compressor | not_closed | variant_unread | 1429 |
| alternator | unmapped | - | 211 |
| alternator | no_records | - | 1117 |
| alternator | not_closed | no_list_manifest | 7863 |
| alternator | not_closed | no_year_manifest | 11317 |
| alternator | not_closed | unverified_product | 19 |
| alternator | not_closed | variant_unread | 1429 |
| bumper-front | unmapped | - | 211 |
| bumper-front | no_records | - | 1982 |
| bumper-front | not_closed | no_list_manifest | 4092 |
| bumper-front | not_closed | no_year_manifest | 10495 |
| bumper-front | not_closed | unread_sibling_page | 3747 |
| bumper-front | not_closed | variant_unread | 1429 |
| bumper-rear | unmapped | - | 211 |
| bumper-rear | no_records | - | 2158 |
| bumper-rear | not_closed | no_list_manifest | 3952 |
| bumper-rear | not_closed | no_year_manifest | 10459 |
| bumper-rear | not_closed | unread_sibling_page | 3747 |
| bumper-rear | not_closed | variant_unread | 1429 |
| climate-control | unmapped | - | 211 |
| climate-control | no_records | - | 2596 |
| climate-control | not_closed | no_list_manifest | 7762 |
| climate-control | not_closed | no_year_manifest | 9914 |
| climate-control | not_closed | unread_sibling_page | 44 |
| climate-control | not_closed | variant_unread | 1429 |
| door-front | unmapped | - | 211 |
| door-front | no_records | - | 2003 |
| door-front | not_closed | no_list_manifest | 3713 |
| door-front | not_closed | no_year_manifest | 10853 |
| door-front | not_closed | unread_sibling_page | 3747 |
| door-front | not_closed | variant_unread | 1429 |
| door-rear | unmapped | - | 211 |
| door-rear | no_records | - | 2592 |
| door-rear | not_closed | no_list_manifest | 3609 |
| door-rear | not_closed | no_year_manifest | 10431 |
| door-rear | not_closed | unread_sibling_page | 3684 |
| door-rear | not_closed | variant_unread | 1429 |
| fender | unmapped | - | 211 |
| fender | no_records | - | 1853 |
| fender | not_closed | no_list_manifest | 3713 |
| fender | not_closed | no_year_manifest | 11003 |
| fender | not_closed | unread_sibling_page | 3747 |
| fender | not_closed | variant_unread | 1429 |
| fuel-pump-module | unmapped | - | 211 |
| fuel-pump-module | no_records | - | 2288 |
| fuel-pump-module | not_closed | no_list_manifest | 7449 |
| fuel-pump-module | not_closed | no_year_manifest | 10569 |
| fuel-pump-module | not_closed | unread_sibling_page | 44 |
| fuel-pump-module | not_closed | variant_unread | 1395 |
| gauge-cluster | unmapped | - | 211 |
| gauge-cluster | no_records | - | 2895 |
| gauge-cluster | not_closed | no_list_manifest | 3898 |
| gauge-cluster | not_closed | no_year_manifest | 9776 |
| gauge-cluster | not_closed | suspect_variant | 84 |
| gauge-cluster | not_closed | unattested | 559 |
| gauge-cluster | not_closed | unread_sibling_page | 3104 |
| gauge-cluster | not_closed | variant_unread | 1429 |
| grille | unmapped | - | 211 |
| grille | no_records | - | 2817 |
| grille | not_closed | no_list_manifest | 4092 |
| grille | not_closed | no_year_manifest | 9660 |
| grille | not_closed | suspect_variant | 4 |
| grille | not_closed | unattested | 2181 |
| grille | not_closed | uncrawled_chain_member | 1562 |
| grille | not_closed | variant_unread | 1429 |
| headlights | unmapped | - | 211 |
| headlights | no_records | - | 1673 |
| headlights | not_closed | no_list_manifest | 7762 |
| headlights | not_closed | no_year_manifest | 10837 |
| headlights | not_closed | unattested | 44 |
| headlights | not_closed | variant_unread | 1429 |
| hood | unmapped | - | 211 |
| hood | no_records | - | 1961 |
| hood | not_closed | no_list_manifest | 3659 |
| hood | not_closed | no_year_manifest | 10949 |
| hood | not_closed | unread_sibling_page | 3747 |
| hood | not_closed | variant_unread | 1429 |
| ignition-coils | unmapped | - | 211 |
| ignition-coils | no_records | - | 390 |
| ignition-coils | not_closed | no_list_manifest | 4113 |
| ignition-coils | not_closed | no_year_manifest | 12066 |
| ignition-coils | not_closed | unattested | 10 |
| ignition-coils | not_closed | unverified_product | 3737 |
| ignition-coils | not_closed | variant_unread | 1429 |
| knuckle | unmapped | - | 211 |
| knuckle | no_records | - | 5153 |
| knuckle | not_closed | no_list_manifest | 538 |
| knuckle | not_closed | no_year_manifest | 8677 |
| knuckle | not_closed | suspect_variant | 4 |
| knuckle | not_closed | unattested | 2203 |
| knuckle | not_closed | uncrawled_chain_member | 1060 |
| knuckle | not_closed | unverified_product | 2681 |
| knuckle | not_closed | variant_unread | 1429 |
| liftgate | unmapped | - | 211 |
| liftgate | no_records | - | 12801 |
| liftgate | not_closed | no_list_manifest | 2346 |
| liftgate | not_closed | no_year_manifest | 5248 |
| liftgate | not_closed | unattested | 972 |
| liftgate | not_closed | uncrawled_chain_member | 201 |
| liftgate | not_closed | variant_unread | 177 |
| power-steering-pump | unmapped | - | 211 |
| power-steering-pump | no_records | - | 13494 |
| power-steering-pump | not_closed | no_list_manifest | 3192 |
| power-steering-pump | not_closed | no_year_manifest | 4857 |
| power-steering-pump | not_closed | unread_sibling_page | 25 |
| power-steering-pump | not_closed | variant_unread | 177 |
| radiator | unmapped | - | 211 |
| radiator | no_records | - | 3515 |
| radiator | not_closed | no_list_manifest | 3536 |
| radiator | not_closed | no_year_manifest | 9589 |
| radiator | not_closed | unread_sibling_page | 3710 |
| radiator | not_closed | variant_unread | 1395 |
| side-mirrors | unmapped | - | 211 |
| side-mirrors | no_records | - | 1301 |
| side-mirrors | not_closed | no_list_manifest | 7730 |
| side-mirrors | not_closed | no_year_manifest | 11241 |
| side-mirrors | not_closed | unattested | 44 |
| side-mirrors | not_closed | variant_unread | 1429 |
| starter | unmapped | - | 211 |
| starter | no_records | - | 403 |
| starter | not_closed | no_list_manifest | 7903 |
| starter | not_closed | no_year_manifest | 11966 |
| starter | not_closed | unverified_product | 44 |
| starter | not_closed | variant_unread | 1429 |
| strut | unmapped | - | 211 |
| strut | no_records | - | 3006 |
| strut | not_closed | no_list_manifest | 472 |
| strut | not_closed | no_year_manifest | 10062 |
| strut | not_closed | suspect_variant | 256 |
| strut | not_closed | unattested | 2830 |
| strut | not_closed | uncrawled_chain_member | 3527 |
| strut | not_closed | unverified_product | 163 |
| strut | not_closed | variant_unread | 1429 |
| tail-lights | unmapped | - | 211 |
| tail-lights | no_records | - | 2415 |
| tail-lights | not_closed | no_list_manifest | 7458 |
| tail-lights | not_closed | no_year_manifest | 10399 |
| tail-lights | not_closed | unattested | 44 |
| tail-lights | not_closed | variant_unread | 1429 |
| throttle-body | unmapped | - | 211 |
| throttle-body | no_records | - | 2334 |
| throttle-body | not_closed | no_list_manifest | 7305 |
| throttle-body | not_closed | no_year_manifest | 10633 |
| throttle-body | not_closed | unattested | 44 |
| throttle-body | not_closed | variant_unread | 1429 |
| trunk-lid | unmapped | - | 211 |
| trunk-lid | no_records | - | 9405 |
| trunk-lid | not_closed | no_list_manifest | 1918 |
| trunk-lid | not_closed | no_year_manifest | 6363 |
| trunk-lid | not_closed | unattested | 141 |
| trunk-lid | not_closed | unread_sibling_page | 2632 |
| trunk-lid | not_closed | variant_unread | 1286 |
| wheels | unmapped | - | 211 |
| wheels | no_records | - | 815 |
| wheels | not_closed | no_year_manifest | 11646 |
| wheels | not_closed | suspect_variant | 163 |
| wheels | not_closed | unattested | 5967 |
| wheels | not_closed | uncrawled_chain_member | 1188 |
| wheels | not_closed | unverified_product | 537 |
| wheels | not_closed | variant_unread | 1429 |
| window-regulator | unmapped | - | 211 |
| window-regulator | no_records | - | 1169 |
| window-regulator | not_closed | no_list_manifest | 7486 |
| window-regulator | not_closed | no_year_manifest | 11617 |
| window-regulator | not_closed | unread_sibling_page | 44 |
| window-regulator | not_closed | variant_unread | 1429 |
| window-switch | unmapped | - | 211 |
| window-switch | no_records | - | 2554 |
| window-switch | not_closed | no_list_manifest | 7413 |
| window-switch | not_closed | no_year_manifest | 10305 |
| window-switch | not_closed | unread_sibling_page | 44 |
| window-switch | not_closed | variant_unread | 1429 |
| wiper-motor | unmapped | - | 211 |
| wiper-motor | no_records | - | 2105 |
| wiper-motor | not_closed | no_list_manifest | 606 |
| wiper-motor | not_closed | no_year_manifest | 10757 |
| wiper-motor | not_closed | unattested | 4585 |
| wiper-motor | not_closed | uncrawled_chain_member | 421 |
| wiper-motor | not_closed | unverified_product | 1842 |
| wiper-motor | not_closed | variant_unread | 1429 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 211 |
| ac-compressor | no_records | - | 1316 |
| ac-compressor | split | option_split | 16532 |
| ac-compressor | conditional | conditional:engine_unattested | 3859 |
| ac-compressor | conditional | conditional:option | 38 |
| alternator | unmapped | - | 211 |
| alternator | no_records | - | 1117 |
| alternator | split | option_split | 16782 |
| alternator | conditional | conditional:engine_unattested | 3846 |
| bumper-front | unmapped | - | 211 |
| bumper-front | no_records | - | 1982 |
| bumper-front | split | option_split | 17153 |
| bumper-front | conditional | conditional:engine_unattested | 2527 |
| bumper-front | conditional | conditional:fuel | 4 |
| bumper-front | conditional | conditional:option | 36 |
| bumper-front | conditional | conditional:package | 43 |
| bumper-rear | unmapped | - | 211 |
| bumper-rear | no_records | - | 2158 |
| bumper-rear | split | option_split | 16803 |
| bumper-rear | conditional | conditional:engine_unattested | 2218 |
| bumper-rear | conditional | conditional:option | 566 |
| climate-control | unmapped | - | 211 |
| climate-control | no_records | - | 2596 |
| climate-control | split | option_split | 19114 |
| climate-control | conditional | conditional:engine_unattested | 35 |
| door-front | unmapped | - | 211 |
| door-front | no_records | - | 2003 |
| door-front | split | option_split | 9419 |
| door-front | conditional | conditional:engine_unattested | 10323 |
| door-rear | unmapped | - | 211 |
| door-rear | no_records | - | 2592 |
| door-rear | split | option_split | 10715 |
| door-rear | split | slot_missing | 304 |
| door-rear | conditional | conditional:engine_unattested | 8134 |
| fender | unmapped | - | 211 |
| fender | no_records | - | 1853 |
| fender | split | option_split | 5443 |
| fender | split | slot_missing | 28 |
| fender | conditional | conditional:body | 271 |
| fender | conditional | conditional:engine_unattested | 14150 |
| fuel-pump-module | unmapped | - | 211 |
| fuel-pump-module | no_records | - | 2288 |
| fuel-pump-module | split | option_split | 16391 |
| fuel-pump-module | conditional | conditional:engine_unattested | 3066 |
| gauge-cluster | unmapped | - | 211 |
| gauge-cluster | no_records | - | 2895 |
| gauge-cluster | split | no_candidates | 10 |
| gauge-cluster | split | option_split | 18704 |
| gauge-cluster | conditional | conditional:engine_unattested | 136 |
| grille | unmapped | - | 211 |
| grille | no_records | - | 2817 |
| grille | split | no_candidates | 26 |
| grille | split | option_split | 17762 |
| grille | conditional | conditional:engine_unattested | 1031 |
| grille | conditional | conditional:package | 109 |
| headlights | unmapped | - | 211 |
| headlights | no_records | - | 1673 |
| headlights | split | option_split | 16803 |
| headlights | split | slot_missing | 239 |
| headlights | conditional | conditional:engine_unattested | 2994 |
| headlights | conditional | conditional:option | 36 |
| hood | unmapped | - | 211 |
| hood | no_records | - | 1961 |
| hood | split | option_split | 3578 |
| hood | conditional | conditional:engine_unattested | 16206 |
| ignition-coils | unmapped | - | 211 |
| ignition-coils | no_records | - | 390 |
| ignition-coils | split | option_split | 13866 |
| ignition-coils | conditional | conditional:engine_unattested | 6186 |
| ignition-coils | conditional | conditional:package | 1303 |
| knuckle | unmapped | - | 211 |
| knuckle | no_records | - | 5153 |
| knuckle | split | no_candidates | 525 |
| knuckle | split | option_split | 16067 |
| liftgate | unmapped | - | 211 |
| liftgate | no_records | - | 12801 |
| liftgate | split | option_split | 6583 |
| liftgate | conditional | conditional:engine_unattested | 2361 |
| power-steering-pump | unmapped | - | 211 |
| power-steering-pump | no_records | - | 13494 |
| power-steering-pump | split | option_split | 6240 |
| power-steering-pump | conditional | conditional:engine_unattested | 2011 |
| radiator | unmapped | - | 211 |
| radiator | no_records | - | 3515 |
| radiator | split | no_candidates | 599 |
| radiator | split | option_split | 16527 |
| radiator | conditional | conditional:engine_unattested | 1104 |
| side-mirrors | unmapped | - | 211 |
| side-mirrors | no_records | - | 1301 |
| side-mirrors | split | option_split | 19380 |
| side-mirrors | conditional | conditional:engine_unattested | 1064 |
| starter | unmapped | - | 211 |
| starter | no_records | - | 403 |
| starter | split | option_split | 20047 |
| starter | conditional | conditional:engine_unattested | 1295 |
| strut | unmapped | - | 211 |
| strut | no_records | - | 3006 |
| strut | split | option_split | 17918 |
| strut | conditional | conditional:engine_unattested | 821 |
| tail-lights | unmapped | - | 211 |
| tail-lights | no_records | - | 2415 |
| tail-lights | split | option_split | 18075 |
| tail-lights | conditional | conditional:engine_unattested | 1255 |
| throttle-body | unmapped | - | 211 |
| throttle-body | no_records | - | 2334 |
| throttle-body | split | option_split | 15099 |
| throttle-body | conditional | conditional:engine_unattested | 4312 |
| trunk-lid | unmapped | - | 211 |
| trunk-lid | no_records | - | 9405 |
| trunk-lid | split | no_candidates | 141 |
| trunk-lid | split | option_split | 4544 |
| trunk-lid | conditional | conditional:engine_unattested | 5931 |
| trunk-lid | conditional | conditional:option | 1401 |
| trunk-lid | conditional | conditional:package | 323 |
| wheels | unmapped | - | 211 |
| wheels | no_records | - | 815 |
| wheels | split | option_split | 20241 |
| wheels | conditional | conditional:engine_unattested | 664 |
| wheels | conditional | conditional:package | 25 |
| window-regulator | unmapped | - | 211 |
| window-regulator | no_records | - | 1169 |
| window-regulator | split | packaging_incomplete | 897 |
| window-regulator | split | packaging_split | 12325 |
| window-regulator | split | packaging_unstated | 7354 |
| window-switch | unmapped | - | 211 |
| window-switch | no_records | - | 2554 |
| window-switch | split | option_split | 17240 |
| window-switch | split | position_missing | 1647 |
| window-switch | conditional | conditional:engine_unattested | 304 |
| wiper-motor | unmapped | - | 211 |
| wiper-motor | no_records | - | 2105 |
| wiper-motor | split | no_candidates | 130 |
| wiper-motor | split | option_split | 8261 |
| wiper-motor | conditional | conditional:engine_unattested | 11249 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 124
- disputed_class: 211
- rule_drift: 10
- universal_part_suspect: 3
- wheel_compact_spare: 3
- wheels_not_audited: 19

## Unknown note clauses (top 30)

- `Package Quantity: 1`: 781
- `SPEEDOMETER TYPE - MPH(KMPH)`: 571
- `Require Quantity: 4`: 566
- `TIRE PRESSURE MONITORG SYS - HIGH LINE`: 449
- `ESC (ELECTRONIC STABILITY CONTROL)`: 427
- `I.M.S`: 345
- `VEHICLE PACKAGE - SPORTS`: 300
- `ABS (ANTI LOCK BRK SYS)`: 287
- `SIDE REPEATER LAMP (O/S MRR)`: 258
- `P/WINDOW DR'S - AUTO UP/DOWN & SAFETY`: 249
- `TIRE PRESSURE MONITORG SYS - LOW LINE`: 244
- `MODEL YEAR PACKAGE - 16MY`: 242
- `AUTO CRUISE CONTROL - CONVENTIONAL`: 235
- `SMART KEY-FR DR`: 219
- `AUTO CRUISE CONTROL - SMART`: 210
- `MODEL YEAR PACKAGE - 14MY`: 207
- `FOB KEY`: 204
- `PARKG BRK CONTROL-EPB`: 198
- `BLIND SPOT DETECTION SYSTEM - RADAR TYPE`: 194
- `TEMPORARY - STEEL WHEEL & TIRE (MINI)`: 184
- `COLOR - BODY COLOR`: 175
- `RR PARK'G ASSIST SYSTEM(RPAS)`: 173
- `TYPE - SEPARATED TYPE`: 168
- `Fit Note: HIGH GRADE`: 167
- `DRL - DEDICATED LED TYPE`: 163
- `CLUSTER TYPE - SUPER VISION 4.2" TFT LCD INFO`: 162
- `AUTONOMOUS EMERGENCY BRAKING - PEDESTRIAN`: 157
- `MDPS-BLAC-COLUMN`: 154
- `AIR VENTILATION SEAT`: 148
- `TUN'G MODE - SPORTY SUSPENSION`: 148

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
