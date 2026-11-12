/* E2E: the Pro sheet's buy button and first price are on screen without
 * scrolling (2026-11-12 funnel audit: the button sat 80 to 490 px below the
 * fold on a phone, and the $1.99 first month only appeared next to it).
 *
 * Opens the real sheet on the web (checkout live) and inside both app shells
 * (Capacitor stub, the store reporting the $1.99 intro offer) at 390x844,
 * 375x667 and 320x568, light and dark, 100% and 200% text, and checks that
 *   - the primary button is fully inside the viewport and is what a tap hits
 *   - the price line under it is inside the viewport too
 *   - the feature list scrolls under the button (the button does not move)
 *   - an Android browser's store link goes to Google Play, an iPhone's to
 *     the App Store
 * docs/ is answered from disk (as https://yardscout.io/ and, for the shells,
 * https://localhost/); nothing reaches production.
 *
 * Run: node backend/test/pro_sheet_fold_e2e.mjs   (SHOTS=<dir> saves a
 * screenshot of every case). */
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
const SIZES = [[390, 844], [375, 667], [320, 568]];
const UA = { ios: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
  android: 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36' };

let failures = 0, passes = 0;
const check = (name, ok, detail = '') => { if (ok) passes++; else failures++; if (!ok || process.env.VERBOSE) console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + detail}`); };

const fileFor = (pathname) => {
  let p = decodeURIComponent(pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(DOCS, path.normalize(p));
  return f.startsWith(DOCS) && fs.existsSync(f) && !fs.statSync(f).isDirectory() ? f : null;
};
/* Same 200% text emulation as ui_no_truncation.mjs (computed sizes doubled). */
const ZOOM_FN = (on) => {
  if (on) {
    const els = [...document.querySelectorAll('html, body, body *')];
    const orig = els.map(el => { const cs = getComputedStyle(el); return [cs.fontSize, cs.lineHeight]; });
    window.__z = els.map((el) => [el, el.style.getPropertyValue('font-size'), el.style.getPropertyPriority('font-size'), el.style.getPropertyValue('line-height'), el.style.getPropertyPriority('line-height')]);
    els.forEach((el, i) => {
      const [f, lh] = orig[i];
      el.style.setProperty('font-size', parseFloat(f) * 2 + 'px', 'important');
      if (lh.endsWith('px')) el.style.setProperty('line-height', parseFloat(lh) * 2 + 'px', 'important');
    });
  } else if (window.__z) {
    for (const [el, f, fp, lh, lhp] of window.__z) {
      el.style.removeProperty('font-size'); el.style.removeProperty('line-height');
      if (f) el.style.setProperty('font-size', f, fp); if (lh) el.style.setProperty('line-height', lh, lhp);
    }
    window.__z = null;
  }
};

/* kind: 'web-ios' | 'web-android' (a phone browser on yardscout.io) | 'ios' | 'android' (app shell). */
async function open(browser, kind, w, h) {
  const native = kind === 'ios' || kind === 'android' ? kind : null;
  const origin = native ? 'https://localhost' : 'https://yardscout.io';
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 1, hasTouch: true, userAgent: UA[/android/.test(kind) ? 'android' : 'ios'], serviceWorkers: 'block' });
  const page = await ctx.newPage();
  await page.route('**/*', (route) => {
    const u = new URL(route.request().url());
    if (/api\.zippopotam\.us/.test(u.hostname)) return route.fulfill({ json: { places: [{ latitude: '33.4511', longitude: '-112.0783' }] }, headers: { 'access-control-allow-origin': '*' } });
    if (u.pathname === '/api/ent/config') return route.fulfill({ json: { billing: true }, headers: { 'access-control-allow-origin': '*' } });
    if (u.hostname === 'yardscout.io' || u.origin === origin) {
      const f = fileFor(u.pathname);
      if (f) return route.fulfill({ path: f, contentType: TYPES[path.extname(f)] || 'application/octet-stream', headers: { 'access-control-allow-origin': '*' } });
      return route.fulfill({ status: 404, body: '' });
    }
    if (/fonts\.(googleapis|gstatic)\.com/.test(u.hostname)) return route.continue();   // the fonts shape every line break
    return route.abort();
  });
  await page.addInitScript((native) => {
    navigator.sendBeacon = () => true;
    document.addEventListener('DOMContentLoaded', () => {
      const st = document.createElement('style');
      st.textContent = '*,*::before,*::after{transition-duration:0s!important;transition-delay:0s!important;animation-duration:0s!important;animation-delay:0s!important}';
      document.head.appendChild(st);
    });
    if (native) {
      const L = () => ({ remove() {} });
      window.Capacitor = { isNativePlatform: () => true, getPlatform: () => native, Plugins: {
        Purchases: { isEntitled: async () => ({ entitled: false }), getProduct: async () => ({ available: true, price: '$8.99', introPrice: '$1.99', introPeriod: '1 month', introCycles: 1 }),
          purchase: async () => ({ cancelled: true }), restore: async () => ({ entitled: false }) },
        PushNotifications: { addListener: L, checkPermissions: async () => ({ receive: 'prompt' }), requestPermissions: async () => ({ receive: 'denied' }), register: async () => {} },
        App: { addListener: L, getInfo: async () => ({ version: '1.12.14', build: '36' }), getLaunchUrl: async () => null },
        Geolocation: { getCurrentPosition: async () => { throw new Error('x'); }, checkPermissions: async () => ({ location: 'prompt' }) },
        StatusBar: { setStyle: async () => {}, setBackgroundColor: async () => {} },
      } };
    }
  }, native);
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e.message).slice(0, 160)));
  await page.goto(origin + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => typeof liveLoaded !== 'undefined' && liveLoaded, null, { timeout: 180000 });
  await page.fill('#zip-banner-input', '85003');
  await page.click('#zip-banner-go');
  await page.waitForSelector('#live-grid .car-card', { timeout: 120000 });
  await page.waitForTimeout(600);
  return { ctx, page, native, errors };
}

const measure = (page, native) => page.evaluate((native) => {
  const sheet = document.getElementById('upgrade-sheet').getBoundingClientRect();
  const b = document.getElementById(native ? 'iap-subscribe' : 'ent-checkout');
  const l = native ? document.getElementById('iap-intro') : document.querySelector('#ent-buy .sheet-foot-line');
  const br = b.getBoundingClientRect(), lr = l ? l.getBoundingClientRect() : null;
  const hit = br.height ? document.elementFromPoint(br.left + br.width / 2, br.top + br.height / 2) : null;
  const sc = document.getElementById('upgrade-scroll');
  let moved = null;
  if (sc) { sc.scrollTop = sc.scrollHeight; moved = Math.abs(b.getBoundingClientRect().top - br.top); sc.scrollTop = 0; }
  return { vh: innerHeight, sheetTop: Math.round(sheet.top), top: Math.round(br.top), bottom: Math.round(br.bottom), h: br.height,
    hit: !!hit && (hit === b || b.contains(hit)), text: b.innerText.trim(), line: lr && lr.height ? [Math.round(lr.top), Math.round(lr.bottom), l.innerText.trim()] : null,
    scrolls: !!sc && sc.scrollHeight > sc.clientHeight + 1, moved };
}, native);

const browser = await chromium.launch();
try {
  for (const kind of ['web-ios', 'web-android', 'ios', 'android']) {
    for (const [w, h] of SIZES) {
      if (kind === 'web-android' && w !== 390) continue;   // the store link only; the layout is web-ios's
      const { ctx, page, native, errors } = await open(browser, kind, w, h);
      for (const theme of kind === 'web-android' ? ['light'] : ['light', 'dark']) {
        await page.emulateMedia({ colorScheme: theme });
        await page.evaluate((t) => { document.documentElement.dataset.theme = t; }, theme);
        for (const zoom of kind === 'web-android' ? [1] : [1, 2]) {
          await page.evaluate(() => { closeUpgradeSheet(); openUpgradeSheet('header-pill'); });
          if (native) await page.waitForFunction(() => /\$1\.99/.test(document.getElementById('iap-subscribe').textContent), null, { timeout: 10000 });
          else await page.waitForFunction(() => document.getElementById('ent-buy').style.display !== 'none', null, { timeout: 10000 });
          if (zoom === 2) await page.evaluate(ZOOM_FN, true);
          await page.waitForTimeout(250);
          const m = await measure(page, native);
          const at = `${kind} ${w}x${h} ${theme} ${zoom * 100}%`;
          if (SHOTS) { fs.mkdirSync(SHOTS, { recursive: true }); await page.screenshot({ path: path.join(SHOTS, `fold_${kind}_${w}x${h}_${theme}_${zoom * 100}.png`) }); }
          if (zoom === 2) await page.evaluate(ZOOM_FN, false);
          check(`${at}: buy button fully on screen (${m.top}..${m.bottom} of ${m.vh})`, m.h > 0 && m.top >= Math.max(0, m.sheetTop) && m.bottom <= m.vh, JSON.stringify(m));
          check(`${at}: a tap on the button reaches it`, m.hit, JSON.stringify(m));
          check(`${at}: the price line is on screen under the button`, !!m.line && m.line[0] >= m.bottom - 1 && m.line[1] <= m.vh, JSON.stringify(m));
          check(`${at}: the list scrolls under the button, which stays put`, m.scrolls && m.moved !== null && m.moved <= 1, JSON.stringify(m));
          if (zoom === 1 && theme === 'light') {
            if (native) {
              check(`${at}: the button states the first price, the line what follows`, m.text === 'Start for $1.99 — first month' && m.line && m.line[2] === 'Then $8.99/mo. Cancel anytime.', JSON.stringify([m.text, m.line]));
              check(`${at}: the store's fine print and Restore are still in the sheet`, await page.evaluate((android) => {
                const n = document.getElementById('iap-note'), r = document.getElementById('iap-restore');
                return !!r.getClientRects().length && !!n.getClientRects().length && (android ? /Google Play account/ : /App Store account/).test(n.textContent) && /Privacy/.test(n.textContent) && /Terms/.test(n.textContent);
              }, native === 'android'));
              check(`${at}: no web checkout or store link inside the app`, await page.evaluate(() => !document.getElementById('ent-checkout').getClientRects().length
                && ![...document.querySelectorAll('#upgrade-sheet a[href]')].some(a => /apps\.apple\.com|play\.google\.com/.test(a.href) && a.getClientRects().length)));
            } else {
              check(`${at}: the web button and line keep the price as it was`, m.text === 'Get Pro — $8.99/mo' && m.line && m.line[2] === '$8.99/month, cancel anytime.', JSON.stringify([m.text, m.line]));
              const links = await page.evaluate(() => [...document.querySelectorAll('#upgrade-sheet a[href]')].filter(a => /apps\.apple\.com|play\.google\.com/.test(a.href) && a.getClientRects().length).map(a => [a.href, a.textContent.trim()]));
              const want = kind === 'web-android' ? /^https:\/\/play\.google\.com\/store\/apps\/details\?id=io\.yardscout\.app$/ : /^https:\/\/apps\.apple\.com\/app\/.*id6817126581$/;
              check(`${at}: "Prefer the app?" offers this phone's store only`, links.length === 1 && want.test(links[0][0]) && (kind === 'web-android' ? /Google Play/ : /App Store/).test(links[0][1]), JSON.stringify(links));
              check(`${at}: the store account line matches the store`, await page.evaluate((android) => {
                const t = document.getElementById('upgrade-form-wrap').innerText;   // what is shown, not the other store's hidden link
                return android ? /Google Play account/.test(t) && /Play Store subscriptions/.test(t) && !/iOS Settings/.test(t) : /App Store account/.test(t) && /iOS Settings/.test(t) && !/Google Play/.test(t);
              }, kind === 'web-android'));
            }
          }
        }
      }
      check(`${kind} ${w}x${h}: no page errors`, errors.length === 0, JSON.stringify(errors));
      await ctx.close();
    }
  }
} catch (e) {
  check('harness ran to the end', false, String(e && e.stack || e).split('\n').slice(0, 4).join(' | '));
} finally {
  await browser.close();
}
console.log(`\n${passes} passed, ${failures} failed`);
console.log(failures ? 'PRO SHEET FOLD CHECK FAILED' : 'ALL PASS');
process.exit(failures ? 1 : 0);
