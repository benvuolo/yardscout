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
2. `scraper/oem_fitment/sites/`: two shared template parsers
   (`_partsgiant.py` for the .html catalogs, `_simplepart.py` for Toyota and
   Jeep) plus a thin module per site.
3. `.github/workflows/oem-fitment-crawl.yml`: one Actions job per site with a
   module, `crawl.py` in 30-minute slices, checkpoints committed to the
   `oem-raw` branch (`raw/<site>.jsonl` etc.). Worklist order (cars on lots),
   tier A categories first. Runs every 6 h until each site is done.
4. Next (not started): curation into interchange groups with an
   independent adversarial verification per site, then integration into
   `interchange.json` as verified platform groups and engine-family groups.

## Status

- 2026-11-05 00:05 UTC: harness committed (8ea96df).
- 00:11 UTC: container restart killed the in-session navigator workflow
  (wf_7d045075-e05) a few minutes in; nothing lost but cached pages. Moved
  crawls to GitHub Actions (9203003) and navigator builds to two sessions:
  - session_016ZzJfK5C7Cm4qZpC4QjSVs: .html template + GM, Ford, Mopar,
    Nissan, Infiniti
  - session_016ZzJfHbzhf7ZAm4Xt8ok79: SimplePart template + Toyota, Jeep
  - pending: Honda, Acura, Hyundai, Kia, Subaru, Lexus on the .html
    template once it lands.
