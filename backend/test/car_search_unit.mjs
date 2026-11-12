/* Unit test: the Cars-tab car search (docs/app.js CAR SEARCH).
 *   - parseCarsHash: #cars=<make>|<model>|<years>, parsed and sanitised the
 *     way parseWatchHash parses #watch= (same inputs, same results)
 *   - carSearchMatch: spelling-insensitive suggestions ("xterra", "4 runner",
 *     "f150", "cr v", "chevy silverado"), best match first
 *   - carSearchClearMatch: what Enter may pick (one result, or one exact)
 *   - carSearchFind: the entry a #cars= link names, or null
 * Run: node backend/test/car_search_unit.mjs */
import fs from 'node:fs';
import vm from 'node:vm';

const src = fs.readFileSync(new URL('../../docs/app.js', import.meta.url), 'utf8');
const lines = src.split('\n');
const fn = (name) => {
  const i = lines.findIndex(l => l.startsWith(`function ${name}(`));
  const j = lines.findIndex((l, k) => k > i && l === '}');
  if (i < 0 || j < 0) throw new Error('missing function ' + name);
  return lines.slice(i, j + 1).join('\n');
};
const names = ['carSearchSquash', 'parseCarsHash', 'parseWatchHash', 'carSearchMatch', 'carSearchClearMatch', 'carSearchFind'];
const ctx = vm.createContext({});
vm.runInContext([...names.map(fn), `globalThis.__t = { ${names.join(', ')} };`].join('\n'), ctx);
const { carSearchSquash: squash, parseCarsHash: parse, parseWatchHash, carSearchMatch: match,
  carSearchClearMatch: clearMatch, carSearchFind: find } = ctx.__t;

let fails = 0;
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const check = (name, ok, d = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : '  ' + d}`); if (!ok) fails++; };
const same = (name, got, want) => check(name, eq(got, want), `got ${JSON.stringify(got)} want ${JSON.stringify(want)}`);

/* ---- parseCarsHash ---- */
same('make, model, range', parse('#cars=Nissan|Xterra|2005-2015'), { make: 'Nissan', model: 'Xterra', yrMin: 2005, yrMax: 2015 });
same('make only', parse('#cars=Nissan'), { make: 'Nissan', model: '', yrMin: null, yrMax: null });
same('make + model, no years', parse('#cars=Toyota|4Runner'), { make: 'Toyota', model: '4Runner', yrMin: null, yrMax: null });
same('percent-encoded (pipes and spaces, as chat apps send it)', parse('#cars=Land%20Rover%7CRange%20Rover%7C2003-2012'), { make: 'Land Rover', model: 'Range Rover', yrMin: 2003, yrMax: 2012 });
same('plus as a space', parse('#cars=Land+Rover|Discovery'), { make: 'Land Rover', model: 'Discovery', yrMin: null, yrMax: null });
same('open-ended from', parse('#cars=Nissan|Xterra|2005-'), { make: 'Nissan', model: 'Xterra', yrMin: 2005, yrMax: null });
same('open-ended to', parse('#cars=Nissan|Xterra|-2009'), { make: 'Nissan', model: 'Xterra', yrMin: null, yrMax: 2009 });
same('single year', parse('#cars=Nissan|Xterra|2007'), { make: 'Nissan', model: 'Xterra', yrMin: 2007, yrMax: 2007 });
same('reversed range drops the end', parse('#cars=Nissan|Xterra|2015-2005'), { make: 'Nissan', model: 'Xterra', yrMin: 2015, yrMax: null });
same('junk years ignored', parse('#cars=Nissan|Xterra|abc'), { make: 'Nissan', model: 'Xterra', yrMin: null, yrMax: null });
same('out-of-range years ignored', parse('#cars=Nissan|Xterra|0001-9999'), { make: 'Nissan', model: 'Xterra', yrMin: null, yrMax: null });
same('markup and control characters stripped', parse('#cars=%3Cb%3ENissan%3C%2Fb%3E|Xt%22erra%0A'), { make: 'bNissan/b', model: 'Xterra', yrMin: null, yrMax: null });
check('long values capped at 60 characters', parse('#cars=' + 'A'.repeat(200) + '|' + 'B'.repeat(200)).make.length === 60);
check('truncated escape does not throw', (() => { try { return parse('#cars=Nissan%E0%A4%A|Xterra').make.length > 0; } catch (e) { return false; } })());
same('empty make: null', parse('#cars=|Xterra'), null);
same('empty: null', parse('#cars='), null);
same('no #cars: null', parse('#car=1N6ED27Y21C123456'), null);
same('#car= share link is not a #cars= link', parse('#car=abc'), null);
same('#watch= is not a #cars= link', parse('#watch=Nissan|Xterra'), null);
same('a following &param ends the value', parse('#cars=Nissan|Xterra&x=1'), { make: 'Nissan', model: 'Xterra', yrMin: null, yrMax: null });
same('null / undefined hash', [parse(null), parse(undefined)], [null, null]);
// Mirrors parseWatchHash on the same values.
for (const v of ['Nissan|Xterra|2005-2015', 'Nissan', 'Ford|F-150|-2009', 'Nissan|Xterra|2015-2005', 'Honda|Civic|abc', 'Land%20Rover%7CDefender', '%3Cx%3E|y|2007']) {
  same(`same result as #watch= for "${v}"`, parse('#cars=' + v), parseWatchHash('#watch=' + v));
}

/* ---- normaliser ---- */
same('squash: case, spaces, punctuation', ['4 Runner', 'F-150', 'CR-V', 'cr v', 'Mercedes-Benz'].map(squash), ['4runner', 'f150', 'crv', 'crv', 'mercedesbenz']);

/* ---- carSearchMatch ---- */
// alts: the make's nicknames, on every entry of the make (as carSearchIndex builds them).
const ALTS = { Chevrolet: ['chevy', 'chev'] };
const E = (make, model, n) => ({ make, model, n, alts: ALTS[make] || [] });
const entries = [
  E('Nissan', '', 900), E('Toyota', '', 1200), E('Ford', '', 1500), E('Honda', '', 1400), E('Chevrolet', '', 1300), E('Ram', '', 200),
  E('Nissan', 'Xterra', 41), E('Nissan', 'Frontier', 60), E('Nissan', 'Altima', 300), E('Nissan', 'Pathfinder', 80),
  E('Toyota', '4Runner', 56), E('Toyota', 'Tacoma', 90), E('Toyota', 'Camry', 400),
  E('Ford', 'F-150', 220), E('Ford', 'F-150 Heritage', 4), E('Ford', 'F-250 Super Duty', 30), E('Ford', 'Ranger', 70),
  E('Honda', 'CR-V', 180), E('Honda', 'Civic', 500), E('Honda', 'Civic del Sol', 3), E('Honda', 'CR-Z', 2),
  E('Chevrolet', 'Silverado 1500', 250), E('Chevrolet', 'Cruze', 120),
  E('Dodge', 'Ram 1500', 150),
];
const labels = (rs) => rs.map(r => (r.make + ' ' + r.model).trim());
const top = (q) => labels(match(entries, q))[0];
same('"xterra" -> Nissan Xterra only', labels(match(entries, 'xterra')), ['Nissan Xterra']);
same('"XTERRA" (case) -> Nissan Xterra', top('XTERRA'), 'Nissan Xterra');
same('"  xterra " (spaces) -> Nissan Xterra', top('  xterra '), 'Nissan Xterra');
same('"x-terra" (punctuation) -> Nissan Xterra', top('x-terra'), 'Nissan Xterra');
same('"4runner" -> Toyota 4Runner', top('4runner'), 'Toyota 4Runner');
same('"4 runner" -> Toyota 4Runner', top('4 runner'), 'Toyota 4Runner');
same('"f150" -> Ford F-150 first', top('f150'), 'Ford F-150');
same('"f-150" -> Ford F-150 first, Heritage after', labels(match(entries, 'f-150')), ['Ford F-150', 'Ford F-150 Heritage']);
same('"cr v" -> Honda CR-V', top('cr v'), 'Honda CR-V');
same('"crv" -> Honda CR-V', top('crv'), 'Honda CR-V');
check('"cr v" does not drag in the Cruze', !labels(match(entries, 'cr v')).includes('Chevrolet Cruze'), labels(match(entries, 'cr v')).join(', '));
same('"nissan xterra" -> Nissan Xterra', top('nissan xterra'), 'Nissan Xterra');
same('"xterra nissan" -> Nissan Xterra', top('xterra nissan'), 'Nissan Xterra');
same('"chevy silverado" (make nickname) -> Chevrolet Silverado 1500', top('chevy silverado'), 'Chevrolet Silverado 1500');
same('"nissan" -> the whole make first', top('nissan'), 'Nissan');
check('"nissan" also lists Nissan models', labels(match(entries, 'nissan')).includes('Nissan Xterra'));
same('"civic" -> Civic before Civic del Sol', labels(match(entries, 'civic')), ['Honda Civic', 'Honda Civic del Sol']);
same('"tac" (prefix) -> Toyota Tacoma', top('tac'), 'Toyota Tacoma');
same('"frontier" -> Nissan Frontier', top('frontier'), 'Nissan Frontier');
same('"silverado" -> Chevrolet Silverado 1500 (contains)', top('silverado'), 'Chevrolet Silverado 1500');
same('"super duty" -> Ford F-250 Super Duty (contains)', top('super duty'), 'Ford F-250 Super Duty');
same('"ram": make Ram, then Dodge Ram 1500', labels(match(entries, 'ram')).slice(0, 2), ['Ram', 'Dodge Ram 1500']);
same('"toyota 4 runner" -> Toyota 4Runner', top('toyota 4 runner'), 'Toyota 4Runner');
same('"4runner toyota" -> Toyota 4Runner', top('4runner toyota'), 'Toyota 4Runner');
same('"zzz" -> nothing', match(entries, 'zzz'), []);
same('empty / punctuation only -> nothing', [match(entries, ''), match(entries, '  - ')], [[], []]);
check('a limit caps the list', match(entries, 'c', 3).length === 3);
check('default limit is 8', match(entries, 'r').length <= 8);
same('no entries -> nothing', match(null, 'xterra'), []);
same('within a tier, most cars first', labels(match(entries, 'f')).slice(0, 4), ['Ford', 'Ford F-150', 'Nissan Frontier', 'Ford F-250 Super Duty']);

/* ---- carSearchClearMatch ---- */
same('Enter on "xterra" picks Nissan Xterra', clearMatch(match(entries, 'xterra')) && labels([clearMatch(match(entries, 'xterra'))]), ['Nissan Xterra']);
same('Enter on "civic" picks Civic (the one exact)', labels([clearMatch(match(entries, 'civic'))]), ['Honda Civic']);
same('Enter on "f150" picks F-150 (the one exact)', labels([clearMatch(match(entries, 'f150'))]), ['Ford F-150']);
same('Enter on "cr" picks nothing (CR-V or CR-Z?)', clearMatch(match(entries, 'cr')), null);
same('Enter on "nissan" picks the whole make', labels([clearMatch(match(entries, 'nissan'))]), ['Nissan']);
same('Enter with no results picks nothing', clearMatch(match(entries, 'zzz')), null);

/* ---- carSearchFind ---- */
const f = (mk, md) => { const r = find(entries, mk, md); return r ? (r.make + ' ' + r.model).trim() : null; };
same('find Nissan|Xterra', f('Nissan', 'Xterra'), 'Nissan Xterra');
same('find nissan|xterra (case)', f('nissan', 'xterra'), 'Nissan Xterra');
same('find Toyota|4 Runner (spacing)', f('Toyota', '4 Runner'), 'Toyota 4Runner');
same('find Ford|F150 (punctuation)', f('Ford', 'F150'), 'Ford F-150');
same('find Chevy|Silverado 1500 (make nickname)', f('Chevy', 'Silverado 1500'), 'Chevrolet Silverado 1500');
same('find Nissan (make only)', f('Nissan', ''), 'Nissan');
same('unknown model -> null', f('Nissan', 'Xtera'), null);
same('unknown make -> null', f('Datsun', 'Xterra'), null);
same('model under the wrong make -> null', f('Toyota', 'Xterra'), null);
same('empty make -> null', f('', 'Xterra'), null);

console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
