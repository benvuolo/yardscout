# Interchange research notes — engine-driven parts (alternator, starter)

Working file for the part-first interchange feature. Every engine family that
powers a "Verified fit" claim in the app is documented here with the public
fitment source(s) behind it. **Nothing ships as "Verified" unless the seeker
and the donor both appear inside one published part-number application list
cited below.**

## Methodology

1. **Family definition.** Each family in `ENGINE_FAMILIES` groups vehicles that
   shipped the same engine (platform + displacement), with year ranges per
   model. A donor and seeker must both match a family's applications before any
   tier is assigned.
2. **Likely tier.** Same engine family, year windows overlap the family's
   applications. Shown in the app as "Likely fit — same engine family, verify
   part number".
3. **Verified tier.** The seeker AND the donor both sit inside ONE published
   part-number application list (OEM parts-site fitment, Lester/TYC/Denso
   aftermarket application tables). These lists are maintained by parts sellers
   who take returns when fitment is wrong, so they are conservative. Each
   family's `verified.groups` below reproduces the exact (make, model,
   year-range) spans we accepted from the cited list.
4. **Downgrades.** Applications flagged ambiguous (engine can't be inferred
   from year/make/model alone — e.g. a Taurus that could be Vulcan or Duratec)
   cap at Likely even inside a verified group. Config splits (amp options,
   M/T vs A/T units, mount styles) that the UI cannot distinguish are either
   excluded from groups or noted in the evidence.
5. **No wholesale scraping.** Application lists were spot-read manually from
   public catalog pages; retrieval dates are embedded in each evidence string.

## Primary sources

- Denso remanufactured catalog application tables (densoautoparts.com PDF) —
  engine-coded rows (e.g. `D17A1`, `J32A1`, `3MZFE`) per model/year.
- OEM parts-site fitment lists: subarupartsdeal.com, jeeppartsdeal.com,
  nissanpartsdeal.com, toyotapartsnow.com, hondapartsnow.com.
- Lester-numbered aftermarket application lists: dbelectrical.com,
  maniacelectricmotors.com, aspwholesale.com, qpselectric.com, partshawk.com,
  am-autoparts.com, dssautoparts.com, finditparts.com (TYC), rareelectrical,
  alternatorparts.com, cautop.com, mymromarts.com.
- TYC application tables (tycamericas.com, catalog PDF).

## Per-family evidence


### acura-j32 — Acura J32 3.2 V6 (TL/CL)

- **Engine:** 3.2L 6-cyl
- **Family applications:** Acura TL 1999-2008, Acura CL 2001-2003
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0675 (105A) CL 3.2 2001-2003 (exc Type S; Type S w/ M/T 2003) and TL 3.2 2000-2003; Type S w/ A/T uses 210-0453 (120A) in both models 2001-2003. TL 2004-2008 (J32A3) uses 210-0580 — left at likely.
  - Group 1: Acura CL 2001-2003; Acura TL 2000-2003
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### cadillac-northstar — Cadillac Northstar 4.6 V8

- **Engine:** 4.6L 8-cyl
- **Family applications:** Cadillac Deville 1994-2005, Cadillac Eldorado 1994-2002, Cadillac Seville 1994-2004, Cadillac DTS 2006-2011
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), 4.6 Northstar rows: 210-5184 (140A) Deville, Eldorado and Seville 1997 (unqualified; the 1994-1996 rows carry a 'w/o heated windshield' qualifier — excluded); 210-5185 (140A) Deville and Eldorado 1998-1999; 210-0467 (140A) Deville 2001-2005 and Seville 2001-2003, exc. limousine; 210-0639 (150A) DTS 2006-2011 exc. limousine (limos take 220A 210-0676).
  - Group 1: Cadillac Deville 1997-1997; Cadillac Eldorado 1997-1997; Cadillac Seville 1997-1997
  - Group 2: Cadillac Deville 1998-1999; Cadillac Eldorado 1998-1999
  - Group 3: Cadillac Deville 2001-2005; Cadillac Seville 2001-2003
  - Group 4: Cadillac DTS 2006-2011
- **starter:** no verified group — Likely tier only. Note: under-intake starter on Northstar — match the part number — nose cone / tooth count can differ

### ford-3g-50 — Ford 5.0/5.8 Windsor V8 (3G era)

- **Engine:** 5.0/5.8L 8-cyl
- **Family applications:** Ford Mustang 1987-1995, Ford F-150 1987-1996, Ford Bronco 1987-1996
- **alternator — verified evidence:** Lester 7750 (Ford F07U-10300, 3G 95A side-mount) application list (maniacelectricmotors.com, retrieved 2026-10-22): F-150/F-250 5.0/5.8 1993-1996, Bronco 5.0/5.8 1993-1996, E-150 5.0/5.8 1993-1996. Mustang 5.0 1994-1995 uses the pivot-mount 3G and 1987-93 trucks the 2G — both left at likely.
  - Group 1: Ford F-150 1993-1996; Ford Bronco 1993-1996
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### ford-40sohc — Ford 4.0 SOHC V6

- **Engine:** 4.0L 6-cyl
- **Family applications:** Ford Explorer 1997-2000, Ford Explorer 2001-2010, Ford Explorer Sport Trac 2001-2010, Ford Ranger 2001-2011, Ford Mustang 2005-2010
- **Ambiguity cap:** Ford Explorer — 97–00 Explorers split 4.0 OHV vs 4.0 SOHC — same decode string; confirm SOHC
- **alternator — verified evidence:** TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-07787 (Ford 1L2Z-10346-AB) Explorer 4.0 1997-2003 (97-01 SOHC, 02-03 all); 2-08258 (1L5Z-10346-BA) Ranger 4.0 2001-2005; 2-08437 (6R3Z-10346-A) Mustang 4.0 2005-2008.
  - Group 1: Ford Explorer 1997-2003
  - Group 2: Ford Ranger 2001-2005
  - Group 3: Ford Mustang 2005-2008
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### ford-46-2v — Ford 4.6 2V Modular V8

- **Engine:** 4.6L 8-cyl
- **Family applications:** Ford F-150 1997-2008, Ford Expedition 1997-2004, Ford Crown Victoria 1992-2011, Mercury Grand Marquis 1992-2011, Lincoln Town Car 1991-2011, Ford Mustang 1996-2004, Ford Explorer 2002-2005
- **alternator — verified evidence:** OEG/PartsPlayer listing for Ford F75U-10300-CA/CB 130A 3G (amazon.com, retrieved 2026-10-22): F-150 4.6/5.4 1997-2003, Expedition 5.4 1997-2002. TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-08252 Mustang 4.6 SOHC 99-04 is its own 6G unit; 2-07776 Crown Victoria 95-99; 2-07795 Grand Marquis 98-02.
  - Group 1: Ford F-150 1997-2003; Ford Expedition 1997-2002
  - Group 2: Ford Mustang 1999-2004
  - Group 3: Ford Crown Victoria 1995-1999
  - Group 4: Mercury Grand Marquis 1998-2002
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### ford-54-2v — Ford 5.4 2V Triton V8

- **Engine:** 5.4L 8-cyl
- **Family applications:** Ford F-150 1997-2003, Ford Expedition 1997-2004
- **alternator — verified evidence:** OEG/PartsPlayer listing for Ford F75U-10300-CA/CB 130A 3G (amazon.com, retrieved 2026-10-22): F-150 4.6/5.4 1997-2003, Expedition 5.4 1997-2002 share one unit.
  - Group 1: Ford F-150 1997-2003; Ford Expedition 1997-2002
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### ford-54-3v — Ford 5.4 3V Triton V8

- **Engine:** 5.4L 8-cyl
- **Family applications:** Ford F-150 2004-2010, Ford Expedition 2005-2014
- **alternator — verified evidence:** TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-08318 (Ford 6L3Z-10346-AA) F-150 5.4 2004-2008. Lester 11292 (Ford 9L3Z-10346-C) application table (everychina.com/koeep.com, retrieved 2026-10-22): F-150 4.6/5.4 2009-2010 + Expedition 5.4 2009-2014.
  - Group 1: Ford F-150 2004-2008
  - Group 2: Ford F-150 2009-2010; Ford Expedition 2009-2014
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### ford-cyclone — Ford 3.5/3.7 Cyclone V6 (non-turbo)

- **Engine:** 3.5/3.7L 6-cyl
- **Family applications:** Ford Edge 2007-2014, Ford Taurus 2008-2019, Ford Explorer 2011-2019, Ford Flex 2009-2019, Ford Mustang 2011-2017, Ford F-150 2011-2014
- **Ambiguity cap:** Ford Taurus — SHO is the 3.5 EcoBoost twin-turbo — same decode string; confirm non-turbo
- **Ambiguity cap:** Ford Explorer — Explorer Sport/Platinum is 3.5 EcoBoost — same decode string; confirm non-turbo
- **Ambiguity cap:** Ford Flex — Flex EcoBoost shares the 3.5 decode string; confirm non-turbo
- **alternator — verified evidence:** DSS/TRQ Lester 11273 application table (Ford 7T4Z-10346-A, Mitsubishi A3TJ1291, retrieved 2026-10-22): Edge 2007-2014, Taurus 3.5 2008-2012. Quality-Built 11271 175A (Ford 8A4Z-10346-A, partshawk.com): Taurus 2008-2012, Flex 2009-2012, Edge 2011-2013, Explorer 2011-2012.
  - Group 1: Ford Edge 2007-2014; Ford Taurus 2008-2012
  - Group 2: Ford Taurus 2008-2012; Ford Flex 2009-2012; Ford Edge 2011-2013; Ford Explorer 2011-2012
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### ford-duratec30 — Ford/Mazda Duratec 3.0 DOHC V6

- **Engine:** 3.0L 6-cyl
- **Family applications:** Ford Fusion 2006-2012, Ford Escape 2001-2012, Mercury Milan 2006-2011, Mercury Mariner 2005-2011, Mazda Tribute 2001-2011, Ford Five Hundred 2005-2007, Mercury Montego 2005-2007, Ford Taurus 1996-2007
- **Ambiguity cap:** Ford Taurus — Taurus 3.0s split Vulcan (pushrod) vs Duratec (DOHC) — same decode string; confirm DOHC before buying
- **alternator — verified evidence:** TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-08259 (1L8Z-10V346-CCRM) Escape 3.0 2001-2004; 2-08403 (ZZC2-18-300) Escape 3.0 2005-2006; 2-08269 (2F1Z-10346-BA) Taurus 3.0 DOHC 2002-2005; 2-08442 (6F9Z-10346-AA) Five Hundred 3.0 2005-2007.
  - Group 1: Ford Escape 2001-2004
  - Group 2: Ford Escape 2005-2006
  - Group 3: Ford Taurus 2002-2005
  - Group 4: Ford Five Hundred 2005-2007
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### ford-escape-16eb — Ford Escape 1.6 EcoBoost I4

- **Engine:** 1.6L 4-cyl
- **Family applications:** Ford Escape 2013-2016
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0604 (170A) Escape 1.6 2013-2014. 2015-2016 1.6 cars are past this catalog edition — left at likely.
  - Group 1: Ford Escape 2013-2014
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### ford-escape-20eb — Ford Escape 2.0 EcoBoost I4

- **Engine:** 2.0L 4-cyl
- **Family applications:** Ford Escape 2013-2016
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4202 (135A) Escape 2.0 2013-2014. 2015-2016 2.0 cars are past this catalog edition — left at likely.
  - Group 1: Ford Escape 2013-2014
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### ford-mzr — Ford/Mazda MZR-Duratec 2.0/2.3/2.5 I4

- **Engine:** 2.0/2.3/2.5L 4-cyl
- **Family applications:** Ford Fusion 2006-2014, Ford Escape 2005-2012, Ford Focus 2005-2011, Mazda 3 2004-2013, Mazda 5 2006-2010, Mazda 6 2003-2013, Mercury Milan 2006-2011, Mercury Mariner 2005-2011, Mazda Tribute 2005-2011, Ford Ranger 2001-2011
- **alternator — verified evidence:** Lester 11172 application table (cautop.com; Mitsubishi A3TJ0891, Ford 6E5Z-10346-AA, retrieved 2026-10-22): Fusion 2.3 2006-2009, Milan 2.3 2006-2009. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4214 (90A) Mazda3 2.0 2004-2009, Mazda3 2.3 2004-2006 and non-turbo 2007-2009, Mazda5 2.3 2006-2007; 210-4303 (100A) Mazda3 2.0 2010-2011; 210-4327 (110A) Mazda5 2.3 2008-2010; 210-4238 (100A) Mazda6 2.3 2008 and 2.5 2009; 210-0615 (170A) Fusion 2.5 AND 2.0 Turbo 2013-2014 (one unit spans both engines). Mazda6 2.3 03-05 splits by transmission and Mazdaspeed turbos differ — left at likely.
  - Group 1: Ford Fusion 2006-2009; Mercury Milan 2006-2009
  - Group 2: Mazda 3 2004-2009; Mazda 5 2006-2007
  - Group 3: Mazda 3 2010-2011
  - Group 4: Mazda 5 2008-2010
  - Group 5: Mazda 6 2008-2009
  - Group 6: Ford Fusion 2013-2014
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### ford-vulcan30 — Ford 3.0 Vulcan V6

- **Engine:** 3.0L 6-cyl
- **Family applications:** Ford Taurus 1986-2007, Mercury Sable 1986-2005, Ford Ranger 1991-2008
- **Ambiguity cap:** Ford Taurus — Taurus also offered DOHC 3.0 V6s (Duratec) — same decode string; confirm which 3.0 before buying
- **Ambiguity cap:** Mercury Sable — Sable also offered the Duratec 3.0 — same decode string; confirm which 3.0
- **alternator — verified evidence:** TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-08263 (YF1Z-10V346-FA) Taurus/Sable 3.0 OHV 2000-2001; 2-08268 (3F1Z-10346-AB) Taurus/Sable 3.0 OHV 2002-2006. Fitment data exists, but the Vulcan/Duratec decode ambiguity keeps every pair at likely in the app.
  - Group 1: Ford Taurus 2000-2001; Mercury Sable 2000-2001
  - Group 2: Ford Taurus 2002-2006; Mercury Sable 2002-2005
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### gm-14t — GM 1.4 Turbo I4 (LUJ/LUV)

- **Engine:** 1.4L 4-cyl
- **Family applications:** Chevrolet Cruze 2011-2015, Chevrolet Sonic 2012-2018, Buick Encore 2013-2021, Chevrolet Trax 2013-2021
- **alternator — verified evidence:** Rareelectrical FG12S031/Lester 11399 listing (GM 13577154/13597226, retrieved 2026-10-22): Cruze 1.4T 2011 ONLY, Encore 2013-2021, Trax 2015-2021. 2012-2016 Cruze 1.4 uses a different unit — left at likely.
  - Group 1: Chevrolet Cruze 2011-2011; Buick Encore 2013-2021; Chevrolet Trax 2015-2021
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### gm-3800 — GM 3800 Series II/III V6

- **Engine:** 3.8L 6-cyl
- **Family applications:** Buick Lesabre 1996-2005, Pontiac Grand Prix 1997-2008, Pontiac Bonneville 1996-2005, Chevrolet Impala 2000-2005, Chevrolet Monte Carlo 1998-2005, Buick Regal 1997-2004, Buick Park Avenue 1997-2005, Buick Lucerne 2006-2008, Buick Lacrosse 2005-2009
- **alternator — verified evidence:** Lester 8245 listing (OCPTY/amazon.com, GM 10464439/10480411, retrieved 2026-10-22): LeSabre 3.8 2000-2004, Bonneville 3.8 2000-2004. W-body 3800s (Grand Prix/Impala/Monte Carlo/Regal) use different mounting-era units — left at likely.
  - Group 1: Buick Lesabre 2000-2004; Pontiac Bonneville 2000-2004
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### gm-60deg — GM 60° 3.1/3.4 V6

- **Engine:** 3.1/3.4L 6-cyl
- **Family applications:** Chevrolet Venture 1997-2005, Pontiac Montana 1999-2005, Pontiac Grand Am 1999-2005, Oldsmobile Alero 1999-2004, Chevrolet Impala 2000-2005, Chevrolet Monte Carlo 2000-2005, Chevrolet Malibu 1997-2005, Buick Century 1997-2005, Pontiac Aztek 2001-2005, Buick Rendezvous 2002-2007, Chevrolet Equinox 2005-2009, Pontiac Torrent 2006-2009
- **alternator — verified evidence:** Lester 13993 (GM 10317647/10440635, Valeo SG10S029) application list (dbelectrical.com 400-40079, retrieved 2026-10-22): Venture 3.4 2002-2005, Montana 3.4 2002-2005, Silhouette 3.4 2002-2004. Grand Am/Alero/Impala/Malibu 3.4 use CS130D-era Delco units with multiple amp options — left at likely.
  - Group 1: Chevrolet Venture 2002-2005; Pontiac Montana 2002-2005
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### gm-atlas42 — GM Atlas 4.2 I6 (LL8)

- **Engine:** 4.2L 6-cyl
- **Family applications:** Chevrolet Trailblazer 2002-2009, GMC Envoy 2002-2009, Oldsmobile Bravada 2002-2004, Buick Rainier 2004-2007, Saab 9-7x 2005-2009, Isuzu Ascender 2003-2008
- **alternator — verified evidence:** TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-08290 (GM 19151920) Trailblazer/Envoy 4.2 L6 2002-2006.
  - Group 1: Chevrolet Trailblazer 2002-2006; GMC Envoy 2002-2006
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### gm-ecotec22 — GM Ecotec 2.2 I4 (L61)

- **Engine:** 2.2L 4-cyl
- **Family applications:** Chevrolet Cavalier 2002-2005, Chevrolet Cobalt 2005-2010, Chevrolet Malibu 2004-2008, Chevrolet HHR 2006-2010, Saturn ION 2003-2007, Pontiac G5 2007-2009, Pontiac Sunfire 2002-2005, Saturn VUE 2002-2007
- **alternator — verified evidence:** Lester 11265 (Valeo, GM 15828450/22762984) application list (am-autoparts.com + maniacelectricmotors.com, retrieved 2026-10-22): Cobalt 2008-2010, Malibu 2.4 2008-2012, G5 2008-2009, Saturn Aura/Sky/Vue 2008-2010. Denso unit Lester 11140: Cobalt 2.2/2.4 2006-2007. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0546 (110A) Saturn Vue 2.2 2004-2007 (the same unit also serves the 2.4 and Honda-3.5 Vues those years). Earlier Cavalier/Sunfire/ION use other units — left at likely.
  - Group 1: Chevrolet Cobalt 2008-2010; Chevrolet Malibu 2008-2012; Pontiac G5 2008-2009
  - Group 2: Chevrolet Cobalt 2006-2007
  - Group 3: Saturn VUE 2004-2007
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### gm-ecotec24 — GM Ecotec 2.4 I4 (LE5/LE9/LEA)

- **Engine:** 2.4L 4-cyl
- **Family applications:** Chevrolet Cobalt 2006-2010, Chevrolet Malibu 2008-2012, Chevrolet Equinox 2010-2017, Chevrolet HHR 2008-2010, GMC Terrain 2010-2017, Pontiac G6 2006-2009, Chevrolet Captiva Sport 2012-2015, Saturn VUE 2008-2010
- **alternator — verified evidence:** TYC 2-11459 application table (tycamericas.com, retrieved 2026-10-22; Lester 11459, GM 13512759): Equinox 2.4 2010-2017, Terrain 2.4 2010-2017. Lester 11265 (Valeo, GM 15828450/22762984) application list (am-autoparts.com, retrieved 2026-10-22) includes Saturn Vue 2.4 2008-2010. Cobalt/Malibu/G6-era LE5 uses a different unit — left at likely.
  - Group 1: Chevrolet Equinox 2010-2017; GMC Terrain 2010-2017
  - Group 2: Saturn VUE 2008-2010
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### gm-gen3-truck — GM Gen III Vortec truck V8 (4.8/5.3/6.0)

- **Engine:** 4.8/5.3/6.0L 8-cyl
- **Family applications:** Chevrolet Silverado* 1999-2007, GMC Sierra* 1999-2007, Chevrolet Tahoe 2000-2006, GMC Yukon* 2000-2006, Chevrolet Suburban* 2000-2006, Chevrolet Avalanche 2002-2006, Cadillac Escalade* 2002-2006
- **alternator — verified evidence:** CarQuest weblink part 8292A (Lester 8292, Delco AD244 145A) application summary + aspwholesale.com table (retrieved 2026-10-22): Silverado/Sierra 2003-2006, Tahoe 2003-2004, Yukon 2003-2006, Suburban 2003-2006, Avalanche 2003-2006, Escalade 2003-2005. Earlier 99-02 trucks use the AD230-era unit — left at likely.
  - Group 1: Chevrolet Silverado* 2003-2006; GMC Sierra* 2003-2006; Chevrolet Tahoe 2003-2004; GMC Yukon* 2003-2006; Chevrolet Suburban* 2003-2006; Chevrolet Avalanche 2003-2006; Cadillac Escalade* 2003-2005
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### gm-gen4-truck — GM Gen IV Vortec truck V8 (4.8/5.3/6.0/6.2)

- **Engine:** 4.8/5.3/6.0/6.2L 8-cyl
- **Family applications:** Chevrolet Silverado* 2007-2013, GMC Sierra* 2007-2013, Chevrolet Tahoe 2007-2014, GMC Yukon* 2007-2014, Chevrolet Suburban* 2007-2014, Chevrolet Avalanche 2007-2013, Cadillac Escalade* 2007-2014
- **alternator — verified evidence:** TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-08302 (GM 15225927) C/K pickup 4.8/5.3 2005-2010 — clipped to this family's 2007+ window.
  - Group 1: Chevrolet Silverado* 2007-2010; GMC Sierra* 2007-2010
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### gm-hv-v6 — GM High Value 3.5/3.9 V6

- **Engine:** 3.5/3.9L 6-cyl
- **Family applications:** Chevrolet Impala 2006-2011, Chevrolet Monte Carlo 2006-2007, Chevrolet Malibu 2004-2010, Pontiac G6 2005-2009, Chevrolet Uplander 2005-2009, Buick Terraza 2005-2007
- **alternator — verified evidence:** Lester 11185 (Bosch 0-124-425-032, GM 20911162) application list (TYC 2-11185 via finditparts.com + maniacelectricmotors.com, retrieved 2026-10-22): Impala 3.5/3.9 2006-2011, Monte Carlo 3.5/3.9 2006-2007. Malibu/G6/Uplander use different units — left at likely.
  - Group 1: Chevrolet Impala 2006-2011; Chevrolet Monte Carlo 2006-2007
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### gm-llt36 — GM 3.6 V6 (LY7/LLT/LFX high-feature)

- **Engine:** 3.6L 6-cyl
- **Family applications:** Chevrolet Traverse 2009-2017, GMC Acadia 2007-2016, Buick Enclave 2008-2017, Saturn Outlook 2007-2010, Chevrolet Impala 2012-2019, Chevrolet Camaro 2010-2015, Chevrolet Equinox 2013-2017, GMC Terrain 2013-2017, Buick Lacrosse 2010-2016, Cadillac CTS 2004-2014, Cadillac SRX 2004-2016, Cadillac STS 2005-2011
- **alternator — verified evidence:** BBB Industries 11252 fitment table (partcatalog.com) + Brillman Denso 170A listing (GM 25815839/23105717, retrieved 2026-10-22): Traverse 2009-2017, Acadia 2007-2016, Enclave 2008-2017, Outlook 2007-2010. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0531 (130A) CTS 3.6 2004-2005 (also the 2.8); 210-0641 (145A) CTS 3.6 2008-2009; 210-0765 (150A) CTS 3.0/3.6 2010-2013; 210-0576 (150A) SRX 3.6 2004-2009 and STS 3.6 2005-2011. SRX 2010+ rows carry pulley qualifiers — left at likely.
  - Group 1: Chevrolet Traverse 2009-2017; GMC Acadia 2007-2016; Buick Enclave 2008-2017; Saturn Outlook 2007-2010
  - Group 2: Cadillac CTS 2004-2005
  - Group 3: Cadillac CTS 2008-2009
  - Group 4: Cadillac CTS 2010-2013
  - Group 5: Cadillac SRX 2004-2009; Cadillac STS 2005-2011
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### gm-vortec-van — Chevy/GMC Vortec V8 van (Express/Savana)

- **Engine:** 4.8/5.0/5.3/5.7/6.0L 8-cyl
- **Family applications:** Chevrolet Express* 1996-2010, GMC Savana* 1996-2010
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5190 (124A, w/o black plastic rear cover) Express/Savana 5.0 and 5.7 1996-2000 across 1500/2500/3500 (the w/-cover vans take 210-5119, same vehicle list — match the case style); 210-5384 (145A Delco) Express/Savana 4.8/5.3/6.0 2005-2008 across 1500/2500/3500. The 2001-2004 vans and 2009-2010 case-size splits are left at likely.
  - Group 1: Chevrolet Express* 1996-2000; GMC Savana* 1996-2000
  - Group 2: Chevrolet Express* 2005-2008; GMC Savana* 2005-2008
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### gm-vortec43 — GM Vortec 4.3 V6

- **Engine:** 4.3L 6-cyl
- **Family applications:** Chevrolet S-10* 1994-2004, GMC Sonoma 1994-2004, Chevrolet Blazer* 1995-2005, GMC Jimmy* 1995-2001, Chevrolet Astro* 1994-2005, GMC Safari* 1994-2005, Oldsmobile Bravada 1996-2001, Chevrolet Express* 1996-2008, GMC Savana* 1996-2008
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), 4.3 V6 rows: 210-5112 (100A) S10 1994-1995, Sonoma 1994-1995, Blazer 1995; 210-5111 (105A) Astro and Safari 1994-1995; 210-5119 (105A) S10/Sonoma/Blazer/Jimmy 1996-1997, Astro/Safari 1996-1999, Express/Savana 4.3 1996-2000 (w/ black plastic rear cover — the w/o-cover vans take 210-5190, same vehicle list); 210-5120 (105A) S10/Blazer 1998-1999, Sonoma/Jimmy 1998-2000, Astro/Safari 2000; 210-5159 (100A) S10/Sonoma/Blazer 2001-2004, Jimmy 2001; 210-5384 (145A) Express/Savana 4.3 2005-2008. The 2000 S10/Blazer split mid-year by VIN — excluded from verified.
  - Group 1: Chevrolet S-10* 1994-1995; GMC Sonoma 1994-1995; Chevrolet Blazer* 1995-1995
  - Group 2: Chevrolet Astro* 1994-1995; GMC Safari* 1994-1995
  - Group 3: Chevrolet S-10* 1996-1997; GMC Sonoma 1996-1997; Chevrolet Blazer* 1996-1997; GMC Jimmy* 1996-1997; Chevrolet Astro* 1996-1999; GMC Safari* 1996-1999; Chevrolet Express* 1996-2000; GMC Savana* 1996-2000
  - Group 4: Chevrolet S-10* 1998-1999; Chevrolet Blazer* 1998-1999; GMC Sonoma 1998-2000; GMC Jimmy* 1998-2000; Chevrolet Astro* 2000-2000; GMC Safari* 2000-2000
  - Group 5: Chevrolet S-10* 2001-2004; GMC Sonoma 2001-2004; Chevrolet Blazer* 2001-2004; GMC Jimmy* 2001-2001
  - Group 6: Chevrolet Express* 2005-2008; GMC Savana* 2005-2008
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### hk-alpha — Hyundai Alpha 1.5/1.6 I4

- **Engine:** 1.5/1.6L 4-cyl
- **Family applications:** Hyundai Accent 1995-2011
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 211-6012 (90A) Accent 1.5 1995-1999; 211-6005 (90A) Accent 1.5 2000-2003 and 1.6 2001-2002 (the 2003-2005 1.6 rows carry a Mando-unit qualifier — excluded); 211-6016 (90A) Accent 1.6 2010-2011. The 2006-2009 rows are Mando-qualified — left at likely.
  - Group 1: Hyundai Accent 1995-1999
  - Group 2: Hyundai Accent 2000-2002
  - Group 3: Hyundai Accent 2010-2011
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### hk-beta20 — Hyundai/Kia Beta II 2.0 I4

- **Engine:** 2.0L 4-cyl
- **Family applications:** Hyundai Elantra 2001-2010, Hyundai Tiburon 2003-2008, Hyundai Tucson 2005-2009, Kia Sportage 2005-2010
- **alternator — verified evidence:** Lester 13973 (Hyundai/Kia 37300-23600, Mando AB190147) application lists (qpselectric.com + partshawk.com, retrieved 2026-10-22): Elantra 2.0 2001-2006, Tiburon 2.0 2003-2004 and 2007-2008 (w/ Mando unit), Tucson 2.0 2005, Sportage 2.0 2005-2006.
  - Group 1: Hyundai Elantra 2001-2006; Hyundai Tiburon 2003-2004; Hyundai Tiburon 2007-2008; Hyundai Tucson 2005-2005; Kia Sportage 2005-2006
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### hk-gamma16 — Hyundai/Kia Gamma 1.6 I4

- **Engine:** 1.6L 4-cyl
- **Family applications:** Hyundai Accent 2012-2017, Kia Rio 2012-2017, Kia Soul 2012-2019, Hyundai Veloster 2012-2017
- **alternator — verified evidence:** Lester 13209 (Hyundai/Kia 37300-2B300/2B500/2B510, Valeo) application lists (dbelectrical.com 400-40153 + mymromarts.com, retrieved 2026-10-22): Accent 1.6 2012-2017, Veloster 1.6 2012-2017, Rio 1.6 2012-2013. Soul 1.6 uses 37300-2B760 (Lester 11609) — left at likely.
  - Group 1: Hyundai Accent 2012-2017; Hyundai Veloster 2012-2017; Kia Rio 2012-2013
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### hk-mu-lambda — Hyundai 2.7/3.3/3.8 V6 (Mu/Lambda)

- **Engine:** 2.7/3.3/3.8L 6-cyl
- **Family applications:** Hyundai Santa Fe 2007-2009, Hyundai Azera 2006-2011, Hyundai Veracruz 2007-2012, Hyundai Entourage 2007-2008
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0712 (130A) Santa Fe 2.7 2007-2009 and 3.3 2007-2008, Azera 3.3 2007-2009 and 3.8 2007-2008 (the 2009+ rows carry Denso-unit vendor qualifiers — group capped at 2008).
  - Group 1: Hyundai Santa Fe 2007-2008; Hyundai Azera 2007-2008
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### hk-nu — Hyundai/Kia Nu 1.8/2.0 I4

- **Engine:** 1.8/2.0L 4-cyl
- **Family applications:** Hyundai Elantra 2011-2020, Kia Soul 2012-2019, Kia Forte 2014-2018, Hyundai Tucson 2016-2021
- **alternator — verified evidence:** Lester 11610 (Hyundai 37300-2E200, Valeo FG10T011) fitment (TYC 2-11610 finditparts.com + dahkee.com + thenthgear.com, retrieved 2026-10-22): Elantra 1.8/2.0 2011-2016, Forte 2014-2016, Soul 2.0 2012-2013.
  - Group 1: Hyundai Elantra 2011-2016; Kia Forte 2014-2016; Kia Soul 2012-2013
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### hk-theta-gdi — Hyundai/Kia Theta II 2.4 GDI I4

- **Engine:** 2.4L 4-cyl
- **Family applications:** Hyundai Sonata 2011-2019, Kia Optima 2011-2020, Hyundai Santa Fe Sport 2013-2018, Kia Sorento 2011-2020, Kia Sportage 2011-2016, Hyundai Tucson 2010-2015
- **alternator — verified evidence:** Hyundai 37300-2G150 (Lester 11491/11492, Valeo TG11C087) listings (rareelectrical.com + amazon.com, retrieved 2026-10-22): Sonata 2.4 2011-2013, Optima 2.4 2011-2013. The 2.0T and 2014+ units differ — left at likely.
  - Group 1: Hyundai Sonata 2011-2013; Kia Optima 2011-2013
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### hk-theta-mpi — Hyundai/Kia Theta 2.4 MPI I4

- **Engine:** 2.4L 4-cyl
- **Family applications:** Hyundai Sonata 2006-2010, Kia Optima 2006-2010, Kia Rondo 2007-2010
- **alternator — verified evidence:** Lester 11189 (Hyundai/Kia 37300-25201, Valeo TG11C076) fitment (WAI 11189N partshawk.com + DB Electrical 400-40062, retrieved 2026-10-22): Sonata 2.4 2006-2010, Optima 2.4 2006-2010, Rondo 2.4 2007-2010.
  - Group 1: Hyundai Sonata 2006-2010; Kia Optima 2006-2010; Kia Rondo 2007-2010
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### honda-a20 — Honda A20 2.0 I4

- **Engine:** 2.0L 4-cyl
- **Family applications:** Honda Accord 1986-1989
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0233 (65A) Accord 2.0 A20A3 w/ fuel injection 1986-1989 and 210-0389 (65A) Accord 2.0 A20A1 carbureted 1986-1989 — both published lists span the same four years; match FI vs carb when pulling.
  - Group 1: Honda Accord 1986-1989
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### honda-d16 — Honda D16 1.6 SOHC I4

- **Engine:** 1.6L 4-cyl
- **Family applications:** Honda Civic 1996-2000, Honda Civic del Sol 1996-1997
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4134 (70A) Civic 1.6 D16Y5/D16Y7/D16Y8/D16B5 1996-2000 (exc Canada/Si) and Civic del Sol 1.6 1996-1997. Corroborated by Lester 13649 (Honda 31100-P2E-A01) listings.
  - Group 1: Honda Civic 1996-2000; Honda Civic del Sol 1996-1997
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### honda-d17 — Honda D17 1.7 I4

- **Engine:** 1.7L 4-cyl
- **Family applications:** Honda Civic 2001-2005
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4148 (70A) Civic 1.7 D17A1/A2/A6/A7 2001-2005 (exc Canada). Corroborated by Lester 13893 (Honda 31100-PLM-A02) listings incl. Acura EL 1.7.
  - Group 1: Honda Civic 2001-2005
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### honda-f22 — Honda F22 2.2 I4

- **Engine:** 2.2L 4-cyl
- **Family applications:** Honda Accord 1990-1997
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0216 (90A) Accord 2.2 F22A1/A6 1990-1993; 210-0208 (80A) Accord 2.2 F22B2 1994-1997 and 210-0209 (90A) Accord 2.2 F22B1 VTEC 1994-1997 — the 94-97 lists split by VTEC trim but each spans all four years.
  - Group 1: Honda Accord 1990-1993
  - Group 2: Honda Accord 1994-1997
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### honda-f23 — Honda F23 2.3 I4

- **Engine:** 2.3L 4-cyl
- **Family applications:** Honda Accord 1998-2002, Acura CL 1998-1999
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0192 (80A) Accord 2.3 1998-2002 (coupe/ULEV splits) and 210-0193 (80A) Accord 2.3 sedan exc-ULEV 1998-2001 + Acura CL 2.3 1998-1999. Both units cover the Accord span; the CL pairs via 210-0193.
  - Group 1: Honda Accord 1998-2002
  - Group 2: Honda Accord 1998-2001; Acura CL 1998-1999
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### honda-j30 — Honda/Acura J30 3.0 V6 (Accord)

- **Engine:** 3.0L 6-cyl
- **Family applications:** Honda Accord 1998-2002, Honda Accord 2003-2007, Acura CL 1997-1999
- **alternator — verified evidence:** Lester 8220 (Delco CS130D, Honda 31100-P8A-A01/P8C-A02) application lists (alternatorparts.com + thewrenchmonkey.ca, retrieved 2026-10-22): Accord 3.0 1998-2002, Acura CL 3.0 1997-1999. The 03-07 Accord V6 uses a Denso unit — left at likely.
  - Group 1: Honda Accord 1998-2002; Acura CL 1997-1999
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### honda-j35-early — Honda J35 3.5 V6 (99–04 era)

- **Engine:** 3.5L 6-cyl
- **Family applications:** Honda Odyssey 1999-2004, Honda Pilot 2003-2005, Acura MDX 2001-2006
- **alternator — verified evidence:** TYC 2-13918 fitment (partshawk.com + a-premium.com; Honda 31100-PGK-A01/A03, Denso 104210-3090, retrieved 2026-10-22): MDX 2001-2002, Odyssey 3.5 2002-2004, Pilot 2003-2004. The 99-01 Odyssey unit differs — left at likely.
  - Group 1: Acura MDX 2001-2002; Honda Odyssey 2002-2004; Honda Pilot 2003-2004
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### honda-j35-mid — Honda J35 3.5 V6 (05–10 era)

- **Engine:** 3.5L 6-cyl
- **Family applications:** Honda Odyssey 2005-2010, Honda Pilot 2006-2008, Honda Ridgeline 2006-2008
- **alternator — verified evidence:** TYC 2-11151 fitment (partshawk.com; Honda 31100-RJA-A02 OEM list on hondapartsnow.com, retrieved 2026-10-22): Odyssey 2005-2007, Pilot 2005-2008, Ridgeline 2006-2008 (+ MDX/TL/RL). Honda 31100-RGW-A01 (CSF92, hondapartsconnection.com): Odyssey 2008-2011 is the follow-on unit.
  - Group 1: Honda Odyssey 2005-2007; Honda Pilot 2005-2008; Honda Ridgeline 2006-2008
  - Group 2: Honda Odyssey 2008-2010
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### honda-j35-z — Honda J35Z/Y 3.5 V6 (08–17 era)

- **Engine:** 3.5L 6-cyl
- **Family applications:** Honda Accord 2008-2012, Honda Odyssey 2011-2017, Honda Pilot 2009-2015, Honda Ridgeline 2009-2014, Honda Crosstour 2010-2015
- **alternator — verified evidence:** Honda 31100-RGW-A01 (CSF92, Denso) OEM listing (hondapartsconnection.com, retrieved 2026-10-22): Odyssey/Pilot/Ridgeline 2008-2011 share one unit — clipped to this family's 2009+ apps.
  - Group 1: Honda Pilot 2009-2011; Honda Ridgeline 2009-2011
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### honda-k24a — Honda/Acura K24 2.4 I4 (02–09 era)

- **Engine:** 2.4L 4-cyl
- **Family applications:** Honda Accord 2003-2007, Honda CR-V 2002-2009, Honda Element 2003-2011, Acura TSX 2004-2008
- **alternator — verified evidence:** TYC 2-13980 application table (tycamericas.com, retrieved 2026-10-22; Honda 31100-RAA-A05, Lester 13980): Accord 2.4 2003-2007, Element 2003-2011, TSX 2004-2008, CR-V 2007-2011. CR-V 2002-2006 is NOT in this unit's list — left at likely.
  - Group 1: Honda Accord 2003-2007; Honda Element 2003-2011; Acura TSX 2004-2008; Honda CR-V 2007-2011
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### honda-k24z — Honda/Acura K24Z 2.4 I4 (08–15 era)

- **Engine:** 2.4L 4-cyl
- **Family applications:** Honda Accord 2008-2012, Honda CR-V 2010-2014, Honda Civic 2012-2015, Honda Crosstour 2012-2015, Acura TSX 2009-2014
- **alternator — verified evidence:** Lester 11390 (Honda 31100-R40-A01, Denso 104210-5890) application tables (dssautoparts.com + FVP/autofactsdb.com + DB Electrical 400-52394, retrieved 2026-10-22): Accord 2.4 2008-2012, TSX 2.4 2009-2014.
  - Group 1: Honda Accord 2008-2012; Acura TSX 2009-2014
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### honda-r18 — Honda R18 1.8 I4

- **Engine:** 1.8L 4-cyl
- **Family applications:** Honda Civic 2006-2011, Honda Civic 2012-2015
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4236 (90A) Civic 1.8 R18A1 2006-2011. Corroborated by TYC 2-11176 / Lester 11176 (Honda 31100-RNA-A01) listings. 2012-2015 R18Z Civic uses a different unit — left at likely.
  - Group 1: Honda Civic 2006-2011
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### jeep-40 — Jeep 4.0 I6

- **Engine:** 4.0L 6-cyl
- **Family applications:** Jeep Grand Cherokee 1993-2004, Jeep Cherokee 1991-2001, Jeep Wrangler 1991-2006, Jeep Comanche 1991-1992
- **alternator — verified evidence:** TYC 2-13341 fitment (partshawk.com; Chrysler 56005685AB, Denso 121000-3440, retrieved 2026-10-22): Cherokee 1991-1998, Comanche 1991-1992, Wrangler 1991-1998, Grand Cherokee 1993-1998. TYC 2-13876 (Jeep 56041864AB, standardautopart.com): Wrangler 4.0 2001-2006 is its own unit.
  - Group 1: Jeep Cherokee 1991-1998; Jeep Comanche 1991-1992; Jeep Wrangler 1991-1998; Jeep Grand Cherokee 1993-1998
  - Group 2: Jeep Wrangler 2001-2006
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### mini-r50 — MINI Cooper 1.6 (R50/R52/R53)

- **Engine:** 1.6L 4-cyl
- **Family applications:** MINI Cooper 2002-2006
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0844 (105A) Cooper W10 2002-2004 plus 2005 coupe and convertible rows; the supercharged S (W11, 210-0524) spans 2002-2006 — match trim. Group capped at 2002-2005 where both published lists cover every body style.
  - Group 1: MINI Cooper 2002-2005
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### mopar-37 — Chrysler PowerTech 3.7 V6

- **Engine:** 3.7L 6-cyl
- **Family applications:** Jeep Liberty 2002-2012, Dodge Dakota 2004-2011, Dodge|Ram Ram* 2002-2012, Jeep Grand Cherokee 2005-2010, Dodge Nitro 2007-2011, Jeep Commander 2006-2010
- **alternator — verified evidence:** Mopar OEM 56029914AC fitment (jeeppartsdeal.com, retrieved 2026-10-22): Liberty 3.7 2002-2005, Grand Cherokee 3.7 2005-2006; Denso 421000-0040 vendor table: Commander 3.7 2006-2010. Mopar RL041120AC/56029700AD: Ram 3.7 2002-2008 (same units as the 4.7 trucks).
  - Group 1: Jeep Liberty 2002-2005; Jeep Grand Cherokee 2005-2006; Jeep Commander 2006-2010
  - Group 2: Dodge|Ram Ram* 2002-2008
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### mopar-47 — Chrysler PowerTech 4.7 V8

- **Engine:** 4.7L 8-cyl
- **Family applications:** Jeep Grand Cherokee 1999-2009, Dodge Dakota 2000-2011, Dodge Durango 2000-2009, Dodge|Ram Ram* 2002-2013, Jeep Commander 2006-2009, Chrysler Aspen 2007-2009
- **alternator — verified evidence:** Mopar OEM 56029914AC (160A Denso, replaces 56029914AA) fitment (jeeppartsdeal.com, retrieved 2026-10-22): Durango 3.7/4.7 2001-2007, Grand Cherokee 3.7/4.7 2005-2006; Denso 421000-0040 vendor table adds Commander 3.7/4.7 2006-2010. Mopar RL041120AC (Ram 1500 3.7/4.7 2002-2007) and 56029700AD (Ram 1500 2008) cover the trucks.
  - Group 1: Dodge Durango 2001-2007; Jeep Grand Cherokee 2005-2006; Jeep Commander 2006-2009
  - Group 2: Dodge|Ram Ram* 2002-2008
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### mopar-dart — Dodge Dart 1.4T/2.0/2.4 I4

- **Engine:** 1.4/2.0/2.4L 4-cyl
- **Family applications:** Dodge Dart* 2013-2016
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4237 (120A) Dart 1.4T 2013-2014, 2.0 2013-2015, 2.4 2014-2015; 210-4239 (160A) Dart 2.0/2.4 2013-2015 — every 2013-2015 engine/year pairing sits inside at least the 120A list. 2016 is past this edition — left at likely.
  - Group 1: Dodge Dart* 2013-2015
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### mopar-hemi57 — Chrysler 5.7 HEMI V8

- **Engine:** 5.7L 8-cyl
- **Family applications:** Dodge|Ram Ram* 2003-2024, Dodge Charger 2006-2023, Dodge Challenger 2009-2023, Chrysler 300 2005-2023, Dodge Magnum 2005-2008, Jeep Grand Cherokee 2005-2021, Dodge Durango 2011-2023, Jeep Commander 2006-2009, Chrysler Aspen 2007-2009
- **alternator — verified evidence:** TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-11298 (Chrysler 5602869, Denso 7S) Ram 5.7 2007-2008.
  - Group 1: Dodge|Ram Ram* 2007-2008
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### mopar-magnum — Dodge Magnum 5.2/5.9 V8

- **Engine:** 5.2/5.9L 8-cyl
- **Family applications:** Dodge|Ram Ram* 1994-2001, Dodge Dakota 1992-2003, Dodge Durango 1998-2003, Jeep Grand Cherokee 1993-1998
- **alternator — verified evidence:** Lester 13354 (Denso 121000-3530, Chrysler 56027912) application list (maniacelectricmotors.com + aspwholesale.com, retrieved 2026-10-22): Dakota 1992-1998, Ram 1500/2500/3500 1994-1998, Durango 1998, Grand Cherokee 5.2/5.9 1993-1998, Ramcharger 1992-1993. Corroborated by Lester 13742 (Chrysler 56027913, 136A) with the same spans. Lester 13920/13914 (Bosch/Denso 136A, Chrysler 56028237) application table (dssautoparts.com): Ram 1999-2003, Durango 5.9 2001-2003.
  - Group 1: Dodge|Ram Ram* 1994-1998; Dodge Dakota 1992-1998; Dodge Durango 1998-1998; Jeep Grand Cherokee 1993-1998
  - Group 2: Dodge|Ram Ram* 1999-2001; Dodge Durango 2001-2003
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### mopar-minivan — Chrysler 3.3/3.8 OHV V6

- **Engine:** 3.3/3.8L 6-cyl
- **Family applications:** Dodge Caravan 1996-2007, Dodge Grand Caravan 1996-2010, Chrysler Town & Country 1996-2010, Chrysler Town And Country 1996-2010, Plymouth|Chrysler Voyager 1996-2003, Jeep Wrangler 2007-2011
- **alternator — verified evidence:** TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-11295 (Chrysler 4801304AC) Caravan 3.3/3.8 2008-2010.
  - Group 1: Dodge Grand Caravan 2008-2010
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### mopar-pentastar — Chrysler Pentastar 3.6 V6

- **Engine:** 3.6L 6-cyl
- **Family applications:** Dodge Grand Caravan 2011-2020, Chrysler Town & Country 2011-2016, Chrysler Town And Country 2011-2016, Dodge Journey 2011-2020, Dodge Avenger 2011-2014, Chrysler 200 2011-2017, Dodge Charger 2011-2023, Dodge Challenger 2011-2023, Chrysler 300 2011-2023, Dodge Durango 2011-2024, Jeep Grand Cherokee 2011-2021, Jeep Wrangler 2012-2018, Dodge|Ram Ram* 2013-2024
- **alternator — verified evidence:** TYC 2-11570 fitment list (finditparts.com) + BBB 11570 table (partcatalog.com; Chrysler 68272108AD, Denso 421000-0770, retrieved 2026-10-22): Grand Caravan 2011-2020, Town & Country 2011-2016, Journey 3.6 2011-2019, Avenger 3.6 2011-2014, 200 3.6 2011-2014.
  - Group 1: Dodge Grand Caravan 2011-2020; Chrysler Town & Country 2011-2016; Chrysler Town And Country 2011-2016; Dodge Journey 2011-2019; Dodge Avenger 2011-2014; Chrysler 200 2011-2014
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### mopar-pt24 — Chrysler PT Cruiser 2.4 I4

- **Engine:** 2.4L 4-cyl
- **Family applications:** Chrysler PT Cruiser 2001-2010
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), non-turbo rows: 210-4177 (120A) PT Cruiser 2002; 210-4201 (100A) PT Cruiser 2003-2005; 210-4228 (100A) PT Cruiser 2006-2010. GT/Turbo takes separate 130-145A units (210-0558/0559/0803) — noted, and 2001 is not in this edition — left at likely.
  - Group 1: Chrysler PT Cruiser 2002-2002
  - Group 2: Chrysler PT Cruiser 2003-2005
  - Group 3: Chrysler PT Cruiser 2006-2010
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### mopar-world24 — Chrysler World/GEMA 2.4 I4

- **Engine:** 2.4L 4-cyl
- **Family applications:** Dodge Avenger 2008-2014, Chrysler 200 2011-2014, Dodge Journey 2009-2020, Dodge Caliber 2007-2012, Jeep Patriot 2007-2017, Jeep Compass 2007-2017, Chrysler Sebring 2007-2010
- **alternator — verified evidence:** Lester 11231 (Chrysler 4801323AC, Mitsubishi A2TJ0481) application tables (qpselectric.com + thenthgear.com + TYC 2-11231, retrieved 2026-10-22): Sebring 2.4 2007-2010, 200 2.4 2011-2013, Avenger 2.4 2008-2013, Caliber 2007-2012, Compass 2007-2017, Patriot 2007-2017. Journey uses a different unit — left at likely.
  - Group 1: Chrysler Sebring 2007-2010; Chrysler 200 2011-2013; Dodge Avenger 2008-2013; Dodge Caliber 2007-2012; Jeep Compass 2007-2017; Jeep Patriot 2007-2017
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### nissan-hr16 — Nissan HR16DE 1.6 I4

- **Engine:** 1.6L 4-cyl
- **Family applications:** Nissan Versa 2012-2019, Nissan Versa Note 2014-2019
- **alternator — verified evidence:** Nissan OEM 23100-3BE1A fitment (nissanpartsdeal.com, retrieved 2026-10-22): Versa 1.6 HR16DE 2012-2019, Versa Note 1.6 2014-2019. Cross-referenced Lester 11547 / Mitsubishi A2TJ1791 vendor tables show identical spans.
  - Group 1: Nissan Versa 2012-2019; Nissan Versa Note 2014-2019
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### nissan-ka24 — Nissan KA24DE 2.4 I4

- **Engine:** 2.4L 4-cyl
- **Family applications:** Nissan Altima 1993-2001, Nissan 240SX 1991-1998, Nissan Frontier 1998-2004, Nissan Xterra 2000-2004
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3146 (100A) Altima KA24DE 1998-2001; 210-3156 (70A) Frontier and Xterra KA24DE 2002-2004; 210-3118 (70A) Frontier 1998-2000 and Xterra 2000. 240SX/early Altima use other units — left at likely.
  - Group 1: Nissan Altima 1998-2001
  - Group 2: Nissan Frontier 2002-2004; Nissan Xterra 2002-2004
  - Group 3: Nissan Frontier 1998-2000; Nissan Xterra 2000-2000
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### nissan-mr18 — Nissan MR18DE 1.8 I4

- **Engine:** 1.8L 4-cyl
- **Family applications:** Nissan Versa 2007-2012, Nissan Cube 2009-2014
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4301 (110A) Versa MR18DE 2007-2009 (to 09/2008) and Cube MR18DE 2009; 210-4329 (110A, 7-groove) Cube 2010-2012.
  - Group 1: Nissan Versa 2007-2009; Nissan Cube 2009-2009
  - Group 2: Nissan Cube 2010-2012
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### nissan-mr20 — Nissan MR20DE 2.0 I4

- **Engine:** 2.0L 4-cyl
- **Family applications:** Nissan Sentra 2007-2012
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4301 (110A) Sentra 2.0 MR20DE 2007-2010 (the same list serves the Versa 1.8 and NV200). 2011-2012 Sentra 2.0 keeps the MR20DE but is past this catalog edition — left at likely.
  - Group 1: Nissan Sentra 2007-2010
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### nissan-qr25 — Nissan QR25DE 2.5 I4

- **Engine:** 2.5L 4-cyl
- **Family applications:** Nissan Altima 2002-2018, Nissan Sentra 2002-2006, Nissan Rogue 2008-2020, Nissan Frontier 2005-2019
- **alternator — verified evidence:** TYC 2-13939 application table (tycamericas.com, retrieved 2026-10-22) + DB Electrical 400-44053 (Lester 13939, Hitachi LR1110-726): Altima 2.5 2002-2006, Sentra 2.5 (SE-R/Spec V) 2002-2006.
  - Group 1: Nissan Altima 2002-2006; Nissan Sentra 2002-2006
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### nissan-vk56 — Nissan VK56DE 5.6 V8

- **Engine:** 5.6L 8-cyl
- **Family applications:** Nissan Titan 2004-2015, Nissan Armada 2005-2015, Nissan Pathfinder Armada 2004-2004, Infiniti QX56 2004-2010
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3160 (130A) engine-coded VK56DE — Titan 2004-2006, Armada 2005-2006, Pathfinder Armada 2004. Later VK56DE years are past this catalog edition — left at likely.
  - Group 1: Nissan Titan 2004-2006; Nissan Armada 2005-2006; Nissan Pathfinder Armada 2004-2004
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### nissan-vq35de — Nissan/Infiniti VQ35DE 3.5 V6

- **Engine:** 3.5L 6-cyl
- **Family applications:** Nissan Altima 2002-2006, Nissan Maxima 2002-2014, Nissan Murano 2003-2014, Nissan Pathfinder 2001-2004, Nissan Quest 2004-2009, Nissan 350Z 2003-2006, Infiniti G35 2003-2006, Infiniti I35 2002-2004, Infiniti FX35 2003-2008
- **alternator — verified evidence:** OCPTY Lester 13940 listing (Hitachi LR1110-721, Nissan 23100-8J100, retrieved 2026-10-22): Altima 3.5 2002-2006, Maxima 2002-2003, Murano 2003-2007, Infiniti I35 2002-2004. Nissan OEM 23100-7Y020 (nissanpartsdeal.com): Maxima 3.5 2004-2008 is a separate unit. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4255 (130A) Maxima 3.5 2009-2010 and Murano 2009 — later A35 Maximas (2011-14) use the same VQ35DE but this catalog edition ends there, left at likely.
  - Group 1: Nissan Altima 2002-2006; Nissan Maxima 2002-2003; Nissan Murano 2003-2007; Infiniti I35 2002-2004
  - Group 2: Nissan Maxima 2004-2008
  - Group 3: Nissan Maxima 2009-2010; Nissan Murano 2009-2009
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### nissan-vq40 — Nissan VQ40DE 4.0 V6

- **Engine:** 4.0L 6-cyl
- **Family applications:** Nissan Pathfinder 2005-2012, Nissan Frontier 2005-2019, Nissan Xterra 2005-2015
- **alternator — verified evidence:** Nissan OEM 23100-EA20B fitment (nissanpartsdeal.com, retrieved 2026-10-22): Frontier/Pathfinder/Xterra 4.0 2005-2008 (110A). Nissan 23100-ZH00D (130A): Frontier 4.0 2007-2019. Match amperage — both units appear in the 07-08 overlap.
  - Group 1: Nissan Frontier 2005-2008; Nissan Pathfinder 2005-2008; Nissan Xterra 2005-2008
  - Group 2: Nissan Frontier 2007-2019
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### subaru-ej25na — Subaru EJ25 2.5 SOHC H4 (non-turbo)

- **Engine:** 2.5L 4-cyl
- **Family applications:** Subaru Outback 2000-2009, Subaru Legacy 2000-2009, Subaru Forester 1999-2010, Subaru Impreza 2006-2011, Subaru Baja 2003-2006
- **Ambiguity cap:** Subaru Outback — XT models are the turbo EJ255 — same 2.5 decode string; confirm non-turbo
- **Ambiguity cap:** Subaru Legacy — GT models are the turbo EJ255 — same 2.5 decode string; confirm non-turbo
- **Ambiguity cap:** Subaru Forester — XT models are the turbo EJ255 — same 2.5 decode string; confirm non-turbo
- **Ambiguity cap:** Subaru Impreza — WRX/turbo models share the 2.5 decode string; confirm non-turbo
- **Ambiguity cap:** Subaru Baja — Baja Turbo shares the 2.5 decode string; confirm non-turbo
- **alternator — verified evidence:** Subaru OEM 23700-AA31A/AA37A/AA430 listing (LEESENEVO/amazon.com, retrieved 2026-10-22): Legacy 2.5 2005-2009, Outback 2.5 2005-2009. Forester/Impreza 2.5 use 23700-AA52x — a different unit, left at likely.
  - Group 1: Subaru Legacy 2005-2009; Subaru Outback 2005-2009
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### subaru-ej25t — Subaru EJ255/EJ257 2.5 turbo H4

- **Engine:** 2.5L 4-cyl
- **Family applications:** Subaru Impreza 2006-2014, Subaru WRX 2008-2014, Subaru Impreza WRX 2006-2014, Subaru Forester 2004-2013, Subaru Legacy 2005-2012, Subaru Outback 2005-2009, Subaru Baja 2004-2006
- **Ambiguity cap:** Subaru Impreza — only WRX/STI trims carry the turbo EJ — confirm turbo before buying
- **Ambiguity cap:** Subaru Forester — only XT trims are turbo — confirm before buying
- **Ambiguity cap:** Subaru Legacy — only GT trims are turbo — confirm before buying
- **Ambiguity cap:** Subaru Outback — only XT trims are turbo — confirm before buying
- **Ambiguity cap:** Subaru Baja — only Baja Turbo is turbo — confirm before buying
- **alternator — verified evidence:** Mitsubishi A3TG0491 / Subaru 23700-AA520/AA521/AA570 application list (maniacelectricmotors.com + HC-Cargo 115453, retrieved 2026-10-22): Forester XT 2006-2010, Impreza WRX/STI 2006-2010, Legacy GT 2005, Outback XT 2005, Saab 9-2X 2006. Subaru OEM 23700AA871 (subarupartsdeal.com): Forester XT 2011-2013, Impreza WRX/STI 2011-2014, WRX/WRX STI 2.5 turbo 2015-2020.
  - Group 1: Subaru Forester 2006-2010; Subaru Impreza 2006-2010; Subaru Impreza WRX 2006-2010; Subaru Legacy 2005-2005; Subaru Outback 2005-2005
  - Group 2: Subaru Forester 2011-2013; Subaru Impreza 2011-2014; Subaru Impreza WRX 2011-2014; Subaru WRX 2011-2014
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### subaru-fa20dit — Subaru FA20DIT 2.0 turbo H4

- **Engine:** 2.0L 4-cyl
- **Family applications:** Subaru WRX 2015-2021, Subaru Forester 2014-2018
- **Ambiguity cap:** Subaru Forester — only 2.0XT trims carry the FA20DIT — base Foresters are the 2.5 FB; confirm turbo
- **alternator — verified evidence:** Subaru OEM 23700AA911 (replaces AA910) fitment (subarupartsdeal.com, retrieved 2026-10-22): WRX 2.0 turbo 2015-2020. The Forester 2.0XT shares its unit with the FB25 Forester (23700AB030), not the WRX — left at likely.
  - Group 1: Subaru WRX 2015-2020
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### subaru-fb25 — Subaru FB25 2.5 H4

- **Engine:** 2.5L 4-cyl
- **Family applications:** Subaru Forester 2011-2018, Subaru Outback 2013-2019, Subaru Legacy 2013-2019
- **Ambiguity cap:** Subaru Forester — 11–13 XT is the turbo EJ255 — same 2.5 decode string; confirm FB non-turbo
- **alternator — verified evidence:** Subaru OEM fitment (subarupartsdeal.com, retrieved 2026-10-22): 23700AB030 (replaces 23700AA760/AA761) Forester 2014-2018 (2.5i and 2.0XT trims); 23700AA91B Legacy 2.5i 2015-2017; 23700AB01A Legacy/Outback 2.5i 2018-2019.
  - Group 1: Subaru Forester 2014-2018
  - Group 2: Subaru Legacy 2015-2017
  - Group 3: Subaru Legacy 2018-2019; Subaru Outback 2018-2019
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### toyota-1gr — Toyota 1GR-FE 4.0 V6

- **Engine:** 4.0L 6-cyl
- **Family applications:** Toyota Tacoma 2005-2015, Toyota 4Runner 2003-2021, Toyota Tundra 2005-2010, Toyota FJ Cruiser 2007-2014
- **alternator — verified evidence:** Lester 13984 listings (txasap.com: 4Runner 4.0 2003-2009; OEG amazon.com: Tacoma 4.0 2005-2015; Eagle High: FJ Cruiser 2007-2010, Tundra 4.0 2006-2010; Toyota 27060-31020/31021, Denso 104210-3470/4870, retrieved 2026-10-22).
  - Group 1: Toyota Tacoma 2005-2015; Toyota 4Runner 2003-2009; Toyota FJ Cruiser 2007-2010; Toyota Tundra 2006-2010
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### toyota-1mz — Toyota/Lexus 1MZ-FE 3.0 V6

- **Engine:** 3.0L 6-cyl
- **Family applications:** Toyota Camry 1994-2006, Toyota Avalon 1995-2004, Toyota Solara 1999-2003, Toyota Sienna 1998-2003, Toyota Highlander 2001-2003, Lexus ES 300 1994-2003, Lexus RX 300 1999-2003
- **alternator — verified evidence:** Hollander interchange 601-58691 (retrieved 2026-10-22) crosses Camry V6 97-01 = ES 300 97-01; Denso 101211-7440/7450 = Toyota 27060-20230 100A across the 1MZ family per Denso catalog + ToyotaNation cross-reference
  - Group 1: Toyota Camry 1997-2001; Lexus ES 300 1997-2001
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### toyota-1zz — Toyota/Pontiac 1ZZ-FE 1.8 I4

- **Engine:** 1.8L 4-cyl
- **Family applications:** Toyota Corolla 1998-2008, Toyota Matrix 2003-2008, Pontiac Vibe 2003-2008, Toyota Celica 2000-2005, Toyota MR2 Spyder 2000-2005
- **alternator — verified evidence:** TYC 2-13878 application table (tycamericas.com) + discountstarterandalternator.com VIN-qualified list (Lester 13878, Toyota 27060-22040, retrieved 2026-10-22): Corolla 1ZZ 2003-2008, Matrix 2003-2008 (excl XRS), Vibe 2003-2008 (excl GT), Celica GT 2000-2005, MR2 Spyder 2000-2005. 1998-2002 Corolla uses an earlier unit — left at likely.
  - Group 1: Toyota Corolla 2003-2008; Toyota Matrix 2003-2008; Pontiac Vibe 2003-2008; Toyota Celica 2000-2005; Toyota MR2 Spyder 2000-2005
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### toyota-22re — Toyota 22RE 2.4 I4 (EFI)

- **Engine:** 2.4L 4-cyl
- **Family applications:** Toyota Pickup 1985-1995, Toyota 4Runner 1985-1995
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0116 (60A) Pickup 22RE 1994-1995 and 1993 std; same unit listed for 4Runner 22RE w/ M/T only, while A/T trucks take 210-0297/0299 — transmission splits the unit, so only the unqualified Pickup 1994-1995 span is treated as verified.
  - Group 1: Toyota Pickup 1994-1995
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### toyota-2ar — Toyota/Scion 2AR-FE 2.5 I4

- **Engine:** 2.5L 4-cyl
- **Family applications:** Toyota Camry 2010-2017, Toyota RAV4 2009-2012, Toyota RAV4 2013-2018, Scion tC 2011-2016
- **alternator — verified evidence:** Denso 104210-2270/-2340 (Toyota 27060-36010/36011, Lester 11402) application tables (dcalltech.com + rareelectrical.com, retrieved 2026-10-22): Scion tC 2.5 2011-16, Camry 2.5 2012-15, RAV4 2.5 2009-12.
  - Group 1: Scion tC 2011-2016; Toyota Camry 2012-2015; Toyota RAV4 2009-2012
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### toyota-2az — Toyota/Scion 2AZ-FE 2.4 I4

- **Engine:** 2.4L 4-cyl
- **Family applications:** Toyota Camry 2002-2009, Toyota Solara 2004-2008, Toyota RAV4 2004-2008, Toyota Highlander 2001-2007, Scion tC 2005-2010, Scion xB 2008-2015, Toyota Matrix 2009-2013, Toyota Corolla 2009-2010
- **alternator — verified evidence:** TYC 2-11034 fitment table (standardautopart.com, retrieved 2026-10-22): Camry 2.4 04-06, Highlander 2.4 04-07, RAV4 04-05, Solara 2.4 04-08 + DB Electrical AND0288 adds tC 05-10 (Toyota 27060-0H100/28260/28270). Toyota 27060-0H111-84 OEM listing (toyota.oempartsonline.com, retrieved 2026-10-22): Camry 2.4 07-09, Matrix 2.4 09-13, Corolla 2.4 09-10.
  - Group 1: Toyota Camry 2004-2006; Toyota Highlander 2004-2007; Toyota RAV4 2004-2005; Toyota Solara 2004-2008; Scion tC 2005-2010
  - Group 2: Toyota Camry 2007-2009; Toyota Matrix 2009-2013; Toyota Corolla 2009-2010
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### toyota-2gr — Toyota/Lexus 2GR-FE 3.5 V6

- **Engine:** 3.5L 6-cyl
- **Family applications:** Toyota Camry 2007-2017, Toyota Avalon 2005-2018, Toyota Sienna 2007-2016, Toyota Highlander 2008-2016, Toyota RAV4 2006-2012, Toyota Venza 2009-2015, Lexus ES 350 2007-2018, Lexus RX 350 2007-2015
- **alternator — verified evidence:** TYC 2-11137 application table (tycamericas.com, retrieved 2026-10-22; Toyota 27060-31111-84, Lester 11137, 130A): Camry 3.5 2007-2017, Avalon 2005-2018, Highlander 3.5 2008-2013, RAV4 3.5 2009-2010, Venza 3.5 2009-2015, ES 350 2007-2018, RX 350 2007-2009. Sienna and RAV4 06-08 are NOT in this unit — left at likely.
  - Group 1: Toyota Camry 2007-2017; Toyota Avalon 2005-2018; Toyota Highlander 2008-2013; Toyota RAV4 2009-2010; Toyota Venza 2009-2015; Lexus ES 350 2007-2018; Lexus RX 350 2007-2009
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### toyota-2uz — Toyota/Lexus 2UZ-FE 4.7 V8

- **Engine:** 4.7L 8-cyl
- **Family applications:** Toyota Tundra 2000-2009, Toyota Sequoia 2001-2009, Toyota Land Cruiser 1998-2007, Toyota 4Runner 2003-2009, Lexus GX 470 2003-2009, Lexus LX 470 1998-2007
- **alternator — verified evidence:** Lester 13994 application list (aspwholesale.com, retrieved 2026-10-22; Denso 104210-3380, Toyota 27060-0F040): Tundra 4.7 2003-2009, Sequoia 4.7 2003-2009. Toyota lists a separate OEM number (27060-50320-84) for the 4.7 4Runner — kept out of the group.
  - Group 1: Toyota Tundra 2003-2009; Toyota Sequoia 2003-2009
- **starter:** no verified group — Likely tier only. Note: under-intake starter on 2UZ — match the part number — nose cone / tooth count can differ

### toyota-2zr — Toyota/Scion 2ZR-FE 1.8 I4

- **Engine:** 1.8L 4-cyl
- **Family applications:** Toyota Corolla 2009-2010, Toyota Corolla 2011-2019, Toyota Matrix 2009-2013, Pontiac Vibe 2009-2010, Scion xD 2008-2014
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0699 (100A clutch pulley) Scion xD 1.8 2008-2009 and Corolla 1.8 2009 (Japan-built). Later 2ZR Corolla/Matrix years use successor units — left at likely.
  - Group 1: Scion xD 2008-2009; Toyota Corolla 2009-2009
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### toyota-3mz — Toyota/Lexus 3MZ-FE 3.3 V6

- **Engine:** 3.3L 6-cyl
- **Family applications:** Toyota Camry 2004-2006, Toyota Solara 2004-2008, Toyota Sienna 2004-2006, Toyota Highlander 2004-2007, Lexus ES 330 2004-2006, Lexus RX 330 2004-2006
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0543 (100A std) Lexus ES330 2004-2006, RX330 2004-2006 (Japan-built std), Camry 3.3 2004, Highlander 3.3 2004-2007; 210-0545 (130A opt) RX330 2004-2006 (US-built opt) and Sienna 3.3 2004-2006. Amp option splits noted in research notes.
  - Group 1: Lexus ES 330 2004-2006; Lexus RX 330 2004-2006; Toyota Camry 2004-2004; Toyota Highlander 2004-2007
  - Group 2: Lexus RX 330 2004-2006; Toyota Sienna 2004-2006
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### toyota-5s — Toyota 5S-FE 2.2 I4

- **Engine:** 2.2L 4-cyl
- **Family applications:** Toyota Camry 1992-2001, Toyota Celica 1994-1999, Toyota Solara 1999-2001, Toyota MR2 1991-1995
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0187 (80A) Camry 5SFE 1997-2001 and Solara 5SFE 1999 and 2001. Celica/MR2 5S use earlier units — left at likely.
  - Group 1: Toyota Camry 1997-2001; Toyota Solara 1999-2001
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### toyota-5vz — Toyota 5VZ-FE 3.4 V6

- **Engine:** 3.4L 6-cyl
- **Family applications:** Toyota Tacoma 1995-2004, Toyota 4Runner 1996-2002, Toyota T100 1995-1998, Toyota Tundra 2000-2004
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows engine-coded 5VZFE 3.4: 210-0447 (60A) Tacoma 1995-1996 and 1998-1999, T100 1995-1998, 4Runner 1998, Tundra 2000 std; 210-0180 (70A) 4Runner 1996-1998, T100 1997-1998, Tacoma 1997-1999, Tundra 2000-2002; 210-0434 (80A) 4Runner 1999-2002, Tacoma 2000-2004, Tundra 2001-2002 and 2000 opt; 210-0513 (80A) Tundra 2003-2004.
  - Group 1: Toyota Tacoma 1995-1996; Toyota Tacoma 1998-1999; Toyota T100 1995-1998; Toyota 4Runner 1998-1998; Toyota Tundra 2000-2000
  - Group 2: Toyota 4Runner 1996-1998; Toyota T100 1997-1998; Toyota Tacoma 1997-1999; Toyota Tundra 2000-2002
  - Group 3: Toyota 4Runner 1999-2002; Toyota Tacoma 2000-2004; Toyota Tundra 2000-2002
  - Group 4: Toyota Tundra 2003-2004
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### toyota-rz — Toyota 2RZ/3RZ-FE 2.4/2.7 I4

- **Engine:** 2.4/2.7L 4-cyl
- **Family applications:** Toyota Tacoma 1995-2004, Toyota 4Runner 1996-2000, Toyota T100 1994-1998
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), identical units for the 2.4 (2RZFE) and 2.7 (3RZFE) in every year row: 210-0448 (60A) Tacoma 1995-1996, T100 2.7 1994-1996; 210-0188 (70A) Tacoma 1997-1999, T100 2.7 1997-1998, 4Runner 2.7 1996-1999; 210-0390 (80A) Tacoma 2000-2004, 4Runner 2.7 2000 (the same list runs to the 2005 base-2.7 Tacoma, outside this family's years).
  - Group 1: Toyota Tacoma 1995-1996; Toyota T100 1994-1996
  - Group 2: Toyota Tacoma 1997-1999; Toyota T100 1997-1998; Toyota 4Runner 1996-1999
  - Group 3: Toyota Tacoma 2000-2004; Toyota 4Runner 2000-2000
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### vw-25 — VW 2.5 I5

- **Engine:** 2.5L 5-cyl
- **Family applications:** Volkswagen Jetta 2005-2014, Volkswagen Rabbit 2006-2009, Volkswagen Golf 2010-2014, Volkswagen Beetle 2012-2014, Volkswagen Passat 2012-2014
- **alternator — verified evidence:** Lester 11254 (VW 07K903023A, Bosch 0-124-525-062) fitment (A-Premium APALT130 + miamialternators.com, retrieved 2026-10-22): Jetta 2.5 2005-2014, Rabbit 2.5 2006-2009, Golf 2.5 2010-2014.
  - Group 1: Volkswagen Jetta 2005-2014; Volkswagen Rabbit 2006-2009; Volkswagen Golf 2010-2014
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

## Accuracy-forced exclusions (kept at Likely)

- **ford-3g-50 / Mustang 5.0 1987-1995** — 94-95 Mustang uses the pivot-mount
  3G; 87-93 trucks use the 2G. Only the 93-96 side-mount truck unit (Lester
  7750) is verified.
- **toyota-22re / 4Runner + A/T-M/T split** — Denso lists separate 60A (M/T)
  and 70A (A/T) units for the same model-years. Only the unqualified Pickup
  1994-1995 span is verified.
- **ford-vulcan30 (whole family)** — every Taurus application is ambiguous
  (Vulcan vs Duratec share year/make/model), so the verified tier is
  intentionally unreachable.
- **gm-60deg W-cars (Grand Am, Alero, Impala, Malibu 3.4)** — CS130D-era units
  with multiple amp options; only the 02-05 Venture/Montana van unit (Lester
  13993) is verified.
- **hk-gamma16 / Kia Soul** — Soul 1.6 uses 37300-2B760 (Lester 11609), a
  different unit from the Accent/Veloster/Rio 37300-2B300.
- **acura-j32 / TL 2004-2008** — J32A3 uses Denso 210-0580, not the 00-03 unit.
- **honda-r18 / Civic 2012-2015** — R18Z uses a successor unit.
- **toyota-2zr / Corolla 2010+, Matrix, Vibe** — later 2ZR years use successor
  units; only the 08-09 Japan-built unit is verified.
- **gm-3800 W-bodies, 99-02 GM trucks (AD230 era), Mustang-vs-truck 4.6,
  RAV4/Sienna 3.5 vs 2GR sedans, CR-V 02-06 vs K24A, 99-01 Odyssey,
  Mazda6 vs Fusion MZR, 2012-16 Cruze 1.4T** — all documented in the
  respective family evidence strings; each stays Likely because the published
  lists split them from the verified unit.
- **gm-vortec43 / S-10 + Blazer model-year 2000** — the Denso catalog splits
  2000 S-trucks mid-year by VIN sequence (<230,000 vs >230,000); no
  unqualified 2000 span exists, so 2000 stays Likely.
- **cadillac-northstar / 1994-1996** — every 94-96 row carries a "w/o heated
  windshield" qualifier; only the unqualified 1997 rows, 98-99, 01-05 and
  06-11 DTS spans are verified. 2000 Deville/Seville rows are absent from the
  catalog edition entirely.
- **gm-vortec-van / 2001-2004 + 2009-2010** — the 96-00 and 05-08 lists are
  clean; 01-04 vans are absent from this catalog edition and 09-10 split by
  alternator case diameter.
- **mopar-pt24 / 2001 and GT Turbo** — 2001 is not in the catalog edition;
  the turbo takes separate 130-145A units (210-0558/0559/0803).
- **hk-alpha / Accent 2003-2009** — Mando-vs-Valeo vendor qualifiers on every
  row; stays Likely.
- **mini-r50 / 2006+** — the 2006 base rows and all R56 (2007+) hardtops are
  outside the verified lists; the supercharged S splits by trim throughout.
- **nissan-mr20 / Sentra 2011-2012, nissan-vk56 / 2007-2015,
  nissan-vq35de / Maxima 2011-2014, ford-escape-16eb+20eb / 2015-2016,
  mopar-dart / 2016** — the engines carry over but the Denso catalog edition
  ends at MY2015-ish; later years stay Likely until a published list is found.
- **hk-mu-lambda / 2009+ and Veracruz/Entourage** — 2009+ rows carry
  Denso-vs-Mitsubishi vendor qualifiers; Veracruz and Entourage have no rows
  in this edition at all (family membership is still correct, so Likely).

## Inventory-weighted gap audit (2026-10-22)

`scraper/interchange_gap_audit.py` ranks (make, model, contiguous-year)
clusters by live-vehicle count where NO engine family matches — i.e. the
Parts tab answers "no interchange data". Coverage (share of the 251,732
inventory vehicles inside ≥1 family) moved **63.3% → 70.0%** in this pass
(+16,936 vehicles). Top-25 clusters before the pass, with status after:

| # | Cluster | Cars | Status after this pass |
|---|---------|------|------------------------|
| 1 | Ford Focus 2012-2018 | 2,877 | **Still no data** — the 2.0 GDI/ST/1.0T lists aren't in the Denso edition and live fitment sources were unreachable this session; left honest |
| 2 | Nissan Sentra 2007-2026 | 2,728 | **Partially filled** — nissan-mr20 covers 07-12 (verified 07-10); 2013+ (MRA8DE) still no data, same source gap |
| 3 | Ford Fusion 2013-2020 | 1,574 | **Partially filled** — ford-mzr extended; 13-14 verified via Denso 210-0615 (one unit spans the 2.5 and 2.0T); 15-20 still no data |
| 4 | Ford Escape 2013-2025 | 1,404 | **Partially filled** — ford-escape-16eb/-20eb added, 13-14 verified per displacement; 2017+ still no data |
| 5 | Chevrolet Malibu 2013-2024 | 1,330 | **Still no data** — 2013 column exists (Denso 210-0255) but 14+ start/stop and 16+ 1.5T/2.0T have no clean published spans in reach |
| 6 | Toyota Prius 2001-2016 | 1,214 | **Permanently excluded** — hybrids have no belt alternator and no conventional starter (MG1 spins the engine); "no data" is the correct answer |
| 7 | Cadillac CTS 2003-2017 | 961 | **Filled** — gm-llt36 extended; verified groups 04-05, 08-09, 10-13 |
| 8 | Ford Fiesta 2011-2019 | 911 | **Still no data** — not in the Denso edition; live sources unreachable |
| 9 | Hyundai Santa Fe 2001-2023 | 905 | **Partially filled** — hk-mu-lambda covers the 07-09 V6 (verified 07-08); 01-06 multi-vendor rows and 10+ left honest |
| 10 | BMW 3 Series 1990-2017 | 904 | **Still no data** — Bosch/Valeo splits need a source beyond this catalog |
| 11 | Chrysler PT Cruiser 2001-2010 | 870 | **Filled** — mopar-pt24; verified 02, 03-05, 06-10 (non-turbo) |
| 12 | Nissan Maxima 2009-2014 | 792 | **Filled (partial verify)** — vq35de app extended; 09-10 verified, 11-14 likely |
| 13 | Saturn VUE 2002-2010 | 705 | **Filled** — VUE apps on gm-ecotec22 (verified 04-07) and gm-ecotec24 (verified 08-10) |
| 14 | Nissan Pathfinder 2013-2020 | 659 | **Still no data** — R52 3.5 lists not in this edition |
| 15 | Cadillac SRX 2004-2016 | 657 | **Filled (partial verify)** — gm-llt36; 04-09 verified with STS, 10+ likely (pulley splits) |
| 16 | Audi A4 1996-2018 | 635 | **Still no data** — needs a Euro-vendor source |
| 17 | Dodge Dart 2013-2016 | 633 | **Filled** — mopar-dart; 13-15 verified, 2016 likely |
| 18 | Honda Accord 1983-1997 | 629 | **Filled** — honda-a20 (86-89 verified) + honda-f22 (90-93, 94-97 verified); 83-85 left out (carb-era splits) |
| 19 | Cadillac Deville 1983-2005 | 623 | **Filled (94+)** — cadillac-northstar; 97, 98-99, 01-05 verified; pre-94 4.1/4.5/4.9 left out |
| 20 | Mercedes C-Class 1994-2017 | 606 | **Still no data** — needs a Euro-vendor source |
| 21 | Chevrolet Express 1996-2016 | 595 | **Filled** — gm-vortec43 (4.3) + gm-vortec-van (V8); 96-00 and 05-08 verified; 01-04/09+ likely |
| 22 | Nissan Titan 2004-2018 | 580 | **Filled** — nissan-vk56 with Armada/Pathfinder Armada; 04-06 verified, 07-15 likely; 16+ (VK56VD) out of family |
| 23 | MINI Cooper 2002-2016 | 565 | **Partially filled** — mini-r50 covers 02-06 (verified 02-05); R56 07+ still no data |
| 24 | Chevrolet Blazer 1991-2005 | 531 | **Filled (95+)** — gm-vortec43; verified 95, 96-97, 98-99, 01-04; the 91-94 full-size 5.7 Blazer left out |
| 25 | Mazda 3 2004-2018 | 528 | **Filled** — ford-mzr app spellings fixed so bare "3"/"Mazda 3"/"Mazda3" all match; verified 04-09 (w/ Mazda5) and 10-11 |

Also fixed in this pass: Chrysler "Town And Country" feed spelling never
matched the "Town & Country" apps (the "&" squashes away) — both spellings
are now listed in mopar-pentastar and mopar-minivan, and the 2011-16 verified
group covers both.

## Triple spot-checks

Twenty random (seeker, donor, part) triples re-checked by hand against public
fitment data. Recorded below as they are performed.


| # | Family | Seeker | Donor | Fitment | Shown | Re-check verdict |
|---|--------|--------|-------|---------|-------|------------------|
| 1 | gm-ecotec22 | 2007 Saturn ION | 2006 Chevrolet Cobalt | likely | likely | PASS — ION 2.2 is not in the Lester 11140/11265 lists (Cobalt-only spans); plausible but unproven — maniacelectricmotors.com Cobalt page |
| 2 | ford-46-2v | 1997 Lincoln Town Car | 2005 Ford F-150 | likely | likely | PASS — Town Car uses the passenger-car 6G unit, F-150 the 3G truck unit — Lester 7791/8252 vs F75U lists keep them apart |
| 3 | nissan-vq35de | 2004 Infiniti G35 | 2006 Nissan Altima | likely | likely | PASS — G35 (23100-AM610) and Altima 3.5 (23100-9Y500) carry different OEM numbers — nissanpartsdeal.com |
| 4 | gm-gen4-truck | 2011 Chevrolet Suburban 1500 | 2008 Chevrolet Silverado 3500HD | likely | likely | PASS — TYC 2-08302 list covers 1500-series C/K 2007-2010 only; Suburban 2011 and 3500HD are outside it |
| 5 | gm-ecotec24 | 2013 Chevrolet Captiva Sport | 2008 Chevrolet HHR | likely | likely | PASS — Captiva 2.4 (13-15) uses the later Valeo unit, HHR 2.4 the 11265-era unit — am-autoparts.com 11265 list has no Captiva |
| 6 | vw-25 | 2013 Volkswagen Beetle | 2009 Volkswagen Jetta | likely | likely | PASS — Lester 11254 list (Jetta 05-14, Rabbit, Golf) does not include Beetle 2.5 — dbelectrical.com |
| 7 | ford-mzr | 2006 Ford Focus | 2009 Ford Focus | likely | likely | PASS — 05-07 and 08-11 Focus use different units (Lester 8516 vs 11292-era) — alternatorparts.com Ford listings |
| 8 | toyota-3mz | 2004 Toyota Sienna | 2005 Toyota Camry | likely | likely | PASS — Denso 210-0545 (Sienna) vs 210-0543 (Camry 2004 only; 2005 Camry 3MZ not listed) — Denso reman catalog |
| 9 | ford-cyclone | 2010 Ford Flex | 2008 Ford Taurus | verified | likely | PASS — Quality-Built 11271 list: Taurus 08-12 + Flex 09-12 — partshawk.com; shown Likely because both decode strings are EcoBoost-ambiguous |
| 10 | nissan-hr16 | 2018 Nissan Versa Note | 2014 Nissan Versa Note | verified | verified | PASS — Nissan OEM 23100-3BE1A fitment: Versa Note 2014-2019 — nissanpartsdeal.com |
| 11 | toyota-2ar | 2017 Toyota Camry | 2010 Toyota Camry | likely | likely | PASS — Denso 104210-2270 list covers Camry 12-15; neither 2010 nor 2017 is inside it — dbelectrical.com |
| 12 | honda-r18 | 2009 Honda Civic | 2008 Honda Civic | verified | verified | PASS — Denso 210-4236: Civic 1.8 2006-2011 — Denso reman catalog; TYC 2-11176 agrees |
| 13 | ford-54-3v | 2014 Ford Expedition | 2007 Ford F150 Pickup | likely | likely | PASS — The 09+ trucks changed units; our verified group is 05-08 — Lester 8318/11050 era lists |
| 14 | mopar-47 | 2009 Dodge Durango | 2001 Dodge Durango | likely | likely | PASS — Mopar 56029914AC fitment stops at Durango 2007; the 09 Durango (new body) is outside — jeeppartsdeal.com |
| 15 | honda-f23 | 1998 Honda Accord | 2002 Honda Accord | verified | verified | PASS — Denso 210-0192: Accord 2.3 1998-2002 — Denso reman catalog |
| 16 | ford-40sohc | 2005 Ford Explorer | 1998 Ford Explorer | likely | likely | PASS — 97-04 and 05-10 Explorer 4.0 use different units (Lester 7787 vs 8437 era) — alternatorparts.com |
| 17 | ford-3g-50 | 1988 Ford Mustang | 1989 Ford F-150 | likely | likely | PASS — 87-93 trucks/Mustangs are 2G-era; our verified group is the 93-96 3G side-mount (Lester 7750) — maniacelectricmotors.com |
| 18 | subaru-fb25 | 2016 Subaru Outback | 2014 Subaru Outback | likely | likely | PASS — Subaru OEM fitment splits Outback: AA770/AA820 (13-14) vs 91B/AB01A eras; 2014 vs 2016 cross units — subarupartsdeal.com |
| 19 | gm-atlas42 | 2007 GMC Envoy | 2004 Chevrolet Trailblazer | likely | likely | PASS — Lester 8290 (AD244 150A) covers Trailblazer/Envoy 02-05; 2006+ changed units — victortruck.com TYC table / aspwholesale |
| 20 | toyota-2gr | 2012 Toyota Highlander | 2009 Toyota RAV4 | verified | verified | PASS — TYC 2-11137 list: Highlander 3.5 2008-2013 + RAV4 3.5 2009-2010 — tycamericas.com |

All 20/20 spot-checks consistent with public fitment data (checked 2026-10-22). Random sample: seed 42 over families x inventory donors; seekers drawn from family application spans.
