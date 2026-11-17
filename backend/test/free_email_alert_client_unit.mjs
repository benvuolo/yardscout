/* Unit test: the client half of the free emailed alert (docs/app.js, block
 * FREE EMAILED ALERT ON THE WEB). Loads the REAL pure functions and consts
 * out of docs/app.js into a vm context (as funnel_counters_unit.mjs does) and
 * checks them against the server's own rules (backend/src).
 *
 *   who      offered to a free visitor on the website only (not Pro, not the
 *            app shells)
 *   limits   the distance is the free instant push's 50 mi on both sides; a
 *            wider watch is clamped, a narrower one kept
 *   copy     what is sent is a COPY of free criteria only (rule 6: the stored
 *            watch object is not touched), centre rounded to ~1 km
 *   wording  never "instant", never "every time"; says the limit plainly
 *   events   the app sends shown/asked; confirmed/first-email are the API's
 *
 * Run: node backend/test/free_email_alert_client_unit.mjs */
import fs from 'node:fs';
import vm from 'node:vm';
import { FREE_INSTANT_RADIUS_MI as SERVER_INSTANT_MI } from '../src/devices.js';
import { sanitizeFreeAlertWatch, FREE_ALERT_RADIUS_MI as SERVER_ALERT_MI } from '../src/free_email_alert.js';
import { watchLabel } from '../src/recap_signup.js';

const APP = process.env.APP_JS || new URL('../../docs/app.js', import.meta.url);
const src = fs.readFileSync(APP, 'utf8');
const lines = src.split('\n');

let failures = 0;
const check = (name, ok, detail = '') => {
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + detail}`);
  if (!ok) failures++;
};

// The whole file still parses (compiled, not run).
let parsed = true, parseErr = '';
try { new vm.Script(src, { filename: 'app.js' }); } catch (e) { parsed = false; parseErr = String(e && e.message); }
check('docs/app.js parses', parsed, parseErr);

function fn(name) {
  const start = lines.findIndex(l => l.startsWith(`function ${name}(`) || l.startsWith(`async function ${name}(`));
  if (start < 0) return null;
  const end = lines.findIndex((l, i) => i > start && l === '}');
  return end < 0 ? null : lines.slice(start, end + 1).join('\n');
}
function konst(name) {
  const start = lines.findIndex(l => l.startsWith(`const ${name} = `));
  if (start < 0) return null;
  if (/;\s*(\/\/.*)?$/.test(lines[start])) return lines[start];
  const end = lines.findIndex((l, i) => i > start && /^([}\]]\)?;|\s+\+ .*;$)/.test(l));
  return end < 0 ? null : lines.slice(start, end + 1).join('\n');
}

const FNS = ['falertOffered', 'falertRadiusMi', 'falertLabel', 'falertWatchBody'];
const CONSTS = ['FREE_EMAIL_ALERT_RADIUS_MI', 'FREE_INSTANT_RADIUS_MI', 'FREE_WATCH_LIMIT', 'FUNNEL_EVENTS', 'FALERT_LIMIT_NOTE', 'FALERT_INTRO_HTML'];
const parts = {};
for (const n of CONSTS) { parts[n] = konst(n); check(`app.js has const ${n}`, !!parts[n]); }
for (const n of FNS) { parts[n] = fn(n); check(`app.js has function ${n}`, !!parts[n]); }
if (failures) { console.log(`\n${failures} FAILURES`); process.exit(1); }

const ctx = vm.createContext({ Math, JSON, String, Number });
vm.runInContext([...CONSTS, ...FNS].map(n => parts[n]).join('\n')
  + '\n;globalThis.__x = { falertOffered, falertRadiusMi, falertLabel, falertWatchBody, FREE_EMAIL_ALERT_RADIUS_MI, FREE_INSTANT_RADIUS_MI, FREE_WATCH_LIMIT, FUNNEL_EVENTS, FALERT_LIMIT_NOTE, FALERT_INTRO_HTML };', ctx);
const A = ctx.__x;

/* ---- who ---- */
check('offered: a free visitor on the website', A.falertOffered(false, false) === true);
check('not offered to Pro', A.falertOffered(false, true) === false);
check('not offered in the app shells (free or Pro)', A.falertOffered(true, false) === false && A.falertOffered(true, true) === false);

/* ---- the distance: one number everywhere ---- */
check('client distance = the client free instant push constant', A.FREE_EMAIL_ALERT_RADIUS_MI === A.FREE_INSTANT_RADIUS_MI);
check('client distance = the server constants (devices.js, free_email_alert.js): 50 mi',
  A.FREE_EMAIL_ALERT_RADIUS_MI === SERVER_INSTANT_MI && SERVER_ALERT_MI === SERVER_INSTANT_MI && SERVER_INSTANT_MI === 50);
check('a 250 mi watch is covered for 50 mi', A.falertRadiusMi({ radiusMi: 250 }) === 50);
check('a 25 mi watch keeps its 25 mi', A.falertRadiusMi({ radiusMi: 25 }) === 25);
check('a watch with no radius (made before the picker, or "Anywhere") gets the 50', A.falertRadiusMi({}) === 50 && A.falertRadiusMi({ radiusMi: null }) === 50);
check('only the first 5 watches can carry it (the free watch limit)', A.FREE_WATCH_LIMIT === 5);

/* ---- what is sent: a copy of free criteria ---- */
const stored = { make: 'Toyota', model: '4Runner', yrMin: 2003, yrMax: 2009, matchOnly: true, radiusMi: 250,
  lat: 40.76012, lng: -111.89123, addedAt: '2026-11-12T10:00:00.000Z~abc123', driveFilter: '4x4', trimFilter: 'SR5', serverId: 'x1' };
const before = JSON.stringify(stored);
const body = A.falertWatchBody(stored, null);
check('the copy: make, model, years, rounded centre, radius 50', JSON.stringify(body) === JSON.stringify({ make: 'Toyota', model: '4Runner',
  yearMin: 2003, yearMax: 2009, lat: 40.76, lng: -111.89, radiusMi: 50 }), JSON.stringify(body));
check('no trim, drive, "parts only", addedAt or server id in it', !/SR5|4x4|matchOnly|addedAt|abc123|serverId/.test(JSON.stringify(body)));
check('the stored watch object is untouched (rule 6)', JSON.stringify(stored) === before);
const legacy = { make: 'Honda', model: 'Civic', yrMin: null, yrMax: null };
check('a watch with no centre follows the visitor\'s own place', JSON.stringify(A.falertWatchBody(legacy, { lat: 33.4484, lng: -112.074 }))
  === JSON.stringify({ make: 'Honda', model: 'Civic', yearMin: null, yearMax: null, lat: 33.45, lng: -112.07, radiusMi: 50 }));
check('...and cannot carry the alert when there is no place at all', A.falertWatchBody(legacy, null) === null);
check('a watch with no make cannot carry it', A.falertWatchBody({ model: 'Civic', lat: 1, lng: 1, radiusMi: 50 }, null) === null);
check('the server accepts the copy and keeps the same thing', (() => {
  const s = sanitizeFreeAlertWatch(JSON.parse(JSON.stringify(body)));
  return s && s.make === 'Toyota' && s.model === '4Runner' && s.year_min === 2003 && s.year_max === 2009 && s.lat === 40.76 && s.lng === -111.89 && s.radius_mi === 50;
})());

/* ---- the label is the same text on both sides (the card compares them) ---- */
for (const e of [stored, legacy, { make: 'Ford', model: '', yrMin: 1999, yrMax: null, lat: 1, lng: 1, radiusMi: 10 },
  { make: 'Mercedes-Benz', model: 'Sprinter 2500', yrMin: null, yrMax: 2012, lat: 1, lng: 1, radiusMi: 50 }]) {
  const s = sanitizeFreeAlertWatch(A.falertWatchBody(e, { lat: 1, lng: 1 }));
  check(`label "${A.falertLabel(e)}" = the server's`, A.falertLabel(e) === watchLabel(s), watchLabel(s));
}

/* ---- wording ---- */
const htmlFns = ['falertAskHtml', 'falertPendingHtml', 'falertOnHtml', 'handleFalertHash', 'falertCheck', 'falertTurnOff'].map(fn);
check('the card builders are there', htmlFns.every(Boolean));
const copy = htmlFns.join('\n') + A.FALERT_LIMIT_NOTE + A.FALERT_INTRO_HTML;
check('never "instant", "every time", "always" or "guarantee"', !/instant|every time|always|guarantee/i.test(copy), (copy.match(/.{30}(instant|every time|always|guarantee).{30}/i) || [''])[0]);
check('says "usually the same day"', /usually the same day/.test(copy));
check('says plainly that an email can be late or skipped', /can arrive late or be skipped/.test(A.FALERT_LIMIT_NOTE));
check('the intro sentence: one watch emailed, within 50 mi, on this website', /On this website, free gets <strong>one watch emailed<\/strong>/.test(A.FALERT_INTRO_HTML)
  && /within 50&nbsp;mi/.test(A.FALERT_INTRO_HTML));
check('no Pro prompt in the card (no upgrade sheet, no Pro box)', !/openUpgradeSheet|proBoxHtml|pro-box|See Pro/.test(htmlFns.slice(0, 3).join('\n')));

/* ---- events ---- */
check('the app counts "shown" and "asked"', A.FUNNEL_EVENTS['free-alert-shown'] === 'free-alert-shown' && A.FUNNEL_EVENTS['free-alert-asked'] === 'free-alert-asked');
check('...and never sends the two the API counts', !Object.values(A.FUNNEL_EVENTS).some(v => v === 'free-alert-confirmed' || v === 'free-alert-first-email'));

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
