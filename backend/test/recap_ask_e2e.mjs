/* E2E: the free Monday email offer after a web watch (2026-11-12).
 *
 * The real docs/ bundle, answered from disk AS https://yardscout.io/ (and as
 * https://localhost/ for the app shells); the API's /v1/recap/* endpoints are
 * answered by this script, which records what the page sends. Nothing leaves
 * this machine. The automation flag is hidden so the funnel events can be
 * read from a sendBeacon recorder, as in funnel_events_e2e.mjs.
 *
 *   web    a watch (car screen bell) is saved first, then the toast offers
 *          the email: one line, one field, one button; "email asked" counted
 *   web    a bad address is answered in the toast; a good one posts a COPY
 *          of the criteria (rounded centre, no trim/drive, no addedAt) and
 *          the stored watches stay byte for byte; "email submitted" counted
 *   web    the x dismisses it for the rest of the visit
 *   web    the confirmation link's landing (#recap=confirmed&sub=) remembers
 *          the address; the next watch is one tap ("Add")
 *   web    the sender's daily cap: the reason is shown, the watch is kept
 *   web    Pro: no offer
 *   iOS / Android shells: no offer, no request
 *
 * Run: node backend/test/recap_ask_e2e.mjs   (SHOTS=<dir> for screenshots) */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const DOCS = path.join(ROOT, 'docs');
const SHOTS = process.env.SHOTS || '';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json' };
const UA_IOS = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';
const WL = 'yardscout_watchlist';
const SUB = Buffer.from('visitor@example.com').toString('base64url') + '.' + 'a'.repeat(64);

let failures = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + detail}`); if (!ok) failures++; };

const fileFor = (pathname) => {
  let p = decodeURIComponent(pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(DOCS, path.normalize(p));
  return f.startsWith(DOCS) && fs.existsSync(f) && !fs.statSync(f).isDirectory() ? f : null;
};

async function open(browser, { origin = 'https://yardscout.io', native = null, storage = null, api = {} } = {}) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, hasTouch: true, userAgent: UA_IOS, serviceWorkers: 'block' });
  const page = await ctx.newPage();
  const sent = [];
  const dialogs = [];
  page.on('dialog', async (d) => { dialogs.push(d.message()); await d.dismiss(); });
  await page.route('**/*', async (route) => {
    const req = route.request();
    const u = new URL(req.url());
    if (/api\.zippopotam\.us/.test(u.hostname)) {
      return route.fulfill({ json: { places: [{ latitude: '33.4511', longitude: '-112.0783' }] }, headers: { 'access-control-allow-origin': '*' } });
    }
    if (u.hostname === 'yardscout-api.yardscout.workers.dev' && u.pathname.startsWith('/v1/recap/')) {
      const cors = { 'access-control-allow-origin': '*', 'access-control-allow-headers': 'content-type', 'access-control-allow-methods': 'POST' };
      if (req.method() === 'OPTIONS') return route.fulfill({ status: 204, headers: cors });
      sent.push({ path: u.pathname, body: JSON.parse(req.postData() || '{}') });
      const [status, json] = api[u.pathname] || [200, { ok: true, state: u.pathname.endsWith('/add') ? 'added' : 'confirm-sent' }];
      return route.fulfill({ status, json, headers: cors });
    }
    if (u.pathname === '/api/ent/config') return route.fulfill({ json: { billing: true }, headers: { 'access-control-allow-origin': '*' } });
    if (u.hostname === 'yardscout.io' || u.origin === origin) {
      const f = fileFor(u.pathname);
      if (f) return route.fulfill({ path: f, contentType: TYPES[path.extname(f)] || 'application/octet-stream', headers: { 'access-control-allow-origin': '*' } });
      return route.fulfill({ status: 404, body: '' });
    }
    return route.abort();
  });
  await page.addInitScript(({ native, storage }) => {
    Object.defineProperty(Navigator.prototype, 'webdriver', { get: () => false, configurable: true });
    window.__beacons = [];
    navigator.sendBeacon = (url, blob) => { blob.text().then(t => window.__beacons.push(JSON.parse(t).e)); return true; };
    if (storage && !sessionStorage.getItem('__seeded')) { for (const [k, v] of Object.entries(storage)) localStorage.setItem(k, v); sessionStorage.setItem('__seeded', '1'); }
    document.addEventListener('DOMContentLoaded', () => {
      const st = document.createElement('style');
      st.textContent = '*,*::before,*::after{transition-duration:0s!important;animation-duration:0s!important}';
      document.head.appendChild(st);
    });
    if (native) {
      const L = () => ({ remove() {} });
      window.Capacitor = { isNativePlatform: () => true, getPlatform: () => native, Plugins: {
        Purchases: { isEntitled: async () => ({ entitled: false }), getProduct: async () => ({ available: false }), purchase: async () => ({ cancelled: true }), restore: async () => ({ entitled: false }) },
        PushNotifications: { addListener: L, checkPermissions: async () => ({ receive: 'prompt' }), requestPermissions: async () => ({ receive: 'denied' }), register: async () => {} },
        App: { addListener: L, getInfo: async () => ({ version: '1.12.15', build: '37' }), getLaunchUrl: async () => null },
        Geolocation: { getCurrentPosition: async () => { throw new Error('x'); }, checkPermissions: async () => ({ location: 'prompt' }) },
        StatusBar: { setStyle: async () => {}, setBackgroundColor: async () => {} },
      } };
    }
  }, { native, storage });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e.message).slice(0, 160)));
  await page.goto(origin + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => typeof liveLoaded !== 'undefined' && liveLoaded, null, { timeout: 120000 });
  const events = async () => { await page.waitForTimeout(250); return page.evaluate(() => window.__beacons.slice()); };
  const watches = () => page.evaluate((k) => localStorage.getItem(k) || '[]', WL);
  const toast = () => page.evaluate(() => { const t = document.getElementById('watch-toast'); return t && t.classList.contains('show') ? t.innerText.replace(/\s+/g, ' ').trim() : ''; });
  const shot = async (name) => { if (SHOTS) { fs.mkdirSync(SHOTS, { recursive: true }); await page.screenshot({ path: path.join(SHOTS, name + '.png') }); } };
  return { ctx, page, sent, dialogs, errors, events, watches, toast, shot };
}
const enterZip = async (page) => {
  if (await page.isVisible('#zip-banner-input')) {
    await page.fill('#zip-banner-input', '85003');
    await page.click('#zip-banner-go');
  }
  await page.waitForSelector('#live-grid .car-card .car-open', { timeout: 120000 });
};
// The bell on the n-th car's screen: the quick-watch path every share link uses.
async function bell(page, n = 0) {
  await page.evaluate(() => { try { hideCarDetail(); } catch (e) { /* closed */ } });
  await page.waitForTimeout(400);   // let the grid settle after the zip
  await page.locator('#live-grid .car-card .car-open').nth(n).click();
  await page.waitForSelector('#car-detail.open .watch-btn', { timeout: 15000 });
  const label = await page.evaluate(() => { const b = document.querySelector('#car-detail.open .watch-btn'); return `${b.dataset.make} ${b.dataset.model}`.trim(); });
  await page.click('#car-detail.open .watch-btn');
  await page.waitForSelector('#watch-toast.show', { timeout: 5000 });
  return label;
}
const count = (list, e) => list.filter(x => x === e).length;

const browser = await chromium.launch();
try {
  /* ---- 1. web: offered after the watch is saved; bad then good address ---- */
  {
    // A watch saved earlier in the shape the app writes, to prove it is untouched.
    const OLD = JSON.stringify([{ make: 'Honda', model: 'Civic', yrMin: null, yrMax: null, matchOnly: true, radiusMi: 100, lat: 33.45, lng: -112.07, driveFilter: '', trimFilter: 'Si', addedAt: '2026-10-02T10:00:00.000Z~abc123' }]);
    const v = await open(browser, { storage: { [WL]: OLD, ys_seen: '1', ys_app_promo: '1' } });
    await enterZip(v.page);
    const label = await bell(v.page);
    const after = JSON.parse(await v.watches());
    check('the watch is saved before any email is asked for', after.length === 2 && `${after[1].make} ${after[1].model}` === label && v.sent.length === 0, JSON.stringify(after[1]));
    const t = await v.toast();
    check('the toast offers the Monday email in one line', t.includes(`Watching ${label}`) && t.includes(`Get a free Monday email listing every ${label} set out within`), t);
    check('...with one email field and one button, in view', await v.page.evaluate(() => {
      const ask = document.querySelector('#watch-toast .mail-ask');
      if (!ask) return false;
      const i = ask.querySelectorAll('input'), b = ask.querySelectorAll('button');
      const r = ask.getBoundingClientRect();
      return i.length === 1 && i[0].type === 'email' && b.length === 1 && b[0].textContent.trim() === 'Email me' && r.top >= 0 && r.bottom <= innerHeight;
    }));
    check('no store link and no Pro box squeezed in beside it', await v.page.evaluate(() => !document.querySelector('#watch-toast [data-act="app"], #watch-toast .pro-box')));
    let ev = await v.events();
    check('"email asked" counted once', count(ev, 'email-asked') === 1, JSON.stringify(ev));
    await v.shot('recap_1_ask');
    await v.page.waitForTimeout(13000);   // ordinary toasts leave after 12 s
    check('the offer does not vanish after 12 s', (await v.toast()).includes('Monday email'));
    await v.page.fill('#watch-toast .mail-email', 'not-an-address');
    await v.page.click('#watch-toast .mail-form .btn');
    check('a bad address is answered in the toast, nothing sent', /Enter your email address/.test(await v.toast()) && v.sent.length === 0 && v.dialogs.length === 0);
    await v.page.fill('#watch-toast .mail-email', ' Visitor@Example.com ');
    await v.page.click('#watch-toast .mail-form .btn');
    await v.page.waitForFunction(() => /Check your inbox/.test(document.getElementById('watch-toast').innerText), null, { timeout: 5000 }).catch(() => {});
    const req = v.sent[0] || { body: {} };
    check('one sign-up request: the address and a COPY of the criteria', v.sent.length === 1 && req.path === '/v1/recap/signup' && req.body.email === 'visitor@example.com'
      && `${req.body.watch.make} ${req.body.watch.model}` === label && req.body.watch.radiusMi === after[1].radiusMi
      && req.body.watch.lat === Math.round(after[1].lat * 100) / 100, JSON.stringify(req.body));
    check('the copy carries no browser ids, trim or drivetrain', !/addedAt|matchOnly|trimFilter|driveFilter/.test(JSON.stringify(req.body)));
    const t2 = await v.toast();
    check('"check your inbox", masked address, nothing sent until confirmed', /Check your inbox\. Tap the link we sent to v•••@example\.com/.test(t2) && /Nothing is sent until you do/.test(t2), t2);
    check('stored watches are byte for byte what they were (rule 6)', (await v.watches()).startsWith(OLD.slice(0, -1) + ',')
      && JSON.stringify(JSON.parse(await v.watches())[1]) === JSON.stringify(after[1]));
    check('the address is remembered as pending', await v.page.evaluate(() => JSON.parse(localStorage.getItem('ys_recap')).state === 'pending'));
    ev = await v.events();
    check('"email submitted" counted once; "email confirmed" is never sent by the page', count(ev, 'email-submitted') === 1 && count(ev, 'email-confirmed') === 0, JSON.stringify(ev));
    await v.shot('recap_2_sent');
    check('no dialog, no page error', v.dialogs.length === 0 && v.errors.length === 0, JSON.stringify([v.dialogs, v.errors]));
    await v.ctx.close();
  }

  /* ---- 2. web: x = not asked again during this visit ---- */
  {
    const v = await open(browser, { storage: { ys_seen: '1', ys_app_promo: '1' } });
    await enterZip(v.page);
    await bell(v.page, 0);
    check('offered on the first watch', (await v.toast()).includes('Monday email'));
    await v.page.click('#watch-toast .watch-toast-x');
    await bell(v.page, 3);
    const t = await v.toast();
    check('after a dismissal the next watch toast does not ask again', t.includes('Watching') && !t.includes('Monday email'), t);
    await v.page.reload({ waitUntil: 'domcontentloaded' });
    await v.page.waitForSelector('#live-grid .car-card .car-open', { timeout: 120000 });
    await bell(v.page, 5);
    check('...nor after a reload in the same visit', !(await v.toast()).includes('Monday email'));
    check('only one "email asked"', count(await v.events(), 'email-asked') === 0);   // the recorder restarts on reload
    check('no request was ever sent', v.sent.length === 0);
    await v.ctx.close();
  }

  /* ---- 3. web: the confirmation link lands; later watches are one tap ---- */
  {
    const v = await open(browser, { storage: { ys_seen: '1', ys_app_promo: '1' } });
    await v.page.goto('https://yardscout.io/#recap=confirmed&sub=' + encodeURIComponent(SUB), { waitUntil: 'domcontentloaded' });
    await v.page.waitForFunction(() => typeof liveLoaded !== 'undefined', null, { timeout: 60000 });
    await v.page.waitForSelector('#watch-toast.show', { timeout: 10000 }).catch(() => {});
    check('landing says the Monday email is confirmed', /You’re in\. Your free Monday email to v•••@example\.com is confirmed\./.test(await v.toast()), await v.toast());
    check('the token is stored and the fragment is gone', await v.page.evaluate((s) => location.hash === '' && JSON.parse(localStorage.getItem('ys_recap')).sub === s
      && JSON.parse(localStorage.getItem('ys_recap')).state === 'confirmed', SUB));
    await v.shot('recap_3_confirmed');
    await enterZip(v.page);
    const label = await bell(v.page, 1);
    const t = await v.toast();
    check('the next watch offers one tap, no field', t.includes(`Add ${label} to your free Monday email?`) && await v.page.evaluate(() => !document.querySelector('#watch-toast input')), t);
    await v.shot('recap_4_add');
    await v.page.click('#watch-toast [data-act="recap-add"]');
    await v.page.waitForFunction(() => /Added\./.test(document.getElementById('watch-toast').innerText), null, { timeout: 5000 }).catch(() => {});
    const req = v.sent[0] || { body: {} };
    check('one tap posts the copy with the token', v.sent.length === 1 && req.path === '/v1/recap/add' && req.body.sub === SUB && `${req.body.watch.make} ${req.body.watch.model}` === label, JSON.stringify(req));
    check('"Added" with the masked address', /Added\. It will be in your next Monday email to v•••@example\.com\./.test(await v.toast()), await v.toast());
    await v.ctx.close();
  }

  /* ---- 4. web: the API refuses (daily cap): the reason is shown, the watch stays ---- */
  {
    const v = await open(browser, { storage: { ys_seen: '1', ys_app_promo: '1' },
      api: { '/v1/recap/signup': [503, { error: 'daily_cap', message: "Our email sender has reached today's limit. Your watch is saved here; try the email again tomorrow." }] } });
    await enterZip(v.page);
    await bell(v.page, 2);
    await v.page.fill('#watch-toast .mail-email', 'visitor@example.com');
    await v.page.click('#watch-toast .mail-form .btn');
    await v.page.waitForFunction(() => /today's limit/.test(document.getElementById('watch-toast').innerText), null, { timeout: 5000 }).catch(() => {});
    check('the cap message is shown in the toast', /reached today's limit\. Your watch is saved here/.test(await v.toast()), await v.toast());
    check('the watch is kept; nothing remembered as pending; no "submitted"', JSON.parse(await v.watches()).length === 1
      && await v.page.evaluate(() => !localStorage.getItem('ys_recap')) && count(await v.events(), 'email-submitted') === 0);
    await v.shot('recap_5_cap');
    await v.ctx.close();
  }

  /* ---- 5. web Pro: no offer ---- */
  {
    const v = await open(browser, { storage: { ys_seen: '1', ys_app_promo: '1' } });
    await enterZip(v.page);
    // The web re-checks a stored Pro flag against its entitlement at boot, so
    // set it the way the other UI tests do, after load.
    await v.page.evaluate(() => { localStorage.setItem('jh_pro', '1'); applyProGates(); });
    check('Pro is on for this visitor', await v.page.evaluate(() => isPro()));
    await bell(v.page, 0);
    const t = await v.toast();
    check('Pro on the web: no Monday email offer', !t.includes('Monday email') && v.sent.length === 0, JSON.stringify([t, v.sent]));
    await v.ctx.close();
  }

  /* ---- 6. the app shells: never offered ---- */
  for (const native of ['ios', 'android']) {
    const v = await open(browser, { origin: 'https://localhost', native, storage: { ys_seen: '1' } });
    await enterZip(v.page);
    await bell(v.page, 0);
    const t = await v.toast();
    check(`${native} shell: the watch toast has no email field`, t.includes('Watching') && !t.includes('Monday email') && await v.page.evaluate(() => !document.querySelector('#watch-toast input[type="email"]')), t);
    check(`${native} shell: nothing sent to /v1/recap and no "email asked"`, v.sent.length === 0 && count(await v.events(), 'email-asked') === 0);
    check(`${native} shell: a #recap= link does nothing`, await v.page.evaluate(() => handleRecapHash() === false));
    await v.ctx.close();
  }

  /* ---- 7. the eligibility rule itself ---- */
  {
    const v = await open(browser, { storage: { ys_seen: '1' } });
    const r = await v.page.evaluate(() => {
      const e = { make: 'Ford', model: 'Ranger', lat: 33.4, lng: -112, radiusMi: 100 };
      return [recapEligible(e, false, false, false), recapEligible(e, true, false, false), recapEligible(e, false, true, false),
        recapEligible(e, false, false, true), recapEligible({ make: 'Ford', model: 'Ranger', radiusMi: null }, false, false, false)];
    });
    check('eligible: web, free, not dismissed, with a zip centre — and only then', JSON.stringify(r) === '[true,false,false,false,false]', JSON.stringify(r));
    await v.ctx.close();
  }
} finally {
  await browser.close();
}
console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
