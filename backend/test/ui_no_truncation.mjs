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
 *   - an input whose value or placeholder is wider than the field, or a
 *     select whose choice cannot fit even wrapped (its longest word)
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
 *       TRIMS_FREE=true|false  serve app.js with NOTABLE_TRIMS_FREE set to that
 *       (unset = as shipped).
 * Playwright is pre-installed in this environment (require('playwright')). */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { notableTrimsFixture } from './notable_trims_fixture.mjs';

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
  const cover = document.querySelector('#photo-viewer.open') || document.querySelector('#car-detail.open') || document.querySelector('#yard-rows.open');
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
    // A select may wrap its choice onto more lines (styles.css: select
    // { white-space: normal; height: auto }), so only its longest word has
    // to fit; an input's value or placeholder stays on one line.
    const wraps = f.tagName === 'SELECT' && cs.whiteSpace === 'normal' && !f.multiple;
    const need = wraps ? Math.max(...t.trim().split(/\s+/).map(w => cv.measureText(w).width)) : cv.measureText(t.trim()).width;
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
// Aftermarket donor cards (hub 2026-11-10): only the checks to make at the
// car sit on the card, the listing's provenance is behind "Why it fits"; no
// such card shows more than 8 lines of warnings at 390px (100% text; 7 today).
const amLinesCheck = async (page) => {
  const am = await page.evaluate(() => [...document.querySelectorAll('#pf-results .pf-row-card')].filter(c => c.querySelector('.pf-src-more-text')).map(c => {
    const w = c.querySelector('.pf-warn'); if (!w) return 0;
    return Math.round(w.getBoundingClientRect().height / parseFloat(getComputedStyle(w).lineHeight));
  }));
  if (process.env.AM_LINES) console.log('AM_LINES', page.viewportSize().width, JSON.stringify(am));
  if (am.length && page.viewportSize().width === 390 && Math.max(...am) > 8) throw new Error(`an aftermarket card shows ${Math.max(...am)} warning lines at 390px (max 8)`);
  return am.length;
};
/* Pro sheet (2026-11-12): the primary button and the price line under it are
 * pinned. On a 390x844, 375x667 and 320x568 screen, at 100% and 200% text,
 * the button's bottom edge and the price line must be inside the viewport
 * without scrolling, and the button must be the thing a tap there hits. */
const FOLD_SIZES = [[390, 844], [375, 667], [320, 568]];
const foldCheck = async (page, label, btnSel, lineSel) => {
  const was = page.viewportSize();
  try {
    for (const [w, h] of FOLD_SIZES) {
      await page.setViewportSize({ width: w, height: h });
      for (const z of [1, 2]) {
        if (z !== 1) await page.evaluate(ZOOM_FN, true);
        await settle(page, 150);
        const m = await page.evaluate(({ btnSel, lineSel }) => {
          const sheet = document.getElementById('upgrade-sheet').getBoundingClientRect();
          const b = document.querySelector(btnSel), l = lineSel ? document.querySelector(lineSel) : null;
          if (!b || !b.getClientRects().length) return { err: 'no visible ' + btnSel };
          const br = b.getBoundingClientRect(), lr = l && l.getClientRects().length ? l.getBoundingClientRect() : null;
          const hit = document.elementFromPoint(br.left + br.width / 2, br.top + br.height / 2);
          return { top: Math.round(br.top), bottom: Math.round(br.bottom), vh: innerHeight, sheetTop: Math.round(sheet.top),
            hit: !!hit && (hit === b || b.contains(hit)), line: lineSel ? (lr ? [Math.round(lr.top), Math.round(lr.bottom)] : null) : 'n/a' };
        }, { btnSel, lineSel });
        if (z !== 1) await page.evaluate(ZOOM_FN, false);
        const at = `${label} at ${w}x${h}, ${z * 100}% text`;
        if (m.err) throw new Error(`${at}: ${m.err}`);
        if (m.bottom > m.vh || m.top < Math.max(0, m.sheetTop)) throw new Error(`${at}: the buy button is not fully on screen (${m.top}..${m.bottom} of ${m.vh})`);
        if (!m.hit) throw new Error(`${at}: something covers the buy button`);
        if (m.line === null) throw new Error(`${at}: no price line under the button`);
        if (Array.isArray(m.line) && (m.line[1] > m.vh || m.line[0] < m.bottom - 1)) throw new Error(`${at}: the price line is not on screen under the button (${m.line[0]}..${m.line[1]} of ${m.vh})`);
      }
    }
  } finally {
    await page.setViewportSize(was);
    await settle(page, 150);
  }
};
/* The app shells' sheet, as refreshNativeIapUi leaves it with the store's
 * intro offer (the shells run this same markup and CSS; IS_NATIVE itself
 * cannot be flipped in a loaded page). The real shells are covered by
 * backend/test/pro_sheet_fold_e2e.mjs. */
const appSheet = async (page, android) => {
  await resetUi(page);
  await page.evaluate((android) => {
    openUpgradeSheet('header-pill');
    document.getElementById('upgrade-form-wrap').style.display = 'none';
    document.getElementById('ent-buy').style.display = 'none';
    document.getElementById('store-buy').style.display = 'none';
    document.getElementById('native-iap').style.display = '';
    document.getElementById('iap-buy').style.display = '';
    const sub = document.getElementById('iap-subscribe');
    const offer = introOfferText({ price: '$8.99', introPrice: '$1.99', introPeriod: '1 month', introCycles: 1 });
    sub.textContent = offer.button;
    let line = document.getElementById('iap-intro');
    if (!line) { line = document.createElement('div'); line.id = 'iap-intro'; line.className = 'iap-intro'; sub.insertAdjacentElement('afterend', line); }
    line.textContent = offer.then;
    const note = document.getElementById('iap-note');
    window.__iapNote = window.__iapNote || note.innerHTML;
    if (android) note.innerHTML = 'Auto-renews monthly through your Google Play account &mdash; cancel anytime in Play Store subscriptions. <a href="privacy.html">Privacy</a> &middot; <a href="terms.html">Terms</a>.';
    refreshUpgradeFoot();
  }, android);
  await settle(page, 300);
};
const appSheetOff = async (page) => {
  await resetUi(page);
  await page.evaluate(() => {
    document.getElementById('upgrade-form-wrap').style.display = '';
    document.getElementById('ent-buy').style.display = '';
    document.getElementById('native-iap').style.display = 'none';
    document.getElementById('iap-buy').style.display = 'none';
    const line = document.getElementById('iap-intro'); if (line) line.remove();
    document.getElementById('iap-subscribe').textContent = 'Subscribe \u2014 $8.99/mo';
    if (window.__iapNote) document.getElementById('iap-note').innerHTML = window.__iapNote;
    applyStoreLinks(WEB_STORE, true);
    refreshUpgradeFoot();
  });
};
const carSearchOff = async (page) => {
  await page.evaluate(() => { carSearchClearAll(); document.getElementById('car-search-input').blur(); });
  await settle(page, 300);
};
const SCREENS = [
  ['results', async (page) => { await tab(page, 'live'); }],
  // Car search (2026-11-12): the suggestion list open, a pick applied, and a
  // #cars= link for a model not in range (the box prefilled + a note).
  ['car-search', async (page) => {
    await tab(page, 'live');
    await page.click('#car-search-input');
    await page.fill('#car-search-input', '');
    await page.type('#car-search-input', 'nissan');
    await settle(page, 200);
    if (!(await page.isVisible('#car-search-suggest .compare-suggest-item'))) throw new Error('no car suggestions for "nissan"');
  }, carSearchOff],
  ['car-search-picked', async (page) => {
    await tab(page, 'live');
    await page.click('#car-search-input');
    await page.fill('#car-search-input', '');
    await page.type('#car-search-input', 'xterra');
    await page.keyboard.press('Enter');
    await settle(page, 400);
    if (await page.evaluate(() => !selectedModels.has('Xterra'))) throw new Error('Enter did not pick Nissan Xterra');
    await page.evaluate(() => window.scrollTo(0, 0));
  }, carSearchOff],
  ['car-search-note', async (page) => {
    await tab(page, 'live');
    await page.evaluate(() => { location.hash = '#cars=Mercedes-Benz|Sprinter%202500%20Long%20Wheelbase%20High%20Roof'; });
    await settle(page, 600);
    if (!(await page.isVisible('#car-search-note'))) throw new Error('no note for a model not in range');
    await page.evaluate(() => window.scrollTo(0, 0));
  }, carSearchOff],
  // Mobile-web store banner (shown on phones only; forced here for each store).
  ...['ios', 'android'].map(pl => ['app-promo-' + pl, async (page) => {
    await tab(page, 'live');
    await page.evaluate((pl) => showAppPromo(pl), pl);
  }, async (page) => { await page.evaluate(() => { document.getElementById('app-promo').style.display = 'none'; }); }]),
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
  // Cards without a list photo draw the car (body style from the published
  // "body" extra, paint from the listed colour). Until the scan publishes
  // "body", the three cards after a real-photo card get fixture body styles
  // (suv; pickup marked as a heavy source, so badged; unknown = generic).
  ['cards-mixed', async (page) => {
    await tab(page, 'live');
    // A natural stretch of the list: a car with its own photo (Pick-n-Pull),
    // then cars with no list photo whose yard lists their colour (iPull-uPull).
    await page.evaluate(() => {
      // A card with its own real photo, then the next three cards: their own
      // colour, a fixture body style, and one marked as a heavy source.
      const all = [...document.querySelectorAll('#live-grid .car-card[data-eid]')];
      const hasImg = (c) => c.firstElementChild && c.firstElementChild.querySelector('img');
      const painted = (c) => { const col = String((vehicleExtras[c.dataset.eid] || [])[1] || ''); return !!col && !/unknown|other/i.test(col); };
      // Prefer a stretch whose next cars list a paint colour (shows the tint).
      const run = (k, n) => all.slice(k + 1, k + 1 + n).length === n && all.slice(k + 1, k + 1 + n).every(x => !hasImg(x) && painted(x));
      let n = 3, i = all.findIndex((c, k) => hasImg(c) && run(k, 3));
      if (i < 0) { n = 2; i = all.findIndex((c, k) => hasImg(c) && run(k, 2)); }
      if (i < 0) throw new Error('no real-photo card followed by photo-less cars with a colour');
      const cards = all.slice(i + 1, i + 1 + n);
      window.__fxOrig = cards.map(c => [c.dataset.eid, vehicleExtras[c.dataset.eid]]);
      const own = (c) => (vehicleExtras[c.dataset.eid] || []).slice();
      // Test fixture only (the app never infers body from a name): the real
      // body style of a few well-known models, else blank (generic drawing).
      const KNOWN = { sedan: /^(3\d\d|5\d\d)i|camry|accord|civic sedan|corolla|altima|sentra|malibu|impala|fusion|taurus|tl$|es ?3\d\d|a4$|jetta|passat|elantra|sonata|optima|maxima|charger|300$/i,
        suv: /^x[1-7]$|rogue|cr-?v|rav4|escape|explorer|pilot|highlander|tahoe|suburban|equinox|4runner|grand cherokee|cherokee|murano|pathfinder|tucson|santa fe|edge|expedition|durango|mdx|rx ?3\d\d/i,
        pickup: /f-?150|silverado|sierra|ram|tacoma|tundra|frontier|ranger|colorado|titan|dakota/i,
        van: /odyssey|sienna|caravan|town & country|quest|sedona|transit|express|savana|econoline/i,
        hatchback: /fit$|yaris|versa note|golf|prius|mazda3 hatch|soul/i, wagon: /outback|forester|v70|wagon/i,
        coupe: /mustang|camaro|350z|370z|miata coupe|tc$/i, convertible: /miata|convertible|roadster/i };
      const bodyOf = (m) => Object.keys(KNOWN).find(k => KNOWN[k].test(m)) || '';
      const vOf = (c) => liveInventory.find(x => vehicleKey(x) === c.dataset.vkey);
      // Fixtures: the first card is marked as a light car-screen-only source
      // ("Photo on car page"), the second as a heavy source ("Photo at yard · tap to
      // load"); neither image shows on a card. Colours are the cars' own.
      window.__fxBody = [];
      // the cards after those two have no photo at all (a picked car can hold a
      // car-screen-only photo, which correctly badges "Photo on car page")
      cards.forEach((c, k) => { const e = own(c); if (k === 0) e[0] = 'https://www.kikersupullit.com/inventory-feed/photos/stock-12345.jpg'; else if (k === 1) e[0] = 'tSTK12345'; else e[0] = ''; e[5] = k < n - 1 ? bodyOf(vOf(c).model) : ''; window.__fxBody.push(e[5] || 'car'); vehicleExtras[c.dataset.eid] = e; });
      window.__mixFirst = all[i].dataset.eid;
      renderLive();
      const grid = [...document.querySelectorAll('#live-grid .car-card[data-eid]')];
      const at = grid.findIndex(c => c.dataset.eid === window.__mixFirst);
      const four = grid.slice(at, at + 1 + n);
      const top = four[0].getBoundingClientRect().top + scrollY - 12, bot = four[n].getBoundingClientRect().bottom + scrollY + 12;
      window.__shotClip = { x: 0, y: Math.max(0, top), width: innerWidth, height: bot - top };
      if (typeof cardPhotoHtml === 'undefined') return;   // an older app (before shots): no checks
      const boxes = four.map(c => c.firstElementChild);
      const want = [['photo-box', 'has-illo'], ...cards.map(() => ['photo-illo'])];
      boxes.forEach((b, k) => { if (!want[k].every(x => b.classList.contains(x))) throw new Error(`card ${k}: ${b.className}`); });
      const badge = (b) => (b && b.querySelector('.illo-badge') || {}).textContent || '';
      if (!/Photo on car page/.test(badge(boxes[1])) || !/Photo at yard · tap to load/.test(badge(boxes[2])) || (boxes[3] && badge(boxes[3]))) throw new Error('badges wrong: ' + boxes.map(badge).join(' | '));
      if (document.querySelector('#live-grid .car-card img[src*="kikersupullit"]')) throw new Error('car-screen-only photo on a card');
      window.__fxBody.forEach((b, k) => { if (!boxes[k + 1].innerHTML.includes(`#illo-${b}"`)) throw new Error(`card ${k + 1}: body ${b} not drawn`); });
      if (document.querySelector('#live-grid .car-card img[src*="sturtevant"]')) throw new Error('heavy photo on a card');
      grid[at].scrollIntoView({ block: 'start' }); window.scrollBy(0, -70);
    });
    await page.waitForFunction(() => [...document.querySelectorAll('#live-grid .car-card img')].slice(0, 1).every(im => im.complete), null, { timeout: 15000 }).catch(() => {});
    await settle(page, 1200);
  }, async (page) => { await page.evaluate(() => { window.__shotClip = null; const sel = document.getElementById('live-filter-location'); sel.value = ''; for (const [k, v] of window.__fxOrig || []) { if (v === undefined) delete vehicleExtras[k]; else vehicleExtras[k] = v; } renderLive(); }); await resetUi(page); }],
  // Lot Map: walk one yard by row (free, Pro, and with pull-sheet cars and a
  // watch match marked), the yards map with pins (MapLibre + OpenFreeMap),
  // a yard's sheet from a pin, and the schematic fallback.
  ...[['yard-rows', false, false], ['yard-rows-pro', true, false], ['yard-rows-marked', false, true]].map(([name, pro, marked]) => [name, async (page) => {
    if (pro) await page.evaluate(() => { localStorage.setItem('jh_pro', '1'); applyProGates(); });
    await tab(page, 'yards');
    await page.evaluate((marked) => {
      setYardsView('list'); renderYards();
      const card = document.querySelector('#yards-grid .yard-card[data-loc]');
      if (!card) throw new Error('no yard card');
      const loc = card.dataset.loc;
      if (marked) {
        const cars = liveInventory.filter(v => v.location === loc && v.row).slice(0, 40);
        window.__fxSaved = cars.slice(3, 5).map(v => vehicleKey(v));
        for (const k of window.__fxSaved) if (!savedCars[k]) toggleSaved(k);
        const w = cars[0];
        window.__fxWatch = new Date().toISOString() + '~yardrows';
        saveWatchlist([...loadWatchlist(), { make: w.make, model: w.model, yrMin: null, yrMax: null, matchOnly: false, radiusMi: 100, addedAt: window.__fxWatch }]);
      }
      card.querySelector('.yard-walk-btn').click();
      const box = document.getElementById('yard-rows-body');
      if (!document.querySelector('#yard-rows.open') || !box.querySelector('.yr-row')) throw new Error('row view did not open');
      if (marked && (!box.querySelector('.yr-item.is-pull') || !box.querySelector('.yr-item.is-watch'))) throw new Error('pull-sheet / watch cars not marked');
      const heads = [...box.querySelectorAll('.yr-row-plate')].map(e => e.textContent.replace('Row', '').trim()).filter(r => r !== '?');
      const sorted = [...heads].sort(compareRows);
      if (heads.join('|') !== sorted.join('|')) throw new Error('rows not in number order: ' + heads.slice(0, 8).join(','));
      if (!localStorage.getItem('jh_pro') && /\$\d/.test(box.textContent)) throw new Error('a value leaked to a free user');
      if (!localStorage.getItem('jh_pro') && !box.querySelector('.yr-pro.pro-box')) throw new Error('free: no Pro box');
      if (marked) { const first = box.querySelector('.yr-item.is-pull, .yr-item.is-watch'); const sec = first.closest('.yr-row'); document.getElementById('yard-rows-scroll').scrollTop = sec.offsetTop - 70; }
    }, marked);
    await settle(page, 600);
  }, async (page) => {
    await page.evaluate(() => {
      hideYardRows();
      for (const k of window.__fxSaved || []) if (savedCars[k]) toggleSaved(k);
      if (window.__fxWatch) saveWatchlist(loadWatchlist().filter(e => e.addedAt !== window.__fxWatch));
      window.__fxSaved = null; window.__fxWatch = null;
      localStorage.removeItem('jh_pro'); applyProGates();
    });
    await resetUi(page);
  }]),
  // Checking cars off mid-walk: row 1 all checked (collapsed), row 2 partly,
  // the progress header; checks never touch the pull sheet or watches.
  ...[['yard-rows-checked', 'top'], ['yard-rows-checked-mid', 'mid']].map(([name, at]) => [name, async (page) => {
    await tab(page, 'yards');
    await page.evaluate((at) => {
      setYardsView('list'); renderYards();
      document.querySelector('#yards-grid .yard-card[data-loc] .yard-walk-btn').click();
      const before = JSON.stringify([savedCars, loadWatchlist()]);
      const secs = [...document.querySelectorAll('#yard-rows-body .yr-row')];
      const keysOf = (sec) => [...sec.querySelectorAll('.yr-check')].map(b => b.dataset.vkey);
      let all = loadYardChecks();
      const r1 = keysOf(secs[0]), r2 = keysOf(secs[1]);
      for (const k of r1) all = checksToggle(all, yardRowsLoc, k, Date.now());
      for (const k of r2.slice(0, Math.max(1, Math.floor(r2.length / 2)))) all = checksToggle(all, yardRowsLoc, k, Date.now());
      saveYardChecks(all); renderYardRows();
      // one real tap through the handler (row 3's first car)
      const s3 = document.querySelectorAll('#yard-rows-body .yr-row')[2];
      s3.querySelector('.yr-check').click();
      const box = document.getElementById('yard-rows-body');
      const done = box.querySelector('.yr-row-done .yr-row-toggle');
      if (!done || !/all seen \(\d+\)/.test(done.textContent)) throw new Error('row 1 did not collapse: ' + (done && done.textContent));
      if (!box.querySelector('.yr-item.is-checked') || !box.querySelector('.yr-item:not(.is-checked)')) throw new Error('no mix of checked and unchecked cars');
      const prog = box.querySelector('.yr-progress').textContent.replace(/\s+/g, ' ');
      const n = r1.length + Math.max(1, Math.floor(r2.length / 2)) + 1;
      if (!new RegExp(`\\b${n} of [\\d,]+ seen`).test(prog)) throw new Error('progress header: ' + prog);
      if (JSON.stringify([savedCars, loadWatchlist()]) !== before) throw new Error('checking touched the pull sheet or watches');
      if (!box.querySelector('.yr-reset') || !/Reset seen/.test(box.querySelector('.yr-reset').textContent)) throw new Error('no "Reset seen"');
      const un = box.querySelector('.yr-item:not(.is-checked)');
      if (!/^Seen$/.test(un.querySelector('.yr-check span').textContent) || !/Pull sheet/.test(un.querySelector('.yr-add').textContent)) throw new Error('button labels: ' + un.querySelector('.yr-act').textContent);
      if (!box.querySelector('.yr-item.is-checked .yr-check[aria-pressed="true"]')) throw new Error('seen state not pressed');
      const sc = document.getElementById('yard-rows-scroll');
      const target = at === 'top' ? box.querySelector('.yr-progress') : box.querySelector('.yr-row:not(.yr-row-done) .yr-item.is-checked').previousElementSibling || box.querySelector('.yr-item.is-checked');
      sc.scrollTop += target.getBoundingClientRect().top - sc.getBoundingClientRect().top - (at === 'top' ? 12 : 120);
    }, at);
    await settle(page, 600);
  }, async (page) => {
    await page.evaluate(() => { saveYardChecks({}); try { localStorage.removeItem('ys_yard_checks'); } catch (e) {} hideYardRows(); });
    await resetUi(page);
  }]),
  // Row-view thumbnails follow the cards: real list photo when the source may
  // show on cards, the drawing otherwise, and a "Photo on car page" / heavy
  // tag when the photo is car-screen only (two fixture codes in row 1).
  ['yard-rows-thumbs', async (page) => {
    await tab(page, 'yards');
    await page.evaluate(() => {
      setYardsView('list'); renderYards();
      const loc = document.querySelector('#yards-grid .yard-card[data-loc]').dataset.loc;
      const cars = liveInventory.filter(x => x.location === loc && x.row).sort((a, b) => compareRows(a.row, b.row));
      const r1 = cars.filter(v => v.row === cars[0].row);
      window.__thOrig = r1.slice(0, 2).map(v => [String(v.id), vehicleExtras[String(v.id)]]);
      const set = (v, code) => { const e = (vehicleExtras[String(v.id)] || []).slice(); e[0] = code; vehicleExtras[String(v.id)] = e; };
      set(r1[0], 'https://www.kikersupullit.com/inventory-feed/photos/stock-12345.jpg');
      set(r1[1], 'tSTK12345');
      openYardRows(loc);
      const box = document.getElementById('yard-rows-body');
      const item = (v) => box.querySelector(`.yr-item[data-vkey="${CSS.escape(vehicleKey(v))}"]`);
      if (!/Photo on car page/.test(item(r1[0]).querySelector('.yr-tag-photo').textContent) || item(r1[0]).querySelector('.yr-thumb img')) throw new Error('car-screen-only source: tag or thumb wrong');
      if (!/tap to load/.test(item(r1[1]).querySelector('.yr-tag-photo').textContent) || item(r1[1]).querySelector('.yr-thumb img')) throw new Error('heavy source: tag or thumb wrong');
      const real = [...box.querySelectorAll('.yr-item')].find(li => li.querySelector('.yr-thumb img'));
      if (real && real.querySelector('.yr-thumb img').getAttribute('loading') !== 'lazy') throw new Error('row thumb not lazy');
      const v = liveInventory.find(x => vehicleKey(x) === (real || {}).dataset?.vkey);
      if (real && !(photoInfo(extrasFor(v)[0]) || {}).onCards) throw new Error('a car-screen-only photo shown as a row thumb');
    });
    await settle(page, 600);
  }, async (page) => { await page.evaluate(() => { for (const [k, e] of window.__thOrig || []) { if (e === undefined) delete vehicleExtras[k]; else vehicleExtras[k] = e; } window.__thOrig = null; hideYardRows(); }); await resetUi(page); }],
  // The long-listed notice in the row view (one car's date moved back 200 days).
  ['yard-rows-long', async (page) => {
    await tab(page, 'yards');
    await page.evaluate(() => {
      setYardsView('list'); renderYards();
      const loc = document.querySelector('#yards-grid .yard-card[data-loc]').dataset.loc;
      const v = liveInventory.filter(x => x.location === loc && x.row).sort((a, b) => compareRows(a.row, b.row))[0];
      window.__llOrig = [v, v.dateAdded];
      v.dateAdded = new Date(Date.now() - 200 * 86400000).toISOString().slice(0, 10);
      openYardRows(loc);
      const it = document.querySelector(`#yard-rows .yr-item[data-vkey="${CSS.escape(vehicleKey(v))}"]`);
      if (!it || !it.querySelector('.yr-long')) throw new Error('no long-listed notice in the row view');
      const sc = document.getElementById('yard-rows-scroll');
      sc.scrollTop += it.getBoundingClientRect().top - sc.getBoundingClientRect().top - 140;
    });
    await settle(page, 500);
  }, async (page) => { await page.evaluate(() => { if (window.__llOrig) { window.__llOrig[0].dateAdded = window.__llOrig[1]; window.__llOrig = null; } hideYardRows(); }); await resetUi(page); }],
  // Yards list: a yard's Premium lot rides on the main yard's card (centre moved
  // to Ogden, UT for the test, then restored).
  ['yards-premium-list', async (page) => {
    await tab(page, 'yards');
    await page.waitForFunction(() => liveInventory.some(v => /^Utah Pic-A-Part - Ogden \(Premium\)/.test(v.location)) && liveInventory.some(v => v.location === 'Utah Pic-A-Part - Ogden'), null, { timeout: 120000 });
    await page.evaluate(() => {
      window.__zc = activeZipCoords; activeZipCoords = { lat: 41.223, lng: -111.97 };
      setYardsView('list'); renderYards();
      const cards = [...document.querySelectorAll('#yards-grid .yard-card')];
      if (cards.some(c => /\(Premium\)\s*$/i.test(c.dataset.loc))) throw new Error('a Premium lot still has its own card');
      const c = cards.find(c => c.querySelector('.yard-premium'));
      if (!c || !/Premium lot · [\d,]+ cars/.test(c.querySelector('.yard-premium').textContent)) throw new Error('no Premium lot line: ' + cards.map(x => x.dataset.loc).slice(0, 12).join(' | '));
      if (!/\(Premium\)/.test(c.querySelector('.yard-premium .yard-walk-btn').dataset.loc)) throw new Error('premium buttons not pointed at the Premium lot');
      c.scrollIntoView({ block: 'start' }); window.scrollBy(0, -80);
    });
    await settle(page, 400);
  }, async (page) => { await page.evaluate(() => { activeZipCoords = window.__zc; renderYards(); }); await resetUi(page); }],
  // A yard with a Premium lot is one site: one pin and both lots in its card.
  // Uses Utah Pic-A-Part (main + Premium share an address) when in the data.
  ['yards-map-premium', async (page) => {
    await tab(page, 'yards');
    await page.waitForFunction(() => liveInventory.some(v => /^Utah Pic-A-Part - Ogden \(Premium\)/.test(v.location)) && liveInventory.some(v => v.location === 'Utah Pic-A-Part - Ogden'), null, { timeout: 120000 });
    // The live map centred on Ogden, UT (the owner's report), then restored.
    await page.evaluate(async () => { window.__zc = activeZipCoords; activeZipCoords = { lat: 41.223, lng: -111.97 }; setYardsView('map'); await renderYardsMap(); });
    await page.waitForFunction(() => window._yardsMap && _yardsMap.loaded() && document.querySelector('#yards-map .map-pin'), null, { timeout: 30000 });
    await page.evaluate(async () => {
      if (_mapSites.some(s => /\(Premium\)/i.test(s.key))) throw new Error('a Premium lot got its own pin');
      const st = _mapSites.find(s => s.key === 'Utah Pic-A-Part - Ogden');
      if (!st || st.lots.length !== 2) throw new Error('Ogden main + Premium not merged');
      if (document.querySelector('#yards-map .map-pin[data-loc*="(Premium)"]')) throw new Error('Premium pin drawn');
      selectMapYard(st.key);
      await new Promise(r => setTimeout(r, 400));
      const card = document.getElementById('ms-body');
      if (!/Main lot · [\d,]+ cars/.test(card.textContent) || !/Premium lot · [\d,]+ cars/.test(card.textContent)) throw new Error('lots not listed');
      if (card.querySelectorAll('.map-walk').length !== 2) throw new Error('each lot needs its own Walk the rows');
      // Same-spot yards: a cluster whose yards share a point lists them (no endless zoom).
      const same = _pinGroups.find(g => g.items.length > 1 && g.items.every(x => siteNear(x, g.items[0])));
      if (same) { zoomToYards(same.items.map(x => x.key)); if (!/yards here/.test(document.getElementById('ms-title').textContent)) throw new Error('same-spot cluster did not list its yards'); selectMapYard(st.key); }
    });
    await settle(page, 600);
  }, async (page) => { await page.evaluate(async () => { _mapSheetLoc = null; activeZipCoords = window.__zc; setYardsView('list'); }); await resetUi(page); }],
  ...[['yards-map', 'gl'], ['yards-map-sheet', 'sheet'], ['yards-map-full', 'full'], ['yards-map-schematic', 'schematic'], ['yards-map-watch', 'watch']].map(([name, mode]) => [name, async (page) => {
    await tab(page, 'yards');
    if (mode === 'watch') await page.evaluate(() => {
      // A watch for a model on a nearby lot: its yard's pin gets the bell badge.
      const y = (getYardsView().shown || [])[0];
      const v = liveInventory.find(x => x.location === y.location && x.model);
      window.__mapWatch = new Date().toISOString() + '~mapwatch';
      saveWatchlist([...loadWatchlist(), { make: v.make, model: v.model, yrMin: null, yrMax: null, matchOnly: false, radiusMi: 100, addedAt: window.__mapWatch }]);
    });
    await page.evaluate(async () => { setYardsView('map'); await renderYardsMap(); });
    if (mode === 'watch') {
      await page.waitForFunction(() => window._yardsMap && _yardsMap.loaded() && document.querySelector('#yards-map .map-pin'), null, { timeout: 30000 });
      await page.evaluate(() => {
        const w = document.querySelector('#yards-map .map-pin.has-watch');
        if (!w || !w.querySelector('.pin-watch svg')) throw new Error('no bell badge on a pin with a watch match');
        if (!/(match(es)?|matching) your watches/.test(w.getAttribute('aria-label'))) throw new Error('watch aria-label: ' + w.getAttribute('aria-label'));
        if (![...document.querySelectorAll('#yards-map .map-pin:not(.map-cluster)')].every(p => / cars$/.test(p.querySelector('.pin-cars').textContent))) throw new Error('a single-yard pin without "N cars"');
        { const lg = document.querySelector('.yards-map-legend'); if (!lg.getClientRects().length || !/matches your watches/.test(lg.textContent)) throw new Error('no watch key with a bell pin'); }
      });
    } else if (mode === 'schematic') {
      await page.evaluate(() => renderSchematicMap((getYardsView().shown || []).filter(y => y.lat != null), 'Map tiles couldn\u2019t load, so yards are shown by position only. The row view works offline.'));
    } else {
      await page.waitForFunction(() => window._yardsMap && _yardsMap.loaded() && document.querySelector('#yards-map .map-pin'), null, { timeout: 30000 });
      await page.waitForFunction(() => _yardsMap.areTilesLoaded(), null, { timeout: 30000 }).catch(() => {});
    }
    await page.evaluate(async (mode) => {
      if (!document.querySelector('#yards-map .map-pin')) throw new Error('no pins');
      if (mode === 'gl' && !/OpenStreetMap/.test(document.querySelector('#yards-map').textContent)) throw new Error('no map attribution');
      // Map mode: the page doesn't scroll; the map fills to the tab bar and the
      // bottom sheet is the one scrolling surface.
      if (!document.documentElement.classList.contains('map-lock')) throw new Error('page not locked in map mode');
      const sheet = document.getElementById('yards-map-sheet');
      if (!sheet || !/\d+ yards? near you/.test(document.getElementById('ms-title').textContent)) throw new Error('no sheet title');
      if (!sheet.querySelector('.ms-row')) throw new Error('no yard rows in the sheet');
      if (mode === 'full') {
        document.getElementById('ms-handle').click();
        if (sheet.dataset.state !== 'full' || document.getElementById('ms-handle').getAttribute('aria-expanded') !== 'true') throw new Error('handle did not expand');
      } else if (mode === 'sheet' || mode === 'schematic') {
        const pin = document.querySelector('#yards-map .map-pin:not(.map-cluster)');
        if (pin) { pin.click(); if (!sheet.querySelector('.map-walk') || !sheet.querySelector('.ms-back')) throw new Error('no yard card in the sheet'); }
        else { selectMapYard(_mapSites[0].key); if (!sheet.querySelector('.map-walk')) throw new Error('no yard card in the sheet'); }
      }
      // Pins: no two overlap, none is drawn whose point is outside the open map,
      // and the credit line stays visible; at the fitted zoom and 2 and 4 steps in.
      const pinCheck = (label) => {
        const pins = [...document.querySelectorAll('#yards-map .pin-layer .map-pin')].map(p => p.getBoundingClientRect());
        for (let i = 0; i < pins.length; i++) for (let j = i + 1; j < pins.length; j++) {
          const a = pins[i], b = pins[j];
          if (a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom) throw new Error(`${label}: two pins overlap`);
        }
        const A = pinArea(), box = document.getElementById('yards-map').getBoundingClientRect();
        _pinGroups.forEach(g => { const p = _projectFn(g.items[0]); if (p.x < 0 || p.x > A.W || p.y < A.t || p.y > A.b) throw new Error(`${label}: a pin drawn with its point off the open map`); });
        const inSheet = document.querySelector('#yards-map.credit-in-sheet');
        if (inSheet) {
          const c = document.querySelector('#yards-map-sheet.with-credit .ms-credit');
          if (!c || !c.getClientRects().length || !/OpenStreetMap/.test(c.textContent)) throw new Error(`${label}: credit line not shown in the sheet`);
        }
        const at = !inSheet && document.querySelector('#yards-map .maplibregl-ctrl-attrib');
        if (at) {
          const ar = at.getBoundingClientRect();
          if (!ar.height || ar.bottom > box.bottom + 1) throw new Error(`${label}: attribution not visible ` + JSON.stringify({ ar: [ar.top, ar.bottom, ar.height], box: [box.top, box.bottom], lift: document.getElementById('yards-map').style.getPropertyValue('--sheet-lift'), sheet: document.getElementById('yards-map-sheet').getBoundingClientRect().top }));
          const covers = [...document.querySelectorAll('#yards-map .map-pin, #saved-pill, #yards-map-sheet')].filter(e => e.getClientRects().length).map(e => e.getBoundingClientRect());
          if (covers.some(r => r.left < ar.right && ar.left < r.right && r.top < ar.bottom && ar.top < r.bottom)) throw new Error(`${label}: something covers the attribution`);
        }
        const ctl = document.querySelector('#yards-map .maplibregl-ctrl-group');
        if (ctl) { const cr = ctl.getBoundingClientRect(); if (pins.some(r => r.left < cr.right && cr.left < r.right && r.top < cr.bottom && cr.top < r.bottom)) throw new Error(`${label}: a pin covers the zoom buttons`); }
        if (getComputedStyle(document.getElementById('saved-pill')).display !== 'none' && document.documentElement.classList.contains('map-lock')) throw new Error('floating pull sheet pill shown over the map');
      };
      await new Promise(r => setTimeout(r, 400));   // the sheet's slide, then the pins re-solve
      pinCheck('fitted');
      if (window._yardsMap && mode === 'gl') {
        const z0 = _yardsMap.getZoom();
        for (const d of [2, 4]) { _yardsMap.jumpTo({ zoom: z0 + d }); layoutPins(); pinCheck('zoom +' + d); }
        _yardsMap.jumpTo({ zoom: z0 }); layoutPins();
      }
      const mr = document.getElementById('yards-map-wrap').getBoundingClientRect(), tabs = document.querySelector('.tabs').getBoundingClientRect();
      if (getComputedStyle(document.querySelector('.tabs')).position === 'fixed' && Math.abs(tabs.top - mr.bottom) > 24) throw new Error(`map does not reach the tab bar: ${mr.bottom} vs ${tabs.top}`);
    }, mode);
    await settle(page, 800);
  }, async (page) => { await page.evaluate(() => { _mapSheetLoc = null; if (window.__mapWatch) { saveWatchlist(loadWatchlist().filter(e => e.addedAt !== window.__mapWatch)); window.__mapWatch = null; } setYardsView('list'); }); await resetUi(page); }]),
  // Listed far past the typical stay (owner report, Pull-N-Save Springville):
  // the bar gives way to a neutral notice on the card and the car screen.
  // One car's set-out date is moved 200 days back for the test, then restored.
  ...[['long-listed-card', false], ['long-listed-detail', true]].map(([name, detail]) => [name, async (page) => {
    await tab(page, 'live');
    await page.evaluate((detail) => {
      const card = document.querySelector('#live-grid .car-card[data-vkey]');
      const v = liveInventory.find(x => vehicleKey(x) === card.dataset.vkey);
      window.__llOrig = [v, v.dateAdded];
      // Deterministic (2026-11-10): back far enough to qualify whatever this
      // yard's typical stay is today (> 2x typical, or >= 120 days with none);
      // a fixed 200 days stopped qualifying once a yard's typical reached 101.
      const ls = lifespanFor(v), back = ls && ls.avg ? 3 * ls.avg + 30 : LONG_LISTED_DAYS + 30;
      const d = new Date(Date.now() - back * 86400000);
      v.dateAdded = d.toISOString().slice(0, 10);
      renderLive();
      const c2 = document.querySelector(`#live-grid .car-card[data-vkey="${CSS.escape(vehicleKey(v))}"]`);
      if (!c2 || !c2.querySelector('.long-listed')) throw new Error('no notice on the card');
      if (c2.querySelector('.stay-meter')) throw new Error('overfull bar still on the card');
      if (!/Listed \d+ days, longer than usual here/.test(c2.textContent)) throw new Error('notice wording');
      if (detail) {
        openCarDetail(vehicleKey(v));
        const b = document.getElementById('car-detail-body');
        if (!b.querySelector('.long-listed') || b.querySelector('.stay-meter')) throw new Error('car screen: notice/bar wrong');
        b.querySelector('.long-listed').scrollIntoView({ block: 'center' });
      } else c2.scrollIntoView({ block: 'start' });
    }, detail);
    await settle(page, 500);
  }, async (page) => { await page.evaluate(() => { if (window.__llOrig) { window.__llOrig[0].dateAdded = window.__llOrig[1]; window.__llOrig = null; } if (carDetailKey) hideCarDetail(); renderLive(); }); await resetUi(page); }]),
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
    // Results heading (hub 2026-11-10): the bold headline is its own line and
    // the next line starts plainly: no leading dash, no lowercase start.
    const head = await page.evaluate(() => { const h = document.querySelector('#pf-results .pf-results-head'); if (!h) return null; const st = h.querySelector('strong'); return { strong: st ? st.textContent : '', rest: st ? h.textContent.slice(h.textContent.indexOf(st.textContent) + st.textContent.length).trim() : h.textContent }; });
    if (head && /^[\u2014\u2013-]|^[a-z]/.test(head.rest)) throw new Error(`results heading line 2 starts "${head.rest.slice(0, 30)}"`);
    if (process.env.PF_HEADS && head) console.log('PF_HEAD', name, JSON.stringify(head));
    await amLinesCheck(page);

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
  // Aftermarket donor cards (hub 2026-11-10): GSP CV axle for a 2021 GMC
  // Terrain. Only the checks to make at the car sit on the card; the listing's
  // provenance is behind "Why it fits". No card shows more than 7 lines of
  // warnings at 390px (100% text).
  ['pf-am-cv', async (page) => {
    await tab(page, 'parts');
    await page.evaluate(() => { const r = document.getElementById('pf-radius'); r.value = '250'; r.dispatchEvent(new Event('change', { bubbles: true })); });
    // The real GSP CV axle groups (the fixture interchange has no lazy
    // layer): pick a seeker whose unit is listed for a car on a nearby lot.
    const groups = JSON.parse(fs.readFileSync(path.join(DOCS, 'data/oem/cv-axle.json'), 'utf8')).amGroups;
    const seeker = await page.evaluate((groups) => {
      pfOemLazyData['cv-axle'] = { oemGroups: [], amGroups: groups };
      for (const v of liveInventory) {
        const d = vehicleDistanceMi(v); if (d == null || d > 250) continue;
        const mk = canonicalMake(v.make);
        const g = groups.find(g => g.apps.some(a => pfAppMatches(a, v.year, mk, v.model)));
        if (g) { const a = g.apps.find(a => pfAppMatches(a, v.year, mk, v.model)); return [String(v.year), a[0], a[1]]; }
      }
      return null;
    }, groups);
    if (!seeker) throw new Error('no car near the test zip is listed for any GSP CV axle');
    const [y, mk, md] = seeker;
    await page.selectOption('#pf-year', y);
    await page.selectOption('#pf-make', mk);
    await page.waitForFunction((md) => [...document.getElementById('pf-model').options].some(o => o.value === md), md, { timeout: 8000 });
    await page.selectOption('#pf-model', md);
    await page.evaluate(() => { pfCat = interchangeData.categories.find(c => c.id === 'cv-axle'); pfPartInput.value = pfCat.label; pfRunSearch(); });
    await page.waitForFunction(() => document.querySelector('#pf-results .pf-row-card, #pf-results .pf-empty'), null, { timeout: 20000 });
    await settle(page, 600);
    if (process.env.AM_LINES) console.log('AM_CAR', seeker.join(' '));
    if (!(await amLinesCheck(page))) throw new Error(`no aftermarket donor card for a ${seeker.join(' ')} CV axle`);
    await page.evaluate(() => { const c = document.querySelector('#pf-results .pf-row-card .pf-src-more-text'); if (c) { c.closest('.pf-row-card').scrollIntoView({ block: 'start' }); window.scrollBy(0, -80); } });
  }, async (page) => { await page.evaluate(() => { delete pfOemLazyData['cv-axle']; const r = document.getElementById('pf-radius'); r.value = '100'; r.dispatchEvent(new Event('change', { bubbles: true })); }); }],
  ['pf-likely-pro', async (page) => {
    await page.evaluate(() => { localStorage.setItem('jh_pro', '1'); applyProGates(); });
    await likelySearch(page);
  }, async (page) => { await page.evaluate(() => { localStorage.removeItem('jh_pro'); applyProGates(); }); }],
  ['alerts', async (page) => { await tab(page, 'alerts'); }],
  // A watch from a share page (2026-11-12): the card at the top of Alerts
  // with the car and, when no location is saved, the zip field (and its
  // message), and the same zip question in the toast after a bell tap.
  ...[['alerts-intent-car', true, false], ['alerts-intent-zip', false, false], ['alerts-intent-car-located', true, true]].map(([name, car, located]) => [name, async (page) => {
    await tab(page, 'alerts');
    await page.evaluate(async ({ car, located }) => {
      window.__zipWas = activeZipCoords;
      if (!located) activeZipCoords = null;
      watchIntent = car ? { make: 'Mercedes-Benz', model: 'Sprinter 2500 Cargo Van', yrMin: 2007, yrMax: 2011 } : null;
      renderWatchIntent();
      const el = document.getElementById('watch-intent');
      if (!el || !el.getClientRects().length) throw new Error('no watch-intent card');
      if (!located) {
        if (!document.getElementById('watch-intent-zip')) throw new Error('no zip field in the card');
        await watchIntentGo();   // empty zip: the message shows in the card
        if (!/zip|postal/i.test(el.querySelector('.watch-zip-msg').textContent)) throw new Error('no message for an empty zip');
      } else if (document.getElementById('watch-intent-zip')) throw new Error('zip field shown although a location is saved');
      window.scrollTo(0, 0);
    }, { car, located });
  }, async (page) => { await page.evaluate(() => { watchIntent = null; activeZipCoords = window.__zipWas; renderWatchIntent(); }); }]),
  ['watch-toast-zip', async (page) => {
    await tab(page, 'live');
    await page.evaluate(async () => {
      window.__zipWas = activeZipCoords;
      activeZipCoords = null;
      askZipForWatch('Mercedes-Benz Sprinter 2500 Cargo Van', () => {});
      const t = document.getElementById('watch-toast');
      await watchZipSubmit(t.querySelector('.watch-zip-input'), t.querySelector('.watch-zip-msg'));   // empty: message shows
      if (!document.getElementById('watch-toast-zip').getClientRects().length) throw new Error('no zip field in the toast');
    });
    await settle(page, 300);
  }, async (page) => { await page.evaluate(() => { activeZipCoords = window.__zipWas; document.getElementById('watch-toast').classList.remove('show'); }); }],
  // The free Monday email offer in the watch toast (web, 2026-11-12): the
  // ask, its message line, the "check your inbox" reply, and the one-tap
  // add for a confirmed address. The longest model name in the scan.
  ...[['watch-toast-recap', 'ask'], ['watch-toast-recap-msg', 'msg'], ['watch-toast-recap-sent', 'sent'], ['watch-toast-recap-add', 'add']].map(([name, mode]) => [name, async (page) => {
    await tab(page, 'live');
    await page.evaluate(async (mode) => {
      try { sessionStorage.removeItem('ys_recap_no'); } catch (e) { /* none */ }
      window.__recapWas = localStorage.getItem('ys_recap');
      if (mode === 'add') localStorage.setItem('ys_recap', JSON.stringify({ email: 'christopher.longname@example.com', state: 'confirmed', sub: 'eA.' + '0'.repeat(64) }));
      else localStorage.removeItem('ys_recap');
      const c = activeZipCoords || { lat: 37.33, lng: -121.89 };
      _recapNew = [{ make: 'Mercedes-Benz', model: 'Sprinter 2500 Cargo Van', lat: c.lat, lng: c.lng, radiusMi: 250 }];
      showWatchToast('Mercedes-Benz Sprinter 2500 Cargo Van');
      clearTimeout(_watchToastTimer);
      const t = document.getElementById('watch-toast');
      if (!t.querySelector('.mail-ask')) throw new Error('no Monday-email offer in the toast');
      if (mode === 'msg') {
        t.querySelector('.mail-email').value = 'nope';
        t.querySelector('.mail-form').requestSubmit();
        if (!t.querySelector('.mail-msg').textContent) throw new Error('no message for a bad address');
      }
      if (mode === 'sent') {
        window.__fetchWas = window.fetch;
        window.fetch = async (u, i) => (String(u).includes('/v1/recap/') ? new Response('{"ok":true,"state":"confirm-sent"}', { status: 200 }) : window.__fetchWas(u, i));
        t.querySelector('.mail-email').value = 'christopher.longname@example.com';
        t.querySelector('.mail-form').requestSubmit();
        for (let i = 0; i < 40 && !t.dataset.recapDone; i++) await new Promise(r => setTimeout(r, 25));
        clearTimeout(_watchToastTimer);
        if (!/Check your inbox/.test(t.innerText)) throw new Error('no "check your inbox" reply');
      }
    }, mode);
    await settle(page, 300);
  }, async (page) => {
    await page.evaluate(() => {
      clearTimeout(_watchToastTimer);
      document.getElementById('watch-toast').classList.remove('show');
      if (window.__fetchWas) { window.fetch = window.__fetchWas; window.__fetchWas = null; }
      if (window.__recapWas) localStorage.setItem('ys_recap', window.__recapWas); else localStorage.removeItem('ys_recap');
      try { sessionStorage.removeItem('ys_recap_no'); } catch (e) { /* none */ }
    });
  }]),
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
  // Web with checkout live (what yardscout.io serves; the run answers
  // /api/ent/config with billing on).
  ['pro-sheet', async (page) => {
    await resetUi(page);
    await page.evaluate(() => openUpgradeSheet('header-pill'));
    await settle(page, 400);
    if (!(await page.evaluate(() => document.getElementById('ent-buy').style.display !== 'none'))) throw new Error('web checkout button not shown (billing config not picked up)');
    await foldCheck(page, 'web Pro sheet', '#ent-checkout', '#ent-buy .sheet-foot-line');
    // The feature list scrolls under the pinned footer; the footer is not part of the scroller.
    await page.evaluate(() => {
      const sc = document.getElementById('upgrade-scroll'), foot = document.getElementById('upgrade-foot');
      if (sc.contains(foot)) throw new Error('the footer is inside the scrolling part');
      const before = document.getElementById('ent-checkout').getBoundingClientRect().top;
      sc.scrollTop = sc.scrollHeight;
      if (Math.abs(document.getElementById('ent-checkout').getBoundingClientRect().top - before) > 1) throw new Error('the buy button moved when the sheet scrolled');
      sc.scrollTop = 0;
    });
  }],
  ['pro-sheet-bottom', async (page) => {
    await resetUi(page);
    await page.evaluate(() => { openUpgradeSheet('header-pill'); const s = document.getElementById('upgrade-scroll'); s.scrollTop = s.scrollHeight; });
    await settle(page, 400);
    await page.evaluate(() => {
      // Scrolled to the end, the last line of fine print clears the footer.
      const sc = document.getElementById('upgrade-scroll'), foot = document.getElementById('upgrade-foot').getBoundingClientRect();
      const last = [...sc.querySelectorAll('#ent-redeem, #upgrade-form-wrap')].filter(e => e.getClientRects().length).pop();
      if (last && last.getBoundingClientRect().bottom > foot.top + 1) throw new Error('the end of the sheet is hidden behind the footer');
    });
  }],
  ['pro-sheet-car', async (page) => {
    await tab(page, 'live');
    const [k] = await firstKeys(page, 1);
    await page.evaluate((k) => openUpgradeSheet('card-value', encodeURIComponent(k)), k);
    await settle(page, 400);
    await foldCheck(page, 'web Pro sheet from a car', '#ent-checkout', '#ent-buy .sheet-foot-line');
  }],
  // A phone on the web when checkout is not live: that phone's store leads.
  ...['ios', 'android'].map(pl => ['pro-sheet-store-' + pl, async (page) => {
    await resetUi(page);
    await page.evaluate((pl) => {
      openUpgradeSheet('header-pill');
      document.getElementById('ent-buy').style.display = 'none';
      document.getElementById('ent-buy-note').style.display = 'none';
      applyStoreLinks(pl, false);
      refreshUpgradeFoot();
      const a = document.getElementById('ent-store-primary');
      const want = pl === 'android' ? /^https:\/\/play\.google\.com\// : /^https:\/\/apps\.apple\.com\//;
      if (!want.test(a.href)) throw new Error(pl + ' visitor is sent to ' + a.href);
      const other = document.getElementById(pl === 'android' ? 'ent-appstore-link' : 'ent-play-link');
      if (other.getClientRects().length) throw new Error(pl + ' visitor is shown the other store too');
    }, pl);
    await settle(page, 300);
    await foldCheck(page, 'store-led Pro sheet (' + pl + ')', '#ent-store-primary', '#store-buy .sheet-foot-line');
  }, async (page) => {
    await resetUi(page);
    await page.evaluate(() => { document.getElementById('ent-buy').style.display = ''; document.getElementById('ent-buy-note').style.display = ''; applyStoreLinks(WEB_STORE, true); refreshUpgradeFoot(); });
  }]),
  // The app shells' footer (StoreKit / Play Billing with the intro offer).
  ...[['pro-sheet-app', false], ['pro-sheet-app-android', true]].map(([name, android]) => [name, async (page) => {
    await appSheet(page, android);
    await foldCheck(page, name, '#iap-subscribe', '#iap-intro');
  }, appSheetOff]),
  ['pro-sheet-member', async (page) => {
    // A Pro member: no button to pin, and the sheet's own bottom padding returns.
    await page.evaluate(() => { localStorage.setItem('jh_pro', '1'); localStorage.setItem('jh_pro_source', 'account'); applyProGates(); renderLive(); });
    await resetUi(page);
    await page.evaluate(() => {
      openUpgradeSheet('header-pill');
      if (document.getElementById('upgrade-foot').getClientRects().length) throw new Error('a Pro member is shown a buy button');
      if (!document.getElementById('upgrade-pro-state').getClientRects().length) throw new Error('no "You\u2019re Pro" state');
    });
    await settle(page, 300);
  }, async (page) => { await resetUi(page); await page.evaluate(() => { localStorage.removeItem('jh_pro'); localStorage.removeItem('jh_pro_source'); applyProGates(); renderLive(); }); }],
  // Notable trims (2026-11-13): a card carrying three badges (trim, Manual,
  // New / Leaving soon) and the Filters panel with Trim picked and its
  // "no single trim" note.
  ['cards-trim-badges', async (page) => {
    // The badge is Pro-only when NOTABLE_TRIMS_FREE is false: show the card
    // as a Pro user sees it, so the three-badge layout is checked either way.
    await page.evaluate(() => {
      if (!NOTABLE_TRIMS_FREE && !isPro()) { localStorage.setItem('jh_pro', '1'); applyProGates(); renderLive(); window.__fxTrimPro = true; }
    });
    await tab(page, 'live');
    await page.evaluate(() => {
      const cars = _scopedVehicles.filter(v => notableTrimOf(v) && !isNoPickModel(v.make, v.model) && extrasFor(v));
      if (!cars.length) throw new Error('no notable-trim car in range (no notableTrims in the data?)');
      // The longest name with the longest trim word: the hardest card to fit.
      const size = (v) => `${v.year} ${v.make} ${v.model}`.length + 2 * notableTrimOf(v).length;
      const v = cars.sort((a, b) => size(b) - size(a))[0];
      const eid = String(v.id);
      window.__fxTrim = { eid, ex: vehicleExtras[eid], date: v.dateAdded, v };
      const ex = (vehicleExtras[eid] || []).slice();
      ex[3] = 'Manual'; ex[4] = 'vin';          // fixture: the Manual badge
      vehicleExtras[eid] = ex;
      if (!isNew(v.dateAdded) && !carLotClock(v).leavingSoon) v.dateAdded = new Date().toISOString().slice(0, 10);   // fixture: "New"
      carSearchSetFilter(v.make, canonicalModel(v.make, v.model));
      setLiveTrim(notableTrimOf(v));
      renderLive();
      const c = document.querySelector(`#live-grid .car-card[data-eid="${CSS.escape(eid)}"]`);
      if (!c) throw new Error('fixture card not rendered');
      const n = c.querySelectorAll('.car-badges .badge').length;
      if (n !== 3) throw new Error(`fixture card has ${n} badges, want 3`);
      c.scrollIntoView({ block: 'start' }); window.scrollBy(0, -70);
    });
  }, async (page) => {
    await page.evaluate(() => {
      const f = window.__fxTrim; if (!f) return;
      if (f.ex === undefined) delete vehicleExtras[f.eid]; else vehicleExtras[f.eid] = f.ex;
      f.v.dateAdded = f.date; delete f.v._ts;
      carSearchClearAll(); document.getElementById('car-search-input').blur();
    });
    await page.evaluate(() => {
      if (window.__fxTrimPro) { window.__fxTrimPro = false; localStorage.removeItem('jh_pro'); applyProGates(); renderLive(); }
    });
    await settle(page, 300);
  }],
  ['cars-filters-trim', async (page) => {
    await tab(page, 'live');
    await page.evaluate(() => {
      // The make/model + trim with the most cars the note counts as unknown.
      const groups = new Map();
      for (const v of _scopedVehicles) {
        const w = notableTrimHitsOf(v)[0] || '';   // internal: also in a Pro-only run
        if (!w || isNoPickModel(v.make, v.model)) continue;
        const k = v.make + '\u0000' + canonicalModel(v.make, v.model) + '\u0000' + w;
        if (!groups.has(k)) groups.set(k, { make: v.make, model: canonicalModel(v.make, v.model), word: w, unknown: 0 });
      }
      for (const g of groups.values()) {
        g.unknown = _scopedVehicles.filter(v => v.make === g.make && canonicalModel(v.make, v.model) === g.model
          && !notableTrimHits(v).includes(g.word) && notableTrimMaybe(v, g.word)).length;
      }
      const g = [...groups.values()].sort((a, b) => b.unknown - a.unknown)[0];
      if (!g) throw new Error('no notable-trim car in range (no notableTrims in the data?)');
      if (!document.getElementById('live-filter-toggle').classList.contains('open')) document.getElementById('live-filter-toggle').click();
      carSearchSetFilter(g.make, g.model);
      setLiveTrim(g.word);
      renderLive();
      if (document.getElementById('live-filter-trim-wrap').hidden) throw new Error('Trim control not shown');
      if (!notableTrimsShown()) {   // TRIMS_FREE=false run: the Pro box in its place
        if (!document.querySelector('#live-filter-trim-pro .pro-box')) throw new Error('no Pro box for the Trim filter');
      } else if (g.unknown && document.getElementById('live-filter-trim-note').hidden) throw new Error('no "no single trim" note');
      document.getElementById('live-filter-trim-wrap').scrollIntoView({ block: 'center' });
    });
  }, async (page) => {
    await page.evaluate(() => {
      carSearchClearAll(); document.getElementById('car-search-input').blur();
      if (document.getElementById('live-filter-toggle').classList.contains('open')) document.getElementById('live-filter-toggle').click();
    });
    await settle(page, 300);
  }],
  ['yards', async (page) => { await tab(page, 'yards'); }],
  // Filter panels open (2026-11-13: no screen opened them, so a zip
  // placeholder and "From" cut off in the two-column layout on an iPhone
  // went unseen). The -gps screens put the fields in the state the location
  // button leaves them in: empty zip, the "Near me" placeholder, Pro's 500 mi.
  ['cars-filters', async (page) => {
    await tab(page, 'live');
    await page.evaluate(() => { if (!document.getElementById('live-filter-toggle').classList.contains('open')) document.getElementById('live-filter-toggle').click(); });
    await settle(page, 300);
  }],
  ['cars-filters-gps-pro', async (page) => {
    await page.evaluate(() => { localStorage.setItem('jh_pro', '1'); applyProGates(); renderLive(); });
    await tab(page, 'live');
    await page.evaluate(() => {
      if (!document.getElementById('live-filter-toggle').classList.contains('open')) document.getElementById('live-filter-toggle').click();
      const z = document.getElementById('live-zip'); z.value = ''; z.placeholder = 'Near me';
      const r = document.getElementById('live-radius'); r.value = '500';
    });
    await settle(page, 300);
  }, async (page) => {
    await page.evaluate(() => {
      const z = document.getElementById('live-zip'); z.placeholder = 'e.g. 84101'; z.value = localStorage.getItem('jh_zip') || '';
      document.getElementById('live-radius').value = '100';
      if (document.getElementById('live-filter-toggle').classList.contains('open')) document.getElementById('live-filter-toggle').click();
      localStorage.removeItem('jh_pro'); applyProGates(); renderLive();
    });
  }],
  ['yards-filters-gps', async (page) => {
    await tab(page, 'yards');
    await page.evaluate(() => {
      if (!document.getElementById('yards-filter-toggle').classList.contains('open')) document.getElementById('yards-filter-toggle').click();
      const z = document.getElementById('yards-zip'); z.value = ''; z.placeholder = 'Near me';
    });
    await settle(page, 300);
  }, async (page) => {
    await page.evaluate(() => {
      const z = document.getElementById('yards-zip'); z.placeholder = 'e.g. 84101'; z.value = localStorage.getItem('jh_zip') || '';
      if (document.getElementById('yards-filter-toggle').classList.contains('open')) document.getElementById('yards-filter-toggle').click();
    });
  }],
  ['pf-where-gps', async (page) => {
    await tab(page, 'parts');
    await page.evaluate(() => {
      document.getElementById('pf-where-box').open = true;
      const z = document.getElementById('pf-zip'); z.value = ''; z.placeholder = 'Near me';
    });
    await settle(page, 300);
  }, async (page) => {
    await page.evaluate(() => {
      const z = document.getElementById('pf-zip'); z.placeholder = 'e.g. 84101'; z.value = localStorage.getItem('jh_zip') || '';
      document.getElementById('pf-where-box').open = false;
    });
  }],
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
      // Map screens: let MapLibre finish redrawing after a theme/text-size
      // change (its pins are re-checked every frame) before measuring; under
      // CPU load the fixed settle above can be too short.
      await page.evaluate(async () => {
        if (!document.querySelector('#tab-yards.yards-map-mode #yards-map')) return;
        const t0 = Date.now();
        while (window._yardsMap && !_yardsMap.loaded() && Date.now() - t0 < 4000) await new Promise(r => setTimeout(r, 50));
        for (let i = 0; i < 4; i++) await new Promise(r => requestAnimationFrame(r));
        await new Promise(r => setTimeout(r, 250));
      });
      const rows = await page.evaluate(CHECK_FN);
      if (process.env.DEBUG_IMG) console.log(screen, await page.evaluate(() => [...document.querySelectorAll('.photo-box img')].slice(0, 3).map(i => [i.src.slice(0, 90), i.complete, i.naturalWidth, i.closest('.photo-box').className])));
      if (process.env.DEBUG_PINS && rows.some(r => /yards-map/.test(r.el || ''))) console.log(screen, width, theme, z, JSON.stringify(await page.evaluate(() => { const c = document.getElementById('yards-map').getBoundingClientRect(); return { map: [Math.round(c.top), Math.round(c.bottom)], pins: [...document.querySelectorAll('#yards-map .map-pin')].map(p => { const r = p.getBoundingClientRect(); return [p.textContent.trim().slice(0, 18), Math.round(r.top), Math.round(r.bottom), p.style.transform, getComputedStyle(p).fontSize]; }) }; })));
      if (process.env.DEBUG_WIDE && rows.length) console.log(screen, width, theme, z, await page.evaluate(() => [...document.querySelectorAll('body *')].filter(e => e.getBoundingClientRect().right > innerWidth + 1 && e.getClientRects().length).slice(0, 8).map(e => e.tagName + '.' + e.className + ' ' + Math.round(e.getBoundingClientRect().width))));
      record(screen, `${width}/${theme}/${z * 100}%`, rows);
      passes++;
      if (SHOTS && z === 1 && (width === 390 || width === 1280) && (theme === 'light' || width === 390)) {
        fs.mkdirSync(SHOTS, { recursive: true });
        // A screen may ask for a taller clip (page coordinates) for review shots.
        const clip = await page.evaluate(() => {
          if (!window.__shotClip) return null;
          // Fixed chrome (nav, closed sheets) would land mid-list in a tall shot.
          window.__clipHidden = [...document.querySelectorAll('body *')].filter(e => { const p = getComputedStyle(e).position; return p === 'fixed' || p === 'sticky'; });
          for (const e of window.__clipHidden) e.style.setProperty('visibility', 'hidden', 'important');
          return window.__shotClip;
        });
        await page.screenshot({ path: path.join(SHOTS, `${width === 390 ? 'phone' : 'desk'}-${screen}${theme === 'dark' ? '-dark' : ''}.png`), ...(clip ? { clip, fullPage: true } : {}) });
        if (clip) await page.evaluate(() => { for (const e of window.__clipHidden || []) e.style.removeProperty('visibility'); });
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
    await page.route(/^https?:\/\/(?!127\.0\.0\.1|fonts\.googleapis\.com|fonts\.gstatic\.com|cdn\.pypapps\.com|storage\.googleapis\.com|www\.kikersupullit\.com|ik\.imagekit\.io|cdn\.shopify\.com|cdn\.row52\.com|unpkg\.com|tiles\.openfreemap\.org)/, (route) => route.abort());
    // A heavy source's camera original, answered locally (no 4 MB download).
    await page.route(/^https:\/\/inventory\.sturtevantauto\.com\//, (route) => route.fulfill({ contentType: 'image/png', body: fs.readFileSync(path.join(ROOT, 'docs/icon-512.png')) }));
    // Published photo switch (fail-closed in the app): publish the enabled
    // sources of scraper/photo_sources.json exactly as the scan does.
    const PHOTO_ON = publishedPhotoSources();
    await page.route(/data\/(inv\/manifest|vehicle_extras)\.json(\?|$)/, async (route) => {
      const res = await route.fetch(); const j = await res.json();
      j.photoSources = PHOTO_ON;
      // notableTrims as the scan publishes it (from the first scan after
      // design/notable-trims; computed by the scraper until the data has it).
      if (/manifest/.test(route.request().url()) && !j.notableTrims) j.notableTrims = notableTrimsFixture();
      await route.fulfill({ response: res, json: j });
    });
    // TRIMS_FREE=false: serve docs/app.js with NOTABLE_TRIMS_FREE = false
    // (the owner's Pro-only choice for the trim badge and filter).
    if (process.env.TRIMS_FREE === 'false' || process.env.TRIMS_FREE === 'true') {
      await page.route(/\/app\.js(\?|$)/, async (route) => {
        const res = await route.fetch(); const t = await res.text();
        if (!/^const NOTABLE_TRIMS_FREE = (true|false);$/m.test(t)) throw new Error('NOTABLE_TRIMS_FREE constant not found');
        await route.fulfill({ response: res, body: t.replace(/^const NOTABLE_TRIMS_FREE = (true|false);$/m, `const NOTABLE_TRIMS_FREE = ${process.env.TRIMS_FREE};`) });
      });
    }
    // Web checkout is live on yardscout.io; the Pro sheet is tested in that state.
    await page.route(/\/api\/ent\/config(\?|$)/, (route) => route.fulfill({ json: { billing: true }, headers: { 'access-control-allow-origin': '*' } }));
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
