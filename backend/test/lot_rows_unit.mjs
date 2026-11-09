/* Unit test: Lot Map row order (docs/app.js rowSortKey/compareRows). Rows are
 * listed in the yard's own numbering: numeric part as a number (2 before 10),
 * letter prefixes grouped (A2 before A10, before B1), suffixes after
 * (12 before 12A), and anything without a number after the numbered rows.
 * Run: node backend/test/lot_rows_unit.mjs */
import fs from 'node:fs';
import vm from 'node:vm';

const lines = fs.readFileSync(new URL('../../docs/app.js', import.meta.url), 'utf8').split('\n');
const start = lines.findIndex(l => l.startsWith('const rowSortKey = '));
const end = lines.findIndex((l, k) => k > start && l.startsWith('function compareRows('));
const fnEnd = lines.findIndex((l, k) => k > end && l === '}');
if (start < 0 || end < 0 || fnEnd < 0) throw new Error('row sort helpers not found');
const ctx = vm.createContext({});
vm.runInContext(lines.slice(start, fnEnd + 1).join('\n') + '\nglobalThis.__c = compareRows;', ctx);
const cmp = ctx.__c;

let fails = 0;
const check = (name, ok, d = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + d}`); if (!ok) fails++; };
const sorted = (a) => [...a].sort(cmp).join(',');
check('numbers in numeric order', sorted(['10', '2', '1', '33', '3']) === '1,2,3,10,33', sorted(['10', '2', '1', '33', '3']));
check('letter prefixes grouped, numeric inside', sorted(['B1', 'A10', 'A2', 'A1']) === 'A1,A2,A10,B1', sorted(['B1', 'A10', 'A2', 'A1']));
check('suffix after the plain number', sorted(['12A', '12', '11']) === '11,12,12A', sorted(['12A', '12', '11']));
check('case-insensitive', sorted(['a3', 'A1']) === 'A1,a3', sorted(['a3', 'A1']));
check('rows with no number come after numbered ones of the same prefix', sorted(['Front', '5', '2']) === '2,5,Front', sorted(['Front', '5', '2']));
check('stable for equal rows', cmp('7', '7') === 0);
console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
