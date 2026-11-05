# OEM curation report: volvo

Raw: `ceccc800d7ba22c0291121baabb0a9292eb8f271` @ `ceccc800d7ba`; as of 2026-11-05T12:14:35Z.

- records 964, classes 964, list rows 0, year manifests 0, cells 2606
- Verified groups 0, engine vg groups 0, Likely groups 271
- blocked sites: none

## Gates standing for the whole namespace

- no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close (C1/C2); Verified is impossible by design until the crawler writes them
- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.volvopartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 155 |
| ac-compressor | no_records | - | 377 |
| ac-compressor | not_closed | no_year_manifest | 1929 |
| alternator | unmapped | - | 155 |
| alternator | no_records | - | 169 |
| alternator | not_closed | no_year_manifest | 2137 |
| bumper-front | unmapped | - | 155 |
| bumper-front | no_records | - | 847 |
| bumper-front | not_closed | no_year_manifest | 1459 |
| bumper-rear | unmapped | - | 155 |
| bumper-rear | no_records | - | 776 |
| bumper-rear | not_closed | no_year_manifest | 1530 |
| climate-control | unmapped | - | 155 |
| climate-control | no_records | - | 583 |
| climate-control | not_closed | no_year_manifest | 1723 |
| door-front | unmapped | - | 155 |
| door-front | no_records | - | 532 |
| door-front | not_closed | no_year_manifest | 1774 |
| door-rear | unmapped | - | 155 |
| door-rear | no_records | - | 643 |
| door-rear | not_closed | no_year_manifest | 1663 |
| fender | unmapped | - | 155 |
| fender | no_records | - | 273 |
| fender | not_closed | no_year_manifest | 2033 |
| fuel-pump-module | unmapped | - | 155 |
| fuel-pump-module | no_records | - | 87 |
| fuel-pump-module | not_closed | no_year_manifest | 2219 |
| gauge-cluster | unmapped | - | 155 |
| gauge-cluster | no_records | - | 1125 |
| gauge-cluster | not_closed | no_year_manifest | 1181 |
| grille | unmapped | - | 155 |
| grille | no_records | - | 1368 |
| grille | not_closed | no_year_manifest | 938 |
| headlights | unmapped | - | 155 |
| headlights | no_records | - | 456 |
| headlights | not_closed | no_year_manifest | 1850 |
| hood | unmapped | - | 155 |
| hood | no_records | - | 347 |
| hood | not_closed | no_year_manifest | 1959 |
| ignition-coils | unmapped | - | 155 |
| ignition-coils | no_records | - | 378 |
| ignition-coils | not_closed | no_year_manifest | 1928 |
| liftgate | unmapped | - | 155 |
| liftgate | no_records | - | 1298 |
| liftgate | not_closed | no_year_manifest | 1008 |
| power-steering-pump | unmapped | - | 155 |
| power-steering-pump | no_records | - | 326 |
| power-steering-pump | not_closed | no_year_manifest | 1980 |
| radiator | unmapped | - | 155 |
| radiator | no_records | - | 217 |
| radiator | not_closed | no_year_manifest | 2089 |
| side-mirrors | unmapped | - | 155 |
| side-mirrors | no_records | - | 953 |
| side-mirrors | not_closed | no_year_manifest | 1353 |
| starter | unmapped | - | 155 |
| starter | no_records | - | 203 |
| starter | not_closed | no_year_manifest | 2103 |
| tail-lights | unmapped | - | 155 |
| tail-lights | no_records | - | 852 |
| tail-lights | not_closed | no_year_manifest | 1454 |
| throttle-body | unmapped | - | 155 |
| throttle-body | no_records | - | 281 |
| throttle-body | not_closed | no_year_manifest | 2025 |
| trunk-lid | unmapped | - | 155 |
| trunk-lid | no_records | - | 1301 |
| trunk-lid | not_closed | no_year_manifest | 1005 |
| window-regulator | unmapped | - | 155 |
| window-regulator | no_records | - | 93 |
| window-regulator | not_closed | no_year_manifest | 2213 |
| window-switch | unmapped | - | 155 |
| window-switch | no_records | - | 458 |
| window-switch | not_closed | no_year_manifest | 1848 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 155 |
| ac-compressor | no_records | - | 377 |
| ac-compressor | split | option_split | 605 |
| ac-compressor | conditional | conditional:colour | 1 |
| ac-compressor | conditional | conditional:qualifier | 1320 |
| ac-compressor | conditional | conditional:trim | 3 |
| alternator | unmapped | - | 155 |
| alternator | no_records | - | 169 |
| alternator | split | option_split | 1200 |
| alternator | conditional | conditional:colour | 5 |
| alternator | conditional | conditional:engine | 97 |
| alternator | conditional | conditional:qualifier | 835 |
| bumper-front | unmapped | - | 155 |
| bumper-front | no_records | - | 847 |
| bumper-front | split | option_split | 1407 |
| bumper-front | conditional | conditional:colour | 18 |
| bumper-front | conditional | conditional:engine_unattested | 31 |
| bumper-front | conditional | conditional:trim | 3 |
| bumper-rear | unmapped | - | 155 |
| bumper-rear | no_records | - | 776 |
| bumper-rear | split | option_split | 1378 |
| bumper-rear | conditional | conditional:body | 26 |
| bumper-rear | conditional | conditional:engine_unattested | 51 |
| bumper-rear | conditional | conditional:trim | 75 |
| climate-control | unmapped | - | 155 |
| climate-control | no_records | - | 583 |
| climate-control | split | option_split | 1189 |
| climate-control | conditional | conditional:engine_unattested | 181 |
| climate-control | conditional | conditional:option | 52 |
| climate-control | conditional | conditional:trim | 301 |
| door-front | unmapped | - | 155 |
| door-front | no_records | - | 532 |
| door-front | conditional | conditional:engine_unattested | 1105 |
| door-front | conditional | conditional:trim | 669 |
| door-rear | unmapped | - | 155 |
| door-rear | no_records | - | 643 |
| door-rear | split | slot_missing | 9 |
| door-rear | conditional | conditional:engine_unattested | 1015 |
| door-rear | conditional | conditional:trim | 639 |
| fender | unmapped | - | 155 |
| fender | no_records | - | 273 |
| fender | split | option_split | 123 |
| fender | split | slot_missing | 13 |
| fender | conditional | conditional:engine_unattested | 1388 |
| fender | conditional | conditional:trim | 509 |
| fuel-pump-module | unmapped | - | 155 |
| fuel-pump-module | no_records | - | 87 |
| fuel-pump-module | split | option_split | 1362 |
| fuel-pump-module | conditional | conditional:engine_unattested | 252 |
| fuel-pump-module | conditional | conditional:trim | 605 |
| gauge-cluster | unmapped | - | 155 |
| gauge-cluster | no_records | - | 1125 |
| gauge-cluster | split | option_split | 669 |
| gauge-cluster | conditional | conditional:engine_unattested | 29 |
| gauge-cluster | conditional | conditional:trim | 483 |
| grille | unmapped | - | 155 |
| grille | no_records | - | 1368 |
| grille | split | option_split | 606 |
| grille | conditional | conditional:colour | 9 |
| grille | conditional | conditional:engine_unattested | 42 |
| grille | conditional | conditional:trim | 281 |
| headlights | unmapped | - | 155 |
| headlights | no_records | - | 456 |
| headlights | split | option_split | 1175 |
| headlights | split | slot_missing | 107 |
| headlights | conditional | conditional:engine_unattested | 284 |
| headlights | conditional | conditional:option | 63 |
| headlights | conditional | conditional:trim | 221 |
| hood | unmapped | - | 155 |
| hood | no_records | - | 347 |
| hood | split | option_split | 22 |
| hood | conditional | conditional:engine_unattested | 1242 |
| hood | conditional | conditional:trim | 695 |
| ignition-coils | unmapped | - | 155 |
| ignition-coils | no_records | - | 378 |
| ignition-coils | split | option_split | 999 |
| ignition-coils | conditional | conditional:engine_unattested | 466 |
| ignition-coils | conditional | conditional:trim | 463 |
| liftgate | unmapped | - | 155 |
| liftgate | no_records | - | 1298 |
| liftgate | split | option_split | 25 |
| liftgate | conditional | conditional:engine_unattested | 617 |
| liftgate | conditional | conditional:trim | 366 |
| power-steering-pump | unmapped | - | 155 |
| power-steering-pump | no_records | - | 326 |
| power-steering-pump | split | option_split | 445 |
| power-steering-pump | conditional | conditional:engine_unattested | 569 |
| power-steering-pump | conditional | conditional:trim | 966 |
| radiator | unmapped | - | 155 |
| radiator | no_records | - | 217 |
| radiator | split | option_split | 471 |
| radiator | conditional | conditional:colour | 14 |
| radiator | conditional | conditional:engine | 173 |
| radiator | conditional | conditional:engine_unattested | 431 |
| radiator | conditional | conditional:model_other | 49 |
| radiator | conditional | conditional:trans | 22 |
| radiator | conditional | conditional:trim | 929 |
| side-mirrors | unmapped | - | 155 |
| side-mirrors | no_records | - | 953 |
| side-mirrors | split | option_split | 1253 |
| side-mirrors | split | slot_missing | 70 |
| side-mirrors | conditional | conditional:engine_unattested | 30 |
| starter | unmapped | - | 155 |
| starter | no_records | - | 203 |
| starter | split | option_split | 821 |
| starter | conditional | conditional:engine_unattested | 538 |
| starter | conditional | conditional:trim | 744 |
| tail-lights | unmapped | - | 155 |
| tail-lights | no_records | - | 852 |
| tail-lights | split | option_split | 420 |
| tail-lights | split | slot_missing | 141 |
| tail-lights | conditional | conditional:engine_unattested | 226 |
| tail-lights | conditional | conditional:trim | 667 |
| throttle-body | unmapped | - | 155 |
| throttle-body | no_records | - | 281 |
| throttle-body | split | option_split | 1439 |
| throttle-body | conditional | conditional:engine | 2 |
| throttle-body | conditional | conditional:engine_unattested | 266 |
| throttle-body | conditional | conditional:trim | 318 |
| trunk-lid | unmapped | - | 155 |
| trunk-lid | no_records | - | 1301 |
| trunk-lid | conditional | conditional:engine_unattested | 583 |
| trunk-lid | conditional | conditional:trim | 422 |
| window-regulator | unmapped | - | 155 |
| window-regulator | no_records | - | 93 |
| window-regulator | split | packaging_incomplete | 47 |
| window-regulator | split | packaging_unstated | 2166 |
| window-switch | unmapped | - | 155 |
| window-switch | no_records | - | 458 |
| window-switch | split | option_split | 768 |
| window-switch | split | position_missing | 849 |
| window-switch | conditional | conditional:model_other | 82 |
| window-switch | conditional | conditional:trim | 149 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_pn: 2

## Unknown note clauses (top 30)

- `Without Park Assist`: 61
- `With Park Assist`: 59
- `With Headlamp Washer`: 32
- `2001-04 Without S60R`: 31
- `Primed`: 31
- `Without Headlamp Washer`: 31
- `With Illumination`: 28
- `From Ch# 184399`: 23
- `Ice White`: 23
- `From Ch# 190000`: 22
- `Electric Silver`: 21
- `Without V70R`: 21
- `With Lamp Washer With Fog Lamps`: 20
- `With Lamp Washer Without Fog Lamps`: 20
- `Without Lamp Washer With Fog Lamps`: 20
- `Without Lamp Washer Without Fog Lamps`: 20
- `Painted With Lamp Washer`: 18
- `Painted Without Lamp Washer`: 18
- `Without Headlamp Washers`: 17
- `Without Upper Molding`: 17
- `Mistral Green`: 16
- `With Headlamp Washers`: 16
- `Caspian Blue`: 14
- `With Reverse Sensor`: 14
- `Without Reverse Sensor`: 14
- `Without Turbo`: 14
- `Black Stone`: 13
- `Black Sapphire`: 12
- `With Turbo`: 12
- `With XC`: 12

## Unmapped catalog models

- Volvo 240: feed '240' 53 cars
- Volvo 242: feed '242' 0 cars
