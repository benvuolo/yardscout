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
  one(/^const PHOTO_RESIZE_HOSTS = /), fn('resizedPhotoUrl'),
  one(/^let publishedPhotoSources = /), one(/^let _photoRules = /), one(/^const PHOTO_ASPECT = /),
  one(/^let _photoEpoch = /), one(/^function photoEpochBump\(/),
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

/* Resized photos (owner decision 2026-11-16): big-file sources also publish
 * thumb / thumbLarge on an image-resizing service. Same shape as
 * junkyard_scraper.py published_photo_sources() with the thumb fields. */
const RESIZER = 'wsrv.nl';
const publishFull = (srcs) => Object.fromEntries(Object.entries(srcs)
  .filter(([, s]) => s && s.enabled === true && typeof s.label === 'string')
  .map(([k, s]) => {
    const okT = (u) => typeof u === 'string' && s.thumbHost === RESIZER && u.startsWith(`https://${RESIZER}/?url=https://${s.host}/`);
    const pats = (s.patterns || []).map(p => ({ code: p.code, card: p.card, large: p.large,
      ...(okT(p.thumb) ? { thumb: p.thumb } : {}), ...(okT(p.thumbLarge) ? { thumbLarge: p.thumbLarge } : {}) }));
    return [k, { label: s.label, host: s.host || '', onCards: s.onCards !== false,
      ...(s.heavy === true ? { heavy: true, approxKB: s.approxKB } : {}),
      ...(pats.some(p => p.thumb || p.thumbLarge) ? { thumbHost: s.thumbHost } : {}), patterns: pats }];
  })
  .filter(([, s]) => s.patterns.length));
setPublishedPhotoSources(publishFull(sources));
const R = {
  pap: 'q12/20261103123456/987654/3',
  byot: 'b0123-4567-89ab-cdef',
  ipull: 'iABC12345/front-left_1',
  usautosupply: 'mSTK123456',
  sturtevant: 'tSTK12345',
  papva: 'utt87/ABC123/photo_1',
};
const withThumb = Object.entries(sources).filter(([, s]) => s.enabled === true && s.thumbHost).map(([k]) => k).sort();
check('the sources that publish a resized copy are exactly pap, byot, ipull, usautosupply, sturtevant',
  withThumb.join() === 'byot,ipull,pap,sturtevant,usautosupply', withThumb.join());
for (const k of ['pap', 'byot', 'ipull', 'usautosupply', 'sturtevant']) {
  const i = photoInfo(R[k]);
  const inner = i && i.thumb ? new URL(i.thumb).searchParams.get('url') : '';
  check(`${k}: resized copy is on ${RESIZER}, asks for the yard's own file, and the yard's URLs are unchanged`,
    !!i && new URL(i.thumb).hostname === RESIZER && inner === i.url && new URL(i.url).hostname === sources[k].host && i.large === i.url && i.inList === true,
    JSON.stringify(i));
  const card = i ? photoBoxHtml(i, 'car-9', '2004 Honda Civic', 'card-photo', '<svg></svg>') : '';
  const esc = (u) => u.replace(/&/g, '&amp;');
  check(`${k}: a list card loads the resized copy, lazily, over the drawing`,
    card.includes(`src="${esc(i.thumb)}"`) && /loading="lazy"/.test(card) && /has-illo/.test(card) && /onerror="photoImgFail\(this\)"/.test(card) && card.includes(sources[k].label), card);
  check(`${k}: a failed resized copy falls back to the yard's own file only where that may show in lists`,
    i.onCards ? card.includes(`data-direct="${esc(i.url)}"`) : !/data-direct/.test(card), card);
}
const ip = photoInfo(R.ipull);
check('ipull: the car screen still loads the yard’s own file (no resized copy there)',
  photoBoxHtml(ip, 'car-9', 't', 'cd-photo').includes(`src="${ip.url}"`) && !/data-direct/.test(photoBoxHtml(ip, 'car-9', 't', 'cd-photo')));
const st = photoInfo(R.sturtevant);
const stBox = photoBoxHtml(st, 'car-9', 't', 'cd-photo');
check('sturtevant (4 MB originals): the car screen shows the resized large copy with no tap-to-load, and never the original on its own',
  st.heavy === true && !!st.thumbLarge && stBox.includes(`src="${st.thumbLarge.replace(/&/g, '&amp;')}"`) && !/tap to load/.test(stBox) && /data-photo-vkey="car-9"/.test(stBox) && !stBox.includes(`src="${st.large}"`), stBox);
const pv = photoInfo(R.papva);
check('papva (its host refused the service): no resized copy; its own file shows in lists as before',
  pv && pv.thumb === '' && pv.inList === pv.onCards && photoBoxHtml(pv, 'k', 't', 'card-photo').includes(`src="${pv.url}"`), JSON.stringify(pv));
const lk = photoInfo(C.pyp);
check('LKQ and the other light sources are untouched (no resized copy)', lk && lk.thumb === '' && lk.thumbLarge === '' && lk.inList === true);
// The resizer may only be one we named, and may only be asked for the source's own host.
const bad = (thumbHost, thumb) => { setPublishedPhotoSources({ x: { label: 'Photo: X', host: 'x.example', onCards: false, thumbHost, patterns: [{ code: 'x(\\d+)', card: 'https://x.example/{1}.jpg', large: 'https://x.example/{1}.jpg', thumb }] } }); return photoInfo('x12'); };
let b1 = bad('evil.example', 'https://evil.example/?url=https://x.example/{1}.jpg');
check('a resizing host we did not name is ignored (the photo behaves as before)', b1 && b1.thumb === '' && b1.inList === false && b1.url === 'https://x.example/12.jpg', JSON.stringify(b1));
b1 = bad('wsrv.nl', 'https://wsrv.nl/?url=https://other.example/{1}.jpg');
check('a resized address that asks for another host’s file is ignored', b1 && b1.thumb === '' && b1.inList === false, JSON.stringify(b1));
b1 = bad('wsrv.nl', 'http://wsrv.nl/?url=https://x.example/{1}.jpg');
check('a resized address that is not https is ignored', b1 && b1.thumb === '');
b1 = bad('wsrv.nl', 'https://wsrv.nl.evil.example/?url=https://x.example/{1}.jpg');
check('a look-alike of the resizing host is ignored', b1 && b1.thumb === '');
b1 = bad('wsrv.nl', 'https://wsrv.nl/?url=https://x.example/{1}.jpg&w=640');
check('a valid resized address makes a car-screen-only source show in lists', b1 && b1.thumb === 'https://wsrv.nl/?url=https://x.example/12.jpg&w=640' && b1.inList === true && b1.onCards === false);
// Older data (no thumb fields) behaves exactly as before: checked by every test above this block.

// Newer data without photoSources (older format, or a full takedown) clears everything.
setPublishedPhotoSources(publish(sources));
setPublishedPhotoSources(undefined);
check('data without photoSources clears every rule (no stale switch)', Object.values(C).every(c => photoInfo(c) === null));

console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
