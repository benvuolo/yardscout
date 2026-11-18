/* Unit test: the app's yard list freshness helpers (docs/app.js, "YARD LIST
 * FRESHNESS"): the yard rows' listChangedAt / listState / listReadAt /
 * listFlushAt columns, read by name; the plain sentence; which cars stop
 * counting as new arrivals; the yard_health fallback for older data. Also
 * parses the whole app (syntax). No browser, no server.
 * Run: node backend/test/yard_list_unit.mjs */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const src = fs.readFileSync(path.join(ROOT, 'docs/app.js'), 'utf8');
let failures = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + detail}`); if (!ok) failures++; };

try { new vm.Script(src, { filename: 'docs/app.js' }); check('docs/app.js parses', true); }
catch (e) { check('docs/app.js parses', false, e.message); }

const a = src.indexOf('/* ===== YARD LIST FRESHNESS');
const b = src.indexOf('/* ===== MODEL LIFESPANS');
check('freshness block found', a > 0 && b > a);
const block = src.slice(a, b);
let frozenFallback = null;
const ctx = {
  isNew: (d) => { const t = Date.parse(String(d) + 'T00:00:00'); return Number.isFinite(t) && (Date.now() - t) / 86400000 <= 7; },
  yardFrozenSince: () => frozenFallback,
  escapeHtml: (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'),
};
vm.createContext(ctx);
vm.runInContext(block + '\nthis.api = { setYardLists, yardListStale, arrivalHeld, isNewArrival, yardListSentence, yardListNoteHtml, yardListChipHtml, get lists() { return yardLists; } };', ctx);
const A = ctx.api;

const day = (n) => new Date(Date.now() - n * 86400000).toISOString().slice(0, 10);
const iso = (n) => new Date(Date.now() - n * 86400000).toISOString().replace(/\.\d+Z$/, 'Z');
const YF = ['location', 'city', 'state', 'lat', 'lng', 'avgLifespanDays', 'lifespanBasis', 'listChangedAt', 'listState', 'listReadAt', 'listFlushAt'];
const yards = [
  ['Live Yard', 'A', 'TX', 1, 2, 60, 'yard', iso(0), '', null, null],
  ['Stale Yard', 'B', 'TX', 1, 2, 60, 'yard', '2026-11-06T11:46:31Z', 'stale', null, null],
  ['Frozen Yard', 'C', 'TX', 1, 2, null, null, '2026-10-22T02:14:15Z', 'frozen', '2026-11-17T23:47:19Z', null],
  ['Flush Yard', 'D', 'TX', 1, 2, 60, 'yard', iso(1), '', null, iso(1)],
];

// Old data (no columns): fallback to yard_health's rule.
A.setYardLists(yards.map((y) => y.slice(0, 7)), YF.slice(0, 7));
check('no list columns -> yardLists null (old data files)', A.lists === null);
frozenFallback = new Date('2026-11-10T12:00:00Z');
const fb = A.yardListStale('Any Yard');
check('fallback: yard_health rule shows as stale', fb && fb.state === 'stale' && fb.changed.getTime() === frozenFallback.getTime());
check('fallback: nothing is held back without the columns', !A.arrivalHeld({ location: 'Any Yard', dateAdded: day(1) }));
frozenFallback = null;

A.setYardLists(yards, YF);
check('columns read by name', A.lists['Stale Yard'].state === 'stale' && A.lists['Frozen Yard'].readAt === '2026-11-17T23:47:19Z');
check('a fresh yard is not stale', A.yardListStale('Live Yard') === null);
check('a yard missing from the table is not stale (no fallback once columns exist)', A.yardListStale('Nowhere') === null);
const st = A.yardListStale('Stale Yard');
check('stale yard: state + change date', st && st.state === 'stale' && st.changed.toISOString() === '2026-11-06T11:46:31.000Z' && st.read === null);
const sent = A.yardListSentence(st);
check('the sentence is plain and kind', /^This yard’s list has not changed since [A-Z][a-z]{2} \d{1,2}(, \d{4})?\. Call before you go\.$/.test(sent), sent);
const fr = A.yardListStale('Frozen Yard');
check('frozen + not read this scan: both dates in the sentence',
  fr && fr.state === 'frozen' && /has not changed since .+, and we have not been able to read it since .+\. Call before you go\.$/.test(A.yardListSentence(fr)), A.yardListSentence(fr));
check('frozen note says its cars are left out of Newest arrivals and alerts',
  /left out of Newest arrivals and alerts/.test(A.yardListNoteHtml('Frozen Yard')));
check('stale note does not', !/left out/.test(A.yardListNoteHtml('Stale Yard')) && /class="long-listed list-note"/.test(A.yardListNoteHtml('Stale Yard')));
check('notes reuse the quiet notice style, chips the quiet badge (no alarm colours)',
  /long-listed/.test(A.yardListNoteHtml('Stale Yard', 'x')) && /badge badge-long/.test(A.yardListChipHtml('Stale Yard')) && !/red|orange|alarm/.test(A.yardListNoteHtml('Stale Yard') + A.yardListChipHtml('Stale Yard')));
check('chip text: "List unchanged since <date>"', /List unchanged since [A-Z][a-z]{2} \d{1,2}/.test(A.yardListChipHtml('Stale Yard')));
check('no chip or note for a fresh yard', A.yardListChipHtml('Live Yard') === '' && A.yardListNoteHtml('Live Yard') === '');

check('new arrival at a live yard', A.isNewArrival({ location: 'Live Yard', dateAdded: day(1) }));
check('a frozen yard’s cars are never new arrivals', !A.isNewArrival({ location: 'Frozen Yard', dateAdded: day(1) }) && A.arrivalHeld({ location: 'Frozen Yard', dateAdded: day(30) }));
check('a stale (not frozen) yard’s new car still counts', A.isNewArrival({ location: 'Stale Yard', dateAdded: day(2) }));
check('cars that came in with a flush are not new', !A.isNewArrival({ location: 'Flush Yard', dateAdded: day(1) }) && !A.isNewArrival({ location: 'Flush Yard', dateAdded: day(3) }));
check('a car the flushed yard lists after the flush day is new', A.isNewArrival({ location: 'Flush Yard', dateAdded: day(0) }));
check('old cars are not new anywhere', !A.isNewArrival({ location: 'Live Yard', dateAdded: day(20) }));
check('a car with no date is not held (and not new)', !A.arrivalHeld({ location: 'Flush Yard', dateAdded: '' }) && !A.isNewArrival({ location: 'Flush Yard', dateAdded: '' }));
check('a malformed row is skipped', (() => { A.setYardLists([null, ['X', 'a', 'b', 1, 2, null, null, iso(0), 'stale', null, null], []], YF); return A.lists.X && Object.keys(A.lists).length === 1; })());

console.log(failures ? `\n${failures} FAILED` : '\nALL PASS');
process.exit(failures ? 1 : 0);
