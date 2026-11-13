/* Unit test for the /landed/<make>/<model> pages (src/share.js
 * renderLandedModelPage) through the Worker's own router, fetch stubbed with
 * fixture data in the shape the scraper writes (docs/data/landed/, see
 * scraper/test_landed_models.py). Nothing leaves the machine.
 *   - counts and wording match the fixture; state-first, then yard, newest first
 *   - 4x4 bold / 2WD / AWD and the trim word only when the data has them
 *   - zero-arrival page; unknown make/model 404 noindex; data down 503;
 *     before the first scan writes the files: holding page (503, noindex)
 *   - sitemap entries, make/hub/car/yard pages link to the model pages,
 *     every internal link on a model page resolves to a route that answers 200
 *   - titles: <= 65 chars where the count allows, never cut mid-word
 * Run: node test/model_pages_unit.mjs   (from backend/site-proxy/) */
import worker from '../src/index.js';
import { fitTitle } from '../src/share.js';

let failures = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + detail}`); if (!ok) failures++; };

const today = new Date().toISOString().slice(0, 10);
const daysAgo = (n) => new Date(Date.now() - n * 86400000).toISOString().slice(0, 10);
const SCAN = '2026-11-13T07:41:48Z';
const LAST_MODIFIED = 'Fri, 13 Nov 2026 07:41:48 GMT';
// make file rows: [year, yard, row, date, drive, trim, key]
const NISSAN = {
  scrapedAt: SCAN, days: 7, make: 'Nissan', slug: 'nissan',
  yards: [['Pick-n-Pull - Phoenix', 'Phoenix', 'AZ'], ['Pull-A-Part - Springfield', 'Springfield', 'MO'],
    ['Calgary Pick-a-Part', 'Calgary', 'AB'], ['LKQ <Mesa> & Co', 'Mesa', 'AZ'], ['Odd Yard', 'Nowhere', 'ZZ']],
  models: [
    { model: 'Xterra', slug: 'xterra', total: 1078, recentCount: 6, states: { AZ: 56, MO: 20, AB: 10, TX: 166 }, recent: [
      [2008, 1, '25', today, '4x4', 'Off-Road', '5N1AN08W08C000001'],
      [2005, 0, '', today, '2WD', '', '5N1AN08U05C000002'],
      [2011, 3, 'A7', daysAgo(1), '', '', '5N1AN0NU0BC000003'],
      [2002, 0, '4', daysAgo(3), 'AWD', '', 'ipull-123'],
      [2001, 2, '9', daysAgo(2), '4x4', '', '5N1ED28T01C000005'],
      [2009, 4, '1', daysAgo(5), '', '', '5N1AN08W09C000006'],
    ] },
    { model: 'Frontier', slug: 'frontier', total: 900, recentCount: 0, states: { AZ: 500, MO: 400 }, recent: [] },
  ],
};
const INDEX = { scrapedAt: SCAN, days: 7, minOnLots: 100, minWeek: 10, makes: {
  Nissan: { slug: 'nissan', total: 1978, recentCount: 6, models: [['Xterra', 'xterra', 1078, 6], ['Frontier', 'frontier', 900, 0]] },
  'Mercedes-Benz': { slug: 'mercedes-benz', total: 150, recentCount: 0, models: [['Grand Marquis Super Long Name Edition', 'grand-marquis-super-long-name-edition', 150, 0]] },
} };
const LANDED = { scrapedAt: SCAN, days: 7, yards: [['Pick-n-Pull - Phoenix', 'Phoenix', 'AZ', 100, 5]],
  makes: { Nissan: { total: 1978, recentCount: 6, recent: [[2008, 'Nissan', 'Xterra', '25', today, '5N1AN08W08C000001', 0], [2012, 'Nissan', 'Altima', '3', today, 'X2', 0]] } } };
const YARD_FIELDS = ['location', 'city', 'state', 'lat', 'lng', 'avgLifespanDays', 'lifespanBasis'];
const DIRECTORY = { scrapedAt: SCAN, yardFields: YARD_FIELDS, yards: [['Pick-n-Pull - Phoenix', 'Phoenix', 'AZ', 33.4, -112, 40, 'yard'],
  ['Pull-A-Part - Springfield', 'Springfield', 'MO', 37.2, -93.3, null, null], ['Calgary Pick-a-Part', 'Calgary', 'AB', 51, -114, null, null],
  ['LKQ <Mesa> & Co', 'Mesa', 'AZ', 33.4, -111.8, null, null], ['Odd Yard', 'Nowhere', 'ZZ', 0, 0, null, null], ['Houston U-Pull', 'Houston', 'TX', 29.7, -95.4, null, null]] };
// junkyards.json rows: [location, pageCity, state, lat, lng, carsOnLot, setOutLast7Days]
const JUNKYARDS = { scrapedAt: SCAN, days: 7, yards: DIRECTORY.yards.map((y) => [...y.slice(0, 5), 10, 1]), newest: DIRECTORY.yards.map(() => []), stateMakes: {} };
const SHARD = { vpic: {}, vehicles: [[1, '5N1AN08W08C000001', 2008, 'Nissan', 'Xterra', '25', today, 0, 0, 0, 0], [2, '', 2010, 'Nissan', 'Altima', '2', today, 0, 0, 0, 0]] };

let mode = 'ok';   // 'ok' | 'down' (data host errors) | 'none' (files not written yet)
globalThis.fetch = async (u) => {
  u = String(u);
  const json = (o, status = 200) => new Response(JSON.stringify(o), { status, headers: { 'content-type': 'application/json' } });
  if (u.includes('/data/landed/')) {
    if (mode === 'down') return new Response('down', { status: 502 });
    if (mode === 'none') return new Response('Not Found', { status: 404 });
    if (u.endsWith('/data/landed/index.json')) return json(INDEX);
    if (u.endsWith('/data/landed/nissan.json')) return json(NISSAN);
    return new Response('Not Found', { status: 404 });
  }
  if (u.endsWith('/data/landed.json')) return json(LANDED);
  if (u.endsWith('/v1/yards')) return json(DIRECTORY);
  if (u.endsWith('/data/junkyards.json')) return json(JUNKYARDS);
  if (/\/v1\/inventory\/shard\/0$/.test(u)) return json(SHARD);
  if (/\/v1\/inventory\/shard\/\d+$/.test(u)) return json({ vehicles: [], vpic: {} });
  const m = u.match(/\/v1\/vehicles\/([^/]+)$/);
  if (m) {
    const row = SHARD.vehicles.find((r) => r[1] === m[1] || String(r[0]) === m[1]);
    if (!row) return json({ error: 'not_found' }, 404);
    const [id, vin, year, make, model, rowNo, dateAdded] = row; const y = DIRECTORY.yards[0];
    return json({ scrapedAt: SCAN, tier: 'free', vehicle: { id, vin, year, make, model, row: rowNo, dateAdded, yard: 0 }, vpic: null, yard: { id: 0, location: y[0], city: y[1], state: y[2] } });
  }
  if (u.startsWith('https://benvuolo.github.io/yardscout/') || u.startsWith('https://yardscout-api')) return new Response('Not Found', { status: 404 });
  return new Response('offline', { status: 502 });
};
const get = async (path) => {
  const r = await worker.fetch(new Request(`https://yardscout.io${path}`, { redirect: 'manual' }), {});
  return { status: r.status, headers: r.headers, html: await r.text() };
};
const titleOf = (html) => (html.match(/<title>([^<]*)<\/title>/) || [])[1];
const meta = (html, name) => (html.match(new RegExp(`<meta (?:name|property)="${name}" content="([^"]*)"`)) || [])[1];
const canonical = (html) => (html.match(/<link rel="canonical" href="([^"]+)">/) || [])[1];
const h1s = (html) => [...html.matchAll(/<h1[\s>][\s\S]*?<\/h1>/g)].map((m) => m[0].replace(/<[^>]+>/g, ''));
const ldBlocks = (html) => [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)].map((m) => JSON.parse(m[1]));
const FORBIDDEN_LD = /"@type":\s*"(Vehicle|Car|Product|Offer|AggregateOffer|AggregateRating|Review)"|aggregateRating|"offers"/;
const text = (html) => html.replace(/<script[\s\S]*?<\/script>/g, '').replace(/<style[\s\S]*?<\/style>/g, '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ');

/* ---------- the Xterra page ---------- */
let r = await get('/landed/nissan/xterra');
check('model page → 200', r.status === 200, r.status);
check('one <h1>, query-shaped', JSON.stringify(h1s(r.html)) === JSON.stringify(['Nissan Xterra junkyard inventory: 6 set out this week at self-service yards']), JSON.stringify(h1s(r.html)));
check('title fits 65 chars with the brand', titleOf(r.html) === 'Nissan Xterra junkyard inventory: 6 set out this week — YardScout' && titleOf(r.html).length <= 65, titleOf(r.html));
check('canonical', canonical(r.html) === 'https://yardscout.io/landed/nissan/xterra', canonical(r.html));
check('indexable, cached like the landed pages', meta(r.html, 'robots') === 'index,follow' && /max-age=900/.test(r.headers.get('cache-control')));
check('Last-Modified is the scan time', r.headers.get('last-modified') === LAST_MODIFIED, r.headers.get('last-modified'));
check('meta description carries the counts', meta(r.html, 'description') === '6 Nissan Xterra set out at 5 self-service junkyards in 2 states and 1 Canadian province in the last 7 days, by state, with yard, row and date. 1,078 on the lots now. As of Nov 13, 7:41 AM UTC.', meta(r.html, 'description'));
check('og:title', meta(r.html, 'og:title') === '6 Nissan Xterra set out in junkyards this week', meta(r.html, 'og:title'));
check('first paragraph: count, yards, states, data time', text(r.html).includes('In the last 7 days, 6 Nissan Xterra set out at 5 self-service junkyards in 2 states and 1 Canadian province. 1,078 are on the lots right now. Inventory as of Nov 13, 7:41 AM UTC'));
const ld = ldBlocks(r.html);
check('JSON-LD: BreadcrumbList + ItemList only', ld.map((b) => b['@type']).join() === 'BreadcrumbList,ItemList' && !FORBIDDEN_LD.test(r.html), ld.map((b) => b['@type']).join());
check('breadcrumb: landed > make > model', ld[0].itemListElement.map((e) => e.item).join() === 'https://yardscout.io/landed,https://yardscout.io/landed/nissan,https://yardscout.io/landed/nissan/xterra');
check('ItemList: the 6 cars, car URLs', ld[1].numberOfItems === 6 && ld[1].itemListElement.every((e) => e.url.startsWith('https://yardscout.io/car/')));
// State-first order: Alberta, Arizona, Missouri, then the code with no name last.
const order = [...r.html.matchAll(/<div class="section" id="st-([a-z-]+)">([^<]*)</g)].map((m) => m[2].trim());
check('states A to Z by name, unknown code last', order.join('|') === 'Alberta|Arizona|Missouri|ZZ', order.join('|'));
check('state heading counts', r.html.includes('Arizona <span>· 3 set out · 2 yards</span>') && r.html.includes('Missouri <span>· 1 set out · 1 yard</span>'));
const az = r.html.slice(r.html.indexOf('id="st-az"'), r.html.indexOf('id="st-mo"'));
const azYards = [...az.matchAll(/<div class="yardh"><a href="([^"]+)">([^<]*)<\/a>/g)].map((m) => m[2]);
check('within a state, yards by newest set-out first', azYards.join('|') === 'Pick-n-Pull - Phoenix|LKQ &lt;Mesa&gt; &amp; Co', azYards.join('|'));
const phx = [...az.matchAll(/<li><a href="https:\/\/yardscout\.io\/car\/([^"]+)">/g)].map((m) => m[1]);
check('within a yard, newest car first', phx.slice(0, 2).join() === '5N1AN08U05C000002,ipull-123', phx.join());
check('yard names are escaped and link to /yard/', az.includes('href="https://yardscout.io/yard/lkq-mesa-and-co"') && !r.html.includes('<Mesa>'));
check('jump list of states', /Jump to: <a href="#st-ab">Alberta 1<\/a> · <a href="#st-az">Arizona 3<\/a>/.test(r.html));
const line = (key) => (r.html.match(new RegExp(`<li><a href="https://yardscout.io/car/${key}">[\\s\\S]*?</li>`)) || [''])[0];
check('4x4 in bold, trim word when known', line('5N1AN08W08C000001').includes('2008 Nissan Xterra <strong>4x4</strong> <span class="trimw">Off-Road</span>'), line('5N1AN08W08C000001'));
check('row and set-out date on the line', /Row 25<br>[A-Z][a-z]{2} \d+, \d{4}/.test(line('5N1AN08W08C000001')));
check('2WD plain', line('5N1AN08U05C000002').includes('2005 Nissan Xterra 2WD</a>'), line('5N1AN08U05C000002'));
check('AWD plain', line('ipull-123').includes('2002 Nissan Xterra AWD</a>'));
check('drive and trim left out when unknown', line('5N1AN0NU0BC000003').includes('2011 Nissan Xterra</a>') && !/4x4|2WD|AWD|trimw/.test(line('5N1AN0NU0BC000003')));
check('no row → no "Row" text', !line('5N1AN08U05C000002').includes('Row'));
const lots = r.html.slice(r.html.indexOf('id="on-lots"'));
check('on the lots now: total and regions', lots.startsWith('id="on-lots">On the lots now <span>· 1,078 in 3 states and 1 Canadian province</span>'), lots.slice(0, 120));
check('on the lots table by state, with this week beside it', lots.includes('<td><a href="https://yardscout.io/junkyards/arizona">Arizona</a></td><td class="num">56</td><td class="num">3</td>') && lots.includes('Texas</a></td><td class="num">166</td><td class="num">0</td>'));
check('CTA: the app deep link for this model', r.html.includes('href="https://yardscout.io/#cars=Nissan|Xterra">See every Xterra near you</a>'));
check('CTA: watch link for this model', r.html.includes('href="https://yardscout.io/#watch=Nissan|Xterra"'));
check('stores line', r.html.includes('Arrival alerts live in the app'));
check('honest note: call ahead, VIN-only drive/trim', /call the yard before a long drive/.test(r.html) && /left out when the VIN does not say/.test(r.html));
check('links up to the make, across to siblings, to the state hub', r.html.includes('href="https://yardscout.io/landed/nissan">All Nissan arrivals this week') && r.html.includes('href="https://yardscout.io/landed/nissan/frontier">Frontier') && r.html.includes('href="https://yardscout.io/junkyards"'));
check('no parts, prices or fitment', !/\$\d|price list|fits |fitment|alternator/i.test(text(r.html)));
// Every internal link on the page answers 200 (anchors and app deep links aside).
const internal = [...new Set([...r.html.matchAll(/href="https:\/\/yardscout\.io(\/[^"#]*)"/g)].map((m) => m[1]))]
  .filter((p) => p !== '/' && !p.startsWith('/styles') && !/\.(png|ico)/.test(p) && !p.startsWith('/open'));
const broken = [];
for (const p of internal) {
  if (p.startsWith('/car/') && !SHARD.vehicles.some((v) => p.endsWith('/' + (v[1] || v[0])))) continue;   // cars outside the API fixture
  const x = await get(p);
  if (x.status !== 200) broken.push(`${p} ${x.status}`);
}
check(`internal links resolve (${internal.length} checked)`, !broken.length, broken.join(', '));

/* ---------- zero arrivals ---------- */
r = await get('/landed/nissan/frontier');
check('zero-arrival page → 200 and says so', r.status === 200 && h1s(r.html)[0] === 'Nissan Frontier junkyard inventory: none set out this week, 900 on the lots', h1s(r.html)[0]);
check('zero-arrival: lots table still there', r.html.includes('id="on-lots"') && r.html.includes('>500<'));
check('zero-arrival: title', titleOf(r.html) === 'Nissan Frontier junkyard inventory: 900 on self-service lots — YardScout' || titleOf(r.html) === 'Nissan Frontier junkyard inventory: 900 on the lots', titleOf(r.html));
check('zero-arrival: no ItemList', ldBlocks(r.html).map((b) => b['@type']).join() === 'BreadcrumbList');
check('trailing slash and case are accepted', (await get('/landed/Nissan/Xterra/')).status === 200);

/* ---------- titles ---------- */
check('fitTitle: first that fits', fitTitle(['x'.repeat(70), 'short', 'shorter']) === 'short');
check('fitTitle: none fits → last, whole', fitTitle(['a'.repeat(80), 'b'.repeat(70)]) === 'b'.repeat(70));
const allTitles = [];
for (const p of ['/landed/nissan/xterra', '/landed/nissan/frontier']) allTitles.push(titleOf((await get(p)).html));
check('titles <= 65 where the count allows', allTitles.every((t) => t.length <= 65), allTitles.join(' | '));
check('titles never end mid-word or with an ellipsis', allTitles.every((t) => !/…|\.\.\.$/.test(t) && /(\w|YardScout|lots)$/.test(t)));

/* ---------- 404 / 503 / holding ---------- */
r = await get('/landed/nissan/nope');
check('unknown model → 404 noindex, links the make and its models', r.status === 404 && meta(r.html, 'robots') === 'noindex' && r.html.includes('href="https://yardscout.io/landed/nissan/xterra"'), r.status);
r = await get('/landed/yugo/gv');
check('unknown make → 404 noindex', r.status === 404 && meta(r.html, 'robots') === 'noindex', r.status);
r = await get('/landed/nissan/%E0%A4%A');
check('bad percent-encoding → 404, no crash', r.status === 404, r.status);
mode = 'down';
r = await get('/landed/nissan/xterra');
check('data host down → 503 noindex "briefly unavailable"', r.status === 503 && meta(r.html, 'robots') === 'noindex' && r.html.includes('Briefly unavailable') && /max-age=60/.test(r.headers.get('cache-control')), r.status);
r = await get('/landed/nissan');
check('data down: make page still renders from landed.json', r.status === 200 && !r.html.includes('/landed/nissan/xterra'), r.status);
mode = 'none';
r = await get('/landed/nissan/xterra');
check('before the first scan: holding page, 503 noindex, links the make page', r.status === 503 && meta(r.html, 'robots') === 'noindex' && r.html.includes('not built yet') && r.html.includes('href="https://yardscout.io/landed/nissan"'), r.status);
r = await get('/sitemap.xml');
check('before the first scan: sitemap still 200, no model URLs', r.status === 200 && !r.html.includes('/landed/nissan/'), r.status);
mode = 'ok';

/* ---------- wiring ---------- */
r = await get('/sitemap.xml');
const lastmod = Object.fromEntries([...r.html.matchAll(/<url><loc>https:\/\/yardscout\.io([^<]*)<\/loc>(?:<lastmod>([^<]*)<\/lastmod>)?<\/url>/g)].map((m) => [m[1], m[2] || '']));
check('sitemap: every model page with the scan as lastmod', ['/landed/nissan/xterra', '/landed/nissan/frontier', '/landed/mercedes-benz/grand-marquis-super-long-name-edition'].every((p) => lastmod[p] === SCAN), JSON.stringify(Object.keys(lastmod).filter((k) => k.startsWith('/landed'))));
r = await get('/landed/nissan');
check('make page: model headings link to model pages', r.html.includes('<div class="section"><a href="https://yardscout.io/landed/nissan/xterra">Nissan Xterra</a>'), '');
check('make page: model without a page stays plain text', r.html.includes('<div class="section">Nissan Altima <span>'));
check('make page: grid of every model page', r.html.includes('Every Nissan model with its own page <span>· 2</span>'));
r = await get('/landed');
check('hub: top models this week link to model pages, zero-week models left out', r.html.includes('Top models this week') && r.html.includes('href="https://yardscout.io/landed/nissan/xterra">Nissan Xterra<small>6 this week') && !r.html.includes('/landed/nissan/frontier"'));
r = await get('/car/5N1AN08W08C000001');
check('car page links to its model page', r.status === 200 && r.html.includes('href="https://yardscout.io/landed/nissan/xterra">Every Nissan Xterra set out this week, by state</a>'), r.status);
r = await get('/car/2');
check('car page of a model without a page: no model link', r.status === 200 && !r.html.includes('/landed/nissan/altima'), r.status);
r = await get('/yard/pick-n-pull-phoenix');
check('yard page: model tile links to the model page', r.html.includes('<a href="https://yardscout.io/landed/nissan/xterra">Nissan Xterra<small>'), '');

console.log(failures ? `\n${failures} FAILED` : '\nALL PASS');
process.exit(failures ? 1 : 0);
