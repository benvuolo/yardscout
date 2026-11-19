/* E2E: the compact arrival forecast under the Alerts tab's watch rows
 * (2026-11-19). The real docs/ bundle served AS https://yardscout.io/ from
 * disk by Playwright routing (no local server, no port), service workers
 * blocked, docs/data/arrivals/ answered from a fixture (made-up yards and
 * counts), everything outside aborted.
 *
 *   shows        a plain one-model watch with a centre and a radius
 *   not shown    a trim watch, a drive watch, a make-only watch, a watch with
 *                no centre, an "anywhere" watch, a "Parts only" watch
 *   missing file a make whose file is missing: the mount point stays empty, 0 px
 *   one load     the make file is fetched once over several re-renders
 *   rule 6       the stored watch list is byte-for-byte the same before and
 *                after the tab renders with forecasts
 *   words        the compact block says the module's own words for the watch
 *   counter      watch-forecast/shown once per visit
 *   no page error; no horizontal overflow at 320 px
 *
 * Run: node backend/test/watch_forecast_e2e.mjs */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const DOCS = path.join(ROOT, 'docs');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json' };
let failures = 0, passes = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + String(detail).slice(0, 500)}`); if (ok) passes++; else failures++; };
const fileFor = (pathname) => {
  let p = decodeURIComponent(pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(DOCS, path.normalize(p));
  return f.startsWith(DOCS) && fs.existsSync(f) && !fs.statSync(f).isDirectory() ? f : null;
};

// ---- fixture arrivals (made up) around San Jose ----
const BUILT = '2026-11-19T07:00:00Z';
const INDEX = {
  builtAt: BUILT, windowStart: '2026-09-24', windowEnd: '2026-11-18', weeks: 8,
  yardFields: ['location', 'lat', 'lng', 'coveredWeeks', 'stale'],
  yards: [
    ['Sample Yard - San Jose', 37.35, -121.88, 8, 0],
    ['Sample Yard - Oakland', 37.80, -122.27, 8, 0],
    ['Sample Yard - Reno', 39.53, -119.81, 8, 0],
  ],
  makes: { Toyota: ['toyota', 0], Honda: ['honda', 0] },   // honda.json is missing on purpose
};
const TOYOTA = {
  builtAt: BUILT, windowEnd: '2026-11-18', make: 'Toyota', slug: 'toyota',
  models: {
    '4Runner': [[0, 2004, 1, 0, 1, 0, 2, 0, 1, 1], [1, 2007, 0, 1, 0, 1, 0, 1, 0, 1], [2, 2005, 5, 5, 5, 5, 5, 5, 5, 5], [0, 2015, 3, 3, 3, 3, 3, 3, 3, 3]],
    Tacoma: [[0, 2010, 1, 1, 1, 1, 1, 1, 1, 1]],
  },
};
const C = { lat: 37.3485, lng: -121.8863 };
const W = (over) => ({ make: 'Toyota', model: '4Runner', yrMin: 2003, yrMax: 2009, matchOnly: false, radiusMi: 100, driveFilter: '', trimFilter: '', ...C, ...over });
const WATCHES = [
  W({ addedAt: '2026-11-01T00:00:00.000Z~a1' }),                                   // 0 shows
  W({ model: 'Tacoma', trimFilter: 'TRD', addedAt: '2026-11-02T00:00:00.000Z~a2' }), // 1 trim: no
  W({ model: 'Tacoma', driveFilter: '4x4', addedAt: '2026-11-03T00:00:00.000Z~a3' }), // 2 drive: no
  W({ model: '', addedAt: '2026-11-04T00:00:00.000Z~a4' }),                         // 3 make only: no
  W({ model: 'Tacoma', lat: undefined, lng: undefined, addedAt: '2026-11-05T00:00:00.000Z~a5' }), // 4 no centre: no
  W({ model: 'Tacoma', radiusMi: 0, addedAt: '2026-11-06T00:00:00.000Z~a6' }),      // 5 anywhere: no
  W({ model: 'Tacoma', matchOnly: true, addedAt: '2026-11-07T00:00:00.000Z~a7' }),  // 6 parts only: no
  W({ make: 'Honda', model: 'Civic', yrMin: null, yrMax: null, addedAt: '2026-11-08T00:00:00.000Z~a8' }), // 7 file missing: empty
];
const STORED = JSON.stringify(WATCHES);

const browser = await chromium.launch();
try {
  for (const width of [390, 320]) {
    const ctx = await browser.newContext({ viewport: { width, height: 844 }, serviceWorkers: 'block' });
    const page = await ctx.newPage();
    const arrivals = [];
    await page.route('**/*', async (route) => {
      const u = new URL(route.request().url());
      const a = u.pathname.match(/\/data\/arrivals\/([^/?]+\.json)$/);
      if (u.hostname === 'yardscout.io' && a) {
        arrivals.push(a[1]);
        const body = a[1] === 'index.json' ? INDEX : a[1] === 'toyota.json' ? TOYOTA : null;
        return body ? route.fulfill({ json: body }) : route.fulfill({ status: 404, body: '' });
      }
      if (u.hostname === 'yardscout.io' && u.pathname === '/geo') return route.fulfill({ json: { ok: false } });
      if (/api\.zippopotam\.us/.test(u.href)) return route.fulfill({ json: { places: [{ latitude: String(C.lat), longitude: String(C.lng) }] }, headers: { 'access-control-allow-origin': '*' } });
      if (u.hostname === 'yardscout.io') {
        const f = fileFor(u.pathname);
        return f ? route.fulfill({ path: f, contentType: TYPES[path.extname(f)] || 'application/octet-stream' }) : route.fulfill({ status: 404, body: '' });
      }
      return route.abort();
    });
    await page.addInitScript(({ stored }) => {
      navigator.sendBeacon = () => true;
      if (!sessionStorage.getItem('__seeded')) {
        localStorage.setItem('jh_honesty_ack', '1');
        localStorage.setItem('jh_zip', '95112');
        localStorage.setItem('yardscout_watchlist', stored);
        sessionStorage.setItem('__seeded', '1');
      }
    }, { stored: STORED });
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e.message).slice(0, 200)));
    await page.goto('https://yardscout.io/', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof liveLoaded !== 'undefined' && liveLoaded, null, { timeout: 120000 });
    await page.evaluate(() => { window.__ev = []; window.sendEvent = (e) => window.__ev.push(e); });
    const before = await page.evaluate(() => localStorage.getItem('yardscout_watchlist'));
    await page.click(".tab[data-tab='alerts']");
    await page.waitForSelector('#tab-alerts.active');
    await page.waitForFunction(() => document.querySelector('#alert-watchlist .watch-forecast .ysf'), null, { timeout: 30000 }).catch(() => {});
    // several re-renders (a scan, a sync): the files load once
    await page.evaluate(() => { renderAlerts(); renderAlerts(); renderAlerts(); });
    await page.waitForTimeout(600);
    const r = await page.evaluate(() => {
      const rows = [...document.querySelectorAll('#alert-watchlist .watchlist-item')];
      return rows.map((row) => {
        const m = row.querySelector('.watch-forecast');
        return { name: row.querySelector('.wl-name').textContent, mount: !!m, html: m ? m.innerHTML : '', h: m ? m.getBoundingClientRect().height : 0,
          text: m ? m.textContent.replace(/\s+/g, ' ').trim() : '' };
      });
    });
    const after = await page.evaluate(() => localStorage.getItem('yardscout_watchlist'));
    const tag = `${width}px`;
    check(`${tag}: eight watch rows rendered`, r.length === 8, JSON.stringify(r.map(x => x.name)));
    check(`${tag}: plain 4Runner watch shows the compact forecast`, r[0] && r[0].mount && /class="ysf ysf-compact"/.test(r[0].html) && r[0].h > 0, JSON.stringify(r[0]));
    // Fixture within 100 mi of 95112: San Jose and Oakland (Reno is ~190 mi);
    // 2003-2009 4Runners there: 6 + 4 = 10 in 8 weeks at 2 yards.
    check(`${tag}: its words: subject, the module's headline, facts and label`,
      /2003-2009 4Runner/.test(r[0].text) && /within 100 mi/.test(r[0].text) && /in the last 8 weeks at 2 yards/.test(r[0].text)
      && /From set-out dates YardScout has recorded\. Past weeks, not a promise\./.test(r[0].text) && !/Most land at/.test(r[0].text) && !/alerts/.test(r[0].text), r[0].text);
    for (const [i, why] of [[1, 'trim'], [2, 'drive'], [3, 'make only'], [4, 'no centre'], [5, 'anywhere'], [6, 'Parts only']]) {
      check(`${tag}: ${why} watch shows nothing (no mount point)`, r[i] && !r[i].mount, JSON.stringify(r[i]));
    }
    check(`${tag}: a make with no file renders nothing, takes no space`, r[7] && r[7].mount && r[7].html === '' && r[7].h === 0, JSON.stringify(r[7]));
    check(`${tag}: index and toyota.json fetched once over four renders`, arrivals.filter(a => a === 'index.json').length === 1 && arrivals.filter(a => a === 'toyota.json').length === 1, JSON.stringify(arrivals));
    check(`${tag}: rule 6, the stored watch list is byte-for-byte unchanged`, before === STORED && after === STORED, `${before === STORED} ${after === STORED}`);
    const ev = await page.evaluate(() => window.__ev.filter(e => e.startsWith('watch-forecast/')));
    check(`${tag}: watch-forecast/shown counted once`, JSON.stringify(ev) === '["watch-forecast/shown"]', JSON.stringify(ev));
    const wide = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    check(`${tag}: no horizontal overflow`, wide <= 0, String(wide));
    check(`${tag}: no page error`, !errors.length, errors.join(' | '));
    await ctx.close();
  }
} finally {
  await browser.close();
}
console.log(failures ? `${failures} FAILURE(S), ${passes} passed` : `ALL PASS (${passes})`);
process.exit(failures ? 1 : 0);
