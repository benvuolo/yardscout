/* Native-device (FCM / Android) alerts e2e against `wrangler dev` — run by
 * test/e2e-devices.sh with mock-fcm.mjs standing in for both Google
 * endpoints. The mock VERIFIES the Worker's RS256 service-account assertion,
 * so the OAuth path is genuinely exercised.
 *
 * Covers the full Android parity matrix:
 *   register (fcmToken) → instant dispatch for Pro → dedupe → free-tier
 *   weekly recap (not instant) → token pruning on UNREGISTERED → token
 *   stealing on reinstall.
 */

const BASE = process.env.YS_TEST_BASE || 'http://localhost:8794';
const MOCK = process.env.YS_MOCK_BASE || 'http://127.0.0.1:8797';
const ADMIN = { 'x-admin-secret': 'dev-admin-secret-change-me' };
const UPLOAD = { 'x-upload-token': 'dev-upload-token-change-me' };

let failures = 0;
function check(name, cond, extra = '') {
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${extra ? ' — ' + extra : ''}`);
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
const sentList = async () => (await fetch(MOCK + '/sent')).json();

// FCM-ish tokens (>=80 chars of the documented charset).
const fcmTok = (label) => `${label}:APA91b${'x'.repeat(100)}`;
const uuid = () => crypto.randomUUID();

const OGDEN = { location: 'Utah Pick-A-Part - Ogden', city: 'Ogden', state: 'UT', lat: 41.19, lng: -111.94 };
const arrival = (id, overrides = {}) => ({
  id, year: 1998, make: 'Toyota', model: '4Runner', row: '42',
  dateAdded: '2026-10-20', ...OGDEN, ...overrides,
});
const commit = (newArrivals) => api('/v1/admin/inventory/commit',
  J(UPLOAD, { directory: { yards: [], scrapedAt: new Date().toISOString() }, manifest: {} , newArrivals }));
const waitDispatch = () => new Promise((res) => setTimeout(res, 2500));

/* ---- 1. register: a Pro Android device with one watch ---- */
const proId = uuid();
const proToken = fcmTok('pro-device');
let r = await api('/v1/device/register', J({}, {
  deviceId: proId, fcmToken: proToken, tier: 'pro',
  watches: [{ make: 'Toyota', model: '4Runner', lat: 40.76, lng: -111.89, radiusMi: 100 }],
}));
check('pro android device registers (push ready)', r.status === 200 && r.data.push === true, JSON.stringify(r.data));

/* platform defaults to android when only an fcmToken is sent */
const probe = uuid();
r = await api('/v1/device/register', J({}, { deviceId: probe, fcmToken: fcmTok('probe'), tier: 'free',
  watches: [{ make: 'Honda', lat: 40.76, lng: -111.89, radiusMi: 50 }] }));
check('fcm-only register accepted', r.status === 200);

/* bad tokens rejected (register succeeds but token is not stored → push:false) */
r = await api('/v1/device/register', J({}, { deviceId: uuid(), fcmToken: 'way-too-short', tier: 'pro' }));
check('short/garbage fcm token not stored', r.status === 200 && r.data.push === false);

/* ---- 2. instant dispatch: Pro hears, free does not ---- */
const freeId = uuid();
const freeToken = fcmTok('free-device');
r = await api('/v1/device/register', J({}, {
  deviceId: freeId, fcmToken: freeToken, tier: 'free',
  watches: [{ make: 'Toyota', model: '4Runner', lat: 40.76, lng: -111.89, radiusMi: 100 }],
}));
check('free android device registers', r.status === 200);

r = await commit([arrival(9001), arrival(9002, { id: 9002, make: 'Honda', model: 'Civic' })]);
check('commit accepted', r.status === 200 && r.data.arrivals === 2);
await waitDispatch();

let sent = await sentList();
const proSends = sent.filter((s) => s.token === proToken);
const freeSends = sent.filter((s) => s.token === freeToken);
check('pro device pushed instantly (exactly one)', proSends.length === 1, `got ${proSends.length}`);
check('free device NOT pushed instantly', freeSends.length === 0, `got ${freeSends.length}`);
if (proSends.length) {
  check('push names the matching car only', /4Runner/.test(proSends[0].body) && !/Civic/.test(proSends[0].body), proSends[0].body);
  check('push carries a deep-link url in data', typeof proSends[0].data.url === 'string');
  check('deep link is the alert form with the vehicle id (#alert=<id>)',
    /^\/#alert=9001$/.test(proSends[0].data.url), proSends[0].data.url);
}

/* ---- 3. dedupe: same commit again → no second push ---- */
r = await commit([arrival(9001)]);
await waitDispatch();
sent = await sentList();
check('repeat commit sends nothing (dedupe)', sent.filter((s) => s.token === proToken).length === 1);

/* ---- 4. weekly recap: free tier hears once, Pro skipped ---- */
r = await api('/v1/admin/device-digest/run', { method: 'POST', headers: ADMIN });
check('device digest runs', r.status === 200, JSON.stringify(r.data));
sent = await sentList();
const freeWeekly = sent.filter((s) => s.token === freeToken);
check('free device got the weekly recap', freeWeekly.length === 1, `got ${freeWeekly.length}`);
check('weekly recap is a digest, not an instant alert', /week/i.test(freeWeekly[0]?.title || ''), freeWeekly[0]?.title);
check('weekly recap deep-links to the first arrival (#alert=<id>)',
  /^\/#alert=9001$/.test(freeWeekly[0]?.data?.url || ''), freeWeekly[0]?.data?.url);
check('pro device skipped by weekly digest', sent.filter((s) => s.token === proToken).length === 1);

r = await api('/v1/admin/device-digest/run', { method: 'POST', headers: ADMIN });
await waitDispatch();
sent = await sentList();
check('weekly rerun sends nothing (dedupe)', sent.filter((s) => s.token === freeToken).length === 1);

/* ---- 5. token pruning: UNREGISTERED tokens are cleared like APNs 410 ---- */
const deadId = uuid();
r = await api('/v1/device/register', J({}, {
  deviceId: deadId, fcmToken: fcmTok('dead-token'), tier: 'pro',
  watches: [{ make: 'Toyota', model: '4Runner', lat: 40.76, lng: -111.89, radiusMi: 100 }],
}));
check('doomed device registers', r.status === 200 && r.data.push === true);

/* device/test exercises send + prune without an inventory commit */
r = await api('/v1/device/test', J({}, { deviceId: deadId }));
check('test push to dead token reports not-ok', r.status === 200 && r.data.ok === false, JSON.stringify(r.data));
r = await api('/v1/device/test', J({}, { deviceId: deadId }));
check('dead token was pruned (second test → 404 no_token)', r.status === 404 && r.data.error === 'no_token', JSON.stringify(r.data));

/* a healthy device still passes the same endpoint */
r = await api('/v1/device/test', J({}, { deviceId: proId }));
check('test push to live token ok', r.status === 200 && r.data.ok === true);

/* ---- 6. admin synthetic dispatch (the ops/emulator smoke path) ---- */
const before = (await sentList()).filter((s) => s.token === proToken).length;
r = await api('/v1/admin/device-alerts/dispatch', J(ADMIN, { arrivals: [arrival(9100)] }));
check('admin dispatch runs production path', r.status === 200 && r.data.devices === 1, JSON.stringify(r.data));
sent = await sentList();
check('admin dispatch delivered to pro device', sent.filter((s) => s.token === proToken).length === before + 1);
r = await api('/v1/admin/device-alerts/dispatch', J(ADMIN, { arrivals: [arrival(9100)] }));
check('admin dispatch dedupes too', r.status === 200 && r.data.devices === 0, JSON.stringify(r.data));

/* ---- 7. reinstall steals the token from the stale row ---- */
const newInstall = uuid();
r = await api('/v1/device/register', J({}, {
  deviceId: newInstall, fcmToken: proToken, tier: 'pro',
  watches: [{ make: 'Toyota', model: '4Runner', lat: 40.76, lng: -111.89, radiusMi: 100 }],
}));
check('reinstall re-registers same token under new deviceId', r.status === 200 && r.data.push === true);
r = await api('/v1/device/test', J({}, { deviceId: proId }));
check('old row lost the token (404 no_token)', r.status === 404 && r.data.error === 'no_token', JSON.stringify(r.data));
r = await api('/v1/device/test', J({}, { deviceId: newInstall }));
check('new row owns the token', r.status === 200 && r.data.ok === true);

/* ---- 7. first-watch check-in: once, ~48 h after the first watch, only
 *         if something landed; gives up silently after 7 quiet days ---- */
const chkId = uuid(), chkToken = fcmTok('checkin-device');
r = await api('/v1/device/register', J({}, { deviceId: chkId, fcmToken: chkToken, tier: 'free',
  watches: [{ make: 'Toyota', model: 'Tacoma', lat: 40.76, lng: -111.89, radiusMi: 100 }] }));
check('check-in device registers', r.status === 200);
const quietId = uuid(), quietToken = fcmTok('quiet-device');
r = await api('/v1/device/register', J({}, { deviceId: quietId, fcmToken: quietToken, tier: 'free',
  watches: [{ make: 'Saab', model: '9-3', lat: 40.76, lng: -111.89, radiusMi: 100 }] }));
r = await commit([arrival(9101, { make: 'Toyota', model: 'Tacoma', row: '7' }), arrival(9102, { make: 'Toyota', model: 'Tacoma', row: '9' })]);
await waitDispatch();
const runChk = (h) => api('/v1/admin/checkins/run', { method: 'POST', headers: { ...ADMIN, 'content-type': 'application/json' }, body: JSON.stringify({ nowOffsetHours: h }) });
r = await runChk(0);
let chk = (await sentList()).filter((s) => s.token === chkToken);
check('no check-in before 48 h', chk.length === 0, `got ${chk.length}`);
r = await runChk(49);
chk = (await sentList()).filter((s) => s.token === chkToken);
check('one check-in after 48 h', chk.length === 1, `got ${chk.length} ${JSON.stringify(r.data)}`);
check('check-in names the watch', /Since you started watching Toyota Tacoma/.test(chk[0]?.title || ''), chk[0]?.title);
check('check-in lists what landed', /2 landed within 100 mi/.test(chk[0]?.body || ''), chk[0]?.body);
check('check-in deep-links to a car', /^\/#alert=910[12]$/.test(chk[0]?.data?.url || ''), chk[0]?.data?.url);
check('quiet device gets nothing', (await sentList()).filter((s) => s.token === quietToken).length === 0);
r = await runChk(60);
check('check-in never repeats', (await sentList()).filter((s) => s.token === chkToken).length === 1);
r = await runChk(24 * 8);
check('quiet device given up after 7 days, silently', r.data.gaveUp >= 1 && (await sentList()).filter((s) => s.token === quietToken).length === 0, JSON.stringify(r.data));
r = await api('/v1/admin/device-digest/run', { method: 'POST', headers: ADMIN });
check('weekly recap does not repeat the check-in cars', (await sentList()).filter((s) => s.token === chkToken).length === 1);

/* ---- ops send accounting (src/ops.js): every FCM outcome is counted ----
 * ok = accepted sends above; gone = the UNREGISTERED device; fail = a real
 * provider error (mock answers 500 for "server-error" tokens). */
const errId = uuid();
r = await api('/v1/device/register', J({}, { deviceId: errId, fcmToken: fcmTok('server-error'), tier: 'pro',
  watches: [{ make: 'Subaru', model: 'Outback', lat: 40.76, lng: -111.89, radiusMi: 100 }] }));
r = await api('/v1/admin/device-alerts/dispatch', J(ADMIN, { arrivals: [arrival(9301, { make: 'Subaru', model: 'Outback' })] }));
check('provider 500 → send not ok', r.status === 200 && r.data.sends === 1 && r.data.devices === 0, JSON.stringify(r.data));
const okSends = (await sentList()).length;
r = await api('/v1/admin/ops/daily/run', J(ADMIN, { dryRun: true }));
const fcmStats = r.data.channels?.fcm || {};
check('ops counter: fcm ok = accepted sends', fcmStats.ok === okSends, `${JSON.stringify(fcmStats)} vs ${okSends}`);
check('ops counter: fcm gone counted (dead token)', fcmStats.gone >= 1, JSON.stringify(fcmStats));
check('ops counter: fcm fail = 1 (provider 500)', fcmStats.fail === 1, JSON.stringify(fcmStats));
const fe = (r.data.recentErrors || []).find((e) => e.channel === 'fcm');
check('fcm error row: status 500, no token in detail', fe && fe.status === 500 && !/APA91b|server-error/.test(fe.detail || ''), JSON.stringify(fe));
check('push-ready device counts reported', Number.isInteger(r.data.audience?.proDevices) && r.data.audience.proDevices >= 1, JSON.stringify(r.data.audience));

/* ---- free cap counts KEPT watches: a dropped centre-less watch must not
 * push the 5th valid one out (it used to: slice(0, 5) ran before the drop). */
const capId = uuid(), capToken = fcmTok('cap-device');
const near = { lat: 40.76, lng: -111.89, radiusMi: 100 };
r = await api('/v1/device/register', J({}, { deviceId: capId, fcmToken: capToken, tier: 'free', watches: [
  { make: 'Ford', model: 'Ranger' },                       // no centre → dropped for free
  ...['Kia Rio', 'Kia Soul', 'Kia Optima', 'Kia Sedona'].map((m) => ({ make: 'Kia', model: m.slice(4), ...near })),
  { make: 'Mazda', model: 'MX-5 Miata', ...near },         // 5th valid watch
] }));
check('cap device registers', r.status === 200);
await commit([arrival(9501, { make: 'Mazda', model: 'MX-5 Miata' })]);
await waitDispatch();
r = await api('/v1/admin/device-digest/run', { method: 'POST', headers: ADMIN });
const capSends = (await sentList()).filter((s) => s.token === capToken);
check('5th valid free watch survives a dropped one (recap names the Miata)', capSends.length === 1 && /Miata|MX-5/.test(capSends[0].body), JSON.stringify(capSends));

/* ---- free instant alert (2026-11-16): ONE flagged watch per free device,
 * cars within 50 mi of its centre, from the budget Pro leaves ---- */
const SLC = { lat: 40.76, lng: -111.89 };
// ~80 mi due south of the watch centre: inside the 100 mi watch, past 50 mi.
const FAR = { location: 'Far South Yard', city: 'Far', state: 'UT', lat: 39.60, lng: -111.89 };
const tokensSent = async (tok) => (await sentList()).filter((s) => s.token === tok);

const oldFreeId = uuid(), oldFreeTok = fcmTok('old-free');
r = await api('/v1/device/register', J({}, { deviceId: oldFreeId, fcmToken: oldFreeTok, tier: 'free',
  watches: [{ make: 'Volvo', model: '240', ...SLC, radiusMi: 100 }] }));
check('old-style free register (no flag): no instant in the answer', r.status === 200 && !('instant' in r.data), JSON.stringify(r.data));

const instId = uuid(), instTok = fcmTok('inst-free');
r = await api('/v1/device/register', J({}, { deviceId: instId, fcmToken: instTok, tier: 'free', watches: [
  { make: 'Volvo', model: '740', ...SLC, radiusMi: 100 },
  { make: 'Volvo', model: '240', ...SLC, radiusMi: 100, instant: true },
] }));
check('flagged free watch kept as instant, clamped to 50 mi',
  r.status === 200 && r.data.instant && r.data.instant.model === '240' && r.data.instant.radiusMi === 50, JSON.stringify(r.data));

const smallId = uuid(), smallTok = fcmTok('inst-small');
r = await api('/v1/device/register', J({}, { deviceId: smallId, fcmToken: smallTok, tier: 'free',
  watches: [{ make: 'Volvo', model: '240', ...SLC, radiusMi: 25, instant: true }] }));
check('instant radius keeps a smaller watch radius (25 mi)', r.data.instant && r.data.instant.radiusMi === 25, JSON.stringify(r.data));

const proVolvoId = uuid(), proVolvoTok = fcmTok('pro-volvo');
r = await api('/v1/device/register', J({}, { deviceId: proVolvoId, fcmToken: proVolvoTok, tier: 'pro',
  watches: [{ make: 'Volvo', model: '', instant: true }] }));
check('pro register ignores the flag (no instant row)', r.status === 200 && !('instant' in r.data), JSON.stringify(r.data));

const twoId = uuid(), twoTok = fcmTok('two-flags');
r = await api('/v1/device/register', J({}, { deviceId: twoId, fcmToken: twoTok, tier: 'free', watches: [
  { make: 'Volvo', model: '940', ...SLC, radiusMi: 100, instant: true },
  { make: 'Volvo', model: '240', ...SLC, radiusMi: 100, instant: true },
] }));
check('two flags: the first one is kept', r.data.instant && r.data.instant.model === '940', JSON.stringify(r.data));

// Ogden is ~30 mi from the centre: inside 50, outside 25.
await commit([
  arrival(9601, { make: 'Volvo', model: '240', row: '3' }),
  arrival(9602, { make: 'Volvo', model: '240', row: '4', ...FAR }),
  arrival(9603, { make: 'Volvo', model: '740', row: '5' }),
]);
await waitDispatch();
let inst = await tokensSent(instTok);
check('flagged free watch: one instant push', inst.length === 1, `got ${inst.length}`);
check('instant push is the Pro arrivals push for the car inside 50 mi only',
  /just hit the yard/.test(inst[0]?.title || '') && /240 — Utah Pick-A-Part - Ogden/.test(inst[0]?.body || '')
  && !/Far South/.test(inst[0]?.body || '') && !/740/.test(inst[0]?.body || ''), `${inst[0]?.title} | ${inst[0]?.body}`);
check('instant push deep-links to the car', inst[0]?.data?.url === '/#alert=9601', inst[0]?.data?.url);
check('old-style free device: no instant push', (await tokensSent(oldFreeTok)).length === 0);
check('25 mi instant watch: no push for a car ~30 mi out', (await tokensSent(smallTok)).length === 0);
check('two flags: the unflagged-in-effect watch (240) gets no instant push', (await tokensSent(twoTok)).length === 0);
const proV = await tokensSent(proVolvoTok);
check('pro still gets every match at any distance', proV.length === 1 && /Far South/.test(proV[0].body) && /740/.test(proV[0].body), proV[0]?.body);

r = await api('/v1/admin/device-digest/run', { method: 'POST', headers: ADMIN });
inst = await tokensSent(instTok);
const instWeekly = inst[1];
check('Monday summary still comes for the instant device', inst.length === 2 && /week/i.test(instWeekly?.title || ''), JSON.stringify(inst.map((s) => s.title)));
check('Monday summary holds the far car and the other watch, not the pushed one',
  /Far South/.test(instWeekly?.body || '') && /740/.test(instWeekly?.body || '') && !/row 3/.test(instWeekly?.body || ''), instWeekly?.body);
check('Monday summary names what the instant alert did not cover',
  /Both are outside your instant alert \(Volvo 240, 50 mi\); Pro pushes every watch at any distance\./.test(instWeekly?.body || ''), instWeekly?.body);
const oldWeekly = (await tokensSent(oldFreeTok))[0];
check('old-style free device: Monday summary unchanged (both 240s, Pro line as before)',
  /row 3/.test(oldWeekly?.body || '') && /Far South/.test(oldWeekly?.body || '') && /Pro would have pushed these the day they landed/.test(oldWeekly?.body || '')
  && !/instant/.test(oldWeekly?.body || ''), oldWeekly?.body);
const twoWeekly = (await tokensSent(twoTok))[0];
check('two-flag device: the 240s wait for Monday', /row 3/.test(twoWeekly?.body || ''), twoWeekly?.body);

/* the flag moves with one re-registration; a build that stops sending it
 * goes back to Monday-only */
r = await api('/v1/device/register', J({}, { deviceId: instId, fcmToken: instTok, tier: 'free', watches: [
  { make: 'Volvo', model: '740', ...SLC, radiusMi: 100, instant: true },
  { make: 'Volvo', model: '240', ...SLC, radiusMi: 100 },
] }));
check('moving the flag re-registers as the 740', r.data.instant && r.data.instant.model === '740', JSON.stringify(r.data));
await commit([arrival(9604, { make: 'Volvo', model: '740', row: '6' }), arrival(9605, { make: 'Volvo', model: '240', row: '7' })]);
await waitDispatch();
inst = await tokensSent(instTok);
check('after the move: pushed for the 740 only', inst.length === 3 && /740/.test(inst[2].body) && !/row 7/.test(inst[2].body), inst[2]?.body);
r = await api('/v1/device/register', J({}, { deviceId: instId, fcmToken: instTok, tier: 'free', watches: [
  { make: 'Volvo', model: '740', ...SLC, radiusMi: 100 },
] }));
await commit([arrival(9606, { make: 'Volvo', model: '740', row: '8' })]);
await waitDispatch();
check('flag dropped (old build): no instant push', (await tokensSent(instTok)).length === 3);

/* Pro first when the budget is tight: 25 Pro devices use every outside call
 * this commit may make (the shared commit budget, src/commit_budget.js; the
 * suite runs it at 25 with COMMIT_EXT_CEILING_TEST), the free instant device
 * is carried and also waits for Monday */
const saabPro = [];
for (let i = 0; i < 25; i++) {
  const id = uuid(), tok = fcmTok(`saab-pro-${i}`);
  saabPro.push(tok);
  // The register route allows 30 a minute per IP: on a 429, wait the window out.
  const reg = () => api('/v1/device/register', J({}, { deviceId: id, fcmToken: tok, tier: 'pro', watches: [{ make: 'Saab', model: '900' }] }));
  let rr = await reg();
  if (rr.status === 429) { await new Promise((res) => setTimeout(res, 61_000)); rr = await reg(); }
  if (rr.status !== 200) check(`saab pro ${i} registers`, false, JSON.stringify(rr));
}
const saabFreeId = uuid(), saabFreeTok = fcmTok('saab-free');
await api('/v1/device/register', J({}, { deviceId: saabFreeId, fcmToken: saabFreeTok, tier: 'free',
  watches: [{ make: 'Saab', model: '900', ...SLC, radiusMi: 100, instant: true }] }));
// The production path (commit → waitUntil dispatch), so the car is also stored for Monday.
await commit([arrival(9701, { make: 'Saab', model: '900', row: '11' })]);
await new Promise((res) => setTimeout(res, 5000));
let proGot = 0;
for (const tok of saabPro) proGot += (await tokensSent(tok)).length;
check('tight budget: every Pro device pushed', proGot === 25, `got ${proGot}`);
check('tight budget: free instant device not pushed (Pro used all 25 outside calls of the commit)', (await tokensSent(saabFreeTok)).length === 0);
r = await api('/v1/admin/device-alerts/dispatch', J(ADMIN, { arrivals: [arrival(9702, { make: 'Saab', model: '900', row: '12' })] }));
check('admin path agrees: 25 sends, all Pro, no free instant', r.data.sends === 25 && r.data.freeInstant === 0, JSON.stringify(r.data));
r = await api('/v1/admin/device-digest/run', { method: 'POST', headers: ADMIN });
const saabWeekly = await tokensSent(saabFreeTok);
check('the car the budget cut is in the Monday summary', saabWeekly.length === 1 && /week/i.test(saabWeekly[0].title) && /row 11/.test(saabWeekly[0].body), JSON.stringify(saabWeekly));
check('a cut car is not claimed as outside the instant alert', !/outside your instant alert/.test(saabWeekly[0]?.body || ''), saabWeekly[0]?.body);

/* one phone, one row: a token moved to a new device id leaves the old row
 * unpushable, so one arrival reaches the phone once */
const phoneTok = fcmTok('one-phone');
const oldInstall = uuid(), newInstall2 = uuid();
await api('/v1/device/register', J({}, { deviceId: oldInstall, fcmToken: phoneTok, tier: 'free',
  watches: [{ make: 'Volvo', model: '850', ...SLC, radiusMi: 100, instant: true }] }));
await api('/v1/device/register', J({}, { deviceId: newInstall2, fcmToken: phoneTok, tier: 'free',
  watches: [{ make: 'Volvo', model: '850', ...SLC, radiusMi: 100, instant: true }] }));
// (/v1/device/test allows 5 an hour per IP and the tests above used them, so
// the check is the dispatch itself: both rows carry the same instant watch,
// and the phone must hear once.)
const phoneBefore = (await tokensSent(phoneTok)).length;
r = await api('/v1/admin/device-alerts/dispatch', J(ADMIN, { arrivals: [arrival(9801, { make: 'Volvo', model: '850' })] }));
check('token moved: old row cleared, one instant push reaches the phone once',
  (await tokensSent(phoneTok)).length === phoneBefore + 1 && r.data.freeInstant === 1, JSON.stringify(r.data));

/* daily ops email counts free instant pushes */
r = await api('/v1/admin/ops/daily/run', J(ADMIN, { dryRun: true }));
check('ops: free instant pushes counted (24 h)', r.data.freeInstant24h >= 3, String(r.data.freeInstant24h));
check('ops email text carries the free instant line', /of the app pushes, free instant alerts: \d+/.test(r.data.email?.text || ''));
check('ops email keeps free-instant out of the channel rows', !/^\s+free-instant\s/m.test(r.data.email?.text || ''));

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
