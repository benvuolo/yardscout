/* Browser e2e: a share button on every car card (owner request 2026-11-13).
 * Cars list tiles (feed, 2026-11-16: in a top corner of the picture, the
 * bookmark in the other), Alerts hit cards and Parts donor cards each carry
 * one, at least 44x44 px. On a desktop it copies the car's
 * yardscout.io link; on a phone it opens the system share sheet with that
 * link. Either way it does not open the car screen or change the pull sheet.
 * Run: node backend/test/card_share_e2e.mjs   (Playwright pre-installed) */
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
async function open(opts) {
  const ctx = await browser.newContext(opts);
  await ctx.grantPermissions(['clipboard-read', 'clipboard-write']).catch(() => {});
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(String(e)));
  await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, (r) => r.abort());
  await page.addInitScript(() => {
    localStorage.setItem('jh_honesty_ack', '1');
    localStorage.setItem('jh_zip', '95112');
    localStorage.setItem('jh_zip_coords', JSON.stringify({ '95112': { lat: 37.3485, lng: -121.8863 } }));
    window.__shared = [];
  });
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => typeof liveComplete !== 'undefined' && liveComplete && liveInventory.length > 1000, null, { timeout: 180000 });
  return { page, errs, ctx };
}
const tabTo = async (page, t) => { await page.click(`.tab[data-tab="${t}"]`); await page.waitForTimeout(400); };

try {
  // ---- desktop: copies the link ----
  {
    const { page, errs, ctx } = await open({ viewport: { width: 1280, height: 900 } });
    const info = await page.evaluate(() => {
      const cards = [...document.querySelectorAll('#live-grid .car-card[data-vkey]')];
      const withBtn = cards.filter(c => c.querySelector('.tile-media .card-share')).length;
      const c = cards[0], b = c.querySelector('.card-share'), r = b.getBoundingClientRect();
      return { cards: cards.length, withBtn, key: b.dataset.vkey, same: b.dataset.vkey === c.dataset.vkey, w: r.width, h: r.height, label: b.getAttribute('aria-label') };
    });
    check('Cars: every card has a share button', info.cards > 5 && info.withBtn === info.cards, JSON.stringify(info));
    check('…for that card\'s own car, with an accessible name', info.same && /share/i.test(info.label || ''), JSON.stringify(info));
    check('…at least 44x44 px', info.w >= 43.5 && info.h >= 43.5, `${info.w}x${info.h}`);
    const savedBefore = await page.evaluate(() => localStorage.getItem('yardscout_saved') || localStorage.getItem('jh_saved') || '');
    await page.click('#live-grid .car-card[data-vkey] .card-share');
    await page.waitForTimeout(300);
    const after = await page.evaluate(async () => ({
      clip: await navigator.clipboard.readText().catch(e => 'ERR ' + e),
      detail: !!document.querySelector('#car-detail.open'),
      note: document.querySelector('#live-grid .car-card[data-vkey] .card-share').textContent.trim(),
      saved: localStorage.getItem('yardscout_saved') || localStorage.getItem('jh_saved') || '',
    }));
    check('desktop tap: the car\'s yardscout.io link is on the clipboard', after.clip === 'https://yardscout.io/car/' + encodeURIComponent(info.key), `${after.clip} vs ${info.key}`);
    check('…the button says Copied', /copied/i.test(after.note), after.note);
    check('…the car screen did not open and the pull sheet is unchanged', !after.detail && after.saved === savedBefore, JSON.stringify(after));
    await page.waitForTimeout(1500);
    check('…the icon comes back', await page.evaluate(() => !!document.querySelector('#live-grid .car-card[data-vkey] .card-share svg')));
    // Pull sheet: each yard has an "Hours and directions" link to Maps
    // (the app does not collect yard hours; owner question 2026-11-13).
    {
      await page.click('#live-grid .car-card[data-vkey] .tile-save');
      await page.waitForTimeout(200);
      await page.evaluate(() => openSavedSheet());
      await page.waitForTimeout(300);
      const hl = await page.evaluate(() => {
        const a = document.querySelector('#saved-list .saved-yard-link');
        if (!a) return null;
        const r = a.getBoundingClientRect();
        const yard = document.querySelector('#saved-list .saved-yard-name').textContent.split('·')[0].trim();
        return { href: a.href, text: a.textContent.trim(), h: r.height, target: a.target, yard };
      });
      const firstWord = hl ? hl.yard.split(/[\s-]+/)[0] : '';
      check('pull sheet: a yard has an "Hours and directions" link', !!hl && /Hours and directions/.test(hl.text), JSON.stringify(hl));
      check('…to a Maps search for that yard, in a new tab, at least 44 px tall', !!hl && hl.href.includes('/maps/search/?api=1&query=') && decodeURIComponent(hl.href).includes(firstWord) && hl.target === '_blank' && hl.h >= 43.5, JSON.stringify(hl));
      await page.evaluate(() => { closeSavedSheet(); });
      await page.click('#live-grid .car-card[data-vkey] .tile-save');
      await page.waitForTimeout(200);
    }
    // Yards tab: every yard card has the same link, and tapping it does not
    // open Walk the rows (owner request 2026-11-14).
    {
      await tabTo(page, 'yards');
      const yl = await page.evaluate(() => {
        const cards = [...document.querySelectorAll('#yards-grid .yard-card')];
        const a = cards[0] && cards[0].querySelector('.yard-maps-link');
        const r = a ? a.getBoundingClientRect() : { height: 0 };
        return { cards: cards.length, withLink: cards.filter(c => c.querySelector('.yard-maps-link')).length,
          href: a ? a.href : '', text: a ? a.textContent.trim() : '', h: r.height, target: a ? a.target : '',
          name: cards[0] ? cards[0].dataset.loc : '' };
      });
      check('Yards: every yard card has an "Hours and directions" link', yl.cards > 0 && yl.withLink === yl.cards && /Hours and directions/.test(yl.text), JSON.stringify(yl));
      check('…to a Maps search for that yard, in a new tab, at least 44 px tall', yl.href.includes('/maps/search/?api=1&query=') && decodeURIComponent(yl.href).includes(yl.name.split(/[\s-]+/)[0]) && yl.target === '_blank' && yl.h >= 43.5, JSON.stringify(yl));
      // A click on the link must not also open the rows screen. Stop the
      // navigation itself so the test stays on this page.
      await page.evaluate(() => document.querySelector('#yards-grid .yard-maps-link').addEventListener('click', e => e.preventDefault(), { once: true }));
      await page.click('#yards-grid .yard-card .yard-maps-link');
      await page.waitForTimeout(300);
      check('…and tapping it does not open Walk the rows', !(await page.evaluate(() => !!document.querySelector('#yard-rows.open'))));
      await tabTo(page, 'live');
    }
    // The rest of the tile still opens the car screen.
    await page.click('#live-grid .car-card[data-vkey] .tile-open');
    await page.waitForTimeout(400);
    check('the tile beside it still opens the car screen', await page.evaluate(() => !!document.querySelector('#car-detail.open')));
    await page.evaluate(() => closeCarDetail());
    // Alerts: a watch hit card.
    await page.evaluate(() => {
      const c = document.querySelector('#live-grid .car-card[data-vkey]');
      const v = liveInventory.find(x => vehicleKey(x) === c.dataset.vkey);
      const b = document.createElement('button'); b.dataset.make = v.make; b.dataset.model = v.model;
      watchFromCard(b);
    });
    await tabTo(page, 'alerts');
    const al = await page.evaluate(() => {
      const cards = [...document.querySelectorAll('#tab-alerts .car-card[data-vkey], #tab-alerts article[data-vkey]')].filter(c => c.querySelector('.cc-actions'));
      return { cards: cards.length, withBtn: cards.filter(c => c.querySelector('.cc-actions .card-share')).length };
    });
    check('Alerts: every hit card has a share button', al.cards > 0 && al.withBtn === al.cards, JSON.stringify(al));
    if (al.cards) {
      await page.evaluate(() => navigator.clipboard.writeText('x'));
      await page.click('#tab-alerts .cc-actions .card-share');
      await page.waitForTimeout(300);
      check('…and it copies a car link', /^https:\/\/yardscout\.io\/car\//.test(await page.evaluate(() => navigator.clipboard.readText())));
    }
    // Parts: a donor card.
    await tabTo(page, 'parts');
    let partsOk = true;
    try {
      await page.selectOption('#pf-year', '2009');
      await page.selectOption('#pf-make', 'Toyota');
      await page.waitForFunction(() => [...document.getElementById('pf-model').options].some(o => o.value === 'Camry'), null, { timeout: 15000 });
      await page.selectOption('#pf-model', 'Camry');
      await page.click('#pf-part');
      await page.fill('#pf-part', 'mirror');
      await page.waitForSelector('#pf-part-suggest [data-cat="side-mirrors"]', { timeout: 15000 });
      await page.dispatchEvent('#pf-part-suggest [data-cat="side-mirrors"]', 'mousedown');
      await page.waitForTimeout(400);
      if (!(await page.evaluate(() => !!document.querySelector('#pf-results .pf-row-card')))) await page.click('#pf-go');
      await page.waitForSelector('#pf-results .pf-row-card .cc-actions', { timeout: 20000 });
    } catch (e) { partsOk = false; check('Parts: a donor search rendered', false, String(e).slice(0, 160)); }
    if (partsOk) {
      const pf = await page.evaluate(() => {
        const cards = [...document.querySelectorAll('#pf-results .pf-row-card')].filter(c => c.querySelector('.cc-actions'));
        return { cards: cards.length, withBtn: cards.filter(c => c.querySelector('.cc-actions .card-share')).length };
      });
      check('Parts: every donor card has a share button', pf.cards > 0 && pf.withBtn === pf.cards, JSON.stringify(pf));
      await page.evaluate(() => navigator.clipboard.writeText('x'));
      await page.click('#pf-results .pf-row-card .cc-actions .card-share');
      await page.waitForTimeout(300);
      check('…and it copies a car link', /^https:\/\/yardscout\.io\/car\//.test(await page.evaluate(() => navigator.clipboard.readText())));
    }
    check('desktop: no page errors', errs.length === 0, errs.join(' | '));
    await ctx.close();
  }
  // ---- phone: the system share sheet ----
  {
    const { page, errs, ctx } = await open({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    await page.evaluate(() => { navigator.share = async (d) => { window.__shared.push(d); }; });
    const key = await page.evaluate(() => document.querySelector('#live-grid .car-card[data-vkey] .card-share').dataset.vkey);
    await page.tap('#live-grid .car-card[data-vkey] .card-share');
    await page.waitForTimeout(300);
    const sh = await page.evaluate(() => ({ shared: window.__shared, detail: !!document.querySelector('#car-detail.open') }));
    check('phone tap: the share sheet gets the car\'s link and a title', sh.shared.length === 1 && sh.shared[0].url === 'https://yardscout.io/car/' + encodeURIComponent(key) && /\d{4} /.test(sh.shared[0].title || ''), JSON.stringify(sh.shared));
    check('…and the car screen did not open', !sh.detail);
    const corners = () => page.evaluate(() => [...document.querySelectorAll('#live-grid .car-tile')].slice(0, 6).map(t => {
      const m = t.querySelector('.tile-media .photo-box').getBoundingClientRect(), s = t.querySelector('.tile-share').getBoundingClientRect(), b = t.querySelector('.tile-save').getBoundingClientRect();
      return { s: [s.left - m.left, s.top - m.top, s.width, s.height], b: [m.right - b.right, b.top - m.top, b.width, b.height], mw: m.width, mh: m.height };
    }));
    const inCorners = (cs) => cs.every(c => c.s[0] <= 1 && c.s[1] <= 1 && c.b[0] <= 1 && c.b[1] <= 1 && c.s[2] >= 43.5 && c.s[3] >= 43.5 && c.b[2] >= 43.5 && c.b[3] >= 43.5
      && c.s[2] + c.b[2] <= c.mw && c.s[3] <= c.mh / 2 && c.b[3] <= c.mh / 2);
    const row = await corners();
    check('390 px: share and bookmark each sit in a top corner of the picture, 44 px, apart', row.length > 1 && inCorners(row), JSON.stringify(row.slice(0, 2)));
    check('phone: no page errors', errs.length === 0, errs.join(' | '));
    await ctx.close();
  }
  // ---- 360 px (common Android width): still one line ----
  {
    const { page, ctx } = await open({ viewport: { width: 360, height: 800 }, isMobile: true, hasTouch: true });
    const row = await page.evaluate(() => [...document.querySelectorAll('#live-grid .car-tile')].slice(0, 6).map(t => {
      const m = t.querySelector('.tile-media .photo-box').getBoundingClientRect(), s = t.querySelector('.tile-share').getBoundingClientRect(), b = t.querySelector('.tile-save').getBoundingClientRect();
      return { s: [s.left - m.left, s.top - m.top, s.width, s.height], b: [m.right - b.right, b.top - m.top, b.width, b.height], mw: m.width, mh: m.height };
    }));
    check('360 px: share and bookmark each sit in a top corner of the picture, apart', row.length > 1 && row.every(c => c.s[0] <= 1 && c.s[1] <= 1 && c.b[0] <= 1 && c.b[1] <= 1 && c.s[2] + c.b[2] <= c.mw && c.s[3] <= c.mh / 2), JSON.stringify(row.slice(0, 2)));
    check('…each at least 44 px', row.every(c => c.s[2] >= 43.5 && c.s[3] >= 43.5 && c.b[2] >= 43.5 && c.b[3] >= 43.5), JSON.stringify(row.slice(0, 2)));
    // The bookmark is "Add to pull sheet": the same storage, both ways.
    const k = await page.evaluate(() => document.querySelector('#live-grid .car-tile .tile-save').dataset.vkey);
    await page.tap('#live-grid .car-tile .tile-save');
    await page.waitForTimeout(200);
    const on = await page.evaluate((k) => ({ saved: !!JSON.parse(localStorage.getItem('jh_saved') || '{}')[k], pressed: document.querySelector('#live-grid .car-tile .tile-save').getAttribute('aria-pressed'), detail: !!document.querySelector('#car-detail.open') }), k);
    check('360 px: the bookmark adds the car to the pull sheet (jh_saved), shows it, and opens nothing', on.saved && on.pressed === 'true' && !on.detail, JSON.stringify(on));
    await page.evaluate((k) => openCarDetail(k), k);
    await page.waitForTimeout(300);
    check('…and the car screen\'s button agrees ("On pull sheet")', await page.evaluate(() => /On pull sheet/.test(document.querySelector('#car-detail-actions .pull-btn').textContent)));
    await page.click('#car-detail-actions .pull-btn');
    await page.waitForTimeout(200);
    await page.evaluate(() => closeCarDetail());
    await page.waitForTimeout(300);
    check('…taking it off there clears the tile\'s bookmark', await page.evaluate((k) => !JSON.parse(localStorage.getItem('jh_saved') || '{}')[k] && document.querySelector('#live-grid .car-tile .tile-save').getAttribute('aria-pressed') === 'false', k));
    await ctx.close();
  }
} finally {
  await browser.close();
  server.close();
}
console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
