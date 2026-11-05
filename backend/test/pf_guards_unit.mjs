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
 * Run: node backend/test/pf_guards_unit.mjs   (APP_JS=<path> to test another
 * copy of app.js, e.g. the previous commit's, to see the checks fail). */
import fs from 'node:fs';
import vm from 'node:vm';

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
  'pfParseFits', 'pfPartRow', 'pfTierChip', 'pfEngineQuoteVariants', 'pfRunSearch'];
const NEW_FNS = ['pfVinModelYear', 'pfVinValid', 'pfDonorIdentity'];
const NEW_CONSTS = ['PF_VIN_YEAR_CHARS', 'PF_VIN_TRANSLIT', 'PF_VIN_WEIGHTS'];

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
  ctx.pfRunSearch();
  const html = ctx.__els['pf-results'] ? ctx.__els['pf-results'].innerHTML : '';
  const rows = {};
  for (const chunk of html.split('<div class="pf-row-card ').slice(1)) {
    const tier = chunk.startsWith('pf-verified') ? 'verified' : chunk.startsWith('pf-likely') ? 'likely' : '?';
    const name = (chunk.match(/<span class="pf-car-name">([^<]*)<\/span>/) || [])[1] || '';
    const warn = (chunk.match(/<div class="pf-warn">([\s\S]*?)<\/div>/) || [])[1] || '';
    rows[name] = { tier, warn };
  }
  const head = html.split('<div class="pf-row-card ')[0];
  return { html, head, rows };
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

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
