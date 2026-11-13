/* Browser e2e: the Cars-tab car search and the #cars= deep link
 * (docs/app.js CAR SEARCH, 2026-11-12, from the r/XTerra feedback).
 *   - type "xterra", pick the suggestion: the list shows only Nissan
 *     Xterras, and the Cars filters hold exactly what Filters -> Make ->
 *     Model would (same cars, same order, same stats bar, same sort)
 *   - Enter with one clear match picks it; spelling variants suggest the
 *     right model ("4 runner", "f150", "cr v")
 *   - the clear control resets make + model
 *   - the box sits above the fold at 390x844 once a zip is set
 *   - #cars=Nissan|Xterra|2005-2015 (with utm params) opens with the
 *     filters applied; with no zip yet, they apply once one is entered;
 *     an unknown model leaves every car listed and the box prefilled
 * Serves docs/ locally; the inventory is the published scan in docs/data.
 * Run: node backend/test/car_search_e2e.mjs   (Playwright pre-installed) */
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

let fails = 0;
const check = (name, ok, d = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + d}`); if (!ok) fails++; };

const browser = await chromium.launch();
const errors = [];
async function open(hash = '', { zip = true, pro = false } = {}) {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, (r) => r.abort());
  await page.addInitScript(({ zip, pro }) => {
    localStorage.setItem('jh_honesty_ack', '1');
    localStorage.setItem('ys_app_promo', '1');
    // The zip's coordinates are cached either way (no geocoder offline);
    // without jh_zip the visitor has no location yet and sees the banner.
    localStorage.setItem('jh_zip_coords', JSON.stringify({ '95112': { lat: 37.3485, lng: -121.8863 } }));
    if (zip) localStorage.setItem('jh_zip', '95112');
    if (pro) { localStorage.setItem('jh_pro', '1'); localStorage.setItem('jh_pro_source', 'account'); }
  }, { zip, pro });
  await page.goto(BASE + hash, { waitUntil: 'domcontentloaded' });
  return page;
}
const ready = (page) => page.waitForFunction(() => typeof liveLoaded !== 'undefined' && liveLoaded
  && !(typeof _inv !== 'undefined' && _inv && !liveComplete && invViewPending())
  && document.querySelector('#live-grid .car-card'), null, { timeout: 180000 });
// What is on screen: the filter state, the cars listed, the stats bar.
const state = (page) => page.evaluate(() => {
  const cards = [...document.querySelectorAll('#live-grid .car-card[data-vkey]')].map(c => c.dataset.vkey);
  const cars = cards.map(k => liveInventory.find(v => vehicleKey(v) === k)).filter(Boolean);
  return {
    make: document.getElementById('live-filter-make').value,
    models: [...selectedModels],
    yrMin: document.getElementById('live-filter-year-min').value,
    yrMax: document.getElementById('live-filter-year-max').value,
    sort: document.getElementById('live-sort').value,
    box: document.getElementById('car-search-input').value,
    note: document.getElementById('car-search-note').hidden ? '' : document.getElementById('car-search-note').textContent,
    stats: document.getElementById('live-stats-bar').innerText.replace(/\s+/g, ' '),
    modelBtn: document.getElementById('live-filter-model-btn').textContent,
    filterCount: document.getElementById('live-filter-count').textContent,
    n: getFilteredLive().length,
    order: getFilteredLive().slice(0, 60).map(v => vehicleKey(v)),
    cards: cards.length,
    notXterra: cars.filter(v => !(v.make === 'Nissan' && canonicalModel(v.make, v.model) === 'Xterra')).length,
    years: cars.map(v => v.year),
    href: location.href,
  };
});
const suggestions = (page) => page.evaluate(() => [...document.querySelectorAll('#car-search-suggest .compare-suggest-item')]
  .map(e => e.querySelector('span').textContent.replace(/\s+/g, ' ').trim()));
const typeIn = async (page, text) => {
  await page.click('#car-search-input');
  await page.fill('#car-search-input', '');
  await page.type('#car-search-input', text, { delay: 20 });
  await page.waitForTimeout(150);
};

try {
  // 1. type "xterra" -> pick -> only Nissan Xterras
  let page = await open();
  await ready(page);
  const before = await state(page);
  const fold = await page.evaluate(() => {
    const r = document.getElementById('car-search-input').getBoundingClientRect();
    return { top: r.top, bottom: r.bottom, vh: innerHeight };
  });
  check('search box is above the fold at 390x844 with a zip set', fold.top >= 0 && fold.bottom <= fold.vh, JSON.stringify(fold));
  await typeIn(page, 'xterra');
  const sx = await suggestions(page);
  check('"xterra" suggests Nissan Xterra first', sx[0] === 'Nissan Xterra', JSON.stringify(sx));
  check('free: no car counts in suggestions (counts are Pro, as in the Make/Model lists)', await page.evaluate(() => !document.querySelector('#car-search-suggest .csi-count')));
  check('free: default sort is FREE_DEFAULT_SORT', before.sort === await page.evaluate(() => FREE_DEFAULT_SORT), before.sort);
  await page.click('#car-search-suggest .compare-suggest-item >> nth=0');
  await page.waitForTimeout(300);
  const picked = await state(page);
  check('pick sets Make = Nissan and Model = Xterra', picked.make === 'Nissan' && picked.models.join() === 'Xterra', JSON.stringify(picked.models));
  check('the list shows only Nissan Xterras', picked.cards > 0 && picked.notXterra === 0, `${picked.cards} cards, ${picked.notXterra} not Xterra`);
  check('the stats bar counts the Xterras', new RegExp(`\\b${picked.n.toLocaleString('en-US')}\\b`).test(picked.stats) && picked.n < before.n, picked.stats);
  check('the box shows the pick', picked.box === 'Nissan Xterra', picked.box);
  check('Filters shows the same pick (model button, filter count)', picked.modelBtn === 'Xterra' && picked.filterCount === '2', `${picked.modelBtn} / ${picked.filterCount}`);
  check('sort unchanged by the pick', picked.sort === before.sort, `${before.sort} -> ${picked.sort}`);
  check('suggestion list closed after the pick', await page.evaluate(() => document.getElementById('car-search-suggest').style.display === 'none'));

  // Same result as Filters -> Make -> Model, in a fresh page.
  const viaFilters = await open();
  await ready(viaFilters);
  await viaFilters.click('#live-filter-toggle');
  await viaFilters.selectOption('#live-filter-make', 'Nissan');
  await viaFilters.click('#live-filter-model-btn');
  await viaFilters.check('#live-filter-model-list input[data-model="Xterra"]');
  await viaFilters.click('#live-filter-model-done');
  await viaFilters.waitForTimeout(300);
  const f = await state(viaFilters);
  check('identical to Filters -> Make -> Model: same cars, same order, same stats', f.n === picked.n && JSON.stringify(f.order) === JSON.stringify(picked.order) && f.stats === picked.stats,
    `filters ${f.n} / search ${picked.n}`);
  check('Filters -> Make -> Model updates the search box too', f.box === 'Nissan Xterra', f.box);
  await viaFilters.close();

  // 2. clear resets make + model
  await page.click('#car-search-clear');
  await page.waitForTimeout(300);
  const cleared = await state(page);
  check('clear resets make + model and lists every car again', cleared.make === '' && cleared.models.length === 0 && cleared.n === before.n && cleared.box === '', JSON.stringify({ make: cleared.make, n: cleared.n, was: before.n }));
  check('clear control hidden once empty', await page.evaluate(() => document.getElementById('car-search-clear').hidden));

  // 3. Enter with one clear match picks it; spelling variants
  await typeIn(page, 'xterra');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(300);
  const entered = await state(page);
  check('Enter on "xterra" picks Nissan Xterra', entered.make === 'Nissan' && entered.models.join() === 'Xterra' && entered.notXterra === 0, JSON.stringify(entered.models));
  for (const [q, want] of [['4 runner', 'Toyota 4Runner'], ['4runner', 'Toyota 4Runner'], ['f150', 'Ford F-150'], ['f-150', 'Ford F-150'], ['cr v', 'Honda CR-V'], ['XTERRA', 'Nissan Xterra']]) {
    await typeIn(page, q);
    const s = await suggestions(page);
    check(`"${q}" suggests ${want} first`, s[0] === want, JSON.stringify(s.slice(0, 4)));
  }
  await typeIn(page, 'qqqzzz');
  check('no match: an honest empty row, no suggestions', (await suggestions(page)).length === 0
    && await page.evaluate(() => /No car called .qqqzzz. within 100.*Parts tab/.test(document.getElementById('car-search-suggest').textContent)));
  await page.keyboard.press('Escape');
  // Arrow keys + Enter pick the highlighted one.
  await typeIn(page, 'nissan');
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('ArrowDown');
  const second = (await suggestions(page))[1];
  await page.keyboard.press('Enter');
  await page.waitForTimeout(300);
  const arrowed = await state(page);
  check('ArrowDown + Enter picks the highlighted suggestion', second && arrowed.box === second, `${second} / ${arrowed.box}`);
  await page.close();

  // 4. deep link with utm params, zip set
  page = await open('?utm_source=reddit&utm_campaign=xterra#cars=Nissan|Xterra|2005-2015');
  await ready(page);
  await page.waitForFunction(() => selectedModels.has('Xterra'), null, { timeout: 30000 });
  await page.waitForTimeout(300);
  const link = await state(page);
  check('#cars=Nissan|Xterra|2005-2015: Make + Model applied', link.make === 'Nissan' && link.models.join() === 'Xterra', JSON.stringify(link.models));
  check('#cars= years applied (2005-2015)', link.yrMin === '2005' && link.yrMax === '2015', `${link.yrMin}-${link.yrMax}`);
  check('#cars= list: only 2005-2015 Nissan Xterras', link.cards > 0 && link.notXterra === 0 && link.years.every(y => y >= 2005 && y <= 2015), JSON.stringify(link.years));
  check('#cars= opens the Cars tab', await page.evaluate(() => document.getElementById('tab-live').classList.contains('active')));
  check('utm params stripped and the hash consumed', !/utm_|#cars=/.test(link.href), link.href);
  check('utm attribution kept', await page.evaluate(() => JSON.parse(localStorage.getItem('ys_utm') || '{}').src === 'reddit'));
  check('#cars= leaves the sort alone', link.sort === before.sort, link.sort);
  // in-app: a #cars= link followed while the app is open
  await page.evaluate(() => { location.hash = '#cars=toyota|4%20runner'; });
  await page.waitForFunction(() => selectedModels.has('4Runner'), null, { timeout: 30000 }).catch(() => {});
  const hc = await state(page);
  check('#cars= while open (hashchange), spelling-insensitive: Toyota 4Runner', hc.make === 'Toyota' && hc.models.join() === '4Runner', JSON.stringify([hc.make, hc.models]));
  await page.close();

  // 5. deep link, no zip yet: banner shows, filters apply once a zip is in
  page = await open('#cars=Nissan|Xterra', { zip: false });
  await page.waitForSelector('#zip-banner-input', { state: 'visible', timeout: 60000 });
  const pre = await state(page);
  check('no zip: the zip banner shows', await page.isVisible('#zip-banner'));
  check('no zip: box prefilled with the link\'s car', pre.box === 'Nissan Xterra', pre.box);
  check('no zip: a note says to enter a zip', /zip/i.test(pre.note), pre.note);
  await page.fill('#zip-banner-input', '95112');
  await page.click('#zip-banner-go');
  await ready(page);
  await page.waitForFunction(() => selectedModels.has('Xterra'), null, { timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(300);
  const post = await state(page);
  check('zip entered: the link\'s filters apply', post.make === 'Nissan' && post.models.join() === 'Xterra' && post.cards > 0 && post.notXterra === 0, JSON.stringify({ make: post.make, models: post.models, cards: post.cards }));
  check('zip entered: the note is gone', post.note === '', post.note);
  await page.close();

  // 6. unknown model / make: every car, box prefilled, honest note
  for (const h of ['#cars=Nissan|Xtera', '#cars=Zzyzx|Roadster|2001-2003']) {
    page = await open(h);
    await ready(page);
    await page.waitForTimeout(400);
    const u = await state(page);
    check(`${h}: no filter, every car listed`, u.make === '' && u.models.length === 0 && u.n === before.n && u.cards > 0, JSON.stringify({ make: u.make, n: u.n }));
    check(`${h}: box prefilled, note shown`, u.box.length > 0 && /right now/.test(u.note), `${u.box} / ${u.note}`);
    check(`${h}: no year filter left behind`, u.yrMin === '' && u.yrMax === '', `${u.yrMin}-${u.yrMax}`);
    await page.close();
  }

  // 7. Pro: the default sort stays smart-profit; counts in suggestions
  page = await open('', { pro: true });
  await ready(page);
  const proBefore = await state(page);
  await typeIn(page, 'xterra');
  const proSugg = await page.evaluate(() => document.querySelector('#car-search-suggest .csi-count') && document.querySelector('#car-search-suggest .csi-count').textContent);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(300);
  const proAfter = await state(page);
  check('Pro: suggestion shows a car count', /\d+ cars?/.test(proSugg || ''), proSugg);
  check('Pro: still Pro, default sort smart-profit, unchanged by the pick', await page.evaluate(() => isPro()) && proBefore.sort === 'smart-profit' && proAfter.sort === proBefore.sort, `${proBefore.sort} -> ${proAfter.sort}`);
  check('Pro: only Nissan Xterras', proAfter.notXterra === 0 && proAfter.cards > 0);
  // The Filters panel says what its Make and Model lists hold (2026-11-13).
  {
    const hint = await page.evaluate(() => {
      const w = document.getElementById('live-scope-hint-wrap');
      const before = { hidden: w.hidden, text: w.textContent.trim() };
      const r = document.getElementById('live-radius'); const was = r.value;
      r.value = '50'; r.dispatchEvent(new Event('change', { bubbles: true }));
      const after = w.textContent.trim();
      r.value = was; r.dispatchEvent(new Event('change', { bubbles: true }));
      return { before, after };
    });
    check('Filters: a line says only makes and models within the distance are listed', !hint.before.hidden && /Only makes and models within \d+\smi are listed/.test(hint.before.text), JSON.stringify(hint.before));
    check('…and it follows the distance setting', /within 50\smi/.test(hint.after), hint.after);
  }
  await page.close();

  check('no page errors', errors.length === 0, errors.join(' | '));
} finally {
  await browser.close();
  server.close();
}
console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
