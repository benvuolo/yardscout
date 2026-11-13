/* /app and /get (and /open) send phones to their store. Run from
 * backend/site-proxy/:  node test/redirects_unit.mjs */
import worker from '../src/index.js';

let failures = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + detail}`); if (!ok) failures++; };
const go = async (path, ua) => worker.fetch(new Request('https://yardscout.io' + path, { headers: { 'user-agent': ua } }), {}, { waitUntil() {} });
const IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148';
const ANDROID = 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/120 Mobile';
const DESKTOP = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/120';

for (const path of ['/app', '/app/', '/get', '/APP']) {
  let r = await go(path, IPHONE);
  check(`${path} iPhone -> App Store`, r.status === 302 && /apps\.apple\.com/.test(r.headers.get('location') || ''), `${r.status} ${r.headers.get('location')}`);
  r = await go(path, ANDROID);
  check(`${path} Android -> Google Play`, r.status === 302 && /play\.google\.com/.test(r.headers.get('location') || ''), `${r.status} ${r.headers.get('location')}`);
  r = await go(path, DESKTOP);
  check(`${path} desktop -> site`, r.status === 302 && r.headers.get('location') === 'https://yardscout.io/', `${r.status} ${r.headers.get('location')}`);
}
let r = await go('/app?utm_source=facebook&utm_campaign=x', DESKTOP);
check('/app keeps campaign tags for the site', r.headers.get('location') === 'https://yardscout.io/?utm_source=facebook&utm_campaign=x', r.headers.get('location'));
r = await go('/app?utm_source=facebook', ANDROID);
check('/app passes campaign tags to Play as referrer', /play\.google\.com.*&referrer=utm_source%3Dfacebook$/.test(r.headers.get('location') || ''), r.headers.get('location'));
r = await go('/app?utm_source=facebook', IPHONE);
check('/app iPhone with tags still -> App Store', /^https:\/\/apps\.apple\.com/.test(r.headers.get('location') || ''), r.headers.get('location'));
r = await go('/open', ANDROID);
check('/open Android still -> Google Play', r.status === 302 && /play\.google\.com/.test(r.headers.get('location') || ''));
// Falls through to the upstream proxy; with no network that fetch throws,
// which still proves it is not a store redirect.
r = await go('/apple', IPHONE).catch(() => new Response('offline', { status: 502 }));
check('/apple is not a redirect route', r.status !== 302 || !/apps\.apple\.com/.test(r.headers.get('location') || ''));

/* ---------- www → apex for the server-rendered pages ----------
 * One indexable host. The rule must not touch what the iOS universal-link
 * flow depends on: iPhone "Open the app" buttons point at www.yardscout.io
 * (/open?app=1 and /car/<key>?app=1), and Apple fetches the association
 * file from each host with no redirect allowed. */
const www = async (path, ua = DESKTOP, method = 'GET') => worker.fetch(new Request('https://www.yardscout.io' + path, { method, headers: { 'user-agent': ua } }), {}, { waitUntil() {} });
const loc = (res) => res.headers.get('location');
for (const path of ['/landed', '/landed/', '/landed/toyota', '/landed/toyota/camry', '/yards', '/junkyards', '/junkyards/texas', '/junkyards/texas/dallas', '/yard/pick-n-pull-newark', '/car/1HGFB2F50CL000001', '/prices', '/prices/pick-n-pull', '/prices/pick-your-part/pick-your-part-anaheim', '/sitemap.xml', '/sitemap-yards.xml']) {
  r = await www(path);
  check(`www${path} -> 301 apex`, r.status === 301 && loc(r) === 'https://yardscout.io' + path, `${r.status} ${loc(r)}`);
}
r = await www('/junkyards/texas?utm_source=x&utm_campaign=y');
check('www rendered page keeps its query string', r.status === 301 && loc(r) === 'https://yardscout.io/junkyards/texas?utm_source=x&utm_campaign=y', `${r.status} ${loc(r)}`);
r = await www('/landed', DESKTOP, 'HEAD');
check('www rendered page, HEAD -> 301 apex', r.status === 301 && loc(r) === 'https://yardscout.io/landed', `${r.status} ${loc(r)}`);
r = await www('/car/1HGFB2F50CL000001', IPHONE);
check('www car page on an iPhone (app did not claim it) -> 301 apex page, not a store', r.status === 301 && loc(r) === 'https://yardscout.io/car/1HGFB2F50CL000001', `${r.status} ${loc(r)}`);

// Unchanged: /open and ?app=1 answer on www with their own redirects.
r = await www('/open?app=1', IPHONE);
check('www/open?app=1 iPhone still -> App Store', r.status === 302 && /^https:\/\/apps\.apple\.com/.test(loc(r) || ''), `${r.status} ${loc(r)}`);
r = await www('/open?app=1', ANDROID);
check('www/open?app=1 Android still -> Google Play', r.status === 302 && /play\.google\.com/.test(loc(r) || ''), `${r.status} ${loc(r)}`);
r = await www('/open', DESKTOP);
check('www/open desktop still -> site (302, not the 301 rule)', r.status === 302 && loc(r) === 'https://yardscout.io/', `${r.status} ${loc(r)}`);
r = await www('/open/', IPHONE);
check('www/open/ iPhone without app=1 still -> site', r.status === 302 && loc(r) === 'https://yardscout.io/', `${r.status} ${loc(r)}`);
for (const ua of [IPHONE, ANDROID, DESKTOP]) {
  r = await www('/car/1HGFB2F50CL000001?app=1', ua);
  check(`www/car/<vin>?app=1 still -> the web app's #car= link (${ua.match(/iPhone|Android|Macintosh/)[0]})`, r.status === 302 && loc(r) === 'https://yardscout.io/#car=1HGFB2F50CL000001', `${r.status} ${loc(r)}`);
}
r = await go('/car/1HGFB2F50CL000001?app=1', IPHONE);
check('apex /car/<vin>?app=1 unchanged', r.status === 302 && loc(r) === 'https://yardscout.io/#car=1HGFB2F50CL000001', `${r.status} ${loc(r)}`);
r = await www('/app', IPHONE);
check('www/app iPhone still -> App Store', r.status === 302 && /apps\.apple\.com/.test(loc(r) || ''), `${r.status} ${loc(r)}`);
for (const path of ['/.well-known/apple-app-site-association', '/apple-app-site-association', '/.well-known/assetlinks.json']) {
  r = await www(path);
  check(`www${path} still 200 JSON, no redirect`, r.status === 200 && /application\/json/.test(r.headers.get('content-type') || '') && !loc(r), `${r.status} ${loc(r)}`);
}
r = await www('/.well-known/apple-app-site-association');
const aasa = await r.json();
check('association file still claims /car/* and /open', aasa.applinks.details[0].paths.join() === '/car/*,/open');
// ?app=1 on a rendered page that is not a car link is not part of the iOS
// flow (no button builds one); it follows the page to the apex, query kept.
r = await www('/yard/pick-n-pull-newark?app=1', IPHONE);
check('www/yard/<slug>?app=1 -> 301 apex with the query kept', r.status === 301 && loc(r) === 'https://yardscout.io/yard/pick-n-pull-newark?app=1', `${r.status} ${loc(r)}`);
// The app shell and static files keep the older catch-all www rule.
r = await www('/privacy.html');
check('www static file -> 301 apex (existing rule)', r.status === 301 && loc(r) === 'https://yardscout.io/privacy.html', `${r.status} ${loc(r)}`);
r = await www('/');
check('www home -> 301 apex (existing rule)', r.status === 301 && loc(r) === 'https://yardscout.io/', `${r.status} ${loc(r)}`);
// The apex itself never redirects a rendered page (the render's own data
// fetch is cut off here; anything but a redirect proves the point).
globalThis.fetch = async () => { throw new Error('no network in this test'); };
r = await go('/landed', DESKTOP).catch(() => new Response('offline', { status: 502 }));
check('apex rendered page is not redirected', r.status < 300 || r.status >= 400, r.status);

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
