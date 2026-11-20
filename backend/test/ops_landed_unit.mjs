/* Unit: the daily ops email's landed-pages line (backend/src/ops_monitor.js
 * landedCounts / landedLine, 2026-11-20): views in total, the top 5 pages,
 * views by source; printed at 0 too; other events not counted.
 * Run: node backend/test/ops_landed_unit.mjs */
import { landedCounts, landedLine } from '../src/ops_monitor.js';

let pass = 0, fail = 0;
const check = (name, ok, d = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + d}`); ok ? pass++ : fail++; };
const rows = [
  { event: 'landed-view/toyota-4runner', n: 40 }, { event: 'landed-view/toyota', n: 6 }, { event: 'landed-view/nissan-xterra', n: 3 },
  { event: 'landed-view/honda-civic', n: 2 }, { event: 'landed-view/ford-ranger', n: 2 }, { event: 'landed-view/bmw', n: 1 },
  { event: 'landed-src/reddit/toyota-4runner', n: 30 }, { event: 'landed-src/reddit/toyota', n: 2 }, { event: 'landed-src/google/nissan-xterra', n: 3 },
  { event: 'pf/alternator', n: 99 }, { event: 'pf-yards/shown', n: 5 }, { event: 'landed-view/', n: 7 },
];
const c = landedCounts(rows);
check('views summed over pages (other events ignored)', c.views === 54, String(c.views));
check('top 5 pages, most first, ties by name', JSON.stringify(c.top.map((x) => x.name)) === '["toyota-4runner","toyota","nissan-xterra","ford-ranger","honda-civic"]', JSON.stringify(c.top));
check('sources summed over pages', JSON.stringify(c.sources) === JSON.stringify([{ name: 'reddit', n: 32 }, { name: 'google', n: 3 }]), JSON.stringify(c.sources));
check('the line', landedLine(c) === 'Landed pages (7 d): 54 views · top: toyota-4runner 40, toyota 6, nissan-xterra 3, ford-ranger 2, honda-civic 2 · by source: reddit 32, google 3', landedLine(c));
check('zero: still printed', landedLine(landedCounts([])) === 'Landed pages (7 d): 0 views · by source: none named' && landedLine(undefined) === landedLine(landedCounts([])));
check('one view: singular', landedLine(landedCounts([{ event: 'landed-view/bmw', n: 1 }])) === 'Landed pages (7 d): 1 view · top: bmw 1 · by source: none named');
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
