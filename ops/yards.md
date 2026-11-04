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

Sweep coverage gap (fixed 2026-11-04, unconfirmed live). On 2026-11-03,
OSM/Overpass failed for AL, AK and AZ and the other 47 states were never
queried, so that sweep only checked Ario orgs. Causes, from the run log
(41682922910) and the code:
1. The client timed out at 60 s while the query allowed the server 180 s
   (AK = 2 × 60 s, AZ = 60 s + an instant mirror failure).
2. The kumi mirror failed immediately.
3. The rule "3 failed states in a row → stop discovery" then cancelled the
   other 47 states.
4. Discovery only got 45% of the budget, counted from the start of the run,
   and Ario took about 6 minutes of it.
5. Exceptions were swallowed, so the log said only "failed".

Fix in `scraper/coverage_sweep.py`:
- Read timeout of 210 s (past the server's 180 s), connect timeout of 20 s.
- Ask `/api/status` for a free slot before each query (wait capped at 120 s).
- Back off 15 s, then 45 s, on 429/504 against the same server.
- A 200 with a "runtime error" remark counts as a failure, not as an empty
  state.
- Added the overpass.private.coffee mirror.
- A server is dropped only after 3 consecutive connection errors. Slow answers
  are never dropped.
- Failed states get one retry pass at the end.
- Each failure is logged with its reason.
- Discovery's share of the budget rose to 65%. That leaves about 39 minutes
  for 50 states after Ario, and at least 24 minutes for site checks.
- States still uncovered are saved as `osm_pending` in `coverage_sweep.json`,
  and the next run queries them first, so a short run can't lose the same
  states twice.

Tests: `scraper/test_coverage_sweep.py` has 12 new offline cases, including a
replay of the 2026-11-03 failure. I couldn't measure real Overpass query times
from the Claude sandbox, because its proxy drops connections to
overpass-api.de. Whether all 50 states fit in one run is therefore unverified
until the next sweep runs. **I did not dispatch coverage-sweep.yml.** That's
left to the owner or the hub (a run takes about 70 min). After it runs, check
the `osm <ST>` lines in the log and `osm_pending` in the JSON, then review any
tier A/B rows.

## Next

1. When a reply arrives: build the adapter from whatever feed they offer,
   add a `test_<yard>.py`, register in `INDEPENDENT_FETCHERS`, add the pin
   and site link.
2. Re-check Harold's Ario feed for fresh set-outs (one `_ario_live_post` call).
3. After each monthly sweep: review tiers A–B in `coverage_sweep.md`, verify
   each has self-service inventory online before adding.
4. Chains frozen for 6+ scans show in the daily email as `chain-frozen:<chain>`.
