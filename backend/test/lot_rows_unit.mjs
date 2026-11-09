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
const fnText = (name) => {
  const i = lines.findIndex(l => l.startsWith(`function ${name}(`));
  const j = lines.findIndex((l, k) => k > i && l === '}');
  if (i < 0 || j < 0) throw new Error('missing ' + name);
  return lines.slice(i, j + 1).join('\n');
};
const ttl = lines.find(l => l.startsWith('const CHECK_TTL_MS = '));
const ctx = vm.createContext({});
vm.runInContext([lines.slice(start, fnEnd + 1).join('\n'), ttl, fnText('checksPrune'), fnText('checksToggle'), fnText('rowCheckSummary'), fnText('rowSeenLabel'), fnText('rowPullLabel'),
  'globalThis.__c = compareRows; globalThis.__k = { checksPrune, checksToggle, rowCheckSummary, rowSeenLabel, rowPullLabel, CHECK_TTL_MS };'].join('\n'), ctx);
const cmp = ctx.__c;
const K = ctx.__k;

let fails = 0;
const check = (name, ok, d = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + d}`); if (!ok) fails++; };
const sorted = (a) => [...a].sort(cmp).join(',');
check('numbers in numeric order', sorted(['10', '2', '1', '33', '3']) === '1,2,3,10,33', sorted(['10', '2', '1', '33', '3']));
check('letter prefixes grouped, numeric inside', sorted(['B1', 'A10', 'A2', 'A1']) === 'A1,A2,A10,B1', sorted(['B1', 'A10', 'A2', 'A1']));
check('suffix after the plain number', sorted(['12A', '12', '11']) === '11,12,12A', sorted(['12A', '12', '11']));
check('case-insensitive', sorted(['a3', 'A1']) === 'A1,a3', sorted(['a3', 'A1']));
check('rows with no number come after numbered ones of the same prefix', sorted(['Front', '5', '2']) === '2,5,Front', sorted(['Front', '5', '2']));
check('stable for equal rows', cmp('7', '7') === 0);

// Checking cars off while walking (stored per yard on the device).
const H = 3600 * 1000, now = 1_800_000_000_000;
let c = K.checksToggle({}, 'Yard A', 'k1', now);
check('toggle on stores the time under the yard', c['Yard A'] && c['Yard A'].k1 === now);
c = K.checksToggle(c, 'Yard A', 'k2', now);
c = K.checksToggle(c, 'Yard A', 'k1', now);
check('toggle off removes only that car', !('k1' in c['Yard A']) && c['Yard A'].k2 === now);
check('the last check removed drops the yard entry', !('Yard A' in K.checksToggle(c, 'Yard A', 'k2', now)));
const live = (loc) => new Set(loc === 'Yard A' ? ['k1', 'k2', 'k3'] : ['z1']);
const p = K.checksPrune({ 'Yard A': { k1: now - 2 * H, k2: now - 25 * H, gone: now - H, k3: 'x' }, 'Yard B': { z1: now - 30 * H } }, now, live);
check('a check older than 24 h lapses', !('k2' in (p['Yard A'] || {})));
check('a check on a car that left the inventory lapses', !('gone' in (p['Yard A'] || {})));
check('a fresh check on a car still there is kept', p['Yard A'] && p['Yard A'].k1 === now - 2 * H);
check('junk values are dropped; an emptied yard disappears', !('k3' in (p['Yard A'] || {})) && !('Yard B' in p));
check('a future-dated check is dropped', !('k1' in (K.checksPrune({ Y: { k1: now + 5 * H } }, now, null).Y || {})));
check('prune tolerates missing or broken storage', JSON.stringify(K.checksPrune(null, now, null)) === '{}' && JSON.stringify(K.checksPrune({ Y: 'x' }, now, null)) === '{}');
let r = K.rowCheckSummary(['a', 'b', 'c', 'd'], { a: true, c: true });
check('row summary: 2 of 4 checked, not done', r.checked === 2 && r.total === 4 && !r.done);
r = K.rowCheckSummary(['a', 'b'], { a: true, b: true });
check('row summary: all checked -> collapses', r.done && r.checked === 2);
check('an empty row never counts as done', !K.rowCheckSummary([], {}).done);
// Button wording (owner: "Check" and "+ Add" were unclear).
check('Seen button: "Seen" both ways; aria says mark / unmark', K.rowSeenLabel(false, 'Car').text === 'Seen' && /Mark seen: Car/.test(K.rowSeenLabel(false, 'Car').aria) && /Tap to unmark/.test(K.rowSeenLabel(true, 'Car').aria));
check('Pull-sheet button: "Pull sheet" / "On pull sheet"', K.rowPullLabel(false, 'Car').text === 'Pull sheet' && K.rowPullLabel(true, 'Car').text === 'On pull sheet' && /Add to pull sheet: Car/.test(K.rowPullLabel(false, 'Car').aria) && /Tap to remove/.test(K.rowPullLabel(true, 'Car').aria));

console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
