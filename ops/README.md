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
- same-engine relabel + Honda/Nissan: session_016ZzJfK5RFgko9f1gx7qjEa
- wheels: session_016ZzJfL4wG1wgpyYymW2Z28
- make breadth + Subaru: session_016ZzJfKqBWhtUcqYMMseVgn
- category breadth + coverage matrix: session_016ZzJfKdkBXaVYDDQb9cy2J
Shared oem_fitment code: pull --rebase, run curation_tests + tests before
every push. One crawl run at a time. Nothing ships to users without a §11.4
sample with 0 WRONG and the hub's confirmation.
