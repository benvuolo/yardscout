/* Browser e2e: the mobile-web store banner stays compact (hub 2026-11-09:
 * live jh-v167 showed a ~285px card covering 30% of Cars and the map sheet).
 * With ?appbanner=ios and ?appbanner=android at 320/390/768px, light and dark,
 * 100% and 200% text, asserts:
 *  - at 100% text the banner is one compact row: at most 72px tall;
 *    at 200% text it takes at most a quarter of the screen;
 *  - the ✕ sits in the banner's top-right corner and is at least 44px;
 *  - the button names the store (link to it, label says which store);
 *  - it is hidden while the Yards map view is open and back on the list;
 *  - ✕ dismisses it and the dismissal sticks across a reload.
 * 200% text doubles the root size (rem-based type and spacing).
 * Run: node backend/test/app_promo_e2e.mjs   (Playwright pre-installed). */
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

let checks = 0; const fails = [];
const ok = (cond, msg) => { checks++; if (!cond) fails.push(msg); };
const browser = await chromium.launch();
try {
  for (const plat of ['ios', 'android']) {
    for (const width of [320, 390, 768]) {
      for (const theme of ['light', 'dark']) {
        for (const big of [false, true]) {
          const cfg = `${plat}/${width}/${theme}/${big ? '200%' : '100%'}`;
          const page = await browser.newPage({ viewport: { width, height: width >= 768 ? 1024 : 700 }, colorScheme: theme, hasTouch: true, isMobile: width < 768,
            userAgent: plat === 'ios' ? 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
              : 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36' });
          await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, r => r.abort());
          await page.addInitScript(() => {
            localStorage.setItem('jh_honesty_ack', '1'); localStorage.setItem('jh_zip', '84401');
            localStorage.setItem('jh_zip_coords', JSON.stringify({ '84401': { lat: 41.223, lng: -111.973 } }));
          });
          await page.goto(BASE + '?appbanner=' + plat, { waitUntil: 'domcontentloaded' });
          await page.waitForSelector('#live-grid .car-card', { timeout: 120000 }).catch(() => {});
          if (big) await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
          await page.waitForTimeout(300);
          const m = await page.evaluate(() => {
            const el = document.getElementById('app-promo'), b = el.getBoundingClientRect();
            const x = document.getElementById('app-promo-close').getBoundingClientRect();
            const a = document.getElementById('app-promo-link');
            return { shown: getComputedStyle(el).display !== 'none', h: b.height, vh: innerHeight, right: b.right - x.right, top: x.top - b.top, xw: x.width, xh: x.height,
              href: a.href, label: a.getAttribute('aria-label') || '', text: a.textContent, title: el.querySelector('strong').textContent };
          });
          ok(m.shown, `${cfg}: banner not shown`);
          if (big) ok(m.h <= m.vh / 4, `${cfg}: banner ${Math.round(m.h)}px is over a quarter of the screen`);
          else ok(m.h <= 72, `${cfg}: banner ${Math.round(m.h)}px tall (max 72)`);
          ok(m.right <= 4 && m.top <= 12, `${cfg}: ✕ not in the top-right corner (${Math.round(m.right)}px from right, ${Math.round(m.top)}px from top)`);
          ok(m.xw >= 44 && m.xh >= 44, `${cfg}: ✕ target ${Math.round(m.xw)}×${Math.round(m.xh)}`);
          ok(plat === 'ios' ? /apps\.apple\.com/.test(m.href) && /App Store/.test(m.label) && /iPhone/.test(m.title)
            : /play\.google\.com/.test(m.href) && /Google Play/.test(m.label) && /Android/.test(m.title), `${cfg}: wrong store (${m.href} / ${m.label} / ${m.title})`);
          const onMap = await page.evaluate(() => { document.querySelector('.tab[data-tab="yards"]').click(); setYardsView('map'); return getComputedStyle(document.getElementById('app-promo')).display; });
          ok(onMap === 'none', `${cfg}: banner shown over the map view`);
          const onList = await page.evaluate(() => { setYardsView('list'); return getComputedStyle(document.getElementById('app-promo')).display; });
          ok(onList !== 'none', `${cfg}: banner not back on the yards list`);
          if (!big && theme === 'light' && width === 390) {
            await page.evaluate(() => { document.querySelector('.tab[data-tab="live"]').click(); });
            await page.click('#app-promo-close');
            ok(await page.evaluate(() => getComputedStyle(document.getElementById('app-promo')).display === 'none' && localStorage.getItem('ys_app_promo') === '1'), `${cfg}: ✕ did not dismiss`);
            await page.goto(BASE, { waitUntil: 'domcontentloaded' });   // a real phone visit, no test hook
            await page.waitForTimeout(500);
            ok(await page.evaluate(() => getComputedStyle(document.getElementById('app-promo')).display === 'none'), `${cfg}: dismissed banner came back without the test hook`);
          }
          if (!big && theme === 'dark' && width === 320) {
            await page.evaluate(() => localStorage.removeItem('ys_app_promo'));
            await page.goto(BASE, { waitUntil: 'domcontentloaded' });
            await page.waitForTimeout(500);
            ok(await page.evaluate(() => getComputedStyle(document.getElementById('app-promo')).display !== 'none'), `${cfg}: a phone visit without the hook shows no banner`);
          }
          await page.close();
        }
      }
    }
  }
} finally {
  await browser.close();
  server.close();
}
fails.forEach(f => console.log('FAIL  ' + f));
console.log(`\n${checks} checks; ${fails.length} failed`);
console.log(fails.length ? 'FAILED' : 'ALL PASS');
process.exit(fails.length ? 1 : 0);
