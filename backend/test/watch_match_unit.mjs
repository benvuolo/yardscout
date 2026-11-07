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
check("'Toyota / Scion tC' watch matches a car now filed Scion / tC", watchMatches(w('Toyota', 'Scion tC'), car('Scion', 'tC')));
check("'Toyota / Scion tC' watch still matches a yard filing it under Toyota", watchMatches(w('Toyota', 'Scion tC'), car('Toyota', 'Scion tC')));
check("'Toyota / Scion tC' watch does not match a Toyota Camry", !watchMatches(w('Toyota', 'Scion tC'), car('Toyota', 'Camry')));
check("a plain Toyota watch does not match Scion", !watchMatches(w('Toyota', '4Runner'), car('Scion', 'tC')));

// 2026-11-04 data-quality merge: watches saved under a pre-merge spelling
// (D1 rows are never rewritten) must still match the car under its new
// canonical name, and the canonical watch must still match an old spelling a
// yard may keep sending.
for (const [wm, wmod, cm, cmod] of [
  ['Dodge', 'Ram1500', 'Dodge', 'Ram 1500'], ['Dodge', 'Ram 1500', 'Dodge', 'Ram1500'],
  ['Dodge', 'D-150', 'Dodge', 'D150'], ['Chevrolet', 'Trail Blazer', 'Chevrolet', 'Trailblazer'],
  ['Chevrolet', 'TrailBlazer', 'Chevrolet', 'Trailblazer'], ['Chevrolet', 'Blazers10', 'Chevrolet', 'Blazer S10'],
  ['Chevrolet', 'C/k 10', 'Chevrolet', 'C/K 10'], ['Nissan', 'X-terra', 'Nissan', 'Xterra'],
  ['BMW', '325-I', 'BMW', '325i'], ['Cadillac', 'Ats', 'Cadillac', 'ATS'], ['Cadillac', "Allante'", 'Cadillac', 'Allante'],
  ['Kia', 'Spectra 5', 'Kia', 'Spectra5'], ['Subaru', 'Legacy/ Outback', 'Subaru', 'Legacy Outback'],
  ['Isuzu', 'I-290', 'Isuzu', 'i-290'], ['Scion', 'Fr-S', 'Scion', 'FR-S'], ['Pontiac', 'Le Mans', 'Pontiac', 'LeMans'],
  ['Triumph', 'TR-7', 'Triumph', 'TR7'], ['Lexus', 'Es300', 'Lexus', 'ES 300'], ['Scion', 'TC', 'Scion', 'tC'],
]) {
  check(`old-spelling watch '${wm} ${wmod}' matches car '${cm} ${cmod}'`, watchMatches(w(wm, wmod), car(cm, cmod)));
}
check("'Ram 1500' watch does not match a Ram 2500", !watchMatches(w('Dodge', 'Ram 1500'), car('Dodge', 'Ram2500')));
check("'Trailblazer' watch also matches a Trailblazer EXT (contains, same rule as Silverado)", watchMatches(w('Chevrolet', 'Trailblazer'), car('Chevrolet', 'Trailblazer EXT')));
check("'Dodge / Ram 1500' watch matches a truck filed under make Ram", watchMatches(w('Dodge', 'Ram 1500'), car('Ram', '1500')));

// Round 5 (alerts first): "Alert me when the next one lands", "Want the next
// one?" and "Watch for another …" create quick watches from the car's RAW
// row strings (make + model, no years) through the app's addQuickWatch, or the
// seeker's model + generation years on the Parts tab. Those shapes must match
// the next car of the same model on the server, and nothing else.
check('car-screen watch from raw row strings matches the next one (BMW X5)', watchMatches(w('BMW', 'X5'), car('BMW', 'X5', 2004)));
check('car-screen watch from a yard spelling matches the canonical car (Ram1500)', watchMatches(w('Dodge', 'Ram1500'), car('Dodge', 'Ram 1500')));
check('parts-tab watch with the generation years matches inside them', watchMatches(w('Honda', 'Accord', { year_min: 1994, year_max: 1997 }), car('Honda', 'Accord', 1996)));
check('parts-tab watch with the generation years does not match outside them', !watchMatches(w('Honda', 'Accord', { year_min: 1994, year_max: 1997 }), car('Honda', 'Accord', 2001)));
check('a next-one watch does not match a different model at the same yard', !watchMatches(w('BMW', 'X5'), car('BMW', 'X3')));

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
