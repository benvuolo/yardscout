/* Browser e2e: the Cars tab as a feed (ops/design.md, 2026-11-16, owner:
 * "intuitive, shareable, easy to scroll, Facebook Marketplace level
 * addicting"). Items 1 to 11 of the build brief:
 *   1  tiles: at 390x844 and 360x800, zip set and the first-run note
 *      acknowledged, at least four tiles fully on the first screen above the
 *      tab bar; about five columns at 1280; car-card + data-vkey kept
 *   2  a tile opens the car screen with every block the big card had, plus
 *      "More <make model> near you"; closing returns to the same scroll
 *      offset; the car screen's photo opens the viewer, a tile's opens the car
 *   3  bookmark (pull sheet) and share on every tile, 44 px, top corners
 *   4  one summary line; "updated" visible at 320; national numbers, never 0,
 *      with no location
 *   5  chips: All / New / This week / makes / models, in sync with Filters
 *      and the search box both ways; narrow/chip counted once a day
 *   6  endless scroll: 40 tiles, more near the bottom, the cap line
 *   7  "N set out near you since your last visit (date)" with a faked
 *      earlier visit day, Show just those, the divider, held for the session
 *   8  share a one-model list: /landed/<make>/<model> when the site has the
 *      page, else the tagged #cars= link
 *   9  first visit: "How to read this" after the first row of tiles on a phone
 *   10 the app banner waits for the third row (or 30 s) on a first visit
 *   11 the watch strip's one-step Monday email: one watch + one sign-up with
 *      the right body; the limit sends nothing; confirmed = Add; Pro and the
 *      app shells keep today's strip; the toast does not ask again
 * Offline: serves docs/ on 127.0.0.1 (also answers https://yardscout.io/ from
 * disk for the app-shell page), blocks every other host, answers the API's
 * /v1/recap/* POSTs itself. Images from the yards are answered with a 1x1
 * PNG so photo boxes behave as loaded.
 *   node backend/test/cars_feed_e2e.mjs */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const DOCS = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../docs');
const T = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2', '.webp': 'image/webp', '.webmanifest': 'application/manifest+json' };
const fileFor = (pathname) => {
  let p = decodeURIComponent(pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(DOCS, path.normalize(p));
  return f.startsWith(DOCS) && fs.existsSync(f) && !fs.statSync(f).isDirectory() ? f : null;
};
const srv = http.createServer((q, r) => {
  const f = fileFor(new URL(q.url, 'http://x').pathname);
  if (!f) { r.writeHead(404); r.end(); return; }
  r.writeHead(200, { 'content-type': T[path.extname(f)] || 'application/octet-stream' });
  fs.createReadStream(f).pipe(r);
});
await new Promise((res) => srv.listen(0, '127.0.0.1', res));
const BASE = `http://127.0.0.1:${srv.address().port}/`;
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');
const WL = 'yardscout_watchlist';
const SUB = Buffer.from('visitor@example.com').toString('base64url') + '.' + 'a'.repeat(64);

let pass = 0, fail = 0;
const ok = (c, msg, extra) => { if (c) { pass++; console.log('  ok   ' + msg); } else { fail++; console.log('  FAIL ' + msg + (extra !== undefined ? '  -> ' + String(typeof extra === 'string' ? extra : JSON.stringify(extra)).slice(0, 400) : '')); } };
const daysAgo = (n) => { const d = new Date(); d.setDate(d.getDate() - n); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; };

const browser = await chromium.launch();
async function open({ w = 390, h = 844, storage = {}, zip = true, ack = true, qs = '', native = null, origin = BASE, mobile = w < 700 } = {}) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, isMobile: mobile, hasTouch: mobile, deviceScaleFactor: 1, serviceWorkers: 'block' });
  await ctx.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: origin.replace(/\/$/, '') }).catch(() => {});
  const page = await ctx.newPage();
  const posts = [];
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e.message || e).slice(0, 200)));
  await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, async (route) => {
    const q = route.request();
    const u = new URL(q.url());
    if (u.hostname === 'api.test' && u.pathname.startsWith('/v1/recap/')) {
      const cors = { 'access-control-allow-origin': '*', 'access-control-allow-headers': 'content-type', 'access-control-allow-methods': 'POST' };
      if (q.method() === 'OPTIONS') return route.fulfill({ status: 204, headers: cors });
      posts.push({ path: u.pathname, body: JSON.parse(q.postData() || '{}') });
      return route.fulfill({ status: 200, json: { ok: true, state: u.pathname.endsWith('/add') ? 'added' : 'confirm-sent' }, headers: cors });
    }
    if (q.method() === 'POST') { posts.push({ path: u.hostname + u.pathname, body: q.postData() }); return route.abort(); }
    if (u.hostname === 'yardscout.io') {
      const f = fileFor(u.pathname);
      if (f) return route.fulfill({ path: f, contentType: T[path.extname(f)] || 'application/octet-stream', headers: { 'access-control-allow-origin': '*' } });
      return route.fulfill({ status: 404, body: '' });
    }
    if (q.resourceType() === 'image') return route.fulfill({ status: 200, contentType: 'image/png', body: PNG });
    return route.abort();
  });
  await page.addInitScript(({ storage, zip, ack, native }) => {
    if (sessionStorage.getItem('__seeded')) return;
    sessionStorage.setItem('__seeded', '1');
    if (ack) localStorage.setItem('jh_honesty_ack', '1');
    if (zip) {
      localStorage.setItem('jh_zip', '95112');
      localStorage.setItem('jh_zip_coords', JSON.stringify({ '95112': { lat: 37.3485, lng: -121.8863 } }));
      localStorage.setItem('jh_radius', '100');
    }
    for (const [k, v] of Object.entries(storage)) localStorage.setItem(k, v);
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
  }, { storage, zip, ack, native });
  await page.addInitScript(() => { window.__YS_RECAP_API = 'https://api.test'; window.__shared = []; });
  await page.goto(origin + qs, { waitUntil: 'domcontentloaded' });
  // The whole scan arrives on the web with a location; the app shells and a
  // visitor with no location stop at the first view.
  await page.waitForFunction((zip) => typeof liveLoaded !== 'undefined' && liveLoaded && !(typeof _inv !== 'undefined' && _inv && !liveComplete && invViewPending())
    && (liveComplete || !zip || (window.Capacitor && document.querySelector('#live-grid .car-card'))), zip, { timeout: 180000 });
  await page.waitForTimeout(600);
  // Record what the app counts (analytics are off on 127.0.0.1; track is the one door).
  await page.evaluate(() => { window.__tracked = []; window.track = (e) => { window.__tracked.push(String(e)); }; });
  return { ctx, page, posts, errors };
}
const tracked = (page) => page.evaluate(() => window.__tracked.slice());
const tileCount = (page) => page.evaluate(() => document.querySelectorAll('#live-grid > .car-tile').length);

try {
  /* ---------- 1. tiles: four on the first phone screen ---------- */
  console.log('1. Tiles');
  for (const [w, h] of [[390, 844], [360, 800]]) {
    const { page, ctx, errors } = await open({ w, h });
    const m = await page.evaluate(() => {
      const tb = document.querySelector('.tabs').getBoundingClientRect();
      const bottom = tb.top > innerHeight / 2 ? tb.top : innerHeight;
      const tiles = [...document.querySelectorAll('#live-grid > .car-tile')];
      const full = tiles.filter(t => { const r = t.getBoundingClientRect(); return r.top >= 0 && r.bottom <= bottom + 0.5; });
      const cols = getComputedStyle(document.getElementById('live-grid')).gridTemplateColumns.split(' ').filter(Boolean).length;
      const t = tiles[0];
      return { full: full.length, cols, bottom, hooks: tiles.every(x => x.classList.contains('car-card') && x.dataset.vkey),
        text: t.innerText.replace(/\s+/g, ' '), ell: tiles.slice(0, 8).some(x => [...x.querySelectorAll('*')].some(e => getComputedStyle(e).textOverflow === 'ellipsis' || (getComputedStyle(e).webkitLineClamp || 'none') !== 'none')),
        hscroll: document.documentElement.scrollWidth > innerWidth };
    });
    ok(m.full >= 4, `${w}x${h}: at least four tiles fully on the first screen above the tab bar (${m.full})`, m);
    ok(m.cols === 2, `${w}x${h}: two columns`, m.cols);
    ok(m.hooks, `${w}x${h}: every tile keeps class car-card and data-vkey`);
    ok(/\d{4} \S+/.test(m.text) && / mi\b/.test(m.text) && /Row|No row yet/.test(m.text) && /Set out|Set-out date unknown/.test(m.text), `${w}x${h}: a tile has the name, yard + distance, row and set-out date`, m.text);
    ok(!m.ell && !m.hscroll, `${w}x${h}: no ellipsis or line clamp on tiles, no sideways page scroll`);
    ok(!errors.length, `${w}x${h}: no page errors`, errors);
    await ctx.close();
  }
  {
    const { page, ctx } = await open({ w: 1280, h: 900 });
    const cols = await page.evaluate(() => getComputedStyle(document.getElementById('live-grid')).gridTemplateColumns.split(' ').filter(Boolean).length);
    ok(cols === 5, `1280: five columns (${cols})`);
    await ctx.close();
  }

  /* ---------- 2-6, 8, 11 on one phone page ---------- */
  const P = await open({ w: 390, h: 844, storage: { [WL]: JSON.stringify([{ make: 'Honda', model: 'Civic', yrMin: null, yrMax: null, matchOnly: true, radiusMi: 100, lat: 37.35, lng: -121.89, driveFilter: '', trimFilter: 'Si', addedAt: '2026-10-02T10:00:00.000Z~abc123' }]) } });
  const page = P.page;
  const OLD_WL = await page.evaluate((k) => localStorage.getItem(k), WL);

  console.log('2. The car screen from a tile');
  {
    // A car with parts, a published lifespan and a sibling of the same model in range.
    const key = await page.evaluate(() => {
      const tiles = [...document.querySelectorAll('#live-grid > .car-tile')].map(t => liveInventory.find(v => vehicleKey(v) === t.dataset.vkey));
      const good = tiles.find(v => v && v.hasMatch && v.topParts && v.topParts.length && vehicleKey(v) !== lastSampleKey && carLotClock(v).avg && moreLikeThisCars(v).length);
      return good ? vehicleKey(good) : null;
    });
    ok(!!key, 'found a tile with parts, a typical stay and more of its model');
    await page.evaluate((k) => { const t = document.querySelector(`#live-grid > .car-tile[data-vkey="${CSS.escape(k)}"]`); window.scrollTo(0, window.scrollY + t.getBoundingClientRect().top - 200); }, key);
    const y0 = await page.evaluate(() => Math.round(window.scrollY));
    await page.click(`#live-grid > .car-tile[data-vkey="${key}"] .tile-open`);
    await page.waitForSelector('#car-detail.open', { timeout: 5000 });
    const d = await page.evaluate(() => {
      const b = document.getElementById('car-detail-body'), a = document.getElementById('car-detail-actions');
      const more = b.querySelector('.cd-more');
      const v = liveInventory.find(x => vehicleKey(x) === carDetailKey);
      return {
        row: !!b.querySelector('.locator .row-plate-lg'), yard: b.querySelector('.locator h3').textContent.includes(v.location),
        dist: /\d\smi from 95112/.test(b.querySelector('.locator').textContent),
        hours: (b.querySelector('.cd-hours') || {}).href || '', hoursText: (b.querySelector('.cd-hours') || {}).textContent || '',
        setOut: /Set out|Set-out date unknown/.test(b.querySelector('.eyebrow').textContent),
        stay: !!b.querySelector('.cd-stay .stay-meter') && /typical/.test(b.querySelector('.cd-stay').textContent),
        spec: !!extrasFor(v) ? !!b.querySelector('.cd-spec') : true,
        valueBox: !!b.querySelector('.cd-value .pro-box') && /card-value/.test(b.querySelector('.cd-value .pro-box').getAttribute('onclick')),
        partsLine: /parts? to check/.test((b.querySelector('.cd-parts-summary') || {}).textContent || ''),
        pull: /Add to pull sheet|On pull sheet/.test(a.querySelector('.pull-btn').textContent), share: !!a.querySelector('.share-btn'), watch: !!a.querySelector('.watch-btn'),
        moreHead: more ? more.querySelector('h3').textContent : '', moreTiles: more ? [...more.querySelectorAll('.car-tile')].map(t => { const x = liveInventory.find(y => vehicleKey(y) === t.dataset.vkey); return x && x.make === v.make && canonicalModel(x.make, x.model) === canonicalModel(v.make, v.model) && vehicleKey(x) !== vehicleKey(v); }) : [],
        name: `${v.make} ${canonicalModel(v.make, v.model)}`,
      };
    });
    ok(d.row && d.yard && d.dist, 'car screen: row, yard and distance', d);
    ok(/\/maps\/search\/\?api=1&query=/.test(d.hours) && /Hours and directions/.test(d.hoursText), 'car screen: the hours-and-directions link', d.hours);
    ok(d.setOut && d.stay && d.spec, 'car screen: set-out date, typical stay with its bar, colour/engine line', d);
    ok(d.valueBox, 'car screen (free): the card\'s Pro value box, gate name card-value');
    ok(d.partsLine, 'car screen: the "parts to check" line');
    ok(d.pull && d.share && d.watch, 'car screen: add to pull sheet, share, watch this model');
    ok(d.moreHead === `More ${d.name} near you` && d.moreTiles.length >= 1 && d.moreTiles.length <= 6 && d.moreTiles.every(Boolean), `car screen: "More ${d.name} near you" with up to six of the same model`, d);
    // A "more" tile opens that car in place.
    const k2 = await page.evaluate(() => document.querySelector('#car-detail .cd-more .car-tile').dataset.vkey);
    await page.click('#car-detail .cd-more .car-tile .tile-open');
    await page.waitForTimeout(300);
    ok(await page.evaluate((k) => carDetailKey === k && document.querySelector('#car-detail.open') !== null, k2), 'a "More" tile opens that car on the car screen');
    // The car screen's photo opens the viewer (when the car has one).
    const ph = await page.evaluate(() => {
      const v = liveInventory.find(x => { const ex = extrasFor(x); const i = ex && ex[extraIdx.photo] ? photoInfo(ex[extraIdx.photo]) : null; return i && !i.heavy && i.inList && moreLikeThisCars(x).length !== undefined; });
      return v ? vehicleKey(v) : null;
    });
    if (ph) {
      await page.evaluate((k) => openCarDetail(k), ph);
      await page.waitForTimeout(400);
      await page.click('#car-detail .cd-photo');
      await page.waitForTimeout(300);
      ok(await page.evaluate(() => !!document.querySelector('#photo-viewer.open')), 'the car screen\'s photo still opens the photo viewer');
      await page.evaluate(() => closePhotoViewer());
      await page.waitForTimeout(300);
    } else ok(true, '(no car with a list photo in the data: viewer check skipped)');
    await page.evaluate(() => closeCarDetail());
    await page.waitForTimeout(400);
    const y1 = await page.evaluate(() => Math.round(window.scrollY));
    ok(Math.abs(y1 - y0) <= 2, `closing the car screen returns to the same place in the list (${y0} -> ${y1})`);
    // A tile's photo opens the car screen, not the viewer.
    const tp = await page.evaluate(() => { const t = [...document.querySelectorAll('#live-grid > .car-tile')].find(x => x.querySelector('.photo-box[data-photo-vkey]')); if (!t) return null; t.scrollIntoView({ block: 'center' }); return t.dataset.vkey; });
    if (tp) {
      await page.click(`#live-grid > .car-tile[data-vkey="${tp}"] .photo-box`);
      await page.waitForTimeout(300);
      ok(await page.evaluate((k) => carDetailKey === k && !document.querySelector('#photo-viewer.open'), tp), 'a tile\'s photo opens the car screen (the viewer is on the car screen)');
      await page.evaluate(() => closeCarDetail());
      await page.waitForTimeout(300);
    } else ok(true, '(no tile with a photo on screen: tile-photo check skipped)');
    // The free sample car: its values are on the car screen.
    const sk = await page.evaluate(() => lastSampleKey);
    if (sk) {
      ok(await page.evaluate((k) => /Free Pro look/.test(document.querySelector(`#live-grid > .car-tile[data-vkey="${CSS.escape(k)}"]`).textContent), sk), 'the free sample car\'s tile is badged');
      await page.evaluate((k) => openCarDetail(k), sk);
      await page.waitForTimeout(300);
      ok(await page.evaluate(() => !!document.querySelector('#car-detail .cd-allvalue') && !!document.querySelector('#car-detail .sample-pitch') && !document.querySelector('#car-detail .cd-value')), 'the free sample car shows its unlocked values on the car screen');
      await page.evaluate(() => closeCarDetail());
      await page.waitForTimeout(300);
    }
  }

  console.log('3. Bookmark and share on every tile');
  {
    const c = await page.evaluate(() => [...document.querySelectorAll('#live-grid > .car-tile')].map(t => {
      const m = t.querySelector('.tile-media').getBoundingClientRect(), s = t.querySelector('.tile-share').getBoundingClientRect(), b = t.querySelector('.tile-save').getBoundingClientRect();
      return s.width >= 43.5 && s.height >= 43.5 && b.width >= 43.5 && b.height >= 43.5 && s.left - m.left <= 1 && m.right - b.right <= 1 && s.top - m.top <= 1 && b.top - m.top <= 1 && s.right <= b.left && s.bottom <= m.top + m.height / 2 + 1;
    }));
    ok(c.length && c.every(Boolean), 'every tile: share and bookmark, 44 px, each in a top corner of the picture');
    await page.evaluate(() => window.scrollTo(0, 0));
    const k = await page.evaluate(() => document.querySelector('#live-grid > .car-tile .tile-save').dataset.vkey);
    await page.tap('#live-grid > .car-tile .tile-save');
    await page.waitForTimeout(200);
    ok(await page.evaluate((k) => !!JSON.parse(localStorage.getItem('jh_saved') || '{}')[k] && !document.querySelector('#car-detail.open'), k), 'the bookmark adds to the pull sheet and opens nothing');
    await page.tap('#live-grid > .car-tile .tile-save');
    await page.waitForTimeout(200);
    ok(await page.evaluate((k) => !JSON.parse(localStorage.getItem('jh_saved') || '{}')[k], k), '…and a second tap takes it off');
    await page.evaluate(() => { navigator.share = async (d) => { window.__shared.push(d); }; });
    await page.tap('#live-grid > .car-tile .tile-share');
    await page.waitForTimeout(300);
    const sh = await page.evaluate(() => window.__shared.slice());
    ok(sh.length === 1 && sh[0].url === 'https://yardscout.io/car/' + encodeURIComponent(k), 'the tile\'s share sends the car\'s link (shareVehicle)', sh);
  }

  console.log('4. Summary line');
  {
    const s = await page.evaluate(() => ({ html: document.getElementById('live-stats-bar').innerHTML, text: document.getElementById('live-stats-bar').innerText.replace(/\s+/g, ' '), tiles: document.querySelectorAll('#live-stats-bar .stat-card').length, n: getFilteredLive().length }));
    ok(s.tiles === 0 && new RegExp(`${s.n.toLocaleString('en-US')} cars near you · [\\d,]+ new this week · updated `).test(s.text), 'one line: cars near you · new this week · updated', s.text);
  }

  console.log('5. Chips');
  {
    await page.evaluate(() => { window.__tracked.length = 0; window.scrollTo(0, 0); });
    const before = await page.evaluate(() => ({ chips: [...document.querySelectorAll('#feed-chips .fchip')].map(c => c.textContent.trim()), all: document.querySelector('#feed-chips [data-chip="all"]').getAttribute('aria-pressed'),
      sw: document.getElementById('feed-chips').scrollWidth, cw: document.getElementById('feed-chips').clientWidth, page: document.documentElement.scrollWidth <= innerWidth }));
    ok(before.chips[0] === 'All' && before.chips[1] === 'New' && before.chips[2] === 'This week' && before.all === 'true', 'chips: All (on), New, This week first', before.chips);
    ok(before.sw > before.cw && before.page, 'the chip row scrolls sideways; the page does not');
    const topMakes = await page.evaluate(() => {
      const c = new Map(); for (const v of _scopedVehicles) if (v.make && !JUNK_MAKES.has(v.make.toLowerCase())) c.set(v.make, (c.get(v.make) || 0) + 1);
      return [...c.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, 10).map(e => e[0]);
    });
    ok(JSON.stringify(before.chips.slice(3)) === JSON.stringify(topMakes), 'then the makes with the most cars in range, most first', before.chips.slice(3));
    // A make chip = Filters Make + search box; its models appear.
    await page.click('#feed-chips .fchip[data-chip="make"][data-make="Nissan"]');
    await page.waitForTimeout(300);
    const mk = await page.evaluate(() => ({ make: document.getElementById('live-filter-make').value, box: document.getElementById('car-search-input').value, badge: document.getElementById('live-filter-count').textContent,
      chips: [...document.querySelectorAll('#feed-chips .fchip[data-chip="model"]')].map(c => c.dataset.model), on: document.querySelector('#feed-chips .fchip-make').getAttribute('aria-pressed'),
      notNissan: getFilteredLive().filter(v => v.make !== 'Nissan').length }));
    ok(mk.make === 'Nissan' && mk.box === 'Nissan' && mk.badge === '1' && mk.notNissan === 0, 'a make chip sets Filters -> Make and the search box', mk);
    ok(mk.on === 'true' && mk.chips.includes('Xterra') && mk.chips.length > 3, 'the chosen make shows its models as chips', mk.chips.slice(0, 8));
    await page.click('#feed-chips .fchip[data-chip="model"][data-model="Xterra"]');
    await page.waitForTimeout(300);
    const md = await page.evaluate(() => ({ models: [...selectedModels], box: document.getElementById('car-search-input').value, btn: document.getElementById('live-filter-model-btn').textContent,
      on: document.querySelector('#feed-chips .fchip[data-model="Xterra"]').getAttribute('aria-pressed'), other: getFilteredLive().filter(v => canonicalModel(v.make, v.model) !== 'Xterra').length }));
    ok(md.models.join() === 'Xterra' && md.box === 'Nissan Xterra' && md.btn === 'Xterra' && md.on === 'true' && md.other === 0, 'a model chip = Filters -> Model and the box shows "Nissan Xterra"', md);
    ok(JSON.stringify((await tracked(page)).filter(e => e.startsWith('narrow/'))) === JSON.stringify(['narrow/chip']), 'chips count narrow/chip once a day (make then model = one count)', await tracked(page));
    // Filters -> chips: a make chosen in Filters shows pressed in the chip row.
    await page.click('#live-filter-toggle');
    await page.selectOption('#live-filter-make', 'Toyota');
    await page.waitForTimeout(300);
    ok(await page.evaluate(() => { const m = document.querySelector('#feed-chips .fchip-make'); return m && m.dataset.make === 'Toyota' && !document.querySelector('#feed-chips .fchip[data-model="Xterra"]'); }), 'Filters -> Make shows in the chips (both ways)');
    await page.click('#live-filter-toggle');
    // Search box -> chips.
    await page.click('#car-search-input');
    await page.fill('#car-search-input', '');
    await page.type('#car-search-input', 'civic', { delay: 15 });
    await page.waitForTimeout(200);
    await page.click('#car-search-suggest .compare-suggest-item >> nth=0');
    await page.waitForTimeout(300);
    ok(await page.evaluate(() => document.querySelector('#feed-chips .fchip-make').dataset.make === 'Honda' && document.querySelector('#feed-chips .fchip[data-model="Civic"]').getAttribute('aria-pressed') === 'true'), 'a search-box pick shows in the chips');
    // The make chip again: back to every make.
    await page.click('#feed-chips .fchip-make');
    await page.waitForTimeout(300);
    ok(await page.evaluate(() => !document.getElementById('live-filter-make').value && !selectedModels.size && document.querySelector('#feed-chips [data-chip="all"]').getAttribute('aria-pressed') === 'true'), 'tapping the chosen make clears it (All is on again)');
    // New = set out today or yesterday; This week = liveWeekOnly; All resets.
    await page.click('#feed-chips [data-chip="new"]');
    await page.waitForTimeout(300);
    const nw = await page.evaluate(() => { const l = getFilteredLive(); const y = new Date(); y.setHours(0, 0, 0, 0); y.setDate(y.getDate() - 1); return { n: l.length, bad: l.filter(v => !(parseYardDate(v.dateAdded) >= y)).length, on: liveNewOnly }; });
    ok(nw.on && nw.n > 0 && nw.bad === 0, 'New: only cars set out today or yesterday', nw);
    await page.click('#feed-chips [data-chip="week"]');
    await page.waitForTimeout(300);
    ok(await page.evaluate(() => liveWeekOnly && !liveNewOnly && getFilteredLive().every(v => isNew(v.dateAdded))), 'This week: the existing liveWeekOnly mode (and New off)');
    await page.click('#feed-chips [data-chip="all"]');
    await page.waitForTimeout(300);
    ok(await page.evaluate(() => !liveWeekOnly && !liveNewOnly && !document.getElementById('live-filter-make').value), 'All clears New / This week / make');
    ok((await tracked(page)).filter(e => e === 'narrow/chip').length === 1, 'All, New, This week and clearing a chip count nothing more', await tracked(page));
  }

  console.log('6. Endless scroll');
  {
    await page.evaluate(() => window.scrollTo(0, 0));
    const n0 = await tileCount(page);
    const total = await page.evaluate(() => getFilteredLive().length);
    ok(n0 === Math.min(40, total), `first batch: ${n0} tiles of ${total}`);
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);
    const n1 = await tileCount(page);
    ok(n1 > n0, `more tiles load as the bottom nears (${n0} -> ${n1})`);
    await page.evaluate(() => renderLive());
    ok(await tileCount(page) === n1, 're-rendering the same list keeps what was shown');
    for (let i = 0; i < 60 && (await page.evaluate(() => !!document.getElementById('feed-more'))); i++) {
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(80);
    }
    const end = await page.evaluate(() => ({ n: document.querySelectorAll('#live-grid > .car-tile').length, line: (document.querySelector('#live-grid .feed-end') || {}).textContent || '', total: getFilteredLive().length }));
    ok(end.total > 1200 ? (end.n === 1200 && /Showing the first 1,200 of [\d,]+ cars/.test(end.line)) : end.n === end.total, 'the cap: 1,200 tiles and a plain line', end);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(200);
  }

  console.log('8. Share a list');
  {
    await page.evaluate(() => { carSearchSetFilter('Nissan', 'Xterra'); renderLive(); window.__shared.length = 0; });
    await page.waitForTimeout(400);
    const row = await page.evaluate(() => { const b = document.querySelector('#live-grid .list-share-btn'); return b ? { n: +b.dataset.n, text: b.parentElement.textContent.replace(/\s+/g, ' '), f: getFilteredLive().length } : null; });
    ok(row && row.n === row.f && /Nissan Xterra within 100/.test(row.text), 'one model: a Share this list row with the count', row);
    await page.tap('#live-grid .list-share-btn');
    await page.waitForTimeout(400);
    const sh = await page.evaluate(() => window.__shared.slice());
    ok(sh.length === 1 && sh[0].url === 'https://yardscout.io/landed/nissan/xterra' && sh[0].text.includes('Nissan Xterra') && sh[0].text.includes(String(row.n)), 'a model with a public page shares /landed/nissan/xterra, naming the model and the count', sh);
    const other = await page.evaluate(async () => {
      const idx = await landedIndexLoad();
      const pages = new Set(Object.entries(idx.makes).flatMap(([mk, e]) => e.models.map(m => mk + '|' + m[0])));
      const c = new Map(); for (const v of _scopedVehicles) { const m = canonicalModel(v.make, v.model); if (v.make && m && !isNoPickModel(v.make, v.model) && !pages.has(v.make + '|' + m)) c.set(v.make + '|' + m, (c.get(v.make + '|' + m) || 0) + 1); }
      const k = [...c.keys()][0]; if (!k) return null;
      const [mk, md] = k.split('|');
      if (!carSearchSetFilter(mk, md)) return null;
      renderLive(); window.__shared.length = 0; return { mk, md };
    });
    if (other) {
      await page.waitForTimeout(300);
      await page.tap('#live-grid .list-share-btn');
      await page.waitForTimeout(400);
      const s2 = await page.evaluate(() => window.__shared.slice());
      ok(s2.length === 1 && s2[0].url === `https://yardscout.io/?utm_source=share&utm_medium=list#cars=${encodeURIComponent(other.mk)}|${encodeURIComponent(other.md)}`, `a model without a page (${other.mk} ${other.md}) shares the tagged #cars= link`, s2);
    } else ok(false, 'found a model in range without a public page');
    await page.evaluate(() => { carSearchSetFilter('', ''); renderLive(); });
  }

  console.log('11. The watch strip: one-step Monday email');
  {
    await page.evaluate(() => { window.__tracked.length = 0; carSearchSetFilter('Nissan', 'Xterra'); renderLive(); });
    await page.waitForTimeout(300);
    const st = await page.evaluate(() => { const s = document.querySelector('#live-grid .watch-strip'); return s ? { mail: s.classList.contains('strip-mail'), text: s.innerText.replace(/\s+/g, ' '), field: !!s.querySelector('input.mail-email'), btn: (s.querySelector('.mail-form .btn') || {}).textContent, just: !!s.querySelector('.strip-just-watch') } : null; });
    ok(st && st.mail && st.text.includes('Want the next one? Get a free Monday email with every Nissan Xterra set out within 100 mi.') && st.field && st.btn === 'Email me' && st.just, 'free web + location: the strip asks for the email, with "or just watch it here"', st);
    // (Counted when section 8 first showed the strip: once a visit.)
    await page.evaluate(() => renderLive());
    ok(await page.evaluate(() => _stripAskCounted) && !(await tracked(page)).includes('email-asked'), 'email-asked: counted once this visit, not again on a re-render', await tracked(page));
    // A bad address: nothing made, nothing sent.
    await page.fill('#live-grid .strip-mail .mail-email', 'not-an-address');
    await page.click('#live-grid .strip-mail .mail-form .btn');
    await page.waitForTimeout(300);
    ok(await page.evaluate((k) => localStorage.getItem(k), WL) === OLD_WL && P.posts.length === 0 && /Enter your email/.test(await page.evaluate(() => document.querySelector('#live-grid .strip-mail .mail-msg').textContent)), 'a bad address: no watch, no request, a message');
    await page.fill('#live-grid .strip-mail .mail-email', 'visitor@example.com');
    await page.click('#live-grid .strip-mail .mail-form .btn');
    await page.waitForTimeout(800);
    const wl = JSON.parse(await page.evaluate((k) => localStorage.getItem(k), WL));
    const neu = wl.slice(1);
    ok(neu.length === 1 && neu[0].make === 'Nissan' && neu[0].model === 'Xterra' && neu[0].radiusMi === 100 && !neu[0].yrMin, 'Email me made exactly one watch, Nissan Xterra within 100 mi', neu);
    ok(JSON.stringify(wl[0]) === JSON.stringify(JSON.parse(OLD_WL)[0]), 'the watch saved earlier is untouched (rule 6)');
    const sign = P.posts.filter(p => p.path === '/v1/recap/signup');
    const want = await page.evaluate((e) => recapWatchBody(e), neu[0]);
    ok(P.posts.length === 1 && sign.length === 1 && sign[0].body.email === 'visitor@example.com' && JSON.stringify(sign[0].body.watch) === JSON.stringify(want)
      && ['src', 'cmp', 'med'].every(k => k in sign[0].body), 'one sign-up request, with the watch body recapWatchBody makes and the attribution fields', P.posts);
    const done = await page.evaluate(() => ({ strip: document.querySelector('#live-grid .strip-mail').innerText.replace(/\s+/g, ' '), toast: !!document.querySelector('#watch-toast.show .mail-ask'), rs: JSON.parse(localStorage.getItem('ys_recap') || 'null') }));
    ok(/Check your inbox\./.test(done.strip) && /Watching Nissan Xterra/.test(done.strip) && done.rs && done.rs.state === 'pending', 'the strip says "Check your inbox" and that the car is watched', done);
    ok(!done.toast, 'no toast asks for the email again');
    ok((await tracked(page)).includes('email-submitted') && (await tracked(page)).includes('watch-created/strip'), 'counted: watch-created/strip and email-submitted', await tracked(page));
    // A later watch from a car screen: the toast does not ask about the strip's watch.
    await page.evaluate(() => renderLive());
    ok(await page.evaluate(() => /Watching Nissan Xterra/.test(document.querySelector('#live-grid .watch-strip').textContent) && !document.querySelector('#live-grid .strip-mail')), 'after a re-render the strip shows the watch as watched');
    ok(await page.evaluate(() => !recapAskEntries().some(e => e.make === 'Nissan' && e.model === 'Xterra')), 'the toast\'s queue does not hold the strip\'s watch');
    await page.evaluate(() => { carSearchSetFilter('', ''); renderLive(); });
  }
  ok(!P.errors.length, 'phone page: no page errors', P.errors);
  await P.ctx.close();

  console.log('11b. Limit, confirmed subscriber, "or just watch", Pro, app shell');
  {
    // The free limit: the upgrade sheet opens and nothing is sent.
    const five = JSON.stringify(['Ford|F-150', 'Toyota|Camry', 'Honda|Accord', 'Dodge|Ram 1500', 'Chevrolet|Impala'].map((p, i) => ({ make: p.split('|')[0], model: p.split('|')[1], yrMin: null, yrMax: null, matchOnly: false, radiusMi: 100, lat: 37.35, lng: -121.89, addedAt: `2026-10-0${i + 1}T10:00:00.000Z~x${i}` })));
    const L = await open({ storage: { [WL]: five } });
    await L.page.evaluate(() => { carSearchSetFilter('Nissan', 'Xterra'); renderLive(); });
    await L.page.waitForTimeout(300);
    await L.page.fill('#live-grid .strip-mail .mail-email', 'visitor@example.com');
    await L.page.click('#live-grid .strip-mail .mail-form .btn');
    await L.page.waitForTimeout(600);
    ok(await L.page.evaluate(() => !!document.querySelector('#upgrade-sheet.open')) && L.posts.length === 0 && (await L.page.evaluate((k) => localStorage.getItem(k), WL)) === five, 'over the free limit: the upgrade sheet, no watch, nothing sent', L.posts);
    await L.ctx.close();
    // Confirmed subscriber: "Add X to your free Monday email?" + Add.
    const C = await open({ storage: { ys_recap: JSON.stringify({ email: 'visitor@example.com', state: 'confirmed', sub: SUB }) } });
    await C.page.evaluate(() => { carSearchSetFilter('Nissan', 'Xterra'); renderLive(); window.__tracked.length = 0; });
    await C.page.waitForTimeout(300);
    const ct = await C.page.evaluate(() => (document.querySelector('#live-grid .strip-mail') || {}).innerText || '');
    ok(/Add Nissan Xterra to your free Monday email\?/.test(ct.replace(/\s+/g, ' ')) && await C.page.evaluate(() => !document.querySelector('#live-grid .strip-mail input')), 'confirmed subscriber: "Add Nissan Xterra to your free Monday email?" with Add, no field', ct);
    await C.page.click('#live-grid .strip-mail [data-act="recap-add"]');
    await C.page.waitForTimeout(600);
    const add = C.posts.filter(p => p.path === '/v1/recap/add');
    const cw = JSON.parse(await C.page.evaluate((k) => localStorage.getItem(k) || '[]', WL));
    ok(C.posts.length === 1 && add.length === 1 && add[0].body.sub === SUB && cw.length === 1 && cw[0].model === 'Xterra', 'Add: one watch and one /v1/recap/add with the subscription', C.posts);
    ok(!(await tracked(C.page)).includes('email-asked'), 'no field shown, no email-asked');
    await C.ctx.close();
    // "or just watch it here" = today's Watch button (the toast then offers the email).
    const J = await open();
    await J.page.evaluate(() => { carSearchSetFilter('Nissan', 'Xterra'); renderLive(); renderLive(); carSearchSetFilter('Nissan', 'Frontier'); renderLive(); carSearchSetFilter('Nissan', 'Xterra'); renderLive(); });
    await J.page.waitForTimeout(300);
    ok(JSON.stringify((await tracked(J.page)).filter(e => e === 'email-asked')) === JSON.stringify(['email-asked']), 'a fresh visit: the strip\'s field counts email-asked exactly once over several renders', await tracked(J.page));
    await J.page.click('#live-grid .strip-mail .strip-just-watch');
    await J.page.waitForTimeout(500);
    const jw = JSON.parse(await J.page.evaluate((k) => localStorage.getItem(k) || '[]', WL));
    ok(jw.length === 1 && jw[0].model === 'Xterra' && J.posts.length === 0 && await J.page.evaluate(() => !!document.querySelector('#watch-toast.show .mail-ask')), '"or just watch it here": the watch, then the toast\'s usual email offer; nothing sent', { jw, posts: J.posts });
    await J.ctx.close();
    // Pro: today's strip.
    const Pr = await open({ storage: { jh_pro: '1', jh_pro_source: 'account' } });
    await Pr.page.evaluate(() => { carSearchSetFilter('Nissan', 'Xterra'); renderLive(); });
    await Pr.page.waitForTimeout(300);
    ok(await Pr.page.evaluate(() => { const s = document.querySelector('#live-grid .watch-strip'); return !!s && !s.classList.contains('strip-mail') && /Get pinged when another/.test(s.textContent) && /Watch/.test(s.querySelector('.btn').textContent); }), 'Pro: today\'s strip (Watch button, no email field)');
    await Pr.ctx.close();
    // App shell (stubbed Capacitor, data answered from disk as yardscout.io).
    const N = await open({ native: 'ios' });
    await N.page.evaluate(() => { carSearchSetFilter('Nissan', 'Xterra'); renderLive(); });
    await N.page.waitForTimeout(300);
    ok(await N.page.evaluate(() => IS_NATIVE && (() => { const s = document.querySelector('#live-grid .watch-strip'); return !!s && !s.classList.contains('strip-mail') && !s.querySelector('input'); })()), 'app shell: today\'s strip, no email field');
    ok(N.posts.length === 0, 'app shell: nothing sent', N.posts);
    await N.ctx.close();
  }

  console.log('4b. No location: national numbers, never 0');
  {
    const Z = await open({ zip: false });
    const s = await Z.page.evaluate(() => document.getElementById('live-stats-bar').innerText.replace(/\s+/g, ' '));
    ok(/[\d,]{5,} cars on the lots/.test(s) && /updated/.test(s) && !/(^|\D)0 /.test(s), 'no location: the header\'s national numbers, no "0"', s);
    ok(await Z.page.evaluate(() => document.getElementById('feed-chips').hidden), 'no location (free): no chips over the zip card');
    await Z.ctx.close();
    const W = await open({ w: 320, h: 640 });
    const u = await W.page.evaluate(() => { const e = document.querySelector('#live-stats-bar .fs-upd'); const r = e.getBoundingClientRect(); return { r: r.right, l: r.left, w: innerWidth, h: r.height, page: document.documentElement.scrollWidth }; });
    ok(u.l >= 0 && u.r <= u.w && u.h > 0 && u.page <= u.w, '320 px: "updated" fully visible, no sideways scroll', u);
    await W.ctx.close();
  }

  console.log('7. Since your last visit');
  {
    const S = await open({ storage: { ys_last_visit_day: daysAgo(3) } });
    const ln = await S.page.evaluate(() => {
      const el = document.querySelector('#live-grid .since-line');
      const day = FEED_SINCE_DAY, all = getFilteredLive();
      const n = all.filter(v => setOutSince(v, day)).length;
      return { text: el ? el.textContent.replace(/\s+/g, ' ').trim() : '', n, day, stored: localStorage.getItem('ys_last_visit_day'), today: localDayStr(),
        undatedCounted: all.filter(v => !parseYardDate(v.dateAdded) && setOutSince(v, day)).length };
    });
    ok(ln.day === daysAgo(3) && ln.stored === ln.today, 'the last visit day is read, then today is remembered', ln);
    ok(ln.n > 0 && ln.text.startsWith(`${ln.n.toLocaleString('en-US')} set out near you since your last visit (`) && ln.undatedCounted === 0, `"${ln.text}"`, ln);
    // The divider in the default (newest-first) list where the new ones end.
    for (let i = 0; i < 40 && !(await S.page.evaluate(() => !!document.querySelector('#live-grid .feed-divider'))); i++) await S.page.evaluate(() => feedMore());
    const dv = await S.page.evaluate(() => {
      const kids = [...document.getElementById('live-grid').children];
      const i = kids.findIndex(k => k.classList.contains('feed-divider'));
      const before = kids.slice(0, i).filter(k => k.classList.contains('car-tile')).map(k => liveInventory.find(v => vehicleKey(v) === k.dataset.vkey));
      const after = kids[i + 1] && liveInventory.find(v => vehicleKey(v) === kids[i + 1].dataset.vkey);
      return { i, nBefore: before.length, allNew: before.every(v => setOutSince(v, FEED_SINCE_DAY)), afterOld: after ? !setOutSince(after, FEED_SINCE_DAY) : null };
    });
    ok(dv.i > 0 && dv.nBefore === ln.n && dv.allNew && dv.afterOld === true, 'a divider where the new ones end', dv);
    await S.page.evaluate(() => window.scrollTo(0, 0));
    await S.page.click('#live-grid .since-show');
    await S.page.waitForTimeout(300);
    const only = await S.page.evaluate(() => ({ n: getFilteredLive().length, bad: getFilteredLive().filter(v => !setOutSince(v, FEED_SINCE_DAY)).length, text: document.querySelector('#live-grid .since-line').textContent.replace(/\s+/g, ' '), divider: !!document.querySelector('#live-grid .feed-divider') }));
    ok(only.n === ln.n && only.bad === 0 && /Showing the/.test(only.text) && !only.divider, 'one tap shows just those', only);
    await S.page.click('#live-grid .since-all');
    await S.page.waitForTimeout(300);
    ok(await S.page.evaluate(() => !liveSinceOnly && !!document.querySelector('#live-grid .since-show')), 'Show all cars goes back');
    await S.page.reload({ waitUntil: 'domcontentloaded' });
    await S.page.waitForFunction(() => typeof liveComplete !== 'undefined' && liveComplete, null, { timeout: 180000 });
    await S.page.waitForTimeout(500);
    ok(await S.page.evaluate(() => !!document.querySelector('#live-grid .since-line')), 'held for the session: a reload keeps the line');
    await S.ctx.close();
    const T2 = await open({ storage: { ys_last_visit_day: daysAgo(0) } });
    ok(await T2.page.evaluate(() => !document.querySelector('#live-grid .since-line') && FEED_SINCE_DAY === null), 'a visit earlier the same day: no line');
    await T2.ctx.close();
  }

  console.log('9. First visit: the note after the first row on a phone');
  {
    const want = fs.readFileSync(path.join(DOCS, 'index.html'), 'utf8').match(/<div class="first-run-note"[\s\S]*?<\/div>/)[0].replace(/<!--[\s\S]*?-->/g, '').replace(/<[^>]+>/g, '').replace(/&mdash;/g, '—').replace(/\s+/g, ' ').trim();
    const F = await open({ ack: false });
    const n = await F.page.evaluate(() => { const e = document.getElementById('first-run-note'); const prev = e.previousElementSibling; const tiles = [...document.querySelectorAll('#live-grid > .car-tile')]; return { parent: e.parentElement.id, after: tiles.indexOf(prev), text: e.textContent.replace(/\s+/g, ' ').trim(), shown: getComputedStyle(e).display !== 'none' }; });
    ok(n.shown && n.parent === 'live-grid' && n.after === 1, 'phone: the note sits after the first row (two tiles)', n);
    ok(n.text === want, 'same words and the Got it button', [n.text, want]);
    await F.page.evaluate(() => renderLive());
    ok(await F.page.evaluate(() => document.querySelectorAll('#first-run-note').length === 1 && document.getElementById('first-run-note').previousElementSibling.classList.contains('car-tile')), 'a re-render keeps one note in its place');
    await F.page.click('#first-run-dismiss');
    ok(await F.page.evaluate(() => getComputedStyle(document.getElementById('first-run-note')).display === 'none' && localStorage.getItem('jh_honesty_ack') === '1'), 'Got it hides it for good');
    await F.ctx.close();
    const F2 = await open({ ack: false, zip: false });
    ok(await F2.page.evaluate(() => document.getElementById('first-run-note').parentElement.id === 'tab-live'), 'no location: the note stays where it is');
    await F2.ctx.close();
    const F3 = await open({ ack: false, w: 1280, h: 900 });
    ok(await F3.page.evaluate(() => document.getElementById('first-run-note').parentElement.id === 'tab-live'), 'desktop: the note stays where it is');
    await F3.ctx.close();
  }

  console.log('10. The app banner waits');
  {
    const A = await open({ qs: '?appbanner=ios' });
    const shown = () => A.page.evaluate(() => getComputedStyle(document.getElementById('app-promo')).display !== 'none');
    ok(!(await shown()), 'first visit: no banner over the first screen of cars');
    await A.page.evaluate(() => { const g = document.getElementById('live-grid'); const t = g.querySelectorAll(':scope > .car-tile')[3]; window.scrollTo(0, window.scrollY + t.getBoundingClientRect().bottom + 10); });
    await A.page.waitForTimeout(300);
    ok(!(await shown()), '…nor after the second row');
    await A.page.evaluate(() => { const g = document.getElementById('live-grid'); const t = g.querySelectorAll(':scope > .car-tile')[5]; window.scrollTo(0, window.scrollY + t.getBoundingClientRect().bottom + 10); });
    await A.page.waitForTimeout(300);
    ok(await shown(), 'past the third row of tiles: the banner');
    await A.ctx.close();
    const B = await open({ qs: '?appbanner=android' });
    ok(!(await B.page.evaluate(() => getComputedStyle(document.getElementById('app-promo')).display !== 'none')), 'a visitor who does not scroll: none at first');
    await B.page.waitForTimeout(31000);
    ok(await B.page.evaluate(() => getComputedStyle(document.getElementById('app-promo')).display !== 'none'), '…and the banner 30 s after the list rendered');
    await B.ctx.close();
    const Z = await open({ qs: '?appbanner=ios', zip: false });
    await Z.page.waitForTimeout(500);
    ok(await Z.page.evaluate(() => getComputedStyle(document.getElementById('app-promo')).display === 'none' && getComputedStyle(document.getElementById('zip-banner')).display !== 'none'), 'not on the zip card');
    await Z.ctx.close();
  }
} finally {
  await browser.close();
  srv.close();
}
console.log(`\n${pass} passed, ${fail} failed`);
console.log(fail ? 'FAILED' : 'ALL PASS');
process.exit(fail ? 1 : 0);
