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

### 18.6 Subaru Legacy 1995–2004, 2010–2014

Basis: en.wikipedia.org/wiki/Subaru_Legacy; Consumer Guide used reviews
1995–99, 2000–04, 2010–14; autoblog.com 2012/04/04 "Subaru tweaks Legacy and
Outback for 2013" (fetched).
- **Facelifts added to `FACELIFT_BREAKS`:**
  - 2003: "revisions to suspension and front styling" (Consumer Guide); new
    grille and front fascia (cars.com, snippet).
  - 2013: "new front-end styling with a redesigned grille, bumper, and
    headlights" (Consumer Guide).
- **No facelift found for 1995–99:** "no major change for '98".
- **AWD:** standard 2000–04 and 2010–14. In 1995 the base and L were FWD,
  and in 1996 FWD remained only on the L; the whole line was AWD from 1997
  (Consumer Guide). Wikipedia instead says standard from 1996.

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 1995–99, 2000–04, 2010–14 | — | Every car. |
| A/C compressor | same | option | Standard fitment not confirmed by a source. |
| Rear differential (match final-drive ratio) | 1995–99 | drive: awd/4wd | FWD cars existed in 1995–96. Cost is the rear-diff median ($36); the band is conservative for an open/viscous rear. |
| Rear differential (match final-drive ratio) | 2000–04, 2010–14 | — | AWD standard. |

Left out, no stated basis: tail lights (sedan vs wagon lamps differ, with
no body split researched), sunroof, leather, wheels. How the Outback is
named on US titles in these years is unconfirmed, so no Outback routing
was changed.

Result: Legacy generic-only 528 → 0. Lots: generic-only 25,644 (7.7%) →
25,116 (7.6%).

### 18.7 Lincoln MKZ 2007–2020 (1st gen 2007–12, 2nd gen 2013–20)

Basis: en.wikipedia.org/wiki/Lincoln_MKZ; jalopnik.com "2010 Lincoln MKZ";
autoblog.com "2017 Lincoln MKZ" (LA 2015); cars.com "2017 Lincoln MKZ first
look" (fetched).
- **New `GENERATION_BREAKS` "mkz": [2013]:** the entry had no breaks.
- **Facelifts added to `FACELIFT_BREAKS`:**
  - 2010: "the split-wing grille and thinner wraparound head lamps", "LED
    taillamps" (Jalopnik).
  - 2017: "the all-new one-piece Lincoln signature grille", adaptive LED
    headlamps (Autoblog).
- **Lamp rows re-cut:** the existing MKZ headlight, tail-light and mirror
  rows are now bounded by generation, and the lamps also by facelift.
- **AWD:** optional with the 3.5 V6 from 2007, and on the 2nd gen with the
  2.0T, 3.7 and 3.0TT. Hybrids were FWD.

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 2007–12, 2013–20 | — | Every car. |
| A/C compressor | same | option | Standard fitment not confirmed by a source (conservative). |
| AWD rear differential / transfer unit | same | drive: awd/4wd | |

Left out, no stated basis: THX/Revel audio, panoramic roof, seats and
wheels (not researched), the hybrid battery (years known, but no audited
band for this car), the 2006 Zephyr.

Result: MKZ generic-only 507 → 0. Lots: generic-only 25,116 (7.6%) →
24,609 (7.4%).

### 18.8 Hyundai Elantra 2001–2006 (XD)

Basis: en.wikipedia.org/wiki/Hyundai_Elantra; consumerguide.com/used/2001-06-hyundai-elantra
(fetched).
- **Facelift 2004 (added to `FACELIFT_BREAKS`):** "Elantra gets a new
  grille, taillights, interior console, and interior controls for 2004"
  (Consumer Guide); new headlights and bumpers (Wikipedia, XD2).
- **A/C:** standard on US cars ("all American market models came with …
  air conditioning").
- **GT 5-door hatch:** 2002–06 ("joined the sedan during the 2001 model
  year", sold as a 2002 model).

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 2001–06 | — | Every car. |
| Headlights, tail lights | 2001–03, 2004 | — | The entry had no lamp rows before 2005; cut at the 2004 facelift. They stop at 2004 because the overlay's lamp rows start at 2005, and an overlapping same-name base row would make the window-aware merge skip them. |
| Hatchback tail lights | 2002–03, 2004–06 | body: hatchback | GT hatch rear lamps. |

Left out, no stated basis: sunroof, wheels and GT-specific rows (not
researched).

Result: Elantra 2001–06 generic-only 498 → 0. Lots: generic-only 24,609
(7.4%) → 24,111 (7.3%).

### 18.9 Block totals

Generic-only **28,344 (8.5%) → 24,111 (7.3%)**: 4,233 cars moved. No entry
unchanged at 12,301 (3.7%).
- **New `GENERATION_BREAKS`:** mkz 2013.
- **New `FACELIFT_BREAKS`:** regal 2014; tucson 2009/2014/2019; sportage
  2009/2014/2020; spectra 2007; legacy 2003/2013; mkz 2010/2017; elantra
  2004.
- **Compared with the commit before §18:** none of the 12,726 distinct
  year/make/model combinations on the lots lost a part or had an existing
  part's band or gate status change, and `sharedWith` notes are identical.
- **Tests:** `test_interchange.py`, `test_consensus_parts.py` and the
  other offline scraper tests pass.

Leftovers in these models: Regal 1988–96 and 2018–19 (67), Spectra 2004
(35), Tucson 2022–23 (4), Sportage 2023 (3).

## 19. Next measured block (2026-11-04, owner: "start the next parts block")

Same basis and method as §18: generations and facelifts were researched
first with cited sources. FETCHED means the page was read (Wikipedia via
raw wikitext, Consumer Guide used reviews, cars.com "What's New",
manufacturer releases); SNIPPET means search text only. Before:
generic-only 24,111 (7.3%) of 332,476 cars, no entry 12,301 (3.7%).

| Order | Model | Generic-only cars |
|---|---|---|
| 1 | Mitsubishi Galant 1999–2012 | 493 |
| 2 | Pontiac Grand Am 1996–2005 | 486 |
| 3 | Kia Sorento 2003–09 | 463 |
| 4 | Hyundai Santa Fe 2001–06 | 414 |
| 5 | Lincoln MKX 2007–18 | 413 |
| 6 | Ford Five Hundred 2005–07 | 409 |
| 7 | Kia Optima 2001–10 | 396 |
| 8 | VW CC 2009–17 | 396 |

### 19.1 Mitsubishi Galant 1999–2003, 2004–2012

Basis: en.wikipedia.org/wiki/Mitsubishi_Galant; consumerguide.com/used/1999-03-mitsubishi-galant
and /used/2004-12-mitsubishi-galant; cars.com "What's New" 2002, 2007, 2009;
auto123 2009 launch (all fetched).
- **Facelifts added to `FACELIFT_BREAKS`:**
  - 2002: "revised front and rear styling" (CG); "a new grille", "New aero
    bumpers and fresh taillights" (cars.com).
  - 2007: "revised nose and tail appearance" (CG); "front and rear fascias
    include a single-piece grille" (cars.com).
  - 2009: "freshened styling" (CG); "new grille, taillights … a new bumper
    in back" (auto123).
- **Lamp rows re-cut:** the existing Galant headlight and tail-light rows
  are now cut at those years.
- **A/C:** standard on the DE (1999–2008) and the ES (2009–12) per CG
  equipment lists.

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 1999–03, 2004–12 | — | Every car. |
| Sunroof | 1999–03, 2004–12 | option | Optional or standard by trim and year per CG (ES/LS/GTS/SE/Ralliart). |

Left out, no stated basis: Ralliart-specific rows (2007–09; trim parts not
researched), seats and wheels.

Result: Galant generic-only 493 → 0. Lots: generic-only 24,111 (7.3%) →
23,618 (7.1%).

### 19.2 Pontiac Grand Am 1996–1998, 1999–2005

Basis: en.wikipedia.org/wiki/Pontiac_Grand_Am; consumerguide.com/used/1992-98-pontiac-grand-am
and /used/1999-05-pontiac-grand-am; gmpartsgiant.com Grand Am tail-light
catalog (fetched; a dealer catalog, so check the part number against the
VIN).
- **Facelifts:** the 4th gen's 1996 facelift is the entry's first year, so
  no cut is needed. No 5th-gen facelift was found: the only changes were
  wheels (2001) and sedan cladding (2003).
- **A/C:** CG says A/C was added to "the standard equipment list of all
  models" for 1997, and lists it standard on the SE in 2000–04. The 1999
  and 2005 lists were not available.
- **Tail lamps:** 1999–2005 lamps are split by trim (SE 22612876/77 vs GT
  22612878/79), each shared by coupe and sedan. The 1996–98 lamps are one
  part across GT and SE.

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 1996–98, 1999–05 | — | Every car. |
| A/C compressor | 1997–98, 2000–04 | — | Standard per CG. |
| A/C compressor | 1996, 1999, 2005 | option | Standard not confirmed for those years. |
| GT tail lights | 1999–05 | trim: GT | Separate GT part numbers; same band as the other trim/body lamp rows. |

Left out, no stated basis: sunroof, wheels and GT seats (not researched),
the 3.4 V6 intake gaskets (engine).

Result: Grand Am generic-only 486 → 0. Lots: generic-only 23,618 (7.1%) →
23,132 (7.0%).

### 19.3 Kia Sorento 2003–2009 (BL)

Basis: en.wikipedia.org/wiki/Kia_Sorento; consumerguide.com/used/2003-09-kia-sorento;
autotrader.ca/research/kia/sorento/2007; cars.com "What's New" 2007 and 2009
(fetched).
- **Facelift 2007 (added to `FACELIFT_BREAKS`):** "a new grille, front and
  rear bumpers, head- and taillamps" (autotrader.ca); "Projector beam
  headlamps were added, along with new tail lamps" (Wikipedia).
- **2009 not used:** CG says "slightly freshened", while cars.com says "no
  significant changes". The sources disagree, so there is no cut.
- **A/C:** standard on the LX 2003–07. The 2007 Base had it as an option,
  and it was standard again from 2008. The row is plain 2003–06 and
  option-flagged 2007–09.
- **Sunroof:** standard on the EX 2003–06, optional from 2007.

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 2003–09 | — | Every truck. |
| A/C compressor | 2003–06 | — | Standard. |
| A/C compressor | 2007–09 | option | Optional on the 2007 Base. |
| Tail lights | 2003–06, 2007–09 | — | The entry had none; cut at the facelift. |
| Sunroof | 2003–09 | option | |

Left out, no stated basis: 4WD rows. Part-time 4WD and full-time
Torque-on-Demand were both offered, but the sources disagree on trims, and
no part-level basis was found for a shift motor or transfer unit.

Result: Sorento 2003–09 generic-only 463 → 0. Lots: generic-only 23,132
(7.0%) → 22,669 (6.8%).

### 19.4 Hyundai Santa Fe 2001–2006 (SM)

Basis: en.wikipedia.org/wiki/Hyundai_Santa_Fe; consumerguide.com/used/2001-06-hyundai-santa-fe;
cars.com "2005 Hyundai Santa Fe: What's New" (fetched).
- **Facelift 2005 (added to `FACELIFT_BREAKS`):** "Changes were made to the
  grille, tail lights, rear bumper" (Wikipedia); "new grille and
  taillights" (cars.com).
- **A/C:** standard (CG).
- **AWD:** offered on the V6 models (GL V6/GLS/LX in 2001, V6 models from
  2002; no low range from 2005).
- **Sunroof:** "a sunroof option was added in May 2002" (Wikipedia).

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 2001–06 | — | Every truck. |
| Tail lights | 2001–04, 2005–06 | — | The entry had none; cut at the facelift. |
| AWD rear differential / coupling | 2001–06 | drive: awd/4wd | Same band as the Tucson row. |
| Sunroof | 2002–06 | option | Not offered for 2001. |

Left out, no stated basis: leather and wheels (not researched), the
2.7/3.5 V6 parts (engine).

Result: Santa Fe 2001–06 generic-only 414 → 0. Lots: generic-only 22,669
(6.8%) → 22,255 (6.7%).

### 19.5 Lincoln MKX 2007–2015, 2016–2018

Basis: en.wikipedia.org/wiki/Lincoln_MKX; cars.com "2011 Lincoln MKX: What's
New"; autoblog.com 2007 MKX; slashgear.com 2011 MKX THX; Lincoln 2016 MKX
pricing sheet (all fetched; 2015 package details snippet only).
- **New `GENERATION_BREAKS` "mkx": [2016]:** the entry had no breaks.
- **Facelift 2011 (added to `FACELIFT_BREAKS`):** "Along with the new grille
  comes new headlights"; "The full-width taillight design … has been
  replaced by new split taillights" (cars.com). The existing MKX lamp rows
  are now cut at 2011, and every row at 2016.
- **AWD:** optional on both generations.
- **Audio:** THX II (14 speakers) optional 2007–15; Revel 13- or 19-speaker
  2016–18, with no THX.
- **Vista Roof:** optional (standard on the 2016 Reserve and Black Label).

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 2007–15, 2016–18 | — | Every vehicle. |
| A/C compressor | same | option | Standard fitment not confirmed by a source (conservative). |
| AWD power transfer unit | same | drive: awd/4wd | Same band as the Escape/Explorer PTU rows. |
| Vista panoramic roof | same | option | Same band as the Soul/Sportage panoramic rows. |
| THX II amp + speakers | 2007–15 | option | Cost is the amplifier median ($24); band as the Harman Kardon rows. |
| Revel amp + speakers | 2016–18 | option | Same. |

Left out, no stated basis: the rear drive unit (only the PTU is a known
pull for this platform here), seats and wheels.

Result: MKX generic-only 413 → 0. Lots: generic-only 22,255 (6.7%) →
21,842 (6.6%).

### 19.6 Ford Five Hundred 2005–2007

Basis: en.wikipedia.org/wiki/Ford_Five_Hundred; consumerguide.com/used/2005-07-ford-five-hundred
(fetched).
- **No facelift:** the only change was a mid-2006 side-molding swap. The
  2008 Taurus restyle is the renamed car and outside this entry.
- **A/C:** standard on the SE (CG lists).
- **AWD:** optional on every trim.
- **Moonroof:** optional ($895). The sources disagree on SE availability;
  it is option-flagged either way.

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 2005–07 | — | Every car. |
| AWD rear differential / transfer unit | 2005–07 | drive: awd/4wd | Same band as the Equinox row. |
| Sunroof | 2005–07 | option | |

Left out, no stated basis: the CVT and 6-speed (transmissions), the
chrome mesh grille option (2007, no audited band).

Result: Five Hundred generic-only 409 → 0. Lots: generic-only 21,842 (6.6%)
→ 21,433 (6.4%).

### 19.7 Kia Optima 2001–2005 (MS), 2007–2010 (MG)

Basis: en.wikipedia.org/wiki/Kia_Optima; consumerguide.com/used/2001-06-kia-optima
and /used/2007-10-kia-optima; Kia 2003 release (theautochannel.com
2002/11/08); cars.com "2005 Kia Optima: What's New"; conceptcarz.com copy of
the 2009 Kia release (fetched).
- **2006 is ambiguous:** "Midway through the 2006 model year, Kia issued a
  redesigned version … as a '2006.5' model" (CG). With both generations
  sold as 2006 models, 2006 gets no new rows (58 cars stay generic-only).
- **MS facelift added to `FACELIFT_BREAKS` at 2003, 2004 and 2005:** the
  sources disagree. CG and the Kia 2003 release give 2003 ("new hood and
  grille … new tail lights"). cars.com says "A new grille went on 2004
  models". Wikipedia says "headlamps were restyled for 2004 (2005 model
  year)". Cutting at all three can only narrow windows.
- **MG facelift 2009 (added):** "headlamps narrowed", "taillights are
  narrowed", redesigned rear fascia (Kia release).
- **A/C:** standard on the LX every year 2001–10.
- **Sunroof:** never on the LX; standard or optional on SE/EX (MS) and
  optional on EX/SX packages (MG).

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 2001–05, 2007–10 | — | Every car. |
| Tail lights | 2001–05, 2007–10 (cut at the facelifts) | — | The entry had none. |
| Sunroof | 2001–05, 2007–10 | option | |

The existing 2001–06 headlight row also crosses the 2006 split. It is now
cut at 2003/04/05, and its 2005–06 piece is left as is (flagged here).

Result: Optima 2001–10 generic-only 396 → 58 (all 2006). Lots:
generic-only 21,433 (6.4%) → 21,095 (6.3%).

### 19.8 VW CC 2009–2017

Basis: en.wikipedia.org/wiki/Volkswagen_CC; cars.com "2013 Volkswagen CC at
the 2011 LA Auto Show" and "2009 Volkswagen CC: What's New";
consumerguide.com/used/2009-14-volkswagen-cc; carvana.com 2017 CC
(fetched). The US name "CC" (not "Passat CC") rests on search text only;
the entry already matches both "volkswagen cc" and "vw cc".
- **Facelift 2013 (added to `FACELIFT_BREAKS`):** "Newly standard bi-xenon
  headlights … in new surrounds", "the grille and front bumper have a more
  horizontal, angular appearance", "new rectangular LED taillights"
  (cars.com).
- **4Motion:** VR6 only, 2009–16. It was dropped for 2017 (Carvana).
- **Sunroof:** standard on most trims, but not the 2009 4-cylinder Sport.
  The sources disagree on pop-up vs panoramic.

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 2009–17 | — | Every car. |
| A/C compressor | 2009–17 | option | Standard fitment not confirmed by a source (conservative). |
| 4Motion rear differential | 2009–16 | drive: awd/4wd | Same band and cost basis as the Passat row (§16.7). |
| Sunroof | 2009–17 | option | Not on every trim. |

The existing CC lamp rows are now cut at 2013. Left out, no stated basis:
DSG units (transmission), seats and wheels.

Result: CC generic-only 396 → 0. Lots: generic-only 21,095 (6.3%) → 20,699
(6.2%).

### 19.9 Block totals

Generic-only **24,111 (7.3%) → 20,699 (6.2%)**: 3,412 cars moved. No entry
unchanged at 12,301 (3.7%).
- **New `GENERATION_BREAKS`:** mkx 2016.
- **New `FACELIFT_BREAKS`:** galant 2002/2007/2009, sorento 2007, santa fe
  2005, mkx 2011, optima 2003/2004/2005/2009, volkswagen cc 2013.
- **Compared with the commit before §19:** none of the 12,726 distinct
  year/make/model combinations on the lots lost a part or had an existing
  part's band or gate status change, and `sharedWith` notes are identical.
- **Tests:** `test_interchange.py`, `test_consensus_parts.py` and the
  other offline scraper tests pass.

Leftovers in these models: Optima 2006 (58).

## 20. Next measured block (2026-11-04, owner: "start the next parts block")

Same basis and method as §18/§19 (generations and facelifts researched
first; FETCHED/SNIPPET as before). The §20 code sits just before
`_apply_consensus_evergreens()`, because several of these entries are
created by the §11 breadth pass after the §16–19 blocks. The Saturn Aura
entry is created by the overlay, so its rows go in `parts_overlay.json`.
Before: generic-only 20,699 (6.2%) of 332,476 cars, no entry 12,301 (3.7%).

| Order | Model | Generic-only cars |
|---|---|---|
| 1 | Chevrolet Malibu 1997–2003 | 384 |
| 2 | Mazda Tribute 2001–11 | 379 |
| 3 | Chevrolet Uplander 2005–09 | 376 |
| 4 | Mazda5 2006–15 | 364 |
| 5 | Lexus ES 1992–2006 | 361 |
| 6 | Saturn Aura 2007–09 | 353 |
| 7 | Ford Windstar 1995–2003 | 347 |
| 8 | GMC Savana 1996–2019 | 343 |

### 20.1 Chevrolet Malibu 1997–2003 (N-body), and the Chevrolet Classic fix

Basis: consumerguide.com/used/1997-03-chevrolet-malibu; en.wikipedia.org/wiki/Chevrolet_Malibu
(raw; fetched).
- **Facelift 2000 (added to `FACELIFT_BREAKS`):** "Malibu earned a modest
  facelift this season" (CG); "For 2000, the grille was restyled with a
  chrome center bar" (Wikipedia).
- **A/C:** standard ("Standard equipment included … air conditioning", CG).
- **LS options:** a power sunroof (in the 2000 option table) and, from
  2000, a rear spoiler. Sunroof availability before 2000 is unconfirmed.

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 1997–2003 | — | Every car. |
| Sunroof, LS rear spoiler | 2000–03 | option | |

**Fix: Chevrolet Classic 2004–05 (87 cars).** Wikipedia lists the N-body
as "1997–2003 (Chevrolet Malibu) / 2004–2005 (Chevrolet Classic)". The §11
breadth pass had routed "Chevrolet Classic" to the malibu entry, so those
cars got the 2004–07 Epsilon Malibu's rows. The part names happened to be
the same (pump, compressor, fan, lamps, evergreens), but their "fits"
windows said 2004–07, so the part finder offered Epsilon Malibus as
same-generation donors: a false fitment claim from this workstream's own
earlier change. The per-car check (§20.9) confirms no part was lost; only
those windows changed, to 2004–05.
- The Classic now has its own entry ("Chevrolet Classic (N-body Malibu)",
  2004–05). It carries copies of the Malibu's lamp and mirror rows, the
  mechanical pulls, the sunroof and spoiler options, and the evergreens,
  all bounded 2004–05.
- The malibu entry no longer claims the Classic spelling.
- The §11 test that asserted the old routing now asserts the new entry.
- No interchange with any Malibu year is claimed.

Result: Malibu 1997–2003 generic-only 384 → 0. Lots: generic-only 20,699
(6.2%) → 20,315 (6.1%).

### 20.2 Mazda Tribute 2001–2006, 2008–2011

Basis: en.wikipedia.org/wiki/Mazda_Tribute (raw); cars.com/research/mazda-tribute-2005;
fueleconomy.gov model menus (fetched). A/C evidence is snippet only (KBB,
CarGurus).
- **Generations:** 2001–06, then 2008–11. There was no 2007 US model year
  (EPA lists none).
- **Facelift 2005 (added to `FACELIFT_BREAKS`):** "a different grille and
  headlamps that were redesigned for 2005", "A new rear fascia features
  vertical taillights" (cars.com). No 2nd-gen facelift was found (2009 was
  mechanical only).
- **Drive:** FWD or 4WD in both generations.

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 2001–06, 2008–11 | — | Every vehicle. |
| A/C compressor | same | option | Standard only per snippets. |
| AWD power transfer unit | same | drive: awd/4wd | Escape platform twin; same band as the Escape PTU row. |

Left out, no stated basis: sunroof, leather and wheels (not researched),
and hybrid parts (only a very limited number were built).

Result: Tribute generic-only 379 → 0. Lots: generic-only 20,315 (6.1%) →
19,936 (6.0%).

### 20.3 Chevrolet Uplander 2005–2009

Basis: consumerguide.com/used/2005-08-chevrolet-uplander; en.wikipedia.org/wiki/Chevrolet_Uplander
(raw; fetched).
- **Span:** US 2005–08; Canada and Mexico to 2009.
- **No facelift:** 2006 brought 6-lug wheels, a door logo and a short
  wheelbase.
- **A/C:** front A/C standard every year; rear A/C standard on LS/LT
  trims.
- **AWD:** 2005–06 only; it was dropped for 2007 ("could not handle the
  torque of the 3.9 L").
- **Power sliding doors:** offered every year (passenger side standard on
  LT, driver side optional).

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 2005–09 | — | Every van. |
| Power sliding door motor | 2005–09 | option | Band kept below the audited minivan rows (Rare, $60–150), conservative. |
| AWD rear differential / transfer unit | 2005–06 | drive: awd/4wd | |

Left out, no stated basis: wheels (5-lug 2005 vs 6-lug 2006+, so a set
would need a split not researched), rear-A/C parts (no audited band), the
third row.

Result: Uplander generic-only 376 → 0. Lots: generic-only 19,936 (6.0%) →
19,560 (5.9%).

### 20.4 Mazda5 2006–2010, 2012–2015

Basis: consumerguide.com/used/2006-10-mazda-5; cars.com/research/mazda-mazda5;
fueleconomy.gov; en.wikipedia.org/wiki/Mazda_Premacy (raw; fetched).
- **New `GENERATION_BREAKS` "mazda5": [2012]:** 1st gen 2006–10, 2nd gen
  2012–15. There was no 2011 US model year (EPA lists none). The existing
  Mazda5 lamp and mirror rows are now bounded by generation.
- **Facelift 2008 (added to `FACELIFT_BREAKS`):** "a new front fascia,
  grille, headlights, and taillights" (CG). No 2nd-gen facelift was found.
- **Gen 1:** A/C standard on all trims. Sunroof standard on Touring and
  optional on Sport for 2006–07; Sport automatic only in 2008; Touring and
  Grand Touring only for 2009–10.

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 2006–10, 2012–15 | — | Every car. |
| A/C compressor | 2006–10 | — | Standard (CG). |
| A/C compressor | 2012–15 | option | Unconfirmed. |
| Sunroof | 2006–10 | option | Trim-dependent. |

Left out, no stated basis: the gen-2 sunroof (unconfirmed), and LED rear
lamps on the 2008+ Touring/Grand Touring (a trim gate on lamps was not
researched further).

Result: Mazda5 generic-only 364 → 0. Lots: generic-only 19,560 (5.9%) →
19,196 (5.8%).

### 20.5 Lexus ES 1992–2006 (XV10 1992–96, XV20 1997–2001, XV30 2002–06)

Basis: en.wikipedia.org/wiki/Lexus_ES (raw); consumerguide.com/used/1997-01-lexus-es-300
and /used/2002-06-lexus-es-300es-330; Lexus Knowledge Center pricing and
spec PDFs 1992–2005 (xr793.com; fetched).
- **Facelifts added to `FACELIFT_BREAKS`:**
  - 1995: "a revised grille insert …, new headlights and fog lights".
  - 2000: "new, clear tail lights and turn signals, a revised front end
    with a new grille, headlights, and lower bumper".
  - 2005: "new front and rear fascias, clear taillights, projector
    headlights, and a redesigned grille".
  The existing ES lamp rows are now cut at these years.
- **Moonroof:** option code SR on XV10/XV20; standard on the XV30 (CG and
  the pricing sheets).
- **Audio:** Nakamichi was option code NK 1998–2001. Mark Levinson
  (2002–06) is already an existing row.
- **A/C:** standard on the XV20 and XV30 (CG). For the XV10 it is only
  implied by its absence from the option lists, so it is option-flagged.

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 1992–96, 1997–01, 2002–06 | — | Every car. |
| A/C compressor | 1992–96 | option | Not stated outright for the XV10. |
| A/C compressor | 1997–01, 2002–06 | — | Standard. |
| Sunroof | 1992–96, 1997–01 | option | |
| Sunroof | 2002–06 | — | Standard on the XV30. |
| Nakamichi amp + speakers | 1998–01 | option | Cost is the amplifier median ($24); band as the Harman Kardon rows. |

Also flagged: "ES 300"/"ES 330" listings match both the `lexus es` entry
and the overlay-created `es 300` entry, so they show two "Lexus ES" cards.
This is pre-existing and was not changed here; merging the overlay entry
into `lexus es` is a follow-up.

Result: Lexus ES 1992–2006 generic-only 361 → 0. Lots: generic-only 19,196
(5.8%) → 18,835 (5.7%).

### 20.6 Saturn Aura 2007–2009 (rows in `parts_overlay.json`)

Basis: consumerguide.com/used/2007-09-saturn-aura; en.wikipedia.org/wiki/Saturn_Aura
(raw; fetched).
- **Where the rows live:** the Aura entry is created by the overlay merge,
  so its new rows were added to the overlay's Aura entry (`source:
  parts-gaps-§20.6`). The overlay carries no drive gate, which is not needed
  here.
- **No facelift:** one generation, 2007–09.
- **Equipment:** A/C standard on all trims. The power sunroof was optional
  on every trim and never standard (panoramic $1,500 in 2007). The XR had
  18" machined alloys; the XE had 17" covers.

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 2007–09 | — | Every car; same bands and costs as `_GAP_MECH`. |
| Sunroof | 2007–09 | option | |
| XR 18" alloy wheels | 2007–09 | trim: XR | XR-only wheels. |

Left out, no stated basis: Green Line/Hybrid parts (no audited band), the
3.6 V6 (engine).

Result: Aura generic-only 353 → 0. Lots: generic-only 18,835 (5.7%) →
18,482 (5.6%).

### 20.7 Ford Windstar 1995–1998, 1999–2003

Basis: consumerguide.com/used/1995-98-ford-windstar and /used/1999-03-ford-windstar;
en.wikipedia.org/wiki/Ford_Windstar (raw; fetched).
- **New `GENERATION_BREAKS` "windstar": [1999]:** the existing Windstar lamp
  and mirror rows are now bounded by generation.
- **Facelifts added to `FACELIFT_BREAKS`:**
  - 1998: "The front fascia underwent a facelift, adopting a trapezoidal
    grille and redesigned headlamps".
  - 2001: "Both the nose and tail were slightly restyled" (CG); "Slight
    cosmetic changes … to front and rear fascias for '01".
- **Doors:** gen 1 had a right-side slider only. Gen 2 had dual sliders,
  with power sliding doors standard on the SEL and optional on the SE.
- **A/C:** standard in gen 2. In gen 1 it is confirmed only for 1997–98.

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 1995–98, 1999–03 | — | Every van. |
| A/C compressor | 1995–98 | option | 1995–96 base unconfirmed. |
| A/C compressor | 1999–03 | — | Standard. |
| Power sliding door motor | 1999–03 | option | Same conservative band as the Uplander row. |

Left out, no stated basis: rear A/C parts (no audited band), gen-1 power
doors (none found).

Result: Windstar generic-only 347 → 0. Lots: generic-only 18,482 (5.6%) →
18,135 (5.5%).

### 20.8 GMC Savana 1996–2024

Basis: en.wikipedia.org/wiki/Chevrolet_Express (raw); conceptcarz.com copy
of the GM 2003 release (fetched); 2010–15 Savana brochures and a fleet order
sheet (snippet).
- **Facelift 2003 (added to `FACELIFT_BREAKS`):** "the bodywork forward of
  the windshield was revised"; "Bolder front-end styling - including grille,
  bumper, fascia, fenders and hood", "larger, revamped taillamps" (GM). The
  existing Savana lamp rows are now cut at 2003.
- **2018 not used:** the 2018 headlamp change is confirmed for the Express
  but not stated for the Savana, so there is no 2018 cut.
- **AWD:** 2003–14 (1500 and light-duty 2500, 5.3L).

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module | 1996–2002, 2003–24 | — | Every van; also bounded at the 2003 revision (conservative). |
| A/C compressor | same | option | A front-A/C delete existed on fleet orders (snippet). |

Left out, no stated basis: a radiator-fan row (engine-driven clutch fan on
these V8 vans), AWD rows (the transfer case is kept out with gearboxes and
no other part-level basis was found), rear A/C parts (no audited band).

Result: Savana generic-only 343 → 0. Lots: generic-only 18,135 (5.5%) →
17,792 (5.4%).

### 20.9 Block totals

Generic-only **20,699 (6.2%) → 17,792 (5.4%)**: 2,907 cars moved. No entry
unchanged at 12,301 (3.7%).
- **New `GENERATION_BREAKS`:** mazda5 2012, windstar 1999.
- **New `FACELIFT_BREAKS`:** malibu 2000; tribute 2005; mazda5 2008; lexus
  es 1995/2000/2005; windstar 1998/2001; savana 2003.
- **Fixed:** the Chevrolet Classic now has its own N-body entry (§20.1).
- **Compared with the commit before §20:** none of the 12,726 distinct
  year/make/model combinations on the lots lost a part or had an existing
  part's band or gate status change, including the Classic, whose "fits"
  windows were what changed. `sharedWith` notes are identical.
- **Tests:** `test_interchange.py`, `test_consensus_parts.py` and the
  other offline scraper tests pass.

## 21. Next measured block (2026-11-04, owner: "start the next parts block")

Same basis and method as §18–20: generations and facelifts were researched
first. WP is Wikipedia raw wikitext, CG is Consumer Guide used reviews;
FETCHED/SNIPPET as before. Measured on the new scan: generic-only 17,883
(5.4%) of 333,739 cars, no entry 12,369 (3.7%).

| Order | Model | Generic-only cars |
|---|---|---|
| 1 | Mercury Mariner 2005–11 | 346 |
| 2 | Fiat 500 2012–19 (the count included 500L/500X listings; see §21.2) | 344 |
| 3 | Chevrolet Spark 2013–22 | 330 |
| 4 | Nissan Juke 2011–17 | 330 |
| 5 | Mercury Sable 1992–2009 | 326 |
| 6 | Dodge Stratus 1995–2006 | 325 |
| 7 | Ford Mustang S197 2005–06 | 320 |
| 8 | Ford Transit Connect 2010–22 | 310 |

### 21.1 Mercury Mariner 2005–2007, 2008–2011

Basis: WP Mercury_Mariner; consumerguide.com/used/2005-11-mercury-mariner
(fetched).
- **New `GENERATION_BREAKS` "mariner": [2008]:** the 2008 redesign brought
  "new seats, headlights, taillights, a new liftgate …". The existing
  Mariner lamp and mirror rows are now bounded by generation.
- **No facelift within either generation:** the only lamp change was the
  2010 removal of the turn-signal repeaters, which no row covers.
- **A/C:** standard (CG).
- **AWD:** optional on gas models, and every Hybrid was AWD. Escape twin, so
  AWD cars carry a PTU.
- **Sunroof:** a gen-1 option (Luxury/Premier).

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 2005–07, 2008–11 | — | Every vehicle. |
| AWD power transfer unit | same | drive: awd/4wd | Same band as the Escape/Tribute PTU rows. |
| Sunroof | 2005–07 | option | Gen-2 availability not confirmed. |

Left out, no stated basis: hybrid battery and drive parts (no audited
band), the gen-2 sunroof.

Result: Mariner generic-only 346 → 0. Lots: generic-only 17,883 (5.4%) →
17,537 (5.3%).

### 21.2 Fiat 500 2012–2019, and the 500L / 500X / 500e routing fix

Basis: WP Fiat_500_(2007); consumerguide.com/used/2012-14-fiat-500;
autotrader.ca 2016 Fiat 500 1957 Edition test drive; fiat500usa.com 2013
features matrix; fueleconomy.gov model menus 2012–2023 (fetched).
- **No US facelift:** the 2016 European facelift was not sold in North
  America ("here in North America we don't get any of the exterior
  changes", autotrader.ca). One generation, 2012–19, with the Abarth and
  500c throughout.
- **A/C:** standard on Pop/Sport/Turbo/500c Pop for 2012–13 (CG and the
  2013 matrix). Later years rest on snippets only.

**Fix: 500L, 500X and 500e (91 cars).**
- **What was wrong:** the entry keyword "fiat 500" matched "Fiat 500L",
  "500X" and "500E" listings, because keyword patterns anchor only at the
  start. Those different cars got the 500's lamp, mirror and evergreen rows
  with "fits 2012–2019" windows, which made the part finder treat them as
  the same generation as the 500.
- **500L and 500X:** they now have their own entries over their EPA US runs
  (500L 2014–20, 500X 2016–23), carrying only the consensus evergreens.
  Nothing model-specific is claimed; their lamps await their own research.
- **500e:** it is electric, so its entry has no rows and its listings show
  no card, rather than an alternator, starter or fuel pump.
- **How it works:** the existing specificity guard in `match_vehicle` drops
  "fiat 500" whenever a longer keyword matches. Matching code is unchanged.
- **Code change:** `_max_entry_calibrated_high` (used by `--list-parts`)
  now tolerates an entry with no rows.

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 2012–19 | — | Every 500. |
| A/C compressor | 2012–13 | — | Standard. |
| A/C compressor | 2014–19 | option | Snippet-only for those years. |

Left out, no stated basis: a sunroof row (a hatch-only option, and an
undecoded "500C" listing would wrongly show it as "if equipped"), 500c-
specific lamps (unconfirmed), Abarth parts.

Result, measured on the same inventory (333,449 cars after a new scan):
generic-only 17,518 → 17,262; the Fiat 500's own 255 cars → 0. The 500L/500X
listings (89) stay generic-only by design. No entry 12,357 → 12,359 (the
two 500e listings).

### 21.3 Chevrolet Spark 2013–2015 (M300), 2016–2022 (M400)

Basis: WP Chevrolet_Spark; consumerguide.com/used/2013-15-chevrolet-spark;
kbb.com "2019 Chevrolet Spark freshened"; autoguide.com 2018/04 "2019
Malibu, Cruze, Spark get facelifts"; thetruthaboutcars.com 2016/01;
fueleconomy.gov model menus (fetched).
- **New `GENERATION_BREAKS` "spark": [2016]:** the existing Spark lamp and
  mirror rows are now bounded by generation.
- **Facelift 2019 (added to `FACELIFT_BREAKS`):** "a mid-cycle facelift …
  revised exterior styling" (WP); "new grille treatment … fog lights will
  be more angular … Projector-style headlights … available" (KBB). The US
  M300 launched already wearing its facelift styling, so it has no cut.
- **A/C:** "included across the board" for 2013–15 (CG). For the 2016+ US
  LS the sources disagree (TTAC says standard; an AutoGuide review calls
  the LS "a car without AC").
- **Spark EV (2014–16, EPA):** it is electric, so it now has an entry with
  no rows and its listings show no card. Before, it carried gas-car rows
  (alternator, starter). The specificity guard drops "spark" for these
  listings. Three cars move to no-entry.

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 2013–15, 2016–22 | — | Every gas Spark. |
| A/C compressor | 2013–15 | — | Standard. |
| A/C compressor | 2016–22 | option | The sources disagree. |

Left out, no stated basis: sunroof (no source mentions one), Spark EV
parts (no audited band).

Result (same 333,449-car inventory): generic-only 17,262 (5.2%) → 16,935
(5.1%); Spark generic-only → 0 except the 3 EVs, which now have no entry
(no entry 12,359 → 12,362).

### 21.4 Nissan Juke 2011–2017 (F15)

Basis: WP Nissan_Juke; consumerguide.com/used/2011-14-nissan-juke; Nissan
2015 Juke US press kit (usa.nissannews.com; fetched).
- **Facelift 2015 (added to `FACELIFT_BREAKS`):** "projector beam headlights
  and LED front Signature Accent Lamps"; "The grille incorporates the new
  Nissan V-Motion look"; "revised boomerang taillights with LED accents"
  (press kit). The existing Juke lamp rows are now cut at 2015.
- **A/C:** standard (manual on S, automatic on SV/SL).
- **AWD:** "Each grade level is available in All-Wheel Drive or Front-Wheel
  Drive".
- **Moonroof:** standard on SV 2011–14 and on SV/SL in 2015; not available
  on S.

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 2011–17 | — | Every car. |
| AWD rear differential / coupling | 2011–17 | drive: awd/4wd | Same band as the Rogue/Tucson rows. |
| Sunroof | 2011–17 | option | Not on S; not VIN-decodable by trim here. |

Left out, no stated basis: NISMO/NISMO RS parts (no audited band), the MR16
turbo (engine), the CVT (transmission).

Result (same inventory): generic-only 16,935 (5.1%) → 16,605 (5.0%). Juke
330 → 0.

### 21.5 Mercury Sable 1992–1995, 1996–1999, 2000–2005, 2008–2009

Basis: WP Mercury_Sable; Consumer Guide used reviews 1990–95, 1996–99,
2000–05, 2008–09 (fetched); 1996 A/C from an Edmunds snippet.
- **Facelifts added to `FACELIFT_BREAKS`:**
  - 1998: "new headlights and a centered Mercury emblem in the grille" (WP);
    "a new grille" (CG).
  - 2004: "a new front and rear fascia, taillights, and a new grille" (CG).
  The existing Sable lamp rows are now cut at those years.
- **No facelift found** for 1992–95 or 2008–09.
- **A/C:** standard 2000–05 (GS) and 2008–09 (CG). 1996 rests on a snippet,
  and 1992–95 is unconfirmed.
- **Sunroof:** optional 2000–05 (LS/LS Premium) and 2008–09 (Premier).
- **AWD:** optional on the 2008–09 Base and Premier.

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 1992–95, 1996–99, 2000–05, 2008–09 | — | Every car. |
| A/C compressor | 1992–95, 1996–99 | option | Not confirmed from a fetched source. |
| A/C compressor, sunroof | 2000–05, 2008–09 | — / option | A/C standard; sunroof optional. |
| AWD rear differential / transfer unit | 2008–09 | drive: awd/4wd | Same band as the Five Hundred row (same platform). |

Left out, no stated basis: wagon lamps (wagons 1992–2004; whether their
tail lights differ from the sedan's is not stated), 1992–99 sunroofs.

Result (same inventory): generic-only 16,605 (5.0%) → 16,280 (4.9%). Sable
326 → 0.

### 21.6 Dodge Stratus 1995–2000 (JA sedan), 2001–2006 (JR sedan)

Basis: WP Dodge_Stratus; consumerguide.com/used/1995-00-dodge-stratus and
/used/2001-06-dodge-stratus (fetched).
- **New `GENERATION_BREAKS` "stratus": [2001]:** the existing Stratus lamp
  and mirror rows are now bounded by generation.
- **Facelifts added to `FACELIFT_BREAKS` at 2003 and 2004:**
  - The coupe got "revised styling … for both front and rear" for 2003.
  - The sedan "got revised front styling that mimicked the changes to the
    coupes in 2003" for 2004.
  The existing lamp rows cover both bodies, so both years are cut. Which
  specific lamps changed is not stated; the cut can only narrow windows.
- **The 2001–05 coupe is a different car** (Mitsubishi Eclipse-based
  ST-22). Every listing is spelled just "Stratus", so the JR rows carry a
  body gate (`body: sedan`):
  - a sedan decode confirms them;
  - a coupe decode excludes them;
  - an undecoded car shows them as "if equipped" ($0).
  On the current lots, 2001–05 decodes are 135 sedan and 6 coupe, with 43
  undecoded.
- **A/C:** standard on the 2001–06 sedan and coupe (CG). For 1995–2000 it is
  confirmed only on the 2000 SE.

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 1995–2000 | — | Every JA. |
| A/C compressor | 1995–2000 | option | |
| Fuel pump module, A/C compressor, radiator fan | 2001–06 | body: sedan | JR sedan only. |
| Sunroof | 2001–06 | body: sedan + option | Optional on the sedan (R/T or SXT package in 2006). |

Left out, no stated basis: coupe-specific rows, and JA sunroofs (offered
only in some years: 1996, 1998, 2000).

Result (same inventory): generic-only 16,280 (4.9%) → 15,958 (4.8%).

### 21.7 Ford Mustang S197 2005–2009, 2010–2014

Basis: WP Ford_Mustang_(fifth_generation); consumerguide.com/used/2005-14-ford-mustang
(fetched).
- **Facelift 2013 (added to `FACELIFT_BREAKS` "mustang"):** "new front fascia
  featuring a larger grille, standard HiD headlamps and two LED accent
  strips"; "LED tail lamp clusters" (WP). The 2010 restyle is already a
  generation break. The existing S197 lamp rows are now cut at 2013. CG
  also mentions 2011 fascias, which WP does not corroborate, so there is no
  2011 cut.
- **2005–06 vs 2007–09:** no lamp or grille change is stated. HID
  headlamps became available for 2008.
- **A/C:** "All Mustangs came with air conditioning" (CG).
- **Shaker 500/1000:** the sources disagree on years. WP lists them as 2005
  options; CG's equipment lists show them for 2007–09.

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor | 2005–09, 2010–14 | — | Every car. |
| Shaker 500/1000 amp + subwoofer | 2005–09 | option | Cost is the amplifier median ($24); band as the Harman Kardon rows. |

Left out, no stated basis:
- a radiator-fan row (electric vs clutch fan not confirmed for this
  longitudinal car);
- GT grille/fog-lamp assemblies (no audited band);
- convertible tops;
- the 2010+ premium audio.

Result (same inventory): generic-only 15,958 (4.8%) → 15,637 (4.7%).
Mustang 2005–06 → 0.

### 21.8 Ford Transit Connect 2010–2013, 2014–2023

Basis: WP Ford_Transit_Connect; consumerguide.com/used/2010-13-ford-transit-connect;
cars.com "2019 Ford Transit Connect: What's New"; kbb.com 2019 Transit
Connect Wagon (fetched); Ford media (snippet).
- **Facelift 2019 (added to `FACELIFT_BREAKS`):** "Front-end styling changes
  include a new grille and headlights" (cars.com); "available LED headlights
  and the company's signature hexagonal grille" (KBB). The existing lamp
  rows are now cut at 2019. Tail lights are not stated; the cut is
  conservative.
- **No US facelift for gen 1:** the US launch coincided with the European
  refresh.
- **A/C:** standard on the gen-1 Cargo XL (CG) and the 2019 XL (cars.com).
  For 2014–18 it rests on a snippet only.

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 2010–13, 2014–23 | — | Every van (FWD, transverse). |
| A/C compressor | 2010–13, 2019–23 | — | Standard. |
| A/C compressor | 2014–18 | option | Snippet-only. |

Left out, no stated basis: the gen-2 rear liftgate option and rear doors
(no audited band), wagon-specific parts.

Result (same inventory): generic-only 15,637 (4.7%) → 15,325 (4.6%).

### 21.9 Block totals

Measured on the same 333,449-car inventory with the code before §21
(93f894e) and after: generic-only **17,864 (5.4%) → 15,325 (4.6%)**, so
2,539 cars moved. No entry 12,357 → 12,362: the five EV listings (3 Spark
EV, 2 Fiat 500e) that no longer carry gas-car rows.
- **New `GENERATION_BREAKS`:** mariner 2008, spark 2016, stratus 2001.
- **New `FACELIFT_BREAKS`:** spark 2019, juke 2015, sable 1998/2004,
  stratus 2003/2004, mustang 2013, transit connect 2019.
- **Routing fixes:** Fiat 500L, 500X and 500e no longer take the Fiat 500
  entry. 500L and 500X have evergreen-only entries over their EPA runs; the
  500e and Spark EV have empty entries (no card).
- **Per-car comparison against 93f894e:** of the 12,648 distinct
  year/make/model combinations on the lots, only those 12 changed (5 500L,
  3 500X, 2 500E, 2 Spark EV). No other car lost a part or had an existing
  part's band or gate status change, and `sharedWith` notes are identical.
- **Tests:** all offline scraper suites pass, including
  `test_interchange.py` and `test_consensus_parts.py`, and `--list-parts`
  runs with the empty entries.

## 23. Facelift follow-ups (2026-11-05, owner: "go on facelifts")

Same rule and machinery as §17: `FACELIFT_BREAKS` (entries under the
`# §23` comment) lists the first US model year of each exterior mid-cycle
facelift; only appearance rows (`_FACELIFT_SENSITIVE_RE`: headlights, tail
lights, grille, bumpers, fog/marker/corner lights) are cut there. Mechanical
and interior rows are never cut at a facelift. A cut applies to every
appearance row on the model even where the source names only some lamps;
it can only narrow a "fits" window. Every year below has a cited source.
Quotes were read through a summarising fetch tool (the Expedition 1999
quote was re-checked against the page). Models without a confirmed year
are left out and listed. Batches are pushed as §23.1, §23.2, …

**Check method (each batch).** Every distinct year/make/model on the lots
(333,449 cars, 12,655 distinct, inventory of 2026-11-04 23:03Z) is matched
before and after with seven decodes (none, sedan FWD, coupe, hatch, SUV AWD,
pickup 4WD, minivan RWD). Card list, `max_value`, and every part field
except `fits`/`yr_min`/`yr_max` (name, band, cost, rarity, gate statuses,
`sharedWith`, sell notes) must be identical; only `fits` may narrow.

### 23.1 Grand Caravan, Odyssey, Expedition, Town & Country

| Model | Facelift MY | Basis |
|---|---|---|
| Dodge Grand Caravan (and the `dodge caravan` alias, same entry) | 1999, 2005, 2011 | 1999: "the 1999 Caravan received new front styling on all trims above SE" (en.wikipedia.org/wiki/Dodge_Caravan); CarGurus 1999: "a front-end redesign on all models". 2005: "Changes for 2005 included a revised grille, new foglight fascia" (Wikipedia); cars.com 2005 Grand Caravan: "A new front fascia ... and new fog lamps". 2011: "new 'double-crosshair' grille" (Wikipedia); cars.com 2011: "new crosshair grille, new headlights and a new front bumper", "taillight revisions" |
| Honda Odyssey | 2002, 2008, 2014, 2021 | 2002: hondanews.com 2002 exterior update, "a more aggressive new grille", "taillight design now features amber-colored turn signals". 2008: "a redesigned dashboard, grille, and tail lights" (en.wikipedia.org/wiki/Honda_Odyssey_(North_America)); auto123 "a new grille and front bumper". 2014: "twin-bar grille and revised lower front fascia", "LED rear tail light bars" (Wikipedia); cars.com 2014 "new hood, front bumper, grille and fenders". 2021: hondanews.com 2021 release, "LED headlights", "redesigned blackout grille", "redesigned lower front facia and fog light housings" |
| Ford Expedition | 1999, 2015, 2022 | 1999: "The 1999 model year received a facelift similar to that of the contemporary Ford F-150 ... a new front grille ... a new front bumper that incorporated the fog lamps" (en.wikipedia.org/wiki/Ford_Expedition, re-checked). 2015: "All-new thinner headlamps ... an all-new front bumper" (Wikipedia; EL got the same); cars.com 2015 first look "new head- and taillights". 2022: "mid-cycle refresh ... revised front end styling" (Wikipedia); MotorWeek "standard LED headlamps, updated taillamps" |
| Chrysler Town & Country | 2005, 2011 | 2005: mid-cycle refresh with "revised exterior styling" (en.wikipedia.org/wiki/Chrysler_Town_%26_Country_(minivan)); cars.com 2005: "Sculpted headlights and a new front fascia that contains round fog lamps". 2011: "restyled exterior ... new fog lights" (Wikipedia); AutoGuide 2011 review "new front grille, bumper and lower fascia", "LED taillights" |

**Left out:** Grand Caravan 1998/2000 (colours, wheels, badges only), the
2012 logo change and 2014 appearance packages (trim, not facelifts);
whether the 1999 restyle reached base/SE vans and whether the 2005 fascia
reached the short-wheelbase Caravan are unconfirmed (the cut is applied to
the shared entry, which can only narrow windows). Odyssey 2022 (headlamp
internals only), the 2023 Black Edition (Canada/Mexico), 2025 (out of
range); Odyssey 2002 headlamps/bumpers and 2021 US tail lights are not
claimed to have changed. Expedition 2003–06 (no facelift found), 2000 and
2011 (trim colour/grille changes). Town & Country 2006–07 (no change),
2013–14 S trim and DRLs, 2016 projector headlamps (an equipment change;
a fitment check is needed before any headlamp row relies on it).

**Checks.** Of these four, only the Expedition has an appearance row today
(Headlights 1997–2002, now 1997–1998 and 1999–2002). The other three have no
appearance rows yet; their breaks bound future lamp rows. Per-car
comparison: 0 cars with any non-`fits` difference; 1,027 Expedition cars
(1997–2002) have a narrowed headlight window. Coverage is unchanged:
generic-only 15,326 (4.6%), no entry 12,360 (3.7%). `test_parts_gaps.py`
(new §23.1 check), `test_interchange.py`, `test_consensus_parts.py` and
`test_vpic_fixes.py` pass.

### 23.2 Silverado / Sierra, Ram 1500 and HD, BMW 3 Series, Maxima

| Model | Facelift MY | Basis |
|---|---|---|
| Chevrolet Silverado | 2003, 2016, 2022 | 2003: "refreshed in 2002 for the 2003 model year" (en.wikipedia.org/wiki/Chevrolet_Silverado); GM press text (theautochannel.com 2002-02-06): "redesigned headlamps, park-turn signals and daytime running lamps". 2016: "a new grille, headlights, and front fascia" (Wikipedia); Autoblog "2016 Chevy Silverado puts on a better face". 2022: "mid-cycle refresh ... new front-end design" (Wikipedia) |
| GMC Sierra | 2003, 2016, 2022 | 2003: GM press text (theautochannel.com 2002-02-06): "a restyled grille, bumper and fascia"; Wikipedia "slight design changes". 2016: "a new grille, headlights, and front fascia" (en.wikipedia.org/wiki/GMC_Sierra); Automotive Fleet 2016 styling update (LED headlights, fascia, grilles, bumpers, LED tails). 2022: "a new front-end design" (Wikipedia); GM Authority new grille and thinner headlights |
| Ram 1500 | 2006, 2013 | 2006: "the front fascia was modernized ... a facelift was given to all Ram models" (en.wikipedia.org/wiki/Ram_pickup); Autoblog 2006 Ram 1500 review: new headlamps, fascia, bumper, grille. 2013: "the Ram 1500 received a revised front fascia" (Wikipedia); cars.com 2013 Ram 1500 design deep dive (grille, projector headlamps, LED tails) |
| Ram 2500 / 3500 | 2006, 2013 | 2006: Wikipedia's "a facelift was given to all Ram models"; Edmunds 2006 Ram 2500 "freshened front-end styling" (search excerpt). 2013: Autoblog 2012-09-27 "a new, taller grille, which necessitated a new hood"; CarBuzz Ram 2013 HD reveal (taller grille, LED lamps on SLT) |
| BMW 3 Series | 2002, 2004, 2009, 2011, 2016, 2023 | E46 sedan/Touring 2002: "facelift versions of the sedan and Touring were released for the 2002 model year"; E46 coupe/convertible 2004: "released for the 2004 model year" (en.wikipedia.org/wiki/BMW_3_Series_(E46)). E90/E91 2009: "the facelift (LCI) versions of the saloon and estate were released for the 2009 model year" (Wikipedia E90). E92/E93 2011: Carvana 2011 3 Series "new headlights, taillights, hood, grille, bumpers"; BMWBlog 2011 coupe/convertible LCI. F30/F31 2016: "released in 2015 for the 2016 model year ... Revised headlights and tail-lights" (Wikipedia F30). G20 2023: "new front and rear bumpers, new headlights" (Wikipedia G20); Edmunds "refreshed 2023 BMW 3 Series" |
| Nissan Maxima | 1997, 2002, 2007, 2012, 2019 | 1997: "the Maxima's exterior was refreshed for 1997 ... clear-lens headlights ... redesigned tail-lights" (en.wikipedia.org/wiki/Nissan_Maxima); Nissan 1997 press kit. 2002: "a mild facelift ... larger, revised grille ... revised headlamp design" (Wikipedia); cars.com 2002. 2007: nissannews (Canada) 2007 release "new front grille, hood, bumper and headlights". 2012: "a new grille, taillights" (Wikipedia); Nissan 2012 press kit "new front grille design, new rear combination lights". 2019: AutoGuide 2018-11 (checked): "a larger grille", "Headlamps of the LED variety are also standard", "the taillights and fascia have been reworked"; Nissan US 2019 press kit |

**Body styles (BMW).** The cut is per model, not per body: sedan/wagon
and coupe/convertible facelift years are both applied. That makes some
windows narrower than the true one (a 2003 sedan's E46 headlights now read
2002–2003 where the sedan LCI lamp fits 2002–2005). Narrower is never a
false claim; a body-aware cut would be needed to widen it again.

**Left out:** Ram 1500 2007 (tail lights "slightly revised" only: the cut
cannot target one lamp and would make 2006 headlights read "2006–2006"),
Ram 1999 (Sport trim only), Ram 2025 refresh and Silverado/Sierra/Ram
2019+ beyond the cited years (out of range); Silverado/Sierra GMT900
(no facelift found); the Sierra 2003 headlamps are not claimed to have
changed (grille/bumper/fascia are; the cut is conservative). BMW E36 (no
facelift found), F34 GT (US year unconfirmed; its rows share the F30 cut),
G21 and E36 Touring (not US). Maxima: none.

**Checks.** 0 cars with any non-`fits` difference (seven decodes). 7,537
cars have a narrowed window, by listing make: Chevrolet 2,827 (Silverado
incl. HD and feed spellings), Dodge 2,558 (Ram), GMC 842, BMW 1,024,
Nissan 286. Coverage unchanged:
generic-only 15,326, no entry 12,360. Tests pass (new §23.2 check).

**Found, not fixed (routing, outside this task):** "Ram Van", "Ram Wagon"
(Dodge B-series vans) and "Chevrolet Ram1500" listings match the Ram
pickup entry, so a 2002–05 Ram Van shows pickup headlights. Silverado/
Sierra 2500/3500 listings also match the 1500 rows.

### 23.3 Ranger, Suburban, Traverse, Pathfinder

**Single-component rule (from §23.2 on).** The cut is per model and splits
every appearance row, so a year in which only one item changed (a grille
alone, tail lights alone) would split all the other lamps' windows with no
basis. Such years are listed as left out, not added.

| Model | Facelift MY | Basis |
|---|---|---|
| Ford Ranger | 1989, 2001, 2006 | 1989: "a restyled hood and grille, and flush-mounted composite headlamps ... the front bumper was redesigned" (en.wikipedia.org/wiki/Ford_Ranger_(Americas)). 2001: "the front fascia was redesigned with a new grille and headlamps" (Wikipedia); Autoblog 2001 Ranger review "revamped front styling ... new multi-beam reflector lamps". 2006: "The grille was restyled into a '3-slot' configuration ... adding clear-lens headlamps ... redesigned taillamps" (Wikipedia) |
| Chevrolet Traverse | 2013, 2022 | 2013: "a new grille and front fascia, a redesigned rear liftgate ... reworked Camaro-inspired tail lights" (en.wikipedia.org/wiki/Chevrolet_Traverse); cars.com 2012 NYIAS 2013 Traverse. 2022: "a facelift in 2021 for the 2022 model year ... thin LED headlights and tail lights" (Wikipedia); GM Authority 2021-07 (refresh slipped from MY2021 to 2022) |
| Nissan Pathfinder | 2002, 2008, 2017 | 2002: "another facelift occurred in 2001 for the 2002 model year ... a revised grille" (en.wikipedia.org/wiki/Nissan_Pathfinder); Consumer Guide 2001–04 "New for 2002 were a restyled grille, body-color bumpers". 2008: cars.com 2007 Chicago show "revised grille and slight changes to the front and back ends"; Wikipedia "The facelifted 2008 Pathfinder debuted at the 2007 Chicago Auto Show". 2017: "an exterior update which includes a new fascia with restyled headlights" (Wikipedia); Nissan US 2017 press kit (new tail lights, search summary) |

**Left out:** Ranger 1995 ("all Rangers adopted a four-hole grille") and
2004 ("the grille was enlarged"): grille only. Ranger 2019–23: no
facelift. **Chevrolet Suburban: no year added.** GMT400 1994 is a grille
plus a high-mount brake light (Edmunds, search excerpt; Wikipedia gives no
detail); GMT800 2003 front was "not carried over to the SUVs"; GMT900
2010 raised bumper (single source); K2 2018 LED DRLs only; the T1 refresh
is MY2025 (out of range). Pathfinder 1999.5: a mid-year change inside
MY1999, so no first model year can be cut without mislabelling part of
1999; 2001 (bumper colour and badge only); 2010 R51 (not US); R53 2022–24
(none in range). The 2008 headlamps and the 2017 tail lights (Platinum
only per Wikipedia) are not claimed to have changed.

**Checks.** Inventory after the 2026-11-05 scan: 334,595 cars, 12,673
distinct. 0 cars with any non-`fits` difference. 1,665 cars narrowed
(Ranger 1,626: headlights 1983–92 → 1983–88/1989–92, 1998–2018 →
1998–2000/2001–05/2006–18; Traverse 39: LED headlights 2018–21/2022–24).
Pathfinder has no appearance rows yet. Coverage unchanged: generic-only
15,400, no entry 12,407. Tests pass (new §23.3 check).

### 23.4 TrailBlazer, Pilot, Tahoe / Yukon, Liberty

| Model | Facelift MY | Basis |
|---|---|---|
| Chevrolet TrailBlazer | 2006, 2024 | 2006: "The TrailBlazer was updated in 2005 for the 2006 model year", "An updated front fascia on all models (except for the base version)" (en.wikipedia.org/wiki/Chevrolet_Trailblazer_(SUV)); Edmunds 2006 "new front and rear fascias for the LT" (search excerpt); go-parts grille guide: 2002–05 and 2006–09 grilles are not interchangeable. 2024: "received a facelift ... for the 2024 model year", "new front fascia", "new LED taillights" (en.wikipedia.org/wiki/Chevrolet_Trailblazer_(crossover)); Carscoops 2023-02 "narrowed daytime running lights and a tighter front fascia" |
| Honda Pilot | 2006, 2012, 2019 | 2006: hondanews.com 2006 Pilot summary "Revised taillight and headlight designs"; Wikipedia (en.wikipedia.org/wiki/Honda_Pilot) "a new fascia ... halogen projector headlights". 2012: "a redesigned front fascia ... changes to the bumper" (Wikipedia); Honda release reprint (conceptcarz) "three-bar horizontal" grille, "Reconfigured multi-reflector halogen headlights". 2019: "new bumpers, grille, wheels, standard LED headlights, and revised tail lights" (Wikipedia); Carscoops / Repairer Driven News 2019 refresh (search summaries) |
| Jeep Liberty | 2005 | "In 2005, all models received a minor facelift" (en.wikipedia.org/wiki/Jeep_Liberty); Stellantis media release id=125: "a freshened exterior design with new front fascia, grille, fog lamps" |

**Left out:** **Chevrolet Tahoe and GMC Yukon: no year added.** No
line-wide restyle is cited inside 1995–2024: the GMT400 grille change is
MY1994; GMT800 2003 was interior, and the 2004 "black outlined taillights"
line is uncorroborated; GMT900 2010 raised bumper (single, conflicting
sources); K2 2018 is LED DRLs on Tahoe and a Denali-only grille on Yukon;
Yukon Denali 2001 is trim-only; the T1 refresh is MY2025. TrailBlazer:
the 2006 SS fascias (trim), and the 2005 LT (Autobytel lists a new LT
fascia for 2005, against Wikipedia/Edmunds 2006; 2006 is used and the
2005 LT is noted as uncertain). Pilot 2022 (LED headlights standard, no
restyle), 2023–24 (none in range). Liberty 2005–06 Renegade hood/grille
(trim), KK 2008–12 (none; 2011 Jet package is an option).

**Checks.** Same inventory as §23.3. 0 cars with any non-`fits`
difference. 3,544 cars narrowed: TrailBlazer 2,217 (headlights 2002–05 /
2006–…), Liberty 1,327 (KJ headlights 2002–04 / 2005–07). The Pilot has no
appearance rows yet. Coverage unchanged: generic-only 15,400, no entry
12,407. Tests pass (new §23.4 check).

**Found, not fixed:** the TrailBlazer's second-segment rows read
"2006–2020", running past the GMT360's 2009 end into years with no
TrailBlazer (the crossover starts 2021). This is harmless (no car has
those years) and predates §23.

### 23.5 Edge, Charger, Dakota, Grand Cherokee

| Model | Facelift MY | Basis |
|---|---|---|
| Ford Edge | 2011, 2019 | 2011: "Exterior changes include a new front fascia, wheels, and a revised bumper" (en.wikipedia.org/wiki/Ford_Edge); MotorWeek 2011 Edge "a big drop-jaw Ford-truck style grille, more expressive headlamp housings". 2019: "a mid-cycle facelift for the 2019 model year, with a revised front grille" (Wikipedia); cars.com 2019 "new headlights, bumpers and taillights" |
| Dodge Charger | 2015 | "the most noticeable change coming in the new front grille and rounded LED headlights" (en.wikipedia.org/wiki/Dodge_Charger_(LX/LD)); cars.com 2015 first look "a new grille, headlights, bumper and fog lights" |
| Dodge Dakota | 1991, 2008 | 1991: "The 1991 model year featured a new grille and hood" (en.wikipedia.org/wiki/Dodge_Dakota, re-checked); Edmunds 1991 "composite headlamps (LE and Sport), new bumper, new grille" (search excerpt). 2008: "unveiled at the 2007 Chicago Auto Show as a 2008 model" (Wikipedia); Stellantis release id=7337 "newly styled hood, grille, front fascia ... and headlamps" |
| Jeep Grand Cherokee | 1996, 2004, 2008, 2014, 2017 | ZJ 1996: "a mid-cycle restyling, with new front and rear bumpers" (Wikipedia ZJ page; larger grille, revised headlamps). WJ 2004: "revised front grilles and fascias (bumpers) for all models" (Wikipedia WJ). WK 2008: "a minor facelift for 2008 with revised headlights" (Wikipedia; WK page: new grille, fascia, "new tail lamps"). WK2 2014: "new, smaller headlamps, and new tail lamps" (Wikipedia WK2); cars.com 2014 "the headlights slimmer", "taillights have gotten larger". WK2 2017: "All 2017 models received a second facelift" with "reshaped headlights, and a reshaped grille" (Wikipedia WK2) |

**Left out:** Charger 2009 (tail lamps only: single-component rule) and
2008/2012 (interior; SRT8 badge). Edge 2021 ST-Line/Titanium Elite
(trim). Dakota 1992 (no change described; Wikipedia's "1991 the only
model year for a unique front-end" concerns the mid-1991 headlamp
change-over), 1997–2004 (none; 2000 Quad Cab is a body style), 2006 R/T
(package). Grand Cherokee 1998 5.9 Limited and 2002 Limited grilles
(trim only), the 2016 75th Anniversary edition that already wore the 2017
front (a special edition; its rows read pre-facelift), the 2017 SRT
fascia (conflicting), WL 2022–24 (none). Single-source years: Grand
Cherokee 1996, 2004, 2008 and 2017 rest on Wikipedia alone (with the WK
page corroborating 2008 internally).

**Checks.** Same inventory as §23.3. 0 cars with any non-`fits`
difference. 120 cars narrowed (Edge LED headlights 2015–18 / 2019–24).
Charger, Dakota and Grand Cherokee have no appearance rows yet. Coverage
unchanged: generic-only 15,400, no entry 12,407. Tests pass (new §23.5
check).

### 23 summary

23 models researched; 21 FACELIFT_BREAKS keys added (Grand Caravan,
Odyssey, Expedition, Town & Country, Silverado, Sierra, Ram, Ram
2500, Ram 3500, BMW 3, Maxima, Ranger, Traverse, Pathfinder, TrailBlazer,
Pilot, Liberty, Edge, Charger, Dakota, Grand Cherokee). No year
confirmed, so left out: Suburban, Tahoe, Yukon. 13,893 cars had an
appearance-row window narrowed; none had any other change. Several
models (Odyssey, Grand Caravan, Town & Country, Pathfinder, Pilot,
Charger, Dakota, Grand Cherokee) have no appearance rows yet; their breaks
will bound lamp rows added later.

### 23.6 Routing fixes: Ram Van / Ram Wagon, Silverado / Sierra HD and Classic (2026-11-05)

Accuracy fix under rule 3 ("never invent fitment"), for the routing bugs
found in §23.2. Code: the `# 2026-11 §23.6` block in `junkyard_scraper.py`
(right after `_bound_rows_per_generation()`, so the rows are final as
written) and the engine-family apps of `gm-gen3-truck` / `gm-gen4-truck`.

**Mechanism.** New entries carry longer keywords ("ram van", "silverado
2500", "sierra classic 2500" …). `match_vehicle`'s specificity guard then
drops the shorter "ram" / "silverado" / "sierra" keyword, so these
listings no longer reach the pickup / 1500 entries. Nothing else about
matching changed.

**1. Dodge Ram Van / Ram Wagon / B-vans.** Every 1994–2003 "Ram Van",
"Ram Wagon", "Ram Van 1500/2500/3500" listing matched the Ram pickup
(2nd/3rd gen) and showed the pickup tailgate, the pickup's manual tow
mirrors, and pickup-window headlights and cluster rows.
Basis (en.wikipedia.org/wiki/Dodge_Ram_Van): 1994 facelift ("the model
line's most substantial revision and facelift since 1978"); 1998 third
generation (longer hood and front fenders, new dashboard, mirrors moved
to the doors), ended 2003. Every 1994+ engine is a Magnum multiport-injected
V6/V8. Entries `ram van 1994-1997` and `ram van 1998-2003`
(`GENERATION_BREAKS["ram van"] = [1998]`):

| Row | Gate | Why |
|---|---|---|
| Headlights, Tail Lights | — | Breadth-pass lamp rows (§11 bands), bounded per generation. |
| Side Mirrors (pair) | — | Does not claim power mirrors (Soul row and band, §13). |
| Fuel pump module | — | In-tank electric pump on every injected Magnum engine. |
| A/C compressor | option | Cargo vans were sold without A/C. |
| Evergreens | window regulator and master switch option | Power windows were not standard on cargo vans. |

Left out: tailgate/bed rows (no bed), radiator fan (engine-driven clutch
fan, as Savana), anything engine/transmission/converter. Pre-1994 Ram
Vans have no entry before or after. A "Ram Van" dated 2004+ hits an empty
suppressor entry. Feed spellings "Dodge Van", "B1500/B2500/B3500",
"B150/B250/B350", "1500/2500/3500 Van" route here too; those had no entry
before.

**Ram C/V (found while measuring).** Make Ram, model "C/V" / "Cargo Van" /
"Caravan" (the cargo Grand Caravan, 2012–15) also matched the Ram pickup
(4th gen: tailgate, power-fold tow mirrors, Uconnect 8.4). It now gets a
generic evergreen-only entry for 2012–15 and suppressors elsewhere. Grand
Caravan rows were not copied (the C/V has no rear seats and no row-level
basis was checked).

**2. Silverado / Sierra 2500, 2500HD, 3500, 1500HD.** These matched the
1500 entries, so they took 1500-only rows (tailgates, tow mirrors, running
boards, LED headlights, MultiPro/Multi-Flex steps, Bose, Denali grille)
and the 1500 generation windows. The HD generations differ
(en.wikipedia.org/wiki/Chevrolet_Silverado: GMT400 HD "continued until
2000, with the new GMT800 Silverado/Sierra HD ... released a year later";
GMT900 HD through 2014; K2XX HD 2015–19; T1XX HD from 2020), so a 2014 HD
showed K2XX 1500 rows and a 2019 HD showed T1XX 1500 LED headlights.
Per HD generation (`silverado hd …`, `sierra hd …`; GENERATION_BREAKS
2001/2007/2015/2020, FACELIFT_BREAKS 2003):

| HD generation | Rows | Basis |
|---|---|---|
| 1999–2000 | evergreens only | A "2500"/"3500" of these years is either the GMT400 carry-over or the GMT800 2500; the listing can't tell. |
| GMT800 HD 2001–06 | Silverado: headlights 2003–06; Sierra: headlights 2001–02, 2003–06; evergreens | GM 10396912 (chevypartsdeal.com, retrieved 2026-11-05): 2003–07 Silverado 1500, 2007 1500 Classic, 1500 HD, 2500 HD 2003–07, 2007 2500 HD Classic, 3500 2003–06. GM 15850351 (gmpartsgiant.com): 1999–2007 Sierra 1500/2500/3500 incl. Classic, 6.6 diesel and 8.1 among the engines. The Sierra cut at 2003 follows §23.2 (conservative). |
| GMT900 HD 2007–14 | headlights 2007–14; evergreens | GM 22853027: 2007–13 Silverado 1500, 2007–14 Silverado 2500 HD / 3500 HD. GM 22853029: 2007–13 Sierra 1500, 2007–14 Sierra 2500 HD / 3500 HD. |
| K2XX HD 2015–19 | evergreens only | Own front end; no catalog basis checked. |
| T1XX HD 2020–24 | evergreens only | Same. |

Left out, no basis found that the HD shares them: tailgates, manual and
power-fold tow mirrors, running boards, Bose, Denali grille, LED
headlights, tailgate steps, camera tailgate. Silverado HD 2001–02
headlights: GM 16526137 lists 1999–2002 Silverado 1500/2500 (with the
6.6/8.1 engines) but no 3500, so no row.

**"Classic".** The 2007 "Classic" is the GMT800 carry-over (Wikipedia),
but "Silverado 1500 Classic" 2007 matched the GMT900 entry (power-fold
tow mirrors etc.). Entries `silverado classic 2001-2007` /
`sierra classic 2001-2007` copy the GMT800 1500 rows with the windows
that ended in 2006 extended to 2007 (headlights: GM 10396912 / 15850351
list the 2007 Classic; tailgate and manual tow mirrors: the existing
gmt800-truck / gmt900-truck family notes "incl. 2007 Classic" / "2007
Classic uses GMT800 mirrors"). 1999–2000 "Classic" (GMT400 carry-over)
gets evergreens only. HD Classic 2001–07 gets the GMT800 HD rows (2007
in the headlight window); an HD "Classic" label in other years gets
evergreens only.

**Engine families.** `gm-gen3-truck` (1999–2007) and `gm-gen4-truck`
(2007–13) used `("Chevrolet", "Silverado*")` / `("GMC", "Sierra*")`
prefix apps, as did their verified alternator groups (2003–06, 2007–10).
The prefix caught every 2500/3500/HD truck. The engine guard already
kept out 6.6 Duramax and 8.1 decodes, but the HD 6.0 passed, and
decode-less HD donors and seekers were offered as "likely" (and inside
the verified 2003–06 group as "verified"). The apps are now explicit
light-duty spellings: Silverado, Silverado 1500, Sierra, Sierra 1500,
Sierra Denali 1500 (both families); Silverado/Sierra 1500 Classic,
Silverado/Sierra Classic, Sierra Classic 1500 for 2007 only, in Gen III
only (the Classic no longer also asks "Gen IV?"). The verified groups list
Silverado, Silverado 1500, Sierra, Sierra 1500. Left out on purpose:
"Sierra Hybrid" (the 2-mode hybrid has no belt alternator; 4 cars lose
the Gen IV app) and "Silverado 1500 Ext Cab" (2 cars; the spelling would
also show in the app's model picker). Explicit names were used so
`docs/app.js` (`pfAppMatches`) needs no change.

**Checks.** Every distinct year/make/model on the lots (334,588 cars,
12,666 distinct; main with §22 vs this change, same inventory) matched
with seven decodes (none, sedan FWD, coupe, hatch, SUV AWD, pickup 4WD,
van RWD). 1,140 cars changed, all in the intended groups, and every
decode gives the same row changes as no decode:

| Group | Cars | Before | After |
|---|---|---|---|
| Ram Van / Ram Wagon listings | 259 | Ram pickup 2nd/3rd gen: tailgate, manual tow mirrors, headlights, cluster + evergreens | Ram Van entry: lamps, mirrors, fuel pump, A/C (option), evergreens (windows option) |
| B-van spellings (Dodge Van, B2500 …) | 38 | no entry | Ram Van entry |
| Ram C/V | 31 | Ram pickup 4th gen (tailgate, power-fold mirrors, Uconnect 8.4) | evergreens only |
| Silverado HD (2500/2500HD/3500/1500HD/HD Classic) | 523 | Silverado 1500 entry of the year | HD entry: lost tailgate, tow mirrors, running boards, LED headlights, steps; headlights only where cited |
| Sierra HD | 186 | Sierra 1500 entry | HD entry: also lost Bose, Denali grille, camera tailgate |
| Silverado / Sierra 1500 Classic | 102 | GMT900 1500 (2007): power-fold mirrors, Denali grille | GMT800 rows (manual tow mirrors, tailgate, headlights 2003–07); the 1 1999–2000 car: evergreens |

Engine families: 678 HD/Classic-HD cars left `gm-gen3-truck` /
`gm-gen4-truck`; 102 2007 1500 Classics now resolve to Gen III only; one
1999–2000 GMT400 "Silverado Classic" left Gen III; 4 Sierra Hybrids and
2 "Silverado 1500 Ext Cab" lost the app (above).
Every other car, all 1500s included, is unchanged (matches and families).

Coverage is reported as it falls, not improved. Against main after
§22.1–22.5 (same inventory): generic-only 13,893 (4.2%) → 14,634 (4.4%),
+741 (Silverado HD 523, Sierra HD 186, C/V 31,
one 1999 Classic: they now show generic rows instead of 1500/pickup rows
they did not have a basis for). No entry 12,396 → 12,358 (−38, the
B-vans). Tests: new §23.6 checks in `test_parts_gaps.py` (Ram Van /
Ram Wagon / B-van / C/V never get a pickup card or pickup rows, any
decode; HD never gets 1500-only rows; HD headlight windows; Classic rows;
1500 cards unchanged) and `test_interchange.py` (HD never in the light-duty
families; 1500 families unchanged; HD donor never verified). All of
`test_parts_gaps.py`, `test_interchange.py`, `test_consensus_parts.py`,
`test_vpic_fixes.py`, `test_model_normalization.py` pass.

**Open.** Plain "Silverado" / "Sierra" listings (528 cars) can be HD
trucks the listing doesn't name; they keep the 1500 rows (a VIN decode
naming the series could route them later). HD rows for K2XX/T1XX and HD
tailgates/tow mirrors need catalog part numbers before they're added.
Pre-1999 C/K "Silverado 2500" listings (~80) have no entry, as before.

## 22. Next measured block (2026-11-05, owner via hub: "Ensure everything is at speed")

Same basis and method as §18–21 (generations and facelifts researched first;
FETCHED/SNIPPET as before). A second Parts session works the facelift
follow-ups as §23 at the same time (hub's temporary exception to one session
per workstream). My `FACELIFT_BREAKS` additions sit under a "# §22" comment
group. Measured on the 334,595-car scan with the code before §22:
generic-only 15,399 (4.6%), no entry 12,409 (3.7%).

| Order | Model | Generic-only cars |
|---|---|---|
| 1 | Mercury Milan 2006–11 | 311 |
| 2 | Buick Encore 2013–22 | 307 |
| 3 | Chevrolet Captiva Sport 2012–15 | 301 |
| 4 | Buick Park Avenue 1991–2005 | 299 |
| 5 | Scion xB 2008–15 | 293 |
| 6 | Hyundai Sonata 1999–2005 (EF) | 290 |
| 7 | Infiniti JX35/QX60 2013–20 | 288 |
| 8 | Ford Escort 1991–2003 | 285 |

### 22.1 Mercury Milan 2006–2011

Basis: WP Mercury_Milan; cars.com "2010 Mercury Milan: What's New";
jalopnik.com 2010 Milan (Ford release) and 2010 Fusion/Milan/MKZ design;
consumerguide.com/used/2006-11-mercury-milan; fueleconomy.gov menus
(fetched).
- **Facelift 2010 (added to `FACELIFT_BREAKS`):** "revised tail lamps and an
  enlarged grille, reshaped headlamps and revised front fascia" (WP);
  "taillights are narrower and taller" (cars.com). The existing Milan lamp
  rows are now cut at 2010.
- **A/C:** standard (CG base lists 2006–11).
- **AWD:** optional on the 3.0 V6 from 2007 ("Milan AWD" in EPA's menus
  2007–11).
- **Sunroof:** optional ($795 in 2006–07, packages from 2008, standard on
  the 2010–11 Hybrid).
- **Hybrid:** 2010–11. No "Milan Hybrid" listings are on the lots, and
  hybrid parts are not curated here.

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 2006–11 | — | Every car. |
| Sunroof | 2006–11 | option | |
| AWD rear differential / transfer unit | 2007–11 | drive: awd/4wd | V6 AWD only; same band as the Five Hundred row. |

Result (same inventory): generic-only 15,399 (4.6%) → 15,087 (4.5%). Milan
311 → 0.

### 22.2 Buick Encore 2013–2022, and the Encore GX routing fix

Basis: WP Buick_Encore; cars.com "2017 Buick Encore: What's New";
blog.consumerguide.com (2017 Encore); kbb.com 2013 Encore review and first
drive; fueleconomy.gov menus 2019–2025 (fetched).
- **Facelift 2017 (added to `FACELIFT_BREAKS`):** "revised headlights and
  bumpers, LED tail lights" (WP); a new grille, and LED headlamps on higher
  trims (cars.com). The existing Encore lamp rows are now cut at 2017.
- **A/C:** standard on the base ("The well-equipped base Encore includes …
  air conditioning", KBB 2013); applied to the generation, as in §18–21.
- **AWD:** available every year (EPA "Encore AWD").
- **Sunroof:** "All but the base model can be fitted with … a power sunroof".

**Fix: Encore GX (8 listings).** The GX is a different, larger vehicle; EPA
lists "Encore GX" separately for 2020–25. The "encore" keyword caught it, so
it showed the Encore's rows and windows. It now has its own evergreen-only
entry (2020–25), and the specificity guard drops "encore" for it.

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 2013–22 | — | Every vehicle. |
| AWD rear differential / coupling | 2013–22 | drive: awd/4wd | Same band as the Tucson/Juke rows. |
| Sunroof | 2013–22 | option | |

Result (same inventory): generic-only 15,087 (4.5%) → 14,788 (4.4%). Encore
→ 0; the 8 GX listings stay generic-only on their own entry by design.

### 22.3 Chevrolet Captiva Sport 2012–2015

Basis: WP Opel_Antara; automotive-fleet.com 2012 Captiva Sport; cars.com
2011 "The Saturn Vue is back as the 2012 Captiva Sport"; blog.consumerguide.com
(2013); kbb.com 2013/2014; foxnews.com 2014; fueleconomy.gov menus
2011–2016 (fetched).
- **Fleet-only** in the US for every year ("cannot be purchased new", CG
  2013).
- **No facelift found** (the 2015 model year was abbreviated).
- **A/C:** standard ("All models will include … air conditioning",
  cars.com).
- **Sunroof:** on the LTZ and up-level trims.
- **AWD:** confirmed for the 2012 LTZ V6. EPA also lists "Captiva AWD" for
  2013–14, but CG, Wikipedia, cars.com and KBB all say the V6 and AWD were
  dropped after 2012. The AWD row is therefore limited to 2012.

**Routing:** EPA names this vehicle "Captiva" for 2012–15, the only US
Captiva, so "Chevrolet Captiva" listings (6, all 2012–15) now match this
entry instead of nothing.

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 2012–15 | — | Every vehicle. |
| Sunroof | 2012–15 | option | Up-level trims. |
| AWD rear differential / transfer unit | 2012 | drive: awd/4wd | Same band as the Equinox row. |

Result (same inventory): generic-only 14,788 (4.4%) → 14,487 (4.3%); no
entry 12,409 → 12,403.

### 22.4 Buick Park Avenue 1991–1996, 1997–2005

Basis: WP Buick_Park_Avenue; consumerguide.com/used/1991-96-buick-park-avenue
and /used/1997-05-buick-park-avenue; blog.consumerguide.com 2005 review
flashback; cars.com 2003 "What's New"; 2005 Park Avenue brochure (pdf);
theautochannel.com 1996 review; GM parts catalog pages (chevypartsdeal.com)
for lamp part numbers (fetched).
- **New `GENERATION_BREAKS` "park avenue": [1997]:** the entry had no breaks.
- **Cuts added to `FACELIFT_BREAKS`:**
  - 1993: "new grilles and taillights" (CG); tail lamp part numbers change
    from 1991–92 to 1993–96 (GM catalog).
  - 1995: "Base cars also got a new grille, bodyside moldings, and fascias"
    (CG); headlamp part numbers change from 1994 to 1995 (catalog only).
  - 2003: "Ventiports returned on the Park Avenue Ultra along with a bolder
    grille" (WP); Ultra only, and the cut is conservative for base cars.
  - 2005: "revisions to grille and taillamps" (CG); updated rear fascia
    (WP); tail lamp part numbers change from 1998–2004 to 2005 (catalog).
  The existing Park Avenue lamp rows are now cut at these years and at
  1997.
- **A/C:** standard ("the usual standard comfort items … air conditioning",
  1996; CG 2000–01 lists dual-zone automatic climate control; 2005
  brochure).
- **Sunroof:** optional on the 2nd gen ($1,095 with the Prestige package in
  2000–01; Prestige/Ultra in 2005). 1st-gen availability is snippet-only.
- **Ultra vs base tail lamps:** they differ 1991–97 and are shared 1998–2005
  (GM catalog). The existing generic tail-light row does not separate Ultra
  in 1991–97; flagged, not changed.

| Row | Years (per gen) | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 1991–96, 1997–2005 | — | Every car. |
| Sunroof | 1997–2005 | option | |

Left out, no stated basis: the supercharger (engine), Ultra-specific lamp
rows, the 1st-gen sunroof.

Result (same inventory): generic-only 14,487 (4.3%) → 14,188 (4.2%). Park
Avenue 299 → 0.

### 22.5 Scion xB 2008–2015 (2nd gen)

Basis: WP Scion_xB; pressroom.toyota.com "Scion announces pricing for
restyled 2011 xB"; kbb.com 2013 xB update; cars.com "Scion xB lives another
year"; consumerguide.com/used/2008-14-scion-xb (fetched).
- **Appearance cuts added to `FACELIFT_BREAKS`:**
  - 2011: "fresh exterior styling including changes to the front and rear
    bumpers, grill, headlights and taillights" (Toyota).
  - 2013: "a mild nose and tail tweak", i.e. a revised front bumper and a
    gloss-black lower grille insert (KBB).
  The existing xB lamp rows are now cut at 2011 and 2013.
- **A/C:** standard (CG base lists 2008–13).
- **Sunroof:** no regular factory option; only limited Release Series cars
  had one.

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 2008–15 | — | Every car. |

Left out, no stated basis: a sunroof row, and Release Series parts.

Result (same inventory): generic-only 14,188 (4.2%) → 13,893 (4.2%). xB
2nd gen 293 → 0.

### 22.6 Hyundai Sonata 1999–2005 (EF)

Basis: WP Hyundai_Sonata; cars.com "2002 Hyundai Sonata: What's New";
consumerguide.com/used/1999-01-hyundai-sonata and /used/2002-05-hyundai-sonata;
drivechicago.com 1999 review; fueleconomy.gov menus (fetched).
- **Facelift 2002 (added to the existing `FACELIFT_BREAKS` "sonata"):** the
  EF-B revised "the hood/bonnet, grille, headlights … tail-lights and rear
  license plate location" (WP); "new front and rear sheet metal, lighting
  and bumpers" (cars.com). The EF had no lamp rows in the entry, so the cut
  will apply to any future appearance rows.
- **A/C:** standard every year (CG base lists, cars.com 2002, the 1999
  review).
- **Sunroof:** optional on both engine versions, in packages through 2005
  (not on the 2005 GL 4-cylinder manual).

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 1999–2005 | — | Every car. |
| Sunroof | 1999–2005 | option | |

Left out, no stated basis: EF lamp rows (no lamp rows existed and none were
added in this pass).

Result (same inventory): generic-only 13,893 (4.2%) → 13,604 (4.1%). Sonata
EF 290 → 0 (1 listing remains outside these years).

### 22.7 Infiniti JX35 / QX60 2013–2020

Basis: WP Infiniti_QX60; cars.com "2016 Infiniti QX60 first look" and
"2013 Infiniti JX35: What's New"; 2014 Infiniti QX60 factsheet (pdf);
automotiveworld.com (IIHS headlamp note); fueleconomy.gov menus 2012–2014
(fetched).
- **Appearance cuts added to `FACELIFT_BREAKS` "infiniti qx60":**
  - 2016: "new front and rear fascias with restyled headlights and
    taillights" (WP); "spindle grille now stretching deeper into the bumper"
    (cars.com).
  - 2019: "All 2019 QX60s built before September 2018 have HID headlights",
    and later builds have LED (IIHS). The switch follows build date, so the
    model-year cut at 2019 is the conservative boundary; within 2019 the
    lamp type still varies.
  The existing QX60 lamp rows are now cut at 2016 and 2019.
- **Standard equipment:** tri-zone automatic climate control and a power
  moonroof on every version (2014 factsheet; "Standard power moonroof",
  cars.com 2013).
- **AWD:** available every year (EPA).
- **Hybrid:** 2014–17. There are 2 "QX60 Hybrid" listings; see the
  hybrid note in §22.9.

**Routing:** "Infiniti JX" listings (12, all 2013) are the JX35, Infiniti's
only JX (EPA lists JX35 for 2013). They now match this entry instead of
nothing.

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, A/C compressor, radiator fan | 2013–20 | — | Every vehicle. |
| Sunroof glass + motor | 2013–20 | — | Standard. |
| AWD rear differential / coupling | 2013–20 | drive: awd/4wd | Same band as the Rogue row (same Nissan platform family). |

Left out, no stated basis: the rear panoramic moonroof (option), hybrid
parts.

Result (same inventory): generic-only 13,604 (4.1%) → 13,315 (4.0%); no
entry 12,403 → 12,391.

### 22.8 Ford Escort 1991–1996, 1997–2003, and the ZX2

Basis: WP Ford_Escort_(North_America); consumerguide.com/used/1991-96-ford-escort
and /used/1997-03-ford-escort; Washington Post 1997 review (via cars.com);
drivechicago.com 1998 ZX2 review; NHTSA vPIC model lists and VIN decodes;
fueleconomy.gov; RockAuto catalog (1999 and 2002, both engines); Ford
parts catalog pages (fordpartsdeal.com) for lamp part numbers (fetched).
- **New `GENERATION_BREAKS` "escort": [1997]:** gen 2 ran 1991–96 (hatch,
  wagon, sedan from 1992); gen 3 sedan 1997–2002 (fleet-only 2001–02),
  wagon 1997–99, ZX2 1998–2003.
- **Appearance cuts added to `FACELIFT_BREAKS`:**
  - 1992 and 1993: a minor grille change. WP says 1992 ("the grille oval …
    enlarged") and CG says 1993 ("a slightly restyled grille"); both are
    cut.
  - 1999: "minor visual revision to the rear fascia (integrating the reverse
    lamps into the taillamp units)" (WP); the Ford catalog sedan rear-lamp
    part number changes between 1998 and 1999.
  - 2003: the ZX2's "front fascia underwent a revision" (WP).
  The existing Escort lamp rows are now cut at these years.
- **A/C:** optional in every generation (CG 1995; the 1997 LX review; the
  1998 ZX2 review).
- **Sunroof:** optional on gen 2 (CG); the ZX2 power moonroof was optional.

**ZX2 entry (16 "ZX2" + 5 "Escort ZX2" listings).**
- **Why a separate entry:** the ZX2 coupe has its own front end and lamps,
  and NHTSA decodes 1999+ VINs as model "ZX2".
- **Before:** "ZX2" listings matched nothing, and "Escort ZX2" listings got
  the sedan's lamp rows.
- **Now:** the ZX2 has its own entry ("Ford Escort ZX2", 1998–2003) with the
  pump, fan, A/C (option) and moonroof (option) rows plus the evergreens.
  RockAuto lists the same A/C compressor, fuel pump and radiator fan for the
  Zetec (ZX2) and SPI (sedan) engines in 1999 and 2002. This is aftermarket
  catalog fitment, and 1997–98 and the wagon were not checked.
- **Not covered:** plain "Escort" listings that decode as coupes (45 on the
  lots) stay on the Escort entry, because the listing doesn't say ZX2.
  Flagged.

| Row | Years | Gate | Why |
|---|---|---|---|
| Fuel pump module, radiator fan | 1991–96, 1997–2003 | — | Every car. |
| A/C compressor | same | option | Optional every generation. |
| Sunroof | 1991–96 | option | |
| ZX2: fuel pump, fan, A/C (option), moonroof (option) | 1998–2003 | — / option | As above, on the ZX2 entry. |

Left out, no stated basis: gen-3 sedan sunroof (not stated), wagon-specific
lamps (the 1997–99 wagon kept the gen-2 body from the windshield back), and
lamp rows on the ZX2 entry.

Result (same inventory): generic-only 13,315 (4.0%) → 13,030 (3.9%); no
entry 12,391 → 12,375.

### 22.9 Block totals, and a hybrid finding for the owner

Same 334,595-car inventory, code before §22 (33bce51) vs after:
generic-only **15,399 (4.6%) → 13,030 (3.9%)**, so 2,369 cars moved. No entry
12,409 → 12,375 (34 listings now match: 6 Captiva, 12 JX, 16 ZX2).
- **New `GENERATION_BREAKS`:** park avenue 1997, escort 1997.
- **New appearance cuts (`FACELIFT_BREAKS`, "# §22" group or existing
  keys):** milan 2010; encore 2017; park avenue 1993/1995/2003/2005;
  scion xb 2011/2013; sonata 2002; infiniti qx60 2016/2019; escort
  1992/1993/1999/2003.
- **Routing:** the Encore GX has its own entry; "Captiva", "JX" and "ZX2"
  listings now match their vehicles.
- **Per-car comparison:** only 7 of 12,666 combinations changed, all
  intended (5 Encore GX, 2 "Escort ZX2"). Interchange notes are identical.
  All offline suites and `--list-parts` pass.

**Hybrid finding (not changed; needs an owner decision).** 802 listings on
the lots name a hybrid ("Fusion Hybrid", "Escape Hybrid", "Civic Hybrid",
"Camry Hybrid", "Sonata Hybrid" …). 763 of them show at least one gas-only
row: the consensus-evergreen alternator and starter (752) and/or the
gap-block A/C compressor (405). Hybrids of these families typically use a
high-voltage electric A/C compressor and start/charge through the hybrid
system, so those rows are likely false fitment on hybrid listings.
Proposed fix: a negative gate (e.g. `"not_trim": ["hybrid"]`) on the
alternator, starter and A/C compressor rows that excludes them when the
listing or VIN decode says hybrid. That needs a small `match_vehicle`
change and a per-family check of which hybrids keep a conventional part,
so it is left for the owner's go-ahead.

### 22.10 Hybrid gate (owner via hub, 14:28 UTC: "do everything you think")

`match_vehicle` now drops three gas-only rows when the listing text or the
VIN decode's trim/series says hybrid: the alternator, the starter, and the
belt A/C compressor (`_HYBRID_GAS_ONLY_ROWS`). Hybrids of the families on the
lots generally start and charge through the hybrid system and use an
electric A/C compressor. Where a family is unconfirmed, the row is removed
(unknown is honest).
- **Exceptions:** `_HYBRID_KEEPS` would let a family with a cited
  conventional part keep that row. None are cited yet; the research was
  interrupted by the usage limit and is resuming.
- **Effect (334,595-car inventory):** 86 year/make/model combinations
  changed, all hybrid listings, and no gas car changed. Removed: alternator
  and starter on 81 combinations, A/C compressor on 42. 0 of 803 hybrid
  listings still show one of these rows.
- **ENGINE_FAMILIES (report only, not edited):** `gm-gen4-truck` still
  catches the GMC Yukon Hybrid and Cadillac Escalade Hybrid (2 cars each).
  Left for the hub's Phase 0 hybrid splits.
- **Tests:** Camry Hybrid and Fusion Hybrid lose the three rows and keep
  their other rows; their gas twins keep them; a decode with series
  "Hybrid" also drops them. All suites pass.

**§22.10 exceptions (cited, one source per family):**

| Family | Alternator | Starter | Belt A/C | Source |
|---|---|---|---|---|
| Toyota HSD (Camry/Highlander, Altima Hybrid) | no | no | no (electric) | WP Hybrid_Synergy_Drive ("replaces … alternator, and starter motor") |
| Ford full hybrid (Escape/Mariner, Fusion/Milan/MKZ) | no | no | 05–09 Escape belt, later electric | vehicleservicepros.com 2016-01-19 ("no external starter motor"); greencarreports 1022025; fenderbender |
| Honda IMA (Civic/Accord Hybrid) | no | **yes, backup** | hybrid-specific dual unit | WP Integrated_Motor_Assist ("a conventional starter motor as a backup") |
| Hyundai/Kia HSG (Sonata/Optima Hybrid) | no (270V HSG) | likely no | no (electric) | Kia Optima Hybrid press kit |
| GM two-mode (Tahoe/Yukon/Silverado Hybrid) | no | no | no (300V) | machinedesign.com ("Gone are the alternator, starter …") |
| GM BAS (Vue/Aura/Malibu) | no (36V motor-generator) | **yes (2009 Vue)** | belt-driven | WP BAS_hybrid; greencarreports 1021418 ("retains its standard 12-Volt starter") |

- **Kept rows:** Civic/Accord Hybrid and Vue Hybrid keep the starter row.
- **Still removed:**
  - BAS and early Escape belt compressors, because no source says they are
    the same part as the gas car's;
  - the Aura/Malibu Hybrid starter, which is inferred rather than stated.

## 24. Sensors (2026-11-06, owner via hub: "have we paid attention to sensors?")

Owner asked whether sensors were covered ("I know those can get expensive").
Before this block the table had 8 sensor rows (Subaru EyeSight, a few Hyundai/
Nissan radar rows, Distronic, one BMW MAF).

### 24.1 Federal-mandate rows (all light-vehicle entries)

- **ABS / ESC Pump + Module (match part #)**, MY2013+. Basis: FMVSS 126
  (49 CFR 571.126) requires electronic stability control on every vehicle
  with GVWR ≤ 10,000 lb built on or after 2011-09-01. ESC works through the
  ABS hydraulic unit, so the unit is present. MY2013 is the first model year
  built entirely after the deadline; MY2012 is left out because a few early
  builds came before it.
- **Backup Camera (match part #)**, MY2020+. Basis: FMVSS 111
  (49 CFR 571.111) rear-visibility amendment requires a rear-view camera on
  every vehicle with GVWR ≤ 10,000 lb built on or after 2018-05-01. MY2020 is
  the first full model year after it. MY2018–19 cars are left out because
  some were built before the deadline.
- Band: ABS $50–140 and camera $25–70, both before resale calibration.
  Pull cost: ABS $31 (median of 30 yard lists); camera $15 (minor electrical
  component).
- **Left out:** heavy-duty entries whose GVWR can exceed 10,000 lb
  (F-250/F-350, Ram 2500/3500, Silverado/Sierra HD, Express, Savana,
  Econoline, Transit). Empty suppressor entries stay empty, and entries
  that already track ABS or a camera keep their own row.
- These rows count as generic in `mine_coverage_gaps.GENERIC_PART_TOKENS`, so
  they never make a car look specifically covered.
- Lot reach: 62,176 of 334,432 lot cars get the ABS row; 1,194 get the camera
  row.
- **Not added:**
  - TPMS sensor sets. Several makes use indirect (wheel-speed) TPMS with no
    wheel sensors, and per-make 315 vs 433 MHz needs its own basis.
  - MAF. Speed-density engines (many Chrysler/GM) have none; fitment is
    per engine.

### 24.2 ADAS radar, windshield camera, blind-spot radar (named entries)

Every row name ends "(match part #; needs calibration after install)".
Each cell below comes from a source that names the sensor: radar, windshield
camera, or rear corner radar. AEB or forward-collision features whose sensor
type wasn't stated are left out.

**Optional rows.** These are flagged `option` and ship "if equipped" at $0
ranking value. Each runs from the cited first year to the end of that
generation, and carries a spot-it hint. **Standard rows** cover the cited
years only.

| Entry | Rows | Years | Basis |
|---|---|---|---|
| fusion | front radar opt | 2013–20 | Ford 2013 Fusion launch release (theautochannel reprint, 2012-05-10) |
| fusion | blind spot opt / **std** | 2013–18 / **2019–20** | same; Ford 2019 Fusion release, Co-Pilot360 standard (automotiveworld.com reprint) |
| escape | blind spot opt | 2013–19 | Ford 2013 Escape release (theautochannel, 2011-11-16) |
| escape | radar + camera opt | 2017–19 | Ford 2017 Escape product sheet (media.ford.com) |
| malibu | radar opt (Premier) | 2016–18 | autoblog 2015-07-28, 2016 Malibu safety |
| sentra | radar opt (Tech pkg) | 2016–19 | Nissan 2016 Sentra pricing release (usa.nissannews.com) |
| chrysler 200 | radar + blind spot (UWB radar) opt | 2015–17 | FCA/IIHS TSP+ release (prnewswire) |
| cherokee 2014-2024 | radar + camera + blind spot opt | 2014–18 | FCA 2014 Cherokee release (media.stellantisnorthamerica.com id=14042) |
| explorer 2011-2019 | radar + blind spot opt | 2016–19 | Edmunds 2016 Explorer trims |
| rogue | blind spot (radar) opt | 2017–20 | Nissan 2017 Rogue release (usa.nissannews.com) |
| corolla | radar + camera **std** (TSS-P / TSS 2.0) | 2017–20 | Toyota pressroom (TSS-P std 2017); 2020 Corolla eBrochure |
| camry | radar + camera opt | 2018–24 | auto123 2018 Camry (third-party only, so not claimed standard) |
| rav4 | radar + camera **std** 2017; opt 2018; blind spot opt 2016–18 | | automotive-fleet 2017 RAV4 TSS-P std; Toyota Canada 2016 RAV4 specs |
| accord 2013-2017 / 2018-2024 | radar + camera opt | 2016–17 / 2018–22 | conceptcarz 2016 Accord; autoguide 2018 (secondary, so opt) |
| civic 2016-2024 | radar + camera opt | 2016–21 | automotive-fleet 2016 Civic. The 2019 "standard" release covers sedan/coupe only; Type R lacked Honda Sensing, so the row stays opt. |
| cr-v | radar + camera opt / **std** / opt | 2017–19 / **2020** / 2021–22 | Honda 2017 CR-V release (std EX+); Honda 2020 CR-V release (std) |

**Re-flagged as `option`.** These existing radar rows were shipping as
confirmed. The sources show trim-limited or package-only fitment:
- Altima Blind Spot Radar: 2016 SV/SL only; 2019 Safety Shield 360 SV/SL only.
- Elantra Smart Cruise: 2017 Limited Ultimate package.
- Sonata Smart Cruise: optional in 2015; standard only by 2020.
- Maxima Adaptive Cruise Radar: no standard-equipment basis.

**Left out, no basis or sources conflict:**
- Altima 2013–15 blind spot: it uses the rear camera, not radar.
- Front-sensor type unstated, so no row:
  - Altima 2016+ forward sensor;
  - Cruze, Equinox and Impala FCA/LKA;
  - Malibu blind spot;
  - Hyundai/Kia lower-trim AEB;
  - Nissan AEB and Rogue cruise;
  - Fusion/Explorer 2020 Co-Pilot360 AEB.
- Sources conflict:
  - 2015 and 2020 Sonata blind spot;
  - RAV4 2016 XLE;
  - CR-V blind spot vs LaneWatch;
  - Optima 2019 (no Kia release).
- Not researched:
  - Camry 2013–17, Corolla 2013–16, RAV4 2019+;
  - Accord 2013–15, CR-V 2015–16;
  - Explorer 2013–15, Escape 2020.

**Not done in this block:**
- parking sensors;
- rain/light sensors;
- 360 cameras;
- TPMS and MAF (see 24.1).

**Lot reach** (334,432 cars):
- 9,955 cars now show at least one ADAS row.
- 1,139 of those have a standard (ranked) ADAS row.
- New rows: blind spot 5,750 cars, front radar 5,523, windshield camera 1,170.

## 25. Truck generation audit: Xterra, Ranger, Cherokee, Tacoma (2026-11-12, hub)

**Why.** The owner's weekly "what landed" posts go to owner communities
(r/XTerra today; Ranger, Cherokee XJ and 1st gen Tacoma next). Those owners
read the "fits" years. The Xterra rows said "fits 2000–2015", across two
generations.

**Method.** Every row `match_vehicle` returns for each model year from the
first generation to 2025, compared with the windows in `MODEL_GENERATIONS`
(Tacoma has no row there; its windows are the split entries 1995–2004,
2005–15, 2016+). A row is flagged when its "fits" span covers more than one
window, or years outside every window.

**Audit (before):**

| Row | Fits (before) | Crosses |
|---|---|---|
| Xterra Tail Lights (pair, uncracked) | 2000–2015 | 1st gen 2000–04 / 2nd gen 2005–15 |
| Xterra Side Steps / Rock Rails (pair) | 2000–2015 | 1st / 2nd gen |
| Xterra Center Console (lid intact) | 2000–2015 | 1st / 2nd gen |
| Xterra OEM Roof Rack (tube-style) | 2000–2015 | 1st / 2nd gen |
| Xterra Rear Diff Locker Switch (trim PRO-4X/Off-Road) | 2000–2015 | 1st / 2nd gen |
| Tacoma 3rd gen: all 19 rows | 2016–2024 | 3rd gen / 4th gen (MY2024) |
| Ranger 2019 gen: all 12 rows | 2019–2024 (camera 2020–24) | 2019–23 / P703 (MY2024) |
| Ranger 1998–2011 pieces: 9 rows (tailgate, alternator, starter, cluster, climate panel, window regulator and switch, ECM, 2006 headlights) | 1998–2018 / 2006–2018 | no US Ranger MY2012–18 (no generation crossed; the years do not exist) |
| Ranger ABS/ESC mandate piece | 2013–2018 | wholly in the no-sale years |
| Cherokee KL: all 7 rows | 2014–2024 | KL ended MY2023 (no 2024 Cherokee; no generation crossed) |

Not crossing: every Cherokee XJ row (one window 1984–2001), Ranger
1983–92 and 1993–97 pieces, Tacoma 1st and 2nd gen pieces (the §15 pass
already split them).

### 25.1 Nissan Xterra (2000–04, 2005–15)

Every row is a different part in each generation (different Nissan
numbers), so each row is gated to the generation its band was set for.
The bands have no recorded price basis (no audit row; git history
squashed at 6b170f92). The entry's only gated row (diff-lock switch,
PRO-4X/Off-Road) is 2nd-gen-only, so the entry was read as written for the
2nd gen and the bands stay there.

**1st gen rows (hub decision 2026-11-12, "add the first-gen halves").**
A row's low/high is an anchor by convention, which `ebay_prices.py`
replaces with fitment-filtered listing data once it runs. The 1st gen
trucks already showed these anchors, so each 1st gen row carries the
pre-split anchor (same band, rarity and cost as its 2nd gen twin): **anchor
carried from the pre-split row, no separate price basis; to be replaced
by eBay data.** Years are only those the cited numbers cover.

Basis type: **OEM** = opened catalog record in the repo's OEM data
(oem-raw); **excerpt** = web-search excerpt only, page not opened (to be
upgraded once the catalog hosts are reachable).

| Row | Now | Basis |
|---|---|---|
| Tail Lights (pair, uncracked) | 2005–2015 | Nissan catalog via repo OEM data (oem-raw `raw/www.nissanpartsdeal.com.jsonl`, retrieved 2026-11-05): 26550-EA025 / 26555-EA025 "2005-2015 Nissan Xterra, all trims". 1st gen numbers differ: 26550/26555-7Z825 (2001–04) and -ZD325 (2003–04 SE), so not the same part. 2000 is not in the data. |
| Side Steps / Rock Rails (pair, **match part #**) | 2005–2015 | Search excerpts, 2026-11-12 (pages not opened): 2nd gen 96100/96101-EA000 (2005 Off-Road/S/SE, used-parts listing) and 96100/96101-ZP70A (parts.nissanusa.com); 1st gen 96111-7Z060 and 96110/96111-7Z900. Different numbers by generation; more than one number inside the 2nd gen, so the name now says "match part #". |
| Center Console (lid intact) | 2005–2015 | Search excerpts, 2026-11-12: lid 96920-EA002 (2005–07) superseded by 96920-ZP00C (listed 2005/2006–2015 Xterra, nissanpartsdeal and a dealer site); 1st gen lids 96920-7Z000/7Z001. Covers the lid only; the console body's carry-over is not confirmed. |
| OEM Roof Rack (tube-style) | 2005–2015 | Search excerpts, 2026-11-12: 2nd gen roof side rail 76314-EA030 listed 2005–2015 (parts.nissanusa.com); 1st gen rear rail 73230-7Z030 listed 2000–2004 (nissanpartsdeal). Different parts. |
| Rear Diff Locker Switch (trim PRO-4X/Off-Road kept) | 2005–2015 | Search excerpts, 2026-11-12: switch 25154-7S200 listed for 2005–2015 Xterra with the M226 e-locker (nissanpartsdeal, Z1 Off-Road); no 1st gen fitment found. The trims named are 2nd gen trims. |

Basis type of the 2nd gen rows: tail lights OEM; the other four excerpt.

1st gen rows added (every band: anchor carried from the pre-split row, no
separate price basis; to be replaced by eBay data):

| Row | Years | Basis type | Basis |
|---|---|---|---|
| Tail Lights (pair, uncracked, **match part #**) | 2001–2004 | OEM | oem-raw nissanpartsdeal, retrieved 2026-11-05: 26550/26555-7Z825 "2001-2004 Xterra SE, XE" and 26550/26555-ZD325 "2003-2004" (SE / VG33ER option code). Two numbers in the generation, hence "match part #". **2000 left out:** no 2000 number in the data. |
| Side Steps / Rock Rails (pair, **match part #**) | 2001–2004 | excerpt | Search, 2026-11-12: 96110/96111-7Z900 "2001-2002 SE running boards"; 96111-7Z060 "2003-2004 XE pipe side step". Two numbers, hence "match part #". **2000 left out:** no number found. |
| Center Console (lid intact) | 2000–2002 | excerpt | Search, 2026-11-12: 96920-7Z000 listed "2000-2002 Xterra" (nissanpartsdeal). 96920-7Z001 listed "1998-2002 Nissan" with no model named, so not used. **2003–04 left out:** no number found. Lid only, like the 2nd gen row. |
| OEM Roof Rack (tube-style) | 2000–2004 | excerpt | Search, 2026-11-12: rear rail 73230-7Z030 listed "2000-2004 Xterra SE, XE" (nissanpartsdeal). |
| Rear Diff Locker Switch | none | — | No 1st gen fitment found; not added. |

`GENERATION_BREAKS["xterra"] = [2005]` added as a guard, so a later row
cannot cross the break unnoticed.

**Sites not reached:** www.nissanpartsdeal.com and parts.nissanusa.com do
not resolve from this session (host not on the network allowlist); the
excerpts above came through web search only. Opening those pages would
turn the search excerpts into catalog citations. Nothing was worked around.

### 25.2 Toyota Tacoma 3rd gen ends at 2023

2024 is the 4th generation (TNGA-F): motor1.com 2024 Tacoma vs Ranger
comparison, paultan.org 2023-05-19 "2024 fourth generation Toyota Tacoma
debuts", hagerty.com "The 2024 Tacoma" (search, 2026-11-12). The
`tacoma 2016-2024` entry now runs 2016–2023 (key kept: tests and price
keys use it). The one 2024 Tacoma on the lots gets no card until the
4th gen is researched.

### 25.3 Ford Ranger: 1998–2011 and 2019–2023

- 2024 is the new P703 generation in the US (same search sources as
  25.2). Entry window 1983–2024 → 1983–2023.
- No US Ranger MY2012–18: Ford Authority, last North American Ranger built
  2011-12-22 at Twin Cities; return for MY2019 (first truck 2018-10-22,
  Michigan Assembly); Wikipedia "Ford Ranger" (search, 2026-11-12). The
  1998–2011 pieces now say 1998–2011 (were 1998–2018), and the ABS/ESC
  piece for 2013–18 is dropped. Wikipedia mentions a short 2012 fleet run;
  the lots have no 2012 Ranger, so it is noted, not acted on.

### 25.4 Jeep Cherokee KL ends at 2023

KL production ended February 2023, model years 2014–2023 (Wikipedia
"Jeep Cherokee (KL)"; tflcar.com 2023-03; search, 2026-11-12). The
`cherokee 2014-2024` entry now runs 2014–2023. No car changes rows (no
2024 Cherokee exists).

**Change.** `_apply_gen_end_clamps()` runs right after
`_bound_rows_per_generation()`; it only narrows windows and drops pieces
left with no years. No row was added, no band changed, gates unchanged.

**Checks** (lots 2026-11-12, 336,892 cars, 12,470 distinct
year/make/model; main vs branch with `match_vehicle`):
- Only Xterra, Ranger, Cherokee and Tacoma combos changed.
- Ranger (1,352 cars) and Cherokee (533): "fits" only.
- Xterra 2nd gen (468 cars): "fits" plus the side-step name.
- Xterra 1st gen (604 cars): the rows above (2000: rack and console lid;
  2001–02: all four; 2003–04: tail lights, steps, rack). The diff-lock
  switch is gone from the 1st gen.
- The 2024 Tacoma (1 car) gets no card.
- `test_parts_gaps.py` §25 checks: no row on these four trucks leaves its
  generation window (every year to 2025).

**Needs a real price:** every 1st gen Xterra row carries the anchor
only (see 25.1). The eBay refresh would replace them, but no eBay keyset
exists (ops/ebay.md, 2026-11-06), so the anchors stay for now.

**Fitment still missing:** 2000 tail lights and side steps; 2003–04
console lid; any 1st gen diff-lock switch.

**Unresolved:**
- Whether the Xterra roof rack and side steps are on every 2nd gen trim.
  They are not option-flagged today; that was not changed.
- Inside one window but possibly across a mid-cycle change (leads, not
  checked; not crossings of the generation table, so not changed here):
  - Cherokee XJ dash bezel and door panels 1984–2001 (the 1997 interior
    redesign);
  - Tacoma 1st gen climate unit 1995–2004 (the 2001 refresh);
  - Xterra 2nd gen console body across the 2009 update.

## 26. Next measured block (2026-11-17, owner via hub: "I want everything large done. More breadth, data, parts compatibility.")

Order from `ops/parts.md` "Next" item 2. Measured on the 2026-11-17 scan
(336,279 cars, 12,478 distinct year/make/model) with the code before §26:
generic-only 13,880 (4.1%), no entry 12,381 (3.7%).

| Order | Model | Generic-only cars before |
|---|---|---|
| 1 | Volvo S40 2000–11 | 264 |
| 2 | Saturn SL / SL1 / SL2 1991–2002 (plus 171 S-Series, SC and SW listings with no entry) | 276 |
| 3 | Chevrolet Trax 2015–22 | 267 |
| 4 | Chevrolet Sonic 2012 | 281 |
| 5 | Ford Freestar 2004–07 | 253 |
| 6 | Ford Freestyle 2005–07 | 259 |
| 7 | Mitsubishi Mirage and Mirage G4 | 250 |
| 8 | Chevrolet Venture 1997–2005 | 224 |

**Basis rule for this block (stricter than §13–22).** The hub's brief:
a row needs a stated basis, and "probably the same" is not one.
- **Mechanical rows (fuel pump module, A/C compressor) need a catalog part
  number that lists the window.** The numbers come from the carmaker
  catalog records the interchange crawl already holds: branch `oem-raw`
  (read at 57e8b5b9, 2026-11-15), files `raw/www.gmpartsgiant.com.jsonl`,
  `raw/www.fordpartsgiant.com.jsonl`, `raw/www.volvopartsgiant.com.jsonl`,
  `raw/www.mitsubishipartsgiant.com.jsonl`. Each record carries the
  catalog's own fitment lines and a `retrieved` date (2026-11-05 to
  2026-11-10 for everything cited here). No catalog site was contacted for
  this block; the records were read from the branch.
- **A window is only the years a cited number lists.** The crawl was seeded
  one model year per model, so a year with no number is "not in the data",
  not "does not fit". Such years get no row and are listed as left out.
- **"match part #"** is in the row name where two or more numbers cover the
  same window (a drive, engine or equipment split the listing cannot see).
- **Standard or option:** a row is plain only where a fetched source lists
  the item as standard equipment for those years; otherwise `option`.
- **No radiator-fan rows.** §13–22 added the fan row on the layout alone
  ("every car, FWD transverse"). No source at hand names a fan assembly
  with its years (the crawl has no fan category), so the row is left out
  for every model here. See "For the hub" in §26.9.
- **Bands and pull costs** are the audited templates unchanged (§1, §13:
  `_GAP_MECH`, `_SUNROOF`, the AWD rear-unit rows, the Uplander
  sliding-door motor, the Accent/Rio/Focus hatch tail-light row). Nothing
  was priced from a web page; no eBay data was read.

**Other sources.** WP = Wikipedia raw wikitext; CG = Consumer Guide used
reviews (consumerguide.com/used/…); EPA = fueleconomy.gov model menus. All
read directly on 2026-11-17 (quotes are from the page text, not a summary).
Not used: cars.com (returned 403 to this session; not worked around) and
RockAuto (its robots.txt disallows ClaudeBot; not read).

**New mechanism: `PART_NUMBER_BREAKS`.** A cited catalog-number change cuts
one named row at that model year, the way `FACELIFT_BREAKS` cuts the
appearance rows. Narrowing only. One entry so far (the S40 mirrors).

### 26.1 Volvo S40 2000–2004, 2004.5–2011

Basis: WP Volvo_S40; consumerguide.com/used/2000-04-volvo-s40v40 and
/used/2005-11-volvo-s40v50; EPA menus 1999–2012; Volvo catalog records
(oem-raw `raw/www.volvopartsgiant.com.jsonl`, retrieved 2026-11-05 and
2026-11-10).
- **Generations, and why 2004 stands alone.** US sales began with the 2000
  model year (WP; EPA lists "S40 FWD" 2000–2011). The second generation
  went "on sale part way through the 2004 model year, it is sometimes known
  as the 2004.5 Volvo S40" (WP). The catalog agrees: first-generation
  numbers list "2000-2004 Volvo S40 | Base, LSE | 4 Cyl 1.9 L" and
  second-generation numbers "2004-2011 Volvo S40 | 2.4i, T5 … | 5 Cyl".
  A "2004 S40" listing can be either car, so
  `GENERATION_BREAKS["volvo s40"] = [2004, 2005]`: 2004 is its own window
  and gets no new rows (20 cars).
- **Facelifts added to `FACELIFT_BREAKS`:**
  - 2001: "got a thorough makeover, including freshened styling …
    subtly reshaped the fenders, reworked the front bumper with an
    integrated spoiler" (CG); "slightly different front wings and front
    bumper, and larger front indicators" (WP, Phase II). Volvo sedan tail
    lamps 30621883/4 list 2001–2004.
  - 2008: "Both the S40 and V50 received revised exterior and interior
    styling" (CG); "refreshed for April 2007" (WP). Volvo numbers: grille
    8620116 and tail-lamp lens 30698347 are noted "2004-07"; headlamps
    31265706/7 (halogen) and 31214756/7 (bi-xenon) are noted "2008-11".
- **Mirrors (`PART_NUMBER_BREAKS` 2007):** Volvo mirror assemblies
  30744586/9 list 2004–2006; 31278733/9 are noted "2007-11". The existing
  mirror row is now cut at 2007.
- **A/C:** standard ("air conditioning" in the base 2.4i list every year
  2005–11, CG).
- **AWD:** T5 only, 2005–2010 ("added wagon and all-wheel-drive variants
  for 2005"; "The 2011 Volvo S40 and V50 lineups deleted their
  manual-transmission and all-wheel-drive models", CG; EPA "S40 AWD"
  2005–2010; "the AWD system bought from Haldex Traction", WP).
- **Sunroof:** in option packages 2005–08 and 2010–11; "a sunroof were now
  standard" for 2009, and "power sunroof" is in the 2009 base list (CG).

| Row | Years | Gate | Basis |
|---|---|---|---|
| A/C compressor | 2005–11 | — | Volvo 36050586 lists 2004–2011 S40, every trim. Standard (CG). |
| Fuel pump module (match part #) | 2005–11 | — | Volvo 31261425 (noted 2WD, 2004–2010), 8629907 (4WD, 2004–2006), 30792729 (2007–2011), 30724566 and 30792778 (2005–2006). Several numbers, hence "match part #". |
| AWD rear differential / coupling | 2005–10 | drive: awd/4wd | CG, EPA, WP above. Same band as the Tucson/Juke/Encore rows. |
| Sunroof | 2005–08, 2010–11 | option | CG option packages. |
| Sunroof | 2009 | — | Standard in the 2009 base list (CG). |

Left out, no stated basis:
- First generation (2000–03) pump and compressor: no number in the data.
  A/C was standard ("air conditioning w/automatic climate control", CG
  2000–04 base lists), but a window needs a number in this block. 39 cars
  stay generic-only, with their lamp windows now cut at 2001.
- The 2004 cars (20): both generations, see above.
- First-generation sunroof (an option every year per CG, but the window
  crosses the 2001 makeover with no number).
- 2003 "egg crate" grille (WP; Volvo grille 30652182 lists 2003–2004):
  grille only, so not a cut (single-component rule, §23.3).
- T5 turbo parts, R-Design trim parts (not researched).

Result (same inventory): generic-only 13,880 (4.1%) → 13,675. S40
264 → 59 (39 first generation, 20 from 2004).

### 26.2 Saturn S-Series 1991–2002 (SL, SC, SW)

Basis: WP Saturn_S-Series; GM catalog records (oem-raw
`raw/www.gmpartsgiant.com.jsonl`, retrieved 2026-11-05 and 2026-11-06).
- **Generations** ("marketed in three generations … The model changes took
  place for the 1997 and 2000 model years", WP; per body from the WP
  infoboxes and text):
  - sedan (SL, SL1, SL2): 1991–95, 1996–99 ("a completely redesigned
    exterior"), 2000–02 ("new body panels from the belt-line down");
  - wagon (SW1, SW2): 1993–95, 1996–99, 2000–01;
  - coupe (SC, SC1, SC2): 1991–96, 1997–2000, 2001–02 ("redesigned fascias
    front and rear, as well as new headlamps and tail lamps for the 2001
    model year").
  New `GENERATION_BREAKS`: "saturn sl" [1996, 2000], "saturn sw"
  [1996, 2000], "saturn sc" [1997, 2001]. GM lamp and mirror numbers agree
  for the sedan: mirrors 21096065 list 1991–1995 and 21170588/9 1996–2002;
  headlamps 21111169/70 list 1996–1999 and 21112455/6 2000–2002. The
  existing SL lamp rows are now bounded by generation.
- **Fuel pump:** GM 21015330 lists 1991–1996 (SC 1991–92; SC1, SC2, SW1,
  SW2 1993–96; SL, SL1, SL2 1991–96); 21015072 lists 1997 for every body;
  21015152 lists 1998–2002 (SW1 to 1999, SW2 to 2001). One number per
  window, so the standard row name. The number windows do not follow the
  body generations; the rows are cut at both.
- **Power windows and mirrors were options:** "Some factory options such as
  power windows, power locks, or cruise control were not available on the
  SL"; the SL1 "could be optioned with power windows, power locks, power
  mirror" (WP). The window-regulator, master-switch and power-mirror rows
  on these entries are now `option` ("if equipped"). This changes existing
  rows on 276 SL cars from confirmed to "if equipped".

**Routing: 171 listings had no entry.** "Saturn S-Series" (51), "SC",
"SC1", "SC2" (76) and "SW", "SW1", "SW2" (44) matched nothing. They now
have entries `saturn s-series` (1991–2002), `saturn sc` (1991–2002) and
`saturn sw` (1993–2001) with the pump rows above and the consensus
evergreens. No lamp or mirror rows: they differ by body and no row-level
basis was checked. The bare "S-Series" spelling does not say the body, so
its rows are cut at every sedan and coupe break.

| Row | Years (by GM number, then by generation) | Gate | Basis |
|---|---|---|---|
| Fuel pump module | 1991–96, 1997, 1998–2002 | — | GM 21015330, 21015072, 21015152 (all bodies). |
| Window regulator, master switch, power mirrors (existing rows) | all | option | WP: power windows and mirrors were options. |

Left out, no stated basis: A/C compressor ("air conditioning … available
on the option sheet", WP, and no compressor number in the data); sunroof
("A rear spoiler and a sunroof were available options" on the 2000–02
sedan, WP, but no number); lamp rows for the coupe and wagon; the SC2's
pop-up headlamps (1991–96).

Result (same inventory): generic-only 13,675 → 13,399 (SL/SL1/SL2
276 → 0); no entry 12,381 → 12,210 (the 171 listings).

### 26.3 Chevrolet Trax 2015–2022

Basis: WP Chevrolet_Trax; consumerguide.com/used/2015-chevrolet-trax; EPA
menus 2011–2023; GM catalog records (oem-raw, retrieved 2026-11-05 and
2026-11-09).
- **Years:** "released in the United States for the 2015 model year";
  "discontinued the first-generation Trax … following the 2022 model year
  in North America" (WP). EPA lists Trax 2015–2022. The 2024+ Trax is a
  different, larger vehicle and has no entry.
- **Facelift 2017 (added to `FACELIFT_BREAKS`):** "new halogen projector
  headlights, LED daytime running lights, dual taillights, and a new grille
  design" (WP). GM numbers agree for the front: headlamps 42435939/40,
  hood 42599227, fenders 95210618/9 and the grilles all list 2015–2016.
  The bulb tail lamp 42599449/55 lists 2015–2022, so the tail-light cut is
  narrower than that number needs (conservative).
- **A/C:** standard ("Trax is well equipped with automatic transmission,
  air conditioning, power windows and mirrors", CG).
- **AWD:** "Front-wheel drive and all-wheel drive were available" (CG);
  EPA "Trax AWD" every year 2015–2022.
- **Engine:** the 1.4 turbo was the only US engine (CG); the catalog's
  1.8L numbers are other markets'.

| Row | Years | Gate | Basis |
|---|---|---|---|
| Fuel pump module (match part #) | 2015–22 | — | GM module kits 13516849 and 13516865 both list 2015–2022, 1.4L, LS/LT/LTZ. The catalog does not say what separates them, hence "match part #". |
| A/C compressor | 2015–21 | — | GM kit 42783843 lists 2015–2021, 1.4L. No number in the data for 2022, so the row ends at 2021. Standard (CG). |
| AWD rear differential / coupling | 2015–22 | drive: awd/4wd | CG and EPA. Same row and band as the Encore, its platform twin (§22.2). |

Left out, no stated basis: sunroof (no source read lists it); 2022 A/C
compressor; mirrors by trim (several numbers per year, no clean window).

Result (same inventory): generic-only 13,399 → 13,132. Trax 267 → 0.

### 26.4 Chevrolet Sonic 2012–2020

Basis: WP Chevrolet_Aveo (T300 section); consumerguide.com/used/2012-15-chevrolet-sonic;
EPA menus 2011–2023; GM catalog records (oem-raw, retrieved 2026-11-05).
- **Why 2012 only:** the entry had a headlight row and, from 2013, the
  MyLink row, so the 281 cars from 2012 were generic-only.
- **Years:** EPA lists Sonic 2012–2020; "Chevrolet discontinued the Sonic
  after the 2020 model year in the United States" (WP).
- **Facelift 2017 (added to `FACELIFT_BREAKS`):** "The facelift brought a
  restyled front fascia, new LED tail lights" (WP). GM headlamps
  42390433/4 and all four tail lamps list 2012–2016. The existing
  headlight row is now cut at 2017.
- **A/C:** standard on the LS for 2012–15 ("air conditioning" in the LS
  list, CG). 2016–20 is outside the CG page, so those years are `option`.
- **Bodies:** sedan and hatchback; the tail lamps are separate GM numbers.
- **Sunroof:** "Power sunroof" in the option tables 2012–15 (CG).

| Row | Years | Gate | Basis |
|---|---|---|---|
| Fuel pump module | 2012–16 | — | GM kit 13507609 lists 2012–2016, 1.4L and 1.8L, sedan and hatchback. |
| A/C compressor (match part #) | 2013–15 | — | GM kits 42783843 (1.4L, 2013–2020) and 42783863 (1.8L, 2013–2018): two numbers by engine. Standard (CG). |
| A/C compressor (match part #) | 2016–20 | option | Same numbers; standard fitment not confirmed for these years. |
| Sedan tail lights | 2012–16 | body: sedan | GM 42407872/3, sedan trims only. `_TAILS` band. |
| Hatchback tail lights | 2012–16 | body: hatchback | GM 42407868/9, hatchback trims only. Same band as the Accent/Rio/Focus hatch rows. |
| Sunroof | 2012–15 | option | CG. |

Left out, no stated basis: a 2012 A/C compressor (neither number lists
2012); fuel pump for 2017–20 (13507609 stops at 2016; 13592113 lists
2013–2018 for another 1.8L option code only); 2017–20 tail lamps; mirrors
(numbers at hand list 2013–2014 only); RS and turbo parts.
**Suggestion, not done:** the Sonic entry is not in the consensus-evergreen
list, so its 1,281 cars show 2 to 8 rows. Adding it would put "fits
2012–2020" on rows such as the gauge cluster with no source for that span.

Result (same inventory): generic-only 13,132 → 12,851. Sonic 2012:
281 → 0. The 999 cars from 2013–20 gain the rows above for their years.

### 26.5 Ford Freestar 2004–2007

Basis: consumerguide.com/used/2004-07-ford-freestar; WP Ford_Windstar
("Third generation (Ford Freestar; 2004–2007)"); EPA menus 2003–2008; Ford
catalog records (oem-raw `raw/www.fordpartsgiant.com.jsonl`, retrieved
2026-11-05 and 2026-11-06).
- **One generation, no facelift:** "virtually unchanged for 2005", "little
  changed" for 2006, "carries over unchanged during its last year" (CG).
  The Ford grille numbers list 2004–2007.
- **Drive:** "All-wheel drive was not offered" (CG; EPA lists FWD only).
- **A/C:** "front air conditioning" in the base list every year (CG).
- **Power sliding doors:** "Power operation was available for the sliding
  side doors"; standard on the Limited (CG).

| Row | Years | Gate | Basis |
|---|---|---|---|
| A/C compressor | 2004–07 | — | Ford 4F2Z-19703-AB (and the loaded assembly 4F2Z-19V703-AA) list 2004–2007, 3.9L and 4.2L. Standard (CG). |
| Fuel pump module | 2004–05 | — | Ford 3F2Z-9H307-AB lists 2004–2005. Its replacement 3F2Z-9H307-A is named, but its years are not in the data. |
| Power sliding door motor | 2004–07 | option | CG. Same conservative band as the Uplander/Windstar rows (§20.3). |

Left out, no stated basis: fuel pump 2006–07; rear A/C parts (no audited
band); the Mercury Monterey twin (no entry; not researched).

Result (same inventory): generic-only 12,851 → 12,598. Freestar 253 → 0.

### 26.6 Ford Freestyle 2005–2007

Basis: WP Ford_Freestyle; consumerguide.com/used/2005-07-ford-freestyle;
EPA menus 2003–2008; Ford catalog records (oem-raw, retrieved 2026-11-05
and 2026-11-06).
- **One generation, no facelift:** the 2006 change was "the availability of
  a navigation system" and 2007 made side airbags standard (CG). The 2008
  "mid-cycle revision" was sold as the Taurus X (WP), outside this entry.
  Ford headlamp 5F9Z-13008-A and grille 5F9Z-8200-AAA list 2005–2007.
- **A/C:** "front air conditioning" in the SE list every year (CG).
- **AWD:** "each with front-wheel drive or optional all-wheel drive" (CG);
  EPA "Freestyle AWD" 2005–2007; "the Haldex Traction-equipped all-wheel
  drive model" (WP).
- **Sunroof:** "Power sunroof" in the option tables 2005–07 (CG).

| Row | Years | Gate | Basis |
|---|---|---|---|
| A/C compressor | 2005–07 | — | Ford 5F9Z-19V703-DA lists 2005–2007. Standard (CG). |
| Fuel pump module | 2005 | — | Ford 5F9Z-9H307-AA lists 2005 only. Its replacement 6F9Z-9H307-A is named, but its years are not in the data. |
| AWD rear differential / transfer unit | 2005–07 | drive: awd/4wd | CG, EPA, WP. Same row and band as the Five Hundred, its platform twin (§19.6). |
| Sunroof | 2005–07 | option | CG. |

Left out, no stated basis: fuel pump 2006–07; the CVT (transmission);
third-row seat.

Result (same inventory): generic-only 12,598 → 12,339. Freestyle 259 → 0.

### 26.7 Mitsubishi Mirage 1997–2002, 2014–2024, and the Mirage G4

Basis: WP Mitsubishi_Mirage; consumerguide.com/used/1997-02-mitsubishi-mirage
and /used/2014-mitsubishi-mirage; EPA menus 1996–2004 and 2012–2025;
Mitsubishi catalog records (oem-raw
`raw/www.mitsubishipartsgiant.com.jsonl`, retrieved 2026-11-05 and
2026-11-10).

**Fix: the entry ran 1997–2024 as one window.** Every row said "fits
1997–2024", across two unrelated cars and across years with no US Mirage.
- EPA lists Mirage 1996–2002, nothing 2003–2013, Mirage 2014–2015, nothing
  for 2016, then Mirage and Mirage G4 2017–2024. "There was no 2016 model
  year in the North American market" (WP); "The last time Mitsubishi sold
  a car with the Mirage name in the U.S. was in 2002" (CG).
- Now three entries: `mirage` (1997–2002 sedan and coupe), `mirage
  2014-2024` (the hatchback) and `mirage g4` (the sedan, 2017–2024: "For
  the US market, the Mirage G4 sedan was available from spring 2016 as a
  2017 model", WP). `GENERATION_BREAKS["mirage"] = [2017]` cuts every
  hatchback row at the MY2016 gap, and the §25 clamp removes 2016.
- A Mirage listing dated 2003–2013 or 2016 now gets no card (none on the
  lots today).
- The G4's tail lamps are its own (Mitsubishi 8330B069/70, noted "Sedan",
  2017–2020; hatchback 8330A783/4, 2014–2015), which is why it has its own
  entry and lamp rows.

**Facelifts added to `FACELIFT_BREAKS`:**
- 2017 (hatchback): "a new front end design, projector headlights with LED
  daytime running lights, and LED tail lights" (WP). Already a cut through
  the 2016 gap.
- 2021 (hatchback and G4): "The second facelift of the Mirage was launched
  in November 2019, with new front end styling" (WP, global launch date).
  The US year comes from the catalog: G4 bumper cover 6400H293 and the
  headlamps 8301D117/8 are noted "2017-20".

| Row | Years | Gate | Basis |
|---|---|---|---|
| Fuel pump module (hatchback) | 2014–15, 2017–24 | — | Mitsubishi 17030W000P lists "2017-2024, 2014-2015 Mitsubishi Mirage". |
| Fuel pump module (G4) | 2017–24 | — | Same number lists the G4 2017–2024. |
| A/C compressor (hatchback) | 2014 | — | Mitsubishi 7813A524 (7813A531 is the same unit without clutch) lists 2014–2015 and 2017–2019. "automatic climate control" on the base DE (CG 2014). |
| A/C compressor (hatchback) | 2015, 2017–19 | option | Same number; CG covers 2014 only, so standard fitment is not confirmed. |
| A/C compressor (G4) | 2017–19 | option | Same number lists the G4 2017–2019. |
| Headlights, mirrors, tail lights (G4 and 2014+ hatchback entries) | by entry | — | The breadth-pass lamp rows (§11 bands) carried onto the new entries, as before the split. |

Left out, no stated basis:
- 1997–2002 Mirage (56 cars): no number in the data for pump or
  compressor. A/C was optional on base cars (CG option tables).
- 1999: "Minor revisions to the rear end" (CG), "a minor facelift" (WP):
  rear end only, so not a cut (single-component rule).
- A/C compressor 2020–24 (no number lists those years); sunroof (none
  offered in the sources read); HID headlamps (8301C965/6, an option).
- Note: the halogen headlamp 8301C693/4 lists 2014–15 and 2017–20, so the
  2017 cut is narrower than that number needs. The gap forces it anyway.

Result (same inventory): generic-only 12,339 → 12,145. Mirage and G4
250 → 56 (all 1997–2002).

### 26.8 Chevrolet Venture 1997–2005

Basis: WP Chevrolet_Venture; consumerguide.com/used/1997-05-chevrolet-venture;
GM catalog records (oem-raw, retrieved 2026-11-05, 2026-11-06, 2026-11-09).
- **One generation, 1997–2005** (WP; replaced by the Uplander).
- **Facelift 2001 (added to `FACELIFT_BREAKS`):** "The exterior was
  refreshed in 2001"; "2001: The front fascia and steering wheel were
  redesigned" (WP). GM front fascia 88895114/5 and grille 10310159 list
  2001–2005. The tail lamps 19206745/6 and mirrors 15935752/3 list
  1997–2005, so the tail-light cut is narrower than that number needs
  (conservative).
- **A/C:** "front air conditioning" in the base (Cargo/Value/Plus) lists
  2000–2005 (CG). CG's equipment lists start at 2000, so 1997–99 are
  `option`.
- **AWD:** "Optional all-wheel drive" for 2002; "Venture loses its
  regular-length and all-wheel-drive models for a shortened 2005 season"
  (CG); "GM's Versatrak all-wheel-drive system (on long-wheelbase models
  only) was introduced" in 2002 (WP).
- **Power sliding door:** "GM's exclusive power sliding passenger-side
  door was optional" from 1997; driver side from 2001 (CG).

| Row | Years | Gate | Basis |
|---|---|---|---|
| A/C compressor | 1997–99 | option | GM 89018902 lists 1997–2000. Standard not confirmed before 2000. |
| A/C compressor | 2000 | — | Same number. Standard (CG 2000 lists). |
| A/C compressor (match part #) | 2001–05 | — | GM 19130448 (option C69, rear A/C) and 19258827 (without) both list 2001–2005. Standard (CG). |
| Fuel pump module | 1998–2000 | — | GM 19180118 lists 1998–2000. |
| Fuel pump module | 2004–05 | — | GM 19180125 lists 2004–2005. |
| Power sliding door motor | 1997–2005 | option | CG. Same conservative band as the Uplander row (§20.3), its successor. |
| AWD rear differential / transfer unit | 2002–04 | drive: awd/4wd | CG, WP. Same row and band as the Uplander's Versatrak row (§20.3). |

Left out, no stated basis: fuel pump for 1997 and 2001–03 (no number in the
data); rear A/C parts (no audited band); the Oldsmobile Silhouette and
Pontiac Trans Sport/Montana twins (the pump and compressor records were not
checked for them). CG's 1997 trouble note names "the engine cooling fan",
but gives no part or years, so no fan row.

Result (same inventory): generic-only 12,145 → 11,921. Venture 224 → 0.

### 26.9 Block totals

Same 336,279-car inventory, code before §26 (origin/main 56f108c5) vs
after: generic-only **13,880 (4.1%) → 11,921 (3.5%)**, so 1,959 cars moved
to rows with a part-number basis. No entry **12,381 (3.7%) → 12,210
(3.6%)**: the 171 Saturn S-Series, SC and SW listings.
- **New `GENERATION_BREAKS`:** volvo s40 2004/2005; saturn sl 1996/2000;
  saturn sc 1997/2001; saturn sw 1996/2000; saturn s-series (all four);
  mirage 2017 (the MY2016 gap).
- **New `FACELIFT_BREAKS`:** volvo s40 2001/2008; trax 2017; sonic 2017;
  mirage 2017/2021; mirage g4 2021; venture 2001.
- **New `PART_NUMBER_BREAKS`:** volvo s40 side mirrors 2007.
- **New entries:** saturn sc, saturn sw, saturn s-series, mirage
  2014-2024, mirage g4. The `mirage` entry now ends at 2002.
- **Per-car comparison** (every distinct year/make/model, seven decodes:
  none, sedan FWD, coupe, hatch, SUV AWD, pickup 4WD, minivan RWD): 145
  combinations changed, 3,244 cars, all in the models above. No car lost a
  row. Outside these models nothing changed.
  - Changed on existing rows: "fits" windows narrowed (S40, Saturn SL,
    Trax, Sonic, Venture, Mirage); the Mirage G4 card is now titled
    "Mitsubishi Mirage G4"; Saturn SL window-regulator, master-switch and
    power-mirror rows went from confirmed to "if equipped" (§26.2).
- **Tests:** every `scraper/test_*.py` passes (29 files). New §26 checks in
  `test_parts_gaps.py`; one §22.10 check now names the three canonical
  hybrid-gate rows because the gate set also holds the "match part #" A/C
  name.

Leftovers in these models: S40 2000–04 (59), Mirage 1997–2002 (56).

**Not done (item 2 remainder): Fiat 500L, Fiat 500X, Buick Encore GX.**
They keep their evergreen-only entries (97 cars). The catalog data has no
pump, compressor or lamp record for any of them (no Fiat records in the
Mopar file; for the Encore GX the GM file holds only a hood bumper and two
window-switch numbers), so by this block's rule there is no row to add.

**For the hub.**
1. **Radiator-fan rows.** §13–22 added "Radiator Fan Assembly" to FWD
   transverse models on the layout alone. This block left it out for all
   eight models because no source names the part with its years. If the
   earlier convention is acceptable, it is one row per model
   (`_GAP_FAN`); if not, the fan rows on 64 existing entries have the same gap.
   Recommendation: add a cooling-fan category to the catalog crawl and
   settle it from part numbers.
2. **The catalog records can audit the older blocks.** They showed here
   that same-generation windows are sometimes too wide (Venture A/C
   changed at 2001; Saturn pump at 1997 and 1998; S40 mirrors at 2007).
   The §13–22 mechanical rows were windowed by generation without numbers.
   Recommendation: a pass that compares each existing pump/compressor row
   with the numbers on `oem-raw` and narrows where they disagree.
3. **Years with no number** (Freestyle and Freestar pump 2006–07, Venture
   pump 1997 and 2001–03, Trax A/C 2022, Sonic pump 2017–20, first-gen S40,
   1997–2002 Mirage) would close with a crawl seeded on those years. That
   is the interchange workstream's crawl; nothing was fetched here.

## 27. Nissan Xterra: a longer, sourced list (2026-11-17, `ops/parts.md` note of 2026-11-12)

**Why.** The 2026-11-12 note: "the Xterra parts list is thin" (five rows on
the first generation, six on the second). §25.1 fixed the windows; this
adds rows. 1,088 Xterras are on the lots (2026-11-17 scan).

**Rule.** As §26: a row needs a Nissan catalog number that lists its
window, "match part #" where several numbers share it, no radiator-fan
row. Source: the interchange crawl's records on branch `oem-raw`
(`raw/www.nissanpartsdeal.com.jsonl`, 344 Xterra records, retrieved
2026-11-05 to 2026-11-14; read from the branch, no site contacted).
Equipment and facelift facts: WP Nissan_Xterra;
consumerguide.com/used/2000-04-nissan-xterra and
/used/2005-14-nissan-xterra (read 2026-11-17).

**A caution on this catalog's year labels.** Parts that WP and CG date to
the 2002 front end (hood F5100-7Z830, front fascia F2022-7Z825, grilles
62310-7Z800/-7Z840, headlamps 26010-7Z825/6) are listed "2001-2004", and
parts WP dates to the 2009 facelift "(July 2008 production)" are listed
from 2008 (grille 62310-ZL00A, front fascia FBM22-ZL0MA). The catalog seems
to label by production date, one year ahead of the model year at a
mid-year change. Where it matters (the headlamps) the rows follow WP and CG
for the year and say "match part #".

**Facts used.**
- Generations 2000–04 and 2005–15 (`GENERATION_BREAKS["xterra"] = [2005]`,
  §25.1).
- 2002 front end: "revised front-end styling with rounded headlights and
  raised hood" (WP); "All ’02 Xterras had a 'power-bulge' hood and a
  revised dashboard" (CG).
- A/C: "Standard features on all models included antilock brakes, air
  conditioning" (CG 2000–04); "air conditioning" in the base S and X lists
  every year 2005–14 (CG).
- Power windows: first generation, SE equipment and an XE package ("SE
  adds: … power mirrors, power windows", CG). Second generation: not on the
  base S for 2005 or the base X for 2006–07 ("Off-Road adds: … power
  windows"; "S adds: … power windows"); in the base X list from the 2008
  lists on (CG).
- Rockford Fosgate: "For 2003 … a 6-speaker 300W Rockford Fosgate AM/FM/CD
  audio system with an 8-inch subwoofer" on SE models (WP); in the SE list
  and an XE V6 package for 2003 and 2004 (CG).

| Row | Years | Gate | Basis (Nissan numbers and what they list) |
|---|---|---|---|
| Fuel pump module | 2000–04 | — | 17042-4S400: 2000–2004, SE and XE. One number. |
| A/C compressor (match part #) | 2000–04 | — | By engine: 92600-7B410 (VG33E, 2000–2004), -8B401 (KA24DE, 2000–2004), -5S700 (VG33ER, 2001–2004), -4S100 (VG33E, 2000–2001). Standard (CG). |
| Side mirrors (pair, match part #) | 2000–04 | — | 96301/96302-3S500, -3S510, -ZD000, -S3800, -3B300: all 2000–2004, by trim and engine. Soul/Compass mirror band; the row does not claim power mirrors. |
| Window regulator + motor (front) | 2000–04 | option | Motors 80730/80731-7B400: 2000–2004. Power windows were not standard (CG). |
| Power window master switch | 2000–04 | option | 25401-9E000: 2000–2004. Same. |
| Headlights (pair, clear, match part #) | 2000–01, 2002–04 | — | 26010/26060-7B425 (listed 2000–2002) before the 2002 front end; 26010/26060-7Z825 (XE) and -7Z826 (SE) (listed 2001–2004) after. Years per WP and CG; see the caution above. Breadth-pass headlight band. |
| Rockford Fosgate amp + subwoofer | 2003–04 | option | WP and CG above. Same band and cost as the Shaker / Nakamichi rows (§20.5, §21.7). |
| Fuel pump module (match part #) | 2005–15 | — | 17040-ZZ00A: 2005–2015; also -EA000 (2005–2008) and -ZS00A (2007–2010). |
| A/C compressor (match part #) | 2005–15 | — | 92600-EA31A: 2005–2015; also -EA300 (2005–2007) and -EA30C (2007–2015). Standard (CG). |
| Side mirrors (pair, match part #) | 2005–15 | — | 96301/96302-9BC9A and -9BC9B: 2005–2015; -EA000/-EA005 (2005–2013) and -EA18E (SE, 2008–2011) by trim. |
| Headlights (pair, clear, match part #) | 2007–15 | — | 26010/26060-EA000 (SE, Off-Road): 2007–2015; -ZL00A (S, X): 2008–2015. Nothing in the data lists 2005–06, so those years have no headlight row. |
| Window regulator + motor (front) | 2005–07 | option | Motors 80730/80731-EA005: 2005–2015. Not standard on the base trim before 2008 (CG). |
| Window regulator + motor (front) | 2008–15 | — | Same numbers. Standard (CG). |
| Power window master switch | 2006–07 | option | 25401-ZP70A: 2006–2015. |
| Power window master switch | 2008–15 | — | Same number. |

Bands and pull costs are the audited templates (`_GAP_MECH`, the consensus
evergreen window rows, the breadth-pass headlight row, the Soul mirror
row). The ranking value of every Xterra is unchanged (the new rows sit
below the roof rack).

**Left out, with the reason:**
- **Alternator, starter, throttle body.** The numbers change inside each
  generation at different years by engine, and no one number spans a
  window (alternator 23100-3S500 2000–02 / -9Z000 2001–04 for the 2.4,
  -4S100 2000–03 / -1Z600 2002–04 for the V6; second generation -EA201,
  -EA20B, -ZH00A, -ZH00B, -ZH00C in steps from 2005 to 2013; throttle body
  16119-7S001 2005–10 / -7S00A 2009–13). The app's interchange finder
  already carries the verified alternator groups for these trucks.
- **Climate panel, gauge cluster.** Both changed with the 2002 dashboard
  (WP) and again later ("revised HVAC controls" for 2014, CG); 19 and 96
  numbers by trim and year, with no clean window.
- **2005–06 headlights, 2005 master switch:** no number in the data.
- **Radiator fan:** no source names one.
- **Liftgate, hood, bumpers, fenders:** numbers exist (e.g. liftgate
  K0100-EA031, 2005–2015) but there is no audited band for these on this
  truck; not added.
- **Second-generation Rockford Fosgate:** CG names only the radio
  ("Rockford Fosgate AM/FM radio w/in-dash 6-disc CD/MP3 changer"); no
  source read names an amplifier or subwoofer, so no row.
- **`FACELIFT_BREAKS` for the Xterra: not added.** A 2009 cut would split
  the tail-light row, and Nissan 26550/26555-EA025 lists 2005–2015 (§25.1).
  The headlight rows carry their own windows instead.

**Owner-thread leads (2026-11-12): status.**
- Now sourced and added: window regulators (front), with the switch.
- Still no basis or no audited band: roof gear basket and lid, IPDM, rear
  seat latch, roof lights and covers, ECM, door lock actuators, cam/crank
  sensors, evap canister, stalks, sun visors, rear door latches, rear
  cupholder, first-aid kit. Ignition coils stay excluded by rule.

**Checks** (2026-11-17 inventory, 336,279 cars; code before §27 vs after,
seven decodes): only the 16 Xterra year/make/model combinations changed
(1,088 cars); no row lost, no existing row's band, gate or window changed.
Coverage counts are unchanged (the Xterra was already model-specific):
generic-only 11,921, no entry 12,210. `test_parts_gaps.py`: the §25.1
exact-row check now expects the §27 rows as well; new §27 checks.
