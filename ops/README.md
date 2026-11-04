# Operations — workstreams

One Claude session per workstream. Each session reads its file first, works
only in its files, and updates its file before stopping (what changed, what
is blocked, what is next). The owner's standing rules are in `/CLAUDE.md`.

| Workstream | File | Owns | Starts when |
|---|---|---|---|
| Ops hub | `ops/hub.md` | releases, daily ops email, scheduled watches, owner questions | always open |
| Parts | `ops/parts.md` | parts tables, gap curation, parts tests | "most searched" data or owner ask |
| eBay pricing | `ops/ebay.md` | `ebay_prices.py`, bands, calibration | eBay keys exist, or Terapeak list arrives |
| Yards | `ops/yards.md` | adapters, coverage sweep, outreach, registry | a reply, a new yard, or the monthly sweep |
| Release | `ops/release.md` | version bump, build, store submission | owner says "ship" |

Brief for a new session (paste as the first message):

> Read `/CLAUDE.md` and `ops/<file>`. Work only that workstream. Update
> `ops/<file>` and push before you stop.
