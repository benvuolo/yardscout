# Manual-transmission detection: baseline (step 1)

Built 2026-11-05 from the 2026-11-04T23:03Z scan. Nothing here labels a car.
It only measures what we know today, where that knowledge comes from, and how
much is missing. Every number below comes from `build_baseline.py` /
`epa_profile.py` and the JSON they write. Rebuild:

```
python3 -I scraper/manual_detect/build_baseline.py   # ~15 s, writes ground_truth.jsonl, baseline_summary.json, vpic_cells.json
python3 -I scraper/manual_detect/epa_profile.py      # ~15 s, needs epa/vehicles.csv, writes epa_profile.json
```

## 1. Ground truth: cars whose transmission is known

**File:** `scraper/manual_detect/ground_truth.jsonl` (48,996 lines, ~23 MB).
It stays local and gitignored: rebuild it with `build_baseline.py`, which
reads only committed `docs/data/` files.

"Known" means exactly what the app reads: the `trans` text in the extras
shard (`docs/data/vehicle_extras.json`, `[photo, color, engine, trans,
transSrc]`), which `output_json` fills from the yard listing first
(`transSrc "listing"`) and otherwise from the corrected vPIC decode
(`"vin"`, after `_correct_vpic`). "Manual" uses the app's own test
(`isConfirmedManual`: `/manual/i` and not `/automated/i`).

| Line field | Meaning |
|---|---|
| `id`, `vin`, `year`, `make`, `model`, `yard` | feed identity (make/model already canonical) |
| `trim`, `series`, `trimQuality`, `body`, `drive` | vPIC `Trim`, `Series`, trim quality, `BodyClass`, `DriveType`, from the cache. If the VIN is missing from the cache backup, these come from the published side table (no body) |
| `engine` | published engine text (listing, or the vPIC summary) |
| `displL`, `cyl`, `fuel` | parsed from the vPIC engine summary (`DisplacementL` rounded to 0.1, `EngineCylinders`, non-gasoline `FuelTypePrimary`) |
| `trans`, `transClass`, `speeds` | transmission text; class `manual` / `automatic` / `cvt` / `dct` / `amt` / `other` (speeds only, no style); speed count |
| `source` | `vin` or `listing` |
| `vinTrans` | the cached vPIC transmission (equals `trans` on every `vin` line where both exist: 45,263 of 45,263) |
| `vpicMake`, `vpicModel`, `vpicYear`, `inCache` | the factory identity vPIC decoded, and whether the VIN is in the cache backup |
| `uniformCell` | `manual` / `auto` when vPIC returns that one class for **every** decoded live VIN of this vPIC make/model/year (≥ 5 decodes). That is a model-level default, not evidence about this car (see §2) |

| | Cars |
|---|---:|
| Cars on the lots | 333,449 |
| Transmission known | **48,996** (14.7%) |
| from the VIN decode (`vin`) | 46,442 (46,419 unique VINs; 23 VINs listed twice) |
| from listing text (`listing`) | 2,554, all from **Ace Pick-A-Part Jacksonville**, a feed with no VINs |
| class manual | **4,091** (4,047 vin + 44 listing) |
| automatic / CVT / AMT / DCT / speeds-only | 41,163 / 3,171 / 330 / 32 / 209 |

Per-make counts (`baseline_summary.json` → `per_make`, 82 makes). The
**No trans info** column is the opportunity, split by reason:

| Make | Cars | Known trans | via VIN | via listing | Manual (VIN / listing) | Auto | CVT | AMT/DCT/speeds-only | **No trans info** | of which vPIC blank | VIN not in cache backup | no VIN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ford | 54,106 | 761 | 433 | 328 | 2 (1 / 1) | 734 | 25 | 0 | **53,345** | 42,409 | 1,764 | 9,172 |
| Chevrolet | 48,710 | 7,463 | 7,060 | 403 | 472 (470 / 2) | 6,814 | 22 | 155 | **41,247** | 31,473 | 1,328 | 8,446 |
| Nissan | 29,587 | 793 | 528 | 265 | 3 (1 / 2) | 277 | 511 | 2 | **28,794** | 24,374 | 888 | 3,532 |
| Honda | 24,360 | 21,232 | 21,026 | 206 | 1,688 (1,674 / 14) | 18,438 | 1,101 | 5 | **3,128** | 171 | 258 | 2,699 |
| Dodge | 22,484 | 232 | 80 | 152 | 35 (33 / 2) | 197 | 0 | 0 | **22,252** | 17,384 | 777 | 4,091 |
| Toyota | 21,513 | 365 | 172 | 193 | 4 (3 / 1) | 274 | 59 | 28 | **21,148** | 18,052 | 647 | 2,449 |
| Hyundai | 12,247 | 915 | 779 | 136 | 422 (419 / 3) | 404 | 39 | 50 | **11,332** | 9,413 | 299 | 1,620 |
| Chrysler | 10,258 | 85 | 24 | 61 | 1 (1 / 0) | 84 | 0 | 0 | **10,173** | 8,063 | 299 | 1,811 |
| Jeep | 10,053 | 206 | 161 | 45 | 61 (60 / 1) | 145 | 0 | 0 | **9,847** | 7,710 | 360 | 1,777 |
| Kia | 9,530 | 893 | 810 | 83 | 144 (143 / 1) | 664 | 8 | 77 | **8,637** | 7,118 | 241 | 1,278 |
| GMC | 9,260 | 69 | 25 | 44 | 0 (0 / 0) | 68 | 0 | 1 | **9,191** | 7,390 | 285 | 1,516 |
| Buick | 7,238 | 197 | 132 | 65 | 0 (0 / 0) | 194 | 3 | 0 | **7,041** | 5,352 | 197 | 1,492 |
| Volkswagen | 6,886 | 2,571 | 2,496 | 75 | 222 (219 / 3) | 2,349 | 0 | 0 | **4,315** | 3,242 | 170 | 903 |
| Mazda | 6,231 | 129 | 78 | 51 | 1 (0 / 1) | 97 | 0 | 31 | **6,102** | 5,094 | 165 | 843 |
| Subaru | 5,542 | 4,509 | 4,482 | 27 | 559 (559 / 0) | 2,430 | 1,358 | 162 | **1,033** | 30 | 136 | 867 |
| BMW | 5,353 | 157 | 118 | 39 | 9 (7 / 2) | 148 | 0 | 0 | **5,196** | 4,473 | 168 | 555 |
| Cadillac | 4,985 | 336 | 285 | 51 | 29 (29 / 0) | 306 | 0 | 1 | **4,649** | 3,641 | 156 | 852 |
| Mercedes-Benz | 4,710 | 132 | 87 | 45 | 22 (21 / 1) | 101 | 0 | 9 | **4,578** | 3,929 | 165 | 484 |
| Pontiac | 4,393 | 185 | 161 | 24 | 20 (19 / 1) | 165 | 0 | 0 | **4,208** | 3,158 | 124 | 926 |
| Acura | 4,098 | 3,567 | 3,534 | 33 | 96 (95 / 1) | 3,429 | 10 | 32 | **531** | 60 | 45 | 426 |
| Lincoln | 3,408 | 49 | 29 | 20 | 0 (0 / 0) | 47 | 2 | 0 | **3,359** | 2,651 | 93 | 615 |
| Infiniti | 3,383 | 50 | 26 | 24 | 0 (0 / 0) | 44 | 6 | 0 | **3,333** | 2,922 | 88 | 323 |
| Lexus | 3,131 | 90 | 69 | 21 | 0 (0 / 0) | 88 | 2 | 0 | **3,041** | 2,612 | 84 | 345 |
| Mitsubishi | 2,970 | 51 | 29 | 22 | 0 (0 / 0) | 29 | 22 | 0 | **2,919** | 2,321 | 115 | 483 |
| Mercury | 2,861 | 13 | 1 | 12 | 0 (0 / 0) | 12 | 0 | 1 | **2,848** | 2,124 | 82 | 642 |
| Saturn | 2,759 | 907 | 877 | 30 | 185 (182 / 3) | 722 | 0 | 0 | **1,852** | 1,280 | 49 | 523 |
| Volvo | 2,460 | 684 | 667 | 17 | 2 (2 / 0) | 678 | 0 | 4 | **1,776** | 1,407 | 58 | 311 |
| Audi | 2,271 | 618 | 605 | 13 | 21 (21 / 0) | 596 | 1 | 0 | **1,653** | 1,290 | 69 | 294 |
| Scion | 1,531 | 31 | 14 | 17 | 5 (3 / 2) | 26 | 0 | 0 | **1,500** | 1,263 | 51 | 186 |
| MINI | 1,004 | 15 | 10 | 5 | 3 (1 / 2) | 4 | 0 | 8 | **989** | 852 | 38 | 99 |
| Oldsmobile | 959 | 6 | 0 | 6 | 0 (0 / 0) | 6 | 0 | 0 | **953** | 629 | 43 | 281 |
| Land Rover | 831 | 713 | 708 | 5 | 0 (0 / 0) | 713 | 0 | 0 | **118** | 1 | 1 | 116 |
| Suzuki | 750 | 7 | 0 | 7 | 1 (0 / 1) | 6 | 0 | 0 | **743** | 589 | 27 | 127 |
| Jaguar | 700 | 600 | 594 | 6 | 6 (6 / 0) | 594 | 0 | 0 | **100** | 1 | 2 | 97 |
| Ram | 559 | 8 | 7 | 1 | 0 (0 / 0) | 8 | 0 | 0 | **551** | 475 | 23 | 53 |
| Isuzu | 495 | 4 | 2 | 2 | 0 (0 / 0) | 4 | 0 | 0 | **491** | 367 | 13 | 111 |
| 46 other makes | 1,833 | 353 | 333 | 20 | 78 (78 / 0) | 268 | 2 | 5 | **1,480** | 985 | 116 | 379 |
| **All** | 333,449 | 48,996 | 46,442 | 2,554 | 4,091 (4,047 / 44) | 41,163 | 3,171 | 571 | **284,453** | 224,305 | 9,424 | 50,724 |

### Opportunity (cars with no transmission info): 284,453 (85.3%)

- **vPIC decoded the VIN, TransmissionStyle blank: 224,305.** This is the
  main target for VIN-pattern and trim rules. Ford 42.4k, Chevrolet 31.5k,
  Nissan 24.4k, Toyota 18.1k, Dodge 17.4k, Hyundai 9.4k, GMC 7.4k, Jeep 7.7k,
  Kia 7.1k.
- **No VIN: 50,724.** VIN rules cannot reach these cars. Only year/make/model
  rules can (for example EPA sole-offering), or listing text.
- **VIN not in the cache backup: 9,424.** In total, 10,603 lot cars (10,580
  unique VINs) carry a VIN that is not in `vin_decodes.json.gz`. 9,753 of
  those cars have a 17-character VIN, decoded in CI after the backup export
  or a failed decode. The other 850 are pre-1981 or malformed. 1,179 of the
  10,603 still carry a published `vin` transmission from the CI DB. The
  remaining 9,424 have none.
- **Old-schema cache payloads: 0.** Every live VIN in the backup has the
  engine/transmission fields, so re-decoding would not add TransmissionStyle.

## 2. Ground-truth caveats (read before validating any rule against it)

1. **About 21% of today's vPIC "confirmed manuals" look like vPIC
   model-level defaults, not facts about each VIN.** In 17 vPIC
   make/model/year cells, vPIC returns *manual* for every decoded live VIN
   (≥ 5 each, no automatics): 847 of the 4,047 `vin` manuals
   (`baseline_summary.json` → `vpic_manual_credibility`,
   `uniform_manual_cells`). EPA lists an automatic for every one of these
   cells (`epa/vehicles.csv`, the same year/make/displacement). A live vPIC
   re-decode returns the same values (`vpic_full_sample.json`), so this is
   vPIC data and not our cache. The large cells:

   | vPIC cell | decodes, all "manual" | EPA lists |
   |---|---:|---|
   | 2008 Hyundai Elantra 2.0 | 165 | Automatic 4-spd, Manual 5-spd |
   | 2007 Chevrolet HHR 2.2/2.4 | 120 | Automatic 4-spd, Manual 5-spd (both engines) |
   | 2008 Hyundai Sonata 2.4 (the 3.3 V6 decodes as "5-spd", no style) | 93 | 2.4: Automatic 4-spd, Manual 5-spd; 3.3: Automatic 5-spd only |
   | 2008 Hyundai Accent 1.6 | 90 | Automatic 4-spd, Manual 5-spd |
   | 2008 / 2007 Honda Fit 1.5 (VDS GD37 *and* GD38) | 88 / 78 | Automatic 5-spd, Automatic (S5), Manual 5-spd |
   | 2008 Kia Spectra 2.0 / Rio 1.6 | 72 / 41 | Automatic 4-spd, Manual 5-spd |
   | 2002 Dodge Neon 2.0, decoded as **6-spd** manual | 32 | Automatic 4-spd, Manual **5**-spd (EPA lists no 6-speed) |
   | 2008 Hyundai Tiburon 2.0 | 20 | Automatic 4-spd, Manual 5-spd |
   | 1999 / 2000 Mercedes SLK230 | 14 / 7 | Automatic 5-spd, Manual 5-spd |

   The small cells (1988 Wrangler, 1986 Civic, 2001-02 Saturn SL, 2002 Vue)
   may be real. EPA lists only a manual for the 1988 Wrangler 2.5. The app
   badges all of these cars as Manual today. **Hub decision needed:**
   whether to exclude uniform-manual cells from the badge. That needs a
   scraper/app change, which is integration work, so it is not made here.
   For validation, treat a `uniformCell` line as unlabelled, not as a
   positive.
2. **The VIN-bearing ground truth is all vPIC.** Every listing line comes
   from Ace Jacksonville and has no VIN. So no VIN rule can be checked
   against an independent label on the lots. A rule derived from Part 565
   filings and checked against vPIC (which is built from those filings) is
   partly circular. Use EPA and manufacturer sources as the independent
   check.
3. **Thin positives where the opportunity is largest.** Ford has 2 manual
   lines, Toyota 4, Nissan 3, Dodge 35, GMC 0, Mazda 1, BMW 9. Known-
   transmission lines are concentrated in makes whose VINs vPIC already
   decodes: Honda 21,232, Subaru 4,509, Acura 3,567, Volkswagen 2,571,
   Chevrolet 7,463 (Cruze 3,615). For those three makes the 99.5% agreement
   bar would rest almost entirely on automatics. Report negatives and
   positives separately.
4. **`uniformCell = auto`: 450 cells.** Most are genuinely automatic-only
   models (Odyssey, Pilot), but a cell for a model that also had a manual is
   the same kind of default in reverse. A rule that says *manual* on such a
   car is not automatically wrong.
5. **Other vPIC oddities:** "Automated Manual Transmission (AMT)" on
   154 Cobalts (no speeds) and on 4-speed Subaru Legacy/Outback (159). The
   app does not count these as manual, which is correct either way. 209 lines
   have speeds but no style (`other`), for example 2008 Sonata V6 "5-spd" and
   Kia Soul "6-spd". Treat these as unknown, not as automatic.
6. Existing post-processing is already applied to the ground truth by
   `_correct_vpic`: `VPIC_TRANS_FIXES` (2005 LR3 5→6-spd automatic) and
   `VIN_TRIM_PATTERNS` (RSX Type-S/Base, Camry Hybrid/Gas trims). Neither
   creates or removes a manual.

## 3. Where the vPIC decodes live (and what they do not keep)

There is **no cache of full vPIC decodes**. Every store holds the compact
payload that `_vpic_row_to_decode` builds:

| Store | Path | Coverage |
|---|---|---|
| CI decode cache | `scraper/inventory_history.db`, table `vin_decodes(vin, payload JSON, trim_quality, decoded_at)` | every VIN the scans have decoded. It persists only in the GitHub Actions cache (`scan.yml`, `actions/cache@v4`) and cannot be downloaded. The local copy here is an empty schema (0 rows) |
| Committed backup | `docs/data/vin_decodes.json.gz` (`{vin: payload, "_exportedAt": "2026-11-04T03:53:13Z"}`) | 459,486 payloads: 354,499 with engine/transmission, 59,314 with a non-empty transmission. It covers 269,450 of the 280,030 unique live VINs. It is re-exported only after ≥ 20,000 new rows (`db.export_vin_decodes_gz`) |
| Published subset | `docs/data/inventory_live.json` `vpic` side table (row → trim, trimQuality, series, driveType, mismatch; 262,553 rows) and `vehicle_extras.json` (engine, trans, transSrc) | only cars with UI-relevant values |

Payload fields and how they map to raw vPIC fields:

| vPIC field | Kept? | Where |
|---|---|---|
| TransmissionStyle + TransmissionSpeeds | merged | `transmission` = `"{speeds}-spd {style}"`. Both parts can be recovered (`speeds` = the leading N, style = the rest) |
| Trim, Series, DriveType, BodyClass | yes | `trim` (+ `trimQuality`), `series`, `driveType`, `bodyClass` |
| DisplacementL, EngineCylinders | rounded | `engine` = `"{DisplacementL:.1f}L {EngineCylinders}-cyl"` |
| FuelTypePrimary | only when not gasoline | `engine` suffix |
| Make, Model, ModelYear | yes | `make`, `model`, `modelYear` |
| **EngineModel**, Trim2, Series2, EngineConfiguration, EngineHP, OtherEngineInfo, Turbo, ValveTrainDesign, Doors, GVWR, Plant*, VehicleType, ErrorCode/ErrorText | **no** | not stored anywhere |

A full decode has 154 fields (`vpic_full_sample.json`: 6 VINs from the
suspect cells, fetched live 2026-11-05). EngineModel is often the
distinguishing field, for example Fit `L15A1` and HHR `L61/LBZ`. To get it
for the lots, the scraper must re-decode: 280,030 unique live VINs / 50 per
`DecodeVINValuesBatch` POST ≈ 5,600 calls. Store the extra fields in their
own table rather than changing the shipped payload. That is a scraper
(integration) change and is not made here.

## 4. EPA fueleconomy.gov data

- **Download:** <https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip>,
  fetched once 2026-11-05 with python `requests`. Last-Modified
  2026-09-29 19:47 GMT, 2,212,193 bytes, sha256
  `33d32caa0343cdb11c47be631e8a80b7ed7c351ee8503646a4e96485bd67b22f`.
  Extracted to `scraper/manual_detect/epa/vehicles.csv` (21.8 MB). Both
  files are gitignored (`scraper/manual_detect/.gitignore`: `epa/`).
- **Shape:** 50,407 rows × 84 columns, model years 1984-2027 (about
  1,100-1,350 rows a year). Each row is one certified configuration
  (model × engine × transmission × drive), not a trim.
- **Columns relevant to transmission:**

  | Column | Content |
  |---|---|
  | `year`, `make`, `model`, `baseModel` | model year; make; model name with drive/body/engine qualifiers (`F150 Pickup 2WD`, `Xterra V6 2WD`); family name (`F150`, `Legacy/Outback`) |
  | `trany` | 41 values. `Manual N-spd` (incl. `Manual 4-spd Doubled`); `Automatic N-spd`; `Automatic (SN)` = automatic with select-shift; `(AMN)` / `(AM-SN)` = automated manual, **DCTs included**; `(AV)` / `(AV-SN)` / `Automatic (variable gear ratios)` = CVT; `(A1)` = single-speed (EV) |
  | `trans_dscr` | 53 codes, mostly blank. `CLKUP` (lock-up), `SIL`, `2MODE`/`3MODE`, `Creeper` (a manual creeper gear), `EMS`, `DC/FW` |
  | `displ`, `cylinders` | litres to 0.1, cylinder count. These compare directly with our vPIC `engine` text |
  | `drive` | `Front-Wheel Drive`, `Rear-Wheel Drive`, `All-Wheel Drive`, `4-Wheel or All-Wheel Drive`, `4-Wheel Drive`, `Part-time 4-Wheel Drive`, `2-Wheel Drive`, blank (1,186) |
  | `eng_dscr` | 629 free-text engine notes (`SIDI`, `(FFS)`, `(FFS,TRBO)`, `GUZZLER`, `CA model`, `FFV`, engine codes) |
  | `VClass` | 34 size classes. Pickups and SUVs carry 2WD/4WD |
  | `atvType`, `fuelType`, `fuelType1`, `tCharger`, `sCharger`, `startStop`, `evMotor` | hybrid/EV/diesel/FFV flags, turbo/supercharger, stop-start |
  | `id`, `engId`, `mfrCode`, `createdOn`, `modifiedOn` | row identity and provenance (cite `id` in rules) |

  Class split of rows: automatic 32,833, manual 13,298, CVT 2,185,
  automated manual/DCT 2,080, blank 11.
- **Not covered by EPA:** vehicles over 8,500 lb GVWR (and MDPVs before
  2011). That is 6,103 lot cars in heavy-duty models (F-250/F-350/Super
  Duty, E-250/E-350, Express/Savana 2500/3500, Ram 2500/3500, Silverado/
  Sierra 2500). EPA cannot speak for them.

### Our names compared with EPA's (`epa_profile.json`)

- **Makes:** every feed make with ≥ 50 cars matches an EPA make
  case-insensitively. EPA has both `MINI` and `Mini`, and both `smart` and
  `Smart`. AMC maps to `American Motors Corporation`. Feed makes absent
  from EPA (Datsun, MG, Triumph, Freightliner, International, trailers,
  motorcycles) total 173 cars. 1,944 lot cars predate 1984, EPA's first
  year.
- **Models:** 315,650 of 331,505 cars from 1984 on (95.2%) match some EPA
  row of the same year and make. By the strongest name match: exact
  158,423; drive/body suffix stripped 128,807 (`F150 Pickup 2WD`,
  `Focus FWD`, `Escape AWD`); `baseModel` 12,708 (`Tahoe 1500 2WD` →
  `Tahoe`); slash-split 7,905 (`Caravan/Grand Caravan 2WD`,
  `Voyager/Town and Country`, `Liberty/Cherokee`); alias 5,256 (`Mazda3` →
  `3`, GM `Silverado 1500` → `Silverado C15/K15`); punctuation 1,822
  (`F-150` → `F150`, `&` → `and`); parenthetical 729 (`Legacy AWD (incl.
  Outback)`). Using vPIC's model name instead matches 93.6% (251,960 of
  269,142), so the feed's canonical names match slightly better.
- **Largest unmatched feed models:** E-150/250/350, F-250/350 (Super Duty),
  Express 2500/3500 (heavy duty, see above), Yukon XL, Mercedes `M-Class`
  (EPA uses `ML350` etc.), Versa Note, Captiva Sport, C/K 1500, Dodge `Ram
  Pickup` / `Ram` / `1500 Pickup` blobs, Nissan `Pickup`, `Blazer S10/Jimmy
  S15`, Mazda `B-Series` (EPA `B2300`...).
- **Pitfall found while matching:** a match must take the **union** of
  every EPA row that answers to the name, not only the closest name.
  Examples: 2004 `Xterra 2WD` is 2.4/manual only, but `Xterra V6 2WD` has
  automatics; 2007 `G6` 3.9 is manual only, but `G6 GT/GTP Convertible` 3.9
  is automatic. The first version of the profile took only the closest name
  and produced false "manual-only" cells (151 2004 Xterras). The current
  profile takes the union.

### Size preview of the EPA sole-offering track (not a rule)

Each 1984+ lot car is placed in an EPA cell by year/make/model (union match)
plus vPIC displacement and cylinders, plus drive when vPIC gives one:

| Cell state | Cars |
|---|---:|
| EPA lists only manuals | **397** (Dodge 72, Ford 53, Chevrolet 48, Honda 44, Isuzu 31, Jeep 30 ...) |
| manual and automatic both listed | 113,715 |
| no manual listed | 136,982 |
| no vPIC engine (no VIN / not decoded / no displacement) | 60,340 |
| engine not in the EPA rows | 4,216 |
| model not matched | 15,855 |

Against the known-transmission lines, the 397-car "manual-only" cells hold
63 manual and 4 non-manual lines (94%; the misses are 2012-13 Impreza /
Outback Sport CVTs, a name-union gap). That is below the 99.5% bar, so
cell rules need tighter scoping (trim/body) and their own validation. The
track is also small: most of the opportunity sits in mixed cells, where
only VIN-encoded transmission (track 1) or a manual-only trim (track 3) can
decide. Top cells that look right on spot check: Civic 2.0 (2003, 2006-09) and
2012 Civic 2.4 (both Si), 2007-09 Caliber 1.8, 1996-99 Dakota 2.5,
1995-2000 Metro 1.0, 2008 Mazdaspeed3, 1991-92 Wrangler 2.5. Spot checks are
not validation.

## 5. Files

| File | Committed | What |
|---|---|---|
| `build_baseline.py` | yes | ground truth, per-make counts, vPIC cell uniformity |
| `epa_profile.py` | yes | EPA columns, name matching, sole-offering size preview |
| `baseline_summary.json` | yes | totals, `per_make`, `vpic_manual_credibility`, `uniform_manual_cells`, cache coverage |
| `vpic_cells.json` | yes | `make|model|year` → [manual, non-manual, blank] decodes over live cars |
| `epa_profile.json` | yes | vocabularies, make map, match levels, unmatched list, preview cells |
| `vpic_full_sample.json` | yes | 6 full (154-field) vPIC decodes from the suspect cells |
| `ground_truth.jsonl` | no (gitignored, rebuild) | 48,996 known-transmission cars |
| `epa/vehicles.csv(.zip)` | no (gitignored) | raw EPA download |
