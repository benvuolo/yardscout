/* E2E: "Best yards for this part" (2026-11-19), the game-plan card above the
 * Parts tab's donor list.
 *
 * The real docs/ bundle with the checked-in data, served AS
 * https://yardscout.io/ by Playwright from disk (as pf_late_zip_e2e.mjs
 * does): no local server, no fixed port, nothing leaves this machine. The
 * zip lookup is answered from a table, /geo says "not ok", everything else
 * is aborted. Counters are caught in the page (sendEvent replaced), never
 * sent.
 *
 *   setup        a real fit search near San Jose (side mirrors, the seeker
 *                the most yards in range carry): the card sits right under
 *                the results head, before the donor rows
 *   count proof  for EVERY yard the card names, its "N donor cars" equals
 *                the donor rows the list shows for that yard, and the card
 *                names no yard the list does not show; again with
 *                "Verified fits only" on, and again after the Newest sort
 *   ordering     default Most donor cars (ties: closer), then each chip
 *                (Closest, Newest arrival, Lowest price): the yards are in
 *                that order as measured from the list's own rows, the rule
 *                line changes with the chip, a held yard is last
 *   show all     top 3 shown; "Show all N yards" lists N
 *   tap-to-filter a yard tapped: only its rows show, "Showing <yard> only"
 *                with a maps link; "All yards" resets
 *   one yard     no chips, one yard
 *   no donors    the card still renders: "No donor cars within R mi right
 *                now", with its forecast mount point
 *   forecast     YSForecast undefined: the mount points are empty and take
 *                no space. A stub: mount(el, ctx) called with the parts ctx
 *                (make, model, year, yrMin, yrMax, lat, lng, radiusMi,
 *                where 'parts'), and in the Cars tab's watch strip narrowed
 *                to one model (where 'cars')
 *   counters     pf-yards/shown once per search, pf-yards/chip-<order>,
 *                pf-yards/tap, pf-yards/all
 *
 * Run: node backend/test/pf_plan_e2e.mjs */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const DOCS = path.resolve(process.env.PF_DOCS || path.join(ROOT, 'docs'));
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json' };
const ZIP = '95112';
const ZIPS = { 95112: ['37.3485', '-121.8863'] };

let failures = 0, passes = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + String(detail).slice(0, 500)}`); if (ok) passes++; else failures++; };
const fileFor = (pathname) => {
  let p = decodeURIComponent(pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(DOCS, path.normalize(p));
  return f.startsWith(DOCS) && fs.existsSync(f) && !fs.statSync(f).isDirectory() ? f : null;
};

async function open(browser, { forecastStub = false } = {}) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, serviceWorkers: 'block' });
  const page = await ctx.newPage();
  await page.route('**/*', async (route) => {
    const u = new URL(route.request().url());
    if (u.hostname === 'yardscout.io' && u.pathname === '/geo') return route.fulfill({ json: { ok: false }, headers: { 'cache-control': 'no-store' } });
    const z = u.href.match(/api\.zippopotam\.us\/us\/(\d{5})/);
    if (z) {
      if (!ZIPS[z[1]]) return route.fulfill({ status: 404, body: '' });
      return route.fulfill({ json: { places: [{ latitude: ZIPS[z[1]][0], longitude: ZIPS[z[1]][1] }] }, headers: { 'access-control-allow-origin': '*' } });
    }
    // The arrivals history is never served here: "forecast absent" is the app
    // with no history published (the real files exist in docs/data since
    // 2026-11-19, and with them the real module drew a real forecast). The
    // card with the real module and data is pf_forecast_e2e's job.
    if (u.hostname === 'yardscout.io' && /\/data\/arrivals\//.test(u.pathname)) return route.fulfill({ status: 404, body: '' });
    if (u.hostname === 'yardscout.io') {
      const f = fileFor(u.pathname);
      if (f) return route.fulfill({ path: f, contentType: TYPES[path.extname(f)] || 'application/octet-stream' });
      return route.fulfill({ status: 404, body: '' });
    }
    return route.abort();
  });
  await page.addInitScript(({ zip, forecastStub }) => {
    navigator.sendBeacon = () => true;
    localStorage.setItem('jh_honesty_ack', '1');
    localStorage.setItem('jh_zip', zip);
    window.__fc = [];
    if (forecastStub) {
      // The real module (docs/forecast.js) loads after this and assigns
      // window.YSForecast; the stub must win, so the name is a getter with a
      // setter that ignores the assignment (hub, 2026-11-19: with the real
      // module merged, a plain assignment here was overwritten and the four
      // stub checks failed).
      const stub = { mount(el, ctx) { window.__fc.push({ ctx: JSON.parse(JSON.stringify(ctx)), cls: el.className }); el.innerHTML = '<p class="stub-forecast">Forecast stub</p>'; } };
      Object.defineProperty(window, 'YSForecast', { get: () => stub, set: () => {}, configurable: true });
    }
  }, { zip: ZIP, forecastStub });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e.message).slice(0, 200)));
  await page.goto('https://yardscout.io/', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => typeof liveLoaded !== 'undefined' && liveLoaded && typeof activeZipCoords !== 'undefined' && activeZipCoords, null, { timeout: 120000 });
  // Counters stay in the page.
  await page.evaluate(() => { window.__ev = []; window.sendEvent = (e) => { window.__ev.push(e); }; });
  await page.click(".tab[data-tab='parts']");
  await page.waitForSelector('#tab-parts.active', { timeout: 20000 });
  await page.waitForFunction(() => typeof interchangeData !== 'undefined' && interchangeData, null, { timeout: 60000 }).catch(() => page.evaluate(() => loadInterchange()));
  await page.waitForFunction(() => typeof interchangeData !== 'undefined' && interchangeData, null, { timeout: 60000 });
  return { ctx, page, errors };
}

/** Set the seeker in the form and run the fit search for a category. */
async function search(page, [year, make, model], cat) {
  await page.selectOption('#pf-year', String(year));
  await page.selectOption('#pf-make', make);
  await page.waitForFunction((md) => [...document.getElementById('pf-model').options].some(o => o.value === md), model, { timeout: 10000 });
  await page.selectOption('#pf-model', model);
  await page.evaluate((cat) => { pfCat = interchangeData.categories.find(c => c.id === cat); pfPartInput.value = pfCat.label; pfRunSearch(); }, cat);
  await page.waitForFunction(() => document.querySelector('#pf-results .pf-plan'), null, { timeout: 30000 });
}

/** What the card says and what the list shows, read from the page. */
const read = (page) => page.evaluate(() => {
  const out = document.getElementById('pf-results');
  const locOf = new Map(liveInventory.map(v => [vehicleKey(v), v]));
  const shown = [...out.querySelectorAll('.pf-row-card[data-vkey]')].filter(c => getComputedStyle(c).display !== 'none');
  const listByYard = {};
  const facts = {};
  for (const c of shown) {
    const v = locOf.get(c.dataset.vkey);
    const y = v ? v.location : '?';
    listByYard[y] = (listByYard[y] || 0) + 1;
    const f = facts[y] || (facts[y] = { d: null, newest: 0, price: null, held: !!yardListStale(y) });
    const d = vehicleDistanceMi(v);
    if (d != null && (f.d == null || d < f.d)) f.d = d;
    f.newest = Math.max(f.newest, yardDateMs(v.dateAdded));
    const q = yardPartQuote(y, pfPlan.variants);
    if (q.status === 'priced' && (f.price == null || q.price < f.price)) f.price = q.price;
  }
  const card = out.querySelector('.pf-plan');
  const yards = card ? [...card.querySelectorAll('.pf-plan-yard')].map(b => {
    const m = b.textContent.match(/([\d,]+) donor cars?/);
    return { yard: b.dataset.yard, n: m ? parseInt(m[1].replace(/,/g, ''), 10) : NaN, pressed: b.getAttribute('aria-pressed') === 'true', text: b.textContent.replace(/\s+/g, ' ').trim() };
  }) : [];
  const bar = out.querySelector('.pf-yard-only');
  const children = [...out.children];
  return {
    card: !!card,
    title: card ? (card.querySelector('.pf-plan-title') || {}).textContent : '',
    rule: card ? (card.querySelector('.pf-plan-rule') || {}).textContent : '',
    headline: card && card.querySelector('.pf-plan-headline') ? card.querySelector('.pf-plan-headline').textContent : '',
    ranks: card ? [...card.querySelectorAll('.pf-plan-yard .pf-plan-rank')].map(e => e.textContent.trim()) : [],
    capped: pfPlan ? pfPlan.total > pfPlan.rows.length : false,
    planTotal: pfPlan ? pfPlan.total : 0, planRows: pfPlan ? pfPlan.rows.length : 0,
    radius: effectiveRadiusMi(),
    allYards: pfPlan ? pfPlanYards(pfPlanItems(pfPlanShownRows()), pfPlanView.order).length : 0,
    chips: card ? [...card.querySelectorAll('.pf-plan-chip')].map(c => [c.dataset.order, c.getAttribute('aria-pressed')]) : [],
    allBtn: card && card.querySelector('.pf-plan-all') ? card.querySelector('.pf-plan-all').textContent.trim() : '',
    yards, listByYard, facts, shownN: shown.length,
    barShown: !!(bar && !bar.hidden && getComputedStyle(bar).display !== 'none'),
    barText: bar ? bar.textContent.replace(/\s+/g, ' ').trim() : '',
    barLink: bar && bar.querySelector('a') ? bar.querySelector('a').href : '',
    cardIdx: children.indexOf(card),
    headIdx: children.findIndex(c => c.classList.contains('pf-results-head')),
    firstRowIdx: children.findIndex(c => c.classList.contains('pf-row-card')),
    headText: (out.querySelector('.pf-results-head') || {}).textContent || '',
    forecast: card && card.querySelector('.pf-forecast') ? { html: card.querySelector('.pf-forecast').innerHTML, h: card.querySelector('.pf-forecast').getBoundingClientRect().height } : null,
  };
});

/** Card count == list rows, for every yard, in both directions. */
function countProof(label, r) {
  const bad = r.yards.filter(y => r.listByYard[y.yard] !== y.n);
  const cardYards = new Set(r.yards.map(y => y.yard));
  const missing = Object.keys(r.listByYard).filter(y => !cardYards.has(y));
  check(`${label}: every yard's donor count equals the rows the list shows for it (${r.yards.length} yards, ${r.shownN} rows)`,
    !bad.length && !missing.length && r.yards.reduce((k, y) => k + y.n, 0) === r.shownN,
    JSON.stringify({ bad: bad.slice(0, 3), missing: missing.slice(0, 3), list: r.listByYard }));
  // The headline counts the same rows: "N donor cars at Y yards within R mi."
  const nY = Object.keys(r.listByYard).length;
  if (!r.shownN) {
    check(`${label}: no rows shown, the card says so (no headline)`, !r.headline && /^No donor cars within/.test(r.rule), r.headline + ' | ' + r.rule);
    return;
  }
  const want = `${r.shownN.toLocaleString('en-US')} donor car${r.shownN === 1 ? '' : 's'} at ${nY} yard${nY === 1 ? '' : 's'} within ${r.radius} mi.`;
  check(`${label}: headline "${want}" counts the rows the list shows`, r.headline.startsWith(want) && r.allYards === nY, `${r.headline} | yards ${r.allYards}/${nY}`);
  const capLine = `Showing the first ${r.planRows} of ${r.planTotal.toLocaleString('en-US')} donors`;
  check(`${label}: headline names the list's row cap exactly when the list is capped (${r.planRows}/${r.planTotal})`, r.capped === r.headline.includes(capLine), r.headline);
  check(`${label}: rank numerals 1..n in the card's order`, r.ranks.length === r.yards.length && r.ranks.every((x, i) => x === String(i + 1)), JSON.stringify(r.ranks));
}

/** The card's yard order obeys `order`, measured from the list's own rows. */
function orderOk(r, order) {
  const ys = r.yards.map(y => ({ ...y, ...r.facts[y.yard] }));
  const near = (a, b) => (a.d ?? 1e9) - (b.d ?? 1e9);
  const cmp = {
    most: (a, b) => (b.n - a.n) || near(a, b),
    near: (a, b) => near(a, b) || (b.n - a.n),
    new: (a, b) => (b.newest - a.newest) || near(a, b),
    price: (a, b) => ((a.price == null) - (b.price == null)) || ((a.price ?? 0) - (b.price ?? 0)) || near(a, b),
  }[order];
  for (let i = 1; i < ys.length; i++) {
    const a = ys[i - 1], b = ys[i];
    const held = (a.held ? 1 : 0) - (b.held ? 1 : 0);
    if (held > 0 || (held === 0 && cmp(a, b) > 0)) return `${a.yard} before ${b.yard}: ${JSON.stringify([a, b])}`;
  }
  return '';
}

/** A seeker whose model (same generation) sits on the most yards near the zip. */
const pickSeekers = (page) => page.evaluate(() => {
  const r = effectiveRadiusMi();
  const by = new Map();
  for (const v of liveInventory) {
    const d = vehicleDistanceMi(v);
    if (d == null || (r && d > r)) continue;
    const mk = canonicalMake(v.make), md = canonicalModel(v.make, v.model);
    const w = pfGenWindow(mk, md, v.year);
    if (!w) continue;
    const k = `${mk}|${md}|${w[0]}`;
    const e = by.get(k) || { year: v.year, make: mk, model: md, yards: new Set() };
    e.yards.add(v.location);
    by.set(k, e);
  }
  return [...by.values()].sort((a, b) => b.yards.size - a.yards.size).slice(0, 6).map(e => [e.year, e.make, e.model, e.yards.size]);
});

const browser = await chromium.launch();
try {
  /* ---------- the card, without a forecast ---------- */
  {
    const w = await open(browser);
    const { page } = w;
    const seekers = await pickSeekers(page);
    check('setup: a model sits on several yards near the zip', seekers.length && seekers[0][3] >= 4, JSON.stringify(seekers));
    let r = null, seeker = null;
    for (const s of seekers) {
      try { await search(page, s, 'side-mirrors'); } catch (e) { continue; }
      r = await read(page);
      if (await page.evaluate(() => pfPlanYards(pfPlanItems(pfPlanShownRows()), 'most').length) >= 4) { seeker = s; break; }
    }
    check('setup: a fit search with 4+ yards on the card', !!seeker, JSON.stringify(seekers));
    if (seeker) console.log(`  seeker: ${seeker.slice(0, 3).join(' ')} side mirrors, ${r.yards.length} yards shown of ${seeker[3]}`);
    check('card: renders right under the results head, before the donor rows', r.card && r.headIdx >= 0 && r.cardIdx > r.headIdx && r.cardIdx < r.firstRowIdx, JSON.stringify([r.headIdx, r.cardIdx, r.firstRowIdx]));
    check('card: titled "Best yards for this part"', r.title === 'Best yards for this part', r.title);
    check('card: the head keeps "Yards track cars, not parts left on them"', /Yards track cars, not parts left on them/.test(r.headText), r.headText);
    check('card: default order line is Most donor cars (ties: closer)', /most donor cars first; ties go to the closer yard/i.test(r.rule), r.rule);
    check('card: four chips, Most donor cars pressed', JSON.stringify(r.chips.map(c => c[0])) === '["most","near","new","price"]' && r.chips[0][1] === 'true', JSON.stringify(r.chips));
    check('card: top 3 shown', r.yards.length === 3 || r.yards.length >= 4, String(r.yards.length));

    // Show all
    const shownBefore = (await read(page)).yards.length;
    const total = await page.evaluate(() => pfPlanYards(pfPlanItems(pfPlanShownRows()), 'most').length);
    check('show all: top 3 before expanding', total <= 3 || shownBefore === 3, `${shownBefore}/${total}`);
    if (total > 3) {
      check('show all: the button says how many', (await read(page)).allBtn === `Show all ${total} yards`, (await read(page)).allBtn);
      await page.click('#pf-results .pf-plan-all');
      r = await read(page);
      check('show all: every yard listed after the tap', r.yards.length === total, `${r.yards.length}/${total}`);
    }
    countProof('count proof (default)', r);
    const err0 = orderOk(r, 'most');
    check('ordering: Most donor cars, ties to the closer yard', !err0, err0);
    check('ordering: yard rows say distance and donor count', r.yards.every(y => /\d+ mi/.test(y.text) && /donor cars?/.test(y.text)), r.yards[0] && r.yards[0].text);
    check('facts: no price is said where the list has none', r.yards.every(y => (r.facts[y.yard].price == null) === !/yard price/.test(y.text)), JSON.stringify(r.yards.map(y => [y.yard, r.facts[y.yard].price, y.text])));
    check('facts: no set-out is said where the dates are unknown', r.yards.every(y => (r.facts[y.yard].newest === 0) === !/newest set out/.test(y.text)));

    const shownAtStart = await page.evaluate(() => window.__ev.filter(e => e === 'pf-yards/shown').length);
    // Chips
    for (const [order, rule] of [['near', /^Closest yard first/], ['new', /newest donor set out first/i], ['price', /lowest published yard price/i], ['most', /most donor cars first/i]]) {
      await page.click(`#pf-results .pf-plan-chip[data-order="${order}"]`);
      r = await read(page);
      check(`chip ${order}: pressed and the rule line changes`, r.chips.find(c => c[0] === order)[1] === 'true' && rule.test(r.rule), r.rule);
      const e = orderOk(r, order);
      check(`chip ${order}: the yards are in that order (held yards last)`, !e, e);
      countProof(`chip ${order}: count proof`, r);
    }

    // Tap-to-filter
    const target = r.yards[1] || r.yards[0];
    await page.click(`#pf-results .pf-plan-yard[data-yard="${target.yard.replace(/"/g, '\\"')}"]`);
    r = await read(page);
    check('tap: only the tapped yard\'s rows show', Object.keys(r.listByYard).length === 1 && r.listByYard[target.yard] === target.n, JSON.stringify(r.listByYard));
    check('tap: the yard is marked pressed', r.yards.find(y => y.yard === target.yard).pressed);
    check('tap: "Showing <yard> only · All yards" bar', r.barShown && r.barText.startsWith(`Showing ${target.yard} only`) && /All yards/.test(r.barText), r.barText);
    check('tap: the bar offers the maps link', /^https:\/\/(www\.google\.com\/maps|maps\.apple\.com)\//.test(r.barLink), r.barLink);
    const scrolled = await page.evaluate(() => new Promise(res => setTimeout(() => { const b = document.querySelector('#pf-results .pf-yard-only').getBoundingClientRect(); res(b.top >= 0 && b.top < innerHeight); }, 900)));
    check('tap: the list scrolls into view', scrolled);
    await page.click('#pf-results .pf-plan-reset');
    r = await read(page);
    check('reset: "All yards" shows every yard again', !r.barShown && Object.keys(r.listByYard).length > 1 && !r.yards.some(y => y.pressed), JSON.stringify(r.listByYard));
    countProof('reset: count proof', r);

    // Verified fits only: the card counts what the list shows
    const hasVon = await page.$('#pf-vonly-cb');
    if (hasVon) {
      await page.check('#pf-vonly-cb');
      r = await read(page);
      countProof('verified only: count proof', r);
      await page.uncheck('#pf-vonly-cb');
    }
    // The Newest sort re-renders the list; the yard filter and the chip stay.
    await page.click(`#pf-results .pf-plan-yard[data-yard="${target.yard.replace(/"/g, '\\"')}"]`);
    await page.click('#pf-results .pf-sort-btn[data-sort="new"]');
    r = await read(page);
    check('sort Newest: the yard filter holds across the re-render', r.barShown && Object.keys(r.listByYard).length === 1, JSON.stringify(r.listByYard));
    await page.click('#pf-results .pf-plan-reset');
    countProof('sort Newest: count proof', await read(page));
    await page.click('#pf-results .pf-sort-btn[data-sort="near"]');

    // Forecast absent: mount point empty, no space
    r = await read(page);
    check('forecast absent: the mount point is there, empty, 0 px', r.forecast && r.forecast.html === '' && r.forecast.h === 0, JSON.stringify(r.forecast));

    // Counters
    const ev = await page.evaluate(() => window.__ev.filter(e => e.startsWith('pf-yards/')));
    const nShown = ev.filter(e => e === 'pf-yards/shown').length;
    check('counters: pf-yards/shown counted for the search, not again for chips, taps, the verified toggle or a re-sort', shownAtStart >= 1 && nShown === shownAtStart, `${shownAtStart} then ${nShown}: ${JSON.stringify(ev)}`);
    check('counters: chips, tap and show-all counted', ['pf-yards/chip-near', 'pf-yards/chip-new', 'pf-yards/chip-price', 'pf-yards/chip-most', 'pf-yards/tap'].every(e => ev.includes(e)) && (total <= 3 || ev.includes('pf-yards/all')), JSON.stringify(ev));
    check('counters: nothing but counter names (no ids)', ev.every(e => /^pf-yards\/(shown|tap|all|chip-(most|near|new|price))$/.test(e)), JSON.stringify(ev));

    // A search past the list's 120-row cap: the headline says "Showing the
    // first 120 of N donors" (the list's own words) and counts the 120.
    {
      let capped = null;
      for (const s of [[2009, 'Toyota', 'Camry'], [2005, 'Honda', 'Accord'], [2002, 'Honda', 'Civic'], ...seekers]) {
        try { await search(page, s, 'side-mirrors'); } catch (e) { continue; }
        if (await page.evaluate(() => pfPlan.total > pfPlan.rows.length)) { capped = s; break; }
      }
      check('cap: a search past the list\'s row cap was found', !!capped);
      if (capped) {
        if (await page.$('#pf-results .pf-plan-all')) await page.click('#pf-results .pf-plan-all');
        const rc = await read(page);
        console.log(`  capped: ${capped.join(' ')}: ${rc.headline}`);
        countProof('cap: count proof', rc);
        check('cap: the list shows its own cap line too', await page.evaluate(() => /Showing the first 120 of/.test((document.querySelector('#pf-results .pf-more') || {}).textContent || '')));
      }
    }

    // One yard only: the list narrowed to one yard's cars
    const one = await page.evaluate(() => {
      const keep = pfPlan.rows[0].v.location;
      window.__inv = liveInventory;
      liveInventory = liveInventory.filter(v => v.location === keep);
      pfRunSearch();
      return keep;
    });
    r = await read(page);
    check('one yard: one yard, no chips', r.yards.length === 1 && r.yards[0].yard === one && !r.chips.length, JSON.stringify(r.yards.map(y => y.yard)) + JSON.stringify(r.chips));
    countProof('one yard: count proof', r);
    await page.evaluate(() => { liveInventory = window.__inv; });

    // No donors
    // (the list's own empty state, as the ui test's pf-none: the car's yards
    // are emptied so no data change can give it donors)
    await page.evaluate(() => { window.__inv = liveInventory; liveInventory = []; pfRunSearch(); });
    r = await read(page);
    await page.evaluate(() => { liveInventory = window.__inv; });
    check('no donors: the list shows its own empty line too', await page.evaluate(() => !!document.querySelector('#pf-results .pf-empty')));
    check('no donors: the card renders with "No donor cars within R mi right now"', r.card && /^No donor cars within \d+ mi right now\.$/.test(r.rule) && r.yards.length === 0, r.rule);
    check('no donors: the forecast mount point is in the card', r.forecast !== null);
    check('no page error', !w.errors.length, w.errors.join(' | '));
    await w.ctx.close();

    /* ---------- with a forecast stub ---------- */
    const f = await open(browser, { forecastStub: true });
    await search(f.page, seeker || seekers[0], 'side-mirrors');
    if (await f.page.$('#pf-results .pf-plan-all')) await f.page.click('#pf-results .pf-plan-all');
    let fr = await read(f.page);
    const pc = await f.page.evaluate(() => window.__fc.filter(c => c.ctx.where === 'parts').pop());
    const exp = await f.page.evaluate((s) => ({ w: pfGenWindow(s[1], s[2], s[0]), c: activeZipCoords, r: effectiveRadiusMi() }), seeker || seekers[0]);
    check('forecast stub: mount(el, ctx) called into .pf-forecast', pc && pc.cls === 'pf-forecast' && /Forecast stub/.test(fr.forecast.html), JSON.stringify(pc));
    const sk = seeker || seekers[0];
    check('forecast stub: parts ctx carries the seeker, generation, place and radius',
      pc && pc.ctx.make === sk[1] && pc.ctx.model === sk[2] && pc.ctx.year === sk[0]
      && pc.ctx.yrMin === (exp.w ? exp.w[0] : null) && pc.ctx.yrMax === (exp.w ? exp.w[1] : null)
      && pc.ctx.lat === exp.c.lat && pc.ctx.lng === exp.c.lng && pc.ctx.radiusMi === exp.r && pc.ctx.where === 'parts'
      && JSON.stringify(Object.keys(pc.ctx).filter(k => k !== 'specs' && k !== 'lotNow').sort()) === JSON.stringify(['lat', 'lng', 'make', 'model', 'radiusMi', 'where', 'year', 'yrMax', 'yrMin'])
      && (pc.ctx.specs === undefined || (Array.isArray(pc.ctx.specs) && pc.ctx.specs.length > 0 && pc.ctx.specs.every(x => x.make && x.model && x.yrMin <= x.yrMax && Object.keys(x).length === 4)))
      && (pc.ctx.lotNow === undefined || (pc.ctx.specs && pc.ctx.lotNow.donors <= pc.ctx.lotNow.cars)),
      JSON.stringify({ pc, exp }));
    check('forecast stub: the forecast takes space when filled', fr.forecast.h > 0, JSON.stringify(fr.forecast));
    countProof('forecast stub: count proof', fr);
    // Cars tab, narrowed to one model
    await f.page.click(".tab[data-tab='live']");
    await f.page.evaluate((s) => {
      const m = document.getElementById('live-filter-make'); m.value = s[1]; m.dispatchEvent(new Event('change', { bubbles: true }));
      selectedModels.clear(); selectedModels.add(s[2]); renderLive();
    }, sk);
    await f.page.waitForTimeout(300);
    const cc = await f.page.evaluate(() => ({ calls: window.__fc.filter(c => c.ctx.where === 'cars'), el: !!document.querySelector('#live-grid .watch-strip .strip-forecast .stub-forecast') }));
    const last = cc.calls[cc.calls.length - 1];
    check('forecast stub: the Cars watch strip mounts it for one model', cc.el && last && last.cls === 'strip-forecast' && last.ctx.make === sk[1] && last.ctx.model === sk[2] && last.ctx.where === 'cars', JSON.stringify(cc));
    // two models: no mount point
    // (a real second model of the make: a made-up name can be pruned by a
    // later list refresh, which made this check flaky under load)
    const two = await f.page.evaluate((s) => {
      const other = liveInventory.map(v => canonicalModel(v.make, v.model)).find(m => canonicalMake(liveInventory.find(v => canonicalModel(v.make, v.model) === m).make) === s[1] && m !== s[2]);
      if (other) selectedModels.add(other);
      renderLive();
      return other || null;
    }, sk);
    await f.page.waitForTimeout(500);
    check('forecast stub: no strip mount point for two models', await f.page.evaluate(() => selectedModels.size === 2 && !document.querySelector('#live-grid .strip-forecast')), String(two));
    check('forecast stub: no page error', !f.errors.length, f.errors.join(' | '));
    await f.ctx.close();

    /* ---------- Cars strip without a forecast: empty, no space ---------- */
    const g = await open(browser);
    await g.page.click(".tab[data-tab='live']");
    await g.page.evaluate((s) => {
      const m = document.getElementById('live-filter-make'); m.value = s[1]; m.dispatchEvent(new Event('change', { bubbles: true }));
      selectedModels.clear(); selectedModels.add(s[2]); renderLive();
    }, sk);
    const st = await g.page.evaluate(() => { const e = document.querySelector('#live-grid .strip-forecast'); return e ? { html: e.innerHTML, h: e.getBoundingClientRect().height } : null; });
    check('forecast absent: the Cars strip mount point is empty, 0 px', st && st.html === '' && st.h === 0, JSON.stringify(st));
    check('Cars strip: no page error', !g.errors.length, g.errors.join(' | '));
    await g.ctx.close();
  }
} finally {
  await browser.close();
}
console.log(failures ? `${failures} FAILURE(S), ${passes} passed` : `ALL PASS (${passes})`);
process.exit(failures ? 1 : 0);
