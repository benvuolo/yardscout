/* Unit: docs/forecast.js (arrival forecast). summary(), every wording rule
 * and boundary, and mount() with a fake fetch (missing file, build mismatch).
 * Loads the real file as a plain script in a vm context, as a browser would.
 * Run: node backend/test/forecast_unit.mjs */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const SRC = fs.readFileSync(path.resolve(path.dirname(new URL(import.meta.url).pathname), '../../docs/forecast.js'), 'utf8');
function load(extra = {}) {
  const ctx = vm.createContext({ ...extra });
  vm.runInContext(SRC, ctx, { filename: 'forecast.js' });
  return ctx;
}
let pass = 0, fail = 0;
const check = (name, ok, d = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + d}`); ok ? pass++ : fail++; };
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

const F = load().YSForecast;
check('defines one global YSForecast with summary/words/mount',
  typeof F.summary === 'function' && typeof F.words === 'function' && typeof F.mount === 'function');

// Origin 40.0, -111.0. One degree of latitude is ~69.1 mi.
const index = {
  builtAt: '2026-11-19T07:00:00Z', windowEnd: '2026-11-18', weeks: 8,
  yardFields: ['location', 'lat', 'lng', 'coveredWeeks', 'stale'],
  yards: [
    ['Yard A', 40.1, -111.0, 8, 0],    // 0: ~6.9 mi
    ['Yard B', 40.2, -111.0, 8, 0],    // 1: ~13.8 mi
    ['Yard S', 40.05, -111.0, 8, 1],   // 2: stale
    ['Yard N', 40.05, -111.0, 1, 0],   // 3: one covered week (new)
    ['Yard Far', 42.0, -111.0, 8, 0],  // 4: ~138 mi
    ['Yard P', 40.3, -111.0, 4, 0],    // 5: ~20.7 mi, 4 covered weeks
    ['Yard Two', 40.25, -111.0, 2, 0], // 6: exactly 2 covered weeks: counted
    ['Yard Nowhere', null, null, 8, 0],
  ],
  makes: { Toyota: ['toyota', 40] },
};
const file = {
  builtAt: index.builtAt, windowEnd: '2026-11-18', make: 'Toyota', slug: 'toyota',
  models: {
    '4Runner': [
      [0, 2004, 1, 0, 2, 0, 1, 0, 0, 1],
      [0, 2012, 0, 0, 0, 0, 0, 0, 0, 3],
      [1, 2006, 0, 1, 0, 1, 0, 1, 0, 1],
      [2, 2005, 9, 9, 9, 9, 9, 9, 9, 9],   // stale yard: never counted
      [3, 2005, 0, 0, 0, 0, 0, 0, 0, 7],   // new yard: never counted
      [4, 2005, 5, 5, 5, 5, 5, 5, 5, 5],   // far
      [5, 2008, 0, 0, 0, 0, 2, 0, 1, 1],
      [6, 0, 0, 0, 0, 0, 0, 0, 1, 1],      // no model year
    ],
  },
};
const data = { index, file };
const Q = { make: 'Toyota', model: '4Runner', yrMin: null, yrMax: null, lat: 40.0, lng: -111.0 };

check('miles: 0.1 deg lat ~6.9 mi', Math.abs(F._milesBetween(40, -111, 40.1, -111) - 6.91) < 0.05);

let s = F.summary(data, { ...Q, lat: null });
check('no place: status "no place"', s.status === 'no place');
check('no place: words() is null (nothing to say)', F.words(s, Q) === null);
check('no radius: "no place"', F.summary(data, { ...Q, radiusMi: null }).status === 'no place');
check('no index: "no data"', F.summary({}, { ...Q, radiusMi: 50 }).status === 'no data');

s = F.summary(data, { ...Q, radiusMi: 10 });
check('10 mi: counts A only; S stale and N new skipped', s.yardsCounted === 1 && s.skipped.stale === 1 && s.skipped.newYard === 1, JSON.stringify(s));
check('10 mi: weekly totals (all years)', eq(s.weeks, [1, 0, 2, 0, 1, 0, 0, 4]), JSON.stringify(s.weeks));
check('10 mi: total 8, rate 8/8 = 1', s.total === 8 && s.rate === 1);

s = F.summary(data, { ...Q, radiusMi: 25 });
// A 8/8 + B 4/8 + P 4/4 + Two 2/2 = 1 + 0.5 + 1 + 1 = 3.5
check('25 mi: A, B, P, Two counted', s.yardsCounted === 4, JSON.stringify(s));
check('25 mi: rate = sum of arrivals / covered weeks per yard', Math.abs(s.rate - 3.5) < 1e-9, String(s.rate));
check('25 mi: total 18', s.total === 18, String(s.total));
check('25 mi: weeks', eq(s.weeks, [1, 1, 2, 1, 3, 1, 2, 7]), JSON.stringify(s.weeks));
check('top yards by arrivals, ties by name', eq(s.top, [['Yard A', 8], ['Yard B', 4], ['Yard P', 4], ['Yard Two', 2]]), JSON.stringify(s.top));
check('far yard and null-coordinate yard never counted', !s.top.some(t => t[0] === 'Yard Far' || t[0] === 'Yard Nowhere'));

s = F.summary(data, { ...Q, radiusMi: 25, yrMin: 2003, yrMax: 2009 });
check('year span 2003-2009: drops 2012 and year 0', s.total === 5 + 4 + 4, JSON.stringify(s));
check('year span: yards with no match still counted (rate over them)', s.yardsCounted === 4 && Math.abs(s.rate - (5 / 8 + 4 / 8 + 4 / 4)) < 1e-9, String(s.rate));
s = F.summary(data, { ...Q, radiusMi: 25, yrMin: 2010, yrMax: null });
check('open span 2010+: only the 2012 row', s.total === 3, String(s.total));

s = F.summary(data, { ...Q, model: '4runner', radiusMi: 10 });
check('model key matched case-insensitively as a fallback', s.total === 8);
s = F.summary(data, { ...Q, model: 'Tacoma', radiusMi: 25 });
check('model with no rows: zero at counted yards', s.status === 'ok' && s.total === 0 && s.yardsCounted === 4);

s = F.summary(data, { ...Q, lat: 45, lng: -100, radiusMi: 50 });
check('no yard in reach: "no counted yard"', s.status === 'no counted yard' && s.yardsCounted === 0);
s = F.summary(data, { ...Q, lat: 40.05, lng: -111, radiusMi: 2 });
check('only stale/new yards in reach: "no counted yard", skipped named', s.status === 'no counted yard' && s.skipped.stale === 1 && s.skipped.newYard === 1);

// ---- wording rules (summaries built by hand) ----
const base = { status: 'ok', weeks: [0, 0, 0, 0, 0, 0, 0, 0], total: 0, rate: 0, yardsCounted: 3, skipped: { stale: 0, newYard: 0 }, top: [], radiusMi: 50 };
const W = (o, q = Q) => F.words({ ...base, ...o }, q);
check('rate 1.5: "About 2 a week land within 50 mi"', W({ rate: 1.5, total: 12 }).headline === 'About 2 a week land within 50 mi');
check('rate 2.4: About 2', W({ rate: 2.4, total: 19 }).headline === 'About 2 a week land within 50 mi');
check('rate 2.5: About 3', W({ rate: 2.5, total: 20 }).headline === 'About 3 a week land within 50 mi');
check('rate 11.7: About 12', W({ rate: 11.7, total: 94 }).headline === 'About 12 a week land within 50 mi');
check('rate 1.49: about one a week', W({ rate: 1.49, total: 12 }).headline === 'About one a week lands within 50 mi');
check('rate 0.75: about one a week', W({ rate: 0.75, total: 6 }).headline === 'About one a week lands within 50 mi');
check('rate 0.74: one every 2 weeks (1/rate rounds to 1, said as 2)', W({ rate: 0.74, total: 6 }).headline === 'About one every 2 weeks lands within 50 mi', W({ rate: 0.74, total: 6 }).headline);
check('rate 0.5: one every 2 weeks', W({ rate: 0.5, total: 4 }).headline === 'About one every 2 weeks lands within 50 mi');
check('rate 0.25 with 2 arrivals: one every 4 weeks', W({ rate: 0.25, total: 2 }).headline === 'About one every 4 weeks lands within 50 mi');
check('rate 0.3: one every 3 weeks', W({ rate: 0.3, total: 3 }).headline === 'About one every 3 weeks lands within 50 mi');
check('exactly 1 arrival: Rare here', W({ rate: 0.125, total: 1 }).headline === 'Rare here: 1 landed within 50 mi in the last 8 weeks');
check('exactly 1 even at a high rate (partial coverage): Rare here', W({ rate: 0.5, total: 1 }).headline.startsWith('Rare here: 1 landed'));
check('none: None landed', W({ total: 0 }).headline === 'None landed within 50 mi in the last 8 weeks');
check('no counted yard: Not enough history', W({ status: 'no counted yard', yardsCounted: 0 }).headline === 'Not enough history near you yet');
check('place: "within 50 mi of Ogden"', W({ rate: 2, total: 16 }, { ...Q, place: 'Ogden' }).headline === 'About 2 a week land within 50 mi of Ogden');
// `where` is the surface that mounts the forecast (the app passes 'parts' or
// 'cars'); it must never reach the sentence (hub, 2026-11-19).
check('where is never shown: no "of parts"', W({ rate: 2, total: 16 }, { ...Q, where: 'parts' }).headline === 'About 2 a week land within 50 mi');
check('where is never shown: no "of cars"', W({ total: 0 }, { ...Q, where: 'cars' }).headline === 'None landed within 50 mi in the last 8 weeks');

check('facts: "T in the last 8 weeks at Y yards"', W({ rate: 2, total: 16 }).facts === '16 in the last 8 weeks at 3 yards');
check('facts: one yard singular', W({ total: 0, yardsCounted: 1 }).facts === '0 in the last 8 weeks at 1 yard');
check('facts: both skip reasons', W({ total: 5, rate: 1, skipped: { stale: 1, newYard: 2 } }).facts === '5 in the last 8 weeks at 3 yards (3 yards not counted: list not updating / new to YardScout)', W({ total: 5, rate: 1, skipped: { stale: 1, newYard: 2 } }).facts);
check('facts: stale only, plural', W({ total: 5, rate: 1, skipped: { stale: 2, newYard: 0 } }).facts.endsWith('(2 yards not counted: lists not updating)'));
check('facts: new only, one yard', W({ total: 5, rate: 1, skipped: { stale: 0, newYard: 1 } }).facts.endsWith('(1 yard not counted: new to YardScout)'));
check('facts: always present, even with no counted yard', W({ status: 'no counted yard', yardsCounted: 0, skipped: { stale: 1, newYard: 0 } }).facts === '0 in the last 8 weeks at 0 yards (1 yard not counted: list not updating)');

check('subject: span named "2003-2009 4Runner"', W({ total: 0 }, { ...Q, yrMin: 2003, yrMax: 2009 }).subject === '2003-2009 4Runner');
check('subject: one year "2005 4Runner"', W({ total: 0 }, { ...Q, yrMin: 2005, yrMax: 2005 }).subject === '2005 4Runner');
check('subject: no span "4Runner, any year"', W({ total: 0 }).subject === '4Runner, any year');
check('label fixed', W({ total: 0 }).label === 'From set-out dates YardScout has recorded. Past weeks, not a promise.');
check('most: two yards when total >= 3', W({ total: 3, rate: 0.4, top: [['A', 2], ['B', 1], ['C', 0]] }).most === 'Most land at: A (2), B (1)');
check('most: one yard when only one has arrivals', W({ total: 9, rate: 1.2, top: [['A', 9]] }).most === 'Most land at: A (9)');
check('most: none when total is 2', W({ total: 2, rate: 0.25, top: [['A', 2]] }).most === '');
check('alt text reads the numbers oldest to newest', W({ total: 3, rate: 0.4, weeks: [1, 0, 0, 0, 0, 0, 0, 2] }).alt === 'Arrivals per week, oldest to newest: 1, 0, 0, 0, 0, 0, 0, 2');
const all = [1.5, 0.9, 0.3].map(r => W({ rate: r, total: 5, top: [['A', 5]] }));
check('never a percentage or a promise', all.every(w => !/%|will |guarantee|expect/i.test(Object.values(w).join(' '))));

// end to end through summary -> words with the fixture
s = F.summary(data, { ...Q, radiusMi: 25 });
let w = F.words(s, Q);
check('fixture 25 mi: headline', w.headline === 'About 4 a week land within 25 mi', w.headline);
check('fixture 25 mi: facts with skipped', w.facts === '18 in the last 8 weeks at 4 yards (2 yards not counted: list not updating / new to YardScout)', w.facts);
check('fixture 25 mi: most', w.most === 'Most land at: Yard A (8), Yard B (4)', w.most);

// ---- mount with a fake fetch and element ----
function fakeFetch(map, log) {
  return (url) => {
    log && log.push(url);
    const v = map[url];
    if (v === undefined) return Promise.resolve({ ok: false, status: 404, json: () => Promise.reject(new Error('404')) });
    if (v instanceof Error) return Promise.reject(v);
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(JSON.parse(JSON.stringify(v))) });
  };
}
const ctxQ = { ...Q, radiusMi: 25, place: '84401', where: 'parts' };
{
  const log = [];
  const G = load({ fetch: fakeFetch({ 'data/arrivals/index.json': index, 'data/arrivals/toyota.json': file }, log) }).YSForecast;
  const el = { innerHTML: 'old' };
  const st = await G.mount(el, ctxQ);
  check('mount: renders, resolves "ok"', st === 'ok' && el.innerHTML.includes('About 4 a week land within 25 mi of 84401'), el.innerHTML.slice(0, 200));
  check('mount: eight bars', (el.innerHTML.match(/class="ysf-bar"/g) || []).length === 8);
  check('mount: bars have a text alternative', el.innerHTML.includes('role="img" aria-label="Arrivals per week, oldest to newest: 1, 1, 2, 1, 3, 1, 2, 7"'));
  await G.mount({ innerHTML: '' }, ctxQ);
  check('mount: index and make file fetched once (memory cache)', log.filter(u => u.endsWith('index.json')).length === 1 && log.filter(u => u.endsWith('toyota.json')).length === 1, JSON.stringify(log));
  const el2 = { innerHTML: 'x' };
  check('mount: no place renders nothing', (await G.mount(el2, { ...ctxQ, lat: null })) === null && el2.innerHTML === '');
  const el3 = { innerHTML: 'x' };
  check('mount: make not in the history renders nothing', (await G.mount(el3, { ...ctxQ, make: 'Yugo' })) === null && el3.innerHTML === '');
  const el4 = { innerHTML: '' };
  await G.mount(el4, { ...ctxQ, yrMin: undefined, yrMax: undefined, year: 2012 });
  check('mount: ctx.year alone is a one-year span', el4.innerHTML.includes('2012 4Runner') && el4.innerHTML.includes('Rare here') === false && el4.innerHTML.includes('3 in the last 8 weeks'), el4.innerHTML.slice(0, 300));
  const el5 = { innerHTML: '' };
  await G.mount(el5, { ...ctxQ, model: 'A <b>"x"</b>' });
  check('mount: text is escaped', !el5.innerHTML.includes('<b>') && el5.innerHTML.includes('&lt;b&gt;'));
}
{
  const G = load({ fetch: fakeFetch({}) }).YSForecast;
  const el = { innerHTML: 'x' };
  let threw = false, st;
  try { st = await G.mount(el, ctxQ); } catch (e) { threw = true; }
  check('mount: missing index renders nothing and does not throw', !threw && st === null && el.innerHTML === '');
}
{
  const G = load({ fetch: fakeFetch({ 'data/arrivals/index.json': index }) }).YSForecast;
  const el = { innerHTML: 'x' };
  const st = await G.mount(el, ctxQ);
  check('mount: missing make file renders nothing', st === null && el.innerHTML === '');
}
{
  const G = load({ fetch: fakeFetch({ 'data/arrivals/index.json': index, 'data/arrivals/toyota.json': new Error('offline') }) }).YSForecast;
  const el = { innerHTML: 'x' };
  check('mount: network error renders nothing', (await G.mount(el, ctxQ)) === null && el.innerHTML === '');
}
{
  const G = load({ fetch: fakeFetch({ 'data/arrivals/index.json': { yards: 'bad' }, }) }).YSForecast;
  const el = { innerHTML: 'x' };
  check('mount: malformed index renders nothing', (await G.mount(el, ctxQ)) === null && el.innerHTML === '');
}
{
  const log = [];
  const G = load({ fetch: fakeFetch({ 'data/arrivals/index.json': index, 'data/arrivals/toyota.json': { ...file, builtAt: '2026-11-20T07:00:00Z' } }, log) }).YSForecast;
  const el = { innerHTML: 'x' };
  const st = await G.mount(el, ctxQ);
  check('mount: make file from another build is not read against this index', st === null && el.innerHTML === '');
  check('…the index is fetched again once', log.filter(u => u.endsWith('index.json')).length === 2, JSON.stringify(log));
}
{
  const log = [];
  const G = load({ DATA_BASE: 'https://yardscout.io/', fetch: fakeFetch({ 'https://yardscout.io/data/arrivals/index.json': index, 'https://yardscout.io/data/arrivals/toyota.json': file }, log) }).YSForecast;
  const st = await G.mount({ innerHTML: '' }, ctxQ);
  check('mount: uses the app\'s DATA_BASE (native shells read yardscout.io)', st === 'ok' && log[0] === 'https://yardscout.io/data/arrivals/index.json', JSON.stringify(log));
}
{
  // a newer mount on the same element wins
  let release;
  const gate = new Promise(r => { release = r; });
  const slow = (url) => gate.then(() => fakeFetch({ 'data/arrivals/index.json': index, 'data/arrivals/toyota.json': file })(url));
  const G = load({ fetch: slow }).YSForecast;
  const el = { innerHTML: '' };
  const p1 = G.mount(el, { ...ctxQ, radiusMi: 10 });
  const p2 = G.mount(el, { ...ctxQ, radiusMi: 25 });
  release();
  await Promise.all([p1, p2]);
  check('mount: the newest mount on an element wins', el.innerHTML.includes('within 25 mi') && !el.innerHTML.includes('within 10 mi'));
}
{
  // compact (Alerts watch rows): the full block's own words, small bars, no "Most land at"
  const log = [];
  const G = load({ fetch: fakeFetch({ 'data/arrivals/index.json': index, 'data/arrivals/toyota.json': file }, log) }).YSForecast;
  const full = { innerHTML: '' }, small = { innerHTML: '' };
  const ctxA = { ...Q, radiusMi: 25, where: 'alerts' };
  await G.mount(full, ctxA);
  const st = await G.mount(small, { ...ctxA, compact: true });
  const text = (h, cls) => { const m = h.match(new RegExp(`<p class="${cls}">([^<]*)</p>`)) || h.match(new RegExp(`<div class="${cls}">([^<]*)</div>`)); return m ? m[1] : null; };
  const ww = G.words(G.summary(data, { ...ctxA, yrMin: null, yrMax: null }), ctxA);
  check('compact: renders, resolves "ok", marked ysf-compact', st === 'ok' && small.innerHTML.includes('class="ysf ysf-compact"'), small.innerHTML.slice(0, 200));
  for (const [cls, k] of [['ysf-subject', 'subject'], ['ysf-headline', 'headline'], ['ysf-facts', 'facts'], ['ysf-label', 'label']]) {
    const a = text(small.innerHTML, cls), b = text(full.innerHTML, cls);
    check(`compact: ${k} is the full block's words`, a !== null && a === b && a === ww[k].replace(/&/g, '&amp;'), `${a} | ${b} | ${ww[k]}`);
  }
  check('compact: eight bars with the same text alternative', (small.innerHTML.match(/class="ysf-bar"/g) || []).length === 8
    && small.innerHTML.includes(`aria-label="${ww.alt}"`) && full.innerHTML.includes(`aria-label="${ww.alt}"`));
  check('compact: no "Most land at" line (the full block has one)', !small.innerHTML.includes('ysf-most') && full.innerHTML.includes('Most land at'));
  check('compact: no per-bar numbers', !small.innerHTML.includes('ysf-bar-n') && full.innerHTML.includes('ysf-bar-n'));
  check('compact: "where" is never shown', !/alerts/.test(small.innerHTML));
  check('compact: files loaded once for both mounts', log.length === 2, JSON.stringify(log));
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
