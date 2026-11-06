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
| ac-compressor | unmapped | - | 401 |
| ac-compressor | no_records | - | 2027 |
| ac-compressor | not_closed | no_year_manifest | 25256 |
| ac-compressor | not_closed | year_manifest_bad | 911 |
| alternator | unmapped | - | 401 |
| alternator | no_records | - | 2931 |
| alternator | not_closed | no_year_manifest | 24421 |
| alternator | not_closed | year_manifest_bad | 842 |
| bumper-front | unmapped | - | 401 |
| bumper-front | no_records | - | 7072 |
| bumper-front | not_closed | no_year_manifest | 20200 |
| bumper-front | not_closed | year_manifest_bad | 922 |
| bumper-rear | unmapped | - | 401 |
| bumper-rear | no_records | - | 5117 |
| bumper-rear | not_closed | no_year_manifest | 22155 |
| bumper-rear | not_closed | year_manifest_bad | 922 |
| climate-control | unmapped | - | 401 |
| climate-control | no_records | - | 10879 |
| climate-control | not_closed | no_year_manifest | 16717 |
| climate-control | not_closed | year_manifest_bad | 598 |
| door-front | unmapped | - | 401 |
| door-front | no_records | - | 2889 |
| door-front | not_closed | no_year_manifest | 24383 |
| door-front | not_closed | year_manifest_bad | 922 |
| door-rear | unmapped | - | 401 |
| door-rear | no_records | - | 5429 |
| door-rear | not_closed | no_year_manifest | 21929 |
| door-rear | not_closed | year_manifest_bad | 836 |
| fender | unmapped | - | 401 |
| fender | no_records | - | 20537 |
| fender | not_closed | no_year_manifest | 6737 |
| fender | not_closed | year_manifest_bad | 920 |
| fuel-pump-module | unmapped | - | 401 |
| fuel-pump-module | no_records | - | 5449 |
| fuel-pump-module | not_closed | no_year_manifest | 21857 |
| fuel-pump-module | not_closed | year_manifest_bad | 888 |
| gauge-cluster | unmapped | - | 401 |
| gauge-cluster | no_records | - | 18671 |
| gauge-cluster | not_closed | no_year_manifest | 8607 |
| gauge-cluster | not_closed | year_manifest_bad | 916 |
| grille | unmapped | - | 401 |
| grille | no_records | - | 22980 |
| grille | not_closed | no_year_manifest | 4468 |
| grille | not_closed | year_manifest_bad | 746 |
| headlights | unmapped | - | 401 |
| headlights | no_records | - | 6885 |
| headlights | not_closed | no_year_manifest | 20398 |
| headlights | not_closed | year_manifest_bad | 911 |
| hood | unmapped | - | 401 |
| hood | no_records | - | 5941 |
| hood | not_closed | no_year_manifest | 21331 |
| hood | not_closed | year_manifest_bad | 922 |
| ignition-coils | unmapped | - | 401 |
| ignition-coils | no_records | - | 3236 |
| ignition-coils | not_closed | no_year_manifest | 24236 |
| ignition-coils | not_closed | year_manifest_bad | 722 |
| liftgate | unmapped | - | 401 |
| liftgate | no_records | - | 22807 |
| liftgate | not_closed | no_year_manifest | 4969 |
| liftgate | not_closed | year_manifest_bad | 418 |
| power-steering-pump | unmapped | - | 401 |
| power-steering-pump | no_records | - | 5479 |
| power-steering-pump | not_closed | no_year_manifest | 22147 |
| power-steering-pump | not_closed | year_manifest_bad | 568 |
| radiator | unmapped | - | 401 |
| radiator | no_records | - | 3236 |
| radiator | not_closed | no_year_manifest | 24036 |
| radiator | not_closed | year_manifest_bad | 922 |
| side-mirrors | unmapped | - | 401 |
| side-mirrors | no_records | - | 3084 |
| side-mirrors | not_closed | no_year_manifest | 24203 |
| side-mirrors | not_closed | year_manifest_bad | 907 |
| starter | unmapped | - | 401 |
| starter | no_records | - | 2877 |
| starter | not_closed | no_year_manifest | 24484 |
| starter | not_closed | year_manifest_bad | 833 |
| tail-lights | unmapped | - | 401 |
| tail-lights | no_records | - | 7505 |
| tail-lights | not_closed | no_year_manifest | 19776 |
| tail-lights | not_closed | year_manifest_bad | 913 |
| tailgate | unmapped | - | 401 |
| tailgate | no_records | - | 27966 |
| tailgate | not_closed | no_year_manifest | 142 |
| tailgate | not_closed | year_manifest_bad | 86 |
| throttle-body | unmapped | - | 401 |
| throttle-body | no_records | - | 3428 |
| throttle-body | not_closed | no_year_manifest | 23877 |
| throttle-body | not_closed | year_manifest_bad | 889 |
| trunk-lid | unmapped | - | 401 |
| trunk-lid | no_records | - | 13632 |
| trunk-lid | not_closed | no_year_manifest | 14274 |
| trunk-lid | not_closed | year_manifest_bad | 288 |
| window-regulator | unmapped | - | 401 |
| window-regulator | no_records | - | 893 |
| window-regulator | not_closed | no_year_manifest | 26388 |
| window-regulator | not_closed | year_manifest_bad | 913 |
| window-switch | unmapped | - | 401 |
| window-switch | no_records | - | 5255 |
| window-switch | not_closed | no_year_manifest | 22032 |
| window-switch | not_closed | year_manifest_bad | 907 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 401 |
| ac-compressor | no_records | - | 2027 |
| ac-compressor | split | option_split | 9494 |
| ac-compressor | conditional | conditional:engine_unattested | 16673 |
| alternator | unmapped | - | 401 |
| alternator | no_records | - | 2931 |
| alternator | split | option_split | 12925 |
| alternator | conditional | conditional:engine_unattested | 12338 |
| bumper-front | unmapped | - | 401 |
| bumper-front | no_records | - | 7072 |
| bumper-front | split | no_candidates | 2 |
| bumper-front | split | option_split | 6439 |
| bumper-front | conditional | conditional:engine_unattested | 14681 |
| bumper-rear | unmapped | - | 401 |
| bumper-rear | no_records | - | 5117 |
| bumper-rear | split | option_split | 3805 |
| bumper-rear | conditional | conditional:engine_unattested | 19272 |
| climate-control | unmapped | - | 401 |
| climate-control | no_records | - | 10879 |
| climate-control | split | option_split | 11227 |
| climate-control | conditional | conditional:engine_unattested | 6088 |
| door-front | unmapped | - | 401 |
| door-front | no_records | - | 2889 |
| door-front | split | no_candidates | 25 |
| door-front | split | option_split | 5255 |
| door-front | split | position_missing | 320 |
| door-front | split | slot_missing | 166 |
| door-front | conditional | conditional:engine_unattested | 19539 |
| door-rear | unmapped | - | 401 |
| door-rear | no_records | - | 5429 |
| door-rear | split | no_candidates | 103 |
| door-rear | split | option_split | 5434 |
| door-rear | split | position_missing | 320 |
| door-rear | split | slot_missing | 628 |
| door-rear | conditional | conditional:engine_unattested | 16280 |
| fender | unmapped | - | 401 |
| fender | no_records | - | 20537 |
| fender | split | no_candidates | 802 |
| fender | conditional | conditional:engine_unattested | 6855 |
| fuel-pump-module | unmapped | - | 401 |
| fuel-pump-module | no_records | - | 5449 |
| fuel-pump-module | split | option_split | 12971 |
| fuel-pump-module | conditional | conditional:engine_unattested | 9774 |
| gauge-cluster | unmapped | - | 401 |
| gauge-cluster | no_records | - | 18671 |
| gauge-cluster | split | no_candidates | 287 |
| gauge-cluster | split | option_split | 5669 |
| gauge-cluster | conditional | conditional:engine_unattested | 3567 |
| grille | unmapped | - | 401 |
| grille | no_records | - | 22980 |
| grille | split | no_candidates | 509 |
| grille | split | option_split | 956 |
| grille | conditional | conditional:engine_unattested | 3749 |
| headlights | unmapped | - | 401 |
| headlights | no_records | - | 6885 |
| headlights | split | option_split | 3459 |
| headlights | conditional | conditional:engine_unattested | 17850 |
| hood | unmapped | - | 401 |
| hood | no_records | - | 5941 |
| hood | split | no_candidates | 78 |
| hood | split | option_split | 1772 |
| hood | conditional | conditional:engine_unattested | 20403 |
| ignition-coils | unmapped | - | 401 |
| ignition-coils | no_records | - | 3236 |
| ignition-coils | split | no_candidates | 67 |
| ignition-coils | split | option_split | 11932 |
| ignition-coils | conditional | conditional:engine_unattested | 10395 |
| ignition-coils | conditional | conditional:package | 2564 |
| liftgate | unmapped | - | 401 |
| liftgate | no_records | - | 22807 |
| liftgate | split | no_candidates | 2 |
| liftgate | split | option_split | 1286 |
| liftgate | conditional | conditional:engine_unattested | 4099 |
| power-steering-pump | unmapped | - | 401 |
| power-steering-pump | no_records | - | 5479 |
| power-steering-pump | split | option_split | 7746 |
| power-steering-pump | conditional | conditional:engine_unattested | 14969 |
| radiator | unmapped | - | 401 |
| radiator | no_records | - | 3236 |
| radiator | split | option_split | 14006 |
| radiator | conditional | conditional:engine_unattested | 10952 |
| side-mirrors | unmapped | - | 401 |
| side-mirrors | no_records | - | 3084 |
| side-mirrors | split | option_split | 23869 |
| side-mirrors | split | slot_missing | 317 |
| side-mirrors | conditional | conditional:engine_unattested | 924 |
| starter | unmapped | - | 401 |
| starter | no_records | - | 2877 |
| starter | split | option_split | 11913 |
| starter | conditional | conditional:engine_unattested | 13404 |
| tail-lights | unmapped | - | 401 |
| tail-lights | no_records | - | 7505 |
| tail-lights | split | option_split | 5433 |
| tail-lights | split | slot_missing | 611 |
| tail-lights | conditional | conditional:engine_unattested | 14645 |
| tailgate | unmapped | - | 401 |
| tailgate | no_records | - | 27966 |
| tailgate | conditional | conditional:engine_unattested | 228 |
| throttle-body | unmapped | - | 401 |
| throttle-body | no_records | - | 3428 |
| throttle-body | split | option_split | 14596 |
| throttle-body | conditional | conditional:engine_unattested | 10170 |
| trunk-lid | unmapped | - | 401 |
| trunk-lid | no_records | - | 13632 |
| trunk-lid | split | option_split | 6054 |
| trunk-lid | conditional | conditional:engine_unattested | 8430 |
| trunk-lid | conditional | conditional:model_other | 78 |
| window-regulator | unmapped | - | 401 |
| window-regulator | no_records | - | 893 |
| window-regulator | split | packaging_unstated | 27301 |
| window-switch | unmapped | - | 401 |
| window-switch | no_records | - | 5255 |
| window-switch | split | option_split | 13282 |
| window-switch | split | position_missing | 3441 |
| window-switch | conditional | conditional:engine_unattested | 6216 |

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
- Honda Passport: feed 'Passport' 82 cars
- Honda S2000: feed 'S2000' 0 cars
