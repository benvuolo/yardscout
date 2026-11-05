# OEM fitment curation and integration spec

Status: implementable spec, 2026-11-05 (~01:50 UTC). Workstream: Interchange
(`ops/interchange.md`). It synthesizes two independent designs. Design A is
"accuracy-first closed world"; Design B is "maximize pairs from part-number
structure". Both were checked against the first real crawl checkpoint,
**oem-raw@f2652c3**: `raw/www.toyotapartsnow.com.jsonl`, 363 records, 7 seed
model-years, retrieved 2026-11-05 00:50:41Z–01:23:03Z. No Jeep raw existed at
that commit. Nothing here relaxes CLAUDE.md rules 1–8.

Reading order for implementers: §0 (decisions), §2 (what Verified means),
§5 (curation rules), §7 (integration), §8 (validator), §9 (tests).

---

## 0. Decisions

**Base: Design A.** A proves a closed world for each vehicle-year and
category. Every kind of ambiguity can only remove claims, and an oracle test
checks soundness. A gives "a false Verified is impossible by construction" the
better shape. Most of B's levers fit inside it as later phases.

**Grafted from B:**
- the old-client constraint (native apps read the live `interchange.json`
  with their bundled logic);
- new kinds routed to `categoriesV3`;
- a single door slot per window regulator, with packaging resolved inside it;
- the hybrid alternator/starter over-claim fix;
- worklist-driven completion crawls ordered by gain;
- the kits/sets, RHD and rule-4 guards;
- the model-map "no silent drop" and match self-test lints;
- withhold-not-raise when evidence conflicts;
- the directional (subset) membership rule;
- per-lever attribution metrics.

**New, from the real checkpoint (both designs missed these; §1):**
1. Conditions are carried by **each vehicle's own list-page notes**, and they
   can contradict the product page's fitment table.
2. A **closed-vocabulary note classifier** that fails closed replaces
   deny-list regexes.
3. **Plant of manufacture** ("US Built" / "Japan Built") is the most common
   splitter. It is decode-checkable from VIN position 1 (Phase 2, gated).
4. Toyota `-84` remans arrive with `reman:false`.
5. `other_names` names the wrong side in 35 of 166 mirror records.
6. In option-layout rows, the engine column lists every engine of the model,
   not the engines the part fits.
7. The parser's reman-drop rule can delete the only current listing. More
   broadly, 20 of the 39 successor numbers named on list rows have no
   record.

### Safety conflicts resolved (stricter rule taken)

| # | Topic | A | B | Taken | Why |
|---|---|---|---|---|---|
| 1 | Where OEM claims ship | `platformGroups` / `vg` | `platformGroups` / `vg` (old-safe) | **New keys `oemGroups` / `oemVg`, read only by the new client.** Old keys may only *lose* claims. | Old native clients (iOS 1.12.10, Android 1.12.11) apply none of A's required guards: fail-safe tier, VIN identity guard, `rowWarn`. They also render `g.label`/`g.note` into the header **unescaped** (`groupNotes.push(`${g.label}: ${g.note}`)`). B is right that they read the live file. That is exactly why no new claim may go where they read. |
| 2 | Window-regulator components | each component (regulator, motor, assembly, `regulator?`) is its own sub-slot | one door slot, component as an attribute | **One door slot. Packaging must be exactly one allowed configuration (§5.8).** | Real counterexample to A. 1999 Camry rear doors list 69804-AA010 "Regulator Sub-Assembly" (note "Power"), 69840-AA040 "Regulator Assembly, Rear Door Window" (note "Manual") and motor 85720-AA030, all CE/LE/XLE. Under A's sub-slots each holds one number. A's option tokens include neither "power" nor "manual". Only an unrelated SE row inflating the trim universe stops A from verifying a manual-window donor for a power-window seeker. |
| 3 | Option partitions (HID vs halogen, heated vs not) | never Verified | "Verified, if equipped the same" | **Likely, with both numbers named** (owner question Q1). | The seeker's option is not known to us, and old clients cannot show the condition. |
| 4 | Superseded members whose own fitment was not read | `uncrawled_chain_member` blocks | tolerated (README "or a stated supersession") | **Block.** Every member the donor could carry must itself list the seeker unconditionally (E2). | A consolidated service number does not prove that its predecessors interchange. Real example: 87910-33670-B2 ("Without Heated") replaces two numbers, 87910-33660-B2 and -B0. |
| 5 | Supersession consolidation (B replaces A1, A2; both list T) | `option_split` | one union-find family | **`option_split`** (the candidate set must be a chain) | Same reason as #4. |
| 6 | Blank Trim cell in a trim-layout row | `trims_unknown` | unrestricted after a spot check | **Unknown** (cannot be coverage) | Fail closed. The checkpoint has 0 such rows, so this costs nothing today. |
| 7 | Thin universe | needs at least 5 verified records from at least 3 categories (or a year-page trim list) | at least 3 families in at least 2 categories | **A** | A's threshold is larger. |
| 8 | Evidence age | 180 days | 120 days | **120 days**, applied at curate time and again at payload-build time | Shorter. Build-time expiry also fails closed when crawls stop. |
| 9 | Universal-part cap | 12 feed models per class | none | **12** | A part number listing many models is more likely a catalog aggregate than a real one-part fit. |
| 10 | Spot-check gate | 30 closures + 30 pairs, 0 errors, separate session | 20 pairs, 20/20 | **A** (60 items, 0 errors) | Larger sample, and it covers closures. |
| 11 | Systemic parse failure | per-record evidence re-check makes that record unverified | more than 2% failures withholds the (namespace, category) | **Both** | Union of the two. |
| 12 | Cross-model Likely groups | `platformGroups` tier "likely" | none in old keys | **`oemGroups` only** | Old clients stack header notes and do not escape them. |
| 13 | New categories (ac-compressor and others) | `INTERCHANGE_PART_CATEGORIES` with kind "oem" in `categories` | `categoriesV3` | **`categoriesV3`** | Old clients send an unknown kind into the same-model generation loop and show "Likely" for engine-dependent parts. |
| 14 | Hand groups contradicted by closed OEM evidence | demote the legacy group in the payload | withhold OEM, never touch hand groups | **Both: demote the legacy pair to Likely and withhold OEM Verified for the cells involved.** | When two Verified sources disagree, neither ships Verified there. A demotion is a claim removal, so it may reach old clients. |
| 15 | Bad generated file at scan time | drop that namespace (fail closed) | raise on schema errors | **Drop + `oemStatus` + ops email at scan time; strict raise in tests** | The 4-hourly scan must keep publishing inventory, and nothing unvalidated ships. |
| 16 | Differing duplicate records | both kept, rows `disputed` | newest wins, `changed_between_crawls` flag | **Disputed (unverified)** until a re-crawl record names the line it supersedes (`recrawl_of`, R6) | No silent "newest wins". |
| 17 | Donor identity (vPIC mismatch, VIN year) | Verified needs a consistent donor | not addressed | **A**, in the new client | 541 cars carry a vPIC mismatch. Year mislabels push donors across facelifts. |
| 18 | Which conditions count | deny-list regex | option lexicon plus fitment-row restrictions | **Allow-list classifier: any clause not on the neutral list conditions the row (§5.6)** | The real notes hold 152 distinct clauses, including "California Emissions", "From 4/97", "Fki", "(J)" and "USA VALUE PACKAGE". A's regex misses emissions; B's lexicon misses plant, emissions and production dates. |

---

## 1. What the real checkpoint shows (oem-raw@f2652c3)

| Fact | Evidence | Consequence |
|---|---|---|
| Notes on the **list page** carry the conditions. | 152 distinct clauses. The most common are `Japan Built` (195), `US Built` (192), `With Heated` (106), `Without Heated` (70), colours, `With/Without XLE`, `2007-09`, `California/Federal Emissions`, `From 4/97`, `12V 100A`. | Conditions must come from **the target vehicle's own list rows** (§5.10). A record's `list_notes` are valid only for its `seed`. |
| Notes can be narrower than the fitment table. | 85720-33161 lists Camry 2007 trims Base, Hybrid, LE, SE, XLE in its fitment table, but its 2007 Camry list note says "Japan Built, With XLE". 84820-06061: fitment includes LE and SE; note "With XLE". | "All trims in the table" is not enough. Restricting notes make the row `maybe`. |
| Plant split is the biggest splitter. | Of 136 seed (cell, category, slot) candidate sets, 80 hold 2 or more numbers. Plant appears in 49 of those 80 and is the only split in 16. On the lots, Camry and Camry Hybrid 2007-2011 total 2,594 cars: VIN starting "4" 2,108; "J" 228; no VIN 258. | Phase 1 cannot verify these cells. The Phase 2 plant condition, translated through VIN position 1, unlocks the 16 plant-only slots (gated; Q2). |
| The 2009 Camry cell shows how deep the splits go. | Side mirrors: 24 numbers (US/Japan × heated × colour). Window regulator: 12 numbers (US/Japan; motor XLE vs non-XLE). Headlights: 6 (SE / non-SE / Hybrid). Climate control: 3 (XLE / non-XLE / Hybrid). | Single-model "same number for every configuration" windows are rarer than B assumed. Breadth has to come from conditional classes (Phase 2) and cross-model sharing. |
| Toyota reman `-84` numbers are not flagged. | 28100-20020-84, 27060-20040-84 and 28100-74270-84 all have `reman:false`. | Reman detection adds a withhold-only syntax rule (§5.4). |
| `other_names` is unreliable. | 35 of 166 mirror records give a side that contradicts both `position` and `list_location` (17 Driver Side records say "Front Right"; 18 Passenger Side records say "Front Left"). Window motors carry aliases such as "Door Lock Actuator Motor". | `other_names` is never a position source. It may only remove claims. |
| The option-layout engine column is model-wide. | Alternator 27060-28320: Camry 2007-2009, "2ARFE, 2AZFE, 2GRFE" (2.4 / 2.5 / 3.5). Starter 28100-0A010 lists five engines. | Option-layout rows are never coverage and never narrow engines. They give Likely only, and only for body categories. |
| The reman-drop rule probably removes current listings (unconfirmed). | The builder's test shows the 2009 Camry alternator page lists 4 numbers, all reman (27060-0H111-84, -0P141-84, -28321-84, -31081-84). The 2007 crawl recorded only 27060-28320 (non-reman, catalog-only "other" section), which names 27060-28321-84 as its replacement. The parser drops every reman row whenever any non-reman row is on the page. | Crawler fix R5b. R1's `excluded_by: reman_dropped` will confirm it. C4 treats `reman_dropped` rows as suspects for engine categories. |
| Successors are often missing from raw. | 20 of the 39 successor numbers named in `list_replaced_by` have no record (12 of them -84 remans; also 81130-33652, 44310-06071, 27060-20240). | C5 keeps such cells open. R4 (chain following) is required. |
| The exclusion regex drops real assemblies. | Real Toyota rules exclude "Mirror Assy, Outer Rear View, W/Turn Signal Lamp", "Headlamp Unit Assy, W/Auto Leveling" and "Tube Assy, Fuel Suction W/Pump & Gage". The 2009 Camry fuel-pump candidates are all "California Emissions"; no federal unit was captured. | A's C4 (suspect variant) needs list manifests (R1). |
| Flags | 0 of 363 records carry a flag. 2 of 363 have more fitment rows than rendered rows ("View More"). | The evidence re-check (§5.3) is still required. PartsGiant records use free-text flags. |
| Option-layout share | 91 of 559 fitment rows (16%). They are mostly superseded numbers in the "other" section. | Any cell with a superseded predecessor listing it is blocked by E2 (§5.11). That cost is accepted and measured (funnel stage `chain_member_conditional`). |

Toyota is not special here. The Kia navigator crawls `korean_made` and
`us_georgia_made` catalogs separately, which is another plant split. PartsGiant
engine cells are "per-row aggregates and sometimes wrong" (builder note:
Infiniti FX45 printed as "6 Cyl 3.5L").

---

## 2. Verified: the pair predicate

Notation:
- `ns`: numbering namespace.
- `cv = (ns, cat_make, cat_model, year)`.
- `T = (feed make, feed model, year)`, optionally with a trim subset, mapped
  from one or more `cv` (§6).
- `c`: app category.
- `k`: slot (§5.8).
- `K(T,c,k)`: candidate classes.
- `cover(m,T) ∈ {yes, maybe, no}` (§5.10).
- `closed(T,c)` (§5.10). `eligible(T,c)` (§5.11).
- `sig(T,c) = sorted[(k, sorted K(T,c,k))]` over every slot that T's closed
  pages list.

**Phase 1 (symmetric). Verified(S, D, c) holds iff all of the following:**
1. `closed(S,c)` and `closed(D,c)`.
2. `eligible(S,c)` and `eligible(D,c)`. That is, every `K(·,c,k)` is one
   supersession chain, and every member has `cover = yes`.
3. `sig(S,c) == sig(D,c)`.
4. Every contributing (site, c) is `confirmed`, and the (ns, c) audit gate
   passed (§11).
5. No contradiction is open for S or D in c (§7.6).
6. In the client, the donor identity guard passes (§7.5).

*Why this is sound.* The donor carries some member of `K(D,c,k)`, its factory
number. An aftermarket or swapped part is outside any catalog claim, and the
row warning always says "match the number". Since `K(D,k) = K(S,k)` and every
member is listed unconditionally for S, whatever catalog number the donor
carries is listed by the carmaker for every configuration of S.

**Phase 2 (directional).** Instead of 3, require
`K(D,c,k) ⊆ {m ∈ K(S,c,k) : cover(m,S) = yes}` for every slot k of S, and
`slots(D) ⊇ slots(S)`. Conditions 1, 4, 5 and 6 still hold. S need not be a
chain. Example: Mopar 4801477AA → AG. A 2016 Patriot donor (AG only) verifies
for a 2014 seeker {AA, AG}, but not the reverse.

**Phase 2 (conditional).** Replace `cover = yes` with "unconditional given the
answered atoms" (§5.18). It needs a seeker answer and a donor signal for every
atom involved.

**Likely.** S and D share at least one class in at least one slot, from any
evidence including option layout, but Verified does not hold. The row warning
names the reason (§7.4).

**Hidden (Phase 3).** Both are closed and eligible, and the classes are
disjoint in every slot. The same-generation Likely donor is removed, and the
header counts it.

Ambiguity only removes claims:
- An unresolved position puts a record in every slot it could occupy.
- An uncrawled chain member leaves the closure open.
- A `maybe` member makes the cell ineligible.

No rule adds a pair by inference. That rules out suffix stripping, fuzzy
models, year-gap bridging and cross-namespace string equality.

---

## 3. Raw inputs and crawler requirements

### 3.1 Records as they exist

**SimplePart** (toyotapartsnow, jeeppartsdeal), as observed in oem-raw:
- site, category, seed{make, model, year}, segment, list_url, pn, name,
  aux_desc, product_url;
- list_section ("diagram" | "other"), list_notes[], list_location[],
  list_replaced_by, reman;
- description, other_names, position, replaces[], replaced_by[];
- fitment[{years, make, model, trims[], engines[], raw, other_columns?,
  year_spans?}];
- evidence_lines[], fitment_rows_rendered, fitment_rows_total, retrieved,
  flags?.

**PartsGiant** (`_partsgiant.py`):
- pn, description, position, replaces[], `replaced_by` (raw string or None;
  may be "(MultiSupersession)"), fitment[{years, make, model, trims, engines,
  options, raw}], evidence_lines, flags (free text), retrieved;
- list fields: list_group, list_remark, list_info (e.g. "Fitting Vehicle
  Options: Z(LY7)", "Location: Driver Side").

### 3.2 Crawler requests (interchange workstream; coordinate through `ops/interchange.md` with any builder session still editing a site module)

Without R1 and R2, nothing can be Verified, by design. Without R4, any cell
whose candidates have predecessors stays open.

- **R1 — list manifests: `raw/<site>.lists.jsonl`.** One line per list page
  fetched, written **before** the `products_seen` dedup:
  - `{kind:"list", site, seed{make, model, year}, variant, cat, list_url,
    status, retrieved, rows:[...]}`.
  - Each row: `{pn, section, main, aux, extra:[{name, desc}...] (verbatim
    allExtraInfoList / list_info), replace, url, matched: bool, excluded_by:
    "include_miss" | "global:<tok>" | "rule:<tok>" | "reman_dropped" |
    "url_pn_mismatch", product: "ok" | "seen" | "fail"}`.
  - `rows` holds **every** row of `partList` and `gpgOnlyPartList` (or the
    PartsGiant equivalents).
  - Notes are kept as the structured `extra` list, not the joined string.
    The `;`/`,` structure matters (§5.6).
  - Implementation: `SimplePart.list_rows(list_url)` and a PartsGiant
    equivalent re-read the cached fetch. No extra request.
  - As built (README "Raw files"): each line also carries `read` (true only
    for status 200, no `error`, no `rows_missing`; see C2). Records,
    manifests and their size-capped continuation parts are read through
    `rawparts.py`.
- **R2 — year manifests: `raw/<site>.years.jsonl`.**
  - `{kind:"year", site, seed, variant, year_url, status, final_url, title,
    subs:[every "<group>/<sub>" slug], trims?:[], engines?:[], variants:[all
    catalog variants offered], retrieved}`.
  - For PartsGiant, list **every** variant or trim catalog the model page
    offers. `MAX_CATALOGS = 2` means some are not read, and closure (C1)
    requires all of them.
- **R3 — completion mode.** `crawl.py --site S --complete
  groups/_report/<ns>.completion.json [--minutes 28]`.
  - Each worklist row is `{make, model, year, cats}`, using feed names for
    navigation exactly as today.
  - Progress keys are `C|make|model|year|cat`.
  - Per row it fetches the year page, the category list pages and the
    manifests, then `product()` for every matched pn not yet seen.
  - The worklist is ordered by Verified pairs gained (§10.4).
  - It replaces A's blanket year sweep: same correctness, crawl hours spent
    where cars are.
- **R4 — chain following.**
  - Fetch the product pages of `replaces` / `replaced_by` numbers only when
    the catalog itself links them (gpgOnly rows or /oem/ links on the
    product page). Never construct slugs.
  - Depth 4. Record them as normal records with `"via": "replaces:<pn>"`.
- **R5 — parser fixes**, each with a test:
  - (a) `QUALIFIER` deletes the whole qualifier phrase up to the next `,` or
    `;` before the exclusion checks.
  - (b) The reman-drop rule counts only non-reman rows in the `diagram`
    section that have no `replace` value as "a new number".
  - (c) The Toyota module marks `-84` numbers `reman: true` (basis: the
    catalog's own `replace` pairs, e.g. 27060-28320 → 27060-28321-84,
    28100-20020 → 28100-20020-84).
- **R6 — re-crawls.** A record written for a (site, cat, pn) already in raw
  carries `"recrawl_of": "<line number>"`. The curator then uses the newer
  record and drops the older one, and logs it (§5.1).
- **R7 — notes per page.** When a pn already in `products_seen` appears on
  another vehicle's list page, R1 records that page's row. Since R1 does this,
  no record change is needed. Rule: **notes for T come only from T's own
  manifest rows.**

---

## 4. Files and data model

```
scraper/oem_fitment/
  CURATION_SPEC.md        this file
  curate.py               raw evidence -> groups/<ns>.json + report (offline, deterministic)
  adapters.py             SimplePart / PartsGiant record + manifest -> Evidence objects (§5.2)
  notes.py                list-note clause classifier (§5.6), pure
  positions.py            position / slot / packaging resolution (§5.8), pure
  policy.py               NAMESPACES, CATEGORY_POLICY, CATEGORY_STATUS, NOUN, SIBLING_IGNORE,
                          CONTENT_TOKENS, thresholds, lexicons, each entry with a basis comment
  model_map.json          hand-curated catalog (ns, make, model) -> feed targets (§6)
  trim_signals.json       Phase 2 only: catalog trim -> decode signal, each with a basis
  validate.py             ONE validator: structural() + full() (§8); no network imports
  measure.py              coverage before/after: Python port of the client tier logic (§10)
  groups/<ns>.json        shipped groups (committed on main, reviewed)
  groups/_report/<ns>.json, <ns>.md, <ns>.completion.json, coverage-YYYY-MM-DD.json
  tests/fixtures/curate/<case>/...   tests/test_{notes,positions,curate,model_map,validate,oracle}.py
```

Namespaces (`policy.NAMESPACES`) go by numbering system, not make:
- toyota: Toyota, Scion, Lexus. Sites: toyotapartsnow, lexuspartsnow.
- mopar: Jeep, Dodge, Chrysler, Ram, Plymouth, Eagle, Fiat. Sites:
  jeeppartsdeal, moparpartsgiant.
- gm, ford.
- nissan: Nissan, Infiniti.
- honda: Honda, Acura.
- hmg: Hyundai, Kia, Genesis.
- subaru.

Rules:
- Each site belongs to exactly one namespace.
- Fitment rows naming a make outside the namespace are evidence only.
- Each namespace has `engine_cells_reliable`. It is `false` for every
  PartsGiant site until an audit flips it.

### 4.1 `groups/<ns>.json` (schema 1)

- Keys sorted, one class or group per line.
- No timestamps except `raw.*.retrieved`, `as_of` and the proof pointers.

```json
{
 "schema": 1, "ns": "toyota", "curate_version": "1.0", "as_of": "2026-11-05T01:23:03Z",
 "policy_sha256": "<sha256 of policy.py + notes.py + positions.py + model_map.json>",
 "raw": {"ref": "origin/oem-raw", "commit": "f2652c3...",
         "sites": {"www.toyotapartsnow.com": {"records_sha256": "...", "lists_sha256": "...", "years_sha256": "...",
                   "records": 363, "lists": 0, "years": 0, "done": false, "blocked": false}}},
 "classes": {"toyota:6980408010": {"pns": ["69804-08010"], "cat": "window-regulator", "comp": "reg",
             "reman": false, "evidence": ["www.toyotapartsnow.com:records:L201"]}},
 "groups": [
  {"id": "oem:toyota:window-regulator:3f9a1c2b7e", "cat": "window-regulator", "tier": "verified", "kind": "body",
   "sig": [["SL", [["reg", ["toyota:6980408010"]], ["motor", ["toyota:8572008020"]]]], "..."],
   "apps": [["Toyota", "Sienna", 2004, 2010]], "pn": ["69804-08010", "85720-08020", "..."],
   "note": "Toyota catalog: same numbers on every trim and engine for these years (69804-08010, ...)",
   "years": [{"t": ["Toyota", "Sienna", 2004], "cv": [["Toyota", "Sienna", 2004]],
              "closure": {"year": "www.toyotapartsnow.com:years:L12", "lists": ["...:lists:L88"], "oldest_retrieved": "..."},
              "universe": {"trims_src": "year_page", "trims": ["ce", "le", "xle", "xle limited"]}}]}],
 "vg": [{"id": "oem:toyota:alternator:91ab04c3d2", "family": "toyota-2az", "cat": "alternator",
         "spans": [["Toyota", "Camry Solara", 2004, 2006]], "pn": ["..."], "years": ["...as above..."]}],
 "likely": [{"id": "oem:toyota:side-mirrors:L:5e0c...", "cat": "side-mirrors", "tier": "likely",
             "apps": [["Toyota", "Camry", 2007, 2011], ["Toyota", "Camry Hybrid", 2007, 2011]],
             "pn": ["87910-06925"], "reason": "conditional", "note": "..."}],
 "cells": [["Toyota", "Camry", 2009, "side-mirrors", "open:option_split"],
           ["Toyota", "Sienna", 2004, "window-regulator", "sig:3f9a1c2b7e"]]
}
```

- `id` is `oem:{ns}:{cat}:{sha1(canonical_json(sig))[:10]}`, which is stable
  while the evidence is unchanged. Likely ids add the slot.
- Proof pointers are `<site>:<records|lists|years>:L<line>` into the pinned
  raw commit.
- `cells` holds every (T, c) with either its signature or its first open
  reason. measure.py and the reports read it; it is never shipped.
- `groups/_report/<ns>.json` holds:
  - the funnel (§10.3);
  - every refusal `{reason, t, cat, pn, evidence[]}`;
  - unknown note clauses with counts;
  - unmapped catalog models with feed car counts;
  - contradictions (§7.6);
  - the audit sample;
  - map proposals;
  - near-miss rows (manifest rows with category keywords but `matched:
    false`).

Raw is read without a checkout: `git show <sha>:raw/<file>`
(`--raw-ref origin/oem-raw`), or with `--raw-dir` for fixtures.

---

## 5. Curation rules (curate.py), in order

Nothing depends on dict order or wall-clock time. `--as-of` defaults to the
newest `retrieved` in the input.

### 5.1 Input acceptance
- **Torn last line.** If only the last JSONL line fails to parse, skip it and
  report `torn_tail`.
- **Corrupt line.** Any other bad line refuses the whole site file
  (`corrupt_raw`).
- **Synthetic records.** Lines with `"synthetic": true` are refused unless
  `--fixtures`.
- **Duplicates.**
  - Identical duplicates of a (site, cat, pn) collapse.
  - Differing duplicates are both kept and the record is `disputed`
    (unverified), unless R6's `recrawl_of` links them.
- **Blocked sites.** A `.blocked` site keeps its records as evidence. Being
  blocked never closes anything.

### 5.2 Adapters (adapters.py)

The adapters normalize both templates into one model:
`Record{site, ns, cat, pn, key, names{name, aux, other_names, description},
position_sources[], list_url, section, replaces[], replaced_by[], reman,
rows[FitRow], flags[], evidence_lines[], retrieved, seed, via}` and
`ListRow{...R1 fields..., notes: [[clause...] per ';' segment]}`.

Field mapping:
- **Notes.** SimplePart `list_notes` maps to notes; PartsGiant `list_remark` +
  `list_info` (minus `Location:`) map to notes.
- **`replaced_by`.** PartsGiant's raw string is split. "(MultiSupersession)"
  makes the record `chain_unknown`, which blocks.
- **Options column.** PartsGiant `options` is `other_columns` (option layout)
  unless `option_column_is_trims` is set for that site, in which case the
  values are trims. For trims, the namespace audit must still confirm before
  coverage.

### 5.3 Record verification

A record that fails is **unverified**: it counts as a candidate, never as
coverage, and it blocks.

- **Flags.** *Any* flag string makes the record unverified. This also covers
  PartsGiant's free-text flags.
- **Evidence re-check.** This is the builder's 242/242 audit, re-implemented
  independently. All of the following must hold:
  - the pn is in `evidence_lines`;
  - each fitment row's cells appear in order after "Vehicle Fitment" (or
    after "View More" when the row index is at or beyond
    `fitment_rows_rendered`);
  - `position` appears after "Position";
  - each `replaces` / `replaced_by` number appears after its label.

  Failure is `evidence_mismatch`. If more than 2% of a (site, cat)'s records
  fail, the whole (site, cat) becomes `unconfirmed` (systemic).
- **Rule drift.** Re-run the site module's `match(cat, main, aux)` on the
  stored names (no network: import only the RULES tables). A record that no
  longer matches stays a candidate and keeps its cells open (`rule_drift`).
- **Classification source.** Classify only by `name` / `aux_desc`, never by
  `description` (55111610AC is shown as "Dash Control Unit").
- **Guards:**
  - names matching `kit|set|pair` are evidence-only;
  - rows or notes mentioning RHD or "right hand drive" are evidence-only;
  - a name matching `engine assembly|long block|transmission|transaxle|catalytic|converter`
    is a **lint error** (rule 4);
  - mirrors whose text says tow, towing or trailer are projected to
    `tow-mirrors`.

### 5.4 Part-number identity and reman
- **Key.** `ns + ":" + re.sub(r"[^A-Z0-9]", "", pn.upper())`. Keys never merge
  across namespaces (`cross_ns_string_collision` is reported). The same key
  on two sites in one namespace is one class. Its rows are unioned, and any
  disagreement makes it `disputed`.
- **No suffix interpretation that grants anything.** Colour suffixes, Mopar
  revision letters and Toyota reman suffixes never merge, join or cover.
- **Withhold-only syntax.** A class is `reman` if any of these holds:
  - `reman: true`;
  - "reman" appears in any name or note;
  - the pn starts with R followed by a digit;
  - `ns == toyota` and the pn ends `-84`.

  Syntax may only *tighten* (E4). It may never loosen.

### 5.5 Fitment normalization
- **Catalog vehicle-years.** Each row yields one `cv` per year in its
  inclusive span. Multi-span cells stay separate: 85720-AE010 lists tC
  2007-2008 and 2011-2013, which says nothing about 2009-2010.
- **Layout.** `layout = "option"` if `other_columns` (or PartsGiant `options`
  that are not trims) is present; otherwise `"trim"`. Option-layout rows:
  - are never coverage;
  - never feed universes;
  - never narrow engines (their engine column is model-wide, §1);
  - may support Likely, for body categories only.
- **Trim atoms.** "Base (4WD, FWD)" becomes {("base", "4wd"),
  ("base", "fwd")}. Atoms are case-folded with whitespace collapsed. An empty
  trim cell in a trim-layout row is `trims_unknown`.
- **Engine keys.**

  | printed | key |
  |---|---|
  | "4 Cyl 2.4 L GAS" | (4, 2.4, "gas") |
  | "…FULL HYBRID…(FHEV)" | (…, "hybrid") |
  | "…PLUG-IN…(PHEV)" | (…, "phev") |
  | CNG | "cng" |
  | FLEX | "flex" |
  | "FUEL CELL EV (FCEV)" | ("?", raw) |
  | "2.4L L4" | (4, 2.4, None) |
  | anything else | ("?", raw), which fails every universe test |

- **Engine cells on PartsGiant** are used only when
  `engine_cells_reliable[ns]` is set. Otherwise every engine test on that
  namespace is `maybe`.

### 5.6 List-note classifier (notes.py), new

**Input.** For (pn, T): T's own manifest rows for that pn (R1/R7), the
`extra` entries named "Part Notes" or "Notes", and PartsGiant remark/info.

**Splitting:**
- `;` separates **segments**, which may be alternative row conditions.
- `,` outside parentheses separates **clauses**.
- Each clause is tokenized left to right into atoms. **Any leftover text makes
  the whole clause UNKNOWN.**

| class | examples (real) | restricts? | Phase 2 translatable |
|---|---|---|---|
| NEUTRAL_SPEC | `12V 100A`, `12V 1.7KW`, `1.2 KW` | no (describes the part) | n/a |
| NEUTRAL_MODEL | T's own catalog model ("Camry" on a Camry cell) | no | n/a |
| MODEL_OTHER | another catalog model ("Camry" on a Solara cell; `Prius`, `Sienna`) | yes | no |
| YEARS | `2007-09`, `1997-2001`, `2016-18` | no if T's year is inside; otherwise the row is `listed_not_fitted` | n/a |
| PLANT | `US Built`, `USA Built`, `US Built Only`, `Japan Built`, `Japan Build`, `Canada Built` | yes | plant (VIN position 1) |
| ENGINE | `2.4L`, `3.0L`, `3.5L` | yes | engine (decode liters) |
| FUEL | the model `Camry Hybrid`, the trim `Hybrid` | yes | fuel (vPIC) |
| TRANS | `Manual Transmission`, `Auto Transmission`, `A/T`, `M/T` | yes | trans (extras[3]) |
| OPTION | `With/Without Heated`, `Power With Heater`, `Without Auto Dimmer`, `Without Memory`, `With Signal Lamp`, `With/Without HID`, `High Intensity Discharge`, `Auto Level`, `Auto High Beam`, `Blind Spot`, `Auto A/C Control`, `Atc`, `11.6" Display`, `Power`, `Manual` | yes | no |
| TRIM | `With XLE`, `Without SE`, `SE`, `LE & XLE`, `CE PACKAGE…`, `Without Prime`, `With Solara` | yes | no (Q3) |
| BODY | `Coupe`, `Convertible`, `Sedan`, `Wagon` | yes | no |
| EMISSIONS | `California Emissions`, `Federal Emissions` | yes | no |
| PRODUCTION | `From 4/97`, `Thru …`, `(mm/yy-` | yes | never |
| PACKAGE / MARKET | `USA VALUE PACKAGE`, `KOREA SPEC…`, `20TH ANNIVERSARY(USA)`, `TOWING PACKAGE…` | yes | no |
| COLOUR | `White`, `Blue Ribbon`, `Jasper Pearl`, `SUPER WHITE 2`, `1D7`, `3Q3`, `040`, `Red (3P5)` | yes (colour split; §5.14) | no |
| POSITION | `Left`, `Right`, `Front`, `On Body`, `On Side Panel` | feeds §5.8 (mount axis) | n/a |
| UNKNOWN | `Fki`, `Nal`, `(L)`, `(J)`, `All`, `Control Panel`, `NO PAINT REQ.`, `OUTSIDE RR VIEW MIRROR-HEATED(EC)` | **yes** | no |

**Phase 1 rule.** Notes are clean for (pn, T) iff every clause of every
segment is NEUTRAL_SPEC, NEUTRAL_MODEL or a satisfied YEARS. Anything else
makes cover `maybe`.

**Phase 2.** Segments are read as alternatives only when every segment
classifies with no UNKNOWN clause.

**Lexicon maintenance.** Each lexicon entry carries a basis comment.
UNKNOWN clauses are counted in the report, and new entries come only by
reviewed commit. The test asserts that all 152 clauses from oem-raw@f2652c3
classify into the classes shown above.

**Qualifier phrases in names.** Names, `aux_desc` and `other_names` go
through A's qualifier detector (it only removes claims):
`(w/o|w/|with(out)?|less|exc(ept)?|excl(uding)?|for (models|vehicles) with|if equipped)\s+<phrase>`.

Objects listed in `policy.CONTENT_TOKENS[cat]` describe the assembly, not the
car, and are exempt:

| category | content tokens |
|---|---|
| alternator | regulator, pulley |
| ac-compressor | pulley, clutch, magnet |
| fuel-pump-module | filter, pump, gage, gauge, sender |
| radiator | cap |
| lamps | bulb, socket |
| side-mirrors | glass |

"With/without motor" on regulators sets the packaging (§5.8) instead.

### 5.7 Universes (per cv, pooled over categories and sites in the namespace)
- **TrimU(cv).**
  - Preferred: the year-page trim list (R2), `trims_src: "year_page"`.
  - Otherwise: the union of trim atoms over **verified trim-layout** rows
    covering cv. It is attested only with at least 5 distinct records from at
    least 3 categories.
  - Otherwise: `unattested`, and nothing can be unconditional for that cv.
- **EngineU(cv).** The union of engine keys over verified trim-layout rows.
- **Engine-sliced trims** (engine categories): TrimU_f(cv) is the trims of
  rows whose engine set is a subset of E_f(cv). It must be attested;
  otherwise the full TrimU is used, which fails safe.
- **Trim-subset targets** (§6) use only their subset's atoms.

### 5.8 Positions, slots and packaging (positions.py)

**Position sources.** `position`, each `list_location`, PartsGiant
`Location:` info, `name` / `aux_desc` tokens, POSITION note clauses, and the
`list_url` slug **for the door axis only**. `other_names` is **never** a
source (§1).

**Token grammar (A's):**

| axis | value | pattern |
|---|---|---|
| side | L | `\b(driver\|left\|lh\|l/h\|lt)\b` |
| side | R | `\b(passenger\|right\|rh\|r/h\|rt)\b` |
| side | B (one number, both sides) | `left\s*(or\|and\|/\|&)\s*right`, `lh\s*/\s*rh`, `both sides`, `either side` |
| door | F | `front-door-body`, `front-door`, `\b(front\|fr\|frt)\b` |
| door | R | `rear-door-body`, `rear-door`, `\b(rear\|rr)\b` |
| door | S | `sliding-door-body` |
| door | (none) | `door-body` / `door` give no value |

Category-specific readings:
- For mirrors, ignore "Rear" and "Outer". "Rear Outer Passenger Side" is R.
- For lamps, ignore "Front". Jeep prints "Front Driver Side" on headlamps.

**Resolution:**
- All sources must agree on every axis.
- A disagreement, or L and R in one source without a B pattern, gives
  `position_conflict`: the record goes into every slot it could occupy and
  blocks them all.
- A required axis with no value gives `position_missing`, which also blocks.
- Optional axes (io, beam, and lamp mount body/lid from POSITION notes)
  become required for a (cv, cat) as soon as any candidate there carries
  them.
- A side token on a no-axis category makes the record unverified
  (`unexpected_position`).

**Slots per category:**

| category | slots |
|---|---|
| side-mirrors, tow-mirrors, headlights, fender, door-front, door-rear | L, R |
| tail-lights | L, R (× mount when required) |
| window-regulator | FL, FR, RL, RR, SL, SR |
| window-switch | DM |
| everything else | C |

**Window switch.**
- Toyota "Master Switch" rows map to DM.
- Mopar "Switch - Window And Door Lock" maps to DM only when position resolves
  to L and door F. 4602785AD (Front Right) is out of the category.
- PartsGiant rows without a side are `position_missing`.

**Window-regulator packaging (replaces A's sub-slots).** Each member of a door
slot gets one packaging value:

| packaging | rule on the OEM name |
|---|---|
| `motor` | starts "motor" or matches `power\s+window\s+motor`, and has no "regulator" in the head phrase |
| `assy` | regulator plus `(w/\|with)\s*motor` |
| `reg` | regulator plus `sub-?assy\|(w/o\|without\|less)\s*motor` |
| `reg?` | any other regulator |

The door slot is eligible only if its candidate set is exactly one of:
- **P1:** one chain of `assy`.
- **P2:** one chain of `reg` plus one chain of `motor`.

Anything else blocks the slot:
- `reg?` present gives `packaging_unstated`;
- P1 and P2 together, or two chains of one packaging, give
  `packaging_split`.

A motor that serves several doors is placed in each door slot where T's own
manifests list it.

### 5.9 Supersession graph (per ns, cat)
- **Edges** run old → new. They come from `replaces`, `replaced_by` and the
  list row's `replace` / `list_replaced_by`.
- **Cross-category edges** are not joined; they are reported
  (`cross_category_supersession`).
- **Cycles.** A strongly connected component with more than one node makes
  every member `cyclic`, which blocks.
- **Packaging changes.** An edge whose ends resolve to different slots or
  packaging sets `chain_crosses_slot`, which blocks both ends.
- **Chains.** `comparable(a, b)` holds when a reaches b or b reaches a. A
  chain is a set whose members are pairwise comparable.
- **Supersession is never coverage.** It never makes a number cover a car
  that the number's own rows do not list.

### 5.10 Candidate sets, coverage, closure

**Candidate set.** `K(T,c,k)` is the union of:
- every class with a fitment row mapping to T (any layout, any verification
  state) whose slot is k or unknown;
- every class matched for slot k on T's own list pages;
- every manifest row on T's pages flagged as a suspect variant (C4).

**`cover(m, T)`** is:
- `no` when no row of m maps to T and m is not on T's pages.
- `yes` only when **all** of these hold:
  - m's record is verified;
  - a trim-layout row covers T, and its trims include all of TrimU(T)
    (TrimU_f for engine categories);
  - its engines include all of EngineU(T), or all of E_f(T) for engine
    categories;
  - m appears on T's own list pages;
  - T's own-page notes for m are clean (§5.6);
  - no qualifier phrase appears in names, `aux_desc` or `other_names`;
  - m is not `disputed` or `rule_drift`;
  - TrimU(T) is attested.
- `maybe` in every other case. Reasons include `listed_not_fitted`,
  `fitted_not_listed`, `conditional_notes:<class>`, `conditional_trims`,
  `conditional_engines` and `option_layout`.

**Closure.** T is closed for c iff C1–C9 hold for every cv mapped to T. With
a `merge` mapping, every merged cv must close.

- **C1. Year manifest.** HTTP 200, no redirect, and the title parses to the
  cv. At least one matched pn's fitment lists the cv. For PartsGiant, every
  offered variant or trim catalog has a year manifest.
- **C2. List pages.**
  - Every `CAT_PAGES[c]` sub on those pages has a list manifest line that
    was **read**: `read: true`, which crawl.py sets only for status 200 with
    no `error` and no `rows_missing`. A line with `error` (list-fail, also
    on a status-200 error page) or without `read: true` never counts as read,
    whatever its status: the page is unread and the cell stays open.
  - No other sub matches `policy.NOUN[c]` without having been read
    (`unread_sibling_page`), unless a `SIBLING_IGNORE` entry with a basis
    exempts it.
- **C3. Products.** Every matched row has a verified product record.
- **C4. No suspect variant.** No excluded manifest row has a head phrase
  (the name with every qualifier phrase deleted up to the next comma) that
  matches the include rule but not the exclusion rule. `reman_dropped` rows
  count as suspects for engine categories until R5b lands.
- **C5. Chain completeness.**
  - Every ancestor and descendant (to depth 4) of every member has a
    verified record (`uncrawled_chain_member` otherwise).
  - Every descendant lists T (`chain_fitment_inconsistent` otherwise).
- **C6. Freshness.** Every record and manifest used is no more than 120 days
  older than `--as-of`.
- **C7.** TrimU is attested.
- **C8.** T's mapping validates (§6).
- **C9.** The site is not blocked mid-closure. A partially read year (a page
  fetch failed) never closes.

**Sister makes.** Makes seen only in another catalog's fitment (for example
Dodge Caliber on Jeep 4801477AG) stay open until their own catalog pages are
read. They may still appear in Likely groups.

### 5.11 Eligibility (T, c)

T is closed, and for every slot T's closed pages list:
- **E1.** K is non-empty and is one chain. For window-regulator, it is one of
  P1 or P2 (§5.8).
- **E2.** `cover = yes` for **every** member.
- **E3.** No member is `cyclic`, unverified, `chain_unknown` or in an unknown
  slot.
- **E4.** Some non-reman member is an ancestor of every reman member
  (`reman_only` otherwise).
- **E5.** `CATEGORY_STATUS[site][c] == "confirmed"` for every contributing
  site.
- **E6.** No class lists more than 12 distinct feed models
  (`universal_part_suspect`), and the OEM name still matches the include
  rule.
- **E7.** For engine categories, `engine_cells_reliable[ns]` is set.
- **E8.** The kind is `body`, `engine` or (Phase 3) `oem`. combo and exact
  categories never get OEM groups.

`sig(T,c)` is the sorted list of `(slot, [(packaging, sorted keys)])`.

### 5.12 Category status (policy.CATEGORY_STATUS)

The audit records live in `audits.json` (loaded as `policy.CATEGORY_STATUS`), never in
`policy.py`: `policy_sha256` hashes `policy.py`, so a record kept there would change the hash
it must match (review, 2026-11-05). `audits.json` is not hashed; each record names the
`policy_sha256` and raw commit it audited (V7), so any policy edit still needs a re-audit.

- Every (site, category) starts `unconfirmed`.
- It flips to `confirmed` only with an audit record `{date, auditor_session,
  sample_n, errors: 0}` (§11).
- `jeeppartsdeal/window-switch` and `jeeppartsdeal/gauge-cluster` stay
  unconfirmed until audited. Their CAT_PAGES include passenger switches and
  `cluster-switches`.

### 5.13 Engine attachment (alternator, starter, ignition-coils), output `vg`

E_f(cv) is the engine keys in EngineU(cv) whose liters are within 0.05 of
one of the family's liters and whose cylinder count equals the family's,
regardless of fuel.

A span (T, year) attaches to family f for category c only if:
- (a) an app of f matches it (`_app_matches`). A miss is reported as
  `family_gap`; family apps are never extended.
- (b) exactly one family matches.
- (c) **family uniformity:** every engine key in E_f(cv) gives the same
  signature. That includes fuel twins: 2.4 GAS and 2.4 FHEV both decode as
  "2.4L 4-cyl", and the hybrid has no belt alternator. If any key differs,
  the reason is `family_nonuniform`.
- (d) the part's `years` window contains the year.
- (e) the app is not `ambig`.
- (f) T is eligible.

Spans with equal (f, c, sig) form one OEM vg group. OEM data never edits
`ENGINE_FAMILIES`, `_ALT_VERIFIED` or `_STR_VERIFIED`.

### 5.14 Colour variants: off in Phase 1

A `color_variant` identity edge needs all of these:
- a documented namespace scheme (toyota only);
- each member's own notes state a colour or paint code;
- every other field is identical (names, slot, packaging, fitment rows, and
  notes once the colour clause is removed);
- `CATEGORY_POLICY[c].color_collapse` is set and that category's audit has
  passed.

Candidate categories are mirrors, bumper covers and grille. Lamps, clusters,
engine and oem kinds are never collapsed.

On the real 2009 Camry cell, collapse alone would verify nothing: plant and
heated splits remain. It is deferred.

### 5.15 Groups and spans

- Group eligible (T, c) by (ns, c, sig).
- Per feed (make, model), emit the maximal runs of consecutive eligible
  years. Never bridge an open year or one with a different signature.
- Single-model groups are valid.
- Cross-generation groups (one number listed across a redesign) are valid
  because the signature is proven. They are listed in the report for the
  audit.
- A group needs at least 2 feed vehicle-years.

### 5.16 Likely groups (body categories only)

- **Which classes.** Any class with cover `yes` or `maybe` for at least 2
  distinct feed models emits `{tier: "likely", apps, pn, reason, note}`.
- **Skips and refusals.** Single-model classes are skipped, because the
  same-model generation loop already covers them. Classes over the 12-model
  cap are refused.
- **Note template:** "`<Brand>` catalog lists #`<pn>` for both — `<reason
  text>`; verify the number on the part". Reason texts:
  - "plant-specific (US / Japan built)";
  - "trim-limited: `<trims>`";
  - "option: `<option>`";
  - "older catalog-only number";
  - "fits some configurations".

### 5.17 Determinism

- Inputs are sorted by (site, file, line).
- Output is written with `sort_keys`.
- Two runs give byte-identical output, and shuffled input lines give
  identical output.

### 5.18 Phase 2 conditional atoms (computed in Phase 1, shipped in Phase 2)

For each (pn, T), when every restricting clause and fitment restriction is
translatable, `cond(pn, T)` is a DNF over these atoms:

| atom | seeker answer | donor signal |
|---|---|---|
| plant ∈ {US, CA, MX, JP, KR} | first VIN character (chip) | VIN[0]: 1/4/5 → US, 2 → CA, 3 → MX, J → JP, K/L → KR; no VIN → unknown |
| fuel ∈ {gas, hybrid} | chip | vPIC trim exactly "Gas" → gas; "Hybrid" in the model or as a whole word in vPIC trim/series → hybrid; else unknown |
| engine (liters, cyl) | existing engine chip | decode extras[2] |
| drive | chip | `vpicDriveType` |

Rules:
- Every translation entry carries a basis line in policy.py.
- **Plant translation ships only after owner question Q2 and its audit.**
- A Phase 2 pair is Verified iff Phase 1 conditions 1, 4, 5 and 6 hold, and
  for each slot the candidates whose conditions the answers satisfy form an
  eligible set in both cars (E1–E3 with "unconditional given answers") with
  equal (or, in directional mode, subset) membership.
- An unanswered or unknown atom gives Likely.

---

## 6. Model map (`model_map.json`): catalog (ns, make, model) → feed targets

```json
{"schema": 1, "entries": [
 {"ns": "toyota", "cat_make": "Toyota", "cat_model": "Camry",
  "targets": [{"make": "Toyota", "model": "Camry", "trims": "*"},
              {"make": "Toyota", "model": "Camry Hybrid", "trims": ["hybrid*"], "years": [2007, 2017]}],
  "basis": "catalog files the hybrid under Camry (trim Hybrid); 186 feed 'Camry' 2007-11 decode vPIC trim Hybrid (2026-11-05), so 'Camry' keeps the full trim universe"},
 {"ns": "toyota", "cat_make": "Toyota", "cat_model": "Solara",
  "targets": [{"make": "Toyota", "model": "Camry Solara", "trims": "*"}], "basis": "normalize_model canon"},
 {"ns": "mopar", "cat_make": "Dodge", "cat_model": "Ram 1500",
  "targets": [{"make": "Dodge", "model": "Ram Pickup", "trims": "*", "ambig": "feed 'Ram Pickup' does not say 1500/2500/3500"}]}
],
 "exclude": {"toyota|Toyota|Camry Wagon": "pre-1997 body outside crawled years"}}
```

Semantics:
- `trims: "*"`: the feed model may hold any catalog trim, so the full TrimU
  applies.
- A trim-subset target uses only those atoms.
- `merge: true` is required when two catalog models feed one target in one
  year. Both must close.
- `ambig` targets are Likely-only.
- No `*` prefixes, ever.
- Proposals: `curate.py --propose-map` writes `_report/<ns>.map-proposals.json`
  from `normalize_make` / `normalize_model` plus squash-prefix neighbours.
  Humans merge the decisions.

Validation (test_model_map.py reads `docs/data/inventory_live.json` and the
vPIC block; curate.py refuses to run on any error):

- **M1. Canonical (error).** `normalize_make(make) == make` and
  `normalize_model(model, make) == model`.
- **M2. Present (warn).** At least one car of the target exists in some year.
- **M3. Squash uniqueness (error).** No other same-make feed model squashes
  (`_squash_model`) to the same key.
- **M4. Match self-test (error).** A synthetic car (lo, make, model) matches
  its emitted app under `_app_matches`. It matches no other target of a
  different feed model; for example "Camry" must not catch "Camry Hybrid".
- **M5. No silent drops (error).** Every inventory (make, model) under the
  namespace makes whose squash equals or starts with a mapped catalog squash
  is either a target or in `exclude` with a reason.
- **M6. VIN agreement (error).**
  - At least 98% of cached vPIC decodes map back to the same catalog model.
  - For trim-subset targets, the VIN-derived trim must agree: at most 1% of
    feed "Camry Hybrid" may decode as "Gas".
- **M7. Make guard (error).** Each target make belongs to the namespace.
- **M8. Many-to-one (error).** Many-to-one without `merge: true` is an error.
- **M9. Year sanity (report).** Feed cars outside the catalog years are
  reported. They feed the completion worklist.
- **M10. Coverage (report).** Mapped share of namespace cars, and unmapped
  catalog models with car counts.

---

## 7. Integration

### 7.1 Principle

Old native clients read the live `interchange.json` with their bundled
logic.

- **OEM claims are added only under new keys**, which only the new client
  reads.
- **Existing keys (`categories`, `platformGroups`, `engineFamilies`) may only
  lose claims:**
  - tier "verified" can become "likely";
  - a vg group can be removed;
  - an `ambig` string can be added.

V9 enforces this by building with and without the groups directory and
diffing the old keys.

### 7.2 Phase 0: claim removals and guards (independent of OEM data; do first)

- **P0.1** `docs/app.js` `pfRunSearch()` platform loop: `const gTier =
  g.tier === 'verified' ? 'verified' : 'likely';` (currently fails open).
- **P0.2** Escape at render:
  `groupNotes.map(n => `<div class="pf-caveat">${escapeHtml(n)}</div>`)`.
  Today the header notes are unescaped while row warnings are escaped. All 4
  current pushes are plain text (seeker ambig, the family "Donors narrowed"
  line, the "Showing every same-generation donor" line, `${g.label}:
  ${g.note}`), so nothing intended is lost.
- **P0.3** Same loop: append `escapeHtml(pfCat.rowWarn)` to platform-group
  row warnings. The paint and cutout warning is missing on Verified platform
  rows today.
- **P0.4** New `pfDonorIdentity(v)` → `{ok, warn}`. It applies to every row
  that would be Verified (platform, vg and OEM paths):
  - `v.vpicMismatch` set → Likely, with "the yard's listing doesn't match the
    VIN — verify";
  - a 17-character VIN whose model-year character
    (`pfVinModelYear(vin, v.year)`, resolving the 30-year cycle toward
    `v.year`) differs from `v.year` → Likely;
  - OEM rows only: no valid VIN → Likely, with "no VIN to confirm the model
    year".
- **P0.5** `scraper/junkyard_scraper.py` `ENGINE_FAMILIES` hybrid fix (from
  B; hand data, its own commit). Split toyota-2az
  `("Toyota","Camry",2002,2009)` into 2002-2006 and 2007-2009, with
  `{"ambig": "2007-09 Camry Hybrids also decode as 2.4L 4-cyl and have no
  belt alternator or starter — check for HYBRID badges"}`. Repeat for each
  app that an extended `_audit_verified_fits.py` (vPIC-hybrid column) lists:
  - toyota-2ar Camry;
  - honda-j30 Accord;
  - ford-mzr and ford-fusion-cd4;
  - toyota-2gr Highlander;
  - hk-theta Sonata;
  - gm-ecotec24.

  This is a claim removal, so it reaches old clients at once. Measured on
  2026-11-05: 186 feed "Camry" 2007-2011 cars decode vPIC trim Hybrid.
- **P0.6** Bump `docs/sw.js` `CACHE` (`jh-v141` → next).

P0.1–P0.4 reach web users on deploy and native users only after the owner
says "ship" (rule 1). P0.5 reaches every client as data.

### 7.3 Phase 1: payload

In `scraper/junkyard_scraper.py`:

- **New `_load_oem_layer() -> dict`.**
  - It reads `scraper/oem_fitment/groups/*.json`; `_report/` is skipped.
  - It loads `scraper/oem_fitment/validate.py` through
    `importlib.util.spec_from_file_location`. There is no package import and
    no `fetch` import: validate.py must not import network code. It calls
    `validate.structural(doc, ctx)`, where `ctx` carries
    `INTERCHANGE_PART_CATEGORIES`, `ENGINE_FAMILIES`, `normalize_make`,
    `normalize_model`, `_squash_model` and `_app_matches`.
  - It drops groups whose `years[].closure.oldest_retrieved` is more than
    120 days older than now (build-time expiry). Likely groups carry their
    own `oldest_retrieved` and expire the same way; when the file's `as_of`
    is over 120 days old every group of every tier goes. `oemStatus` counts
    the expired groups.
  - V11 is measured on the payload exactly as written (every `oemStatus`
    edit made, trailing newline included); an `oemVg` family dropped for
    size is reported under the namespaces that shipped it.
  - A failing namespace file is dropped, never raised. The loader prints
    `[interchange] oem <ns> dropped: <reason>` to stderr and records
    `oemStatus[ns]`.
- **`build_interchange_payload()` adds these keys:**
  - `"oemGroups"`: verified body groups plus Likely groups. Each is
    `{id, ns, cat, tier, label: "<Brand> catalog", note, apps, pn, src:
    "oem"}`.
  - `"oemVg"`: `{family_id: {cat: [[[make, model, lo, hi], ...], ...]}}`.
  - `"oemStatus"`: `{ns: "ok <commit8> <n> groups" | "dropped: <reason>"}`.

  It also calls the new `_apply_oem_contradictions(payload, oem)` (§7.6).
  `schemaVersion` stays 2; old clients ignore unknown keys.
- **`write_interchange_payload()`** is unchanged. The byte budget check
  lives in validate.py (V11).
- **Ops alert.** `backend/src/ops_monitor.js` should alert on any `oemStatus`
  value starting with "dropped". That file belongs to the backend ops
  workstream; file the request there.

### 7.4 Phase 1: client (new app.js; web on deploy, native after "ship")

- **Body branch.** In `pfRunSearch()`, iterate
  `[...interchangeData.platformGroups, ...(interchangeData.oemGroups || [])]`
  with the P0 rules.
  - For OEM verified rows, use `pfDonorIdentity()`.
  - OEM Likely groups render with the collapsed caveat: one header line per
    search, "Catalog part numbers shared on some configurations — verify the
    number". Each row's warning keeps its group note.
- **Engine branch.** Replace the `part.vg` gate with
  `const vgs = [...(part.vg || []), ...(((interchangeData.oemVg || {})[fam.id] || {})[pfCat.id] || [])];`
  and loop `vgs`. Apply `pfDonorIdentity()` when the tier would be Verified.
- **Rows** show "`<Brand>` #`<pn>`" from `g.pn` (first two numbers,
  "+N more").
- **Verified tooltip on OEM rows:** "Verified = the carmaker's parts catalog
  lists the same part number for both cars, for every trim and engine of
  these years. It is not a physical inspection; match the number at the
  yard."
- **Tests:** backend e2e (§9). Bump `docs/sw.js` CACHE again.

### 7.5 Phase 2 (only after measure.py shows a gain and the audits pass)

- **Directional index.**
  - `oemIndex[cat] = [[make, model, lo, hi, sigId]]`, with
    `oemSigs[sigId] = [[slot, [[packaging, [classIds]]]]]`.
  - A pure `pfOemTier(seekerSig, donorSig, answers, donorSignals)` sits
    between the markers `/* OEM-TIER BEGIN */` and `/* OEM-TIER END */`.
  - A Python mirror lives in measure.py, and a node parity test compares
    them (§9).
- **Condition chips** (plant, fuel), shown only when the seeker's cell is
  conditional. "Not sure" gives Likely.

### 7.6 Contradictions with hand-curated data (`_apply_oem_contradictions`)

For every hand `platformGroups` verified group and every hand vg group G:

- **`oem_disjoint`.** Two members are both OEM-closed and eligible for that
  category, with disjoint classes in every slot.
- **`oem_split`.** A member is OEM-closed but not eligible because of
  `option_split` or `conditional_*`.

`conditional_*` here means a real condition: a class in
`policy.SPLIT_CONDITIONS` (plant, trim, option, engine, emissions,
production, fuel, trans, body, package, colour, model_other, qualifier).
Evidence gaps (notes_not_own_page, option_layout, fitted_not_listed,
listed_not_fitted, trim/engine universes unattested or unparsed, engine
cells unaudited, a blank trim cell, an UNKNOWN note clause) never trigger.
A hand vg group reads `engine_cells` ([make, model, year, cat, family,
state]): the cell narrowed to its own engine family (§5.13: E_f, TrimU_f,
and a candidate whose every trim-layout row prints only engines outside
the family is not a candidate). Two engines of the family each printing
their own numbers is `conditional:engine` (a split); an engine of the
family with no row is `family_nonuniform` (a gap). A file without `sigs`,
`cells` and `engine_cells`, or whose cells do not hold every Verified year
as its own signature, is refused (V1).

Either trigger does three things:
1. It demotes G for the involved cells in the payload. A platform group's
   tier becomes "likely" and its note gains " — OEM catalog numbers differ
   within this group; verify the part number". A vg group is removed.
2. It withholds OEM Verified groups touching those cells: a body group
   becomes Likely and takes the Likely note template (§5.16), an OEM vg
   group is removed (vg has no Likely tier). V5 is re-run on what ships.
3. It writes a contradiction entry to `_report` and to `oemStatus`.

Hand data is never edited automatically. Separately, the A-listed suspect
hand groups go to the PLATFORM_FAMILIES curator (interchange hub) for
evidence review:
- toyota-22re#2 and #3, which span the 1989/90 redesign;
- legacy-outback#0, a GT-only housing;
- vw-mk7#1;
- escape-cd2#0;
- titan-armada#0;
- ford-superduty#1;
- gmt800-truck#1;
- gmt900-suv#0;
- lambda#0.

### 7.7 Phase 3

- **New categories** (ac-compressor, fuel-pump-module, throttle-body,
  power-steering-pump, radiator).
  - They go into `INTERCHANGE_PART_CATEGORIES` with `kind: "oem"` and
    `clientMin: 3`. `build_interchange_payload()` routes `clientMin >= 3` to
    `payload["categoriesV3"]`, never to `categories`.
  - Donors come only from OEM groups.
  - Vehicle-level engine uniformity is required, because there is no engine
    chip.
  - The empty state is honest.
  - B's label, token and priceToken table applies, with B's test D: no token
    may match clutch, hose, line, support, cap, fan, bottle, shroud, mech or
    electric-steering rows.
  - No UNOBTANIUM_DB rows are added.
- **Negative evidence ("hidden").** It applies only when both cars are closed
  and eligible with disjoint classes in every slot. The header counts the
  hidden donors.

---

## 8. Validator (validate.py)

The validator runs in curate.py (no write on failure), in tests (strict) and
in `_load_oem_layer` (structural; drop on failure).

**Structural checks:**
- **V1. Schema.** Tier is exactly "verified" or "likely". `src == "oem"`.
  Kind routing: body groups → `oemGroups`, engine → `oemVg` with an existing
  family and part, oem kind → Phase 3 only.
- **V2. Apps.**
  - Exactly 4 elements, exact spellings, no `*`.
  - The make belongs to the namespace.
  - `1950 <= lo <= hi <= current year + 1`.
  - The target is in the validated model_map.
- **V3. Partition.**
  - No feed (make, model, year) appears in two OEM verified groups of one
    category.
  - No year appears in two OEM vg groups of one (family, category).
- **V4. Proof.**
  - Each verified group has at least 2 vehicle-years.
  - Every app year has closure pointers, `trims_src`, and
    `oldest_retrieved` within 120 days of `as_of`.
- **V5. Notes.**
  - Notes match the template regex, and are at most 160 characters.
  - Charset is `[A-Za-z0-9 #.,;:()/'+–—-]` (no `<`, `>`, `&` or `"`).
  - Verified notes name at least one pn.
  - "fits all", "guaranteed", "always" and "100%" are banned.
- **V6. Classes.**
  - At most 12 feed models per class.
  - Keys share the group's namespace.
  - No class appears in two slots.
- **V7. Gates.** Every contributing (site, cat) is confirmed, and an audit
  record matches `policy_sha256` and the raw commit.
- **V8. Determinism.** Ids recompute, lists are sorted, and `policy_sha256`
  matches the tree.
  The payload loader enforces V8 and V2 (model-map targets, no Verified app on an
  `ambig` target) too, so a committed file drops its namespace once the policy or the
  model map changes, until it is re-curated.
- **V9. Old-key immutability.** Built with and without `groups/`, the old
  keys differ only by demotions (verified → likely, removed vg groups, added
  ambig).
- **V10. Rule 4 and kinds.** No class name matches the rule-4 pattern. There
  are no OEM groups for combo or exact categories, and no kind oem outside
  `categoriesV3`.
- **V11. Size.** `interchange.json` stays at most 1.3 MB raw (today about
  250 KB). Over budget, Likely groups are dropped first, lowest value
  (cars × (cars − 1)) first, then Verified groups. Each drop is reported.

**Full checks (with raw):**
- **V12. Reproducible.** Recomputing from the pinned raw gives byte-identical
  output.
- **V13. Oracle soundness.** A deliberately naive implementation evaluates
  §2 over every pair of feed vehicle-years. The shipped pairs must be a
  subset of the oracle's pairs, and the ratio is reported.
- **V14. Churn.** Verified pairs growing more than 30%, or more than 200 new
  groups, against the committed file needs `--accept-churn <audit-file>`.
- **V15.** The contradiction and refusal reports are present.
- **V16. Audit gate.** See §11.

**Withhold, not raise, at build time:**
- contradictions (§7.6);
- record evidence failures above 2% in a (site, cat);
- missing audit records.

The affected (ns, cat) ships Likely only.

---

## 9. Tests

All tests are offline and run as `python3 scraper/oem_fitment/tests/test_x.py`.
Skips print their reason (rule 8).

**Fixtures:**
- `tests/fixtures/curate/real/toyota_f2652c3.jsonl` holds **real lines**
  copied from oem-raw@f2652c3. Since no manifests exist yet, list and year
  manifests are fixtures with `"synthetic": true` that follow R1/R2 exactly.
- Builder-asserted Jeep values come from `tests/test_jeeppartsdeal.py`:
  - 4801477AA → AG;
  - Patriot 2014 alternators 4801323AD, 4801323AK, 4801477AA, 4801477AG;
  - 5303843AE "Front Driver Side", which replaces 4 numbers;
  - 56041207AE, with multi-span rows;
  - 4602785AD, Front Right.

**test_notes.py:**
- Every one of the 152 real clauses classifies as in §5.6. The expected-class
  table is committed with the test.
- Safety invariant: no clause outside NEUTRAL_SPEC, NEUTRAL_MODEL and
  satisfied YEARS is ever NEUTRAL. Classifying among the restricting classes
  only affects Phase 2 translatability and reporting.
- Unknown text inside a known clause ("US Built Fki") is UNKNOWN.
- `;` segments are parsed.
- "SUPER WHITE 2,040" classifies as COLOUR and does not crash.

**test_positions.py:**
- The token table, including mirror "Rear Outer Driver Side" → L.
- Toyota "Driver Side" with front-door-body → FL; with rear-door-body → RL.
- **87940 records with `other_names` "Door Mirror, Front Right" still resolve
  to L.**
- A source conflict blocks both slots.
- Packaging P1/P2 cases, `packaging_unstated`, `packaging_split`.

**test_curate.py** (each case asserts the groups and the exact open reason):

| # | case (R = real lines) | expected |
|---|---|---|
| 1 | R Camry 2009 RH mirror: 87910-06925 (US, without heated), -06926 (US, heated), 87910-33670-* (Japan, per colour) | `option_split`. Likely groups only, plant/option reasons. |
| 2 | R Camry 1999 rear doors: 69804-AA010 "Power", 69840-AA040 "Manual", motor 85720-AA030, **with TrimU forced to {CE, LE, XLE}** | `packaging_unstated` / `conditional_notes:option`. Never Verified. This is the regression for conflict #2. |
| 3 | R tail lamp 81560-06240 "US Built, 2007-09", trims without Hybrid | `maybe` (plant, conditional_trims). The Phase 2 cond is fuel=gas ∧ plant=US. A J-VIN donor is never Verified. |
| 4 | R 85720-33161: fitment trims Base, Hybrid, LE, SE, XLE; note "Japan Built, With XLE" | notes override the table: `maybe`. |
| 5 | R starter 28100-20020-84 (`reman:false` in raw), with its ancestor 28100-20020 (option layout) | classed reman by suffix. The ancestor has cover `maybe`, so E2 blocks. With the ancestor record removed: `uncrawled_chain_member`. With the ancestor removed from the graph entirely: `reman_only` (E4). |
| 6 | R alternator 27060-28320 (option layout, engines model-wide) | never coverage, no vg, no engine narrowing. Body-only Likely rule: none. |
| 7 | R 87910-33670-B2, which replaces -33660-B2 and -B0, with both predecessors (fixture records) listing Camry 2007 | `option_split` (consolidation). |
| 8 | R Sienna 2004 sliding-door 69804-08010 + 85720-08020, plus synthetic closed manifests for every door, all P2, clean notes | **one Verified group** (positive control). Removing any manifest makes it open (`unread_sibling_page`). |
| 9 | Notes from a different seed page only (R 85710-AE010 on Sienna 2004) | `maybe` (`notes_not_own_page`). |
| 10 | Excluded manifest row "Mirror Assy, Outer Rear View, W/Turn Signal Lamp" | `suspect_variant` (C4). |
| 11 | Mopar AA→AG (AA option layout) plus 4801323AD/AK on Patriot 2014 | Patriot 2014 is not a chain (`option_split`) and AA is cover `maybe`, so Phase 1 is blocked. Phase 2 directional: a 2016 donor (K = {AG}) verifies for a 2014 seeker iff `cover(AG, 2014) = yes`. A 2014 donor never verifies for a 2016 seeker. |
| 12 | Mopar sister make (Caliber on 4801477AG) | not closed: absent from Verified, present in Likely. |
| 13 | Cross-namespace identical string | no merge; `cross_ns_string_collision`. |
| 14 | R 85720-AE010 tC spans 2007-2008 / 2011-2013 | 2009-10 not covered; no span bridges an open year. |
| 15 | Any flag; evidence mismatch; more than 2% systemic failures | unverified; (site, cat) unconfirmed. |
| 16 | Differing duplicates, with and without `recrawl_of` | disputed / resolved. |
| 17 | Torn tail; corrupt middle line; synthetic line without `--fixtures` | skipped / refused / refused. |
| 18 | `--as-of` set 121 days later | `stale`. |
| 19 | Engine attachment: 2AZ family-uniform year; a year whose EngineU has 2.4 FHEV; a span outside the family apps; a PartsGiant namespace | attach / `family_nonuniform` / `family_gap` / E7. |
| 20 | Legacy contradiction fixture | demoted and withheld (§7.6). |
| 21 | Determinism: two runs, shuffled input | byte-identical. |
| 22 | Rule-4 name "Transmission Assy" | lint error. |
| 23 | Jeep 4602785AD (Front Right) | out of window-switch. DM is present but unconfirmed, so nothing is Verified. |

**test_model_map.py:** M1–M10 against real `docs/data`. Skips with a printed
reason when the data is absent.

**test_validate.py:** one mutation per V-check must be refused:
- tier "verfied";
- an app with `*`;
- an overlap;
- a missing proof;
- a note containing `<b>`;
- an unconfirmed category;
- an OEM entry injected into `platformGroups` (V9);
- an oversize payload.

**test_oracle.py** checks properties over 200 seeded random catalogs:
- soundness, as in V13;
- removing any manifest, record or manifest row never adds a Verified pair;
- adding a candidate that is not in an existing chain never adds one;
- adding a restricting note clause never adds one.

**`scraper/test_interchange.py` additions** (fixture `OEM_GROUPS_DIR`):
- `oemGroups` and `oemVg` are present;
- the old keys are byte-identical to a build without OEM, apart from
  demotions;
- `categories` ids are unchanged;
- a failing namespace file is dropped and recorded in `oemStatus`, not
  raised;
- `interchange_tier is symmetric` still passes;
- every existing assertion passes.

**`backend/test/part_finder_e2e.py` additions:**
- an OEM fixture seeker shows Verified only inside its group;
- a donor with `vpicMismatch` shows Likely;
- a group with tier "bogus" renders Likely;
- a note with `<i>` renders as text;
- a platform-group Verified row carries `rowWarn`.

**Phase 2 parity:** node (`/opt/node22/bin/node`) evaluates the
`OEM-TIER` block on 200 fixture pairs and must equal measure.py. If node is
absent, the test prints SKIP and the skip is reported.

---

## 10. Metrics (measure.py)

### 10.1 Method

- measure.py ports `pfAppMatches`, the platform/OEM group loop, the vg path
  with `pfEngineVerdict` over `vehicle_extras.json`, and `pfDonorIdentity`.
  A parity check runs the e2e on 3 seekers and compares counts.
- Every lot car stands in as a seeker for its own (make, model, year), and
  for its decoded engine family on engine kinds.
- Inputs: before = `git show HEAD:docs/data/interchange.json`; after = the
  build with `groups/`. Two client views: old (no P0 guards, no new keys)
  and new.

### 10.2 Per category

- **M-car:** share of cars with at least one Verified donor, nationwide.
- **M-local:** the same within 100 mi of the car's own yard.
- **M-pairs:** Verified ordered pairs, divided by Verified plus Likely
  pairs.
- **Flip lists**, with 50 random pairs of each sent to the audit:
  - Likely → Verified;
  - Verified → Likely (must be only P0.4, P0.5 and §7.6 demotions);
  - new cross-model Likely pairs.
- **Lever attribution:** single-model, cross-model, cross-make,
  directional, conditional (plant / fuel).
- **Blocked-by:** counts for each open and refusal reason.

### 10.3 OEM funnel

Cars per (ns, cat), stage by stage:
1. unmapped;
2. no records;
3. not closed (`no_list_manifest`, `unread_sibling_page`,
   `suspect_variant`, `uncrawled_chain_member`, `stale`, `unattested`);
4. `option_split` / `packaging_*`;
5. conditional (by class: plant, trim, option, engine, emissions,
   production, unknown);
6. `chain_member_conditional`;
7. `reman_only`;
8. eligible;
9. in a group with at least 2 cars.

The report also gives a "hypothetical if every year closed" count, labelled
and never shipped, to rank crawler work.

### 10.4 Completion worklist

For every open cell, record the Verified pairs that would flip if it closed
with its current candidate state. Write them, sorted by gain, to
`groups/_report/<ns>.completion.json`, which is R3's input.

### 10.5 Baselines

**Real checkpoint (oem-raw@f2652c3), measured 2026-11-05:**
- 136 seed (cell, category, slot) candidate sets.
- 80 (59%) hold 2 or more numbers. Plant is involved in 49, and is the only
  split in 16.
- 11 are single and fitment-unconditional; 9 of those also have clean
  own-page notes.
- 0 are closed, because there are no manifests.

**Phase 1 Verified OEM groups from this checkpoint: 0.** That is the
intended fail-closed result.

**Feed (333,449 cars, 2026-11-04).** Cars with at least one Verified donor
nationwide, as A measured with engine verdicts:

| category | cars |
|---|---|
| alternator | 138,959 (41.7%) |
| starter | 42,640 (12.8%) |
| third-row-seat | 11,670 (3.5%) |
| headlights | 5,036 |
| liftgate | 5,009 |
| side-mirrors | 3,355 |
| tailgate | 2,642 |
| tow-mirrors | 2,048 |
| climate-control | 147 |
| gauge-cluster | 147 |
| grille | 52 |
| window-regulator, window-switch, tail-lights, doors, fender, hood, bumpers, trunk-lid | 0 |

B's higher engine figures (alternator 158,368, starter 52,433) ignore the
seeker's engine choice. measure.py recomputes all of these with one
definition before any comparison.

**Ceiling.** A same-model, same-generation donor exists for 84.5% of cars.
In-scope namespaces: Toyota/Scion/Lexus 26,175 cars; Mopar makes about
43.6k (A counted 43,574, B 43,591).

Results go to `groups/_report/coverage-YYYY-MM-DD.json` and a table in
`ops/interchange.md`.

---

## 11. Gates and rollout

1. **P0** (§7.2). The data fix P0.5 lands with its test. The app guards
   deploy to web; native waits for the owner's "ship".
2. **Crawler.** R1, R2, R5 and R6 first, then R4 and R3. Re-run the trial
   seeds and confirm manifests reproduce the records (same pns, same matched
   set).
3. **Code.** notes.py, positions.py, adapters.py, curate.py, validate.py,
   measure.py and the tests, on fixtures and then on the real oem-raw:
   Likely groups plus the funnel. Commit messages follow
   `interchange: <ns> groups from oem-raw@<sha8>`.
4. **Audit gate (V16).** This is the first ship of any (site, category) and
   every churn-accepted build.
   - Sample 30 random eligible closures and 30 random Verified pairs,
     stratified toward cross-model, cross-generation and single-model
     windows.
   - **A session that did not write curate.py** re-reads both cars' list
     pages and the product pages through `fetch.py`, cache first.
   - 0 errors are required. Record the result under "OEM spot-checks" in
     `scraper/interchange_research.md` and in `CATEGORY_STATUS`.
   - Any error requires a root cause, a rule fix, a re-run and a fresh
     sample.
5. **Ship Phase 1 data** (`oemGroups` / `oemVg`). It reaches web clients
   with the Phase 1 app, and native clients after "ship". The owner reviews
   `_report/<ns>.md` before the first merge per namespace.
6. **Phase 2 and Phase 3**, each only with a measured gain and a passed
   audit.
7. **Recurring.** Re-curate after crawl batches. Build-time expiry withdraws
   groups whose evidence passes 120 days.

---

## 12. Explicitly out of scope / deferred

- **Option partitions as "Verified, if equipped the same"** (Q1). They ship
  Likely, naming both numbers.
- **Plant translation via VIN** (Q2), and **vPIC trim tokens confirming
  trim-restricted rows** (Q3). Computed but not shipped.
- **Colour-variant collapse** (§5.14). Off until a per-category audit.
- **B's "bracketed E2"** calibration (inferring a closed cell between two
  closed years). Not adopted, because closure needs the cell's own pages.
- **README tolerance for superseded numbers with unread fitment.** Not used
  by the OEM layer. Existing hand groups citing reman application lists are
  unaffected.
- **Per-component search** (regulator alone vs motor alone) and **position
  chips** (driver only). Phase 2+ UI.
- **Lazy per-category files** (`docs/data/oem/<cat>.json`). Only if V11's
  budget binds.
- **Aftermarket track** (DB Electrical). Never Verified on its own; joining
  it through OE numbers is a separate design.
- **Second-source catalogs** (toyotapartsdeal, chevypartsdeal). Same dealer
  network, so not independent verification.
- **Automatic edits** of PLATFORM_FAMILIES or ENGINE_FAMILIES by curate.py.
  Only the payload-time demotions of §7.6 run automatically.
- **Out of scope by standing rules:**
  - UNOBTANIUM_DB parts rows (rule 3 basis docs elsewhere);
  - engines, transmissions and catalytic converters (rule 4);
  - saved watches (rule 6);
  - Row52 (rule 7);
  - any bot-check workaround: a refused site stops (rule 2).

## 13. Owner questions

1. Should option partitions (heated vs non-heated, HID vs halogen, with
   both numbers named) ever show "Verified fit, if equipped the same", or
   stay Likely? This spec: Likely.
2. Can the catalog's "US Built / Japan Built" be matched to the VIN's first
   character (USA 1/4/5, Japan J) to unlock plant-conditional Verified
   pairs? It needs an audit. On the lots, 2,108 of 2,594 Camry 2007-11 are
   US-built.
3. Can vPIC trim strings confirm catalog trim restrictions (Phase 2+,
   with its own audit)?
4. Should donors that the catalog contradicts be hidden with a count, or
   kept as Likely with a warning?
5. Should OEM claims ever be mirrored into the old keys before native users
   have the P0 guards? This spec: no.
