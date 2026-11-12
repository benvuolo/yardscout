/* E2E: a first-time visitor who arrives from a server-rendered page with
 * "Alert me when the next one lands" can set that watch (2026-11-12 funnel
 * audit, two dead ends):
 *   - /car/<vin> -> "Alert me when the next <make model> lands near me"
 *     (/#tab=alerts) landed on a watch form whose Make list was empty, with
 *     no zip field on the tab
 *   - /car/<vin> -> "Open in YardScout" -> the bell answered with a browser
 *     alert, "Set your zip code up top first", on a screen with no zip field
 *
 * The server pages are stood in for by pages with the same links (the real
 * ones are backend/site-proxy/src/share.js); docs/ is answered from disk as
 * https://yardscout.io/, so referrers and hashes behave as in production.
 * Nothing reaches production. A browser dialog anywhere is a failure.
 *
 * Run: node backend/test/share_watch_e2e.mjs   (SHOTS=<dir> for screenshots) */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const DOCS = path.join(ROOT, 'docs');
const SHOTS = process.env.SHOTS || '';
const SITE = 'https://yardscout.io';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json' };
const UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';
const WL = 'yardscout_watchlist';

let failures = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + detail}`); if (!ok) failures++; };

// A real car from the published scan: a VIN, a model with several cars.
const names = JSON.parse(fs.readFileSync(path.join(DOCS, 'data/models.json'), 'utf8')).makes;
const shard = JSON.parse(fs.readFileSync(path.join(DOCS, 'data/inv/shard-00.json'), 'utf8'));
const row = shard.vehicles.find(r => r[1] && String(r[1]).length === 17 && ((names[r[3]] || {})[r[4]] || 0) >= 5);
const CAR = { key: String(row[1]), year: row[2], make: row[3], model: row[4] };
const slug = (v) => String(v).toLowerCase().replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');

// Stand-ins for the server-rendered pages: the same two links share.js renders.
const serverPage = (title, links) => `<!doctype html><meta charset="utf-8"><title>${title}</title><h1>${title}</h1>${links.map(([id, href, text]) => `<p><a id="${id}" href="${href}">${text}</a></p>`).join('')}`;
const PAGES = {
  ['/car/' + CAR.key]: serverPage(`${CAR.year} ${CAR.make} ${CAR.model}`, [
    ['open', `${SITE}/#car=${encodeURIComponent(CAR.key)}`, 'Open in YardScout'],
    ['alert', `${SITE}/#tab=alerts`, `Alert me when the next ${CAR.make} ${CAR.model} lands near me`]]),
  ['/landed/' + slug(CAR.make)]: serverPage(`${CAR.make}: what landed`, [['alert', `${SITE}/#tab=alerts`, `Alert me when a ${CAR.make} I want lands near me`]]),
  '/yard/some-yard': serverPage('A yard', [['alert', `${SITE}/#tab=alerts`, 'Alert me when a car I want lands here']]),
};

const fileFor = (pathname) => {
  let p = decodeURIComponent(pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(DOCS, path.normalize(p));
  return f.startsWith(DOCS) && fs.existsSync(f) && !fs.statSync(f).isDirectory() ? f : null;
};
async function visitor(browser, { storage = null } = {}) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, hasTouch: true, userAgent: UA, serviceWorkers: 'block' });
  const page = await ctx.newPage();
  const dialogs = [], errors = [];
  page.on('dialog', async (d) => { dialogs.push(d.message()); await d.dismiss(); });
  page.on('pageerror', (e) => errors.push(String(e.message).slice(0, 200)));
  await page.route('**/*', (route) => {
    const u = new URL(route.request().url());
    if (/api\.zippopotam\.us/.test(u.hostname)) {
      if (/\/us\/00000$/.test(u.pathname)) return route.fulfill({ status: 404, json: {}, headers: { 'access-control-allow-origin': '*' } });
      return route.fulfill({ json: { places: [{ latitude: '33.4511', longitude: '-112.0783' }] }, headers: { 'access-control-allow-origin': '*' } });
    }
    if (u.hostname === 'yardscout.io') {
      if (PAGES[u.pathname]) return route.fulfill({ contentType: 'text/html', body: PAGES[u.pathname] });
      if (u.pathname === '/api/ent/config') return route.fulfill({ json: { billing: true } });
      const f = fileFor(u.pathname);
      if (f) return route.fulfill({ path: f, contentType: TYPES[path.extname(f)] || 'application/octet-stream' });
      return route.fulfill({ status: 404, body: '' });
    }
    return route.abort();
  });
  await page.addInitScript((storage) => {
    navigator.sendBeacon = () => true;
    if (storage && !sessionStorage.getItem('__seeded')) { for (const [k, v] of Object.entries(storage)) localStorage.setItem(k, v); sessionStorage.setItem('__seeded', '1'); }
    document.addEventListener('DOMContentLoaded', () => {
      const st = document.createElement('style');
      st.textContent = '*,*::before,*::after{transition-duration:0s!important;animation-duration:0s!important;scroll-behavior:auto!important}';
      document.head.appendChild(st);
    });
  }, storage);
  const shot = async (name) => { if (SHOTS) { fs.mkdirSync(SHOTS, { recursive: true }); await page.screenshot({ path: path.join(SHOTS, name + '.png') }); } };
  const watches = () => page.evaluate((k) => JSON.parse(localStorage.getItem(k) || '[]'), WL);
  // From a server page, follow one of its links the way a visitor does.
  const follow = async (from, id) => {
    await page.goto(SITE + from, { waitUntil: 'domcontentloaded' });
    await Promise.all([page.waitForURL((u) => u.pathname === '/'), page.click('#' + id)]);
    await page.waitForFunction(() => typeof liveLoaded !== 'undefined', null, { timeout: 60000 });
  };
  return { ctx, page, dialogs, errors, shot, watches, follow };
}
const cardText = (page) => page.evaluate(() => { const c = document.getElementById('watch-intent'); return c && c.getClientRects().length ? c.innerText.replace(/\s+/g, ' ').trim() : null; });
const makeCount = (page) => page.evaluate(() => document.getElementById('alert-make').options.length - 1);

const browser = await chromium.launch();
try {
  /* ---- 1. /car/<vin> -> "Alert me when the next one lands near me" ---- */
  {
    const v = await visitor(browser);
    await v.follow('/car/' + CAR.key, 'alert');
    check('car page alert link: lands on the Alerts tab', await v.page.evaluate(() => document.getElementById('tab-alerts').classList.contains('active') && location.hash === ''));
    await v.page.waitForFunction((label) => (document.getElementById('watch-intent') || {}).innerText && document.getElementById('watch-intent').innerText.includes(label), `${CAR.make} ${CAR.model}`, { timeout: 30000 })
      .catch(() => {});
    const text = await cardText(v.page);
    check('the card names the car the visitor came for', !!text && text.includes(`Get told when another ${CAR.make} ${CAR.model} lands near you`), String(text));
    check('a zip field is right there (no zip saved)', await v.page.evaluate(() => { const i = document.getElementById('watch-intent-zip'); return !!i && !!i.getClientRects().length && i.getBoundingClientRect().bottom < innerHeight; }));
    await v.page.waitForFunction(() => document.getElementById('alert-make').options.length > 20, null, { timeout: 30000 }).catch(() => {});
    check('the form\'s Make list is filled without any inventory loaded', (await makeCount(v.page)) > 40 && await v.page.evaluate(() => liveInventory.length < 20000), String(await makeCount(v.page)));
    await v.page.waitForFunction((mk) => document.getElementById('alert-make').value === mk, CAR.make, { timeout: 15000 }).catch(() => {});
    check('the form is prefilled with the car\'s make and model', await v.page.evaluate((c) => document.getElementById('alert-make').value === c.make && document.getElementById('alert-model-btn').textContent.trim() === c.model, CAR),
      JSON.stringify(await v.page.evaluate(() => [document.getElementById('alert-make').value, document.getElementById('alert-model-btn').textContent])));
    await v.shot('share_1_car_alert_landing');
    // A wrong zip is answered in the card, not with a dialog; then the real one.
    await v.page.fill('#watch-intent-zip', '123');
    await v.page.click('#watch-intent-go');
    check('an incomplete zip is answered in the card', /5-digit zip/.test(await cardText(v.page) || '') && (await v.watches()).length === 0, String(await cardText(v.page)));
    await v.page.fill('#watch-intent-zip', '00000');
    await v.page.click('#watch-intent-go');
    await v.page.waitForFunction(() => /could not find/i.test(document.getElementById('watch-intent').innerText), null, { timeout: 10000 }).catch(() => {});
    check('a zip that does not exist is answered in the card', /could not find/i.test(await cardText(v.page) || '') && (await v.watches()).length === 0, String(await cardText(v.page)));
    await v.page.fill('#watch-intent-zip', '85003');
    await v.page.click('#watch-intent-go');   // the one tap
    await v.page.waitForFunction((k) => JSON.parse(localStorage.getItem(k) || '[]').length === 1, WL, { timeout: 15000 }).catch(() => {});
    const w = (await v.watches())[0] || {};
    check('zip + one tap creates the watch: that make and model, centred on the zip', w.make === CAR.make && w.model === CAR.model && !w.yrMin && !w.yrMax
      && Math.abs(w.lat - 33.4511) < 0.01 && Math.abs(w.lng + 112.0783) < 0.01 && w.radiusMi > 0, JSON.stringify(w));
    check('the zip is saved for the rest of the app', await v.page.evaluate(() => localStorage.getItem('jh_zip') === '85003'));
    await v.page.waitForFunction(() => { const t = document.getElementById('watch-toast'); return t && t.classList.contains('show'); }, null, { timeout: 5000 }).catch(() => {});
    check('the usual "Watching" confirmation follows, the card is gone, the watch is listed', await v.page.evaluate((c) => /Watching/.test(document.getElementById('watch-toast').innerText)
      && !document.getElementById('watch-intent') && document.getElementById('alert-watchlist').innerText.includes(c.model), CAR), String(await cardText(v.page)));
    await v.shot('share_2_car_alert_watching');
    check('no browser dialog and no page error on the way', v.dialogs.length === 0 && v.errors.length === 0, JSON.stringify([v.dialogs, v.errors]));
    await v.ctx.close();
  }

  /* ---- 2. /car/<vin> -> "Open in YardScout" -> the bell ---- */
  {
    const v = await visitor(browser);
    await v.follow('/car/' + CAR.key, 'open');
    await v.page.waitForSelector('#live-grid .car-card', { timeout: 60000 });
    await v.page.click('#live-grid .car-card .car-open');
    await v.page.waitForSelector('#car-detail.open .watch-btn', { timeout: 15000 });
    await v.page.click('#car-detail.open .watch-btn');
    await v.page.waitForSelector('#watch-toast.show #watch-toast-zip', { timeout: 5000 }).catch(() => {});
    check('shared car, bell, no zip saved: the toast asks for the zip (no dialog)', v.dialogs.length === 0
      && await v.page.evaluate(() => { const i = document.getElementById('watch-toast-zip'); return !!i && !!i.getClientRects().length; }), JSON.stringify(v.dialogs));
    await v.shot('share_3_shared_car_bell_zip');
    await v.page.waitForTimeout(13000);   // other toasts leave after 12 s; this one waits for the answer
    check('the zip prompt does not time out', await v.page.evaluate(() => document.getElementById('watch-toast').classList.contains('show') && !!document.getElementById('watch-toast-zip')));
    await v.page.fill('#watch-toast-zip', '85003');
    await v.page.click('#watch-toast [data-act="zip"]');
    await v.page.waitForFunction((k) => JSON.parse(localStorage.getItem(k) || '[]').length === 1, WL, { timeout: 15000 }).catch(() => {});
    const w = (await v.watches())[0] || {};
    check('zip + one tap in the toast creates the watch for that car\'s model', w.make === CAR.make && w.model === CAR.model && w.radiusMi > 0 && Math.abs(w.lat - 33.4511) < 0.01, JSON.stringify(w));
    check('the bell shows as watching and the toast confirms', await v.page.evaluate(() => document.querySelector('#car-detail .watch-btn').classList.contains('watching') && /Watching/.test(document.getElementById('watch-toast').innerText)));
    check('no browser dialog and no page error on the way', v.dialogs.length === 0 && v.errors.length === 0, JSON.stringify([v.dialogs, v.errors]));
    await v.ctx.close();
  }

  /* ---- 3. a returning visitor (zip saved, watches saved): one tap, nothing rewritten ---- */
  {
    // Stored watches in the shapes the app has written over time (a legacy
    // one without radiusMi among them). They must come through untouched.
    const OLD = JSON.stringify([
      { make: 'Toyota', model: '4Runner', yrMin: 1996, yrMax: 2002, matchOnly: false, addedAt: '2026-09-01T10:00:00.000Z' },
      { make: 'Honda', model: 'Civic', yrMin: null, yrMax: null, matchOnly: true, radiusMi: 100, lat: 33.45, lng: -112.07, driveFilter: '', trimFilter: 'Si', addedAt: '2026-10-02T10:00:00.000Z~abc123' },
    ]);
    const v = await visitor(browser, { storage: { [WL]: OLD, jh_zip: '85003', jh_zip_coords: JSON.stringify({ 85003: { lat: 33.4511, lng: -112.0783 } }), ys_seen: '1' } });
    await v.follow('/car/' + CAR.key, 'alert');
    await v.page.waitForFunction((label) => (document.getElementById('watch-intent') || {}).innerText && document.getElementById('watch-intent').innerText.includes(label), `${CAR.make} ${CAR.model}`, { timeout: 60000 })
      .catch(() => {});
    check('returning visitor: the card offers the car with no zip field', (await cardText(v.page) || '').includes(`${CAR.make} ${CAR.model}`) && await v.page.evaluate(() => !document.getElementById('watch-intent-zip')), String(await cardText(v.page)));
    await v.page.click('#watch-intent-go');
    await v.page.waitForFunction((k) => JSON.parse(localStorage.getItem(k) || '[]').length === 3, WL, { timeout: 15000 }).catch(() => {});
    const list = await v.watches();
    check('one tap adds the watch', list.length === 3 && list[2].make === CAR.make && list[2].model === CAR.model, JSON.stringify(list[2]));
    check('the watches already saved are byte-for-byte what they were (rule 6)', JSON.stringify(list.slice(0, 2)) === OLD, JSON.stringify(list.slice(0, 2)));
    // The same link again: already watching, so no card and nothing added.
    await v.follow('/car/' + CAR.key, 'alert');
    await v.page.waitForTimeout(2500);
    check('following the link again does not offer or add a duplicate', (await cardText(v.page)) === null && (await v.watches()).length === 3);
    check('no browser dialog and no page error on the way', v.dialogs.length === 0 && v.errors.length === 0, JSON.stringify([v.dialogs, v.errors]));
    await v.ctx.close();
  }

  /* ---- 4. /landed/<make> and /yard/<slug>: the form works, the zip is asked for in place ---- */
  {
    const v = await visitor(browser);
    await v.follow('/landed/' + slug(CAR.make), 'alert');
    await v.page.waitForFunction((mk) => document.getElementById('alert-make').value === mk, CAR.make, { timeout: 30000 }).catch(() => {});
    check('make page alert link: the form\'s make is prefilled', await v.page.evaluate((mk) => document.getElementById('alert-make').value === mk, CAR.make));
    check('...and the card asks where to watch, with a zip field', /Where should we watch\?/.test(await cardText(v.page) || '') && await v.page.evaluate(() => !!document.getElementById('watch-intent-zip')), String(await cardText(v.page)));
    // Pick the model in the form and tap Add with no zip yet: the card takes
    // the zip and finishes that same Add.
    await v.page.click('#alert-model-btn');
    await v.page.waitForSelector(`#alert-model-list input[data-model="${CAR.model}"]`, { timeout: 10000 });
    await v.page.check(`#alert-model-list input[data-model="${CAR.model}"]`);
    await v.page.click('#alert-model-done');
    await v.page.click('#alert-add-btn');
    check('Add with no location: no dialog, the card asks for the zip to finish it', v.dialogs.length === 0 && /Add watch/.test(await cardText(v.page) || '') && (await v.watches()).length === 0, JSON.stringify([v.dialogs, await cardText(v.page)]));
    await v.shot('share_4_form_add_needs_zip');
    await v.page.fill('#watch-intent-zip', '85003');
    await v.page.click('#watch-intent-go');
    await v.page.waitForFunction((k) => JSON.parse(localStorage.getItem(k) || '[]').length === 1, WL, { timeout: 15000 }).catch(() => {});
    const w = (await v.watches())[0] || {};
    check('the zip finishes that Add: the watch the visitor set up in the form', w.make === CAR.make && w.model === CAR.model && w.radiusMi > 0 && Math.abs(w.lat - 33.4511) < 0.01, JSON.stringify(w));
    check('no browser dialog and no page error on the way', v.dialogs.length === 0 && v.errors.length === 0, JSON.stringify([v.dialogs, v.errors]));
    await v.ctx.close();

    const y = await visitor(browser);
    await y.follow('/yard/some-yard', 'alert');
    await y.page.waitForFunction(() => document.getElementById('alert-make').options.length > 20, null, { timeout: 30000 }).catch(() => {});
    check('yard page alert link: Make list filled, zip asked for in place, nothing prefilled', (await makeCount(y.page)) > 40 && /Where should we watch\?/.test(await cardText(y.page) || '')
      && await y.page.evaluate(() => document.getElementById('alert-make').value === ''), String(await cardText(y.page)));
    await y.page.fill('#watch-intent-zip', '85003');
    await y.page.click('#watch-intent-go');
    await y.page.waitForFunction(() => !document.getElementById('watch-intent'), null, { timeout: 15000 }).catch(() => {});
    check('setting the zip there clears the card and creates nothing by itself', (await cardText(y.page)) === null && (await y.watches()).length === 0 && await y.page.evaluate(() => localStorage.getItem('jh_zip') === '85003'));
    check('no browser dialog and no page error on the way', y.dialogs.length === 0 && y.errors.length === 0, JSON.stringify([y.dialogs, y.errors]));
    await y.ctx.close();
  }

  /* ---- 5. the #watch= link shape (for the server pages to adopt) ---- */
  {
    const v = await visitor(browser);
    await v.page.goto(`${SITE}/#watch=${encodeURIComponent(`${CAR.make}|${CAR.model}|2007-2011`)}`, { waitUntil: 'domcontentloaded' });
    await v.page.waitForFunction(() => !!document.getElementById('watch-intent'), null, { timeout: 30000 }).catch(() => {});
    check('#watch=make|model|years: Alerts tab, the card names the car and years, the hash is consumed',
      await v.page.evaluate(() => document.getElementById('tab-alerts').classList.contains('active') && location.hash === '') && (await cardText(v.page) || '').includes(`another 2007–2011 ${CAR.make} ${CAR.model}`), String(await cardText(v.page)));
    await v.page.waitForFunction((mk) => document.getElementById('alert-make').value === mk, CAR.make, { timeout: 15000 }).catch(() => {});
    check('...and the form shows the same make, model and years', await v.page.evaluate((c) => document.getElementById('alert-make').value === c.make && document.getElementById('alert-model-btn').textContent.trim() === c.model
      && document.getElementById('alert-yr-min').value === '2007' && document.getElementById('alert-yr-max').value === '2011', CAR));
    await v.page.fill('#watch-intent-zip', '85003');
    await v.page.press('#watch-intent-zip', 'Enter');   // Enter in the zip field is the tap
    await v.page.waitForFunction((k) => JSON.parse(localStorage.getItem(k) || '[]').length === 1, WL, { timeout: 15000 }).catch(() => {});
    const w = (await v.watches())[0] || {};
    check('the watch carries the years from the link', w.make === CAR.make && w.model === CAR.model && w.yrMin === 2007 && w.yrMax === 2011, JSON.stringify(w));
    check('no browser dialog and no page error on the way', v.dialogs.length === 0 && v.errors.length === 0, JSON.stringify([v.dialogs, v.errors]));
    await v.ctx.close();
  }
} catch (e) {
  check('harness ran to the end', false, String(e && e.stack || e).split('\n').slice(0, 4).join(' | '));
} finally {
  await browser.close();
}
console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
