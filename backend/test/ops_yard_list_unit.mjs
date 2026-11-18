/* Unit: the daily ops email's per-yard frozen list names the yards the SITE
 * marks (yard_health.json listState, written by scraper/yard_freshness.py),
 * with the same "since" date; a separate early-warning list keeps the old
 * 3-weekday rule for yards the site does not mark yet; a file without list
 * fields keeps the old behaviour.
 * Run: node backend/test/ops_yard_list_unit.mjs */
import { yardFlags } from '../src/ops_monitor.js';

let failures = 0;
const check = (name, cond, extra = '') => { console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${!cond && extra ? ' — ' + extra : ''}`); if (!cond) failures++; };

// Wed 2026-11-18 13:47 UTC, the data the freshness work measured on.
const NOW = '2026-11-18T13:47:46Z';
const H = { scrapedAt: NOW, yards: {
  // marked on the site (listState), dates from listChangedAt
  'Wrench-A-Part - Holland': { count: 1113, lastChangedAt: '2026-10-22T02:14:15Z', listChangedAt: '2026-10-22T02:14:15Z', listState: 'frozen', unchangedScans: 144 },
  'Youngstown U-Pull-It': { count: 1557, lastChangedAt: '2026-11-06T00:39:55Z', listChangedAt: '2026-11-06T00:39:55Z', listState: 'stale', unchangedScans: 71 },
  // id-only date earlier than the id|date one: the email follows the site
  "Army's Auto Wrecking - Lima": { count: 234, lastChangedAt: '2026-11-17T23:47:19Z', listChangedAt: '2026-11-10T06:39:38Z', listState: 'stale', unchangedScans: 2 },
  // 2 business days, 3 weekdays (today counted): early warning only
  'Pull-A-Part - Canton': { count: 1129, lastChangedAt: '2026-11-13T18:43:19Z', listChangedAt: '2026-11-13T18:43:19Z', unchangedScans: 23 },
  // fresh
  'Pick-n-Pull - Fremont': { count: 900, lastChangedAt: '2026-11-18T08:41:39Z', listChangedAt: '2026-11-18T08:41:39Z', unchangedScans: 1 },
  // carried and marked: on the site with "could not read", so listed, tagged
  'Carried Yard - Bartow': { count: 879, lastChangedAt: '2026-11-06T11:46:31Z', listChangedAt: '2026-11-06T11:46:31Z', listReadAt: '2026-11-17T23:47:19Z', listState: 'stale', carried: true, unchangedScans: 66 },
  // missing: not on the site, not listed as marked
  'Gone Yard - Toledo': { count: 300, lastChangedAt: '2026-10-21T00:00:00Z', listChangedAt: '2026-10-21T00:00:00Z', listState: 'frozen', missingScans: 40, missingReason: 'blocked' },
} };
const f = yardFlags(H);
const names = (l) => l.map((y) => y.name);
check('list mode on when the file has list fields', f.listMode === true);
check('marked list = the yards with listState (missing excluded), oldest first',
  JSON.stringify(names(f.frozen)) === JSON.stringify(['Wrench-A-Part - Holland', 'Youngstown U-Pull-It', 'Carried Yard - Bartow', "Army's Auto Wrecking - Lima"]), JSON.stringify(names(f.frozen)));
check('since = listChangedAt (the date the site prints)', f.frozen.find((y) => y.name.startsWith('Army')).lastChangedAt === '2026-11-10T06:39:38Z');
check('state and not-read tags carried', f.frozen[0].state === 'frozen' && f.frozen.find((y) => y.name.startsWith('Carried')).notRead === true);
check('carried yard still listed in its own line', JSON.stringify(names(f.carried)) === JSON.stringify(['Carried Yard - Bartow']));
check('early warning: 3 weekdays, not marked yet', JSON.stringify(names(f.frozenSoon)) === JSON.stringify(['Pull-A-Part - Canton']), JSON.stringify(f.frozenSoon));
check('a marked yard is never also in the early warning', !f.frozenSoon.some((y) => names(f.frozen).includes(y.name)));

// A file from before the scan wrote list fields: the old 3-weekday rule.
const old = { scrapedAt: NOW, yards: Object.fromEntries(Object.entries(H.yards).map(([n, y]) => {
  const o = { ...y }; delete o.listChangedAt; delete o.listState; delete o.listReadAt; return [n, o];
})) };
const g = yardFlags(old);
check('old file: list mode off, no early-warning list', g.listMode === false && g.frozenSoon.length === 0);
check('old file: the 3-weekday rule as before (carried and missing excluded)',
  JSON.stringify(names(g.frozen)) === JSON.stringify(['Wrench-A-Part - Holland', 'Youngstown U-Pull-It', 'Pull-A-Part - Canton']), JSON.stringify(names(g.frozen)));

console.log(failures ? `\n${failures} FAILED` : '\nALL PASS');
process.exit(failures ? 1 : 0);
