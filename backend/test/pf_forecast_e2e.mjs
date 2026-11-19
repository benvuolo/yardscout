/* Browser e2e: the Parts "Best yards for this part" card WITH the real
 * arrival forecast module mounted in it, and the Cars watch strip's forecast
 * (hub, 2026-11-19). The card's own e2e (pf_plan_e2e) uses a stub for the
 * forecast and the forecast's own e2e (forecast_e2e) mounts into a test
 * element; this one runs the two together on the local app, with
 * docs/data/arrivals/ served from a fixture (made-up yards near the test
 * zip; not real data).
 *   - the forecast renders inside the card's .pf-forecast, names the model
 *     and its year span, and says "within R mi" with the search's radius
 *   - the surface tag the app passes (where: 'parts' / 'cars') never reaches
 *     the sentence ("within 100 mi of parts" was the first integration bug)
 *   - eight bars, no horizontal overflow, no page errors
 *   - with the arrivals files missing the card still works and the mount
 *     point takes no space
 * Run: node backend/test/pf_forecast_e2e.mjs   (SHOT=path.png saves a picture) */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const DOCS = path.join(ROOT, 'docs');
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

// ---- fixture (made-up yards and counts near the test zip; not real data) ----
const BUILT = '2026-11-19T07:00:00Z';
const INDEX = {
  builtAt: BUILT, windowStart: '2026-09-24', windowEnd: '2026-11-18', weeks: 8,
  yardFields: ['location', 'lat', 'lng', 'coveredWeeks', 'stale'],
  yards: [
    ['Sample Yard - San Jose', 37.36, -121.90, 8, 0],
    ['Sample Yard - Newark', 37.52, -122.03, 8, 0],
    ['Sample Yard - Stale', 37.40, -121.95, 8, 1],
    ['Sample Yard - Far Away', 45.5, -122.6, 8, 0],
  ],
  makes: { Toyota: ['toyota', 0] },
};
const TOYOTA = {
  builtAt: BUILT, windowEnd: '2026-11-18', make: 'Toyota', slug: 'toyota',
  models: { Camry: [[0, 2009, 2, 1, 3, 2, 1, 2, 3, 4], [1, 2010, 1, 1, 0, 1, 2, 1, 1, 2], [1, 1999, 5, 5, 5, 5, 5, 5, 5, 5], [3, 2009, 9, 9, 9, 9, 9, 9, 9, 9]] },
};
const ARRIVALS = { 'index.json': INDEX, 'toyota.json': TOYOTA };

async function open(browser, { arrivals = true } = {}) {
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
    if (u.hostname === 'yardscout.io') {
      const a = u.pathname.match(/\/data\/arrivals\/([^/]+\.json)$/);
      if (a) return arrivals && ARRIVALS[a[1]] ? route.fulfill({ json: ARRIVALS[a[1]] }) : route.fulfill({ status: 404, body: '' });
      const f = fileFor(u.pathname);
      if (f) return route.fulfill({ path: f, contentType: TYPES[path.extname(f)] || 'application/octet-stream' });
      return route.fulfill({ status: 404, body: '' });
    }
    return route.abort();
  });
  await page.addInitScript((zip) => {
    navigator.sendBeacon = () => true;
    localStorage.setItem('jh_honesty_ack', '1');
    localStorage.setItem('jh_zip', zip);
  }, ZIP);
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e.message).slice(0, 200)));
  await page.goto('https://yardscout.io/', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => typeof liveLoaded !== 'undefined' && liveLoaded && typeof activeZipCoords !== 'undefined' && activeZipCoords, null, { timeout: 120000 });
  await page.evaluate(() => { window.sendEvent = () => {}; });
  return { ctx, page, errors };
}

async function partsSearch(page, [year, make, model], cat) {
  await page.click(".tab[data-tab='parts']");
  await page.waitForSelector('#tab-parts.active', { timeout: 20000 });
  await page.waitForFunction(() => typeof interchangeData !== 'undefined' && interchangeData, null, { timeout: 60000 }).catch(() => page.evaluate(() => loadInterchange()));
  await page.waitForFunction(() => typeof interchangeData !== 'undefined' && interchangeData, null, { timeout: 60000 });
  await page.selectOption('#pf-year', String(year));
  await page.selectOption('#pf-make', make);
  await page.waitForFunction((md) => [...document.getElementById('pf-model').options].some(o => o.value === md), model, { timeout: 10000 });
  await page.selectOption('#pf-model', model);
  await page.evaluate((cat) => { pfCat = interchangeData.categories.find(c => c.id === cat); pfPartInput.value = pfCat.label; pfRunSearch(); }, cat);
  await page.waitForFunction(() => document.querySelector('#pf-results .pf-plan'), null, { timeout: 30000 });
}

const readForecast = (page, sel) => page.evaluate((sel) => {
  const el = document.querySelector(sel);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return { text: el.innerText.replace(/\s+/g, ' ').trim(), bars: el.querySelectorAll('.ysf-bar').length, h: Math.round(r.height),
    right: Math.round(r.right), vw: document.documentElement.clientWidth, scrollW: document.documentElement.scrollWidth };
}, sel);

const browser = await chromium.launch();
try {
  console.log('1. Parts: the card with the real forecast inside');
  {
    const { ctx, page, errors } = await open(browser);
    await partsSearch(page, [2009, 'Toyota', 'Camry'], 'side-mirrors');
    await page.waitForFunction(() => { const e = document.querySelector('#pf-results .pf-plan .pf-forecast'); return e && e.innerText.trim().length > 20; }, null, { timeout: 15000 }).catch(() => {});
    const f = await readForecast(page, '#pf-results .pf-plan .pf-forecast');
    const radius = await page.evaluate(() => pfPlan && pfPlan.radius);
    const span = await page.evaluate(() => pfPlan && [pfPlan.ctx.yrMin, pfPlan.ctx.yrMax]);
    check('the forecast renders inside the card', !!f && f.text.length > 20 && f.h > 40, JSON.stringify(f));
    check('it names the model' + (span && span[0] ? ' and its year span' : ''), !!f && /Camry/i.test(f.text) && (!span || !span[0] || f.text.includes(String(span[0]))), JSON.stringify({ f, span }));
    check('it says "within R mi" with the search radius, and a rate or count sentence', !!f && new RegExp(`within ${radius}\\smi`).test(f.text) && /(a week land|a week lands|weeks lands|landed within|Not enough history)/.test(f.text), JSON.stringify({ f, radius }));
    check('the surface tag never reaches the sentence (no "of parts")', !!f && !/\bof (parts|cars)\b/i.test(f.text), f && f.text);
    check('eight weekly bars', !!f && f.bars === 8, JSON.stringify(f));
    check('facts line and the "not a promise" label', !!f && /in the last 8 weeks at \d+ yards?/.test(f.text) && /Past weeks, not a promise\./.test(f.text), f && f.text);
    check('the stale fixture yard is left out and said so', !!f && /1 yard not counted: list not updating/.test(f.text), f && f.text);
    check('no horizontal overflow', !!f && f.right <= f.vw + 1 && f.scrollW <= f.vw + 1, JSON.stringify(f));
    const yards = await page.evaluate(() => document.querySelectorAll('#pf-results .pf-plan .pf-plan-yard').length);
    check('the yards are still there above it', yards >= 1, String(yards));
    if (process.env.SHOT) {
      await page.evaluate(() => document.querySelector('#pf-results .pf-plan').scrollIntoView({ block: 'start' }));
      await page.locator('#pf-results .pf-plan').screenshot({ path: process.env.SHOT });
    }
    check('no page error', errors.length === 0, errors.join(' | '));
    await ctx.close();
  }

  console.log('2. Cars: the watch strip of one model carries the forecast');
  {
    const { ctx, page, errors } = await open(browser);
    await page.evaluate(() => { carSearchSetFilter('Toyota', 'Camry'); renderLive(); });
    await page.waitForFunction(() => { const e = document.querySelector('#live-grid .strip-forecast'); return e && e.innerText.trim().length > 20; }, null, { timeout: 15000 }).catch(() => {});
    const f = await readForecast(page, '#live-grid .strip-forecast');
    check('the forecast renders in the strip', !!f && f.text.length > 20 && f.bars === 8, JSON.stringify(f));
    check('any year, and no "of cars"', !!f && /Camry, any year/i.test(f.text) && !/\bof (parts|cars)\b/i.test(f.text), f && f.text);
    check('no horizontal overflow', !!f && f.right <= f.vw + 1 && f.scrollW <= f.vw + 1, JSON.stringify(f));
    check('no page error', errors.length === 0, errors.join(' | '));
    await ctx.close();
  }

  console.log('3. No arrivals files yet: the card works, the mount point takes no space');
  {
    const { ctx, page, errors } = await open(browser, { arrivals: false });
    await partsSearch(page, [2009, 'Toyota', 'Camry'], 'side-mirrors');
    await page.waitForTimeout(1500);
    const f = await readForecast(page, '#pf-results .pf-plan .pf-forecast');
    const yards = await page.evaluate(() => document.querySelectorAll('#pf-results .pf-plan .pf-plan-yard').length);
    check('the card shows its yards', yards >= 1, String(yards));
    check('the forecast mount point is empty and takes no space', !!f && f.text === '' && f.h === 0, JSON.stringify(f));
    check('no page error', errors.length === 0, errors.join(' | '));
    await ctx.close();
  }
} finally {
  await browser.close();
}
console.log(`\n${passes} passed, ${failures} failed`);
process.exit(failures ? 1 : 0);
