/* Unit: a chain unchanged only across a weekend or overnight is "quiet"
 * (no full 14:00-22:00 UTC weekday block inside the window), not an issue.
 * Run: node backend/test/ops_quiet_unit.mjs */
import { fullBusinessDaysBetween as f } from '../src/ops_monitor.js';

let failures = 0;
const check = (name, cond, extra = '') => { console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${!cond && extra ? ' — ' + extra : ''}`); if (!cond) failures++; };
const t = (s) => Date.parse(s);
// 2026-11-06 is a Friday, 11-07 Sat, 11-08 Sun, 11-09 Mon, 11-10 Tue.
const cases = [
  ['Sat evening -> Mon 10:06 (the 2026-11-09 email): quiet', '2026-11-07T18:48Z', '2026-11-09T10:06Z', 0],
  ['Fri evening -> Mon morning: quiet', '2026-11-06T18:48Z', '2026-11-09T10:06Z', 0],
  ['Sun -> Mon 13:00 (business day under way, not finished): quiet', '2026-11-08T10:32Z', '2026-11-09T13:00Z', 0],
  ['Sat -> Mon 22:30 (Monday passed with no change): 1', '2026-11-07T18:48Z', '2026-11-09T22:30Z', 1],
  ['Sat -> Tue 10:00: 1 (Monday)', '2026-11-07T18:48Z', '2026-11-10T10:00Z', 1],
  ['Fri 06:00 -> Mon 10:00: 1 (all of Friday)', '2026-11-06T06:00Z', '2026-11-09T10:00Z', 1],
  ['Thu 17:00 -> Fri 12:00 overnight: quiet', '2026-11-05T17:00Z', '2026-11-06T12:00Z', 0],
  ['Thu 17:00 -> Fri 23:00: 1 (Friday)', '2026-11-05T17:00Z', '2026-11-06T23:00Z', 1],
  ['Mon 09:00 -> Wed 23:00: 3', '2026-11-09T09:00Z', '2026-11-11T23:00Z', 3],
  ['reversed window: 0', '2026-11-10T00:00Z', '2026-11-09T00:00Z', 0],
];
for (const [name, a, b, want] of cases) { const got = f(t(a), t(b)); check(name, got === want, `got ${got}, want ${want}`); }
console.log(failures ? `\n${failures} FAILURE(S)` : '\nALL PASS');
process.exit(failures ? 1 : 0);
