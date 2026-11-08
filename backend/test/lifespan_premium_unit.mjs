/* Unit test: premium-lot lifespans (docs/app.js lifespanFor, yardLifespan).
 * UTPAP "(Premium)" lots keep cars for months, so the chain or all-yards
 * average must not drive "Day X of ~N typical", the stay bar or the yard
 * card's "Cars typically last ~N days" there. A premium lot shows a lifespan
 * only from its own history: a model entry, the scan's own yard figure, or
 * its own typical in model_lifespan.json. Other yards are unchanged.
 * Run: node backend/test/lifespan_premium_unit.mjs */
import fs from 'node:fs';
import vm from 'node:vm';

const lines = fs.readFileSync(new URL('../../docs/app.js', import.meta.url), 'utf8').split('\n');
const fn = (name) => {
  const i = lines.findIndex(l => l.startsWith(`function ${name}(`));
  const j = lines.findIndex((l, k) => k > i && l === '}');
  if (i < 0 || j < 0) throw new Error('missing function ' + name);
  return lines.slice(i, j + 1).join('\n');
};
const one = (re) => { const l = lines.find(x => re.test(x)); if (!l) throw new Error('missing ' + re); return l; };
const ctx = vm.createContext({});
vm.runInContext(['var modelLifespan = null;', one(/^const LIFESPAN_FAST_RATIO = /), one(/^const isPremiumLot = /),
  fn('lifespanFor'), fn('yardLifespan'),
  'globalThis.__t = { lifespanFor, yardLifespan, set: (m) => { modelLifespan = m; } };'].join('\n'), ctx);
const { lifespanFor, yardLifespan, set } = ctx.__t;

let fails = 0;
const check = (name, ok, d = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + d}`); if (!ok) fails++; };
const OREM = 'Utah Pic-A-Part - Orem (Premium)', OGDEN = 'Utah Pic-A-Part - Ogden (Premium)', BASE = 'Utah Pic-A-Part - Orem';
const car = (loc, avg, basis, extra = {}) => ({ location: loc, make: 'Toyota', model: 'Camry', yardAvgLifespan: avg, yardLifespanBasis: basis, ...extra });

check('premium lot, chain average only: no lifespan', lifespanFor(car(OREM, 40, 'chain')) === null);
check('premium lot, all-yards average only: no lifespan', lifespanFor(car(OREM, 50, 'all')) === null);
check('premium lot, chain average: yard card gets no figure', yardLifespan(OREM, 40, 'chain') === null);
check('premium lot, its own yard figure: kept', JSON.stringify(lifespanFor(car(OREM, 180, 'yard'))) === JSON.stringify({ avg: 180, basis: 'yard', fast: false }));
set({ yards: { [OGDEN]: { typical: 150, models: { 'Toyota|Camry': [120, 8] } } } });
check('premium lot with its own model entry: model-here kept', lifespanFor(car(OGDEN, 40, 'chain')).basis === 'model-here');
const og = lifespanFor(car(OGDEN, 40, 'chain', { model: 'Corolla' }));
check('premium lot, chain average but own typical in model_lifespan: uses its own typical', og && og.avg === 150 && og.basis === 'yard', JSON.stringify(og));
check('premium lot yard card: own typical, labelled as this yard', JSON.stringify(yardLifespan(OGDEN, 40, 'chain')) === JSON.stringify({ avg: 150, basis: 'yard', fast: false }));
check('regular yard, chain average: unchanged', JSON.stringify(lifespanFor(car(BASE, 40, 'chain'))) === JSON.stringify({ avg: 40, basis: 'chain', fast: false }));
check('regular yard, no figure: none', lifespanFor(car(BASE, null, null)) === null);
check('"premium" elsewhere in a name is not a premium lot', lifespanFor(car('Premium Auto Parts', 40, 'chain')) !== null);

console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
