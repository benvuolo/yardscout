#!/usr/bin/env node
/* Local stand-in for Resend (POST /emails) and for the public site data
 * files the daily ops email reads (GET /data/yard_health.json,
 * /data/inventory_meta.json). The Worker only talks to it when DEV_MODE=1 and
 * RESEND_API_URL_TEST / OPS_DATA_BASE_TEST are set (see src/ops.js and
 * src/ops_monitor.js) — same guard style as mock-fcm.mjs.
 *
 *   POST /emails   → records the email; answers with the current mode
 *                    (default 200 {id}); requires "Bearer re_…" auth
 *   POST /mode     {status, message}  — force the next answers (e.g. 403)
 *   GET  /sent     → accepted emails [{from, to, subject, text}]
 *   GET  /rejected → emails answered with a non-2xx status
 *   GET  /ping
 *
 * Usage: node mock-resend.mjs <port>
 */
import { createServer } from 'node:http';

const port = Number(process.argv[2] || 8798);
const sent = [];
const rejected = [];
let mode = { status: 200, message: '' };

const now = Date.now();
const iso = (ms) => new Date(ms).toISOString().replace(/\.\d+Z$/, 'Z');
const day = (ms) => new Date(ms).toISOString().slice(0, 10);
const D = 86400_000;
// Fixture: one healthy yard, one dormant (newest car 200 d old), one frozen
// (unchanged for 5 d), one both.
const YARD_HEALTH = {
  schemaVersion: 1, scrapedAt: iso(now), staleAfterScans: 6,
  yards: {
    'Healthy Yard - Ogden': { count: 900, lastChangedAt: iso(now - 3600_000), newestDateAdded: day(now - D), unchangedScans: 0 },
    'Dormant Yard - Orem': { count: 80, lastChangedAt: iso(now - 3600_000), newestDateAdded: day(now - 200 * D), unchangedScans: 0 },
    'Frozen Yard - Provo': { count: 500, lastChangedAt: iso(now - 5 * D), newestDateAdded: day(now - 6 * D), unchangedScans: 30 },
    'Ghost Yard - Lehi': { count: 60, lastChangedAt: iso(now - 9 * D), newestDateAdded: day(now - 300 * D), unchangedScans: 54 },
    'Lull Yard - Sandy': { count: 700, lastChangedAt: iso(now - 2.5 * D), newestDateAdded: day(now - 3 * D), unchangedScans: 15 },   // 2.5 d: an ordinary lull, NOT frozen
    'Carried Yard - Bartow': { count: 900, lastChangedAt: iso(now - 6 * D), newestDateAdded: day(now - 7 * D), unchangedScans: 36, carried: true },
    'Renamed Yard - Old Name': { count: 400, lastChangedAt: iso(now - 6 * D), unchangedScans: 10, missingScans: 8 },
  },
};
const INVENTORY_META = { scrapedAt: iso(now), vehicles: 1541 };

const json = (res, status, obj) => {
  res.writeHead(status, { 'content-type': 'application/json' });
  res.end(JSON.stringify(obj));
};
const readBody = (req) => new Promise((resolve) => {
  let b = '';
  req.on('data', (c) => { b += c; });
  req.on('end', () => resolve(b));
});

createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  if (req.method === 'GET' && url.pathname === '/ping') return json(res, 200, { ok: true });
  if (req.method === 'GET' && url.pathname === '/sent') return json(res, 200, sent);
  if (req.method === 'GET' && url.pathname === '/rejected') return json(res, 200, rejected);
  if (req.method === 'GET' && url.pathname === '/data/yard_health.json') return json(res, 200, YARD_HEALTH);
  if (req.method === 'GET' && url.pathname === '/data/inventory_meta.json') return json(res, 200, INVENTORY_META);
  if (req.method === 'POST' && url.pathname === '/mode') {
    try { mode = { status: 200, message: '', ...JSON.parse(await readBody(req)) }; } catch { /* keep */ }
    return json(res, 200, mode);
  }
  if (req.method === 'POST' && url.pathname === '/emails') {
    let msg = {};
    try { msg = JSON.parse(await readBody(req)); } catch { msg = {}; }
    if (!/^Bearer re_/.test(req.headers.authorization || '')) {
      return json(res, 401, { statusCode: 401, name: 'missing_api_key', message: 'Missing API key' });
    }
    const rec = { from: msg.from, to: msg.to, subject: msg.subject, text: msg.text };
    if (mode.status >= 300) {
      rejected.push({ ...rec, status: mode.status });
      return json(res, mode.status, { statusCode: mode.status, name: 'validation_error', message: mode.message || 'rejected' });
    }
    sent.push(rec);
    return json(res, 200, { id: `mock-${sent.length}` });
  }
  json(res, 404, { error: 'not found' });
}).listen(port, '127.0.0.1', () => console.log('mock-resend listening on', port));
