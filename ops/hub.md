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
