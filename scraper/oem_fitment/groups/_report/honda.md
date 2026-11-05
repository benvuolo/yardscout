# OEM curation report: honda

Raw: `50ac4a48cdc62d02bd819bec33a67d0f07d8a71e` @ `50ac4a48cdc6`; as of 2026-11-05T07:44:33Z.

- records 1987, classes 1952, list rows 0, year manifests 0, cells 3393
- Verified groups 0, engine vg groups 0, Likely groups 29
- blocked sites: www.hondapartsnow.com

## Gates standing for the whole namespace

- no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close (C1/C2); Verified is impossible by design until the crawler writes them
- no (site, category) of this namespace has passed the audit gate (CATEGORY_STATUS has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.acurapartswarehouse.com, www.hondapartsnow.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.acurapartswarehouse.com: only 0% of its 2965 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)
- www.hondapartsnow.com: only 0% of its 4973 fitment rows can be coverage: it prints an option column, and option-layout rows are never coverage (spec 5.5)
- blocked by the crawl breaker: www.hondapartsnow.com (their cells never close, C9)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 408 |
| ac-compressor | no_records | - | 2012 |
| ac-compressor | not_closed | no_year_manifest | 26139 |
| alternator | unmapped | - | 408 |
| alternator | no_records | - | 2925 |
| alternator | not_closed | no_year_manifest | 25226 |
| bumper-front | unmapped | - | 408 |
| bumper-front | no_records | - | 9415 |
| bumper-front | not_closed | no_year_manifest | 18736 |
| bumper-rear | unmapped | - | 408 |
| bumper-rear | no_records | - | 7469 |
| bumper-rear | not_closed | no_year_manifest | 20682 |
| climate-control | unmapped | - | 408 |
| climate-control | no_records | - | 10837 |
| climate-control | not_closed | no_year_manifest | 17314 |
| door-front | unmapped | - | 408 |
| door-front | no_records | - | 4881 |
| door-front | not_closed | no_year_manifest | 23270 |
| door-rear | unmapped | - | 408 |
| door-rear | no_records | - | 6872 |
| door-rear | not_closed | no_year_manifest | 21279 |
| fender | unmapped | - | 408 |
| fender | no_records | - | 21594 |
| fender | not_closed | no_year_manifest | 6557 |
| fuel-pump-module | unmapped | - | 408 |
| fuel-pump-module | no_records | - | 5418 |
| fuel-pump-module | not_closed | no_year_manifest | 22733 |
| gauge-cluster | unmapped | - | 408 |
| gauge-cluster | no_records | - | 21043 |
| gauge-cluster | not_closed | no_year_manifest | 7108 |
| grille | unmapped | - | 408 |
| grille | no_records | - | 23989 |
| grille | not_closed | no_year_manifest | 4162 |
| headlights | unmapped | - | 408 |
| headlights | no_records | - | 6838 |
| headlights | not_closed | no_year_manifest | 21313 |
| hood | unmapped | - | 408 |
| hood | no_records | - | 8268 |
| hood | not_closed | no_year_manifest | 19883 |
| ignition-coils | unmapped | - | 408 |
| ignition-coils | no_records | - | 4319 |
| ignition-coils | not_closed | no_year_manifest | 23832 |
| liftgate | unmapped | - | 408 |
| liftgate | no_records | - | 23865 |
| liftgate | not_closed | no_year_manifest | 4286 |
| power-steering-pump | unmapped | - | 408 |
| power-steering-pump | no_records | - | 5479 |
| power-steering-pump | not_closed | no_year_manifest | 22672 |
| radiator | unmapped | - | 408 |
| radiator | no_records | - | 5220 |
| radiator | not_closed | no_year_manifest | 22931 |
| side-mirrors | unmapped | - | 408 |
| side-mirrors | no_records | - | 3075 |
| side-mirrors | not_closed | no_year_manifest | 25076 |
| starter | unmapped | - | 408 |
| starter | no_records | - | 2859 |
| starter | not_closed | no_year_manifest | 25292 |
| tail-lights | unmapped | - | 408 |
| tail-lights | no_records | - | 7456 |
| tail-lights | not_closed | no_year_manifest | 20695 |
| throttle-body | unmapped | - | 408 |
| throttle-body | no_records | - | 3419 |
| throttle-body | not_closed | no_year_manifest | 24732 |
| trunk-lid | unmapped | - | 408 |
| trunk-lid | no_records | - | 14258 |
| trunk-lid | not_closed | no_year_manifest | 13893 |
| window-regulator | unmapped | - | 408 |
| window-regulator | no_records | - | 890 |
| window-regulator | not_closed | no_year_manifest | 27261 |
| window-switch | unmapped | - | 408 |
| window-switch | no_records | - | 5223 |
| window-switch | not_closed | no_year_manifest | 22928 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 408 |
| ac-compressor | no_records | - | 2012 |
| ac-compressor | split | option_split | 9490 |
| ac-compressor | conditional | conditional:notes_not_own_page | 12428 |
| ac-compressor | conditional | conditional:option_layout | 4221 |
| alternator | unmapped | - | 408 |
| alternator | no_records | - | 2925 |
| alternator | split | option_split | 12914 |
| alternator | conditional | conditional:notes_not_own_page | 9093 |
| alternator | conditional | conditional:option_layout | 3219 |
| bumper-front | unmapped | - | 408 |
| bumper-front | no_records | - | 9415 |
| bumper-front | split | option_split | 3431 |
| bumper-front | conditional | conditional:notes_not_own_page | 9018 |
| bumper-front | conditional | conditional:option_layout | 6287 |
| bumper-rear | unmapped | - | 408 |
| bumper-rear | no_records | - | 7469 |
| bumper-rear | split | option_split | 2375 |
| bumper-rear | conditional | conditional:notes_not_own_page | 11842 |
| bumper-rear | conditional | conditional:option_layout | 6465 |
| climate-control | unmapped | - | 408 |
| climate-control | no_records | - | 10837 |
| climate-control | split | option_split | 11237 |
| climate-control | conditional | conditional:notes_not_own_page | 4683 |
| climate-control | conditional | conditional:option_layout | 1394 |
| door-front | unmapped | - | 408 |
| door-front | no_records | - | 4881 |
| door-front | split | option_split | 5051 |
| door-front | split | position_missing | 321 |
| door-front | split | slot_missing | 25 |
| door-front | conditional | conditional:notes_not_own_page | 12086 |
| door-front | conditional | conditional:option_layout | 5787 |
| door-rear | unmapped | - | 408 |
| door-rear | no_records | - | 6872 |
| door-rear | split | option_split | 5094 |
| door-rear | split | position_missing | 321 |
| door-rear | split | slot_missing | 334 |
| door-rear | conditional | conditional:listed_not_fitted | 150 |
| door-rear | conditional | conditional:notes_not_own_page | 11155 |
| door-rear | conditional | conditional:option_layout | 4225 |
| fender | unmapped | - | 408 |
| fender | no_records | - | 21594 |
| fender | conditional | conditional:notes_not_own_page | 4912 |
| fender | conditional | conditional:option_layout | 1645 |
| fuel-pump-module | unmapped | - | 408 |
| fuel-pump-module | no_records | - | 5418 |
| fuel-pump-module | split | option_split | 12960 |
| fuel-pump-module | conditional | conditional:notes_not_own_page | 6683 |
| fuel-pump-module | conditional | conditional:option_layout | 3090 |
| gauge-cluster | unmapped | - | 408 |
| gauge-cluster | no_records | - | 21043 |
| gauge-cluster | split | option_split | 4728 |
| gauge-cluster | conditional | conditional:notes_not_own_page | 1157 |
| gauge-cluster | conditional | conditional:option_layout | 1223 |
| grille | unmapped | - | 408 |
| grille | no_records | - | 23989 |
| grille | split | option_split | 608 |
| grille | conditional | conditional:notes_not_own_page | 2029 |
| grille | conditional | conditional:option_layout | 1525 |
| headlights | unmapped | - | 408 |
| headlights | no_records | - | 6838 |
| headlights | split | option_split | 3466 |
| headlights | conditional | conditional:notes_not_own_page | 11188 |
| headlights | conditional | conditional:option_layout | 6659 |
| hood | unmapped | - | 408 |
| hood | no_records | - | 8268 |
| hood | split | option_split | 1772 |
| hood | conditional | conditional:notes_not_own_page | 12528 |
| hood | conditional | conditional:option_layout | 5583 |
| ignition-coils | unmapped | - | 408 |
| ignition-coils | no_records | - | 4319 |
| ignition-coils | split | option_split | 11544 |
| ignition-coils | conditional | conditional:notes_not_own_page | 10142 |
| ignition-coils | conditional | conditional:option_layout | 2146 |
| liftgate | unmapped | - | 408 |
| liftgate | no_records | - | 23865 |
| liftgate | split | option_split | 1020 |
| liftgate | conditional | conditional:notes_not_own_page | 2061 |
| liftgate | conditional | conditional:option_layout | 1205 |
| power-steering-pump | unmapped | - | 408 |
| power-steering-pump | no_records | - | 5479 |
| power-steering-pump | split | option_split | 7734 |
| power-steering-pump | conditional | conditional:notes_not_own_page | 10725 |
| power-steering-pump | conditional | conditional:option_layout | 4213 |
| radiator | unmapped | - | 408 |
| radiator | no_records | - | 5220 |
| radiator | split | option_split | 11774 |
| radiator | conditional | conditional:notes_not_own_page | 8177 |
| radiator | conditional | conditional:option_layout | 2980 |
| side-mirrors | unmapped | - | 408 |
| side-mirrors | no_records | - | 3075 |
| side-mirrors | split | option_split | 23842 |
| side-mirrors | split | slot_missing | 323 |
| side-mirrors | conditional | conditional:notes_not_own_page | 911 |
| starter | unmapped | - | 408 |
| starter | no_records | - | 2859 |
| starter | split | option_split | 11889 |
| starter | conditional | conditional:notes_not_own_page | 10040 |
| starter | conditional | conditional:option_layout | 3363 |
| tail-lights | unmapped | - | 408 |
| tail-lights | no_records | - | 7456 |
| tail-lights | split | option_split | 5434 |
| tail-lights | split | slot_missing | 608 |
| tail-lights | conditional | conditional:notes_not_own_page | 8556 |
| tail-lights | conditional | conditional:option_layout | 6097 |
| throttle-body | unmapped | - | 408 |
| throttle-body | no_records | - | 3419 |
| throttle-body | split | option_split | 14573 |
| throttle-body | conditional | conditional:notes_not_own_page | 8255 |
| throttle-body | conditional | conditional:option_layout | 1904 |
| trunk-lid | unmapped | - | 408 |
| trunk-lid | no_records | - | 14258 |
| trunk-lid | split | option_split | 4775 |
| trunk-lid | conditional | conditional:notes_not_own_page | 6185 |
| trunk-lid | conditional | conditional:option_layout | 2933 |
| window-regulator | unmapped | - | 408 |
| window-regulator | no_records | - | 890 |
| window-regulator | split | packaging_unstated | 27261 |
| window-switch | unmapped | - | 408 |
| window-switch | no_records | - | 5223 |
| window-switch | split | option_split | 13281 |
| window-switch | split | position_missing | 3434 |
| window-switch | conditional | conditional:notes_not_own_page | 3791 |
| window-switch | conditional | conditional:option_layout | 2422 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- disputed_class: 35
- rule_drift: 7

## Unknown note clauses (top 30)

- `Fit Note: Mfg.Origin: JPN`: 116
- `Fit Note: Mfg.Origin: USA`: 70
- `CN2`: 30
- `Interior Color: A-BLACK`: 23
- `CN1`: 22
- `F-IVORY`: 20
- `CAN`: 19
- `Package Quantity: 1`: 18
- `USA`: 15
- `Require Quantity: 6`: 11
- `B-GRAY`: 10
- `CN4`: 9
- `Fit Note: Mfg.Origin: CN1`: 9
- `Interior Color: B-GRAY`: 9
- `CN3`: 8
- `Fit Note: Mfg.Origin: GBR`: 8
- `Require Quantity: 4`: 7
- `Interior Color: A-BLACK/GRAY`: 6
- `MEX`: 6
- `D-BLACK`: 5
- `C-BLUE`: 4
- `F-BEIGE`: 4
- `B-GRAY/BLUE`: 3
- `C-GRAY/GREEN`: 3
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
- Honda S2000: feed 'S2000' 0 cars
