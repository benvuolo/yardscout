# OEM curation report: mopar

Raw: `c36da2eb98835c02f81c05e8c36b6a926634a332` @ `c36da2eb9883`; as of 2026-11-06T20:19:29Z.

- records 7856, classes 7047, list rows 78527, year manifests 317, cells 12219
- Verified groups 0, engine vg groups 0, Likely groups 281
- blocked sites: www.moparpartsgiant.com

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.moparpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.moparpartsgiant.com: only 3% of its 7351 fitment rows can be coverage: its option column holds trims (option_column_is_trims), which count only after a namespace audit (spec 5.2)
- blocked by the crawl breaker: www.moparpartsgiant.com (their cells never close, C9)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2132 |
| ac-compressor | no_records | - | 3653 |
| ac-compressor | not_closed | list_manifest_bad | 7 |
| ac-compressor | not_closed | no_list_manifest | 285 |
| ac-compressor | not_closed | no_year_manifest | 29980 |
| ac-compressor | not_closed | site_blocked | 67 |
| ac-compressor | not_closed | stale | 26 |
| ac-compressor | not_closed | suspect_variant | 230 |
| ac-compressor | not_closed | unattested | 13 |
| ac-compressor | not_closed | uncrawled_chain_member | 1543 |
| ac-compressor | not_closed | unread_sibling_page | 2020 |
| ac-compressor | not_closed | unverified_product | 4224 |
| ac-compressor | not_closed | year_manifest_bad | 2 |
| alternator | unmapped | - | 2132 |
| alternator | no_records | - | 1269 |
| alternator | not_closed | list_manifest_bad | 7 |
| alternator | not_closed | no_list_manifest | 313 |
| alternator | not_closed | no_year_manifest | 32364 |
| alternator | not_closed | site_blocked | 40 |
| alternator | not_closed | suspect_variant | 453 |
| alternator | not_closed | unattested | 3 |
| alternator | not_closed | uncrawled_chain_member | 140 |
| alternator | not_closed | unread_sibling_page | 2013 |
| alternator | not_closed | unverified_product | 5446 |
| alternator | not_closed | year_manifest_bad | 2 |
| bumper-front | unmapped | - | 2132 |
| bumper-front | no_records | - | 9212 |
| bumper-front | not_closed | no_list_manifest | 447 |
| bumper-front | not_closed | no_year_manifest | 24734 |
| bumper-front | not_closed | unread_sibling_page | 7655 |
| bumper-front | not_closed | year_manifest_bad | 2 |
| bumper-rear | unmapped | - | 2132 |
| bumper-rear | no_records | - | 7186 |
| bumper-rear | not_closed | no_list_manifest | 531 |
| bumper-rear | not_closed | no_year_manifest | 26682 |
| bumper-rear | not_closed | unread_sibling_page | 7649 |
| bumper-rear | not_closed | year_manifest_bad | 2 |
| climate-control | unmapped | - | 2132 |
| climate-control | no_records | - | 11687 |
| climate-control | not_closed | no_list_manifest | 1270 |
| climate-control | not_closed | no_year_manifest | 22640 |
| climate-control | not_closed | unread_sibling_page | 6453 |
| door-front | unmapped | - | 2132 |
| door-front | no_records | - | 6327 |
| door-front | not_closed | no_list_manifest | 521 |
| door-front | not_closed | no_year_manifest | 27551 |
| door-front | not_closed | unread_sibling_page | 7649 |
| door-front | not_closed | year_manifest_bad | 2 |
| door-rear | unmapped | - | 2132 |
| door-rear | no_records | - | 12941 |
| door-rear | not_closed | no_list_manifest | 227 |
| door-rear | not_closed | no_year_manifest | 21233 |
| door-rear | not_closed | unread_sibling_page | 7649 |
| fender | unmapped | - | 2132 |
| fender | no_records | - | 12130 |
| fender | not_closed | no_list_manifest | 652 |
| fender | not_closed | no_year_manifest | 21654 |
| fender | not_closed | site_blocked | 379 |
| fender | not_closed | uncrawled_chain_member | 569 |
| fender | not_closed | unread_sibling_page | 5842 |
| fender | not_closed | unverified_product | 600 |
| fender | not_closed | year_manifest_bad | 2 |
| fender | split | no_candidates | 214 |
| fender | conditional | conditional:trim | 8 |
| fuel-pump-module | unmapped | - | 2132 |
| fuel-pump-module | no_records | - | 3903 |
| fuel-pump-module | not_closed | list_manifest_bad | 7 |
| fuel-pump-module | not_closed | no_list_manifest | 285 |
| fuel-pump-module | not_closed | no_year_manifest | 29732 |
| fuel-pump-module | not_closed | unread_sibling_page | 8123 |
| gauge-cluster | unmapped | - | 2132 |
| gauge-cluster | no_records | - | 26057 |
| gauge-cluster | not_closed | no_list_manifest | 272 |
| gauge-cluster | not_closed | no_year_manifest | 8245 |
| gauge-cluster | not_closed | unread_sibling_page | 7476 |
| grille | unmapped | - | 2132 |
| grille | no_records | - | 12490 |
| grille | not_closed | no_list_manifest | 458 |
| grille | not_closed | no_year_manifest | 21445 |
| grille | not_closed | suspect_variant | 401 |
| grille | not_closed | uncrawled_chain_member | 231 |
| grille | not_closed | unread_sibling_page | 4415 |
| grille | not_closed | unverified_product | 1234 |
| grille | not_closed | year_manifest_bad | 2 |
| grille | split | no_candidates | 41 |
| grille | split | option_split | 439 |
| grille | conditional | conditional:colour | 72 |
| grille | conditional | conditional:engine | 20 |
| grille | conditional | conditional:model_other | 484 |
| grille | conditional | conditional:position | 17 |
| grille | conditional | conditional:trim | 281 |
| grille | gated | category_unconfirmed | 20 |
| headlights | unmapped | - | 2132 |
| headlights | no_records | - | 7410 |
| headlights | not_closed | list_manifest_bad | 7 |
| headlights | not_closed | no_list_manifest | 286 |
| headlights | not_closed | no_year_manifest | 26255 |
| headlights | not_closed | site_blocked | 140 |
| headlights | not_closed | suspect_variant | 12 |
| headlights | not_closed | uncrawled_chain_member | 34 |
| headlights | not_closed | unread_sibling_page | 7904 |
| headlights | not_closed | year_manifest_bad | 2 |
| hood | unmapped | - | 2132 |
| hood | no_records | - | 6577 |
| hood | not_closed | no_list_manifest | 330 |
| hood | not_closed | no_year_manifest | 27476 |
| hood | not_closed | suspect_variant | 401 |
| hood | not_closed | uncrawled_chain_member | 268 |
| hood | not_closed | unread_sibling_page | 5622 |
| hood | not_closed | unverified_product | 1332 |
| hood | not_closed | year_manifest_bad | 2 |
| hood | conditional | conditional:engine | 18 |
| hood | conditional | conditional:option | 16 |
| hood | conditional | conditional:trim | 8 |
| ignition-coils | unmapped | - | 2132 |
| ignition-coils | no_records | - | 972 |
| ignition-coils | not_closed | no_list_manifest | 755 |
| ignition-coils | not_closed | no_year_manifest | 32691 |
| ignition-coils | not_closed | unread_sibling_page | 6900 |
| ignition-coils | not_closed | unverified_product | 730 |
| ignition-coils | not_closed | year_manifest_bad | 2 |
| liftgate | unmapped | - | 2132 |
| liftgate | no_records | - | 23773 |
| liftgate | not_closed | no_list_manifest | 439 |
| liftgate | not_closed | no_year_manifest | 14093 |
| liftgate | not_closed | unread_sibling_page | 3745 |
| power-steering-pump | unmapped | - | 2132 |
| power-steering-pump | no_records | - | 4940 |
| power-steering-pump | not_closed | list_manifest_bad | 7 |
| power-steering-pump | not_closed | no_list_manifest | 443 |
| power-steering-pump | not_closed | no_year_manifest | 29809 |
| power-steering-pump | not_closed | unread_sibling_page | 6851 |
| radiator | unmapped | - | 2132 |
| radiator | no_records | - | 2724 |
| radiator | not_closed | no_list_manifest | 677 |
| radiator | not_closed | no_year_manifest | 30975 |
| radiator | not_closed | uncrawled_chain_member | 401 |
| radiator | not_closed | unread_sibling_page | 7217 |
| radiator | not_closed | unverified_product | 54 |
| radiator | not_closed | year_manifest_bad | 2 |
| side-mirrors | unmapped | - | 2132 |
| side-mirrors | no_records | - | 4178 |
| side-mirrors | not_closed | no_list_manifest | 572 |
| side-mirrors | not_closed | no_year_manifest | 29654 |
| side-mirrors | not_closed | site_blocked | 80 |
| side-mirrors | not_closed | unattested | 13 |
| side-mirrors | not_closed | unread_sibling_page | 7545 |
| side-mirrors | conditional | conditional:option | 8 |
| starter | unmapped | - | 2132 |
| starter | no_records | - | 2461 |
| starter | not_closed | list_manifest_bad | 7 |
| starter | not_closed | no_list_manifest | 332 |
| starter | not_closed | no_year_manifest | 31205 |
| starter | not_closed | site_blocked | 13 |
| starter | not_closed | stale | 26 |
| starter | not_closed | suspect_variant | 354 |
| starter | not_closed | uncrawled_chain_member | 169 |
| starter | not_closed | unread_sibling_page | 1932 |
| starter | not_closed | unverified_product | 5549 |
| starter | not_closed | year_manifest_bad | 2 |
| tail-lights | unmapped | - | 2132 |
| tail-lights | no_records | - | 9461 |
| tail-lights | not_closed | list_manifest_bad | 7 |
| tail-lights | not_closed | no_list_manifest | 97 |
| tail-lights | not_closed | no_year_manifest | 24393 |
| tail-lights | not_closed | site_blocked | 1670 |
| tail-lights | not_closed | stale | 26 |
| tail-lights | not_closed | suspect_variant | 42 |
| tail-lights | not_closed | uncrawled_chain_member | 1059 |
| tail-lights | not_closed | unread_sibling_page | 2026 |
| tail-lights | not_closed | unverified_product | 3043 |
| tail-lights | not_closed | year_manifest_bad | 2 |
| tail-lights | split | no_candidates | 10 |
| tail-lights | split | slot_missing | 7 |
| tail-lights | conditional | conditional:trim | 207 |
| tailgate | unmapped | - | 2132 |
| tailgate | no_records | - | 38204 |
| tailgate | not_closed | no_list_manifest | 40 |
| tailgate | not_closed | no_year_manifest | 2437 |
| tailgate | not_closed | site_blocked | 379 |
| tailgate | not_closed | uncrawled_chain_member | 1 |
| tailgate | not_closed | unread_sibling_page | 581 |
| tailgate | not_closed | unverified_product | 408 |
| throttle-body | unmapped | - | 2132 |
| throttle-body | no_records | - | 2363 |
| throttle-body | not_closed | list_manifest_bad | 7 |
| throttle-body | not_closed | no_list_manifest | 455 |
| throttle-body | not_closed | no_year_manifest | 31286 |
| throttle-body | not_closed | site_blocked | 1663 |
| throttle-body | not_closed | suspect_variant | 351 |
| throttle-body | not_closed | unattested | 9 |
| throttle-body | not_closed | uncrawled_chain_member | 13 |
| throttle-body | not_closed | unread_sibling_page | 1939 |
| throttle-body | not_closed | unverified_product | 3962 |
| throttle-body | not_closed | year_manifest_bad | 2 |
| tow-mirrors | unmapped | - | 2132 |
| tow-mirrors | no_records | - | 39509 |
| tow-mirrors | not_closed | no_list_manifest | 527 |
| tow-mirrors | not_closed | no_year_manifest | 2014 |
| trunk-lid | unmapped | - | 2132 |
| trunk-lid | no_records | - | 40863 |
| trunk-lid | not_closed | no_year_manifest | 208 |
| trunk-lid | not_closed | site_blocked | 54 |
| trunk-lid | not_closed | unread_sibling_page | 925 |
| window-regulator | unmapped | - | 2132 |
| window-regulator | no_records | - | 2461 |
| window-regulator | not_closed | list_manifest_bad | 7 |
| window-regulator | not_closed | no_list_manifest | 758 |
| window-regulator | not_closed | no_year_manifest | 31339 |
| window-regulator | not_closed | site_blocked | 397 |
| window-regulator | not_closed | stale | 26 |
| window-regulator | not_closed | suspect_variant | 18 |
| window-regulator | not_closed | unattested | 9 |
| window-regulator | not_closed | uncrawled_chain_member | 972 |
| window-regulator | not_closed | unread_sibling_page | 3505 |
| window-regulator | not_closed | unverified_product | 1889 |
| window-regulator | not_closed | year_manifest_bad | 2 |
| window-regulator | split | packaging_unstated | 667 |
| window-switch | unmapped | - | 2132 |
| window-switch | no_records | - | 8813 |
| window-switch | not_closed | list_manifest_bad | 7 |
| window-switch | not_closed | no_list_manifest | 300 |
| window-switch | not_closed | no_year_manifest | 24856 |
| window-switch | not_closed | site_blocked | 14 |
| window-switch | not_closed | stale | 26 |
| window-switch | not_closed | suspect_variant | 19 |
| window-switch | not_closed | unread_sibling_page | 8015 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2132 |
| ac-compressor | no_records | - | 3653 |
| ac-compressor | split | no_candidates | 93 |
| ac-compressor | split | option_split | 33516 |
| ac-compressor | conditional | conditional:engine | 20 |
| ac-compressor | conditional | conditional:engine_unattested | 41 |
| ac-compressor | conditional | conditional:engine_unparsed | 21 |
| ac-compressor | conditional | conditional:notes_not_own_page | 2060 |
| ac-compressor | conditional | conditional:option | 51 |
| ac-compressor | conditional | conditional:qualifier | 193 |
| ac-compressor | conditional | conditional:trim | 2386 |
| ac-compressor | chain_member_conditional | chain_member_conditional | 9 |
| ac-compressor | gated | kind_not_phase1 | 7 |
| alternator | unmapped | - | 2132 |
| alternator | no_records | - | 1269 |
| alternator | split | no_candidates | 3 |
| alternator | split | option_split | 35622 |
| alternator | conditional | conditional:engine | 1554 |
| alternator | conditional | conditional:engine_unattested | 69 |
| alternator | conditional | conditional:engine_unparsed | 20 |
| alternator | conditional | conditional:fitted_not_listed | 7 |
| alternator | conditional | conditional:notes_not_own_page | 239 |
| alternator | conditional | conditional:option | 188 |
| alternator | conditional | conditional:trim | 3079 |
| bumper-front | unmapped | - | 2132 |
| bumper-front | no_records | - | 9212 |
| bumper-front | split | no_candidates | 25 |
| bumper-front | split | option_split | 26553 |
| bumper-front | conditional | conditional:engine | 2483 |
| bumper-front | conditional | conditional:model_other | 12 |
| bumper-front | conditional | conditional:notes_not_own_page | 840 |
| bumper-front | conditional | conditional:trim | 2493 |
| bumper-front | eligible | - | 432 |
| bumper-rear | unmapped | - | 2132 |
| bumper-rear | no_records | - | 7186 |
| bumper-rear | split | no_candidates | 448 |
| bumper-rear | split | option_split | 30105 |
| bumper-rear | conditional | conditional:colour | 113 |
| bumper-rear | conditional | conditional:engine | 67 |
| bumper-rear | conditional | conditional:model_other | 2 |
| bumper-rear | conditional | conditional:notes_not_own_page | 1509 |
| bumper-rear | conditional | conditional:trim | 2562 |
| bumper-rear | eligible | - | 58 |
| climate-control | unmapped | - | 2132 |
| climate-control | no_records | - | 11687 |
| climate-control | split | no_candidates | 52 |
| climate-control | split | option_split | 25031 |
| climate-control | conditional | conditional:engine | 49 |
| climate-control | conditional | conditional:engine_unattested | 2 |
| climate-control | conditional | conditional:fitted_not_listed | 37 |
| climate-control | conditional | conditional:notes_not_own_page | 1748 |
| climate-control | conditional | conditional:option | 22 |
| climate-control | conditional | conditional:option_layout | 165 |
| climate-control | conditional | conditional:trim | 3248 |
| climate-control | blocked | unverified_member | 9 |
| door-front | unmapped | - | 2132 |
| door-front | no_records | - | 6327 |
| door-front | split | no_candidates | 149 |
| door-front | split | option_split | 8924 |
| door-front | split | position_missing | 73 |
| door-front | split | slot_missing | 340 |
| door-front | conditional | conditional:engine | 1609 |
| door-front | conditional | conditional:notes_not_own_page | 3895 |
| door-front | conditional | conditional:production | 48 |
| door-front | conditional | conditional:trim | 18703 |
| door-front | conditional | conditional:unknown | 7 |
| door-front | eligible | - | 1975 |
| door-rear | unmapped | - | 2132 |
| door-rear | no_records | - | 12941 |
| door-rear | split | no_candidates | 1926 |
| door-rear | split | option_split | 4266 |
| door-rear | split | position_missing | 93 |
| door-rear | split | slot_missing | 782 |
| door-rear | conditional | conditional:body | 432 |
| door-rear | conditional | conditional:fitted_not_listed | 351 |
| door-rear | conditional | conditional:notes_not_own_page | 6388 |
| door-rear | conditional | conditional:option_layout | 634 |
| door-rear | conditional | conditional:trim | 11804 |
| door-rear | eligible | - | 2396 |
| door-rear | grouped | - | 37 |
| fender | unmapped | - | 2132 |
| fender | no_records | - | 12130 |
| fender | split | no_candidates | 1319 |
| fender | split | option_split | 7492 |
| fender | split | position_missing | 12 |
| fender | split | slot_missing | 63 |
| fender | conditional | conditional:body | 202 |
| fender | conditional | conditional:engine | 2278 |
| fender | conditional | conditional:notes_not_own_page | 3441 |
| fender | conditional | conditional:option | 10 |
| fender | conditional | conditional:trim | 13109 |
| fender | chain_member_conditional | chain_member_conditional | 806 |
| fender | eligible | - | 1155 |
| fender | grouped | - | 33 |
| fuel-pump-module | unmapped | - | 2132 |
| fuel-pump-module | no_records | - | 3903 |
| fuel-pump-module | split | no_candidates | 190 |
| fuel-pump-module | split | option_split | 30830 |
| fuel-pump-module | conditional | conditional:engine | 441 |
| fuel-pump-module | conditional | conditional:engine_unattested | 64 |
| fuel-pump-module | conditional | conditional:engine_unparsed | 33 |
| fuel-pump-module | conditional | conditional:fitted_not_listed | 31 |
| fuel-pump-module | conditional | conditional:fuel | 31 |
| fuel-pump-module | conditional | conditional:notes_not_own_page | 1573 |
| fuel-pump-module | conditional | conditional:package | 2 |
| fuel-pump-module | conditional | conditional:trim | 4943 |
| fuel-pump-module | blocked | unverified_member | 9 |
| gauge-cluster | unmapped | - | 2132 |
| gauge-cluster | no_records | - | 26057 |
| gauge-cluster | split | no_candidates | 1562 |
| gauge-cluster | split | option_split | 12867 |
| gauge-cluster | conditional | conditional:engine | 389 |
| gauge-cluster | conditional | conditional:notes_not_own_page | 541 |
| gauge-cluster | conditional | conditional:trim | 604 |
| gauge-cluster | eligible | - | 30 |
| grille | unmapped | - | 2132 |
| grille | no_records | - | 12490 |
| grille | split | no_candidates | 361 |
| grille | split | option_split | 18198 |
| grille | conditional | conditional:body | 407 |
| grille | conditional | conditional:colour | 82 |
| grille | conditional | conditional:engine | 801 |
| grille | conditional | conditional:model_other | 484 |
| grille | conditional | conditional:notes_not_own_page | 2128 |
| grille | conditional | conditional:option | 137 |
| grille | conditional | conditional:position | 17 |
| grille | conditional | conditional:trim | 6188 |
| grille | chain_member_conditional | chain_member_conditional | 419 |
| grille | eligible | - | 338 |
| headlights | unmapped | - | 2132 |
| headlights | no_records | - | 7410 |
| headlights | split | no_candidates | 379 |
| headlights | split | option_split | 26208 |
| headlights | split | position_missing | 468 |
| headlights | split | slot_missing | 120 |
| headlights | conditional | conditional:engine | 277 |
| headlights | conditional | conditional:fitted_not_listed | 15 |
| headlights | conditional | conditional:notes_not_own_page | 1695 |
| headlights | conditional | conditional:option | 200 |
| headlights | conditional | conditional:option_layout | 13 |
| headlights | conditional | conditional:production | 23 |
| headlights | conditional | conditional:trim | 4510 |
| headlights | conditional | conditional:unknown | 264 |
| headlights | chain_member_conditional | chain_member_conditional | 222 |
| headlights | eligible | - | 246 |
| hood | unmapped | - | 2132 |
| hood | no_records | - | 6577 |
| hood | split | no_candidates | 142 |
| hood | split | option_split | 3747 |
| hood | conditional | conditional:body | 203 |
| hood | conditional | conditional:engine | 2868 |
| hood | conditional | conditional:engine_unparsed | 15 |
| hood | conditional | conditional:notes_not_own_page | 8093 |
| hood | conditional | conditional:option | 2174 |
| hood | conditional | conditional:option_layout | 629 |
| hood | conditional | conditional:trim | 15857 |
| hood | conditional | conditional:unknown | 8 |
| hood | chain_member_conditional | chain_member_conditional | 645 |
| hood | blocked | unverified_member | 255 |
| hood | eligible | - | 804 |
| hood | grouped | - | 33 |
| ignition-coils | unmapped | - | 2132 |
| ignition-coils | no_records | - | 972 |
| ignition-coils | split | option_split | 27988 |
| ignition-coils | conditional | conditional:body | 203 |
| ignition-coils | conditional | conditional:engine | 2299 |
| ignition-coils | conditional | conditional:engine_unattested | 230 |
| ignition-coils | conditional | conditional:engine_unparsed | 49 |
| ignition-coils | conditional | conditional:notes_not_own_page | 4825 |
| ignition-coils | conditional | conditional:option | 526 |
| ignition-coils | conditional | conditional:option_layout | 29 |
| ignition-coils | conditional | conditional:trim | 4527 |
| ignition-coils | chain_member_conditional | chain_member_conditional | 169 |
| ignition-coils | blocked | unverified_member | 233 |
| liftgate | unmapped | - | 2132 |
| liftgate | no_records | - | 23773 |
| liftgate | split | no_candidates | 342 |
| liftgate | split | option_split | 1684 |
| liftgate | conditional | conditional:engine | 1554 |
| liftgate | conditional | conditional:notes_not_own_page | 4452 |
| liftgate | conditional | conditional:trim | 8711 |
| liftgate | eligible | - | 1534 |
| power-steering-pump | unmapped | - | 2132 |
| power-steering-pump | no_records | - | 4940 |
| power-steering-pump | split | no_candidates | 180 |
| power-steering-pump | split | option_split | 30794 |
| power-steering-pump | conditional | conditional:engine | 838 |
| power-steering-pump | conditional | conditional:engine_unparsed | 32 |
| power-steering-pump | conditional | conditional:notes_not_own_page | 2837 |
| power-steering-pump | conditional | conditional:option_layout | 9 |
| power-steering-pump | conditional | conditional:qualifier | 672 |
| power-steering-pump | conditional | conditional:trim | 1365 |
| power-steering-pump | conditional | conditional:unknown | 349 |
| power-steering-pump | reman_only | reman_only | 34 |
| radiator | unmapped | - | 2132 |
| radiator | no_records | - | 2724 |
| radiator | split | no_candidates | 17 |
| radiator | split | option_split | 26119 |
| radiator | conditional | conditional:body | 78 |
| radiator | conditional | conditional:colour | 980 |
| radiator | conditional | conditional:engine | 749 |
| radiator | conditional | conditional:engine_unattested | 1 |
| radiator | conditional | conditional:notes_not_own_page | 4767 |
| radiator | conditional | conditional:option | 836 |
| radiator | conditional | conditional:production | 152 |
| radiator | conditional | conditional:trim | 5547 |
| radiator | conditional | conditional:unknown | 17 |
| radiator | blocked | unverified_member | 54 |
| radiator | gated | kind_not_phase1 | 9 |
| side-mirrors | unmapped | - | 2132 |
| side-mirrors | no_records | - | 4178 |
| side-mirrors | split | no_candidates | 85 |
| side-mirrors | split | option_split | 36302 |
| side-mirrors | split | position_conflict | 2 |
| side-mirrors | split | position_missing | 206 |
| side-mirrors | split | slot_missing | 492 |
| side-mirrors | conditional | conditional:colour | 8 |
| side-mirrors | conditional | conditional:notes_not_own_page | 61 |
| side-mirrors | conditional | conditional:option | 8 |
| side-mirrors | conditional | conditional:trim | 708 |
| starter | unmapped | - | 2132 |
| starter | no_records | - | 2461 |
| starter | split | no_candidates | 150 |
| starter | split | option_split | 36964 |
| starter | conditional | conditional:engine | 153 |
| starter | conditional | conditional:engine_unattested | 142 |
| starter | conditional | conditional:engine_unparsed | 27 |
| starter | conditional | conditional:listed_not_fitted | 7 |
| starter | conditional | conditional:notes_not_own_page | 485 |
| starter | conditional | conditional:option | 85 |
| starter | conditional | conditional:option_layout | 27 |
| starter | conditional | conditional:trim | 1534 |
| starter | conditional | conditional:trim_unknown | 6 |
| starter | blocked | unverified_member | 9 |
| tail-lights | unmapped | - | 2132 |
| tail-lights | no_records | - | 9461 |
| tail-lights | split | no_candidates | 80 |
| tail-lights | split | option_split | 15429 |
| tail-lights | split | position_missing | 133 |
| tail-lights | split | slot_missing | 7 |
| tail-lights | conditional | conditional:body | 203 |
| tail-lights | conditional | conditional:engine | 2547 |
| tail-lights | conditional | conditional:engine_unparsed | 27 |
| tail-lights | conditional | conditional:model_other | 12 |
| tail-lights | conditional | conditional:notes_not_own_page | 2323 |
| tail-lights | conditional | conditional:option | 218 |
| tail-lights | conditional | conditional:option_layout | 153 |
| tail-lights | conditional | conditional:trim | 10382 |
| tail-lights | chain_member_conditional | chain_member_conditional | 516 |
| tail-lights | blocked | unverified_member | 138 |
| tail-lights | eligible | - | 421 |
| tailgate | unmapped | - | 2132 |
| tailgate | no_records | - | 38204 |
| tailgate | split | no_candidates | 802 |
| tailgate | conditional | conditional:engine_unattested | 8 |
| tailgate | conditional | conditional:notes_not_own_page | 444 |
| tailgate | conditional | conditional:option | 78 |
| tailgate | conditional | conditional:qualifier | 167 |
| tailgate | conditional | conditional:trim | 2340 |
| tailgate | conditional | conditional:unknown | 7 |
| throttle-body | unmapped | - | 2132 |
| throttle-body | no_records | - | 2363 |
| throttle-body | split | no_candidates | 84 |
| throttle-body | split | option_split | 31903 |
| throttle-body | conditional | conditional:engine | 1182 |
| throttle-body | conditional | conditional:engine_unattested | 14 |
| throttle-body | conditional | conditional:engine_unparsed | 19 |
| throttle-body | conditional | conditional:fitted_not_listed | 175 |
| throttle-body | conditional | conditional:notes_not_own_page | 3543 |
| throttle-body | conditional | conditional:option | 54 |
| throttle-body | conditional | conditional:option_layout | 49 |
| throttle-body | conditional | conditional:package | 151 |
| throttle-body | conditional | conditional:qualifier | 69 |
| throttle-body | conditional | conditional:trim | 1864 |
| throttle-body | chain_member_conditional | chain_member_conditional | 580 |
| tow-mirrors | unmapped | - | 2132 |
| tow-mirrors | no_records | - | 39509 |
| tow-mirrors | split | option_split | 2537 |
| tow-mirrors | conditional | conditional:trim | 4 |
| trunk-lid | unmapped | - | 2132 |
| trunk-lid | no_records | - | 40863 |
| trunk-lid | split | no_candidates | 379 |
| trunk-lid | conditional | conditional:notes_not_own_page | 208 |
| trunk-lid | conditional | conditional:option_layout | 600 |
| window-regulator | unmapped | - | 2132 |
| window-regulator | no_records | - | 2461 |
| window-regulator | split | no_candidates | 80 |
| window-regulator | split | packaging_incomplete | 44 |
| window-regulator | split | packaging_unstated | 39465 |
| window-switch | unmapped | - | 2132 |
| window-switch | no_records | - | 8813 |
| window-switch | split | no_candidates | 852 |
| window-switch | split | option_split | 23298 |
| window-switch | split | position_missing | 8557 |
| window-switch | conditional | conditional:notes_not_own_page | 170 |
| window-switch | conditional | conditional:trim | 360 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_pn: 4
- cross_category_supersession: 357
- disputed_class: 809
- exclude_at_curation: 2
- held_exterior_cross_model: 63
- recrawl_resolved: 4
- rule_drift: 63
- universal_part_suspect: 33

## Unknown note clauses (top 30)

- `D - DODGE`: 487
- `C - CHRYSLER`: 389
- `E - DODGE AWD`: 275
- `With Body Color`: 260
- `F - BRAND AWD`: 246
- `With Power Fold`: 203
- `All Models`: 198
- `62 - REG CAB 8 FT BOX`: 135
- `Without Power Fold`: 134
- `ERB - 6 Cyl 3.6L VVT`: 121
- `Body Color`: 119
- `With Foldaway`: 115
- `K - DODGE`: 114
- `All`: 105
- `Y - CHRYSLER`: 104
- `Remanufactured`: 96
- `Package Quantity: 1`: 89
- `EZH - 8 Cyl 5.7L HEMI MDS VVT`: 86
- `7 - Med. Duty DODGE 4WD`: 80
- `Man Fold`: 80
- `ED3 - 4 Cyl 2.4L DOHC Dual VVT`: 75
- `Without Foldaway`: 74
- `41 - SEDAN/QUAD CAB SWB`: 72
- `81 - Mega Cab`: 72
- `3.3 & 3.8L`: 71
- `61 - REG CAB 6.5 FT BOX`: 68
- `EGH - 6 Cyl 3.8L OHV`: 64
- `With Rear AC`: 63
- `6 - Lt. Duty DODGE 4WD`: 61
- `98 - CREW CAB W.B.9`: 61

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
- Dodge Sprinter 3500: feed 'Sprinter 3500' 7 cars
- Dodge Viper: feed 'Viper' 0 cars (excluded: catalog model with no feed cars as 'Viper' (inventory 2026-11-04); nothing to map)
- Jeep Gladiator: feed 'Gladiator' 1 cars
- Jeep J20: feed 'J20' 0 cars (excluded: catalog model with no feed cars as 'J20' (inventory 2026-11-04); nothing to map)
- Ram 4500: feed '4500' 0 cars
- Ram 5500: feed '5500' 0 cars
- Ram ProMaster EV: feed 'ProMaster EV' 0 cars
