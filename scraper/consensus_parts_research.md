# Consensus top-selling used-parts research (2026-10)

Research notes behind the **2026-10 consensus evergreens** expansion in
`junkyard_scraper.py` (search for `_EVERGREEN_PARTS`). The owner asked whether
a creator's "top 25 parts to sell" list could be used. Legal guidance: facts
are free, expression isn't — so **no single creator's list or wording is
reproduced**. Instead, each category below is a fact confirmed independently
by **3+ public sources**. Sources are cited here (not in the app).

Source key (all publicly accessible, retrieved 2026-10-22):

- **[PAP]** Pull-A-Part (self-service chain) blog, "Valuable Car Parts at a
  Junkyard: What to Pull and Skip" — blog.pullapart.com
- **[JYI]** JunkyardInventory.com, "Top 10 Most Valuable Junkyard Parts to
  Pull & Resell (2026)"
- **[ROW]** RowGold guides: "Junkyard Parts to Sell on eBay" and "Junkyard
  Parts Flipping" — rowgold.com
- **[REP]** Reparta, "Most Profitable Car Parts to Sell: Ranked Guide (2026)"
  — reparta.com
- **[RF-1]** r/Flipping, "Auto parts flipping" thread (2024)
- **[RF-2]** r/Flipping, "Does anybody here flip used auto parts" thread
- **[RF-3]** r/Flipping, "I tracked junkyard inventory for 30 days" thread
- **[YT]** Several parts-flipper creators' publicly stated category lists
  (incl. a "top 25 parts" video); used ONLY to confirm categories that at
  least two non-creator sources also name — no rankings, order, thresholds,
  or phrasing copied.

## Categories added (3+ sources each)

| Category | Sources | Used sold basis (working parts) | Band wired (anchor → displayed) |
|---|---|---|---|
| Alternators | PAP, REP, RF-3, JYI(FAQ) | $35–80; Toyota/Honda fastest | 35–90 → ~$30–70 |
| Starters | PAP, REP, ROW | $30–65; bench-test/disclose | 30–75 → ~$25–60 |
| Gauge/instrument clusters | ROW, REP, JYI, YT | $40–150 commuters; tach/digital higher; disclose mileage shown | 50–140 → ~$45–105 |
| Climate control panels | ROW, REP, YT | mostly $40–120 | 40–110 → ~$35–85 |
| Window regulators (w/ motor) | RF-1, ROW, REP | $35–85; common failure item | 30–75 → ~$25–60 (existing audited band) |
| Power window master switches | RF-2, ROW, YT | $25–80; test every button | 30–90 → ~$25–70 (existing audited band) |
| Engine/body control modules | RF-2, REP, ROW | $40–150 high-population apps; many need programming — caveat shipped in sell notes | 40–140 → ~$35–110 |
| Manual tow mirrors (90s–00s full-size trucks) | existing category (ROW/JYI mirrors + truck demand per RF-3); gap was generational | pairs $60–150 | 60–160 → ~$55–125 (matches audited GMT800 row) |
| Steering wheels (pre-airbag-era trucks only) | YT, ROW (interior), yard price lists carry "STEERING WHEEL" as a standard category | $50–150 clean/uncracked | 50–150 → ~$45–115 |

Already well covered before this pass (no change needed): headlights/tail
lights, door mirrors, seats incl. 3rd row, infotainment/radio units, tailgates,
grilles, OEM wheels (targeted), premium audio, towing mirrors on modern trucks.

## Fitment rules

- The seven "evergreen" categories apply to ~105 high-population entries
  (volume-ranked against the 2026-10 national scan, ~252k vehicles). Classic /
  exotic / enthusiast entries keep curated lists — a $30 alternator line on a
  Supra entry is noise.
- Token dedupe: an entry that already tracks a category (e.g. Ram gauge
  clusters, Camry alternator) keeps its hand-tuned band.
- Manual tow mirrors: added only to the pre-power-fold truck generations that
  lacked any tow-mirror row (OBS + 10th-gen F-150, 2nd/3rd-gen Ram, C1500);
  option-flagged ("if equipped", $0 toward ranking value) like every other
  tow-mirror row.
- Steering wheels: year-gated to pre-airbag model years (Ford/Dodge trucks
  ≤1993, GM C/K ≤1994) so the wheel ships bare.

## Deliberately excluded (and why)

- **Airbags, inflators, airbag covers, seatbelt pretensioners** — eBay
  prohibits ALL airbag/inflator/airbag-cover listings sitewide effective
  **2026-09-24** (vehicle parts & accessories policy; other SRS electronics
  are US pre-approved-sellers-only). Federally, the render-inoperative rule
  (49 U.S.C. 30122) and NHTSA guidance make used SRS parts a liability chain
  this app won't touch. PAP's own guide says leave them. Nothing in the DB
  names an airbag; steering wheels are pre-airbag-era only.
- **AC compressors** — real resale exists (REP, JYI) but internal failure is
  invisible at the yard, install needs refrigerant handling, and contaminated-
  system returns are common. Fails the app's "stand behind the band" standard.
- **Power steering racks** — safety-critical steering + heavy, messy pull;
  ROW explicitly flags steering components as liability categories.
- **Catalytic converters** — provenance/legal restrictions (state scrap laws);
  most self-service yards restrict or strip them anyway.
- **Sun visors, cup holders, center caps** — named by one creator and REP's
  "overlooked smalls", but medians sit below the app's meaningful-money bar;
  console lids already exist where the market is real (trucks).
- **Engines/transmissions** — out of scope by app charter ("no engines, no
  transmissions — parts you can carry out").

## Downstream check (maxValue consumers)

`maxValue` = highest calibrated high among CONFIRMED parts. Verified consumers:
gold-first sort and value display in the app, free-tier value stripping,
carry-profit ranking in the scraper. There are **no hard dollar thresholds**
(no "worth the trip" cutoff) that a band shift could break. Option-flagged
parts (tow mirrors) contribute $0 to ranking value, so truck maxValues didn't
jump from unconfirmed options. The "Going fast" stat counts `sell_speed ==
"Fast"` parts; all new categories ship at Medium, so that stat can only stay
the same or grow via existing Fast parts.
