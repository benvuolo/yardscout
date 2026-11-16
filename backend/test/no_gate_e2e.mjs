/* E2E: a first visit shows cars, not a zip gate (2026-11-16).
 *
 * The real docs/ bundle, served AS https://yardscout.io/ by Playwright from
 * disk (like funnel_events_e2e.mjs, so the anonymous counters really fire and
 * are caught by a stubbed sendBeacon). Nothing leaves this machine: /geo is
 * answered per case, the zip lookups are stubbed, everything else is aborted.
 *
 *   guess ok         cars render with no zip typed; the line names the city;
 *                    nothing written to jh_zip / jh_zip_coords / jh_gps; a
 *                    watch asks for the zip first and is then centred on it;
 *                    'first-view-guess' once per visit, 'guess-replaced' once
 *   zip replaces     the line's zip field: saved, line gone, chip back, no
 *                    /geo on the next launch
 *   guess not ok, failing, slow (over 2.5 s), no city
 *   car-named zip card ("Find a Nissan Xterra near you"), make only, none
 *   #yard= and #near=, with and without a saved zip, with #cars=, bad input
 *   ATTRIB: utm_source=page never replaces an outside source
 *   pure helpers: parseNearHash, parseYardHash, geoAnswerOk, attribKeepsStored
 *
 * Run: node backend/test/no_gate_e2e.mjs */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { serveWithNotableTrims } from './notable_trims_fixture.mjs';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const DOCS = path.join(ROOT, 'docs');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json' };
const ZIPS = { 95814: ['38.5816', '-121.4944'], 85003: ['33.4511', '-112.0783'] };
const UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';
const SAC = { ok: true, lat: 38.6, lng: -121.5, city: 'Sacramento', region: 'CA', country: 'US' };
const YARD = 'Pick-n-Pull - Rancho Cordova';   // a yard in the checked-out data, near Sacramento
const SHOTS = process.env.NOGATE_SHOTS || '';   // a folder: save the phone screenshots there

let failures = 0, passes = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + String(detail).slice(0, 400)}`); if (ok) passes++; else failures++; };

const fileFor = (pathname) => {
  let p = decodeURIComponent(pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(DOCS, path.normalize(p));
  return f.startsWith(DOCS) && fs.existsSync(f) && !fs.statSync(f).isDirectory() ? f : null;
};

/* geo: an object (the answer), 'fail' (500), 'abort', or { delay, answer }. */
async function open(browser, { geo = { ok: false }, hash = '', search = '', storage = null, scheme = 'light' } = {}) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, hasTouch: true, userAgent: UA,
    serviceWorkers: 'block', colorScheme: scheme });
  const page = await ctx.newPage();
  const geoHits = [];
  const leaked = [];
  await page.route('**/*', async (route) => {
    const u = new URL(route.request().url());
    if (u.hostname === 'yardscout.io' && u.pathname === '/geo') {
      geoHits.push(u.href);
      const g = typeof geo === 'function' ? geo() : geo;
      if (g === 'abort') return route.abort();
      if (g === 'fail') return route.fulfill({ status: 500, body: 'no' });
      if (g && g.delay) {
        await new Promise((r) => setTimeout(r, g.delay));
        return route.fulfill({ json: g.answer, headers: { 'cache-control': 'no-store' } }).catch(() => {});
      }
      return route.fulfill({ json: g, headers: { 'cache-control': 'no-store' } });
    }
    const z = u.href.match(/api\.zippopotam\.us\/us\/(\d{5})/);
    if (z && ZIPS[z[1]]) return route.fulfill({ json: { places: [{ latitude: ZIPS[z[1]][0], longitude: ZIPS[z[1]][1] }] }, headers: { 'access-control-allow-origin': '*' } });
    if (u.hostname === 'yardscout.io') {
      const f = fileFor(u.pathname);
      const nt = f && serveWithNotableTrims(f);
      if (nt) return route.fulfill({ body: nt, contentType: 'application/json' });
      if (f) return route.fulfill({ path: f, contentType: TYPES[path.extname(f)] || 'application/octet-stream' });
      return route.fulfill({ status: 404, body: '' });
    }
    if (/yardscout-api|workers\.dev/.test(u.hostname)) leaked.push(u.href);
    return route.abort();
  });
  await page.addInitScript(({ storage }) => {
    Object.defineProperty(Navigator.prototype, 'webdriver', { get: () => false, configurable: true });
    window.__beacons = [];
    window.__beaconsFull = [];
    navigator.sendBeacon = (url, blob) => { blob.text().then((t) => { const b = JSON.parse(t); window.__beacons.push(b.e); window.__beaconsFull.push(b); }); return true; };
    if (!sessionStorage.getItem('__seeded')) {
      localStorage.setItem('jh_honesty_ack', '1');
      for (const [k, v] of Object.entries(storage || {})) localStorage.setItem(k, v);
      sessionStorage.setItem('__seeded', '1');
    }
  }, { storage });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e.message).slice(0, 200)));
  await page.goto('https://yardscout.io/' + search + hash, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => typeof liveLoaded !== 'undefined' && liveLoaded, null, { timeout: 120000 });
  const events = async () => { await page.waitForTimeout(300); return page.evaluate(() => window.__beacons.slice()); };
  const state = () => page.evaluate(() => ({
    zip: localStorage.getItem('jh_zip'), coords: localStorage.getItem('jh_zip_coords'), gps: localStorage.getItem('jh_gps'),
    guess: locationIsGuess(), temp: _tempPlace ? { kind: _tempPlace.kind, label: _tempPlace.label, saved: _tempPlace.saved } : null,
    center: activeZipCoords, own: ownCenter(),
    banner: getComputedStyle(document.getElementById('zip-banner')).display !== 'none',
    head: document.getElementById('zip-banner-head').textContent, lead: document.getElementById('zip-banner-lead').textContent,
    line: getComputedStyle(document.getElementById('place-line')).display !== 'none',
    lineText: document.getElementById('place-line-text').textContent.replace(/\s+/g, ' ').trim(),
    formShown: !document.getElementById('place-line-form').hidden,
    changeShown: !document.getElementById('place-line-change').hidden,
    back: document.getElementById('place-line-back').hidden ? null : document.getElementById('place-line-back').textContent,
    chip: getComputedStyle(document.getElementById('zip-chip')).display !== 'none',
    yardFilter: document.getElementById('live-filter-location').value,
    make: document.getElementById('live-filter-make').value,
    cards: document.querySelectorAll('#live-grid .car-card').length,
    watches: loadWatchlist().length,
    url: location.href,
  }));
  const cars = () => page.waitForSelector('#live-grid .car-card', { timeout: 120000 });
  return { ctx, page, geoHits, leaked, errors, events, state, cars };
}
const count = (list, e) => list.filter((x) => x === e).length;
/* NOGATE_SHOTS=<dir>: the screen at 390 px, light and dark, tall enough to show what is under the line. */
const shot = async (page, name) => {
  if (!SHOTS) return;
  fs.mkdirSync(SHOTS, { recursive: true });
  await page.evaluate(() => window.scrollTo(0, 0));
  const fixed = await page.evaluate(() => { const els = [...document.querySelectorAll('body *')].filter((e) => getComputedStyle(e).position === 'fixed'); els.forEach((e) => e.style.setProperty('visibility', 'hidden', 'important')); return els.length; });
  for (const scheme of ['light', 'dark']) {
    await page.emulateMedia({ colorScheme: scheme });
    await page.waitForTimeout(200);
    await page.screenshot({ path: path.join(SHOTS, `${name}-390-${scheme}.png`), fullPage: true, clip: { x: 0, y: 0, width: 390, height: 1700 } });
  }
  await page.emulateMedia({ colorScheme: null });
  if (fixed) await page.evaluate(() => [...document.querySelectorAll('body *')].forEach((e) => e.style.removeProperty('visibility')));
};

const browser = await chromium.launch();
try {
  /* ---------- pure helpers ---------- */
  {
    const w = await open(browser, { geo: 'abort' });
    const r = await w.page.evaluate(() => ({
      near: parseNearHash('#near=38.58,-121.49,Sacramento%2C%20CA'),
      nearAmp: parseNearHash('#near=38.58%2C-121.49%2CSacramento&cars=Nissan|Xterra'),
      nearOut: [parseNearHash('#near=0,0,Null Island'), parseNearHash('#near=51.5,-0.12,London'), parseNearHash('#near=95,-100,x'), parseNearHash('#near=abc,-100,x'), parseNearHash('#near=38.5'), parseNearHash('#near=%E0%A4%A')],
      nearLabel: parseNearHash('#near=38.58,-121.49,' + encodeURIComponent('<b>Sacramento</b> "town"\n with a very long name that goes past forty characters')),
      nearNoLabel: parseNearHash('#near=38.58,-121.49'),
      yard: parseYardHash('#yard=' + encodeURIComponent('U-Pull & Pay - Denver') + '&cars=Toyota'),
      yardBad: [parseYardHash('#yard='), parseYardHash('#yardx=1'), parseYardHash('#yard=%E0%A4%A')],
      cars: parseCarsHash('#yard=X&cars=Nissan|Xterra'), carsPlain: parseCarsHash('#cars=Toyota'),
      geo: [geoAnswerOk({ ok: true, lat: 38.6, lng: -121.5, city: 'Sacramento', region: 'CA' }), geoAnswerOk({ ok: true, lat: 45.5, lng: -73.6, city: '', region: 'QC' }),
        geoAnswerOk({ ok: false }), geoAnswerOk({ ok: true, lat: 51.5, lng: -0.1 }), geoAnswerOk({ ok: true, lat: '38', lng: '-121' }), geoAnswerOk(null),
        geoAnswerOk({ ok: true, lat: 38.6, lng: -121.5, city: '<img src=x>Sac', region: 'C<A' })],
      keep: [attribKeepsStored({ src: 'reddit', at: Date.now() }, 'page', Date.now()), attribKeepsStored({ src: 'reddit', at: Date.now() }, 'google', Date.now()),
        attribKeepsStored(null, 'page', Date.now()), attribKeepsStored({ src: 'page', at: Date.now() }, 'page', Date.now()),
        attribKeepsStored({ src: 'reddit', at: Date.now() - 91 * 86400000 }, 'page', Date.now())],
    }));
    check('#near= parses lat, lng and the label', JSON.stringify(r.near) === JSON.stringify({ lat: 38.58, lng: -121.49, label: 'Sacramento, CA' }), JSON.stringify(r.near));
    check('#near= works encoded and before &cars=', r.nearAmp && r.nearAmp.lat === 38.58 && r.nearAmp.label === 'Sacramento', JSON.stringify(r.nearAmp));
    check('#near= outside the US and Canada, out of range, not numbers or broken: ignored', r.nearOut.every((x) => x === null), JSON.stringify(r.nearOut));
    check('#near= label: plain text, at most 40 characters', r.nearLabel && !/[<>"\n]/.test(r.nearLabel.label) && r.nearLabel.label.length <= 40 && /^Sacramento town with/.test(r.nearLabel.label), JSON.stringify(r.nearLabel));
    check('#near= with no label is still a place', r.nearNoLabel && r.nearNoLabel.label === '', JSON.stringify(r.nearNoLabel));
    check('#yard= gives the yard name as in the data (encoded &, before &cars=)', r.yard === 'U-Pull & Pay - Denver', r.yard);
    check('#yard= empty, another key or broken: none', r.yardBad.every((x) => x === null), JSON.stringify(r.yardBad));
    check('#cars= still parses after a place, and alone', r.cars && r.cars.make === 'Nissan' && r.cars.model === 'Xterra' && r.carsPlain.make === 'Toyota', JSON.stringify([r.cars, r.carsPlain]));
    check('/geo answer: ok with city and region', JSON.stringify(r.geo[0]) === JSON.stringify({ lat: 38.6, lng: -121.5, label: 'Sacramento, CA' }), JSON.stringify(r.geo[0]));
    check('/geo answer: no city keeps the point, no label', r.geo[1] && r.geo[1].label === '' && r.geo[1].lat === 45.5, JSON.stringify(r.geo[1]));
    check('/geo answer: not ok, abroad, strings, null: none', r.geo.slice(2, 6).every((x) => x === null), JSON.stringify(r.geo.slice(2, 6)));
    check('/geo answer: markup in the city is dropped, a bad region left out', r.geo[6] && r.geo[6].label === 'Sac', JSON.stringify(r.geo[6]));
    check('ATTRIB rule: page keeps an outside source; anything else replaces; page replaces page or an expired one', JSON.stringify(r.keep) === JSON.stringify([true, false, false, false, false]), JSON.stringify(r.keep));
    await w.ctx.close();
  }

  /* ---------- guess ok ---------- */
  {
    const w = await open(browser, { geo: SAC });
    await w.cars();
    let s = await w.state();
    check('guess: cars render with no zip typed', s.cards > 0 && !s.banner, JSON.stringify({ cards: s.cards, banner: s.banner }));
    check('guess: the line names the place and says it is a guess', s.line && s.lineText === 'Showing yards near Sacramento, CA. That is a guess from your internet connection.', s.lineText);
    // The line starts as one sentence and a "Change" button, so cars sit on
    // the first screen; the button opens the zip field and "Use my location".
    check('guess: the line starts closed: the sentence and one "Change" button', !s.formShown && s.changeShown && !s.back
      && await w.page.evaluate(() => document.getElementById('place-line-change').getBoundingClientRect().width > 0
        && ['place-line-input', 'place-line-go', 'place-line-gps'].every((id) => document.getElementById(id).getBoundingClientRect().width === 0)), JSON.stringify(s));
    await shot(w.page, 'guess-line-closed');
    await w.page.click('#place-line-change');
    s = await w.state();
    check('guess: "Change" opens the zip field, its button and "Use my location", with the cursor in the field', s.formShown && !s.changeShown && !s.back
      && await w.page.evaluate(() => ['place-line-input', 'place-line-go', 'place-line-gps'].every((id) => document.getElementById(id).getBoundingClientRect().width > 0)
        && document.activeElement === document.getElementById('place-line-input')), JSON.stringify(s));
    await w.page.evaluate(() => renderLive());
    check('guess: the open field stays open when the list redraws', (await w.state()).formShown);
    check('guess: nothing written to jh_zip, jh_zip_coords or jh_gps', s.zip === null && s.coords === null && s.gps === null, JSON.stringify(s));
    check('guess: locationIsGuess() and no own centre', s.guess === true && s.own === null && s.center && s.center.lat === 38.6, JSON.stringify(s));
    check('guess: /geo asked exactly once', w.geoHits.length === 1, String(w.geoHits.length));
    check('guess: no zip chip (the line does its job)', !s.chip);
    const ev = await w.events();
    check('guess: "first-view-guess" counted once', count(ev, 'first-view-guess') === 1 && count(ev, 'zip-entered') === 0, JSON.stringify(ev));
    const all = await w.page.evaluate(() => [...document.querySelectorAll('#live-grid .car-card')].length);
    check('guess: the radius loader serves the guessed area (cars near Sacramento)', await w.page.evaluate(() => getFilteredLive().slice(0, 50).every((v) => vehicleDistanceMi(v) <= effectiveRadiusMi())), String(all));
    check('guess: the yard filter lists yards around the guess', await w.page.evaluate(() => document.getElementById('live-filter-location').options.length > 1 && !document.getElementById('live-filter-location').disabled));
    check('guess: the Parts tab says where, and that it is a guess', /Sacramento, CA \(a guess\)/.test(await w.page.evaluate(() => document.getElementById('pf-where-sum') ? document.getElementById('pf-where-sum').textContent : 'Sacramento, CA (a guess)')));
    await shot(w.page, 'guess-line');
    // A watch while the place is a guess: the zip step runs.
    const r = await w.page.evaluate(() => addQuickWatch('Toyota', 'Camry', null, null, 'test'));
    check('guess: addQuickWatch answers no-zip', r === 'no-zip', r);
    // The card bell when the card has one; else the same step the bell takes on 'no-zip'.
    const viaBell = await w.page.evaluate(() => {
      const b = document.querySelector('#live-grid .watch-btn');
      if (b) { b.click(); return true; }
      askZipForWatch('Toyota Camry', () => { const r = addQuickWatch('Toyota', 'Camry', null, null, 'test'); if (r !== 'added') throw new Error(r); });
      return false;
    });
    console.log(`  (watch step via ${viaBell ? 'a card bell' : 'askZipForWatch, as the bell does on no-zip'})`);
    await w.page.waitForSelector('#watch-toast-zip', { timeout: 5000 }).catch(() => {});
    s = await w.state();
    const toast = await w.page.evaluate(() => (document.getElementById('watch-toast') || document.querySelector('.watch-toast') || { innerText: '' }).innerText);
    check('guess: the bell asks for the zip ("Enter your zip so we know where near you is"), no watch saved', /Enter your zip so we know where/.test(toast) && s.watches === 0, toast);
    await w.page.fill('#watch-toast-zip', '95814');
    await w.page.keyboard.press('Enter');
    await w.page.waitForFunction(() => loadWatchlist().length > 0, null, { timeout: 10000 }).catch(() => {});
    s = await w.state();
    const wl = await w.page.evaluate(() => loadWatchlist()[0] || null);
    check('guess -> zip in the toast: the watch is made, centred on the zip, not the guess', wl && Math.abs(wl.lat - 38.5816) < 1e-6 && Math.abs(wl.lng + 121.4944) < 1e-6, JSON.stringify(wl));
    check('guess -> zip: saved for good, guess gone, line gone, chip back', s.zip === '95814' && !s.guess && !s.temp && !s.line && s.chip, JSON.stringify(s));
    const ev2 = await w.events();
    check('guess -> zip: "guess-replaced" and "zip-entered" once each', count(ev2, 'guess-replaced') === 1 && count(ev2, 'zip-entered') === 1, JSON.stringify(ev2));
    check('guess: no request to the production API', w.leaked.filter((u) => !/\/v1\/events/.test(u)).length === 0, JSON.stringify(w.leaked));
    check('guess: no page errors', w.errors.length === 0, JSON.stringify(w.errors));
    await w.ctx.close();
  }

  /* ---------- the line's zip field replaces the guess; a reload is the same visit ---------- */
  {
    const w = await open(browser, { geo: SAC });
    await w.cars();
    await w.page.reload({ waitUntil: 'domcontentloaded' });
    await w.page.waitForFunction(() => typeof liveLoaded !== 'undefined' && liveLoaded && !!_tempPlace, null, { timeout: 60000 });
    const evR = await w.events();
    check('reload (same visit): /geo asked again (nothing saved) but counted once in total', w.geoHits.length === 2 && count(evR, 'first-view-guess') === 0, `${w.geoHits.length} ${JSON.stringify(evR)}`);
    await w.page.click('#place-line-change');
    await w.page.fill('#place-line-input', '9581');
    await w.page.click('#place-line-go');
    let msg = await w.page.textContent('#place-line-msg');
    check('the line\'s field: a half zip says what is wrong, keeps the guess', /5-digit zip/.test(msg) && (await w.state()).guess, msg);
    await w.page.fill('#place-line-input', '95814');
    await w.page.click('#place-line-go');
    await w.page.waitForFunction(() => !_tempPlace, null, { timeout: 10000 }).catch(() => {});
    const s = await w.state();
    check('the line\'s field: the zip replaces the guess for good', s.zip === '95814' && !s.line && s.chip && s.center && Math.abs(s.center.lat - 38.5816) < 1e-6, JSON.stringify(s));
    const ev = await w.events();
    check('the line\'s field: "guess-replaced" once', count(ev, 'guess-replaced') === 1, JSON.stringify(ev));
    await w.page.reload({ waitUntil: 'domcontentloaded' });
    await w.page.waitForFunction(() => typeof liveLoaded !== 'undefined' && liveLoaded, null, { timeout: 60000 });
    await w.page.waitForTimeout(400);
    check('next launch with a saved zip: /geo is not asked', w.geoHits.length === 2, String(w.geoHits.length));
    await w.ctx.close();
  }

  /* ---------- no guess: not ok, failing, slow, no city ---------- */
  for (const [name, geo] of [['not ok', { ok: false }], ['failing (500)', 'fail'], ['unreachable', 'abort'], ['abroad', { ok: true, lat: 51.5, lng: -0.1, city: 'London', region: 'ENG', country: 'GB' }]]) {
    const w = await open(browser, { geo });
    await w.page.waitForTimeout(600);
    const s = await w.state();
    check(`guess ${name}: today's zip card, unchanged`, s.banner && s.head === 'Where are you?' && /show you what.s in the self-service yards near you/.test(s.lead) && !s.line && !s.temp, JSON.stringify(s));
    const ev = await w.events();
    check(`guess ${name}: nothing counted for a guess`, count(ev, 'first-view-guess') === 0, JSON.stringify(ev));
    await w.ctx.close();
  }
  {
    const w = await open(browser, { geo: { delay: 4500, answer: SAC } });
    const t0 = Date.now();
    await w.page.waitForFunction(() => getComputedStyle(document.getElementById('zip-banner')).display !== 'none', null, { timeout: 8000 }).catch(() => {});
    const waited = Date.now() - t0;
    let s = await w.state();
    check('guess slow: the zip card after about 2.5 s', s.banner && !s.temp && waited < 4000, `${waited} ms ${JSON.stringify(s)}`);
    await w.page.waitForTimeout(3500);
    s = await w.state();
    check('guess slow: a late answer is not applied', s.banner && !s.temp && !s.center, JSON.stringify(s));
    await w.ctx.close();
  }
  {
    const w = await open(browser, { geo: { ok: true, lat: 38.6, lng: -121.5, city: '', region: '', country: 'US' } });
    await w.cars();
    const s = await w.state();
    check('guess with no city: "near your internet connection\'s location"', s.line && s.lineText === 'Showing yards near your internet connection’s location. That is a guess.', s.lineText);
    await w.ctx.close();
  }

  /* ---------- the zip card names the car ---------- */
  {
    const w = await open(browser, { geo: { ok: false }, hash: '#cars=Nissan|Xterra|2000-2004' });
    await w.page.waitForTimeout(500);
    const s = await w.state();
    check('zip card with a cars link: "Find a Nissan Xterra near you"', s.banner && s.head === 'Find a Nissan Xterra near you', s.head);
    check('zip card with a cars link: the first sentence names it (no years, no counts)', s.lead === 'Enter your zip or postal code and we’ll list every Nissan Xterra in the self-service yards near you.', s.lead);
    await shot(w.page, 'zip-card-car');
    await w.ctx.close();
  }
  {
    const w = await open(browser, { geo: 'fail', hash: '#cars=acura' });
    await w.page.waitForTimeout(500);
    const s = await w.state();
    check('zip card, make only: "Find an Acura near you"', s.head === 'Find an Acura near you' && /list every Acura in the/.test(s.lead), `${s.head} | ${s.lead}`);
    await w.ctx.close();
  }

  /* ---------- #yard= ---------- */
  {
    const w = await open(browser, { geo: SAC, hash: '#yard=' + encodeURIComponent(YARD) });
    await w.cars();
    const s = await w.state();
    check('#yard= (nothing saved): /geo is not asked', w.geoHits.length === 0, String(w.geoHits.length));
    check('#yard=: the line names the yard, from the page you came from', s.line && s.lineText === `Showing the cars at ${YARD} (from the page you came from).`, s.lineText);
    check('#yard=: the Cars list is filtered to that yard', s.yardFilter === YARD && await w.page.evaluate((y) => getFilteredLive().every((v) => v.location === y) && getFilteredLive().length > 0, YARD), s.yardFilter);
    check('#yard=: never saved, never a watch centre', s.zip === null && s.coords === null && s.guess && await w.page.evaluate(() => addQuickWatch('Toyota', 'Camry', null, null, 'test')) === 'no-zip', JSON.stringify(s));
    check('#yard=: the hash is cleared', !/#/.test(s.url), s.url);
    await shot(w.page, 'yard-link-line');
    await w.ctx.close();
  }
  {
    const saved = { jh_zip: '85003', jh_zip_coords: JSON.stringify({ 85003: { lat: 33.4511, lng: -112.0783 } }) };
    const w = await open(browser, { geo: SAC, hash: '#yard=' + encodeURIComponent(YARD) + '&cars=Toyota', storage: saved });
    await w.cars();
    await w.page.waitForFunction(() => document.getElementById('live-filter-make').value === 'Toyota', null, { timeout: 30000 }).catch(() => {});
    let s = await w.state();
    check('#yard=&cars= with a saved zip: the yard for this visit, the make applied', s.yardFilter === YARD && s.make === 'Toyota' && s.temp && s.temp.saved, JSON.stringify(s));
    check('#yard= with a saved zip: the zip is kept, one tap back offered', s.zip === '85003' && s.back === 'Back to 85003' && !s.formShown && !s.changeShown && !s.guess, JSON.stringify(s));
    check('#yard= with a saved zip: a watch keeps the saved centre', await w.page.evaluate(() => { const r = addQuickWatch('Honda', 'Civic', null, null, 'test'); const e = loadWatchlist().find((x) => x.make === 'Honda'); return r === 'added' && e && e.lat === 33.4511 && e.lng === -112.0783; }));
    await shot(w.page, 'yard-link-saved');
    await w.page.click('#place-line-back');
    await w.page.waitForTimeout(300);
    s = await w.state();
    check('back to my place: the saved zip is the centre again, the yard filter goes', !s.temp && !s.line && s.chip && s.center.lat === 33.4511 && s.yardFilter === '', JSON.stringify(s));
    check('#yard= with a saved zip: /geo is not asked', w.geoHits.length === 0);
    await w.ctx.close();
  }
  {
    const w = await open(browser, { geo: { ok: false }, hash: '#yard=' + encodeURIComponent('No Such Yard - Nowhere') });
    await w.page.waitForTimeout(800);
    const s = await w.state();
    check('#yard= for a yard we do not have: the zip card, nothing invented', s.banner && !s.temp && !s.center, JSON.stringify(s));
    await w.ctx.close();
  }

  /* ---------- #near= ---------- */
  {
    const w = await open(browser, { geo: SAC, hash: '#near=38.58,-121.49,' + encodeURIComponent('Sacramento, CA') + '&cars=Nissan|Xterra', scheme: 'dark' });
    await w.cars().catch(() => {});
    await w.page.waitForTimeout(500);
    const s = await w.state();
    check('#near=: "Showing yards near Sacramento, CA (from the page you came from)"', s.line && s.lineText === 'Showing yards near Sacramento, CA (from the page you came from).', s.lineText);
    check('#near=: never saved, a watch asks for the zip, no /geo', s.zip === null && s.coords === null && s.guess && w.geoHits.length === 0
      && await w.page.evaluate(() => addQuickWatch('Toyota', 'Camry', null, null, 'test')) === 'no-zip', JSON.stringify(s));
    check('#near=&cars=: the car filter applies around the link\'s place', s.make === 'Nissan' || /Nissan Xterra/.test(await w.page.evaluate(() => document.getElementById('car-search-input').value)), s.make);
    await w.ctx.close();
  }
  {
    const saved = { jh_gps: JSON.stringify({ lat: 33.45, lng: -112.07 }) };
    const w = await open(browser, { hash: '#near=38.58,-121.49,Sacramento', storage: saved });
    await w.cars();
    const s = await w.state();
    check('#near= with a saved GPS place: "Back to my location", GPS kept', s.back === 'Back to my location' && s.gps && !s.guess, JSON.stringify(s));
    await w.ctx.close();
  }
  {
    const w = await open(browser, { geo: { ok: false }, hash: '#near=51.5,-0.12,London' });
    await w.page.waitForTimeout(600);
    const s = await w.state();
    check('#near= abroad: ignored, the zip card', s.banner && !s.temp, JSON.stringify(s));
    await w.ctx.close();
  }
  // A link opened while the app is already open (hashchange).
  {
    const w = await open(browser, { geo: SAC });
    await w.cars();
    await w.page.evaluate((y) => { location.hash = 'yard=' + encodeURIComponent(y); }, YARD);
    await w.page.waitForFunction((y) => _tempPlace && _tempPlace.kind === 'link' && document.getElementById('live-filter-location').value === y, YARD, { timeout: 30000 }).catch(() => {});
    const s = await w.state();
    check('#yard= while open: the yard replaces the guess, labelled as a link', s.temp && s.temp.kind === 'link' && s.yardFilter === YARD && /from the page you came from/.test(s.lineText), JSON.stringify(s));
    await w.ctx.close();
  }

  /* ---------- the site Worker's own buttons, as it writes them, land right ---------- */
  {
    const { appHref, nearHash } = await import('../site-proxy/src/share.js');
    const cityUrl = new URL(appHref('city', 'ca-sacramento', nearHash({ lat: 38.5816, lng: -121.4944 }, 'Sacramento, CA')));
    const w = await open(browser, { geo: SAC, search: cityUrl.search, hash: cityUrl.hash });
    await w.cars();
    let s = await w.state();
    const a = await w.page.evaluate(() => JSON.parse(localStorage.getItem('ys_utm')));
    check('city page button (share.js appHref + nearHash): "Sacramento, CA (from the page you came from)", no /geo', s.lineText === 'Showing yards near Sacramento, CA (from the page you came from).' && w.geoHits.length === 0, s.lineText);
    check('city page button: remembered as source page, medium city, campaign ca-sacramento; address bar clean', a && a.src === 'page' && a.med === 'city' && a.cmp === 'ca-sacramento' && !/utm_|#/.test(s.url), JSON.stringify(a) + ' ' + s.url);
    await w.ctx.close();
    const yardUrl = new URL(appHref('yard', 'pick-n-pull-rancho-cordova', '#yard=' + encodeURIComponent(YARD)));
    const w2 = await open(browser, { geo: SAC, search: yardUrl.search, hash: yardUrl.hash });
    await w2.cars();
    s = await w2.state();
    check('yard page button (share.js): the app opens on that yard', s.yardFilter === YARD && s.temp && s.temp.kind === 'link' && w2.geoHits.length === 0, JSON.stringify(s));
    await w2.ctx.close();
  }

  /* ---------- ATTRIB: an internal page tag never replaces an outside source ---------- */
  {
    const reddit = JSON.stringify({ src: 'reddit', cmp: 'xterra', med: '', at: Date.now() });
    const w = await open(browser, { geo: { ok: false }, storage: { ys_utm: reddit }, search: '?utm_source=page&utm_medium=yard&utm_campaign=pick-n-pull-windsor' });
    const a = await w.page.evaluate(() => ({ stored: JSON.parse(localStorage.getItem('ys_utm')), attrib: ATTRIB, url: location.href }));
    check('ATTRIB: a Reddit visitor who taps a page button stays a Reddit visitor', a.stored.src === 'reddit' && a.attrib.src === 'reddit' && a.stored.cmp === 'xterra', JSON.stringify(a));
    check('ATTRIB: the tags are still stripped from the address bar', !/utm_/.test(a.url), a.url);
    await w.events();
    const fr = await w.page.evaluate(() => window.__beaconsFull.filter((x) => x.e === 'first-visit').map((x) => x.src));
    check('ATTRIB: that visit\'s events still carry reddit', fr.every((x) => x === 'reddit'), JSON.stringify(fr));
    await w.ctx.close();
    const w2 = await open(browser, { geo: { ok: false }, search: '?utm_source=page&utm_medium=yard&utm_campaign=pick-n-pull-windsor' });
    const b = await w2.page.evaluate(() => JSON.parse(localStorage.getItem('ys_utm')));
    await w2.events();
    const fv = await w2.page.evaluate(() => window.__beaconsFull.find((x) => x.e === 'first-visit') || null);
    check('ATTRIB: with no outside source, the page tag is remembered (source page, medium yard)', b && b.src === 'page' && b.med === 'yard' && b.cmp === 'pick-n-pull-windsor', JSON.stringify(b));
    check('ATTRIB: the first visit carries it', fv && fv.src === 'page' && fv.med === 'yard' && fv.cmp === 'pick-n-pull-windsor', JSON.stringify(fv));
    await w2.ctx.close();
    const w3 = await open(browser, { geo: { ok: false }, storage: { ys_utm: JSON.stringify({ src: 'page', cmp: 'x', med: 'yard', at: Date.now() }) }, search: '?utm_source=reddit&utm_campaign=4runner' });
    const c = await w3.page.evaluate(() => JSON.parse(localStorage.getItem('ys_utm')));
    check('ATTRIB: an outside source replaces a remembered page tag', c.src === 'reddit' && c.cmp === '4runner', JSON.stringify(c));
    await w3.ctx.close();
  }
} finally {
  await browser.close();
}
console.log(`\n${passes} passed, ${failures} failed`);
process.exit(failures ? 1 : 0);
