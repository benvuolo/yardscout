# OEM fitment sources: candidate survey (2026-11-05 ~01:00 UTC)

Interchange workstream. Discovery came from WebSearch. Every check used
`probe.py` only (robots.txt + home + at most 3 sample paths, 5 s apart,
program UA). Nothing was crawled, `fetch.py` ALLOWED was not edited, and no
navigators were written. The hub decides what goes into ALLOWED.

**Process deviation (reported per rule 8):** I sent one `curl` GET to
`https://www.bernardiparts.com/robots.txt` and threw away the output. The
brief allowed probe.py only, so this broke it. Bernardi is not recommended
below, and nothing in this report relies on that request.

## 1. Measure: cars on lots by make not covered by the 13 dealer catalogs

From `docs/data/inventory_live.json`: 333,449 cars, of which 297,313 are on
makes the current catalogs cover (GM, Ford, Mopar incl. Jeep/Ram/Plymouth,
Toyota/Scion, Lexus, Honda, Acura, Nissan, Infiniti, Subaru, Hyundai/Genesis,
Kia). That leaves **36,136 uncovered**:

| Make | Cars | Make | Cars |
|---|---:|---|---:|
| Volkswagen | 6,886 | Land Rover | 831 |
| Mazda | 6,231 | Suzuki | 750 |
| BMW | 5,353 | Jaguar | 700 |
| Mercedes-Benz | 4,710 | Isuzu | 495 |
| Mitsubishi | 2,970 | Saab | 391 |
| Volvo | 2,460 | Fiat | 367 |
| Audi | 2,271 | Porsche | 184 |
| MINI | 1,004 | Geo / Smart / other | ~400 |

## 2. Qualifying sources, ranked by uncovered cars

All of them belong to the same SimplePart/PartsGiant dealer network as the 13
allowed sites. The toyotapartsdeal and bmwpartsdeal footers link to the
allowed sites as sister stores. Robots for `*` is the same everywhere:
`Disallow: /Page_Customer/ /Page_Cart/ /Page_Product/ /online/ /onlineapi/`,
with no Crawl-delay. Catalog paths (`/genuine/`, `/oem/`, `/parts/`,
`/parts-list/`, `/oem-...`, `/service/`) are allowed.

| # | Domain | Makes | Uncovered cars | Template | Probe result | Fitment sample (server HTML, verified via probe) | Terms note | Verdict |
|---|---|---|---:|---|---|---|---|---|
| 1 | www.vwpartsgiant.com | Volkswagen | 6,886 | SimplePart store, `/genuine/volkswagen~<slug>~<pn>`, `/parts-list/<yr>-volkswagen-<model>/...` | robots 200; home, product and terms 200; no challenge | `/genuine/volkswagen~alternator~06k903026l`: "Vehicle Fitment" with 8 YMM rows (2020-2025 Atlas, 2022-2024 Golf ...) | `/service/volkswagen-terms_and_conditions` returns 200, but its body is client-rendered (75 KB shell, same size as a 404). No automation clause appears in served HTML or store. Not human-read. | **Qualifies** |
| 2 | www.mazdapartsnow.com | Mazda | 6,231 | SimplePart store, `/genuine/mazda~<slug>~<pn>`; `/oem-<yr>-mazda-<model>-<cat>` redirects to `/parts-list/...` | all 200, no challenge | `/genuine/mazda~alternator~px4n18300`: "Vehicle Fitment", 2021-2025 Mazda CX-30 | `/service/mazda-terms_and_conditions` 200, client-rendered, no clause found | **Qualifies** |
| 3 | www.bmwpartsdeal.com | BMW (MINI not confirmed) | 5,353 | `.html` PartsGiant: `/parts/bmw-<slug>-<pn>.html` | all 200, no challenge | `/parts/bmw-alternator-12318571357.html`: 11 YMM rows (2016-2018 340i, 2017-2020 440i ...) | `/service/bmw-terms_and_conditions.html` 200, client-rendered, no clause found | **Qualifies** |
| 4 | www.mbpartsgiant.com | Mercedes-Benz | 4,710 | SimplePart store, `/genuine/mercedes-benz~<slug>~<pn>`, `/parts-list/<yr>-mercedes_benz-<model>/...` | all 200, no challenge | `/genuine/mercedes-benz~window-regulator~2037301146`: 13 YMM rows (2002-2007 C230, 2002-2005 C240, 2006-2007 C280 ...) | `/service/mercedes_benz-terms_and_conditions` 200, client-rendered, no clause found | **Qualifies** |
| 5 | www.mitsubishipartsgiant.com | Mitsubishi | 2,970 | SimplePart store, `/genuine/mitsubishi~<slug>~<pn>` | all 200, no challenge (the first home try hit one transient connection reset; the retry was clean) | `/genuine/mitsubishi~strut~1092a034`: 2014-2015 and 2017-2024 Mirage, 2017-2024 Mirage G4 | `/service/mitsubishi-terms_and_conditions` 200, client-rendered, no clause found | **Qualifies** |
| 6 | www.volvopartsgiant.com | Volvo | 2,460 | SimplePart store, `/genuine/volvo~<slug>~<pn>` | all 200, no challenge | `/genuine/volvo~alternator~36000210`: 2011-2013 S60, 2007-2015 S80, 2008-2010 V70, 2010-2013 XC60, 2008-2015 XC70. `/genuine/volvo~radiator~31368221` shows **no** fitment rows. | `/service/volvo-terms_and_conditions` 200, client-rendered; the privacy policy mentions only "automated support features" (their own tooling) | **Qualifies.** Some part numbers carry no fitment, so the navigator must flag `no_fitment_rows`. |
| 7 | www.audipartsgiant.com | Audi | 2,271 | SimplePart store, `/genuine/audi~<slug>~<pn>`, `/oem-audi-<model>-<cat>` | all 200, no challenge (one transient connection reset on a home fetch) | List page `/oem-audi-a6-alternator`: "fits the following", 32 YMM rows. Product pages `03g903016l`, `4n0903028p` and `06e903016r` showed **no** fitment rows in server HTML. | `/service/audi-terms_and_conditions` 200, client-rendered, no clause found | **Conditional.** Fitment appears on list pages, but no product sample showed rows. Before building on it, check whether the rows sit in `__INITIAL_STORE__` the way VW's do. |

Seven sources cover 30,881 of the 36,136 uncovered cars (85%). That would
raise catalog coverage from 89% to about 98.4% of lot cars.

### Second sources for big makes (load spreading; same operator, so NOT an independent cross-check)

| Domain | Makes | Template | Probe | Fitment sample | Terms | Verdict |
|---|---|---|---|---|---|---|
| www.toyotapartsdeal.com | Toyota, Scion | `.html` PartsGiant: `/oem/toyota~<slug>~<pn>.html` (a different template from toyotapartsnow, which is SimplePart) | all 200, no challenge | `/oem/toyota~alternator~assy~w~r~27060-0v010.html`: 2012-2015 Camry, 2009-2012 RAV4 | `/service/toyota-terms_and_conditions.html` 200, client-rendered, no clause found | **Qualifies** as a second Toyota source. It is the same dealer network as toyotapartsnow, so agreement between them is not independent verification. |
| www.chevypartsdeal.com | GM (Chevrolet, GMC, Buick per its make pages) | SimplePart store, `/oem/gm~<slug>~<pn>`, `/parts-select/<yr>-chevrolet-<model>-<cat>`, `/catalog/<yr>-chevrolet-<model>-parts` | all 200, no challenge (one transient reset on the first try) | `/oem/gm~fan-assembly-engine-cooler~23434158`: 2008-2017 Enclave, 2009-2017 Traverse, 2007-2016 Acadia | `/service/gm-terms_and_conditions` 200, client-rendered, no clause found | **Qualifies** as a second GM source. Same network as gmpartsgiant. |

No qualifying second source turned up for Ford, Mopar, Honda or Nissan. Every
independent dealer store found for those makes is behind Cloudflare (see §3).

### Caveats the hub should weigh

- **Terms not human-read.** On every PartsGiant/SimplePart site, the terms
  page body is loaded client-side. probe.py can see that the page exists
  (200) and that served HTML and the embedded store contain no
  automated/robots/scrape/crawl/spider/data-mining clause. It cannot see the
  clause text itself. The 13 allowed sites have the same set-up. Someone
  should read one terms page in a browser before ALLOWED is extended.
- **Honeypot link:** the vwpartsgiant home links to `/login/honeypot.html`.
  The other sites in this family probably do too. fetch.py's honeypot guard
  must stay on.
- `www.bmwpartsgiant.com` reset the connection twice, so it is not usable.
  bmwpartsdeal is the BMW source. MINI coverage on bmwpartsdeal is untested.

## 3. Rejected candidates

| Domain | Makes | Reason |
|---|---|---|
| parts.vw.com | VW (official) | Cloudflare "Just a moment..." 403; robots has `Disallow: /` groups |
| parts.audiusa.com | Audi (official) | Cloudflare 403; robots `Disallow: /` groups |
| parts.mitsubishicars.com | Mitsubishi (official) | Cloudflare 403 (RevolutionParts platform, Crawl-delay 10) |
| www.autonationparts.com | multi-make incl. BMW, Volvo, Land Rover, Porsche, Mercedes | Cloudflare 403 (RevolutionParts) |
| www.tascaparts.com | Mazda, Ford, multi | Cloudflare 403 (RevolutionParts) |
| www.mazdawholesaledirect.com, www.realmazdaparts.com | Mazda | Cloudflare 403 (RevolutionParts) |
| www.europarts4less.com, www.audiusaparts.com | VW, Audi | Cloudflare 403 (RevolutionParts) |
| www.sunsetporscheparts.com | Porsche | Cloudflare 403 (RevolutionParts) |
| parts.landrovercary.com | Land Rover | Cloudflare 403 (RevolutionParts) |
| www.gmoutletparts.com, www.gmpartsclub.com | GM | Cloudflare 403 (RevolutionParts) |
| www.moparpartsproonline.com, www.directfactoryparts.com | Mopar, Fiat | Cloudflare 403 |
| www.hondafactoryparts.com, www.hondapartshq.com | Honda | Cloudflare 403 (RevolutionParts) |
| parts.olathetoyota.com | Toyota | Cloudflare 403 (RevolutionParts) |
| www.ecstuning.com | Euro makes | Cloudflare 403; robots.txt itself 403 |
| www.europartsgiant.com | Euro makes | Cloudflare 403 |
| partsouq.com | EPC, all makes | Cloudflare 403 |
| www.nengun.com | JDM OEM | security verification page (403); robots `Disallow: /` group plus `/oem/parts/` |
| www.fcpeuro.com | BMW, VW, Audi, Volvo, Mercedes, MINI, Saab, Porsche | No challenge and robots allows `/products/`, but its Terms of Service say: "any use of data mining, robots, or similar gathering and extraction tools is strictly prohibited". Rejected under rule 2. Its retailer fitment is also not OEM catalog data. |
| www.megazip.net | JDM OEM | Terms (`/info/terms`) forbid using the site "to spam, phish, pharm, pretext, spider, crawl, or scrape". Also, the product sample showed no fitment list in server HTML, and robots disallows `/*/diagrams/`. |
| yoshiparts.com | JDM OEM | Product page `/parts/mazda-ZJ0118400` has no fitment list in server HTML (the model list is JS-rendered or absent); `/terms` 404; robots disallows `/parts/*/*/products/` and diagrams |
| 7zap.com | EPC, incl. Suzuki, Saab, Porsche | No challenge, but it is a diagram EPC with no per-part "fits these vehicles" list. `/en/terms/` serves the home page, so terms could not be checked. Not qualified. |
| www.jaguarpartsgiant.com, www.porschepartsgiant.com, www.mitsubishifactoryparts.com | Jaguar, Porsche, Mitsubishi | Home is a 114-byte stub with empty robots and no catalog (parked or redirect shell) |
| www.bmwpartsgiant.com | BMW | connection reset twice |
| volvopartswebstore.com, www.mazdapartsgiant.com, www.minipartsgiant.com, www.minipartsdeal.com, www.landroverpartsgiant.com, www.landroverpartsdeal.com, www.porschepartsdeal.com, www.fiatpartsgiant.com, www.fiatpartsdeal.com, www.saabpartsgiant.com, www.suzukipartsgiant.com, www.suzukipartsdeal.com, www.isuzupartsgiant.com, www.mitsubishipartsdeal.com, www.vwpartsdeal.com, www.volvopartsdeal.com, www.dodgepartsgiant.com, www.fordpartsdeal.com, www.hondapartsdeal.com, www.minipartsnow.com | guessed family names | did not resolve or connect (proxy 502, reset or TLS error). Treated as nonexistent. |
| www.bernardiparts.com | Honda (second source) | Home and `/Honda-Parts.aspx` return 200 with no challenge, but I found no product sample and its robots has `Disallow: /` lines for some agent groups. Not evaluated (see the deviation note at top). |

Still without any source: MINI (1,004), Land Rover (831), Suzuki (750),
Jaguar (700), Isuzu (495), Saab (391), Fiat (367), Porsche (184), Geo (182).
Isuzu Ascender/i-Series and Saab 9-7X/9-2X are GM/Subaru badge-engineered;
the hub could check whether gmpartsgiant or subarupartsdeal list them. Fiat
may appear on moparpartsgiant; that is untested.

## Probe tooling change

`probe.py` now prints read-only `signals` for each response it already
fetched: template markers, fitment markers, YMM row samples, terms-clause
hits, linked sister domains, and same-site `.html` links. The request
pattern is unchanged.

## Aftermarket catalogs, probe 2026-11-09 (Aftermarket breadth session)

Each checked with `probe.py` (robots, home page, challenge markers) and, where
it passed that, by hand: the terms read for an anti-automation clause and one
or two catalog pages fetched with the program UA, 5-6 s apart. Rule: a robots
disallow, a challenge, or an anti-automation clause is OUT; no workaround.

| source | robots (RFC 9309) | challenge | terms | per-unit pages as GET HTML | verdict |
|---|---|---|---|---|---|
| Depo (www.depoautolamp.com) | Cloudflare-managed file (`Content-signal: ai-train=no`; named AI crawlers disallowed; `*` allowed) | **yes**: home page is a challenge (probe `challenge: true`) | not reached | not reached | **OUT** (challenge) |
| Four Seasons (www.4s.com) | managed file | **yes**: HTTP 403 "Just a moment..." | not reached | not reached | **OUT** (challenge) |
| SMP e-catalog (ecatalog.smpcorp.com) | managed file | **yes**: HTTP 403 "Access is denied" | not reached | not reached | **OUT** (refusal) |
| ACI (window regulators / motors) | ACI is an SMP / Four Seasons brand; no own catalog found; its data is SMP's e-catalog above | (as SMP) | (as SMP) | resellers only (out of scope: third-party) | **OUT** (same owner, refused) |
| Cardone (www.cardone.com) | `*` allows product/category paths, disallows `*?` (every query URL, incl. the sub-sitemaps) and `/terms-of-use/` | none | **unreadable**: the terms pages are robots-disallowed for us | **no**: category pages (e.g. /motors/window-lift/window-regulator/) carry no product links; the grid loads client-side | **OUT / unreachable** (owner may read the terms in a browser; still no server-side product list) |
| Spectra Premium (ecat.spectrapremium.com; corporate www.spectrapremium.com) | ecat: `User-Agent: * / Disallow:` (all allowed); corporate: only /qr.php | none on catalog pages; Google reCAPTCHA protects only the VIN search form (never called) | Legal Notice: copyright, "may not be reproduced in whole or in part without prior written consent"; **no anti-automation clause** | **yes**: `/en/parts/<pn>` (all application rows, year x submodel x engine code, paginated `?page=N`), `/en/vehicles/<id>/parts` (every part for one vehicle WITH the application note), GET JSON vehicle tree (`/en/vehicules/get-*.json`) | **PASS, pending hub**: allowlist + the fetch.py captcha marker (below); the hub weighs the no-reproduction clause (we store facts, not pages, and publish groups) |

Spectra notes for the hub:
- `fetch.CHALLENGE_RE` matches `captcha` in `<script src="https://www.google.com/recaptcha/api.js">`,
  present in the first 20 KB of EVERY ecat page (the VIN form's invisible
  reCAPTCHA). As is, the first page would trip the permanent breaker. The
  pages are served in full (no interstitial). Narrow fix proposed: ignore
  exactly that script tag when matching; any other marker still stops.
  Not changed; the hub's call.
- The application note is only on vehicle pages, so the adapter is
  vehicle-driven (`aftermarket/spectrapremium.py`).
- Pages print no OE numbers (only Spectra part numbers and specs); the
  "Interchange #" search exists but was not probed. The dealer-catalog OE
  join is therefore not available from the pages we read.

Second pass (2026-11-09, after the hub's HOLD on Spectra; same criteria):

| source | result | verdict |
|---|---|---|
| CSF radiators (www.csfradiators.com) | connection reset on robots.txt | **unreachable** (not retried) |
| OSC Cooling (www.osccoolingproducts.com) | proxy 502 on robots.txt (host not reachable) | **unreachable** |
| Eagle Eye lamps (www.eagleeyelights.com) | domain parked (redirects to DropCatch) | **defunct** |
| Koyorad (koyoradracing.com) | robots ok, no challenge; WooCommerce performance-radiator shop, few street applications | **low value**, not pursued |
| Nissens (catalogue.nissens.com) | robots allow; catalogue now redirects to customerportal.nissens.com (login); EU-market data | **OUT** (no plain-GET application pages) |

Spectra Premium is ON HOLD (hub, 2026-11-09 ~18:48 UTC): the reCAPTCHA marker in
fetch.CHALLENGE_RE and the Legal Notice's no-reproduction clause go to the owner.
Not allowlisted, fetch.py unchanged, not crawled.

**Spectra Premium: OUT (owner decision relayed by the hub, 2026-11-09 ~19:41 UTC:
"no email needed").** No outreach. `fetch.py` and `fetch.ALLOWED` stay
unchanged. `aftermarket/spectrapremium.py` stays on main unused; it may not
be run against the site unless the owner reverses this.

**Spectra Premium: REOPENED (owner, verbatim, relayed by the hub 2026-11-09
~19:45 UTC: "use spectra if it doesnt break anything").** This supersedes the
OUT entry above. The hub approved detector rule (a)-(e) at ~19:45 UTC.

Page evidence (4 pages fetched in the probe: home, part-number search,
/en/vehicles/23745/parts, /en/parts/CU13221). Every page carries:
- in `<head>`, `<script src="https://www.google.com/recaptcha/api.js?hl=en" async="async" defer="defer"></script>`;
- exactly one `<div class="g-recaptcha" data-sitekey=… data-callback="googleRecaptchaOnSubmit"
  data-size="invisible"></div>`, inside `<form id="vin-search-form" action="/en/vehicules/get-vehicle">`
  (header VIN search; it runs only when a VIN is submitted, which we never do), at byte ~19.7-20.2 K;
- the full catalog content alongside it: no interstitial.

The old detector (`captcha` in the first 20 KB) would have stopped the
domain on the first page. Rule, in `fetch.challenged()`, for
`ecat.spectrapremium.com` only: the page is NOT challenged only when ALL of
these hold:
- (a) HTTP 200;
- (b) the expected catalog body for the path is present:
  - vehicle page: `parts__motorization` + "Showing parts";
  - part page: `part__table-applications`;
  - home: the vehicle-search form;
  - `.json`: valid JSON;
  - any other path: none, so it stops;
- (c) exactly one api.js include of that exact form;
- (d) exactly one `g-recaptcha`, the invisible VIN-form widget above, inside vin-search-form;
- (e) with exactly those two snippets removed, CHALLENGE_RE and HUMAN_RE
  ("verify you are human", "unusual traffic", "are you a robot", "access denied")
  match nowhere in the body.

Anything else stops the domain for good. Other hosts keep the old rule
byte for byte. We never load, render, execute or submit anything
captcha-related.

Tests: `tests/test_fetch_challenge.py`:
- 350 non-Spectra inputs are identical to the old rule;
- the real vehicle and part pages pass;
- each of these stops:
  - a second widget, a visible widget, a widget without data-size, a widget outside the form;
  - a missing motorization block, a missing counter, a missing application table;
  - "unusual traffic", "verify you are human", challenge-platform, other "captcha" text, hCaptcha;
  - a second include, an interstitial, an empty body;
  - HTML on a JSON path, an unknown path;
  - HTTP 403/429/503/500/404/301.

Data use (hub): store application facts only, as for DB Electrical.
Publish only our derived groups, labelled "Spectra Premium" + unit number,
with notes in our own words. No page text, images or descriptions.

## Source scout 2 (2026-11-09)

Interchange source-scout session (session_016ZzJfKZ49mzzQhu4KT7HkU). Brief: more FREE
per-part application catalogs that pass rule 2. Method: a scratch copy of
`probe.py`'s request pattern (program UA, robots first, 5-6 s apart, at most a
handful of GETs per host) that reads robots with the RFC 9309 rules of
`aftermarket/common.py` (all `*` groups merged, wildcards, longest match) and
tests `fetch.CHALLENGE_RE` + `fetch.HUMAN_RE` on the first 20 KB. A host
stopped for good on 403/429/503 or any marker. Terms were read in full where
reachable and searched for automated/robots/scrape/crawl/spider/data-mining/
reproduction clauses. Nothing was added to `fetch.ALLOWED`; nothing was crawled.
Sources already decided in the sections above were not re-probed.

### Verdicts

| source | categories it would feed | robots (RFC 9309) | challenge | terms (quoted) | per-part lists as GET | verdict |
|---|---|---|---|---|---|---|
| **GSP North America** (gspnorthamerica.com; Shopify) | cv-axle (NCV…), knuckle-side hubs (excluded by "hub only"), steering/suspension, ride control (strut) | `*`: only Shopify defaults (`/admin`, `/cart`, `/checkout`, `/account`, `/orders`, `/services`, …); `/products/*` and the product sitemaps allowed; no crawl-delay | none as an interstitial. **But** every HTML page carries Shopify's form-protection script `<script id="captcha-bootstrap">` (contact/account forms) at byte ~32 K, and the JSON variant of `/` had it inside 20 KB. `fetch.challenged()` would stop the domain whenever a page's head shrinks below that | `/policies/terms-of-service` body is literally "Coming soon..."; no terms published, so no anti-automation or no-reproduction clause | **yes**: `/products/<handle>` server-renders `<table class="product-applications__table">` with Year Range / Make / Model / Submodel / Position; specs (spline counts, lengths, ABS ring) server-rendered too; ~20k products in 20 product sitemaps | **PASS, pending hub** (site-scoped marker rule like Spectra's; data-quality caveat below) |
| 1A Auto (www.1aauto.com) | broad (mirrors, regulators, lamps, struts, handles, wiper motors…) | `*` allows catalog; disallows `/search`, `/*Fld=`, `/*sort=`, `/cart`, …; `Crawl-Delay: 1` | none on home, terms, `/catalog/parts` | Terms of use: "1A Auto grants you a limited, revocable, non-exclusive, non-transferable license to view, download, and print the Site Content solely for your personal, non-commercial use … Any other use of the Site Content, including but not limited to modification, reproduction, redistribution, republication … without the prior written consent of 1A Auto, is strictly prohibited." No automated-access clause found | not confirmed (sample category URL 404; no product page reached) | **owner decision** (personal/non-commercial licence + no-reproduction). Also a retailer catalog, not a maker's |
| Monroe (www.monroe.com) / DRiV-Tenneco | strut | `*` allows / (disallows `/data/`) | none | Terms & conditions: prohibited are "any collection and use of any product listings or descriptions; any derivative use of this Website or its contents; or any use of data mining, robots, or similar data gathering and extraction tools" | not checked | **OUT** (anti-automation clause) |
| Moog (www.moogparts.com) / DRiV | knuckle, steering | as Monroe | none | identical clause to Monroe | not checked | **OUT** (anti-automation clause) |
| Mevotech (www.mevotech.com) | knuckle, suspension | robots.txt 404 (all allowed) | none | Terms of use PDF (2020-09): may not "systematically collect from the Website and use any Mevotech Content, including the use of any data mining, robots, or similar data gathering and extraction methods" | not checked | **OUT** (anti-automation clause) |
| TRW (www.trwaftermarket.com → aftermarket.zf.com) | suspension, steering | aftermarket.zf.com: `User-agent: *` / `Disallow: /` | — | not read (robots) | — | **OUT** (robots disallows all) |
| KYB (www.kyb.com) | strut | allows (disallows `/wp-json/`) | **yes**: home HTTP 403 "Just a moment..." | not reached | — | **OUT** (challenge) |
| Bilstein (www.bilstein.com) | strut (B4) | `/robots.txt` serves the HTML home page (no robots file); that page contains "reCAPTCHA" (consent-manager config) | marker present | not reached | not checked | **OUT** (challenge marker; not pursued) |
| Gabriel (www.gabriel.com) | strut | proxy 502 twice | — | — | — | **unreachable** |
| ACDelco (www.acdelco.com), GM Parts (www.gmparts.com) | all GM | robots.txt HTTP 403 | refusal | — | — | **OUT** (403) |
| Motorcraft (www.fordparts.com) | all Ford | robots.txt timed out twice | — | — | — | **unreachable** (not retried further) |
| Genuine Toyota (parts.toyota.com) | all Toyota | proxy 502 twice | — | — | — | **unreachable** |
| ShowMeTheParts (www.showmetheparts.com), the catalog platform behind many brand finders (FCS uses it in an iframe) | many | robots.txt HTTP 403 | refusal | — | — | **OUT** (403) |
| Opticat (walkerproducts.opticatonline.com), platform behind Walker Products' lookup | MAF, sensors, throttle body (Walker) | — | **yes**: HTTP 403 challenge | — | — | **OUT** (challenge); Walker's own site has no application lookup |
| FCS Automotive (fcsautoparts.com) | strut (complete assemblies) | robots has no rules | none | Terms: licence "for personal, non-commercial transitory viewing only … you may not: modify or copy the materials; use the materials for any commercial purpose" | no: the light-duty lookup is a ShowMeTheParts iframe (403); only a heavy-duty XLSX | **OUT** (lookup is on a refused platform; restrictive licence) |
| UAC (www.uacparts.com) | ac-compressor, condensers, evaporators, blower-wheel chart | robots.txt 404 (all allowed) | none | only credit-card and ordering-system terms (customer contracts); no site terms of use found | **no**: the vehicle application catalog (AwesomeMVC cascading selects) and every result list are POST-only AJAX; GETs on `/VA_*AjaxDropdown/GetItems` answer HTTP 500; `/Catalog/SearchIndex?search=` renders an empty shell | **not qualified** (no plain-GET application data). Hub may ask the owner whether POSTs to a public dropdown API are acceptable; this session did not send any |
| Delphi (www.delphiautoparts.com) | fuel-pump-module, sensors | `*` allows / | none | Terms of use read (23 KB text): no automated/robots/scrape/data-mining clause found | not resolved: `/parts-catalog` serves a "No Results Found" shell; results appear to load client-side (not confirmed) | **unresolved**, low priority |
| BBB Industries (www.bbbind.com) | power-steering, alternators, calipers | robots.txt HTTP 403 | refusal | — | — | **OUT** (403) |
| WAI Global (www.wai-gbl.com) | alternators/starters, wiper motors | proxy 502 | — | — | — | **unreachable** |
| GPD Global Parts (www.globalparts.co) | ac-compressor, radiator | allow / | none | — | home is a 114-byte stub | **no catalog** at that host |
| Unity (www.unityautoparts.com) | — | — | — | — | the domain is Unity Group (India), not the US strut maker | **wrong host**, not pursued |
| LKQ Online (www.lkqonline.com) | used OE parts | `*` allows catalog (disallows checkout/user/cms) | none | not read | no: home is a 5 KB JS shell | **not qualified** (no server-rendered content seen) |
| RockAuto (www.rockauto.com) | everything | `*`: `Disallow: /info/`, `/cgi-bin/` | **marker**: the home page matches `captcha` (the image security code on its account/password forms). Under `fetch.challenged()` the domain stops on the first page. First two attempts on the home page: connection error | not reached; its help/legal pages sit under `/info/`, which robots disallows for us | catalog is a per-vehicle tree, not per-part "fits" lists | **OUT**: challenge marker on every page plus terms unreadable under robots. This is the concrete reason behind the decision record's "not used" |

### GSP North America: what the data looks like

- Sample `NCV36167XD` (title "17-22 Honda CR-V (1.5, 2.4) CV Axle Assembly - Front Left"):
  four rows: 2017-2018, 2019-2019, 2019-2019, 2020-2022 Honda CR-V,
  Submodel "-", Position "Front Left".
- **Qualifiers are dropped.** Submodel is "-" and the table has no engine,
  drive or transmission column. The engines appear only in the title, as
  "(1.5, 2.4)". The duplicate 2019 row shows that some distinguishing
  attribute was collapsed away. AWD/FWD and auto/manual axle splits are
  therefore invisible.
- Sample `NS90049`: "1996-2002 Land Rover Range Rover", Submodel "-".
- Specs are server-rendered: inboard/outboard spline counts, compressed and
  extended lengths, ABS tone ring, axle-nut thread. These help a twin check:
  two units with equal specs are physically alike.
- No OE numbers on the page.

Yield estimate, CV axle: GSP is a full-line CV maker (NCV10xxx-NCV7xxxx
covers Asian, domestic and Euro makes). Most cars on our lots are FWD or AWD,
so the potential cv-axle coverage is broad. The dropped qualifiers limit what
can ship. A cv-axle group can be Likely only where:
- every row of the unit has Submodel "-" or a submodel we can gate on;
- no duplicate (years, make, model, position) row appears;
- the title's engine list matches our engine.

Units whose rows contain duplicates refuse. An AWD/FWD split must never be
inferred. Strut ("Ride Control") yield is not yet sampled.

### Adapter plan: `aftermarket/gspnorthamerica.py` (not built; waits for the hub)

Same contract as `dbelectrical.py` (`SITE`, `STATUS`, `CATEGORIES`,
`listing()`, `product()`, `get = common.get`). It runs through `run.py`, so
fetch.py pacing, cache, robots and the permanent stop are unchanged.

- **Navigation (no search URLs):** `/sitemap.xml`, then the
  `sitemap_products_N.xml` files (GET XML, robots-allowed), then the product
  handles. Keep only handles with a category prefix:
  - `ncv` = cv-axle;
  - the ride-control/strut prefixes, after one sample confirms them.
  Unknown prefixes are skipped. `score()` orders the worklist by
  lot-weighted make/model taken from the sitemap image titles where printed,
  otherwise by sitemap order.
- **Product page parse:**
  - `<table class="product-applications__table">`: one application per
    printed row (years, make, model, submodel, position), verbatim.
  - `GSP Part Number:`: the unit number.
  - `<title>`: the engine list in parentheses, verbatim.
  - The Specifications block: spline counts, lengths, ABS ring, nut thread.
  - Duplicate rows are kept as printed, with a `duplicate_rows` count.
  - No OE join; `replaces` is empty.
  - Never read: the `.json` variant, prices, images, descriptions.
- **Curation rules (groups_am):**
  - Likely only.
  - Refuse a unit when:
    - it has a duplicate (years, make, model, submodel, position) row;
    - a Submodel cell names a trim we cannot gate on;
    - the title's engines do not include the car's engine.
  - Never infer drive or transmission. A position must be printed.
- **Challenge detector (hub decision first):** every page carries Shopify's
  `<script id="captcha-bootstrap">` (forms only), at ~32 KB, so it moves
  around the 20 KB window. Proposed site-scoped rule, built on the Spectra
  (a)-(e) pattern:
  - HTTP 200;
  - for a product path, the `product-applications__table` or the GSP
    Part Number block is present; for a sitemap path, valid sitemap XML;
  - exactly one `captcha-bootstrap` script;
  - with that one script removed, no CHALLENGE_RE or HUMAN_RE match.
  Anything else stops the domain. Tests both ways, as in
  `tests/test_fetch_challenge.py`.
- **Data use:** application facts and specs only. Publish derived groups
  labelled "GSP" plus the unit number. No page text.
- **Size:** about 20k handles, of which perhaps 3-5k are cv-axle. At 4 s/site
  that is 4-6 h of crawl in 28-minute slices.

### Owner decisions and the GSP detector rule (2026-11-09)

Owner, verbatim (question dialog, relayed by the hub, ops/hub.md, ~20:15 UTC):
- GSP North America: "Yes, use GSP".
- 1A Auto: "Yes, use 1A Auto anyway". This accepts the risk of its
  personal/non-commercial licence.
- ~20:20 UTC: "lets do it, also 1A im not selling the part fitment portion".

**1A Auto data-use design (hub, from the owner's words):**
- Fits derived from 1A data are never behind Pro. They stay in the free part
  of the Parts tab, as all fitment does today: donors and tiers are free, and
  only prices/values are Pro.
- 1A's prices, descriptions and images are never shown.
- Labelled "1A Auto" plus the unit number. Notes are in our own wording.
- When 1A groups are integrated, a test must assert that 1A-sourced rows
  render identically for free and Pro users, apart from the existing
  price/value lines. That test is not written yet, because no 1A rows exist
  yet; it is a ship blocker for 1A.
- The "Part Interchange" cross-brand numbers (e.g. Unity 13432, FCS 2337077R)
  are evidence of brand equivalence only. They are never evidence of vehicle
  fitment on their own.

**GSP detector rule, hub-approved (~20:21 UTC); `fetch.gsp_challenged`, host
`gspnorthamerica.com` only.** The page counts as NOT challenged only when ALL
of these hold:
- (a) HTTP 200.
- (b) The expected body for the path is present:
  - `/products/<handle>`: `<p class="product__text …"><strong>Part Number:</strong>`
    and a `<title>` ending "GSP North America";
  - `/sitemap.xml` and `/sitemap_products_N.xml`: a valid `sitemapindex` or
    `urlset`;
  - `/`: that title.
  - Any other path stops, including `/search`, `/collections/*` and `.json`.
- (c) HTML has exactly one `<script id="captcha-bootstrap">`.
- (d) With every `<script>…</script>` element removed, neither CHALLENGE_RE,
  HUMAN_RE nor "turnstile" matches anywhere.
- (e) The full body has no strong marker (cf-chl, challenge-platform,
  "Just a moment...", "Attention Required!", `/challenge`, `/checkpoint`) and
  no HUMAN_RE anywhere, scripts included. Sitemaps allow no marker at all.

Anything else, and any 403/429/503, stops the domain for good. Every other
host keeps the old rule byte for byte (`tests/test_fetch_gsp.py`, 1,260
inputs, including the real GSP pages).

Page evidence, from the real pages retrieved 2026-11-09 (product
ncv36167xd, home, /pages/products, terms):
- Each page has 68 matches of the bare word "captcha", all inside `<script>`
  elements. One is Shopify's `captcha-bootstrap` (form protection for
  contact/account forms, 3,417 bytes). The rest are the Globo Form Builder
  config (`"reCaptcha":{"enable":false}`, `"hCaptcha":{"siteKey":false}`,
  `"turnstile":{"siteKey":false}`) and translation strings
  (`"requiredCaptcha"`, `"Please complete reCAPTCHA task"`).
- No match is in visible markup or text. None are cf-chl, challenge-platform,
  interstitial titles or HUMAN_RE.
- The full product page is committed as
  `tests/fixtures/gsp_full_product_ncv36167xd.html.gz`.

Stops proved in tests:
- visible widgets: g-recaptcha, h-captcha, turnstile;
- visible text: "verify you are human", "unusual traffic", "captcha";
- "verify you are human" inside a script;
- Shopify `/challenge` and `/checkpoint`;
- cf-chl, challenge-platform, "Just a moment...", "Attention Required!";
- a second bootstrap script, or none;
- a missing part-number line, a missing title;
- an interstitial page, an empty body;
- unknown, search or `.json` paths; an HTML or marked sitemap;
- HTTP 403/429/503/500/404/301.

We never load, run or submit anything.
