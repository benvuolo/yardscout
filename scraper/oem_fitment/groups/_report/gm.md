# OEM curation report: gm

Raw: `c36da2eb98835c02f81c05e8c36b6a926634a332` @ `c36da2eb9883`; as of 2026-11-09T02:38:43Z.

- records 5875, classes 5875, list rows 95531, year manifests 424, cells 21446
- Verified groups 0, engine vg groups 0, Likely groups 309
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.gmpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.gmpartsgiant.com: only 0% of its 17867 fitment rows can be coverage: its option column holds trims (option_column_is_trims), which count only after a namespace audit (spec 5.2)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 15834 |
| ac-compressor | no_records | - | 3433 |
| ac-compressor | not_closed | ambig_target | 6661 |
| ac-compressor | not_closed | no_list_manifest | 12265 |
| ac-compressor | not_closed | no_year_manifest | 41180 |
| ac-compressor | not_closed | unattested | 34 |
| ac-compressor | not_closed | uncrawled_chain_member | 799 |
| ac-compressor | not_closed | unverified_product | 1042 |
| ac-compressor | not_closed | variant_unread | 382 |
| ac-compressor | not_closed | year_manifest_bad | 7 |
| alternator | unmapped | - | 15834 |
| alternator | no_records | - | 4561 |
| alternator | not_closed | ambig_target | 6293 |
| alternator | not_closed | no_list_manifest | 12318 |
| alternator | not_closed | no_year_manifest | 40411 |
| alternator | not_closed | unread_sibling_page | 1831 |
| alternator | not_closed | variant_unread | 382 |
| alternator | not_closed | year_manifest_bad | 7 |
| bumper-front | unmapped | - | 15834 |
| bumper-front | no_records | - | 18587 |
| bumper-front | not_closed | ambig_target | 4697 |
| bumper-front | not_closed | no_list_manifest | 12359 |
| bumper-front | not_closed | no_year_manifest | 29778 |
| bumper-front | not_closed | variant_unread | 382 |
| bumper-rear | unmapped | - | 15834 |
| bumper-rear | no_records | - | 20338 |
| bumper-rear | not_closed | ambig_target | 4101 |
| bumper-rear | not_closed | no_list_manifest | 11717 |
| bumper-rear | not_closed | no_year_manifest | 29265 |
| bumper-rear | not_closed | variant_unread | 382 |
| climate-control | unmapped | - | 15834 |
| climate-control | no_records | - | 16760 |
| climate-control | not_closed | ambig_target | 6946 |
| climate-control | not_closed | no_list_manifest | 10541 |
| climate-control | not_closed | no_year_manifest | 29605 |
| climate-control | not_closed | unread_sibling_page | 1583 |
| climate-control | not_closed | variant_unread | 362 |
| climate-control | not_closed | year_manifest_bad | 6 |
| door-front | unmapped | - | 15834 |
| door-front | no_records | - | 14736 |
| door-front | not_closed | ambig_target | 6370 |
| door-front | not_closed | no_list_manifest | 11747 |
| door-front | not_closed | no_year_manifest | 32562 |
| door-front | not_closed | variant_unread | 382 |
| door-front | not_closed | year_manifest_bad | 6 |
| door-rear | unmapped | - | 15834 |
| door-rear | no_records | - | 21658 |
| door-rear | not_closed | ambig_target | 3011 |
| door-rear | not_closed | no_list_manifest | 11366 |
| door-rear | not_closed | no_year_manifest | 29380 |
| door-rear | not_closed | variant_unread | 382 |
| door-rear | not_closed | year_manifest_bad | 6 |
| fender | unmapped | - | 15834 |
| fender | no_records | - | 27206 |
| fender | not_closed | ambig_target | 4113 |
| fender | not_closed | no_list_manifest | 9982 |
| fender | not_closed | no_year_manifest | 24134 |
| fender | not_closed | variant_unread | 362 |
| fender | not_closed | year_manifest_bad | 6 |
| fuel-pump-module | unmapped | - | 15834 |
| fuel-pump-module | no_records | - | 6719 |
| fuel-pump-module | not_closed | ambig_target | 6486 |
| fuel-pump-module | not_closed | no_list_manifest | 12347 |
| fuel-pump-module | not_closed | no_year_manifest | 37988 |
| fuel-pump-module | not_closed | unread_sibling_page | 1874 |
| fuel-pump-module | not_closed | variant_unread | 382 |
| fuel-pump-module | not_closed | year_manifest_bad | 7 |
| gauge-cluster | unmapped | - | 15834 |
| gauge-cluster | no_records | - | 35703 |
| gauge-cluster | not_closed | ambig_target | 3283 |
| gauge-cluster | not_closed | no_list_manifest | 11390 |
| gauge-cluster | not_closed | no_year_manifest | 15065 |
| gauge-cluster | not_closed | variant_unread | 362 |
| grille | unmapped | - | 15834 |
| grille | no_records | - | 19474 |
| grille | not_closed | ambig_target | 4442 |
| grille | not_closed | no_list_manifest | 11675 |
| grille | not_closed | no_year_manifest | 29850 |
| grille | not_closed | variant_unread | 362 |
| headlights | unmapped | - | 15834 |
| headlights | no_records | - | 9940 |
| headlights | not_closed | ambig_target | 6886 |
| headlights | not_closed | no_list_manifest | 11669 |
| headlights | not_closed | no_year_manifest | 35045 |
| headlights | not_closed | unattested | 282 |
| headlights | not_closed | uncrawled_chain_member | 714 |
| headlights | not_closed | unread_sibling_page | 828 |
| headlights | not_closed | unverified_product | 51 |
| headlights | not_closed | variant_unread | 382 |
| headlights | not_closed | year_manifest_bad | 6 |
| hood | unmapped | - | 15834 |
| hood | no_records | - | 23266 |
| hood | not_closed | ambig_target | 4113 |
| hood | not_closed | no_list_manifest | 10992 |
| hood | not_closed | no_year_manifest | 27064 |
| hood | not_closed | variant_unread | 362 |
| hood | not_closed | year_manifest_bad | 6 |
| ignition-coils | unmapped | - | 15834 |
| ignition-coils | no_records | - | 5982 |
| ignition-coils | not_closed | ambig_target | 5375 |
| ignition-coils | not_closed | no_list_manifest | 13809 |
| ignition-coils | not_closed | no_year_manifest | 40248 |
| ignition-coils | not_closed | variant_unread | 382 |
| ignition-coils | not_closed | year_manifest_bad | 7 |
| liftgate | unmapped | - | 15834 |
| liftgate | no_records | - | 43884 |
| liftgate | not_closed | ambig_target | 4396 |
| liftgate | not_closed | no_list_manifest | 4227 |
| liftgate | not_closed | no_year_manifest | 13270 |
| liftgate | not_closed | variant_unread | 20 |
| liftgate | not_closed | year_manifest_bad | 6 |
| power-steering-pump | unmapped | - | 15834 |
| power-steering-pump | no_records | - | 17659 |
| power-steering-pump | not_closed | ambig_target | 6935 |
| power-steering-pump | not_closed | no_list_manifest | 8061 |
| power-steering-pump | not_closed | no_year_manifest | 31454 |
| power-steering-pump | not_closed | unread_sibling_page | 1513 |
| power-steering-pump | not_closed | variant_unread | 174 |
| power-steering-pump | not_closed | year_manifest_bad | 7 |
| radiator | unmapped | - | 15834 |
| radiator | no_records | - | 10309 |
| radiator | not_closed | ambig_target | 6744 |
| radiator | not_closed | no_list_manifest | 12915 |
| radiator | not_closed | no_year_manifest | 35447 |
| radiator | not_closed | variant_unread | 382 |
| radiator | not_closed | year_manifest_bad | 6 |
| side-mirrors | unmapped | - | 15834 |
| side-mirrors | no_records | - | 3039 |
| side-mirrors | not_closed | ambig_target | 6976 |
| side-mirrors | not_closed | no_list_manifest | 12466 |
| side-mirrors | not_closed | no_year_manifest | 41058 |
| side-mirrors | not_closed | unread_sibling_page | 1875 |
| side-mirrors | not_closed | variant_unread | 382 |
| side-mirrors | not_closed | year_manifest_bad | 7 |
| starter | unmapped | - | 15834 |
| starter | no_records | - | 2266 |
| starter | not_closed | ambig_target | 6993 |
| starter | not_closed | no_list_manifest | 12196 |
| starter | not_closed | no_year_manifest | 42085 |
| starter | not_closed | unread_sibling_page | 1874 |
| starter | not_closed | variant_unread | 382 |
| starter | not_closed | year_manifest_bad | 7 |
| tail-lights | unmapped | - | 15834 |
| tail-lights | no_records | - | 5376 |
| tail-lights | not_closed | ambig_target | 6857 |
| tail-lights | not_closed | no_list_manifest | 12238 |
| tail-lights | not_closed | no_year_manifest | 39069 |
| tail-lights | not_closed | unattested | 384 |
| tail-lights | not_closed | uncrawled_chain_member | 1337 |
| tail-lights | not_closed | unverified_product | 154 |
| tail-lights | not_closed | variant_unread | 382 |
| tail-lights | not_closed | year_manifest_bad | 6 |
| tailgate | unmapped | - | 15834 |
| tailgate | no_records | - | 62806 |
| tailgate | not_closed | ambig_target | 1438 |
| tailgate | not_closed | no_list_manifest | 110 |
| tailgate | not_closed | no_year_manifest | 1449 |
| throttle-body | unmapped | - | 15834 |
| throttle-body | no_records | - | 24477 |
| throttle-body | not_closed | ambig_target | 6372 |
| throttle-body | not_closed | no_list_manifest | 7404 |
| throttle-body | not_closed | no_year_manifest | 25671 |
| throttle-body | not_closed | unattested | 1047 |
| throttle-body | not_closed | uncrawled_chain_member | 577 |
| throttle-body | not_closed | unverified_product | 249 |
| throttle-body | not_closed | year_manifest_bad | 6 |
| trunk-lid | unmapped | - | 15834 |
| trunk-lid | no_records | - | 43770 |
| trunk-lid | not_closed | no_list_manifest | 6802 |
| trunk-lid | not_closed | no_year_manifest | 14869 |
| trunk-lid | not_closed | variant_unread | 362 |
| window-regulator | unmapped | - | 15834 |
| window-regulator | no_records | - | 1907 |
| window-regulator | not_closed | ambig_target | 6818 |
| window-regulator | not_closed | no_list_manifest | 12479 |
| window-regulator | not_closed | no_year_manifest | 42343 |
| window-regulator | not_closed | unattested | 33 |
| window-regulator | not_closed | uncrawled_chain_member | 671 |
| window-regulator | not_closed | unread_sibling_page | 979 |
| window-regulator | not_closed | unverified_product | 184 |
| window-regulator | not_closed | variant_unread | 382 |
| window-regulator | not_closed | year_manifest_bad | 7 |
| window-switch | unmapped | - | 15834 |
| window-switch | no_records | - | 7410 |
| window-switch | not_closed | ambig_target | 6928 |
| window-switch | not_closed | no_list_manifest | 11670 |
| window-switch | not_closed | no_year_manifest | 37540 |
| window-switch | not_closed | unattested | 139 |
| window-switch | not_closed | uncrawled_chain_member | 651 |
| window-switch | not_closed | unread_sibling_page | 755 |
| window-switch | not_closed | unverified_product | 322 |
| window-switch | not_closed | variant_unread | 382 |
| window-switch | not_closed | year_manifest_bad | 6 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 15834 |
| ac-compressor | no_records | - | 3433 |
| ac-compressor | split | no_candidates | 66 |
| ac-compressor | split | option_split | 37038 |
| ac-compressor | conditional | conditional:engine_unattested | 16716 |
| ac-compressor | conditional | conditional:option | 154 |
| ac-compressor | conditional | conditional:qualifier | 8396 |
| alternator | unmapped | - | 15834 |
| alternator | no_records | - | 4561 |
| alternator | split | no_candidates | 7 |
| alternator | split | option_split | 42487 |
| alternator | conditional | conditional:engine_unattested | 17100 |
| alternator | conditional | conditional:qualifier | 1648 |
| bumper-front | unmapped | - | 15834 |
| bumper-front | no_records | - | 18587 |
| bumper-front | split | option_split | 40617 |
| bumper-front | conditional | conditional:engine_unattested | 6323 |
| bumper-front | conditional | conditional:qualifier | 276 |
| bumper-rear | unmapped | - | 15834 |
| bumper-rear | no_records | - | 20338 |
| bumper-rear | split | option_split | 38732 |
| bumper-rear | conditional | conditional:engine_unattested | 4420 |
| bumper-rear | conditional | conditional:qualifier | 2313 |
| climate-control | unmapped | - | 15834 |
| climate-control | no_records | - | 16760 |
| climate-control | split | no_candidates | 129 |
| climate-control | split | option_split | 39704 |
| climate-control | conditional | conditional:engine_unattested | 7605 |
| climate-control | conditional | conditional:option | 1596 |
| climate-control | conditional | conditional:qualifier | 9 |
| door-front | unmapped | - | 15834 |
| door-front | no_records | - | 14736 |
| door-front | split | option_split | 7822 |
| door-front | split | slot_missing | 3367 |
| door-front | conditional | conditional:engine_unattested | 29700 |
| door-front | conditional | conditional:option | 189 |
| door-front | conditional | conditional:qualifier | 9989 |
| door-rear | unmapped | - | 15834 |
| door-rear | no_records | - | 21658 |
| door-rear | split | option_split | 8678 |
| door-rear | split | slot_missing | 2858 |
| door-rear | conditional | conditional:engine_unattested | 15895 |
| door-rear | conditional | conditional:qualifier | 16714 |
| fender | unmapped | - | 15834 |
| fender | no_records | - | 27206 |
| fender | split | option_split | 6571 |
| fender | conditional | conditional:engine_unattested | 25630 |
| fender | conditional | conditional:option | 149 |
| fender | conditional | conditional:qualifier | 6247 |
| fuel-pump-module | unmapped | - | 15834 |
| fuel-pump-module | no_records | - | 6719 |
| fuel-pump-module | split | no_candidates | 48 |
| fuel-pump-module | split | option_split | 44540 |
| fuel-pump-module | conditional | conditional:engine_unattested | 6720 |
| fuel-pump-module | conditional | conditional:qualifier | 7776 |
| gauge-cluster | unmapped | - | 15834 |
| gauge-cluster | no_records | - | 35703 |
| gauge-cluster | split | option_split | 28419 |
| gauge-cluster | conditional | conditional:engine_unattested | 1681 |
| grille | unmapped | - | 15834 |
| grille | no_records | - | 19474 |
| grille | split | option_split | 39827 |
| grille | conditional | conditional:engine_unattested | 3817 |
| grille | conditional | conditional:qualifier | 2685 |
| headlights | unmapped | - | 15834 |
| headlights | no_records | - | 9940 |
| headlights | split | no_candidates | 315 |
| headlights | split | option_split | 26136 |
| headlights | split | position_missing | 393 |
| headlights | split | slot_missing | 164 |
| headlights | conditional | conditional:engine_unattested | 15216 |
| headlights | conditional | conditional:option | 744 |
| headlights | conditional | conditional:qualifier | 12895 |
| hood | unmapped | - | 15834 |
| hood | no_records | - | 23266 |
| hood | split | option_split | 4146 |
| hood | conditional | conditional:engine_unattested | 34636 |
| hood | conditional | conditional:qualifier | 3755 |
| ignition-coils | unmapped | - | 15834 |
| ignition-coils | no_records | - | 5982 |
| ignition-coils | split | option_split | 36392 |
| ignition-coils | conditional | conditional:engine_unattested | 20266 |
| ignition-coils | conditional | conditional:package | 639 |
| ignition-coils | conditional | conditional:qualifier | 2524 |
| liftgate | unmapped | - | 15834 |
| liftgate | no_records | - | 43884 |
| liftgate | split | option_split | 691 |
| liftgate | conditional | conditional:engine_unattested | 12849 |
| liftgate | conditional | conditional:qualifier | 8379 |
| power-steering-pump | unmapped | - | 15834 |
| power-steering-pump | no_records | - | 17659 |
| power-steering-pump | split | no_candidates | 35 |
| power-steering-pump | split | option_split | 23865 |
| power-steering-pump | conditional | conditional:engine_unattested | 18029 |
| power-steering-pump | conditional | conditional:qualifier | 6215 |
| radiator | unmapped | - | 15834 |
| radiator | no_records | - | 10309 |
| radiator | split | option_split | 43782 |
| radiator | conditional | conditional:engine_unattested | 9005 |
| radiator | conditional | conditional:qualifier | 2707 |
| side-mirrors | unmapped | - | 15834 |
| side-mirrors | no_records | - | 3039 |
| side-mirrors | split | no_candidates | 1 |
| side-mirrors | split | option_split | 57032 |
| side-mirrors | split | position_missing | 14 |
| side-mirrors | split | slot_missing | 123 |
| side-mirrors | conditional | conditional:engine_unattested | 4697 |
| side-mirrors | conditional | conditional:option | 533 |
| side-mirrors | conditional | conditional:qualifier | 364 |
| starter | unmapped | - | 15834 |
| starter | no_records | - | 2266 |
| starter | split | no_candidates | 196 |
| starter | split | option_split | 34670 |
| starter | conditional | conditional:engine_unattested | 16882 |
| starter | conditional | conditional:option | 306 |
| starter | conditional | conditional:qualifier | 11483 |
| tail-lights | unmapped | - | 15834 |
| tail-lights | no_records | - | 5376 |
| tail-lights | split | no_candidates | 65 |
| tail-lights | split | option_split | 36412 |
| tail-lights | split | position_missing | 986 |
| tail-lights | split | slot_missing | 430 |
| tail-lights | conditional | conditional:engine_unattested | 21786 |
| tail-lights | conditional | conditional:option | 67 |
| tail-lights | conditional | conditional:qualifier | 681 |
| tailgate | unmapped | - | 15834 |
| tailgate | no_records | - | 62806 |
| tailgate | split | option_split | 2302 |
| tailgate | conditional | conditional:engine_unattested | 695 |
| throttle-body | unmapped | - | 15834 |
| throttle-body | no_records | - | 24477 |
| throttle-body | split | no_candidates | 810 |
| throttle-body | split | option_split | 19969 |
| throttle-body | conditional | conditional:engine_unattested | 5436 |
| throttle-body | conditional | conditional:qualifier | 15111 |
| trunk-lid | unmapped | - | 15834 |
| trunk-lid | no_records | - | 43770 |
| trunk-lid | split | option_split | 8867 |
| trunk-lid | conditional | conditional:engine_unattested | 11673 |
| trunk-lid | conditional | conditional:qualifier | 1493 |
| window-regulator | unmapped | - | 15834 |
| window-regulator | no_records | - | 1907 |
| window-regulator | split | no_candidates | 51 |
| window-regulator | split | packaging_incomplete | 3759 |
| window-regulator | split | packaging_split | 16526 |
| window-regulator | split | packaging_unstated | 43150 |
| window-regulator | split | slot_missing | 13 |
| window-regulator | conditional | conditional:engine_unattested | 361 |
| window-regulator | conditional | conditional:option | 36 |
| window-switch | unmapped | - | 15834 |
| window-switch | no_records | - | 7410 |
| window-switch | split | no_candidates | 133 |
| window-switch | split | option_split | 38801 |
| window-switch | split | position_missing | 12322 |
| window-switch | conditional | conditional:engine_unattested | 4327 |
| window-switch | conditional | conditional:option | 103 |
| window-switch | conditional | conditional:qualifier | 2707 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 17
- held_exterior_cross_model: 30
- recrawl_resolved: 1
- rule_drift: 2
- universal_part_suspect: 190

## Unknown note clauses (top 30)

- `2`: 619
- `CK1`: 258
- `Package Quantity: 1`: 102
- `INSTRUMENT`: 90
- `FASCIA`: 87
- `Require Quantity: 02`: 83
- `BS`: 68
- `JV`: 53
- `GRILLE`: 48
- `OUTSIDE REAR VIEW(INCLUDES 1,2,5)(PAINT TO MATCH)`: 45
- `SWITCH`: 45
- `GENERATOR`: 44
- `MODULE KIT`: 44
- `NC`: 43
- `2(5B5)`: 40
- `2(A31)(EXC 5B5)`: 40
- `TAIL`: 34
- `CONTROL`: 31
- `HOOD`: 31
- `PUMP`: 31
- `FRONT BUMPER(PAINT TO MATCH)`: 30
- `REAR BUMPER(PAINT TO MATCH)`: 30
- `AK`: 27
- `FRONT SIDE DOOR WINDOW`: 27
- `HEATER & A/C`: 27
- `KE`: 27
- `OUTSIDE REAR VIEW`: 26
- `ZC`: 25
- `3(8B2)`: 24
- `OUTSIDE REAR VIEW(INCLUDES 2-6,8-15)`: 24

## Unmapped catalog models

- Buick Estate Wagon: feed 'Estate Wagon' 0 cars
- Buick Somerset: feed 'Somerset' 0 cars
- Cadillac CT4: feed 'CT4' 0 cars
- Cadillac Catera: feed 'Catera' 19 cars
- Cadillac Cimarron: feed 'Cimarron' 0 cars
- Cadillac Commercial Chassis: feed 'Commercial Chassis' 1 cars
- Cadillac XT4: feed 'XT4' 2 cars
- Cadillac XT6: feed 'XT6' 0 cars
- Chevrolet Aveo: feed 'Aveo' 610 cars
- Chevrolet Bolt EUV: feed 'Bolt EUV' 0 cars
- Chevrolet Cadet: feed 'Cadet' 0 cars
- Chevrolet Chevette: feed 'Chevette' 6 cars
- Chevrolet Citation: feed 'Citation' 3 cars
- Chevrolet El Camino: feed 'El Camino' 34 cars
- Chevrolet K30: feed 'K30' 0 cars
- Chevrolet P20: feed 'P20' 0 cars
- Chevrolet Prizm: feed 'Prizm' 88 cars
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
- Pontiac GTO: feed 'GTO' 3 cars
- Pontiac J2000: feed 'J2000' 0 cars
- Pontiac LeMans: feed 'LeMans' 4 cars
- Pontiac Parisienne: feed 'Parisienne' 4 cars
- Pontiac Phoenix: feed 'Phoenix' 2 cars
- Pontiac Safari: feed 'Safari' 2 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (2 cars, under catalog squash 'safari'); unmapped until a reviewed entry exists)
- Pontiac T1000: feed 'T1000' 0 cars
- Saturn LS2: feed 'LS2' 11 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (11 cars, under catalog squash 'ls'); unmapped until a reviewed entry exists)
- Saturn LW2: feed 'LW2' 12 cars
- Saturn LW300: feed 'LW300' 5 cars
- Saturn SC: feed 'SC' 31 cars
- Saturn SC1: feed 'SC1' 23 cars
- Saturn SC2: feed 'SC2' 27 cars
- Saturn SL: feed 'SL' 99 cars
- Saturn SL1: feed 'SL1' 83 cars
- Saturn SL2: feed 'SL2' 109 cars
- Saturn SW1: feed 'SW1' 4 cars
