# DB Electrical aftermarket groups (origin/oem-raw@9d2c3b76:aftermarket/raw/www.dbelectrical.com.jsonl)

- records 1457, groups 1302, app rows 20496
- refused: {"flag:item_number_differs": 42, "flag:no_application_rows": 10, "flag:unit_type_not_alternator": 38, "flag:unit_type_not_starter": 48, "flag:unparsed_application_row": 17}
- combined-make rows skipped: 464
- app rows whose model matches no lot model: 23230 (1788 names; top: Acura | CL Base (2), Acura | CL Premium (1), Acura | CL Type-S (1), Acura | EL Base (5), Acura | Integra GS (1), Acura | Integra GS-R (7), Acura | Integra GS-R Coupe (4), Acura | Integra GS-R Sedan (4), Acura | Integra LS (2), Acura | Integra Sedan (1), Acura | Integra Type R (3), Acura | RSX Base (17))
- groups sha256 ee2a145092ece681

Tier: Likely only (src aftermarket). Cars covered = lot cars in at least one unit group with at least one other engine-compatible lot car in the same group.

| make | lot cars | alternator | starter | either | engine-confirmed either |
|---|---:|---:|---:|---:|---:|
| MINI | 1011 | 846 | 842 | 846 | 528 |
| Land Rover | 827 | 400 | 729 | 729 | 653 |
| Suzuki | 750 | 540 | 523 | 589 | 486 |
| Jaguar | 704 | 242 | 410 | 410 | 349 |
| Isuzu | 501 | 367 | 399 | 419 | 328 |
| Saab | 387 | 37 | 53 | 53 | 49 |
| Fiat | 372 | 170 | 316 | 316 | 247 |
| Plymouth | 222 | 108 | 110 | 137 | 108 |
| Porsche | 183 | 41 | 124 | 125 | 103 |
| Geo | 182 | 0 | 0 | 0 | 0 |
| Smart | 77 | 0 | 62 | 62 | 49 |

| all makes | 334293 | 235517 | 280180 | 303605 | 258374 |

Verified pairs added: 0 (by construction). Rebuild: `groups_am.py` then `measure.py --aftermarket groups/_report/aftermarket-dbelectrical.json --aftermarket-only`. The groups JSON (4.2 MB) is git-ignored; it rebuilds byte-identically from the pinned raw (sha above).
