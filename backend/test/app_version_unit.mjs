/* Unit test for src/app_version.js — fetch and KV are stubbed. Run: node test/app_version_unit.mjs */
import { appVersionInfo, handleAppVersion } from '../src/app_version.js';

let failures = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + detail}`); if (!ok) failures++; };
const H = 3600_000, NOW = Date.parse('2026-11-01T12:00:00Z');
let site = {}, itunes = { results: [{ version: '1.12.9' }] }, itunesCalls = 0, siteDown = false, itunesDown = false;
globalThis.fetch = async (url) => {
  url = String(url);
  if (url.includes('itunes.apple.com')) { itunesCalls++; if (itunesDown) throw new Error('down'); return new Response(JSON.stringify(itunes)); }
  if (url.endsWith('/app-version.json')) { if (siteDown) return new Response('nope', { status: 500 }); return new Response(JSON.stringify(site)); }
  throw new Error('unexpected ' + url);
};
const kv = new Map();
const env = { ENTITLEMENTS: { get: async (k) => kv.get(k) ?? null, put: async (k, v) => { kv.set(k, v); } } };

site = { min: { ios: '1.12.8', android: '' }, message: 'Please update', android: { latest: '1.12.9', releasedAt: new Date(NOW - 10 * H).toISOString() } };
let r = await appVersionInfo(env, 'ios', NOW);
check('ios latest from Apple lookup', r.latest === '1.12.9', JSON.stringify(r));
check('ios min from file', r.min === '1.12.8');
check('message passed through', r.message === 'Please update');
check('ios store url', /apps\.apple\.com\/app\/id6817126581/.test(r.storeUrl));
await appVersionInfo(env, 'ios', NOW + 10 * 60_000);
check('Apple lookup cached for an hour', itunesCalls === 1, `calls=${itunesCalls}`);
await appVersionInfo(env, 'ios', NOW + 2 * H);
check('Apple lookup refreshed after an hour', itunesCalls === 2, `calls=${itunesCalls}`);

r = await appVersionInfo(env, 'android', NOW);
check('android latest held back during Play review (10 h after upload)', r.latest === null, JSON.stringify(r));
check('android empty min = none', r.min === null);
r = await appVersionInfo(env, 'android', NOW + 40 * H);
check('android latest shown 48 h after upload', r.latest === '1.12.9', JSON.stringify(r));

site = { min: { ios: 'not-a-version' } };
r = await appVersionInfo(env, 'ios', NOW);
check('junk min ignored', r.min === null);

siteDown = true; itunesDown = true; kv.clear();
r = await appVersionInfo(env, 'ios', NOW);
check('everything down → no latest, no min (never blocks)', r.latest === null && r.min === null, JSON.stringify(r));

const resp = await handleAppVersion(new Request('https://x/v1/app-version?platform=windows'), env);
check('bad platform → 400', resp.status === 400);
const ok = await handleAppVersion(new Request('https://x/v1/app-version?platform=ios'), env);
check('handler 200 + cacheable', ok.status === 200 && /max-age=300/.test(ok.headers.get('cache-control') || ''));

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
