/* Ops-monitoring e2e against `wrangler dev` — run by test/e2e-ops.sh with
 * mock-resend.mjs standing in for Resend and the public data files.
 *
 * Covers: send counters (ok + fail, scrubbed error detail) → a forced Resend
 * failure makes /v1/auth/request-link return an error → the hourly check
 * fires a stale-data alert ONCE (dedupe), reminds after 6 h, sends one
 * all-clear on recovery → Resend 403 + channel-failure alerts combine into
 * one email → the daily report has every section (dryRun sends nothing) →
 * admin auth.
 */

const BASE = process.env.YS_TEST_BASE || 'http://127.0.0.1:8795';
const MOCK = process.env.YS_MOCK_BASE || 'http://127.0.0.1:8798';
const ADMIN = { 'x-admin-secret': 'dev-admin-secret-change-me' };
const UPLOAD = { 'x-upload-token': 'dev-upload-token-change-me' };
const OWNER = 'owner@example.com';

let failures = 0;
function check(name, cond, extra = '') {
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${extra && !cond ? ' — ' + extra : ''}`);
  if (!cond) failures++;
}
async function api(path, opts = {}) {
  const r = await fetch(BASE + path, opts);
  return { status: r.status, data: await r.json().catch(() => ({})) };
}
const J = (headers, body) => ({
  method: 'POST', headers: { ...headers, 'content-type': 'application/json' },
  body: JSON.stringify(body),
});
const mockGet = async (p) => (await fetch(MOCK + p)).json();
const mockMode = (status, message = '') => fetch(MOCK + '/mode', {
  method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ status, message }),
});
const opsSent = async () => (await mockGet('/sent')).filter((m) => (m.to || []).includes(OWNER));
const checkRun = (body = {}) => api('/v1/admin/ops/check/run', J(ADMIN, body));
const dailyRun = (body = {}) => api('/v1/admin/ops/daily/run', J(ADMIN, body));
const requestLink = (email) => api('/v1/auth/request-link', J({}, { email }));

/* ---- 0. admin auth ---- */
let r = await api('/v1/admin/ops/check/run', J({}, { dryRun: true }));
check('check run requires x-admin-secret', r.status === 401, `got ${r.status}`);
r = await api('/v1/admin/ops/daily/run', J({ 'x-admin-secret': 'nope' }, { dryRun: true }));
check('daily run rejects a bad secret', r.status === 401, `got ${r.status}`);

/* ---- 1. no inventory yet → stale (dry run computes, sends nothing) ---- */
r = await checkRun({ dryRun: true });
check('dry check run: no commit yet → stale active', r.status === 200 && r.data.active.some((c) => c.id === 'stale'), JSON.stringify(r.data));
check('dry check run sends nothing', r.data.sent === false && r.data.reason === 'dry run' && (await opsSent()).length === 0);

/* ---- 2. fresh commit ---- */
r = await api('/v1/admin/inventory/commit', J(UPLOAD, {
  directory: { yards: [['Y1'], ['Y2'], ['Y3']], scrapedAt: new Date().toISOString(), counts: { yards: 3, vehicles: 1541 } },
  manifest: {},
}));
check('commit accepted', r.status === 200, JSON.stringify(r.data));

r = await checkRun();
check('fresh data: no open conditions, no email', r.data.active.length === 0 && r.data.sent === false && (await opsSent()).length === 0, JSON.stringify(r.data));

/* ---- 3. stale alert: once, deduped, reminder after 6 h, one all-clear ---- */
r = await checkRun({ nowOffsetHours: 7 });
let ops = await opsSent();
check('+7 h: stale alert fires', r.data.alerted.includes('stale') && r.data.sent === true, JSON.stringify(r.data));
check('+7 h: exactly one ops email', ops.length === 1, `got ${ops.length}`);
check('alert subject starts with [YardScout alert] and names staleness',
  /^\[YardScout alert\] Inventory data is stale: last scan commit 7(\.\d)? h ago/.test(ops[0]?.subject || ''), ops[0]?.subject);
check('alert body says what to check', /Check: GitHub Actions/.test(ops[0]?.text || '') && /PROBLEM:/.test(ops[0]?.text || ''), ops[0]?.text);
check('alert is plain text from EMAIL_FROM', !!ops[0]?.text && /yardscout\.io/.test(ops[0]?.from || ''), ops[0]?.from);

r = await checkRun({ nowOffsetHours: 8 });
check('+8 h: deduped (no second email)', r.data.alerted.length === 0 && r.data.deduped.includes('stale') && (await opsSent()).length === 1, JSON.stringify(r.data));
r = await checkRun({ nowOffsetHours: 11 });
check('+11 h: still deduped', (await opsSent()).length === 1 && r.data.sent === false);

r = await checkRun({ nowOffsetHours: 13.5 });
ops = await opsSent();
check('+13.5 h: one reminder after 6 h', r.data.alerted.includes('stale') && ops.length === 2, JSON.stringify(r.data));
check('reminder says still open', /still open/.test(ops[1]?.text || ''), ops[1]?.text);

r = await checkRun();   // real now: the commit is fresh again
ops = await opsSent();
check('recovery: all-clear sent once', r.data.cleared.includes('stale') && r.data.sent === true && ops.length === 3, JSON.stringify(r.data));
check('all-clear subject', /^\[YardScout alert\] All clear: data stale/.test(ops[2]?.subject || ''), ops[2]?.subject);
r = await checkRun();
check('after recovery: silent', r.data.sent === false && r.data.cleared.length === 0 && (await opsSent()).length === 3, JSON.stringify(r.data));

/* ---- 4. counters: ok ---- */
r = await requestLink('tester1@users.test');
check('request-link with Resend OK → {sent:true}', r.status === 200 && r.data.sent === true && !r.data.dev_link, JSON.stringify(r.data));
const linkMail = (await mockGet('/sent')).find((m) => (m.to || []).includes('tester1@users.test'));
check('magic link actually went through (mock) Resend', !!linkMail && /\/v1\/auth\/callback\?token=/.test(linkMail.text || ''));

r = await dailyRun({ dryRun: true });
check('counter: email:auth ok = 1', r.data.channels?.['email:auth']?.ok === 1, JSON.stringify(r.data.channels));
check('counter: email:ops ok = 3 (alerts above)', r.data.channels?.['email:ops']?.ok === 3, JSON.stringify(r.data.channels));
check('Resend today counts all ok emails (4)', r.data.resend?.sentToday === 4 && r.data.resend?.dailyCap === 100, JSON.stringify(r.data.resend));

/* ---- 5. forced Resend failure → request-link errors; counted + scrubbed ---- */
await mockMode(403, `You can only send testing emails to your own email address (${OWNER}). key re_live_abcdefghijklmnop`);
r = await requestLink('tester2@users.test');
check('request-link with Resend 403 → 502 email_failed', r.status === 502 && r.data.error === 'email_failed', `${r.status} ${JSON.stringify(r.data)}`);
check('…and NOT {sent:true}', r.data.sent !== true);
r = await dailyRun({ dryRun: true });
check('counter: email:auth fail = 1', r.data.channels?.['email:auth']?.fail === 1, JSON.stringify(r.data.channels));
const e0 = (r.data.recentErrors || [])[0] || {};
check('error row: channel + status', e0.channel === 'email:auth' && e0.status === 403, JSON.stringify(e0));
check('error detail scrubbed: no full emails, no keys', !/owner@example\.com|tester2@|re_live_/.test(e0.detail || '') && /\*@example\.com/.test(e0.detail || ''), e0.detail);
check("error detail keeps recipient domain only", /^to \*@users\.test: /.test(e0.detail || ""), e0.detail);

r = await checkRun({ dryRun: true });
check('dry check: Resend 403 → resend-limit active', r.data.active.some((c) => c.id === 'resend-limit'), JSON.stringify(r.data.active));
check('dry check: 1 failure is not yet a channel alert', !r.data.active.some((c) => c.id === 'fail:email:auth'));

await requestLink('tester3@users.test');
await requestLink('tester4@users.test');
r = await checkRun({ dryRun: true });
check('3 failures in the last hour → fail:email:auth active', r.data.active.some((c) => c.id === 'fail:email:auth'), JSON.stringify(r.data.active));

await mockMode(200);
r = await checkRun();
ops = await opsSent();
check('both problems go out in ONE email', r.data.sent === true && ops.length === 4
  && r.data.alerted.includes('resend-limit') && r.data.alerted.includes('fail:email:auth'), JSON.stringify(r.data));
check('combined subject', /^\[YardScout alert\] 2 problems: /.test(ops[3]?.subject || ''), ops[3]?.subject);
check('alert email leaks no user email / key', !/tester\d@users|re_live_|re_test_mock/.test(ops[3]?.text || ''), ops[3]?.text);
console.log('\n----- sample alert emails -----\n' + [ops[0], ops[2], ops[3]].map((m) => `${m.subject}\n\n${m.text}`).join('\n=====\n') + '-------------------------------\n');
r = await checkRun();
check('re-run within 6 h: deduped', r.data.sent === false && (await opsSent()).length === 4, JSON.stringify(r.data));

/* ---- 6. daily report (dry run): every section present ---- */
const before = (await opsSent()).length;
r = await dailyRun({ dryRun: true });
const d = r.data;
const text = d.email?.text || '';
check('daily dry run: 200 + not sent', r.status === 200 && d.dryRun === true && d.sent === false && (await opsSent()).length === before, JSON.stringify(d).slice(0, 300));
check('daily subject + verdict', /^\[YardScout daily\] 2 issues · 3 yards · 1,541 cars$/.test(d.email?.subject || ''), d.email?.subject);
check('daily: scan commit time + age', !!d.scan?.lastCommitAt && d.scan.ageHours >= 0 && d.scan.ageHours < 1, JSON.stringify(d.scan));
check('daily: live yard + vehicle counts', d.inventory?.yards === 3 && d.inventory?.vehicles === 1541 && d.inventory?.publicVehicles === 1541, JSON.stringify(d.inventory));
check('daily: dormant yards listed', JSON.stringify(d.yardHealth?.dormant?.map((y) => y.name).sort()) === JSON.stringify(['Dormant Yard - Orem', 'Ghost Yard - Lehi']), JSON.stringify(d.yardHealth));
check('daily: frozen yards listed (3+ d; a 2.5 d lull is not frozen; missing/carried excluded)', JSON.stringify(d.yardHealth?.frozen?.map((y) => y.name)) === JSON.stringify(['Ghost Yard - Lehi', 'Frozen Yard - Provo']), JSON.stringify(d.yardHealth));
check('daily: carried yards listed separately', JSON.stringify(d.yardHealth?.carried?.map((y) => y.name)) === JSON.stringify(['Carried Yard - Bartow']), JSON.stringify(d.yardHealth?.carried));
check('daily: renamed/missing yard not dormant or frozen', !JSON.stringify(d.yardHealth).includes('Renamed Yard'), JSON.stringify(d.yardHealth));
check('daily: per-channel 24 h sends', d.channels?.['email:auth']?.ok === 1 && d.channels?.['email:auth']?.fail === 3 && d.channels?.['email:ops']?.ok === 4, JSON.stringify(d.channels));
check('daily: audience counts', d.audience && ['proDevices', 'freeDevices', 'emailWatchers'].every((k) => Number.isInteger(d.audience[k])), JSON.stringify(d.audience));
check('daily: usage loads', d.usage && !d.usage.error && Number.isInteger(d.usage.devices?.total) && typeof d.usage.funnel === 'object', JSON.stringify(d.usage));
check('daily: open conditions', d.openConditions?.length === 2, JSON.stringify(d.openConditions));
for (const sec of ['Verdict: 2 issues', 'OPEN ISSUES (2)', 'SCAN', 'Last commit:', 'Live: 3 yards · 1,541 vehicles', 'Watchdog:',
  'YARD HEALTH', 'Dormant Yard - Orem', 'Frozen Yard - Provo', 'Re-serving last copy', 'Carried Yard - Bartow', 'SENDS, last 24 h', 'email:auth', 'Resend today (UTC): 5 / 100', 'USAGE', 'App devices:', 'Funnel (all platforms)', 'Purchases']) {
  check(`daily text has "${sec}"`, text.includes(sec));
}
check('daily text leaks no user email', !/tester\d@users/.test(text));
const html = d.email?.html || '';
check('daily html part present', html.startsWith('<!doctype html>') && html.length > 2000, String(html.length));
for (const sec of ['YardScout daily', 'Open issues', 'Scan', 'Yard health', 'Alerts sent', 'Users', 'Funnel', '2 issues', 're-serving last copy', 'Carried Yard - Bartow']) {
  check(`daily html has "${sec}"`, html.includes(sec));
}
check('daily html leaks no user email', !/tester\d@users/.test(html));
check('daily html escapes yard names', !/<script/i.test(html));
console.log('\n----- sample daily email (dry run) -----\n' + d.email?.subject + '\n\n' + text + '----------------------------------------\n');

/* ---- 6b. usage: funnel counters land in "yesterday" when the clock moves a day ---- */
const ev = (e, extra = {}) => fetch(BASE + '/v1/events', { method: 'POST', headers: { 'content-type': 'text/plain' },
  body: JSON.stringify({ e, p: 'ios', ...extra }) });
await ev('first-visit', { src: 'reddit', cmp: 'r-4runner' }); await ev('first-visit'); await ev('checkout-start');
await ev('paywall/part-value'); await ev('paywall/part-value'); await ev('paywall/watch-limit'); await ev('checkout/watch-limit'); await ev('purchase/watch-limit');
r = await dailyRun({ dryRun: true, nowOffsetHours: 24 });
const u = r.data.usage || {};
check('usage: yesterday funnel counts', u.funnel?.['first-visit']?.yesterday === 2 && u.funnel?.['first-visit']?.week === 2
  && u.funnel?.['checkout-start']?.yesterday === 1, JSON.stringify(u.funnel));
check('usage: gates ranked by purchases', JSON.stringify(u.gates) === JSON.stringify([
  { gate: 'watch-limit', paywall: 1, checkout: 1, purchase: 1 }, { gate: 'part-value', paywall: 2, checkout: 0, purchase: 0 }]), JSON.stringify(u.gates));
check('usage: email lists gates', /Pro sheet by gate[\s\S]*watch-limit\s+1 \/ 1 \/ 1[\s\S]*part-value\s+2 \/ 0 \/ 0/.test(r.data.email?.text || ''), (r.data.email?.text || '').split('USAGE')[1]);
check('usage: tagged source listed', JSON.stringify(u.sources) === JSON.stringify([{ source: 'reddit', n: 1 }]), JSON.stringify(u.sources));
check('usage: email shows source + checkout taps', /Tagged sources \(first visits, 7 d\): reddit 1/.test(r.data.email?.text || '')
  && /Checkout taps\s+1\s+1/.test(r.data.email?.text || ''), (r.data.email?.text || '').split('USAGE')[1]);

/* ---- 7. daily run (send) ---- */
r = await dailyRun();
ops = await opsSent();
check('daily run sends one [YardScout daily] email', r.data.sent === true && ops.length === before + 1 && /^\[YardScout daily\]/.test(ops.at(-1)?.subject || ''), JSON.stringify(r.data.sent));

/* ---- 8. the real cron branches (wrangler dev --test-scheduled) ---- */
const allBefore = (await mockGet('/sent')).length;
const opsBefore = (await opsSent()).length;
await fetch(BASE + '/__scheduled?cron=' + encodeURIComponent('7 13 * * *'));
await new Promise((res) => setTimeout(res, 2500));
ops = await opsSent();
check('cron "7 13 * * *" sends the daily email', ops.length === opsBefore + 1 && /^\[YardScout daily\]/.test(ops.at(-1)?.subject || ''), ops.at(-1)?.subject);
await fetch(BASE + '/__scheduled?cron=' + encodeURIComponent('23 * * * *'));
await new Promise((res) => setTimeout(res, 2500));
r = await api('/v1/health');
check('cron "23 * * * *" runs the watchdog first (decision stored)', r.data.scanWatchdog?.last?.action === 'skipped', JSON.stringify(r.data.scanWatchdog));
check('hourly cron: open problems stay deduped (no new email)', (await opsSent()).length === opsBefore + 1);
check('neither cron sent any user email (no Monday digest)', (await mockGet('/sent')).length === allBefore + 1);

/* ---- 9. production guard: the clock offset is DEV-only (sanity: present here) ---- */
r = await checkRun({ dryRun: true, nowOffsetHours: 30 });
check('offset honored in DEV_MODE', r.data.active.some((c) => c.id === 'stale'));

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
