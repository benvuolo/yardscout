# Ops hub — status (updated 2026-11-04)

This workstream stays in the long-running session because the scheduled
watches are bound to it. It does not build features.

## Live state

- **iOS 1.12.10 build 26**: submitted 2026-11-03 17:21 UTC, WAITING_FOR_REVIEW.
  Check: dispatch `asc-status.yml`.
- **Android 1.12.11 (33)**: Play production, status completed (Google review).
  Check: dispatch `play-status.yml`.
- **Web**: `main` deploys to GitHub Pages; sw cache `jh-v139`.
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

## Waiting on the owner

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
- Web only; the apps load the same files, so no store release is needed.
- Suggestion counts show for Pro only (same rule as the Make/Model lists).
