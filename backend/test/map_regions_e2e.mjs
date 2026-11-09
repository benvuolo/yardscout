/* Browser e2e: the map's pin rules hold nationwide (owner request 2026-11-09).
 * Over dense real regions with today's data (national view plus nine metro
 * areas), at 320/390/768/1280px, light and dark, 100% and 200% map text, and
 * three zoom levels each, asserts:
 *  - no two pins overlap;
 *  - no pin is drawn whose yard's point is off the open map;
 *  - the credit line and the zoom buttons are visible and nothing covers
 *    them (the credit may move into the sheet when there's no room);
 *  - no floating pull-sheet pill over the map;
 *  - a cluster of yards at one spot opens a list in the sheet;
 *  - no "(Premium)" lot gets its own pin;
 *  - no pin covers the You dot or its label (if nothing clears it, the dot
 *    is drawn on top; counted in the summary);
 *  - first view (hub 2026-11-09): the nearest yard is its own named pin,
 *    drawn above the sheet, and the user's spot is on the map (unless the
 *    nearest yard needed a closer view than that allows; reported). Zooming out
 *    from there (-2, -4) still clusters under the same rules.
 * 200% text doubles the map's own text (pins, legend, credit, sheet) and the
 * pin's rem-based width cap, as a real text-size change does; the app
 * measures pins every time it places them, which is what a real text-size
 * change goes through.
 * Run: node backend/test/map_regions_e2e.mjs   (Playwright pre-installed;
 * needs tiles.openfreemap.org and unpkg.com). WIDTHS=… REGIONS=… to narrow. */
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

const REGIONS = [
  ['National', 39.5, -98.35, true],
  ['Atlanta', 33.749, -84.388], ['Phoenix', 33.448, -112.074], ['Los Angeles / Inland Empire', 34.05, -117.75],
  ['Chicago', 41.878, -87.63], ['Dallas–Fort Worth', 32.85, -97.05], ['Houston', 29.76, -95.37],
  ['Denver', 39.74, -104.99], ['Northeast corridor', 40.35, -74.65], ['Salt Lake', 40.76, -111.89],
  ['Ogden', 41.223, -111.973],
].filter(r => !process.env.REGIONS || process.env.REGIONS.split(',').some(x => r[0].toLowerCase().startsWith(x.toLowerCase())));
const WIDTHS = (process.env.WIDTHS || '320,390,768,1280').split(',').map(Number);

const results = new Map();   // region -> {checks, fails:[], pins:Set, clusters:Set, same:0}
const rec = (r) => { if (!results.has(r)) results.set(r, { checks: 0, fails: [], pins: [], clusters: [], same: 0 }); return results.get(r); };

const browser = await chromium.launch();
try {
  for (const width of WIDTHS) {
    const page = await browser.newPage({ viewport: { width, height: width >= 768 ? 900 : 844 } });
    await page.route(/^https?:\/\/(?!127\.0\.0\.1|unpkg\.com|tiles\.openfreemap\.org)/, r => r.abort());
    // Full-file data path: every region's cars are in from the start.
    await page.route(/data\/inv\/manifest\.json/, r => r.fulfill({ status: 404, body: '' }));
    await page.addInitScript(() => {
      localStorage.setItem('jh_honesty_ack', '1'); localStorage.setItem('jh_zip', '30303');
      localStorage.setItem('jh_zip_coords', JSON.stringify({ '30303': { lat: 33.749, lng: -84.388 } }));
      localStorage.setItem('ys_rows_tip_off', '1');
    });
    await page.goto(BASE, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof liveComplete !== 'undefined' && liveComplete && liveInventory.length > 100000, null, { timeout: 300000 });
    await page.evaluate(() => document.querySelector('.tab[data-tab="yards"]').click());
    for (const [name, lat, lng, national] of REGIONS) {
      for (const theme of ['light', 'dark']) {
        for (const big of [false, true]) {
          const cfg = `${width}/${theme}/${big ? '200%' : '100%'}`;
          const out = await page.evaluate(async ({ lat, lng, national, theme, big }) => {
            document.documentElement.dataset.theme = theme; applyThemeColor();
            if (national) { localStorage.setItem('jh_pro', '1'); applyProGates(); document.getElementById('live-radius').value = ''; }
            else { localStorage.removeItem('jh_pro'); applyProGates(); document.getElementById('live-radius').value = '100'; }
            activeZipCoords = { lat, lng };
            let st = document.getElementById('__big');
            if (big && !st) { st = document.createElement('style'); st.id = '__big'; st.textContent = '#yards-map .map-pin{max-width:15rem!important}#yards-map .map-pin .pin-name{font-size:24px!important}#yards-map .map-pin .pin-cars,#yards-map .map-pin .pin-watch{font-size:22px!important}#yards-map-wrap .yards-map-legend,#yards-map .maplibregl-ctrl-attrib,.ms-credit{font-size:24px!important}.ms-title{font-size:32px!important}.ms-row-name{font-size:28px!important}.ms-row-meta{font-size:24px!important}'; document.head.appendChild(st); }
            if (!big && st) st.remove();
            setYardsView('map'); await renderYardsMap();
            const t0 = Date.now();
            while (!(window._yardsMap && _yardsMap.loaded()) && Date.now() - t0 < 20000) await new Promise(r => setTimeout(r, 100));
            await new Promise(r => setTimeout(r, 300));
            const fails = [], stats = []; let youOverCount = 0;
            const ov = (a, b) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
            const vis = (el) => el && el.getClientRects().length && getComputedStyle(el).display !== 'none' && getComputedStyle(el).visibility !== 'hidden';
            const check = (label) => {
              layoutPins(); liftMapControls();
              const pins = [...document.querySelectorAll('#yards-map .pin-layer .map-pin')];
              const rs = pins.map(p => p.getBoundingClientRect());
              for (let i = 0; i < rs.length; i++) for (let j = i + 1; j < rs.length; j++) if (ov(rs[i], rs[j])) fails.push(`${label}: pins overlap (${pins[i].textContent.trim().slice(0, 30)} / ${pins[j].textContent.trim().slice(0, 30)})`);
              const A = pinArea();
              _pinGroups.forEach(g => { const p = _projectFn(g.items[0]); if (p.x < 0 || p.x > A.W || p.y < A.t || p.y > A.b) fails.push(`${label}: pin drawn with its point off the open map (${g.items[0].key})`); });
              if (_mapSites.some(s => /\(Premium\)/i.test(s.key))) fails.push(`${label}: a Premium lot has its own pin`);
              const box = document.getElementById('yards-map').getBoundingClientRect();
              const inSheet = document.querySelector('#yards-map.credit-in-sheet');
              const at = document.querySelector('#yards-map .maplibregl-ctrl-attrib');
              const covers = [...pins, document.getElementById('saved-pill'), document.getElementById('yards-map-sheet')].filter(vis).map(e => e.getBoundingClientRect());
              if (inSheet) { const c = document.querySelector('#yards-map-sheet.with-credit .ms-credit'); if (!vis(c)) fails.push(`${label}: credit line missing (sheet)`); }
              else if (!vis(at)) fails.push(`${label}: credit line not visible`);
              else { const ar = at.getBoundingClientRect(); if (ar.top < box.top - 1 || ar.bottom > box.bottom + 1) fails.push(`${label}: credit line outside the map`); if (covers.some(r => ov(r, ar))) fails.push(`${label}: something covers the credit line`); }
              const zc = document.querySelector('#yards-map .maplibregl-ctrl-group');
              if (!vis(zc)) fails.push(`${label}: zoom buttons not visible`);
              else { const zr = zc.getBoundingClientRect(); if (rs.some(r => ov(r, zr))) fails.push(`${label}: a pin covers the zoom buttons`); }
              if (vis(document.getElementById('saved-pill'))) fails.push(`${label}: floating pull sheet pill over the map`);
              // The You dot (and its label) is never under a pin; if no pin
              // placement clears it, the dot is drawn on top (counted).
              const youEl = document.querySelector('#yards-map .map-you');
              if (youEl) {
                const parts = [youEl, youEl.querySelector('span')].map(e => e.getBoundingClientRect());
                const under = rs.some(r => parts.some(q => ov(r, q)));
                if (under && !youEl.classList.contains('over')) fails.push(`${label}: a pin covers the You dot`);
                if (youEl.classList.contains('over')) youOverCount++;
              }
              const same = _pinGroups.filter(g => g.items.length > 1 && g.items.every(x => siteNear(x, g.items[0])));
              for (const g of same.slice(0, 2)) {
                zoomToYards(g.items.map(x => x.key));
                if (!/yards here/.test(document.getElementById('ms-title').textContent) || document.querySelectorAll('#ms-body .ms-row').length !== g.items.length) fails.push(`${label}: same-spot cluster did not list its ${g.items.length} yards`);
                selectMapYard(null);
              }
              stats.push({ label, pins: _pinGroups.filter(g => g.items.length === 1).length, clusters: _pinGroups.filter(g => g.items.length > 1).length, same: same.length, sites: _mapSites.length });
            };
            const z0 = _yardsMap.getZoom();
            check('fitted');
            {
              const near = _mapSites.filter(s => s.dist != null).sort((a, b) => a.dist - b.dist)[0];
              const sheetTop = document.getElementById('yards-map-sheet').getBoundingClientRect().top;
              const sheetSpans = document.getElementById('yards-map-sheet').getBoundingClientRect().width > document.getElementById('yards-map').getBoundingClientRect().width - 48;
              const pin = near && [...document.querySelectorAll('#yards-map .pin-layer .map-pin')].find(p => p.dataset.loc === near.key && !p.classList.contains('map-cluster'));
              if (!near) fails.push('first view: no nearest yard');
              else if (!pin) fails.push(`first view: nearest yard ${near.key} (${Math.round(near.dist)} mi) is not its own pin`);
              else if (sheetSpans && pin.getBoundingClientRect().bottom > sheetTop + 0.5) fails.push(`first view: nearest yard pin under the sheet`);
              const youEl = document.querySelector('#yards-map .map-you');
              if (!youEl) { if (!_firstViewNoYou) fails.push('first view: the user\'s spot is not on the map'); }
              else {
                const yr = (youEl.querySelector('span') || youEl).getBoundingClientRect(), A2 = pinArea(), mb = document.getElementById('yards-map').getBoundingClientRect();
                if (yr.bottom > mb.top + A2.b + 1) fails.push(`first view: the "You" label runs under the sheet or credit line`);
              }
              stats.push({ label: 'first', nearest: near ? `${yardShortLabel(near.key)} ${Math.round(near.dist)} mi, zoom ${z0.toFixed(1)}${_firstViewNoYou ? ', zoomed past your spot' : ''}` : '' , pins: _pinGroups.filter(g => g.items.length === 1).length, clusters: _pinGroups.filter(g => g.items.length > 1).length, same: 0, sites: _mapSites.length });
            }
            for (const d of [2, 4, -2, -4]) { _yardsMap.jumpTo({ zoom: z0 + d }); check('zoom ' + (d > 0 ? '+' : '') + d); }
            _yardsMap.jumpTo({ zoom: z0 });
            return { fails, stats, youOver: youOverCount };
          }, { lat, lng, national: !!national, theme, big });
          const r = rec(name);
          r.checks += out.stats.length;
          out.fails.forEach(f => r.fails.push(`${cfg} ${f}`));
          r.youOver = (r.youOver || 0) + out.youOver;
          out.stats.forEach(s => { if (s.nearest) r.nearest = s.nearest; r.pins.push(s.pins); r.clusters.push(s.clusters); r.same = Math.max(r.same, s.same); r.sites = s.sites; });
        }
      }
    }
    await page.close();
  }
} finally {
  await browser.close();
  server.close();
}
let total = 0;
for (const [name, r] of results) {
  total += r.fails.length;
  const rng = (a) => a.length ? `${Math.min(...a)}–${Math.max(...a)}` : '0';
  console.log(`${r.fails.length ? 'FAIL' : 'PASS'}  ${name}: ${r.checks} layouts, ${r.sites} yards in view, single pins ${rng(r.pins)}, clusters ${rng(r.clusters)}, same-spot clusters ${r.same}; first view: ${r.nearest || '-'}; You drawn over a pin ${r.youOver || 0}×${r.fails.length ? ` — ${r.fails.length} problems:` : ''}`);
  [...new Set(r.fails)].slice(0, 8).forEach(f => console.log('      ' + f));
}
console.log(total ? `\n${total} FAILED` : '\nALL PASS');
process.exit(total ? 1 : 0);
