/* UI guard: no text is ever cut off, touch targets are >= 44px, text meets
 * WCAG AA contrast. Owner requirement (2026-11-06): "I want no words cut off
 * and I want everything super clean."
 *
 * Serves docs/ locally (no network needed: data comes from docs/data), walks
 * every main screen of the web app (the same code the iOS/Android shells
 * load) at widths 320, 375, 390, 430, 768, 1280, light and dark, 100% and
 * 200% text, and fails on any of:
 *   - a text element with scrollWidth > clientWidth (text wider than its box)
 *   - a computed text-overflow: ellipsis, or -webkit-line-clamp, anywhere
 *   - text clipped by an ancestor with overflow hidden/clip/auto/scroll
 *     (vertical scrolling of a sheet or page is allowed; horizontal is not)
 *   - text past the viewport edge, or a page that scrolls sideways
 *   - an input/select whose value or placeholder is wider than the field
 *   - a tap target smaller than 44x44 CSS px (inline links in a sentence
 *     are exempt, as in WCAG 2.5.8)
 *   - text contrast below 4.5:1 (3:1 for large text), WCAG 1.4.3
 *   - a Pro nudge shown as bare underlined link text (it must be the Pro
 *     box), or a Pro box shown to a Pro user
 *
 * 200% text emulates the OS text-size setting the way Android WebView's
 * textZoom does: every element's computed font-size (and px line-height) is
 * doubled, so px-sized text grows too.
 *
 * Run:  node backend/test/ui_no_truncation.mjs
 * Env:  WIDTHS=390,1280  THEMES=light  ZOOMS=1  SCREENS=results,pro-sheet
 *       SHOTS=<dir>  screenshots of every screen (390 @2x and 1280, light,
 *       plus dark at 390) for design review.
 *       BASE=<url>  test a deployed copy instead of serving docs/.
 * Playwright is pre-installed in this environment (require('playwright')). */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const DOCS = path.join(ROOT, 'docs');
const list = (v, d) => (v ? v.split(',').map(s => s.trim()).filter(Boolean) : d);
const WIDTHS = list(process.env.WIDTHS, ['320', '375', '390', '430', '768', '1280']).map(Number);
const THEMES = list(process.env.THEMES, ['light', 'dark']);
const ZOOMS = list(process.env.ZOOMS, ['1', '2']).map(Number);
const ONLY = list(process.env.SCREENS, null);
const SHOTS = process.env.SHOTS || '';
const ZIP = '95112';

/* ---------- static server for docs/ ---------- */
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json',
  '.woff2': 'font/woff2', '.webp': 'image/webp', '.jpg': 'image/jpeg' };
let BASE = process.env.BASE;
let server;
if (!BASE) {
  server = http.createServer((req, res) => {
    let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    if (p.endsWith('/')) p += 'index.html';
    const f = path.join(DOCS, path.normalize(p));
    if (!f.startsWith(DOCS) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' });
    fs.createReadStream(f).pipe(res);
  });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  BASE = `http://127.0.0.1:${server.address().port}/`;
}

/* scraper/photo_sources.json -> the published `photoSources` (enabled
 * sources with a label and valid patterns), as junkyard_scraper.py's
 * published_photo_sources() writes it into the data files. */
function publishedPhotoSources() {
  const f = JSON.parse(fs.readFileSync(path.join(ROOT, 'scraper/photo_sources.json'), 'utf8'));
  const out = {};
  for (const [key, src] of Object.entries(f.sources || {})) {
    if (!src || src.enabled !== true || typeof src.label !== 'string') continue;
    const pats = (src.patterns || []).filter(p => p && ['code', 'card', 'large'].every(k => typeof p[k] === 'string'))
      .map(p => ({ code: p.code, card: p.card, large: p.large }));
    if (pats.length) out[key] = { label: src.label, host: src.host || '', onCards: src.onCards !== false,
      ...(src.heavy === true ? { heavy: true, approxKB: src.approxKB } : {}), patterns: pats };
  }
  return out;
}

/* Fixture for the "Likely fits" OEM row: the published interchange.json may
 * not carry the lazy OEM layer yet, so the test adds one (the same shape the
 * pf_guards unit test uses) with long part numbers and notes. */
const OEM_FIXTURE = {
  schemaVersion: 1, cat: 'side-mirrors', amGroups: [],
  oemGroups: [{
    id: 'oem:toyota:side-mirrors:L:ui', ns: 'toyota', cat: 'side-mirrors', tier: 'likely', src: 'oem',
    label: 'Toyota catalog',
    note: 'Toyota catalog lists #87910-06470 for both — fits some configurations; verify the number on the part',
    apps: [['Toyota', 'Camry', 1997, 2017], ['Toyota', 'Avalon', 1995, 2018], ['Toyota', 'Corolla', 1998, 2019], ['Toyota', 'Solara', 1999, 2008]],
    pn: ['87910-06470', '87940-06470', '87940-06480', '87940-06490'],
  }],
};

/* ---------- in-page checks ---------- */
const CHECK_FN = () => {
  const out = [];
  const W = innerWidth, H = innerHeight;
  // Per-pass caches: thousands of text nodes share the same ancestors.
  const csCache = new Map();
  const CS = (el) => { let c = csCache.get(el); if (!c) { c = getComputedStyle(el); csCache.set(el, c); } return c; };
  const memo = (fn) => { const m = new Map(); return (el) => { if (!el) return fn(el); if (m.has(el)) return m.get(el); const r = fn(el); m.set(el, r); return r; }; };
  const desc = (el) => {
    let s = el.tagName.toLowerCase();
    if (el.id) s += '#' + el.id;
    const cls = typeof el.className === 'string' ? el.className.trim().split(/\s+/).filter(Boolean).slice(0, 3) : [];
    if (cls.length) s += '.' + cls.join('.');
    return s;
  };
  const ctxOf = (el) => { // nearest ancestor with an id, for a readable path
    let a = el.parentElement;
    while (a && !a.id) a = a.parentElement;
    return a ? '#' + a.id : '';
  };
  const snippet = (t) => t.replace(/\s+/g, ' ').trim().slice(0, 60);
  const add = (kind, el, text, extra = '') => out.push({ kind, el: desc(el), ctx: ctxOf(el), text: snippet(text || el.textContent || ''), extra });
  // A full-screen page (the car screen) covers everything under it.
  const cover = document.querySelector('#photo-viewer.open') || document.querySelector('#car-detail.open');
  const covered = (el) => cover && !cover.contains(el) && !el.closest('#upgrade-sheet, #saved-sheet, #prices-sheet, .watch-toast');
  const visible = (el) => !covered(el) && (el.checkVisibility ? el.checkVisibility({ opacityProperty: true, visibilityProperty: true }) : !!el.getClientRects().length);
  const fixedAnc = memo((el) => (!el || el === document.body) ? null : (CS(el).position === 'fixed' ? el : fixedAnc(el.parentElement)));
  const offscreenFixed = (el) => {
    const f = fixedAnc(el);
    if (!f) return false;
    const r = f.getBoundingClientRect();
    return r.bottom <= 0 || r.top >= H || r.right <= 0 || r.left >= W || r.width === 0 || r.height === 0;
  };
  const srOnly = memo((a) => {
    if (!a || a === document.body) return false;
    const cs = CS(a);
    if ((cs.clip && cs.clip !== 'auto') || (cs.clipPath && cs.clipPath !== 'none')) {
      const r = a.getBoundingClientRect();
      if (r.width <= 2 || r.height <= 2) return true;
    }
    if (a.getAttribute('aria-hidden') === 'true') return true;
    return srOnly(a.parentElement);
  });
  const isInline = (cs) => cs.display === 'inline' || cs.display === 'contents';
  const blockOf = (el) => { let a = el; while (a && isInline(CS(a))) a = a.parentElement; return a; };

  // 1) text-overflow / line-clamp anywhere visible
  for (const el of document.querySelectorAll('body *')) {
    const cs = CS(el);
    if (cs.textOverflow === 'ellipsis' && visible(el) && el.textContent.trim()) add('ellipsis', el);
    const lc = cs.webkitLineClamp || cs.getPropertyValue('-webkit-line-clamp');
    if (lc && lc !== 'none' && visible(el)) add('line-clamp', el);
  }

  // 2) per text node: overflow, clipping, viewport, contrast
  const parse = (c) => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; };
  const over = (top, bot) => ({ r: top.r * top.a + bot.r * (1 - top.a), g: top.g * top.a + bot.g * (1 - top.a), b: top.b * top.a + bot.b * (1 - top.a), a: 1 });
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  const bgOf = memo((el) => { // composite background colours up to the first opaque one
    const stack = [];
    for (let a = el; a; a = a.parentElement) {
      const cs = CS(a);
      if (cs.backgroundImage && cs.backgroundImage !== 'none') return null; // gradient/image: can't judge
      const c = parse(cs.backgroundColor);
      if (c && c.a > 0) { stack.push(c); if (c.a >= 1) break; }
    }
    let base = { r: 255, g: 255, b: 255, a: 1 };
    for (let i = stack.length - 1; i >= 0; i--) base = over(stack[i], base);
    return base;
  });
  const opacityOf = memo((el) => el ? parseFloat(CS(el).opacity) * opacityOf(el.parentElement) : 1);
  const blurred = memo((el) => (!el || el === document.body) ? false : ((CS(el).filter || '').includes('blur') || blurred(el.parentElement)));
  const clipAnc = memo((el) => { // nearest ancestor (or self) whose overflow is not visible
    if (!el || el === document.documentElement) return null;
    const cs = CS(el);
    return (cs.overflowX !== 'visible' || cs.overflowY !== 'visible') ? el : clipAnc(el.parentElement);
  });
  const disabled = (el) => !!el.closest('[disabled],[aria-disabled="true"],fieldset:disabled') || (el.closest('label') && el.closest('label').querySelector(':disabled'));

  const seen = new Set();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walker.nextNode())) {
    if (!n.nodeValue.trim()) continue;
    const el = n.parentElement;
    if (!el || ['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE', 'OPTION', 'TITLE'].includes(el.tagName)) continue;
    if (el.closest('svg')) continue;
    if (!visible(el) || offscreenFixed(el) || srOnly(el)) continue;
    const range = document.createRange(); range.selectNodeContents(n);
    const rects = [...range.getClientRects()].filter(r => r.width > 0 && r.height > 0);
    if (!rects.length) continue;
    const tr = rects.reduce((u, r) => ({ left: Math.min(u.left, r.left), top: Math.min(u.top, r.top), right: Math.max(u.right, r.right), bottom: Math.max(u.bottom, r.bottom) }),
      { left: Infinity, top: Infinity, right: -Infinity, bottom: -Infinity });
    const text = n.nodeValue;
    // (a) the text's block box is narrower than its content
    const blk = blockOf(el);
    if (blk && !seen.has(blk)) {
      seen.add(blk);
      if (blk.scrollWidth > blk.clientWidth + 1 && blk.clientWidth > 0) add('scrollWidth>clientWidth', blk, text, `${blk.scrollWidth}>${blk.clientWidth}`);
    }
    // (b) clipped by an ancestor (horizontal: any non-visible overflow;
    // vertical: hidden/clip only — vertical scrolling is fine)
    for (let a = clipAnc(el); a; a = clipAnc(a.parentElement)) {
      const cs = CS(a);
      const ox = cs.overflowX, oy = cs.overflowY;
      const r = a.getBoundingClientRect();
      const bl = parseFloat(cs.borderLeftWidth), br = parseFloat(cs.borderRightWidth), bt = parseFloat(cs.borderTopWidth), bb = parseFloat(cs.borderBottomWidth);
      const box = { left: r.left + bl, right: r.right - br, top: r.top + bt, bottom: r.bottom - bb };
      if (ox !== 'visible' && (tr.left < box.left - 1 || tr.right > box.right + 1)) { add('clipped-x', el, text, `by ${desc(a)} (${ox})`); break; }
      const outY = tr.top < box.top - 1 || tr.bottom > box.bottom + 1;
      if ((oy === 'auto' || oy === 'scroll') && outY) break;   // scrolled out of view, not clipped
      if ((oy === 'hidden' || oy === 'clip') && outY) { add('clipped-y', el, text, `by ${desc(a)}`); break; }
    }
    // (c) past the viewport edge
    if (tr.right > W + 1 || tr.left < -1) add('offscreen-x', el, text, `${Math.round(tr.left)}..${Math.round(tr.right)} of ${W}`);
    // (d) contrast
    // WCAG 1.4.3 exempts logotypes: the stencil wordmark keeps its brand orange.
    if (!blurred(el) && !disabled(el) && !el.closest('header h1')) {
      const cs = CS(el);
      const fg = parse(cs.color); const bg = bgOf(el);
      if (fg && bg) {
        const op = opacityOf(el);
        const eff = over({ ...fg, a: fg.a * op }, bg);
        const px = parseFloat(cs.fontSize), bold = parseInt(cs.fontWeight, 10) >= 700;
        const large = px >= 24 || (bold && px >= 18.66);
        const cr = ratio(eff, bg);
        if (cr < (large ? 3 : 4.5) - 0.01) add('contrast', el, text, `${cr.toFixed(2)}:1 ${cs.color} on rgb(${bg.r | 0},${bg.g | 0},${bg.b | 0})`);
      }
    }
  }
  if (document.documentElement.scrollWidth > W + 1) out.push({ kind: 'page-hscroll', el: 'html', ctx: '', text: '', extra: `${document.documentElement.scrollWidth}>${W}` });

  // 3) form fields: value / placeholder must fit
  const cv = document.createElement('canvas').getContext('2d');
  for (const f of document.querySelectorAll('input:not([type=checkbox]):not([type=radio]):not([type=hidden]), select, textarea')) {
    if (!visible(f) || offscreenFixed(f) || srOnly(f)) continue;
    const cs = getComputedStyle(f);
    const t = f.tagName === 'SELECT' ? (f.selectedOptions[0] ? f.selectedOptions[0].textContent : '') : (f.value || f.placeholder || '');
    if (!t.trim() || f.tagName === 'TEXTAREA') continue;
    cv.font = `${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
    const need = cv.measureText(t.trim()).width;
    const avail = f.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight) - (f.tagName === 'SELECT' && cs.appearance !== 'none' ? 20 : 0);
    if (need > avail + 1) add('field-text-cut', f, t, `${Math.round(need)}>${Math.round(avail)}`);
    if (!f.value && f.placeholder && f.tagName === 'INPUT' && !disabled(f)) {
      const pc = parse(getComputedStyle(f, '::placeholder').color), bg = bgOf(f);
      if (pc && bg) { const cr = ratio(over(pc, bg), bg); if (cr < 4.49) add('contrast', f, f.placeholder, `placeholder ${cr.toFixed(2)}:1`); }
    }
  }

  // 4) touch targets
  const TARGETS = 'a[href], button, input:not([type=hidden]), select, textarea, summary, [role=button], [role=link], [role=tab], [role=switch], [role=checkbox]';
  for (const t of document.querySelectorAll(TARGETS)) {
    if (!visible(t) || offscreenFixed(t) || srOnly(t) || disabled(t)) continue;
    let box = t;
    if (t.matches('input[type=checkbox], input[type=radio]') && t.closest('label')) box = t.closest('label');
    else if (t.matches('input[type=checkbox], input[type=radio]') && t.id && document.querySelector(`label[for="${t.id}"]`)) box = document.querySelector(`label[for="${t.id}"]`);
    const cs = getComputedStyle(t);
    if (cs.display === 'inline' && t.parentElement) { // a link inside a sentence
      const own = t.textContent.trim().length, par = t.parentElement.textContent.trim().length;
      if (par > own + 12) continue;
    }
    const r = box.getBoundingClientRect();
    if (r.width < 43.5 || r.height < 43.5) add('target<44', t, t.textContent || t.getAttribute('aria-label') || t.title || t.placeholder || '', `${Math.round(r.width)}x${Math.round(r.height)}`);
  }
  // A Pro nudge is always the Pro box, never bare underlined link text, and
  // Pro users never see a Pro box.
  for (const t of document.querySelectorAll('a, button, [role=button], .linklike, .lock-text, .lock-chip')) {
    if (!t.getClientRects().length || covered(t) || getComputedStyle(t).visibility === 'hidden' || t.closest('.pro-box, #upgrade-sheet, .sheet, header')) continue;
    if (!/\bPro\b/.test(t.textContent || '')) continue;
    if (/underline/.test(getComputedStyle(t).textDecorationLine)) add('bare-pro-link', t, t.textContent);
  }
  if (localStorage.getItem('jh_pro') === '1') for (const b of document.querySelectorAll('.pro-box')) if (b.getClientRects().length && !covered(b) && getComputedStyle(b).visibility !== 'hidden') add('pro-box-for-pro', b, b.textContent);
  return out;
};

/* Double every element's computed font-size (and px line-height); undo restores. */
const ZOOM_FN = (on) => {
  if (on) {
    const els = [...document.querySelectorAll('html, body, body *')];
    const orig = els.map(el => { const cs = getComputedStyle(el); return [cs.fontSize, cs.lineHeight]; });
    window.__z = els.map((el, i) => [el, el.style.getPropertyValue('font-size'), el.style.getPropertyPriority('font-size'), el.style.getPropertyValue('line-height'), el.style.getPropertyPriority('line-height')]);
    els.forEach((el, i) => {
      const [fs, lh] = orig[i];
      el.style.setProperty('font-size', parseFloat(fs) * 2 + 'px', 'important');
      if (lh.endsWith('px')) el.style.setProperty('line-height', parseFloat(lh) * 2 + 'px', 'important');
    });
  } else if (window.__z) {
    for (const [el, fs, fsp, lh, lhp] of window.__z) {
      el.style.removeProperty('font-size'); el.style.removeProperty('line-height');
      if (fs) el.style.setProperty('font-size', fs, fsp); if (lh) el.style.setProperty('line-height', lh, lhp);
    }
    window.__z = null;
  }
};

/* ---------- screens ---------- */
const settle = (page, ms = 250) => page.waitForTimeout(ms);
const resetUi = async (page) => {
  await page.evaluate(() => {
    for (const f of ['hidePhotoViewer', 'hideCarDetail', 'closeUpgradeSheet', 'closeSavedSheet', 'closePricesSheet', 'closeYardSheet']) { try { window[f] && window[f](); } catch (e) { /* not open */ } }
    window.scrollTo(0, 0);
  });
};
const tab = async (page, t) => {
  await resetUi(page);
  await page.evaluate((t) => document.querySelector(`.tab[data-tab="${t}"]`).click(), t);
  await settle(page, 400);
  await page.evaluate(() => window.scrollTo(0, 0));
};
const firstKeys = (page, n) => page.evaluate((n) => [...document.querySelectorAll('#live-grid .heart-btn[data-vkey], #live-grid [data-vkey]')].map(b => b.dataset.vkey).filter((k, i, a) => a.indexOf(k) === i).slice(0, n), n);

const likelySearch = async (page) => {
    await tab(page, 'parts');
    await page.selectOption('#pf-year', '2009');
    await page.selectOption('#pf-make', 'Toyota');
    await page.waitForFunction(() => [...document.getElementById('pf-model').options].some(o => o.value === 'Camry'));
    await page.selectOption('#pf-model', 'Camry');
    await page.click('#pf-part');
    await page.fill('#pf-part', 'mirror');
    await page.waitForSelector('#pf-part-suggest [data-cat="side-mirrors"]');
    await page.dispatchEvent('#pf-part-suggest [data-cat="side-mirrors"]', 'mousedown');
    await settle(page, 300);
    if (!(await page.evaluate(() => /Likely fits/.test(document.getElementById('pf-results').textContent)))) await page.click('#pf-go');
    await page.waitForFunction(() => /Likely fits/.test(document.getElementById('pf-results').textContent), null, { timeout: 15000 })
      .catch(() => { throw new Error('part finder: no "Likely fits" OEM row rendered (fixture not picked up)'); });
    await page.evaluate(() => { const r = document.querySelector('.pf-row-card.pf-likely'); if (r) r.scrollIntoView({ block: 'center' }); });
};
const SCREENS = [
  ['results', async (page) => { await tab(page, 'live'); }],
  ['car-card', async (page) => {
    await tab(page, 'live');
    await page.evaluate(() => {
      document.querySelectorAll('#live-grid details').forEach((d, i) => { if (i < 6) d.open = true; });
      const c = document.querySelector('#live-grid .car-card'); if (c) c.scrollIntoView();
    });
  }],
  ['car-detail', async (page) => {
    await tab(page, 'live');
    const [k] = await firstKeys(page, 1);
    await page.evaluate((k) => {
      if (typeof openCarDetail === 'function') openCarDetail(k);
      else document.querySelectorAll('#live-grid details').forEach(d => { d.open = true; });
    }, k);
    await settle(page, 400);
  }],
  ['car-detail-more', async (page) => {
    // the car with the most parts, "Also on this car" opened
    await tab(page, 'live');
    const k = await page.evaluate(() => {
      let best = null, n = 0;
      for (const c of document.querySelectorAll('#live-grid .car-card[data-vkey]')) {
        const v = liveInventory.find(x => vehicleKey(x) === c.dataset.vkey);
        if (v && v.topParts && v.topParts.length > n) { n = v.topParts.length; best = c.dataset.vkey; }
      }
      return best;
    });
    await page.evaluate((k) => openCarDetail(k), k);
    await settle(page, 300);
    await page.evaluate(() => {
      const d = document.querySelector('#car-detail .also-parts'); if (d) d.open = true;
      const t = document.querySelector('#car-detail .worth-total, #car-detail .worth .parts-lock') || document.querySelector('#car-detail .worth');
      if (t) t.scrollIntoView({ block: 'start' });
    });
  }],
  ['car-detail-more-pro', async (page) => {
    await page.evaluate(() => { localStorage.setItem('jh_pro', '1'); applyProGates(); renderLive(); });
    await tab(page, 'live');
    const k = await page.evaluate(() => {
      let best = null, n = 0;
      for (const c of document.querySelectorAll('#live-grid .car-card[data-vkey]')) {
        const v = liveInventory.find(x => vehicleKey(x) === c.dataset.vkey);
        if (v && v.topParts && v.topParts.length > n) { n = v.topParts.length; best = c.dataset.vkey; }
      }
      return best;
    });
    await page.evaluate((k) => openCarDetail(k), k);
    await settle(page, 300);
    await page.evaluate(() => {
      const d = document.querySelector('#car-detail .also-parts'); if (d) d.open = true;
      const t = document.querySelector('#car-detail .worth-total') || document.querySelector('#car-detail .worth');
      if (t) t.scrollIntoView({ block: 'start' });
    });
  }, async (page) => { await resetUi(page); await page.evaluate(() => { localStorage.removeItem('jh_pro'); applyProGates(); renderLive(); }); }],
  ['photo-card', async (page) => {
    await tab(page, 'live');
    await page.evaluate(() => { const k = photoCarKey('p'); location.hash = '#car=' + encodeURIComponent(k); });
    await settle(page, 800);
    await page.waitForSelector('#live-grid .card-photo img', { timeout: 10000 });
    await page.evaluate(() => window.scrollTo(0, 0));
  }, async (page) => { await page.evaluate(() => { history.replaceState(null, '', location.pathname); window.dispatchEvent(new HashChangeEvent('hashchange')); }); await settle(page, 400); }],
  ['photo-detail', async (page) => {
    await tab(page, 'live');
    await page.evaluate(() => openCarDetail(photoCarKey('https://ik.imagekit.io')));
    await settle(page, 1200);
  }],
  // Heavy source (Sturtevant: camera originals only): the car screen shows a
  // tap-to-load box with the size; the tap loads the original into it. The
  // code is put on a car in view; the image host is answered locally.
  ...[['photo-heavy', false], ['photo-heavy-loaded', true]].map(([name, load]) => [name, async (page) => {
    await tab(page, 'live');
    await page.evaluate(() => {
      const v = liveInventory.find(x => vehicleKey(x) === document.querySelector('#live-grid .car-card[data-vkey]').dataset.vkey);
      vehicleExtras = vehicleExtras || {};
      const ex = vehicleExtras[String(v.id)] || [];
      ex[0] = 'tSTK12345'; vehicleExtras[String(v.id)] = ex;
      if (!photoInfo('tSTK12345') || !photoInfo('tSTK12345').heavy) throw new Error('heavy source not published');
      openCarDetail(vehicleKey(v));
      const box = document.querySelector('#car-detail .photo-heavy');
      if (!box || !/tap to load \(~3\.8\u00a0MB\)/.test(box.textContent)) throw new Error('no tap-to-load box: ' + (box && box.textContent));
      if (document.querySelector('#car-detail .photo-box img')) throw new Error('heavy photo loaded without a tap');
    });
    if (load) {
      await page.click('#car-detail .photo-heavy');
      await page.waitForSelector('#car-detail .photo-box[data-photo-vkey] img', { timeout: 10000 });
    }
    await settle(page, 800);
  }, async (page) => { await page.evaluate(() => { heavyPhotosLoaded.clear(); }); }]),
  ['photo-viewer', async (page) => {
    await tab(page, 'live');
    await page.evaluate(() => { const k = photoCarKey('p'); openCarDetail(k); openPhotoViewer(k); });
    await settle(page, 1200);
  }],
  ['results-pro', async (page) => {
    await page.evaluate(() => { localStorage.setItem('jh_pro', '1'); applyProGates(); renderLive(); });
    await tab(page, 'live');
    await page.evaluate(() => document.querySelectorAll('#live-grid details').forEach((d, i) => { if (i < 6) d.open = true; }));
  }, async (page) => { await page.evaluate(() => { localStorage.removeItem('jh_pro'); applyProGates(); renderLive(); }); }],
  ['car-detail-pro', async (page) => {
    await page.evaluate(() => { localStorage.setItem('jh_pro', '1'); applyProGates(); renderLive(); });
    await tab(page, 'live');
    const [k] = await firstKeys(page, 1);
    await page.evaluate((k) => { if (typeof openCarDetail === 'function') openCarDetail(k); }, k);
    await settle(page, 400);
  }, async (page) => { await resetUi(page); await page.evaluate(() => { localStorage.removeItem('jh_pro'); applyProGates(); renderLive(); }); }],
  ['part-finder', async (page) => { await tab(page, 'parts'); }],
  ['part-finder-likely', likelySearch],
  // Parts tab states (round 4): try chips run real searches near the zip.
  ...[['pf-fit', 'Alternator'], ['pf-hunt', 'Hunt'], ['pf-browse', 'Browse']].map(([name, label]) => [name, async (page) => {
    await tab(page, 'parts');
    await page.evaluate(() => { pfCat = null; document.getElementById('pf-results').innerHTML = ''; pfRenderTry(); });
    await page.waitForSelector('#pf-results .pf-try-chip');
    await page.evaluate((label) => { const c = [...document.querySelectorAll('#pf-results .pf-try-chip')].find(b => b.textContent.trim().startsWith(label)); if (!c) throw new Error('no try chip ' + label); c.click(); }, label);
    await page.waitForFunction(() => document.querySelector('#pf-results .pf-row-card, #pf-results .pf-empty'), null, { timeout: 15000 });
    await settle(page, 400);
  }]),
  ['pf-fit-pro', async (page) => {
    await page.evaluate(() => { localStorage.setItem('jh_pro', '1'); applyProGates(); });
    await tab(page, 'parts');
    await page.evaluate(() => { pfCat = null; document.getElementById('pf-results').innerHTML = ''; pfRenderTry(); });
    await page.waitForSelector('#pf-results .pf-try-chip');
    await page.evaluate(() => [...document.querySelectorAll('#pf-results .pf-try-chip')].find(b => b.textContent.trim().startsWith('Alternator')).click());
    await page.waitForSelector('#pf-results .pf-row-card', { timeout: 15000 });
    await page.evaluate(() => { const r = document.querySelector('#pf-results .pf-row-card'); if (r) r.scrollIntoView({ block: 'start' }); window.scrollBy(0, -90); });
    await settle(page, 400);
  }, async (page) => { await page.evaluate(() => { localStorage.removeItem('jh_pro'); applyProGates(); }); }],
  ['pf-none', async (page) => {
    await tab(page, 'parts');
    await page.selectOption('#pf-year', '1985');
    await page.selectOption('#pf-make', 'Toyota');
    await page.waitForFunction(() => [...document.getElementById('pf-model').options].some(o => o.value));
    await page.evaluate(() => { const m = document.getElementById('pf-model'); m.value = [...m.options].map(o => o.value).filter(Boolean)[0]; m.dispatchEvent(new Event('change', { bubbles: true })); });
    await page.evaluate(() => { pfCat = interchangeData.categories.find(c => c.id === 'side-mirrors'); pfPartInput.value = pfCat.label; pfRunSearch(); });
    await settle(page, 600);
  }],
  ['pf-likely-pro', async (page) => {
    await page.evaluate(() => { localStorage.setItem('jh_pro', '1'); applyProGates(); });
    await likelySearch(page);
  }, async (page) => { await page.evaluate(() => { localStorage.removeItem('jh_pro'); applyProGates(); }); }],
  ['alerts', async (page) => { await tab(page, 'alerts'); }],
  ['alerts-hits', async (page) => {
    await tab(page, 'live');
    await page.evaluate(() => {
      const c = document.querySelector('#live-grid .car-card[data-vkey]');
      const v = liveInventory.find(x => vehicleKey(x) === c.dataset.vkey);
      const b = document.createElement('button'); b.dataset.make = v.make; b.dataset.model = v.model;
      watchFromCard(b);   // the card's own quick-watch path (shows the toast too)
    });
    await settle(page, 300);
    await page.evaluate(() => document.querySelector('.tab[data-tab="alerts"]').click());
    await settle(page, 600);
    await page.evaluate(() => { const g = document.getElementById('alert-watchlist'); if (g) g.scrollIntoView(); });
  }],
  // Round 5 (alerts first)
  ['r5-alerts-recap', async (page) => {
    // A free watch made 60 days ago, with the email recap on: matches that
    // landed after it carry the "you'd have known sooner" line.
    await tab(page, 'live');
    await page.evaluate(() => {
      const c = document.querySelector('#live-grid .car-card[data-vkey]');
      const v = liveInventory.find(x => vehicleKey(x) === c.dataset.vkey);
      const when = new Date(Date.now() - 60 * 86400000).toISOString() + '~test01';
      saveWatchlist([...loadWatchlist().filter(e => !String(e.addedAt).endsWith('~test01')), { make: v.make, model: v.model, yrMin: null, yrMax: null, matchOnly: false, radiusMi: 100, addedAt: when }]);
      localStorage.setItem('ys_email_alerts_on', '1');
      renderAlerts();
      document.querySelector('.tab[data-tab="alerts"]').click();
    });
    await settle(page, 500);
    await page.evaluate(() => { const r = document.querySelector('#alert-matches-grid .recap-line'); if (!r) throw new Error('no recap line rendered'); r.closest('.car-card').scrollIntoView({ block: 'start' }); window.scrollBy(0, -90); });
  }, async (page) => { await page.evaluate(() => { saveWatchlist(loadWatchlist().filter(e => !String(e.addedAt).endsWith('~test01'))); localStorage.removeItem('ys_email_alerts_on'); renderAlerts(); }); }],
  ...[['r5-car-life', false], ['r5-car-life-pro', true]].map(([name, pro]) => [name, async (page) => {
    if (pro) await page.evaluate(() => { localStorage.setItem('jh_pro', '1'); applyProGates(); renderLive(); });
    await tab(page, 'live');
    await page.evaluate(() => {
      const keys = [...document.querySelectorAll('#live-grid .car-card[data-vkey]')].map(c => c.dataset.vkey);
      const k = keys.find(k => { const v = liveInventory.find(x => vehicleKey(x) === k); const l = v && lifespanFor(v); return l && l.basis === 'model-here'; });
      if (!k) throw new Error('no car with model-here lifespan in view');
      openCarDetail(k);
    });
    await settle(page, 400);
    await page.evaluate(() => {
      const l = document.querySelector('#car-detail .cd-life'); l.scrollIntoView({ block: 'center' });
      // The next-one button sits on its own full-width line, one text line
      // from 375px up; the Pro box (free only) is stacked under it.
      const btn = l.querySelector('.next-one-btn'), box = l.querySelector('.pro-box');
      if (btn && innerWidth >= 375) {
        const tops = new Set();
        for (const n of btn.childNodes) if (n.nodeType === 3 && n.textContent.trim()) { const rg = document.createRange(); rg.selectNodeContents(n); for (const x of rg.getClientRects()) if (x.width > 1) tops.add(Math.round(x.top)); }
        const lines = tops.size;
        if (lines !== 1) throw new Error(`next-one button text on ${lines} lines at ${innerWidth}px`);
      }
      if (btn && box && box.getBoundingClientRect().top < btn.getBoundingClientRect().bottom - 1) throw new Error('Pro box not stacked under the next-one button');
      if (!localStorage.getItem('jh_pro') && btn && !box) throw new Error('free car screen: no Pro box under the next-one button');
    });
  }, pro ? async (page) => { await resetUi(page); await page.evaluate(() => { localStorage.removeItem('jh_pro'); applyProGates(); renderLive(); }); } : undefined]),
  ['r5-cars-next', async (page) => {
    await tab(page, 'live');
    await page.evaluate(() => { const m = document.getElementById('live-filter-make'); m.value = 'Toyota'; m.dispatchEvent(new Event('change', { bubbles: true })); });
    await settle(page, 500);
    await page.evaluate(() => { const st = document.querySelector('#live-grid .watch-strip'); if (!st) throw new Error('no watch strip'); st.scrollIntoView({ block: 'center' }); });
  }, async (page) => { await page.evaluate(() => { const m = document.getElementById('live-filter-make'); m.value = ''; m.dispatchEvent(new Event('change', { bubbles: true })); }); await settle(page, 300); }],
  ['pull-sheet', async (page) => {
    await tab(page, 'live');
    const ks = await firstKeys(page, 3);
    await page.evaluate((ks) => { for (const k of ks) if (!savedCars[k]) toggleSaved(k); renderLive(); openSavedSheet(); }, ks);
    await settle(page, 400);
  }],
  ['pro-sheet', async (page) => {
    await resetUi(page);
    await page.evaluate(() => openUpgradeSheet('header-pill'));
    await settle(page, 400);
  }],
  ['pro-sheet-bottom', async (page) => {
    await resetUi(page);
    await page.evaluate(() => { openUpgradeSheet('header-pill'); const s = document.getElementById('upgrade-sheet'); s.scrollTop = s.scrollHeight; });
    await settle(page, 400);
  }],
  ['pro-sheet-car', async (page) => {
    await tab(page, 'live');
    const [k] = await firstKeys(page, 1);
    await page.evaluate((k) => openUpgradeSheet('card-value', encodeURIComponent(k)), k);
    await settle(page, 400);
  }],
  ['yards', async (page) => { await tab(page, 'yards'); }],
  ['yard-prices', async (page) => {
    await tab(page, 'yards');
    await page.evaluate(() => { const c = document.querySelector('#yards-grid .yard-card'); openYardPrices(c.dataset.loc); });
    await settle(page, 800);
  }],
  ['empty', async (page) => {
    await tab(page, 'live');
    await page.evaluate(() => {
      const s = document.getElementById('live-filter-year-min');
      const o = [...s.options].map(o => o.value).filter(Boolean).sort().pop();
      s.value = o; s.dispatchEvent(new Event('change', { bubbles: true }));
      const m = document.getElementById('live-filter-make');
      const mk = [...m.options].map(o => o.value).find(v => v && /^[A-Z]/.test(v) && v.length > 3);
      m.value = mk; m.dispatchEvent(new Event('change', { bubbles: true }));
      document.getElementById('live-filter-year-max').value = o;
      document.getElementById('live-filter-year-max').dispatchEvent(new Event('change', { bubbles: true }));
    });
    await settle(page, 500);
  }, async (page) => {
    await page.evaluate(() => {
      for (const id of ['live-filter-year-min', 'live-filter-year-max', 'live-filter-make']) { const s = document.getElementById(id); s.value = ''; s.dispatchEvent(new Event('change', { bubbles: true })); }
    });
    await settle(page, 300);
  }],
];

/* ---------- run ---------- */
const failures = new Map(); // key -> {screen, kind, el, text, extra, configs:Set}
let passes = 0;
const record = (screen, cfg, rows) => {
  for (const r of rows) {
    const key = [screen, r.kind, r.ctx, r.el, r.text].join(' | ');
    if (!failures.has(key)) failures.set(key, { screen, ...r, configs: new Set() });
    failures.get(key).configs.add(cfg);
  }
};
async function checkAll(page, screen, width) {
  for (const theme of THEMES) {
    await page.emulateMedia({ colorScheme: theme });
    await page.evaluate((t) => { document.documentElement.dataset.theme = t; }, theme);
    for (const z of ZOOMS) {
      if (z !== 1) await page.evaluate(ZOOM_FN, true);
      await settle(page, 120);
      const rows = await page.evaluate(CHECK_FN);
      if (process.env.DEBUG_IMG) console.log(screen, await page.evaluate(() => [...document.querySelectorAll('.photo-box img')].slice(0, 3).map(i => [i.src.slice(0, 90), i.complete, i.naturalWidth, i.closest('.photo-box').className])));
      if (process.env.DEBUG_WIDE && rows.length) console.log(screen, width, theme, z, await page.evaluate(() => [...document.querySelectorAll('body *')].filter(e => e.getBoundingClientRect().right > innerWidth + 1 && e.getClientRects().length).slice(0, 8).map(e => e.tagName + '.' + e.className + ' ' + Math.round(e.getBoundingClientRect().width))));
      record(screen, `${width}/${theme}/${z * 100}%`, rows);
      passes++;
      if (SHOTS && z === 1 && (width === 390 || width === 1280) && (theme === 'light' || width === 390)) {
        fs.mkdirSync(SHOTS, { recursive: true });
        await page.screenshot({ path: path.join(SHOTS, `${width === 390 ? 'phone' : 'desk'}-${screen}${theme === 'dark' ? '-dark' : ''}.png`) });
      }
      if (z !== 1) await page.evaluate(ZOOM_FN, false);
    }
  }
}

const browser = await chromium.launch();
try {
  for (const width of WIDTHS) {
    const ctx = await browser.newContext({
      viewport: { width, height: width >= 1024 ? 900 : 820 },
      deviceScaleFactor: SHOTS && width === 390 ? 2 : 1,
      hasTouch: width < 1024, isMobile: false,
      serviceWorkers: 'block',
    });
    const page = await ctx.newPage();
    page.on('pageerror', (e) => console.log(`  [pageerror ${width}] ${e.message}`));
    // interchange.json + the lazy OEM fixture for the "Likely fits" row
    await page.route(/data\/interchange\.json(\?|$)/, async (route) => {
      const res = await route.fetch(); const j = await res.json();
      j.oemLazy = { schema: 1, path: 'data/oem/', cats: { 'side-mirrors': { oem: 1, am: 0 } } };
      await route.fulfill({ response: res, json: j });
    });
    await page.route(/data\/oem\/side-mirrors\.json/, (route) => route.fulfill({ json: OEM_FIXTURE }));
    // No third-party calls (API, analytics) except the web fonts, which
    // shape every line break; the zip lookup is answered locally.
    // Chain photo hosts load for real (the photo boxes are measured with
    // their images); everything else stays blocked.
    await page.route(/^https?:\/\/(?!127\.0\.0\.1|fonts\.googleapis\.com|fonts\.gstatic\.com|cdn\.pypapps\.com|storage\.googleapis\.com|www\.kikersupullit\.com|ik\.imagekit\.io|cdn\.shopify\.com|cdn\.row52\.com)/, (route) => route.abort());
    // A heavy source's camera original, answered locally (no 4 MB download).
    await page.route(/^https:\/\/inventory\.sturtevantauto\.com\//, (route) => route.fulfill({ contentType: 'image/png', body: fs.readFileSync(path.join(ROOT, 'docs/icon-512.png')) }));
    // Published photo switch (fail-closed in the app): publish the enabled
    // sources of scraper/photo_sources.json exactly as the scan does.
    const PHOTO_ON = publishedPhotoSources();
    await page.route(/data\/(inv\/manifest|vehicle_extras)\.json(\?|$)/, async (route) => {
      const res = await route.fetch(); const j = await res.json();
      j.photoSources = PHOTO_ON;
      await route.fulfill({ response: res, json: j });
    });
    await page.route(/api\.zippopotam\.us\//, (route) => route.fulfill({ json: { 'post code': ZIP, country: 'United States',
      places: [{ 'place name': 'San Jose', state: 'California', 'state abbreviation': 'CA', latitude: '37.3485', longitude: '-121.8863' }] } }));
    // hold the inventory so the loading state can be checked
    let release; const held = new Promise(r => { release = r; });
    await page.route(/data\/inventory_live\.json/, async (route) => { await held; await route.continue(); });

    // Measure what a person sees once scrolled to it: render every card
    // (content-visibility skips off-screen layout) and finish transitions.
    await page.addInitScript(() => document.addEventListener('DOMContentLoaded', () => {
      const st = document.createElement('style');
      st.textContent = '*,*::before,*::after{content-visibility:visible!important;transition-duration:0s!important;transition-delay:0s!important;animation-duration:0s!important;animation-delay:0s!important}';
      document.head.appendChild(st);
    }));
    await page.addInitScript(() => {
      window.photoCarKey = (prefix) => {
        for (const v of liveInventory) {
          const ex = extrasFor(v);
          if (ex && ex[0] && String(ex[0]).startsWith(prefix) && photoInfo(ex[0])) return vehicleKey(v);
        }
        throw new Error('no car with a ' + prefix + ' photo in the loaded inventory');
      };
    });
    await page.goto(BASE, { waitUntil: 'domcontentloaded' });
    await settle(page, 1200);
    if (!ONLY || ONLY.includes('loading')) await checkAll(page, 'loading', width);
    release();
    await page.waitForSelector('#zip-banner-input', { state: 'visible', timeout: 60000 }).catch(() => {});
    await settle(page, 600);
    if (!ONLY || ONLY.includes('home')) await checkAll(page, 'home', width);
    // enter the zip the way a person does
    if (await page.isVisible('#zip-banner-input')) {
      await page.fill('#zip-banner-input', ZIP);
      await page.click('#zip-banner-go');
    } else {
      await page.evaluate((z) => { const i = document.getElementById('live-zip'); i.value = z; i.dispatchEvent(new Event('change', { bubbles: true })); }, ZIP);
    }
    await page.waitForSelector('#live-grid .car-card', { timeout: 60000 });
    await settle(page, 1500);
    for (const [name, setup, teardown] of SCREENS) {
      if (ONLY && !ONLY.includes(name)) continue;
      try {
        await setup(page);
        await settle(page, 300);
        await checkAll(page, name, width);
      } catch (e) {
        record(name, `${width}`, [{ kind: 'setup-error', el: '', ctx: '', text: '', extra: e.message.split('\n')[0] }]);
      }
      if (teardown) await teardown(page).catch(() => {});
    }
    await ctx.close();
    console.log(`width ${width}: done`);
  }
} catch (e) {
  record('run', 'harness', [{ kind: 'harness-error', el: '', ctx: '', text: '', extra: e.message.split('\n')[0] }]);
} finally {
  await browser.close();
  if (server) server.close();
}

const rows = [...failures.values()];
const byKind = {};
for (const r of rows) byKind[r.kind] = (byKind[r.kind] || 0) + 1;
for (const r of rows.sort((a, b) => (a.screen + a.kind).localeCompare(b.screen + b.kind))) {
  const cfgs = [...r.configs];
  console.log(`FAIL  [${r.screen}] ${r.kind}  ${r.ctx} ${r.el}  "${r.text}"  ${r.extra}  (${cfgs.length} cfg: ${cfgs.slice(0, 4).join(', ')}${cfgs.length > 4 ? ', …' : ''})`);
}
console.log(`\n${passes} checks run; ${rows.length} distinct failures`, JSON.stringify(byKind));
console.log(rows.length ? 'UI CHECK FAILED' : 'ALL PASS');
process.exit(rows.length ? 1 : 0);
