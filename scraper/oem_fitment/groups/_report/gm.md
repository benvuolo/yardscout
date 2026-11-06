# OEM curation report: gm

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-06T07:20:17Z.

- records 3633, classes 3633, list rows 95531, year manifests 152, cells 13611
- Verified groups 0, engine vg groups 0, Likely groups 357
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.gmpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.gmpartsgiant.com: only 0% of its 11390 fitment rows can be coverage: its option column holds trims (option_column_is_trims), which count only after a namespace audit (spec 5.2)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 15201 |
| ac-compressor | no_records | - | 5340 |
| ac-compressor | not_closed | ambig_target | 6608 |
| ac-compressor | not_closed | no_year_manifest | 49895 |
| ac-compressor | not_closed | unattested | 33 |
| ac-compressor | not_closed | uncrawled_chain_member | 780 |
| ac-compressor | not_closed | unverified_product | 1003 |
| ac-compressor | not_closed | year_manifest_bad | 6 |
| alternator | unmapped | - | 15201 |
| alternator | no_records | - | 5461 |
| alternator | not_closed | ambig_target | 6317 |
| alternator | not_closed | no_year_manifest | 50106 |
| alternator | not_closed | unread_sibling_page | 1775 |
| alternator | not_closed | year_manifest_bad | 6 |
| climate-control | unmapped | - | 15201 |
| climate-control | no_records | - | 17176 |
| climate-control | not_closed | ambig_target | 6944 |
| climate-control | not_closed | no_year_manifest | 38014 |
| climate-control | not_closed | unread_sibling_page | 1531 |
| fuel-pump-module | unmapped | - | 15201 |
| fuel-pump-module | no_records | - | 7611 |
| fuel-pump-module | not_closed | ambig_target | 6490 |
| fuel-pump-module | not_closed | no_list_manifest | 1 |
| fuel-pump-module | not_closed | no_year_manifest | 47748 |
| fuel-pump-module | not_closed | unread_sibling_page | 1815 |
| headlights | unmapped | - | 15201 |
| headlights | no_records | - | 11153 |
| headlights | not_closed | ambig_target | 6568 |
| headlights | not_closed | no_year_manifest | 44122 |
| headlights | not_closed | unattested | 284 |
| headlights | not_closed | uncrawled_chain_member | 680 |
| headlights | not_closed | unread_sibling_page | 802 |
| headlights | not_closed | unverified_product | 50 |
| headlights | not_closed | year_manifest_bad | 6 |
| power-steering-pump | unmapped | - | 15201 |
| power-steering-pump | no_records | - | 18027 |
| power-steering-pump | not_closed | ambig_target | 6891 |
| power-steering-pump | not_closed | no_year_manifest | 37277 |
| power-steering-pump | not_closed | unread_sibling_page | 1464 |
| power-steering-pump | not_closed | year_manifest_bad | 6 |
| side-mirrors | unmapped | - | 15201 |
| side-mirrors | no_records | - | 3914 |
| side-mirrors | not_closed | ambig_target | 6991 |
| side-mirrors | not_closed | no_year_manifest | 50938 |
| side-mirrors | not_closed | unread_sibling_page | 1816 |
| side-mirrors | not_closed | year_manifest_bad | 6 |
| starter | unmapped | - | 15201 |
| starter | no_records | - | 2990 |
| starter | not_closed | ambig_target | 6991 |
| starter | not_closed | no_year_manifest | 51863 |
| starter | not_closed | unread_sibling_page | 1815 |
| starter | not_closed | year_manifest_bad | 6 |
| tail-lights | unmapped | - | 15201 |
| tail-lights | no_records | - | 6480 |
| tail-lights | not_closed | ambig_target | 6855 |
| tail-lights | not_closed | no_year_manifest | 48508 |
| tail-lights | not_closed | unattested | 377 |
| tail-lights | not_closed | uncrawled_chain_member | 1291 |
| tail-lights | not_closed | unverified_product | 148 |
| tail-lights | not_closed | year_manifest_bad | 6 |
| throttle-body | unmapped | - | 15201 |
| throttle-body | no_records | - | 24356 |
| throttle-body | not_closed | ambig_target | 6405 |
| throttle-body | not_closed | no_year_manifest | 31084 |
| throttle-body | not_closed | unattested | 1015 |
| throttle-body | not_closed | uncrawled_chain_member | 524 |
| throttle-body | not_closed | unverified_product | 275 |
| throttle-body | not_closed | year_manifest_bad | 6 |
| window-regulator | unmapped | - | 15201 |
| window-regulator | no_records | - | 2382 |
| window-regulator | not_closed | ambig_target | 6841 |
| window-regulator | not_closed | no_year_manifest | 52628 |
| window-regulator | not_closed | unattested | 33 |
| window-regulator | not_closed | uncrawled_chain_member | 645 |
| window-regulator | not_closed | unread_sibling_page | 950 |
| window-regulator | not_closed | unverified_product | 180 |
| window-regulator | not_closed | year_manifest_bad | 6 |
| window-switch | unmapped | - | 15201 |
| window-switch | no_records | - | 8554 |
| window-switch | not_closed | ambig_target | 6846 |
| window-switch | not_closed | no_year_manifest | 46451 |
| window-switch | not_closed | unattested | 137 |
| window-switch | not_closed | uncrawled_chain_member | 631 |
| window-switch | not_closed | unread_sibling_page | 732 |
| window-switch | not_closed | unverified_product | 308 |
| window-switch | not_closed | year_manifest_bad | 6 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 15201 |
| ac-compressor | no_records | - | 5340 |
| ac-compressor | split | no_candidates | 64 |
| ac-compressor | split | option_split | 35106 |
| ac-compressor | conditional | conditional:engine_unattested | 14820 |
| ac-compressor | conditional | conditional:option | 96 |
| ac-compressor | conditional | conditional:qualifier | 8239 |
| alternator | unmapped | - | 15201 |
| alternator | no_records | - | 5461 |
| alternator | split | no_candidates | 7 |
| alternator | split | option_split | 40387 |
| alternator | conditional | conditional:engine_unattested | 16150 |
| alternator | conditional | conditional:qualifier | 1660 |
| climate-control | unmapped | - | 15201 |
| climate-control | no_records | - | 17176 |
| climate-control | split | no_candidates | 122 |
| climate-control | split | option_split | 37700 |
| climate-control | conditional | conditional:engine_unattested | 7189 |
| climate-control | conditional | conditional:option | 1478 |
| fuel-pump-module | unmapped | - | 15201 |
| fuel-pump-module | no_records | - | 7611 |
| fuel-pump-module | split | no_candidates | 48 |
| fuel-pump-module | split | option_split | 41693 |
| fuel-pump-module | conditional | conditional:engine_unattested | 6766 |
| fuel-pump-module | conditional | conditional:qualifier | 7547 |
| headlights | unmapped | - | 15201 |
| headlights | no_records | - | 11153 |
| headlights | split | no_candidates | 349 |
| headlights | split | option_split | 24743 |
| headlights | conditional | conditional:engine_unattested | 14249 |
| headlights | conditional | conditional:option | 703 |
| headlights | conditional | conditional:qualifier | 12468 |
| power-steering-pump | unmapped | - | 15201 |
| power-steering-pump | no_records | - | 18027 |
| power-steering-pump | split | no_candidates | 34 |
| power-steering-pump | split | option_split | 22296 |
| power-steering-pump | conditional | conditional:engine_unattested | 17371 |
| power-steering-pump | conditional | conditional:qualifier | 5937 |
| side-mirrors | unmapped | - | 15201 |
| side-mirrors | no_records | - | 3914 |
| side-mirrors | split | no_candidates | 8 |
| side-mirrors | split | option_split | 54361 |
| side-mirrors | split | position_missing | 44 |
| side-mirrors | split | slot_missing | 116 |
| side-mirrors | conditional | conditional:engine_unattested | 4349 |
| side-mirrors | conditional | conditional:option | 521 |
| side-mirrors | conditional | conditional:qualifier | 352 |
| starter | unmapped | - | 15201 |
| starter | no_records | - | 2990 |
| starter | split | no_candidates | 188 |
| starter | split | option_split | 32947 |
| starter | conditional | conditional:engine_unattested | 16004 |
| starter | conditional | conditional:option | 296 |
| starter | conditional | conditional:qualifier | 11240 |
| tail-lights | unmapped | - | 15201 |
| tail-lights | no_records | - | 6480 |
| tail-lights | split | no_candidates | 64 |
| tail-lights | split | option_split | 32385 |
| tail-lights | split | position_missing | 874 |
| tail-lights | split | slot_missing | 421 |
| tail-lights | conditional | conditional:engine_unattested | 22228 |
| tail-lights | conditional | conditional:option | 66 |
| tail-lights | conditional | conditional:qualifier | 1147 |
| throttle-body | unmapped | - | 15201 |
| throttle-body | no_records | - | 24356 |
| throttle-body | split | no_candidates | 788 |
| throttle-body | split | option_split | 18371 |
| throttle-body | conditional | conditional:engine_unattested | 5598 |
| throttle-body | conditional | conditional:qualifier | 14552 |
| window-regulator | unmapped | - | 15201 |
| window-regulator | no_records | - | 2382 |
| window-regulator | split | no_candidates | 52 |
| window-regulator | split | packaging_incomplete | 3763 |
| window-regulator | split | packaging_split | 16088 |
| window-regulator | split | packaging_unstated | 40963 |
| window-regulator | split | slot_missing | 25 |
| window-regulator | conditional | conditional:engine_unattested | 357 |
| window-regulator | conditional | conditional:option | 35 |
| window-switch | unmapped | - | 15201 |
| window-switch | no_records | - | 8554 |
| window-switch | split | no_candidates | 129 |
| window-switch | split | option_split | 36524 |
| window-switch | split | position_missing | 11771 |
| window-switch | conditional | conditional:engine_unattested | 3961 |
| window-switch | conditional | conditional:option | 101 |
| window-switch | conditional | conditional:qualifier | 2625 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 6
- recrawl_resolved: 1
- rule_drift: 1
- universal_part_suspect: 144

## Unknown note clauses (top 30)

- `2`: 659
- `CK1`: 290
- `Package Quantity: 1`: 69
- `Require Quantity: 02`: 68
- `OUTSIDE REAR VIEW(INCLUDES 1,2,5)(PAINT TO MATCH)`: 45
- `BS`: 42
- `2(5B5)`: 40
- `2(A31)(EXC 5B5)`: 40
- `JV`: 40
- `MODULE KIT`: 40
- `SWITCH`: 37
- `GENERATOR`: 36
- `3(5B5)`: 28
- `3(A31)(EXC 5B5)`: 28
- `PUMP`: 25
- `3(8B2)`: 24
- `HEATER & A/C`: 24
- `OUTSIDE REAR VIEW(INCLUDES 2-6,8-15)`: 24
- `3(8G9)`: 23
- `KE`: 23
- `AK`: 22
- `CONTROL`: 22
- `FRONT SIDE DOOR WINDOW`: 21
- `TAIL`: 21
- `ZC`: 21
- `OUTSIDE REAR VIEW`: 19
- `STARTER`: 19
- `REAR SIDE DOOR WINDOW`: 18
- `XR`: 18
- `3(X88,Z88,5B5)`: 16

## Unmapped catalog models

- Buick Estate Wagon: feed 'Estate Wagon' 0 cars
- Buick Somerset: feed 'Somerset' 0 cars
- Cadillac CT4: feed 'CT4' 0 cars
- Cadillac Cimarron: feed 'Cimarron' 0 cars
- Cadillac Commercial Chassis: feed 'Commercial Chassis' 1 cars
- Cadillac XT6: feed 'XT6' 0 cars
- Chevrolet Aveo: feed 'Aveo' 577 cars
- Chevrolet Bolt EUV: feed 'Bolt EUV' 0 cars
- Chevrolet Cadet: feed 'Cadet' 0 cars
- Chevrolet Chevette: feed 'Chevette' 5 cars
- Chevrolet Citation: feed 'Citation' 4 cars
- Chevrolet El Camino: feed 'El Camino' 34 cars
- Chevrolet K30: feed 'K30' 0 cars
- Chevrolet P20: feed 'P20' 0 cars
- Chevrolet R10: feed 'R10' 0 cars
- Chevrolet R20: feed 'R20' 0 cars
- Chevrolet R2500: feed 'R2500' 0 cars
- Chevrolet SS: feed 'SS' 0 cars
- Chevrolet SSR: feed 'SSR' 0 cars
- Chevrolet Tracker: feed 'Tracker' 115 cars
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
- Pontiac G3: feed 'G3' 23 cars
- Pontiac G8: feed 'G8' 26 cars
- Pontiac J2000: feed 'J2000' 0 cars
- Pontiac LeMans: feed 'LeMans' 5 cars
- Pontiac Parisienne: feed 'Parisienne' 4 cars
- Pontiac Phoenix: feed 'Phoenix' 2 cars
- Pontiac Safari: feed 'Safari' 2 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (2 cars, under catalog squash 'safari'); unmapped until a reviewed entry exists)
- Pontiac T1000: feed 'T1000' 0 cars
