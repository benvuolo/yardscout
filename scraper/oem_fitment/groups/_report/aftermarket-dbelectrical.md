# DB Electrical aftermarket groups (origin/oem-raw@9d2c3b76:aftermarket/raw/www.dbelectrical.com.jsonl)

- records 1457, groups 1298, app rows 18170
- refused: {"flag:item_number_differs": 42, "flag:no_application_rows": 10, "flag:unit_type_not_alternator": 38, "flag:unit_type_not_starter": 48, "flag:unparsed_application_row": 17, "no_mapped_applications": 4}
- combined-make rows skipped: 418
- app rows dropped because their engine size is not in the unit's own Fits text: 9501
- app rows whose model matches no lot model: 20623 (1703 names; top: Acura | CL Base (2), Acura | CL Premium (1), Acura | CL Type-S (1), Acura | EL Base (5), Acura | Integra GS (1), Acura | Integra GS-R (7), Acura | Integra GS-R Coupe (4), Acura | Integra GS-R Sedan (4), Acura | Integra LS (2), Acura | Integra Sedan (1), Acura | Integra Type R (3), Acura | RSX Base (17))
- groups sha256 2a32305770eae586

Tier: Likely only (src aftermarket). Cars covered = lot cars in at least one unit group with at least one other engine-compatible lot car in the same group.

| make | lot cars | alternator | starter | either | engine-confirmed either |
|---|---:|---:|---:|---:|---:|
| MINI | 1011 | 846 | 842 | 846 | 528 |
| Land Rover | 827 | 400 | 729 | 729 | 653 |
| Suzuki | 750 | 540 | 457 | 585 | 474 |
| Jaguar | 704 | 242 | 306 | 363 | 310 |
| Isuzu | 501 | 367 | 395 | 419 | 328 |
| Saab | 387 | 37 | 53 | 53 | 49 |
| Fiat | 372 | 150 | 316 | 316 | 247 |
| Plymouth | 222 | 108 | 110 | 137 | 108 |
| Porsche | 183 | 41 | 123 | 125 | 103 |
| Geo | 182 | 0 | 0 | 0 | 0 |
| Smart | 77 | 0 | 62 | 62 | 49 |
| all makes | 334293 | 231938 | 270856 | 300275 | 254921 |

Verified pairs added: 0 (by construction). The Fits-text row guard is fail-closed: the Fits text is a summary, so many dropped rows are probably right; they are left out until a per-row basis exists. Rebuild: `aftermarket/groups_am.py`, then `measure.py --aftermarket groups/_report/aftermarket-dbelectrical.json --aftermarket-only`. The groups JSON (4 MB) is git-ignored and rebuilds byte-identically from the pinned raw (sha above).

## Badge twins (aftermarket/twins.py)

Basis: the same DB Electrical unit prints both vehicles. The pair list only selects what is reported; a listed pair with no shared unit gets nothing. Cars = lot cars of that side in a shared unit with an engine-compatible lot car of the other side.

| twin pair | lot A / B | alternator units | alt A / B cars | starter units | str A / B cars |
|---|---|---:|---|---:|---|
| Geo Prizm / Toyota Corolla | 91 / 3568 | 0 | 0 / 0 | 0 | 0 / 0 |
| Geo Metro / Suzuki Swift | 60 / 10 | 0 | 0 / 0 | 0 | 0 / 0 |
| Geo Tracker / Suzuki Sidekick | 26 / 29 | 0 | 0 / 0 | 0 | 0 / 0 |
| Geo Tracker / Chevrolet Tracker | 26 / 115 | 0 | 0 / 0 | 0 | 0 / 0 |
| Saab 9-7X / Chevrolet TrailBlazer | 28 / 1983 | 2 | 26 / 736 | 2 | 26 / 736 |
| Saab 9-7X / GMC Envoy | 28 / 857 | 2 | 26 / 257 | 2 | 26 / 257 |
| Saab 9-2X / Subaru Impreza | 11 / 974 | 6 | 11 / 590 | 5 | 11 / 627 |
| Isuzu Ascender / GMC Envoy | 42 / 857 | 3 | 40 / 790 | 5 | 41 / 793 |
| Isuzu Ascender / Chevrolet TrailBlazer | 42 / 1983 | 3 | 40 / 1950 | 5 | 41 / 1954 |
| Isuzu i-Series / Chevrolet Colorado | 14 / 593 | 2 | 10 / 551 | 2 | 9 / 190 |
| Isuzu i-Series / GMC Canyon | 14 / 132 | 2 | 10 / 121 | 2 | 9 / 52 |
| Isuzu Rodeo / Honda Passport | 222 / 86 | 3 | 193 / 86 | 2 | 207 / 86 |
| Isuzu Amigo / Isuzu Rodeo | 8 / 222 | 2 | 6 / 147 | 3 | 6 / 210 |
| Isuzu Hombre / Chevrolet S10 | 18 / 1065 | 4 | 17 / 593 | 3 | 3 / 328 |
| Suzuki XL-7 / Chevrolet Equinox | 149 / 4114 | 1 | 70 / 373 | 2 | 70 / 769 |
| Suzuki Equator / Nissan Frontier | 3 / 644 | 2 | 3 / 185 | 2 | 3 / 274 |
| Mazda B-Series / Ford Ranger | 258 / 2239 | 5 | 34 / 1380 | 8 | 56 / 2117 |
| Mitsubishi Raider / Dodge Dakota | 43 / 1855 | 2 | 39 / 757 | 3 | 43 / 1341 |
| Plymouth Voyager / Dodge Caravan | 52 / 1039 | 3 | 29 / 101 | 4 | 24 / 361 |
| Plymouth Grand Voyager / Dodge Grand Caravan | 55 / 3235 | 3 | 38 / 162 | 4 | 51 / 672 |
| Plymouth Neon / Dodge Neon | 33 / 352 | 1 | 24 / 338 | 2 | 24 / 114 |
| Plymouth Breeze / Dodge Stratus | 17 / 318 | 1 | 17 / 146 | 1 | 11 / 12 |
| Pontiac Vibe / Toyota Matrix | 408 / 431 | 3 | 387 / 397 | 2 | 350 / 392 |
| Mercury Grand Marquis / Ford Crown Victoria | 997 / 771 | 10 | 803 / 725 | 2 | 712 / 459 |
| Mercury Mountaineer / Ford Explorer | 424 / 4583 | 12 | 421 / 3255 | 4 | 424 / 3270 |
| Mercury Mariner / Ford Escape | 332 / 4929 | 6 | 318 / 2265 | 3 | 332 / 2505 |
| Mercury Milan / Ford Fusion | 311 / 5078 | 4 | 311 / 2941 | 8 | 311 / 3012 |
| Mercury Sable / Ford Taurus | 314 / 2829 | 10 | 312 / 2586 | 5 | 312 / 2686 |
| Mercury Villager / Nissan Quest | 80 / 604 | 0 | 0 / 0 | 1 | 43 / 43 |
| Mercury Tracer / Ford Escort | 26 / 290 | 2 | 17 / 194 | 1 | 25 / 266 |

| make | lot cars | cross-make alt | cross-make starter | either |
|---|---:|---:|---:|---:|
| MINI | 1011 | 0 | 0 | 0 |
| Land Rover | 827 | 59 | 0 | 59 |
| Suzuki | 750 | 186 | 281 | 281 |
| Jaguar | 704 | 0 | 230 | 230 |
| Isuzu | 501 | 360 | 389 | 413 |
| Saab | 387 | 37 | 37 | 37 |
| Fiat | 372 | 0 | 166 | 166 |
| Plymouth | 222 | 108 | 110 | 137 |
| Porsche | 183 | 25 | 32 | 32 |
| Geo | 182 | 0 | 0 | 0 |
| Smart | 77 | 0 | 0 | 0 |
| Mercury | 2869 | 2371 | 2408 | 2541 |
| Pontiac | 4391 | 3595 | 3869 | 4110 |
| Mazda | 6241 | 884 | 586 | 959 |
| Mitsubishi | 2996 | 305 | 1341 | 1352 |
