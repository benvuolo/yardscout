/* Browser e2e: noPickModels (data-quality contract, main 4e6fbe7).
 * The scan publishes {make: [model]} at the top of inventory_live.json and
 * inv/manifest.json for raw (make, model) pairs that are mislabelled. Those
 * cars stay in inventory, but the model string is never offered in a model
 * picker: Parts "Your car", the Cars model filter, the Alerts watch picker.
 * The test picks a real Toyota model (one whose display name has no other
 * raw spelling), publishes it as no-pick on the shard path and on the
 * full-file path, and checks all three pickers drop it while the cars stay.
 * Scope: names that come from the inventory ROWS. The Parts picker also
 * lists curated nameplates from interchange.json (real names such as
 * "Camry"); those are not row strings and are not part of this contract, so
 * the check runs before the Parts tab loads that table.
 * Run: node backend/test/no_pick_models_e2e.mjs   (Playwright pre-installed) */
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
const publish = (target) => async (route) => {
  const res = await route.fetch(); const j = await res.json();
  j.noPickModels = { [target[0]]: [target[1]] };
  await route.fulfill({ response: res, json: j });
};

try {
  // 1. choose the target from the real data
  let page = await open([]);
  const target = await page.evaluate(() => {
    const byDisp = new Map(), n = new Map();
    for (const v of liveInventory) {
      if (v.make !== 'Toyota' || !v.model) continue;
      const d = canonicalModel(v.make, v.model);
      if (!byDisp.has(d)) byDisp.set(d, new Set());
      byDisp.get(d).add(v.model);
      n.set(v.model, (n.get(v.model) || 0) + 1);
    }
    const ok = [...n.entries()].filter(([m, c]) => c >= 2 && byDisp.get(canonicalModel('Toyota', m)).size === 1);
    ok.sort((a, b) => b[1] - a[1]);
    return ok.length ? ['Toyota', ok[0][0]] : null;
  });
  await page.close();
  check('a Toyota model with a single raw spelling exists in the data', !!target);

  // 2. publish it on each data path
  for (const [name, routes] of [
    ['shard path', [[/data\/inv\/manifest\.json/, publish(target)]]],
    ['full-file path', [[/data\/inv\/manifest\.json/, (r) => r.fulfill({ status: 404, body: '' })], [/data\/inventory_live\.json/, publish(target)]]],
  ]) {
    page = await open(routes);
    const r = await page.evaluate(([make, model]) => {
      const disp = canonicalModel(make, model);
      const inInventory = liveInventory.filter(v => v.make === make && v.model === model).length;
      pfPopulatePickers();
      document.getElementById('pf-make').value = make; pfPopulateModels();
      const pf = [...document.getElementById('pf-model').options].some(o => o.value === disp);
      document.getElementById('live-filter-make').value = make; populateModelFilter();
      const live = _modelCounts.has(disp);
      const am = document.getElementById('alert-make');
      if (![...am.options].some(o => o.value === make)) am.insertAdjacentHTML('beforeend', `<option>${make}</option>`);
      am.value = make; populateWatchModelOptions();
      const watch = _watchModelCounts.has(model);
      // Control: a different Toyota model is still offered everywhere.
      const other = [..._watchModelCounts.keys()][0];
      return { read: isNoPickModel(make, model), inInventory, pf, live, watch, other };
    }, target);
    check(`${name}: published noPickModels is read (${target.join(' ')})`, r.read, JSON.stringify(r));
    check(`${name}: those cars stay in inventory`, r.inInventory > 0, JSON.stringify(r));
    check(`${name}: Parts "Your car" does not offer it`, !r.pf, JSON.stringify(r));
    check(`${name}: Cars model filter does not offer it`, !r.live, JSON.stringify(r));
    check(`${name}: Alerts watch picker does not offer it, other models still offered`, !r.watch && !!r.other, JSON.stringify(r));
    await page.close();
  }
} finally {
  await browser.close();
  server.close();
}
console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
