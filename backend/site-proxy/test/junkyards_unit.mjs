/* Unit test for the server-rendered pages (src/share.js) through the Worker's
 * own router (src/index.js) — fetch is stubbed with fixture data, nothing
 * leaves the machine. Started as the /junkyards test; it now also holds the
 * search-engine rules every rendered page must keep (ops/seo.md): one <h1>,
 * title formats, JSON-LD types, sitemap, Last-Modified, internal links.
 * Run: node test/junkyards_unit.mjs   (from backend/site-proxy/) */
import worker from '../src/index.js';
import { buildJunkyardIndex } from '../src/share.js';

let failures = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + detail}`); if (!ok) failures++; };

const today = new Date().toISOString().slice(0, 10);
const daysAgo = (n) => new Date(Date.now() - n * 86400000).toISOString().slice(0, 10);
// junkyards.json rows: [location, pageCity, state, lat, lng, carsOnLot, setOutLast7Days]
const JUNKYARDS = {
  scrapedAt: '2026-10-30T11:58:45Z', days: 7,
  yards: [
    ['Pick-n-Pull - Dallas South', 'Dallas', 'TX', 32.70, -96.80, 100, 7],
    ["Bob's <Pull> & Save", 'Dallas', 'TX', 32.75, -96.85, 50, 3],
    ['Grand Prairie U-Pull', 'Grand Prairie', 'TX', 32.74, -97.00, 40, 2],
    ['Houston Dateless Yard', 'Houston', 'TX', 29.76, -95.37, 70, 0],
    ['UAPI - Texarkana', 'Wake Village', 'TX', 33.42, -94.11, 30, 1],
    ['Texarkana Pull-It', 'Texarkana', 'AR', 33.44, -94.04, 20, 2],
    ['Duke City U-Pull', 'Albuquerque', 'NM', 35.08, -106.65, 60, 5],
    ['Calgary Pick-a-Part', 'Calgary', 'AB', 51.05, -114.07, 80, 4],
    ['Mystery Yard', 'Nowhere', 'ZZ', 0, 0, 999, 99],
    // 15 miles north of Seattle: the metro has no yard of its own, so it
    // gets a "near Seattle" alias page (METRO_ALIASES in share.js).
    ['Pick-n-Pull - Lynnwood', 'Lynnwood', 'WA', 47.8279, -122.3053, 55, 6],
  ],
  newest: [
    [[2012, 'Honda', 'Civic', '12', today, '1HGFB2F50CL000001'], [2009, 'Ford', 'F-150', '3', daysAgo(2), '1FTRF12W09K000002']],
    [[2015, 'Toyota', 'Camry <script>alert(1)</script>', 'A&B', daysAgo(1), 'stock-77']],
    [[2004, 'Chevrolet', 'Tahoe', '9', today, '1GNEK13Z04R000003']],
    [],
    [[2010, 'Nissan', 'Altima', '1', today, '1N4AL2AP0AN000004']],
    [[2011, 'Kia', 'Soul', '2', today, 'KNDJT2A20B7000005']],
    [[2008, 'Subaru', 'Outback', '4', today, '4S4BP61C087000006']],
    [[2013, 'Dodge', 'Ram 1500', '5', today, '1C6RD7GT0DS000007']],
    [],
    [[2006, 'Mazda', 'Mazda3', '7', today, 'JM1BK32F061000008']],
  ],
  stateMakes: { TX: [['Ford', 6], ['Honda', 4]], NM: [['Subaru', 5]], AB: [['Dodge', 4]] },
};
// landed.json rows: [year, make, model, row, dateAdded, key, yardIdx]
const LANDED = {
  scrapedAt: JUNKYARDS.scrapedAt, days: 7,
  yards: JUNKYARDS.yards.map(([loc, city, st, , , n, w]) => [loc, city, st, n, w]),
  makes: {
    Ford: { total: 30, recentCount: 6, recent: [
      [2009, 'Ford', 'F-150', '3', daysAgo(2), '1FTRF12W09K000002', 0], [2010, 'Ford', 'Focus', '8', daysAgo(1), '1FAHP3FN0AW000010', 0],
      [2011, 'Ford', 'Fusion', '9', today, '3FAHP0HA0BR000011', 2], [2007, 'Ford', 'Escape', '2', today, '1FMYU03147K000012', 6],
    ] },   // 4 rows carried of 6 this week: the scan capped the list
    Lexus: { total: 25, recentCount: 2, recent: [[2005, 'Lexus', 'ES 330', '4', today, 'JTHBA30G055000013', 7], [2004, 'Lexus', 'RX 330', '6', today, 'JTJGA31U740000014', 9]] },
    Yugo: { total: 2, recentCount: 2, recent: [] },   // under 20 on the lots: not listed, still counted
  },
};
// yardscout-api fixtures. Inventory rows follow backend/src/inventory.js:
// [id, vin, year, make, model, row, dateAdded, yard, partSet, maxValue, premium]
const YARD_FIELDS = ['location', 'city', 'state', 'lat', 'lng', 'avgLifespanDays', 'lifespanBasis'];
const DIRECTORY = { scrapedAt: JUNKYARDS.scrapedAt, yardFields: YARD_FIELDS, yards: JUNKYARDS.yards.map((y, i) => [...y.slice(0, 5), i === 0 ? 45 : null, i === 0 ? 'yard' : null]) };
const SHARDS = {
  0: { vpic: { 101: ['EX', 'usable', '', 'FWD/Front-Wheel Drive'] }, vehicles: [
    [101, '1HGFB2F50CL000001', 2012, 'Honda', 'Civic', '12', today, 0, 0, 0, 0],
    [102, '1FTRF12W09K000002', 2009, 'Ford', 'F-150', '3', daysAgo(2), 0, 0, 0, 0],
    [103, '1FTRF12W08K000003', 2008, 'Ford', 'F-150', '4', daysAgo(20), 0, 0, 0, 0],
    [104, '', 2001, 'Ford', 'Ranger <b>', '5', daysAgo(30), 0, 0, 0, 0],
    [105, '2T1BR32E54C000005', 2004, 'Toyota', 'Corolla', '6', daysAgo(40), 0, 0, 0, 0],
  ] },
  3: { vpic: {}, vehicles: [[301, '', 1999, 'Chevrolet', 'Malibu', '', '', 3, 0, 0, 0], [302, '', 2002, 'Chevrolet', 'Impala', '', '', 3, 0, 0, 0]] },
  // A big lot for the "top 12 makes / top 15 models" caps: 14 makes with 14,
  // 13, ... 1 cars, each alternating two models: 105 cars, 27 models.
  6: { vpic: {}, vehicles: Array.from({ length: 14 }, (_, k) => Array.from({ length: 14 - k }, (_, n) =>
    [6000 + k * 100 + n, '', 1990 + n, `Make${String(k + 1).padStart(2, '0')}`, n % 2 ? 'Beta' : 'Alpha', String(k), daysAgo(30 + n), 6, 0, 0, 0])).flat() },
};
// Pick-n-Pull's price file as the scraper saves it: the till's item list,
// including rows that are not a part price.
const PNP_PRICES = [
  { description: 'ALTERNATOR', price: '32.99', corePrice: '9.99' }, { description: 'ALTERNATOR BRACKET', price: '5.00', corePrice: '0.00' },
  { description: 'STARTER', price: '30.99', corePrice: '9.99' }, { description: 'STARTER SOLENOID', price: '11.99', corePrice: '0.00' },
  { description: 'HOOD - CAR', price: '64.99', corePrice: '0.00' }, { description: 'HOOD LATCH', price: '9.99', corePrice: '0.00' },
  { description: 'RADIATOR  (W/O SHROUD)', price: '69.99', corePrice: '0.00' }, { description: 'ENGINE (COMPLETE)', price: '299.99', corePrice: '50.00' },
  { description: 'TRIM <b>MOLDING</b>', price: '0.79', corePrice: '0.00', per: 'Inches' },
  { description: 'MISCELLANEOUS', price: '0.00', corePrice: '0.00' }, { description: 'CORE - ALUM WHEEL', price: '0.00', corePrice: '53.99' },
  { description: 'AIR BAGWE DO NOT SELL\r\n            AIR CLEANER', price: '14.00', corePrice: '0.00' },
  { description: 'CATALYTIC CONVERTER', price: '99.00', corePrice: '0.00' }, { description: 'Reimbursement', price: '5662.80', corePrice: '0.00' },
];
let dataDown = true;
globalThis.fetch = async (u) => {
  u = String(u);
  const json = (o, status = 200) => new Response(JSON.stringify(o), { status, headers: { 'content-type': 'application/json' } });
  if (u.endsWith('/data/picknpull_pricing.json')) return json(PNP_PRICES);
  if (u.endsWith('/data/junkyards.json')) return dataDown ? new Response('down', { status: 502 }) : json(JUNKYARDS);
  if (u.endsWith('/data/landed.json')) return json(LANDED);
  if (u.endsWith('/data/yards_added.json')) return json([]);
  if (u.endsWith('/v1/yards')) return json(DIRECTORY);
  let m = u.match(/\/v1\/inventory\/shard\/(\d+)$/);
  if (m && m[1] === '7') return new Response('boom', { status: 500 });   // Calgary: the API fails for this lot
  if (m) return SHARDS[m[1]] ? json(SHARDS[m[1]]) : json({ vehicles: [], vpic: {} });
  m = u.match(/\/v1\/vehicles\/([^/]+)$/);
  if (m) {
    const row = SHARDS[0].vehicles.find((r) => r[1] === m[1] || String(r[0]) === m[1]);
    if (!row) return json({ error: 'not_found' }, 404);
    const [id, vin, year, make, model, rowNo, dateAdded] = row; const y = DIRECTORY.yards[0];
    return json({ scrapedAt: DIRECTORY.scrapedAt, tier: 'free', vehicle: { id, vin, year, make, model, row: rowNo, dateAdded, yard: 0 }, vpic: SHARDS[0].vpic[id] || null, yard: { id: 0, location: y[0], city: y[1], state: y[2], lat: y[3], lng: y[4] } });
  }
  if (u.startsWith('https://benvuolo.github.io/yardscout/')) return new Response('Not Found', { status: 404 });
  throw new Error('unexpected fetch ' + u);
};
const get = async (path, host = 'yardscout.io') => {
  const r = await worker.fetch(new Request(`https://${host}${path}`, { redirect: 'manual' }), {});
  return { status: r.status, headers: r.headers, html: await r.text() };
};
const canonical = (html) => (html.match(/<link rel="canonical" href="([^"]+)">/) || [])[1];
const section = (html, title) => { const i = html.indexOf(title); return i < 0 ? '' : html.slice(i, html.indexOf('<div class="section">', i + 1) >>> 0); };
const titleOf = (html) => (html.match(/<title>([^<]*)<\/title>/) || [])[1];
const meta = (html, name) => (html.match(new RegExp(`<meta (?:name|property)="${name}" content="([^"]*)"`)) || [])[1];
const h1s = (html) => [...html.matchAll(/<h1[\s>][\s\S]*?<\/h1>/g)].map((m) => m[0].replace(/<[^>]+>/g, ''));
/** Every JSON-LD block on a page, parsed (throws if one is not valid JSON). */
const ldBlocks = (html) => [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)].map((m) => JSON.parse(m[1]));
const ldOf = (html, type) => ldBlocks(html).find((b) => b['@type'] === type);
// YardScout lists cars in yards; it does not sell them and has 4 ratings.
const FORBIDDEN_LD = /"@type":\s*"(Vehicle|Car|Product|Offer|AggregateOffer|AggregateRating|Review)"|aggregateRating|"offers"/;
const LAST_MODIFIED = 'Fri, 30 Oct 2026 11:58:45 GMT';   // JUNKYARDS.scrapedAt as an HTTP date
/** The rules every indexable rendered page keeps. */
function seoChecks(label, r, { h1, ld }) {
  const heads = h1s(r.html);
  check(`${label}: exactly one <h1>, and it is the page's headline`, heads.length === 1 && heads[0] === h1, JSON.stringify(heads));
  check(`${label}: wordmark is not a heading`, r.html.includes('<p class="wm-name">') && !/<h1>\s*<a[^>]*>Yard/.test(r.html));
  let types = null; try { types = ldBlocks(r.html).map((b) => b['@type']); } catch (e) { types = 'unparseable: ' + e.message; }
  check(`${label}: JSON-LD parses and is ${ld.join(' + ') || 'absent'}`, Array.isArray(types) && types.join() === ld.join(), String(types));
  check(`${label}: no Vehicle/Product/Offer/rating markup`, !FORBIDDEN_LD.test(r.html));
  check(`${label}: Last-Modified is the scan time`, r.headers.get('last-modified') === LAST_MODIFIED, r.headers.get('last-modified'));
  check(`${label}: indexable`, meta(r.html, 'robots') === 'index,follow', meta(r.html, 'robots'));
}

// Data file unreachable on a cold isolate → honest 503, not an empty page.
let r = await get('/junkyards/texas');
check('data down → 503 noindex', r.status === 503 && /noindex/.test(r.html), r.status);
dataDown = false;

r = await get('/junkyards');
check('/junkyards → 200', r.status === 200, r.status);
check('/junkyards canonical', canonical(r.html) === 'https://yardscout.io/junkyards', canonical(r.html));
check('index: real total yards (unknown state code skipped)', /<span class="label">Yards<\/span><span class="value">9<\/span>/.test(r.html));
check('index: real total cars', r.html.includes('<span class="value">505</span>'));
seoChecks('index', r, { h1: 'Self-service junkyards near you, by state', ld: ['ItemList'] });
check('index: title carries the real counts', titleOf(r.html) === 'Self-service junkyards by state: 9 yards with live inventory, 505 cars — YardScout', titleOf(r.html));
check('index: ItemList is the state pages it lists', ldOf(r.html, 'ItemList').numberOfItems === 5 && ldOf(r.html, 'ItemList').itemListElement.some((e) => e.url === 'https://yardscout.io/junkyards/new-mexico' && e.position >= 1));
check('index: links the other hubs', r.html.includes('href="https://yardscout.io/yards"') && r.html.includes('href="https://yardscout.io/landed"'));
check('index: Texas with 5 yards · 290 cars', /junkyards\/texas">Texas<small>5 yards · 290 cars<\/small>/.test(r.html));
check('index: multi-word state slug', r.html.includes('href="https://yardscout.io/junkyards/new-mexico"'));
check('index: provinces under Canada', /Canada <span>· 1 province<\/span><\/div><ul class="grid"><li><a href="https:\/\/yardscout.io\/junkyards\/alberta">/.test(r.html));
check('index: unknown state code not listed', !r.html.includes('Mystery Yard') && !r.html.includes('/junkyards/zz'));
check('index: scan time shown', r.html.includes('Oct 30, 11:58 AM UTC'));
check('index: cacheable', /max-age=900/.test(r.headers.get('cache-control') || ''));

r = await get('/junkyards/texas');
check('/junkyards/texas → 200', r.status === 200, r.status);
check('state canonical', canonical(r.html) === 'https://yardscout.io/junkyards/texas', canonical(r.html));
check('state: yard count', /<span class="label">Yards<\/span><span class="value">5<\/span>/.test(r.html));
check('state: cars on the lots', r.html.includes('<span class="value">290</span>'));
check('state: new this week', r.html.includes('<span class="value accent">13</span>'));
check('state: top makes this week', r.html.includes('Ford<small>6 set out in TX</small>') && r.html.includes('Honda<small>4 set out in TX</small>'));
check('state: Grand Prairie grouped with Dallas (within 30 mi)', r.html.includes('Dallas · Grand Prairie <span>· 3 yards · 190 cars</span>'));
check('state: city page links', ['dallas', 'grand-prairie', 'houston', 'wake-village'].every((c) => r.html.includes(`href="https://yardscout.io/junkyards/texas/${c}"`)));
check('state: yard links to /yard/<slug>', r.html.includes('href="https://yardscout.io/yard/pick-n-pull-dallas-south"'));
check('state: dateless yard says so instead of "0 this week"', /Houston Dateless Yard.*?no set-out dates/.test(r.html));
check('state: no other state\'s yards', !r.html.includes('Duke City') && !r.html.includes('Texarkana Pull-It'));
check('state: yard name escaped', r.html.includes('Bob&#39;s &lt;Pull&gt; &amp; Save') && !r.html.includes('<Pull>'));
check('state: breadcrumb JSON-LD', r.html.includes('"@type":"BreadcrumbList"'));
seoChecks('state', r, { h1: 'Self-service junkyards in Texas', ld: ['BreadcrumbList', 'ItemList'] });
check('state: title carries the real counts', titleOf(r.html) === 'Junkyards in Texas: 5 self-service yards with live inventory (290 cars) — YardScout', titleOf(r.html));
check('state: ItemList is its 5 yard pages', ldOf(r.html, 'ItemList').numberOfItems === 5 && ldOf(r.html, 'ItemList').itemListElement.every((e) => e.url.startsWith('https://yardscout.io/yard/')));
check('state: JSON-LD cannot be closed by a yard name', !/<script type="application\/ld\+json">[^<]*<Pull>/.test(r.html) && ldOf(r.html, 'ItemList').itemListElement.some((e) => e.name === "Bob's <Pull> & Save"));
check('state: breadcrumb ends on this page', ldOf(r.html, 'BreadcrumbList').itemListElement.map((e) => e.item).join() === 'https://yardscout.io/junkyards,https://yardscout.io/junkyards/texas');

r = await get('/junkyards/texas/dallas');
check('/junkyards/texas/dallas → 200', r.status === 200, r.status);
check('city canonical', canonical(r.html) === 'https://yardscout.io/junkyards/texas/dallas', canonical(r.html));
check('city: title', titleOf(r.html) === 'Junkyards in Dallas, TX: 2 self-service yards with live inventory (150 cars) — YardScout', titleOf(r.html));
seoChecks('city', r, { h1: 'Self-service junkyards in Dallas, TX', ld: ['BreadcrumbList', 'ItemList'] });
check('city: ItemList is the yards shown (2 in the city + 1 nearby)', ldOf(r.html, 'ItemList').numberOfItems === 3 && ldOf(r.html, 'ItemList').name === 'Self-service junkyards in and near Dallas, TX');
check('city: links up to its state page', r.html.includes('href="https://yardscout.io/junkyards/texas">All junkyards in Texas</a>'));
check('city: in-city yard count + cars + week', /<span class="label">Yards<\/span><span class="value">2<\/span>/.test(r.html) && r.html.includes('<span class="value">150</span>') && r.html.includes('<span class="value accent">10</span>'));
const nearBlock = section(r.html, 'Within 30 miles');
check('city: nearby yard listed with distance', /Grand Prairie U-Pull.*?\d+ mi/.test(nearBlock), nearBlock.slice(0, 200));
check('city: far yard not listed', !r.html.includes('Houston Dateless Yard'));
check('city: arrivals link to /car/<key>', r.html.includes('href="https://yardscout.io/car/1HGFB2F50CL000001"') && r.html.includes('href="https://yardscout.io/car/1GNEK13Z04R000003"'));
const order = ['1HGFB2F50CL000001', '1GNEK13Z04R000003', 'stock-77', '1FTRF12W09K000002'].map((k) => r.html.indexOf('/car/' + k));
check('city: arrivals newest first', order.every((p, i) => p > 0 && (i === 0 || p > order[i - 1])), order.join(','));
check('city: arrival row + set-out date', r.html.includes('Row 12<br>') && r.html.includes('Row A&amp;B<br>'));
check('city: model escaped (no script injection)', !r.html.includes('<script>alert') && r.html.includes('Camry &lt;script&gt;alert(1)&lt;/script&gt;'));
check('city: zip CTA', r.html.includes('Search near your zip'));
check('city: scan time + coverage caveat', r.html.includes('Oct 30, 11:58 AM UTC') && r.html.includes('only tracks self-service yards that post their inventory online'));

r = await get('/junkyards/texas/houston');
check('dateless city: no arrivals list, says why', r.status === 200 && r.html.includes("doesn't publish set-out dates"));

r = await get('/junkyards/texas/wake-village');
check('nearby crosses a state line (Texarkana, AR)', /Texarkana Pull-It<span class="where">Texarkana, AR · \d+ mi/.test(r.html));

r = await get('/junkyards/alberta/calgary');
check('province city page → 200', r.status === 200 && r.html.includes('Self-service junkyards in Calgary, AB'), r.status);
r = await get('/junkyards/new-mexico/albuquerque/');
check('trailing slash → 200, canonical without it', r.status === 200 && canonical(r.html) === 'https://yardscout.io/junkyards/new-mexico/albuquerque', canonical(r.html));
r = await get('/junkyards/Texas/Dallas');
check('mixed case → 200, lowercase canonical', r.status === 200 && canonical(r.html) === 'https://yardscout.io/junkyards/texas/dallas');

r = await get('/junkyards/tx/dallas');
check('postal code → 301 to the slug', r.status === 301 && r.headers.get('location') === 'https://yardscout.io/junkyards/texas/dallas', `${r.status} ${r.headers.get('location')}`);
for (const p of ['/junkyards/narnia', '/junkyards/zz', '/junkyards/oregon', '/junkyards/texas/narnia', '/junkyards/texas/albuquerque', '/junkyards/%E0%A4%A']) {
  r = await get(p);
  check(`${p} → 404 noindex`, r.status === 404 && /content="noindex"/.test(r.html), r.status);
}
r = await get('/junkyards/texas/dallas/extra');
check('three segments → not a junkyards page (falls through to 404)', r.status === 404);

/* ---------- metro aliases: Seattle has no tracked yard of its own ---------- */
r = await get('/junkyards/washington/seattle');
check('alias: /junkyards/washington/seattle → 200', r.status === 200, r.status);
seoChecks('alias', r, { h1: 'Self-service junkyards near Seattle, WA', ld: ['BreadcrumbList', 'ItemList'] });
check('alias: title says "near" with the real counts', titleOf(r.html) === 'Junkyards near Seattle, WA: 1 self-service yard within 30 miles, live inventory (55 cars) — YardScout', titleOf(r.html));
check('alias: says no yard is inside the city', r.html.includes('YardScout tracks no self-service yard inside Seattle itself'));
check('alias: lists the suburb yard with its distance', /Pick-n-Pull - Lynnwood<span class="where">Lynnwood, WA · 1[0-9] mi/.test(r.html));
check('alias: no "In Seattle" yard block', !r.html.includes('In Seattle <span>'));
check('alias: canonical is its own URL', canonical(r.html) === 'https://yardscout.io/junkyards/washington/seattle', canonical(r.html));
r = await get('/junkyards/washington');
check('alias: linked from its state page, not shown as a metro group', r.html.includes('href="https://yardscout.io/junkyards/washington/seattle">Seattle area</a>') && !r.html.includes('<div class="section">Seattle'));
{
  const withCity = buildJunkyardIndex({ yards: [['Emerald City Pull', 'Seattle', 'WA', 47.6, -122.33, 10, 1]], newest: [[]] });
  check('alias: a real yard in the city makes it a normal city page', withCity.states.get('washington').cities.get('seattle').alias !== true && withCity.states.get('washington').cities.get('seattle').yards.length === 1);
  const farAway = buildJunkyardIndex({ yards: [['Spokane Pull', 'Spokane', 'WA', 47.66, -117.43, 10, 1]], newest: [[]] });
  check('alias: not built when no tracked yard is within 30 miles', !farAway.states.get('washington').cities.has('seattle'));
  check('alias: not built for a state with no tracked yards', !buildJunkyardIndex(JUNKYARDS).states.has('nevada'));
}

/* ---------- sitemap ---------- */
r = await get('/sitemap-yards.xml');
const locs = [...r.html.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);
const lastmod = Object.fromEntries([...r.html.matchAll(/<url><loc>([^<]+)<\/loc>(?:<lastmod>([^<]+)<\/lastmod>)?<\/url>/g)].map((m) => [m[1].replace('https://yardscout.io', ''), m[2] || '']));
check('sitemap 200', r.status === 200, r.status);
check('sitemap has /junkyards, states and cities', ['/junkyards', '/junkyards/texas', '/junkyards/texas/dallas', '/junkyards/texas/grand-prairie', '/junkyards/new-mexico/albuquerque', '/junkyards/alberta/calgary', '/junkyards/arkansas/texarkana']
  .every((p) => locs.includes('https://yardscout.io' + p)));
check('sitemap: one URL per state/city (1 + 5 states + 8 cities + 1 metro alias)', locs.filter((l) => l.includes('/junkyards')).length === 15, locs.filter((l) => l.includes('/junkyards')).length);
check('sitemap keeps the existing yard + landed URLs', locs.includes('https://yardscout.io/yards') && locs.includes('https://yardscout.io/yard/pick-n-pull-dallas-south'));
check('sitemap: home page, hubs, make pages and the metro alias are in', ['/', '/yards', '/landed', '/junkyards', '/landed/ford', '/landed/lexus', '/junkyards/washington/seattle'].every((p) => p in lastmod), Object.keys(lastmod).join(' '));
check('sitemap: makes with under 20 cars on the lots are left out', !('/landed/yugo' in lastmod));
check('sitemap: no car pages', !locs.some((l) => l.includes('/car/')));
const undated = (p) => p === '/' || p.startsWith('/prices');   // no scan time to quote for these
check('sitemap: every scan-driven URL has <lastmod> = the scan time', Object.entries(lastmod).every(([p, lm]) => (undated(p) ? lm === '' : lm === '2026-10-30T11:58:45Z')), JSON.stringify(Object.entries(lastmod).filter(([p, lm]) => !undated(p) && lm !== '2026-10-30T11:58:45Z')));
check('sitemap: price pages for chains with a tracked yard only, no lastmod (the price files carry no date)', lastmod['/prices'] === '' && lastmod['/prices/pick-n-pull'] === '' && !('/prices/tear-a-part' in lastmod) && Object.keys(lastmod).filter((p) => p.startsWith('/prices')).length === 2, Object.keys(lastmod).filter((p) => p.startsWith('/prices')).join(' '));
check('sitemap: home page has no guessed lastmod', lastmod['/'] === '');
check('sitemap: no <changefreq>', !r.html.includes('changefreq'));
check('sitemap: no duplicate URLs', new Set(locs).size === locs.length);
check('sitemap: valid XML shell + Last-Modified', r.html.startsWith('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">') && r.html.endsWith('</urlset>') && /application\/xml/.test(r.headers.get('content-type')) && r.headers.get('last-modified') === LAST_MODIFIED);
const sitemapBody = r.html;
r = await get('/sitemap.xml');
check('/sitemap.xml → 200 with the same body', r.status === 200 && r.html === sitemapBody, r.status);

/* ---------- /yards ---------- */
r = await get('/yards');
check('/yards links each state to its /junkyards page', r.html.includes('href="https://yardscout.io/junkyards/texas">by city</a>'));
seoChecks('/yards', r, { h1: '10 self-service junkyards with online inventory, by state', ld: ['ItemList'] });
check('/yards: title', titleOf(r.html) === 'Self-service junkyards with online inventory: all 10 yards by state — YardScout', titleOf(r.html));
check('/yards: og:title keeps the share wording', meta(r.html, 'og:title') === '10 self-service junkyards tracked by YardScout', meta(r.html, 'og:title'));
check('/yards: ItemList is every yard page', ldOf(r.html, 'ItemList').numberOfItems === 10 && ldOf(r.html, 'ItemList').itemListElement.some((e) => e.url === 'https://yardscout.io/yard/calgary-pick-a-part'));
check('/yards: states and provinces counted apart', meta(r.html, 'description').startsWith('10 self-service junkyards in 4 states and 1 Canadian province, '), meta(r.html, 'description'));
check('/yards: province named, not shown as its code', r.html.includes('id="AB">Alberta <span>'));

/* ---------- /landed and /landed/<make> ---------- */
r = await get('/landed');
seoChecks('/landed', r, { h1: 'What landed in self-service junkyards this week', ld: [] });
check('/landed: title counts every set-out and only yards that had one', titleOf(r.html) === 'Junkyard new arrivals this week: 10 cars set out at 9 self-service yards, by make — YardScout', titleOf(r.html));
check('/landed: week total on the page is the same figure', r.html.includes('<span class="label">Set out this week</span><span class="value accent">10</span>') && r.html.includes('<span class="label">Yards with arrivals</span><span class="value">9</span>'));
check('/landed: says how many set-outs the make grid leaves out', r.html.includes('2 more set out from makes with fewer than 20 cars on the lots.') && !r.html.includes('/landed/yugo'));
check('/landed: og:title keeps the share wording', meta(r.html, 'og:title') === 'What landed in the junkyards this week');
check('/landed: links the other hubs', r.html.includes('href="https://yardscout.io/junkyards"') && r.html.includes('href="https://yardscout.io/yards"'));

r = await get('/landed/ford');
seoChecks('make', r, { h1: '6 Fords landed in self-service junkyards this week', ld: ['BreadcrumbList'] });
check('make: title', titleOf(r.html) === 'Ford in junkyards: 30 on self-service lots, 6 new this week — YardScout', titleOf(r.html));
check('make: og:title keeps the share wording', meta(r.html, 'og:title') === '6 Fords landed in junkyards this week', meta(r.html, 'og:title'));
check('make: breadcrumb', ldOf(r.html, 'BreadcrumbList').itemListElement.map((e) => e.item).join() === 'https://yardscout.io/landed,https://yardscout.io/landed/ford');
const statesBlock = section(r.html, 'Where they landed');
check('make: links to the state pages where it landed', statesBlock.includes('href="https://yardscout.io/junkyards/texas">Junkyards in Texas<small>3 Ford set out</small>') && statesBlock.includes('href="https://yardscout.io/junkyards/new-mexico">Junkyards in New Mexico<small>1 Ford set out</small>'), statesBlock.slice(0, 300));
check('make: state counts are labelled as covering the rows carried (4 of 6)', statesBlock.includes('newest 4 set-outs'), statesBlock.slice(0, 120));
check('make: no hardcoded lot-life figure', !/about 70 days/.test(r.html));
r = await get('/landed/lexus');
check('make: plural that does not just add an s', h1s(r.html)[0] === '2 Lexuses landed in self-service junkyards this week', h1s(r.html)[0]);
check('make: all of the week carried → state counts are "this week", provinces included', section(r.html, 'Where they landed').includes('· this week') && r.html.includes('href="https://yardscout.io/junkyards/alberta">Junkyards in Alberta<small>1 Lexus set out</small>'));
r = await get('/landed/nope');
check('unknown make → 404 noindex with one <h1> and hub links', r.status === 404 && /content="noindex"/.test(r.html) && h1s(r.html).length === 1 && r.html.includes('href="https://yardscout.io/junkyards"'));
r = await get('/landed/%E0%A4%A');
check('malformed make path → 404, not an exception', r.status === 404, r.status);

/* ---------- /yard/<slug> ---------- */
r = await get('/yard/pick-n-pull-dallas-south');
check('yard → 200', r.status === 200, r.status);
seoChecks('yard', r, { h1: 'Pick-n-Pull - Dallas South inventory', ld: ['BreadcrumbList'] });
check('yard: title is "<Yard> inventory: N cars on the lot, n new this week (City, ST)"', titleOf(r.html) === 'Pick-n-Pull - Dallas South inventory: 5 cars on the lot, 2 new this week (Dallas, TX) — YardScout', titleOf(r.html));
check('yard: og:title keeps the share wording', meta(r.html, 'og:title') === 'What&#39;s at Pick-n-Pull - Dallas South this week', meta(r.html, 'og:title'));
check('yard: description from the same counts, with the top makes', meta(r.html, 'description') === '5 cars on the lot at Pick-n-Pull - Dallas South (Dallas, TX): Ford 3, Honda 1, Toyota 1. 2 set out in the last 7 days. Cars typically last ~45 days here. Live inventory, refreshed every 4 hours.', meta(r.html, 'description'));
check('yard: og:description keeps the share wording', meta(r.html, 'og:description') === '5 cars on the lot at Pick-n-Pull - Dallas South (Dallas, TX), 2 set out in the last 7 days, cars typically last ~45 days here. Live list, refreshed every 4 hours.', meta(r.html, 'og:description'));
check('yard: summary sentence states the lot', r.html.includes('5 cars are on the lot at Pick-n-Pull - Dallas South in Dallas, TX, 2 of them set out in the last 7 days.') && r.html.includes('as of Oct 30, 11:58 AM UTC'));
check('yard: stats (on the lot, new this week, typical stay)', r.html.includes('<span class="label">On the lot</span><span class="value">5</span>') && r.html.includes('<span class="label">New this week</span><span class="value accent">2</span>') && r.html.includes('<span class="value">~45 days</span>'));
const modelsBlock = section(r.html, 'Most common models on this lot');
check('yard: models with counts and model-year span', modelsBlock.includes('<span class="tile">Ford F-150<small>2 cars · 2008–2009</small></span>') && modelsBlock.includes('<span class="tile">Honda Civic<small>1 car · 2012</small></span>') && modelsBlock.includes('· 4 models'), modelsBlock.slice(0, 400));
check('yard: model name escaped', modelsBlock.includes('Ford Ranger &lt;b&gt;<small>1 car · 2001</small>') && !r.html.includes('Ranger <b>'));
check('yard: newest-arrivals list kept (2 cars, newest first)', section(r.html, 'New arrivals: set out in the last 7 days').indexOf('/car/1HGFB2F50CL000001') > 0 && section(r.html, 'New arrivals: set out in the last 7 days').indexOf('/car/1HGFB2F50CL000001') < section(r.html, 'New arrivals: set out in the last 7 days').indexOf('/car/1FTRF12W09K000002'));
check('yard: plain map link from its lat/lng', r.html.includes('<a href="https://www.google.com/maps/search/?api=1&query=32.7%2C-96.8" target="_blank" rel="noopener">Map &#8599;</a>'));
const commonBlock = section(r.html, 'Common part prices here');
check('yard: short common-parts table instead of the full price list', (commonBlock.match(/<tr><td>/g) || []).length === 3 && commonBlock.includes('<td>ALTERNATOR</td><td class="num">$32.99</td><td class="num">$9.99</td>') && commonBlock.includes('<td>STARTER</td>') && commonBlock.includes('<td>HOOD - CAR</td><td class="num">$64.99</td><td class="num"></td>') && commonBlock.includes('· 3 of 9 parts'), commonBlock.slice(0, 500));
check('yard: an accessory row never stands in for the part; no engine row', !commonBlock.includes('BRACKET') && !commonBlock.includes('SOLENOID') && !commonBlock.includes('ENGINE') && !commonBlock.includes('RADIATOR'));
check('yard: links to the full price list page', commonBlock.includes('<a href="https://yardscout.io/prices/pick-n-pull">Full Pick-n-Pull price list</a> (9 parts)') && r.html.includes('<a href="https://yardscout.io/prices/pick-n-pull">Pick-n-Pull price list</a>'));
check('yard: no filter box, no 472-row list', !r.html.includes('id="pl-q"') && !r.html.includes('id="pl-rows"') && !r.html.includes('tap to open'));
check('yard: call to action unchanged', r.html.includes(`<a class="btn btn-primary" href="https://yardscout.io/">Search this yard in YardScout</a>`) && r.html.includes('Alert me when a car I want lands here'));
check('yard: breadcrumb Junkyards > State > City > Yard', ldOf(r.html, 'BreadcrumbList').itemListElement.map((e) => e.item).join() === 'https://yardscout.io/junkyards,https://yardscout.io/junkyards/texas,https://yardscout.io/junkyards/texas/dallas,https://yardscout.io/yard/pick-n-pull-dallas-south');
check('yard: links to its city and state pages', r.html.includes('href="https://yardscout.io/junkyards/texas/dallas">Junkyards in Dallas, TX</a>') && r.html.includes('href="https://yardscout.io/junkyards/texas">Junkyards in Texas</a>'));
const nearYards = section(r.html, 'Nearest tracked yards');
const nearOrder = ['bob-s-pull-and-save', 'grand-prairie-u-pull', 'uapi-texarkana', 'texarkana-pull-it', 'houston-dateless-yard'].map((s) => nearYards.indexOf('/yard/' + s + '"'));
check('yard: nearest 5 other yards, closest first, with distance', nearOrder.every((p, i) => p > 0 && (i === 0 || p > nearOrder[i - 1])) && (nearYards.match(/<li>/g) || []).length === 5 && /Grand Prairie U-Pull<span class="where">Grand Prairie, TX · 1[0-9] mi/.test(nearYards), nearOrder.join(','));
check('yard: never lists itself as a nearby yard', !nearYards.includes('/yard/pick-n-pull-dallas-south"'));
check('yard: makes link to /landed/<make> with this lot\'s counts', r.html.includes('<a href="https://yardscout.io/landed/ford">Ford<small>3 on this lot</small></a>') && r.html.includes('<a href="https://yardscout.io/landed/honda">Honda<small>1 on this lot</small></a>') && r.html.includes('On the lot now, by make <span>· 3 makes</span>'));
check('yard: arrivals link to /car/<vin>', r.html.includes('href="https://yardscout.io/car/1HGFB2F50CL000001"') && !r.html.includes('/car/2T1BR32E54C000005'));
r = await get('/yard/houston-dateless-yard');
check('dateless yard: title has no "new this week" figure', titleOf(r.html) === 'Houston Dateless Yard inventory: 2 cars on the lot (Houston, TX) — YardScout', titleOf(r.html));
check('dateless yard: says dates are not published instead of "0 new"', r.html.includes("doesn't publish set-out dates") && r.html.includes('<span class="label">New this week</span><span class="value accent">—</span>') && !meta(r.html, 'description').includes('set out in the last'));
r = await get('/yard/duke-city-u-pull');
check('big lot: title counts all 105 cars', titleOf(r.html) === 'Duke City U-Pull inventory: 105 cars on the lot, 0 new this week (Albuquerque, NM) — YardScout', titleOf(r.html));
check('big lot: makes capped at 12 of 14, and says so', (r.html.match(/on this lot<\/small>/g) || []).length === 12 && r.html.includes('Make12<small>3 on this lot</small>') && !r.html.includes('Make13') && r.html.includes('· 14 makes') && r.html.includes('The 12 most common of 14 makes on this lot.'));
check('big lot: models capped at 15 of 27, and says so', (r.html.match(/<span class="tile">/g) || []).length === 15 && r.html.includes('· top 15 of 27') && r.html.includes('<span class="tile">Make01 Alpha<small>7 cars · 1990–2002</small></span>') && r.html.includes('Make08 Alpha<small>4 cars') && !r.html.includes('Make08 Beta'));
check('big lot: description names the top 3 makes and how many more', meta(r.html, 'description') === '105 cars on the lot at Duke City U-Pull (Albuquerque, NM): Make01 14, Make02 13, Make03 12 and 11 more makes. 0 set out in the last 7 days. Live inventory, refreshed every 4 hours.', meta(r.html, 'description'));
check('big lot: dated yard with nothing new says so', r.html.includes('No new set-outs in the last 7 days'));
r = await get('/yard/calgary-pick-a-part');
check('lot unreadable → 503 noindex, never "0 cars on the lot"', r.status === 503 && /content="noindex"/.test(r.html) && !/0 cars/.test(r.html) && h1s(r.html).length === 1, r.status);
r = await get('/yard/nope');
check('unknown yard → 404 noindex with one <h1> and hub links', r.status === 404 && /content="noindex"/.test(r.html) && h1s(r.html).length === 1 && r.html.includes('href="https://yardscout.io/junkyards"') && !r.headers.get('last-modified'));
r = await get('/yard/%E0%A4%A');
check('malformed yard path → 404, not an exception', r.status === 404, r.status);

/* ---------- /car/<vin> ---------- */
r = await get('/car/1HGFB2F50CL000001');
check('car → 200', r.status === 200, r.status);
seoChecks('car', r, { h1: '2012 Honda Civic at Pick-n-Pull - Dallas South', ld: ['BreadcrumbList'] });
check('car: title', titleOf(r.html) === '2012 Honda Civic at Pick-n-Pull - Dallas South (Dallas, TX) — YardScout', titleOf(r.html));
check('car: og:title keeps the share wording', meta(r.html, 'og:title') === '2012 Honda Civic · Row 12 · Pick-n-Pull - Dallas South', meta(r.html, 'og:title'));
check('car: breadcrumb Junkyards > State > City > Yard > Car', ldOf(r.html, 'BreadcrumbList').itemListElement.map((e) => e.item).join() === 'https://yardscout.io/junkyards,https://yardscout.io/junkyards/texas,https://yardscout.io/junkyards/texas/dallas,https://yardscout.io/yard/pick-n-pull-dallas-south,https://yardscout.io/car/1HGFB2F50CL000001');
check('car: links to its yard, its make page and its city page', r.html.includes('href="https://yardscout.io/yard/pick-n-pull-dallas-south">Pick-n-Pull - Dallas South inventory</a>') && r.html.includes('href="https://yardscout.io/landed/honda">Honda arrivals at self-service yards this week</a>') && r.html.includes('href="https://yardscout.io/junkyards/texas/dallas">Junkyards in Dallas, TX</a>'));
check('car: facts still shown (row, set-out date, VIN, trim, lot clock)', r.html.includes('Row 12') && r.html.includes('VIN 1HGFB2F50CL000001') && r.html.includes('EX · FWD') && r.html.includes('Day 1 on the lot'));
check('car: no inline price list', !r.html.includes('class="ptable"') && !r.html.includes('id="pl-q"') && !r.html.includes('$32.99') && !r.html.includes('ALTERNATOR') && !r.html.includes('tap to open'));
check('car: links to the price list page instead', r.html.includes('<a href="https://yardscout.io/prices/pick-n-pull">Pick-n-Pull price list</a>'));
check('car: page is its own content, not a price list (under 20 KB)', r.html.length < 20000, r.html.length);
check('car: app link unchanged', r.html.includes('href="https://yardscout.io/#car=1HGFB2F50CL000001" data-app-path="/car/1HGFB2F50CL000001"'));
r = await get('/car/1HGCM56405A000000');
check('gone car → 404 noindex, one <h1>, no JSON-LD', r.status === 404 && /content="noindex"/.test(r.html) && h1s(r.html).join() === 'This car is no longer listed' && ldBlocks(r.html).length === 0);
check('gone car: links to the hubs (its yard and make are no longer known)', ['/junkyards', '/yards', '/landed'].every((p) => r.html.includes(`href="https://yardscout.io${p}"`)));
r = await get('/car/not%20a%20car');
check('bad car link → 404 noindex with one <h1>', r.status === 404 && h1s(r.html).length === 1 && /content="noindex"/.test(r.html));

/* ---------- /prices: a chain with one list (per-yard chains: prices_unit.mjs) ---------- */
r = await get('/prices/pick-n-pull');
check('price page → 200', r.status === 200, r.status);
check('price page: one <h1> "<Chain> price list"', h1s(r.html).join('|') === 'Pick-n-Pull price list', JSON.stringify(h1s(r.html)));
check('price page: title and description from the list itself', titleOf(r.html) === 'Pick-n-Pull price list: 9 parts and their pull prices — YardScout' && meta(r.html, 'description') === 'Pick-n-Pull self-service price list, 9 parts: alternator $32.99 plus $9.99 core, starter $30.99 plus $9.99 core, hood - car $64.99. From the yard&#39;s own published list; confirm at the counter.', `${titleOf(r.html)} | ${meta(r.html, 'description')}`);
check('price page: BreadcrumbList only, no Offer/Product markup', ldBlocks(r.html).map((b) => b['@type']).join() === 'BreadcrumbList' && !FORBIDDEN_LD.test(r.html) && ldOf(r.html, 'BreadcrumbList').itemListElement.map((e) => e.item).join() === 'https://yardscout.io/prices,https://yardscout.io/prices/pick-n-pull');
check('price page: indexable, canonical, and no Last-Modified (the file has no read date)', meta(r.html, 'robots') === 'index,follow' && canonical(r.html) === 'https://yardscout.io/prices/pick-n-pull' && !r.headers.get('last-modified') && !/as of|read on|updated/i.test(section(r.html, '<h1')));
const priceRowsHtml = (r.html.match(/<table class="ptable" id="pl-rows">[\s\S]*?<\/table>/) || [''])[0];
check('price page: every priced row, in the yard\'s words, with core', (priceRowsHtml.match(/<tr><td>/g) || []).length === 9 && priceRowsHtml.includes('<td>ALTERNATOR</td><td class="num">$32.99</td><td class="num">$9.99</td>') && priceRowsHtml.includes('<td>ENGINE (COMPLETE)</td><td class="num">$299.99</td><td class="num">$50.00</td>') && priceRowsHtml.includes('<td>RADIATOR (W/O SHROUD)</td>'), priceRowsHtml.slice(0, 300));
check('price page: priced by length says so', priceRowsHtml.includes('<td class="num">$0.79<small> / inch</small></td>'));
check('price page: part name escaped', priceRowsHtml.includes('TRIM &lt;b&gt;MOLDING&lt;/b&gt;') && !r.html.includes('<b>MOLDING'));
check('price page: no unpriced, run-together or bookkeeping rows, no catalytic converter', !/MISCELLANEOUS|CORE - ALUM|DO NOT SELL|AIR CLEANER|CATALYTIC|Reimbursement|5662/i.test(r.html));
check('price page: lists the chain\'s tracked yards and the chain\'s own price page', section(r.html, 'Yards on this list').includes('href="https://yardscout.io/yard/pick-n-pull-dallas-south"') && section(r.html, 'Yards on this list').includes('href="https://yardscout.io/yard/pick-n-pull-lynnwood"') && r.html.includes('· 2 yards') && r.html.includes('href="https://www.picknpull.com/part-pricing" target="_blank" rel="noopener">Pick-n-Pull\'s own price page'));
check('price page: filter box', r.html.includes('id="pl-q"') && r.html.includes("querySelectorAll('#pl-rows tbody tr')"));
r = await get('/prices');
check('/prices hub → 200, one <h1>, lists chains with a tracked yard only', r.status === 200 && h1s(r.html).join('|') === 'Self-service junkyard price lists' && r.html.includes('href="https://yardscout.io/prices/pick-n-pull">Pick-n-Pull price list<span class="where">TX, WA</span></a><span class="meta">2 yards</span>') && !r.html.includes('/prices/tear-a-part'));
check('/prices hub: counts and ItemList', titleOf(r.html) === 'Junkyard price lists: pull prices at 2 self-service yards — YardScout' && r.html.includes('covering 2 of the 9 yards YardScout tracks') && ldBlocks(r.html).map((b) => b['@type']).join() === 'ItemList' && ldOf(r.html, 'ItemList').numberOfItems === 1 && !FORBIDDEN_LD.test(r.html), titleOf(r.html));
r = await get('/prices/pick-n-pull/pick-n-pull-dallas-south');
check('yard URL under a one-list chain → 301 to the chain page', r.status === 301 && r.headers.get('location') === 'https://yardscout.io/prices/pick-n-pull', `${r.status} ${r.headers.get('location')}`);
for (const p of ['/prices/pick-n-pull/duke-city-u-pull', '/prices/tear-a-part', '/prices/nope', '/prices/%E0%A4%A', '/prices/pick-n-pull/x/y']) {
  r = await get(p);
  check(`${p} → 404${p.endsWith('/x/y') ? '' : ' noindex, one <h1>'}`, r.status === 404 && (p.endsWith('/x/y') || (/content="noindex"/.test(r.html) && h1s(r.html).length === 1)), r.status);
}

/* ---------- www → apex for rendered pages ---------- */
r = await get('/junkyards/texas/dallas?utm_source=x', 'www.yardscout.io');
check('www rendered page → 301 to the apex, query kept', r.status === 301 && r.headers.get('location') === 'https://yardscout.io/junkyards/texas/dallas?utm_source=x', `${r.status} ${r.headers.get('location')}`);

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
