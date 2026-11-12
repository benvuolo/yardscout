/* Unit test: the funnel counters in docs/app.js count what they say
 * (2026-11-12 funnel audit). Loads the REAL analytics code out of docs/app.js
 * (top-level functions and consts) into a vm context with a fake browser and
 * reads the beacons it would send.
 *
 *   guard      web on localhost / 127.0.0.1: silent. Automated browser: silent
 *              everywhere. The app shells (hostname "localhost" too): counted,
 *              with their platform and the counting-rules version.
 *   once only  a zip counts when entered or changed, not when a launch
 *              restores it; a part search counts once per distinct part + car,
 *              not per re-render; the Pro sheet is a "paywall open" only for
 *              someone who is not Pro, and never for the re-open after a
 *              checkout or an unlock code.
 *   store taps store-click + store-click/<store>-<place>, web only.
 *   store link one builder decides the store per platform (Android to
 *              Google Play, iPhone and iPad to the App Store).
 *
 * Run: node backend/test/funnel_counters_unit.mjs   (APP_JS=<path> tests
 * another copy of app.js, e.g. the previous commit's, to see it fail). */
import fs from 'node:fs';
import vm from 'node:vm';

const APP = process.env.APP_JS || new URL('../../docs/app.js', import.meta.url);
const src = fs.readFileSync(APP, 'utf8');
const lines = src.split('\n');

let failures = 0;
const check = (name, ok, detail = '') => {
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + detail}`);
  if (!ok) failures++;
};

/* A top-level function: from "function NAME(" (or "async function NAME(") at
 * column 0 to the next line that is exactly "}". */
function fn(name) {
  const start = lines.findIndex(l => l.startsWith(`function ${name}(`) || l.startsWith(`async function ${name}(`));
  if (start < 0) return null;
  const end = lines.findIndex((l, i) => i > start && l === '}');
  return end < 0 ? null : lines.slice(start, end + 1).join('\n');
}
/* A top-level const: one line, or through the closing "};" / "];" line. */
function konst(name) {
  const start = lines.findIndex(l => l.startsWith(`const ${name} = `));
  if (start < 0) return null;
  if (/;\s*(\/\/.*)?$/.test(lines[start])) return lines[start];
  const end = lines.findIndex((l, i) => i > start && /^[}\]]\)?;/.test(l));
  return end < 0 ? null : lines.slice(start, end + 1).join('\n');
}

const FNS = ['analyticsOff', 'sendEvent', 'track', 'zipEntryIsNew', 'pfSearchIsNew', 'paywallIsProspect',
  'pfSearchSignal', 'pfCountSearch', 'normalizePostal', 'setZipCenter', 'storeClickEvent'];
const CONSTS = ['FUNNEL_EVENTS', 'REASON_EVENTS', 'ANALYTICS_OFF', 'EVENTS_V', '_pfCounted', 'PAYWALL_NOT_PROSPECT'];
const parts = {};
for (const n of CONSTS) { parts[n] = konst(n); check(`app.js has const ${n}`, !!parts[n]); }
for (const n of FNS) { parts[n] = fn(n); check(`app.js has function ${n}`, !!parts[n]); }
if (failures) { console.log(`\n${failures} FAILURES (cannot load the analytics code)`); process.exit(1); }

/* One fake browser (or app shell) with the real analytics code loaded. */
function boot({ hostname = 'yardscout.io', webdriver = false, native = false, android = false, storage = {} } = {}) {
  const beacons = [];
  const store = { ...storage };
  const el = () => ({ style: {}, placeholder: '', value: '' });
  const ctx = {
    console, URLSearchParams, TextEncoder,
    location: { hostname, search: '', pathname: '/', hash: '' },
    navigator: { webdriver, userAgent: '', sendBeacon: (url, blob) => { beacons.push(JSON.parse(blob.text)); return true; } },
    Blob: class { constructor(p) { this.text = p.join(''); } },
    localStorage: { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); }, removeItem: (k) => { delete store[k]; } },
    document: { getElementById: el },
    fetch: async (url) => ({ ok: true, json: async () => ({ places: [{ latitude: '33.45', longitude: '-112.07' }] }) }),
    setTimeout: () => 0,
    window: {},
  };
  vm.createContext(ctx);
  const prelude = `
    const IS_NATIVE = ${native}; const IS_ANDROID = ${native && android};
    const GOATCOUNTER_CODE = null; const ATTRIB = null; const EVENTS_API = 'https://api.test/v1/events';
    let zipCoordsCache = {}; let activeZipCoords = null; let pfCat = { id: 'alternator' };
    function pfSyncWhere() {} function renderLive() {}
    globalThis.__set = (k, v) => { if (k === 'pfCat') pfCat = v; };
  `;
  new vm.Script(prelude + [...CONSTS.slice(0, 2), 'analyticsOff', ...CONSTS.slice(2), ...FNS.filter(n => n !== 'analyticsOff')].map(n => parts[n]).join('\n')
    + '\nglobalThis.__api = { analyticsOff, sendEvent, track, zipEntryIsNew, pfSearchIsNew, paywallIsProspect, pfCountSearch, setZipCenter, storeClickEvent, ANALYTICS_OFF, EVENTS_V };',
  { filename: 'app.js (extract)' }).runInContext(ctx);
  return { api: ctx.__api, beacons, store, set: ctx.__set, events: () => beacons.map(b => b.e) };
}

/* ---------- 1. the guard ---------- */
{
  const a = boot().api.analyticsOff;
  check('guard: web on localhost is silent', a('localhost', false, false) === true);
  check('guard: web on 127.0.0.1 is silent', a('127.0.0.1', false, false) === true);
  check('guard: web on [::1] and 0.0.0.0 is silent', a('[::1]', false, false) === true && a('0.0.0.0', false, false) === true);
  check('guard: the live site counts', a('yardscout.io', false, false) === false && a('benvuolo.github.io', false, false) === false);
  check('guard: an automated browser is silent on the live site', a('yardscout.io', true, false) === true);
  check('guard: the app shell on hostname "localhost" counts', a('localhost', false, true) === false);
  check('guard: an automated browser is silent inside an app shell too', a('localhost', true, true) === true);
  check('guard: webdriver undefined (real WebViews) is not "automated"', a('localhost', undefined, true) === false && a('yardscout.io', undefined, false) === false);
}
{
  // The whole path: what each kind of client actually sends for one event.
  const web = boot(); web.api.track('first-visit');
  check('web on yardscout.io sends first-visit as web, counting rules v2', web.beacons.length === 1 && web.beacons[0].e === 'first-visit' && web.beacons[0].p === 'web' && web.beacons[0].v === 2, JSON.stringify(web.beacons));
  const local = boot({ hostname: 'localhost' }); local.api.track('first-visit');
  check('web on localhost sends nothing', local.beacons.length === 0 && local.api.ANALYTICS_OFF === true, JSON.stringify(local.beacons));
  const bot = boot({ webdriver: true }); bot.api.track('first-visit');
  check('automated browser on the live site sends nothing', bot.beacons.length === 0, JSON.stringify(bot.beacons));
  const ios = boot({ hostname: 'localhost', native: true }); ios.api.track('first-visit');
  check('iOS shell (capacitor://localhost) sends first-visit as ios', ios.beacons.length === 1 && ios.beacons[0].p === 'ios' && ios.beacons[0].v === 2 && ios.api.ANALYTICS_OFF === false, JSON.stringify(ios.beacons));
  const and = boot({ hostname: 'localhost', native: true, android: true }); and.api.track('iap-subscribe/watch-limit');
  check('Android shell (https://localhost) sends checkout-start + checkout/<gate> as android', JSON.stringify(and.events()) === JSON.stringify(['checkout-start', 'checkout/watch-limit']) && and.beacons.every(b => b.p === 'android'), JSON.stringify(and.beacons));
  const botApp = boot({ hostname: 'localhost', native: true, webdriver: true }); botApp.api.track('first-visit');
  check('automated app shell (the e2e stubs) sends nothing', botApp.beacons.length === 0);
  check('no beacon carries anything but the event, the utm fields, the platform and the version',
    [...web.beacons, ...ios.beacons, ...and.beacons].every(b => Object.keys(b).sort().join() === 'cmp,e,med,p,src,v'), JSON.stringify(web.beacons[0]));
}

/* ---------- 2. once-only counters ---------- */
{
  // Zip: first entry counts, a launch restoring it does not, a change does.
  const b = boot();
  await b.api.setZipCenter('85003');
  check('zip: first entry counts once', JSON.stringify(b.events()) === JSON.stringify(['zip-entered']) && b.store.jh_zip === '85003', JSON.stringify(b.events()));
  await b.api.setZipCenter('85003'); await b.api.setZipCenter('85003');
  check('zip: the same zip again (a launch restoring it, a second field) does not count', b.events().length === 1, JSON.stringify(b.events()));
  await b.api.setZipCenter('30310');
  check('zip: a changed zip counts', b.events().length === 2, JSON.stringify(b.events()));
  await b.api.setZipCenter('85003');
  check('zip: changing back counts (it is a change)', b.events().length === 3);
  await b.api.setZipCenter('8500');
  check('zip: an incomplete zip counts nothing and is not saved', b.events().length === 3 && b.store.jh_zip === '85003');
  // A returning visitor: the saved zip is restored at launch.
  const back = boot({ storage: { jh_zip: '85003', ys_seen: '1' } });
  await back.api.setZipCenter('85003');
  check('zip: a returning visitor\'s launch sends no "entered a zip"', back.beacons.length === 0, JSON.stringify(back.beacons));
  const ca = boot(); await ca.api.setZipCenter('T2A 0A1'); await ca.api.setZipCenter('T2A0A1');
  check('zip: a Canadian postal code counts once too', JSON.stringify(ca.events()) === JSON.stringify(['zip-entered']), JSON.stringify(ca.events()));
}
{
  // Part search: the audit recorded one search four times (pick the car, tap
  // "Find donor cars", re-sort, tap again). Each of those re-runs pfRunSearch.
  const b = boot();
  const s = { year: 2012, make: 'Chevrolet', model: 'Equinox' };
  const first = b.api.pfCountSearch('fit', s);
  for (let i = 0; i < 3; i++) b.api.pfCountSearch('fit', { ...s });
  check('part search: four renders of one search count once', first === true && b.events().filter(e => e === 'part-first-search').length === 1, JSON.stringify(b.events()));
  check('part search: the most-searched signals count once too', JSON.stringify(b.events()) === JSON.stringify(['part-first-search', 'pf/alternator', 'pf-car/chevrolet-equinox']), JSON.stringify(b.events()));
  b.api.pfCountSearch('fit', { year: 2013, make: 'Chevrolet', model: 'Equinox' });
  check('part search: another year is another search', b.events().filter(e => e === 'part-first-search').length === 2);
  b.set('pfCat', { id: 'starter' });
  b.api.pfCountSearch('fit', s);
  check('part search: another part is another search', b.events().filter(e => e === 'part-first-search').length === 3 && b.events().includes('pf/starter'));
  const n = b.beacons.length;
  b.api.pfCountSearch('browse', { year: 0, make: '', model: '' }); b.api.pfCountSearch('browse', { year: 0, make: '', model: '' });
  check('part browse (no car): not a funnel "part search", its part signal counts once', !b.events().slice(n).includes('part-first-search')
    && JSON.stringify(b.events().slice(n)) === JSON.stringify(['pf/starter']), JSON.stringify(b.events().slice(n)));
  check('pfRunSearch and pfRunBrowse count through pfCountSearch only', /\n  pfCountSearch\('fit', s\);/.test(src) && /\n  pfCountSearch\('browse', s\);/.test(src)
    && !/\n  track\('part-first-search'\);/.test(src) && !/\n  track\('part-browse'\);/.test(src));
}
{
  const { api } = boot();
  check('paywall: a free visitor opening the sheet is a prospect', api.paywallIsProspect('header-pill', false) === true && api.paywallIsProspect('watch-limit', false) === true);
  check('paywall: a Pro member opening their own sheet is not', api.paywallIsProspect('header-pill', true) === false);
  check('paywall: the re-open after an unlock code is not', api.paywallIsProspect('code-redeemed', false) === false && api.paywallIsProspect('code-redeemed', true) === false);
  check('paywall: the re-opens around a Stripe return are not', api.paywallIsProspect('checkout-return', false) === false && api.paywallIsProspect('checkout-done', true) === false);
  check('openUpgradeSheet decides with paywallIsProspect and has no unconditional pro-lock',
    /track\(\(paywallIsProspect\(upgradeTrigger, isPro\(\)\) \? 'pro-lock\/' : 'pro-sheet-member\/'\) \+ upgradeTrigger\);/.test(src) && !/\n  track\('pro-lock\/' \+ upgradeTrigger\);/.test(src));
  const b = boot();
  b.api.track('pro-lock/header-pill'); b.api.track('pro-sheet-member/code-redeemed'); b.api.track('pro-sheet-member/header-pill');
  check('only the prospect open reaches the funnel (paywall + paywall/<gate>)', JSON.stringify(b.events()) === JSON.stringify(['paywall', 'paywall/header-pill']), JSON.stringify(b.events()));
  const w = boot();
  w.api.track('ent-checkout-start/card-value'); w.api.track('ent-purchased/card-value'); w.api.track('ent-purchased');
  check('web checkout and purchase count per gate, like the apps', JSON.stringify(w.events()) === JSON.stringify(['checkout-start', 'checkout/card-value', 'pro-converted', 'purchase/card-value', 'pro-converted']), JSON.stringify(w.events()));
}

/* ---------- 3. store-link taps ---------- */
{
  const b = boot();
  const ev = b.api.storeClickEvent;
  check('store tap: App Store link from the Pro sheet', ev('https://apps.apple.com/app/yardscout-junkyard-parts/id6817126581', 'sheet') === 'store-click/appstore-sheet');
  check('store tap: short App Store link (static badges)', ev('https://apps.apple.com/app/id6817126581', 'footer') === 'store-click/appstore-footer');
  check('store tap: Google Play link from the watch toast', ev('https://play.google.com/store/apps/details?id=io.yardscout.app', 'toast') === 'store-click/play-toast');
  check('store tap: any other link is not one', ev('https://yardscout.io/yards', 'footer') === null && ev('privacy.html', 'sheet') === null && ev('', 'x') === null);
  b.api.track(ev('https://play.google.com/store/apps/details?id=io.yardscout.app', 'banner'));
  check('store tap sends the funnel counter and the per-store, per-place counter', JSON.stringify(b.events()) === JSON.stringify(['store-click', 'store-click/play-banner']), JSON.stringify(b.events()));
  check('store taps are wired once for every link on the page, web only',
    /if \(!IS_NATIVE\) document\.addEventListener\('click', \(e\) => \{\n  const a = e\.target && e\.target\.closest && e\.target\.closest\('a\[href\]'\);\n  const ev = a && storeClickEvent\(a\.href, storeClickPlace\(a\)\);\n  if \(ev\) track\(ev\);\n\}, true\);/.test(src));
}

/* ---------- 4. the store a web visitor is sent to (one builder) ---------- */
{
  const wsp = fn('webStorePlatform'), sl = fn('storeLink');
  check('app.js has one store-link builder (webStorePlatform + storeLink)', !!wsp && !!sl);
  if (wsp && sl) {
    const ctx = {};
    vm.createContext(ctx);
    new vm.Script(`${konst('APP_STORE_URL')}\n${konst('PLAY_URL')}\n${wsp}\n${sl}\nglobalThis.__api = { webStorePlatform, storeLink };`).runInContext(ctx);
    const { webStorePlatform, storeLink } = ctx.__api;
    const UA = {
      android: 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36',
      iphone: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
      ipad: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
      mac: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
      win: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
    };
    check('store: an Android browser is an Android visitor', webStorePlatform(UA.android, 'Linux armv8l', 5) === 'android');
    check('store: an iPhone is an iOS visitor', webStorePlatform(UA.iphone, 'iPhone', 5) === 'ios');
    check('store: an iPad (reports as a Mac with touch) is an iOS visitor', webStorePlatform(UA.ipad, 'MacIntel', 5) === 'ios');
    check('store: a Mac or Windows desktop is neither', webStorePlatform(UA.mac, 'MacIntel', 0) === null && webStorePlatform(UA.win, 'Win32', 0) === null);
    const play = storeLink('android'), apple = storeLink('ios');
    check('store: Android goes to Google Play', /^https:\/\/play\.google\.com\/store\/apps\/details\?id=io\.yardscout\.app$/.test(play.url) && play.name === 'Google Play' && play.store === 'play', JSON.stringify(play));
    check('store: iOS goes to the App Store', /^https:\/\/apps\.apple\.com\/app\/.*id6817126581$/.test(apple.url) && apple.name === 'the App Store' && apple.store === 'appstore', JSON.stringify(apple));
    check('store: every "Get the app" builder goes through storeLink (no second place picks a store URL)',
      (src.match(/\bPLAY_URL\b/g) || []).length === 2 && (src.match(/\bAPP_STORE_URL\b/g) || []).length === 2
      && /href="\$\{storeLink\(WEB_STORE\)\.url\}"/.test(src) && /const st = storeLink\(platform\);/.test(src));
    check('store: the Pro sheet link is set per platform (applyStoreLinks)', /function applyStoreLinks\(/.test(src));
  }
}

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
