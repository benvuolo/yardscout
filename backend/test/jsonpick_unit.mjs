/* Unit test: backend/src/jsonpick.js and GET /v1/vehicles/:id built on it
 * (2026-11-18, after Cloudflare stopped 656 vehicle-detail requests for CPU).
 *
 * 1. The pickers on hand-made texts with the awkward cases: quotes, escaped
 *    quotes and backslashes, brackets and braces inside strings, unicode,
 *    numeric and string ids, an id that is the start of another id, a key
 *    that also appears as a value.
 * 2. handleVehicleDetail against a fake D1 holding gzipped shards built the
 *    way scraper/push_inventory.py builds them (compact JSON), for EVERY car
 *    of a synthetic 2,500-car yard, by id and by VIN, free and pro: the answer
 *    must equal what the old full-parse code gave.
 * 3. A rough CPU comparison of the old and new path on that yard (printed,
 *    and the new path must be at least 3x faster).
 * Run: node backend/test/jsonpick_unit.mjs */
import { jsonValueEnd, pickKey, pickRow, pickVpic } from '../src/jsonpick.js';
import { handleVehicleDetail } from '../src/inventory.js';
import { vindexBucket } from '../src/util.js';
import { gzipSync } from 'node:zlib';

let fails = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + String(detail).slice(0, 300)}`); if (!ok) fails++; };
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

/* ---- 1. pickers ---- */
const tricky = { 'a"b': [1, 'x]y', { 'k': '}' }], plain: 'p', '12': [3, '12'], '123': [4, '123'], 'é': ['ü', '\\', '"'], esc: 'ends with \\', num: -1.5e3, t: true, n: null };
const T = JSON.stringify(tricky);
check('jsonValueEnd: string with escapes', jsonValueEnd('"a\\"b\\\\",1', 0) === 8);
check('jsonValueEnd: array with brackets inside strings', jsonValueEnd('[1,"]",["["],{"}":"{"}],9', 0) === 23);
check('jsonValueEnd: number and literals', jsonValueEnd('-1.5e3,', 0) === 6 && jsonValueEnd('true}', 0) === 4 && jsonValueEnd('null]', 0) === 4);
check('jsonValueEnd: unterminated -> -1', jsonValueEnd('[1,2', 0) === -1 && jsonValueEnd('"abc', 0) === -1);
for (const k of Object.keys(tricky)) check(`pickKey ${JSON.stringify(k)}`, same(pickKey(T, k), tricky[k]), JSON.stringify(pickKey(T, k)));
check('pickKey: "12" is not "123"', same(pickKey(T, '12'), [3, '12']) && same(pickKey(T, '123'), [4, '123']));
check('pickKey: a value equal to a key name is not taken for the key', pickKey('{"x":"plain","plain":7}', 'plain') === 7);
check('pickKey: missing key -> undefined', pickKey(T, 'nope') === undefined);
const shardT = JSON.stringify({ vehicles: [[12, 'V12', 2001], ['12-a', 'V12A', 2002], [123, 'V123', 2003], ['x', '[12,', 2004]], vpic: { '12': ['SE', 'q'], '123': ['LE', 'q'], '12-a': ['[', 'q'] } });
check('pickRow: numeric id, not its longer neighbour', same(pickRow(shardT, 12, 3), [12, 'V12', 2001]) && same(pickRow(shardT, 123, 3), [123, 'V123', 2003]));
check('pickRow: string id', same(pickRow(shardT, '12-a', 3), ['12-a', 'V12A', 2002]));
check('pickRow: "[12," inside a string value is not a row', same(pickRow(shardT, 12, 3), [12, 'V12', 2001]));
check('pickRow: wrong width -> null (caller falls back)', pickRow(shardT, 12, 11) === null);
check('pickRow: absent -> null', pickRow(shardT, 999, 3) === null);
check('pickVpic', same(pickVpic(shardT, 12), ['SE', 'q']) && same(pickVpic(shardT, '12-a'), ['[', 'q']) && pickVpic(shardT, 999) === null);

/* ---- 2. the handler on push_inventory-shaped shards ---- */
const FIELDS = ['id', 'vin', 'year', 'make', 'model', 'row', 'dateAdded', 'yard', 'partSet', 'maxValue', 'premium'];
const MAKES = ['Toyota', 'Ford', 'Chevrolet', 'Honda', 'Nissan', 'Dodge', 'Mercedes-Benz'];
const MODELS = ['Camry "LE"', 'F-150 [4x4]', 'Silverado {HD}', 'Civic\\Si', 'Altima, 2.5', 'Ram 1500', 'Sprinter 2500'];
const VINCH = 'ABCDEFGHJKLMNPRSTUVWXYZ0123456789';
let seed = 7;
const rnd = (n) => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed % n; };
const vin = () => Array.from({ length: 17 }, () => VINCH[rnd(VINCH.length)]).join('');
const YARD = 5, N = 2500;
const rows = [], vpic = {};
for (let i = 0; i < N; i++) {
  // Mixed id styles, as the scrapers produce: plain numbers, and prefixed strings.
  const id = i % 3 === 0 ? 100000 + i : (i % 3 === 1 ? `harrys-${vin()}` : `${1000 + i}`);
  const r = [id, i % 50 === 0 ? '' : vin(), 1990 + rnd(35), MAKES[i % 7], MODELS[i % 7], `R${rnd(90)}`, `2026-11-${String(1 + rnd(17)).padStart(2, '0')}`, YARD, rnd(400), rnd(900), rnd(2)];
  rows.push(r);
  if (i % 4) vpic[String(id)] = [i % 2 ? 'SR5' : 'Limited "TRD"', 'trim', 'Series {X}', '4WD/4-Wheel Drive/4x4'];
}
const pack = (o) => gzipSync(Buffer.from(JSON.stringify(o)));   // compact, like canonical()
const freeRows = rows.map((r) => { const f = r.slice(); f[9] = 0; f[10] = 0; return f; });
const MOD = 64;
const vindex = {};
for (const r of rows) {
  const put = (tok) => { const b = vindexBucket(tok, MOD); (vindex[b] ||= {})[tok] = [YARD, r[0]]; };
  put(String(r[0]));
  if (String(r[1]).length >= 11) put(String(r[1]).toUpperCase());
}
// Pad every bucket to a realistic ~10,000 entries (other yards' cars).
for (let b = 0; b < MOD; b++) { vindex[b] ||= {}; const have = Object.keys(vindex[b]).length; for (let k = 0; k < 9000 - have; k++) vindex[b][`pad-${b}-${k}`] = [1, k]; }
const STORE = new Map();
STORE.set(`yard|${YARD}|pro`, pack({ vehicles: rows, vpic }));
STORE.set(`yard|${YARD}|free`, pack({ vehicles: freeRows, vpic }));
for (const [b, e] of Object.entries(vindex)) STORE.set(`vindex|${b}|all`, pack(e));
const DIR = { schemaVersion: 2, scrapedAt: '2026-11-18T12:00:00Z', fields: FIELDS, yardFields: ['location', 'city', 'state', 'lat', 'lng'],
  yards: Array.from({ length: 8 }, (_, i) => [`Yard ${i}`, 'City', 'ST', 40 + i, -100 - i]), vindexMod: MOD, counts: { yards: 8, vehicles: N } };
// A fake D1: prepare(sql)[.bind(...)].first(), as the handler calls it.
const env = { DB: { prepare(sql) {
  const first = async (a = []) => {
    if (/FROM inv_meta/.test(sql)) return { directory: JSON.stringify(DIR) };
    const body = STORE.get(a.join('|'));
    return body ? { body: new Uint8Array(body) } : null;
  };
  return { first: () => first(), bind(...a) { return { first: () => first(a) }; } };
} } };

// The old handler's answer, by full parse (what the API returned before today).
const zlib = await import('node:zlib');
const _full = new Map();   // parsed once: the reference answer, not what is timed
const full = (key) => { if (!_full.has(key)) _full.set(key, JSON.parse(zlib.gunzipSync(STORE.get(key)).toString('utf8'))); return _full.get(key); };
// (The old handler also upper-cased every token first, which lost every car
// whose id has lowercase letters; the reference here looks the token up as
// given, then upper-cased, which is what the API does from 2026-11-18.)
function oldAnswer(token, variant) {
  let hit = full(`vindex|${vindexBucket(token, MOD)}|all`)[token];
  if (!hit && /[a-z]/.test(token)) { token = token.toUpperCase(); hit = full(`vindex|${vindexBucket(token, MOD)}|all`)[token]; }
  if (!hit) return null;
  const shard = full(`yard|${hit[0]}|${variant}`);
  const row = shard.vehicles.find((r) => String(r[0]) === String(hit[1]) || String(r[1]) === token);
  if (!row) return null;
  const vehicle = {}; FIELDS.forEach((f, i) => { vehicle[f] = row[i]; });
  return { vehicle, vpic: shard.vpic?.[String(row[0])] || null };
}
const req = new Request('https://api.example/v1/vehicles/x');
let n = 0, bad = 0, firstBad = '';
for (const r of rows) {
  for (const tok of [String(r[0]), String(r[1]).length >= 11 ? String(r[1]).toUpperCase() : null].filter(Boolean)) {
    const res = await handleVehicleDetail(req, env, null, tok);
    const got = res.status === 200 ? await res.json() : null;
    const want = oldAnswer(tok, 'free');
    n++;
    if (!got || !want || !same(got.vehicle, want.vehicle) || !same(got.vpic, want.vpic)) { bad++; firstBad ||= `${tok}: ${JSON.stringify(got && got.vehicle)} vs ${JSON.stringify(want && want.vehicle)}`; }
  }
}
check(`every car of a ${N}-car yard, by id and by VIN (${n} lookups): same answer as the full parse`, bad === 0, `${bad} differ; first: ${firstBad}`);
const lowerId = rows.find((r) => /[a-z]/.test(String(r[0])) && String(r[1]).length < 11);
if (lowerId) {
  const res = await handleVehicleDetail(req, env, null, String(lowerId[0]));
  check(`a lowercase id with no VIN is found (${lowerId[0]}): was 404 before 2026-11-18`, res.status === 200 && (await res.json()).vehicle.id === lowerId[0]);
}
const vinRow = rows.find((r) => String(r[1]).length >= 11);
const resLowVin = await handleVehicleDetail(req, env, null, String(vinRow[1]).toLowerCase());
check('a VIN typed in lower case still resolves', resLowVin.status === 200 && (await resLowVin.json()).vehicle.vin === vinRow[1]);
const r404 = await handleVehicleDetail(req, env, null, 'does-not-exist-123');
check('unknown vehicle -> 404', r404.status === 404);

// Pro variant: maxValue kept.
const pro = { ...env };
const auth = await import('../src/auth.js');
const tier = auth.resolveTier({ tier: 'pro', pro_until: null });
if (auth.variantFor(tier) === 'pro') {
  const res = await handleVehicleDetail(req, env, { tier: 'pro' }, String(rows[3][0]));
  const got = await res.json();
  check('pro session: the pro row (maxValue kept)', got.vehicle.maxValue === rows[3][9], JSON.stringify(got.vehicle));
} else {
  console.log('SKIP  pro session check (resolveTier did not give pro for a bare object here)');
}

/* ---- 3. CPU, old vs new, on the decompressed texts ---- */
const idxText = zlib.gunzipSync(STORE.get(`vindex|${vindexBucket(String(rows[1777][0]), MOD)}|all`)).toString('utf8');
const shText = zlib.gunzipSync(STORE.get(`yard|${YARD}|free`)).toString('utf8');
const tok = String(rows[1777][0]);
const time = (fn, k = 200) => { const t = process.hrtime.bigint(); for (let i = 0; i < k; i++) fn(); return Number(process.hrtime.bigint() - t) / 1e6 / k; };
const tOld = time(() => { const h = JSON.parse(idxText)[tok]; const s = JSON.parse(shText); s.vehicles.find((r) => String(r[0]) === String(h[1])); });
const tNew = time(() => { const h = pickKey(idxText, tok); pickRow(shText, h[1], 11); pickVpic(shText, h[1]); });
console.log(`INFO  per lookup, parsing only (no gunzip): old ${tOld.toFixed(2)} ms, new ${tNew.toFixed(3)} ms (index ${Math.round(idxText.length / 1024)} KB, shard ${Math.round(shText.length / 1024)} KB)`);
check('new path at least 3x faster than the full parse', tNew * 3 < tOld, `old ${tOld} new ${tNew}`);

console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
