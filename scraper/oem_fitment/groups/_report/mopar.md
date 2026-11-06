# OEM curation report: mopar

Raw: `42683f9d86450b6bd00eb7fc7cc9640154607768` @ `42683f9d8645`; as of 2026-11-06T07:21:04Z.

- records 4533, classes 4034, list rows 29436, year manifests 104, cells 6496
- Verified groups 0, engine vg groups 0, Likely groups 150
- blocked sites: none

## Gates standing for the whole namespace

- no (site, category) of this namespace has passed the audit gate (audits.json has no record; spec 11.4, E5/V7)
- engine cells not audited as reliable on www.moparpartsgiant.com: every engine test there is maybe (spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks engine categories; the completion worklist cannot rank their cells until an audit flips ENGINE_CELLS_RELIABLE
- www.moparpartsgiant.com: only 2% of its 4357 fitment rows can be coverage: its option column holds trims (option_column_is_trims), which count only after a namespace audit (spec 5.2)

## Funnel (lot cars per category, first open reason)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2344 |
| ac-compressor | no_records | - | 8256 |
| ac-compressor | not_closed | no_year_manifest | 25788 |
| ac-compressor | not_closed | stale | 24 |
| ac-compressor | not_closed | suspect_variant | 306 |
| ac-compressor | not_closed | uncrawled_chain_member | 2336 |
| ac-compressor | not_closed | unverified_product | 4960 |
| ac-compressor | split | no_candidates | 49 |
| alternator | unmapped | - | 2344 |
| alternator | no_records | - | 3292 |
| alternator | not_closed | no_list_manifest | 24 |
| alternator | not_closed | no_year_manifest | 30752 |
| alternator | not_closed | suspect_variant | 857 |
| alternator | not_closed | unattested | 27 |
| alternator | not_closed | uncrawled_chain_member | 140 |
| alternator | not_closed | unverified_product | 6627 |
| bumper-front | unmapped | - | 2344 |
| bumper-front | no_records | - | 35027 |
| bumper-front | not_closed | no_year_manifest | 6692 |
| bumper-rear | unmapped | - | 2344 |
| bumper-rear | no_records | - | 33036 |
| bumper-rear | not_closed | no_year_manifest | 8683 |
| climate-control | unmapped | - | 2344 |
| climate-control | no_records | - | 14883 |
| climate-control | not_closed | no_list_manifest | 629 |
| climate-control | not_closed | no_year_manifest | 20173 |
| climate-control | not_closed | unread_sibling_page | 6034 |
| door-front | unmapped | - | 2344 |
| door-front | no_records | - | 33943 |
| door-front | not_closed | no_year_manifest | 7776 |
| door-rear | unmapped | - | 2344 |
| door-rear | no_records | - | 33526 |
| door-rear | not_closed | no_year_manifest | 8193 |
| fender | unmapped | - | 2344 |
| fender | no_records | - | 33895 |
| fender | not_closed | no_year_manifest | 7824 |
| fuel-pump-module | unmapped | - | 2344 |
| fuel-pump-module | no_records | - | 6405 |
| fuel-pump-module | not_closed | no_year_manifest | 27639 |
| fuel-pump-module | not_closed | unread_sibling_page | 7675 |
| gauge-cluster | unmapped | - | 2344 |
| gauge-cluster | no_records | - | 39431 |
| gauge-cluster | not_closed | no_year_manifest | 2288 |
| grille | unmapped | - | 2344 |
| grille | no_records | - | 36334 |
| grille | not_closed | no_year_manifest | 5385 |
| headlights | unmapped | - | 2344 |
| headlights | no_records | - | 8843 |
| headlights | not_closed | no_year_manifest | 25228 |
| headlights | not_closed | uncrawled_chain_member | 32 |
| headlights | not_closed | unread_sibling_page | 7476 |
| headlights | split | no_candidates | 140 |
| hood | unmapped | - | 2344 |
| hood | no_records | - | 33563 |
| hood | not_closed | no_year_manifest | 8156 |
| ignition-coils | unmapped | - | 2344 |
| ignition-coils | no_records | - | 5040 |
| ignition-coils | not_closed | no_list_manifest | 6635 |
| ignition-coils | not_closed | no_year_manifest | 30044 |
| liftgate | unmapped | - | 2344 |
| liftgate | no_records | - | 34893 |
| liftgate | not_closed | no_year_manifest | 6826 |
| power-steering-pump | unmapped | - | 2344 |
| power-steering-pump | no_records | - | 6302 |
| power-steering-pump | not_closed | no_list_manifest | 224 |
| power-steering-pump | not_closed | no_year_manifest | 28786 |
| power-steering-pump | not_closed | unread_sibling_page | 6407 |
| radiator | unmapped | - | 2344 |
| radiator | no_records | - | 26632 |
| radiator | not_closed | no_list_manifest | 1755 |
| radiator | not_closed | no_year_manifest | 13332 |
| side-mirrors | unmapped | - | 2344 |
| side-mirrors | no_records | - | 5057 |
| side-mirrors | not_closed | no_list_manifest | 277 |
| side-mirrors | not_closed | no_year_manifest | 29235 |
| side-mirrors | not_closed | unattested | 27 |
| side-mirrors | not_closed | unread_sibling_page | 5161 |
| side-mirrors | not_closed | unverified_product | 1905 |
| side-mirrors | split | no_candidates | 47 |
| side-mirrors | split | position_conflict | 2 |
| side-mirrors | conditional | conditional:option | 8 |
| starter | unmapped | - | 2344 |
| starter | no_records | - | 2915 |
| starter | not_closed | no_list_manifest | 18 |
| starter | not_closed | no_year_manifest | 31131 |
| starter | not_closed | stale | 24 |
| starter | not_closed | suspect_variant | 440 |
| starter | not_closed | uncrawled_chain_member | 152 |
| starter | not_closed | unverified_product | 7039 |
| tail-lights | unmapped | - | 2344 |
| tail-lights | no_records | - | 12790 |
| tail-lights | not_closed | no_list_manifest | 27 |
| tail-lights | not_closed | no_year_manifest | 21254 |
| tail-lights | not_closed | stale | 24 |
| tail-lights | not_closed | suspect_variant | 111 |
| tail-lights | not_closed | uncrawled_chain_member | 1377 |
| tail-lights | not_closed | unverified_product | 3721 |
| tail-lights | split | no_candidates | 86 |
| tail-lights | split | option_split | 596 |
| tail-lights | conditional | conditional:body | 201 |
| tail-lights | conditional | conditional:option_layout | 140 |
| tail-lights | conditional | conditional:trim | 1392 |
| throttle-body | unmapped | - | 2344 |
| throttle-body | no_records | - | 3413 |
| throttle-body | not_closed | no_list_manifest | 152 |
| throttle-body | not_closed | no_year_manifest | 30657 |
| throttle-body | not_closed | suspect_variant | 278 |
| throttle-body | not_closed | unverified_product | 5597 |
| throttle-body | split | option_split | 1122 |
| throttle-body | conditional | conditional:fitted_not_listed | 167 |
| throttle-body | chain_member_conditional | chain_member_conditional | 333 |
| tow-mirrors | unmapped | - | 2344 |
| tow-mirrors | no_records | - | 39179 |
| tow-mirrors | not_closed | no_list_manifest | 476 |
| tow-mirrors | not_closed | no_year_manifest | 2064 |
| window-regulator | unmapped | - | 2344 |
| window-regulator | no_records | - | 4088 |
| window-regulator | not_closed | no_list_manifest | 369 |
| window-regulator | not_closed | no_year_manifest | 30199 |
| window-regulator | not_closed | stale | 24 |
| window-regulator | not_closed | uncrawled_chain_member | 945 |
| window-regulator | not_closed | unread_sibling_page | 2736 |
| window-regulator | not_closed | unverified_product | 2347 |
| window-regulator | split | no_candidates | 47 |
| window-regulator | split | packaging_unstated | 964 |
| window-switch | unmapped | - | 2344 |
| window-switch | no_records | - | 13355 |
| window-switch | not_closed | no_year_manifest | 20716 |
| window-switch | not_closed | stale | 24 |
| window-switch | not_closed | unread_sibling_page | 7624 |

## Hypothetical funnel (closure assumed; never shipped)

| category | stage | reason | cars |
|---|---|---|---|
| ac-compressor | unmapped | - | 2344 |
| ac-compressor | no_records | - | 8256 |
| ac-compressor | split | no_candidates | 100 |
| ac-compressor | split | option_split | 28490 |
| ac-compressor | conditional | conditional:engine | 42 |
| ac-compressor | conditional | conditional:engine_unattested | 56 |
| ac-compressor | conditional | conditional:engine_unparsed | 25 |
| ac-compressor | conditional | conditional:notes_not_own_page | 2205 |
| ac-compressor | conditional | conditional:trim | 2545 |
| alternator | unmapped | - | 2344 |
| alternator | no_records | - | 3292 |
| alternator | split | option_split | 33649 |
| alternator | conditional | conditional:engine | 1550 |
| alternator | conditional | conditional:engine_unattested | 94 |
| alternator | conditional | conditional:engine_unparsed | 3 |
| alternator | conditional | conditional:notes_not_own_page | 511 |
| alternator | conditional | conditional:option | 188 |
| alternator | conditional | conditional:trim | 2432 |
| bumper-front | unmapped | - | 2344 |
| bumper-front | no_records | - | 35027 |
| bumper-front | split | option_split | 6164 |
| bumper-front | conditional | conditional:notes_not_own_page | 62 |
| bumper-front | conditional | conditional:trim | 466 |
| bumper-rear | unmapped | - | 2344 |
| bumper-rear | no_records | - | 33036 |
| bumper-rear | split | option_split | 7609 |
| bumper-rear | conditional | conditional:notes_not_own_page | 656 |
| bumper-rear | conditional | conditional:trim | 418 |
| climate-control | unmapped | - | 2344 |
| climate-control | no_records | - | 14883 |
| climate-control | split | no_candidates | 83 |
| climate-control | split | option_split | 20914 |
| climate-control | conditional | conditional:engine_unattested | 313 |
| climate-control | conditional | conditional:engine_unparsed | 17 |
| climate-control | conditional | conditional:notes_not_own_page | 1947 |
| climate-control | conditional | conditional:option | 8 |
| climate-control | conditional | conditional:option_layout | 167 |
| climate-control | conditional | conditional:trim | 3387 |
| door-front | unmapped | - | 2344 |
| door-front | no_records | - | 33943 |
| door-front | split | option_split | 1859 |
| door-front | conditional | conditional:notes_not_own_page | 867 |
| door-front | conditional | conditional:production | 47 |
| door-front | conditional | conditional:trim | 4658 |
| door-front | eligible | - | 345 |
| door-rear | unmapped | - | 2344 |
| door-rear | no_records | - | 33526 |
| door-rear | split | option_split | 1568 |
| door-rear | conditional | conditional:notes_not_own_page | 1960 |
| door-rear | conditional | conditional:trim | 3617 |
| door-rear | eligible | - | 1048 |
| fender | unmapped | - | 2344 |
| fender | no_records | - | 33895 |
| fender | split | option_split | 2562 |
| fender | conditional | conditional:notes_not_own_page | 1035 |
| fender | conditional | conditional:trim | 3589 |
| fender | chain_member_conditional | chain_member_conditional | 265 |
| fender | eligible | - | 373 |
| fuel-pump-module | unmapped | - | 2344 |
| fuel-pump-module | no_records | - | 6405 |
| fuel-pump-module | split | no_candidates | 201 |
| fuel-pump-module | split | option_split | 26744 |
| fuel-pump-module | conditional | conditional:engine | 39 |
| fuel-pump-module | conditional | conditional:engine_unattested | 29 |
| fuel-pump-module | conditional | conditional:fuel | 54 |
| fuel-pump-module | conditional | conditional:notes_not_own_page | 3338 |
| fuel-pump-module | conditional | conditional:option | 76 |
| fuel-pump-module | conditional | conditional:trim | 4833 |
| gauge-cluster | unmapped | - | 2344 |
| gauge-cluster | no_records | - | 39431 |
| gauge-cluster | split | option_split | 1985 |
| gauge-cluster | conditional | conditional:trim | 303 |
| grille | unmapped | - | 2344 |
| grille | no_records | - | 36334 |
| grille | split | option_split | 3840 |
| grille | conditional | conditional:notes_not_own_page | 1054 |
| grille | conditional | conditional:trim | 262 |
| grille | eligible | - | 229 |
| headlights | unmapped | - | 2344 |
| headlights | no_records | - | 8843 |
| headlights | split | no_candidates | 350 |
| headlights | split | option_split | 24677 |
| headlights | split | position_missing | 494 |
| headlights | split | slot_missing | 117 |
| headlights | conditional | conditional:engine | 263 |
| headlights | conditional | conditional:notes_not_own_page | 1846 |
| headlights | conditional | conditional:option | 198 |
| headlights | conditional | conditional:option_layout | 84 |
| headlights | conditional | conditional:trim | 4142 |
| headlights | conditional | conditional:unknown | 265 |
| headlights | chain_member_conditional | chain_member_conditional | 211 |
| headlights | eligible | - | 229 |
| hood | unmapped | - | 2344 |
| hood | no_records | - | 33563 |
| hood | split | option_split | 551 |
| hood | conditional | conditional:notes_not_own_page | 1869 |
| hood | conditional | conditional:trim | 5252 |
| hood | chain_member_conditional | chain_member_conditional | 162 |
| hood | eligible | - | 322 |
| ignition-coils | unmapped | - | 2344 |
| ignition-coils | no_records | - | 5040 |
| ignition-coils | split | option_split | 17604 |
| ignition-coils | conditional | conditional:engine | 3016 |
| ignition-coils | conditional | conditional:engine_unattested | 454 |
| ignition-coils | conditional | conditional:engine_unparsed | 28 |
| ignition-coils | conditional | conditional:notes_not_own_page | 6235 |
| ignition-coils | conditional | conditional:trim | 9113 |
| ignition-coils | eligible | - | 229 |
| liftgate | unmapped | - | 2344 |
| liftgate | no_records | - | 34893 |
| liftgate | split | option_split | 503 |
| liftgate | conditional | conditional:notes_not_own_page | 2806 |
| liftgate | conditional | conditional:trim | 2915 |
| liftgate | eligible | - | 602 |
| power-steering-pump | unmapped | - | 2344 |
| power-steering-pump | no_records | - | 6302 |
| power-steering-pump | split | no_candidates | 144 |
| power-steering-pump | split | option_split | 28562 |
| power-steering-pump | conditional | conditional:engine | 50 |
| power-steering-pump | conditional | conditional:engine_unattested | 302 |
| power-steering-pump | conditional | conditional:notes_not_own_page | 4176 |
| power-steering-pump | conditional | conditional:qualifier | 668 |
| power-steering-pump | conditional | conditional:trim | 1139 |
| power-steering-pump | conditional | conditional:unknown | 344 |
| power-steering-pump | reman_only | reman_only | 32 |
| radiator | unmapped | - | 2344 |
| radiator | no_records | - | 26632 |
| radiator | split | option_split | 10057 |
| radiator | conditional | conditional:engine | 80 |
| radiator | conditional | conditional:notes_not_own_page | 2312 |
| radiator | conditional | conditional:trim | 2638 |
| side-mirrors | unmapped | - | 2344 |
| side-mirrors | no_records | - | 5057 |
| side-mirrors | split | no_candidates | 74 |
| side-mirrors | split | option_split | 35144 |
| side-mirrors | split | position_conflict | 2 |
| side-mirrors | split | position_missing | 172 |
| side-mirrors | split | slot_missing | 501 |
| side-mirrors | conditional | conditional:notes_not_own_page | 62 |
| side-mirrors | conditional | conditional:option | 8 |
| side-mirrors | conditional | conditional:trim | 699 |
| starter | unmapped | - | 2344 |
| starter | no_records | - | 2915 |
| starter | split | no_candidates | 140 |
| starter | split | option_split | 35218 |
| starter | conditional | conditional:engine | 605 |
| starter | conditional | conditional:engine_unattested | 511 |
| starter | conditional | conditional:engine_unparsed | 7 |
| starter | conditional | conditional:notes_not_own_page | 436 |
| starter | conditional | conditional:option | 84 |
| starter | conditional | conditional:trim | 1803 |
| tail-lights | unmapped | - | 2344 |
| tail-lights | no_records | - | 12790 |
| tail-lights | split | no_candidates | 186 |
| tail-lights | split | option_split | 14738 |
| tail-lights | split | position_missing | 105 |
| tail-lights | conditional | conditional:body | 201 |
| tail-lights | conditional | conditional:engine | 937 |
| tail-lights | conditional | conditional:engine_unparsed | 17 |
| tail-lights | conditional | conditional:notes_not_own_page | 2213 |
| tail-lights | conditional | conditional:option | 219 |
| tail-lights | conditional | conditional:option_layout | 140 |
| tail-lights | conditional | conditional:trim | 9173 |
| tail-lights | chain_member_conditional | chain_member_conditional | 533 |
| tail-lights | blocked | unverified_member | 141 |
| tail-lights | eligible | - | 326 |
| throttle-body | unmapped | - | 2344 |
| throttle-body | no_records | - | 3413 |
| throttle-body | split | no_candidates | 229 |
| throttle-body | split | option_split | 30977 |
| throttle-body | conditional | conditional:engine | 1194 |
| throttle-body | conditional | conditional:engine_unattested | 185 |
| throttle-body | conditional | conditional:engine_unparsed | 7 |
| throttle-body | conditional | conditional:fitted_not_listed | 167 |
| throttle-body | conditional | conditional:notes_not_own_page | 3178 |
| throttle-body | conditional | conditional:option_layout | 47 |
| throttle-body | conditional | conditional:qualifier | 4 |
| throttle-body | conditional | conditional:trim | 1756 |
| throttle-body | chain_member_conditional | chain_member_conditional | 562 |
| tow-mirrors | unmapped | - | 2344 |
| tow-mirrors | no_records | - | 39179 |
| tow-mirrors | split | option_split | 2533 |
| tow-mirrors | conditional | conditional:trim | 7 |
| window-regulator | unmapped | - | 2344 |
| window-regulator | no_records | - | 4088 |
| window-regulator | split | no_candidates | 71 |
| window-regulator | split | packaging_unstated | 37560 |
| window-switch | unmapped | - | 2344 |
| window-switch | no_records | - | 13355 |
| window-switch | split | no_candidates | 1073 |
| window-switch | split | option_split | 20210 |
| window-switch | split | position_missing | 6400 |
| window-switch | conditional | conditional:notes_not_own_page | 162 |
| window-switch | conditional | conditional:trim | 519 |

## Contradictions with hand-curated groups (spec 7.6)

- none (a contradiction needs an OEM-closed cell inside a hand group)

## Refusals by reason

- cross_category_supersession: 77
- disputed_class: 499
- exclude_at_curation: 2
- held_exterior_cross_model: 19
- recrawl_resolved: 3
- rule_drift: 27
- universal_part_suspect: 20

## Unknown note clauses (top 30)

- `D - DODGE`: 307
- `C - CHRYSLER`: 284
- `E - DODGE AWD`: 198
- `F - BRAND AWD`: 188
- `With Body Color`: 122
- `Body Color`: 115
- `With Foldaway`: 115
- `With Power Fold`: 96
- `All Models`: 82
- `Without Power Fold`: 80
- `Without Foldaway`: 74
- `ERB - 6 Cyl 3.6L VVT`: 65
- `Remanufactured`: 65
- `ED3 - 4 Cyl 2.4L DOHC Dual VVT`: 64
- `EGH - 6 Cyl 3.8L OHV`: 61
- `EZH - 8 Cyl 5.7L HEMI MDS VVT`: 60
- `Heated & Foldaway`: 58
- `Y - CHRYSLER`: 56
- `K - DODGE`: 55
- `41 - SEDAN/QUAD CAB SWB`: 54
- `With Rear AC`: 52
- `(GTS)`: 51
- `EGM - 6 Cyl 3.3L SMPI`: 51
- `3.3 & 3.8L`: 49
- `5 - Lt. Duty DODGE 4WD`: 46
- `With Psngr One Touch`: 46
- `AC & Heater`: 45
- `Without Psngr One Touch`: 45
- `74 - SPORT UTILITY 4-DR TYPE #4`: 43
- `61 - REG CAB 6.5 FT BOX`: 41

## Unmapped catalog models

- Chrysler Grand Voyager: feed 'Grand Voyager' 8 cars
- Chrysler Prowler: feed 'Prowler' 0 cars (excluded: catalog model with no feed cars as 'Prowler' (inventory 2026-11-04); nothing to map)
- Dodge D250: feed 'D250' 10 cars (excluded: M3: the feed spells this truck 'D250', 'D-250' and 'D250 Pickup' (one squash key); not mapped until the feed normalizes them)
- Dodge Omni: feed 'Omni' 1 cars (excluded: catalog model with no feed cars as 'Omni' (inventory 2026-11-04); nothing to map)
- Dodge Ram 4500: feed 'Ram 4500' 0 cars (excluded: catalog model with no feed cars as 'Ram 4500' (inventory 2026-11-04); nothing to map)
- Dodge Ram 5500: feed 'Ram 5500' 0 cars (excluded: catalog model with no feed cars as 'Ram 5500' (inventory 2026-11-04); nothing to map)
- Dodge Viper: feed 'Viper' 0 cars (excluded: catalog model with no feed cars as 'Viper' (inventory 2026-11-04); nothing to map)
- Jeep Gladiator: feed 'Gladiator' 1 cars
- Jeep J20: feed 'J20' 0 cars (excluded: catalog model with no feed cars as 'J20' (inventory 2026-11-04); nothing to map)
- Ram 4500: feed '4500' 0 cars
- Ram 5500: feed '5500' 0 cars
