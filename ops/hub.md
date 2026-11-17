# Ops hub — status (updated 2026-11-04)

This workstream stays in the long-running session because the scheduled
watches are bound to it. It does not build features.

## Live state

- **iOS 1.12.16 build 40**: READY_FOR_SALE (live) as of the 2026-11-15 00:31
  UTC check; shipped 2026-11-14. Check: dispatch `asc-status.yml`.
- **Android 1.12.16 (39)**: Play production, status completed, rollout 100%
  (the API does not show Google's review state). Check: dispatch
  `play-status.yml`.
- **Web**: `main` deploys to GitHub Pages; sw cache `jh-v198` (2026-11-15).
  Changes after `jh-v196` are NOT in the 1.12.16 apps (next release needs a
  new "ship").
- **Cloudflare free plan**: 100,000 Workers requests a day, owner cannot pay
  for more. After the 2026-11-14 crawler fix the rate is 700 to 900 an hour
  (about 20,000 a day). Check: dispatch `cf-usage.yml`.
- **Scan**: `scan.yml` every 4 h, commits `docs/data/`. GitHub skips crons
  often (12:00 and the hourly watchdog were skipped 2026-11-04); dispatch by
  hand when the last scan is over 5 h old.
- **model_lifespan.json** live since the 2026-11-04 15:54 scan: 638 models,
  193 yards, 2,382 yard+model figures, global median 61 d, 134 fast pairs.
  Data-quality pass e787fc9 (2026-11-04): split spellings merged (54 groups,
  GM→division), yards with flushed/stale departure feeds excluded from
  lifespans (rule in `db.yard_departure_reliability`). Takes effect on the
  first scan after e787fc9. Open owner call: Dodge|Ram 1500 vs Ram|1500
  (NHTSA decodes 2011+ as both makes); see `ops/data.md`.
- **Daily ops email** 13:07 UTC (`backend/src/ops_monitor.js`): subscribers
  (Apple + Google from KV `ops:store-subs`, Stripe + comps from entitlement
  records), chain-frozen flags, review-prompt funnel, most-searched parts/cars.
- **Store subscriber count** `store-subscribers.yml` 12:41 UTC daily. Apple
  works (4 active on 11-02). Google stays blank until Google applies the
  service account's "View financial data" permission (owner granted it
  2026-11-03); the job retries daily.

## Scheduled tasks bound to this session

- `trig_019imiZ2pPN5QP6g5kuvcYYR` U-Pull-R reply watch, twice daily, Gmail
  thread `1a1a39a67c2ba6f8` (sales@upullrparts.com, jessef@upullrparts.com).
  Disable after 2026-11-14 if no reply.
- `trig_016qavfgFfYSVTGUH5ERmJuH` one-shot 14:27 UTC 2026-11-04: check
  `docs/data/model_lifespan.json` exists after the 13:23 scan.
- Disabled: `trig_0185m2qk4vqHhGtnwMEqkjoz` (iOS retry, no longer needed).
- Not bound to this session: `trig_01PQWZukG51yQNZQ4zbm1956` "Reddit reply
  drafts" (fresh session per run, hourly 6:42–21:42 America/Denver).
  Owner added Gmail 2026-11-13; enabled by the hub at 16:58 UTC. See
  `ops/reddit.md`.

## Waiting on the owner

- **Model pages tabled by the owner (2026-11-13): "bring them up again when
  you think relevant".** The pages stay live (`/landed/<make>/<model>`).
  Raise them when: the next weekly list is drafted (link the page instead of
  pasting the list); a commenter asks for a state or model list; Search
  Console shows impressions for them; or the full-week-free question needs an
  answer. Do not push the sitemap resubmission again before then.

- Harry's: note via their contact form (draft in the outreach file, see `ops/yards.md`).
- Terapeak medians for the 30 parts listed in `ops/ebay.md`.
- eBay developer keyset (`EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET` as repo
  secrets) and the Marketplace Insights access request.
- Forward any U-Pull-R reply or sample file.

## Known competitor

"Pick and Pull: Junkyard Finder" (BudgetAppsCo, iOS only, $3.99/mo, $24.99/yr,
5 free searches/day). Our keywords and Play title were retuned 2026-11-02;
share link yardscout.io/app.

## Workstream sessions open

| Session | Id | Opened | Brief |
|---|---|---|---|
| Parts curation | session_016ZzJfMzKVhFWLabqYjTTwd | 2026-11-04 13:17 UTC | Accent, LeSabre/LaCrosse, Soul, 1990s Camry/Corolla |
| Yards coverage | session_016ZzJfKB8HduBmXqMGt4kB8 | 2026-11-04 13:17 UTC | sweep review done; Geofabrik OSM source live; OKC Pull-A-Part adapter |
| Data quality | session_016ZzJfL9TNASMsWQaajvZTe | 2026-11-04 18:40 UTC | model-spelling merge; unreliable-yard rule for lifespans |

Not opened: eBay (blocked on keys and Terapeak), Release (needs "ship").

### 2026-11-05 02:55 UTC (usage reset; owner: "ensure everything is at speed")

Running: hub workflows wf_231e5bc1-597 (manual-transmission research, resumed
after the 01:5x usage-limit stop) and wf_9b3745bc-31f (interchange Phase 0 /
crawler R1-R6 / curation pipeline, each on a branch for hub review); Actions:
one capped OEM crawl run (41957090873, 8 sites at a time, 8 s per site),
DB Electrical aftermarket crawl, scan 41949003681 (vPIC default-cell fix),
coverage sweep osm_pending for WA/AL (41958070374). Sessions: Audi builder
(session_016ZzJfL2a85N1tgt5nnonXc), checkpoint auditor
(session_016ZzJfLtcR8MerD7PWDQVoN), Parts next block
(session_016ZzJfMzKVhFWLabqYjTTwd), Parts facelift follow-ups
(session_016ZzJfMe6Km3PdbWY99nsXL). Mopar and VW catalogs stopped by the
breaker (403/503) pending an owner decision on one VW retry.

## 2026-11-06 ~12:30 UTC owner decisions ("do everything you think")
- OEM Likely groups on: toyota, gm, subaru, mopar, ford, vag, hmg, mb, own-page rule plus a hold on exterior styling groups that span base models (308 held for a later owner checklist). Session session_016ZzJfMapNmKpMbuoJzVupB commits the groups and checks the live site after the next scan.
- Aftermarket (DB Electrical) on only for mazda/starter, mitsubishi/starter, mopar/alternator, mopar/starter, nissan/starter, volvo/alternator. Gap makes stay off. Session session_016ZzJfLB9KQDQ64RoN6T9sX.
- Design: Direction A "Pull Sheet". Part names free, prices locked; "Saved" becomes "Pull sheet" (UI label only, rule 6); map deferred. Hard requirement: no truncated text anywhere, enforced by an automated check. Built on branch design/pull-sheet by session_016ZzJfHZvCRTjz2pPUso8tr; not merged until the owner has tested it on TestFlight.
- release-ios.yml gained `source_ref` (commit 2026-11-06). A non-main branch builds to TestFlight only: submit is refused and the version bump goes to that branch. Plan: TestFlight 1.12.13 from design/pull-sheet once its checks pass. The App Store submission still needs the owner's explicit "ship".

## 2026-11-06 ~18:30 UTC owner decisions: photos and TestFlight
- Photos back on in the app ("I don't think yards would object, and if they do then we can switch"). Only chain-hosted photos, loaded from the yard's own URL with the "Photo: <yard>" credit and the per-chain kill switch. Never Pick-n-Pull/Row52 images; no rehosting or proxying. Coverage and native-fit study: session_016ZzJfLCh5MFJ1FuhfySZCL. Display goes in on design/pull-sheet.
- The owner's Apple ID email was granted comp Pro via grant-pro (masked in logs; expires 2027-11-06) so Pro can be tested on TestFlight. TestFlight IAP runs in Apple's sandbox, so Restore cannot see the App Store subscription; this is expected.
- The stray TestFlight prerelease version 2.0 was expired by the owner.
- Next TestFlight (build 29): "Worth pulling" leads the car screen (top 3-5 parts; Pro sees values, free sees names only), plus photos if they are ready.
- 2026-11-06 ~18:40 UTC, owner: "its fine to put pick-n-pull photos even with the water mark. I'll take it down if they request it but it attracts customers to them." Narrow exception to the photo policy: show the Pick-n-Pull photo URLs that their API already returns (Row52-hosted, watermarked). They load from the original URL with the credit "Photo: Pick-n-Pull" and their own kill switch. CLAUDE.md rule 7 otherwise stands (no Row52 site, API, account or data).

## 2026-11-06 ~23:30 UTC alerts: free weekly recap teaser (branch, awaiting review)
Branch `alerts/recap-teaser` @ 181f0a2 (session_016ZzJfKjBN7He2RMxFV9A8z's
app work is separate, on design/pull-sheet). Not merged, not deployed.
- Free weekly recap email only (`sendWeeklyDigests` → `buildDigestEmail`):
  per car "Landed Tue — Pro would have pinged you Tue." (first sighting
  seen_at + yard dateAdded; weekday only when the same in ET..PT, else
  "N days before this email"; nothing if found < 1 day before the email or
  data is missing). Gone cars: "Was at <yard> from Wed and left before this
  email" (current shards via the saved-car resolver, now `inv_resolve.js`;
  only when the yard is still scanned). No days-on-lot for gone cars:
  last-seen is not stored, so the number would be invented.
- One summary line at the top plus one link to the existing Pro page
  (`/#tab=alerts`, "See Pro alerts ($8.99/mo)"); gone count only when
  presence is known for every match. Weekly recap gains an HTML part.
- Unchanged: which cars are included, dedupe, free limits/gates, Pro instant
  email (byte-identical text, unit-tested) and pushes, device weekly push.
- DEV_MODE-only `{now, preview}` body on `/v1/admin/digest/run` (prod ignores it).
- Tests run locally: `test/recap_unit.mjs` ALL PASS (new); `e2e-email.sh`
  ALL PASS (new section 7: real shards, gone/present/unknown, Pro skipped,
  match set, one link, dedupe); `e2e-devices.sh` ALL PASS; `e2e-ops.sh` ALL
  PASS; `alerts_e2e.mjs` ALL PASS (ad-hoc harness, no runner script exists);
  `e2e.sh` 38/39, the 1 failure ("radius filter did not narrow") also fails
  on unmodified main, so pre-existing.
- Screenshot: `design/screenshots/recap-teaser/free-recap-phone.png` (390 px,
  2x) + sample .html/.txt, rendered by `backend/test/recap_preview.mjs`.
- To deploy once the owner approves: merge `alerts/recap-teaser` into main.
  The push touches `backend/**`, so Deploy Workers runs automatically
  (deploy-workers.yml; no new migration, no new secret). The next Monday
  15:00 UTC cron sends the new recap. Check after deploy:
  `POST /v1/admin/digest/run` is NOT a dry run in prod (it sends), so verify
  with the Monday cron logs / ops daily email instead.

## 2026-11-09 ~03:10 UTC owner decisions: held exterior release and heavy photos
- Held exterior groups: the owner chose option 1, "Do 1". Release all 96 groups in scraper/oem_fitment/groups/_report/held_exterior_release.json: still held, agent RIGHT, and at least one cited independent non-eBay source. Agent RIGHT plus one source is enough; owner checklist taps are not required. The groups still have to pass every curate rule. Subaru entries stay out while Subaru is withheld. Claims read "Likely fits — check the part number".
- Heavy photos (VinPlus ~22k, Sturtevant, Army's 4 MB originals): the owner wants them included. They are published per scan with a heavy flag, and the app shows them on the car screen as tap-to-load.

## 2026-11-09 ~07:40 UTC Round 9 (map sheet) regression; Ogden pins wait on the next scan
- Trial merge main (503f24cf) + design/map-sheet (33ffc9d), shell jh-v167. All pass: unit 11/11, scraper tests 26/26, backend e2e/e2e-email/e2e-devices/e2e-coverage/e2e-ops, interchange_e2e, pf_ux_e2e, tab_retap, no_pick_models, model_years, yaris, map_regions_e2e (10 regions, 480 layouts) and ui_no_truncation (1248 checks, 0 failures).
- part_finder_e2e fails only on the known M3 data case: no E46 M3 on a tracked lot today.
- e2e-email "gone car" failed between 00:00 ET and 00:00 PT because the recap rightly names no weekday then. That was a test bug, not an app bug. Fixed in 503f24cf, and the suite passes.
- Watch for this: the backend e2e scripts leave `wrangler dev` / `workerd` running. Kill them before rerunning a suite, or the rerun talks to the stale server and fails with "internal" errors.
- Ogden is still a same-spot cluster on live data because junkyards.json predates c5fe7570. Scan 42567561362 checked out f3111e3f before the re-pin. The ~08:00Z scheduled scan publishes the new coordinates.
- Waiting on the owner's "ship it" for Round 9. On "ship it", merge design/map-sheet (head cb8b36a8, which includes main) and confirm the live sw is jh-v167.
- Today, Monday, the 15:00Z cron sends the first weekly recap with the Pro teaser (alerts/recap-teaser). Check it in the next daily ops email.
- Manual filter (owner asked 11-09): it was dropped 2026-10-27 because it emptied most searches. Today 3,658 cars in the extras are confirmed manual (vin 3118, vin_code 463, listing 43, engine 25, trim 8, model 1). Proposed: a free "Manual (N nearby)" chip with honest copy, and "manual only" as a Pro watch option. Waiting on the owner.
- 08:46Z scan (51e4c23c) published the re-pinned coordinates. Ogden: Tear-A-Part 41.2444,-111.9962; Utah Pic-A-Part and its Premium lot 41.2369,-111.9917. Nationwide, no two different yards share a spot (304 yards, 302 spots; only the Premium lots pair with their main yard). map_regions_e2e rerun on main + cb8b36a8: 10/10 PASS, Salt Lake same-spot clusters 0.

## 2026-11-09 ~17:30 UTC banner + map first view shipped (web); open items
- Owner said "ship it". Merged design/promo-map-fit (f3f1cae3) as 86d29797, sw jh-v168, live. Regression on the merged tree all passed: units, app_promo_e2e, map_regions_e2e, ui_no_truncation 1296/0, pf_ux, interchange, tab_retap.
- Sent to the design session, in this order:
  1. Desktop photos. The credit is covered by the image (`.photo-box img { z-index:1 }`), and wide grey letterbox bars appear in the 3-column grid. Owner report: "images are large/wonky" on the computer.
  2. The You dot is hidden under a bubble (Atlanta).
  3. First view on short Safari viewports (390×664): only the nearest yard is drawn, without You.
- ops_monitor: chain freezes with no full weekday 14–22Z block since are "quiet", not issues (ca2a07c0).
- Owner asked about the Parts tab:
  - Headlights: same-model generation for every car, plus 87 OEM groups across 30 models.
  - Missing: Honda/Nissan/Mazda/BMW catalog data, and wheels, AC compressor, PS pump.
  - GX vs Tundra accessories: GX 470 is not on the 2UZ alternator part-number list, so it shows as "Likely fit — verify part #". GX 460 (1UR-FE) has no engine family yet.
  - Proposed: label same-engine/different-model accessory donors "Same engine — part may differ". Waiting on the owner.
- 17:10 UTC owner: "Yes relabel those, and start on Honda/Nissan and wheels".
  - Relabel approved: same-engine/different-model accessory donors get "Same engine — part may differ" and are listed below the verified matches.
  - Honda/Nissan and wheels: start. Shipping new cross-model groups still needs the owner's go.
  - New interchange sessions:
    - session_016ZzJfK5RFgko9f1gx7qjEa: relabel first (branch interchange/same-engine-label, hub merges), then Honda/Acura + Nissan/Infiniti R1/R3 + curation + §11.4 sample (0 WRONG bar).
    - session_016ZzJfL4wG1wgpyYymW2Z28: wheels. Research the basis, propose to the hub, then build on branch interchange/wheels.
  - Both were created without the repo attached and were told to add_repo first.
- 17:30 UTC owner: "Great, again we're going for breadth here and data quality, its embarrasing to not have this when car-part.com has a gorgeous example. We will create the better version, with no external or third party costs".
  - Hub policy under it: a new make or category ships once its CURATION_SPEC §11.4 sample has 0 WRONG. The hub confirms each and tells the owner as it goes live, so there's no per-namespace wait.
  - Paid sources and licences stay out.
  - Added session_016ZzJfKqBWhtUcqYMMseVgn (make breadth + Subaru) and session_016ZzJfKdkBXaVYDDQb9cy2J (categories + coverage matrix). See the ops/README exception.
- 18:50 UTC: aftermarket probe results.
  - OUT: Depo (challenge), Four Seasons (403), SMP/ACI (403), Cardone (robots, client-side).
  - Spectra Premium passes robots, has no challenge on catalog pages, and no anti-automation clause. Two issues are HELD for the owner:
    (1) fetch.py's CHALLENGE_RE trips on the inert reCAPTCHA script include on every ecat page. An exemption would loosen our bot-check detector, so it's the owner's call under CLAUDE.md rule 2.
    (2) Their Legal Notice has a no-reproduction clause. We would store facts only.
  - Not crawled; fetch.py unchanged.
- 18:47 UTC: make-breadth pushed rules 1-3 (7192563). GM went 309→279 (30 removed, 3 lose apps, 11 gain cab notes). These were live wrong or uncertain claims: GMT800/900 regulators and EXPORT-coded mirrors. Hub verified oemStatus ok x8 and test_groups_hash.
- 18:40 UTC: same-engine relabel merged (080e1061, sw jh-v171).
- ~19:35 UTC:
  - Wheels merged (b71585bc, sw jh-v172). Conflicts with tier C were resolved by keeping tier C's name rules plus the tier W entries. Worklist versions where both flags apply: jeep v5, kia v3; ford/hyundai/lexus/vw v3.
  - Tier W crawl dispatched for gm/vw/mb/hyundai/kia (42684614492), queued behind 42666726212.
  - Relabel live (jh-v171) and verified on the GX 470 alternator search. Photo fix live (jh-v170).
  - Make breadth pushed the climate-control note fix (661d537) and the GM 1500 series filter (c5d7f44/f9423ed). oemStatus verified ok x8.
  - CR-Z normalizer fix 1cf5dd03. test_model_map stays red on the published inventory's "Cr-Z" until the next scan.
  - You-dot map fix (design/you-dot d9cff7d → sw jh-v173): regression running.
- ~19:45 UTC owner on Spectra Premium: "no email needed". Hub reading: no outreach, so Spectra stays out. fetch.py's challenge detector is unchanged and the site is not allowlisted, because using it would mean loosening the bot-check stop and accepting their no-reproduction clause. That needs an explicit owner "use Spectra" (rule 2). The aftermarket session is stopping.
- ~19:47 UTC owner: "use spectra if it doesnt break anything".
  - Spectra Premium reopened. The site is allowlisted, and the detector exemption is site-scoped and narrow: only the inert reCAPTCHA api.js include on pages that also carry catalog markup. Any real challenge, 403/429/503 or missing body still means a permanent stop. Tests go both ways, and other sites' detection stays unchanged.
  - Data use is facts only; we publish our own groups.
  - Ship bar unchanged: §11.4 sample with 0 WRONG plus hub confirmation. Session: session_016ZzJfMnemMEFN88kPnYgxs.
- ~20:15 UTC owner decisions (question dialog):
  - GSP North America: "Yes, use GSP". Site-scoped detector rule on the Spectra pattern (Shopify captcha-bootstrap form-protection script). Likely-only, with strict refusals; drive and trans never inferred.
  - 1A Auto: "Yes, use 1A Auto anyway". The owner accepts the risk from its personal/non-commercial licence. No rule-2 issue: robots OK, no challenge. Facts only.
  - Builder: source scout 2 (session_016ZzJfKZ49mzzQhu4KT7HkU). Ship bar unchanged.
- ~20:20 UTC owner: "lets do it, also 1A im not selling the part fitment portion".
  - 1A-derived fits stay in the free part of the Parts tab, never behind Pro (a test enforces it).
  - No 1A prices, descriptions or images.
  - The GSP detector rule (script-only "captcha" word tolerated; visible or strong markers still stop) was approved under the owner's GSP go.
- ~20:40 UTC: oem-aftermarket-crawl.yml now runs a matrix over every live aftermarket site (scout, 33655227; schedule 53 */6, input "all"). Hub cancelled the serial Spectra and 1A runs and dispatched "all": run 42694329196 has Spectra, GSP and 1A Auto in parallel. DB Electrical is .done.
- ~22:55 UTC:
  - The scan finished at 22:29 (data 22:24). Live oemStatus: subaru 42, gm 279, the others unchanged, CR-Z clean.
  - Main fast-forwarded to b271356 (wheels-ship): 29 audited cross-model Mopar wheels groups, 9,610 lot cars, mopar 281→310. WHEELS_AUDITED_NS={mopar}; hmg/mb/vag wheels wait for their own §11.4 rounds.
  - Verified: test_groups_hash, oemStatus ok x8, pf_guards, test_interchange.
  - The stale branches interchange/wheels and interchange/wheels-curation are left in place; deleting them was refused as destructive, and that's harmless.
- ~23:00 UTC owner: "in terms of priority, think of parts people go to junkyards for. It wont be brake pads, its more likely other items."
  - Hub ordering: (1) cross-model depth on the existing body/lighting/interior/electronics categories for the high-volume makes (Honda/Nissan, make breadth); (2) new tier D categories: fog lights, center console, door panel, door handles int/ext, door lock actuator, blower motor, rear seat, sunroof, tailgate handle/camera; (3) Spectra radiator/AC/fuel; (4) strut/knuckle/CV audits last (they keep crawling).
  - 1A Auto widens to junkyard-demand lines where its fitment is clean.
- ~23:15 UTC: merged wheels-ship-3, giving 41 audited cross-model wheels groups (mopar 28 / 9,047 cars, mb 10 / 243, vag 3 / 117). New rules: body words identical, spoke counts agree, Front/Rear notes refuse. Verified: oemStatus ok x8, test_groups_hash, pf_guards.
- Phoenix map tweak merged (sw jh-v174).
- Category breadth is preparing interchange/categories-ship: 14 new Parts-tab categories with same-model-generation donors only, no aftermarket/OEM groups yet. The hub runs the regression before merging.

## 2026-11-10 ~01:00 UTC desktop rows + 14 new part categories live
- Merged design/rows-desktop to main (b22c744a, sw jh-v175). It went live at 00:20. Desktop Walk the rows now has 112x84 thumbs with the soft fill, and photos stay under the sticky row header (checked live at 1280px).
  - Regression: units, photo_layout, app_promo, tab_retap and ui_no_truncation (1296/0) all pass.
  - map_regions_e2e: an intermittent Phoenix 375x553/200% first-view failure (the nearest yard ends up in a 2-yard bubble at zoom 13). It reproduces on main (1 of 3 reruns), so it's not from this branch. Handed to design, branching from b22c744a, sw v177.
- Merged interchange/categories-ship to main (ef5d52e6, sw jh-v176). It went live at 00:56.
  - The 14 new categories offer same-generation donors only; GROUP_HOLD_CATS holds their OEM/aftermarket groups.
  - interchange.json was regenerated in the merge: only `categories` changed (30→44); oemStatus is ok x8 with unchanged group counts.
  - Live check: all 14 are findable in the part search at 390px, with 0 page errors.
  - Regression: everything passes except part_finder_e2e's known E46 M3 case (0 M3s on lots).
- Wheels hmg: the §11.4 census found 8 WRONG, all 2010-13 Forte/Koup (body-code and production-date). The rule fix ships exactly the 9 census-OK groups (1,784 lot cars). Hub CONFIRMED hmg 9; the single push is based on ef5d52e6 under the usual gates.
- U-Pull-R 00:13 check: no reply from Glenn; the scan still shows 0 cars (captcha).

## 2026-11-10 ~01:00–04:00 UTC hmg wheels, scan revert fixed, Phoenix + headings, Spectra live
- Wheels hmg merged (e0ea686c): 9 audited Hyundai/Kia groups; wheels.json 50 (mopar 28, mb 10, hmg 9, vag 3).
  - 39 tier C hmg strut groups sit in groups/hmg.json, held by GROUP_HOLD_CATS (verified: not in any lazy file or the payload).
- INCIDENT, fixed:
  - Scan run 42724288950 (checkout 00dc804 at 23:55, commit 01:12) put its stale interchange payload over categories-ship and wheels-hmg. Live dropped from 44 to 30 categories and from 50 to 41 wheels groups.
  - Restored at ec594131 (live 01:49).
  - Fixed at 838ca475: scan.yml rebuilds the payload on the rebased tree whenever main's scraper/ or payload changed during the scan. Simulated in 4 cases. ops/data.md has the details.
  - A check after the 04:00 scan is scheduled for 05:40 (trig_01XWZbqvWoTTpekUTtHaXzea).
- Completion-first (make breadth, fa624032): markers.mode runs own-page completion before a re-opened category pass on sites with a previous marker. Effective from run 26.
- design/firstview-settle-v3 merged (4c748386, sw jh-v177, live 03:47):
  - Phoenix first view settles: 375x553 passed 10/10 reruns (main was 1/3 failing); map_regions 11/11.
  - Parts headings: the headline is on its own line and there's no em-dash line.
  - ui_no_truncation 1296/0.
- Spectra Premium release merged (13c0c898, live 03:47):
  - §11.4 round 2: fresh seed, independent agent, 597 vehicle pages, 0 WRONG in all 9 categories; hub confirmed.
  - 613 groups pinned to oem-raw@ac4d1f0d: radiator 95, A/C compressor 98, A/C condenser 63, heater core 75, evaporator 53, throttle body 76, fuel pump module 86, ignition coils 67.
  - Per-source fail-closed release (_AM_SITE_CATS): OEM and other sources stay held.
  - Live check: a 2012 Equinox 2.4L radiator search shows Spectra CU13103 with no catalog row and 0 page errors.
  - Gated coverage beyond same model+gen: coils 11.1%, throttle body 7.6%, heater core 5.7%, A/C compressor 4.9%, condenser 4.0%, evaporator 3.4%, radiator 3.3%, fuel pump 1.3% of 338k lot cars.
- Not done: cancelling the stale aftermarket run 42714835085 to move 1A lamp lines ~3 h earlier was refused by the permission classifier. The normal order applies, and 1A lighting starts ~07:40.
- Pending: GM wheels (tier W lands in more than a day); Honda/Nissan R3 after tier C; make-breadth completion from run 26; category tier D after the placeholder pass; GSP/1A §11.4 when their categories finish.

## 2026-11-10 ~07:00–12:30 UTC 503 cluster, platform pacing, GSP cv-axle live
- 503 cluster: 07:10–07:16 mbpartsgiant, nissanpartsdeal and subarupartsdeal got a 503 each and went .blocked. Run 25 had 6 SimplePart jobs live at once (max-parallel 6). All 20 dealer stores are one platform (SOURCES.md §2).
  - Fix merged at f603b035 (make breadth): one CI job per platform, round-robin site turns, an 8 s platform-wide gap in fetch.py, and a refusal log (raw/<site>.refusals.jsonl).
  - platform_crawl.py skips a site after an unexpected crawl exit or 2 net-failure exits; turns end 10 min inside the job timeout.
  - Run 26 (42775878285) started 10:00 on the old workflow and couldn't be cancelled; no new .blocked as of 12:12.
  - OWNER DECISION PENDING: one retry each for mbpartsgiant and nissanpartsdeal after the pacing fix (subaru already used its retry).
- 1A Auto: 503-blocked at 04:30 and OUT (raw kept, unused; the stored-copy verifier was refused; outreach is the owner's call). No other permitted free lamp/mirror source (SOURCES.md); lamp depth comes from the OEM catalogs.
- GSP cv-axle merged (eb09d422 + 491c846e, sw jh-v178, live 12:23).
  - §11.4 needed 4 rounds: round 1 found union engines; round 3 had 2 WRONG (Santa Fe Sport vs LWB). Fixes: per-year strict engine coverage, sibling-name guard, spline/length checks in the note.
  - Round 4: 0 WRONG.
  - 88 groups (59 front, 29 rear) with the donor-side driven-axle gate (d) in the app.
  - Live check: a 2021 Terrain search from Tulsa shows a 2022 Equinox via NCV10179.
  - Follow-up to design: move provenance sentences behind "Why it fits" (cards are long).
- HMG own-page breadth: option 3. Keep the shipped groups; make-breadth-hmg-body is parked (round 1: 9 WRONG; round 2: 3 WRONG + 16 UNSURE on variant pairs).
- LIVE-ACCURACY: production-date windows. Shipped toyota/lexus (26 dropped + 6 trimmed) and ford (7 dropped) rest on own-page rows whose production window misses the claimed year (e.g. IS 83800-53580, RX 83800-0E011, GS 81070-30B82). Make breadth is running a 39-item 2-verifier check, then ships rule (b) (07..06 OR calendar span) or (a) in one re-curated push. Priority over new breadth.
- The scan.yml payload-rebuild fix worked in production (the 05:23 scan rebuilt and kept 44 categories / 50 wheels / Spectra).

## 2026-11-10 ~14:45 UTC PAUSED (owner near the weekly usage limit)
- Live: 45 categories (wiper-motor added at f8a3a958, sw jh-v180; same-gen donors only, OEM groups held, OEM_RELEASED empty), Spectra 613, GSP cv-axle 88, wheels 50, toyota 533, ford 74; aftermarket card notes declutter v179.
- All workstream sessions are idle with their check-ins cancelled. The U-Pull-R trigger (trig_019imiZ2pPN5QP6g5kuvcYYR) is disabled; re-enable it on resume.
- Owner decisions pending: one 503 retry each for mbpartsgiant and nissanpartsdeal; the design combined-search proposal. 1A outreach email is DRAFTED in Gmail (no recipient; the owner adds 1A's contact and sends).
- Resume order: make breadth (ford/jeep/bmw advances + wiper per-ns release), then Honda/Nissan R3 audits, then scout (GSP strut/other cats).

## 2026-11-12 business review; search pages and funnel fixes live
- Plan and owner decisions: `ops/business-plan.md`. Workstream files: `ops/seo.md`, `ops/growth.md`.
- Live: seo/onpage-1 (3a886748, sw v181): real H1s and titles, yard inventory pages, /prices pages, /sitemap.xml with 751 URLs, robots.txt points at it. growth/funnel-1 (2f372660, sw v182): apps exempt from the localhost analytics guard, once-only counters, per-platform funnel in the daily email, Pro sheet button pinned (live check 375x667: bottom edge 628), Android web visitors to Google Play, share-page alert intent lands on a prefilled watch card.
- iOS 1.12.14 went live 2026-11-12 00:59 UTC; Android 1.12.14 live since 11-09. The app half of growth/funnel-1 needs a 1.12.15 store release (owner's "ship").
- GitHub Pages serves assets with a ~10 min CDN cache: sw.js can show the new version before styles.css/app.js do. Wait for the asset hash before judging a live check.
- Waiting on the owner: decisions D1-D8 in the plan (weekly email signup for web watchers, free prompt alert, annual plan, privacy page wording, community posts, Search Console + Bing with /sitemap.xml, store listing text, mb/nissan retry).
- Next builds when approved: web email signup at watch creation (D1), nationwide make/model pages, privacy wording (D4), landing-page measurement.
- 2026-11-12 ~16:15 UTC owner decisions: "ship" 1.12.15 (release-ios run 43256550663 submit=true, release-android run 43256556677 track=production, both from cdc8778a); D1 weekly email signup for web watchers APPROVED (not built yet: held for the weekly usage cap, build first after reset); D4 privacy wording done (cdc8778a, sw v183); D8 one 503 retry for nissanpartsdeal and mbpartsgiant (.blocked removed, .retried503 added on oem-raw; next crawl run uses platform pacing); D3 annual plan declined for now; D2, D5, D7 explained, awaiting answer. Owner does Search Console + Bing (sitemap.xml).
- 2026-11-12 ~18:50 UTC: growth/email-signup merged and live (8be283e4, sw v184). Live check: POST /v1/recap/signup answered 200 confirm-sent and the confirmation email arrived in the owner's inbox (EMAIL_UNSUB_SECRET is set in production). EMAIL_POSTAL_ADDRESS empty by owner's choice for now. New store screenshots (style A) merged at 3331342f; Play listing push and iOS 1.12.15 resubmit (build 37, new shots + listing text) both succeeded; the owner files the expedite request. Outreach: r/fordranger sample sent 11-12; XJ follow-up and r/1stGenTacoma modmail drafted; Tacoma next.
- Known small items for later: Pick Your Part rows blank; car screen repeats model as trim; dark-mode map zoom buttons white and Map/List tab contrast; ui_no_truncation full run now exceeds 55 min (split by width).

## 2026-11-12 ~20:50 UTC r/XTerra post live; car search building

- Owner posted the weekly Xterra list on r/XTerra (115 set out Nov 5–12, 4x4
  marked). Site link tagged `utm_source=reddit&utm_campaign=xterra`; Play link
  carries the same referrer; App Store link is untagged (needs the owner's
  provider token). First hour: 341 views, 7 upvotes, 2 comments.
- Comment asked for cars near a zip without picking a part. It exists (Cars
  tab, Filters → Make → Model) but is hard to find. Build agent is on
  `design/car-search`: search box at the top of the Cars tab plus a
  `#cars=Make|Model|years` link. Hub reviews, regresses and merges.
- iOS 1.12.15 (37): WAITING_FOR_REVIEW since 17:27 UTC (asc-status 20:44).
  Expedite request is the owner's to file.
- Subscribers as of 11-11: Apple 4, Google 1.

## 2026-11-12 ~22:10 UTC car search merged (sw jh-v185)

- `design/car-search` merged at bf82ec45: search box at the top of the Cars
  tab and `#cars=Make|Model|years` links. Hub regression on the merged tree:
  car_search unit + e2e, model_years, no_pick_models, funnel_events,
  share_watch, tab_retap, browser_e2e (17/0), all pass. ui_no_truncation was
  run by the builder at 390 and 1280 only (568 checks, 0 failures); the full
  width matrix was not run.
- Live on the web at merge. The apps bundle the web files (`webDir`
  `native/www`, no remote URL), so iPhone and Android get it only with the
  next store release, which needs the owner's "ship".
- Suggestion counts show for Pro only (same rule as the Make/Model lists).

## 2026-11-12 ~23:00 UTC car search wording; U-Pull-R follow-up drafted

- Owner asked whether the new search box should go (an earlier free-text
  search was removed because people could type anything). Kept: it is a
  picker, not free text; the list only changes when a suggestion is picked.
  bf9c7653 (sw jh-v186): the no-match row now says the box finds cars by make
  or model and points to the Parts tab.
- U-Pull-R: Glenn (CTO) has not replied since 11-06. Follow-up saved as a
  Gmail draft in thread `1a1b2b1b2f24f262`; the owner sends it. Reply watch
  `trig_019imiZ2pPN5QP6g5kuvcYYR` is still disabled.

## 2026-11-12 ~23:30 UTC owner: "lets do 3 and 4" (parts accuracy, weekly scorecard)

- Owner sent the U-Pull-R follow-up to Glenn (thread `1a1b2b1b2f24f262`).
- Two builders running, each in its own worktree; hub reviews and merges:
  - `parts/gen-splits-trucks`: Xterra, Ranger, Cherokee XJ and Tacoma parts
    rows that span generations get gated or split, each with a stated basis
    (rule 3); no invented prices.
  - `growth/scorecard`: weekly scorecard at the top of the daily ops email
    (visitors by source, watches, emails, paywall to checkout, subscribers)
    plus an admin JSON endpoint. Not deployed until merged.

## 2026-11-12 ~23:15 UTC weekly scorecard live in the Worker

- `growth/scorecard` merged at 5761863e; deploy-workers run 43326783612
  succeeded. Hub regression on the merged tree: scorecard_unit (96),
  ops_quiet, funnel_counters, recap_signup units and e2e-ops.sh, all pass.
  `/v1/admin/scorecard` answers 401 without the secret (was not there before).
- First real scorecard: the 13:07 UTC email on 2026-11-13. Week-on-week
  changes read "not comparable" until two full weeks are on the fixed
  counting; the subscriber change starts 7 days after the first snapshot.
- Not done: confirmed email sign-ups cannot be split by link (the server
  counts confirmations without a source). Noted in `ops/growth.md`.
- Still running: `parts/gen-splits-trucks`.

## 2026-11-13 ~00:00 UTC parts generation splits merged

- `parts/gen-splits-trucks` merged (head b87fabbf). Hub regression on the
  merged tree: all 25 scraper test files that import the parts tables exit 0;
  `match_vehicle` checked for 2000/2002/2004/2008 Xterra, 2005 Ranger, 2024
  Tacoma. Live with the next scan after the merge.
- Hub decision: first-gen Xterra rows were added back where a part-number
  basis exists, carrying the pre-split anchor band (the builder's strict
  version left 604 first-gen trucks with no Xterra card). Recorded in
  PARTS_GAPS §25.1 as carried anchors.
- eBay bands do NOT refresh: eBay rejected the developer account on
  2026-11-06 (`ops/ebay.md`), so anchors stay until a keyset exists.
- Open for the parts workstream: 2000 tail lights and side steps, 2003–04
  console lid (no fitment found); four 2nd-gen and three 1st-gen Xterra bases
  are search-excerpt-only (nissanpartsdeal and parts.nissanusa.com are not on
  this environment's network allowlist); Tacoma is missing from
  MODEL_GENERATIONS; the 2024 Tacoma and Ranger have no rows.

## 2026-11-13 ~01:00 UTC tab scroll fix (tester feedback); Canada question

- Tester: after scrolling to the bottom of one tab, the next tab opened at
  the bottom too. d570aa41 (sw jh-v187): each tab keeps its own scroll
  position on real taps; a tab not opened yet starts at the top; re-tap still
  goes to the top. tab_retap_e2e extended (14 checks pass); car_search,
  share_watch, model_years, funnel_events e2e and browser_e2e pass. Not run:
  alerts_e2e (needs the local API server), map_regions_e2e (timed out at
  420 s, long matrix). Checked live at 390 px.
- Web only until the next store release (owner's "ship").
- r/XTerra commenter asked about Canada: 5 Canadian yards are covered
  (Pick-n-Pull Calgary x2, Edmonton, Kelowna; iPull-uPull Edmonton), postal
  codes work. Kenny U-Pull (~25 Canadian yards) stays a candidate.

## 2026-11-13 ~04:50 UTC Reddit reply drafting

- Owner asked for an agent that drafts Reddit replies. Reddit's reply emails
  reach the owner's Gmail with the comment text, so no screenshots are needed.
  Playbook: `ops/reddit.md`. Gmail label `reddit-drafted` created; the seven
  r/XTerra reply emails so far are labelled.
- Scheduled task created but disabled (no Gmail connector; see above).
- Open branch: `design/filters-no-cutoff` (a293925e, sw jh-v188): filter
  panels no longer cut text off; waiting on the full layout run at 360, 402
  and 412 before merging.

## 2026-11-13 ~06:00 UTC filter panels and card share live (sw jh-v189)

- Merged 95e7d737: `design/filters-no-cutoff` and `design/card-share`.
- Filters (owner iPhone screenshot: "Using your loca", "Fron"): in the
  two-column grid the zip field and Years were too narrow. Zip and Years take
  a full row below 900 px; placeholder is "Near me"; selects wrap; location
  button is 44 px; Yards search placeholder "Yard or city". Four filter
  screens added to ui_no_truncation (none opened a filter panel before).
  Run: those screens at 320–1280 (9 widths), and every screen at 360/402/412,
  light and dark, 100% and 200%: 900 checks, 0 failures.
- Share: every car card (Cars, Alerts hits, Parts donors) has a share button
  beside Details; one line from 360 px, two lines at 320. New
  card_share_e2e.mjs (19 checks). Card screens re-run through
  ui_no_truncation at 320/360/375/390/402/1280: 168 checks, 0 failures.
- Checked on yardscout.io at 360, 402, 430. Not verifiable here: iPhone's
  own browser engine (Chromium only), in particular select wrapping.
- Web only; the apps need the next store release (owner's "ship"). The app
  build the owner is using has none of: search box, tab scroll, filters fix,
  card share.

## 2026-11-13 ~08:30 UTC notable trims merged (sw jh-v190); free-or-Pro open

- Owner asked whether the app can tell an Outback XT (and similar trims).
  `design/notable-trims` merged at 70dae8f4, then 50889cac:
  - Scan publishes `notableTrims` (make → model → trim words): words the parts
    table gates non-option rows on, plus a labels-only list
    (`NOTABLE_TRIM_LABELS`: Outback XT, Cherokee and Grand Cherokee Trailhawk,
    Liberty Renegade, Silverado Trail Boss). Labels add no part row and
    confirm nothing. 1,842 cars across 61 names on 11-13 data.
  - App: trim badge on cards and the car screen, a Trim filter once one model
    is picked, trim rows in the search box, `#cars=Make|Model|years|trim`.
  - Accuracy fix: a VIN decode that lists several trims ("Sport, R/T") no
    longer confirms a trim-gated part. 412 confirmations on 275 cars became
    "if equipped" (Veloster 276 → 2, Dakota 75 → 0, Jetta 74 → 24).
- **Open, owner's call:** `NOTABLE_TRIMS_FREE` in `docs/app.js`. Shipped
  `false` (Pro-only, like the trim line today). Hub recommends `true`. One
  line plus the two "ships false" test checks.
- Goes live with the first scan that STARTS after the merge (the 06:23 UTC
  scan started on 135f7204 and will not carry `notableTrims`).
- Regression on the merged tree: notable_trims unit and e2e, all scraper
  tests, car_search / card_share / tab_retap e2e, ui_no_truncation trim and
  filter screens at 320/360/390/402 in free, Pro-only and as-shipped modes.
- Open for parts: 21 Outbacks (2005–06) decode as "2.5GT" and look like XTs
  by VIN pattern; not badged. Tacoma, Ranger, F-150, Tundra, Frontier decodes
  never name TRD Pro / FX4 / etc., so those trucks cannot be badged from the
  VIN. The scraper still confirms an "R" gate from an "R-Line" decode.

## 2026-11-13 ~09:00 UTC owner: trims free; counter yes; overnight builds

- Owner: "Free and yes". `NOTABLE_TRIMS_FREE = true` shipped at b3005269
  (sw jh-v191). Trim alerts stay Pro.
- Owner asked for overnight work that improves the business. Two builders
  running in their own worktrees; hub reviews and merges each when it reports:
  - `seo/model-pages`: a permanent page per model, `/landed/<make>/<model>`,
    this week's set-outs by state plus what is on the lots; sitemap and
    internal links. Business plan priority 8.
  - `growth/narrowing-counters`: counts search-box picks against Filters
    picks, links and the trim filter, shown in the daily email (the owner
    decides on the search box from this in two weeks); confirmed Monday-email
    sign-ups by link.
- Still waiting on the owner: adding Gmail to the "Reddit reply drafts"
  scheduled task; the two U-Pull-R suggestions (reader off, reply watch on).

## 2026-11-13 ~08:15 UTC model pages merged and deployed

- `seo/model-pages` merged at 946f2b71; deploy-workers run 43391577905
  succeeded. `/landed/<make>/<model>`: 405 model pages across 40 makes on
  today's data (100+ on the lots, or 10+ set out this week). Week's set-outs
  by state, then yard; "on the lots now" by state; links from the make pages,
  the hub, car and yard pages, and the sitemap.
- Hub regression on the merged tree: site-proxy model_pages / junkyards /
  redirects / prices unit tests and e2e.sh (43/0); all scraper tests.
- Until a scan that started after the merge writes `docs/data/landed/`, model
  URLs answer 503 "Model page coming soon" (noindex) and nothing links to
  them. Scan dispatched by hand at 08:14 UTC on 946f2b71 (also carries
  `notableTrims` for the trim badges). Check-in scheduled to verify.
- For the owner once live: resubmit the sitemap in Search Console.
- Judgement call to confirm with the owner: model pages list the whole week
  nationwide, free (the make page stays capped at the newest 40).

## 2026-11-13 ~09:15 UTC narrowing counters and sign-ups by link live (sw jh-v192)

- `growth/narrowing-counters` merged at 0efca23d; deploy-workers run
  43392668897 succeeded (migration 0016 applied, then the API worker; site
  worker too). Hub regression on the merged tree: scorecard (128),
  funnel_counters, recap_signup, recap, ops_quiet units; funnel_events,
  car_search, recap_ask e2e; e2e-ops.sh. Live check at 390 px: search pick,
  Filters, all four tabs, 0 page errors.
- Daily email gains "How people narrowed the Cars list (7 days)": search box,
  Filters, link, trim filter; each at most once a day per device, website
  only until the next app release. First full 7-day line about 11-21; the
  owner decides on the search box from about 11-27.
- Confirmed Monday-email sign-ups now count under the link the person came
  through; the source is kept only while the sign-up is pending.
- Privacy page updated to say both (dated November 13, 2026).
- Still pending: the 08:14 UTC scan (trim badges and model page data).

## 2026-11-13 ~11:45 UTC overnight work verified live

- Scan 08:14 → 09:37 UTC succeeded on 946f2b71 (commit 69cfbf80): wrote
  `docs/data/landed/` (40 make files + index) and `notableTrims` (248 pairs).
- Model pages: `/landed/nissan/xterra` 200 (99 set out this week),
  `/landed/toyota/camry` 200 (811), `/landed/isuzu/trooper` 200 (7), unknown
  model 404. Sitemap lists 410 model URLs.
- Trims: `#cars=Subaru|Forester||XT` at 390 px near 95112 shows 4 cars, each
  with the XT badge; Filters shows Trim = XT; 0 page errors.
- All three overnight items merged: model pages, narrowing counters,
  confirmed sign-ups by link. Nothing left on a branch.
- For the owner: resubmit the sitemap in Search Console; read the updated
  privacy page.

## 2026-11-13 ~17:00 UTC Reddit reply task running

- Owner added the Gmail connector to "Reddit reply drafts" and ran it by hand
  at 16:31 UTC: 4 new r/XTerra replies drafted in 64 s, threads labelled.
  Hub enabled the schedule (next run 17:42 UTC).
- It runs on the session default model; that first run cost about $0.89 at
  list price. Asked the owner whether to move it to a cheaper model (a model
  change needs the owner's explicit ask).
- From the drafts: u/underling1978 reports the Android app is not available
  in Canada on Google Play. Country availability is set in Play Console (and
  App Store Connect), not in this repo; owner to check. u/cgarcusm could not
  find Xterra as an option: the Model list only offers models within range.

## 2026-11-13 ~17:45 UTC Canada: both stores sell in the US only

- Owner asked the hub to look into "app isn't available in Canada"
  (u/underling1978). New read-only workflow `store-availability.yml`
  (run 43470143537):
  - Google Play production: 1 country listed, US. CA, MX, GB, AU: no. The Pro
    subscription is already priced in 174 regions (CA: CAD 12.99).
  - App Store: available in 1 of 175 territories (US). The Pro subscription is
    sold in 1 territory (US), `availableInNewTerritories` false.
- Not changed. Play's API cannot set countries (Play Console only). App Store
  Connect's API can, but adding a country is the owner's decision; waiting.
- Reddit reply task moved to `claude-sonnet-5-5` at the owner's request.
- App: Filters now says "Only makes and models within N mi are listed. Widen
  the distance to see more." (2d580eb5, sw jh-v193), live and checked at 390 px.
- Test fix: notable_trims_e2e's "no trim list in the data" case assumed the
  checked-out data lacked `notableTrims`; it failed (3 checks) once the 09:33
  scan published the list. The test now strips the list itself. The hub
  pushed 2d580eb5 before reading that failure; the failure was in the test's
  premise, not in the app.

## 2026-11-13 18:02 UTC Canada added on the App Store (owner: "add Canada on the App Store, I'll do Play")

- New workflow `appstore-add-territory.yml` (dry run by default; never
  removes a country or changes an existing price). Dry run 43478521310, then
  apply run 43478608446:
  - App: Canada `available` false → true. Read back:
    `['CANNOT_SELL', 'PROCESSING_TO_AVAILABLE']` (Apple is rolling it out).
  - Pro (`yardscout_pro_monthly`): sold in USA → CAN and USA. Its Canadian
    price already existed (CAD 11.99, Apple's equalised price); not changed.
- Google Play: the owner is adding Canada in Play Console (the API cannot).
- To verify later: dispatch `store-availability.yml`; expect App Store CA=yes
  for the app and the subscription, and Play CA=yes once the owner has done it.
- Side finding: the App Store subscription has no introductory offer in any
  territory. If the Pro sheet's "$1.99 first month" is meant to apply on
  iPhone, that needs a look (growth workstream).

## 2026-11-13 ~18:25 UTC no first-month discount exists anywhere

- Owner: "does android have the first month being cheaper? If so stop that."
  Checked: Google Play base plan `monthly` has no offers (play-status run
  43481427692: offers endpoint HTTP 204); App Store has no introductory offer
  in any territory; the web checkout (`backend/src/billing.js`) has no
  built-in discount, only `allow_promotion_codes`. Nothing to stop.
- Correction: the hub told the owner earlier that Google Play had a
  first-month offer. That was not verified and was wrong. The "$1.99 first
  month" wording in `ops/business-plan.md` came from the funnel audit; the app
  shows an intro price only when a store reports one (`introOfferText`).
- Play country availability: the Android Publisher API only reads it. The
  owner could not find the screen; hub gave the Play Console path.

## 2026-11-13 ~18:45 UTC Canada on both stores

- Owner added Canada in Play Console. `store-availability.yml` run
  43486697066: Play production lists CA and US (Pro buyable at CAD 12.99);
  App Store app and Pro both show CA and US (Pro CAD 11.99).
- The Play API shows the saved setting, not whether Google has finished
  reviewing or rolling it out; same for Apple's "processing" state earlier.

## 2026-11-13 ~22:40 UTC iOS 1.12.15 live; first scorecard read

- asc-status run 43519623862: iOS 1.12.15 (37) is READY_FOR_SALE. Android
  1.12.15 (38) is completed on Play production.
- First scorecard (13:07 UTC email, week Nov 6–12, fixed counting from Nov
  12 only): web first visits 35 on Nov 12 (117 in 7 d); reddit / xterra 20
  tagged visits in the post's first hours, 0 watches, 0 emails, 0 checkouts;
  Pro sheet opened 32, checkout taps 8 (iPhone 7, web 1), purchases 0;
  6 paying subscribers (App Store 4, Play 1, web 1).
- Gap: the app counts a checkout tap and a purchase and nothing between
  (cancelled, pending, not completed, error, product failed to load). Builder
  on `growth/checkout-outcomes`; hub reviews and merges. The apps need a
  store release for it.
- Next app release would carry: search box, tab scroll, filter fix, card
  share, trim badge and filter, the model-range line, narrowing counters,
  checkout outcomes. Needs the owner's "ship".

## 2026-11-13 ~23:15 UTC checkout outcomes live on the web (sw jh-v194)

- `growth/checkout-outcomes` merged at e2601c12; deploy-workers run
  43522743494 succeeded; site serving jh-v194. No native file, no migration.
- Each checkout attempt now ends in exactly one counter: bought, cancelled,
  pending, incomplete, failed (by class), web "paid, not confirmed"; plus
  "store product did not load" when the Pro sheet opens in the apps. The
  scorecard's item 4 shows "of N checkout taps: …" with "no result recorded"
  for the rest. Counting version is now 4.
- Hub regression on the merged tree: funnel_counters (139), scorecard (155),
  recap_signup, ops_quiet units; funnel_events, car_search, card_share e2e;
  e2e-ops.sh. All pass.
- The apps report outcomes only after the next store release (owner's
  "ship"). The release is now ready to cut: nothing else is pending on a
  branch.
- Plugin limit noted by the builder: both native Purchases plugins reject
  with text only, so several store errors share one "store" class. Splitting
  them needs a small native change in a later release.

## 2026-11-13 ~23:50 UTC pull sheet: hours and directions link (sw jh-v195)

- Owner asked whether yard hours can be seen from the pull sheet. They could
  not: the app collects no yard hours, and the pull sheet showed only the
  yard name and its cars.
- 4d68a992: each yard on the pull sheet gets an "Hours and directions" link
  that opens the yard by name, city and state in Maps (Apple Maps in the
  iPhone app, Google Maps elsewhere). No hours are stored or claimed by us.
  card_share_e2e extended (21 checks pass); ui_no_truncation pull-sheet
  screen at 320/360/390/402/1280: 20 checks, 0 failures.
- Not built: real opening hours shown in the app. That needs a per-chain
  source for hours (Pick-n-Pull, Pick Your Part and Pull-A-Part publish them
  per store) and a rule for holidays; owner to decide.

## 2026-11-14 ~00:20 UTC yard cards: hours and directions link (sw jh-v196)

- Pull-sheet link confirmed live at 390 px (a page load with the new code
  shows it; the CDN served a mix of old and new app.js for some minutes
  after the push, so two earlier live checks saw the old file).
- Owner asked for the same on the yard cards. 86f91170: every yard card on
  the Yards tab has "Hours and directions" under the town, opening the yard
  in Maps; tapping it does not open Walk the rows. card_share_e2e now 24
  checks; ui_no_truncation yards, yards-premium-list and pull-sheet at
  320/360/390/402/1280: 60 checks, 0 failures.
- Lesson for live checks: wait for a page load that actually has the new
  code (check for a new function or class in the page), not for sw.js or a
  cache-busted fetch.

## 2026-11-14 ~16:35 UTC status for the owner

- Yard-card "Hours and directions" link confirmed live (all 7 cards near
  84101, 0 page errors).
- Scorecard 13:07 UTC (week Nov 7–13; fixed counting from Nov 12): web first
  visits 37 on Nov 13 and 35 on Nov 12 (about 14 a day before); Android app
  first visits 12 on Nov 13; watches created 9 in the week (web 2, iPhone 2,
  Android 5); reddit / xterra 34 tagged visits (post 27, comment 7), 0
  watches, 0 emails, 0 checkouts; chatgpt.com 5 visits, 1 watch; Pro sheet
  opened 54, checkout taps 9 (iPhone 8), purchases 0; subscribers 6.
  First day of narrowing counts (website): search box 4, Filters 5, link 3.
- Reddit reply task: running hourly on Sonnet; the 15:42 UTC run found
  nothing new and ended in 7 s.
- Waiting on the owner: "ship" for the next app release (iPhone checkout
  outcomes only exist from a new build); U-Pull-R reader off and reply watch
  on; which parts checks and which post next.

## 2026-11-14 ~17:30 UTC Cloudflare daily limit passed; cause found and cut

- Cloudflare warned at 15:57 UTC: 90% of the free plan's 100,000 Workers
  requests a day. New read-only workflow `cf-usage.yml` (run 43618208468):
  113,751 requests today by 16:55 UTC (yardscout-api 73,177, yardscout-site
  40,574). 11:00–14:45 UTC ran at 23–25k an hour against about 2k normally.
  The site and API were still answering at 16:53 and 17:25 UTC.
- Cause (hub's change): the model pages published 11-13 link to every car set
  out that week (~28,000 car pages). A crawler walked them. Each /car/ page
  cost 1 site-worker request + 2 API-worker requests (`/v1/vehicles/<vin>`
  and `/v1/yards`); `cf.cacheTtl` on a fetch to another Worker saves nothing.
  The crawler's identity is unknown: the deploy token cannot read zone
  analytics.
- Fix 4362f843 + 1ae8d5e9, deploy run 43618471158: robots.txt disallows
  /car/ for crawlers (link-preview bots still allowed); car links on model
  and make lists are rel=nofollow; `apiJson` keeps API answers in the site
  worker's edge cache and the yard list in memory. Checked live: robots.txt,
  99 nofollow links on the Xterra page, a real car page renders (200).
- The hub's own live checks today were a few thousand requests at most.
  Standing rule from now: no polling loops against yardscout.io; one page
  load per check.
- yardscout.io is served entirely by the site Worker (it proxies GitHub
  Pages), and the apps load data from yardscout.io: at the limit, site, apps'
  data, alerts and checkout all stop until 00:00 UTC. Owner asked to upgrade
  to Workers Paid ($5 a month). Follow-ups if not: render car pages from the
  static data files (1 request each), serve /data/ without the Worker.
- 1.12.16 release: owner said "ship" at ~16:35 UTC. Held for the pre-release
  layout run and this incident; not dispatched yet.

## 2026-11-14 17:03 UTC 1.12.16 dispatched (owner: "ship")

- Pre-release, all on main at ac24bcb5 (sw jh-v196):
  - every `backend/test/*_unit.mjs`, the browser e2es (funnel_events,
    car_search, card_share, notable_trims, tab_retap, model_years,
    no_pick_models, share_watch, recap_ask, app_promo), browser_e2e.py,
    site-proxy units: pass. tab_retap failed once while the layout suite was
    running beside it and passed alone.
  - Parts tab: pf_ux, interchange, yaris_coverage and part_finder e2e pass.
  - ui_no_truncation, every screen at 320 and 390, both themes, 100% and
    200%: 616 checks, 0 failures.
  - Two test faults found and fixed (009fcc44): pf_guards_unit lacked stubs
    for the new card pieces (broken since 11-13, never run); part_finder_e2e
    hardcoded "1" E46 M3 on the lots.
- Dispatched straight to production, as on 11-12: release-android run 29
  (version_name 1.12.16, track production), release-ios run 40
  (marketing_version 1.12.16, submit=true; build number = run number 40).
- Correction: the times "17:25/17:30 UTC" in the entry above were wrong;
  those checks were made at about 16:55–17:00 UTC.
- Still to confirm: both runs finish; asc-status and play-status.

## 2026-11-14 17:15 UTC Cloudflare: staying on the free plan

- Owner cannot pay for Workers Paid ("I can't afford the $5"). The site must
  stay inside the free 100,000 Workers requests a day. Do not suggest the
  paid plan again unless the owner raises it.
- Owner asked whether freezing the inventory until the reset would help. It
  would not: scans are not what is counted; visitors, apps and crawlers
  loading pages and data files are.
- cf-usage at 17:11 UTC: 114,194 today; site and API still answering (200).
  The 17:00 hour is running at about 1,200 an hour, with site and API about
  equal (it was 1 site to 2 API before the fix), against 23–25k an hour at
  the peak.
- Free levers, in order: (1) done: robots.txt, nofollow, API answers cached
  in the site worker; (2) owner: Cloudflare dashboard, Security → Bots →
  "Block AI bots" and "Bot Fight Mode" (blocked requests never reach a
  Worker, so they are not counted; Bot Fight Mode may also block the scan's
  /_upstream fallback for Indy U-Pull-It, which would show as "re-serving
  last copy"); (3) hub, not urgent: the app loads /data/ files straight from
  GitHub Pages instead of through the Worker (web first, apps at the next
  release), and car pages render from the static data files.
- Check tomorrow midday with `cf-usage.yml` (it reads Cloudflare's analytics
  API and costs no Worker requests).

## 2026-11-14 17:20 UTC 1.12.16 accepted by both stores

- release-android run 29 (43618947678) and release-ios run 40 (43618949981)
  both succeeded. asc-status 43619959666: 1.12.16 build 40
  WAITING_FOR_REVIEW, submitted 17:13 UTC. play-status 43619961360:
  production 1.12.16 (39), status completed, rollout 100%.
- `ops/release.md` table updated.
- After approval: the apps report narrowing and checkout outcomes; the
  scorecard's "website only until the next app update" lines go away as
  each platform's first v4 event arrives.

## 2026-11-14 ~19:00 UTC coverage requests triaged (owner sent the four emails)

| Request | What it is | Done |
|---|---|---|
| U-Pull-It, "Kennewick, WA" (Nov 12, left an email) | Already tracked since 2026-10-28 (`upullitwa`, 853 cars; Pasco and Yakima too). The Yards tab lists only yards inside the chosen distance, so a covered yard farther out looks missing. | Gmail draft reply to the requester (owner sends). Yard request form now checks the full yard table first. |
| 2003 Chevrolet Colorado, alternator (Nov 11) | No such car: the Colorado starts in 2004. The Parts model list offers a nameplate one year either side of its known span, and the empty state then said "ask us to add it". | Empty state now says the year was never seen, names the span, and offers "search 2004 instead" (2004 has donors). No ask link in that case. |
| 2003 Audi A3, alternator (Nov 7, "Can you add this family?") | Same cause (US A3 on the lots is 2006 to 2019; 2003 is no longer offered). The real gap behind it: the 2006+ A3 has no alternator coverage at all. | Noted in `ops/interchange.md` as a demand signal. Not built. |
| U-Pull R Parts (Nov 3, left an email) | The yard that refuses the scraper. Follow-up to its CTO sent by the owner 2026-11-12; no reply known. | Nothing new. The requester has not been told; their address is only in the admin coverage list. |

Web change: sw `jh-v197`, test `backend/test/coverage_gaps_e2e.mjs` (21 checks).
Apps get it with the next store release (needs a new "ship").

Open suggestions made to the owner:
- The digest email should mark a yard request that matches a tracked yard
  ("already tracked: <name>") so it is not read as a gap. Not built.
- `/junkyards/wa` is a redirect to `/junkyards/washington`; the Washington
  page data is correct (8 yards). An earlier hub check that found "0
  mentions" had read the redirect, not the page.

## 2026-11-15 ~00:45 UTC owner: "Update? Do what you think"

Status checks (all read-only):
- iOS 1.12.16 (40) READY_FOR_SALE. Play production 1.12.16 (39) completed.
- Cloudflare: 2026-11-14 ended near 122,000 Workers requests (over the
  100,000 limit, all from the 11:00 to 14:00 UTC crawl). Since the fix:
  18:00 to 24:00 UTC ran 700 to 1,500 an hour, and before the crawl the
  normal rate was 1,400 to 3,100 an hour, so the fix also cut the everyday
  load. Zone analytics still unreadable (token lacks zone analytics read).
- Reddit drafter ran at 23:43 UTC, succeeded. The owner's r/projectcar post
  ("My first try at actual bodywork") is drawing many replies; the drafter
  is labelling them hourly. Suggested to the owner: draft only for questions
  on personal posts, to save usage. Not changed.

Built and pushed (85f20360, sw `jh-v198`, Worker deployed 00:35 UTC):
- **Lost yard requests (bug found while reading the Worker).** The in-app
  Yards form sent no `city`; the Worker refused any yard request without
  ", ST" in the note, and the app showed "check your connection". The hint
  even said "Only the yard name is needed". Now: the Worker accepts a zip or
  a website as the place (this also fixes the shipped 1.12.16 apps for anyone
  with a zip set); the app sends `city`, shows the server's reason on a 400,
  and the hint asks for city and state. How many requests were lost is
  unknown (refusals are not stored).
- **Digest tag.** A yard request that matches a tracked yard is tagged
  "ALREADY TRACKED: <yard> (N cars)" in the coverage digest
  (`trackedYardTag` in `backend/src/coverage.js`).
- Tests: `backend/test/coverage_gaps_e2e.mjs` 26/26,
  `backend/test/coverage_tracked_unit.mjs` 14/14, `e2e-coverage.sh` 27/27.
  Not exercised against production (a live POST would put a fake request in
  the owner's digest).

Next for the hub: read iPhone checkout outcomes once 1.12.16 has a day of
use (the "8 Subscribe taps, 0 purchases" question); first full 7-day
narrowing line about 2026-11-21.

## 2026-11-16 ~07:05 UTC owner: "I want to get more users" (saw $48 in subs)

Read from the 2026-11-15 daily email (week Nov 8 to 14) and local checks:
- **Reach is small.** 188 new visitors in the week (web 141, Android app 33,
  iPhone app 14). Tagged: reddit/xterra 37, chatgpt.com 9, facebook 2.
  One purchase recorded (Android, Nov 14; Google's report had not confirmed it
  by the Nov 15 count). Paying: 5 (App Store 3 as of 11-14, down from 4
  earlier in the month; Play 1 as of 11-13; Stripe 1).
- **Web visitors leave without a hook.** 141 first web visits: 3 watches, the
  Monday email offered 2 times, 0 addresses, 4 store-link taps. Android app:
  10 watches from 33 new. reddit/xterra: 37 visits, 0 watches. chatgpt.com:
  9 visits, 2 watches.
- **Why (hub screenshots, fresh phone browser, the Reddit link):** the zip
  card never names the car the link was for; after the zip the first car
  card starts at y=685 of 844, under the "How to read this" note, the stat
  tiles, the search box, the filter row and the watch strip, and behind the
  app banner. The email ask is two steps and sits in a 30 s toast.
- **iPhone "10 checkout taps, 10 cancelled"** all fell on Nov 14, the day
  build 40 was in App Review, and only builds that report outcomes (1.12.16)
  are counted there. Hub's reading: Apple's reviewer and testers, not
  customers. Same doubt for Android's "store price not loaded" x3 on its
  upload day (Play pre-launch devices). No conclusion about price or the
  purchase flow can be drawn from this week. Idea for the next app release:
  do not count sandbox (TestFlight, App Review) or test-lab sessions.
- **Who is engaged:** most watched Toyota 4Runner 14 of 88 watches (may
  include the owner's own), Pickup 4, Tacoma 4; most searched car Lexus
  GX 470 (18). This week's arrivals (scan 2026-11-16 05:14Z): 4Runner 47 in
  20 states (3rd gen 32, 4th gen 12; 4x4 18, 2WD 27), Tacoma 29, Sequoia 46,
  Toyota Pickup 13, GX 470 1.

Started: builder on branch `growth/first-view` (worktree, web only): zip card
names the car from a cars link; on phones the accuracy note moves below the
first car on a first visit; the app banner waits for scroll or 30 s; the
watch strip takes the Monday-email address in one step. Hub reviews, merges,
and shows the owner before/after. See `ops/growth.md` when it reports.

Told the owner (plan): 1. the landing fix above; 2. next post is the
4Runner list (hub writes it on the day), and the YardScout link goes in the
Reddit profile because the personal bodywork post drew far more replies than
the Xterra list; 3. a Search Console screenshot (Performance, 28 days, Pages)
to judge the model pages, which is the tabled model-pages topic raised again
as agreed; 4. offered, not started: a printable QR flyer for yard counters.
Open from before: Kennewick draft, Reddit drafter limit, U-Pull R requester.

## 2026-11-16 ~07:20 UTC owner: "Do everything you think" (more Pro users, more people using it; main page, look, features, flow all open)

Standing rule 1 still applies: a store release needs an explicit "ship".

Hub's read after screenshots of every main screen (phone and desktop, local):
the screens work once someone is in (Cars list, car card, Parts, Pro sheet);
the weak part is the first minute. So the work is flow, not a new look.
- Brand-new desktop visitor: "Where are you?" card, then stat tiles reading
  "CARS 0 / NEW THIS WEEK 0", no sentence saying what the site is.
- Yard pages' "Search this yard in YardScout" and city pages' "Search near
  your zip" both land on the generic zip card (no yard or city carried over).
  Model pages already carry the model (`#cars=`).
- No rendered-page button carries a source tag, so visits that arrive from
  search pages are invisible in the scorecard.
- Web Alerts tab never mentions the Monday email.

Done this hour:
- `/geo` on the site Worker (b72ebe6e, `backend/site-proxy/src/geo.js`, 13
  checks): the visitor's approximate area from the location Cloudflare
  attaches to the request; one decimal, US and Canada only, nothing stored,
  never cached. The app does not call it yet.
- Reddit drafter prompt: in threads that are not YardScout threads (the
  owner's personal posts) it drafts only for questions or parts/junkyard
  talk and lists the rest in one line. Same schedule, same model.

Queued (task list #50 to #53):
1. Review and merge `growth/first-view` when the builder reports.
2. Wave 2, same builder: first visit shows cars near the guessed area with
   the zip field beside it (a guess is never a watch centre; privacy text
   updated in the same change); national numbers instead of zero tiles;
   `#yard=` and `#near=` intents and the rendered pages' buttons using them;
   internal source tag `page/<type>` that never replaces an external source.
3. 4Runner post on the day the owner posts; Reddit profile link (owner).
4. Next app release batch, then ask for "ship". Listing text (D7) already
   went out with 1.12.15. Add: do not count sandbox or test-lab sessions.

Asked the owner, not decided for them: D2, one free instant alert on one
watch within a short radius (two $3.99 rivals give one). It gives away part
of Pro, so it stays the owner's yes or no.

## 2026-11-16 ~07:30 UTC owner on the free instant alert (D2): "Do what u think", asked how one free user is told apart

Owner added the YardScout line to their Reddit profile.

Answer given: the free tier has no accounts; the server knows app installs
(device id plus push token, `backend/src/devices.js`), which is how the
5-watch free limit already works. An alert can only reach that phone, so the
limit is one instant watch per phone; a reinstall is the same phone. Web is
left out because email addresses are easy to multiply.

Decision recorded: build it into the next app batch (task #54), apps only,
one watch, cars within 50 mi of the watch centre, opt-in by a new field so
no shipped build changes behaviour. It reaches users only with a release,
which needs "ship"; the release summary must spell it out so the owner can
still say no. Today's free tier for reference: up to 5 watches within
250 mi, one Monday summary push, one check-in push after the first watch.
Pro: up to 20 watches, any distance, trim and 4WD filters, a push on every
scan that finds a match, sale-day pushes.

## 2026-11-16 ~07:50 to 08:15 UTC photos (owner: "the more photos the better", then "Do it")

- Count this morning: 47.3% of cars show a photo in the list, 9.7% only on
  the car screen, 42.8% none (details and the table in `ops/yards.md`).
- Within the old rules (dc37bbab): six sources of 400 to 700 KB moved onto
  list cards; Pull-A-Part lookups 500 a scan at 6 s. Scan dispatched 07:46.
- **Owner decision, recorded:** asked whether a free image-resizing service
  may shrink big photo files, changing the 2026-11-06 "no proxying" rule, the
  owner answered "Do it". Built for the five big-file sources the service
  can fetch (5e2e5198, sw `jh-v199`); four sources whose host refuses the
  service stay direct. `CLAUDE.md` now carries the rule and its limits.
- Not taken as approved: user-uploaded photos (mentioned as a later option).
- Follow-up: second scan queued 08:07 UTC publishes the resized addresses;
  then recount and look at a live card.

## 2026-11-16 ~08:20 UTC free instant alert merged (fa2ec748, sw `jh-v200`)

Owner: "Do it and ship!" (2026-11-16). Hub read the server diff and the app
diff before merging. What it does is in `ops/growth.md` (builder's section).

- **Inactive until the app release.** The API pushes instantly for a free
  device only when that device flagged a watch, and only builds with the new
  code send the flag. Pro devices are dispatched first, unchanged; free
  instant pushes use what is left of the 25 sends per scan.
- **Deploy order is satisfied by this merge:** Deploy Workers runs on the
  push and applies migration 0017 before any store build exists.
- **Held on the website:** two sentences in `docs/index.html` that describe
  the apps' free tier keep their old wording until the new version is live
  in both stores (comments in the file carry the new text; the check in
  `free_instant_e2e.mjs` expects the held wording). The apps set their own
  text in code, so the release is not affected.
- **Store listing lines to correct with the release** (builder's list):
  `fastlane/metadata/en-US/description.txt` and
  `android/en-US/full_description.txt` lines 24 and 28, and
  `android/en-US/pro_subscription_benefits.txt` line 1. All in task #53.
- **Test fixed on the way:** `backend/test/e2e.sh` had been failing on main
  ("radius filter did not narrow (0 of 6)") because it hardcoded the first
  yard's location and the scan's yard order changed. It now reads the
  location from the seeded directory. 39 of 39.
- Tests on the merged tree: e2e-devices, e2e (39), e2e-ops, free_instant_e2e
  (30), coverage_gaps (26), alerts_first, photo_policy, illo, pf_guards,
  scorecard, card_share, funnel_events, recap_ask, share_watch, tab_retap,
  and ui_no_truncation on four screens at 320 and 390 (32 checks): all pass.
- Left for later, from the builder's notes: `e2e-devices.sh` leaves its
  local server running after it exits (a second run on the same port fails);
  the privacy page does not list saved cars among what the server stores for
  a device (predates this work).

## 2026-11-16 10:41 to 10:50 UTC check-in: photos verified; landing-fix builder had stopped

- **Photos verified** (table in `ops/yards.md`): list photos on the website
  47.3% to 56.2%; live Pull-A-Part cards load from the resizing service at
  about 44 KB each; Pull-A-Part lookups ran 500 in the scan, no errors.
- **The first landing-fix builder stopped at 07:10 UTC**, minutes after it
  started: two small edits in its worktree, nothing committed or pushed, no
  completion notice. The hub only saw it at 10:41 (no agent listed, branch
  never pushed). About three and a half hours lost on that piece. The owner
  was told.
- **Restarted as two builders (Opus, worktrees), ~10:47 UTC**, each told to
  commit and push after every numbered item:
  - `design/cars-feed`: the feed from `ops/design.md`, with the old
    landing-fix items that belong to the list folded in (note below the
    first row of tiles, app banner waits, one-step Monday email in the
    strip).
  - `growth/no-gate`: first visit shows cars near a guessed location
    (`/geo`) instead of the zip card; the zip card names the car when it
    does show; `#yard=` and `#near=` links; search-page buttons use them and
    carry `utm_source=page`; an internal source never replaces an outside
    one.
  - Ownership split so the two do not edit the same functions: the list,
    car screen, strip, note and banner belong to the feed; the zip card,
    zip chip, location storage, link parsing, `ATTRIB` and the site Worker
    buttons belong to no-gate. Merge note for the hub: the feed's email
    strip must treat a guessed location as "no zip" (no-gate exposes a
    helper for that).
- **Guard against another silent stop:** a check-in every 40 minutes looks
  at both branches (`trig_01UQ5GHubAnWVnxHKb3Smjmi` first, 11:29 UTC).

## 2026-11-16 11:40 UTC no-gate merged (4e02c968, sw `jh-v201`)

Builder finished in 42 minutes; hub read the app, site and server diffs and
the screenshots, then merged. Details in `ops/growth.md` ("No zip gate on
the first visit").

- First visit with no saved place: one `/geo` question, then the Cars list
  near the guessed city with "That is a guess from your internet connection"
  and the zip field beside it. Never saved, never a watch or Monday-email
  centre (helpers `locationIsGuess()`, `ownCenter()`, `needOwnZip()` in the
  app script).
- `#yard=` and `#near=` links; the search pages' buttons use them and carry
  `utm_source=page`, which never replaces an outside source. All tagged
  buttons are `rel="nofollow"`; `robots.txt` disallows the tagged address.
- New counters `first-view-guess` and `guess-replaced` in the daily email;
  the per-link scorecard line gains "entered a zip".
- Hub change: a yard link's line reads "Showing the cars at <yard>" while
  the Yard filter is on it.
- Tests on the merged tree all pass (list in the commit message).
- **For the feed merge (hub):** the feed's email strip must use
  `needOwnZip()` / `locationIsGuess()`; the car screen's "N mi from <zip>"
  should read `zip && !_tempPlace`; under a guess the summary says "Cars
  near you" and the Yards tab centres on the guess with no label.
- Noted by the builder, not changed: on phones the page script rewrites
  "Open in YardScout" / "Open the app" to app paths, so the source tag rides
  only on desktop and the Android browser fallback; car links on yard pages
  and city "Newest arrivals" lack `rel="nofollow"` (`/car/` is disallowed in
  the robots file regardless).

## 2026-11-16 11:50 UTC no-gate confirmed live

One fresh page load of yardscout.io with nothing stored (phone size): the
new code was served, `/geo` answered 200 `no-store` with a city, the line
read "Showing yards near <city>. That is a guess from your internet
connection." with the zip field and "Use my location", the zip card was
hidden, 400 cars rendered, and neither `jh_zip` nor `jh_gps` was written.
The Kennewick yard page's "Search this yard in YardScout" button now points
at `/?utm_source=page&utm_medium=yard&utm_campaign=<slug>#yard=<yard>` with
`rel="nofollow"`. Deploy Workers succeeded for 4e02c968.

Still true on the live site until the feed merges: on a phone the first car
sits below the guess line, the "How to read this" note, the three stat
tiles, the search box and Filters, and the app banner shows at once.

## 2026-11-16 13:16 UTC Cars feed merged (c5d2b414; main at 29376618, sw `jh-v202`)

Builder's branch `design/cars-feed` (6d08b0bf) merged with main, plus hub
fix-ups, on a side branch (`hub/feed-merge`) while the regression ran; main
was moved to it only after everything passed. Design and build notes:
`ops/design.md` ("Cars feed").

- What changed for a visitor: the Cars tab is a grid of photo tiles (2
  columns on a phone), a tile opens the car screen, chips for All / New /
  This week / makes / models, endless scroll, "since your last visit", share
  a list, the "How to read this" note after the first row, the app banner
  later, the Monday email asked for in the watch strip.
- Hub fix-ups where the feed met the no-gate first visit:
  - under a guessed place the strip asks for the zip in the same step as the
    email; watch and sign-up are centred on that zip, never on the guess
    (`stripZipFirst`, test `backend/test/strip_guess_e2e.mjs`);
  - on a phone the watch strip follows the first row of tiles
    (`feedPlaceStrip`): a model link on a first visit showed no car on the
    first screen, now two;
  - the guess line is one sentence and a "Change" button that opens the zip
    field and "Use my location": first tile 84 px higher at 390 px;
  - a long-listed car says "Listed N days" on its tile (the tile had dropped
    the old card's notice; found by the full layout run); the whole notice
    stays on the car screen and in the row view;
  - "Set out <date>" no longer breaks after "Set" on a tile;
  - yard request: shorter placeholder (cut at 360 px, large text).
- Regression on the merged tree, all pass: 52 test files (browser e2e incl.
  cars_feed 96 checks, no_gate, strip_guess, free_instant, map_regions; all
  units; site Worker units; the five Parts-tab and freshness Python e2es;
  three scraper photo tests), then 51 of them again after the tile fix
  (map_regions left out: it tests map pins); the six API suites (e2e.sh
  39/39, e2e-ops, e2e-devices, e2e-coverage 27/27, e2e-email, browser_e2e
  17/17); `ui_no_truncation` every screen at all six widths, both themes,
  100% and 200% text: 2,184 checks, 0 failures.
- Layout-check fixtures brought up to date: the heavy photo source now
  publishes a resized copy (tap-to-load is tested with the copy taken out; a
  new screen covers the resized car-screen photo); `cards-mixed` no longer
  needs a natural run of photo-less cars; `r5-car-life` looks past the first
  40 tiles.
- Store files, committed, nothing sent yet: listing text for the free
  instant alert (f262671d), all twelve screenshots regenerated (29376618;
  the Cars slide is taken at 25 mi).
- Not checked: no Safari/WebKit engine in this environment. The new CSS and
  script were read for anything iOS 15 lacks: `:has()` and `:focus-visible`
  are used for cosmetics only (iOS 15.0 to 15.3 ignore those rules), no
  regex lookbehind, no `.at()`.
- Housekeeping: 22 finished builders' worktrees removed (clean and already
  in main); the session disk was at 94%.

## 2026-11-16 13:28 UTC feed confirmed live; 1.13.0 dispatched (owner: "Do it and ship!")

- Live check at 13:28 UTC, ten minutes after the push (Pages and Deploy
  Workers both succeeded at 13:17): one fresh phone-size load of
  yardscout.io with nothing stored, and one of a `#cars=Toyota|4Runner`
  link. Both served the new shell (`jh-v202`), no page errors. First visit:
  the guess line with "Change" (zip field closed), no zip card, 40 tiles,
  first tile at 378 px, two whole tiles and their photos on the first
  screen, nothing written to `jh_zip` / `jh_gps`. Model link: the four
  4Runners near the guessed city, "Share this list", then the Monday-email
  strip with its zip field under the first row.
- Before/after screenshots sent to the owner.
- Dispatched straight to production, as on 11-12 and 11-14, from main
  67fa5d2b: release-android run 30 (43876161947; version_name 1.13.0, track
  production) at 13:28:56 UTC; release-ios run 41 (43876188232;
  marketing_version 1.13.0, submit=true, build number = run number 41) at
  13:29:06 UTC. The iOS submit carries the corrected listing text and the
  six regenerated screenshots.
- Release notes (both stores): new Cars photo grid with one-tap filters;
  cars near you as soon as the app opens; free alerts on one watched car
  within 50 miles; more yard photos; share a list; what was set out since
  the last visit.
- Still to do: confirm both runs; asc-status and play-status; then the Play
  listing (`store-listing.yml`: text and screenshots;
  `play-subscription-listing.yml`: benefit line) once the Android build is
  accepted; when BOTH stores show 1.13.0 live, flip the two held website
  sentences in `docs/index.html` and the check in
  `backend/test/free_instant_e2e.mjs`.

## 2026-11-16 13:40 UTC 1.13.0 accepted by both stores

- release-android run 30 (43876161947) succeeded 13:33 UTC; play-status
  43876886357: production 1.13.0 (40), status completed, rollout 100%.
  Google's review still stands between that and users.
- release-ios run 41 (43876188232) succeeded 13:39 UTC; asc-status
  43877889988: 1.13.0 build 41 WAITING_FOR_REVIEW, submitted 13:39 UTC,
  build processing VALID. Released automatically on approval. The listing
  text and six new screenshots went up with it.
- Scorecard (180222b2, Deploy Workers 120 succeeded 13:37 UTC): the
  narrowing line counts the feed's chips ("search box · chips · Filters ·
  link · trim filter").
- NOT done yet, on purpose: the Play listing (`store-listing.yml`,
  `play-subscription-listing.yml`). Play publishes listing text apart from
  the app, and the new text says free gets one alert within hours, which is
  true only once 1.13.0 is what people install. Send both after 1.13.0 is
  live on Play; until then the old listing is still true, only incomplete.
- Same trigger for the website: when BOTH stores show 1.13.0 live, flip the
  two held sentences in `docs/index.html` (the comments beside them carry
  the new text), flip the check in `backend/test/free_instant_e2e.mjs`,
  bump the sw cache.
- 4Runner post: `tools/landed_post.py Toyota 4Runner --gens ...` writes the
  "what landed" list (fe9f77c2; how to use it is in `ops/reddit.md`). As of
  the 10:22 UTC scan, 48 4Runners were set out Nov 9 to 16 in 21 states and
  provinces, 18 confirmed 4x4. A draft went to the owner; run the tool again
  on the newest scan right before they post.
- Follow-up scheduled: `trig_016dADedHXNCLcakiqQW9irq`, 2026-11-17 15:00
  UTC (store status, then the held website sentences and the Play listing).

## 2026-11-16 ~16:00 UTC owner's first look on an iPhone (three screenshots)

Owner: "Like the format, lack of pictures is annoying. For pro isn't see
what you'd save and see what parts are worth the same? Should we make /
promote alerts as the main flagship feature? Don't want to mess up the
shopping/scrolling experience with too much. But also want to direct folks
towards [Pro]." The screenshots are the first real-Safari view of the feed:
tiles, chips, the note after row one and the car page all render as tested.

**Changed (a373ccdf, sw `jh-v203`, website only until the next app release):**
- Free car page: one Pro box for the prices, under the parts ("See what
  each part is worth", gate `part-value`). The second one above the parts
  ("See what you'd save on this car", gate `card-value`) came over from the
  old card when the list became tiles; it is gone. Nothing renders
  `card-value` now.
- "fits 2013–2013" reads "fits 2013" (`fitsText`; 170 part rows).
- Newest-first list: within one set-out day, cars whose photo shows in the
  list come first, then the nearest yard (`listPhotoFlag`). It was the order
  of the data files, so one yard's batch filled the first screens.

**Photos, measured on the 13:47 UTC scan** (script in the session
scratchpad; counts only): nationwide 56.0% of cars show a photo in the
list. Within 100 mi of Salt Lake: 15%. Pick-n-Pull Salt Lake City 98%;
Pull-N-Save Salt Lake City and Springville (2,710 cars) about 1%, because
the photo checks are paused (owner, 2026-11-07); Tear-A-Part (1,558) and
Utah Pic-A-Part (1,710) publish no per-car photo. The owner's screenshot
was a 50-car batch set out 11-15 at Utah Pic-A-Part Ogden (Premium), so the
new order does not change that screen. Nationwide the cars with no list
photo sit at: Pull-A-Part 26,781 (lookups running, 500 a scan), Pull-N-Save
11,352 (paused), Jalopy Jungle 6,476 (none on site), LKQ 5,690 (no photo
id in the feed), then chains whose sites show none.

Also seen: about 7,000 YardSmart photos (U-Pick-It AZ, U-Pull-It IA/NE,
Genesis, Chuck & Eddie's, and the Bessler's / Chesterfield / Bluegrass
VinPlus brands) are missing today compared with 11-09. Their own feeds have
been frozen since 11-13/14 (the scan's STALE YARD lines), so the signed
photo ids in them have lapsed and the scraper rightly drops them. Source
side; they come back when those feeds refresh. Check in a later scan.

**Pro prompts, 14 days (usage-stats 43900005790; aggregate counts):** Pro
sheet opened from the header button 49, distance limits 37 (nationwide 18,
500 mi 15, any distance 4), the two price boxes 33 (18 + 15), alert prompts
12, the free sample note 8. Checkout started: header 15, nationwide 7,
alert 1, part name 1. Purchases recorded: 3 (header 2, part name 1). App
installs: 38 devices, 33 with at least one watch, 247 pushes sent.

**Hub's answer to the owner:** alerts are already the lead of the Pro sheet
and the store page (round 5, 2026-11-06) and they are what installs
actually do (33 of 38 have a watch); keep them the flagship. What gets
people to open Pro is mostly reach (distance) and prices, so Pro reads best
as "every watch, any distance" with prices second. Rule proposed: one Pro
prompt per screen, at a limit or beside the thing it unlocks; none inside
the car grid. Asked the owner about (1) one dismissible "set an alert" card
in the feed for people with no watch, (2) Pull-N-Save photos: a note to
them, or un-pausing. Not done without an answer. Not recommended for now:
example photos of a model for cars with none.

## 2026-11-16 ~16:30 UTC owner: "Yes add the alert card and draft the Pull-N-Save note. lots of no car pics on the web"

With a desktop screenshot: twelve tiles on the first screen, all drawings,
all from one yard's batch (Utah Pic-A-Part Ogden Premium, set out 11-15).

- **Alert card** (89f38002): one card in the feed after the first dozen
  cars, for someone with no watch; opens the Alerts form on the Make field;
  dismissible for good; no Pro prompt in it. Counted as `alert-card-shown`,
  `alert-card`, `alert-card-x` (the scorecard does not print them yet; the
  usage-stats "funnel events" list shows them).
- **Order of "Newest arrivals"** (89f38002): a car whose photo shows in the
  list counts as one day newer (`PHOTO_DAY_BOOST = 1`); ties go to the
  photo, then the truly newer day, then the nearest yard; cars set out since
  the last visit always lead. For a Salt Lake visitor the first 21 tiles are
  now photos (Pick-n-Pull, set out 11-14), then the 19 drawings of 11-15.
  A wider boost was weighed and left: it would bury a no-photo yard's new
  arrivals under days of another yard's photos.
- **Pull-N-Save note**: Gmail draft, thread `1a1e52cb8accbc08` (details and
  the scanner-name finding in `ops/yards.md`, same date). The Pull-N-Save
  inventory reader now sends the YardScout name (34f4b957).
- Asked the owner: switch Budget, U-Pull-R and Harry's readers to the
  YardScout name too (their 11-02 emails said the scanner uses it)?
- All of this is on the website only; the apps get it with the next release
  (1.13.0 is still waiting for review; a newer build needs a new "ship").

## 2026-11-16 ~16:35 UTC owner: "Yes switch all three, however I dont think new arrivles should be buried by a day just because they dont have a picture"

- The one-day photo boost is OUT (e46de036). "Newest arrivals" is strictly
  by set-out day again; a photo only orders cars set out the same day
  (photo first, then the nearest yard). Do not bring a boost back without
  the owner asking. Consequence, told to the owner: when the newest day's
  arrivals near someone are all at yards with no photos (Salt Lake on a
  Sunday), the first screen is drawings; only real photos fix that
  (Pull-N-Save, if they agree).
- U-Pull-R, Budget and Harry's readers send the YardScout name (table in
  `ops/yards.md`, same date).
- The alert-card entry above stands. The "Order" bullet in it is superseded
  by this entry.

## 2026-11-16 ~16:50 UTC owner: "Yes draft the corrections for all three"

- Two Gmail drafts and one form text (details in
  `ops/yard-outreach-drafts.md`, "Corrections, 2026-11-16"): U-Pull-R as a
  reply to their CTO in thread `1a1b2b1b2f24f262`, Budget as a reply in
  thread `1a19e455f0efaf97`, Harry's as text for their contact form (no
  record that the 11-02 note to Harry's was ever sent). None is sent; the
  owner sends them after the hub confirms the first scan with the new name.
- U-Pull-R is the serious one: the CTO was told on 11-03 and 11-06 that
  every request identified itself as YardScout, including the home pull.
  The reader had always sent a generic browser name.
- Found by the full run while this was going on, and fixed (0aca7aca): with
  the alert card above the screen, coming back to the Cars tab landed ~100
  px short. The tile at the top is now remembered and put back
  (`feedAnchor` / `feedAnchorRestore`).
- Suggested to the owner, not done: stop the U-Pull-R reader altogether
  until their API arrives (each scan still asks their site for the makes,
  hits the captcha on the first search and reads the price page).

## 2026-11-16 17:17 UTC today's feedback goes to main (sw `jh-v203`)

Branch `hub/feedback-1116`, 16 commits on top of main at 7a33d5c5, pushed to
main as a fast-forward. Website only; the apps get it with the next release
(a new "ship").

- In it: the alert card, one price Pro box on a car page instead of two,
  "fits 2013" instead of "fits 2013–2013", strict newest-first order with a
  photo deciding only inside a day, the tab-return fix, and the four readers
  (Pull-N-Save, Budget, U-Pull-R, Harry's) sending the YardScout name.
- Checks on the final state: run 6 (77 suites: browser e2e, units, site
  units, python e2e, every `scraper/test_*.py`) passed except `illo_unit`
  and `photo_policy_unit`, which stopped at "photoEpochBump is not defined".
  Both copy named functions out of the app and had not been given the new
  photo counter; tests fixed (app unchanged), both pass. Layout check: six
  widths, 2,208 checks, 0 failures. API suites and `browser_e2e.py` rerun at
  17:15 on the final state: all six pass.
- Owner, ~17:05: "give me harrys, the form never sent". The 11-02 Harry's
  note never went out, so no correction; the note was reworded to say what
  the reader does (every four hours, about 290 pages, answers the Sucuri
  check itself, asks for their OK) and given to the owner
  (`ops/yard-outreach-drafts.md` section 5). Held with the other three
  until a scan has run with the name.
- No reply from any yard in Gmail in the last three days (checked 17:08).
- NEXT: the 20:00 UTC scan is the first with the YardScout name (the 16:00
  scan started on the old code). Read its log: Pull-N-Save about 11,400
  cars, Budget 1,627 + 879, Harry's about 4,259 over three yards, U-Pull-R
  captcha and 0 cars as before. Then tell the owner the four notes can go.
  A yard that answers the name differently has given its answer.

## 2026-11-16 17:27 UTC today's feedback confirmed live

One fresh page load of yardscout.io at phone size, nothing stored (script
`xt/live_feedback.js` in the hub scratchpad): cache `jh-v203`; 40 tiles, the
first 12 photos loaded; the alert card after the 12th tile with the web
wording and no Pro prompt; a car page opened in the same load has one price
Pro box (`part-value`, under the parts) and no same-year "fits" range; no
page errors. The script's own order check failed on a name it could not
reach (`tsOf` is local to the sort), so order was not measured live; it is
covered by `cars_feed_e2e` section 1b on the same code, and the screenshot
shows Nov 14 cars ahead of Nov 13.

- Scans run late on GitHub's clock (12:00 started 12:31; yesterday's 20:00
  started 23:39). The 16:00 slot had not started at 17:17, so the next scan
  to start is the first with the YardScout name. Check-in scheduled for
  19:18 UTC (`trig_01LTCx4YjVckmAEk5HJttNSN`); it reschedules itself until
  that scan has finished.
- Seen in the live car page, to fix in the next web change: the turnover
  label ("Gets picked over fast") sits flush under the yard box. `.cd-value`
  has no top margin (styles.css, "Car screen additions") and `.locator` no
  bottom margin. On main since the feed merge; plainer now that the Pro box
  under it is gone.

## 2026-11-16 18:02 UTC car page spacing fix to main (sw `jh-v204`); a test race found and fixed

- **Fix** (63867a1d): 12 px between the yard box and the turnover label on
  a free user's car page (`.cd-value` top margin). Measured at phone and
  desktop width on the local build.
- **Checks**: run 7 (77 suites) passed except `interchange_e2e`; car-screen
  layout check at six widths, 192 checks, 0 failures.
- **`interchange_e2e` was not the fix.** It failed 2 of 3 reruns on the
  branch and 2 of 4 on main without the fix, at three different steps. Cause:
  the four Parts tests typed a zip and waited for cards; since the no-gate
  change cards show without a zip, so the tests moved on before the outside
  zip lookup (api.zippopotam.us, 0.4 to 0.7 s from here this evening)
  answered. It passed six times earlier today because the lookup was
  quicker. Tests now wait until the zip is stored (second commit on this
  branch); after that `interchange_e2e` 6 of 6, `part_finder_e2e`,
  `pf_ux_e2e`, `yaris_coverage_e2e` 2 of 2 each. Lesson: a hub merge that
  changes what "the page is ready" means has to be followed through the
  tests that waited on the old sign.
- **A small real gap found on the way, not fixed** (Parts tab code; noted in
  `ops/interchange.md`): if a zip typed on the Cars tab answers after a part
  was already picked on the Parts tab, the Parts tab keeps saying "Set a zip
  code" until the part is picked again. Needs a slow connection and quick
  fingers; shown with `xt/zip_late.py` in the hub scratchpad.
- **Scan**: no scheduled scan had started since 12:31 (GitHub dropped or
  delayed the 16:00 slot, as it did 04:00 and 08:00 today), so the hub
  dispatched one at 17:54 UTC: run 43923253337 on 4ba8328b, the first with
  the YardScout name. Scans queue one at a time (`junkyard-scan` group), so
  a late scheduled run cannot overlap it.

## 2026-11-16 18:13 UTC spacing fix confirmed live

One fresh load of yardscout.io at phone size: cache `jh-v204`; on a car page
opened in that load the turnover label sits 12 px under the yard box; no
page errors. Scan 43923253337 (dispatched 17:54, on 4ba8328b) is in
progress; the 19:18 UTC check-in reads its log for the four yards.

## 2026-11-16 19:25 UTC first scan with the YardScout name: all four yards as before

Scan 43923253337 finished 19:13 UTC (336,886 cars, 304 yards; data commit
dfa266c3). Pull-N-Save 11,446 over 8 yards, Budget 1,627 + 879, Harry's
4,259 over 3 yards (live read), U-Pull-R captcha and 0 cars as always; all
four price lists read. Table in `ops/yards.md`. Owner told the four notes
can be sent: two Gmail drafts as replies (U-Pull-R thread
`1a1b2b1b2f24f262`, Budget thread `1a19e455f0efaf97`), the Pull-N-Save
photo note (draft, thread `1a1e52cb8accbc08`), and the Harry's text for the
form at wegotused.com/contact (`ops/yard-outreach-drafts.md` section 5; its
Sucuri sentence was made conditional, see the note there).

Still open with the owner: stop the U-Pull-R reader until their API arrives
(hub recommends yes). Pull-N-Save photo checks stay paused until they
answer. Next hub wake: 2026-11-17 15:00 UTC, the two held website sentences
once both stores show 1.13.0 live (`trig_016dADedHXNCLcakiqQW9irq`).

## 2026-11-17 05:10 UTC owner asked "Update?"

- Stores (status runs 44021860463, 44021863386): **Play production 1.13.0
  (40) completed, full rollout. App Store 1.13.0 build 41 IN_REVIEW**
  (was WAITING_FOR_REVIEW; submitted 11-16 13:39); 1.12.16 is still the
  live iOS version. The two held website sentences wait for iOS; the 15:00
  UTC check-in (`trig_016dADedHXNCLcakiqQW9irq`) handles it.
- Three scans since the name change, all green (19:13, 00:40, 01:58 UTC).
  Latest: Pull-N-Save 11,191 over 8 yards, Budget 1,624 + 879, Harry's
  4,259 over 3 (their list unchanged since Sat 11-14 07:42 UTC, as before
  the change), U-Pull-R captcha and 0. 337,259 cars, 304 yards. No failed
  workflow since 11-16 17:30.
- Gmail: nothing sent in two days, so the three yard drafts have not gone
  out; no reply from any yard; no mail from Apple or Google. Only Reddit
  notices in the inbox.
- Website: `jh-v204`, unchanged since 18:13 UTC on 11-16.

## 2026-11-17 14:18 UTC a Reddit comment: "Looks like a copy of www.pullscout.com though?"

On the owner's r/projectcar post (Gmail thread `1a1e8425eb1d6a5d`, already
labelled `reddit-drafted`). What the hub could establish, from search
results only (pullscout.com is not on this session's allowed network hosts,
so the site itself was not opened and its look was not compared):

- PullScout is another junkyard-inventory search site: "Find donor cars and
  salvage yard inventory near you"; its home page states 288,420 vehicles,
  233 yards, 35 states and 6 Canadian provinces; search by year, make,
  model, zip, radius and freshness; pages per yard, per city/state and per
  car (VIN in the address, "crushed" and "seen 2 months ago" marks);
  "community-powered updates", "approved photos", saved searches. No app
  or alert feature could be confirmed either way.
- Age: one of its car pages records a car crushed on 2026-09-01, so it was
  collecting by about then. This repo was created 2026-09-02. Who was first
  is not known; do not claim it.
- Same category, similar "-Scout" name, different weight: YardScout's own
  ground is the parts list per car with values, interchange, row numbers,
  alerts with push, and the two store apps.
- Draft reply given to the owner in chat (playbook voice). The sentence
  about not having seen PullScout before is the owner's to keep or cut.

## 2026-11-17 14:27 UTC who was first: PullScout, by about five months (public records)

Owner: "They look concerningly similar, can we tell who made theirs first? I
had no idea pullscout was a thing and they even have the same orange."

| | PullScout | YardScout |
|---|---|---|
| Domain registered (registry RDAP) | 2026-03-19 (NameCheap, Cloudflare DNS) | yardscout.io 2026-10-09 |
| First certificates (crt.sh) | 2026-03-19, incl. www | 2026-10-09 |
| Web Archive | a working copy dated 2026-05-01 | 2026-10-10 |
| Project history | not visible | first commit 2026-09-02 as "Junkyard Hunter"; "rebrand to YardScout" 2026-09-09 |
| Orange | not seen (see below) | `#ff6b35` in the first stylesheet (09-02); today's `#B84A0A` since 2026-10-27 ("brand: logo kit rollout") |

- Their site existed at least four months before this repo's first commit.
  Do not say or imply YardScout was first, anywhere.
- Nothing in this repo mentions PullScout before the hub's own note of
  today, and YardScout's orange dates from its first day under its first
  name: both fit the owner's statement that it was built without knowing
  of them.
- NOT established: what their site looked like at any date, and so whether
  the look or the orange is theirs first. The hub could not open
  pullscout.com (the fetch tool could not reach it; a plain fetch from the
  shell was refused by the session's permission check, and the hub did not
  try another way) nor the Web Archive copy. A side-by-side needs the
  owner's screenshots or their go-ahead to open the site.
- Hub's view given to the owner: since they were first, a close likeness
  is YardScout's problem to solve, not theirs. Worth making the look
  plainly its own (accent, wordmark, first screen) once the two can be
  compared; a trademark question belongs with a trademark lawyer.
- Script: `xt/own_history.py` in the hub scratchpad (dates from the public
  GitHub history).

## 2026-11-17 14:35 UTC PullScout side by side (owner's four screenshots)

What their site shows today: wordmark "Pull" dark + "Scout" orange, serif
type throughout, blue-grey page, white rounded cards, orange pill buttons;
"THE LARGEST SELF-SERVICE YARD SEARCH", "Find donor cars all in one place",
378,119 vehicles at 348 yards, 42,292 arrivals in 7 days, "1 million+
tracked"; free account with an email "the day a new one lands on a lot";
USA and Canada; filters for colour, cylinders, transmission, drivetrain,
fuel; VIN decoder; a "Unicorns" page; yards unchanged for three weeks are
hidden. (The search engine's stored copy of their home page had older
wording and 288,420 vehicles at 233 yards, so the page was rewritten and
grew at some point before today; when is not known.)

Hub's read, given to the owner:
- Not alike as pages (type, background, layout, product). Alike in the
  three cues seen first: the "-Scout" name, "Scout" picked out in orange
  (ours: `header h1 .wm-scout { color: var(--brand) }`), orange pills on
  light cards. Also the pitch ("all in one place" / "into one search").
- Recommended: name in one colour (one CSS line; mock sent, image
  `for_owner/pullscout_vs_yardscout.png` in the hub scratchpad). Keep the
  orange for now (ours since the first commit; it is on the icon and the
  store listings). Lead with parts and values, not "every yard in one
  search": that is their headline and they list more yards (348 vs 304).
- The name is the overlap no design change removes; they were first. A
  trademark question is for a lawyer.
- WAITING ON THE OWNER: yes or no to the one-colour name. Nothing changed
  in the product.

## 2026-11-17 14:43 UTC owner: "Make the name one color, perhaps let's look at different accents"

Also from the owner: "extremely concerning that this was a thing before
YardScout, I had no idea, and now I look like a copy. His version also
appears to be free alerts".

- **Name in one colour**: branch `hub/one-colour-name` (65e1becc, sw
  `jh-v205`): app header, 404 page, rendered pages (`share.js`), both
  lockup SVGs, `og-card.png` regenerated from `og-card.html`. Full run 8
  and the layout check (two halves) in flight; live after they pass. Store
  screenshots still show the two-colour name: next release.
- **Accent mocks sent, nothing shipped** (`xt/accent_mocks.js` in the hub
  scratchpad swaps the orange values on the way to the browser; images in
  `for_owner/accents/`): orange as today, petrol `#0B6477`, cobalt
  `#1D4ED8`, racing green `#1E7042`, signal red `#B3261E`. Hub's pick if
  the owner moves: petrol (green collides with the turnover and "swaps
  with" tags, red with warnings, cobalt reads like every other app). A
  real switch touches the tokens in `styles.css` (light and dark), the
  mark, app icon and splash, OG card, store art; the icon needs a release.
- **Free alerts**: theirs is a free emailed alert with an account ("the
  day a new one lands on a lot"). Ours: one free instant push per phone in
  1.13.0 (Android live, iPhone in review), no account; emailed alerts on
  the web are Pro only (`backend/src/email_alerts.js`). Hub recommended one
  free emailed alert on the web (one car, capped sends), Pro for the rest.
  WAITING ON THE OWNER: accent (pick or keep orange); free web email alert
  (yes or no).
