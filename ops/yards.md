# Yards workstream — status (updated 2026-11-04, sweep review)

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
| U-Pull-R | blocked (Cloudflare Turnstile). Email sent 2026-11-03 to sales@ and jessef@upullrparts.com. sales@ bounced (Microsoft 365 550 5.4.1, address rejected); jessef@ (the contact from the owner's call) did not bounce, so it was delivered. Do not use sales@ again; reader stops at the first 403. Watch in `ops/hub.md`. |
| Harry's | Sucuri; the owner is sending a note via their contact form |
| Pull-N-Save, Budget, Route 34 | outreach sent 2026-11-02, no reply yet. Budget: sales@budgetupullit.com delivered; the CC to Craig@budgetfl.com bounced (user does not exist). |
| Harold's Auto Parts U-Pull-It (Briggs TX) | registry `candidate`. Ario feed embedded on their own site, 612 cars, but all set out 2026-09-09..09-29 and none since (looks like a one-time load). Wire it as config-only in `ARIO_CHAINS` once set-outs newer than 30 days appear. Refine the pin to the parcel first. |
| Young's U-Pull-It (Dudley NC) | directory-only. The site's "inventory" is a full-service part-type search; latest-arrivals shows no cars |
| Sam's Pull-A-Part (Worcester MA) | directory-only. Linder's recent-arrivals is their full-service stock, not the self-service lot |
| Route 50 U-Pull-It (Mays Landing NJ), U-Pull It Auto Salvage of Paducah (KY) | directory-only, no website |

Outreach drafts: `ops/yard-outreach-drafts.md` (all sent except Harry's).
No new drafts from the 2026-11-04 sweep review, because no checked yard blocked us.

## 2026-11-04 sweep review

`coverage_sweep.md` (2026-11-03) had 0 tier A, 0 tier B and 0 tier C, so no
adapters were built and no outreach was needed. I checked every named tier D/E
yard by hand. Per-yard outcomes are in `scraper/INDEPENDENT_YARDS.md`, under the
2026-11-04 section. Not added: A-Z U-Pull-It PA (listed closed), TAS Kingsport,
Salisbury MA and A-1 Metals CA (full-service), Jamm, Jalopy Wizards, Southern
Auto Salvage and Gaston Towing (no site, self-service unconfirmed), Yank A Part
(1 row from 2024), and vendor test/demo orgs. I added `ario_slug` to Bevell's,
Blue & Gold and Prestige so the sweep stops re-listing them.
`coverage_candidates.md` is the Parts workstream's report and has no yard tiers.

Sweep coverage gap. On 2026-11-03 OSM covered no state at all (60 s client
timeout, dead mirror, "3 failed states → stop", Ario eating the discovery
budget). The first fix (ff72088) made the timeouts long and the retries
patient. Its run (41852487799, 2026-11-04, 70 min, dispatched by the hub)
covered only 5 states: AR 2 yards, CA 20. AL, AK and AZ failed on all three
servers (overpass-api.de 502, kumi and private.coffee read timeouts at 210 s),
about 10 minutes each. The real problem was the query: a case-insensitive name
regex over every named object in a state is too heavy for the public servers.
`osm_pending` now holds the 48 uncovered states, and the next run resumes from
them.

Second fix (this commit, unconfirmed live):
- `overpass_query` selects by exact, indexed tags first (`OSM_TAG_CLAUSES`:
  shop=car_parts/car/car_repair/scrap_yard, industrial=scrap_yard/auto_wrecker,
  landuse=industrial, amenity=scrap_yard/recycling, craft=car_repair). It runs
  the name regex only over that set, with `[timeout:90]` and
  `[maxsize:64MB]`, and the client read timeout is 120 s.
- Trade-off: a yard mapped with a name and no tag is missed. Compare CA's
  count with the 20 found by the name-only query.
- 502/503/504 move to the next server at once. Only 429 gets a same-server
  retry (after 30 s).
- Any server failure is a strike, and 3 in a row skip that server for the
  pass. If every server fails the first states, the pass stops (worst case
  about 3 states × 3 servers × 2 min) and everything stays pending.
- The retry pass runs only when some server answered.
- No geographic tiling: the repo has no reliable state bounding boxes, and the
  indexed query should make a whole state cheap. If the next run still fails
  on whole states, add tiling then.
- New `--osm-pending` mode, also the `osm_pending` dispatch input of
  coverage-sweep.yml (plus a `budget_min` input). It skips Ario, queries only
  the pending states with 75% of the budget, checks the new sites, merges into
  the existing report and shrinks `osm_pending`. Dispatch it repeatedly until
  the list is empty. With nothing pending it exits without changes.
- No weekly schedule was added. That is the owner's call: add a cron line to
  coverage-sweep.yml if wanted.

Tests: `scraper/test_coverage_sweep.py` all pass offline, with mocked cases for
the query shape, fast failover on 502, the stop when all servers fail, the
retry pass, 429 handling, the merge, and the `--osm-pending` paths. Live
Overpass is unreachable from the Claude sandbox, so the speed of the new query
is untested until a run happens. After that run, review any tier A/B rows.

## Next

1. When a reply arrives: build the adapter from whatever feed they offer,
   add a `test_<yard>.py`, register in `INDEPENDENT_FETCHERS`, add the pin
   and site link.
2. Re-check Harold's Ario feed for fresh set-outs (one `_ario_live_post` call).
3. After each monthly sweep: review tiers A–B in `coverage_sweep.md`, verify
   each has self-service inventory online before adding.
4. Chains frozen for 6+ scans show in the daily email as `chain-frozen:<chain>`.
