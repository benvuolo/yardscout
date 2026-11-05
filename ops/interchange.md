# Interchange workstream — status (opened 2026-11-05)

Goal (owner, 2026-11-04): car-part.com-level cross-compatibility, accuracy
first. Owner approved multi-agent ("ultra") scale.

## Decision record

- car-part.com is Hollander Interchange (licensed, proprietary). Its
  robots.txt blocks its search (/cgi-bin) and /Services/Hollander. Not
  scraped, not reverse-engineered. Licensing Hollander remains an owner
  option (quote-based).
- Verified interchange = the carmaker's own catalog lists both vehicles
  under one OEM part number (or a stated supersession).
- Sources that pass rule 2 (robots allows the pages, no bot check, no
  anti-scraping terms found): the SimplePart/PartsGiant dealer catalogs
  listed in `scraper/oem_fitment/fetch.py` ALLOWED. Refused or out:
  gmpartsdirect.com, parts.nissanusa.com, store.mopar.com,
  hondapartsonline.net (Cloudflare bot check); dormanproducts.com (robots
  blocks all); olathetoyotaparts.com (domain hijacked by spam);
  car-part.com; rockauto.com (not used).
- Coverage ceiling of this source: the 13 catalogs cover 297k of 333k cars
  on the lots (89%). VW, Mazda, Mitsubishi, BMW, Mercedes, Volvo are not
  reachable this way.

## Pipeline

1. `scraper/oem_fitment/fetch.py`: allowlist, robots, 4 s/site, 0.5 s global,
   cache, permanent stop on any bot check/403/429/503.
2. `scraper/oem_fitment/sites/<site>.py`: per-site navigator (written by one
   agent per site, workflow run wf_7d045075-e05, 2026-11-05).
3. `scraper/oem_fitment/crawl.py`: background crawl per site, worklist
   order (cars on lots), tier A categories first, resumable. Raw evidence in
   `raw/<site>.jsonl`.
4. Next (not started): curation into interchange groups with an
   independent adversarial verification per site, then integration into
   `interchange.json` as verified platform groups and engine-family groups.

## Status

- 2026-11-05 00:20 UTC: harness committed (8ea96df); navigator workflow running.
