# OEM curation report: nissan

Raw: `57e8b5b99de0` @ `57e8b5b99de0`; as of 2026-11-14T11:38:15Z.

- records 7778, classes 7552, list rows 75222, year manifests 457, cells 9944
- Verified groups 0, engine vg groups 0, Likely groups 226
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.infinitipartsdeal.com, www.nissanpartsdeal.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.infinitipartsdeal.com: only 0% of its 4664 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)
- www.nissanpartsdeal.com: only 0% of its 6335 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 1355 |
| ac-compressor | no_records | - | 3061 |
| ac-compressor | not_closed | no_list_manifest | 19895 |
| ac-compressor | not_closed | no_year_manifest | 3714 |
| ac-compressor | not_closed | variant_unread | 4202 |
| ac-compressor | not_closed | year_manifest_bad | 1257 |
| alternator | unmapped | - | 1355 |
| alternator | no_records | - | 1186 |
| alternator | not_closed | no_list_manifest | 21246 |
| alternator | not_closed | no_year_manifest | 4235 |
| alternator | not_closed | variant_unread | 4222 |
| alternator | not_closed | year_manifest_bad | 1240 |
| bumper-front | unmapped | - | 1355 |
| bumper-front | no_records | - | 2327 |
| bumper-front | not_closed | no_list_manifest | 19240 |
| bumper-front | not_closed | no_year_manifest | 3878 |
| bumper-front | not_closed | unread_sibling_page | 1243 |
| bumper-front | not_closed | variant_unread | 4191 |
| bumper-front | not_closed | year_manifest_bad | 1250 |
| bumper-rear | unmapped | - | 1355 |
| bumper-rear | no_records | - | 2614 |
| bumper-rear | not_closed | no_list_manifest | 19417 |
| bumper-rear | not_closed | no_year_manifest | 4256 |
| bumper-rear | not_closed | unread_sibling_page | 401 |
| bumper-rear | not_closed | variant_unread | 4191 |
| bumper-rear | not_closed | year_manifest_bad | 1250 |
| climate-control | unmapped | - | 1355 |
| climate-control | no_records | - | 6481 |
| climate-control | not_closed | no_list_manifest | 14852 |
| climate-control | not_closed | no_year_manifest | 3681 |
| climate-control | not_closed | unread_sibling_page | 2157 |
| climate-control | not_closed | variant_unread | 4017 |
| climate-control | not_closed | year_manifest_bad | 941 |
| door-front | unmapped | - | 1355 |
| door-front | no_records | - | 1390 |
| door-front | not_closed | no_list_manifest | 16991 |
| door-front | not_closed | no_year_manifest | 4129 |
| door-front | not_closed | unread_sibling_page | 4176 |
| door-front | not_closed | variant_unread | 4191 |
| door-front | not_closed | year_manifest_bad | 1252 |
| door-rear | unmapped | - | 1355 |
| door-rear | no_records | - | 1582 |
| door-rear | not_closed | no_list_manifest | 19642 |
| door-rear | not_closed | no_year_manifest | 4347 |
| door-rear | not_closed | unread_sibling_page | 1110 |
| door-rear | not_closed | variant_unread | 4191 |
| door-rear | not_closed | year_manifest_bad | 1257 |
| fender | unmapped | - | 1355 |
| fender | no_records | - | 1096 |
| fender | not_closed | no_list_manifest | 18525 |
| fender | not_closed | no_year_manifest | 4513 |
| fender | not_closed | unattested | 207 |
| fender | not_closed | uncrawled_chain_member | 314 |
| fender | not_closed | unread_sibling_page | 2015 |
| fender | not_closed | variant_unread | 4191 |
| fender | not_closed | year_manifest_bad | 1268 |
| fuel-pump-module | unmapped | - | 1355 |
| fuel-pump-module | no_records | - | 1850 |
| fuel-pump-module | not_closed | no_list_manifest | 20965 |
| fuel-pump-module | not_closed | no_year_manifest | 3837 |
| fuel-pump-module | not_closed | variant_unread | 4191 |
| fuel-pump-module | not_closed | year_manifest_bad | 1286 |
| gauge-cluster | unmapped | - | 1355 |
| gauge-cluster | no_records | - | 2332 |
| gauge-cluster | not_closed | no_list_manifest | 16807 |
| gauge-cluster | not_closed | no_year_manifest | 3513 |
| gauge-cluster | not_closed | unread_sibling_page | 3932 |
| gauge-cluster | not_closed | variant_unread | 4304 |
| gauge-cluster | not_closed | year_manifest_bad | 1241 |
| grille | unmapped | - | 1355 |
| grille | no_records | - | 12489 |
| grille | not_closed | no_list_manifest | 12941 |
| grille | not_closed | no_year_manifest | 1937 |
| grille | not_closed | unattested | 2204 |
| grille | not_closed | uncrawled_chain_member | 222 |
| grille | not_closed | unverified_product | 34 |
| grille | not_closed | variant_unread | 1049 |
| grille | not_closed | year_manifest_bad | 1253 |
| headlights | unmapped | - | 1355 |
| headlights | no_records | - | 2133 |
| headlights | not_closed | no_list_manifest | 17817 |
| headlights | not_closed | no_year_manifest | 3632 |
| headlights | not_closed | suspect_variant | 119 |
| headlights | not_closed | unattested | 1351 |
| headlights | not_closed | uncrawled_chain_member | 1465 |
| headlights | not_closed | unread_sibling_page | 171 |
| headlights | not_closed | variant_unread | 4191 |
| headlights | not_closed | year_manifest_bad | 1250 |
| hood | unmapped | - | 1355 |
| hood | no_records | - | 1190 |
| hood | not_closed | no_list_manifest | 18200 |
| hood | not_closed | no_year_manifest | 4286 |
| hood | not_closed | unread_sibling_page | 3004 |
| hood | not_closed | variant_unread | 4191 |
| hood | not_closed | year_manifest_bad | 1258 |
| ignition-coils | unmapped | - | 1355 |
| ignition-coils | no_records | - | 2420 |
| ignition-coils | not_closed | no_list_manifest | 19973 |
| ignition-coils | not_closed | no_year_manifest | 4243 |
| ignition-coils | not_closed | variant_unread | 4222 |
| ignition-coils | not_closed | year_manifest_bad | 1271 |
| knuckle | unmapped | - | 1355 |
| knuckle | no_records | - | 666 |
| knuckle | not_closed | list_manifest_bad | 588 |
| knuckle | not_closed | no_list_manifest | 11697 |
| knuckle | not_closed | no_year_manifest | 4603 |
| knuckle | not_closed | unattested | 3815 |
| knuckle | not_closed | uncrawled_chain_member | 4175 |
| knuckle | not_closed | unverified_product | 1143 |
| knuckle | not_closed | variant_unread | 4191 |
| knuckle | not_closed | year_manifest_bad | 1251 |
| liftgate | unmapped | - | 1355 |
| liftgate | no_records | - | 20872 |
| liftgate | not_closed | no_list_manifest | 7534 |
| liftgate | not_closed | no_year_manifest | 2205 |
| liftgate | not_closed | unattested | 209 |
| liftgate | not_closed | uncrawled_chain_member | 255 |
| liftgate | not_closed | variant_unread | 1042 |
| liftgate | not_closed | year_manifest_bad | 12 |
| power-steering-pump | unmapped | - | 1355 |
| power-steering-pump | no_records | - | 11227 |
| power-steering-pump | not_closed | no_list_manifest | 14661 |
| power-steering-pump | not_closed | no_year_manifest | 2771 |
| power-steering-pump | not_closed | variant_unread | 3149 |
| power-steering-pump | not_closed | year_manifest_bad | 321 |
| radiator | unmapped | - | 1355 |
| radiator | no_records | - | 1102 |
| radiator | not_closed | no_list_manifest | 21034 |
| radiator | not_closed | no_year_manifest | 4427 |
| radiator | not_closed | variant_unread | 4305 |
| radiator | not_closed | year_manifest_bad | 1261 |
| side-mirrors | unmapped | - | 1355 |
| side-mirrors | no_records | - | 1058 |
| side-mirrors | not_closed | no_list_manifest | 16363 |
| side-mirrors | not_closed | no_year_manifest | 4444 |
| side-mirrors | not_closed | suspect_variant | 64 |
| side-mirrors | not_closed | unattested | 1594 |
| side-mirrors | not_closed | uncrawled_chain_member | 1855 |
| side-mirrors | not_closed | unverified_product | 1307 |
| side-mirrors | not_closed | variant_unread | 4191 |
| side-mirrors | not_closed | year_manifest_bad | 1253 |
| starter | unmapped | - | 1355 |
| starter | no_records | - | 886 |
| starter | not_closed | no_list_manifest | 21295 |
| starter | not_closed | no_year_manifest | 4433 |
| starter | not_closed | variant_unread | 4275 |
| starter | not_closed | year_manifest_bad | 1240 |
| strut | unmapped | - | 1355 |
| strut | no_records | - | 1066 |
| strut | not_closed | list_manifest_bad | 588 |
| strut | not_closed | no_list_manifest | 11349 |
| strut | not_closed | no_year_manifest | 4552 |
| strut | not_closed | unverified_product | 9133 |
| strut | not_closed | variant_unread | 4190 |
| strut | not_closed | year_manifest_bad | 1251 |
| tail-lights | unmapped | - | 1355 |
| tail-lights | no_records | - | 2513 |
| tail-lights | not_closed | no_list_manifest | 19620 |
| tail-lights | not_closed | no_year_manifest | 3446 |
| tail-lights | not_closed | suspect_variant | 42 |
| tail-lights | not_closed | unattested | 737 |
| tail-lights | not_closed | uncrawled_chain_member | 254 |
| tail-lights | not_closed | unread_sibling_page | 74 |
| tail-lights | not_closed | variant_unread | 4191 |
| tail-lights | not_closed | year_manifest_bad | 1252 |
| tailgate | unmapped | - | 1355 |
| tailgate | no_records | - | 30844 |
| tailgate | not_closed | no_list_manifest | 1276 |
| tailgate | not_closed | no_year_manifest | 9 |
| throttle-body | unmapped | - | 1355 |
| throttle-body | no_records | - | 950 |
| throttle-body | not_closed | no_list_manifest | 21230 |
| throttle-body | not_closed | no_year_manifest | 4473 |
| throttle-body | not_closed | variant_unread | 4222 |
| throttle-body | not_closed | year_manifest_bad | 1254 |
| trunk-lid | unmapped | - | 1355 |
| trunk-lid | no_records | - | 12677 |
| trunk-lid | not_closed | no_list_manifest | 12348 |
| trunk-lid | not_closed | no_year_manifest | 2205 |
| trunk-lid | not_closed | unread_sibling_page | 504 |
| trunk-lid | not_closed | variant_unread | 3149 |
| trunk-lid | not_closed | year_manifest_bad | 1246 |
| window-regulator | unmapped | - | 1355 |
| window-regulator | no_records | - | 568 |
| window-regulator | not_closed | list_manifest_bad | 1084 |
| window-regulator | not_closed | no_list_manifest | 4698 |
| window-regulator | not_closed | no_year_manifest | 4570 |
| window-regulator | not_closed | uncrawled_chain_member | 496 |
| window-regulator | not_closed | unread_sibling_page | 15146 |
| window-regulator | not_closed | variant_unread | 4222 |
| window-regulator | not_closed | year_manifest_bad | 1345 |
| window-switch | unmapped | - | 1355 |
| window-switch | no_records | - | 1684 |
| window-switch | not_closed | no_list_manifest | 20714 |
| window-switch | not_closed | no_year_manifest | 4196 |
| window-switch | not_closed | variant_unread | 4267 |
| window-switch | not_closed | year_manifest_bad | 1268 |
| wiper-motor | unmapped | - | 1355 |
| wiper-motor | no_records | - | 658 |
| wiper-motor | not_closed | list_manifest_bad | 588 |
| wiper-motor | not_closed | no_list_manifest | 11690 |
| wiper-motor | not_closed | no_year_manifest | 4613 |
| wiper-motor | not_closed | unattested | 4461 |
| wiper-motor | not_closed | uncrawled_chain_member | 4021 |
| wiper-motor | not_closed | unverified_product | 651 |
| wiper-motor | not_closed | variant_unread | 4190 |
| wiper-motor | not_closed | year_manifest_bad | 1257 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 1355 |
| ac-compressor | no_records | - | 3061 |
| ac-compressor | split | option_split | 20812 |
| ac-compressor | conditional | conditional:engine_unattested | 8226 |
| ac-compressor | conditional | conditional:option | 30 |
| alternator | unmapped | - | 1355 |
| alternator | no_records | - | 1186 |
| alternator | split | option_split | 20437 |
| alternator | conditional | conditional:engine_unattested | 10506 |
| bumper-front | unmapped | - | 1355 |
| bumper-front | no_records | - | 2327 |
| bumper-front | split | option_split | 22059 |
| bumper-front | conditional | conditional:colour | 101 |
| bumper-front | conditional | conditional:engine_unattested | 7642 |
| bumper-rear | unmapped | - | 1355 |
| bumper-rear | no_records | - | 2614 |
| bumper-rear | split | option_split | 22606 |
| bumper-rear | conditional | conditional:engine_unattested | 6813 |
| bumper-rear | conditional | conditional:option | 96 |
| climate-control | unmapped | - | 1355 |
| climate-control | no_records | - | 6481 |
| climate-control | split | option_split | 21281 |
| climate-control | conditional | conditional:engine_unattested | 4343 |
| climate-control | conditional | conditional:package | 24 |
| door-front | unmapped | - | 1355 |
| door-front | no_records | - | 1390 |
| door-front | split | option_split | 18173 |
| door-front | conditional | conditional:engine_unattested | 12285 |
| door-front | conditional | conditional:option | 281 |
| door-rear | unmapped | - | 1355 |
| door-rear | no_records | - | 1582 |
| door-rear | split | option_split | 7698 |
| door-rear | split | slot_missing | 35 |
| door-rear | conditional | conditional:engine_unattested | 21908 |
| door-rear | conditional | conditional:option | 906 |
| fender | unmapped | - | 1355 |
| fender | no_records | - | 1096 |
| fender | split | option_split | 15878 |
| fender | split | slot_missing | 2 |
| fender | conditional | conditional:engine_unattested | 15153 |
| fuel-pump-module | unmapped | - | 1355 |
| fuel-pump-module | no_records | - | 1850 |
| fuel-pump-module | split | option_split | 18589 |
| fuel-pump-module | conditional | conditional:engine_unattested | 11687 |
| fuel-pump-module | conditional | conditional:option | 3 |
| gauge-cluster | unmapped | - | 1355 |
| gauge-cluster | no_records | - | 2332 |
| gauge-cluster | split | option_split | 28897 |
| gauge-cluster | conditional | conditional:engine_unattested | 852 |
| gauge-cluster | conditional | conditional:option | 48 |
| grille | unmapped | - | 1355 |
| grille | no_records | - | 12489 |
| grille | split | option_split | 13775 |
| grille | conditional | conditional:engine_unattested | 5688 |
| grille | conditional | conditional:option | 177 |
| headlights | unmapped | - | 1355 |
| headlights | no_records | - | 2133 |
| headlights | split | option_split | 24083 |
| headlights | conditional | conditional:engine_unattested | 5913 |
| hood | unmapped | - | 1355 |
| hood | no_records | - | 1190 |
| hood | split | option_split | 8327 |
| hood | conditional | conditional:engine_unattested | 22607 |
| hood | conditional | conditional:option | 5 |
| ignition-coils | unmapped | - | 1355 |
| ignition-coils | no_records | - | 2420 |
| ignition-coils | split | option_split | 19297 |
| ignition-coils | conditional | conditional:engine_unattested | 10112 |
| ignition-coils | conditional | conditional:package | 300 |
| knuckle | unmapped | - | 1355 |
| knuckle | no_records | - | 666 |
| knuckle | split | no_candidates | 17 |
| knuckle | split | option_split | 31446 |
| liftgate | unmapped | - | 1355 |
| liftgate | no_records | - | 20872 |
| liftgate | split | option_split | 10513 |
| liftgate | conditional | conditional:engine_unattested | 744 |
| power-steering-pump | unmapped | - | 1355 |
| power-steering-pump | no_records | - | 11227 |
| power-steering-pump | split | option_split | 12101 |
| power-steering-pump | conditional | conditional:engine_unattested | 8723 |
| power-steering-pump | conditional | conditional:option | 78 |
| radiator | unmapped | - | 1355 |
| radiator | no_records | - | 1102 |
| radiator | split | option_split | 21746 |
| radiator | conditional | conditional:engine_unattested | 9281 |
| side-mirrors | unmapped | - | 1355 |
| side-mirrors | no_records | - | 1058 |
| side-mirrors | split | option_split | 28834 |
| side-mirrors | split | slot_missing | 4 |
| side-mirrors | conditional | conditional:engine_unattested | 2233 |
| starter | unmapped | - | 1355 |
| starter | no_records | - | 886 |
| starter | split | option_split | 21562 |
| starter | conditional | conditional:engine_unattested | 9681 |
| strut | unmapped | - | 1355 |
| strut | no_records | - | 1066 |
| strut | split | option_split | 30748 |
| strut | conditional | conditional:engine_unattested | 315 |
| tail-lights | unmapped | - | 1355 |
| tail-lights | no_records | - | 2513 |
| tail-lights | split | option_split | 22467 |
| tail-lights | conditional | conditional:engine_unattested | 7104 |
| tail-lights | conditional | conditional:package | 45 |
| tailgate | unmapped | - | 1355 |
| tailgate | no_records | - | 30844 |
| tailgate | split | option_split | 285 |
| tailgate | conditional | conditional:engine_unattested | 1000 |
| throttle-body | unmapped | - | 1355 |
| throttle-body | no_records | - | 950 |
| throttle-body | split | option_split | 21929 |
| throttle-body | conditional | conditional:engine_unattested | 9250 |
| trunk-lid | unmapped | - | 1355 |
| trunk-lid | no_records | - | 12677 |
| trunk-lid | split | option_split | 18909 |
| trunk-lid | conditional | conditional:engine_unattested | 543 |
| window-regulator | unmapped | - | 1355 |
| window-regulator | no_records | - | 568 |
| window-regulator | split | packaging_unstated | 31561 |
| window-switch | unmapped | - | 1355 |
| window-switch | no_records | - | 1684 |
| window-switch | split | no_candidates | 8 |
| window-switch | split | option_split | 21151 |
| window-switch | split | position_missing | 9286 |
| wiper-motor | unmapped | - | 1355 |
| wiper-motor | no_records | - | 658 |
| wiper-motor | split | option_split | 19455 |
| wiper-motor | split | packaging_split | 92 |
| wiper-motor | split | slot_missing | 152 |
| wiper-motor | conditional | conditional:engine_unattested | 11772 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 127
- disputed_class: 226
- held_drive_qualifier: 62
- held_engine_conflict: 47
- held_exterior_cross_model: 279
- held_market_kph: 62
- held_window_note_cap: 26
- strict_note: 1
- strict_slot_split: 9
- universal_part_suspect: 15

## Unknown note clauses (top 30)

- `Package Quantity: 1`: 403
- `NO PAINT`: 339
- `Require Quantity: 02`: 324
- `Production Date: 04/2007-04/2008`: 217
- `Production Date: 08/2006-04/2007`: 86
- `W. VK45DE`: 82
- `Production Date: 04/2008-09/2009`: 81
- `Production Date: 08/2009-01/2010`: 74
- `W`: 73
- `W. VK50VE`: 72
- `*W. VQ35DE`: 68
- `INFINITI`: 63
- `W. SE`: 59
- `Production Date: 08/2007-04/2008`: 58
- `Production Date: from 04/2007`: 57
- `Production Date: 11/2005-04/2007`: 56
- `Production Date: 08/2005-08/2006`: 55
- `PRIMER`: 52
- `Interior Color: BLACK`: 51
- `Production Date: from 08/2005`: 50
- `Production Date: 10/2004-08/2006`: 48
- `Production Date: 01/2010-08/2010`: 47
- `Production Date: 09/2006-07/2008`: 47
- `Production Date: 08/2010-04/2011`: 46
- `Production Date: 04/2011-08/2011`: 42
- `Production Date: 08/2004-11/2005`: 42
- `S. (PREMIUM + SPORT/P)`: 42
- `Production Date: 07/2008-08/2009`: 41
- `*KC. SE + *CC. SE`: 40
- `HITACHI`: 39

## Unmapped catalog models

- Nissan 300ZX: feed '300ZX' 54 cars
- Nissan Axxess: feed 'Axxess' 1 cars
- Nissan Hardbody Pickup (D21): feed 'Hardbody Pickup (D21)' 0 cars (excluded: catalog model with no feed cars as 'Hardbody Pickup (D21)' (inventory 2026-11-04); nothing to map)
- Nissan Hardbody Pickup (D21U): feed 'Hardbody Pickup (D21U)' 0 cars (excluded: catalog model with no feed cars as 'Hardbody Pickup (D21U)' (inventory 2026-11-04); nothing to map)
- Nissan Kicks Play: feed 'Kicks Play' 0 cars
- Nissan Pulsar NX: feed 'Pulsar NX' 2 cars
- Nissan Rogue Sport: feed 'Rogue Sport' 40 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (35 cars, under catalog squash 'rogue'); unmapped until a reviewed entry exists)
- Nissan Van: feed 'Van' 0 cars
- Nissan Versa Note: feed 'Versa Note' 324 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (313 cars, under catalog squash 'versa'); unmapped until a reviewed entry exists)
