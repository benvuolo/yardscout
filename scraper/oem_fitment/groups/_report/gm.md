# OEM curation report: gm

Raw: `c36da2eb98835c02f81c05e8c36b6a926634a332` @ `c36da2eb9883`; as of 2026-11-09T02:38:43Z.

- records 5875, classes 5875, list rows 95531, year manifests 424, cells 22215
- Verified groups 0, engine vg groups 0, Likely groups 279
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.gmpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.gmpartsgiant.com: only 0% of its 17867 fitment rows can be coverage: its option column holds trims (option_column_is_trims), which count only after a namespace audit (spec 5.2)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 11216 |
| ac-compressor | no_records | - | 3527 |
| ac-compressor | not_closed | ambig_target | 10515 |
| ac-compressor | not_closed | no_list_manifest | 12225 |
| ac-compressor | not_closed | no_year_manifest | 41322 |
| ac-compressor | not_closed | unattested | 34 |
| ac-compressor | not_closed | uncrawled_chain_member | 1107 |
| ac-compressor | not_closed | unverified_product | 1041 |
| ac-compressor | not_closed | variant_unread | 381 |
| ac-compressor | not_closed | year_manifest_bad | 7 |
| alternator | unmapped | - | 11216 |
| alternator | no_records | - | 4571 |
| alternator | not_closed | ambig_target | 10229 |
| alternator | not_closed | no_list_manifest | 12278 |
| alternator | not_closed | no_year_manifest | 40554 |
| alternator | not_closed | unread_sibling_page | 2139 |
| alternator | not_closed | variant_unread | 381 |
| alternator | not_closed | year_manifest_bad | 7 |
| bumper-front | unmapped | - | 11216 |
| bumper-front | no_records | - | 21999 |
| bumper-front | not_closed | ambig_target | 5797 |
| bumper-front | not_closed | no_list_manifest | 12319 |
| bumper-front | not_closed | no_year_manifest | 29663 |
| bumper-front | not_closed | variant_unread | 381 |
| bumper-rear | unmapped | - | 11216 |
| bumper-rear | no_records | - | 22820 |
| bumper-rear | not_closed | ambig_target | 6123 |
| bumper-rear | not_closed | no_list_manifest | 11680 |
| bumper-rear | not_closed | no_year_manifest | 29155 |
| bumper-rear | not_closed | variant_unread | 381 |
| climate-control | unmapped | - | 11216 |
| climate-control | no_records | - | 17104 |
| climate-control | not_closed | ambig_target | 10799 |
| climate-control | not_closed | no_list_manifest | 10503 |
| climate-control | not_closed | no_year_manifest | 29495 |
| climate-control | not_closed | unread_sibling_page | 1891 |
| climate-control | not_closed | variant_unread | 361 |
| climate-control | not_closed | year_manifest_bad | 6 |
| door-front | unmapped | - | 11216 |
| door-front | no_records | - | 15378 |
| door-front | not_closed | ambig_target | 10245 |
| door-front | not_closed | no_list_manifest | 11710 |
| door-front | not_closed | no_year_manifest | 32439 |
| door-front | not_closed | variant_unread | 381 |
| door-front | not_closed | year_manifest_bad | 6 |
| door-rear | unmapped | - | 11216 |
| door-rear | no_records | - | 23429 |
| door-rear | not_closed | ambig_target | 5746 |
| door-rear | not_closed | no_list_manifest | 11330 |
| door-rear | not_closed | no_year_manifest | 29267 |
| door-rear | not_closed | variant_unread | 381 |
| door-rear | not_closed | year_manifest_bad | 6 |
| fender | unmapped | - | 11216 |
| fender | no_records | - | 29951 |
| fender | not_closed | ambig_target | 5838 |
| fender | not_closed | no_list_manifest | 9955 |
| fender | not_closed | no_year_manifest | 24048 |
| fender | not_closed | variant_unread | 361 |
| fender | not_closed | year_manifest_bad | 6 |
| fuel-pump-module | unmapped | - | 11216 |
| fuel-pump-module | no_records | - | 7157 |
| fuel-pump-module | not_closed | ambig_target | 10282 |
| fuel-pump-module | not_closed | no_list_manifest | 12307 |
| fuel-pump-module | not_closed | no_year_manifest | 37844 |
| fuel-pump-module | not_closed | unread_sibling_page | 2181 |
| fuel-pump-module | not_closed | variant_unread | 381 |
| fuel-pump-module | not_closed | year_manifest_bad | 7 |
| gauge-cluster | unmapped | - | 11216 |
| gauge-cluster | no_records | - | 36862 |
| gauge-cluster | not_closed | ambig_target | 6569 |
| gauge-cluster | not_closed | no_list_manifest | 11354 |
| gauge-cluster | not_closed | no_year_manifest | 15013 |
| gauge-cluster | not_closed | variant_unread | 361 |
| grille | unmapped | - | 11216 |
| grille | no_records | - | 21976 |
| grille | not_closed | ambig_target | 6449 |
| grille | not_closed | no_list_manifest | 11636 |
| grille | not_closed | no_year_manifest | 29737 |
| grille | not_closed | variant_unread | 361 |
| headlights | unmapped | - | 11216 |
| headlights | no_records | - | 10011 |
| headlights | not_closed | ambig_target | 10739 |
| headlights | not_closed | no_list_manifest | 11633 |
| headlights | not_closed | no_year_manifest | 35207 |
| headlights | not_closed | unattested | 592 |
| headlights | not_closed | uncrawled_chain_member | 712 |
| headlights | not_closed | unread_sibling_page | 827 |
| headlights | not_closed | unverified_product | 51 |
| headlights | not_closed | variant_unread | 381 |
| headlights | not_closed | year_manifest_bad | 6 |
| hood | unmapped | - | 11216 |
| hood | no_records | - | 26030 |
| hood | not_closed | ambig_target | 5838 |
| hood | not_closed | no_list_manifest | 10964 |
| hood | not_closed | no_year_manifest | 26960 |
| hood | not_closed | variant_unread | 361 |
| hood | not_closed | year_manifest_bad | 6 |
| ignition-coils | unmapped | - | 11216 |
| ignition-coils | no_records | - | 6340 |
| ignition-coils | not_closed | ambig_target | 9335 |
| ignition-coils | not_closed | no_list_manifest | 13862 |
| ignition-coils | not_closed | no_year_manifest | 40234 |
| ignition-coils | not_closed | variant_unread | 381 |
| ignition-coils | not_closed | year_manifest_bad | 7 |
| liftgate | unmapped | - | 11216 |
| liftgate | no_records | - | 48311 |
| liftgate | not_closed | ambig_target | 4390 |
| liftgate | not_closed | no_list_manifest | 4218 |
| liftgate | not_closed | no_year_manifest | 13214 |
| liftgate | not_closed | variant_unread | 20 |
| liftgate | not_closed | year_manifest_bad | 6 |
| power-steering-pump | unmapped | - | 11216 |
| power-steering-pump | no_records | - | 17754 |
| power-steering-pump | not_closed | ambig_target | 10729 |
| power-steering-pump | not_closed | no_list_manifest | 8036 |
| power-steering-pump | not_closed | no_year_manifest | 31639 |
| power-steering-pump | not_closed | unread_sibling_page | 1821 |
| power-steering-pump | not_closed | variant_unread | 173 |
| power-steering-pump | not_closed | year_manifest_bad | 7 |
| radiator | unmapped | - | 11216 |
| radiator | no_records | - | 11017 |
| radiator | not_closed | ambig_target | 10563 |
| radiator | not_closed | no_list_manifest | 12875 |
| radiator | not_closed | no_year_manifest | 35317 |
| radiator | not_closed | variant_unread | 381 |
| radiator | not_closed | year_manifest_bad | 6 |
| side-mirrors | unmapped | - | 11216 |
| side-mirrors | no_records | - | 3133 |
| side-mirrors | not_closed | ambig_target | 10829 |
| side-mirrors | not_closed | no_list_manifest | 12425 |
| side-mirrors | not_closed | no_year_manifest | 41202 |
| side-mirrors | not_closed | unread_sibling_page | 2182 |
| side-mirrors | not_closed | variant_unread | 381 |
| side-mirrors | not_closed | year_manifest_bad | 7 |
| starter | unmapped | - | 11216 |
| starter | no_records | - | 2262 |
| starter | not_closed | ambig_target | 10947 |
| starter | not_closed | no_list_manifest | 12155 |
| starter | not_closed | no_year_manifest | 42226 |
| starter | not_closed | unread_sibling_page | 2181 |
| starter | not_closed | variant_unread | 381 |
| starter | not_closed | year_manifest_bad | 7 |
| tail-lights | unmapped | - | 11216 |
| tail-lights | no_records | - | 5608 |
| tail-lights | not_closed | ambig_target | 10711 |
| tail-lights | not_closed | no_list_manifest | 12197 |
| tail-lights | not_closed | no_year_manifest | 39074 |
| tail-lights | not_closed | unattested | 598 |
| tail-lights | not_closed | uncrawled_chain_member | 1430 |
| tail-lights | not_closed | unverified_product | 154 |
| tail-lights | not_closed | variant_unread | 381 |
| tail-lights | not_closed | year_manifest_bad | 6 |
| tailgate | unmapped | - | 11216 |
| tailgate | no_records | - | 64453 |
| tailgate | not_closed | ambig_target | 4148 |
| tailgate | not_closed | no_list_manifest | 110 |
| tailgate | not_closed | no_year_manifest | 1448 |
| throttle-body | unmapped | - | 11216 |
| throttle-body | no_records | - | 24452 |
| throttle-body | not_closed | ambig_target | 10263 |
| throttle-body | not_closed | no_list_manifest | 7377 |
| throttle-body | not_closed | no_year_manifest | 25881 |
| throttle-body | not_closed | unattested | 1046 |
| throttle-body | not_closed | uncrawled_chain_member | 849 |
| throttle-body | not_closed | unverified_product | 285 |
| throttle-body | not_closed | year_manifest_bad | 6 |
| trunk-lid | unmapped | - | 11216 |
| trunk-lid | no_records | - | 48210 |
| trunk-lid | not_closed | no_list_manifest | 6776 |
| trunk-lid | not_closed | no_year_manifest | 14812 |
| trunk-lid | not_closed | variant_unread | 361 |
| window-regulator | unmapped | - | 11216 |
| window-regulator | no_records | - | 1926 |
| window-regulator | not_closed | ambig_target | 10754 |
| window-regulator | not_closed | no_list_manifest | 12438 |
| window-regulator | not_closed | no_year_manifest | 42479 |
| window-regulator | not_closed | unattested | 33 |
| window-regulator | not_closed | uncrawled_chain_member | 669 |
| window-regulator | not_closed | unread_sibling_page | 1288 |
| window-regulator | not_closed | unverified_product | 184 |
| window-regulator | not_closed | variant_unread | 381 |
| window-regulator | not_closed | year_manifest_bad | 7 |
| window-switch | unmapped | - | 11216 |
| window-switch | no_records | - | 7754 |
| window-switch | not_closed | ambig_target | 10804 |
| window-switch | not_closed | no_list_manifest | 11631 |
| window-switch | not_closed | no_year_manifest | 37409 |
| window-switch | not_closed | unattested | 139 |
| window-switch | not_closed | uncrawled_chain_member | 649 |
| window-switch | not_closed | unread_sibling_page | 1064 |
| window-switch | not_closed | unverified_product | 322 |
| window-switch | not_closed | variant_unread | 381 |
| window-switch | not_closed | year_manifest_bad | 6 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 11216 |
| ac-compressor | no_records | - | 3527 |
| ac-compressor | split | no_candidates | 66 |
| ac-compressor | split | option_split | 40976 |
| ac-compressor | conditional | conditional:engine_unattested | 16709 |
| ac-compressor | conditional | conditional:option | 152 |
| ac-compressor | conditional | conditional:qualifier | 8729 |
| alternator | unmapped | - | 11216 |
| alternator | no_records | - | 4571 |
| alternator | split | no_candidates | 7 |
| alternator | split | option_split | 46491 |
| alternator | conditional | conditional:engine_unattested | 17450 |
| alternator | conditional | conditional:qualifier | 1640 |
| bumper-front | unmapped | - | 11216 |
| bumper-front | no_records | - | 21999 |
| bumper-front | split | option_split | 41434 |
| bumper-front | conditional | conditional:engine_unattested | 6450 |
| bumper-front | conditional | conditional:qualifier | 276 |
| bumper-rear | unmapped | - | 11216 |
| bumper-rear | no_records | - | 22820 |
| bumper-rear | split | option_split | 38599 |
| bumper-rear | conditional | conditional:engine_unattested | 4406 |
| bumper-rear | conditional | conditional:qualifier | 4334 |
| climate-control | unmapped | - | 11216 |
| climate-control | no_records | - | 17104 |
| climate-control | split | no_candidates | 439 |
| climate-control | split | option_split | 43439 |
| climate-control | conditional | conditional:engine_unattested | 7578 |
| climate-control | conditional | conditional:option | 1590 |
| climate-control | conditional | conditional:qualifier | 9 |
| door-front | unmapped | - | 11216 |
| door-front | no_records | - | 15378 |
| door-front | split | option_split | 7790 |
| door-front | split | slot_missing | 6075 |
| door-front | conditional | conditional:engine_unattested | 29609 |
| door-front | conditional | conditional:option | 189 |
| door-front | conditional | conditional:qualifier | 11118 |
| door-rear | unmapped | - | 11216 |
| door-rear | no_records | - | 23429 |
| door-rear | split | option_split | 10698 |
| door-rear | split | slot_missing | 3113 |
| door-rear | conditional | conditional:engine_unattested | 15840 |
| door-rear | conditional | conditional:option | 373 |
| door-rear | conditional | conditional:qualifier | 16706 |
| fender | unmapped | - | 11216 |
| fender | no_records | - | 29951 |
| fender | split | option_split | 7168 |
| fender | conditional | conditional:engine_unattested | 25578 |
| fender | conditional | conditional:option | 521 |
| fender | conditional | conditional:qualifier | 6941 |
| fuel-pump-module | unmapped | - | 11216 |
| fuel-pump-module | no_records | - | 7157 |
| fuel-pump-module | split | no_candidates | 358 |
| fuel-pump-module | split | option_split | 48206 |
| fuel-pump-module | conditional | conditional:engine_unattested | 6695 |
| fuel-pump-module | conditional | conditional:qualifier | 7743 |
| gauge-cluster | unmapped | - | 11216 |
| gauge-cluster | no_records | - | 36862 |
| gauge-cluster | split | option_split | 31621 |
| gauge-cluster | conditional | conditional:engine_unattested | 1676 |
| grille | unmapped | - | 11216 |
| grille | no_records | - | 21976 |
| grille | split | option_split | 41418 |
| grille | conditional | conditional:engine_unattested | 3804 |
| grille | conditional | conditional:qualifier | 2961 |
| headlights | unmapped | - | 11216 |
| headlights | no_records | - | 10011 |
| headlights | split | no_candidates | 315 |
| headlights | split | option_split | 28048 |
| headlights | split | position_missing | 393 |
| headlights | split | slot_missing | 164 |
| headlights | conditional | conditional:engine_unattested | 16226 |
| headlights | conditional | conditional:option | 853 |
| headlights | conditional | conditional:qualifier | 14149 |
| hood | unmapped | - | 11216 |
| hood | no_records | - | 26030 |
| hood | split | option_split | 4749 |
| hood | conditional | conditional:engine_unattested | 34545 |
| hood | conditional | conditional:qualifier | 4835 |
| ignition-coils | unmapped | - | 11216 |
| ignition-coils | no_records | - | 6340 |
| ignition-coils | split | option_split | 40248 |
| ignition-coils | conditional | conditional:engine_unattested | 20180 |
| ignition-coils | conditional | conditional:package | 635 |
| ignition-coils | conditional | conditional:qualifier | 2756 |
| liftgate | unmapped | - | 11216 |
| liftgate | no_records | - | 48311 |
| liftgate | split | option_split | 686 |
| liftgate | conditional | conditional:engine_unattested | 12810 |
| liftgate | conditional | conditional:qualifier | 8352 |
| power-steering-pump | unmapped | - | 11216 |
| power-steering-pump | no_records | - | 17754 |
| power-steering-pump | split | no_candidates | 35 |
| power-steering-pump | split | option_split | 27954 |
| power-steering-pump | conditional | conditional:engine_unattested | 18142 |
| power-steering-pump | conditional | conditional:qualifier | 6274 |
| radiator | unmapped | - | 11216 |
| radiator | no_records | - | 11017 |
| radiator | split | option_split | 47475 |
| radiator | conditional | conditional:engine_unattested | 8971 |
| radiator | conditional | conditional:qualifier | 2696 |
| side-mirrors | unmapped | - | 11216 |
| side-mirrors | no_records | - | 3133 |
| side-mirrors | split | no_candidates | 1 |
| side-mirrors | split | option_split | 61320 |
| side-mirrors | split | position_missing | 14 |
| side-mirrors | split | slot_missing | 123 |
| side-mirrors | conditional | conditional:engine_unattested | 4676 |
| side-mirrors | conditional | conditional:option | 530 |
| side-mirrors | conditional | conditional:qualifier | 362 |
| starter | unmapped | - | 11216 |
| starter | no_records | - | 2262 |
| starter | split | no_candidates | 195 |
| starter | split | option_split | 38671 |
| starter | conditional | conditional:engine_unattested | 17202 |
| starter | conditional | conditional:option | 306 |
| starter | conditional | conditional:qualifier | 11523 |
| tail-lights | unmapped | - | 11216 |
| tail-lights | no_records | - | 5608 |
| tail-lights | split | no_candidates | 279 |
| tail-lights | split | option_split | 39477 |
| tail-lights | split | position_missing | 982 |
| tail-lights | split | slot_missing | 429 |
| tail-lights | conditional | conditional:engine_unattested | 22545 |
| tail-lights | conditional | conditional:option | 67 |
| tail-lights | conditional | conditional:qualifier | 772 |
| tailgate | unmapped | - | 11216 |
| tailgate | no_records | - | 64453 |
| tailgate | split | option_split | 4704 |
| tailgate | conditional | conditional:engine_unattested | 1002 |
| throttle-body | unmapped | - | 11216 |
| throttle-body | no_records | - | 24452 |
| throttle-body | split | no_candidates | 809 |
| throttle-body | split | option_split | 23953 |
| throttle-body | conditional | conditional:engine_unattested | 5520 |
| throttle-body | conditional | conditional:qualifier | 15425 |
| trunk-lid | unmapped | - | 11216 |
| trunk-lid | no_records | - | 48210 |
| trunk-lid | split | option_split | 8831 |
| trunk-lid | conditional | conditional:engine_unattested | 11630 |
| trunk-lid | conditional | conditional:qualifier | 1488 |
| window-regulator | unmapped | - | 11216 |
| window-regulator | no_records | - | 1926 |
| window-regulator | split | no_candidates | 50 |
| window-regulator | split | packaging_incomplete | 3739 |
| window-regulator | split | packaging_split | 19580 |
| window-regulator | split | packaging_unstated | 44455 |
| window-regulator | split | slot_missing | 13 |
| window-regulator | conditional | conditional:engine_unattested | 360 |
| window-regulator | conditional | conditional:option | 36 |
| window-switch | unmapped | - | 11216 |
| window-switch | no_records | - | 7754 |
| window-switch | split | no_candidates | 443 |
| window-switch | split | option_split | 41858 |
| window-switch | split | position_missing | 12974 |
| window-switch | conditional | conditional:engine_unattested | 4331 |
| window-switch | conditional | conditional:option | 102 |
| window-switch | conditional | conditional:qualifier | 2697 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 17
- held_exterior_cross_model: 17
- recrawl_resolved: 1
- rule_drift: 2
- universal_part_suspect: 198

## Unknown note clauses (top 30)

- `2`: 957
- `CK1`: 479
- `Package Quantity: 1`: 118
- `FASCIA`: 89
- `Require Quantity: 02`: 89
- `2(5B5)`: 80
- `2(A31)(EXC 5B5)`: 80
- `BS`: 68
- `INSTRUMENT`: 64
- `JV`: 52
- `GRILLE`: 50
- `SWITCH`: 47
- `MODULE KIT`: 46
- `GENERATOR`: 44
- `NC`: 43
- `CONTROL`: 35
- `HOOD`: 35
- `PUMP`: 33
- `3(X88,Z88,5B5)`: 32
- `FRONT BUMPER(PAINT TO MATCH)`: 31
- `HEATER & A/C`: 30
- `REAR BUMPER(PAINT TO MATCH)`: 30
- `FRONT SIDE DOOR WINDOW`: 27
- `OUTSIDE REAR VIEW(INCLUDES 1,2,5)(PAINT TO MATCH)`: 26
- `ZC`: 25
- `3(5B5)`: 24
- `3(8B2)`: 24
- `3(A31)(EXC 5B5)`: 24
- `REAR SIDE DOOR WINDOW`: 24
- `TAIL`: 24

## Unmapped catalog models

- Buick Estate Wagon: feed 'Estate Wagon' 0 cars
- Buick Somerset: feed 'Somerset' 0 cars
- Cadillac CT4: feed 'CT4' 0 cars
- Cadillac Catera: feed 'Catera' 20 cars
- Cadillac Cimarron: feed 'Cimarron' 0 cars
- Cadillac Commercial Chassis: feed 'Commercial Chassis' 1 cars
- Cadillac XT4: feed 'XT4' 1 cars
- Cadillac XT6: feed 'XT6' 0 cars
- Chevrolet Bolt EUV: feed 'Bolt EUV' 0 cars
- Chevrolet Cadet: feed 'Cadet' 0 cars
- Chevrolet Chevette: feed 'Chevette' 6 cars
- Chevrolet Citation: feed 'Citation' 3 cars
- Chevrolet El Camino: feed 'El Camino' 34 cars
- Chevrolet K30: feed 'K30' 0 cars
- Chevrolet P20: feed 'P20' 0 cars
- Chevrolet Prizm: feed 'Prizm' 87 cars
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
- Saturn SL2: feed 'SL2' 110 cars
- Saturn SW1: feed 'SW1' 4 cars
- Saturn SW2: feed 'SW2' 24 cars
