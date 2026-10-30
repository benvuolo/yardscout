/* Unit test for the /junkyards pages (src/share.js) through the Worker's own
 * router (src/index.js) — fetch is stubbed with fixture data, nothing leaves
 * the machine. Run: node test/junkyards_unit.mjs   (from backend/site-proxy/) */
import worker from '../src/index.js';

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
  ],
  stateMakes: { TX: [['Ford', 6], ['Honda', 4]], NM: [['Subaru', 5]], AB: [['Dodge', 4]] },
};
const LANDED = {
  scrapedAt: JUNKYARDS.scrapedAt, days: 7,
  yards: JUNKYARDS.yards.map(([loc, city, st, , , n, w]) => [loc, city, st, n, w]),
  makes: { Ford: { total: 30, recent: [], recentCount: 6 } },
};
let dataDown = true;
globalThis.fetch = async (u) => {
  u = String(u);
  const json = (o) => new Response(JSON.stringify(o), { headers: { 'content-type': 'application/json' } });
  if (u.endsWith('/data/junkyards.json')) return dataDown ? new Response('down', { status: 502 }) : json(JUNKYARDS);
  if (u.endsWith('/data/landed.json')) return json(LANDED);
  if (u.endsWith('/data/yards_added.json')) return json([]);
  if (u.endsWith('/v1/yards')) return json({ yardFields: ['location', 'city', 'state'], yards: JUNKYARDS.yards.map((y) => y.slice(0, 3)), scrapedAt: JUNKYARDS.scrapedAt });
  if (u.startsWith('https://benvuolo.github.io/yardscout/')) return new Response('Not Found', { status: 404 });
  throw new Error('unexpected fetch ' + u);
};
const get = async (path) => {
  const r = await worker.fetch(new Request('https://yardscout.io' + path, { redirect: 'manual' }), {});
  return { status: r.status, headers: r.headers, html: await r.text() };
};
const canonical = (html) => (html.match(/<link rel="canonical" href="([^"]+)">/) || [])[1];
const section = (html, title) => { const i = html.indexOf(title); return i < 0 ? '' : html.slice(i, html.indexOf('<div class="section">', i + 1) >>> 0); };

// Data file unreachable on a cold isolate → honest 503, not an empty page.
let r = await get('/junkyards/texas');
check('data down → 503 noindex', r.status === 503 && /noindex/.test(r.html), r.status);
dataDown = false;

r = await get('/junkyards');
check('/junkyards → 200', r.status === 200, r.status);
check('/junkyards canonical', canonical(r.html) === 'https://yardscout.io/junkyards', canonical(r.html));
check('index: real total yards (unknown state code skipped)', /<span class="label">Yards<\/span><span class="value">8<\/span>/.test(r.html));
check('index: real total cars', r.html.includes('<span class="value">450</span>'));
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

r = await get('/junkyards/texas/dallas');
check('/junkyards/texas/dallas → 200', r.status === 200, r.status);
check('city canonical', canonical(r.html) === 'https://yardscout.io/junkyards/texas/dallas', canonical(r.html));
check('city: title', r.html.includes('<title>Junkyards in Dallas, TX: live self-service yard inventory — YardScout</title>'));
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

r = await get('/sitemap-yards.xml');
const locs = [...r.html.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);
check('sitemap 200', r.status === 200, r.status);
check('sitemap has /junkyards, states and cities', ['/junkyards', '/junkyards/texas', '/junkyards/texas/dallas', '/junkyards/texas/grand-prairie', '/junkyards/new-mexico/albuquerque', '/junkyards/alberta/calgary', '/junkyards/arkansas/texarkana']
  .every((p) => locs.includes('https://yardscout.io' + p)));
check('sitemap: one URL per state/city (1 + 4 states + 7 cities)', locs.filter((l) => l.includes('/junkyards')).length === 12, locs.filter((l) => l.includes('/junkyards')).length);
check('sitemap keeps the existing yard + landed URLs', locs.includes('https://yardscout.io/yards') && locs.includes('https://yardscout.io/yard/pick-n-pull-dallas-south'));

r = await get('/yards');
check('/yards links each state to its /junkyards page', r.html.includes('href="https://yardscout.io/junkyards/texas">by city</a>'));

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
