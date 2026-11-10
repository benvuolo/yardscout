/* Unit test: aftermarket unit notes on Parts donor cards (hub 2026-11-10,
 * owner: no clutter). pfAmSplitNote (docs/app.js) keeps the checks to make
 * at the car inline and moves the listing's provenance behind "Why it fits".
 * Over every aftermarket note in docs/data/oem/*.json, asserts:
 *  - nothing is lost: every word of the note is in inline + more;
 *  - provenance never stays inline ("is listed for each", "lists these
 *    vehicles", "not the carmaker's catalog", "Only the years shown", "No
 *    other unit", "Engines shown are", vendor "fit notes" without a
 *    transmission requirement);
 *  - the checks stay inline: Match the engine / amperage / body style /
 *    drivetrain, spline and length checks, transmission requirements,
 *    "Transmission, trim and suspension ... match them";
 *  - inline is short: at most 240 characters (about 4 lines at 390px).
 * Run: node backend/test/am_notes_unit.mjs */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const here = path.dirname(new URL(import.meta.url).pathname);
const lines = fs.readFileSync(path.join(here, '../../docs/app.js'), 'utf8').split('\n');
const block = (start, end) => {
  const i = lines.findIndex(l => l.startsWith(start));
  const j = lines.findIndex((l, k) => k > i && l === end);
  if (i < 0 || j < 0) throw new Error('missing ' + start);
  return lines.slice(i, j + 1).join('\n');
};
const ctx = vm.createContext({});
vm.runInContext([block('const PF_AM_PROVENANCE = [', '];'), block('function pfAmSplitNote(', '}'), 'globalThis.__s = pfAmSplitNote;'].join('\n'), ctx);
const split = ctx.__s;

let fails = 0, n = 0;
const bad = {};
const fail = (k, d) => { bad[k] = bad[k] || []; if (bad[k].length < 3) bad[k].push(d); };
const words = (t) => (t.match(/[A-Za-z0-9][A-Za-z0-9'./&-]*/g) || []).map(w => w.toLowerCase().replace(/[.;,]+$/, ''));
const MAX = 240;
let longest = 0;
for (const f of fs.readdirSync(path.join(here, '../../docs/data/oem')).filter(x => x.endsWith('.json'))) {
  const d = JSON.parse(fs.readFileSync(path.join(here, '../../docs/data/oem', f), 'utf8'));
  for (const g of d.amGroups || []) {
    const note = String(g.note || ''); if (!note) continue;
    n++;
    const { inline, more } = split(note);
    longest = Math.max(longest, inline.length);
    const have = new Map(); for (const w of words(inline + ' ' + more)) have.set(w, (have.get(w) || 0) + 1);
    for (const w of words(note)) { if (!have.get(w)) { fail('lost text', `${g.id}: "${w}"`); break; } have.set(w, have.get(w) - 1); }
    if (/is listed for each|lists these vehicles|not the carmaker's catalog|Only the years shown|No other unit of the same brand|Engines shown are/i.test(inline)) fail('provenance inline', `${g.id}: ${inline.slice(0, 120)}`);
    const fitInline = /fit notes:/i.test(inline);
    if (fitInline && !/transmission only/i.test(inline)) fail('fit notes inline without a transmission need', `${g.id}`);
    for (const rx of [/Match the [^.;]*/i, /check the donor's axle matches[^.]*/i, /(automatic|manual) transmission only/i, /Transmission, trim and suspension[^;]*/i, /some of these years also came with a different amperage/i]) {
      const m = note.match(rx);
      if (m && !inline.toLowerCase().includes(m[0].toLowerCase().slice(0, 30))) fail('check moved off the card', `${g.id}: "${m[0].slice(0, 60)}"`);
    }
    if (inline.length > MAX) fail(`inline over ${MAX} chars`, `${g.id}: ${inline.length}`);
    if (inline && !/^[A-Z]/.test(inline)) fail('inline starts lowercase', `${g.id}: ${inline.slice(0, 40)}`);
  }
}
const check = (name, ok, d = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + d}`); if (!ok) fails++; };
check(`notes found (${n})`, n > 500, String(n));
for (const k of ['lost text', 'provenance inline', 'fit notes inline without a transmission need', 'check moved off the card', `inline over ${MAX} chars`, 'inline starts lowercase']) {
  check(`all notes: no ${k}`, !bad[k], (bad[k] || []).join(' | '));
}
// worked examples
const gsp = "GSP NCV10028 (front right CV axle) is listed for each of these vehicles in GSP's own application list; aftermarket data, not the carmaker's catalog. Match the engine. Transmission, trim and suspension (sport / electronic) are not stated; match them. Before pulling, check the donor's axle matches: inboard splines 25, outboard splines 33, compressed length 640 mm. No other unit of the same brand is listed for the same front right position on these cars. Engines shown are the title's engines that cars of that model and year on the lots have.";
const r1 = split(gsp);
check('GSP CV axle: inline is the three checks', r1.inline === "Match the engine. Transmission, trim and suspension (sport / electronic) are not stated; match them. Before pulling, check the donor's axle matches: inboard splines 25, outboard splines 33, compressed length 640 mm.", r1.inline);
check('GSP CV axle: provenance behind the fold', /is listed for each/.test(r1.more) && /No other unit/.test(r1.more) && /Engines shown/.test(r1.more), r1.more);
const db = "DB Electrical 400-12345 (130A unit) lists these vehicles; aftermarket application data, not the carmaker's catalog. Match the engine and the amperage on the tag. DB Electrical fit notes: MANUAL TRANSMISSION ONLY.";
const r2 = split(db);
check('DB alternator: a transmission-only fit note stays on the card', /MANUAL TRANSMISSION ONLY/.test(r2.inline), r2.inline);
const db2 = "DB Electrical 410-48123 (unit) lists these vehicles; aftermarket application data, not the carmaker's catalog. Match the engine; automatic transmission only. DB Electrical fit notes: FORD MAZDA 1990-97 AUTOMATIC TRANSMISSION ONLY.";
const r3 = split(db2);
check('DB starter: fit note repeating the transmission goes behind the fold', r3.inline === 'Match the engine; automatic transmission only.' && /FORD MAZDA/.test(r3.more), JSON.stringify(r3));
check(`longest inline note: ${longest} chars`, longest <= MAX);
console.log(fails ? `${fails} FAILURES` : 'ALL PASS');
process.exit(fails ? 1 : 0);
