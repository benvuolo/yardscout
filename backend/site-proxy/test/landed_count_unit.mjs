/* Unit test: counting views of the /landed pages (src/landed_count.js,
 * 2026-11-20). The event names, the source rule, and the inline page script
 * itself run in a vm with a fake browser (beacons and the button rewrite).
 * Run: node test/landed_count_unit.mjs   (from backend/site-proxy/) */
import vm from 'node:vm';
import { landedSource, landedEventNames, landedCountScript, EVENTS_URL } from '../src/landed_count.js';

let failures = 0, passes = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + detail}`); if (ok) passes++; else failures++; };
const EVENT_RE = /^[a-z0-9][a-z0-9/_-]{0,47}$/;   // backend/src/attribution.js
const J = JSON.stringify;

/* ---- names ---- */
check('model page, plain', J(landedEventNames('toyota-4runner', '')) === J(['landed-view/toyota-4runner']), J(landedEventNames('toyota-4runner', '')));
check('model page, a source', J(landedEventNames('toyota-4runner', 'reddit')) === J(['landed-view/toyota-4runner', 'landed-src/reddit/toyota-4runner']));
check('make page', J(landedEventNames('toyota', 'google')) === J(['landed-view/toyota', 'landed-src/google/toyota']));
const long = 'mercedes-benz-grand-marquis-super-long-name-edition-extra';
const ln = landedEventNames(long, 'abcdefghijkl');
check('long slugs are cut to fit 48 characters, never ending in a hyphen', ln.length === 2 && ln.every((e) => EVENT_RE.test(e) && e.length <= 48 && !e.endsWith('-')), J(ln));
check('every name passes the API\'s rule', [...landedEventNames('a', 'x'), ...landedEventNames(long, ''), ...landedEventNames('Toyota 4Runner!', 'bing')].every((e) => EVENT_RE.test(e)));
check('odd characters in a slug are made safe', J(landedEventNames('Toyota 4Runner!', '')) === J(['landed-view/toyota-4runner']));
check('no slug: no events', J(landedEventNames('', 'reddit')) === '[]');
check('a bad source adds nothing', J(landedEventNames('toyota', 'Bad Word!')) === J(['landed-view/toyota']) && J(landedEventNames('toyota', '-x')) === J(['landed-view/toyota']));

/* ---- source rule ---- */
const S = (q, r) => landedSource(q, r);
check('?s=reddit wins over any referrer', J(S('?s=reddit', 'https://www.google.com/')) === J({ src: 'reddit', explicit: true }));
check('?s= is lowercased', S('?s=Reddit', '').src === 'reddit');
check('?s= with letters, digits and hyphens up to 12', S('?s=r-cartalk-1', '').src === 'r-cartalk-1' && S('?x=1&s=fb2', '').src === 'fb2');
for (const bad of ['?s=', '?s=thirteenchars', '?s=a%20b', '?s=a_b', '?s=%3Cb%3E', '?s=-lead', '?s=%E0%A4%A', '?s=a.b'])
  check(`bad ?s ignored (${bad}): falls to the referrer`, J(S(bad, 'https://old.reddit.com/r/4Runner/')) === J({ src: 'reddit', explicit: false }), J(S(bad, 'https://old.reddit.com/')));
check('referrer: google (any country site)', S('', 'https://www.google.com/').src === 'google' && S('', 'https://www.google.co.uk/').src === 'google' && S('', 'https://google.de/').src === 'google');
check('referrer: bing, duckduckgo, facebook (m., l.), youtube', S('', 'https://www.bing.com/search?q=x').src === 'bing' && S('', 'https://duckduckgo.com/').src === 'duckduckgo'
  && S('', 'https://m.facebook.com/').src === 'facebook' && S('', 'https://l.facebook.com/l.php').src === 'facebook' && S('', 'https://www.youtube.com/watch').src === 'youtube');
check('unknown referrers: none', S('', 'https://example.com/').src === '' && S('', 'https://notreddit.com/').src === '' && S('', 'https://reddit.com.evil.io/').src === '' && S('', 'https://google.evil.io/').src === '' && S('', 'https://yardscout.io/landed').src === '');
check('no or bad referrer: none', J(S('', '')) === J({ src: '', explicit: false }) && S('', 'not a url').src === '');

/* ---- the page script, run as a browser would ---- */
function runScript(page, { search = '', referrer = '', webdriver = false, host = 'yardscout.io', beacon = true } = {}) {
  const sent = [], links = [{ href: 'https://yardscout.io/?utm_source=page&utm_medium=model&utm_campaign=toyota-4runner#cars=Toyota%7C4Runner' }, { href: 'https://yardscout.io/landed/toyota' }];
  const a = links.map((l) => ({ getAttribute: () => l.href, setAttribute: (k, v) => { l.href = v; } }));
  let ready = null;
  const ctx = vm.createContext({
    navigator: { webdriver, ...(beacon ? { sendBeacon: (u, b) => { sent.push([u, b]); return true; } } : {}) },
    location: { search, hostname: host }, Blob: class { constructor(parts, o) { this.text = parts.join(''); this.type = o.type; } },
    document: { referrer, addEventListener: (ev, f) => { if (ev === 'DOMContentLoaded') ready = f; }, querySelectorAll: (sel) => a.filter((x) => sel.includes('utm_source=page') && x.getAttribute().includes('utm_source=page')) },
    JSON, URL, Object, decodeURIComponent,
  });
  const src = landedCountScript(page).replace(/^<script>|<\/script>$/g, '');
  vm.runInContext(src, ctx);
  if (ready) ready();
  return { sent: sent.map(([u, b]) => ({ u, body: JSON.parse(b.text), type: b.type })), links: links.map((l) => l.href) };
}
let r = runScript('toyota-4runner');
check('plain view: one beacon, landed-view/toyota-4runner, to the API\'s event endpoint', r.sent.length === 1 && r.sent[0].u === EVENTS_URL && J(r.sent[0].body) === J({ e: 'landed-view/toyota-4runner', p: 'web' }) && r.sent[0].type === 'text/plain', J(r.sent));
check('what is sent: the event name and platform only (no ids)', Object.keys(r.sent[0].body).join() === 'e,p');
check('plain view: the buttons keep their tag', r.links[0].includes('utm_source=page&utm_medium=model&utm_campaign=toyota-4runner'));
r = runScript('toyota-4runner', { search: '?s=reddit' });
check('?s=reddit: view + landed-src/reddit/toyota-4runner', J(r.sent.map((x) => x.body.e)) === J(['landed-view/toyota-4runner', 'landed-src/reddit/toyota-4runner']), J(r.sent));
check('?s=reddit: app buttons carry utm_source=reddit, medium and campaign kept; other links untouched', r.links[0] === 'https://yardscout.io/?utm_source=reddit&utm_medium=model&utm_campaign=toyota-4runner#cars=Toyota%7C4Runner' && r.links[1] === 'https://yardscout.io/landed/toyota', J(r.links));
r = runScript('toyota-4runner', { referrer: 'https://www.google.com/' });
check('google referrer: view + landed-src/google/toyota-4runner; buttons unchanged', J(r.sent.map((x) => x.body.e)) === J(['landed-view/toyota-4runner', 'landed-src/google/toyota-4runner']) && r.links[0].includes('utm_source=page'), J(r));
check('automated browser: nothing sent', runScript('toyota-4runner', { webdriver: true }).sent.length === 0);
check('local copy: nothing sent', runScript('toyota-4runner', { host: 'localhost' }).sent.length === 0 && runScript('toyota-4runner', { host: '127.0.0.1' }).sent.length === 0);
check('no sendBeacon: nothing sent, no error', runScript('toyota-4runner', { beacon: false }).sent.length === 0);
check('the script is plain inline JS with no other host than the API', !/https?:\/\/(?!yardscout-api\.yardscout\.workers\.dev)/.test(landedCountScript('toyota-4runner').replace(/new URL\(/g, '')));
check('no slug: no script', landedCountScript('') === '');

console.log(failures ? `${failures} FAILURE(S), ${passes} passed` : `ALL PASS (${passes})`);
process.exit(failures ? 1 : 0);
