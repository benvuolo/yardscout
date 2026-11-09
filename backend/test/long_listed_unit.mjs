/* Unit test: "listed far past the typical stay" (docs/app.js isLongListed,
 * longListedHtml, carLotClock). Owner report 2026-11-09: Pull-N-Save
 * Springville cars read "Day 150 of ~60 typical". Over 2x the typical figure
 * in use (or 120+ days with no figure) the bar is replaced by a neutral
 * notice; the car itself is never hidden.
 * Run: node backend/test/long_listed_unit.mjs */
import fs from 'node:fs';
import vm from 'node:vm';

const lines = fs.readFileSync(new URL('../../docs/app.js', import.meta.url), 'utf8').split('\n');
const fn = (name) => {
  const i = lines.findIndex(l => l.startsWith(`function ${name}(`));
  const j = lines.findIndex((l, k) => k > i && l === '}');
  if (i < 0 || j < 0) throw new Error('missing ' + name);
  return lines.slice(i, j + 1).join('\n');
};
const one = (re) => { const l = lines.find(x => re.test(x)); if (!l) throw new Error('missing ' + re); return l; };
const ctx = vm.createContext({});
vm.runInContext([
  'var __ls = null, __days = null;',
  'function lifespanFor() { return __ls; }',
  'function daysSinceAdded() { return __days; }',
  "function escapeHtml(s) { return String(s); }",
  one(/^const LONG_LISTED_DAYS = /), fn('isLongListed'), fn('longListedHtml'), fn('carLotClock'),
  'globalThis.__t = { isLongListed, longListedHtml, carLotClock, set: (ls, d) => { __ls = ls; __days = d; } };',
].join('\n'), ctx);
const T = ctx.__t;

let fails = 0;
const check = (name, ok, d = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + d}`); if (!ok) fails++; };

check('exactly 2x typical is not long-listed', !T.isLongListed(120, 60));
check('over 2x typical is long-listed', T.isLongListed(121, 60));
check('no typical figure: under 120 days is fine', !T.isLongListed(119, null));
check('no typical figure: 120+ days is long-listed', T.isLongListed(120, null));
check('unknown age is never long-listed', !T.isLongListed(null, 60) && !T.isLongListed(NaN, null));
const h = T.longListedHtml(150);
check('notice wording', /Listed 150 days, longer than usual here\. Yards’ lists can fall behind; call before going for this one\./.test(h), h);
check('notice is neutral (no warning/red class)', !/warn|red|danger|soon/.test(h), h);

const car = { dateAdded: '2026-05-01', make: 'Ford', model: 'Taurus' };
T.set({ avg: 60, basis: 'chain', fast: false }, 149);
let c = T.carLotClock(car);
check('Springville case: day 150 of ~60 -> notice, no bar, no "Leaving soon"', c.longListed && c.avg === null && c.lotClock === '' && !c.leavingSoon, JSON.stringify(c));
T.set({ avg: 60, basis: 'chain', fast: false }, 50);
c = T.carLotClock(car);
check('a car within the typical stay keeps its bar and clock', !c.longListed && c.avg === 60 && /Day 51 of ~60 typical/.test(c.lotClock), JSON.stringify(c));
T.set({ avg: 60, basis: 'chain', fast: false }, 100);
c = T.carLotClock(car);
check('between 1x and 2x keeps the existing "past typical" wording', !c.longListed && /past the ~60-day typical|Day 101 of ~60/.test(c.lotClock), c.lotClock);
T.set(null, 130);
c = T.carLotClock(car);
check('no lifespan at all, 130 days -> notice', c.longListed && c.avg === null, JSON.stringify(c));

console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
