/* E2E: the funnel events the real app sends, per platform (2026-11-12 audit).
 *
 * The page is the real docs/ bundle, but nothing leaves this machine: every
 * request is answered from disk by Playwright (docs/ is served AS
 * https://yardscout.io/ for the web run and AS https://localhost/ for the app
 * shells, which is the hostname the Android shell really uses), anything else
 * is aborted, and navigator.sendBeacon is replaced by a recorder. The
 * automation flag is hidden so the guard behaves as it does for a person;
 * one run leaves it on to prove an automated browser stays silent.
 *
 *   web  (yardscout.io)   first visit, a zip counted once across reloads, one
 *                         part search across re-renders, paywall opens only
 *                         while not Pro, a store-link tap per store and place
 *   web  (127.0.0.1)      silent (local copy)
 *   web  (automated)      silent
 *   web  narrowing        search-box pick, Filters model, Filters make only,
 *                         Trim filter, search trim row, #cars= link: one event
 *                         each under the route used, once a day per kind
 *                         (also across a reload), a new day counts again
 *   iOS / Android shell   counted on hostname "localhost", with its platform
 *
 * Run: node backend/test/funnel_events_e2e.mjs */
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { createRequire } from 'node:module';
import { serveWithNotableTrims } from './notable_trims_fixture.mjs';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const DOCS = path.join(ROOT, 'docs');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json' };
const ZIPS = { 85003: ['33.4511', '-112.0783'], 30310: ['33.7278', '-84.4232'] };
const UA_ANDROID = 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36';
const UA_IOS = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';

let failures = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + detail}`); if (!ok) failures++; };

const fileFor = (pathname) => {
  let p = decodeURIComponent(pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(DOCS, path.normalize(p));
  return f.startsWith(DOCS) && fs.existsSync(f) && !fs.statSync(f).isDirectory() ? f : null;
};
// A plain local server too, for the "local copy is silent" run.
const server = http.createServer((req, res) => {
  const f = fileFor(new URL(req.url, 'http://x').pathname);
  if (!f) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' });
  fs.createReadStream(f).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const LOCAL = `http://127.0.0.1:${server.address().port}/`;

async function open(browser, { origin, native = null, automated = false, ua = UA_IOS, storage = null }) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, hasTouch: true, userAgent: ua, serviceWorkers: 'block' });
  const page = await ctx.newPage();
  const leaked = [];
  await page.route('**/*', (route) => {
    const u = new URL(route.request().url());
    if (u.hostname === '127.0.0.1') return route.continue();
    const z = u.href.match(/api\.zippopotam\.us\/us\/(\d{5})/);
    if (z && ZIPS[z[1]]) return route.fulfill({ json: { places: [{ latitude: ZIPS[z[1]][0], longitude: ZIPS[z[1]][1] }] }, headers: { 'access-control-allow-origin': '*' } });
    if (u.pathname === '/api/ent/config') return route.fulfill({ json: { billing: true }, headers: { 'access-control-allow-origin': '*' } });
    // docs/ answers for the site itself (and for the shells' https://yardscout.io/data/...).
    if (u.hostname === 'yardscout.io' || u.origin === origin) {
      const f = fileFor(u.pathname);
      const nt = f && serveWithNotableTrims(f);   // notableTrims until the published scan carries it
      if (nt) return route.fulfill({ body: nt, contentType: 'application/json', headers: { 'access-control-allow-origin': '*' } });
      if (f) return route.fulfill({ path: f, contentType: TYPES[path.extname(f)] || 'application/octet-stream', headers: { 'access-control-allow-origin': '*' } });
      return route.fulfill({ status: 404, body: '' });
    }
    if (/yardscout-api/.test(u.hostname)) leaked.push(u.href);
    return route.abort();
  });
  await page.addInitScript(({ native, automated, storage }) => {
    if (!automated) Object.defineProperty(Navigator.prototype, 'webdriver', { get: () => false, configurable: true });
    window.__beacons = [];
    navigator.sendBeacon = (url, blob) => { blob.text().then(t => window.__beacons.push(JSON.parse(t))); return true; };
    if (storage && !sessionStorage.getItem('__seeded')) { for (const [k, v] of Object.entries(storage)) localStorage.setItem(k, v); sessionStorage.setItem('__seeded', '1'); }
    if (native) {
      const L = () => ({ remove() {} });
      window.Capacitor = { isNativePlatform: () => true, getPlatform: () => native, Plugins: {
        Purchases: { isEntitled: async () => ({ entitled: false }), getProduct: async () => ({ available: true, price: '$8.99', introPrice: '$1.99', introPeriod: '1 month', introCycles: 1 }),
          purchase: async () => ({ cancelled: true }), restore: async () => ({ entitled: false }) },
        PushNotifications: { addListener: L, checkPermissions: async () => ({ receive: 'prompt' }), requestPermissions: async () => ({ receive: 'denied' }), register: async () => {} },
        App: { addListener: L, getInfo: async () => ({ version: '1.12.14', build: '36' }), getLaunchUrl: async () => null },
        Geolocation: { getCurrentPosition: async () => { throw new Error('x'); }, checkPermissions: async () => ({ location: 'prompt' }) },
        StatusBar: { setStyle: async () => {}, setBackgroundColor: async () => {} },
      } };
    }
  }, { native, automated, storage });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e.message).slice(0, 160)));
  await page.goto(origin + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => typeof liveLoaded !== 'undefined' && liveLoaded, null, { timeout: 120000 });
  const events = async () => { await page.waitForTimeout(250); return page.evaluate(() => window.__beacons.map(b => b.e)); };
  const beacons = async () => { await page.waitForTimeout(250); return page.evaluate(() => window.__beacons.slice()); };
  const clear = () => page.evaluate(() => { window.__beacons.length = 0; });
  return { ctx, page, events, beacons, clear, leaked, errors };
}
const enterZip = async (page, zip) => {
  await page.fill('#zip-banner-input', zip);
  await page.click('#zip-banner-go');
  await page.waitForSelector('#live-grid .car-card', { timeout: 120000 });
};
const count = (list, e) => list.filter(x => x === e).length;

const browser = await chromium.launch();
try {
  /* ---------- web, as a person on yardscout.io ---------- */
  {
    const w = await open(browser, { origin: 'https://yardscout.io', ua: UA_ANDROID });
    check('web: the page thinks it is on yardscout.io and is not automated', await w.page.evaluate(() => location.hostname === 'yardscout.io' && navigator.webdriver === false && !IS_NATIVE && !ANALYTICS_OFF));
    let ev = await w.events();
    check('web: a fresh browser sends one first visit', count(ev, 'first-visit') === 1, JSON.stringify(ev));
    await enterZip(w.page, '85003');
    ev = await w.events();
    check('web: entering a zip counts once', count(ev, 'zip-entered') === 1, JSON.stringify(ev));
    const all = await w.beacons();
    check('web: every beacon says platform web, counting rules v4, and nothing else', all.length > 0 && all.every(b => b.p === 'web' && b.v === 4 && Object.keys(b).sort().join() === 'cmp,e,med,p,src,v'), JSON.stringify(all[0]));

    // Two reloads with the saved zip: the audit recorded "entered a zip" each time.
    ev = [];
    for (let i = 0; i < 2; i++) {
      await w.page.reload({ waitUntil: 'domcontentloaded' });   // the recorder starts empty on each load
      await w.page.waitForSelector('#live-grid .car-card', { timeout: 120000 });
      ev = ev.concat(await w.events());
    }
    check('web: two launches with the saved zip send no "entered a zip" and no first visit', count(ev, 'zip-entered') === 0 && count(ev, 'first-visit') === 0, JSON.stringify(ev));
    await w.page.evaluate(() => { const i = document.getElementById('live-zip'); i.value = '30310'; i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new Event('change', { bubbles: true })); });
    await w.page.waitForFunction(() => localStorage.getItem('jh_zip') === '30310', null, { timeout: 15000 });
    ev = await w.events();
    check('web: changing the zip counts once', count(ev, 'zip-entered') === 1, JSON.stringify(ev));
    await w.clear();

    // One part search, re-rendered the way the audit walked it.
    await w.page.click('.tab[data-tab="parts"]');
    await w.page.waitForFunction(() => document.getElementById('pf-make').options.length > 5, null, { timeout: 30000 });
    await w.page.selectOption('#pf-year', '2009');
    await w.page.selectOption('#pf-make', 'Toyota');
    await w.page.waitForFunction(() => [...document.getElementById('pf-model').options].some(o => o.value === 'Camry'));
    await w.page.selectOption('#pf-model', 'Camry');
    await w.page.click('.pf-tile[data-cat="alternator"]');
    await w.page.waitForFunction(() => document.querySelector('#pf-results .pf-row-card, #pf-results .pf-empty'), null, { timeout: 30000 });
    await w.page.click('#pf-go'); await w.page.click('#pf-go');
    const sort = await w.page.$('#pf-results .pf-sort-btn:not(.active)');
    if (sort) await sort.click();
    await w.page.evaluate(() => pfRunSearch());
    ev = await w.events();
    check('web: one part search, tapped and re-sorted five times, counts once', count(ev, 'part-first-search') === 1 && count(ev, 'pf/alternator') === 1 && count(ev, 'pf-car/toyota-camry') === 1, JSON.stringify(ev));
    await w.clear();

    // Paywall: a free visitor is a prospect; a Pro member and the code re-open are not.
    await w.page.click('.tab[data-tab="live"]');
    await w.page.click('#pro-pill');
    ev = await w.events();
    check('web: a free visitor opening the Pro sheet is one paywall open, with its gate', JSON.stringify(ev) === JSON.stringify(['paywall', 'paywall/header-pill']), JSON.stringify(ev));
    await w.clear();
    // Store link in the sheet: an Android browser goes to Google Play.
    const store = await w.page.evaluate(() => { const a = [...document.querySelectorAll('#upgrade-sheet a[href]')].find(x => /apps\.apple\.com|play\.google\.com/.test(x.href) && x.getClientRects().length);
      if (!a) return null; a.addEventListener('click', e => e.preventDefault()); a.click(); return a.href; });
    ev = await w.events();
    check('web: a store link tap in the Pro sheet is counted per store and place', !!store && count(ev, 'store-click') === 1 && ev.some(e => /^store-click\/(appstore|play)-sheet$/.test(e)), JSON.stringify([store, ev]));
    await w.page.click('#upgrade-close');
    await w.clear();
    await w.page.evaluate(() => { localStorage.setItem('jh_pro', '1'); localStorage.setItem('jh_pro_source', 'account'); applyProGates(); });
    await w.page.click('#pro-pill');
    await w.page.evaluate(() => { closeUpgradeSheet(); openUpgradeSheet('code-redeemed'); closeUpgradeSheet(); openUpgradeSheet('checkout-done'); closeUpgradeSheet(); });
    ev = await w.events();
    check('web: a Pro member tapping "Pro ✓", and the re-opens after a code or a checkout, are not paywall opens', !ev.some(e => /^paywall/.test(e)), JSON.stringify(ev));
    await w.page.evaluate(() => { localStorage.removeItem('jh_pro'); localStorage.removeItem('jh_pro_source'); applyProGates(); openUpgradeSheet('checkout-return'); closeUpgradeSheet(); });
    ev = await w.events();
    check('web: the sheet re-opening on a Stripe return is not a paywall open', !ev.some(e => /^paywall/.test(e)), JSON.stringify(ev));
    check('web: nothing tried to reach the events API over the network', w.leaked.length === 0, JSON.stringify(w.leaked));
    check('web: no page errors', w.errors.length === 0, JSON.stringify(w.errors));
    await w.ctx.close();
  }

  /* ---------- web: how the Cars list is narrowed (2026-11-13) ---------- */
  {
    const w = await open(browser, { origin: 'https://yardscout.io', ua: UA_ANDROID });
    await enterZip(w.page, '85003');
    await w.page.waitForFunction(() => !(typeof _inv !== 'undefined' && _inv && !liveComplete && invViewPending()), null, { timeout: 120000 });
    const narrow = async () => (await w.events()).filter(e => /^narrow\//.test(e));
    // Cars in range: two plain models of one make, and a model with a notable trim.
    const pick = await w.page.evaluate(() => {
      const byMake = new Map(), trims = new Map();
      for (const v of _scopedVehicles) {
        if (!v.make || !v.model || isNoPickModel(v.make, v.model)) continue;
        const m = canonicalModel(v.make, v.model);
        const s = byMake.get(v.make) || new Map(); s.set(m, (s.get(m) || 0) + 1); byMake.set(v.make, s);
        const t = notableTrimOf(v);
        if (t) { const k = v.make + '|' + m + '|' + t; trims.set(k, (trims.get(k) || 0) + 1); }
      }
      const [make, models] = [...byMake.entries()].sort((a, b) => b[1].size - a[1].size)[0];
      const two = [...models.entries()].sort((a, b) => b[1] - a[1]).slice(0, 2).map(x => x[0]);
      const t = [...trims.entries()].sort((a, b) => b[1] - a[1])[0];
      const [tMake, tModel, tWord] = t ? t[0].split('|') : [];
      return { make, models: two, tMake, tModel, tWord };
    });
    check('narrow e2e: fixture has a make with two models and a notable-trim model near 85003', pick.models.length === 2 && !!pick.tWord, JSON.stringify(pick));
    const typeIn = async (text) => {
      await w.page.click('#car-search-input');
      await w.page.fill('#car-search-input', '');
      await w.page.type('#car-search-input', text, { delay: 15 });
      await w.page.waitForTimeout(150);
    };
    const clickSuggestion = async (re) => {
      const i = await w.page.evaluate((src) => { const r = new RegExp(src);
        return [...document.querySelectorAll('#car-search-suggest .compare-suggest-item')].findIndex(e => r.test(e.querySelector('span').textContent.replace(/\s+/g, ' ').trim())); }, re.source);
      if (i < 0) return false;
      await w.page.click(`#car-search-suggest .compare-suggest-item[data-i="${i}"]`);
      await w.page.waitForTimeout(300);
      return true;
    };
    const filtersState = () => w.page.evaluate(() => ({ make: document.getElementById('live-filter-make').value, models: [...selectedModels], trim: liveTrimWord(), box: document.getElementById('car-search-input').value }));
    const pickModelInFilters = async (make, model) => {
      await w.page.selectOption('#live-filter-make', make);
      await w.page.click('#live-filter-model-btn');
      await w.page.check(`#live-filter-model-list input[data-model="${model.replace(/"/g, '\\"')}"]`);
      await w.page.click('#live-filter-model-done');
      await w.page.waitForTimeout(300);
    };
    const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    await w.page.evaluate(() => { const p = document.getElementById('live-controls'); if (!p.classList.contains('open')) document.getElementById('live-filter-toggle').click(); });
    await w.clear();

    // 1. search box pick: one search event, no Filters event
    await typeIn(pick.models[0]);
    const okPick = await clickSuggestion(new RegExp(`^${esc(pick.make)} ${esc(pick.models[0])}$`));
    let st = await filtersState();
    let ev = await narrow();
    check('narrow e2e: a search-box pick sets the filters', okPick && st.make === pick.make && st.models.join() === pick.models[0], JSON.stringify(st));
    check('narrow e2e: a search-box pick = one narrow/search, no Filters event', JSON.stringify(ev) === JSON.stringify(['narrow/search']), JSON.stringify(ev));
    // Moving on afterwards (leaving the tab) must not turn it into a Filters make.
    await w.page.click('.tab[data-tab="parts"]'); await w.page.click('.tab[data-tab="live"]');
    ev = await narrow();
    check('narrow e2e: leaving the tab after a search pick counts no Filters make', JSON.stringify(ev) === JSON.stringify(['narrow/search']), JSON.stringify(ev));
    await typeIn(pick.models[1]);
    await clickSuggestion(new RegExp(`^${esc(pick.make)} ${esc(pick.models[1])}$`));
    ev = await narrow();
    check('narrow e2e: a second search pick the same day is not counted again', JSON.stringify(ev) === JSON.stringify(['narrow/search']), JSON.stringify(ev));
    await w.page.click('#car-search-clear');
    await w.page.waitForTimeout(200);
    await w.clear();

    // 2. Filters Make -> Model: one Filters model event, no search event (the box syncing is not a pick)
    await w.page.selectOption('#live-filter-make', pick.make);
    await w.page.click('#live-filter-model-btn');
    await w.page.check(`#live-filter-model-list input[data-model="${pick.models[0]}"]`);
    await w.page.check(`#live-filter-model-list input[data-model="${pick.models[1]}"]`);
    await w.page.uncheck(`#live-filter-model-list input[data-model="${pick.models[1]}"]`);
    ev = await narrow();
    check('narrow e2e: checkbox ticks alone count nothing (the list is still open)', ev.length === 0, JSON.stringify(ev));
    await w.page.click('#live-filter-model-done');
    await w.page.waitForTimeout(300);
    st = await filtersState();
    ev = await narrow();
    check('narrow e2e: the box shows the Filters choice', st.box === `${pick.make} ${pick.models[0]}`, JSON.stringify(st));
    check('narrow e2e: a model chosen in Filters = one narrow/filters-model, no search and no make-only event', JSON.stringify(ev) === JSON.stringify(['narrow/filters-model']), JSON.stringify(ev));
    await w.page.click('.tab[data-tab="parts"]'); await w.page.click('.tab[data-tab="live"]');
    await pickModelInFilters(pick.make, pick.models[1]);
    ev = await narrow();
    check('narrow e2e: a second Filters model the same day is not counted again; no make-only for it', JSON.stringify(ev) === JSON.stringify(['narrow/filters-model']), JSON.stringify(ev));
    await w.clear();
    // Opening and closing the Model list without a change counts nothing.
    await w.page.click('#live-filter-model-btn'); await w.page.click('#live-filter-model-done');
    check('narrow e2e: opening and closing the Model list unchanged counts nothing', (await narrow()).length === 0);

    // 3. Filters make only: counted when the person moves on, once a day
    await w.page.selectOption('#live-filter-make', pick.tMake);
    ev = await narrow();
    check('narrow e2e: choosing a make in Filters counts nothing yet (a model may follow)', ev.length === 0, JSON.stringify(ev));
    await w.page.click('.tab[data-tab="parts"]'); await w.page.click('.tab[data-tab="live"]');
    ev = await narrow();
    check('narrow e2e: a make chosen in Filters with no model = one narrow/filters-make', JSON.stringify(ev) === JSON.stringify(['narrow/filters-make']), JSON.stringify(ev));
    await w.page.selectOption('#live-filter-make', pick.make);
    await w.page.click('.tab[data-tab="parts"]'); await w.page.click('.tab[data-tab="live"]');
    ev = await narrow();
    check('narrow e2e: a second make-only choice the same day is not counted again', JSON.stringify(ev) === JSON.stringify(['narrow/filters-make']), JSON.stringify(ev));
    await w.clear();

    // 4. Trim filter: one trim event (the model was already counted today)
    await pickModelInFilters(pick.tMake, pick.tModel);
    await w.page.waitForFunction(() => !document.getElementById('live-filter-trim-wrap').hidden, null, { timeout: 10000 });
    await w.page.selectOption('#live-filter-trim', pick.tWord);
    await w.page.waitForTimeout(250);
    st = await filtersState();
    ev = await narrow();
    check('narrow e2e: the Trim filter is set', st.trim === pick.tWord, JSON.stringify(st));
    check('narrow e2e: the Trim filter = one narrow/trim (and nothing for the box showing it)', JSON.stringify(ev) === JSON.stringify(['narrow/trim']), JSON.stringify(ev));
    await w.page.selectOption('#live-filter-trim', '');
    await w.page.selectOption('#live-filter-trim', pick.tWord);
    ev = await narrow();
    check('narrow e2e: the Trim filter again the same day is not counted again', JSON.stringify(ev) === JSON.stringify(['narrow/trim']), JSON.stringify(ev));
    await w.page.click('#car-search-clear');
    await w.page.waitForTimeout(200);
    await w.clear();

    // 5. a trim row from the search box: search-trim only, not the Trim filter
    await typeIn(`${pick.tModel} ${pick.tWord}`);
    const okTrim = await clickSuggestion(new RegExp(`^${esc(pick.tMake)} ${esc(pick.tModel)} · ${esc(pick.tWord)}$`));
    st = await filtersState();
    ev = await narrow();
    check('narrow e2e: a trim row sets make, model and trim', okTrim && st.make === pick.tMake && st.models.join() === pick.tModel && st.trim === pick.tWord, JSON.stringify(st));
    check('narrow e2e: a trim row = one narrow/search-trim, no narrow/trim, no Filters event', JSON.stringify(ev) === JSON.stringify(['narrow/search-trim']), JSON.stringify(ev));
    await w.page.click('#car-search-clear');
    await w.page.waitForTimeout(200);
    await w.clear();

    // 6. a #cars= link: one link event, nothing else
    await w.page.evaluate((h) => { location.hash = h; }, `#cars=${encodeURIComponent(pick.make + '|' + pick.models[0])}`);
    await w.page.waitForFunction((m) => [...selectedModels].join() === m, pick.models[0], { timeout: 15000 });
    ev = await narrow();
    check('narrow e2e: a #cars= link = one narrow/link, no search or Filters event', JSON.stringify(ev) === JSON.stringify(['narrow/link']), JSON.stringify(ev));
    await w.page.click('.tab[data-tab="parts"]'); await w.page.click('.tab[data-tab="live"]');
    await w.page.evaluate((h) => { location.hash = h; }, `#cars=${encodeURIComponent(pick.make + '|' + pick.models[1])}`);
    await w.page.waitForFunction((m) => [...selectedModels].join() === m, pick.models[1], { timeout: 15000 });
    ev = await narrow();
    check('narrow e2e: a second link the same day is not counted again (and leaving the tab adds no make-only)', JSON.stringify(ev) === JSON.stringify(['narrow/link']), JSON.stringify(ev));

    // 7. the per-day rule survives a reload; a new day counts again
    const all = await w.beacons();
    check('narrow e2e: narrowing beacons are ordinary v4 web counters', all.filter(b => /^narrow\//.test(b.e)).every(b => b.p === 'web' && b.v === 4 && Object.keys(b).sort().join() === 'cmp,e,med,p,src,v'), JSON.stringify(all));
    await w.page.reload({ waitUntil: 'domcontentloaded' });
    await w.page.waitForSelector('#live-grid .car-card', { timeout: 120000 });
    await w.page.waitForFunction(() => !(typeof _inv !== 'undefined' && _inv && !liveComplete && invViewPending()), null, { timeout: 120000 });
    await typeIn(pick.models[0]);
    await clickSuggestion(new RegExp(`^${esc(pick.make)} ${esc(pick.models[0])}$`));
    ev = await narrow();
    check('narrow e2e: after a reload the same day a search pick is not counted again', ev.length === 0, JSON.stringify(ev));
    await w.page.evaluate(() => { const s = JSON.parse(localStorage.getItem('ys_narrow')); for (const k of Object.keys(s)) s[k] = '2000-01-01'; localStorage.setItem('ys_narrow', JSON.stringify(s)); });
    await typeIn(pick.models[1]);
    await clickSuggestion(new RegExp(`^${esc(pick.make)} ${esc(pick.models[1])}$`));
    ev = await narrow();
    check('narrow e2e: on a new day the search pick counts again (once)', JSON.stringify(ev) === JSON.stringify(['narrow/search']), JSON.stringify(ev));
    check('narrow e2e: only the day per kind is kept on the device', await w.page.evaluate(() => Object.keys(JSON.parse(localStorage.getItem('ys_narrow'))).every(k => NARROW_KINDS.includes(k))
      && Object.values(JSON.parse(localStorage.getItem('ys_narrow'))).every(v => /^\d{4}-\d{2}-\d{2}$/.test(v))));
    check('narrow e2e: nothing reached the network', w.leaked.length === 0, JSON.stringify(w.leaked));
    check('narrow e2e: no page errors', w.errors.length === 0, JSON.stringify(w.errors));
    await w.ctx.close();
  }

  /* ---------- web, local copy and automated browser: silent ---------- */
  {
    const l = await open(browser, { origin: LOCAL.replace(/\/$/, '') });
    await enterZip(l.page, '85003');
    await l.page.click('#pro-pill');
    const ev = await l.events();
    check('local copy (127.0.0.1): no event at all, though the browser is not automated', ev.length === 0 && await l.page.evaluate(() => navigator.webdriver === false && ANALYTICS_OFF === true), JSON.stringify(ev));
    await l.ctx.close();
    const a = await open(browser, { origin: 'https://yardscout.io', automated: true });
    await enterZip(a.page, '85003');
    await a.page.click('#pro-pill');
    const ev2 = await a.events();
    check('automated browser on yardscout.io: no event at all', ev2.length === 0 && await a.page.evaluate(() => navigator.webdriver === true && ANALYTICS_OFF === true), JSON.stringify(ev2));
    await a.ctx.close();
  }

  /* ---------- the app shells: hostname "localhost", counted ---------- */
  for (const plat of ['ios', 'android']) {
    const n = await open(browser, { origin: 'https://localhost', native: plat, ua: plat === 'android' ? UA_ANDROID : UA_IOS });
    check(`${plat} shell: runs on hostname "localhost" as a native app, analytics on`, await n.page.evaluate(() => location.hostname === 'localhost' && IS_NATIVE && !ANALYTICS_OFF), JSON.stringify(n.errors));
    await enterZip(n.page, '85003');
    await n.page.click('#pro-pill');
    await n.page.waitForFunction(() => /\$1\.99/.test(document.getElementById('iap-subscribe').textContent), null, { timeout: 10000 });
    await n.page.evaluate(() => document.getElementById('iap-subscribe').click());
    const all = await n.beacons();
    const ev = all.map(b => b.e);
    check(`${plat} shell: first visit, zip, paywall and checkout tap all arrive`, ['first-visit', 'zip-entered', 'paywall', 'paywall/header-pill', 'checkout-start', 'checkout/header-pill'].every(e => count(ev, e) === 1), JSON.stringify(ev));
    check(`${plat} shell: every beacon carries platform ${plat} and v4`, all.length >= 6 && all.every(b => b.p === plat && b.v === 4), JSON.stringify(all.map(b => [b.e, b.p, b.v])));
    check(`${plat} shell: the stubbed events API was never contacted`, n.leaked.length === 0, JSON.stringify(n.leaked));
    await n.ctx.close();
  }
} catch (e) {
  check('harness ran to the end', false, String(e && e.stack || e).split('\n').slice(0, 4).join(' | '));
} finally {
  await browser.close();
  server.close();
}
console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
