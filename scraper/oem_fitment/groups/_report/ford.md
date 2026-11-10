# OEM curation report: ford

Raw: `dca9cd845f26` @ `dca9cd845f26`; as of 2026-11-09T20:24:52Z.

- records 7799, classes 7799, list rows 77788, year manifests 702, cells 12485
- Verified groups 0, engine vg groups 0, Likely groups 81
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.fordpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.fordpartsgiant.com: only 1% of its 15529 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2233 |
| ac-compressor | no_records | - | 8843 |
| ac-compressor | not_closed | ambig_target | 411 |
| ac-compressor | not_closed | no_list_manifest | 11060 |
| ac-compressor | not_closed | no_year_manifest | 31350 |
| ac-compressor | not_closed | unattested | 81 |
| ac-compressor | not_closed | uncrawled_chain_member | 62 |
| ac-compressor | not_closed | unverified_product | 253 |
| ac-compressor | not_closed | variant_unread | 2323 |
| ac-compressor | not_closed | year_manifest_bad | 4214 |
| alternator | unmapped | - | 2233 |
| alternator | no_records | - | 7203 |
| alternator | not_closed | no_list_manifest | 11059 |
| alternator | not_closed | no_year_manifest | 33101 |
| alternator | not_closed | suspect_variant | 51 |
| alternator | not_closed | uncrawled_chain_member | 126 |
| alternator | not_closed | unverified_product | 180 |
| alternator | not_closed | variant_unread | 2323 |
| alternator | not_closed | year_manifest_bad | 4554 |
| bumper-front | unmapped | - | 2233 |
| bumper-front | no_records | - | 7314 |
| bumper-front | not_closed | ambig_target | 358 |
| bumper-front | not_closed | no_list_manifest | 752 |
| bumper-front | not_closed | no_year_manifest | 31897 |
| bumper-front | not_closed | unread_sibling_page | 10655 |
| bumper-front | not_closed | variant_unread | 2323 |
| bumper-front | not_closed | year_manifest_bad | 5298 |
| bumper-rear | unmapped | - | 2233 |
| bumper-rear | no_records | - | 3853 |
| bumper-rear | not_closed | ambig_target | 519 |
| bumper-rear | not_closed | no_list_manifest | 668 |
| bumper-rear | not_closed | no_year_manifest | 34921 |
| bumper-rear | not_closed | unread_sibling_page | 10655 |
| bumper-rear | not_closed | variant_unread | 2323 |
| bumper-rear | not_closed | year_manifest_bad | 5658 |
| climate-control | unmapped | - | 2233 |
| climate-control | no_records | - | 23013 |
| climate-control | not_closed | ambig_target | 171 |
| climate-control | not_closed | no_list_manifest | 9712 |
| climate-control | not_closed | no_year_manifest | 20551 |
| climate-control | not_closed | unread_sibling_page | 396 |
| climate-control | not_closed | variant_unread | 1985 |
| climate-control | not_closed | year_manifest_bad | 2769 |
| door-front | unmapped | - | 2233 |
| door-front | no_records | - | 21452 |
| door-front | not_closed | ambig_target | 203 |
| door-front | not_closed | no_list_manifest | 634 |
| door-front | not_closed | no_year_manifest | 19868 |
| door-front | not_closed | unread_sibling_page | 10655 |
| door-front | not_closed | variant_unread | 2323 |
| door-front | not_closed | year_manifest_bad | 3462 |
| door-rear | unmapped | - | 2233 |
| door-rear | no_records | - | 20954 |
| door-rear | not_closed | ambig_target | 203 |
| door-rear | not_closed | no_list_manifest | 692 |
| door-rear | not_closed | no_year_manifest | 21785 |
| door-rear | not_closed | unread_sibling_page | 10153 |
| door-rear | not_closed | variant_unread | 2323 |
| door-rear | not_closed | year_manifest_bad | 2487 |
| fender | unmapped | - | 2233 |
| fender | no_records | - | 10370 |
| fender | not_closed | ambig_target | 408 |
| fender | not_closed | no_list_manifest | 606 |
| fender | not_closed | no_year_manifest | 28618 |
| fender | not_closed | unattested | 4952 |
| fender | not_closed | uncrawled_chain_member | 2264 |
| fender | not_closed | unverified_product | 3439 |
| fender | not_closed | variant_unread | 2323 |
| fender | not_closed | year_manifest_bad | 5617 |
| fuel-pump-module | unmapped | - | 2233 |
| fuel-pump-module | no_records | - | 24623 |
| fuel-pump-module | not_closed | ambig_target | 93 |
| fuel-pump-module | not_closed | no_list_manifest | 10269 |
| fuel-pump-module | not_closed | no_year_manifest | 19771 |
| fuel-pump-module | not_closed | unread_sibling_page | 396 |
| fuel-pump-module | not_closed | variant_unread | 1985 |
| fuel-pump-module | not_closed | year_manifest_bad | 1460 |
| gauge-cluster | unmapped | - | 2233 |
| gauge-cluster | no_records | - | 26977 |
| gauge-cluster | not_closed | ambig_target | 319 |
| gauge-cluster | not_closed | no_list_manifest | 332 |
| gauge-cluster | not_closed | no_year_manifest | 13783 |
| gauge-cluster | not_closed | unread_sibling_page | 10655 |
| gauge-cluster | not_closed | variant_unread | 1935 |
| gauge-cluster | not_closed | year_manifest_bad | 4596 |
| grille | unmapped | - | 2233 |
| grille | no_records | - | 11427 |
| grille | not_closed | ambig_target | 358 |
| grille | not_closed | no_list_manifest | 566 |
| grille | not_closed | no_year_manifest | 28075 |
| grille | not_closed | unattested | 7169 |
| grille | not_closed | uncrawled_chain_member | 941 |
| grille | not_closed | unverified_product | 2545 |
| grille | not_closed | variant_unread | 2323 |
| grille | not_closed | year_manifest_bad | 5193 |
| headlights | unmapped | - | 2233 |
| headlights | no_records | - | 14552 |
| headlights | not_closed | ambig_target | 410 |
| headlights | not_closed | no_list_manifest | 10396 |
| headlights | not_closed | no_year_manifest | 25347 |
| headlights | not_closed | unattested | 212 |
| headlights | not_closed | uncrawled_chain_member | 184 |
| headlights | not_closed | variant_unread | 2023 |
| headlights | not_closed | year_manifest_bad | 5473 |
| hood | unmapped | - | 2233 |
| hood | no_records | - | 6358 |
| hood | not_closed | ambig_target | 358 |
| hood | not_closed | no_list_manifest | 775 |
| hood | not_closed | no_year_manifest | 32563 |
| hood | not_closed | unattested | 7523 |
| hood | not_closed | uncrawled_chain_member | 747 |
| hood | not_closed | unverified_product | 2385 |
| hood | not_closed | variant_unread | 2323 |
| hood | not_closed | year_manifest_bad | 5565 |
| ignition-coils | unmapped | - | 2233 |
| ignition-coils | no_records | - | 8833 |
| ignition-coils | not_closed | ambig_target | 220 |
| ignition-coils | not_closed | no_list_manifest | 807 |
| ignition-coils | not_closed | no_year_manifest | 32726 |
| ignition-coils | not_closed | uncrawled_chain_member | 469 |
| ignition-coils | not_closed | unverified_product | 10186 |
| ignition-coils | not_closed | variant_unread | 2323 |
| ignition-coils | not_closed | year_manifest_bad | 3033 |
| liftgate | unmapped | - | 2233 |
| liftgate | no_records | - | 32404 |
| liftgate | not_closed | ambig_target | 203 |
| liftgate | not_closed | no_list_manifest | 172 |
| liftgate | not_closed | no_year_manifest | 10076 |
| liftgate | not_closed | unread_sibling_page | 10625 |
| liftgate | not_closed | variant_unread | 1985 |
| liftgate | not_closed | year_manifest_bad | 3132 |
| power-steering-pump | unmapped | - | 2233 |
| power-steering-pump | no_records | - | 32211 |
| power-steering-pump | not_closed | no_list_manifest | 6714 |
| power-steering-pump | not_closed | no_year_manifest | 16717 |
| power-steering-pump | not_closed | unread_sibling_page | 238 |
| power-steering-pump | not_closed | variant_unread | 512 |
| power-steering-pump | not_closed | year_manifest_bad | 2205 |
| radiator | unmapped | - | 2233 |
| radiator | no_records | - | 12381 |
| radiator | not_closed | ambig_target | 519 |
| radiator | not_closed | no_list_manifest | 695 |
| radiator | not_closed | no_year_manifest | 27277 |
| radiator | not_closed | unattested | 1717 |
| radiator | not_closed | uncrawled_chain_member | 6986 |
| radiator | not_closed | unverified_product | 1952 |
| radiator | not_closed | variant_unread | 2323 |
| radiator | not_closed | year_manifest_bad | 4747 |
| side-mirrors | unmapped | - | 2233 |
| side-mirrors | no_records | - | 7812 |
| side-mirrors | not_closed | ambig_target | 457 |
| side-mirrors | not_closed | no_list_manifest | 10900 |
| side-mirrors | not_closed | no_year_manifest | 31031 |
| side-mirrors | not_closed | unread_sibling_page | 396 |
| side-mirrors | not_closed | variant_unread | 2323 |
| side-mirrors | not_closed | year_manifest_bad | 5678 |
| starter | unmapped | - | 2233 |
| starter | no_records | - | 17898 |
| starter | not_closed | ambig_target | 17 |
| starter | not_closed | no_list_manifest | 11059 |
| starter | not_closed | no_year_manifest | 26748 |
| starter | not_closed | suspect_variant | 94 |
| starter | not_closed | unattested | 27 |
| starter | not_closed | uncrawled_chain_member | 30 |
| starter | not_closed | unverified_product | 206 |
| starter | not_closed | variant_unread | 2323 |
| starter | not_closed | year_manifest_bad | 195 |
| tail-lights | unmapped | - | 2233 |
| tail-lights | no_records | - | 12693 |
| tail-lights | not_closed | ambig_target | 460 |
| tail-lights | not_closed | no_list_manifest | 10845 |
| tail-lights | not_closed | no_year_manifest | 27030 |
| tail-lights | not_closed | unattested | 178 |
| tail-lights | not_closed | uncrawled_chain_member | 218 |
| tail-lights | not_closed | variant_unread | 2323 |
| tail-lights | not_closed | year_manifest_bad | 4850 |
| tailgate | unmapped | - | 2233 |
| tailgate | no_records | - | 35138 |
| tailgate | not_closed | ambig_target | 358 |
| tailgate | not_closed | no_list_manifest | 7 |
| tailgate | not_closed | no_year_manifest | 7776 |
| tailgate | not_closed | unattested | 9931 |
| tailgate | not_closed | uncrawled_chain_member | 694 |
| tailgate | not_closed | unread_sibling_page | 30 |
| tailgate | not_closed | variant_unread | 1775 |
| tailgate | not_closed | year_manifest_bad | 2888 |
| throttle-body | unmapped | - | 2233 |
| throttle-body | no_records | - | 27182 |
| throttle-body | not_closed | no_list_manifest | 6622 |
| throttle-body | not_closed | no_year_manifest | 20159 |
| throttle-body | not_closed | unattested | 48 |
| throttle-body | not_closed | uncrawled_chain_member | 176 |
| throttle-body | not_closed | variant_unread | 2323 |
| throttle-body | not_closed | year_manifest_bad | 2087 |
| tow-mirrors | unmapped | - | 2233 |
| tow-mirrors | no_records | - | 52562 |
| tow-mirrors | not_closed | ambig_target | 220 |
| tow-mirrors | not_closed | no_list_manifest | 649 |
| tow-mirrors | not_closed | no_year_manifest | 4124 |
| tow-mirrors | not_closed | variant_unread | 840 |
| tow-mirrors | not_closed | year_manifest_bad | 202 |
| trunk-lid | unmapped | - | 2233 |
| trunk-lid | no_records | - | 33352 |
| trunk-lid | not_closed | no_list_manifest | 325 |
| trunk-lid | not_closed | no_year_manifest | 12316 |
| trunk-lid | not_closed | unattested | 7372 |
| trunk-lid | not_closed | uncrawled_chain_member | 2255 |
| trunk-lid | not_closed | unverified_product | 43 |
| trunk-lid | not_closed | variant_unread | 935 |
| trunk-lid | not_closed | year_manifest_bad | 1999 |
| wheels | unmapped | - | 2233 |
| wheels | no_records | - | 5952 |
| wheels | not_closed | ambig_target | 65 |
| wheels | not_closed | no_list_manifest | 11462 |
| wheels | not_closed | no_year_manifest | 34819 |
| wheels | not_closed | variant_unread | 2323 |
| wheels | not_closed | year_manifest_bad | 3976 |
| window-regulator | unmapped | - | 2233 |
| window-regulator | no_records | - | 17127 |
| window-regulator | not_closed | ambig_target | 17 |
| window-regulator | not_closed | no_list_manifest | 10958 |
| window-regulator | not_closed | no_year_manifest | 26356 |
| window-regulator | not_closed | unread_sibling_page | 396 |
| window-regulator | not_closed | variant_unread | 2323 |
| window-regulator | not_closed | year_manifest_bad | 1420 |
| window-switch | unmapped | - | 2233 |
| window-switch | no_records | - | 11441 |
| window-switch | not_closed | ambig_target | 155 |
| window-switch | not_closed | no_list_manifest | 10970 |
| window-switch | not_closed | no_year_manifest | 30991 |
| window-switch | not_closed | unattested | 224 |
| window-switch | not_closed | uncrawled_chain_member | 103 |
| window-switch | not_closed | unverified_product | 69 |
| window-switch | not_closed | variant_unread | 2323 |
| window-switch | not_closed | year_manifest_bad | 2321 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2233 |
| ac-compressor | no_records | - | 8843 |
| ac-compressor | split | no_candidates | 90 |
| ac-compressor | split | option_split | 33946 |
| ac-compressor | conditional | conditional:engine | 1161 |
| ac-compressor | conditional | conditional:engine_unattested | 13609 |
| ac-compressor | conditional | conditional:trim | 948 |
| alternator | unmapped | - | 2233 |
| alternator | no_records | - | 7203 |
| alternator | split | no_candidates | 74 |
| alternator | split | option_split | 43298 |
| alternator | conditional | conditional:engine | 272 |
| alternator | conditional | conditional:engine_unattested | 7261 |
| alternator | conditional | conditional:production | 45 |
| alternator | conditional | conditional:trim | 444 |
| bumper-front | unmapped | - | 2233 |
| bumper-front | no_records | - | 7314 |
| bumper-front | split | no_candidates | 343 |
| bumper-front | split | option_split | 47373 |
| bumper-front | conditional | conditional:engine_unattested | 3332 |
| bumper-front | conditional | conditional:production | 14 |
| bumper-front | conditional | conditional:trim | 221 |
| bumper-rear | unmapped | - | 2233 |
| bumper-rear | no_records | - | 3853 |
| bumper-rear | split | no_candidates | 274 |
| bumper-rear | split | option_split | 50765 |
| bumper-rear | conditional | conditional:engine_unattested | 3632 |
| bumper-rear | conditional | conditional:option | 16 |
| bumper-rear | conditional | conditional:trim | 57 |
| climate-control | unmapped | - | 2233 |
| climate-control | no_records | - | 23013 |
| climate-control | split | no_candidates | 132 |
| climate-control | split | option_split | 26243 |
| climate-control | conditional | conditional:colour | 221 |
| climate-control | conditional | conditional:engine_unattested | 8761 |
| climate-control | conditional | conditional:trim | 227 |
| door-front | unmapped | - | 2233 |
| door-front | no_records | - | 21452 |
| door-front | split | no_candidates | 3200 |
| door-front | split | option_split | 15742 |
| door-front | split | slot_missing | 920 |
| door-front | conditional | conditional:body | 262 |
| door-front | conditional | conditional:engine_unattested | 10145 |
| door-front | conditional | conditional:qualifier | 4359 |
| door-front | conditional | conditional:trim | 2517 |
| door-rear | unmapped | - | 2233 |
| door-rear | no_records | - | 20954 |
| door-rear | split | no_candidates | 1854 |
| door-rear | split | option_split | 16389 |
| door-rear | split | slot_missing | 101 |
| door-rear | conditional | conditional:engine_unattested | 1210 |
| door-rear | conditional | conditional:qualifier | 17249 |
| door-rear | conditional | conditional:trim | 840 |
| fender | unmapped | - | 2233 |
| fender | no_records | - | 10370 |
| fender | split | no_candidates | 391 |
| fender | split | option_split | 24719 |
| fender | split | slot_missing | 950 |
| fender | conditional | conditional:body | 70 |
| fender | conditional | conditional:engine_unattested | 16544 |
| fender | conditional | conditional:trim | 5553 |
| fuel-pump-module | unmapped | - | 2233 |
| fuel-pump-module | no_records | - | 24623 |
| fuel-pump-module | split | no_candidates | 27 |
| fuel-pump-module | split | option_split | 26832 |
| fuel-pump-module | conditional | conditional:engine | 27 |
| fuel-pump-module | conditional | conditional:engine_unattested | 5828 |
| fuel-pump-module | conditional | conditional:trim | 1260 |
| gauge-cluster | unmapped | - | 2233 |
| gauge-cluster | no_records | - | 26977 |
| gauge-cluster | split | no_candidates | 1307 |
| gauge-cluster | split | option_split | 27640 |
| gauge-cluster | conditional | conditional:engine_unattested | 2225 |
| gauge-cluster | conditional | conditional:production | 199 |
| gauge-cluster | conditional | conditional:trim | 249 |
| grille | unmapped | - | 2233 |
| grille | no_records | - | 11427 |
| grille | split | no_candidates | 903 |
| grille | split | option_split | 42728 |
| grille | conditional | conditional:colour | 23 |
| grille | conditional | conditional:engine_unattested | 2508 |
| grille | conditional | conditional:option | 494 |
| grille | conditional | conditional:production | 45 |
| grille | conditional | conditional:trim | 469 |
| headlights | unmapped | - | 2233 |
| headlights | no_records | - | 14552 |
| headlights | split | no_candidates | 23 |
| headlights | split | option_split | 34116 |
| headlights | split | slot_missing | 438 |
| headlights | conditional | conditional:engine_unattested | 7933 |
| headlights | conditional | conditional:option | 101 |
| headlights | conditional | conditional:package | 61 |
| headlights | conditional | conditional:production | 454 |
| headlights | conditional | conditional:trim | 919 |
| hood | unmapped | - | 2233 |
| hood | no_records | - | 6358 |
| hood | split | no_candidates | 468 |
| hood | split | option_split | 8011 |
| hood | conditional | conditional:engine_unattested | 33625 |
| hood | conditional | conditional:production | 59 |
| hood | conditional | conditional:trim | 10076 |
| ignition-coils | unmapped | - | 2233 |
| ignition-coils | no_records | - | 8833 |
| ignition-coils | split | no_candidates | 157 |
| ignition-coils | split | option_split | 29239 |
| ignition-coils | conditional | conditional:engine_unattested | 16722 |
| ignition-coils | conditional | conditional:package | 3462 |
| ignition-coils | conditional | conditional:trim | 184 |
| liftgate | unmapped | - | 2233 |
| liftgate | no_records | - | 32404 |
| liftgate | split | no_candidates | 9838 |
| liftgate | split | option_split | 3593 |
| liftgate | conditional | conditional:engine_unattested | 9271 |
| liftgate | conditional | conditional:option | 1278 |
| liftgate | conditional | conditional:production | 14 |
| liftgate | conditional | conditional:trim | 2199 |
| power-steering-pump | unmapped | - | 2233 |
| power-steering-pump | no_records | - | 32211 |
| power-steering-pump | split | no_candidates | 186 |
| power-steering-pump | split | option_split | 11934 |
| power-steering-pump | conditional | conditional:colour | 440 |
| power-steering-pump | conditional | conditional:engine | 302 |
| power-steering-pump | conditional | conditional:engine_unattested | 11864 |
| power-steering-pump | conditional | conditional:option | 160 |
| power-steering-pump | conditional | conditional:trim | 1500 |
| radiator | unmapped | - | 2233 |
| radiator | no_records | - | 12381 |
| radiator | split | no_candidates | 1359 |
| radiator | split | option_split | 41316 |
| radiator | conditional | conditional:engine_unattested | 2662 |
| radiator | conditional | conditional:trim | 879 |
| side-mirrors | unmapped | - | 2233 |
| side-mirrors | no_records | - | 7812 |
| side-mirrors | split | no_candidates | 28 |
| side-mirrors | split | option_split | 45560 |
| side-mirrors | split | position_missing | 7 |
| side-mirrors | split | slot_missing | 2029 |
| side-mirrors | conditional | conditional:colour | 167 |
| side-mirrors | conditional | conditional:engine_unattested | 2420 |
| side-mirrors | conditional | conditional:option | 408 |
| side-mirrors | conditional | conditional:trim | 166 |
| starter | unmapped | - | 2233 |
| starter | no_records | - | 17898 |
| starter | split | no_candidates | 195 |
| starter | split | option_split | 34166 |
| starter | conditional | conditional:engine | 27 |
| starter | conditional | conditional:engine_unattested | 6149 |
| starter | conditional | conditional:option | 160 |
| starter | conditional | conditional:trim | 2 |
| tail-lights | unmapped | - | 2233 |
| tail-lights | no_records | - | 12693 |
| tail-lights | split | no_candidates | 49 |
| tail-lights | split | option_split | 38455 |
| tail-lights | split | slot_missing | 556 |
| tail-lights | conditional | conditional:colour | 54 |
| tail-lights | conditional | conditional:engine_unattested | 5592 |
| tail-lights | conditional | conditional:option | 2 |
| tail-lights | conditional | conditional:production | 130 |
| tail-lights | conditional | conditional:trim | 1066 |
| tailgate | unmapped | - | 2233 |
| tailgate | no_records | - | 35138 |
| tailgate | split | no_candidates | 10958 |
| tailgate | split | option_split | 9432 |
| tailgate | conditional | conditional:engine_unattested | 2476 |
| tailgate | conditional | conditional:trim | 593 |
| throttle-body | unmapped | - | 2233 |
| throttle-body | no_records | - | 27182 |
| throttle-body | split | no_candidates | 9 |
| throttle-body | split | option_split | 14511 |
| throttle-body | conditional | conditional:engine | 53 |
| throttle-body | conditional | conditional:engine_unattested | 14292 |
| throttle-body | conditional | conditional:option | 204 |
| throttle-body | conditional | conditional:trim | 2346 |
| tow-mirrors | unmapped | - | 2233 |
| tow-mirrors | no_records | - | 52562 |
| tow-mirrors | split | option_split | 2962 |
| tow-mirrors | split | position_conflict | 607 |
| tow-mirrors | split | slot_missing | 2375 |
| tow-mirrors | conditional | conditional:colour | 30 |
| tow-mirrors | conditional | conditional:engine_unattested | 61 |
| trunk-lid | unmapped | - | 2233 |
| trunk-lid | no_records | - | 33352 |
| trunk-lid | split | no_candidates | 6081 |
| trunk-lid | split | option_split | 14900 |
| trunk-lid | conditional | conditional:engine_unattested | 3796 |
| trunk-lid | conditional | conditional:option | 39 |
| trunk-lid | conditional | conditional:qualifier | 39 |
| trunk-lid | conditional | conditional:trim | 390 |
| wheels | unmapped | - | 2233 |
| wheels | no_records | - | 5952 |
| wheels | split | option_split | 49650 |
| wheels | conditional | conditional:engine_unattested | 2941 |
| wheels | conditional | conditional:package | 54 |
| window-regulator | unmapped | - | 2233 |
| window-regulator | no_records | - | 17127 |
| window-regulator | split | no_candidates | 100 |
| window-regulator | split | packaging_incomplete | 3974 |
| window-regulator | split | packaging_split | 13915 |
| window-regulator | split | packaging_unstated | 22132 |
| window-regulator | split | position_missing | 738 |
| window-regulator | conditional | conditional:trim | 611 |
| window-switch | unmapped | - | 2233 |
| window-switch | no_records | - | 11441 |
| window-switch | split | no_candidates | 1399 |
| window-switch | split | option_split | 23494 |
| window-switch | split | position_missing | 16414 |
| window-switch | conditional | conditional:colour | 1334 |
| window-switch | conditional | conditional:engine_unattested | 3160 |
| window-switch | conditional | conditional:trim | 1355 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 1072
- held_exterior_cross_model: 58
- recrawl_resolved: 2
- rule_drift: 96
- universal_part_suspect: 20
- wheel_compact_spare: 21

## Unknown note clauses (top 30)

- `Callout Name: 10849`: 1471
- `Base Number: 10849`: 1287
- `(CP) Designates Crash Part - When Ordering Please Refer To Crash Part Truckload Program Guidelines`: 958
- `Callout Name: 17682`: 937
- `Callout Name: 8200`: 685
- `Package Quantity: 1`: 643
- `Order From Instrument Cluster Online Ordering System Using The Online 1878 Form`: 603
- `Paint to match`: 598
- `For Instrument Cluster QC Issues Contact fesg@ford.com`: 578
- `With MPH/KMH Speedometer`: 548
- `Require Quantity: 4`: 530
- `With KMH/MPH Speedometer`: 513
- `Base Number: 17682`: 439
- `Callout Name: 13008`: 432
- `Export Dealers And Affiliates: Order Direct From FCSD-IDO`: 408
- `Order From Instrument Cluster Online Ordering System Using The Online Ordering System`: 405
- `Callout Name: 13404`: 329
- `Callout Name: 16005`: 328
- `Base Number: 8200`: 318
- `Fit Note: Ford Division Derivative`: 316
- `Callout Name: 19980`: 312
- `Callout Name: 17906`: 310
- `Callout Name: 17D957`: 289
- `Callout Name: 8005`: 282
- `Callout Name: 17757`: 281
- `Callout Name: 17K835`: 245
- `Callout Name: 10346`: 232
- `XLT`: 219
- `Base Number: 16005`: 213
- `Must Replace Valve Stem & Screw With Every Tire Or Wheel Change`: 210

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
