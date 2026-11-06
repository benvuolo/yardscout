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
| ac-compressor | unmapped | - | 154 |
| ac-compressor | no_records | - | 380 |
| ac-compressor | not_closed | no_year_manifest | 1932 |
| alternator | unmapped | - | 154 |
| alternator | no_records | - | 169 |
| alternator | not_closed | no_year_manifest | 2143 |
| bumper-front | unmapped | - | 154 |
| bumper-front | no_records | - | 850 |
| bumper-front | not_closed | no_year_manifest | 1462 |
| bumper-rear | unmapped | - | 154 |
| bumper-rear | no_records | - | 784 |
| bumper-rear | not_closed | no_year_manifest | 1528 |
| climate-control | unmapped | - | 154 |
| climate-control | no_records | - | 585 |
| climate-control | not_closed | no_year_manifest | 1727 |
| door-front | unmapped | - | 154 |
| door-front | no_records | - | 538 |
| door-front | not_closed | no_year_manifest | 1774 |
| door-rear | unmapped | - | 154 |
| door-rear | no_records | - | 650 |
| door-rear | not_closed | no_year_manifest | 1662 |
| fender | unmapped | - | 154 |
| fender | no_records | - | 272 |
| fender | not_closed | no_year_manifest | 2040 |
| fuel-pump-module | unmapped | - | 154 |
| fuel-pump-module | no_records | - | 86 |
| fuel-pump-module | not_closed | no_year_manifest | 2226 |
| gauge-cluster | unmapped | - | 154 |
| gauge-cluster | no_records | - | 1130 |
| gauge-cluster | not_closed | no_year_manifest | 1182 |
| grille | unmapped | - | 154 |
| grille | no_records | - | 1377 |
| grille | not_closed | no_year_manifest | 935 |
| headlights | unmapped | - | 154 |
| headlights | no_records | - | 457 |
| headlights | not_closed | no_year_manifest | 1855 |
| hood | unmapped | - | 154 |
| hood | no_records | - | 351 |
| hood | not_closed | no_year_manifest | 1961 |
| ignition-coils | unmapped | - | 154 |
| ignition-coils | no_records | - | 388 |
| ignition-coils | not_closed | no_year_manifest | 1924 |
| liftgate | unmapped | - | 154 |
| liftgate | no_records | - | 1296 |
| liftgate | not_closed | no_year_manifest | 1016 |
| power-steering-pump | unmapped | - | 154 |
| power-steering-pump | no_records | - | 331 |
| power-steering-pump | not_closed | no_year_manifest | 1981 |
| radiator | unmapped | - | 154 |
| radiator | no_records | - | 222 |
| radiator | not_closed | no_year_manifest | 2090 |
| side-mirrors | unmapped | - | 154 |
| side-mirrors | no_records | - | 962 |
| side-mirrors | not_closed | no_year_manifest | 1350 |
| starter | unmapped | - | 154 |
| starter | no_records | - | 205 |
| starter | not_closed | no_year_manifest | 2107 |
| tail-lights | unmapped | - | 154 |
| tail-lights | no_records | - | 858 |
| tail-lights | not_closed | no_year_manifest | 1454 |
| throttle-body | unmapped | - | 154 |
| throttle-body | no_records | - | 280 |
| throttle-body | not_closed | no_year_manifest | 2032 |
| trunk-lid | unmapped | - | 154 |
| trunk-lid | no_records | - | 1304 |
| trunk-lid | not_closed | no_year_manifest | 1008 |
| window-regulator | unmapped | - | 154 |
| window-regulator | no_records | - | 92 |
| window-regulator | not_closed | no_year_manifest | 2220 |
| window-switch | unmapped | - | 154 |
| window-switch | no_records | - | 458 |
| window-switch | not_closed | no_year_manifest | 1854 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 154 |
| ac-compressor | no_records | - | 380 |
| ac-compressor | split | option_split | 607 |
| ac-compressor | conditional | conditional:colour | 1 |
| ac-compressor | conditional | conditional:qualifier | 1321 |
| ac-compressor | conditional | conditional:trim | 3 |
| alternator | unmapped | - | 154 |
| alternator | no_records | - | 169 |
| alternator | split | option_split | 1201 |
| alternator | conditional | conditional:colour | 5 |
| alternator | conditional | conditional:engine | 98 |
| alternator | conditional | conditional:qualifier | 839 |
| bumper-front | unmapped | - | 154 |
| bumper-front | no_records | - | 850 |
| bumper-front | split | option_split | 1409 |
| bumper-front | conditional | conditional:colour | 18 |
| bumper-front | conditional | conditional:engine_unattested | 32 |
| bumper-front | conditional | conditional:trim | 3 |
| bumper-rear | unmapped | - | 154 |
| bumper-rear | no_records | - | 784 |
| bumper-rear | split | option_split | 1370 |
| bumper-rear | conditional | conditional:body | 27 |
| bumper-rear | conditional | conditional:engine_unattested | 52 |
| bumper-rear | conditional | conditional:trim | 79 |
| climate-control | unmapped | - | 154 |
| climate-control | no_records | - | 585 |
| climate-control | split | option_split | 1188 |
| climate-control | conditional | conditional:engine_unattested | 182 |
| climate-control | conditional | conditional:option | 51 |
| climate-control | conditional | conditional:trim | 306 |
| door-front | unmapped | - | 154 |
| door-front | no_records | - | 538 |
| door-front | conditional | conditional:engine_unattested | 1107 |
| door-front | conditional | conditional:trim | 667 |
| door-rear | unmapped | - | 154 |
| door-rear | no_records | - | 650 |
| door-rear | split | slot_missing | 9 |
| door-rear | conditional | conditional:engine_unattested | 1016 |
| door-rear | conditional | conditional:trim | 637 |
| fender | unmapped | - | 154 |
| fender | no_records | - | 272 |
| fender | split | option_split | 125 |
| fender | split | slot_missing | 13 |
| fender | conditional | conditional:engine_unattested | 1393 |
| fender | conditional | conditional:trim | 509 |
| fuel-pump-module | unmapped | - | 154 |
| fuel-pump-module | no_records | - | 86 |
| fuel-pump-module | split | option_split | 1358 |
| fuel-pump-module | conditional | conditional:engine_unattested | 254 |
| fuel-pump-module | conditional | conditional:trim | 614 |
| gauge-cluster | unmapped | - | 154 |
| gauge-cluster | no_records | - | 1130 |
| gauge-cluster | split | option_split | 666 |
| gauge-cluster | conditional | conditional:engine_unattested | 28 |
| gauge-cluster | conditional | conditional:trim | 488 |
| grille | unmapped | - | 154 |
| grille | no_records | - | 1377 |
| grille | split | option_split | 605 |
| grille | conditional | conditional:colour | 9 |
| grille | conditional | conditional:engine_unattested | 42 |
| grille | conditional | conditional:trim | 279 |
| headlights | unmapped | - | 154 |
| headlights | no_records | - | 457 |
| headlights | split | option_split | 1177 |
| headlights | split | slot_missing | 108 |
| headlights | conditional | conditional:engine_unattested | 286 |
| headlights | conditional | conditional:option | 64 |
| headlights | conditional | conditional:trim | 220 |
| hood | unmapped | - | 154 |
| hood | no_records | - | 351 |
| hood | split | option_split | 22 |
| hood | conditional | conditional:engine_unattested | 1245 |
| hood | conditional | conditional:trim | 694 |
| ignition-coils | unmapped | - | 154 |
| ignition-coils | no_records | - | 388 |
| ignition-coils | split | option_split | 1000 |
| ignition-coils | conditional | conditional:engine_unattested | 464 |
| ignition-coils | conditional | conditional:trim | 460 |
| liftgate | unmapped | - | 154 |
| liftgate | no_records | - | 1296 |
| liftgate | split | option_split | 24 |
| liftgate | conditional | conditional:engine_unattested | 621 |
| liftgate | conditional | conditional:trim | 371 |
| power-steering-pump | unmapped | - | 154 |
| power-steering-pump | no_records | - | 331 |
| power-steering-pump | split | option_split | 443 |
| power-steering-pump | conditional | conditional:engine_unattested | 568 |
| power-steering-pump | conditional | conditional:trim | 970 |
| radiator | unmapped | - | 154 |
| radiator | no_records | - | 222 |
| radiator | split | option_split | 472 |
| radiator | conditional | conditional:colour | 14 |
| radiator | conditional | conditional:engine | 174 |
| radiator | conditional | conditional:engine_unattested | 432 |
| radiator | conditional | conditional:model_other | 48 |
| radiator | conditional | conditional:trans | 22 |
| radiator | conditional | conditional:trim | 928 |
| side-mirrors | unmapped | - | 154 |
| side-mirrors | no_records | - | 962 |
| side-mirrors | split | option_split | 1250 |
| side-mirrors | split | slot_missing | 69 |
| side-mirrors | conditional | conditional:engine_unattested | 31 |
| starter | unmapped | - | 154 |
| starter | no_records | - | 205 |
| starter | split | option_split | 824 |
| starter | conditional | conditional:engine_unattested | 544 |
| starter | conditional | conditional:trim | 739 |
| tail-lights | unmapped | - | 154 |
| tail-lights | no_records | - | 858 |
| tail-lights | split | option_split | 423 |
| tail-lights | split | slot_missing | 141 |
| tail-lights | conditional | conditional:engine_unattested | 224 |
| tail-lights | conditional | conditional:trim | 666 |
| throttle-body | unmapped | - | 154 |
| throttle-body | no_records | - | 280 |
| throttle-body | split | option_split | 1445 |
| throttle-body | conditional | conditional:engine | 2 |
| throttle-body | conditional | conditional:engine_unattested | 266 |
| throttle-body | conditional | conditional:trim | 319 |
| trunk-lid | unmapped | - | 154 |
| trunk-lid | no_records | - | 1304 |
| trunk-lid | conditional | conditional:engine_unattested | 589 |
| trunk-lid | conditional | conditional:trim | 419 |
| window-regulator | unmapped | - | 154 |
| window-regulator | no_records | - | 92 |
| window-regulator | split | packaging_incomplete | 48 |
| window-regulator | split | packaging_unstated | 2172 |
| window-switch | unmapped | - | 154 |
| window-switch | no_records | - | 458 |
| window-switch | split | option_split | 774 |
| window-switch | split | position_missing | 850 |
| window-switch | conditional | conditional:model_other | 81 |
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

- Volvo 240: feed '240' 52 cars
- Volvo 242: feed '242' 0 cars
