/* YardScout — application logic (loading, filtering, rendering, saved list, alerts). */

/* ===== ANALYTICS — GoatCounter (privacy-friendly: no cookies, anonymous) =====
 * Set the site code after creating a (free) account at goatcounter.com.
 * While GOATCOUNTER_CODE is null every track() call is a no-op. */
const GOATCOUNTER_CODE = null; // e.g. 'yardscout' for https://yardscout.goatcounter.com
function track(event) {
  if (!GOATCOUNTER_CODE) return;
  try {
    if (window.goatcounter && window.goatcounter.count) {
      window.goatcounter.count({ path: event, title: event, event: true });
    }
  } catch (e) { /* analytics must never break the app */ }
}
if (GOATCOUNTER_CODE) {
  window.goatcounter = { endpoint: 'https://' + GOATCOUNTER_CODE + '.goatcounter.com/count' };
  const gcScript = document.createElement('script');
  gcScript.async = true;
  gcScript.src = 'https://gc.zgo.at/count.js';
  document.head.appendChild(gcScript);
}
/* ===== YARD PRICING MAPS =====
 * One map per chain, each built ONLY from that chain's published price list.
 * pypPricing / papPricing are keyed by yard display name (prices differ per yard).
 * There is deliberately NO estimated-cost fallback: if a part isn't on the
 * yard's own price list, we show "check yard price list" instead of a guess. */
let pnpPricing = {};
let tapPricing = {};
let utpapPricing = {};
let pypPricing = {};   // { "Pick Your Part - Orlando": { "HEADLIGHT": {price, core}, ... } }
let papPricing = {};   // { "Pull-A-Part - Charlotte": { "BRAKE CALIPER": {price, core}, ... } }
let wapPricing = {};   // { "Wrench-A-Part - Austin": { "ALTERNATOR": {price, core}, ... } } (per yard)
let upullrPricing = {}; // U-Pull-R Parts: one chain-wide flat-rate list, keyed by description

/* utpap = exact "Part Description" from utpap.com/1064Carpricelist.php (Ogden pricelist iframe on ogden-prices page)
 * pyp = exact "Description" from pyp.com per-location PriceList API
 * pap = exact "partname" from Pull-A-Part's per-location pricing API
 * wap = exact "name" from Wrench-A-Part's per-location price-list API (api.wrenchapart.com/price-list)
 * upullr = exact title from upullrparts.com/part-pricing/ (chain-wide flat-rate list)
 *
 * Matching: lowercase substring, LONGEST matching keyword wins (see
 * _lookupYardCostUncached), so specific keywords beat generic ones regardless
 * of table order. A chain column is omitted when that chain's published list
 * has no unambiguous item for the part — those stay "check yard price list"
 * honestly. An entry with a kw and no chain columns deliberately pins an
 * ambiguous part name to "unmapped" so a shorter generic keyword can't
 * mis-price it. */
const PART_KEYWORD_MAP = [
  // --- lighting ---
  { kw: 'hid headlight',       pnp: 'HEADLIGHT COMP',               tap: 'HEADLIGHT COMPOSITE', utpap: 'HEADLAMP W/ TURN SIG', pyp: 'HEADLIGHT', pap: 'HEADLIGHT LED OR HID LAMP ASSEMBLY W/BALLAST', wap: 'HEADLAMP COMP HID', upullr: 'HEADLAMP HID' },
  { kw: 'led headlight',       pnp: 'HEADLIGHT COMP',               tap: 'HEADLIGHT COMPOSITE', utpap: 'HEADLAMP W/ TURN SIG', pyp: 'HEADLIGHT', pap: 'HEADLIGHT LED OR HID LAMP ASSEMBLY W/BALLAST', wap: 'HEADLAMP COMP HID', upullr: 'HEADLAMP HID' },
  { kw: 'headlight',           pnp: 'HEADLIGHT COMP',               tap: 'HEADLIGHT COMPOSITE', utpap: 'HEADLAMP W/ TURN SIG', pyp: 'HEADLIGHT', pap: 'HEADLIGHT ASSEMBLY (NON-HID/BALLAST)', wap: 'HEADLAMP COMPOSITE NO HID', upullr: 'HEADLAMP' },
  { kw: 'headlamp',            pnp: 'HEADLIGHT COMP',               tap: 'HEADLIGHT COMPOSITE', utpap: 'HEADLAMP W/ TURN SIG', pyp: 'HEADLIGHT', pap: 'HEADLIGHT ASSEMBLY (NON-HID/BALLAST)', wap: 'HEADLAMP COMPOSITE NO HID', upullr: 'HEADLAMP' },
  { kw: 'tail light',          pnp: 'TAILLIGHT ASSY',               tap: 'TAIL LIGHT ASSY ANY', utpap: 'TAIL LIGHT ASSY LRG', pyp: 'TAILLIGHT (QUARTER MOUNTED)', pap: 'TAILLIGHT ASSEMBLY - SINGLE SIDE', wap: 'TAIL LIGHT SMALL', upullr: 'TAILLIGHT' },
  { kw: 'taillight',           pnp: 'TAILLIGHT ASSY',               tap: 'TAIL LIGHT ASSY ANY', utpap: 'TAIL LIGHT ASSY LRG', pyp: 'TAILLIGHT (QUARTER MOUNTED)', pap: 'TAILLIGHT ASSEMBLY - SINGLE SIDE', wap: 'TAIL LIGHT SMALL', upullr: 'TAILLIGHT' },
  { kw: 'fog light',           pnp: 'FOG LAMPS EACH',               tap: 'HEADLIGHT COMP BULB', utpap: 'FOG LIGHT', pyp: 'FRONT LAMP (FOG/PARKING/TURN/MARKER)', pap: 'FOG LAMP (EACH)', wap: 'FOG LIGHT', upullr: 'FOG LIGHT' },
  { kw: 'fog lamp',            pnp: 'FOG LAMPS EACH',               tap: 'HEADLIGHT COMP BULB', utpap: 'FOG LIGHT', pyp: 'FRONT LAMP (FOG/PARKING/TURN/MARKER)', pap: 'FOG LAMP (EACH)', wap: 'FOG LIGHT', upullr: 'FOG LIGHT' },
  // --- seats ---
  { kw: 'recaro seat',         pnp: 'SEAT-BUCK(EA)W/TRK (PWR)',     tap: 'BUCKET SEAT POWER', utpap: 'BUCKET SEAT ELCTRIC', pyp: 'SEAT WITH AIR BAG FRONT', pap: 'SEAT, BUCKET W/ POWER TRACK (LEATHER)', upullr: 'SEATS BUCKET' },
  { kw: 'stow-n-go 2nd',      pnp: 'SEAT-BUCK(EA)W/TRK (MAN)',     tap: 'BUCKET SEAT', utpap: 'BUCKET SEAT ELCTRIC', pyp: 'SEAT NO AIR BAG FRONT', pap: 'SEAT, BUCKET W/ MANUAL TRACK', upullr: 'SEATS BUCKET' },
  { kw: 'stow-n-go 3rd',      pnp: 'SEAT-REAR (EA)',               tap: 'SEAT SECTION', utpap: 'BENCH SEAT ELECTRIC', pyp: 'SEAT REAR', pap: 'SEAT, BENCH/3RD ROW MANUAL TRACK', wap: 'BENCH SEAT', upullr: 'SEATS BENCH' },
  { kw: 'stow-n-go',          pnp: 'SEAT-BUCK(EA)W/TRK (MAN)',     tap: 'BUCKET SEAT', utpap: 'BUCKET SEAT ELCTRIC', pyp: 'SEAT NO AIR BAG FRONT', pap: 'SEAT, BUCKET W/ MANUAL TRACK', upullr: 'SEATS BUCKET' },
  { kw: '3rd row seat',        pnp: 'SEAT-REAR (EA)',               tap: 'SEAT SECTION', utpap: 'BENCH SEAT ELECTRIC', pyp: 'SEAT THIRD ROW', pap: 'SEAT, BENCH/3RD ROW MANUAL TRACK', wap: 'BENCH SEAT', upullr: 'SEATS BENCH' },
  { kw: 'rear seat',           pnp: 'SEAT-REAR (EA)',               tap: 'SEAT SECTION', utpap: 'BENCH SEAT ELECTRIC', pyp: 'SEAT REAR', pap: 'SEAT, REAR - EACH SECTION (CLOTH)', wap: 'BENCH SEAT', upullr: 'SEAT RR SECTION-CAR' },
  { kw: 'bench seat',          pnp: 'SEAT-BENCH W/TRK',             tap: 'SEAT BENCH', utpap: 'BENCH SEAT ELECTRIC', pyp: 'SEAT REAR', pap: 'SEAT, BENCH W/ POWER TRACK (LEATHER)', wap: 'BENCH SEAT', upullr: 'SEATS BENCH' },
  { kw: 'bench',               pnp: 'SEAT-BENCH W/TRK',             tap: 'SEAT BENCH', utpap: 'BENCH SEAT MANUAL', pyp: 'SEAT REAR', pap: 'SEAT, BENCH/3RD ROW MANUAL TRACK', wap: 'BENCH SEAT', upullr: 'SEATS BENCH' },
  { kw: 'bucket seat',         pnp: 'SEAT-BUCK(EA)W/TRK (PWR)',     tap: 'BUCKET SEAT POWER', utpap: 'BUCKET SEAT ELCTRIC', pyp: 'SEAT WITH AIR BAG FRONT', pap: 'SEAT, BUCKET W/ POWER TRACK (LEATHER)', upullr: 'SEATS BUCKET' },
  { kw: 'seat',                pnp: 'SEAT-BUCK(EA)W/TRK (PWR)',     tap: 'BUCKET SEAT POWER', utpap: 'BUCKET SEAT ELCTRIC', pyp: 'SEAT WITH AIR BAG FRONT', pap: 'SEAT, BUCKET W/ POWER TRACK (LEATHER)', upullr: 'SEATS BUCKET' },
  { kw: 'track',               pnp: 'SEAT TRACK ELEC W/MOTOR (EA)', tap: 'SEAT TRACKSET+MOTOR', utpap: 'SEAT TRACK ELECTRIC', pyp: 'SEAT TRACK, (ELECTRIC)', pap: 'SEAT TRACK, ELECTRIC W/MOTOR', wap: 'SEAT TRACK ELECTRIC', upullr: 'SEAT TRACK-ELECTRIC' },
  // --- gauges / clusters ---
  { kw: 'digital dash',        pnp: 'INSTRUMENT CLUSTER ASSY',      tap: 'INSTRUMENT CLUSTER', utpap: 'INSTRUMENT CLUSTER', pyp: 'INSTRUMENT CLUSTER', pap: 'INSTRUMENT CLUSTER ASSEMBLY', wap: 'INSTRUMENT CLUSTER DIGITAL', upullr: 'INSTRUMENT CLUSTER' },
  { kw: 'digital cluster',     pnp: 'INSTRUMENT CLUSTER ASSY',      tap: 'INSTRUMENT CLUSTER', utpap: 'INSTRUMENT CLUSTER', pyp: 'INSTRUMENT CLUSTER', pap: 'INSTRUMENT CLUSTER ASSEMBLY', wap: 'INSTRUMENT CLUSTER DIGITAL', upullr: 'INSTRUMENT CLUSTER' },
  { kw: 'cluster',             pnp: 'INSTRUMENT CLUSTER ASSY',      tap: 'INSTRUMENT CLUSTER', utpap: 'INSTRUMENT CLUSTER', pyp: 'INSTRUMENT CLUSTER', pap: 'INSTRUMENT CLUSTER ASSEMBLY', wap: 'INSTRUMENT CLUSTER ANALOG', upullr: 'INSTRUMENT CLUSTER' },
  { kw: 'speedometer',         pnp: 'SPEEDOMETER OR TACHOMETER',    tap: 'GAUGE SINGLE', utpap: 'SPEEDOMETER', pyp: 'GAUGES', pap: 'SPEEDOMETER OR TACHOMETER', upullr: 'GAUGE SINGLE' },
  { kw: 'gauge',               pnp: 'CLOCK/ SMALL GAUGES EACH',     tap: 'GAUGE SINGLE', utpap: 'GAUGE SINGLE', pyp: 'GAUGES', pap: 'CLOCK OR SMALL GAUGES (EACH)', wap: 'GAUGE (SINGLE/MISC)', upullr: 'GAUGE SINGLE' },
  // --- charging / hybrid ---
  { kw: 'alternator',          pnp: 'ALTERNATOR',                   tap: 'ALTERNATOR', utpap: 'ALTERNATOR', pyp: 'ALTERNATOR', pap: 'ALTERNATOR (NON HYBRID)', wap: 'ALTERNATOR', upullr: 'ALTERNATOR' },
  { kw: 'hybrid battery',      pnp: 'BATTERY HYBRID/ELECTRICAL',    pyp: 'BATTERY (HYBRID BATTERY)', pap: 'HYBRID BATTERY ANY', wap: 'HYBRID BATTERY' },
  { kw: 'battery cells',       pnp: 'BATTERY HYBRID/ELECTRICAL',    pyp: 'BATTERY (HYBRID BATTERY)', pap: 'HYBRID BATTERY ANY', wap: 'HYBRID BATTERY' },
  { kw: 'inverter pump',       pnp: 'WATER PUMP',                   tap: 'WATER PUMP (ELECTRIC', utpap: 'WATER PUMP', pyp: 'WATER PUMP', pap: 'AUXILIARY WATER PUMP', wap: 'WATER PUMP', upullr: 'WATER PUMP' },
  { kw: 'dc-dc',               pnp: 'POWER VOLTAGE INVERTER',       pyp: 'DC CONVERTER (HYBRID/ELECTRIC)', pap: 'HYBRID POWER CONTROL MODULE/INVERTER', wap: 'INVERTER HYBRID', upullr: 'HYBRID INVERTER/CONV' },
  { kw: 'dc converter',        pnp: 'POWER VOLTAGE INVERTER',       pyp: 'DC CONVERTER (HYBRID/ELECTRIC)', pap: 'HYBRID POWER CONTROL MODULE/INVERTER', wap: 'INVERTER HYBRID', upullr: 'HYBRID INVERTER/CONV' },
  { kw: 'inverter',            pnp: 'POWER VOLTAGE INVERTER',       pyp: 'DC CONVERTER (HYBRID/ELECTRIC)', pap: 'HYBRID POWER CONTROL MODULE/INVERTER', wap: 'INVERTER HYBRID', upullr: 'HYBRID INVERTER/CONV' },
  // --- audio / infotainment ---
  { kw: 'amplifier',           pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER', wap: 'AMPLIFIER OEM', upullr: 'AMPLIFIER/EQUALIZER' },
  { kw: 'amp',                 pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER', wap: 'AMPLIFIER OEM', upullr: 'AMPLIFIER/EQUALIZER' },
  { kw: 'audio',               pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER', wap: 'AMPLIFIER OEM', upullr: 'AMPLIFIER/EQUALIZER' },
  { kw: 'bose',                pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER', wap: 'AMPLIFIER OEM', upullr: 'AMPLIFIER/EQUALIZER' },
  { kw: 'harman',              pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER', wap: 'AMPLIFIER OEM', upullr: 'AMPLIFIER/EQUALIZER' },
  { kw: 'jbl',                 pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER', wap: 'AMPLIFIER OEM', upullr: 'AMPLIFIER/EQUALIZER' },
  { kw: 'logic7',              pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER', wap: 'AMPLIFIER OEM', upullr: 'AMPLIFIER/EQUALIZER' },
  { kw: 'b&o',                 pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER', wap: 'AMPLIFIER OEM', upullr: 'AMPLIFIER/EQUALIZER' },
  { kw: 'bang & olufsen',      pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER', wap: 'AMPLIFIER OEM', upullr: 'AMPLIFIER/EQUALIZER' },
  { kw: 'speaker',             pnp: 'SPEAKER EACH',                 tap: 'SPEAKER', utpap: 'RADIO SPEAKER', pyp: 'RADIO SPEAKER', pap: 'SPEAKER (ANY)', wap: 'SPEAKER 0-5.9"', upullr: 'SPEAKER' },
  { kw: 'heads-up display',    pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY', wap: 'RADIO (SCREEN)', upullr: 'INFORMATION SCREEN' },
  { kw: 'touchscreen',         pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY', wap: 'RADIO (SCREEN)', upullr: 'INFORMATION SCREEN' },
  { kw: 'infotainment',        pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY', wap: 'RADIO (SCREEN)', upullr: 'INFORMATION SCREEN' },
  { kw: 'navigation',          pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'NAVIGATION UNIT', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY', wap: 'RADIO (SCREEN)', upullr: 'NAVIGATION UNIT' },
  { kw: 'display',             pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY', wap: 'RADIO (SCREEN)', upullr: 'INFORMATION SCREEN' },
  { kw: 'sync',                pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY', wap: 'RADIO (SCREEN)', upullr: 'INFORMATION SCREEN' },
  { kw: 'myford',              pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY', wap: 'RADIO (SCREEN)', upullr: 'INFORMATION SCREEN' },
  { kw: 'mmi',                 pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY', wap: 'RADIO (SCREEN)', upullr: 'INFORMATION SCREEN' },
  { kw: 'head unit',           pnp: 'RADIO',                        tap: 'RADIO', utpap: 'RADIO CD PLAYER', pyp: 'RADIO WITH DISPLAY', pap: 'RADIO  - W/CD OR MEDIA PLAYER', wap: 'RADIO (NO SCREEN)', upullr: 'RADIO' },
  { kw: 'radio',               pnp: 'RADIO',                        tap: 'RADIO', utpap: 'RADIO CD PLAYER', pyp: 'RADIO WITH DISPLAY', pap: 'RADIO  - W/CD OR MEDIA PLAYER', wap: 'RADIO (NO SCREEN)', upullr: 'RADIO' },
  { kw: 'entertainment',       pnp: 'LRG MULTIFUNCT DISPLAY',      tap: 'DVD PLAYER', utpap: 'RADIO CD PLAYER', pyp: 'GPS TV SCREEN', pap: 'VIDEO SCREEN', wap: 'HEADREST SCREEN', upullr: 'MEDIA PLAYER' },
  { kw: 'dvd',                 pnp: 'LRG MULTIFUNCT DISPLAY',      tap: 'DVD PLAYER', utpap: 'RADIO CD PLAYER', pyp: 'GPS TV SCREEN', pap: 'VIDEO SCREEN', wap: 'HEADREST SCREEN', upullr: 'MEDIA PLAYER' },
  // --- body / exterior ---
  { kw: 'front bumper',        pnp: 'BUMPER COMP',                  tap: 'BUMPR CVER W/RENFORC', utpap: 'BUMPER', pyp: 'FRONT BUMPER (STEEL)', pap: 'BUMPER COVER ASSEMBLY', wap: 'BUMPER ASSEMBLY FRONT CAR', upullr: 'BUMPER (BARE)' },
  { kw: 'bumper cover',        pnp: 'BUMPER COVER (PLAST/RUBR)',    tap: 'BUMPER COVER', utpap: 'BUMPER', pyp: 'BUMPER COVER, FRONT', pap: 'BUMPER COVER', wap: 'BUMPER COVER FRONT (BARE)', upullr: 'BUMPER (BARE)' },
  { kw: 'bumper',              pnp: 'BUMPER COMP',                  tap: 'BUMPR CVER W/RENFORC', utpap: 'BUMPER', pyp: 'FRONT BUMPER (STEEL)', pap: 'BUMPER STEEL OR ALUMINUM', wap: 'BUMPER ASSEMBLY FRONT CAR', upullr: 'BUMPER (BARE)' },
  { kw: 'tailgate',            pnp: 'GATE-PU/VAN',                  tap: 'TAIL GATE', utpap: 'TAIL GATE/ ENDGATE', pyp: 'DECKLID/TAILGATE (BARE)', pap: 'TRUCK GATE FOR BED', wap: 'TAILGATE BARE', upullr: 'TAIL GATE-TRUCK' },
  { kw: 'rear gate',           pnp: 'GATE-PU/VAN',                  tap: 'TAIL GATE W/ GLASS', utpap: 'TAILGATE W/ GLASS', pyp: 'DECKLID/TAILGATE (BARE)', pap: 'TRUCK GATE FOR BED', wap: 'TAILGATE BARE', upullr: 'TAIL GATE-SUV/VAN' },
  { kw: 'spoiler',             pnp: 'SPOILERS - BOLT ON (EA)',      tap: 'SPOILER', utpap: 'SPOILER', pyp: 'SPOILER REAR', pap: 'SPOILER - BOLT ON (EACH)', wap: 'SPOILER NO LIGHT', upullr: 'SPOILER' },
  { kw: 'grille',              pnp: 'GRILL PLASTIC',               tap: 'GRILLE', utpap: 'GRILLE LRG', pyp: 'GRILLE', pap: 'GRILLE PLASTIC (BARE) - ANY', wap: 'GRILLE 19-48"', upullr: 'GRILLE' },
  { kw: 'running board',       pnp: 'RUNNING BOARD',               tap: 'RUNNING BOARD (EACH)', utpap: 'RUNNING BOARD', pyp: 'RUNNING BOARD', pap: 'RUNNING BOARD (EACH)', wap: 'RUNNING BOARD NON-ELECTRIC', upullr: 'RUNNING BOARD' },
  { kw: 'fender flare',        pnp: 'FENDER EXT/FLARE (FRT/RR)',   tap: 'FENDER TRIM/FLARES', utpap: 'FENDER EXTENSION', pyp: 'FENDER EXTENSION', pap: 'FENDER FLARE OR SKIRT', wap: 'FENDER TRIM/ FLARES', upullr: 'FENDER FLARE/TRIM' },
  { kw: 'mudflap',             pnp: 'MUD FLAP (EA)',               tap: 'MUDFLAP', utpap: 'MUD FLAP', pyp: 'MUD FLAP/SPLASH GUARD', pap: 'MUD FLAP OR SPLASH GUARD' },
  { kw: 'emblem',              pnp: 'EMBLEM',                      tap: 'EMBLEM (ANY)', utpap: 'EMBLEM', pyp: 'EMBLEMS', pap: 'EMBLEM', wap: 'EMBLEM (SMALL)', upullr: 'EMBLEM (ANY)' },
  { kw: 'skid plate',          utpap: 'SKID PLATE',                 pyp: 'SKID PLATE', pap: 'SKID PLATE', wap: 'SKID PLATE', upullr: 'SKID PLATE' },
  { kw: 'mirror',              pnp: 'MIRROR-DOOR OUTSIDE(ELEC)',    tap: 'POWER MIRROR - DOOR', utpap: 'DOOR POWER MIRROR', pyp: 'MIRROR (SIDE VIEW)', pap: 'DOOR MIRROR, OUTSIDE ELECTRIC REMOTE', wap: 'DOOR MIRROR POWER REGULAR', upullr: 'MIRROR-DOOR' },
  // --- racks / rails / towing ---
  { kw: 'roof rack',           pnp: 'LUGGAGE RACK',                tap: 'LUGGAGE RACK', utpap: 'LUGGAGE RACK', pyp: 'ROOF RACK ASSEMBLY', pap: 'LUGGAGE RACK', wap: 'LUGGAGE RACK', upullr: 'LUGGAGE/LADDER RACK' },
  { kw: 'roof rail',           pnp: 'LUGGAGE RACK',                tap: 'LUGGAGE RACK', utpap: 'LUGGAGE RACK', pyp: 'ROOF RACK RAIL/ CROSS BAR (EACH)', pap: 'LUGGAGE RACK', wap: 'LUGGAGE RACK', upullr: 'LUGGAGE/LADDER RACK' },
  { kw: 'crossbar',            pnp: 'LUGGAGE RACK',                tap: 'CARGO RACK', utpap: 'LUGGAGE RACK', pyp: 'ROOF RACK RAIL/ CROSS BAR (EACH)', pap: 'LUGGAGE RACK CROSS BAR', upullr: 'LUGGAGE RACH CROSS BAR' },
  { kw: 'cargo rail',          tap: 'CARGO RACK',                   pap: 'TRUCK BED RAIL (EACH)' },
  { kw: 'cargo cover',         pyp: 'CARGO COVER',                  pap: 'CARGO COVER, SHADE TYPE', wap: 'CARGO COVER RETRACTABLE', upullr: 'CARGO COVER' },
  { kw: 'spare tire cover',    pnp: 'SPARE TIRE COVER',             tap: 'SPARE TIRE COVER', utpap: 'SPARE TIRE COVER MET', pap: 'SPARE TIRE COVER', wap: 'FLOOR MAT/ SPARE TIRE COVER', upullr: 'SPARE TIRE COVER' },
  { kw: 'hitch',               pnp: 'TRAILER HITCH W/O BALL',       tap: 'TRAILER HITCH', utpap: 'TRAILERHITCH RECEIVE', pyp: 'TRAILER HITCH', pap: 'TRAILER HITCH RECEIVER', wap: 'TRAILERHITCH RECEIVER', upullr: 'TRAILER HITCH' },
  // --- glass / roofs ---
  { kw: 'panoramic sunroof',   pnp: 'SUN ROOF ASSY',               tap: 'SUNROOF ASSY+MOTOR', utpap: 'SUNROOF/T-TOP', pyp: 'ROOF GLASS PANORAMIC (FULL GLASS ROOF ASSEMBLY)', pap: 'TOP - SUNROOF FRAME WITH GLASS', wap: 'SUNROOF ASSEMBLY ELECTRIC', upullr: 'SUNROOF ASSEMBLY' },
  { kw: 'panoramic',           pnp: 'SUN ROOF ASSY',               tap: 'SUNROOF ASSY+MOTOR', utpap: 'SUNROOF ASSY', pyp: 'ROOF GLASS PANORAMIC (FULL GLASS ROOF ASSEMBLY)', pap: 'TOP - SUNROOF FRAME WITH GLASS', wap: 'SUNROOF ASSEMBLY ELECTRIC', upullr: 'SUNROOF ASSEMBLY' },
  { kw: 'sunroof motor',       pnp: 'SUN ROOF MOTOR',               pap: 'TOP MOTOR, SUNROOF' },
  { kw: 'panoramic roof motor', pnp: 'SUN ROOF MOTOR',              pap: 'TOP MOTOR, SUNROOF' },
  { kw: 'sunroof glass',       pyp: 'ROOF GLASS (SUN ROOF)',        pap: 'TOP - SUNROOF GLASS ONLY', wap: 'SUNROOF GLASS ONLY', upullr: 'SUNROOF GLASS ONLY' },
  { kw: 'sunroof',             pnp: 'SUN ROOF ASSY',               tap: 'SUN ROOF ASSEMBLY', utpap: 'SUNROOF/T-TOP', pyp: 'ROOF GLASS (SUN ROOF)', pap: 'SUNROOF/COVER/SHADE ASSEMBLY W/MOTOR', wap: 'SUNROOF ASSEMBLY ELECTRIC', upullr: 'SUNROOF ASSEMBLY' },
  { kw: 'targa',               pnp: 'T-TOP (EACH)',                 tap: 'SUNROOF/T-TOP', utpap: 'SUNROOF/T-TOP', pyp: 'ROOF GLASS (T-TOP)', pap: 'TOP, T-TOP (EACH)', upullr: 'T-TOPS' },
  { kw: 't-top',               pnp: 'T-TOP (EACH)',                 tap: 'SUNROOF/T-TOP', utpap: 'SUNROOF/T-TOP', pyp: 'ROOF GLASS (T-TOP)', pap: 'TOP, T-TOP (EACH)', upullr: 'T-TOPS' },
  { kw: 'hardtop motor',       pnp: 'TOP-CONVERTIBLE MOTOR',        utpap: 'CONVERTIBLE TOP MOTO', pyp: 'CONVERTIBLE TOP MOTOR', pap: 'TOP - CONVERTIBLE TOP MOTOR', wap: 'CONVERTIBLE TOP MOTOR', upullr: 'CONVERTIBLE TOP OR SLIDING DOOR MOTOR' },
  { kw: 'roof motor',          pnp: 'TOP-CONVERTIBLE MOTOR',        utpap: 'CONVERTIBLE TOP MOTO', pyp: 'CONVERTIBLE TOP MOTOR', pap: 'TOP - CONVERTIBLE TOP MOTOR', wap: 'CONVERTIBLE TOP MOTOR', upullr: 'CONVERTIBLE TOP OR SLIDING DOOR MOTOR' },
  { kw: 'convertible top motor', pnp: 'TOP-CONVERTIBLE MOTOR',      utpap: 'CONVERTIBLE TOP MOTO', pyp: 'CONVERTIBLE TOP MOTOR', pap: 'TOP - CONVERTIBLE TOP MOTOR', wap: 'CONVERTIBLE TOP MOTOR', upullr: 'CONVERTIBLE TOP OR SLIDING DOOR MOTOR' },
  { kw: 'convertible top',     pnp: 'TOP-CONVERTIBLE (NO RAMS)',    tap: 'CONVERTIBLE TOP', utpap: 'CONVERTIBLE TOP CANV', pap: 'TOP - CONVERTIBLE (NO RAMS)', wap: 'CONVERTIBLE TOP ASSEMBLY', upullr: 'CONVERTIBLE TOP' },
  { kw: 'soft top',            pnp: 'TOP-CONVERTIBLE (NO RAMS)',    tap: 'CONVERTIBLE TOP', utpap: 'CONVERTIBLE TOP CANV', pap: 'TOP - CONVERTIBLE (NO RAMS)', wap: 'CONVERTIBLE TOP CLOTH ONLY', upullr: 'CONVERTIBLE TOP' },
  { kw: 'hardtop',             pap: 'HARDTOP W/O DOORS' },
  { kw: 'barn door',           pnp: 'GLASS DOOR (BARE)',            tap: 'DOOR GLASS', utpap: 'DOOR GLASS', pyp: 'GLASS DOOR REAR', pap: 'DOOR GLASS (BARE)', wap: 'DOOR GLASS TRUCK', upullr: 'BACK GLASS' },
  { kw: 'dutch door',          pnp: 'GLASS DOOR (BARE)',            tap: 'DOOR GLASS', utpap: 'DOOR GLASS', pyp: 'GLASS DOOR REAR', pap: 'DOOR GLASS (BARE)', wap: 'DOOR GLASS TRUCK', upullr: 'BACK GLASS' },
  { kw: 'midgate',             pnp: 'GLASS BACK (ONLY)',            tap: 'BACK GLASS (SOLID)', utpap: 'BACK GLASS', pyp: 'GLASS BACK', wap: 'BACK GLASS TRUCK', upullr: 'BACK GLASS' },
  { kw: 'liftgate glass',      pnp: 'GLASS BACK (ONLY)',            tap: 'GLASS HATCH', utpap: 'GLASS HATCH', pyp: 'GLASS BACK', wap: 'BACK GLASS HATCH', upullr: 'BACK GLASS' },
  { kw: 'hatch glass',         pnp: 'GLASS BACK (ONLY)',            tap: 'GLASS HATCH', utpap: 'GLASS HATCH', pyp: 'GLASS BACK', wap: 'BACK GLASS HATCH', upullr: 'BACK GLASS' },
  // --- doors / windows ---
  { kw: 'sliding door motor',  pnp: 'DOOR/GATE MOTOR',             tap: 'SIDE DOOR SLIDE MTR', utpap: 'ELECTRIC MODULE', pyp: 'SLIDING DOOR MOTOR', pap: 'DOOR/HATCH MOTOR, (SLIDING VAN/SUV)', upullr: 'SLIDING DOOR MOTOR' },
  { kw: 'door motor',          pnp: 'DOOR/GATE MOTOR',             tap: 'SIDE DOOR SLIDE MTR', utpap: 'ELECTRIC MODULE', pyp: 'SLIDING DOOR MOTOR', pap: 'DOOR/HATCH MOTOR, (SLIDING VAN/SUV)', upullr: 'SLIDING DOOR MOTOR' },
  { kw: 'liftgate',            pnp: 'DOOR/GATE MOTOR',             tap: 'SIDE DOOR SLIDE MTR', utpap: 'TAIL GATE/ ENDGATE', pyp: 'DECKLID/TAILGATE (BARE)', pap: 'DOOR/HATCH MOTOR, (SLIDING VAN/SUV)' },
  { kw: 'window regulator',    pnp: 'WINDOW REGULATOR W/MOTOR',   tap: 'WINDOW REG W/MOTOR', utpap: 'WINDOW REGULATOR', pyp: 'WINDOW REGULATOR FRONT (ELECTRIC)', pap: 'WINDOW REGULATOR W/MOTOR', wap: 'WINDOW REGULATOR W/ MOTOR', upullr: 'WINDOW REGULATOR POWER' },
  { kw: 'master switch',       pnp: 'SWITCH POWER WINDOW(MULTI)',   tap: 'SWITCH COMBO', utpap: 'WINDOW SWITCH MASTER', pyp: 'DOOR ELECTRICAL SWITCH (MULTI)', pap: 'SWITCH, POWER WINDOW (MULTIPLE) ONLY', wap: 'SWITCH, MASTER WINDOW', upullr: 'SWITCH-MULTI' },
  { kw: 'window switch',       pnp: 'SWITCH POWER WINDOW(MULTI)',   tap: 'SWITCH COMBO', utpap: 'WINDOW SWITCH MASTER', pyp: 'DOOR ELECTRICAL SWITCH (MULTI)', pap: 'SWITCH, POWER WINDOW (MULTIPLE) ONLY', wap: 'SWITCH, MASTER WINDOW', upullr: 'SWITCH-MULTI' },
  { kw: 'door panel',          pnp: 'DOOR TRIM PANEL',              tap: 'INT DOOR PANEL', utpap: 'INTERIOR DOOR PANEL', pyp: 'DOOR PANEL FRONT (BARE)', pap: 'INTERIOR TRIM PANEL (OVER 8IN LONG)', wap: 'TRIM LARGE 18"+', upullr: 'DOOR TRIM PANEL' },
  // --- interior ---
  { kw: 'wood trim',           utpap: 'TRIM PANNEL',                pap: 'INTERIOR TRIM PANEL (OVER 8IN LONG)', wap: 'TRIM MEDIUM 9-18"' },
  { kw: 'interior trim',       utpap: 'TRIM PANNEL',                pap: 'INTERIOR TRIM PANEL (OVER 8IN LONG)', wap: 'TRIM MEDIUM 9-18"' },
  // ambiguous grab-bag names — pinned unmapped so shorter generic keywords
  // ('shifter', 'targa', ...) can't mis-price them
  { kw: 'chrome accessories' },
  { kw: 'whole car' },
  { kw: 'dash pad',            pnp: 'DASH PAD',                    tap: 'DASH PAD', utpap: 'DASH PAD', pyp: 'DASH PAD', pap: 'DASH PAD (OVER 24in LENGTH)', wap: 'DASH PAD', upullr: 'DASH PANEL OR PAD' },
  { kw: 'console lid',         pnp: 'CONSOLE COVER',               tap: 'CONSOLE LID', utpap: 'CONSOLE LID', pyp: 'CENTER CONSOLE', pap: 'CONSOLE LID', wap: 'CONSOLE LID', upullr: 'CONSOLE LID' },
  { kw: 'console',             pnp: 'CONSOLE',                     tap: 'CONSOLE (ANY)', utpap: 'CONSOLE BARE', pyp: 'CENTER CONSOLE', pap: 'CONSOLE (OVER 16in LENGTH)', wap: 'CONSOLE LG 17"+', upullr: 'CONSOLE (ANY)' },
  // --- drivetrain / shifters ---
  { kw: 'shift assembly',      pnp: 'TRANS FLOOR SHIFTER',          tap: 'SHIFTER LEVER ASSY', utpap: 'SHIFTER ARM MANUAL', pyp: 'SHIFT ASSEMBLY', pap: 'TRANSMISSION FLOOR SHIFTER', wap: 'SHIFTER LEVER ASSY', upullr: 'SHIFTER' },
  { kw: 'shifter',             pnp: 'TRANS FLOOR SHIFTER',          tap: 'SHIFTER LEVER ASSY', utpap: 'SHIFTER ARM MANUAL', pyp: 'SHIFT ASSEMBLY', pap: 'TRANSMISSION FLOOR SHIFTER', wap: 'SHIFTER LEVER ASSY', upullr: 'SHIFTER' },
  { kw: 'pedal',               pnp: 'PEDAL BRAKE/CLUTCH ASSY',      tap: 'PEDAL ASSY', utpap: 'CLUTCH PEDAL ASSY', pyp: 'BRAKE/CLUTCH PEDAL BOX', pap: 'PEDAL, BRAKE & CLUTCH ASSEMBLY', wap: 'PEDAL ASSEMBLY', upullr: 'PEDAL(ANY)' },
  { kw: 'transfer case shift motor', pnp: 'TRANSFER CASE MOTOR',    tap: 'TRANSFER CASE MOTOR', utpap: 'TRANSFERCAS ACTUATOR', pyp: 'TRANSFER CASE MOTOR', pap: '4 WHEEL DRIVE ACTUATOR VACUUM OR ELECTRIC', wap: 'TRANSFER CASE MOTOR', upullr: 'TRANSFER CASE SHIFT MOTOR' },
  { kw: 'transfer case motor', pnp: 'TRANSFER CASE MOTOR',         tap: 'TRANSFER CASE MOTOR', utpap: 'TRANSFERCAS ACTUATOR', pyp: 'TRANSFER CASE MOTOR', pap: '4 WHEEL DRIVE ACTUATOR VACUUM OR ELECTRIC', wap: 'TRANSFER CASE MOTOR', upullr: 'TRANSFER CASE SHIFT MOTOR' },
  { kw: 'awd transfer case',   pnp: 'TRANSFER CASE 4X4',           tap: 'TRANSFER CASE (4X4)', utpap: 'TRANSFER CASE ( 4X4)', pyp: 'TRANSFER CASE', pap: 'TRANSFER CASE, 4X4', wap: 'TRANSFER CASE ASSEMBLY', upullr: 'TRANSFER CASE ( 4X4)' },
  { kw: '4wd selector',        pnp: 'SWITCH MISC',                  tap: 'SWITCH SINGLE', utpap: 'ELECTRIC SWITCH', pyp: 'TRANSFER CASE SWITCH (4X4)', pap: 'SWITCH, MISC.', wap: 'SWITCH, SINGLE', upullr: 'SWITCH SINGLE' },
  { kw: 'differential controller', pnp: 'CONTROL MODULE',           tap: 'MODULE', utpap: 'COMPUTER', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL', wap: 'MODULE, BODY CONTROL', upullr: 'ELECT MODULE OTHER THAN ECM' },
  { kw: 'diff',                pnp: 'REAR END CARRIER ASSEMBLY',    tap: 'DIFFERENTIAL', utpap: 'AXLE CARRIER', pyp: 'CARRIER ASSEMBLY', pap: 'DIFFERENTIAL (FRONT, REAR OR 3RD MEMBER DROP-OUT)', wap: 'DIFFERENTIAL CARRIER W/ GEARS', upullr: 'DIFFERENTIAL CARRIER' },
  { kw: 'plenum',              pnp: 'MANIFOLD INTAKE',              tap: 'INTAKE PLENUM', utpap: 'INTAKE MANIFOLD', pyp: 'INTAKE MANIFOLD', pap: 'INTAKE PLENUM, UPPER', wap: 'INTAKE MANIFOLD OEM', upullr: 'INTAKE/EXH MANIFOLD' },
  { kw: 'intake',              pnp: 'MANIFOLD INTAKE',              tap: 'INTAKE MANIFOLD', utpap: 'INTAKE MANIFOLD', pyp: 'INTAKE MANIFOLD', wap: 'INTAKE MANIFOLD OEM', upullr: 'INTAKE/EXH MANIFOLD' },
  { kw: 'intercooler',         pnp: 'INTERCOOLER',                  tap: 'TURBO INTERCOOLER', utpap: 'TURBO INNER COOLER', pyp: 'INTERCOOLER', pap: 'TURBO INTERCOOLER', wap: 'INTERCOOLER', upullr: 'TURBO INTER COOLER' },
  // --- suspension ---
  { kw: 'suspension compressor', pnp: "AIR COMPRESSOR(AIR SUSP'N)", utpap: 'AIR SHOCK PUMP', pyp: 'SUSPENSION COMPRESSOR/PUMP', pap: 'AIR COMPRESSOR (AIR SUSPENSION)', upullr: 'AIR RIDE PUMP' },
  { kw: 'air suspension',      pnp: "AIR COMPRESSOR(AIR SUSP'N)", utpap: 'AIR SHOCK PUMP', pyp: 'SUSPENSION COMPRESSOR/PUMP', pap: 'AIR COMPRESSOR (AIR SUSPENSION)', upullr: 'AIR RIDE PUMP' },
  { kw: 'air spring',          pyp: 'STRUT (AIR)',                  pap: 'SHOCK ABSORBER AIR OR AIRBAG TYPE', wap: 'SUSPENSION AIR BAG', upullr: 'STRUT-AIR BAG TYPE' },
  { kw: 'hood shock',          pnp: 'HATCH OR HOOD SHOCK',          tap: 'HOOD/TRUNK SHOCKS', utpap: 'SHOCK HOOD/LID', pap: 'HATCH OR HOOD SHOCK (MANUAL)', wap: 'HOOD SHOCK', upullr: 'GAS STRUTS' },
  { kw: 'hatch shock',         pnp: 'HATCH OR HOOD SHOCK',          tap: 'HOOD/TRUNK SHOCKS', utpap: 'SHOCK HOOD/LID', pap: 'HATCH OR HOOD SHOCK (MANUAL)', wap: 'HATCH SHOCK', upullr: 'GAS STRUTS' },
  { kw: 'air shock',           pnp: 'SHOCK ABSORBER',               tap: 'SHOCK', utpap: 'SHOCK', pyp: 'SHOCK ABSORBER', pap: 'SHOCK ABSORBER AIR OR AIRBAG TYPE', wap: 'AIR SHOCK ONLY', upullr: 'SHOCK' },
  { kw: 'autoride',            pnp: 'SHOCK ABSORBER',               tap: 'SHOCK', utpap: 'SHOCK', pyp: 'SHOCK ABSORBER', pap: 'SHOCK ABSORBER AIR OR AIRBAG TYPE', wap: 'AIR SHOCK ONLY', upullr: 'SHOCK' },
  { kw: 'shock',               pnp: 'SHOCK ABSORBER',               tap: 'SHOCK', utpap: 'SHOCK', pyp: 'SHOCK ABSORBER', pap: 'SHOCK ABSORBER (REGULAR)', wap: 'SHOCK ABSORBER NO SPRING', upullr: 'SHOCK' },
  // --- wheels ---
  { kw: 'wheels (set',         pnp: 'WHEEL & TIRE CUSTOM SET 4',    utpap: 'PREMI WHEEL/TIRE SET', pyp: 'TIRE/WHEEL SET' },
  // --- brakes ---
  { kw: 'brembo',              pnp: 'BRAKE CALIPER',                tap: 'BRAKE CALIPER', utpap: 'BRAKE CALIPER 2-4 PI', pyp: 'BRAKE CALIPER', pap: 'BRAKE CALIPER', wap: 'CALIPER 4 PISTON', upullr: 'BRAKE CALIPER' },
  { kw: 'brake caliper',       pnp: 'BRAKE CALIPER',                tap: 'BRAKE CALIPER', utpap: 'BRAKE CALIPER 2-4 PI', pyp: 'BRAKE CALIPER', pap: 'BRAKE CALIPER', wap: 'CALIPER 1 PISTON', upullr: 'BRAKE CALIPER' },
  { kw: 'caliper',             pnp: 'BRAKE CALIPER',                tap: 'BRAKE CALIPER', utpap: 'BRAKE CALIPER 2-4 PI', pyp: 'BRAKE CALIPER', pap: 'BRAKE CALIPER', wap: 'CALIPER 1 PISTON', upullr: 'BRAKE CALIPER' },
  // --- steering ---
  { kw: 'steering wheel',      pnp: 'STEERING WHEEL',               tap: 'STEERNG WHL W/SWITCH', utpap: 'STEERING WHEEL', pyp: 'STEERING WHEEL', pap: 'STEERING WHEEL', wap: 'STEERING WHEEL NO AIR BAG', upullr: 'STEERING WHEEL' },
  // --- modules / electronics ---
  { kw: 'sliding door control', pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'COMPUTER', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL', wap: 'MODULE, BODY CONTROL', upullr: 'ELECT MODULE OTHER THAN ECM' },
  { kw: 'control module',      pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'COMPUTER', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL', wap: 'MODULE, BODY CONTROL', upullr: 'ELECT MODULE OTHER THAN ECM' },
  { kw: 'radar',               pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'COMPUTER', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL', wap: 'MODULE, BODY CONTROL', upullr: 'ELECT MODULE OTHER THAN ECM' },
  { kw: 'camera',              pnp: 'CONTROL MODULE',              tap: 'REVERSE CAMERA', utpap: 'COMPUTER', pyp: 'SENSOR CAMERAS', pap: 'CAMERA, ON BOARD OR BACK UP', wap: 'CAMERA', upullr: 'BACKUP CAMERA' },
  { kw: 'module',              pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'COMPUTER', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL', wap: 'MODULE, BODY CONTROL', upullr: 'ELECT MODULE OTHER THAN ECM' },
  { kw: 'wireless charging',   pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'ELECTRIC MODULE', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL', wap: 'MODULE, BODY CONTROL', upullr: 'ELECT MODULE OTHER THAN ECM' },
  { kw: 'charging pad',        pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'ELECTRIC MODULE', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL', wap: 'MODULE, BODY CONTROL', upullr: 'ELECT MODULE OTHER THAN ECM' },
  // --- misc ---
  { kw: 'cable',               tap: 'CABLE (ANY)',                  utpap: 'SHIFTER CABLE', pyp: 'CABLE', pap: 'CABLE - BRAKE/CLUTCH/SHIFTER/THROTTLE/RELEASE', wap: 'CABLE (MISCELLANEOUS)', upullr: 'MISC CABLES' },
  { kw: 'wiper motor',         pnp: 'WINDSHIELD WIPER MOTOR',      tap: 'WIPER MOTOR', utpap: 'WIPER MOTOR', pyp: 'ELECTRIC WIPER MOTOR, WINDSHIELD', pap: 'WINDSHIELD WIPER MOTOR', wap: 'WIPER MOTOR', upullr: 'ELECTRIC MOTORS' },
  { kw: 'actuator',            pnp: 'ACUATOR (4X4)',               tap: 'ACTUATOR', utpap: 'TRANSFERCAS ACTUATOR', pyp: 'ACTUATOR', pap: 'ACTUATOR', wap: '4X4 ACTUATOR' },
  { kw: 'switch',              pnp: 'SWITCH MISC',                  tap: 'SWITCH SINGLE', utpap: 'ELECTRIC SWITCH', pap: 'SWITCH, MISC.', wap: 'SWITCH, SINGLE', upullr: 'SWITCH SINGLE' },
];

/* Strict provenance: each chain's price list applies ONLY to that chain's own
 * yards, and there is no estimated fallback. Returns {cost:null, source:'none'}
 * whenever the yard's real price list doesn't cover the part — callers then
 * show "check yard price list" and compute resale-only ranges. */
/* Memoized: called O(vehicles x parts) during sorting/rendering; the distinct
 * (part, location) pairs number only a few thousand. Cleared when price lists
 * finish loading so early misses don't stick. */
const _yardCostMemo = new Map();
function lookupYardCost(partName, location) {
  const memoKey = partName + '|' + (location || '');
  const hit = _yardCostMemo.get(memoKey);
  if (hit !== undefined) return hit;
  const result = _lookupYardCostUncached(partName, location);
  _yardCostMemo.set(memoKey, result);
  return result;
}

function _lookupYardCostUncached(partName, location) {
  const lower = partName.toLowerCase();
  const loc = (location || '').toLowerCase();
  let bestMatch = null;
  let bestLen = 0;
  for (const entry of PART_KEYWORD_MAP) {
    if (lower.includes(entry.kw) && entry.kw.length > bestLen) {
      bestMatch = entry;
      bestLen = entry.kw.length;
    }
  }
  const none = { cost: null, source: 'none', yardName: null };
  if (!bestMatch) return none;

  if (loc.startsWith('tear-a-part')) {
    const t = tapPricing[bestMatch.tap];
    return t ? { cost: parseFloat(t.price), source: 'tap', yardName: t.description } : none;
  }
  if (loc.startsWith('pick-n-pull')) {
    const p = pnpPricing[bestMatch.pnp];
    return p ? { cost: parseFloat(p.price), source: 'pnp', yardName: p.description } : none;
  }
  if (loc.startsWith('utah pic-a-part')) {
    const u = utpapPricing[bestMatch.utpap];
    return u ? { cost: parseFloat(u.price), source: 'utpap', yardName: u.description } : none;
  }
  if (loc.startsWith('pick your part')) {
    const yard = pypPricing[location];
    const e = yard && bestMatch.pyp ? yard[bestMatch.pyp] : null;
    return e ? { cost: parseFloat(e.price), source: 'pyp', yardName: bestMatch.pyp } : none;
  }
  if (loc.startsWith('pull-a-part')) {
    const yard = papPricing[location];
    const e = yard && bestMatch.pap ? yard[bestMatch.pap] : null;
    return e ? { cost: parseFloat(e.price), source: 'pap', yardName: bestMatch.pap } : none;
  }
  // Wrench-A-Part yard names aren't all prefix-consistent ("Primo Wrench-A-Part
  // - Del Valle", "Roosevelt Wrench-A-Part - San Antonio"), so match anywhere.
  if (loc.includes('wrench-a-part')) {
    const yard = wapPricing[location];
    const e = yard && bestMatch.wap ? yard[bestMatch.wap] : null;
    return e ? { cost: parseFloat(e.price), source: 'wap', yardName: bestMatch.wap } : none;
  }
  if (loc.startsWith('u-pull-r')) {
    const u = bestMatch.upullr ? upullrPricing[bestMatch.upullr] : null;
    return u ? { cost: parseFloat(u.price), source: 'upullr', yardName: u.description } : none;
  }
  return none;
}

/* ===== LIVE INVENTORY ===== */
let liveInventory = [];
let liveLoaded = false;
let liveScrapedAt = null;

function escapeHtml(str) {
  if (str == null || str === '') return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function normalizeVinForDedupe(vin) {
  if (!vin || typeof vin !== 'string') return '';
  return vin.trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
}

function annotateVinDuplicates(vehicles) {
  const counts = {};
  for (const v of vehicles) {
    const nv = normalizeVinForDedupe(v.vin);
    if (nv.length === 17) counts[nv] = (counts[nv] || 0) + 1;
  }
  for (const v of vehicles) {
    const nv = normalizeVinForDedupe(v.vin);
    v.vinDuplicate = nv.length === 17 && (counts[nv] || 0) > 1;
  }
}

/** Full VIN in UI when present (yards often provide 17 chars). */
/* Single inline SVG icon set — one stroke weight, currentColor, sized by
 * font-size via the .ico class. No emoji in the interface. */
const ICON = {
  tag: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z"/><circle cx="7.5" cy="7.5" r=".5" fill="currentColor"/></svg>',
  pin: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>',
  heart: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 14c1.5-1.46 3-3.2 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.04 3 5.5l7 7Z"/></svg>',
  copy: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',
  bell: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>',
  check: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>',
  x: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg>',
  lock: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
  chev: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>',
  share: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v13M8 7l4-4 4 4"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/></svg>',
};

// Masks rendered under the blur for locked rows. Deliberately NOT plausible
// fake data: if someone strips the blur in dev tools they see obvious bullet
// masks, not made-up part names/prices that could read as faked data.
const LOCKED_PART_PLACEHOLDERS = [
  '\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022 \u2022\u2022\u2022\u2022\u2022 (\u2022\u2022\u2022\u2022)',
  '\u2022\u2022\u2022\u2022\u2022 \u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022',
  '\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022 \u2022\u2022\u2022\u2022',
  '\u2022\u2022\u2022\u2022\u2022\u2022 \u2022\u2022\u2022\u2022\u2022\u2022\u2022 (\u2022\u2022\u2022)',
  '\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022',
  '\u2022\u2022\u2022\u2022\u2022\u2022 \u2022\u2022\u2022\u2022\u2022\u2022\u2022',
];
const LOCKED_PRICE_MASK = '$\u2022\u2022\u2022&ndash;$\u2022\u2022\u2022';

function vinMetaHtml(v) {
  if (!v.vin || !String(v.vin).trim()) return '';
  const show = String(v.vin).trim();
  // Quiet metadata, not badge soup: VIN + icon copy button, then plain dim
  // text notes. Only a genuine warning (VIN/listing mismatch) gets color.
  const dup = v.vinDuplicate
    ? ' <span class="meta-note" title="Same VIN appears at more than one yard in this file">also at another yard</span>'
    : '';
  const copyBtn = show.length >= 11
    ? `<button type="button" class="btn-copy-vin" data-vin="${escapeHtml(show)}" title="Copy VIN">${ICON.copy}</button>`
    : '';
  let vpic = '';
  const vt = v.vpicTrim != null ? String(v.vpicTrim).trim() : '';
  if (vt && (v.vpicTrimQuality === 'usable' || v.vpicDecodeWell === true)) {
    vpic = ` <span class="meta-note" title="Specific trim decoded from the VIN via NHTSA VPIC — used to confirm trim-gated parts">trim: ${escapeHtml(vt)} (VIN-confirmed)</span>`;
  }
  let mismatch = '';
  if (v.vpicMismatch) {
    mismatch = ` <span class="meta-warn" title="The VIN's factory decode disagrees with the yard listing — the lot sign may be mislabeled. The VIN is used for matching; verify at the yard.">${escapeHtml(v.vpicMismatch)}</span>`;
  }
  return ` &middot; VIN <span class="mono-vin">${escapeHtml(show)}</span>${copyBtn}${dup}${vpic}${mismatch}`;
}

/* No bulk export at any tier: inventory goes stale in days, but the part
 * values attached to every row don't — a one-click download of them is a
 * permanent copy of the product. Deliberate decision, not an oversight. */

async function loadAllPricing() {
  // All chain price lists fetch in parallel (this used to be a serial
  // waterfall queued in front of the big inventory fetch). Each is optional.
  const grab = async (url, apply) => {
    try {
      const resp = await fetch(url);
      if (resp.ok) apply(await resp.json());
    } catch (e) { /* price list not available */ }
  };
  await Promise.all([
    grab('data/picknpull_pricing.json', d => d.forEach(p => { pnpPricing[p.description] = p; })),
    grab('data/utpap_pricing.json', d => d.forEach(p => { utpapPricing[p.description] = p; })),
    grab('data/tearapart_pricing.json', d => d.forEach(p => { tapPricing[p.description] = p; })),
    grab('data/pyp_pricing.json', d => { pypPricing = d; }),
    grab('data/pap_pricing.json', d => { papPricing = d; }),
    grab('data/wap_pricing.json', d => { wapPricing = d; }),
    grab('data/upullr_pricing.json', d => d.forEach(p => { upullrPricing[p.description] = p; })),
  ]);
  _yardCostMemo.clear();
}

/* Expand a fetched inventory payload into app state + render. `quiet` is the
 * background-refresh path after cached data was already shown: state is
 * swapped, but the grid only re-renders immediately if the user is still near
 * the top and hasn't opened anything — otherwise the fresh data shows on
 * their next interaction (every control calls renderLive). */
function applyInventory(raw, { quiet = false } = {}) {
  parseInventoryPayload(raw);
  annotateVinDuplicates(liveInventory);
  liveLoaded = true;
  updateCoverageCounts();
  _makeScopeKey = null;   // data changed — force the scoped rebuild
  refreshScopedInventory();
  populateWatchOptions();
  updateStaleBanner();
  if (!quiet) {
    applyShareHash();
    renderLive();
    checkAndNotify();
    updateAlertsBadge();
    if (document.getElementById('tab-yards').classList.contains('active')) renderYards();
  } else if (window.scrollY < 400 && !document.querySelector('#live-grid details[open]')) {
    renderLive();
  }
}

function parseInventoryPayload(raw) {
  {
    if (raw && raw.schemaVersion === 2 && Array.isArray(raw.vehicles)) {
      // v2 compact format: expand lookup-table rows into full vehicle objects.
      const yards = raw.yards || [];
      const partSets = raw.partSets || [];
      const vpic = raw.vpic || {};
      liveInventory = raw.vehicles.map((r, i) => {
        const y = yards[r[7]] || [];
        const parts = r[8] >= 0 ? (partSets[r[8]] || []) : [];
        const v = {
          id: r[0], vin: r[1], year: r[2], make: r[3], model: r[4], row: r[5],
          dateAdded: r[6], location: y[0] || '', city: y[1] || '', state: y[2] || '',
          lat: y[3], lng: y[4], utpapPremium: !!r[10],
          hasMatch: parts.length > 0, maxValue: r[9] || 0,
          displayName: `${r[3]} ${r[4]}`.trim(), topParts: parts,
        };
        if (y[5] != null) { v.yardAvgLifespan = y[5]; v.yardLifespanBasis = y[6] || 'all'; }
        const vp = vpic[String(i)];
        if (vp) {
          v.vpicTrim = vp[0]; v.vpicTrimQuality = vp[1];
          v.vpicDecodeWell = vp[1] === 'usable';
          if (vp[2]) v.vpicSeries = vp[2];
          if (vp[3]) v.vpicDriveType = vp[3];
          if (vp[4]) v.vpicMismatch = vp[4];
        }
        return v;
      });
      liveScrapedAt = raw.scrapedAt || null;
      if (raw.pricesLastReviewed) {
        const d = new Date(raw.pricesLastReviewed + 'T12:00:00Z');
        if (!isNaN(d)) {
          document.getElementById('prices-reviewed').textContent =
            ` Value ranges last reviewed ${d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}.`;
        }
      }
    } else if (Array.isArray(raw)) {
      liveInventory = raw;
      liveScrapedAt = null;
    } else if (raw && Array.isArray(raw.vehicles)) {
      liveInventory = raw.vehicles;
      liveScrapedAt = raw.scrapedAt || null;
    } else {
      liveInventory = [];
      liveScrapedAt = null;
    }
  }
}

const DATA_CACHE = 'jh-data-v1';

/* ===== PHOTO / SPEC ENRICHMENT (lazy shard) =====
 * data/vehicle_extras.json maps vehicle id -> [photoCode, color, engine, trans].
 * It loads in parallel with the inventory and is never on the critical path:
 * cards render photo-less first if it hasn't arrived, then hydrate.
 *
 * PHOTO POLICY: a photo renders ONLY when the chain whose car it is hosts the
 * image itself (same-chain, hotlinked — their server serves it, we never
 * download/rehost/proxy). Each chain has a kill switch below so photos can be
 * turned off with one flag if a chain ever objects. Pick-n-Pull photo codes
 * ("r..." — Row52-hosted, Row52-watermarked, a competitor's assets) are never
 * rendered even if present in older data. */
const PHOTO_SOURCES = {
  // LKQ hosts these on its own CDN (cdn.pypapps.com) with LKQ's PYP watermark.
  // 2026-09 owner decision (legal caution): ALL chain-sourced photos are OFF —
  // LKQ's watermark prompted a blanket no-chain-photos call. URL capture and
  // this rendering plumbing stay intact so we can revisit (e.g. user-submitted
  // photos); flipping `enabled` back on is the only change needed.
  pyp: {
    enabled: false,
    label: 'Photo: LKQ Pick Your Part',
    url: id => 'https://cdn.pypapps.com/carbuy/CAR-FRONT-LEFT_' + id
      + '_front_left_corner.jpg?quality=70&w=640&h=427&mode=crop&format=webp',
  },
};
let vehicleExtras = null;

function photoInfo(code) {
  if (!code || code[0] !== 'p') return null; // 'r' (Row52) codes: excluded by policy
  const src = PHOTO_SOURCES.pyp;
  if (!src || !src.enabled) return null;
  return { url: src.url(code.slice(1)), label: src.label };
}
function extrasFor(v) {
  return (vehicleExtras && vehicleExtras[String(v.id)]) || null;
}
/* Confirmed manual transmission — from the VIN decode (or a chain feed's trans
 * field) carried in the extras shard. Honest rule: only ever true when the
 * data says "Manual"; never inferred, and automatics get no badge at all. */
function isConfirmedManual(v) {
  const ex = extrasFor(v);
  const t = ex && ex[3] ? String(ex[3]) : '';
  return /manual/i.test(t) && !/automated/i.test(t);
}

fetch('data/vehicle_extras.json')
  .then(r => (r.ok ? r.json() : null))
  .then(d => {
    if (!d || !d.extras) return;
    vehicleExtras = d.extras;
    hydratePhotos();
  })
  .catch(() => { /* enrichment is optional */ });

/* ===== SALE DAYS (chain sale calendars -> data/sale_events.json) =====
 * Events come from each chain's own published calendar (Pick-n-Pull events
 * API, PYP deals pages) plus hand-verified manual entries. An event with
 * yard=null is chain-wide. Free feature for everyone — sale days are when
 * normal people plan yard trips, not a value leak. */
let saleEvents = [];
fetch('data/sale_events.json')
  .then(r => (r.ok ? r.json() : null))
  .then(d => {
    if (!d || !d.events || !d.events.length) return;
    saleEvents = d.events;
    if (liveLoaded) {
      renderLive();
      if (document.getElementById('tab-yards').classList.contains('active')) renderYards();
    }
  })
  .catch(() => { /* sale calendar is optional enrichment */ });

const SALE_LOOKAHEAD_DAYS = 14;

/** Active or upcoming (≤14d) sale for a yard, else null. */
function saleForYard(location) {
  if (!saleEvents.length || !location) return null;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const horizon = new Date(today.getTime() + SALE_LOOKAHEAD_DAYS * 86400000);
  let best = null;
  for (const ev of saleEvents) {
    const start = new Date(ev.start + 'T00:00:00');
    const end = new Date(ev.end + 'T23:59:59');
    if (end < today || start > horizon) continue;
    if (ev.yard ? ev.yard !== location : !location.startsWith(ev.chain)) continue;
    if (!best || start < new Date(best.start + 'T00:00:00')) best = ev;
  }
  return best;
}

function saleDateLabel(ev) {
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const start = new Date(ev.start + 'T00:00:00');
  const end = new Date(ev.end + 'T00:00:00');
  const fmt = d => d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  // same-month ranges collapse: "Sep 25–27", not "Sep 25–Sep 27"
  const fmtEnd = d => d.getMonth() === start.getMonth()
    ? d.toLocaleDateString(undefined, { day: 'numeric' }) : fmt(d);
  if (start <= today && end >= today) {
    return +start === +end ? 'today' : `now &ndash; ${fmt(end)}`;
  }
  return +start === +end ? fmt(start) : `${fmt(start)}&ndash;${fmtEnd(end)}`;
}

function saleBadgeHtml(location) {
  const ev = saleForYard(location);
  if (!ev) return '';
  const label = (ev.pct ? ev.pct + '% off ' : 'Sale ') + saleDateLabel(ev);
  return ` <span class="sale-pill" title="${escapeHtml(ev.title || 'Sale')} &mdash; from the chain's published sale calendar">${ICON.tag}${label}</span>`;
}

/** Live-tab strip: sales at yards inside the current radius. */
function renderSaleStrip() {
  const strip = document.getElementById('sale-strip');
  if (!strip) return;
  if (!saleEvents.length || !liveLoaded || !activeZipCoords) { strip.style.display = 'none'; return; }
  const radius = effectiveRadiusMi();
  const rows = [];
  const seen = new Set();
  for (const y of buildYardDirectory()) {
    const ev = saleForYard(y.location);
    if (!ev) continue;
    const d = (y.lat != null && y.lng != null)
      ? haversineMiles(activeZipCoords.lat, activeZipCoords.lng, y.lat, y.lng) : null;
    if (radius && (d == null || d > radius)) continue;
    const key = y.location + ev.start;
    if (seen.has(key)) continue;
    seen.add(key);
    rows.push({ y, ev, d });
  }
  if (!rows.length) { strip.style.display = 'none'; return; }
  rows.sort((a, b) => (a.ev.start < b.ev.start ? -1 : 1) || ((a.d ?? 1e9) - (b.d ?? 1e9)));
  const shown = rows.slice(0, 3);
  strip.innerHTML = shown.map(({ y, ev, d }) =>
    `<button type="button" class="sale-strip-row" data-loc="${escapeHtml(y.location)}">
       <span class="sale-pill">${ev.pct ? ev.pct + '% off' : 'Sale'}</span>
       <span class="sale-strip-yard">${escapeHtml(y.location)}</span>
       <span class="sale-strip-when">${saleDateLabel(ev)}${d != null ? ' &middot; ' + Math.round(d) + ' mi' : ''}</span>
     </button>`).join('')
    + (rows.length > shown.length ? `<div class="sale-strip-more">+${rows.length - shown.length} more sale${rows.length - shown.length > 1 ? 's' : ''} in range</div>` : '');
  strip.style.display = '';
}
document.getElementById('sale-strip').addEventListener('click', e => {
  const row = e.target.closest('.sale-strip-row');
  if (row) viewYardInLive(row.dataset.loc);
});

/* Insert photos into already-rendered cards (extras arrived after render). */
function hydratePhotos() {
  document.querySelectorAll('#live-grid .car-card[data-eid]').forEach(card => {
    if (card.querySelector('.car-photo-wrap')) return;
    const ex = vehicleExtras && vehicleExtras[card.dataset.eid];
    const info = ex && ex[0] ? photoInfo(ex[0]) : null;
    if (!info) return;
    const wrap = document.createElement('div');
    wrap.className = 'car-photo-wrap';
    wrap.innerHTML = '<img class="car-photo" loading="lazy" alt="" onerror="this.parentNode.remove()">'
      + '<span class="photo-credit"></span>';
    wrap.querySelector('img').src = info.url;
    wrap.querySelector('.photo-credit').textContent = info.label;
    card.prepend(wrap);
  });
}
const INVENTORY_URL = 'data/inventory_live.json';

async function loadLiveInventory() {
  // Pricing files load concurrently with the inventory (they used to be a
  // serial waterfall in front of the 4MB fetch). Rendering needs them for
  // pull costs, so each render path awaits this promise before first paint
  // of cards.
  const pricingReady = loadAllPricing();

  // API mode (feature-flagged, see api.js): load tier-aware shards from the
  // backend instead of the public static file. Falls back to static on error.
  if (window.YSApi && YSApi.enabled()) {
    try {
      const raw = await YSApi.fetchInventory();
      await pricingReady;
      applyInventory(raw);
      return;
    } catch (e) {
      console.log('API inventory failed, falling back to static:', e && e.message);
    }
  }

  // Repeat visits: render instantly from the Cache API copy, then revalidate
  // in the background. (The service worker deliberately skips this file.)
  let shownScrapedAt = null;
  let cache = null;
  try {
    if ('caches' in window) {
      cache = await caches.open(DATA_CACHE);
      const hit = await cache.match(INVENTORY_URL);
      if (hit) {
        const raw = await hit.json();
        await pricingReady;
        applyInventory(raw);
        shownScrapedAt = raw.scrapedAt || 'unknown';
      }
    }
  } catch (e) { /* cached copy unreadable — fall through to network */ }

  try {
    const resp = await fetch(INVENTORY_URL, shownScrapedAt ? { cache: 'no-cache' } : {});
    if (!resp.ok) throw new Error('not found');
    if (cache) { try { await cache.put(INVENTORY_URL, resp.clone()); } catch (e) { /* quota */ } }
    const raw = await resp.json();
    if (shownScrapedAt && (raw.scrapedAt || 'unknown') === shownScrapedAt) return; // nothing new
    await pricingReady;
    applyInventory(raw, { quiet: !!shownScrapedAt });
  } catch (e) {
    if (shownScrapedAt) return; // cached data already on screen — stay quiet
    liveLoaded = false;
    document.getElementById('live-stats-bar').innerHTML = '';
    document.getElementById('live-grid').innerHTML = `
      <div class="empty-state" style="grid-column: 1/-1;">
        <h3>Couldn't load inventory</h3>
        <p>The inventory data didn't load. Check your connection and pull to refresh (or tap Refresh data in Filters).</p>
        <p style="margin-top:0.75rem;">If this keeps happening, the latest scan may still be publishing &mdash; try again in a few minutes.</p>
      </div>`;
  }
}

/* Coverage transparency: the yard count shown in the zip banner / footer is
 * computed from the live data, never hardcoded. */
function coverageYardCount() {
  return new Set(liveInventory.map(v => v.location).filter(Boolean)).size;
}
function updateCoverageCounts() {
  const n = coverageYardCount();
  if (!n) return;
  document.querySelectorAll('.coverage-count').forEach(el => { el.textContent = n; });
  startHeadTicker();
}

/* Header data plate: instead of one static line, the spec line under the
 * wordmark stamps through a rotation of real numbers pulled from the live
 * data — like reading fields off an equipment plate one at a time. Every
 * fact is computed, never hardcoded. */
let _headTickerTimer = null;
let _headTickerIdx = 0;
function headTickerFacts() {
  const facts = [];
  const cars = liveInventory.length;
  const n = coverageYardCount();
  if (cars) facts.push(`${cars.toLocaleString()} CARS ON ROW`);
  if (n) facts.push(`${n} YARDS COAST TO COAST`);
  const weekAgo = Date.now() - 7 * 86400000;
  const fresh = liveInventory.reduce((k, v) => k + ((Date.parse(v.dateAdded) || 0) >= weekAgo ? 1 : 0), 0);
  if (fresh) facts.push(`${fresh.toLocaleString()} SET OUT THIS WEEK`);
  if (activeZipCoords) {
    const r = effectiveRadiusMi();
    const near = new Set(liveInventory
      .filter(v => v.lat != null && haversineMiles(activeZipCoords.lat, activeZipCoords.lng, v.lat, v.lng) <= r)
      .map(v => v.location)).size;
    if (near) facts.push(`${near} YARD${near === 1 ? '' : 'S'} IN YOUR RANGE`);
  }
  const ts = Date.parse(liveScrapedAt || '');
  if (ts) {
    const hrs = Math.max(0, Math.round((Date.now() - ts) / 3600000));
    facts.push(hrs < 1 ? 'SCANNED UNDER AN HOUR AGO'
      : hrs < 48 ? `SCANNED ${hrs}H AGO`
      : `SCANNED ${Math.round(hrs / 24)}D AGO`);
  }
  return facts;
}
function startHeadTicker() {
  const spec = document.getElementById('head-spec');
  if (!spec) return;
  const show = () => {
    const facts = headTickerFacts();
    if (!facts.length) return;
    _headTickerIdx = _headTickerIdx % facts.length;
    spec.classList.add('spec-swap');
    setTimeout(() => {
      spec.textContent = facts[_headTickerIdx];
      spec.classList.remove('spec-swap');
      _headTickerIdx += 1;
    }, 260);
  };
  if (_headTickerTimer) return;         // already running; facts refresh per tick
  const facts = headTickerFacts();
  if (facts.length) { spec.textContent = facts[0]; _headTickerIdx = 1; }
  _headTickerTimer = setInterval(show, 5000);
}

/* One-tap actions for the out-of-range empty state. */
function jhWidenRadius(mi) {
  const sel = document.getElementById('live-radius');
  const opts = [...sel.options].map(o => parseFloat(o.value)).filter(v => !isNaN(v));
  const fit = opts.find(v => v >= mi);
  // Nothing wide enough means "any distance", which is nationwide — Pro only.
  if (fit == null && !isPro()) { openUpgradeSheet('widen-radius-nationwide'); return; }
  sel.value = fit != null ? String(fit) : '';
  renderLive();
}
function jhShowNationwide() {
  if (!isPro()) { openUpgradeSheet('nationwide-browse'); return; }
  document.getElementById('live-radius').value = '';
  renderLive();
}

/* Free tier is always radius-scoped: no location means no cars, and "Any
 * distance" (nationwide) is a Pro feature. Pro gets the raw select value,
 * where empty = unlimited. */
const FREE_MAX_RADIUS_MI = 250;
function effectiveRadiusMi() {
  const raw = parseFloat(document.getElementById('live-radius').value) || null;
  if (isPro()) return raw;
  return raw ? Math.min(raw, FREE_MAX_RADIUS_MI) : FREE_MAX_RADIUS_MI;
}

/* Feed placeholder pseudo-makes that would look broken in a picker
 * ("Misc" rows are Pull-A-Part's "1977 CAR" / "Commercial Truck" stubs).
 * The cars stay browsable under "All makes"; they just don't get a
 * dropdown entry. */
const JUNK_MAKES = new Set(['misc', 'miscellaneous', 'unknown', 'other', '']);

/* Vehicles inside the current center+radius — the population for the Make
 * and Model dropdowns, so the picker never offers a brand with zero cars
 * near you. Cached per scope, same pattern as the yard filter. */
let _makeScopeKey = null;
let _scopedVehicles = [];
function refreshScopedInventory() {
  const radius = effectiveRadiusMi();
  const key = activeZipCoords
    ? activeZipCoords.lat + ',' + activeZipCoords.lng + ',' + (radius || 'any')
    : 'none';
  if (key === _makeScopeKey) return;
  _makeScopeKey = key;
  _scopedVehicles = !activeZipCoords ? [] : liveInventory.filter(v => {
    if (!radius) return true;   // "Any distance" (Pro) = nationwide
    const d = vehicleDistanceMi(v);
    return d != null && d <= radius;
  });
  populateLiveMakeFilter();
}

function populateLiveMakeFilter() {
  const sel = document.getElementById('live-filter-make');
  const prev = sel.value;
  const counts = new Map();
  for (const v of _scopedVehicles) {
    if (!v.make || JUNK_MAKES.has(v.make.toLowerCase())) continue;
    counts.set(v.make, (counts.get(v.make) || 0) + 1);
  }
  sel.innerHTML = '<option value="">All makes</option>';
  const pro = isPro();
  [...counts.keys()].sort().forEach(m => {
    const opt = document.createElement('option');
    opt.value = m;
    // Inventory counts are intel — Pro sees them, free gets a clean list.
    opt.textContent = pro ? m + ' (' + counts.get(m) + ')' : m;
    sel.appendChild(opt);
  });
  sel.value = counts.has(prev) ? prev : '';
  populateModelFilter();
  populateYearFilters();
}

/* Model cascade, multi-select: the panel only ever lists the chosen make's
 * models that exist within the current radius — picked from real inventory so
 * there's nothing to misspell. Check any number of models (e.g. Tacoma +
 * 4Runner + Land Cruiser); empty selection = all models. Disabled until a
 * make is chosen. */
let selectedModels = new Set();

function populateModelFilter() {
  const make = document.getElementById('live-filter-make').value;
  const btn = document.getElementById('live-filter-model-btn');
  if (!make) {
    selectedModels.clear();
    btn.disabled = true;
    closeModelPanel();
    updateModelBtnLabel();
    return;
  }
  btn.disabled = false;   // location gate lives in updateFilterAvailability
  const counts = new Map();
  for (const v of _scopedVehicles) {
    if (v.make === make && v.model) counts.set(v.model, (counts.get(v.model) || 0) + 1);
  }
  // Drop selections that no longer exist in scope (make change, radius change).
  for (const m of [...selectedModels]) if (!counts.has(m)) selectedModels.delete(m);
  renderModelList(counts);
  updateModelBtnLabel();
}

let _modelCounts = new Map();
function renderModelList(counts) {
  if (counts) _modelCounts = counts;
  const list = document.getElementById('live-filter-model-list');
  const q = (document.getElementById('live-filter-model-search').value || '').trim().toLowerCase();
  const pro = isPro();
  const models = [...(_modelCounts).keys()].sort()
    .filter(m => !q || m.toLowerCase().includes(q));
  list.innerHTML = models.length ? models.map(m => `
    <label class="multi-select-row">
      <input type="checkbox" data-model="${escapeHtml(m)}" ${selectedModels.has(m) ? 'checked' : ''}>
      <span>${escapeHtml(m)}${pro ? ` <small>(${_modelCounts.get(m)})</small>` : ''}</span>
    </label>`).join('')
    : '<div class="multi-select-empty">No models match</div>';
}

function updateModelBtnLabel() {
  const btn = document.getElementById('live-filter-model-btn');
  btn.textContent = !selectedModels.size ? 'All models'
    : selectedModels.size === 1 ? [...selectedModels][0]
    : `${selectedModels.size} models`;
  btn.classList.toggle('has-selection', selectedModels.size > 0);
}

function closeModelPanel() {
  document.getElementById('live-filter-model-panel').style.display = 'none';
}

/* Optional year range, populated from the years actually in inventory
 * (newest first) — no typing, no typos. */
function populateYearFilters() {
  const years = [...new Set(liveInventory.map(v => v.year).filter(Boolean))].sort((a, b) => b - a);
  for (const [id, label] of [['live-filter-year-min', 'From'], ['live-filter-year-max', 'To']]) {
    const sel = document.getElementById(id);
    const prev = sel.value;
    sel.innerHTML = `<option value="">${label}</option>`;
    years.forEach(y => {
      const opt = document.createElement('option');
      opt.value = y;
      opt.textContent = y;
      sel.appendChild(opt);
    });
    sel.value = prev && years.includes(+prev) ? prev : '';
  }
}

/* The Yard dropdown only ever lists yards inside the chosen radius of the
 * current center, nearest first — a national wall of yard names is useless
 * and leaks coverage the free tier shouldn't browse. Rebuilds only when the
 * center or radius actually changes. */
let _yardScopeKey = null;
function populateYardFilter() {
  const locSel = document.getElementById('live-filter-location');
  const radius = effectiveRadiusMi();
  const key = activeZipCoords
    ? activeZipCoords.lat + ',' + activeZipCoords.lng + ',' + (radius || 'any')
    : 'none';
  if (key === _yardScopeKey) return;
  _yardScopeKey = key;
  const prev = locSel.value;

  const yards = new Map();
  for (const v of liveInventory) {
    if (!v.location) continue;
    let y = yards.get(v.location);
    if (!y) { y = { count: 0, lat: null, lng: null }; yards.set(v.location, y); }
    y.count++;
    if (y.lat == null && v.lat != null) { y.lat = v.lat; y.lng = v.lng; }
  }
  let rows = [...yards.entries()].map(([name, y]) => ({
    name,
    count: y.count,
    dist: (activeZipCoords && y.lat != null)
      ? haversineMiles(activeZipCoords.lat, activeZipCoords.lng, y.lat, y.lng)
      : null,
  }));
  if (activeZipCoords) {
    // Radius-scoped, nearest first. Empty radius = "Any distance" (Pro).
    if (radius) rows = rows.filter(r => r.dist != null && r.dist <= radius);
    rows.sort((a, b) => (a.dist ?? 1e9) - (b.dist ?? 1e9));
  } else {
    rows = [];  // no center — the select is disabled anyway
  }
  locSel.innerHTML = '<option value="">All yards in range</option>';
  rows.forEach(r => {
    const opt = document.createElement('option');
    opt.value = r.name;
    opt.textContent = r.name
      + (r.dist != null ? ' \u2014 ' + Math.round(r.dist) + ' mi' : '')
      + ' (' + r.count + ' cars)';
    locSel.appendChild(opt);
  });
  // Keep the selection only if that yard is still in range.
  locSel.value = (prev && rows.some(r => r.name === prev)) ? prev : '';
}

/* A location anchors every other filter: with no center there's nothing to
 * scope the yard list or radius to, so everything except zip/GPS stays
 * disabled until one is set. */
function updateFilterAvailability() {
  const hasLoc = !!activeZipCoords;
  ['live-radius', 'live-filter-make', 'live-filter-location', 'live-filter-match', 'live-sort',
   'live-filter-year-min', 'live-filter-year-max']
    .forEach(id => { const el = document.getElementById(id); if (el) el.disabled = !hasLoc; });
  // Model stays a cascade: enabled only when a location AND a make are set.
  const modelBtn = document.getElementById('live-filter-model-btn');
  if (modelBtn) {
    modelBtn.disabled = !hasLoc || !document.getElementById('live-filter-make').value;
    if (modelBtn.disabled) closeModelPanel();
  }
  const hint = document.getElementById('filters-need-zip');
  if (hint) hint.style.display = hasLoc ? 'none' : '';
}

/* ===== ZIP + RADIUS FILTER ===== */
let activeZipCoords = null;   // {lat, lng} once a valid zip is entered
const zipCoordsCache = JSON.parse(localStorage.getItem('jh_zip_coords') || '{}');

function haversineMiles(lat1, lng1, lat2, lng2) {
  const R = 3958.8, toRad = d => d * Math.PI / 180;
  const dLat = toRad(lat2 - lat1), dLng = toRad(lng2 - lng1);
  const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

async function setZipCenter(zip) {
  if (!/^\d{5}$/.test(zip)) { activeZipCoords = null; renderLive(); return; }
  try {
    if (!zipCoordsCache[zip]) {
      const r = await fetch('https://api.zippopotam.us/us/' + zip);
      if (!r.ok) throw new Error('zip not found');
      const p = (await r.json()).places[0];
      zipCoordsCache[zip] = { lat: parseFloat(p.latitude), lng: parseFloat(p.longitude) };
      localStorage.setItem('jh_zip_coords', JSON.stringify(zipCoordsCache));
    }
    activeZipCoords = zipCoordsCache[zip];
    track('zip-entered');
    localStorage.setItem('jh_zip', zip);
    localStorage.removeItem('jh_gps');
    document.getElementById('live-zip').placeholder = 'e.g. 84101';
  } catch (e) {
    activeZipCoords = null;
    document.getElementById('live-zip').style.borderColor = 'var(--red)';
    setTimeout(() => { document.getElementById('live-zip').style.borderColor = ''; }, 1500);
  }
  renderLive();
}

function vehicleDistanceMi(v) {
  if (!activeZipCoords || v.lat == null || v.lng == null) return null;
  return haversineMiles(activeZipCoords.lat, activeZipCoords.lng, v.lat, v.lng);
}

/* GPS "near me": browser geolocation sets the center directly (needs HTTPS). */
function useMyLocation() {
  if (!navigator.geolocation) { alert('Your browser does not support location.'); return; }
  const btns = [document.getElementById('live-gps'), document.getElementById('zip-banner-gps')].filter(Boolean);
  btns.forEach(b => { b.disabled = true; b.dataset.orig = b.innerHTML; b.innerHTML = '&hellip;'; });
  navigator.geolocation.getCurrentPosition(
    pos => {
      activeZipCoords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
      track('gps-used');
      localStorage.setItem('jh_gps', JSON.stringify(activeZipCoords));
      localStorage.removeItem('jh_zip');
      const zipEl = document.getElementById('live-zip');
      zipEl.value = '';
      zipEl.placeholder = 'Using your location';
      btns.forEach(b => { b.disabled = false; b.innerHTML = b.dataset.orig; });
      updateZipBanner();
      renderLive();
      if (document.getElementById('tab-yards').classList.contains('active')) renderYards();
    },
    () => {
      btns.forEach(b => { b.disabled = false; b.innerHTML = b.dataset.orig; });
      alert("Couldn't get your location. Check that location access is allowed for this site, or enter a zip code instead.");
    },
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 }
  );
}
document.getElementById('live-gps').addEventListener('click', useMyLocation);
document.getElementById('zip-banner-gps').addEventListener('click', useMyLocation);

/* ===== PRO (fake door) =====
 * Freemium gating with NO real payments yet: locked touchpoints open a single
 * upgrade sheet with a waitlist email form, so demand can be measured before
 * building auth/payment infrastructure. Client-side gating is intentionally
 * bypassable in this phase (?pro=1 / 7 taps on the footer version string).
 *
 * Waitlist signups: POSTed to the ntfy topic below (subscribe to it in the
 * ntfy app to get each signup as a push; ntfy.sh only caches ~12h, so keep the
 * phone subscribed, or poll: curl -s "https://ntfy.sh/<topic>/json?poll=1").
 * Signups are ALSO stored in this browser's localStorage under
 * "jh_waitlist_log" as a backup. Swap in a Formspree endpoint here later for
 * durable server-side storage. */
const WAITLIST_NTFY_TOPIC = 'jh-pro-waitlist-7g4kx2m';
const FREE_SAVE_CAP = 5;

// Dev escape hatch: ?pro=1 unlocks, ?pro=0 relocks (persisted in localStorage).
(() => {
  const qp = new URLSearchParams(location.search).get('pro');
  if (qp === '1') localStorage.setItem('jh_pro', '1');
  if (qp === '0') localStorage.removeItem('jh_pro');
})();
function isPro() { return localStorage.getItem('jh_pro') === '1'; }

/* Plan picker (fake door): Pro subscription vs one-time Weekend Pass. The
 * selection is recorded with each waitlist signup so real demand for the two
 * price shapes is measurable before any payment code exists. */
let selectedPlan = 'pro';
function selectPlan(plan) {
  selectedPlan = plan;
  document.querySelectorAll('#upgrade-sheet .plan-option').forEach(c => {
    c.classList.toggle('selected', c.dataset.plan === plan);
  });
  track('plan-selected/' + plan);
}
document.querySelectorAll('#upgrade-sheet .plan-option').forEach(c => {
  c.addEventListener('click', () => selectPlan(c.dataset.plan));
  c.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectPlan(c.dataset.plan); } });
});

let upgradeTrigger = 'unknown';
function openUpgradeSheet(trigger) {
  upgradeTrigger = trigger || 'unknown';
  track('pro-lock/' + upgradeTrigger);
  const apiMode = window.YSApi && YSApi.enabled();
  if (apiMode) {
    // Real billing: the waitlist form gives way to sign-in + checkout.
    document.getElementById('upgrade-form-wrap').style.display = 'none';
    document.getElementById('upgrade-thanks').style.display = 'none';
  } else {
    // Fake-door mode: returning waitlist members see the thank-you state.
    const done = localStorage.getItem('jh_waitlist_email');
    document.getElementById('upgrade-form-wrap').style.display = done ? 'none' : '';
    document.getElementById('upgrade-thanks').style.display = done ? '' : 'none';
  }
  document.getElementById('upgrade-sheet').classList.add('open');
  document.getElementById('upgrade-backdrop').classList.add('open');
}
function closeUpgradeSheet() {
  document.getElementById('upgrade-sheet').classList.remove('open');
  document.getElementById('upgrade-backdrop').classList.remove('open');
}

async function submitWaitlist() {
  const input = document.getElementById('waitlist-email');
  const email = input.value.trim();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    input.style.borderColor = 'var(--red)';
    setTimeout(() => { input.style.borderColor = ''; }, 1500);
    return;
  }
  const btn = document.getElementById('waitlist-submit');
  btn.disabled = true;
  btn.textContent = 'Saving...';
  // Record the plan the user picked and the price they actually saw (single
  // source of truth: the selected card in the DOM) so signups stay comparable
  // across future price changes without building an A/B system.
  const priceEl = document.querySelector('#upgrade-sheet .plan-option.selected')
    || document.querySelector('#upgrade-sheet .tier-card');
  const shownPrice = (priceEl && priceEl.dataset.price) || '';
  const entry = { email, plan: selectedPlan, trigger: upgradeTrigger, price: shownPrice, at: new Date().toISOString() };
  // Local backup log (survives even if the ntfy POST fails).
  try {
    const log = JSON.parse(localStorage.getItem('jh_waitlist_log') || '[]');
    log.push(entry);
    localStorage.setItem('jh_waitlist_log', JSON.stringify(log));
  } catch (e) { /* ignore */ }
  try {
    await fetch('https://ntfy.sh/' + WAITLIST_NTFY_TOPIC, {
      method: 'POST',
      body: `${email} | plan: ${entry.plan} | trigger: ${entry.trigger} | price: $${entry.price} | ${entry.at}`,
      headers: { 'Title': 'YardScout Pro signup', 'Tags': 'moneybag' },
    });
  } catch (e) { /* local log still has it */ }
  // Durable copy: ntfy only caches ~12h, so when an API base is configured the
  // signup also lands in the backend's waitlist table (works even before the
  // full ?api=1 cutover — durability shouldn't wait for it).
  try {
    if (window.YSApi && YSApi.base()) {
      await fetch(YSApi.base() + '/v1/waitlist', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ email, plan: entry.plan, price: String(entry.price), trigger: entry.trigger }),
      });
    }
  } catch (e) { /* ntfy + local log still have it */ }
  localStorage.setItem('jh_waitlist_email', email);
  track('waitlist-submitted/' + selectedPlan);
  btn.disabled = false;
  btn.textContent = 'Notify Me';
  document.getElementById('upgrade-form-wrap').style.display = 'none';
  document.getElementById('upgrade-thanks').style.display = '';
}

/* Re-apply every gate; called at startup and whenever pro state flips. */
function applyProGates() {
  const pro = isPro();
  // Dropdown inventory counts are Pro-only — rebuild the lists on tier change.
  if (liveLoaded) populateLiveMakeFilter();
  const pill = document.getElementById('pro-pill');
  if (pill) {
    pill.textContent = pro ? 'Pro \u2713' : 'Pro';
    pill.classList.toggle('active', pro);
  }
  const setup = document.getElementById('ntfy-setup');
  const locked = document.getElementById('ntfy-locked');
  if (setup && locked) {
    setup.style.display = pro ? '' : 'none';
    locked.style.display = pro ? 'none' : '';
  }
  // Nationwide browsing is Pro: the zip-banner skip and the "Any distance"
  // radius option say so honestly for free users, and work normally for Pro.
  const skipBtn = document.getElementById('zip-banner-skip');
  if (skipBtn) skipBtn.innerHTML = pro ? 'Skip &mdash; show everything nationwide' : 'Nationwide browsing is a Pro feature &rarr;';
  const anyOpt = document.querySelector('#live-radius option[value=""]');
  if (anyOpt) anyOpt.innerHTML = pro ? 'Any distance' : 'Any distance &mdash; Pro';
  // Value-intelligence sorts are Pro: a free user sorting by value would get
  // the ranking (the actual product) with the dollar signs merely hidden.
  const sortSel = document.getElementById('live-sort');
  [...sortSel.options].forEach(o => {
    if (!o.dataset.base) o.dataset.base = o.textContent;
    o.textContent = (!pro && PRO_SORTS.has(o.value)) ? o.dataset.base + ' \u2014 Pro' : o.dataset.base;
  });
  if (!pro && PRO_SORTS.has(sortSel.value)) sortSel.value = FREE_DEFAULT_SORT;
  // Tier-appropriate default: a Pro who never picked a sort gets Best flips
  // (that's what they paid for); free default stays Newest arrivals. An
  // explicit choice (jh_sort) always wins and is restored at boot.
  if (pro && !localStorage.getItem('jh_sort')) sortSel.value = 'smart-profit';
}

/* Sorting BY value hands out the value ranking even with prices blurred, so
 * those sorts ride with the Pro value data. Free sorts are the neutral ones. */
const PRO_SORTS = new Set(['smart-profit', 'gold-first', 'fastest-sell', 'leaving-soonest']);
const FREE_DEFAULT_SORT = 'date-desc';

function toggleProDev() {
  if (isPro()) localStorage.removeItem('jh_pro');
  else localStorage.setItem('jh_pro', '1');
  applyProGates();
  updateZipBanner();
  renderLive();
  if (document.getElementById('tab-yards').classList.contains('active')) renderYards();
  renderSavedSheet();
  alert('Pro mode ' + (isPro() ? 'ON' : 'OFF') + ' (dev toggle)');
}

// First-run honesty note: shown until dismissed, then never again.
(() => {
  const note = document.getElementById('first-run-note');
  if (!note) return;
  if (!localStorage.getItem('jh_honesty_ack')) note.style.display = '';
  document.getElementById('first-run-dismiss').addEventListener('click', () => {
    localStorage.setItem('jh_honesty_ack', '1');
    note.style.display = 'none';
  });
})();

document.getElementById('upgrade-backdrop').addEventListener('click', closeUpgradeSheet);
document.getElementById('upgrade-close').addEventListener('click', closeUpgradeSheet);
document.getElementById('waitlist-submit').addEventListener('click', submitWaitlist);
document.getElementById('waitlist-email').addEventListener('keydown', e => {
  if (e.key === 'Enter') submitWaitlist();
});
document.getElementById('pro-pill').addEventListener('click', () => openUpgradeSheet('header-pill'));
// Demo/dev escape hatch #2: 7 quick taps on the footer version string.
let _verTaps = 0, _verTimer = null;
document.getElementById('jh-version').addEventListener('click', () => {
  _verTaps++;
  clearTimeout(_verTimer);
  _verTimer = setTimeout(() => { _verTaps = 0; }, 1600);
  if (_verTaps >= 7) { _verTaps = 0; toggleProDev(); }
});
// Restore the remembered sort BEFORE the pro gates run: gates snap Pro-only
// values back for free users, so an invalid saved choice self-heals here.
(() => {
  const saved = localStorage.getItem('jh_sort');
  const sel = document.getElementById('live-sort');
  if (saved && [...sel.options].some(o => o.value === saved)) sel.value = saved;
})();
applyProGates();

/* ===== SAVED CARS (hearts + yard-visit sheet) ===== */
let savedCars = {};
try { savedCars = JSON.parse(localStorage.getItem('jh_saved') || '{}'); } catch (e) { savedCars = {}; }

function vehicleKey(v) { return v.vin || String(v.id); }
function isSaved(v) { return !!savedCars[vehicleKey(v)]; }
function persistSaved() { localStorage.setItem('jh_saved', JSON.stringify(savedCars)); }

function toggleSaved(key) {
  if (savedCars[key]) {
    delete savedCars[key];
  } else {
    if (!isPro() && Object.keys(savedCars).length >= FREE_SAVE_CAP) {
      openUpgradeSheet('saved-cap');
      return;
    }
    const v = liveInventory.find(x => vehicleKey(x) === key);
    if (!v) return;
    // Snapshot the vehicle so the list survives the car leaving inventory.
    savedCars[key] = {
      vin: v.vin, id: v.id, year: v.year, make: v.make, model: v.model,
      row: v.row, location: v.location, city: v.city, state: v.state,
      dateAdded: v.dateAdded, topParts: v.topParts || [], hasMatch: v.hasMatch,
      savedAt: new Date().toISOString(),
    };
  }
  persistSaved();
  updateSavedPill();
  renderSavedSheet();
}

function savedRange(s) {
  if (!s.topParts || !s.topParts.length) return null;
  // Only subtract pull costs that come from the yard's real price list; when a
  // part isn't covered we don't invent a cost — the range is flagged resale-only.
  let lo = 0, hi = 0, unknownCost = false;
  s.topParts.forEach(p => {
    // "If equipped" (trim/option-unconfirmed) parts contribute $0 — the saved
    // list shows confirmed value only, same as the live cards and sorts.
    if (p.trim_status === 'unconfirmed') return;
    const lk = lookupYardCost(p.name, s.location);
    const cost = lk.cost != null ? lk.cost : 0;
    if (lk.cost == null) unknownCost = true;
    lo += p.low - cost;
    hi += p.high - cost;
  });
  // Same freshness discount the live cards apply, so the numbers agree.
  const fm = freshnessMultiplier(s.dateAdded);
  return { lo: Math.max(0, Math.round(lo * fm)), hi: Math.round(hi * fm), unknownCost };
}

function updateSavedPill() {
  const n = Object.keys(savedCars).length;
  const pill = document.getElementById('saved-pill');
  pill.style.display = n ? '' : 'none';
  document.getElementById('saved-count').textContent = n;
  if (!n) closeSavedSheet();
}

function renderSavedSheet() {
  const list = document.getElementById('saved-list');
  const entries = Object.entries(savedCars);
  if (!entries.length) {
    list.innerHTML = '<div class="saved-empty">Tap the heart on any car to build your pull list.</div>';
    return;
  }
  // Group by yard; inside each yard sort by row number so the list matches a
  // physical walk through the lot.
  const byYard = {};
  entries.forEach(([key, s]) => {
    const yard = s.location || 'Unknown yard';
    (byYard[yard] = byYard[yard] || []).push([key, s]);
  });
  const rowNum = r => { const n = parseInt(String(r).replace(/\D/g, ''), 10); return isNaN(n) ? 9999 : n; };
  list.innerHTML = Object.keys(byYard).sort().map(yard => {
    const items = byYard[yard].sort((a, b) => rowNum(a[1].row) - rowNum(b[1].row));
    return `
      <div class="saved-yard-group">
        <div class="saved-yard-name">${yard} &middot; ${items.length} car${items.length > 1 ? 's' : ''}</div>
        ${items.map(([key, s]) => {
          const range = savedRange(s);
          const best = (s.topParts && s.topParts[0]) ? s.topParts[0].name : '';
          return `
            <div class="saved-item">
              <div class="saved-row-badge">${s.row || '?'}<small>row</small></div>
              <div class="saved-item-info">
                <div class="saved-item-name">${s.year} ${s.make} ${s.model}</div>
                <div class="saved-item-sub">${!best ? 'No flagged parts' : isPro()
                  ? best + (s.topParts.length > 1 ? ' +' + (s.topParts.length - 1) + ' more' : '')
                  : s.topParts.length + ' flagged part' + (s.topParts.length > 1 ? 's' : '') + ' \u2014 names with Pro'}</div>
              </div>
              ${range && range.hi > 0 ? (isPro()
                ? `<div class="saved-item-profit" title="${range.unknownCost ? 'Resale estimate — pull cost not on this yard\u2019s published price list, check at the yard' : 'Estimated range if parts are good, after this yard\u2019s list pull costs'}">${formatPrice(range.lo)}&ndash;${formatPrice(range.hi)}${range.unknownCost ? '<small style="display:block;font-weight:400;opacity:0.7;">resale</small>' : ''}</div>`
                : `<div class="saved-item-profit locked-blur" role="button" onclick="openUpgradeSheet('saved-value')">${LOCKED_PRICE_MASK}</div>`) : ''}
              <button type="button" class="saved-remove" data-vkey="${key}" title="Remove">${ICON.x}</button>
            </div>`;
        }).join('')}
      </div>`;
  }).join('');
}

function openSavedSheet() {
  renderSavedSheet();
  document.getElementById('saved-sheet').classList.add('open');
  document.getElementById('saved-backdrop').classList.add('open');
}
function closeSavedSheet() {
  document.getElementById('saved-sheet').classList.remove('open');
  document.getElementById('saved-backdrop').classList.remove('open');
}
document.getElementById('saved-pill').addEventListener('click', openSavedSheet);
document.getElementById('saved-backdrop').addEventListener('click', closeSavedSheet);
document.getElementById('saved-clear').addEventListener('click', () => {
  if (!confirm('Remove all saved cars?')) return;
  savedCars = {};
  persistSaved();
  updateSavedPill();
  renderSavedSheet();
  renderLive();
});
document.getElementById('saved-list').addEventListener('click', e => {
  const btn = e.target.closest('.saved-remove');
  if (!btn) return;
  toggleSaved(btn.dataset.vkey);
  renderLive();
});
document.getElementById('live-grid').addEventListener('click', e => {
  const watch = e.target.closest('.watch-btn');
  if (watch) {
    e.preventDefault();
    // One-tap watch is a Pro convenience: free users build watches in the
    // Alerts tab (their radius tops out anyway), Pro watches from any card.
    if (!isPro()) { openUpgradeSheet('watch-card'); return; }
    watchFromCard(watch);
    return;
  }
  const share = e.target.closest('.share-btn');
  if (share) {
    e.preventDefault();
    shareVehicle(share.dataset.vkey);
    return;
  }
  const btn = e.target.closest('.heart-btn');
  if (!btn) return;
  e.preventDefault();
  toggleSaved(btn.dataset.vkey);
  btn.classList.toggle('saved', !!savedCars[btn.dataset.vkey]);
});
updateSavedPill();

/* ===== SHAREABLE FINDS (deep links) ===== */
let focusedCarKey = null;

function applyShareHash() {
  const m = location.hash.match(/#car=([^&]+)/);
  focusedCarKey = m ? decodeURIComponent(m[1]) : null;
}
window.addEventListener('hashchange', () => {
  applyShareHash();
  if (liveLoaded) {
    renderLive();
    if (focusedCarKey) window.scrollTo({ top: 0 });
  }
});

function jhClearFocus() {
  focusedCarKey = null;
  history.replaceState(null, '', location.pathname + location.search);
  renderLive();
}

function shareUrlFor(v) {
  return location.origin + location.pathname + '#car=' + encodeURIComponent(vehicleKey(v));
}

async function shareVehicle(key) {
  const v = liveInventory.find(x => vehicleKey(x) === key);
  if (!v) return;
  const added = v.dateAdded ? new Date(v.dateAdded) : null;
  const arrived = added
    ? added.toLocaleDateString('en-US', {
        month: 'short', day: 'numeric',
        ...(added.getFullYear() !== new Date().getFullYear() ? { year: 'numeric' } : {}),
      }) : '';
  const bits = [`${v.year} ${v.make} ${v.model}`];
  if (v.row) bits.push(`Row ${v.row}`);
  const text = `${bits.join(' — ')} at ${v.location}${arrived ? ', arrived ' + arrived : ''}`;
  const url = shareUrlFor(v);
  track('share-used');
  if (navigator.share) {
    try { await navigator.share({ title: 'YardScout find', text, url }); return; } catch (e) { /* cancelled/unsupported -> fall through */ }
  }
  try {
    await navigator.clipboard.writeText(`${text}\n${url}`);
    const btn = document.querySelector(`.share-btn[data-vkey="${CSS.escape(key)}"]`);
    if (btn) {
      const orig = btn.innerHTML;
      btn.innerHTML = '<small style="font-size: 0.6875rem;">Copied</small>';
      setTimeout(() => { btn.innerHTML = orig; }, 1400);
    }
  } catch (e) {
    prompt('Copy this link:', url);
  }
}

/* First-run banner: ask for a zip once, in plain language. */
function updateZipBanner() {
  // A shared deep link should land on the car, not the onboarding banner.
  // The skip flag only counts for Pro — free users can't dismiss their way
  // into the national list, so the banner stays until they set a location.
  const show = !focusedCarKey
    && !localStorage.getItem('jh_zip') && !localStorage.getItem('jh_gps')
    && !(isPro() && localStorage.getItem('jh_zip_skipped') === '1');
  document.getElementById('zip-banner').style.display = show ? '' : 'none';
}
document.getElementById('zip-banner-go').addEventListener('click', () => {
  const zip = document.getElementById('zip-banner-input').value.trim();
  if (!/^\d{5}$/.test(zip)) {
    document.getElementById('zip-banner-input').style.borderColor = 'var(--red)';
    setTimeout(() => { document.getElementById('zip-banner-input').style.borderColor = ''; }, 1500);
    return;
  }
  document.getElementById('live-zip').value = zip;
  setZipCenter(zip);
});
document.getElementById('zip-banner-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') document.getElementById('zip-banner-go').click();
});
document.getElementById('zip-banner-skip').addEventListener('click', () => {
  // Free users don't get a nationwide skip — honest Pro pitch instead.
  if (!isPro()) { openUpgradeSheet('zip-banner-nationwide'); return; }
  localStorage.setItem('jh_zip_skipped', '1');
  updateZipBanner();
  renderLive();
});

function getFilteredLive() {
  // Focused shared-find view: show exactly that car, ignoring all filters, so
  // a deep link works for someone with no zip/radius state at all.
  if (focusedCarKey) {
    const v = liveInventory.find(x => vehicleKey(x) === focusedCarKey);
    if (v) return [v];
  }
  // Free tier requires a location: with no center there's no radius to scope
  // to, and the unscoped national list is Pro-only. (Shared deep links above
  // still work — they show exactly one car.)
  if (!isPro() && !activeZipCoords) return [];

  const makeFilter = document.getElementById('live-filter-make').value;
  const modelFilter = makeFilter ? selectedModels : null;   // empty set = all models
  const yearMin = parseInt(document.getElementById('live-filter-year-min').value, 10) || null;
  const yearMax = parseInt(document.getElementById('live-filter-year-max').value, 10) || null;
  const matchFilter = document.getElementById('live-filter-match').value;
  const locationFilter = document.getElementById('live-filter-location').value;
  let sortBy = document.getElementById('live-sort').value;
  // Belt & suspenders: value sorts never apply for free even if the select
  // was tampered with.
  if (!isPro() && PRO_SORTS.has(sortBy)) sortBy = FREE_DEFAULT_SORT;
  const radiusMi = effectiveRadiusMi();

  let filtered = liveInventory.filter(v => {
    if (makeFilter && v.make !== makeFilter) return false;
    if (modelFilter && modelFilter.size && !modelFilter.has(v.model)) return false;
    if (yearMin && (!v.year || v.year < yearMin)) return false;
    if (yearMax && (!v.year || v.year > yearMax)) return false;
    if (locationFilter && v.location !== locationFilter) return false;
    if (activeZipCoords && radiusMi) {
      const d = vehicleDistanceMi(v);
      if (d == null || d > radiusMi) return false;
    }
    if (matchFilter === 'match' && !v.hasMatch) return false;
    // Confirmed from the VIN decode only — cars with unknown transmission are
    // excluded rather than guessed at.
    if (matchFilter === 'manual' && !isConfirmedManual(v)) return false;
    return true;
  });

  function totalProfit(v) {
    if (!v.topParts || !v.topParts.length) return 0;
    return v.topParts.reduce((sum, p) => {
      // "If equipped" (trim/option-unconfirmed) parts contribute $0 to all
      // sorting and totals — the car probably doesn't have them.
      if (p.trim_status === 'unconfirmed') return sum;
      const lookup = lookupYardCost(p.name, v.location);
      // No fabricated costs: subtract only real price-list costs (0 when unknown).
      const yc = lookup.cost != null ? lookup.cost : 0;
      return sum + ((p.low + p.high) / 2 - yc);
    }, 0);
  }
  function smartProfit(v) {
    return totalProfit(v) * freshnessMultiplier(v.dateAdded);
  }

  /* Decorate-sort-undecorate: sort keys are computed ONCE per vehicle (O(n)),
   * never inside the comparator. The old comparators recomputed profit (with
   * per-part yard-cost lookups) and re-parsed dates on every comparison --
   * ~3M comparator calls on 163k rows cost multiple SECONDS of main-thread
   * time and froze first paint. */
  const tsOf = v => {
    if (v._ts === undefined) v._ts = Date.parse(v.dateAdded) || 0;
    return v._ts;
  };
  const speedRk = s => s === 'Fast' ? 3 : s === 'Medium' ? 2 : s === 'Slow' ? 1 : 0;
  // Fastest-sell ranks by CONFIRMED parts only — an unconfirmed hardtop that
  // "sells fast" (if it exists) must not put the car in the fast band.
  const bestSpeed = v => {
    const conf = (v.topParts || []).filter(p => p.trim_status !== 'unconfirmed');
    return conf.length ? Math.max(...conf.map(p => speedRk(p.sell_speed))) : 0;
  };
  // Days-on-lot as a share of the yard's historical average. Cars past 2x the
  // average have already defied it (the average predicts nothing for them),
  // so they rank below the genuine 0.8-2x leaving window; cars without
  // lifespan data sort last.
  const urgency = v => {
    if (!v.yardAvgLifespan || !v.dateAdded) return -1;
    const r = daysSinceAdded(v.dateAdded) / v.yardAvgLifespan;
    return r > 2 ? 0.75 : r;
  };

  let keyFn = null, asc = false, tieAsc = false;
  switch (sortBy) {
    case 'smart-profit': keyFn = smartProfit; break;
    // composite keys preserve the old multi-level tie-breaks: values stay well
    // below each 1e9/1e12 band, so bands never collide
    case 'gold-first': keyFn = v => (v.hasMatch ? 1e12 : 0) + (v.maxValue || 0); break;
    case 'fastest-sell': keyFn = v => bestSpeed(v) * 1e9 + totalProfit(v); break;
    case 'leaving-soonest': keyFn = urgency; tieAsc = true; break;
    case 'date-desc': keyFn = tsOf; break;
    case 'date-asc': keyFn = tsOf; asc = true; break;
    case 'year-asc': keyFn = v => v.year || 0; asc = true; break;
  }
  if (keyFn) {
    const dec = filtered.map(v => [keyFn(v), tsOf(v), v]);
    dec.sort((x, y) => (asc ? x[0] - y[0] : y[0] - x[0])
      || (tieAsc ? x[1] - y[1] : y[1] - x[1]));
    filtered = dec.map(d => d[2]);
  }
  return filtered;
}

function updateLiveFilterCount() {
  let n = 0;
  if (document.getElementById('live-filter-make').value) n++;
  if (selectedModels.size) n++;
  if (document.getElementById('live-filter-year-min').value
      || document.getElementById('live-filter-year-max').value) n++;
  if (document.getElementById('live-filter-location').value) n++;
  if (document.getElementById('live-filter-match').value) n++;
  if (activeZipCoords && document.getElementById('live-radius').value) n++;
  const el = document.getElementById('live-filter-count');
  el.style.display = n ? 'inline-grid' : 'none';
  el.textContent = n;
}

function renderLive() {
  updateFilterAvailability();
  if (!liveLoaded) return;
  populateYardFilter();
  refreshScopedInventory();   // make/model dropdowns follow the radius too
  const vehicles = getFilteredLive();

  // KPIs describe what the user is LOOKING AT (their zip/filters), not the
  // whole national database — that's what a parts hunter actually cares about.
  const nearLabel = activeZipCoords && effectiveRadiusMi() ? 'Cars Near You' : 'Cars';
  const worthPulling = vehicles.filter(v => v.hasMatch).length;
  const newThisWeek = vehicles.filter(v => isNew(v.dateAdded)).length;
  const fastSellers = vehicles.filter(v => v.hasMatch && (v.topParts || []).some(p => p.sell_speed === 'Fast')).length;
  const scrapedLabel = liveScrapedAt
    ? new Date(liveScrapedAt).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
    : '—';

  updateLiveFilterCount();
  updateZipBanner();
  renderSaleStrip();

  document.getElementById('live-stats-bar').innerHTML = `
    <div class="stat-card"><div class="label">${nearLabel}</div><div class="value">${vehicles.length.toLocaleString()}</div></div>
    <div class="stat-card"><div class="label">Worth a look</div><div class="value accent">${worthPulling.toLocaleString()}</div></div>
    <div class="stat-card"><div class="label">Fast sellers</div><div class="value">${fastSellers.toLocaleString()}</div></div>
    <div class="stat-card"><div class="label">New this week</div><div class="value">${newThisWeek.toLocaleString()}</div></div>
    <div class="stat-card"><div class="label">Updated</div><div class="value value-sm">${scrapedLabel}</div></div>
  `;

  // Shared-link landing: focused single-car view, or an honest message when
  // the shared car has left the inventory.
  if (focusedCarKey) {
    const found = liveInventory.find(x => vehicleKey(x) === focusedCarKey);
    if (!found) {
      document.getElementById('live-grid').innerHTML = `
        <div class="empty-state" style="grid-column:1/-1;">
          <h3>That car isn't in the current inventory</h3>
          <p>It may have been pulled or crushed since the link was shared &mdash; yards turn over daily.</p>
          <button type="button" class="btn btn-primary" style="margin-top:0.8rem;" onclick="jhClearFocus()">See all cars</button>
        </div>`;
      return;
    }
  }

  if (!vehicles.length) {
    // If the radius filter is what emptied the grid, say so helpfully: name the
    // closest yard and how far it is instead of showing a blank wall.
    const radiusMi = effectiveRadiusMi();
    let msg = '<h3>No matches</h3><p>Try adjusting your filters.</p>';
    if (!isPro() && !activeZipCoords) {
      // Free tier with no location set: point at the zip banner, and be honest
      // that skipping straight to the national list is a Pro feature.
      msg = `<h3>Enter your zip to see cars near you</h3>
        <p>YardScout shows the self-service inventory within ${FREE_MAX_RADIUS_MI} miles of you &mdash; free. Use the zip box or location button above.</p>
        <button type="button" class="btn" style="margin-top:0.8rem;" onclick="openUpgradeSheet('no-zip-empty-state')">Nationwide browsing is a Pro feature &rarr;</button>`;
    } else if (activeZipCoords && radiusMi) {
      let closest = null;
      const seenYards = new Set();
      for (const v of liveInventory) {
        if (v.lat == null || v.lng == null || !v.location || seenYards.has(v.location)) continue;
        seenYards.add(v.location);
        const d = haversineMiles(activeZipCoords.lat, activeZipCoords.lng, v.lat, v.lng);
        if (!closest || d < closest.d) closest = { d, name: v.location, city: v.city, state: v.state };
      }
      if (closest && closest.d > radiusMi) {
        const where = closest.city ? ' in ' + escapeHtml(closest.city) + (closest.state ? ', ' + escapeHtml(closest.state) : '') : '';
        msg = `<h3>No covered yards within ${radiusMi} miles of you</h3>
          <p>The closest is <strong>${escapeHtml(closest.name)}</strong>${where} — about <strong>${Math.round(closest.d)} miles</strong> away.</p>
          <div style="display:flex;gap:0.5rem;justify-content:center;flex-wrap:wrap;margin-top:1rem;">
            <button type="button" class="btn btn-primary" onclick="jhWidenRadius(${Math.ceil(closest.d)})">Widen radius to include it</button>
            <button type="button" class="btn" onclick="jhShowNationwide()">${isPro() ? 'Show everything nationwide' : 'Nationwide search &mdash; Pro'}</button>
          </div>
          <p style="margin-top:1rem;font-size: 0.75rem;">We track every major self-service chain — LKQ Pick Your Part, Pick-n-Pull, and Pull-A-Part — <span class="coverage-count">${coverageYardCount()}</span> yards nationwide. Independent local yards aren't covered yet.</p>`;
      }
    }
    document.getElementById('live-grid').innerHTML = `<div class="empty-state" style="grid-column:1/-1;">${msg}</div>`;
    return;
  }

  // National scans can be 45k+ vehicles — rendering all as DOM cards freezes the
  // browser. Cap the grid; filters/search still run against the full dataset.
  const RENDER_CAP = 400;
  const overflow = vehicles.length > RENDER_CAP ? vehicles.length - RENDER_CAP : 0;
  const vehiclesToRender = overflow ? vehicles.slice(0, RENDER_CAP) : vehicles;

  // Free sample: fully unlock the single best find in the current view so free
  // users see exactly what Pro shows — one car per view, never the database.
  let sampleKey = null;
  if (!isPro() && !focusedCarKey) {
    let bestScore = 0;
    for (const sv of vehiclesToRender) {
      if (!sv.hasMatch || !sv.topParts || !sv.topParts.length) continue;
      const score = sv.topParts.reduce((k, sp) =>
        k + (sp.trim_status === 'unconfirmed' ? 0 : (sp.high || 0)), 0) * freshnessMultiplier(sv.dateAdded);
      if (score > bestScore) { bestScore = score; sampleKey = vehicleKey(sv); }
    }
  }

  const focusBanner = focusedCarKey ? `
    <div class="focus-banner" style="grid-column:1/-1;">
      <span>Shared find &mdash; showing this car from the latest scan.</span>
      <button type="button" class="btn" onclick="jhClearFocus()">See all cars</button>
    </div>` : '';

  document.getElementById('live-grid').innerHTML = focusBanner + vehiclesToRender.map(v => {
    // Pro sees everything; free users get exactly one fully-unlocked sample card.
    const unlocked = isPro() || (sampleKey !== null && vehicleKey(v) === sampleKey);
    const isSampleCard = unlocked && !isPro();
    const isMatch = v.hasMatch;
    const isNewVehicle = isNew(v.dateAdded);
    const dateStr = new Date(v.dateAdded).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    const cardClass = isMatch ? 'match-card' : 'dim-card';
    const fm = freshnessMultiplier(v.dateAdded);
    const fl = freshnessLabel(v.dateAdded);

    // Crush-risk signal from yard departure history: factual day count vs the
    // yard's historical average — an estimate, never a prediction.
    const daysOn = v.dateAdded ? Math.floor(daysSinceAdded(v.dateAdded)) : null;
    let lotClock = '', leavingSoon = false;
    if (v.yardAvgLifespan && daysOn != null) {
      const basisTxt = v.yardLifespanBasis === 'yard' ? 'at this yard'
        : v.yardLifespanBasis === 'chain' ? 'for this chain' : 'across covered yards';
      const avg = v.yardAvgLifespan;
      const title = `Compared to the average time departed vehicles spent on the lot (historical average ${basisTxt} — an estimate, not a schedule)`;
      if (daysOn > 2 * avg) {
        // Long-timers have already outlived the average — claiming "leaving
        // soon" would be false urgency, so just state the facts.
        lotClock = `<div class="lot-clock" title="${title}">On the lot ${daysOn} days &mdash; past the ~${avg}-day typical ${basisTxt}</div>`;
      } else {
        leavingSoon = daysOn >= 0.8 * avg;
        lotClock = `<div class="lot-clock${leavingSoon ? ' lot-clock-soon' : ''}" title="${title}">Day ${daysOn + 1} of ~${avg} typical ${basisTxt}</div>`;
      }
    }

    let cardStyle = '', profitLine = '', partsBlock = '';
    if (isMatch && v.topParts && v.topParts.length) {
      let totalCost = 0, lowSum = 0, highSum = 0, unconfirmedHigh = 0, bestPart = null, bestHigh = -Infinity;
      let anyUnknownCost = false;
      const speedRk = s => s === 'Fast' ? 3 : s === 'Medium' ? 2 : s === 'Slow' ? 1 : 0;
      let demandRk = 0;
      const chainLabel = { pnp: 'PnP list', tap: 'TAP list', utpap: 'UTPAP list', pyp: 'PYP list', pap: 'PAP list', wap: 'WAP list', upullr: 'UPR list' };
      const chainTitle = {
        pnp: 'Pick-n-Pull published price',
        tap: 'Tear-A-Part published price',
        utpap: 'Utah Pic-A-Part published price',
        pyp: 'This Pick Your Part yard\u2019s published price',
        pap: 'This Pull-A-Part yard\u2019s published price',
        wap: 'This Wrench-A-Part yard\u2019s published price',
        upullr: 'U-Pull-R Parts published price',
      };
      const partRows = v.topParts.map((p, pi) => {
        const lookup = lookupYardCost(p.name, v.location);
        const hasCost = lookup.cost != null;
        const yardCost = hasCost ? lookup.cost : 0;
        if (!hasCost) anyUnknownCost = true;
        const pHigh = Math.round(p.high - yardCost);
        // Trim/option-unconfirmed parts ("if equipped") are excluded from the
        // headline range entirely — they're tallied separately and shown as a
        // muted "+ up to $X more if equipped" note, never as promised dollars.
        const ifEquipped = p.trim_status === 'unconfirmed';
        if (ifEquipped) {
          unconfirmedHigh += p.high - yardCost;
        } else {
          totalCost += yardCost;
          lowSum += p.low - yardCost;
          highSum += p.high - yardCost;
        }
        if (pHigh > bestHigh) { bestHigh = pHigh; bestPart = p.name; }
        demandRk = Math.max(demandRk, speedRk(p.sell_speed));
        const sellSpd = p.sell_speed || '';
        const sellCls = sellSpd === 'Fast' ? 'sell-fast' : sellSpd === 'Slow' ? 'sell-slow' : 'sell-medium';
        const costHtml = hasCost
          ? `<span class="part-cost" title="${chainTitle[lookup.source]}: ${lookup.yardName || ''}">${formatPrice(yardCost)} <small style="opacity:0.65">${chainLabel[lookup.source]}</small></span>`
          : `<span class="part-cost" title="This part isn\u2019t on the yard\u2019s published price list — ask at the counter" style="opacity:0.75;"><small>check yard price list</small></span>`;
        const localNote = /\bFB\b|Facebook/i.test(p.sell_at || '')
          ? ' <span class="sell-tip" title="Facebook Marketplace is a local market — prices vary by area">FB prices vary by area</span>' : '';
        // Trim-honesty marker: shown to everyone (it's about whether the part
        // exists on the car, not its value).
        const trimMark = p.trim_status === 'vin'
          ? ' <span class="trim-badge trim-vin" title="This car\u2019s VIN decode confirms the trim, drivetrain, or transmission that carries this part">VIN-confirmed</span>'
          : ifEquipped
          ? ' <span class="trim-badge trim-unknown" title="This part is specific to a trim, drivetrain, or transmission that couldn\u2019t be confirmed from the VIN or the yard listing — check the car at the yard">if equipped &mdash; unconfirmed</span>'
          : '';
        // Generation provenance: which model years this part actually fits
        // (from the generation-specific DB entry) — shown to everyone.
        const fitsMark = p.fits
          ? ` <span class="fits-badge" title="Model years this part fits — prices are specific to this generation">fits ${p.fits}</span>`
          : '';
        // Free tier: everything the parts database produces is blurred —
        // names, fits, values, channels. Real strings never reach the DOM;
        // rows render plausible placeholders so the blur has a shape. The
        // free tease is the count, the demand word, and one sample card.
        if (!unlocked) {
          const ph = LOCKED_PART_PLACEHOLDERS[pi % LOCKED_PART_PLACEHOLDERS.length];
          return `
            <li class="part-item" style="flex-wrap:wrap;">
              <span class="part-name locked-blur" role="button" onclick="openUpgradeSheet('part-name')">${ph}</span>
              <span class="part-cost locked-blur" role="button" onclick="openUpgradeSheet('part-value')">$\u2022\u2022 list</span>
              <span class="part-price locked-blur" role="button" onclick="openUpgradeSheet('part-value')">sells ${LOCKED_PRICE_MASK}</span>
            </li>`;
        }
        return `
          <li class="part-item" style="flex-wrap:wrap;">
            <span class="part-name">${p.name}</span>
            ${trimMark}${fitsMark}
            ${costHtml}
            <span class="part-price" title="Typical eBay sold range (national), working condition">sells ${formatPrice(p.low)}&ndash;${formatPrice(p.high)}</span>
            ${p.sell_at ? `<div style="width:100%;display:flex;align-items:center;gap:0.4rem;margin-top:0.1rem;flex-wrap:wrap;">
              <span class="sell-badge ${sellCls}">${sellSpd === 'Fast' ? 'Sells fast' : sellSpd === 'Slow' ? 'Slow mover' : 'Steady seller'}</span>
              <span class="sell-channel">Sell on: ${p.sell_at}</span>${localNote}
              ${p.sell_notes ? '<span class="sell-tip">' + displaySellNotes(p.sell_notes, v.make) + '</span>' : ''}
            </div>` : ''}
          </li>`;
      }).join('');

      // Demand is the primary signal; dollars are a supporting range, never a promise.
      // Only real price-list pull costs are subtracted — when any part isn't on
      // the yard's list, the range is labeled resale-only instead of guessing.
      const rangeLow = Math.max(0, Math.round(lowSum * fm));
      const rangeHigh = Math.round(highSum * fm);
      const extraHigh = Math.round(unconfirmedHigh * fm);
      const demand = demandRk === 3
        ? { cls: 'demand-fast', label: 'Sells fast' }
        : demandRk === 1
        ? { cls: 'demand-slow', label: 'Slow mover' }
        : { cls: 'demand-steady', label: 'Steady seller' };
      cardStyle = `--tier-color:var(--${demandRk === 3 ? 'demand-fast' : demandRk === 1 ? 'demand-slow' : 'demand-steady'});`;
      const rangeText = anyUnknownCost
        ? `resale ~${formatPrice(rangeLow)}&ndash;${formatPrice(rangeHigh)} if parts are good &middot; pull cost: check yard price list`
        : `e.g. ${formatPrice(rangeLow)}&ndash;${formatPrice(rangeHigh)} if parts are good &middot; ${formatPrice(Math.round(totalCost))} to pull`;
      // Upside stays visible without misleading: unconfirmed ("if equipped")
      // parts never inflate the headline range — they get a muted second line.
      const extraNote = extraHigh > 0 ? `
        <div class="range-extra" title="Parts specific to a trim or factory option that couldn\u2019t be confirmed for this car &mdash; they add nothing to its ranking or headline value">+ up to ${formatPrice(extraHigh)}${rangeHigh > 0 ? ' more' : ''} if equipped (unconfirmed &mdash; check at the yard)</div>` : '';
      profitLine = (rangeHigh > 0 || extraHigh > 0)
        ? (unlocked ? `
        ${isSampleCard ? '<div class="sample-note" role="button" onclick="openUpgradeSheet(\'sample-note\')">Free sample &mdash; Pro shows this for every car</div>' : ''}
        <div class="profit-line">
          <span class="demand-badge ${demand.cls}">${demand.label}</span>
          ${rangeHigh > 0 ? `<span class="range-text">${rangeText}</span>` : ''}
        </div>${extraNote}` : `
        <div class="profit-line">
          <span class="demand-badge ${demand.cls}" title="How quickly this car's flagged parts typically sell">${demand.label}</span>
          <button type="button" class="lock-chip" onclick="openUpgradeSheet('card-value')">${ICON.lock} See parts &amp; values &mdash; Pro</button>
        </div>`)
        : '';
      partsBlock = `
        <details class="parts-details">
          <summary>${unlocked
            ? `Came with ${v.topParts.length} part${v.topParts.length > 1 ? 's' : ''} worth a look &middot; top: ${bestPart}`
            : `${v.topParts.length} valuable part${v.topParts.length > 1 ? 's' : ''} spotted &middot; names &amp; values are Pro`} <span class="chev">${ICON.chev}</span></summary>
          <div class="car-body">
            <div class="ghost-note">These are parts this car <strong>originally came with</strong> &mdash; yards track cars, not remaining parts, so some may already be pulled. Newer arrivals are more likely intact, which is why estimates shrink the longer a car sits.</div>
            <ul class="parts-list">${partRows}</ul>
            <a class="feedback-link" href="https://github.com/benvuolo/yardscout/issues/new" target="_blank" rel="noopener">Spot a wrong price or bug? Tell us</a>
          </div>
        </details>`;
    }

    // One status badge per card, by priority — never a row of colored pills.
    const statusBadge = isNewVehicle
      ? '<span class="badge badge-new">New</span>'
      : leavingSoon
      ? '<span class="badge badge-soon" title="This car has been on the lot longer than ~80% of the historical average — yards rotate stock, so it may not be there much longer. An estimate, not a schedule.">Leaving soon</span>'
      : '';
    // Freshness is context, not an alert: quiet text in the metadata line.
    const freshNote = isMatch
      ? ` &middot; <span title="Time on the lot — older arrivals are more likely already picked over, so value estimates are discounted">${fl.text.toLowerCase()}</span>`
      : '';
    const ex = extrasFor(v);
    const photo = ex && ex[0] ? photoInfo(ex[0]) : null;
    const specBits = ex ? [ex[1], ex[2], ex[3]].filter(Boolean) : [];
    return `
      <div class="car-card ${cardClass}" style="${cardStyle}" data-eid="${escapeHtml(String(v.id))}">
        ${photo ? `<div class="car-photo-wrap"><img class="car-photo" loading="lazy" src="${photo.url}" alt="" onerror="this.parentNode.remove()"><span class="photo-credit">${escapeHtml(photo.label)}</span></div>` : ''}
        <div class="car-header">
          <div style="min-width:0;">
            <div class="car-name">${v.year} ${v.make} ${v.model}</div>
            <div class="live-card-location">${ICON.pin} <span class="loc-name">${v.location}</span>${(() => { const d = vehicleDistanceMi(v); return d != null ? ' <span class="dist">&middot; ' + Math.round(d) + ' mi</span>' : ''; })()}${v.row ? '<span class="live-card-row">Row ' + v.row + '</span>' : ''}${saleBadgeHtml(v.location)}</div>
            <div class="car-meta">Added ${dateStr}${freshNote}${vinMetaHtml(v)}</div>
            ${specBits.length ? `<div class="car-meta car-specs">${specBits.map(escapeHtml).join(' &middot; ')}</div>` : ''}
            ${lotClock}
          </div>
          <div class="car-badges">
            ${isConfirmedManual(v) ? '<span class="badge badge-manual" title="Manual transmission, confirmed from this car\u2019s VIN decode \u2014 never inferred">Manual</span>' : ''}
            ${statusBadge}
            <button type="button" class="watch-btn ${hasWatchFor(v.make, v.model) ? 'watching' : ''}" data-make="${escapeHtml(v.make || '')}" data-model="${escapeHtml(v.model || '')}" title="${hasWatchFor(v.make, v.model) ? 'Already on your watchlist' : 'Watch this model — get alerted when another shows up'}">${ICON.bell}</button>
            <button type="button" class="share-btn" data-vkey="${vehicleKey(v)}" title="Share this find">${ICON.share}</button>
            <button type="button" class="heart-btn ${isSaved(v) ? 'saved' : ''}" data-vkey="${vehicleKey(v)}" title="Save for your yard visit">${ICON.heart}</button>
          </div>
        </div>
        ${profitLine}
        ${partsBlock}
      </div>`;
  }).join('') + (overflow
    ? `<div class="empty-state" style="grid-column:1/-1;padding:1rem;"><p>Showing first ${RENDER_CAP} of ${vehicles.length.toLocaleString()} vehicles &mdash; narrow with search or filters (results stay fully sorted).</p></div>`
    : '');
}

document.getElementById('live-filter-toggle').addEventListener('click', () => {
  const panel = document.getElementById('live-controls');
  const btn = document.getElementById('live-filter-toggle');
  const open = panel.classList.toggle('open');
  btn.classList.toggle('open', open);
  localStorage.setItem('jh_filters_open', open ? '1' : '0');
});
if (localStorage.getItem('jh_filters_open') === '1') {
  document.getElementById('live-controls').classList.add('open');
  document.getElementById('live-filter-toggle').classList.add('open');
}
document.getElementById('live-filter-make').addEventListener('change', () => {
  selectedModels.clear();  // a new make invalidates the old model picks
  populateModelFilter();   // cascade: model list follows the make
  renderLive();
});
/* Multi-select model panel: open/close, search, toggle, clear. */
document.getElementById('live-filter-model-btn').addEventListener('click', e => {
  e.stopPropagation();
  const panel = document.getElementById('live-filter-model-panel');
  const opening = panel.style.display === 'none';
  panel.style.display = opening ? '' : 'none';
  if (opening) {
    const search = document.getElementById('live-filter-model-search');
    search.value = '';
    renderModelList();
    // Mobile keyboards jumping open on tap are worse than one extra tap to
    // search — only autofocus where there's a physical keyboard.
    if (matchMedia('(pointer: fine)').matches) search.focus();
  }
});
document.getElementById('live-filter-model-panel').addEventListener('click', e => e.stopPropagation());
document.addEventListener('click', () => closeModelPanel());
document.getElementById('live-filter-model-search').addEventListener('input', () => renderModelList());
document.getElementById('live-filter-model-list').addEventListener('change', e => {
  const cb = e.target.closest('input[type="checkbox"]');
  if (!cb) return;
  if (cb.checked) selectedModels.add(cb.dataset.model);
  else selectedModels.delete(cb.dataset.model);
  updateModelBtnLabel();
  renderLive();
});
document.getElementById('live-filter-model-clear').addEventListener('click', () => {
  selectedModels.clear();
  renderModelList();
  updateModelBtnLabel();
  renderLive();
});
document.getElementById('live-filter-model-done').addEventListener('click', () => closeModelPanel());
document.getElementById('live-filter-year-min').addEventListener('change', () => {
  // Keep the range sane: from > to snaps "to" up to match.
  const lo = document.getElementById('live-filter-year-min');
  const hi = document.getElementById('live-filter-year-max');
  if (lo.value && hi.value && +lo.value > +hi.value) hi.value = lo.value;
  renderLive();
});
document.getElementById('live-filter-year-max').addEventListener('change', () => {
  const lo = document.getElementById('live-filter-year-min');
  const hi = document.getElementById('live-filter-year-max');
  if (lo.value && hi.value && +hi.value < +lo.value) lo.value = hi.value;
  renderLive();
});
document.getElementById('live-filter-location').addEventListener('change', renderLive);
let _lastFreeSort = (() => {
  const s = localStorage.getItem('jh_sort');
  return (s && !PRO_SORTS.has(s)) ? s : FREE_DEFAULT_SORT;
})();
document.getElementById('live-sort').addEventListener('change', e => {
  const val = e.target.value;
  if (PRO_SORTS.has(val) && !isPro()) {
    e.target.value = _lastFreeSort;   // snap back, pitch honestly
    openUpgradeSheet('sort-' + val);
    return;
  }
  if (!PRO_SORTS.has(val)) _lastFreeSort = val;
  localStorage.setItem('jh_sort', val);   // explicit choice, remembered
  renderLive();
});
document.getElementById('live-filter-match').addEventListener('change', renderLive);
document.getElementById('live-zip').addEventListener('input', e => setZipCenter(e.target.value.trim()));
document.getElementById('live-radius').addEventListener('change', () => {
  const sel = document.getElementById('live-radius');
  // "Any distance" (empty value) is nationwide — Pro only. Snap free users
  // back to their previous radius and pitch the upgrade instead.
  if (sel.value === '' && !isPro()) {
    const prev = localStorage.getItem('jh_radius');
    sel.value = prev && prev !== '' ? prev : String(FREE_MAX_RADIUS_MI);
    openUpgradeSheet('radius-any-distance');
    return;
  }
  localStorage.setItem('jh_radius', sel.value);
  renderLive();
});
// Restore saved zip/radius/GPS center across visits
(() => {
  const savedZip = localStorage.getItem('jh_zip') || '';
  let savedRadius = localStorage.getItem('jh_radius');
  // Radius is capped at 250 mi now; migrate any older saved value down.
  if (savedRadius !== null && parseInt(savedRadius, 10) > 250) {
    savedRadius = '250';
    localStorage.setItem('jh_radius', savedRadius);
  }
  // Legacy "any distance" ('' = nationwide) is Pro-only now; migrate free
  // users down to the widest free radius.
  if (savedRadius === '' && !isPro()) {
    savedRadius = String(FREE_MAX_RADIUS_MI);
    localStorage.setItem('jh_radius', savedRadius);
  }
  if (savedRadius !== null) document.getElementById('live-radius').value = savedRadius;
  if (savedZip) {
    document.getElementById('live-zip').value = savedZip;
    setZipCenter(savedZip);
  } else {
    const gps = localStorage.getItem('jh_gps');
    if (gps) {
      try {
        activeZipCoords = JSON.parse(gps);
        document.getElementById('live-zip').placeholder = 'Using your location';
      } catch (e) { localStorage.removeItem('jh_gps'); }
    }
  }
})();
updateFilterAvailability();   // filters stay disabled until a location exists
/* Yards are re-scanned automatically every ~6 hours; this button re-checks
 * for a newer published scan (no-cache fetch + background revalidate). */
document.getElementById('live-refresh-btn').addEventListener('click', async () => {
  const btn = document.getElementById('live-refresh-btn');
  const prev = liveScrapedAt;
  btn.disabled = true;
  const orig = btn.innerHTML;
  btn.innerHTML = 'Checking&hellip;';
  try { await loadLiveInventory(); } catch (e) { /* handled inside */ }
  btn.disabled = false;
  btn.innerHTML = orig;
  if (liveScrapedAt && liveScrapedAt !== prev) return; // new data rendered
  let age = '';
  const ts = Date.parse(liveScrapedAt || '');
  if (ts) {
    const hrs = Math.max(0, Math.round((Date.now() - ts) / 3600000));
    age = hrs < 1 ? ' Last scan: under an hour ago.'
      : hrs < 48 ? ` Last scan: ${hrs}h ago.`
      : ` Last scan: ${Math.round(hrs / 24)} days ago.`;
  }
  alert("You're already seeing the latest scan. Yards are re-scanned automatically about every 6 hours." + age);
});
document.getElementById('tab-live').addEventListener('click', (e) => {
  const btn = e.target.closest('.btn-copy-vin');
  if (!btn || !btn.dataset.vin) return;
  e.preventDefault();
  navigator.clipboard.writeText(btn.dataset.vin).then(() => {
    btn.innerHTML = ICON.check;
    btn.classList.add('copied');
    setTimeout(() => { btn.innerHTML = ICON.copy; btn.classList.remove('copied'); }, 1200);
  }).catch(() => {});
});

/* ===== YARDS DIRECTORY ===== */
/* Built entirely from the live inventory (yard rows + per-yard lifespan from
 * the history DB). Free-tier friendly by design: counts and freshness only,
 * no part values anywhere on this tab. */
const CHAIN_PRICE_PAGES = [
  [/^pick[\s-]*n[\s-]*pull/i, 'https://www.picknpull.com/parts-pricing', 'Pick-n-Pull'],
  [/^pull[\s-]*a[\s-]*part/i, 'https://www.pullapart.com/used-auto-parts/parts-pricing/', 'Pull-A-Part'],
  [/^tear[\s-]*a[\s-]*part/i, 'https://tearapart.com/price-list/', 'Tear-A-Part'],
  [/pic[\s-]*a[\s-]*part/i, 'https://utpap.com/ogden-prices/', 'Utah Pic-A-Part'],
  // Wrench-A-Part publishes per-location lists; every page carries the same
  // location picker, so the Austin URL works as the chain-wide entry point.
  [/wrench[\s-]*a[\s-]*part/i, 'https://wrenchapart.com/austin-price-list', 'Wrench-A-Part'],
  [/^u[\s-]*pull[\s-]*r/i, 'https://upullrparts.com/part-pricing/', 'U-Pull-R Parts'],
  // LKQ Pick Your Part publishes prices per location inside its site/app with
  // no stable public price-list URL, so those yards get no link.
];

function buildYardDirectory() {
  const byLoc = new Map();
  for (const v of liveInventory) {
    if (!v.location) continue;
    let y = byLoc.get(v.location);
    if (!y) {
      y = {
        location: v.location, city: v.city || '', state: v.state || '',
        lat: v.lat, lng: v.lng, count: 0, newCount: 0,
        avgLifespan: v.yardAvgLifespan || null,
        lifespanBasis: v.yardLifespanBasis || null,
      };
      byLoc.set(v.location, y);
    }
    y.count++;
    if (isNew(v.dateAdded)) y.newCount++;
  }
  return [...byLoc.values()];
}

/* ===== STALE-DATA GUARD =====
 * The scan runs every 6 hours; if the newest data is older than a day,
 * say so instead of quietly presenting stale inventory as live.
 * Test hook: ?stale=<hours> forces an age for screenshots/QA. */
function updateStaleBanner() {
  const el = document.getElementById('stale-banner');
  if (!el) return;
  const forced = parseFloat(new URLSearchParams(location.search).get('stale'));
  let hours = null;
  if (!isNaN(forced)) hours = forced;
  else if (liveScrapedAt) hours = (Date.now() - new Date(liveScrapedAt).getTime()) / 3600000;
  if (hours == null || hours < 24) { el.style.display = 'none'; return; }
  const days = Math.floor(hours / 24);
  const ago = days >= 2 ? `${days} days` : `${Math.round(hours)} hours`;
  el.textContent = `Inventory last updated ${ago} ago — new arrivals may be missing.`;
  el.classList.toggle('severe', hours >= 72);
  el.style.display = '';
}

function renderYards() {
  const grid = document.getElementById('yards-grid');
  const statsBar = document.getElementById('yards-stats-bar');
  if (!liveLoaded) {
    grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1;"><p>Loading live inventory&hellip;</p></div>';
    statsBar.innerHTML = '';
    return;
  }

  // The Yards tab reflects the same vicinity as Live: it needs a center.
  if (!activeZipCoords) {
    statsBar.innerHTML = '';
    grid.innerHTML = `
      <div class="empty-state yards-locate" style="grid-column:1/-1;">
        <h3>Where are you?</h3>
        <p>Yards are listed by distance from you. Set a zip code or use your location to see the yards nearby.</p>
        <div class="zip-banner-form" style="justify-content:center;">
          <input type="text" id="yards-zip-input" inputmode="numeric" maxlength="5" placeholder="Zip code">
          <button type="button" class="btn btn-primary" id="yards-zip-go">Show yards</button>
        </div>
        <button type="button" class="btn gps-btn" id="yards-gps" style="margin-top:0.6rem;">${ICON.pin} Or use my location</button>
      </div>`;
    const go = () => {
      const zip = document.getElementById('yards-zip-input').value.trim();
      if (/^\d{5}$/.test(zip)) {
        document.getElementById('live-zip').value = zip;
        setZipCenter(zip).then(() => { updateZipBanner(); renderYards(); });
      }
    };
    document.getElementById('yards-zip-go').addEventListener('click', go);
    document.getElementById('yards-zip-input').addEventListener('keydown', e => { if (e.key === 'Enter') go(); });
    document.getElementById('yards-gps').addEventListener('click', useMyLocation);
    return;
  }

  let yards = buildYardDirectory();
  const allCount = yards.length;
  const states = new Set(yards.map(y => y.state).filter(Boolean));

  yards.forEach(y => {
    y.dist = (y.lat != null && y.lng != null)
      ? haversineMiles(activeZipCoords.lat, activeZipCoords.lng, y.lat, y.lng) : null;
  });
  yards.sort((a, b) => (a.dist ?? 1e9) - (b.dist ?? 1e9));

  // Same radius as the Live tab (capped at 250 mi). "Any distance" shows all,
  // still nearest-first — but the full national yard list is Pro-only, so
  // free users are always clamped to the widest free radius.
  const radius = effectiveRadiusMi();
  const inRange = radius ? yards.filter(y => y.dist != null && y.dist <= radius) : yards;

  const q = (document.getElementById('yards-search').value || '').trim().toLowerCase();
  const shown = q ? inRange.filter(y => (y.location + ' ' + y.city + ' ' + y.state).toLowerCase().includes(q)) : inRange;

  statsBar.innerHTML = `
    <div class="stat-card"><div class="label">Yards near you</div><div class="value">${inRange.length}</div></div>
    <div class="stat-card"><div class="label">Within</div><div class="value-sm">${radius ? radius + ' mi' : 'any distance'}</div></div>
    <div class="stat-card"><div class="label">Tracked nationwide</div><div class="value">${allCount}</div></div>
  `;

  if (!shown.length) {
    if (!inRange.length) {
      const nearest = yards.find(y => y.dist != null);
      const nearestTxt = nearest
        ? `The nearest yard we track is <strong>${escapeHtml(nearest.location)}</strong> in ${escapeHtml([nearest.city, nearest.state].filter(Boolean).join(', '))} &mdash; ${Math.round(nearest.dist)} mi away.`
        : '';
      grid.innerHTML = `
        <div class="empty-state" style="grid-column:1/-1;">
          <h3>No yards within ${radius} mi</h3>
          <p>${nearestTxt}</p>
          <div style="display:flex;gap:0.6rem;justify-content:center;flex-wrap:wrap;margin-top:0.75rem;">
            ${radius < 250 ? '<button type="button" class="btn" id="yards-widen">Widen to 250 mi</button>' : ''}
            <button type="button" class="btn" id="yards-any">${isPro() ? 'Show all yards nearest-first' : 'See every yard nationwide &mdash; Pro'}</button>
          </div>
        </div>`;
      const setRadius = v => {
        document.getElementById('live-radius').value = v;
        localStorage.setItem('jh_radius', v);
        renderYards();
      };
      const widen = document.getElementById('yards-widen');
      if (widen) widen.addEventListener('click', () => setRadius('250'));
      document.getElementById('yards-any').addEventListener('click', () => {
        // The unscoped national yard list is Pro-only.
        if (!isPro()) { openUpgradeSheet('yards-show-all'); return; }
        setRadius('');
      });
    } else {
      grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1;"><h3>No yards match</h3><p>Try a different name, city, or state.</p></div>';
    }
    return;
  }

  grid.innerHTML = shown.map(y => {
    const chain = CHAIN_PRICE_PAGES.find(c => c[0].test(y.location));
    const place = [y.city, y.state].filter(Boolean).join(', ');
    const distTxt = y.dist != null ? ` <span class="dist">&middot; ${Math.round(y.dist)} mi</span>` : '';
    const life = y.avgLifespan
      ? `Cars typically last ~${y.avgLifespan} days here` +
        (y.lifespanBasis === 'chain' ? ' (chain average)' : y.lifespanBasis === 'all' ? ' (all-yards average)' : '')
      : 'Not enough departure history yet for a typical-lifespan estimate';
    return `
      <div class="car-card yard-card" data-loc="${escapeHtml(y.location)}" role="button" tabindex="0"
           aria-label="View cars at ${escapeHtml(y.location)}">
        <div class="car-header">
          <div style="min-width:0;">
            <div class="car-name">${escapeHtml(y.location)}</div>
            <div class="live-card-location">${ICON.pin} <span class="loc-name">${escapeHtml(place) || 'Location unknown'}</span>${distTxt}${saleBadgeHtml(y.location)}</div>
            <div class="car-meta">${y.count.toLocaleString()} cars on the lot &middot; ${y.newCount.toLocaleString()} new this week</div>
            <div class="lot-clock" title="Based on historical arrival-to-departure data — an estimate, not a schedule">${life}</div>
          </div>
        </div>
        <div class="yard-actions">
          <button type="button" class="btn yard-view-btn">View cars</button>
          ${chain ? `<a class="yard-price-link" href="${chain[1]}" target="_blank" rel="noopener">${chain[2]} price list</a>` : '<span class="yard-price-none">Prices posted at the yard</span>'}
        </div>
      </div>`;
  }).join('');
}

/* Tap a yard -> Live tab filtered to it. Distance is cleared for the session
 * so a far-away yard isn't immediately hidden by the radius filter. */
function viewYardInLive(loc) {
  track('yard-opened');
  const sel = document.getElementById('live-filter-location');
  sel.value = loc;
  if (sel.value !== loc) return; // option missing (shouldn't happen — same data)
  document.querySelector('.tab[data-tab="live"]').click();
  window.scrollTo({ top: 0 });
}

document.getElementById('yards-grid').addEventListener('click', e => {
  if (e.target.closest('a')) return; // price-list link navigates normally
  const card = e.target.closest('.yard-card');
  if (card) viewYardInLive(card.dataset.loc);
});
document.getElementById('yards-grid').addEventListener('keydown', e => {
  if (e.key !== 'Enter') return;
  const card = e.target.closest('.yard-card');
  if (card) viewYardInLive(card.dataset.loc);
});
document.getElementById('yards-search').addEventListener('input', () => renderYards());

/* ===== PROFIT BREAKDOWN ===== */
/** Baked sell_notes can mention Lexus for any "Mark Levinson" part; donor make may differ. */
function displaySellNotes(notes, vehicleMake) {
  if (!notes) return '';
  const m = (vehicleMake || '').toLowerCase();
  if (!m.includes('lexus') && /lexus\s+audio/i.test(notes)) {
    return 'Premium OEM audio — strong eBay market';
  }
  return notes;
}

/* ===== TABS ===== */
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
    if (tab.dataset.tab === 'yards') renderYards();
    if (tab.dataset.tab === 'live') renderLive();
    if (tab.dataset.tab === 'alerts') renderAlerts();
  });
});


/* ===== ALERTS / WATCHLIST ===== */
const WATCHLIST_KEY = 'yardscout_watchlist';
const ALERTED_KEY = 'yardscout_alerted';
// One-time migration from the pre-rebrand keys.
for (const [oldK, newK] of [['junkyard_hunter_watchlist', WATCHLIST_KEY], ['junkyard_hunter_alerted', ALERTED_KEY]]) {
  const v = localStorage.getItem(oldK);
  if (v !== null && localStorage.getItem(newK) === null) localStorage.setItem(newK, v);
  if (v !== null) localStorage.removeItem(oldK);
}

function loadWatchlist() {
  try { return JSON.parse(localStorage.getItem(WATCHLIST_KEY)) || []; }
  catch { return []; }
}
function saveWatchlist(list) { localStorage.setItem(WATCHLIST_KEY, JSON.stringify(list)); }
function loadAlerted() {
  try { return JSON.parse(localStorage.getItem(ALERTED_KEY)) || {}; }
  catch { return {}; }
}
function saveAlerted(obj) { localStorage.setItem(ALERTED_KEY, JSON.stringify(obj)); }

function watchlistMatches(entry, v) {
  const makeLow = (entry.make || '').toLowerCase();
  const modelLow = (entry.model || '').toLowerCase();
  if (makeLow && !(v.make || '').toLowerCase().includes(makeLow)) return false;
  if (modelLow && !(v.model || '').toLowerCase().includes(modelLow)) return false;
  if (entry.yrMin && v.year < entry.yrMin) return false;
  if (entry.yrMax && v.year > entry.yrMax) return false;
  if (entry.matchOnly && !v.hasMatch) return false;
  // Radius-scoped watches (center snapshotted when the watch was created).
  if (entry.radiusMi && entry.lat != null && entry.lng != null) {
    if (v.lat == null || v.lng == null) return false;
    if (haversineMiles(entry.lat, entry.lng, v.lat, v.lng) > entry.radiusMi) return false;
  }
  return true;
}

function getWatchlistHits() {
  const watchlist = loadWatchlist();
  if (!watchlist.length || !liveLoaded) return [];
  const results = [];
  for (const entry of watchlist) {
    const hits = liveInventory.filter(v => watchlistMatches(entry, v));
    results.push({ entry, hits });
  }
  return results;
}

function renderAlerts() {
  const watchlist = loadWatchlist();
  const results = getWatchlistHits();

  const wlContainer = document.getElementById('alert-watchlist');
  if (!watchlist.length) {
    wlContainer.innerHTML = '<div class="empty-state"><h3>No vehicles on your watchlist</h3><p>Add a make/model above to start tracking.</p></div>';
  } else {
    wlContainer.innerHTML = results.map((r, i) => {
      const e = r.entry;
      const label = [e.make, e.model].filter(Boolean).join(' ') || 'Any Vehicle';
      const yrLabel = e.yrMin || e.yrMax
        ? (e.yrMin || 'any') + '–' + (e.yrMax || 'any')
        : 'All years';
      // Legacy watches (no radiusMi key) predate radius scoping — say nothing.
      const radLabel = !('radiusMi' in e) ? ''
        : e.radiusMi ? ` &middot; within ${e.radiusMi} mi` : ' &middot; anywhere';
      const hitCount = r.hits.length;
      return `<div class="watchlist-item">
        <div class="wl-info">
          <span class="wl-name">${label}</span>
          <span class="wl-detail">${yrLabel}${radLabel}${e.matchOnly ? ' &middot; Parts only' : ''}</span>
          <span class="wl-count ${hitCount > 0 ? 'has-hits' : 'no-hits'}">${hitCount} in yard now</span>
        </div>
        <div style="display:flex;gap:0.5rem;align-items:center;">
          <button class="wl-remove" onclick="removeWatchItem(${i})">Remove</button>
        </div>
      </div>`;
    }).join('');
  }

  const totalHits = results.reduce((s, r) => s + r.hits.length, 0);
  const uniqueHits = new Set();
  results.forEach(r => r.hits.forEach(v => uniqueHits.add(v.id || v.vin || `${v.year}${v.make}${v.model}`)));

  document.getElementById('alert-matches-bar').innerHTML = `
    <div class="stat-card"><div class="label">Watchlist items</div><div class="value">${watchlist.length}</div></div>
    <div class="stat-card"><div class="label">Vehicles found</div><div class="value accent">${uniqueHits.size}</div></div>
    <div class="stat-card"><div class="label">Total hits</div><div class="value">${totalHits}</div></div>
  `;

  const allHitVehicles = [];
  const seenIds = new Set();
  results.forEach(r => r.hits.forEach(v => {
    const vid = v.id || v.vin || `${v.year}${v.make}${v.model}`;
    if (!seenIds.has(vid)) {
      seenIds.add(vid);
      allHitVehicles.push(v);
    }
  }));
  allHitVehicles.sort((a, b) => new Date(b.dateAdded) - new Date(a.dateAdded));

  const grid = document.getElementById('alert-matches-grid');
  if (!allHitVehicles.length) {
    grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1;"><h3>No matches yet</h3><p>None of your watchlist vehicles are in the yard right now. The scraper checks automatically in <code>--watch</code> mode.</p></div>';
    return;
  }

  grid.innerHTML = allHitVehicles.slice(0, 100).map(v => {
    const isMatch = v.hasMatch;
    const dateStr = new Date(v.dateAdded).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    const matchedRules = watchlist.filter(e => watchlistMatches(e, v)).map(e =>
      [e.make, e.model].filter(Boolean).join(' ') || 'Any'
    );
    return `
      <div class="car-card match-card" style="--tier-color:var(--accent);">
        <div class="car-header">
          <div style="min-width:0;">
            <div class="car-name">${v.year} ${v.make} ${v.model}</div>
            <div class="live-card-location">${ICON.pin} <span class="loc-name">${v.location}</span>${(() => { const d = vehicleDistanceMi(v); return d != null ? ' <span class="dist">&middot; ' + Math.round(d) + ' mi</span>' : ''; })()}${v.row ? '<span class="live-card-row">Row ' + v.row + '</span>' : ''}${saleBadgeHtml(v.location)}</div>
            <div class="car-meta">Added ${dateStr}${vinMetaHtml(v)} &middot; matched: ${matchedRules.join(', ')}</div>
          </div>
          <div class="car-badges">
            <span class="badge badge-new">Watchlist hit</span>
          </div>
        </div>
        ${isMatch && v.topParts && v.topParts.length ? `
          <details class="parts-details">
            <summary>Came with ${v.topParts.length} part${v.topParts.length > 1 ? 's' : ''} <span class="chev">${ICON.chev}</span></summary>
            <div class="car-body">
              <ul class="parts-list">
                ${v.topParts.slice(0, 5).map(p => `
                  <li class="part-item">
                    <span class="part-name">${p.name}</span>
                    
                    ${isPro()
                      ? `<span class="part-price">${formatPrice(p.low)}&ndash;${formatPrice(p.high)}</span>`
                      : `<span class="part-price locked-blur" role="button" onclick="openUpgradeSheet('alerts-value')">${LOCKED_PRICE_MASK}</span>`}
                  </li>
                `).join('')}
              </ul>
            </div>
          </details>
        ` : ''}
      </div>`;
  }).join('');
}

/* True when an existing watch already covers this make+model (an "any model"
 * watch on the make counts). Drives the bell state on car cards. */
function hasWatchFor(make, model) {
  if (!make) return false;
  return loadWatchlist().some(e =>
    (e.make || '').toLowerCase() === make.toLowerCase() &&
    (!e.model || (e.model || '').toLowerCase() === (model || '').toLowerCase()));
}

/* One-tap watch from a Live card (Pro): make+model, all years, any condition.
 * Idempotent — tapping an already-watched card just confirms. */
function watchFromCard(btn) {
  const make = btn.dataset.make, model = btn.dataset.model;
  if (!make) return;
  if (!hasWatchFor(make, model)) {
    // One-tap watch follows the current search scope: "watch this near me."
    // Radius = whatever the Live tab is set to right now (null = Pro's "Any
    // distance" = nationwide). Tighter or wider is an Alerts-tab edit away.
    const radiusMi = activeZipCoords ? (effectiveRadiusMi() || null) : null;
    const entry = { make, model, yrMin: null, yrMax: null, matchOnly: false, radiusMi,
      addedAt: new Date().toISOString() + '~' + Math.random().toString(36).slice(2, 8) };
    if (radiusMi) { entry.lat = activeZipCoords.lat; entry.lng = activeZipCoords.lng; }
    const watchlist = loadWatchlist();
    watchlist.push(entry);
    saveWatchlist(watchlist);
    // The car you tapped (and its lot-mates) are already known to you —
    // alert only on arrivals from here on.
    seedAlertedForEntry(entry);
    syncWatchToServer(entry);
    renderAlerts();
    checkAndNotify();
  }
  // Flash confirmation on every matching bell currently rendered.
  document.querySelectorAll('.watch-btn').forEach(b => {
    if (b.dataset.make === make && b.dataset.model === model) {
      b.classList.add('watching');
      b.title = 'Already on your watchlist';
    }
  });
  const orig = btn.innerHTML;
  btn.innerHTML = ICON.check;
  setTimeout(() => { btn.innerHTML = orig; }, 1200);
}

/* Watchlist pickers mirror the Live filters, with one intentional difference:
 * they draw from the FULL national inventory, not the current radius — you
 * watch for cars that aren't near you *yet*. Values are exact scraper strings,
 * so both local and server-side alert matching hit reliably (no typos). */
function populateWatchOptions() {
  const makeSel = document.getElementById('alert-make');
  if (!makeSel || !liveLoaded) return;
  const prevMake = makeSel.value;
  const makes = new Set();
  for (const v of liveInventory) {
    if (v.make && !JUNK_MAKES.has(v.make.toLowerCase())) makes.add(v.make);
  }
  makeSel.innerHTML = '<option value="">Select make&hellip;</option>';
  [...makes].sort().forEach(m => {
    const opt = document.createElement('option');
    opt.value = m; opt.textContent = m;
    makeSel.appendChild(opt);
  });
  makeSel.value = makes.has(prevMake) ? prevMake : '';
  populateWatchModelOptions();

  const years = [...new Set(liveInventory.map(v => v.year).filter(Boolean))].sort((a, b) => b - a);
  for (const id of ['alert-yr-min', 'alert-yr-max']) {
    const sel = document.getElementById(id);
    const prev = sel.value;
    sel.innerHTML = '<option value="">Any</option>';
    years.forEach(y => {
      const opt = document.createElement('option');
      opt.value = y; opt.textContent = y;
      sel.appendChild(opt);
    });
    sel.value = prev && years.includes(+prev) ? prev : '';
  }
}

/* Watch models: same multi-select panel as the Live filter — check several
 * models under one make and one Add creates a watch per model. Empty
 * selection = any model of the make. */
let watchSelectedModels = new Set();
let _watchModelCounts = new Map();

function populateWatchModelOptions() {
  const make = document.getElementById('alert-make').value;
  const btn = document.getElementById('alert-model-btn');
  watchSelectedModels.clear();
  if (!make) {
    btn.disabled = true;
    document.getElementById('alert-model-panel').style.display = 'none';
    updateWatchModelBtnLabel();
    return;
  }
  btn.disabled = false;
  _watchModelCounts = new Map();
  for (const v of liveInventory) {
    if (v.make === make && v.model) {
      _watchModelCounts.set(v.model, (_watchModelCounts.get(v.model) || 0) + 1);
    }
  }
  renderWatchModelList();
  updateWatchModelBtnLabel();
}

function renderWatchModelList() {
  const list = document.getElementById('alert-model-list');
  const q = (document.getElementById('alert-model-search').value || '').trim().toLowerCase();
  const models = [..._watchModelCounts.keys()].sort()
    .filter(m => !q || m.toLowerCase().includes(q));
  list.innerHTML = models.length ? models.map(m => `
    <label class="multi-select-row">
      <input type="checkbox" data-model="${escapeHtml(m)}" ${watchSelectedModels.has(m) ? 'checked' : ''}>
      <span>${escapeHtml(m)}</span>
    </label>`).join('')
    : '<div class="multi-select-empty">No models match</div>';
}

function updateWatchModelBtnLabel() {
  const btn = document.getElementById('alert-model-btn');
  btn.textContent = !watchSelectedModels.size ? 'Any model'
    : watchSelectedModels.size === 1 ? [...watchSelectedModels][0]
    : `${watchSelectedModels.size} models`;
  btn.classList.toggle('has-selection', watchSelectedModels.size > 0);
}

/* Watches alert on FUTURE arrivals, never the cars already sitting on the
 * lot when the watch was created — mark every current match as
 * already-alerted so only genuinely new arrivals notify. The backend does
 * the same for push/email (see handleWatchCreate). */
function seedAlertedForEntry(entry) {
  if (!liveLoaded) return;
  const alerted = loadAlerted();
  let n = 0;
  for (const v of liveInventory) {
    if (!watchlistMatches(entry, v)) continue;
    const key = `${v.id || v.vin || ''}:${v.year}:${v.make}:${v.model}`;
    if (!alerted[key]) { alerted[key] = new Date().toISOString(); n++; }
  }
  if (n) saveAlerted(alerted);
}

function addWatchItem() {
  const make = document.getElementById('alert-make').value;
  if (!make) return alert('Pick a make first.');
  const yrMin = parseInt(document.getElementById('alert-yr-min').value) || null;
  const yrMax = parseInt(document.getElementById('alert-yr-max').value) || null;
  if (yrMin && yrMax && yrMin > yrMax) return alert('Year min is after year max.');
  const radiusMi = parseInt(document.getElementById('alert-radius').value) || null;
  if (radiusMi && !activeZipCoords) {
    return alert('Set a ZIP (or use "near me") in the Live tab first, so the radius has a center.');
  }
  const matchOnly = document.getElementById('alert-match-only').checked;
  const watchlist = loadWatchlist();
  // One watch per checked model; no models checked = one any-model watch.
  const models = watchSelectedModels.size ? [...watchSelectedModels] : [''];
  let added = 0;
  for (const model of models) {
    const dupe = watchlist.some(e =>
      (e.make || '') === make && (e.model || '') === model &&
      (e.yrMin || null) === yrMin && (e.yrMax || null) === yrMax &&
      (e.radiusMi || null) === radiusMi &&
      !!e.matchOnly === matchOnly);
    if (dupe) continue;
    // addedAt doubles as the local↔server sync key — the random suffix keeps
    // it unique when several models are added in the same millisecond.
    const entry = { make, model, yrMin, yrMax, matchOnly, radiusMi,
      addedAt: new Date().toISOString() + '~' + Math.random().toString(36).slice(2, 8) };
    if (radiusMi) { entry.lat = activeZipCoords.lat; entry.lng = activeZipCoords.lng; }
    watchlist.push(entry);
    seedAlertedForEntry(entry);
    syncWatchToServer(entry);
    added++;
  }
  if (!added) return alert('Already on your watchlist.');
  saveWatchlist(watchlist);
  document.getElementById('alert-make').value = '';
  populateWatchModelOptions();   // resets + disables the model picker
  document.getElementById('alert-yr-min').value = '';
  document.getElementById('alert-yr-max').value = '';
  renderAlerts();
  saveWatchlistFile();
  checkAndNotify();
}

function removeWatchItem(idx) {
  const watchlist = loadWatchlist();
  const [removed] = watchlist.splice(idx, 1);
  saveWatchlist(watchlist);
  if (removed && removed.serverId && window.YSApi && YSApi.enabled()) {
    YSApi.deleteWatch(removed.serverId).catch(() => { /* gone next sync */ });
  }
  renderAlerts();
  saveWatchlistFile();
}

/* ===== Cloud alerts (API mode): server-side watches + real web push =====
 * The local watchlist stays the editor; entries mirror to the account so the
 * backend can push even when the app is closed. serverId on each local entry
 * links the two. */
/* Any signed-in account syncs watches now: free watches feed the weekly
 * digest email, Pro adds instant push. The server enforces free limits
 * (radius required, 250 mi cap, 5 watches). */
function canCloudSync() {
  const me = window.YSApi && YSApi.enabled() && YSApi.getMe();
  return !!me;
}

async function syncWatchToServer(entry) {
  if (!canCloudSync() || entry.serverId) return;
  try {
    const w = {
      make: entry.make || null, model: entry.model || null,
      yearMin: entry.yrMin || null, yearMax: entry.yrMax || null,
    };
    if (entry.radiusMi && entry.lat != null && entry.lng != null) {
      // Explicit per-watch radius, chosen when the watch was created.
      w.lat = entry.lat; w.lng = entry.lng; w.radiusMi = entry.radiusMi;
    } else if (!('radiusMi' in entry) && activeZipCoords) {
      // Legacy watches (pre radius picker): scope to the current search area,
      // matching the old behavior. New "Anywhere" watches send no center.
      w.lat = activeZipCoords.lat; w.lng = activeZipCoords.lng;
      w.radiusMi = effectiveRadiusMi() || 100;
    }
    const res = await YSApi.createWatch(w);
    entry.serverId = res.id;
    const list = loadWatchlist();
    const match = list.find(e => e.addedAt === entry.addedAt);
    if (match) { match.serverId = res.id; saveWatchlist(list); }
  } catch (e) { /* offline or lapsed Pro — retried on next auth change */ }
}

async function syncAllWatchesToServer() {
  if (!canCloudSync()) return;
  for (const entry of loadWatchlist()) await syncWatchToServer(entry);
}

async function updateCloudAlertsUi() {
  const panel = document.getElementById('cloud-alerts-panel');
  if (!panel) return;
  const apiMode = window.YSApi && YSApi.enabled();
  panel.style.display = apiMode ? '' : 'none';
  // ntfy is the self-hosted fallback — hide it once real push is available.
  const ntfy = document.getElementById('ntfy-panel');
  if (ntfy) ntfy.style.display = apiMode ? 'none' : '';
  if (!apiMode) return;
  const me = YSApi.getMe();
  const status = document.getElementById('cloud-alerts-status');
  const enableBtn = document.getElementById('cloud-push-enable');
  const testBtn = document.getElementById('cloud-push-test');
  if (!me) {
    status.textContent = 'Sign in (in the Pro sheet) to get alerts even when the app is closed.';
    enableBtn.style.display = 'none'; testBtn.style.display = 'none';
    return;
  }
  if (me.tier !== 'pro') {
    status.textContent = 'Your watches sync to your account — matches arrive in a weekly email digest. Instant push alerts are part of Pro.';
    enableBtn.style.display = 'none'; testBtn.style.display = 'none';
    return;
  }
  const on = await YSApi.pushEnabled();
  enableBtn.style.display = on ? 'none' : '';
  testBtn.style.display = on ? '' : 'none';
  status.textContent = on
    ? 'This device gets a push when a watched car hits a yard \u2014 even with the app closed.'
    : 'Watches sync to your account. Enable push on this device to get alerts with the app closed.';
}

function saveWatchlistFile() { /* watchlist lives in localStorage; nothing to write */ }

function requestNotifPermission() {
  if (!('Notification' in window)) {
    alert('Your browser does not support desktop notifications.');
    return;
  }
  Notification.requestPermission().then(perm => {
    const btn = document.getElementById('alert-notif-btn');
    if (perm === 'granted') {
      btn.textContent = 'Notifications Enabled';
      btn.style.background = 'var(--accent2)';
      btn.style.color = 'var(--bg)';
    } else {
      btn.textContent = 'Notifications Blocked';
      btn.style.background = 'var(--red)';
      btn.style.color = 'var(--bg)';
    }
  });
}

function checkAndNotify() {
  if (!('Notification' in window) || Notification.permission !== 'granted') return;
  if (!liveLoaded) return;
  const results = getWatchlistHits();
  const alerted = loadAlerted();
  let newHits = 0;
  results.forEach(r => {
    r.hits.forEach(v => {
      const key = `${v.id || v.vin || ''}:${v.year}:${v.make}:${v.model}`;
      if (!alerted[key]) {
        alerted[key] = new Date().toISOString();
        newHits++;
        const label = [r.entry.make, r.entry.model].filter(Boolean).join(' ');
        new Notification('YardScout alert', {
          body: `${v.year} ${v.make} ${v.model} at ${v.location}${v.vin && String(v.vin).replace(/[^A-Z0-9]/gi, '').length === 17 ? ' · VIN ' + String(v.vin).trim() : ''}${v.hasMatch ? ' — has flagged parts' : ''}`,
          icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="80" font-size="80">🔔</text></svg>',
          tag: key,
        });
      }
    });
  });
  if (newHits) saveAlerted(alerted);
  updateAlertsBadge();
}

function updateAlertsBadge() {
  const badge = document.getElementById('alerts-badge');
  const results = getWatchlistHits();
  const total = results.reduce((s, r) => s + r.hits.length, 0);
  badge.style.display = total > 0 ? '' : 'none';
  badge.textContent = total > 99 ? '99+' : total;
}

document.getElementById('alert-add-btn').addEventListener('click', addWatchItem);
document.getElementById('alert-notif-btn').addEventListener('click', requestNotifPermission);

/* ===== NTFY PHONE PUSH ===== */
(() => {
  const topicEl = document.getElementById('ntfy-topic');
  const statusEl = document.getElementById('ntfy-status');
  // Suggest a private-ish random topic on first visit; remember whatever they use.
  let topic = localStorage.getItem('jh_ntfy_topic');
  if (!topic) {
    topic = 'junkyard-' + Math.random().toString(36).slice(2, 8);
    localStorage.setItem('jh_ntfy_topic', topic);
  }
  topicEl.value = topic;
  topicEl.addEventListener('change', () => {
    const t = topicEl.value.trim().replace(/[^a-zA-Z0-9_-]/g, '');
    topicEl.value = t;
    if (t) localStorage.setItem('jh_ntfy_topic', t);
  });
  document.getElementById('ntfy-test').addEventListener('click', async () => {
    const t = topicEl.value.trim();
    if (!t) { statusEl.textContent = 'Enter a topic name first.'; return; }
    statusEl.textContent = 'Sending…';
    try {
      const r = await fetch('https://ntfy.sh/' + encodeURIComponent(t), {
        method: 'POST',
        body: 'Test received. Watchlist alerts will look like this.',
        headers: { 'Title': 'YardScout test', 'Tags': 'wrench' },
      });
      statusEl.textContent = r.ok
        ? 'Sent — check your phone (make sure the ntfy app is subscribed to "' + t + '").'
        : 'ntfy.sh returned an error — try a different topic name.';
    } catch (e) {
      statusEl.textContent = "Couldn't reach ntfy.sh — check your connection.";
    }
  });
})();
document.getElementById('alert-make').addEventListener('change', populateWatchModelOptions);
// "Anywhere" watches are the Pro tier of alerts — free radius tops out at 250 mi
// (mirrors the Live tab's distance cap). Snap back and pitch honestly.
document.getElementById('alert-radius').addEventListener('change', e => {
  if (!e.target.value && !isPro()) {
    e.target.value = '250';
    openUpgradeSheet('watch-anywhere');
  }
});
['alert-make', 'alert-yr-min', 'alert-yr-max'].forEach(id => {
  document.getElementById(id).addEventListener('keydown', e => {
    if (e.key === 'Enter') addWatchItem();
  });
});
/* Watch-model multi-select panel: open/close, search, toggle, clear. */
document.getElementById('alert-model-btn').addEventListener('click', e => {
  e.stopPropagation();
  const panel = document.getElementById('alert-model-panel');
  const opening = panel.style.display === 'none';
  panel.style.display = opening ? '' : 'none';
  if (opening) {
    const search = document.getElementById('alert-model-search');
    search.value = '';
    renderWatchModelList();
    if (matchMedia('(pointer: fine)').matches) search.focus();
  }
});
document.getElementById('alert-model-panel').addEventListener('click', e => e.stopPropagation());
document.addEventListener('click', () => {
  document.getElementById('alert-model-panel').style.display = 'none';
});
document.getElementById('alert-model-search').addEventListener('input', renderWatchModelList);
document.getElementById('alert-model-list').addEventListener('change', e => {
  const cb = e.target.closest('input[type="checkbox"]');
  if (!cb) return;
  if (cb.checked) watchSelectedModels.add(cb.dataset.model);
  else watchSelectedModels.delete(cb.dataset.model);
  updateWatchModelBtnLabel();
});
document.getElementById('alert-model-clear').addEventListener('click', () => {
  watchSelectedModels.clear();
  renderWatchModelList();
  updateWatchModelBtnLabel();
});
document.getElementById('alert-model-done').addEventListener('click', () => {
  document.getElementById('alert-model-panel').style.display = 'none';
});

(function initNotifBtn() {
  if ('Notification' in window && Notification.permission === 'granted') {
    const btn = document.getElementById('alert-notif-btn');
    btn.textContent = 'Notifications Enabled';
    btn.style.background = 'var(--accent2)';
    btn.style.color = 'var(--bg)';
  }
})();

/* ===== INIT ===== */
// The onboarding zip banner doesn't depend on inventory data — show it (or a
// shared-find suppression) immediately instead of after the 4MB fetch.
applyShareHash();
updateZipBanner();
loadLiveInventory();

// Offline + instant-launch cache. Needs a secure context (HTTPS or localhost) —
// silently skipped when served over plain LAN IP, active once on GitHub Pages.
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js').catch(() => {});
}

/* ===== iOS INSTALL HINT =====
 * Safari-on-iPhone users get a one-time tip to add the app to the home
 * screen. Skipped when already installed (standalone) or dismissed.
 * Test hook: ?installhint=1 forces it for QA. */
(function installHint() {
  const forced = new URLSearchParams(location.search).get('installhint') === '1';
  const isIOS = /iphone|ipod|ipad/i.test(navigator.userAgent)
    || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1); // iPadOS
  const standalone = window.matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
  if (!forced && (!isIOS || standalone || localStorage.getItem('ys_install_hint') === '1')) return;
  const el = document.getElementById('install-hint');
  if (!el) return;
  el.style.display = '';
  document.getElementById('install-hint-close').addEventListener('click', () => {
    localStorage.setItem('ys_install_hint', '1');
    el.style.display = 'none';
  });
})();

/* ===== ACCOUNT / API SESSION (active only in API mode — see api.js) =====
 * When the backend session reports a paid tier, the jh_pro gate is driven by
 * the ACCOUNT — and once inventory loads through the API, the server refuses
 * value data to free sessions anyway, so the client gate stops being the
 * enforcement and becomes presentation. */
if (window.YSApi) {
  YSApi.init({
    onAuthChange(me) {
      const paid = !!(me && me.tier && me.tier !== 'free');
      if (paid) {
        localStorage.setItem('jh_pro', '1');
        localStorage.setItem('jh_pro_source', 'account');
      } else if (localStorage.getItem('jh_pro_source') === 'account') {
        // Only claw back Pro that an account granted — never the dev toggle.
        localStorage.removeItem('jh_pro');
        localStorage.removeItem('jh_pro_source');
      }
      applyProGates();
      if (liveLoaded) renderLive();
      // Cloud alerts: mirror local watches to the account + refresh panel state.
      syncAllWatchesToServer();
      updateCloudAlertsUi();
    },
  });
  updateCloudAlertsUi();
  const pushEnableBtn = document.getElementById('cloud-push-enable');
  if (pushEnableBtn) pushEnableBtn.addEventListener('click', async () => {
    pushEnableBtn.disabled = true;
    const status = document.getElementById('cloud-alerts-status');
    try {
      await YSApi.enablePush();
      track('push-enabled');
      await updateCloudAlertsUi();
    } catch (e) {
      status.textContent = e.message || 'Could not enable push.';
    } finally {
      pushEnableBtn.disabled = false;
    }
  });
  const pushTestBtn = document.getElementById('cloud-push-test');
  if (pushTestBtn) pushTestBtn.addEventListener('click', async () => {
    pushTestBtn.disabled = true;
    const status = document.getElementById('cloud-alerts-status');
    try {
      const r = await YSApi.testPush();
      status.textContent = `Test sent to ${r.sent} device${r.sent === 1 ? '' : 's'} — you should feel a buzz.`;
    } catch (e) {
      status.textContent = e.message || 'Test failed.';
    } finally {
      pushTestBtn.disabled = false;
    }
  });
  // "Continue to payment" starts Stripe Checkout for whichever plan card is
  // selected. Not signed in yet → the sheet's sign-in form is right above.
  const co = document.getElementById('account-checkout');
  if (co) co.addEventListener('click', async () => {
    track('checkout-start/' + selectedPlan);
    co.disabled = true;
    try {
      await YSApi.checkout(selectedPlan);
    } catch (e) {
      YSApi.setStatus(e.code === 401
        ? 'Sign in first (link above) — your purchase needs an account to stick to.'
        : (e.message || 'Could not start checkout.'), true);
    } finally {
      co.disabled = false;
    }
  });
}
