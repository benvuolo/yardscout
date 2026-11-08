/* Unit test: the model-picker year filter (docs/app.js setModelYears,
 * modelFitsYears). The scan publishes modelYears {make: {rawModel:
 * [first, last]}}; with a year chosen, a picker offers only models built
 * within one year of it. Missing field = no filter (today's behaviour);
 * a model with no span is kept, never hidden.
 * Run: node backend/test/model_years_unit.mjs */
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
const one = (re) => { const l = lines.find(x => re.test(x)); if (!l) throw new Error('missing ' + re); return l; };
const ctx = vm.createContext({});
vm.runInContext([one(/^let modelYearSpans = /), fn('setModelYears'), fn('modelFitsYears'),
  'globalThis.__t = { setModelYears, modelFitsYears };'].join('\n'), ctx);
const { setModelYears, modelFitsYears: fits } = ctx.__t;

let fails = 0;
const check = (name, ok) => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}`); if (!ok) fails++; };

check('no field published: every model offered', fits('Chevrolet', 'Chevelle', 2003, 2003));
setModelYears({ Chevrolet: { Chevelle: [1964, 1977], Impala: [1958, 2020], Celebrity: [1982, 1990] } });
check('2003: Chevelle (1964-77) hidden', !fits('Chevrolet', 'Chevelle', 2003, 2003));
check('2003: Celebrity (1982-90) hidden', !fits('Chevrolet', 'Celebrity', 2003, 2003));
check('2003: Impala (1958-2020) offered', fits('Chevrolet', 'Impala', 2003, 2003));
check('one year either side counts: 1978 offers Chevelle', fits('Chevrolet', 'Chevelle', 1978, 1978));
check('one year either side counts: 1963 offers Chevelle', fits('Chevrolet', 'Chevelle', 1963, 1963));
check('two years out: 1979 hides Chevelle', !fits('Chevrolet', 'Chevelle', 1979, 1979));
check('no year chosen: every model offered', fits('Chevrolet', 'Chevelle', null, null));
check('range overlapping the span: offered', fits('Chevrolet', 'Chevelle', 1975, 1990));
check('open-ended "from 2000": Chevelle hidden, Impala offered', !fits('Chevrolet', 'Chevelle', 2000, null) && fits('Chevrolet', 'Impala', 2000, null));
check('open-ended "to 1970": Celebrity hidden, Chevelle offered', !fits('Chevrolet', 'Celebrity', null, 1970) && fits('Chevrolet', 'Chevelle', null, 1970));
check('model with no span: kept', fits('Chevrolet', 'Malibu', 2003, 2003));
check('make with no spans: kept', fits('Ford', 'Taurus', 2003, 2003));
setModelYears({ Chevrolet: { Bad: ['x', 1990], Odd: [0, 0], Short: [1990] } });
check('malformed spans: kept', fits('Chevrolet', 'Bad', 2003, 2003) && fits('Chevrolet', 'Odd', 2003, 2003) && fits('Chevrolet', 'Short', 2003, 2003));
setModelYears([1, 2]);
check('array instead of object: treated as missing', fits('Chevrolet', 'Chevelle', 2003, 2003));
setModelYears({ Chevrolet: { Chevelle: [1964, 1977] } }); setModelYears(undefined);
check('newer data without the field clears it (no stale filter)', fits('Chevrolet', 'Chevelle', 2003, 2003));

console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
