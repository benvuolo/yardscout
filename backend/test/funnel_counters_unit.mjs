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
 *   narrowing  narrow/<kind> (search box, Filters model / make only, trim
 *              filter, #cars= link): at most once per device per UTC day per
 *              kind, kinds independent, a new day counts again, storage that
 *              throws still counts once (memory), unknown kinds never sent.
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
  'pfSearchSignal', 'pfCountSearch', 'normalizePostal', 'setZipCenter', 'storeClickEvent', 'narrowDayIsNew', 'trackNarrow',
  'checkoutFailClass', 'checkoutOutcomeOf', 'webCheckoutFailClass', 'productLoadFailClass', 'checkoutBegin', 'checkoutResume', 'checkoutEnd'];
const CONSTS = ['FUNNEL_EVENTS', 'REASON_EVENTS', 'ANALYTICS_OFF', 'EVENTS_V', '_pfCounted', 'PAYWALL_NOT_PROSPECT', 'NARROW_KINDS', '_narrowMem',
  'CHECKOUT_OUTCOMES', 'CHECKOUT_FAIL_CLASSES'];
const parts = {};
for (const n of CONSTS) { parts[n] = konst(n); check(`app.js has const ${n}`, !!parts[n]); }
for (const n of FNS) { parts[n] = fn(n); check(`app.js has function ${n}`, !!parts[n]); }
if (failures) { console.log(`\n${failures} FAILURES (cannot load the analytics code)`); process.exit(1); }

/* One fake browser (or app shell) with the real analytics code loaded. */
function boot({ hostname = 'yardscout.io', webdriver = false, native = false, android = false, storage = {}, brokenStorage = false, session = {} } = {}) {
  const beacons = [];
  const store = { ...storage };
  const sess = session;   // shared on purpose: one tab across a Stripe redirect is two boots
  const el = () => ({ style: {}, placeholder: '', value: '' });
  const ctx = {
    console, URLSearchParams, TextEncoder,
    location: { hostname, search: '', pathname: '/', hash: '' },
    navigator: { webdriver, userAgent: '', sendBeacon: (url, blob) => { beacons.push(JSON.parse(blob.text)); return true; } },
    Blob: class { constructor(p) { this.text = p.join(''); } },
    localStorage: brokenStorage
      ? { getItem: () => { throw new Error('SecurityError'); }, setItem: () => { throw new Error('QuotaExceeded'); }, removeItem: () => {} }
      : { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); }, removeItem: (k) => { delete store[k]; } },
    sessionStorage: brokenStorage
      ? { getItem: () => { throw new Error('SecurityError'); }, setItem: () => { throw new Error('QuotaExceeded'); }, removeItem: () => { throw new Error('SecurityError'); } }
      : { getItem: (k) => (k in sess ? sess[k] : null), setItem: (k, v) => { sess[k] = String(v); }, removeItem: (k) => { delete sess[k]; } },
    document: { getElementById: el },
    fetch: async (url) => ({ ok: true, json: async () => ({ places: [{ latitude: '33.45', longitude: '-112.07' }] }) }),
    setTimeout: () => 0,
    window: {},
  };
  vm.createContext(ctx);
  const prelude = `
    const IS_NATIVE = ${native}; const IS_ANDROID = ${native && android};
    const GOATCOUNTER_CODE = null; const ATTRIB = null; const EVENTS_API = 'https://api.test/v1/events';
    let zipCoordsCache = {}; let activeZipCoords = null; let pfCat = { id: 'alternator' }; let _coOpen = false;
    function pfSyncWhere() {} function renderLive() {}
    globalThis.__set = (k, v) => { if (k === 'pfCat') pfCat = v; };
  `;
  new vm.Script(prelude + [...CONSTS.slice(0, 2), 'analyticsOff', ...CONSTS.slice(2), ...FNS.filter(n => n !== 'analyticsOff')].map(n => parts[n]).join('\n')
    + '\nglobalThis.__api = { analyticsOff, sendEvent, track, zipEntryIsNew, pfSearchIsNew, paywallIsProspect, pfCountSearch, setZipCenter, storeClickEvent, narrowDayIsNew, trackNarrow, ANALYTICS_OFF, EVENTS_V,'
    + ' checkoutFailClass, checkoutOutcomeOf, webCheckoutFailClass, productLoadFailClass, checkoutBegin, checkoutResume, checkoutEnd, CHECKOUT_OUTCOMES, CHECKOUT_FAIL_CLASSES };',
  { filename: 'app.js (extract)' }).runInContext(ctx);
  return { api: ctx.__api, beacons, store, sess, set: ctx.__set, events: () => beacons.map(b => b.e) };
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
  check('web on yardscout.io sends first-visit as web, counting rules v4', web.beacons.length === 1 && web.beacons[0].e === 'first-visit' && web.beacons[0].p === 'web' && web.beacons[0].v === 4, JSON.stringify(web.beacons));
  const local = boot({ hostname: 'localhost' }); local.api.track('first-visit');
  check('web on localhost sends nothing', local.beacons.length === 0 && local.api.ANALYTICS_OFF === true, JSON.stringify(local.beacons));
  const bot = boot({ webdriver: true }); bot.api.track('first-visit');
  check('automated browser on the live site sends nothing', bot.beacons.length === 0, JSON.stringify(bot.beacons));
  const ios = boot({ hostname: 'localhost', native: true }); ios.api.track('first-visit');
  check('iOS shell (capacitor://localhost) sends first-visit as ios', ios.beacons.length === 1 && ios.beacons[0].p === 'ios' && ios.beacons[0].v === 4 && ios.api.ANALYTICS_OFF === false, JSON.stringify(ios.beacons));
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

/* ---------- 5. how the Cars list is narrowed ---------- */
{
  const today = new Date().toISOString().slice(0, 10);
  const yesterday = new Date(Date.now() - 864e5).toISOString().slice(0, 10);
  const b = boot();
  const ok1 = b.api.trackNarrow('search');
  const ok2 = b.api.trackNarrow('search');
  check('narrow: a search-box pick counts once, the second pick the same day does not', ok1 === true && ok2 === false
    && JSON.stringify(b.events()) === JSON.stringify(['narrow/search']), JSON.stringify(b.events()));
  check('narrow: the beacon is an ordinary anonymous counter (event, utm fields, platform, v4)',
    b.beacons.length === 1 && Object.keys(b.beacons[0]).sort().join() === 'cmp,e,med,p,src,v' && b.beacons[0].v === 4 && b.beacons[0].p === 'web', JSON.stringify(b.beacons));
  check('narrow: the day is kept on the device only, per kind', JSON.parse(b.store.ys_narrow).search === today, b.store.ys_narrow);
  for (const k of ['search-trim', 'filters-model', 'filters-make', 'trim', 'link']) b.api.trackNarrow(k);
  for (const k of ['search-trim', 'filters-model', 'filters-make', 'trim', 'link']) b.api.trackNarrow(k);
  check('narrow: each kind counts once a day, independently of the others',
    JSON.stringify(b.events()) === JSON.stringify(['narrow/search', 'narrow/search-trim', 'narrow/filters-model', 'narrow/filters-make', 'narrow/trim', 'narrow/link']), JSON.stringify(b.events()));
  const later = boot({ storage: { ys_narrow: JSON.stringify({ search: today, link: yesterday }) } });
  later.api.trackNarrow('search'); later.api.trackNarrow('link'); later.api.trackNarrow('link');
  check('narrow: a reload the same day does not count again; a new day does (once)', JSON.stringify(later.events()) === JSON.stringify(['narrow/link']), JSON.stringify(later.events()));
  check('narrow: the stored day moves to today', JSON.parse(later.store.ys_narrow).link === today);
  const broken = boot({ brokenStorage: true });
  broken.api.trackNarrow('trim'); broken.api.trackNarrow('trim');
  check('narrow: storage that throws (private mode) still counts once while the page is open', JSON.stringify(broken.events()) === JSON.stringify(['narrow/trim']), JSON.stringify(broken.events()));
  const junk = boot({ storage: { ys_narrow: '{not json' } });
  junk.api.trackNarrow('filters-make');
  check('narrow: a damaged stored value is ignored, not fatal', JSON.stringify(junk.events()) === JSON.stringify(['narrow/filters-make']), JSON.stringify(junk.events()));
  const u = boot();
  check('narrow: an unknown kind is never sent', u.api.trackNarrow('search-box-typed-xterra') === false && u.beacons.length === 0);
  const ios = boot({ hostname: 'localhost', native: true });
  ios.api.trackNarrow('search');
  check('narrow: the iPhone app sends it as ios (after its next store update)', ios.beacons.length === 1 && ios.beacons[0].p === 'ios' && ios.beacons[0].e === 'narrow/search');
  const off = boot({ hostname: 'localhost' });
  off.api.trackNarrow('search');
  check('narrow: a local copy sends nothing', off.beacons.length === 0);
  // Wiring: one route per action.
  check('narrow: the search pick counts a search (or a trim row) and hands over the route',
    /narrowRouteTaken\(\);\n  trackNarrow\(trimRow \? 'search-trim' : 'search'\);/.test(src) && !/track\('car-search'\)/.test(src));
  check('narrow: a #cars= link counts as link (not car-link, which reached only the switched-off analytics)',
    /function startCarsIntent\(c\) \{\n  narrowRouteTaken\(\);\n  trackNarrow\('link'\);/.test(src) && !/track\('car-link'\)/.test(src));
  check('narrow: the box syncing to the filters never counts', !/trackNarrow/.test(fn('carSearchSync') || 'trackNarrow'));
  check('narrow: the week chip and the box\'s clear tag their make change so it is not a Filters choice',
    (src.match(/new CustomEvent\('change', \{ detail: \{ route: '(week-chip|search-clear)' \} \}\)/g) || []).length === 2 && !/sel\.dispatchEvent\(new Event\('change'\)\)/.test(src));
  check('narrow: the Trim control counts only a chosen trim', /setLiveTrim\(e\.target\.value\);\n  if \(e\.target\.value\) trackNarrow\('trim'\);/.test(src));
}

/* ---------- 6. how a checkout attempt ends (counting rules v4) ---------- */
{
  const { api } = boot();
  // Exactly what each native plugin rejects with today (they send a message, no code).
  const IOS_REJECTS = { 'Product not available.': 'product-unavailable', 'Purchase could not be verified.': 'unverified',
    // StoreKit's own localizedDescription (network, payments not allowed, ...): one class, "store"
    'The operation couldn’t be completed. (StoreKit.StoreKitError error 1.)': 'store', 'Purchases are not allowed on this device.': 'store' };
  const ANDROID_REJECTS = { 'Google Play billing isn’t available on this device right now.': 'store-unavailable',
    'Can’t reach Google Play — check your connection and try again.': 'network',
    'Google Play billing error.': 'store', 'Item already owned.': 'store', 'Product not available.': 'product-unavailable', 'Purchase failed.': 'unknown' };
  for (const [m, c] of Object.entries({ ...IOS_REJECTS, ...ANDROID_REJECTS })) {
    check(`fail class: plugin reject "${m.slice(0, 50)}" -> ${c}`, api.checkoutFailClass(new Error(m)) === c, api.checkoutFailClass(new Error(m)));
  }
  check('fail class: no message, a bare string, a Capacitor error with a code', api.checkoutFailClass(new Error('')) === 'unknown' && api.checkoutFailClass(null) === 'unknown'
    && api.checkoutFailClass('Product not available.') === 'product-unavailable' && api.checkoutFailClass(Object.assign(new Error('"Purchases" plugin is not implemented on ios'), { code: 'UNIMPLEMENTED' })) === 'unknown');
  check('fail class: every class it can return is in CHECKOUT_FAIL_CLASSES', [...Object.values(IOS_REJECTS), ...Object.values(ANDROID_REJECTS), 'unknown'].every(c => api.CHECKOUT_FAIL_CLASSES.includes(c)));
  // purchase() resolves
  const R = [[{ entitled: true }, 'bought'], [{ entitled: false, cancelled: true }, 'cancelled'], [{ cancelled: true }, 'cancelled'],
    [{ entitled: false, pending: true }, 'pending'], [{ entitled: false }, 'incomplete'], [{}, 'incomplete'], [null, 'incomplete'], [undefined, 'incomplete']];
  for (const [r, o] of R) check(`outcome: purchase() resolved ${JSON.stringify(r)} -> ${o}`, api.checkoutOutcomeOf(r) === o, api.checkoutOutcomeOf(r));
  check('outcome: every outcome name is in CHECKOUT_OUTCOMES', R.every(([, o]) => api.CHECKOUT_OUTCOMES.includes(o)));
  check('web fail class: 503 not configured, other answers server, no answer network', api.webCheckoutFailClass(503, false) === 'not-configured'
    && api.webCheckoutFailClass(500, false) === 'server' && api.webCheckoutFailClass(200, false) === 'server' && api.webCheckoutFailClass(0, true) === 'network');
  // getProduct as the sheet opens
  check('product load: available = no failure', api.productLoadFailClass({ available: true, price: '$8.99' }) === null);
  check('product load: not available, no error (iOS: Apple returned no product) = product-unavailable', api.productLoadFailClass({ available: false }) === 'product-unavailable' && api.productLoadFailClass(null) === 'product-unavailable');
  check('product load: not available with the store\'s error = its class', api.productLoadFailClass({ available: false, error: 'Can’t reach Google Play — check your connection and try again.' }) === 'network'
    && api.productLoadFailClass({ available: false, error: 'Google Play billing error.' }) === 'store' && api.productLoadFailClass({ available: false, error: 'NSURLErrorDomain -1009' }) === 'store');
  check('product load: getProduct threw (Android billing setup failed) = its class', api.productLoadFailClass(null, new Error('Google Play billing isn’t available on this device right now.')) === 'store-unavailable');
}
{
  // One attempt, exactly one end; the second attempt counts again.
  const b = boot({ hostname: 'localhost', native: true });
  b.api.checkoutBegin(false);
  const e1 = b.api.checkoutEnd('cancelled'), e2 = b.api.checkoutEnd('failed-store');
  check('attempt: tap = checkout-try; the first end counts, a second end for the same attempt does not', e1 === true && e2 === false
    && JSON.stringify(b.events()) === JSON.stringify(['checkout-try', 'checkout-end/cancelled']), JSON.stringify(b.events()));
  b.api.checkoutBegin(false); b.api.checkoutEnd('failed-' + b.api.checkoutFailClass(new Error('Product not available.')));
  check('attempt: a second attempt counts again, with its own end', JSON.stringify(b.events().slice(2)) === JSON.stringify(['checkout-try', 'checkout-end/failed-product-unavailable']), JSON.stringify(b.events()));
  check('attempt: an end with no attempt open sends nothing', b.api.checkoutEnd('bought') === false && b.events().length === 4);
  b.api.checkoutBegin(false); b.api.checkoutEnd('failed-The operation could not be completed');
  check('attempt: an unknown outcome name is never sent as given (failed-unknown)', b.events()[5] === 'checkout-end/failed-unknown', JSON.stringify(b.events()));
  check('attempt: beacons are ordinary v4 counters for the platform', b.beacons.every(x => x.p === 'ios' && x.v === 4 && Object.keys(x).sort().join() === 'cmp,e,med,p,src,v'));
  check('attempt: nothing is kept on the device for an app attempt', !('ys_co_try' in b.sess) && Object.keys(b.store).length === 0);
  // Web: across the Stripe redirect, in this tab's sessionStorage.
  const tab = {};
  const before = boot({ session: tab });
  before.api.checkoutBegin(true);
  check('web attempt: the tap marks this tab ("1", nothing else)', tab.ys_co_try === '1' && Object.keys(tab).join() === 'ys_co_try' && JSON.stringify(before.events()) === JSON.stringify(['checkout-try']));
  const after = boot({ session: tab });   // back from Stripe: a new page in the same tab
  check('web attempt: back from Stripe the attempt is open again', after.api.checkoutResume() === true);
  after.api.checkoutEnd('cancelled');
  check('web attempt: the return ends it once and clears the mark', JSON.stringify(after.events()) === JSON.stringify(['checkout-end/cancelled']) && !('ys_co_try' in tab));
  const again = boot({ session: tab });
  check('web attempt: a later page in the tab with no tap has nothing open', again.api.checkoutResume() === false && again.api.checkoutEnd('unconfirmed') === false && again.beacons.length === 0);
  const priv = boot({ brokenStorage: true });
  priv.api.checkoutBegin(true); priv.api.checkoutEnd('failed-network');
  check('web attempt: storage that throws still counts the tap and an end on the same page', JSON.stringify(priv.events()) === JSON.stringify(['checkout-try', 'checkout-end/failed-network']), JSON.stringify(priv.events()));
  const off = boot({ hostname: 'localhost' });
  off.api.checkoutBegin(true); off.api.checkoutEnd('bought');
  check('attempt: a local copy sends nothing', off.beacons.length === 0);
  // Wiring in app.js: where each end is counted.
  check('wiring: the app tap begins an attempt right after iap-subscribe', /track\('iap-subscribe\/' \+ upgradeTrigger\);\n    checkoutBegin\(false\);/.test(src));
  check('wiring: purchase() resolving ends it with checkoutOutcomeOf, rejecting with a class', /const r = await P\.purchase\(\{ productId: IAP_PRODUCT_ID \}\);\n      checkoutEnd\(checkoutOutcomeOf\(r\)\);/.test(src)
    && /\} catch \(e\) \{\n      checkoutEnd\('failed-' \+ checkoutFailClass\(e\)\);/.test(src));
  check('wiring: the web tap begins an attempt that survives the redirect', /track\('ent-checkout-start\/' \+ upgradeTrigger\);\n[^\n]*\n    checkoutBegin\(true\);/.test(src));
  check('wiring: web cancel, bought and unconfirmed each end it', /if \(checkoutResume\(\)\) checkoutEnd\('cancelled'\);/.test(src) && /checkoutEnd\('bought'\);/.test(src) && /checkoutEnd\('unconfirmed'\);/.test(src)
    && (src.match(/checkoutEnd\('failed-' \+ webCheckoutFailClass\(/g) || []).length === 2);
  check('wiring: the sheet counts a product that did not load, from both failure paths', (src.match(/track\('iap-product-failed\/' \+ /g) || []).length === 2);
  check('wiring: no error text is ever put into an event name', !/track\([^)]*e\.message/.test(src) && !/track\([^)]*p\.error/.test(src));
}

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
