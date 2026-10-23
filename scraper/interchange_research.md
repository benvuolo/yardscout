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

### acura-rdx — Acura RDX 2.3T I4 (1st gen)

- **Engine:** 2.3L 4-cyl
- **Family applications:** Acura RDX 2007-2012
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0788 (110A) RDX 2.3 K23A1 2007-2012 — one published unit, unqualified.
  - Group 1: Acura RDX 2007-2012
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-6018 RDX 2.3 2007-2009; 280-6019 RDX 2.3 2010-2012 — both unqualified.
  - Group 1: Acura RDX 2007-2009
  - Group 2: Acura RDX 2010-2012

### acura-rdx35 — Acura RDX 3.5 V6 (2nd gen)

- **Engine:** 3.5L 6-cyl
- **Family applications:** Acura RDX 2013-2018
- **alternator:** no verified group — Likely tier only. Note: match amperage, pulley and plug before buying — options packages used higher-amp units
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0440 RDX 3.5 J35Z2 2013-2015 — one published unit, unqualified.
  - Group 1: Acura RDX 2013-2015

### acura-rl — Acura RL 3.5/3.7 V6

- **Engine:** 3.5/3.7L 6-cyl
- **Family applications:** Acura RL 1996-2012
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows unqualified: 210-0204 (110A) RL 3.5 C35A1 1996-2004; 210-0580 (130A) RL 3.5 J35A8 2005-2008; 210-0750 (130A) RL 3.7 J37A2 2009-2012.
  - Group 1: Acura RL 1996-2004
  - Group 2: Acura RL 2005-2008
  - Group 3: Acura RL 2009-2012
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows unqualified: 280-4197 RL 3.5 1996-2004; 280-4328 RL 3.5 2005-2008; 280-0403 RL 3.7 2009-2010 (2011-12 is dual-listed with 280-0423/281-6001 — excluded).
  - Group 1: Acura RL 1996-2004
  - Group 2: Acura RL 2005-2008
  - Group 3: Acura RL 2009-2010

### acura-tl — Acura TL 3.2/3.5/3.7 V6

- **Engine:** 3.2/3.5/3.7L 6-cyl
- **Family applications:** Acura TL 1999-2014
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows unqualified: 210-0750 (130A) TL 3.5 (J35Z6) AND 3.7 (J37A4) 2009-2014 — one unit for both engines; 210-0580 (130A) TL 3.2 (J32A3) 2004-2008 and 3.5 (J35A8) 2007-2008; 210-0675 (105A) TL 3.2 2000-2003 base — Type S 02-03 uses its own unit (210-0453), so the verified span stops at 2001; 210-0444 (105A) TL 3.2 1999.
  - Group 1: Acura TL 2009-2014
  - Group 2: Acura TL 2004-2008
  - Group 3: Acura TL 2000-2001
  - Group 4: Acura TL 1999-1999
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-6000 TL 3.2 1999-2003 — one published row, unqualified (covers Type S too); 280-0403 TL 3.5 2009-2011 and 3.7 2009 — the 2009 model year has both engines on the one number. 04-08 and 10-14 rows split by transmission — excluded.
  - Group 1: Acura TL 1999-2003
  - Group 2: Acura TL 2009-2009

### bmw-m52 — BMW M50/M52/S50/S52 I6 (E36/E39/Z3)

- **Engine:** 2.5/2.8/3.0/3.2L 6-cyl
- **Family applications:** BMW 3 Series 1992-1999, BMW 325i 1992-1995, BMW 325is 1992-1995, BMW 328i 1996-1999, BMW 328is 1996-1998, BMW 323i 1998-1999, BMW 323is 1998-1999, BMW M3 1995-1999, BMW Z3 1996-2002, BMW 525i 1992-1995, BMW 528i 1997-2000
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5395 (140A) 528i 2.8 1997-1998 unqualified — the Z3 2.8 rows for the same unit are case-size-qualified and excluded; every other E36-era row is OEM-number- or case-qualified (Bosch vs Valeo sourcing) and excluded.
  - Group 1: BMW 528i 1997-1998
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5355 M3 3.2 1996-1999 and every Z3 1996-2002 (1.9/2.5/2.8/3.0/3.2 rows all carry the one number), unqualified; 280-5346 M3 3.0 1995.
  - Group 1: BMW M3 1996-1999; BMW Z3 1996-2002
  - Group 2: BMW M3 1995-1995

### bmw-m54 — BMW M54 2.5/3.0 I6 (E46/E39/E53/E85)

- **Engine:** 2.5/3.0L 6-cyl
- **Family applications:** BMW 3 Series 2000-2006, BMW 325i 2001-2006, BMW 325ci 2001-2006, BMW 325xi 2001-2006, BMW 330i 2001-2006, BMW 330ci 2001-2006, BMW 330xi 2001-2006, BMW 525i 2001-2003, BMW 530i 2001-2003, BMW X3 2004-2006, BMW X5 2001-2006, BMW Z4 2003-2005
- **alternator:** no verified group — Likely tier only. Note: every published M54 alternator row is OEM-number qualified (Bosch vs Valeo split) — all pairs stay Likely; match the number stamped on your unit
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5371 X5 3.0 2001-2006 unqualified — the one clean published M54 starter span (3-Series starter rows aren't published in this edition).
  - Group 1: BMW X5 2001-2006

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
- **alternator — verified evidence:** Lester 7750 (Ford F07U-10300, 3G 95A side-mount) application list (maniacelectricmotors.com, retrieved 2026-10-22): F-150/F-250 5.0/5.8 1993-1996, Bronco 5.0/5.8 1993-1996, E-150 5.0/5.8 1993-1996; 1987-93 trucks (2G era) left at likely. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5123 and 210-5305 both list Mustang 5.0 1988-1993 with identical spans (two published case styles — match yours); 210-5310 Mustang 5.0 1994-1995 and 5.8 1995 (the same list also covers the 3.8 those years).
  - Group 1: Ford F-150 1993-1996; Ford Bronco 1993-1996
  - Group 2: Ford Mustang 1988-1993
  - Group 3: Ford Mustang 1994-1995
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### ford-40ohv — Ford 4.0 OHV V6 (Explorer 1st gen)

- **Engine:** 4.0L 6-cyl
- **Family applications:** Ford Explorer 1991-1996, Ford Aerostar 1990-1997
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5210 (95A) Explorer 4.0 OHV 1991-1992 — unqualified (93-94 rows split by Limited trim, 95-98 by door keypad).
  - Group 1: Ford Explorer 1991-1992
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### ford-40sohc — Ford 4.0 SOHC V6

- **Engine:** 4.0L 6-cyl
- **Family applications:** Ford Explorer 1997-2000, Ford Explorer 2001-2010, Ford Explorer Sport Trac 2001-2010, Ford Ranger 2001-2011, Ford Mustang 2005-2010, Mercury Mountaineer 1998-2010, Ford Explorer Sport 2001-2003
- **Ambiguity cap:** Ford Explorer — 97–00 Explorers split 4.0 OHV vs 4.0 SOHC — same decode string; confirm SOHC
- **alternator — verified evidence:** TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-07787 (Ford 1L2Z-10346-AB) Explorer 4.0 1997-2003 (97-01 SOHC, 02-03 all); 2-08258 (1L5Z-10346-BA) Ranger 4.0 2001-2005; 2-08437 (6R3Z-10346-A) Mustang 4.0 2005-2008. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0701 (150A) Mustang 4.0 2009-2010; Mountaineer 4.0: 210-5320 (130A) 1998-2001 (one number covers OHV and SOHC), 210-5316 (130A) 2005-2008, 210-4307 (115A) 2009-2010, all unqualified (02-04 rows carry rear-cover/build-date qualifiers).
  - Group 1: Ford Explorer 1997-2003
  - Group 2: Ford Ranger 2001-2005
  - Group 3: Ford Mustang 2005-2008
  - Group 4: Ford Mustang 2009-2010
  - Group 5: Mercury Mountaineer 1998-2001
  - Group 6: Mercury Mountaineer 2005-2008
  - Group 7: Mercury Mountaineer 2009-2010
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### ford-46-2v — Ford 4.6 2V Modular V8

- **Engine:** 4.6L 8-cyl
- **Family applications:** Ford F-150 1997-2008, Ford F-150 Heritage 2004-2004, Ford Expedition 1997-2004, Ford Crown Victoria 1992-2011, Mercury Grand Marquis 1992-2011, Lincoln Town Car 1991-2011, Ford Mustang 1996-2004, Ford Explorer 2002-2005
- **alternator — verified evidence:** OEG/PartsPlayer listing for Ford F75U-10300-CA/CB 130A 3G (amazon.com, retrieved 2026-10-22): F-150 4.6/5.4 1997-2003, Expedition 5.4 1997-2002. TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-08252 Mustang 4.6 SOHC 99-04 is its own 6G unit; 2-07776 Crown Victoria 95-99; 2-07795 Grand Marquis 98-02.
  - Group 1: Ford F-150 1997-2003; Ford Expedition 1997-2002
  - Group 2: Ford Mustang 1999-2004
  - Group 3: Ford Crown Victoria 1995-1999
  - Group 4: Mercury Grand Marquis 1998-2002
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### ford-46-3v — Ford 4.6 3V Modular V8 (Mustang GT S197)

- **Engine:** 4.6L 8-cyl
- **Family applications:** Ford Mustang 2005-2010
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5367 (135A) Mustang 4.6 2006-2008 unqualified (the 2009 row for the same unit is transmission-qualified and excluded); 210-5355 (135A) Mustang 4.6 2005. 09-10 rows split by transmission — left at likely.
  - Group 1: Ford Mustang 2006-2008
  - Group 2: Ford Mustang 2005-2005
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### ford-54-2v — Ford 5.4 2V Triton V8

- **Engine:** 5.4L 8-cyl
- **Family applications:** Ford F-150 1997-2003, Ford F-150 Heritage 2004-2004, Ford Expedition 1997-2004
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

### ford-coyote — Ford Coyote 5.0 V8 (Mustang GT/F-150)

- **Engine:** 5.0L 8-cyl
- **Family applications:** Ford Mustang 2011-2023, Ford F-150 2011-2023, Ford F150* 2011-2023
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0533 (150A) Mustang 5.0 2012-2013 unqualified (the same published list covers the 3.7 and the 13 GT500 5.8); 210-0743 (200A) F-150 5.0 2012-2014 unqualified (the 11-14 'w/ Power Converter' rows are option-qualified and excluded).
  - Group 1: Ford Mustang 2012-2013
  - Group 2: Ford F-150 2012-2014; Ford F150* 2012-2014
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### ford-cyclone — Ford 3.5/3.7 Cyclone V6 (non-turbo)

- **Engine:** 3.5/3.7L 6-cyl
- **Family applications:** Ford Edge 2007-2015, Mercury Sable 2008-2009, Lincoln MKZ 2007-2012, Lincoln MKS 2009-2016, Lincoln MKX 2007-2015, Ford Taurus 2008-2019, Ford Explorer 2011-2019, Ford Flex 2009-2019, Ford Mustang 2011-2014, Ford Mustang 2011-2017, Ford F-150 2011-2014
- **Ambiguity cap:** Lincoln MKS — MKS EcoBoost is the 3.5 twin-turbo — same decode string; confirm non-turbo
- **Ambiguity cap:** Ford Taurus — SHO is the 3.5 EcoBoost twin-turbo — same decode string; confirm non-turbo
- **Ambiguity cap:** Ford Explorer — Explorer Sport/Platinum is 3.5 EcoBoost — same decode string; confirm non-turbo
- **Ambiguity cap:** Ford Flex — Flex EcoBoost shares the 3.5 decode string; confirm non-turbo
- **alternator — verified evidence:** DSS/TRQ Lester 11273 application table (Ford 7T4Z-10346-A, Mitsubishi A3TJ1291, retrieved 2026-10-22): Edge 2007-2014, Taurus 3.5 2008-2012. Quality-Built 11271 175A (Ford 8A4Z-10346-A, partshawk.com): Taurus 2008-2012, Flex 2009-2012, Edge 2011-2013, Explorer 2011-2012. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0533 (150A) Mustang 3.7 and 5.0 2012-2013 unqualified (11/14 rows split by transmission — excluded); 210-4316 (150A) Edge 3.5 2010-2015, Taurus 3.5 2008-2009 and 2012 (10-11 rows are option-qualified), Sable 3.5 2008-2009, MKZ 3.5 2011-2012.
  - Group 1: Ford Edge 2007-2014; Ford Taurus 2008-2012
  - Group 2: Ford Taurus 2008-2012; Ford Flex 2009-2012; Ford Edge 2011-2013; Ford Explorer 2011-2012
  - Group 3: Ford Mustang 2012-2013
  - Group 4: Ford Edge 2010-2015; Ford Taurus 2008-2009; Ford Taurus 2012-2012; Mercury Sable 2008-2009; Lincoln MKZ 2011-2012
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4266 MKZ 3.5 2007-2010; 280-4235 MKZ 3.5 2011-2012 — each one published unit, unqualified. Ford-badged rows in this catalog split by transmission/option — excluded.
  - Group 1: Lincoln MKZ 2007-2010
  - Group 2: Lincoln MKZ 2011-2012

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

### ford-escort — Ford Escort 1.9/2.0 I4

- **Engine:** 1.9/2.0L 4-cyl
- **Family applications:** Ford Escort 1991-2003, Ford Escort ZX2 1998-2003
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5218 (75A) Escort 1.9 1991-1993; 210-5200 (75A) Escort 1.9 1994-1996; 210-5203 and 210-5314 (95A) both list Escort 2.0 SPI 1998-2003 with identical spans (two published case styles — match yours); 210-5201 (75A) ZX2 2.0 Zetec 1997-2002, all unqualified.
  - Group 1: Ford Escort 1991-1993
  - Group 2: Ford Escort 1994-1996
  - Group 3: Ford Escort 1998-2003
  - Group 4: Ford Escort ZX2 1998-2002
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### ford-essex38 — Ford Essex 3.8/3.9 V6 (Mustang SN95)

- **Engine:** 3.8/3.9L 6-cyl
- **Family applications:** Ford Mustang 1994-2004
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5207 and 210-5310 both list Mustang 3.8 1994-2000 with identical spans (two published 130A case styles — match yours); 210-5348 (110A) Mustang 3.8 2001-2004 and 3.9 2004, unqualified.
  - Group 1: Ford Mustang 1994-2000
  - Group 2: Ford Mustang 2001-2004
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### ford-focus3 — Ford Focus 2.0 I4 (Mk3)

- **Engine:** 2.0L 4-cyl
- **Family applications:** Ford Focus 2012-2018
- **alternator:** no verified group — Likely tier only. Note: 2012+ alternator rows are not published unqualified in this catalog edition — pairs stay Likely
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4241 Focus 2.0 2012-2014 — the 13-14 rows list both 2.0 VIN engine codes (GDI and EcoBoost ST) on the one number, unqualified.
  - Group 1: Ford Focus 2012-2014

### ford-freestar — Ford Freestar/Mercury Monterey 3.9/4.2 V6

- **Engine:** 3.9/4.2L 6-cyl
- **Family applications:** Ford Freestar 2004-2007, Mercury Monterey 2004-2007
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5361 (135A) Freestar 3.9 2004-2006 AND 4.2 2004-2006 — one published unit for both engines, unqualified.
  - Group 1: Ford Freestar 2004-2006
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5314 Freestar 3.9 2004-2007 AND 4.2 2004-2007 — one published unit for both engines, unqualified.
  - Group 1: Ford Freestar 2004-2007

### ford-mod-sd — Ford Modular 4.6/5.4 V8 (Super Duty/E-Series/Navigator)

- **Engine:** 4.6/5.4L 8-cyl
- **Family applications:** Ford F-250* 1999-2010, Ford F250* 1999-2010, Ford F-350* 1999-2010, Ford F350* 1999-2010, Ford Excursion 2000-2005, Ford E-150* 1997-2014, Ford E150* 1997-2014, Ford E-250* 1997-2014, Ford E-350* 1997-2014, Ford E-Series 1997-2014, Ford Econoline* 1997-2014, Lincoln Navigator* 1998-2014, Ford Navigator* 1998-2014
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5350 (110A) F-250 Super Duty 5.4 and V10 6.8 2002-2003, unqualified; 210-5205 (115A) Navigator 5.4 2000-2002; 210-0760 (150A) Navigator 5.4 2005-2009. E-Series rows split by case diameter/battery-post options and stay Likely.
  - Group 1: Ford F-250* 2002-2003; Ford F250* 2002-2003
  - Group 2: Lincoln Navigator* 2000-2002; Ford Navigator* 2000-2002
  - Group 3: Lincoln Navigator* 2005-2009; Ford Navigator* 2005-2009
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5315 — one published gas starter for F-250 Super Duty 5.4 and V10 6.8 1999-2008 AND Navigator 5.4 1999-2014 (2009 splits by build date on the SD); 280-5312 — one published starter for E-150 4.6 and 5.4 1997-2012 and Econoline Super Duty 5.4/V10 1997-1999.
  - Group 1: Ford F-250* 1999-2008; Ford F250* 1999-2008; Lincoln Navigator* 1999-2014; Ford Navigator* 1999-2014
  - Group 2: Ford E-150* 1997-2012; Ford E150* 1997-2012; Ford Econoline* 1997-1999

### ford-mzr — Ford/Mazda MZR-Duratec 2.0/2.3/2.5 I4

- **Engine:** 2.0/2.3/2.5L 4-cyl
- **Family applications:** Ford Fusion 2006-2014, Ford Escape 2005-2012, Ford Focus 2005-2011, Mazda 3 2004-2013, Mazda 5 2006-2010, Mazda 6 2003-2013, Mercury Milan 2006-2011, Mercury Mariner 2005-2011, Mazda Tribute 2005-2011, Ford Ranger 2001-2011
- **alternator — verified evidence:** Lester 11172 application table (cautop.com; Mitsubishi A3TJ0891, Ford 6E5Z-10346-AA, retrieved 2026-10-22): Fusion 2.3 2006-2009, Milan 2.3 2006-2009. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4214 (90A) Mazda3 2.0 2004-2009, Mazda3 2.3 2004-2006 and non-turbo 2007-2009, Mazda5 2.3 2006-2007; 210-4303 (100A) Mazda3 2.0 2010-2011; 210-4327 (110A) Mazda5 2.3 2008-2010; 210-4238 (100A) Mazda6 2.3 2008 and 2.5 2009; 210-0615 (170A) Fusion 2.5 AND 2.0 Turbo 2013-2014 (one unit spans both engines); 210-4304 (150A) Focus 2.0 2009-2010 unqualified (2008 splits by trim vendor, 2011 is Mitsubishi-unit-qualified). Mazda6 2.3 03-05 splits by transmission and Mazdaspeed turbos differ — left at likely.
  - Group 1: Ford Fusion 2006-2009; Mercury Milan 2006-2009
  - Group 2: Mazda 3 2004-2009; Mazda 5 2006-2007
  - Group 3: Mazda 3 2010-2011
  - Group 4: Mazda 5 2008-2010
  - Group 5: Mazda 6 2008-2009
  - Group 6: Ford Fusion 2013-2014
  - Group 7: Ford Focus 2009-2010
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### ford-tc — Ford Transit Connect 1.6/2.0/2.5

- **Engine:** 1.6/2.0/2.5L 4-cyl
- **Family applications:** Ford Transit Connect 2010-2014
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4304 (150A) Transit Connect 2.0 2010 and 2012-2013 unqualified (the 2011 row carries a Mitsubishi-unit qualifier — excluded).
  - Group 1: Ford Transit Connect 2010-2010; Ford Transit Connect 2012-2013
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

### ford-windstar38 — Ford Windstar 3.8 Essex V6

- **Engine:** 3.8L 6-cyl
- **Family applications:** Ford Windstar 1995-2003
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5343 (135A) Windstar 3.8 1999-2003 — one published unit, unqualified (the 1995 3.8 rows split by build date; 96-98 Windstars are 3.0-only).
  - Group 1: Ford Windstar 1999-2003
- **starter:** no verified group — Likely tier only. Note: every published starter row splits by switch-terminal style — match the terminal on your old unit

### gm-14t — GM 1.4 Turbo I4 (LUJ/LUV)

- **Engine:** 1.4L 4-cyl
- **Family applications:** Chevrolet Cruze 2011-2015, Chevrolet Cruze Limited 2016-2016, Chevrolet Sonic 2012-2018, Buick Encore 2013-2021, Chevrolet Trax 2013-2021
- **alternator — verified evidence:** Rareelectrical FG12S031/Lester 11399 listing (GM 13577154/13597226, retrieved 2026-10-22): Cruze 1.4T 2011 ONLY, Encore 2013-2021, Trax 2015-2021. Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6019 (130A) Cruze 1.4 2012-2013 unqualified.
  - Group 1: Chevrolet Cruze 2011-2011; Buick Encore 2013-2021; Chevrolet Trax 2015-2021
  - Group 2: Chevrolet Cruze 2012-2013
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4209 Cruze 1.4 2011-2014 — one published unit, unqualified.
  - Group 1: Chevrolet Cruze 2011-2014

### gm-3800 — GM 3800 Series II/III V6

- **Engine:** 3.8L 6-cyl
- **Family applications:** Buick Lesabre 1996-2005, Pontiac Grand Prix 1997-2008, Pontiac Bonneville 1996-2005, Chevrolet Impala 2000-2005, Chevrolet Monte Carlo 1998-2005, Buick Regal 1997-2004, Buick Park Avenue 1997-2005, Buick Lucerne 2006-2008, Buick Lacrosse 2005-2009, Chevrolet Camaro 1995-2002, Pontiac Firebird 1995-2002
- **alternator — verified evidence:** Lester 8245 listing (OCPTY/amazon.com, GM 10464439/10480411, retrieved 2026-10-22): LeSabre 3.8 2000-2004, Bonneville 3.8 2000-2004. W-body 3800s (Grand Prix/Impala/Monte Carlo/Regal) use different mounting-era units — left at likely. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5118 (105A, engine code K) Camaro 3.8 1995-1999 and Firebird 3.8 1995-1999, both unqualified.
  - Group 1: Buick Lesabre 2000-2004; Pontiac Bonneville 2000-2004
  - Group 2: Chevrolet Camaro 1995-1999; Pontiac Firebird 1995-1999
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5100 Camaro 3.8 (K) 1995-1997 and Firebird 3.8 1995-1997, unqualified.
  - Group 1: Chevrolet Camaro 1995-1997; Pontiac Firebird 1995-1997

### gm-60deg — GM 60° 2.8/3.1/3.4 V6

- **Engine:** 2.8/3.1/3.4L 6-cyl
- **Family applications:** Chevrolet Camaro 1987-1995, Pontiac Firebird 1987-1995, Chevrolet Venture 1997-2005, Pontiac Montana 1999-2005, Pontiac Grand Am 1999-2005, Oldsmobile Alero 1999-2004, Chevrolet Impala 2000-2005, Chevrolet Monte Carlo 2000-2005, Chevrolet Malibu 1997-2005, Buick Century 1997-2005, Pontiac Aztek 2001-2005, Buick Rendezvous 2002-2007, Chevrolet Equinox 2005-2009, Pontiac Torrent 2006-2009
- **alternator — verified evidence:** Lester 13993 (GM 10317647/10440635, Valeo SG10S029) application list (dbelectrical.com 400-40079, retrieved 2026-10-22): Venture 3.4 2002-2005, Montana 3.4 2002-2005, Silhouette 3.4 2002-2004. Grand Am/Alero/Impala/Malibu 3.4 use CS130D-era Delco units with multiple amp options — left at likely. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5132 (100A) Camaro and Firebird 2.8 1987-1989 and 3.1 1990-1992, one unit across both displacements; 210-5126 (105A) Camaro and Firebird 3.4 1993-1995.
  - Group 1: Chevrolet Venture 2002-2005; Pontiac Montana 2002-2005
  - Group 2: Chevrolet Camaro 1987-1992; Pontiac Firebird 1987-1992
  - Group 3: Chevrolet Camaro 1993-1995; Pontiac Firebird 1993-1995
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### gm-atlas-i45 — GM Atlas I4/I5 2.8/2.9/3.5/3.7 (Colorado/Canyon)

- **Engine:** 2.8/2.9/3.5/3.7L 5-cyl
- **Family applications:** Chevrolet Colorado 2004-2008, GMC Canyon 2004-2008, Chevrolet Colorado 2009-2012, GMC Canyon 2009-2012, Hummer H3* 2006-2010
- **alternator:** no verified group — Likely tier only. Note: 04-06 2.8/3.5 share one published unit; 07-09 2.9/3.7 share another — both across Colorado and Canyon
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5394 Colorado 2.9 and 3.7 2008-2012; Canyon 3.7 2008-2012 and 2.9 2009-2012 (the Canyon span starts at 2009 because the 2008 2.9 row is not published).
  - Group 1: Chevrolet Colorado 2008-2012; GMC Canyon 2009-2012

### gm-atlas42 — GM Atlas 4.2 I6 (LL8)

- **Engine:** 4.2L 6-cyl
- **Family applications:** Chevrolet Trailblazer 2002-2009, GMC Envoy 2002-2009, Oldsmobile Bravada 2002-2004, Buick Rainier 2004-2007, Saab 9-7x 2005-2009, Isuzu Ascender 2003-2008, Chevrolet Trailblazer Ext 2002-2006, GMC Envoy Xl 2002-2006
- **alternator — verified evidence:** TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-08290 (GM 19151920) Trailblazer/Envoy 4.2 L6 2002-2006.
  - Group 1: Chevrolet Trailblazer 2002-2006; GMC Envoy 2002-2006
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### gm-aveo — Chevrolet Aveo 1.6 I4

- **Engine:** 1.6L 4-cyl
- **Family applications:** Chevrolet Aveo 2004-2011, Chevrolet Aveo5 2006-2011
- **alternator:** no verified group — Likely tier only. Note: no unqualified alternator rows in this catalog edition — pairs stay Likely
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5397 Aveo 1.6 2004-2008 and Aveo5 2007-2008; 280-5377 Aveo and Aveo5 1.6 2010-2011 (2009 rows absent from this edition).
  - Group 1: Chevrolet Aveo 2004-2008; Chevrolet Aveo5 2007-2008
  - Group 2: Chevrolet Aveo 2010-2011; Chevrolet Aveo5 2010-2011

### gm-corvette-c6 — GM Gen IV LS V8 (Corvette C6/Camaro SS)

- **Engine:** 6.0/6.2/7.0L 8-cyl
- **Family applications:** Chevrolet Corvette 2005-2013, Chevrolet Camaro 2010-2015
- **alternator — verified evidence:** Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6020 (145A) Corvette 6.0 2005-2007, 7.0 2006-2012 and 6.2 2008-2012 — one published unit across the LS2/LS3/LS7; the supercharged ZR1 (211-6028) is its own unit, so the verified span stops at 2008 before the ZR1 enters the fleet. Denso reman 210-0325 (150A) Camaro 6.2 2012-2013 (the 2014 row is stamp-qualified and excluded).
  - Group 1: Chevrolet Corvette 2005-2008
  - Group 2: Chevrolet Camaro 2012-2013
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5391 Corvette 6.0 2006-2007, 6.2 2008-2013 and 7.0 2006-2013, unqualified — one published starter for the whole C6 including the ZR1; 280-4331 Camaro 6.2 2012 and 2015 (the 10-11 rows are vendor-qualified and excluded).
  - Group 1: Chevrolet Corvette 2006-2013
  - Group 2: Chevrolet Camaro 2012-2012; Chevrolet Camaro 2015-2015

### gm-ecotec-lcv — GM Ecotec Gen3 2.0T/2.4/2.5 I4 (Malibu 8th gen)

- **Engine:** 2.0/2.4/2.5L 4-cyl
- **Family applications:** Chevrolet Malibu 2013-2015, Chevrolet Malibu Limited 2016-2016, Chevrolet Impala 2014-2015
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0255 (110A) Malibu 2013 — one published unit across the 2.0 turbo, 2.4 and 2.5. 2014-15 alternator rows are beyond this catalog edition.
  - Group 1: Chevrolet Malibu 2013-2013
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0434 Malibu 2013 2.0 turbo and 2.5, one published unit, unqualified.
  - Group 1: Chevrolet Malibu 2013-2013

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
- **Family applications:** Chevrolet Cobalt 2006-2010, Chevrolet Malibu 2008-2012, Chevrolet Equinox 2010-2017, Chevrolet HHR 2008-2011, GMC Terrain 2010-2017, Pontiac G6 2006-2009, Chevrolet Captiva Sport 2012-2015, Saturn VUE 2008-2010, Buick Verano 2012-2017, Saturn Aura 2007-2009, Buick Regal 2011-2013
- **alternator — verified evidence:** TYC 2-11459 application table (tycamericas.com, retrieved 2026-10-22; Lester 11459, GM 13512759): Equinox 2.4 2010-2017, Terrain 2.4 2010-2017. Lester 11265 (Valeo, GM 15828450/22762984) application list (am-autoparts.com, retrieved 2026-10-22) includes Saturn Vue 2.4 2008-2010. Cobalt/Malibu/G6-era LE5 uses a different unit — left at likely.
  - Group 1: Chevrolet Equinox 2010-2017; GMC Terrain 2010-2017
  - Group 2: Saturn VUE 2008-2010
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5396 Malibu 2.4 2008-2012, Verano 2.4 2012-2015 and Aura 2.4 2007-2009 — one published unit, unqualified.
  - Group 1: Chevrolet Malibu 2008-2012; Buick Verano 2012-2015; Saturn Aura 2007-2009

### gm-fbody-lt1 — GM LT1 5.7 V8 (F-body/C4 Corvette)

- **Engine:** 5.7L 8-cyl
- **Family applications:** Chevrolet Camaro 1993-1997, Pontiac Firebird 1993-1997, Chevrolet Corvette 1992-1996
- **alternator:** no verified group — Likely tier only. Note: LT1 alternator rows aren't published in this catalog (Delco CS-series cars) — all pairs stay Likely; match the CS130/CS144 number on your unit
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5109 Camaro 5.7 (P) 1995-1997 and Firebird 5.7 1995-1997, unqualified; 280-5160 Camaro and Firebird 5.7 1987-1994 (the LT1 years 93-94 of that span sit in this family); 280-0299 Corvette 5.7 1996 (the 90-95 rows are 'Exc. ZR1' and excluded).
  - Group 1: Chevrolet Camaro 1995-1997; Pontiac Firebird 1995-1997
  - Group 2: Chevrolet Camaro 1987-1994; Pontiac Firebird 1987-1994
  - Group 3: Chevrolet Corvette 1996-1996

### gm-fbody-tpi — GM 5.0/5.7 TBI/TPI V8 (F-body/C4 Corvette)

- **Engine:** 5.0/5.7L 8-cyl
- **Family applications:** Chevrolet Camaro 1982-1992, Pontiac Firebird 1982-1992, Chevrolet Corvette 1985-1991
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5144 (100A) Camaro and Firebird 5.0 (E/F) and 5.7 (8) 1988-1989 — one unqualified unit across both displacements and models; 210-5102 (100A) the same four applications 1990-1992. Pre-88 rows and C4 Corvette alternator rows aren't published — left at likely.
  - Group 1: Chevrolet Camaro 1988-1989; Pontiac Firebird 1988-1989
  - Group 2: Chevrolet Camaro 1990-1992; Pontiac Firebird 1990-1992
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0299 Corvette 5.7 1988-1989 unqualified (the 90-95 rows exclude the ZR1 and the 96 row anchors the LT1 family). F-body starter rows split 5.0 vs 5.7 within the same years — excluded to avoid cross-displacement claims.
  - Group 1: Chevrolet Corvette 1988-1989

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
- **Family applications:** Chevrolet Impala 2006-2011, Chevrolet Monte Carlo 2006-2007, Chevrolet Malibu 2004-2010, Pontiac G6 2005-2009, Chevrolet Uplander 2005-2009, Buick Terraza 2005-2007, Saturn Aura 2007-2008, Buick Lucerne 2009-2011
- **alternator — verified evidence:** Lester 11185 (Bosch 0-124-425-032, GM 20911162) application list (TYC 2-11185 via finditparts.com + maniacelectricmotors.com, retrieved 2026-10-22): Impala 3.5/3.9 2006-2011, Monte Carlo 3.5/3.9 2006-2007. Malibu/G6/Uplander use different units — left at likely.
  - Group 1: Chevrolet Impala 2006-2011; Chevrolet Monte Carlo 2006-2007
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5390 Impala 3.5/3.9 2006-2011; 280-5386 Malibu 3.5/3.9 2007-2010 and Aura 3.5 2007-2008 — each one published unit, unqualified (the 2006 Malibu 3.5 row is absent, so it stays outside the span).
  - Group 1: Chevrolet Impala 2006-2011
  - Group 2: Chevrolet Malibu 2007-2010; Saturn Aura 2007-2008

### gm-jbody22 — GM J-body 2.2 I4 (Cavalier/Sunfire)

- **Engine:** 2.2L 4-cyl
- **Family applications:** Chevrolet Cavalier 1995-2005, Pontiac Sunfire 1995-2005
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5117 (105A) Cavalier 2.2 1996-2002 and Sunfire 2.2 1996-2002 — one published unit, unqualified; 210-5157 (105A) both cars 1995.
  - Group 1: Chevrolet Cavalier 1996-2002; Pontiac Sunfire 1996-2002
  - Group 2: Chevrolet Cavalier 1995-1995; Pontiac Sunfire 1995-1995
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5378 Cavalier 2.2 2003-2005 and Sunfire 2.2 2003-2005 (the 2002 rows carry a DOHC/Ecotec qualifier — excluded); 280-5167 Cavalier 2.2 1996-1997 and Sunfire 2.2 1996-1997 (the 1998 rows carry a thru-bolt qualifier — excluded).
  - Group 1: Chevrolet Cavalier 2003-2005; Pontiac Sunfire 2003-2005
  - Group 2: Chevrolet Cavalier 1996-1997; Pontiac Sunfire 1996-1997

### gm-llt36 — GM 3.6 V6 (LY7/LLT/LFX high-feature)

- **Engine:** 3.6L 6-cyl
- **Family applications:** Chevrolet Traverse 2009-2017, GMC Acadia 2007-2016, Buick Enclave 2008-2017, Saturn Outlook 2007-2010, Chevrolet Impala 2012-2019, Chevrolet Impala Limited 2014-2016, Chevrolet Camaro 2010-2015, Chevrolet Equinox 2013-2017, GMC Terrain 2013-2017, Buick Lacrosse 2010-2016, Cadillac CTS 2004-2014, Cadillac SRX 2004-2016, Cadillac STS 2005-2011
- **alternator — verified evidence:** BBB Industries 11252 fitment table (partcatalog.com) + Brillman Denso 170A listing (GM 25815839/23105717, retrieved 2026-10-22): Traverse 2009-2017, Acadia 2007-2016, Enclave 2008-2017, Outlook 2007-2010. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0531 (130A) CTS 3.6 2004-2005 (also the 2.8); 210-0641 (145A) CTS 3.6 2008-2009; 210-0765 (150A) CTS 3.0/3.6 2010-2013; 210-0576 (150A) SRX 3.6 2004-2009 and STS 3.6 2005-2011. SRX 2010+ rows carry pulley qualifiers — left at likely.
  - Group 1: Chevrolet Traverse 2009-2017; GMC Acadia 2007-2016; Buick Enclave 2008-2017; Saturn Outlook 2007-2010
  - Group 2: Cadillac CTS 2004-2005
  - Group 3: Cadillac CTS 2008-2009
  - Group 4: Cadillac CTS 2010-2013
  - Group 5: Cadillac SRX 2004-2009; Cadillac STS 2005-2011
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### gm-ls1-car — GM LS1/LS6 5.7 V8 (F-body/C5 Corvette)

- **Engine:** 5.7L 8-cyl
- **Family applications:** Chevrolet Camaro 1998-2002, Pontiac Firebird 1998-2002, Chevrolet Corvette 1997-2004
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5164 (102A, engine code G) Camaro 5.7 1998-2002 and Firebird 5.7 1998-2002, one published unit, unqualified. Denso First Time Fit 211-6025 (145A) Corvette 5.7 2004 (the 2003 row is transmission/design-qualified and excluded; 97-02 C5 alternator rows aren't published).
  - Group 1: Chevrolet Camaro 1998-2002; Pontiac Firebird 1998-2002
  - Group 2: Chevrolet Corvette 2004-2004
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5112 in one published set — Camaro 5.7 1998-2001, Firebird 5.7 1998-2001 and Corvette 5.7 1997-2001, unqualified.
  - Group 1: Chevrolet Camaro 1998-2001; Pontiac Firebird 1998-2001; Chevrolet Corvette 1997-2001

### gm-lumina31 — Chevrolet Lumina 3.1 V6

- **Engine:** 3.1L 6-cyl
- **Family applications:** Chevrolet Lumina 1990-2001, Chevrolet Monte Carlo 1995-1999
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), Lumina 3.1 rows all unqualified: 210-5106 (100A) 1990-1994; 210-5109 (105A) 1995-1997; 210-5114 (105A) 1998-1999; 210-5160 (102A) 2000; 210-5161 (102A) 2001. Monte Carlo spans not separately verified — left at likely.
  - Group 1: Chevrolet Lumina 1990-1994
  - Group 2: Chevrolet Lumina 1995-1997
  - Group 3: Chevrolet Lumina 1998-1999
  - Group 4: Chevrolet Lumina 2000-2000
  - Group 5: Chevrolet Lumina 2001-2001
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### gm-vortec-gen3 — GM Gen-III/IV 4.8/5.3 V8 (full-size SUVs)

- **Engine:** 4.8/5.3L 8-cyl
- **Family applications:** Chevrolet Tahoe 2000-2014, Chevrolet Suburban 2000-2014, GMC Yukon 2000-2014, Chevrolet Avalanche 2002-2013, Chevrolet Avalanche 1500 2002-2006
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5381 (160A) Tahoe 5.3 2011-2012 — the one unqualified row; every other year splits by case diameter (145 vs 156mm) and is excluded.
  - Group 1: Chevrolet Tahoe 2011-2012
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5383 Tahoe 4.8/5.3 2003-2008 and Suburban 4.8/5.3 2003-2008 — one published unit for both engines, unqualified; 280-5398 Tahoe 5.3 2009-2014 (and the lone 2009 4.8) — unqualified.
  - Group 1: Chevrolet Tahoe 2003-2008; Chevrolet Suburban 2003-2008
  - Group 2: Chevrolet Tahoe 2009-2014

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

### gm-vortec57 — GM 5.7 Vortec/TBI V8 (GMT400 trucks)

- **Engine:** 5.7L 8-cyl
- **Family applications:** Chevrolet Tahoe 1995-2000, Chevrolet Suburban 1992-1999, GMC Yukon 1995-1999, Chevrolet C/K 1500 1988-1999, Chevrolet C/K 1500 Series 1988-1999, Chevrolet K1500 1988-1999, Chevrolet C1500 1988-1999, Chevrolet Gmt-400 1988-2000, Chevrolet C/K 2500 1988-2000, GMC Sierra 1989-1998, GMC Suburban 1993-1999
- **alternator:** no verified group — Likely tier only. Note: every published alternator row splits by case diameter or rear-cover style — match the case on your old unit
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5101 Tahoe 5.7 1995-1996 and 1999-2000, Suburban (C/K 1500-2500) 5.7 1995-1996 and 1999-2000 — one published unit across both spans, unqualified; 280-5164 both models 1997 (the 1998 rows carry a thru-bolt qualifier — excluded).
  - Group 1: Chevrolet Tahoe 1995-1996; Chevrolet Suburban 1995-1996; Chevrolet Tahoe 1999-2000; Chevrolet Suburban 1999-1999
  - Group 2: Chevrolet Tahoe 1997-1997; Chevrolet Suburban 1997-1997

### hk-alpha — Hyundai/Kia Alpha 1.5/1.6 I4

- **Engine:** 1.5/1.6L 4-cyl
- **Family applications:** Hyundai Accent 1995-2011, Kia Rio 2001-2011, Kia Rio5 2006-2011
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 211-6012 (90A) Accent 1.5 1995-1999; 211-6005 (90A) Accent 1.5 2000-2003 and 1.6 2001-2002 (the 2003-2005 1.6 rows carry a Mando-unit qualifier — excluded); 211-6016 (90A) Accent 1.6 2010-2011 plus Rio and Rio5 1.6 2010-2011 in the same published set; 211-6006 (80A) Rio 1.5 2001-2002 and 1.6 2003-2005; 211-6002 (90A) Rio 1.6 2006-2009 and Rio5 2006-2007 (the Rio5 08-09 rows are Valeo-qualified). The Accent 2006-2009 rows are Mando-qualified — left at likely.
  - Group 1: Hyundai Accent 1995-1999
  - Group 2: Hyundai Accent 2000-2002
  - Group 3: Hyundai Accent 2010-2011; Kia Rio 2010-2011; Kia Rio5 2010-2011
  - Group 4: Kia Rio 2001-2005
  - Group 5: Kia Rio 2006-2009; Kia Rio5 2006-2007
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### hk-beta20 — Hyundai/Kia Beta 1.8/2.0 I4

- **Engine:** 1.8/2.0L 4-cyl
- **Family applications:** Hyundai Elantra 1996-2012, Hyundai Tiburon 1997-2008, Hyundai Tucson 2005-2009, Kia Sportage 2005-2010, Kia Soul 2010-2011
- **alternator — verified evidence:** Lester 13973 (Hyundai/Kia 37300-23600, Mando AB190147) application lists (qpselectric.com + partshawk.com, retrieved 2026-10-22): Elantra 2.0 2001-2006, Tiburon 2.0 2003-2004 and 2007-2008 (w/ Mando unit), Tucson 2.0 2005, Sportage 2.0 2005-2006. Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6008 (90A) Elantra 2.0 2007-2012 and Soul 2.0 2010-2011 unqualified (the same published unit); 211-6012 (90A) Elantra 1.8/2.0 1996-2000 and Tiburon 1.8/2.0 1997-2001 unqualified.
  - Group 1: Hyundai Elantra 2001-2006; Hyundai Tiburon 2003-2004; Hyundai Tiburon 2007-2008; Hyundai Tucson 2005-2005; Kia Sportage 2005-2006
  - Group 2: Hyundai Elantra 2007-2012; Kia Soul 2010-2011
  - Group 3: Hyundai Elantra 1996-2000; Hyundai Tiburon 1997-2001
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### hk-delta27 — Hyundai/Kia Delta 2.7 V6

- **Engine:** 2.7L 6-cyl
- **Family applications:** Hyundai Tucson 2005-2009, Hyundai Tiburon 2003-2008, Kia Sportage 2005-2010, Hyundai Sonata 1999-2005, Kia Optima 2001-2006, Hyundai Santa Fe 2001-2006
- **alternator — verified evidence:** Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6010 (120A) in one published set — Tucson 2.7 2005-2009, Tiburon 2.7 2005-2008, Sportage 2.7 2005-2010, Sonata 2.7 2005 and Santa Fe 2.7 2005-2006, all unqualified (Sonata/Tiburon 03-04 rows carry pulley/build-date qualifiers).
  - Group 1: Hyundai Tucson 2005-2009; Hyundai Tiburon 2005-2008; Kia Sportage 2005-2010; Hyundai Sonata 2005-2005; Hyundai Santa Fe 2005-2006
- **starter — verified evidence:** Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 281-6004 in one published set — Tucson 2.7 2005-2009, Tiburon 2.7 2003-2008, Sportage 2.7 2005-2009, Sonata 2.7 2002-2005, Optima 2.7 2002-2006, Santa Fe 2.7 2001-2006, all unqualified.
  - Group 1: Hyundai Tucson 2005-2009; Hyundai Tiburon 2003-2008; Kia Sportage 2005-2009; Hyundai Sonata 2002-2005; Kia Optima 2002-2006; Hyundai Santa Fe 2001-2006

### hk-gamma16 — Hyundai/Kia Gamma 1.6 I4

- **Engine:** 1.6L 4-cyl
- **Family applications:** Hyundai Accent 2012-2017, Kia Rio 2012-2017, Kia Soul 2012-2019, Hyundai Veloster 2012-2017
- **alternator — verified evidence:** Lester 13209 (Hyundai/Kia 37300-2B300/2B500/2B510, Valeo) application lists (dbelectrical.com 400-40153 + mymromarts.com, retrieved 2026-10-22): Accent 1.6 2012-2017, Veloster 1.6 2012-2017, Rio 1.6 2012-2013. Soul 1.6 uses 37300-2B760 (Lester 11609) — left at likely.
  - Group 1: Hyundai Accent 2012-2017; Hyundai Veloster 2012-2017; Kia Rio 2012-2013
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### hk-mu-lambda — Hyundai 2.7/3.3/3.8 V6 (Mu/Lambda)

- **Engine:** 2.7/3.3/3.8L 6-cyl
- **Family applications:** Hyundai Santa Fe 2007-2009, Hyundai Azera 2006-2011, Hyundai Veracruz 2007-2012, Hyundai Entourage 2007-2008, Kia Sorento 2007-2009
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0712 (130A) Santa Fe 2.7 2007-2009 and 3.3 2007-2008, Azera 3.3 2007-2009 and 3.8 2007-2008 (the 2009+ rows carry Denso-unit vendor qualifiers — group capped at 2008), plus Sorento 3.8 2007-2009 and 3.3 2008-2009 in the same published set (2007 Sorentos are all 3.8, so the span is clean).
  - Group 1: Hyundai Santa Fe 2007-2008; Hyundai Azera 2007-2008; Kia Sorento 2007-2009
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5001 Sorento 3.8 2007-2009 and 3.3 2008-2009, unqualified (280-5376 was dual-sourced on 08-09 — match yours).
  - Group 1: Kia Sorento 2007-2009

### hk-nu — Hyundai/Kia Nu 1.8/2.0 I4

- **Engine:** 1.8/2.0L 4-cyl
- **Family applications:** Hyundai Elantra 2011-2020, Hyundai Elantra GT 2013-2017, Kia Soul 2012-2019, Kia Forte 2014-2018, Hyundai Tucson 2016-2021
- **alternator — verified evidence:** Lester 11610 (Hyundai 37300-2E200, Valeo FG10T011) fitment (TYC 2-11610 finditparts.com + dahkee.com + thenthgear.com, retrieved 2026-10-22): Elantra 1.8/2.0 2011-2016, Forte 2014-2016, Soul 2.0 2012-2013.
  - Group 1: Hyundai Elantra 2011-2016; Kia Forte 2014-2016; Kia Soul 2012-2013
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### hk-sirius24 — Hyundai/Kia Sirius 2.4 I4 (Sonata/Optima)

- **Engine:** 2.4L 4-cyl
- **Family applications:** Hyundai Sonata 1999-2005, Kia Optima 2001-2006
- **alternator — verified evidence:** Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6007 (110A) — one published unit for Sonata 2.4 1999-2005 and Optima 2.4 2001-2006, unqualified.
  - Group 1: Hyundai Sonata 1999-2005; Kia Optima 2001-2006
- **starter:** no verified group — Likely tier only. Note: every published row splits M/T vs A/T — pairs stay Likely

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

### hk-theta24 — Hyundai/Kia Theta 2.4 I4 (Sonata/Optima NF)

- **Engine:** 2.4L 4-cyl
- **Family applications:** Hyundai Sonata 2006-2010, Kia Optima 2006-2010
- **alternator — verified evidence:** Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6014 (110A) Sonata 2.4 2006-2008 and Optima 2.4 2006-2010 — one published unit, unqualified (Sonata 09-10 rows are option-qualified — excluded).
  - Group 1: Hyundai Sonata 2006-2008; Kia Optima 2006-2010
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5372 Sonata 2.4 2006-2008 — one published unit, unqualified (Optima rows carry trans qualifiers — excluded).
  - Group 1: Hyundai Sonata 2006-2008

### hk-theta2gdi — Hyundai/Kia Theta-II 2.0T/2.4 GDI (Sonata/Optima)

- **Engine:** 2.0/2.4L 4-cyl
- **Family applications:** Hyundai Sonata 2011-2014, Kia Optima 2011-2015
- **alternator — verified evidence:** Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6030 (110A) Sonata 2.4 2014 and 2.0T 2011-2013 (SE and Limited rows cover the turbo lineup) and Optima 2.4 2012-2013 and 2.0T 2011-2013 — spans capped to the years where BOTH engines publish the one number (Sonata 2.4 11-13 rows are absent from this catalog edition).
  - Group 1: Hyundai Sonata 2014-2014; Kia Optima 2012-2013
- **starter:** no verified group — Likely tier only. Note: starters were dual-sourced (Denso/Delco) across these years — pairs stay Likely, match your part number

### honda-a20 — Honda A20 2.0 I4

- **Engine:** 2.0L 4-cyl
- **Family applications:** Honda Accord 1986-1989
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0233 (65A) Accord 2.0 A20A3 w/ fuel injection 1986-1989 and 210-0389 (65A) Accord 2.0 A20A1 carbureted 1986-1989 — both published lists span the same four years; match FI vs carb when pulling.
  - Group 1: Honda Accord 1986-1989
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### honda-b18 — Honda/Acura B17/B18 1.7/1.8 I4 (Integra)

- **Engine:** 1.7/1.8L 4-cyl
- **Family applications:** Acura Integra 1990-2001
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows unqualified: 210-0223 (65A) Integra B18A1 1990-1991; 210-0214 (80A) Integra B18A1 1992-1993 and B17A1 1993; 210-0211 (90A) Integra B18B1 and B18C1 1994-1995, one unit for both. The 96-01 span splits by trim (Type R B18C5 210-4190 vs all others 210-0199) — excluded from verified; match part number there.
  - Group 1: Acura Integra 1990-1991
  - Group 2: Acura Integra 1992-1993
  - Group 3: Acura Integra 1994-1995
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0194 Integra 1.8 1990-1993 and 1.7 1993, unqualified. 94-01 rows split by transmission and are excluded.
  - Group 1: Acura Integra 1990-1993

### honda-b20 — Honda B20 2.0 I4 (CR-V)

- **Engine:** 2.0L 4-cyl
- **Family applications:** Honda CR-V 1997-2001
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0196 (95A) CR-V 2.0 B20B4 1997-1998 unqualified. The 99-01 B20Z2 rows split M/T vs A/T and stay Likely.
  - Group 1: Honda CR-V 1997-1998
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0185 CR-V 2.0 1997 unqualified (98-01 rows split M/T vs A/T).
  - Group 1: Honda CR-V 1997-1997

### honda-d-ef — Honda D15/D16 1.5/1.6 I4 (EF Civic/CRX)

- **Engine:** 1.5/1.6L 4-cyl
- **Family applications:** Honda Civic 1988-1991, Honda CRX 1988-1991
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0227 (60A) Civic D15B2 1990-1991, Civic D16A6 1990-1991, CRX D15B2/D15B6 1990-1991 and CRX D16A6 1990-1991 — one unqualified unit across both engines and models. The 1988-89 rows are vendor-split (DENSO Unit) and excluded.
  - Group 1: Honda Civic 1990-1991; Honda CRX 1990-1991
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### honda-d-eg — Honda D15/D16 1.5/1.6 I4 (EG Civic/Del Sol)

- **Engine:** 1.5/1.6L 4-cyl
- **Family applications:** Honda Civic 1992-1995, Honda Civic Del Sol 1993-1995, Honda Del Sol 1993-1995
- **Ambiguity cap:** Honda Civic Del Sol — VTEC (B16A3 1.6 DOHC) Del Sols use a different unit — this family covers the D-series singles-cam cars; confirm the engine code
- **Ambiguity cap:** Honda Del Sol — VTEC (B16A3 1.6 DOHC) Del Sols use a different unit — this family covers the D-series single-cam cars; confirm the engine code
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4133 lists Civic D15B7/B8/Z1 1994-1995 and Del Sol D15B7 1993-1995 unqualified; for the 1.6 D16Z6 (Civic 92-95, Del Sol 93-95) the catalog publishes two interchange-equivalent sourcings with identical spans — Denso-built 210-0213 and Mitsubishi-built 210-4133 — so every 92-95 D-series car is covered by a published list; match the vendor tag on a 1.6 (3MZ-precedent dual-list note). VTEC (B16A3) Del Sols are a different engine and capped by the app-level ambiguity flag.
  - Group 1: Honda Civic 1992-1995; Honda Civic Del Sol 1993-1995; Honda Del Sol 1993-1995
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

### honda-f20c — Honda F20C/F22C 2.0/2.2 I4 (S2000)

- **Engine:** 2.0/2.2L 4-cyl
- **Family applications:** Honda S2000 2000-2009
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0458 (105A) S2000 F20C1 2000-2003; 210-0597 (105A) S2000 F22C1 2004-2005, both unqualified. 2006-09 (same F22C1) is past this catalog edition — left at likely.
  - Group 1: Honda S2000 2000-2003
  - Group 2: Honda S2000 2004-2005
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

### honda-h22 — Honda H22/H23/F22 2.2/2.3 I4 (Prelude)

- **Engine:** 2.2/2.3L 4-cyl
- **Family applications:** Honda Prelude 1992-2001
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0197 (90A) Prelude H22A4 1997-1998; 210-0456 (90A) Prelude H22A4 1999-2001, both unqualified. The 92-96 span splits three ways (F22A1 non-VTEC 210-0216 / H22A1 VTEC 210-0217 / H23A1 2.3 210-0215) — year spans can't separate the trims, so 92-96 stays at likely.
  - Group 1: Honda Prelude 1997-1998
  - Group 2: Honda Prelude 1999-2001
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### honda-j30 — Honda/Acura J30 3.0 V6 (Accord)

- **Engine:** 3.0L 6-cyl
- **Family applications:** Honda Accord 1998-2002, Honda Accord 2003-2007, Acura CL 1997-1999
- **alternator — verified evidence:** Lester 8220 (Delco CS130D, Honda 31100-P8A-A01/P8C-A02) application lists (alternatorparts.com + thewrenchmonkey.ca, retrieved 2026-10-22): Accord 3.0 1998-2002, Acura CL 3.0 1997-1999. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0606 (110A) Accord 3.0 J30A4/J30A5 2004-2007 unqualified (2003 shipped 210-0511 shared with the 2.4).
  - Group 1: Honda Accord 1998-2002; Acura CL 1997-1999
  - Group 2: Honda Accord 2004-2007
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-6000 Accord 3.0 J30A1 1998-2002 unqualified (03-07 rows split by transmission/trim; the hybrid uses 280-4333).
  - Group 1: Honda Accord 1998-2002

### honda-j35-early — Honda J35 3.5 V6 (99–04 era)

- **Engine:** 3.5L 6-cyl
- **Family applications:** Honda Odyssey 1999-2004, Honda Pilot 2003-2005, Acura MDX 2001-2006
- **alternator — verified evidence:** TYC 2-13918 fitment (partshawk.com + a-premium.com; Honda 31100-PGK-A01/A03, Denso 104210-3090, retrieved 2026-10-22): MDX 2001-2002, Odyssey 3.5 2002-2004, Pilot 2003-2004. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0580 (130A) MDX 3.5 J35A5 2003-2006 (the same published unit continues on the 3.7 MDX through 2009). The 99-01 Odyssey unit differs — left at likely.
  - Group 1: Acura MDX 2001-2002; Honda Odyssey 2002-2004; Honda Pilot 2003-2004
  - Group 2: Acura MDX 2003-2006
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-6000 MDX 3.5 2001-2002; 280-4207 MDX 3.5 2003-2006 — each one published unit, unqualified.
  - Group 1: Acura MDX 2001-2002
  - Group 2: Acura MDX 2003-2006

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

### honda-j37 — Acura J37 3.7 V6 (MDX 2nd gen)

- **Engine:** 3.7L 6-cyl
- **Family applications:** Acura MDX 2007-2013
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0580 (130A) MDX 3.7 J37A1 2007-2009 (continues from the 03-06 3.5); 210-0750 (130A) MDX 3.7 2010-2013, both unqualified.
  - Group 1: Acura MDX 2007-2009
  - Group 2: Acura MDX 2010-2013
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0404 MDX 3.7 2007-2009; 280-0405 MDX 3.7 2010-2013 — each one published unit, unqualified.
  - Group 1: Acura MDX 2007-2009
  - Group 2: Acura MDX 2010-2013

### honda-k20 — Honda/Acura K20 2.0 I4 (Civic Si/RSX)

- **Engine:** 2.0L 4-cyl
- **Family applications:** Honda Civic 2002-2011, Acura RSX 2002-2006
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0525 (80A) Civic 2.0 (K20A3, EP3 Si) 2002-2005 unqualified; 210-0609 (105A) Civic 2.0 K20Z3 (FG/FA Si) 2006-2011 unqualified. RSX rows split by trim (Type S 210-0507 vs base 210-4168) and are excluded.
  - Group 1: Honda Civic 2002-2005
  - Group 2: Honda Civic 2006-2011
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### honda-k24a — Honda/Acura K24 2.4 I4 (02–09 era)

- **Engine:** 2.4L 4-cyl
- **Family applications:** Honda Accord 2003-2007, Honda CR-V 2002-2009, Honda Element 2003-2011, Acura TSX 2004-2008
- **alternator — verified evidence:** TYC 2-13980 application table (tycamericas.com, retrieved 2026-10-22; Honda 31100-RAA-A05, Lester 13980): Accord 2.4 2003-2007, Element 2003-2011, TSX 2004-2008, CR-V 2007-2011. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4168 (90A) CR-V 2.4 K24A1 2002-2006 — its own published unit, unqualified.
  - Group 1: Honda Accord 2003-2007; Honda Element 2003-2011; Acura TSX 2004-2008; Honda CR-V 2007-2011
  - Group 2: Honda CR-V 2002-2006
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-6005 CR-V 2.4 K24A1 2002-2006 unqualified; 280-6007 CR-V 2.4 2007-2009 and Accord 2.4 K24A8 2006-2007, one published set, unqualified.
  - Group 1: Honda CR-V 2002-2006
  - Group 2: Honda CR-V 2007-2009; Honda Accord 2006-2007

### honda-k24z — Honda/Acura K24Z 2.4 I4 (08–15 era)

- **Engine:** 2.4L 4-cyl
- **Family applications:** Honda Accord 2008-2012, Honda CR-V 2010-2014, Honda Civic 2012-2015, Honda Crosstour 2012-2015, Acura TSX 2009-2014
- **alternator — verified evidence:** Lester 11390 (Honda 31100-R40-A01, Denso 104210-5890) application tables (dssautoparts.com + FVP/autofactsdb.com + DB Electrical 400-52394, retrieved 2026-10-22): Accord 2.4 2008-2012, TSX 2.4 2009-2014. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0808 (105A) CR-V 2.4 K24Z7 2012-2014 unqualified.
  - Group 1: Honda Accord 2008-2012; Acura TSX 2009-2014
  - Group 2: Honda CR-V 2012-2014
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-6010 CR-V 2.4 K24Z6 2010-2011 unqualified (Accord 08-12 rows split by region/transmission).
  - Group 1: Honda CR-V 2010-2011

### honda-l15 — Honda L15 1.5 I4 (Fit)

- **Engine:** 1.5L 4-cyl
- **Family applications:** Honda Fit 2007-2014
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4299 (75A) Fit 1.5 L15A1 2007-2008 unqualified (2015 rows split CVT vs M/T).
  - Group 1: Honda Fit 2007-2008
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0412 Fit 1.5 2010-2013 unqualified; 280-0368 Fit 1.5 2007-2008 unqualified. 2009 was dual-sourced between the two — groups capped either side; match your part number in 2009.
  - Group 1: Honda Fit 2010-2013
  - Group 2: Honda Fit 2007-2008

### honda-r18 — Honda R18 1.8 I4

- **Engine:** 1.8L 4-cyl
- **Family applications:** Honda Civic 2006-2011, Honda Civic 2012-2015
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4236 (90A) Civic 1.8 R18A1 2006-2011. Corroborated by TYC 2-11176 / Lester 11176 (Honda 31100-RNA-A01) listings. 2012-2015 R18Z Civic uses a different unit — left at likely.
  - Group 1: Honda Civic 2006-2011
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### hyundai-gencoupe20 — Hyundai Genesis Coupe 2.0T I4

- **Engine:** 2.0L 4-cyl
- **Family applications:** Hyundai Genesis Coupe 2010-2014
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 211-6017 (110A) Genesis Coupe 2.0T 2010-2012; 210-0713 (130A) Genesis Coupe 2.0T 2013-2014 — both unqualified.
  - Group 1: Hyundai Genesis Coupe 2010-2012
  - Group 2: Hyundai Genesis Coupe 2013-2014
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### hyundai-gencoupe38 — Hyundai Genesis Coupe 3.8 V6

- **Engine:** 3.8L 6-cyl
- **Family applications:** Hyundai Genesis Coupe 2010-2015
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0713 (130A) Genesis Coupe 3.8 2010-2015 — one published unit, unqualified (2012 is also dual-listed with 211-6017 — match yours).
  - Group 1: Hyundai Genesis Coupe 2010-2015
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### hyundai-genesis38 — Hyundai Genesis sedan 3.8 V6

- **Engine:** 3.8L 6-cyl
- **Family applications:** Hyundai Genesis 2009-2015
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), Genesis sedan 3.8 rows all unqualified: 210-0715 (150A) 2009-2011 and 2013; 210-0827 (200A) 2012; 210-0717 (180A) 2014-2015 (shared with the V8s).
  - Group 1: Hyundai Genesis 2009-2011
  - Group 2: Hyundai Genesis 2013-2013
  - Group 3: Hyundai Genesis 2012-2012
  - Group 4: Hyundai Genesis 2014-2015
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5380 Genesis sedan 3.8 2009 (the 4.6 carries the same number) — unqualified.
  - Group 1: Hyundai Genesis 2009-2009

### hyundai-santafe1 — Hyundai Santa Fe 2.4/2.7/3.5 (1st gen)

- **Engine:** 2.4/2.7/3.5L 6-cyl
- **Family applications:** Hyundai Santa Fe 2001-2006
- **alternator:** no verified group — Likely tier only. Note: 2.7 02-04 and 2.4 01-04 each have one clean unit, but the mixed-engine years keep cross-engine spans at Likely; 05 rows are dual-sourced
- **starter — verified evidence:** Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 281-6004 Santa Fe — 2.7 2001-2006, 3.5 2003-2006 and 2.4 2005-2006 in one published set. The verified span is capped to 2005-2006, the years where ALL family engines carry this number (2.4 02-04 splits M/T vs A/T).
  - Group 1: Hyundai Santa Fe 2005-2006

### hyundai-santafe2 — Hyundai Santa Fe 2.4 (2nd/3rd gen)

- **Engine:** 2.4L 4-cyl
- **Family applications:** Hyundai Santa Fe 2010-2012, Hyundai Santa Fe Sport 2013-2016
- **alternator — verified evidence:** Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6030 (110A) Santa Fe 2.4 2010-2012 — one published unit (the same number as the Sonata/Optima Theta-II GDI), unqualified.
  - Group 1: Hyundai Santa Fe 2010-2012
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### isuzu-6vd1 — Isuzu 6VD1 3.2 V6 (Rodeo/Passport)

- **Engine:** 3.2L 6-cyl
- **Family applications:** Isuzu Rodeo 1992-2004, Honda Passport 1994-2002, Isuzu Trooper 1992-1997
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3145 (90A) Rodeo 3.2 1999-2001; 210-3140 (60A) Rodeo 3.2 1997 — both unqualified (1996 rows carry a plug-position qualifier). Passport/Trooper spans not separately verified — left at likely.
  - Group 1: Isuzu Rodeo 1999-2001
  - Group 2: Isuzu Rodeo 1997-1997
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### jeep-40 — Jeep 4.0 I6

- **Engine:** 4.0L 6-cyl
- **Family applications:** Jeep Grand Cherokee 1993-2004, Jeep Cherokee 1991-2001, Jeep Wrangler 1991-2006, Jeep Comanche 1991-1992
- **alternator — verified evidence:** TYC 2-13341 fitment (partshawk.com; Chrysler 56005685AB, Denso 121000-3440, retrieved 2026-10-22): Cherokee 1991-1998, Comanche 1991-1992, Wrangler 1991-1998, Grand Cherokee 1993-1998. TYC 2-13876 (Jeep 56041864AB, standardautopart.com): Wrangler 4.0 2001-2006 is its own unit.
  - Group 1: Jeep Cherokee 1991-1998; Jeep Comanche 1991-1992; Jeep Wrangler 1991-1998; Jeep Grand Cherokee 1993-1998
  - Group 2: Jeep Wrangler 2001-2006
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### kia-forte1 — Kia Forte 1.6T/2.0/2.4 I4

- **Engine:** 1.6/2.0/2.4L 4-cyl
- **Family applications:** Kia Forte 2010-2015, Kia Forte Koup 2010-2015, Kia Forte5 2010-2015
- **alternator — verified evidence:** Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6014 (100A) Forte Koup 2.0 and 2.4 2010-2013, one published unit, unqualified (sedan 2.0 splits hydraulic vs electric power steering those years and stays Likely).
  - Group 1: Kia Forte Koup 2010-2013
- **starter — verified evidence:** Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 281-6017 Forte Koup 2.0 2014-2015 and 1.6 2014, one published unit, unqualified (sedan 14-15 rows carry start/stop-feature qualifiers; 10-11 rows split by build date).
  - Group 1: Kia Forte Koup 2014-2015

### kia-sedona1 — Kia Sedona 3.5/3.8 V6

- **Engine:** 3.5/3.8L 6-cyl
- **Family applications:** Kia Sedona 2002-2012, Kia Sedona 2014-2014
- **alternator — verified evidence:** Denso First Time Fit + reman catalog (densoautoparts.com, retrieved 2026-10-22): 211-6013 (120A) Sedona 3.5 2002-2005 unqualified; 210-0711 (130A) Sedona 3.8 2006-2007 unqualified (08-09 split by rear-DVD option); 210-5000 (150A) Sedona 3.5 2011-2012 and 2014 (2015 is AMS-qualified).
  - Group 1: Kia Sedona 2002-2005
  - Group 2: Kia Sedona 2006-2007
  - Group 3: Kia Sedona 2011-2012; Kia Sedona 2014-2014
- **starter — verified evidence:** Denso reman + First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 281-6004 Sedona 3.5 2002-2005 unqualified; 280-5379 Sedona 3.8 2006-2007; 280-5375 Sedona 3.8 2008-2010 and 3.5 2011-2012, one number (a second number, 281-6009, was dual-sourced over 08-12 — match yours).
  - Group 1: Kia Sedona 2002-2005
  - Group 2: Kia Sedona 2006-2007
  - Group 3: Kia Sedona 2008-2012

### kia-sorento1 — Kia Sorento 3.5 V6 (1st gen)

- **Engine:** 3.5L 6-cyl
- **Family applications:** Kia Sorento 2003-2006
- **alternator — verified evidence:** Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6003 (120A) Sorento 3.5 2003-2006 — one published unit, unqualified.
  - Group 1: Kia Sorento 2003-2006
- **starter — verified evidence:** Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 281-6002 Sorento 3.5 2003-2006 — one published unit, unqualified.
  - Group 1: Kia Sorento 2003-2006

### kia-spectra — Kia Spectra 1.8/2.0 I4

- **Engine:** 1.8/2.0L 4-cyl
- **Family applications:** Kia Spectra 2000-2009, Kia Spectra5 2005-2009
- **alternator — verified evidence:** Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6002 (90A) Spectra 2.0 2008-2009 unqualified (05-07 rows split Valeo vs Mando vendor; the 2004 2.0 row is excluded because early-2004 1.8 cars used the vendor-split unit); 211-6011 (90A) Spectra 1.8 2000-2001 unqualified.
  - Group 1: Kia Spectra 2008-2009
  - Group 2: Kia Spectra 2000-2001
- **starter:** no verified group — Likely tier only. Note: every published row splits M/T vs A/T — all pairs stay Likely

### lexus-1uz — Lexus LS 400 1UZ-FE 4.0 V8

- **Engine:** 4.0L 8-cyl
- **Family applications:** Lexus LS 400 1990-2000
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows unqualified: 210-0170 (100A) LS 400 1990-1992; 210-0282 (100A) 1993-1994; 210-0174 (80A) 1995-1997; 210-0176 (100A) 1999-2000 (1998 splits by production date).
  - Group 1: Lexus LS 400 1990-1992
  - Group 2: Lexus LS 400 1993-1994
  - Group 3: Lexus LS 400 1995-1997
  - Group 4: Lexus LS 400 1999-2000
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0164 LS 400 1990-1994; 280-0165 LS 400 1995-2000 — both unqualified.
  - Group 1: Lexus LS 400 1990-1994
  - Group 2: Lexus LS 400 1995-2000

### lexus-3uz — Lexus LS 430 3UZ-FE 4.3 V8

- **Engine:** 4.3L 8-cyl
- **Family applications:** Lexus LS 430 2001-2006
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0508 (130A) LS 430 2001-2004; 210-0570 (130A) LS 430 2005-2006 — both unqualified.
  - Group 1: Lexus LS 430 2001-2004
  - Group 2: Lexus LS 430 2005-2006
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### lexus-is2 — Lexus IS 250/350 (2nd gen)

- **Engine:** 2.5/3.5L 6-cyl
- **Family applications:** Lexus IS 250 2006-2015, Lexus IS 350 2006-2015, Lexus IS 2006-2015
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0657 (150A) IS 250 2006-2009 AND IS 350 2006-2009 — one published unit for both engines, unqualified (the 2010-2013 rows carry a Base-trim qualifier — excluded).
  - Group 1: Lexus IS 250 2006-2009; Lexus IS 350 2006-2009
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0366 IS 250 2.5 2006-2011 — one published unit, unqualified.
  - Group 1: Lexus IS 250 2006-2011

### lincoln-ls39 — Lincoln LS 3.9 V8

- **Engine:** 3.9L 8-cyl
- **Family applications:** Lincoln LS 2000-2006
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0532 (150A) LS 3.9 2003-2006; 210-5344 (110A) LS 3.9 2000-2002 — both unqualified (the V6 3.0's rows split by transmission and sit outside this 3.9 family).
  - Group 1: Lincoln LS 2003-2006
  - Group 2: Lincoln LS 2000-2002
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5317 LS 3.9 2000-2006 — ONE published starter for every 3.9 LS, unqualified.
  - Group 1: Lincoln LS 2000-2006

### mazda-cx7 — Mazda CX-7 2.3T/2.5

- **Engine:** 2.3/2.5L 4-cyl
- **Family applications:** Mazda CX-7 2007-2012, Mazda CX7 2007-2012
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4312 (110A) — one published unit for CX-7 2.3 turbo 2007-2011 and 2.5 2010-2011.
  - Group 1: Mazda CX-7 2007-2011; Mazda CX7 2007-2011
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4230 CX-7 2.3 turbo 2007-2009 unqualified; 280-4323 CX-7 2011 (2.3 and 2.5), unqualified.
  - Group 1: Mazda CX-7 2007-2009; Mazda CX7 2007-2009
  - Group 2: Mazda CX-7 2011-2011; Mazda CX7 2011-2011

### mazda-cx9 — Mazda CX-9 3.5/3.7 V6

- **Engine:** 3.5/3.7L 6-cyl
- **Family applications:** Mazda CX-9 2007-2015, Mazda CX9 2007-2015
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4321 (110A) — one published unit for CX-9 3.5 2007 and 3.7 2008-2011.
  - Group 1: Mazda CX-9 2007-2011; Mazda CX9 2007-2011
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4326 CX-9 3.5 2007 and 3.7 2008-2009; 280-4329 CX-9 3.7 2010-2012, both unqualified.
  - Group 1: Mazda CX-9 2007-2009; Mazda CX9 2007-2009
  - Group 2: Mazda CX-9 2010-2012; Mazda CX9 2010-2012

### mazda-miata-16 — Mazda B6 1.6 I4 (Miata NA)

- **Engine:** 1.6L 4-cyl
- **Family applications:** Mazda Miata 1990-1993, Mazda MX-5* 1990-1993
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4184 (60A) Miata 1.6 1990 unqualified — the 1991-93 rows for the same and sibling units are transmission-qualified (M/T 210-4184 / A/T 210-4270) and excluded.
  - Group 1: Mazda Miata 1990-1990; Mazda MX-5* 1990-1990
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4160 Miata 1.6 1990-1993 unqualified (the same published list covers the 94-97 1.8 M/T cars, which are transmission-qualified rows).
  - Group 1: Mazda Miata 1990-1993; Mazda MX-5* 1990-1993

### mazda-miata-18 — Mazda BP 1.8 I4 (Miata NA/NB)

- **Engine:** 1.8L 4-cyl
- **Family applications:** Mazda Miata 1994-2005, Mazda MX-5* 1994-2005
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3155 (70A) Miata 1.8 1999-2000; 210-3157 (80A) Miata 1.8 2001-2005, both unqualified. The 1994-97 (NA8) rows split by transmission (210-4157 A/T / 210-4284 M/T) and are excluded.
  - Group 1: Mazda Miata 1999-2000; Mazda MX-5* 1999-2000
  - Group 2: Mazda Miata 2001-2005; Mazda MX-5* 2001-2005
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4137 Miata 1.8 1999-2005 unqualified. The 94-97 rows split by transmission and are excluded.
  - Group 1: Mazda Miata 1999-2005; Mazda MX-5* 1999-2005

### mazda-miata-nc — Mazda MZR 2.0 I4 (Miata NC)

- **Engine:** 2.0L 4-cyl
- **Family applications:** Mazda Miata 2006-2015, Mazda MX-5* 2006-2015
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4238 (100A) MX-5 Miata 2.0 2006-2008 (the same published list covers the 2006-09 Mazda6); 210-4334 (100A) MX-5 Miata 2.0 2009-2012, both unqualified. 2013-15 is past this catalog edition — left at likely.
  - Group 1: Mazda Miata 2006-2008; Mazda MX-5* 2006-2008
  - Group 2: Mazda Miata 2009-2012; Mazda MX-5* 2009-2012
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4334 MX-5 Miata 2.0 2006-2008; 280-4336 MX-5 Miata 2.0 2009-2012, both unqualified.
  - Group 1: Mazda Miata 2006-2008; Mazda MX-5* 2006-2008
  - Group 2: Mazda Miata 2009-2012; Mazda MX-5* 2009-2012

### mazda-mpv30 — Mazda MPV 3.0 V6

- **Engine:** 3.0L 6-cyl
- **Family applications:** Mazda MPV 1989-1998, Mazda MPV 2002-2006
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4180 (110A) MPV 3.0 2002-2005; 210-4105 (70A) MPV 3.0 1989-1998 — both unqualified.
  - Group 1: Mazda MPV 2002-2005
  - Group 2: Mazda MPV 1989-1998
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4192 MPV 3.0 2002-2006; 280-4116 MPV 3.0 1992-1995 — both unqualified (96-98 rows split Std/Opt — excluded).
  - Group 1: Mazda MPV 2002-2006
  - Group 2: Mazda MPV 1992-1995

### mazda-protege — Mazda Protege 1.5/1.6/1.8/2.0 I4

- **Engine:** 1.5/1.6/1.8/2.0L 4-cyl
- **Family applications:** Mazda Protege 1992-2003, Mazda Protege5 2002-2003
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4163 (80A) Protege 2.0 2001-2003 and Protege5 2.0 2002-2003 — span capped to 02-03 because the 1.6 (its own unit) was still sold in 2001; 210-4200 (70A) Protege 1.5 and 1.8 1997-1998 — one unit for both engines (the 99-01 1.8 rows aren't published, so those years are excluded).
  - Group 1: Mazda Protege 2002-2003; Mazda Protege5 2002-2003
  - Group 2: Mazda Protege 1997-1998
- **starter:** no verified group — Likely tier only. Note: every published starter row splits by transmission — match part number

### mazda-rx7 — Mazda 13B rotary (RX-7)

- **Engine:** 1.3L 2-cyl
- **Family applications:** Mazda RX-7 1986-1995, Mazda RX7 1986-1995
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4241 (100A) RX-7 1.3 rotary 1993-1995 unqualified (the FD span). The 86-88 FC row is turbo-qualified and 89-92 FC rows aren't published — both excluded.
  - Group 1: Mazda RX-7 1993-1995; Mazda RX7 1993-1995
- **starter:** no verified group — Likely tier only. Note: FC starters split by transmission — match part number

### mazda-rx8 — Mazda 13B-MSP Renesis rotary (RX-8)

- **Engine:** 1.3L 2-cyl
- **Family applications:** Mazda RX-8 2004-2011, Mazda RX8 2004-2011
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4213 (100A) RX-8 2005-2007 (the 2004 row is build-date-qualified 'From 04/04/2003' and excluded); 210-4343 (110A) RX-8 2009-2011, unqualified. No 2008 alternator row is published — 2008 stays at likely.
  - Group 1: Mazda RX-8 2005-2007; Mazda RX8 2005-2007
  - Group 2: Mazda RX-8 2009-2011; Mazda RX8 2009-2011
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4342 RX-8 2011 (engine codes M, P) unqualified — the 2009-10 rows for the same unit are transmission-qualified and excluded.
  - Group 1: Mazda RX-8 2011-2011; Mazda RX8 2011-2011

### mini-r50 — MINI Cooper 1.6 (R50/R52/R53)

- **Engine:** 1.6L 4-cyl
- **Family applications:** MINI Cooper 2002-2006
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0844 (105A) Cooper W10 2002-2004 plus 2005 coupe and convertible rows; the supercharged S (W11, 210-0524) spans 2002-2006 — match trim. Group capped at 2002-2005 where both published lists cover every body style.
  - Group 1: MINI Cooper 2002-2005
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### mitsu-24 — Mitsubishi 4G64/4G69 2.4 I4

- **Engine:** 2.4L 4-cyl
- **Family applications:** Mitsubishi Eclipse 2000-2012, Mitsubishi Galant 1994-2012, Mitsubishi Lancer 2005-2017, Mitsubishi Outlander 2003-2006, Mitsubishi Outlander 2007-2013, Mitsubishi Outlander Sport 2015-2017
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows engine-coded 4G64/4G69 and unqualified: 210-4215 (110A) Eclipse 2.4 2006-2011, Galant 2.4 2004-2011 and Lancer 2.4 2005-2006 — one published unit across all three; 210-4142 (85A) Galant 2.4 2000-2003; 210-4156 (90A) Galant 2.4 1997-1999; 210-4160 (90A) Eclipse 2.4 2000-2001 (the 02-05 rows split by transmission and are excluded).
  - Group 1: Mitsubishi Eclipse 2006-2011; Mitsubishi Galant 2004-2011; Mitsubishi Lancer 2005-2006
  - Group 2: Mitsubishi Galant 2000-2003
  - Group 3: Mitsubishi Galant 1997-1999
  - Group 4: Mitsubishi Eclipse 2000-2001
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4213 Galant 2.4 2005-2009 and Lancer 2.4 2005-2006 (both 4G69), unqualified — the 2004 Galant row carries a From-09/2003 build-date qualifier, so 2004 stays outside the span.
  - Group 1: Mitsubishi Galant 2005-2009; Mitsubishi Lancer 2005-2006

### mitsu-4b11 — Mitsubishi 4B11 2.0 I4 (Lancer)

- **Engine:** 2.0L 4-cyl
- **Family applications:** Mitsubishi Lancer 2008-2017, Mitsubishi Outlander Sport 2011-2017
- **alternator:** no verified group — Likely tier only. Note: turbo (Ralliart/Evo) and non-turbo 2.0s use different published units — confirm which you have; pairs stay Likely
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4317 Lancer 2.0 2010 — the one year where both the naturally-aspirated row and the Evolution GSR turbo row carry the same number (the Evo MR's dual-clutch starter isn't published; other years split by turbo or build date).
  - Group 1: Mitsubishi Lancer 2010-2010

### mitsu-4g94 — Mitsubishi 4G94 2.0 I4 (Lancer 02-07)

- **Engine:** 2.0L 4-cyl
- **Family applications:** Mitsubishi Lancer 2002-2007
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4165 (85A) Lancer 2.0 2002 — clean row (03-04 rows carry a non-turbo qualifier because the Evo arrived in 2003); 210-4271 (105A) Lancer 2.0 4G94 2007 — clean row (the Evo IX ended in 2006).
  - Group 1: Mitsubishi Lancer 2002-2002
  - Group 2: Mitsubishi Lancer 2007-2007
- **starter:** no verified group — Likely tier only. Note: 03+ rows carry non-turbo qualifiers (Evo years) — match part number

### mitsu-6g72 — Mitsubishi 6G72 3.0 V6 (Eclipse/Galant)

- **Engine:** 3.0L 6-cyl
- **Family applications:** Mitsubishi Eclipse 2000-2005, Mitsubishi Galant 1999-2003, Chrysler Sebring 2001-2005, Dodge Stratus 2001-2005, Mitsubishi Montero Sport 1997-2004
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4179 (85A) in one published set — Eclipse 3.0 2002-2005 and 2000, Galant 3.0 2002-2003 and 1999-2000, plus Sebring 3.0 coupe 2001-2005, all unqualified (2001 rows aren't printed for Eclipse/Galant, so their 2001 cars sit between spans).
  - Group 1: Mitsubishi Eclipse 2002-2005; Chrysler Sebring 2001-2005; Mitsubishi Eclipse 2000-2000; Mitsubishi Galant 2002-2003; Mitsubishi Galant 1999-2000
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4165 Galant 3.0 1999-2003 and Sebring 3.0 coupe 2001-2005 — one published unit, unqualified.
  - Group 1: Mitsubishi Galant 1999-2003; Chrysler Sebring 2001-2005

### mitsu-6g75 — Mitsubishi 6G75 3.8 V6 (Eclipse/Galant)

- **Engine:** 3.8L 6-cyl
- **Family applications:** Mitsubishi Eclipse 2006-2012, Mitsubishi Galant 2004-2009, Mitsubishi Endeavor 2004-2011
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4230 (110A) Eclipse 3.8 2006-2011 and Galant 3.8 2005-2009, one published unit, unqualified; 210-4208 (110A) Galant 3.8 2004.
  - Group 1: Mitsubishi Eclipse 2006-2011; Mitsubishi Galant 2005-2009
  - Group 2: Mitsubishi Galant 2004-2004
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4212 Galant 3.8 2004-2009 — one published unit, unqualified.
  - Group 1: Mitsubishi Galant 2004-2009

### mitsu-dsm — Mitsubishi 4G63/420A 1.8/2.0 I4 (DSM Eclipse/Talon)

- **Engine:** 1.8/2.0L 4-cyl
- **Family applications:** Mitsubishi Eclipse 1990-1995, Mitsubishi Eclipse 1996-1999, Eagle Talon 1990-1998, Plymouth Laser 1990-1994
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4120 (90A) Eclipse 1999 listed for the 420A and the 4G63 turbo alike, unqualified — one published unit for every 99 Eclipse. All earlier DSM rows split by transmission, turbo or drivetrain and are excluded.
  - Group 1: Mitsubishi Eclipse 1999-1999
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### mitsu-evo — Mitsubishi Evo 2.0 turbo I4 (4G63T/4B11T)

- **Engine:** 2.0L 4-cyl
- **Family applications:** Mitsubishi Lancer Evolution 2003-2015
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4229 (90A) Lancer 4G63 'w/ Turbo' 2003-2006 — every US Lancer Evolution those years is the 4G63 turbo, so the span is exact for the Evolution model; 210-4338 (130A) Lancer 4B11 'w/ Turbo' 2008-2011 — the Evo X span (the Ralliart shares the engine but is a separate feed model). 2012-15 Evo X is past this catalog edition — left at likely.
  - Group 1: Mitsubishi Lancer Evolution 2003-2006
  - Group 2: Mitsubishi Lancer Evolution 2008-2011
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### mopar-37 — Chrysler PowerTech 3.7 V6

- **Engine:** 3.7L 6-cyl
- **Family applications:** Jeep Liberty 2002-2012, Dodge Dakota 2004-2011, Dodge|Ram Ram* 2002-2012, Ram 1500* 2011-2012, Jeep Grand Cherokee 2005-2010, Dodge Nitro 2007-2011, Jeep Commander 2006-2010
- **alternator — verified evidence:** Mopar OEM 56029914AC fitment (jeeppartsdeal.com, retrieved 2026-10-22): Liberty 3.7 2002-2005, Grand Cherokee 3.7 2005-2006; Denso 421000-0040 vendor table: Commander 3.7 2006-2010. Mopar RL041120AC/56029700AD: Ram 3.7 2002-2008 (same units as the 4.7 trucks).
  - Group 1: Jeep Liberty 2002-2005; Jeep Grand Cherokee 2005-2006; Jeep Commander 2006-2010
  - Group 2: Dodge|Ram Ram* 2002-2008
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### mopar-47 — Chrysler PowerTech 4.7 V8

- **Engine:** 4.7L 8-cyl
- **Family applications:** Jeep Grand Cherokee 1999-2009, Dodge Dakota 2000-2011, Dodge Durango 2000-2009, Dodge|Ram Ram* 2002-2013, Chrysler|Dodge Dodge 1500 2002-2008, Ram 1500* 2011-2013, Jeep Commander 2006-2009, Chrysler Aspen 2007-2009
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
- **Family applications:** Dodge|Ram Ram* 2003-2024, Chrysler|Dodge Dodge 1500 2003-2008, Ram 1500* 2011-2024, Ram 2500* 2011-2024, Ram 3500* 2011-2024, Dodge Charger 2006-2023, Dodge Challenger 2009-2023, Chrysler 300 2005-2023, Dodge Magnum 2005-2008, Jeep Grand Cherokee 2005-2021, Dodge Durango 2011-2023, Jeep Commander 2006-2009, Chrysler Aspen 2007-2009
- **alternator — verified evidence:** TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-11298 (Chrysler 5602869, Denso 7S) Ram 5.7 2007-2008.
  - Group 1: Dodge|Ram Ram* 2007-2008
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### mopar-lh27 — Chrysler LH 2.7 V6 (Intrepid/Concorde)

- **Engine:** 2.7L 6-cyl
- **Family applications:** Dodge Intrepid 1998-2004, Chrysler Concorde 1998-2004, Chrysler 300M 1999-2004
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0686 (120A) Intrepid 2.7 1999-2001 — one published unit, unqualified (the 3.2/3.5 use their own units; 02-04 rows split Std/Opt). Concorde/300M spans not separately verified — left at likely.
  - Group 1: Dodge Intrepid 1999-2001
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### mopar-magnum — Dodge Magnum 5.2/5.9 V8

- **Engine:** 5.2/5.9L 8-cyl
- **Family applications:** Dodge|Ram Ram* 1994-2001, Chrysler|Dodge Dodge 1500 1994-2001, Dodge Dakota 1992-2003, Dodge Durango 1998-2003, Jeep Grand Cherokee 1993-1998
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

### mopar-minivan-ohv — Chrysler minivan 3.3/3.8 OHV V6 (01-10)

- **Engine:** 3.3/3.8L 6-cyl
- **Family applications:** Dodge Grand Caravan 2001-2010, Chrysler Grand Caravan 2001-2010, Dodge Caravan 2001-2007, Chrysler Caravan 2001-2007, Chrysler Town & Country 2000-2010, Chrysler Town And Country 2000-2010, Chrysler Town &amp; Country 2000-2010, Chrysler Voyager 2001-2003
- **alternator:** no verified group — Likely tier only. Note: every published alternator row splits Std vs Opt amperage — match the amp rating on your old unit
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), Grand Caravan rows unqualified for both the 3.3 and 3.8: 280-0360 2006-2010; 280-0349 2004-2005; 280-0321 2001-2003 (the 2003 FLEX Fuel/GAS tags don't discriminate — both carry the same number). Caravan/Town & Country spans not separately verified — left at likely.
  - Group 1: Dodge Grand Caravan 2006-2010
  - Group 2: Dodge Grand Caravan 2004-2005
  - Group 3: Dodge Grand Caravan 2001-2003

### mopar-neon — Dodge/Plymouth Neon 2.0 I4

- **Engine:** 2.0L 4-cyl
- **Family applications:** Dodge Neon 1995-2005, Plymouth Neon 1995-2001
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), Dodge rows all unqualified: 210-4139 (85A) Neon 2.0 2000-2005 (a 145A option unit, 210-0558, is also listed for 2003 — match amperage); 210-4138 (83A) 1998-1999; 210-4119 (83A) 1996-1997; 210-4233 (85A) 1995. Plymouth spans not separately published — left at likely.
  - Group 1: Dodge Neon 2000-2005
  - Group 2: Dodge Neon 1998-1999
  - Group 3: Dodge Neon 1996-1997
  - Group 4: Dodge Neon 1995-1995
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), Dodge rows unqualified: 280-5370 Neon 2.0 2000-2002; 280-6109 1998-1999; 280-5349 1996-1997 (the 1995 year is dual-listed with 280-6108 — excluded).
  - Group 1: Dodge Neon 2000-2002
  - Group 2: Dodge Neon 1998-1999
  - Group 3: Dodge Neon 1996-1997

### mopar-pacifica — Chrysler Pacifica 3.5/3.8/4.0 V6

- **Engine:** 3.5/3.8/4.0L 6-cyl
- **Family applications:** Chrysler Pacifica* 2004-2008
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0671 (120A) Pacifica 3.5 2004-2006 — kept to 2004 only (the sole-3.5 model year); 05-06 also fielded the 3.8 whose alternator is not published for those years, and 07-08 units differ 3.8 (210-4340) vs 4.0 (210-0632), so cross-engine years stay Likely.
  - Group 1: Chrysler Pacifica* 2004-2004
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0349 Pacifica 3.5 2005-2006 and 3.8 2005 — the verified span is 2005 only, the year both engines carry the one number (2006 3.8 moved to 280-0360; 2004 splits by build date).
  - Group 1: Chrysler Pacifica* 2005-2005

### mopar-pentastar — Chrysler Pentastar 3.6 V6

- **Engine:** 3.6L 6-cyl
- **Family applications:** Dodge Grand Caravan 2011-2020, Chrysler Town & Country 2011-2016, Chrysler Town And Country 2011-2016, Chrysler Town &amp; Country 2011-2016, Dodge Caravan 2011-2019, Chrysler Caravan 2011-2019, Volkswagen Routan 2011-2014, Dodge Journey 2011-2020, Chrysler Journey 2011-2020, Dodge Avenger 2011-2014, Chrysler Avenger 2011-2014, Chrysler 200 2011-2017, Dodge Charger 2011-2023, Dodge Challenger 2011-2023, Chrysler 300 2011-2023, Dodge Durango 2011-2024, Jeep Grand Cherokee 2011-2021, Jeep Wrangler 2012-2018, Dodge|Ram Ram* 2013-2024, Ram 1500* 2013-2024
- **alternator — verified evidence:** TYC 2-11570 fitment list (finditparts.com) + BBB 11570 table (partcatalog.com; Chrysler 68272108AD, Denso 421000-0770, retrieved 2026-10-22): Grand Caravan 2011-2020, Town & Country 2011-2016, Journey 3.6 2011-2019, Avenger 3.6 2011-2014, 200 3.6 2011-2014.
  - Group 1: Dodge Grand Caravan 2011-2020; Chrysler Town & Country 2011-2016; Chrysler Town And Country 2011-2016; Dodge Journey 2011-2019; Dodge Avenger 2011-2014; Chrysler 200 2011-2014
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0438 Avenger 3.6 2011-2014 and Journey 3.6 2011-2014 — the rows carry a 'FLEX Fuel' tag, but every 3.6 Pentastar in these models is flex-fuel, so it doesn't discriminate.
  - Group 1: Dodge Avenger 2011-2014; Dodge Journey 2011-2014

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
- **Family applications:** Dodge Avenger 2008-2014, Chrysler Avenger 2008-2014, Chrysler 200 2011-2014, Dodge Journey 2009-2020, Chrysler Journey 2009-2020, Dodge Caliber 2007-2012, Jeep Patriot 2007-2017, Jeep Compass 2007-2017, Chrysler Sebring 2007-2010
- **alternator — verified evidence:** Lester 11231 (Chrysler 4801323AC, Mitsubishi A2TJ0481) application tables (qpselectric.com + thenthgear.com + TYC 2-11231, retrieved 2026-10-22): Sebring 2.4 2007-2010, 200 2.4 2011-2013, Avenger 2.4 2008-2013, Caliber 2007-2012, Compass 2007-2017, Patriot 2007-2017. Journey uses a different unit — left at likely.
  - Group 1: Chrysler Sebring 2007-2010; Chrysler 200 2011-2013; Dodge Avenger 2008-2013; Dodge Caliber 2007-2012; Jeep Compass 2007-2017; Jeep Patriot 2007-2017
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4273 in one published set — Caliber 2.0/2.4 2007-2011, Compass 2.0/2.4 2008-2011 and 2015, Patriot 2.0/2.4 2008-2011 and 2015, Sebring 2.4 2007-2010, Avenger 2.4 2008-2010, Journey 2.4 2009-2010 and 2015, all unqualified (the gap years carry build-date splits — excluded).
  - Group 1: Dodge Caliber 2007-2011; Jeep Compass 2008-2011; Jeep Compass 2015-2015; Jeep Patriot 2008-2011; Jeep Patriot 2015-2015; Chrysler Sebring 2007-2010; Dodge Avenger 2008-2010; Dodge Journey 2009-2010; Dodge Journey 2015-2015

### nissan-ga16 — Nissan GA16DE 1.6 I4

- **Engine:** 1.6L 4-cyl
- **Family applications:** Nissan Sentra 1995-1999, Nissan 200SX 1995-1998
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3127 (80A) Sentra 1.6 GA16DE 1997-1999 unqualified; 210-3117 (70A) Sentra 1.6 1995-1996 unqualified. 200SX rows are not published separately in this edition.
  - Group 1: Nissan Sentra 1997-1999
  - Group 2: Nissan Sentra 1995-1996
- **starter:** no verified group — Likely tier only. Note: every published starter row splits M/T vs A/T and California — all pairs stay Likely

### nissan-hr16 — Nissan HR16DE 1.6 I4

- **Engine:** 1.6L 4-cyl
- **Family applications:** Nissan Versa 2012-2019, Nissan Versa Note 2014-2019
- **alternator — verified evidence:** Nissan OEM 23100-3BE1A fitment (nissanpartsdeal.com, retrieved 2026-10-22): Versa 1.6 HR16DE 2012-2019, Versa Note 1.6 2014-2019. Cross-referenced Lester 11547 / Mitsubishi A2TJ1791 vendor tables show identical spans.
  - Group 1: Nissan Versa 2012-2019; Nissan Versa Note 2014-2019
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### nissan-ka24 — Nissan KA24E/DE 2.4 I4

- **Engine:** 2.4L 4-cyl
- **Family applications:** Nissan Altima 1993-2001, Nissan 240SX 1989-1998, Nissan Frontier 1998-2004, Nissan Xterra 2000-2004, Nissan Pickup 1990-1997
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3146 (100A) Altima KA24DE 1998-2001; 210-3156 (70A) Frontier and Xterra KA24DE 2002-2004; 210-3118 (70A) Frontier 1998-2000 and Xterra 2000; 210-3170 (80A) 240SX KA24E 1989-1990. The 91-98 (KA24DE) 240SX and early Altima use other units — left at likely.
  - Group 1: Nissan Altima 1998-2001
  - Group 2: Nissan Frontier 2002-2004; Nissan Xterra 2002-2004
  - Group 3: Nissan Frontier 1998-2000; Nissan Xterra 2000-2000
  - Group 4: Nissan 240SX 1989-1990
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4109 240SX 2.4 1991-1996 unqualified (the 89-90 rows are vendor-split and excluded); 280-4175 Xterra and Frontier KA24DE 2002-2004 unqualified; 280-4100 Xterra and Frontier KA24DE 2000-2001 unqualified (98-99 Frontier splits 2WD vs 4WD).
  - Group 1: Nissan 240SX 1991-1996
  - Group 2: Nissan Xterra 2002-2004; Nissan Frontier 2002-2004
  - Group 3: Nissan Xterra 2000-2001; Nissan Frontier 2000-2001

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

### nissan-qg18 — Nissan QG18DE 1.8 I4

- **Engine:** 1.8L 4-cyl
- **Family applications:** Nissan Sentra 2000-2006
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3158 (80A) Sentra 1.8 QG18DE 2002-2006 unqualified; 210-3147 (100A) Sentra 1.8 2000-2001 unqualified.
  - Group 1: Nissan Sentra 2002-2006
  - Group 2: Nissan Sentra 2000-2001
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5373 Sentra 1.8 2003-2005 unqualified (three CID spellings, one number); 280-3138 Sentra 1.8 QG18DE 2006; 280-3137 Sentra 1.8 2000-2001.
  - Group 1: Nissan Sentra 2003-2005
  - Group 2: Nissan Sentra 2006-2006
  - Group 3: Nissan Sentra 2000-2001

### nissan-qr25 — Nissan QR25DE 2.5 I4

- **Engine:** 2.5L 4-cyl
- **Family applications:** Nissan Altima 2002-2018, Nissan Sentra 2002-2006, Nissan Rogue 2008-2020, Nissan Rogue Select 2014-2015, Nissan Frontier 2005-2019
- **alternator — verified evidence:** TYC 2-13939 application table (tycamericas.com, retrieved 2026-10-22) + DB Electrical 400-44053 (Lester 13939, Hitachi LR1110-726): Altima 2.5 2002-2006, Sentra 2.5 (SE-R/Spec V) 2002-2006. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3163 (110A) Frontier 2.5 QR25DE 2005-2011 unqualified.
  - Group 1: Nissan Altima 2002-2006; Nissan Sentra 2002-2006
  - Group 2: Nissan Frontier 2005-2011
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4282 Frontier 2.5 QR25DE 2005-2011 unqualified (Altima/Sentra QR25 starters split M/T vs A/T and stay Likely).
  - Group 1: Nissan Frontier 2005-2011

### nissan-vg30-maxima — Nissan VG30E/VE30DE 3.0 V6 (Maxima)

- **Engine:** 3.0L 6-cyl
- **Family applications:** Nissan Maxima 1989-1994
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3131 (90A) Maxima 3.0 VG30E 1989-1991 unqualified (the 92-94 rows are SOHC-vs-DOHC split between 210-3131 and 210-3135 and stay Likely).
  - Group 1: Nissan Maxima 1989-1991
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-3106 Maxima 3.0 1989-1991 unqualified (92-94 rows split SOHC/DOHC and M/T vs A/T).
  - Group 1: Nissan Maxima 1989-1991

### nissan-vg33 — Nissan VG33E 3.3 V6 (Pathfinder/Xterra/Frontier)

- **Engine:** 3.3L 6-cyl
- **Family applications:** Nissan Pathfinder 1996-2000, Infiniti QX4* 1997-2000, Nissan Xterra 2000-2004, Nissan Frontier 1999-2004, Nissan Quest 1999-2002, Mercury Villager 1999-2002
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3134 (90A) Pathfinder 3.3 VG33E 1998-2000 (1997 splits 1st/2nd production); 210-3128 (80A) Xterra 3.3 2000 and Frontier 3.3 1999-2000; 210-3149 (100A) Xterra and Frontier 3.3 2003-2004 incl. the supercharged VG33ER.
  - Group 1: Nissan Pathfinder 1998-2000
  - Group 2: Nissan Xterra 2000-2000; Nissan Frontier 1999-2000
  - Group 3: Nissan Xterra 2003-2004; Nissan Frontier 2003-2004
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4135 Pathfinder 3.3 1996-2000 unqualified; 280-4136 Xterra 3.3 2000-2004 and Frontier 3.3 1999-2004 (incl. VG33ER), unqualified.
  - Group 1: Nissan Pathfinder 1996-2000
  - Group 2: Nissan Xterra 2000-2004; Nissan Frontier 1999-2004

### nissan-vk56 — Nissan VK56DE 5.6 V8

- **Engine:** 5.6L 8-cyl
- **Family applications:** Nissan Titan 2004-2015, Nissan Armada 2005-2015, Nissan Pathfinder Armada 2004-2004, Infiniti QX56 2004-2010
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3160 (130A) engine-coded VK56DE — Titan 2004-2006, Armada 2005-2006, Pathfinder Armada 2004. Later VK56DE years are past this catalog edition — left at likely.
  - Group 1: Nissan Titan 2004-2006; Nissan Armada 2005-2006; Nissan Pathfinder Armada 2004-2004
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### nissan-vq-hr — Nissan/Infiniti VQ35HR/VQ37VHR 3.5/3.7 V6

- **Engine:** 3.5/3.7L 6-cyl
- **Family applications:** Nissan 350Z 2007-2009, Nissan 370Z 2009-2020, Infiniti G35 2007-2008, Infiniti G37 2008-2013, Infiniti M35 2009-2010, Infiniti Q50 2014-2019
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4313 (150A) in one published application set — 350Z VQ35HR 2007-2009, G35 VQ35HR 2007-2008 (both 07 trim rows carry the same number), G37 VQ37VHR 2008-2010, 370Z VQ37VHR 2009 (the 2010 370Z rows are build-date-qualified 'To 02/2010' and excluded).
  - Group 1: Nissan 350Z 2007-2009; Infiniti G35 2007-2008; Infiniti G37 2008-2010; Nissan 370Z 2009-2009
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-3143 370Z 3.7 2010-2011 and G37 3.7 2011, unqualified (350Z/G35 HR starter rows are build-date- or trim-qualified and excluded).
  - Group 1: Nissan 370Z 2010-2011; Infiniti G37 2011-2011

### nissan-vq30 — Nissan VQ30DE 3.0 V6 (Maxima/I30)

- **Engine:** 3.0L 6-cyl
- **Family applications:** Nissan Maxima 1995-2001, Infiniti I30 1996-2001
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3106 (125A) in one published set — Maxima 3.0 VQ30DE 1995-1997 and I30 1996-1997; 210-3105 (110A) Maxima 1999 and 2001 (1998 splits SE vs Exc. SE) and I30 1998-2001; 210-3137 (100A) Maxima 2000.
  - Group 1: Nissan Maxima 1995-1997; Infiniti I30 1996-1997
  - Group 2: Nissan Maxima 1999-1999; Nissan Maxima 2001-2001; Infiniti I30 1998-2001
  - Group 3: Nissan Maxima 2000-2000
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-3126 — ONE published starter for Maxima 3.0 1995-2001 and I30 1996-2001, unqualified.
  - Group 1: Nissan Maxima 1995-2001; Infiniti I30 1996-2001

### nissan-vq35de — Nissan/Infiniti VQ35DE 3.5 V6

- **Engine:** 3.5L 6-cyl
- **Family applications:** Nissan Altima 2002-2006, Nissan Maxima 2002-2014, Nissan Murano 2003-2014, Nissan Pathfinder 2001-2004, Nissan Quest 2004-2009, Nissan Quest 2011-2017, Infiniti M35 2006-2008, Infiniti JX35 2013-2013, Infiniti QX60 2014-2020, Nissan 350Z 2003-2006, Infiniti G35 2003-2006, Infiniti I35 2002-2004, Infiniti FX35 2003-2008
- **alternator — verified evidence:** OCPTY Lester 13940 listing (Hitachi LR1110-721, Nissan 23100-8J100, retrieved 2026-10-22): Altima 3.5 2002-2006, Maxima 2002-2003, Murano 2003-2007, Infiniti I35 2002-2004. Nissan OEM 23100-7Y020 (nissanpartsdeal.com): Maxima 3.5 2004-2008 is a separate unit. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4255 (130A) Maxima 3.5 2009-2010 and Murano 2009 — later A35 Maximas (2011-14) use the same VQ35DE but this catalog edition ends there, left at likely; 210-4211 (110A) 350Z VQ35DE 2003-2006 and G35 2004-2006 (the 2003 G35 sedan row is body-qualified and excluded); 210-4207 (110A) Pathfinder 3.5 2003-2004; 210-3150 (110A) Pathfinder 3.5 2002.
  - Group 1: Nissan Altima 2002-2006; Nissan Maxima 2002-2003; Nissan Murano 2003-2007; Infiniti I35 2002-2004
  - Group 2: Nissan Maxima 2004-2008
  - Group 3: Nissan Maxima 2009-2010; Nissan Murano 2009-2009
  - Group 4: Nissan 350Z 2003-2006; Infiniti G35 2004-2006
  - Group 5: Nissan Pathfinder 2003-2004
  - Group 6: Nissan Pathfinder 2002-2002
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-3133 350Z VQ35DE 2003-2006 unqualified (the 2007 HR rows are build-date-qualified; G35 rows are drivetrain-qualified and excluded); 280-4222 Pathfinder 3.5 2001-2004 unqualified; 280-4237 Maxima 3.5 2007-2008 unqualified (02-06 Maxima splits M/T vs A/T).
  - Group 1: Nissan 350Z 2003-2006
  - Group 2: Nissan Pathfinder 2001-2004
  - Group 3: Nissan Maxima 2007-2008

### nissan-vq40 — Nissan VQ40DE 4.0 V6

- **Engine:** 4.0L 6-cyl
- **Family applications:** Nissan Pathfinder 2005-2012, Nissan Frontier 2005-2019, Nissan Xterra 2005-2015
- **alternator — verified evidence:** Nissan OEM 23100-EA20B fitment (nissanpartsdeal.com, retrieved 2026-10-22): Frontier/Pathfinder/Xterra 4.0 2005-2008 (110A). Nissan 23100-ZH00D (130A): Frontier 4.0 2007-2019. Match amperage — both units appear in the 07-08 overlap.
  - Group 1: Nissan Frontier 2005-2008; Nissan Pathfinder 2005-2008; Nissan Xterra 2005-2008
  - Group 2: Nissan Frontier 2007-2019
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4302 — one published starter for Pathfinder 4.0 2005-2011, Xterra 4.0 2005-2011 and 2015, Frontier 4.0 2005-2011 and 2015 (12-14 rows are not in this edition).
  - Group 1: Nissan Pathfinder 2005-2011; Nissan Xterra 2005-2011; Nissan Frontier 2005-2011

### nissan-z32 — Nissan VG30DE/DETT 3.0 V6 (300ZX Z32)

- **Engine:** 3.0L 6-cyl
- **Family applications:** Nissan 300ZX 1990-1996
- **alternator:** no verified group — Likely tier only. Note: NA (VG30DE) and twin-turbo (VG30DETT) alternators differ and the decode can't tell them apart — all pairs stay Likely; match part number
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4122 300ZX 3.0 1990-1996 unqualified — one published starter for every Z32, NA and twin-turbo (the 1989 Z31 row is vendor-qualified and excluded).
  - Group 1: Nissan 300ZX 1990-1996

### saturn-s19 — Saturn S-Series 1.9 I4

- **Engine:** 1.9L 4-cyl
- **Family applications:** Saturn S-Series 1991-2002
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5100 (96A) published for SL/SL1/SL2/SC/SC1/SC2 1.9 1991-1996 — one unit across every S-Series nameplate, SOHC and DOHC, unqualified (1997 rows carry an external-fan qualifier).
  - Group 1: Saturn S-Series 1991-1996
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 281-6000 SL 1.9 1998-1999 — unqualified.
  - Group 1: Saturn S-Series 1998-1999

### subaru-ej205 — Subaru EJ205 2.0 turbo H4 (WRX 02-05)

- **Engine:** 2.0L 4-cyl
- **Family applications:** Subaru WRX 2002-2005, Subaru Impreza WRX 2002-2005, Subaru Impreza 2002-2005
- **Ambiguity cap:** Subaru Impreza — only WRX trims carry the 2.0 turbo — confirm turbo before buying
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4167 (75A) Impreza EJ205 2.0 2002-2005 unqualified (the same published list covers the 03-04 EJ251 2.5 NA, which lives in subaru-ej25na).
  - Group 1: Subaru WRX 2002-2005; Subaru Impreza WRX 2002-2005
- **starter:** no verified group — Likely tier only. Note: 02-05 WRX starters split by transmission — match part number

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

### subaru-legacy25 — Subaru Legacy/Outback 2.2/2.5 H4

- **Engine:** 2.2/2.5L 4-cyl
- **Family applications:** Subaru Legacy 1990-2014, Subaru Outback 1995-2014
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows unqualified unless noted: 210-3142 (70A) Legacy 2.2 1990-1994; 210-3144 (85A) Legacy 2.2 AND 2.5 1996-1999; 210-4140 (90A) Legacy 2.5 2000 and 2002-2004 plus Outback 2.5 2002-2003 (2001 rows are M/T-qualified); 210-4216 (110A) Legacy/Outback 2.5 2006-2009 — one row covers EJ253 AND the EJ255 GT turbo; 210-4309 (110A) Legacy/Outback 2.5 2010-2011 (incl. 2.5GT); 210-4203 (110A) Legacy/Outback 2.5 FB25 2013-2014.
  - Group 1: Subaru Legacy 1990-1994
  - Group 2: Subaru Legacy 1996-1999
  - Group 3: Subaru Legacy 2000-2000; Subaru Legacy 2002-2004; Subaru Outback 2002-2003
  - Group 4: Subaru Legacy 2006-2009; Subaru Outback 2006-2009
  - Group 5: Subaru Legacy 2010-2011; Subaru Outback 2010-2011
  - Group 6: Subaru Legacy 2013-2014; Subaru Outback 2013-2014
- **starter:** no verified group — Likely tier only. Note: published rows split by transmission — match part number

### toyota-1gr — Toyota 1GR-FE 4.0 V6

- **Engine:** 4.0L 6-cyl
- **Family applications:** Toyota Tacoma 2005-2015, Toyota 4Runner 2003-2021, Toyota Tundra 2005-2010, Toyota FJ Cruiser 2007-2014
- **alternator — verified evidence:** Lester 13984 listings (txasap.com: 4Runner 4.0 2003-2009; OEG amazon.com: Tacoma 4.0 2005-2015; Eagle High: FJ Cruiser 2007-2010, Tundra 4.0 2006-2010; Toyota 27060-31020/31021, Denso 104210-3470/4870, retrieved 2026-10-22).
  - Group 1: Toyota Tacoma 2005-2015; Toyota 4Runner 2003-2009; Toyota FJ Cruiser 2007-2010; Toyota Tundra 2006-2010
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### toyota-1mz — Toyota/Lexus 1MZ-FE 3.0 V6

- **Engine:** 3.0L 6-cyl
- **Family applications:** Toyota Camry 1994-2006, Toyota Avalon 1995-2004, Toyota Solara 1999-2003, Toyota Camry Solara 1999-2003, Toyota Sienna 1998-2003, Toyota Highlander 2001-2003, Lexus ES 300 1994-2003, Lexus RX 300 1999-2003
- **alternator — verified evidence:** Hollander interchange 601-58691 (retrieved 2026-10-22) crosses Camry V6 97-01 = ES 300 97-01; Denso 101211-7440/7450 = Toyota 27060-20230 100A across the 1MZ family per Denso catalog + ToyotaNation cross-reference
  - Group 1: Toyota Camry 1997-2001; Lexus ES 300 1997-2001
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### toyota-1nz — Toyota 1NZ-FE 1.5 I4 (Yaris/Echo/xA/xB)

- **Engine:** 1.5L 4-cyl
- **Family applications:** Toyota Yaris 2007-2015, Toyota Echo 2000-2005, Scion xA 2004-2006, Scion xB 2004-2006
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0799 (80A) Yaris 1.5 1NZ-FE 2010-2014 unqualified; 210-0619 (80A) Yaris 1.5 2007-2009 unqualified.
  - Group 1: Toyota Yaris 2010-2014
  - Group 2: Toyota Yaris 2007-2009
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0401 Yaris 1.5 2013-2015 unqualified; 280-0395 Yaris 1.5 2012 unqualified (07-11 rows split M/T vs A/T).
  - Group 1: Toyota Yaris 2013-2015
  - Group 2: Toyota Yaris 2012-2012

### toyota-1zz — Toyota/Pontiac 1ZZ-FE 1.8 I4

- **Engine:** 1.8L 4-cyl
- **Family applications:** Toyota Corolla 1998-2008, Toyota Matrix 2003-2008, Pontiac Vibe 2003-2008, Toyota Celica 2000-2005, Toyota MR2 Spyder 2000-2005, Chevrolet Prizm 1998-2002
- **alternator — verified evidence:** TYC 2-13878 application table (tycamericas.com) + discountstarterandalternator.com VIN-qualified list (Lester 13878, Toyota 27060-22040, retrieved 2026-10-22): Corolla 1ZZ 2003-2008, Matrix 2003-2008 (excl XRS), Vibe 2003-2008 (excl GT), Celica GT 2000-2005, MR2 Spyder 2000-2005. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0432 (80A) Corolla 1ZZ-FE 1998-2001 and Chevrolet Prizm 1.8 1998-2002, both unqualified (the 2002 Corolla splits by build plant — excluded).
  - Group 1: Toyota Corolla 2003-2008; Toyota Matrix 2003-2008; Pontiac Vibe 2003-2008; Toyota Celica 2000-2005; Toyota MR2 Spyder 2000-2005
  - Group 2: Toyota Corolla 1998-2001; Chevrolet Prizm 1998-2002
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
- **Family applications:** Toyota Camry 2002-2009, Toyota Solara 2004-2008, Toyota Camry Solara 2004-2008, Toyota RAV4 2004-2008, Toyota Highlander 2001-2007, Scion tC 2005-2010, Scion xB 2008-2015, Toyota Matrix 2009-2013, Toyota Corolla 2009-2010
- **alternator — verified evidence:** TYC 2-11034 fitment table (standardautopart.com, retrieved 2026-10-22): Camry 2.4 04-06, Highlander 2.4 04-07, RAV4 04-05, Solara 2.4 04-08 + DB Electrical AND0288 adds tC 05-10 (Toyota 27060-0H100/28260/28270). Toyota 27060-0H111-84 OEM listing (toyota.oempartsonline.com, retrieved 2026-10-22): Camry 2.4 07-09, Matrix 2.4 09-13, Corolla 2.4 09-10.
  - Group 1: Toyota Camry 2004-2006; Toyota Highlander 2004-2007; Toyota RAV4 2004-2005; Toyota Solara 2004-2008; Toyota Camry Solara 2004-2008; Scion tC 2005-2010
  - Group 2: Toyota Camry 2007-2009; Toyota Matrix 2009-2013; Toyota Corolla 2009-2010
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0174 RAV4 2.4 2004-2005; 280-0345 RAV4 2.4 2006-2008 (the 3.5 V6 carries the same number) — both unqualified.
  - Group 1: Toyota RAV4 2004-2005
  - Group 2: Toyota RAV4 2006-2008

### toyota-2gr — Toyota/Lexus 2GR-FE 3.5 V6

- **Engine:** 3.5L 6-cyl
- **Family applications:** Toyota Camry 2007-2017, Toyota Avalon 2005-2018, Toyota Sienna 2007-2016, Toyota Highlander 2008-2016, Toyota RAV4 2006-2012, Toyota Venza 2009-2015, Lexus ES 350 2007-2018, Lexus RX 350 2007-2015
- **alternator — verified evidence:** TYC 2-11137 application table (tycamericas.com, retrieved 2026-10-22; Toyota 27060-31111-84, Lester 11137, 130A): Camry 3.5 2007-2017, Avalon 2005-2018, Highlander 3.5 2008-2013, RAV4 3.5 2009-2010, Venza 3.5 2009-2015, ES 350 2007-2018, RX 350 2007-2009. Sienna and RAV4 06-08 are NOT in this unit — left at likely.
  - Group 1: Toyota Camry 2007-2017; Toyota Avalon 2005-2018; Toyota Highlander 2008-2013; Toyota RAV4 2009-2010; Toyota Venza 2009-2015; Lexus ES 350 2007-2018; Lexus RX 350 2007-2009
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### toyota-2jz — Toyota/Lexus 2JZ 3.0 I6 (Supra MK4/SC/GS/IS)

- **Engine:** 3.0L 6-cyl
- **Family applications:** Toyota Supra 1993-1998, Lexus SC300 1992-2000, Lexus GS300 1993-2005, Lexus IS300 2001-2005
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows engine-coded 2JZGE and unqualified: 210-0506 (100A) GS300 2001-2005 and IS300 2001-2005; 210-0286 (100A) GS300 1999-2000 (the 1998 row is production-split and excluded); 210-0293 (80A) GS300 1996-1997; 210-0169 (80A) GS300 1993-1995; 210-0290 (80A) SC300 1997-2000; 210-0287 (80A) SC300 1996 (the 1995 rows are production-split); 210-0168 (100A) SC300 1992-1994. Supra rows split NA/turbo and by transmission — excluded.
  - Group 1: Lexus GS300 2001-2005; Lexus IS300 2001-2005
  - Group 2: Lexus GS300 1999-2000
  - Group 3: Lexus GS300 1996-1997
  - Group 4: Lexus GS300 1993-1995
  - Group 5: Lexus SC300 1997-2000
  - Group 6: Lexus SC300 1996-1996
  - Group 7: Lexus SC300 1992-1994
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows engine-coded 2JZGE/unqualified: 280-0234 GS300 1998-2005 and IS300 2001-2005; 280-0163 Supra 3.0 1993-1998, SC300 1995-2000 and GS300 1993-1997 — one published starter across the NA and twin-turbo Supra alike.
  - Group 1: Lexus GS300 1998-2005; Lexus IS300 2001-2005
  - Group 2: Toyota Supra 1993-1998; Lexus SC300 1995-2000; Lexus GS300 1993-1997

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
- **Family applications:** Toyota Camry 2004-2006, Toyota Solara 2004-2008, Toyota Camry Solara 2004-2008, Toyota Sienna 2004-2006, Toyota Highlander 2004-2007, Lexus ES 330 2004-2006, Lexus RX 330 2004-2006
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0543 (100A std) Lexus ES330 2004-2006, RX330 2004-2006 (Japan-built std), Camry 3.3 2004, Highlander 3.3 2004-2007; 210-0545 (130A opt) RX330 2004-2006 (US-built opt) and Sienna 3.3 2004-2006. Amp option splits noted in research notes.
  - Group 1: Lexus ES 330 2004-2006; Lexus RX 330 2004-2006; Toyota Camry 2004-2004; Toyota Highlander 2004-2007
  - Group 2: Lexus RX 330 2004-2006; Toyota Sienna 2004-2006
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### toyota-3s — Toyota 2S/3S 2.0 I4 (Celica/MR2 Turbo)

- **Engine:** 2.0L 4-cyl
- **Family applications:** Toyota Celica 1986-1993, Toyota MR2 1991-1995
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0103 (70A) Celica 3S-FE and 3S-GE 1988-1989, one unit for both; 210-0274 (60A) Celica 3S-FE/3S-GE 1987; 210-0264 (80A) Celica All-Trac 3S-GTE 1992-1993 (the only 2.0 Celica those years). The 90-93 5S-FE 2.2 rows split by transmission and belong to toyota-5s anyway; MR2 Turbo rows aren't separately published — MR2 pairs stay Likely.
  - Group 1: Toyota Celica 1988-1989
  - Group 2: Toyota Celica 1987-1987
  - Group 3: Toyota Celica 1992-1993
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### toyota-4a — Toyota 4A/7A 1.6/1.8 I4 (Corolla era)

- **Engine:** 1.6/1.8L 4-cyl
- **Family applications:** Toyota Corolla 1985-1997, Geo|Chevrolet Prizm 1989-1997, Toyota Celica 1990-1999
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0100 (17mm shaft) and 210-0101 (15mm shaft) both list Corolla 4A-FE 1.6 and 7A-FE 1.8 1993-1997 with identical spans — two published shaft diameters, match yours; 210-0152 Corolla 4A-FE 1990 unqualified (1991-92 rows are stamp-number-qualified, 88-89 split 4A-F/FE vs the twin-cam 4A-GE, and Prizm rows are fan- or vendor-qualified — all excluded).
  - Group 1: Toyota Corolla 1993-1997
  - Group 2: Toyota Corolla 1990-1990
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0305 Prizm 1.6/1.8 1994-1997 unqualified (the matching Corolla rows those years are Cold-Spec-qualified and excluded); 280-0304 Prizm 1.6/1.8 1993; 280-0100 Corolla 1.6/1.8 1997 unqualified.
  - Group 1: Geo|Chevrolet Prizm 1994-1997
  - Group 2: Geo|Chevrolet Prizm 1993-1993
  - Group 3: Toyota Corolla 1997-1997

### toyota-5s — Toyota 5S-FE 2.2 I4

- **Engine:** 2.2L 4-cyl
- **Family applications:** Toyota Camry 1992-2001, Toyota Celica 1994-1999, Toyota Solara 1999-2001, Toyota Camry Solara 1999-2001, Toyota MR2 1991-1995
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0187 (80A) Camry 5SFE 1997-2001 and Solara 5SFE 1999 and 2001. Celica/MR2 5S use earlier units — left at likely.
  - Group 1: Toyota Camry 1997-2001; Toyota Solara 1999-2001; Toyota Camry Solara 1999-2001
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

### toyota-m6 — Toyota 5M/7M 2.8/3.0 I6 (Supra MK3/Cressida)

- **Engine:** 2.8/3.0L 6-cyl
- **Family applications:** Toyota Supra 1986-1992, Toyota Cressida 1985-1992
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0158 (80A) Cressida 7M-GE 1989-1992 unqualified (the Supra rows for the same unit are turbo/transmission-qualified and excluded); 210-0167 (60A) Cressida 5M-GE 1987-1988; 210-0111 (60A) Cressida 5M-GE 1984-1986 (clipped to this family's 1985 start).
  - Group 1: Toyota Cressida 1989-1992
  - Group 2: Toyota Cressida 1987-1988
  - Group 3: Toyota Cressida 1985-1986
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0107 in one published set — Supra 3.0 1986-1990 and Cressida 2.8/3.0 1983-1990 (clipped to this family's 1985 start; the 81-82 rows are option-qualified); 280-0121 Supra 3.0 1991-1992 and Cressida 3.0 1991-1992.
  - Group 1: Toyota Supra 1986-1990; Toyota Cressida 1985-1990
  - Group 2: Toyota Supra 1991-1992; Toyota Cressida 1991-1992

### toyota-rav4-1 — Toyota RAV4 2.0 I4 (1st/2nd gen)

- **Engine:** 2.0L 4-cyl
- **Family applications:** Toyota RAV4 1996-2003
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0186 (80A) RAV4 2.0 3S-FE 1996-1997; 210-0436 (80A) RAV4 2.0 3S-FE 1998-2000 — both unqualified (01-03 1AZ-FE rows split by transmission).
  - Group 1: Toyota RAV4 1996-1997
  - Group 2: Toyota RAV4 1998-2000
- **starter:** no verified group — Likely tier only. Note: 01-03 rows carry a Mfd-in-Japan qualifier — match part number

### toyota-rz — Toyota 2RZ/3RZ-FE 2.4/2.7 I4

- **Engine:** 2.4/2.7L 4-cyl
- **Family applications:** Toyota Tacoma 1995-2004, Toyota 4Runner 1996-2000, Toyota T100 1994-1998
- **alternator — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), identical units for the 2.4 (2RZFE) and 2.7 (3RZFE) in every year row: 210-0448 (60A) Tacoma 1995-1996, T100 2.7 1994-1996; 210-0188 (70A) Tacoma 1997-1999, T100 2.7 1997-1998, 4Runner 2.7 1996-1999; 210-0390 (80A) Tacoma 2000-2004, 4Runner 2.7 2000 (the same list runs to the 2005 base-2.7 Tacoma, outside this family's years).
  - Group 1: Toyota Tacoma 1995-1996; Toyota T100 1994-1996
  - Group 2: Toyota Tacoma 1997-1999; Toyota T100 1997-1998; Toyota 4Runner 1996-1999
  - Group 3: Toyota Tacoma 2000-2004; Toyota 4Runner 2000-2000
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### vw-20t — VW 2.0T EA113/EA888 I4 (GTI/Jetta)

- **Engine:** 2.0L 4-cyl
- **Family applications:** Volkswagen GTI 2006-2014, Volkswagen Jetta 2006-2013, Volkswagen Passat 2006-2010, Volkswagen CC 2009-2017, Volkswagen Tiguan 2009-2017, Volkswagen Eos 2007-2016
- **alternator:** no verified group — Likely tier only. Note: every published 2.0T alternator row is vendor-qualified (Bosch vs Valeo) — all pairs stay Likely; match the unit on your car
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5338 GTI 2.0 2006-2009, Jetta 2.0 2006-2008 and Passat 2.0T 2007-2009 in one published set, unqualified (the 2010 Passat row carries a Bosch-unit qualifier and 07-10 Passats are also dual-listed with 281-6001 — match yours); 281-6001 (First Time Fit) GTI 2.0 2010-2011 unqualified. Later Jetta rows split by fuel, body and transmission and are excluded.
  - Group 1: Volkswagen GTI 2006-2009; Volkswagen Jetta 2006-2008; Volkswagen Passat 2007-2009
  - Group 2: Volkswagen GTI 2010-2011

### vw-25 — VW 2.5 I5

- **Engine:** 2.5L 5-cyl
- **Family applications:** Volkswagen Jetta 2005-2014, Volkswagen Rabbit 2006-2009, Volkswagen Golf 2010-2014, Volkswagen Beetle 2012-2014, Volkswagen Passat 2012-2014
- **alternator — verified evidence:** Lester 11254 (VW 07K903023A, Bosch 0-124-525-062) fitment (A-Premium APALT130 + miamialternators.com, retrieved 2026-10-22): Jetta 2.5 2005-2014, Rabbit 2.5 2006-2009, Golf 2.5 2010-2014.
  - Group 1: Volkswagen Jetta 2005-2014; Volkswagen Rabbit 2006-2009; Volkswagen Golf 2010-2014
- **starter:** no verified group — Likely tier only. Note: match the part number — nose cone / tooth count can differ

### vw-b5-18t — VW/Audi 1.8T I4 (Passat/A4 longitudinal)

- **Engine:** 1.8L 4-cyl
- **Family applications:** Volkswagen Passat* 1997-2005, Audi A4 1997-2006, Audi A4 Quattro 1997-2006, Audi A4 Avant 1997-2006
- **alternator:** no verified group — Likely tier only. Note: every published alternator row carries Bosch/Valeo vendor qualifiers — all pairs stay Likely
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-6111 Passat 1.8 AWM 2002-2004, A4 1.8 2004 and A4 Quattro 1.8 2004 (2005 rows split by chassis number).
  - Group 1: Volkswagen Passat* 2002-2004; Audi A4 2004-2004; Audi A4 Quattro 2004-2004

### vw-b5-v6 — VW/Audi B5 V6 2.8/3.0 (Passat/A4)

- **Engine:** 2.8/3.0L 6-cyl
- **Family applications:** Volkswagen Passat* 1998-2005, Audi A4 1996-2006, Audi A4 Quattro 1996-2006, Audi A4 Avant 1996-2006
- **alternator:** no verified group — Likely tier only. Note: every published alternator row carries Bosch/Valeo vendor qualifiers — all pairs stay Likely
- **starter — verified evidence:** Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5364 — one published starter for Passat 2.8 2000-2005, A4 2.8 2000-2001, A4 3.0 2002-2005, A4 Quattro 2.8 2000-2001 and 3.0 2003-2006 (A4 Quattro 2002 is not published — spans split around it).
  - Group 1: Volkswagen Passat* 2000-2005; Audi A4 2000-2005; Audi A4 Quattro 2000-2001; Audi A4 Quattro 2003-2006

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

## Phase A (2026-10): enthusiast platforms

33 new engine families (Miata NA/NB/NC, RX-7 FD, RX-8, EF+EG Civic, Integra
B18, K20, S2000, Prelude H/F, Supra MK3+MK4 w/ SC300/GS300/IS300, 300ZX Z32,
VQ35HR/VQ37, DSM, Eclipse 2.4/3.0/3.8 + Galant/Lancer, Evo, WRX EJ205,
BMW M52/M54, VW 2.0T, Mustang 4.6-3V/Coyote/SN95-3.8, F-body TPI/LT1/LS1,
Corvette C4-C6+gen5 Camaro SS, Corolla 4A, Celica 3S). All evidence from the
Denso reman + First Time Fit catalog (densoautoparts.com, retrieved
2026-10-22); per-family details in the evidence block above.

### New: starter-verified families

`_STR_VERIFIED` mirrors the alternator table for the starter category. Four
families publish ONLY qualified alternator rows (turbo/vendor/OEM-number
splits) but clean starter spans — nissan-z32, bmw-m54, vw-20t, gm-fbody-lt1
are starter-verified and their alternators honestly stay at Likely. The test
gate is now "≥1 verified group in ANY category", with reachability checked
per category.

### Phase A accuracy-forced exclusions (no verified data / kept out)

- **BRZ / FR-S / 86** — absent from this Denso catalog edition entirely; no
  engine family created (body-part gen windows still apply).
- **BMW E9x N52 (328i 2007+) and E36/E46 3-Series starters** — no unqualified
  rows in this edition; bmw-m52/m54 verified groups ride on M3/Z3/X5/528i
  spans instead.
- **VW VR6 + 1.8T** — every row carries Bosch-vs-Valeo vendor qualifiers;
  no family created. vw-20t covers the 2.0T era via GTI-only spans.
- **Mustang GT500, Corvette C7 (2014+), 300ZX Z31 (84-89), RX-7 FC
  alternators (86-92)** — supercharger-, stamp- or vendor-qualified rows
  only; excluded from verified spans.
- **MR2 1985-1989 (4A-GE), 3000GT, Prelude 1992-1996 (3-way trim split),
  Integra 1994-2001 Type R split, RSX Type-S split, Eclipse/Talon 1990-1998
  trans/turbo starter splits, RX-8 2004 build-date + 2008 gap** — published
  rows exist but every one is qualified; families stay Likely for those
  years (family membership itself remains correct).
- **Lexus "SC 300/400" and "GS 300/400" combined feed rows** (37 vehicles) —
  the feed string doesn't distinguish 2JZ from 1UZ cars; honestly uncovered.
- **Chrysler Laser** — the 84-86 G-body, not a DSM; only Plymouth Laser
  90-94 is in mitsu-dsm.
- **Mitsubishi Lancer Evolution** — the live feed labels every Evo plainly
  "Lancer", so mitsu-evo is currently unreachable from inventory rows. It is
  kept (correct, published spans) for when the feed distinguishes trims;
  plain Lancer 02-04 (4G94 2.0) stays uncovered rather than guessing.

### Body parts by generation (evergreen gen windows)

`_ENTHUSIAST_EVERGREEN_GENS` (junkyard_scraper.py) appends the consensus
evergreen parts to enthusiast entries with per-copy `yr_min`/`yr_max` set to
factory generation boundaries (US model years) — e.g. the `supra` entry
(1979-1998) now carries four window-gated copies of each evergreen, so a
1994 donor ships "fits 1993–1998", never "fits 1979–1998". Single-generation
entries (s2000, rx-8, 350z, gen-split camaro/mustang/wrangler/civic keys)
get ungated copies clipped to the entry range. The body-part finder's
same-model match inherits these windows, so cross-generation false positives
are structurally impossible for these entries. No new cross-model lighting
groups were added: TYC/Depo application catalogs were unreachable this
session (fetch blocked), so lighting interchange stays within same-model
generation windows only.

## Phase B (2026-10): highest-volume commuter platforms

Working down the inventory-weighted gap ranking after Phase A. ~60 new engine
families plus feed-spelling aliases, in six pushed batches. Coverage of the
251,732-vehicle inventory snapshot: 71.9% (end of Phase A) → 83.2%.
All evidence from the Denso reman + First Time Fit catalog
(densoautoparts.com, retrieved 2026-10-22); per-family details in the
evidence block above.

### Phase B triple spot-checks (20 new, random seed 42 over Phase B families)

Every triple hand-checked against the catalog dump: both the seeker's and the
donor's year/engine rows must carry the SAME published part number with no
disqualifying qualifier.

| # | Family | Part | Seeker | Donor | Published # | Result |
|---|--------|------|--------|-------|-------------|--------|
| 1 | gm-lumina31 | alternator | 2001 Chevrolet Lumina | 2001 Chevrolet Lumina | 210-5161 (102A) | PASS — single unqualified 2001 row |
| 2 | gm-atlas-i45 | starter | 2011 Chevrolet Colorado | 2010 Chevrolet Colorado | 280-5394 | PASS — 2.9 + 3.7 rows 2008-2012 both carry it |
| 3 | nissan-qg18 | starter | 2003 Nissan Sentra | 2003 Nissan Sentra | 280-5373 | PASS — three 1.8 CID spellings 2003-2005, one number |
| 4 | hyundai-gencoupe38 | alternator | 2014 Hyundai Genesis Coupe | 2012 Hyundai Genesis Coupe | 210-0713 (130A) | PASS — 3.8 row 2010-2015 unqualified |
| 5 | vw-b5-v6 | starter | 2000 VW Passat 2.8 | 2005 Audi A4 Quattro 3.0 | 280-5364 | PASS — Passat 2.8 2000-2005 + A4 Quattro 3.0 2003-2006 rows |
| 6 | mopar-pacifica | starter | 2005 Chrysler Pacifica | 2005 Chrysler Pacifica | 280-0349 | PASS — 3.5 and 3.8 2005 rows both carry it |
| 7 | mazda-cx9 | alternator | 2009 Mazda CX-9 | 2010 Mazda CX9 (feed spelling) | 210-4321 (110A) | PASS — 3.7 2008-2011 row |
| 8 | hyundai-santafe1 | starter | 2005 Hyundai Santa Fe | 2006 Hyundai Santa Fe | 281-6004 | PASS — 2.4/2.7/3.5 rows all on one number 2005-2006 |
| 9 | lexus-is2 | alternator | 2009 Lexus IS 250 | 2009 Lexus IS 250 | 210-0657 (150A) | PASS — 2006-2009 row unqualified (2010-2013 Base-qualified, excluded) |
| 10 | gm-ecotec-lcv | starter | 2013 Chevrolet Malibu | 2013 Chevrolet Malibu | 280-0434 | PASS — 2.0T + 2.5 2013 rows both carry it |
| 11 | lexus-3uz | alternator | 2005 Lexus LS 430 | 2006 Lexus LS 430 | 210-0570 (130A) | PASS — 3UZFE 2005-2006 row |
| 12 | mazda-mpv30 | alternator | 1991 Mazda MPV | 1993 Mazda MPV | 210-4105 (70A) | PASS — V6-3.0 1989-1998 row |
| 13 | mitsu-4b11 | starter | 2010 Mitsubishi Lancer | 2010 Mitsubishi Lancer | 280-4317 | PASS — 2010 4B11 NA and Evo GSR rows both carry it |
| 14 | honda-b20 | alternator | 1997 Honda CR-V | 1997 Honda CR-V | 210-0196 (95A) | PASS — B20B4 1997-1998 row unqualified |
| 15 | ford-40ohv | alternator | 1992 Ford Explorer | 1992 Ford Explorer | 210-5210 (95A) | PASS — 4.0 1991-1992 row unqualified (93-94 trim-qualified, excluded) |
| 16 | honda-j37 | starter | 2012 Acura MDX | 2012 Acura MDX | 280-0405 | PASS — J37A1 2010-2013 row |
| 17 | nissan-vg30-maxima | alternator | 1990 Nissan Maxima | 1989 Nissan Maxima | 210-3131 (90A) | PASS — VG30E 1989-1991 row unqualified |
| 18 | mopar-lh27 | alternator | 2001 Dodge Intrepid | 2001 Dodge Intrepid | 210-0686 (120A) | PASS — 2.7 1999-2001 row unqualified |
| 19 | hyundai-gencoupe20 | alternator | 2012 Hyundai Genesis Coupe | 2012 Hyundai Genesis Coupe | 211-6017 | PASS — 2.0T 2010-2012 row |
| 20 | mazda-cx7 | alternator | 2007 Mazda CX7 | 2009 Mazda CX-7 | 210-4312 (110A) | PASS — 2.3T 2007-2011 row |

All 20/20 PASS (checked 2026-10-22).

### Phase B accuracy-forced exclusions

Catalog-absent models (no rows at all in this edition — no family created):
Ford Fiesta, Nissan Juke, Fiat 500, Chevrolet Spark, Scion/Subaru BRZ-family.

Catalog year ceiling (~2015) — these high-volume 2016+ clusters cannot be
verified from this edition and stay uncovered: Sentra 2013+ span past 2015,
Fusion 2015+, Pathfinder 2013+ past 2015, Malibu 2016+, Cruze 2016+, Accord
2013+ past 2015, Civic 2016+, Equinox 2018+. 2016+ vehicles are 2.6% of the
inventory snapshot.

Hybrids: Prius (0.5% of inventory) and all other hybrids excluded — HV
systems make alternator/starter interchange inapplicable or dealer-only.

Qualified-row families (published rows exist but every one carries a
disqualifying split — stays Likely or no family):
- Mercedes C/E/S-Class — vendor-mixed (Bosch/Valeo) in every span.
- BMW 3-Series 2007-2017 (N52) — no unqualified rows published.
- Ford Focus 2000-2004 — SOHC/Zetec + transmission splits.
- VW Jetta 1994-2004, Golf 1995-2006, New Beetle/Beetle — vendor and
  transmission qualifiers on every row (Beetle starters all trans-qualified).
- MINI Cooper — supercharged/vendor splits throughout.
- Volvo XC90 and sedans — fragmented vendor/amp splits.
- Ford Freestyle — Rear-A/C option splits on alternator rows.
- Toyota Tercel — transmission and cold-spec qualifiers.
- Mazda B-Series — mixed Ford/Mazda engines per year; no clean span.
- Lexus IS 250/350 2010-2013 alternators — Base-trim-qualified rows only.
- VW Passat 2.0T 2010 starter — Bosch-vendor-qualified (07-09 verified via
  280-5338; 07-10 also dual-listed with 281-6001 — match yours).
