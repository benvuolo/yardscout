# OEM curation report: gm

Raw: `ceccc800d7ba22c0291121baabb0a9292eb8f271` @ `ceccc800d7ba`; as of 2026-11-05T22:22:36Z.

- records 2902, classes 2902, list rows 16746, year manifests 30, cells 11697
- Verified groups 0, engine vg groups 0, Likely groups 930
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.gmpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.gmpartsgiant.com: only 0% of its 9152 fitment rows can be coverage: its option column holds trims (option_column_is_trims), which count only after a namespace audit (spec 5.2)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 15150 |
| ac-compressor | no_records | - | 6698 |
| ac-compressor | not_closed | ambig_target | 6421 |
| ac-compressor | not_closed | no_year_manifest | 49665 |
| ac-compressor | not_closed | uncrawled_chain_member | 381 |
| ac-compressor | not_closed | unverified_product | 471 |
| alternator | unmapped | - | 15150 |
| alternator | no_records | - | 7668 |
| alternator | not_closed | ambig_target | 6165 |
| alternator | not_closed | no_year_manifest | 48951 |
| alternator | not_closed | unread_sibling_page | 852 |
| climate-control | unmapped | - | 15150 |
| climate-control | no_records | - | 18608 |
| climate-control | not_closed | ambig_target | 6567 |
| climate-control | not_closed | no_year_manifest | 37704 |
| climate-control | not_closed | unread_sibling_page | 757 |
| fuel-pump-module | unmapped | - | 15150 |
| fuel-pump-module | no_records | - | 10075 |
| fuel-pump-module | not_closed | ambig_target | 6455 |
| fuel-pump-module | not_closed | no_year_manifest | 46254 |
| fuel-pump-module | not_closed | unread_sibling_page | 852 |
| headlights | unmapped | - | 15150 |
| headlights | no_records | - | 13296 |
| headlights | not_closed | ambig_target | 6127 |
| headlights | not_closed | no_year_manifest | 43361 |
| headlights | not_closed | unattested | 99 |
| headlights | not_closed | uncrawled_chain_member | 245 |
| headlights | not_closed | unread_sibling_page | 459 |
| headlights | not_closed | unverified_product | 49 |
| power-steering-pump | unmapped | - | 15150 |
| power-steering-pump | no_records | - | 18811 |
| power-steering-pump | not_closed | ambig_target | 6744 |
| power-steering-pump | not_closed | no_year_manifest | 37324 |
| power-steering-pump | not_closed | unread_sibling_page | 757 |
| side-mirrors | unmapped | - | 15150 |
| side-mirrors | no_records | - | 5460 |
| side-mirrors | not_closed | ambig_target | 6950 |
| side-mirrors | not_closed | no_year_manifest | 50374 |
| side-mirrors | not_closed | unread_sibling_page | 852 |
| starter | unmapped | - | 15150 |
| starter | no_records | - | 3663 |
| starter | not_closed | ambig_target | 6820 |
| starter | not_closed | no_year_manifest | 52301 |
| starter | not_closed | unread_sibling_page | 852 |
| tail-lights | unmapped | - | 15150 |
| tail-lights | no_records | - | 8089 |
| tail-lights | not_closed | ambig_target | 6580 |
| tail-lights | not_closed | no_year_manifest | 48115 |
| tail-lights | not_closed | unattested | 173 |
| tail-lights | not_closed | uncrawled_chain_member | 546 |
| tail-lights | not_closed | unverified_product | 133 |
| throttle-body | unmapped | - | 15150 |
| throttle-body | no_records | - | 26364 |
| throttle-body | not_closed | ambig_target | 6234 |
| throttle-body | not_closed | no_year_manifest | 30186 |
| throttle-body | not_closed | unattested | 422 |
| throttle-body | not_closed | uncrawled_chain_member | 372 |
| throttle-body | not_closed | unverified_product | 58 |
| window-regulator | unmapped | - | 15150 |
| window-regulator | no_records | - | 2927 |
| window-regulator | not_closed | ambig_target | 6831 |
| window-regulator | not_closed | no_year_manifest | 53026 |
| window-regulator | not_closed | uncrawled_chain_member | 417 |
| window-regulator | not_closed | unread_sibling_page | 435 |
| window-switch | unmapped | - | 15150 |
| window-switch | no_records | - | 10606 |
| window-switch | not_closed | ambig_target | 6102 |
| window-switch | not_closed | no_year_manifest | 46076 |
| window-switch | not_closed | unattested | 74 |
| window-switch | not_closed | uncrawled_chain_member | 212 |
| window-switch | not_closed | unread_sibling_page | 375 |
| window-switch | not_closed | unverified_product | 191 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 15150 |
| ac-compressor | no_records | - | 6698 |
| ac-compressor | split | option_split | 34430 |
| ac-compressor | conditional | conditional:engine_unattested | 14974 |
| ac-compressor | conditional | conditional:option | 83 |
| ac-compressor | conditional | conditional:qualifier | 7451 |
| alternator | unmapped | - | 15150 |
| alternator | no_records | - | 7668 |
| alternator | split | option_split | 38154 |
| alternator | conditional | conditional:engine_unattested | 15874 |
| alternator | conditional | conditional:qualifier | 1940 |
| climate-control | unmapped | - | 15150 |
| climate-control | no_records | - | 18608 |
| climate-control | split | no_candidates | 119 |
| climate-control | split | option_split | 36048 |
| climate-control | conditional | conditional:engine_unattested | 7383 |
| climate-control | conditional | conditional:option | 1478 |
| fuel-pump-module | unmapped | - | 15150 |
| fuel-pump-module | no_records | - | 10075 |
| fuel-pump-module | split | no_candidates | 15 |
| fuel-pump-module | split | option_split | 39021 |
| fuel-pump-module | conditional | conditional:engine_unattested | 6016 |
| fuel-pump-module | conditional | conditional:qualifier | 8509 |
| headlights | unmapped | - | 15150 |
| headlights | no_records | - | 13296 |
| headlights | split | no_candidates | 99 |
| headlights | split | option_split | 23544 |
| headlights | conditional | conditional:engine_unattested | 13632 |
| headlights | conditional | conditional:option | 703 |
| headlights | conditional | conditional:qualifier | 12362 |
| power-steering-pump | unmapped | - | 15150 |
| power-steering-pump | no_records | - | 18811 |
| power-steering-pump | split | option_split | 21167 |
| power-steering-pump | conditional | conditional:engine_unattested | 17146 |
| power-steering-pump | conditional | conditional:qualifier | 6512 |
| side-mirrors | unmapped | - | 15150 |
| side-mirrors | no_records | - | 5460 |
| side-mirrors | split | option_split | 51731 |
| side-mirrors | split | position_missing | 213 |
| side-mirrors | split | slot_missing | 71 |
| side-mirrors | conditional | conditional:engine_unattested | 5168 |
| side-mirrors | conditional | conditional:option | 521 |
| side-mirrors | conditional | conditional:qualifier | 472 |
| starter | unmapped | - | 15150 |
| starter | no_records | - | 3663 |
| starter | split | no_candidates | 145 |
| starter | split | option_split | 31891 |
| starter | conditional | conditional:engine_unattested | 16181 |
| starter | conditional | conditional:option | 300 |
| starter | conditional | conditional:qualifier | 11456 |
| tail-lights | unmapped | - | 15150 |
| tail-lights | no_records | - | 8089 |
| tail-lights | split | option_split | 30313 |
| tail-lights | split | position_missing | 1019 |
| tail-lights | split | slot_missing | 405 |
| tail-lights | conditional | conditional:engine_unattested | 22869 |
| tail-lights | conditional | conditional:qualifier | 941 |
| throttle-body | unmapped | - | 15150 |
| throttle-body | no_records | - | 26364 |
| throttle-body | split | no_candidates | 422 |
| throttle-body | split | option_split | 17021 |
| throttle-body | conditional | conditional:engine_unattested | 4923 |
| throttle-body | conditional | conditional:qualifier | 14906 |
| window-regulator | unmapped | - | 15150 |
| window-regulator | no_records | - | 2927 |
| window-regulator | split | packaging_incomplete | 4311 |
| window-regulator | split | packaging_split | 15734 |
| window-regulator | split | packaging_unstated | 40272 |
| window-regulator | conditional | conditional:engine_unattested | 392 |
| window-switch | unmapped | - | 15150 |
| window-switch | no_records | - | 10606 |
| window-switch | split | no_candidates | 95 |
| window-switch | split | option_split | 35075 |
| window-switch | split | position_missing | 11385 |
| window-switch | conditional | conditional:engine_unattested | 3678 |
| window-switch | conditional | conditional:option | 51 |
| window-switch | conditional | conditional:qualifier | 2746 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 1
- universal_part_suspect: 118

## Unknown note clauses (top 30)

- `CK1`: 54
- `OUTSIDE REAR VIEW(INCLUDES 1,2,5)(PAINT TO MATCH)`: 45
- `2`: 42
- `BS`: 42
- `2(5B5)`: 40
- `2(A31)(EXC 5B5)`: 40
- `JV`: 40
- `MODULE KIT`: 40
- `SWITCH`: 37
- `GENERATOR`: 36
- `PUMP`: 25
- `HEATER & A/C`: 24
- `OUTSIDE REAR VIEW(INCLUDES 2-6,8-15)`: 24
- `AK`: 22
- `CONTROL`: 22
- `FRONT SIDE DOOR WINDOW`: 21
- `TAIL`: 21
- `OUTSIDE REAR VIEW`: 19
- `STARTER`: 19
- `REAR SIDE DOOR WINDOW`: 18
- `BODY`: 15
- `COMPRESSOR KIT`: 15
- `PUMP KIT`: 15
- `EF`: 14
- `(INCLUDES 3,4,16,17,20)`: 13
- `OUTSIDE REAR VIEW(INCLUDES 1,2,4-15)(PAINT TO MATCH)`: 13
- `OUTSIDE REAR VIEW(INCLUDES 1-3)(PAINT TO MATCH)`: 13
- `OUTSIDE REAR VIEW(INCLUDES 2,7)(PAINT TO MATCH)`: 13
- `KE`: 12
- `OUTSIDE REAR VIEW(INCLUDES 2,4-6)(PAINT TO MATCH)`: 12

## Unmapped catalog models

- Buick Somerset: feed 'Somerset' 0 cars
- Cadillac CT4: feed 'CT4' 0 cars
- Cadillac Cimarron: feed 'Cimarron' 0 cars
- Cadillac XT6: feed 'XT6' 0 cars
- Chevrolet Aveo: feed 'Aveo' 575 cars
- Chevrolet Bolt EUV: feed 'Bolt EUV' 0 cars
- Chevrolet Cadet: feed 'Cadet' 0 cars
- Chevrolet Citation: feed 'Citation' 4 cars
- Chevrolet K30: feed 'K30' 0 cars
- Chevrolet P20: feed 'P20' 0 cars
- Chevrolet R10: feed 'R10' 0 cars
- Chevrolet R20: feed 'R20' 0 cars
- Chevrolet R2500: feed 'R2500' 0 cars
- Chevrolet SS: feed 'SS' 0 cars
- Chevrolet SSR: feed 'SSR' 0 cars
- Chevrolet V10: feed 'V10' 0 cars
- Chevrolet V20: feed 'V20' 0 cars
- Chevrolet V30: feed 'V30' 0 cars
- Chevrolet V3500: feed 'V3500' 0 cars
- GMC G3500: feed 'G3500' 0 cars
- GMC P2500: feed 'P2500' 0 cars
- GMC P3500: feed 'P3500' 0 cars
- GMC R1500: feed 'R1500' 0 cars
- GMC R2500: feed 'R2500' 0 cars
- GMC R3500: feed 'R3500' 0 cars
- GMC Syclone: feed 'Syclone' 0 cars
- GMC Typhoon: feed 'Typhoon' 0 cars
- GMC V1500: feed 'V1500' 0 cars
- GMC V2500: feed 'V2500' 0 cars
- GMC V3500: feed 'V3500' 0 cars
- Hummer H3T: feed 'H3T' 0 cars
- Oldsmobile Omega: feed 'Omega' 4 cars
- Pontiac G3: feed 'G3' 24 cars
- Pontiac G8: feed 'G8' 26 cars
- Pontiac J2000: feed 'J2000' 0 cars
- Pontiac LeMans: feed 'LeMans' 5 cars
- Pontiac Phoenix: feed 'Phoenix' 2 cars
