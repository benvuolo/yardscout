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
