/* Browser e2e: the arrival forecast (docs/forecast.js) mounted into a test
 * element on the real local app, with docs/data/arrivals/ served from a
 * fixture by request routing. Checks the text, the eight bars, no horizontal
 * overflow at 320 / 390 / 1280 px, dark mode, the missing-file case, and that
 * the page throws no errors.
 * Run: node backend/test/forecast_e2e.mjs        (Playwright pre-installed)
 *      SHOTS=1 node backend/test/forecast_e2e.mjs  also writes the two owner
 *      screenshots (fixture data) to ops/screens/arrival-forecast-1119-{1,2}.png */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const HERE = path.dirname(new URL(import.meta.url).pathname);
const DOCS = path.resolve(HERE, '../../docs');
const SHOTS = path.resolve(HERE, '../../ops/screens');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.webmanifest': 'application/manifest+json' };
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

let fails = 0, passes = 0;
const check = (name, ok, d = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + d}`); ok ? passes++ : fails++; };

// ---- fixture (made-up yards and counts; not real data) ----
const BUILT = '2026-11-19T07:00:00Z';
const index = {
  builtAt: BUILT, windowStart: '2026-09-24', windowEnd: '2026-11-18', weeks: 8,
  yardFields: ['location', 'lat', 'lng', 'coveredWeeks', 'stale'],
  yards: [
    ['Sample Pull-and-Save - North Salt Lake City', 40.85, -111.92, 8, 0],
    ['Sample U-Pull - West Valley', 40.69, -112.00, 8, 0],
    ['Sample Auto Salvage - Ogden', 41.22, -111.97, 8, 0],
    ['Sample Pick-a-Part - Provo', 40.23, -111.66, 8, 1],       // list not updating
    ['Sample Self Serve - Tooele', 40.53, -112.30, 1, 0],       // new to YardScout
    ['Sample Yard - Boise', 43.61, -116.20, 8, 0],              // far away
  ],
  makes: { Honda: ['honda', 0], Toyota: ['toyota', 0] },
};
const honda = {
  builtAt: BUILT, windowEnd: '2026-11-18', make: 'Honda', slug: 'honda',
  models: {
    Civic: [
      [0, 2001, 2, 1, 3, 2, 1, 2, 3, 2], [0, 2006, 1, 2, 1, 0, 2, 1, 1, 3],
      [1, 2003, 1, 1, 2, 1, 0, 2, 1, 1], [1, 2008, 0, 1, 0, 1, 1, 0, 2, 1],
      [2, 2005, 1, 0, 1, 1, 1, 0, 1, 2], [3, 2004, 4, 4, 4, 4, 4, 4, 4, 4],
      [4, 2007, 0, 0, 0, 0, 0, 0, 0, 3], [5, 2004, 9, 9, 9, 9, 9, 9, 9, 9],
    ],
  },
};
const toyota = {
  builtAt: BUILT, windowEnd: '2026-11-18', make: 'Toyota', slug: 'toyota',
  models: {
    '4Runner': [[0, 2004, 0, 0, 1, 0, 0, 0, 0, 0], [2, 2007, 0, 0, 0, 0, 0, 1, 0, 0], [1, 2012, 0, 0, 0, 0, 0, 0, 0, 1]],
    Previa: [[2, 1995, 0, 0, 0, 0, 0, 0, 1, 0]],
  },
};
const FILES = { 'index.json': index, 'honda.json': honda, 'toyota.json': toyota };
const SLC = { lat: 40.7608, lng: -111.891, radiusMi: 50, where: 'Salt Lake City' };
const CIVIC = { make: 'Honda', model: 'Civic', yrMin: null, yrMax: null, ...SLC };
const RUNNER = { make: 'Toyota', model: '4Runner', yrMin: 2003, yrMax: 2009, ...SLC };
const PREVIA = { make: 'Toyota', model: 'Previa', yrMin: null, yrMax: null, ...SLC };

const browser = await chromium.launch();
async function open({ width = 390, dark = false, missing = false, dsf = 1 } = {}) {
  const ctx = await browser.newContext({ viewport: { width, height: 820 }, deviceScaleFactor: dsf, colorScheme: dark ? 'dark' : 'light', reducedMotion: 'reduce' });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e && e.message || e)));
  page.on('console', m => { if (m.type() === 'error' && /forecast|YSForecast|ysf/i.test(m.text())) errors.push(m.text()); });
  await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, r => r.abort());
  const seen = [];
  await page.route(/\/data\/arrivals\/[^/?]+\.json/, (r) => {
    const name = new URL(r.request().url()).pathname.split('/').pop();
    seen.push(name);
    if (missing || !FILES[name]) return r.fulfill({ status: 404, body: 'not found' });
    return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(FILES[name]) });
  });
  await page.addInitScript((d) => {
    localStorage.setItem('jh_honesty_ack', '1');
    if (d) localStorage.setItem('ys_theme', 'dark');
  }, dark);
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => !!window.YSForecast, null, { timeout: 60000 });
  await page.evaluate(() => {
    const host = document.createElement('div');
    host.id = 'ysf-host';
    host.style.cssText = 'position:fixed;inset:0;z-index:2147483000;overflow:auto;background:var(--bg);padding:16px;box-sizing:border-box';
    const el = document.createElement('div');
    el.id = 'ysf-test';
    host.appendChild(el);
    document.body.appendChild(host);
  });
  return { page, ctx, errors, seen };
}
const mount = (page, q) => page.evaluate(q => YSForecast.mount(document.getElementById('ysf-test'), q), q);
const read = (page) => page.evaluate(() => {
  const el = document.getElementById('ysf-test');
  const t = (s) => (el.querySelector(s) || {}).textContent || '';
  const host = document.getElementById('ysf-host');
  const hr = host.getBoundingClientRect();
  let over = [];
  for (const n of el.querySelectorAll('*')) {
    const r = n.getBoundingClientRect();
    if (r.width && (r.right > hr.right - 16 + 0.5 || r.left < hr.left + 16 - 0.5)) over.push(n.className + ' ' + Math.round(r.left) + '..' + Math.round(r.right));
    if (n.scrollWidth > n.clientWidth + 1 && getComputedStyle(n).overflowX !== 'visible') over.push('scroll ' + n.className);
  }
  const bars = [...el.querySelectorAll('.ysf-bar')].map(b => ({
    n: b.querySelector('.ysf-bar-n').textContent,
    h: b.querySelector('.ysf-bar-fill').getBoundingClientRect().height,
    track: b.querySelector('.ysf-bar-track').getBoundingClientRect().height,
  }));
  const box = el.querySelector('.ysf');
  const cs = box ? getComputedStyle(box) : null;
  return {
    html: el.innerHTML, subject: t('.ysf-subject'), headline: t('.ysf-headline'), facts: t('.ysf-facts'),
    most: t('.ysf-most'), label: t('.ysf-label'), alt: (el.querySelector('.ysf-bars') || { getAttribute: () => '' }).getAttribute('aria-label'),
    bars, over, docOver: document.documentElement.scrollWidth > window.innerWidth,
    bg: cs && cs.backgroundColor, color: cs && cs.color, fill: el.querySelector('.ysf-bar-fill') ? getComputedStyle(el.querySelector('.ysf-bar-fill')).backgroundColor : '',
  };
});

try {
  // ---- text and bars, at three widths ----
  for (const width of [320, 390, 1280]) {
    const { page, ctx, errors } = await open({ width });
    const st = await mount(page, CIVIC);
    const r = await read(page);
    // Civic in 50 mi: yards 0,1,2 counted (8 weeks each); Provo stale, Tooele new, Boise far.
    // weekly totals: [5,5,7,5,5,5,8,9] = 49; rate 49/8 = 6.1
    check(`${width}px: mount resolves ok`, st === 'ok', String(st));
    check(`${width}px: subject "Civic, any year"`, r.subject === 'Civic, any year', r.subject);
    check(`${width}px: headline`, r.headline === 'About 6 a week land within 50 mi of Salt Lake City', r.headline);
    check(`${width}px: facts with skipped yards`, r.facts === '49 in the last 8 weeks at 3 yards (2 yards not counted: list not updating / new to YardScout)', r.facts);
    check(`${width}px: most land at`, r.most === 'Most land at: Sample Pull-and-Save - North Salt Lake City (27), Sample U-Pull - West Valley (15)', r.most);
    check(`${width}px: label`, r.label === 'From set-out dates YardScout has recorded. Past weeks, not a promise.');
    check(`${width}px: eight bars with the weekly numbers`, r.bars.length === 8 && r.bars.map(b => b.n).join(',') === '5,5,7,5,5,5,8,9', JSON.stringify(r.bars));
    const max = Math.max(...r.bars.map(b => b.h));
    check(`${width}px: tallest bar is the newest week and fills its track`, r.bars[7].h === max && Math.abs(max - r.bars[7].track) < 1.5, JSON.stringify(r.bars));
    check(`${width}px: bar heights follow the counts`, r.bars.every(b => Math.abs(b.h - r.bars[7].track * (+b.n) / 9) < 1.5), JSON.stringify(r.bars));
    check(`${width}px: text alternative reads the numbers`, r.alt === 'Arrivals per week, oldest to newest: 5, 5, 7, 5, 5, 5, 8, 9', r.alt);
    check(`${width}px: no horizontal overflow`, r.over.length === 0 && !r.docOver, JSON.stringify(r.over));
    // a long, rare one
    await mount(page, RUNNER);
    const r2 = await read(page);
    check(`${width}px: year span named, rate wording`, r2.subject === '2003-2009 4Runner' && r2.headline === 'About one every 4 weeks lands within 50 mi of Salt Lake City', r2.subject + ' | ' + r2.headline);
    check(`${width}px: 4Runner facts and no "most" under 3`, r2.facts.startsWith('2 in the last 8 weeks at 3 yards') && r2.most === '', r2.facts + ' | ' + r2.most);
    check(`${width}px: zero weeks draw no bar`, r2.bars.filter(b => b.h === 0).length === 6, JSON.stringify(r2.bars));
    check(`${width}px: rare one has no overflow`, r2.over.length === 0 && !r2.docOver, JSON.stringify(r2.over));
    await mount(page, PREVIA);
    const r3 = await read(page);
    check(`${width}px: exactly one: Rare here`, r3.headline === 'Rare here: 1 landed within 50 mi of Salt Lake City in the last 8 weeks', r3.headline);
    await mount(page, { ...CIVIC, model: 'Fit' });
    check(`${width}px: none landed`, (await read(page)).headline === 'None landed within 50 mi of Salt Lake City in the last 8 weeks');
    await mount(page, { ...CIVIC, lat: 40.53, lng: -112.30, radiusMi: 5, where: '' });
    const r4 = await read(page);
    check(`${width}px: only a new yard in reach: not enough history, no bars`, r4.headline === 'Not enough history near you yet' && r4.bars.length === 0 && r4.facts.includes('(1 yard not counted: new to YardScout)'), r4.headline + ' | ' + r4.facts);
    const st5 = await mount(page, { ...CIVIC, lat: null, lng: null });
    check(`${width}px: no place renders nothing`, st5 === null && (await read(page)).html === '');
    check(`${width}px: page has no errors`, errors.length === 0, JSON.stringify(errors));
    await ctx.close();
  }

  // ---- dark mode ----
  {
    const light = await open({ width: 390 });
    await mount(light.page, CIVIC);
    const L = await read(light.page);
    await light.ctx.close();
    const { page, ctx, errors } = await open({ width: 390, dark: true });
    await mount(page, CIVIC);
    const D = await read(page);
    const lum = (c) => { const m = String(c).match(/\d+(\.\d+)?/g) || [0, 0, 0]; return (0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]) / 255; };
    const tokens = await page.evaluate(() => { const s = getComputedStyle(document.documentElement); return { surface: s.getPropertyValue('--surface').trim(), text: s.getPropertyValue('--text').trim() }; });
    check('dark: box and text colours change with the theme', D.bg !== L.bg && D.color !== L.color, JSON.stringify({ L: [L.bg, L.color], D: [D.bg, D.color] }));
    check('dark: dark surface, light text', lum(D.bg) < 0.3 && lum(D.color) > 0.6, JSON.stringify([D.bg, D.color, tokens]));
    check('dark: bars drawn in a visible colour', D.fill && D.fill !== D.bg && !/rgba\(0, 0, 0, 0\)/.test(D.fill), D.fill);
    check('dark: no overflow, no errors', D.over.length === 0 && !D.docOver && errors.length === 0, JSON.stringify([D.over, errors]));
    await ctx.close();
  }

  // ---- missing files ----
  {
    const { page, ctx, errors, seen } = await open({ width: 390, missing: true });
    let threw = null, st;
    try { st = await mount(page, CIVIC); } catch (e) { threw = e; }
    const r = await read(page);
    check('missing index: renders nothing, resolves null, does not throw', !threw && st === null && r.html === '', String(threw) + ' ' + r.html);
    check('missing index: it was asked for', seen.includes('index.json'), JSON.stringify(seen));
    check('missing index: page has no errors', errors.length === 0, JSON.stringify(errors));
    await ctx.close();
  }
  {
    const { page, ctx, errors } = await open({ width: 390 });
    const st = await mount(page, { ...CIVIC, make: 'Subaru' });
    check('make with no file in the index: renders nothing', st === null && (await read(page)).html === '');
    await page.unroute(/\/data\/arrivals\/[^/?]+\.json/);
    await page.route(/\/data\/arrivals\/[^/?]+\.json/, (r) => {
      const name = new URL(r.request().url()).pathname.split('/').pop();
      return name === 'index.json' ? r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(index) }) : r.fulfill({ status: 404, body: '' });
    });
    const st2 = await mount(page, CIVIC);
    check('make file missing (404): renders nothing', st2 === null && (await read(page)).html === '');
    check('no errors after the failed loads', errors.length === 0, JSON.stringify(errors));
    await ctx.close();
  }

  // ---- owner screenshots (fixture data), only on request ----
  if (process.env.SHOTS) {
    fs.mkdirSync(SHOTS, { recursive: true });
    for (const [n, q] of [[1, CIVIC], [2, RUNNER]]) {
      const { page, ctx } = await open({ width: 390, dsf: 2 });
      await mount(page, q);
      await page.locator('#ysf-test').screenshot({ path: path.join(SHOTS, `arrival-forecast-1119-${n}.png`) });
      console.log(`wrote ops/screens/arrival-forecast-1119-${n}.png`);
      await ctx.close();
    }
  }
} finally {
  await browser.close();
  server.close();
}
console.log(`\n${passes} passed, ${fails} failed`);
process.exit(fails ? 1 : 0);
