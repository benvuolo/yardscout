# OEM curation report: bmw

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-05T10:07:33Z.

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
| ac-compressor | unmapped | - | 323 |
| ac-compressor | no_records | - | 1503 |
| ac-compressor | not_closed | no_year_manifest | 3565 |
| alternator | unmapped | - | 323 |
| alternator | no_records | - | 1497 |
| alternator | not_closed | no_year_manifest | 3571 |
| bumper-front | unmapped | - | 323 |
| bumper-front | no_records | - | 970 |
| bumper-front | not_closed | no_year_manifest | 4098 |
| bumper-rear | unmapped | - | 323 |
| bumper-rear | no_records | - | 1314 |
| bumper-rear | not_closed | no_year_manifest | 3754 |
| climate-control | unmapped | - | 323 |
| climate-control | no_records | - | 1701 |
| climate-control | not_closed | no_year_manifest | 3367 |
| door-front | unmapped | - | 323 |
| door-front | no_records | - | 231 |
| door-front | not_closed | no_year_manifest | 4837 |
| door-rear | unmapped | - | 323 |
| door-rear | no_records | - | 526 |
| door-rear | not_closed | no_year_manifest | 4542 |
| fender | unmapped | - | 323 |
| fender | no_records | - | 495 |
| fender | not_closed | no_year_manifest | 4573 |
| fuel-pump-module | unmapped | - | 323 |
| fuel-pump-module | no_records | - | 4765 |
| fuel-pump-module | not_closed | no_year_manifest | 303 |
| gauge-cluster | unmapped | - | 323 |
| gauge-cluster | no_records | - | 562 |
| gauge-cluster | not_closed | no_year_manifest | 4506 |
| grille | unmapped | - | 323 |
| grille | no_records | - | 3787 |
| grille | not_closed | no_year_manifest | 1281 |
| headlights | unmapped | - | 323 |
| headlights | no_records | - | 359 |
| headlights | not_closed | no_year_manifest | 4709 |
| hood | unmapped | - | 323 |
| hood | no_records | - | 566 |
| hood | not_closed | no_year_manifest | 4502 |
| ignition-coils | unmapped | - | 323 |
| ignition-coils | no_records | - | 103 |
| ignition-coils | not_closed | no_year_manifest | 4965 |
| power-steering-pump | unmapped | - | 323 |
| power-steering-pump | no_records | - | 1463 |
| power-steering-pump | not_closed | no_year_manifest | 3605 |
| radiator | unmapped | - | 323 |
| radiator | no_records | - | 564 |
| radiator | not_closed | no_year_manifest | 4504 |
| side-mirrors | unmapped | - | 323 |
| side-mirrors | no_records | - | 882 |
| side-mirrors | not_closed | no_year_manifest | 4186 |
| starter | unmapped | - | 323 |
| starter | no_records | - | 109 |
| starter | not_closed | no_year_manifest | 4959 |
| tail-lights | unmapped | - | 323 |
| tail-lights | no_records | - | 1024 |
| tail-lights | not_closed | no_year_manifest | 4044 |
| throttle-body | unmapped | - | 323 |
| throttle-body | no_records | - | 453 |
| throttle-body | not_closed | no_year_manifest | 4615 |
| trunk-lid | unmapped | - | 323 |
| trunk-lid | no_records | - | 1167 |
| trunk-lid | not_closed | no_year_manifest | 3901 |
| window-regulator | unmapped | - | 323 |
| window-regulator | no_records | - | 242 |
| window-regulator | not_closed | no_year_manifest | 4826 |
| window-switch | unmapped | - | 323 |
| window-switch | no_records | - | 2864 |
| window-switch | not_closed | no_year_manifest | 2204 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 323 |
| ac-compressor | no_records | - | 1503 |
| ac-compressor | split | option_split | 2345 |
| ac-compressor | conditional | conditional:engine_unattested | 1220 |
| alternator | unmapped | - | 323 |
| alternator | no_records | - | 1497 |
| alternator | split | option_split | 1563 |
| alternator | conditional | conditional:engine_unattested | 352 |
| alternator | conditional | conditional:qualifier | 1656 |
| bumper-front | unmapped | - | 323 |
| bumper-front | no_records | - | 970 |
| bumper-front | split | option_split | 3225 |
| bumper-front | conditional | conditional:engine_unattested | 873 |
| bumper-rear | unmapped | - | 323 |
| bumper-rear | no_records | - | 1314 |
| bumper-rear | split | option_split | 1956 |
| bumper-rear | conditional | conditional:engine_unattested | 1798 |
| climate-control | unmapped | - | 323 |
| climate-control | no_records | - | 1701 |
| climate-control | split | option_split | 3104 |
| climate-control | conditional | conditional:engine_unattested | 263 |
| door-front | unmapped | - | 323 |
| door-front | no_records | - | 231 |
| door-front | split | option_split | 1150 |
| door-front | conditional | conditional:engine_unattested | 3687 |
| door-rear | unmapped | - | 323 |
| door-rear | no_records | - | 526 |
| door-rear | split | option_split | 1371 |
| door-rear | conditional | conditional:engine_unattested | 3171 |
| fender | unmapped | - | 323 |
| fender | no_records | - | 495 |
| fender | split | option_split | 1308 |
| fender | conditional | conditional:engine_unattested | 3265 |
| fuel-pump-module | unmapped | - | 323 |
| fuel-pump-module | no_records | - | 4765 |
| fuel-pump-module | conditional | conditional:engine_unattested | 303 |
| gauge-cluster | unmapped | - | 323 |
| gauge-cluster | no_records | - | 562 |
| gauge-cluster | split | option_split | 3876 |
| gauge-cluster | conditional | conditional:engine_unattested | 630 |
| grille | unmapped | - | 323 |
| grille | no_records | - | 3787 |
| grille | split | option_split | 1281 |
| headlights | unmapped | - | 323 |
| headlights | no_records | - | 359 |
| headlights | split | option_split | 4328 |
| headlights | conditional | conditional:engine_unattested | 381 |
| hood | unmapped | - | 323 |
| hood | no_records | - | 566 |
| hood | split | option_split | 1651 |
| hood | conditional | conditional:engine_unattested | 2851 |
| ignition-coils | unmapped | - | 323 |
| ignition-coils | no_records | - | 103 |
| ignition-coils | split | option_split | 3041 |
| ignition-coils | conditional | conditional:engine_unattested | 1856 |
| ignition-coils | conditional | conditional:package | 68 |
| power-steering-pump | unmapped | - | 323 |
| power-steering-pump | no_records | - | 1463 |
| power-steering-pump | split | option_split | 2718 |
| power-steering-pump | conditional | conditional:engine_unattested | 665 |
| power-steering-pump | conditional | conditional:qualifier | 222 |
| radiator | unmapped | - | 323 |
| radiator | no_records | - | 564 |
| radiator | split | option_split | 3867 |
| radiator | conditional | conditional:engine_unattested | 637 |
| side-mirrors | unmapped | - | 323 |
| side-mirrors | no_records | - | 882 |
| side-mirrors | split | option_split | 3784 |
| side-mirrors | conditional | conditional:option | 71 |
| side-mirrors | conditional | conditional:qualifier | 331 |
| starter | unmapped | - | 323 |
| starter | no_records | - | 109 |
| starter | split | option_split | 3751 |
| starter | conditional | conditional:engine_unattested | 89 |
| starter | conditional | conditional:qualifier | 1119 |
| tail-lights | unmapped | - | 323 |
| tail-lights | no_records | - | 1024 |
| tail-lights | split | option_split | 3927 |
| tail-lights | conditional | conditional:engine_unattested | 117 |
| throttle-body | unmapped | - | 323 |
| throttle-body | no_records | - | 453 |
| throttle-body | split | option_split | 897 |
| throttle-body | conditional | conditional:engine_unattested | 3712 |
| throttle-body | conditional | conditional:package | 6 |
| trunk-lid | unmapped | - | 323 |
| trunk-lid | no_records | - | 1167 |
| trunk-lid | split | option_split | 2722 |
| trunk-lid | conditional | conditional:engine_unattested | 903 |
| trunk-lid | conditional | conditional:qualifier | 276 |
| window-regulator | unmapped | - | 323 |
| window-regulator | no_records | - | 242 |
| window-regulator | split | packaging_unstated | 4826 |
| window-switch | unmapped | - | 323 |
| window-switch | no_records | - | 2864 |
| window-switch | split | option_split | 2204 |

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
