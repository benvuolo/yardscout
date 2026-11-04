# Parts-gap curation — 2026-11

The most common cars on the lots matched only the generic commuter rows
(headlights, mirrors, tail lights, the seven consensus evergreens), so their
Pro value lines said little about the car. This pass adds model-specific
rows, one model at a time, with the owner reviewing each before the next.

**Basis for every row**

- *Pull cost*: the median of the category across the 30 yard price lists the
  app already publishes (`docs/data/*_pricing.json`, 2026-11-03), e.g.
  fuel pump $24, throttle body $32, A/C compressor $40, fan assembly $16,
  seat $24 (power seats run higher), alloy wheel $25 each, spoiler $28,
  tail light $23, headlight $10–25.
- *Band*: a conservative used-OEM resale anchor for that exact part, kept
  in line with the audited bands for the same category elsewhere in the
  table (e.g. the Camry/Accord headlight and seat rows). The display pass
  (`_resale_sold_calibrate`) scales anchors down toward sold prices, and
  the live eBay feed (`ebay_prices.py`) replaces each band with real
  listing data once the keys exist. These anchors are placeholders for
  that, not claims of measured sold prices.
- *Gates*: options (spoilers, leather, wheels, HID) are flagged `option`
  so they ship "if equipped" and add $0 to ranking; coupe-only parts use
  the new `body` gate, which the VIN decode confirms or excludes.
- Never engines, transmissions or catalytic converters.

## 1. Nissan Altima (8,700 cars tracked; #3 nationally)

Generations: L31 2002–2006 · L32 2007–2012 (sedan + 2008–2013 coupe) ·
L33 2013–2018 · L34 2019+.

| Row | Years | Gate | Why |
|---|---|---|---|
| Electronic Steering Column Lock (ESCL) | 2007–2012 | — | Push-button start was standard on every L32; the ESCL is the generation's famous failure (dealer fix $800+), so working used units sell steadily. Overlay row widened from 2009-only. |
| Fuel Pump Module | 2002–2018 | — | Common DIY replacement on QR25/VQ35 cars; cheap pull, reliable seller. |
| Electronic Throttle Body | 2002–2018 | — | Known QR25DE failure point; match the part number across the three generations. |
| A/C Compressor | 2002–2018 | — | High-population application; verify the clutch spins. |
| Radiator Fan Assembly | 2002–2018 | — | Dual-fan assembly, frequent failure, low pull cost. |
| Rear Spoiler (factory) | 2002–2018 | option | Trim-package option on every generation. |
| Leather Power Driver Seat (SL) | 2007–2018 | option | SL package; never VIN-decodable. |
| 17"/18" Alloy Wheels (set) | 2007–2018 | option | SE/SL/SR wheels; set price, local sale. |
| HID Xenon Headlights (pair) | 2010–2012 | option | 3.5 SR premium package only; rare. |
| Headlights w/ LED Signature (facelift) | 2016–2018 | — | The 2016 facelift lamps resell well above the pre-2016 halogen row, which now stops at 2015. |
| Coupe Tail Lights (pair) | 2008–2013 | body: coupe | Coupe-only lamps, far fewer cars built. |
| Coupe Headlights (pair) | 2008–2013 | body: coupe | Same. |

Also: the overlay's Bose row extended 2005–2012 (the base entry covers
2013+).

Not added, on purpose: CVT (transmission), QR25DE/VQ35 engines, catalytic
converter, key fobs (programming), ignition coils (cheap new).

## 2–10. The next nine (same basis; "mech" = fuel pump module, A/C compressor, radiator fan assembly)

| Model | Cars | Rows added | Notes |
|---|---|---|---|
| Toyota Camry | 7,600 | mech 2002–17; Entune touchscreen 2012–17 and Entune 3 2018+; JBL and hybrid pack extended to 2015–17; SE/XSE spoiler, 17"/18" wheels, XLE leather seat, sunroof (options) | The 2012–17 Camry had no head-unit row at all. |
| Honda Civic | 6,500 | mech per generation 2001–15; EX sunroof, EX/Si wheels (options); tail lights; 8th-gen EX-L navigation unit (option) | Rows go on the generation entries, since the split replaces the base entry. |
| Ford Focus | 6,350 | mech 2008–18; DCT transmission control module 2012–18; MyFord Touch screen 2012–14; mirrors and tail lights (the entry had neither); hatchback tail lights (body gate); Titanium wheels and heated leather seats (options) | The TCM is the electronic module, not the gearbox. |
| Chevrolet Malibu | 5,760 | mech 2004–24; sunroof, LTZ heated leather, 17"/18" wheels, remote-start BCM (options) | |
| Ford Escape | 4,850 | mech 2001–19; EcoBoost turbo 2013–19 (option: engine not gated); AWD power transfer unit 2013–19 (drive gate); MyFord Touch 2013–16; roof rack crossbars; heated leather (options) | PTU confirmed only on an AWD decode; FWD decodes exclude it. |
| Chevrolet Equinox | 4,140 | mech 2005–24; mirrors and tail lights (missing before); AWD rear differential/transfer unit (drive gate); sunroof, Pioneer audio, LTZ leather, 18"/19" wheels (options) | |
| Nissan Sentra | 4,130 | mech 2007–19; SR spoiler and SR 17" wheels (trim); Bose (SL), sunroof, leather seat (options) | |
| Toyota Corolla | 3,450 | mech 2003–19; S/XSE spoiler, 16"/17" wheels, sunroof (options) | |
| Hyundai Elantra | 3,170 | mech 2007–16; headlights, mirrors, tail lights for 2011–16 (the overlay's cover 2005–10); Limited navigation and heated leather, sunroof, wheels (options) | |

**Merge fix that came out of this:** the overlay merge used to skip any
part whose name already existed in the entry, regardless of years, so a
new 2011–16 Elantra headlight row silently dropped the 2005–10 one. It now
skips only when the model-year windows overlap.

## 11. Breadth pass (2026-11-04)

Measured against the lots (334k cars): 9% of cars had no entry at all and 9%
matched only generic rows.

- **101 mid-volume models with no entry** (80–490 cars each, ~16,500 cars:
  Lincoln MKZ/MKX/MKS, Uplander, Mazda5, Windstar, Spark, Captiva Sport, Juke,
  Encore, Park Avenue, Stratus, Trax, Escort, Volvo S40/V70/XC60/C70, Fiat
  500, Jaguar S-/X-Type/XF/XJ, Infiniti QX60/Q50/EX35/I30 …) get the commuter
  lamp/mirror rows plus the consensus evergreens (`_GAP_GENERIC_KEYS`).
  Year ranges are the model's US run; nothing model-specific is claimed.
- **Feed spellings routed to existing entries:** "Dodge 1500 Pickup"/"D1500"
  → Ram, "Chevrolet Gmt-400"/K2500/C2500/C10 → C/K, "Chrysler Caravan" →
  Caravan, "Chevrolet Classic" → Malibu.
- **Curated** (same basis as the Altima block): Rogue 2008–20, CR-V 2002–16,
  RAV4 2001–18, Explorer 2011–19 — pre-LED headlight rows (all three had only
  LED rows), the three mechanical pulls, AWD transfer units on a drive gate,
  Entune/navigation units, and option-flagged sunroofs, leather, wheels,
  roof-rack crossbars, JBL/Bose.

## 12. Enthusiast audit (2026-11-04)

The cars people flip most, reviewed row by row:

- **WRX / Impreza:** a "Subaru Impreza WRX" listing matched both the `impreza`
  entry (whose interchange rows carry WRX parts "if equipped") and the `wrx`
  entry, so the hood scoop and intercooler showed twice. The `wrx` entry now
  owns the "impreza wrx"/"impreza sti" spellings, so those listings match it
  alone; it gained headlight and tail-light rows so the WRX card isn't poorer
  than the Impreza one. 1998–2001 2.5RS: gold wheels and hood scoop (trim RS).
- **Miata:** no headlight row existed before 2006. NA pop-up motors + lamps
  (1990–97), NB lamps (1999–2005), NC power-hardtop mechanism (option).
- **4Runner:** 4th/5th gen power rear-window regulator (a known failure),
  sliding cargo deck and 3rd row (options), Limited X-REAS shocks (trim),
  2014–19 Entune unit.
- **Tacoma:** TRD skid plate, TRD Pro grille and colour-matched flares were
  listed as if every truck had them; now option-flagged. Added deck-rail
  system (option), 2nd-gen flares (option), 3rd-gen Entune unit.
- **Cherokee XJ:** had three rows. Added liftgate, uncracked dash bezel and
  door panels (the plastics everyone hunts), tail lights, 1997–2001
  composite headlights and fog lights (option), mirrors.
- Civic Si needed nothing; vPIC supplies its trims and the rows were right.

## 13. Measured block (2026-11-04): Camry/Corolla 1990s, Accent, LeSabre, LaCrosse, Soul

**Measurement.** Every distinct year/make/model on the lots (333,460 cars,
`docs/data/inventory_live.json`) re-matched with the current tables;
"generic-only" means every matched row is in the miner's generic tier
(`GENERIC_PART_TOKENS` in `mine_coverage_gaps.py`: lamps, mirrors, window
regulators/switches and the consensus evergreens). `interchange_coverage.py`
measures engine-family donors, not this, so the count was taken offline
with the same rule (the miner's `--no-fetch` analysis; its eBay page fetch
was not used, see rule 2). Before this block: no entry 12,298 cars (3.7%),
generic-only 43,010 (12.9%).

| Order | Model (years) | Cars | Generic-only before |
|---|---|---|---|
| 1 | Toyota Camry 1990–2001 | 2,271 | 2,047 |
| 2 | Hyundai Accent | 1,331 | 1,323 |
| 3 | Buick LeSabre | 1,144 | 1,098 |
| 4 | Buick LaCrosse | 1,077 | 1,077 |
| 5 | Toyota Corolla 1990–2001 (+2002) | 1,044 | 983 (+153 for 2002) |
| 6 | Kia Soul 2010–2013 | 1,673 total | 915 (all 2010–13; 2014+ already curated) |

**Pull costs**, re-checked against the 30 price lists (median of each yard's
median, regex on the description): fuel pump $25, A/C compressor $40,
radiator/cooling fan $21, spoiler $26, sunroof $39, alloy wheel $22, tail
light $21. These are within a few dollars of the §1 figures, so the new rows
reuse the audited `_GAP_MECH` costs and the existing row templates (sunroof
$30, leather power seat $40, wheel set $100) unchanged, for consistency.

**Generation bounds.** `_GEN_MECH_EXCLUDE_RE` keeps pump/compressor/motor
rows out of the automatic generation split, which is why the §2–10
mechanical rows show spans like "2002–2017". The rows in this block are
bounded per generation by hand (`_per_gen`), so no new "fits" badge crosses a
generation. The older spans are left as they are (an owner decision, not
changed in passing).

### 13.1 Toyota Camry 1992–2001 (XV10 1992–96, XV20 1997–2001)

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 1992–96, 1997–01 | — | Same commodity pulls as the 2002–17 rows; every car has them. |
| Leather power driver seat (XLE) | 1992–96, 1997–01 | option | XLE trim from 1992; not VIN-decodable. |
| Sunroof glass + motor | 1992–96, 1997–01 | option | Optional on LE/XLE. |
| Alloy wheels (set) | 1992–96, 1997–01 | option | Band below the 17"/18" row (smaller, older wheels). |

Left out, no stated basis: JBL audio before 2002 (offer years not confirmed),
coupe (1994–96) and wagon (1992–96) body lamps (exact years not confirmed),
distributor (ignition; cheap new). 1990–91 (V20) stays outside the entry.

Result: Camry 1990–2001 generic-only 2,047 → 0. Lots: generic-only 43,010
(12.9%) → 40,963 (12.3%); no-entry unchanged at 12,298 (3.7%).

### 13.2 Hyundai Accent 2000–2017 (LC 2000–05, MC 2006–11, RB 2012–17)

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 2000–05, 2006–11, 2012–17 | — | Commodity pulls on every car. |
| A/C compressor | 2000–05, 2006–11 | option | A/C was optional on the base LC/MC cars. |
| A/C compressor | 2012–17 | — | Standard on the RB. |
| Tail lights (pair) | 2000–05, 2006–11, 2012–17 | — | The entry had no tail-light row. |
| Hatchback tail lights | 2006–11, 2012–17 | body: hatchback | 3-door (MC) / 5-door (RB) lamps differ from the sedan's; fewer built. Same band as the Focus hatch row. |
| Sunroof, alloy wheels | 2006–11, 2012–17 | option | SE/premium-package options. |

Left out, no stated basis: LC (2000–05) hatch lamps, sunroof and wheels
(offer years not confirmed), SE rear spoiler. Headlights and gauge cluster
were already generation-split. 2018+ (HC, 29 cars) not in this block.

Result: Accent generic-only 1,323 → 29 (all 2018+). Lots: generic-only
40,963 (12.3%) → 39,669 (11.9%).

### 13.3 Buick LeSabre 1992–2005 (1992–99, 2000–05)

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 1992–99, 2000–05 | — | Commodity pulls on every car. |
| Leather power driver seat (Limited) | 1992–99, 2000–05 | option | Limited trim; not VIN-decodable. |
| Alloy wheels (set) | 1992–99, 2000–05 | option | |
| Tail lights (pair) | 2000–05 | — | The entry had none. |
| Sunroof | 2000–05 | option | |

Left out, no stated basis: 1992–99 tail lights and sunroof (a mid-run
lamp change could not be confirmed), head-up display (offer years not
confirmed), upper intake plenum (an engine component, and buyers replace the
failure-prone OEM part with the revised new one, so a used one has little
value). Pre-1992 LeSabres (46 cars) stay outside the entry.

Result: LeSabre generic-only 1,098 → 0. Lots: generic-only 39,669 (11.9%)
→ 38,571 (11.6%).

### 13.4 Buick LaCrosse 2005–2016 (W-body 2005–09, Epsilon II 2010–16)

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 2005–09, 2010–16 | — | Commodity pulls on every car. |
| Tail lights (pair) | 2005–09, 2010–16 | — | The entry had none. |
| Headlights (clear, non-hazed) | 2005–09 | — | Halogen lamps; the entry's only lamp row was the 2010+ HID/LED one. |
| AWD rear differential / transfer unit | 2010–16 | drive: awd/4wd | AWD offered on the Epsilon II; same band as the Equinox row. A FWD decode excludes it. |
| Harman Kardon amp + speakers | 2010–16 | option | Premium-audio option. |
| Sunroof, leather power seat (CXL/CXS), 17"/18" wheels | 2005–09, 2010–16 | option | |

Left out, no stated basis: IntelliLink touchscreen (first model year not
confirmed between 2013 and 2014), halogen lamps for 2010–16 base cars.
2017–19 (8 cars) not in this block.

Result: LaCrosse generic-only 1,077 → 8 (all 2017+). Lots: generic-only
38,571 (11.6%) → 37,502 (11.2%).

### 13.5 Toyota Corolla 1993–2002 (E100 1993–97, E110 1998–2002)

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 1993–97, 1998–02 | — | Commodity pulls on every car. |
| A/C compressor | 1993–97, 1998–02 | option | A/C was optional on the base 1990s cars. |
| Sunroof | 1993–97, 1998–02 | option | |

2002 is included because it is the last E110 year and the 2003+ rows start
at E120 (153 cars). Left out, no stated basis: alloy wheels (offer by trim
and year not confirmed), 1993–97 wagon lamps. 1990–92 (E90, 61 cars) stay
outside the entry.

Result: Corolla 1990–2001 generic-only 983 → 0, and 2002 153 → 0. Lots:
generic-only 37,502 (11.2%) → 36,366 (10.9%).

### 13.6 Kia Soul 2010–2019 (AM 2010–13, PS 2014–19)

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 2010–13, 2014–19 | — | Commodity pulls on every car. |
| Tail lights (pair) | 2010–13, 2014–19 | — | The entry had none. |
| Side mirrors (pair) | 2010–13, 2014–19 | — | The entry had none; the row does not claim power mirrors. |
| Sunroof, alloy wheels | 2010–13 | option | 2014+ keeps its trim-gated panoramic-roof row. |

Left out, no stated basis: the 2010–13 premium audio (speaker-light /
Infinity package offer years not confirmed). 2020+ not in this block.

Result: Soul generic-only 915 → 0. Lots: generic-only 36,366 (10.9%) →
35,451 (10.6%).

### 13.7 Block totals and what is next

Before → after (333,460 cars): generic-only **43,010 (12.9%) → 35,451
(10.6%)**, 7,559 cars moved to model-specific rows; no-entry unchanged at
12,298 (3.7%). Leftovers in the six models: Accent 2018+ (29), LaCrosse
2017+ (8), and the pre-entry years (Camry 1990–91, Corolla 1990–92,
LeSabre pre-1992).

Largest generic-only groups now: Ford Focus 2000–07 (1,535), Explorer
1st/2nd gen (1,173), Jeep Compass (911), Kia Rio (781), Buick Century
(704), Chevrolet Aveo (674), VW Passat (652), Buick Lucerne (621), Kia
Forte (582), Buick Regal (576), Hyundai Tucson (564), Kia Sportage (550),
Kia Spectra (548), Subaru Legacy (538), Lincoln MKZ (501).

## 14. Gap-block rows bounded per generation (2026-11-04, owner go-ahead)

**Why.** The part finder (`docs/app.js` ~5926) treats a row's "fits" range
as the same-generation donor window. `_apply_generation_bounds` skips
names containing pump/compressor/motor (`_GEN_MECH_EXCLUDE_RE`) and names it
does not consider sensitive (fans, throttle bodies, AWD units, crossbars),
so 56 rows from the §1–12 blocks shipped spans across generations (e.g.
Camry fuel pump "2002–2017", Malibu "2004–2024"). That made a false
cross-generation fitment claim.

**Change.** Gap-block calls go through `_gap_extend`, which registers each
row object, holding a reference so ids are not reused. `_bound_gap_rows_per_generation()`
runs after `_apply_generation_bounds` and splits any registered row that
crosses a `GENERATION_BREAKS` break (every gap model has breaks; no
PARTS_GAPS notes were needed). Rows from outside the gap blocks are not
touched.

**Rows split (56 → 153 per-generation rows):** fuel pump, A/C compressor,
radiator fan on Altima (with throttle body), Camry, Corolla, CR-V, Elantra,
Equinox, Escape, Focus, Malibu, RAV4, Rogue, Sentra; sunroof rows on Camry,
Corolla, CR-V, Elantra, Equinox, Malibu, RAV4, Rogue, Sentra; AWD rear units
on CR-V, Equinox, RAV4, Rogue; roof-rack crossbars on Escape, RAV4, Rogue;
side mirrors on Equinox and Focus; Malibu remote-start BCM. Civic, Explorer
2011–19, the §12 enthusiast rows and the §13 rows already sat inside one
generation.

**Checks.**
- Bands, costs and gates are identical on every piece, and the pieces
  exactly cover the original span.
- Whole-table diff against the previous commit: only those 56 rows changed.
- All 12,740 distinct year/make/model combinations on the lots match
  identical part names, gate statuses and bands before and after; only
  "fits" moved.
- Coverage did not drop: no entry 12,298 (3.7%) and generic-only 35,451
  (10.6%), both unchanged.
- New tests: no registered row crosses a break; the registry holds only
  gap-block entries; spot checks on Camry, Malibu, Altima and Equinox; the
  shared alternator row is untouched.

**Out of scope, still crossing:** 776 rows on 196 entries outside the gap
blocks. These are mostly the shared standard rows (alternator, starter,
climate panel, window regulator and switch, control module, mirrors) plus
some power liftgate/sliding-door motors and tow mirrors. Not changed here:
owner decision whether those get the same treatment.

## 15. Every row bounded per generation (2026-11-04, owner: "go on the 776 rows")

**Scope.** The 776 rows outside the gap blocks whose "fits" span crossed a
`GENERATION_BREAKS` break (196 entries): mostly the shared standard rows
(alternator, starter, climate panel, window regulator and switch, control
module, mirrors), plus overlay rows (e.g. Elantra 2005–10 lamps across the
2007 break, Camry JBL 2002–14), liftgate/sliding-door motors, tow mirrors,
and platform-family rows.

**Change.** `_bound_gap_rows_per_generation` became `_bound_rows_per_generation`.
It now applies to every row on a `GENERATION_BREAKS` model and runs once,
right after `_apply_platform_families` (the overlay merge and the platform
copies are the last steps that add rows). Each crossing row becomes one row
per generation; bands, costs, gates and `sharedWith` carry over; nothing is
dropped. The §14 gap-block registry is still recorded.

**Ordering matters, caught in testing.** A first version ran the pass before
the platform families. The families locate each member's row by name and
best year overlap, so their interchange note landed on one generation piece
only. Per-car comparison showed 200 car/part notes lost, e.g. 2008–11 Escape
mirrors losing "Tribute/Mariner share doors", 2002–03 Camry alternators the
1MZ note, and the Yukon Autoride note. Running after the families fixed it.

**Checks.**
- Table: 5,079 → 6,649 rows; the 776 crossing rows became 2,346 pieces with
  identical fields that exactly cover the original years. No row on a
  `GENERATION_BREAKS` model crosses a break now.
- Lots: all 12,740 distinct year/make/model combinations match identical
  part names, gate statuses and bands, and identical `sharedWith` notes, as
  before. Only "fits" changed.
- Coverage unchanged: no entry 12,298 (3.7%), generic-only 35,451 (10.6%).
- `test_interchange.py`, `test_consensus_parts.py`, `test_vpic_fixes.py` and
  the other offline scraper tests pass; the platform/trim/generation/engine
  lints are clean.
- `test_parts_gaps.py`: three checks asserted the old cross-generation
  spans (Elantra overlay lamps "2005–2010", Camry JBL "2002–2014", and the
  §14 "alternator untouched" check). Each now asserts the per-generation
  span and keeps its intent. New checks: no row on any `GENERATION_BREAKS`
  model crosses a break, and interchange notes survive the split.

Models not in `GENERATION_BREAKS` are unchanged (no break data to bound by).

## 16. Next measured block (2026-11-04, owner: "start the next parts block")

Same basis and measurement as §13. Every row is bounded to one generation
(or facelift window where the notes give one), and §15's pass guarantees
no row crosses a `GENERATION_BREAKS` year. Before: generic-only 35,451
cars (10.6%), no entry 12,298 (3.7%).

| Order | Model (years) | Generic-only cars |
|---|---|---|
| 1 | Ford Focus 2000–07 | 1,535 |
| 2 | Ford Explorer 1991–2001 | 1,173 |
| 3 | Jeep Compass 2007–16 | 911 |
| 4 | Kia Rio 2001–23 | 781 |
| 5 | Buick Century 1983–2005 | 704 |
| 6 | Chevrolet Aveo 2004–11 | 674 |
| 7 | VW Passat 1998–2011 | 652 |
| 8 | Buick Lucerne 2006–11 | 621 |

New pull-cost medians (30 lists): transfer case $83, shock/strut $13,
amplifier $24, rear differential $36. The rows below reuse the audited
templates; these medians are recorded for the categories they touch.

### 16.1 Ford Focus 2000–2007 (C170)

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 2000–04, 2005–07 | — | Every car. Split at the 2005 facelift, which also changed the engine (Zetec → Duratec 2.0). |
| A/C compressor | 2000–04, 2005–07 | option | A/C was optional on the early base cars. |
| Sunroof | 2000–04, 2005–07 | option | |
| SVT front seats (pair), SVT 17" wheels | 2002–04 | trim: SVT | SVT Focus run. Seat band matches the audited leather-seat pair rows. |

Windows follow the repo's own Focus platform notes (00–04 housings, HVAC
and switchgear shared). Left out, no stated basis: ZX3/ZX5 hatch and wagon
lamps (whether the rear lamps changed in 2005 is not confirmed), Audiophile
audio. The existing 2000–07 lamp rows were left as they are; they cross the
2005 facelift, which is not a `GENERATION_BREAKS` year.

Result: Focus 2000–07 generic-only 1,535 → 0. Lots: generic-only 35,451
(10.6%) → 33,916 (10.2%).

### 16.2 Ford Explorer 1991–2001 (1991–94, 1995–2001)

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module | 1991–94, 1995–01 | — | In-tank on every truck. |
| A/C compressor | 1991–94, 1995–01 | option | Not confirmed standard on base XL trucks. |
| Transfer case shift motor | 1991–94, 1995–01 | drive: 4wd/awd | Electric-shift 4x4 and the 1996+ AWD; a RWD decode excludes it. Same band as the Grand Cherokee row. |
| Leather power driver seat (Eddie Bauer/Limited), sunroof, alloy wheels | 1991–94, 1995–01 | option | |

Left out, no stated basis: a radiator-fan row (these trucks use an
engine-driven clutch fan, not the electric assembly the row describes), the
transfer case itself (a drivetrain gearbox, kept out with transmissions),
Mach audio (offer years not confirmed), 2-door Sport body parts.

Result: Explorer 1991–2001 generic-only 1,173 → 0. Lots: generic-only
33,916 (10.2%) → 32,743 (9.8%).

### 16.3 Jeep Compass 2007–2016 (MK49)

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 2007–16 | — | One generation; mechanicals carried through the facelift. |
| A/C compressor | 2007–16 | option | Standard fitment on the base car not confirmed. |
| AWD rear differential / transfer unit | 2007–16 | drive: awd/4wd | Freedom Drive cars; same band as the Equinox row. |
| Tail lights, side mirrors (pair) | 2007–10, 2011–16 | — | The entry had neither; split at the 2011 facelift. The mirror row does not claim power mirrors. |
| Sunroof, leather power seat (Limited), alloy wheels | 2007–16 | option | |

Left out, no stated basis: Boston Acoustics audio (offer by year not
confirmed), the CVT (transmission). The existing headlight row spans
2007–16 across the 2011 facelift, which changed the front end. It is not a
`GENERATION_BREAKS` year, so the row was left as is and is flagged here.

Result: Compass generic-only 911 → 0. Lots: generic-only 32,743 (9.8%) →
31,832 (9.5%).

### 16.4 Kia Rio 2001–2017 (DC 2001–05, JB 2006–11, UB 2012–17)

The JB and UB share their platforms with the MC and RB Accent, so the rows
follow §13.2.

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan, tail lights | 2001–05, 2006–11, 2012–17 | — | Every car; the entry had no tail-light row. |
| A/C compressor | 2001–05, 2006–11 | option | Optional on base cars. |
| A/C compressor | 2012–17 | — | Standard on the UB. |
| Hatchback tail lights | 2006–11, 2012–17 | body: hatchback | Rio5 / 5-door lamps differ from the sedan's. |
| Sunroof, alloy wheels | 2006–11, 2012–17 | option | SX/EX options. |

Left out, no stated basis: 2001–05 Rio Cinco wagon lamps, sunroof and
wheels; 2018+ (YB, 30 cars, not in this block).

Result: Rio generic-only 781 → 30 (all 2018+). Lots: generic-only 31,832
(9.5%) → 31,081 (9.3%).

### 16.5 Buick Century 1986–2005 (A-body to 1996, W-body 1997–2005)

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 1986–96, 1997–05 | — | Every fuel-injected car; the FWD A-body has an electric fan. |
| A/C compressor | 1986–96 | option | Standard fitment not confirmed on base A-bodies. |
| A/C compressor | 1997–05 | — | Standard on the W-body. |
| Side mirrors (pair) | 1997–05 | — | The entry had none. |
| Leather power driver seat (Limited), alloy wheels | 1997–05 | option | |

Left out, no stated basis: 1982–85 cars (carbureted engines had an
engine-mounted mechanical pump; 3 cars stay generic-only), sunroof (offer
not confirmed), the 3.1 V6 intake gaskets/manifold (engine).

Result: Century generic-only 704 → 3 (pre-1986). Lots: generic-only 31,081
(9.3%) → 30,380 (9.1%).

### 16.6 Chevrolet Aveo 2004–2011 (new `GENERATION_BREAKS`: 2007, 2009)

The Aveo had no breaks on record. The T200 ran 2004–06; the T250 sedan
arrived for 2007 while the hatch stayed T200 through 2008, and the Aveo5 was
restyled for 2009. Both years are now breaks, so no window mixes T200 and
T250 cars of one body. This also bounds the existing Aveo rows, e.g. the
headlight row is now 2004–06 / 2007–08 / 2009–11 instead of 2004–11 (§15
pass).

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 2004–06, 2007–08, 2009–11 | — | Every car. |
| A/C compressor | same | option | A/C was optional on the base cars. |
| Sunroof | same | option | |

Left out, no stated basis: tail lights and mirrors (2007–08 sedan and
hatch lamps are from different generations, and the rows carry no body
gate that could separate them confidently), Aveo5 hatch-specific rows.

Result: Aveo generic-only 674 → 0. Lots: generic-only 30,380 (9.1%) →
29,706 (8.9%).

### 16.7 VW Passat 1998–2011 (B5/B5.5 1998–2005, B6 2006–11)

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 1998–05, 2006–11 | — | Every car. |
| 4Motion rear differential | 1998–05, 2006–11 | drive: awd/4wd | 4Motion cars only; band matches the audited Audi quattro/Haldex rear-diff row; cost is the rear-differential median ($36). |
| Monsoon amp + speakers | 1998–05 | option | B5 premium-audio option; cost is the amplifier median ($24). |
| Sunroof, leather power seat (GLX), alloy wheels | 1998–05, 2006–11 | option | |

Left out, no stated basis: tail lights and headlights for 1998–2005 (the
B5.5 refresh changed them mid-2001, and 2001 is split across both), W8
parts, Dynaudio on the B6 (offer years not confirmed), coil packs (cheap
new), the DSG/Tiptronic units (transmissions).

Result: Passat generic-only 652 → 0. Lots: generic-only 29,706 (8.9%) →
29,054 (8.7%).

### 16.8 Buick Lucerne 2006–2011 (one generation)

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 2006–11 | — | Every car. |
| Tail lights (pair) | 2006–11 | — | The entry had none. |
| Sunroof, leather heated seats (CXL/CXS), Harman Kardon audio, 17"/18" wheels | 2006–11 | option | |

Left out, no stated basis: CXS Magnetic Ride shocks. The only audited band
for that category is the CTS-V's ($300–700 a pair), which is not a fair
anchor for a Lucerne. Also the Northstar V8 (engine).

Result: Lucerne generic-only 621 → 0. Lots: generic-only 29,054 (8.7%) →
28,433 (8.5%).

### 16.9 Block totals

Generic-only **35,451 (10.6%) → 28,433 (8.5%)**: 7,018 cars moved to
model-specific rows. No entry unchanged at 12,298 (3.7%). Compared with the
commit before §16, none of the 12,740 distinct year/make/model combinations
on the lots lost a part or had an existing part's band or gate status
change. `test_interchange.py`, `test_consensus_parts.py` and the other
offline scraper tests pass. Leftovers in these models: Rio 2018+ (30),
Century pre-1986 (3).

## 17. Facelift bounds for appearance rows (2026-11-04, owner: "go on facelifts")

**Rule.** `FACELIFT_BREAKS` lists the first US model year of each mid-cycle
facelift that restyled the exterior. The §15 pass (run after
`_apply_platform_families`) cuts appearance rows, those matching
`_FACELIFT_SENSITIVE_RE` (headlights, tail lights, grille, bumpers,
fog/marker/corner lights), at those years as well as at the generation
breaks. Mechanical and interior rows are not cut at facelifts. A cut
applies to every appearance row on the model even where a source does not
say that particular lamp changed: splitting only narrows a "fits" window,
so it cannot create a false fitment claim; leaving a span across a
facelift could.

**Sources.** Researched 2026-11-04, mostly Wikipedia model pages
(en.wikipedia.org/wiki/<model page>), corroborated by manufacturer press
material where noted. Quotes were read through a summarising fetch tool;
spot-check one against the page before relying on it for fitment.

| Model | Facelift MY | Basis |
|---|---|---|
| Nissan Altima | 2005, 2010, 2016 | L31 "new front grille, all-red taillights"; L32 2010 "new front fascia, hood, and headlights"; L33 2016 "new front and rear bumpers, headlamps, and taillights" (Nissan_Altima) |
| Toyota Camry | 2000, 2005, 2010, 2015 | XV20 "mid-model upgrade to the front and rear fascias"; XV30 "new headlight and taillight designs, redesigned front bumper"; XV40 "updated front fascia, including grille and bumper"; XV50 near-total reskin (Wikipedia per generation; pressroom.toyota.com 2014 NYIAS reveal) |
| Ford Focus | 2005, 2015 | C170 "a new front bumper facia", "new tail lamps"; 2015 refresh "thinner and sharper headlights, a new trapezoidal grille". **2008–11: no facelift found.** |
| Chevrolet Malibu | 2006, 2014, 2019 | 2006 "front fascia removing the chrome bar in favor of a smaller rectangular grille"; 2014 front restyle (Autoblog: headlamps carried over); 2019 "new larger front grille". **2008–12: no facelift.** |
| Honda Accord | 2006, 2011 | hondanews.com 2006: "new front and rear styling with new bumper fascias, front grille"; 2011 "new front fascias and updated tail lamps" (sedan and coupe) |
| Ford Fusion | 2010, 2017, 2019 | 2010 "revised front and rear end fascias"; 2017 "new front and rear end styling"; 2019 "updated front and rear styling" |
| Ford Escape | 2005, 2017 | 2005 "a redesigned front bumper" plus press "new grille and quad headlamps"; 2017 "reshaped LED taillights", new grille |
| Ford F-150 | 2013 | "a new 2011+ Super Duty–styled grille" (twelfth generation page) |
| Chevrolet Cruze | 2015 | US 2015 refresh (new front fascia/headlamps). The 2013 facelift was other markets only, so it is not used. |
| Hyundai Sonata | 2014, 2018 | YF "facelift in late 2013, for the 2014 model year"; LF 2018 "new headlights, tail lights, cascading grille" |
| Nissan Sentra | 2010, 2016 | B16 2010 "Altima-inspired grille", front bumper; B17 2016 "new front and rear bumpers, lights" |
| Chevrolet Equinox | 2016 | "a new grille, headlights, wheels, and front fascia, as well as reworked tail lights" |
| Toyota Corolla | 2005, 2011, 2017 | E120 2005 "revised front bumper and grille"; E140 2011 grille, headlights, bumpers, rear lamps; E170 2017 "new headlight design", "redesigned taillights" |
| Hyundai Elantra | 2014, 2019 | MD 2014 "new front and rear styling with tinted tail lights"; AD 2019 new headlights and "redesigned tail lights" |
| Ford Explorer | 2016, 2018 | 2016 "redesigned front fascia, hood, and lower bumper", "restyled LED tail lamps"; 2018 front fascia and fog-light update |
| Ford Taurus | 2013 | "revised hood, front and rear fascias", "restyled headlamps", LED taillights |
| VW Jetta | 2015 | A6 2015 updates incl. front and rear styling |
| Nissan Versa | 2015 | sedan: "redesigned tail lights and larger headlights". The Versa Note's year is unconfirmed; the cut also applies to it, which can only narrow its windows. |
| Nissan Rogue | 2011, 2017 | S35 2011 "new front fascia and grille"; T32 2017 "restyled headlights and tail lights" |
| Honda Civic | 2004, 2009 | 7th gen 2004 "new headlights, bumper, and grille"; 8th gen 2009 "front bumper and grille were restyled" |
| Jeep Compass | 2011 | Stellantis media release: "new fascia, new headlamps and a new grille ... new rear fascia ... new LED taillamps" |
| Chevrolet Impala | 2012 | "the exterior received a slight refresh"; new grille (cars.com) |
| Kia Optima | 2014, 2019 | kiamedia.com 2014: "updated front and rear fascias"; 2019 US refresh (secondary press for part detail) |
| Mazda3 | 2012, 2017 | 2012 "revised grille and air intakes ... rear valance"; 2017 "new front and rear exterior styling" |

**Left out (no confirmed facelift, or not yet researched):** Focus
2008–11 and Malibu 2008–12 (none found); the Versa Note's own facelift
year and the Elantra coupe (unconfirmed). Every other `GENERATION_BREAKS`
model is not researched yet and is left as is. The top remaining by cars:
Grand Caravan, Odyssey, Expedition, Town & Country, Silverado, Ram, BMW 3,
Maxima, Ranger, Suburban, Traverse, Pathfinder.

**Checks.**
- 75 appearance rows became 152 facelift-bounded pieces, with identical
  fields that exactly cover the original years. No mechanical or interior
  row was touched.
- On the current lots (332,883 cars after today's scan), every distinct
  year/make/model matches identical part names, gate statuses, bands and
  `sharedWith` notes before and after. Coverage is therefore unchanged:
  generic-only 28,395 (8.5%), no entry 12,291 (3.7%).
- `test_interchange.py`, `test_consensus_parts.py` and the other offline
  scraper tests pass. Two `test_parts_gaps.py` checks asserted spans that
  crossed a facelift (Equinox tail lights 2010–17, Elantra headlights
  2011–16); they now assert the facelift-bounded windows.
- New checks: no facelift-sensitive row crosses a listed facelift year;
  every table key is a real entry; Focus/Compass spot checks; a mechanical
  row (Compass fuel pump) is not cut.

## 18. Next measured block (2026-11-04, owner: "start the next parts block")

Same basis as §13/§16. Rows stay inside one generation, and appearance rows
inside one facelift window (§15/§17 pass). Generations, facelifts and the
per-model fitment questions were researched first. Sources are cited per
model; "fetched" means the page was read, while "snippet" (weaker) means
only a search-result summary was available. Before: generic-only 28,344
(8.5%) of 332,476 cars, no entry 12,301 (3.7%).

| Order | Model | Generic-only cars |
|---|---|---|
| 1 | Kia Forte 2010–13 | 582 |
| 2 | Buick Regal (1988–2019) | 574 |
| 3 | Hyundai Tucson 2005–23 | 562 |
| 4 | Kia Sportage 2005–23 | 546 |
| 5 | Kia Spectra 2001–09 | 545 |
| 6 | Subaru Legacy 1995–2004, 2013–14 | 528 |
| 7 | Lincoln MKZ 2007–20 | 507 |
| 8 | Hyundai Elantra 2001–06 | 498 |

### 18.1 Kia Forte 2010–2013 (TD)

Basis: en.wikipedia.org/wiki/Kia_Forte and consumerguide.com/used/2010-13-kia-forte
(fetched). No US facelift: 2012 changed only the Koup door handles and 2013
only wheels and LED DRLs; the 2012–13 restyle seen in search results is
China-market.

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan, tail lights | 2010–13 | — | Every car; the entry had no tail-light row. |
| A/C compressor | 2010–11 | option | A/C was in the LX Convenience Package for 2010–11 (Consumer Guide). |
| A/C compressor | 2012–13 | — | Standard from 2012. |
| Koup tail lights | 2010–13 | body: coupe | A separate part number from the sedan's (Kia parts catalog via kiapartsnow; snippet). Same band as the Altima coupe row. |
| Sunroof, alloy wheels | 2010–13 | option | Sunroof optional on EX/SX (Consumer Guide). |

Left out, no stated basis: 5-door hatch-specific lamps (no source says they
differ from the sedan's).

Result: Forte generic-only 582 → 0. Lots: generic-only 28,344 (8.5%) →
27,762 (8.4%).

### 18.2 Buick Regal 1997–2004 (W-body), 2011–2017 (5th gen)

Basis: en.wikipedia.org/wiki/Buick_Regal; cars.com "2014 Buick Regal: What's
New" and "2003 Buick Regal: What's New" (fetched).
- **Facelift 2014 (added to `FACELIFT_BREAKS`):** "New grille styling",
  "Available xenon high-intensity-discharge headlights and LED daytime
  running lights", "LED taillights … new elements that extend into the
  trunklid" (cars.com). The existing Regal lamp rows are now cut at 2014
  as well.
- **No W-body facelift found:** 2003 brought "two new body colors". The
  2003 grille and fascia change belongs to the Century.
- **AWD:** 2014–17 only, with the 2.0T and 6-speed automatic (Wikipedia).

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 1997–04, 2011–17 | — | Every car; A/C as on the W-body Century (§16.5). |
| Tail lights | 1997–04, 2011–13, 2014–17 | — | The entry had none; cut at the 2014 facelift. |
| AWD rear differential / transfer unit | 2014–17 | drive: awd/4wd | Same band as the Equinox row. |
| Leather power driver seat (LS/GS) | 1997–04 | option | |
| Sunroof, leather heated seats | 2011–17 | option | |
| Alloy wheels | 1997–04, 2011–17 | option | |

Left out, no stated basis: the GS supercharger (engine), GS-specific seats
and wheels, and 1988–96 cars (about 70; not researched in this block).

Result: Regal 1997–2017 generic-only 507 → 0 (the remaining 67 are
1988–96 and 2018–19). Lots: generic-only 27,762 (8.4%) → 27,255 (8.2%).

### 18.3 Hyundai Tucson 2005–2021 (JM 2005–09, LM 2010–15, TL 2016–21)

Basis: en.wikipedia.org/wiki/Hyundai_Tucson; consumerguide.com/used/2005-09-hyundai-tucson;
cars.com 2005 "What's New", 2014 "What's Changed", 2019 "What's New"
(all fetched).
- **Facelifts added to `FACELIFT_BREAKS`:**
  - 2009: "slightly freshened exterior styling" (Consumer Guide, no part
    detail; the cut is conservative).
  - 2014: "new projector-type headlights with LED accents and LED
    taillights" (cars.com); in North America only the lamps changed.
  - 2019: "cascading grille", "slightly restyled" bumpers, "revised
    headlight and taillight designs" (cars.com).
- **AWD:** offered on all three generations.
- **A/C:** standard on the 2005 GL (Consumer Guide and cars.com).

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 2005–09, 2010–15, 2016–21 | — | Every car. |
| A/C compressor | 2005–09 | — | Standard per the sources. |
| A/C compressor | 2010–15, 2016–21 | option | Standard fitment not confirmed by a source. |
| AWD rear differential / coupling | 2005–09, 2010–15, 2016–21 | drive: awd/4wd | Same band as the Rogue/RAV4 rows. |

Left out, no stated basis: sunroof, leather and wheel rows (option
availability not researched).

Result: Tucson 2005–21 generic-only 558 → 0 (4 cars from 2022–23 remain).
Lots: generic-only 27,255 (8.2%) → 26,697 (8.0%).

### 18.4 Kia Sportage 2005–2022 (KM 2005–10, SL 2011–16, QL 2017–22)

Basis: en.wikipedia.org/wiki/Kia_Sportage; kbb.com/kia/sportage/2009;
autotrader.ca/research/kia/sportage/2014; carscoops.com 2019/02 "2020 Kia
Sportage gets refreshed looks" (fetched).
- **Facelifts added to `FACELIFT_BREAKS`:**
  - 2009: "a new grille and headlamp treatment, color keyed front and rear
    bumpers" (KBB).
  - 2014: "a new front grille", new HID and LED-tail options (autotrader.ca).
  - 2020: "redesigned headlights and bumpers" (Wikipedia), "new front and
    rear fascias" (Carscoops).
- **Lamp rows re-cut:** the existing tail-light and LED-headlight rows are
  now cut at those years (e.g. tail lights 2005–08 / 2009–10).
- **AWD/4WD:** offered on all three generations.
- **Panoramic sunroof:** an SL EX option (cars.com and others; snippets).

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 2005–10, 2011–16, 2017–22 | — | Every car. |
| A/C compressor | same | option | Standard fitment not confirmed by a source. |
| AWD rear differential / coupling | same | drive: awd/4wd | |
| Panoramic sunroof assembly | 2011–16 | option | Same band as the Soul row. |

Left out, no stated basis: KM/QL sunroofs, leather, wheels (not
researched).

Result: Sportage 2005–22 generic-only 543 → 0 (3 cars from 2023 remain).
Lots: generic-only 26,697 (8.0%) → 26,154 (7.9%).

### 18.5 Kia Spectra 2000–2003, 2005–2009

Basis: en.wikipedia.org/wiki/Kia_Spectra; consumerguide.com/used/2005-09-kia-spectra;
cars.com "2007 Kia Spectra: What's New" (fetched).
- **Generations:** gen 1 is Sephia-based and runs to early 2004. The LD
  went on sale in spring 2004 as a "2004.5", i.e. still a 2004 model, and
  ran through 2009. With two generations under one model year, 2004 cars
  get no new rows (35 stay generic-only).
- **Facelift 2007 (added to `FACELIFT_BREAKS`):** "updated front and rear
  styling — including the grille, bumper, lights and deck lid"; "the
  Spectra5 received similar styling changes for 2007" (cars.com).
- **Spectra5 hatch:** 2005–09 (Consumer Guide).

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 2000–03, 2005–09 | — | Every car. |
| A/C compressor | 2000–03, 2005–09 | option | Standard fitment not confirmed by a source. |
| Tail lights | 2005–06, 2007–09 | — | The entry had none; cut at the facelift. |
| Hatchback tail lights | 2005–06, 2007–09 | body: hatchback | Spectra5 rear lamps; same band as the Accent/Rio hatch rows. |

Left out, no stated basis: gen-1 tail lights (sedan vs 5-door differ and
the 2001 "slight facelift" has no part detail), sunroof, wheels.

Result: Spectra generic-only 545 → 35 (all 2004). Lots: generic-only 26,154
(7.9%) → 25,644 (7.7%).
