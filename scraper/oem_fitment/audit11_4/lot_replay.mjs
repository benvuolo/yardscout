// lot_replay.mjs GROUPS.json INVENTORY.json EXTRAS.json OUT.json [APP_JS]
//
// Replays a pinned lot through the web app's OWN OEM donor code: the
// OEM-GATE block (pfOemDonorGate and helpers), the AM-GATE helpers it calls,
// pfAppMatches / pfSquashModel / canonicalMake and expandV2Row (vPIC side
// table), all extracted from docs/app.js and run unchanged in a vm context.
// GROUPS.json: [{id, ns, cat, apps, pn}] in the payload's shape (apps may
// carry the 6th-element gate), e.g. from replay_groups.py. OUT.json:
// {id: {plain: [i...], unc: [i...], exc: [i...]}} where i is the vehicle's
// index in INVENTORY.json's `vehicles` (round3-1119). Read-only; no fetch.
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const [gp, ip, ep, op, appArg] = process.argv.slice(2);
if (!op) { console.error('usage: lot_replay.mjs GROUPS INVENTORY EXTRAS OUT [APP_JS]'); process.exit(2); }
const here = path.dirname(fileURLToPath(import.meta.url));
const appPath = appArg || path.resolve(here, '../../../docs/app.js');
const src = fs.readFileSync(appPath, 'utf8');

function extractFn(name) {
  const lines = src.split('\n');
  const start = lines.findIndex(l => l.startsWith(`function ${name}(`));
  if (start < 0) throw new Error(`app.js: no function ${name}`);
  const end = lines.findIndex((l, i) => i > start && l === '}');
  return lines.slice(start, end + 1).join('\n');
}
function extractBlock(re, what) {
  const m = src.match(re);
  if (!m) throw new Error(`app.js: no ${what}`);
  return m[0];
}
let code = '';
code += extractBlock(/^const MAKE_ALIASES = \{[\s\S]*?\n\};/m, 'MAKE_ALIASES') + '\n';
code += extractBlock(/^const _CAT_MAKES = .*$/m, '_CAT_MAKES') + '\n';
code += extractBlock(/^const _CAT_MODELS = .*$/m, '_CAT_MODELS') + '\n';
code += extractBlock(/^const _CAT_NOISE = .*$/m, '_CAT_NOISE') + '\n';
for (const fn of ['canonicalMake', 'pfSquash', 'pfSquashModel', 'pfAppMatches', 'splitCategoryMake',
  'expandV2Row', 'pfAmParseEngine', 'pfAmCarTrans']) code += extractFn(fn) + '\n';
code += extractBlock(/\/\* AM-GATE BEGIN[\s\S]*?\/\* AM-GATE END \*\//, 'AM-GATE block') + '\n';
code += extractBlock(/\/\* OEM-GATE BEGIN[\s\S]*?\/\* OEM-GATE END \*\//, 'OEM-GATE block') + '\n';

const inv = JSON.parse(fs.readFileSync(ip, 'utf8'));
const extras = JSON.parse(fs.readFileSync(ep, 'utf8'));
const groups = JSON.parse(fs.readFileSync(gp, 'utf8'));
const ctx = vm.createContext({ console, Map, Set, Math, String, Number, JSON, Array, Object, RegExp, parseFloat, parseInt });
vm.runInContext(code + `
var extraIdx = { photo: 0, color: 1, engine: 2, trans: 3, transSrc: 4, body: 5 };
var __ex = null;
function __setExtras(fields, ex) {
  const next = { ...extraIdx }; (fields || []).forEach((n, i) => { next[n] = i; }); extraIdx = next; __ex = ex;
}
function __expand(raw) {
  return raw.vehicles.map((r, i) => expandV2Row(r, raw.yards, raw.partSets, raw.vpic[String(i)]));
}
function __extrasFor(v) { return (__ex && __ex[String(v.id)]) || null; }
`, ctx, { filename: 'app.js-extract' });
ctx.__setExtras(extras.extraFields, extras.extras);
const cars = ctx.__expand(inv);

// index: canonical make (lowercase) -> squashed model candidate -> [vehicle index]
const idx = new Map();
cars.forEach((v, i) => {
  const mk = String(ctx.canonicalMake(v.make)).toLowerCase();
  if (!idx.has(mk)) idx.set(mk, new Map());
  const m = idx.get(mk);
  for (const c of new Set([ctx.pfSquashModel(v.model, ctx.canonicalMake(v.make)), ctx.pfSquashModel(v.model, '')])) {
    if (!m.has(c)) m.set(c, []);
    m.get(c).push(i);
  }
});
function candidates(app) {
  const out = new Set();
  const prefix = app[1].endsWith('*');
  const am = ctx.pfSquash(prefix ? app[1].slice(0, -1) : app[1]);
  for (const mk of app[0].toLowerCase().split('|')) {
    const m = idx.get(mk);
    if (!m) continue;
    for (const [c, is] of m) if (prefix ? c.startsWith(am) : c === am) is.forEach(i => out.add(i));
  }
  return out;
}
const out = {};
for (const g of groups) {
  const res = { plain: [], unc: [], exc: [] };
  const seen = new Set();
  for (const a of g.apps) for (const i of candidates(a)) seen.add(i);
  for (const i of [...seen].sort((a, b) => a - b)) {
    const v = cars[i];
    const dApps = g.apps.filter(a => ctx.pfAppMatches(a, v.year, ctx.canonicalMake(v.make), v.model));
    if (!dApps.length) continue;
    const gate = ctx.pfOemDonorGate(dApps, v, ctx.__extrasFor(v));
    (gate.verdict === 'exclude' ? res.exc : gate.verdict === 'confirm' ? res.plain : res.unc).push(i);
  }
  out[g.id] = res;
}
fs.writeFileSync(op, JSON.stringify(out));
const tot = Object.values(out).reduce((s, r) => [s[0] + r.plain.length, s[1] + r.unc.length, s[2] + r.exc.length], [0, 0, 0]);
console.log(`lot_replay: ${groups.length} groups, ${cars.length} cars; pairs plain ${tot[0]}, if-equipped ${tot[1]}, excluded ${tot[2]}`);
