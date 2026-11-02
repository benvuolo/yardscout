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
let r = await go('/open', ANDROID);
check('/open Android still -> Google Play', r.status === 302 && /play\.google\.com/.test(r.headers.get('location') || ''));
r = await go('/apple', IPHONE);
check('/apple is not a redirect route', r.status !== 302 || !/apps\.apple\.com/.test(r.headers.get('location') || ''));

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
