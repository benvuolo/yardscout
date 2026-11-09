# OEM curation report: vag

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-06T01:15:49Z.

- records 2376, classes 2318, list rows 20061, year manifests 76, cells 8544
- Verified groups 0, engine vg groups 0, Likely groups 6
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.audipartsgiant.com, www.vwpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 719 |
| ac-compressor | no_records | - | 602 |
| ac-compressor | not_closed | no_list_manifest | 1002 |
| ac-compressor | not_closed | no_year_manifest | 6334 |
| ac-compressor | not_closed | unread_sibling_page | 543 |
| ac-compressor | not_closed | year_manifest_bad | 28 |
| alternator | unmapped | - | 719 |
| alternator | no_records | - | 636 |
| alternator | not_closed | no_list_manifest | 1008 |
| alternator | not_closed | no_year_manifest | 6294 |
| alternator | not_closed | suspect_variant | 74 |
| alternator | not_closed | uncrawled_chain_member | 141 |
| alternator | not_closed | unverified_product | 328 |
| alternator | not_closed | year_manifest_bad | 28 |
| bumper-front | unmapped | - | 719 |
| bumper-front | no_records | - | 1207 |
| bumper-front | not_closed | no_year_manifest | 5766 |
| bumper-front | not_closed | unread_sibling_page | 1536 |
| bumper-rear | unmapped | - | 719 |
| bumper-rear | no_records | - | 897 |
| bumper-rear | not_closed | no_list_manifest | 12 |
| bumper-rear | not_closed | no_year_manifest | 6036 |
| bumper-rear | not_closed | unread_sibling_page | 1536 |
| bumper-rear | not_closed | year_manifest_bad | 28 |
| climate-control | unmapped | - | 719 |
| climate-control | no_records | - | 824 |
| climate-control | not_closed | no_list_manifest | 1002 |
| climate-control | not_closed | no_year_manifest | 6119 |
| climate-control | not_closed | unread_sibling_page | 536 |
| climate-control | not_closed | year_manifest_bad | 28 |
| fender | unmapped | - | 719 |
| fender | no_records | - | 525 |
| fender | not_closed | no_list_manifest | 16 |
| fender | not_closed | no_year_manifest | 6404 |
| fender | not_closed | uncrawled_chain_member | 194 |
| fender | not_closed | unread_sibling_page | 1039 |
| fender | not_closed | year_manifest_bad | 28 |
| fender | split | option_split | 7 |
| fender | conditional | conditional:trim | 296 |
| fuel-pump-module | unmapped | - | 719 |
| fuel-pump-module | no_records | - | 1356 |
| fuel-pump-module | not_closed | no_list_manifest | 944 |
| fuel-pump-module | not_closed | no_year_manifest | 5638 |
| fuel-pump-module | not_closed | unread_sibling_page | 543 |
| fuel-pump-module | not_closed | year_manifest_bad | 28 |
| gauge-cluster | unmapped | - | 719 |
| gauge-cluster | no_records | - | 2763 |
| gauge-cluster | not_closed | no_year_manifest | 4182 |
| gauge-cluster | not_closed | unread_sibling_page | 1536 |
| gauge-cluster | not_closed | year_manifest_bad | 28 |
| grille | unmapped | - | 719 |
| grille | no_records | - | 1662 |
| grille | not_closed | no_list_manifest | 12 |
| grille | not_closed | no_year_manifest | 5339 |
| grille | not_closed | uncrawled_chain_member | 1342 |
| grille | split | option_split | 99 |
| grille | conditional | conditional:trim | 55 |
| headlights | unmapped | - | 719 |
| headlights | no_records | - | 1430 |
| headlights | not_closed | no_list_manifest | 1002 |
| headlights | not_closed | no_year_manifest | 5506 |
| headlights | not_closed | unread_sibling_page | 543 |
| headlights | not_closed | year_manifest_bad | 28 |
| hood | unmapped | - | 719 |
| hood | no_records | - | 721 |
| hood | not_closed | no_list_manifest | 16 |
| hood | not_closed | no_year_manifest | 6208 |
| hood | not_closed | uncrawled_chain_member | 1314 |
| hood | not_closed | unread_sibling_page | 52 |
| hood | not_closed | year_manifest_bad | 28 |
| hood | conditional | conditional:engine_unattested | 7 |
| hood | conditional | conditional:trim | 163 |
| ignition-coils | unmapped | - | 719 |
| ignition-coils | no_records | - | 287 |
| ignition-coils | not_closed | no_list_manifest | 16 |
| ignition-coils | not_closed | no_year_manifest | 6642 |
| ignition-coils | not_closed | uncrawled_chain_member | 44 |
| ignition-coils | not_closed | unread_sibling_page | 1492 |
| ignition-coils | not_closed | year_manifest_bad | 28 |
| liftgate | unmapped | - | 719 |
| liftgate | no_records | - | 4276 |
| liftgate | not_closed | no_list_manifest | 12 |
| liftgate | not_closed | no_year_manifest | 3415 |
| liftgate | not_closed | unread_sibling_page | 797 |
| liftgate | split | no_candidates | 7 |
| liftgate | conditional | conditional:trim | 2 |
| power-steering-pump | unmapped | - | 719 |
| power-steering-pump | no_records | - | 3834 |
| power-steering-pump | not_closed | no_list_manifest | 630 |
| power-steering-pump | not_closed | no_year_manifest | 3702 |
| power-steering-pump | not_closed | unread_sibling_page | 343 |
| radiator | unmapped | - | 719 |
| radiator | no_records | - | 236 |
| radiator | not_closed | no_list_manifest | 16 |
| radiator | not_closed | no_year_manifest | 6693 |
| radiator | not_closed | unread_sibling_page | 1536 |
| radiator | not_closed | year_manifest_bad | 28 |
| side-mirrors | unmapped | - | 719 |
| side-mirrors | no_records | - | 2862 |
| side-mirrors | not_closed | no_list_manifest | 1002 |
| side-mirrors | not_closed | no_year_manifest | 4074 |
| side-mirrors | not_closed | uncrawled_chain_member | 52 |
| side-mirrors | not_closed | unread_sibling_page | 491 |
| side-mirrors | not_closed | year_manifest_bad | 28 |
| starter | unmapped | - | 719 |
| starter | no_records | - | 395 |
| starter | not_closed | no_list_manifest | 1008 |
| starter | not_closed | no_year_manifest | 6535 |
| starter | not_closed | suspect_variant | 324 |
| starter | not_closed | uncrawled_chain_member | 52 |
| starter | not_closed | unverified_product | 167 |
| starter | not_closed | year_manifest_bad | 28 |
| tail-lights | unmapped | - | 719 |
| tail-lights | no_records | - | 967 |
| tail-lights | not_closed | no_list_manifest | 1014 |
| tail-lights | not_closed | no_year_manifest | 5969 |
| tail-lights | not_closed | uncrawled_chain_member | 319 |
| tail-lights | not_closed | unread_sibling_page | 59 |
| tail-lights | not_closed | year_manifest_bad | 28 |
| tail-lights | split | option_split | 138 |
| tail-lights | conditional | conditional:model_other | 7 |
| tail-lights | conditional | conditional:trim | 8 |
| throttle-body | unmapped | - | 719 |
| throttle-body | no_records | - | 595 |
| throttle-body | not_closed | no_list_manifest | 1009 |
| throttle-body | not_closed | no_year_manifest | 6334 |
| throttle-body | not_closed | uncrawled_chain_member | 135 |
| throttle-body | not_closed | unverified_product | 337 |
| throttle-body | not_closed | year_manifest_bad | 28 |
| throttle-body | split | option_split | 59 |
| throttle-body | conditional | conditional:trim | 12 |
| trunk-lid | unmapped | - | 719 |
| trunk-lid | no_records | - | 2351 |
| trunk-lid | not_closed | no_list_manifest | 4 |
| trunk-lid | not_closed | no_year_manifest | 4851 |
| trunk-lid | not_closed | unread_sibling_page | 1303 |
| window-regulator | unmapped | - | 719 |
| window-regulator | no_records | - | 738 |
| window-regulator | not_closed | no_list_manifest | 968 |
| window-regulator | not_closed | no_year_manifest | 6274 |
| window-regulator | not_closed | uncrawled_chain_member | 268 |
| window-regulator | not_closed | unread_sibling_page | 198 |
| window-regulator | not_closed | unverified_product | 35 |
| window-regulator | not_closed | year_manifest_bad | 28 |
| window-switch | unmapped | - | 719 |
| window-switch | no_records | - | 858 |
| window-switch | not_closed | no_list_manifest | 1009 |
| window-switch | not_closed | no_year_manifest | 6113 |
| window-switch | not_closed | unread_sibling_page | 501 |
| window-switch | not_closed | year_manifest_bad | 28 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 719 |
| ac-compressor | no_records | - | 602 |
| ac-compressor | split | option_split | 5877 |
| ac-compressor | conditional | conditional:engine | 79 |
| ac-compressor | conditional | conditional:engine_unattested | 818 |
| ac-compressor | conditional | conditional:trim | 1133 |
| alternator | unmapped | - | 719 |
| alternator | no_records | - | 636 |
| alternator | split | option_split | 7334 |
| alternator | conditional | conditional:engine | 83 |
| alternator | conditional | conditional:engine_unattested | 141 |
| alternator | conditional | conditional:trim | 315 |
| bumper-front | unmapped | - | 719 |
| bumper-front | no_records | - | 1207 |
| bumper-front | split | option_split | 3812 |
| bumper-front | conditional | conditional:body | 116 |
| bumper-front | conditional | conditional:engine | 12 |
| bumper-front | conditional | conditional:engine_unattested | 523 |
| bumper-front | conditional | conditional:trim | 2839 |
| bumper-rear | unmapped | - | 719 |
| bumper-rear | no_records | - | 897 |
| bumper-rear | split | no_candidates | 7 |
| bumper-rear | split | option_split | 5276 |
| bumper-rear | conditional | conditional:body | 227 |
| bumper-rear | conditional | conditional:colour | 6 |
| bumper-rear | conditional | conditional:engine_unattested | 634 |
| bumper-rear | conditional | conditional:trim | 1462 |
| climate-control | unmapped | - | 719 |
| climate-control | no_records | - | 824 |
| climate-control | split | option_split | 7115 |
| climate-control | conditional | conditional:engine_unattested | 215 |
| climate-control | conditional | conditional:model_other | 1 |
| climate-control | conditional | conditional:trim | 354 |
| fender | unmapped | - | 719 |
| fender | no_records | - | 525 |
| fender | split | option_split | 2429 |
| fender | split | slot_missing | 4 |
| fender | conditional | conditional:body | 2 |
| fender | conditional | conditional:engine | 12 |
| fender | conditional | conditional:engine_unattested | 1690 |
| fender | conditional | conditional:production | 44 |
| fender | conditional | conditional:trim | 3803 |
| fuel-pump-module | unmapped | - | 719 |
| fuel-pump-module | no_records | - | 1356 |
| fuel-pump-module | split | no_candidates | 7 |
| fuel-pump-module | split | option_split | 5394 |
| fuel-pump-module | conditional | conditional:engine | 7 |
| fuel-pump-module | conditional | conditional:engine_unattested | 425 |
| fuel-pump-module | conditional | conditional:fuel | 13 |
| fuel-pump-module | conditional | conditional:trim | 1307 |
| gauge-cluster | unmapped | - | 719 |
| gauge-cluster | no_records | - | 2763 |
| gauge-cluster | split | option_split | 5064 |
| gauge-cluster | conditional | conditional:engine | 22 |
| gauge-cluster | conditional | conditional:engine_unattested | 13 |
| gauge-cluster | conditional | conditional:trim | 647 |
| grille | unmapped | - | 719 |
| grille | no_records | - | 1662 |
| grille | split | option_split | 5642 |
| grille | conditional | conditional:engine | 12 |
| grille | conditional | conditional:engine_unattested | 276 |
| grille | conditional | conditional:trim | 917 |
| headlights | unmapped | - | 719 |
| headlights | no_records | - | 1430 |
| headlights | split | option_split | 5887 |
| headlights | split | position_missing | 1 |
| headlights | conditional | conditional:engine_unattested | 3 |
| headlights | conditional | conditional:option | 210 |
| headlights | conditional | conditional:trim | 978 |
| hood | unmapped | - | 719 |
| hood | no_records | - | 721 |
| hood | split | option_split | 1871 |
| hood | conditional | conditional:body | 42 |
| hood | conditional | conditional:engine | 12 |
| hood | conditional | conditional:engine_unattested | 1278 |
| hood | conditional | conditional:trim | 4585 |
| ignition-coils | unmapped | - | 719 |
| ignition-coils | no_records | - | 287 |
| ignition-coils | split | option_split | 5176 |
| ignition-coils | conditional | conditional:engine | 241 |
| ignition-coils | conditional | conditional:engine_unattested | 1164 |
| ignition-coils | conditional | conditional:trim | 1641 |
| liftgate | unmapped | - | 719 |
| liftgate | no_records | - | 4276 |
| liftgate | split | no_candidates | 7 |
| liftgate | split | option_split | 587 |
| liftgate | conditional | conditional:body | 264 |
| liftgate | conditional | conditional:engine_unattested | 670 |
| liftgate | conditional | conditional:production | 52 |
| liftgate | conditional | conditional:trim | 2653 |
| power-steering-pump | unmapped | - | 719 |
| power-steering-pump | no_records | - | 3834 |
| power-steering-pump | split | no_candidates | 52 |
| power-steering-pump | split | option_split | 3086 |
| power-steering-pump | conditional | conditional:engine | 152 |
| power-steering-pump | conditional | conditional:engine_unattested | 280 |
| power-steering-pump | conditional | conditional:trim | 1105 |
| radiator | unmapped | - | 719 |
| radiator | no_records | - | 236 |
| radiator | split | option_split | 6483 |
| radiator | conditional | conditional:body | 42 |
| radiator | conditional | conditional:colour | 17 |
| radiator | conditional | conditional:engine | 129 |
| radiator | conditional | conditional:engine_unattested | 852 |
| radiator | conditional | conditional:production | 7 |
| radiator | conditional | conditional:trans | 5 |
| radiator | conditional | conditional:trim | 738 |
| side-mirrors | unmapped | - | 719 |
| side-mirrors | no_records | - | 2862 |
| side-mirrors | split | option_split | 4879 |
| side-mirrors | split | slot_missing | 3 |
| side-mirrors | conditional | conditional:body | 42 |
| side-mirrors | conditional | conditional:engine_unattested | 27 |
| side-mirrors | conditional | conditional:trim | 696 |
| starter | unmapped | - | 719 |
| starter | no_records | - | 395 |
| starter | split | option_split | 6545 |
| starter | conditional | conditional:engine_unattested | 470 |
| starter | conditional | conditional:trans | 4 |
| starter | conditional | conditional:trim | 1095 |
| tail-lights | unmapped | - | 719 |
| tail-lights | no_records | - | 967 |
| tail-lights | split | option_split | 4766 |
| tail-lights | split | slot_missing | 3 |
| tail-lights | conditional | conditional:body | 272 |
| tail-lights | conditional | conditional:engine_unattested | 497 |
| tail-lights | conditional | conditional:model_other | 7 |
| tail-lights | conditional | conditional:production | 5 |
| tail-lights | conditional | conditional:trim | 1992 |
| throttle-body | unmapped | - | 719 |
| throttle-body | no_records | - | 595 |
| throttle-body | split | option_split | 5845 |
| throttle-body | conditional | conditional:engine | 11 |
| throttle-body | conditional | conditional:engine_unattested | 1177 |
| throttle-body | conditional | conditional:trim | 881 |
| trunk-lid | unmapped | - | 719 |
| trunk-lid | no_records | - | 2351 |
| trunk-lid | split | no_candidates | 7 |
| trunk-lid | split | option_split | 1412 |
| trunk-lid | conditional | conditional:body | 305 |
| trunk-lid | conditional | conditional:engine_unattested | 366 |
| trunk-lid | conditional | conditional:trim | 4068 |
| window-regulator | unmapped | - | 719 |
| window-regulator | no_records | - | 738 |
| window-regulator | split | no_candidates | 12 |
| window-regulator | split | packaging_unstated | 7759 |
| window-switch | unmapped | - | 719 |
| window-switch | no_records | - | 858 |
| window-switch | split | no_candidates | 83 |
| window-switch | split | option_split | 6800 |
| window-switch | split | position_missing | 231 |
| window-switch | conditional | conditional:body | 116 |
| window-switch | conditional | conditional:engine_unattested | 288 |
| window-switch | conditional | conditional:model_other | 46 |
| window-switch | conditional | conditional:production | 21 |
| window-switch | conditional | conditional:trim | 66 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- disputed_class: 58
- evidence_mismatch: 6
- held_exterior_cross_model: 14
- rule_drift: 2
- systemic_evidence_failure: 2
- universal_part_suspect: 6

## Unknown note clauses (top 30)

- `Remanufactured`: 63
- `Valeo`: 53
- `Bosch`: 47
- `With Heated Seats`: 40
- `Without Heated Seats`: 37
- `With Directional Beam`: 34
- `Without Directional Beam`: 32
- `With Xenon Headlamps`: 30
- `Without GLI`: 28
- `With Park Sensor`: 27
- `With Park Sensors`: 27
- `Without R`: 24
- `All`: 23
- `Denso`: 23
- `Sedan/Wagon`: 23
- `With S-Line Package`: 23
- `Without Park Sensor`: 23
- `With S-Line`: 22
- `Without Park Sensors`: 20
- `Without S-Line Package`: 20
- `Without Turbocharger`: 20
- `Without Hybrid`: 18
- `Without Auto Dim`: 16
- `Black/Chrome`: 15
- `With GLI`: 15
- `With Headlamp Washer`: 15
- `Without Headlamp Washer`: 15
- `Without R32`: 15
- `Without S-Line`: 15
- `Lift Gate`: 14

## Unmapped catalog models

- Audi 100 Quattro: feed '100 Quattro' 0 cars
- Audi 90: feed '90' 0 cars
- Audi 90 Quattro: feed '90 Quattro' 0 cars
- Audi A3 Sportback e-tron: feed 'A3 Sportback e-tron' 0 cars
- Audi A4 allroad: feed 'A4 allroad' 0 cars
- Audi A5 Sportback: feed 'A5 Sportback' 0 cars
- Audi A6 allroad: feed 'A6 allroad' 0 cars
- Audi A7 Sportback: feed 'A7 Sportback' 0 cars
- Audi Q4 e-tron: feed 'Q4 e-tron' 0 cars
- Audi Q4 e-tron Sportback: feed 'Q4 e-tron Sportback' 0 cars
- Audi Q5 PHEV: feed 'Q5 PHEV' 0 cars
- Audi Q6 e-tron: feed 'Q6 e-tron' 0 cars
- Audi Q8: feed 'Q8' 0 cars
- Audi Q8 e-tron: feed 'Q8 e-tron' 0 cars
- Audi Q8 e-tron Sportback: feed 'Q8 e-tron Sportback' 0 cars
- Audi R8: feed 'R8' 0 cars
- Audi RS Q8: feed 'RS Q8' 0 cars
- Audi RS e-tron GT: feed 'RS e-tron GT' 0 cars
- Audi RS3: feed 'RS3' 0 cars
- Audi RS4: feed 'RS4' 0 cars
- Audi RS5: feed 'RS5' 0 cars
- Audi RS5 Sportback: feed 'RS5 Sportback' 0 cars
- Audi RS6: feed 'RS6' 0 cars
- Audi RS6 Avant: feed 'RS6 Avant' 0 cars
- Audi RS7: feed 'RS7' 0 cars
- Audi RS7 Sportback: feed 'RS7 Sportback' 0 cars
- Audi S5 Sportback: feed 'S5 Sportback' 0 cars
- Audi S7 Sportback: feed 'S7 Sportback' 0 cars
- Audi SQ5 Sportback: feed 'SQ5 Sportback' 0 cars
- Audi SQ6 e-tron: feed 'SQ6 e-tron' 0 cars
- Audi SQ7: feed 'SQ7' 0 cars
- Audi SQ8: feed 'SQ8' 0 cars
- Audi SQ8 e-tron: feed 'SQ8 e-tron' 0 cars
- Audi SQ8 e-tron Sportback: feed 'SQ8 e-tron Sportback' 0 cars
- Audi TT RS Quattro: feed 'TT RS Quattro' 0 cars
- Audi TTS Quattro: feed 'TTS Quattro' 0 cars
- Audi V8 Quattro: feed 'V8 Quattro' 0 cars
- Audi e-tron GT: feed 'e-tron GT' 0 cars
- Audi e-tron Quattro: feed 'e-tron Quattro' 0 cars
- Audi e-tron S: feed 'e-tron S' 0 cars
- Audi e-tron S Sportback: feed 'e-tron S Sportback' 0 cars
- Audi e-tron Sportback: feed 'e-tron Sportback' 0 cars
- Volkswagen Atlas Cross Sport: feed 'Atlas Cross Sport' 0 cars
- Volkswagen Corrado: feed 'Corrado' 0 cars
- Volkswagen EuroVan: feed 'EuroVan' 0 cars
- Volkswagen Golf R: feed 'Golf R' 1 cars (excluded: feed sub-model 'Golf R' (1 car) under catalog 'Golf'; R bodywork and lamps differ (interchange, 2026-11-09; unmapped, no claims, until a reviewed entry exists))
- Volkswagen Golf SportWagen: feed 'Golf SportWagen' 0 cars
- Volkswagen ID. Buzz: feed 'ID. Buzz' 0 cars
- Volkswagen ID.4: feed 'ID.4' 0 cars
- Volkswagen Quantum: feed 'Quantum' 0 cars
- Volkswagen R32: feed 'R32' 0 cars
- Volkswagen Rabbit: feed 'Rabbit' 136 cars
- Volkswagen Taos: feed 'Taos' 5 cars
- Volkswagen Tiguan Limited: feed 'Tiguan Limited' 0 cars
- Volkswagen e-Golf: feed 'e-Golf' 0 cars
