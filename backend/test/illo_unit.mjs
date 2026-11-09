/* Unit test: the vehicle illustration for cards with no list photo
 * (docs/app.js). The card's photo slot shows:
 *  - a real photo when its source may show on cards (drawing under it, so a
 *    failed image leaves the drawing, not a hole);
 *  - otherwise a drawing: body style from the car's published "body" extra
 *    (one of 8 classes; anything else or missing = generic car, never a guess
 *    from the name), painted the listed colour (unknown = neutral), with the
 *    year/make/model; badged "Photo on car page" when a light car-screen-only
 *    source has a photo, "Photo at yard · tap to load" for a heavy source.
 * Run: node backend/test/illo_unit.mjs */
import fs from 'node:fs';
import vm from 'node:vm';

const lines = fs.readFileSync(new URL('../../docs/app.js', import.meta.url), 'utf8').split('\n');
const block = (start, end) => {
  const i = lines.findIndex(l => l.startsWith(start));
  const j = lines.findIndex((l, k) => k > i && l === end);
  if (i < 0 || j < 0) throw new Error('missing ' + start);
  return lines.slice(i, j + 1).join('\n');
};
const fn = (name) => block(`function ${name}(`, '}');
const one = (re) => { const l = lines.find(x => re.test(x)); if (!l) throw new Error('missing ' + re); return l; };
const ctx = vm.createContext({ URL });
vm.runInContext([
  "function escapeHtml(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\"/g, '&quot;'); }",
  'var __ex = {}; function extrasFor(v) { return __ex[v.id] || null; }',
  one(/^let publishedPhotoSources = /), one(/^let _photoRules = /), one(/^const PHOTO_ASPECT = /),
  fn('setPublishedPhotoSources'), fn('photoInfo'), one(/^const heavyPhotosLoaded = /), fn('photoSizeText'), fn('photoBoxHtml'),
  one(/^let extraIdx = /), fn('setExtraFields'), one(/^const ILLO_BODIES = /), block('const PAINTS = [', '];'),
  fn('paintHex'), fn('illoBody'), fn('illoBoxHtml'), one(/^const ICON_CAMERA = /), fn('cardPhotoHtml'), fn('illoSvgHtml'),
  'globalThis.__t = { paintHex, illoBody, cardPhotoHtml, setPublishedPhotoSources, setExtraFields, set: (o) => { __ex = o; } };',
].join('\n'), ctx);
const T = ctx.__t;

let fails = 0;
const check = (name, ok, d = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + d}`); if (!ok) fails++; };

check('paint: yard spellings map to a colour', ['White', '[White]', 'Field-Black', 'Silver', 'Grey', 'Charcoal', 'Maroon', 'Champagne'].every(c => /^#[0-9A-F]{6}$/.test(T.paintHex(c))));
check('paint: unknown, other, blank -> neutral (no colour)', ['', 'Unknown', 'Other', 'Multi', null, 'Zebra'].every(c => T.paintHex(c) === ''));
check('paint: charcoal is not plain gray, champagne is not gold', T.paintHex('Charcoal') !== T.paintHex('Gray') && T.paintHex('Champagne') !== T.paintHex('Gold'));
check('body: the 8 classes pass through', ['sedan', 'coupe', 'hatchback', 'wagon', 'suv', 'pickup', 'van', 'convertible'].every(b => T.illoBody(['', '', '', '', '', b]) === b));
check('body: missing, blank or anything else -> generic car', [null, [], ['', '', '', '', '', ''], ['', '', '', '', '', 'Sport Utility Vehicle (SUV)'], ['', '', '', '', '', 'truck']].every(e => T.illoBody(e) === 'car'));
T.setExtraFields(['photo', 'color', 'engine', 'trans', 'transSrc', 'notes', 'body']);
check('body is read by name from extraFields', T.illoBody(['', '', '', '', '', 'x', 'van']) === 'van');
T.setExtraFields(['photo', 'color', 'engine', 'trans', 'transSrc', 'body']);

T.setPublishedPhotoSources({
  pyp: { label: 'Photo: LKQ', host: 'cdn.pypapps.com', patterns: [{ code: 'p(\\d+)', card: 'https://cdn.pypapps.com/{1}.jpg', large: 'https://cdn.pypapps.com/{1}L.jpg' }] },
  side: { label: 'Photo: Side', host: 'side.example', onCards: false, patterns: [{ code: 's(\\d+)', card: 'https://side.example/{1}.jpg', large: 'https://side.example/{1}.jpg' }] },
  big: { label: 'Photo: Big', host: 'big.example', heavy: true, approxKB: 3800, patterns: [{ code: 'b(\\d+)', card: 'https://big.example/{1}.jpg', large: 'https://big.example/{1}.jpg' }] },
});
const car = (id) => ({ id, year: 2014, make: 'Nissan', model: 'Rogue <S>' });
T.set({ 1: ['p123', 'Blue', '', '', '', 'suv'], 2: ['', 'Red', '', '', '', 'pickup'], 3: ['b77', 'White', '', '', '', 'sedan'], 4: ['s9', '', '', '', '', ''] });
let h = T.cardPhotoHtml(car(1), 'k1');
check('card with an on-card photo: the real photo, drawing underneath', /<img src="https:\/\/cdn\.pypapps\.com\/123\.jpg"/.test(h) && /has-illo/.test(h) && /#illo-suv/.test(h) && !/illo-badge/.test(h), h);
h = T.cardPhotoHtml(car(2), 'k2');
check('no photo: drawing, body style, paint, name (escaped), no badge', /photo-illo/.test(h) && /#illo-pickup/.test(h) && /--paint:#B3261E/.test(h) && /2014 Nissan Rogue &lt;S&gt;/.test(h) && !/<img/.test(h) && !/illo-badge/.test(h), h);
h = T.cardPhotoHtml(car(3), 'k3');
check('heavy source: drawing + "Photo at yard · tap to load" badge, the image is never on the card', /photo-illo/.test(h) && /Photo at yard &middot; tap to load/.test(h) && !/Photo on car page/.test(h) && !/<img/.test(h) && !/big\.example/.test(h), h);
h = T.cardPhotoHtml(car(4), 'k4');
check('onCards false (light) source: drawing + "Photo on car page" badge; unknown body and colour: generic, neutral', /photo-illo/.test(h) && /Photo on car page/.test(h) && !/Photo at yard/.test(h) && !/<img/.test(h) && /#illo-car"/.test(h) && !/--paint/.test(h), h);
T.set({});
h = T.cardPhotoHtml(car(5), 'k5');
check('extras not loaded yet: generic neutral drawing in the same box', /photo-illo/.test(h) && /#illo-car"/.test(h) && !/--paint/.test(h) && /card-photo/.test(h), h);
check('the drawing is labelled as a drawing for screen readers', /role="img" aria-label="Drawing of a 2014 Nissan Rogue/.test(h), h);

console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
