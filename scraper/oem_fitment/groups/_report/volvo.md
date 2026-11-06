# OEM curation report: volvo

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-05T12:14:35Z.

- records 964, classes 964, list rows 0, year manifests 0, cells 2606
- Verified groups 0, engine vg groups 0, Likely groups 0
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
| ac-compressor | not_closed | no_year_manifest | 1921 |
| alternator | unmapped | - | 155 |
| alternator | no_records | - | 168 |
| alternator | not_closed | no_year_manifest | 2130 |
| bumper-front | unmapped | - | 155 |
| bumper-front | no_records | - | 843 |
| bumper-front | not_closed | no_year_manifest | 1455 |
| bumper-rear | unmapped | - | 155 |
| bumper-rear | no_records | - | 776 |
| bumper-rear | not_closed | no_year_manifest | 1522 |
| climate-control | unmapped | - | 155 |
| climate-control | no_records | - | 580 |
| climate-control | not_closed | no_year_manifest | 1718 |
| door-front | unmapped | - | 155 |
| door-front | no_records | - | 531 |
| door-front | not_closed | no_year_manifest | 1767 |
| door-rear | unmapped | - | 155 |
| door-rear | no_records | - | 643 |
| door-rear | not_closed | no_year_manifest | 1655 |
| fender | unmapped | - | 155 |
| fender | no_records | - | 270 |
| fender | not_closed | no_year_manifest | 2028 |
| fuel-pump-module | unmapped | - | 155 |
| fuel-pump-module | no_records | - | 86 |
| fuel-pump-module | not_closed | no_year_manifest | 2212 |
| gauge-cluster | unmapped | - | 155 |
| gauge-cluster | no_records | - | 1119 |
| gauge-cluster | not_closed | no_year_manifest | 1179 |
| grille | unmapped | - | 155 |
| grille | no_records | - | 1363 |
| grille | not_closed | no_year_manifest | 935 |
| headlights | unmapped | - | 155 |
| headlights | no_records | - | 450 |
| headlights | not_closed | no_year_manifest | 1848 |
| hood | unmapped | - | 155 |
| hood | no_records | - | 345 |
| hood | not_closed | no_year_manifest | 1953 |
| ignition-coils | unmapped | - | 155 |
| ignition-coils | no_records | - | 382 |
| ignition-coils | not_closed | no_year_manifest | 1916 |
| liftgate | unmapped | - | 155 |
| liftgate | no_records | - | 1288 |
| liftgate | not_closed | no_year_manifest | 1010 |
| power-steering-pump | unmapped | - | 155 |
| power-steering-pump | no_records | - | 327 |
| power-steering-pump | not_closed | no_year_manifest | 1971 |
| radiator | unmapped | - | 155 |
| radiator | no_records | - | 218 |
| radiator | not_closed | no_year_manifest | 2080 |
| side-mirrors | unmapped | - | 155 |
| side-mirrors | no_records | - | 950 |
| side-mirrors | not_closed | no_year_manifest | 1348 |
| starter | unmapped | - | 155 |
| starter | no_records | - | 204 |
| starter | not_closed | no_year_manifest | 2094 |
| tail-lights | unmapped | - | 155 |
| tail-lights | no_records | - | 850 |
| tail-lights | not_closed | no_year_manifest | 1448 |
| throttle-body | unmapped | - | 155 |
| throttle-body | no_records | - | 279 |
| throttle-body | not_closed | no_year_manifest | 2019 |
| trunk-lid | unmapped | - | 155 |
| trunk-lid | no_records | - | 1297 |
| trunk-lid | not_closed | no_year_manifest | 1001 |
| window-regulator | unmapped | - | 155 |
| window-regulator | no_records | - | 92 |
| window-regulator | not_closed | no_year_manifest | 2206 |
| window-switch | unmapped | - | 155 |
| window-switch | no_records | - | 456 |
| window-switch | not_closed | no_year_manifest | 1842 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 155 |
| ac-compressor | no_records | - | 377 |
| ac-compressor | split | option_split | 604 |
| ac-compressor | conditional | conditional:colour | 1 |
| ac-compressor | conditional | conditional:qualifier | 1313 |
| ac-compressor | conditional | conditional:trim | 3 |
| alternator | unmapped | - | 155 |
| alternator | no_records | - | 168 |
| alternator | split | option_split | 1195 |
| alternator | conditional | conditional:colour | 5 |
| alternator | conditional | conditional:engine | 98 |
| alternator | conditional | conditional:qualifier | 832 |
| bumper-front | unmapped | - | 155 |
| bumper-front | no_records | - | 843 |
| bumper-front | split | option_split | 1402 |
| bumper-front | conditional | conditional:colour | 18 |
| bumper-front | conditional | conditional:engine_unattested | 32 |
| bumper-front | conditional | conditional:trim | 3 |
| bumper-rear | unmapped | - | 155 |
| bumper-rear | no_records | - | 776 |
| bumper-rear | split | option_split | 1369 |
| bumper-rear | conditional | conditional:body | 26 |
| bumper-rear | conditional | conditional:engine_unattested | 51 |
| bumper-rear | conditional | conditional:trim | 76 |
| climate-control | unmapped | - | 155 |
| climate-control | no_records | - | 580 |
| climate-control | split | option_split | 1184 |
| climate-control | conditional | conditional:engine_unattested | 179 |
| climate-control | conditional | conditional:option | 52 |
| climate-control | conditional | conditional:trim | 303 |
| door-front | unmapped | - | 155 |
| door-front | no_records | - | 531 |
| door-front | conditional | conditional:engine_unattested | 1102 |
| door-front | conditional | conditional:trim | 665 |
| door-rear | unmapped | - | 155 |
| door-rear | no_records | - | 643 |
| door-rear | split | slot_missing | 9 |
| door-rear | conditional | conditional:engine_unattested | 1010 |
| door-rear | conditional | conditional:trim | 636 |
| fender | unmapped | - | 155 |
| fender | no_records | - | 270 |
| fender | split | option_split | 125 |
| fender | split | slot_missing | 13 |
| fender | conditional | conditional:engine_unattested | 1385 |
| fender | conditional | conditional:trim | 505 |
| fuel-pump-module | unmapped | - | 155 |
| fuel-pump-module | no_records | - | 86 |
| fuel-pump-module | split | option_split | 1353 |
| fuel-pump-module | conditional | conditional:engine_unattested | 252 |
| fuel-pump-module | conditional | conditional:trim | 607 |
| gauge-cluster | unmapped | - | 155 |
| gauge-cluster | no_records | - | 1119 |
| gauge-cluster | split | option_split | 666 |
| gauge-cluster | conditional | conditional:engine_unattested | 29 |
| gauge-cluster | conditional | conditional:trim | 484 |
| grille | unmapped | - | 155 |
| grille | no_records | - | 1363 |
| grille | split | option_split | 605 |
| grille | conditional | conditional:colour | 9 |
| grille | conditional | conditional:engine_unattested | 43 |
| grille | conditional | conditional:trim | 278 |
| headlights | unmapped | - | 155 |
| headlights | no_records | - | 450 |
| headlights | split | option_split | 1173 |
| headlights | split | slot_missing | 107 |
| headlights | conditional | conditional:engine_unattested | 285 |
| headlights | conditional | conditional:option | 64 |
| headlights | conditional | conditional:trim | 219 |
| hood | unmapped | - | 155 |
| hood | no_records | - | 345 |
| hood | split | option_split | 22 |
| hood | conditional | conditional:engine_unattested | 1239 |
| hood | conditional | conditional:trim | 692 |
| ignition-coils | unmapped | - | 155 |
| ignition-coils | no_records | - | 382 |
| ignition-coils | split | option_split | 996 |
| ignition-coils | conditional | conditional:engine_unattested | 463 |
| ignition-coils | conditional | conditional:trim | 457 |
| liftgate | unmapped | - | 155 |
| liftgate | no_records | - | 1288 |
| liftgate | split | option_split | 24 |
| liftgate | conditional | conditional:engine_unattested | 619 |
| liftgate | conditional | conditional:trim | 367 |
| power-steering-pump | unmapped | - | 155 |
| power-steering-pump | no_records | - | 327 |
| power-steering-pump | split | option_split | 443 |
| power-steering-pump | conditional | conditional:engine_unattested | 564 |
| power-steering-pump | conditional | conditional:trim | 964 |
| radiator | unmapped | - | 155 |
| radiator | no_records | - | 218 |
| radiator | split | option_split | 472 |
| radiator | conditional | conditional:colour | 14 |
| radiator | conditional | conditional:engine | 174 |
| radiator | conditional | conditional:engine_unattested | 428 |
| radiator | conditional | conditional:model_other | 48 |
| radiator | conditional | conditional:trans | 21 |
| radiator | conditional | conditional:trim | 923 |
| side-mirrors | unmapped | - | 155 |
| side-mirrors | no_records | - | 950 |
| side-mirrors | split | option_split | 1249 |
| side-mirrors | split | slot_missing | 69 |
| side-mirrors | conditional | conditional:engine_unattested | 30 |
| starter | unmapped | - | 155 |
| starter | no_records | - | 204 |
| starter | split | option_split | 819 |
| starter | conditional | conditional:engine_unattested | 537 |
| starter | conditional | conditional:trim | 738 |
| tail-lights | unmapped | - | 155 |
| tail-lights | no_records | - | 850 |
| tail-lights | split | option_split | 420 |
| tail-lights | split | slot_missing | 140 |
| tail-lights | conditional | conditional:engine_unattested | 226 |
| tail-lights | conditional | conditional:trim | 662 |
| throttle-body | unmapped | - | 155 |
| throttle-body | no_records | - | 279 |
| throttle-body | split | option_split | 1436 |
| throttle-body | conditional | conditional:engine | 2 |
| throttle-body | conditional | conditional:engine_unattested | 266 |
| throttle-body | conditional | conditional:trim | 315 |
| trunk-lid | unmapped | - | 155 |
| trunk-lid | no_records | - | 1297 |
| trunk-lid | conditional | conditional:engine_unattested | 582 |
| trunk-lid | conditional | conditional:trim | 419 |
| window-regulator | unmapped | - | 155 |
| window-regulator | no_records | - | 92 |
| window-regulator | split | packaging_incomplete | 47 |
| window-regulator | split | packaging_unstated | 2159 |
| window-switch | unmapped | - | 155 |
| window-switch | no_records | - | 456 |
| window-switch | split | option_split | 763 |
| window-switch | split | position_missing | 847 |
| window-switch | conditional | conditional:model_other | 82 |
| window-switch | conditional | conditional:trim | 150 |

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
