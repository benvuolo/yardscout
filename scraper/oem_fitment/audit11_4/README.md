# §11.4 sample tools for OEM Likely groups (interchange, 2026-11-18)

Read-only: they read oem-raw through `adapters.RawSource` (git) and never fetch.

- `sample.py NS RAW_SHA INVENTORY DECODES SEED OUTDIR [N_GROUPS N_PAIRS]`: curates NS
  in-process with the given pins, draws a seeded sample of shippable Likely groups
  (every category represented, cross-make / cross-base-model first) plus donor pairs
  from other groups, and writes `<ns>_sample_<seed>.txt` (dossier: product-page
  fitment rows, every app vehicle-year's own-page rows with notes and catalog
  variant, same-part competitor numbers, lot vPIC body mix) and `.json` (index).
- `summ.py DOSSIER [ITEM,ITEM]`: one-screen summary per item.
- `census.py NS RAW INVENTORY DECODES`: every shippable group checked for the failure
  classes found in the nissan rounds (option-column body codes, Infiniti engine
  codes, single-cab rows without a cab note, production windows).
- `gdiff.py OLD.json NEW.json`: claim diff of two groups files by (category, pn).

Pins used on 2026-11-18: raw `57e8b5b99de0` (nissan) / `dca9cd845f26` (shipped),
inventory and decodes from main@a85c654 (`git show a85c654:docs/data/inventory_live.json`,
sha256 1a9cfa73..., `vin_decodes.json.gz` sha256 1357625b...).
