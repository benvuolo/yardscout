# eBay pricing workstream — status (updated 2026-11-04)

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

- Repo secrets `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET` (owner creates a
  keyset at developer.ebay.com). Until then `ebay-prices.yml` exits early
  and bands are the curated placeholders.
- Marketplace Insights needs an access request on the eBay developer
  account; Browse works with the plain keyset.
- Terapeak medians (owner has Terapeak via a seller account). The 30 parts
  to look up are listed in the session notes; when they arrive, calibrate
  the anchors in the gap blocks and record the date in PARTS_GAPS.

## Next, once keys exist

1. Dispatch `ebay-prices.yml` manually, check the summary for `source` and
   per-key counts.
2. Spot-check 10 bands against the app's "sold prices" link.
3. Tighten the plausibility gate if sold data disagrees with anchors.
