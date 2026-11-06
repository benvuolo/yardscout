/* Unit test: chain-photo policy in docs/app.js (owner decision 2026-11-06,
 * ops/hub.md; sources from ops/yards.md "2026-11-06 vehicle photos").
 *  - fail closed: no published photoSources -> no photo for any source
 *  - each source needs BOTH its app flag and photoSources[key] === true
 *  - only the listed hosts/path prefixes render; Row52 "r" codes,
 *    api.yardsmartapp.com and any other host never do
 *  - Wrench-A-Part ".j" codes give a thumb for the card and the full image
 *    for the viewer; ".p" codes use the one PNG for both
 * Run: node backend/test/photo_policy_unit.mjs */
import fs from 'node:fs';
import vm from 'node:vm';

const src = fs.readFileSync(new URL('../../docs/app.js', import.meta.url), 'utf8');
const lines = src.split('\n');
const block = (startRe) => {
  const i = lines.findIndex(l => startRe.test(l));
  if (i < 0) throw new Error('missing ' + startRe);
  const j = lines.findIndex((l, k) => k > i && /^};?$/.test(l));
  return lines.slice(i, j + 1).join('\n');
};
const one = (re) => { const l = lines.find(x => re.test(x)); if (!l) throw new Error('missing ' + re); return l; };
const code = [
  block(/^const PHOTO_SOURCES = \{/),
  one(/^let publishedPhotoSources = /),
  block(/^function setPublishedPhotoSources\(/),
  lines.slice(lines.findIndex(l => /^const photoOn = /.test(l)), lines.findIndex(l => /^const photoOn = /.test(l)) + 2).join('\n'),
  block(/^function photoInfo\(/),
  'globalThis.__t = { photoInfo, setPublishedPhotoSources, PHOTO_SOURCES };',
].join('\n');
const ctx = vm.createContext({ URL, encodeURIComponent });
vm.runInContext(code, ctx);
const { photoInfo, setPublishedPhotoSources } = ctx.__t;

let fails = 0;
const check = (name, ok, d = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + d}`); if (!ok) fails++; };
const PYP = 'p12345-678';
const WAPJ = 'w12/1HGCM82633A004352/1730000000000.j';
const WAPP = 'w12/1HGCM82633A004352/1730000000000.p';
const KIK = 'https://www.kikersupullit.com/uploads/car123.jpg';
const WEL = 'https://ik.imagekit.io/rm8xun1iy5t/cars/abc.jpg';
const PAS = 'https://cdn.shopify.com/s/files/1/0731/9250/5650/files/car.jpg';

check('fail closed: nothing published -> no photo for any source',
  [PYP, WAPJ, WAPP, KIK, WEL, PAS].every(c => photoInfo(c) === null));
setPublishedPhotoSources({ pyp: true });
check('published pyp only -> pyp renders, the others stay off',
  !!photoInfo(PYP) && [WAPJ, KIK, WEL, PAS].every(c => photoInfo(c) === null));
setPublishedPhotoSources({ pyp: true, wap: true, kikers: true, weller: true, pasco: true });
const j = photoInfo(WAPJ), p = photoInfo(WAPP);
check('wap .j: card thumb + full-size viewer image on the GCS bucket',
  j && j.url.endsWith('-front_driver-thumb.jpg') && j.large.endsWith('-front_driver.jpg')
  && j.url.startsWith('https://storage.googleapis.com/wrench-car-photos/v1%2F12%2F1HGCM82633A004352%2F1730000000000'), JSON.stringify(j));
check('wap .p: one PNG for both', p && p.url === p.large && p.url.endsWith('1730000000000.png'), JSON.stringify(p));
check('labels credit the chain', photoInfo(KIK).label === 'Photo: Kiker’s U-Pull-It'
  && photoInfo(WEL).label === 'Photo: Weller Self Serve' && photoInfo(PAS).label === 'Photo: Pasco EZ Pull It'
  && photoInfo(PYP).label === 'Photo: LKQ Pick Your Part' && j.label === 'Photo: Wrench-A-Part');
check('never: Row52 r codes, yardsmart, other hosts, wrong path, http',
  [ 'r123456', 'https://api.yardsmartapp.com/x.jpg', 'https://cdn.row52.com/x.jpg',
    'https://ik.imagekit.io/someoneelse/x.jpg', 'https://cdn.shopify.com/s/files/1/9999/x.jpg',
    'http://www.kikersupullit.com/x.jpg', 'https://evil.example/www.kikersupullit.com/x.jpg',
    'w12/../evil/1.j', ''].every(c => photoInfo(c) === null));
setPublishedPhotoSources({ pyp: true, wap: false, kikers: true, weller: true, pasco: true });
check('a published false turns one chain off (remote kill switch)', photoInfo(WAPJ) === null && !!photoInfo(KIK));
setPublishedPhotoSources({ pyp: 'yes', wap: 1 });
check('only literal true counts', photoInfo(PYP) === null && photoInfo(WAPJ) === null);

console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
