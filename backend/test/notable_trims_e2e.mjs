/* Browser e2e: notable trims (docs/app.js NOTABLE TRIMS, 2026-11-13).
 *   - a car whose usable VIN trim names one of its model's notable trims
 *     carries a badge with that word; a car of the same model without it,
 *     and a car with no usable trim, carry none; the car screen says it
 *   - Filters -> Trim appears only with exactly one model picked; picking a
 *     trim leaves only cars badged with it, counts in the Filters badge,
 *     says how many cars have no single trim in their VIN data, survives a
 *     re-render (sort change) and resets when the model or make changes
 *   - the search box suggests "Make Model · Trim" for "model trim" text and
 *     the pick sets make, model and trim
 *   - #cars=Make|Model||Trim applies the trim; an unknown trim leaves the
 *     model's cars listed with a note
 *   - without notableTrims in the data (before the first scan that has it):
 *     no badges, no Trim control, no errors
 * The car is picked from the published scan in docs/data (Subaru XT first,
 * else the most common notable trim near the test zip), so it does not
 * depend on one VIN staying on a lot. With no such car the run SKIPS and
 * exits 2 (not a pass).
 * Run: node backend/test/notable_trims_e2e.mjs   (Playwright pre-installed) */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { serveWithNotableTrims } from './notable_trims_fixture.mjs';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const DOCS = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../../docs');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png' };
let inject = true;
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(DOCS, path.normalize(p));
  if (!f.startsWith(DOCS) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' });
  const body = inject ? serveWithNotableTrims(f) : null;
  if (body) res.end(body); else fs.createReadStream(f).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const BASE = `http://127.0.0.1:${server.address().port}/`;

let fails = 0;
const check = (name, ok, d = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + d}`); if (!ok) fails++; };

const browser = await chromium.launch();
const errors = [];
async function open(hash = '', { pro = false } = {}) {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, (r) => r.abort());
  await page.addInitScript(({ pro }) => {
    localStorage.setItem('jh_honesty_ack', '1');
    localStorage.setItem('ys_app_promo', '1');
    localStorage.setItem('jh_zip_coords', JSON.stringify({ '95112': { lat: 37.3485, lng: -121.8863 } }));
    localStorage.setItem('jh_zip', '95112');
    if (pro) { localStorage.setItem('jh_pro', '1'); localStorage.setItem('jh_pro_source', 'account'); }
  }, { pro });
  await page.goto(BASE + hash, { waitUntil: 'domcontentloaded' });
  return page;
}
const ready = (page) => page.waitForFunction(() => typeof liveLoaded !== 'undefined' && liveLoaded
  && !(typeof _inv !== 'undefined' && _inv && !liveComplete && invViewPending())
  && document.querySelector('#live-grid .car-card'), null, { timeout: 180000 });
const state = (page) => page.evaluate(() => {
  const cards = [...document.querySelectorAll('#live-grid .car-card[data-vkey]')];
  const sel = document.getElementById('live-filter-trim');
  const note = document.getElementById('live-filter-trim-note');
  return {
    make: document.getElementById('live-filter-make').value,
    models: [...selectedModels],
    trimShown: !document.getElementById('live-filter-trim-wrap').hidden
      && getComputedStyle(document.getElementById('live-filter-trim-wrap')).display !== 'none',
    trimValue: sel.value,
    trimOptions: [...sel.options].map(o => o.textContent),
    note: note.hidden ? '' : note.textContent,
    filterCount: document.getElementById('live-filter-count').textContent,
    countShown: document.getElementById('live-filter-count').style.display !== 'none',
    n: getFilteredLive().length,
    cards: cards.length,
    badges: cards.map(c => (c.querySelector('.badge-trim') || {}).textContent || ''),
    box: document.getElementById('car-search-input').value,
    searchNote: document.getElementById('car-search-note').hidden ? '' : document.getElementById('car-search-note').textContent,
    sort: document.getElementById('live-sort').value,
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
const pickModel = async (page, make, model) => {
  await page.selectOption('#live-filter-make', make);
  await page.click('#live-filter-model-btn');
  await page.check(`#live-filter-model-list input[data-model="${model.replace(/"/g, '\\"')}"]`);
  await page.click('#live-filter-model-done');
  await page.waitForTimeout(300);
};

let skipped = '';
try {
  let page = await open();
  await ready(page);
  // The car under test, from the cars in range (_scopedVehicles): a
  // notable-trim car of the most common make/model + trim, Subaru XT first.
  const pick = await page.evaluate(() => {
    const groups = new Map();
    for (const v of _scopedVehicles) {
      const w = notableTrimOf(v);
      if (!w || isNoPickModel(v.make, v.model)) continue;
      const model = canonicalModel(v.make, v.model);
      const k = v.make + '|' + model + '|' + w;
      const g = groups.get(k) || { make: v.make, model, word: w, n: 0, key: vehicleKey(v) };
      g.n++; groups.set(k, g);
    }
    const all = [...groups.values()];
    // The model must also have cars WITHOUT the badge (usable + unusable)
    // so the negatives are on the same filtered list.
    const has = (g, f) => _scopedVehicles.some(v => v.make === g.make && canonicalModel(v.make, v.model) === g.model && f(v));
    const ok = all.filter(g => has(g, v => v.vpicTrimQuality === 'usable' && !notableTrimOf(v))
      && has(g, v => v.vpicTrimQuality !== 'usable'));
    const rank = (g) => (g.make === 'Subaru' && g.word === 'XT' ? 1e6 : 0) + g.n;
    ok.sort((a, b) => rank(b) - rank(a));
    return { pick: ok[0] || null, groups: all.length, cars: all.reduce((s, g) => s + g.n, 0) };
  });
  if (!pick.pick) {
    skipped = `no make/model in range of 95112 has notable-trim cars plus cars without (groups=${pick.groups})`;
    throw new Error('SKIP');
  }
  const P = pick.pick;
  console.log(`car under test: ${P.make} ${P.model} · ${P.word} (${P.n} in range; ${pick.cars} badged cars in range overall)`);

  // 1. Badges on the Cars list (model filtered so every car is rendered)
  const before = await state(page);
  check('Trim control hidden with no model picked', !before.trimShown);
  await page.click('#live-filter-toggle');
  await page.selectOption('#live-filter-make', P.make);
  await page.waitForTimeout(200);
  check('Trim control hidden with only a make picked', !(await state(page)).trimShown);
  await pickModel(page, P.make, P.model);
  const m1 = await state(page);
  check('Trim control appears with exactly one model picked', m1.trimShown, JSON.stringify(m1.trimOptions));
  check('Trim options: "Any trim" first, then the notable trims present', m1.trimOptions[0] === 'Any trim' && m1.trimOptions.includes(P.word), JSON.stringify(m1.trimOptions));
  check('free: no car counts in the Trim options', m1.trimOptions.every(o => !/\(\d+\)/.test(o)), JSON.stringify(m1.trimOptions));
  const cardFacts = await page.evaluate((P) => {
    const out = { badged: null, plain: null, unusable: null };
    for (const c of document.querySelectorAll('#live-grid .car-card[data-vkey]')) {
      const v = liveInventory.find(x => vehicleKey(x) === c.dataset.vkey);
      if (!v) continue;
      const b = (c.querySelector('.badge-trim') || {}).textContent || '';
      if (!out.badged && notableTrimOf(v) === P.word) out.badged = { trim: v.vpicTrim, badge: b, key: c.dataset.vkey };
      if (!out.plain && v.vpicTrimQuality === 'usable' && !notableTrimOf(v)) out.plain = { trim: v.vpicTrim, badge: b };
      if (!out.unusable && v.vpicTrimQuality !== 'usable') out.unusable = { trim: v.vpicTrim, q: v.vpicTrimQuality, badge: b };
    }
    return out;
  }, P);
  check(`badge "${P.word}" on a ${P.model} whose VIN trim names it`, cardFacts.badged && cardFacts.badged.badge === P.word, JSON.stringify(cardFacts.badged));
  check(`no badge on a ${P.model} with another usable trim`, cardFacts.plain && cardFacts.plain.badge === '', JSON.stringify(cardFacts.plain));
  check(`no badge on a ${P.model} with no usable trim`, cardFacts.unusable && cardFacts.unusable.badge === '', JSON.stringify(cardFacts.unusable));

  // 2. Pick the trim
  await page.selectOption('#live-filter-trim', P.word);
  await page.waitForTimeout(300);
  const t1 = await state(page);
  const expect = await page.evaluate((P) => {
    let yes = 0, unknown = 0;
    for (const v of _scopedVehicles) {
      if (v.make !== P.make || canonicalModel(v.make, v.model) !== P.model) continue;
      if (notableTrimHits(v).includes(P.word)) yes++;
      else if (notableTrimMaybe(v, P.word)) unknown++;
    }
    return { yes, unknown };
  }, P);
  check(`Trim = ${P.word}: only cars badged ${P.word} listed`, t1.cards > 0 && t1.badges.every(b => b === P.word), JSON.stringify(t1.badges.slice(0, 12)));
  check(`Trim = ${P.word}: the list holds every such car in range`, t1.n === expect.yes, `${t1.n} listed, ${expect.yes} expected`);
  check('Trim counts in the Filters badge (make + model + trim = 3)', t1.filterCount === '3' && t1.countShown, t1.filterCount);
  if (expect.unknown) {
    check('the panel says how many have no single trim and are not shown',
      new RegExp(`^${expect.unknown.toLocaleString('en-US')} \\S.* (has|have) no single trim in (its|their) VIN data and (is|are) not shown\\.$`).test(t1.note), t1.note);
  } else {
    check('no unknown cars: no note', t1.note === '', t1.note);
  }
  check('the search box shows the trim', t1.box === `${P.make} ${P.model} · ${P.word}`, t1.box);
  // survives a re-render
  await page.selectOption('#live-sort', 'year-desc');
  await page.waitForTimeout(300);
  const t2 = await state(page);
  check('Trim survives a re-render (sort change)', t2.trimValue === P.word && t2.n === t1.n && t2.badges.every(b => b === P.word), `${t2.trimValue} ${t2.n}`);
  // car screen
  await page.click(`#live-grid .car-card[data-vkey] .car-open`);
  await page.waitForTimeout(400);
  const cd = await page.evaluate(() => {
    const t = document.querySelector('.cd-trim');
    return t ? t.textContent.replace(/\s+/g, ' ').trim() : '';
  });
  check(`car screen names the ${P.word} trim`, cd.startsWith(P.word + ' ') && /VIN/.test(cd), cd);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);
  await page.evaluate(() => { if (typeof closeCarDetail === 'function') closeCarDetail(); });

  // 3. Reset on model change, then on make change
  const otherModel = await page.evaluate((P) => [..._modelCounts.keys()].find(m => m !== P.model) || '', P);
  if (otherModel) {
    await page.click('#live-filter-model-btn');
    await page.uncheck(`#live-filter-model-list input[data-model="${P.model.replace(/"/g, '\\"')}"]`);
    await page.check(`#live-filter-model-list input[data-model="${otherModel.replace(/"/g, '\\"')}"]`);
    await page.click('#live-filter-model-done');
    await page.waitForTimeout(300);
    await page.click('#live-filter-model-btn');
    await page.uncheck(`#live-filter-model-list input[data-model="${otherModel.replace(/"/g, '\\"')}"]`);
    await page.check(`#live-filter-model-list input[data-model="${P.model.replace(/"/g, '\\"')}"]`);
    await page.click('#live-filter-model-done');
    await page.waitForTimeout(300);
    const r1 = await state(page);
    check(`Trim resets on a model change (${P.model} -> ${otherModel} -> ${P.model})`, r1.trimValue === '' && r1.filterCount === '2' && r1.n === m1.n, `${r1.trimValue} ${r1.filterCount} ${r1.n}/${m1.n}`);
  } else console.log(`SKIP  model-change reset: ${P.make} has one model in range`);
  await page.selectOption('#live-filter-trim', P.word);
  await page.waitForTimeout(200);
  await page.selectOption('#live-filter-make', '');
  await page.waitForTimeout(200);
  await pickModel(page, P.make, P.model);
  const r2 = await state(page);
  check('Trim resets on a make change', r2.trimValue === '' && r2.n === m1.n, `${r2.trimValue} ${r2.n}`);
  // two models picked: no Trim control
  if (otherModel) {
    await page.click('#live-filter-model-btn');
    await page.check(`#live-filter-model-list input[data-model="${otherModel.replace(/"/g, '\\"')}"]`);
    await page.click('#live-filter-model-done');
    await page.waitForTimeout(300);
    check('Trim control hidden with two models picked', !(await state(page)).trimShown);
  }
  await page.close();

  // 4. Search box: "model trim" suggests Make Model · Trim; Enter picks it
  page = await open();
  await ready(page);
  await typeIn(page, `${P.model} ${P.word}`.toLowerCase());
  const sg = await suggestions(page);
  check(`"${`${P.model} ${P.word}`.toLowerCase()}" suggests ${P.make} ${P.model} · ${P.word} first`, sg[0] === `${P.make} ${P.model} · ${P.word}`, JSON.stringify(sg.slice(0, 4)));
  await page.keyboard.press('Enter');
  await page.waitForTimeout(300);
  const s1 = await state(page);
  check('the pick sets make, model and trim', s1.make === P.make && s1.models.join() === P.model && s1.trimValue === P.word && s1.badges.every(b => b === P.word) && s1.cards > 0,
    JSON.stringify({ make: s1.make, models: s1.models, trim: s1.trimValue }));
  await typeIn(page, P.model.toLowerCase());
  const sg2 = await suggestions(page);
  check('the model alone suggests no trim rows', sg2.every(s => !s.includes('·') || s.endsWith('all models')), JSON.stringify(sg2));
  await page.keyboard.press('Escape');
  await page.close();

  // 5. #cars=Make|Model||Trim
  page = await open(`#cars=${encodeURIComponent(P.make)}|${encodeURIComponent(P.model)}||${encodeURIComponent(P.word.toLowerCase())}`);
  await ready(page);
  await page.waitForFunction((m) => selectedModels.has(m), P.model, { timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(300);
  const l1 = await state(page);
  check(`#cars=${P.make}|${P.model}||${P.word.toLowerCase()}: make, model and trim applied (spelling-insensitive)`,
    l1.make === P.make && l1.models.join() === P.model && l1.trimValue === P.word && l1.badges.every(b => b === P.word) && l1.cards > 0,
    JSON.stringify({ make: l1.make, models: l1.models, trim: l1.trimValue }));
  await page.close();
  page = await open(`#cars=${encodeURIComponent(P.make)}|${encodeURIComponent(P.model)}||Zzq`);
  await ready(page);
  await page.waitForFunction((m) => selectedModels.has(m), P.model, { timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(300);
  const l2 = await state(page);
  check('#cars= with an unknown trim: the model listed, no trim, a note', l2.models.join() === P.model && l2.trimValue === '' && /No Zzq trim/.test(l2.searchNote), JSON.stringify({ trim: l2.trimValue, note: l2.searchNote }));
  await page.close();

  // 6. Pro: counts in the Trim options
  page = await open('', { pro: true });
  await ready(page);
  await page.click('#live-filter-toggle');
  await pickModel(page, P.make, P.model);
  const p1 = await state(page);
  check('Pro: Trim options carry car counts', p1.trimOptions.some(o => o.startsWith(P.word + ' (')), JSON.stringify(p1.trimOptions));
  await page.close();

  // 7. Data without notableTrims (before the first scan that has it)
  inject = false;
  page = await open();
  await ready(page);
  await page.click('#live-filter-toggle');
  await pickModel(page, P.make, P.model);
  const n1 = await state(page);
  check('no notableTrims in the data: no badges', n1.badges.every(b => b === '') && n1.cards > 0, JSON.stringify(n1.badges.filter(Boolean).slice(0, 5)));
  check('no notableTrims in the data: no Trim control', !n1.trimShown);
  await typeIn(page, `${P.model} ${P.word}`.toLowerCase());
  check('no notableTrims in the data: no trim suggestion', (await suggestions(page)).every(s => !s.endsWith('· ' + P.word)));
  await page.close();
  inject = true;

  check('no page errors', errors.length === 0, errors.join(' | '));
} catch (e) {
  if (e.message !== 'SKIP') throw e;
} finally {
  await browser.close();
  server.close();
}
if (skipped) { console.log(`\nSKIPPED (not a pass): ${skipped}`); process.exit(2); }
console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
