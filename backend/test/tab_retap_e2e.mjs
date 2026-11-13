/* Browser e2e: re-tapping the tab you're on (owner request 2026-11-09).
 * First re-tap closes a screen pushed over the tab (car screen, Walk the
 * rows, the map's yard sheet); the next scrolls the list to the top, instantly
 * under prefers-reduced-motion. Tapping another tab works as before, and app
 * code that calls .click() on the active tab to re-render is unaffected.
 * The car screen and Walk the rows cover the tab bar (they have their own
 * Back), so those two cases call tabRetap() directly; the rest are real taps.
 * Run: node backend/test/tab_retap_e2e.mjs   (Playwright pre-installed) */
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
  const page = await browser.newPage({ viewport: { width: 390, height: 820 }, reducedMotion: 'reduce' });
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
try {
  const page = await open([]);
  const tabSel = (t) => `.tab[data-tab="${t}"]`;
  const y = () => page.evaluate(() => Math.round(window.scrollY));
  // 1. Cars tab: scroll down, open a car, re-tap: the car screen closes first.
  await page.evaluate(() => window.scrollTo(0, 1500));
  // The car screen covers the tab bar, so the re-tap path is called directly
  // here (same function the tab's click runs).
  await page.evaluate(() => openCarDetail(document.querySelector('#live-grid .car-card[data-vkey]').dataset.vkey));
  await page.evaluate(() => tabRetap());
  await page.waitForTimeout(400);
  const afterFirst = await page.evaluate(() => ({ open: !!document.querySelector('#car-detail.open'), y: Math.round(scrollY) }));
  check('re-tap with the car screen open: closes it first', !afterFirst.open, JSON.stringify(afterFirst));
  check('…and keeps the list where it was', afterFirst.y > 1000, JSON.stringify(afterFirst));
  await page.click(tabSel('live'));
  await page.waitForTimeout(400);
  check('second re-tap: scrolls the list to the top (instant with reduced motion)', (await y()) === 0, String(await y()));
  // 2. Yards tab: Walk the rows open, re-tap closes it, again goes to top.
  await page.click(tabSel('yards'));
  await page.waitForTimeout(400);
  await page.evaluate(() => { window.scrollTo(0, 600); openYardRows(document.querySelector('#yards-grid .yard-card[data-loc]').dataset.loc); });
  await page.evaluate(() => tabRetap());
  await page.waitForTimeout(400);
  check('Yards re-tap with Walk the rows open: closes it', !(await page.evaluate(() => !!document.querySelector('#yard-rows.open'))));
  await page.click(tabSel('yards'));
  await page.waitForTimeout(400);
  check('Yards second re-tap: top', (await y()) === 0, String(await y()));
  // 3. Map view: a selected yard sheet closes on re-tap.
  await page.evaluate(() => { setYardsView('map'); renderSchematicMap((getYardsView().shown || []).filter(y => y.lat != null), ''); selectMapYard(document.querySelector('#yards-map .map-pin:not(.map-cluster)').dataset.loc); });
  await page.click(tabSel('yards'));
  await page.waitForTimeout(300);
  check('map: re-tap closes the yard sheet', await page.evaluate(() => _mapSheetLoc === null && !document.querySelector('#yards-map-sheet .map-walk')));
  await page.evaluate(() => setYardsView('list'));
  // 4. Switching to another tab is unchanged: it renders that tab.
  await page.click(tabSel('alerts'));
  await page.waitForTimeout(300);
  check('tapping a different tab switches to it', await page.evaluate(() => document.getElementById('tab-alerts').classList.contains('active')));
  // 4b. Each tab keeps its own place (2026-11-13): a tab not opened yet starts
  // at the top even when the one left was scrolled down; coming back returns
  // to where that tab was left; a re-tap still goes to the top.
  await page.click(tabSel('live'));
  await page.waitForTimeout(300);
  await page.evaluate(() => window.scrollTo(0, 1800));
  const liveY = await y();
  await page.click(tabSel('parts'));
  await page.waitForTimeout(300);
  check('scrolled Cars -> Parts (first visit): opens at the top', (await y()) === 0, String(await y()));
  await page.click(tabSel('yards'));
  await page.waitForTimeout(300);
  check('-> Yards (left at the top earlier): at the top', (await y()) === 0, String(await y()));
  await page.evaluate(() => window.scrollTo(0, 500));
  await page.click(tabSel('alerts'));
  await page.waitForTimeout(300);
  check('scrolled Yards -> Alerts: at the top', (await y()) === 0, String(await y()));
  await page.click(tabSel('live'));
  await page.waitForTimeout(400);
  check('back to Cars: returns to where it was left', liveY > 1000 && Math.abs((await y()) - liveY) <= 2, `${await y()} vs ${liveY}`);
  await page.click(tabSel('yards'));
  await page.waitForTimeout(300);
  check('back to Yards: returns to where it was left', Math.abs((await y()) - 500) <= 2, String(await y()));
  await page.click(tabSel('yards'));
  await page.waitForTimeout(400);
  check('re-tap still goes to the top', (await y()) === 0, String(await y()));
  await page.click(tabSel('alerts'));
  await page.waitForTimeout(300);
  // 5. A programmatic click on the active tab (used by app code to re-render) still re-renders, no scroll.
  await page.evaluate(() => { window.scrollTo(0, 300); document.querySelector('.tab[data-tab="alerts"]').click(); });
  await page.waitForTimeout(300);
  check('programmatic click on the active tab keeps the old behaviour (no jump)', (await y()) === 300, String(await y()));
  await page.close();
} finally {
  await browser.close();
  server.close();
}
console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
