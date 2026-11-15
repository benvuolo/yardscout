// The coverage digest marks a yard request that is already tracked.
// Uses the real yard table from docs/data/inv/manifest.json.
//   node backend/test/coverage_tracked_unit.mjs
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { trackedYardMatches, trackedYardTag, cityFromNote } from '../src/coverage.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const m = JSON.parse(fs.readFileSync(path.resolve(here, '../../docs/data/inv/manifest.json'), 'utf8'));
const dir = { yards: m.yards, counts: m.yardCount };

let pass = 0, fail = 0;
const ok = (c, msg, extra) => { if (c) { pass++; console.log('  ok   ' + msg); } else { fail++; console.log('  FAIL ' + msg + (extra !== undefined ? '  -> ' + JSON.stringify(extra).slice(0, 300) : '')); } };

ok(cityFromNote('Kennewick, WA') === 'Kennewick', 'app note "Kennewick, WA" gives the city');
ok(cityFromNote('https://example.com/inv · Conway, SC') === 'Conway', 'public-form note "site · City, ST" gives the city');
ok(cityFromNote('example.com') === '' && cityFromNote(null) === '', 'a website alone, or no note, gives no city');

let hits = trackedYardMatches(dir, 'U-Pull-It', 'Kennewick');
ok(hits.length === 1 && hits[0].name === 'U-Pull-It Auto Parts - Kennewick' && hits[0].cars > 0, 'U-Pull-It + Kennewick is the one tracked yard', hits);
ok(trackedYardMatches(dir, 'UPullIt', 'Kennewick').length === 1, '"UPullIt" matches "U-Pull-It"');
ok(trackedYardMatches(dir, 'U-Pull-It Auto Parts', 'Kennewick').length === 1, 'filler words in the request do not block a match');
ok(trackedYardMatches(dir, 'Zzyzx Pull Yard', 'Baker').length === 0, 'an unknown yard matches nothing');
ok(trackedYardMatches(dir, 'U-Pull-It', 'Spokane').length === 0, 'the same name in a city we do not track matches nothing');
ok(trackedYardMatches(dir, 'U', 'Kennewick').length === 0 && trackedYardMatches(dir, 'Auto Parts', '').length === 0, 'a one-letter or filler-only name matches nothing');
ok(trackedYardMatches(null, 'U-Pull-It', 'Kennewick').length === 0 && trackedYardMatches({}, 'x', 'y').length === 0, 'no directory, no match (and no throw)');

let tag = trackedYardTag(dir, 'U-Pull-It', ['Kennewick, WA']);
ok(/^ALREADY TRACKED: U-Pull-It Auto Parts - Kennewick \([\d,]+ cars\)$/.test(tag), 'digest tag names the yard and its cars', tag);
ok(trackedYardTag(dir, 'Pick-n-Pull', [null]) === '' && trackedYardTag(dir, 'Pick-n-Pull', []) === '', 'a chain name with no city gets no tag');
ok(trackedYardTag(dir, 'U-Pull R Parts', ['Lexington, KY']) === '', 'a yard we do not track gets no tag');
tag = trackedYardTag({ yards: dir.yards }, 'U-Pull-It', ['Kennewick, WA']);
ok(tag === 'ALREADY TRACKED: U-Pull-It Auto Parts - Kennewick', 'no counts in the directory: the tag still names the yard', tag);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
