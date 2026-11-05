# OEM curation report: subaru

Raw: `ceccc800d7ba22c0291121baabb0a9292eb8f271` @ `ceccc800d7ba`; as of 2026-11-05T10:25:33Z.

- records 993, classes 993, list rows 0, year manifests 0, cells 1160
- Verified groups 0, engine vg groups 0, Likely groups 553
- blocked sites: none

## Gates standing for the whole namespace

- no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close (C1/C2); Verified is impossible by design until the crawler writes them
- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.subarupartsdeal.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.subarupartsdeal.com: only 0% of its 2100 fitment rows can be coverage: its option column holds trims (option_column_is_trims), which count only after a namespace audit (spec 5.2)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 263 |
| ac-compressor | no_records | - | 747 |
| ac-compressor | not_closed | no_year_manifest | 4535 |
| alternator | unmapped | - | 263 |
| alternator | no_records | - | 827 |
| alternator | not_closed | no_year_manifest | 4455 |
| climate-control | unmapped | - | 263 |
| climate-control | no_records | - | 740 |
| climate-control | not_closed | no_year_manifest | 4542 |
| fuel-pump-module | unmapped | - | 263 |
| fuel-pump-module | no_records | - | 668 |
| fuel-pump-module | not_closed | no_year_manifest | 4614 |
| headlights | unmapped | - | 263 |
| headlights | no_records | - | 1334 |
| headlights | not_closed | no_year_manifest | 3948 |
| power-steering-pump | unmapped | - | 263 |
| power-steering-pump | no_records | - | 1255 |
| power-steering-pump | not_closed | no_year_manifest | 4027 |
| side-mirrors | unmapped | - | 263 |
| side-mirrors | no_records | - | 861 |
| side-mirrors | not_closed | no_year_manifest | 4421 |
| starter | unmapped | - | 263 |
| starter | no_records | - | 104 |
| starter | not_closed | no_year_manifest | 5178 |
| tail-lights | unmapped | - | 263 |
| tail-lights | no_records | - | 833 |
| tail-lights | not_closed | no_year_manifest | 4449 |
| throttle-body | unmapped | - | 263 |
| throttle-body | no_records | - | 164 |
| throttle-body | not_closed | no_year_manifest | 5118 |
| window-regulator | unmapped | - | 263 |
| window-regulator | no_records | - | 269 |
| window-regulator | not_closed | no_year_manifest | 5013 |
| window-switch | unmapped | - | 263 |
| window-switch | no_records | - | 1182 |
| window-switch | not_closed | no_year_manifest | 4100 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 263 |
| ac-compressor | no_records | - | 747 |
| ac-compressor | split | option_split | 2570 |
| ac-compressor | conditional | conditional:engine_unattested | 1965 |
| alternator | unmapped | - | 263 |
| alternator | no_records | - | 827 |
| alternator | split | option_split | 2522 |
| alternator | conditional | conditional:engine_unattested | 1933 |
| climate-control | unmapped | - | 263 |
| climate-control | no_records | - | 740 |
| climate-control | split | option_split | 3235 |
| climate-control | conditional | conditional:engine_unattested | 1307 |
| fuel-pump-module | unmapped | - | 263 |
| fuel-pump-module | no_records | - | 668 |
| fuel-pump-module | split | option_split | 3392 |
| fuel-pump-module | conditional | conditional:engine_unattested | 1222 |
| headlights | unmapped | - | 263 |
| headlights | no_records | - | 1334 |
| headlights | split | option_split | 2958 |
| headlights | conditional | conditional:engine_unattested | 990 |
| power-steering-pump | unmapped | - | 263 |
| power-steering-pump | no_records | - | 1255 |
| power-steering-pump | split | option_split | 3322 |
| power-steering-pump | conditional | conditional:engine_unattested | 657 |
| power-steering-pump | conditional | conditional:option | 48 |
| side-mirrors | unmapped | - | 263 |
| side-mirrors | no_records | - | 861 |
| side-mirrors | split | option_split | 4172 |
| side-mirrors | conditional | conditional:engine_unattested | 249 |
| starter | unmapped | - | 263 |
| starter | no_records | - | 104 |
| starter | split | option_split | 5068 |
| starter | conditional | conditional:engine_unattested | 110 |
| tail-lights | unmapped | - | 263 |
| tail-lights | no_records | - | 833 |
| tail-lights | split | option_split | 3515 |
| tail-lights | conditional | conditional:engine_unattested | 934 |
| throttle-body | unmapped | - | 263 |
| throttle-body | no_records | - | 164 |
| throttle-body | split | option_split | 4136 |
| throttle-body | conditional | conditional:engine_unattested | 982 |
| window-regulator | unmapped | - | 263 |
| window-regulator | no_records | - | 269 |
| window-regulator | split | packaging_unstated | 5013 |
| window-switch | unmapped | - | 263 |
| window-switch | no_records | - | 1182 |
| window-switch | split | no_candidates | 186 |
| window-switch | split | option_split | 2040 |
| window-switch | split | position_missing | 1874 |

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
