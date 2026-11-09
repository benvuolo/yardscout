# OEM curation report: gm

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-06T07:20:17Z.

- records 3633, classes 3633, list rows 95531, year manifests 152, cells 13272
- Verified groups 0, engine vg groups 0, Likely groups 289
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.gmpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.gmpartsgiant.com: only 0% of its 11390 fitment rows can be coverage: its option column holds trims (option_column_is_trims), which count only after a namespace audit (spec 5.2)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 15834 |
| ac-compressor | no_records | - | 5554 |
| ac-compressor | not_closed | ambig_target | 6590 |
| ac-compressor | not_closed | no_year_manifest | 51778 |
| ac-compressor | not_closed | unattested | 34 |
| ac-compressor | not_closed | uncrawled_chain_member | 799 |
| ac-compressor | not_closed | unverified_product | 1042 |
| ac-compressor | not_closed | year_manifest_bad | 6 |
| alternator | unmapped | - | 15834 |
| alternator | no_records | - | 5665 |
| alternator | not_closed | ambig_target | 6293 |
| alternator | not_closed | no_year_manifest | 52008 |
| alternator | not_closed | unread_sibling_page | 1831 |
| alternator | not_closed | year_manifest_bad | 6 |
| climate-control | unmapped | - | 15834 |
| climate-control | no_records | - | 17734 |
| climate-control | not_closed | ambig_target | 6933 |
| climate-control | not_closed | no_year_manifest | 39553 |
| climate-control | not_closed | unread_sibling_page | 1583 |
| fuel-pump-module | unmapped | - | 15834 |
| fuel-pump-module | no_records | - | 7874 |
| fuel-pump-module | not_closed | ambig_target | 6470 |
| fuel-pump-module | not_closed | no_list_manifest | 1 |
| fuel-pump-module | not_closed | no_year_manifest | 49584 |
| fuel-pump-module | not_closed | unread_sibling_page | 1874 |
| headlights | unmapped | - | 15834 |
| headlights | no_records | - | 11595 |
| headlights | not_closed | ambig_target | 6553 |
| headlights | not_closed | no_year_manifest | 45774 |
| headlights | not_closed | unattested | 302 |
| headlights | not_closed | uncrawled_chain_member | 694 |
| headlights | not_closed | unread_sibling_page | 828 |
| headlights | not_closed | unverified_product | 51 |
| headlights | not_closed | year_manifest_bad | 6 |
| power-steering-pump | unmapped | - | 15834 |
| power-steering-pump | no_records | - | 18689 |
| power-steering-pump | not_closed | ambig_target | 6892 |
| power-steering-pump | not_closed | no_year_manifest | 38703 |
| power-steering-pump | not_closed | unread_sibling_page | 1513 |
| power-steering-pump | not_closed | year_manifest_bad | 6 |
| side-mirrors | unmapped | - | 15834 |
| side-mirrors | no_records | - | 4040 |
| side-mirrors | not_closed | ambig_target | 6976 |
| side-mirrors | not_closed | no_year_manifest | 52906 |
| side-mirrors | not_closed | unread_sibling_page | 1875 |
| side-mirrors | not_closed | year_manifest_bad | 6 |
| starter | unmapped | - | 15834 |
| starter | no_records | - | 3088 |
| starter | not_closed | ambig_target | 6972 |
| starter | not_closed | no_year_manifest | 53863 |
| starter | not_closed | unread_sibling_page | 1874 |
| starter | not_closed | year_manifest_bad | 6 |
| tail-lights | unmapped | - | 15834 |
| tail-lights | no_records | - | 6712 |
| tail-lights | not_closed | ambig_target | 6857 |
| tail-lights | not_closed | no_year_manifest | 50353 |
| tail-lights | not_closed | unattested | 391 |
| tail-lights | not_closed | uncrawled_chain_member | 1330 |
| tail-lights | not_closed | unverified_product | 154 |
| tail-lights | not_closed | year_manifest_bad | 6 |
| throttle-body | unmapped | - | 15834 |
| throttle-body | no_records | - | 25119 |
| throttle-body | not_closed | ambig_target | 6372 |
| throttle-body | not_closed | no_year_manifest | 32433 |
| throttle-body | not_closed | unattested | 1047 |
| throttle-body | not_closed | uncrawled_chain_member | 577 |
| throttle-body | not_closed | unverified_product | 249 |
| throttle-body | not_closed | year_manifest_bad | 6 |
| window-regulator | unmapped | - | 15834 |
| window-regulator | no_records | - | 2445 |
| window-regulator | not_closed | ambig_target | 6818 |
| window-regulator | not_closed | no_year_manifest | 54667 |
| window-regulator | not_closed | unattested | 33 |
| window-regulator | not_closed | uncrawled_chain_member | 671 |
| window-regulator | not_closed | unread_sibling_page | 979 |
| window-regulator | not_closed | unverified_product | 184 |
| window-regulator | not_closed | year_manifest_bad | 6 |
| window-switch | unmapped | - | 15834 |
| window-switch | no_records | - | 8839 |
| window-switch | not_closed | ambig_target | 6836 |
| window-switch | not_closed | no_year_manifest | 48255 |
| window-switch | not_closed | unattested | 139 |
| window-switch | not_closed | uncrawled_chain_member | 651 |
| window-switch | not_closed | unread_sibling_page | 755 |
| window-switch | not_closed | unverified_product | 322 |
| window-switch | not_closed | year_manifest_bad | 6 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 15834 |
| ac-compressor | no_records | - | 5554 |
| ac-compressor | split | no_candidates | 66 |
| ac-compressor | split | option_split | 36233 |
| ac-compressor | conditional | conditional:engine_unattested | 15305 |
| ac-compressor | conditional | conditional:option | 104 |
| ac-compressor | conditional | conditional:qualifier | 8541 |
| alternator | unmapped | - | 15834 |
| alternator | no_records | - | 5665 |
| alternator | split | no_candidates | 7 |
| alternator | split | option_split | 41608 |
| alternator | conditional | conditional:engine_unattested | 16795 |
| alternator | conditional | conditional:qualifier | 1728 |
| climate-control | unmapped | - | 15834 |
| climate-control | no_records | - | 17734 |
| climate-control | split | no_candidates | 129 |
| climate-control | split | option_split | 38965 |
| climate-control | conditional | conditional:engine_unattested | 7445 |
| climate-control | conditional | conditional:option | 1530 |
| fuel-pump-module | unmapped | - | 15834 |
| fuel-pump-module | no_records | - | 7874 |
| fuel-pump-module | split | no_candidates | 48 |
| fuel-pump-module | split | option_split | 42947 |
| fuel-pump-module | conditional | conditional:engine_unattested | 7070 |
| fuel-pump-module | conditional | conditional:qualifier | 7864 |
| headlights | unmapped | - | 15834 |
| headlights | no_records | - | 11595 |
| headlights | split | no_candidates | 367 |
| headlights | split | option_split | 25464 |
| headlights | conditional | conditional:engine_unattested | 14865 |
| headlights | conditional | conditional:option | 735 |
| headlights | conditional | conditional:qualifier | 12777 |
| power-steering-pump | unmapped | - | 15834 |
| power-steering-pump | no_records | - | 18689 |
| power-steering-pump | split | no_candidates | 35 |
| power-steering-pump | split | option_split | 22905 |
| power-steering-pump | conditional | conditional:engine_unattested | 17925 |
| power-steering-pump | conditional | conditional:qualifier | 6249 |
| side-mirrors | unmapped | - | 15834 |
| side-mirrors | no_records | - | 4040 |
| side-mirrors | split | no_candidates | 8 |
| side-mirrors | split | option_split | 56185 |
| side-mirrors | split | position_missing | 44 |
| side-mirrors | split | slot_missing | 122 |
| side-mirrors | conditional | conditional:engine_unattested | 4507 |
| side-mirrors | conditional | conditional:option | 533 |
| side-mirrors | conditional | conditional:qualifier | 364 |
| starter | unmapped | - | 15834 |
| starter | no_records | - | 3088 |
| starter | split | no_candidates | 196 |
| starter | split | option_split | 33945 |
| starter | conditional | conditional:engine_unattested | 16704 |
| starter | conditional | conditional:option | 306 |
| starter | conditional | conditional:qualifier | 11564 |
| tail-lights | unmapped | - | 15834 |
| tail-lights | no_records | - | 6712 |
| tail-lights | split | no_candidates | 65 |
| tail-lights | split | option_split | 33436 |
| tail-lights | split | position_missing | 889 |
| tail-lights | split | slot_missing | 433 |
| tail-lights | conditional | conditional:engine_unattested | 22997 |
| tail-lights | conditional | conditional:option | 67 |
| tail-lights | conditional | conditional:qualifier | 1204 |
| throttle-body | unmapped | - | 15834 |
| throttle-body | no_records | - | 25119 |
| throttle-body | split | no_candidates | 810 |
| throttle-body | split | option_split | 18927 |
| throttle-body | conditional | conditional:engine_unattested | 5876 |
| throttle-body | conditional | conditional:qualifier | 15071 |
| window-regulator | unmapped | - | 15834 |
| window-regulator | no_records | - | 2445 |
| window-regulator | split | no_candidates | 51 |
| window-regulator | split | packaging_incomplete | 3880 |
| window-regulator | split | packaging_split | 16487 |
| window-regulator | split | packaging_unstated | 42517 |
| window-regulator | split | slot_missing | 26 |
| window-regulator | conditional | conditional:engine_unattested | 361 |
| window-regulator | conditional | conditional:option | 36 |
| window-switch | unmapped | - | 15834 |
| window-switch | no_records | - | 8839 |
| window-switch | split | no_candidates | 133 |
| window-switch | split | option_split | 37572 |
| window-switch | split | position_missing | 12302 |
| window-switch | conditional | conditional:engine_unattested | 4147 |
| window-switch | conditional | conditional:option | 103 |
| window-switch | conditional | conditional:qualifier | 2707 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 6
- held_exterior_cross_model: 50
- recrawl_resolved: 1
- rule_drift: 1
- universal_part_suspect: 137

## Unknown note clauses (top 30)

- `2`: 596
- `CK1`: 253
- `Package Quantity: 1`: 69
- `Require Quantity: 02`: 68
- `OUTSIDE REAR VIEW(INCLUDES 1,2,5)(PAINT TO MATCH)`: 45
- `BS`: 42
- `2(5B5)`: 40
- `2(A31)(EXC 5B5)`: 40
- `JV`: 40
- `MODULE KIT`: 40
- `GENERATOR`: 36
- `SWITCH`: 35
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
- `BODY`: 15
- `COMPRESSOR KIT`: 15

## Unmapped catalog models

- Buick Estate Wagon: feed 'Estate Wagon' 0 cars
- Buick Somerset: feed 'Somerset' 0 cars
- Cadillac CT4: feed 'CT4' 0 cars
- Cadillac Cimarron: feed 'Cimarron' 0 cars
- Cadillac Commercial Chassis: feed 'Commercial Chassis' 1 cars
- Cadillac XT6: feed 'XT6' 0 cars
- Chevrolet Aveo: feed 'Aveo' 610 cars
- Chevrolet Bolt EUV: feed 'Bolt EUV' 0 cars
- Chevrolet Cadet: feed 'Cadet' 0 cars
- Chevrolet Chevette: feed 'Chevette' 6 cars
- Chevrolet Citation: feed 'Citation' 3 cars
- Chevrolet El Camino: feed 'El Camino' 34 cars
- Chevrolet K30: feed 'K30' 0 cars
- Chevrolet P20: feed 'P20' 0 cars
- Chevrolet R10: feed 'R10' 0 cars
- Chevrolet R20: feed 'R20' 0 cars
- Chevrolet R2500: feed 'R2500' 0 cars
- Chevrolet SS: feed 'SS' 0 cars
- Chevrolet SSR: feed 'SSR' 0 cars
- Chevrolet Suburban: feed 'Suburban' 221 cars (excluded: M6: of 4 cached vPIC decodes of feed 'Chevrolet Suburban' (221 cars) 1 names GMC (VIN 3GK, a mislabelled listing); over the 2% cap, so unmapped like Acura ILX (interchange, 2026-11-09; unmapped, no claims, until a reviewed entry exists))
- Chevrolet Tracker: feed 'Tracker' 117 cars
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
- Pontiac G8: feed 'G8' 27 cars
- Pontiac J2000: feed 'J2000' 0 cars
- Pontiac LeMans: feed 'LeMans' 4 cars
- Pontiac Parisienne: feed 'Parisienne' 4 cars
- Pontiac Phoenix: feed 'Phoenix' 2 cars
- Pontiac Safari: feed 'Safari' 2 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (2 cars, under catalog squash 'safari'); unmapped until a reviewed entry exists)
- Pontiac T1000: feed 'T1000' 0 cars
