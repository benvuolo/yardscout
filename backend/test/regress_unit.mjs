/* Unit test: tools/regress.sh, the regression runner (2026-11-18).
 *
 *   coverage   --list holds every backend and site-proxy *_unit.mjs, every
 *              scraper/test_*.py, every self-contained *_e2e.mjs / *_e2e.py,
 *              the six API suites and the layout check at six widths; what it
 *              leaves out is exactly the list in its header, each with a reason
 *   behaviour  on a copy of the runner in a scratch tree of fake tests (its
 *              own lock file and port list, so it never waits on, or watches,
 *              the real ones): one log per test, one summary line per test,
 *              exit 1 when a test fails (with the failing log's tail), exit 0
 *              when all pass, --quick runs units and scraper tests only, a
 *              test that leaves a server on a watched port fails, and the
 *              lock is waited for
 *
 * Run: node backend/test/regress_unit.mjs */
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import net from 'node:net';
import os from 'node:os';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const ROOT = path.resolve(HERE, '../..');
const RUNNER = path.join(ROOT, 'tools/regress.sh');
let failures = 0, passes = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + String(detail).slice(0, 700)}`); if (ok) passes++; else failures++; };

check('tools/regress.sh exists and is executable', fs.existsSync(RUNNER) && (fs.statSync(RUNNER).mode & 0o111) !== 0);
const src = fs.readFileSync(RUNNER, 'utf8');
check('it takes the shared lock itself (flock /tmp/ys-test.lock)', /LOCK="\$\{YS_TEST_LOCK:-\/tmp\/ys-test\.lock\}"/.test(src) && /exec env YS_REGRESS_HOLDS_LOCK=1 flock "\$LOCK"/.test(src));
check('the header documents --quick, --list, --only, --out and the left-out suites', ['--quick', '--list', '--only', '--out', 'Left out on purpose'].every((w) => src.split('set -uo pipefail')[0].includes(w)));

/* ---------- coverage, from --list on the real tree ---------- */
const list = spawnSync('bash', [RUNNER, '--list'], { encoding: 'utf8', cwd: ROOT });
check('--list runs without the lock and exits 0', list.status === 0, list.stderr);
const listed = new Set(list.stdout.split('\n').map((l) => l.trim().split(/\s+/)[1]).filter(Boolean));
const rel = (dir, re) => fs.readdirSync(path.join(ROOT, dir)).filter((f) => re.test(f)).map((f) => `${dir}/${f}`);
const units = [...rel('backend/test', /_unit\.mjs$/), ...rel('backend/site-proxy/test', /_unit\.mjs$/)];
const scraper = rel('scraper', /^test_.*\.py$/);
const e2e = [...rel('backend/test', /_e2e\.mjs$/), ...rel('backend/test', /_e2e\.py$/)];
const LEFT_OUT = ['map_regions_e2e.mjs', 'alerts_e2e.mjs', 'billing_e2e.py', 'device_alerts_e2e.mjs', 'ops_e2e.mjs', 'email_alerts_e2e.mjs', 'recap_signup_e2e.mjs', 'free_email_alert_e2e.mjs'];
const missing = (xs) => xs.filter((x) => !listed.has(x));
check(`every unit test is listed (${units.length})`, units.length >= 25 && !missing(units).length, missing(units).join(', '));
check(`every scraper test is listed (${scraper.length})`, scraper.length >= 10 && !missing(scraper).length, missing(scraper).join(', '));
const wantE2e = e2e.filter((f) => !LEFT_OUT.includes(path.basename(f)));
check(`every self-contained browser suite is listed (${wantE2e.length})`, !missing(wantE2e).length, missing(wantE2e).join(', '));
check('...and nothing on the left-out list is (each named with a reason in the header)', e2e.filter((f) => LEFT_OUT.includes(path.basename(f)) && path.basename(f) !== 'browser_e2e.py').every((f) => !listed.has(f))
  && LEFT_OUT.every((n) => src.includes(n.replace(/_e2e\.mjs$/, '')) ), [...listed].filter((x) => LEFT_OUT.some((n) => x.endsWith(n))).join(', '));
for (const s of ['e2e.sh', 'e2e-ops.sh', 'e2e-devices.sh', 'e2e-coverage.sh', 'e2e-email.sh', 'browser_e2e.py']) {
  check(`API suite listed: ${s}`, list.stdout.split('\n').some((l) => /^api\s/.test(l) && l.trim().endsWith(`backend/test/${s}`)));
}
check('the layout check at its six widths, as two halves', /layout\s+backend\/test\/ui_no_truncation\.mjs WIDTHS=320,375,390 \| WIDTHS=430,768,1280/.test(list.stdout));
const quickList = spawnSync('bash', [RUNNER, '--list', '--quick'], { encoding: 'utf8', cwd: ROOT }).stdout;
check('--quick lists units and scraper tests only', quickList.trim().split('\n').every((l) => /^(unit|scraper)\s/.test(l)) && quickList.includes('scraper/'), quickList.split('\n').filter((l) => !/^(unit|scraper)\s/.test(l)).slice(0, 3).join(' | '));

/* ---------- behaviour, on a scratch tree ---------- */
const freePort = () => new Promise((res) => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => res(p)); }); });
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ys-regress-unit-'));
const put = (f, body) => { fs.mkdirSync(path.dirname(path.join(tmp, f)), { recursive: true }); fs.writeFileSync(path.join(tmp, f), body); };
put('tools/regress.sh', src); fs.chmodSync(path.join(tmp, 'tools/regress.sh'), 0o755);
put('backend/test/a_unit.mjs', "console.log('a ok');\n");
put('backend/test/b_unit.mjs', "console.log('the b check'); console.log('boom: expected 2, got 3'); process.exit(1);\n");
put('backend/site-proxy/test/c_unit.mjs', "console.log('c ok');\n");
put('scraper/test_d.py', "print('d ok')\n");
const leakPort = await freePort();
put('backend/test/leak_e2e.mjs', `import { spawn } from 'node:child_process';
const c = spawn(process.execPath, ['-e', "require('http').createServer((q, r) => r.end()).listen(${leakPort}, '127.0.0.1')"], { detached: true, stdio: 'ignore' });
c.unref();
await new Promise((r) => setTimeout(r, 700));
console.log('started a server and did not stop it');
`);
spawnSync('git', ['init', '-q'], { cwd: tmp });
const LOCKF = path.join(tmp, 'lock');
const env = { ...process.env, YS_TEST_LOCK: LOCKF, YS_REGRESS_PORTS: String(leakPort) };
delete env.YS_REGRESS_HOLDS_LOCK;
const runIt = (args, outName) => spawnSync('bash', [path.join(tmp, 'tools/regress.sh'), ...args, '--out', path.join(tmp, outName)], { encoding: 'utf8', env, cwd: tmp });

const q = runIt(['--quick'], 'out-q');
const sumQ = fs.existsSync(path.join(tmp, 'out-q/summary.txt')) ? fs.readFileSync(path.join(tmp, 'out-q/summary.txt'), 'utf8') : '';
check('--quick on a tree with one failing unit: exit 1', q.status === 1, `status ${q.status}\n${q.stdout}\n${q.stderr}`);
check('one summary line per test, the failure with its exit code', /PASS\s+\d+s\s+unit\s+backend\/test\/a_unit\.mjs/.test(sumQ) && /FAIL \(exit 1\)\s+\d+s\s+unit\s+backend\/test\/b_unit\.mjs/.test(sumQ)
  && /PASS\s+\d+s\s+unit\s+backend\/site-proxy\/test\/c_unit\.mjs/.test(sumQ) && /PASS\s+\d+s\s+scraper\s+scraper\/test_d\.py/.test(sumQ), sumQ);
check('...and a total line', /──── 3 passed, 1 failed, 0 skipped \(--quick: units and scraper tests only\) ────/.test(sumQ), sumQ);
check('--quick ran no browser suite', !/leak_e2e/.test(sumQ));
check('one log per test, in the log directory', ['backend_test_a_unit.mjs.log', 'backend_test_b_unit.mjs.log', 'scraper_test_d.py.log'].every((f) => fs.existsSync(path.join(tmp, 'out-q/logs', f))));
check('the failing test\'s output is shown at the end', /Not passed/.test(q.stdout) && /boom: expected 2, got 3/.test(q.stdout), q.stdout);

fs.rmSync(path.join(tmp, 'backend/test/b_unit.mjs'));
const ok = runIt(['--quick'], 'out-ok');
check('all passing: exit 0', ok.status === 0, `status ${ok.status}\n${ok.stdout}`);

const leak = runIt(['--only', 'leak_e2e'], 'out-leak');
const sumL = fs.existsSync(path.join(tmp, 'out-leak/summary.txt')) ? fs.readFileSync(path.join(tmp, 'out-leak/summary.txt'), 'utf8') : '';
check('a test that exits 0 but leaves a server on a watched port fails', leak.status === 1 && new RegExp(`FAIL \\(left a server on :${leakPort}\\)\\s+\\d+s\\s+browser\\s+backend/test/leak_e2e\\.mjs`).test(sumL), sumL + leak.stderr);
check('--only ran just that test', !/a_unit|test_d/.test(sumL), sumL);
for (const pid of (spawnSync('bash', ['-c', `lsof -nP -t -iTCP:${leakPort} -sTCP:LISTEN || true`], { encoding: 'utf8' }).stdout || '').trim().split(/\s+/).filter(Boolean)) {
  try { process.kill(Number(pid), 'SIGKILL'); } catch { /* gone */ }
}

{
  // The lock: held by "another session" for 2 s; the runner waits, then runs.
  const holder = spawn('flock', [LOCKF, 'sleep', '2'], { stdio: 'ignore' });
  await new Promise((r) => setTimeout(r, 300));
  const t0 = Date.now();
  const w = runIt(['--quick'], 'out-wait');
  const took = Date.now() - t0;
  check('the lock: a run waits for it, says so, then runs', w.status === 0 && took >= 1500 && /waiting for .*lock/.test(w.stdout), `status ${w.status}, ${took} ms\n${w.stdout}`);
  holder.kill();
}

fs.rmSync(tmp, { recursive: true, force: true });
console.log(failures ? `\n${failures} FAILURE(S), ${passes} passed` : `\nALL PASS (${passes})`);
process.exit(failures ? 1 : 0);
