/* Unit test: server watch matching (src/alerts.js watchMatches) follows the
 * app's rule — contains OR canonical-equal — and drops a leading own make.
 * Run: node test/watch_match_unit.mjs */
import { watchMatches } from '../src/alerts.js';

let failures = 0;
const check = (name, ok) => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}`); if (!ok) failures++; };
const car = (make, model, year = 2008) => ({ make, model, year, lat: 40, lng: -111, vpic: null });
const w = (make, model, extra = {}) => ({ make, model, ...extra });

check('Silverado watch matches a Silverado 1500 (contains)', watchMatches(w('Chevrolet', 'Silverado'), car('Chevrolet', 'Silverado 1500')));
check('Accord watch matches Accord Hybrid', watchMatches(w('Honda', 'Accord'), car('Honda', 'Accord Hybrid')));
check('exact names still match', watchMatches(w('Toyota', '4Runner'), car('Toyota', '4Runner')));
check('MX-5 watch matches MX-5 Miata (canonical alias)', watchMatches(w('Mazda', 'MX-5'), car('Mazda', 'MX-5 Miata')));
check('Miata watch matches MX-5 Miata (contains)', watchMatches(w('Mazda', 'Miata'), car('Mazda', 'MX-5 Miata')));
check("'Infiniti G35' watch matches a G35 (own make dropped)", watchMatches(w('Infiniti', 'Infiniti G35'), car('Infiniti', 'G35')));
check('a more specific watch does NOT match the plainer car', !watchMatches(w('Chevrolet', 'Silverado 1500'), car('Chevrolet', 'Silverado')));
check('different model does not match', !watchMatches(w('Toyota', 'Tacoma'), car('Toyota', 'Tundra')));
check('different make does not match', !watchMatches(w('Ford', 'Ranger'), car('Mazda', 'B3000')));
check('year range still applies', !watchMatches(w('Toyota', '4Runner', { year_min: 1996, year_max: 2002 }), car('Toyota', '4Runner', 2005)));
check('radius still applies', !watchMatches(w('Toyota', '4Runner', { lat: 30, lng: -97, radius_mi: 50 }), car('Toyota', '4Runner')));
check('any-model watch (no model) matches the make', watchMatches(w('Toyota', ''), car('Toyota', 'Camry')));

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
