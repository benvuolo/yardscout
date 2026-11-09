/* Unit test: part-finder Phase 0 guards in docs/app.js (CURATION_SPEC §7.2
 * P0.1-P0.4). Loads the REAL pfRunSearch and its pure helpers out of
 * docs/app.js (top-level `function` blocks, which end at a column-0 "}"),
 * runs them in a vm context with DOM/app stubs and fixture data, and reads
 * the rendered #pf-results HTML.
 *   P0.1 platform-group tier fails closed (only "verified" is Verified)
 *   P0.2 header notes are escaped at render
 *   P0.3 platform-group rows carry the category rowWarn
 *   P0.4 pfDonorIdentity: vpicMismatch / VIN model-year char -> Likely;
 *        OEM rows also need a valid VIN
 *   §7.4 Phase 1 display: OEM catalog groups (oemGroups, oemVg) and the
 *        §12 lazy per-category files (oemGroups + aftermarket amGroups):
 *        nothing Verified unless the main file ships it Verified, labels
 *        name the source, old keys render exactly as before
 * Run: node backend/test/pf_guards_unit.mjs   (APP_JS=<path> to test another
 * copy of app.js, e.g. the previous commit's, to see the checks fail). */
import fs from 'node:fs';
import vm from 'node:vm';
import { execFileSync } from 'node:child_process';

const APP = process.env.APP_JS || new URL('../../docs/app.js', import.meta.url);
const src = fs.readFileSync(APP, 'utf8');

let failures = 0;
const check = (name, ok, detail = '') => {
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ' — ' + detail}`);
  if (!ok) failures++;
};

/* Top-level function source: from "function NAME(" at column 0 to the next
 * line that is exactly "}". app.js keeps that layout for every top-level
 * function; vm.Script below proves each extract parses. */
function extractFn(name) {
  const lines = src.split('\n');
  const start = lines.findIndex(l => l.startsWith(`function ${name}(`));
  if (start < 0) return null;
  const end = lines.findIndex((l, i) => i > start && l === '}');
  return end < 0 ? null : lines.slice(start, end + 1).join('\n');
}
function extractConst(name) {
  const line = src.split('\n').find(l => l.startsWith(`const ${name} = `));
  return line || null;
}

const REAL_FNS = ['escapeHtml', 'normalizeVinForDedupe', 'pfSquash', 'pfSquashModel',
  'pfAppMatches', 'pfGenWindows', 'pfGenWindow', 'pfParseEngine', 'pfEngineVerdict',
  'pfParseFits', 'pfPartRow', 'pfTierChip', 'pfEngineQuoteVariants', 'pfRunSearch',
  // Pull Sheet round 4: the donor card + sort the rows are rendered through
  // (real, so the markup parsed below is the markup users get).
  'pfSortRows', 'pfSortRowHtml', 'pfDonorName', 'pfDonorCardHtml', 'pfWatchHtml'];
const NEW_FNS = ['pfVinModelYear', 'pfVinValid', 'pfDonorIdentity'];
const NEW_CONSTS = ['PF_VIN_YEAR_CHARS', 'PF_VIN_TRANSLIT', 'PF_VIN_WEIGHTS'];
// Phase 1 (§7.4 / §12). Absent in an older app.js: stubbed so the P0 checks
// still run there; the Phase 1 checks then fail, as they should.
const P1_FNS = ['pfOemLazyLoad', 'pfOemSourceText', 'pfAmSourceText', 'pfAmParseEngine',
  'pfAmEngineAgrees', 'pfAmCarTrans', 'pfAmRows'];
const P1_CONSTS = ['PF_OEM_LIKELY_HEAD', 'PF_AM_HEAD'];

let code = '';
for (const fn of REAL_FNS) {
  const s = extractFn(fn);
  check(`app.js has top-level function ${fn}`, !!s);
  if (s) { new vm.Script(s); code += s + '\n'; }
}
for (const c of NEW_CONSTS) {
  const s = extractConst(c);
  check(`app.js has const ${c}`, !!s);
  if (s) code += s + '\n';
}
for (const fn of NEW_FNS) {
  const s = extractFn(fn);
  check(`app.js has top-level function ${fn}`, !!s);
  // Absent (an older app.js): stub permissively so the other checks still run.
  code += (s || `function ${fn}() { return ${fn === 'pfDonorIdentity' ? "{ ok: true, warn: '' }" : 'null'}; }`) + '\n';
}

for (const c of P1_CONSTS) {
  const s = extractConst(c);
  check(`app.js has const ${c}`, !!s);
  code += (s || `const ${c} = '';`) + '\n';
}
for (const fn of P1_FNS) {
  const s = extractFn(fn);
  check(`app.js has top-level function ${fn}`, !!s);
  if (s) new vm.Script(s);
  code += (s || `function ${fn}() { return ${fn === 'pfAmRows' ? 0 : 'null'}; }`) + '\n';
}

/* ---- stubs for everything else pfRunSearch touches ---------------------- */
const prelude = `
var __els = {};
var document = { getElementById(id) {
  if (!__els[id]) __els[id] = { id, innerHTML: '', textContent: '', value: '',
    classList: { toggle() {}, add() {}, remove() {} } };
  return __els[id]; } };
var __seeker = { year: 0, make: '', model: '' };
function pfSeeker() { return __seeker; }
var activeZipCoords = { lat: 40, lng: -111 };
var interchangeData = null, liveInventory = [], pfCat = null, pfChosenFam = null;
var _pfGenMap = null, pfVerifiedOnly = false, __extras = {};
var pfOemLazyData = {}, pfOemLazyWait = {}, DATA_BASE = '', __files = {}, __fetched = [];
function fetch(url) {
  __fetched.push(url);
  const f = __files[url];
  if (f === 'reject') return Promise.reject(new Error('offline'));
  return Promise.resolve(f ? { ok: true, json: () => Promise.resolve(JSON.parse(JSON.stringify(f))) }
                           : { ok: false, json: () => Promise.resolve(null) });
}
function loadInterchange() { return Promise.resolve(interchangeData); }
function ensurePricingFor() { return null; }
function getYardsView() { return { inRange: [] }; }
function pfRunBrowse() { __els['pf-results'] = document.getElementById('pf-results'); __els['pf-results'].innerHTML = 'BROWSE'; }
function track() {} function pfSearchSignal() {} function pfSaveState() {}
function effectiveRadiusMi() { return 0; }
function pfRenderEngineChips() {}
function pfAskHtml() { return ''; }
function vehicleDistanceMi(v) { return v._d ?? 10; }
function extrasFor(v) { return __extras[String(v.id)] || null; }
function canonicalMake(m) { return m; }
function canonicalModel(mk, md) { return md; }
function isPro() { return false; }
function pfVonlyRowHtml() { return ''; }
function yardPartQuote() { return { status: 'in-store' }; }
function onlinePriceHtml() { return ''; }
function formatPrice(n) { return '$' + n; }
function pfDateLabel() { return ''; }
function saleBadgeHtml() { return ''; }
var pfSort = 'near';
function yardDateMs() { return 0; }
function vehicleKey(v) { return v.vin || String(v.id); }
function photoInfo() { return null; }
function photoBoxHtml() { return ''; }
function rowPlateHtml() { return ''; }
function pullBtnHtml() { return ''; }
function pfRenderTiles() {}
function pfRevealResults() {}
var ICON = { bell: '' };
function freeDeliveryNote() { return ''; }
function proBoxHtml() { return ''; }
function cardPhotoHtml() { return ''; }
var PRO_PUSH_LINE = '';
`;
const ctx = vm.createContext({ console, Promise, Map, Set, Math, String, Number, JSON, Infinity });
vm.runInContext(prelude + code, ctx, { filename: 'app.js-extract' });

/* ---- fixtures ------------------------------------------------------------ */
// Real lot VINs with valid check digits (docs/data/inventory_live.json,
// 2026-11-04): position 10 'D' = 2013, 'C' = 2012, '8' = 2008, '7' = 2007.
const VIN_2013 = '19UUA8F74DA009061';
const VIN_2012 = '19UUA8F58CA002093';
const VIN_2008 = '5J8TB18508A019426';
const VIN_2007 = '19UUA76517A006678';

const cat = (over = {}) => ({ id: 'side-mirrors', label: 'Side mirror', kind: 'body',
  tokens: ['side mirror'], priceTokens: ['mirror'], rowWarn: 'match the <paint> code', ...over });
const car = (id, year, make, model, over = {}) => ({ id, vin: '', year, make, model,
  location: 'Yard', row: '1', dateAdded: '', topParts: [], _d: id, ...over });

function run(data, inventory, seeker, pcat, extras = {}) {
  ctx.interchangeData = data;
  ctx.liveInventory = inventory;
  ctx.__seeker = seeker;
  ctx.pfCat = pcat;
  ctx.pfChosenFam = null;
  ctx._pfGenMap = null;
  ctx.__extras = extras;
  ctx.__els = {};
  ctx.pfOemLazyData = lazyPreset ? { ...lazyPreset } : {};
  ctx.pfOemLazyWait = {};
  ctx.pfRunSearch();
  return parse(ctx);
}
let lazyPreset = null;   // {cat: {oemGroups, amGroups}} set before run() = file already loaded
function parse(c) {
  const html = c.__els['pf-results'] ? c.__els['pf-results'].innerHTML : '';
  const rows = {};
  for (const chunk of html.split('<div class="pf-row-card ').slice(1)) {
    const tier = chunk.startsWith('pf-verified') ? 'verified' : chunk.startsWith('pf-likely') ? 'likely' : '?';
    const name = (chunk.match(/<span class="pf-car-name">([^<]*)<\/span>/) || [])[1] || '';
    const warn = (chunk.match(/<div class="pf-warn">([\s\S]*?)<\/div>/) || [])[1] || '';
    const chip = (chunk.match(/<span class="pf-tier [^"]*" title="([^"]*)">([^<]*(?:&mdash;[^<]*)?)<\/span>/) || []);
    const src = (chunk.match(/<div class="pf-note pf-src">([\s\S]*?)<\/div>/) || [])[1] || '';
    rows[name] = { tier, warn, chip: chip[2] || '', tip: chip[1] || '', src };
  }
  const head = html.split('<div class="pf-row-card ')[0];
  return { html, head, rows, status: c.__els['pf-status'] ? c.__els['pf-status'].textContent : '' };
}

const base = (groups, extra = {}) => ({ categories: [], engineFamilies: [], platformGroups: groups,
  modelGenerations: [], ...extra });
const grp = (tier, over = {}) => ({ id: 'fam#0', label: 'Test platform', cat: 'side-mirrors',
  note: 'same mirror on both', apps: [['Toyota', 'Camry', 2007, 2011], ['Toyota', 'Avalon', 2007, 2011]],
  ...(tier === undefined ? {} : { tier }), ...over });
const SEEK = { year: 2009, make: 'Toyota', model: 'Camry' };
const inv1 = [car(1, 2010, 'Toyota', 'Avalon')];

/* ---- P0.1: tier fails closed -------------------------------------------- */
for (const [label, tier, want] of [['"verified"', 'verified', 'verified'], ['"likely"', 'likely', 'likely'],
  ['"bogus"', 'bogus', 'likely'], ['"verfied" (typo)', 'verfied', 'likely'], ['missing', undefined, 'likely'],
  ['"Verified" (case)', 'Verified', 'likely']]) {
  const r = run(base([grp(tier)]), inv1, SEEK, cat());
  check(`P0.1 platform group tier ${label} renders ${want}`,
    r.rows['2010 Toyota Avalon'] && r.rows['2010 Toyota Avalon'].tier === want, JSON.stringify(r.rows));
}

/* ---- P0.2: header notes escaped ------------------------------------------ */
{
  const r = run(base([grp('verified', { label: 'Plat <b>form</b>', note: 'note with <i>tags</i> & <img src=x onerror=alert(1)>' })]),
    inv1, SEEK, cat());
  check('P0.2 group note <i> renders as text in the header', r.head.includes('&lt;i&gt;tags&lt;/i&gt;') && !r.head.includes('<i>'), r.head);
  check('P0.2 group label <b> renders as text in the header', r.head.includes('Plat &lt;b&gt;form&lt;/b&gt;') && !r.head.includes('<b>'), r.head);
  check('P0.2 no live <img> anywhere in the output', !r.html.includes('<img'), r.html);
  check('P0.2 plain "&" is escaped once (renders as &)', r.head.includes('&amp; &lt;img') && !r.head.includes('&amp;amp;'), r.head);
}
{
  // Engine branch: the seeker's own ambig note goes to the header as "Your car: ...".
  const fam = { id: 'fam-x', label: 'Test 2.4 I4', liters: [2.4], cyl: 4,
    apps: [['Toyota', 'Camry', 2007, 2009, 0, 'Hybrids <script>x</script> also decode as 2.4L']],
    parts: { alternator: { note: 'unit note' } } };
  const ecat = { id: 'alternator', label: 'Alternator', kind: 'engine', tokens: ['alternator'], priceTokens: ['alternator'] };
  const r = run(base([], { engineFamilies: [fam] }), [car(1, 2008, 'Toyota', 'Camry')], { year: 2008, make: 'Toyota', model: 'Camry' }, ecat);
  check('P0.2 seeker ambig note ("Your car: …") is escaped', r.head.includes('Your car: Hybrids &lt;script&gt;') && !r.head.includes('<script>'), r.head);
}

/* ---- P0.3: rowWarn on platform-group rows -------------------------------- */
{
  const r = run(base([grp('verified')]), inv1, SEEK, cat());
  const row = r.rows['2010 Toyota Avalon'];
  check('P0.3 Verified platform row carries the category rowWarn (escaped)',
    row && row.tier === 'verified' && row.warn.includes('match the &lt;paint&gt; code') && row.warn.includes('same mirror on both'),
    JSON.stringify(row));
  const r2 = run(base([grp('likely')]), inv1, SEEK, cat());
  check('P0.3 Likely platform row carries the rowWarn too',
    r2.rows['2010 Toyota Avalon'] && r2.rows['2010 Toyota Avalon'].warn.includes('match the &lt;paint&gt; code'));
  const r3 = run(base([grp('verified')]), inv1, SEEK, cat({ rowWarn: undefined }));
  check('P0.3 no rowWarn on the category: row warns are just the group note',
    r3.rows['2010 Toyota Avalon'] && r3.rows['2010 Toyota Avalon'].warn === 'same mirror on both', JSON.stringify(r3.rows));
}

/* ---- P0.4 unit: pfVinModelYear / pfVinValid / pfDonorIdentity ------------ */
const vy = (vin, y) => ctx.pfVinModelYear(vin, y);
check('pfVinModelYear: D near 2013 = 2013', vy(VIN_2013, 2013) === 2013);
check('pfVinModelYear: A resolves toward the listed year (2009 -> 2010, 1985 -> 1980)',
  vy('1HGCG165XAA015811', 2009) === 2010 && vy('1HGCG165XAA015811', 1985) === 1980);
check('pfVinModelYear: Y = 2000, 1 = 2001, 9 = 2009', vy('1HGCG1651YA015811', 2001) === 2000
  && vy('1HGCG16511A015811', 2001) === 2001 && vy('1HGCG16519A015811', 2009) === 2009);
check('pfVinModelYear: equidistant cycle tie goes to the later year (A, 1995 -> 2010)', vy('1HGCG165XAA015811', 1995) === 2010);
check('pfVinModelYear: non-year char (Z, U, 0) and short VINs -> null',
  vy('1HGCG1651ZA015811', 2009) === null && vy('1HGCG1651UA015811', 2009) === null
  && vy('1HGCG16510A015811', 2009) === null && vy('1HGCG1651XA01581', 1999) === null && vy('', 2009) === null);
check('pfVinModelYear: lower case and dashes normalise', vy('19uua8f7-4da009061', 2013) === 2013);
check('pfVinValid: real lot VINs pass the check digit',
  [VIN_2013, VIN_2012, VIN_2008, VIN_2007].every(v => ctx.pfVinValid(v)));
check('pfVinValid: one changed character fails it', !ctx.pfVinValid('19UUA8F74DA009062') && !ctx.pfVinValid('19UUA8F84DA009061'));
check('pfVinValid: I/O/Q letters, short or empty VINs fail',
  !ctx.pfVinValid('19UUA8F74DA00906I') && !ctx.pfVinValid('19UUA8F74DA00906') && !ctx.pfVinValid(''));

const id = (v, o) => ctx.pfDonorIdentity(v, o);
check('pfDonorIdentity: VIN agrees with the year -> ok', id({ vin: VIN_2013, year: 2013 }).ok === true);
check('pfDonorIdentity: vpicMismatch -> not ok, with the spec warning',
  id({ vin: VIN_2013, year: 2013, vpicMismatch: 'VIN decodes as Honda (listed Acura)' }).ok === false
  && /listing doesn.t match the VIN/.test(id({ vin: VIN_2013, year: 2013, vpicMismatch: 'x' }).warn));
const yid = id({ vin: VIN_2013, year: 2012 });
check('pfDonorIdentity: VIN year char 2013 vs listed 2012 -> not ok, names both years',
  yid.ok === false && yid.warn.includes('2013') && yid.warn.includes('2012'), JSON.stringify(yid));
check('pfDonorIdentity: no VIN on a non-OEM row -> ok (nothing contradicts the listing)', id({ vin: '', year: 2012 }).ok === true);
check('pfDonorIdentity: OEM row with no VIN -> not ok, "no VIN to confirm the model year"',
  id({ vin: '', year: 2012 }, { oem: true }).ok === false
  && id({ vin: '', year: 2012 }, { oem: true }).warn === 'no VIN to confirm the model year');
check('pfDonorIdentity: OEM row with a check-digit-failing VIN -> not ok',
  id({ vin: '19UUA8F74DA009062', year: 2013 }, { oem: true }).ok === false);
check('pfDonorIdentity: OEM row with a valid matching VIN -> ok', id({ vin: VIN_2013, year: 2013 }, { oem: true }).ok === true);

/* ---- P0.4 in pfRunSearch: platform path ---------------------------------- */
{
  const inv = [
    car(1, 2012, 'Toyota', 'Avalon', { vin: VIN_2012 }),                 // agrees -> Verified
    car(2, 2011, 'Toyota', 'Avalon', { vin: VIN_2012 }),                 // VIN says 2012 -> Likely
    car(3, 2010, 'Toyota', 'Avalon', { vpicMismatch: 'VIN decodes as 2009 (listed 2010)' }), // -> Likely
    car(4, 2009, 'Toyota', 'Avalon'),                                    // no VIN -> Verified (non-OEM)
  ];
  const r = run(base([grp('verified', { apps: [['Toyota', 'Camry', 2007, 2012], ['Toyota', 'Avalon', 2007, 2012]] })]),
    inv, SEEK, cat());
  check('P0.4 platform: donor whose VIN agrees stays Verified', r.rows['2012 Toyota Avalon']?.tier === 'verified', JSON.stringify(r.rows));
  check('P0.4 platform: VIN year char disagrees -> Likely with the year warning',
    r.rows['2011 Toyota Avalon']?.tier === 'likely' && r.rows['2011 Toyota Avalon'].warn.includes('the yard lists 2011'),
    JSON.stringify(r.rows['2011 Toyota Avalon']));
  check('P0.4 platform: vpicMismatch donor -> Likely with the listing warning',
    r.rows['2010 Toyota Avalon']?.tier === 'likely' && r.rows['2010 Toyota Avalon'].warn.includes('listing doesn’t match the VIN'),
    JSON.stringify(r.rows['2010 Toyota Avalon']));
  check('P0.4 platform: donor with no VIN stays Verified (rule applies to OEM rows only)',
    r.rows['2009 Toyota Avalon']?.tier === 'verified');
  check('P0.4 platform: demoted rows keep the group note and rowWarn',
    r.rows['2011 Toyota Avalon']?.warn.includes('same mirror on both') && r.rows['2011 Toyota Avalon'].warn.includes('paint'));
}

/* ---- P0.4 in pfRunSearch: engine (vg) path and engine-assembly ------------ */
{
  const fam = { id: 'fam-e', label: 'Test 2.4 I4', liters: [2.4], cyl: 4,
    apps: [['Toyota', 'Camry', 2004, 2013, 0, '']],
    parts: { alternator: { note: 'unit note', vg: [[['Toyota', 'Camry', 2004, 2013]]] } } };
  const ecat = { id: 'alternator', label: 'Alternator', kind: 'engine', tokens: ['alternator'], priceTokens: ['alternator'] };
  const inv = [
    car(1, 2013, 'Toyota', 'Camry', { vin: VIN_2013 }),
    car(2, 2012, 'Toyota', 'Camry', { vin: VIN_2013 }),
    car(3, 2008, 'Toyota', 'Camry', { vin: VIN_2008, vpicMismatch: 'VIN decodes as Scion (listed Toyota)' }),
    car(4, 2007, 'Toyota', 'Camry', { vin: VIN_2007 }),
  ];
  const extras = { 1: ['', '', '2.4L 4-cyl'], 2: ['', '', '2.4L 4-cyl'], 3: ['', '', '2.4L 4-cyl'], 4: ['', '', '2.4L 4-cyl'] };
  const data = base([], { engineFamilies: [fam] });
  const r = run(data, inv, { year: 2010, make: 'Toyota', model: 'Camry' }, ecat, extras);
  check('P0.4 vg path: engine-confirmed donor with an agreeing VIN is Verified', r.rows['2013 Toyota Camry']?.tier === 'verified', JSON.stringify(r.rows));
  check('P0.4 vg path: VIN year char disagrees -> Likely', r.rows['2012 Toyota Camry']?.tier === 'likely'
    && r.rows['2012 Toyota Camry'].warn.includes('model-year code reads 2013'), JSON.stringify(r.rows['2012 Toyota Camry']));
  check('P0.4 vg path: vpicMismatch -> Likely', r.rows['2008 Toyota Camry']?.tier === 'likely', JSON.stringify(r.rows['2008 Toyota Camry']));
  check('P0.4 vg path: control donor stays Verified', r.rows['2007 Toyota Camry']?.tier === 'verified');
  const fa = { ...fam, parts: { 'engine-assembly': { note: 'same long block' } } };
  const acat = { id: 'engine-assembly', label: 'Engine', kind: 'engine', tokens: ['engine'], priceTokens: ['engine'], noValue: true };
  const r2 = run(base([], { engineFamilies: [fa] }), inv, { year: 2010, make: 'Toyota', model: 'Camry' }, acat, extras);
  check('P0.4 engine-assembly: VIN-confirmed donor with agreeing VIN is Verified', r2.rows['2013 Toyota Camry']?.tier === 'verified', JSON.stringify(r2.rows));
  check('P0.4 engine-assembly: VIN year char disagrees -> Likely', r2.rows['2012 Toyota Camry']?.tier === 'likely');
  check('P0.4 engine-assembly: vpicMismatch -> Likely', r2.rows['2008 Toyota Camry']?.tier === 'likely');
  // The P0.5 data effect, end to end: an ambig app caps donors at Likely.
  const famA = { ...fam, apps: [['Toyota', 'Camry', 2004, 2006, 0, ''], ['Toyota', 'Camry', 2007, 2013, 0, 'Camry Hybrids also decode as 2.4L']] };
  const r3 = run(base([], { engineFamilies: [famA] }), inv, { year: 2005, make: 'Toyota', model: 'Camry' }, ecat, extras);
  check('ambig app (P0.5 data) caps an otherwise Verified donor at Likely and shows the note',
    r3.rows['2013 Toyota Camry']?.tier === 'likely' && r3.rows['2013 Toyota Camry'].warn.includes('Camry Hybrids also decode'),
    JSON.stringify(r3.rows['2013 Toyota Camry']));
}

/* ---- Engine browse (pfRunBrowse) and the tier hint (pfVonlyRowHtml) ------
 * A second context loads the REAL pfRunBrowse and pfVonlyRowHtml (the one
 * above stubs both). Review 2026-11-05: browse gave hybrids on an ambig app
 * the green "VIN-confirmed" chip, and the engine-assembly fit search said
 * "Verified = published catalog fitment data" though no catalog lists engine
 * assemblies. */
const browseFns = ['pfRunBrowse', 'pfVonlyRowHtml'].map(fn => {
  const s = extractFn(fn);
  check(`app.js has top-level function ${fn}`, !!s);
  return s || '';
}).join('\n');
const prelude2 = prelude
  .replace(/^function pfRunBrowse\(\).*$/m, '')
  .replace(/^function pfVonlyRowHtml\(\).*$/m, '')
  + `function pfRenderBrowseFamPicker() {}
function partQueryHit() { return false; }
`;
const ctx2 = vm.createContext({ console, Promise, Map, Set, Math, String, Number, JSON, Infinity });
vm.runInContext(prelude2 + code + browseFns, ctx2, { filename: 'app.js-extract-browse' });

function browse(data, inventory, pcat, famId, extras = {}) {
  Object.assign(ctx2, { interchangeData: data, liveInventory: inventory, pfCat: pcat,
    pfChosenFam: famId, _pfGenMap: null, __extras: extras, __els: {}, pfVerifiedOnly: false });
  ctx2.pfRunBrowse({ year: 0, make: '', model: '' });
  const html = ctx2.__els['pf-results'] ? ctx2.__els['pf-results'].innerHTML : '';
  const rows = {}, list = [];
  for (const chunk of html.split('<div class="pf-row-card ').slice(1)) {
    const name = (chunk.match(/<span class="pf-car-name">([^<]*)<\/span>/) || [])[1] || '';
    const warn = (chunk.match(/<div class="pf-warn">([\s\S]*?)<\/div>/) || [])[1] || '';
    const row = { name, chip: chunk.includes('pf-tier-verified'), vinClass: chunk.startsWith('pf-browse pf-vin'), warn };
    rows[name] = row;
    list.push(row);
  }
  return { html, rows, list };
}
{
  // Real lot VINs: 2007 Camry Hybrids (VIN position 5 "B" = 2AZ-FXE; decode
  // "2.4L 4-cyl") and 2010 Matrix 2.4s (2T1KE4EE1AC045106, 2T1KE4EE9AC031549).
  const HYB_A = 'JTNBB46K073026167', HYB_B = 'JTNBB46K673029980';
  const fam = { id: 'toyota-2az', label: 'Toyota/Scion 2AZ-FE 2.4 I4', liters: [2.4], cyl: 4,
    apps: [['Toyota', 'Camry', 2002, 2006, 0, ''],
           ['Toyota', 'Camry', 2007, 2009, 0, '2007–09 Camry Hybrids also decode as 2.4L 4-cyl, but their engine parts can differ and they have no belt alternator or starter — check for HYBRID badges'],
           ['Toyota', 'Matrix', 2009, 2013, 0, '']],
    parts: { alternator: { note: 'unit note' } } };
  const ecat = { id: 'alternator', label: 'Alternator', kind: 'engine', tokens: ['alternator'], priceTokens: ['alternator'] };
  const inv = [
    car(1, 2007, 'Toyota', 'Camry', { vin: HYB_A }),
    car(2, 2007, 'Toyota', 'Camry', { vin: HYB_B }),
    car(3, 2010, 'Toyota', 'Matrix', { vin: '2T1KE4EE1AC045106' }),           // year char A = 2010
    car(4, 2011, 'Toyota', 'Matrix', { vin: '2T1KE4EE9AC031549' }),           // VIN says 2010
    car(5, 2012, 'Toyota', 'Matrix', { vpicMismatch: 'VIN decodes as Corolla (listed Matrix)' }),
  ];
  const ex = { 1: ['', '', '2.4L 4-cyl'], 2: ['', '', '2.4L 4-cyl'], 3: ['', '', '2.4L 4-cyl'],
               4: ['', '', '2.4L 4-cyl'], 5: ['', '', '2.4L 4-cyl'] };
  const data = base([], { engineFamilies: [fam] });
  for (const pc of [ecat, { id: 'engine-assembly', label: 'Engine', kind: 'engine', tokens: [], priceTokens: ['engine'], noValue: true }]) {
    const r = browse(data, inv, pc, 'toyota-2az', ex);
    const hyb = r.list.filter(x => x.name === '2007 Toyota Camry');
    check(`browse ${pc.id}: hybrid-year Camry rows (ambig app) get no VIN-confirmed chip`,
      hyb.length === 2 && hyb.every(x => !x.chip && !x.vinClass), JSON.stringify(r.rows));
    check(`browse ${pc.id}: those rows keep the ambig warning`,
      hyb.every(x => x.warn.includes('Camry Hybrids also decode as 2.4L')), JSON.stringify(hyb));
    check(`browse ${pc.id}: decode-confirmed non-ambig donor with an agreeing VIN keeps the chip`,
      r.rows['2010 Toyota Matrix']?.chip === true, JSON.stringify(r.rows['2010 Toyota Matrix']));
    check(`browse ${pc.id}: VIN year char disagrees (P0.4) -> no chip, year warning`,
      r.rows['2011 Toyota Matrix']?.chip === false && r.rows['2011 Toyota Matrix'].warn.includes('model-year code reads 2010'),
      JSON.stringify(r.rows['2011 Toyota Matrix']));
    check(`browse ${pc.id}: vpicMismatch (P0.4) -> no chip, listing warning`,
      r.rows['2012 Toyota Matrix']?.chip === false && r.rows['2012 Toyota Matrix'].warn.includes('listing doesn’t match the VIN'),
      JSON.stringify(r.rows['2012 Toyota Matrix']));
    check(`browse ${pc.id}: the "N VIN-confirmed" count leaves the hybrids and identity-flagged out`,
      r.html.includes('<strong>1</strong> VIN-confirmed') && r.html.includes('<strong>4</strong> unconfirmed'),
      (r.html.match(/pf-tier-counts">([\s\S]*?)<\/span>/) || [])[1]);
  }
  // Hint copy: engine-assembly Verified is a confirming decode, not a catalog.
  ctx2.pfVerifiedOnly = false;
  const hEng = ctx2.pfVonlyRowHtml(1, 1, 'engine'), hFit = ctx2.pfVonlyRowHtml(1, 1, 'fit');
  check('hint: engine-assembly vocab says VIN decode, not catalog data, and to match displacement',
    hEng.includes('VIN decode shows an engine in this family') && hEng.includes('match the displacement')
    && !hEng.includes('published catalog fitment data'), hEng);
  check('hint: part-number categories keep "published catalog fitment data"',
    hFit.includes('Verified = published catalog fitment data'), hFit);
  // ... and pfRunSearch passes the engine vocab for engine assembly only.
  ctx2.__seeker = { year: 2010, make: 'Toyota', model: 'Matrix' };
  const famE = { ...fam, parts: { alternator: { note: 'unit note' }, 'engine-assembly': { note: 'family note' } } };
  for (const [pc, want, notWant] of [
      [{ id: 'engine-assembly', label: 'Engine', kind: 'engine', tokens: [], priceTokens: ['engine'], noValue: true },
       'no catalog lists engine assemblies', 'published catalog fitment data'],
      [ecat, 'published catalog fitment data', 'no catalog lists engine assemblies']]) {
    Object.assign(ctx2, { interchangeData: base([], { engineFamilies: [famE] }), liveInventory: inv,
      pfCat: pc, pfChosenFam: null, __extras: ex, __els: {} });
    ctx2.pfRunSearch();
    const h = ctx2.__els['pf-results'] ? ctx2.__els['pf-results'].innerHTML : '';
    check(`fit search ${pc.id}: hint reads "${want}"`, h.includes(want) && !h.includes(notWant),
      (h.match(/<div class="pf-hint">([\s\S]*?)<\/div>/) || [])[1]);
  }
}

/* ==== §7.4 Phase 1 display: OEM catalog groups and §12 lazy files ======== */
const LIKELY_OEM_CHIP = 'Likely fits &mdash; check the part number';
const noVerifiedText = html => !/Verified fit|>Verified</.test(html);
const oemG = (over = {}) => ({ id: 'oem:toyota:side-mirrors:L:aa', ns: 'toyota', cat: 'side-mirrors', tier: 'likely',
  label: 'Toyota catalog', note: 'Toyota catalog lists #87910-06470 for both — fits some configurations; verify the number on the part',
  apps: [['Toyota', 'Camry', 2007, 2011], ['Toyota', 'Avalon', 2007, 2011]], pn: ['87910-06470'], src: 'oem', ...over });
const lazyIdx = cats => ({ oemLazy: { schema: 1, path: 'data/oem/', cats } });
{
  // (1) lazy file fetched on first search of its category, then rendered
  const g2 = oemG({ id: 'oem:toyota:side-mirrors:L:bb', pn: ['87940-06470', '87940-06480', '87940-06490'],
    note: 'Toyota catalog lists #87940-06470 for both — fits some configurations; verify the number on the part' });
  const file = { schemaVersion: 1, cat: 'side-mirrors', oemGroups: [oemG(), g2], amGroups: [] };
  ctx.__files = { 'data/oem/side-mirrors.json': file };
  ctx.__fetched = [];
  lazyPreset = null;
  const data = base([], lazyIdx({ 'side-mirrors': { oem: 2, am: 0 } }));
  let r = run(data, inv1, SEEK, cat());
  check('lazy: first search shows "Loading catalog matches…" and fetches data/oem/side-mirrors.json',
    r.status === 'Loading catalog matches…' && ctx.__fetched.join() === 'data/oem/side-mirrors.json', r.status + ' ' + ctx.__fetched);
  await new Promise(res => setTimeout(res, 0));
  r = parse(ctx);
  const row = r.rows['2010 Toyota Avalon'];
  check('lazy: after the file arrives the search re-runs and lists the catalog donor', !!row, r.html.slice(0, 300));
  check('OEM Likely row: Likely tier, chip "Likely fits — check the part number"',
    row && row.tier === 'likely' && row.chip === LIKELY_OEM_CHIP, JSON.stringify(row));
  check('OEM Likely row: source names the factory catalog and the part numbers (first two, +N more)',
    row && row.src === 'Source: Toyota factory parts catalog #87910-06470, #87940-06470 +2 more', JSON.stringify(row));
  check('OEM Likely row: keeps its group note and the category rowWarn',
    row && row.warn.includes('fits some configurations; verify the number on the part') && row.warn.includes('paint'), JSON.stringify(row));
  check('OEM Likely: ONE collapsed header line for the search, group notes not repeated in the header',
    r.head.split('Catalog part numbers shared on some configurations — verify the number').length === 2
    && !r.head.includes('Toyota catalog lists'), r.head);
  check('OEM Likely: nothing on the page says Verified', noVerifiedText(r.html), r.html);
  check('OEM Likely: the chip tooltip says carmaker catalog, some configurations',
    row && row.tip.includes('carmaker’s parts catalog') && row.tip.includes('some configurations'), row && row.tip);
  // second search: no refetch
  ctx.__fetched = [];
  ctx.__els = {};
  ctx.pfRunSearch();
  check('lazy: a loaded category is not fetched again', ctx.__fetched.length === 0 && !!parse(ctx).rows['2010 Toyota Avalon']);
}
{
  // (2) a lazy-file group that claims "verified" still renders Likely (fail closed)
  lazyPreset = { 'side-mirrors': { oemGroups: [oemG({ tier: 'verified' })], amGroups: [] } };
  const r2 = run(base([], lazyIdx({ 'side-mirrors': { oem: 1, am: 0 } })),
    [car(1, 2010, 'Toyota', 'Avalon', { vin: VIN_2012 })], SEEK, cat());
  check('lazy: "verified" in a lazy file -> Likely row, no Verified text',
    r2.rows['2010 Toyota Avalon']?.tier === 'likely' && noVerifiedText(r2.html), JSON.stringify(r2.rows));
  lazyPreset = null;
}
{
  // (3) main-file Verified OEM group: Verified only with a VIN that confirms the year
  const g = oemG({ id: 'oem:toyota:side-mirrors:V:1', tier: 'verified',
    note: 'Toyota catalog lists #87910-06470 for every trim of both', apps: [['Toyota', 'Camry', 2007, 2012], ['Toyota', 'Avalon', 2007, 2012]] });
  const inv = [car(1, 2012, 'Toyota', 'Avalon', { vin: VIN_2012 }), car(2, 2011, 'Toyota', 'Avalon')];
  const r = run(base([], { oemGroups: [g] }), inv, SEEK, cat());
  const v = r.rows['2012 Toyota Avalon'], n = r.rows['2011 Toyota Avalon'];
  check('main-file OEM Verified + valid agreeing VIN -> Verified with the OEM tooltip',
    v?.tier === 'verified' && v.tip.startsWith('Verified = the carmaker’s parts catalog lists the same part number for both cars'), JSON.stringify(v));
  check('main-file OEM Verified, donor with no VIN -> Likely, "no VIN to confirm the model year"',
    n?.tier === 'likely' && n.warn.includes('no VIN to confirm the model year'), JSON.stringify(n));
  check('main-file OEM Verified row names the catalog part number',
    v?.src === 'Source: Toyota factory parts catalog #87910-06470', JSON.stringify(v));
}
{
  // (4) hand data wins: a Verified platform row stays; a hand Likely row keeps its tier and gains the catalog line
  lazyPreset = { 'side-mirrors': { oemGroups: [oemG()], amGroups: [] } };
  const r = run(base([grp('verified')], lazyIdx({ 'side-mirrors': { oem: 1, am: 0 } })), inv1, SEEK, cat());
  const row = r.rows['2010 Toyota Avalon'];
  check('hand Verified platform row wins over an OEM Likely group (tier, chip, warnings unchanged)',
    row?.tier === 'verified' && row.chip === 'Verified fit' && !row.warn.includes('factory parts catalog') && !row.src, JSON.stringify(row));
  const r2 = run(base([grp('likely')], lazyIdx({ 'side-mirrors': { oem: 1, am: 0 } })), inv1, SEEK, cat());
  const row2 = r2.rows['2010 Toyota Avalon'];
  check('hand Likely row keeps its chip and gains the catalog line',
    row2?.tier === 'likely' && row2.chip === 'Likely fit &mdash; verify part #' && row2.warn.includes('Toyota factory parts catalog #87910-06470'),
    JSON.stringify(row2));
  lazyPreset = null;
}
{
  // (5) V9 view: with no OEM data, or OEM data for OTHER categories only, the output is byte-identical
  const inv = [car(1, 2010, 'Toyota', 'Avalon'), car(2, 2008, 'Toyota', 'Camry')];
  const plain = run(base([grp('verified')]), inv, SEEK, cat()).html;
  lazyPreset = { 'headlights': { oemGroups: [oemG({ cat: 'headlights' })], amGroups: [] } };
  const other = run(base([grp('verified')], { oemGroups: [], oemVg: {}, oemStatus: { toyota: 'ok' },
    ...lazyIdx({ headlights: { oem: 1, am: 0 } }) }), inv, SEEK, cat()).html;
  check('old-keys view unchanged: OEM data for another category leaves this search byte-identical', plain === other);
  lazyPreset = null;
  // the lazy file failing to load: hand data renders, no retry loop
  ctx.__files = { 'data/oem/side-mirrors.json': 'reject' };
  ctx.__fetched = [];
  let r = run(base([grp('verified')], lazyIdx({ 'side-mirrors': { oem: 1, am: 0 } })), inv, SEEK, cat());
  await new Promise(res => setTimeout(res, 0));
  r = parse(ctx);
  check('lazy file fails to load: the hand rows render, fetched once', r.html === plain && ctx.__fetched.length === 1,
    ctx.__fetched.join());
  // a file for the wrong category is ignored
  ctx.__files = { 'data/oem/side-mirrors.json': { cat: 'headlights', oemGroups: [oemG()], amGroups: [] } };
  run(base([grp('verified')], lazyIdx({ 'side-mirrors': { oem: 1, am: 0 } })), inv, SEEK, cat());
  await new Promise(res => setTimeout(res, 0));
  check('lazy file whose cat differs from the request is ignored', parse(ctx).html === plain);
}
{
  // (6) aftermarket unit groups (engine categories): MINI with no engine family
  const ecat = { id: 'alternator', label: 'Alternator', kind: 'engine', tokens: ['alternator'], priceTokens: ['alternator'] };
  const amg = (over = {}) => ({ id: 'am:dbe:alternator:400-24098', cat: 'alternator', tier: 'likely', src: 'aftermarket',
    label: 'DB Electrical', unit: '400-24098', amps: 110,
    note: 'DB Electrical 400-24098 (110A unit) lists these vehicles; aftermarket application data, not the carmaker\'s catalog. Match the engine and the amperage on the tag.',
    apps: [['MINI', 'Cooper', 2002, 2008, '1.6L 4-cyl']], ...over });
  const inv = [car(1, 2005, 'MINI', 'Cooper'), car(2, 2006, 'MINI', 'Cooper'), car(3, 2007, 'MINI', 'Cooper'),
    car(4, 2004, 'MINI', 'Cooper'), car(5, 2010, 'MINI', 'Cooper')];
  const ex = { 1: ['', '', '1.6L 4-cyl'], 2: ['', '', '2.0L 4-cyl'], 4: ['', '', '1.6L 4-cyl', 'Manual'], 5: ['', '', '1.6L 4-cyl'] };
  lazyPreset = { alternator: { oemGroups: [], amGroups: [amg(), amg({ id: 'am:dbe:starter:x', cat: 'starter', unit: '410-1', apps: [['MINI', 'Cooper', 2002, 2010, '1.6L']] })] } };
  const seek = { year: 2003, make: 'MINI', model: 'Cooper' };
  const r = run(base([], lazyIdx({ alternator: { oem: 0, am: 1 } })), inv, seek, ecat, ex);
  const ok = r.rows['2005 MINI Cooper'];
  check('aftermarket: MINI donor with an agreeing engine is listed Likely with the Likely chip',
    ok?.tier === 'likely' && ok.chip === LIKELY_OEM_CHIP, JSON.stringify(r.rows) + r.html.slice(0, 300));
  check('aftermarket: source names the aftermarket unit and its amperage',
    ok?.src === 'Source: aftermarket unit: DB Electrical 400-24098 (110 A unit)', ok && ok.src);
  check('aftermarket: row keeps the unit note and says which engine of yours the unit lists',
    ok?.warn.includes('aftermarket application data, not the carmaker&#39;s catalog') || ok?.warn.includes('not the carmaker'), ok && ok.warn);
  check('aftermarket: row says the unit lists your engine (1.6L 4-cyl)', ok?.warn.includes('with the 1.6L 4-cyl — match your engine'), ok && ok.warn);
  check('aftermarket: donor whose decode says another engine (2.0L) is left out', !r.rows['2006 MINI Cooper'], JSON.stringify(r.rows['2006 MINI Cooper']));
  check('aftermarket: undecoded donor kept with "engine not confirmed"',
    r.rows['2007 MINI Cooper']?.warn.includes('engine not confirmed'), JSON.stringify(r.rows['2007 MINI Cooper']));
  check('aftermarket: donor outside the unit\'s years is left out', !r.rows['2010 MINI Cooper']);
  check('aftermarket: header explains the rebuilder\'s list, not the carmaker\'s',
    r.head.includes('Aftermarket match:') && r.head.includes('not the carmaker'), r.head);
  check('aftermarket: nothing on the page says Verified', noVerifiedText(r.html), r.html);
  check('aftermarket: chip tooltip says aftermarket rebuilder, not the carmaker',
    ok?.tip.includes('aftermarket rebuilder (not the carmaker)'), ok && ok.tip);
  check('aftermarket: a starter unit does not answer an alternator search', !r.html.includes('410-1'));
  // trans gate and a "verified" claim in data
  lazyPreset = { alternator: { oemGroups: [], amGroups: [amg({ trans: 'AT', tier: 'verified' })] } };
  const r2 = run(base([], lazyIdx({ alternator: { oem: 0, am: 1 } })), inv, seek, ecat, ex);
  check('aftermarket: an automatic-only unit leaves out a decoded manual donor', !r2.rows['2004 MINI Cooper'], JSON.stringify(r2.rows['2004 MINI Cooper']));
  check('aftermarket: unknown transmission kept with a check-the-transmission warning',
    r2.rows['2005 MINI Cooper']?.warn.includes('automatic-transmission cars'), JSON.stringify(r2.rows['2005 MINI Cooper']));
  check('aftermarket: an amGroup claiming "verified" still renders Likely',
    Object.values(r2.rows).length > 0 && Object.values(r2.rows).every(x => x.tier === 'likely') && noVerifiedText(r2.html), JSON.stringify(r2.rows));
  // (7) a car with neither: the honest empty state stands
  lazyPreset = { alternator: { oemGroups: [], amGroups: [amg()] } };
  const r3 = run(base([], lazyIdx({ alternator: { oem: 0, am: 1 } })), inv, { year: 2003, make: 'Geo', model: 'Metro' }, ecat, ex);
  check('neither layer covers the car: "No interchange data yet" empty state, no rows',
    r3.html.includes('No interchange data yet') && Object.keys(r3.rows).length === 0, r3.html);
  // (8) hand engine family present: family rows win, the unit adds donors the family does not list
  const fam = { id: 'mini-w10', label: 'MINI W10 1.6', liters: [1.6], cyl: 4, apps: [['MINI', 'Cooper', 2002, 2006, 0, '']],
    parts: { alternator: { note: 'unit note', vg: [[['MINI', 'Cooper', 2002, 2006]]] } } };
  lazyPreset = { alternator: { oemGroups: [], amGroups: [amg()] } };
  const r4 = run(base([], { engineFamilies: [fam], ...lazyIdx({ alternator: { oem: 0, am: 1 } }) }), inv, seek, ecat, ex);
  check('with a hand family: its Verified row stays Verified and gets no aftermarket line',
    r4.rows['2005 MINI Cooper']?.tier === 'verified' && !r4.rows['2005 MINI Cooper'].warn.includes('aftermarket unit'), JSON.stringify(r4.rows['2005 MINI Cooper']));
  check('with a hand family: the unit adds the 2007 donor the family does not list, Likely, unit named',
    r4.rows['2007 MINI Cooper']?.tier === 'likely' && r4.rows['2007 MINI Cooper'].src.includes('DB Electrical 400-24098'), JSON.stringify(r4.rows['2007 MINI Cooper']));
  lazyPreset = null;
}
{
  // (9) oemVg (engine branch, main file): Verified needs a VIN that confirms the year
  const fam = { id: 'fam-o', label: 'Test 2.4 I4', liters: [2.4], cyl: 4, apps: [['Toyota', 'Camry', 2004, 2013, 0, '']],
    parts: { alternator: { note: 'unit note' } } };
  const ecat = { id: 'alternator', label: 'Alternator', kind: 'engine', tokens: ['alternator'], priceTokens: ['alternator'] };
  const inv = [car(1, 2013, 'Toyota', 'Camry', { vin: VIN_2013 }), car(2, 2012, 'Toyota', 'Camry')];
  const extras = { 1: ['', '', '2.4L 4-cyl'], 2: ['', '', '2.4L 4-cyl'] };
  const r = run(base([], { engineFamilies: [fam], oemVg: { 'fam-o': { alternator: [[['Toyota', 'Camry', 2004, 2013]]] } } }),
    inv, { year: 2010, make: 'Toyota', model: 'Camry' }, ecat, extras);
  check('oemVg: donor with a valid agreeing VIN is Verified with the OEM tooltip',
    r.rows['2013 Toyota Camry']?.tier === 'verified' && r.rows['2013 Toyota Camry'].tip.startsWith('Verified = the carmaker'), JSON.stringify(r.rows));
  check('oemVg: donor with no VIN -> Likely, "no VIN to confirm the model year"',
    r.rows['2012 Toyota Camry']?.tier === 'likely' && r.rows['2012 Toyota Camry'].warn.includes('no VIN to confirm'), JSON.stringify(r.rows['2012 Toyota Camry']));
  const r0 = run(base([], { engineFamilies: [fam] }), inv, { year: 2010, make: 'Toyota', model: 'Camry' }, ecat, extras);
  check('no vg at all: the same donors stay Likely', Object.values(r0.rows).every(x => x.tier === 'likely'));
}
{
  // (10) JS engine mirror vs the Python original (aftermarket/groups_am.py)
  const cases = [['1.6L', '1.6L 4-cyl'], ['1.6L 4-cyl', '2.0L 4-cyl'], ['2.0L 4-cyl Diesel', '2.0L 4-cyl'],
    ['', '1.6L'], ['3.5L V6', '3.5L 6-cyl'], ['3.5L V6', '3.5L 8-cyl'], ['5.7L', ''], ['1.6l 4-cyl', '1.64L'],
    ['2.2L 4-cyl diesel', '2.2L diesel 4-cyl'], ['4.6L W8', '4.6L 8-cyl'], ['1.8L', '1.85L'], ['1.8L', '1.84L']];
  const py = JSON.parse(execFileSync('python3', ['-I', '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(new URL('../../scraper/oem_fitment/aftermarket', import.meta.url).pathname)})
import groups_am as G
cases = json.loads(sys.argv[1])
print(json.dumps([G.engine_agrees(G.parse_engine(a), G.parse_engine(b)) for a, b in cases]
                 + [G.car_trans(s) for s in ["Manual", "Automatic", "CVT", "6-speed auto", ""]]))
`, JSON.stringify(cases)]).toString());
  const js = cases.map(([a, b]) => ctx.pfAmEngineAgrees(a, b))
    .concat(['Manual', 'Automatic', 'CVT', '6-speed auto', ''].map(x => ctx.pfAmCarTrans(x)));
  check('pfAmEngineAgrees / pfAmCarTrans agree with groups_am.py on every case', JSON.stringify(js) === JSON.stringify(py),
    JSON.stringify(js) + ' vs ' + JSON.stringify(py));
}

{
  // (11) Wheels (ops/interchange.md "Wheels"): the shipped category is a
  // same-model-generation Likely search with the lug/size check on every
  // row; the yard price reads "each" and no savings line compares one wheel
  // with a set-of-4 value.
  const real = JSON.parse(fs.readFileSync(new URL('../../docs/data/interchange.json', import.meta.url), 'utf8'));
  const wc = real.categories.find(c => c.id === 'wheels');
  check('interchange.json ships a wheels category (body kind, perEach, rowWarn)',
    !!wc && wc.kind === 'body' && wc.perEach === true && /lugs/.test(wc.rowWarn || ''), JSON.stringify(wc));
  check('no platform group or main-file OEM group claims a cross-model wheel fit',
    !real.platformGroups.some(g => g.cat === 'wheels') && !(real.oemGroups || []).some(g => g.cat === 'wheels'));
  check('wheels notes carry the yard checks (TPMS, lug nuts, spares, curb rash, tire size)',
    ['TPMS', 'lug', 'spare', 'curb rash', 'tire size'].every(k => (wc.notes || []).join(' ').includes(k)));
  const steer = { name: 'Steering Wheel (no airbag)', low: 20, high: 40 };
  const set = { name: '17"/18" Alloy Wheels (set)', low: 200, high: 400, fits: '2007–2011' };
  const trim = { name: 'Red Line Trim + Wheels', low: 50, high: 90 };
  check('pfPartRow(wheels) finds the wheel-set row, never the steering wheel or a trim kit',
    ctx.pfPartRow({ topParts: [steer, trim, set] }, wc) === set
    && ctx.pfPartRow({ topParts: [steer, trim] }, wc) === null);
  const gens = { modelGenerations: [['Toyota', 'Camry', [[2007, 2011], [2012, 2017]]]] };
  const inv = [car(1, 2010, 'Toyota', 'Camry', { topParts: [set] }), car(2, 2013, 'Toyota', 'Camry'),
    car(3, 2010, 'Toyota', 'Avalon', { topParts: [set] }), car(4, 2008, 'Toyota', 'Camry')];
  const saved = { isPro: ctx.isPro, q: ctx.yardPartQuote, o: ctx.onlinePriceHtml };
  ctx.isPro = () => true;
  ctx.yardPartQuote = () => ({ status: 'priced', part: 'WHEEL ALUMINUM', price: 31.99, core: 0 });
  ctx.onlinePriceHtml = () => '<span class="pf-ebay">$200–$400</span>';
  const r = run({ ...real, ...gens, platformGroups: real.platformGroups, oemGroups: [] }, inv,
    { year: 2009, make: 'Toyota', model: 'Camry' }, wc);
  const names = Object.keys(r.rows).sort();
  check('wheels: same-generation Camry donors only (no Avalon, no 2013)',
    JSON.stringify(names) === JSON.stringify(['2008 Toyota Camry', '2010 Toyota Camry']), JSON.stringify(names));
  check('wheels: every donor Likely, with the lug-count check on the row',
    Object.values(r.rows).every(x => x.tier === 'likely' && x.warn.includes('count the lugs')), JSON.stringify(r.rows));
  check('wheels: yard price reads "each" with the yard row (size tier) inline, and no savings line', r.html.includes('Yard: $31.99 each <span class="pf-price-row"') && r.html.includes('(WHEEL ALUMINUM)') && !r.html.includes('pf-save'));
  const rm = run(base([], gens), inv, { year: 2009, make: 'Toyota', model: 'Camry' }, cat());
  check('other categories: no "each" on the yard price', rm.html.includes('Yard: $31.99') && !rm.html.includes('Yard: $31.99 each'), '');
  Object.assign(ctx, { isPro: saved.isPro, yardPartQuote: saved.q, onlinePriceHtml: saved.o });
}

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
