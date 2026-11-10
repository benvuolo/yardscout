# OEM curation report: bmw

Raw: `dca9cd845f26` @ `dca9cd845f26`; as of 2026-11-05T10:07:33Z.

- records 1746, classes 1746, list rows 0, year manifests 0, cells 7561
- Verified groups 0, engine vg groups 0, Likely groups 0
- blocked sites: none

## Gates standing for the whole namespace

- no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close (C1/C2); Verified is impossible by design until the crawler writes them
- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.bmwpartsdeal.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.bmwpartsdeal.com: only 0% of its 11623 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 329 |
| ac-compressor | no_records | - | 1510 |
| ac-compressor | not_closed | no_year_manifest | 3607 |
| alternator | unmapped | - | 329 |
| alternator | no_records | - | 1516 |
| alternator | not_closed | no_year_manifest | 3601 |
| bumper-front | unmapped | - | 329 |
| bumper-front | no_records | - | 987 |
| bumper-front | not_closed | no_year_manifest | 4130 |
| bumper-rear | unmapped | - | 329 |
| bumper-rear | no_records | - | 1325 |
| bumper-rear | not_closed | no_year_manifest | 3792 |
| climate-control | unmapped | - | 329 |
| climate-control | no_records | - | 1715 |
| climate-control | not_closed | no_year_manifest | 3402 |
| door-front | unmapped | - | 329 |
| door-front | no_records | - | 233 |
| door-front | not_closed | no_year_manifest | 4884 |
| door-rear | unmapped | - | 329 |
| door-rear | no_records | - | 530 |
| door-rear | not_closed | no_year_manifest | 4587 |
| fender | unmapped | - | 329 |
| fender | no_records | - | 498 |
| fender | not_closed | no_year_manifest | 4619 |
| fuel-pump-module | unmapped | - | 329 |
| fuel-pump-module | no_records | - | 4815 |
| fuel-pump-module | not_closed | no_year_manifest | 302 |
| gauge-cluster | unmapped | - | 329 |
| gauge-cluster | no_records | - | 576 |
| gauge-cluster | not_closed | no_year_manifest | 4541 |
| grille | unmapped | - | 329 |
| grille | no_records | - | 3830 |
| grille | not_closed | no_year_manifest | 1287 |
| headlights | unmapped | - | 329 |
| headlights | no_records | - | 367 |
| headlights | not_closed | no_year_manifest | 4750 |
| hood | unmapped | - | 329 |
| hood | no_records | - | 571 |
| hood | not_closed | no_year_manifest | 4546 |
| ignition-coils | unmapped | - | 329 |
| ignition-coils | no_records | - | 103 |
| ignition-coils | not_closed | no_year_manifest | 5014 |
| power-steering-pump | unmapped | - | 329 |
| power-steering-pump | no_records | - | 1472 |
| power-steering-pump | not_closed | no_year_manifest | 3645 |
| radiator | unmapped | - | 329 |
| radiator | no_records | - | 570 |
| radiator | not_closed | no_year_manifest | 4547 |
| side-mirrors | unmapped | - | 329 |
| side-mirrors | no_records | - | 892 |
| side-mirrors | not_closed | no_year_manifest | 4225 |
| starter | unmapped | - | 329 |
| starter | no_records | - | 110 |
| starter | not_closed | no_year_manifest | 5007 |
| tail-lights | unmapped | - | 329 |
| tail-lights | no_records | - | 1050 |
| tail-lights | not_closed | no_year_manifest | 4067 |
| throttle-body | unmapped | - | 329 |
| throttle-body | no_records | - | 451 |
| throttle-body | not_closed | no_year_manifest | 4666 |
| trunk-lid | unmapped | - | 329 |
| trunk-lid | no_records | - | 1168 |
| trunk-lid | not_closed | no_year_manifest | 3949 |
| window-regulator | unmapped | - | 329 |
| window-regulator | no_records | - | 249 |
| window-regulator | not_closed | no_year_manifest | 4868 |
| window-switch | unmapped | - | 329 |
| window-switch | no_records | - | 2879 |
| window-switch | not_closed | no_year_manifest | 2238 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 329 |
| ac-compressor | no_records | - | 1510 |
| ac-compressor | split | option_split | 2370 |
| ac-compressor | conditional | conditional:engine_unattested | 1237 |
| alternator | unmapped | - | 329 |
| alternator | no_records | - | 1516 |
| alternator | split | option_split | 1578 |
| alternator | conditional | conditional:engine_unattested | 352 |
| alternator | conditional | conditional:qualifier | 1671 |
| bumper-front | unmapped | - | 329 |
| bumper-front | no_records | - | 987 |
| bumper-front | split | option_split | 3242 |
| bumper-front | conditional | conditional:engine_unattested | 888 |
| bumper-rear | unmapped | - | 329 |
| bumper-rear | no_records | - | 1325 |
| bumper-rear | split | option_split | 1967 |
| bumper-rear | conditional | conditional:engine_unattested | 1825 |
| climate-control | unmapped | - | 329 |
| climate-control | no_records | - | 1715 |
| climate-control | split | option_split | 3127 |
| climate-control | conditional | conditional:engine_unattested | 275 |
| door-front | unmapped | - | 329 |
| door-front | no_records | - | 233 |
| door-front | split | option_split | 1162 |
| door-front | conditional | conditional:engine_unattested | 3722 |
| door-rear | unmapped | - | 329 |
| door-rear | no_records | - | 530 |
| door-rear | split | option_split | 1370 |
| door-rear | conditional | conditional:engine_unattested | 3217 |
| fender | unmapped | - | 329 |
| fender | no_records | - | 498 |
| fender | split | option_split | 1336 |
| fender | conditional | conditional:engine_unattested | 3283 |
| fuel-pump-module | unmapped | - | 329 |
| fuel-pump-module | no_records | - | 4815 |
| fuel-pump-module | conditional | conditional:engine_unattested | 302 |
| gauge-cluster | unmapped | - | 329 |
| gauge-cluster | no_records | - | 576 |
| gauge-cluster | split | option_split | 3902 |
| gauge-cluster | conditional | conditional:engine_unattested | 639 |
| grille | unmapped | - | 329 |
| grille | no_records | - | 3830 |
| grille | split | option_split | 1287 |
| headlights | unmapped | - | 329 |
| headlights | no_records | - | 367 |
| headlights | split | option_split | 4365 |
| headlights | conditional | conditional:engine_unattested | 385 |
| hood | unmapped | - | 329 |
| hood | no_records | - | 571 |
| hood | split | option_split | 1669 |
| hood | conditional | conditional:engine_unattested | 2877 |
| ignition-coils | unmapped | - | 329 |
| ignition-coils | no_records | - | 103 |
| ignition-coils | split | option_split | 3070 |
| ignition-coils | conditional | conditional:engine_unattested | 1874 |
| ignition-coils | conditional | conditional:package | 70 |
| power-steering-pump | unmapped | - | 329 |
| power-steering-pump | no_records | - | 1472 |
| power-steering-pump | split | option_split | 2737 |
| power-steering-pump | conditional | conditional:engine_unattested | 681 |
| power-steering-pump | conditional | conditional:qualifier | 227 |
| radiator | unmapped | - | 329 |
| radiator | no_records | - | 570 |
| radiator | split | option_split | 3910 |
| radiator | conditional | conditional:engine_unattested | 637 |
| side-mirrors | unmapped | - | 329 |
| side-mirrors | no_records | - | 892 |
| side-mirrors | split | option_split | 3818 |
| side-mirrors | conditional | conditional:option | 71 |
| side-mirrors | conditional | conditional:qualifier | 336 |
| starter | unmapped | - | 329 |
| starter | no_records | - | 110 |
| starter | split | option_split | 3783 |
| starter | conditional | conditional:engine_unattested | 87 |
| starter | conditional | conditional:qualifier | 1137 |
| tail-lights | unmapped | - | 329 |
| tail-lights | no_records | - | 1050 |
| tail-lights | split | option_split | 3952 |
| tail-lights | conditional | conditional:engine_unattested | 115 |
| throttle-body | unmapped | - | 329 |
| throttle-body | no_records | - | 451 |
| throttle-body | split | option_split | 914 |
| throttle-body | conditional | conditional:engine_unattested | 3746 |
| throttle-body | conditional | conditional:package | 6 |
| trunk-lid | unmapped | - | 329 |
| trunk-lid | no_records | - | 1168 |
| trunk-lid | split | option_split | 2757 |
| trunk-lid | conditional | conditional:engine_unattested | 915 |
| trunk-lid | conditional | conditional:qualifier | 277 |
| window-regulator | unmapped | - | 329 |
| window-regulator | no_records | - | 249 |
| window-regulator | split | packaging_unstated | 4868 |
| window-switch | unmapped | - | 329 |
| window-switch | no_records | - | 2879 |
| window-switch | split | option_split | 2238 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- universal_part_suspect: 172

## Unknown note clauses (top 30)

- `electric`: 239
- `Extra Info: MPH`: 120
- `Extra Info: GLANZSCHWARZ`: 74
- `Only in conjunction with: 63117489213`: 70
- `with memory(S459A)`: 70
- `Headlight Xenon does not comprise ignition control unit and Xenon light bulb`: 58
- `For Vehicles With: Xenon Light(S522A)`: 54
- `For Vehicles With: Seat adjustment`: 53
- `Front panel`: 48
- `control`: 48
- `Production Date: From 201404`: 38
- `For Vehicles With: Xenon Light(S522A) and Adaptive Headlights(S524A)`: 36
- `Production Date: Till 200509`: 34
- `Headlight does not contains any electronic components or xenon lamp`: 32
- `For Vehicles With: White direction indicator lights(S785A)`: 31
- `Extra Info: PDC`: 28
- `Production Date: Till 200109`: 27
- `Production Date: From 200303`: 26
- `Production Date: From 200310`: 26
- `Production Date: Till 200503`: 26
- `Production Date: From 200503`: 24
- `Production Date: Till 201404`: 24
- `Production Date: Till 200310`: 23
- `Production Date: Till 200907`: 23
- `and vehicles produced from 01.03.2013`: 22
- `Extra Info: CHROM PEARLGREY`: 21
- `Production Date: Till 200409`: 21
- `Extra Info: PERLGLANZ CHROM`: 20
- `For Vehicles With: Interior/outside mirror with auto dip(S430A)`: 20
- `For Vehicles With: Park Distance Control (PDC)(S508A)`: 20

## Unmapped catalog models

- BMW 1 Series M: feed '1 Series M' 0 cars
- BMW 228i xDrive: feed '228i xDrive' 0 cars
- BMW 230i xDrive: feed '230i xDrive' 0 cars
- BMW 323is: feed '323is' 0 cars
- BMW 328i GT: feed '328i GT' 0 cars
- BMW 330e: feed '330e' 0 cars
- BMW 330i xDrive: feed '330i xDrive' 0 cars
- BMW 335i GT xDrive: feed '335i GT xDrive' 0 cars
- BMW 340i GT xDrive: feed '340i GT xDrive' 0 cars
- BMW 340i xDrive: feed '340i xDrive' 0 cars
- BMW 428i xDrive: feed '428i xDrive' 0 cars
- BMW 428i xDrive Gran Coupe: feed '428i xDrive Gran Coupe' 0 cars
- BMW 430i Gran Coupe: feed '430i Gran Coupe' 0 cars
- BMW 430i xDrive Gran Coupe: feed '430i xDrive Gran Coupe' 0 cars
- BMW 435i Gran Coupe: feed '435i Gran Coupe' 0 cars
- BMW 435i xDrive: feed '435i xDrive' 0 cars
- BMW 435i xDrive Gran Coupe: feed '435i xDrive Gran Coupe' 0 cars
- BMW 440i: feed '440i' 0 cars
- BMW 440i Gran Coupe: feed '440i Gran Coupe' 0 cars
- BMW 440i xDrive: feed '440i xDrive' 0 cars
- BMW 440i xDrive Gran Coupe: feed '440i xDrive Gran Coupe' 0 cars
- BMW 525iT: feed '525iT' 0 cars
- BMW 535d: feed '535d' 0 cars
- BMW 535d xDrive: feed '535d xDrive' 0 cars
- BMW 535i GT xDrive: feed '535i GT xDrive' 0 cars
- BMW 640i Gran Coupe: feed '640i Gran Coupe' 0 cars
- BMW 640i xDrive: feed '640i xDrive' 0 cars
- BMW 640i xDrive Gran Coupe: feed '640i xDrive Gran Coupe' 0 cars
- BMW 650i Gran Coupe: feed '650i Gran Coupe' 0 cars
- BMW 650i xDrive: feed '650i xDrive' 0 cars
- BMW 650i xDrive Gran Coupe: feed '650i xDrive Gran Coupe' 0 cars
- BMW 740Ld xDrive: feed '740Ld xDrive' 0 cars
- BMW 750i xDrive: feed '750i xDrive' 0 cars
- BMW 840Ci: feed '840ci' 0 cars
- BMW 840i: feed '840i' 0 cars
- BMW 840i xDrive: feed '840i xDrive' 0 cars
- BMW 850CSi: feed '850CSi' 0 cars
- BMW 850Ci: feed '850ci' 0 cars
- BMW ActiveHybrid 7: feed 'ActiveHybrid 7' 0 cars
- BMW Alpina B6 xDrive Gran Coupe: feed 'Alpina B6 xDrive Gran Coupe' 0 cars
- BMW Alpina V8 Roadster: feed 'Alpina V8 Roadster' 0 cars
- BMW M2: feed 'M2' 0 cars
- BMW M235i xDrive: feed 'M235i xDrive' 0 cars
- BMW M240i: feed 'M240i' 0 cars
- BMW M240i xDrive: feed 'M240i xDrive' 0 cars
- BMW M4: feed 'M4' 0 cars
- BMW M550i xDrive: feed 'M550i xDrive' 0 cars
- BMW M6: feed 'M6' 0 cars
- BMW M760i xDrive: feed 'M760i xDrive' 0 cars
- BMW M8: feed 'M8' 0 cars
- BMW M850i xDrive: feed 'M850i xDrive' 0 cars
- BMW X5 M: feed 'X5 M' 0 cars
- BMW X6 M: feed 'X6 M' 0 cars
- BMW X7: feed 'X7' 0 cars
- BMW Z3 M: feed 'Z3 M' 0 cars
- BMW Z4 M: feed 'Z4 M' 0 cars
- BMW Z8: feed 'Z8' 0 cars
- BMW i3s: feed 'i3s' 0 cars
- BMW i8: feed 'i8' 0 cars
