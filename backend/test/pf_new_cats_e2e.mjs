/* Browser e2e for the 2026-11-09 categories (hub: interchange/categories-ship).
 *
 * The 14 new Parts-tab categories (aftermarket layer + tier D wave 1) must be
 * findable by name in the part search, open a search without a page error,
 * show no catalog group row (OEM sources stay held: GROUP_HOLD_CATS), and
 * no unit row either, except the 7 categories released for Spectra Premium
 * (AM_RELEASED, hub 2026-11-10), which may show its aftermarket rows. A
 * radiator search for a 2012 Equinox 2.4L must show the Spectra unit row
 * (CU13103) without overflow at 390 and 320 px (screenshots saved to
 * $PF_SHOT_DIR when set). Neither the start tiles nor a suggestion row may
 * overflow. Needs docs/data/interchange.json built with the new categories
 * (junkyard_scraper.write_interchange_payload). Serves docs/ locally.
 *
 *   node backend/test/pf_new_cats_e2e.mjs
 * Playwright is pre-installed in this environment (require('playwright')). */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const DOCS = path.join(ROOT, 'docs');
const FAILS = [];
const check = (name, ok, detail = '') => {
  console.log((ok ? 'ok   ' : 'FAIL ') + name + (detail && !ok ? `  [${detail}]` : ''));
  if (!ok) FAILS.push(name);
};

// id -> what a person types
const NEW = { radiator: 'radiator', 'ac-compressor': 'a/c compressor', 'ac-condenser': 'condenser',
  'heater-core': 'heater core', evaporator: 'evaporator', 'throttle-body': 'throttle body',
  'fuel-pump-module': 'fuel pump', 'cv-axle': 'cv axle', strut: 'strut', sunroof: 'sunroof',
  'center-console': 'console', 'door-panel': 'door panel', 'blower-motor': 'blower motor', 'fog-lights': 'fog' };

// released per source (junkyard_scraper.AM_RELEASED["spectrapremium"])
const SPECTRA = new Set(['radiator', 'ac-compressor', 'ac-condenser', 'heater-core', 'evaporator',
  'throttle-body', 'fuel-pump-module']);
const SHOTS = process.env.PF_SHOT_DIR || '';
const cats = new Set(JSON.parse(fs.readFileSync(path.join(DOCS, 'data/interchange.json'), 'utf8')).categories.map(c => c.id));
const missing = Object.keys(NEW).filter(c => !cats.has(c));
if (missing.length) { console.log(`SKIP docs/data/interchange.json lacks ${missing}: build it first`); process.exit(0); }

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.svg': 'image/svg+xml', '.webmanifest': 'application/manifest+json', '.woff2': 'font/woff2' };
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

const OVERFLOW = els => els.filter(e => e.scrollWidth > e.clientWidth + 1
  || [...e.querySelectorAll('*')].some(k => k.getBoundingClientRect().right > e.getBoundingClientRect().right + 1))
  .map(e => e.innerText.slice(0, 40));

const browser = await chromium.launch();
for (const width of [390, 360, 320]) {
  const ctx = await browser.newContext({ viewport: { width, height: 800 } });
  await ctx.addInitScript(() => {
    localStorage.setItem('jh_pro', '1'); localStorage.setItem('jh_pro_source', 'account');
    localStorage.setItem('jh_honesty_ack', '1'); localStorage.setItem('jh_zip', '85003');
  });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  await page.goto(BASE + 'index.html', { waitUntil: 'domcontentloaded' });
  await page.click(".tab[data-tab='parts']");
  await page.waitForSelector('#tab-parts.active #pf-body', { state: 'visible' });
  await page.waitForSelector('#pf-tiles .pf-tile', { timeout: 20000 });
  let bad = await page.$$eval('#pf-tiles .pf-tile', OVERFLOW);
  check(`${width}px: no start tile overflows`, !bad.length, JSON.stringify(bad));
  const box = await page.$eval('#pf-tiles', e => [e.scrollWidth, e.clientWidth]);
  check(`${width}px: tile row fits its box`, box[0] <= box[1] + 1, JSON.stringify(box));
  for (const [cid, q] of Object.entries(NEW)) {
    await page.fill('#pf-part', '');
    await page.type('#pf-part', q);
    const sel = `#pf-part-suggest .compare-suggest-item[data-cat='${cid}']`;
    let found = true;
    try { await page.waitForSelector(sel, { timeout: 5000 }); } catch { found = false; }
    check(`${width}px: '${q}' finds ${cid}`, found,
      found ? '' : (await page.locator('#pf-part-suggest').innerText()).slice(0, 160));
    if (!found) continue;
    bad = await page.$$eval('#pf-part-suggest .compare-suggest-item', OVERFLOW);
    check(`${width}px: '${q}' suggestion rows do not overflow`, !bad.length, JSON.stringify(bad));
    await page.click(sel);
    await page.waitForTimeout(400);
    const res = await page.locator('#pf-results').innerText();
    if (SPECTRA.has(cid)) {
      check(`${width}px: ${cid} shows no catalog group row (OEM held; Spectra released)`,
        !res.includes('factory parts catalog'), res.slice(0, 160));
    } else {
      check(`${width}px: ${cid} shows no unit or catalog group row (groups held)`,
        !res.includes('Aftermarket match') && !res.includes('factory parts catalog'), res.slice(0, 160));
    }
  }
  // a released category with a Spectra unit row for a real lot car
  await page.fill('#pf-part', '');
  await page.type('#pf-part', 'radiator');
  await page.waitForSelector("#pf-part-suggest .compare-suggest-item[data-cat='radiator']", { timeout: 5000 });
  await page.dispatchEvent("#pf-part-suggest .compare-suggest-item[data-cat='radiator']", 'mousedown');
  await page.selectOption('#pf-year', '2012');
  await page.selectOption('#pf-make', 'Chevrolet');
  await page.waitForTimeout(200);
  await page.selectOption('#pf-model', 'Equinox');
  await page.click('#pf-go');
  await page.waitForTimeout(700);
  const chips = page.locator('#pf-engine .pf-chip');
  for (let i = 0; i < await chips.count(); i++) {
    if ((await chips.nth(i).innerText()).includes('2.4')) { await chips.nth(i).click(); break; }
  }
  await page.waitForTimeout(700);
  const rres = await page.locator('#pf-results').innerText();
  check(`${width}px: 2012 Equinox 2.4L radiator shows the Spectra Premium CU13103 row`,
    rres.includes('Spectra Premium') && rres.includes('CU13103'), rres.slice(0, 300));
  check(`${width}px: no catalog group row on the radiator search`, !rres.includes('factory parts catalog'));
  // the new rows: Spectra unit rows, visible overflow only (a child clipped by an
  // overflow:hidden ancestor inside the card, e.g. the photo placeholder, is not)
  bad = await page.$$eval('#pf-results .pf-row-card', els => els.filter(e => e.innerText.includes('Spectra Premium'))
    .filter(e => e.scrollWidth > e.clientWidth + 1 || [...e.querySelectorAll('*')].some(k => {
      for (let a = k.parentElement; a && a !== e; a = a.parentElement) if (getComputedStyle(a).overflowX !== 'visible') return false;
      return k.getBoundingClientRect().right > e.getBoundingClientRect().right + 1;
    })).map(e => e.innerText.slice(0, 60)));
  check(`${width}px: Spectra unit rows do not overflow`, !bad.length, JSON.stringify(bad));
  const wide = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  check(`${width}px: no horizontal page scroll`, !wide);
  if (SHOTS && (width === 390 || width === 320)) {
    await page.locator('#pf-results').screenshot({ path: path.join(SHOTS, `pf_radiator_spectra_${width}.png`) });
  }
  check(`${width}px: no page errors`, !errors.length, errors.slice(0, 3).join('; '));
  await ctx.close();
}
await browser.close();
server.close();
console.log();
if (FAILS.length) { console.log(`FAILED ${FAILS.length}`); process.exit(1); }
console.log('pf_new_cats_e2e: all passed');
