# Data quality workstream — status (opened 2026-11-04)

Owns: make/model normalization in `scraper/junkyard_scraper.py` (and its
tests `test_make_normalization.py`, `test_model_normalization.py`), the
lifespan writer `_write_model_lifespan_json` and `db.model_lifespan_stats`,
`scraper/test_model_lifespan.py`, and the lifespan display in `docs/app.js`
(`lifespanFor`, "leaves fast here", "Day N of ~X").

## Open issues (from the hub, 2026-11-04)

1. **Split model spellings** in `docs/data/model_lifespan.json`:
   "Dodge|Ram", "Dodge|RAM", "Dodge|Ram 1500" counted separately;
   "General Motors|ION" and "General Motors|VUE" should be Saturn. Likely
   more of the same kind across the inventory.
2. **Yards with implausibly long lifespans**: Prestige Pull-Your-Part
   Houston (typical 296 d), San Antonio Pick-N-Pull (233 d), Pick Your Part
   Wichita (181 d), Wrench-A-Part Belton (180 d), Pick-n-Pull Dallas South
   (161 d). Likely feeds that keep departed cars listed, so departures are
   detected late. Global median is 61 d.

## Rules specific to this work

- Saved watches are never rewritten (CLAUDE.md rule 6). Any normalization
  change must keep existing watches matching the same cars (match both
  old and new spellings if needed); add a test for that.
- Do not invent a lifespan. Where a yard's data is unreliable, the app shows
  nothing rather than a number.
