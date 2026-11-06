# OEM curation report: mb

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-05T22:14:32Z.

- records 1658, classes 1658, list rows 16468, year manifests 75, cells 7085
- Verified groups 0, engine vg groups 0, Likely groups 22
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.mbpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 3066 |
| ac-compressor | no_records | - | 57 |
| ac-compressor | not_closed | no_list_manifest | 171 |
| ac-compressor | not_closed | no_year_manifest | 1444 |
| alternator | unmapped | - | 3066 |
| alternator | no_records | - | 64 |
| alternator | not_closed | no_list_manifest | 171 |
| alternator | not_closed | no_year_manifest | 1437 |
| bumper-front | unmapped | - | 3066 |
| bumper-front | no_records | - | 231 |
| bumper-front | not_closed | no_year_manifest | 1270 |
| bumper-front | not_closed | unread_sibling_page | 171 |
| bumper-rear | unmapped | - | 3066 |
| bumper-rear | no_records | - | 133 |
| bumper-rear | not_closed | no_year_manifest | 1368 |
| bumper-rear | not_closed | unread_sibling_page | 171 |
| fender | unmapped | - | 3066 |
| fender | no_records | - | 54 |
| fender | not_closed | no_year_manifest | 1447 |
| fender | not_closed | uncrawled_chain_member | 10 |
| fender | not_closed | unread_sibling_page | 146 |
| fender | conditional | conditional:engine_unattested | 15 |
| gauge-cluster | unmapped | - | 3066 |
| gauge-cluster | no_records | - | 286 |
| gauge-cluster | not_closed | no_year_manifest | 1219 |
| gauge-cluster | not_closed | unread_sibling_page | 167 |
| grille | unmapped | - | 3066 |
| grille | no_records | - | 179 |
| grille | not_closed | no_year_manifest | 1322 |
| grille | not_closed | uncrawled_chain_member | 124 |
| grille | split | option_split | 43 |
| grille | conditional | conditional:engine_unattested | 2 |
| grille | conditional | conditional:trim | 2 |
| headlights | unmapped | - | 3066 |
| headlights | no_records | - | 130 |
| headlights | not_closed | no_list_manifest | 171 |
| headlights | not_closed | no_year_manifest | 1371 |
| hood | unmapped | - | 3066 |
| hood | no_records | - | 81 |
| hood | not_closed | no_year_manifest | 1420 |
| hood | not_closed | uncrawled_chain_member | 145 |
| hood | not_closed | unread_sibling_page | 7 |
| hood | conditional | conditional:engine_unattested | 19 |
| ignition-coils | unmapped | - | 3066 |
| ignition-coils | no_records | - | 61 |
| ignition-coils | not_closed | no_year_manifest | 1440 |
| ignition-coils | not_closed | unread_sibling_page | 167 |
| ignition-coils | not_closed | unverified_product | 4 |
| liftgate | unmapped | - | 3066 |
| liftgate | no_records | - | 1016 |
| liftgate | not_closed | no_year_manifest | 595 |
| liftgate | not_closed | unread_sibling_page | 61 |
| power-steering-pump | unmapped | - | 3066 |
| power-steering-pump | no_records | - | 102 |
| power-steering-pump | not_closed | no_list_manifest | 153 |
| power-steering-pump | not_closed | no_year_manifest | 1417 |
| radiator | unmapped | - | 3066 |
| radiator | no_records | - | 71 |
| radiator | not_closed | no_year_manifest | 1430 |
| radiator | not_closed | uncrawled_chain_member | 6 |
| radiator | not_closed | unread_sibling_page | 165 |
| starter | unmapped | - | 3066 |
| starter | no_records | - | 44 |
| starter | not_closed | no_list_manifest | 168 |
| starter | not_closed | no_year_manifest | 1460 |
| tail-lights | unmapped | - | 3066 |
| tail-lights | no_records | - | 380 |
| tail-lights | not_closed | no_list_manifest | 150 |
| tail-lights | not_closed | no_year_manifest | 1142 |
| throttle-body | unmapped | - | 3066 |
| throttle-body | no_records | - | 429 |
| throttle-body | not_closed | no_list_manifest | 157 |
| throttle-body | not_closed | no_year_manifest | 1086 |
| trunk-lid | unmapped | - | 3066 |
| trunk-lid | no_records | - | 612 |
| trunk-lid | not_closed | no_year_manifest | 929 |
| trunk-lid | not_closed | unread_sibling_page | 131 |
| window-regulator | unmapped | - | 3066 |
| window-regulator | no_records | - | 117 |
| window-regulator | not_closed | no_list_manifest | 147 |
| window-regulator | not_closed | no_year_manifest | 1408 |
| window-switch | unmapped | - | 3066 |
| window-switch | no_records | - | 573 |
| window-switch | not_closed | no_list_manifest | 103 |
| window-switch | not_closed | no_year_manifest | 996 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 3066 |
| ac-compressor | no_records | - | 57 |
| ac-compressor | split | option_split | 384 |
| ac-compressor | conditional | conditional:engine | 5 |
| ac-compressor | conditional | conditional:engine_unattested | 488 |
| ac-compressor | conditional | conditional:model_other | 22 |
| ac-compressor | conditional | conditional:qualifier | 171 |
| ac-compressor | conditional | conditional:trim | 545 |
| alternator | unmapped | - | 3066 |
| alternator | no_records | - | 64 |
| alternator | split | option_split | 647 |
| alternator | conditional | conditional:engine | 5 |
| alternator | conditional | conditional:engine_unattested | 575 |
| alternator | conditional | conditional:qualifier | 22 |
| alternator | conditional | conditional:trim | 359 |
| bumper-front | unmapped | - | 3066 |
| bumper-front | no_records | - | 231 |
| bumper-front | split | option_split | 1360 |
| bumper-front | conditional | conditional:engine_unattested | 14 |
| bumper-front | conditional | conditional:qualifier | 56 |
| bumper-front | conditional | conditional:trim | 11 |
| bumper-rear | unmapped | - | 3066 |
| bumper-rear | no_records | - | 133 |
| bumper-rear | split | no_candidates | 9 |
| bumper-rear | split | option_split | 1412 |
| bumper-rear | conditional | conditional:engine | 18 |
| bumper-rear | conditional | conditional:engine_unattested | 8 |
| bumper-rear | conditional | conditional:qualifier | 92 |
| fender | unmapped | - | 3066 |
| fender | no_records | - | 54 |
| fender | split | option_split | 171 |
| fender | split | slot_missing | 1 |
| fender | conditional | conditional:body | 3 |
| fender | conditional | conditional:engine_unattested | 1172 |
| fender | conditional | conditional:model_other | 9 |
| fender | conditional | conditional:trim | 262 |
| gauge-cluster | unmapped | - | 3066 |
| gauge-cluster | no_records | - | 286 |
| gauge-cluster | split | no_candidates | 21 |
| gauge-cluster | split | option_split | 741 |
| gauge-cluster | conditional | conditional:body | 11 |
| gauge-cluster | conditional | conditional:engine_unattested | 235 |
| gauge-cluster | conditional | conditional:qualifier | 109 |
| gauge-cluster | conditional | conditional:trim | 269 |
| grille | unmapped | - | 3066 |
| grille | no_records | - | 179 |
| grille | split | option_split | 1211 |
| grille | conditional | conditional:colour | 10 |
| grille | conditional | conditional:engine_unattested | 212 |
| grille | conditional | conditional:trim | 60 |
| headlights | unmapped | - | 3066 |
| headlights | no_records | - | 130 |
| headlights | split | option_split | 1464 |
| headlights | split | position_missing | 1 |
| headlights | split | slot_missing | 1 |
| headlights | conditional | conditional:engine_unattested | 49 |
| headlights | conditional | conditional:trim | 27 |
| hood | unmapped | - | 3066 |
| hood | no_records | - | 81 |
| hood | split | option_split | 150 |
| hood | conditional | conditional:body | 3 |
| hood | conditional | conditional:engine_unattested | 920 |
| hood | conditional | conditional:trim | 518 |
| ignition-coils | unmapped | - | 3066 |
| ignition-coils | no_records | - | 61 |
| ignition-coils | split | option_split | 160 |
| ignition-coils | conditional | conditional:body | 3 |
| ignition-coils | conditional | conditional:engine | 95 |
| ignition-coils | conditional | conditional:engine_unattested | 928 |
| ignition-coils | conditional | conditional:model_other | 16 |
| ignition-coils | conditional | conditional:trim | 409 |
| liftgate | unmapped | - | 3066 |
| liftgate | no_records | - | 1016 |
| liftgate | split | option_split | 149 |
| liftgate | conditional | conditional:body | 12 |
| liftgate | conditional | conditional:engine_unattested | 174 |
| liftgate | conditional | conditional:trim | 321 |
| power-steering-pump | unmapped | - | 3066 |
| power-steering-pump | no_records | - | 102 |
| power-steering-pump | split | option_split | 1053 |
| power-steering-pump | conditional | conditional:engine | 10 |
| power-steering-pump | conditional | conditional:engine_unattested | 323 |
| power-steering-pump | conditional | conditional:qualifier | 10 |
| power-steering-pump | conditional | conditional:trim | 174 |
| radiator | unmapped | - | 3066 |
| radiator | no_records | - | 71 |
| radiator | split | option_split | 583 |
| radiator | conditional | conditional:body | 5 |
| radiator | conditional | conditional:engine | 80 |
| radiator | conditional | conditional:engine_unattested | 673 |
| radiator | conditional | conditional:fuel | 3 |
| radiator | conditional | conditional:model_other | 6 |
| radiator | conditional | conditional:production | 10 |
| radiator | conditional | conditional:trim | 241 |
| starter | unmapped | - | 3066 |
| starter | no_records | - | 44 |
| starter | split | option_split | 643 |
| starter | conditional | conditional:engine | 5 |
| starter | conditional | conditional:engine_unattested | 468 |
| starter | conditional | conditional:trim | 512 |
| tail-lights | unmapped | - | 3066 |
| tail-lights | no_records | - | 380 |
| tail-lights | split | option_split | 869 |
| tail-lights | split | slot_missing | 7 |
| tail-lights | conditional | conditional:engine_unattested | 265 |
| tail-lights | conditional | conditional:trim | 151 |
| throttle-body | unmapped | - | 3066 |
| throttle-body | no_records | - | 429 |
| throttle-body | split | option_split | 85 |
| throttle-body | conditional | conditional:engine_unattested | 637 |
| throttle-body | conditional | conditional:trim | 521 |
| trunk-lid | unmapped | - | 3066 |
| trunk-lid | no_records | - | 612 |
| trunk-lid | split | no_candidates | 16 |
| trunk-lid | split | option_split | 252 |
| trunk-lid | conditional | conditional:body | 12 |
| trunk-lid | conditional | conditional:engine_unattested | 603 |
| trunk-lid | conditional | conditional:trim | 177 |
| window-regulator | unmapped | - | 3066 |
| window-regulator | no_records | - | 117 |
| window-regulator | split | packaging_incomplete | 10 |
| window-regulator | split | packaging_split | 10 |
| window-regulator | split | packaging_unstated | 1535 |
| window-switch | unmapped | - | 3066 |
| window-switch | no_records | - | 573 |
| window-switch | split | option_split | 671 |
| window-switch | split | position_missing | 421 |
| window-switch | conditional | conditional:model_other | 7 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- evidence_mismatch: 2
- systemic_evidence_failure: 1
- universal_part_suspect: 14

## Unknown note clauses (top 30)

- `Without Lamp Wash`: 59
- `With Lamp Washer`: 52
- `Sedan/Wagon`: 44
- `With Parktronic`: 43
- `With Park Sensor`: 34
- `Without AMG`: 28
- `Without Park Sensor`: 28
- `Classic`: 27
- `With AMG`: 25
- `Avantgarde`: 23
- `Elegance`: 23
- `Without Parktronic`: 23
- `Without Proximity Cruise`: 23
- `With Lamp Wash`: 21
- `Without Parktrnic`: 16
- `All`: 15
- `With Proximity Cruise`: 15
- `With Park Sensors`: 12
- `Without C63`: 12
- `Without Lamp Washer`: 12
- `Without Park Sensors`: 12
- `With Parking Sensor`: 11
- `Without Parking Sensor`: 11
- `With Bi-Xenon`: 10
- `With Hitch`: 10
- `Without Adaptive Cruise`: 10
- `Without E63 AMG`: 10
- `Without Hitch`: 10
- `Without Park Sens`: 10
- `Without Reverse Sensor`: 10

## Unmapped catalog models

- Mercedes-Benz 300CD: feed '300CD' 0 cars
- Mercedes-Benz 300SDL: feed '300SDL' 0 cars
- Mercedes-Benz 300TE: feed '300TE' 0 cars
- Mercedes-Benz 350SD: feed '350SD' 0 cars
- Mercedes-Benz 350SDL: feed '350SDL' 0 cars
- Mercedes-Benz 380SE: feed '380SE' 0 cars
- Mercedes-Benz 400E: feed '400E' 0 cars
- Mercedes-Benz 400SEL: feed '400SEL' 0 cars
- Mercedes-Benz 500E: feed '500E' 0 cars
- Mercedes-Benz 500SEC: feed '500SEC' 0 cars
- Mercedes-Benz 500SEL: feed '500SEL' 0 cars
- Mercedes-Benz 600SEC: feed '600SEC' 0 cars
- Mercedes-Benz 600SEL: feed '600SEL' 0 cars
- Mercedes-Benz 600SL: feed '600SL' 0 cars
- Mercedes-Benz AMG GT: feed 'AMG GT' 0 cars
- Mercedes-Benz AMG GT 55: feed 'AMG GT 55' 0 cars
- Mercedes-Benz AMG GT 63: feed 'AMG GT 63' 0 cars
- Mercedes-Benz AMG GT 63 S: feed 'AMG GT 63 S' 0 cars
- Mercedes-Benz AMG GT Black Series: feed 'AMG GT Black Series' 0 cars
- Mercedes-Benz AMG GT C: feed 'AMG GT C' 0 cars
- Mercedes-Benz AMG GT R: feed 'AMG GT R' 0 cars
- Mercedes-Benz AMG GT R Pro: feed 'AMG GT R Pro' 0 cars
- Mercedes-Benz AMG GT S: feed 'AMG GT S' 0 cars
- Mercedes-Benz B Electric Drive: feed 'B Electric Drive' 0 cars
- Mercedes-Benz B250e: feed 'B250e' 0 cars
- Mercedes-Benz C32 AMG: feed 'C32 AMG' 0 cars
- Mercedes-Benz C350e: feed 'C350e' 0 cars
- Mercedes-Benz C400: feed 'C400' 0 cars
- Mercedes-Benz C450 AMG: feed 'C450 AMG' 0 cars
- Mercedes-Benz C55 AMG: feed 'C55 AMG' 0 cars
- Mercedes-Benz C63 AMG: feed 'C63 AMG' 0 cars
- Mercedes-Benz C63 AMG S: feed 'C63 AMG S' 0 cars
- Mercedes-Benz C63 AMG S E Performance: feed 'C63 AMG S E Performance' 0 cars
- Mercedes-Benz CL63 AMG: feed 'CL63 AMG' 0 cars
- Mercedes-Benz CL65 AMG: feed 'CL65 AMG' 0 cars
- Mercedes-Benz CLA45 AMG: feed 'CLA45 AMG' 0 cars
- Mercedes-Benz CLA45 AMG S: feed 'CLA45 AMG S' 0 cars
- Mercedes-Benz CLK63 AMG: feed 'CLK63 AMG' 0 cars
- Mercedes-Benz CLS400: feed 'CLS400' 0 cars
- Mercedes-Benz CLS55 AMG: feed 'CLS55 AMG' 0 cars
- Mercedes-Benz CLS63 AMG: feed 'CLS63 AMG' 0 cars
- Mercedes-Benz CLS63 AMG S: feed 'CLS63 AMG S' 0 cars
- Mercedes-Benz E250: feed 'E250' 0 cars
- Mercedes-Benz E400: feed 'E400' 0 cars
- Mercedes-Benz E43 AMG: feed 'E43 AMG' 0 cars
- Mercedes-Benz E450: feed 'E450' 0 cars
- Mercedes-Benz E53 AMG: feed 'E53 AMG' 0 cars
- Mercedes-Benz E63 AMG: feed 'E63 AMG' 0 cars
- Mercedes-Benz E63 AMG S: feed 'E63 AMG S' 0 cars
- Mercedes-Benz G500: feed 'G500' 0 cars
- Mercedes-Benz G55 AMG: feed 'G55 AMG' 0 cars
- Mercedes-Benz G550: feed 'G550' 0 cars
- Mercedes-Benz G63 AMG: feed 'G63 AMG' 0 cars
- Mercedes-Benz G65 AMG: feed 'G65 AMG' 0 cars
- Mercedes-Benz GL63 AMG: feed 'GL63 AMG' 0 cars
- Mercedes-Benz GLA45 AMG: feed 'GLA45 AMG' 0 cars
- Mercedes-Benz GLC300: feed 'GLC300' 0 cars
- Mercedes-Benz GLC350e: feed 'GLC350e' 0 cars
- Mercedes-Benz GLC43 AMG: feed 'GLC43 AMG' 0 cars
- Mercedes-Benz GLC63 AMG: feed 'GLC63 AMG' 0 cars
