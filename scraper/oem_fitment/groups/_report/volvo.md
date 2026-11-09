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
| ac-compressor | unmapped | - | 146 |
| ac-compressor | no_records | - | 380 |
| ac-compressor | not_closed | no_year_manifest | 1941 |
| alternator | unmapped | - | 146 |
| alternator | no_records | - | 165 |
| alternator | not_closed | no_year_manifest | 2156 |
| bumper-front | unmapped | - | 146 |
| bumper-front | no_records | - | 856 |
| bumper-front | not_closed | no_year_manifest | 1465 |
| bumper-rear | unmapped | - | 146 |
| bumper-rear | no_records | - | 789 |
| bumper-rear | not_closed | no_year_manifest | 1532 |
| climate-control | unmapped | - | 146 |
| climate-control | no_records | - | 589 |
| climate-control | not_closed | no_year_manifest | 1732 |
| door-front | unmapped | - | 146 |
| door-front | no_records | - | 534 |
| door-front | not_closed | no_year_manifest | 1787 |
| door-rear | unmapped | - | 146 |
| door-rear | no_records | - | 650 |
| door-rear | not_closed | no_year_manifest | 1671 |
| fender | unmapped | - | 146 |
| fender | no_records | - | 270 |
| fender | not_closed | no_year_manifest | 2051 |
| fuel-pump-module | unmapped | - | 146 |
| fuel-pump-module | no_records | - | 84 |
| fuel-pump-module | not_closed | no_year_manifest | 2237 |
| gauge-cluster | unmapped | - | 146 |
| gauge-cluster | no_records | - | 1136 |
| gauge-cluster | not_closed | no_year_manifest | 1185 |
| grille | unmapped | - | 146 |
| grille | no_records | - | 1384 |
| grille | not_closed | no_year_manifest | 937 |
| headlights | unmapped | - | 146 |
| headlights | no_records | - | 448 |
| headlights | not_closed | no_year_manifest | 1873 |
| hood | unmapped | - | 146 |
| hood | no_records | - | 352 |
| hood | not_closed | no_year_manifest | 1969 |
| ignition-coils | unmapped | - | 146 |
| ignition-coils | no_records | - | 391 |
| ignition-coils | not_closed | no_year_manifest | 1930 |
| liftgate | unmapped | - | 146 |
| liftgate | no_records | - | 1304 |
| liftgate | not_closed | no_year_manifest | 1017 |
| power-steering-pump | unmapped | - | 146 |
| power-steering-pump | no_records | - | 332 |
| power-steering-pump | not_closed | no_year_manifest | 1989 |
| radiator | unmapped | - | 146 |
| radiator | no_records | - | 219 |
| radiator | not_closed | no_year_manifest | 2102 |
| side-mirrors | unmapped | - | 146 |
| side-mirrors | no_records | - | 965 |
| side-mirrors | not_closed | no_year_manifest | 1356 |
| starter | unmapped | - | 146 |
| starter | no_records | - | 199 |
| starter | not_closed | no_year_manifest | 2122 |
| tail-lights | unmapped | - | 146 |
| tail-lights | no_records | - | 858 |
| tail-lights | not_closed | no_year_manifest | 1463 |
| throttle-body | unmapped | - | 146 |
| throttle-body | no_records | - | 282 |
| throttle-body | not_closed | no_year_manifest | 2039 |
| trunk-lid | unmapped | - | 146 |
| trunk-lid | no_records | - | 1310 |
| trunk-lid | not_closed | no_year_manifest | 1011 |
| window-regulator | unmapped | - | 146 |
| window-regulator | no_records | - | 91 |
| window-regulator | not_closed | no_year_manifest | 2230 |
| window-switch | unmapped | - | 146 |
| window-switch | no_records | - | 450 |
| window-switch | not_closed | no_year_manifest | 1871 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 146 |
| ac-compressor | no_records | - | 380 |
| ac-compressor | split | option_split | 616 |
| ac-compressor | conditional | conditional:colour | 1 |
| ac-compressor | conditional | conditional:qualifier | 1321 |
| ac-compressor | conditional | conditional:trim | 3 |
| alternator | unmapped | - | 146 |
| alternator | no_records | - | 165 |
| alternator | split | option_split | 1215 |
| alternator | conditional | conditional:colour | 5 |
| alternator | conditional | conditional:engine | 94 |
| alternator | conditional | conditional:qualifier | 842 |
| bumper-front | unmapped | - | 146 |
| bumper-front | no_records | - | 856 |
| bumper-front | split | option_split | 1414 |
| bumper-front | conditional | conditional:colour | 17 |
| bumper-front | conditional | conditional:engine_unattested | 31 |
| bumper-front | conditional | conditional:trim | 3 |
| bumper-rear | unmapped | - | 146 |
| bumper-rear | no_records | - | 789 |
| bumper-rear | split | option_split | 1370 |
| bumper-rear | conditional | conditional:body | 29 |
| bumper-rear | conditional | conditional:engine_unattested | 53 |
| bumper-rear | conditional | conditional:trim | 80 |
| climate-control | unmapped | - | 146 |
| climate-control | no_records | - | 589 |
| climate-control | split | option_split | 1185 |
| climate-control | conditional | conditional:engine_unattested | 185 |
| climate-control | conditional | conditional:option | 51 |
| climate-control | conditional | conditional:trim | 311 |
| door-front | unmapped | - | 146 |
| door-front | no_records | - | 534 |
| door-front | conditional | conditional:engine_unattested | 1110 |
| door-front | conditional | conditional:trim | 677 |
| door-rear | unmapped | - | 146 |
| door-rear | no_records | - | 650 |
| door-rear | split | slot_missing | 8 |
| door-rear | conditional | conditional:engine_unattested | 1017 |
| door-rear | conditional | conditional:trim | 646 |
| fender | unmapped | - | 146 |
| fender | no_records | - | 270 |
| fender | split | option_split | 122 |
| fender | split | slot_missing | 13 |
| fender | conditional | conditional:engine_unattested | 1395 |
| fender | conditional | conditional:trim | 521 |
| fuel-pump-module | unmapped | - | 146 |
| fuel-pump-module | no_records | - | 84 |
| fuel-pump-module | split | option_split | 1365 |
| fuel-pump-module | conditional | conditional:engine_unattested | 251 |
| fuel-pump-module | conditional | conditional:trim | 621 |
| gauge-cluster | unmapped | - | 146 |
| gauge-cluster | no_records | - | 1136 |
| gauge-cluster | split | option_split | 670 |
| gauge-cluster | conditional | conditional:engine_unattested | 28 |
| gauge-cluster | conditional | conditional:trim | 487 |
| grille | unmapped | - | 146 |
| grille | no_records | - | 1384 |
| grille | split | option_split | 605 |
| grille | conditional | conditional:colour | 10 |
| grille | conditional | conditional:engine_unattested | 43 |
| grille | conditional | conditional:trim | 279 |
| headlights | unmapped | - | 146 |
| headlights | no_records | - | 448 |
| headlights | split | option_split | 1179 |
| headlights | split | slot_missing | 108 |
| headlights | conditional | conditional:engine_unattested | 293 |
| headlights | conditional | conditional:option | 64 |
| headlights | conditional | conditional:trim | 229 |
| hood | unmapped | - | 146 |
| hood | no_records | - | 352 |
| hood | split | option_split | 20 |
| hood | conditional | conditional:engine_unattested | 1246 |
| hood | conditional | conditional:trim | 703 |
| ignition-coils | unmapped | - | 146 |
| ignition-coils | no_records | - | 391 |
| ignition-coils | split | option_split | 1004 |
| ignition-coils | conditional | conditional:engine_unattested | 459 |
| ignition-coils | conditional | conditional:trim | 467 |
| liftgate | unmapped | - | 146 |
| liftgate | no_records | - | 1304 |
| liftgate | split | option_split | 23 |
| liftgate | conditional | conditional:engine_unattested | 618 |
| liftgate | conditional | conditional:trim | 376 |
| power-steering-pump | unmapped | - | 146 |
| power-steering-pump | no_records | - | 332 |
| power-steering-pump | split | option_split | 441 |
| power-steering-pump | conditional | conditional:engine_unattested | 568 |
| power-steering-pump | conditional | conditional:trim | 980 |
| radiator | unmapped | - | 146 |
| radiator | no_records | - | 219 |
| radiator | split | option_split | 471 |
| radiator | conditional | conditional:colour | 15 |
| radiator | conditional | conditional:engine | 176 |
| radiator | conditional | conditional:engine_unattested | 435 |
| radiator | conditional | conditional:model_other | 46 |
| radiator | conditional | conditional:trans | 21 |
| radiator | conditional | conditional:trim | 938 |
| side-mirrors | unmapped | - | 146 |
| side-mirrors | no_records | - | 965 |
| side-mirrors | split | option_split | 1257 |
| side-mirrors | split | slot_missing | 68 |
| side-mirrors | conditional | conditional:engine_unattested | 31 |
| starter | unmapped | - | 146 |
| starter | no_records | - | 199 |
| starter | split | option_split | 833 |
| starter | conditional | conditional:engine_unattested | 546 |
| starter | conditional | conditional:trim | 743 |
| tail-lights | unmapped | - | 146 |
| tail-lights | no_records | - | 858 |
| tail-lights | split | option_split | 427 |
| tail-lights | split | slot_missing | 141 |
| tail-lights | conditional | conditional:engine_unattested | 224 |
| tail-lights | conditional | conditional:trim | 671 |
| throttle-body | unmapped | - | 146 |
| throttle-body | no_records | - | 282 |
| throttle-body | split | option_split | 1448 |
| throttle-body | conditional | conditional:engine | 2 |
| throttle-body | conditional | conditional:engine_unattested | 270 |
| throttle-body | conditional | conditional:trim | 319 |
| trunk-lid | unmapped | - | 146 |
| trunk-lid | no_records | - | 1310 |
| trunk-lid | conditional | conditional:engine_unattested | 588 |
| trunk-lid | conditional | conditional:trim | 423 |
| window-regulator | unmapped | - | 146 |
| window-regulator | no_records | - | 91 |
| window-regulator | split | packaging_incomplete | 47 |
| window-regulator | split | packaging_unstated | 2183 |
| window-switch | unmapped | - | 146 |
| window-switch | no_records | - | 450 |
| window-switch | split | option_split | 782 |
| window-switch | split | position_missing | 863 |
| window-switch | conditional | conditional:body | 1 |
| window-switch | conditional | conditional:model_other | 80 |
| window-switch | conditional | conditional:trim | 145 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_pn: 2

## Unknown note clauses (top 30)

- `Without Park Assist`: 61
- `With Park Assist`: 59
- `With Headlamp Washer`: 32
- `2001-04 Without S60R`: 31
- `Without Headlamp Washer`: 31
- `Primed`: 29
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

- Volvo 240: feed '240' 51 cars
- Volvo 242: feed '242' 0 cars
