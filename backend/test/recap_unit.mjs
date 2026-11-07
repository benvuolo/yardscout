/* Unit test: free weekly recap teaser copy (src/alerts.js buildDigestEmail /
 * recapLine / recapSummary). Pure — no Worker needed.
 * Run: node test/recap_unit.mjs */
import { buildDigestEmail, recapLine, recapSummary, usWeekday, digestText } from '../src/alerts.js';

let failures = 0;
const check = (name, ok, extra = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${extra ? ' — ' + extra : ''}`); if (!ok) failures++; };

// "Now" = Monday 2026-11-09 15:00 UTC, the weekly cron instant.
const NOW = Date.parse('2026-11-09T15:00:00Z');
const env = { APP_URL: 'https://yardscout.io/' };
const car = (id, seenAt, dateAdded, extra = {}) => ({ id, year: 2004, make: 'Toyota', model: '4Runner',
  row: '12', location: 'Utah Pick-A-Part - Ogden', seenAt, dateAdded, ...extra });

const tue = car(1, '2026-11-03T18:10:00Z', '2026-11-03');      // Tue midday in every US zone
const lateUtc = car(2, '2026-11-05T05:30:00Z', '2026-11-04');  // Thu 00:30 ET, Wed 23:30 CT → no weekday
const fresh = car(3, '2026-11-09T09:00:00Z', '2026-11-09');    // 6 h before the email
const noSeen = car(4, null, '2026-11-02');
const oldAdded = car(5, '2026-11-04T18:00:00Z', '2026-11-01'); // yard listed it before we saw it
const badAdded = car(6, '2026-11-04T18:00:00Z', 'soon');

check('weekday printed when all US zones agree', usWeekday(Date.parse(tue.seenAt)) === 'Tue');
check('no weekday when zones disagree', usWeekday(Date.parse(lateUtc.seenAt)) === null);

check('certain data → "Landed Tue — Pro would have pinged you Tue."',
  recapLine(tue, { now: NOW }) === 'Landed Tue — Pro would have pinged you Tue.', recapLine(tue, { now: NOW }));
check('zone-ambiguous first sighting → days-before wording, no weekday',
  recapLine(lateUtc, { now: NOW }) === 'Pro would have pinged you 4 days before this email.', recapLine(lateUtc, { now: NOW }));
check('found < 1 day before the email → no line', recapLine(fresh, { now: NOW }) === '');
check('no first-sighting timestamp → no line', recapLine(noSeen, { now: NOW }) === '');
check('landed day uses the yard dateAdded', recapLine(oldAdded, { now: NOW }) === 'Landed Sun — Pro would have pinged you Wed.',
  recapLine(oldAdded, { now: NOW }));
check('malformed dateAdded → no "Landed" claim', recapLine(badAdded, { now: NOW }) === 'Pro would have pinged you Wed.',
  recapLine(badAdded, { now: NOW }));
check('first sighting in the future → no line', recapLine(car(7, '2026-11-10T12:00:00Z', null), { now: NOW }) === '');

/* gone wording */
check('gone car wording (no invented days-on-lot)',
  recapLine(tue, { now: NOW, presence: 'gone' }) === 'Was at Utah Pick-A-Part - Ogden from Tue and left before this email — Pro would have pinged you Tue.',
  recapLine(tue, { now: NOW, presence: 'gone' }));
check('gone line never states "N days" on the lot', !/for \d+ days/.test(recapLine(tue, { now: NOW, presence: 'gone' })));
check('gone, found < 1 day ago → gone line without the Pro clause',
  recapLine(fresh, { now: NOW, presence: 'gone' }) === 'Was at Utah Pick-A-Part - Ogden from Mon and left before this email.',
  recapLine(fresh, { now: NOW, presence: 'gone' }));
check('presence unknown → never says gone', !/left/.test(recapLine(tue, { now: NOW, presence: null })));

/* summary */
const matches = [tue, lateUtc, fresh];
const allKnown = new Map([['1', 'gone'], ['2', 'present'], ['3', 'present']]);
check('summary counts only certain early finds, states gone when all known',
  recapSummary(matches, { now: NOW, presence: allKnown })
    === "2 of this week's 3 matches were found 4–5 days before this email; 1 is already gone. Pro sends an alert within hours of the scan that finds a car.",
  recapSummary(matches, { now: NOW, presence: allKnown }));
const partKnown = new Map([['1', 'gone']]);
check('gone count omitted when presence is incomplete',
  !/gone/.test(recapSummary(matches, { now: NOW, presence: partKnown })), recapSummary(matches, { now: NOW, presence: partKnown }));
check('no summary when nothing certain', recapSummary([fresh, noSeen], { now: NOW }) === '');
check('single-match grammar', /^This week's match was found 5 days before/.test(recapSummary([tue], { now: NOW })), recapSummary([tue], { now: NOW }));

/* full email: free weekly */
const free = buildDigestEmail(env, 'f@test.dev', matches, { weekly: true, now: NOW, presence: allKnown });
check('free recap: summary at the top', free.text.startsWith("2 of this week's 3 matches"));
check('free recap: exactly one upgrade link (text)', (free.text.match(/#tab=alerts/g) || []).length === 1);
check('free recap: exactly one upgrade link (html)', (free.html.match(/#tab=alerts/g) || []).length === 1);
check('free recap: per-car lines present in html', free.html.includes('Landed Tue — Pro would have pinged you Tue.') === false
  && free.html.includes('Was at Utah Pick-A-Part - Ogden from Tue and left before this email'));
check('free recap: every match listed, same order', matches.every((v, i) =>
  free.text.indexOf(`— ${v.location} (row ${v.row})`) >= 0) && free.text.split('\n').filter((l) => /^2004 Toyota 4Runner/.test(l)).length === 3);
check('free recap: no fake urgency words', !/hurry|last chance|act now|only \d+ left/i.test(free.text + free.html));

/* no certain data → original calm line, still one link */
const freeUncertain = buildDigestEmail(env, 'f@test.dev', [fresh, noSeen], { weekly: true, now: NOW });
check('uncertain data: no summary, no per-car lines', !/were found|pinged you/.test(freeUncertain.text));
check('uncertain data: original upsell kept, one link', /Pro would have told you/.test(freeUncertain.text)
  && (freeUncertain.text.match(/#tab=alerts/g) || []).length === 1, freeUncertain.text);

/* Pro instant fallback email is unchanged */
const pro = buildDigestEmail(env, 'p@test.dev', matches, { weekly: false, now: NOW, presence: allKnown });
const expectedPro = `New arrivals matching your YardScout watches:\n\n${digestText(matches)}\n\n`
  + `Open the app for rows, VINs, and part details:\nhttps://yardscout.io/\n\n`
  + `Yards crush cars within weeks — fresh arrivals are the best odds.`;
check('Pro instant email: text identical to before, no html, no teaser', pro.text === expectedPro && !pro.html);
check('Pro instant email subject unchanged', pro.subject === '3 watched cars just hit the yard');

/* sale-only weekly: nothing about Pro */
const saleOnly = buildDigestEmail(env, 'f@test.dev', [], { weekly: true, now: NOW,
  sales: [{ yard: 'Utah Pick-A-Part - Ogden', start_date: '2026-11-14', end_date: '2026-11-15', pct: 50 }] });
check('sale-only recap mentions no Pro', !/Pro/.test(saleOnly.text) && !/Pro/.test(saleOnly.html));

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
