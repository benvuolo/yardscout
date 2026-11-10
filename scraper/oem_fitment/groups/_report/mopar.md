# OEM curation report: mopar

Raw: `dca9cd845f26` @ `dca9cd845f26`; as of 2026-11-09T19:24:53Z.

- records 8390, classes 7581, list rows 80300, year manifests 460, cells 12822
- Verified groups 0, engine vg groups 0, Likely groups 309
- blocked sites: www.moparpartsgiant.com

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.moparpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.moparpartsgiant.com: only 3% of its 7351 fitment rows can be coverage: its option column holds trims (option_column_is_trims), which count only after a namespace audit (spec 5.2)
- blocked by the crawl breaker: www.moparpartsgiant.com (their cells never close, C9)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2128 |
| ac-compressor | no_records | - | 3647 |
| ac-compressor | not_closed | list_manifest_bad | 7 |
| ac-compressor | not_closed | no_list_manifest | 4282 |
| ac-compressor | not_closed | no_year_manifest | 25946 |
| ac-compressor | not_closed | site_blocked | 67 |
| ac-compressor | not_closed | stale | 26 |
| ac-compressor | not_closed | suspect_variant | 218 |
| ac-compressor | not_closed | unattested | 13 |
| ac-compressor | not_closed | uncrawled_chain_member | 1394 |
| ac-compressor | not_closed | unread_sibling_page | 2185 |
| ac-compressor | not_closed | unverified_product | 4223 |
| alternator | unmapped | - | 2128 |
| alternator | no_records | - | 1274 |
| alternator | not_closed | list_manifest_bad | 7 |
| alternator | not_closed | no_list_manifest | 4430 |
| alternator | not_closed | no_year_manifest | 28199 |
| alternator | not_closed | site_blocked | 28 |
| alternator | not_closed | suspect_variant | 455 |
| alternator | not_closed | unattested | 3 |
| alternator | not_closed | unread_sibling_page | 2166 |
| alternator | not_closed | unverified_product | 5446 |
| bumper-front | unmapped | - | 2128 |
| bumper-front | no_records | - | 9210 |
| bumper-front | not_closed | no_list_manifest | 4405 |
| bumper-front | not_closed | no_year_manifest | 20734 |
| bumper-front | not_closed | unread_sibling_page | 7659 |
| bumper-rear | unmapped | - | 2128 |
| bumper-rear | no_records | - | 7173 |
| bumper-rear | not_closed | no_list_manifest | 4384 |
| bumper-rear | not_closed | no_year_manifest | 22798 |
| bumper-rear | not_closed | unread_sibling_page | 7653 |
| climate-control | unmapped | - | 2128 |
| climate-control | no_records | - | 11674 |
| climate-control | not_closed | no_list_manifest | 4199 |
| climate-control | not_closed | no_year_manifest | 19676 |
| climate-control | not_closed | unread_sibling_page | 6459 |
| door-front | unmapped | - | 2128 |
| door-front | no_records | - | 6309 |
| door-front | not_closed | no_list_manifest | 4245 |
| door-front | not_closed | no_year_manifest | 23801 |
| door-front | not_closed | unread_sibling_page | 7653 |
| door-rear | unmapped | - | 2128 |
| door-rear | no_records | - | 12923 |
| door-rear | not_closed | no_list_manifest | 3918 |
| door-rear | not_closed | no_year_manifest | 17514 |
| door-rear | not_closed | unread_sibling_page | 7653 |
| fender | unmapped | - | 2128 |
| fender | no_records | - | 12123 |
| fender | not_closed | no_list_manifest | 4000 |
| fender | not_closed | no_year_manifest | 18268 |
| fender | not_closed | site_blocked | 373 |
| fender | not_closed | uncrawled_chain_member | 567 |
| fender | not_closed | unread_sibling_page | 5850 |
| fender | not_closed | unverified_product | 601 |
| fender | split | no_candidates | 217 |
| fender | conditional | conditional:trim | 9 |
| fuel-pump-module | unmapped | - | 2128 |
| fuel-pump-module | no_records | - | 3896 |
| fuel-pump-module | not_closed | list_manifest_bad | 7 |
| fuel-pump-module | not_closed | no_list_manifest | 4083 |
| fuel-pump-module | not_closed | no_year_manifest | 25896 |
| fuel-pump-module | not_closed | unread_sibling_page | 8126 |
| gauge-cluster | unmapped | - | 2128 |
| gauge-cluster | no_records | - | 26002 |
| gauge-cluster | not_closed | no_list_manifest | 1859 |
| gauge-cluster | not_closed | no_year_manifest | 6667 |
| gauge-cluster | not_closed | unread_sibling_page | 7480 |
| grille | unmapped | - | 2128 |
| grille | no_records | - | 12495 |
| grille | not_closed | no_list_manifest | 3580 |
| grille | not_closed | no_year_manifest | 18274 |
| grille | not_closed | suspect_variant | 399 |
| grille | not_closed | uncrawled_chain_member | 234 |
| grille | not_closed | unread_sibling_page | 4411 |
| grille | not_closed | unverified_product | 1235 |
| grille | split | no_candidates | 42 |
| grille | split | option_split | 444 |
| grille | conditional | conditional:colour | 71 |
| grille | conditional | conditional:engine | 19 |
| grille | conditional | conditional:model_other | 483 |
| grille | conditional | conditional:position | 18 |
| grille | conditional | conditional:trim | 283 |
| grille | gated | category_unconfirmed | 20 |
| headlights | unmapped | - | 2128 |
| headlights | no_records | - | 7404 |
| headlights | not_closed | list_manifest_bad | 7 |
| headlights | not_closed | no_list_manifest | 4089 |
| headlights | not_closed | no_year_manifest | 22415 |
| headlights | not_closed | uncrawled_chain_member | 34 |
| headlights | not_closed | unread_sibling_page | 8059 |
| hood | unmapped | - | 2128 |
| hood | no_records | - | 6572 |
| hood | not_closed | no_list_manifest | 4232 |
| hood | not_closed | no_year_manifest | 23534 |
| hood | not_closed | suspect_variant | 399 |
| hood | not_closed | uncrawled_chain_member | 269 |
| hood | not_closed | unread_sibling_page | 5623 |
| hood | not_closed | unverified_product | 1335 |
| hood | conditional | conditional:engine | 19 |
| hood | conditional | conditional:option | 16 |
| hood | conditional | conditional:trim | 9 |
| ignition-coils | unmapped | - | 2128 |
| ignition-coils | no_records | - | 977 |
| ignition-coils | not_closed | no_list_manifest | 4902 |
| ignition-coils | not_closed | no_year_manifest | 28494 |
| ignition-coils | not_closed | unread_sibling_page | 6909 |
| ignition-coils | not_closed | unverified_product | 726 |
| liftgate | unmapped | - | 2128 |
| liftgate | no_records | - | 23739 |
| liftgate | not_closed | no_list_manifest | 3447 |
| liftgate | not_closed | no_year_manifest | 11072 |
| liftgate | not_closed | unread_sibling_page | 3750 |
| power-steering-pump | unmapped | - | 2128 |
| power-steering-pump | no_records | - | 4936 |
| power-steering-pump | not_closed | list_manifest_bad | 7 |
| power-steering-pump | not_closed | no_list_manifest | 4339 |
| power-steering-pump | not_closed | no_year_manifest | 25871 |
| power-steering-pump | not_closed | unread_sibling_page | 6855 |
| radiator | unmapped | - | 2128 |
| radiator | no_records | - | 2713 |
| radiator | not_closed | no_list_manifest | 4806 |
| radiator | not_closed | no_year_manifest | 26812 |
| radiator | not_closed | uncrawled_chain_member | 399 |
| radiator | not_closed | unread_sibling_page | 7226 |
| radiator | not_closed | unverified_product | 52 |
| side-mirrors | unmapped | - | 2128 |
| side-mirrors | no_records | - | 4169 |
| side-mirrors | not_closed | no_list_manifest | 4626 |
| side-mirrors | not_closed | no_year_manifest | 25564 |
| side-mirrors | not_closed | site_blocked | 62 |
| side-mirrors | not_closed | unattested | 13 |
| side-mirrors | not_closed | unread_sibling_page | 7565 |
| side-mirrors | conditional | conditional:option | 9 |
| starter | unmapped | - | 2128 |
| starter | no_records | - | 2450 |
| starter | not_closed | list_manifest_bad | 7 |
| starter | not_closed | no_list_manifest | 4261 |
| starter | not_closed | no_year_manifest | 27244 |
| starter | not_closed | site_blocked | 13 |
| starter | not_closed | stale | 26 |
| starter | not_closed | suspect_variant | 354 |
| starter | not_closed | uncrawled_chain_member | 170 |
| starter | not_closed | unread_sibling_page | 1935 |
| starter | not_closed | unverified_product | 5548 |
| tail-lights | unmapped | - | 2128 |
| tail-lights | no_records | - | 9459 |
| tail-lights | not_closed | list_manifest_bad | 7 |
| tail-lights | not_closed | no_list_manifest | 3774 |
| tail-lights | not_closed | no_year_manifest | 20675 |
| tail-lights | not_closed | site_blocked | 1524 |
| tail-lights | not_closed | stale | 26 |
| tail-lights | not_closed | suspect_variant | 35 |
| tail-lights | not_closed | uncrawled_chain_member | 1061 |
| tail-lights | not_closed | unread_sibling_page | 2180 |
| tail-lights | not_closed | unverified_product | 3042 |
| tail-lights | split | no_candidates | 10 |
| tail-lights | split | slot_missing | 7 |
| tail-lights | conditional | conditional:trim | 208 |
| tailgate | unmapped | - | 2128 |
| tailgate | no_records | - | 38178 |
| tailgate | not_closed | no_list_manifest | 59 |
| tailgate | not_closed | no_year_manifest | 2412 |
| tailgate | not_closed | site_blocked | 373 |
| tailgate | not_closed | uncrawled_chain_member | 1 |
| tailgate | not_closed | unread_sibling_page | 579 |
| tailgate | not_closed | unverified_product | 406 |
| throttle-body | unmapped | - | 2128 |
| throttle-body | no_records | - | 2354 |
| throttle-body | not_closed | list_manifest_bad | 7 |
| throttle-body | not_closed | no_list_manifest | 4472 |
| throttle-body | not_closed | no_year_manifest | 27237 |
| throttle-body | not_closed | site_blocked | 1664 |
| throttle-body | not_closed | suspect_variant | 340 |
| throttle-body | not_closed | unattested | 9 |
| throttle-body | not_closed | uncrawled_chain_member | 13 |
| throttle-body | not_closed | unread_sibling_page | 1954 |
| throttle-body | not_closed | unverified_product | 3958 |
| tow-mirrors | unmapped | - | 2128 |
| tow-mirrors | no_records | - | 39476 |
| tow-mirrors | not_closed | no_list_manifest | 524 |
| tow-mirrors | not_closed | no_year_manifest | 2008 |
| trunk-lid | unmapped | - | 2128 |
| trunk-lid | no_records | - | 40824 |
| trunk-lid | not_closed | no_year_manifest | 210 |
| trunk-lid | not_closed | site_blocked | 52 |
| trunk-lid | not_closed | unread_sibling_page | 922 |
| wheels | unmapped | - | 2128 |
| wheels | no_records | - | 1471 |
| wheels | not_closed | chain_fitment_inconsistent | 233 |
| wheels | not_closed | no_list_manifest | 839 |
| wheels | not_closed | no_year_manifest | 28040 |
| wheels | not_closed | uncrawled_chain_member | 9346 |
| wheels | not_closed | unverified_product | 1268 |
| wheels | split | no_candidates | 61 |
| wheels | split | option_split | 436 |
| wheels | conditional | conditional:colour | 115 |
| wheels | conditional | conditional:trim | 192 |
| wheels | conditional | conditional:unknown | 7 |
| window-regulator | unmapped | - | 2128 |
| window-regulator | no_records | - | 2457 |
| window-regulator | not_closed | list_manifest_bad | 7 |
| window-regulator | not_closed | no_list_manifest | 4828 |
| window-regulator | not_closed | no_year_manifest | 27229 |
| window-regulator | not_closed | site_blocked | 389 |
| window-regulator | not_closed | stale | 26 |
| window-regulator | not_closed | suspect_variant | 12 |
| window-regulator | not_closed | unattested | 9 |
| window-regulator | not_closed | uncrawled_chain_member | 966 |
| window-regulator | not_closed | unread_sibling_page | 3522 |
| window-regulator | not_closed | unverified_product | 1894 |
| window-regulator | split | packaging_unstated | 669 |
| window-switch | unmapped | - | 2128 |
| window-switch | no_records | - | 8803 |
| window-switch | not_closed | list_manifest_bad | 7 |
| window-switch | not_closed | no_list_manifest | 3377 |
| window-switch | not_closed | no_year_manifest | 21743 |
| window-switch | not_closed | site_blocked | 9 |
| window-switch | not_closed | stale | 26 |
| window-switch | not_closed | suspect_variant | 13 |
| window-switch | not_closed | unread_sibling_page | 8030 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2128 |
| ac-compressor | no_records | - | 3647 |
| ac-compressor | split | no_candidates | 93 |
| ac-compressor | split | option_split | 33484 |
| ac-compressor | conditional | conditional:engine | 22 |
| ac-compressor | conditional | conditional:engine_unattested | 41 |
| ac-compressor | conditional | conditional:engine_unparsed | 21 |
| ac-compressor | conditional | conditional:notes_not_own_page | 2057 |
| ac-compressor | conditional | conditional:option | 52 |
| ac-compressor | conditional | conditional:qualifier | 192 |
| ac-compressor | conditional | conditional:trim | 2383 |
| ac-compressor | chain_member_conditional | chain_member_conditional | 9 |
| ac-compressor | gated | kind_not_phase1 | 7 |
| alternator | unmapped | - | 2128 |
| alternator | no_records | - | 1274 |
| alternator | split | no_candidates | 3 |
| alternator | split | option_split | 35591 |
| alternator | conditional | conditional:engine | 1552 |
| alternator | conditional | conditional:engine_unattested | 68 |
| alternator | conditional | conditional:engine_unparsed | 20 |
| alternator | conditional | conditional:fitted_not_listed | 7 |
| alternator | conditional | conditional:notes_not_own_page | 238 |
| alternator | conditional | conditional:option | 187 |
| alternator | conditional | conditional:trim | 3068 |
| bumper-front | unmapped | - | 2128 |
| bumper-front | no_records | - | 9210 |
| bumper-front | split | no_candidates | 24 |
| bumper-front | split | option_split | 26509 |
| bumper-front | conditional | conditional:engine | 2479 |
| bumper-front | conditional | conditional:model_other | 12 |
| bumper-front | conditional | conditional:notes_not_own_page | 831 |
| bumper-front | conditional | conditional:trim | 2510 |
| bumper-front | eligible | - | 433 |
| bumper-rear | unmapped | - | 2128 |
| bumper-rear | no_records | - | 7173 |
| bumper-rear | split | no_candidates | 446 |
| bumper-rear | split | option_split | 30078 |
| bumper-rear | conditional | conditional:colour | 114 |
| bumper-rear | conditional | conditional:engine | 68 |
| bumper-rear | conditional | conditional:model_other | 2 |
| bumper-rear | conditional | conditional:notes_not_own_page | 1118 |
| bumper-rear | conditional | conditional:trim | 2951 |
| bumper-rear | eligible | - | 58 |
| climate-control | unmapped | - | 2128 |
| climate-control | no_records | - | 11674 |
| climate-control | split | no_candidates | 52 |
| climate-control | split | option_split | 25027 |
| climate-control | conditional | conditional:engine | 50 |
| climate-control | conditional | conditional:engine_unattested | 2 |
| climate-control | conditional | conditional:fitted_not_listed | 37 |
| climate-control | conditional | conditional:notes_not_own_page | 1735 |
| climate-control | conditional | conditional:option | 23 |
| climate-control | conditional | conditional:option_layout | 164 |
| climate-control | conditional | conditional:trim | 3235 |
| climate-control | blocked | unverified_member | 9 |
| door-front | unmapped | - | 2128 |
| door-front | no_records | - | 6309 |
| door-front | split | no_candidates | 150 |
| door-front | split | option_split | 8924 |
| door-front | split | position_missing | 73 |
| door-front | split | slot_missing | 340 |
| door-front | conditional | conditional:engine | 1600 |
| door-front | conditional | conditional:notes_not_own_page | 3890 |
| door-front | conditional | conditional:production | 48 |
| door-front | conditional | conditional:trim | 18696 |
| door-front | conditional | conditional:unknown | 7 |
| door-front | eligible | - | 1971 |
| door-rear | unmapped | - | 2128 |
| door-rear | no_records | - | 12923 |
| door-rear | split | no_candidates | 1932 |
| door-rear | split | option_split | 4261 |
| door-rear | split | position_missing | 93 |
| door-rear | split | slot_missing | 779 |
| door-rear | conditional | conditional:body | 432 |
| door-rear | conditional | conditional:fitted_not_listed | 353 |
| door-rear | conditional | conditional:notes_not_own_page | 6377 |
| door-rear | conditional | conditional:option_layout | 634 |
| door-rear | conditional | conditional:trim | 11800 |
| door-rear | eligible | - | 2387 |
| door-rear | grouped | - | 37 |
| fender | unmapped | - | 2128 |
| fender | no_records | - | 12123 |
| fender | split | no_candidates | 1322 |
| fender | split | option_split | 7485 |
| fender | split | position_missing | 12 |
| fender | split | slot_missing | 62 |
| fender | conditional | conditional:body | 201 |
| fender | conditional | conditional:engine | 2286 |
| fender | conditional | conditional:notes_not_own_page | 3424 |
| fender | conditional | conditional:option | 10 |
| fender | conditional | conditional:trim | 13097 |
| fender | chain_member_conditional | chain_member_conditional | 801 |
| fender | eligible | - | 1153 |
| fender | grouped | - | 32 |
| fuel-pump-module | unmapped | - | 2128 |
| fuel-pump-module | no_records | - | 3896 |
| fuel-pump-module | split | no_candidates | 189 |
| fuel-pump-module | split | option_split | 30811 |
| fuel-pump-module | conditional | conditional:engine | 438 |
| fuel-pump-module | conditional | conditional:engine_unattested | 63 |
| fuel-pump-module | conditional | conditional:engine_unparsed | 33 |
| fuel-pump-module | conditional | conditional:fitted_not_listed | 31 |
| fuel-pump-module | conditional | conditional:fuel | 31 |
| fuel-pump-module | conditional | conditional:notes_not_own_page | 1569 |
| fuel-pump-module | conditional | conditional:package | 2 |
| fuel-pump-module | conditional | conditional:trim | 4936 |
| fuel-pump-module | blocked | unverified_member | 9 |
| gauge-cluster | unmapped | - | 2128 |
| gauge-cluster | no_records | - | 26002 |
| gauge-cluster | split | no_candidates | 1560 |
| gauge-cluster | split | option_split | 12884 |
| gauge-cluster | conditional | conditional:engine | 393 |
| gauge-cluster | conditional | conditional:notes_not_own_page | 534 |
| gauge-cluster | conditional | conditional:trim | 604 |
| gauge-cluster | eligible | - | 31 |
| grille | unmapped | - | 2128 |
| grille | no_records | - | 12495 |
| grille | split | no_candidates | 361 |
| grille | split | option_split | 18180 |
| grille | conditional | conditional:body | 406 |
| grille | conditional | conditional:colour | 81 |
| grille | conditional | conditional:engine | 802 |
| grille | conditional | conditional:model_other | 483 |
| grille | conditional | conditional:notes_not_own_page | 2127 |
| grille | conditional | conditional:option | 137 |
| grille | conditional | conditional:position | 18 |
| grille | conditional | conditional:trim | 6161 |
| grille | chain_member_conditional | chain_member_conditional | 420 |
| grille | eligible | - | 337 |
| headlights | unmapped | - | 2128 |
| headlights | no_records | - | 7404 |
| headlights | split | no_candidates | 376 |
| headlights | split | option_split | 26200 |
| headlights | split | position_missing | 469 |
| headlights | split | slot_missing | 121 |
| headlights | conditional | conditional:engine | 280 |
| headlights | conditional | conditional:fitted_not_listed | 15 |
| headlights | conditional | conditional:notes_not_own_page | 1690 |
| headlights | conditional | conditional:option | 200 |
| headlights | conditional | conditional:option_layout | 13 |
| headlights | conditional | conditional:production | 24 |
| headlights | conditional | conditional:trim | 4490 |
| headlights | conditional | conditional:unknown | 259 |
| headlights | chain_member_conditional | chain_member_conditional | 221 |
| headlights | eligible | - | 246 |
| hood | unmapped | - | 2128 |
| hood | no_records | - | 6572 |
| hood | split | no_candidates | 143 |
| hood | split | option_split | 3733 |
| hood | conditional | conditional:body | 203 |
| hood | conditional | conditional:engine | 2866 |
| hood | conditional | conditional:engine_unparsed | 15 |
| hood | conditional | conditional:notes_not_own_page | 7686 |
| hood | conditional | conditional:option | 2175 |
| hood | conditional | conditional:option_layout | 631 |
| hood | conditional | conditional:trim | 16239 |
| hood | conditional | conditional:unknown | 7 |
| hood | chain_member_conditional | chain_member_conditional | 641 |
| hood | blocked | unverified_member | 261 |
| hood | eligible | - | 804 |
| hood | grouped | - | 32 |
| ignition-coils | unmapped | - | 2128 |
| ignition-coils | no_records | - | 977 |
| ignition-coils | split | option_split | 27958 |
| ignition-coils | conditional | conditional:body | 203 |
| ignition-coils | conditional | conditional:engine | 2290 |
| ignition-coils | conditional | conditional:engine_unattested | 227 |
| ignition-coils | conditional | conditional:engine_unparsed | 48 |
| ignition-coils | conditional | conditional:notes_not_own_page | 4825 |
| ignition-coils | conditional | conditional:option | 524 |
| ignition-coils | conditional | conditional:option_layout | 30 |
| ignition-coils | conditional | conditional:trim | 4523 |
| ignition-coils | chain_member_conditional | chain_member_conditional | 170 |
| ignition-coils | blocked | unverified_member | 233 |
| liftgate | unmapped | - | 2128 |
| liftgate | no_records | - | 23739 |
| liftgate | split | no_candidates | 342 |
| liftgate | split | option_split | 1682 |
| liftgate | conditional | conditional:engine | 1549 |
| liftgate | conditional | conditional:notes_not_own_page | 4453 |
| liftgate | conditional | conditional:trim | 8712 |
| liftgate | eligible | - | 1531 |
| power-steering-pump | unmapped | - | 2128 |
| power-steering-pump | no_records | - | 4936 |
| power-steering-pump | split | no_candidates | 181 |
| power-steering-pump | split | option_split | 30765 |
| power-steering-pump | conditional | conditional:engine | 822 |
| power-steering-pump | conditional | conditional:engine_unparsed | 31 |
| power-steering-pump | conditional | conditional:notes_not_own_page | 2832 |
| power-steering-pump | conditional | conditional:option_layout | 9 |
| power-steering-pump | conditional | conditional:qualifier | 670 |
| power-steering-pump | conditional | conditional:trim | 1380 |
| power-steering-pump | conditional | conditional:unknown | 348 |
| power-steering-pump | reman_only | reman_only | 34 |
| radiator | unmapped | - | 2128 |
| radiator | no_records | - | 2713 |
| radiator | split | no_candidates | 17 |
| radiator | split | option_split | 26093 |
| radiator | conditional | conditional:body | 78 |
| radiator | conditional | conditional:colour | 979 |
| radiator | conditional | conditional:engine | 748 |
| radiator | conditional | conditional:engine_unattested | 1 |
| radiator | conditional | conditional:notes_not_own_page | 4764 |
| radiator | conditional | conditional:option | 836 |
| radiator | conditional | conditional:production | 152 |
| radiator | conditional | conditional:trim | 5550 |
| radiator | conditional | conditional:unknown | 16 |
| radiator | blocked | unverified_member | 52 |
| radiator | gated | kind_not_phase1 | 9 |
| side-mirrors | unmapped | - | 2128 |
| side-mirrors | no_records | - | 4169 |
| side-mirrors | split | no_candidates | 85 |
| side-mirrors | split | option_split | 36272 |
| side-mirrors | split | position_conflict | 2 |
| side-mirrors | split | position_missing | 204 |
| side-mirrors | split | slot_missing | 493 |
| side-mirrors | conditional | conditional:colour | 7 |
| side-mirrors | conditional | conditional:notes_not_own_page | 62 |
| side-mirrors | conditional | conditional:option | 9 |
| side-mirrors | conditional | conditional:trim | 705 |
| starter | unmapped | - | 2128 |
| starter | no_records | - | 2450 |
| starter | split | no_candidates | 148 |
| starter | split | option_split | 36947 |
| starter | conditional | conditional:engine | 153 |
| starter | conditional | conditional:engine_unattested | 141 |
| starter | conditional | conditional:engine_unparsed | 27 |
| starter | conditional | conditional:listed_not_fitted | 7 |
| starter | conditional | conditional:notes_not_own_page | 484 |
| starter | conditional | conditional:option | 84 |
| starter | conditional | conditional:option_layout | 27 |
| starter | conditional | conditional:trim | 1525 |
| starter | conditional | conditional:trim_unknown | 6 |
| starter | blocked | unverified_member | 9 |
| tail-lights | unmapped | - | 2128 |
| tail-lights | no_records | - | 9459 |
| tail-lights | split | no_candidates | 80 |
| tail-lights | split | option_split | 15422 |
| tail-lights | split | position_missing | 133 |
| tail-lights | split | slot_missing | 7 |
| tail-lights | conditional | conditional:body | 203 |
| tail-lights | conditional | conditional:engine | 2547 |
| tail-lights | conditional | conditional:engine_unparsed | 27 |
| tail-lights | conditional | conditional:model_other | 12 |
| tail-lights | conditional | conditional:notes_not_own_page | 2313 |
| tail-lights | conditional | conditional:option | 217 |
| tail-lights | conditional | conditional:option_layout | 151 |
| tail-lights | conditional | conditional:trim | 10364 |
| tail-lights | chain_member_conditional | chain_member_conditional | 516 |
| tail-lights | blocked | unverified_member | 139 |
| tail-lights | eligible | - | 418 |
| tailgate | unmapped | - | 2128 |
| tailgate | no_records | - | 38178 |
| tailgate | split | no_candidates | 795 |
| tailgate | conditional | conditional:engine_unattested | 8 |
| tailgate | conditional | conditional:notes_not_own_page | 54 |
| tailgate | conditional | conditional:option | 78 |
| tailgate | conditional | conditional:qualifier | 167 |
| tailgate | conditional | conditional:trim | 2721 |
| tailgate | conditional | conditional:unknown | 7 |
| throttle-body | unmapped | - | 2128 |
| throttle-body | no_records | - | 2354 |
| throttle-body | split | no_candidates | 86 |
| throttle-body | split | option_split | 31869 |
| throttle-body | conditional | conditional:engine | 1169 |
| throttle-body | conditional | conditional:engine_unattested | 13 |
| throttle-body | conditional | conditional:engine_unparsed | 19 |
| throttle-body | conditional | conditional:fitted_not_listed | 175 |
| throttle-body | conditional | conditional:notes_not_own_page | 3550 |
| throttle-body | conditional | conditional:option | 55 |
| throttle-body | conditional | conditional:option_layout | 47 |
| throttle-body | conditional | conditional:package | 150 |
| throttle-body | conditional | conditional:qualifier | 69 |
| throttle-body | conditional | conditional:trim | 1873 |
| throttle-body | chain_member_conditional | chain_member_conditional | 579 |
| tow-mirrors | unmapped | - | 2128 |
| tow-mirrors | no_records | - | 39476 |
| tow-mirrors | split | option_split | 2528 |
| tow-mirrors | conditional | conditional:trim | 4 |
| trunk-lid | unmapped | - | 2128 |
| trunk-lid | no_records | - | 40824 |
| trunk-lid | split | no_candidates | 373 |
| trunk-lid | conditional | conditional:notes_not_own_page | 210 |
| trunk-lid | conditional | conditional:option_layout | 601 |
| wheels | unmapped | - | 2128 |
| wheels | no_records | - | 1471 |
| wheels | split | no_candidates | 61 |
| wheels | split | option_split | 38994 |
| wheels | conditional | conditional:colour | 115 |
| wheels | conditional | conditional:engine | 5 |
| wheels | conditional | conditional:engine_unparsed | 3 |
| wheels | conditional | conditional:notes_not_own_page | 112 |
| wheels | conditional | conditional:trim | 1238 |
| wheels | conditional | conditional:unknown | 9 |
| window-regulator | unmapped | - | 2128 |
| window-regulator | no_records | - | 2457 |
| window-regulator | split | no_candidates | 80 |
| window-regulator | split | packaging_incomplete | 44 |
| window-regulator | split | packaging_unstated | 39427 |
| window-switch | unmapped | - | 2128 |
| window-switch | no_records | - | 8803 |
| window-switch | split | no_candidates | 851 |
| window-switch | split | option_split | 23284 |
| window-switch | split | position_missing | 8542 |
| window-switch | conditional | conditional:notes_not_own_page | 169 |
| window-switch | conditional | conditional:trim | 359 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_pn: 4
- cross_category_supersession: 357
- disputed_class: 809
- exclude_at_curation: 2
- held_exterior_cross_model: 63
- recrawl_resolved: 5
- rule_drift: 66
- universal_part_suspect: 33
- wheel_axle_limited: 2
- wheel_body_conflict: 1
- wheel_compact_spare: 6
- wheel_model_other: 2
- wheel_size_conflict: 3
- wheel_size_unstated: 42
- wheel_spare_description: 3
- wheel_width_conflict: 2

## Unknown note clauses (top 30)

- `D - DODGE`: 519
- `C - CHRYSLER`: 403
- `E - DODGE AWD`: 294
- `With Body Color`: 260
- `F - BRAND AWD`: 253
- `Package Quantity: 1`: 218
- `With Power Fold`: 203
- `All Models`: 198
- `62 - REG CAB 8 FT BOX`: 144
- `Without Power Fold`: 134
- `K - DODGE`: 127
- `ERB - 6 Cyl 3.6L VVT`: 121
- `Body Color`: 119
- `With Foldaway`: 115
- `Y - CHRYSLER`: 112
- `Require Quantity: 2`: 107
- `All`: 105
- `Remanufactured`: 96
- `EZH - 8 Cyl 5.7L HEMI MDS VVT`: 86
- `7 - Med. Duty DODGE 4WD`: 83
- `Man Fold`: 80
- `81 - Mega Cab`: 76
- `41 - SEDAN/QUAD CAB SWB`: 75
- `ED3 - 4 Cyl 2.4L DOHC Dual VVT`: 75
- `Without Foldaway`: 74
- `61 - REG CAB 6.5 FT BOX`: 73
- `3.3 & 3.8L`: 71
- `6 - Lt. Duty DODGE 4WD`: 66
- `98 - CREW CAB W.B.9`: 66
- `91 - CREW CAB W.B.2`: 64

## Unmapped catalog models

- Chrysler Crossfire: feed 'Crossfire' 50 cars
- Chrysler E Class: feed 'E Class' 0 cars
- Chrysler Executive Limousine: feed 'Executive Limousine' 0 cars
- Chrysler Executive Sedan: feed 'Executive Sedan' 0 cars
- Chrysler Grand Voyager: feed 'Grand Voyager' 8 cars
- Chrysler Laser: feed 'Laser' 0 cars
- Chrysler Prowler: feed 'Prowler' 0 cars (excluded: catalog model with no feed cars as 'Prowler' (inventory 2026-11-04); nothing to map)
- Dodge 600: feed '600' 6 cars
- Dodge D250: feed 'D250' 10 cars (excluded: M3: the feed spells this truck 'D250', 'D-250' and 'D250 Pickup' (one squash key); not mapped until the feed normalizes them)
- Dodge Monaco: feed 'Monaco' 4 cars
- Dodge Omni: feed 'Omni' 1 cars (excluded: catalog model with no feed cars as 'Omni' (inventory 2026-11-04); nothing to map)
- Dodge Ram 4500: feed 'Ram 4500' 0 cars (excluded: catalog model with no feed cars as 'Ram 4500' (inventory 2026-11-04); nothing to map)
- Dodge Ram 5500: feed 'Ram 5500' 0 cars (excluded: catalog model with no feed cars as 'Ram 5500' (inventory 2026-11-04); nothing to map)
- Dodge Sprinter 2500: feed 'Sprinter 2500' 21 cars
- Dodge Sprinter 3500: feed 'Sprinter 3500' 8 cars
- Dodge Viper: feed 'Viper' 0 cars (excluded: catalog model with no feed cars as 'Viper' (inventory 2026-11-04); nothing to map)
- Jeep Gladiator: feed 'Gladiator' 1 cars
- Jeep J20: feed 'J20' 0 cars (excluded: catalog model with no feed cars as 'J20' (inventory 2026-11-04); nothing to map)
- Ram 4500: feed '4500' 0 cars
- Ram 5500: feed '5500' 0 cars
- Ram ProMaster EV: feed 'ProMaster EV' 0 cars
