/* Unit test: chain-photo rendering in docs/app.js against the REAL remote
 * kill switch, scraper/photo_sources.json (owner decisions 2026-11-06,
 * ops/hub.md; runbook ops/yards.md "Photo takedown").
 *  - fail closed: nothing published -> no photo for any code
 *  - the app renders only through a published, enabled source's patterns
 *    (a source switched off in photo_sources.json renders nothing)
 *  - every URL must be https on that source's own published host
 *  - Army's (signed URLs that expire) is off; unknown hosts never render
 *  - Wrench-A-Part ".j": thumb on the card, full image in the viewer
 *  - LKQ: the card URL keeps the whole image (mode=max, never mode=crop)
 *  - heavy sources: never on cards; car screen shows a tap-to-load box with
 *    the size and credit; the original loads only on that tap
 * Run: node backend/test/photo_policy_unit.mjs */
import fs from 'node:fs';
import vm from 'node:vm';

const ROOT = new URL('../../', import.meta.url);
const src = fs.readFileSync(new URL('docs/app.js', ROOT), 'utf8');
const sources = JSON.parse(fs.readFileSync(new URL('scraper/photo_sources.json', ROOT), 'utf8')).sources;
const lines = src.split('\n');
const fn = (name) => {
  const i = lines.findIndex(l => l.startsWith(`function ${name}(`));
  const j = lines.findIndex((l, k) => k > i && l === '}');
  if (i < 0 || j < 0) throw new Error('missing function ' + name);
  return lines.slice(i, j + 1).join('\n');
};
const one = (re) => { const l = lines.find(x => re.test(x)); if (!l) throw new Error('missing ' + re); return l; };
const ctx = vm.createContext({ URL });
vm.runInContext([
  one(/^let publishedPhotoSources = /), one(/^let _photoRules = /), one(/^const PHOTO_ASPECT = /),
  fn('setPublishedPhotoSources'), fn('photoInfo'),
  one(/^const heavyPhotosLoaded = /), fn('photoSizeText'), fn('photoBoxHtml'),
  "function escapeHtml(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\"/g, '&quot;'); }",
  'globalThis.__t = { photoInfo, setPublishedPhotoSources, photoBoxHtml, heavyPhotosLoaded };',
].join('\n'), ctx);
const { photoInfo, setPublishedPhotoSources, photoBoxHtml, heavyPhotosLoaded } = ctx.__t;

/* Same shape junkyard_scraper.py published_photo_sources() writes. */
const publish = (srcs) => Object.fromEntries(Object.entries(srcs)
  .filter(([, s]) => s && s.enabled === true && typeof s.label === 'string')
  .map(([k, s]) => [k, { label: s.label, host: s.host || '', onCards: s.onCards !== false, ...(s.heavy === true ? { heavy: true, approxKB: s.approxKB } : {}), patterns: (s.patterns || []).map(p => ({ code: p.code, card: p.card, large: p.large })) }])
  .filter(([, s]) => s.patterns.length));

let fails = 0;
const check = (name, ok, d = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + d}`); if (!ok) fails++; };
const C = {
  pyp: 'p48213397',
  pnp: 'n0123456789abcdef0123456789abcdef',
  wapj: 'w12/1HGCM82633A004352/1730000000000.j',
  wapp: 'w12/1HGCM82633A004352/1730000000000.p',
  weller: 'https://ik.imagekit.io/rm8xun1iy5t/abc123/car_photo-1.jpg',
  ezpullit: 'https://cdn.shopify.com/s/files/1/0731/9250/5650/files/IMG_1234.jpg?v=1730000000',
  kikers: 'https://www.kikersupullit.com/inventory-feed/photos/stock-12345.jpg',
};
const ARMYS = 'https://api.yardsmartapp.com/rails/active_storage/blobs/redirect/abc--0123456789abcdef0123456789abcdef01234567/car.jpg';

check('fail closed: nothing published -> no photo for any code', Object.values(C).every(c => photoInfo(c) === null));

const pub = publish(sources);
setPublishedPhotoSources(pub);
for (const [k, code] of Object.entries(C)) {
  const key = k.startsWith('wap') ? 'wap' : k;
  const want = sources[key] && sources[key].enabled === true;
  const got = photoInfo(code);
  check(`${k}: ${want ? 'renders with its credit' : 'off in photo_sources.json, never renders'}`,
    want ? !!got && got.label === sources[key].label && got.key === key : got === null, JSON.stringify(got));
}
const j = photoInfo(C.wapj), p = photoInfo(C.wapp), l = photoInfo(C.pyp);
check('wap .j: thumb on the card, full-size in the viewer',
  j && j.url.endsWith('-front_driver-thumb.jpg') && j.large.endsWith('-front_driver.jpg'), JSON.stringify(j));
check('wap .p: one PNG for both', p && p.url === p.large && p.url.endsWith('.png'), JSON.stringify(p));
check('LKQ card URL keeps the whole image (never mode=crop)', l && !/mode=crop/.test(l.url) && !/mode=crop/.test(l.large), l && l.url);
check('Army’s (expiring signed URLs) never renders', photoInfo(ARMYS) === null);
check('unknown hosts, wrong paths, http and junk never render',
  ['https://evil.example/x.jpg', 'https://ik.imagekit.io/someoneelse/a/b.jpg', 'http://www.kikersupullit.com/inventory-feed/photos/a.jpg',
   'https://cdn.shopify.com/s/files/1/9999/files/a.jpg', 'r123456', 'p12x', 'w12/../x/1730000000000.j', ''].every(c => photoInfo(c) === null));

// onCards: a heavy source (published onCards false) is car-screen only.
const heavy = Object.entries(sources).find(([, s]) => s.enabled === true && s.onCards === false);
check('onCards false in photo_sources.json -> photoInfo marks it car-screen only; others default to cards',
  !!heavy && photoInfo(C.pyp).onCards === true && photoInfo(C.kikers).onCards === (sources.kikers.onCards !== false), heavy && heavy[0]);

// A takedown: switch one source off in the data -> it stops rendering.
const off = JSON.parse(JSON.stringify(sources)); off.wap.enabled = false;
setPublishedPhotoSources(publish(off));
check('takedown: wap off in the published data -> no wap photo, others unaffected',
  photoInfo(C.wapj) === null && !!photoInfo(C.pyp));
// A pattern whose URL leaves its own host is refused.
setPublishedPhotoSources({ pyp: { label: 'Photo: X', host: 'cdn.pypapps.com', patterns: [{ code: '^p(\\d+)$', card: 'https://evil.example/{1}.jpg', large: 'https://cdn.pypapps.com/{1}.jpg' }] } });
check('a URL off the source’s own host is refused', photoInfo('p123') === null);

// heavy: true (a yard that offers only a camera original) -> never on cards,
// a tap-to-load box on the car screen, the original loads only on that tap.
setPublishedPhotoSources(publish(sources));
const heavyKey = Object.entries(sources).find(([, s]) => s.enabled === true && s.heavy === true);
check('photo_sources.json publishes at least one heavy source', !!heavyKey);
if (heavyKey) {
  const [hk, hs] = heavyKey;
  const code = hk === 'sturtevant' ? 'tSTK12345' : null;
  const hi = code && photoInfo(code);
  check(`${hk}: heavy, never on cards, size published`, hi && hi.heavy === true && hi.onCards === false && hi.approxKB === hs.approxKB, JSON.stringify(hi));
  const box = hi ? photoBoxHtml(hi, 'car-1', '2004 Honda Civic', 'cd-photo') : '';
  const mb = (hs.approxKB / 1000).toFixed(1).replace(/\.0$/, '');
  check(`${hk}: car screen shows "Photo available — tap to load (~${mb} MB)" with the credit, no image`,
    /Photo available &mdash; tap to load \(~[\d.]+\u00a0MB\)/.test(box) && box.includes(`~${mb}\u00a0MB`) && box.includes(hs.label) && !/<img/.test(box) && /data-photo-load="car-1"/.test(box) && !/data-photo-vkey/.test(box), box);
  heavyPhotosLoaded.add('car-1');
  const loaded = photoBoxHtml(hi, 'car-1', '2004 Honda Civic', 'cd-photo');
  check(`${hk}: after the tap, the box loads the original (large) and opens the viewer as usual`,
    loaded.includes(`src="${hi.large}"`) && /data-photo-vkey="car-1"/.test(loaded) && !/loading="lazy"/.test(loaded) && loaded.includes(hs.label), loaded);
  heavyPhotosLoaded.clear();
}
setPublishedPhotoSources({ x: { label: 'Photo: X', host: 'x.example', onCards: true, heavy: true, patterns: [{ code: 'x(\\d+)', card: 'https://x.example/{1}.jpg', large: 'https://x.example/{1}.jpg' }] } });
const hx = photoInfo('x12');
check('heavy overrides onCards true; no approxKB -> "large file"', hx && hx.onCards === false && hx.approxKB === null && photoBoxHtml(hx, 'k', 't').includes('tap to load (large file)'), JSON.stringify(hx));
setPublishedPhotoSources({ x: { label: 'Photo: X', host: 'x.example', heavy: 'yes', patterns: [{ code: 'x(\\d+)', card: 'https://x.example/{1}.jpg', large: 'https://x.example/{1}.jpg' }] } });
check('heavy missing or not exactly true -> not heavy (normal photo)', photoInfo('x12') && photoInfo('x12').heavy === false && /<img/.test(photoBoxHtml(photoInfo('x12'), 'k', 't')));

// Newer data without photoSources (older format, or a full takedown) clears everything.
setPublishedPhotoSources(publish(sources));
setPublishedPhotoSources(undefined);
check('data without photoSources clears every rule (no stale switch)', Object.values(C).every(c => photoInfo(c) === null));

console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
