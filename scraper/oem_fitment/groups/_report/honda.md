# OEM curation report: honda

Raw: `3b4677ae1df7` @ `3b4677ae1df7`; as of 2026-11-05T21:30:02Z.

- records 2213, classes 2177, list rows 8746, year manifests 50, cells 3925
- Verified groups 0, engine vg groups 0, Likely groups 0
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.acurapartswarehouse.com, www.hondapartsnow.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.acurapartswarehouse.com: only 0% of its 2965 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)
- www.hondapartsnow.com: only 0% of its 5844 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 399 |
| ac-compressor | no_records | - | 2028 |
| ac-compressor | not_closed | no_year_manifest | 25249 |
| ac-compressor | not_closed | year_manifest_bad | 914 |
| alternator | unmapped | - | 399 |
| alternator | no_records | - | 2924 |
| alternator | not_closed | no_year_manifest | 24424 |
| alternator | not_closed | year_manifest_bad | 843 |
| bumper-front | unmapped | - | 399 |
| bumper-front | no_records | - | 7048 |
| bumper-front | not_closed | no_year_manifest | 20219 |
| bumper-front | not_closed | year_manifest_bad | 924 |
| bumper-rear | unmapped | - | 399 |
| bumper-rear | no_records | - | 5107 |
| bumper-rear | not_closed | no_year_manifest | 22160 |
| bumper-rear | not_closed | year_manifest_bad | 924 |
| climate-control | unmapped | - | 399 |
| climate-control | no_records | - | 10876 |
| climate-control | not_closed | no_year_manifest | 16711 |
| climate-control | not_closed | year_manifest_bad | 604 |
| door-front | unmapped | - | 399 |
| door-front | no_records | - | 2891 |
| door-front | not_closed | no_year_manifest | 24376 |
| door-front | not_closed | year_manifest_bad | 924 |
| door-rear | unmapped | - | 399 |
| door-rear | no_records | - | 5410 |
| door-rear | not_closed | no_year_manifest | 21945 |
| door-rear | not_closed | year_manifest_bad | 836 |
| fender | unmapped | - | 399 |
| fender | no_records | - | 20500 |
| fender | not_closed | no_year_manifest | 6769 |
| fender | not_closed | year_manifest_bad | 922 |
| fuel-pump-module | unmapped | - | 399 |
| fuel-pump-module | no_records | - | 5432 |
| fuel-pump-module | not_closed | no_year_manifest | 21867 |
| fuel-pump-module | not_closed | year_manifest_bad | 892 |
| gauge-cluster | unmapped | - | 399 |
| gauge-cluster | no_records | - | 18661 |
| gauge-cluster | not_closed | no_year_manifest | 8611 |
| gauge-cluster | not_closed | year_manifest_bad | 919 |
| grille | unmapped | - | 399 |
| grille | no_records | - | 22953 |
| grille | not_closed | no_year_manifest | 4485 |
| grille | not_closed | year_manifest_bad | 753 |
| headlights | unmapped | - | 399 |
| headlights | no_records | - | 6851 |
| headlights | not_closed | no_year_manifest | 20426 |
| headlights | not_closed | year_manifest_bad | 914 |
| hood | unmapped | - | 399 |
| hood | no_records | - | 5916 |
| hood | not_closed | no_year_manifest | 21351 |
| hood | not_closed | year_manifest_bad | 924 |
| ignition-coils | unmapped | - | 399 |
| ignition-coils | no_records | - | 3225 |
| ignition-coils | not_closed | no_year_manifest | 24241 |
| ignition-coils | not_closed | year_manifest_bad | 725 |
| liftgate | unmapped | - | 399 |
| liftgate | no_records | - | 22779 |
| liftgate | not_closed | no_year_manifest | 4989 |
| liftgate | not_closed | year_manifest_bad | 423 |
| power-steering-pump | unmapped | - | 399 |
| power-steering-pump | no_records | - | 5474 |
| power-steering-pump | not_closed | no_year_manifest | 22146 |
| power-steering-pump | not_closed | year_manifest_bad | 571 |
| radiator | unmapped | - | 399 |
| radiator | no_records | - | 3228 |
| radiator | not_closed | no_year_manifest | 24039 |
| radiator | not_closed | year_manifest_bad | 924 |
| side-mirrors | unmapped | - | 399 |
| side-mirrors | no_records | - | 3080 |
| side-mirrors | not_closed | no_year_manifest | 24200 |
| side-mirrors | not_closed | year_manifest_bad | 911 |
| starter | unmapped | - | 399 |
| starter | no_records | - | 2867 |
| starter | not_closed | no_year_manifest | 24488 |
| starter | not_closed | year_manifest_bad | 836 |
| tail-lights | unmapped | - | 399 |
| tail-lights | no_records | - | 7478 |
| tail-lights | not_closed | no_year_manifest | 19797 |
| tail-lights | not_closed | year_manifest_bad | 916 |
| tailgate | unmapped | - | 399 |
| tailgate | no_records | - | 27963 |
| tailgate | not_closed | no_year_manifest | 142 |
| tailgate | not_closed | year_manifest_bad | 86 |
| throttle-body | unmapped | - | 399 |
| throttle-body | no_records | - | 3424 |
| throttle-body | not_closed | no_year_manifest | 23875 |
| throttle-body | not_closed | year_manifest_bad | 892 |
| trunk-lid | unmapped | - | 399 |
| trunk-lid | no_records | - | 13623 |
| trunk-lid | not_closed | no_year_manifest | 14284 |
| trunk-lid | not_closed | year_manifest_bad | 284 |
| window-regulator | unmapped | - | 399 |
| window-regulator | no_records | - | 897 |
| window-regulator | not_closed | no_year_manifest | 26378 |
| window-regulator | not_closed | year_manifest_bad | 916 |
| window-switch | unmapped | - | 399 |
| window-switch | no_records | - | 5224 |
| window-switch | not_closed | no_year_manifest | 22056 |
| window-switch | not_closed | year_manifest_bad | 911 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 399 |
| ac-compressor | no_records | - | 2028 |
| ac-compressor | split | option_split | 9504 |
| ac-compressor | conditional | conditional:engine_unattested | 16659 |
| alternator | unmapped | - | 399 |
| alternator | no_records | - | 2924 |
| alternator | split | option_split | 12933 |
| alternator | conditional | conditional:engine_unattested | 12334 |
| bumper-front | unmapped | - | 399 |
| bumper-front | no_records | - | 7048 |
| bumper-front | split | no_candidates | 2 |
| bumper-front | split | option_split | 6462 |
| bumper-front | conditional | conditional:engine_unattested | 14679 |
| bumper-rear | unmapped | - | 399 |
| bumper-rear | no_records | - | 5107 |
| bumper-rear | split | option_split | 3815 |
| bumper-rear | conditional | conditional:engine_unattested | 19269 |
| climate-control | unmapped | - | 399 |
| climate-control | no_records | - | 10876 |
| climate-control | split | option_split | 11208 |
| climate-control | conditional | conditional:engine_unattested | 6107 |
| door-front | unmapped | - | 399 |
| door-front | no_records | - | 2891 |
| door-front | split | no_candidates | 24 |
| door-front | split | option_split | 5264 |
| door-front | split | position_missing | 317 |
| door-front | split | slot_missing | 165 |
| door-front | conditional | conditional:engine_unattested | 19530 |
| door-rear | unmapped | - | 399 |
| door-rear | no_records | - | 5410 |
| door-rear | split | no_candidates | 102 |
| door-rear | split | option_split | 5420 |
| door-rear | split | position_missing | 317 |
| door-rear | split | slot_missing | 636 |
| door-rear | conditional | conditional:engine_unattested | 16306 |
| fender | unmapped | - | 399 |
| fender | no_records | - | 20500 |
| fender | split | no_candidates | 802 |
| fender | conditional | conditional:engine_unattested | 6889 |
| fuel-pump-module | unmapped | - | 399 |
| fuel-pump-module | no_records | - | 5432 |
| fuel-pump-module | split | option_split | 12997 |
| fuel-pump-module | conditional | conditional:engine_unattested | 9762 |
| gauge-cluster | unmapped | - | 399 |
| gauge-cluster | no_records | - | 18661 |
| gauge-cluster | split | no_candidates | 285 |
| gauge-cluster | split | option_split | 5687 |
| gauge-cluster | conditional | conditional:engine_unattested | 3558 |
| grille | unmapped | - | 399 |
| grille | no_records | - | 22953 |
| grille | split | no_candidates | 515 |
| grille | split | option_split | 948 |
| grille | conditional | conditional:engine_unattested | 3775 |
| headlights | unmapped | - | 399 |
| headlights | no_records | - | 6851 |
| headlights | split | option_split | 3463 |
| headlights | conditional | conditional:engine_unattested | 17877 |
| hood | unmapped | - | 399 |
| hood | no_records | - | 5916 |
| hood | split | no_candidates | 78 |
| hood | split | option_split | 1767 |
| hood | conditional | conditional:engine_unattested | 20430 |
| ignition-coils | unmapped | - | 399 |
| ignition-coils | no_records | - | 3225 |
| ignition-coils | split | no_candidates | 70 |
| ignition-coils | split | option_split | 11952 |
| ignition-coils | conditional | conditional:engine_unattested | 10385 |
| ignition-coils | conditional | conditional:package | 2559 |
| liftgate | unmapped | - | 399 |
| liftgate | no_records | - | 22779 |
| liftgate | split | no_candidates | 2 |
| liftgate | split | option_split | 1292 |
| liftgate | conditional | conditional:engine_unattested | 4118 |
| power-steering-pump | unmapped | - | 399 |
| power-steering-pump | no_records | - | 5474 |
| power-steering-pump | split | option_split | 7753 |
| power-steering-pump | conditional | conditional:engine_unattested | 14964 |
| radiator | unmapped | - | 399 |
| radiator | no_records | - | 3228 |
| radiator | split | option_split | 14020 |
| radiator | conditional | conditional:engine_unattested | 10943 |
| side-mirrors | unmapped | - | 399 |
| side-mirrors | no_records | - | 3080 |
| side-mirrors | split | option_split | 23871 |
| side-mirrors | split | slot_missing | 313 |
| side-mirrors | conditional | conditional:engine_unattested | 927 |
| starter | unmapped | - | 399 |
| starter | no_records | - | 2867 |
| starter | split | option_split | 11924 |
| starter | conditional | conditional:engine_unattested | 13400 |
| tail-lights | unmapped | - | 399 |
| tail-lights | no_records | - | 7478 |
| tail-lights | split | option_split | 5451 |
| tail-lights | split | slot_missing | 605 |
| tail-lights | conditional | conditional:engine_unattested | 14657 |
| tailgate | unmapped | - | 399 |
| tailgate | no_records | - | 27963 |
| tailgate | conditional | conditional:engine_unattested | 228 |
| throttle-body | unmapped | - | 399 |
| throttle-body | no_records | - | 3424 |
| throttle-body | split | option_split | 14608 |
| throttle-body | conditional | conditional:engine_unattested | 10159 |
| trunk-lid | unmapped | - | 399 |
| trunk-lid | no_records | - | 13623 |
| trunk-lid | split | option_split | 6050 |
| trunk-lid | conditional | conditional:engine_unattested | 8440 |
| trunk-lid | conditional | conditional:model_other | 78 |
| window-regulator | unmapped | - | 399 |
| window-regulator | no_records | - | 897 |
| window-regulator | split | packaging_unstated | 27294 |
| window-switch | unmapped | - | 399 |
| window-switch | no_records | - | 5224 |
| window-switch | split | option_split | 13313 |
| window-switch | split | position_missing | 3450 |
| window-switch | conditional | conditional:engine_unattested | 6204 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 11
- disputed_class: 36
- rule_drift: 7

## Unknown note clauses (top 30)

- `Package Quantity: 1`: 34
- `Require Quantity: 6`: 18
- `Interior Color: A-BLACK`: 17
- `F-IVORY`: 16
- `Require Quantity: 4`: 16
- `Interior Color: B-GRAY`: 11
- `Fit Note: Mfg.Origin: JPN`: 10
- `Fit Note: Mfg.Origin: USA`: 10
- `Interior Color: A-BLACK/GRAY`: 8
- `B-GRAY`: 6
- `D-BLACK`: 5
- `C-BLUE`: 4
- `C-GRAY/GREEN`: 4
- `F-BEIGE`: 4
- `B-GRAY/BLUE`: 3
- `H-BLACK/BROWN`: 3
- `Interior Color: F-LIGHT GRAY`: 3
- `P-TAUPE`: 3
- `B-MEDIUM GRAY`: 2
- `C-TRUFFLE`: 2
- `E-TAUPE`: 2
- `G-FERN`: 2
- `Interior Color: B-GRAY/BLUE`: 2
- `Interior Color: B-QUARTZ GRAY`: 2
- `Interior Color: C-BLUE`: 2
- `Interior Color: D-RED`: 2
- `Interior Color: Y-GRAY`: 2
- `L-BEIGE`: 2
- `W-DARK GRAY`: 2
- `Y-QUARTZ GRAY`: 2

## Unmapped catalog models

- Acura ILX: feed 'ILX' 68 cars
- Acura ILX Hybrid: feed 'ILX Hybrid' 0 cars
- Acura NSX: feed 'NSX' 0 cars
- Honda Fit EV: feed 'Fit EV' 0 cars
- Honda Passport: feed 'Passport' 82 cars
- Honda S2000: feed 'S2000' 0 cars
