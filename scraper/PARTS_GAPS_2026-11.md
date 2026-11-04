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
