/* Junkyard Hunter — application logic (loading, filtering, rendering, saved list, alerts). */
/* ===== YARD PRICING MAPS ===== */
let pnpPricing = {};
let tapPricing = {};
let utpapPricing = {};

/* utpap = exact "Part Description" from utpap.com/1064Carpricelist.php (Ogden pricelist iframe on ogden-prices page) */
const PART_KEYWORD_MAP = [
  { kw: 'hid headlight',       pnp: 'HEADLIGHT COMP',               tap: 'HEADLIGHT COMPOSITE', utpap: 'HEADLAMP W/ TURN SIG' },
  { kw: 'led headlight',       pnp: 'HEADLIGHT COMP',               tap: 'HEADLIGHT COMPOSITE', utpap: 'HEADLAMP W/ TURN SIG' },
  { kw: 'headlight',           pnp: 'HEADLIGHT COMP',               tap: 'HEADLIGHT COMPOSITE', utpap: 'HEADLAMP W/ TURN SIG' },
  { kw: 'headlamp',            pnp: 'HEADLIGHT COMP',               tap: 'HEADLIGHT COMPOSITE', utpap: 'HEADLAMP W/ TURN SIG' },
  { kw: 'recaro seat',         pnp: 'SEAT-BUCK(EA)W/TRK (PWR)',     tap: 'BUCKET SEAT POWER', utpap: 'BUCKET SEAT ELCTRIC' },
  { kw: 'stow-n-go 2nd',      pnp: 'SEAT-BUCK(EA)W/TRK (MAN)',     tap: 'BUCKET SEAT', utpap: 'BUCKET SEAT ELCTRIC' },
  { kw: 'stow-n-go 3rd',      pnp: 'SEAT-REAR (EA)',               tap: 'SEAT SECTION', utpap: 'BENCH SEAT ELECTRIC' },
  { kw: 'stow-n-go',          pnp: 'SEAT-BUCK(EA)W/TRK (MAN)',     tap: 'BUCKET SEAT', utpap: 'BUCKET SEAT ELCTRIC' },
  { kw: '3rd row seat',        pnp: 'SEAT-REAR (EA)',               tap: 'SEAT SECTION', utpap: 'BENCH SEAT ELECTRIC' },
  { kw: 'rear seat',           pnp: 'SEAT-REAR (EA)',               tap: 'SEAT SECTION', utpap: 'BENCH SEAT ELECTRIC' },
  { kw: 'bench seat',          pnp: 'SEAT-BENCH W/TRK',             tap: 'SEAT BENCH', utpap: 'BENCH SEAT ELECTRIC' },
  { kw: 'bucket seat',         pnp: 'SEAT-BUCK(EA)W/TRK (PWR)',     tap: 'BUCKET SEAT POWER', utpap: 'BUCKET SEAT ELCTRIC' },
  { kw: 'seat',                pnp: 'SEAT-BUCK(EA)W/TRK (PWR)',     tap: 'BUCKET SEAT POWER', utpap: 'BUCKET SEAT ELCTRIC' },
  { kw: 'intercooler',         pnp: 'INTERCOOLER',                  tap: 'TURBO INTERCOOLER', utpap: 'TURBO INNER COOLER' },
  { kw: 'heads-up display',    pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL' },
  { kw: 'touchscreen',         pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL' },
  { kw: 'infotainment',        pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL' },
  { kw: 'navigation',          pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'NAVIGATION UNIT', utpap: 'TOUCH SCREEN RDO DBL' },
  { kw: 'display',             pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL' },
  { kw: 'head unit',           pnp: 'RADIO',                        tap: 'RADIO', utpap: 'RADIO CD PLAYER' },
  { kw: 'radio',               pnp: 'RADIO',                        tap: 'RADIO', utpap: 'RADIO CD PLAYER' },
  { kw: 'front bumper',        pnp: 'BUMPER COMP',                  tap: 'BUMPR CVER W/RENFORC', utpap: 'BUMPER' },
  { kw: 'bumper cover',        pnp: 'BUMPER COVER (PLAST/RUBR)',    tap: 'BUMPER COVER', utpap: 'BUMPER' },
  { kw: 'bumper',              pnp: 'BUMPER COMP',                  tap: 'BUMPR CVER W/RENFORC', utpap: 'BUMPER' },
  { kw: 'steering wheel',      pnp: 'STEERING WHEEL',               tap: 'STEERNG WHL W/SWITCH', utpap: 'STEERING WHEEL' },
  { kw: 'spoiler',             pnp: 'SPOILERS - BOLT ON (EA)',      tap: 'SPOILER', utpap: 'SPOILER' },
  { kw: 'fog light',           pnp: 'FOG LAMPS EACH',               tap: 'HEADLIGHT COMP BULB', utpap: 'FOG LIGHT' },
  { kw: 'fog lamp',            pnp: 'FOG LAMPS EACH',               tap: 'HEADLIGHT COMP BULB', utpap: 'FOG LIGHT' },
  { kw: 'brake caliper',       pnp: 'BRAKE CALIPER',                tap: 'BRAKE CALIPER', utpap: 'BRAKE CALIPER 2-4 PI' },
  { kw: 'caliper',             pnp: 'BRAKE CALIPER',                tap: 'BRAKE CALIPER', utpap: 'BRAKE CALIPER 2-4 PI' },
  { kw: 'mirror',              pnp: 'MIRROR-DOOR OUTSIDE(ELEC)',    tap: 'POWER MIRROR - DOOR', utpap: 'DOOR POWER MIRROR' },
  { kw: 'amplifier',           pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER' },
  { kw: 'amp',                 pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER' },
  { kw: 'speaker',             pnp: 'SPEAKER EACH',                 tap: 'SPEAKER', utpap: 'RADIO SPEAKER' },
  { kw: 'panoramic sunroof',   pnp: 'SUN ROOF ASSY',               tap: 'SUNROOF ASSY+MOTOR', utpap: 'SUNROOF/T-TOP' },
  { kw: 'sunroof',             pnp: 'SUN ROOF ASSY',               tap: 'SUN ROOF ASSEMBLY', utpap: 'SUNROOF/T-TOP' },
  { kw: 'sliding door motor',  pnp: 'DOOR/GATE MOTOR',             tap: 'SIDE DOOR SLIDE MTR', utpap: 'ELECTRIC MODULE' },
  { kw: 'door motor',          pnp: 'DOOR/GATE MOTOR',             tap: 'SIDE DOOR SLIDE MTR', utpap: 'ELECTRIC MODULE' },
  { kw: 'liftgate',            pnp: 'DOOR/GATE MOTOR',             tap: 'SIDE DOOR SLIDE MTR', utpap: 'TAIL GATE/ ENDGATE' },
  { kw: 'sliding door control', pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'COMPUTER' },
  { kw: 'control module',      pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'COMPUTER' },
  { kw: 'radar',               pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'COMPUTER' },
  { kw: 'camera',              pnp: 'CONTROL MODULE',              tap: 'REVERSE CAMERA', utpap: 'COMPUTER' },
  { kw: 'module',              pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'COMPUTER' },
  { kw: 'roof rack',           pnp: 'LUGGAGE/SKI RACK',            tap: 'LUGGAGE RACK', utpap: 'LUGGAGE RACK' },
  { kw: 'crossbar',            pnp: 'LUGGAGE/SKI RACK',            tap: 'CARGO RACK', utpap: 'LUGGAGE RACK' },
  { kw: 'grille',              pnp: 'GRILLE',                      tap: 'GRILLE', utpap: 'GRILLE LRG' },
  { kw: 'running board',       pnp: 'RUNNING BOARDS (EACH)',       tap: 'RUNNING BOARD (EACH)', utpap: 'RUNNING BOARD' },
  { kw: 'fender flare',        pnp: 'FENDER FLARE (EA)',           tap: 'FENDER TRIM/FLARES', utpap: 'FENDER EXTENSION' },
  { kw: 'window regulator',    pnp: 'WINDOW REG W/MOTOR ELEC',    tap: 'WINDOW REG W/MOTOR', utpap: 'WINDOW REGULATOR' },
  { kw: 'tail light',          pnp: 'TAILLIGHT',                   tap: 'TAIL LIGHT ASSY ANY', utpap: 'TAIL LIGHT ASSY LRG' },
  { kw: 'taillight',           pnp: 'TAILLIGHT',                   tap: 'TAIL LIGHT ASSY ANY', utpap: 'TAIL LIGHT ASSY LRG' },
  { kw: 'wireless charging',   pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'ELECTRIC MODULE' },
  { kw: 'charging pad',        pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'ELECTRIC MODULE' },
  { kw: 'entertainment',       pnp: 'LRG MULTIFUNCT DISPLAY',      tap: 'DVD PLAYER', utpap: 'RADIO CD PLAYER' },
  { kw: 'dvd',                 pnp: 'LRG MULTIFUNCT DISPLAY',      tap: 'DVD PLAYER', utpap: 'RADIO CD PLAYER' },
  { kw: 'cable',               pnp: 'CABLE/PUSH-PULL',             tap: 'CABLE (ANY)', utpap: 'SHIFTER CABLE' },
  { kw: 'track',               pnp: 'SEAT TRACK ELEC W/MOTOR (EA)', tap: 'SEAT TRACKSET+MOTOR', utpap: 'SEAT TRACK ELECTRIC' },
  { kw: 'dash pad',            pnp: 'DASH PAD',                    tap: 'DASH PAD', utpap: 'DASH PAD' },
  { kw: 'console lid',         pnp: 'CONSOLE LID',                 tap: 'CONSOLE LID', utpap: 'CONSOLE LID' },
  { kw: 'console',             pnp: 'CONSOLE',                     tap: 'CONSOLE (ANY)', utpap: 'CONSOLE BARE' },
  { kw: 'mudflap',             pnp: 'MUDFLAP',                     tap: 'MUDFLAP', utpap: 'MUD FLAP' },
  { kw: 'emblem',              pnp: 'EMBLEM',                      tap: 'EMBLEM (ANY)', utpap: 'EMBLEM' },
  { kw: 'wiper motor',         pnp: 'WIPER MOTOR',                 tap: 'WIPER MOTOR', utpap: 'WIPER MOTOR' },
  { kw: 'actuator',            pnp: 'ACTUATOR',                    tap: 'ACTUATOR', utpap: 'DOOR LOCK ACTUATOR' },
  { kw: 'transfer case motor', pnp: 'TRANSFER CASE MOTOR',         tap: 'TRANSFER CASE MOTOR', utpap: 'TRANSFERCAS ACTUATOR' },
];

function lookupYardCost(partName, location) {
  const lower = partName.toLowerCase();
  const loc = (location || '').toLowerCase();
  const isTap = loc.includes('tear');
  const isPnp = loc.includes('pick');
  const isUtpap = loc.includes('pic-a-part');
  let bestMatch = null;
  let bestLen = 0;
  for (const entry of PART_KEYWORD_MAP) {
    if (lower.includes(entry.kw) && entry.kw.length > bestLen) {
      bestMatch = entry;
      bestLen = entry.kw.length;
    }
  }
  if (!bestMatch) return { cost: null, source: 'none', yardName: null };

  if (isTap) {
    const tapEntry = tapPricing[bestMatch.tap];
    if (tapEntry) return { cost: parseFloat(tapEntry.price), source: 'tap', yardName: tapEntry.description };
  }
  if (isPnp) {
    const pnpEntry = pnpPricing[bestMatch.pnp];
    if (pnpEntry) return { cost: parseFloat(pnpEntry.price), source: 'pnp', yardName: pnpEntry.description };
  }
  if (isUtpap) {
    const u = utpapPricing[bestMatch.utpap];
    if (u) return { cost: parseFloat(u.price), source: 'utpap', yardName: u.description };
    return { cost: null, source: 'none', yardName: null };
  }
  const fallback = isTap ? tapPricing[bestMatch.tap] : pnpPricing[bestMatch.pnp];
  if (fallback) return { cost: parseFloat(fallback.price), source: isTap ? 'tap' : 'pnp', yardName: fallback.description };
  return { cost: null, source: 'none', yardName: null };
}

// Backward compat wrapper
function lookupPnpCost(partName) { return lookupYardCost(partName, 'Pick-n-Pull'); }

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
    populateLiveMakeFilter();
    populateProfitFilters();
    renderLive();
    renderProfitTab();
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
        <p style="margin-top:1rem;">This will check Utah junkyards for vehicles and cross-reference them against the parts database. The output file <strong>inventory_live.json</strong> will appear in this directory.</p>
        <p style="margin-top:0.75rem;"><strong>Tip:</strong> Open this page via a local server (not <code>file://</code>), or the browser cannot load the JSON. <strong>cd into the folder that contains</strong> <code>index.html</code> (the <code>junkyard-hunter</code> project folder), then run <code>cd docs && python3 -m http.server 8765</code> and open <code>http://localhost:8765/index.html</code>. If you see 404, the server was started in the wrong directory.</p>
      </div>`;
  }
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

function savedProfit(s) {
  if (!s.topParts || !s.topParts.length) return 0;
  const raw = s.topParts.reduce((sum, p) => {
    const lk = lookupYardCost(p.name, s.location);
    return sum + ((p.low + p.high) / 2 - (lk.cost != null ? lk.cost : p.cost));
  }, 0);
  // Same freshness discount the live cards apply, so the numbers agree.
  return Math.round(raw * freshnessMultiplier(s.dateAdded));
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
          const profit = savedProfit(s);
          const best = (s.topParts && s.topParts[0]) ? s.topParts[0].name : '';
          return `
            <div class="saved-item">
              <div class="saved-row-badge">${s.row || '?'}<small>row</small></div>
              <div class="saved-item-info">
                <div class="saved-item-name">${s.year} ${s.make} ${s.model}</div>
                <div class="saved-item-sub">${best ? best + (s.topParts.length > 1 ? ' +' + (s.topParts.length - 1) + ' more' : '') : 'No flagged parts'}</div>
              </div>
              ${profit > 0 ? `<div class="saved-item-profit">+${formatPrice(profit)}</div>` : ''}
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
      const yc = lookup.cost != null ? lookup.cost : p.cost;
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

function vehicleAdjProfit(v) {
  if (!v.hasMatch || !v.topParts || !v.topParts.length) return 0;
  return v.topParts.reduce((s, p) => {
    const lk = lookupYardCost(p.name, v.location);
    return s + ((p.low + p.high) / 2 - (lk.cost != null ? lk.cost : p.cost));
  }, 0) * freshnessMultiplier(v.dateAdded);
}

function renderLive() {
  if (!liveLoaded) return;
  const vehicles = getFilteredLive();

  // KPIs describe what the user is LOOKING AT (their zip/filters), not the
  // whole national database — that's what a parts hunter actually cares about.
  const nearLabel = activeZipCoords && document.getElementById('live-radius').value ? 'Cars Near You' : 'Cars';
  const worthPulling = vehicles.filter(v => v.hasMatch).length;
  const newThisWeek = vehicles.filter(v => isNew(v.dateAdded)).length;
  const bestFind = vehicles.length ? Math.max(0, ...vehicles.map(vehicleAdjProfit)) : 0;
  const scrapedLabel = liveScrapedAt
    ? new Date(liveScrapedAt).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
    : '—';

  updateLiveFilterCount();
  updateZipBanner();

  document.getElementById('live-stats-bar').innerHTML = `
    <div class="stat-card"><div class="label">${nearLabel}</div><div class="value blue">${vehicles.length.toLocaleString()}</div></div>
    <div class="stat-card"><div class="label">Worth Pulling</div><div class="value gold">${worthPulling.toLocaleString()}</div></div>
    <div class="stat-card"><div class="label">New This Week</div><div class="value green">${newThisWeek.toLocaleString()}</div></div>
    ${bestFind > 0 ? `<div class="stat-card"><div class="label">Best Find</div><div class="value green">+${formatPrice(Math.round(bestFind))}</div></div>` : ''}
    <div class="stat-card"><div class="label">Updated</div><div class="value orange" style="font-size:0.85rem;line-height:1.5;">${scrapedLabel}</div></div>
  `;

  if (!vehicles.length) {
    document.getElementById('live-grid').innerHTML = '<div class="empty-state" style="grid-column:1/-1;"><h3>No matches</h3><p>Try adjusting your filters.</p></div>';
    return;
  }

  function tierColor(profit, maxP) {
    if (profit <= 0) return 'var(--red)';
    const t = maxP > 0 ? Math.min(profit / maxP, 1) : 0;
    if (t > 0.7) return 'var(--accent2)';
    if (t > 0.4) return '#8ee6b8';
    if (t > 0.15) return 'var(--gold)';
    return 'var(--orange)';
  }

  const maxProfit = Math.max(1, ...vehicles.filter(v => v.hasMatch).map(v => {
    if (!v.topParts || !v.topParts.length) return 0;
    return v.topParts.reduce((s, p) => {
      const lk = lookupYardCost(p.name, v.location);
      return s + ((p.low + p.high) / 2 - (lk.cost != null ? lk.cost : p.cost));
    }, 0) * freshnessMultiplier(v.dateAdded);
  }));

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
      const haul = v.topParts.reduce((s, p) => s + p.high, 0);
      let totalCost = 0, totalProfit = 0, bestPart = null, bestProfit = -Infinity;
      const partRows = v.topParts.map(p => {
        const lookup = lookupYardCost(p.name, v.location);
        const yardCost = lookup.cost != null ? lookup.cost : p.cost;
        const costLabel = lookup.source === 'pnp' ? 'PnP' : lookup.source === 'tap' ? 'TAP' : lookup.source === 'utpap' ? 'UTPAP' : 'est';
        const costTitle = lookup.source === 'pnp' ? 'Real Pick-n-Pull price' : lookup.source === 'tap' ? 'Real Tear-A-Part price' : lookup.source === 'utpap' ? 'Utah Pic-A-Part list price' : 'Estimated';
        const avgResale = (p.low + p.high) / 2;
        const profit = Math.round(avgResale - yardCost);
        totalCost += yardCost;
        totalProfit += avgResale - yardCost;
        if (profit > bestProfit) { bestProfit = profit; bestPart = p.name; }
        const sellSpd = p.sell_speed || '';
        const sellCls = sellSpd === 'Fast' ? 'sell-fast' : sellSpd === 'Slow' ? 'sell-slow' : 'sell-medium';
        return `
          <li class="part-item" style="flex-wrap:wrap;">
            <span class="part-name">${p.name}</span>
            <span class="part-rarity ${rarityClass(p.rarity)}">${p.rarity}</span>
            <span class="part-cost" title="${costTitle}: ${lookup.yardName || 'N/A'}">${formatPrice(yardCost)} <small style="opacity:0.65">${costLabel}</small></span>
            <span class="part-price">${formatPrice(p.low)}&ndash;${formatPrice(p.high)}</span>
            <span class="part-profit" style="color:${profit > 100 ? 'var(--accent2)' : profit > 0 ? 'var(--orange)' : 'var(--red)'};font-weight:800;font-size:0.78rem;min-width:55px;text-align:right;">+${formatPrice(profit)}</span>
            ${p.sell_at ? `<div style="width:100%;display:flex;align-items:center;gap:0.4rem;margin-top:0.1rem;flex-wrap:wrap;">
              <span class="sell-badge ${sellCls}">${sellSpd}</span>
              <span class="sell-channel">Sell on: ${p.sell_at}</span>
              ${p.sell_notes ? '<span class="sell-tip">' + displaySellNotes(p.sell_notes, v.make) + '</span>' : ''}
            </div>` : ''}
          </li>`;
      }).join('');

      const adjProfit = Math.round(totalProfit * fm);
      cardStyle = `--tier-color:${tierColor(totalProfit * fm, maxProfit)};`;
      profitLine = `
        <div class="profit-line">
          <span class="live-card-value">+${formatPrice(adjProfit)}</span>
          <span class="profit-sub">est. profit &middot; ${formatPrice(haul)} resale &middot; ${formatPrice(Math.round(totalCost))} to pull</span>
        </div>`;
      partsBlock = `
        <details class="parts-details">
          <summary>&#x1F9F0; ${v.topParts.length} part${v.topParts.length > 1 ? 's' : ''} &middot; best: ${bestPart} +${formatPrice(bestProfit)} <span class="chev">&#x25BC;</span></summary>
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
        <div class="car-notes">${car.utahNotes}</div>
        <ul class="parts-list">
          ${car.parts.map(p => `
            <li class="part-item">
              <span class="part-name">${p.name}</span>
              <span class="part-rarity ${rarityClass(p.rarity)}">${p.rarity}</span>
              <span class="part-cost">${formatPrice(p.yardCost)} pull</span>
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
      const hay = (car.name + ' ' + car.make + ' ' + car.years + ' ' + car.category + ' ' + car.utahNotes + ' ' + car.parts.map(p => p.name + ' ' + p.sellOn).join(' ')).toLowerCase();
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

/* ===== VALUE GUIDE ===== */
function renderValueTable() {
  const search = document.getElementById('value-search').value.toLowerCase();
  const sortBy = document.getElementById('value-sort').value;
  let rows = [];
  DATABASE.forEach(car => {
    car.parts.forEach(p => {
      const avgResale = (p.priceRange[0] + p.priceRange[1]) / 2;
      const roi = avgResale / p.yardCost;
      rows.push({ carName: car.name, make: car.make, part: p, avgResale, roi, category: car.category });
    });
  });
  if (search) rows = rows.filter(r => (r.carName + ' ' + r.make + ' ' + r.part.name + ' ' + r.part.sellOn).toLowerCase().includes(search));
  rows.sort((a, b) => {
    switch (sortBy) {
      case 'high-desc': return b.part.priceRange[1] - a.part.priceRange[1];
      case 'roi-desc': return b.roi - a.roi;
      case 'profit-desc': return (b.avgResale - b.part.yardCost) - (a.avgResale - a.part.yardCost);
      case 'cost-asc': {
        const cd = a.part.yardCost - b.part.yardCost;
        if (cd !== 0) return cd;
        return b.roi - a.roi;
      }
      case 'rarity-desc': {
        const rd = rarityRank(b.part.rarity) - rarityRank(a.part.rarity);
        if (rd !== 0) return rd;
        return b.part.priceRange[1] - a.part.priceRange[1];
      }
      case 'name-asc': return a.part.name.localeCompare(b.part.name);
      case 'car-asc': return a.carName.localeCompare(b.carName);
      default: return 0;
    }
  });
  document.getElementById('value-tbody').innerHTML = rows.map(r => {
    const roiLabel = r.roi >= 10 ? 'HIGH' : r.roi >= 5 ? 'MED' : 'LOW';
    const roiCls = r.roi >= 10 ? 'roi-high' : r.roi >= 5 ? 'roi-medium' : 'roi-low';
    const profit = Math.round(r.avgResale - r.part.yardCost);
    return `<tr>
      <td>${r.carName}</td>
      <td>${r.part.name}</td>
      <td><span class="part-rarity ${rarityClass(r.part.rarity)}">${r.part.rarity}</span></td>
      <td>${formatPrice(r.part.yardCost)}</td>
      <td style="font-weight:700;color:var(--accent2);">${formatPrice(r.part.priceRange[0])}–${formatPrice(r.part.priceRange[1])}</td>
      <td style="font-weight:700;color:var(--accent);">${formatPrice(profit)}</td>
      <td><span class="roi-badge ${roiCls}">${Math.round(r.roi)}x ${roiLabel}</span></td>
      <td style="font-size:0.8rem;color:var(--text-dim);">${r.part.sellOn}</td>
    </tr>`;
  }).join('');
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

function populateProfitFilters() {
  if (!liveLoaded) return;
  const locations = [...new Set(liveInventory.map(v => v.location).filter(Boolean))].sort();
  const makes = [...new Set(liveInventory.filter(v => v.hasMatch).map(v => v.make))].sort();
  const locSel = document.getElementById('profit-filter-location');
  locSel.innerHTML = '<option value="">All Yards</option>' + locations.map(l => `<option value="${l}">${l}</option>`).join('');
  const makeSel = document.getElementById('profit-filter-make');
  makeSel.innerHTML = '<option value="">All Makes</option>' + makes.map(m => `<option value="${m}">${m}</option>`).join('');
}

function renderProfitTab() {
  if (!liveLoaded) {
    document.getElementById('profit-tbody').innerHTML = '<tr><td colspan="10" style="text-align:center;padding:2rem;color:var(--text-dim);">Load live inventory first (run scraper with --save --all)</td></tr>';
    return;
  }
  const search = document.getElementById('profit-search').value.toLowerCase();
  const filterLoc = document.getElementById('profit-filter-location').value;
  const filterMake = document.getElementById('profit-filter-make').value;
  const sortBy = document.getElementById('profit-sort').value;
  const matchOnly = document.getElementById('profit-match-only').checked;

  let vehicles = liveInventory.filter(v => {
    if (matchOnly && !v.hasMatch) return false;
    if (!v.topParts || !v.topParts.length) return false;
    if (filterLoc && v.location !== filterLoc) return false;
    if (filterMake && v.make !== filterMake) return false;
    if (search) {
      const blob = `${v.year} ${v.make} ${v.model} ${v.location} ${v.vin || ''} ${v.topParts.map(p=>p.name).join(' ')}`.toLowerCase();
      if (!blob.includes(search)) return false;
    }
    return true;
  });

  vehicles.forEach(v => {
    v._profitParts = v.topParts.map(p => {
      const lookup = lookupYardCost(p.name, v.location);
      const yardCost = lookup.cost != null ? lookup.cost : p.cost;
      const costSource = lookup.source === 'pnp' ? 'PnP' : lookup.source === 'tap' ? 'TAP' : lookup.source === 'utpap' ? 'UTPAP' : 'est';
      const avgResale = (p.low + p.high) / 2;
      const profit = avgResale - yardCost;
      const roi = yardCost > 0 ? avgResale / yardCost : 0;
      return { ...p, yardCost, costSource, avgResale, profit, roi, yardPartName: lookup.yardName };
    });
    v._totalProfit = v._profitParts.reduce((s, p) => s + p.profit, 0);
    v._totalCost = v._profitParts.reduce((s, p) => s + p.yardCost, 0);
    v._totalResale = v._profitParts.reduce((s, p) => s + p.avgResale, 0);
    v._bestPartProfit = Math.max(...v._profitParts.map(p => p.profit));
    v._avgRoi = v._totalCost > 0 ? v._totalResale / v._totalCost : 0;
    v._freshness = freshnessMultiplier(v.dateAdded);
    v._smartProfit = v._totalProfit * v._freshness;
  });

  vehicles.sort((a, b) => {
    switch (sortBy) {
      case 'smart-profit': return b._smartProfit - a._smartProfit;
      case 'profit-desc': return b._totalProfit - a._totalProfit;
      case 'best-part-profit': return b._bestPartProfit - a._bestPartProfit;
      case 'roi-desc': return b._avgRoi - a._avgRoi;
      case 'cheapest-pull': return a._totalCost - b._totalCost;
      case 'haul-desc': return b._totalResale - a._totalResale;
      case 'year-desc': return b.year - a.year;
      default: return 0;
    }
  });

  const grandProfit = vehicles.reduce((s, v) => s + v._totalProfit, 0);
  const grandCost = vehicles.reduce((s, v) => s + v._totalCost, 0);
  const avgProfit = vehicles.length ? grandProfit / vehicles.length : 0;
  const pnpCount = vehicles.filter(v => v.location && v.location.toLowerCase().includes('pick')).length;
  const tapCount = vehicles.filter(v => v.location && v.location.toLowerCase().includes('tear')).length;
  const utpapCount = vehicles.filter(v => v.location && v.location.toLowerCase().includes('pic-a-part')).length;

  const profitScraped = liveScrapedAt
    ? new Date(liveScrapedAt).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
    : '—';

  document.getElementById('profit-stats-bar').innerHTML = `
    <div class="stat-card"><div class="label">Vehicles w/ Parts</div><div class="value blue">${vehicles.length}</div></div>
    <div class="stat-card"><div class="label">Total Profit Potential</div><div class="value green">${formatPrice(Math.round(grandProfit))}</div></div>
    <div class="stat-card"><div class="label">Total Pull Cost</div><div class="value orange">${formatPrice(Math.round(grandCost))}</div></div>
    <div class="stat-card"><div class="label">Avg Profit / Vehicle</div><div class="value gold">${formatPrice(Math.round(avgProfit))}</div></div>
    <div class="stat-card"><div class="label">PnP / TAP / UTPAP</div><div class="value purple">${pnpCount} / ${tapCount} / ${utpapCount}</div></div>
    <div class="stat-card"><div class="label">Inventory scraped</div><div class="value" style="font-size:0.85rem;">${profitScraped}</div></div>
  `;

  let rows = [];
  vehicles.forEach(v => {
    v._profitParts.forEach(p => {
      rows.push({ v, p });
    });
  });

  const sellSpeedRank = s => s === 'Fast' ? 3 : s === 'Medium' ? 2 : s === 'Slow' ? 1 : 0;
  if (sortBy === 'fastest-sell') rows.sort((a, b) => {
    const diff = sellSpeedRank(b.p.sell_speed) - sellSpeedRank(a.p.sell_speed);
    return diff !== 0 ? diff : b.p.profit - a.p.profit;
  });
  else if (sortBy === 'best-part-profit') rows.sort((a, b) => b.p.profit - a.p.profit);
  else if (sortBy === 'roi-desc') rows.sort((a, b) => b.p.roi - a.p.roi);
  else if (sortBy === 'cheapest-pull') rows.sort((a, b) => a.p.yardCost - b.p.yardCost);

  const showing = rows.slice(0, 500);
  document.getElementById('profit-tbody').innerHTML = showing.map(({v, p}) => {
    const roiLabel = p.roi >= 10 ? 'HIGH' : p.roi >= 5 ? 'MED' : p.roi >= 3 ? 'OK' : 'LOW';
    const roiCls = p.roi >= 10 ? 'roi-high' : p.roi >= 5 ? 'roi-medium' : 'roi-low';
    const profitColor = p.profit > 150 ? 'var(--accent2)' : p.profit > 50 ? 'var(--accent)' : p.profit > 0 ? 'var(--text)' : 'var(--red)';
    const costBadge = p.costSource === 'PnP'
      ? '<span class="src-pnp" style="margin-left:4px;" title="Real Pick-n-Pull price">PnP</span>'
      : p.costSource === 'TAP'
      ? '<span class="src-tap" style="margin-left:4px;" title="Real Tear-A-Part price">TAP</span>'
      : p.costSource === 'UTPAP'
      ? '<span class="src-utpap" style="margin-left:4px;" title="Utah Pic-A-Part list price">UTPAP</span>'
      : '<span class="src-est" style="margin-left:4px;" title="Estimated">est</span>';
    const sellSpd = p.sell_speed || '';
    const sellCls = sellSpd === 'Fast' ? 'sell-fast' : sellSpd === 'Slow' ? 'sell-slow' : 'sell-medium';
    return `<tr>
      <td style="white-space:nowrap;">${v.year} ${v.make} ${v.model}${v.row ? '<br><small style="color:var(--text-dim)">Row '+v.row+'</small>' : ''}</td>
      <td style="font-size:0.78rem;">${v.location}</td>
      <td>${p.name}</td>
      <td><span class="part-rarity ${rarityClass(p.rarity)}">${p.rarity}</span></td>
      <td style="white-space:nowrap;">${formatPrice(p.yardCost)}${costBadge}</td>
      <td style="white-space:nowrap;font-weight:600;">${formatPrice(Math.round(p.avgResale))}</td>
      <td style="white-space:nowrap;font-weight:700;color:${profitColor};">+${formatPrice(Math.round(p.profit))}</td>
      <td><span class="roi-badge ${roiCls}">${Math.round(p.roi)}x ${roiLabel}</span></td>
      <td style="font-size:0.75rem;min-width:120px;">${p.sell_at ? `<span class="sell-badge ${sellCls}">${sellSpd}</span> ${p.sell_at}${p.sell_notes ? '<br><span class="sell-tip">' + displaySellNotes(p.sell_notes, v.make) + '</span>' : ''}` : '<span style="color:var(--text-dim);">—</span>'}</td>
      <td style="white-space:nowrap;font-size:0.78rem;"><span style="color:${v._freshness >= 0.75 ? 'var(--accent2)' : v._freshness >= 0.5 ? 'var(--orange)' : 'var(--red)'};font-weight:600;">${Math.round(v._freshness * 100)}%</span> <span style="color:var(--text-dim);">${Math.round(daysSinceAdded(v.dateAdded))}d</span></td>
    </tr>`;
  }).join('') + (rows.length > 500 ? `<tr><td colspan="10" style="text-align:center;padding:1rem;color:var(--text-dim);">Showing 500 of ${rows.length} rows — filter to narrow down</td></tr>` : '');
}

document.getElementById('profit-search').addEventListener('input', renderProfitTab);
document.getElementById('profit-filter-location').addEventListener('change', renderProfitTab);
document.getElementById('profit-filter-make').addEventListener('change', renderProfitTab);
document.getElementById('profit-sort').addEventListener('change', renderProfitTab);
document.getElementById('profit-match-only').addEventListener('change', renderProfitTab);

/* ===== TABS ===== */
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
    if (tab.dataset.tab === 'database') updateDatabase();
    if (tab.dataset.tab === 'value') renderValueTable();
    if (tab.dataset.tab === 'live') renderLive();
    if (tab.dataset.tab === 'profit') { populateProfitFilters(); renderProfitTab(); }
    if (tab.dataset.tab === 'alerts') renderAlerts();
  });
});

document.getElementById('search').addEventListener('input', updateDatabase);
document.getElementById('filter-make').addEventListener('change', updateDatabase);
document.getElementById('filter-category').addEventListener('change', updateDatabase);
document.getElementById('filter-rarity').addEventListener('change', updateDatabase);
document.getElementById('sort-by').addEventListener('change', updateDatabase);
document.getElementById('value-search').addEventListener('input', renderValueTable);
document.getElementById('value-sort').addEventListener('change', renderValueTable);

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
      btn.style.color = '#0b0d11';
    } else {
      btn.textContent = 'Notifications Blocked';
      btn.style.background = 'var(--red)';
      btn.style.color = '#0b0d11';
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
    btn.style.color = '#0b0d11';
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
