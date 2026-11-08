/* Browser e2e: modelYears (per-model year spans the scan publishes at the
 * top of inventory_live.json and inv/manifest.json, {make: {rawModel:
 * [first, last]}}). With a year chosen, the model pickers (Parts "Your car",
 * the Cars model filter, the Alerts watch builder) offer only models whose
 * span reaches within one year of it. No year = every model; field missing =
 * today's behaviour; a model the user already picked is never dropped.
 * The test gives a real Chevrolet model a 1964-77 span on the shard path
 * and on the full-file path.
 * Run: node backend/test/model_years_e2e.mjs   (Playwright pre-installed) */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const DOCS = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../../docs');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(DOCS, path.normalize(p));
  if (!f.startsWith(DOCS) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' });
  fs.createReadStream(f).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const BASE = `http://127.0.0.1:${server.address().port}/`;

let fails = 0;
const check = (name, ok, d = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + d}`); if (!ok) fails++; };

const browser = await chromium.launch();
async function open(routes) {
  const page = await browser.newPage({ viewport: { width: 390, height: 820 } });
  await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, (r) => r.abort());
  for (const [re, fn] of routes) await page.route(re, fn);
  await page.addInitScript(() => {
    localStorage.setItem('jh_honesty_ack', '1');
    localStorage.setItem('jh_zip', '95112');
    localStorage.setItem('jh_zip_coords', JSON.stringify({ '95112': { lat: 37.3485, lng: -121.8863 } }));
  });
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => typeof liveComplete !== 'undefined' && liveComplete && liveInventory.length > 1000, null, { timeout: 180000 });
  return page;
}
// Publish a span for the target that ends long before 2003, as the scan would.
const publish = (target) => async (route) => {
  const res = await route.fetch(); const j = await res.json();
  j.modelYears = { [target[0]]: { [target[1]]: [1964, 1977] } };
  await route.fulfill({ response: res, json: j });
};

try {
  // 1. choose a real Chevrolet model (single raw spelling, 2+ cars)
  let page = await open([]);
  const target = await page.evaluate(() => {
    const byDisp = new Map(), n = new Map();
    for (const v of liveInventory) {
      if (v.make !== 'Chevrolet' || !v.model) continue;
      const d = canonicalModel(v.make, v.model);
      if (!byDisp.has(d)) byDisp.set(d, new Set());
      byDisp.get(d).add(v.model);
      n.set(v.model, (n.get(v.model) || 0) + 1);
    }
    const ok = [...n.entries()].filter(([m, c]) => c >= 2 && byDisp.get(canonicalModel('Chevrolet', m)).size === 1);
    ok.sort((a, b) => b[1] - a[1]);
    return ok.length ? ['Chevrolet', ok[0][0]] : null;
  });
  // Without the field: today's behaviour, the model is offered with a year chosen.
  const base = await page.evaluate(([make, model]) => {
    const disp = canonicalModel(make, model);
    pfPopulatePickers();
    document.getElementById('pf-year').value = '2003';
    document.getElementById('pf-make').value = make; pfPopulateModels();
    return [...document.getElementById('pf-model').options].some(o => o.value === disp);
  }, target);
  await page.close();
  check('a Chevrolet model with a single raw spelling exists in the data', !!target);
  check('no modelYears published: 2003 Parts picker unchanged (model offered)', base);

  // 2. publish a 1964-77 span for it on each data path
  for (const [name, routes] of [
    ['shard path', [[/data\/inv\/manifest\.json/, publish(target)]]],
    ['full-file path', [[/data\/inv\/manifest\.json/, (r) => r.fulfill({ status: 404, body: '' })], [/data\/inventory_live\.json/, publish(target)]]],
  ]) {
    page = await open(routes);
    const r = await page.evaluate(([make, model]) => {
      const disp = canonicalModel(make, model);
      const pfHas = () => [...document.getElementById('pf-model').options].some(o => o.value === disp);
      const otherPf = () => [...document.getElementById('pf-model').options].filter(o => o.value && o.value !== disp).length;
      pfPopulatePickers();
      const yr = document.getElementById('pf-year');
      document.getElementById('pf-make').value = make;
      yr.value = ''; pfPopulateModels(); const pfNoYear = pfHas();
      yr.value = '2003'; yr.dispatchEvent(new Event('change')); const pf2003 = pfHas(), pfOthers = otherPf();
      yr.value = '1978'; yr.dispatchEvent(new Event('change')); const pf1978 = pfHas();
      // The car already chosen survives a year change that would hide it.
      document.getElementById('pf-model').value = disp;
      yr.value = '2003'; yr.dispatchEvent(new Event('change'));
      const pfKept = document.getElementById('pf-model').value === disp;
      // Cars model filter
      const lo = document.getElementById('live-filter-year-min'), hi = document.getElementById('live-filter-year-max');
      document.getElementById('live-filter-make').value = make;
      const setYr = (v) => { for (const s of [lo, hi]) { if (v && ![...s.options].some(o => o.value === v)) s.insertAdjacentHTML('beforeend', `<option>${v}</option>`); s.value = v; } populateModelFilter(); };
      setYr(''); const liveNoYear = _modelCounts.has(disp);
      setYr('2003'); const live2003 = _modelCounts.has(disp), liveOthers = _modelCounts.size;
      // Alerts watch builder
      const am = document.getElementById('alert-make');
      if (![...am.options].some(o => o.value === make)) am.insertAdjacentHTML('beforeend', `<option>${make}</option>`);
      am.value = make;
      const amin = document.getElementById('alert-yr-min'), amax = document.getElementById('alert-yr-max');
      const setA = (v) => { for (const s of [amin, amax]) { if (v && ![...s.options].some(o => o.value === v)) s.insertAdjacentHTML('beforeend', `<option>${v}</option>`); s.value = v; } amin.dispatchEvent(new Event('change')); };
      setA(''); populateWatchModelOptions(); const watchNoYear = _watchModelCounts.has(model);
      setA('2003'); const watch2003 = _watchModelCounts.has(model), watchOthers = _watchModelCounts.size;
      // A picked model stays when the year range would hide it.
      setA(''); watchSelectedModels.add(model); setA('2003');
      const watchKept = watchSelectedModels.has(model) && _watchModelCounts.has(model);
      return { pfNoYear, pf2003, pfOthers, pf1978, pfKept, liveNoYear, live2003, liveOthers, watchNoYear, watch2003, watchOthers, watchKept,
               inInventory: liveInventory.filter(v => v.make === make && v.model === model).length };
    }, target);
    const d = JSON.stringify(r);
    check(`${name}: the cars stay in inventory`, r.inInventory > 0, d);
    check(`${name}: Parts, no year: offered`, r.pfNoYear, d);
    check(`${name}: Parts, 2003: hidden, other models still offered`, !r.pf2003 && r.pfOthers > 0, d);
    check(`${name}: Parts, 1978 (one year past the span): offered`, r.pf1978, d);
    check(`${name}: Parts, the car already chosen is kept`, r.pfKept, d);
    check(`${name}: Cars filter, no year: offered; 2003: hidden, others offered`, r.liveNoYear && !r.live2003 && r.liveOthers > 0, d);
    check(`${name}: Alerts watch, no year: offered; 2003: hidden, others offered`, r.watchNoYear && !r.watch2003 && r.watchOthers > 0, d);
    check(`${name}: Alerts watch, a picked model is kept when the years change`, r.watchKept, d);
    await page.close();
  }
} finally {
  await browser.close();
  server.close();
}
console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
