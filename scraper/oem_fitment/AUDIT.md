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
| 01:24 | www.toyotapartsnow.com | 363 | 0 | 0 | 0 | 0 | 0.0% |

Toyota 01:24: the first heuristic pass raised 21 C hits. All 21 were wrong
heuristics, now fixed in the auditor. Toyota names the tail-lamp assembly
"Lens & Body, Rear Combination Lamp" or "Lens & Housing" (8155x/8156x), and
the power-steering pump "Pump Assy, Vane" (44310-...). "Body Assembly,
Throttle W/Throttle Position Sensor" is a throttle body.

## Findings needing a module change (proposed to the hub, not applied)

Pre-crawl sample: 38 records from a local 2-segment tier A trial on Mopar (10),
Nissan (13) and Infiniti (15). The trial was stopped at the hub's request
because Actions is crawling these sites.
- Field-by-field against the cached page text (rendered table and store):
  38/38 match.
- Against evidence_lines: 0 E.

1. **Mopar headlights keeps a bulb kit.** LBK13001, list
   `parts-list/2002-dodge-ram_1500/electrical/lamps_front.html`. Group "LAMP
   Headlamp Park And Turn", list info "Light Bulb Kit (Assorted Bulbs and
   Fuses)". The Mopar PARTS excludes run on the head
   (group|main|remark), not on info.
   Fix: add `r"Bulb Kit|Assorted Bulbs"` as the third (full-text) exclude on
   Mopar `headlights` and `tail-lights`.

## Tier B rule review (fetch.py; at most 20 requests per site, 10 s apart)

Requests used: Mopar 5, Nissan 12, Infiniti 7. Year pages already in the local
cache were read for free. Subcategory regexes match only the last URL segment
(`categories_for` uses `tail`).

### moparpartsgiant.py

Navigation was checked offline on six year pages (2002 Ram 1500, 2010 Grand
Caravan, 2015 200, 2012 Journey, 2006 300, 2012 Ram 1500):

| # | category | problem | evidence | proposed fix |
|---|---|---|---|---|
| M1 | door-front, door-rear | 2002 Ram 1500 and 2006 300 get no door-shell page: their slugs are `doors_related_parts/door_front_shell_hinges` and `door_rear_shell_hinges`, which `front_door_shell\|door_shell` does not match | 2002 Ram page lists "DOOR Front" Right/Left (55276054AB/55AB) | SUBCATS door-front `...\|door_front_shell`, door-rear `...\|door_rear_shell` |
| M2 | fender | 2015 200's fender page is `front_fenders_shields`; SUBCAT_EXCL `shield` drops it | page has "FENDER Front" 68143656AA/57AA | drop the fender SUBCAT_EXCL `shield` (COMMON_EXCLUDE and the fender rule already drop SHIELD rows); costs one extra page where a shield-only page exists |
| M3 | ignition-coils | 2002 Ram 1500 and 2006 300 coil page is `spark_plugs_cables_coils`; `ignition` does not match | 2006 300 page has "COIL Ignition" 4606869AA | SUBCATS ignition-coils `ignition\|coils?$` |
| M4 | trunk-lid | "PANEL Deck Lid Opening" (5065744AD, 2006 300 `decklid_liftgate_panel`) is kept: it is a rear body panel, not the lid | list row on that page | add `Opening` to trunk-lid excludes |
| M5 | hood, grille | accessory pages (`mopar_accessories_component_parts/hood`, `/grille_kit`) are read; "HOOD KIT Vehicle" 82211065AD (2012 Ram 1500) is kept as a hood | list row | add `KIT` to the hood and grille excludes (the accessory page carries no factory hood); a path-level exclude for `mopar_accessories_*` would need an additive template option |
| M6 | liftgate | `decklid_liftgate_panel` (Chrysler 300 / Dodge Magnum layout) is routed only to trunk-lid, so a Magnum liftgate would be missed | slug seen on 2006 300; Magnum not fetched | liftgate SUBCATS `...\|decklid_liftgate` |
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
| I1 | gauge-cluster | the 2003-2007 G35 cluster rows are named "Meter Assy-Analog" (24820-AC700/701/705/706); the rule keeps nothing on that page | product page 24820-AC700: mainDesc "Meter Assembly", site pdName "Instrument Cluster", fits 2004-2006 Infiniti G35 Sport/Track | add `^Meter Assy-Analog` to `nissanpartsdeal.PARTS["gauge-cluster"]` include (shared). Do not add "Meter Assy-Temperature" (the F/COMPASS gauge) |

### gmpartsgiant.py, fordpartsgiant.py

Not reviewed yet (next, within the same budget).
