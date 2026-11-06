# eBay pricing workstream — status (updated 2026-11-06)

Owns: `scraper/ebay_prices.py`, `.github/workflows/ebay-prices.yml`
(Mondays), `docs/data/ebay_prices.json`, `_ebay_band` in the scraper,
`onlinePriceHtml` / `ebaySoldSearchUrl` in `docs/app.js`,
`scraper/test_ebay_prices.py`.

## How it works

- `ebay_prices.py` tries Marketplace Insights (sold prices) first, falls
  back to Browse (asking prices) on a scope error. Records carry a `sold`
  flag; the app labels "Sold on eBay" / "On eBay now" / "Typical online".
- `_ebay_band` replaces a curated band only when the record is under 45 days
  old, has n ≥ 5, and is plausible against the anchor (not >4× high, not
  <low/5).
- The app shows a "sold prices ↗" link to eBay's own sold-listings search
  (LH_Sold=1&LH_Complete=1) so users can verify.
- No eBay page scraping, ever (robots disallows /sch/).

## Blocked on

- **2026-11-06: eBay rejected the developer account** (username benvuolo; registration rejected, appeal answered "unable to approve activation at this time ... you may consider reapplying at a later time", no reason given). No keyset exists. `ebay-prices.yml` stays dormant; bands stay curated; the app's "sold prices" link to eBay's own search is unaffected. Do not open a second account. Reapply later as YardScout LLC (business registration, hello@yardscout.io, details matching the eBay account and W-9) once the app has more history.

- Repo secrets `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET` (owner creates a
  keyset at developer.ebay.com). Until then `ebay-prices.yml` exits early
  and bands are the curated placeholders.
- Marketplace Insights needs an access request on the eBay developer
  account; Browse works with the plain keyset.
- Terapeak medians (owner has Terapeak free in Seller Hub: Research →
  Product research; sold, last 90 days, used). When they arrive, calibrate
  every band by category from these anchors and record the date in
  PARTS_GAPS. Lamps and wheels are per piece on eBay: double them for our
  pair and set rows.

  ```
  Toyota Camry alternator 2007-2011
  Honda Civic starter 2006-2011
  Nissan Altima headlight 2007-2012 (one side)
  Toyota Corolla tail light 2009-2013 (one side)
  Ford F-150 side mirror 2004-2008 (power, one side)
  Chevy Silverado gauge cluster 2007-2013
  Honda Accord climate control 2003-2007
  Ford Focus window regulator 2012-2018
  Toyota Camry power window master switch 2007-2011
  Honda Civic ECM 2006-2011
  Nissan Altima fuel pump 2007-2012
  Toyota Camry AC compressor 2007-2011
  Ford Escape radiator fan assembly 2013-2019
  Toyota 4Runner rear window regulator 2003-2009
  Toyota 4Runner JBL amplifier 2003-2009
  Toyota Tacoma tailgate 2005-2015
  Jeep Grand Cherokee power liftgate motor 2011-2021
  Honda Odyssey power sliding door motor 2005-2010
  Toyota Sienna 3rd row seat 2011-2020
  Ford Explorer PTU 2011-2019
  Subaru WRX top mount intercooler 2002-2007
  Mazda Miata soft top 1999-2005
  Toyota Camry 17 inch alloy wheel (single) 2012-2017
  Ford Focus Titanium leather seat 2012-2018
  Nissan Rogue Bose amplifier 2014-2020
  Chevy Malibu MyLink radio 2013-2015
  Toyota RAV4 Entune head unit 2013-2018
  Hyundai Elantra navigation unit 2011-2016
  Honda CR-V sunroof glass 2007-2011
  Toyota 4Runner TRD Pro grille 2014-2019
  ```

## Next, once keys exist

1. Dispatch `ebay-prices.yml` manually, check the summary for `source` and
   per-key counts.
2. Spot-check 10 bands against the app's "sold prices" link.
3. Tighten the plausibility gate if sold data disagrees with anchors.
