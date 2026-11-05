# Aftermarket application tables (second evidence track)

Aftermarket catalogs list, per replacement part number, every vehicle it
fits and the part numbers it replaces. This track records those tables
verbatim. It is separate from the dealer-catalog crawl (`../crawl.py`) and
uses the same politeness: every request goes through `../fetch.py`
(allowlist, robots, 4 s per site, cache, permanent stop on a bot check /
403 / 429 / 503), wrapped by `common.get`, which adds an RFC 9309 robots
reading (all `User-agent: *` groups merged, wildcards honored; Python's
robotparser in fetch.py keeps only the first `*` group).

## Sites (checked 2026-11-05)

| site | status | what it yields |
|---|---|---|
| www.dbelectrical.com | **ok** | alternators + starters: item number, specs, Applications List (Make, Type, Model, Year, Engine; one row per year), "Replaces These Part Numbers" by brand (carmaker OE, Motorcraft/ACDelco, Denso/Visteon/..., Lester, rebuilders) |
| www.densoautoparts.com | unreachable | catalog is POST-only `admin-ajax.php` with a nonce; no GET product pages; PDFs withdrawn (see `densoautoparts.py`) |
| www.tycamericas.com | unreachable | D365 Commerce; product lists load client-side from the retail-server API on another domain; no product URLs server-side; search disallowed (see `tycamericas.py`) |

## Run

```
python3 scraper/oem_fitment/aftermarket/run.py --site www.dbelectrical.com \
    [--category alternator|starter|all] [--max-products N] [--minutes M]
python3 scraper/oem_fitment/aftermarket/verify_records.py scraper/oem_fitment/aftermarket/raw/www.dbelectrical.com.jsonl
python3 scraper/oem_fitment/aftermarket/tests/test_dbelectrical.py
```

Output (git-ignored): `raw/<site>.jsonl`, `.progress.json` (priority queue,
done pages, seen products), `.log`, `.done`, `.blocked`. Exit 10 = time
budget reached (resume by running again), 3 = site stopped (final, no
workaround), 4 = module unreachable.

Order: category root, then every make page, then model pages by value
(cars on our lots from `../worklist.json`, ENGINE_FAMILIES applications,
+500 for makes no dealer catalog reaches), then each make page's own
pagination last (it repeats the model pages and catches unfiled products).
Products are de-duplicated by URL per category.

## Record

```
site, category, aftermarket_pn, aftermarket_brand, title, lester[],
oe_numbers[{brand, pn}]      carmaker-brand numbers (FORD, MAZDA, TOYOTA, MOPAR, ...)
oe_scope: "product"          the replaces table is per product, NOT per application row
oe_service_numbers[]         MOTORCRAFT / ACDELCO (service numbers, not engineering numbers)
oe_supplier_numbers[]        DENSO, VISTEON, BOSCH, HITACHI, Mitsubishi Electric (by number shape)
interchange_numbers[]        LESTER, USA INDUSTRIES, DENSO FIRST TIME FIT
other_numbers[], ambiguous_numbers[]   everything else, verbatim
replaces[{brand, numbers[]}] the table exactly as printed
specs{}, fits_text           Product Specs table (Fits keeps its line breaks as \n)
applications[{years:[y,y], make, type, model, engine, notes:"", raw}]   one per printed row
application_spans[]          derived: contiguous rows with identical verbatim cells merged
multi_make, evidence_lines[] (title, item #, specs, every application row, every replaces row)
flags[], product_url, found_on, retrieved
```

## What a curator must know (DB Electrical)

- **The OE list is product-level.** "Replaces" does not say which OE number
  goes with which application row. Two vehicles on one DB item share that
  aftermarket unit; that is weaker evidence than one OEM number. Use the OE
  numbers to join this track to the dealer-catalog track (an OE number the
  dealer catalog lists for vehicle A, appearing here on a unit that lists
  vehicle B, is a lead for B, to be confirmed in B's dealer catalog), never
  as a verified claim by itself.
- Aftermarket units are often built to cover several OE units (pulley or
  plug differences called out in `fits_text`, e.g. "6-GROOVE PULLEY 59mm OD
  ,BUT OE IS 59mm"; "OE HAS 64mm OD PULLEY REPLACEMENT HAS 59mm"). Applications
  can span engines and bodies the OE numbers do not cover (400-14106 lists
  Explorer/Ranger/Aerostar 4.0 while its Ford OE numbers are Mustang 4R3T/6R3T).
- Application rows come from two data feeds: "Auto and Light Truck" (model
  upper-case, engine like "181cu in 3.0L V6") and "Truck" (model mixed case,
  engine like "3000cc 3.0L V6"). Both are kept; they can disagree on years.
- Make pages list non-road items too (Kubota, Volvo Penta marine). Filter
  by application make, not by the page the product was found on.
- `flags`: `unit_type_not_<cat>:<x>`, `no_carmaker_oe_numbers`,
  `unparsed_application_row:...`, `applications_header:...`,
  `item_number_differs:...`. Treat flagged records as unverified.
- "MITSUBISHI" numbers are split by shape only: `A3TG0491`/`M1T70384`/
  `A002TG0491` -> Mitsubishi Electric (supplier); `MD.../MN.../1800A...` ->
  Mitsubishi Motors (OE); anything else -> `ambiguous_numbers`.
