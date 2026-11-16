/* E2E: the free instant alert in the apps (owner decision 2026-11-16).
 *
 * The real docs/ bundle from a local server on 127.0.0.1; every other host is
 * blocked, and the API's /v1/device/register is answered by this script,
 * which records what the page sends. The native shell is stubbed as in
 * recap_ask_e2e.mjs, with a stored push token so the app registers.
 *
 *   iOS free, 3 watches   one watch marked "Instant alert, within 50 mi" (the
 *                         first, by default); the others offer "Make this my
 *                         instant alert"; one tap moves it; the registration
 *                         carries exactly one instant:true, on that watch; the
 *                         choice survives a reload; the stored watches are
 *                         byte for byte what they were
 *   iOS free, 1 watch     simply marked, no move control
 *   Android free          same flag, in the fcmToken registration
 *   iOS Pro, web          no mark, no control, no flag
 *   copy                  the Pro sheet and Alerts lines say what free gets
 *
 * Run: node backend/test/free_instant_e2e.mjs   (SHOTS=<dir> for screenshots) */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const DOCS = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../docs');
const SHOTS = process.env.SHOTS || '';
const T = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2', '.webp': 'image/webp', '.webmanifest': 'application/manifest+json', '.ico': 'image/x-icon' };
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

let failures = 0, passes = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + String(detail).slice(0, 400)}`); if (ok) passes++; else failures++; };

const WL = 'yardscout_watchlist';
const PHX = { lat: 33.45, lng: -112.07 };
const W = (make, model, i, extra = {}) => ({ make, model, yrMin: null, yrMax: null, matchOnly: false, radiusMi: 100, ...PHX,
  driveFilter: '', trimFilter: '', addedAt: `2026-11-0${i}T10:00:00.000Z~w${i}xyz`, ...extra });
const THREE = JSON.stringify([W('Toyota', 'Camry', 1), W('Honda', 'Accord', 2, { radiusMi: 25 }), W('Ford', 'F150', 3)]);
const ONE = JSON.stringify([W('Toyota', 'Camry', 1)]);
const BASE_STORE = {
  jh_honesty_ack: '1', ys_seen: '1', ys_app_promo: '1',
  jh_zip: '85003', jh_zip_coords: JSON.stringify({ 85003: PHX }), jh_radius: '100',
};

async function open(browser, { native = null, storage = {}, entitled = false } = {}) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, hasTouch: true, serviceWorkers: 'block' });
  const page = await ctx.newPage();
  const regs = [];
  await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, (route) => {
    const q = route.request();
    const u = new URL(q.url());
    const cors = { 'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': '*' };
    if (q.method() === 'OPTIONS') return route.fulfill({ status: 204, headers: cors });
    if (u.pathname === '/v1/device/register' && q.method() === 'POST') {
      regs.push(JSON.parse(q.postData() || '{}'));
      return route.fulfill({ status: 200, contentType: 'application/json', headers: cors, body: '{"ok":true,"push":true}' });
    }
    // The app shells read data from https://yardscout.io/data/ (DATA_BASE):
    // answered from the local docs/ folder, never the live site.
    if (u.hostname === 'yardscout.io') {
      const f = path.join(DOCS, path.normalize(decodeURIComponent(u.pathname)));
      if (f.startsWith(DOCS) && fs.existsSync(f) && !fs.statSync(f).isDirectory()) {
        return route.fulfill({ path: f, contentType: T[path.extname(f)] || 'application/octet-stream', headers: cors });
      }
      return route.fulfill({ status: 404, headers: cors, body: '' });
    }
    return route.abort();
  });
  await page.addInitScript(({ native, storage, entitled }) => {
    if (!sessionStorage.getItem('__seeded')) { for (const [k, v] of Object.entries(storage)) localStorage.setItem(k, v); sessionStorage.setItem('__seeded', '1'); }
    document.addEventListener('DOMContentLoaded', () => {
      const st = document.createElement('style');
      st.textContent = '*,*::before,*::after{transition-duration:0s!important;animation-duration:0s!important}';
      document.head.appendChild(st);
    });
    if (native) {
      const L = () => ({ remove() {} });
      // Push: register() hands back the stored token, as APNs / FCM do at
      // launch, so the app's own launch re-registration runs.
      const pn = {};
      window.Capacitor = { isNativePlatform: () => true, getPlatform: () => native, Plugins: {
        // Pro comes from the store entitlement check, as in the real apps.
        Purchases: { isEntitled: async () => ({ entitled: !!entitled }), getProduct: async () => ({ available: false }), purchase: async () => ({ cancelled: true }), restore: async () => ({ entitled: !!entitled }) },
        PushNotifications: { addListener: (n, fn) => { pn[n] = fn; return { remove() {} }; }, checkPermissions: async () => ({ receive: 'granted' }), requestPermissions: async () => ({ receive: 'granted' }),
          register: async () => { setTimeout(() => pn.registration && pn.registration({ value: localStorage.getItem('ys_push_token') }), 50); } },
        App: { addListener: L, getInfo: async () => ({ version: '1.12.15', build: '37' }), getLaunchUrl: async () => null },
        Geolocation: { getCurrentPosition: async () => { throw new Error('x'); }, checkPermissions: async () => ({ location: 'prompt' }) },
        StatusBar: { setStyle: async () => {}, setBackgroundColor: async () => {} },
      } };
    }
  }, { native, storage, entitled });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e.message).slice(0, 160)));
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => typeof liveLoaded !== 'undefined' && liveLoaded, null, { timeout: 180000 });
  const alerts = async () => {
    await page.click('.tab[data-tab="alerts"]');
    await page.waitForSelector('#alert-watchlist .watchlist-item', { timeout: 20000 });
  };
  const list = () => page.evaluate(() => [...document.querySelectorAll('#alert-watchlist .watchlist-item')].map((el) => ({
    name: el.querySelector('.wl-name').textContent,
    instant: el.querySelector('.wl-instant') ? el.querySelector('.wl-instant').textContent : null,
    move: !!el.querySelector('.wl-instant-move'),
  })));
  const shot = async (name) => {
    if (!SHOTS) return;
    fs.mkdirSync(SHOTS, { recursive: true });
    // The phone screen (390 x 844) with the watch list near the top.
    await page.evaluate(() => { const el = document.getElementById('alert-watchlist'); window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - 120); });
    await page.waitForTimeout(200);
    await page.screenshot({ path: path.join(SHOTS, name + '.png') });
  };
  return { ctx, page, regs, errors, alerts, list, shot };
}
const flags = (reg) => (reg.watches || []).map((w, i) => (w.instant === true ? i : -1)).filter((i) => i >= 0);
const lastReg = async (v, n) => { for (let i = 0; i < 40 && v.regs.length < n; i++) await v.page.waitForTimeout(250); return v.regs[v.regs.length - 1]; };

const PUSH_IOS = { ys_push_on: '1', ys_push_token: 'ab'.repeat(32) };
const PUSH_AND = { ys_push_on: '1', ys_push_token: 'fcmtok:APA91b' + 'x'.repeat(100) };

const browser = await chromium.launch();
try {
  /* ---- 1. iOS free, three watches ---- */
  {
    const v = await open(browser, { native: 'ios', storage: { ...BASE_STORE, ...PUSH_IOS, [WL]: THREE } });
    await v.alerts();
    let l = await v.list();
    check('three watches listed', l.length === 3, JSON.stringify(l));
    check('exactly one instant watch, the first by default', l.filter((x) => x.instant).length === 1 && l[0].instant, JSON.stringify(l));
    check('marked "Instant alert, within 50 mi" (100 mi watch clamped)', l[0].instant === 'Instant alert, within 50 mi', l[0].instant);
    check('the other two offer "Make this my instant alert"', !l[0].move && l[1].move && l[2].move, JSON.stringify(l));
    const moveText = await v.page.evaluate(() => document.querySelector('.wl-instant-move').textContent);
    check('the move control reads "Make this my instant alert"', moveText === 'Make this my instant alert', moveText);
    await v.shot('ios-free-three-watches');
    const r0 = await lastReg(v, 1);
    check('launch registration carries exactly one flag, on the first watch', r0 && JSON.stringify(flags(r0)) === '[0]', JSON.stringify(r0 && r0.watches));
    check('registration is the iOS shape (apnsToken, tier free)', r0 && r0.apnsToken && r0.tier === 'free' && !r0.fcmToken, JSON.stringify(r0 && { t: r0.tier, a: !!r0.apnsToken }));
    const pushSt = await v.page.evaluate(() => document.getElementById('native-push-status').textContent);
    check('push status names the instant alert and the Monday recap', pushSt === 'Push is on — your instant alert pushes within hours; the rest come in your Monday recap.', pushSt);

    const before = await v.page.evaluate((k) => localStorage.getItem(k), WL);
    const n = v.regs.length;
    await v.page.locator('#alert-watchlist .watchlist-item').nth(1).locator('.wl-instant-move').click();
    await v.page.waitForTimeout(300);
    l = await v.list();
    check('one tap moves it: the 25 mi watch is now the instant one', l[1].instant === 'Instant alert, within 25 mi' && !l[0].instant && !l[2].instant, JSON.stringify(l));
    check('the old one now offers the move', l[0].move && l[2].move && !l[1].move, JSON.stringify(l));
    const r1 = await lastReg(v, n + 1);
    check('the tap re-registers with exactly one flag, on that watch', v.regs.length > n && JSON.stringify(flags(r1)) === '[1]', JSON.stringify(r1 && r1.watches));
    const after = await v.page.evaluate((k) => localStorage.getItem(k), WL);
    check('stored watches unchanged byte for byte', after === before && after === THREE, after);
    const key = await v.page.evaluate(() => localStorage.getItem('ys_instant_watch'));
    check('the choice lives in its own key (the watch addedAt)', key === '2026-11-02T10:00:00.000Z~w2xyz', key);
    await v.page.reload({ waitUntil: 'domcontentloaded' });
    await v.page.waitForFunction(() => typeof liveLoaded !== 'undefined' && liveLoaded, null, { timeout: 180000 });
    await v.alerts();
    l = await v.list();
    check('the choice survives a reload', l[1].instant && !l[0].instant, JSON.stringify(l));

    // Copy for the native free tier.
    const intro = await v.page.evaluate(() => document.getElementById('alerts-intro-copy').innerText);
    check('Alerts intro says one watch pushes within hours (50 mi)', /one watch pushes within hours/.test(intro) && /50\s?mi/.test(intro) && /weekly recap push/.test(intro), intro);
    await v.page.evaluate(() => openUpgradeSheet('watch-limit'));
    await v.page.waitForTimeout(300);
    const sheet = await v.page.evaluate(() => ({ lead: document.getElementById('pro-proof').textContent,
      sub: document.querySelector('#upgrade-sheet .sheet-sub').textContent, li: document.getElementById('tier-alerts-li').innerText }));
    check('Pro sheet lead (watch limit) states the free instant watch', /one pushes within hours for cars within 50 mi/.test(sheet.lead), sheet.lead);
    check('Pro sheet intro no longer says "Free gets a Monday recap instead"', !/Monday recap instead/.test(sheet.sub) && /Free pushes one watch within 50 mi/.test(sheet.sub), sheet.sub);
    check('Pro sheet bullet: every watch, any distance; free one watch within 50 mi', /every watch, at any distance/.test(sheet.li) && /one watch within 50\s?mi/.test(sheet.li), sheet.li);
    check('no page errors (iOS free)', v.errors.length === 0, v.errors.join(' | '));
    await v.ctx.close();
  }

  /* ---- 2. iOS free, one watch: simply marked ---- */
  {
    const v = await open(browser, { native: 'ios', storage: { ...BASE_STORE, ...PUSH_IOS, [WL]: ONE } });
    await v.alerts();
    const l = await v.list();
    check('one watch: marked as the instant alert, no move control', l.length === 1 && l[0].instant === 'Instant alert, within 50 mi' && !l[0].move, JSON.stringify(l));
    await v.shot('ios-free-one-watch');
    const r = await lastReg(v, 1);
    check('one watch: registration flags it', r && JSON.stringify(flags(r)) === '[0]', JSON.stringify(r && r.watches));
    await v.ctx.close();
  }

  /* ---- 3. Android free: same flag in the FCM registration ---- */
  {
    const v = await open(browser, { native: 'android', storage: { ...BASE_STORE, ...PUSH_AND, [WL]: THREE, ys_instant_watch: '2026-11-03T10:00:00.000Z~w3xyz' } });
    await v.alerts();
    const l = await v.list();
    check('Android: the stored choice (third watch) is the instant one', l[2].instant && !l[0].instant && !l[1].instant, JSON.stringify(l));
    const r = await lastReg(v, 1);
    check('Android: fcmToken registration with exactly one flag, on the third watch', r && r.fcmToken && JSON.stringify(flags(r)) === '[2]', JSON.stringify(r && r.watches));
    await v.ctx.close();
  }

  /* ---- 4. iOS Pro: no mark, no control, no flag ---- */
  {
    const v = await open(browser, { native: 'ios', storage: { ...BASE_STORE, ...PUSH_IOS, [WL]: THREE }, entitled: true });
    await v.page.waitForFunction(() => isPro(), null, { timeout: 10000 }).catch(() => {});
    await v.page.evaluate(() => renderAlerts());
    await v.alerts();
    const l = await v.list();
    check('Pro: no instant mark and no move control', l.length === 3 && l.every((x) => !x.instant && !x.move), JSON.stringify(l));
    const r = await lastReg(v, 1);
    check('Pro: registration (tier pro) carries no instant flag', r && r.tier === 'pro' && flags(r).length === 0 && !(r.watches || []).some((w) => 'instant' in w), JSON.stringify(r && r.watches));
    await v.ctx.close();
  }

  /* ---- 5. web: no control, no registration ---- */
  {
    const v = await open(browser, { storage: { ...BASE_STORE, [WL]: THREE } });
    await v.alerts();
    const l = await v.list();
    check('web: no instant mark and no move control', l.length === 3 && l.every((x) => !x.instant && !x.move), JSON.stringify(l));
    await v.page.waitForTimeout(2000);
    check('web: nothing sent to /v1/device/register', v.regs.length === 0, JSON.stringify(v.regs));
    const intro = await v.page.evaluate(() => document.getElementById('alerts-intro-copy').innerText);
    // HELD (hub, 2026-11-16): until the app release with the free instant
    // alert is live in both stores, the website keeps the old sentence, so it
    // never promises what the store versions do not do yet (see the HELD
    // comment in docs/index.html). When the release is live, switch the page
    // text and make this check expect "free gets one watch pushed within hours".
    check('web intro: no instant-alert promise before the app release is live',
      /in the iOS and Android apps free watches get a weekly recap push/.test(intro) && !/one watch pushed within hours/.test(intro), intro);
    await v.page.evaluate(() => openUpgradeSheet('watch-limit'));
    await v.page.waitForTimeout(300);
    const lead = await v.page.evaluate(() => document.getElementById('pro-proof').textContent);
    check('web Pro sheet lead unchanged (Monday recap)', /with a recap every Monday/.test(lead), lead);
    check('no page errors (web)', v.errors.length === 0, v.errors.join(' | '));
    await v.ctx.close();
  }
} finally {
  await browser.close();
  srv.close();
}
console.log(`\n${passes} passed, ${failures} failed`);
process.exit(failures ? 1 : 0);
