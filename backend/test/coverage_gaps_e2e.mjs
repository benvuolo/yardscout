// Two coverage requests that the app itself caused (2026-11-11/12):
//   1. "2003 Chevrolet Colorado, alternator": the Colorado starts in 2004. The
//      empty state now points at 2004 instead of "ask us to add it".
//   2. "U-Pull-It, Kennewick, WA": already tracked. The yard request form now
//      says so before sending, and still sends on the second tap.
// Offline: serves docs/ locally and blocks every other host.
//   node backend/test/coverage_gaps_e2e.mjs
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const DOCS = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../docs');
const T = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2', '.webp': 'image/webp' };
const srv = http.createServer((q, r) => {
  let p = decodeURIComponent(new URL(q.url, 'http://x').pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(DOCS, path.normalize(p));
  if (!f.startsWith(DOCS) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); r.end(); return; }
  r.writeHead(200, { 'content-type': T[path.extname(f)] || 'application/octet-stream' });
  fs.createReadStream(f).pipe(r);
});
await new Promise((res) => srv.listen(0, '127.0.0.1', res));
const BASE = `http://127.0.0.1:${srv.address().port}/`;

let pass = 0, fail = 0;
const ok = (c, msg, extra) => { if (c) { pass++; console.log('  ok   ' + msg); } else { fail++; console.log('  FAIL ' + msg + (extra ? '  -> ' + String(extra).slice(0, 300) : '')); } };

const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
const posts = [];
await p.route(/^https?:\/\/(?!127\.0\.0\.1)/, (r) => {
  const q = r.request();
  if (q.method() === 'POST' && /\/v1\/coverage\/request$/.test(q.url())) {
    posts.push(JSON.parse(q.postData() || '{}'));
    return r.fulfill({ status: 200, contentType: 'application/json', headers: { 'access-control-allow-origin': '*' }, body: '{"ok":true}' });
  }
  if (q.method() === 'OPTIONS') return r.fulfill({ status: 204, headers: { 'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': '*' } });
  return r.abort();
});
// Seattle, 100 mi: Kennewick (about 180 mi away) is outside the list.
await p.addInitScript(() => {
  localStorage.setItem('jh_honesty_ack', '1');
  localStorage.setItem('jh_zip', '98101');
  localStorage.setItem('jh_zip_coords', JSON.stringify({ '98101': { lat: 47.61, lng: -122.33 } }));
  localStorage.setItem('jh_radius', '100');
});
await p.goto(BASE, { waitUntil: 'domcontentloaded' });
await p.waitForFunction(() => typeof liveComplete !== 'undefined' && liveComplete, null, { timeout: 180000 });

console.log('Parts tab: a year the model was never built');
await p.click('.tab[data-tab="parts"]');
await p.waitForTimeout(400);
const pick = async (yr, mk, md) => {
  await p.selectOption('#pf-year', yr);
  await p.selectOption('#pf-make', mk);
  await p.waitForFunction(() => document.getElementById('pf-model').options.length > 1, null, { timeout: 15000 });
  await p.selectOption('#pf-model', md);
  await p.click('#pf-part'); await p.fill('#pf-part', 'alternator');
  await p.waitForSelector('#pf-part-suggest [data-cat="alternator"]', { timeout: 15000 });
  await p.dispatchEvent('#pf-part-suggest [data-cat="alternator"]', 'mousedown');
  await p.waitForSelector('#pf-results .pf-row-card, #pf-results .pf-empty', { timeout: 20000 });
};
await pick('2003', 'Chevrolet', 'Colorado');
let st = await p.evaluate(() => {
  const e = document.querySelector('#pf-results .pf-empty');
  return { text: e ? e.innerText.replace(/\s+/g, ' ') : '', fix: e && e.querySelector('.pf-year-fix') ? e.querySelector('.pf-year-fix').dataset.year : null,
    ask: !!(e && e.querySelector('.pfc-ask:not(.pf-year-fix)')) };
});
ok(/Nothing for a 2003 Chevrolet Colorado alternator/.test(st.text), '2003 Colorado says there is nothing for that year', st.text);
ok(/never seen a 2003 Colorado on a lot: the ones we track run 2004–\d{4}/.test(st.text), 'it says the Colorados we track start in 2004', st.text);
ok(st.fix === '2004', 'it offers "search 2004 instead"', st.fix);
ok(!st.ask, 'no "ask us to add it" for a year that does not exist');
ok(!/guess|fits? a 2003/i.test(st.text), 'no fit is claimed for the 2003', st.text);
await p.click('#pf-results .pf-year-fix');
await p.waitForFunction(() => document.getElementById('pf-year').value === '2004', null, { timeout: 10000 });
await p.waitForTimeout(1500);
st = await p.evaluate(() => ({ year: document.getElementById('pf-year').value, model: document.getElementById('pf-model').value,
  nearMsg: !!document.querySelector('#pf-results .pf-year-fix'), text: (document.getElementById('pf-results').innerText || '').replace(/\s+/g, ' ').slice(0, 200) }));
ok(st.year === '2004' && st.model === 'Colorado', 'the tap switches the year to 2004 and keeps the model', JSON.stringify(st));
ok(!st.nearMsg && !/No interchange data yet/.test(st.text), '2004 runs a real search (no "no data" message)', st.text);

// A real car with no coverage keeps the plain message and the ask link.
await pick('2006', 'Audi', 'A3');
st = await p.evaluate(() => { const e = document.querySelector('#pf-results .pf-empty'); return { text: e ? e.innerText.replace(/\s+/g, ' ') : '(rows)', ask: !!(e && e.querySelector('.pfc-ask:not(.pf-year-fix)')), fix: !!(e && e.querySelector('.pf-year-fix')) }; });
ok(st.text === '(rows)' || (st.ask && !st.fix), 'a real uncovered car (2006 A3) still gets "ask us to add it"', JSON.stringify(st));

console.log('Yards tab: asking for a yard we already track');
await p.click('.tab[data-tab="yards"]');
await p.waitForSelector('#yr-name', { state: 'attached' });
const listBtn = await p.$('.yv-btn[data-view="list"]');
if (listBtn) await listBtn.click();
await p.locator('#yr-name').scrollIntoViewIfNeeded();
const inList = await p.evaluate(() => [...document.querySelectorAll('#yards-grid .yard-card')].some(c => /Kennewick/.test(c.innerText)));
ok(!inList, 'Kennewick is not in the 100 mi list from Seattle (the case being fixed)');
await p.fill('#yr-name', 'U-Pull-It');
await p.fill('#yr-where', 'Kennewick, WA');
await p.click('#yr-send');
await p.waitForTimeout(400);
st = await p.evaluate(() => ({ hidden: document.getElementById('yr-covered').hidden, text: document.getElementById('yr-covered').innerText.replace(/\s+/g, ' '), btn: document.getElementById('yr-send').textContent,
  clipped: (() => { const e = document.getElementById('yr-covered'); return e.scrollWidth > e.clientWidth + 1; })() }));
ok(!st.hidden && /We already track U-Pull-It Auto Parts - Kennewick: [\d,]+ cars on the lot, \d+ mi from you/.test(st.text), 'the form says the yard is already tracked, with cars and distance', st.text);
ok(/outside your 100 mi distance/.test(st.text), 'it explains why the yard is not in the list', st.text);
ok(!/Pasco|Yakima/.test(st.text), 'only the Kennewick yard is named', st.text);
ok(st.btn === 'Send anyway' && posts.length === 0, 'nothing is sent on the first tap; the button reads "Send anyway"', `${st.btn} posts=${posts.length}`);
ok(!st.clipped, 'the note is not cut off');
await p.fill('#yr-name', 'U-Pull-It x');
st = await p.evaluate(() => ({ hidden: document.getElementById('yr-covered').hidden, btn: document.getElementById('yr-send').textContent }));
ok(st.hidden && st.btn === 'Request this yard', 'editing the name clears the note', JSON.stringify(st));
await p.fill('#yr-name', 'U-Pull-It');
await p.click('#yr-send');
await p.waitForTimeout(300);
await p.click('#yr-send');
await p.waitForSelector('#yard-request .pfc-thanks', { timeout: 10000 });
ok(posts.length === 1 && posts[0].kind === 'yard' && posts[0].part === 'U-Pull-It' && posts[0].note === 'Kennewick, WA', 'the second tap still sends the request unchanged', JSON.stringify(posts));

// A yard we do not track goes straight through; a name-only match on a big
// chain asks for the city instead of listing dozens.
await p.reload({ waitUntil: 'domcontentloaded' });
await p.waitForFunction(() => typeof liveComplete !== 'undefined' && liveComplete, null, { timeout: 180000 });
st = await p.evaluate(() => ({
  none: coveredYardMatches('Zzyzx Pull Yard', 'Baker, CA').length,
  chain: coveredYardMatches('Pick-n-Pull', '').length,
  chainHtml: yrCoveredHtml(coveredYardMatches('Pick-n-Pull', '')),
  site: coveredYardMatches('U-Pull-It', 'https://upullitwa.example/inventory').map(h => h.name).filter(n => /Kennewick/.test(n)).length,
  squashed: coveredYardMatches('UPullIt', 'Kennewick').map(h => h.name),
  short: coveredYardMatches('U', 'Kennewick').length,
  filler: coveredYardMatches('Auto Parts', '').length,
}));
ok(st.none === 0, 'an unknown yard matches nothing');
ok(st.chain > 4 && /Add the city/.test(st.chainHtml) && !/yr-view/.test(st.chainHtml), 'a chain name with no city asks for the city', `${st.chain} ${st.chainHtml}`);
ok(st.site === 1, 'a website in the second box is not read as a city');
ok(st.squashed.length === 1 && /Kennewick/.test(st.squashed[0]), '"UPullIt" matches "U-Pull-It"', JSON.stringify(st.squashed));
ok(st.short === 0 && st.filler === 0, 'a one-letter name or only filler words match nothing', `${st.short} ${st.filler}`);

await b.close(); srv.close();
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
