// GET /geo: the visitor's approximate area for the first view.
//   node backend/site-proxy/test/geo_unit.mjs
import { geoAnswer, geoResponse } from '../src/geo.js';
import worker from '../src/index.js';

let pass = 0, fail = 0;
const ok = (c, msg, extra) => { if (c) { pass++; console.log('  ok   ' + msg); } else { fail++; console.log('  FAIL ' + msg + (extra !== undefined ? '  -> ' + JSON.stringify(extra).slice(0, 300) : '')); } };

let a = geoAnswer({ latitude: '38.58157', longitude: '-121.49440', city: 'Sacramento', regionCode: 'CA', country: 'US', postalCode: '95814' });
ok(a.ok && a.lat === 38.6 && a.lng === -121.5, 'coordinates are rounded to one decimal', a);
ok(a.city === 'Sacramento' && a.region === 'CA' && a.country === 'US', 'city, region and country come back', a);
ok(!('postalCode' in a) && !('postal' in a) && !('ip' in a) && Object.keys(a).sort().join() === 'city,country,lat,lng,ok,region', 'nothing else is returned (no postal code, no address)', Object.keys(a));

a = geoAnswer({ latitude: '51.05', longitude: '-114.07', city: 'Calgary', regionCode: 'AB', country: 'CA' });
ok(a.ok && a.region === 'AB', 'Canada is answered');
ok(geoAnswer({ latitude: '48.85', longitude: '2.35', city: 'Paris', country: 'FR' }).ok === false, 'outside the US and Canada: no guess');
ok(geoAnswer(undefined).ok === false && geoAnswer({}).ok === false && geoAnswer({ country: 'US' }).ok === false, 'no location on the request: no guess');
ok(geoAnswer({ latitude: 'abc', longitude: '-100', country: 'US' }).ok === false && geoAnswer({ latitude: '95', longitude: '-100', country: 'US' }).ok === false, 'bad coordinates: no guess');
a = geoAnswer({ latitude: '40', longitude: '-100', city: '<script>alert(1)</script>"x', regionCode: 'nebraska', country: 'us' });
ok(a.ok && !/[<>"']/.test(a.city) && a.region.length <= 3 && a.country === 'US', 'city and region are cleaned and clipped', a);
a = geoAnswer({ latitude: '40', longitude: '-100', country: 'US' });
ok(a.ok && a.city === '' && a.region === '', 'a location without a city still answers (the app labels it by the nearest yard)', a);

const r = geoResponse({ cf: { latitude: '38.58', longitude: '-121.49', city: 'Sacramento', regionCode: 'CA', country: 'US' } });
ok(r.headers.get('cache-control') === 'no-store', 'the answer is never cached');
ok(r.headers.get('access-control-allow-origin') === '*', 'the apps can read it');
ok((await r.json()).city === 'Sacramento', 'the response body is the answer');

// Through the Worker's own router.
const g = new Request('https://yardscout.io/geo');
Object.defineProperty(g, 'cf', { value: { latitude: '37.2', longitude: '-93.3', city: 'Springfield', regionCode: 'MO', country: 'US' } });
const out = await worker.fetch(g, {});
const body = await out.json();
ok(out.status === 200 && body.ok && body.city === 'Springfield' && body.lat === 37.2, 'yardscout.io/geo answers through the Worker', body);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
