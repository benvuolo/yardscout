/* Junkyard Hunter — application logic (loading, filtering, rendering, saved list, alerts). */
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
function lookupYardCost(partName, location) {
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
function vinMetaHtml(v) {
  if (!v.vin || !String(v.vin).trim()) return '';
  const show = String(v.vin).trim();
  const dup = v.vinDuplicate
    ? ' <span class="badge" style="background:var(--blue-soft);color:var(--blue);font-size:0.62rem;" title="Same VIN appears at more than one yard in this file">Also at another yard</span>'
    : '';
  const copyBtn = show.length >= 11
    ? `<button type="button" class="btn-copy-vin" data-vin="${escapeHtml(show)}" title="Copy VIN">Copy</button>`
    : '';
  let vpic = '';
  const vt = v.vpicTrim != null ? String(v.vpicTrim).trim() : '';
  const decodeWell = v.vpicDecodeWell === true;
  if (vt) {
    const q = v.vpicTrimQuality;
    const ambTitle = 'NHTSA returned a multi-trim list for this model; matching uses yard title, not this blob';
    const okTitle = 'VIN decoded well: specific trim from NHTSA VPIC (used for trim-gated parts)';
    if (q === 'usable' || decodeWell) {
      vpic = ` <span class="badge" style="background:var(--green-soft);color:var(--accent2);font-size:0.62rem;" title="${escapeHtml(okTitle)}">VIN trim OK</span> <span class="badge" style="background:var(--purple-soft);color:var(--purple);font-size:0.62rem;" title="${escapeHtml(okTitle)}">${escapeHtml(vt)}</span>`;
    } else if (q === 'ambiguous') {
      vpic = ` <span class="badge" style="background:var(--surface3);color:var(--text-dim);font-size:0.62rem;" title="${escapeHtml(ambTitle)}">VPIC: multi-trim</span>`;
    }
  }
  return ` &middot; VIN: <strong class="mono-vin">${escapeHtml(show)}</strong>${copyBtn}${dup}${vpic}`;
}

function csvEscapeCell(val) {
  const s = String(val ?? '');
  if (/[",\r\n]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
  return s;
}

function exportLiveCsv() {
  if (!liveLoaded) return alert('No inventory loaded.');
  const rows = getFilteredLive();
  const header = ['year', 'make', 'model', 'vin', 'location', 'row', 'hasMatch', 'maxValue', 'dateAdded', 'displayName', 'vpicDecodeWell', 'vpicTrim', 'vpicTrimQuality', 'vpicSeries', 'partsSummary'];
  const lines = [header.join(',')];
  for (const v of rows) {
    const partsSummary = (v.topParts || []).map(p => p.name + ':' + p.low + '-' + p.high).join('; ');
    lines.push([
      csvEscapeCell(v.year),
      csvEscapeCell(v.make),
      csvEscapeCell(v.model),
      csvEscapeCell(v.vin),
      csvEscapeCell(v.location),
      csvEscapeCell(v.row),
      csvEscapeCell(v.hasMatch),
      csvEscapeCell(v.maxValue),
      csvEscapeCell(v.dateAdded),
      csvEscapeCell(v.displayName),
      csvEscapeCell(v.vpicDecodeWell),
      csvEscapeCell(v.vpicTrim),
      csvEscapeCell(v.vpicTrimQuality),
      csvEscapeCell(v.vpicSeries),
      csvEscapeCell(partsSummary),
    ].join(','));
  }
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'junkyard-hunter-live-' + new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-') + '.csv';
  a.click();
  URL.revokeObjectURL(url);
}

function exportLiveJson() {
  if (!liveLoaded) return alert('No inventory loaded.');
  const rows = getFilteredLive();
  const payload = {
    schemaVersion: 1,
    sourceScrapedAt: liveScrapedAt,
    exportedAt: new Date().toISOString(),
    note: 'Filtered rows only (current Live tab filters)',
    vehicles: rows,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'junkyard-hunter-live-' + new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-') + '.json';
  a.click();
  URL.revokeObjectURL(url);
}

async function loadAllPricing() {
  try {
    const resp = await fetch('data/picknpull_pricing.json');
    if (resp.ok) {
      const data = await resp.json();
      data.forEach(p => { pnpPricing[p.description] = p; });
    }
  } catch (e) { /* PnP pricing not available */ }
  try {
    const resp = await fetch('data/utpap_pricing.json');
    if (resp.ok) {
      const data = await resp.json();
      data.forEach(p => { utpapPricing[p.description] = p; });
    }
  } catch (e) { /* Utah Pic-A-Part pricing not available */ }
  try {
    const resp = await fetch('data/tearapart_pricing.json');
    if (resp.ok) {
      const data = await resp.json();
      data.forEach(p => { tapPricing[p.description] = p; });
    }
  } catch (e) { /* TAP pricing not available */ }
  try {
    const resp = await fetch('data/pyp_pricing.json');
    if (resp.ok) pypPricing = await resp.json();
  } catch (e) { /* PYP pricing not available */ }
  try {
    const resp = await fetch('data/pap_pricing.json');
    if (resp.ok) papPricing = await resp.json();
  } catch (e) { /* PAP pricing not available */ }
}

async function loadLiveInventory() {
  await loadAllPricing();
  try {
    const resp = await fetch('data/inventory_live.json');
    if (!resp.ok) throw new Error('not found');
    const raw = await resp.json();
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
        const vp = vpic[String(i)];
        if (vp) {
          v.vpicTrim = vp[0]; v.vpicTrimQuality = vp[1];
          v.vpicDecodeWell = vp[1] === 'usable';
          if (vp[2]) v.vpicSeries = vp[2];
          if (vp[3]) v.vpicDriveType = vp[3];
        }
        return v;
      });
      liveScrapedAt = raw.scrapedAt || null;
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
    annotateVinDuplicates(liveInventory);
    liveLoaded = true;
    updateCoverageCounts();
    populateLiveMakeFilter();
    renderLive();
    checkAndNotify();
    updateAlertsBadge();
  } catch (e) {
    liveLoaded = false;
    document.getElementById('live-stats-bar').innerHTML = '';
    document.getElementById('live-grid').innerHTML = `
      <div class="empty-state" style="grid-column: 1/-1;">
        <h3>No Live Inventory Yet</h3>
        <p>The live inventory file wasn't found. Run the scraper to generate it:</p>
        <code>python scraper/junkyard_scraper.py --save --all</code>
        <p style="margin-top:1rem;">This scans the supported junkyard chains and cross-references every vehicle against the parts database. The output file <strong>inventory_live.json</strong> will appear in this directory.</p>
        <p style="margin-top:0.75rem;"><strong>Tip:</strong> Open this page via a local server (not <code>file://</code>), or the browser cannot load the JSON. <strong>cd into the folder that contains</strong> <code>index.html</code> (the <code>junkyard-hunter</code> project folder), then run <code>cd docs && python3 -m http.server 8765</code> and open <code>http://localhost:8765/index.html</code>. If you see 404, the server was started in the wrong directory.</p>
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
  sel.value = fit != null ? String(fit) : '';
  renderLive();
}
function jhShowNationwide() {
  document.getElementById('live-radius').value = '';
  renderLive();
}

function populateLiveMakeFilter() {
  const makes = [...new Set(liveInventory.map(v => v.make))].sort();
  const sel = document.getElementById('live-filter-make');
  sel.innerHTML = '<option value="">All Makes</option>';
  makes.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m;
    opt.textContent = m + ' (' + liveInventory.filter(v => v.make === m).length + ')';
    sel.appendChild(opt);
  });
  const locations = [...new Set(liveInventory.map(v => v.location).filter(Boolean))].sort();
  const locSel = document.getElementById('live-filter-location');
  locSel.innerHTML = '<option value="">All Yards</option>';
  locations.forEach(l => {
    const opt = document.createElement('option');
    opt.value = l;
    opt.textContent = l + ' (' + liveInventory.filter(v => v.location === l).length + ')';
    locSel.appendChild(opt);
  });
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
  btns.forEach(b => { b.disabled = true; b.dataset.orig = b.innerHTML; b.innerHTML = '&#x23F3;'; });
  navigator.geolocation.getCurrentPosition(
    pos => {
      activeZipCoords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
      localStorage.setItem('jh_gps', JSON.stringify(activeZipCoords));
      localStorage.removeItem('jh_zip');
      const zipEl = document.getElementById('live-zip');
      zipEl.value = '';
      zipEl.placeholder = '\u{1F4CD} Using your location';
      btns.forEach(b => { b.disabled = false; b.innerHTML = b.dataset.orig; });
      updateZipBanner();
      renderLive();
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
    list.innerHTML = '<div class="saved-empty">Tap the &#x2764;&#xFE0F; on any car to build your pull list.</div>';
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
              ${range && range.hi > 0 ? `<div class="saved-item-profit" title="${range.unknownCost ? 'Resale estimate — pull cost not on this yard\u2019s published price list, check at the yard' : 'Estimated range if parts are good, after this yard\u2019s list pull costs'}">${formatPrice(range.lo)}&ndash;${formatPrice(range.hi)}${range.unknownCost ? '<small style="display:block;font-weight:400;opacity:0.7;">resale</small>' : ''}</div>` : ''}
              <button type="button" class="saved-remove" data-vkey="${key}" title="Remove">&#x1F5D1;&#xFE0F;</button>
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
  const btn = e.target.closest('.heart-btn');
  if (!btn) return;
  e.preventDefault();
  toggleSaved(btn.dataset.vkey);
  btn.classList.toggle('saved', !!savedCars[btn.dataset.vkey]);
});
updateSavedPill();

/* First-run banner: ask for a zip once, in plain language. */
function updateZipBanner() {
  const show = !localStorage.getItem('jh_zip') && !localStorage.getItem('jh_gps')
    && localStorage.getItem('jh_zip_skipped') !== '1';
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
  localStorage.setItem('jh_zip_skipped', '1');
  updateZipBanner();
});

function getFilteredLive() {
  const search = document.getElementById('live-search').value.toLowerCase();
  const makeFilter = document.getElementById('live-filter-make').value;
  const matchFilter = document.getElementById('live-filter-match').value;
  const locationFilter = document.getElementById('live-filter-location').value;
  const sortBy = document.getElementById('live-sort').value;
  const radiusMi = parseFloat(document.getElementById('live-radius').value) || null;

  let filtered = liveInventory.filter(v => {
    if (makeFilter && v.make !== makeFilter) return false;
    if (locationFilter && v.location !== locationFilter) return false;
    if (activeZipCoords && radiusMi) {
      const d = vehicleDistanceMi(v);
      if (d == null || d > radiusMi) return false;
    }
    if (matchFilter === 'match' && !v.hasMatch) return false;
    if (matchFilter === 'nomatch' && v.hasMatch) return false;
    if (search) {
      const hay = [v.year, v.make, v.model, v.location, v.city, v.displayName, v.vin,
        v.vpicDecodeWell, v.vpicTrim, v.vpicSeries, v.vpicDriveType,
        ...(v.topParts || []).map(p => p.name)].join(' ').toLowerCase();
      return hay.includes(search);
    }
    return true;
  });

  function totalHaul(v) {
    if (!v.topParts || !v.topParts.length) return 0;
    return v.topParts.reduce((sum, p) => sum + p.high, 0);
  }
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

  filtered.sort((a, b) => {
    switch (sortBy) {
      case 'smart-profit': {
        const diff = smartProfit(b) - smartProfit(a);
        if (diff !== 0) return diff;
        return new Date(b.dateAdded) - new Date(a.dateAdded);
      }
      case 'gold-first': {
        const matchDiff = (b.hasMatch ? 1 : 0) - (a.hasMatch ? 1 : 0);
        if (matchDiff !== 0) return matchDiff;
        const valDiff = (b.maxValue || 0) - (a.maxValue || 0);
        if (valDiff !== 0) return valDiff;
        return new Date(b.dateAdded) - new Date(a.dateAdded);
      }
      case 'fastest-sell': {
        const speedRk = s => s === 'Fast' ? 3 : s === 'Medium' ? 2 : s === 'Slow' ? 1 : 0;
        const bestSpeed = v => v.topParts && v.topParts.length ? Math.max(...v.topParts.map(p => speedRk(p.sell_speed))) : 0;
        const sd = bestSpeed(b) - bestSpeed(a);
        return sd !== 0 ? sd : totalProfit(b) - totalProfit(a);
      }
      case 'profit-desc': return totalProfit(b) - totalProfit(a);
      case 'value-desc': return (b.maxValue || 0) - (a.maxValue || 0);
      case 'haul-desc': return totalHaul(b) - totalHaul(a);
      case 'date-desc': return new Date(b.dateAdded) - new Date(a.dateAdded);
      case 'date-asc': return new Date(a.dateAdded) - new Date(b.dateAdded);
      case 'year-desc': return (b.year || 0) - (a.year || 0);
      case 'year-asc': return (a.year || 0) - (b.year || 0);
      case 'make-asc': {
        const mk = (a.make || '').localeCompare(b.make || '');
        if (mk !== 0) return mk;
        return (a.model || '').localeCompare(b.model || '');
      }
      default: return 0;
    }
  });
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
  if (!liveLoaded) return;
  const vehicles = getFilteredLive();

  // KPIs describe what the user is LOOKING AT (their zip/filters), not the
  // whole national database — that's what a parts hunter actually cares about.
  const nearLabel = activeZipCoords && document.getElementById('live-radius').value ? 'Cars Near You' : 'Cars';
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
    <div class="stat-card"><div class="label">Worth Pulling</div><div class="value accent">${worthPulling.toLocaleString()}</div></div>
    <div class="stat-card"><div class="label">Fast Sellers</div><div class="value green">${fastSellers.toLocaleString()}</div></div>
    <div class="stat-card"><div class="label">New This Week</div><div class="value">${newThisWeek.toLocaleString()}</div></div>
    <div class="stat-card"><div class="label">Updated</div><div class="value" style="font-size:0.85rem;line-height:1.5;">${scrapedLabel}</div></div>
  `;

  if (!vehicles.length) {
    // If the radius filter is what emptied the grid, say so helpfully: name the
    // closest yard and how far it is instead of showing a blank wall.
    const radiusMi = parseFloat(document.getElementById('live-radius').value) || null;
    let msg = '<h3>No matches</h3><p>Try adjusting your filters.</p>';
    if (activeZipCoords && radiusMi) {
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
            <button type="button" class="btn" onclick="jhShowNationwide()">Show everything nationwide</button>
          </div>
          <p style="margin-top:1rem;font-size:0.72rem;">We track every major self-service chain — LKQ Pick Your Part, Pick-n-Pull, and Pull-A-Part — <span class="coverage-count">${coverageYardCount()}</span> yards nationwide. Independent local yards aren't covered yet.</p>`;
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

  document.getElementById('live-grid').innerHTML = vehiclesToRender.map(v => {
    const isMatch = v.hasMatch;
    const isNewVehicle = isNew(v.dateAdded);
    const dateStr = new Date(v.dateAdded).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    const cardClass = isMatch ? 'match-card' : 'dim-card';
    const fm = freshnessMultiplier(v.dateAdded);
    const fl = freshnessLabel(v.dateAdded);

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
        totalCost += yardCost;
        lowSum += p.low - yardCost;
        highSum += p.high - yardCost;
        if (pHigh > bestHigh) { bestHigh = pHigh; bestPart = p.name; }
        demandRk = Math.max(demandRk, speedRk(p.sell_speed));
        const sellSpd = p.sell_speed || '';
        const sellCls = sellSpd === 'Fast' ? 'sell-fast' : sellSpd === 'Slow' ? 'sell-slow' : 'sell-medium';
        const costHtml = hasCost
          ? `<span class="part-cost" title="${chainTitle[lookup.source]}: ${lookup.yardName || ''}">${formatPrice(yardCost)} <small style="opacity:0.65">${chainLabel[lookup.source]}</small></span>`
          : `<span class="part-cost" title="This part isn\u2019t on the yard\u2019s published price list — ask at the counter" style="opacity:0.75;"><small>check yard price list</small></span>`;
        const localNote = /\bFB\b|Facebook/i.test(p.sell_at || '')
          ? ' <span class="sell-tip" title="Facebook Marketplace is a local market — prices vary by area">FB prices vary by area</span>' : '';
        return `
          <li class="part-item" style="flex-wrap:wrap;">
            <span class="part-name">${p.name}</span>
            <span class="part-rarity ${rarityClass(p.rarity)}">${p.rarity}</span>
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
      profitLine = rangeHigh > 0 ? `
        <div class="profit-line">
          <span class="demand-badge ${demand.cls}">${demand.label}</span>
          <span class="range-text">${rangeText}</span>
        </div>` : '';
      partsBlock = `
        <details class="parts-details">
          <summary>${v.topParts.length} part${v.topParts.length > 1 ? 's' : ''} flagged &middot; top: ${bestPart} <span class="chev">&#x25BC;</span></summary>
          <div class="car-body"><ul class="parts-list">${partRows}</ul></div>
        </details>`;
    }

    return `
      <div class="car-card ${cardClass}" style="${cardStyle}">
        <div class="car-header">
          <div style="min-width:0;">
            <div class="car-name">${v.year} ${v.make} ${v.model}</div>
            <div class="live-card-location">&#x1F4CD; ${v.location}${(() => { const d = vehicleDistanceMi(v); return d != null ? ' <span style="color:var(--blue);font-weight:700;">&middot; ' + Math.round(d) + ' mi</span>' : ''; })()}${v.row ? '<span class="live-card-row">Row ' + v.row + '</span>' : ''}</div>
            <div class="car-meta">Added ${dateStr}${vinMetaHtml(v)}</div>
          </div>
          <div class="car-badges">
            <button type="button" class="heart-btn ${isSaved(v) ? 'saved' : ''}" data-vkey="${vehicleKey(v)}" title="Save for your yard visit">&#x2764;&#xFE0F;</button>
            ${isNewVehicle ? '<span class="badge badge-new">NEW</span>' : ''}
            ${isMatch
              ? '<span class="badge" style="background:' + (fm >= 0.75 ? 'var(--green-soft)' : fm >= 0.5 ? 'var(--gold-soft)' : 'var(--red-soft)') + ';color:' + fl.color + ';">' + fl.text + '</span>'
              : '<span class="badge" style="background:var(--surface3);color:var(--text-dim);">No parts</span>'}
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
document.getElementById('live-sort').addEventListener('change', renderLive);
document.getElementById('live-filter-match').addEventListener('change', renderLive);
document.getElementById('live-zip').addEventListener('input', e => setZipCenter(e.target.value.trim()));
document.getElementById('live-radius').addEventListener('change', () => {
  localStorage.setItem('jh_radius', document.getElementById('live-radius').value);
  renderLive();
});
// Restore saved zip/radius/GPS center across visits
(() => {
  const savedZip = localStorage.getItem('jh_zip') || '';
  const savedRadius = localStorage.getItem('jh_radius');
  if (savedRadius !== null) document.getElementById('live-radius').value = savedRadius;
  if (savedZip) {
    document.getElementById('live-zip').value = savedZip;
    setZipCenter(savedZip);
  } else {
    const gps = localStorage.getItem('jh_gps');
    if (gps) {
      try {
        activeZipCoords = JSON.parse(gps);
        document.getElementById('live-zip').placeholder = '\u{1F4CD} Using your location';
      } catch (e) { localStorage.removeItem('jh_gps'); }
    }
  }
})();
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
    const t = btn.textContent;
    btn.textContent = 'Copied';
    setTimeout(() => { btn.textContent = t || 'Copy'; }, 1200);
  }).catch(() => {});
});

/* ===== PARTS DATABASE ===== */
function renderStats(cars) {
  const allParts = cars.flatMap(c => c.parts);
  document.getElementById('stats-bar').innerHTML = `
    <div class="stat-card"><div class="label">Vehicles</div><div class="value blue">${cars.length}</div></div>
    <div class="stat-card"><div class="label">Parts Tracked</div><div class="value purple">${allParts.length}</div></div>
    <div class="stat-card"><div class="label">Legendary Parts</div><div class="value gold">${allParts.filter(p => p.rarity === 'Legendary').length}</div></div>
    <div class="stat-card"><div class="label">Best Single Part</div><div class="value green">${formatPrice(Math.max(...allParts.map(p => p.priceRange[1])))}</div></div>
    <div class="stat-card"><div class="label">Toyota Vehicles</div><div class="value orange">${cars.filter(c => c.make === 'Toyota').length}</div></div>
  `;
}

function renderCarGrid(cars) {
  const grid = document.getElementById('car-grid');
  if (!cars.length) {
    grid.innerHTML = '<div class="empty-state"><h3>No matches found</h3><p>Try adjusting your search or filters.</p></div>';
    return;
  }
  grid.innerHTML = cars.map(car => `
    <div class="car-card">
      <div class="car-header">
        <div>
          <div class="car-name">${car.name}</div>
          <div class="car-years">${car.years}</div>
          <div class="car-make">${car.make}</div>
        </div>
        <div class="car-badges">
          <span class="badge ${categoryClass(car.category)}">${car.category}</span>
          <span class="freq-badge freq-${car.frequency.toLowerCase()}">${car.frequency}</span>
        </div>
      </div>
      <div class="car-body">
        <div class="car-notes">${car.notes}</div>
        <ul class="parts-list">
          ${car.parts.map(p => `
            <li class="part-item">
              <span class="part-name">${p.name}</span>
              <span class="part-rarity ${rarityClass(p.rarity)}">${p.rarity}</span>
              <span class="part-cost" title="Typical self-service yard price — actual price comes from your yard's own price list">~${formatPrice(p.yardCost)} typical pull</span>
              <span class="part-price">${formatPrice(p.priceRange[0])}–${formatPrice(p.priceRange[1])}</span>
            </li>
          `).join('')}
        </ul>
      </div>
    </div>
  `).join('');
}

function populateMakeFilter() {
  const makes = [...new Set(DATABASE.map(c => c.make))].sort();
  const sel = document.getElementById('filter-make');
  makes.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m;
    opt.textContent = m + ' (' + DATABASE.filter(c => c.make === m).length + ')';
    sel.appendChild(opt);
  });
}

function getFilteredCars() {
  const search = document.getElementById('search').value.toLowerCase();
  const makeFilter = document.getElementById('filter-make').value;
  const catFilter = document.getElementById('filter-category').value;
  const rarityFilter = document.getElementById('filter-rarity').value;
  const sortBy = document.getElementById('sort-by').value;

  let filtered = DATABASE.filter(car => {
    if (makeFilter && car.make !== makeFilter) return false;
    if (catFilter && car.category !== catFilter) return false;
    if (rarityFilter && !car.parts.some(p => p.rarity === rarityFilter)) return false;
    if (search) {
      const hay = (car.name + ' ' + car.make + ' ' + car.years + ' ' + car.category + ' ' + car.notes + ' ' + car.parts.map(p => p.name + ' ' + p.sellOn).join(' ')).toLowerCase();
      return hay.includes(search);
    }
    return true;
  });

  if (rarityFilter) {
    filtered = filtered.map(car => ({ ...car, parts: car.parts.filter(p => p.rarity === rarityFilter) }));
  }

  filtered.sort((a, b) => {
    switch (sortBy) {
      case 'value-desc': return totalPotentialValue(b) - totalPotentialValue(a);
      case 'best-part-desc': return maxPartValue(b) - maxPartValue(a);
      case 'value-asc': return totalPotentialValue(a) - totalPotentialValue(b);
      case 'name-asc': return a.name.localeCompare(b.name);
      case 'rarity': {
        const rd = Math.max(...b.parts.map(p => rarityRank(p.rarity))) - Math.max(...a.parts.map(p => rarityRank(p.rarity)));
        if (rd !== 0) return rd;
        return totalPotentialValue(b) - totalPotentialValue(a);
      }
      case 'roi-desc': return avgROI(b) - avgROI(a);
      case 'parts-count': {
        const cd = b.parts.length - a.parts.length;
        if (cd !== 0) return cd;
        return totalPotentialValue(b) - totalPotentialValue(a);
      }
      default: return 0;
    }
  });
  return filtered;
}

function updateDatabase() {
  const cars = getFilteredCars();
  renderStats(cars);
  renderCarGrid(cars);
}

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
    if (tab.dataset.tab === 'database') updateDatabase();
    if (tab.dataset.tab === 'live') renderLive();
    if (tab.dataset.tab === 'alerts') renderAlerts();
  });
});

document.getElementById('search').addEventListener('input', updateDatabase);
document.getElementById('filter-make').addEventListener('change', updateDatabase);
document.getElementById('filter-category').addEventListener('change', updateDatabase);
document.getElementById('filter-rarity').addEventListener('change', updateDatabase);
document.getElementById('sort-by').addEventListener('change', updateDatabase);

/* ===== ALERTS / WATCHLIST ===== */
const WATCHLIST_KEY = 'junkyard_hunter_watchlist';
const ALERTED_KEY = 'junkyard_hunter_alerted';

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
    <div class="stat-card"><div class="label">Watchlist Items</div><div class="value blue">${watchlist.length}</div></div>
    <div class="stat-card"><div class="label">Vehicles Found</div><div class="value ${uniqueHits.size > 0 ? 'green' : 'orange'}">${uniqueHits.size}</div></div>
    <div class="stat-card"><div class="label">Total Hits</div><div class="value gold">${totalHits}</div></div>
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
      <div class="car-card match-card" style="--tier-color:var(--blue);">
        <div class="car-header">
          <div style="min-width:0;">
            <div class="car-name">${v.year} ${v.make} ${v.model}</div>
            <div class="live-card-location">&#x1F4CD; ${v.location}${(() => { const d = vehicleDistanceMi(v); return d != null ? ' <span style="color:var(--blue);font-weight:700;">&middot; ' + Math.round(d) + ' mi</span>' : ''; })()}${v.row ? '<span class="live-card-row">Row ' + v.row + '</span>' : ''}</div>
            <div class="car-meta">Added ${dateStr}${vinMetaHtml(v)}</div>
          </div>
          <div class="car-badges">
            <span class="badge" style="background:var(--blue-soft);color:var(--blue);">&#x1F514; ${matchedRules.join(', ')}</span>
            ${isMatch ? '<span class="badge" style="background:var(--gold-soft);color:var(--gold);">&#x2B50; Has parts</span>' : ''}
          </div>
        </div>
        ${isMatch && v.topParts && v.topParts.length ? `
          <details class="parts-details">
            <summary>&#x1F9F0; ${v.topParts.length} part${v.topParts.length > 1 ? 's' : ''} <span class="chev">&#x25BC;</span></summary>
            <div class="car-body">
              <ul class="parts-list">
                ${v.topParts.slice(0, 5).map(p => `
                  <li class="part-item">
                    <span class="part-name">${p.name}</span>
                    <span class="part-rarity ${rarityClass(p.rarity)}">${p.rarity}</span>
                    <span class="part-price">${formatPrice(p.low)}&ndash;${formatPrice(p.high)}</span>
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

function exportWatchlistFile() {
  const watchlist = loadWatchlist();
  if (!watchlist.length) return alert('Watchlist is empty — add vehicles first.');
  const blob = new Blob([JSON.stringify(watchlist, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'watchlist.json';
  a.click();
  URL.revokeObjectURL(url);
}
function saveWatchlistFile() { /* auto-exports are handled by Export button */ }

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
        new Notification('Junkyard Hunter Alert', {
          body: `${v.year} ${v.make} ${v.model} at ${v.location}${v.vin && String(v.vin).replace(/[^A-Z0-9]/gi, '').length === 17 ? ' · VIN ' + String(v.vin).trim() : ''}${v.hasMatch ? ' — has unobtanium parts!' : ''}`,
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
        body: 'It works! Watchlist alerts will show up like this.',
        headers: { 'Title': 'Junkyard Hunter test', 'Tags': 'wrench' },
      });
      statusEl.textContent = r.ok
        ? 'Sent! Check your phone (make sure the ntfy app is subscribed to "' + t + '").'
        : 'ntfy.sh returned an error — try a different topic name.';
    } catch (e) {
      statusEl.textContent = "Couldn't reach ntfy.sh — check your connection.";
    }
  });
})();
document.getElementById('alert-export-btn').addEventListener('click', exportWatchlistFile);

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
populateMakeFilter();
loadLiveInventory();

// Offline + instant-launch cache. Needs a secure context (HTTPS or localhost) —
// silently skipped when served over plain LAN IP, active once on GitHub Pages.
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js').catch(() => {});
}
