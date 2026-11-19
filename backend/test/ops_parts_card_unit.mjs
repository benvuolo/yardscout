/* Unit: the daily ops email's Parts card lines (backend/src/ops_monitor.js
 * partsCardCounts / partsCardLines, 2026-11-19). Aggregate counts only;
 * the lines print even when every count is 0; pf/ and pf-car/ rows are not
 * counted here.
 * Run: node backend/test/ops_parts_card_unit.mjs */
import { partsCardCounts, partsCardLines } from '../src/ops_monitor.js';

let pass = 0, fail = 0;
const check = (name, ok, d = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + d}`); ok ? pass++ : fail++; };

const rows = [
  { event: 'pf/alternator', n: 9 }, { event: 'pf-car/toyota-4runner', n: 4 },
  { event: 'pf-yards/shown', n: 1200 }, { event: 'pf-yards/tap', n: 31 },
  { event: 'pf-yards/chip-near', n: 5 }, { event: 'pf-yards/chip-new', n: 2 }, { event: 'pf-yards/chip-price', n: 1 }, { event: 'pf-yards/chip-most', n: 1 },
  { event: 'pf-yards/all', n: 7 }, { event: 'pf-forecast/donor-models', n: 640 }, { event: 'watch-forecast/shown', n: 12 },
];
const c = partsCardCounts(rows);
check('counts: shown, taps, order changes (all chips summed), show all, donor, alert forecasts',
  JSON.stringify(c) === JSON.stringify({ shown: 1200, taps: 31, orders: 9, all: 7, donor: 640, alertForecasts: 12 }), JSON.stringify(c));
const L = partsCardLines(c);
check('line 1', L[0] === 'Parts card (7 d): shown 1,200, yard taps 31, order changes 9, show all 7, donor-model forecasts 640', L[0]);
check('line 2', L[1] === 'Alert forecasts shown (7 d): 12', L[1]);
const Z = partsCardLines(partsCardCounts([]));
check('zero counts still print both lines', Z.length === 2 && Z[0] === 'Parts card (7 d): shown 0, yard taps 0, order changes 0, show all 0, donor-model forecasts 0' && Z[1] === 'Alert forecasts shown (7 d): 0', JSON.stringify(Z));
check('no counts object = zeros', JSON.stringify(partsCardLines(undefined)) === JSON.stringify(Z));
check('pf/ and pf-car/ rows are not counted', JSON.stringify(partsCardCounts(rows.slice(0, 2))) === JSON.stringify(partsCardCounts([])));

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
