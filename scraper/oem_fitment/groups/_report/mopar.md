# OEM curation report: mopar

Raw: `50ac4a48cdc62d02bd819bec33a67d0f07d8a71e` @ `50ac4a48cdc6`; as of 2026-11-05T03:26:17Z.

- records 1716, classes 1700, list rows 0, year manifests 0, cells 3980
- Verified groups 0, engine vg groups 0, Likely groups 320
- blocked sites: www.moparpartsgiant.com

## Gates standing for the whole namespace

- no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close (C1/C2); Verified is impossible by design until the crawler writes them
- no (site, category) of this namespace has passed the audit gate (CATEGORY_STATUS has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.moparpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.moparpartsgiant.com: only 2% of its 1522 fitment rows can be coverage: its option column holds trims (option_column_is_trims), which count only after a namespace audit (spec 5.2)
- blocked by the crawl breaker: www.moparpartsgiant.com (their cells never close, C9)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2343 |
| ac-compressor | no_records | - | 20581 |
| ac-compressor | not_closed | no_year_manifest | 21260 |
| alternator | unmapped | - | 2343 |
| alternator | no_records | - | 12924 |
| alternator | not_closed | no_year_manifest | 28917 |
| bumper-front | unmapped | - | 2343 |
| bumper-front | no_records | - | 35097 |
| bumper-front | not_closed | no_year_manifest | 6744 |
| bumper-rear | unmapped | - | 2343 |
| bumper-rear | no_records | - | 33075 |
| bumper-rear | not_closed | no_year_manifest | 8766 |
| climate-control | unmapped | - | 2343 |
| climate-control | no_records | - | 29515 |
| climate-control | not_closed | no_year_manifest | 12326 |
| door-front | unmapped | - | 2343 |
| door-front | no_records | - | 34004 |
| door-front | not_closed | no_year_manifest | 7837 |
| door-rear | unmapped | - | 2343 |
| door-rear | no_records | - | 33578 |
| door-rear | not_closed | no_year_manifest | 8263 |
| fender | unmapped | - | 2343 |
| fender | no_records | - | 33944 |
| fender | not_closed | no_year_manifest | 7897 |
| fuel-pump-module | unmapped | - | 2343 |
| fuel-pump-module | no_records | - | 21889 |
| fuel-pump-module | not_closed | no_year_manifest | 19952 |
| gauge-cluster | unmapped | - | 2343 |
| gauge-cluster | no_records | - | 39548 |
| gauge-cluster | not_closed | no_year_manifest | 2293 |
| grille | unmapped | - | 2343 |
| grille | no_records | - | 36420 |
| grille | not_closed | no_year_manifest | 5421 |
| headlights | unmapped | - | 2343 |
| headlights | no_records | - | 27300 |
| headlights | not_closed | no_year_manifest | 14541 |
| hood | unmapped | - | 2343 |
| hood | no_records | - | 33613 |
| hood | not_closed | no_year_manifest | 8228 |
| ignition-coils | unmapped | - | 2343 |
| ignition-coils | no_records | - | 5052 |
| ignition-coils | not_closed | no_year_manifest | 36789 |
| liftgate | unmapped | - | 2343 |
| liftgate | no_records | - | 34968 |
| liftgate | not_closed | no_year_manifest | 6873 |
| power-steering-pump | unmapped | - | 2343 |
| power-steering-pump | no_records | - | 17998 |
| power-steering-pump | not_closed | no_year_manifest | 23843 |
| radiator | unmapped | - | 2343 |
| radiator | no_records | - | 26672 |
| radiator | not_closed | no_year_manifest | 15169 |
| side-mirrors | unmapped | - | 2343 |
| side-mirrors | no_records | - | 26277 |
| side-mirrors | not_closed | no_year_manifest | 15564 |
| starter | unmapped | - | 2343 |
| starter | no_records | - | 10436 |
| starter | not_closed | no_year_manifest | 31405 |
| tail-lights | unmapped | - | 2343 |
| tail-lights | no_records | - | 30908 |
| tail-lights | not_closed | no_year_manifest | 10933 |
| throttle-body | unmapped | - | 2343 |
| throttle-body | no_records | - | 10828 |
| throttle-body | not_closed | no_year_manifest | 31013 |
| window-regulator | unmapped | - | 2343 |
| window-regulator | no_records | - | 23321 |
| window-regulator | not_closed | no_year_manifest | 18520 |
| window-switch | unmapped | - | 2343 |
| window-switch | no_records | - | 21906 |
| window-switch | not_closed | no_year_manifest | 19935 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2343 |
| ac-compressor | no_records | - | 20581 |
| ac-compressor | split | option_split | 14390 |
| ac-compressor | conditional | conditional:notes_not_own_page | 6451 |
| ac-compressor | conditional | conditional:trim | 187 |
| ac-compressor | conditional | conditional:unknown | 232 |
| alternator | unmapped | - | 2343 |
| alternator | no_records | - | 12924 |
| alternator | split | option_split | 20969 |
| alternator | conditional | conditional:engine | 270 |
| alternator | conditional | conditional:notes_not_own_page | 7678 |
| bumper-front | unmapped | - | 2343 |
| bumper-front | no_records | - | 35097 |
| bumper-front | split | option_split | 6215 |
| bumper-front | conditional | conditional:notes_not_own_page | 387 |
| bumper-front | conditional | conditional:trim | 142 |
| bumper-rear | unmapped | - | 2343 |
| bumper-rear | no_records | - | 33075 |
| bumper-rear | split | option_split | 7664 |
| bumper-rear | conditional | conditional:notes_not_own_page | 921 |
| bumper-rear | conditional | conditional:trim | 181 |
| climate-control | unmapped | - | 2343 |
| climate-control | no_records | - | 29515 |
| climate-control | split | option_split | 8045 |
| climate-control | conditional | conditional:notes_not_own_page | 3734 |
| climate-control | conditional | conditional:trim | 547 |
| door-front | unmapped | - | 2343 |
| door-front | no_records | - | 34004 |
| door-front | split | option_split | 1857 |
| door-front | conditional | conditional:notes_not_own_page | 3643 |
| door-front | conditional | conditional:production | 47 |
| door-front | conditional | conditional:trim | 1942 |
| door-front | eligible | - | 348 |
| door-rear | unmapped | - | 2343 |
| door-rear | no_records | - | 33578 |
| door-rear | split | option_split | 1577 |
| door-rear | conditional | conditional:notes_not_own_page | 4188 |
| door-rear | conditional | conditional:trim | 1437 |
| door-rear | eligible | - | 1061 |
| fender | unmapped | - | 2343 |
| fender | no_records | - | 33944 |
| fender | split | option_split | 2596 |
| fender | conditional | conditional:notes_not_own_page | 3366 |
| fender | conditional | conditional:option_layout | 134 |
| fender | conditional | conditional:trim | 1157 |
| fender | chain_member_conditional | chain_member_conditional | 267 |
| fender | eligible | - | 377 |
| fuel-pump-module | unmapped | - | 2343 |
| fuel-pump-module | no_records | - | 21889 |
| fuel-pump-module | split | option_split | 11773 |
| fuel-pump-module | conditional | conditional:notes_not_own_page | 7364 |
| fuel-pump-module | conditional | conditional:trim | 815 |
| gauge-cluster | unmapped | - | 2343 |
| gauge-cluster | no_records | - | 39548 |
| gauge-cluster | split | option_split | 1994 |
| gauge-cluster | conditional | conditional:notes_not_own_page | 299 |
| grille | unmapped | - | 2343 |
| grille | no_records | - | 36420 |
| grille | split | option_split | 3870 |
| grille | conditional | conditional:notes_not_own_page | 1197 |
| grille | conditional | conditional:trim | 122 |
| grille | eligible | - | 232 |
| headlights | unmapped | - | 2343 |
| headlights | no_records | - | 27300 |
| headlights | split | option_split | 5243 |
| headlights | split | position_missing | 493 |
| headlights | conditional | conditional:notes_not_own_page | 7054 |
| headlights | conditional | conditional:option | 200 |
| headlights | conditional | conditional:option_layout | 722 |
| headlights | conditional | conditional:trim | 116 |
| headlights | conditional | conditional:unknown | 267 |
| headlights | chain_member_conditional | chain_member_conditional | 214 |
| headlights | eligible | - | 232 |
| hood | unmapped | - | 2343 |
| hood | no_records | - | 33613 |
| hood | split | option_split | 559 |
| hood | conditional | conditional:notes_not_own_page | 5554 |
| hood | conditional | conditional:option_layout | 200 |
| hood | conditional | conditional:trim | 1422 |
| hood | chain_member_conditional | chain_member_conditional | 167 |
| hood | eligible | - | 326 |
| ignition-coils | unmapped | - | 2343 |
| ignition-coils | no_records | - | 5052 |
| ignition-coils | split | option_split | 17648 |
| ignition-coils | conditional | conditional:engine | 1632 |
| ignition-coils | conditional | conditional:notes_not_own_page | 17277 |
| ignition-coils | eligible | - | 232 |
| liftgate | unmapped | - | 2343 |
| liftgate | no_records | - | 34968 |
| liftgate | split | option_split | 506 |
| liftgate | conditional | conditional:notes_not_own_page | 4508 |
| liftgate | conditional | conditional:trim | 1246 |
| liftgate | eligible | - | 613 |
| power-steering-pump | unmapped | - | 2343 |
| power-steering-pump | no_records | - | 17998 |
| power-steering-pump | split | option_split | 6648 |
| power-steering-pump | conditional | conditional:engine | 24 |
| power-steering-pump | conditional | conditional:notes_not_own_page | 16623 |
| power-steering-pump | conditional | conditional:trim | 200 |
| power-steering-pump | conditional | conditional:unknown | 348 |
| radiator | unmapped | - | 2343 |
| radiator | no_records | - | 26672 |
| radiator | split | option_split | 10119 |
| radiator | conditional | conditional:engine | 78 |
| radiator | conditional | conditional:notes_not_own_page | 4972 |
| side-mirrors | unmapped | - | 2343 |
| side-mirrors | no_records | - | 26277 |
| side-mirrors | split | option_split | 15056 |
| side-mirrors | split | position_missing | 125 |
| side-mirrors | split | slot_missing | 1 |
| side-mirrors | conditional | conditional:notes_not_own_page | 382 |
| starter | unmapped | - | 2343 |
| starter | no_records | - | 10436 |
| starter | split | option_split | 18328 |
| starter | conditional | conditional:engine | 1227 |
| starter | conditional | conditional:notes_not_own_page | 11850 |
| tail-lights | unmapped | - | 2343 |
| tail-lights | no_records | - | 30908 |
| tail-lights | split | option_split | 6143 |
| tail-lights | conditional | conditional:notes_not_own_page | 2849 |
| tail-lights | conditional | conditional:option_layout | 796 |
| tail-lights | conditional | conditional:trim | 815 |
| tail-lights | eligible | - | 330 |
| throttle-body | unmapped | - | 2343 |
| throttle-body | no_records | - | 10828 |
| throttle-body | split | option_split | 20209 |
| throttle-body | conditional | conditional:engine | 339 |
| throttle-body | conditional | conditional:notes_not_own_page | 10233 |
| throttle-body | chain_member_conditional | chain_member_conditional | 232 |
| window-regulator | unmapped | - | 2343 |
| window-regulator | no_records | - | 23321 |
| window-regulator | split | packaging_unstated | 18520 |
| window-switch | unmapped | - | 2343 |
| window-switch | no_records | - | 21906 |
| window-switch | split | no_candidates | 427 |
| window-switch | split | option_split | 8620 |
| window-switch | split | position_missing | 4963 |
| window-switch | conditional | conditional:notes_not_own_page | 5589 |
| window-switch | conditional | conditional:option | 122 |
| window-switch | conditional | conditional:position | 214 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- disputed_class: 16
- exclude_at_curation: 2
- universal_part_suspect: 11

## Unknown note clauses (top 30)

- `D - DODGE`: 104
- `E - DODGE AWD`: 88
- `Y - CHRYSLER`: 79
- `F - BRAND AWD`: 47
- `C - CHRYSLER`: 46
- `Sales Code [GUK]`: 22
- `All`: 20
- `P - PREMIUM`: 20
- `With Sales Code [GTL]`: 18
- `With Sales Codes [GUL] & [LEP]`: 18
- `Bumper Cover & Components`: 17
- `K - DODGE`: 16
- `Power Fold Away`: 16
- `Power Multi Function`: 16
- `Without Tow Hooks`: 16
- `EGV - 6 Cyl 3.3L OHV`: 14
- `Without Hitch`: 14
- `ERB - 6 Cyl 3.6L VVT`: 13
- `With Hitch`: 13
- `With Tow Hooks`: 13
- `EGL - 6 Cyl 3.8L OHV`: 12
- `Left [GTR`: 12
- `Primed`: 12
- `Right [GTR`: 12
- `All Models`: 11
- `With Park Sensors`: 11
- `Left [GTS`: 10
- `Right [GTS`: 10
- `T - TOURING`: 10
- `With Sales Codes [GTS] and [JSC] and [LEP]`: 10

## Unmapped catalog models

- Chrysler Prowler: feed 'Prowler' 0 cars (excluded: catalog model with no feed cars as 'Prowler' (inventory 2026-11-04); nothing to map)
- Dodge D250: feed 'D250' 10 cars (excluded: M3: the feed spells this truck 'D250', 'D-250' and 'D250 Pickup' (one squash key); not mapped until the feed normalizes them)
- Dodge Omni: feed 'Omni' 1 cars (excluded: catalog model with no feed cars as 'Omni' (inventory 2026-11-04); nothing to map)
- Dodge Ram 4500: feed 'Ram 4500' 0 cars (excluded: catalog model with no feed cars as 'Ram 4500' (inventory 2026-11-04); nothing to map)
- Dodge Ram 5500: feed 'Ram 5500' 0 cars (excluded: catalog model with no feed cars as 'Ram 5500' (inventory 2026-11-04); nothing to map)
- Dodge Viper: feed 'Viper' 0 cars (excluded: catalog model with no feed cars as 'Viper' (inventory 2026-11-04); nothing to map)
- Jeep J20: feed 'J20' 0 cars (excluded: catalog model with no feed cars as 'J20' (inventory 2026-11-04); nothing to map)
