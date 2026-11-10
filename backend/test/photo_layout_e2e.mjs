/* Browser e2e: photos on cards and the car screen (hub 2026-11-09, owner:
 * "on the computer, the images are large/wonky"). Real chain photos are
 * replaced by local fixture photos of three shapes (3:2, 4:3, portrait 3:4),
 * so images actually load. At 390/768/1280/1440px, light and dark, asserts:
 *  - the photo credit is fully visible: elementFromPoint at each of its
 *    corners hits the credit (it was under the photo; cards read "-Pull");
 *  - the credit stays clear of the bottom-right corner (chain watermarks);
 *  - the photo is never cropped: the image shows at its own shape (contain);
 *  - no grey bars: wherever the photo doesn't reach the box edge, the box
 *    shows the soft fill of the same photo (ph-filled), on every screen;
 *  - wide screens (>=700px): card photo boxes are 3:2, a 3:2 photo fills its
 *    box edge to edge, and every card's photo slot in a grid row is the same
 *    height (photo or drawing);
 *  - the car screen photo follows the same rules;
 *  - Walk the rows: thumbs get the fill, and a thumb scrolled under the sticky
 *    row header never paints over it.
 * Run: node backend/test/photo_layout_e2e.mjs   (Playwright pre-installed). */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const HERE = path.dirname(new URL(import.meta.url).pathname);
const DOCS = path.resolve(HERE, '../../docs');
const FIX = ['photo_600x400.jpg', 'photo_640x480.jpg', 'photo_480x640.jpg'].map(f => fs.readFileSync(path.join(HERE, 'fixtures', f)));
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
const YARD = process.env.YARD || 'Pick-n-Pull - Salt Lake City';

let checks = 0; const fails = [];
const ok = (cond, msg) => { checks++; if (!cond) fails.push(msg); };
const hash = (s) => { let h = 0; for (const c of s) h = (h * 31 + c.charCodeAt(0)) >>> 0; return h; };

// Runs in the page: inspect every loaded photo box in `root`.
const inspect = (sel) => {
  const out = [];
  for (const box of document.querySelectorAll(sel)) {
    const img = box.querySelector('img');
    if (!img || !img.complete || !img.naturalWidth || box.classList.contains('photo-failed')) continue;
    box.scrollIntoView({ block: 'center' });
    const b = box.getBoundingClientRect(), r = img.naturalWidth / img.naturalHeight;
    const cw = Math.min(b.width, b.height * r), ch = cw / r;   // contain
    const gapX = (b.width - cw) / 2, gapY = (b.height - ch) / 2;
    const fit = getComputedStyle(img).objectFit;
    const cr = box.querySelector('.photo-credit');
    let creditOk = null, creditRight = null;
    if (cr) {
      const c = cr.getBoundingClientRect();
      // corners, inset past the rounded corner
      const pts = [[c.left + 3, c.top + 3], [c.right - 3, c.top + 3], [c.left + 3, c.bottom - 3], [c.right - 3, c.bottom - 3]];
      const hits = pts.map(([x, y]) => document.elementFromPoint(x, y));
      creditOk = hits.every(e => e === cr || cr.contains(e)) && c.right <= b.right + 0.5 && c.left >= b.left - 0.5 && c.bottom <= b.bottom + 0.5;
      if (!creditOk) window.__creditMiss = hits.map(e => e ? e.tagName + '.' + e.className : 'none').join(' | ') + ` ${c.left|0},${c.top|0},${c.right|0},${c.bottom|0} box ${b.left|0},${b.top|0},${b.right|0},${b.bottom|0}`;
      creditRight = c.right > b.right - 2;
    }
    const fill = box.querySelector('.ph-fill');
    out.push({ w: b.width, h: b.height, top: Math.round(b.top + scrollY), nat: `${img.naturalWidth}x${img.naturalHeight}`, gapX, gapY, fit,
      filled: box.classList.contains('ph-filled') && !!fill && /url\(/.test(fill.style.backgroundImage) && getComputedStyle(fill).opacity === '1',
      creditOk, creditRight, cls: box.className });
  }
  return out;
};

const browser = await chromium.launch();
try {
  for (const width of (process.env.WIDTHS || "390,768,1280,1440").split(",").map(Number)) {
    for (const theme of ['light', 'dark']) {
      const cfg = `${width}/${theme}`;
      const page = await browser.newPage({ viewport: { width, height: 900 }, colorScheme: theme });
      await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, (route) => {
        if (route.request().resourceType() === 'image') return route.fulfill({ status: 200, contentType: 'image/jpeg', body: FIX[hash(route.request().url()) % 3] });
        return route.abort();
      });
      await page.route(/data\/inv\/manifest\.json/, r => r.fulfill({ status: 404, body: '' }));
      await page.addInitScript(() => {
        localStorage.setItem('jh_honesty_ack', '1'); localStorage.setItem('jh_zip', '84401');
        localStorage.setItem('jh_zip_coords', JSON.stringify({ '84401': { lat: 41.223, lng: -111.973 } }));
      });
      await page.goto(BASE, { waitUntil: 'domcontentloaded' });
      await page.waitForFunction(() => typeof liveComplete !== 'undefined' && liveComplete, null, { timeout: 300000 });
      await page.evaluate((y) => viewYardInLive(y), YARD);
      await page.waitForSelector('#live-grid .photo-box img', { timeout: 60000 });
      // load the first dozen cards' photos (lazy) by scrolling them in
      await page.evaluate(async () => { for (const b of [...document.querySelectorAll('#live-grid .car-card')].slice(0, 12)) { b.scrollIntoView(); await new Promise(r => setTimeout(r, 120)); } });
      await page.waitForTimeout(800);
      const cards = await page.evaluate(inspect, '#live-grid .car-card:nth-child(-n+12) .photo-box');
      ok(cards.length >= 4, `${cfg}: only ${cards.length} card photos loaded`);
      if (process.env.DEBUG) console.log(cfg, await page.evaluate(() => window.__creditMiss));
      const shapes = new Set(cards.map(c => c.nat));
      for (const c of cards) {
        const tag = `${cfg} card ${c.nat}`;
        ok(c.creditOk === true, `${tag}: photo credit not fully visible`);
        ok(c.creditRight === false, `${tag}: credit sits in the bottom-right (watermark) corner`);
        ok(c.fit === 'contain', `${tag}: photo cropped (object-fit ${c.fit})`);
        ok(c.filled || (c.gapX <= 1.5 && c.gapY <= 1.5), `${tag}: grey bars (${c.gapX.toFixed(0)}px sides, ${c.gapY.toFixed(0)}px top/bottom) with no fill`);
        if (width >= 700) {
          ok(Math.abs(c.w / c.h - 1.5) < 0.02, `${tag}: card photo box ${c.w.toFixed(0)}x${c.h.toFixed(0)} is not 3:2`);
          if (c.nat === '600x400') ok(c.gapX <= 1.5 && c.gapY <= 1.5, `${tag}: a 3:2 photo does not fill its box (${c.gapX.toFixed(0)}/${c.gapY.toFixed(0)}px)`);
        }
      }
      // cards even: every photo slot (photo or drawing) in one grid row is the same height
      const rows = await page.evaluate(() => {
        const by = {};
        for (const card of [...document.querySelectorAll('#live-grid .car-card')].slice(0, 24)) {
          const b = card.querySelector('.photo-box'); if (!b) continue;
          const r = card.getBoundingClientRect(); const k = Math.round(r.top + scrollY);
          (by[k] = by[k] || []).push(Math.round(b.getBoundingClientRect().height));
        }
        return Object.values(by).filter(a => a.length > 1);
      });
      for (const r of rows) ok(Math.max(...r) - Math.min(...r) <= 1, `${cfg}: photo slots in one card row differ: ${r.join('/')}px`);
      if (process.env.SHOTS) {
        await page.evaluate(() => { const c = [...document.querySelectorAll('#live-grid .car-card')].find(x => x.querySelector('.photo-box img[src]') && x.querySelector('img').naturalHeight > x.querySelector('img').naturalWidth); (c || document.querySelector('#live-grid .car-card')).scrollIntoView({ block: 'start' }); window.scrollBy(0, -90); });
        await page.waitForTimeout(500);
        await page.screenshot({ path: `${process.env.SHOTS}/photo-cards-${cfg.replace('/', '-')}.png` });
      }
      // car screen
      const key = await page.evaluate(() => { const b = document.querySelector('#live-grid .photo-box[data-photo-vkey] img'); return b && b.closest('.photo-box').dataset.photoVkey; });
      await page.evaluate((k) => openCarDetail(k), key);
      await page.waitForTimeout(900);
      const cd = await page.evaluate(inspect, '.cd-photo');
      ok(cd.length === 1, `${cfg}: car screen photo did not load`);
      for (const c of cd) {
        const tag = `${cfg} car screen ${c.nat}`;
        ok(c.creditOk === true, `${tag}: photo credit not fully visible`);
        ok(c.creditRight === false, `${tag}: credit sits in the bottom-right (watermark) corner`);
        ok(c.fit === 'contain', `${tag}: photo cropped`);
        ok(c.filled || (c.gapX <= 1.5 && c.gapY <= 1.5), `${tag}: grey bars with no fill`);
      }
      // Walk the rows: thumbs have the fill (no bands), and a thumb scrolled under
      // the sticky row header never paints over it (it did with the fill layers).
      await page.evaluate(() => { hideCarDetail && hideCarDetail(); });
      const rowsOut = await page.evaluate(async (y) => {
        openYardRows(y);
        await new Promise(r => setTimeout(r, 900));
        const thumbs = [...document.querySelectorAll('#yard-rows .yr-thumb')].slice(0, 8);
        for (const t of thumbs) { t.scrollIntoView({ block: 'center' }); await new Promise(r => setTimeout(r, 80)); }
        await new Promise(r => setTimeout(r, 500));
        const loaded = thumbs.filter(t => { const i = t.querySelector('img'); return i && i.complete && i.naturalWidth; });
        const unfilled = loaded.filter(t => !t.classList.contains('ph-filled')).length;
        // put a thumb right under the sticky header of its row
        const head = document.querySelector('#yard-rows .yr-row-head'), t = loaded[1] || loaded[0];
        let covered = null;
        if (head && t) {
          const sc = (function f(el) { while (el && el !== document.body) { const o = getComputedStyle(el).overflowY; if ((o === 'auto' || o === 'scroll') && el.scrollHeight > el.clientHeight) return el; el = el.parentElement; } return document.scrollingElement; })(t);
          const hr = head.getBoundingClientRect(), tr = t.getBoundingClientRect();
          sc.scrollTop += (tr.top - hr.top) - 4;
          await new Promise(r => setTimeout(r, 200));
          const h2 = document.querySelector('#yard-rows .yr-row-head[style], #yard-rows .yr-row-head');
          const heads = [...document.querySelectorAll('#yard-rows .yr-row-head')].filter(h => { const r = h.getBoundingClientRect(); return r.top >= -1 && r.top < 200 && r.height; });
          const hh = heads[0] || h2, r = hh.getBoundingClientRect();
          // probe where the thumb now sits under the header
          const tr2 = t.getBoundingClientRect(), px = (Math.max(tr2.left, r.left) + Math.min(tr2.right, r.right)) / 2, py = (Math.max(tr2.top, r.top) + Math.min(tr2.bottom, r.bottom)) / 2;
          const e = document.elementFromPoint(px, py);
          covered = !(e && hh.contains(e)) ? (e ? e.tagName + '.' + e.className : 'none') : false;
        }
        hideYardRows && hideYardRows();
        return { loaded: loaded.length, unfilled, covered };
      }, YARD);
      ok(rowsOut.loaded >= 2, `${cfg}: only ${rowsOut.loaded} row thumbs loaded`);
      ok(rowsOut.unfilled === 0, `${cfg}: ${rowsOut.unfilled} row thumbs without the fill`);
      ok(rowsOut.covered === false, `${cfg}: the sticky row header is covered by ${rowsOut.covered}`);
      console.log(`${cfg}: ${cards.length} card photos (${[...shapes].join(', ')}), ${rows.length} card rows, car screen ${cd.map(c => `${c.w.toFixed(0)}x${c.h.toFixed(0)} ${c.nat}`).join('')}`);
      if (process.env.SHOTS) { await page.screenshot({ path: `${process.env.SHOTS}/photo-car-${cfg.replace('/', '-')}.png` }); }
      await page.close();
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
