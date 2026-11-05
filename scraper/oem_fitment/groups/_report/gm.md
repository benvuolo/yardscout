# OEM curation report: gm

Raw: `50ac4a48cdc62d02bd819bec33a67d0f07d8a71e` @ `50ac4a48cdc6`; as of 2026-11-05T12:57:33Z.

- records 2418, classes 2418, list rows 0, year manifests 0, cells 9680
- Verified groups 0, engine vg groups 0, Likely groups 842
- blocked sites: none

## Gates standing for the whole namespace

- no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close (C1/C2); Verified is impossible by design until the crawler writes them
- no (site, category) of this namespace has passed the audit gate (CATEGORY_STATUS has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.gmpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.gmpartsgiant.com: only 0% of its 7116 fitment rows can be coverage: its option column holds trims (option_column_is_trims), which count only after a namespace audit (spec 5.2)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 15153 |
| ac-compressor | no_records | - | 10641 |
| ac-compressor | not_closed | ambig_target | 6322 |
| ac-compressor | not_closed | no_year_manifest | 46753 |
| alternator | unmapped | - | 15153 |
| alternator | no_records | - | 11005 |
| alternator | not_closed | ambig_target | 6010 |
| alternator | not_closed | no_year_manifest | 46701 |
| climate-control | unmapped | - | 15153 |
| climate-control | no_records | - | 20906 |
| climate-control | not_closed | ambig_target | 6323 |
| climate-control | not_closed | no_year_manifest | 36487 |
| fuel-pump-module | unmapped | - | 15153 |
| fuel-pump-module | no_records | - | 11832 |
| fuel-pump-module | not_closed | ambig_target | 6037 |
| fuel-pump-module | not_closed | no_year_manifest | 45847 |
| headlights | unmapped | - | 15153 |
| headlights | no_records | - | 15731 |
| headlights | not_closed | ambig_target | 6133 |
| headlights | not_closed | no_year_manifest | 41852 |
| power-steering-pump | unmapped | - | 15153 |
| power-steering-pump | no_records | - | 20979 |
| power-steering-pump | not_closed | ambig_target | 6747 |
| power-steering-pump | not_closed | no_year_manifest | 35990 |
| side-mirrors | unmapped | - | 15153 |
| side-mirrors | no_records | - | 8206 |
| side-mirrors | not_closed | ambig_target | 6734 |
| side-mirrors | not_closed | no_year_manifest | 48776 |
| starter | unmapped | - | 15153 |
| starter | no_records | - | 5835 |
| starter | not_closed | ambig_target | 6697 |
| starter | not_closed | no_year_manifest | 51184 |
| tail-lights | unmapped | - | 15153 |
| tail-lights | no_records | - | 10601 |
| tail-lights | not_closed | ambig_target | 6350 |
| tail-lights | not_closed | no_year_manifest | 46765 |
| throttle-body | unmapped | - | 15153 |
| throttle-body | no_records | - | 33977 |
| throttle-body | not_closed | ambig_target | 6234 |
| throttle-body | not_closed | no_year_manifest | 23505 |
| window-regulator | unmapped | - | 15153 |
| window-regulator | no_records | - | 4059 |
| window-regulator | not_closed | ambig_target | 6822 |
| window-regulator | not_closed | no_year_manifest | 52835 |
| window-switch | unmapped | - | 15153 |
| window-switch | no_records | - | 12784 |
| window-switch | not_closed | ambig_target | 5727 |
| window-switch | not_closed | no_year_manifest | 45205 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 15153 |
| ac-compressor | no_records | - | 10641 |
| ac-compressor | split | option_split | 32378 |
| ac-compressor | conditional | conditional:notes_not_own_page | 18107 |
| ac-compressor | conditional | conditional:option | 83 |
| ac-compressor | conditional | conditional:option_layout | 2507 |
| alternator | unmapped | - | 15153 |
| alternator | no_records | - | 11005 |
| alternator | split | option_split | 35699 |
| alternator | conditional | conditional:notes_not_own_page | 15053 |
| alternator | conditional | conditional:option_layout | 1959 |
| climate-control | unmapped | - | 15153 |
| climate-control | no_records | - | 20906 |
| climate-control | split | option_split | 34735 |
| climate-control | conditional | conditional:notes_not_own_page | 6587 |
| climate-control | conditional | conditional:option | 1488 |
| fuel-pump-module | unmapped | - | 15153 |
| fuel-pump-module | no_records | - | 11832 |
| fuel-pump-module | split | option_split | 37030 |
| fuel-pump-module | conditional | conditional:notes_not_own_page | 12663 |
| fuel-pump-module | conditional | conditional:option_layout | 2191 |
| headlights | unmapped | - | 15153 |
| headlights | no_records | - | 15731 |
| headlights | split | option_split | 21869 |
| headlights | conditional | conditional:notes_not_own_page | 19403 |
| headlights | conditional | conditional:option | 621 |
| headlights | conditional | conditional:option_layout | 6092 |
| power-steering-pump | unmapped | - | 15153 |
| power-steering-pump | no_records | - | 20979 |
| power-steering-pump | split | option_split | 17678 |
| power-steering-pump | conditional | conditional:notes_not_own_page | 21327 |
| power-steering-pump | conditional | conditional:option_layout | 3732 |
| side-mirrors | unmapped | - | 15153 |
| side-mirrors | no_records | - | 8206 |
| side-mirrors | split | option_split | 48938 |
| side-mirrors | split | position_missing | 280 |
| side-mirrors | split | slot_missing | 16 |
| side-mirrors | conditional | conditional:notes_not_own_page | 5351 |
| side-mirrors | conditional | conditional:option | 524 |
| side-mirrors | conditional | conditional:option_layout | 401 |
| starter | unmapped | - | 15153 |
| starter | no_records | - | 5835 |
| starter | split | option_split | 28167 |
| starter | conditional | conditional:notes_not_own_page | 27098 |
| starter | conditional | conditional:option | 306 |
| starter | conditional | conditional:option_layout | 2310 |
| tail-lights | unmapped | - | 15153 |
| tail-lights | no_records | - | 10601 |
| tail-lights | split | option_split | 29348 |
| tail-lights | split | position_missing | 1022 |
| tail-lights | split | slot_missing | 403 |
| tail-lights | conditional | conditional:notes_not_own_page | 17255 |
| tail-lights | conditional | conditional:option_layout | 5087 |
| throttle-body | unmapped | - | 15153 |
| throttle-body | no_records | - | 33977 |
| throttle-body | split | option_split | 15724 |
| throttle-body | conditional | conditional:notes_not_own_page | 12734 |
| throttle-body | conditional | conditional:option_layout | 1281 |
| window-regulator | unmapped | - | 15153 |
| window-regulator | no_records | - | 4059 |
| window-regulator | split | packaging_incomplete | 5428 |
| window-regulator | split | packaging_split | 12956 |
| window-regulator | split | packaging_unstated | 38609 |
| window-regulator | conditional | conditional:notes_not_own_page | 2312 |
| window-regulator | conditional | conditional:option_layout | 352 |
| window-switch | unmapped | - | 15153 |
| window-switch | no_records | - | 12784 |
| window-switch | split | option_split | 33913 |
| window-switch | split | position_missing | 10841 |
| window-switch | conditional | conditional:notes_not_own_page | 5004 |
| window-switch | conditional | conditional:option_layout | 1174 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- universal_part_suspect: 81

## Unknown note clauses (top 30)

- `OUTSIDE REAR VIEW(INCLUDES 1,2,5)(PAINT TO MATCH)`: 45
- `2`: 42
- `BS`: 42
- `MODULE KIT`: 40
- `SWITCH`: 37
- `GENERATOR`: 36
- `JV`: 25
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
- `(INCLUDES 3,4,16,17,20)`: 13
- `OUTSIDE REAR VIEW(INCLUDES 1,2,4-15)(PAINT TO MATCH)`: 13
- `OUTSIDE REAR VIEW(INCLUDES 1-3)(PAINT TO MATCH)`: 13
- `OUTSIDE REAR VIEW(INCLUDES 2,7)(PAINT TO MATCH)`: 13
- `KE`: 12
- `OUTSIDE REAR VIEW(INCLUDES 2,4-6)(PAINT TO MATCH)`: 12
- `CK1`: 10
- `FRONT SIDE DOOR WINDOW REGULATOR`: 10
- `FRONT SIDE DOOR WINDOW REGULATOR(PART OF 4)`: 10
- `ZC`: 10

## Unmapped catalog models

- Buick Somerset: feed 'Somerset' 0 cars
- Cadillac CT4: feed 'CT4' 0 cars
- Cadillac Cimarron: feed 'Cimarron' 0 cars
- Cadillac XT6: feed 'XT6' 0 cars
- Chevrolet Bolt EUV: feed 'Bolt EUV' 0 cars
- Chevrolet Cadet: feed 'Cadet' 0 cars
- Chevrolet K30: feed 'K30' 0 cars
- Chevrolet P20: feed 'P20' 0 cars
- Chevrolet R10: feed 'R10' 0 cars
- Chevrolet R20: feed 'R20' 0 cars
- Chevrolet R2500: feed 'R2500' 0 cars
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
- Pontiac J2000: feed 'J2000' 0 cars
