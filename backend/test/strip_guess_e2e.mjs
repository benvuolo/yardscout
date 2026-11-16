// Where the Cars feed's one-step Monday email meets the no-gate first visit
// (hub, 2026-11-16). A first-time visitor now sees cars around a GUESSED
// place, and a guessed place is never a watch centre. So under a guess the
// strip asks for the zip in the same step as the email:
//   - the strip shows a zip field beside the email field
//   - no zip: nothing is made or sent
//   - zip + email: the zip is saved, ONE watch is made centred on the zip
//     (not on the guess), ONE sign-up is sent with that centre
//   - someone with a saved zip who follows a place link gets no zip field,
//     and the sentence says the watch is around their own location
// Offline: serves docs/ on 127.0.0.1, blocks every other host, answers /geo
// and the sign-up POST itself.
//   node backend/test/strip_guess_e2e.mjs
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
  const u = new URL(q.url, 'http://x');
  if (u.pathname === '/geo') {
    r.writeHead(200, { 'content-type': 'application/json', 'cache-control': 'no-store' });
    r.end(JSON.stringify({ ok: true, lat: 37.3, lng: -121.9, city: 'San Jose', region: 'CA', country: 'US' }));
    return;
  }
  let p = decodeURIComponent(u.pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(DOCS, path.normalize(p));
  if (!f.startsWith(DOCS) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); r.end(); return; }
  r.writeHead(200, { 'content-type': T[path.extname(f)] || 'application/octet-stream' });
  fs.createReadStream(f).pipe(r);
});
await new Promise((res) => srv.listen(0, '127.0.0.1', res));
const BASE = `http://127.0.0.1:${srv.address().port}/`;
const WL = 'yardscout_watchlist';
const ZIP = '95112', ZLAT = 37.34, ZLNG = -121.88;   // the visitor's real place: not the guessed point

let pass = 0, fail = 0;
const ok = (c, msg, extra) => { if (c) { pass++; console.log('  ok   ' + msg); } else { fail++; console.log('  FAIL ' + msg + (extra !== undefined ? '  -> ' + String(typeof extra === 'string' ? extra : JSON.stringify(extra)).slice(0, 400) : '')); } };

const b = await chromium.launch();
async function open(hash, init) {
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 } });
  const page = await ctx.newPage();
  const posts = [];
  await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, (r) => {
    const q = r.request();
    if (q.method() === 'POST' && /\/v1\/recap\/signup$/.test(new URL(q.url()).pathname)) {
      posts.push(JSON.parse(q.postData() || '{}'));
      return r.fulfill({ status: 200, contentType: 'application/json', headers: { 'access-control-allow-origin': '*' }, body: JSON.stringify({ ok: true, state: 'confirm-sent' }) });
    }
    if (q.method() === 'OPTIONS') return r.fulfill({ status: 204, headers: { 'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': '*' } });
    return r.abort();
  });
  await page.addInitScript((i) => {
    localStorage.setItem('jh_honesty_ack', '1');
    // The zip's coordinates are known (so no outside lookup is needed), but
    // no zip is SAVED unless the case says so.
    localStorage.setItem('jh_zip_coords', JSON.stringify({ [i.zip]: { lat: i.lat, lng: i.lng } }));
    if (i.saved) localStorage.setItem('jh_zip', i.zip);
  }, { zip: ZIP, lat: ZLAT, lng: ZLNG, saved: !!(init && init.saved) });
  await page.goto(BASE + hash, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => typeof liveLoaded !== 'undefined' && liveLoaded && !placePending(), null, { timeout: 180000 });
  await page.waitForSelector('#live-grid .watch-strip', { timeout: 60000 });
  return { page, posts, ctx };
}
const strip = (page) => page.evaluate(() => {
  const s = document.querySelector('#live-grid .watch-strip');
  return s ? { mail: s.classList.contains('strip-mail'), text: s.innerText.replace(/\s+/g, ' '), zip: !!s.querySelector('#strip-zip'), email: !!s.querySelector('.mail-email'),
    msg: (s.querySelector('.mail-msg') || {}).textContent || '' } : null;
});

console.log('A first-time visitor under a guess: zip and email in one step');
{
  const { page, posts, ctx } = await open('#cars=Nissan|Xterra');
  const st0 = await page.evaluate(() => ({ guess: locationIsGuess(), savedZip: localStorage.getItem('jh_zip'), line: document.getElementById('place-line-text').innerText }));
  ok(st0.guess && !st0.savedZip && /guess from your internet connection/.test(st0.line), 'the list is centred on a guess and nothing is saved', st0);
  let s = await strip(page);
  ok(s && s.mail && s.zip && s.email, 'the strip shows a zip field beside the email field', s);
  ok(s && /Get a free Monday email with every Nissan Xterra set out within 100 mi of your zip\./.test(s.text), 'the sentence says the email is for cars around the visitor’s zip', s && s.text);
  await page.fill('#live-grid .strip-mail .mail-email', 'visitor@example.com');
  await page.click('#live-grid .strip-mail .mail-form .btn');
  await page.waitForTimeout(500);
  s = await strip(page);
  ok(/Enter a 5-digit zip code\./.test(s.msg) && posts.length === 0 && !(await page.evaluate((k) => localStorage.getItem(k), WL)) && !(await page.evaluate(() => localStorage.getItem('jh_zip'))),
    'no zip: nothing is made, saved or sent', { msg: s.msg, posts: posts.length });
  await page.fill('#strip-zip', ZIP);
  await page.click('#live-grid .strip-mail .mail-form .btn');
  await page.waitForFunction(() => /Check your inbox/.test((document.querySelector('#live-grid .strip-mail') || {}).innerText || ''), null, { timeout: 15000 }).catch(() => {});
  const done = await page.evaluate((k) => ({
    zip: localStorage.getItem('jh_zip'), guess: locationIsGuess(), line: document.getElementById('place-line').style.display,
    wl: JSON.parse(localStorage.getItem(k) || '[]').map(e => ({ make: e.make, model: e.model, lat: e.lat, lng: e.lng, radiusMi: e.radiusMi })),
    strip: (document.querySelector('#live-grid .strip-mail') || {}).innerText || '',
  }), WL);
  ok(done.zip === ZIP && done.guess === false && done.line === 'none', 'the zip is saved and replaces the guess', done);
  ok(done.wl.length === 1 && done.wl[0].make === 'Nissan' && done.wl[0].model === 'Xterra' && done.wl[0].lat === ZLAT && done.wl[0].lng === ZLNG && done.wl[0].radiusMi === 100,
    'one watch, centred on the zip and not on the guessed point', done.wl);
  ok(posts.length === 1 && posts[0].email === 'visitor@example.com' && posts[0].watch && posts[0].watch.make === 'Nissan' && posts[0].watch.model === 'Xterra'
    && posts[0].watch.lat === ZLAT && posts[0].watch.lng === ZLNG && posts[0].watch.radiusMi === 100, 'one sign-up, with the zip’s centre', posts);
  ok(/Check your inbox\./.test(done.strip.replace(/\s+/g, ' ')) && /Watching Nissan Xterra/.test(done.strip.replace(/\s+/g, ' ')), 'the strip says "Check your inbox" and that the car is watched', done.strip);
  await ctx.close();
}

console.log('A zip that cannot be found');
{
  const { page, posts, ctx } = await open('#cars=Nissan|Xterra');
  await page.fill('#live-grid .strip-mail .mail-email', 'visitor@example.com');
  await page.fill('#strip-zip', '00001');   // not in the cache; the lookup host is blocked
  await page.click('#live-grid .strip-mail .mail-form .btn');
  await page.waitForFunction(() => /could not find/.test((document.querySelector('#live-grid .strip-mail .mail-msg') || {}).textContent || ''), null, { timeout: 15000 }).catch(() => {});
  const s = await strip(page);
  ok(/We could not find that one/.test(s.msg) && posts.length === 0 && !(await page.evaluate((k) => localStorage.getItem(k), WL)) && await page.evaluate(() => locationIsGuess()),
    'an unknown zip: a plain message, nothing made or sent, the guess stays', { msg: s.msg, posts: posts.length });
  await ctx.close();
}

console.log('A saved zip, then a place link');
{
  const { page, posts, ctx } = await open('#near=37.3,-121.9,San%20Jose%2C%20CA&cars=Nissan|Xterra', { saved: true });
  const s = await strip(page);
  ok(s && s.mail && !s.zip && s.email, 'no zip field: their own zip is known', s);
  ok(s && /set out within 100 mi of your own location\./.test(s.text), 'the sentence says the watch is around their own location', s && s.text);
  await page.fill('#live-grid .strip-mail .mail-email', 'visitor@example.com');
  await page.click('#live-grid .strip-mail .mail-form .btn');
  await page.waitForFunction(() => /Check your inbox/.test((document.querySelector('#live-grid .strip-mail') || {}).innerText || ''), null, { timeout: 15000 }).catch(() => {});
  ok(posts.length === 1 && posts[0].watch.lat === ZLAT && posts[0].watch.lng === ZLNG, 'the sign-up carries their own zip’s centre, not the link’s place', posts);
  await ctx.close();
}

await b.close(); srv.close();
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
