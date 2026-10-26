# Compare-combobox alias layer — what shipped, what was left, and why

*2026-10-26, jh-v71 (`fix(web): compare combobox merges chains' raw price-sheet
spellings into canonical parts`). Companion code: `docs/app.js` (CANONICAL
PART-NAME MERGING block), validator: `tools/check_part_aliases.py`, prod
check: `tools/_verify_compare_aliases_prod.py`.*

## What shipped

Measured over the 25 wired pricing sources (~7,192 usable raw names) at ship
time — rerun `tools/check_part_aliases.py` for current numbers:

| layer | entries |
|---|---|
| old `partMergeKey` (punctuation + plural only) | 6,568 |
| token-normalizing `partMergeKey` (word order, fillers, chain abbreviations, closed-up compounds, lamp=light) | 6,014 |
| + 5 curated `PART_ALIAS_GROUPS` (airbox, air cleaner lid, alternator, MAF sensor, hood prop rod) | **5,996** |

517 fragment clusters unified mechanically; 764 final entries carry 2+ raw
spellings. The audit reviewed every unified cluster; 3 token-set collisions
are blocklisted in `PART_NEVER_MERGE` ('back seat back', pnpsa's
'motor - seat without tracks' and 'motor - window without regulator').

## Judgment calls made (conservative doctrine: same physical part only)

- **Merged**: Lg/Sm/round/carb/plastic/steel/aftermarket variants of the
  airbox — one physical part category, the yard's own raw spelling stays on
  its compare row. Same for grille/console/emblem SIZE spellings only where
  the size token matched exactly (mechanical), never across sizes.
- **Merged**: lamp = light vocabulary (headlamp/headlight, tail lamp/tail
  light, fog lamp/fog light, parking lamp/light, license plate lamp/light).
  Every surveyed list uses them interchangeably for the same hardware.
- **NOT merged**: air cleaner BASE, HALF, HOSE, TUBE(s), RESONATOR, FILTER —
  adjacent but distinct items on the lists that carry them. LID/TOP became
  their own canonical entry, separate from the housing.
- **NOT merged**: hybrid alternators ('alternator hybrid', 'hybrid
  alternator' merged with each other mechanically, but kept separate from
  'Alternator') — genuinely different unit, different price tier.
- **NOT merged**: starter (diesel) vs starter; material-variant pans/covers
  (oil pan steel vs aluminum, valve cover aluminum vs plastic) — same part
  family, but a given car takes one or the other and yards price them
  differently, so cross-material unification would misquote.

## Left for a future pass (fragmentation that is REAL but unresolved)

1. **Battery** (~40 spellings across 24 chains): used/recycled/refreshed/
   reconditioned/reman/15-month/premium/standard/dealership are warranty and
   condition TIERS, not spellings. Unifying them into 'Battery (used)' with
   the raw tier shown per row is probably right, but needs an owner call on
   whether tier differences belong in one compare sheet. Hybrid battery rows
   are already consistent (mechanical).
2. **Engine block long/short/bare**: three real configurations; the finder's
   'Engine assembly' category quotes the assembly tokens. A curated
   'Engine block' group per configuration would add 3 canonical entries over
   ~9 raw spellings. Low urgency — spellings within each configuration
   already merged mechanically.
3. **Console size ladder** (ace's sm/med/large/xlarge vs others' short/long/
   36+"): size tokens differ per chain vocabulary ('med' vs 'short'?) —
   ambiguous mapping, left fragmented. The generic 'Console' entry already
   covers 11 chains.
4. **Seat taxonomy** (bucket/bench/section/rear/3rd row/track variants): the
   finder's front-seats and 3rd-row categories plus PART_KEYWORD_MAP already
   canonicalize the common asks; full unification needs the P1 seat
   categories from PART_CATALOG_SPEC §3.
5. **'Air cleaner - half'** (budget): ambiguous (half the housing?) —
   excluded from the airbox group on purpose.
6. **Compound-word residue**: the ABBR table folds the compounds actually
   observed (sparkplug, clockspring, oilpan...). New lists can introduce new
   ones; the validator's multi-spelling stats make them findable. Mechanical
   discovery script pattern lives in this commit's history (super-key
   clustering in the audit).

## Maintenance

- `tools/check_part_aliases.py` exits 1 when a curated raw name or
  blocklisted name disappears from the live lists (scraper drift) or two
  alias groups claim one merge key. Run it whenever pricing scrapers change.
- `partMergeKey` is mirrored in that validator — keep both in sync.
- New curated groups: canon must equal the finder category label where one
  exists (one-taxonomy rule, PART_CATALOG_SPEC §6); raw names verbatim from
  the lists; quoting is exact-tier by construction, so a group can never
  substring-sweep a wrong row.
