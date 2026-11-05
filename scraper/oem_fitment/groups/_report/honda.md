# OEM curation report: honda

Raw: `ceccc800d7ba22c0291121baabb0a9292eb8f271` @ `ceccc800d7ba`; as of 2026-11-05T21:30:02Z.

- records 2213, classes 2177, list rows 8746, year manifests 50, cells 3925
- Verified groups 0, engine vg groups 0, Likely groups 35
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.acurapartswarehouse.com, www.hondapartsnow.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.acurapartswarehouse.com: only 0% of its 2965 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)
- www.hondapartsnow.com: only 0% of its 5844 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 407 |
| ac-compressor | no_records | - | 2014 |
| ac-compressor | not_closed | no_year_manifest | 25177 |
| ac-compressor | not_closed | year_manifest_bad | 911 |
| alternator | unmapped | - | 407 |
| alternator | no_records | - | 2923 |
| alternator | not_closed | no_year_manifest | 24338 |
| alternator | not_closed | year_manifest_bad | 841 |
| bumper-front | unmapped | - | 407 |
| bumper-front | no_records | - | 7035 |
| bumper-front | not_closed | no_year_manifest | 20145 |
| bumper-front | not_closed | year_manifest_bad | 922 |
| bumper-rear | unmapped | - | 407 |
| bumper-rear | no_records | - | 5097 |
| bumper-rear | not_closed | no_year_manifest | 22083 |
| bumper-rear | not_closed | year_manifest_bad | 922 |
| climate-control | unmapped | - | 407 |
| climate-control | no_records | - | 10829 |
| climate-control | not_closed | no_year_manifest | 16673 |
| climate-control | not_closed | year_manifest_bad | 600 |
| door-front | unmapped | - | 407 |
| door-front | no_records | - | 2875 |
| door-front | not_closed | no_year_manifest | 24305 |
| door-front | not_closed | year_manifest_bad | 922 |
| door-rear | unmapped | - | 407 |
| door-rear | no_records | - | 5402 |
| door-rear | not_closed | no_year_manifest | 21866 |
| door-rear | not_closed | year_manifest_bad | 834 |
| fender | unmapped | - | 407 |
| fender | no_records | - | 20457 |
| fender | not_closed | no_year_manifest | 6725 |
| fender | not_closed | year_manifest_bad | 920 |
| fuel-pump-module | unmapped | - | 407 |
| fuel-pump-module | no_records | - | 5424 |
| fuel-pump-module | not_closed | no_year_manifest | 21790 |
| fuel-pump-module | not_closed | year_manifest_bad | 888 |
| gauge-cluster | unmapped | - | 407 |
| gauge-cluster | no_records | - | 18599 |
| gauge-cluster | not_closed | no_year_manifest | 8587 |
| gauge-cluster | not_closed | year_manifest_bad | 916 |
| grille | unmapped | - | 407 |
| grille | no_records | - | 22904 |
| grille | not_closed | no_year_manifest | 4453 |
| grille | not_closed | year_manifest_bad | 745 |
| headlights | unmapped | - | 407 |
| headlights | no_records | - | 6839 |
| headlights | not_closed | no_year_manifest | 20352 |
| headlights | not_closed | year_manifest_bad | 911 |
| hood | unmapped | - | 407 |
| hood | no_records | - | 5912 |
| hood | not_closed | no_year_manifest | 21268 |
| hood | not_closed | year_manifest_bad | 922 |
| ignition-coils | unmapped | - | 407 |
| ignition-coils | no_records | - | 3221 |
| ignition-coils | not_closed | no_year_manifest | 24158 |
| ignition-coils | not_closed | year_manifest_bad | 723 |
| liftgate | unmapped | - | 407 |
| liftgate | no_records | - | 22723 |
| liftgate | not_closed | no_year_manifest | 4957 |
| liftgate | not_closed | year_manifest_bad | 422 |
| power-steering-pump | unmapped | - | 407 |
| power-steering-pump | no_records | - | 5459 |
| power-steering-pump | not_closed | no_year_manifest | 22075 |
| power-steering-pump | not_closed | year_manifest_bad | 568 |
| radiator | unmapped | - | 407 |
| radiator | no_records | - | 3222 |
| radiator | not_closed | no_year_manifest | 23958 |
| radiator | not_closed | year_manifest_bad | 922 |
| side-mirrors | unmapped | - | 407 |
| side-mirrors | no_records | - | 3072 |
| side-mirrors | not_closed | no_year_manifest | 24123 |
| side-mirrors | not_closed | year_manifest_bad | 907 |
| starter | unmapped | - | 407 |
| starter | no_records | - | 2855 |
| starter | not_closed | no_year_manifest | 24414 |
| starter | not_closed | year_manifest_bad | 833 |
| tail-lights | unmapped | - | 407 |
| tail-lights | no_records | - | 7459 |
| tail-lights | not_closed | no_year_manifest | 19730 |
| tail-lights | not_closed | year_manifest_bad | 913 |
| tailgate | unmapped | - | 407 |
| tailgate | no_records | - | 27875 |
| tailgate | not_closed | no_year_manifest | 143 |
| tailgate | not_closed | year_manifest_bad | 84 |
| throttle-body | unmapped | - | 407 |
| throttle-body | no_records | - | 3415 |
| throttle-body | not_closed | no_year_manifest | 23797 |
| throttle-body | not_closed | year_manifest_bad | 890 |
| trunk-lid | unmapped | - | 407 |
| trunk-lid | no_records | - | 13592 |
| trunk-lid | not_closed | no_year_manifest | 14223 |
| trunk-lid | not_closed | year_manifest_bad | 287 |
| window-regulator | unmapped | - | 407 |
| window-regulator | no_records | - | 889 |
| window-regulator | not_closed | no_year_manifest | 26300 |
| window-regulator | not_closed | year_manifest_bad | 913 |
| window-switch | unmapped | - | 407 |
| window-switch | no_records | - | 5221 |
| window-switch | not_closed | no_year_manifest | 21974 |
| window-switch | not_closed | year_manifest_bad | 907 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 407 |
| ac-compressor | no_records | - | 2014 |
| ac-compressor | split | option_split | 9465 |
| ac-compressor | conditional | conditional:engine_unattested | 16623 |
| alternator | unmapped | - | 407 |
| alternator | no_records | - | 2923 |
| alternator | split | option_split | 12886 |
| alternator | conditional | conditional:engine_unattested | 12293 |
| bumper-front | unmapped | - | 407 |
| bumper-front | no_records | - | 7035 |
| bumper-front | split | no_candidates | 2 |
| bumper-front | split | option_split | 6424 |
| bumper-front | conditional | conditional:engine_unattested | 14641 |
| bumper-rear | unmapped | - | 407 |
| bumper-rear | no_records | - | 5097 |
| bumper-rear | split | option_split | 3801 |
| bumper-rear | conditional | conditional:engine_unattested | 19204 |
| climate-control | unmapped | - | 407 |
| climate-control | no_records | - | 10829 |
| climate-control | split | option_split | 11210 |
| climate-control | conditional | conditional:engine_unattested | 6063 |
| door-front | unmapped | - | 407 |
| door-front | no_records | - | 2875 |
| door-front | split | no_candidates | 25 |
| door-front | split | option_split | 5238 |
| door-front | split | position_missing | 318 |
| door-front | split | slot_missing | 167 |
| door-front | conditional | conditional:engine_unattested | 19479 |
| door-rear | unmapped | - | 407 |
| door-rear | no_records | - | 5402 |
| door-rear | split | no_candidates | 103 |
| door-rear | split | option_split | 5423 |
| door-rear | split | position_missing | 318 |
| door-rear | split | slot_missing | 630 |
| door-rear | conditional | conditional:engine_unattested | 16226 |
| fender | unmapped | - | 407 |
| fender | no_records | - | 20457 |
| fender | split | no_candidates | 801 |
| fender | conditional | conditional:engine_unattested | 6844 |
| fuel-pump-module | unmapped | - | 407 |
| fuel-pump-module | no_records | - | 5424 |
| fuel-pump-module | split | option_split | 12931 |
| fuel-pump-module | conditional | conditional:engine_unattested | 9747 |
| gauge-cluster | unmapped | - | 407 |
| gauge-cluster | no_records | - | 18599 |
| gauge-cluster | split | no_candidates | 286 |
| gauge-cluster | split | option_split | 5657 |
| gauge-cluster | conditional | conditional:engine_unattested | 3560 |
| grille | unmapped | - | 407 |
| grille | no_records | - | 22904 |
| grille | split | no_candidates | 510 |
| grille | split | option_split | 952 |
| grille | conditional | conditional:engine_unattested | 3736 |
| headlights | unmapped | - | 407 |
| headlights | no_records | - | 6839 |
| headlights | split | option_split | 3449 |
| headlights | conditional | conditional:engine_unattested | 17814 |
| hood | unmapped | - | 407 |
| hood | no_records | - | 5912 |
| hood | split | no_candidates | 78 |
| hood | split | option_split | 1772 |
| hood | conditional | conditional:engine_unattested | 20340 |
| ignition-coils | unmapped | - | 407 |
| ignition-coils | no_records | - | 3221 |
| ignition-coils | split | no_candidates | 68 |
| ignition-coils | split | option_split | 11883 |
| ignition-coils | conditional | conditional:engine_unattested | 10367 |
| ignition-coils | conditional | conditional:package | 2563 |
| liftgate | unmapped | - | 407 |
| liftgate | no_records | - | 22723 |
| liftgate | split | no_candidates | 2 |
| liftgate | split | option_split | 1282 |
| liftgate | conditional | conditional:engine_unattested | 4095 |
| power-steering-pump | unmapped | - | 407 |
| power-steering-pump | no_records | - | 5459 |
| power-steering-pump | split | option_split | 7724 |
| power-steering-pump | conditional | conditional:engine_unattested | 14919 |
| radiator | unmapped | - | 407 |
| radiator | no_records | - | 3222 |
| radiator | split | option_split | 13950 |
| radiator | conditional | conditional:engine_unattested | 10930 |
| side-mirrors | unmapped | - | 407 |
| side-mirrors | no_records | - | 3072 |
| side-mirrors | split | option_split | 23801 |
| side-mirrors | split | slot_missing | 319 |
| side-mirrors | conditional | conditional:engine_unattested | 910 |
| starter | unmapped | - | 407 |
| starter | no_records | - | 2855 |
| starter | split | option_split | 11869 |
| starter | conditional | conditional:engine_unattested | 13378 |
| tail-lights | unmapped | - | 407 |
| tail-lights | no_records | - | 7459 |
| tail-lights | split | option_split | 5416 |
| tail-lights | split | slot_missing | 610 |
| tail-lights | conditional | conditional:engine_unattested | 14617 |
| tailgate | unmapped | - | 407 |
| tailgate | no_records | - | 27875 |
| tailgate | conditional | conditional:engine_unattested | 227 |
| throttle-body | unmapped | - | 407 |
| throttle-body | no_records | - | 3415 |
| throttle-body | split | option_split | 14546 |
| throttle-body | conditional | conditional:engine_unattested | 10141 |
| trunk-lid | unmapped | - | 407 |
| trunk-lid | no_records | - | 13592 |
| trunk-lid | split | option_split | 6027 |
| trunk-lid | conditional | conditional:engine_unattested | 8405 |
| trunk-lid | conditional | conditional:model_other | 78 |
| window-regulator | unmapped | - | 407 |
| window-regulator | no_records | - | 889 |
| window-regulator | split | packaging_unstated | 27213 |
| window-switch | unmapped | - | 407 |
| window-switch | no_records | - | 5221 |
| window-switch | split | option_split | 13250 |
| window-switch | split | position_missing | 3421 |
| window-switch | conditional | conditional:engine_unattested | 6210 |

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

- Acura ILX: feed 'ILX' 71 cars
- Acura ILX Hybrid: feed 'ILX Hybrid' 0 cars
- Acura NSX: feed 'NSX' 0 cars
- Honda Fit EV: feed 'Fit EV' 0 cars
- Honda Passport: feed 'Passport' 87 cars
- Honda S2000: feed 'S2000' 0 cars
