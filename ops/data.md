# Data quality workstream — status (opened 2026-11-04)

Owns: make/model normalization in `scraper/junkyard_scraper.py` (and its
tests `test_make_normalization.py`, `test_model_normalization.py`), the
lifespan writer `_write_model_lifespan_json` and `db.model_lifespan_stats`,
`scraper/test_model_lifespan.py`, and the lifespan display in `docs/app.js`
(`lifespanFor`, "leaves fast here", "Day N of ~X"); since 2026-11-18 also
yard list freshness (`scraper/yard_freshness.py`, its test, the app's
"YARD LIST FRESHNESS" block and share.js `yardListOf`).

## Rules specific to this work

- Saved watches are never rewritten (CLAUDE.md rule 6). Any normalization
  change must keep existing watches matching the same cars (match both
  old and new spellings if needed); add a test for that.
- Do not invent a lifespan. Where a yard's data is unreliable, the app shows
  nothing rather than a number.

## 2026-11-04 session — both open issues closed

Method note: the CI history DB lives only in the Actions cache (no download
path), so the 64-day history was rebuilt from the 293 scan commits of
`docs/data/inventory_live.json` (2026-09-02 → 11-04) with the same semantics
as `db.record_scan` (292 snapshots used; one, `d80f0fa5`, skipped on a
transient fetch error). All numbers below are from that rebuild; the CI DB
will differ slightly. The code change runs against the real DB on the next
scan, which publishes the real figures.

### 1. Split model spellings — fixed

Measured before (published `model_lifespan.json`, 17:29 scan): 640 model
keys, of which 54 groups were spellings of one model under one make
(`FORD|Focus`/`Ford|Focus`, `Lexus|Es300`/`Es 300`/`ES 300`, `Scion|TC`/`tC`,
`Dodge|RAM`/`Ram`, `MINI|Cooper`/`Mini|Cooper` …) plus 32 `General Motors|…`
keys (ION, VUE, Malibu, Cruze …). Live inventory: 2,198 make|model pairs,
53 groups colliding on case/space/hyphen (largest `Dodge|Ram1500` 113 rows
beside `Ram 1500` 3,579).

Two causes, two fixes:

1. **The history DB freezes make/model at first insert**, so every row
   written before the 2026-10 make/model merges keeps its old spelling and
   the writer counted it as its own model. Fix: `db.model_lifespan_stats`
   takes a `normalize` callback and the writer passes
   `_lifespan_canon_factory` = the scan's own three steps (`normalize_make`
   incl. the General Motors → division resolution by VIN/model,
   `normalize_model`, `resolve_model_blob` by cached NHTSA decode). Basis
   for each merge is therefore the existing canon tables plus the VIN
   decode; an unresolved blob stays a blob.
2. **~70 feed spellings had no canon entry** (`Ram1500`, `Trail Blazer`,
   `X-terra`, `325-I`, `Ats`, `300c`, `Blazers10`, `C/k 10`, `D-150`,
   `Allante'`, `Spectra 5`, `Fr-S`, `Le Mans`, bare Lexus `Gs`/`Es`/`Rx`/`Ls`
   …). Added to `_MODEL_CANON_BY_MAKE` with the audit cited; BMW rule now
   tolerates a hyphen; trailing apostrophes are stripped. Full list is the
   "2026-11 collision audit" section of `test_model_normalization.py`.

After (same writer on the rebuilt history): 531 model keys, 0 split groups,
0 General Motors keys; global median 61 → 60 d. Live inventory after
`normalize_model`: 0 collision groups except three one-row body-style
spellings (`F-150 ext cab`/`EXT Cab`) deliberately kept apart.

Deliberately NOT merged (different cars or different marques):
- `Dodge|Ram 1500` vs `Ram|1500`: marque split follows the feeds' own
  year boundary (3,476 of 3,579 Dodge-filed are ≤2010; 380 of 398 Ram-filed
  are 2011+). NHTSA itself decodes the 2011+ Dodge-filed trucks as DODGE
  (83) and the Ram-filed ones as both RAM (226) and DODGE (131), so there
  is no clean basis to move them. Watches already match across the two
  (`watchMatches` MAKE_IN_MODEL rule). Owner call if they want a year split.
- `Dodge|Ram` (37 departures, no decode) and `Dodge|Ram Pickup` (53) stay
  as blobs; `Ram` → `Ram 1500` only when the VIN decode says so (that
  resolved 1,928 → 2,308 Ram 1500 rows).

Saved watches: not touched. Proof added in two places:
- `test_model_normalization.py` "saved watches under old spellings": for
  26 old spellings, the scan's alert matcher (normalize both sides +
  substring) matches the renamed car, and the app's `canonicalModel` and
  the Worker's `canonModelLow` tables (parsed from `docs/app.js` /
  `backend/src/alerts.js`) map the old squashed key to the new canonical;
  also asserts the two JS tables agree.
- `backend/test/watch_match_unit.mjs` (node, real `watchMatches`): 36 → 58
  cases incl. `Ram1500`↔`Ram 1500`, `Trail Blazer`↔`Trailblazer`,
  `Es300`↔`ES 300`, `Allante'`↔`Allante`.
Mirror entries added to both JS tables (marked "2026-11-04 collision
audit"); `docs/sw.js` cache bumped to `jh-v141`.

### 2. Implausible yard lifespans — cause found, rule added

Per yard (rebuilt history; "flow" = live count ÷ departures per day, a
second estimate of lifespan that is immune to bad dates):

| Yard | median | flow | largest single-scan share of departures | verdict |
|---|---|---|---|---|
| Prestige Pull-Your-Part - Houston | 296 d | 22 d | 866 of 916 (95%) on 10-28 | **excluded** — the legacy endpoint had been frozen since 07-10 (newest `yard_date`); when the adapter moved to VinPlus the whole old list "departed" in one scan |
| Pick-n-Pull - Dallas South | 161 d | 124 d | 699 of 1,101 (63%) on 10-28 | **excluded** — the PnP index re-listed 360 cars dated Mar–Jun on 10-21 with no removals, then purged 699 on 10-28 (508 cold-start cars dated Mar–Aug + 184 of the re-listed). Same pattern at Sherwood (60%, excluded) and Little Rock (359 of 737 = 38%, under the line, 121 d stays) |
| Pick Your Part - Wichita | 180 d | 154 d | 19 of 699 (3%), 48 departure scans | kept — removals continuous, new listings dated 0.1 d before first seen, 21% of listed cars > 120 d old: a genuinely slow yard |
| Wrench-A-Part - Belton | 180 d | 143 d | 101 of 877 (12%), 35 scans | kept — genuinely slow; Lubbock / Del Valle / San Antonio WAP (120–139 d) look the same |
| San Antonio Pick-N-Pull (Independent) | 233 d | 208 d | 48 of 241 (20%), 8 scans | kept by the rule, **watch it**: only 13 days of history, 58% of listed cars > 120 d old; cannot yet tell a slow yard from a VinPlus tenant listing old stock |

Rule (`db.yard_departure_reliability`, thresholds `LIFESPAN_FLUSH_SHARE =
0.4`, `LIFESPAN_STALE_SCANS = 36` in `junkyard_scraper.py`): a yard's
departure data is unreliable when
- **flush** — the largest single-scan group holds ≥ 40% of its departures
  (every span in a flush is "time until the feed caught up"), or
- **stale** — it is still listed and no departure was detected in the last
  36 scans (~6 days; Pull-A-Part's weekly removal batches top out at 31).

Effect of an exclusion: `typical` null and no yard+model figures (the entry
ships as `{"typical": null, "models": {}, "unreliable": "<reason>"}` so the
file documents it), the yard's rows leave the chain, global and national
model aggregates, and the inventory payload's `avgLifespanDays`/`basis`
columns are null with **no chain/global fallback**. The app's `lifespanFor`
then finds nothing and shows nothing (no display change needed).

Measured effect: 70 of 299 yards with departures excluded (list in the
JSON; mostly small independents whose feeds remove in batches: Pull-N-Save
×6, U-Pull-It NE ×4, Chesterfield ×3, U-Pull-R ×3, BYOT ×5, Foss ×6,
Ryan's, Indy, Des Moines …), 223 yards keep a yard-basis figure, yard+model
figures 2,401 → 2,154, inventory-payload global average 66.7 d. Tests:
`test_model_lifespan.py` builds a flush yard and a stale yard and checks
verdicts, aggregates, the JSON shape and the payload columns.

Caveat on all lifespans: with 64 days of history the medians are mostly
cold-start cars (long-stayers over-represented), so figures will drift
down as history grows. Not a per-yard problem; noted for the owner.

### Next

- Read the next scan log for `[lifespan] excluded …` (only yards with
  ≥ 30 departures are logged) and the `unreliable` entries in
  `model_lifespan.json`; confirm Prestige and Dallas South show no number.
- Little Rock (38%) sits just under the flush line; revisit if the PnP
  index re-lists again.
- Owner question: year-split Dodge Ram → Ram (2011+)? Not done; no clean
  basis (see above).

## Manual-transmission detection (opened 2026-11-05, hub workflow wf_231e5bc1-597)

Baseline: 4,091 confirmed manuals of 333k cars (4,047 vPIC, 44 listing);
transmission known for ~49k cars; Ford/Toyota/Nissan ~0 confirmed. VW/Audi/
BMW/Mercedes VINs do not encode the transmission; build (PR/option) codes are
not public in bulk. Evidence tracks, each validated against the known-
transmission cars (>= 99.5% agreement) and adversarially re-checked:
1. VIN-encoded transmission from manufacturer Part 565 filings (NHTSA MID).
2. EPA fueleconomy.gov sole-offering: manual-only year/make/model/engine/drive.
3. Manual-only trims identified from the VIN decode/VIN patterns.
Work files: scraper/manual_detect/. Integration lands on a worktree branch for
hub review before merge.
- 2026-11-05 01:35 UTC: live accuracy fix b55e403. The manual-detection
  baseline found 14 vPIC cells (17 model-years) where vPIC returns "manual"
  for every decoded car although EPA lists automatics: 887 lot cars were
  badged Manual on that basis. `VPIC_TRANS_DEFAULT_CELLS` now drops the
  decoded transmission there (unknown, no badge); 1,193 cached decodes
  affected, nothing else. Live with scan 41949003681. True manuals in those
  cells return only through independent evidence (manual-detection work).
- 2026-11-05 integration (worktree branch, NOT merged, NOT live): the
  verified worklists (vin_rules_0..7, manual_trims, epa_sole) compile into
  `scraper/manual_detect/trans_rules.json`
  (`python3 -I scraper/manual_detect/compile_trans_rules.py`; rerun after any
  worklist edit, `test_manual_detect.py` fails on a stale table).
  `scraper/trans_evidence.py` applies it in `output_json`: precedence vPIC >
  listing > VIN code > manual-only trim > EPA sole offering; any
  disagreement records nothing; rule claims only ever add "Manual"
  (automatic codes only withhold). New transSrc: vin_code, trim, engine,
  model; app.js names them in plain words (badge tooltip + spec line), sw
  jh-v144. On the 17:18Z data (cached decodes, no network): confirmed
  manuals 3,207 -> 3,573 (+476 new, -110 withheld: 109 MY1997 Accords and
  the 1989 Integra DA344 where Honda's filing contradicts vPIC). Ground
  truth: manual claims 2,738/2,738, all claims 27,701/27,702.
  Hub decisions open: (1) the 1997 Accord rule is used conflict-only
  (CONFLICT_ONLY in compile_trans_rules.py; remove it to keep vPIC's 1997
  labels); (2) listing-vs-vPIC disagreements now record nothing (was:
  listing wins); no lot car has both today.

## 2026-11-06 — cross-family make in the model (owner report: Toyota "Audi A3")

Commit 4e6fbe7, scan dispatched 42308781489. Measured on the 21:10Z
inventory: **40 cars** (25 make|model pairs) have a model opening with a
different marque after the existing family rule — not ~480 as first
estimated. All Pull-N-Save / Nevada Pic-A-Part; 39 have a cached decode, and
the decodes show the rows are scrambled, not mislabelled (Toyota "Audi A3" =
JTEBU5JR0D5116438 4Runner; Acura "Bmw Rl" = WBAVC535X7FZ81105 BMW 328i;
Volvo/Lexus "Ls600hl" = S60s; Alfa Romeo "Hyundai Alfa-Romeo 4c" =
KMHEC4A40FA137265 Hyundai Sonata).

`resolve_foreign_make_model` (in `_apply_match`, and in the lifespan canon
with VIN only): confident decode agreeing with either make -> decoded
make/model; else strip onto a model the scan lists >= 3x under the row's
make; else raw text kept, row flagged `noPick`. Untouched: GM twins whose
make the VIN confirms, "Mini Ram", own-make spellings.
`noPickModels` {make: [models]} is in inventory_live.json and
inv/manifest.json; models.json moves those pairs to `noPick` (out of
`makes`). The app does not read it yet — sent to the design session.
Toyota folds: Rav-4 Sport/Prius Awd-E/T100 Pickup (canon, basis in code),
"EL" by VIN only, Scion tC/xB/xD filed under Toyota -> Scion when the VIN
decode names the same Scion model. Left: "Celica Supra", "Corona" (real
names).

Before/after on that data: 46 cars changed — vin 32 (19 of them change
make), canon fold 3, Toyota EL by VIN 1, Scion by VIN 10, noPick 2 (BMW
"Alfa-Romeo 4C" — decode is "750i, Alpina B7"; Lexus "Audi A6"), twin
untouched 3. Toyota 57 -> 49 names, Acura 20 -> 18, BMW 129 -> 127,
Dodge 134 -> 133.

Open / next:
- Same scrambling WITHOUT a make prefix is still there: Dodge "Civic Crx",
  "CL", "CSX", "EL", "MDX", "RDX", "RL"; BMW "EL", "MDX", "TSX". The VIN
  decode can fix these the same way (model not known for the row's make +
  confident decode of another make); not done here.
- BMW decode names with commas ("750i, Alpina B7", "750Li, Alpina B7") show
  up as models via blob resolution; should stay the blob.
- App/Worker canon mirrors (app.js `canonicalModel`, alerts.js
  `canonModelLow`) lack rav4sport/priusawde/t100pickup; the scan's alert
  matcher handles them. Add to both together (the mirror-agreement test
  requires it).

## 2026-11-07 — follow-up: another make's model without a make word; comma decodes

Commit d40a940, scan 42318061784 (published 4ebc0aa, 02:00Z). Rule
`resolve_other_make_model`: model not known for the row's make (< 3 cars)
and owned by exactly one other-family make (>= 10 cars) -> confident VIN
decode (make agrees with the row's make or the owner) wins; else noPick.
Skipped: numeric names, makes outside the mainstream list, Sprinter twins;
a decode agreeing with the row's model leaves it as is. `resolve_model_blob`
treats comma decodes ("750i, Alpina B7") as unconfident.

Counts. Pre-scan, on the 00:19Z data: 33 cars resolved by VIN (2 change
make), 9 noPick, 8 comma-named BMWs back to "7 Series". In the CI scan log:
other_vin 3, other_nopick 8, vin 20, scion_vin 10, twin 10. Live noPick
now: Chevrolet Capri/Ram1500, Chrysler XTS, Ford KONA, Mercury Aspen,
Plymouth SW, Pontiac Optima, Subaru Bravada.
Known false positive: a Dodge "Lancer" with no decode would be flagged
noPick (a real 1985-89 car). That follows the hub's "no decode -> noPick".

Follow-up commit (no scan dispatched; the next scheduled scan applies it): a
row whose own model is a comma list is flagged noPick. One car: US Auto
Supply's VIN-only feed takes the model straight from the decode ("750Lxi,
Alpina B7").

**Open, needs a hub/owner call — Pull-N-Save scramble moves between
columns.** `fetch_pns_inventory` sets `make` to the make we QUERIED
(getVehicles per make); the site's per-make answers include other makes'
cars with wrong models. Which column is wrong changes from scan to scan.
At 00:19Z JTEBU5JR0D5116438 was Toyota "Audi A3" (fixed to 4Runner); at
02:00Z the same car came back as Audi "A3", which no make-in-model rule can
catch. The 02:00Z data has 59 Pull-N-Save cars whose row make contradicts
a confident VIN decode across corporate families (e.g. Acura "MDX" =
Dodge Grand Caravan / Kia Optima / Subaru Outback). Proposed fix: for
Pull-N-Save rows only, take make/model from a confident decode when the
decode's make is in another family. Basis: the row's make there is our
query parameter, not the yard's data. Not done; it belongs to the
Pull-N-Save adapter (yards workstream) and needs a decision.

## 2026-11-08 — Geo Tracker watch regression; junk model names; modelYears

**Geo Tracker (5aa00ba, scan 42499474067, live 17:31Z).** The daily email
reported a saved "Geo Tracker" watch matching no car. No car was renamed (the
VIN rules skip Geo; Prizm/Metro/Storm untouched). Cause: noPickModels was
built per make|model pair from ANY flagged car. The PNS adapter flag
(3edce5b) on one undecoded PNS "Tracker" (Geo or Chevrolet) moved all 27 Geo
Trackers out of models.json `makes`. The same thing hid Ford F-150 (9,374),
Mazda3 (2,256), Sierra 1500, Express 2500, Fiat 500 ... Fix: a pair is listed
only when every car of it is flagged, in compact_inventory_v2 and in the
carry-forward merge. After: Geo Tracker 27 back, noPick 23 cars. No watch,
matcher or app change. "Ford Mustang Svt Cobra" and "Infiniti Q60 Coupe" are
already absent from the oldest models.json in the clone (2026-11-06 06:02,
before the VIN rules): no lot car carries those names, unrelated.

**Junk model names (3667837, live in the scheduled scan 42504914255,
18:43Z).** `junk_model_kind`: make alias ("chevy", "Smart", "Dodge"),
alternatives (" or ", "/" except canon names like C/K 1500 and Blazer
S10/Jimmy S15, and VIN blobs like SC 300/400 and Jimmy Or Envoy), bare body
type or "Unknown". Confident VIN decode -> decoded model, else noPick. Real
generic names are kept, with the basis in `_JUNK_MODEL_REAL` (Toyota/Nissan
Pickup, Nissan/Mazda Truck, Toyota/Mitsubishi Van, Saturn SW, MINI
Convertible, VW Bus, Dodge Ram, Range Rover, Fleetwood). "S10/S15/Sonoma
Pickup|Truck" fold into the canon "S10/S15/Sonoma". Audit on the 12:05Z
data: alias 49 cars (19 VIN / 30 noPick), alternatives 45 (9 / 36), body or
Unknown 77 (3 / 74). After publish: 0 junk names left in models.json `makes`;
noPick 134 cars / 72 names.

**modelYears** {make: {model: [min, max]}} (VIN model year where decoded,
else the listing year; 1900..now+1) in inventory_live.json,
inv/manifest.json and models.json: 81 makes / 2,053 pairs. The app on main
(design, 8bbac6d) filters pickers to span +-1. 2003 Chevrolet: 62 of 211
names. Limits: one span per model, no gaps (Caprice [1966, 2017]); a typo
year only widens (Impala min 1901 from an undecoded listing).

## 2026-11-09 — body style in vehicle_extras (design request)

`extraFields` gains "body" (index 5), from the cached vPIC bodyClass only
(`body_style_from_vpic`): sedan/coupe/hatchback/wagon/suv/pickup/van/
convertible, else "". SUT -> pickup, Step Van -> van; Incomplete, Truck,
Truck-Tractor, Limousine, Motorcycle, Bus -> "". Blank when the decode's
make contradicts the row's make across corporate families. On the
2026-11-09 data: 281,687 / 338,652 cars (83.2%) non-empty. No scan
dispatched; the next scheduled scan publishes it.

## 2026-11-09 Honda "Cr-Z" spelling (hub)
The auto-scan 77423a1 published one car as "Cr-Z", which split the CR-Z key. scraper/oem_fitment's model_map validator (M3/M5) then refused every curate run, blocking OEM fixes. Added "crz": "CR-Z" to _MODEL_CANON, plus a check in test_model_normalization. The next scan republishes the inventory with "CR-Z". Watches are untouched (rule 6).

## 2026-11-10 ~01:50 UTC (hub): scan no longer reverts merged interchange payloads
- Incident: scan run 42724288950 checked out 00dc804 at 23:55 and committed at 01:12. The "scan wins" rebase rule put its stale interchange payload over two newer merges (categories-ship ef5d52e6, wheels-ship-hmg e0ea686c).
  - Live dropped from 44 categories to 30, and from 50 wheels groups to 41 (no hmg).
  - The hub restored it at ec594131 by rebuilding on main.
- Fix in scan.yml, "Commit and push inventory": after every rebase, if scraper/ or the payload changed on main since the scan's checkout (SCAN_BASE), the step clears __pycache__ and reruns write_interchange_payload() on the rebased tree (main's code and groups + this scan's inventory), then amends the scan commit. If the rebuild fails, main's payload is kept and a warning is logged.
- Simulated in a scratch repo with a stub payload writer and all four cases correct: code changed mid-scan, rebuild fails, ops-only change, main didn't move.
- Still to watch: other generated docs/data files built from code (not only the scan) still take the scan's copy on conflict. None is known to be code-built today besides the interchange payload.
- 2026-11-10 ~13:00 UTC (hub): the feed spelled one Jeep "J-10" (auto-scan 6f12e6d), which split the J10 key and broke curate M3/M5 (same pattern as Cr-Z). _MODEL_CANON jeep gets "j10": "J10", with a test in test_model_normalization. The next scan writes the canonical name.

## 2026-11-13 — notableTrims in the scan output (design/notable-trims)

New top-level field `notableTrims` in `docs/data/inventory_live.json` and
`docs/data/inv/manifest.json`: `{make: {model: [word, ...]}}`, the trim
words the parts table gates NON-option rows on for that make/model
(`notable_trims_from_spans` in junkyard_scraper.py, over the scan's
`modelYears` spans, with the same entry selection as `match_vehicle` via the
new `_keyword_hits` / `_matched_entries` helpers; row yr_min/yr_max
respected). Left out: option rows, words already in the model name, words
with no letters, body styles gated through "trim". Recomputed after a
stale-keep carry-forward. ~6 KB, 244 make/model pairs on the 11-13 data.
The app's trim badge and Cars Trim filter read it; before the first scan
after the merge the field is absent and the app shows neither. Refactor of
match_vehicle checked identical on 37,407 (year, make, model, decode)
combinations against main. Test: `python3 scraper/test_notable_trims.py`.
- Data-quality gap (for this workstream): vPIC trims rated `usable` include
  multi-trim lists ("SE / SE NAVI / Limited / Limited NAVI" on 254 Sonatas,
  "Sport, R/T" Dakotas, "Base/ BaseStyle/ Base Tech Turbo/ Turbo Ultimate"
  Velosters) and negations ("Premier (non R design)" on Volvo S60s). The
  app now ignores those for the badge, but the scraper's trim gate
  (`_gate_hit` on trim + series, whole words) treats any word in such a
  list as a match, so it can VIN-confirm a trim-gated part the car may not
  have (not measured here).
  Recommendation: rate such decodes `ambiguous` in the trim-quality pass.
- Hub follow-up: notableTrims also carries `NOTABLE_TRIM_LABELS` words
  (labels only, appended after the gate words; list and drops in
  ops/parts.md). 248 pairs, ~6.5 KB. Badged cars on 11-13: 1,809 across
  61 make/model names (1,686 from gates + 123 from labels).

## 2026-11-18 — yard list freshness (branch data/yard-freshness-1117, hub review)

Owner ask (11-17, "watertight"): be honest when a yard's own published list
has gone stale. Before this, the scan only logged it (`STALE YARD`); the
app showed an orange "yard list unchanged since" stamp on the car screen
only, from yard_health.json, at 3 weekdays (a guess).

### What the scan publishes (`scraper/yard_freshness.py`)

Four columns appended at the END of every yard row in inventory_live.json,
inv/manifest.json and the API's yard directory (push_inventory copies
`yardFields`/`yards`, so `/v1/yards` carries them without touching
backend/src), named in `yardFields`:

| column | meaning |
|---|---|
| `listChangedAt` | scan at which a car was last ADDED or REMOVED (id set; a date-only edit is not a change) |
| `listState` | `""` / `"stale"` (3+ full business days unchanged) / `"frozen"` (10+) |
| `listReadAt` | null when this scan read the yard; else the last scan that did (carried yard) |
| `listFlushAt` | a frozen list that then changed by >= 40% in one scan (kept 8 days) |

Unread scans (stale-keep carried, or yard missing) neither change nor
confirm a list; the next read is compared with the last READ copy, and the
flush check asks "frozen as of the last read" (unread days are not frozen
days). yard_health.json gets the same values (`listFingerprint`,
`listChangedAt`, `listReadAt` only when it is not that scan, `listFlushAt`;
+23 KB raw on a 51 KB file the app also loads); its own fields, which the ops
email reads, are unchanged. First scan after merge: a yard whose
id|date fingerprint did not change seeds `listChangedAt` from its
`lastChangedAt` (so the dates match the ops email from day one); anything
else seeds "now" (never claims a list is older than known).

Compatibility: positions 0..6 of a yard row are untouched; every reader
found indexes them by position (app `expandV2Row` y[0..6], Worker
`inventory.js` y[3]/y[4]) or by name (`yardFields.indexOf`), so old app
builds in the stores and the current Workers ignore the extra columns.
Cost: +11 KB raw / +0.6 KB gzipped on the 304-yard table (manifest 121 KB);
the Workers read it from the directory they already parse.

### Thresholds: how they were measured

Sources reachable here: 163 committed versions of yard_health.json and 160
of inventory_live.json (2026-10-25 16:15 -> 11-18 13:47 UTC; the clone is
shallow, nothing earlier). The CI history DB (Actions cache) is not
reachable. Per yard, a "change" = the id set differs from the last scan
that READ the yard; gaps spanning an unread scan (192) set aside. Unit:
full business days = weekdays whose 14:00-22:00 UTC block lies wholly in
the gap (the ops email's `fullBusinessDaysBetween`), Thanksgiving + Friday,
Dec 24/25/31 and Jan 1 not counted (no holiday was in the window: that rule
is judgment, not measurement).

6,791 closed gaps, 301 yards (cumulative): 0 bd 65.5% · 1 bd 95.3% · 2 bd
98.9% · 3 bd 99.4% · 4 bd 99.7% · 5 bd 99.8% · 6 bd 99.87% · 8 bd 99.97% ·
10 bd 99.985% · 12 bd 100%. Calendar days: p50 0.83, p90 2.76, p99 4.67,
p99.9 11.0. Weekends are the 1-bd bump (a daily yard's Fri->Mon gap).

Healthy = the 265 yards whose median gap is <= 1.25 days (daily updaters).
Share of their yard-scans that a threshold would flag / yards ever flagged
in 24 days: 2 bd 2.84% / 94 · **3 bd 1.00% / 25** · 4 bd 0.57% / 16 ·
5 bd 0.35% / 5 · 6 bd 0.22% / 2 · 8 bd 0.13% / 2 · **10 bd 0.05% / 1**.
Daily yards' 3+ bd gaps: 27 of 6,561 (0.41%), all plausibly feed lags (five
yards of one feed together 10-22 -> 10-28, Pull-A-Part, Pick-n-Pull Carson
City/Kelowna, Flagstaff 8 bd). The 36 slower yards are weekly-batch feeds
(Foss, EZ Pull N Pay, Shelby, Utah Pic-A-Part Ogden, St. Cloud ...) and
Budget Bartow (~12-day cycle, 8 bd): 3 bd flags 25% of their scans, 10 bd
2.2% (5 yards).

- **Stale = 3 full business days** without a car added or removed: almost
  never on a daily updater (1% of scans, all lag-shaped); 2 bd would flag
  ordinary lulls (173 gaps). Weekly-batch lists will carry the notice part
  of most weeks; their lists really are days old then.
- **Frozen = 10 full business days** (two working weeks): 2 closed gaps in
  the window ever reached it (Eichelberger's 12, M&M Buffalo 10); the
  slowest regular updater (Bartow) peaks at 8.
- Flush: the lifespan writer's `LIFESPAN_FLUSH_SHARE` (0.4), one constant
  (a test checks they agree). No post-freeze flush happened in the window
  (Eichelberger and M&M resumed with 3% and 9% changes, i.e. real
  arrivals); the canonical case is Prestige Houston on 10-28 (frozen since
  07-10, then 866 of 916 replaced).
- The ops email's per-yard rule (3+ weekdays, today counted) flags 1.45% of
  daily yards' scans / 53 yards; it stays as is (an early warning for us);
  the visitor-facing rule waits for one more complete business day.

### What would be marked today (11-18 13:47 UTC data, first scan after merge)

Frozen: Wrench-A-Part - Holland (1,113 cars, since Oct 22), UAPI -
Alexandria (827, Oct 29), Colorado Auto & Parts - Englewood (283, Oct 28),
Utah Pic-A-Part - Orem (Premium) (86, Oct 22): 4 yards, 2,309 cars.
Stale: Youngstown U-Pull-It (1,557, Nov 6 UTC), Paul's Auto Yard - Lake
Station (1,399, Nov 10), M&M U-Pull-It - Buffalo (702, Nov 12), Foss
U-Pull-It - Wilson (675, Nov 8): 4 yards, 4,333 cars. 14 more sit at 2 bd
(Pull-A-Part Canton / Corpus Christi / New Orleans West, BYOT Baton Rouge /
Jackson, RG Anthony ...) and turn stale at 22:00 UTC if still unchanged.
Agreement with the ops email: the same "since" date for all 8 (seeded from
`lastChangedAt`); the email's frozen list has those 8 plus the 14 at 2 bd.
Over time the id-only date can be earlier than the email's: on 11-18 19
yards' `lastChangedAt` was one scan after their last id change (a date-only
edit the scan after), and Utah Pic-A-Part Ogden (Premium) / Army's Auto
Wrecking - Lima have had date edits only since Nov 2 / Nov 10.

### What a visitor sees

- App tiles (stale or frozen yard): a quiet `badge-long` chip "List
  unchanged since Nov 6" in the status slot (before New / Leaving soon).
- App car screen: in place of the stay meter, the quiet `.long-listed`
  notice "This yard's list has not changed since Nov 6. Call before you
  go." (+ ", and we have not been able to read it since Nov 16" when the
  last scan could not read it); frozen adds "Until it changes, its cars are
  left out of Newest arrivals and alerts." The orange stamp is gone.
- App Yards tab card and the yard's rows sheet: the same notice.
- Frozen yard's cars and flush cars: not "New", not in any "new this week"
  count or the New / This week / since-last-visit chips, and sorted after
  every other car in Newest arrivals (unless that yard is picked). Still
  listed, still searchable, in order on the yard's own views.
- Site worker /yard/<slug> and /car/<key>: the same sentence (UTC date with
  year); the car page drops the "~N days left" countdown and the yard
  page's new-this-week list leaves held cars out.
- Alerts (all paths read push_inventory's arrivals) and the weekly counts in
  landed.json, landed/<make>.json and junkyards.json skip held cars.
- Old data files (no columns): the app falls back to yard_health at 3
  weekdays, shown the new quiet way; nothing is held back.

Tests (all pass): `python3 scraper/test_yard_freshness.py` (64 checks),
`node backend/test/yard_list_unit.mjs` (24), `node backend/site-proxy/test/
yard_list_pages_unit.mjs` (23), ui_no_truncation SCREENS=list-stale-tiles,
list-stale-detail,list-frozen-yard,list-frozen-rows at 320/390/768/1280
(64 checks). Re-run unchanged: test_inventory_shards, test_model_lifespan,
test_junkyards_json, test_landed_models, test_notable_trims,
test_photo_sources, and the five site-proxy unit tests. sw jh-v209.

### Open / for the owner or hub

- Decisions to confirm: 3 / 10 business days; weekly-batch yards showing
  the notice part of each week; frozen cars moved to the end of Newest
  arrivals (not hidden, unlike dormant yards); the flush rule applies only
  after a 10-bd freeze, as asked, and holds 8 days by set-out date; a stale
  (not frozen) yard's new cars still alert; holidays list.
- Suggest: the same 40% hold for ANY single-scan change, not only after a
  freeze. Measured re-keys and flaps that re-added whole lists: Ryan's
  Detroit 10-26 (+1,348), U-Pull-It Omaha N/S, Lincoln, Des Moines and
  Prestige 10-28 (+4,313 new ids), Indy-U-Pull-It alternating two lists
  every scan 10-30 -> 11-09, Pull-N-Save Riverside likewise; new ids defeat
  the Worker's per-vehicle alert dedupe for cars dated in the last 3 days.
- Hub: the ops email could read `listState` for its per-yard frozen list so
  the email and the site name the same yards (one line in ops_monitor.js).
- Yards workstream: outreach / adapter check for Holland (since Oct 22),
  UAPI Alexandria, Colorado Auto & Parts, Youngstown, and Budget Bartow's
  12-day cycle.
- Backend (other builder): saved-car "leaving soon" alerts
  (saved_alerts.js) still count days against the typical stay at a frozen
  yard; a flush also sends "gone" for every car it removes at once.
