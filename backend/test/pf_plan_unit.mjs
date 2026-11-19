/* Unit test: "Best yards for this part" (2026-11-19), the pure pieces in
 * docs/app.js: pfPlanYards (group the donor rows the list shows by yard and
 * order the yards), pfPlanRuleText (the line that states the order) and
 * pfPlanSetOutText (the newest set-out, said plainly). Loads the REAL
 * functions out of docs/app.js (top-level, ending at a column-0 "}").
 *
 *   grouping   one entry per yard; n = its rows; nCheck = rows with an
 *              "if equipped" line; nearest distance; newest date; cheapest
 *              published price (null when none); fast when any row is fast
 *   orders     most (ties: closer), near, new (no dates last), price (no
 *              price last), unknown order = most
 *   held       a yard whose list stopped changing goes after every other
 *              yard in every order, and is still listed
 *   counts     the sum of n equals the items given (nothing dropped/added)
 *   rule line  says each order; mentions held yards only when there are some
 *   set-out    today / yesterday / N days ago / a date; '' when unknown
 *
 * Run: node backend/test/pf_plan_unit.mjs  (APP_JS=<path> tests another copy) */
import fs from 'node:fs';
import vm from 'node:vm';

const APP = process.env.APP_JS || new URL('../../docs/app.js', import.meta.url);
const src = fs.readFileSync(APP, 'utf8');
const lines = src.split('\n');
let failures = 0, passes = 0;
const check = (name, ok, detail = '') => {
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + detail}`);
  if (ok) passes++; else failures++;
};
function fn(name) {
  const start = lines.findIndex(l => l.startsWith(`function ${name}(`));
  if (start < 0) return null;
  const end = lines.findIndex((l, i) => i > start && l === '}');
  return end < 0 ? null : lines.slice(start, end + 1).join('\n');
}
let code = '';
for (const name of ['pfPlanYards', 'pfPlanRuleText', 'pfPlanSetOutText']) {
  const s = fn(name);
  check(`app.js has top-level function ${name}`, !!s);
  code += (s || `function ${name}() { return null; }`) + '\n';
}
const orders = lines.find(l => l.startsWith('const PF_PLAN_ORDERS = '));
check('app.js has const PF_PLAN_ORDERS', !!orders);
code += (orders || 'const PF_PLAN_ORDERS = [];') + '\nthis.PF_PLAN_ORDERS = PF_PLAN_ORDERS;\n';
const ctx = vm.createContext({ Map, Set, Math, Number, Date, String });
vm.runInContext(code, ctx);
const { pfPlanYards, pfPlanRuleText, pfPlanSetOutText } = ctx;

const DAY = 86400000;
const T0 = new Date(2026, 10, 19, 15, 0, 0).getTime();       // Nov 19 2026, 3 pm local
const mid = (daysAgo) => { const d = new Date(T0); d.setHours(0, 0, 0, 0); return d.getTime() - daysAgo * DAY; };
const it = (yard, d, over = {}) => ({ yard, d, dateMs: 0, check: false, price: null, fast: false, fastNote: '', held: false, ...over });
const names = (ys) => ys.map(y => y.yard).join(',');

/* ---- grouping ---- */
{
  const items = [
    it('A', 10, { dateMs: mid(3), check: true, price: 40 }),
    it('A', 10, { dateMs: mid(1), price: 40 }),
    it('A', 10.4, { dateMs: 0, check: true }),
    it('B', 5, { dateMs: mid(0), fast: true, fastNote: 'Honda Civics leave fast' }),
    it('C', 30, { price: 25.5 }),
    it('C', 30, { price: 22 }),
  ];
  const ys = pfPlanYards(items, 'most');
  const a = ys.find(y => y.yard === 'A'), b = ys.find(y => y.yard === 'B'), c = ys.find(y => y.yard === 'C');
  check('grouping: one entry per yard', ys.length === 3, names(ys));
  check('grouping: n = rows of that yard', a.n === 3 && b.n === 1 && c.n === 2, JSON.stringify(ys.map(y => [y.yard, y.n])));
  check('grouping: nCheck = rows with an if-equipped line', a.nCheck === 2 && b.nCheck === 0, `${a.nCheck} ${b.nCheck}`);
  check('grouping: nearest distance of the yard', a.d === 10, String(a.d));
  check('grouping: newest set-out of the yard (unknown dates ignored)', a.newestMs === mid(1), String(a.newestMs));
  check('grouping: no date anywhere = 0 (unknown)', c.newestMs === 0, String(c.newestMs));
  check('grouping: cheapest published price; none = null', c.price === 22 && b.price === null && a.price === 40, `${c.price} ${b.price}`);
  check('grouping: fast with its note when a row is fast', b.fast && b.fastNote === 'Honda Civics leave fast' && !a.fast);
  check('counts: the sum of n equals the items given', ys.reduce((k, y) => k + y.n, 0) === items.length);
  check('grouping: items without a yard are not counted', pfPlanYards([it('', 1), null, it('A', 1)], 'most').length === 1);
  check('grouping: empty input = no yards', pfPlanYards([], 'most').length === 0);
}

/* ---- orders ---- */
{
  const items = [
    ...[1, 2, 3].map(() => it('Far3', 40, { dateMs: mid(9), price: 50 })),
    ...[1, 2, 3].map(() => it('Near3', 12, { dateMs: mid(4) })),
    it('Close1', 2, { dateMs: mid(20), price: 30 }),
    ...[1, 2].map(() => it('Mid2', 20, { dateMs: mid(0), price: 18 })),
  ];
  check('most: most donors first, ties to the closer yard', names(pfPlanYards(items, 'most')) === 'Near3,Far3,Mid2,Close1', names(pfPlanYards(items, 'most')));
  check('near: closest yard first', names(pfPlanYards(items, 'near')) === 'Close1,Near3,Mid2,Far3', names(pfPlanYards(items, 'near')));
  check('new: newest set-out first', names(pfPlanYards(items, 'new')) === 'Mid2,Near3,Far3,Close1', names(pfPlanYards(items, 'new')));
  check('price: lowest published price first, no price last', names(pfPlanYards(items, 'price')) === 'Mid2,Close1,Far3,Near3', names(pfPlanYards(items, 'price')));
  check('unknown order = most', names(pfPlanYards(items, 'bogus')) === names(pfPlanYards(items, 'most')));
  const noDates = [it('X', 5), it('Y', 1), it('Z', 9, { dateMs: mid(30) })];
  check('new: yards with no set-out dates last (closer first among them)', names(pfPlanYards(noDates, 'new')) === 'Z,Y,X', names(pfPlanYards(noDates, 'new')));
  const noPrice = [it('X', 5), it('Y', 1)];
  check('price: no price anywhere = closest first', names(pfPlanYards(noPrice, 'price')) === 'Y,X');
  const tie = [it('Bbb', 5), it('Aaa', 5)];
  check('full tie: by yard name (stable, deterministic)', names(pfPlanYards(tie, 'most')) === 'Aaa,Bbb');
  check('PF_PLAN_ORDERS lists the four orders', JSON.stringify([...ctx.PF_PLAN_ORDERS]) === '["most","near","new","price"]');
}

/* ---- held yards ---- */
{
  const items = [
    ...[1, 2, 3, 4, 5].map(() => it('Frozen', 1, { held: true, dateMs: mid(0), price: 1 })),
    it('Open', 30, { dateMs: mid(5), price: 99 }),
    it('Open2', 40),
  ];
  for (const o of ['most', 'near', 'new', 'price']) {
    const ys = pfPlanYards(items, o);
    check(`held: last in "${o}" and still listed`, ys[ys.length - 1].yard === 'Frozen' && ys.length === 3, names(ys));
  }
  check('held: its donor count is kept', pfPlanYards(items, 'most').find(y => y.yard === 'Frozen').n === 5);
}

/* ---- rule line ---- */
{
  check('rule: most', /most donor cars first; ties go to the closer yard/i.test(pfPlanRuleText('most', false)), pfPlanRuleText('most', false));
  check('rule: near', /^Closest yard first\.$/.test(pfPlanRuleText('near', false)), pfPlanRuleText('near', false));
  check('rule: new', /newest donor set out first/i.test(pfPlanRuleText('new', false)));
  check('rule: price says no-price yards go last', /lowest published yard price/i.test(pfPlanRuleText('price', false)) && /no price last/i.test(pfPlanRuleText('price', false)));
  check('rule: held yards named only when present', /stopped changing go last/.test(pfPlanRuleText('near', true)) && !/stopped/.test(pfPlanRuleText('near', false)));
}

/* ---- set-out line ---- */
{
  check('set-out: unknown = nothing', pfPlanSetOutText(0, T0) === '');
  check('set-out: today', pfPlanSetOutText(mid(0), T0) === 'newest set out today', pfPlanSetOutText(mid(0), T0));
  check('set-out: yesterday', pfPlanSetOutText(mid(1), T0) === 'newest set out yesterday');
  check('set-out: 2 days ago', pfPlanSetOutText(mid(2), T0) === 'newest set out 2 days ago');
  check('set-out: 13 days ago', pfPlanSetOutText(mid(13), T0) === 'newest set out 13 days ago');
  check('set-out: older = the date', pfPlanSetOutText(mid(20), T0) === 'newest set out Oct 30', pfPlanSetOutText(mid(20), T0));
  check('set-out: a date a day ahead (time zones) reads today', pfPlanSetOutText(mid(-1), T0) === 'newest set out today');
}

console.log(failures ? `${failures} FAILURE(S), ${passes} passed` : `ALL PASS (${passes})`);
process.exit(failures ? 1 : 0);
