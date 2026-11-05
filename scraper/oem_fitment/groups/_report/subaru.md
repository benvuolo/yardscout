# OEM curation report: subaru

Raw: `50ac4a48cdc62d02bd819bec33a67d0f07d8a71e` @ `50ac4a48cdc6`; as of 2026-11-05T10:25:33Z.

- records 993, classes 993, list rows 0, year manifests 0, cells 1160
- Verified groups 0, engine vg groups 0, Likely groups 553
- blocked sites: www.subarupartsdeal.com

## Gates standing for the whole namespace

- no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close (C1/C2); Verified is impossible by design until the crawler writes them
- no (site, category) of this namespace has passed the audit gate (CATEGORY_STATUS has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.subarupartsdeal.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.subarupartsdeal.com: only 0% of its 2100 fitment rows can be coverage: its option column holds trims (option_column_is_trims), which count only after a namespace audit (spec 5.2)
- blocked by the crawl breaker: www.subarupartsdeal.com (their cells never close, C9)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 263 |
| ac-compressor | no_records | - | 749 |
| ac-compressor | not_closed | no_year_manifest | 4543 |
| alternator | unmapped | - | 263 |
| alternator | no_records | - | 828 |
| alternator | not_closed | no_year_manifest | 4464 |
| climate-control | unmapped | - | 263 |
| climate-control | no_records | - | 742 |
| climate-control | not_closed | no_year_manifest | 4550 |
| fuel-pump-module | unmapped | - | 263 |
| fuel-pump-module | no_records | - | 670 |
| fuel-pump-module | not_closed | no_year_manifest | 4622 |
| headlights | unmapped | - | 263 |
| headlights | no_records | - | 1339 |
| headlights | not_closed | no_year_manifest | 3953 |
| power-steering-pump | unmapped | - | 263 |
| power-steering-pump | no_records | - | 1256 |
| power-steering-pump | not_closed | no_year_manifest | 4036 |
| side-mirrors | unmapped | - | 263 |
| side-mirrors | no_records | - | 865 |
| side-mirrors | not_closed | no_year_manifest | 4427 |
| starter | unmapped | - | 263 |
| starter | no_records | - | 104 |
| starter | not_closed | no_year_manifest | 5188 |
| tail-lights | unmapped | - | 263 |
| tail-lights | no_records | - | 836 |
| tail-lights | not_closed | no_year_manifest | 4456 |
| throttle-body | unmapped | - | 263 |
| throttle-body | no_records | - | 165 |
| throttle-body | not_closed | no_year_manifest | 5127 |
| window-regulator | unmapped | - | 263 |
| window-regulator | no_records | - | 271 |
| window-regulator | not_closed | no_year_manifest | 5021 |
| window-switch | unmapped | - | 263 |
| window-switch | no_records | - | 1183 |
| window-switch | not_closed | no_year_manifest | 4109 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 263 |
| ac-compressor | no_records | - | 749 |
| ac-compressor | split | option_split | 2582 |
| ac-compressor | conditional | conditional:notes_not_own_page | 1409 |
| ac-compressor | conditional | conditional:option_layout | 552 |
| alternator | unmapped | - | 263 |
| alternator | no_records | - | 828 |
| alternator | split | option_split | 2524 |
| alternator | conditional | conditional:notes_not_own_page | 1418 |
| alternator | conditional | conditional:option_layout | 522 |
| climate-control | unmapped | - | 263 |
| climate-control | no_records | - | 742 |
| climate-control | split | option_split | 3244 |
| climate-control | conditional | conditional:notes_not_own_page | 1175 |
| climate-control | conditional | conditional:option_layout | 131 |
| fuel-pump-module | unmapped | - | 263 |
| fuel-pump-module | no_records | - | 670 |
| fuel-pump-module | split | option_split | 3403 |
| fuel-pump-module | conditional | conditional:notes_not_own_page | 1016 |
| fuel-pump-module | conditional | conditional:option_layout | 203 |
| headlights | unmapped | - | 263 |
| headlights | no_records | - | 1339 |
| headlights | split | option_split | 2958 |
| headlights | conditional | conditional:notes_not_own_page | 565 |
| headlights | conditional | conditional:option_layout | 430 |
| power-steering-pump | unmapped | - | 263 |
| power-steering-pump | no_records | - | 1256 |
| power-steering-pump | split | option_split | 3332 |
| power-steering-pump | conditional | conditional:notes_not_own_page | 593 |
| power-steering-pump | conditional | conditional:option | 48 |
| power-steering-pump | conditional | conditional:option_layout | 63 |
| side-mirrors | unmapped | - | 263 |
| side-mirrors | no_records | - | 865 |
| side-mirrors | split | option_split | 4178 |
| side-mirrors | conditional | conditional:notes_not_own_page | 249 |
| starter | unmapped | - | 263 |
| starter | no_records | - | 104 |
| starter | split | option_split | 5076 |
| starter | conditional | conditional:notes_not_own_page | 112 |
| tail-lights | unmapped | - | 263 |
| tail-lights | no_records | - | 836 |
| tail-lights | split | option_split | 3526 |
| tail-lights | conditional | conditional:notes_not_own_page | 626 |
| tail-lights | conditional | conditional:option_layout | 304 |
| throttle-body | unmapped | - | 263 |
| throttle-body | no_records | - | 165 |
| throttle-body | split | option_split | 4144 |
| throttle-body | conditional | conditional:notes_not_own_page | 826 |
| throttle-body | conditional | conditional:option_layout | 157 |
| window-regulator | unmapped | - | 263 |
| window-regulator | no_records | - | 271 |
| window-regulator | split | packaging_unstated | 5021 |
| window-switch | unmapped | - | 263 |
| window-switch | no_records | - | 1183 |
| window-switch | split | no_candidates | 187 |
| window-switch | split | option_split | 2050 |
| window-switch | split | position_missing | 1872 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason


## Unknown note clauses (top 30)

- `Production Date: 199105 - 199204`: 82
- `Production Date: 200201 - 200306`: 61
- `NO PAINTED`: 46
- `Production Date: 200311 - 200505`: 40
- `Production Date: 200610 - 200804`: 38
- `Production Date: 199912 - 200105`: 37
- `W/O SD TURN-LAMP`: 26
- `Production Date: 199710 - 199905`: 24
- `Production Date: 200606 - 200706`: 24
- `Production Date: 199909 - 200102`: 18
- `Notes: C0`: 16
- `S.25I +W.4AT`: 16
- `S.25I.4AT +W.25I.4AT +WOBK.25I.4AT`: 16
- `Notes: UT U4`: 14
- `S.25GLI +W.25GLI +WOBK.(25GT+25GLI)`: 14
- `*S.(GT+SUS) +SW.GT`: 12
- `*W.WRX`: 12
- `Notes: C0 UT U1`: 12
- `S.25ILTD +W.25I.5MT +WOBK.25ILTD`: 12
- `*S.WRX +W.WRX`: 10
- `Notes: C4`: 10
- `Notes: C4 UT U1`: 10
- `Notes: CO`: 10
- `Notes: LIMITED FOR C/P`: 10
- `Notes: U4`: 10
- `RMT-C`: 10
- `S.25ILTD +W.25ILTD +WOBK.25ILTD`: 10
- `S.STI`: 10
- `Notes: AUTO`: 9
- `S.36R`: 9

## Unmapped catalog models

- Subaru Impreza STI: feed 'Impreza STI' 0 cars
- Subaru WRX STI: feed 'WRX STI' 0 cars
