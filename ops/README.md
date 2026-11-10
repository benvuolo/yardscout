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
| Data quality | `ops/data.md` | normalization, lifespan data and its display | owner ask |
| Interchange | `ops/interchange.md` | OEM-fitment crawl, curation, verified interchange | running (hub-orchestrated workflows) |
| Release | `ops/release.md` | version bump, build, store submission | owner says "ship" |
| Design | `ops/design.md` | redesign exploration (branch `design/redesign-2026-11`), prototypes, review artifact; no production files until the owner approves a direction | owner ask |

Brief for a new session (paste as the first message):

> Read `/CLAUDE.md` and `ops/<file>`. Work only that workstream. Update
> `ops/<file>` and push before you stop.

Temporary exception (2026-11-05, owner asked for full speed): two Parts
sessions run at once. The model-block session writes PARTS_GAPS §22 and the
facelift session §23, each with its own comment group in FACELIFT_BREAKS; both
pull --rebase and rerun the parts tests before every push.

Temporary exception (2026-11-09, owner: "we're going for breadth here and
data quality … We will create the better version, with no external or third
party costs"). Four Interchange sessions run at once, each in its own
section of ops/interchange.md:
- Honda/Acura + Nissan/Infiniti (R3 completion): session_016ZzJfMtLKpUFu8TiEFMrkF
  (replaces session_016ZzJfK5RFgko9f1gx7qjEa, which had no push access; the
  hub lands its same-engine relabel)
- wheels: session_016ZzJfKi8ND3Ey2g66qhiZT, branch interchange/wheels
  (replaces session_016ZzJfL4wG1wgpyYymW2Z28, no push access)
- make breadth + Subaru: session_016ZzJfKqBWhtUcqYMMseVgn
- category breadth + coverage matrix: session_016ZzJfHdWViThcgyPbNG4i7 (tier C;
  continues session_016ZzJfKdkBXaVYDDQb9cy2J from its §8 handover)
- aftermarket application catalogs (Depo, Cardone/ACI, Spectra, Four
  Seasons): session_016ZzJfMnemMEFN88kPnYgxs
- source scout 2 (strut/suspension makers, OE-brand retail catalogs):
  session_016ZzJfKZ49mzzQhu4KT7HkU
Shared oem_fitment code: pull --rebase, run curation_tests + tests before
every push. One crawl run at a time. Nothing ships to users without a §11.4
sample with 0 WRONG and the hub's confirmation.

Standing rule (2026-11-09, after a near-miss): any change to the hashed
curation inputs (scraper/oem_fitment curate.py, policy.py, notes.py,
positions.py, markers.py, model_map.json, release_allowlist.json) ships in
the SAME push as re-curated groups/<ns>.json for every shipped namespace,
with an identical-or-explained diff. Otherwise the next scan's V8 check drops
every OEM namespace from users. A test enforces it.


| Interchange: wiper-motor curation (tier C) | session_016ZzJfKQPmCKfP14gyJpp6a | started 2026-11-10 12:40 from category-breadth handover (§10); pushes only on hub go (Lexus chassis gate may be in flight) |
