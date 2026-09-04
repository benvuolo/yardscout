# Price Validation Report — UNOBTANIUM_DB vs. Real-World Market

**Date:** 2026-09-02
**Scope:** Top 55 database entries (by live-inventory frequency × claimed high value), covering the ~50 parts that carry the product's credibility.
**Author:** Automated accuracy audit (skeptical pass, per owner request).

---

## TL;DR — Overall verdict

**The database is broadly honest. It is NOT inflated.** Of the 55 highest-exposure entries audited:

| Classification | Count | % |
|---|---|---|
| ACCURATE (DB range overlaps observed market range) | 47 | 85% |
| UNDERSTATED (DB is *below* what parts actually fetch) | 5 | 9% |
| INFLATED (DB high substantially above observed — **corrected in this PR**) | 3 | 5% |
| UNVERIFIABLE | 0 | 0% |

Evidence confidence: **good** (multiple independent price points) for 41 entries, **thin** (single source, proxy vehicle, or asking-price-only) for 14 entries. No entry had zero evidence, so nothing was left unverifiable — but thin-confidence rows are flagged below and are worth a manual spot-check before marketing claims lean on them.

If anything, the calibration layer (`_resale_sold_calibrate`, which shaves 10–30% off the raw anchors before display) makes the product *conservative*: several flagship parts (Focus Recaros, Raptor grilles, Mustang Recaros, CTS-V Brembos) sell used for well above what the app promises.

### Methodology and honest caveats

- **What users see:** the app displays *calibrated* ranges, not the raw `low`/`high` anchors in `UNOBTANIUM_DB`. All comparisons below are against the **displayed (calibrated) range**, since that is the advertised claim. Corrections were applied to the raw anchors so the displayed output lands inside observed evidence.
- **eBay sold listings were bot-blocked** (captcha on `LH_Sold=1`, HTTP 403 on active search). Per instructions I backed off after two attempts. Evidence therefore comes from web search: salvage-yard/recycler listed prices (Automotix, LKQ-network yards, PartsHotlines, 4u.parts, etc.), enthusiast-forum for-sale threads (including *sold* threads), and new-OEM dealer prices as upper bounds.
- **Asking vs. sold:** most recycler prices are asks, which typically run above realized private-sale prices. Where forum *sold* data existed it was weighted heavier. This bias means ACCURATE calls are safe, and UNDERSTATED calls are conservative — but a couple of "accurate" calls could be flattered by ask-price data (flagged inline).
- **Condition sensitivity:** electronics (clusters, touchscreens, head units, amps), headlights (hazing, tab breakage), and body/paint parts (bumpers, grilles, tailgates, lips) have inherently wide real ranges — a broken tab or wrong paint code can halve the price. These rows are marked ⚠ below; wide DB bands there are appropriate, not evasive.

---

## Corrections applied (the 3 INFLATED entries)

Raw anchors changed in `UNOBTANIUM_DB`; displayed = post-calibration range users see.

| Part (model) | Displayed before | Displayed after | Raw anchor change | Evidence |
|---|---|---|---|---|
| ST/RS Intercooler (Ford Focus) | $85–185 | $50–120 | 100–250 → **60–160** | Forum *sold* prices $20–100 ([focusst.org: "sold mine for 20 bucks"](https://www.focusst.org/threads/does-my-replaced-original-intercooler-have-any-value.173779/), [$60 FS thread](https://www.focusst.org/threads/fs-oem-intercooler-for-mk3-5-focus-st.175949/), [$100 parts-lot](https://www.focusst.org/threads/bunch-of-stock-parts.178909/)); warrantied retail tops out ~$230 (B-Parts). Old high of $185 displayed was ~2–3× typical realized sale. Note: at the $95 yard cost this part is now marginal — that is the honest picture. |
| Sport Twin-Turbo Intercooler (Ford Fusion Sport 2.7EB) | $130–260 | $85–185 | 150–350 → **100–250** | Used stock unit asked at $100 on the owners' forum ([fusionsportforums.com](https://www.fusionsportforums.com/threads/2017-2019-ford-fusion-sport-lincoln-mkz-front-mount-intercooler-2-7-turbos-and-brand-new-ultimate-intercooler.21971/)); **new OEM is $204–245** ([fordpartsdeal, G3GZ-6K775-A](https://www.fordpartsdeal.com/oem/ford~cooler-assembly-engine-charge-air~g3gz-6k775-a)). A used part advertised above the new-OEM price is indefensible. |
| GLI Brembo Calipers, set (VW Jetta) | $310–570 | $155–380 | 350–750 → **175–500** | Used GTI/GLI 4-caliper sets: $400–430 ask ([Redline Auto Parts](https://www.redlineautoparts.com/volkswagen/2015-2021-mk7-gti/2015-2018-volkswagen-mk7-gti-oem-brake-calipers-red-52k-set-of-4-m7004/)), $400 private for all four ([Shoppok Chicago](https://www.shoppok.com/chicago/a,43,641268,GTI-GLI-brakes--150.htm)), front pairs $135–245 ([VAGParts](https://vagparts.co.nz/vw-volkswagen-audi-skoda-golf-mk5-mk6-gti-polo-scirocco-a3-2005-2009-front-brake-caliper-312mm-red-oem-genuine-oem-ate-left-right-or-pair-used/)). Old displayed low of $310 exceeded most complete-set sale prices. (Also worth a naming review later: standard GLI calipers are ATE, not Brembo — only 2019+ 35th/Autobahn got the Golf-R big brakes. Name untouched per scope.) |

---

## UNDERSTATED entries (no change applied — flagged for owner)

These are the opposite problem: the app under-promises. No edits made (understating isn't false advertising), but raising these would make the product *more* accurate:

| Part (model) | Displayed | Observed used market | Evidence |
|---|---|---|---|
| Recaro Seats pair (Focus ST/RS) | $350–685 | $950–2,000 | [Forum sale $950 w/ rears](https://www.focusst.org/threads/14-recaro-grey-focus-st-seats-front-and-back-set.170822/), [$1,600–2,000 pairs](https://www.shoppok.com/sacramento/a,43,551103,2017-ford-focus-recaro-seats-st3-leather-20-k-miles.htm) |
| Recaro Seats PP/GT350 (Mustang) | $440–910 | ~$1,750–3,500 retail asks; $2,350 forum | [GT350 front pair $1,750](https://oemperformancespareparts.com/product/ford-mustang-shelby-gt350-oem-recaro-seats/), [Mustang7G $2,350 sold](https://www.mustang7g.com/forums/threads/recaro-seat-set.176310/). One $350 take-off outlier exists — condition/urgency matters. |
| Raptor Grille (F-150) | $175–390 | $525–600 | [Kosiski recycler $525](https://kosiski.com/parts/FORD/FORD_F150_RAPTOR/CAA1476/2013/GRILLE/1005202188), [forum: "$550 on eBay"](https://www.fordraptorforum.com/threads/grill-replacement.104548/), [Tremor forum $550 sold](https://www.f150tremor.com/threads/sold-oem-21-23-raptor-grille.5739/) |
| ST3/RS HID Headlights pair (Focus) | $220–340 | $400–1,300/pair ($200–650/side) | [Salvaged Motorsports set $600](https://www.salvagedmotorsports.com/product/13-14-ford-focus-st-halogen-headlight-rh-lh-set-st3-hid/), [recycler $650/side](https://picclick.ca/Used-Right-Headlight-Assembly-fits-2014-Ford-Focus-366470693036.html), forum consensus ~$200/side floor |
| Brembo Calipers set (Cadillac CTS-V) | $350–685 | $575–1,300 (typical $800–1,200) | [Recycler aggregate: sets $575–1,400](http://communitychevy.com/vwi545ea0ecdb70f/cts-v-calipers/) |

---

## Full audit table (all 55 rows)

Displayed = calibrated range shown to users. Freq = vehicles in current live inventory carrying the part. ⚠ = condition-sensitive category.

| # | Part — Vehicle | Freq | Displayed | Observed used range | Verdict | Confidence |
|---|---|---|---|---|---|---|
| 1 | Recaro Seats (pair) — Ford Focus ST/RS | 2,967 | $350–685 | $950–2,000 | **UNDERSTATED** | good |
| 2 | Si/Type R Seats (pair) — Honda Civic | 3,519 | $265–530 | $240–750 | ACCURATE | good |
| 3 | 3rd Row Seat — Chevy Tahoe | 4,473 | $175–340 | $300–600 (07–14 gen) | ACCURATE (conservative) | good |
| 4 | 3rd Row Seat — Ford Expedition | 4,473 | $175–340 | proxy: Tahoe/Explorer $190–600 | ACCURATE | thin |
| 5 | Raptor Grille — Ford F-150 | 3,608 | $175–390 | $525–600 | **UNDERSTATED** | good |
| 6 | RS Brake Calipers (set) — Ford Focus RS | 2,880 | $265–455 | $400–910/set | ACCURATE (conservative) | good |
| 7 | Headlights (clear) ⚠ — Toyota Camry | 12,584 | $40–80 | $28–180/side (halogen) | ACCURATE | good |
| 8 | Headlights (clear) ⚠ — Chevy Silverado | 12,584 | $40–80 | generic halogen $28–180 | ACCURATE | thin |
| 9 | 3rd Row Seat — Honda Pilot | 3,717 | $130–265 | $189–246 | ACCURATE | good |
| 10 | 3rd Row Seat — Ford Explorer | 3,717 | $130–265 | $192–392 | ACCURATE | good |
| 11 | Power-Fold Tow Mirrors (pair) — Ford F-150 | 2,124 | $225–430 | $450–1,200 (2021+); older gens lower | ACCURATE / understated for new gens | good |
| 12 | Headlights (clear) ⚠ — Honda Accord | 8,956 | $40–90 | halogen $28–180 | ACCURATE | good |
| 13 | Stow-N-Go 2nd Row (each) — Dodge Grand Caravan | 2,341 | $175–340 | $135–500/seat ($600–1,000/pair kits) | ACCURATE | good |
| 14 | Stow-N-Go 2nd Row (each) — Chrysler T&C | 2,341 | $175–340 | same as above | ACCURATE | good |
| 15 | GLI Brembo Calipers (set) — VW Jetta | 1,385 | was $310–570 → now $155–380 | $135–450/set | **INFLATED → corrected** | good |
| 16 | Tailgate (clean) ⚠ — Dodge Ram 1500 | 2,532 | $130–305 | $50 (rough) – $900+ (2017+ grade A) | ACCURATE (wide by nature) | good |
| 17 | Power Sliding Door Motor — Toyota Sienna | 2,651 | $135–275 | $245–400 | ACCURATE (conservative) | good |
| 18 | Power Sliding Door Motor — Honda Odyssey | 2,651 | $135–275 | $245–400 | ACCURATE (conservative) | good |
| 19 | Sport Seats (pair) — BMW 3-Series E90 | 1,353 | $265–530 | $360–700 | ACCURATE | good |
| 20 | Sport Front Lip ⚠ — Honda Accord | 4,338 | $70–155 | new OEM lip $95; used likely $50–120; underbody spoiler new $296+ | ACCURATE (borderline high — see note) | **thin** |
| 21 | ST3/RS HID Headlights (pair) — Ford Focus | 1,818 | $220–340 | $400–1,300/pair | **UNDERSTATED** | good |
| 22 | SRT/Scat Brembo Calipers (set) — Dodge Charger | 894 | $350–685 | $600–775/set (to $1,900 w/ rotors) | ACCURATE (conservative) | good |
| 23 | Sport Twin-Turbo Intercooler — Ford Fusion | 2,256 | was $130–260 → now $85–185 | used ~$100; new OEM $204–245 | **INFLATED → corrected** | good |
| 24 | N/Sport Front Bumper Assembly ⚠ — Hyundai Elantra | 1,671 | $175–350 | used assemblies $625–774; new aftermarket $265–300 | ACCURATE (conservative) | good |
| 25 | Gauge Cluster / IPC ⚠ — Honda Accord | 4,654 | $50–120 | $75–185 | ACCURATE | good |
| 26 | ST/RS Intercooler — Ford Focus | 2,881 | was $85–185 → now $50–120 | forum sold $20–100; retail ≤$230 | **INFLATED → corrected** | good |
| 27 | Heated Leather Front Seats (pair) — Chevy Impala | 1,835 | $130–265 | $156–524/seat (recycler ask) | ACCURATE | good |
| 28 | ST/RS Steering Wheel — Ford Focus | 2,881 | $90–165 | $75–241 | ACCURATE | good |
| 29 | Si Front Lip (OEM) ⚠ — Honda Civic | 3,519 | $70–135 | $130–225 (HFP, forum sold ~$130–200) | ACCURATE (conservative) | good |
| 30 | Comfort Seats / Multi-Contour (pair) — BMW 5-Series | 620 | $310–685 | $494–900 | ACCURATE | good |
| 31 | SHO Turbo / Intercooler Parts — Ford Taurus | 1,138 | $170–370 | used turbos ~$225/ea; new pair $580–1,050; reman $780+/ea | ACCURATE | thin |
| 32 | Brembo Calipers (set) — Cadillac CTS-V | 610 | $350–685 | $575–1,300/set | **UNDERSTATED** | good |
| 33 | Instrument Cluster ⚠ — Honda Civic | 3,792 | $45–110 | proxy: Accord clusters $75–185 | ACCURATE | thin |
| 34 | Panoramic Sunroof Glass ⚠ — Hyundai Sonata | 1,484 | $135–275 | $125 (11–15 gen) – $275–800 (2020+) | ACCURATE | good |
| 35 | Headlights (clear) ⚠ — Ford Explorer (≤2005) | 4,767 | $40–85 | generic halogen $28–180 | ACCURATE | thin |
| 36 | Headlights (clear) ⚠ — Ford Explorer (06–10) | 4,767 | $40–85 | generic halogen $28–180 | ACCURATE | thin |
| 37 | Headlights (clear) ⚠ — Nissan Altima | 4,767 | $40–85 | generic halogen $28–180 | ACCURATE | thin |
| 38 | Power Window Master Switch ⚠ — Honda Accord | 4,654 | $30–85 | $45–150 (typ. $58–92) | ACCURATE | good |
| 39 | iDrive / Navigation Head Unit ⚠ — BMW 3-Series | 962 | $180–405 | $120–443 (CIC sets ~$295) | ACCURATE | good |
| 40 | Brembo Front Calipers (Type-S) — Acura TL | 803 | $220–455 | $240–390/pair | ACCURATE | good |
| 41 | Headlights (clear) ⚠ — Honda Civic | 4,743 | $35–75 | generic halogen $28–180 | ACCURATE | thin |
| 42 | Headlights (clear) ⚠ — Nissan Sentra | 4,743 | $35–75 | generic halogen $28–180 | ACCURATE | thin |
| 43 | Brembo Calipers (set, sport pkg) — Infiniti G35 | 662 | $265–530 | $509–650 calipers-only; $750–1,100 kits | ACCURATE (conservative) | good |
| 44 | Headlights (clear) ⚠ — Chevy Equinox | 3,438 | $50–100 | generic halogen $28–180 | ACCURATE | thin |
| 45 | Headlights (clear) ⚠ — Ford Escape | 3,438 | $50–100 | generic halogen $28–180 | ACCURATE | thin |
| 46 | Headlights (clear) ⚠ — Kia Optima | 3,438 | $50–100 | generic halogen $28–180 | ACCURATE | thin |
| 47 | OEM HID Headlights ⚠ — Infiniti G35 | 1,484 | $125–225 | $130–350/side | ACCURATE | good |
| 48 | Gauge Cluster ⚠ — Dodge Ram | 2,166 | $70–150 | $35–148 (98–05); $125–250 (2013+) | ACCURATE (low end slightly rich for old trucks) | good |
| 49 | Sony Audio Amp + Speakers ⚠ — Ford Fusion | 2,403 | $70–135 | amp alone $120–203; sub $100 | ACCURATE (conservative) | good |
| 50 | Headlights (clear) ⚠ — Subaru Legacy | 3,358 | $45–95 | generic halogen $28–180 | ACCURATE | thin |
| 51 | Recaro Seats (PP/GT350) — Ford Mustang | 350 | $440–910 | $1,750–3,500 (one $350 take-off outlier) | **UNDERSTATED** | good |
| 52 | MyLink Touchscreen ⚠ — Chevy Cruze | 1,892 | $90–165 | $80–300 | ACCURATE | good |
| 53 | MyLink Touchscreen ⚠ — Chevy Sonic | 1,892 | $90–165 | proxy: Cruze $80–300 | ACCURATE | thin |
| 54 | Turbo Intercooler + Pipes — Chevy Cruze | 2,074 | $70–150 | $120–350 (recycler) | ACCURATE (conservative) | good |
| 55 | Stow-N-Go 3rd Row — Dodge Grand Caravan | 1,633 | $90–190 | $145–380 | ACCURATE (conservative) | good |

---

## Per-part evidence notes and links

Grouped where multiple DB rows share one market (e.g. the same part across sibling models).

### Seats (condition-sensitive: bolster wear, airbag status, rips)

- **Focus ST/RS Recaros** — UNDERSTATED. Sold/asking: $950 (grey pair + rears, [focusst.org sold thread](https://www.focusst.org/threads/14-recaro-grey-focus-st-seats-front-and-back-set.170822/)), $1,600 pair / $2,000 w/ rears ([Shoppok](https://www.shoppok.com/sacramento/a,43,549558,2017-ford-focus-recaro-seats-ford-focus-fiesta-st.htm)), $950–1,050 single retail ([autoultraparts](https://autoultraparts.com/shop/recaro-ford-focus-seat/)). Sample: 4+.
- **Civic Si seats** — ACCURATE. $450–500 FG2 pairs ([hamedsafari](https://hamedsafari.com/products/06-11-honda-civic-si-fg2-coupe-front-seats-pair-left-right-s/12428157/), [wolfsburgautoparts eBay listing](https://howto.tutorialkita.net/06-11-honda-civic-si-fg2-coupe-front-seats-pair-left-right-sport-cloth-07-08-09-WldARFobRkNFVkJZ)), $240–750 EM1-era sets ([HQ Automotive aggregate](https://www.hqautomotive.com/mfq55344c6e0f536/99-civic-si-seats/)), $600 10th-gen pair. Sample: 8+.
- **Tahoe/Suburban 3rd row** — ACCURATE-conservative. 07–14 gen (bulk of yard inventory): $304–575 ([Community Chevy aggregate](http://www.communitychevy.com/vwi545ea0ecdb70f/tahoe-third-row-seats/)); 2015+ leather $500–1,400 ([oemcarandtruckseats $1,399](https://www.oemcarandtruckseats.com/products/gm-chevy-tahoe-suburban-yukon-3rd-row-leather-seat-2015-2016-2017-2018-2019-2020-1640i)). Expedition row proxied to this + Explorer data (thin).
- **Pilot / Explorer 3rd row** — ACCURATE. Pilot $189–246, Explorer $192–392 ([Automotix Pilot](https://automotix.net/usedautoparts/2019-honda-pilot-third_row_seat-inventory.html), [Automotix Explorer](https://www.automotix.net/usedautoparts/2021-ford-explorer-third_row_seat-inventory.html)). Sample: 20+ listings.
- **Stow-N-Go 2nd row (each)** — ACCURATE. $135 recycler single ([St James](https://stjamesautoparts.com/parts/DODGE/CARAVAN/J1432/2017/SEAT_REAR/1569604)), $600 CAD pair kit ([Kijiji/VanGuard](https://www.kijiji.ca/v-other-auto-parts-and-accessories/city-of-toronto/complete-conversion-stow-n-go-seats-used/1677801375)), $1,000 pair ([AMS Vans](https://www.amsvans.com/mobility-equipment/factory-oem-minivan-products/stow-and-go-seats-chrysler-dodge-minivans)). Per-seat $135–500.
- **Stow-N-Go 3rd row** — ACCURATE. $145–380 across years ([Automotix 2009](https://automotix.net/usedautoparts/2009-dodge-caravan-third_row_seat-inventory.html), [2018](https://automotix.net/usedautoparts/2018-dodge-caravan-third_row_seat-inventory.html), [2020](https://automotix.net/usedautoparts/2020-dodge-caravan-third_row_seat-inventory.html)); leather $270–295 (Cornell's, Veldman's). Sample: 30+.
- **BMW E90 sport seats** — ACCURATE. $494 ([Prussian Motors](https://prussianmotors.com/bmw-e90-3-series-4dr-front-sports-seat-pair-black-leather-heat-mem-pwr-2006-2011/)), $600 pair w/ bad rail motor, $700 ([recycleBMWs](https://recyclebmws.com/products/bmw-e90-3-series-lci-heated-leather-sport-seats-pair-black-52107246857.html)).
- **BMW F10 comfort seats** — ACCURATE. $494–715 pairs ([Prussian $715](https://prussianmotors.com/14-16-bmw-f10-5-series-f07-front-comfort-seat-pair-ivory-white-napa-leather-oem/), [recycleBMWs $600](https://recyclebmws.com/products/bmw-f07-f10-f11-5-series-front-seats-leather-power-lumbar-heated-52107230653.html), [$650 eBay full set](https://www.ebay.ca/itm/223692283846)).
- **Impala heated leather pair** — ACCURATE. $156–524 per seat recycler ask ([Automotix](https://automotix.net/usedautoparts/2017-chevrolet-impala-front_seat-inventory.html)); $1,100–1,200 full interior local ([Shoppok](https://www.shoppok.com/atlanta/a,43,514172,Chevy-Impala-Seats-Leather-Front-Rear-Chevrolet-Complete-LTZ-Premier--1-100.htm)).
- **Mustang Recaro (PP/GT350)** — UNDERSTATED. $1,750 GT350 fronts, $1,800–3,000 sets ([oemperformancespareparts](https://oemperformancespareparts.com/product/ford-mustang-shelby-gt350-oem-recaro-seats/), [thepartfarms](https://thepartfarms.com/product/2019-ford-mustang-gt-leather-recaro-seats/)), $2,350 forum sold ([Mustang7G](https://www.mustang7g.com/forums/threads/recaro-seat-set.176310/)). One $350 take-off private sale shows the floor when a seller wants them gone.

### Brakes

- **Focus RS Brembo set** — ACCURATE. $800 set of 4 ([brakesi](https://www.brakesi.com/products/2016-2017-2018-ford-focus-rs-brembo.html)), £384 set ([Proper Parts](https://properparts.co/products/ford-mk3-focus-rs-brembo-brake-caliper-set)), salvage singles $175–910 ([Metro Auto Salvage](https://metroautosalvageinc.com/parts/FORD/FOCUS_RS/K25047/2017/CALIPER/1-800-252-5831)).
- **Charger SRT/Scat Brembo set** — ACCURATE-conservative. $600–775 caliper sets ([bigcatautosalvage $601](https://picclick.ca/2018-Dodge-Charger-Scat-Pack-Oem-Brake-Caliper-178245860949.html), [$708](https://picclick.ca/2015-2023-Dodge-Charger-Scat-Pack-64l-Brembo-Brake-358569147590.html), [$775](https://picclick.ca/%85-06-20-OEM-Dodge-Charger-Scat-Pack-Front-277923249961.html)); $1,900 with rotors.
- **CTS-V Brembo set** — UNDERSTATED. Sets $575–1,400, typical $800–1,200 ([recycler aggregate](http://communitychevy.com/vwi545ea0ecdb70f/cts-v-calipers/), [pro-touring: "used caliper set – $1,200"](https://www.pro-touring.com/threads/129002-Complete-CTS-V-ZL1-Brembo-Brake-system-including-calipers-rotors-adapter-brackets)).
- **Acura TL Type-S front Brembos** — ACCURATE. Pairs $240–390 ([racebuilds $350](https://www.racebuilds.com/l/2ay9cc/brembo-front-caliper-set-with-hardware-kit-2004-2008-acura-tl-type-s), [aggregate $269–389](http://communitychevy.com/vwi545ea0ecdb70f/acura-brembo-calipers/), honda-tech $350 shipped).
- **G35 Brembo set** — ACCURATE-conservative. $509–650 calipers-only ([metsen $509/650 OBO](https://metsen.com/pyckp/g863673.html)), $750–1,100 kits ([infinitipartsales $800](https://infinitipartsales.com/product/g35-brembo-brake-kit/), [On Point $1,100 w/ rotors](https://onpointparts.com/products/2003-infiniti-v35-g35-complete-brembo-brake-calipers-set-with-rotors-oem-23bcefk)).
- **VW GLI "Brembo" set** — **INFLATED, corrected** (see corrections table above).

### Headlights ⚠ (most condition-sensitive category: hazing, tabs, ballasts)

- **Generic halogen "clear, non-hazed"** (Camry, Accord, Civic, Silverado, Explorer, Altima, Sentra, Equinox, Escape, Optima, Legacy) — ACCURATE. Evidence: $28 rough / $56–77 decent / $99–180 very good ([PicClick/eBay Camry examples](https://picclick.ca/%85-2010-2011-Toyota-Camry-RH-Right-Passenger-Halogen-277963191815.html), [Tom's Foreign $99–120](https://www.tomsforeign.com/products/headlight-lamp-assembly-toyota-camry-2010-10-2011-11-right-1298896)). DB bands of $35–100 per-model sit inside this. Note these are per-side prices, and the DB doesn't specify side/pair — fine at these bands, but worth clarifying in UI copy someday. Confidence marked thin for models where I only had cross-model halogen evidence.
- **Focus ST3/RS HID pair** — UNDERSTATED (see table above).
- **G35 OEM HID** — ACCURATE. $130–185 (03–06), $300+ (07–08 adaptive) ([603 Auto Salvage](https://603autosalvage.com/Used-Auto-Parts/used-2006-infiniti-g35-headlamp-assembly-lh-oem/), [HK Auto $135](https://hkautoparts.com/product/2003-2005-infiniti-g35-headlamp-assembly-right-passenger-side-tested-xenon-oem/), [PartsBeast $300 sold](https://partsbeast.com/Infiniti/G35-Parts/Headlight/305590)).

### Body / exterior ⚠ (paint code and shipping-size sensitive)

- **Raptor grille** — UNDERSTATED (see table above).
- **Ram tailgate** — ACCURATE. $50 rough 2010 ([Highway Auto](https://highwayautoparts.com/parts/DODGE/DODGE_1500_PICKUP/Y17457/2010/DECKLID_TAILGATE/1797431/)) to $899–1,444 for 2017+ grade A/B ([Nationwide $899](https://nationwideautorecycling.com/parts/DODGE/DODGE_1500_PICKUP/U06018/2017/DECKLID_TAILGATE/630496/), [Maritime $1,201](https://maritimeauto.com/parts/DODGE/DODGE_1500_PICKUP/R103/2019/DECKLID_TAILGATE/96149)). DB band $130–305 is honest for the older, cosmetically average gates that dominate self-serve yards; understated for late-model clean gates.
- **Elantra N/Sport bumper** — ACCURATE-conservative. Used assemblies $625–774 ([Veldman's](https://veldmansautoparts.com/parts/HYUNDAI/ELANTRA/250076/2022/BUMPER_ASSY_FRONT/2724462), [TLS](https://www.tlsautorecycling.com/search/2021/hyundai/elantra/6257370.html)); new aftermarket cover $265–300 caps what a bare used cover fetches.
- **Accord Sport front lip** — ACCURATE but **thin and borderline**: new OEM lip (71110-T3V-A00) is only [$95](https://www.hondapartsnow.com/genuine/honda~spoiler~fr~bumper~lip~71110-t3v-a00.html), which argues the $155 displayed high is rich if the DB means that little chin strip; if it means the underbody sport spoiler (new $296–312), the band is fine. **Recommend the owner confirm which part is intended.**
- **Civic Si front lip (HFP)** — ACCURATE-conservative. Used HFP lips sold $130–200 on forums ([8thcivic: "both sold for $200 each"](https://www.8thcivic.com/threads/hfp-lip-kit-09-si.313705/), [CivicX $180–225](https://www.civicx.com/forum/threads/civic-hfp-oem-front-lip-dark-red.84307/), [honda-tech $130](https://honda-tech.com/forums/sale-10/oh-fg2-hfp-lip-kit-s2k-parts-2963744/)).

### Powertrain-adjacent / turbo

- **Focus ST intercooler** — **INFLATED, corrected** (see corrections table).
- **Fusion Sport 2.7EB intercooler** — **INFLATED, corrected** (see corrections table).
- **Cruze 1.4T intercooler + pipes** — ACCURATE-conservative. Used $120–350 ([Redline $120](https://redlineusedautoparts.com/public/index.php/part/17798643/intercooler-2014-chevrolet-cruze), [Automotix $135–274 / $255–350](https://automotix.net/usedautoparts/2015-chevrolet-cruze-intercooler-inventory.html)).
- **Taurus SHO turbo/intercooler parts** — ACCURATE (thin). Used pulled EcoBoost turbos ~$225/each (forum), new aftermarket pairs $580–1,050 ([Dale's $1,049](https://dalessuperstore.com/i-23918802-ecoboost-3-5l-turbo-set-for-explorer-flex-taurus-sho-790318-0003s-2010-2019-ford-explorer-flex-taurus-ecoboost-3-5l.html)), reman OEM $784–832/each ([Turbochargers Direct](https://turbochargersdirect.com/turbochargers-direct-remanufactured-oem-turbo-for-ford-explorer-flex-taurus-and-lincoln-3-5l-ecoboost-left-tur-102978-tdr/)). DB $170–370 brackets a yard-pulled untested turbo sensibly.

### Electronics ⚠ (programming/VIN-lock risk; ranges inherently wide)

- **Accord gauge cluster** — ACCURATE. $75–185 ([aletoparts](https://aletoparts.com/car/honda-accord-18-/instrument-panel/), [4u.parts $84–165](https://www.4u.parts/b/honda/instrument-cluster)). Civic cluster proxied to this (thin).
- **Ram gauge cluster** — ACCURATE. Old gens $35–148 ([HQ aggregate](https://www.hqautomotive.com/mfq55344c6e0f536/2001-dodge-ram-1500-cluster/)), 2013+ $125–250. DB low ($70) is a touch rich for 98–01 trucks; fine blended.
- **BMW iDrive/CIC head unit** — ACCURATE. $295 full set eBay ([listing](https://www.ebay.com.au/itm/376095881072)), £90–200 units, $443 Schmiedmann retail.
- **Cruze/Sonic MyLink touchscreen** — ACCURATE. $80 eBay display ([listing](https://www.ebay.ca/itm/236303655897)), $135–165 recycler ([Weber Bros](https://www.weberbrothersauto.com/product/audio-video-equipment-1000701536-tb189/)), $265 retail ([Biggs](https://www.biggsmotoring.com/products/2017-chevy-cruze-mylink-radio-touch-display-screen-42481577)). Note: many need dealer programming — sell_notes could mention this.
- **Accord power window master switch** — ACCURATE. $45–150, typical $58–92 ([PicClick/eBay aggregate](https://picclick.ca/2008-2012-Honda-Accord-Driver-Master-Power-Window-307010534420.html), [Autohub $45](https://www.autohub.express/product-page/window-switch-panel-master-2015-honda-accord-used-oem)).
- **Fusion Sony amp + speakers** — ACCURATE-conservative. Amp alone $120–203 ([cd4car $120–167](https://cd4car.com/2010-2017-ford-fusion-mercury-milan-oem-sony-audio-amplifier/), [Biggs $203](https://www.biggsmotoring.com/products/2010-2012-ford-fusion-sony-audio-amplifier-bl3t-18b849-ae)), Sony sub $100 ([aletoparts](https://aletoparts.com/detail/subwoofer-ford-fusion-mk5-13-sony/)).

### Mechanical / misc

- **Sienna/Odyssey power sliding door motor** — ACCURATE-conservative. $245–400 used ([Importapart $400](https://www.importapart.com/product/11-17-honda-odyssey-rear-driver-side-lh-sliding-power-door-motor-assembly-5168/), [4u.parts sold $292–337](https://www.4u.parts/c/rear-sliding-door-motor-right), BE FORWARD $245 landed); new OEM $532+.
- **F-150 power-fold tow mirrors** — ACCURATE for the 2004–2014 trucks that dominate yards; understated for 2015+/gen14 loaded mirrors which sell $650–1,200 ([forum sold $750](https://www.lightningerevforum.com/forum/threads/power-fold-mirrors-htd-360-blis-360-blis-xl-xlt-pf-harness-750.34645/), [$999 ask vs $1,910 MSRP](https://www.f150lightningforum.com/forum/threads/fs-oem-tow-mirrors-blis-360-camera-dimming-power-folding-power-telescope.19403/), [$500 XLT manual-fold](https://www.shoppok.com/lincoln/a,43,305431,2021-2023-Ford-F150-tow-mirrors--500.htm)). Consider a `yr_min: 2015` premium tier later.
- **Focus ST/RS steering wheel** — ACCURATE. $75–241 ([4u.parts $180](https://www.4u.parts/p/2015-18-ford-focus-st-leather-steering-wheel-audio-cruise-control/7176-0313), UK £75–£200).
- **Sonata panoramic sunroof glass** — ACCURATE. $125 (11–15 center glass, [Intermountain](https://intermountainautorecycling.com/parts/HYUNDAI/SONATA/2A0706/2012/ROOF_GLASS/192691/)) to $275–800 (2020+, [ahparts](https://ahparts.com/buy-used/2020-hyundai-sonata-sunroof-middle-panoramic-roof-glass-window-81630-l1000-81630l1000/429220-1), [Speedy's $750](https://speedysusedparts.com/products/26056-5ea48e59)). Glass shipping risk is the real cost here — sell_notes already steer to local pickup categories elsewhere; consider it for this one.

---

## Recommendations beyond the applied fixes

1. **Raise the understated five** (Focus Recaros, Mustang Recaros, Raptor grille, Focus ST HID pair, CTS-V Brembo set) — the product currently undersells its best finds by 2–3×.
2. **Clarify per-side vs. pair** on headlight entries in UI copy; the bands are right either way at current levels, but ambiguity is where "false advertising" complaints breed.
3. **Confirm the Accord "Sport Front Lip"** part identity (chin lip vs. underbody spoiler) — the only borderline-high entry not corrected, held back for thin evidence.
4. **Electronics caveat in sell_notes** ("may require dealer programming") for MyLink/cluster/head-unit entries would preempt buyer disputes that depress realized prices.
5. Naming nit (out of scope for this PR): "GLI Brembo Calipers" — standard GLI brakes are ATE; only 2019+ 35th Anniversary/Autobahn carry the Golf R big-brake package.
