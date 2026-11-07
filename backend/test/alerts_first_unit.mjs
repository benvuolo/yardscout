/* Unit test: round-5 "alerts first" teasers in docs/app.js stay honest.
 *  - recapLineHtml (Alerts tab, free only): shown only for a car that landed
 *    on/after the day the watch was made, with a known set-out date; names a
 *    recap date only when this user has a recap channel and the car did not
 *    land on a Monday; the recap date is the next Monday; never for Pro.
 *  - freeDeliveryNote never promises a recap without a recap channel.
 * Run: node backend/test/alerts_first_unit.mjs */
import fs from 'node:fs';
import vm from 'node:vm';

const src = fs.readFileSync(new URL('../../docs/app.js', import.meta.url), 'utf8');
const lines = src.split('\n');
const fn = (name) => {
  const i = lines.findIndex(l => l.startsWith(`function ${name}(`));
  const j = lines.findIndex((l, k) => k > i && l === '}');
  if (i < 0 || j < 0) throw new Error('missing function ' + name);
  return lines.slice(i, j + 1).join('\n');
};
const one = (re) => { const l = lines.find(x => re.test(x)); if (!l) throw new Error('missing ' + re); return l; };
const ctx = vm.createContext({ Date, Math, Number, String, Array });
vm.runInContext(`
var __pro = false, __native = false, __token = null, __email = null;
function isPro() { return __pro; }
var IS_NATIVE = false;
function storedPushToken() { return __token; }
var localStorage = { getItem(k) { return k === 'ys_email_alerts_on' ? __email : null; } };
function escapeHtml(s) { return String(s); }
var ICON = { bell: '' };
function parseYardDate(s) { if (!s) return null; const d = new Date(s + 'T12:00:00'); d.setHours(0, 0, 0, 0); return d; }
${one(/^const RECAP_WEEKDAY = /)}
${fn('hasRecapChannel')}
${fn('proBoxHtml')}
${fn('freeDeliveryNote')}
${one(/^const fmtDay = /)}
${fn('recapLineHtml')}
globalThis.__t = { recapLineHtml, freeDeliveryNote, set: (o) => Object.assign(globalThis, o) };
`, ctx);
const T = ctx.__t;
const set = (o) => vm.runInContext(Object.entries(o).map(([k, v]) => `${k} = ${JSON.stringify(v)};`).join(''), ctx);

let fails = 0;
const check = (name, ok, d = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + d}`); if (!ok) fails++; };
const iso = (d) => d.toISOString();
const text = (h) => h.replace(/<[^>]+>/g, ' ');
const day = (y, m, d) => `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
const watch = (y, m, d) => [{ addedAt: iso(new Date(y, m - 1, d, 9)) + '~abc123' }];

set({ __pro: false, __email: '1' });
// Tue 2026-11-03 set-out, watch made Sun 2026-11-01 -> next Monday is 2026-11-09
let h = T.recapLineHtml({ dateAdded: day(2026, 11, 3) }, watch(2026, 11, 1));
check('free + email recap: names the next Monday after the set-out day', /Landed Tue, Nov 3/.test(h) && /Mon, Nov 9/.test(h) && /Would have pushed it the day it landed/.test(h), h);
check('free: the Pro half is a Pro box that opens the Pro sheet, no bare link', /class="pro-box"/.test(h) && /openUpgradeSheet\('watch-near-miss'\)/.test(h) && !/linklike/.test(h), h);
check('car that landed before the watch was made: no line', T.recapLineHtml({ dateAdded: day(2026, 10, 20) }, watch(2026, 11, 1)) === '');
check('unknown set-out date: no line', T.recapLineHtml({ dateAdded: '' }, watch(2026, 11, 1)) === '');
h = T.recapLineHtml({ dateAdded: day(2026, 11, 2) }, watch(2026, 11, 1));   // a Monday
check('Monday set-out: no recap date claimed (may or may not make that recap)', !/recap/.test(text(h)) && /Landed Mon, Nov 2/.test(h), h);
set({ __email: null });
h = T.recapLineHtml({ dateAdded: day(2026, 11, 3) }, watch(2026, 11, 1));
check('no recap channel: no recap mentioned, Pro line kept', !/recap/.test(text(h)) && /Would have pushed/.test(h), h);
check('no recap channel: delivery note promises no recap', !/recap/i.test(T.freeDeliveryNote()), T.freeDeliveryNote());
set({ __email: '1' });
check('recap channel: delivery note names the Monday recap', /Monday recap/.test(T.freeDeliveryNote()));
set({ __pro: true });
check('Pro: never shown', T.recapLineHtml({ dateAdded: day(2026, 11, 3) }, watch(2026, 11, 1)) === '');
set({ __pro: false });
check('the earliest matching watch counts', /Landed/.test(T.recapLineHtml({ dateAdded: day(2026, 11, 3) }, [...watch(2026, 11, 5), ...watch(2026, 10, 30)])));

console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
