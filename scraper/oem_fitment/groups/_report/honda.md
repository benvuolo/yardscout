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
| ac-compressor | unmapped | - | 406 |
| ac-compressor | no_records | - | 2017 |
| ac-compressor | not_closed | no_year_manifest | 25228 |
| ac-compressor | not_closed | year_manifest_bad | 912 |
| alternator | unmapped | - | 406 |
| alternator | no_records | - | 2929 |
| alternator | not_closed | no_year_manifest | 24385 |
| alternator | not_closed | year_manifest_bad | 843 |
| bumper-front | unmapped | - | 406 |
| bumper-front | no_records | - | 7049 |
| bumper-front | not_closed | no_year_manifest | 20185 |
| bumper-front | not_closed | year_manifest_bad | 923 |
| bumper-rear | unmapped | - | 406 |
| bumper-rear | no_records | - | 5105 |
| bumper-rear | not_closed | no_year_manifest | 22129 |
| bumper-rear | not_closed | year_manifest_bad | 923 |
| climate-control | unmapped | - | 406 |
| climate-control | no_records | - | 10844 |
| climate-control | not_closed | no_year_manifest | 16712 |
| climate-control | not_closed | year_manifest_bad | 601 |
| door-front | unmapped | - | 406 |
| door-front | no_records | - | 2884 |
| door-front | not_closed | no_year_manifest | 24350 |
| door-front | not_closed | year_manifest_bad | 923 |
| door-rear | unmapped | - | 406 |
| door-rear | no_records | - | 5424 |
| door-rear | not_closed | no_year_manifest | 21899 |
| door-rear | not_closed | year_manifest_bad | 834 |
| fender | unmapped | - | 406 |
| fender | no_records | - | 20507 |
| fender | not_closed | no_year_manifest | 6729 |
| fender | not_closed | year_manifest_bad | 921 |
| fuel-pump-module | unmapped | - | 406 |
| fuel-pump-module | no_records | - | 5445 |
| fuel-pump-module | not_closed | no_year_manifest | 21823 |
| fuel-pump-module | not_closed | year_manifest_bad | 889 |
| gauge-cluster | unmapped | - | 406 |
| gauge-cluster | no_records | - | 18641 |
| gauge-cluster | not_closed | no_year_manifest | 8599 |
| gauge-cluster | not_closed | year_manifest_bad | 917 |
| grille | unmapped | - | 406 |
| grille | no_records | - | 22951 |
| grille | not_closed | no_year_manifest | 4459 |
| grille | not_closed | year_manifest_bad | 747 |
| headlights | unmapped | - | 406 |
| headlights | no_records | - | 6858 |
| headlights | not_closed | no_year_manifest | 20387 |
| headlights | not_closed | year_manifest_bad | 912 |
| hood | unmapped | - | 406 |
| hood | no_records | - | 5923 |
| hood | not_closed | no_year_manifest | 21311 |
| hood | not_closed | year_manifest_bad | 923 |
| ignition-coils | unmapped | - | 406 |
| ignition-coils | no_records | - | 3231 |
| ignition-coils | not_closed | no_year_manifest | 24202 |
| ignition-coils | not_closed | year_manifest_bad | 724 |
| liftgate | unmapped | - | 406 |
| liftgate | no_records | - | 22769 |
| liftgate | not_closed | no_year_manifest | 4965 |
| liftgate | not_closed | year_manifest_bad | 423 |
| power-steering-pump | unmapped | - | 406 |
| power-steering-pump | no_records | - | 5464 |
| power-steering-pump | not_closed | no_year_manifest | 22123 |
| power-steering-pump | not_closed | year_manifest_bad | 570 |
| radiator | unmapped | - | 406 |
| radiator | no_records | - | 3228 |
| radiator | not_closed | no_year_manifest | 24006 |
| radiator | not_closed | year_manifest_bad | 923 |
| side-mirrors | unmapped | - | 406 |
| side-mirrors | no_records | - | 3078 |
| side-mirrors | not_closed | no_year_manifest | 24171 |
| side-mirrors | not_closed | year_manifest_bad | 908 |
| starter | unmapped | - | 406 |
| starter | no_records | - | 2867 |
| starter | not_closed | no_year_manifest | 24456 |
| starter | not_closed | year_manifest_bad | 834 |
| tail-lights | unmapped | - | 406 |
| tail-lights | no_records | - | 7485 |
| tail-lights | not_closed | no_year_manifest | 19758 |
| tail-lights | not_closed | year_manifest_bad | 914 |
| tailgate | unmapped | - | 406 |
| tailgate | no_records | - | 27931 |
| tailgate | not_closed | no_year_manifest | 142 |
| tailgate | not_closed | year_manifest_bad | 84 |
| throttle-body | unmapped | - | 406 |
| throttle-body | no_records | - | 3430 |
| throttle-body | not_closed | no_year_manifest | 23837 |
| throttle-body | not_closed | year_manifest_bad | 890 |
| trunk-lid | unmapped | - | 406 |
| trunk-lid | no_records | - | 13615 |
| trunk-lid | not_closed | no_year_manifest | 14255 |
| trunk-lid | not_closed | year_manifest_bad | 287 |
| window-regulator | unmapped | - | 406 |
| window-regulator | no_records | - | 889 |
| window-regulator | not_closed | no_year_manifest | 26354 |
| window-regulator | not_closed | year_manifest_bad | 914 |
| window-switch | unmapped | - | 406 |
| window-switch | no_records | - | 5237 |
| window-switch | not_closed | no_year_manifest | 22012 |
| window-switch | not_closed | year_manifest_bad | 908 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 406 |
| ac-compressor | no_records | - | 2017 |
| ac-compressor | split | option_split | 9471 |
| ac-compressor | conditional | conditional:engine_unattested | 16669 |
| alternator | unmapped | - | 406 |
| alternator | no_records | - | 2929 |
| alternator | split | option_split | 12916 |
| alternator | conditional | conditional:engine_unattested | 12312 |
| bumper-front | unmapped | - | 406 |
| bumper-front | no_records | - | 7049 |
| bumper-front | split | no_candidates | 2 |
| bumper-front | split | option_split | 6439 |
| bumper-front | conditional | conditional:engine_unattested | 14667 |
| bumper-rear | unmapped | - | 406 |
| bumper-rear | no_records | - | 5105 |
| bumper-rear | split | option_split | 3805 |
| bumper-rear | conditional | conditional:engine_unattested | 19247 |
| climate-control | unmapped | - | 406 |
| climate-control | no_records | - | 10844 |
| climate-control | split | option_split | 11234 |
| climate-control | conditional | conditional:engine_unattested | 6079 |
| door-front | unmapped | - | 406 |
| door-front | no_records | - | 2884 |
| door-front | split | no_candidates | 25 |
| door-front | split | option_split | 5246 |
| door-front | split | position_missing | 316 |
| door-front | split | slot_missing | 168 |
| door-front | conditional | conditional:engine_unattested | 19518 |
| door-rear | unmapped | - | 406 |
| door-rear | no_records | - | 5424 |
| door-rear | split | no_candidates | 103 |
| door-rear | split | option_split | 5424 |
| door-rear | split | position_missing | 316 |
| door-rear | split | slot_missing | 631 |
| door-rear | conditional | conditional:engine_unattested | 16259 |
| fender | unmapped | - | 406 |
| fender | no_records | - | 20507 |
| fender | split | no_candidates | 801 |
| fender | conditional | conditional:engine_unattested | 6849 |
| fuel-pump-module | unmapped | - | 406 |
| fuel-pump-module | no_records | - | 5445 |
| fuel-pump-module | split | option_split | 12960 |
| fuel-pump-module | conditional | conditional:engine_unattested | 9752 |
| gauge-cluster | unmapped | - | 406 |
| gauge-cluster | no_records | - | 18641 |
| gauge-cluster | split | no_candidates | 286 |
| gauge-cluster | split | option_split | 5671 |
| gauge-cluster | conditional | conditional:engine_unattested | 3559 |
| grille | unmapped | - | 406 |
| grille | no_records | - | 22951 |
| grille | split | no_candidates | 511 |
| grille | split | option_split | 950 |
| grille | conditional | conditional:engine_unattested | 3745 |
| headlights | unmapped | - | 406 |
| headlights | no_records | - | 6858 |
| headlights | split | option_split | 3464 |
| headlights | conditional | conditional:engine_unattested | 17835 |
| hood | unmapped | - | 406 |
| hood | no_records | - | 5923 |
| hood | split | no_candidates | 78 |
| hood | split | option_split | 1776 |
| hood | conditional | conditional:engine_unattested | 20380 |
| ignition-coils | unmapped | - | 406 |
| ignition-coils | no_records | - | 3231 |
| ignition-coils | split | no_candidates | 67 |
| ignition-coils | split | option_split | 11918 |
| ignition-coils | conditional | conditional:engine_unattested | 10379 |
| ignition-coils | conditional | conditional:package | 2562 |
| liftgate | unmapped | - | 406 |
| liftgate | no_records | - | 22769 |
| liftgate | split | no_candidates | 2 |
| liftgate | split | option_split | 1282 |
| liftgate | conditional | conditional:engine_unattested | 4104 |
| power-steering-pump | unmapped | - | 406 |
| power-steering-pump | no_records | - | 5464 |
| power-steering-pump | split | option_split | 7733 |
| power-steering-pump | conditional | conditional:engine_unattested | 14960 |
| radiator | unmapped | - | 406 |
| radiator | no_records | - | 3228 |
| radiator | split | option_split | 13980 |
| radiator | conditional | conditional:engine_unattested | 10949 |
| side-mirrors | unmapped | - | 406 |
| side-mirrors | no_records | - | 3078 |
| side-mirrors | split | option_split | 23843 |
| side-mirrors | split | slot_missing | 317 |
| side-mirrors | conditional | conditional:engine_unattested | 919 |
| starter | unmapped | - | 406 |
| starter | no_records | - | 2867 |
| starter | split | option_split | 11908 |
| starter | conditional | conditional:engine_unattested | 13382 |
| tail-lights | unmapped | - | 406 |
| tail-lights | no_records | - | 7485 |
| tail-lights | split | option_split | 5424 |
| tail-lights | split | slot_missing | 608 |
| tail-lights | conditional | conditional:engine_unattested | 14640 |
| tailgate | unmapped | - | 406 |
| tailgate | no_records | - | 27931 |
| tailgate | conditional | conditional:engine_unattested | 226 |
| throttle-body | unmapped | - | 406 |
| throttle-body | no_records | - | 3430 |
| throttle-body | split | option_split | 14580 |
| throttle-body | conditional | conditional:engine_unattested | 10147 |
| trunk-lid | unmapped | - | 406 |
| trunk-lid | no_records | - | 13615 |
| trunk-lid | split | option_split | 6045 |
| trunk-lid | conditional | conditional:engine_unattested | 8419 |
| trunk-lid | conditional | conditional:model_other | 78 |
| window-regulator | unmapped | - | 406 |
| window-regulator | no_records | - | 889 |
| window-regulator | split | packaging_unstated | 27268 |
| window-switch | unmapped | - | 406 |
| window-switch | no_records | - | 5237 |
| window-switch | split | option_split | 13285 |
| window-switch | split | position_missing | 3421 |
| window-switch | conditional | conditional:engine_unattested | 6214 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 11
- disputed_class: 36
- rule_drift: 7

## Unknown note clauses (top 30)

- `Fit Note: Mfg.Origin: JPN`: 126
- `Fit Note: Mfg.Origin: USA`: 80
- `Package Quantity: 1`: 34
- `CN2`: 30
- `Interior Color: A-BLACK`: 23
- `CN1`: 22
- `F-IVORY`: 20
- `CAN`: 19
- `Require Quantity: 6`: 18
- `Require Quantity: 4`: 16
- `USA`: 16
- `Interior Color: B-GRAY`: 11
- `B-GRAY`: 10
- `CN4`: 9
- `Fit Note: Mfg.Origin: CN1`: 9
- `CN3`: 8
- `Fit Note: Mfg.Origin: GBR`: 8
- `Interior Color: A-BLACK/GRAY`: 8
- `MEX`: 6
- `D-BLACK`: 5
- `C-BLUE`: 4
- `C-GRAY/GREEN`: 4
- `F-BEIGE`: 4
- `B-GRAY/BLUE`: 3
- `D-SADDLE`: 3
- `H-BLACK/BROWN`: 3
- `Interior Color: F-LIGHT GRAY`: 3
- `P-TAUPE`: 3
- `B-MEDIUM GRAY`: 2
- `C-TRUFFLE`: 2

## Unmapped catalog models

- Acura ILX: feed 'ILX' 72 cars
- Acura ILX Hybrid: feed 'ILX Hybrid' 0 cars
- Acura NSX: feed 'NSX' 0 cars
- Honda Fit EV: feed 'Fit EV' 0 cars
- Honda Passport: feed 'Passport' 85 cars
- Honda S2000: feed 'S2000' 0 cars
