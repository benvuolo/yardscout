/* Unit test: how the app reads a watch from a share-page arrival
 * (docs/app.js, 2026-11-12): the #watch=<make>|<model>|<years> link shape,
 * the referrer of our own server-rendered pages, and the make slug that must
 * match the site worker's. Loads the real functions out of docs/app.js.
 * Run: node backend/test/share_watch_unit.mjs */
import fs from 'node:fs';
import vm from 'node:vm';
import { slugify } from '../site-proxy/src/share.js';

const src = fs.readFileSync(new URL('../../docs/app.js', import.meta.url), 'utf8');
const lines = src.split('\n');
const fn = (name) => {
  const a = lines.findIndex(l => l.startsWith(`function ${name}(`));
  const b = lines.findIndex((l, i) => i > a && l === '}');
  return a < 0 || b < 0 ? null : lines.slice(a, b + 1).join('\n');
};
let failures = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + detail}`); if (!ok) failures++; };

const ctx = { URL };
vm.createContext(ctx);
for (const n of ['parseWatchHash', 'shareReferrerIntent', 'shareSlug']) check(`app.js has function ${n}`, !!fn(n));
new vm.Script(['parseWatchHash', 'shareReferrerIntent', 'shareSlug'].map(fn).join('\n') + '\nglobalThis.__api = { parseWatchHash, shareReferrerIntent, shareSlug };').runInContext(ctx);
const { parseWatchHash: P, shareReferrerIntent: R, shareSlug } = ctx.__api;
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

check('#watch=make|model', eq(P('#watch=Chevrolet|Equinox'), { make: 'Chevrolet', model: 'Equinox', yrMin: null, yrMax: null }), JSON.stringify(P('#watch=Chevrolet|Equinox')));
check('#watch= url-encoded, with a year range', eq(P('#watch=' + encodeURIComponent('Mercedes-Benz|Sprinter 2500|2007-2011')), { make: 'Mercedes-Benz', model: 'Sprinter 2500', yrMin: 2007, yrMax: 2011 }));
check('#watch= one year means that year only', eq(P('#watch=Toyota|Camry|2009'), { make: 'Toyota', model: 'Camry', yrMin: 2009, yrMax: 2009 }), JSON.stringify(P('#watch=Toyota|Camry|2009')));
check('#watch= open-ended years', eq(P('#watch=Toyota|Camry|2009-'), { make: 'Toyota', model: 'Camry', yrMin: 2009, yrMax: null }) && eq(P('#watch=Toyota|Camry|-2011'), { make: 'Toyota', model: 'Camry', yrMin: null, yrMax: 2011 }));
check('#watch= make only', eq(P('#watch=Toyota'), { make: 'Toyota', model: '', yrMin: null, yrMax: null }));
check('#watch= reversed or junk years are dropped, the car is kept', eq(P('#watch=Toyota|Camry|2011-2007'), { make: 'Toyota', model: 'Camry', yrMin: 2011, yrMax: null }) && eq(P('#watch=Toyota|Camry|soon'), { make: 'Toyota', model: 'Camry', yrMin: null, yrMax: null }),
  JSON.stringify([P('#watch=Toyota|Camry|2011-2007'), P('#watch=Toyota|Camry|soon')]));
check('#watch= with no make is not a watch', P('#watch=') === null && P('#watch=|Camry') === null && P('#tab=alerts') === null && P('') === null);
{
  const x = P('#watch=' + encodeURIComponent('<img src=x>|"Camry"'));
  check('#watch= markup characters are stripped from the names', !!x && !/[<>"]/.test(x.make + x.model) && x.model === 'Camry', JSON.stringify(x));
}
check('#watch= stops at the next & part', eq(P('#watch=Honda|Civic&x=1'), { make: 'Honda', model: 'Civic', yrMin: null, yrMax: null }));

const O = 'https://yardscout.io';
check('referrer: our car page gives the car key', eq(R('https://yardscout.io/car/19UUA8F54DA000651', O), { kind: 'car', key: '19UUA8F54DA000651' }));
check('referrer: a car page by numeric id', eq(R('https://yardscout.io/car/7962049', O), { kind: 'car', key: '7962049' }));
check('referrer: our make page gives the make slug', eq(R('https://yardscout.io/landed/mercedes-benz', O), { kind: 'make', slug: 'mercedes-benz' }));
check('referrer: a yard page or /landed itself is one of ours, with no car', eq(R('https://yardscout.io/yard/pick-n-pull-fresno', O), { kind: 'page' }) && eq(R('https://yardscout.io/landed', O), { kind: 'page' }));
check('referrer: another site, or none, tells us nothing', R('https://www.reddit.com/car/19UUA8F54DA000651', O) === null && R('', O) === null && R(undefined, O) === null);
check('referrer: a strange car path is not treated as a key', eq(R('https://yardscout.io/car/a/b', O), { kind: 'page' }) && eq(R('https://yardscout.io/car/' + 'x'.repeat(40), O), { kind: 'page' }));

const makes = Object.keys(JSON.parse(fs.readFileSync(new URL('../../docs/data/models.json', import.meta.url), 'utf8')).makes);
const off = makes.filter(mk => shareSlug(mk) !== slugify(mk));
check(`the app's make slug equals the site worker's for all ${makes.length} makes in the scan`, makes.length > 40 && off.length === 0, off.join(', '));
check('...and makes do not collide on a slug', new Set(makes.map(shareSlug)).size === makes.length);

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
