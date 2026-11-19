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

const REAL_FNS = ['escapeHtml', 'pfYardPriceHtml', 'normalizeVinForDedupe', 'pfSquash', 'pfSquashModel',
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
const P1_CONSTS = ['PF_OEM_LIKELY_HEAD', 'PF_AM_HEAD', 'PF_AM_HEAD_PART'];

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
// Gated aftermarket app rows (2026-11-09): the AM-GATE block (pfAmGate and its
// helpers, multi-line consts) comes in whole; scraper/test_am_gates.py tests it.
{
  const m = src.match(/\/\* AM-GATE BEGIN[\s\S]*?\/\* AM-GATE END \*\//);
  check('app.js carries the AM-GATE block', !!m);
  if (m) { new vm.Script(m[0]); code += m[0] + '\n'; }
  else code += 'function pfAmGateParse() { return null; } function pfAmGate() { return "confirm"; } function pfAmGateText() { return ""; }\n';
}
// Gated OEM app rows (gates-1118): the OEM-GATE block (pfOemGate and helpers).
// Absent in an older app.js: stubbed open (no gate), so the OEM gate checks
// below fail there, as they should.
{
  const m = src.match(/\/\* OEM-GATE BEGIN[\s\S]*?\/\* OEM-GATE END \*\//);
  check('app.js carries the OEM-GATE block', !!m);
  if (m) { new vm.Script(m[0]); code += m[0] + '\n'; }
  else code += 'function pfOemGateParse() { return null; } function pfOemGateText() { return ""; } function pfOemGate() { return { verdict: "confirm", keys: [] }; } function pfOemDonorGate() { return { verdict: "confirm", warn: "" }; }\n';
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
var extraIdx = { photo: 0, color: 1, engine: 2, trans: 3, transSrc: 4, body: 5 };
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
function track() {} function pfSearchSignal() {} function pfCountSearch() {} function pfSaveState() {}
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
var __priceList = null;
function yardPriceList() { return __priceList; }
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
// Card pieces added 2026-11-13 (share button, trim badge): not under test here.
function cardEndActionsHtml() { return ''; }
function notableTrimBadgeHtml() { return ''; }
function pfRenderTiles() {}
function pfRevealResults() {}
// The radius-first loader's "cars around the centre still loading?" (2026-11-18): all in here.
function invViewPending() { return false; }
var _pfAwaitShards = false;
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
  // 2026-11-10 (hub): the note's checks stay inline; its provenance moved
  // behind "Why it fits" on the same card (nothing dropped).
  check('aftermarket: row keeps the note\'s check inline (engine + amperage)',
    ok?.warn.includes('Match the engine and the amperage on the tag'), ok && ok.warn);
  check('aftermarket: the note\'s provenance is on the card behind "Why it fits", not inline',
    /pf-src-more-text">[^<]*not the carmaker/.test(r.html) && !(ok?.warn || '').includes('not the carmaker'), ok && ok.warn);
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

/* ---- Same engine, different model (owner, 2026-11-09) ---------------------
 * Real toyota-2uz shape: the family spans Tundra/Sequoia/4Runner/Land
 * Cruiser/GX 470/LX 470, but the alternator part-number list (vg) covers only
 * Tundra 2003-09 + Sequoia 2003-09. A donor joined to the seeker ONLY by the
 * family, of another base model, is "Same engine — part may differ", listed
 * after Verified and part-number-backed Likely rows, with its own count. */
{
  const fam2uz = { id: 'toyota-2uz', label: 'Toyota/Lexus 2UZ-FE 4.7 V8', liters: [4.7], cyl: 8,
    apps: [['Toyota', 'Tundra', 2000, 2009, 0, ''], ['Toyota', 'Sequoia', 2001, 2009, 0, ''],
      ['Toyota', 'Land Cruiser', 1998, 2007, 1, ''], ['Toyota', '4Runner', 2003, 2009, 0, ''],
      ['Lexus', 'GX 470', 2003, 2009, 1, ''], ['Lexus', 'LX 470', 1998, 2007, 1, '']],
    parts: {
      alternator: { note: '2UZ unit', vg: [[['Toyota', 'Tundra', 2003, 2009], ['Toyota', 'Sequoia', 2003, 2009]]] },
      'engine-assembly': { note: 'same long block' },
    } };
  const acat = { id: 'alternator', label: 'Alternator', kind: 'engine', tokens: ['alternator'], priceTokens: ['alternator'] };
  const engcat = { id: 'engine-assembly', label: 'Engine', kind: 'engine', tokens: ['engine'], priceTokens: ['engine'], noValue: true };
  const V8 = ['', '', '4.7L 8-cyl'];
  const inv = [
    car(1, 2005, 'Toyota', 'Tundra'),        // nearest, other model, no vg with a GX
    car(2, 2006, 'Lexus', 'GX 470'),         // same model, outside any vg
    car(3, 2005, 'Toyota', 'Sequoia'),
    car(4, 2002, 'Toyota', 'Tundra'),        // outside the vg years
  ];
  const extras = { 1: V8, 2: V8, 3: V8, 4: V8 };
  const data = base([], { engineFamilies: [fam2uz] });
  const GX = { year: 2005, make: 'Lexus', model: 'GX 470' };
  const r = run(data, inv, GX, acat, extras);
  const tu = r.rows['2005 Toyota Tundra'], gx = r.rows['2006 Lexus GX 470'];
  check('same-engine: GX 470 seeker + Tundra alternator donor -> "Same engine — part may differ"',
    tu?.chip === 'Same engine &mdash; part may differ', JSON.stringify(tu));
  check('same-engine: its tooltip says different model / match the number on both cars, not "very likely"',
    /different model/.test(tu?.tip) && /both cars/.test(tu?.tip) && !/very likely/i.test(tu?.tip), tu?.tip);
  check('same-engine: card stays pf-likely (Verified-only hides it) and carries pf-same-engine',
    /pf-row-card pf-likely pf-same-engine/.test(r.html), r.html.slice(0, 300));
  check('same-engine: same-model GX donor outside the vg keeps a Likely label',
    gx?.tier === 'likely' && gx.chip === 'Likely fit &mdash; verify part #', JSON.stringify(gx));
  check('same-engine: the Likely tooltip no longer says "very likely fits"',
    !/very likely/i.test(gx?.tip || 'very likely'), gx?.tip);
  const order = Object.keys(r.rows);
  check('same-engine: rows list after the part-number-backed / same-model rows (nearer Tundra goes last group)',
    order.indexOf('2006 Lexus GX 470') < order.indexOf('2005 Toyota Tundra')
    && order.indexOf('2006 Lexus GX 470') < order.indexOf('2005 Toyota Sequoia'), order.join(' | '));
  check('same-engine: no "very likely" text anywhere in the rendered list', !/very likely/i.test(r.html));

  // Tundra 2005 seeker + Sequoia 2005 donor: one vg names both -> Verified.
  const rT = run(data, inv, { year: 2005, make: 'Toyota', model: 'Tundra' }, acat, extras);
  check('same-engine: Tundra 2005 + Sequoia 2005 alternator -> Verified', rT.rows['2005 Toyota Sequoia']?.tier === 'verified',
    JSON.stringify(rT.rows['2005 Toyota Sequoia']));
  check('same-engine: Tundra seeker + GX donor (outside the vg) -> same-engine label',
    rT.rows['2006 Lexus GX 470']?.chip === 'Same engine &mdash; part may differ', JSON.stringify(rT.rows['2006 Lexus GX 470']));
  check('same-engine: Tundra 2005 seeker + 2002 Tundra (same model, outside vg years) -> Likely',
    rT.rows['2002 Toyota Tundra']?.chip === 'Likely fit &mdash; verify part #', JSON.stringify(rT.rows['2002 Toyota Tundra']));

  // vg names both but the donor engine is unconfirmed -> part-number-backed Likely, not same-engine.
  const rU = run(data, inv, { year: 2005, make: 'Toyota', model: 'Tundra' }, acat, { ...extras, 3: ['', '', ''] });
  check('same-engine: vg-joined donor with an unconfirmed engine stays plain Likely',
    rU.rows['2005 Toyota Sequoia']?.tier === 'likely' && rU.rows['2005 Toyota Sequoia'].chip === 'Likely fit &mdash; verify part #',
    JSON.stringify(rU.rows['2005 Toyota Sequoia']));

  // Engine assembly: the long block is the fit; label unchanged.
  const rE = run(data, inv, GX, engcat, extras);
  check('same-engine: engine-assembly search never uses the new label',
    !/Same engine &mdash; part may differ/.test(rE.html) && rE.rows['2005 Toyota Tundra']?.tier === 'verified',
    JSON.stringify(rE.rows['2005 Toyota Tundra']));

  // An aftermarket unit list naming both cars makes the row part-number-backed.
  lazyPreset = { alternator: { oemGroups: [], amGroups: [{ id: 'am#gx', cat: 'alternator', src: 'aftermarket', tier: 'likely',
    label: 'DB Electrical', unit: '400-52xxx', note: 'unit note', apps: [['Lexus', 'GX 470', 2003, 2009, ''], ['Toyota', 'Tundra', 2003, 2006, '']] }] } };
  const rA = run(data, inv, GX, acat, extras);
  lazyPreset = null;
  check('same-engine: an aftermarket list naming both cars lifts the row to part-number-backed Likely',
    rA.rows['2005 Toyota Tundra']?.chip === 'Likely fits &mdash; check the part number', JSON.stringify(rA.rows['2005 Toyota Tundra']));

  // Free users still see no values; Pro does.
  const invP = inv.map(v => ({ ...v, topParts: [{ name: 'Alternator', low: 40, high: 90 }] }));
  ctx.onlinePriceHtml = () => '<span class="VALUEMARK">$40-90</span>';
  const rFree = run(data, invP, GX, acat, extras);
  ctx.isPro = () => true;
  const rPro = run(data, invP, GX, acat, extras);
  ctx.isPro = () => false;
  ctx.onlinePriceHtml = () => '';
  check('same-engine: free users see no value on any row', !/VALUEMARK/.test(rFree.html));
  check('same-engine: Pro users see the value on same-engine rows too',
    (rPro.html.split('pf-same-engine')[1] || '').includes('VALUEMARK'));

  // Counts: real pfVonlyRowHtml (ctx2) — same-engine has its own count.
  ctx2.pfVerifiedOnly = false;
  const hc = ctx2.pfVonlyRowHtml(1, 3, 'fit', 2);
  check('same-engine: tier counts read "1 verified · 1 likely · 2 same engine"',
    /<strong>1<\/strong> verified &middot; <strong>1<\/strong> likely &middot; <strong>2<\/strong> same engine/.test(hc), hc);
  check('same-engine: no same-engine count when there are none',
    !/same engine/.test(ctx2.pfVonlyRowHtml(1, 3, 'fit')));
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
  ctx.onlinePriceHtml = (p, c, v, unit = '') => `<span class="pf-ebay">$200–$400${unit}</span>`;
  // the shipped payload indexes a wheels lazy file (OEM wheels groups, 2026-11-09):
  // these checks isolate the same-generation search with that file loaded and empty
  lazyPreset = { wheels: { oemGroups: [], amGroups: [] } };
  const r = run({ ...real, ...gens, platformGroups: real.platformGroups, oemGroups: [] }, inv,
    { year: 2009, make: 'Toyota', model: 'Camry' }, wc);
  const names = Object.keys(r.rows).sort();
  check('wheels: same-generation Camry donors only (no Avalon, no 2013)',
    JSON.stringify(names) === JSON.stringify(['2008 Toyota Camry', '2010 Toyota Camry']), JSON.stringify(names));
  check('wheels: every donor Likely, with the lug-count check on the row',
    Object.values(r.rows).every(x => x.tier === 'likely' && x.warn.includes('count the lugs')), JSON.stringify(r.rows));
  check('wheels: yard price reads "each" with the yard row (size tier) inline, and no savings line', r.html.includes('Yard: $31.99 each <span class="pf-price-row"') && r.html.includes('(WHEEL ALUMINUM)') && !r.html.includes('pf-save'));
  check('wheels: the online value says it is for a set of 4 (the yard price is per wheel)', r.html.includes('$200–$400 for a set of 4</span>'), '');
  check('wheels: header reads "carry fitting wheels" (no "a" before a plural label)',
    /carr(y|ies) fitting wheels/.test(r.html) && !r.html.includes('a fitting wheels'), (r.html.match(/carr[^<]{0,40}/) || [''])[0]);
  // size-tiered yard list: the line shows the whole per-wheel range, never only the cheapest tier
  ctx.yardPartQuote = () => ({ status: 'priced', part: 'WHEEL ALUM UNDER 16"', price: 28.99, core: 14 });
  ctx.__priceList = [{ part: 'WHEEL ALUM UNDER 16"', price: 28.99, core: 14 }, { part: 'WHEEL ALUM OVER 16"', price: 39.99, core: 14 },
    { part: 'WHEEL STEEL', price: 19.99, core: 0 }, { part: 'STEERING WHEEL', price: 24.99, core: 0 }];
  const rt = run({ ...real, ...gens, platformGroups: real.platformGroups, oemGroups: [] }, inv,
    { year: 2009, make: 'Toyota', model: 'Camry' }, wc);
  check('wheels: a size-tiered yard shows the per-wheel range by size with both row names',
    rt.html.includes('Yard: $28.99\u2013$39.99 each by size') && rt.html.includes('(WHEEL ALUM UNDER 16&quot; \u2026 WHEEL ALUM OVER 16&quot;)')
    && !rt.html.includes('$19.99') && !rt.html.includes('$24.99'), (rt.html.match(/Yard:[^\n]{0,160}/) || [''])[0]);
  ctx.__priceList = null;
  ctx.yardPartQuote = () => ({ status: 'priced', part: 'WHEEL ALUMINUM', price: 31.99, core: 0 });
  // a shipped OEM wheels group (Mopar 1AN31PAKAD, census OK) adds a cross-model donor
  // as Likely, part-number-backed; never Verified
  const vanGens = { modelGenerations: [['Chrysler', 'Town & Country', [[2008, 2016]]], ['Dodge', 'Grand Caravan', [[2008, 2020]]]] };
  const vinv = [car(11, 2010, 'Dodge', 'Grand Caravan', { topParts: [set] }), car(12, 2010, 'Chrysler', 'Town & Country')];
  lazyPreset = { wheels: { oemGroups: [{ id: 'oem:mopar:wheels:C:x', ns: 'mopar', src: 'oem', label: 'Mopar catalog', cat: 'wheels', tier: 'likely', kind: 'body', pn: ['1AN31PAKAD'],
    apps: [['Chrysler', 'Town & Country', 2010, 2010], ['Dodge', 'Grand Caravan', 2010, 2010]], reason: 'trim',
    note: 'Mopar catalog lists #1AN31PAKAD for both' }], amGroups: [] } };
  const rv = run({ ...real, ...vanGens, platformGroups: real.platformGroups, oemGroups: [] }, vinv,
    { year: 2010, make: 'Chrysler', model: 'Town & Country' }, wc);
  const gc = rv.rows['2010 Dodge Grand Caravan'];
  check('wheels: a shipped OEM wheels group adds the cross-model Grand Caravan donor as Likely (never Verified)',
    !!gc && gc.tier === 'likely', JSON.stringify(rv.rows));
  lazyPreset = null;
  const rm = run(base([], gens), inv, { year: 2009, make: 'Toyota', model: 'Camry' }, cat());
  check('other categories: no "each" on the yard price', rm.html.includes('Yard: $31.99') && !rm.html.includes('Yard: $31.99 each'), '');
  Object.assign(ctx, { isPro: saved.isPro, yardPartQuote: saved.q, onlinePriceHtml: saved.o });
}

/* ==== OEM-GATE (gates-1118): per-app limits on OEM catalog groups ========
 * A gated OEM app is [make, model, lo, hi, null, gate]. A donor whose own VIN
 * decode or listing contradicts the limit is not offered; one the car cannot
 * confirm stays, "if equipped", with a line naming the limit (the aftermarket
 * gate's and the parts table's rule for unknown); a group with no gate renders
 * exactly as before. */
{
  const G = (gate, v = {}, ex = null) => ctx.pfOemGate(gate, { model: 'Tahoe', ...v }, ex).verdict;
  const DT4 = '4WD/4-Wheel Drive/4x4', DT2 = '4x2';
  // drive
  check('gate drive 2wd: a 4WD decode excludes', G({ drive: '2wd' }, { vpicDriveType: DT4 }) === 'exclude');
  check('gate drive 2wd: an AWD decode excludes', G({ drive: '2wd' }, { vpicDriveType: 'AWD/All-Wheel Drive' }) === 'exclude');
  check('gate drive 2wd: 4x2, RWD and FWD decodes confirm',
    G({ drive: '2wd' }, { vpicDriveType: DT2 }) === 'confirm' && G({ drive: '2wd' }, { vpicDriveType: 'RWD/Rear-Wheel Drive' }) === 'confirm'
    && G({ drive: '2wd' }, { vpicDriveType: 'FWD/Front-Wheel Drive' }) === 'confirm');
  check('gate drive 2wd: no decode -> unconfirmed (shown, "if equipped")', G({ drive: '2wd' }, {}) === 'unconfirmed');
  check('gate drive 2wd: a decode naming both families ("2WD/4WD") -> unconfirmed', G({ drive: '2wd' }, { vpicDriveType: '2WD/4WD' }) === 'unconfirmed');
  check('gate drive 2wd: the listing naming it confirms ("Tahoe 2WD", no decode)', G({ drive: '2wd' }, { model: 'Tahoe 2WD' }) === 'confirm');
  check('gate drive 4wd: 4x2 excludes, 4WD confirms, no decode unconfirmed',
    G({ drive: '4wd' }, { vpicDriveType: DT2 }) === 'exclude' && G({ drive: '4wd' }, { vpicDriveType: DT4 }) === 'confirm'
    && G({ drive: '4wd' }, {}) === 'unconfirmed');
  check('gate drive awd vs a 4WD decode: excluded, as pfAmDriveVerdict does (one class named, not the gate’s)',
    G({ drive: 'awd' }, { vpicDriveType: DT4 }) === 'exclude' && ctx.pfAmDriveVerdict('awd', 'ML350', DT4) === 'exclude');
  check('gate drive fwd: 4x2 (front or rear not said) -> unconfirmed; RWD excludes',
    G({ drive: 'fwd' }, { vpicDriveType: DT2 }) === 'unconfirmed' && G({ drive: 'fwd' }, { vpicDriveType: 'RWD/Rear-Wheel Drive' }) === 'exclude');
  check('gate drive fwd/rwd reads as 2WD (4x2 confirms)', G({ drive: 'fwd/rwd' }, { vpicDriveType: DT2 }) === 'confirm');
  check('gate drive a4wd (All-Mode 4WD): a 4WD decode cannot confirm it; 4x2 excludes',
    G({ drive: 'a4wd' }, { vpicDriveType: DT4 }) === 'unconfirmed' && G({ drive: 'a4wd' }, { vpicDriveType: DT2 }) === 'exclude');
  check('drive_basis does not change the gate', G({ drive: '2wd', drive_basis: 'unchecked' }, { vpicDriveType: DT4 }) === 'exclude'
    && G({ drive: '2wd', drive_basis: 'stated' }, { vpicDriveType: DT2 }) === 'confirm');
  // body (the decode's silhouette, extras position 5)
  const ex = (o = {}) => ['', '', o.engine || '', o.trans || '', '', o.body || ''];
  check('gate body coupe: a sedan decode excludes, a coupe decode confirms, no decode unconfirmed',
    G({ body: 'coupe' }, { model: 'Altima' }, ex({ body: 'sedan' })) === 'exclude'
    && G({ body: 'coupe' }, { model: 'Altima' }, ex({ body: 'coupe' })) === 'confirm'
    && G({ body: 'coupe' }, { model: 'Altima' }, null) === 'unconfirmed');
  check('gate body coupe: the listing naming it confirms ("Altima Coupe")', G({ body: 'coupe' }, { model: 'Altima Coupe' }, null) === 'confirm');
  check('gate body list [sedan, coupe]: coupe confirms, wagon excludes',
    G({ body: ['sedan', 'coupe'] }, { model: 'G37' }, ex({ body: 'coupe' })) === 'confirm'
    && G({ body: ['sedan', 'coupe'] }, { model: 'G37' }, ex({ body: 'wagon' })) === 'exclude');
  // cab
  check('gate cab: listing or VIN series naming the cab confirms; another cab excludes; nothing said unconfirmed',
    G({ cab: 'crew cab' }, { model: 'Colorado Crew Cab' }) === 'confirm'
    && G({ cab: 'crew cab' }, { model: 'Colorado', vpicSeries: 'Extended Cab' }) === 'exclude'
    && G({ cab: 'crew cab' }, { model: 'Colorado', vpicSeries: '1/2 Ton' }) === 'unconfirmed');
  check('gate cab: a "Crew" trim (Grand Caravan) is not a cab', G({ cab: 'crew cab' }, { model: 'Grand Caravan', vpicTrim: 'Crew', vpicTrimQuality: 'usable' }) === 'unconfirmed');
  check('gate cab: a decode naming two cabs ("Club Cab, Quad Cab") confirms neither',
    G({ cab: 'quad cab' }, { model: 'Dakota', vpicTrim: 'Laramie Club Cab, Quad Cab', vpicTrimQuality: 'usable' }) === 'unconfirmed');
  // engine, transmission, fuel
  check('gate eng 3.7L: 3.7L confirms, 5.6L excludes, unknown unconfirmed',
    G({ eng: ['3.7L'] }, { model: 'Q70' }, ex({ engine: '3.7L 6-cyl' })) === 'confirm'
    && G({ eng: ['3.7L'] }, { model: 'Q70' }, ex({ engine: '5.6L 8-cyl' })) === 'exclude'
    && G({ eng: ['3.7L'] }, { model: 'Q70' }, null) === 'unconfirmed');
  check('gate trans MT: manual confirms, automatic and AMT exclude, unknown unconfirmed',
    G({ trans: 'MT' }, {}, ex({ trans: '6-spd Manual/Standard' })) === 'confirm'
    && G({ trans: 'MT' }, {}, ex({ trans: '5-spd Automatic' })) === 'exclude'
    && G({ trans: 'MT' }, {}, ex({ trans: 'Automated Manual Transmission (AMT)' })) === 'exclude'
    && G({ trans: 'MT' }, {}, null) === 'unconfirmed');
  check('gate fuel gas: as the parts table (§22.10): a hybrid named by the VIN series or a diesel decode excludes; FFV and plain confirm',
    G({ fuel: 'gas' }, { model: 'Silverado 1500', vpicSeries: '1/2 Ton Hybrid' }) === 'exclude'
    && G({ fuel: 'gas' }, { model: 'Silverado 1500' }, ex({ engine: '6.6L 8-cyl Diesel' })) === 'exclude'
    && G({ fuel: 'gas' }, { model: 'Silverado 1500' }, ex({ engine: '5.3L 8-cyl Flexible Fuel Vehicle (FFV)' })) === 'confirm'
    && G({ fuel: 'gas' }, { model: 'Silverado 1500' }, null) === 'confirm');
  check('gate fuel hybrid: a hybrid named confirms, nothing said unconfirmed',
    G({ fuel: 'hybrid' }, { model: 'Q70', vpicTrim: 'Hybrid', vpicTrimQuality: 'usable' }) === 'confirm'
    && G({ fuel: 'hybrid' }, { model: 'Q70' }, null) === 'unconfirmed');
  check('no gate (4-element app) confirms', G(undefined, { vpicDriveType: DT4 }) === 'confirm');
  const W = gate => ctx.pfOemDonorGate([['Ram', '1500', 2012, 2012, null, gate]], { model: '1500' }, null).warn;
  check('donor line: a stated drive limit is "listed for", an unchecked one "checked for" (as the note words it)',
    W({ drive: '4wd', drive_basis: 'stated' }).startsWith('if equipped: this part is listed for 4WD only')
    && W({ drive: '4wd', drive_basis: 'unchecked' }).startsWith('if equipped: this part is checked for 4WD only'));
  check('donor gate: every matching app ruled out -> exclude; one ungated app -> confirm',
    ctx.pfOemDonorGate([['Ram', '1500', 2012, 2012, null, { drive: '4wd' }]], { model: '1500', vpicDriveType: DT2 }, null).verdict === 'exclude'
    && ctx.pfOemDonorGate([['Ram', '1500', 2012, 2012, null, { drive: '4wd' }], ['Ram', '1500', 2012, 2012]], { model: '1500', vpicDriveType: DT2 }, null).verdict === 'confirm');
  check('gate text words the limit like the note', ctx.pfOemGateText({ cab: 'crew cab', drive: '4wd', eng: ['2.4L'] }) === 'crew cab, 4WD, 2.4L'
    && ctx.pfOemGateText({ drive: 'fwd/rwd' }) === '2WD' && ctx.pfOemGateText({ eng: ['3.7L'], fuel: 'gas' }) === '3.7L, gas');
}
{
  // pfRunSearch: a 2WD-only Tahoe app; the twin (Avalanche) app has no limit
  const twoWd = { drive: '2wd', drive_basis: 'unchecked' };
  const gTahoe = oemG({ id: 'oem:gm:side-mirrors:L:t1', ns: 'gm', label: 'GM catalog', pn: ['22853025'],
    note: 'GM catalog lists #22853025 for both — fits some configurations; Tahoe: only 2WD checked; verify the number on the part',
    apps: [['Chevrolet', 'Avalanche', 2006, 2008], ['Chevrolet', 'Tahoe', 2006, 2008, null, twoWd]] });
  const inv = [car(1, 2006, 'Chevrolet', 'Tahoe', { vpicDriveType: '4WD/4-Wheel Drive/4x4' }),
    car(2, 2007, 'Chevrolet', 'Tahoe', { vpicDriveType: '4x2' }),
    car(3, 2008, 'Chevrolet', 'Tahoe'),
    car(4, 2007, 'Chevrolet', 'Avalanche', { vpicDriveType: '4WD/4-Wheel Drive/4x4' })];
  const seek = { year: 2007, make: 'Chevrolet', model: 'Avalanche' };
  lazyPreset = { 'side-mirrors': { oemGroups: [gTahoe], amGroups: [] } };
  const r = run(base([], lazyIdx({ 'side-mirrors': { oem: 1, am: 0 } })), inv, seek, cat());
  check('OEM gate: a 4WD Tahoe is NOT listed as a donor for a 2WD-only part', !r.rows['2006 Chevrolet Tahoe'], JSON.stringify(Object.keys(r.rows)));
  const t2 = r.rows['2007 Chevrolet Tahoe'], t3 = r.rows['2008 Chevrolet Tahoe'], av = r.rows['2007 Chevrolet Avalanche'];
  check('OEM gate: a 2WD-decoded Tahoe is listed, with no "if equipped" line', t2 && !t2.warn.includes('if equipped'), JSON.stringify(t2));
  check('OEM gate: a Tahoe with no drive decode is listed "if equipped", the line names the limit (as the aftermarket gate)',
    t3 && t3.tier === 'likely' && t3.warn.includes("if equipped: this part is checked for 2WD only — this donor's drivetrain isn't confirmed, check the car"),
    JSON.stringify(t3));
  check('OEM gate: the ungated twin app (4WD Avalanche) is unchanged', av && !av.warn.includes('if equipped'), JSON.stringify(av));
  check('OEM gate: the seeker on an ungated app gets no "listed for ... only" header line', !r.head.includes('Some catalog numbers here were found for'), r.head);
  const rs = run(base([], lazyIdx({ 'side-mirrors': { oem: 1, am: 0 } })), inv, { year: 2007, make: 'Chevrolet', model: 'Tahoe' }, cat());
  check('OEM gate: a seeker whose own app is gated is told in the header (escaped)',
    rs.head.includes('Some catalog numbers here were found for a 2007 Tahoe with 2WD only — check yours matches before you pull.'), rs.head);
  // the same group with no gate renders as before: every Tahoe, no gate line
  lazyPreset = { 'side-mirrors': { oemGroups: [oemG({ ...gTahoe, apps: [['Chevrolet', 'Avalanche', 2006, 2008], ['Chevrolet', 'Tahoe', 2006, 2008]] })], amGroups: [] } };
  const r0 = run(base([], lazyIdx({ 'side-mirrors': { oem: 1, am: 0 } })), inv, seek, cat());
  check('OEM group with no gate: unchanged (the 4WD Tahoe listed, no "if equipped" line anywhere)',
    Object.keys(r0.rows).length === 4 && !r0.html.includes('if equipped') && !r0.head.includes('Some catalog numbers here'), JSON.stringify(Object.keys(r0.rows)));
  // a second group whose gate the donor cannot confirm adds its line to the row
  const gYukon = oemG({ id: 'oem:gm:side-mirrors:L:t2', ns: 'gm', label: 'GM catalog', pn: ['22853026'],
    note: 'GM catalog lists #22853026 for both — fits some configurations; verify the number on the part',
    apps: [['Chevrolet', 'Avalanche', 2006, 2008], ['Chevrolet', 'Tahoe', 2006, 2008, null, { cab: 'crew cab' }]] });
  lazyPreset = { 'side-mirrors': { oemGroups: [oemG({ ...gTahoe, apps: [['Chevrolet', 'Avalanche', 2006, 2008], ['Chevrolet', 'Tahoe', 2006, 2008]] }), gYukon], amGroups: [] } };
  const r2 = run(base([], lazyIdx({ 'side-mirrors': { oem: 2, am: 0 } })), inv, seek, cat());
  const m = r2.rows['2007 Chevrolet Tahoe'];
  check('OEM gate: a second, gated group on the same donor adds its number and its "if equipped" line',
    m && m.src.includes('#22853025, #22853026') && m.warn.includes('listed for crew cab only'), JSON.stringify(m));
  // fail closed: a main-file Verified group with a gate the donor cannot confirm renders Likely
  const gv = oemG({ id: 'oem:toyota:side-mirrors:V:9', tier: 'verified', note: 'Toyota catalog lists #87910-06470 for every trim of both',
    apps: [['Toyota', 'Avalon', 2012, 2012, null, { drive: 'fwd' }], ['Toyota', 'Camry', 2007, 2012]] });
  const rv = run(base([], { oemGroups: [gv] }), [car(1, 2012, 'Toyota', 'Avalon', { vin: VIN_2012 })], SEEK, cat());
  check('OEM gate: an unconfirmed limit never renders Verified', rv.rows['2012 Toyota Avalon']?.tier === 'likely', JSON.stringify(rv.rows));
  lazyPreset = null;
}
{
  // body gate through pfRunSearch: coupe-only app; the decode's silhouette rules
  const gB = oemG({ id: 'oem:nissan:side-mirrors:L:b1', ns: 'nissan', label: 'Nissan catalog', pn: ['96301-ZX00A'],
    note: 'Nissan catalog lists #96301-ZX00A for both — fits some configurations; verify the number on the part',
    apps: [['Nissan', 'Altima', 2009, 2011, null, { body: 'coupe' }], ['Nissan', 'Maxima', 2009, 2011]] });
  const inv = [car(1, 2009, 'Nissan', 'Altima'), car(2, 2010, 'Nissan', 'Altima'), car(3, 2011, 'Nissan', 'Altima')];
  const exs = { 1: ['', '', '', '', '', 'sedan'], 2: ['', '', '', '', '', 'coupe'] };
  lazyPreset = { 'side-mirrors': { oemGroups: [gB], amGroups: [] } };
  const r = run(base([], lazyIdx({ 'side-mirrors': { oem: 1, am: 0 } })), inv, { year: 2010, make: 'Nissan', model: 'Maxima' }, cat(), exs);
  check('OEM body gate: a sedan-decoded Altima is not listed for a coupe-only app', !r.rows['2009 Nissan Altima'], JSON.stringify(Object.keys(r.rows)));
  check('OEM body gate: a coupe-decoded Altima is listed plainly', r.rows['2010 Nissan Altima'] && !r.rows['2010 Nissan Altima'].warn.includes('if equipped'));
  check('OEM body gate: an undecoded Altima is listed "if equipped" (body style isn’t confirmed)',
    r.rows['2011 Nissan Altima']?.warn.includes("listed for coupe only — this donor's body style isn't confirmed, check the car"), JSON.stringify(r.rows['2011 Nissan Altima']));
  lazyPreset = null;
}
/* ==== OEM-GATE round3-1119: cab lists, drive_not (All-Mode sibling), the
 * product-page engine column on a hybrid twin ============================== */
{
  const G = (gate, v = {}, ex = null) => ctx.pfOemGate(gate, { model: 'Frontier', ...v }, ex).verdict;
  const ex = (o = {}) => ['', '', o.engine || '', o.trans || '', '', o.body || ''];
  const KC_CC = ['king cab', 'crew cab'];
  check('r3 cab list: a listing naming a listed cab confirms (King Cab, Crew Cab)',
    G({ cab: KC_CC }, { model: 'Frontier King Cab' }) === 'confirm' && G({ cab: KC_CC }, { model: 'Frontier Crew Cab' }) === 'confirm');
  check('r3 cab list: a listing naming a cab outside the list excludes (Regular Cab)',
    G({ cab: KC_CC }, { model: 'Frontier Regular Cab' }) === 'exclude');
  check('r3 cab list: nothing said about the cab -> unconfirmed ("if equipped")', G({ cab: KC_CC }, {}) === 'unconfirmed');
  check('r3 cab list: two cabs named, one listed -> unconfirmed (not confirmed, not excluded)',
    G({ cab: KC_CC }, { model: 'Frontier', vpicTrim: 'Regular Cab, King Cab', vpicTrimQuality: 'usable' }) === 'unconfirmed');
  check('r3 cab string unchanged by the list support: crew cab vs extended cab excludes, crew confirms',
    G({ cab: 'crew cab' }, { model: 'Silverado', vpicSeries: 'Extended Cab' }) === 'exclude' && G({ cab: 'crew cab' }, { model: 'Silverado Crew Cab' }) === 'confirm');
  check('r3 cab list text: "king cab/crew cab"', ctx.pfOemGateText({ cab: KC_CC }) === 'king cab/crew cab');
  const DT4 = '4WD/4-Wheel Drive/4x4', DT2 = '4x2';
  const PT = { drive: '4wd', drive_basis: 'stated', drive_not: 'a4wd' };
  check('r3 drive_not a4wd: a 4WD decode (could be All-Mode) stays unconfirmed', G(PT, { model: 'Pathfinder', vpicDriveType: DT4 }) === 'unconfirmed');
  check('r3 drive_not a4wd: the listing saying 4WD cannot confirm either', G(PT, { model: 'Pathfinder 4WD' }) === 'unconfirmed');
  check('r3 drive_not a4wd: a 4x2 or AWD decode still excludes',
    G(PT, { model: 'Pathfinder', vpicDriveType: DT2 }) === 'exclude' && G(PT, { model: 'Pathfinder', vpicDriveType: 'AWD/All-Wheel Drive' }) === 'exclude');
  check('r3 drive 4wd without drive_not: a 4WD decode confirms (unchanged)', G({ drive: '4wd' }, { vpicDriveType: DT4 }) === 'confirm');
  check('r3 drive_not text: "part-time 4WD"', ctx.pfOemGateText(PT) === 'part-time 4WD');
  const W = ctx.pfOemDonorGate([['Nissan', 'Pathfinder', 2005, 2005, null, PT]], { model: 'Pathfinder', vpicDriveType: DT4 }, null).warn;
  check('r3 drive_not donor line names the part-time limit', W.startsWith('if equipped: this part is listed for part-time 4WD only'), W);
  // the QX60 3.5L cluster: engine gate from the product page; the 2.5L hybrid
  // (decoded 2.5L, listed plain "QX60", nothing saying hybrid) is ruled out
  const Q = { eng: ['3.5L'], fuel: 'gas' };
  check('r3 eng+gas: a QX60 decoded 2.5L with nothing saying hybrid is excluded by the engine',
    G(Q, { model: 'QX60' }, ex({ engine: '2.5L 4-cyl' })) === 'exclude');
  check('r3 eng+gas: a 3.5L QX60 confirms; undecoded unconfirmed',
    G(Q, { model: 'QX60' }, ex({ engine: '3.5L 6-cyl' })) === 'confirm' && G(Q, { model: 'QX60' }, null) === 'unconfirmed');
  // a hybrid-only Camry part (engine column "2.4 L FULL HYBRID"): gas Camrys out
  const H = { eng: ['2.4L'], fuel: 'hybrid' };
  check('r3 eng+hybrid: a 2.5L gas Camry is excluded; a 2.4L "Camry" not named hybrid is unconfirmed; a named hybrid 2.4L confirms',
    G(H, { model: 'Camry' }, ex({ engine: '2.5L 4-cyl' })) === 'exclude'
    && G(H, { model: 'Camry' }, ex({ engine: '2.4L 4-cyl' })) === 'unconfirmed'
    && G(H, { model: 'Camry', vpicTrim: 'Hybrid', vpicTrimQuality: 'usable' }, ex({ engine: '2.4L 4-cyl' })) === 'confirm');
  check('r3 gate text: "2.4L, hybrid"', ctx.pfOemGateText(H) === '2.4L, hybrid');
  // a "gas" gate that also reads the decode (eng_not): QX60 2016 mirror whose
  // engine column lists 3.5L only; the 2.5L hybrid listed as plain "QX60"
  const GN = { fuel: 'gas', eng_not: ['2.5L'] };
  check('r3 eng_not: a QX60 decoded 2.5L with nothing saying hybrid is excluded',
    G(GN, { model: 'QX60' }, ex({ engine: '2.5L 4-cyl' })) === 'exclude');
  check('r3 eng_not: a 3.5L QX60 confirms; an undecoded QX60 still confirms (as the gas gate alone)',
    G(GN, { model: 'QX60' }, ex({ engine: '3.5L 6-cyl' })) === 'confirm' && G(GN, { model: 'QX60' }, null) === 'confirm');
  check('r3 eng_not: a hybrid named in the listing is still excluded', G(GN, { model: 'QX60 Hybrid' }, ex({ engine: '3.5L 6-cyl' })) === 'exclude');
  check('r3 eng_not: the gate text stays "gas"', ctx.pfOemGateText(GN) === 'gas');
  check('r3 gas gate without eng_not unchanged: a 2.5L decode confirms', G({ fuel: 'gas' }, { model: 'QX60' }, ex({ engine: '2.5L 4-cyl' })) === 'confirm');
}
{
  // pfRunSearch with a cab-list app (2002 Frontier power regulator) beside an ungated twin
  const gF = oemG({ id: 'oem:nissan:window-regulator:FL:r3', ns: 'nissan', cat: 'window-regulator', label: 'Nissan catalog', pn: ['80721-3S500'],
    note: 'Nissan catalog lists #80721-3S500 for both — fits some configurations; Frontier: king cab/crew cab only; verify the number on the part',
    apps: [['Nissan', 'Frontier', 2002, 2004, null, { cab: ['king cab', 'crew cab'] }], ['Nissan', 'Xterra', 2002, 2004]] });
  // one Frontier per year: VIN series naming the regular cab, the king cab, nothing
  const inv = [car(1, 2002, 'Nissan', 'Frontier', { vpicSeries: 'Regular Cab' }), car(2, 2003, 'Nissan', 'Frontier', { vpicSeries: 'King Cab' }),
    car(3, 2004, 'Nissan', 'Frontier'), car(4, 2003, 'Nissan', 'Xterra')];
  lazyPreset = { 'window-regulator': { oemGroups: [gF], amGroups: [] } };
  const r = run(base([], lazyIdx({ 'window-regulator': { oem: 1, am: 0 } })), inv, { year: 2003, make: 'Nissan', model: 'Xterra' },
    cat({ id: 'window-regulator', label: 'Window regulator', tokens: ['window regulator'], priceTokens: ['regulator'], rowWarn: '' }));
  check('r3 OEM cab list: a Frontier whose VIN series says Regular Cab is not offered', !r.rows['2002 Nissan Frontier'], JSON.stringify(Object.keys(r.rows)));
  check('r3 OEM cab list: a Frontier whose VIN series says King Cab is a plain row', r.rows['2003 Nissan Frontier'] && !r.rows['2003 Nissan Frontier'].warn.includes('if equipped'),
    JSON.stringify(r.rows['2003 Nissan Frontier']));
  check('r3 OEM cab list: a Frontier with nothing on the cab is "if equipped", the cab list named',
    (r.rows['2004 Nissan Frontier']?.warn || '').includes("listed for king cab/crew cab only — this donor's cab isn't confirmed, check the car"), JSON.stringify(r.rows['2004 Nissan Frontier']));
  check('r3 OEM cab list: the ungated twin is unchanged', r.rows['2003 Nissan Xterra'] && !r.rows['2003 Nissan Xterra'].warn.includes('if equipped'));
  lazyPreset = null;
}

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
