/* E2E: the free emailed alert in the Alerts tab (2026-11-17).
 *
 * The real docs/ bundle, answered from disk AS https://yardscout.io/ (and as
 * https://localhost/ for the app shells), as recap_ask_e2e.mjs does. The
 * API's /v1/free-alert/* endpoints are answered by this script, which records
 * what the page sends. Nothing leaves this machine; no port is opened. The
 * automation flag is hidden so the funnel events can be read from a
 * sendBeacon recorder.
 *
 *   web free   the card under the watchlist: pick ONE watch (rows), one email field,
 *              one button; "shown" counted once; a bad address is answered in
 *              the card; a good one posts a COPY of the criteria (rounded
 *              centre, at most 50 mi, no trim / drive / addedAt); the stored
 *              watches stay byte for byte; "asked" counted; "check your inbox"
 *   web free   the confirmation link's landing (#falert=confirmed&sub=): the
 *              card says it is on, the watch wears the mark, the server is
 *              asked what it holds; change car (token, no new email); turn off
 *   web free   unsubscribed from an email: the card goes back to the ask
 *   web free   the sender's daily cap: the reason is shown, nothing remembered
 *   web free   an address already confirmed for the Monday email here: on at
 *              once (the token rides along)
 *   web free   only the first 5 watches can carry it; no watch, no card
 *   web Pro    no card, no sentence; the Pro email panel is as it was
 *   web free   the watch toast's one offer is the alert (case 10); dismissed,
 *              or once asked for, the Monday email is offered instead
 *   web free   the near-miss line ("Would have sent a push within hours")
 *              leaves out the cars the alert that is on covers
 *   web free   the Cars watch strip, one model (case 11, 2026-11-18): asks for
 *              the alert in the Monday email's place; "shown" sent once, in
 *              view; one new watch, a copy of it sent; pending; rule 6
 *   iOS / Android shells: no card, no sentence, no request
 *
 * Run: node backend/test/free_email_alert_ui_e2e.mjs   (SHOTS=<dir> for screenshots;
 * YS_DOCS=<another docs/ folder> runs it against other sources) */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const DOCS = path.resolve(process.env.YS_DOCS || path.join(ROOT, 'docs'));   // YS_DOCS: another docs/ folder (e.g. before a fix)
const SHOTS = process.env.SHOTS || '';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json' };
const UA_IOS = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';
const WL = 'yardscout_watchlist';
const EMAIL = 'visitor@example.com';
const SUB = Buffer.from(EMAIL).toString('base64url') + '.' + 'a'.repeat(64);
const PHX = { lat: 33.4484, lng: -112.0741 };
const W = (make, model, i, extra = {}) => ({ make, model, yrMin: null, yrMax: null, matchOnly: false, radiusMi: 100, ...PHX,
  driveFilter: '', trimFilter: '', addedAt: `2026-11-0${i}T10:00:00.000Z~w${i}xyz`, ...extra });
// As the app writes them: a Pro-era trim filter and "parts only" on the first, a narrow radius on the second.
const TWO = JSON.stringify([W('Toyota', '4Runner', 1, { yrMin: 2003, yrMax: 2009, radiusMi: 250, matchOnly: true, trimFilter: 'SR5' }), W('Honda', 'Civic', 2, { radiusMi: 25 })]);
const ONE = JSON.stringify([W('Toyota', '4Runner', 1)]);
const SIX = JSON.stringify(['Camry', 'Corolla', 'Tacoma', 'Tundra', 'Sienna', 'Prius'].map((m, i) => W('Toyota', m, i + 1)));
const BASE_STORE = { jh_honesty_ack: '1', ys_seen: '1', ys_app_promo: '1', jh_zip: '85003', jh_zip_coords: JSON.stringify({ 85003: PHX }), jh_radius: '100' };

let failures = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + String(detail).slice(0, 500)}`); if (!ok) failures++; };

const fileFor = (pathname) => {
  let p = decodeURIComponent(pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(DOCS, path.normalize(p));
  return f.startsWith(DOCS) && fs.existsSync(f) && !fs.statSync(f).isDirectory() ? f : null;
};

/* api: { '/v1/free-alert/signup': [status, json] | (body) => [status, json] } */
async function open(browser, { origin = 'https://yardscout.io', native = null, storage = {}, api = {}, hash = '', width = 390 } = {}) {
  const ctx = await browser.newContext({ viewport: { width, height: 844 }, deviceScaleFactor: 1, hasTouch: true, userAgent: UA_IOS, serviceWorkers: 'block' });
  const page = await ctx.newPage();
  const sent = [];
  const dialogs = [];
  page.on('dialog', async (d) => { dialogs.push(d.message()); await d.dismiss(); });
  await page.route('**/*', async (route) => {
    const req = route.request();
    const u = new URL(req.url());
    if (/api\.zippopotam\.us/.test(u.hostname)) {
      return route.fulfill({ json: { places: [{ latitude: String(PHX.lat), longitude: String(PHX.lng) }] }, headers: { 'access-control-allow-origin': '*' } });
    }
    if (u.hostname === 'yardscout-api.yardscout.workers.dev' && (u.pathname.startsWith('/v1/free-alert/') || u.pathname.startsWith('/v1/recap/'))) {
      const cors = { 'access-control-allow-origin': '*', 'access-control-allow-headers': 'content-type', 'access-control-allow-methods': 'POST' };
      if (req.method() === 'OPTIONS') return route.fulfill({ status: 204, headers: cors });
      const body = JSON.parse(req.postData() || '{}');
      sent.push({ path: u.pathname, body });
      let ans = api[u.pathname];
      if (typeof ans === 'function') ans = ans(body);
      const [status, json] = ans || [200, u.pathname.endsWith('/status') ? { ok: true, state: 'off' } : { ok: true, state: 'confirm-sent' }];
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
        App: { addListener: L, getInfo: async () => ({ version: '1.13.0', build: '40' }), getLaunchUrl: async () => null },
        Geolocation: { getCurrentPosition: async () => { throw new Error('x'); }, checkPermissions: async () => ({ location: 'prompt' }) },
        StatusBar: { setStyle: async () => {}, setBackgroundColor: async () => {} },
      } };
    }
  }, { native, storage });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e.message).slice(0, 160)));
  await page.goto(origin + '/' + hash, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => typeof liveLoaded !== 'undefined' && liveLoaded, null, { timeout: 180000 });
  const events = async () => { await page.waitForTimeout(250); return page.evaluate(() => window.__beacons.slice()); };
  const watches = () => page.evaluate((k) => localStorage.getItem(k), WL);
  const alerts = async () => { await page.click('.tab[data-tab="alerts"]'); await page.waitForTimeout(300); };
  /* What the card shows, as a person would read it. */
  const card = () => page.evaluate(() => {
    const el = document.getElementById('free-alert');
    const shown = !!el && getComputedStyle(el).display !== 'none' && el.getClientRects().length > 0;
    return {
      shown, text: shown ? el.innerText.replace(/\s+/g, ' ').trim() : '',
      inputs: shown ? [...el.querySelectorAll('input')].map(i => i.type) : [],
      options: shown ? [...el.querySelectorAll('.fa-opt')].map(o => o.innerText.replace(/\s+/g, ' ').trim()) : [],
      buttons: shown ? [...el.querySelectorAll('button')].map(b => b.textContent.trim()) : [],
      pro: shown ? !!el.querySelector('.pro-box, .pro-badge, .pro-tag, [onclick*="openUpgradeSheet"]') : false,
      msg: shown && el.querySelector('.fa-msg') ? el.querySelector('.fa-msg').textContent : '',
    };
  });
  const note = () => page.evaluate(() => {
    const n = document.getElementById('alerts-free-email-copy');
    return n && getComputedStyle(n).display !== 'none' && n.getClientRects().length ? n.innerText.replace(/\s+/g, ' ').trim() : '';
  });
  const marks = () => page.evaluate(() => [...document.querySelectorAll('#alert-watchlist .watchlist-item')].map(el => (el.querySelector('.wl-falert') ? el.querySelector('.wl-falert').textContent : null)));
  const state = () => page.evaluate(() => JSON.parse(localStorage.getItem('ys_falert') || 'null'));
  const shot = async (name) => {
    if (!SHOTS) return;
    fs.mkdirSync(SHOTS, { recursive: true });
    // The card in the middle of the screen, with no toast over it.
    await page.evaluate(() => {
      const t = document.getElementById('watch-toast'); if (t) t.classList.remove('show');
      const el = document.getElementById('free-alert'); (el && el.getClientRects().length ? el : document.getElementById('alert-watchlist')).scrollIntoView({ block: 'center' });
    });
    await page.waitForTimeout(200);
    await page.screenshot({ path: path.join(SHOTS, name + '.png') });
  };
  return { ctx, page, sent, dialogs, errors, events, watches, alerts, card, note, marks, state, shot };
}
const count = (list, e) => list.filter(x => x === e).length;
const until = (page, re) => page.waitForFunction((src) => new RegExp(src).test(document.getElementById('free-alert').innerText), re.source, { timeout: 6000 }).catch(() => {});

const browser = await chromium.launch();
try {
  /* ---- 1. web, free: ask → bad address → good address → check your inbox ---- */
  {
    const v = await open(browser, { storage: { ...BASE_STORE, [WL]: TWO } });
    check('one distance on both features (the free instant push\'s 50 mi)', await v.page.evaluate(() => FREE_EMAIL_ALERT_RADIUS_MI === FREE_INSTANT_RADIUS_MI && FREE_EMAIL_ALERT_RADIUS_MI === 50));
    await v.alerts();
    const n = await v.note();
    check('the intro has its own sentence about the website\'s free emailed alert', /^On this website, free gets one watch emailed: pick it under your watchlist and we email you when one is set out within 50\smi\.$/.test(n), n);
    check('...placed right after the paragraph about the apps, whose own text it leaves alone', await v.page.evaluate(() => {
      const intro = document.getElementById('alerts-intro-copy');
      return !!intro && intro.nextElementSibling && intro.nextElementSibling.id === 'alerts-free-email-copy' && !intro.querySelector('#alerts-free-email-copy') && !/emailed/.test(intro.innerText);
    }));
    let c = await v.card();
    check('the card is under the watchlist, before the matches', c.shown && await v.page.evaluate(() => {
      const el = document.getElementById('free-alert');
      return el.previousElementSibling.id === 'alert-watchlist' && !!(el.compareDocumentPosition(document.getElementById('alert-matches-grid')) & Node.DOCUMENT_POSITION_FOLLOWING);
    }));
    check('it says what it is: one car, one address, no account, usually the same day', /Free email alert/.test(c.text)
      && /Pick one car and we email you when one is set out within 50\smi, usually the same day\. One car, one address, no account\./.test(c.text), c.text);
    check('it is honest about the sending limit, and never says instant or every', /can arrive late or be skipped/.test(c.text) && !/instant|every time|always/i.test(c.text), c.text);
    check('the two watches to pick from (years shown, the first one picked), one email field, one button', JSON.stringify(c.options) === JSON.stringify(['2003–2009 Toyota 4Runner', 'Honda Civic'])
      && JSON.stringify(c.inputs) === '["radio","radio","email"]' && JSON.stringify(c.buttons) === '["Email me"]'
      && await v.page.evaluate(() => document.querySelector('#free-alert input[name="fa-watch"]:checked').value === '0'), JSON.stringify(c));
    check('no Pro prompt inside the card', !c.pro && !/\bPro\b/.test(c.text));
    await v.page.evaluate(() => document.getElementById('free-alert').scrollIntoView({ block: 'center' }));
    let ev = await v.events();
    check('"free alert shown" counted once it is on screen', count(ev, 'free-alert-shown') === 1, JSON.stringify(ev));
    await v.page.evaluate(() => { renderAlerts(); renderAlerts(); });
    check('...and not again on a re-render', count(await v.events(), 'free-alert-shown') === 1);
    await v.shot('falert_1_ask');

    // The sentence names the distance of the car that is picked.
    await v.page.click('#free-alert .fa-opt:has-text("Honda Civic")');
    check('picking the 25 mi watch: the sentence says 25 mi', /set out within 25\smi/.test((await v.card()).text));
    await v.page.fill('#fa-email', 'half-typed@');
    await v.page.evaluate(() => renderAlerts());   // a scan arriving re-renders the tab
    check('a re-render keeps what was typed and picked', await v.page.evaluate(() => document.getElementById('fa-email').value === 'half-typed@'
      && document.querySelector('#free-alert input[name="fa-watch"]:checked').closest('label').innerText.trim() === 'Honda Civic'));
    await v.page.click('#free-alert .fa-form .btn-primary');
    c = await v.card();
    check('a bad address is answered in the card, nothing sent', /Enter your email address/.test(c.msg) && v.sent.length === 0 && v.dialogs.length === 0, c.msg);

    const before = await v.watches();
    await v.page.click('#free-alert .fa-opt:has-text("Toyota 4Runner")');
    await v.page.fill('#fa-email', ' Visitor@Example.com ');
    await v.page.click('#free-alert .fa-form .btn-primary');
    await until(v.page, /Check your inbox/);
    const req = v.sent[0] || { body: { watch: {} } };
    check('one sign-up request: the address and a COPY of the one watch', v.sent.length === 1 && req.path === '/v1/free-alert/signup' && req.body.email === EMAIL
      && JSON.stringify(req.body.watch) === JSON.stringify({ make: 'Toyota', model: '4Runner', yearMin: 2003, yearMax: 2009, lat: 33.45, lng: -112.07, radiusMi: 50 }), JSON.stringify(req.body));
    check('the 250 mi watch is sent as 50 mi; no trim, "parts only", addedAt or token in the request',
      req.body.watch.radiusMi === 50 && !/SR5|matchOnly|addedAt|w1xyz|trimFilter|driveFilter/.test(JSON.stringify(req.body)) && !('sub' in req.body));
    c = await v.card();
    check('"check your inbox", masked address, the car, nothing sent until confirmed',
      /Check your inbox\. Tap the link we sent to v•••@example\.com to turn on your email alert for 2003–2009 Toyota 4Runner\. Nothing is sent until you do\./.test(c.text), c.text);
    check('no field left, one way back', c.inputs.length === 0 && JSON.stringify(c.buttons) === '["Use a different address or car"]', JSON.stringify(c));
    check('stored watches are byte for byte what they were (rule 6)', (await v.watches()) === before && before === TWO);
    let st = await v.state();
    check('this browser remembers it as pending, in its own key', st && st.state === 'pending' && st.email === EMAIL && st.key === '2026-11-01T10:00:00.000Z~w1xyz' && !st.sub, JSON.stringify(st));
    check('no watch wears the mark before the click', (await v.marks()).every(m => m === null));
    ev = await v.events();
    check('"free alert asked" counted once; the page never sends "confirmed" or "first email"', count(ev, 'free-alert-asked') === 1
      && count(ev, 'free-alert-confirmed') === 0 && count(ev, 'free-alert-first-email') === 0, JSON.stringify(ev));
    await v.shot('falert_2_pending');

    await v.page.reload({ waitUntil: 'domcontentloaded' });
    await v.page.waitForFunction(() => typeof liveLoaded !== 'undefined' && liveLoaded, null, { timeout: 180000 });
    await v.alerts();
    check('pending survives a reload', /Check your inbox/.test((await v.card()).text));
    await v.page.click('#free-alert [data-act="fa-restart"]');
    c = await v.card();
    check('"Use a different address or car" brings the ask back', c.inputs.includes('email') && (await v.state()) === null);
    check('no dialog, no page error', v.dialogs.length === 0 && v.errors.length === 0, JSON.stringify([v.dialogs, v.errors]));
    await v.ctx.close();
  }

  /* ---- 2. the confirmation link lands: on, marked, change car, turn off ---- */
  {
    const pending = JSON.stringify({ email: EMAIL, key: '2026-11-01T10:00:00.000Z~w1xyz', label: '2003–2009 Toyota 4Runner', r: 50, state: 'pending', at: Date.now() });
    const serverWatch = { make: 'Toyota', model: '4Runner', yearMin: 2003, yearMax: 2009, radiusMi: 50 };
    let held = serverWatch;
    const v = await open(browser, { storage: { ...BASE_STORE, [WL]: TWO, ys_falert: pending }, hash: '#falert=confirmed&sub=' + encodeURIComponent(SUB),
      api: {
        '/v1/free-alert/status': () => [200, held ? { ok: true, state: 'on', watch: held } : { ok: true, state: 'off' }],
        '/v1/free-alert/signup': (b) => { held = { make: b.watch.make, model: b.watch.model, yearMin: b.watch.yearMin, yearMax: b.watch.yearMax, radiusMi: b.watch.radiusMi }; return [200, { ok: true, state: 'on', sub: SUB, watch: held }]; },
        '/v1/free-alert/off': () => { held = null; return [200, { ok: true, state: 'off' }]; },
      } });
    await v.page.waitForSelector('#watch-toast.show', { timeout: 10000 }).catch(() => {});
    const toast = await v.page.evaluate(() => document.getElementById('watch-toast').innerText.replace(/\s+/g, ' ').trim());
    check('landing says the free email alert is on (masked address)', /Your free email alert is on\. We’ll email v•••@example\.com when one is set out near you\./.test(toast), toast);
    check('the Alerts tab is open and the fragment is gone', await v.page.evaluate(() => document.getElementById('tab-alerts').classList.contains('active') && location.hash === ''));
    let st = await v.state();
    check('the token is stored; the car that was asked for here is kept', st && st.state === 'on' && st.sub === SUB && st.label === '2003–2009 Toyota 4Runner' && st.key === '2026-11-01T10:00:00.000Z~w1xyz', JSON.stringify(st));
    await v.page.waitForTimeout(500);
    check('the server is asked what it holds, with the token', v.sent.some(s => s.path === '/v1/free-alert/status' && s.body.sub === SUB), JSON.stringify(v.sent));
    let c = await v.card();
    check('the card says it is on: car, distance, masked address, one email per scan', /Free email alert is on/.test(c.text)
      && /2003–2009 Toyota 4Runner, within 50\smi, to v•••@example\.com\. At most one email per scan, usually the same day a car is listed\./.test(c.text), c.text);
    check('...with the limit said plainly, two buttons, no field, no Pro prompt', /can arrive late or be skipped/.test(c.text)
      && JSON.stringify(c.buttons) === '["Change car","Turn off"]' && c.inputs.length === 0 && !c.pro && !/\bPro\b/.test(c.text), JSON.stringify(c));
    // The page opened straight into Alerts: the list fills in once the scan
    // for the saved zip is in (as on any #tab=alerts arrival).
    await v.page.waitForSelector('#alert-watchlist .watchlist-item', { timeout: 120000 }).catch(() => {});
    check('the watch it stands for wears the mark, the other does not', JSON.stringify(await v.marks()) === JSON.stringify(['Email alert, within 50 mi', null]), JSON.stringify(await v.marks()));
    check('"shown" is not counted for someone who already has it', count(await v.events(), 'free-alert-shown') === 0);
    await v.shot('falert_3_on');

    const before = await v.watches();
    await v.page.click('#free-alert [data-act="fa-change"]');
    c = await v.card();
    check('Change car: the other watch to pick, Save / Cancel', JSON.stringify(c.options) === '["Honda Civic"]' && JSON.stringify(c.buttons) === '["Save","Cancel"]', JSON.stringify(c));
    await v.shot('falert_4_change');
    await v.page.click('#free-alert [data-act="fa-cancel"]');
    check('Cancel closes it, nothing sent', JSON.stringify((await v.card()).buttons) === '["Change car","Turn off"]' && !v.sent.some(s => s.path === '/v1/free-alert/signup'));
    await v.page.click('#free-alert [data-act="fa-change"]');
    await v.page.click('#free-alert .fa-change .btn-primary');
    await until(v.page, /Honda Civic, within 25/);
    const ch = v.sent.find(s => s.path === '/v1/free-alert/signup') || { body: { watch: {} } };
    check('the change is one request with the token (no new confirmation email) and the 25 mi copy', ch.body.sub === SUB && ch.body.email === EMAIL
      && JSON.stringify(ch.body.watch) === JSON.stringify({ make: 'Honda', model: 'Civic', yearMin: null, yearMax: null, lat: 33.45, lng: -112.07, radiusMi: 25 }), JSON.stringify(ch.body));
    c = await v.card();
    check('the card now names the Civic within 25 mi', /Honda Civic, within 25\smi, to v•••@example\.com/.test(c.text) && !/4Runner/.test(c.text), c.text);
    check('the mark moved to the Civic', JSON.stringify(await v.marks()) === JSON.stringify([null, 'Email alert, within 25 mi']));
    check('a change is not counted as a new ask', count(await v.events(), 'free-alert-asked') === 0);
    check('stored watches unchanged byte for byte (rule 6): not edited, not reordered', (await v.watches()) === before && before === TWO);

    // The watch is removed here: the server's copy runs on, and the card says so.
    await v.page.evaluate(() => removeWatchItem(1));
    c = await v.card();
    check('the picked watch removed from the list: the card says the alert keeps running', /This car is no longer in your list here; the email alert keeps running until you change it or turn it off\./.test(c.text), c.text);
    check('...and removing it sent nothing to the alert API', !v.sent.some(s => s.path === '/v1/free-alert/off'));

    await v.page.click('#free-alert [data-act="fa-off"]');
    await until(v.page, /Email alert off/);
    check('Turn off: one request with the token', v.sent.filter(s => s.path === '/v1/free-alert/off').length === 1 && v.sent.find(s => s.path === '/v1/free-alert/off').body.sub === SUB);
    c = await v.card();
    check('the card says it is off and what was deleted, and offers the ask again', /Email alert off\. We deleted your address and the watch copied for it\./.test(c.msg)
      && c.inputs.includes('email') && (await v.state()) === null, JSON.stringify(c));
    check('no watch wears the mark', (await v.marks()).every(m => m === null));
    check('no dialog, no page error', v.dialogs.length === 0 && v.errors.length === 0, JSON.stringify([v.dialogs, v.errors]));
    await v.shot('falert_5_off');
    await v.ctx.close();
  }

  /* ---- 3. unsubscribed from an email's link: the card finds out ---- */
  {
    const on = JSON.stringify({ email: EMAIL, key: '2026-11-01T10:00:00.000Z~w1xyz', label: '2003–2009 Toyota 4Runner', r: 50, state: 'on', sub: SUB });
    const v = await open(browser, { storage: { ...BASE_STORE, [WL]: TWO, ys_falert: on }, api: { '/v1/free-alert/status': [200, { ok: true, state: 'off' }] } });
    await v.alerts();
    await until(v.page, /unsubscribed/);
    const c = await v.card();
    check('the server says off: the card says so and shows the ask again', /Your email alert is off: that address was unsubscribed\. You can ask for it again here\./.test(c.msg)
      && c.inputs.includes('email') && (await v.state()) === null && (await v.marks()).every(m => m === null), JSON.stringify(c));
    await v.ctx.close();
  }
  {
    // Changed from another browser: the card shows what the server holds.
    const on = JSON.stringify({ email: EMAIL, key: '2026-11-01T10:00:00.000Z~w1xyz', label: '2003–2009 Toyota 4Runner', r: 50, state: 'on', sub: SUB });
    const v = await open(browser, { storage: { ...BASE_STORE, [WL]: TWO, ys_falert: on },
      api: { '/v1/free-alert/status': [200, { ok: true, state: 'on', watch: { make: 'Honda', model: 'Civic', yearMin: null, yearMax: null, radiusMi: 25 } }] } });
    await v.alerts();
    await until(v.page, /Honda Civic, within 25/);
    check('changed elsewhere: the card and the mark follow the server', /Honda Civic, within 25\smi/.test((await v.card()).text)
      && JSON.stringify(await v.marks()) === JSON.stringify([null, 'Email alert, within 25 mi']), (await v.card()).text);
    await v.ctx.close();
  }

  /* ---- 4. the API refuses (daily cap): the reason is shown, nothing remembered ---- */
  {
    const v = await open(browser, { storage: { ...BASE_STORE, [WL]: ONE },
      api: { '/v1/free-alert/signup': [503, { error: 'daily_cap', message: "Our email sender has reached today's limit. Your watch is saved here; try the email again tomorrow." }] } });
    await v.alerts();
    let c = await v.card();
    check('one watch: no select, the car is named', c.options.length === 0 && /For Toyota 4Runner/.test(c.text) && /within 50\smi/.test(c.text), c.text);
    await v.page.fill('#fa-email', EMAIL);
    await v.page.click('#free-alert .fa-form .btn-primary');
    await until(v.page, /today's limit/);
    c = await v.card();
    check('the cap message is shown in the card', /reached today's limit\. Your watch is saved here; try the email again tomorrow\./.test(c.msg), c.msg);
    check('nothing remembered, the field still there, no "asked" counted', (await v.state()) === null && JSON.stringify(c.inputs) === '["email"]' && count(await v.events(), 'free-alert-asked') === 0);
    await v.ctx.close();
  }
  {
    // The server cannot be reached at all.
    const v = await open(browser, { storage: { ...BASE_STORE, [WL]: ONE }, api: { '/v1/free-alert/signup': [500, { error: 'internal', message: 'Internal error.' }] } });
    await v.alerts();
    await v.page.fill('#fa-email', EMAIL);
    await v.page.click('#free-alert .fa-form .btn-primary');
    await until(v.page, /could not reach/);
    check('a server error: a plain message, nothing remembered', /We could not reach our server/.test((await v.card()).msg) && (await v.state()) === null);
    await v.ctx.close();
  }

  /* ---- 5. an address already confirmed for the Monday email in this browser ---- */
  {
    const v = await open(browser, { storage: { ...BASE_STORE, [WL]: ONE, ys_recap: JSON.stringify({ email: EMAIL, state: 'confirmed', sub: SUB }) },
      api: { '/v1/free-alert/signup': (b) => [200, { ok: true, state: 'on', sub: SUB, watch: { make: b.watch.make, model: b.watch.model, yearMin: null, yearMax: null, radiusMi: 50 } }],
        '/v1/free-alert/status': [200, { ok: true, state: 'on', watch: { make: 'Toyota', model: '4Runner', yearMin: null, yearMax: null, radiusMi: 50 } }] } });
    await v.alerts();
    check('the address is filled in', await v.page.evaluate(() => document.getElementById('fa-email').value) === EMAIL);
    await v.page.click('#free-alert .fa-form .btn-primary');
    await until(v.page, /Free email alert is on/);
    const req = v.sent.find(s => s.path === '/v1/free-alert/signup') || { body: {} };
    check('the Monday email\'s token rides along, so no second confirmation is needed', req.body.sub === SUB && req.body.email === EMAIL, JSON.stringify(req.body));
    const c = await v.card();
    check('on at once, no "check your inbox"', /Free email alert is on/.test(c.text) && /Toyota 4Runner, within 50\smi/.test(c.text) && !/Check your inbox/.test(c.text), c.text);
    check('one watch: "Turn off" only (nothing to change to)', JSON.stringify(c.buttons) === '["Turn off"]');
    check('"asked" counted', count(await v.events(), 'free-alert-asked') === 1);
    check('the Monday email state is untouched', await v.page.evaluate(() => JSON.parse(localStorage.getItem('ys_recap')).state === 'confirmed'));
    // Another address typed instead: the token is NOT sent for it.
    await v.page.evaluate(() => { localStorage.removeItem('ys_falert'); renderAlerts(); });
    v.sent.length = 0;
    await v.page.fill('#fa-email', 'other@example.com');
    await v.page.click('#free-alert .fa-form .btn-primary');
    await v.page.waitForTimeout(400);
    const req2 = v.sent.find(s => s.path === '/v1/free-alert/signup') || { body: {} };
    check('a different address never carries this browser\'s token', req2.body.email === 'other@example.com' && !('sub' in req2.body), JSON.stringify(req2.body));
    await v.ctx.close();
  }

  /* ---- 6. only the first 5 watches; a watch with no centre follows the zip; no watch, no card ---- */
  {
    const v = await open(browser, { storage: { ...BASE_STORE, [WL]: SIX } });
    await v.alerts();
    const c = await v.card();
    check('six watches: the five that alert at all can be picked', c.options.length === 5 && !c.options.includes('Toyota Prius'), JSON.stringify(c.options));
    await v.ctx.close();
  }
  {
    const legacy = JSON.stringify([{ make: 'Ford', model: 'Ranger', yrMin: null, yrMax: null, matchOnly: false, addedAt: '2026-01-01T10:00:00.000Z~old001' }]);
    const v = await open(browser, { storage: { ...BASE_STORE, [WL]: legacy } });
    await v.alerts();
    await v.page.fill('#fa-email', EMAIL);
    await v.page.click('#free-alert .fa-form .btn-primary');
    await until(v.page, /Check your inbox/);
    const req = v.sent[0] || { body: { watch: {} } };
    check('a watch made before the radius picker: centred on the visitor\'s own zip, 50 mi', req.body.watch.lat === 33.45 && req.body.watch.lng === -112.07 && req.body.watch.radiusMi === 50, JSON.stringify(req.body));
    check('...and the stored watch still has no centre (not migrated)', (await v.watches()) === legacy);
    await v.ctx.close();
  }
  {
    const v = await open(browser, { storage: { ...BASE_STORE } });
    await v.alerts();
    check('no watch yet: no card, the sentence in the intro still tells', !(await v.card()).shown && /one watch emailed/.test(await v.note()));
    check('...and nothing was asked of the alert API', v.sent.length === 0);
    await v.ctx.close();
  }

  /* ---- 7. web Pro: unchanged ---- */
  {
    const on = JSON.stringify({ email: EMAIL, key: '2026-11-01T10:00:00.000Z~w1xyz', label: '2003–2009 Toyota 4Runner', r: 50, state: 'on', sub: SUB });
    const v = await open(browser, { storage: { ...BASE_STORE, [WL]: TWO, ys_falert: on } });
    const proPanelFree = await v.page.evaluate(() => { document.querySelector('.tab[data-tab="alerts"]').click(); return document.getElementById('email-alerts-panel').innerText.replace(/\s+/g, ' ').trim(); });
    // The web re-checks a stored Pro flag against its entitlement at boot, so
    // set it the way the other UI tests do, after load.
    await v.page.evaluate(() => { localStorage.setItem('jh_pro', '1'); applyProGates(); renderAlerts(); });
    check('Pro is on for this visitor', await v.page.evaluate(() => isPro()));
    check('Pro on the web: no card, no sentence, no mark on a watch', !(await v.card()).shown && (await v.note()) === '' && (await v.marks()).every(m => m === null));
    const pro = await v.page.evaluate(() => ({ shown: getComputedStyle(document.getElementById('email-alerts-panel')).display !== 'none',
      head: document.querySelector('#email-alerts-panel h4').innerText.replace(/\s+/g, ' ').trim(), copy: document.getElementById('email-alerts-copy').innerText.replace(/\s+/g, ' ').trim(),
      link: getComputedStyle(document.getElementById('email-alerts-link')).display !== 'none', upgrade: getComputedStyle(document.getElementById('email-alerts-upgrade')).display !== 'none' }));
    check('the Pro email alerts panel is what it was (same text, its own controls)', pro.shown && /^Email alerts/.test(pro.head)
      && /Get an email the same day a watched car hits any yard/.test(pro.copy) && pro.link && !pro.upgrade, JSON.stringify(pro));
    check('...and for a free visitor that panel still shows its one "See Pro" button', /Email alerts/.test(proPanelFree) && /See Pro/.test(proPanelFree), proPanelFree);
    await v.page.evaluate(() => { localStorage.removeItem('jh_pro'); applyProGates(); renderAlerts(); });
    check('Pro lapses: the card is back (what the browser remembered was not thrown away)', (await v.card()).shown);
    await v.ctx.close();
  }

  /* ---- 7b. the near-miss line leaves out the cars the email alert covers (2026-11-18) ---- */
  {
    // One watch (Phoenix, 100 mi, set 11-01) and two cars listed three days
    // ago: one 13 mi out (inside the alert's 50 mi), one 78 mi out (inside
    // the watch's own 100 only). The page's inventory is swapped for the two
    // inside one evaluate, so the background loader cannot interfere.
    const DAY = 86400000, listed = new Date(Date.now() - 3 * DAY).toISOString().slice(0, 10);
    const near = { id: 'nm-near', vin: '', year: 2005, make: 'Toyota', model: '4Runner', lat: 33.6, lng: -112.2, dateAdded: listed, location: 'Near Test Yard', row: '1', topParts: [] };
    const far = { id: 'nm-far', vin: '', year: 2006, make: 'Toyota', model: '4Runner', lat: 34.54, lng: -112.47, dateAdded: listed, location: 'Far Test Yard', row: '2', topParts: [] };
    const statusOn = { '/v1/free-alert/status': [200, { ok: true, state: 'on', watch: { make: 'Toyota', model: '4Runner', yearMin: null, yearMax: null, radiusMi: 50 } }] };
    const v = await open(browser, { storage: { ...BASE_STORE, [WL]: ONE }, api: statusOn });
    await v.alerts();
    const miss = (falert, cars) => v.page.evaluate(({ falert, cars }) => {
      if (falert) localStorage.setItem('ys_falert', JSON.stringify(falert)); else localStorage.removeItem('ys_falert');
      liveInventory = cars;
      renderAlerts();
      const el = document.querySelector('#alert-watchlist .watchlist-item');
      const m = el && el.querySelector('.wl-miss');
      return { text: m ? m.textContent.replace(/\s+/g, ' ').trim() : '', pro: !!(el && el.querySelector('.wl-pro')), mark: !!(el && el.querySelector('.wl-falert')) };
    }, { falert, cars });
    const on = (extra) => ({ email: EMAIL, key: '2026-11-01T10:00:00.000Z~w1xyz', label: 'Toyota 4Runner', r: 50, state: 'on', sub: SUB, ...extra });
    let r = await miss(null, [near, far]);
    check('near-miss, no email alert: both cars, with the Pro box', /^2 landed since you set this watch/.test(r.text) && r.pro, JSON.stringify(r));
    r = await miss(on({ onAt: Date.now() - 5 * DAY }), [near, far]);
    check('near-miss, email alert on before they landed: only the car outside its 50 mi', r.mark && /^One landed on/.test(r.text) && r.pro, JSON.stringify(r));
    r = await miss(on({ onAt: Date.now() - 5 * DAY }), [near]);
    check('near-miss, email alert on: a car it covers gets no line and no Pro box', r.mark && r.text === '' && !r.pro, JSON.stringify(r));
    r = await miss(on({ onAt: Date.now() }), [near, far]);
    check('near-miss, email alert turned on after they landed: both still count (it never emailed them)', /^2 landed/.test(r.text) && r.pro, JSON.stringify(r));
    r = await miss(on({}), [near, far]);
    check('near-miss, email alert on since an unknown time: the car in its range is left out', /^One landed on/.test(r.text) && r.pro, JSON.stringify(r));
    r = await miss({ email: EMAIL, key: '2026-11-01T10:00:00.000Z~w1xyz', label: 'Toyota 4Runner', r: 50, state: 'pending', at: Date.now() }, [near, far]);
    check('near-miss, email alert only pending: both cars', /^2 landed/.test(r.text) && r.pro, JSON.stringify(r));
    check('near-miss: the stored watch is untouched (rule 6)', (await v.watches()) === ONE);
    check('near-miss: no page error', !v.errors.length, v.errors.join(' | '));
    await v.ctx.close();
  }

  /* ---- 8. the app shells: never ---- */
  for (const native of ['ios', 'android']) {
    const on = JSON.stringify({ email: EMAIL, key: '2026-11-01T10:00:00.000Z~w1xyz', label: '2003–2009 Toyota 4Runner', r: 50, state: 'on', sub: SUB });
    const v = await open(browser, { origin: 'https://localhost', native, storage: { ...BASE_STORE, [WL]: TWO, ys_falert: on } });
    await v.alerts();
    check(`${native} shell: no card, no sentence, no email-alert mark`, !(await v.card()).shown && (await v.note()) === ''
      && (await v.marks()).every(m => m === null) && await v.page.evaluate(() => !document.getElementById('alerts-free-email-copy')));
    check(`${native} shell: the free instant push is still there`, await v.page.evaluate(() => document.querySelectorAll('#alert-watchlist .wl-instant').length === 1));
    check(`${native} shell: nothing sent to /v1/free-alert, nothing counted`, v.sent.length === 0 && count(await v.events(), 'free-alert-shown') === 0);
    check(`${native} shell: a #falert= link does nothing`, await v.page.evaluate(() => handleFalertHash() === false));
    check(`${native} shell: no page error`, v.errors.length === 0, v.errors.join(' | '));
    await v.ctx.close();
  }

  /* ---- 10. the watch toast's one offer is the free email alert (2026-11-18) ---- */
  {
    const v = await open(browser, { storage: { ...BASE_STORE } });
    const toast = () => v.page.evaluate(() => { const t = document.getElementById('watch-toast'); return t && t.classList.contains('show') ? t.innerText.replace(/\s+/g, ' ').trim() : ''; });
    // The bell on the n-th car's screen (the quick-watch path, as recap_ask_e2e.mjs drives it).
    const bell = async (n) => {
      await v.page.evaluate(() => { try { hideCarDetail(); } catch (e) { /* closed */ } });
      await v.page.waitForTimeout(400);
      await v.page.locator('#live-grid .car-card .car-open').nth(n).click();
      await v.page.waitForSelector('#car-detail.open .watch-btn', { timeout: 15000 });
      const label = await v.page.evaluate(() => { const b = document.querySelector('#car-detail.open .watch-btn'); return `${b.dataset.make} ${b.dataset.model}`.trim(); });
      await v.page.click('#car-detail.open .watch-btn');
      await v.page.waitForSelector('#watch-toast.show', { timeout: 5000 });
      return label;
    };
    await v.page.waitForSelector('#live-grid .car-card .car-open', { timeout: 120000 });
    const label = await bell(0);
    const saved = await v.watches();
    const t = await toast();
    check('toast: a new watch offers the free email alert for that car, in place of the Monday email', t.includes(`Watching ${label}`)
      && /Free email alert for [^:]*/.test(t) && t.includes(label) && /usually the same day/.test(t) && !/Monday email/.test(t), t);
    check('toast: never "instant", "every time" or "always"', !/instant|every time|always|guarantee/i.test(t), t);
    check('toast: one email field, one button, no Pro box, no store link', await v.page.evaluate(() => {
      const ask = document.querySelector('#watch-toast .mail-ask');
      if (!ask) return false;
      const i = ask.querySelectorAll('input'), b = ask.querySelectorAll('button');
      return i.length === 1 && i[0].type === 'email' && b.length === 1 && b[0].textContent.trim() === 'Email me'
        && !document.querySelector('#watch-toast .pro-box, #watch-toast [data-act="app"], #watch-toast [data-act="pro"]');
    }));
    let ev = await v.events();
    check('toast: "free alert shown" counted once, "email asked" (the Monday offer) not at all', ev.filter(e => e === 'free-alert-shown').length === 1 && !ev.includes('email-asked'), JSON.stringify(ev));
    await v.page.fill('#watch-toast .mail-email', 'not-an-address');
    await v.page.click('#watch-toast .mail-form .btn');
    check('toast: a bad address is answered in the toast, nothing sent', /Enter your email address/.test(await toast()) && v.sent.length === 0);
    await v.page.fill('#watch-toast .mail-email', ' Visitor@Example.com ');
    await v.page.click('#watch-toast .mail-form .btn');
    await v.page.waitForFunction(() => /Check your inbox/.test(document.getElementById('watch-toast').innerText), null, { timeout: 5000 }).catch(() => {});
    const req = v.sent.find(x => x.path === '/v1/free-alert/signup') || { body: {} };
    const neww = JSON.parse(saved).slice(-1)[0];
    check('toast: one sign-up request, for the NEW watch, as a copy (at most 50 mi, no addedAt)', v.sent.length === 1 && req.body.email === EMAIL
      && `${req.body.watch.make} ${req.body.watch.model}` === label && req.body.watch.radiusMi <= 50 && !/addedAt|trimFilter|driveFilter|matchOnly/.test(JSON.stringify(req.body)), JSON.stringify(v.sent));
    const t2 = await toast();
    check('toast: "check your inbox", masked address, names the car', /Check your inbox\. Tap the link we sent to v•••@example\.com to turn on your email alert for/.test(t2) && t2.includes(label), t2);
    const st = await v.state();
    check('toast: this browser remembers it as pending, for that watch', st && st.state === 'pending' && st.key === neww.addedAt, JSON.stringify(st));
    ev = await v.events();
    check('toast: "free alert asked" counted once', ev.filter(e => e === 'free-alert-asked').length === 1, JSON.stringify(ev));
    check('toast: the stored watches are byte for byte what they were (rule 6)', (await v.watches()) === saved);
    await v.page.evaluate(() => { try { hideCarDetail(); } catch (e) { /* closed */ } });
    await v.page.waitForTimeout(400);
    await v.alerts();
    check('toast: the Alerts card now waits for the click', /Check your inbox/.test((await v.card()).text), (await v.card()).text);
    await v.page.click('.tab[data-tab="live"]');
    const label2 = await bell(3);
    const t3 = await toast();
    check('toast: with the alert asked for, the next watch is offered the Monday email again', t3.includes(`Watching ${label2}`) && /Monday email/.test(t3) && !/Free email alert/.test(t3), t3);
    check('toast: no page error', !v.errors.length, v.errors.join(' | '));
    await v.ctx.close();
  }

  /* ---- 10b. dismissing the alert offer: the next watch offers the Monday email ---- */
  {
    const v = await open(browser, { storage: { ...BASE_STORE } });
    const toast = () => v.page.evaluate(() => { const t = document.getElementById('watch-toast'); return t && t.classList.contains('show') ? t.innerText.replace(/\s+/g, ' ').trim() : ''; });
    const bell = async (n) => {
      await v.page.evaluate(() => { try { hideCarDetail(); } catch (e) { /* closed */ } });
      await v.page.waitForTimeout(400);
      await v.page.locator('#live-grid .car-card .car-open').nth(n).click();
      await v.page.waitForSelector('#car-detail.open .watch-btn', { timeout: 15000 });
      await v.page.click('#car-detail.open .watch-btn');
      await v.page.waitForSelector('#watch-toast.show', { timeout: 5000 });
    };
    await v.page.waitForSelector('#live-grid .car-card .car-open', { timeout: 120000 });
    await bell(0);
    check('dismiss: offered first', /Free email alert/.test(await toast()));
    await v.page.click('#watch-toast .watch-toast-x');
    await bell(3);
    const t = await toast();
    check('dismiss: the next watch offers the Monday email, not the alert again', /Monday email/.test(t) && !/Free email alert/.test(t), t);
    check('dismiss: nothing was sent', v.sent.length === 0);
    await v.ctx.close();
  }

  /* ---- 11. the Cars watch strip asks for the alert for one model (2026-11-18) ---- */
  {
    // An earlier watch is stored (rule 6: it must come out byte for byte);
    // the strip is for another model in range, taken from the list itself.
    const v = await open(browser, { storage: { ...BASE_STORE, [WL]: ONE } });
    // The whole scan in first, so no late render replaces the strip mid-case
    // (that case is checked on purpose below).
    await v.page.waitForFunction(() => liveComplete && document.querySelector('#live-grid .car-card'), null, { timeout: 180000 });
    const pick = await v.page.evaluate(() => {
      const c = getFilteredLive().find(x => x.make && x.model && !(x.make === 'Toyota' && x.model === '4Runner') && !isNoPickModel(x.make, x.model) && carSearchSetFilter(x.make, canonicalModel(x.make, x.model)));
      if (!c) return null;
      renderLive();
      return { make: c.make, model: [...selectedModels][0] };
    });
    check('strip: a model in range to filter on', !!pick, JSON.stringify(pick));
    const label = pick ? `${pick.make} ${pick.model}` : '';
    await v.page.evaluate(() => { const s = document.querySelector('#live-grid .watch-strip'); if (s) s.scrollIntoView({ block: 'center' }); });
    const strip = () => v.page.evaluate(() => { const s = document.querySelector('#live-grid .watch-strip'); return s ? { fa: s.classList.contains('strip-falert'), text: s.innerText.replace(/\s+/g, ' ').trim(),
      ask: (s.querySelector('.mail-ask') || {}).innerText || '', inputs: [...s.querySelectorAll('.mail-ask input')].map(i => i.type), pro: !!s.querySelector('.mail-ask .pro-box, .mail-ask [onclick*="openUpgradeSheet"]') } : null; });
    let s = await strip();
    check('strip: one model, free web visitor: the free email alert for that car, in place of the Monday email', s && s.fa && s.text.includes(`Free email alert for ${label}: we email you when`)
      && /within 50\smi, usually the same day\. One car, one address, no account\./.test(s.text) && !/Monday/.test(s.ask), JSON.stringify(s));
    check('strip: one email field, no Pro prompt inside the ask', s && JSON.stringify(s.inputs) === '["email"]' && !s.pro && !/\bPro\b/.test(s.ask), JSON.stringify(s));
    let ev = await v.events();
    check('strip: "free alert shown" sent once it is on screen, "email asked" (the Monday offer) not at all', count(ev, 'free-alert-shown') === 1 && count(ev, 'email-asked') === 0, JSON.stringify(ev));
    await v.page.evaluate(() => { renderLive(); renderLive(); });
    await v.page.evaluate(() => document.querySelector('#live-grid .watch-strip').scrollIntoView({ block: 'center' }));
    check('strip: ...and not again on a re-render', count(await v.events(), 'free-alert-shown') === 1);
    await v.page.fill('#live-grid .strip-falert .mail-email', ' Visitor@Example.com ');
    await v.page.click('#live-grid .strip-falert .mail-form .btn');
    await v.page.waitForFunction(() => /Check your inbox/.test((document.querySelector('#live-grid .strip-falert') || {}).innerText || ''), null, { timeout: 8000 }).catch(() => {});
    const wl = JSON.parse(await v.watches());
    const req = v.sent.find(x => x.path === '/v1/free-alert/signup') || { body: { watch: {} } };
    check('strip: exactly one new watch, made as the strip always made it (the list\'s 100 mi); the earlier one byte for byte (rule 6)',
      wl.length === 2 && JSON.stringify(wl[0]) === JSON.stringify(JSON.parse(ONE)[0]) && `${wl[1].make} ${wl[1].model}` === label && wl[1].radiusMi === 100, JSON.stringify(wl));
    check('strip: one request, a copy of the NEW watch (50 mi, rounded centre, no addedAt)', v.sent.length === 1 && req.body.email === EMAIL
      && JSON.stringify(req.body.watch) === JSON.stringify({ make: pick.make, model: pick.model, yearMin: null, yearMax: null, lat: 33.45, lng: -112.07, radiusMi: 50 }) && !/addedAt/.test(JSON.stringify(req.body)), JSON.stringify(v.sent));
    s = await strip();
    check('strip: "check your inbox" for the alert, and the car is watched', /Check your inbox\. Tap the link we sent to v•••@example\.com to turn on your email alert for/.test(s.text) && s.text.includes(`Watching ${label}`), s.text);
    const st = await v.state();
    check('strip: the alert is pending in its own key, for the new watch', st && st.state === 'pending' && st.key === wl[1].addedAt && st.label === label && st.r === 50, JSON.stringify(st));
    ev = await v.events();
    check('strip: "free alert asked" sent once; no Monday-email event', count(ev, 'free-alert-asked') === 1 && count(ev, 'email-asked') === 0 && count(ev, 'email-submitted') === 0, JSON.stringify(ev));
    // A later render (a scan coming in) shows the strip as watched: it still
    // says the alert waits for the click, and goes on to say when it is on.
    await v.page.evaluate(() => renderLive());
    s = await strip();
    check('strip: re-rendered as watched, it still says to check the inbox', s && !s.fa && s.text.includes(`Watching ${label}`) && /Check your inbox to turn on its email alert\./.test(s.text), s && s.text);
    await v.page.evaluate(() => { const f = JSON.parse(localStorage.getItem('ys_falert')); localStorage.setItem('ys_falert', JSON.stringify({ ...f, state: 'on', sub: 'x.' + 'a'.repeat(64) })); renderLive(); });
    s = await strip();
    check('strip: ...and that its free email alert is on, once it is', s && /Its free email alert is on\./.test(s.text) && !/Check your inbox/.test(s.text), s && s.text);
    await v.page.evaluate((p) => { localStorage.setItem('ys_falert', p); renderLive(); }, JSON.stringify(st));
    await v.alerts();
    check('strip: the Alerts card agrees (waiting for the click, that car)', /Check your inbox/.test((await v.card()).text) && (await v.card()).text.includes(label), (await v.card()).text);
    check('strip: "shown" still once this visit', count(await v.events(), 'free-alert-shown') === 1);
    check('strip: no page error, no dialog', !v.errors.length && !v.dialogs.length, JSON.stringify([v.errors, v.dialogs]));
    await v.ctx.close();
  }

  /* ---- 9. a wide screen: the card still fits its column ---- */
  {
    const v = await open(browser, { storage: { ...BASE_STORE, [WL]: TWO }, width: 1280 });
    await v.alerts();
    check('1280 px: the card is shown and no wider than the watchlist', await v.page.evaluate(() => {
      const a = document.getElementById('free-alert').getBoundingClientRect(), b = document.getElementById('alert-watchlist').getBoundingClientRect();
      return a.width > 0 && a.width <= b.width + 1 && document.documentElement.scrollWidth <= innerWidth;
    }));
    await v.shot('falert_6_wide');
    await v.ctx.close();
  }
} finally {
  await browser.close();
}
console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
