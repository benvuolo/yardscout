/* Unit test: test suites stop the servers they start, and refuse a port that
 * is taken (2026-11-18). On 11-17 e2e.sh failed 3 of 39 because it talked
 * to a server an earlier run had left on its port: `npx wrangler dev` is a
 * tree (npx -> node wrangler -> node -> workerd), and the suites killed only
 * the npx PID (or walked its children after a middle process had gone), so
 * workerd lived on. backend/test/servers.sh now starts every server in a
 * process group of its own and stops the whole group on any exit;
 * browser_e2e.py does the same in Python.
 *
 *   static     every shell suite that starts wrangler dev or a mock server
 *              sources servers.sh, checks its ports, starts servers through
 *              ys_start and sets no trap of its own; browser_e2e.py starts
 *              its servers in their own session and checks its ports
 *   behaviour  servers.sh, on OS-picked ports (no fixed port, no wrangler):
 *              a server whose launcher has exited (the workerd shape) is
 *              gone after a normal end, a failed check (`exit 1`), and a
 *              SIGTERM from a runner; a control shows the old trap (kill
 *              the PID) leaving it behind; a taken port is refused with exit
 *              2 and a clear message; ys_stop waits for the port to close
 *   python     browser_e2e.py's start_group / stop_group / need_ports, the same
 *
 * Run: node backend/test/servers_unit.mjs (starts small local servers on
 * free ports; run it under the shared test lock like any server test). */
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import net from 'node:net';
import os from 'node:os';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const BACKEND = path.resolve(HERE, '..');
const LIB = path.join(HERE, 'servers.sh');
let failures = 0, passes = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + String(detail).slice(0, 600)}`); if (ok) passes++; else failures++; };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* ---------- static: every suite that starts a server uses the helper ---------- */
const suites = [
  ...fs.readdirSync(HERE).filter((f) => f.endsWith('.sh') && f !== 'servers.sh').map((f) => path.join(HERE, f)),
  ...fs.readdirSync(path.join(BACKEND, 'site-proxy/test')).filter((f) => f.endsWith('.sh')).map((f) => path.join(BACKEND, 'site-proxy/test', f)),
];
const starters = suites.filter((f) => /wrangler dev|mock-[a-z]+\.mjs/.test(fs.readFileSync(f, 'utf8')));
check('the server-starting shell suites are found (5 API suites + the site-proxy one)', starters.length >= 6, starters.map((f) => path.basename(f)).join(', '));
for (const f of starters) {
  const src = fs.readFileSync(f, 'utf8');
  const code = src.split('\n').filter((l) => !/^\s*#/.test(l)).join('\n');
  const name = path.relative(BACKEND, f);
  check(`${name}: sources servers.sh`, /^source .*servers\.sh/m.test(code));
  check(`${name}: checks its ports before starting (ys_need_port)`, /ys_need_port "?\$\{?PORT/.test(code));
  if (/MOCKPORT/.test(code)) check(`${name}: checks the mock's port too`, /ys_need_port "?\$\{?MOCKPORT/.test(code));
  check(`${name}: no server started with a bare "&" (only through ys_start)`, !/^\s*(npx wrangler dev|node test\/mock-[a-z]+\.mjs)\b/m.test(code),
    (code.match(/^\s*(npx wrangler dev|node test\/mock-[a-z]+\.mjs).*$/m) || [''])[0]);
  check(`${name}: sets no trap of its own (servers.sh owns EXIT / INT / TERM)`, !/^\s*trap\b/m.test(code), (code.match(/^\s*trap\b.*$/m) || [''])[0]);
  check(`${name}: no kill of a bare PID left (the old kill / kill_tree)`, !/\bkill_tree\b|^\s*kill \$/m.test(code));
}
{
  const py = fs.readFileSync(path.join(HERE, 'browser_e2e.py'), 'utf8');
  check('browser_e2e.py: servers start in their own session (start_new_session)', /start_new_session=True/.test(py) && /start_group\(\s*\[\s*"npx", "wrangler", "dev"/.test(py));
  check('browser_e2e.py: stops the whole group, never terminate() on npx alone', /os\.killpg\(/.test(py) && !/\.terminate\(\)/.test(py));
  check('browser_e2e.py: refuses taken ports first thing in main()', /def main\(\):\n\s+need_ports\(API_PORT, WEB_PORT\)/.test(py));
}

/* ---------- behaviour of servers.sh ---------- */
const freePort = () => new Promise((res) => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => res(p)); }); });
const portOpen = (port) => new Promise((res) => {
  const c = net.connect({ port, host: '127.0.0.1' });
  c.once('connect', () => { c.destroy(); res(true); });
  c.once('error', () => res(false));
  c.setTimeout(500, () => { c.destroy(); res(false); });
});
const waitClosed = async (port, ms = 4000) => { for (let t = 0; t < ms; t += 100) { if (!(await portOpen(port))) return true; await sleep(100); } return false; };
const waitOpen = async (port, ms = 6000) => { for (let t = 0; t < ms; t += 100) { if (await portOpen(port)) return true; await sleep(100); } return false; };
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ys-servers-unit-'));
// A server whose launcher exits at once, so it is re-parented away from the
// process the suite started (as workerd is once npx / wrangler go): only a
// process-group stop reaches it. A plain leader (sleep) keeps the group's id.
fs.writeFileSync(path.join(tmp, 'server.js'), "require('http').createServer((q, r) => r.end('ok')).listen(+process.argv[2], '127.0.0.1');\n");
const treeCmd = (port) => `bash -c 'node ${path.join(tmp, 'server.js')} ${port} & disown; exec sleep 300'`;
const suite = (body) => { const f = path.join(tmp, `suite-${Math.random().toString(36).slice(2)}.sh`); fs.writeFileSync(f, `set -euo pipefail\nsource ${LIB}\n${body}\n`); return f; };
const pidsOn = (port) => (spawnSync('bash', ['-c', `command -v lsof >/dev/null && lsof -nP -t -iTCP:${port} -sTCP:LISTEN || true`], { encoding: 'utf8' }).stdout || '').trim().split(/\s+/).filter(Boolean);
const killPort = (port) => { for (const pid of pidsOn(port)) { try { process.kill(Number(pid), 'SIGKILL'); } catch { /* gone */ } } };

for (const [label, tail, how] of [
  ['a normal end', 'true', 'end'],
  ['a failed check (exit 1)', 'exit 1', 'end'],
  ['a SIGTERM from a runner', 'sleep 30', 'term'],
]) {
  const port = await freePort();
  const f = suite(`ys_need_port ${port} "test server"\nys_start ${tmp}/s.log ${treeCmd(port)}\nfor i in $(seq 1 60); do (exec 3<>/dev/tcp/127.0.0.1/${port}) 2>/dev/null && break; sleep 0.1; done\nif (exec 3<>/dev/tcp/127.0.0.1/${port}) 2>/dev/null; then echo UP; else echo NEVER-UP; fi\n${tail}`);
  const child = spawn('bash', [f], { stdio: ['ignore', 'pipe', 'pipe'] });
  const done = new Promise((r) => child.on('close', (c, sig) => r(c ?? sig)));   // before any await: it may end quickly
  let out = '';
  child.stdout.on('data', (d) => { out += d; });
  // The suite itself says when its server answered (a quick suite may be
  // gone again before a poll from out here would see it).
  if (how === 'term') { for (let t = 0; t < 80 && !/\bUP\b/.test(out); t++) await sleep(100); child.kill('SIGTERM'); }
  const code = await done;
  const up = /^UP$/m.test(out);
  const closed = await waitClosed(port);
  check(`servers.sh, ${label}: the server came up, and is gone after (port ${port} closed)`, up && closed, `up=${up} closed=${closed} exit=${code} left=${pidsOn(port)}`);
  if (how === 'term') check('servers.sh: a SIGTERM still exits non-zero (143)', code === 143, String(code));
  if (label === 'a failed check (exit 1)') check('servers.sh: the suite\'s own exit code is kept (1)', code === 1, String(code));
  killPort(port);
}

{
  // Control: the old trap, `kill $PID` of the process the suite started.
  const port = await freePort();
  const f = path.join(tmp, 'old.sh');
  fs.writeFileSync(f, `${treeCmd(port)} >/dev/null 2>&1 &\nPID=$!\ntrap 'kill $PID 2>/dev/null' EXIT\nfor i in $(seq 1 60); do (exec 3<>/dev/tcp/127.0.0.1/${port}) 2>/dev/null && break; sleep 0.1; done\n`);
  spawnSync('bash', [f], { stdio: 'ignore' });
  await sleep(500);
  const left = await portOpen(port);
  check('control: the old trap (kill the PID it started) leaves the server on its port', left, 'the control server did not survive; the behaviour checks above prove less');
  killPort(port);
  check('control: cleaned up after itself', await waitClosed(port));
}

{
  // A taken port: refused, exit 2, a clear message, nothing started.
  const port = await freePort();
  const holder = net.createServer().listen(port, '127.0.0.1');
  await new Promise((r) => holder.once('listening', r));
  const marker = path.join(tmp, 'started');
  const f = suite(`ys_need_port ${port} "wrangler dev"\ntouch ${marker}`);
  const r = spawnSync('bash', [f], { encoding: 'utf8' });
  check('a taken port: the suite refuses with exit 2', r.status === 2, `status ${r.status}`);
  check('...says which port, for what, and what to do', new RegExp(`REFUSING TO START: port ${port}, needed for wrangler dev by suite-.*\\.sh, is already in use`).test(r.stderr)
    && /an earlier run left a server behind/.test(r.stderr) && /pick another port/.test(r.stderr), r.stderr);
  check('...and starts nothing', !fs.existsSync(marker));
  holder.close();
}

{
  // ys_stop between phases (e2e-email.sh, site-proxy e2e.sh): the port is free when it returns.
  const port = await freePort();
  const f = suite(`ys_start ${tmp}/p.log ${treeCmd(port)}\nP=$YS_LAST_PID\nfor i in $(seq 1 60); do (exec 3<>/dev/tcp/127.0.0.1/${port}) 2>/dev/null && break; sleep 0.1; done\nys_stop "$P" ${port}\nif (exec 3<>/dev/tcp/127.0.0.1/${port}) 2>/dev/null; then echo STILL-OPEN; else echo FREED; fi\nys_need_port ${port} "next phase"\necho NEXT-OK`);
  const r = spawnSync('bash', [f], { encoding: 'utf8' });
  check('ys_stop: the port is free when it returns, so the next phase may start', /FREED/.test(r.stdout) && /NEXT-OK/.test(r.stdout) && r.status === 0, r.stdout + r.stderr);
  killPort(port);
}

/* ---------- browser_e2e.py's helpers ---------- */
{
  const port = await freePort(), held = await freePort();
  const holder = net.createServer().listen(held, '127.0.0.1');
  await new Promise((r) => holder.once('listening', r));
  const py = `
import sys, time
sys.path.insert(0, ${JSON.stringify(HERE)})
import browser_e2e as b
p = b.start_group(["bash", "-c", ${JSON.stringify(`node ${path.join(tmp, 'server.js')} ${port} & disown; exec sleep 300`)}])
for _ in range(60):
    if b.port_busy(${port}): break
    time.sleep(0.1)
up = b.port_busy(${port})
b.stop_group(p, ${port})
print("UP" if up else "NOT-UP", "FREED" if not b.port_busy(${port}) else "STILL-OPEN")
try:
    b.need_ports(${held})
    print("NOT-REFUSED")
except SystemExit as e:
    print("REFUSED", e.code)
`;
  const r = spawnSync('python3', ['-c', py], { encoding: 'utf8', cwd: BACKEND });
  check('browser_e2e.py: stop_group stops a server whose launcher has exited', /UP FREED/.test(r.stdout), r.stdout + r.stderr);
  check('browser_e2e.py: need_ports refuses a taken port with exit 2', /REFUSED 2/.test(r.stdout) && /REFUSING TO START: port \d+, needed by browser_e2e\.py/.test(r.stderr), r.stdout + r.stderr);
  holder.close();
  killPort(port);
}

fs.rmSync(tmp, { recursive: true, force: true });
console.log(failures ? `\n${failures} FAILURE(S), ${passes} passed` : `\nALL PASS (${passes})`);
process.exit(failures ? 1 : 0);
