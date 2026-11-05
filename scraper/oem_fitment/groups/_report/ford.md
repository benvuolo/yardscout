# OEM curation report: ford

Raw: `ceccc800d7ba22c0291121baabb0a9292eb8f271` @ `ceccc800d7ba`; as of 2026-11-05T22:17:38Z.

- records 3672, classes 3672, list rows 10341, year manifests 43, cells 5958
- Verified groups 0, engine vg groups 0, Likely groups 1033
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.fordpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.fordpartsgiant.com: only 1% of its 7541 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2255 |
| ac-compressor | no_records | - | 8943 |
| ac-compressor | not_closed | ambig_target | 408 |
| ac-compressor | not_closed | no_year_manifest | 48246 |
| ac-compressor | not_closed | unattested | 82 |
| ac-compressor | not_closed | uncrawled_chain_member | 59 |
| ac-compressor | not_closed | unverified_product | 260 |
| ac-compressor | not_closed | year_manifest_bad | 156 |
| alternator | unmapped | - | 2255 |
| alternator | no_records | - | 7193 |
| alternator | not_closed | no_year_manifest | 50444 |
| alternator | not_closed | suspect_variant | 51 |
| alternator | not_closed | uncrawled_chain_member | 134 |
| alternator | not_closed | unverified_product | 176 |
| alternator | not_closed | year_manifest_bad | 156 |
| climate-control | unmapped | - | 2255 |
| climate-control | no_records | - | 22846 |
| climate-control | not_closed | ambig_target | 166 |
| climate-control | not_closed | no_year_manifest | 34622 |
| climate-control | not_closed | unread_sibling_page | 401 |
| climate-control | not_closed | year_manifest_bad | 119 |
| fuel-pump-module | unmapped | - | 2255 |
| fuel-pump-module | no_records | - | 24450 |
| fuel-pump-module | not_closed | ambig_target | 89 |
| fuel-pump-module | not_closed | no_year_manifest | 33079 |
| fuel-pump-module | not_closed | unread_sibling_page | 401 |
| fuel-pump-module | not_closed | year_manifest_bad | 135 |
| headlights | unmapped | - | 2255 |
| headlights | no_records | - | 14527 |
| headlights | not_closed | ambig_target | 408 |
| headlights | not_closed | no_year_manifest | 42662 |
| headlights | not_closed | unattested | 214 |
| headlights | not_closed | uncrawled_chain_member | 187 |
| headlights | not_closed | year_manifest_bad | 156 |
| power-steering-pump | unmapped | - | 2255 |
| power-steering-pump | no_records | - | 32109 |
| power-steering-pump | not_closed | no_year_manifest | 25646 |
| power-steering-pump | not_closed | unread_sibling_page | 243 |
| power-steering-pump | not_closed | year_manifest_bad | 156 |
| side-mirrors | unmapped | - | 2255 |
| side-mirrors | no_records | - | 7792 |
| side-mirrors | not_closed | ambig_target | 452 |
| side-mirrors | not_closed | no_year_manifest | 49353 |
| side-mirrors | not_closed | unread_sibling_page | 401 |
| side-mirrors | not_closed | year_manifest_bad | 156 |
| starter | unmapped | - | 2255 |
| starter | no_records | - | 17786 |
| starter | not_closed | ambig_target | 17 |
| starter | not_closed | no_year_manifest | 39834 |
| starter | not_closed | suspect_variant | 95 |
| starter | not_closed | unattested | 28 |
| starter | not_closed | uncrawled_chain_member | 31 |
| starter | not_closed | unverified_product | 207 |
| starter | not_closed | year_manifest_bad | 156 |
| tail-lights | unmapped | - | 2255 |
| tail-lights | no_records | - | 12621 |
| tail-lights | not_closed | ambig_target | 456 |
| tail-lights | not_closed | no_year_manifest | 44541 |
| tail-lights | not_closed | unattested | 187 |
| tail-lights | not_closed | uncrawled_chain_member | 214 |
| tail-lights | not_closed | year_manifest_bad | 135 |
| throttle-body | unmapped | - | 2255 |
| throttle-body | no_records | - | 27015 |
| throttle-body | not_closed | no_list_manifest | 18 |
| throttle-body | not_closed | no_year_manifest | 30850 |
| throttle-body | not_closed | unattested | 45 |
| throttle-body | not_closed | uncrawled_chain_member | 180 |
| throttle-body | not_closed | year_manifest_bad | 46 |
| tow-mirrors | unmapped | - | 2255 |
| tow-mirrors | no_records | - | 52192 |
| tow-mirrors | not_closed | ambig_target | 219 |
| tow-mirrors | not_closed | no_list_manifest | 31 |
| tow-mirrors | not_closed | no_year_manifest | 5712 |
| window-regulator | unmapped | - | 2255 |
| window-regulator | no_records | - | 17040 |
| window-regulator | not_closed | ambig_target | 17 |
| window-regulator | not_closed | no_year_manifest | 40561 |
| window-regulator | not_closed | unread_sibling_page | 401 |
| window-regulator | not_closed | year_manifest_bad | 135 |
| window-switch | unmapped | - | 2255 |
| window-switch | no_records | - | 14279 |
| window-switch | not_closed | ambig_target | 151 |
| window-switch | not_closed | no_year_manifest | 43267 |
| window-switch | not_closed | unattested | 225 |
| window-switch | not_closed | uncrawled_chain_member | 105 |
| window-switch | not_closed | unverified_product | 71 |
| window-switch | not_closed | year_manifest_bad | 56 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2255 |
| ac-compressor | no_records | - | 8943 |
| ac-compressor | split | no_candidates | 81 |
| ac-compressor | split | option_split | 33679 |
| ac-compressor | conditional | conditional:engine | 1119 |
| ac-compressor | conditional | conditional:engine_unattested | 13393 |
| ac-compressor | conditional | conditional:trim | 939 |
| alternator | unmapped | - | 2255 |
| alternator | no_records | - | 7193 |
| alternator | split | no_candidates | 33 |
| alternator | split | option_split | 42967 |
| alternator | conditional | conditional:engine | 264 |
| alternator | conditional | conditional:engine_unattested | 7210 |
| alternator | conditional | conditional:production | 41 |
| alternator | conditional | conditional:trim | 446 |
| climate-control | unmapped | - | 2255 |
| climate-control | no_records | - | 22846 |
| climate-control | split | no_candidates | 132 |
| climate-control | split | option_split | 26023 |
| climate-control | conditional | conditional:colour | 185 |
| climate-control | conditional | conditional:engine_unattested | 8741 |
| climate-control | conditional | conditional:trim | 227 |
| fuel-pump-module | unmapped | - | 2255 |
| fuel-pump-module | no_records | - | 24450 |
| fuel-pump-module | split | no_candidates | 25 |
| fuel-pump-module | split | option_split | 26614 |
| fuel-pump-module | conditional | conditional:engine | 28 |
| fuel-pump-module | conditional | conditional:engine_unattested | 5785 |
| fuel-pump-module | conditional | conditional:trim | 1252 |
| headlights | unmapped | - | 2255 |
| headlights | no_records | - | 14527 |
| headlights | split | no_candidates | 12 |
| headlights | split | option_split | 33881 |
| headlights | split | slot_missing | 434 |
| headlights | conditional | conditional:engine_unattested | 7834 |
| headlights | conditional | conditional:option | 100 |
| headlights | conditional | conditional:package | 62 |
| headlights | conditional | conditional:production | 440 |
| headlights | conditional | conditional:trim | 864 |
| power-steering-pump | unmapped | - | 2255 |
| power-steering-pump | no_records | - | 32109 |
| power-steering-pump | split | no_candidates | 186 |
| power-steering-pump | split | option_split | 11762 |
| power-steering-pump | conditional | conditional:colour | 447 |
| power-steering-pump | conditional | conditional:engine | 295 |
| power-steering-pump | conditional | conditional:engine_unattested | 11713 |
| power-steering-pump | conditional | conditional:option | 163 |
| power-steering-pump | conditional | conditional:trim | 1479 |
| side-mirrors | unmapped | - | 2255 |
| side-mirrors | no_records | - | 7792 |
| side-mirrors | split | no_candidates | 21 |
| side-mirrors | split | option_split | 45253 |
| side-mirrors | split | slot_missing | 1986 |
| side-mirrors | conditional | conditional:colour | 160 |
| side-mirrors | conditional | conditional:engine_unattested | 2374 |
| side-mirrors | conditional | conditional:option | 411 |
| side-mirrors | conditional | conditional:trim | 157 |
| starter | unmapped | - | 2255 |
| starter | no_records | - | 17786 |
| starter | split | no_candidates | 156 |
| starter | split | option_split | 33886 |
| starter | conditional | conditional:engine | 28 |
| starter | conditional | conditional:engine_unattested | 6133 |
| starter | conditional | conditional:option | 163 |
| starter | conditional | conditional:trim | 2 |
| tail-lights | unmapped | - | 2255 |
| tail-lights | no_records | - | 12621 |
| tail-lights | split | no_candidates | 42 |
| tail-lights | split | option_split | 38151 |
| tail-lights | split | slot_missing | 542 |
| tail-lights | conditional | conditional:colour | 56 |
| tail-lights | conditional | conditional:engine_unattested | 5552 |
| tail-lights | conditional | conditional:option | 2 |
| tail-lights | conditional | conditional:production | 125 |
| tail-lights | conditional | conditional:trim | 1063 |
| throttle-body | unmapped | - | 2255 |
| throttle-body | no_records | - | 27015 |
| throttle-body | split | option_split | 14374 |
| throttle-body | conditional | conditional:engine | 56 |
| throttle-body | conditional | conditional:engine_unattested | 14172 |
| throttle-body | conditional | conditional:option | 205 |
| throttle-body | conditional | conditional:trim | 2332 |
| tow-mirrors | unmapped | - | 2255 |
| tow-mirrors | no_records | - | 52192 |
| tow-mirrors | split | option_split | 2921 |
| tow-mirrors | split | position_conflict | 604 |
| tow-mirrors | split | slot_missing | 2347 |
| tow-mirrors | conditional | conditional:colour | 31 |
| tow-mirrors | conditional | conditional:engine_unattested | 59 |
| window-regulator | unmapped | - | 2255 |
| window-regulator | no_records | - | 17040 |
| window-regulator | split | no_candidates | 68 |
| window-regulator | split | packaging_incomplete | 3966 |
| window-regulator | split | packaging_split | 13776 |
| window-regulator | split | packaging_unstated | 21970 |
| window-regulator | split | position_missing | 738 |
| window-regulator | conditional | conditional:trim | 596 |
| window-switch | unmapped | - | 2255 |
| window-switch | no_records | - | 14279 |
| window-switch | split | no_candidates | 2943 |
| window-switch | split | option_split | 21855 |
| window-switch | split | position_missing | 12711 |
| window-switch | conditional | conditional:colour | 1327 |
| window-switch | conditional | conditional:engine_unattested | 3685 |
| window-switch | conditional | conditional:trim | 1354 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 104
- recrawl_resolved: 1
- rule_drift: 37
- universal_part_suspect: 9

## Unknown note clauses (top 30)

- `Callout Name: 17682`: 983
- `Base Number: 17682`: 459
- `Callout Name: 13008`: 450
- `(CP) Designates Crash Part - When Ordering Please Refer To Crash Part Truckload Program Guidelines`: 352
- `Callout Name: 13404`: 335
- `Callout Name: 19980`: 310
- `Callout Name: 10346`: 232
- `Base Number: 13008`: 213
- `Headlamp Assy`: 183
- `Callout Name: 9H307`: 172
- `Paint to match`: 163
- `Lamp Assy - Rear`: 161
- `Callout Name: 19703`: 151
- `Base Number: 19980`: 149
- `Callout Name: <23394`: 141
- `Base Number: 13404`: 131
- `R.H.`: 110
- `Callout Name: 3A674`: 105
- `Callout Name: <23200`: 103
- `L.H.`: 103
- `Mirror Assy`: 100
- `Callout Name: 11002`: 98
- `Base Number: <23394`: 95
- `Less Blind Spot Information System`: 95
- `Fit Note: Dual Zone Auto Temp Control A/C`: 92
- `Base Number: 9H307`: 91
- `Excludes Cover`: 91
- `Callout Name: <27000`: 88
- `With Drivers Heated Seat`: 86
- `XLT`: 84

## Unmapped catalog models

- Ford E-350/E-350 Super Duty: feed 'E-350/E-350 Super Duty' 0 cars (excluded: feed has no 'E-350/E-350 Super Duty'; feed splits E-350 spellings)
- Ford E-550 Super Duty: feed 'E-550 Super Duty' 0 cars
- Ford EcoSport: feed 'EcoSport' 0 cars
- Ford Econoline Super Duty(1996-1999): feed 'Econoline Super Duty(1996-1999)' 0 cars
- Ford F Super Duty: feed 'F Super Duty' 0 cars
- Ford F53: feed 'F-53' 0 cars
- Ford F53 Stripped Chassis: feed 'F53 Stripped Chassis' 0 cars (excluded: catalog model with no feed cars as 'F53 Stripped Chassis' (inventory 2026-11-04); nothing to map)
- Ford Fairmont: feed 'Fairmont' 4 cars
- Ford Granada: feed 'Granada' 2 cars
- Ford Pinto: feed 'Pinto' 5 cars
- Ford Police Responder Hybrid: feed 'Police Responder Hybrid' 0 cars (excluded: catalog model with no feed cars as 'Police Responder Hybrid' (inventory 2026-11-04); nothing to map)
- Ford SSV Plug-In Hybrid: feed 'SSV Plug-In Hybrid' 0 cars (excluded: catalog model with no feed cars as 'SSV Plug-In Hybrid' (inventory 2026-11-04); nothing to map)
- Mercury Bobcat: feed 'Bobcat' 0 cars
- Mercury Lynx: feed 'Lynx' 0 cars
- Mercury Marquis: feed 'Marquis' 30 cars
- Mercury Villager: feed 'Villager' 80 cars
- Mercury Zephyr: feed 'Zephyr' 3 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (3 cars, under catalog squash 'zephyr'); unmapped until a reviewed entry exists)
