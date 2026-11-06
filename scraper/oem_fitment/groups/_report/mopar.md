# OEM curation report: mopar

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-06T07:21:04Z.

- records 4533, classes 4034, list rows 29436, year manifests 104, cells 6496
- Verified groups 0, engine vg groups 0, Likely groups 169
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.moparpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.moparpartsgiant.com: only 2% of its 4357 fitment rows can be coverage: its option column holds trims (option_column_is_trims), which count only after a namespace audit (spec 5.2)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2391 |
| ac-compressor | no_records | - | 8241 |
| ac-compressor | not_closed | no_year_manifest | 25724 |
| ac-compressor | not_closed | stale | 24 |
| ac-compressor | not_closed | suspect_variant | 304 |
| ac-compressor | not_closed | uncrawled_chain_member | 2337 |
| ac-compressor | not_closed | unverified_product | 4963 |
| ac-compressor | split | no_candidates | 49 |
| alternator | unmapped | - | 2391 |
| alternator | no_records | - | 3274 |
| alternator | not_closed | no_list_manifest | 24 |
| alternator | not_closed | no_year_manifest | 30691 |
| alternator | not_closed | suspect_variant | 858 |
| alternator | not_closed | unattested | 27 |
| alternator | not_closed | uncrawled_chain_member | 141 |
| alternator | not_closed | unverified_product | 6627 |
| bumper-front | unmapped | - | 2391 |
| bumper-front | no_records | - | 34940 |
| bumper-front | not_closed | no_year_manifest | 6702 |
| bumper-rear | unmapped | - | 2391 |
| bumper-rear | no_records | - | 32949 |
| bumper-rear | not_closed | no_year_manifest | 8693 |
| climate-control | unmapped | - | 2391 |
| climate-control | no_records | - | 14843 |
| climate-control | not_closed | no_list_manifest | 629 |
| climate-control | not_closed | no_year_manifest | 20132 |
| climate-control | not_closed | unread_sibling_page | 6038 |
| door-front | unmapped | - | 2391 |
| door-front | no_records | - | 33864 |
| door-front | not_closed | no_year_manifest | 7778 |
| door-rear | unmapped | - | 2391 |
| door-rear | no_records | - | 33446 |
| door-rear | not_closed | no_year_manifest | 8196 |
| fender | unmapped | - | 2391 |
| fender | no_records | - | 33808 |
| fender | not_closed | no_year_manifest | 7834 |
| fuel-pump-module | unmapped | - | 2391 |
| fuel-pump-module | no_records | - | 6404 |
| fuel-pump-module | not_closed | no_year_manifest | 27561 |
| fuel-pump-module | not_closed | unread_sibling_page | 7677 |
| gauge-cluster | unmapped | - | 2391 |
| gauge-cluster | no_records | - | 39348 |
| gauge-cluster | not_closed | no_year_manifest | 2294 |
| grille | unmapped | - | 2391 |
| grille | no_records | - | 36250 |
| grille | not_closed | no_year_manifest | 5392 |
| headlights | unmapped | - | 2391 |
| headlights | no_records | - | 8815 |
| headlights | not_closed | no_year_manifest | 25177 |
| headlights | not_closed | uncrawled_chain_member | 32 |
| headlights | not_closed | unread_sibling_page | 7477 |
| headlights | split | no_candidates | 141 |
| hood | unmapped | - | 2391 |
| hood | no_records | - | 33479 |
| hood | not_closed | no_year_manifest | 8163 |
| ignition-coils | unmapped | - | 2391 |
| ignition-coils | no_records | - | 5033 |
| ignition-coils | not_closed | no_list_manifest | 6636 |
| ignition-coils | not_closed | no_year_manifest | 29973 |
| liftgate | unmapped | - | 2391 |
| liftgate | no_records | - | 34817 |
| liftgate | not_closed | no_year_manifest | 6825 |
| power-steering-pump | unmapped | - | 2391 |
| power-steering-pump | no_records | - | 6283 |
| power-steering-pump | not_closed | no_list_manifest | 225 |
| power-steering-pump | not_closed | no_year_manifest | 28728 |
| power-steering-pump | not_closed | unread_sibling_page | 6406 |
| radiator | unmapped | - | 2391 |
| radiator | no_records | - | 26576 |
| radiator | not_closed | no_list_manifest | 1755 |
| radiator | not_closed | no_year_manifest | 13311 |
| side-mirrors | unmapped | - | 2391 |
| side-mirrors | no_records | - | 5036 |
| side-mirrors | not_closed | no_list_manifest | 276 |
| side-mirrors | not_closed | no_year_manifest | 29178 |
| side-mirrors | not_closed | unattested | 27 |
| side-mirrors | not_closed | unread_sibling_page | 5152 |
| side-mirrors | not_closed | unverified_product | 1916 |
| side-mirrors | split | no_candidates | 47 |
| side-mirrors | split | position_conflict | 2 |
| side-mirrors | conditional | conditional:option | 8 |
| starter | unmapped | - | 2391 |
| starter | no_records | - | 2906 |
| starter | not_closed | no_list_manifest | 18 |
| starter | not_closed | no_year_manifest | 31061 |
| starter | not_closed | stale | 24 |
| starter | not_closed | suspect_variant | 441 |
| starter | not_closed | uncrawled_chain_member | 151 |
| starter | not_closed | unverified_product | 7041 |
| tail-lights | unmapped | - | 2391 |
| tail-lights | no_records | - | 12754 |
| tail-lights | not_closed | no_list_manifest | 27 |
| tail-lights | not_closed | no_year_manifest | 21211 |
| tail-lights | not_closed | stale | 24 |
| tail-lights | not_closed | suspect_variant | 111 |
| tail-lights | not_closed | uncrawled_chain_member | 1378 |
| tail-lights | not_closed | unverified_product | 3718 |
| tail-lights | split | no_candidates | 86 |
| tail-lights | split | option_split | 600 |
| tail-lights | conditional | conditional:body | 203 |
| tail-lights | conditional | conditional:option_layout | 141 |
| tail-lights | conditional | conditional:trim | 1389 |
| throttle-body | unmapped | - | 2391 |
| throttle-body | no_records | - | 3398 |
| throttle-body | not_closed | no_list_manifest | 151 |
| throttle-body | not_closed | no_year_manifest | 30593 |
| throttle-body | not_closed | suspect_variant | 276 |
| throttle-body | not_closed | unverified_product | 5601 |
| throttle-body | split | option_split | 1127 |
| throttle-body | conditional | conditional:fitted_not_listed | 168 |
| throttle-body | chain_member_conditional | chain_member_conditional | 328 |
| tow-mirrors | unmapped | - | 2391 |
| tow-mirrors | no_records | - | 39091 |
| tow-mirrors | not_closed | no_list_manifest | 479 |
| tow-mirrors | not_closed | no_year_manifest | 2072 |
| window-regulator | unmapped | - | 2391 |
| window-regulator | no_records | - | 4081 |
| window-regulator | not_closed | no_list_manifest | 369 |
| window-regulator | not_closed | no_year_manifest | 30128 |
| window-regulator | not_closed | stale | 24 |
| window-regulator | not_closed | uncrawled_chain_member | 945 |
| window-regulator | not_closed | unread_sibling_page | 2739 |
| window-regulator | not_closed | unverified_product | 2346 |
| window-regulator | split | no_candidates | 47 |
| window-regulator | split | packaging_unstated | 963 |
| window-switch | unmapped | - | 2391 |
| window-switch | no_records | - | 13330 |
| window-switch | not_closed | no_year_manifest | 20662 |
| window-switch | not_closed | stale | 24 |
| window-switch | not_closed | unread_sibling_page | 7626 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2391 |
| ac-compressor | no_records | - | 8241 |
| ac-compressor | split | no_candidates | 100 |
| ac-compressor | split | option_split | 28441 |
| ac-compressor | conditional | conditional:engine | 42 |
| ac-compressor | conditional | conditional:engine_unattested | 55 |
| ac-compressor | conditional | conditional:engine_unparsed | 25 |
| ac-compressor | conditional | conditional:notes_not_own_page | 2202 |
| ac-compressor | conditional | conditional:trim | 2536 |
| alternator | unmapped | - | 2391 |
| alternator | no_records | - | 3274 |
| alternator | split | option_split | 33600 |
| alternator | conditional | conditional:engine | 1551 |
| alternator | conditional | conditional:engine_unattested | 93 |
| alternator | conditional | conditional:engine_unparsed | 3 |
| alternator | conditional | conditional:notes_not_own_page | 511 |
| alternator | conditional | conditional:option | 185 |
| alternator | conditional | conditional:trim | 2425 |
| bumper-front | unmapped | - | 2391 |
| bumper-front | no_records | - | 34940 |
| bumper-front | split | option_split | 6176 |
| bumper-front | conditional | conditional:notes_not_own_page | 62 |
| bumper-front | conditional | conditional:trim | 464 |
| bumper-rear | unmapped | - | 2391 |
| bumper-rear | no_records | - | 32949 |
| bumper-rear | split | option_split | 7613 |
| bumper-rear | conditional | conditional:notes_not_own_page | 658 |
| bumper-rear | conditional | conditional:trim | 422 |
| climate-control | unmapped | - | 2391 |
| climate-control | no_records | - | 14843 |
| climate-control | split | no_candidates | 83 |
| climate-control | split | option_split | 20880 |
| climate-control | conditional | conditional:engine_unattested | 313 |
| climate-control | conditional | conditional:engine_unparsed | 17 |
| climate-control | conditional | conditional:notes_not_own_page | 1959 |
| climate-control | conditional | conditional:option | 8 |
| climate-control | conditional | conditional:option_layout | 166 |
| climate-control | conditional | conditional:trim | 3373 |
| door-front | unmapped | - | 2391 |
| door-front | no_records | - | 33864 |
| door-front | split | option_split | 1852 |
| door-front | conditional | conditional:notes_not_own_page | 872 |
| door-front | conditional | conditional:production | 47 |
| door-front | conditional | conditional:trim | 4658 |
| door-front | eligible | - | 349 |
| door-rear | unmapped | - | 2391 |
| door-rear | no_records | - | 33446 |
| door-rear | split | option_split | 1562 |
| door-rear | conditional | conditional:notes_not_own_page | 1966 |
| door-rear | conditional | conditional:trim | 3610 |
| door-rear | eligible | - | 1058 |
| fender | unmapped | - | 2391 |
| fender | no_records | - | 33808 |
| fender | split | option_split | 2568 |
| fender | conditional | conditional:notes_not_own_page | 1040 |
| fender | conditional | conditional:trim | 3583 |
| fender | chain_member_conditional | chain_member_conditional | 267 |
| fender | eligible | - | 376 |
| fuel-pump-module | unmapped | - | 2391 |
| fuel-pump-module | no_records | - | 6404 |
| fuel-pump-module | split | no_candidates | 202 |
| fuel-pump-module | split | option_split | 26684 |
| fuel-pump-module | conditional | conditional:engine | 39 |
| fuel-pump-module | conditional | conditional:engine_unattested | 29 |
| fuel-pump-module | conditional | conditional:fuel | 53 |
| fuel-pump-module | conditional | conditional:notes_not_own_page | 3337 |
| fuel-pump-module | conditional | conditional:option | 76 |
| fuel-pump-module | conditional | conditional:trim | 4818 |
| gauge-cluster | unmapped | - | 2391 |
| gauge-cluster | no_records | - | 39348 |
| gauge-cluster | split | option_split | 1992 |
| gauge-cluster | conditional | conditional:trim | 302 |
| grille | unmapped | - | 2391 |
| grille | no_records | - | 36250 |
| grille | split | option_split | 3847 |
| grille | conditional | conditional:notes_not_own_page | 1053 |
| grille | conditional | conditional:trim | 261 |
| grille | eligible | - | 231 |
| headlights | unmapped | - | 2391 |
| headlights | no_records | - | 8815 |
| headlights | split | no_candidates | 349 |
| headlights | split | option_split | 24635 |
| headlights | split | position_missing | 489 |
| headlights | split | slot_missing | 117 |
| headlights | conditional | conditional:engine | 264 |
| headlights | conditional | conditional:notes_not_own_page | 1841 |
| headlights | conditional | conditional:option | 198 |
| headlights | conditional | conditional:option_layout | 84 |
| headlights | conditional | conditional:trim | 4139 |
| headlights | conditional | conditional:unknown | 267 |
| headlights | chain_member_conditional | chain_member_conditional | 213 |
| headlights | eligible | - | 231 |
| hood | unmapped | - | 2391 |
| hood | no_records | - | 33479 |
| hood | split | option_split | 555 |
| hood | conditional | conditional:notes_not_own_page | 1869 |
| hood | conditional | conditional:trim | 5249 |
| hood | chain_member_conditional | chain_member_conditional | 164 |
| hood | eligible | - | 326 |
| ignition-coils | unmapped | - | 2391 |
| ignition-coils | no_records | - | 5033 |
| ignition-coils | split | option_split | 17567 |
| ignition-coils | conditional | conditional:engine | 3019 |
| ignition-coils | conditional | conditional:engine_unattested | 451 |
| ignition-coils | conditional | conditional:engine_unparsed | 28 |
| ignition-coils | conditional | conditional:notes_not_own_page | 6229 |
| ignition-coils | conditional | conditional:trim | 9084 |
| ignition-coils | eligible | - | 231 |
| liftgate | unmapped | - | 2391 |
| liftgate | no_records | - | 34817 |
| liftgate | split | option_split | 507 |
| liftgate | conditional | conditional:notes_not_own_page | 2805 |
| liftgate | conditional | conditional:trim | 2905 |
| liftgate | eligible | - | 608 |
| power-steering-pump | unmapped | - | 2391 |
| power-steering-pump | no_records | - | 6283 |
| power-steering-pump | split | no_candidates | 142 |
| power-steering-pump | split | option_split | 28508 |
| power-steering-pump | conditional | conditional:engine | 50 |
| power-steering-pump | conditional | conditional:engine_unattested | 302 |
| power-steering-pump | conditional | conditional:notes_not_own_page | 4172 |
| power-steering-pump | conditional | conditional:qualifier | 669 |
| power-steering-pump | conditional | conditional:trim | 1137 |
| power-steering-pump | conditional | conditional:unknown | 347 |
| power-steering-pump | reman_only | reman_only | 32 |
| radiator | unmapped | - | 2391 |
| radiator | no_records | - | 26576 |
| radiator | split | option_split | 10054 |
| radiator | conditional | conditional:engine | 80 |
| radiator | conditional | conditional:notes_not_own_page | 2300 |
| radiator | conditional | conditional:trim | 2632 |
| side-mirrors | unmapped | - | 2391 |
| side-mirrors | no_records | - | 5036 |
| side-mirrors | split | no_candidates | 74 |
| side-mirrors | split | option_split | 35091 |
| side-mirrors | split | position_conflict | 2 |
| side-mirrors | split | position_missing | 171 |
| side-mirrors | split | slot_missing | 498 |
| side-mirrors | conditional | conditional:notes_not_own_page | 63 |
| side-mirrors | conditional | conditional:option | 8 |
| side-mirrors | conditional | conditional:trim | 699 |
| starter | unmapped | - | 2391 |
| starter | no_records | - | 2906 |
| starter | split | no_candidates | 141 |
| starter | split | option_split | 35148 |
| starter | conditional | conditional:engine | 605 |
| starter | conditional | conditional:engine_unattested | 510 |
| starter | conditional | conditional:engine_unparsed | 7 |
| starter | conditional | conditional:notes_not_own_page | 435 |
| starter | conditional | conditional:option | 84 |
| starter | conditional | conditional:trim | 1806 |
| tail-lights | unmapped | - | 2391 |
| tail-lights | no_records | - | 12754 |
| tail-lights | split | no_candidates | 186 |
| tail-lights | split | option_split | 14727 |
| tail-lights | split | position_missing | 105 |
| tail-lights | conditional | conditional:body | 203 |
| tail-lights | conditional | conditional:engine | 931 |
| tail-lights | conditional | conditional:engine_unparsed | 17 |
| tail-lights | conditional | conditional:notes_not_own_page | 2207 |
| tail-lights | conditional | conditional:option | 219 |
| tail-lights | conditional | conditional:option_layout | 141 |
| tail-lights | conditional | conditional:trim | 9151 |
| tail-lights | chain_member_conditional | chain_member_conditional | 530 |
| tail-lights | blocked | unverified_member | 142 |
| tail-lights | eligible | - | 329 |
| throttle-body | unmapped | - | 2391 |
| throttle-body | no_records | - | 3398 |
| throttle-body | split | no_candidates | 227 |
| throttle-body | split | option_split | 30919 |
| throttle-body | conditional | conditional:engine | 1196 |
| throttle-body | conditional | conditional:engine_unattested | 185 |
| throttle-body | conditional | conditional:engine_unparsed | 7 |
| throttle-body | conditional | conditional:fitted_not_listed | 168 |
| throttle-body | conditional | conditional:notes_not_own_page | 3172 |
| throttle-body | conditional | conditional:option_layout | 47 |
| throttle-body | conditional | conditional:qualifier | 4 |
| throttle-body | conditional | conditional:trim | 1760 |
| throttle-body | chain_member_conditional | chain_member_conditional | 559 |
| tow-mirrors | unmapped | - | 2391 |
| tow-mirrors | no_records | - | 39091 |
| tow-mirrors | split | option_split | 2544 |
| tow-mirrors | conditional | conditional:trim | 7 |
| window-regulator | unmapped | - | 2391 |
| window-regulator | no_records | - | 4081 |
| window-regulator | split | no_candidates | 71 |
| window-regulator | split | packaging_unstated | 37490 |
| window-switch | unmapped | - | 2391 |
| window-switch | no_records | - | 13330 |
| window-switch | split | no_candidates | 1083 |
| window-switch | split | option_split | 20166 |
| window-switch | split | position_missing | 6382 |
| window-switch | conditional | conditional:notes_not_own_page | 164 |
| window-switch | conditional | conditional:trim | 517 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 77
- disputed_class: 499
- exclude_at_curation: 2
- recrawl_resolved: 3
- rule_drift: 27
- universal_part_suspect: 20

## Unknown note clauses (top 30)

- `D - DODGE`: 307
- `C - CHRYSLER`: 284
- `E - DODGE AWD`: 198
- `F - BRAND AWD`: 188
- `With Body Color`: 122
- `Body Color`: 115
- `With Foldaway`: 115
- `With Power Fold`: 96
- `All Models`: 82
- `Without Power Fold`: 80
- `Without Foldaway`: 74
- `ERB - 6 Cyl 3.6L VVT`: 65
- `Remanufactured`: 65
- `ED3 - 4 Cyl 2.4L DOHC Dual VVT`: 64
- `EGH - 6 Cyl 3.8L OHV`: 61
- `EZH - 8 Cyl 5.7L HEMI MDS VVT`: 60
- `Heated & Foldaway`: 58
- `Y - CHRYSLER`: 56
- `K - DODGE`: 55
- `41 - SEDAN/QUAD CAB SWB`: 54
- `With Rear AC`: 52
- `(GTS)`: 51
- `EGM - 6 Cyl 3.3L SMPI`: 51
- `3.3 & 3.8L`: 49
- `5 - Lt. Duty DODGE 4WD`: 46
- `With Psngr One Touch`: 46
- `AC & Heater`: 45
- `Without Psngr One Touch`: 45
- `74 - SPORT UTILITY 4-DR TYPE #4`: 43
- `61 - REG CAB 6.5 FT BOX`: 41

## Unmapped catalog models

- Chrysler Grand Voyager: feed 'Grand Voyager' 8 cars
- Chrysler Prowler: feed 'Prowler' 0 cars (excluded: catalog model with no feed cars as 'Prowler' (inventory 2026-11-04); nothing to map)
- Dodge D250: feed 'D250' 11 cars (excluded: M3: the feed spells this truck 'D250', 'D-250' and 'D250 Pickup' (one squash key); not mapped until the feed normalizes them)
- Dodge Omni: feed 'Omni' 1 cars (excluded: catalog model with no feed cars as 'Omni' (inventory 2026-11-04); nothing to map)
- Dodge Ram 4500: feed 'Ram 4500' 0 cars (excluded: catalog model with no feed cars as 'Ram 4500' (inventory 2026-11-04); nothing to map)
- Dodge Ram 5500: feed 'Ram 5500' 0 cars (excluded: catalog model with no feed cars as 'Ram 5500' (inventory 2026-11-04); nothing to map)
- Dodge Viper: feed 'Viper' 0 cars (excluded: catalog model with no feed cars as 'Viper' (inventory 2026-11-04); nothing to map)
- Jeep Gladiator: feed 'Gladiator' 1 cars
- Jeep J20: feed 'J20' 0 cars (excluded: catalog model with no feed cars as 'J20' (inventory 2026-11-04); nothing to map)
- Ram 4500: feed '4500' 0 cars
- Ram 5500: feed '5500' 0 cars
