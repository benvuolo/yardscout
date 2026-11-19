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

## 2026-11-17 14:49 UTC owner: "let's do petrol, do the free emailed alert ... Can I get sued now? I'm scared"

- **Petrol accent: approved.** Values from the mock: deep `#0B6477`
  (buttons and links on light), bright `#0E8FA8` (mark, dark theme),
  darker `#084C5B`. Website first, after the one-colour name is live; app
  icon, splash and store art follow with the next release (needs "ship").
- **Free emailed alert on the website: approved.** A builder agent is on
  branch `growth/free-email-alert` (brief: one watch per confirmed email,
  the app free tier's distance, lowest email class under the Resend budget,
  one-click unsubscribe, no change to held sentences or colours). Hub
  reviews before anything reaches main. Shared test lock:
  `flock /tmp/ys-test.lock <test>` for anything that starts a server or
  browser, on both sides.
- **Legal worry, what the hub said (not legal advice):** no copying took
  place and the public history shows it; the open question is the name
  (trademark turns on confusion, not copying; they used theirs first).
  Third-party trademark indexes show no filing for PULLSCOUT or YARDSCOUT
  (not the official record). Risk-lowering steps are the ones in hand.
  Suggested one consult with a trademark lawyer. Rules for us from now on:
  never name PullScout in ads, keywords or page text; never claim first or
  largest; never copy their wording; never read their site by machine.
- Reminder given to the owner: the four yard notes are still unsent.

## 2026-11-17 15:05 UTC one-colour name to main (sw `jh-v205`); 1.13.0 live in both stores

- **Name in one colour**: run 8 (77 suites) all pass; layout check six
  widths, 2,208 checks, 0 failures. Pushed to main as a fast-forward.
  (Hub slip, no harm found: one browser test was started in the petrol
  working copy while the layout check was still running; both layout
  halves still ended clean. Every server or browser test now goes through
  `flock /tmp/ys-test.lock`.)
- **1.13.0 is live in both stores** (status runs 44109467799 and
  44109474369, 15:01 UTC): App Store 1.13.0 build 41 READY_FOR_SALE; Play
  production 1.13.0 (40) completed, full rollout. `docs/app-version.json`
  still says iOS 1.12.16; `app-store-version.yml` (every two hours) writes
  the new one.
- **Play listing uploaded** (part of the release the owner shipped on
  11-16): `store-listing.yml` run 44109917152 and
  `play-subscription-listing.yml` run 44109922973, both success. Google
  reviews listing edits like a release. The screenshots show the app as
  1.13.0 looks (orange, two-colour name); new ones go with the next
  release.
- **Held sentences**: switched on branch `hub/petrol` (bc4a8585) together
  with the petrol accent (064f043b, sw `jh-v206`); they go live as one
  batch after their regression. Task #58 closes then.
- Builder told that the held sentences are no longer held.

## 2026-11-17 15:17 UTC one-colour name confirmed live

One fresh load of yardscout.io at phone size: cache `jh-v205`; both halves
of the name compute to the same colour (rgb 28, 28, 26); 40 tiles; no page
errors. Deploy Workers (rendered pages) and Pages both succeeded at 15:06.
Usage stats run 44109930771: `funnel-v5` rows web 88, android 80, ios 14,
so 1.13.0 is in real use on both phones (check-in step 2). Devices: android
14 (1 Pro), ios 24 (9 Pro); 33 devices hold 87 watches.

## 2026-11-17 15:27 UTC petrol accent and the switched sentences to main (sw `jh-v206`)

- Run 9 (77 suites) all pass; layout check six widths, 2,208 checks
  (contrast included), 0 failures; dark theme looked at by eye.
- Petrol values: light accent `#0B6477`, hover and text-on-tint
  `#084C5B`; dark accent `#2BB3CC`, hover `#5CC6DA`, text-on-tint
  `#7FD0E0`; mark `#1095AF` (the mock's `#0E8FA8` put the NEW badge's dark
  text at 4.48:1, so the mark is a shade lighter: 4.8:1).
- Web icons recoloured with `xt/recolour_icons.py` (hub scratchpad); the
  same script will do the app icon and splash at the next release.
- STILL ORANGE, on purpose or pending: the apps in the stores (1.13.0), the
  store screenshots and icon, the app icon and splash sources under
  `assets/`, `android/`, `ios/` (next release, needs "ship"); the colours
  inside emails (`#ff9500` in `alerts.js`, `email_alerts.js`,
  `recap_signup.js`; `#f26b1d`/`#b84a0a` in the owner-only ops emails):
  after the free-email-alert branch merges, since the builder is in those
  files.
- Task #58 (held sentences) closes with this push once confirmed live.

## 2026-11-17 15:39 UTC petrol and the switched sentences confirmed live; task #58 closed

One fresh load of yardscout.io at phone size: cache `jh-v206`; accent
`#0B6477`, mark `#1095AF`; the name in one colour; the Alerts intro reads
"In the iOS and Android apps, free gets one watch pushed within hours
(cars within 50 mi)..."; 40 tiles; no page errors. Screenshot sent to the
owner.

- Release prep, NOT shipped: branch `release/brand-petrol` (48995190) holds
  the app icon, splash and Play icon in petrol (57 PNGs; recoloured with
  `xt/recolour_icons2.py`, which moves only the orange share of a pixel).
  Still to do with the release: store screenshots, the Play feature graphic
  (two-colour name and "250+" in it), email colours, version bump. Task #66.
  Needs the owner's "ship".
- Seen while doing this, for a copy pass with the owner: the site
  description and the Play feature graphic say "Find the donor car before
  you drive", close to PullScout's "Find donor cars all in one place".
  Three stock Capacitor splash files (blue logo on white) sit unused in
  `ios/App/App/Assets.xcassets/Splash.imageset/`.
- Builder still working on `growth/free-email-alert`.

## 2026-11-17 16:06 UTC free emailed alert: builder done, hub review, merged branch in checks

Builder's branch `growth/free-email-alert` (29bb2275; its own notes are in
`ops/growth.md`, dated section). Hub read all of
`backend/src/free_email_alert.js`, the hook in `admin.js`, the budget in
`ops.js`, the routes in `index.js` and the whole website diff.

What it is: on the website, a free visitor picks ONE watch in the Alerts
tab and leaves an address; after a confirmation click they are emailed when
a matching car is set out within 50 mi (the app free tier's own constant).
Changing the car replaces it; "Turn off" or the email's one-click
unsubscribe deletes the address and its copy of the watch.

Review, what holds:
- Double opt-in; the GET confirm page needs a button press (a mail scanner
  cannot opt anyone in); the reply never says whether an address exists;
  per-address and per-IP limits shared with the Monday email.
- Lowest class of mail, fail closed: 5 per scan, 20 a day, none once 70
  emails of any kind went out that day (shares of `RESEND_DAILY_CAP`, 100);
  if the counters cannot be read it sends nothing. It starts only after the
  same commit's Pro alert emails are out. Held alerts are counted and
  retried for 48 h.
- Rule 6: the browser's watches are read, never written; the page keeps its
  own key `ys_falert`. Not shown to Pro or in the app shells. No Pro prompt
  in the card. Privacy page says what is stored and how to remove it.
- Known limits, accepted: a send that fails outright is counted, not
  retried; the watch toast still offers only the Monday email; "parts only"
  is not carried to the server.
- Noted for later (builder's finding, not new): the commit's dispatchers
  together can exceed the free plan's 50 subrequests on a busy commit; the
  free alert runs last, so it is the first to lose.

Merge branch `hub/free-email-alert`: main merged in (only `docs/sw.js`
conflicted; now `jh-v207`), plus the email colour pass (36a12971: petrol
`#2BB3CC` in every user email and its pages, `#0B6477` in the light ops
email). Run 10 (the 77 suites plus the three new tests), the full layout
check and the six API suites are in flight under the test lock.

## 2026-11-17 16:35 UTC free emailed alert to main (sw `jh-v207`, migration 0018)

- Run 10: 80 suites (the 77, plus `free_email_alert_ui_e2e`,
  `free_email_alert_unit`, `free_email_alert_client_unit`) all pass. Layout
  check six widths: 2,400 checks, 0 failures. API suites: `e2e-ops`,
  `e2e-devices`, `e2e-coverage`, `e2e-email` (with the new phase 3) and
  `browser_e2e` pass.
- `e2e.sh` failed 3 of 39 in that batch ("inventory before any upload",
  "new user starts on free tier", "values still stripped"): all three say
  the server it talked to already held data. It runs first in the API
  batch, on port 8788, right after the browser suites; re-run by itself
  after stopping every local server: 39 of 39. Read as a leftover local
  server from an earlier suite, not as a fault in the change. The API
  runner should stop stray servers before its first suite too (it only did
  so after each one).
- Pushed as a fast-forward. Deploy Workers applies migration 0018 and
  deploys the API; Pages publishes the page. Until the API is up the card
  says it could not reach the server.
- After it is live: one page load to see the card for a free web visitor;
  a real sign-up is NOT tested by the hub (it would need a real inbox).
  First real numbers come from the ops email ("free alerts" lines) and the
  four `free-alert-*` events.

## 2026-11-17 16:46 UTC free emailed alert confirmed live

Deploy Workers (migration 0018 + API) and Pages both succeeded at 16:36.
One fresh load of yardscout.io at phone size as a free web visitor with one
watch (set in the test browser only): cache `jh-v207`; the card "Free email
alert" sits under the watchlist with the email field, names the car, says
"within 50 mi, usually the same day" and the sending-limit line, and has no
Pro prompt; the intro carries the new sentence; a status request with a
made-up token is refused with 401, so the API side is deployed; no page
errors. No sign-up was made (it needs a real inbox): the first real one is
the owner's to try, or the first visitor's.

- Watch for in the daily ops email: the "free alerts" lines (on, pending,
  mailed, held) and the four `free-alert-*` events.
- The builder's working copy is removed; its branch stays on origin.
- Many old agent working copies remain under `.claude/worktrees/` and the
  hub scratchpad (29 listed); harmless, worth pruning if disk gets tight.

## 2026-11-17 20:02 UTC owner: "Ship ... Do everything you think you should ... I want everything large done"

Owner, ~17:00 UTC: "Ship, and yes give me the replacement lines. Do
everything you think you should, my billing cycle ends in a few days and I
want everything large done. More breadth, data, parts compatability,
watertight features, etc."

- **"Ship" = 1.13.1** (petrol, one-colour name, alert card and the rest of
  the 11-16/17 website changes into the apps). Branch `release/1.13.1`:
  `release/brand-petrol` merged (app icon, splash, Play icon). Still to do
  before dispatch: tagline, Play feature graphic, store screenshots, full
  regression. Task #66.
- **Five builders launched ~17:10 UTC**, each in its own worktree, each told
  to push its own branch and report: `yards/breadth-1117` (more yards;
  stop the U-Pull-R reader), `parts/next-block-1117` (parts table next
  block), `interchange/next-1117` (release-ready interchange from data
  already held, no new crawl), `hub/watertight-1117` (alert dispatch
  inside the Workers subrequest limit, Parts late zip, free-alert loose
  ends, scorecard lines, test servers, `tools/regress.sh`, eBay workflow),
  `data/yard-freshness-1117` (a yard's frozen list shown honestly).
  Agent ids are in task #67.
- **All five stopped at the account's 5-hour usage limit** (reset 18:40
  UTC) before pushing anything; the session itself restarted. Owner at
  20:00: limit reset, continue. Resumed three at 20:01 (watertight, yards,
  parts); interchange and yard-freshness are resumed when a slot frees, so
  the limit is not hit again mid-release. Lesson: five builders at once on
  top of a full day's work is more than one 5-hour window carries.
- Freed 5.5 GB by removing 15 old working copies whose commits were on
  origin; 14 others kept (not on origin or with edits).

## 2026-11-17 20:38 UTC yards builder done: 3 yards added, U-Pull-R reader off (branch reviewed, not merged yet)

Branch `yards/breadth-1117` (f850bd22). Hub read the whole scraper diff.
- Added, all read under the YardScout name, offline tests with fixtures:
  Intermountain Auto iPull (Idaho Falls ID, 578 cars; the host that
  answered our name with HTTP 500 on 10-28 answers it normally now), S&S
  U-Pull-It (Lebanon MO, 573 in a 4-make probe of 35 makes), Standard Auto
  Wreckers UPIC (Scarborough ON, 524; first Ontario yard; read from the
  Google Sheet the yard's own page names).
- `UPULLR_READER_ENABLED = False`: nothing is sent to upullrparts.com;
  `scraper/test_upullr_switch.py` fails if it is switched on.
- Not added, with reasons and drafts 6 to 12 in
  `ops/yard-outreach-drafts.md`: Carolina Pick N Pull (terms forbid
  robots), Kenny U-Pull (Cloudflare 403), Express Pull-N-Save (terms),
  U Pull It Davie (robots.txt names AI agents), Pull N' Go (503), Andersen
  (feed frozen since August), Russellville (stale), Ewe Pullet (empty).
- Scraper-only change: merge after 1.13.1 is dispatched; scraper tests are
  the check. Afterwards: run `scraper/gen_yard_site_links.py` once the
  first scan has the yards (it rewrites a list in `docs/app.js`, so that
  is a website change with its own regression), and wire the two new price
  files into the app's price-sheet list.
- FOR THE OWNER (builder's findings, hub agrees they are theirs to decide):
  1. **Ario**: `ario.autorecycler.io/robots.txt` now disallows `/yard/`
     for every crawler ("Paid Website Search / embed product") and the host
     serves Ario's own consumer search. Our reader (about 45 yards, about
     45,000 cars) does not fetch those pages; it calls the search function
     behind them on another host, under a browser name. Nothing changed
     yet. Draft 10 asks Ario.
  2. **Older readers' names**: the nine older CRUSH MVC tenants, Barry's,
     Pick-A-Part VA, Ario and the big chains still send a browser name.
  3. Which outreach drafts to send; Davie needs a human look first;
     Standard's price list is in Canadian dollars (the app has no currency
     label).

## 2026-11-18 15:17 UTC yards + parts builders' work to main (scraper only)

Branch `hub/scraper-1118` = `yards/breadth-1117` (f850bd22) +
`parts/next-block-1117` (ad6cf91b) merged on main. All 33
`scraper/test_*.py` pass on the combined tree. Takes effect at the next
scan; no website file changes.
- Yards: Intermountain Auto iPull (Idaho Falls ID), S&S U-Pull-It
  (Lebanon MO), Standard Auto Wreckers UPIC (Toronto ON); U-Pull-R reader
  switched off (`UPULLR_READER_ENABLED = False`, nothing sent to their
  site). After the first scan with them: run `scraper/gen_yard_site_links.py`
  (rewrites a list in `docs/app.js`, needs a website regression) and wire
  `ifipull_pricing.json` / `ssupullit_pricing.json` into the app's
  price-sheet list.
- Parts §26: Volvo S40, Saturn S-Series, Trax, Sonic, Freestar, Freestyle,
  Mirage, Venture, Xterra; every mechanical row from a catalog part number
  in the `oem-raw` crawl records. Generic-only 4.1% → 3.5% on the same
  inventory; no car lost a row.
- Check the next scan log: the three new yards' counts, "[U-Pull-R] reader
  is switched off", no new WARNING lines.
- Fable agents stopped by the weekly model limit (reset 2026-11-19 02:00
  UTC); session switched to Opus by the owner. Watertight, interchange and
  yard-freshness builders restarted on Opus at ~15:15 UTC.

## 2026-11-18 15:22 UTC CPU-limit fix to main (API only)

Cloudflare emailed (owner screenshot, ~14:22 UTC): "Your Workers hit the
free tier CPU time limit at least 100+ times in the past 24 hours".
`cf-usage.yml` (now with CPU lines, 9174695f): yardscout-api, 656 requests
stopped ("exceededResources") on 11-17 between 12:00 and 15:00 UTC; none
on yardscout-site; none on 11-18 so far. From 07:00 to 17:00 on 11-17 the
API took up to 2,645 requests an hour with p50 14-17 ms of CPU: a crawler
on the website's /car/ pages, each needing `GET /v1/vehicles/:id`.
Fix (branch `hub/cpu-limit`): `backend/src/jsonpick.js` picks the one
entry instead of parsing a ~400 KB index bucket and a yard shard of up to
~770 KB; ~5 ms per lookup with gunzip instead of ~14. Plus: tokens are no
longer upper-cased first; 45,985 cars (lowercase id, no VIN) had 404 car
pages. Tests: new `jsonpick_unit`, every API unit, site units, `e2e`
(39/39), `e2e-ops`, `e2e-devices`, `e2e-email`, `e2e-coverage`,
`browser_e2e`: all pass. The owner was told no upgrade is needed.
Next: one live check of a lowercase-id car page; `cf-usage.yml` again
after the next crawl. Further options if needed: VINDEX_MOD 64→512
(saves ~1.3 ms of gunzip a lookup), memoize landed.json in the site worker
(its p90 is 28 ms, p99 99 ms; it has not been stopped).
Zone analytics (paths, user agents) is not readable with the current API
token ("zone.analytics.read" missing), so the crawler is not named.
- 15:45 UTC confirmed live: `GET /v1/vehicles/utpap-orem-K026992` (a
  lowercase id with no VIN, 404 before) → 200 with the car; a VIN lookup →
  200; `yardscout.io/car/utpap-orem-K026992` → 200. Re-check of the CPU
  numbers scheduled ~20 h later (`cf-usage.yml`).

## 2026-11-18 16:29 UTC yard list freshness to main (sw `jh-v209`)

Builder's branch `data/yard-freshness-1117` (c2c69279; notes in
`ops/data.md`, "2026-11-18 — yard list freshness"), merged as
`hub/freshness-1118`. Hub read the scan side (`yard_freshness.py`, the
arrivals filter in `push_inventory.py`) and checked that the four new yard
columns go at the END of each yard row: every reader (the app's
`expandV2Row`, `placeYardResolve`, the workers) reads positions 0-6 or by
name, so the apps already in the stores ignore them.
- Thresholds from 3.5 weeks of committed history (6,791 gaps, 301 yards):
  "stale" after 3 full business days without a car added or removed
  (fires on 1.00% of healthy yards' scans), "frozen" after 10 (0.05%).
  Frozen yards' cars: no New badge, out of "new this week", last in Newest
  arrivals, no alerts; still listed. A list that jumps 40%+ after a freeze
  (flush) does not alert either (the lifespan rule's share, tested equal).
- Today's dry run: frozen 4 yards / 2,309 cars (Wrench-A-Part Holland since
  Oct 22, UAPI Alexandria, Colorado Auto & Parts Englewood, Utah Pic-A-Part
  Orem Premium); stale 4 / 4,333 (Youngstown, Paul's Lake Station, M&M
  Buffalo, Foss Wilson). Takes effect at the next scan; until then the app
  falls back to the old yard_health rule in the new quiet style.
- Run 12 (89 suites incl. the new `yard_list_unit`, `yard_list_pages_unit`,
  `jsonpick_unit`; `test_yard_freshness.py` 64 checks), layout 2,496
  checks, six API suites: all pass except `long_listed_unit` ("yardListStale
  is not defined": the test copies functions out of the app); test fixed
  (95285c18), passes.
- Builder's suggestions, not done: apply the 40% hold to ANY one-scan jump
  (whole lists re-added under new ids on 10-26/10-28 got past alert dedupe;
  Indy-U-Pull-It and Pull-N-Save Riverside flip-flopped lists for 10 days);
  saved-car "leaving soon"/"gone" at frozen or flushed yards; ops email to
  read `listState`; date-only edits at 19 yards make `lastChangedAt` look
  fresher than the list. Yards to check: Wrench-A-Part Holland, UAPI
  Alexandria, Colorado Auto & Parts, Youngstown, Budget Bartow (12-day cycle).

## 2026-11-18 interchange builder done; independent verifier started

`interchange/next-1117` (12f9a78d; builder's section at the end of
`ops/interchange.md`). Nothing shipped yet.
- Nissan/Infiniti candidate: 343 Likely groups, 15,788 lot cars (window
  regulators, mirrors, gauge clusters, climate controls). Builder's round 5
  had 0 WRONG, but the builder wrote the rule fixes, so §11.4 needs an
  independent sample: verifier agent on `interchange/verify-1118`.
- New rules (all namespaces): a model-year sold in more than one body joins
  a cross-model group only when its own pages list the number for every
  body; "Production Date: from MM/YYYY" windows are now read. They REMOVE
  live claims: gm 63 groups (Cavalier/Sunfire, Cobalt/G5, Alero/Grand Am
  coupe vs sedan), subaru 14, mopar 8 + 1 narrowed, ford 7, toyota 4
  (`groups/_report/live_diff_2026-11-18.txt`). The verifier also checks at
  least 25 of those removals before they go out.
- Ranking of what else can ship without a crawl: toyota +15.9k lot cars,
  mopar +10.7k, hmg (after its parked body rules), vag, bmw.
- Crawl wishes (not dispatched): Tier D wave 1 product pages (need strict
  name rules per site first); gmpartsgiant / fordpartsgiant own-page
  completion (24% / 18% of lot cars) are blocked with 503: a retry is the
  owner's call (rule 2: no workaround either way).
- `test_model_map` fails on main too: new one-car spellings in the live
  inventory ("Honda Cr-V E:fcev", "BMW 535i GT xDrive"); data quality.

## 2026-11-18 16:43 UTC parts round 2 to main (scraper only)

`parts/next-block-1118` (0b78d7bb; PARTS_GAPS §28-31, `ops/parts.md`).
All 34 `scraper/test_*.py` pass on the tree merged with main.
- §28 accuracy audit of the §13-22 fuel-pump and A/C windows against the
  catalog numbers in `oem-raw`: 205 checked, 91 confirmed, 64 corrected
  (narrowed or split where the numbers change; table in §28.1), 18 left
  with reasons (§28.2), 32 with no number in the data (§28.3). 439
  year/make/model combinations, 19,355 cars, get narrower windows; no row
  lost. Radiator fans, AWD units and similar could not be checked (no
  catalog category).
- §29 Lexus ES duplicate card fixed; §30 facelift cuts for 12 models from
  catalog appearance numbers; §31 Torrent, MKS, Alero, Lincoln LS, S80.
- Generic-only 3.55% → 3.23% on the same inventory.
- Builder said Wikipedia and Consumer Guide "do not resolve": the hub
  checked, both answer 200 from this session with a plain request; the
  builder's page-reading tool failed, not the network. Tell the next parts
  builder to read them with `curl` (read-only reference pages).
- Builder's questions, hub's view: rename the 45 multi-number §13-22 rows
  "match part #" (yes, next round; it changes eBay keys, check
  `ebay_prices.py` first); Chrysler 200 generation break (with a source);
  audit alternator and starter rows the same way (next round); seed a crawl
  on the 32 no-number windows (interchange crawl list).

## 2026-11-18 17:56 UTC interchange: wrong live claims removed; Nissan held

Independent verifier (seed 46021118 / 7731118; report `groups/_report/
nissan_verify_2026-11-18.json`, `removals_verify_2026-11-18.json`, section
"Independent verification" in `ops/interchange.md`):
- **Nissan candidate: 9 WRONG of 60** → NOT shipped. 6 drive (4WD-only or
  2WD-only gauge clusters claimed for every car of a model-year built in
  both; 43 of 343 groups have it), 3 body (sedan-only clusters on the
  200SX coupe). 11 RISK (engine/transmission/hybrid splits, Titan rear-door
  motors without a cab code).
- **Removals: shipped.** 28 checked: 18 wrong live claims (coupe parts on
  sedans, rear-door parts on coupes, "from 10/2012" rows on 2012 IS 350s), 7
  true claims lost (Ford window motors split by feature, Sonic, Camaro/
  Firebird, Cobalt/G5, one Subaru), 3 cannot tell. Losing a true claim
  shows less, never something wrong; recover them later by decoding GM body
  codes (37/69/67) and Subaru S./W.
- Tests on the merged tree: run 13 (89 suites incl. part finder,
  interchange, pf_ux, pf_new_cats) all pass; curation tests pass except
  `test_model_map` (fails on main too: new one-car spellings in the live
  inventory); oem_fitment tests pass. Payload 1,538,963 → 1,503,938 bytes.
- Rule flaws the verifier found, for the next interchange round: drive
  codes in the option column not read (may affect LIVE makes too: check),
  body check leans on lot vPIC bodies, engine/transmission splits get only
  "option", gas/hybrid pages, body codes not read as bodies.

## 2026-11-18 17:58 UTC list jumps held from "new"; ops email names the site's stale yards

`data/list-jumps-1118` (66e6e6b4; numbers in `ops/data.md`, "2026-11-18
(later)"). A scan where a yard adds cars under ids it has NEVER listed
(history DB) making up 25%+ of its list and 50+ cars is a jump: its cars
get the flush mark (no alerts, not "new this week", no New badge) for 8
days. Measured on 160 committed scans: catches all 15 re-key / source-swap
events (Ryan's Detroit 10-26, U-Pull-It x5 10-28, Pull-N-Save x6 10-31,
Midway x2 11-14), no real set-out day (largest real 18.9%, smallest jump
27.5%). Ids that come back (Indy's 35 flips, Riverside's 13, partial reads)
are not held: they keep their dates and the alert dedupe already stops
them. Ops email: the per-yard list now uses `listState` (same yards and
dates as the site) plus an "early warning" line a day earlier.
Tests on the tree merged with main: 33 scraper tests and every API unit
(incl. new `ops_yard_list_unit`) pass; builder's `e2e-ops` 154/154.
Not done (saved_alerts.js, after the watertight merge): skip "leaving soon"
at stale/frozen yards; send "gone" only after two missing commits and no
flush mark. Flip-flopping feeds (Indy, Pull-N-Save Riverside) and the date
fields of the 10-28/10-31 source changes: yards workstream.

## 2026-11-18 ~18:45 UTC LKQ partial read, Pull-N-Save check page, Play 1.13.1 live

- Scan 44350039303 (16:40): LKQ Pick Your Part 51,476 cars against ~72,200
  before. 17 yards stopped after their first one or two pages (25 or 50
  cars); STALE-KEEP carried their earlier lists forward, so no car vanished.
  The 13 scans before it had 0 such yards except one on 11-16 (1 yard).
  The reader ended a store's read on ANY error, silently. Now
  (`_pyp_get_page`): one retry after 5 s for a timeout, dropped connection,
  429 or 5xx (Retry-After honoured, at most 30 s); 403/404 not retried; a
  stop is logged with yard, page and reason. Test `scraper/test_pyp_reader.py`.
- Same scan: Pull-N-Save answered getMakes with HTTP 202 and a meta-refresh
  page (a check page) 3 times; the 01:58 scan saw the same, 07:23 and 12:30
  read all 11,310 cars. Rule 2: no workaround. Their 8 yards were carried
  forward. The draft to Pull-N-Save is in Gmail (ops/yard-outreach-drafts.md).
  If it lasts a full day, add it to that draft.
- Also 0 this scan: Bevell's (1,145 kept), Route 34 (333 kept), Budget
  Winter Garden (1,624 kept).
- Google Play: production 1.13.1 (41) rollout complete (play-status 18:18).
  Apple: 1.13.1 build 42 WAITING_FOR_REVIEW (submitted 15:03).
- usage-stats: Apple's sales report printed a 404 as a row of zeros (0
  downloads since 11-06 while the app counts ~5 new iPhone users a day). Now
  it says "no report" with Apple's words, and units by product type (0145a829).
- Apple sales reports (usage-stats 44369641326): SALES SUMMARY 1_1 has 404
  "expected results but none were found" for every day from 11-06 to 11-17;
  1_0 also 404; 1_2/1_3 are not valid versions (400); the WEEKLY report for
  the week ending 11-15 is 404 too. 11-04/05 had 153 and 190 updates a day,
  so Apple has stopped publishing sales for this vendor, not our users. The
  SUBSCRIPTION snapshot still arrives (3 active on 11-17). Owner to check App
  Store Connect: Business (an agreement waiting to be accepted?) and Trends
  (does the web page show units after 11-06?).
- Gmail connector turns every URL or bare domain in a draft into a
  google.com/url redirect (RAW-checked). Sent 11-18 ~17:28 with such links:
  Kenny U-Pull, Carolina Pick N Pull, Express Pull-N-Save, Andersen. The two
  unsent drafts (Budget follow-up, 1A Auto) rewritten with no addresses.
  Rule from now: hub drafts carry no web addresses (ops/yard-outreach-drafts.md).
- Check-in (trig_01Bj2uqq2oFAy4JdziSoq38G) on scan 44350039303 (committed
  18:17): new yards in: Standard UPIC 524, Intermountain Idaho Falls 578,
  S&S Lebanon 1,187. "[U-Pull-R] reader is switched off ... no request
  sent". "[list freshness] 4 stale (4,333 cars), 4 frozen (2,309)", as the
  dry run said. Manifest yardFields end with listChangedAt, listState,
  listReadAt, listFlushAt. No FAILED or Traceback lines; 2 WARNING lines
  (Pull-N-Save check page, Route 34 0 cars). Live: yardscout.io/car/
  utpap-orem-K026992 says "This yard's list has not changed since Oct 22,
  2026. Call before you go." Next: wire ifipull/ssupullit price lists and
  run gen_yard_site_links.py after the watertight merge.

## 2026-11-18 ~19:20 UTC watertight batch to main (sw `jh-v210`, ca283423)

`hub/watertight-merge-1118` = builder branch `hub/watertight-1117` (notes in
`ops/growth.md`, "Watertight" and "Watertight, continued") + main of 19:00 +
three hub commits: regress_unit lists API suites without node_modules
(612b1a10), price sheets for Intermountain Idaho Falls and S&S Lebanon
(1459c696), inventory links for the three new yards from
`gen_yard_site_links.py` (ca283423).
- In it: one shared outside-call / D1 budget per scan commit with the
  dispatchers in priority order; the watch toast offers the free email alert;
  the Parts tab re-runs its search when a late zip arrives; tests stop the
  servers they start; `tools/regress.sh` (the whole regression under the lock).
- Tests: full `tools/regress.sh` on fe91f512: 95 PASS, regress_unit FAIL and
  6 API suites SKIP (no backend/node_modules in the worktree). Fixed the
  test, linked node_modules: regress_unit + all six API suites PASS. After
  merging main + the price sheets: --quick 71 PASS; interchange_e2e,
  part_finder_e2e, pf_ux_e2e, cars_feed_e2e, card_share_e2e,
  alert_freshness_e2e, e2e-ops, browser_e2e all PASS. After the yard links:
  site-proxy units, yard_list units, card_share_e2e, cars_feed_e2e PASS.
  Not run: map_regions_e2e (left out of the runner by design; needs outside
  map servers); the layout check was not repeated after the merge (main's
  changes since were data and server-side).
- The strip builder (`growth/strip-falert-1118`) was told the toast is done
  and to merge this head.
- 19:24 UTC confirmed live: yardscout.io/sw.js names `jh-v210`; one load of
  /car/utpap-orem-K026992: 200, the frozen-list sentence, no page errors.

## 2026-11-18 ~20:00 UTC Cars watch strip offers the free email alert (sw `jh-v211`, f27e3e22)

Builder branch `growth/strip-falert-1118` (6f2ab742; cases, counting change
and suggestions at the end of `ops/growth.md`). Hub read the app.js diff:
one rule (`falertAskOpen`) shared by the toast and the strip; `stripAskKind`
picks alert / Monday / Monday-add / plain; the removed `recapEligible` call
was equivalent to the checks already at the top of `stripMailHtml`; new
watches only through `addQuickWatch` (rule 6); not in the app shells or for
Pro. Builder's full `tools/regress.sh` on the merged tree 3e881c5e: 104
PASS, 0 FAIL, 0 SKIP (layout 2,664 checks). Main since: ops only.
- Counting from today: the strip's alert ask counts `free-alert-shown`, not
  `email-asked`; "Monday email asked" will fall and "Free alert offered"
  rise. Weeks across 11-18 are not like for like on those two rows.
- Builder's open items: the scorecard could note the switch date; a
  "Watching X" strip could offer the alert for an existing watch; backend/
  has no package-lock.json (npm ci fails; tests use the main checkout's
  node_modules); year ranges are written after the model in the strip and
  before it in the alert.

## 2026-11-18 ~20:30 UTC interchange rules round 2 back; two agents started

`interchange/rules-1118` (54d0784d; builder section "2026-11-18 Rules after
the independent check" in ops/interchange.md on the branch). Live diff vs
main: gm 11 removed, 2 restored, 47 narrowed (36 drive, 11 "gas only");
ford 6 restored; mopar 9 narrowed ("1500: 4WD only"); mb 1 narrowed;
subaru 1 restored. Nissan candidate 283 groups, builder's own sample 0
WRONG (not independent). Not merged.
- Started an independent check of every restored claim (built from the diff,
  not the builder's list), the disputed R14 Cobalt headlamp, and 8 seeded
  drive notes: branch `interchange/verify-restored-1118`.
- Started a builder to turn the notes into real per-app gates (drive, body,
  cab, engine, fuel, transmission) in the payload and docs/app.js, claims
  only down, sw jh-v212, plus test_model_map on pinned inventory: branch
  `interchange/gates-1118`. Reason: rule 3 asks for drive and body GATES; a
  note does not stop a 2WD car being listed for a 4WD-only part.
- Order: restorations verified -> gates merged -> a fresh independent §11.4
  sample of nissan WITH the gates -> nissan may ship (0 WRONG).
- Owner decision named by the builder: a gm 4wd/awd/hybrid catalog crawl
  would turn many "2WD only" notes back into plain claims; gmpartsgiant is
  marked blocked (rule 2), so it stays off unless the owner decides.
- 20:25 UTC confirmed live: sw jh-v211; one load of #cars=Nissan|Xterra with a zip shows the strip-falert ask ("Free email alert for Nissan Xterra ... within 50 mi"), no page errors.

## 2026-11-18 ~21:15 UTC interchange rules round 2 to main (ad97b79b)

`interchange/rules-1118` + `interchange/verify-restored-1118` merged. Data
only (docs/data/oem/*.json and docs/data/interchange.json; the app fetches
data network-first per scan, no sw bump).
- Independent check (verifier did not write the rules; own reader on
  oem-raw@dca9cd84): the diff restores 9 groups / 19 apps (ford 6, gm 2,
  subaru 1): 19 RIGHT, 0 WRONG, 0 RISK. R14 Cobalt 2007 headlamp is AP(37)
  coupe only: its removal is right. 8 seeded drive notes (seed 20261118):
  no over-claim; 7 GM notes rest on an unread 4wd page and the Mopar note on
  4WD-only fitment rows, so they under-claim. The gates builder was told to
  carry that basis and word those notes "checked for 2WD; 4WD not checked".
- Tests on the merge: --quick 71 PASS; interchange_e2e, part_finder_e2e,
  pf_ux_e2e, yaris_coverage_e2e, card_share_e2e PASS.
- Verifier notes not fixed: the Ford 6CPZ window motors are different doors
  on Focus vs Transit Connect (no door in the note); Mopar "Up To 07/23/2012"
  production windows are not named; 1999 Tahoe/Yukon rear-door regulators
  ("CLASSIC 4 DOOR") carry no body note (both already on main).
- 20:55 UTC confirmed live: yardscout.io/data/oem/window-regulator.json carries the new drive notes, same counts as main.

## 2026-11-18 ~22:40 UTC OEM per-app gates to main (sw `jh-v212`, 6703c2cc)

`interchange/gates-1118` (builder section at the end of ops/interchange.md).
OEM groups' drive / cab / engine / fuel / transmission limits are real per-app
gates: payload app `[make, model, lo, hi, null, gate]`; the app's OEM-GATE
block (`pfOemDonorGate`): a donor whose own decode or listing contradicts the
limit is not offered; unknown is "if equipped" with a line naming the limit
(same as the parts table's drive/body/manual gates and the aftermarket gate);
an unconfirmed limit is never Verified. Notes from an unread other-drive page
now read "<model>: only 2WD checked".
- Hub review asked for one fix, done: no drive limit where the model-year
  comes in one drive (GM: decided by the year page's catalogs; Ford Focus
  2012/2015, C-Max 2013, Transit Connect 2015 FWD and ML350 2007-08 AWD in
  `policy.SINGLE_DRIVE_TABLE`, each with its basis). Ford/MB donors back to
  plain rows.
- Live diff vs main: 0 groups added or removed, 0 app-years added; 48 notes
  reworded. Donor pairs on the pinned lot: GM 59,852 -> 56,081 (3,771
  excluded, 1,787 "if equipped"); Mopar 116,281 -> 115,939; Ford, MB, Toyota,
  Subaru, VAG, HMG unchanged.
- Builder's full tools/regress.sh on a833fe49 (code head; main contained):
  104 PASS / 0 FAIL / 0 SKIP. Main had not moved; fast-forward.
- test_model_map now checks the pinned inventory (a85c654) and only REPORTs
  live-inventory spellings.
- Hub decisions recorded: unknown drive stays "if equipped"; no body gates
  that add claims this round.
- Next: independent §11.4 sample of the nissan candidate WITH the gates.
- 23:15 UTC confirmed live: sw jh-v212; data/oem/window-regulator.json carries 22 unchecked drive gates, as main; one page load, no page errors.
- 23:25 UTC container restart lost the first independent nissan check (no
  work had been pushed); restarted with the same brief, told to push partial
  work every 30-40 min. Branch-to-be: `interchange/verify-nissan-1118c`.
- 23:30 UTC Apple 1.13.1 build 42 still WAITING_FOR_REVIEW. Check-in
  trig_01JcAHSWqZ1rxaB5VAPHXG34 at 2026-11-19 09:10 UTC (on acceptance:
  store-listing.yml + play-subscription-listing.yml).

## 2026-11-19 ~00:10 UTC nissan independent check FAILED again; round 3 started

`interchange/verify-nissan-1118c` (961fdf12; verifier's section at the end
of ops/interchange.md, report groups/_report/nissan_verify_2026-11-18c.json).
Seed 73901118: groups 21 RIGHT / 9 WRONG / 0 RISK, pairs 27 / 2 / 1. Do not
ship nissan. Classes: product-page engine column never used as a limit (20
groups, 286 plain lot cars); the "gas" gate lets QX60 hybrids through
(5N1CL0 VINs decoded 2.5L); joined drive codes (2WDSTD/2WDHICAS) ungated;
4wd gate confirms All-Mode cars beside a "W. AUTO" sibling; a Kph cluster;
feed "Rogue" 2014-15 = Rogue Select (JN8AS5); Frontier regular cab listed
under another number (borderline).
- Round 3 builder on `interchange/round3-1119`: census of the same classes
  on the 8 LIVE makes first, fixed claims-only-down on live; then the 8 fixes
  on the nissan candidate. A new independent check follows before nissan
  ships.
- 00:40 UTC container restart stopped the round 3 builder after its first push (894bde7b: lot replay + census tools); a new builder continues on the same branch, pushing every 20-30 min.

## 2026-11-19 ~02:30 UTC interchange round 3 to main (sw `jh-v213`, b3d995d4)

`interchange/round3-1119` (builder section at the end of ops/interchange.md;
census groups/_report/class_census_2026-11-19.json; live diff
live_diff_2026-11-19_round3.txt). The verifier's five flaw classes, fixed on
all 8 LIVE makes, claims only down: 0 added groups, 0 gained years, 0 widened
gates; 16 groups removed (3 Ford km/h clusters, 1 MKZ 2010 hybrid cluster, 3
Mopar export mirrors, 9 note-cap refusals), 87 narrowed. Biggest live wrong:
2011 Camry hybrid-only body parts were plain for ~350 gas Camrys each; Fusion/
MKZ hybrid clusters; 2016 Malibu motors on the Malibu Limited. Plain donor
pairs on the pinned lot 319,276 -> 292,967; "if equipped" 1,814 -> 12,071;
excluded 4,113 -> 12,076. New gate keys (cab lists, drive_not, eng_not);
payload shape unchanged.
- Tests: builder's full regression on bf5fe452: 101 PASS, 3 FAIL:
  cars_feed_e2e 1 check (passed 139/0 re-run alone: flake);
  ui_no_truncation both halves "[cards-mixed] setup-error: no real-photo card
  with three cards after it". Hub ran that screen on MAIN (55cb877a, 390 light)
  and it fails the same way: data-dependent, pre-existing on main with the
  newest scan data; to be fixed in the test. Main was contained; fast-forward.
- Nissan candidate rebuilt: 246 shippable groups (was 283). Not shipped; a
  new independent check is next.
- Builder's open points: the 160-char note cap now costs 9 live and 65 nissan
  groups (suggestion: once a limit is a gate, the note may say "engine-limited,
  see each car"); YL3Z-10849-DA removed on a strict "KPH/MPH" reading;
  JK61C/JK61D left the nissan candidate with no refusal recorded.
- 02:45 UTC confirmed live: sw jh-v213; page loads with no page errors (Xterra strip and a San Jose Cars list).
- Layout check fix (test only): the cards-mixed screen failed on main with
  the 11-19 data (first 40 cards near San Jose were new iPull-uPull Sacramento
  cars, photos not up yet). It now narrows the list to one yard when the first
  page has no photo card. Full layout check 1,332 + 1,332 checks PASS,
  cars_feed_e2e PASS.
- Owner-facing observation, not changed: near San Jose the newest-first list
  opens with 82-mi-away Sacramento arrivals without photos. A possible tweak:
  within the same day, nearer yards first (photo-first stays within a day).

## 2026-11-19 ~03:45 UTC nissan check 1119d: 2 WRONG; round 4 started

`interchange/verify-nissan-1119d` (e4bd8ccc). Seed 38271119: groups 19 / 2 /
9, pairs 26 / 0 / 4. Round 3's classes are fixed (0 engine leaks, 0 Kph, 0
Rogue Select, cab gates hold). New: same-option AWD siblings ("*W. AWD.
PREMIUM" vs "*W. PREMIUM": 96301-3JA9B QX60 mirror, 24820-3ZD0A QX56
speedometer; 4 groups, 94 plain AWD rows); build-date windows that split a
model year with an unlinked number for the other builds (166 rows / 111
groups); lot cars whose VIN decodes as another vehicle shown plain.
- Hub decisions for round 4 (stricter rule 3, recorded in the brief): drive
  gate for same-option drive siblings; a build window inside a model year is
  kept only with the window named in the note and a `built` gate that makes
  every donor "if equipped: check the build date" (never plain), else refused;
  two pages disagreeing on a window take the narrower one; a VIN/listing
  mismatch car is never a plain OEM donor ("if equipped").
- Round 4 builder on `interchange/round4-1119` (sw jh-v214): live makes
  first, then nissan; another independent check follows.

## 2026-11-19 ~03:50 UTC owner check-in: list order, Glenn, status

- Glenn replied 11-18 22:35 (ops/yards.md, "Glenn ... replied"). Reply
  drafted in Gmail (thread 1a1b2b1b2f24f262), owner sends.
- Correction to the hub's 11-18 note: the Pull-N-Save email was SENT by the
  owner on 2026-11-02 (info@pullnsave.com, no reply); it is not a waiting
  draft. Pull-N-Save read fully in the 22:09 and 22:47 scans (11,310 cars);
  the check page was seen in 2 scans on 11-18 only.
- LKQ after the retry fix: 71,998 and 72,140 cars, 0 failed pages, 0
  STALE-KEEP in the 22:09 and 22:47 scans. No WARNING lines in either scan.
- Apple 1.13.1 build 42: still WAITING_FOR_REVIEW at 03:37.
- Cars list order: owner said yes to "nearer yards first within the same
  day". Hub then found the list ALREADY does that (day, then list photo,
  then nearest; sort code in docs/app.js, 'date-desc'). The San Jose case
  (48 Sacramento cars, 82 mi, first) is a different thing: they were the
  only cars within 100 mi dated 11-18; Pick-n-Pull's newest set-out date at
  that scan was 11-17 (52 cars 1 mi away, all with photos). Changing it
  means relaxing the owner's 11-16 rule "strictly by set-out day", so the
  hub asked instead of changing it: option = treat today and yesterday as
  one group, nearest yard first, older days as now.

## 2026-11-19 ~05:00 UTC round 4 live; fifth nissan check started; store-app gap

- Round 4 (`interchange/round4-1119`, 9da7e293) reviewed by the hub and merged
  to main as df0bdc0a (sw jh-v214). Hub's own checks: `live_diff.py` re-run
  against main = 0 added groups, 0 gained app-years, 0 widened gates on all 8
  live makes (ford 1 group removed, 4 narrowed; toyota 16; hmg 1);
  `pf_guards_unit.mjs` ALL PASS; `test_round4_1119.py` 28 checks;
  `tools/regress.sh --quick` on the merged tree 71/0/0. Builder's full run on
  the code head: 104/0/0.
- Hub decisions on the builder's two "stricter than the brief" choices:
  1. `no_page` windows (window only in the product record's notes, list page
     not in the raw) stay gated. Claims only go down. Cost: ford 1 group.
  2. Titan 7S00E / 7S006 "starred or not" read as a drive split (nissan
     candidate only): left as built; the independent check judges it blind.
- Fifth independent nissan check: verifier on `interchange/verify-nissan-1119e`,
  seed 52941119, 30 groups + 30 pairs, blind to earlier reports. 0 WRONG to
  ship.
- **Store apps and the gates (new finding, owner told).** Store builds bundle
  `docs/` (native/README.md); 1.13.1 was cut at 343262c2 = jh-v208, before
  the OEM gates (jh-v212). The apps read the live payload with code that
  ignores gates: every gated donor is a plain Likely row (the note names the
  limit; multi-group rows may show another group's note). Pinned lot, 8 live
  makes: the website hides 12,076 donor pairs and marks 13,294 "if
  equipped"; the apps show all of them plain. Closing it = a store release
  from current main (1.13.2). Rule 1: waits for the owner's "ship". Apple
  1.13.1 is still in review, so iPhone follows that approval.
- Builder suggestions carried forward (not done): the scraper's mismatch
  check compares year and make only (a QX60 VIN listed as QX80 is not
  flagged; data workstream); aftermarket rows, hand platform groups and
  same-generation donors never read the mismatch flag; a short note once a
  limit is a gate would keep 18 + 66 nissan groups the 160-char cap refuses;
  Mopar "Up to / After" dates still unread.
- Live check 05:07 UTC (one load of the home page): cache `jh-v214`, no page
  errors; the live gate code returns "if equipped ... built 04/2014-12/2014
  only — check the build date on the door sticker" for a windowed app-year,
  a plain row for an ungated one, and "if equipped: this car's listing and
  VIN disagree, check the car" for a mismatch car.
- Data need written to ops/data.md (model mismatches not flagged; census:
  3,143 cars in 316 name pairs, most are naming, a few hundred real).

## 2026-11-19 ~05:45 UTC nissan check 1119e FAILED (7 WRONG, one class); round 5 started

- Independent check `interchange/verify-nissan-1119e` (4998471a), seed
  52941119: groups 21 RIGHT / 4 WRONG / 5 RISK, pairs 23 / 3 / 4. Nissan
  stays off.
- All 7 WRONG are one class, and it is a hub decision that was wrong: round
  4 decision 2 left a build window alone when the rest of the model year is
  carried by the number's own predecessor or successor. "Replaced By" runs
  one way (the newer number serves the older car; the older part is not
  stated to fit a car built with the newer one), so those vehicle-years
  need the build-date gate too. Checker's census on the candidate: 76
  vehicle-years in 50 groups, about 2,917 plain rows.
- **Same class on the live makes** (round 4 census, `window_linked`): toyota
  88 app-years (676 plain lot pairs), ford 1 (13), hmg 1 (323). Live since
  the makes first shipped; Likely tier, "verify the number on the part".
- RISK kinds: an unexplained leading "*" on option clauses decides drive or
  engine scope (5 items); 7 drive gates labelled "stated" with no drive
  word on the row (Titan 2005 7S00E among them: the hub's "leave it for the
  check" call came back "no basis"); a 1-2 month model-year edge.
- Round 5 hub decisions (builder a2ac3fad resumed, branch
  `interchange/round5-1119`, live makes first, claims only down):
  1. linked windows are windows: note names the window + `built` gate, or
     the vehicle-year is dropped at the 160-char cap; launch / end-of-run
     windows with no other number stay as they are;
  2. other-page windows match on the number, not the option clause (Sentra
     2004); find why Stanza 1995 has no gate;
  3. a starred / unstarred difference alone is never a drive split (Titan
     pair reverted);
  4. `drive_basis: "stated"` only with the drive word on the number's own
     row; sibling-inferred gates get basis `"sibling"` and say so in the
     app line;
  5. "*": no fetch; grep the raw for a legend, report, change nothing
     unless the raw settles it.
- Checker suggestions kept for later (not in round 5): show the donor's
  door position on regulator and mirror rows (80730-JX30C is a front-door
  motor on a Cube/Juke and a rear-door one on a Rogue); name a stated
  option such as "without A/C" in the note.
- After round 5: hub review, live diff 0 added, regress, merge the live
  part, live check; then a sixth independent nissan check (new seed; used:
  46021118, 61181118, 73901118, 38271119, 52941119).

## 2026-11-19 ~07:05 UTC owner replies; Apple sales finding; round 5 on main; "Ship" 1.13.2

Owner (~06:40 UTC) answered the 03:40 list by number: 1 list order "What are
you talking about" (the question was not understood; re-ask as one plain
question, nothing changed); 2 Apple "See photo" (Trends, Oct 18 to Nov 17:
App Units 275, In-App Purchases 5, Sales $44.95, units on every day through
Nov 17; the account header reads "YardScout LLC"); 3 Ario "Are we blocked?";
4 free trial "Are we positive?"; 5 drafts "Will look"; 6 Reddit "I'll peep";
then "Ship" (= 1.13.2, task #75). Then: an email signature with the logo
(`ops/email-signature.html`, "Ben | title"), "am I the CEO?", and whether
ben@yardscout.io can be used.

- **Apple sales** (usage-stats 44475176114, read-only checks added in
  e31966b0): for `ASC_VENDOR_NUMBER`, SALES is 404 "There were no sales for
  the date specified" on every day since 11-06. Its newest report is 11-05,
  and that report's Developer column carries both "BENJAMIN ALEXANDER VUOLO"
  and "YardScout LLC". The SUBSCRIPTION snapshot still arrives (4 active
  through 11-12, 3 from 11-13); SUBSCRIPTION_EVENT and SUBSCRIBER have
  nothing in 16 days. Reading: the account's legal entity became YardScout
  LLC on 11-05 and sales since 11-06 are filed under a new vendor number.
  Not proven until that number is read. `usage-stats.yml` now runs the same
  report for a second number when the secret `ASC_VENDOR_NUMBER_LLC` exists
  (the owner adds it; the secrets API is not reachable from the hub). Then:
  decide from the two subscription snapshots how
  `tools/store_subscribers.py` counts (both numbers, or the new one). Our
  "App Store 3" may be low, and "0 downloads since 11-06" was the report,
  not the users.
- **Correction (hub's mistake):** "all 11 people who reached Apple's payment
  screen backed out" (told to the owner 11-18 and 11-19) was not sound. They
  are 11 taps, 10 of them on Nov 14 while build 40 was in App Review (this
  file, 11-16 entry: "Apple's reviewer and testers, not customers"), and
  Apple's page shows purchases around Nov 11 and Nov 13 that the app's
  counter did not record. The free-trial idea has no evidence behind it yet;
  look again after a clean week (about 11-26).
- **Round 5 merged.** Builder head 982adbf3 pushed to main at 07:02 UTC as a
  fast-forward (sw `jh-v215`). Hub's own `live_diff.py` against main: toyota
  88 groups narrowed (build-window gates), hmg 1 narrowed, ford 1 app-year
  lost (MKZ 2011, note over the cap), 0 added claims on the 8 live makes.
  The hub's merge and the builder's merge gave the same 30 payload files
  apart from `builtAt`. Quick regression on the merged tree 71/0/0. Shipped
  donor pairs on the pinned lot: plain 291,603 -> 290,592; "if equipped"
  13,294 -> 14,285; excluded 12,076 -> 12,034.
- **Disk full.** The container had 0 bytes free near the end of the
  builder's full regression: its 2 failures (both layout halves, "Target
  crashed") and the hub's first quick run (22 scraper tests could not
  write) were that, not code. Hub removed 17 working copies with no edits
  whose commits are on origin (6 GB freed); kept every copy with edits or
  with commits that are not on origin. Hub is running the full layout
  suite again on 982adbf3 before the store builds.
- **Nissan: round 5b started** (builder resumed, branch
  `interchange/round5b-1119`, candidate only): hold out every claim whose
  drive or engine scope is decided by a starred option clause, since the
  raw has no legend for the "*". Then the sixth independent check (new
  seed; used 46021118, 61181118, 73901118, 38271119, 52941119).
- **1.13.2** goes out from main once the live check and the layout pass are
  in: Android production; iPhone build to TestFlight only (`submit=false`),
  because 1.13.1 build 42 is still WAITING_FOR_REVIEW (asc-status
  44476352084, 07:01 UTC). When 1.13.1 is READY_FOR_SALE: `release-ios.yml`
  with `submit_only=true` and the 1.13.2 build number.
- **Email set-up, as found:** yardscout.io receives through Cloudflare Email
  Routing; the owner's mail goes out from the Gmail account; Resend is set
  up for sending on the domain. ben@ needs a routing rule to receive and a
  Gmail "Send mail as" set-up to send. Nothing changed by the hub.
- 07:15 UTC live check (one load): caches `jh-v215`; the sibling-basis line
  and the build-window line render; `data/oem/side-mirrors.json` on the live
  site has 100 `built` gates (12 before round 5), e.g. 87910-48240-A0
  RX 400h 2006 "built 03/2005-01/2006 only". The 05:14 scan's commit kept
  the round 5 payload.
- 07:26 UTC full layout suite on 982adbf3: both halves pass (1,332 checks
  each, 0 failures).
- **07:27 UTC 1.13.2 dispatched** from main 3591e082: release-android run 32
  (44479741801, production, versionCode 42) and release-ios run 43
  (44479745314, `submit=false`, build 43); both succeeded by 07:32.
  play-status 44480389133: production 1.13.2 (42) completed, rollout 100%.
  asc-status 44480392647: 1.13.1 build 42 still WAITING_FOR_REVIEW (not
  touched); build 43 not listed yet (Apple is processing it). Details and
  the What's New text: `ops/release.md`. iPhone submission of build 43
  follows 1.13.1's approval (`submit_only=true`).
- Apple sales, supporting fact: the owner's inbox has Apple Developer's
  "verify your work email address ... to enroll your organization in the
  Apple Developer Program" dated 2026-11-01, four days before the first
  report row that names YardScout LLC. Task #76 waits for the new vendor
  number (`ASC_VENDOR_NUMBER_LLC`).
- Email: hello@yardscout.io receives (mail delivered 11-01, 11-05, 11-09);
  nothing has ever arrived for ben@, so it is treated as not set up.
- 09:10 UTC check-in (trig_01JcAHSWqZ1rxaB5VAPHXG34) now also submits iOS
  1.13.2 build 43 with `submit_only=true` when 1.13.1 is READY_FOR_SALE, and
  must not run it while 1.13.1 is still in the queue.

## 2026-11-19 ~07:50 UTC round 5b on main (candidate only); sixth nissan check started

- Round 5b (builder, branch `interchange/round5b-1119`, head 43bca593):
  nissan candidate only. 22 groups / 59 vehicle-years held as "starred
  clause decides scope" (`groups/_report/nissan.starred_held.json`): drive
  gates 7 groups, engine gates 5, ungated drive 2, ungated engine 14; 9
  groups held whole, 13 narrowed. Titan 24810-7S00E 2005 is held (its 4WD
  basis 7S007 is a starred clause). Shippable 223 -> 214; plain pairs
  40,326 -> 38,357. The rule is in `curate.py` (`STARRED_SCOPE_NS`), not in
  policy.py, so no hash moved and no payload was rebuilt.
- Hub review: the 8 live groups files are byte-identical to main; hub's
  `live_diff.py` 0 changed groups on all 8; `test_round5b_1119` 28 checks
  pass; quick regression on the merged tree 71/0/0. Merged to main at
  29e5fe96. `docs/` untouched (sw stays `jh-v215`).
- Hub decision on the builder's question: the 9 groups (19 vehicle-years)
  held only because a SIBLING's starred clause decides stay held. Not
  decided: transmission scope from a starred clause (the candidate has one
  transmission-gated group, 24810-9BD4C); left for the check to judge.
- Sixth independent nissan check started 07:50 UTC: fresh agent, blind,
  seed 27641119, candidate at 29e5fe96, branch
  `interchange/verify-nissan-1119f`, report
  `groups/_report/nissan_verify_2026-11-19f.json`. Used seeds now:
  46021118, 61181118, 73901118, 38271119, 52941119, 27641119. Ship nissan
  only on 0 WRONG; then payload + sw bump + full regression + live check.
- Still open for the owner from the builder: the 160-character note cap now
  refuses 88 nissan groups; naming models that share a label once would
  keep many. Windows no other number carries stay plain by design (ford 5,
  toyota 4, nissan 49 app-years).

## 2026-11-19 ~08:00 UTC owner: list order "Yes"; Ario left as it is; trial on hold; ben@ rule added

Owner, answering the 07:35 summary by number: 1 list order "Yes"; 2 the new
Apple vendor number "I'll do this tmrw" (task #76 waits); 3 Ario "I'll email
when we stop reading them into the app" (hub's reading, told to the owner:
leave the Ario reader as it is and send nothing now; the owner emails Ario
if the feed ever stops; rule 2 still applies then, no workaround); 4 free
trial on hold "Ok" (look again about 11-26). No "swap": iOS 1.13.2 build 43
still waits for 1.13.1's approval. Also: "I added the cloud flare rule, am
I good to put it in my sig" (ben@yardscout.io).

- **List order (task #74), branch `hub/list-two-day-1119` (d3540acc, sw
  `jh-v216`).** Newest arrivals: the newest day in the list (never a day
  after today) and the day before it sort as ONE group: nearest yard, then
  the newer day, then the car whose photo shows. Older days unchanged
  (day, photo, nearest). Held cars last, as before.
  - Why "the newest day in the list" and not the calendar's today: before
    a yard publishes today's cars the calendar reading would put one far
    yard's yesterday cars over a near yard's cars of the day before, which
    is the complaint again.
  - The 2026-11-16 rule ("new arrivals should not be buried by a day
    because they don't have a picture") is why photos cannot come first
    across the two days: inside the group distance decides between yards,
    and a photo only orders cars of the same yard and day. So in the top
    group a nearer car without a photo now sits above a farther car with
    one. Told to the owner.
  - The "set out before your last visit" divider assumed the new cars
    lead; it is now drawn only where they all do (the count line and "Show
    just those" are unchanged).
  - `cars_feed_e2e` section 1b rewritten: 142 passed, 0 failed (group of
    478 cars over 2 days in the test view; both divider cases exercised).
    Full regression running; then main, live check.
  - Apps: web only until the next store build. Android 1.13.2 (42) and iOS
    build 43 do not have it. A 1.13.3 needs the owner's "ship".
- **ben@yardscout.io:** no mail has arrived for it yet (searched 08:00
  UTC). The hub does not send mail, so the test is the owner's: one message
  from a different account (Gmail hides a message an account sends to its
  own forwarding address).

## 2026-11-19 ~08:20 UTC owner asleep until ~15:00 UTC: "build something meaningful ... jaw dropping"

Owner (08:05 UTC): "Going to bed, I'll be up around 7ish. Until then build
something meaningful and useful. Something that differentiates us from any
competitor. I want to wake up to something jaw dropping."

Hub's choice, and why: a **game plan in the Parts results**. Today the
Parts tab lists donor cars. Tonight it also says (1) which yard to drive
to: donors by yard with distance, newest set-out and the yard's own price,
and (2) how often the seeker's model lands near them, from the history
database only a tracker has (252,356 recorded departures as of the 05:14
scan). Facts only: counts and past weeks, no percentages, no promise, no
"first" or "only" claims. Considered and not chosen tonight: a rare-finds
feed (fun, less useful to someone fixing their own car), a multi-yard
route planner (too large to finish tested in one night).

- Builder A, branch `feat/where-to-go-1119` (from
  `origin/hub/list-two-day-1119`): "Best yards for this part" card, chips,
  tap-to-filter, the count-equals-list proof, mount points for the
  forecast in the card and in the Cars watch strip; sw `jh-v217`.
- Builder B, branch `feat/arrival-forecast-1119` (same base): the scan
  writes `docs/data/arrivals/` (8 full weeks, per yard coverage, relists
  and flush scans excluded, frozen yards marked stale, at most once per 20
  hours, never fails the scan); `docs/forecast.js` with
  `YSForecast.summary` and `.mount`; offline tests on a synthetic DB.
- Hub: review both (the scan writer is on the scan's critical path), merge
  list order -> A -> B, ONE full regression on the combined tree, main,
  then a real scan for real arrivals data (dispatch `scan.yml` or the
  13:14 UTC cron), read its log and file sizes, one live load, screenshots
  in `ops/screens/` for the owner. Web only; the apps need a "ship"
  (1.13.3). Task #77.
- Running alongside: the list-order full regression (task #74), the sixth
  nissan check (task #72), Apple check-in 09:10 UTC (task #75), Cloudflare
  check-in 11:25 UTC.

## 2026-11-19 ~08:25 UTC sixth independent nissan check: FAIL (2 WRONG, one class); nissan stays off

Check 1119f (seed 27641119, candidate at 29e5fe96, branch
`interchange/verify-nissan-1119f`, head bad522d4, report
`groups/_report/nissan_verify_2026-11-19f.json` on that branch).
Groups 23 RIGHT / 1 WRONG / 6 RISK; pairs 21 / 1 / 8.

- **WRONG (both the same):** a `cab: "crew cab"` gate on Titan rear-door
  regulators (82720-7S000 Titan 2005, 145 lot donors; 82730-9FJ0A Titan
  2012, 20). The part's own row has no cab clause, and "crew cab" appears
  nowhere in the raw; the gate was inferred from page structure. The app
  then says "this part is listed for crew cab only" and the note "Titan:
  crew cab only": a stated basis the pages do not carry. No donor is
  wrongly shown as plain (cab is never decoded, all are "if equipped").
  Census: 6 groups, 8 vehicle-years, 227 Titan donors; the other 9 cab
  gates have KC/CC/T clauses on their own rows.
- **RISK kinds:** claims that rest ONLY on starred clauses (33 groups / 91
  vehicle-years; round 5b held only those where the star decides drive or
  engine scope); QX60 "gas only" gates with no `eng_not` 2.5L, so decoded
  2.5L hybrids are plain (8 groups, 54 cars; the fix reached the gauge
  clusters but not regulators or mirrors); transmission or drive words on
  the page with no gate (G35/G37 2008 JK61D, Xterra 96302-EA000 "4WD. S.
  6MT"); production windows that end inside the model year and are not
  gated (7 groups / 12 vehicle-years / 264 plain); pages that date one
  number differently (96302-7S600).
- Hub's reading: round 5's fixes held (no linked-window WRONG, no drive
  basis WRONG). The new class is the cab twin of the drive-basis class
  fixed in round 5. Six checks, each finding the next thinner class.
- **Round 6, NOT started** (the overnight build has the builders; a third
  agent risks the 5-hour usage limit, as on 11-17). Decisions ready for it:
  1. cab gates get a basis like drive (`stated` only when the number's own
     row carries the cab code); an inferred cab limit is held out of the
     candidate (the 6 groups' Titan years), not reworded;
  2. hold every vehicle-year whose claim rests only on starred clauses;
  3. `eng_not` 2.5L on every QX60/JX gas-only gate, all categories;
  4. a census of every production window against the model-year span, and
     gate or drop the ones that end inside it;
  5. a page that ties the part to a transmission or drive in the option
     text gets the gate or is held;
  6. where two pages date a number differently, the narrower window.
  Then a seventh independent check, new seed (used: 46021118, 61181118,
  73901118, 38271119, 52941119, 27641119).

## 2026-11-19 ~09:10 UTC list order cleared; arrivals builder done; Apple still waiting

- **List order (task #74):** full regression on `hub/list-two-day-1119`
  (d3540acc): 103 passed, 1 failed, 0 skipped. The failure:
  `free_email_alert_ui_e2e` "strip: 'check your inbox' for the alert, and
  the car is watched": the strip had already re-rendered as watched
  ("Watching Acura TL — new ones light up in Alerts. Check your inbox to
  turn on its email alert.") when the test read it, so the first-moment
  wording it expects was gone. Two builders and the regression were running
  at once. Re-run alone on the same commit, twice: PASS, PASS (41-44 s).
  Read as a timing flake of that check under load, not the order change;
  both layout halves passed. Cleared to merge.
- **Arrivals builder (B) handed back**, branch `feat/arrival-forecast-1119`
  head 664bc459: the scan writer (never fatal, temp + rename, at most once
  per 20 h; coverage restarts after a flush at the hub's request), the new
  forecast module in `docs/` (`YSForecast.summary/words/mount`, reads the
  app's `DATA_BASE`), tests: `test_arrivals.py` 55, `forecast_unit` 71,
  `forecast_e2e` 70, quick regression 73/0/0. Hub read the writer and the
  query line by line. Size estimate 4-6 MB raw in ~80 files, about once a
  day. The app's main script is untouched; nothing calls the module until
  builder A's card lands.
- Release candidate `hub/rc-1119` = list order + main + B (sw `jh-v216`,
  the forecast module in SHELL). Hub's checks on it (quick, forecast_e2e,
  cars_feed, free_email_alert_ui) are queued behind builder A's layout
  run. It missed the 09:14 cron scan; a scan is dispatched by hand once it
  is on main, so real arrivals data exists hours before the owner is up.
- **Apple 09:08 UTC** (asc-status 44493603300): 1.13.1 build 42 still
  WAITING_FOR_REVIEW; 1.13.2 build 43 processed (VALID, internal
  TestFlight). Nothing submitted. Next check 15:10 UTC
  (trig_01GRs6LuCfyqatRgBeKiiF9y); the 09:10 check-in is answered by this.
- Builder A (best-yards card): first version pushed, hub asked for a
  headline count line and rank numerals (81d682eb); its layout run is on.
- Tooling note for the next session: a privacy hook refuses some Bash
  commands whose text names the app's main script or index page (those
  files hold the public support address). Use the Read, Grep and Edit
  tools on them, and write ops text with the Write tool, then append it.

## 2026-11-19 ~10:15 UTC list order LIVE; arrivals writer on main and a scan running; card + forecast in one full regression

- **List order LIVE (task #74 done).** `hub/rc-1119` (list order + main +
  arrivals builder B, sw `jh-v216`) pushed to main at 09:56 UTC (8c48be12)
  after: quick regression 73/0/0, `cars_feed_e2e` PASS,
  `free_email_alert_ui_e2e` PASS, `forecast_e2e` PASS twice. One live load
  at 10:08 UTC with zip 95112: caches `jh-v216`; 18,011 cars in view, the
  two-day group is 478 cars and leads, nearest first holds; the list opens
  with Pick-n-Pull San Jose North, 1 mi, set out the day before the newest
  day (the owner's own case); `YSForecast` is defined (unused until the
  card lands).
- `forecast_e2e` failed once on the release candidate (the 390 px case read
  the real, missing files): the test did not block service workers, so the
  fixture was served or not depending on timing. Hub fixed the test
  (`serviceWorkers: 'block'`, as the other e2e tests do); it then passed
  twice.
- **Scan 44500938468** dispatched by hand at 09:56 UTC on 8c48be12: the
  first run of the arrivals writer against the real history database. To
  check when it ends: the `[arrivals]` log line (arrivals in the low
  hundreds of thousands, flush scans in the thousands, 4-6 MB, under 30
  s), `docs/data/arrivals/index.json` (about 307 yards, most with 8
  covered weeks), steady weekly counts for a common model at a big yard,
  and that the commit carried the new directory. GitHub's cron for this
  workflow runs hours late (the 04:00 run started 05:13, the 08:00 run had
  not started by 09:55), so the hand dispatch was the way to get data
  tonight.
- **Builder A handed back** (`feat/where-to-go-1119`, head 5c80e8e9, sw
  `jh-v217`): "Best yards for this part" card: headline "N donor cars at Y
  yards within R mi", rank numerals, chips (Most donor cars / Closest /
  Newest arrival / Lowest price), tap-to-filter with the maps link, held
  yards last, the count-equals-list proof in `pf_plan_e2e` (91 checks),
  layout screens. Its first layout run failed at 320 px with 200% text (39
  failures, "yard price $X" could not wrap); fixed, then both halves
  passed (1,380 checks each).
- **Integration bug found by the hub:** the card passes `where: 'parts'`
  and the strip `where: 'cars'` (the surface), and the forecast module
  read `where` as a place name, so the line would have said "within 100
  mi of parts". Fixed in the module: the place comes only from `place`;
  `where` is never shown. New `pf_forecast_e2e` (17 checks) runs the real
  card with the real module, the Cars strip, and the missing-files case;
  `forecast_unit` gained the two "never shown" cases (73 checks).
- Release candidate `hub/rc2-1119` (ec53c018) = main + A + the fix. The
  one full regression on the combined tree started 10:00 UTC.
- **Nissan round 6 started 10:10 UTC** (interchange builder resumed, branch
  `interchange/round6-1119`): the 08:25 decisions plus a census of the
  same classes on the live makes first (cab gates not on the number's own
  row, ungated windows that cut the model year, option text tying a part
  to a transmission or drive).

## 2026-11-19 ~11:10 UTC game-plan card LIVE (jh-v217); round 6 on main; seventh nissan check started

- **Full regression on the combined tree** (`hub/rc2-1119`: list order +
  arrivals + best-yards card + the place/where fix): 109 passed, 1 failed,
  0 skipped; both layout halves pass (1,380 checks each). The failure:
  `pf_plan_e2e`, 4 "forecast stub" checks. Cause: the test put a stub on
  `window.YSForecast` before load and the real module, now merged, replaced
  it. Fixed in the test (a getter with an ignoring setter). Re-run:
  `pf_plan_e2e` ALL PASS (91), `pf_forecast_e2e` PASS (17), `forecast_e2e`
  PASS (70), `pf_plan_unit` PASS.
- **Pushed to main 10:51 UTC (3a35f2f2), sw `jh-v217`.** One live load at
  11:06 UTC: caches `jh-v217`. The hub's first script searched a 2004
  4Runner alternator and saw no card: that search asks for the engine
  first ("Pick your engine above"), and the card comes with the results
  once one is picked (checked on the local tree: "45 donor cars at 13
  yards within 100 mi"). The script now picks the engine; the live check
  with real arrivals data follows the scan.
- **Scan 44500938468** still scraping at 11:08 UTC (72 min in); the
  arrivals files come with its commit.
- **Round 6 (interchange builder), branch `interchange/round6-1119` head
  5928f884, merged to main at 0212ed03.** Live makes, claims only down:
  toyota 2 groups gated (GS 300/400 1998 rear doors, built 08/1997-08/1998),
  ford 3 gated and 2 groups held at the note cap (8G1Z-19980-C,
  1L2Z-7823394-BB), subaru 2 groups held (61041AL04A/05A Legacy/Outback
  2015: a sibling lists the 6MT separately). Hub's own `live_diff.py`: 0
  added groups, 0 gained app-years, 0 widened gates in all 8; quick
  regression on the merged tree 74/0/0; `test_round6_1119` 26 checks.
  Shipped pairs (pinned lot): plain 290,592 -> 290,089; if equipped
  14,285 -> 14,264; excluded 12,034. App untouched, sw unchanged.
  Live-make census of the 1119f classes: cab gates not on the number's own
  row 0; ungated cutting windows ford 5 / toyota 4 vehicle-years; option
  text tying a part to a transmission: subaru 4 vehicle-years.
- Nissan candidate after round 6: 214 -> 171 shippable groups; plain pairs
  38,357 -> 30,048. Held lists: `nissan.starred_held.json` (45 groups, 150
  vehicle-years), `nissan.round6_held.json` (14 groups: inferred cab 6,
  transmission tie 8).
- **Seventh independent nissan check started 11:05 UTC**: fresh agent,
  blind, seed 91371119, candidate at 0212ed03, branch
  `interchange/verify-nissan-1119g`. Used seeds now: 46021118, 61181118,
  73901118, 38271119, 52941119, 27641119, 91371119.
- Builder suggestions kept for the owner: a transmission-basis line in the
  app (like the drive "sibling" line) would let the held JK61D and the two
  subaru groups show as "if equipped" instead of being held; the note cap
  now costs ford 2 live groups; a census of hybrid displacements on the
  live makes' gas-only gates before deciding anything there.

## 2026-11-19 ~11:30 UTC the game plan is LIVE with real data (task #77)

- **Scan 44500938468 finished 11:18 UTC** (commit f40e7ff7) and wrote the
  first real arrivals history: 196,802 arrivals in 8 weeks, 307 yards (4
  stale), 77 files, 3.87 MB, 6.9 s. Numbers, coverage and the checks are in
  `ops/data.md` (11:25 entry).
- **One live load at 11:21 UTC** (zip 95112, 2004 Toyota 4Runner,
  alternator, 4.7 V8): caches `jh-v217`, no page error, no overflow.
  - Card: "42 donor cars at 12 yards within 100 mi", ranked: iPull-uPull
    Sacramento 82 mi, 8 donor cars, newest set out 6 days ago; Pick-n-Pull
    Rancho Cordova 92 mi, 8, yard price $32.99; Pick-n-Pull Stockton 54 mi,
    5, $32.99; "Show all 12 yards".
  - Forecast in the card: "2003-2009 4Runner: About one every 2 weeks lands
    within 100 mi", bars 1 0 1 0 1 2 0 0, "5 in the last 8 weeks at 17
    yards", "Most land at: Pick-n-Pull - American Canyon (2), Pick-n-Pull -
    Salinas (1)".
  - Cars watch strip for the 4Runner: "4Runner, any year: About 5 a week
    land within 100 mi", bars 7 6 2 1 6 6 3 5, "36 in the last 8 weeks at
    17 yards", "Most land at: Pick-n-Pull - Stockton (6), Pick-n-Pull - San
    Jose North (5)".
  - Screenshots of that load: `ops/screens/game-plan-live-1119-{1,2,3}.png`.
- **Arrivals rules 2** (b1055c74): a batch-loaded week restarts a yard's
  coverage (5 yards, 610 of 196,802 arrivals on today's numbers); the index
  carries a rules version, so the next scan rebuilds the files once. No
  extra scan dispatched for it. To check after the next scan: the
  `[arrivals]` line shows "bulk week" and `index.json` has `rules: 2`.
- **Cloudflare, 24 h to 11:28 UTC** (cf-usage 44514626425): CPU EXCEEDED
  total 0; 14,634 requests, every one success or client-disconnected; API
  CPU p50 2.6 ms, p99 24.7 ms. The 11-18 fix holds. The 11:25 check-in is
  answered by this.
- Web only. The store apps (Android 1.13.2, iOS build 43 not yet
  submitted) do not have the list order, the card or the forecast. A
  1.13.3 needs the owner's "ship"; if it comes before Apple approves
  1.13.1, submit 1.13.3 instead of build 43 and save a review cycle.
- Not done / next: the card's forecast is for the seeker's own model and
  generation, not for every donor model; the `pf-yards/*` counters are not
  in the daily email yet; a forecast line on the public landed pages.

## 2026-11-19 ~11:40 UTC seventh independent nissan check: FAIL (1 WRONG); round 7 started

Check 1119g (seed 91371119, candidate at 0212ed03, branch
`interchange/verify-nissan-1119g`, head d0399b47, report
`groups/_report/nissan_verify_2026-11-19g.json` on that branch). Groups 18
RIGHT / 1 WRONG / 11 RISK; pairs 26 / 0 / 4. Its lot replay matches
`lot_replay.mjs` exactly (30,229 plain / 3,268 if equipped / 246 hidden).
Every gate in the sample was judged right with its basis on the pages.

- **WRONG:** 80730-89915 Versa 2007 (175 plain lot rows). Both 2007 Versa
  pages end the number inside the model year (sedan 12/2006-07/2007,
  hatchback 05/2006-01/2007, 8991A after), and the year carries no `built`
  gate. The checker's guess at the cause: the sedan and hatchback windows
  are joined before the cut test, and together they cover the year. Census:
  the only such vehicle-year in the candidate.
- **RISK kinds:** a changeover month at a model-year edge gated on one side
  only (FX35 2005 gated, 2006 not; M 2009 gated, 2008 not): 45
  vehicle-years / 26 groups / 1,268 plain; a number undated on its own
  page whose date split shows on another page (4 items); the `*` deciding
  AWD on 96301/96302-3JA9A (2 groups, 170 plain; round 5 put them back on
  purpose); numbers that sit in a different door on different models with
  no word about it in the note (6 groups, e.g. 82730-3Z005 rear on the
  Altima, front on the Sentra).
- Seven checks: 11, 2, 7 (the hub's own rule), 2, 2, 2, 1 WRONG. The
  classes get thinner each time; none of round 6's came back.
- **Round 7 started 11:40 UTC** (interchange builder resumed, branch
  `interchange/round7-1119`), live makes first:
  1. the window cut test runs against each body-variant page of a model
     year on its own, never against their union;
  2. a changeover month is treated the same on both sides: every
     vehicle-year whose build span holds the changeover gets the `built`
     gate (or leaves at the note cap);
  3. a number undated on its own page with a date split on another page of
     the same model: the narrower reading on every year it touches;
  4. a group whose number sits in a different door or position on
     different models is held until the note can name the donor's door
     (no note wording invented in this round);
  5. the two `*`-decides-AWD groups are held (reason: starred clause).
  Then an eighth independent check, new seed (used: 46021118, 61181118,
  73901118, 38271119, 52941119, 27641119, 91371119).

## 2026-11-19 ~13:00 UTC Alerts-tab forecast on main (jh-v218); round 7 on main; eighth nissan check started

- **Forecast under each watch on the Alerts tab** (builder A, branch
  `feat/watch-forecast-1119`, head 4de98e1b): a compact block (subject,
  headline, facts, eight small bars, the "past weeks, not a promise"
  label) under a watch that names one make and one model, has a centre and
  a finite radius, and has no trim filter, no drive filter and is not
  "Parts only". Anything else shows nothing. Rule 6: the watch list is only
  read; `watch_forecast_e2e` (30 checks) proves the stored list is byte for
  byte the same after four renders.
- **Full regression on `hub/rc3-1119`** (main + that branch): 109 passed, 2
  failed, 0 skipped; both layout halves pass (1,392 checks each). Both
  failures are tests overtaken by tonight's data, not the change:
  - `pf_plan_e2e` "forecast absent: the mount point is there, empty, 0 px":
    the real arrivals files exist on main since 11:17, so the real module
    drew a real forecast ("2004-2008 TL: About 8 a week land within 100
    mi"). The test now never serves the arrivals files; the card with the
    real module is `pf_forecast_e2e`'s job.
  - `tab_retap_e2e` "back to Cars: the same car at the top, in the same
    place (the alert card is above it)": the car came back in place (14 px
    before and after); the alert card was still on screen at the test's
    fixed 1800 px with today's list. The same failure on main without the
    change (run by the hub). The test now scrolls past the card.
  Re-run: `pf_plan_e2e` ALL PASS (91), `tab_retap_e2e` ALL PASS,
  `pf_forecast_e2e` PASS, `watch_forecast_e2e` PASS.
- **Pushed to main 12:55 UTC (416ab407), sw `jh-v218`.** Live check queued
  behind the deploy and the CDN.
- **Round 7 (interchange builder), branch `interchange/round7-1119` head
  9a5f78e9, merged to main at 084c178d.** Cause of the 1119g WRONG
  confirmed: `build_window` merged the windows of every page of a model
  year before the cut test (sedan + hatchback covered the year), and an
  undated row on one page made the year plain even when another page cut
  it. Now the cut test runs per page. Live makes: only toyota changed, 4
  Lexus headlight groups gained `built` gates (81145/81185-53543 IS 350
  2012; 81070-30B51/30B61 GS 430 2006); the other seven are byte-identical.
  Hub's own `live_diff.py`: 0 added groups, 0 gained app-years, 0 widened
  gates; `test_round7_1119` 21 checks; quick regression 74/0/0. Shipped
  pairs: plain 290,089 -> 290,075; if equipped 14,264 -> 14,278.
- Nissan candidate after round 7: 171 -> 153 shippable groups; plain pairs
  30,048 -> 24,198. Held: cross-position 5 groups (the number sits in a
  different door on different models), starred 47 groups, note cap 61
  groups, inferred cab 6, transmission tie 7.
- **Eighth independent nissan check started 12:58 UTC**: fresh agent,
  blind, seed 15841119, candidate at 084c178d, branch
  `interchange/verify-nissan-1119h`. Its brief now asks, for every sampled
  vehicle-year, for each body page on its own, the changeover month, option
  ties, hybrids, the door, and unexplained marks, and for the verdicts that
  would change under a one-month-different build span. Used seeds:
  46021118, 61181118, 73901118, 38271119, 52941119, 27641119, 91371119,
  15841119.
- For the owner, from round 7 (not acted on): a class sized but left alone:
  two same-option numbers on a page, both undated, no date anywhere (36
  vehicle-years on nissan, but 155 vehicle-years / 97 groups / 13,892 plain
  rows on gm); naming the donor's door on the row would let the 5
  cross-position groups ship (an app change); the note cap now refuses 61
  nissan groups.
- **13:09 UTC live check (one load, zip 95112): caches `jh-v218`**, no page
  error. Alerts tab, a 2003-2009 4Runner watch within 100 mi (made in the
  check's own throwaway browser): "8 in yard now" and under it the compact
  forecast "About one every 2 weeks lands within 100 mi", eight bars, "5 in
  the last 8 weeks at 17 yards", the "past weeks, not a promise" label.
  The Parts card (42 donor cars at 12 yards) and both full forecasts read
  as at 11:21. Screenshot: `ops/screens/game-plan-live-1119-4.png`.

## 2026-11-19 ~13:20 UTC eighth independent nissan check: FAIL (1 WRONG, a mislabeled lot car); two fixes started

Check 1119h (seed 15841119, candidate at 084c178d, branch
`interchange/verify-nissan-1119h`, head 86b211a3, report
`groups/_report/nissan_verify_2026-11-19h.json` on that branch). Groups 7
RIGHT / 1 WRONG / 22 RISK; pairs 14 / 0 / 16. No verdict moves with a
one-month-wider or narrower build span.

- **WRONG, and it is not a curation flaw:** lot car wap-STK039874 is listed
  as a 2017 QX80; its VIN decodes as a 2017 QX60 (3.5L). The listing/VIN
  check compares year and make only, so the car is a plain donor for a
  QX80-only regulator motor (82731-1MA0A) and for 3 more groups. This is
  the gap the hub wrote into `ops/data.md` at 04:xx UTC ("model mismatches
  are not flagged") and did not start. It applies to every make, live ones
  included: 3,143 lot cars have a listed and a decoded model with no word
  in common, most of them naming differences, a few hundred real.
- **RISK is much higher than in check 7 (22 of 30 groups)** because this
  brief asked for more per vehicle-year. Kinds: the claimed vehicle-year
  has no catalog page of its own in the raw (61 vehicle-years / 61 groups /
  3,029 lot rows; e.g. Altima 1995, Xterra 2004 and 2010, Rogue 2016); a
  build window taken from another model year's page (24 gates / 743 rows);
  several same-option numbers on a page, none dated; codes the pages never
  explain ("CC." read as crew cab, the "*", a "+"); "gas only" notes where
  the hybrid's own pages were never read (56 vehicle-years / 22 groups);
  Xterra 2005-08 mirror EA000 "W. 4WD. S. 6MT" with 4WD automatics plain.
- Hub's reading: the curation rules now hold (no curation WRONG in two
  checks running); what is left is what the raw cannot show. A clean pass
  needs either more pages read (a crawl: the owner's decision, like the
  open gm one) or a smaller candidate that claims only what its own pages
  carry.
- **Started 13:20 UTC:**
  1. Data builder (B) resumed, branch `data/model-mismatch-1119`: the
     listing/VIN check learns the model, from a hand-sorted table of the
     name pairs (same vehicle under another name / a different vehicle),
     each with its basis. A different-vehicle car gets the existing
     mismatch message, so every client, the released apps included, stops
     showing it as a plain catalog donor at the next scan. No app change.
  2. Interchange builder resumed, round 8, branch
     `interchange/round8-1119`: hold every nissan vehicle-year with no page
     of its own, take build windows from the car's own row only, hold the
     undated same-option siblings and the Xterra tie, say "checked on
     gas-model pages" where the hybrid pages were not read; and first a
     census of the same classes on the live makes (no live action without
     the hub).
  Then a ninth independent check on the smaller candidate.

## 2026-11-19 ~13:40 UTC listing/VIN model mismatch on main; a scan started by hand

- **Data builder (B), branch `data/model-mismatch-1119` head 5cb64f12,
  merged to main at a0a467eb.** The listing/VIN check now also compares the
  model, through a hand-sorted table `scraper/vin_model_names.json`: 505
  name pairs (6,036 lot cars whose listed and decoded model share no word
  after the scan's normalization), each with a one-line basis.
  - `same` 428 pairs / 5,737 cars (another name for the same vehicle): not
    flagged.
  - `different` 56 pairs / 121 cars: flagged "VIN decodes as <Make> <Model>
    (listed <model>)" in the existing mismatch field. Largest: Subaru
    Outback / Impreza 30 (Impreza Outback Sport), Fiat 500 / 500L 12, 500 /
    500X 10, Forester / Outback 5, Forester / Legacy 4; the 1119h car
    (QX80 / QX60) is one of them. Hub read all 56 bases: each names two
    plainly different vehicles.
  - `unsure` 15 pairs / 120 cars: not flagged (Subaru Legacy / Outback 96 is
    the large one).
  - `decode_wrong` 6 pairs / 58 cars (the builder's addition, and right):
    the VIN's own series and engine show the listing is right and the
    decoder's model name is wrong (Silverado decoded "S-10" 36 cars, all
    2001, full-size series codes; Genesis decoded "Equus" 10; FX35 decoded
    "FX50" 12). Not flagged. So the hub's 04:xx examples of "real
    mislabels" were mostly decoder errors.
  - Effect of the flag, with no app change and in the released apps too:
    the car card shows the warning; a Verified parts row drops to Likely; a
    catalog donor is never a plain row. Cars with any VIN flag: 265 -> 381.
  - Parts matching stays on the listing for a model mismatch (only a year
    mismatch re-matches on the VIN today). Open for the owner: re-match the
    121 on the VIN's model (113 parts lists would change), and the card
    tooltip's "The VIN is used for matching", which is true for the year
    only (an app text change; next shell batch).
  - A broken table never fails a scan (one WARNING, year/make checks only).
    New scan log line `[vin model] N car(s) flagged ... top unclassified`.
  - Tests: `test_vin_model_mismatch.py` 48 checks; `test_arrivals.py` 63;
    quick regression on the merged tree 75/0/0.
- **Scan 44535632042 dispatched by hand at 13:39 UTC** on a0a467eb.
  GitHub's scheduler has not started `scan.yml` since 05:13 UTC (the 08:00
  and 12:00 slots never ran), so this is the regular 4-hourly scan, 3 h 43
  min after the last one started, not an extra one. It will be the first
  with arrivals rules 2 and the model flag. To check after it: the
  `[arrivals]` line ("bulk week", `rules: 2`), the `[vin model]` line
  (about 121 flagged), and one live load.
- Worth the owner knowing: the scheduler gap. If GitHub keeps skipping
  cron runs, lists go stale; the daily ops email reports scan age. A
  second trigger (a scheduled task that dispatches the scan when the last
  one is over 5 hours old) would close it. Not built.

## 2026-11-19 ~14:00 UTC round 8 on main (candidate only); a large live class sized, not acted on

- **Round 8 (interchange builder), branch `interchange/round8-1119` head
  c7ecaa9e, merged to main.** Nissan only (`ROUND8_NS`): a vehicle-year is
  claimed only when its own catalog page carries it. Held: no page of its
  own (61 vehicle-years on the round-7 candidate), a build window borrowed
  from another model year's page (17), undated same-option siblings (155),
  claims that depend on reading "+" (29); "gas only" notes now say
  "checked on gas-model pages" where the hybrid pages were not read.
  Candidate: 153 -> 108 shippable groups (regulators 82, mirrors 16,
  climate 7, gauge 3), app-years 915 -> 617, plain pairs 24,198 -> 14,890.
  Hub check: the 8 live groups files and `docs/` are identical to main;
  `test_round8_1119` 24 checks; quick regression on the merged tree 75/0/0.
- **Part A census on the LIVE makes** (`groups/_report/round8_census_2026-11-19.json`;
  nothing changed):

  | make | vehicle-years with no page of their own | lot rows | beside undated same-option siblings | lot rows | pages a crawl would read |
  |---|---|---|---|---|---|
  | toyota | 600 (439 groups) | 94,567 | 239 | 7,798 | 122 |
  | gm | 173 | 37,555 | 212 | 15,598 | 57 |
  | ford | 47 | 9,731 | 2 | 279 | 15 |
  | subaru | 23 | 1,571 | 9 | 252 | 5 |
  | mopar | 12 | 2,106 | 96 | 16,129 | 4 |
  | vag | 4 | 832 | 0 | 0 | 1 |
  | mb | 0 | 0 | 18 | 122 | 0 |
  | hmg | 0 | 0 | 4 | 16 | 0 |

  No live gate borrows a window from another page. "No page of its own"
  means the claim rests on the part's product record (its fitment list)
  while the model year's own list page, where options, build windows and
  sibling numbers show, was never read: about 146,000 of the roughly
  290,000 plain donor rows. These are "Likely" rows ("verify the number on
  the part"), and seven makes passed their release samples with them; the
  nissan checks show what such a page can add. Hub's call: do NOT hold them
  on a census alone (it would halve the live catalog matches on no finding
  of a wrong fit). The honest next step is to read the pages: 204 list
  pages for the live makes plus 22 for nissan. A crawl is the owner's
  decision (like the open gm one); put to the owner 11-19.
- **Ninth independent nissan check: waits for scan 44535632042's commit**,
  so the lot it replays carries the new listing/VIN model flag (on the old
  pinned lot the QX80 / QX60 car would be plain again and the check would
  fail on a thing already fixed). New seed; used: 46021118, 61181118,
  73901118, 38271119, 52941119, 27641119, 91371119, 15841119.

## 2026-11-19 ~14:30 UTC owner up: status asked; Play listing pushed; profile picture made

Owner (14:20 UTC): "update? What did we push? Did we ship things? Are apps
the same color that we chose including the logo color change and what not?
Can I have a png of the logo I can use as my google profile pic?"

- Stores at 14:26 UTC: Play production 1.13.2 (42), completed (play-status
  44543563592). Apple: 1.13.1 build 42 still WAITING_FOR_REVIEW (submitted
  11-18 15:03; asc-status 44543558819); the live iPhone app is 1.13.0, the
  last build with the old colours and icon; 1.13.2 build 43 is in internal
  TestFlight.
- **Google Play listing pushed 14:28 UTC**: `store-listing.yml`
  (44543912651: icon, feature graphic, six phone screenshots and text in
  the petrol look, as prepared 11-17) and `play-subscription-listing.yml`
  (44543917581: the four benefit lines). Both succeeded; Google reviews
  listing edits like a release. They were covered by the owner's "Ship" of
  11-17 for 1.13.1 "in the apps and store listings"; the hub had held them
  for "after both stores accept" (`ops/release.md`), which made the Play
  store page show the old icon and screenshots beside an app that has had
  the new look since 11-18. Nothing on the Play side depends on Apple, so
  the hold was the hub's own and is dropped. Nothing was submitted to
  Apple.
- Profile picture for the owner: `ops/brand/yardscout-profile-dark-1024.png`
  and `-light-1024.png` (1024 px square, the mark at 64% width so a round
  crop keeps all of it; from `docs/brand/yardscout-mark-on-*.svg`).

## 2026-11-19 ~15:20 UTC scan 44535632042 verified (model flag, arrivals rules 2); ninth nissan check started

- **Scan 44535632042** (dispatched by hand 13:39 UTC on a0a467eb, finished
  15:03, commit b22c3640). Log warnings are Node deprecation notices only.
  - `[vin model] 118 car(s) flagged` (the table expected 121; the lot
    moved), 1 unclassified car in 1 pair (Chevrolet "10 Van" / "G-Series").
  - `[arrivals]` rebuilt under rules 2: 196,272 arrivals; `index.json`
    carries `rules: 2`; 610 arrivals left out under the bulk-week rule;
    covered weeks went down for Pick Ur Part (1), M&M Buffalo (1),
    Youngstown (2), RTP Maiden (2), Budget Bartow (3). 307 yards, 4 stale.
- **One live load 15:15 UTC** (2004 4Runner alternator near 95112): the
  card reads "42 donor cars at 12 yards within 100 mi"; the forecast draws
  in Parts, on the Cars strip and under the watch on Alerts; no page
  errors. A second load for the offline cache: `jh-v218` (15 entries),
  `jh-data-v1` (42), no failed requests.
- Apple at 15:10 UTC (asc-status 44552469720): 1.13.1 build 42 still
  WAITING_FOR_REVIEW (24 h in the queue). Next check 21:15 UTC.
- **Ninth independent nissan check started 15:17 UTC**: fresh agent,
  blind, seed 60231119, candidate at b22c3640, lot replay on b22c3640 (the
  first lot with the model flag), branch `interchange/verify-nissan-1119i`,
  report `nissan_verify_2026-11-19i.json`. New in the brief: item (h),
  every lot donor whose VIN decode names a different model than its
  listing. Used seeds: 46021118, 61181118, 73901118, 38271119, 52941119,
  27641119, 91371119, 15841119, 60231119.
- GitHub's scheduler: no `scan.yml` cron run since 05:13 UTC. The next
  slot is 16:00 UTC; if it does not start by about 17:40 (4 h after the
  last scan began) the hub dispatches the regular scan by hand again.

## 2026-11-19 15:21 UTC correction: the backup scan trigger exists and works (hub was wrong to call it "not built")

The 13:40 and 15:20 entries (and `ops/data.md`) said a backup trigger for
skipped scans was "recommended, not built". Wrong: two exist, and the hub
had not looked.

- `.github/workflows/scan-watchdog.yml`: hourly at :23 on GitHub's own
  scheduler, starts a scan when the last successful one began 5+ hours
  ago. GitHub runs it as irregularly as the scan itself (4 runs in the
  last 24 h instead of 24).
- `backend/src/scan_watchdog.js`: the same rule on Cloudflare's hourly
  cron, independent of GitHub's scheduler. Token configured; last decision
  readable at the API's `/v1/health` (15:20 UTC: 14:23 "scan active").
- What happened today: GitHub skipped the 08:00 and 12:00 slots; the hub
  dispatched by hand at 09:56 (4 h 43 after the last scan began) and 13:39
  (3 h 43), each time before the Cloudflare watchdog's 5-hour mark, so the
  watchdog never had to fire. Without the hub it would have started scans
  at 10:23 and about 15:23.
- So with GitHub's cron skipping, lists are at most about 6 hours old, by
  design. No owner decision is open on this. The hub does NOT need to
  dispatch at 17:40 (line in the 15:20 entry withdrawn); the 16:00 slot or
  the watchdog (19:23 UTC at the latest) starts the next scan.
- Observed delay of GitHub's scan cron over the last two days when it did
  run: 30 min to 2 h 47 min after the slot.

## 2026-11-19 15:22 UTC web builder (A) started: donor-model forecast on the part card

Branch `feat/donor-forecast-1119` (from fca57105; next sw `jh-v219`). Not
on main until the hub has reviewed it and run the full regression.

- The part card's forecast today counts only the searcher's own model
  generation. It will count the donor models the list's own matching
  accepts (parts-table fits and catalog groups), following "Verified
  only". The arrivals history knows make, model and year only, so the
  counted cars are never called donors: subject "Donor models", a models
  line, and a caveat that the list shows car by car which have the right
  engine and options. At most 4 make files; more, or a missing file, falls
  back to today's own-model forecast (no partial sums).
- Cars strip and Alerts watch rows stay on the own model.
- Same branch, own commits: the car-card tooltip stops saying "The VIN is
  used for matching" (true for a year mismatch only); the daily ops email
  gains one line with the card's counters (`pf-yards/*`,
  `watch-forecast/shown`, new `pf-forecast/donor-models`). The Worker
  deploy for that line is the hub's step after merge.

## 2026-11-19 15:40 UTC ninth independent nissan check: PASS (0 WRONG); round 9 started before shipping

Check 1119i (seed 60231119, candidate and lot at b22c3640, branch
`interchange/verify-nissan-1119i` head 093bcaef, merged to main at
bbd9591b; report `groups/_report/nissan_verify_2026-11-19i.json`).
Groups 20 RIGHT / 0 WRONG / 10 RISK; pairs 26 / 0 / 4. Lot 337,838 cars
(33,433 Nissan/Infiniti); replay 108 groups: 15,001 plain, 1,150 if
equipped, 31 hidden. No verdict moves with a one-month-different build
span; every build gate matches its pages; door and side match on every
claimed page across the whole candidate. First pass in nine checks.

Hub's decision: the pass criterion is met, but nissan does not go live on
this candidate as it stands, because of one thing the checker raised as a
suggestion:

- **33 of 82 window-regulator groups are motor-only numbers** by the
  catalog's own part name ("Motor Assy-Regulator"), 12,269 lot rows, some
  across platforms whose regulators differ (M37 with QX56, Murano with
  Rogue). The row does not say "motor". Live makes do ("window motor
  only" in the note). A user after a regulator would be sent to a car for
  its motor. The pages are read right; the row says less than it must.

Round 9 (interchange builder, branch `interchange/round9-1119`), nissan
may only shrink or say less, live makes byte-identical:
- A. "window motor only" on every motor-named number, from the page's
  name; mixed or unreadable names held; the same check for component
  numbers in the other categories; a census of names; a measure of the
  same on the live makes (no change).
- B. Holds, each as a rule with a census: model years whose variant pages
  were not all read (Rogue 2017 in 3 groups: 102 lot cars plain, most not
  the variant that was read; Sentra 1995-96 gauge); an undated number
  whose same-option twin changes inside the year (Altima 1994, 1995-96,
  Stanza 1995: 5 groups); unexplained body marks (QX50 2016 mirrors, 2
  groups); QX56 2013 gauge, an undated AWD-only sibling.
- C. Infiniti-site rows say "Nissan catalog": name the site the pages
  came from.
- D. Measure only: plain rows under a gas-only limit on cars with no
  engine decode, where the model has a hybrid that year (the documented
  app exception; 4 RISK items here). Hub decides after the numbers.
- E. Ship preparation on `interchange/nissan-ship-1119` (not merged): the
  namespace turned on, payload rebuilt, no cache-name bump.

Then: hub's own subset check (0 added groups, 0 gained vehicle-years, 0
widened gates against the checked candidate), a short independent check of
the new "motor only" wording against the page names, full regression, go
live, one live load.

Not acted on from 1119i: EX37 listed / EX35 decoded (one model, already
`same` in `scraper/vin_model_names.json`); "for both" in notes means the
searcher's car and the donor, not two models.

## 2026-11-19 16:02 UTC owner: "Great, ship and crawl and do whatever els[e]"

Owner (about 15:55 UTC), in reply to the nissan result. Hub's reading, stated to
the owner: "ship" = the 1.13.3 app release and "crawl" = the 226 catalog
list pages, the two decisions the hub had put to them under those words
(14:00 and 14:30 UTC entries); "whatever else" = the hub goes on with what
it recommends, inside the standing rules. Not read into it: "swap" (the
queued 1.13.1 at Apple stays in the queue).

- **Crawl** (task 81): the interchange builder prepares it first (part F of
  round 9, branch `interchange/crawl-own-pages-1119`): completion files
  from the round 8 census lists and raised worklist versions, through the
  existing completion mode; no change to fetch rules, pacing, allowlist,
  robots handling or stop conditions (rule 2). Rogue 2017 / Sentra 1995-96
  variant pages only if the existing crawler can reach them. The hub
  reviews, merges and dispatches `oem-fitment-crawl.yml`.
- **1.13.3** (task 80): one release with today's batch once it is on main
  and green: list order, the part card and forecasts (jh-v216 to v218),
  the donor-model forecast and tooltip fix (builder A), and the newer
  payload field (below). Android to production; iPhone built to TestFlight
  and submitted when Apple approves 1.13.1, in place of 1.13.2 build 43.
  If the batch slips past about 19:30 UTC, what is on main and green ships.
- **Nissan and older app versions** (hub decision): store apps bundle the
  shell and read new payloads with their own older gate code (iPhone users
  are on 1.13.0, which ignores every gate). For the eight live makes that
  exposure exists; nissan must not add to it. Part G of round 9: nissan
  groups go in a payload field only shells from this release on read, so
  older apps show no nissan catalog rows, as today. Nissan reaches the
  website when that merges, and the apps with 1.13.3.
- **Flagged cars re-matched on the VIN's model** (task 82): builder B,
  branch `data/vin-rematch-1119`; `different` class only, never Verified,
  listing fields untouched (rule 6); also sorts the one unclassified pair.
- Not started, on purpose: Subaru Legacy / Outback stays `unsure`; the
  note-cap relaxation and the readers' user-agent names stay as they are.

## 2026-11-19 16:12 UTC time labels corrected

The four entries above were first labelled 15:35, 15:45, 16:10 and 16:40
UTC: the hub had estimated the time instead of reading the clock. The
headings now carry the commit times (15:21, 15:22, 15:40, 16:02); the
owner's "ship and crawl" came at about 15:55 UTC, not 16:20 (the briefs to
the two builders say 16:20; same message). No 16:00 scheduled scan has
started by 16:10 UTC; the Cloudflare watchdog covers it from 18:39.

## 2026-11-19 16:14 UTC donor-model forecast: built, sent back once for calibration

Builder A, `feat/donor-forecast-1119` head 239dd15d (sw `jh-v219`), all
its tests passing (quick 76/0, forecast/pf set 16/0, layout 1,416 checks
per half). Hub read the app-side diff: the donor set comes from the
definitions the rows come from; tooltip and ops-email commits as asked.

Not merged yet, hub's call: for engine parts the count includes cars with
other engines (2002 ES 300 alternator: "About 72 a week", every 1997-2003
Camry counted). The caveat line is true but the number stands uncalibrated.
Sent back for: subject "Cars of the donor models", and one line of fact
from today's lot under the headline, "On lots within 100 mi now: 42 of 118
cars of these models are donors for this part" (cars = lot cars in range
matching the spec set; donors = the rows the list shows among them). No
scaled or estimated rate. The source fix (arrivals history split by
decoded engine) is a later data task.

## 2026-11-19 16:18 UTC catalog crawl started (owner "crawl"); builder B's re-match accepted, one addition asked

- **Crawl run 44564564713** of `oem-fitment-crawl.yml`, dispatched 16:18
  UTC on main 838b7f94 (merge of `interchange/crawl-own-pages-1119`
  fba96a9d: worklist, four completion files, a plan report, a test; no
  fetch, pacing, allowlist, robots or stop-rule code touched, checked by
  diff). Six sites: infinitipartsdeal, nissanpartsdeal, jeeppartsdeal,
  lexuspartsnow, toyotapartsnow, vwpartsgiant. 27 vehicle-year rows; 118
  requests if every number on those pages is already known, 622 at most;
  16 to 83 minutes at the crawler's own pacing.
- **Not in the crawl, and why:**
  - gmpartsgiant (57 pages), fordpartsgiant (15), subarupartsdeal (5):
    these sites refused the crawler earlier (`.blocked` on oem-raw) and a
    refusal is permanent (rule 2: no workaround). So the largest live class
    with no page of its own (gm 173 vehicle-years, ford 47) cannot be
    closed by crawling. Also blocked: moparpartsgiant, mbpartsgiant,
    bmwpartsdeal.
  - 37 of the census pages were already read on oem-raw after the pin the
    live makes ship from. They count only when the live makes are curated
    on the newer raw: a re-pin that can add claims, so it needs an
    independent check. After nissan.
  - Rogue 2017 (t32j, t32d) and Sentra 1995-96 (b14x) variant pages: the
    site rules read one variant per year; no new fetch path was written.
    Those vehicle-years stay held.
- Check-in set for about 17:45 UTC (conclusion, `.c2.done` per site, any
  refusal, request counts).
- **Builder B, `data/vin-rematch-1119` head 19b511ef: accepted.** 120 cars
  on the b22c3640 lot are matched on the VIN's vehicle (`different` class
  only); 112 lists change (rows 889 -> 838; 14 cars gain a list, 6 lose
  every row); listing fields unchanged; test 73 checks, quick regression
  75/0/0. "Parts only" watches: the answer changes for 20 cars; hub's call:
  that is match logic improving (rule 6), no stored watch is touched.
  Chevrolet "10 Van" / "G-Series" sorted `same`.
  Asked for one addition before merge: when the listing's and the VIN's
  makes are in different maker groups (77 cars; a Titan with a Yamaha VIN),
  the VIN is another vehicle's, so the match uses the listing's year too
  and no VIN-derived confirmation applies; the flag stays.

## 2026-11-19 16:20 UTC VIN re-match on main (21c10ba8); live with the next scan

`data/vin-rematch-1119` head 46385712 merged. Scraper only, no app
change.
- Hand-sorted mislabels (`different` class): parts matched on the VIN's
  make, model and year. On the b22c3640 lot 120 cars, 112 lists change.
- New, from the builder's own recommendation: when the listing's and the
  VIN's makes are in different maker groups (77 cars; the test is the
  existing `_trans_make_conflict`), the VIN is treated as another
  vehicle's: listing year for the match and for `spanYear`, no decode
  gates, no "VIN-confirmed" mark, no decode specs in the payload (trim,
  series, drive, engine, body, transmission); the flag stays. 21 of them
  have a parts list; 7 lists change (rows 169 -> 198, rows a wrong decode
  had ruled out come back as "if equipped"). One-maker-group pairs (GMC /
  Chevrolet, Chrysler / Dodge / Ram) unchanged.
- Hub on the merged tree: `test_vin_model_mismatch` 87, `test_arrivals`
  63, `test_vpic_fixes`, `test_interchange`, `test_model_normalization`
  all pass; the builder's quick regression 75/0/0 on its head. The full
  regression runs on the combined batch before the 1.13.3 build.
- To confirm in the next scan's log: "[vin model] N car(s) flagged ... (M
  matched on the VIN's model)" with M about 120, and "K VIN(s) of another
  maker's vehicle ignored" with K about 77.
- Report: `scraper/vin_rematch_2026-11-19.json`. Parts-table row to check
  noted in `ops/parts.md` (E-350 7.3L Power Stroke year window).

## 2026-11-19 16:50 UTC crawl 44564564713 finished: two sites read, FOUR MORE REFUSED (HTTP 403, permanent)

Run 16:18 to about 16:28 UTC, conclusion success; oem-raw head d867a65a.

| site | result |
|---|---|
| toyotapartsnow | finished, `.c2.done` (8 rows; 76 list lines, 8 year lines; 16:20-16:25) |
| vwpartsgiant | finished, `.c2.done` (1 row; 16:26) |
| infinitipartsdeal | HTTP 403 at 16:26:44 on its third request; `.blocked` |
| jeeppartsdeal | HTTP 403 at 16:27:00 on its second request; `.blocked` |
| lexuspartsnow | HTTP 403 at 16:27:16 on its second request; `.blocked` |
| nissanpartsdeal | HTTP 403 at 16:27:32 on its second request; `.blocked` |

- The crawler did what it is built to do: one refusal, the domain is
  stopped for good, the refusal is logged with request counts
  (`raw/<site>.refusals.jsonl`), nothing was retried. Rule 2: no
  workaround is written. All six sites are on the same hosting platform;
  the refusals began about six minutes and roughly 45 requests into the
  run, at the crawler's 8-second pacing, and then met every next site on
  its first requests.
- Blocked now: gm, ford, mopar, mb, bmw, subaru (earlier) and infiniti,
  nissan, jeep, lexus (today). Still open: toyota, vw, honda, acura,
  hyundai, kia, audi, mazda, mitsubishi, volvo. **The scheduled 6-hourly
  crawl goes on reading the open sites on the same platform; whether it
  should is a question for the owner (below).**
- What this does NOT change: everything live, and the nissan candidate,
  are built from pages already stored on oem-raw (pin 57e8b5b9). Nissan
  can still ship from them.
- What it does change: the 22 nissan / infiniti own pages, the 3 jeep and
  9 lexus pages will not be read; the nissan vehicle-years held for "no
  page of its own" stay held. The hub's dispatch cost four sites their
  future reading: the owner said "crawl", the hub chose to run six sites
  in one job.
- The route rule 2 names for a refusal is an email asking permission. To
  put to the owner: (1) a draft to the catalog operator asking for
  permission or a data arrangement (hub drafts, owner sends); (2) whether
  the scheduled crawl should pause on the remaining open sites until an
  answer comes, so they are not lost the same way.
- Check-in `trig_014D4eJ7LVizMXhBBto8jp6C` (17:44 UTC) could not be deleted
  (the session's permission check refused it); when it fires it is already
  answered by this entry.
- Owner's email question (16:49 UTC): the Cloudflare "Missing email?"
  notice is not a failure. The owner's test went from the same Gmail
  account the alias forwards to; Gmail hides the forwarded copy of a
  message the account itself sent (one copy, in Sent, 16:19 UTC, checked).
  A test from any other account settles it.

## 2026-11-19 16:53 UTC owner asked: two App Store Connect pages show different numbers; which vendor number goes in GitHub

Owner sent two screenshots (numbers kept out of this file where they
identify the account).
- Payments and Financial Reports, October 2026, legal entity shown: the
  owner's personal name, with its vendor number: 3 units, 22.92 USD,
  paid about Dec 3.
- Analytics, last 90 days to Nov 18: 523 first-time downloads, 19
  redownloads, 569 product page views, 10.4K impressions, 6 in-app
  purchases, 48 USD proceeds; download to paid: day 1 0.6%, day 7 0.8%,
  day 35 3.45%.
- Hub's answer: not a contradiction. One page is one fiscal month of paid
  sales for one legal entity; the other is 90 days of everything (free
  downloads never appear in financial reports). 3 of the 6 purchases fall
  in fiscal October. 22.92 / 3 = 7.64 per sale, which is 8.99 less Apple's
  15%.
- The vendor number on that page sits under the personal name, i.e. the
  entity that stopped receiving sales about 11-05, so it is most likely
  the one already stored as `ASC_VENDOR_NUMBER`. The one task 76 needs is
  the YardScout LLC entity's: the name on that page is a menu; choose
  YardScout LLC there and take the vendor number shown under it, as secret
  `ASC_VENDOR_NUMBER_LLC`. If the menu shows one entity only, the owner
  adds the number they see under that name anyway and the hub compares the
  two in `usage-stats.yml` (identical output means the same number).

## 2026-11-19 17:01 UTC LLC vendor number in; subscriber count fixed (Apple 4, Google 1)

Owner added secret `ASC_VENDOR_NUMBER_LLC` (about 16:55 UTC). No vendor
number is written here.
- `usage-stats.yml` run 44571628330, both numbers. They are different
  numbers: the first still has its newest sales report on 11-05 (naming
  both entities); the LLC one has reports from 11-05 to 11-17, Developer
  "YardScout LLC".
- LLC number, 11-05 to 11-18: 64 first-time downloads; 2 subscription
  sales, 15.28 USD (a new subscriber 11-10, a renewal 11-13).
- Active paid subscriptions by day: first number 4 until 11-12, 3 from
  11-13, 2 on 11-18 (one Cancel event 11-18); LLC number 1 from 11-10, 2
  from 11-13. A subscription shows under the old number until it renews,
  then under the new one (the 11-13 renewal moved one). So 11-18: 2 + 2 =
  **4 on iPhone**. The count had read the first number only and showed 2.
- Fix on main 3c971eef: `tools/store_subscribers.py` reads both numbers
  for the same report day and adds them (`apple_combine`; adding different
  days could count a moving subscription twice), per-entity counts in the
  output without the numbers; `store-subscribers.yml` passes the second
  secret; 8 new checks in `tools/test_store_subscribers.py`, all pass.
  Run 44572345210 stored: Apple 4 active, 0 trial, as of 11-18 (2 + 2);
  Google 1 as of 11-17. The daily ops email reads that value.
- This closes the 11-18 puzzle of "0 downloads since 11-06": they were
  under the LLC number.
