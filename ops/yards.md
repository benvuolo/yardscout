# Yards workstream — status (updated 2026-11-04)

Owns: independent-yard adapters in `scraper/junkyard_scraper.py`
(`INDEPENDENT_FETCHERS`), `scraper/independent_yards_registry.json`,
`scraper/INDEPENDENT_YARDS.md`, `scraper/coverage_sweep.py` +
`coverage-sweep.yml` (monthly, 70-min budget), `coverage_sweep.md/json`,
`scraper/gen_yard_site_links.py` → `docs/data/yard_site_links.json`.

## Rule

No bypasses. A yard that blocks the scraper (Cloudflare, Sucuri, captcha)
gets an email asking for a feed or permission. The existing Harry's Sucuri
solver is left as is; no new solvers. Yards without inventory online are
directory-only entries.

## State

| Yard | State |
|---|---|
| Bevell's Pull It Yourself (NC) | adapter live (`fetch_bevells_inventory`, 50 rows/page, hash ids) |
| Blue & Gold | directory-only, no website |
| Ewe Pullet | not added: site renders no inventory cards |
| U-Pull-R | blocked (Cloudflare Turnstile). Email sent 2026-11-03 to sales@ and jessef@upullrparts.com; reader stops at the first 403. Watch in `ops/hub.md`. |
| Harry's | Sucuri; the owner is sending a note via their contact form |
| Pull-N-Save, Budget, Route 34 | outreach sent 2026-11-02, no reply yet |

Outreach drafts: `ops/yard-outreach-drafts.md` (all sent except Harry's).

## Next

1. When a reply arrives: build the adapter from whatever feed they offer,
   add a `test_<yard>.py`, register in `INDEPENDENT_FETCHERS`, add the pin
   and site link.
2. After each monthly sweep: review tiers A–B in `coverage_sweep.md`, verify
   each has self-service inventory online before adding.
3. Chains frozen for 6+ scans show in the daily email as `chain-frozen:<chain>`.
