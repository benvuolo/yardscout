# Where YardScout came from — the record (private; not for public claims)

Kept by the hub at the owner's request (2026-11-20: "I had a cursor agent
(on this local machine) that started the roots of this ... Should we find
and acredit that?"; then three files, "Here are all the old files! From
march"). Facts and dates only. **Nothing here supports saying YardScout was
first; do not say or imply it anywhere** (see `ops/hub.md`, 2026-11-17 14:27
UTC: the other site's domain was registered 2026-03-19 and a working copy
was archived 2026-05-01).

## The owner's account

Before this repository existed, the owner had an agent in the Cursor editor
on their own computer pull the inventories of the self-service yards near
them (Salt Lake City area) into local files. This repository's history
starts 2026-09-02 as "Junkyard Hunter" and was renamed YardScout 2026-09-09.

## The three files the owner uploaded on 2026-11-20

The uploads are copies, so their file dates are the upload time; what dates
them is the data inside. The files are NOT in this repository (they are
other parties' inventory data; one is from Row52, which is out of scope by
standing rule 7, and nothing from them is used). Fingerprints, so the
owner's originals can be matched later:

| File | Size | sha256 | What it holds | Dates inside |
|---|---|---|---|---|
| `tearapart_inventory.json` | 1,149,882 bytes | `0ab180fc791f41d297e21ebade73c20bd7158e10a7f407b50e1c27c61343dfc8` | 1,188 cars from the yard's own inventory feed: Tear A Part Salt Lake City 613, Tear-A-Part Ogden 575 | every record's `lastupdate` is 03/22/2026 (02:00 AM Ogden, 07:00 PM Salt Lake City); newest `yard_date` 2026-03-20 at both yards |
| `inventory_data.json` | 1,887,920 bytes | `5bc31f90aeace8f63dff2565dd144bbe5ec3d4fefff4e534424374332c2f58e1` | 1,002 cars at Pick-n-Pull Salt Lake City, in Row52's record format | newest `dateAdded` 2026-03-20 (13 cars that day, 14 on 03-19, 17 on 03-18); newest `creationDate` 2026-03-20 07:20 UTC |
| `scraper_err.log` | 0 bytes | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | empty | none |

## What this shows, and what it does not

- The data in both inventory files was current as of 2026-03-20 to
  2026-03-22: it cannot have been downloaded before those dates, and since
  both sources change daily it was most likely downloaded on them.
- So the owner was collecting the inventories of three Utah self-service
  yards within days of 2026-03-19, the day the other site's domain was
  registered, and weeks before any public copy of that site is recorded
  (2026-05-01). That fits two people starting on the same idea at the same
  time, each without knowing of the other.
- It does not show who started first, and it does not date the owner's
  code: no script, chat or original file date is in what was uploaded.

## Stronger evidence, on the owner's computer (leave it untouched)

The original files' created and modified dates; the folder they sit in and
the script that wrote them; the Cursor chat history for that folder; any
early local git history. If the owner sends those dates or shares the
folder with a session, add them here.
