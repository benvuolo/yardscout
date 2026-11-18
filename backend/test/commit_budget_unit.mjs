/* Unit test: one scan commit stays inside the Workers Free limits, whatever
 * the load, and gives way in priority order (src/commit_budget.js, the runner
 * in src/admin.js, every dispatcher it calls). Real handlers on an in-memory
 * SQLite with every migration (a D1 shim over node:sqlite), real push and
 * email code against a stubbed network. No Worker needed.
 *
 * The limits are counted HERE, at the network stub and the D1/KV shim, not by
 * the code under test:
 *   outside calls per commit   must never pass 50 (Workers Free)
 *   D1 + KV calls per commit   must never pass 1,000
 * Then: Pro is served before free, in the documented order; what did not fit
 * is counted and nothing is marked sent for it; later scans deliver it, once.
 *
 * Run: node test/commit_budget_unit.mjs
 * (YS_SRC=/path/to/another/src runs the same load against other sources: on
 * the tree before this change the first checks fail.) */
import { DatabaseSync } from 'node:sqlite';
import { readdirSync, readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const SRC = process.env.YS_SRC
  ? pathToFileURL(resolve(process.env.YS_SRC) + '/').href
  : new URL('../src/', import.meta.url).href;
const load = (f) => import(SRC + f);
const { handleCommit } = await load('admin.js');
const ops = await load('ops.js');

const PLATFORM_EXT = 50, PLATFORM_SVC = 1000;

let failures = 0;
const check = (name, ok, extra = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${extra && !ok ? ' — ' + extra : ''}`); if (!ok) failures++; };
const origLog = console.log;
const logged = [];
console.log = (...a) => { logged.push(a.join(' ')); if (/^(PASS|FAIL|ALL PASS|\d+ FAILURE)/.test(String(a[0]))) origLog(...a); };

/* ---- counters owned by the test ---- */
const seen = { ext: 0, svc: 0, maxInFlight: 0, inFlight: 0 };
const sent = { apns: [], fcm: [], webpush: [], email: [], fcmToken: 0 };
const resetCounts = () => { seen.ext = 0; seen.svc = 0; seen.maxInFlight = 0; };

/* ---- D1 shim: one call per first/all/run/batch, as D1 counts them ---- */
function d1(db) {
  const isRead = (sql) => /^\s*SELECT/i.test(sql);
  const wrap = (sql, args = []) => ({
    bind: (...a) => wrap(sql, a),
    first: async () => { seen.svc++; return db.prepare(sql).get(...args) ?? null; },
    all: async () => { seen.svc++; return { results: db.prepare(sql).all(...args) }; },
    run: async () => { seen.svc++; const r = db.prepare(sql).run(...args); return { meta: { changes: Number(r.changes) } }; },
    _exec: () => (isRead(sql) ? { results: db.prepare(sql).all(...args) } : (db.prepare(sql).run(...args), { results: [] })),
  });
  return {
    prepare: (sql) => wrap(sql),
    batch: async (stmts) => {
      seen.svc++;
      db.exec('BEGIN');
      try { const out = stmts.map((s) => s._exec()); db.exec('COMMIT'); return out; } catch (e) { db.exec('ROLLBACK'); throw e; }
    },
  };
}

/* ---- network stub: every outside call lands here ---- */
globalThis.fetch = async (input, init = {}) => {
  const url = String(input);
  seen.ext++;
  seen.inFlight++;
  seen.maxInFlight = Math.max(seen.maxInFlight, seen.inFlight);
  await new Promise((r) => setTimeout(r, 0));
  seen.inFlight--;
  if (url.startsWith('https://api.push.apple.com/3/device/')) { sent.apns.push(url.split('/').pop()); return new Response('', { status: 200 }); }
  if (url === 'https://oauth2.googleapis.com/token') { sent.fcmToken++; return Response.json({ access_token: 'stub-bearer', expires_in: 3600 }); }
  if (url.startsWith('https://fcm.googleapis.com/')) { sent.fcm.push(JSON.parse(init.body).message.token); return Response.json({ name: 'ok' }); }
  if (url.startsWith('https://push.test/')) { sent.webpush.push(url); return new Response('', { status: 201 }); }
  if (url === 'https://api.resend.com/emails') { const b = JSON.parse(init.body); sent.email.push({ to: b.to[0], subject: b.subject }); return Response.json({ id: 'stub' }); }
  return new Response('not found', { status: 404 });
};

/* ---- real keys, so the real signing and encryption code runs ---- */
const b64u = (buf) => Buffer.from(buf).toString('base64url');
const pem = (der) => `-----BEGIN PRIVATE KEY-----\n${Buffer.from(der).toString('base64').match(/.{1,64}/g).join('\n')}\n-----END PRIVATE KEY-----`;
const vapid = await crypto.subtle.generateKey({ name: 'ECDSA', namedCurve: 'P-256' }, true, ['sign', 'verify']);
const apnsKey = await crypto.subtle.generateKey({ name: 'ECDSA', namedCurve: 'P-256' }, true, ['sign', 'verify']);
const fcmKey = await crypto.subtle.generateKey({ name: 'RSASSA-PKCS1-v1_5', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' }, true, ['sign', 'verify']);
const subKey = await crypto.subtle.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, true, ['deriveBits']);
const KEYS = {
  VAPID_PUBLIC_KEY: b64u(await crypto.subtle.exportKey('raw', vapid.publicKey)),
  VAPID_PRIVATE_JWK: JSON.stringify(await crypto.subtle.exportKey('jwk', vapid.privateKey)),
  VAPID_SUBJECT: 'mailto:ops@example.com',
  APNS_TEAM_ID: 'TEAMID0000', APNS_KEY_ID: 'KEYID00000', APNS_BUNDLE_ID: 'com.example.app',
  APNS_P8: pem(await crypto.subtle.exportKey('pkcs8', apnsKey.privateKey)),
  FCM_PROJECT_ID: 'unit', FCM_SA_EMAIL: 'unit@example.com',
  FCM_SA_KEY: pem(await crypto.subtle.exportKey('pkcs8', fcmKey.privateKey)),
};
const SUB = { p256dh: b64u(await crypto.subtle.exportKey('raw', subKey.publicKey)), auth: b64u(crypto.getRandomValues(new Uint8Array(16))) };

function freshEnv(extra = {}) {
  const db = new DatabaseSync(':memory:');
  const dir = new URL('../migrations/', import.meta.url);
  for (const f of readdirSync(dir).filter((x) => x.endsWith('.sql')).sort()) db.exec(readFileSync(new URL(f, dir), 'utf8'));
  const kv = new Map();
  return {
    raw: db, kv, DB: d1(db),
    ENTITLEMENTS: {
      get: async (k, type) => { seen.svc++; const v = kv.get(k) ?? null; return v && type === 'json' ? JSON.parse(v) : v; },
      put: async (k, v) => { seen.svc++; kv.set(k, v); }, delete: async (k) => { seen.svc++; kv.delete(k); },
    },
    RESEND_API_KEY: 're_test_key', EMAIL_UNSUB_SECRET: 'unit-secret', APP_URL: 'https://yardscout.io/',
    API_PUBLIC_URL: 'https://api.test', EMAIL_FROM: 'YardScout <hello@example.com>',
    EMAIL_ALERTS_FROM: 'YardScout Alerts <alerts@example.com>', OWNER_EMAIL: 'owner@example.com',
    RESEND_DAILY_CAP: '100000',   // the EMAIL budget is another test's subject; here it never binds
    ...KEYS, ...extra,
  };
}

/* ---- the load ---- */
const SLC = { lat: 40.76, lng: -111.89 };
const WATCH = { make: 'Toyota', model: 'Tacoma', year_min: null, year_max: null, ...SLC, radius_mi: 50, drive_filter: null, trim_filter: null };
const NOW = new Date().toISOString();
const OLD = new Date(Date.now() - 72 * 3600_000).toISOString();
const pad = (i) => String(i).padStart(3, '0');
const uuid = (p, i) => `${p}0000000-0000-4000-8000-000000000${pad(i)}`;
const apnsTok = (p, i) => (p + pad(i)).padEnd(64, 'a').replace(/[^0-9a-f]/g, 'b');
const fcmTok = (p, i) => `${p}-${pad(i)}:APA91b`.padEnd(120, 'x');

/** counts: {web, webEmail, proDev, proEmail, freeInstant, checkin, freeEmail, coverage} */
function seed(env, n) {
  const run = (sql, ...a) => env.raw.prepare(sql).run(...a);
  for (let i = 0; i < (n.web || 0) + (n.webEmail || 0); i++) {
    const id = `web-${pad(i)}`;
    run('INSERT INTO users (id, email, tier, created_at) VALUES (?, ?, ?, ?)', id, `${id}@example.com`, 'pro', NOW);
    run('INSERT INTO watches (id, user_id, make, model, lat, lng, radius_mi, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', `w-${id}`, id, 'Toyota', 'Tacoma', SLC.lat, SLC.lng, 50, NOW);
    // The first n.web users have a browser to push to; the rest get the email fallback.
    if (i < (n.web || 0)) run('INSERT INTO push_subscriptions (endpoint, user_id, p256dh, auth, created_at) VALUES (?, ?, ?, ?, ?)', `https://push.test/${id}`, id, SUB.p256dh, SUB.auth, NOW);
  }
  const device = (id, tier, tok, extra = {}) => run(
    `INSERT INTO devices (id, apns_token, fcm_token, platform, tier, watches_json, instant_watch_json, first_watch_at, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    id, tok.apns || null, tok.fcm || null, tok.apns ? 'ios' : 'android', tier, JSON.stringify([WATCH]),
    extra.instant ? JSON.stringify(WATCH) : null, extra.firstWatchAt || NOW, NOW, NOW);
  for (let i = 0; i < (n.proDev || 0); i++) device(uuid('a', i), 'pro', i % 2 ? { fcm: fcmTok('pro', i) } : { apns: apnsTok('a', i) });
  for (let i = 0; i < (n.freeInstant || 0); i++) device(uuid('b', i), 'free', i % 2 ? { fcm: fcmTok('fin', i) } : { apns: apnsTok('b', i) }, { instant: true });
  // Free devices due for the one-time check-in (first watch 72 h ago, no instant watch).
  for (let i = 0; i < (n.checkin || 0); i++) device(uuid('c', i), 'free', { apns: apnsTok('c', i) }, { firstWatchAt: OLD });
  for (let i = 0; i < (n.proEmail || 0); i++) {
    const email = `proemail-${pad(i)}@example.com`;
    run('INSERT INTO email_watchers (email, watches_json, enabled, created_at, updated_at) VALUES (?, ?, 1, ?, ?)', email, JSON.stringify([WATCH]), NOW, NOW);
    env.kv.set('ent:' + email, JSON.stringify({ pro: true }));
  }
  for (let i = 0; i < (n.freeEmail || 0); i++) {
    run('INSERT INTO free_email_alerts (email, created_at, confirmed_at, watch_json, watch_set_at, confirm_sends) VALUES (?, ?, ?, ?, ?, 0)',
      `freealert-${pad(i)}@example.com`, OLD, OLD, JSON.stringify(WATCH), OLD);
  }
  if (n.coverage) run('INSERT INTO coverage_requests (request_key, kind, year, make, model, part, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)', 'k1', 'part', 2004, 'Toyota', 'Tacoma', 'tailgate', NOW);
}

/** A scan's arrivals: `cars` that match everyone's watch, padded with cars
 * that match nobody, up to the scraper's own cap (MAX_ARRIVALS = 4000). */
function arrivals(ids, total = 4000) {
  const out = ids.map((id) => ({ id, year: 2004, make: 'Toyota', model: 'Tacoma', row: '7', location: 'Yard A', city: 'Salt Lake City', state: 'UT', ...SLC, dateAdded: NOW.slice(0, 10) }));
  for (let i = out.length; i < total; i++) out.push({ id: `filler-${i}`, year: 1999, make: 'Honda', model: 'Civic', row: '1', location: 'Yard Z', city: 'Miami', state: 'FL', lat: 25.76, lng: -80.19, dateAdded: NOW.slice(0, 10) });
  return out;
}
const today = NOW.slice(0, 10);
const SALE = [{ chain: 'x', yard: 'Yard A', title: 'Half off', start: today, end: today, pct: 50, ...SLC }];
const DIRECTORY = { yards: [], scrapedAt: NOW, fields: [] };

/** One scan commit, start to finish. Returns what the TEST counted. */
async function commit(env, newArrivals, { saleEvents } = {}) {
  resetCounts();
  for (const k of Object.keys(sent)) sent[k] = Array.isArray(sent[k]) ? [] : 0;
  logged.length = 0;
  const waits = [];
  const res = await handleCommit(new Request('https://api.test/v1/admin/inventory/commit', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ directory: DIRECTORY, manifest: {}, newArrivals, ...(saleEvents ? { saleEvents } : {}) }),
  }), env, { waitUntil: (p) => waits.push(p) });
  const settled = await Promise.all(waits);
  const budget = settled.find((x) => x && x.used && x.cuts) || null;
  return {
    status: res.status, ext: seen.ext, svc: seen.svc, maxInFlight: seen.maxInFlight, budget,
    apns: [...sent.apns], fcm: [...sent.fcm], webpush: [...sent.webpush], email: [...sent.email], fcmToken: sent.fcmToken,
    log: [...logged],
  };
}
const count = (env, sql, ...a) => Number(Object.values(env.raw.prepare(sql).get(...a))[0]);
const heldRows = (env) => Object.fromEntries(env.raw.prepare("SELECT metric, n FROM ops_counters WHERE metric LIKE 'commit%:held'").all().map((r) => [r.metric.replace(/:held$/, ''), r.n]));
const emailsTo = (r, prefix) => r.email.filter((m) => m.to.startsWith(prefix));
const pushesTo = (r, re) => [...r.apns, ...r.fcm].filter((t) => re.test(t)).length;

/* ====================================================================
 * 1. The worst case: every dispatcher has more to send than fits.
 * ==================================================================== */
const WORST = { web: 30, webEmail: 30, proDev: 40, proEmail: 30, freeInstant: 30, checkin: 20, freeEmail: 10, coverage: 1 };
{
  const env = freshEnv();
  seed(env, WORST);
  const r = await commit(env, arrivals(['car-1']), { saleEvents: SALE });
  origLog(`  (worst case: ${r.ext} outside calls, ${r.svc} D1+KV calls; by step ${JSON.stringify(r.budget ? r.budget.by : null)})`);
  check('worst case: the commit is accepted', r.status === 200);
  check(`worst case: outside calls stay under the platform's 50 a commit`, r.ext <= PLATFORM_EXT, `made ${r.ext}`);
  check(`worst case: D1 + KV calls stay under the platform's 1,000 a commit`, r.svc <= PLATFORM_SVC, `made ${r.svc}`);
  check('worst case: one outside call at a time (the steps run in order)', r.maxInFlight === 1, `up to ${r.maxInFlight} at once`);

  const { COMMIT_EXT_CEILING, COMMIT_SVC_CEILING } = await load('commit_budget.js');
  check('the ceiling sits under the limit (45 of 50, 900 of 1,000)', COMMIT_EXT_CEILING === 45 && COMMIT_SVC_CEILING === 900);
  check('worst case: exactly the ceiling was used, no more', r.ext === COMMIT_EXT_CEILING, `made ${r.ext}`);
  check('the budget counted what the network saw', r.budget && r.budget.used.ext === r.ext, r.budget && String(r.budget.used.ext));
  check('the budget counted every D1/KV call but its own final counter write', r.budget && r.budget.used.svc + 1 === r.svc, `${r.budget && r.budget.used.svc} + 1 vs ${r.svc}`);

  // Order of sacrifice: the first step takes it all, every later step gives way.
  check('worst case: Pro web users were served first, with the whole budget', r.webpush.length + emailsTo(r, 'web-').length === 45, `${r.webpush.length} pushes + ${emailsTo(r, 'web-').length} emails`);
  check('worst case: nothing free went out', pushesTo(r, /^b|^fin|^c/) === 0 && emailsTo(r, 'freealert-').length === 0);
  check('worst case: no lower step sent anything', r.apns.length === 0 && r.fcm.length === 0 && emailsTo(r, 'proemail-').length === 0 && emailsTo(r, 'owner@').length === 0);

  // Counted, per step, in the table the ops email reads.
  const held = heldRows(env);
  check('carried: 15 Pro web users', held['commit:pro-webpush'] === 15, JSON.stringify(held));
  check('carried: all 40 Pro devices', held['commit:pro-device'] === 40, JSON.stringify(held));
  check('carried: all 30 Pro email members', held['commit:pro-email'] === 30, JSON.stringify(held));
  check('carried: all 30 free instant devices', held['commit:free-instant'] === 30, JSON.stringify(held));
  check('carried: all 10 free alert emails', held['commit:free-email'] === 10, JSON.stringify(held));
  check('carried: the owner digest', held['commit:coverage'] === 1, JSON.stringify(held));
  check('carried or not looked at: sale pushes and check-ins', held['commit:sales'] >= 1 && held['commit:checkin'] === 1 && held['commit-unchecked:checkin'] === 19, JSON.stringify(held));
  const peak = env.raw.prepare("SELECT metric, n FROM ops_counters WHERE metric LIKE 'commit:%:max'").all();
  // ... and in the daily ops email (ops_monitor.js), read before the later scans add to it.
  {
    const mon = await load('ops_monitor.js');
    const cb = mon.commitBudgetReport(await mon.sendStats(env));
    const lines = mon.commitBudgetLines(cb);
    check('ops email: the busiest scan is one calm line', /^Busiest scan since yesterday \(UTC\): 45 of 45 outside calls, \d+ of 900 database calls$/.test(lines[0] || ''), lines[0]);
    check('ops email: what was carried, per step, Pro named first',
      /^CARRIED TO THE NEXT SCAN by the per-scan call budget \(24 h\): Pro web push alerts 15, Pro app push alerts 40, Pro email alerts 30, .*free instant pushes 30, first-watch check-ins 1, free alert emails 10; not looked at: .*first-watch check-ins 19 \(Pro goes first; a carried Pro alert arrives one scan later\)$/.test(lines[1] || ''), lines[1]);
    check('ops email: carried Pro alerts count as an open issue', cb.pro >= 85, String(cb.pro));
    check('ops email: no line says HELD BACK (other tests look for that word)', !lines.some((l) => /HELD BACK/.test(l)));
  }
  check("the day's busiest commit is recorded", peak.length === 2 && peak.find((p) => p.metric === 'commit:ext:max').n === 45, JSON.stringify(peak));
  check('one summary line in the log', r.log.some((l) => /^commit budget: outside calls 45\/45, D1\+KV calls \d+\/900/.test(l) && /carried to the next scan/.test(l)));

  // Nothing is marked sent for anyone who was not served.
  check('sent rows: 45 web users, nobody else', count(env, 'SELECT COUNT(DISTINCT user_id) FROM alerts_sent') === 45
    && count(env, 'SELECT COUNT(*) FROM device_alerts_sent') === 0 && count(env, 'SELECT COUNT(*) FROM email_alerts_sent') === 0
    && count(env, 'SELECT COUNT(*) FROM free_email_alerts_sent') === 0);
  check('the arrivals were still stored for the Monday recap', count(env, 'SELECT COUNT(*) FROM arrivals') === 4000);
  check('no dispatcher failed or stopped at the ceiling itself', !r.log.some((l) => /failed:|stopped at the commit budget/.test(l)), r.log.filter((l) => /failed:|stopped at/.test(l)).join(' | '));

  /* ---- later scans carry the same 3 days of arrivals: everyone is served, once ---- */
  const got = { web: new Map(), dev: new Map(), proEmail: new Map(), freeEmail: new Map(), owner: 0 };
  const tally = (m, k) => m.set(k, (m.get(k) || 0) + 1);
  const absorb = (x) => {
    for (const u of x.webpush) if (!/sale/.test(u)) tally(got.web, u.split('/').pop());
    for (const m of x.email) {
      if (m.to.startsWith('web-')) tally(got.web, m.to.split('@')[0]);
      else if (m.to.startsWith('proemail-')) tally(got.proEmail, m.to);
      else if (m.to.startsWith('freealert-')) tally(got.freeEmail, m.to);
      else if (m.to.startsWith('owner@')) got.owner++;
    }
    for (const t of [...x.apns, ...x.fcm]) tally(got.dev, t);
  };
  absorb(r);
  let scans = 1, worstExt = r.ext, worstSvc = r.svc, orderOk = true, last = r;
  const STEPS = ops.COMMIT_STEPS.map(([k]) => k);
  const sentBy = (x) => ({
    'pro-webpush': x.webpush.length + emailsTo(x, 'web-').length,   // (sale pushes share the endpoint; see below)
    'pro-email': emailsTo(x, 'proemail-').length,
    coverage: emailsTo(x, 'owner@').length,
    'free-email': emailsTo(x, 'freealert-').length,
    'free-instant': pushesTo(x, /^b|^fin/),
    checkin: pushesTo(x, /^c/),
  });
  // (The free alert email also has its own 5 a scan, so it needs one scan
  // more than the call budget does.)
  while (scans < 20 && last.budget && (Object.keys(last.budget.cuts).length || got.freeEmail.size < 10)) {
    last = await commit(env, arrivals(['car-1']), { saleEvents: SALE });
    scans++;
    worstExt = Math.max(worstExt, last.ext); worstSvc = Math.max(worstSvc, last.svc);
    absorb(last);
    // Strict order: once a step is carried for lack of outside calls, no later step sends.
    if (last.budget.extClosed) {
      const firstCut = STEPS.findIndex((s) => last.budget.cuts[s] && (last.budget.cuts[s].carried || last.budget.cuts[s].unchecked));
      const by = sentBy(last);
      for (const s of STEPS.slice(firstCut + 1)) if (by[s]) { orderOk = false; origLog(`  scan ${scans}: ${s} sent ${by[s]} after ${STEPS[firstCut]} was carried`); }
    }
  }
  check('carry-over: every scan stayed inside both limits', worstExt <= PLATFORM_EXT && worstSvc <= PLATFORM_SVC, `ext ${worstExt}, svc ${worstSvc}`);
  check('carry-over: in every scan, no step sent after a higher one was carried', orderOk);
  check('carry-over: the backlog cleared', Object.keys(last.budget.cuts).length === 0, `${scans} scans, still ${JSON.stringify(last.budget.cuts)}`);
  origLog(`  (backlog of the worst case cleared in ${scans} scans)`);
  // Each Pro web user: one arrivals alert and, for the 30 with a browser, one sale push.
  const webCounts = [...got.web.values()];
  check('carry-over: all 60 Pro web users were reached', got.web.size === 60, String(got.web.size));
  check('carry-over: all 30 Pro email members got exactly one email', got.proEmail.size === 30 && [...got.proEmail.values()].every((v) => v === 1));
  check('carry-over: all 10 free alert addresses got exactly one email', got.freeEmail.size === 10 && [...got.freeEmail.values()].every((v) => v === 1));
  check('carry-over: the owner digest went once', got.owner === 1, String(got.owner));
  check('carry-over: nobody was alerted twice about the car',
    count(env, 'SELECT COUNT(*) FROM alerts_sent') === 60 && count(env, 'SELECT COUNT(*) FROM device_alerts_sent') === 90
    && webCounts.every((v) => v <= 2),
    `alerts_sent ${count(env, 'SELECT COUNT(*) FROM alerts_sent')}, device_alerts_sent ${count(env, 'SELECT COUNT(*) FROM device_alerts_sent')}`);
  // 40 Pro devices: arrivals + sale push = 2 each. 30 free instant: 1 each. 20 check-ins: 1 each.
  const devN = (re) => [...got.dev].filter(([t]) => re.test(t)).map(([, v]) => v);
  check('carry-over: every Pro device got its arrivals push and its sale push, once each', devN(/^a|^pro/).length === 40 && devN(/^a|^pro/).every((v) => v === 2), JSON.stringify(devN(/^a|^pro/)));
  check('carry-over: every free instant device got exactly one push', devN(/^b|^fin/).length === 30 && devN(/^b|^fin/).every((v) => v === 1));
  check('carry-over: every due check-in went exactly once', devN(/^c/).length === 20 && devN(/^c/).every((v) => v === 1));
  await ops.flushOps(env);
}

/* ====================================================================
 * 2. A busy but possible scan: Pro fits, free gives way from the bottom.
 * ==================================================================== */
{
  const env = freshEnv();
  seed(env, { web: 6, webEmail: 4, proDev: 10, proEmail: 5, freeInstant: 30, checkin: 6, freeEmail: 10, coverage: 1 });
  const r = await commit(env, arrivals(['car-2'], 500));
  // Pro: 10 web + 10 devices (+1 FCM token request if none is cached) + 5 emails; then the owner digest.
  origLog(`  (busy scan: ${r.ext} outside calls, ${r.svc} D1+KV calls)`);
  const proExt = r.webpush.length + emailsTo(r, 'web-').length + pushesTo(r, /^a|^pro/) + emailsTo(r, 'proemail-').length;
  check('busy scan: every Pro alert went out', r.webpush.length === 6 && emailsTo(r, 'web-').length === 4 && pushesTo(r, /^a|^pro/) === 10 && emailsTo(r, 'proemail-').length === 5,
    `${r.webpush.length} web push, ${emailsTo(r, 'web-').length} fallback emails, ${pushesTo(r, /^a|^pro/)} devices, ${emailsTo(r, 'proemail-').length} Pro emails`);
  check('busy scan: the owner digest went out before any free send', emailsTo(r, 'owner@').length === 1);
  const freeInstant = pushesTo(r, /^b|^fin/);
  check('busy scan: free instant pushes took exactly what Pro left', freeInstant === 45 - proExt - 1 - r.fcmToken && freeInstant > 0 && freeInstant < 30, `${freeInstant} of 30, Pro used ${proExt}`);
  check('busy scan: check-ins and free alert emails, lower still, sent nothing', pushesTo(r, /^c/) === 0 && emailsTo(r, 'freealert-').length === 0);
  check('busy scan: still inside the limits', r.ext <= PLATFORM_EXT && r.ext === 45 && r.svc <= PLATFORM_SVC, `ext ${r.ext}, svc ${r.svc}`);
  const held = heldRows(env);
  check('busy scan: nothing Pro was carried', !Object.keys(held).some((k) => /pro-|saved|sales/.test(k)), JSON.stringify(held));
  check('busy scan: the free tier is what was carried, and it is counted', held['commit:free-instant'] === 30 - freeInstant && held['commit:free-email'] === 10 && held['commit:checkin'] === 1, JSON.stringify(held));
  {
    const mon = await load('ops_monitor.js');
    const cb = mon.commitBudgetReport(await mon.sendStats(env));
    const line = mon.commitBudgetLines(cb).find((l) => /^CARRIED/.test(l)) || '';
    check('ops email: a free-only carry says so and is not an open issue', cb.pro === 0 && /free alert emails 10; not looked at: first-watch check-ins \d+ \(free tier only; Pro went out in full\)$/.test(line), line);
  }
  // The free emailed alert keeps its own promise: held rows are flagged for the 48 h catch-up.
  check('busy scan: carried free alerts are flagged for their catch-up', count(env, 'SELECT COUNT(*) FROM free_email_alerts WHERE held_at IS NOT NULL') === 10);
  // The next scan: Pro has nothing new, so the free tier is served.
  const r2 = await commit(env, arrivals(['car-2'], 500));
  check('next scan: no Pro alert is repeated', r2.webpush.length === 0 && pushesTo(r2, /^a|^pro/) === 0 && emailsTo(r2, 'proemail-').length === 0 && emailsTo(r2, 'web-').length === 0);
  check('next scan: the carried free instant devices are pushed', pushesTo(r2, /^b|^fin/) === 30 - freeInstant, String(pushesTo(r2, /^b|^fin/)));
  check('next scan: check-ins go out', pushesTo(r2, /^c/) === 6, String(pushesTo(r2, /^c/)));
  check('next scan: free alert emails go out, at their own 5 a scan', emailsTo(r2, 'freealert-').length === 5, String(emailsTo(r2, 'freealert-').length));
  check('next scan: the longest-waiting free devices went first (no device pushed twice)', count(env, "SELECT COUNT(*) FROM device_alerts_sent WHERE device_id LIKE 'b%'") === 30);
  await ops.flushOps(env);
}

/* ====================================================================
 * 3. A quiet scan costs almost nothing and reports nothing.
 * ==================================================================== */
{
  const env = freshEnv();
  seed(env, { web: 2, proDev: 2, proEmail: 1, freeInstant: 1, freeEmail: 1 });
  const r = await commit(env, arrivals([], 300));   // nothing matches anyone
  origLog(`  (quiet scan: ${r.ext} outside calls, ${r.svc} D1+KV calls)`);
  check('quiet scan: no outside call at all', r.ext === 0, String(r.ext));
  check('quiet scan: a few dozen D1 calls', r.svc > 0 && r.svc < 40, String(r.svc));
  check('quiet scan: nothing carried, nothing counted as carried', Object.keys(r.budget.cuts).length === 0 && Object.keys(heldRows(env)).length === 0);
  {
    const mon = await load('ops_monitor.js');
    const lines = mon.commitBudgetLines(mon.commitBudgetReport(await mon.sendStats(env)));
    check('quiet scan: the ops email has the one usage line and no carried line', lines.length === 1 && /^Busiest scan since yesterday \(UTC\): 0 of 45 outside calls/.test(lines[0]), JSON.stringify(lines));
  }
}

/* ====================================================================
 * 4. The budget itself, and the backstop at the network.
 * ==================================================================== */
{
  const { CommitBudget, BudgetExhausted, withBudget, meteredFetch, hasRoom, ownCap, budgetFor } = await load('commit_budget.js');
  let t = 0;
  const b = new CommitBudget({ ext: 2, svc: 3, ms: 1000, now: () => t });
  check('fits: room for what is asked', b.fits({ ext: 2, svc: 3 }) && !b.fits({ svc: 4 }));
  b.spend('ext');
  check('fits: an ask that does not fit closes outside calls for the rest of the commit', !b.fits({ ext: 2 }) && b.extClosed && !b.fits({ ext: 1 }));
  check('fits: D1-only work is still allowed after that', b.fits({ svc: 1 }));
  {
    // A send refused for lack of D1 room is carried too: no cheaper send
    // (one that needs less D1) may go out after it.
    const s = new CommitBudget({ ext: 10, svc: 5, ms: 1000, now: () => 0 });
    s.spend('svc', 4);
    const refused = !s.fits({ ext: 1, svc: 3 });
    check('fits: a send refused for D1 room closes outside calls too', refused && s.extClosed && !s.fits({ ext: 1, svc: 1 }) && s.fits({ svc: 1 }));
  }
  b.spend('ext');
  let threw = null;
  try { b.spend('ext'); } catch (e) { threw = e; }
  check('spend: refuses at the ceiling, before the call', threw instanceof BudgetExhausted && b.used.ext === 2);
  t = 1000;
  check('deadline: nothing new starts after it', !b.fits({ svc: 1 }) && b.timeUp());
  b.spend('svc');
  check('deadline: bookkeeping for a send already made is still written', b.used.svc === 1);

  // No budget on env: nothing changes for admin routes and the cron.
  check('no budget: always room, private caps stand', hasRoom({}, { ext: 999 }) && ownCap({}, 25) === 25);
  const env = freshEnv();
  const tight = new CommitBudget({ ext: 0 });
  const benv = withBudget(env, tight);
  check('in a commit: private Pro caps are lifted (the budget is the limit)', ownCap(benv, 25) === Infinity);
  resetCounts();
  const { sendApns } = await load('apns.js');
  const { sendFcm } = await load('fcm.js');
  const { sendWebPush } = await load('push.js');
  const a = await sendApns(benv, apnsTok('z', 1), { title: 't', body: 'b' });
  const f = await sendFcm(benv, fcmTok('z', 1), { title: 't', body: 'b' });
  const w = await sendWebPush(benv, { endpoint: 'https://push.test/z', ...SUB }, { title: 't' });
  check('backstop: with no outside calls left, a push helper sends nothing and says so', a.deferred && f.deferred && w.deferred && !a.ok && !f.ok && !w.ok && seen.ext === 0, JSON.stringify([a, f, w, seen.ext]));
  let mf = null;
  try { await meteredFetch(benv, 'https://api.resend.com/emails', { method: 'POST', body: '{"to":["x@example.com"]}' }); } catch (e) { mf = e; }
  check('backstop: an email is refused the same way, and no call is made', mf instanceof BudgetExhausted && seen.ext === 0);
  await ops.flushOps(env);
  check('backstop: a refused send is not counted as a failure', count(env, "SELECT COUNT(*) FROM ops_counters WHERE metric LIKE '%:fail%'") === 0 && count(env, 'SELECT COUNT(*) FROM ops_errors') === 0);
  // The metered D1: one count per call, a batch is one call, and it refuses at the ceiling.
  const small = new CommitBudget({ svc: 2 });
  const denv = withBudget(env, small);
  await denv.DB.prepare('SELECT 1 AS x').first();
  await denv.DB.batch([denv.DB.prepare('SELECT 1 AS x'), denv.DB.prepare('SELECT 2 AS x').bind()]);
  let dthrew = null;
  try { await denv.DB.prepare('SELECT 1 AS x').all(); } catch (e) { dthrew = e; }
  check('metered D1: a batch is one call; the third call is refused', small.used.svc === 2 && dthrew instanceof BudgetExhausted);
  check('test override: only in DEV_MODE, only downwards', budgetFor({ COMMIT_EXT_CEILING_TEST: '5' }).cap.ext === 45
    && budgetFor({ DEV_MODE: '1', COMMIT_EXT_CEILING_TEST: '5' }).cap.ext === 5 && budgetFor({ DEV_MODE: '1', COMMIT_EXT_CEILING_TEST: '500' }).cap.ext === 45);
}

/* ---- the deadline, end to end: a commit that is out of time starts nothing and still counts it ---- */
{
  const { CommitBudget, withBudget } = await load('commit_budget.js');
  const { runCommitDispatch } = await load('admin.js');
  const env = freshEnv();
  seed(env, { web: 3, proDev: 3, proEmail: 2, freeInstant: 2, freeEmail: 2, coverage: 1 });
  const late = new CommitBudget({ ms: 0 });
  resetCounts();
  await runCommitDispatch(env, withBudget(env, late), late, { newArrivals: arrivals(['car-9'], 50), saleEvents: SALE });
  const held = heldRows(env);
  check('out of time: no outside call, no step started', seen.ext === 0 && count(env, 'SELECT COUNT(*) FROM arrivals') === 0 && count(env, 'SELECT COUNT(*) FROM alerts_sent') === 0, String(seen.ext));
  check('out of time: every step is counted as not looked at, and the count is written', ops.COMMIT_STEPS.every(([k]) => held['commit-unchecked:' + k] === 1) && seen.svc === 1, JSON.stringify(held) + ' svc ' + seen.svc);
  const r = await commit(env, arrivals(['car-9'], 50), { saleEvents: SALE });
  check('out of time: the next scan does all of it', r.webpush.length >= 3 && pushesTo(r, /^a|^pro/) >= 3 && emailsTo(r, 'proemail-').length === 2 && emailsTo(r, 'freealert-').length === 2 && Object.keys(r.budget.cuts).length === 0,
    JSON.stringify([r.webpush.length, pushesTo(r, /^a|^pro/), r.email.length, r.budget.cuts]));
}

/* ====================================================================
 * 5. Every outside call in the commit path goes through the meter.
 * ==================================================================== */
{
  const dir = new URL(SRC);
  const COMMIT_PATH = ['admin.js', 'alerts.js', 'devices.js', 'email_alerts.js', 'free_email_alert.js', 'saved_alerts.js', 'coverage.js',
    'push.js', 'apns.js', 'fcm.js', 'ops.js', 'inv_resolve.js', 'inventory.js', 'recap_signup.js', 'util.js'];
  const bare = [];
  for (const f of COMMIT_PATH) {
    const text = readFileSync(new URL(f, dir), 'utf8');
    text.split('\n').forEach((line, i) => { if (/(^|[^A-Za-z.])fetch\(/.test(line.replace(/\/\/.*$/, '')) && !/^\s*\*/.test(line) && !/^\s*\/\*/.test(line)) bare.push(`${f}:${i + 1}`); });
  }
  check('no bare fetch() in any file the commit path runs', bare.length === 0, bare.join(', '));
}

origLog(failures ? `\n${failures} FAILURE(S)` : '\nALL PASS');
process.exit(failures ? 1 : 0);
