# OEM curation report: honda

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-05T21:30:02Z.

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
| ac-compressor | unmapped | - | 396 |
| ac-compressor | no_records | - | 2030 |
| ac-compressor | not_closed | no_year_manifest | 25254 |
| ac-compressor | not_closed | year_manifest_bad | 913 |
| alternator | unmapped | - | 396 |
| alternator | no_records | - | 2927 |
| alternator | not_closed | no_year_manifest | 24427 |
| alternator | not_closed | year_manifest_bad | 843 |
| bumper-front | unmapped | - | 396 |
| bumper-front | no_records | - | 7063 |
| bumper-front | not_closed | no_year_manifest | 20211 |
| bumper-front | not_closed | year_manifest_bad | 923 |
| bumper-rear | unmapped | - | 396 |
| bumper-rear | no_records | - | 5117 |
| bumper-rear | not_closed | no_year_manifest | 22157 |
| bumper-rear | not_closed | year_manifest_bad | 923 |
| climate-control | unmapped | - | 396 |
| climate-control | no_records | - | 10851 |
| climate-control | not_closed | no_year_manifest | 16743 |
| climate-control | not_closed | year_manifest_bad | 603 |
| door-front | unmapped | - | 396 |
| door-front | no_records | - | 2882 |
| door-front | not_closed | no_year_manifest | 24392 |
| door-front | not_closed | year_manifest_bad | 923 |
| door-rear | unmapped | - | 396 |
| door-rear | no_records | - | 5422 |
| door-rear | not_closed | no_year_manifest | 21939 |
| door-rear | not_closed | year_manifest_bad | 836 |
| fender | unmapped | - | 396 |
| fender | no_records | - | 20538 |
| fender | not_closed | no_year_manifest | 6738 |
| fender | not_closed | year_manifest_bad | 921 |
| fuel-pump-module | unmapped | - | 396 |
| fuel-pump-module | no_records | - | 5456 |
| fuel-pump-module | not_closed | no_year_manifest | 21851 |
| fuel-pump-module | not_closed | year_manifest_bad | 890 |
| gauge-cluster | unmapped | - | 396 |
| gauge-cluster | no_records | - | 18666 |
| gauge-cluster | not_closed | no_year_manifest | 8613 |
| gauge-cluster | not_closed | year_manifest_bad | 918 |
| grille | unmapped | - | 396 |
| grille | no_records | - | 22986 |
| grille | not_closed | no_year_manifest | 4459 |
| grille | not_closed | year_manifest_bad | 752 |
| headlights | unmapped | - | 396 |
| headlights | no_records | - | 6870 |
| headlights | not_closed | no_year_manifest | 20414 |
| headlights | not_closed | year_manifest_bad | 913 |
| hood | unmapped | - | 396 |
| hood | no_records | - | 5924 |
| hood | not_closed | no_year_manifest | 21350 |
| hood | not_closed | year_manifest_bad | 923 |
| ignition-coils | unmapped | - | 396 |
| ignition-coils | no_records | - | 3222 |
| ignition-coils | not_closed | no_year_manifest | 24250 |
| ignition-coils | not_closed | year_manifest_bad | 725 |
| liftgate | unmapped | - | 396 |
| liftgate | no_records | - | 22777 |
| liftgate | not_closed | no_year_manifest | 4998 |
| liftgate | not_closed | year_manifest_bad | 422 |
| power-steering-pump | unmapped | - | 396 |
| power-steering-pump | no_records | - | 5472 |
| power-steering-pump | not_closed | no_year_manifest | 22157 |
| power-steering-pump | not_closed | year_manifest_bad | 568 |
| radiator | unmapped | - | 396 |
| radiator | no_records | - | 3232 |
| radiator | not_closed | no_year_manifest | 24042 |
| radiator | not_closed | year_manifest_bad | 923 |
| side-mirrors | unmapped | - | 396 |
| side-mirrors | no_records | - | 3068 |
| side-mirrors | not_closed | no_year_manifest | 24219 |
| side-mirrors | not_closed | year_manifest_bad | 910 |
| starter | unmapped | - | 396 |
| starter | no_records | - | 2863 |
| starter | not_closed | no_year_manifest | 24499 |
| starter | not_closed | year_manifest_bad | 835 |
| tail-lights | unmapped | - | 396 |
| tail-lights | no_records | - | 7487 |
| tail-lights | not_closed | no_year_manifest | 19795 |
| tail-lights | not_closed | year_manifest_bad | 915 |
| tailgate | unmapped | - | 396 |
| tailgate | no_records | - | 27970 |
| tailgate | not_closed | no_year_manifest | 142 |
| tailgate | not_closed | year_manifest_bad | 85 |
| throttle-body | unmapped | - | 396 |
| throttle-body | no_records | - | 3433 |
| throttle-body | not_closed | no_year_manifest | 23872 |
| throttle-body | not_closed | year_manifest_bad | 892 |
| trunk-lid | unmapped | - | 396 |
| trunk-lid | no_records | - | 13656 |
| trunk-lid | not_closed | no_year_manifest | 14256 |
| trunk-lid | not_closed | year_manifest_bad | 285 |
| window-regulator | unmapped | - | 396 |
| window-regulator | no_records | - | 891 |
| window-regulator | not_closed | no_year_manifest | 26391 |
| window-regulator | not_closed | year_manifest_bad | 915 |
| window-switch | unmapped | - | 396 |
| window-switch | no_records | - | 5242 |
| window-switch | not_closed | no_year_manifest | 22045 |
| window-switch | not_closed | year_manifest_bad | 910 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 396 |
| ac-compressor | no_records | - | 2030 |
| ac-compressor | split | option_split | 9479 |
| ac-compressor | conditional | conditional:engine_unattested | 16688 |
| alternator | unmapped | - | 396 |
| alternator | no_records | - | 2927 |
| alternator | split | option_split | 12918 |
| alternator | conditional | conditional:engine_unattested | 12352 |
| bumper-front | unmapped | - | 396 |
| bumper-front | no_records | - | 7063 |
| bumper-front | split | no_candidates | 2 |
| bumper-front | split | option_split | 6445 |
| bumper-front | conditional | conditional:engine_unattested | 14687 |
| bumper-rear | unmapped | - | 396 |
| bumper-rear | no_records | - | 5117 |
| bumper-rear | split | option_split | 3807 |
| bumper-rear | conditional | conditional:engine_unattested | 19273 |
| climate-control | unmapped | - | 396 |
| climate-control | no_records | - | 10851 |
| climate-control | split | option_split | 11227 |
| climate-control | conditional | conditional:engine_unattested | 6119 |
| door-front | unmapped | - | 396 |
| door-front | no_records | - | 2882 |
| door-front | split | no_candidates | 25 |
| door-front | split | option_split | 5252 |
| door-front | split | position_missing | 315 |
| door-front | split | slot_missing | 165 |
| door-front | conditional | conditional:engine_unattested | 19558 |
| door-rear | unmapped | - | 396 |
| door-rear | no_records | - | 5422 |
| door-rear | split | no_candidates | 103 |
| door-rear | split | option_split | 5447 |
| door-rear | split | position_missing | 315 |
| door-rear | split | slot_missing | 636 |
| door-rear | conditional | conditional:engine_unattested | 16274 |
| fender | unmapped | - | 396 |
| fender | no_records | - | 20538 |
| fender | split | no_candidates | 801 |
| fender | conditional | conditional:engine_unattested | 6858 |
| fuel-pump-module | unmapped | - | 396 |
| fuel-pump-module | no_records | - | 5456 |
| fuel-pump-module | split | option_split | 12967 |
| fuel-pump-module | conditional | conditional:engine_unattested | 9774 |
| gauge-cluster | unmapped | - | 396 |
| gauge-cluster | no_records | - | 18666 |
| gauge-cluster | split | no_candidates | 284 |
| gauge-cluster | split | option_split | 5676 |
| gauge-cluster | conditional | conditional:engine_unattested | 3571 |
| grille | unmapped | - | 396 |
| grille | no_records | - | 22986 |
| grille | split | no_candidates | 515 |
| grille | split | option_split | 945 |
| grille | conditional | conditional:engine_unattested | 3751 |
| headlights | unmapped | - | 396 |
| headlights | no_records | - | 6870 |
| headlights | split | option_split | 3455 |
| headlights | conditional | conditional:engine_unattested | 17872 |
| hood | unmapped | - | 396 |
| hood | no_records | - | 5924 |
| hood | split | no_candidates | 78 |
| hood | split | option_split | 1763 |
| hood | conditional | conditional:engine_unattested | 20432 |
| ignition-coils | unmapped | - | 396 |
| ignition-coils | no_records | - | 3222 |
| ignition-coils | split | no_candidates | 69 |
| ignition-coils | split | option_split | 11928 |
| ignition-coils | conditional | conditional:engine_unattested | 10414 |
| ignition-coils | conditional | conditional:package | 2564 |
| liftgate | unmapped | - | 396 |
| liftgate | no_records | - | 22777 |
| liftgate | split | no_candidates | 2 |
| liftgate | split | option_split | 1291 |
| liftgate | conditional | conditional:engine_unattested | 4127 |
| power-steering-pump | unmapped | - | 396 |
| power-steering-pump | no_records | - | 5472 |
| power-steering-pump | split | option_split | 7724 |
| power-steering-pump | conditional | conditional:engine_unattested | 15001 |
| radiator | unmapped | - | 396 |
| radiator | no_records | - | 3232 |
| radiator | split | option_split | 13982 |
| radiator | conditional | conditional:engine_unattested | 10983 |
| side-mirrors | unmapped | - | 396 |
| side-mirrors | no_records | - | 3068 |
| side-mirrors | split | option_split | 23882 |
| side-mirrors | split | slot_missing | 316 |
| side-mirrors | conditional | conditional:engine_unattested | 931 |
| starter | unmapped | - | 396 |
| starter | no_records | - | 2863 |
| starter | split | option_split | 11903 |
| starter | conditional | conditional:engine_unattested | 13431 |
| tail-lights | unmapped | - | 396 |
| tail-lights | no_records | - | 7487 |
| tail-lights | split | option_split | 5442 |
| tail-lights | split | slot_missing | 613 |
| tail-lights | conditional | conditional:engine_unattested | 14655 |
| tailgate | unmapped | - | 396 |
| tailgate | no_records | - | 27970 |
| tailgate | conditional | conditional:engine_unattested | 227 |
| throttle-body | unmapped | - | 396 |
| throttle-body | no_records | - | 3433 |
| throttle-body | split | option_split | 14583 |
| throttle-body | conditional | conditional:engine_unattested | 10181 |
| trunk-lid | unmapped | - | 396 |
| trunk-lid | no_records | - | 13656 |
| trunk-lid | split | option_split | 6052 |
| trunk-lid | conditional | conditional:engine_unattested | 8411 |
| trunk-lid | conditional | conditional:model_other | 78 |
| window-regulator | unmapped | - | 396 |
| window-regulator | no_records | - | 891 |
| window-regulator | split | packaging_unstated | 27306 |
| window-switch | unmapped | - | 396 |
| window-switch | no_records | - | 5242 |
| window-switch | split | option_split | 13300 |
| window-switch | split | position_missing | 3448 |
| window-switch | conditional | conditional:engine_unattested | 6207 |

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

- Acura ILX: feed 'ILX' 69 cars
- Acura ILX Hybrid: feed 'ILX Hybrid' 0 cars
- Acura NSX: feed 'NSX' 0 cars
- Honda Fit EV: feed 'Fit EV' 0 cars
- Honda Passport: feed 'Passport' 81 cars
- Honda S2000: feed 'S2000' 0 cars
