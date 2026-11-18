/* Unit test: the yard and car pages say plainly when a yard's own list has
 * not changed for a while (src/share.js yardListOf / yardListSentence /
 * yardListHeld), from the yard directory's list columns
 * (scraper/yard_freshness.py). Fetch stubbed; nothing leaves the machine.
 *   - stale yard: the sentence on its yard page and its car pages; no
 *     countdown against the typical stay; the car still "New" by its date
 *   - frozen yard, not read in the last scan: both dates, "left out of new
 *     arrivals and alerts", no "New" badge, 0 new this week
 *   - flushed yard: cars that came in with the flush are not new arrivals;
 *     one the yard listed after it is
 *   - a directory without the columns (before the first scan with them):
 *     pages exactly as before, no sentence
 * Run: node test/yard_list_pages_unit.mjs   (from backend/site-proxy/) */
import worker from '../src/index.js';
import { yardListOf, yardListSentence, yardListHeld } from '../src/share.js';

let failures = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + detail}`); if (!ok) failures++; };

const daysAgo = (n) => new Date(Date.now() - n * 86400000).toISOString().slice(0, 10);
const isoAgo = (n) => new Date(Date.now() - n * 86400000).toISOString().replace(/\.\d+Z$/, 'Z');
const SCAN = isoAgo(0);
const BASE_YF = ['location', 'city', 'state', 'lat', 'lng', 'avgLifespanDays', 'lifespanBasis'];
const YF = [...BASE_YF, 'listChangedAt', 'listState', 'listReadAt', 'listFlushAt'];
const YARDS = [
  ['Stale Yard - Austin', 'Austin', 'TX', 30.2, -97.7, 60, 'yard', '2026-11-06T11:46:31Z', 'stale', null, null],
  ['Frozen Yard - Waco', 'Waco', 'TX', 31.5, -97.1, 60, 'yard', '2026-10-22T02:14:15Z', 'frozen', '2026-11-17T23:47:19Z', null],
  ['Flush Yard - Tyler', 'Tyler', 'TX', 32.3, -95.3, 60, 'yard', isoAgo(1), '', null, isoAgo(1)],
  ['Live Yard - Bryan', 'Bryan', 'TX', 30.6, -96.3, 60, 'yard', SCAN, '', null, null],
];
let directory = { scrapedAt: SCAN, yardFields: YF, yards: YARDS, counts: { yards: 4, vehicles: 6 } };
const car = (id, vin, yard, d) => [id, vin, 2008, 'Honda', 'Civic', '12', d, yard, -1, 0, 0];
const SHARDS = {
  0: [car(1, 'VINSTALE0000001', 0, daysAgo(2))],
  1: [car(2, 'VINFROZEN000002', 1, daysAgo(2)), car(3, 'VINFROZEN000003', 1, daysAgo(40))],
  2: [car(4, 'VINFLUSH0000004', 2, daysAgo(3)), car(5, 'VINFLUSH0000005', 2, daysAgo(0))],
  3: [car(6, 'VINLIVE00000006', 3, daysAgo(1))],
};
globalThis.fetch = async (u) => {
  u = String(u);
  const json = (o, status = 200) => new Response(JSON.stringify(o), { status, headers: { 'content-type': 'application/json' } });
  if (u.endsWith('/v1/yards')) return json(directory);
  const sh = u.match(/\/v1\/inventory\/shard\/(\d+)$/);
  if (sh) return json({ vehicles: SHARDS[sh[1]] || [], vpic: {} });
  const m = u.match(/\/v1\/vehicles\/([^/]+)$/);
  if (m) {
    for (const rows of Object.values(SHARDS)) {
      const row = rows.find((r) => r[1] === m[1]);
      if (row) {
        const [id, vin, year, make, model, rowNo, dateAdded, yi] = row; const y = YARDS[yi];
        return json({ scrapedAt: SCAN, tier: 'free', vehicle: { id, vin, year, make, model, row: rowNo, dateAdded, yard: yi }, vpic: null, yard: { id: yi, location: y[0], city: y[1], state: y[2] } });
      }
    }
    return json({ error: 'not_found' }, 404);
  }
  return new Response('offline', { status: 502 });
};
let n = 0;
const get = async (path) => {
  // A fresh query string per call: the pages keep the directory in memory.
  const r = await worker.fetch(new Request(`https://yardscout.io${path}`, { redirect: 'manual' }), {});
  return { status: r.status, html: await r.text() };
};
const text = (html) => html.replace(/<script[\s\S]*?<\/script>/g, '').replace(/<style[\s\S]*?<\/style>/g, '').replace(/<[^>]+>/g, ' ').replace(/&#39;|&rsquo;/g, '’').replace(/\s+/g, ' ');

/* ---------- helpers ---------- */
check('no columns -> null', yardListOf(BASE_YF, YARDS[0].slice(0, 7)) === null);
const st = yardListOf(YF, YARDS[0]);
check('columns read by name', st && st.state === 'stale' && st.changedAt === '2026-11-06T11:46:31Z');
check('stale sentence', yardListSentence(st) === 'This yard’s list has not changed since Nov 6, 2026. Call before you go.', yardListSentence(st));
check('frozen + not read sentence', yardListSentence(yardListOf(YF, YARDS[1])) === 'This yard’s list has not changed since Oct 22, 2026, and we have not been able to read it since Nov 17, 2026. Call before you go.', yardListSentence(yardListOf(YF, YARDS[1])));
check('fresh yard: no sentence', yardListSentence(yardListOf(YF, YARDS[3])) === '');
check('held: frozen yes, stale no, flush car yes, later car no',
  yardListHeld(yardListOf(YF, YARDS[1]), daysAgo(1)) && !yardListHeld(st, daysAgo(1))
  && yardListHeld(yardListOf(YF, YARDS[2]), daysAgo(3)) && !yardListHeld(yardListOf(YF, YARDS[2]), daysAgo(0)));

/* ---------- yard pages ---------- */
let r = await get('/yard/stale-yard-austin');
check('stale yard page -> 200', r.status === 200, r.status);
check('stale yard page: the sentence, in the quiet notice style',
  /<p class="long-listed list-note" role="note">This yard’s list has not changed since Nov 6, 2026\. Call before you go\.<\/p>/.test(r.html), (r.html.match(/long-listed[^<]*/) || [''])[0]);
check('stale yard page: its car still counts as new this week (a stale list is not held back)', /1 new this week/.test(text(r.html)) || /New this week<\/span><span class="value accent">1</.test(r.html));
r = await get('/yard/frozen-yard-waco');
check('frozen yard page: both dates + left out of new arrivals and alerts',
  /has not changed since Oct 22, 2026, and we have not been able to read it since Nov 17, 2026\. Call before you go\. Until it changes, its cars are left out of new arrivals and alerts\./.test(text(r.html)));
check('frozen yard page: 0 new this week, the recently dated car not listed as an arrival',
  /New this week<\/span><span class="value accent">0</.test(r.html) && !r.html.includes('/car/VINFROZEN000002'), (r.html.match(/New this week<\/span><span class="value accent">[^<]*/) || [''])[0]);
check('frozen yard page: its cars are still on the lot count', /On the lot<\/span><span class="value">2</.test(r.html));
r = await get('/yard/flush-yard-tyler');
check('flushed yard page: no notice (the list changed)', !r.html.includes('list-note'));
check('flushed yard page: the flush car is not a new arrival, the later one is',
  !r.html.includes('/car/VINFLUSH0000004') && r.html.includes('/car/VINFLUSH0000005') && /New this week<\/span><span class="value accent">1</.test(r.html));
r = await get('/yard/live-yard-bryan');
check('live yard page: no notice', r.status === 200 && !r.html.includes('list-note') && !/has not changed since/.test(r.html));

/* ---------- car pages ---------- */
r = await get('/car/VINSTALE0000001');
check('stale car page -> 200', r.status === 200, r.status);
check('stale car page: the sentence replaces the typical-stay countdown',
  /This yard’s list has not changed since Nov 6, 2026\. Call before you go\./.test(text(r.html)) && !/Cars typically last ~60 days/.test(r.html) && !/~60 typical/.test(r.html));
check('stale car page: still "New" (its own date; the list is not frozen)', /badge-new">New</.test(r.html));
check('stale car page: the description says so too', /yard list unchanged since Nov 6, 2026, call before you go/.test(r.html));
r = await get('/car/VINFROZEN000002');
check('frozen car page: no "New" badge though dated 2 days ago', !/badge-new">New</.test(r.html) && /Until it changes/.test(r.html));
r = await get('/car/VINFLUSH0000004');
check('flush car page: not "New", no notice (the list changed)', !/badge-new">New</.test(r.html) && !r.html.includes('list-note'));
r = await get('/car/VINLIVE00000006');
check('live car page: typical-stay line as before, no notice', /Cars typically last ~60 days at this yard/.test(r.html) && !r.html.includes('list-note'));

/* ---------- a directory from before the columns ---------- */
// (The pages keep /v1/yards in memory per isolate, so this is checked on the
// helpers the pages call: no columns -> no list info -> nothing changes.)
const old = yardListOf(BASE_YF, YARDS[1].slice(0, 7));
check('old directory: no sentence, nothing held back', old === null && yardListSentence(old) === '' && !yardListHeld(old, daysAgo(1)));

console.log(failures ? `\n${failures} FAILED` : '\nALL PASS');
process.exit(failures ? 1 : 0);
