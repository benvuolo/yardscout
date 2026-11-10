# OEM curation report: ford

Raw: `dca9cd845f26` @ `dca9cd845f26`; as of 2026-11-09T20:24:52Z.

- records 7799, classes 7799, list rows 77788, year manifests 702, cells 12485
- Verified groups 0, engine vg groups 0, Likely groups 74
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.fordpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.fordpartsgiant.com: only 1% of its 15529 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2235 |
| ac-compressor | no_records | - | 8861 |
| ac-compressor | not_closed | ambig_target | 410 |
| ac-compressor | not_closed | no_list_manifest | 11075 |
| ac-compressor | not_closed | no_year_manifest | 31396 |
| ac-compressor | not_closed | unattested | 81 |
| ac-compressor | not_closed | uncrawled_chain_member | 62 |
| ac-compressor | not_closed | unverified_product | 252 |
| ac-compressor | not_closed | variant_unread | 2325 |
| ac-compressor | not_closed | year_manifest_bad | 4221 |
| alternator | unmapped | - | 2235 |
| alternator | no_records | - | 7211 |
| alternator | not_closed | no_list_manifest | 11074 |
| alternator | not_closed | no_year_manifest | 33156 |
| alternator | not_closed | suspect_variant | 51 |
| alternator | not_closed | uncrawled_chain_member | 128 |
| alternator | not_closed | unverified_product | 178 |
| alternator | not_closed | variant_unread | 2325 |
| alternator | not_closed | year_manifest_bad | 4560 |
| bumper-front | unmapped | - | 2235 |
| bumper-front | no_records | - | 7315 |
| bumper-front | not_closed | ambig_target | 358 |
| bumper-front | not_closed | no_list_manifest | 752 |
| bumper-front | not_closed | no_year_manifest | 31955 |
| bumper-front | not_closed | unread_sibling_page | 10669 |
| bumper-front | not_closed | variant_unread | 2325 |
| bumper-front | not_closed | year_manifest_bad | 5309 |
| bumper-rear | unmapped | - | 2235 |
| bumper-rear | no_records | - | 3854 |
| bumper-rear | not_closed | ambig_target | 519 |
| bumper-rear | not_closed | no_list_manifest | 669 |
| bumper-rear | not_closed | no_year_manifest | 34979 |
| bumper-rear | not_closed | unread_sibling_page | 10669 |
| bumper-rear | not_closed | variant_unread | 2325 |
| bumper-rear | not_closed | year_manifest_bad | 5668 |
| climate-control | unmapped | - | 2235 |
| climate-control | no_records | - | 23040 |
| climate-control | not_closed | ambig_target | 171 |
| climate-control | not_closed | no_list_manifest | 9726 |
| climate-control | not_closed | no_year_manifest | 20587 |
| climate-control | not_closed | unread_sibling_page | 395 |
| climate-control | not_closed | variant_unread | 1988 |
| climate-control | not_closed | year_manifest_bad | 2776 |
| door-front | unmapped | - | 2235 |
| door-front | no_records | - | 21470 |
| door-front | not_closed | ambig_target | 203 |
| door-front | not_closed | no_list_manifest | 635 |
| door-front | not_closed | no_year_manifest | 19911 |
| door-front | not_closed | unread_sibling_page | 10669 |
| door-front | not_closed | variant_unread | 2325 |
| door-front | not_closed | year_manifest_bad | 3470 |
| door-rear | unmapped | - | 2235 |
| door-rear | no_records | - | 20982 |
| door-rear | not_closed | ambig_target | 203 |
| door-rear | not_closed | no_list_manifest | 693 |
| door-rear | not_closed | no_year_manifest | 21820 |
| door-rear | not_closed | unread_sibling_page | 10165 |
| door-rear | not_closed | variant_unread | 2325 |
| door-rear | not_closed | year_manifest_bad | 2495 |
| fender | unmapped | - | 2235 |
| fender | no_records | - | 10380 |
| fender | not_closed | ambig_target | 409 |
| fender | not_closed | no_list_manifest | 606 |
| fender | not_closed | no_year_manifest | 28667 |
| fender | not_closed | unattested | 4952 |
| fender | not_closed | uncrawled_chain_member | 2268 |
| fender | not_closed | unverified_product | 3449 |
| fender | not_closed | variant_unread | 2325 |
| fender | not_closed | year_manifest_bad | 5627 |
| fuel-pump-module | unmapped | - | 2235 |
| fuel-pump-module | no_records | - | 24648 |
| fuel-pump-module | not_closed | ambig_target | 93 |
| fuel-pump-module | not_closed | no_list_manifest | 10284 |
| fuel-pump-module | not_closed | no_year_manifest | 19813 |
| fuel-pump-module | not_closed | unread_sibling_page | 395 |
| fuel-pump-module | not_closed | variant_unread | 1988 |
| fuel-pump-module | not_closed | year_manifest_bad | 1462 |
| gauge-cluster | unmapped | - | 2235 |
| gauge-cluster | no_records | - | 27015 |
| gauge-cluster | not_closed | ambig_target | 319 |
| gauge-cluster | not_closed | no_list_manifest | 332 |
| gauge-cluster | not_closed | no_year_manifest | 13807 |
| gauge-cluster | not_closed | unread_sibling_page | 10669 |
| gauge-cluster | not_closed | variant_unread | 1938 |
| gauge-cluster | not_closed | year_manifest_bad | 4603 |
| grille | unmapped | - | 2235 |
| grille | no_records | - | 11434 |
| grille | not_closed | ambig_target | 358 |
| grille | not_closed | no_list_manifest | 567 |
| grille | not_closed | no_year_manifest | 28126 |
| grille | not_closed | unattested | 7178 |
| grille | not_closed | uncrawled_chain_member | 941 |
| grille | not_closed | unverified_product | 2550 |
| grille | not_closed | variant_unread | 2325 |
| grille | not_closed | year_manifest_bad | 5204 |
| headlights | unmapped | - | 2235 |
| headlights | no_records | - | 14569 |
| headlights | not_closed | ambig_target | 409 |
| headlights | not_closed | no_list_manifest | 10412 |
| headlights | not_closed | no_year_manifest | 25393 |
| headlights | not_closed | unattested | 211 |
| headlights | not_closed | uncrawled_chain_member | 184 |
| headlights | not_closed | variant_unread | 2024 |
| headlights | not_closed | year_manifest_bad | 5481 |
| hood | unmapped | - | 2235 |
| hood | no_records | - | 6357 |
| hood | not_closed | ambig_target | 358 |
| hood | not_closed | no_list_manifest | 775 |
| hood | not_closed | no_year_manifest | 32623 |
| hood | not_closed | unattested | 7532 |
| hood | not_closed | uncrawled_chain_member | 747 |
| hood | not_closed | unverified_product | 2390 |
| hood | not_closed | variant_unread | 2325 |
| hood | not_closed | year_manifest_bad | 5576 |
| ignition-coils | unmapped | - | 2235 |
| ignition-coils | no_records | - | 8835 |
| ignition-coils | not_closed | ambig_target | 220 |
| ignition-coils | not_closed | no_list_manifest | 807 |
| ignition-coils | not_closed | no_year_manifest | 32789 |
| ignition-coils | not_closed | uncrawled_chain_member | 470 |
| ignition-coils | not_closed | unverified_product | 10199 |
| ignition-coils | not_closed | variant_unread | 2325 |
| ignition-coils | not_closed | year_manifest_bad | 3038 |
| liftgate | unmapped | - | 2235 |
| liftgate | no_records | - | 32447 |
| liftgate | not_closed | ambig_target | 203 |
| liftgate | not_closed | no_list_manifest | 173 |
| liftgate | not_closed | no_year_manifest | 10096 |
| liftgate | not_closed | unread_sibling_page | 10639 |
| liftgate | not_closed | variant_unread | 1988 |
| liftgate | not_closed | year_manifest_bad | 3137 |
| power-steering-pump | unmapped | - | 2235 |
| power-steering-pump | no_records | - | 32270 |
| power-steering-pump | not_closed | no_list_manifest | 6718 |
| power-steering-pump | not_closed | no_year_manifest | 16739 |
| power-steering-pump | not_closed | unread_sibling_page | 239 |
| power-steering-pump | not_closed | variant_unread | 512 |
| power-steering-pump | not_closed | year_manifest_bad | 2205 |
| radiator | unmapped | - | 2235 |
| radiator | no_records | - | 12399 |
| radiator | not_closed | ambig_target | 519 |
| radiator | not_closed | no_list_manifest | 696 |
| radiator | not_closed | no_year_manifest | 27318 |
| radiator | not_closed | unattested | 1724 |
| radiator | not_closed | uncrawled_chain_member | 6988 |
| radiator | not_closed | unverified_product | 1957 |
| radiator | not_closed | variant_unread | 2325 |
| radiator | not_closed | year_manifest_bad | 4757 |
| side-mirrors | unmapped | - | 2235 |
| side-mirrors | no_records | - | 7824 |
| side-mirrors | not_closed | ambig_target | 457 |
| side-mirrors | not_closed | no_list_manifest | 10914 |
| side-mirrors | not_closed | no_year_manifest | 31080 |
| side-mirrors | not_closed | unread_sibling_page | 395 |
| side-mirrors | not_closed | variant_unread | 2325 |
| side-mirrors | not_closed | year_manifest_bad | 5688 |
| starter | unmapped | - | 2235 |
| starter | no_records | - | 17923 |
| starter | not_closed | ambig_target | 17 |
| starter | not_closed | no_list_manifest | 11074 |
| starter | not_closed | no_year_manifest | 26792 |
| starter | not_closed | suspect_variant | 94 |
| starter | not_closed | unattested | 26 |
| starter | not_closed | uncrawled_chain_member | 30 |
| starter | not_closed | unverified_product | 207 |
| starter | not_closed | variant_unread | 2325 |
| starter | not_closed | year_manifest_bad | 195 |
| tail-lights | unmapped | - | 2235 |
| tail-lights | no_records | - | 12701 |
| tail-lights | not_closed | ambig_target | 460 |
| tail-lights | not_closed | no_list_manifest | 10857 |
| tail-lights | not_closed | no_year_manifest | 27085 |
| tail-lights | not_closed | unattested | 179 |
| tail-lights | not_closed | uncrawled_chain_member | 216 |
| tail-lights | not_closed | variant_unread | 2325 |
| tail-lights | not_closed | year_manifest_bad | 4860 |
| tailgate | unmapped | - | 2235 |
| tailgate | no_records | - | 35186 |
| tailgate | not_closed | ambig_target | 358 |
| tailgate | not_closed | no_list_manifest | 7 |
| tailgate | not_closed | no_year_manifest | 7789 |
| tailgate | not_closed | unattested | 9944 |
| tailgate | not_closed | uncrawled_chain_member | 695 |
| tailgate | not_closed | unread_sibling_page | 30 |
| tailgate | not_closed | variant_unread | 1779 |
| tailgate | not_closed | year_manifest_bad | 2895 |
| throttle-body | unmapped | - | 2235 |
| throttle-body | no_records | - | 27217 |
| throttle-body | not_closed | no_list_manifest | 6626 |
| throttle-body | not_closed | no_year_manifest | 20199 |
| throttle-body | not_closed | unattested | 47 |
| throttle-body | not_closed | uncrawled_chain_member | 177 |
| throttle-body | not_closed | variant_unread | 2325 |
| throttle-body | not_closed | year_manifest_bad | 2092 |
| tow-mirrors | unmapped | - | 2235 |
| tow-mirrors | no_records | - | 52645 |
| tow-mirrors | not_closed | ambig_target | 220 |
| tow-mirrors | not_closed | no_list_manifest | 649 |
| tow-mirrors | not_closed | no_year_manifest | 4126 |
| tow-mirrors | not_closed | variant_unread | 841 |
| tow-mirrors | not_closed | year_manifest_bad | 202 |
| trunk-lid | unmapped | - | 2235 |
| trunk-lid | no_records | - | 33406 |
| trunk-lid | not_closed | no_list_manifest | 324 |
| trunk-lid | not_closed | no_year_manifest | 12331 |
| trunk-lid | not_closed | unattested | 7385 |
| trunk-lid | not_closed | uncrawled_chain_member | 2255 |
| trunk-lid | not_closed | unverified_product | 43 |
| trunk-lid | not_closed | variant_unread | 938 |
| trunk-lid | not_closed | year_manifest_bad | 2001 |
| wheels | unmapped | - | 2235 |
| wheels | no_records | - | 5958 |
| wheels | not_closed | ambig_target | 65 |
| wheels | not_closed | no_list_manifest | 11476 |
| wheels | not_closed | no_year_manifest | 34875 |
| wheels | not_closed | variant_unread | 2325 |
| wheels | not_closed | year_manifest_bad | 3984 |
| window-regulator | unmapped | - | 2235 |
| window-regulator | no_records | - | 17151 |
| window-regulator | not_closed | ambig_target | 17 |
| window-regulator | not_closed | no_list_manifest | 10972 |
| window-regulator | not_closed | no_year_manifest | 26400 |
| window-regulator | not_closed | unread_sibling_page | 395 |
| window-regulator | not_closed | variant_unread | 2325 |
| window-regulator | not_closed | year_manifest_bad | 1423 |
| window-switch | unmapped | - | 2235 |
| window-switch | no_records | - | 11465 |
| window-switch | not_closed | ambig_target | 155 |
| window-switch | not_closed | no_list_manifest | 10984 |
| window-switch | not_closed | no_year_manifest | 31034 |
| window-switch | not_closed | unattested | 224 |
| window-switch | not_closed | uncrawled_chain_member | 103 |
| window-switch | not_closed | unverified_product | 68 |
| window-switch | not_closed | variant_unread | 2325 |
| window-switch | not_closed | year_manifest_bad | 2325 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2235 |
| ac-compressor | no_records | - | 8861 |
| ac-compressor | split | no_candidates | 90 |
| ac-compressor | split | option_split | 33993 |
| ac-compressor | conditional | conditional:engine | 1162 |
| ac-compressor | conditional | conditional:engine_unattested | 13633 |
| ac-compressor | conditional | conditional:trim | 944 |
| alternator | unmapped | - | 2235 |
| alternator | no_records | - | 7211 |
| alternator | split | no_candidates | 74 |
| alternator | split | option_split | 43367 |
| alternator | conditional | conditional:engine | 272 |
| alternator | conditional | conditional:engine_unattested | 7269 |
| alternator | conditional | conditional:production | 46 |
| alternator | conditional | conditional:trim | 444 |
| bumper-front | unmapped | - | 2235 |
| bumper-front | no_records | - | 7315 |
| bumper-front | split | no_candidates | 345 |
| bumper-front | split | option_split | 47448 |
| bumper-front | conditional | conditional:engine_unattested | 3339 |
| bumper-front | conditional | conditional:production | 14 |
| bumper-front | conditional | conditional:trim | 222 |
| bumper-rear | unmapped | - | 2235 |
| bumper-rear | no_records | - | 3854 |
| bumper-rear | split | no_candidates | 277 |
| bumper-rear | split | option_split | 50843 |
| bumper-rear | conditional | conditional:engine_unattested | 3636 |
| bumper-rear | conditional | conditional:option | 16 |
| bumper-rear | conditional | conditional:trim | 57 |
| climate-control | unmapped | - | 2235 |
| climate-control | no_records | - | 23040 |
| climate-control | split | no_candidates | 132 |
| climate-control | split | option_split | 26281 |
| climate-control | conditional | conditional:colour | 220 |
| climate-control | conditional | conditional:engine_unattested | 8783 |
| climate-control | conditional | conditional:trim | 227 |
| door-front | unmapped | - | 2235 |
| door-front | no_records | - | 21470 |
| door-front | split | no_candidates | 3207 |
| door-front | split | option_split | 15776 |
| door-front | split | slot_missing | 925 |
| door-front | conditional | conditional:body | 262 |
| door-front | conditional | conditional:engine_unattested | 10160 |
| door-front | conditional | conditional:qualifier | 4364 |
| door-front | conditional | conditional:trim | 2519 |
| door-rear | unmapped | - | 2235 |
| door-rear | no_records | - | 20982 |
| door-rear | split | no_candidates | 1861 |
| door-rear | split | option_split | 16416 |
| door-rear | split | slot_missing | 102 |
| door-rear | conditional | conditional:engine_unattested | 1212 |
| door-rear | conditional | conditional:qualifier | 17269 |
| door-rear | conditional | conditional:trim | 841 |
| fender | unmapped | - | 2235 |
| fender | no_records | - | 10380 |
| fender | split | no_candidates | 394 |
| fender | split | option_split | 24760 |
| fender | split | slot_missing | 955 |
| fender | conditional | conditional:body | 70 |
| fender | conditional | conditional:engine_unattested | 16568 |
| fender | conditional | conditional:trim | 5556 |
| fuel-pump-module | unmapped | - | 2235 |
| fuel-pump-module | no_records | - | 24648 |
| fuel-pump-module | split | no_candidates | 27 |
| fuel-pump-module | split | option_split | 26887 |
| fuel-pump-module | conditional | conditional:engine | 26 |
| fuel-pump-module | conditional | conditional:engine_unattested | 5837 |
| fuel-pump-module | conditional | conditional:trim | 1258 |
| gauge-cluster | unmapped | - | 2235 |
| gauge-cluster | no_records | - | 27015 |
| gauge-cluster | split | no_candidates | 1308 |
| gauge-cluster | split | option_split | 27681 |
| gauge-cluster | conditional | conditional:engine_unattested | 2230 |
| gauge-cluster | conditional | conditional:production | 198 |
| gauge-cluster | conditional | conditional:trim | 251 |
| grille | unmapped | - | 2235 |
| grille | no_records | - | 11434 |
| grille | split | no_candidates | 905 |
| grille | split | option_split | 42805 |
| grille | conditional | conditional:colour | 23 |
| grille | conditional | conditional:engine_unattested | 2506 |
| grille | conditional | conditional:option | 493 |
| grille | conditional | conditional:production | 46 |
| grille | conditional | conditional:trim | 471 |
| headlights | unmapped | - | 2235 |
| headlights | no_records | - | 14569 |
| headlights | split | no_candidates | 23 |
| headlights | split | option_split | 34169 |
| headlights | split | slot_missing | 438 |
| headlights | conditional | conditional:engine_unattested | 7946 |
| headlights | conditional | conditional:option | 101 |
| headlights | conditional | conditional:package | 61 |
| headlights | conditional | conditional:production | 454 |
| headlights | conditional | conditional:trim | 922 |
| hood | unmapped | - | 2235 |
| hood | no_records | - | 6357 |
| hood | split | no_candidates | 470 |
| hood | split | option_split | 8027 |
| hood | conditional | conditional:engine_unattested | 33678 |
| hood | conditional | conditional:production | 59 |
| hood | conditional | conditional:trim | 10092 |
| ignition-coils | unmapped | - | 2235 |
| ignition-coils | no_records | - | 8835 |
| ignition-coils | split | no_candidates | 157 |
| ignition-coils | split | option_split | 29304 |
| ignition-coils | conditional | conditional:engine_unattested | 16741 |
| ignition-coils | conditional | conditional:package | 3462 |
| ignition-coils | conditional | conditional:trim | 184 |
| liftgate | unmapped | - | 2235 |
| liftgate | no_records | - | 32447 |
| liftgate | split | no_candidates | 9852 |
| liftgate | split | option_split | 3601 |
| liftgate | conditional | conditional:engine_unattested | 9283 |
| liftgate | conditional | conditional:option | 1282 |
| liftgate | conditional | conditional:production | 14 |
| liftgate | conditional | conditional:trim | 2204 |
| power-steering-pump | unmapped | - | 2235 |
| power-steering-pump | no_records | - | 32270 |
| power-steering-pump | split | no_candidates | 186 |
| power-steering-pump | split | option_split | 11953 |
| power-steering-pump | conditional | conditional:colour | 440 |
| power-steering-pump | conditional | conditional:engine | 302 |
| power-steering-pump | conditional | conditional:engine_unattested | 11870 |
| power-steering-pump | conditional | conditional:option | 160 |
| power-steering-pump | conditional | conditional:trim | 1502 |
| radiator | unmapped | - | 2235 |
| radiator | no_records | - | 12399 |
| radiator | split | no_candidates | 1365 |
| radiator | split | option_split | 41372 |
| radiator | conditional | conditional:engine_unattested | 2669 |
| radiator | conditional | conditional:trim | 878 |
| side-mirrors | unmapped | - | 2235 |
| side-mirrors | no_records | - | 7824 |
| side-mirrors | split | no_candidates | 28 |
| side-mirrors | split | option_split | 45632 |
| side-mirrors | split | position_missing | 7 |
| side-mirrors | split | slot_missing | 2033 |
| side-mirrors | conditional | conditional:colour | 169 |
| side-mirrors | conditional | conditional:engine_unattested | 2417 |
| side-mirrors | conditional | conditional:option | 407 |
| side-mirrors | conditional | conditional:trim | 166 |
| starter | unmapped | - | 2235 |
| starter | no_records | - | 17923 |
| starter | split | no_candidates | 195 |
| starter | split | option_split | 34209 |
| starter | conditional | conditional:engine | 26 |
| starter | conditional | conditional:engine_unattested | 6168 |
| starter | conditional | conditional:option | 160 |
| starter | conditional | conditional:trim | 2 |
| tail-lights | unmapped | - | 2235 |
| tail-lights | no_records | - | 12701 |
| tail-lights | split | no_candidates | 49 |
| tail-lights | split | option_split | 38515 |
| tail-lights | split | slot_missing | 561 |
| tail-lights | conditional | conditional:colour | 54 |
| tail-lights | conditional | conditional:engine_unattested | 5603 |
| tail-lights | conditional | conditional:option | 2 |
| tail-lights | conditional | conditional:production | 130 |
| tail-lights | conditional | conditional:trim | 1068 |
| tailgate | unmapped | - | 2235 |
| tailgate | no_records | - | 35186 |
| tailgate | split | no_candidates | 10976 |
| tailgate | split | option_split | 9445 |
| tailgate | conditional | conditional:engine_unattested | 2483 |
| tailgate | conditional | conditional:trim | 593 |
| throttle-body | unmapped | - | 2235 |
| throttle-body | no_records | - | 27217 |
| throttle-body | split | no_candidates | 9 |
| throttle-body | split | option_split | 14537 |
| throttle-body | conditional | conditional:engine | 53 |
| throttle-body | conditional | conditional:engine_unattested | 14316 |
| throttle-body | conditional | conditional:option | 203 |
| throttle-body | conditional | conditional:trim | 2348 |
| tow-mirrors | unmapped | - | 2235 |
| tow-mirrors | no_records | - | 52645 |
| tow-mirrors | split | option_split | 2964 |
| tow-mirrors | split | position_conflict | 606 |
| tow-mirrors | split | slot_missing | 2377 |
| tow-mirrors | conditional | conditional:colour | 30 |
| tow-mirrors | conditional | conditional:engine_unattested | 61 |
| trunk-lid | unmapped | - | 2235 |
| trunk-lid | no_records | - | 33406 |
| trunk-lid | split | no_candidates | 6093 |
| trunk-lid | split | option_split | 14914 |
| trunk-lid | conditional | conditional:engine_unattested | 3803 |
| trunk-lid | conditional | conditional:option | 38 |
| trunk-lid | conditional | conditional:qualifier | 39 |
| trunk-lid | conditional | conditional:trim | 390 |
| wheels | unmapped | - | 2235 |
| wheels | no_records | - | 5958 |
| wheels | split | option_split | 49724 |
| wheels | conditional | conditional:engine_unattested | 2948 |
| wheels | conditional | conditional:package | 53 |
| window-regulator | unmapped | - | 2235 |
| window-regulator | no_records | - | 17151 |
| window-regulator | split | no_candidates | 100 |
| window-regulator | split | packaging_incomplete | 3979 |
| window-regulator | split | packaging_split | 13934 |
| window-regulator | split | packaging_unstated | 22165 |
| window-regulator | split | position_missing | 742 |
| window-regulator | conditional | conditional:trim | 612 |
| window-switch | unmapped | - | 2235 |
| window-switch | no_records | - | 11465 |
| window-switch | split | no_candidates | 1403 |
| window-switch | split | option_split | 23530 |
| window-switch | split | position_missing | 16581 |
| window-switch | conditional | conditional:colour | 1337 |
| window-switch | conditional | conditional:engine_unattested | 3160 |
| window-switch | conditional | conditional:trim | 1207 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 1072
- held_exterior_cross_model: 57
- recrawl_resolved: 2
- rule_drift: 96
- universal_part_suspect: 20
- wheel_compact_spare: 21

## Unknown note clauses (top 30)

- `Callout Name: 10849`: 1380
- `Base Number: 10849`: 1198
- `(CP) Designates Crash Part - When Ordering Please Refer To Crash Part Truckload Program Guidelines`: 948
- `Callout Name: 17682`: 898
- `Callout Name: 8200`: 685
- `Package Quantity: 1`: 640
- `Paint to match`: 596
- `For Instrument Cluster QC Issues Contact fesg@ford.com`: 553
- `Order From Instrument Cluster Online Ordering System Using The Online 1878 Form`: 553
- `Require Quantity: 4`: 530
- `With MPH/KMH Speedometer`: 503
- `With KMH/MPH Speedometer`: 480
- `Base Number: 17682`: 428
- `Callout Name: 13008`: 412
- `Export Dealers And Affiliates: Order Direct From FCSD-IDO`: 392
- `Order From Instrument Cluster Online Ordering System Using The Online Ordering System`: 364
- `Callout Name: 16005`: 328
- `Base Number: 8200`: 318
- `Callout Name: 13404`: 317
- `Fit Note: Ford Division Derivative`: 312
- `Callout Name: 17906`: 310
- `Callout Name: 17D957`: 289
- `Callout Name: 8005`: 282
- `Callout Name: 17757`: 281
- `Callout Name: 17K835`: 245
- `Callout Name: 19980`: 236
- `Callout Name: 10346`: 230
- `Base Number: 16005`: 213
- `Must Replace Valve Stem & Screw With Every Tire Or Wheel Change`: 210
- `Base Number: 13008`: 206

## Unmapped catalog models

- Ford Aspire: feed 'Aspire' 17 cars
- Ford E-350/E-350 Super Duty: feed 'E-350/E-350 Super Duty' 0 cars (excluded: feed has no 'E-350/E-350 Super Duty'; feed splits E-350 spellings)
- Ford E-550 Super Duty: feed 'E-550 Super Duty' 0 cars
- Ford EXP: feed 'EXP' 1 cars
- Ford EcoSport: feed 'EcoSport' 0 cars
- Ford Econoline Super Duty(1996-1999): feed 'Econoline Super Duty(1996-1999)' 0 cars
- Ford F Super Duty: feed 'F Super Duty' 0 cars
- Ford F53: feed 'F-53' 0 cars
- Ford F53 Stripped Chassis: feed 'F53 Stripped Chassis' 0 cars (excluded: catalog model with no feed cars as 'F53 Stripped Chassis' (inventory 2026-11-04); nothing to map)
- Ford F59: feed 'F-59' 0 cars
- Ford Fairmont: feed 'Fairmont' 4 cars
- Ford Festiva: feed 'Festiva' 14 cars
- Ford GT: feed 'GT' 3 cars
- Ford Granada: feed 'Granada' 2 cars
- Ford Maverick: feed 'Maverick' 11 cars
- Ford Pinto: feed 'Pinto' 8 cars
- Ford Police Responder Hybrid: feed 'Police Responder Hybrid' 0 cars (excluded: catalog model with no feed cars as 'Police Responder Hybrid' (inventory 2026-11-04); nothing to map)
- Ford SSV Plug-In Hybrid: feed 'SSV Plug-In Hybrid' 0 cars (excluded: catalog model with no feed cars as 'SSV Plug-In Hybrid' (inventory 2026-11-04); nothing to map)
- Lincoln Mark VI: feed 'Mark VI' 4 cars
- Mercury Bobcat: feed 'Bobcat' 0 cars
- Mercury LN7: feed 'LN7' 0 cars
- Mercury Lynx: feed 'Lynx' 0 cars
- Mercury Marquis: feed 'Marquis' 30 cars
- Mercury Villager: feed 'Villager' 80 cars
- Mercury Zephyr: feed 'Zephyr' 3 cars (excluded: feed spelling or sub-model the catalog does not print as its own model (3 cars, under catalog squash 'zephyr'); unmapped until a reviewed entry exists)
