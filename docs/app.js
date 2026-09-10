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

/* utpap = exact "Part Description" from utpap.com/1064Carpricelist.php (Ogden pricelist iframe on ogden-prices page)
 * pyp = exact "Description" from pyp.com per-location PriceList API
 * pap = exact "partname" from Pull-A-Part's per-location pricing API */
const PART_KEYWORD_MAP = [
  { kw: 'hid headlight',       pnp: 'HEADLIGHT COMP',               tap: 'HEADLIGHT COMPOSITE', utpap: 'HEADLAMP W/ TURN SIG', pyp: 'HEADLIGHT', pap: 'HEADLIGHT LED OR HID LAMP ASSEMBLY W/BALLAST' },
  { kw: 'led headlight',       pnp: 'HEADLIGHT COMP',               tap: 'HEADLIGHT COMPOSITE', utpap: 'HEADLAMP W/ TURN SIG', pyp: 'HEADLIGHT', pap: 'HEADLIGHT LED OR HID LAMP ASSEMBLY W/BALLAST' },
  { kw: 'headlight',           pnp: 'HEADLIGHT COMP',               tap: 'HEADLIGHT COMPOSITE', utpap: 'HEADLAMP W/ TURN SIG', pyp: 'HEADLIGHT', pap: 'HEADLIGHT ASSEMBLY (NON-HID/BALLAST)' },
  { kw: 'headlamp',            pnp: 'HEADLIGHT COMP',               tap: 'HEADLIGHT COMPOSITE', utpap: 'HEADLAMP W/ TURN SIG', pyp: 'HEADLIGHT', pap: 'HEADLIGHT ASSEMBLY (NON-HID/BALLAST)' },
  { kw: 'recaro seat',         pnp: 'SEAT-BUCK(EA)W/TRK (PWR)',     tap: 'BUCKET SEAT POWER', utpap: 'BUCKET SEAT ELCTRIC', pyp: 'SEAT WITH AIR BAG FRONT', pap: 'SEAT, BUCKET W/ POWER TRACK (LEATHER)' },
  { kw: 'stow-n-go 2nd',      pnp: 'SEAT-BUCK(EA)W/TRK (MAN)',     tap: 'BUCKET SEAT', utpap: 'BUCKET SEAT ELCTRIC', pyp: 'SEAT NO AIR BAG FRONT', pap: 'SEAT, BUCKET W/ MANUAL TRACK' },
  { kw: 'stow-n-go 3rd',      pnp: 'SEAT-REAR (EA)',               tap: 'SEAT SECTION', utpap: 'BENCH SEAT ELECTRIC', pyp: 'SEAT REAR', pap: 'SEAT, BENCH/3RD ROW MANUAL TRACK' },
  { kw: 'stow-n-go',          pnp: 'SEAT-BUCK(EA)W/TRK (MAN)',     tap: 'BUCKET SEAT', utpap: 'BUCKET SEAT ELCTRIC', pyp: 'SEAT NO AIR BAG FRONT', pap: 'SEAT, BUCKET W/ MANUAL TRACK' },
  { kw: '3rd row seat',        pnp: 'SEAT-REAR (EA)',               tap: 'SEAT SECTION', utpap: 'BENCH SEAT ELECTRIC', pyp: 'SEAT THIRD ROW', pap: 'SEAT, BENCH/3RD ROW MANUAL TRACK' },
  { kw: 'rear seat',           pnp: 'SEAT-REAR (EA)',               tap: 'SEAT SECTION', utpap: 'BENCH SEAT ELECTRIC', pyp: 'SEAT REAR', pap: 'SEAT, REAR - EACH SECTION (CLOTH)' },
  { kw: 'bench seat',          pnp: 'SEAT-BENCH W/TRK',             tap: 'SEAT BENCH', utpap: 'BENCH SEAT ELECTRIC', pyp: 'SEAT REAR', pap: 'SEAT, BENCH W/ POWER TRACK (LEATHER)' },
  { kw: 'bucket seat',         pnp: 'SEAT-BUCK(EA)W/TRK (PWR)',     tap: 'BUCKET SEAT POWER', utpap: 'BUCKET SEAT ELCTRIC', pyp: 'SEAT WITH AIR BAG FRONT', pap: 'SEAT, BUCKET W/ POWER TRACK (LEATHER)' },
  { kw: 'seat',                pnp: 'SEAT-BUCK(EA)W/TRK (PWR)',     tap: 'BUCKET SEAT POWER', utpap: 'BUCKET SEAT ELCTRIC', pyp: 'SEAT WITH AIR BAG FRONT', pap: 'SEAT, BUCKET W/ POWER TRACK (LEATHER)' },
  { kw: 'intercooler',         pnp: 'INTERCOOLER',                  tap: 'TURBO INTERCOOLER', utpap: 'TURBO INNER COOLER', pyp: 'INTERCOOLER', pap: 'TURBO INTERCOOLER' },
  { kw: 'heads-up display',    pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY' },
  { kw: 'touchscreen',         pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY' },
  { kw: 'infotainment',        pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY' },
  { kw: 'navigation',          pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'NAVIGATION UNIT', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY' },
  { kw: 'display',             pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY' },
  { kw: 'head unit',           pnp: 'RADIO',                        tap: 'RADIO', utpap: 'RADIO CD PLAYER', pyp: 'RADIO WITH DISPLAY', pap: 'RADIO  - W/CD OR MEDIA PLAYER' },
  { kw: 'radio',               pnp: 'RADIO',                        tap: 'RADIO', utpap: 'RADIO CD PLAYER', pyp: 'RADIO WITH DISPLAY', pap: 'RADIO  - W/CD OR MEDIA PLAYER' },
  { kw: 'front bumper',        pnp: 'BUMPER COMP',                  tap: 'BUMPR CVER W/RENFORC', utpap: 'BUMPER', pyp: 'FRONT BUMPER (STEEL)', pap: 'BUMPER COVER ASSEMBLY' },
  { kw: 'bumper cover',        pnp: 'BUMPER COVER (PLAST/RUBR)',    tap: 'BUMPER COVER', utpap: 'BUMPER', pyp: 'BUMPER COVER, FRONT', pap: 'BUMPER COVER' },
  { kw: 'bumper',              pnp: 'BUMPER COMP',                  tap: 'BUMPR CVER W/RENFORC', utpap: 'BUMPER', pyp: 'FRONT BUMPER (STEEL)', pap: 'BUMPER STEEL OR ALUMINUM' },
  { kw: 'steering wheel',      pnp: 'STEERING WHEEL',               tap: 'STEERNG WHL W/SWITCH', utpap: 'STEERING WHEEL', pyp: 'STEERING WHEEL', pap: 'STEERING WHEEL' },
  { kw: 'spoiler',             pnp: 'SPOILERS - BOLT ON (EA)',      tap: 'SPOILER', utpap: 'SPOILER', pyp: 'SPOILER REAR', pap: 'SPOILER - BOLT ON (EACH)' },
  { kw: 'fog light',           pnp: 'FOG LAMPS EACH',               tap: 'HEADLIGHT COMP BULB', utpap: 'FOG LIGHT', pyp: 'FRONT LAMP (FOG/PARKING/TURN/MARKER)', pap: 'FOG LAMP (EACH)' },
  { kw: 'fog lamp',            pnp: 'FOG LAMPS EACH',               tap: 'HEADLIGHT COMP BULB', utpap: 'FOG LIGHT', pyp: 'FRONT LAMP (FOG/PARKING/TURN/MARKER)', pap: 'FOG LAMP (EACH)' },
  { kw: 'brake caliper',       pnp: 'BRAKE CALIPER',                tap: 'BRAKE CALIPER', utpap: 'BRAKE CALIPER 2-4 PI', pyp: 'BRAKE CALIPER', pap: 'BRAKE CALIPER' },
  { kw: 'caliper',             pnp: 'BRAKE CALIPER',                tap: 'BRAKE CALIPER', utpap: 'BRAKE CALIPER 2-4 PI', pyp: 'BRAKE CALIPER', pap: 'BRAKE CALIPER' },
  { kw: 'mirror',              pnp: 'MIRROR-DOOR OUTSIDE(ELEC)',    tap: 'POWER MIRROR - DOOR', utpap: 'DOOR POWER MIRROR', pyp: 'MIRROR (SIDE VIEW)', pap: 'DOOR MIRROR, OUTSIDE ELECTRIC REMOTE' },
  { kw: 'amplifier',           pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER' },
  { kw: 'amp',                 pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER' },
  { kw: 'speaker',             pnp: 'SPEAKER EACH',                 tap: 'SPEAKER', utpap: 'RADIO SPEAKER', pyp: 'RADIO SPEAKER', pap: 'SPEAKER (ANY)' },
  { kw: 'panoramic sunroof',   pnp: 'SUN ROOF ASSY',               tap: 'SUNROOF ASSY+MOTOR', utpap: 'SUNROOF/T-TOP', pyp: 'ROOF GLASS (SUN ROOF)', pap: 'SUNROOF/COVER/SHADE ASSEMBLY W/MOTOR' },
  { kw: 'sunroof',             pnp: 'SUN ROOF ASSY',               tap: 'SUN ROOF ASSEMBLY', utpap: 'SUNROOF/T-TOP', pyp: 'ROOF GLASS (SUN ROOF)', pap: 'SUNROOF/COVER/SHADE ASSEMBLY W/MOTOR' },
  { kw: 'sliding door motor',  pnp: 'DOOR/GATE MOTOR',             tap: 'SIDE DOOR SLIDE MTR', utpap: 'ELECTRIC MODULE', pyp: 'SLIDING DOOR MOTOR', pap: 'DOOR/HATCH MOTOR, (SLIDING VAN/SUV)' },
  { kw: 'door motor',          pnp: 'DOOR/GATE MOTOR',             tap: 'SIDE DOOR SLIDE MTR', utpap: 'ELECTRIC MODULE', pyp: 'SLIDING DOOR MOTOR', pap: 'DOOR/HATCH MOTOR, (SLIDING VAN/SUV)' },
  { kw: 'liftgate',            pnp: 'DOOR/GATE MOTOR',             tap: 'SIDE DOOR SLIDE MTR', utpap: 'TAIL GATE/ ENDGATE', pyp: 'DECKLID/TAILGATE (BARE)', pap: 'DOOR/HATCH MOTOR, (SLIDING VAN/SUV)' },
  { kw: 'sliding door control', pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'COMPUTER', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL' },
  { kw: 'control module',      pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'COMPUTER', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL' },
  { kw: 'radar',               pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'COMPUTER', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL' },
  { kw: 'camera',              pnp: 'CONTROL MODULE',              tap: 'REVERSE CAMERA', utpap: 'COMPUTER', pyp: 'SENSOR CAMERAS', pap: 'CAMERA, ON BOARD OR BACK UP' },
  { kw: 'module',              pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'COMPUTER', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL' },
  { kw: 'roof rack',           pnp: 'LUGGAGE/SKI RACK',            tap: 'LUGGAGE RACK', utpap: 'LUGGAGE RACK', pyp: 'ROOF RACK ASSEMBLY', pap: 'LUGGAGE RACK' },
  { kw: 'crossbar',            pnp: 'LUGGAGE/SKI RACK',            tap: 'CARGO RACK', utpap: 'LUGGAGE RACK', pyp: 'ROOF RACK RAIL/ CROSS BAR (EACH)', pap: 'LUGGAGE RACK CROSS BAR' },
  { kw: 'grille',              pnp: 'GRILLE',                      tap: 'GRILLE', utpap: 'GRILLE LRG', pyp: 'GRILLE', pap: 'GRILLE PLASTIC (BARE) - ANY' },
  { kw: 'running board',       pnp: 'RUNNING BOARDS (EACH)',       tap: 'RUNNING BOARD (EACH)', utpap: 'RUNNING BOARD', pyp: 'RUNNING BOARD', pap: 'RUNNING BOARD (EACH)' },
  { kw: 'fender flare',        pnp: 'FENDER FLARE (EA)',           tap: 'FENDER TRIM/FLARES', utpap: 'FENDER EXTENSION', pyp: 'FENDER EXTENSION', pap: 'FENDER FLARE OR SKIRT' },
  { kw: 'window regulator',    pnp: 'WINDOW REG W/MOTOR ELEC',    tap: 'WINDOW REG W/MOTOR', utpap: 'WINDOW REGULATOR', pyp: 'WINDOW REGULATOR FRONT (ELECTRIC)', pap: 'WINDOW REGULATOR W/MOTOR' },
  { kw: 'tail light',          pnp: 'TAILLIGHT',                   tap: 'TAIL LIGHT ASSY ANY', utpap: 'TAIL LIGHT ASSY LRG', pyp: 'TAILLIGHT (QUARTER MOUNTED)', pap: 'TAILLIGHT ASSEMBLY - SINGLE SIDE' },
  { kw: 'taillight',           pnp: 'TAILLIGHT',                   tap: 'TAIL LIGHT ASSY ANY', utpap: 'TAIL LIGHT ASSY LRG', pyp: 'TAILLIGHT (QUARTER MOUNTED)', pap: 'TAILLIGHT ASSEMBLY - SINGLE SIDE' },
  { kw: 'wireless charging',   pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'ELECTRIC MODULE', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL' },
  { kw: 'charging pad',        pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'ELECTRIC MODULE', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL' },
  { kw: 'entertainment',       pnp: 'LRG MULTIFUNCT DISPLAY',      tap: 'DVD PLAYER', utpap: 'RADIO CD PLAYER', pyp: 'GPS TV SCREEN', pap: 'VIDEO SCREEN' },
  { kw: 'dvd',                 pnp: 'LRG MULTIFUNCT DISPLAY',      tap: 'DVD PLAYER', utpap: 'RADIO CD PLAYER', pyp: 'GPS TV SCREEN', pap: 'VIDEO SCREEN' },
  { kw: 'cable',               pnp: 'CABLE/PUSH-PULL',             tap: 'CABLE (ANY)', utpap: 'SHIFTER CABLE', pyp: 'CABLE', pap: 'CABLE - BRAKE/CLUTCH/SHIFTER/THROTTLE/RELEASE' },
  { kw: 'track',               pnp: 'SEAT TRACK ELEC W/MOTOR (EA)', tap: 'SEAT TRACKSET+MOTOR', utpap: 'SEAT TRACK ELECTRIC', pyp: 'SEAT TRACK, (ELECTRIC)', pap: 'SEAT TRACK, ELECTRIC W/MOTOR' },
  { kw: 'dash pad',            pnp: 'DASH PAD',                    tap: 'DASH PAD', utpap: 'DASH PAD', pyp: 'DASH PAD', pap: 'DASH PAD (OVER 24in LENGTH)' },
  { kw: 'console lid',         pnp: 'CONSOLE LID',                 tap: 'CONSOLE LID', utpap: 'CONSOLE LID', pyp: 'CENTER CONSOLE', pap: 'CONSOLE LID' },
  { kw: 'console',             pnp: 'CONSOLE',                     tap: 'CONSOLE (ANY)', utpap: 'CONSOLE BARE', pyp: 'CENTER CONSOLE', pap: 'CONSOLE (OVER 16in LENGTH)' },
  { kw: 'mudflap',             pnp: 'MUDFLAP',                     tap: 'MUDFLAP', utpap: 'MUD FLAP', pyp: 'MUD FLAP/SPLASH GUARD', pap: 'MUD FLAP OR SPLASH GUARD' },
  { kw: 'emblem',              pnp: 'EMBLEM',                      tap: 'EMBLEM (ANY)', utpap: 'EMBLEM', pyp: 'EMBLEMS', pap: 'EMBLEM' },
  { kw: 'wiper motor',         pnp: 'WIPER MOTOR',                 tap: 'WIPER MOTOR', utpap: 'WIPER MOTOR', pyp: 'ELECTRIC WIPER MOTOR, WINDSHIELD', pap: 'WINDSHIELD WIPER MOTOR' },
  { kw: 'actuator',            pnp: 'ACTUATOR',                    tap: 'ACTUATOR', utpap: 'DOOR LOCK ACTUATOR', pyp: 'ACTUATOR', pap: 'ACTUATOR' },
  { kw: 'transfer case motor', pnp: 'TRANSFER CASE MOTOR',         tap: 'TRANSFER CASE MOTOR', utpap: 'TRANSFERCAS ACTUATOR', pyp: 'TRANSFER CASE MOTOR', pap: '4 WHEEL DRIVE ACTUATOR VACUUM OR ELECTRIC' },
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
  pin: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>',
  heart: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 14c1.5-1.46 3-3.2 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.04 3 5.5l7 7Z"/></svg>',
  copy: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',
  check: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>',
  x: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg>',
  lock: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
  chev: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>',
  share: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v13M8 7l4-4 4 4"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/></svg>',
};

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

function csvEscapeCell(val) {
  const s = String(val ?? '');
  if (/[",\r\n]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
  return s;
}

function exportLiveCsv() {
  // Exports are Pro: a bulk download of the dataset is exactly the thing the
  // free tier shouldn't hand out.
  if (!isPro()) { openUpgradeSheet('export-csv'); return; }
  if (!liveLoaded) return alert('No inventory loaded.');
  const rows = getFilteredLive();
  const header = ['year', 'make', 'model', 'vin', 'location', 'row', 'hasMatch', 'dateAdded', 'displayName', 'vpicDecodeWell', 'vpicTrim', 'vpicTrimQuality', 'vpicSeries', 'partsFlagged', 'maxValue', 'partsSummary'];
  const lines = [header.join(',')];
  for (const v of rows) {
    const cells = [
      csvEscapeCell(v.year),
      csvEscapeCell(v.make),
      csvEscapeCell(v.model),
      csvEscapeCell(v.vin),
      csvEscapeCell(v.location),
      csvEscapeCell(v.row),
      csvEscapeCell(v.hasMatch),
      csvEscapeCell(v.dateAdded),
      csvEscapeCell(v.displayName),
      csvEscapeCell(v.vpicDecodeWell),
      csvEscapeCell(v.vpicTrim),
      csvEscapeCell(v.vpicTrimQuality),
      csvEscapeCell(v.vpicSeries),
      csvEscapeCell((v.topParts || []).map(p => p.name).join('; ')),
      csvEscapeCell(v.maxValue),
      csvEscapeCell((v.topParts || []).map(p => p.name + ':' + p.low + '-' + p.high).join('; ')),
    ];
    lines.push(cells.join(','));
  }
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'yardscout-live-' + new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-') + '.csv';
  a.click();
  URL.revokeObjectURL(url);
}

function exportLiveJson() {
  if (!isPro()) { openUpgradeSheet('export-json'); return; }
  if (!liveLoaded) return alert('No inventory loaded.');
  const vehicles = getFilteredLive();
  const payload = {
    schemaVersion: 1,
    sourceScrapedAt: liveScrapedAt,
    exportedAt: new Date().toISOString(),
    note: 'Filtered rows only (current Live tab filters)',
    vehicles,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'yardscout-live-' + new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-') + '.json';
  a.click();
  URL.revokeObjectURL(url);
}

async function loadAllPricing() {
  // All five price lists fetch in parallel (this used to be a serial
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
  populateLiveMakeFilter();
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
        <h3>No Live Inventory Yet</h3>
        <p>The live inventory file wasn't found. Run the scraper to generate it:</p>
        <code>python scraper/junkyard_scraper.py --save --all</code>
        <p style="margin-top:1rem;">This scans the supported junkyard chains and cross-references every vehicle against the parts database. The output file <strong>inventory_live.json</strong> will appear in this directory.</p>
        <p style="margin-top:0.75rem;"><strong>Tip:</strong> Open this page via a local server (not <code>file://</code>), or the browser cannot load the JSON. <strong>cd into the folder that contains</strong> <code>index.html</code> (the <code>yardscout</code> project folder), then run <code>cd docs && python3 -m http.server 8765</code> and open <code>http://localhost:8765/index.html</code>. If you see 404, the server was started in the wrong directory.</p>
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

function populateLiveMakeFilter() {
  const makes = [...new Set(liveInventory.map(v => v.make))].sort();
  const sel = document.getElementById('live-filter-make');
  sel.innerHTML = '<option value="">All makes</option>';
  makes.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m;
    opt.textContent = m + ' (' + liveInventory.filter(v => v.make === m).length + ')';
    sel.appendChild(opt);
  });
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
  ['live-radius', 'live-filter-make', 'live-filter-location', 'live-filter-match', 'live-sort']
    .forEach(id => { const el = document.getElementById(id); if (el) el.disabled = !hasLoc; });
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

let upgradeTrigger = 'unknown';
function openUpgradeSheet(trigger) {
  upgradeTrigger = trigger || 'unknown';
  track('pro-lock/' + upgradeTrigger);
  // Returning waitlist members see the thank-you state, not the form again.
  const done = localStorage.getItem('jh_waitlist_email');
  document.getElementById('upgrade-form-wrap').style.display = done ? 'none' : '';
  document.getElementById('upgrade-thanks').style.display = done ? '' : 'none';
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
  // Record the price the user actually saw (single source of truth: the tier
  // card in the DOM) so future price changes can be compared against signups
  // without building an A/B system.
  const priceEl = document.querySelector('#upgrade-sheet .tier-card');
  const shownPrice = (priceEl && priceEl.dataset.price) || '';
  const entry = { email, trigger: upgradeTrigger, price: shownPrice, at: new Date().toISOString() };
  // Local backup log (survives even if the ntfy POST fails).
  try {
    const log = JSON.parse(localStorage.getItem('jh_waitlist_log') || '[]');
    log.push(entry);
    localStorage.setItem('jh_waitlist_log', JSON.stringify(log));
  } catch (e) { /* ignore */ }
  try {
    await fetch('https://ntfy.sh/' + WAITLIST_NTFY_TOPIC, {
      method: 'POST',
      body: `${email} | trigger: ${entry.trigger} | price: $${entry.price} | ${entry.at}`,
      headers: { 'Title': 'YardScout Pro signup', 'Tags': 'moneybag' },
    });
  } catch (e) { /* local log still has it */ }
  localStorage.setItem('jh_waitlist_email', email);
  track('waitlist-submitted');
  btn.disabled = false;
  btn.textContent = 'Notify Me';
  document.getElementById('upgrade-form-wrap').style.display = 'none';
  document.getElementById('upgrade-thanks').style.display = '';
}

/* Re-apply every gate; called at startup and whenever pro state flips. */
function applyProGates() {
  const pro = isPro();
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
  // Export buttons carry a small "Pro" tag for free users only.
  document.querySelectorAll('.export-pro-tag').forEach(t => { t.style.display = pro ? 'none' : ''; });
  // Value-intelligence sorts are Pro: a free user sorting by value would get
  // the ranking (the actual product) with the dollar signs merely hidden.
  const sortSel = document.getElementById('live-sort');
  [...sortSel.options].forEach(o => {
    if (!o.dataset.base) o.dataset.base = o.textContent;
    o.textContent = (!pro && PRO_SORTS.has(o.value)) ? o.dataset.base + ' \u2014 Pro' : o.dataset.base;
  });
  if (!pro && PRO_SORTS.has(sortSel.value)) sortSel.value = FREE_DEFAULT_SORT;
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
    const lk = lookupYardCost(p.name, s.location);
    const cost = lk.cost != null ? lk.cost : 0;
    if (lk.cost == null) unknownCost = true;
    // "If equipped" (trim-unconfirmed) parts only raise the high end; the low
    // end assumes the car doesn't have them.
    if (p.trim_status === 'unconfirmed') {
      hi += p.high - cost;
    } else {
      lo += p.low - cost;
      hi += p.high - cost;
    }
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
                <div class="saved-item-sub">${best ? best + (s.topParts.length > 1 ? ' +' + (s.topParts.length - 1) + ' more' : '') : 'No flagged parts'}</div>
              </div>
              ${range && range.hi > 0 ? (isPro()
                ? `<div class="saved-item-profit" title="${range.unknownCost ? 'Resale estimate — pull cost not on this yard\u2019s published price list, check at the yard' : 'Estimated range if parts are good, after this yard\u2019s list pull costs'}">${formatPrice(range.lo)}&ndash;${formatPrice(range.hi)}${range.unknownCost ? '<small style="display:block;font-weight:400;opacity:0.7;">resale</small>' : ''}</div>`
                : `<div class="saved-item-profit locked-blur" role="button" onclick="openUpgradeSheet('saved-value')">$400&ndash;$900</div>`) : ''}
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

  const search = document.getElementById('live-search').value.toLowerCase();
  const makeFilter = document.getElementById('live-filter-make').value;
  const matchFilter = document.getElementById('live-filter-match').value;
  const locationFilter = document.getElementById('live-filter-location').value;
  let sortBy = document.getElementById('live-sort').value;
  // Belt & suspenders: value sorts never apply for free even if the select
  // was tampered with.
  if (!isPro() && PRO_SORTS.has(sortBy)) sortBy = FREE_DEFAULT_SORT;
  const radiusMi = effectiveRadiusMi();

  let filtered = liveInventory.filter(v => {
    if (makeFilter && v.make !== makeFilter) return false;
    if (locationFilter && v.location !== locationFilter) return false;
    if (activeZipCoords && radiusMi) {
      const d = vehicleDistanceMi(v);
      if (d == null || d > radiusMi) return false;
    }
    if (matchFilter === 'match' && !v.hasMatch) return false;
    // Confirmed from the VIN decode only — cars with unknown transmission are
    // excluded rather than guessed at.
    if (matchFilter === 'manual' && !isConfirmedManual(v)) return false;
    if (search) {
      const hay = [v.year, v.make, v.model, v.location, v.city, v.displayName, v.vin,
        v.vpicDecodeWell, v.vpicTrim, v.vpicSeries, v.vpicDriveType,
        isConfirmedManual(v) ? 'manual' : '',
        ...(v.topParts || []).map(p => p.name)].join(' ').toLowerCase();
      return hay.includes(search);
    }
    return true;
  });

  function totalProfit(v) {
    if (!v.topParts || !v.topParts.length) return 0;
    return v.topParts.reduce((sum, p) => {
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
  const bestSpeed = v => v.topParts && v.topParts.length ? Math.max(...v.topParts.map(p => speedRk(p.sell_speed))) : 0;
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

  const focusBanner = focusedCarKey ? `
    <div class="focus-banner" style="grid-column:1/-1;">
      <span>Shared find &mdash; showing this car from the latest scan.</span>
      <button type="button" class="btn" onclick="jhClearFocus()">See all cars</button>
    </div>` : '';

  document.getElementById('live-grid').innerHTML = focusBanner + vehiclesToRender.map(v => {
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
      let totalCost = 0, lowSum = 0, highSum = 0, bestPart = null, bestHigh = -Infinity;
      let anyUnknownCost = false;
      const speedRk = s => s === 'Fast' ? 3 : s === 'Medium' ? 2 : s === 'Slow' ? 1 : 0;
      let demandRk = 0;
      const chainLabel = { pnp: 'PnP list', tap: 'TAP list', utpap: 'UTPAP list', pyp: 'PYP list', pap: 'PAP list' };
      const chainTitle = {
        pnp: 'Pick-n-Pull published price',
        tap: 'Tear-A-Part published price',
        utpap: 'Utah Pic-A-Part published price',
        pyp: 'This Pick Your Part yard\u2019s published price',
        pap: 'This Pull-A-Part yard\u2019s published price',
      };
      const partRows = v.topParts.map(p => {
        const lookup = lookupYardCost(p.name, v.location);
        const hasCost = lookup.cost != null;
        const yardCost = hasCost ? lookup.cost : 0;
        if (!hasCost) anyUnknownCost = true;
        const pHigh = Math.round(p.high - yardCost);
        // Trim-unconfirmed parts ("if equipped") only contribute to the HIGH
        // end of the range — the low end assumes the car doesn't have them,
        // so the range never overstates a car whose trim we can't verify.
        const ifEquipped = p.trim_status === 'unconfirmed';
        if (ifEquipped) {
          highSum += p.high - yardCost;
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
        // Free tier: part names/rarity/channels stay visible, but dollar values
        // and demand speed are blurred placeholders (real numbers never render).
        if (!isPro()) {
          return `
            <li class="part-item" style="flex-wrap:wrap;">
              <span class="part-name">${p.name}</span>
              <span class="part-rarity ${rarityClass(p.rarity)}">${p.rarity}</span>${trimMark}
              <span class="part-cost locked-blur" role="button" onclick="openUpgradeSheet('part-value')">$28 list</span>
              <span class="part-price locked-blur" role="button" onclick="openUpgradeSheet('part-value')">sells $250&ndash;$600</span>
              ${p.sell_at ? `<div style="width:100%;display:flex;align-items:center;gap:0.4rem;margin-top:0.1rem;flex-wrap:wrap;">
                <span class="sell-badge sell-medium locked-blur" role="button" onclick="openUpgradeSheet('part-value')">Steady seller</span>
                <span class="sell-channel">Sell on: ${p.sell_at}</span>${localNote}
              </div>` : ''}
            </li>`;
        }
        return `
          <li class="part-item" style="flex-wrap:wrap;">
            <span class="part-name">${p.name}</span>
            <span class="part-rarity ${rarityClass(p.rarity)}">${p.rarity}</span>${trimMark}
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
      const demand = demandRk === 3
        ? { cls: 'demand-fast', label: 'Sells fast' }
        : demandRk === 1
        ? { cls: 'demand-slow', label: 'Slow mover' }
        : { cls: 'demand-steady', label: 'Steady seller' };
      cardStyle = `--tier-color:var(--${demandRk === 3 ? 'demand-fast' : demandRk === 1 ? 'demand-slow' : 'demand-steady'});`;
      const rangeText = anyUnknownCost
        ? `resale ~${formatPrice(rangeLow)}&ndash;${formatPrice(rangeHigh)} if parts are good &middot; pull cost: check yard price list`
        : `e.g. ${formatPrice(rangeLow)}&ndash;${formatPrice(rangeHigh)} if parts are good &middot; ${formatPrice(Math.round(totalCost))} to pull`;
      profitLine = rangeHigh > 0
        ? (isPro() ? `
        <div class="profit-line">
          <span class="demand-badge ${demand.cls}">${demand.label}</span>
          <span class="range-text">${rangeText}</span>
        </div>` : `
        <div class="profit-line">
          <button type="button" class="lock-chip" onclick="openUpgradeSheet('card-value')">${ICON.lock} See what this is worth &mdash; Pro</button>
        </div>`)
        : '';
      partsBlock = `
        <details class="parts-details">
          <summary>Came with ${v.topParts.length} part${v.topParts.length > 1 ? 's' : ''} worth a look &middot; top: ${bestPart} <span class="chev">${ICON.chev}</span></summary>
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
            <div class="live-card-location">${ICON.pin} <span class="loc-name">${v.location}</span>${(() => { const d = vehicleDistanceMi(v); return d != null ? ' <span class="dist">&middot; ' + Math.round(d) + ' mi</span>' : ''; })()}${v.row ? '<span class="live-card-row">Row ' + v.row + '</span>' : ''}</div>
            <div class="car-meta">Added ${dateStr}${freshNote}${vinMetaHtml(v)}</div>
            ${specBits.length ? `<div class="car-meta car-specs">${specBits.map(escapeHtml).join(' &middot; ')}</div>` : ''}
            ${lotClock}
          </div>
          <div class="car-badges">
            ${isConfirmedManual(v) ? '<span class="badge badge-manual" title="Manual transmission, confirmed from this car\u2019s VIN decode \u2014 never inferred">Manual</span>' : ''}
            ${statusBadge}
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
let _searchDebounce = null;
document.getElementById('live-search').addEventListener('input', () => {
  clearTimeout(_searchDebounce);
  _searchDebounce = setTimeout(renderLive, 180);
});
document.getElementById('live-filter-make').addEventListener('change', renderLive);
document.getElementById('live-filter-location').addEventListener('change', renderLive);
let _lastFreeSort = FREE_DEFAULT_SORT;
document.getElementById('live-sort').addEventListener('change', e => {
  const val = e.target.value;
  if (PRO_SORTS.has(val) && !isPro()) {
    e.target.value = _lastFreeSort;   // snap back, pitch honestly
    openUpgradeSheet('sort-' + val);
    return;
  }
  if (!PRO_SORTS.has(val)) _lastFreeSort = val;
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
document.getElementById('live-refresh-btn').addEventListener('click', () => {
  alert('To refresh live inventory data, run this in your terminal:\n\npython scraper/junkyard_scraper.py --save --all\n\nThen reload this page.');
});
document.getElementById('live-export-csv').addEventListener('click', exportLiveCsv);
document.getElementById('live-export-json').addEventListener('click', exportLiveJson);

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
            <div class="live-card-location">${ICON.pin} <span class="loc-name">${escapeHtml(place) || 'Location unknown'}</span>${distTxt}</div>
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
      const hitCount = r.hits.length;
      return `<div class="watchlist-item">
        <div class="wl-info">
          <span class="wl-name">${label}</span>
          <span class="wl-detail">${yrLabel}${e.matchOnly ? ' &middot; Parts only' : ''}</span>
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
            <div class="live-card-location">${ICON.pin} <span class="loc-name">${v.location}</span>${(() => { const d = vehicleDistanceMi(v); return d != null ? ' <span class="dist">&middot; ' + Math.round(d) + ' mi</span>' : ''; })()}${v.row ? '<span class="live-card-row">Row ' + v.row + '</span>' : ''}</div>
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
                    <span class="part-rarity ${rarityClass(p.rarity)}">${p.rarity}</span>
                    ${isPro()
                      ? `<span class="part-price">${formatPrice(p.low)}&ndash;${formatPrice(p.high)}</span>`
                      : `<span class="part-price locked-blur" role="button" onclick="openUpgradeSheet('alerts-value')">$100&ndash;$400</span>`}
                  </li>
                `).join('')}
              </ul>
            </div>
          </details>
        ` : ''}
      </div>`;
  }).join('');
}

function addWatchItem() {
  const make = document.getElementById('alert-make').value.trim();
  const model = document.getElementById('alert-model').value.trim();
  if (!make && !model) return alert('Enter at least a make or model.');
  const yrMin = parseInt(document.getElementById('alert-yr-min').value) || null;
  const yrMax = parseInt(document.getElementById('alert-yr-max').value) || null;
  const matchOnly = document.getElementById('alert-match-only').checked;
  const watchlist = loadWatchlist();
  watchlist.push({ make, model, yrMin, yrMax, matchOnly, addedAt: new Date().toISOString() });
  saveWatchlist(watchlist);
  document.getElementById('alert-make').value = '';
  document.getElementById('alert-model').value = '';
  document.getElementById('alert-yr-min').value = '';
  document.getElementById('alert-yr-max').value = '';
  renderAlerts();
  saveWatchlistFile();
  checkAndNotify();
}

function removeWatchItem(idx) {
  const watchlist = loadWatchlist();
  watchlist.splice(idx, 1);
  saveWatchlist(watchlist);
  renderAlerts();
  saveWatchlistFile();
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
['alert-make', 'alert-model', 'alert-yr-min', 'alert-yr-max'].forEach(id => {
  document.getElementById(id).addEventListener('keydown', e => {
    if (e.key === 'Enter') addWatchItem();
  });
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
