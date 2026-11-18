/* E2E: the Parts tab picks up a zip that arrives late (2026-11-18).
 *
 * The bug: a part picked while the zip lookup (api.zippopotam.us) was still
 * out showed "Set a zip code (or use your location) up top", and the line
 * stayed after the zip arrived: setZipCenter ended with pfSyncWhere() and
 * renderLive() and never ran the Parts search again. Fixed in docs/app.js
 * (pfRerunIfPlaceArrived, called from pfSyncWhere).
 *
 * The real docs/ bundle, served AS https://yardscout.io/ by Playwright from
 * disk (as no_gate_e2e.mjs does): no local server, no fixed port, nothing
 * leaves this machine. /geo answers "not ok" (no guessed place), the zip
 * lookup is answered from a table and HELD until the test releases it,
 * everything else is aborted.
 *
 *   typed zip, late    zip typed in the first-visit zip card, Parts opened
 *                      and a part picked while the lookup is held: the
 *                      waiting line shows; release; the results come
 *   saved zip, late    launch with a saved zip whose coordinates are not
 *                      cached (the launch's own lookup is held): same
 *   saved zip, cached  launch with the coordinates cached (setZipCenter runs
 *                      to its end during the launch, before the Parts state
 *                      exists): no page error, results straight away
 *
 * Run: node backend/test/pf_late_zip_e2e.mjs
 * PF_DOCS=<another docs/ folder> runs the same cases against other sources
 * (on the tree before the fix the two "late" cases fail). */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const DOCS = path.resolve(process.env.PF_DOCS || path.join(ROOT, 'docs'));
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json' };
const ZIPS = { 85003: ['33.4511', '-112.0783'] };   // Phoenix: several yards in the checked-in data
const PART = 'headlights';                           // a start tile; browse mode lists every nearby car with it
const WAITING = 'Set a zip code (or use your location) up top';

let failures = 0, passes = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + String(detail).slice(0, 400)}`); if (ok) passes++; else failures++; };

const fileFor = (pathname) => {
  let p = decodeURIComponent(pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(DOCS, path.normalize(p));
  return f.startsWith(DOCS) && fs.existsSync(f) && !fs.statSync(f).isDirectory() ? f : null;
};

async function open(browser, { storage = {} } = {}) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, serviceWorkers: 'block' });
  const page = await ctx.newPage();
  let release;
  const held = new Promise((r) => { release = r; });
  const zipHits = [];
  await page.route('**/*', async (route) => {
    const u = new URL(route.request().url());
    if (u.hostname === 'yardscout.io' && u.pathname === '/geo') return route.fulfill({ json: { ok: false }, headers: { 'cache-control': 'no-store' } });
    const z = u.href.match(/api\.zippopotam\.us\/us\/(\d{5})/);
    if (z) {
      zipHits.push(z[1]);
      await held;   // the lookup stays out until the test releases it
      if (!ZIPS[z[1]]) return route.fulfill({ status: 404, body: '' }).catch(() => {});
      return route.fulfill({ json: { places: [{ latitude: ZIPS[z[1]][0], longitude: ZIPS[z[1]][1] }] }, headers: { 'access-control-allow-origin': '*' } }).catch(() => {});
    }
    if (u.hostname === 'yardscout.io') {
      const f = fileFor(u.pathname);
      if (f) return route.fulfill({ path: f, contentType: TYPES[path.extname(f)] || 'application/octet-stream' });
      return route.fulfill({ status: 404, body: '' });
    }
    return route.abort();
  });
  await page.addInitScript(({ storage }) => {
    navigator.sendBeacon = () => true;   // counters stay on this machine
    if (!sessionStorage.getItem('__seeded')) {
      localStorage.setItem('jh_honesty_ack', '1');
      for (const [k, v] of Object.entries(storage)) localStorage.setItem(k, v);
      sessionStorage.setItem('__seeded', '1');
    }
  }, { storage });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e.message).slice(0, 200)));
  await page.goto('https://yardscout.io/', { waitUntil: 'domcontentloaded' });
  return { ctx, page, errors, zipHits, release };
}

const results = (page) => page.evaluate((waiting) => {
  const out = document.getElementById('pf-results');
  return {
    waiting: out.textContent.includes(waiting),
    head: (out.querySelector('.pf-results-head') || {}).textContent || '',
    text: out.textContent.replace(/\s+/g, ' ').trim().slice(0, 160),
  };
}, WAITING);

async function pickPart(page) {
  await page.click(".tab[data-tab='parts']");
  await page.waitForSelector('#tab-parts.active', { timeout: 20000 });
  await page.waitForSelector(`#pf-tiles .pf-tile[data-cat="${PART}"]`, { timeout: 60000 });
  await page.click(`#pf-tiles .pf-tile[data-cat="${PART}"]`);
}
/** Up to 30 s for the results head (the browse list) to replace the waiting line. */
const resultsCame = (page) => page.waitForFunction(() => !!document.querySelector('#pf-results .pf-results-head'), null, { timeout: 30000 })
  .then(() => true, () => false);

const browser = await chromium.launch();
try {
  /* ---------- typed zip, late ---------- */
  {
    const w = await open(browser);
    await w.page.waitForFunction(() => typeof liveLoaded !== 'undefined' && liveLoaded, null, { timeout: 120000 });
    await w.page.fill('#zip-banner-input', '85003');
    await w.page.click('#zip-banner-go');
    await pickPart(w.page);
    await w.page.waitForFunction((waiting) => document.getElementById('pf-results').textContent.includes(waiting), WAITING, { timeout: 30000 }).catch(() => {});
    const before = await results(w.page);
    check('typed zip, late: the lookup is out when the part is picked', w.zipHits.length >= 1, JSON.stringify(w.zipHits));
    check('typed zip, late: while it is out, the Parts tab asks for a zip', before.waiting, before.text);
    w.release();
    const came = await resultsCame(w.page);
    const after = await results(w.page);
    check('typed zip, late: once the zip arrives, the results come', came && !after.waiting && /near you/.test(after.head), after.text);
    check('typed zip, late: the zip is saved', (await w.page.evaluate(() => localStorage.getItem('jh_zip'))) === '85003');
    check('typed zip, late: no page error', !w.errors.length, w.errors.join(' | '));
    await w.ctx.close();
  }

  /* ---------- saved zip, late (the launch's own lookup is held) ---------- */
  {
    const w = await open(browser, { storage: { jh_zip: '85003' } });
    await pickPart(w.page);
    await w.page.waitForFunction((waiting) => document.getElementById('pf-results').textContent.includes(waiting), WAITING, { timeout: 30000 }).catch(() => {});
    const before = await results(w.page);
    check('saved zip, late: the launch asked for the saved zip', w.zipHits.includes('85003'), JSON.stringify(w.zipHits));
    check('saved zip, late: while it is out, the Parts tab asks for a zip', before.waiting, before.text);
    w.release();
    const came = await resultsCame(w.page);
    const after = await results(w.page);
    check('saved zip, late: once the zip arrives, the results come', came && !after.waiting && /near you/.test(after.head), after.text);
    check('saved zip, late: no page error', !w.errors.length, w.errors.join(' | '));
    await w.ctx.close();
  }

  /* ---------- saved zip, cached: the launch call itself ---------- */
  {
    const coords = JSON.stringify({ 85003: { lat: 33.4511, lng: -112.0783 } });
    const w = await open(browser, { storage: { jh_zip: '85003', jh_zip_coords: coords } });
    w.release();
    await w.page.waitForFunction(() => typeof liveLoaded !== 'undefined' && liveLoaded, null, { timeout: 120000 });
    check('saved zip, cached: the launch makes no lookup', w.zipHits.length === 0, JSON.stringify(w.zipHits));
    check('saved zip, cached: the launch throws nothing (the Parts state is not read before it exists)', !w.errors.length, w.errors.join(' | '));
    await pickPart(w.page);
    const came = await resultsCame(w.page);
    const after = await results(w.page);
    check('saved zip, cached: results straight away, no waiting line', came && !after.waiting, after.text);
    check('saved zip, cached: no page error after the search', !w.errors.length, w.errors.join(' | '));
    await w.ctx.close();
  }
} finally {
  await browser.close();
}
console.log(failures ? `${failures} FAILURE(S), ${passes} passed` : `ALL PASS (${passes})`);
process.exit(failures ? 1 : 0);
