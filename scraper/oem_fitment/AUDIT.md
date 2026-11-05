# OEM fitment raw-output audit

Auditor: session_016ZzJfLtcR8MerD7PWDQVoN (hub request 2026-11-05 01:14 UTC).
Re-run at each `oem-raw` checkpoint for ~2 h.

## Method

Every record in `raw/<site>.jsonl` from the `oem-raw` branch is checked offline
(no network, no cache) against its own `evidence_lines`. The evidence is
re-parsed by an independent parser, not by `sites/_partsgiant.py` or
`sites/_simplepart.py`.

- **E, evidence mismatch** (counted in the rate): pn (PartsGiant: the
  "Part Number:" line; SimplePart: the product URL, unless flagged
  `pn_differs_from_url`), description (PartsGiant), position (must be the
  printed Position line or the printed list-row side; empty only when
  flagged as a conflict), replaces, replaced_by, and every fitment entry:
  years (must be one printed span), year_spans, make, model, trims, engines,
  options (PartsGiant), with one entry per printed span. The fitment cells
  must equal the evidence rows exactly, in order. When evidence is flagged
  truncated, only rows missing from fitment count.
  Per-site convention: on GM and Mopar `trims` = the option column when there
  is no Trim column.
- **C, category suspect** (counted in the rate): the name/description lacks
  the category's word, or the name, list info or remark carries a junk word
  (bulb, socket, bracket, bolt, lens, clutch, glass ... per category).
  This is a heuristic, so every C hit is read by hand before it is reported.
- **D, duplicate** (category + pn twice) and **F, fitment suspect** (empty
  fitment without a flag, years outside 1940-2027, the seed vehicle-year not
  in its own part's fitment) are listed for curators. They are not counted.

The auditor was mutation-tested before use. Each of these single-field
corruptions was caught in every record: years, make, model, trims, engines,
dropped row, replaces, replaced_by, position, pn. PartsGiant: 38/38 records;
SimplePart: 363/363.

## Results by checkpoint

| UTC | site | records | E | C | D | F | mismatch rate |
|---|---|---|---|---|---|---|---|
| 01:23 | www.toyotapartsnow.com | 363 | 0 | 0 | 0 | 0 | 0.0% |
| 01:25 | www.jeeppartsdeal.com | 385 | 0 | 1 | 0 | 0 | 0.26% |
| 01:43 | www.fordpartsgiant.com | 359 | 0 | 0 | 0 | 0 | 0.0% |
| ~01:45 | www.nissanpartsdeal.com | 332 | 0 | 0 | 0 | 0 | 0.0% |
| ~01:45 | www.infinitipartsdeal.com | 355 | 0 | 0 | 0 | 0 | 0.0% |
| ~01:45 | www.dbelectrical.com (aftermarket) | 363 | 0 | 0 | 0 | 0 | 0.0% |

### Checkpoint audit ~02:05 UTC (all sites on oem-raw)

Category hits are a heuristic; "real" is the count left after reading every
hit by hand.

| site | records | E | C (heuristic) | C real | D | F |
|---|---|---|---|---|---|---|
| toyotapartsnow | 757 | 0 | 14 | 0 (2 records + policy question T1) | 0 | 0 |
| jeeppartsdeal | 748 | 0 | 1 | 1 (5143152AA, exclude list) | 0 | 0 |
| gmpartsgiant | 453 | 0 | 104 | 0 | 0 | 0 |
| fordpartsgiant | 654 | 0 | 2 | 0 | 0 | 3 |
| moparpartsgiant | 759 | 0 | 2 | 1 (LBK13001, exclude list) | 0 | 3 |
| nissanpartsdeal | 707 | 0 | 0 | 0 | 0 | 0 |
| infinitipartsdeal | 645 | 0 | 0 | 0 | 0 | 0 |
| hondapartsnow | 244 | 0 | 0 | 0 | 0 | 0 |
| acurapartswarehouse | 224 | 0 | 1 | 0 | 0 | 0 |
| hyundaipartsdeal | 355 | 0 | 99 | 0 (+ policy question P1) | 0 | 0 |
| kiapartsnow | 349 | 0 | 136 | 0 (+ policy question P1) | 0 | 0 |
| subarupartsdeal | 330 | 0 | 37 | 0 | 0 | 0 |
| lexuspartsnow | 392 | 0 | 6 | 0 | 0 | 0 |
| bmwpartsdeal | 297 | 0 | 134 | 0 | 0 | 0 |
| vwpartsgiant | 298 | 0 | 14 | 0 | 0 | 0 |
| mitsubishipartsgiant | 242 | 0 | 7 | 0 | 0 | 0 |
| dbelectrical (aftermarket) | 630 | 0 | 0 | 0 | 0 | 0 |

Later checkpoints: DB Electrical 02:41 (726 records) and 03:09 (799): 0 E,
0 C, 0 F. As of 03:12 the dealer-site files are unchanged since ~02:05.
03:14 checkpoints: Acura 334 records (0 E; 2 C, both correct: 34156-SEC-A51
is the TSX deck-lid tail lamp "Lamp Unit, L."; 06388-P5A-505RM is a reman
compressor "(RMD) (INCLUDES CLUTCH & COIL)", kept because the page lists no
new number). Jeep 912 records (0 E; the only C is 5143152AA, already on the
exclude list).
03:18-03:20 checkpoints: BMW 458, GM 554, Honda 384, Infiniti 819 records;
0 E. The 128 new C hits (BMW 86, GM 42) repeat patterns already read and
judged correct: BMW headlights that "do not contain" covers or modules,
mirrors "w/o glass", trunk-lid/side-panel tail lamps, "Drive for window
lifter"; GM "(INCLUDES n-m)" assemblies, "DOOR LOCK & SIDE WINDOW" switches.
Real C: 0.
03:23-03:26 checkpoints: Hyundai 582, Ford 866, Jeep 959 records; 0 E. The
new C hits are Hyundai fit notes ("O/S RR VIEW MRR LABEL", "SIDE REPEATER
LAMP", "ANTI-FOG", "W/ OIL-SEPARATOR", "LED(W/BULB T/SIGNAL)"), door
modules (P1, hub-decided) and Ford AE8Z-9H307-H "Kit" (base 9H307, "Fuel
Pump/Sending Unit"). Real C: 0.
DB Electrical 03:37: 1136 records, 0 E/C/F. Dealer files unchanged at 03:43.

The auditor's first pass on Honda, Acura and BMW reported 100% E. That was
the auditor: those modules declare `trim_col` ("Body & Trim") and
`option_col` ("Emission & Transmission", "Submodel"), which it now reads from
CFG. One VW E was a rendered double space ("2020-2022,  2012-2015"); the
SimplePart template collapses whitespace on purpose, and the auditor now
does too.

Hits read and found correct: assemblies with their contents spelled out
(GM "(INCLUDES 2-10)", "W/HARNESS", "W/CHROME CAP"; Kia/Hyundai mirrors with
"SIDE REPEATER LAMP" and label notes; Subaru mirrors by paint colour; Lexus
and Kia "level"/levelling headlamps; Subaru "Chamber And Sensor
Assembly-Throttle"; Toyota "Lens&Body, Rear Combination Lamp" short-named
"Lens"; Mitsubishi 8301xxxx "Lens & Housing" headlamps; Ford 23394 "Control
Unit"/"Module" = "Window Operating Motor Assembly"; BMW "Drive for window
lifter", "Tandem pump", "Rear light in trunk lid / side panel").

Policy questions for the hub (not errors):
- **T1, Toyota climate-control sub-assemblies.** The rule keeps "Control
  Sub-Assembly, Heater" (55901/55902/55903) as well as the full control
  assemblies (55900/55910). On Japan-built cars without climate control the
  list notes describe single switch modules: 55903-12100 "Temp Control",
  55901-12170 "Air Mode Control" (name "Temperature Switch"). They are not
  the whole control head. Curators should keep them apart from the full
  assemblies. To drop them, the Toyota rule would exclude sub-assemblies
  whose list note says Temp/Air Mode/Blower Control.
- **P1, door module panels as window regulators.** Hyundai and Kia keep
  "Panel Assy-Front/Rear Door Module" (e.g. 82471-3Q000, Sonata), the panel
  that carries the regulator. The Nissan module drops "Module Assy-Front
  Door" on purpose. The sites should follow one policy.

Scope notes for curators:
- BMW sells "Exterior mirror w/o glass" (51-16-7-268-261/-277) and
  headlights that "do not comprise ignition control unit and Xenon light
  bulb" (63-12-3-418-395/396). A pulled unit can include more than the part
  number covers.
- VW names outside mirrors "Housing Assembly" (1K1-857-507-DH-9B9).
- F hits are list-page parts whose own fitment omits the seed vehicle.
  Ford DG1Z-10346-E and FJ7Z-10346-A came from the 2014 Fusion page but list
  Edge/Taurus/MKC/MKZ only, and HU2Z-10V346-CJRM lists the Fusion but not
  2014. Mopar R5233006 came from the 1990 D150 starter page but lists only
  K-car family Chryslers. The other two Mopar F hits are the auditor
  comparing the feed name "Ram 1500" with the catalog's "D150". Being listed
  on a vehicle's page is not fitment; only the product page's own rows are.

Ford 01:43: the first pass raised 107 category hits, all heuristic. Ford
names are generic ("Lamp Assy", "Sender And Pump Assy"), its list info is
fit notes about contents ("Body and lens", "Includes Clutch (19D786)",
"Does Not Include Bulbs Or Ballast"), and the module decides category by
the engineering base number. The auditor now reads only Ford part names
for junk words. Curator notes:
- A/C compressors come both as "Compressor only" (F7LZ-19703-AA,
  8H6Z-19703-A) and as "New Loaded Compressor Assembly. Includes Clutch,
  Coil, Pulley" (4L3Z-19V703-AB) under different numbers. Do not merge the
  two scopes.
- Fusion/MKZ list "inner" tail lamps (9H6Z-13404-B/-13405-B, "Backup
  Lamp") separately from the outer lamps; both are 13404/13405.

DB Electrical: its own `verify_records.py` re-reads the HTML cache, which
stays on the Actions runner, so `audit.py` checks these records offline. It
checks the item #, every spec line, every application row cell for cell
(YEAR may print as a span "1999 - 2001"), that each row is in exactly one
application_span, the replaces table row for row (a brand can print on
several rows), and that every classified number (oe, service, supplier,
interchange, other, ambiguous) comes from that table. Curator notes:
- 7 records carry `unparsed_application_row` (88 rows). 400-52039--003
  prints the engine in the YEAR column ("DAKOTA | 2.5L(153) L4 | 1997")
  under a MAKE | TYPE | MODEL | YEAR | ENGINE header. The rest are
  tractors, forklifts and race cars with year 0 or blank. Leaving them
  unparsed is correct.
- The FORD replaces row mixes engineering numbers with short forms printed
  on the page ("4L3U-BA", "5L7T-CB") and GL-series numbers (GL579, GL622,
  GL908, Motorcraft service-number shape) printed under FORD, so they land
  in `oe_numbers`. Do not treat the short forms or GL numbers as Ford
  engineering numbers when joining to the dealer track.
- `aftermarket_pn` can carry a variant suffix ("400-52039--003") and is
  then flagged `item_number_differs` (Item # 400-52039).

Junk words are read only in the OEM name, the short name (aux_desc) and the
list-row text. They are not read in the product display name, which carries
option words ("Headlamp Assembly, Black Bezel"), or in `other_names`, which
lists retail synonyms ("HVAC ... Blower Control", "Lens&Body"). These
phrasings were read by hand and are allowed: Mopar "Switch - Window And Door
Lock" (the documented Jeep convention), "Pump - Power Steering With Pulley",
"Module Kit Fuel Pump/Level Unit: Pump, Unit, O-Ring", Toyota "Alternator
Assembly, With Regulator", "Pump Assembly, Fuel With Filter", "Tube Assembly,
Fuel Suction" (77020-*, the in-tank pump/sender module, short name "Fuel Pump
Assembly"), "Pump Assembly, L/Pulley".

Toyota 01:23: the first heuristic pass raised 21 C hits. All 21 were wrong
heuristics, now fixed in the auditor. Toyota names the tail-lamp assembly
"Lens & Body, Rear Combination Lamp" or "Lens & Housing" (8155x/8156x), and
the power-steering pump "Pump Assy, Vane" (44310-...). "Body Assembly,
Throttle W/Throttle Position Sensor" is a throttle body.

## Exclude at curation

Records already crawled that a later rule fix drops. The curation layer drops
them by (site, category, pn).

| site | category | pn | reason |
|---|---|---|---|
| www.moparpartsgiant.com | headlights | LBK13001 | light bulb kit ("Light Bulb Kit (Assorted Bulbs and Fuses)"), not a headlamp; rule fixed in the Mopar fixes commit |
| www.jeeppartsdeal.com | headlights | 5143152AA | headlamp boot / bulb cap ("Boot, Front"), not a headlamp; rule fixed in the Jeep/GM fixes commit |

## Applied fixes (hub go 01:28 UTC)

(1), M1-M6 (moparpartsgiant.py) and I1 (nissanpartsdeal.py, shared with
Infiniti) are applied in the site modules only; no template change. Each has
a pure regression check in the site's test, and those checks fail on the old
modules. A before/after parse of every cached year page and list page for
Mopar (700 selections), Nissan (875) and Infiniti (275) changed only these
items:
- parts dropped: LBK13001 (headlights), 5065744AD (trunk-lid), 82211065AD (hood)
- parts added: 24820-AC700/701/705/706 (G35 gauge-cluster)
- pages added: 2002 Ram 1500 and 2006 300 door_front_shell_hinges
  (door-front) and door_rear_shell_hinges (door-rear),
  spark_plugs_cables_coils (ignition-coils), 2006 300 decklid_liftgate_panel
  (liftgate), 2015 200 front_fenders_shields and 2010 Grand Caravan
  front_fender_shields (fender).

The new pages yield the right parts: DOOR Front 55276054AB/55AB, FENDER
Front 68143656AA/57AA, COIL Ignition 4606869AA. The 300 sedan decklid page
gives no liftgate (correct) and still gives DECKLID 5134207AD.

Second batch (hub go 01:36 UTC): Jeep `boot` (0) and GM G1-G3, same
conditions.
- GM, before/after on 175 cached selections:
  - 2012 Equinox gauge-cluster: + instrument_panel, - luggage_carrier.
  - ignition-coils: + engine_assembly_cylinder_head_related_parts on the
    Equinox, 2000 Silverado 2wd/4wd and 2008 Impala. On the last two it is
    an extra fetch; duplicate pns are deduplicated by crawl.py.
  - 2000 Silverado door-front: + door_hardware_side_front (and its _lh/_rh
    variants); door-rear: + door_hardware_side_rear.
  - No part list changed.
- Jeep: one fetch (2005 Grand Cherokee headlamp-components). Before/after,
  only 5143152AA drops; the six headlamp assemblies stay.
- The regression checks fail on the old modules; all tests pass.

## Findings needing a module change

0. **(applied)** **Jeep headlights keeps a headlamp boot.** 5143152AA, list
   `parts-list/2005-jeep-grand-cherokee/headlights-lighting/headlamp-components`.
   OEM name "Headlamp", short name "Boot", product page "Boot, Front" /
   "Headlight Bulb Cap, Front". The jeeppartsdeal `headlights` exclude has
   cover/cap but not boot. Fix: add `boot` to that exclude (the Mopar module
   already excludes Boot).


Pre-crawl sample: 38 records from a local 2-segment tier A trial on Mopar (10),
Nissan (13) and Infiniti (15). The trial was stopped at the hub's request
because Actions is crawling these sites.
- Field-by-field against the cached page text (rendered table and store):
  38/38 match.
- Against evidence_lines: 0 E.

1. **(applied)** **Mopar headlights keeps a bulb kit.** LBK13001, list
   `parts-list/2002-dodge-ram_1500/electrical/lamps_front.html`. Group "LAMP
   Headlamp Park And Turn", list info "Light Bulb Kit (Assorted Bulbs and
   Fuses)". The Mopar PARTS excludes run on the head
   (group|main|remark), not on info.
   Fix: add `r"Bulb Kit|Assorted Bulbs"` as the third (full-text) exclude on
   Mopar `headlights` and `tail-lights`.

## Tier B rule review (fetch.py; at most 20 requests per site, 10 s apart)

Requests used: Mopar 5, Nissan 12, Infiniti 7, GM 10, Ford 6. Year pages already in the local
cache were read for free. Subcategory regexes match only the last URL segment
(`categories_for` uses `tail`).

### moparpartsgiant.py

Navigation was checked offline on six year pages (2002 Ram 1500, 2010 Grand
Caravan, 2015 200, 2012 Journey, 2006 300, 2012 Ram 1500):

| # | category | problem | evidence | proposed fix |
|---|---|---|---|---|
| M1 (applied) | door-front, door-rear | 2002 Ram 1500 and 2006 300 get no door-shell page: their slugs are `doors_related_parts/door_front_shell_hinges` and `door_rear_shell_hinges`, which `front_door_shell\|door_shell` does not match | 2002 Ram page lists "DOOR Front" Right/Left (55276054AB/55AB) | SUBCATS door-front `...\|door_front_shell`, door-rear `...\|door_rear_shell` |
| M2 (applied) | fender | 2015 200's fender page is `front_fenders_shields`; SUBCAT_EXCL `shield` drops it | page has "FENDER Front" 68143656AA/57AA | drop the fender SUBCAT_EXCL `shield` (COMMON_EXCLUDE and the fender rule already drop SHIELD rows); costs one extra page where a shield-only page exists |
| M3 (applied) | ignition-coils | 2002 Ram 1500 and 2006 300 coil page is `spark_plugs_cables_coils`; `ignition` does not match | 2006 300 page has "COIL Ignition" 4606869AA | SUBCATS ignition-coils `ignition\|coils?$` |
| M4 (applied) | trunk-lid | "PANEL Deck Lid Opening" (5065744AD, 2006 300 `decklid_liftgate_panel`) is kept: it is a rear body panel, not the lid | list row on that page | add `Opening` to trunk-lid excludes |
| M5 (applied) | hood, grille | accessory pages (`mopar_accessories_component_parts/hood`, `/grille_kit`) are read; "HOOD KIT Vehicle" 82211065AD (2012 Ram 1500) is kept as a hood | list row | add `KIT` to the hood and grille excludes (the accessory page carries no factory hood); a path-level exclude for `mopar_accessories_*` would need an additive template option |
| M6 (applied) | liftgate | `decklid_liftgate_panel` (Chrysler 300 / Dodge Magnum layout) is routed only to trunk-lid, so a Magnum liftgate would be missed | slug seen on 2006 300; Magnum not fetched | liftgate SUBCATS `...\|decklid_liftgate` |
| - | door-front | 2002 Ram quad-cab "DOOR Front" rows (55275852AC/53AC) have no product link on the list page, so the template skips them (correct: nothing to fetch) | list page | none; note for curators |

The other tier B regexes found the right pages: hood, bumpers (fascia_front/
rear, bumper_front/rear), grille (exterior_ornamentation/grille,
cooling/grille_related_parts), gauge-cluster, radiator (part rule drops
support/closure), tailgate (Ram), liftgate (Journey, Grand Caravan).

### nissanpartsdeal.py

Navigation was checked offline on the 2004 Xterra, 2013 Rogue and 2006 Sentra
year pages, plus one fetch for the 2005 Frontier. Every tier B category finds
its page. Part rules were checked on 10 Rogue 2013 pages and the 2005
Frontier rear gate: they keep "Door Assy-Back" (3), "Door Assy-Front, LH/RH",
"Hood", "Fender-Front, LH/RH", "Fascia-Front Bumper" (2),
"Fascia-Rear Bumper" (2), "Grille Assy-Front" (3),
"Combination Meter Assy-Instrument" (3), "Coil Assy-Ignition",
"Radiator Assy" and "Gate Assy-Rear" (2). They drop glass, panels, sash,
tape, armature, bumper grille, housing, air guides and gate hardware.

| # | category | note | proposed fix |
|---|---|---|---|
| N1 | radiator | "Core Assy-Radiator" 21411-ES60C (2013 Rogue) is not kept, next to "Radiator Assy" 21400-JM00A | none: a core is a service part; no basis that a core is what a puller removes |
| N2 | tailgate | `rear_body` also loads three unrelated bed pages per truck (floor, front panel guard, side gate); the part rule drops them | efficiency only: `rear_gate` instead of `rear_body` |

### infinitipartsdeal.py (Nissan rules)

The 2004 G35 coupe was checked on 6 pages plus 1 product page. Kept as
expected: "Lid-Trunk" (4), "Door Assy-Front, LH/RH" (4), "Fascia
Kit-Front Bumper" (4), "Grille Assy-Front" (3), "Hood" (4).

| # | category | problem | evidence | proposed fix |
|---|---|---|---|---|
| I1 (applied) | gauge-cluster | the 2003-2007 G35 cluster rows are named "Meter Assy-Analog" (24820-AC700/701/705/706); the rule keeps nothing on that page | product page 24820-AC700: mainDesc "Meter Assembly", site pdName "Instrument Cluster", fits 2004-2006 Infiniti G35 Sport/Track | add `^Meter Assy-Analog` to `nissanpartsdeal.PARTS["gauge-cluster"]` include (shared). Do not add "Meter Assy-Temperature" (the F/COMPASS gauge) |

### gmpartsgiant.py

Navigation was checked with the module's own `categories_for` on the 2000
Silverado 1500, 2012 Equinox and 2008 Impala (the author checked the 2012
Malibu). Requests used: 10.

| # | category | problem | evidence | proposed fix |
|---|---|---|---|---|
| G1 (applied) | gauge-cluster | the 2012 Equinox cluster page is `windshield_wiper_mirrors_instrument_panel_console_doors/instrument_panel`, which is not selected; the only page selected is `luggage_carrier` ("gage" matches inside "lugGAGE") | instrument_panel page: the rule keeps "CLUSTER, Instrument Panel Gage" 20907579/80/81/82 once read | SUBCATS gauge-cluster: add `instrument_panel$`; change `gage` to `(^\|_)gage` |
| G2 (applied) | ignition-coils | the 2012 Equinox coils are on `engine/engine_assembly_cylinder_head_related_parts`; nothing is selected | page: "COIL, Ignition Coil" 12632479, 12638824 kept by the rule | SUBCATS ignition-coils: add `cylinder_head_related` |
| G3 (applied) | door-front, door-rear | the 2000 Silverado door pages are `door_hardware_side_front` / `_side_rear`; nothing is selected | page: "DOOR, Front and Rear Side Door" 15017223 kept by the door-front rule | SUBCATS door-front `...\|door_hardware_side_front`, door-rear `...\|door_hardware_side_rear` |

Impala 2008 and Equinox 2012 otherwise select the expected pages (hood,
fender_wheelhouse_front_end, bumper_front/rear, grille_radiator,
radiator_assembly, liftgate_hardware, rear_compartment_*). The 2000 Silverado
tailgate loads 5+ pickup_box pages (efficiency only).

### fordpartsgiant.py

Navigation was checked on the 2004 F-150 and 2008 Escape: every tier B
category selects its page. Ford rules key on the base part number, so names
don't matter. Spot checks: the 2004 F-150 tailgate page keeps "Tailgate Asy"
4L3Z-9940700-AA / 4L3Z-8340700-AA and drops cables, liners and
"Box Assy - Pick Up"; the radiator page keeps "Radiator Assy" 4L3Z-8005-BB.
Requests used: 6. No change proposed.
