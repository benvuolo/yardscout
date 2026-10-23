# Part Catalog Spec — expanding the Parts-tab finder to the full u-pull catalog

*Research + design spec, 2026-10-22. No code in this commit. Implementer: the
interchange worker (feature/interchange), after its current performance-trims
task lands. Companion docs: `scraper/interchange_research.md` (per-family
evidence, Verified methodology), `scraper/consensus_parts_research.md` (demand
sources + existing exclusions), `docs/data/interchange.json` (shipped schema).*

## 0. What this spec is

The Parts-tab finder today answers 12 categories: **alternator** and
**starter** through 177 engine families (`engineFamilies`, Verified groups
from published part-number application lists), and ten body/interior
categories (gauge cluster, climate panel, window regulator, window switch,
tail lights, headlights, side mirrors, tow mirrors, 3rd-row seat, tailgate)
through 80 `platformGroups` plus the same-model same-generation fallback.

This spec defines the target catalog: **~75 categories** covering what people
actually pull at self-service yards, each with an interchange rule class, a
confidence policy, coarse value data, demand evidence from the yards' own
published price sheets, and a priority tier. It ends with a **P0 ship list of
25 categories** buildable in one pass, almost entirely on data the app
already has.

### Inputs absorbed

- `interchange_research.md` — 177 verified engine families, Verified/Likely
  methodology ("Verified = seeker AND donor inside ONE published part-number
  application list"), ambiguity caps, config-split downgrades.
- `docs/data/interchange.json` — shipped schema: `categories[]` (id, label,
  kind ∈ {engine, body}, tokens, priceTokens), `engineFamilies[]` (apps +
  per-part `vg` verified groups + year windows), `platformGroups[]` (80
  groups across 33 platforms), `trimEngineNotes[]`.
- **22 yard price-sheet sources** in `docs/data/*_pricing.json` (~6,300
  distinct published part names) — the demand-side catalog: if yards print a
  price for it, people pull it.
- `PART_KEYWORD_MAP` in `docs/app.js` (~142 canonical keywords → per-chain
  price-list names) — the Yards-tab compare vocabulary.
- `consensus_parts_research.md` — 3+-source demand evidence per evergreen
  category; the documented exclusions (airbags/SRS, A/C compressors, steering
  racks, cats).
- `price_baseline.json` (67 audited part bands, eBay-sold observed) and the
  UNOBTANIUM/overlay per-vehicle part rows (name/low/high/fits).
- External 2026 pricing surveys for the new big-ticket categories (used
  engines $300–2,800 typical junkyard-sourced, 4-cyl $400–900 / V6 $600–1,400
  / V8 $800–2,200; transmissions auto $250–1,200 self-serve→online, manual
  $200–800; doors complete $100–500; fenders $50–250; bumpers $50–300 —
  u-pull-it.com, partpriceguide.com, hotlinehq.online, 603autosalvage.com,
  allescarparts.com, all retrieved 2026-10-22).

### Charter note (owner decision required in copy, already made in scope)

`README.md:16` and `junkyard_scraper.py:11` say **"No engines. No
transmissions. Just parts you can carry out."** This spec adds both — as
**repair-fitment categories in the finder**, not as flip-value rows. The
UNOBTANIUM value DB keeps its carry-out-and-flip charter; engines and
transmissions get finder rows, yard-sheet prices, and honesty notes, but no
"worth $X–Y flip" band. The README/scraper tagline needs rewording when P0
ships (suggested: "Flip parts you can carry out. Fix your car with the rest.").

---

## 1. Interchange rule classes

Every category gets exactly one class. Classes map to search strategies the
app already has (or nearly has):

| Class | Question it answers | Existing machinery | Gap |
|---|---|---|---|
| **A. engine-family** | "same engine ⇒ same part" | `engineFamilies` (177 fams, apps, VIN-decode verdict via `pfEngineVerdict`, per-part `vg`) | add new part ids to `parts{}` per family; new `vg` research only where Verified is wanted |
| **B. platform-generation** | "same body platform / same generation ⇒ same part" | `platformGroups` (80) + same-model same-gen fallback (`pfSquashModel` + per-part `fits` windows) | generation-window table for high-population models so the fallback works without a hand-researched part row (see §5.1) |
| **C. engine+platform combo** | part must match BOTH engine and chassis (trans, transfer case, axle, radiator, exhaust manifold, ECU) | both tables exist; no combined query path | new `kind: "combo"`: body-path donor filter × engine-family chip; tier capped Likely unless a code-level table verifies |
| **D. exact-match-only** | same model + same generation is the *only* honest claim; options/electronics vary too much (radios, clusters, BCMs) | same-model fallback path | new `kind: "exact"`: skip platform groups, always-Likely, category-level mandatory note |
| **E. universal-ish** | fits by spec, not by vehicle (batteries, wheels by bolt pattern) | none | out of scope for the finder — the compare tab already prices these; don't build fitment UI for them |

Class D vs B is a policy line, not a data line: a 2007 Silverado radio *is*
GMT800-shared hardware, but VIN-locks and RPO splits make "platform fits"
a false promise — so radios are D even though the metal interchanges.

## 2. Confidence policy

Existing standard stays the law: **Verified only when seeker AND donor sit
inside one published part-number application list** (or a hand-verified
platform group for by-design-identical body hardware). Everything else is
Likely, and some categories are **always-Likely-with-note** — the note is
part of the category definition, not optional copy:

| Policy | Categories | Mandatory note (gist) |
|---|---|---|
| Verified possible (existing vg/groups) | alternator, starter, tailgate, headlights, window reg/switch, climate panel, 3rd row, tow mirrors, tail lights, side mirrors, gauge cluster | per-group notes as shipped |
| Verified possible (new research) | engine assembly (family = the application list; see §4), ignition coils, intake manifolds, turbos, cylinder heads | "match casting/part number" |
| Always-Likely + code note | **transmissions** ("verify the transmission code on the case tag — ratios, bellhousing and TCM calibration differ within one model year"), transfer cases ("match the assembly tag — gear vs chain drive, manual vs electric shift"), axles/diffs ("match the axle code and ring-gear ratio tag; ABS tone ring differs"), ECM/PCM ("match the part number exactly; most 2000s+ need programming"), radios/infotainment ("many are VIN-locked / anti-theft coded"), clusters ("mileage shows the donor's reading; many 2000s+ need mileage/immobilizer pairing") | |
| Always-Likely + wear note | struts ("springs sag with miles — donor mileage unknown"), fuel pumps ("electric pumps are wear items; donor mileage unknown"), control arms ("bushings/ball joints wear — inspect before pulling") | |
| Always-Likely + paint note | every painted panel: doors, fenders, hoods, bumpers, trunk lids, liftgates ("color code must match or plan to paint — check the door-jamb sticker on both cars") | |

### Safety / legal exclusions (researched; recommendations)

- **Airbags, inflators, airbag covers, SRS modules — stay excluded.** eBay
  prohibits all airbag/inflator/cover listings sitewide since 2026-09-24;
  49 U.S.C. 30122 render-inoperative liability. Already documented in
  `consensus_parts_research.md`; nothing changes.
- **Seatbelt pretensioners — recommend KEEP EXCLUDED.** Same pyrotechnic SRS
  family, same eBay policy cluster (SRS electronics are pre-approved-sellers-
  only), same liability chain. Practical consequence: no "seatbelt" category
  at all, since effectively every belt 1996+ carries a pretensioner. Not
  worth a pre-1996-only category.
- **Front seats with side airbags — include the category, carry a mandatory
  note.** Most 2000s+ front seats contain seat-mounted side airbags; the
  category ships with "many 2000s+ front seats contain side airbags — those
  can't be listed on eBay; local sale or own-car use only." This mirrors how
  steering wheels were handled (pre-airbag year gates in the value DB).
- **Used brake rotors — recommend EXCLUDE.** Wear item with a legal minimum-
  thickness spec you can't verify in a yard row, new aftermarket is $25–60,
  resale ≈ nil; every flipper source says skip. Exclusion is value-based,
  not legal. Calipers/boosters/master cylinders stay in (hydraulics are
  commonly bought used; notes below).
- **A/C compressors — existing exclusion stands for value bands** (internal
  failure invisible at the yard, contamination returns; the "stand behind the
  band" standard — `consensus_parts_research.md`). Finder inclusion is
  deferred to P2 *at most*, finder-only, no resale band, mandatory "internal
  condition unknowable at the yard; a contaminated system kills the
  replacement too" note. Not in P0/P1.
- **Catalytic converters — stay excluded** (state scrap-law provenance;
  yards strip or restrict them anyway).
- **Power steering racks — stay excluded** per existing research (safety-
  critical steering + messy pull). Power steering *pumps* are P2.
- **Windshields — exclude.** ADAS recalibration on 2016+ cars, cheap
  installed-new aftermarket, high transport breakage. Door/back/quarter
  glass stay in.

## 3. Master catalog table

Column key — **Class**: rule class from §1. **Data**: what answers it today
(EF = engineFamilies, PG = platformGroups, GEN = same-model generation
fallback) and what's missing. **Conf**: V = Verified reachable, L = Likely
only, L! = always-Likely-with-mandatory-note. **eBay**: coarse working-part
sold range (national; sources §0 + `price_baseline.json`). **Sheets**: how
many of the 22 price-sheet sources publish the part (measured this pass).
**Tier**: P0 ship-first / P1 / P2.

### Body panels & exterior

| Category | Class | Data | Conf | eBay | Sheets | Tier |
|---|---|---|---|---|---|---|
| Door (front, shell/complete) | B | GEN now; PG twins (Silverado/Sierra etc.) cheap adds | L! paint | $100–400 | 20/22 | **P0** |
| Door (rear) | B | same | L! paint | $75–300 | 20/22 | P1 |
| Fender | B | GEN now | L! paint | $50–250 | 19/22 | **P0** |
| Hood | B | GEN now; PG twins | L! paint | $75–300 | 17/22 | **P0** |
| Tailgate (truck) | B | **shipped** (6 PG verified) | V | $150–600 | 20/22 | **P0** ✓ |
| Trunk lid / decklid | B | GEN; spoiler/camera-hole note | L! paint | $75–250 | 18/22 | **P0** |
| Liftgate / hatch (SUV/van) | B | GEN; glass/wiper/camera variant note | L! paint | $100–400 | ~8 explicit, most price via door/gate rows | **P0** |
| Bumper (front, cover or steel) | B | GEN; park-sensor cutout note | L! paint | $50–300 | 22/22 | **P0** |
| Bumper (rear) | B | GEN | L! paint | $40–250 | 22/22 | P1 |
| Grille | B | GEN **with facelift windows** (§5.2) | L→V (facelift-split groups) | $40–300; halo trims $300–600 | 22/22 | **P0** |
| Side mirrors | B | **shipped** (1 PG) | V/L | $30–200 ea | 22/22 | **P0** ✓ |
| Tow mirrors | B | **shipped** (4 PG) | V | $60–160 pr | 22/22 | **P0** ✓ |
| Door glass | B | GEN; PG across cab styles later | L | $40–120 | 22/22 | P1 |
| Back glass / hatch glass | B | GEN | L | $50–150 | 22/22 | P2 |
| Quarter / vent glass | B | GEN | L | $25–80 | 22/22 | P2 |
| Door handles (ext.) | B | GEN | L! paint | $15–50 | ~18/22 | P2 |
| Hood hinges / latches | B | GEN | L | $15–40 | 17/22 | P2 |
| Running boards | B | GEN | L | $75–250 pr | ~20/22 | P2 |

### Lighting

| Category | Class | Data | Conf | eBay | Sheets | Tier |
|---|---|---|---|---|---|---|
| Headlights | B | **shipped** (10 PG); add facelift windows + halogen-vs-HID/LED split note | V/L | $40–200; OEM HID/LED $150–600 pr | 22/22 | **P0** ✓ |
| Tail lights | B | **shipped** (5 PG); facelift windows | V/L | $30–150 | 22/22 | **P0** ✓ |
| Fog lights | B | GEN | L | $20–60 | 22/22 | P2 |
| 3rd brake light / markers | B | GEN | L | $15–40 | ~19/22 | P2 |

### Interior

| Category | Class | Data | Conf | eBay | Sheets | Tier |
|---|---|---|---|---|---|---|
| Front seats (pair) | B | GEN + curated trim rows (Recaro etc. already in DB) | L! side-airbag note | $100–500 pr; perf trims $400–1,200 | 22/22 | **P0** |
| 2nd row / bench | B | GEN | L | $60–250 | 22/22 | P1 |
| 3rd row seat | B | **shipped** (6 PG) | V | $150–400 | 22/22 | **P0** ✓ |
| Instrument cluster | D | **shipped** (GEN + 1 PG); keep D policy | L! mileage/pairing | $40–150; perf/digital higher | 22/22 | **P0** ✓ |
| Radio / infotainment screen | D | GEN only — **new category, high demand** | L! VIN-lock | $50–500 | 22/22 | **P0** |
| Climate control panel | B | **shipped** (13 PG) | V/L | $40–120 | 15/22 | **P0** ✓ |
| Steering wheel | B | GEN; value DB stays pre-airbag-gated | L! "swap bare wheel only — your airbag stays" | $50–150; perf $150–400 | 22/22 | P1 |
| Steering column | D | GEN; key/immobilizer + column-shifter variants | L! | $75–250 | 16/22 | P2 |
| Center console | B | GEN | L! color | $50–200 | 22/22 | P1 |
| Door panels | B | GEN | L! color | $40–150 | 19/22 | P1 |
| Carpet | B | GEN | L! color | $50–150 | 19/22 | P2 |
| Headliner | B | GEN | L! color | $40–120 | 5/22 | P2 |
| Shifter assembly | B | GEN (compare map already has it) | L | $30–100 | ~20/22 | P2 |
| Pedal assembly | B | GEN | L | $25–80 | ~20/22 | P2 |

### Electrical

| Category | Class | Data | Conf | eBay | Sheets | Tier |
|---|---|---|---|---|---|---|
| Alternator | A | **shipped** (177 fams, vg) | V/L | $35–90 | 22/22 | **P0** ✓ |
| Starter | A | **shipped** (177 fams, vg) | V/L | $30–75 | 19/22 | **P0** ✓ |
| ECM / PCM | C | EF chip × GEN — band already in value DB, finder category missing | L! program/match | $40–150 (to $400 high-pop) | 19/22 | **P0** |
| BCM | D | GEN | L! program | $40–120 | 22/22 (module rows) | P1 |
| TCM | C | EF × GEN | L! program | $40–120 | ~15/22 | P2 |
| Window switches | B | **shipped** (17 PG) | V/L | $25–80 | 10/22 explicit (others via switch rows) | **P0** ✓ |
| Window regulators | B | **shipped** (17 PG) | V/L | $35–85 | 21/22 | **P0** ✓ |
| Ignition coils (set) | A | EF answers directly — zero new fitment data | L "match coil part #" | $8–25 ea, $40–120 set | 17/22 | **P0** |
| Blower motor | B | GEN (heavy supplier overlap, still platform-keyed) | L | $25–80 | 18/22 | P1 |
| Radiator cooling fan assy | C | EF × GEN (engine option changes fan) | L! | $40–120 | 19/22 | P1 |
| Wiper motor | B | GEN | L | $30–80 | 20/22 | P1 |
| Door lock actuators | B | GEN | L | $20–60 | 13/22 | P2 |
| Ignition switch w/ key | D | GEN; immobilizer | L! pairing | $30–100 | 14/22 | P2 |
| Misc switches (dimmer, 4WD selector…) | B | GEN; compare map rows exist | L | $10–40 | 22/22 | P2 |

### Engine & driveline

| Category | Class | Data | Conf | eBay | Sheets | Tier |
|---|---|---|---|---|---|---|
| **Engine assembly** | A | **EF is the application list** — crown jewel, §4 | V (decode-confirmed, §4) / L | resale $400–1,500 common; yard price $150–350 + core | 18/22 | **P0** |
| Transmission (automatic) | C | GEN × EF chip; no code table yet | **L! always** ("verify transmission code — ratios differ") | $250–1,200 | 18/22 | **P0** |
| Transmission (manual) | C | same; enthusiast demand | L! code note | $200–800 | 18/22 | P1 |
| Transfer case | C | GEN × EF; PG for common GM/Ford cases later | L! tag note | $150–500 | 21/22 | P1 |
| Axle assembly (front/rear) | C | GEN; ratio/ABS tag note | L! ratio note | $150–600 | 17/22 | P1 |
| Differential / 3rd member | C | same | L! ratio note | $100–400 | 22/22 | P1 |
| Cylinder head | A | EF + casting number note | L→V (casting lists) | $75–300 | 8/22 | P1 |
| Intake manifold | A | EF; upper/lower + chassis-variant note | L | $40–150 | 20/22 | P1 |
| Turbocharger | A | EF | L | $150–500 | 19/22 | P1 |
| Exhaust manifold | C | EF × chassis routing | L | $30–120 | 8/22 | P2 |
| Throttle body | A | EF | L | $30–100 | ~18/22 | P2 |
| Fuel injectors / rail | A | EF | L | $30–90 set | ~17/22 | P2 |
| Valve cover / oil pan | A | EF; pan is chassis-variant | L | $20–80 | ~18/22 | P2 |
| Engine wiring harness | C | exact-leaning | L! | $75–250 | ~15/22 | P2 |
| CV axle / halfshaft | B | GEN | L | $25–80 | 16/22 | P2 |
| Driveshaft | C | GEN + length/config | L! | $60–200 | 18/22 | P2 |
| Flywheel / flexplate | C | EF × trans | L! | $40–120 | ~16/22 | P2 |

### Suspension, steering, brakes

| Category | Class | Data | Conf | eBay | Sheets | Tier |
|---|---|---|---|---|---|---|
| Struts / strut assemblies | B | GEN; FWD/AWD + corner split | L! wear | $40–150 pr | 20/22 | P1 |
| Spindle / knuckle | B | GEN (collision demand) | L! ABS note | $40–120 | 19/22 | P1 |
| Control arms | B | GEN | L! wear | $30–100 | 18/22 | P1 |
| Coil / leaf springs | B | GEN; payload-package variance | L! | $40–120 | 14–16/22 | P2 |
| Sway bars | B | GEN (enthusiast upsize swaps) | L | $30–80 | ~16/22 | P2 |
| Hub / bearing assembly | B | GEN | L! wear | $25–80 | 19/22 | P2 |
| Brake calipers | B | GEN + curated perf PG rows (Brembo already in DB) | V (perf groups) / L | $25–80 ea; perf sets $250–800 | 22/22 | P1 |
| Brake booster | B | GEN | L | $40–120 | 16/22 | P2 |
| Master cylinder | B | GEN | L | $25–80 | 9/22 | P2 |
| ABS pump / module | D | curated rows exist (E39/E46) | L! pairing | $75–300 | 21/22 | P1 |
| Power steering pump | C | EF-adjacent | L! | $30–90 | 16/22 | P2 |

### Cooling, fuel, HVAC

| Category | Class | Data | Conf | eBay | Sheets | Tier |
|---|---|---|---|---|---|---|
| Radiator | C | GEN × EF (trans-cooler + dims variants); cheap-new-aftermarket honesty note | L! | $40–120 | 18/22 | P1 |
| A/C condenser | C | same | L | $30–80 | ~18/22 | P2 |
| Fuel pump (in-tank) | **B (not A!)** | tank/platform-keyed, not engine-keyed — call this out in implementation | L! wear | $30–80 | 18/22 | P1 |
| Fuel tank | B | GEN | L | $75–200 | 19/22 | P2 |
| Water pump | A | EF | L! wear | $20–60 | ~20/22 | P2 |
| Heater core | B | GEN | L | $25–70 | ~15/22 | P2 |
| Intercooler | A | EF (turbo cars; curated rows exist) | L | $75–300 | 19/22 | P1 |
| A/C compressor | A | **existing exclusion** — see §2; P2 at most, finder-only, no band | L! condition | — | 19/22 | P2* |

## 4. Engine assemblies — the careful spec

The engine-family table **is** the application list for the assembly itself,
which makes this the cheapest high-value category in the whole expansion —
but only with these rules:

1. **Tier.** Donor shows **Verified** only when (a) seeker and donor both
   match the family's apps without an ambiguity cap, AND (b) the donor's VIN
   decode (`vehicle_extras`, existing `pfEngineVerdict` path) confirms the
   engine. Decode-unconfirmed donors show Likely with the existing "engine
   not confirmed — check under the hood" warning. Ambiguity-capped apps
   (Vulcan-vs-Duratec Taurus etc.) stay Likely exactly as they do for
   alternators.
2. **Long-block caveat (always shown).** "Same family = the long block
   interchanges. Manifolds, mounts, oil pan, accessories and wiring often
   differ between models — plan to swap yours over." (Real example for the
   note's accuracy: LS truck vs car oil pans/intakes within one family.)
3. **Mileage disclaimer (always shown).** "Mileage and internal condition
   are unknown — yards track cars, not engines. Pull a valve cover or check
   the oil before you commit."
4. **Pull-reality note (always shown).** "Engine pulls take hours and need a
   hoist — call ahead. Some self-serve yards don't allow engine pulls or
   rent hoists; most charge a core fee refunded on your old unit."
5. **Price display.** Yard-sheet engine rows vary by cylinder count
   ("ENGINE 4 CYL" / "ENGINE (NO ACC)" / "ENGINE - LONG BLOCK" …);
   priceTokens should prefer the cylinder-count row matching the family's
   `cyl` field where the sheet splits, else the generic engine row. No
   resale band (charter, §0) — show yard price + core only.
6. **No new fitment research needed for P0.** Optional later: per-family
   `assemblySpans` (analogous to `vg`) marking spans where accessories also
   match, upgrading the long-block note to "drop-in within this span".

Transmissions ship the same honesty pattern minus the Verified path:
**always Likely**, note "verify the transmission code on the case tag —
ratios, bellhousing and TCM calibration differ even within one model year",
same pull-reality and mileage notes, 4x4/2WD split from the donor row where
the sheet prices them differently. A future transmission-code table (RPO
codes / J-cases) is the only path to Verified — out of scope here.

## 5. New data the implementer needs (and what it does NOT need)

1. **Generation-window table** (`modelGenerations`): make|model → list of
   (gen label, year-from, year-to) for the ~150 highest-population models.
   Today the same-model fallback only fires when a hand-researched part row
   carries a `fits` window; a generation table makes every class-B category
   work for every covered model with zero per-part research.
   `_ENTHUSIAST_EVERGREEN_GENS` in the scraper and the fits-window audit
   (`_audit_genfits.py`) are the seed.
2. **Facelift windows** for grille/headlight/tail-light groups: optional
   `facelift` year-splits on platformGroups (mid-cycle refresh changes these
   parts while the generation continues). Without it, those categories keep
   generation-width windows and stay Likely — acceptable for P0.
3. **New `kind` values** in `interchange.json categories[]`: `combo` and
   `exact` (§1). `body` continues to mean class B. Schema version bump.
4. **Token hygiene** (§6): per-category `tokens`/`priceTokens` defined here
   become the single taxonomy for finder + compare + value DB.
5. **NOT needed for P0:** transmission code tables, axle ratio tables,
   casting-number lists, per-category vg research for body panels. Verified
   coverage grows later exactly the way alternators did — part-number lists,
   one family at a time.

## 6. One taxonomy — where finder and price-compare disagree today

The two tabs must feel like one system. Today there are three vocabularies:
finder `categories[]` (12 ids + priceTokens), compare's `PART_KEYWORD_MAP`
(~142 keywords) + raw sheet names (~6,300), and UNOBTANIUM row names.
Divergences found this pass — all fixed by making THIS table's category ids,
tokens and priceTokens the single source both tabs read:

1. **`starter` and `climate control` are missing from `PART_KEYWORD_MAP`**
   entirely. The compare tab prices them only when a yard's raw sheet
   happens to contain the substring — "climate" misses the 15 sources that
   spell it "HEATER CONTROL"/"TEMPERATURE CONTROL", which the finder's
   priceTokens *do* catch. Same part, different price answer per tab.
2. **Tow mirrors quote the wrong row.** Finder priceTokens for
   `tow-mirrors` are `["mirror"]`, so a tow-mirror search quotes the generic
   power-door-mirror price (and the compare map's `mirror` keyword does the
   same). Tow mirrors need their own sheet mappings where chains price them
   (several price "MIRROR (TOW)" / truck-mirror rows).
3. **`third-row-seat` priceTokens are a substring hazard**: tokens
   `["third","3rd","seat"]` with cheapest-row-wins can land on "3RD BRAKE
   LIGHT" or "DIFFERENTIAL (… 3RD MEMBER …)" rows. Token matching needs
   word-boundary anchoring or ordered-token-priority before the catalog
   grows 6× (this bug class multiplies with every new category).
4. **Coverage asymmetry.** The compare map prices ~30 whole categories the
   finder doesn't know (bumper, grille, console, sunroof, transfer case,
   differential, caliper, shifter, intercooler, hitch…). Users can price a
   bumper but not find one that fits — the finder expansion closes exactly
   this gap, and each new category must reuse the compare map's existing
   per-chain name mappings rather than invent new priceTokens.
5. **Display-name drift**: finder "Gauge cluster" vs compare suggestions
   "Instrument Cluster" (raw sheets) vs value-DB "Gauge Cluster / IPC".
   Canonical display labels in this spec's table win everywhere; raw sheet
   spellings remain match-targets, never display names.

## 7. P0 ship list — 25 categories, one implementation pass

Twelve already live (keep, extend where noted) + thirteen new. Chosen by
search demand × how cheaply existing tables answer them:

**Live (12):** alternator ✓, starter ✓, gauge cluster ✓, climate control
panel ✓, window regulator ✓, window switch ✓, headlights ✓ (+facelift note),
tail lights ✓, side mirrors ✓, tow mirrors ✓ (+fix priceTokens, §6.2),
3rd-row seat ✓ (+fix tokens, §6.3), tailgate ✓.

**New (13):**
1. **Engine assembly** (class A — the crown jewel; §4)
2. **Transmission, automatic** (class C — always-Likely + code note)
3. **Door, front** (B)
4. **Fender** (B)
5. **Hood** (B)
6. **Bumper, front** (B)
7. **Grille** (B)
8. **Trunk lid / decklid** (B)
9. **Liftgate / hatch** (B)
10. **Front seats, pair** (B — side-airbag note mandatory)
11. **Radio / infotainment** (D — VIN-lock note)
12. **ECM / PCM** (C — value band already exists in the DB; finder row missing)
13. **Ignition coils** (A — rides the 177 families with zero new fitment data)

All 13 run on machinery that exists today (engine families, platform groups,
same-model generation fallback) plus the §5.1 generation-window table. None
require new Verified research to ship honestly — Likely-with-note is the
launch posture everywhere the tables don't already prove Verified.

**P1 next (14):** rear doors, rear bumper, door glass, 2nd-row seats,
steering wheels, consoles, door panels, BCM, blower motor, cooling fan,
wiper motor, manual transmission, transfer case, axle/diff, struts,
spindles, control arms, calipers, ABS module, radiator, fuel pump,
intercooler, cylinder head, intake manifold, turbo. (Build order inside P1:
whatever the generation table makes free first.)

**Excluded permanently (with reasons, §2):** airbags/SRS, seatbelt
pretensioners, catalytic converters, windshields, used brake rotors, power
steering racks, sun visors/smalls under the money bar. A/C compressor
deferred to P2-if-ever under finder-only conditions.
