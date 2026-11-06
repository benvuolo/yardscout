# OEM curation report: vag

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-06T01:15:49Z.

- records 2376, classes 2318, list rows 20061, year manifests 76, cells 8544
- Verified groups 0, engine vg groups 0, Likely groups 31
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.audipartsgiant.com, www.vwpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 708 |
| ac-compressor | no_records | - | 602 |
| ac-compressor | not_closed | no_list_manifest | 1003 |
| ac-compressor | not_closed | no_year_manifest | 6313 |
| ac-compressor | not_closed | unread_sibling_page | 540 |
| ac-compressor | not_closed | year_manifest_bad | 27 |
| alternator | unmapped | - | 708 |
| alternator | no_records | - | 639 |
| alternator | not_closed | no_list_manifest | 1008 |
| alternator | not_closed | no_year_manifest | 6271 |
| alternator | not_closed | suspect_variant | 73 |
| alternator | not_closed | uncrawled_chain_member | 139 |
| alternator | not_closed | unverified_product | 328 |
| alternator | not_closed | year_manifest_bad | 27 |
| bumper-front | unmapped | - | 708 |
| bumper-front | no_records | - | 1201 |
| bumper-front | not_closed | no_year_manifest | 5750 |
| bumper-front | not_closed | unread_sibling_page | 1534 |
| bumper-rear | unmapped | - | 708 |
| bumper-rear | no_records | - | 896 |
| bumper-rear | not_closed | no_list_manifest | 12 |
| bumper-rear | not_closed | no_year_manifest | 6016 |
| bumper-rear | not_closed | unread_sibling_page | 1534 |
| bumper-rear | not_closed | year_manifest_bad | 27 |
| climate-control | unmapped | - | 708 |
| climate-control | no_records | - | 830 |
| climate-control | not_closed | no_list_manifest | 1003 |
| climate-control | not_closed | no_year_manifest | 6093 |
| climate-control | not_closed | unread_sibling_page | 532 |
| climate-control | not_closed | year_manifest_bad | 27 |
| fender | unmapped | - | 708 |
| fender | no_records | - | 526 |
| fender | not_closed | no_list_manifest | 16 |
| fender | not_closed | no_year_manifest | 6382 |
| fender | not_closed | uncrawled_chain_member | 193 |
| fender | not_closed | unread_sibling_page | 1037 |
| fender | not_closed | year_manifest_bad | 27 |
| fender | split | option_split | 8 |
| fender | conditional | conditional:trim | 296 |
| fuel-pump-module | unmapped | - | 708 |
| fuel-pump-module | no_records | - | 1343 |
| fuel-pump-module | not_closed | no_list_manifest | 942 |
| fuel-pump-module | not_closed | no_year_manifest | 5633 |
| fuel-pump-module | not_closed | unread_sibling_page | 540 |
| fuel-pump-module | not_closed | year_manifest_bad | 27 |
| gauge-cluster | unmapped | - | 708 |
| gauge-cluster | no_records | - | 2752 |
| gauge-cluster | not_closed | no_year_manifest | 4172 |
| gauge-cluster | not_closed | unread_sibling_page | 1534 |
| gauge-cluster | not_closed | year_manifest_bad | 27 |
| grille | unmapped | - | 708 |
| grille | no_records | - | 1666 |
| grille | not_closed | no_list_manifest | 12 |
| grille | not_closed | no_year_manifest | 5315 |
| grille | not_closed | uncrawled_chain_member | 1336 |
| grille | split | option_split | 100 |
| grille | conditional | conditional:trim | 56 |
| headlights | unmapped | - | 708 |
| headlights | no_records | - | 1427 |
| headlights | not_closed | no_list_manifest | 1003 |
| headlights | not_closed | no_year_manifest | 5488 |
| headlights | not_closed | unread_sibling_page | 540 |
| headlights | not_closed | year_manifest_bad | 27 |
| hood | unmapped | - | 708 |
| hood | no_records | - | 715 |
| hood | not_closed | no_list_manifest | 16 |
| hood | not_closed | no_year_manifest | 6193 |
| hood | not_closed | uncrawled_chain_member | 1309 |
| hood | not_closed | unread_sibling_page | 54 |
| hood | not_closed | year_manifest_bad | 27 |
| hood | conditional | conditional:engine_unattested | 7 |
| hood | conditional | conditional:trim | 164 |
| ignition-coils | unmapped | - | 708 |
| ignition-coils | no_records | - | 285 |
| ignition-coils | not_closed | no_list_manifest | 16 |
| ignition-coils | not_closed | no_year_manifest | 6623 |
| ignition-coils | not_closed | uncrawled_chain_member | 41 |
| ignition-coils | not_closed | unread_sibling_page | 1493 |
| ignition-coils | not_closed | year_manifest_bad | 27 |
| liftgate | unmapped | - | 708 |
| liftgate | no_records | - | 4255 |
| liftgate | not_closed | no_list_manifest | 12 |
| liftgate | not_closed | no_year_manifest | 3410 |
| liftgate | not_closed | unread_sibling_page | 798 |
| liftgate | split | no_candidates | 8 |
| liftgate | conditional | conditional:trim | 2 |
| power-steering-pump | unmapped | - | 708 |
| power-steering-pump | no_records | - | 3830 |
| power-steering-pump | not_closed | no_list_manifest | 628 |
| power-steering-pump | not_closed | no_year_manifest | 3689 |
| power-steering-pump | not_closed | unread_sibling_page | 338 |
| radiator | unmapped | - | 708 |
| radiator | no_records | - | 231 |
| radiator | not_closed | no_list_manifest | 16 |
| radiator | not_closed | no_year_manifest | 6677 |
| radiator | not_closed | unread_sibling_page | 1534 |
| radiator | not_closed | year_manifest_bad | 27 |
| side-mirrors | unmapped | - | 708 |
| side-mirrors | no_records | - | 2847 |
| side-mirrors | not_closed | no_list_manifest | 1003 |
| side-mirrors | not_closed | no_year_manifest | 4068 |
| side-mirrors | not_closed | uncrawled_chain_member | 52 |
| side-mirrors | not_closed | unread_sibling_page | 488 |
| side-mirrors | not_closed | year_manifest_bad | 27 |
| starter | unmapped | - | 708 |
| starter | no_records | - | 396 |
| starter | not_closed | no_list_manifest | 1008 |
| starter | not_closed | no_year_manifest | 6514 |
| starter | not_closed | suspect_variant | 320 |
| starter | not_closed | uncrawled_chain_member | 52 |
| starter | not_closed | unverified_product | 168 |
| starter | not_closed | year_manifest_bad | 27 |
| tail-lights | unmapped | - | 708 |
| tail-lights | no_records | - | 970 |
| tail-lights | not_closed | no_list_manifest | 1015 |
| tail-lights | not_closed | no_year_manifest | 5945 |
| tail-lights | not_closed | uncrawled_chain_member | 316 |
| tail-lights | not_closed | unread_sibling_page | 59 |
| tail-lights | not_closed | year_manifest_bad | 27 |
| tail-lights | split | option_split | 136 |
| tail-lights | conditional | conditional:model_other | 7 |
| tail-lights | conditional | conditional:trim | 10 |
| throttle-body | unmapped | - | 708 |
| throttle-body | no_records | - | 592 |
| throttle-body | not_closed | no_list_manifest | 1010 |
| throttle-body | not_closed | no_year_manifest | 6316 |
| throttle-body | not_closed | uncrawled_chain_member | 133 |
| throttle-body | not_closed | unverified_product | 335 |
| throttle-body | not_closed | year_manifest_bad | 27 |
| throttle-body | split | option_split | 60 |
| throttle-body | conditional | conditional:trim | 12 |
| trunk-lid | unmapped | - | 708 |
| trunk-lid | no_records | - | 2354 |
| trunk-lid | not_closed | no_list_manifest | 4 |
| trunk-lid | not_closed | no_year_manifest | 4828 |
| trunk-lid | not_closed | unread_sibling_page | 1299 |
| window-regulator | unmapped | - | 708 |
| window-regulator | no_records | - | 740 |
| window-regulator | not_closed | no_list_manifest | 966 |
| window-regulator | not_closed | no_year_manifest | 6252 |
| window-regulator | not_closed | uncrawled_chain_member | 267 |
| window-regulator | not_closed | unread_sibling_page | 198 |
| window-regulator | not_closed | unverified_product | 35 |
| window-regulator | not_closed | year_manifest_bad | 27 |
| window-switch | unmapped | - | 708 |
| window-switch | no_records | - | 867 |
| window-switch | not_closed | no_list_manifest | 1006 |
| window-switch | not_closed | no_year_manifest | 6085 |
| window-switch | not_closed | unread_sibling_page | 500 |
| window-switch | not_closed | year_manifest_bad | 27 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 708 |
| ac-compressor | no_records | - | 602 |
| ac-compressor | split | option_split | 5864 |
| ac-compressor | conditional | conditional:engine | 79 |
| ac-compressor | conditional | conditional:engine_unattested | 807 |
| ac-compressor | conditional | conditional:trim | 1133 |
| alternator | unmapped | - | 708 |
| alternator | no_records | - | 639 |
| alternator | split | option_split | 7312 |
| alternator | conditional | conditional:engine | 81 |
| alternator | conditional | conditional:engine_unattested | 136 |
| alternator | conditional | conditional:trim | 317 |
| bumper-front | unmapped | - | 708 |
| bumper-front | no_records | - | 1201 |
| bumper-front | split | option_split | 3790 |
| bumper-front | conditional | conditional:body | 115 |
| bumper-front | conditional | conditional:engine | 11 |
| bumper-front | conditional | conditional:engine_unattested | 522 |
| bumper-front | conditional | conditional:trim | 2846 |
| bumper-rear | unmapped | - | 708 |
| bumper-rear | no_records | - | 896 |
| bumper-rear | split | no_candidates | 7 |
| bumper-rear | split | option_split | 5260 |
| bumper-rear | conditional | conditional:body | 226 |
| bumper-rear | conditional | conditional:colour | 6 |
| bumper-rear | conditional | conditional:engine_unattested | 630 |
| bumper-rear | conditional | conditional:trim | 1460 |
| climate-control | unmapped | - | 708 |
| climate-control | no_records | - | 830 |
| climate-control | split | option_split | 7083 |
| climate-control | conditional | conditional:engine_unattested | 217 |
| climate-control | conditional | conditional:model_other | 2 |
| climate-control | conditional | conditional:trim | 353 |
| fender | unmapped | - | 708 |
| fender | no_records | - | 526 |
| fender | split | option_split | 2417 |
| fender | split | slot_missing | 4 |
| fender | conditional | conditional:body | 1 |
| fender | conditional | conditional:engine | 11 |
| fender | conditional | conditional:engine_unattested | 1676 |
| fender | conditional | conditional:production | 41 |
| fender | conditional | conditional:trim | 3809 |
| fuel-pump-module | unmapped | - | 708 |
| fuel-pump-module | no_records | - | 1343 |
| fuel-pump-module | split | no_candidates | 7 |
| fuel-pump-module | split | option_split | 5396 |
| fuel-pump-module | conditional | conditional:engine | 7 |
| fuel-pump-module | conditional | conditional:engine_unattested | 423 |
| fuel-pump-module | conditional | conditional:fuel | 13 |
| fuel-pump-module | conditional | conditional:trim | 1296 |
| gauge-cluster | unmapped | - | 708 |
| gauge-cluster | no_records | - | 2752 |
| gauge-cluster | split | option_split | 5044 |
| gauge-cluster | conditional | conditional:engine | 22 |
| gauge-cluster | conditional | conditional:engine_unattested | 14 |
| gauge-cluster | conditional | conditional:trim | 653 |
| grille | unmapped | - | 708 |
| grille | no_records | - | 1666 |
| grille | split | option_split | 5619 |
| grille | conditional | conditional:engine | 11 |
| grille | conditional | conditional:engine_unattested | 273 |
| grille | conditional | conditional:trim | 916 |
| headlights | unmapped | - | 708 |
| headlights | no_records | - | 1427 |
| headlights | split | option_split | 5858 |
| headlights | split | position_missing | 1 |
| headlights | conditional | conditional:engine_unattested | 3 |
| headlights | conditional | conditional:option | 210 |
| headlights | conditional | conditional:trim | 986 |
| hood | unmapped | - | 708 |
| hood | no_records | - | 715 |
| hood | split | option_split | 1859 |
| hood | conditional | conditional:body | 43 |
| hood | conditional | conditional:engine | 11 |
| hood | conditional | conditional:engine_unattested | 1269 |
| hood | conditional | conditional:trim | 4588 |
| ignition-coils | unmapped | - | 708 |
| ignition-coils | no_records | - | 285 |
| ignition-coils | split | option_split | 5176 |
| ignition-coils | conditional | conditional:engine | 241 |
| ignition-coils | conditional | conditional:engine_unattested | 1147 |
| ignition-coils | conditional | conditional:trim | 1636 |
| liftgate | unmapped | - | 708 |
| liftgate | no_records | - | 4255 |
| liftgate | split | no_candidates | 8 |
| liftgate | split | option_split | 595 |
| liftgate | conditional | conditional:body | 260 |
| liftgate | conditional | conditional:engine_unattested | 666 |
| liftgate | conditional | conditional:production | 51 |
| liftgate | conditional | conditional:trim | 2650 |
| power-steering-pump | unmapped | - | 708 |
| power-steering-pump | no_records | - | 3830 |
| power-steering-pump | split | no_candidates | 52 |
| power-steering-pump | split | option_split | 3063 |
| power-steering-pump | conditional | conditional:engine | 157 |
| power-steering-pump | conditional | conditional:engine_unattested | 270 |
| power-steering-pump | conditional | conditional:trim | 1113 |
| radiator | unmapped | - | 708 |
| radiator | no_records | - | 231 |
| radiator | split | option_split | 6464 |
| radiator | conditional | conditional:body | 43 |
| radiator | conditional | conditional:colour | 15 |
| radiator | conditional | conditional:engine | 127 |
| radiator | conditional | conditional:engine_unattested | 850 |
| radiator | conditional | conditional:production | 7 |
| radiator | conditional | conditional:trans | 5 |
| radiator | conditional | conditional:trim | 743 |
| side-mirrors | unmapped | - | 708 |
| side-mirrors | no_records | - | 2847 |
| side-mirrors | split | option_split | 4871 |
| side-mirrors | split | slot_missing | 3 |
| side-mirrors | conditional | conditional:body | 44 |
| side-mirrors | conditional | conditional:engine_unattested | 27 |
| side-mirrors | conditional | conditional:trim | 693 |
| starter | unmapped | - | 708 |
| starter | no_records | - | 396 |
| starter | split | option_split | 6525 |
| starter | conditional | conditional:engine | 100 |
| starter | conditional | conditional:engine_unattested | 468 |
| starter | conditional | conditional:trans | 4 |
| starter | conditional | conditional:trim | 992 |
| tail-lights | unmapped | - | 708 |
| tail-lights | no_records | - | 970 |
| tail-lights | split | option_split | 4741 |
| tail-lights | split | slot_missing | 3 |
| tail-lights | conditional | conditional:body | 269 |
| tail-lights | conditional | conditional:engine_unattested | 498 |
| tail-lights | conditional | conditional:model_other | 7 |
| tail-lights | conditional | conditional:production | 5 |
| tail-lights | conditional | conditional:trim | 1992 |
| throttle-body | unmapped | - | 708 |
| throttle-body | no_records | - | 592 |
| throttle-body | split | option_split | 5842 |
| throttle-body | conditional | conditional:engine | 11 |
| throttle-body | conditional | conditional:engine_unattested | 1159 |
| throttle-body | conditional | conditional:trim | 881 |
| trunk-lid | unmapped | - | 708 |
| trunk-lid | no_records | - | 2354 |
| trunk-lid | split | no_candidates | 8 |
| trunk-lid | split | option_split | 1398 |
| trunk-lid | conditional | conditional:body | 304 |
| trunk-lid | conditional | conditional:engine_unattested | 356 |
| trunk-lid | conditional | conditional:trim | 4065 |
| window-regulator | unmapped | - | 708 |
| window-regulator | no_records | - | 740 |
| window-regulator | split | no_candidates | 12 |
| window-regulator | split | packaging_unstated | 7733 |
| window-switch | unmapped | - | 708 |
| window-switch | no_records | - | 867 |
| window-switch | split | no_candidates | 79 |
| window-switch | split | option_split | 6668 |
| window-switch | split | position_missing | 330 |
| window-switch | conditional | conditional:body | 115 |
| window-switch | conditional | conditional:engine_unattested | 292 |
| window-switch | conditional | conditional:model_other | 45 |
| window-switch | conditional | conditional:production | 21 |
| window-switch | conditional | conditional:trim | 68 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- disputed_class: 58
- evidence_mismatch: 6
- held_exterior_cross_model: 15
- rule_drift: 2
- systemic_evidence_failure: 2
- universal_part_suspect: 6

## Unknown note clauses (top 30)

- `Remanufactured`: 63
- `Valeo`: 54
- `Bosch`: 48
- `With Heated Seats`: 42
- `Without Heated Seats`: 39
- `With Directional Beam`: 34
- `Without Directional Beam`: 32
- `With Xenon Headlamps`: 30
- `Without GLI`: 28
- `All`: 27
- `With Park Sensor`: 27
- `With Park Sensors`: 27
- `Without R`: 24
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
- Volkswagen Golf R: feed 'Golf R' 0 cars
- Volkswagen Golf SportWagen: feed 'Golf SportWagen' 0 cars
- Volkswagen ID. Buzz: feed 'ID. Buzz' 0 cars
- Volkswagen ID.4: feed 'ID.4' 0 cars
- Volkswagen Quantum: feed 'Quantum' 0 cars
- Volkswagen R32: feed 'R32' 0 cars
- Volkswagen Rabbit: feed 'Rabbit' 131 cars
- Volkswagen Taos: feed 'Taos' 5 cars
- Volkswagen Tiguan Limited: feed 'Tiguan Limited' 0 cars
- Volkswagen e-Golf: feed 'e-Golf' 0 cars
