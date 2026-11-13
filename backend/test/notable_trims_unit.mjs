/* Unit test: notable trims (docs/app.js NOTABLE TRIMS + the car-search
 * trim rows and the #cars= 4th field).
 *   - notableTrimWords: the scan's per-model lookup; unknown make/model,
 *     missing or malformed table -> []
 *   - notableTrimHits / notableTrimOf: usable trims that name the word
 *     ("2.5XT", "OBK 2.5XT LTD", "XT Limited" are XT); not "2.5X",
 *     "X-Plus", "LTZ" for "LT"; unusable or empty quality never; decodes
 *     listing several trims or saying "non ..." never; "N Line" beats "N"
 *   - notableTrimMaybe: what the Trim filter counts as "no single trim"
 *   - trimAlternatives: list splitting, "R/T" kept whole, "w/" not a split
 *   - carSearchTrimMatch and parseCarsHash's trim field
 * The functions are taken from docs/app.js as written (no copy).
 * Run: node backend/test/notable_trims_unit.mjs */
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
const constLine = (name) => {
  const l = lines.find(x => x.startsWith(`const ${name} =`));
  if (!l) throw new Error('missing const ' + name);
  return l;
};
// The trim-watch matcher block (TRIM_ALIASES ... trimFilterMatches), as is.
const a = src.indexOf('const TRIM_ALIASES = ['), b = src.indexOf('function vpicFilterMatches(');
if (a < 0 || b < a) throw new Error('missing trim matcher block');
const names = ['setNotableTrims', 'notableTrimWords', 'trimAlternatives', 'notableTrimHits', 'notableTrimMaybe',
  'notableTrimsShown', 'notableTrimHitsOf', 'notableTrimOf', 'carSearchSquash', 'carSearchTrimMatch', 'parseCarsHash'];
const ctx = vm.createContext({});
vm.runInContext([src.slice(a, b), 'let notableTrims = null;', constLine('TRIM_NEGATION'),
  'const NOTABLE_TRIMS_FREE = true;', 'function isPro() { return false; }', ...names.map(fn),
  `globalThis.__t = { ${names.join(', ')}, get table() { return notableTrims; } };`].join('\n'), ctx);
const T = ctx.__t;

let fails = 0;
const eq = (x, y) => JSON.stringify(x) === JSON.stringify(y);
const check = (name, ok, d = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : '  ' + d}`); if (!ok) fails++; };
const same = (name, got, want) => check(name, eq(got, want), `got ${JSON.stringify(got)} want ${JSON.stringify(want)}`);

const TABLE = {
  Subaru: { Forester: ['XT'], Outback: ['Wilderness'], Legacy: ['GT', 'Spec'], Impreza: ['RS', '2.5RS', 'WRX', 'STI'] },
  Chevrolet: { Silverado: ['LT'] },   // test-only word, for "LTZ" vs "LT"
  Hyundai: { Elantra: ['N', 'Sport', 'N Line'], Sonata: ['Limited'] },
  Dodge: { Dakota: ['R/T'] },
  Toyota: { '4Runner': ['Trail', 'TRD Off-Road', 'TRD Pro', 'Limited'] },
  Volvo: { S60: ['R', 'T6 R'] },
  Ford: { Explorer: ['ST'] },                 // a label-only word (NOTABLE_TRIM_LABELS shape)
  Volkswagen: { Golf: ['GTI', 'R', 'Autobahn'] },
};
const car = (make, model, trim, q = 'usable', series = '') => ({ make, model, vpicTrim: trim, vpicTrimQuality: q, vpicSeries: series });

/* ---- lookup ---- */
T.setNotableTrims(null);
same('no table yet: no words', T.notableTrimWords('Subaru', 'Forester'), []);
same('no table yet: no badge', T.notableTrimOf(car('Subaru', 'Forester', '2.5XT')), '');
T.setNotableTrims([['XT']]);
check('an array is not a table', T.table === null);
T.setNotableTrims(TABLE);
same('Forester -> XT', T.notableTrimWords('Subaru', 'Forester'), ['XT']);
same('unknown model -> []', T.notableTrimWords('Subaru', 'Baja'), []);
same('unknown make -> []', T.notableTrimWords('Saab', '9-3'), []);
same('make and model are exact strings (raw model names)', T.notableTrimWords('subaru', 'forester'), []);
T.setNotableTrims({ Subaru: { Forester: 'XT', Outback: [null, '', 'Wilderness'] } });
same('malformed list -> []', T.notableTrimWords('Subaru', 'Forester'), []);
same('blank / non-string words dropped', T.notableTrimWords('Subaru', 'Outback'), ['Wilderness']);
T.setNotableTrims(TABLE);

/* ---- matching: positives ---- */
const hit = (v) => T.notableTrimHits(v);
for (const t of ['2.5XT', 'OBK 2.5XT LTD', 'XT Limited', 'XT', '2.0XT Touring', '2.5 XT / 2.5 XT Limited']) {
  same(`Forester "${t}" -> XT`, hit(car('Subaru', 'Forester', t)), ['XT']);
}
same('series can name it (trim empty)', hit(car('Subaru', 'Forester', '', 'usable', '2.5XT')), ['XT']);
same('Legacy "GT Limited" -> GT', hit(car('Subaru', 'Legacy', 'GT Limited')), ['GT']);
same('Legacy "2.5GT spec.B" -> GT + Spec', hit(car('Subaru', 'Legacy', '2.5GT spec.B')), ['GT', 'Spec']);
same('Impreza "2.5RS": the longer "2.5RS" beats "RS"', hit(car('Subaru', 'Impreza', '2.5RS')), ['2.5RS']);
same('Impreza "WRX STI" -> WRX + STI', hit(car('Subaru', 'Impreza', 'WRX STI')), ['WRX', 'STI']);
same('Elantra "N Line": "N Line" beats "N"', hit(car('Hyundai', 'Elantra', 'N Line')), ['N Line']);
same('Elantra "N" -> N', hit(car('Hyundai', 'Elantra', 'N')), ['N']);
same('Dakota "R/T" kept whole', hit(car('Dodge', 'Dakota', 'R/T')), ['R/T']);
same('4Runner "TRD Pro"', hit(car('Toyota', '4Runner', 'TRD Pro')), ['TRD Pro']);
same('4Runner "Grade: Luxury" -> Limited (the trim watch\'s Toyota alias)', hit(car('Toyota', '4Runner', 'Grade: Luxury')), ['Limited']);
same('Sonata "Limited/Limited w/Ultimate": both alternatives are Limited', hit(car('Hyundai', 'Sonata', 'Limited/Limited w/Ultimate')), ['Limited']);
same('notableTrimOf: the first hit', T.notableTrimOf(car('Subaru', 'Legacy', '2.5GT spec.B')), 'GT');

/* ---- matching: negatives ---- */
for (const t of ['2.5X', 'X-Plus', '2.5X Premium', 'XS', 'Base', 'Premium', '']) {
  same(`Forester "${t}" -> none`, hit(car('Subaru', 'Forester', t)), []);
}
same('"LTZ" is not "LT"', hit(car('Chevrolet', 'Silverado', 'LTZ')), []);
same('"1LT" is LT (leading digit split, as the trim watch does)', hit(car('Chevrolet', 'Silverado', '1LT')), ['LT']);
same('unusable quality never', hit(car('Subaru', 'Forester', '2.5XT', 'ambiguous')), []);
same('empty quality never', hit(car('Subaru', 'Forester', '2.5XT', '')), []);
same('missing quality never', hit({ make: 'Subaru', model: 'Forester', vpicTrim: '2.5XT' }), []);
same('unknown model never', hit(car('Subaru', 'Baja', 'Turbo XT')), []);
same('a list of trims never: "SE / SE NAVI / Limited / Limited NAVI"', hit(car('Hyundai', 'Sonata', 'SE / SE NAVI / Limited / Limited NAVI')), []);
same('a list of trims never: "Sport, R/T"', hit(car('Dodge', 'Dakota', 'Sport, R/T')), []);
same('a list of trims never: "Hybrid/ Hybrid Limited"', hit(car('Hyundai', 'Sonata', 'Hybrid/ Hybrid Limited')), []);
same('"Premier (non R design)" is not R', hit(car('Volvo', 'S60', 'Premier (non R design)')), []);
same('"Base (non R design)" is not R', hit(car('Volvo', 'S60', 'Base (non R design)')), []);
same('"R-Line"-style word with R alone still R (word match, as the trim watch)', hit(car('Volvo', 'S60', 'R')), ['R']);
same('null car', hit(null), []);
same('"ST-Line" is not ST (appearance package)', hit(car('Ford', 'Explorer', 'ST-Line')), []);
same('"R-Line" is not R', hit(car('Volkswagen', 'Golf', 'R-Line')), []);
same('"ST" is ST', hit(car('Ford', 'Explorer', 'ST')), ['ST']);
same('"Golf R" trim "R" is R', hit(car('Volkswagen', 'Golf', 'R')), ['R']);
same('"N Line" still names N Line', hit(car('Hyundai', 'Elantra', 'N Line')), ['N Line']);
// Gate-derived and label words are one list to the app: both badge.
T.setNotableTrims({ ...TABLE, Subaru: { ...TABLE.Subaru, Outback: ['Wilderness', 'XT'] } });
same('gate word badges (Outback "Wilderness")', hit(car('Subaru', 'Outback', 'Wilderness')), ['Wilderness']);
same('label word badges (Outback "OBK 2.5XT LTD")', hit(car('Subaru', 'Outback', 'OBK 2.5XT LTD')), ['XT']);
same('Outback "2.5GT Limited" is not XT', hit(car('Subaru', 'Outback', '2.5GT Limited')), []);
T.setNotableTrims(TABLE);

/* ---- maybe (counted as "no single trim") ---- */
check('maybe: unusable decode', T.notableTrimMaybe(car('Subaru', 'Forester', '', 'empty'), 'XT'));
check('maybe: list naming it', T.notableTrimMaybe(car('Hyundai', 'Sonata', 'SE / Limited'), 'Limited'));
check('maybe: not when the usable trim is another one', !T.notableTrimMaybe(car('Subaru', 'Forester', '2.5X'), 'XT'));

/* ---- alternatives ---- */
same('slash list', T.trimAlternatives('SE / SE NAVI / Limited', []), ['SE', 'SE NAVI', 'Limited']);
same('comma + and', T.trimAlternatives('Turbo R-Spec, Turbo and Turbo Ultimate', []), ['Turbo R-Spec', 'Turbo', 'Turbo Ultimate']);
same('w/ is not a split', T.trimAlternatives('Limited/Limited w/Ultimate', []), ['Limited', 'Limited with Ultimate']);
same('a gate word with a slash stays whole', T.trimAlternatives('SLT, R/T', ['R/T']), ['SLT', 'R/T']);
same('no separators: one', T.trimAlternatives('OBK 2.5XT LTD', ['XT']), ['OBK 2.5XT LTD']);

/* ---- car search trim rows ---- */
const entries = [
  { make: 'Subaru', model: '', n: 50, alts: [] },
  { make: 'Subaru', model: 'Forester', n: 30, alts: [], trims: [['XT', 7]] },
  { make: 'Subaru', model: 'Outback', n: 40, alts: [] },
  { make: 'Toyota', model: '4Runner', n: 20, alts: [], trims: [['TRD Pro', 2], ['Limited', 5]] },
  { make: 'Chevrolet', model: 'Camaro', n: 9, alts: ['chevy'], trims: [['SS', 3]] },
];
const tm = (q) => T.carSearchTrimMatch(entries, q).map(r => `${r.make} ${r.model} · ${r.trim} t${r.tier}`);
same('"forester xt" -> Subaru Forester · XT (exact)', tm('forester xt'), ['Subaru Forester · XT t0']);
same('"Subaru Forester XT" (make in front)', tm('Subaru Forester XT'), ['Subaru Forester · XT t0']);
same('"forester x" -> the start of XT', tm('forester x'), ['Subaru Forester · XT t1']);
same('"forester" alone -> no trim row', tm('forester'), []);
same('"outback xt": no Outback XT in the table -> none', tm('outback xt'), []);
same('"4runner trd pro"', tm('4runner trd pro'), ['Toyota 4Runner · TRD Pro t0']);
same('"4 runner trd" -> start of TRD Pro', tm('4 runner trd'), ['Toyota 4Runner · TRD Pro t1']);
same('"chevy camaro ss" (make nickname)', tm('chevy camaro ss'), ['Chevrolet Camaro · SS t0']);
same('"forester xtz" -> none', tm('forester xtz'), []);
same('empty -> none', tm(''), []);

/* ---- #cars= 4th field ---- */
same('#cars=Subaru|Outback||XT', T.parseCarsHash('#cars=Subaru|Outback||XT'), { make: 'Subaru', model: 'Outback', yrMin: null, yrMax: null, trim: 'XT' });
same('#cars=Subaru|Forester|2004-2008|XT', T.parseCarsHash('#cars=Subaru|Forester|2004-2008|XT'), { make: 'Subaru', model: 'Forester', yrMin: 2004, yrMax: 2008, trim: 'XT' });
same('percent-encoded trim', T.parseCarsHash('#cars=Toyota%7C4Runner%7C%7CTRD%20Pro'), { make: 'Toyota', model: '4Runner', yrMin: null, yrMax: null, trim: 'TRD Pro' });
same('three fields: no trim key (unchanged)', T.parseCarsHash('#cars=Nissan|Xterra|2005-2015'), { make: 'Nissan', model: 'Xterra', yrMin: 2005, yrMax: 2015 });
same('a trim without a model is dropped', T.parseCarsHash('#cars=Subaru|||XT'), { make: 'Subaru', model: '', yrMin: null, yrMax: null });
same('markup stripped from the trim', T.parseCarsHash('#cars=Subaru|Forester||<b>XT</b>'), { make: 'Subaru', model: 'Forester', yrMin: null, yrMax: null, trim: 'bXT/b' });

/* ---- NOTABLE_TRIMS_FREE: the owner's free-or-Pro switch ---- */
const shipped = /^const NOTABLE_TRIMS_FREE = (true|false);$/m.exec(src);
check('NOTABLE_TRIMS_FREE is one constant, true on this branch', !!shipped && shipped[1] === 'true', shipped && shipped[0]);
for (const free of [true, false]) {
  for (const pro of [false, true]) {
    const c2 = vm.createContext({});
    vm.runInContext([src.slice(a, b), 'let notableTrims = null;', constLine('TRIM_NEGATION'),
      `const NOTABLE_TRIMS_FREE = ${free};`, `function isPro() { return ${pro}; }`,
      ...['setNotableTrims', 'notableTrimWords', 'trimAlternatives', 'notableTrimHits', 'notableTrimsShown', 'notableTrimHitsOf', 'notableTrimOf'].map(fn),
      'globalThis.__u = { setNotableTrims, notableTrimsShown, notableTrimHitsOf, notableTrimOf };'].join('\n'), c2);
    const U = c2.__u;
    U.setNotableTrims(TABLE);
    const v = car('Subaru', 'Forester', '2.5XT');
    const want = free || pro;
    const tag = `FREE=${free}, ${pro ? 'Pro' : 'free user'}`;
    same(`${tag}: shown = ${want}`, U.notableTrimsShown(), want);
    same(`${tag}: badge word ${want ? '"XT"' : 'none'}`, U.notableTrimOf(v), want ? 'XT' : '');
    same(`${tag}: internal hits still computed (stats, never shown)`, U.notableTrimHitsOf(v), ['XT']);
  }
}

console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
