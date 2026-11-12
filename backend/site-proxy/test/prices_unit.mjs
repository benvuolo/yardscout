/* Unit test for the /prices pages of chains that post a price list per yard
 * (src/share.js), through the Worker's own router. fetch is stubbed with
 * fixture data; nothing leaves the machine. The one-list chains, the yard
 * page's common-parts table and the car page are in junkyards_unit.mjs.
 * Run: node test/prices_unit.mjs   (from backend/site-proxy/) */
import worker from '../src/index.js';
import { buildPriceBook, commonParts, priceRows, PRICE_CHAIN_SLUGS } from '../src/share.js';

let failures = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + detail}`); if (!ok) failures++; };

// junkyards.json rows: [location, pageCity, state, lat, lng, carsOnLot, setOutLast7Days]
const JUNKYARDS = {
  scrapedAt: '2026-10-30T11:58:45Z', days: 7,
  yards: [
    ['Pull-A-Part - Atlanta South', 'Conley', 'GA', 33.65, -84.33, 900, 40],
    ['Pull-A-Part - Atlanta North', 'Norcross', 'GA', 33.94, -84.21, 800, 30],
    ['Pull-A-Part - Tucson', 'Tucson', 'AZ', 32.16, -110.93, 700, 20],
    ['Budget U-Pull-It - Bartow', 'Bartow', 'FL', 27.9, -81.84, 600, 10],
    ['Budget U-Pull-It - Winter Garden', 'Winter Garden', 'FL', 28.56, -81.59, 500, 15],
    ['Solo Yard', 'Reno', 'NV', 39.53, -119.81, 100, 5],   // no price list
  ],
  newest: [[], [], [], [], [], []],
  stateMakes: {},
};
// Per-yard price files: {yard name: {part: {price, core}}}.
const PAP = {
  'Pull-A-Part - Atlanta South': { 'ALTERNATOR (NON HYBRID)': { price: 26.95, core: 9.25 }, 'STEERING WHEEL': { price: 19.95, core: 0 }, 'TRANSFER CASE, 4X4': { price: 87.95, core: 27 } },
  'Pull-A-Part - Atlanta North': { 'ALTERNATOR (NON HYBRID)': { price: 26.95, core: 9.25 }, 'STEERING WHEEL': { price: 19.95, core: 0 }, 'TRANSFER CASE, 4X4': { price: 87.95, core: 27 } },
  'Pull-A-Part - Tucson': { 'ALTERNATOR (NON HYBRID)': { price: 29.95, core: 9.25 }, 'STEERING WHEEL': { price: 19.95, core: 0 } },
  // A yard in the chain's file that YardScout does not track: it never
  // appears on a page and is never counted in "N of M yards".
  'Pull-A-Part - Ghost Town': { 'ALTERNATOR (NON HYBRID)': { price: 26.95, core: 9.25 }, 'STEERING WHEEL': { price: 19.95, core: 0 }, 'TRANSFER CASE, 4X4': { price: 87.95, core: 27 } },
};
const BUDGET = {
  'Budget U-Pull-It - Bartow': { ALTERNATOR: { price: 25, core: 5 }, RADIATOR: { price: 40, core: 0 }, 'TIMING GEAR': { price: 4, core: 0 } },
  'Budget U-Pull-It - Winter Garden': { ALTERNATOR: { price: 27.5, core: 5 }, RADIATOR: { price: 40, core: 0 }, 'CATALYTIC CONVERTER': { price: 50, core: 0 }, 'FREE THING': { price: 0, core: 0 } },
};
const fetched = [];
globalThis.fetch = async (u) => {
  u = String(u); fetched.push(u);
  const json = (o) => new Response(JSON.stringify(o), { headers: { 'content-type': 'application/json' } });
  if (u.endsWith('/data/junkyards.json')) return json(JUNKYARDS);
  if (u.endsWith('/data/pap_pricing.json')) return json(PAP);
  if (u.endsWith('/data/budget_pricing.json')) return json(BUDGET);
  if (u.endsWith('/data/landed.json')) return json({ scrapedAt: JUNKYARDS.scrapedAt, days: 7, yards: JUNKYARDS.yards.map(([loc, city, st, , , n, w]) => [loc, city, st, n, w]), makes: {} });
  if (u.endsWith('/v1/yards')) return json({ scrapedAt: JUNKYARDS.scrapedAt, yardFields: ['location', 'city', 'state', 'lat', 'lng', 'avgLifespanDays', 'lifespanBasis'], yards: JUNKYARDS.yards.map((y) => [...y.slice(0, 5), null, null]) });
  if (/\/v1\/inventory\/shard\/\d+$/.test(u)) return json({ vehicles: [[1, 'VIN00000000000001', 2010, 'Ford', 'Focus', '1', '', 0, 0, 0, 0]], vpic: {} });
  if (u.startsWith('https://benvuolo.github.io/yardscout/')) return new Response('Not Found', { status: 404 });
  throw new Error('unexpected fetch ' + u);
};
const get = async (path) => {
  fetched.length = 0;
  const r = await worker.fetch(new Request('https://yardscout.io' + path, { redirect: 'manual' }), {});
  return { status: r.status, headers: r.headers, html: await r.text(), fetched: fetched.slice() };
};
const titleOf = (html) => (html.match(/<title>([^<]*)<\/title>/) || [])[1];
const meta = (html, name) => (html.match(new RegExp(`<meta (?:name|property)="${name}" content="([^"]*)"`)) || [])[1];
const canonical = (html) => (html.match(/<link rel="canonical" href="([^"]+)">/) || [])[1];
const h1s = (html) => [...html.matchAll(/<h1[\s>][\s\S]*?<\/h1>/g)].map((m) => m[0].replace(/<[^>]+>/g, ''));
const ldTypes = (html) => [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)].map((m) => JSON.parse(m[1])['@type']).join();
const FORBIDDEN_LD = /"@type":\s*"(Vehicle|Car|Product|Offer|AggregateOffer|AggregateRating|Review)"|aggregateRating|"offers"/;
const table = (html) => (html.match(/<table class="ptable" id="pl-rows">[\s\S]*?<\/table>/) || [''])[0];

/* ---------- the rules, without the router ---------- */
check('chain slugs are unique and URL-safe', new Set(PRICE_CHAIN_SLUGS).size === PRICE_CHAIN_SLUGS.length && PRICE_CHAIN_SLUGS.every((s) => /^[a-z0-9]+(-[a-z0-9]+)*$/.test(s)), PRICE_CHAIN_SLUGS.join(' '));
check('slugs people will type', ['pick-n-pull', 'pick-your-part', 'pull-a-part', 'harrys-u-pull-it', 'm-and-m-u-pull-it', 'chuck-and-eddies'].every((s) => PRICE_CHAIN_SLUGS.includes(s)));
{
  const rows = priceRows([['B  PART', '2.50', '0.00'], ['a part', 1, 3], ['', 9, 0], ['ZERO', '0.00', '4.00'], ['TWO\r\nLINES', 5, 0], ['Catalytic Converter', 5, 0], ['Gift Store Credit', 0.01, 0], ['RED DOT TIRE NON REFUNDABLE', 15, 0], ['HOSE', '0.68', '0', 'Inches'], ['BAD', 'n/a', 0]]);
  check('priceRows: keeps priced single-line parts, sorted, whitespace tidied', rows.map((r) => r.part).join('|') === 'a part|B PART|HOSE|RED DOT TIRE NON REFUNDABLE', rows.map((r) => r.part).join('|'));
  check('priceRows: core and unit', rows[0].core === 3 && rows[1].core === 0 && rows[2].unit === 'inch' && rows[0].unit === '');
  const pick = (names) => commonParts(priceRows(names.map((n, i) => [n, 10 + i, 0]))).map((r) => r.part).join('|');
  check('commonParts: the plain part, never an accessory of it', pick(['ALTERNATOR BRACKET', 'ALTERNATOR', 'STARTER SOLENOID', 'DOOR HANDLE', 'HOOD LATCH', 'RADIATOR CAP']) === 'ALTERNATOR', pick(['ALTERNATOR BRACKET', 'ALTERNATOR', 'STARTER SOLENOID', 'DOOR HANDLE', 'HOOD LATCH', 'RADIATOR CAP']));
  check('commonParts: plain qualifiers and vetted wordings count', pick(['Alternator (Non Hybrid)', 'A/C COMPRESSOR (ALL)', 'FENDER BARE', 'HOOD- CAR', 'Door Complete - Car', 'HEADLAMP COMPOSITE', 'WINDOW REGULATOR W/MOTOR']) === 'Alternator (Non Hybrid)|A/C COMPRESSOR (ALL)|Door Complete - Car|FENDER BARE|HOOD- CAR|HEADLAMP COMPOSITE|WINDOW REGULATOR W/MOTOR');
  check('commonParts: the exact name wins over a qualified one', pick(['FENDER BARE', 'FENDER']) === 'FENDER');
  check('commonParts: never an engine, transmission or converter', pick(['ENGINE', 'TRANSMISSION', 'TORQUE CONVERTER', 'ENGINE LONG BLOCK']) === '');
  check('commonParts: at most 8 rows', commonParts(priceRows(['ALTERNATOR', 'STARTER', 'RADIATOR', 'A/C COMPRESSOR', 'WATER PUMP', 'POWER STEERING PUMP', 'BRAKE CALIPER', 'DOOR', 'FENDER', 'HOOD'].map((n) => [n, 5, 0]))).length === 8);
}
{
  const pap = buildPriceBook({ kind: 'dict' }, PAP);
  check('book: a list most yards share word for word is the chain list', pap.base && pap.base.locs.size === 3 && pap.rows.length === 3 && pap.lists === 2);
  check('book: half is not most (2 of 4 yards sharing a list is no chain list)', buildPriceBook({ kind: 'dict' }, { A: { X: { price: 1 } }, B: { X: { price: 1 } }, C: { X: { price: 2 } }, D: { X: { price: 3 } } }).base === null);
  const budget = buildPriceBook({ kind: 'dict' }, BUDGET);
  check('book: no shared list → no chain list, each yard has its own', budget.base === null && budget.rows === null && budget.yards.size === 2);
  check('book: one yard alone is the chain list', buildPriceBook({ kind: 'dict' }, { 'Only Yard': { ALTERNATOR: { price: 5, core: 0 } } }).base.locs.size === 1);
  check('book: an empty or priceless file is no book', buildPriceBook({ kind: 'dict' }, {}) === null && buildPriceBook({ kind: 'list' }, [{ description: 'X', price: '0.00' }]) === null);
}

/* ---------- chain where most yards share one list (Pull-A-Part) ---------- */
let r = await get('/prices/pull-a-part');
check('shared-list chain → 200, H1, title', r.status === 200 && h1s(r.html).join('|') === 'Pull-A-Part price list' && titleOf(r.html) === 'Pull-A-Part price list: 3 parts and their pull prices — YardScout', `${r.status} ${titleOf(r.html)}`);
check('shared-list chain: says how many yards post it, from tracked yards only', r.html.includes('3 parts on the price list posted for 2 of the 3 Pull-A-Part yards YardScout tracks. The other yard posts its own list, linked below.'));
check('shared-list chain: the shared list\'s rows', (table(r.html).match(/<tr><td>/g) || []).length === 3 && table(r.html).includes('<td>ALTERNATOR (NON HYBRID)</td><td class="num">$26.95</td><td class="num">$9.25</td>'));
check('shared-list chain: yards on the list link to their inventory pages', ['pull-a-part-atlanta-south', 'pull-a-part-atlanta-north'].every((s) => r.html.includes(`href="https://yardscout.io/yard/${s}"`)) && !r.html.includes('href="https://yardscout.io/yard/pull-a-part-tucson"'));
check('shared-list chain: the yard that differs links to its own price page', r.html.includes('href="https://yardscout.io/prices/pull-a-part/pull-a-part-tucson">Pull-A-Part - Tucson price list<span class="where">Tucson, AZ</span></a><span class="meta">2 parts</span>'));
check('shared-list chain: an untracked yard in the file is nowhere', !/Ghost/.test(r.html));
check('shared-list chain: BreadcrumbList only', ldTypes(r.html) === 'BreadcrumbList' && !FORBIDDEN_LD.test(r.html));
r = await get('/prices/pull-a-part/pull-a-part-tucson');
check('differing yard → its own page: H1 "<Yard> price list", own rows', r.status === 200 && h1s(r.html).join('|') === 'Pull-A-Part - Tucson price list' && (table(r.html).match(/<tr><td>/g) || []).length === 2 && table(r.html).includes('$29.95') && !table(r.html).includes('TRANSFER CASE'), `${r.status} ${h1s(r.html)}`);
check('differing yard: title, canonical, breadcrumb', titleOf(r.html) === 'Pull-A-Part - Tucson price list: 2 parts and their pull prices — YardScout' && canonical(r.html) === 'https://yardscout.io/prices/pull-a-part/pull-a-part-tucson' && ldTypes(r.html) === 'BreadcrumbList' && r.html.includes('"item":"https://yardscout.io/prices/pull-a-part"'), titleOf(r.html));
check('differing yard: links to its inventory page and the chain page', r.html.includes('href="https://yardscout.io/yard/pull-a-part-tucson">Pull-A-Part - Tucson inventory</a>') && r.html.includes('href="https://yardscout.io/prices/pull-a-part">Pull-A-Part prices at every yard</a>'));
check('differing yard: no Last-Modified, indexable', !r.headers.get('last-modified') && meta(r.html, 'robots') === 'index,follow');
r = await get('/prices/pull-a-part/pull-a-part-atlanta-south');
check('yard on the shared list → 301 to the chain page', r.status === 301 && r.headers.get('location') === 'https://yardscout.io/prices/pull-a-part', `${r.status} ${r.headers.get('location')}`);
r = await get('/prices/pull-a-part/pull-a-part-ghost-town');
check('untracked yard → 404 noindex', r.status === 404 && /content="noindex"/.test(r.html), r.status);

/* ---------- chain where every yard posts its own list (Budget) ---------- */
r = await get('/prices/budget-u-pull-it');
check('per-yard chain → 200, H1, title with the real counts', r.status === 200 && h1s(r.html).join('|') === 'Budget U-Pull-It price list' && titleOf(r.html) === 'Budget U-Pull-It price list: 3 parts, prices at 2 yards — YardScout', `${r.status} ${titleOf(r.html)}`);
check('per-yard chain: says the lists differ and links each yard\'s list', r.html.includes('2 different lists across the 2 yards YardScout tracks') && ['budget-u-pull-it-bartow', 'budget-u-pull-it-winter-garden'].every((s) => r.html.includes(`href="https://yardscout.io/prices/budget-u-pull-it/${s}"`)));
check('per-yard chain: lowest and highest posted price per part, and how many lists carry it', table(r.html).includes('<tr><td>ALTERNATOR</td><td class="num">$25.00</td><td class="num">$27.50</td><td class="num">2</td></tr>') && table(r.html).includes('<tr><td>TIMING GEAR</td><td class="num">$4.00</td><td class="num">$4.00</td><td class="num">1</td></tr>') && (table(r.html).match(/<tr><td>/g) || []).length === 3, table(r.html).slice(0, 400));
check('per-yard chain: description quotes the real spread', meta(r.html, 'description') === 'Budget U-Pull-It self-service price lists for 2 yards, 3 parts: alternator $25.00 to $27.50, radiator $40.00. Prices differ by yard; each yard&#39;s own published list is linked.', meta(r.html, 'description'));
check('per-yard chain: no catalytic converter, no unpriced row', !/CATALYTIC|FREE THING/i.test(r.html));
r = await get('/prices/budget-u-pull-it/budget-u-pull-it-winter-garden');
check('per-yard chain: a yard\'s page shows only its priced rows', r.status === 200 && (table(r.html).match(/<tr><td>/g) || []).length === 2 && table(r.html).includes('<td>ALTERNATOR</td><td class="num">$27.50</td><td class="num">$5.00</td>') && !/CATALYTIC|FREE THING/i.test(r.html), r.status);

/* ---------- hub, yard page link, sitemap ---------- */
r = await get('/prices');
check('hub lists both chains with their tracked yard counts', r.html.includes('Budget U-Pull-It price list<span class="where">FL</span></a><span class="meta">2 yards</span>') && r.html.includes('Pull-A-Part price list<span class="where">AZ, GA</span></a><span class="meta">3 yards</span>') && r.html.includes('covering 5 of the 6 yards YardScout tracks'));
check('hub reads no price file', !r.fetched.some((u) => u.includes('_pricing.json')), r.fetched.join(' '));
r = await get('/yard/pull-a-part-tucson');
check('yard with its own list links to its own price page', r.html.includes('<a href="https://yardscout.io/prices/pull-a-part/pull-a-part-tucson">Full Pull-A-Part - Tucson price list</a> (2 parts)'));
r = await get('/yard/pull-a-part-atlanta-north');
check('yard on the shared list links to the chain page', r.html.includes('<a href="https://yardscout.io/prices/pull-a-part">Full Pull-A-Part price list</a> (3 parts)'));
r = await get('/yard/solo-yard');
check('yard with no price list shows no price block', r.status === 200 && !r.html.includes('Common part prices here') && !r.html.includes('/prices/'));
r = await get('/sitemap.xml');
const priceLocs = [...r.html.matchAll(/<url><loc>https:\/\/yardscout\.io(\/prices[^<]*)<\/loc>(<lastmod>)?/g)].map((m) => m[1] + (m[2] ? ' DATED' : ''));
check('sitemap: hub, chains, and only the yards with a list of their own; none dated', priceLocs.join(' ') === '/prices /prices/budget-u-pull-it /prices/budget-u-pull-it/budget-u-pull-it-bartow /prices/budget-u-pull-it/budget-u-pull-it-winter-garden /prices/pull-a-part /prices/pull-a-part/pull-a-part-tucson', priceLocs.join(' '));

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
