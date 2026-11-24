/* Unit: the hourly backup scan trigger (src/scan_watchdog.js). It dispatches
 * a scan only when none is active and the newest successful scan, in EITHER
 * of GitHub's two answers, started 5 h or more ago (2026-11-24: a scan was
 * dispatched two hours after a successful one).
 * Run: node backend/test/scan_watchdog_unit.mjs */
import { runScanWatchdog } from '../src/scan_watchdog.js';

let failures = 0;
const check = (name, cond, extra = '') => { console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${!cond && extra ? ' — ' + extra : ''}`); if (!cond) failures++; };
const NOW = Date.parse('2026-11-24T18:23:46Z');
const run = (startedAt, conclusion = 'success', status = 'completed') => ({ run_started_at: startedAt, created_at: startedAt, status, conclusion });

async function watch({ plain, filtered, plainStatus = 200, filteredStatus = 200, dispatchStatus = 204, token = 't' }) {
  const calls = [];
  const real = globalThis.fetch;
  globalThis.fetch = async (url, init = {}) => {
    calls.push({ url: String(url), method: init.method || 'GET' });
    const json = (status, body) => ({ ok: status >= 200 && status < 300, status, json: async () => body });
    if (String(url).includes('/dispatches')) return json(dispatchStatus, {});
    if (String(url).includes('status=success')) return json(filteredStatus, { workflow_runs: filtered });
    return json(plainStatus, { workflow_runs: plain });
  };
  try { return { r: await runScanWatchdog({ SCAN_DISPATCH_TOKEN: token }, { now: NOW }), calls }; } finally { globalThis.fetch = real; }
}
const posted = (calls) => calls.filter((c) => c.method === 'POST').length;

let x = await watch({ plain: [], filtered: [], token: '' });
check('no token: nothing asked, nothing dispatched', x.r.action === 'skipped' && x.calls.length === 0, JSON.stringify(x));

x = await watch({ plain: [run('2026-11-24T18:00:00Z', null, 'in_progress'), run('2026-11-24T10:23:48Z')], filtered: [run('2026-11-24T10:23:48Z')] });
check('a scan is running: none', x.r.action === 'none' && x.r.reason === 'scan active' && posted(x.calls) === 0, JSON.stringify(x.r));

// The case of 2026-11-24 18:23: the plain list has the scan that started 16:23 and succeeded, the filtered list is behind.
x = await watch({ plain: [run('2026-11-24T16:23:48Z'), run('2026-11-24T10:23:48Z')], filtered: [run('2026-11-24T10:23:48Z')] });
check('filtered list behind, plain list has a success 2 h ago: fresh, no dispatch', x.r.action === 'none' && x.r.reason === 'fresh' && x.r.ageHours === 2 && posted(x.calls) === 0, JSON.stringify(x.r));

x = await watch({ plain: [run('2026-11-24T16:23:48Z', 'failure'), run('2026-11-24T10:23:48Z')], filtered: [run('2026-11-24T16:23:48Z')] });
check('plain list behind, filtered list has a success 2 h ago: fresh, no dispatch', x.r.action === 'none' && x.r.reason === 'fresh' && posted(x.calls) === 0, JSON.stringify(x.r));

x = await watch({ plain: [run('2026-11-24T16:23:48Z', 'failure'), run('2026-11-24T10:23:48Z')], filtered: [run('2026-11-24T10:23:48Z')] });
check('newest success 8 h ago in both (a later run failed): dispatched once', x.r.action === 'dispatched' && x.r.ageHours === 8 && posted(x.calls) === 1, JSON.stringify(x.r));

x = await watch({ plain: [run('2026-11-24T13:23:46Z')], filtered: [run('2026-11-24T13:23:46Z')] });
check('exactly 5 h: dispatched', x.r.action === 'dispatched' && posted(x.calls) === 1, JSON.stringify(x.r));
x = await watch({ plain: [run('2026-11-24T13:24:47Z')], filtered: [run('2026-11-24T13:24:47Z')] });
check('one minute short of 5 h: fresh', x.r.action === 'none' && x.r.reason === 'fresh' && posted(x.calls) === 0, JSON.stringify(x.r));

x = await watch({ plain: [], filtered: [] });
check('no successful scan on record: dispatched', x.r.action === 'dispatched' && posted(x.calls) === 1, JSON.stringify(x.r));

x = await watch({ plain: [], filtered: [], plainStatus: 502 });
check('GitHub answers an error on the list: error, no dispatch', x.r.action === 'error' && x.r.status === 502 && posted(x.calls) === 0, JSON.stringify(x.r));
x = await watch({ plain: [run('2026-11-24T10:23:48Z')], filtered: [], filteredStatus: 403 });
check('GitHub answers an error on the filtered list: error, no dispatch', x.r.action === 'error' && x.r.status === 403 && posted(x.calls) === 0, JSON.stringify(x.r));
x = await watch({ plain: [run('2026-11-24T10:23:48Z')], filtered: [run('2026-11-24T10:23:48Z')], dispatchStatus: 422 });
check('the dispatch itself is refused: error', x.r.action === 'error' && x.r.status === 422, JSON.stringify(x.r));

console.log(failures ? `\n${failures} FAILED` : '\nALL PASS');
process.exit(failures ? 1 : 0);
