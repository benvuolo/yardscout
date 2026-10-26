/* YardScout — application logic (loading, filtering, rendering, saved list, alerts). */

/* ===== NATIVE SHELL (Capacitor iOS wrapper) =====
 * The App Store build bundles this app's shell (HTML/JS/CSS) but NOT the
 * ~36MB data/ directory — instead the native app fetches live data from the
 * web deployment, so inventory stays fresh without shipping app updates.
 * IS_NATIVE also disables web-only machinery (service worker, native-app
 * promo banner) and keeps Stripe checkout out of the native build entirely (Apple
 * guideline 3.1.1 — digital subscriptions in-app must use StoreKit). */
const IS_NATIVE = !!(window.Capacitor && window.Capacitor.isNativePlatform
  && window.Capacitor.isNativePlatform());
// Android has its own Purchases plugin (Google Play Billing — see
// android/.../PurchasesPlugin.java) with the same JS surface as iOS StoreKit,
// so the IAP flow below is platform-agnostic. Push is too since 1.2: the
// same @capacitor/push-notifications surface yields an APNs token on iOS
// and an FCM token on Android (see the NATIVE section's push init).
const IS_ANDROID = IS_NATIVE && window.Capacitor.getPlatform
  && window.Capacitor.getPlatform() === 'android';
const DATA_BASE = IS_NATIVE ? 'https://yardscout.io/' : '';

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
let fenixPricing = {};  // { "Fenix U-Pull - Elmira": { "ALTERNATOR": {price, core}, ... } } (per yard)
let harrysPricing = {}; // Harry's U-Pull-It: one chain-wide list, keyed by description
let indyPricing = {};   // Indy-U-Pull-It (Indianapolis): one yard-wide list, keyed by description
let upullitnePricing = {}; // U-Pull-It (Des Moines IA / Omaha / Lincoln NE): one chain-wide list
let rupertsPricing = {};   // Rupert's U-Pull-It (Fredericksburg VA): one yard-wide list
let pnsPricing = {};       // Pull-N-Save (UT/AZ/CA): one chain-wide list
let partsgalorePricing = {}; // Parts Galore (Detroit MI): one yard-wide list
let chesterfieldPricing = {}; // Chesterfield Auto Parts (Richmond metro VA): one chain-wide list
let acePricing = {};       // Ace Pick-A-Part (Jacksonville FL): one yard-wide list
let sturtevantPricing = {}; // Sturtevant Auto (Sturtevant WI): one yard-wide list
let nvpapPricing = {};     // Nevada Pic-A-Part (Las Vegas/Henderson NV): one chain-wide list
let barrysPricing = {};    // Barry's U Pull It (Mobile AL): one yard-wide list
let budgetPricing = {};    // Budget U-Pull-It (FL): per-yard lists keyed by location (WG and Bartow differ)
let p195Pricing = {};      // 195 Used Auto Parts (Killeen TX): one yard-wide list
let pnpsaPricing = {};     // San Antonio Pick-N-Pull (Independent, TX): one yard-wide list
let ryansPricing = {};     // Ryan's Pick-a-Part (Detroit MI): one yard-wide list
let usautoPricing = {};    // US Auto Supply (Sterling Heights MI): one yard-wide list
let upasPricing = {};      // U-Pull and Save (Pontiac MI): one yard-wide list

/* utpap = exact "Part Description" from utpap.com/1064Carpricelist.php (Ogden pricelist iframe on ogden-prices page)
 * pyp = exact "Description" from pyp.com per-location PriceList API
 * pap = exact "partname" from Pull-A-Part's per-location pricing API
 * wap = exact "name" from Wrench-A-Part's per-location price-list API (api.wrenchapart.com/price-list)
 * upullr = exact title from upullrparts.com/part-pricing/ (chain-wide flat-rate list)
 * bwg / bba = exact descriptions from Budget U-Pull-It's two FL yard lists
 *   (bwg: budgetupullit.com/used-car-part-prices/ for Winter Garden; bba:
 *   budgetupullit.s3softwaresolutions.com/partspricelist.aspx for Bartow).
 *   TWO columns because the yards publish genuinely different lists — only
 *   421 of ~660 part names are spelled identically across them.
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
  { kw: 'hid headlight',       pnp: 'HEADLIGHT COMP',               tap: 'HEADLIGHT COMPOSITE', utpap: 'HEADLAMP W/ TURN SIG', pyp: 'HEADLIGHT', pap: 'HEADLIGHT LED OR HID LAMP ASSEMBLY W/BALLAST', wap: 'HEADLAMP COMP HID', upullr: 'HEADLAMP HID', bwg: 'HEADLIGHT COMPOSITE', bba: 'HEADLAMP COMPOSITE' },
  { kw: 'led headlight',       pnp: 'HEADLIGHT COMP',               tap: 'HEADLIGHT COMPOSITE', utpap: 'HEADLAMP W/ TURN SIG', pyp: 'HEADLIGHT', pap: 'HEADLIGHT LED OR HID LAMP ASSEMBLY W/BALLAST', wap: 'HEADLAMP COMP HID', upullr: 'HEADLAMP HID', bwg: 'HEADLIGHT COMPOSITE', bba: 'HEADLAMP COMPOSITE' },
  { kw: 'headlight',           pnp: 'HEADLIGHT COMP',               tap: 'HEADLIGHT COMPOSITE', utpap: 'HEADLAMP W/ TURN SIG', pyp: 'HEADLIGHT', pap: 'HEADLIGHT ASSEMBLY (NON-HID/BALLAST)', wap: 'HEADLAMP COMPOSITE NO HID', upullr: 'HEADLAMP', bwg: 'HEADLIGHT COMPOSITE', bba: 'HEADLAMP COMPOSITE' },
  { kw: 'headlamp',            pnp: 'HEADLIGHT COMP',               tap: 'HEADLIGHT COMPOSITE', utpap: 'HEADLAMP W/ TURN SIG', pyp: 'HEADLIGHT', pap: 'HEADLIGHT ASSEMBLY (NON-HID/BALLAST)', wap: 'HEADLAMP COMPOSITE NO HID', upullr: 'HEADLAMP', bwg: 'HEADLIGHT COMPOSITE', bba: 'HEADLAMP COMPOSITE' },
  { kw: 'tail light',          pnp: 'TAILLIGHT ASSY',               tap: 'TAIL LIGHT ASSY ANY', utpap: 'TAIL LIGHT ASSY LRG', pyp: 'TAILLIGHT (QUARTER MOUNTED)', pap: 'TAILLIGHT ASSEMBLY - SINGLE SIDE', wap: 'TAIL LIGHT SMALL', upullr: 'TAILLIGHT', bwg: 'TAIL LIGHT ASSY', bba: 'TAIL LIGHT ASSY' },
  { kw: 'taillight',           pnp: 'TAILLIGHT ASSY',               tap: 'TAIL LIGHT ASSY ANY', utpap: 'TAIL LIGHT ASSY LRG', pyp: 'TAILLIGHT (QUARTER MOUNTED)', pap: 'TAILLIGHT ASSEMBLY - SINGLE SIDE', wap: 'TAIL LIGHT SMALL', upullr: 'TAILLIGHT', bwg: 'TAIL LIGHT ASSY', bba: 'TAIL LIGHT ASSY' },
  { kw: 'fog light',           pnp: 'FOG LAMPS EACH',               tap: 'HEADLIGHT COMP BULB', utpap: 'FOG LIGHT', pyp: 'FRONT LAMP (FOG/PARKING/TURN/MARKER)', pap: 'FOG LAMP (EACH)', wap: 'FOG LIGHT', upullr: 'FOG LIGHT', bwg: 'FOG LIGHT', bba: 'FOG LIGHT' },
  { kw: 'fog lamp',            pnp: 'FOG LAMPS EACH',               tap: 'HEADLIGHT COMP BULB', utpap: 'FOG LIGHT', pyp: 'FRONT LAMP (FOG/PARKING/TURN/MARKER)', pap: 'FOG LAMP (EACH)', wap: 'FOG LIGHT', upullr: 'FOG LIGHT', bwg: 'FOG LIGHT', bba: 'FOG LIGHT' },
  // --- seats ---
  { kw: 'recaro seat',         pnp: 'SEAT-BUCK(EA)W/TRK (PWR)',     tap: 'BUCKET SEAT POWER', utpap: 'BUCKET SEAT ELCTRIC', pyp: 'SEAT WITH AIR BAG FRONT', pap: 'SEAT, BUCKET W/ POWER TRACK (LEATHER)', upullr: 'SEATS BUCKET', bwg: 'SEAT BUCKET', bba: 'BUCKET SEAT' },
  { kw: 'stow-n-go 2nd',      pnp: 'SEAT-BUCK(EA)W/TRK (MAN)',     tap: 'BUCKET SEAT', utpap: 'BUCKET SEAT ELCTRIC', pyp: 'SEAT NO AIR BAG FRONT', pap: 'SEAT, BUCKET W/ MANUAL TRACK', upullr: 'SEATS BUCKET', bwg: 'SEAT BUCKET', bba: 'BUCKET SEAT' },
  { kw: 'stow-n-go 3rd',      pnp: 'SEAT-REAR (EA)',               tap: 'SEAT SECTION', utpap: 'BENCH SEAT ELECTRIC', pyp: 'SEAT REAR', pap: 'SEAT, BENCH/3RD ROW MANUAL TRACK', wap: 'BENCH SEAT', upullr: 'SEATS BENCH', bwg: 'SEATREAR (VAN)', bba: 'SEAT SECTION' },
  { kw: 'stow-n-go',          pnp: 'SEAT-BUCK(EA)W/TRK (MAN)',     tap: 'BUCKET SEAT', utpap: 'BUCKET SEAT ELCTRIC', pyp: 'SEAT NO AIR BAG FRONT', pap: 'SEAT, BUCKET W/ MANUAL TRACK', upullr: 'SEATS BUCKET', bwg: 'SEAT BUCKET', bba: 'BUCKET SEAT' },
  { kw: '3rd row seat',        pnp: 'SEAT-REAR (EA)',               tap: 'SEAT SECTION', utpap: 'BENCH SEAT ELECTRIC', pyp: 'SEAT THIRD ROW', pap: 'SEAT, BENCH/3RD ROW MANUAL TRACK', wap: 'BENCH SEAT', upullr: 'SEATS BENCH', bwg: 'SEATREAR (VAN)', bba: 'SEAT SECTION' },
  { kw: 'rear seat',           pnp: 'SEAT-REAR (EA)',               tap: 'SEAT SECTION', utpap: 'BENCH SEAT ELECTRIC', pyp: 'SEAT REAR', pap: 'SEAT, REAR - EACH SECTION (CLOTH)', wap: 'BENCH SEAT', upullr: 'SEAT RR SECTION-CAR', bwg: 'SEATREAR (CAR) EA', bba: 'SEAT REAR. (CAR) EA' },
  { kw: 'bench seat',          pnp: 'SEAT-BENCH W/TRK',             tap: 'SEAT BENCH', utpap: 'BENCH SEAT ELECTRIC', pyp: 'SEAT REAR', pap: 'SEAT, BENCH W/ POWER TRACK (LEATHER)', wap: 'BENCH SEAT', upullr: 'SEATS BENCH', bwg: 'BENCH SEAT', bba: 'BENCH SEAT' },
  { kw: 'bench',               pnp: 'SEAT-BENCH W/TRK',             tap: 'SEAT BENCH', utpap: 'BENCH SEAT MANUAL', pyp: 'SEAT REAR', pap: 'SEAT, BENCH/3RD ROW MANUAL TRACK', wap: 'BENCH SEAT', upullr: 'SEATS BENCH', bwg: 'BENCH SEAT', bba: 'BENCH SEAT' },
  { kw: 'bucket seat',         pnp: 'SEAT-BUCK(EA)W/TRK (PWR)',     tap: 'BUCKET SEAT POWER', utpap: 'BUCKET SEAT ELCTRIC', pyp: 'SEAT WITH AIR BAG FRONT', pap: 'SEAT, BUCKET W/ POWER TRACK (LEATHER)', upullr: 'SEATS BUCKET', bwg: 'SEAT BUCKET', bba: 'BUCKET SEAT' },
  { kw: 'seat',                pnp: 'SEAT-BUCK(EA)W/TRK (PWR)',     tap: 'BUCKET SEAT POWER', utpap: 'BUCKET SEAT ELCTRIC', pyp: 'SEAT WITH AIR BAG FRONT', pap: 'SEAT, BUCKET W/ POWER TRACK (LEATHER)', upullr: 'SEATS BUCKET', bwg: 'SEAT BUCKET', bba: 'BUCKET SEAT' },
  { kw: 'track',               pnp: 'SEAT TRACK ELEC W/MOTOR (EA)', tap: 'SEAT TRACKSET+MOTOR', utpap: 'SEAT TRACK ELECTRIC', pyp: 'SEAT TRACK, (ELECTRIC)', pap: 'SEAT TRACK, ELECTRIC W/MOTOR', wap: 'SEAT TRACK ELECTRIC', upullr: 'SEAT TRACK-ELECTRIC', bwg: 'SEAT TRK W/O MOTOR', bba: 'SEAT TRACK' },
  // --- gauges / clusters ---
  { kw: 'digital dash',        pnp: 'INSTRUMENT CLUSTER ASSY',      tap: 'INSTRUMENT CLUSTER', utpap: 'INSTRUMENT CLUSTER', pyp: 'INSTRUMENT CLUSTER', pap: 'INSTRUMENT CLUSTER ASSEMBLY', wap: 'INSTRUMENT CLUSTER DIGITAL', upullr: 'INSTRUMENT CLUSTER', bwg: 'INSTRUMENT CLUSTER', bba: 'INSTRUMENT CLUSTER' },
  { kw: 'digital cluster',     pnp: 'INSTRUMENT CLUSTER ASSY',      tap: 'INSTRUMENT CLUSTER', utpap: 'INSTRUMENT CLUSTER', pyp: 'INSTRUMENT CLUSTER', pap: 'INSTRUMENT CLUSTER ASSEMBLY', wap: 'INSTRUMENT CLUSTER DIGITAL', upullr: 'INSTRUMENT CLUSTER', bwg: 'INSTRUMENT CLUSTER', bba: 'INSTRUMENT CLUSTER' },
  { kw: 'cluster',             pnp: 'INSTRUMENT CLUSTER ASSY',      tap: 'INSTRUMENT CLUSTER', utpap: 'INSTRUMENT CLUSTER', pyp: 'INSTRUMENT CLUSTER', pap: 'INSTRUMENT CLUSTER ASSEMBLY', wap: 'INSTRUMENT CLUSTER ANALOG', upullr: 'INSTRUMENT CLUSTER', bwg: 'INSTRUMENT CLUSTER', bba: 'INSTRUMENT CLUSTER' },
  { kw: 'speedometer',         pnp: 'SPEEDOMETER OR TACHOMETER',    tap: 'GAUGE SINGLE', utpap: 'SPEEDOMETER', pyp: 'GAUGES', pap: 'SPEEDOMETER OR TACHOMETER', upullr: 'GAUGE SINGLE', bwg: 'SPEEDOMETER', bba: 'SPEEDOMETER' },
  { kw: 'gauge',               pnp: 'CLOCK/ SMALL GAUGES EACH',     tap: 'GAUGE SINGLE', utpap: 'GAUGE SINGLE', pyp: 'GAUGES', pap: 'CLOCK OR SMALL GAUGES (EACH)', wap: 'GAUGE (SINGLE/MISC)', upullr: 'GAUGE SINGLE', bwg: 'GAUGE SINGLE', bba: 'GAUGE SINGLE' },
  // --- charging / hybrid ---
  { kw: 'alternator',          pnp: 'ALTERNATOR',                   tap: 'ALTERNATOR', utpap: 'ALTERNATOR', pyp: 'ALTERNATOR', pap: 'ALTERNATOR (NON HYBRID)', wap: 'ALTERNATOR', upullr: 'ALTERNATOR', bwg: 'ALTERNATOR', bba: 'ALTERNATOR' },
  // Chains listed only where the exact row name is verified on the yard's
  // published list (spec §6.1) — unverified chains fall through honestly.
  { kw: 'starter',             pnp: 'STARTER',                      tap: 'STARTER', utpap: 'STARTER', upullr: 'STARTER' },
  { kw: 'climate control',     pnp: 'HEATER CONTROL PANEL(MAN)' },
  { kw: 'heater control',      pnp: 'HEATER CONTROL PANEL(MAN)' },
  { kw: 'tow mirror',          utpap: 'TOW MIRRORS' },
  { kw: 'hybrid battery',      pnp: 'BATTERY HYBRID/ELECTRICAL',    pyp: 'BATTERY (HYBRID BATTERY)', pap: 'HYBRID BATTERY ANY', wap: 'HYBRID BATTERY' },
  { kw: 'battery cells',       pnp: 'BATTERY HYBRID/ELECTRICAL',    pyp: 'BATTERY (HYBRID BATTERY)', pap: 'HYBRID BATTERY ANY', wap: 'HYBRID BATTERY' },
  { kw: 'inverter pump',       pnp: 'WATER PUMP',                   tap: 'WATER PUMP (ELECTRIC', utpap: 'WATER PUMP', pyp: 'WATER PUMP', pap: 'AUXILIARY WATER PUMP', wap: 'WATER PUMP', upullr: 'WATER PUMP', bwg: 'WATER PUMP', bba: 'WATER PUMP' },
  { kw: 'dc-dc',               pnp: 'POWER VOLTAGE INVERTER',       pyp: 'DC CONVERTER (HYBRID/ELECTRIC)', pap: 'HYBRID POWER CONTROL MODULE/INVERTER', wap: 'INVERTER HYBRID', upullr: 'HYBRID INVERTER/CONV', bwg: 'HYBRID INVERTER' },
  { kw: 'dc converter',        pnp: 'POWER VOLTAGE INVERTER',       pyp: 'DC CONVERTER (HYBRID/ELECTRIC)', pap: 'HYBRID POWER CONTROL MODULE/INVERTER', wap: 'INVERTER HYBRID', upullr: 'HYBRID INVERTER/CONV', bwg: 'HYBRID INVERTER' },
  { kw: 'inverter',            pnp: 'POWER VOLTAGE INVERTER',       pyp: 'DC CONVERTER (HYBRID/ELECTRIC)', pap: 'HYBRID POWER CONTROL MODULE/INVERTER', wap: 'INVERTER HYBRID', upullr: 'HYBRID INVERTER/CONV', bwg: 'HYBRID INVERTER' },
  // --- audio / infotainment ---
  { kw: 'amplifier',           pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER', wap: 'AMPLIFIER OEM', upullr: 'AMPLIFIER/EQUALIZER', bwg: 'AMPLIFIER' },
  { kw: 'amp',                 pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER', wap: 'AMPLIFIER OEM', upullr: 'AMPLIFIER/EQUALIZER', bwg: 'AMPLIFIER' },
  { kw: 'audio',               pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER', wap: 'AMPLIFIER OEM', upullr: 'AMPLIFIER/EQUALIZER', bwg: 'AMPLIFIER' },
  { kw: 'bose',                pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER', wap: 'AMPLIFIER OEM', upullr: 'AMPLIFIER/EQUALIZER', bwg: 'AMPLIFIER' },
  { kw: 'harman',              pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER', wap: 'AMPLIFIER OEM', upullr: 'AMPLIFIER/EQUALIZER', bwg: 'AMPLIFIER' },
  { kw: 'jbl',                 pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER', wap: 'AMPLIFIER OEM', upullr: 'AMPLIFIER/EQUALIZER', bwg: 'AMPLIFIER' },
  { kw: 'logic7',              pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER', wap: 'AMPLIFIER OEM', upullr: 'AMPLIFIER/EQUALIZER', bwg: 'AMPLIFIER' },
  { kw: 'b&o',                 pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER', wap: 'AMPLIFIER OEM', upullr: 'AMPLIFIER/EQUALIZER', bwg: 'AMPLIFIER' },
  { kw: 'bang & olufsen',      pnp: 'AMPLIFIER / EQ - AUDIO',      tap: 'AMPLIFIER', utpap: 'AMPLIFIER', pyp: 'AMPLIFIER', pap: 'AMPLIFIER', wap: 'AMPLIFIER OEM', upullr: 'AMPLIFIER/EQUALIZER', bwg: 'AMPLIFIER' },
  { kw: 'speaker',             pnp: 'SPEAKER EACH',                 tap: 'SPEAKER', utpap: 'RADIO SPEAKER', pyp: 'RADIO SPEAKER', pap: 'SPEAKER (ANY)', wap: 'SPEAKER 0-5.9"', upullr: 'SPEAKER', bwg: 'SPEAKER OEM EA.', bba: 'SPEAKER OEM EA' },
  { kw: 'heads-up display',    pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY', wap: 'RADIO (SCREEN)', upullr: 'INFORMATION SCREEN', bwg: 'NAV SCREEN', bba: 'RADIO-DVD/SCREEN' },
  { kw: 'touchscreen',         pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY', wap: 'RADIO (SCREEN)', upullr: 'INFORMATION SCREEN', bwg: 'NAV SCREEN', bba: 'RADIO-DVD/SCREEN' },
  { kw: 'infotainment',        pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY', wap: 'RADIO (SCREEN)', upullr: 'INFORMATION SCREEN', bwg: 'NAV SCREEN', bba: 'RADIO-DVD/SCREEN' },
  { kw: 'navigation',          pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'NAVIGATION UNIT', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY', wap: 'RADIO (SCREEN)', upullr: 'NAVIGATION UNIT', bwg: 'NAV SCREEN', bba: 'RADIO-DVD/SCREEN' },
  { kw: 'display',             pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY', wap: 'RADIO (SCREEN)', upullr: 'INFORMATION SCREEN', bwg: 'NAV SCREEN', bba: 'RADIO-DVD/SCREEN' },
  { kw: 'sync',                pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY', wap: 'RADIO (SCREEN)', upullr: 'INFORMATION SCREEN', bwg: 'NAV SCREEN', bba: 'RADIO-DVD/SCREEN' },
  { kw: 'myford',              pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY', wap: 'RADIO (SCREEN)', upullr: 'INFORMATION SCREEN', bwg: 'NAV SCREEN', bba: 'RADIO-DVD/SCREEN' },
  { kw: 'mmi',                 pnp: 'LRG MULTIFUNCT DISPLAY',       tap: 'DIGITAL DISPLAY SCRN', utpap: 'TOUCH SCREEN RDO DBL', pyp: 'GPS TV SCREEN', pap: 'RADIO W/NAV DISPLAY', wap: 'RADIO (SCREEN)', upullr: 'INFORMATION SCREEN', bwg: 'NAV SCREEN', bba: 'RADIO-DVD/SCREEN' },
  { kw: 'head unit',           pnp: 'RADIO',                        tap: 'RADIO', utpap: 'RADIO CD PLAYER', pyp: 'RADIO WITH DISPLAY', pap: 'RADIO  - W/CD OR MEDIA PLAYER', wap: 'RADIO (NO SCREEN)', upullr: 'RADIO', bwg: 'RADIO', bba: 'RADIO-CD/CASS' },
  { kw: 'radio',               pnp: 'RADIO',                        tap: 'RADIO', utpap: 'RADIO CD PLAYER', pyp: 'RADIO WITH DISPLAY', pap: 'RADIO  - W/CD OR MEDIA PLAYER', wap: 'RADIO (NO SCREEN)', upullr: 'RADIO', bwg: 'RADIO', bba: 'RADIO-CD/CASS' },
  { kw: 'entertainment',       pnp: 'LRG MULTIFUNCT DISPLAY',      tap: 'DVD PLAYER', utpap: 'RADIO CD PLAYER', pyp: 'GPS TV SCREEN', pap: 'VIDEO SCREEN', wap: 'HEADREST SCREEN', upullr: 'MEDIA PLAYER', bwg: 'DVD SCREEN', bba: 'RADIO-DVD/SCREEN' },
  { kw: 'dvd',                 pnp: 'LRG MULTIFUNCT DISPLAY',      tap: 'DVD PLAYER', utpap: 'RADIO CD PLAYER', pyp: 'GPS TV SCREEN', pap: 'VIDEO SCREEN', wap: 'HEADREST SCREEN', upullr: 'MEDIA PLAYER', bwg: 'DVD SCREEN', bba: 'RADIO-DVD/SCREEN' },
  // --- body / exterior ---
  { kw: 'front bumper',        pnp: 'BUMPER COMP',                  tap: 'BUMPR CVER W/RENFORC', utpap: 'BUMPER', pyp: 'FRONT BUMPER (STEEL)', pap: 'BUMPER COVER ASSEMBLY', wap: 'BUMPER ASSEMBLY FRONT CAR', upullr: 'BUMPER (BARE)', bwg: 'BUMPER', bba: 'BUMPER' },
  { kw: 'bumper cover',        pnp: 'BUMPER COVER (PLAST/RUBR)',    tap: 'BUMPER COVER', utpap: 'BUMPER', pyp: 'BUMPER COVER, FRONT', pap: 'BUMPER COVER', wap: 'BUMPER COVER FRONT (BARE)', upullr: 'BUMPER (BARE)', bwg: 'BUMPER COVER', bba: 'BUMPER COVER' },
  { kw: 'bumper',              pnp: 'BUMPER COMP',                  tap: 'BUMPR CVER W/RENFORC', utpap: 'BUMPER', pyp: 'FRONT BUMPER (STEEL)', pap: 'BUMPER STEEL OR ALUMINUM', wap: 'BUMPER ASSEMBLY FRONT CAR', upullr: 'BUMPER (BARE)', bwg: 'BUMPER', bba: 'BUMPER' },
  { kw: 'tailgate',            pnp: 'GATE-PU/VAN',                  tap: 'TAIL GATE', utpap: 'TAIL GATE/ ENDGATE', pyp: 'DECKLID/TAILGATE (BARE)', pap: 'TRUCK GATE FOR BED', wap: 'TAILGATE BARE', upullr: 'TAIL GATE-TRUCK', bwg: 'TAILGATE W/O GLASS', bba: 'TAIL GATE' },
  { kw: 'rear gate',           pnp: 'GATE-PU/VAN',                  tap: 'TAIL GATE W/ GLASS', utpap: 'TAILGATE W/ GLASS', pyp: 'DECKLID/TAILGATE (BARE)', pap: 'TRUCK GATE FOR BED', wap: 'TAILGATE BARE', upullr: 'TAIL GATE-SUV/VAN', bwg: 'TAIL GATE W/ GLASS', bba: 'TAIL GATE W/ GLASS' },
  { kw: 'spoiler',             pnp: 'SPOILERS - BOLT ON (EA)',      tap: 'SPOILER', utpap: 'SPOILER', pyp: 'SPOILER REAR', pap: 'SPOILER - BOLT ON (EACH)', wap: 'SPOILER NO LIGHT', upullr: 'SPOILER', bwg: 'SPOILER', bba: 'SPOILER' },
  { kw: 'grille',              pnp: 'GRILL PLASTIC',               tap: 'GRILLE', utpap: 'GRILLE LRG', pyp: 'GRILLE', pap: 'GRILLE PLASTIC (BARE) - ANY', wap: 'GRILLE 19-48"', upullr: 'GRILLE', bwg: 'GRILLE', bba: 'GRILLE' },
  { kw: 'running board',       pnp: 'RUNNING BOARD',               tap: 'RUNNING BOARD (EACH)', utpap: 'RUNNING BOARD', pyp: 'RUNNING BOARD', pap: 'RUNNING BOARD (EACH)', wap: 'RUNNING BOARD NON-ELECTRIC', upullr: 'RUNNING BOARD', bwg: 'RUNNING BOARD', bba: 'RUNNING BOARD' },
  { kw: 'fender flare',        pnp: 'FENDER EXT/FLARE (FRT/RR)',   tap: 'FENDER TRIM/FLARES', utpap: 'FENDER EXTENSION', pyp: 'FENDER EXTENSION', pap: 'FENDER FLARE OR SKIRT', wap: 'FENDER TRIM/ FLARES', upullr: 'FENDER FLARE/TRIM', bwg: 'FENDER FLARE', bba: 'FENDER TRIM/FLARES' },
  { kw: 'mudflap',             pnp: 'MUD FLAP (EA)',               tap: 'MUDFLAP', utpap: 'MUD FLAP', pyp: 'MUD FLAP/SPLASH GUARD', pap: 'MUD FLAP OR SPLASH GUARD', bwg: 'MUD FLAP', bba: 'MUD FLAP' },
  { kw: 'emblem',              pnp: 'EMBLEM',                      tap: 'EMBLEM (ANY)', utpap: 'EMBLEM', pyp: 'EMBLEMS', pap: 'EMBLEM', wap: 'EMBLEM (SMALL)', upullr: 'EMBLEM (ANY)', bwg: 'EMBLEM *AS IS*', bba: 'EMBLEM (ANY)' },
  { kw: 'skid plate',          utpap: 'SKID PLATE',                 pyp: 'SKID PLATE', pap: 'SKID PLATE', wap: 'SKID PLATE', upullr: 'SKID PLATE' },
  { kw: 'mirror',              pnp: 'MIRROR-DOOR OUTSIDE(ELEC)',    tap: 'POWER MIRROR - DOOR', utpap: 'DOOR POWER MIRROR', pyp: 'MIRROR (SIDE VIEW)', pap: 'DOOR MIRROR, OUTSIDE ELECTRIC REMOTE', wap: 'DOOR MIRROR POWER REGULAR', upullr: 'MIRROR-DOOR', bwg: 'POWER MIRROR - DOOR', bba: 'POWER MIRROR - DOOR' },
  // --- racks / rails / towing ---
  { kw: 'roof rack',           pnp: 'LUGGAGE RACK',                tap: 'LUGGAGE RACK', utpap: 'LUGGAGE RACK', pyp: 'ROOF RACK ASSEMBLY', pap: 'LUGGAGE RACK', wap: 'LUGGAGE RACK', upullr: 'LUGGAGE/LADDER RACK', bwg: 'ROOF RACK', bba: 'ROOF RACK' },
  { kw: 'roof rail',           pnp: 'LUGGAGE RACK',                tap: 'LUGGAGE RACK', utpap: 'LUGGAGE RACK', pyp: 'ROOF RACK RAIL/ CROSS BAR (EACH)', pap: 'LUGGAGE RACK', wap: 'LUGGAGE RACK', upullr: 'LUGGAGE/LADDER RACK', bwg: 'ROOF RACK', bba: 'ROOF RACK' },
  { kw: 'crossbar',            pnp: 'LUGGAGE RACK',                tap: 'CARGO RACK', utpap: 'LUGGAGE RACK', pyp: 'ROOF RACK RAIL/ CROSS BAR (EACH)', pap: 'LUGGAGE RACK CROSS BAR', upullr: 'LUGGAGE RACH CROSS BAR', bwg: 'LUGGAGE RACK', bba: 'LUGGAGE RACK' },
  { kw: 'cargo rail',          tap: 'CARGO RACK',                   pap: 'TRUCK BED RAIL (EACH)' },
  { kw: 'cargo cover',         pyp: 'CARGO COVER',                  pap: 'CARGO COVER, SHADE TYPE', wap: 'CARGO COVER RETRACTABLE', upullr: 'CARGO COVER', bwg: 'CARGO COVER', bba: 'CARGO COVER' },
  { kw: 'spare tire cover',    pnp: 'SPARE TIRE COVER',             tap: 'SPARE TIRE COVER', utpap: 'SPARE TIRE COVER MET', pap: 'SPARE TIRE COVER', wap: 'FLOOR MAT/ SPARE TIRE COVER', upullr: 'SPARE TIRE COVER', bwg: 'SPARE CAS  COVERTRUN', bba: 'SPARE TIRE COVER' },
  { kw: 'hitch',               pnp: 'TRAILER HITCH W/O BALL',       tap: 'TRAILER HITCH', utpap: 'TRAILERHITCH RECEIVE', pyp: 'TRAILER HITCH', pap: 'TRAILER HITCH RECEIVER', wap: 'TRAILERHITCH RECEIVER', upullr: 'TRAILER HITCH', bwg: 'TRAILER HITCH FRAME', bba: 'TRAILER HITCH FRAME' },
  // --- glass / roofs ---
  { kw: 'panoramic sunroof',   pnp: 'SUN ROOF ASSY',               tap: 'SUNROOF ASSY+MOTOR', utpap: 'SUNROOF/T-TOP', pyp: 'ROOF GLASS PANORAMIC (FULL GLASS ROOF ASSEMBLY)', pap: 'TOP - SUNROOF FRAME WITH GLASS', wap: 'SUNROOF ASSEMBLY ELECTRIC', upullr: 'SUNROOF ASSEMBLY', bwg: 'SUN ROOF ELECTRIC CO', bba: 'SUN ROOF ELECTRIC CO' },
  { kw: 'panoramic',           pnp: 'SUN ROOF ASSY',               tap: 'SUNROOF ASSY+MOTOR', utpap: 'SUNROOF ASSY', pyp: 'ROOF GLASS PANORAMIC (FULL GLASS ROOF ASSEMBLY)', pap: 'TOP - SUNROOF FRAME WITH GLASS', wap: 'SUNROOF ASSEMBLY ELECTRIC', upullr: 'SUNROOF ASSEMBLY', bwg: 'SUN ROOF ELECTRIC CO', bba: 'SUN ROOF ELECTRIC CO' },
  { kw: 'sunroof motor',       pnp: 'SUN ROOF MOTOR',               pap: 'TOP MOTOR, SUNROOF' },
  { kw: 'panoramic roof motor', pnp: 'SUN ROOF MOTOR',              pap: 'TOP MOTOR, SUNROOF' },
  { kw: 'sunroof glass',       pyp: 'ROOF GLASS (SUN ROOF)',        pap: 'TOP - SUNROOF GLASS ONLY', wap: 'SUNROOF GLASS ONLY', upullr: 'SUNROOF GLASS ONLY', bwg: 'SUN ROOF GLASS', bba: 'SUN ROOF GLASS' },
  { kw: 'sunroof',             pnp: 'SUN ROOF ASSY',               tap: 'SUN ROOF ASSEMBLY', utpap: 'SUNROOF/T-TOP', pyp: 'ROOF GLASS (SUN ROOF)', pap: 'SUNROOF/COVER/SHADE ASSEMBLY W/MOTOR', wap: 'SUNROOF ASSEMBLY ELECTRIC', upullr: 'SUNROOF ASSEMBLY', bwg: 'SUN ROOF ELECTRIC CO', bba: 'SUN ROOF ELECTRIC CO' },
  { kw: 'targa',               pnp: 'T-TOP (EACH)',                 tap: 'SUNROOF/T-TOP', utpap: 'SUNROOF/T-TOP', pyp: 'ROOF GLASS (T-TOP)', pap: 'TOP, T-TOP (EACH)', upullr: 'T-TOPS', bwg: 'T. TOPS (EACH)', bba: 'T. TOPS (EACH)' },
  { kw: 't-top',               pnp: 'T-TOP (EACH)',                 tap: 'SUNROOF/T-TOP', utpap: 'SUNROOF/T-TOP', pyp: 'ROOF GLASS (T-TOP)', pap: 'TOP, T-TOP (EACH)', upullr: 'T-TOPS', bwg: 'T. TOPS (EACH)', bba: 'T. TOPS (EACH)' },
  { kw: 'hardtop motor',       pnp: 'TOP-CONVERTIBLE MOTOR',        utpap: 'CONVERTIBLE TOP MOTO', pyp: 'CONVERTIBLE TOP MOTOR', pap: 'TOP - CONVERTIBLE TOP MOTOR', wap: 'CONVERTIBLE TOP MOTOR', upullr: 'CONVERTIBLE TOP OR SLIDING DOOR MOTOR', bwg: 'CONV TOP PUMP', bba: 'CONV TOP PUMP' },
  { kw: 'roof motor',          pnp: 'TOP-CONVERTIBLE MOTOR',        utpap: 'CONVERTIBLE TOP MOTO', pyp: 'CONVERTIBLE TOP MOTOR', pap: 'TOP - CONVERTIBLE TOP MOTOR', wap: 'CONVERTIBLE TOP MOTOR', upullr: 'CONVERTIBLE TOP OR SLIDING DOOR MOTOR', bwg: 'CONV TOP PUMP', bba: 'CONV TOP PUMP' },
  { kw: 'convertible top motor', pnp: 'TOP-CONVERTIBLE MOTOR',      utpap: 'CONVERTIBLE TOP MOTO', pyp: 'CONVERTIBLE TOP MOTOR', pap: 'TOP - CONVERTIBLE TOP MOTOR', wap: 'CONVERTIBLE TOP MOTOR', upullr: 'CONVERTIBLE TOP OR SLIDING DOOR MOTOR', bwg: 'CONV TOP PUMP', bba: 'CONV TOP PUMP' },
  { kw: 'convertible top',     pnp: 'TOP-CONVERTIBLE (NO RAMS)',    tap: 'CONVERTIBLE TOP', utpap: 'CONVERTIBLE TOP CANV', pap: 'TOP - CONVERTIBLE (NO RAMS)', wap: 'CONVERTIBLE TOP ASSEMBLY', upullr: 'CONVERTIBLE TOP', bwg: 'CONVERTIBLE TOP CANV', bba: 'CONVERTIBLE TOP' },
  { kw: 'soft top',            pnp: 'TOP-CONVERTIBLE (NO RAMS)',    tap: 'CONVERTIBLE TOP', utpap: 'CONVERTIBLE TOP CANV', pap: 'TOP - CONVERTIBLE (NO RAMS)', wap: 'CONVERTIBLE TOP CLOTH ONLY', upullr: 'CONVERTIBLE TOP', bwg: 'CONVERTIBLE TOP CANV', bba: 'CONVERTIBLE TOP' },
  { kw: 'hardtop',             pap: 'HARDTOP W/O DOORS' },
  { kw: 'barn door',           pnp: 'GLASS DOOR (BARE)',            tap: 'DOOR GLASS', utpap: 'DOOR GLASS', pyp: 'GLASS DOOR REAR', pap: 'DOOR GLASS (BARE)', wap: 'DOOR GLASS TRUCK', upullr: 'BACK GLASS', bwg: 'DOOR GLASS', bba: 'DOOR GLASS' },
  { kw: 'dutch door',          pnp: 'GLASS DOOR (BARE)',            tap: 'DOOR GLASS', utpap: 'DOOR GLASS', pyp: 'GLASS DOOR REAR', pap: 'DOOR GLASS (BARE)', wap: 'DOOR GLASS TRUCK', upullr: 'BACK GLASS', bwg: 'DOOR GLASS', bba: 'DOOR GLASS' },
  { kw: 'midgate',             pnp: 'GLASS BACK (ONLY)',            tap: 'BACK GLASS (SOLID)', utpap: 'BACK GLASS', pyp: 'GLASS BACK', wap: 'BACK GLASS TRUCK', upullr: 'BACK GLASS', bwg: 'BACK GLASS', bba: 'BACK GLASS' },
  { kw: 'liftgate glass',      pnp: 'GLASS BACK (ONLY)',            tap: 'GLASS HATCH', utpap: 'GLASS HATCH', pyp: 'GLASS BACK', wap: 'BACK GLASS HATCH', upullr: 'BACK GLASS', bwg: 'GLASS HATCH', bba: 'GLASS HATCH' },
  { kw: 'hatch glass',         pnp: 'GLASS BACK (ONLY)',            tap: 'GLASS HATCH', utpap: 'GLASS HATCH', pyp: 'GLASS BACK', wap: 'BACK GLASS HATCH', upullr: 'BACK GLASS', bwg: 'GLASS HATCH', bba: 'GLASS HATCH' },
  // --- doors / windows ---
  { kw: 'sliding door motor',  pnp: 'DOOR/GATE MOTOR',             tap: 'SIDE DOOR SLIDE MTR', utpap: 'ELECTRIC MODULE', pyp: 'SLIDING DOOR MOTOR', pap: 'DOOR/HATCH MOTOR, (SLIDING VAN/SUV)', upullr: 'SLIDING DOOR MOTOR', bwg: 'ELEC MOTOR MISC', bba: 'ELEC MOTOR MISC' },
  { kw: 'door motor',          pnp: 'DOOR/GATE MOTOR',             tap: 'SIDE DOOR SLIDE MTR', utpap: 'ELECTRIC MODULE', pyp: 'SLIDING DOOR MOTOR', pap: 'DOOR/HATCH MOTOR, (SLIDING VAN/SUV)', upullr: 'SLIDING DOOR MOTOR', bwg: 'ELEC MOTOR MISC', bba: 'ELEC MOTOR MISC' },
  { kw: 'liftgate',            pnp: 'DOOR/GATE MOTOR',             tap: 'SIDE DOOR SLIDE MTR', utpap: 'TAIL GATE/ ENDGATE', pyp: 'DECKLID/TAILGATE (BARE)', pap: 'DOOR/HATCH MOTOR, (SLIDING VAN/SUV)', bwg: 'HATCH ASSM.', bba: 'HATCH NO GLASS' },
  { kw: 'window regulator',    pnp: 'WINDOW REGULATOR W/MOTOR',   tap: 'WINDOW REG W/MOTOR', utpap: 'WINDOW REGULATOR', pyp: 'WINDOW REGULATOR FRONT (ELECTRIC)', pap: 'WINDOW REGULATOR W/MOTOR', wap: 'WINDOW REGULATOR W/ MOTOR', upullr: 'WINDOW REGULATOR POWER', bwg: 'WINDOW REG W/ MOTOR', bba: 'REG AND MOTOR' },
  { kw: 'master switch',       pnp: 'SWITCH POWER WINDOW(MULTI)',   tap: 'SWITCH COMBO', utpap: 'WINDOW SWITCH MASTER', pyp: 'DOOR ELECTRICAL SWITCH (MULTI)', pap: 'SWITCH, POWER WINDOW (MULTIPLE) ONLY', wap: 'SWITCH, MASTER WINDOW', upullr: 'SWITCH-MULTI', bwg: 'WINDOW MASTER SW.', bba: 'WINDOW MASTER SWITCH' },
  { kw: 'window switch',       pnp: 'SWITCH POWER WINDOW(MULTI)',   tap: 'SWITCH COMBO', utpap: 'WINDOW SWITCH MASTER', pyp: 'DOOR ELECTRICAL SWITCH (MULTI)', pap: 'SWITCH, POWER WINDOW (MULTIPLE) ONLY', wap: 'SWITCH, MASTER WINDOW', upullr: 'SWITCH-MULTI', bwg: 'WINDOW MASTER SW.', bba: 'WINDOW MASTER SWITCH' },
  { kw: 'door panel',          pnp: 'DOOR TRIM PANEL',              tap: 'INT DOOR PANEL', utpap: 'INTERIOR DOOR PANEL', pyp: 'DOOR PANEL FRONT (BARE)', pap: 'INTERIOR TRIM PANEL (OVER 8IN LONG)', wap: 'TRIM LARGE 18"+', upullr: 'DOOR TRIM PANEL', bwg: 'DOOR PANEL W/O SWITC', bba: 'DOOR PANEL W/O SWITC' },
  // --- interior ---
  { kw: 'wood trim',           utpap: 'TRIM PANNEL',                pap: 'INTERIOR TRIM PANEL (OVER 8IN LONG)', wap: 'TRIM MEDIUM 9-18"', bwg: 'TRIM PANEL MEDIUM', bba: 'TRIM PANEL MEDIUM' },
  { kw: 'interior trim',       utpap: 'TRIM PANNEL',                pap: 'INTERIOR TRIM PANEL (OVER 8IN LONG)', wap: 'TRIM MEDIUM 9-18"', bwg: 'TRIM PANEL MEDIUM', bba: 'TRIM PANEL MEDIUM' },
  // ambiguous grab-bag names — pinned unmapped so shorter generic keywords
  // ('shifter', 'targa', ...) can't mis-price them
  { kw: 'chrome accessories' },
  { kw: 'whole car' },
  { kw: 'dash pad',            pnp: 'DASH PAD',                    tap: 'DASH PAD', utpap: 'DASH PAD', pyp: 'DASH PAD', pap: 'DASH PAD (OVER 24in LENGTH)', wap: 'DASH PAD', upullr: 'DASH PANEL OR PAD', bwg: 'DASH PAD', bba: 'DASH PAD' },
  { kw: 'console lid',         pnp: 'CONSOLE COVER',               tap: 'CONSOLE LID', utpap: 'CONSOLE LID', pyp: 'CENTER CONSOLE', pap: 'CONSOLE LID', wap: 'CONSOLE LID', upullr: 'CONSOLE LID', bwg: 'CONSOLE LID', bba: 'CONSOLE LID' },
  { kw: 'console',             pnp: 'CONSOLE',                     tap: 'CONSOLE (ANY)', utpap: 'CONSOLE BARE', pyp: 'CENTER CONSOLE', pap: 'CONSOLE (OVER 16in LENGTH)', wap: 'CONSOLE LG 17"+', upullr: 'CONSOLE (ANY)', bwg: 'CONSOLE', bba: 'CONSOLE (ANY)' },
  // --- drivetrain / shifters ---
  { kw: 'shift assembly',      pnp: 'TRANS FLOOR SHIFTER',          tap: 'SHIFTER LEVER ASSY', utpap: 'SHIFTER ARM MANUAL', pyp: 'SHIFT ASSEMBLY', pap: 'TRANSMISSION FLOOR SHIFTER', wap: 'SHIFTER LEVER ASSY', upullr: 'SHIFTER', bwg: 'SHIFTER ASSY', bba: 'SHIFTER ASSY' },
  { kw: 'shifter',             pnp: 'TRANS FLOOR SHIFTER',          tap: 'SHIFTER LEVER ASSY', utpap: 'SHIFTER ARM MANUAL', pyp: 'SHIFT ASSEMBLY', pap: 'TRANSMISSION FLOOR SHIFTER', wap: 'SHIFTER LEVER ASSY', upullr: 'SHIFTER', bwg: 'SHIFTER ASSY', bba: 'SHIFTER ASSY' },
  { kw: 'pedal',               pnp: 'PEDAL BRAKE/CLUTCH ASSY',      tap: 'PEDAL ASSY', utpap: 'CLUTCH PEDAL ASSY', pyp: 'BRAKE/CLUTCH PEDAL BOX', pap: 'PEDAL, BRAKE & CLUTCH ASSEMBLY', wap: 'PEDAL ASSEMBLY', upullr: 'PEDAL(ANY)', bwg: 'PEDAL ASSEMBLY', bba: 'PEDAL (EACH)' },
  { kw: 'transfer case shift motor', pnp: 'TRANSFER CASE MOTOR',    tap: 'TRANSFER CASE MOTOR', utpap: 'TRANSFERCAS ACTUATOR', pyp: 'TRANSFER CASE MOTOR', pap: '4 WHEEL DRIVE ACTUATOR VACUUM OR ELECTRIC', wap: 'TRANSFER CASE MOTOR', upullr: 'TRANSFER CASE SHIFT MOTOR' },
  { kw: 'transfer case motor', pnp: 'TRANSFER CASE MOTOR',         tap: 'TRANSFER CASE MOTOR', utpap: 'TRANSFERCAS ACTUATOR', pyp: 'TRANSFER CASE MOTOR', pap: '4 WHEEL DRIVE ACTUATOR VACUUM OR ELECTRIC', wap: 'TRANSFER CASE MOTOR', upullr: 'TRANSFER CASE SHIFT MOTOR' },
  { kw: 'awd transfer case',   pnp: 'TRANSFER CASE 4X4',           tap: 'TRANSFER CASE (4X4)', utpap: 'TRANSFER CASE ( 4X4)', pyp: 'TRANSFER CASE', pap: 'TRANSFER CASE, 4X4', wap: 'TRANSFER CASE ASSEMBLY', upullr: 'TRANSFER CASE ( 4X4)', bwg: 'TRANSFER CASE', bba: 'TRANSFER CASE ( 4X4)' },
  { kw: '4wd selector',        pnp: 'SWITCH MISC',                  tap: 'SWITCH SINGLE', utpap: 'ELECTRIC SWITCH', pyp: 'TRANSFER CASE SWITCH (4X4)', pap: 'SWITCH, MISC.', wap: 'SWITCH, SINGLE', upullr: 'SWITCH SINGLE', bwg: 'SWITCH SINGLE', bba: 'SWITCH SINGLE' },
  { kw: 'differential controller', pnp: 'CONTROL MODULE',           tap: 'MODULE', utpap: 'COMPUTER', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL', wap: 'MODULE, BODY CONTROL', upullr: 'ELECT MODULE OTHER THAN ECM', bwg: 'OTHER-COMPUTER SMALL', bba: 'ELEC MODULE MED' },
  { kw: 'diff',                pnp: 'REAR END CARRIER ASSEMBLY',    tap: 'DIFFERENTIAL', utpap: 'AXLE CARRIER', pyp: 'CARRIER ASSEMBLY', pap: 'DIFFERENTIAL (FRONT, REAR OR 3RD MEMBER DROP-OUT)', wap: 'DIFFERENTIAL CARRIER W/ GEARS', upullr: 'DIFFERENTIAL CARRIER', bwg: 'REAR END CHUNK', bba: 'AXLE CARRIER' },
  { kw: 'plenum',              pnp: 'MANIFOLD INTAKE',              tap: 'INTAKE PLENUM', utpap: 'INTAKE MANIFOLD', pyp: 'INTAKE MANIFOLD', pap: 'INTAKE PLENUM, UPPER', wap: 'INTAKE MANIFOLD OEM', upullr: 'INTAKE/EXH MANIFOLD', bwg: 'INTAKE MANIFOLD', bba: 'INTAKE MANIFOLD' },
  { kw: 'intake',              pnp: 'MANIFOLD INTAKE',              tap: 'INTAKE MANIFOLD', utpap: 'INTAKE MANIFOLD', pyp: 'INTAKE MANIFOLD', wap: 'INTAKE MANIFOLD OEM', upullr: 'INTAKE/EXH MANIFOLD', bwg: 'INTAKE MANIFOLD', bba: 'INTAKE MANIFOLD' },
  { kw: 'intercooler',         pnp: 'INTERCOOLER',                  tap: 'TURBO INTERCOOLER', utpap: 'TURBO INNER COOLER', pyp: 'INTERCOOLER', pap: 'TURBO INTERCOOLER', wap: 'INTERCOOLER', upullr: 'TURBO INTER COOLER', bwg: 'INTERCOOLER', bba: 'INTERCOOLER' },
  // --- suspension ---
  { kw: 'suspension compressor', pnp: "AIR COMPRESSOR(AIR SUSP'N)", utpap: 'AIR SHOCK PUMP', pyp: 'SUSPENSION COMPRESSOR/PUMP', pap: 'AIR COMPRESSOR (AIR SUSPENSION)', upullr: 'AIR RIDE PUMP', bwg: 'AIR RIDE PUMP', bba: 'AIR RIDE PUMP' },
  { kw: 'air suspension',      pnp: "AIR COMPRESSOR(AIR SUSP'N)", utpap: 'AIR SHOCK PUMP', pyp: 'SUSPENSION COMPRESSOR/PUMP', pap: 'AIR COMPRESSOR (AIR SUSPENSION)', upullr: 'AIR RIDE PUMP', bwg: 'AIR RIDE PUMP', bba: 'AIR RIDE PUMP' },
  { kw: 'air spring',          pyp: 'STRUT (AIR)',                  pap: 'SHOCK ABSORBER AIR OR AIRBAG TYPE', wap: 'SUSPENSION AIR BAG', upullr: 'STRUT-AIR BAG TYPE', bwg: 'AIR BAG SUSPENSION', bba: 'SHOCK (AIR)' },
  { kw: 'hood shock',          pnp: 'HATCH OR HOOD SHOCK',          tap: 'HOOD/TRUNK SHOCKS', utpap: 'SHOCK HOOD/LID', pap: 'HATCH OR HOOD SHOCK (MANUAL)', wap: 'HOOD SHOCK', upullr: 'GAS STRUTS', bwg: 'HOOD/HATCH STRUT', bba: 'HOOD/HATCH STRUT' },
  { kw: 'hatch shock',         pnp: 'HATCH OR HOOD SHOCK',          tap: 'HOOD/TRUNK SHOCKS', utpap: 'SHOCK HOOD/LID', pap: 'HATCH OR HOOD SHOCK (MANUAL)', wap: 'HATCH SHOCK', upullr: 'GAS STRUTS', bwg: 'HOOD/HATCH STRUT', bba: 'HOOD/HATCH STRUT' },
  { kw: 'air shock',           pnp: 'SHOCK ABSORBER',               tap: 'SHOCK', utpap: 'SHOCK', pyp: 'SHOCK ABSORBER', pap: 'SHOCK ABSORBER AIR OR AIRBAG TYPE', wap: 'AIR SHOCK ONLY', upullr: 'SHOCK', bwg: 'SHOCK (AIR)', bba: 'SHOCK (AIR)' },
  { kw: 'autoride',            pnp: 'SHOCK ABSORBER',               tap: 'SHOCK', utpap: 'SHOCK', pyp: 'SHOCK ABSORBER', pap: 'SHOCK ABSORBER AIR OR AIRBAG TYPE', wap: 'AIR SHOCK ONLY', upullr: 'SHOCK', bwg: 'SHOCK (AIR)', bba: 'SHOCK (AIR)' },
  { kw: 'shock',               pnp: 'SHOCK ABSORBER',               tap: 'SHOCK', utpap: 'SHOCK', pyp: 'SHOCK ABSORBER', pap: 'SHOCK ABSORBER (REGULAR)', wap: 'SHOCK ABSORBER NO SPRING', upullr: 'SHOCK', bwg: 'SHOCK', bba: 'SHOCK' },
  // --- wheels ---
  { kw: 'wheels (set',         pnp: 'WHEEL & TIRE CUSTOM SET 4',    utpap: 'PREMI WHEEL/TIRE SET', pyp: 'TIRE/WHEEL SET', bwg: 'CASING & RIM SET OF' },
  // --- brakes ---
  { kw: 'brembo',              pnp: 'BRAKE CALIPER',                tap: 'BRAKE CALIPER', utpap: 'BRAKE CALIPER 2-4 PI', pyp: 'BRAKE CALIPER', pap: 'BRAKE CALIPER', wap: 'CALIPER 4 PISTON', upullr: 'BRAKE CALIPER', bwg: 'BRAKE CALIPER', bba: 'BRAKE CALIPER' },
  { kw: 'brake caliper',       pnp: 'BRAKE CALIPER',                tap: 'BRAKE CALIPER', utpap: 'BRAKE CALIPER 2-4 PI', pyp: 'BRAKE CALIPER', pap: 'BRAKE CALIPER', wap: 'CALIPER 1 PISTON', upullr: 'BRAKE CALIPER', bwg: 'BRAKE CALIPER', bba: 'BRAKE CALIPER' },
  { kw: 'caliper',             pnp: 'BRAKE CALIPER',                tap: 'BRAKE CALIPER', utpap: 'BRAKE CALIPER 2-4 PI', pyp: 'BRAKE CALIPER', pap: 'BRAKE CALIPER', wap: 'CALIPER 1 PISTON', upullr: 'BRAKE CALIPER', bwg: 'BRAKE CALIPER', bba: 'BRAKE CALIPER' },
  // --- steering ---
  { kw: 'steering wheel',      pnp: 'STEERING WHEEL',               tap: 'STEERNG WHL W/SWITCH', utpap: 'STEERING WHEEL', pyp: 'STEERING WHEEL', pap: 'STEERING WHEEL', wap: 'STEERING WHEEL NO AIR BAG', upullr: 'STEERING WHEEL', bwg: 'STEERING WHEEL W/O', bba: 'STEERING WHEEL W/O' },
  // --- modules / electronics ---
  { kw: 'sliding door control', pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'COMPUTER', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL', wap: 'MODULE, BODY CONTROL', upullr: 'ELECT MODULE OTHER THAN ECM', bwg: 'OTHER-COMPUTER SMALL', bba: 'ELEC MODULE MED' },
  { kw: 'control module',      pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'COMPUTER', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL', wap: 'MODULE, BODY CONTROL', upullr: 'ELECT MODULE OTHER THAN ECM', bwg: 'OTHER-COMPUTER SMALL', bba: 'ELEC MODULE MED' },
  { kw: 'radar',               pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'COMPUTER', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL', wap: 'MODULE, BODY CONTROL', upullr: 'ELECT MODULE OTHER THAN ECM', bwg: 'OTHER-COMPUTER SMALL', bba: 'ELEC MODULE MED' },
  { kw: 'camera',              pnp: 'CONTROL MODULE',              tap: 'REVERSE CAMERA', utpap: 'COMPUTER', pyp: 'SENSOR CAMERAS', pap: 'CAMERA, ON BOARD OR BACK UP', wap: 'CAMERA', upullr: 'BACKUP CAMERA' },
  { kw: 'module',              pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'COMPUTER', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL', wap: 'MODULE, BODY CONTROL', upullr: 'ELECT MODULE OTHER THAN ECM', bwg: 'OTHER-COMPUTER SMALL', bba: 'ELEC MODULE MED' },
  { kw: 'wireless charging',   pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'ELECTRIC MODULE', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL', wap: 'MODULE, BODY CONTROL', upullr: 'ELECT MODULE OTHER THAN ECM', bwg: 'OTHER-COMPUTER SMALL', bba: 'ELEC MODULE MED' },
  { kw: 'charging pad',        pnp: 'CONTROL MODULE',              tap: 'MODULE', utpap: 'ELECTRIC MODULE', pyp: 'CHASSIS CONTROL MODULE', pap: 'MODULE - BODY / CHASSIS / GATEWAY/ FUEL', wap: 'MODULE, BODY CONTROL', upullr: 'ELECT MODULE OTHER THAN ECM', bwg: 'OTHER-COMPUTER SMALL', bba: 'ELEC MODULE MED' },
  // --- misc ---
  { kw: 'cable',               tap: 'CABLE (ANY)',                  utpap: 'SHIFTER CABLE', pyp: 'CABLE', pap: 'CABLE - BRAKE/CLUTCH/SHIFTER/THROTTLE/RELEASE', wap: 'CABLE (MISCELLANEOUS)', upullr: 'MISC CABLES', bwg: 'CABLE', bba: 'CABLE (ANY)' },
  { kw: 'wiper motor',         pnp: 'WINDSHIELD WIPER MOTOR',      tap: 'WIPER MOTOR', utpap: 'WIPER MOTOR', pyp: 'ELECTRIC WIPER MOTOR, WINDSHIELD', pap: 'WINDSHIELD WIPER MOTOR', wap: 'WIPER MOTOR', upullr: 'ELECTRIC MOTORS', bwg: 'WIPER MOTOR', bba: 'WIPER MOTOR' },
  { kw: 'actuator',            pnp: 'ACUATOR (4X4)',               tap: 'ACTUATOR', utpap: 'TRANSFERCAS ACTUATOR', pyp: 'ACTUATOR', pap: 'ACTUATOR', wap: '4X4 ACTUATOR' },
  { kw: 'switch',              pnp: 'SWITCH MISC',                  tap: 'SWITCH SINGLE', utpap: 'ELECTRIC SWITCH', pap: 'SWITCH, MISC.', wap: 'SWITCH, SINGLE', upullr: 'SWITCH SINGLE', bwg: 'SWITCH SINGLE', bba: 'SWITCH SINGLE' },
];

/* Strict provenance: each chain's price list applies ONLY to that chain's own
 * yards, and there is no estimated fallback. Returns {cost:null, source:'none'}
 * whenever the yard's real price list doesn't cover the part — callers then
 * show "check yard price list" and compute value-only ranges. */
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
  if (loc.startsWith('budget u-pull-it')) {
    // Two different published lists behind one brand: column picked by yard.
    const yard = budgetPricing[location];
    const key = loc.includes('winter garden') ? bestMatch.bwg : bestMatch.bba;
    const e = yard && key ? yard[key] : null;
    return e ? { cost: parseFloat(e.price), source: 'budget', yardName: key } : none;
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
  // Factory specs decoded from the VIN (trim, drivetrain, engine) are a Pro
  // feature; the mismatch warning stays free — it's a data-honesty flag, not
  // a value signal.
  let vpic = '';
  const specBits = [];
  const vt = v.vpicTrim != null ? String(v.vpicTrim).trim() : '';
  if (vt && (v.vpicTrimQuality === 'usable' || v.vpicDecodeWell === true)) {
    specBits.push(`trim: ${escapeHtml(vt)}`);
  } else if (v.vpicSeries) {
    specBits.push(`series: ${escapeHtml(String(v.vpicSeries).trim())}`);
  }
  if (v.vpicDriveType) {
    const d = String(v.vpicDriveType);
    const short = /4wd|4x4|four/i.test(d) ? '4WD' : /awd|all/i.test(d) ? 'AWD'
      : /rwd|rear/i.test(d) ? 'RWD' : /fwd|front/i.test(d) ? 'FWD' : '';
    if (short) specBits.push(short);
  }
  // (Engine deliberately NOT included here — it already renders on the
  // card's spec line below; repeating it read as a bug.)
  if (specBits.length) {
    vpic = isPro()
      ? ` <span class="meta-note" title="Factory build — trim/drivetrain decoded from the VIN via NHTSA VPIC, engine from the VIN or the yard\u2019s own feed — so you know what to look for before walking over">${specBits.join(' &middot; ')} (factory spec)</span>`
      : '';   // free cards carry one Pro link (the savings line) — not a second one per VIN
  }
  let mismatch = '';
  if (v.vpicMismatch) {
    mismatch = ` <span class="meta-warn" title="The VIN\u2019s factory decode disagrees with the yard listing — the lot sign may be mislabeled. The VIN is used for matching; verify at the yard.">${escapeHtml(v.vpicMismatch)}</span>`;
  }
  // Separator lives inside the chunk so it can't wrap onto a line by itself.
  return ` <span class="vin-chunk">&middot;&nbsp;VIN <span class="mono-vin">${escapeHtml(show)}</span>${copyBtn}</span>${dup}${vpic}${mismatch}`;
}

/* No bulk export at any tier: inventory goes stale in days, but the part
 * values attached to every row don't — a one-click download of them is a
 * permanent copy of the product. Deliberate decision, not an oversight. */

async function loadAllPricing() {
  // All chain price lists fetch in parallel (this used to be a serial
  // waterfall queued in front of the big inventory fetch). Each is optional.
  const grab = async (url, apply) => {
    try {
      const resp = await fetch(DATA_BASE + url);
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
    grab('data/fenix_pricing.json', d => { fenixPricing = d; }),
    grab('data/harrys_pricing.json', d => d.forEach(p => { harrysPricing[p.description] = p; })),
    grab('data/indy_pricing.json', d => d.forEach(p => { indyPricing[p.description] = p; })),
    grab('data/upullitne_pricing.json', d => d.forEach(p => { upullitnePricing[p.description] = p; })),
    grab('data/ruperts_pricing.json', d => d.forEach(p => { rupertsPricing[p.description] = p; })),
    grab('data/pns_pricing.json', d => d.forEach(p => { pnsPricing[p.description] = p; })),
    grab('data/partsgalore_pricing.json', d => d.forEach(p => { partsgalorePricing[p.description] = p; })),
    grab('data/chesterfield_pricing.json', d => d.forEach(p => { chesterfieldPricing[p.description] = p; })),
    grab('data/ace_pricing.json', d => d.forEach(p => { acePricing[p.description] = p; })),
    grab('data/sturtevant_pricing.json', d => d.forEach(p => { sturtevantPricing[p.description] = p; })),
    grab('data/nvpap_pricing.json', d => d.forEach(p => { nvpapPricing[p.description] = p; })),
    grab('data/barrys_pricing.json', d => d.forEach(p => { barrysPricing[p.description] = p; })),
    grab('data/budget_pricing.json', d => { budgetPricing = d; }),
    grab('data/p195_pricing.json', d => d.forEach(p => { p195Pricing[p.description] = p; })),
    grab('data/pnpsa_pricing.json', d => d.forEach(p => { pnpsaPricing[p.description] = p; })),
    grab('data/ryans_pricing.json', d => d.forEach(p => { ryansPricing[p.description] = p; })),
    grab('data/usauto_pricing.json', d => d.forEach(p => { usautoPricing[p.description] = p; })),
    grab('data/upas_pricing.json', d => d.forEach(p => { upasPricing[p.description] = p; })),
  ]);
  _yardCostMemo.clear();
  // Compare/type-ahead caches may have been built against empty lists.
  _partQuoteMemo.clear();
  _partIndex = null;
  _partIndexSig = '';
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
  // Part-first pickers draw from the inventory; refresh them if the Parts
  // tab was visited before the data arrived (function declarations hoist,
  // so this forward reference is safe).
  if (pfInited) pfPopulatePickers();
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
 * data/vehicle_extras.json maps vehicle id ->
 * [photoCode, color, engine, trans, transSrc('listing'|'vin')].
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
/* Confirmed manual transmission — from the VIN decode or the yard's own
 * listing text, carried in the extras shard. Honest rule: only ever true when
 * the data says "Manual"; never inferred, and automatics get no badge at all.
 * Most cars have NEITHER signal (vPIC leaves TransmissionStyle blank for most
 * makes, and most yard listings don't say) — those stay unknown, so a real
 * manual that nothing confirms simply won't carry the badge or pass the
 * filter. The copy around this must never claim otherwise. */
function isConfirmedManual(v) {
  const ex = extrasFor(v);
  const t = ex && ex[3] ? String(ex[3]) : '';
  return /manual/i.test(t) && !/automated/i.test(t);
}
/* Which data source confirmed the transmission: 'listing' (the yard's own
 * feed/table) or 'vin' (the VIN decode) — same vocabulary as parts'
 * trim_status. Older extras shards predate the source column; everything in
 * them came from the VIN decode, so that's the fallback. */
function transSource(v) {
  const ex = extrasFor(v);
  if (!ex || !ex[3]) return null;
  return ex[4] === 'listing' ? 'listing' : 'vin';
}

fetch(DATA_BASE + 'data/vehicle_extras.json')
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
fetch(DATA_BASE + 'data/sale_events.json')
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
  return ` <span class="sale-pill" title="${escapeHtml(ev.title || 'Sale')} &mdash; from the chain\u2019s published sale calendar">${ICON.tag}${label}</span>`;
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
const INVENTORY_URL = DATA_BASE + 'data/inventory_live.json';
const INVENTORY_META_URL = DATA_BASE + 'data/inventory_meta.json';

/* In-flight guard: the boot load, the resume self-heal, an alert-tap entry,
 * and the manual refresh button can all ask at once — piggyback on the
 * running fetch instead of stacking multi-MB downloads. */
let _invInFlight = null;
function loadLiveInventory(opts = {}) {
  if (_invInFlight) return _invInFlight;
  _invInFlight = _loadLiveInventory(opts).finally(() => { _invInFlight = null; });
  return _invInFlight;
}

/* opts.fresh — bypass the HTTP cache outright (cache:'reload'); used when we
 *   KNOW a newer scan exists (the user arrived from a push alert that the
 *   scan commit itself triggered).
 * opts.quiet — override the apply mode: false forces a full re-render (alert
 *   entry must show the alerted car), true keeps a background refresh
 *   unobtrusive (resume self-heal). Default: quiet iff data was already on
 *   screen (the original behavior). */
async function _loadLiveInventory({ fresh = false, quiet = null } = {}) {
  // Pricing files load concurrently with the inventory (they used to be a
  // serial waterfall in front of the ~37MB fetch). Rendering needs them for
  // pull costs, so each render path awaits this promise before first paint
  // of cards.
  const pricingReady = loadAllPricing();

  // API mode (feature-flagged, see api.js): load tier-aware shards from the
  // backend instead of the public static file. Falls back to static on error.
  if (!IS_NATIVE && window.YSApi && YSApi.enabled()) {
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
  // Mid-session refetches (resume self-heal, alert entry, refresh button)
  // skip the cache re-apply — what's on screen IS the cached copy — and go
  // straight to the conditional network fetch.
  let shownScrapedAt = liveLoaded ? (liveScrapedAt || 'unknown') : null;
  let cache = null;
  try {
    if ('caches' in window) {
      cache = await caches.open(DATA_CACHE);
      if (!shownScrapedAt) {
        const hit = await cache.match(INVENTORY_URL);
        if (hit) {
          const raw = await hit.json();
          await pricingReady;
          applyInventory(raw);
          shownScrapedAt = raw.scrapedAt || 'unknown';
        }
      }
    }
  } catch (e) { /* cached copy unreadable — fall through to network */ }

  try {
    // 'reload' bypasses the HTTP cache outright (alert entry — the push
    // proves a newer scan is published); 'no-cache' is a conditional
    // revalidation (GitHub Pages serves ETags, so it costs one 304 round
    // trip when nothing changed).
    // Cheap freshness probe first: the scan publishes a few-byte
    // inventory_meta.json beside the big file. When its scrapedAt matches
    // what's on screen there is nothing to download or parse — the old
    // path re-read and re-parsed the whole ~37 MB file just to learn that
    // (a 304 upstream still hands the browser the full cached body).
    if (shownScrapedAt && !fresh) {
      try {
        const mr = await fetch(INVENTORY_META_URL, { cache: 'no-cache' });
        if (mr.ok) {
          const meta = await mr.json();
          if (meta && meta.scrapedAt && meta.scrapedAt === shownScrapedAt) return; // nothing new
        }
      } catch (e) { /* meta missing/offline — fall through to the real check */ }
    }
    const resp = await fetch(INVENTORY_URL,
      fresh ? { cache: 'reload' } : (shownScrapedAt ? { cache: 'no-cache' } : {}));
    if (!resp.ok) throw new Error('not found');
    // Write-through and parse concurrently; the cache write used to block
    // parsing for the full disk write.
    const putP = cache ? cache.put(INVENTORY_URL, resp.clone()).catch(() => { /* quota */ }) : null;
    const raw = await resp.json();
    if (putP) await putP;
    if (shownScrapedAt && (raw.scrapedAt || 'unknown') === shownScrapedAt) return; // nothing new
    await pricingReady;
    applyInventory(raw, { quiet: quiet != null ? quiet : !!shownScrapedAt });
  } catch (e) {
    if (shownScrapedAt) return; // cached data already on screen — stay quiet
    liveLoaded = false;
    document.getElementById('live-stats-bar').innerHTML = '';
    document.getElementById('live-grid').innerHTML = `
      <div class="empty-state" style="grid-column: 1/-1;">
        <h3>Couldn\u2019t load inventory</h3>
        <p>The inventory data didn\u2019t load. Check your connection and pull to refresh (or tap Refresh data in Filters).</p>
        <p style="margin-top:0.75rem;">If this keeps happening, the latest scan may still be publishing &mdash; try again in a few minutes.</p>
      </div>`;
  }
}

/* ===== RESUME SELF-HEAL =====
 * The inventory only revalidated at launch, so an app resumed after hours in
 * the background kept presenting a superseded scan as live. On resume, if
 * the loaded scan is over an hour old, revalidate in the background: a
 * conditional request (ETag) when nothing changed, a quiet in-place swap
 * when a newer scan published. Keeps the "SCANNED xH AGO" fact chips honest. There is deliberately NO
 * periodic timer — launch + resume + alert entry + the manual refresh button
 * cover every way stale data meets eyeballs, without idle-drain. */
const RESUME_STALE_MS = 60 * 60 * 1000;          // scans publish every ~4-6h
const RESUME_THROTTLE_MS = 5 * 60 * 1000;        // visibility flaps; don't hammer
let _lastResumeRefresh = 0;

function refreshIfStale() {
  if (!liveLoaded || !liveScrapedAt) return;     // boot path owns the first load
  const age = Date.now() - new Date(liveScrapedAt).getTime();
  if (!isFinite(age) || age < RESUME_STALE_MS) return;
  if (Date.now() - _lastResumeRefresh < RESUME_THROTTLE_MS) return;
  _lastResumeRefresh = Date.now();
  loadLiveInventory({ quiet: true }).catch(() => { /* retried on next resume */ });
}
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') refreshIfStale();
});
// Capacitor/Cordova fire a document 'resume' event on app foreground; where
// it never fires, the visibilitychange above covers the same transition.
document.addEventListener('resume', refreshIfStale);

/* Coverage transparency: the yard count shown in the zip banner / footer is
 * computed from the live data, never hardcoded. */
function coverageYardCount() {
  return new Set(liveInventory.map(v => v.location).filter(Boolean)).size;
}
/* Marketing surfaces (zip banner, header ticker, about copy) show a rounded
 * tier that auto-scales with coverage — floored to the nearest 10 with a
 * plus ("210+" at 212 yards, "250+" when we get there) so nobody maintains
 * an exact number in copy. Analytical surfaces (Yards tab stat cards) keep
 * the exact count. */
function yardCountDisplay() {
  const n = coverageYardCount();
  if (!n) return '';
  return n >= 10 ? `${Math.floor(n / 10) * 10}+` : String(n);
}
function updateCoverageCounts() {
  const disp = yardCountDisplay();
  if (!disp) return;
  document.querySelectorAll('.coverage-count').forEach(el => { el.textContent = disp; });
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
  const nDisp = yardCountDisplay();
  if (cars) facts.push(`${cars.toLocaleString()} CARS ON ROW`);
  if (nDisp) facts.push(`${nDisp} YARDS COAST TO COAST`);
  const { fresh, near } = headTickerHeavy();
  if (fresh) facts.push(`${fresh.toLocaleString()} SET OUT THIS WEEK`);
  if (near) facts.push(`${near} YARD${near === 1 ? '' : 'S'} IN YOUR RANGE`);
  const ts = Date.parse(liveScrapedAt || '');
  if (ts) {
    const hrs = Math.max(0, Math.round((Date.now() - ts) / 3600000));
    facts.push(hrs < 1 ? 'SCANNED UNDER AN HOUR AGO'
      : hrs < 48 ? `SCANNED ${hrs}H AGO`
      : `SCANNED ${Math.round(hrs / 24)}D AGO`);
  }
  return facts;
}
/* The two full-inventory passes (fresh-this-week count, yards in range) are
 * memoised on what can change them; the 5 s tick only rotates the text. */
let _headHeavyKey = null, _headHeavyVal = { fresh: 0, near: 0 };
function headTickerHeavy() {
  const r = activeZipCoords ? effectiveRadiusMi() : null;
  const key = [liveScrapedAt, liveInventory.length, activeZipCoords && activeZipCoords.lat,
    activeZipCoords && activeZipCoords.lng, r, Math.floor(Date.now() / 3600000)].join('|');
  if (key === _headHeavyKey) return _headHeavyVal;
  const weekAgo = Date.now() - 7 * 86400000;
  const fresh = liveInventory.reduce((k, v) => k + (yardDateMs(v.dateAdded) >= weekAgo ? 1 : 0), 0);
  let near = 0;
  if (activeZipCoords) {
    near = new Set(liveInventory
      .filter(v => v.lat != null && haversineMiles(activeZipCoords.lat, activeZipCoords.lng, v.lat, v.lng) <= r)
      .map(v => v.location)).size;
  }
  _headHeavyKey = key;
  _headHeavyVal = { fresh, near };
  return _headHeavyVal;
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
  // No point rotating a header nobody can see; resume on return.
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') { clearInterval(_headTickerTimer); _headTickerTimer = null; }
    else if (!_headTickerTimer) _headTickerTimer = setInterval(show, 5000);
  });
}

/* One-tap actions for the out-of-range empty state. */
function jhWidenRadius(mi) {
  const sel = document.getElementById('live-radius');
  // Free users can only widen to free tiers (≤ 250 mi); 500 mi and "any
  // distance" are Pro, so nothing wide enough gets the honest pitch instead.
  const opts = [...sel.options].map(o => parseFloat(o.value))
    .filter(v => !isNaN(v) && (isPro() || v <= FREE_MAX_RADIUS_MI));
  const fit = opts.find(v => v >= mi);
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
/* The radius select ships at 100 mi (the `selected` option in index.html).
 * Filter badges count only what the user CHANGED from its default — a fresh
 * install must not wear a "Filters 1" badge (owner request 2026-10-26). */
const DEFAULT_RADIUS = '100';
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

/* Yard inventory systems disagree on model naming — most still file the WRX
 * as an Impreza trim (true until 2015), so the same car shows up as "WRX",
 * "Impreza WRX", or "Impreza" depending on the yard. This table merges the
 * *spellings* into one filter entry per real model. It can't catch cars
 * filed under the plain parent name (a 2016 WRX typed as "Impreza") — that
 * needs the VIN decode and is a separate project. Keys are lowercase. */
const MODEL_ALIASES = {
  subaru: {
    'impreza wrx': 'WRX',
    'wrx': 'WRX',
    'impreza wrx sti': 'WRX STI',
    'impreza sti': 'WRX STI',
    'wrx sti': 'WRX STI',
    'xv crosstrek': 'Crosstrek',
    'crosstrek': 'Crosstrek',
  },
  mazda: {
    'mx-5 miata': 'Miata (MX-5)',
    'mx-5': 'Miata (MX-5)',
    'mx5': 'Miata (MX-5)',
    'miata': 'Miata (MX-5)',
  },
};

/* 2026-10 model merge — mirror of the scraper's normalize_model output for
 * every pre-merge inventory spelling whose canonical form differs beyond
 * case ('Mazda 3'->'Mazda3', 'F250Sd Pickup'->'F-250 Super Duty', 'BMW
 * 328i'->'328i', 'Charger Lc'->'Charger'...). The inventory now ships
 * canonical models; this map exists so WATCHES saved BEFORE the merge keep
 * matching at comparison time — same approach as MAKE_ALIASES (fa3480c).
 * Outer keys: squashed canonical make; inner keys: squashed old model.
 * Generated from the full pre-merge inventory audit (2026-10-22); keep in
 * sync with scraper/test_model_normalization.py. */
const MODEL_RENAMES_2026_10 = {
  "alfaromeo": {
    "alfaromeogtv6": "Gtv-6",
  },
  "audi": {
    "audi4000": "4000", "audia3": "A3", "audia4": "A4", "audia5": "A5", "audia6": "A6",
    "audia8": "A8", "audiallroad": "Allroad", "audicabriolet": "Cabriolet", "audiq3": "Q3",
    "audiq5": "Q5", "audiq7": "Q7", "audis3": "S3", "audis5": "S5", "auditt": "TT",
  },
  "bmw": {
    "525ia": "525i", "530ia": "530i", "bmw128i": "128i", "bmw318i": "318i", "bmw320i": "320i",
    "bmw323i": "323i", "bmw325i": "325i", "bmw328i": "328i", "bmw330i": "330i",
    "bmw335i": "335i", "bmw430i": "430i", "bmw525i": "525i", "bmw528e": "528e",
    "bmw528i": "528i", "bmw530i": "530i", "bmw535i": "535i", "bmw540i": "540i",
    "bmw550i": "550i", "bmw550igt": "550i GT", "bmw645i": "645i", "bmw650i": "650i",
    "bmw735i": "735i", "bmw740i": "740i", "bmw745i": "745i", "bmw750i": "750i",
    "bmwalpinab7": "Alpina B7", "bmwi3": "i3", "bmwx1": "X1", "bmwx3": "X3", "bmwx5": "X5",
    "bmwz3": "Z3", "bmwz4": "Z4",
  },
  "buick": {
    "rendezvoussrv": "Rendezvous",
  },
  "cadillac": {
    "eldorado": "Eldorado",
  },
  "chevrolet": {
    "astrovan": "Astro", "belair": "Bel Air", "blazers10jimmys15": "Blazer S10/Jimmy S15",
    "c10": "C10", "c10pickup": "C10", "c20truck": "C20", "c30pickup": "C30",
    "chevrolet10pickup": "10 Pickup", "chevrolet10van": "10 Van",
    "chevrolet1500pickup": "1500 Pickup", "chevrolet20pickup": "20 Pickup",
    "chevrolet20van": "20 Van", "chevrolet2500pickup": "2500 Pickup", "chevrolet30van": "30 Van",
    "chevrolet3500pickup": "3500 Pickup", "chevyvanclassic": "Chevy Van",
    "cityexpressls": "City Express", "ck10series": "C/K 10", "ck1500series": "C/K 1500",
    "ck20series": "C/K 20", "ck2500series": "C/K 2500", "ck30series": "C/K 30",
    "ck3500series": "C/K 3500", "express1500van": "Express 1500",
    "express2500van": "Express 2500", "express3500van": "Express 3500", "geoprizm": "Prizm",
    "gseriesvan": "G-Series", "luminacar": "Lumina", "luminaminivan": "Lumina APV",
    "luminavan": "Lumina APV", "pu": "P.U", "rv20series": "R/V 20", "s10pickup": "S-10",
    "s10pu": "S-10", "s10s15sonoma": "S10/S15/Sonoma", "silverado1500hd": "Silverado 1500HD",
    "silverado1500pickup": "Silverado 1500", "silverado2500pickup": "Silverado 2500",
    "silverado3500pickup": "Silverado 3500", "silveradoclassic1500": "Silverado 1500 Classic",
    "silveradohd2500": "Silverado 2500HD", "ventureapv": "Venture",
  },
  "chrysler": {
    "200js": "200", "200lx": "200", "200uf": "200", "300clx": "300C", "300lx": "300",
    "300m": "300M", "aspenhg": "Aspen", "concordelh": "Concorde", "crossfirezh": "Crossfire",
    "lhslh": "LHS", "pacificacs": "Pacifica", "ptcruiserpt": "PT Cruiser",
    "sebringjr": "Sebring", "sebringjs": "Sebring", "tcmaserati": "TC By Maserati",
    "townampcountry": "Town & Country", "townandcountry": "Town & Country",
    "townandcountryrs": "Town & Country", "townandcountryrt": "Town & Country",
    "voyagerrs": "Voyager",
  },
  "dodge": {
    "200pu": "200 P.U", "avengerjs": "Avenger", "caliberpm": "Caliber",
    "caravangrandcaravanrs": "Caravan/Grand Caravan", "caravanrs": "Caravan",
    "challengerla": "Challenger", "challengerlc": "Challenger", "chargerlc": "Charger",
    "chargerlx": "Charger", "d100pickup": "D100", "d10pu": "D-10 P.U", "d150pickup": "D150",
    "dakotaan": "Dakota", "dakotand": "Dakota", "dartpf": "Dart",
    "dodge1500pickup": "1500 Pickup", "dodge1500van": "1500 Van", "dodge150pickup": "150 Pickup",
    "dodge2500pickup": "2500 Pickup", "dodge2500van": "2500 Van",
    "dodge3500pickup": "3500 Pickup", "dodge3500van": "3500 Van", "dodge600": "600",
    "durangodn": "Durango", "durangohb": "Durango", "grandcaravan": "Grand Caravan",
    "grandcaravanrs": "Grand Caravan", "grandcaravanrt": "Grand Caravan",
    "intrepidlh": "Intrepid", "journeyjc": "Journey", "magnumlx": "Magnum", "neonpl": "Neon",
    "nitroka": "Nitro", "pud250": "D250", "ram1500van": "Ram Van 1500",
    "ram2500van": "Ram Van 2500", "ram3500van": "Ram Van 3500", "stratusja": "Stratus",
    "stratusjr": "Stratus", "w100pickup": "W100", "w150pickup": "W150", "w200pickup": "W200",
    "w250pickup": "W250", "w350pickup": "W350",
  },
  "fiat": {
    "fiat500": "500", "fiatfiat500": "500",
  },
  "ford": {
    "e100econoline": "E-100", "e150clubwagon": "E-150", "e150econoline": "E-150",
    "e150econolineclubwagon": "E-150", "e150van": "E-150", "e250econoline": "E-250",
    "e250van": "E-250", "e300econoline": "E-300", "e350clubwagon": "E-350",
    "e350econoline": "E-350", "e350econolineclubwagon": "E-350", "e350van": "E-350",
    "e350wagon": "E-350", "e450sdvan": "E-450 Super Duty", "ecosportse": "Ecosport",
    "ecosportses": "Ecosport", "escapelimited": "Escape", "escapexls": "Escape",
    "escapexlt": "Escape", "f100pickup": "F-100", "f100truck": "F-100", "f150pickup": "F-150",
    "f250pickup": "F-250", "f250sd": "F-250 Super Duty", "f250sdpickup": "F-250 Super Duty",
    "f350pickup": "F-350", "f350sd": "F-350 Super Duty", "f350sdpickup": "F-350 Super Duty",
    "f450sd": "F-450 Super Duty", "f450sdpickup": "F-450 Super Duty", "forde150van": "E-150",
    "forde250van": "E-250", "forde350van": "E-350", "forde450sdvan": "E-450 Super Duty",
    "fordf150pickup": "F-150", "fordf250pickup": "F-250", "fordf250sdpickup": "F-250 Super Duty",
    "fordf350pickup": "F-350", "fordf350sdpickup": "F-350 Super Duty",
    "fordf450sdpickup": "F-450 Super Duty", "fordf550sdpickup": "F-550 Super Duty",
    "fordpass": "Pass", "transit150": "Transit-150", "transit250": "Transit-250",
    "transit350": "Transit-350",
  },
  "gmc": {
    "c15c1500pickup": "C1500", "ck1500series": "C/K 1500", "ck2500series": "C/K 2500",
    "gmc1500pickup": "1500 Pickup", "gmc1500van": "1500 Van", "gmc2500pickup": "2500 Pickup",
    "gmc2500van": "2500 Van", "gmc3500pickup": "3500 Pickup", "gmcenvoy": "Envoy",
    "gmcenvoyxl": "Envoy Xl", "gmcs10s15sonoma": "S10/S15/Sonoma", "gmcsafarigmc": "Safari",
    "gmcsierra1500pickup": "Sierra 1500", "gmcsierradenaliev": "Sierra Denali Ev",
    "gmcterrain": "Terrain", "gmcyukon": "Yukon", "gmcyukonxl1500": "Yukon XL 1500",
    "jimmys15": "S-15 Jimmy", "jimmyutility": "Jimmy", "s15pickup": "S-15",
    "s15utility": "S-15 Jimmy", "safarigmc": "Safari", "savana1500van": "Savana 1500",
    "savana2500van": "Savana 2500", "savana3500van": "Savana 3500",
    "sierra1500pickup": "Sierra 1500", "sierra2500pickup": "Sierra 2500",
    "sierrack1500": "Sierra 1500", "sierrack2500": "Sierra 2500", "sierrack3500": "Sierra 3500",
  },
  "honda": {
    "civiccrx": "CRX",
  },
  "hummer": {
    "hummerh3": "H3",
  },
  "infiniti": {
    "infinitiex35": "EX35", "infinitiex37": "EX37", "infinitifxseries": "FX Series",
    "infinitig20": "G20", "infinitig25": "G25", "infinitig35": "G35", "infinitig37": "G37",
    "infinitii30": "I30", "infinitii35": "I35", "infinitij30": "J30", "infinitijx35": "JX35",
    "infinitim35": "M35", "infinitim37": "M37", "infinitiq45": "Q45", "infinitiq50": "Q50",
    "infinitiq60": "Q60", "infinitiq70": "Q70", "infinitiqx30": "QX30", "infinitiqx4": "QX4",
    "infinitiqx50": "QX50", "infinitiqx56": "QX56", "infinitiqx60": "QX60",
    "infinitiqx80": "QX80", "qx41999": "QX4",
  },
  "isuzu": {
    "isuzuascender": "Ascender", "isuzui280": "I-280", "isuzupuppickup": "Pup (Pickup)",
    "isuzurodeo": "Rodeo", "isuzutrooper": "Trooper",
  },
  "jaguar": {
    "xj6": "XJ6", "xjsedan": "XJ",
  },
  "jeep": {
    "cherokeekl": "Cherokee", "cherokeexj": "Cherokee", "cj7": "CJ7", "commanderxh": "Commander",
    "commanderxk": "Commander", "compassmk": "Compass", "grandcherokeewj": "Grand Cherokee",
    "grandcherokeewk": "Grand Cherokee", "j10pickup": "J10", "libertykj": "Liberty",
    "libertykk": "Liberty", "patriotmk": "Patriot", "pucomanche": "Comanche",
    "wranglerjk": "Wrangler",
  },
  "kia": {
    "forte5door": "Forte5", "rio5door": "Rio5", "riocinco": "Rio5",
  },
  "landrover": {
    "discoveryii": "Discovery Series II", "evoque": "Range Rover Evoque",
    "landroverdiscovery": "Discovery", "landroverevoque": "Range Rover Evoque",
    "landroverlr2": "Lr2", "landroverrangerover": "Range Rover",
    "landroverrangesport": "Range Rover Sport",
  },
  "lexus": {
    "es300h": "ES 300h", "is200t": "IS 200t", "lexusct200h": "CT 200h", "lexuses300": "ES 300",
    "lexuses330": "ES 330", "lexuses350": "ES 350", "lexusgs300": "GS 300",
    "lexusgs350": "GS 350", "lexusgs400": "GS 400", "lexusgs430": "GS 430",
    "lexusgs450h": "GS 450h", "lexusgs460": "GS 460", "lexusis250": "IS 250",
    "lexusis300": "IS 300", "lexusis350": "IS 350", "lexusls400": "LS 400",
    "lexusls430": "LS 430", "lexusls460": "LS 460", "lexusls600hl": "LS 600h L",
    "lexusrx300": "RX 300", "lexusrx330": "RX 330", "lexusrx350": "RX 350",
    "lexusrx400h": "RX 400h", "lexusscseries": "SC Series", "rx450h": "RX 450h",
    "ux250h": "UX 250h",
  },
  "lincoln": {
    "lincolnls": "LS",
  },
  "mazda": {
    "2": "Mazda2", "3": "Mazda3", "5": "Mazda5", "6": "Mazda6", "b2000": "B2000",
    "b2200": "B2200", "b2300": "B2300", "mazda2": "Mazda2", "mazda3": "Mazda3",
    "mazda5": "Mazda5", "mazda6": "Mazda6", "mazda626": "626", "mazdab2200": "B2200",
    "mazdab2300": "B2300", "mazdab2600": "B2600", "mazdab3000": "B3000", "mazdab4000": "B4000",
    "mazdacx30": "Cx-30", "mazdacx5": "Cx-5", "mazdacx7": "CX-7", "mazdacx9": "CX-9",
    "mazdamillenia": "Millenia", "mazdampv": "MPV", "mazdamx5miata": "MX-5 Miata",
    "mazdamx6": "Mx-6", "mazdaprotege": "Protege", "mazdarx8": "RX-8", "mazdatribute": "Tribute",
    "miata": "MX-5 Miata", "mx5": "MX-5 Miata", "rx8": "RX-8", "tributedx": "Tribute",
    "tributees": "Tribute", "tributelx": "Tribute",
  },
  "mercedesbenz": {
    "mercedes190": "190", "mercedes2304": "230-4", "mercedes280": "280", "mercedes300d": "300D",
    "mercedes300e": "300E", "mercedes380": "380", "mercedes560": "560",
    "mercedescclass": "C-Class", "mercedesclaclass": "CLA-Class", "mercedesclclass": "CL-Class",
    "mercedesclk": "CLK", "mercedesclsclass": "CLS-Class", "mercedeseclass": "E-Class",
    "mercedesglaclass": "GLA-Class", "mercedesglclass": "GL-Class",
    "mercedesglkclass": "GLK-Class", "mercedesmlclass": "M-Class", "mercedesrclass": "R-Class",
    "mercedessclass": "S-Class", "mercedesslk": "SLK", "mercedessprinter2500": "Sprinter 2500",
    "mercedessprinter3500": "Sprinter 3500", "mlclass": "M-Class", "smartsmart": "Smart",
  },
  "mini": {
    "cooperclubman": "Clubman", "cooperconvertible": "Convertible",
    "coopercountryman": "Countryman", "cooperhardtop": "Hardtop", "cooperpaceman": "Paceman",
    "miniclubman": "Clubman", "minicooper": "Cooper", "minicountryman": "Countryman",
    "miniminicooper": "Cooper",
  },
  "mitsubishi": {
    "mitsubishipickup": "Pickup", "mitsubishiraider": "Raider", "raidernm": "Raider",
  },
  "nissan": {
    "nissanpickup": "Pickup", "nv1500": "NV1500", "nv2500hd": "NV2500 HD", "nv3500": "NV3500",
    "pathfinder19995": "Pathfinder", "pu": "P.U",
  },
  "oldsmobile": {
    "ciera": "Cutlass Ciera", "culassciera": "Cutlass Ciera",
    "deltaeightyeightroyale": "Delta 88", "eightyeight88": "Eighty-Eight",
    "eightyeightroyale": "Eighty-Eight", "intriguegls": "Intrigue", "intriguegx": "Intrigue",
    "ninetyeight98": "Ninety-Eight", "oldsmobilebravada": "Bravada",
    "silhouetteapv": "Silhouette",
  },
  "pontiac": {
    "azteksrv": "Aztek", "bonnevillegxp": "Bonneville", "bonnevillese": "Bonneville",
    "g3wave": "G3", "grandamgt": "Grand Am", "grandamgt1": "Grand Am", "grandamse": "Grand Am",
    "grandamse1": "Grand Am", "grandprixgt": "Grand Prix", "grandprixgt2": "Grand Prix",
    "grandprixgtp": "Grand Prix", "grandprixse": "Grand Prix", "grandprixse1": "Grand Prix",
    "pontiacfirebird": "Firebird", "pontiacg6": "G6", "pontiacgrandam": "Grand Am",
    "pontiacgrandprix": "Grand Prix", "pontiacmontana": "Montana", "pontiactorrent": "Torrent",
    "sunfirese": "Sunfire",
  },
  "porsche": {
    "porsche944": "944", "porscheboxster": "Boxster", "porschecayenne": "Cayenne",
  },
  "ram": {
    "dodge1500pickup": "1500", "dodge2500pickup": "2500", "promaster1500van": "ProMaster 1500",
    "promaster2500van": "ProMaster 2500", "promaster3500van": "ProMaster 3500",
  },
  "saab": {
    "saab93": "9-3", "saab95": "9-5", "saab97x": "9-7X",
  },
  "saturn": {
    "astraxe": "Astra", "auragreenlinehybrid": "Aura Green Line", "auraxe": "Aura",
    "auraxr": "Aura", "l300sedan": "L300", "saturnaura": "Aura", "saturnion": "ION",
    "saturnlseries": "L-Series", "saturnsseries": "S-Series", "saturnvue": "VUE", "sl1": "SL1",
    "vuegreenlinehybrid": "VUE Green Line",
  },
  "scion": {
    "scionia": "iA", "sciontc": "tC", "scionxa": "xA", "scionxb": "xB", "scionxd": "xD",
    "toyotascionxa": "xA", "toyotatc": "tC", "toyotaxb": "xB", "toyotaxd": "xD",
  },
  "suzuki": {
    "grandvitaraxl7": "XL-7", "sx4sedan": "SX4 Sport",
  },
  "toyota": {
    "corollamatrix": "Matrix", "pickup": "Pickup", "pickupdlx": "Pickup", "pickupstd": "Pickup",
    "solara": "Camry Solara", "toyotapickup": "Pickup", "vanwagon": "Van",
  },
  "volkswagen": {
    "cabrioletconvertible": "Cabriolet", "gli": "Jetta GLI", "golfgti": "GTI",
  },
  "volvo": {
    "240series": "240", "240series240": "240", "740series": "740", "760series": "760",
    "850series": "850", "850series850": "850", "940series": "940", "940series940": "940",
    "960series": "960", "volvo120series": "120 Series", "volvo240series": "240",
    "volvo30series": "30 Series", "volvo40series": "40 Series", "volvo50series": "50 Series",
    "volvo60series": "60 Series", "volvo70series": "70 Series", "volvo740": "740",
    "volvo80series": "80 Series", "volvos60": "S60", "volvoxc60": "XC60", "volvoxc90": "XC90",
  },
};

function canonicalModel(make, model) {
  // canonicalMake first so a pre-merge watch make ('Vw') finds the table.
  const mk = canonicalMake(make);
  const table = MODEL_ALIASES[String(mk || '').toLowerCase()];
  const hit = table && table[String(model || '').trim().toLowerCase()];
  if (hit) return hit;
  const ren = MODEL_RENAMES_2026_10[String(mk || '').toLowerCase().replace(/[^a-z0-9]/g, '')];
  if (ren) {
    const r = ren[String(model || '').toLowerCase().replace(/[^a-z0-9]/g, '')];
    if (r) return r;
  }
  return model;
}

/* Make aliases — mirror of the scraper's _MAKE_ALIASES (2026-10 dropdown
 * dedupe: MINI Cooper/MINI, Alfa-Romeo, Fiat-Lancia, Vw, Mercedes, Rover).
 * The inventory ships already-canonical makes; this map exists so WATCHES
 * users saved BEFORE the merge (localStorage + synced backend copies, e.g.
 * make "MINI Cooper" or "Vw") still match at comparison time — simpler and
 * safer than migrating every stored watch. Keys are squashed lowercase
 * alphanumerics. */
const MAKE_ALIASES = {
  minicooper: 'MINI',
  alfaromeo: 'Alfa Romeo',
  fiatlancia: 'Fiat',
  mercedes: 'Mercedes-Benz',
  mercedesbenz: 'Mercedes-Benz',
  vw: 'Volkswagen',
  volkswagon: 'Volkswagen',
  chevy: 'Chevrolet',
  chev: 'Chevrolet',
  rover: 'Land Rover',
  landrover: 'Land Rover',
  rangerover: 'Land Rover',
  infinity: 'Infiniti',
};

function canonicalMake(make) {
  const key = String(make || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  return MAKE_ALIASES[key] || String(make || '');
}

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
    if (v.make === make && v.model) {
      const m = canonicalModel(make, v.model);
      counts.set(m, (counts.get(m) || 0) + 1);
    }
  }
  // Drop selections that no longer exist in scope (make change, radius change).
  for (const m of [...selectedModels]) if (!counts.has(m)) selectedModels.delete(m);
  renderModelList(counts);
  updateModelBtnLabel();
}

/* Space/punctuation-insensitive model search: the 2026-10 normalization
 * canonicalized display names to hyphenated/spaced forms (F-150, S-10,
 * MR2 Spyder), so a plain substring test misses the spellings people
 * actually type — 'f150', 's10', 'mr 2'. Squash BOTH sides to lowercase
 * alphanumerics before the substring test; a squashed match is a strict
 * superset of the old plain match, so nothing that used to match stops. */
function modelSearchMatch(model, q) {
  if (!q) return true;
  const squash = s => String(s).toLowerCase().replace(/[^a-z0-9]/g, '');
  return squash(model).includes(squash(q));
}

let _modelCounts = new Map();
function renderModelList(counts) {
  if (counts) _modelCounts = counts;
  const list = document.getElementById('live-filter-model-list');
  const q = (document.getElementById('live-filter-model-search').value || '').trim().toLowerCase();
  const pro = isPro();
  const models = [...(_modelCounts).keys()].sort()
    .filter(m => modelSearchMatch(m, q));
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
/* A half-written value (quota hit mid-setItem) or a storage-disabled browser
 * must not throw at top level — everything below this line would never run. */
const zipCoordsCache = (() => {
  try { const v = JSON.parse(localStorage.getItem('jh_zip_coords') || '{}'); return v && typeof v === 'object' ? v : {}; }
  catch (e) { return {}; }
})();

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
  pfSyncWhere();   // keep the Parts-tab mirror current (skips a focused input)
  renderLive();
}

function vehicleDistanceMi(v) {
  if (!activeZipCoords || v.lat == null || v.lng == null) return null;
  return haversineMiles(activeZipCoords.lat, activeZipCoords.lng, v.lat, v.lng);
}

/* GPS "near me". Native: Capacitor Geolocation plugin, so iOS shows the real
 * system prompt ("YardScout would like to use your location") instead of the
 * WKWebView one that says "localhost". Web: browser geolocation (needs HTTPS). */
async function useMyLocation() {
  const btns = [document.getElementById('live-gps'), document.getElementById('zip-banner-gps')].filter(Boolean);
  const busy = on => btns.forEach(b => {
    if (on) { b.disabled = true; b.dataset.orig = b.innerHTML; b.innerHTML = '&hellip;'; }
    else { b.disabled = false; b.innerHTML = b.dataset.orig; }
  });
  const onPos = (lat, lng) => {
    activeZipCoords = { lat, lng };
    track('gps-used');
    localStorage.setItem('jh_gps', JSON.stringify(activeZipCoords));
    localStorage.removeItem('jh_zip');
    const zipEl = document.getElementById('live-zip');
    zipEl.value = '';
    zipEl.placeholder = 'Using your location';
    busy(false);
    updateZipBanner();
    pfSyncWhere();
    renderLive();
    if (document.getElementById('tab-yards').classList.contains('active')) renderYards();
  };
  /* Honest errors: if location permission is denied (e.g. "Don't allow" was
   * tapped once — Android 11+ then silently rejects every later request with
   * NO system prompt), telling the user to "check access" without saying
   * where is useless. Point them at Settings explicitly. */
  const DENIED_MSG = IS_NATIVE
    ? "Location is turned off for YardScout. To use this, open your phone\u2019s Settings > Apps > YardScout > Permissions and allow Location — or enter a zip code instead."
    : "Location is blocked for this site. Allow location access in your browser\u2019s site settings, or enter a zip code instead.";
  const GENERIC_MSG = "Couldn\u2019t get your location. Check that location access is allowed for YardScout, or enter a zip code instead.";
  const onErr = async (e) => {
    busy(false);
    // Native plugin rejects permission denials with OS-PLUG-GLOC-0003 (both
    // iOS and Android); web GeolocationPositionError uses code 1. As a
    // fallback, ask the plugin for the current permission state.
    let denied = e && (e.code === 'OS-PLUG-GLOC-0003' || e.code === 1);
    if (!denied && nativeGeo) {
      try {
        const st = await nativeGeo.checkPermissions();
        denied = st.location === 'denied' && st.coarseLocation === 'denied';
      } catch (_) { /* best effort — fall through to generic message */ }
    }
    alert(denied ? DENIED_MSG : GENERIC_MSG);
  };
  const opts = { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 };
  const nativeGeo = IS_NATIVE && window.Capacitor?.Plugins?.Geolocation;
  if (nativeGeo) {
    busy(true);
    try {
      const pos = await nativeGeo.getCurrentPosition(opts);
      onPos(pos.coords.latitude, pos.coords.longitude);
    } catch (e) { onErr(e); }
    return;
  }
  if (!navigator.geolocation) { alert('Your browser does not support location.'); return; }
  busy(true);
  navigator.geolocation.getCurrentPosition(
    pos => onPos(pos.coords.latitude, pos.coords.longitude), onErr, opts);
}
document.getElementById('live-gps').addEventListener('click', useMyLocation);
document.getElementById('zip-banner-gps').addEventListener('click', useMyLocation);

/* ===== PRO =====
 * Pro ships exclusively through the iOS app (StoreKit, $8.99/mo). Web
 * touchpoints open the same upgrade sheet; its CTA links to the App Store. */
const FREE_SAVE_CAP = 5;

// Pro is a PAID product (App Store subscription). The only legitimate Pro
// sources are a StoreKit entitlement ('iap') or an account tier ('account').
// Anything else — the old ?pro=1 URL hatch, the old 7-tap dev toggle, a
// hand-edited localStorage — is revoked at boot. Real subscribers are
// re-granted moments later when the native launch entitlement check runs.
(() => {
  const src = localStorage.getItem('jh_pro_source');
  if (localStorage.getItem('jh_pro') === '1' && src !== 'iap' && src !== 'account') {
    localStorage.removeItem('jh_pro');
  }
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
  // Native builds never enter Stripe billing mode — Pro purchase on iOS will
  // go through StoreKit IAP when it ships; until then natives see the waitlist.
  const apiMode = !IS_NATIVE && window.YSApi && YSApi.enabled();
  const proState = document.getElementById('upgrade-pro-state');
  if (isPro()) {
    // Already Pro: no waitlist, no "launches soon" — just confirmation.
    document.getElementById('upgrade-form-wrap').style.display = 'none';
    document.getElementById('upgrade-thanks').style.display = 'none';
    if (proState) proState.style.display = '';
  } else if (apiMode) {
    // Real billing: the waitlist form gives way to sign-in + checkout.
    document.getElementById('upgrade-form-wrap').style.display = 'none';
    document.getElementById('upgrade-thanks').style.display = 'none';
    if (proState) proState.style.display = 'none';
  } else if (IS_NATIVE) {
    // Native: Pro is purchasable in-app — never show the web waitlist.
    // refreshNativeIapUi (below) reveals the StoreKit subscribe flow.
    document.getElementById('upgrade-form-wrap').style.display = 'none';
    document.getElementById('upgrade-thanks').style.display = 'none';
    if (proState) proState.style.display = 'none';
  } else {
    // Web: Pro is live in the iOS app — the sheet's CTA links to the App Store.
    document.getElementById('upgrade-form-wrap').style.display = '';
    document.getElementById('upgrade-thanks').style.display = 'none';
    if (proState) proState.style.display = 'none';
  }
  // Native: the sheet intro never mentions the web waitlist — Pro is a real
  // purchase here (and for Pro users, a real subscription they already have).
  if (IS_NATIVE) {
    const sheetSub = document.querySelector('#upgrade-sheet .sheet-sub');
    // Both platforms have real push now (APNs on iOS, FCM on Android since
    // 1.2) — same honest copy, only the store name differs.
    if (sheetSub) sheetSub.textContent =
      'Finding cars near you is free and stays free. '
      + 'Pro adds the savings layer — what each part would cost you '
      + 'used online, what the yard charges, what you\u2019d save, '
      + 'and push alerts within hours of arrival. Subscribe through '
      + (IS_ANDROID ? 'Google Play' : 'the App Store') + '; cancel anytime.';
  }
  document.getElementById('upgrade-sheet').classList.add('open');
  document.getElementById('upgrade-backdrop').classList.add('open');
  // Native app: swap the waitlist for the StoreKit subscribe flow when the
  // App Store product is loadable (defined later in the native module).
  if (IS_NATIVE && typeof refreshNativeIapUi === 'function') refreshNativeIapUi();
}
document.addEventListener('keydown', (e) => {
  if (e.key !== 'Escape') return;
  const open = (id) => { const el = document.getElementById(id); return el && el.classList.contains('open'); };
  if (open('upgrade-sheet')) closeUpgradeSheet();
  else if (open('saved-sheet')) closeSavedSheet();
  else if (open('prices-sheet')) closePricesSheet();
});
function closeUpgradeSheet() {
  document.getElementById('upgrade-sheet').classList.remove('open');
  document.getElementById('upgrade-backdrop').classList.remove('open');
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
  // Tier-appropriate default: a Pro who never picked a sort gets Worth the
  // trip (that's what they paid for); free default stays Newest arrivals. An
  // explicit choice (jh_sort) always wins and is restored at boot.
  if (pro && !localStorage.getItem('jh_sort')) sortSel.value = 'smart-profit';
}

/* Sorting BY value hands out the value ranking even with prices blurred, so
 * those sorts ride with the Pro value data. Free sorts are the neutral ones. */
const PRO_SORTS = new Set(['smart-profit', 'gold-first', 'fastest-sell', 'leaving-soonest']);
const FREE_DEFAULT_SORT = 'date-desc';

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
document.getElementById('pro-pill').addEventListener('click', () => openUpgradeSheet('header-pill'));
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
  // part isn't covered we don't invent a cost — the range is flagged value-only.
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
                ? `<div class="saved-item-profit" title="${range.unknownCost ? 'What these parts would cost to buy used online — pull cost not on this yard\u2019s published price list, check at the yard' : 'Estimated savings vs buying these parts used online, after this yard\u2019s list pull costs — if parts are good'}">${formatPrice(range.lo)}&ndash;${formatPrice(range.hi)}${range.unknownCost ? '<small style="display:block;font-weight:400;opacity:0.7;">online price</small>' : '<small style="display:block;font-weight:400;opacity:0.7;">est. savings</small>'}</div>`
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
  if (e.target.closest('.yard-site-link')) { track('yard-site-link'); return; } // anchor navigates normally
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

/* decodeURIComponent throws URIError on a truncated escape ("%E0%A4%A" —
 * what SMS/Messenger do to long share links); fall back to the raw key so a
 * bad link degrades to "no match" instead of a dead app. */
function safeDecode(s) {
  try { return decodeURIComponent(s); } catch (e) { return s; }
}
function applyShareHash() {
  // #car= is the share-link form; #alert= is the push-payload form (same key,
  // but it additionally signals "bypass caches" — see openFromAlert).
  const m = location.hash.match(/#(?:car|alert)=([^&]+)/);
  focusedCarKey = m ? safeDecode(m[1]) : null;
}
window.addEventListener('hashchange', () => {
  const alertId = (location.hash.match(/#alert=([^&]+)/) || [])[1];
  if (alertId) { openFromAlert(safeDecode(alertId)); return; }
  applyShareHash();
  if (liveLoaded) {
    renderLive();
    if (focusedCarKey) window.scrollTo({ top: 0 });
  }
});

/* ===== ALERT ENTRY (push-tap deep links) =====
 * A push alert PROVES a newer scan exists than whatever this session has
 * loaded — the alert fired from that scan's commit. The 19:44 incident:
 * push arrives, owner opens the app, and the watched 4Runner isn't there
 * because the app is still showing pre-scan cache. So entering from a
 * notification always bypasses the inventory caches, then lands on the
 * alerted car's card. Reached from: the native notification-tap listener
 * (iOS + Android), the service worker's web-push tap message, and any
 * #alert=<id> url (cold launches route through the boot loader instead). */
function openFromAlert(vehicleId) {
  track('alert-open' + (vehicleId ? '/car' : ''));
  if (vehicleId) {
    try { document.querySelector('.tab[data-tab="live"]').click(); } catch (e) { /* boot race */ }
    history.replaceState(null, '',
      location.pathname + location.search + '#car=' + encodeURIComponent(vehicleId));
    applyShareHash();
    if (liveLoaded) { renderLive(); window.scrollTo({ top: 0 }); }
  } else {
    // Payload without a vehicle id (sale-day alerts, pre-update payloads):
    // the Alerts tab is where the matches are — the old behavior.
    try { document.querySelector('.tab[data-tab="alerts"]').click(); } catch (e) { /* boot race */ }
  }
  loadLiveInventory({ fresh: true, quiet: false })
    .then(() => {
      // "Nothing new" returns without rendering — but the focused view may be
      // showing the honest "isn't in the current inventory" state from before
      // the fetch settled. One final render pins the true outcome.
      if (liveLoaded && focusedCarKey) renderLive();
    })
    .catch(() => { /* load error path already rendered its message */ });
}

function jhClearFocus() {
  focusedCarKey = null;
  history.replaceState(null, '', location.pathname + location.search);
  renderLive();
}

// Share links go to the server-rendered page (backend/site-proxy/src/share.js)
// so they unfurl in forum threads / texts with the car, yard, row and crush
// window — and never carry capacitor://localhost from the native shells.
function shareUrlFor(v) {
  return 'https://yardscout.io/car/' + encodeURIComponent(vehicleKey(v));
}

async function shareVehicle(key) {
  const v = liveInventory.find(x => vehicleKey(x) === key);
  if (!v) return;
  const added = parseYardDate(v.dateAdded);
  const arrived = added
    ? added.toLocaleDateString('en-US', {
        month: 'short', day: 'numeric',
        ...(added.getFullYear() !== new Date().getFullYear() ? { year: 'numeric' } : {}),
      }) : '';
  const bits = [`${v.year} ${v.make} ${v.model}`];
  if (v.row) bits.push(`Row ${v.row}`);
  const text = `${bits.join(' — ')} at ${v.location}${arrived ? ', set out ' + arrived : ''}`;
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

// Part-first search: lowercase query typed in the live-tab toolbar. Filters
// the grid to cars carrying a matching part (name or interchange provenance).
/* Spotted-part name matching — now serves the Parts tab's browse mode (the
 * Live-tab filter it powered was absorbed there, owner decision 2026-10). */
function partQueryHit(p, q) {
  return p.name.toLowerCase().includes(q)
    || (p.sharedWith || '').toLowerCase().includes(q);
}

function getFilteredLive() {
  // Focused shared-find view: show exactly that car, ignoring all filters, so
  // a deep link works for someone with no zip/radius state at all.
  // Matches the share key (vin || id) OR the bare id — alert emails link by
  // id (the scan's arrivals don't carry VINs).
  if (focusedCarKey) {
    const v = liveInventory.find(x => vehicleKey(x) === focusedCarKey || String(x.id) === focusedCarKey);
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
    if (modelFilter && modelFilter.size && !modelFilter.has(canonicalModel(v.make, v.model))) return false;
    if (yearMin && (!v.year || v.year < yearMin)) return false;
    if (yearMax && (!v.year || v.year > yearMax)) return false;
    if (locationFilter && v.location !== locationFilter) return false;
    if (activeZipCoords && radiusMi) {
      const d = vehicleDistanceMi(v);
      if (d == null || d > radiusMi) return false;
    }
    // 'manual' is the only Show option besides All cars. (The old 'valuable
    // parts' option was removed in the Oct 2026 needs-first copy rework —
    // a value-first filter was seller-framing baked into the UI; value info
    // stays on the cards and in the sorts, where it reads as context.)
    // Confirmed from the VIN decode or the yard's own listing — cars with
    // unknown transmission are excluded rather than guessed at (the inline
    // hint under the control says so).
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
    if (v._ts === undefined) v._ts = yardDateMs(v.dateAdded);
    return v._ts;
  };
  const speedRk = s => s === 'Fast' ? 3 : s === 'Medium' ? 2 : s === 'Slow' ? 1 : 0;
  // Fastest-sell ranks by CONFIRMED parts only — an unconfirmed hardtop that
  // "goes fast" (if it exists) must not put the car in the fast band.
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
    case 'date-desc': keyFn = tsOf; break;   // unknown set-out dates (ts 0) land last, not faked
    // Ascending sorts: a missing date/year means "we don't know", never
    // "oldest" — unknowns get a beyond-the-range key so they land LAST.
    // (8.64e15 is the max JS date ms; 9999 clears any real model year.)
    case 'date-asc': keyFn = v => tsOf(v) || 8.64e15; asc = true; break;
    // Closest: cars without coords (or no zip center set — Pro nationwide)
    // key at 1e9 mi, so the date-desc tie-break takes over and the list
    // degrades gracefully to newest arrivals instead of a frozen order.
    case 'dist-asc': { const dOf = v => { const d = vehicleDistanceMi(v); return d == null ? 1e9 : d; }; keyFn = dOf; asc = true; break; }
    case 'year-desc': keyFn = v => v.year || 0; break;   // unknown years land last
    case 'year-asc': keyFn = v => v.year || 9999; asc = true; break;
  }
  const tieFn = tsOf, tieAscEff = tieAsc;
  if (keyFn) {
    const dec = filtered.map(v => [keyFn(v), tieFn(v), v]);
    dec.sort((x, y) => (asc ? x[0] - y[0] : y[0] - x[0])
      || (tieAscEff ? x[1] - y[1] : y[1] - x[1]));
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
  // Radius counts only when moved off the default — the untouched 100 mi
  // ships with the app, so it isn't "a filter the user applied".
  if (activeZipCoords && document.getElementById('live-radius').value !== DEFAULT_RADIUS) n++;
  const el = document.getElementById('live-filter-count');
  el.style.display = n ? 'inline-grid' : 'none';
  el.textContent = n;
}

/* Last-scan stamp for the always-visible "Updated" chip (Live + Yards bars):
 * short relative time in the chip, full timestamp in the hover title. */
function scrapeAgoLabel() {
  if (!liveScrapedAt) return '\u2014';
  const hrs = Math.floor((Date.now() - new Date(liveScrapedAt)) / 3.6e6);
  return hrs < 1 ? 'just now' : hrs < 48 ? `${hrs}h ago` : `${Math.round(hrs / 24)}d ago`;
}
function scrapedTitle() {
  return liveScrapedAt
    ? new Date(liveScrapedAt).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
    : '\u2014';
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
  // "New this week" replaced "Worth a look" (owner request 2026-10-26): with
  // value coverage this broad, worth-a-look counted nearly every car in view
  // — a stat that never changes anyone's plan. Fresh arrivals do.
  const newThisWeek = vehicles.filter(v => isNew(v.dateAdded)).length;

  updateLiveFilterCount();
  updateZipBanner();
  renderSaleStrip();

  // Three chips, no horizontal scroll (owner request 2026-10-24): the old
  // five-chip bar swiped sideways at phone widths and hid "Updated" — the
  // chip people most needed — off the end. Freshness now always visible,
  // which also retired the fresh-stamp line that papered over it.
  document.getElementById('live-stats-bar').innerHTML = `
    <div class="stat-card" title="Cars on the lots in view, as of the last scan"><div class="label">${nearLabel}</div><div class="value">${vehicles.length.toLocaleString()}</div></div>
    <div class="stat-card" title="Cars set out in the last 7 days at the yards in view"><div class="label">New this week</div><div class="value accent">${newThisWeek.toLocaleString()}</div></div>
    <div class="stat-card" title="Last scan: ${scrapedTitle()} — automatic, about every 4 hours"><div class="label">Updated</div><div class="value value-sm">${scrapeAgoLabel()}</div></div>
  `;

  // Shared-link landing: focused single-car view, or an honest message when
  // the shared car has left the inventory.
  if (focusedCarKey) {
    const found = liveInventory.find(x => vehicleKey(x) === focusedCarKey || String(x.id) === focusedCarKey);
    if (!found) {
      document.getElementById('live-grid').innerHTML = `
        <div class="empty-state" style="grid-column:1/-1;">
          <h3>That car isn\u2019t in the current inventory</h3>
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
          <p style="margin-top:1rem;font-size: 0.75rem;">We track every major self-service chain — LKQ Pick Your Part, Pick-n-Pull, and Pull-A-Part — plus a growing set of independents: <span class="coverage-count">${yardCountDisplay()}</span> yards nationwide. Missing your local yard? <a href="mailto:yardscout.io@gmail.com?subject=Add%20my%20yard">Tell us</a>.</p>`;
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
    const setOutDate = parseYardDate(v.dateAdded);
    const dateStr = setOutDate ? setOutDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';
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
        lotClock = `<div class="lot-clock${leavingSoon ? ' lot-clock-soon' : ''}" title="${title}">Day ${daysOn + 1} on the lot &middot; ~${avg} typical ${basisTxt}</div>`;
      }
    }

    // Scan stamp so a screenshot carries when this list was true. The
    // inventory has no per-yard scan time (yard_health.json isn't loaded
    // here), so this is the global scrapedAt in the viewer's local time.
    const scanLine = liveScrapedAt
      ? `<div class="lot-clock scan-stamp" title="When YardScout last scanned the yards — cars can leave between scans">Scanned ${escapeHtml(scrapedTitle())}</div>`
      : '';

    let cardStyle = '', profitLine = '', partsBlock = '';
    if (isMatch && v.topParts && v.topParts.length) {
      let totalCost = 0, lowSum = 0, highSum = 0, unconfirmedHigh = 0, bestPart = null, bestHigh = -Infinity;
      let anyUnknownCost = false;
      const speedRk = s => s === 'Fast' ? 3 : s === 'Medium' ? 2 : s === 'Slow' ? 1 : 0;
      let demandRk = 0;
      const chainLabel = { pnp: 'PnP list', tap: 'TAP list', utpap: 'UTPAP list', pyp: 'PYP list', pap: 'PAP list', wap: 'WAP list', upullr: 'UPR list', budget: 'yard list' };
      const chainTitle = {
        pnp: 'Pick-n-Pull published price',
        tap: 'Tear-A-Part published price',
        utpap: 'Utah Pic-A-Part published price',
        pyp: 'This Pick Your Part yard\u2019s published price',
        pap: 'This Pull-A-Part yard\u2019s published price',
        wap: 'This Wrench-A-Part yard\u2019s published price',
        upullr: 'U-Pull-R Parts published price',
        budget: 'This Budget U-Pull-It yard\u2019s published price',
      };
      // Transmission honesty: the parts DB is model-generation-level, so a
      // manual-only part (shifter, clutch, pedal box) can list on a car that
      // left the factory as an automatic. If this car's own data confirms
      // "Automatic", drop manual-only parts entirely; if the transmission is
      // simply unknown, force them into the "if equipped" bucket.
      const exTrans = (extrasFor(v) || [])[3] ? String(extrasFor(v)[3]) : '';
      const confirmedAuto = /automatic/i.test(exTrans) && !/manual/i.test(exTrans);
      const manualOnly = (p) => /\bmanual\b|clutch/i.test(p.name || '');
      const shownParts = v.topParts.filter((p) => !(confirmedAuto && manualOnly(p)));
      const partRows = shownParts.map((p, pi) => {
        const lookup = lookupYardCost(p.name, v.location);
        const hasCost = lookup.cost != null;
        const yardCost = hasCost ? lookup.cost : 0;
        if (!hasCost) anyUnknownCost = true;
        const pHigh = Math.round(p.high - yardCost);
        // Trim/option-unconfirmed parts ("if equipped") are excluded from the
        // headline range entirely — they're tallied separately and shown as a
        // muted "+ up to $X more if equipped" note, never as promised dollars.
        const ifEquipped = p.trim_status === 'unconfirmed'
          || (manualOnly(p) && !isConfirmedManual(v));
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
          ? `<span class="part-cost" title="${chainTitle[lookup.source]}: ${lookup.yardName || ''}">Yard: ${formatPrice(yardCost)} <small style="opacity:0.65">${chainLabel[lookup.source]}</small></span>`
          : `<span class="part-cost" title="This part isn\u2019t on the yard\u2019s published price list — ask at the counter" style="opacity:0.75;"><small>check yard price list</small></span>`;
        // Buyer's math: the eBay-sold band is what this used part costs to BUY
        // online; the yard's list price is the gate price. The difference is
        // the reader's savings — only shown when the yard cost is real.
        const saveLow = Math.max(0, Math.round(p.low - yardCost));
        const saveHigh = Math.round(p.high - yardCost);
        const saveHtml = hasCost && saveHigh > 0
          ? `<span class="part-save" title="What you\u2019d save over buying this part used online — if the part on this car is good">Save ~${formatPrice(saveLow)}&ndash;${formatPrice(saveHigh)}</span>`
          : '';
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
        const hitCls = '';  // part-hit highlight retired with the Live filter
        // Free tier: everything the parts database produces is blurred —
        // names, fits, values, channels. Real strings never reach the DOM;
        // rows render plausible placeholders so the blur has a shape. The
        // free tease is the count, the demand word, and one sample card.
        if (!unlocked) {
          const ph = LOCKED_PART_PLACEHOLDERS[pi % LOCKED_PART_PLACEHOLDERS.length];
          return `
            <li class="part-item" style="flex-wrap:wrap;">
              <span class="part-name locked-blur" role="button" onclick="openUpgradeSheet('part-name')">${ph}</span>
              <span class="part-cost locked-blur" role="button" onclick="openUpgradeSheet('part-value')">Yard: $\u2022\u2022</span>
              <span class="part-price locked-blur" role="button" onclick="openUpgradeSheet('part-value')">Used online: ${LOCKED_PRICE_MASK}</span>
            </li>`;
        }
        // "Spot it" tell for unconfirmed option parts — the VIN can't confirm
        // an option box was ticked, but nearly every option has a physical
        // tell you can check from outside the car.
        const verifyNote = ifEquipped && p.verify
          ? `<div class="verify-note">Spot it: ${escapeHtml(p.verify)}</div>` : '';
        // Interchange provenance: the same unit (or a bolt-up swap) appears
        // on sibling models — widens the donor pool for buyers searching the
        // sibling's name. The caveat ships verbatim; never trimmed to fit.
        const sharedNote = p.sharedWith
          ? `<div class="shared-note"><span class="shared-badge" title="Platform interchange: hand-verified shared unit across sibling models. Read the caveat and verify part numbers before buying.">swaps with</span>${escapeHtml(p.sharedWith)}</div>` : '';
        return `
          <li class="part-item${hitCls}" style="flex-wrap:wrap;">
            <span class="part-name">${escapeHtml(p.name)}</span>
            ${trimMark}${fitsMark}
            <span class="part-price" title="Typical online price for this used part (eBay sold listings, national) — what you\u2019d pay if you didn\u2019t pull it yourself">Used online: ~${formatPrice(p.low)}&ndash;${formatPrice(p.high)}</span>
            ${costHtml}
            ${saveHtml}
            ${verifyNote}${sharedNote}
            ${sellSpd ? `<div style="width:100%;display:flex;align-items:center;gap:0.4rem;margin-top:0.1rem;flex-wrap:wrap;">
              <span class="sell-badge ${sellCls}" title="How quickly parts like these typically get claimed at the yard">${sellSpd === 'Fast' ? 'Picked over fast' : sellSpd === 'Slow' ? 'Usually still there' : 'Steady demand'}</span>
            </div>` : ''}
          </li>`;
      }).join('');

      // Demand is the primary signal; dollars are a supporting range, never a promise.
      // Only real price-list pull costs are subtracted — when any part isn't on
      // the yard's list, the range is labeled value-only instead of guessing.
      const rangeLow = Math.max(0, Math.round(lowSum * fm));
      const rangeHigh = Math.round(highSum * fm);
      const extraHigh = Math.round(unconfirmedHigh * fm);
      // Demand reads as "how soon should I go", not "how fast it sells":
      // only the two informative states get a label; steady is the default
      // and says nothing.
      const demand = demandRk === 3
        ? { cls: 'demand-fast', label: 'Gets picked over fast' }
        : demandRk === 1
        ? { cls: 'demand-slow', label: 'Usually still there' }
        : { cls: 'demand-steady', label: '' };
      cardStyle = `--tier-color:var(--${demandRk === 3 ? 'demand-fast' : demandRk === 1 ? 'demand-slow' : 'demand-steady'});`;
      const rangeText = anyUnknownCost
        ? `parts worth ~${formatPrice(rangeLow)}&ndash;${formatPrice(rangeHigh)} if bought elsewhere &middot; pull cost: check yard price list`
        : `save ~${formatPrice(rangeLow)}&ndash;${formatPrice(rangeHigh)} vs buying used online, if parts are good &middot; ${formatPrice(Math.round(totalCost))} to pull`;
      // Upside stays visible without misleading: unconfirmed ("if equipped")
      // parts never inflate the headline range — they get a muted second line.
      const extraNote = extraHigh > 0 ? `
        <div class="range-extra" title="Parts specific to a trim or factory option that couldn\u2019t be confirmed for this car &mdash; they add nothing to its ranking or headline value">+ up to ${formatPrice(extraHigh)}${rangeHigh > 0 ? ' more' : ''} if equipped (unconfirmed &mdash; check at the yard)</div>` : '';
      profitLine = (rangeHigh > 0 || extraHigh > 0)
        ? (unlocked ? `
        ${isSampleCard ? '<div class="sample-note" role="button" onclick="openUpgradeSheet(\'sample-note\')">Free sample &mdash; Pro shows this for every car</div>' : ''}
        <div class="profit-line">
          ${demand.label ? `<span class="demand-badge ${demand.cls}" title="How quickly parts like these typically get claimed at the yard">${demand.label}</span>` : ''}
          ${rangeHigh > 0 ? `<span class="range-text">${rangeText}</span>` : ''}
        </div>${extraNote}` : `
        <div class="profit-line">
          ${demand.label ? `<span class="demand-badge ${demand.cls}" title="How quickly parts like these typically get claimed at the yard">${demand.label}</span>` : ''}
          <button type="button" class="lock-chip" onclick="openUpgradeSheet('card-value')">${ICON.lock} What you’d save &mdash; Pro</button>
        </div>`)
        : '';
      partsBlock = `
        <details class="parts-details">
          <summary>${unlocked
            ? `Up to ${shownParts.length} part${shownParts.length > 1 ? 's' : ''} worth a look &middot; top: ${bestPart}`
            : `${shownParts.length} part${shownParts.length > 1 ? 's' : ''} to check`} <span class="chev">${ICON.chev}</span></summary>
          <div class="car-body">
            <div class="ghost-note">These are parts this <strong>model</strong> typically shipped with &mdash; parts tied to a trim, option, or transmission that can\u2019t be confirmed from the VIN are marked &ldquo;if equipped.&rdquo; Yards track cars, not remaining parts, so some may already be pulled; newer arrivals are more likely intact.</div>
            <ul class="parts-list">${partRows}</ul>
            <a class="feedback-link" href="mailto:yardscout.io@gmail.com?subject=YardScout%20feedback">Spot a wrong price or bug? Tell us</a>
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
            <div class="car-name">${escapeHtml(`${v.year} ${v.make} ${v.model}`)}</div>
            <div class="live-card-location">${ICON.pin} <span class="loc-name">${escapeHtml(v.location)}</span>${(() => { const d = vehicleDistanceMi(v); return d != null ? ' <span class="dist">&middot; ' + Math.round(d) + ' mi</span>' : ''; })()}${v.row ? '<span class="live-card-row">Row ' + escapeHtml(v.row) + '</span>' : ''}${saleBadgeHtml(v.location)}</div>
            <div class="car-meta">${dateStr ? `<span title="Set-out date published by the yard">Set out ${dateStr}</span>` : 'Set-out date unknown'}${freshNote}${vinMetaHtml(v)}</div>
            ${specBits.length ? `<div class="car-meta car-specs">${specBits.map(escapeHtml).join(' &middot; ')}</div>` : ''}
            ${lotClock}
            ${scanLine}
          </div>
          <div class="car-badges">
            ${isConfirmedManual(v) ? `<span class="badge badge-manual" title="${transSource(v) === 'listing' ? 'Manual transmission, from the yard\u2019s own listing \u2014 never inferred' : 'Manual transmission, confirmed from this car\u2019s VIN decode \u2014 never inferred'}">Manual</span>` : ''}
            ${statusBadge}
            <button type="button" class="watch-btn ${hasWatchFor(v.make, v.model) ? 'watching' : ''}" data-make="${escapeHtml(v.make || '')}" data-model="${escapeHtml(v.model || '')}" title="${hasWatchFor(v.make, v.model) ? 'Already on your watchlist' : 'Watch this model — get alerted when another shows up'}">${ICON.bell}</button>
            <button type="button" class="share-btn" data-vkey="${escapeHtml(vehicleKey(v))}" title="Share this find">${ICON.share}</button>
            <button type="button" class="heart-btn ${isSaved(v) ? 'saved' : ''}" data-vkey="${escapeHtml(vehicleKey(v))}" title="Save for your yard visit">${ICON.heart}</button>
          </div>
        </div>
        ${profitLine}
        ${partsBlock}
        ${yardSiteLinkHtml(v)}
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
/* Self-heal, same pattern as the jh_sort restore above: a browser's form
 * restore (or an old WebView's saved state) can re-select a match option
 * that no longer exists, leaving the select with no valid choice and the
 * grid filtered by nothing the UI can show. Snap back to All cars. */
(() => {
  const sel = document.getElementById('live-filter-match');
  if (sel.selectedIndex < 0 || ![...sel.options].some(o => o.value === sel.value)) sel.value = '';
})();
document.getElementById('live-filter-match').addEventListener('change', (e) => {
  // The manual option under-counts by design (confirmed-only) — say so right
  // where the choice is made, not in a hover-only tooltip phones never see.
  const hint = document.getElementById('manual-filter-hint');
  if (hint) hint.style.display = e.target.value === 'manual' ? '' : 'none';
  renderLive();
});
// The old spotted-part filter is the Parts tab's browse mode now — the
// drawer keeps only this pointer for anyone who comes looking for it here.
document.getElementById('live-parts-pointer').addEventListener('click', () => {
  document.querySelector(".tab[data-tab='parts']").click();
});
document.getElementById('live-zip').addEventListener('input', e => {
  const val = e.target.value.trim();
  if (val === '') {
    // Cleared on purpose: forget the stored zip too, or it quietly comes
    // back on the next launch while the field shows nothing.
    localStorage.removeItem('jh_zip');
    activeZipCoords = null;
    updateZipBanner();
    renderLive();
    return;
  }
  if (/^\d{5}$/.test(val)) setZipCenter(val);   // partial zips: wait, don't re-render per keystroke
});
document.getElementById('live-radius').addEventListener('change', () => {
  const sel = document.getElementById('live-radius');
  // Widths beyond the free cap ("any distance" and 500 mi) are Pro only.
  // Snap free users back to their previous radius and pitch the upgrade.
  if (!isPro() && (sel.value === '' || parseFloat(sel.value) > FREE_MAX_RADIUS_MI)) {
    const trigger = sel.value === '' ? 'radius-any-distance' : 'radius-' + sel.value + 'mi';
    const prev = localStorage.getItem('jh_radius');
    sel.value = prev && prev !== '' && parseFloat(prev) <= FREE_MAX_RADIUS_MI
      ? prev : String(FREE_MAX_RADIUS_MI);
    openUpgradeSheet(trigger);
    return;
  }
  localStorage.setItem('jh_radius', sel.value);
  renderLive();
});
// Restore saved zip/radius/GPS center across visits
(() => {
  const savedZip = localStorage.getItem('jh_zip') || '';
  let savedRadius = localStorage.getItem('jh_radius');
  // The widest numeric tier is 500 mi now; migrate any older saved value down.
  if (savedRadius !== null && parseInt(savedRadius, 10) > 500) {
    savedRadius = '500';
    localStorage.setItem('jh_radius', savedRadius);
  }
  // Pro-only widths ('' = any distance, 500 mi) migrate down to the widest
  // free radius for free users.
  if (savedRadius !== null && !isPro()
      && (savedRadius === '' || parseInt(savedRadius, 10) > FREE_MAX_RADIUS_MI)) {
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
/* Yards are re-scanned automatically every ~4 hours; this button re-checks
 * for a newer published scan (no-cache fetch + background revalidate). */
document.getElementById('live-refresh-btn').addEventListener('click', async () => {
  const btn = document.getElementById('live-refresh-btn');
  const prev = liveScrapedAt;
  btn.disabled = true;
  const orig = btn.innerHTML;
  btn.innerHTML = 'Checking&hellip;';
  // quiet:false — the user explicitly asked; render whatever arrives.
  try { await loadLiveInventory({ quiet: false }); } catch (e) { /* handled inside */ }
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
  alert("You\u2019re already seeing the latest scan. Yards are re-scanned automatically about every 4 hours." + age);
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
/* Chain-published tool rules (researched from each chain's official yard-rules
 * page, Oct 2026). Chain policy, not location gospel — franchises vary, so the
 * UI always carries a "confirm at the gate" tooltip. Every chain bans torches
 * and jacks; the useful differences are cutting tools. */
const CHAIN_TOOL_POLICY = [
  [/^pick[\s-]*n[\s-]*pull/i, 'Hand & battery tools \u2014 NO sawzalls/body saws'],
  [/pick your part/i, 'Cordless tools incl. sawzall OK \u2014 no grinders or gas tools'],
  [/^pull[\s-]*a[\s-]*part/i, 'Battery tools & small generators OK \u2014 no grinders'],
  [/^tear[\s-]*a[\s-]*part/i, 'Hand & battery tools \u2014 NO sawzalls; compressors OK'],
  [/^fenix[\s-]*u[\s-]*pull/i, 'Battery tools incl. sawzall OK \u2014 no grinders/cutting wheels'],
  [/wrench[\s-]*a[\s-]*part/i, 'Hand & battery tools incl. sawzall OK \u2014 no grinders'],
  [/^harry'?s[\s-]*u[\s-]*pull/i, 'Hand tools only \u2014 NO sawzalls or grinders'],
];

function chainToolPolicy(location) {
  const hit = CHAIN_TOOL_POLICY.find(c => c[0].test(location));
  return hit ? hit[1] : 'Tool rules unpublished \u2014 call before bringing power tools';
}

const CHAIN_PRICE_PAGES = [
  [/^pick[\s-]*n[\s-]*pull/i, 'https://www.picknpull.com/part-pricing', 'Pick-n-Pull'],
  [/^pull[\s-]*a[\s-]*part/i, 'https://www.pullapart.com/used-auto-parts/parts-pricing/', 'Pull-A-Part'],
  [/^tear[\s-]*a[\s-]*part/i, 'https://tearapart.com/price-list/', 'Tear-A-Part'],
  [/pic[\s-]*a[\s-]*part/i, 'https://utpap.com/ogden-prices/', 'Utah Pic-A-Part'],
  // Wrench-A-Part publishes per-location lists; every page carries the same
  // location picker, so the Austin URL works as the chain-wide entry point.
  [/wrench[\s-]*a[\s-]*part/i, 'https://wrenchapart.com/austin-price-list', 'Wrench-A-Part'],
  [/^u[\s-]*pull[\s-]*r/i, 'https://upullrparts.com/part-pricing/', 'U-Pull-R Parts'],
  [/^fenix[\s-]*u[\s-]*pull/i, 'https://fenixupull.com/parts-prices/', 'Fenix U-Pull'],
  [/^harry'?s[\s-]*u[\s-]*pull/i, 'https://wegotused.com/price-list/', "Harry's U-Pull-It"],
  // Joliet's Wix price page only embeds a handful of "popular" prices
  // server-side, so it's link-only (no structured list to parse).
  [/^joliet u[\s-]*pull[\s-]*it/i, 'https://www.jolietupullit.com/auto-part-prices', 'Joliet U-Pull-It'],
  // Go Pull-It's chain list renders client-side only — link-only too.
  [/^go pull[\s-]*it/i, 'https://gopullit.com/parts-price-list/', 'Go Pull-It'],
  [/^195 used auto parts/i, 'https://www.195usedautoparts.com/Home/PartPrices', '195 Used Auto Parts'],
  // The independent San Antonio yard (picknpullsa.com) — NOT picknpull.com.
  [/^san antonio pick[\s-]*n[\s-]*pull/i, 'https://www.picknpullsa.com/price-list', 'San Antonio Pick-N-Pull'],
  // LKQ Pick Your Part publishes prices per location inside its site/app with
  // no stable public price-list URL, so those yards get no link.
];

/* ===== PER-CAR YARD-SITE LINKS (free feature) =====
 * Every car card links to the yard's own site, best-available first:
 *   tier 1 — the exact car's page (photos!): Wrench-A-Part family, Fenix,
 *            Go Pull-It. Verified against live stock/VINs 2026-10.
 *   tier 2 — the yard site's search, pre-filtered to this make/model:
 *            Pick-A-Part VA (path-based), Rupert's (query params). Both
 *            server-rendered GETs, verified 2026-10.
 *   tier 3 — the yard's inventory page (generated map below) so every card
 *            links somewhere sensible.
 *
 * BUSINESS DECISION — Pick-n-Pull: Row52 hosts per-car pages for PnP yards,
 * but Row52 is a direct competitor to this app. PnP deliberately stays tier 3
 * on picknpull.com. Do not "helpfully" add Row52 links.
 * Harry's is tier 3 only: their stock ids get recycled and there are no
 * per-car photos, so a per-car link would routinely show the wrong car. */
/* GEN:YARD_INVENTORY_PAGES:BEGIN (gen_yard_site_links.py) */
const YARD_INVENTORY_PAGES = [
  [/^ez pull n pay - atlanta$/i, 'https://app.autorecycler.io/inventory/ez-pull-n-pay-atlanta'],
  [/^ez pull n pay - stockbridge$/i, 'https://app.autorecycler.io/inventory/ez-pull-n-pay-stockbridge'],
  [/^ez pull n pay - warner robins$/i, 'https://app.autorecycler.io/inventory/ez-pull-n-pay-warner-robins'],
  [/^ez pull n pay - columbus$/i, 'https://app.autorecycler.io/inventory/ez-pull-n-pay-columbus'],
  [/^ez pull n pay - montgomery$/i, 'https://app.autorecycler.io/inventory/ez-pull-n-pay-montgomery'],
  [/^ez pull n pay - decatur$/i, 'https://app.autorecycler.io/inventory/ez-pull-n-pay-decatur'],
  [/^ez pull n pay - birmingham$/i, 'https://app.autorecycler.io/inventory/ez-pull-n-pay-birmingham'],
  [/^foss u-pull-it - winston-salem$/i, 'https://app.autorecycler.io/inventory/foss-winston-salem'],
  [/^foss u-pull-it - jacksonville$/i, 'https://app.autorecycler.io/inventory/foss-jacksonville'],
  [/^foss u-pull-it - la grange$/i, 'https://app.autorecycler.io/inventory/foss-la-grange'],
  [/^foss u-pull-it - chesapeake$/i, 'https://app.autorecycler.io/inventory/foss-recycling'],
  [/^foss u-pull-it - wilson$/i, 'https://app.autorecycler.io/inventory/foss-wilson'],
  [/^foss u-pull-it - havelock$/i, 'https://app.autorecycler.io/inventory/foss-havelock'],
  [/^uapi - north shreveport$/i, 'https://app.autorecycler.io/inventory/uapi'],
  [/^uapi - south shreveport$/i, 'https://app.autorecycler.io/inventory/uapi-south-shreveport'],
  [/^uapi - bossier city$/i, 'https://app.autorecycler.io/inventory/uapi-bossier-city'],
  [/^uapi - monroe$/i, 'https://app.autorecycler.io/inventory/uapi-monroe'],
  [/^uapi - alexandria$/i, 'https://app.autorecycler.io/inventory/uapi-alexandria'],
  [/^uapi - texarkana$/i, 'https://app.autorecycler.io/inventory/uapi-texarkana'],
  [/^auto parts u pull - shelby$/i, 'https://app.autorecycler.io/inventory/auto-parts-u-pull-shelby-nc'],
  [/^auto parts u pull - lincolnton$/i, 'https://app.autorecycler.io/inventory/auto-parts-u-pull-nc'],
  [/^l and l u-pull auto parts$/i, 'https://app.autorecycler.io/inventory/l-and-l-u-pull'],
  [/^a & a auto recycling$/i, 'https://app.autorecycler.io/inventory/a-a-auto-recycling'],
  [/^samson auto salvage$/i, 'https://app.autorecycler.io/inventory/samson-auto-salvage'],
  [/^utah pic-a-part - ogden \(premium\)/i, 'https://utpap.com/ogden-premium-inventory/'],
  [/^utah pic-a-part - ogden/i, 'https://utpap.com/ogden-inventory/'],
  [/^utah pic-a-part - orem \(premium\)/i, 'https://utpap.com/orem-premium-inventory/'],
  [/^utah pic-a-part - orem/i, 'https://utpap.com/orem-inventory/'],
  [/^budget u-pull-it - bartow/i, 'http://budgetupullit.s3softwaresolutions.com/inventory.aspx'],
  [/^pick[\s-]*n[\s-]*pull/i, 'https://www.picknpull.com/check-inventory'],
  [/^pick your part/i, 'https://www.pyp.com/inventory/'],
  [/^pull[\s-]*a[\s-]*part/i, 'https://www.pullapart.com/used-auto-parts/search-car-inventory/'],
  [/^tear[\s-]*a[\s-]*part/i, 'https://tearapart.com/inventory/'],
  [/wrench[\s-]*a[\s-]*part/i, 'https://wrenchapart.com/vehicle-search.html'],
  [/^fenix/i, 'https://fenixupull.com/recent-inventory/'],
  [/^go pull[\s-]*it/i, 'https://gopullit.com/inventory/'],
  [/^pull[\s-]*n[\s-]*save/i, 'https://www.pullnsave.com/inventory-search/'],
  [/^parts galore/i, 'https://parts-galore.com/'],
  [/^sturtevant/i, 'https://inventory.sturtevantauto.com/'],
  [/^ace pick/i, 'https://acepickapart.com/search-inventory/'],
  [/^harry'?s/i, 'https://wegotused.com/our-inventory/'],
  [/^indy[\s-]*u[\s-]*pull/i, 'https://indyupullit.com/vehicle-inventory/'],
  [/^u[\s-]*pull[\s-]*it\b/i, 'https://upullitne.com/search-inventory/'],
  [/^rupert/i, 'https://rupertsupullit.com/search-our-inventory/'],
  [/^chesterfield/i, 'https://chesterfieldauto.com/search-our-inventory-by-location'],
  [/^ipull/i, 'https://ipullupull.com/inventory-pricing/'],
  [/^st\.?\s*cloud/i, 'https://stccrush.com/Home/Inventory'],
  [/^pick-a-part va/i, 'https://pickapartva.com/inventory/ANY/ANY/?k=1'],
  [/^nevada pic/i, 'https://www.nvpap.com/'],
  [/^bessler/i, 'https://vinplus.texnrewards.com/road-tested-parts'],
  [/^bluegrass/i, 'https://vinplus.texnrewards.com/road-tested-parts'],
  [/^raceway/i, 'https://vinplus.texnrewards.com/road-tested-parts'],
  [/^rtp\b/i, 'https://vinplus.texnrewards.com/road-tested-parts'],
  [/^pickers\b/i, 'https://vinplus.texnrewards.com/pickers-longview'],
  [/^pipes\b/i, 'https://vinplus.texnrewards.com/pickers-longview'],
  [/^joliet u[\s-]*pull[\s-]*it/i, 'https://www.jolietupullit.com/inventory'],
  [/^san antonio pick[\s-]*n[\s-]*pull/i, 'https://www.picknpullsa.com/inventory'],
  [/^195 used auto parts/i, 'https://www.195usedautoparts.com/Home/Inventory'],
  [/^pick ur part/i, 'https://pickurpart.com/inventory/'],
  [/^u[\s-]*pick[\s-]*it az/i, 'https://upickitaz.com/'],
  [/^barry'?s/i, 'https://barrysupullit.net/vehicle-inventory-2/'],
  [/^prestige/i, 'https://prestigepullyourpart.com/vehicle-search/'],
  [/^budget/i, 'https://budgetupullit.com/current-inventory/'],
  [/^ryan'?s pick/i, 'https://ryanspickapart.com/Home/Inventory'],
  [/^us auto supply/i, 'https://usautosupplymi.com/inventory/'],
  [/^u[\s-]*pull and save/i, 'https://www.u-pullandsave.com/used-car-parts'],
];
/* GEN:YARD_INVENTORY_PAGES:END */

/** Best link into the yard's own site for this car: {url, tier} (never null
 *  for a yard the scraper covers — tier 3 is validated against every yard). */
function yardPageUrl(v) {
  const loc = v.location || '';
  const id = String(v.id || '');
  // Tier 1 — per-car pages. Fenix/Go Pull-It ids are "chain-{stock}" where
  // {stock} is the yard site's own URL key; Wrench-A-Part keys photos by VIN.
  if (/wrench[\s-]*a[\s-]*part/i.test(loc) && v.vin) {
    return { url: `https://wrenchapart.com/vehicle-search?photo=${encodeURIComponent(v.vin)}`, tier: 1 };
  }
  if (id.startsWith('fenix-')) {
    // ?setLocation={city-state} is what the site's own location-gate buttons
    // use — without it, first-time visitors get a "select your location"
    // interstitial that drops the deep link (verified 2026-10).
    const slug = (v.city && v.state)
      ? `?setLocation=${encodeURIComponent(v.city.toLowerCase().replace(/[^a-z0-9]+/g, '-') + '-' + v.state.toLowerCase())}`
      : '';
    return { url: `https://fenixupull.com/inventory/${encodeURIComponent(id.slice(6))}/${slug}`, tier: 1 };
  }
  if (id.startsWith('gopullit-')) {
    return { url: `https://gopullit.com/inventory/${encodeURIComponent(id.slice(9))}/`, tier: 1 };
  }
  // U-Pull and Save (Pontiac MI): ids are "upas-{vehicleID}" and the site
  // serves a public per-car page at /vehicles/{vehicleID}.
  if (id.startsWith('upas-')) {
    return { url: `https://www.u-pullandsave.com/vehicles/${encodeURIComponent(id.slice(5))}`, tier: 1 };
  }
  // Tier 2 — make-filtered search on the yard's site. Deliberately make-ONLY:
  // our model strings are canonicalized (normalize_model in the scraper, e.g.
  // F150 -> F-150, SSERIES -> S-Series) and no longer match these sites'
  // native model names exactly, so a model-filtered link can land on a
  // misleading "no results" page. A make-filtered list always shows the car.
  if (/^pick-a-part va/i.test(loc) && v.make) {
    return {
      url: `https://pickapartva.com/inventory/${encodeURIComponent(v.make.toUpperCase())}/ANY/?k=1`,
      tier: 2,
    };
  }
  if (/^rupert/i.test(loc) && v.make) {
    return {
      url: `https://rupertsupullit.com/search-our-inventory/?make=${encodeURIComponent(v.make.toUpperCase())}&model=all&year_start=1963&year_end=2026`,
      tier: 2,
    };
  }
  // Tier 3 — the yard's inventory page.
  const hit = YARD_INVENTORY_PAGES.find(c => c[0].test(loc));
  return hit ? { url: hit[1], tier: 3 } : null;
}

/** The quiet link line at the bottom of a car card ('' when yard unknown). */
function yardSiteLinkHtml(v) {
  const link = yardPageUrl(v);
  if (!link) return '';
  const label = link.tier === 1 ? "View on yard\u2019s site" : "Find it on the yard\u2019s site";
  const title = link.tier === 1
    ? 'Opens this exact car on the yard\u2019s own website'
    : link.tier === 2
    ? 'Opens the yard\u2019s website, searched for this make and model'
    : 'Opens the yard\u2019s own inventory page';
  return `<div class="yard-site-line"><a class="yard-site-link" href="${escapeHtml(link.url)}" target="_blank" rel="noopener" title="${title}">${label} &#8599;</a></div>`;
}

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
 * The scan runs every 4 hours; if the newest data is older than a day,
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

/** Chain display name for a yard ("Pick-n-Pull - Salt Lake City" -> "Pick-n-Pull").
 *  The Wrench-A-Part family trades under per-yard prefixes (Primo, Roosevelt,
 *  ...) but shares one brand, site, and price-list source — group them. */
function yardChainName(location) {
  if (/wrench[\s-]*a[\s-]*part/i.test(location)) return 'Wrench-A-Part family';
  const i = location.indexOf(' - ');
  return i > 0 ? location.slice(0, i) : location;
}

/** One source of truth for "the yards you're looking at": distance-sorted
 *  directory, radius cap, then this tab's chain/state/text filters. The yard
 *  grid, the part type-ahead, and the cross-yard price compare all read the
 *  same view — compare answers "across the yards I care about", not the world.
 *  Requires activeZipCoords (callers check). */
function getYardsView() {
  const yards = buildYardDirectory();
  const allCount = yards.length;
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
  const chain = document.getElementById('yards-filter-chain').value;
  const state = document.getElementById('yards-filter-state').value;
  const q = (document.getElementById('yards-search').value || '').trim().toLowerCase();
  let shown = inRange;
  if (chain) shown = shown.filter(y => yardChainName(y.location) === chain);
  if (state) shown = shown.filter(y => y.state === state);
  if (q) shown = shown.filter(y => (y.location + ' ' + y.city + ' ' + y.state).toLowerCase().includes(q));
  return { yards, allCount, radius, inRange, shown, filtered: !!(chain || state || q) };
}

/* Chain/state options reflect the yards in range; the current selection is
 * kept when still present so re-renders don't wipe an active filter. */
function populateYardFilters(inRange) {
  const chains = new Map();
  const states = new Map();
  for (const y of inRange) {
    const c = yardChainName(y.location);
    chains.set(c, (chains.get(c) || 0) + 1);
    if (y.state) states.set(y.state, (states.get(y.state) || 0) + 1);
  }
  const rebuild = (id, map, allLabel) => {
    const sel = document.getElementById(id);
    const prev = sel.value;
    sel.innerHTML = `<option value="">${allLabel}</option>` + [...map.keys()].sort()
      .map(k => `<option value="${escapeHtml(k)}">${escapeHtml(k)} (${map.get(k)})</option>`).join('');
    if (prev && map.has(prev)) sel.value = prev;
  };
  rebuild('yards-filter-chain', chains, 'All chains');
  rebuild('yards-filter-state', states, 'All states');
}

function renderYards() {
  const grid = document.getElementById('yards-grid');
  const statsBar = document.getElementById('yards-stats-bar');
  // This tab's Within select and zip mirror the Live tab's (one stored
  // radius/center, one free cap, one Pro gate) — resync so they never
  // disagree. The zip is left alone while the user is typing in it.
  document.getElementById('yards-radius').value = document.getElementById('live-radius').value;
  const yz = document.getElementById('yards-zip');
  const lz = document.getElementById('live-zip');
  if (document.activeElement !== yz) {
    yz.value = lz.value;
    yz.placeholder = lz.placeholder;   // carries 'Using your location' when GPS is the center
  }
  updateYardsFilterCount();
  if (!liveLoaded) {
    grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1;"><p>Loading live inventory&hellip;</p></div>';
    statsBar.innerHTML = '';
    return;
  }

  // Compare needs a center too — hide the bar until a ZIP is set so the
  // fresh-visitor view is just the locate prompt.
  document.getElementById('price-compare-bar').style.display = activeZipCoords ? '' : 'none';

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

  let view = getYardsView();
  // Rebuilding the filter options can drop a selection whose chain/state left
  // the radius — recompute the view so the grid matches the (reset) selects.
  const fChain = document.getElementById('yards-filter-chain');
  const fState = document.getElementById('yards-filter-state');
  const prevChain = fChain.value, prevState = fState.value;
  populateYardFilters(view.inRange);
  if (fChain.value !== prevChain || fState.value !== prevState) view = getYardsView();
  const { radius, inRange, shown } = view;

  // Three chips, no horizontal scroll (owner request 2026-10-24): the old
  // bar truncated "Tracked nationwide" and swiped sideways on phones. The
  // radius lives in the Within select and the nationwide count in the
  // footer coverage note — the chips now carry yards, cars, and freshness.
  const chipYards = view.filtered ? shown : inRange;
  const carsInView = chipYards.reduce((s, y) => s + (y.count || 0), 0);
  statsBar.innerHTML = `
    <div class="stat-card" title="Yards ${view.filtered ? 'matching your filters' : 'inside your radius'}${radius ? ` — within ${radius} mi` : ''}"><div class="label">${view.filtered ? 'Yards in view' : 'Yards near you'}</div><div class="value">${chipYards.length.toLocaleString()}</div></div>
    <div class="stat-card" title="Cars on those lots as of the last scan"><div class="label">${view.filtered ? 'Cars in view' : 'Cars in range'}</div><div class="value">${carsInView.toLocaleString()}</div></div>
    <div class="stat-card" title="Last scan: ${scrapedTitle()} — every yard re-scanned about every 4 hours"><div class="label">Updated</div><div class="value value-sm">${scrapeAgoLabel()}</div></div>
  `;

  if (!shown.length) {
    if (!inRange.length) {
      const nearest = view.yards.find(y => y.dist != null);
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
      grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1;"><h3>No yards match</h3><p>Try a different name, or clear the chain/state filters above.</p></div>';
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
            <div class="lot-clock" title="Chain-published rule — individual locations can differ; torches and jacks are banned everywhere. Confirm at the gate before a long drive.">${ICON.tag} Tools: ${chainToolPolicy(y.location)}</div>
          </div>
        </div>
        <div class="yard-actions">
          <button type="button" class="btn yard-view-btn">View cars</button>
          ${yardPriceList(y.location)
            ? '<button type="button" class="btn yard-prices-btn">' + ICON.tag + ' Price list</button>'
            : (chain ? `<a class="yard-price-link" href="${chain[1]}" target="_blank" rel="noopener">${chain[2]} price list</a>` : '<span class="yard-price-none">Prices posted at the yard</span>')}
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
  if (!card) return;
  if (e.target.closest('.yard-prices-btn')) { openYardPrices(card.dataset.loc); return; }
  viewYardInLive(card.dataset.loc);
});
document.getElementById('yards-grid').addEventListener('keydown', e => {
  if (e.key !== 'Enter') return;
  const card = e.target.closest('.yard-card');
  if (card) viewYardInLive(card.dataset.loc);
});
document.getElementById('yards-search').addEventListener('input', () => renderYards());
/* Filters drawer — same handle/panel mechanics as the Live tab, with its own
 * remembered open state. Default is CLOSED on first paint (no half-open
 * illusion in the iOS webview — see the Live tab's 'Show' filter saga). */
document.getElementById('yards-filter-toggle').addEventListener('click', () => {
  const panel = document.getElementById('yards-controls');
  const btn = document.getElementById('yards-filter-toggle');
  const open = panel.classList.toggle('open');
  btn.classList.toggle('open', open);
  localStorage.setItem('jh_yards_filters_open', open ? '1' : '0');
});
if (localStorage.getItem('jh_yards_filters_open') === '1') {
  document.getElementById('yards-controls').classList.add('open');
  document.getElementById('yards-filter-toggle').classList.add('open');
}
/* Active-filter badge on the drawer handle — mirrors updateLiveFilterCount. */
function updateYardsFilterCount() {
  let n = 0;
  if (document.getElementById('yards-search').value.trim()) n++;
  if (document.getElementById('yards-filter-chain').value) n++;
  if (document.getElementById('yards-filter-state').value) n++;
  // Same default-aware radius rule as updateLiveFilterCount: the shipped
  // 100 mi doesn't count, a user-changed radius does.
  if (activeZipCoords && document.getElementById('yards-radius').value !== DEFAULT_RADIUS) n++;
  const el = document.getElementById('yards-filter-count');
  el.style.display = n ? 'inline-grid' : 'none';
  el.textContent = n;
}
/* Yards-tab distance control: same stored value, same free 250 mi cap, and
 * the same Pro gate as the Live tab's radius select — "any distance" snaps
 * free users back and pitches honestly, identical trigger and prompt. */
document.getElementById('yards-radius').addEventListener('change', e => {
  const sel = e.target;
  if (!isPro() && (sel.value === '' || parseFloat(sel.value) > FREE_MAX_RADIUS_MI)) {
    const trigger = sel.value === '' ? 'radius-any-distance' : 'radius-' + sel.value + 'mi';
    // Snap back to the radius actually in effect (the Live select is the
    // source of truth), so the two selects and the stats bar keep agreeing.
    sel.value = document.getElementById('live-radius').value || String(FREE_MAX_RADIUS_MI);
    openUpgradeSheet(trigger);
    return;
  }
  document.getElementById('live-radius').value = sel.value;
  localStorage.setItem('jh_radius', sel.value);
  renderYards();
});
/* Yards-tab zip: the same geocoder and stored center as the Live tab's zip
 * input (setZipCenter) — one implementation, two entry points. */
document.getElementById('yards-zip').addEventListener('input', async e => {
  const v = e.target.value.trim();
  document.getElementById('live-zip').value = v;
  await setZipCenter(v);
  updateZipBanner();
  renderYards();
});

/* ===== YARD PRICE LISTS & CROSS-YARD COMPARE =====
 * Every chain's published price list, browsable in-app so nobody has to dig
 * through nine junkyard websites. Both the per-yard list AND the cross-yard
 * compare are free: it's the yards' own published data, and the compare only
 * reads the same lists the free Price list buttons already show. */

/** Normalized [{part, price, core}] for a yard, or null when the chain
 *  doesn't publish a scrapeable list (e.g. LKQ posts prices in-store only). */
function yardPriceList(location) {
  const loc = (location || '').toLowerCase();
  const fromList = obj => Object.values(obj).map(p => ({
    part: p.description, price: parseFloat(p.price), core: parseFloat(p.corePrice || 0),
  }));
  const fromDict = d => d ? Object.entries(d).map(([k, v]) => ({
    part: k, price: v.price, core: v.core || 0,
  })) : null;
  let rows = null;
  if (loc.startsWith('pick-n-pull')) rows = fromList(pnpPricing);
  else if (loc.startsWith('tear-a-part')) rows = fromList(tapPricing);
  else if (loc.startsWith('utah pic-a-part')) rows = fromList(utpapPricing);
  else if (loc.startsWith('u-pull-r')) rows = fromList(upullrPricing);
  else if (loc.startsWith("harry's u-pull-it")) rows = fromList(harrysPricing);
  else if (loc.startsWith('indy-u-pull-it')) rows = fromList(indyPricing);
  else if (loc.startsWith("rupert's u-pull-it")) rows = fromList(rupertsPricing);
  else if (loc.startsWith('u-pull-it')) rows = fromList(upullitnePricing);
  else if (loc.startsWith('pull-n-save')) rows = fromList(pnsPricing);
  else if (loc.startsWith('parts galore')) rows = fromList(partsgalorePricing);
  else if (loc.startsWith('chesterfield auto parts')) rows = fromList(chesterfieldPricing);
  else if (loc.startsWith('ace pick-a-part')) rows = fromList(acePricing);
  else if (loc.startsWith('sturtevant auto')) rows = fromList(sturtevantPricing);
  else if (loc.startsWith('nevada pic-a-part')) rows = fromList(nvpapPricing);
  else if (loc.startsWith("barry's u pull it")) rows = fromList(barrysPricing);
  else if (loc.startsWith('195 used auto parts')) rows = fromList(p195Pricing);
  // The independent San Antonio yard — NOT the Pick-n-Pull chain (whose
  // startsWith('pick-n-pull') branch above can never match this name).
  else if (loc.startsWith('san antonio pick-n-pull')) rows = fromList(pnpsaPricing);
  else if (loc.startsWith("ryan's pick-a-part")) rows = fromList(ryansPricing);
  else if (loc.startsWith('us auto supply')) rows = fromList(usautoPricing);
  // Must not collide with the startsWith('u-pull-it') NE branch above —
  // "u-pull and save" shares only the "u-pull" prefix, not "u-pull-it".
  else if (loc.startsWith('u-pull and save')) rows = fromList(upasPricing);
  else if (loc.startsWith('budget u-pull-it')) rows = fromDict(budgetPricing[location]);
  else if (loc.startsWith('pick your part')) rows = fromDict(pypPricing[location]);
  else if (loc.startsWith('pull-a-part')) rows = fromDict(papPricing[location]);
  else if (loc.includes('wrench-a-part')) rows = fromDict(wapPricing[location]);
  else if (loc.startsWith('fenix u-pull')) rows = fromDict(fenixPricing[location]);
  if (!rows || !rows.length) return null;
  rows = rows.filter(r => r.part && isFinite(r.price));
  rows.sort((a, b) => a.part.localeCompare(b.part));
  return rows.length ? rows : null;
}

let pricesSheetRows = null;   // rows currently in the sheet (yard mode)
let pricesSheetMode = 'yard'; // 'yard' | 'compare'

function priceRowHtml(r) {
  const core = r.core > 0
    ? ` <span class="price-core" title="Refundable core deposit — bring the old part back to get it refunded">+ $${r.core.toFixed(2)} core</span>` : '';
  return `<div class="price-row"><span class="price-part">${escapeHtml(r.part)}</span><span class="price-amt">$${r.price.toFixed(2)}${core}</span></div>`;
}

function renderPricesSheetRows() {
  const body = document.getElementById('prices-body');
  const q = (document.getElementById('prices-search').value || '').trim().toLowerCase();
  const rows = q ? pricesSheetRows.filter(r => r.part.toLowerCase().includes(q)) : pricesSheetRows;
  body.innerHTML = rows.length
    ? rows.map(priceRowHtml).join('')
    : '<div class="empty-state"><p>No parts match. The chain may list it under a different name &mdash; try a shorter word.</p></div>';
}

function openYardPrices(location) {
  const rows = yardPriceList(location);
  if (!rows) return;
  track('price-list-opened');
  pricesSheetMode = 'yard';
  pricesSheetRows = rows;
  document.getElementById('prices-title').textContent = location;
  const chain = CHAIN_PRICE_PAGES.find(c => c[0].test(location));
  document.getElementById('prices-sub').innerHTML =
    `${rows.length} parts on the published list.` +
    (chain ? ` <a href="${chain[1]}" target="_blank" rel="noopener">View on ${escapeHtml(chain[2])}'s site</a>` : '');
  document.getElementById('prices-search-wrap').style.display = '';
  document.getElementById('prices-sort-wrap').style.display = 'none';
  document.getElementById('prices-search').value = '';
  renderPricesSheetRows();
  document.getElementById('prices-sheet').classList.add('open');
  document.getElementById('prices-backdrop').classList.add('open');
}

/** One yard's take on a part: the cheapest list row whose name contains any
 *  of the query's name variants (merged spellings like "tail light" /
 *  "taillight" travel together) — a part can hit several rows; the cheapest
 *  is what you'd pay at the counter — else the PART_KEYWORD_MAP mapping, so a
 *  common word ("headlight") still lands on chains that spell it differently
 *  ("HEADLAMP COMPOSITE"). Memoized: the combobox counts call this a lot. */
const _partQuoteMemo = new Map();
function yardPartQuote(location, variants) {
  const key = variants.map(v => Array.isArray(v) ? v.join('\u0002') : v).join('\u0001') + '|' + location;
  let hit = _partQuoteMemo.get(key);
  if (hit === undefined) {
    hit = _yardPartQuoteUncached(location, variants);
    _partQuoteMemo.set(key, hit);
  }
  return hit;
}
function _yardPartQuoteUncached(location, variants) {
  const rows = yardPriceList(location);
  if (!rows) return { status: 'no-list' };
  // Variants are ORDERED by specificity (PART_CATALOG_SPEC §6.3): the first
  // variant with any hit wins, cheapest row within THAT variant only. A "="
  // prefix demands an exact row-name match — "=door" prices a row named
  // DOOR without also sweeping up DOOR HANDLE, the old cheapest-substring
  // hazard that quoted a $9 handle as the price of a door. An ARRAY variant
  // is one tier of synonymous names (a curated alias group's raw spellings):
  // cheapest hit across the whole tier wins together.
  let best = null;
  for (const v of variants) {
    for (const tv of (Array.isArray(v) ? v : [v])) {
      const exact = tv.charAt(0) === '=';
      const needle = exact ? tv.slice(1) : tv;
      for (const r of rows) {
        const pl = r.part.toLowerCase();
        const hit = exact ? pl.trim() === needle : pl.includes(needle);
        if (hit && (!best || r.price < best.price)) best = r;
      }
    }
    if (best) break;
  }
  if (!best) {
    for (let v of variants) {
      if (Array.isArray(v)) v = v[0];
      const kw = lookupYardCost(v.charAt(0) === '=' ? v.slice(1) : v, location);
      if (kw.cost != null) {
        // Recover the full row (core charge) behind the keyword-map name.
        best = rows.find(r => r.part === kw.yardName) || { part: kw.yardName, price: kw.cost, core: 0 };
        break;
      }
    }
  }
  return best
    ? { status: 'priced', part: best.part, price: best.price, core: best.core || 0 }
    : { status: 'not-listed' };
}

/* Compare state: results re-sort client-side (cheapest/nearest toggle). */
let compareResults = [];
let compareMissing = [];  // yards with a published list but no row for the query
let compareNoList = 0;    // yards in view with no published list at all
let compareSort = 'price';

function renderCompareResults() {
  const sorted = [...compareResults].sort(compareSort === 'dist'
    ? (a, b) => (a.dist ?? 1e9) - (b.dist ?? 1e9)
    : (a, b) => a.price - b.price);
  const rows = sorted.map(r => {
    const core = r.core > 0 ? ` <span class="price-core" title="Refundable core deposit — bring the old part back to get it refunded">+ $${r.core.toFixed(2)} core</span>` : '';
    const dist = r.dist != null ? ` &middot; ${Math.round(r.dist)} mi` : '';
    return `<div class="price-row compare-row" data-loc="${escapeHtml(r.yard)}" role="button" tabindex="0">
      <span class="price-part"><strong>${escapeHtml(r.yard)}</strong><br>
        <span class="compare-detail">${escapeHtml(r.part)}${dist}</span></span>
      <span class="price-amt">$${r.price.toFixed(2)}${core}</span>
    </div>`;
  }).join('');
  let extra = '';
  if (compareMissing.length) {
    const names = compareMissing.slice(0, 8).map(y =>
      y.dist != null ? `${escapeHtml(y.location)} (${Math.round(y.dist)} mi)` : escapeHtml(y.location));
    const more = compareMissing.length > 8 ? ` +${compareMissing.length - 8} more` : '';
    extra += `<div class="compare-missing">Not on the published list at ${names.join(', ')}${more} &mdash; ask at the counter.</div>`;
  }
  if (compareNoList) {
    extra += `<div class="compare-missing">${compareNoList} yard${compareNoList === 1 ? '' : 's'} in view post${compareNoList === 1 ? 's' : ''} prices at the yard only &mdash; no published list to read.</div>`;
  }
  document.getElementById('prices-body').innerHTML =
    (rows || '<div class="empty-state"><p>No published price for that part at the yards in view. Chains list parts under category names &mdash; try a broader word like "seat" or "door", or clear a chain/state filter.</p></div>') + extra;
}

/** Free: one search, every visible yard's published price for that part.
 *  Respects the tab's chain/state/text filters and the distance control —
 *  "compare across the yards YOU care about", reading only the same published
 *  price lists the free Price list buttons already show. */
function openPriceCompare(query) {
  if (!activeZipCoords) { alert('Set a zip code first so we know which yards are near you.'); return; }
  const q = query.trim().toLowerCase();
  if (q.length < 3) return;
  track('price-compare');

  const { shown } = getYardsView();
  // Merged spelling variants compare as one part: a pick of "Tail Light"
  // must still price yards whose list spells it "TAILLIGHT". Curated alias
  // groups carry a dedicated exact-name quote tier (never substrings).
  const entry = getPartIndex().byName.get(q);
  const variants = entry ? (entry.quote || entry.names) : [q];
  // UTPAP's premium-row sections appear as separate "(Premium)" yards in the
  // directory but share the base yard's price list — keep one per real yard.
  const seen = new Set();
  compareResults = []; compareMissing = []; compareNoList = 0;
  for (const y of shown) {
    const key = y.location.replace(/\s*\(premium\)\s*$/i, '');
    if (seen.has(key)) continue;
    seen.add(key);
    const quote = yardPartQuote(y.location, variants);
    if (quote.status === 'priced') {
      compareResults.push({ yard: y.location, dist: y.dist, part: quote.part, price: quote.price, core: quote.core });
    } else if (quote.status === 'not-listed') {
      compareMissing.push(y);
    } else {
      compareNoList++;
    }
  }

  pricesSheetMode = 'compare';
  document.getElementById('prices-title').textContent = `"${query.trim()}" across yards in view`;
  document.getElementById('prices-sub').textContent = compareResults.length
    ? `Prices from each yard\u2019s own published price list \u2014 ${compareResults.length} of ${seen.size} yard${seen.size === 1 ? '' : 's'} in view publish${compareResults.length === 1 ? 'es' : ''} this part.`
    : '';
  document.getElementById('prices-search-wrap').style.display = 'none';
  document.getElementById('prices-sort-wrap').style.display = compareResults.length > 1 ? '' : 'none';
  renderCompareResults();
  document.getElementById('prices-sheet').classList.add('open');
  document.getElementById('prices-backdrop').classList.add('open');
}

function setCompareSort(s) {
  compareSort = s;
  document.getElementById('prices-sort-price').classList.toggle('active', s === 'price');
  document.getElementById('prices-sort-dist').classList.toggle('active', s === 'dist');
  renderCompareResults();
}
document.getElementById('prices-sort-price').addEventListener('click', () => setCompareSort('price'));
document.getElementById('prices-sort-dist').addEventListener('click', () => setCompareSort('dist'));

function closePricesSheet() {
  document.getElementById('prices-sheet').classList.remove('open');
  document.getElementById('prices-backdrop').classList.remove('open');
}
document.getElementById('prices-close').addEventListener('click', closePricesSheet);
document.getElementById('prices-backdrop').addEventListener('click', closePricesSheet);
document.getElementById('prices-search').addEventListener('input', () => {
  if (pricesSheetMode === 'yard') renderPricesSheetRows();
});
document.getElementById('prices-body').addEventListener('click', e => {
  const row = e.target.closest('.compare-row');
  if (row) { closePricesSheet(); viewYardInLive(row.dataset.loc); }
});
/* ===== PART TYPE-AHEAD =====
 * Suggestions come from two pools: every part name on the visible yards'
 * published lists, plus the canonical PART_KEYWORD_MAP keywords (so 'headlight'
 * suggests even when every chain spells it 'HEADLAMP ...'). Each suggestion
 * shows how many visible yards publish it. Rebuilt lazily when the yard view
 * (filters / radius / zip) changes. */
let _partIndex = null;
let _partIndexSig = '';

function titleCasePart(s) {
  // Some chains' raw lists carry stray leading punctuation ('.VALVE COVER-');
  // clean it for display so junk doesn't sort to the top of the browse list.
  return s.replace(/^[^a-zA-Z0-9]+/, '').replace(/\s+/g, ' ').trim()
    .toLowerCase().replace(/(^|[^a-z0-9])([a-z])/g, (m, pre, c) => pre + c.toUpperCase());
}

/* Scraper parse artifacts: a handful of price-list rows ship the PRICE as the
 * part name ("5.00" — Barry's U Pull It list), and Chesterfield's list carries
 * "...we do not sell" disclaimer rows. Neither belongs in the picker. */
const JUNK_PART_NAME = /^[\s\d.,$-]+$/;
const JUNK_PART_PHRASE = /we do not sell/i;

/* ===== CANONICAL PART-NAME MERGING (the make/model-normalization pattern,
 * applied to the chains' raw price-sheet spellings) =====
 *
 * partMergeKey folds TRUE spelling variants of one physical part into one
 * compare entry: punctuation, word order ("spring, coil" = "coil spring"),
 * singular/plural, filler words ("(each)", "any", "misc"), and the chains'
 * stock abbreviations (HOUS→housing, ASSY→assembly, ELEC→electric, W/→with).
 * Genuinely different parts keep different keys because their CONTENT tokens
 * differ — "air cleaner lid" never folds into "air cleaner housing".
 * Every rule below was audited against the full ~7,200-name corpus across
 * all wired price lists (see tools/check_part_aliases.py); where a fold was
 * ambiguous it was NOT added — honest fragmentation beats wrong unification. */
const PART_FILLER_TOKENS = new Set([
  'each', 'any', 'only', 'misc', 'oem', 'per', 'type', 'style',
  'the', 'of', 'or', 'and', 'ea', 's', 'n',
]);
const PART_TOKEN_ABBR = {
  // chain abbreviations (verified against the lists that use them)
  assy: 'assembly', hous: 'housing', housng: 'housing', alum: 'aluminum',
  elec: 'electric', elect: 'electric', elctric: 'electric', electrc: 'electric',
  cyl: 'cylinder', trans: 'transmission', mtr: 'motor', moto: 'motor',
  pwr: 'power', cvr: 'cover', cntrl: 'control', ctrl: 'control',
  sml: 'small', sm: 'small', lrg: 'large', lg: 'large', frt: 'front',
  rr: 'rear', w: 'with', reg: 'regulator', pla: 'plastic', plas: 'plastic',
  plast: 'plastic', met: 'metal', sw: 'switch', eng: 'engine', man: 'manual',
  pres: 'pressure', press: 'pressure', susp: 'suspension',
  // compound words some chains close up that others split (or vice versa)
  airbag: 'air bag', airflow: 'air flow', sparkplug: 'spark plug',
  clockspring: 'clock spring', domelight: 'dome light', foglamp: 'fog light',
  pushrod: 'push rod', hubcap: 'hub cap', oilpan: 'oil pan',
  signalswitch: 'signal switch', sunroof: 'sun roof', subwoofer: 'sub woofer',
  ujoint: 'u joint',
  // lamp/light vocabularies name the same hardware on every list surveyed
  lamp: 'light', taillight: 'tail light', taillamp: 'tail light',
  headlight: 'head light', headlamp: 'head light',
};
/* Token-set collisions where the SAME sorted tokens describe DIFFERENT parts
 * (found in the corpus audit). These raw names always keep their own entry. */
const PART_NEVER_MERGE = new Set([
  'back seat back',                  // a seat-back section, not a back seat
  'motor - seat without tracks',     // the motor, not the track
  'motor - window without regulator',// the motor, not the regulator
]);

function partMergeKey(name) {
  const n = name.toLowerCase().replace(/w\/o/g, ' without ').replace(/w\//g, ' with ');
  const toks = [];
  for (let t of n.split(/[^a-z0-9]+/)) {
    if (!t) continue;
    let exp = PART_TOKEN_ABBR[t];
    if (exp === undefined && t.length > 3 && t.endsWith('s') && !t.endsWith('ss')) {
      t = t.slice(0, -1);
      exp = PART_TOKEN_ABBR[t];
    }
    for (const p of (exp !== undefined ? exp.split(' ') : [t])) {
      if (!PART_FILLER_TOKENS.has(p)) toks.push(p);
    }
  }
  const key = [...new Set(toks)].sort().join(' ');
  return key || name.toLowerCase();
}

/* ===== CURATED ALIAS GROUPS =====
 * Hand-curated merges partMergeKey can't prove mechanically: the same
 * physical part published under different VOCABULARY per chain (airbox vs
 * air cleaner housing vs air cleaner box), plus Lg/Sm-style size variants of
 * one part. Raw names were taken verbatim from the live price lists
 * (tools/check_part_aliases.py validates them and flags drift). Where a
 * chain's catalog makes a merge ambiguous (air cleaner BASE / HALF / LID vs
 * housing) the name is deliberately NOT listed. `syn` adds searchable
 * mechanic's words. Quoting uses the group's EXACT raw names as one tier —
 * cheapest matching row per yard, the yard's own spelling shown in the row —
 * never substrings, so "air cleaner" can't sweep up a $6 lid.
 * Where a finder category covers the same part, `canon` must EQUAL that
 * category's label (one taxonomy — spec §6); the category's own suggest
 * entry stands down in favor of the alias group (same name, honest counts). */
const PART_ALIAS_GROUPS = [
  {
    canon: 'Air intake / airbox',   // = finder `airbox` category label
    syn: ['airbox', 'air box', 'intake box', 'air cleaner'],
    raw: [
      'air cleaner', 'air cleaner (round)', 'air cleaner sm',
      'air cleaner assembly', 'air cleaner assembly aftermarket',
      'air cleaner assembly plastic', 'air cleaner assembly steel',
      'air cleaner assy', 'air cleaner box', 'air cleaner box plas',
      'air cleaner box plastic', 'air cleaner hous(lg)', 'air cleaner hous(sm)',
      'air cleaner housing', 'air cleaner housing carb', 'air box - complete',
    ],
  },
  {
    canon: 'Air cleaner lid',
    syn: ['airbox lid', 'air box lid', 'air cleaner top'],
    raw: ['air cleaner lid', 'air cleaner top', 'air box lid'],
  },
  {
    canon: 'Alternator',            // = finder `alternator` category label
    syn: [],
    raw: ['alternator', 'alternator (non hybrid)'],
  },
  {
    canon: 'Mass air flow sensor',
    syn: ['maf', 'maf sensor', 'mass airflow sensor'],
    raw: [
      'mass air flow sensor', 'sensor (mass air flow)', 'sensor - mass air flow',
      'sensor-mass airflow', 'air flow sensor', 'sensor- air flow',
    ],
  },
  {
    canon: 'Hood prop rod',
    syn: [],
    raw: [
      'hood prop', 'hood prop - any', 'hood prop any',
      'hood prop rod', 'prop rod - hood', 'prop rod-hood',
    ],
  },
];
// merge-key → group, so punctuation/abbreviation variants of a listed raw
// name (and future list drift that normalizes the same) land in the group.
const PART_ALIAS_BY_KEY = new Map();
const PART_ALIAS_CANON = new Set();
for (const g of PART_ALIAS_GROUPS) {
  PART_ALIAS_CANON.add(g.canon.toLowerCase());
  for (const r of g.raw) PART_ALIAS_BY_KEY.set(partMergeKey(r), g);
}

function getPartIndex() {
  const { shown } = getYardsView();
  // The finder taxonomy merges in once interchange.json arrives — fetch it
  // lazily and let the signature change rebuild the index on the next open.
  if (!interchangeData) loadInterchange();
  const sig = shown.map(y => y.location).join('|') + (interchangeData ? '#ic' : '');
  if (_partIndex && sig === _partIndexSig) return _partIndex;
  const baseName = loc => loc.replace(/\s*\(premium\)\s*$/i, '');

  // Pass 1 — every (cleaned) part name on the visible yards' published lists.
  const raw = new Map(); // lower raw name -> { display, yards: Set<base yard> }
  for (const y of shown) {
    const rows = yardPriceList(y.location);
    if (!rows) continue;
    const base = baseName(y.location);
    for (const r of rows) {
      if (JUNK_PART_NAME.test(r.part) || JUNK_PART_PHRASE.test(r.part)) continue;
      const k = r.part.toLowerCase();
      let e = raw.get(k);
      if (!e) { e = { display: titleCasePart(r.part), yards: new Set() }; raw.set(k, e); }
      e.yards.add(base);
    }
  }
  // Canonical keywords ('headlight', ...) that reach chain lists through the
  // keyword map, so the common word exists even when no chain spells it so.
  for (const entry of PART_KEYWORD_MAP) {
    if (raw.has(entry.kw)) continue;
    const yards = new Set();
    for (const y of shown) {
      const base = baseName(y.location);
      if (yards.has(base)) continue;
      if (yardPartQuote(y.location, [entry.kw]).status === 'priced') yards.add(base);
    }
    if (yards.size) raw.set(entry.kw, { display: titleCasePart(entry.kw), yards });
  }

  // Finder categories (spec §6 taxonomy convergence): the Parts-tab part
  // names resolve here too, carrying the finder's ORDERED price tokens as
  // the quote variants — so "Automatic transmission" or "Engine assembly"
  // compares across yards with the same careful row matching the finder
  // uses, and the finder's canonical label names the merged group.
  for (const cat of (interchangeData && interchangeData.categories) || []) {
    if (!cat.priceTokens || !cat.priceTokens.length) continue;
    const key = cat.label.toLowerCase();
    // A curated alias group with the same canonical name owns this part:
    // its exact-raw-name tier quotes and counts honestly (substring tokens
    // can land on the wrong row — the LID-for-airbox hazard), and the group
    // already wears the category's label. The category stands down here;
    // the Parts tab itself is untouched.
    if (PART_ALIAS_CANON.has(key)) continue;
    const toks = cat.priceTokens.map(t => t.toLowerCase());
    const existing = raw.get(key);
    if (existing) {
      existing.display = cat.label;
      existing.variants = toks;
      existing.canonical = true;
      continue;
    }
    const yards = new Set();
    for (const y of shown) {
      const base = baseName(y.location);
      if (yards.has(base)) continue;
      if (yardPartQuote(y.location, toks).status === 'priced') yards.add(base);
    }
    if (yards.size) {
      raw.set(key, { display: cat.label, yards, variants: toks, canonical: true });
    }
  }

  // Pass 2 — fold spelling variants into one entry; the best-covered variant
  // names the group, and all variant spellings stay searchable/matchable.
  // Curated alias groups fold across VOCABULARIES: their raw names share one
  // group keyed by the group object, display the canonical name, and collect
  // the exact raw spellings for quoting.
  const groups = new Map(); // merge key -> { display, repCoverage, yards, names }
  for (const [k, e] of raw) {
    const mkRaw = partMergeKey(k);
    const ag = PART_NEVER_MERGE.has(k) ? undefined : PART_ALIAS_BY_KEY.get(mkRaw);
    const mk = PART_NEVER_MERGE.has(k) ? 'solo:' + k : (ag ? 'alias:' + ag.canon : mkRaw);
    let g = groups.get(mk);
    if (!g) {
      g = { display: e.display, repCoverage: e.yards.size, yards: new Set(), names: [] };
      if (ag) {
        g.display = ag.canon;
        g.canonical = true;      // canonical name wins; suggestions rank by yards
        g.exact = [];            // exact raw spellings — the quote tier
        g.names.push(ag.canon.toLowerCase(), ...ag.syn);
      }
      groups.set(mk, g);
    }
    if (g.exact) g.exact.push(k);
    // Canonical finder labels win the group's display name outright
    // (spec §6.5); otherwise the best-covered spelling names the group.
    if (e.canonical && !g.exact && !g.canonical) {
      g.display = e.display;
      g.canonical = true;
    } else if (!g.canonical
        && (e.yards.size > g.repCoverage
            || (e.yards.size === g.repCoverage && e.display.length < g.display.length))) {
      g.display = e.display;
      g.repCoverage = e.yards.size;
    }
    g.names.push(k);
    // Finder categories quote through their ordered tokens, not the label.
    if (e.variants) g.names.push(...e.variants.filter(t => t !== k));
    e.yards.forEach(b => g.yards.add(b));
  }

  const entries = [...groups.values()];
  const byName = new Map();
  for (const g of entries) {
    // Alias groups quote through ONE exact-match tier: every raw spelling at
    // once, cheapest row per yard, never substrings (openPriceCompare).
    if (g.exact) g.quote = [g.exact.map(n => '=' + n)];
    byName.set(g.display.toLowerCase(), g);
    for (const n of g.names) byName.set(n, g);
  }
  _partIndex = { entries, byName };
  _partIndexSig = sig;
  return _partIndex;
}

const compareInput = document.getElementById('compare-input');
const compareSuggest = document.getElementById('compare-suggest');
let suggestItems = [];
let suggestActive = -1;

function hideCompareSuggest() {
  compareSuggest.style.display = 'none';
  suggestItems = [];
  suggestActive = -1;
}

/* Combobox, not plain type-ahead: tapping the empty field browses the FULL
 * parts list for the visible yards (alphabetical); typing filters it live
 * (best matches first). Comparisons only ever run against a real entry, so
 * free text can't dead-end on an empty sheet. */
function renderCompareSuggest() {
  if (!activeZipCoords || !liveLoaded) { hideCompareSuggest(); return; }
  const q = compareInput.value.trim().toLowerCase();
  const { entries } = getPartIndex();
  const byCount = (a, b) => b.yards.size - a.yards.size || a.display.localeCompare(b.display);
  if (q) {
    // Any spelling variant matches; prefix hits rank above substring hits.
    const starts = [], contains = [];
    for (const e of entries) {
      if (e.names.some(n => n.startsWith(q)) || e.display.toLowerCase().startsWith(q)) starts.push(e);
      else if (e.names.some(n => n.includes(q)) || e.display.toLowerCase().includes(q)) contains.push(e);
    }
    starts.sort(byCount);
    contains.sort(byCount);
    suggestItems = [...starts, ...contains];
  } else {
    // Browse mode: best-covered parts first, single-yard oddities sink.
    suggestItems = [...entries].sort(byCount);
  }
  suggestActive = -1;
  compareSuggest.innerHTML = suggestItems.length
    ? suggestItems.map((e, i) =>
        `<div class="compare-suggest-item" role="option" data-i="${i}">
           <span class="csi-name">${escapeHtml(e.display)}</span>
           <span class="csi-count">${e.yards.size} yard${e.yards.size === 1 ? '' : 's'}</span>
         </div>`).join('')
    : '<div class="compare-suggest-empty">No matching part on the visible yards\u2019 published lists \u2014 try a shorter word, or widen the filters above.</div>';
  compareSuggest.style.display = '';
}

function pickSuggestion(i) {
  const item = suggestItems[i];
  if (!item) return;
  compareInput.value = item.display;
  hideCompareSuggest();
  openPriceCompare(item.display);
}

/** Enter / the Compare button resolve to a real entry: the highlighted one,
 *  an exact name match, else the best current suggestion. Nothing matching
 *  keeps the "no matching part" row up instead of opening an empty sheet. */
function resolveAndCompare() {
  const q = compareInput.value.trim().toLowerCase();
  if (!q) { renderCompareSuggest(); return; }
  if (suggestActive >= 0) { pickSuggestion(suggestActive); return; }
  const exact = getPartIndex().byName.get(q);
  if (exact) {
    compareInput.value = exact.display;
    hideCompareSuggest();
    openPriceCompare(exact.display);
    return;
  }
  renderCompareSuggest();
  if (suggestItems.length) pickSuggestion(0);
}

compareInput.addEventListener('input', renderCompareSuggest);
compareInput.addEventListener('focus', renderCompareSuggest);
// mousedown (not click) so the pick wins the race against the input's blur.
compareSuggest.addEventListener('mousedown', e => {
  const item = e.target.closest('.compare-suggest-item');
  if (item) { e.preventDefault(); pickSuggestion(+item.dataset.i); }
});
compareInput.addEventListener('keydown', e => {
  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    if (!suggestItems.length) { renderCompareSuggest(); if (!suggestItems.length) return; }
    e.preventDefault();
    const d = e.key === 'ArrowDown' ? 1 : -1;
    suggestActive = (suggestActive + d + suggestItems.length) % suggestItems.length;
    [...compareSuggest.children].forEach((el, i) => el.classList.toggle('active', i === suggestActive));
    const active = compareSuggest.children[suggestActive];
    if (active) active.scrollIntoView({ block: 'nearest' });
  } else if (e.key === 'Enter') {
    resolveAndCompare();
  } else if (e.key === 'Escape') {
    hideCompareSuggest();
  }
});
compareInput.addEventListener('blur', () => setTimeout(hideCompareSuggest, 150));
document.getElementById('compare-go').addEventListener('click', resolveAndCompare);

/* ===== PART-FIRST SEARCH ("I need an alternator") =====
 * Inverts the Live grid: the user names a PART and THEIR car; we list every
 * donor vehicle in range carrying a part that fits, each row wearing an
 * honest confidence tier:
 *   "Verified fit"  — the family's part application was cross-checked against
 *                     public part-number fitment data (research notes in the
 *                     repo), AND this donor's engine is confirmed (VIN decode
 *                     or the model only ever came with the family engine).
 *   "Likely fit"    — same engine family / same generation, so it very likely
 *                     carries over — but either the application or this
 *                     donor's engine wasn't individually verified. The row
 *                     says what's missing. NEVER an unqualified "fits".
 * Data: docs/data/interchange.json (engine families + platform groups built
 * by the scraper), plus each donor's own part rows for generation windows.
 * Free vs Pro: search is free inside the free radius; the existing gates
 * (distance cap, blurred eBay values) apply unchanged. */
let interchangeData = null;
let _interchangeFetch = null;
function loadInterchange() {
  if (interchangeData) return Promise.resolve(interchangeData);
  if (!_interchangeFetch) {
    _interchangeFetch = fetch(DATA_BASE + 'data/interchange.json')
      .then(r => (r.ok ? r.json() : null))
      .then(d => { interchangeData = d; return d; })
      .catch(() => null);
  }
  return _interchangeFetch;
}

/* Mirrors the scraper's _squash_model: lowercase alphanumerics, leading make
 * token dropped, trailing "pickup" dropped when something remains. */
function pfSquash(s) { return String(s || '').toLowerCase().replace(/[^a-z0-9]/g, ''); }
function pfSquashModel(model, make) {
  let sm = pfSquash(model);
  const mk = pfSquash(make);
  if (mk && sm.startsWith(mk) && sm.length > mk.length) sm = sm.slice(mk.length);
  if (sm.endsWith('pickup') && sm.length > 'pickup'.length) sm = sm.slice(0, -'pickup'.length);
  return sm;
}
/* app = [make, model, yrLo, yrHi, sole, ambigNote] (engine families) or
 * [make, model, yrLo, yrHi] (platform groups). Model may end in "*". */
function pfAppMatches(app, year, make, model) {
  if (!(app[2] <= year && year <= app[3])) return false;
  const mk = String(make || '').toLowerCase();
  if (!app[0].toLowerCase().split('|').includes(mk)) return false;
  // Try both the make-stripped and raw squashes: a 'Ram 2500' under make
  // 'Ram' must keep its leading 'ram' or the 'Ram*' pattern never matches.
  const cands = [pfSquashModel(model, make), pfSquashModel(model, '')];
  const prefix = app[1].endsWith('*');
  const am = pfSquash(prefix ? app[1].slice(0, -1) : app[1]);
  return prefix ? cands.some(sm => sm.startsWith(am)) : cands.includes(am);
}
/* Factory generation windows (PART_CATALOG_SPEC §5.1). A same-model donor
 * fits a class-B/C/D category when seeker and donor years share ONE window.
 * Alias spellings ("Ram Pickup", "Suburban 1500") ship as their own rows,
 * so a plain squash-keyed map resolves every feed spelling. */
let _pfGenMap = null;
function pfGenWindows(make, model) {
  if (!interchangeData || !interchangeData.modelGenerations) return null;
  if (!_pfGenMap) {
    _pfGenMap = new Map();
    for (const [gmk, gmd, wins] of interchangeData.modelGenerations) {
      _pfGenMap.set(pfSquash(gmk) + '|' + pfSquashModel(gmd, gmk), wins);
    }
  }
  const mk = pfSquash(make);
  return _pfGenMap.get(mk + '|' + pfSquashModel(model, make))
    || _pfGenMap.get(mk + '|' + pfSquashModel(model, ''))
    || null;
}
function pfGenWindow(make, model, year) {
  const wins = pfGenWindows(make, model);
  if (wins) for (const w of wins) { if (year >= w[0] && year <= w[1]) return w; }
  return null;
}

/* Engine-assembly yard quotes are cylinder-tiered on most price lists
 * ("ENGINE 4 CYL", "ENGINE (NO ACC) 8-10", "ENGINE - 8CYL & UP") — prefer
 * the row matching the chosen family's cylinder count before the generic
 * complete-engine rows. */
function pfEngineQuoteVariants(cyl) {
  if (!cyl) return [];
  if (cyl >= 8) {
    return ['engine 8 cyl', 'engine 8 cly', 'engine (no acc) 8-10',
            '8cyl & up', 'engine 6.0 & above'];
  }
  return [`engine ${cyl} cyl`, `engine ${cyl} cly`, 'engine (no acc) 3-6',
          'engine - 4cyl - 6cyl', 'engine 5.9 and below',
          'engine 3&4 cylinder'];
}

function pfParseEngine(s) {
  if (!s) return { l: null, cyl: null };
  const sl = String(s).toLowerCase();
  const lm = sl.match(/(\d+\.\d+)\s*l/);
  const cm = sl.match(/(\d+)[\s-]*cyl/);
  return { l: lm ? parseFloat(lm[1]) : null, cyl: cm ? parseInt(cm[1], 10) : null };
}
/* true = decode confirms the family engine; false = denies; null = no data. */
function pfEngineVerdict(engineStr, fam) {
  if (engineStr && /diesel/i.test(engineStr)) return false;
  const { l, cyl } = pfParseEngine(engineStr);
  if (l == null) return null;
  if (!fam.liters.some(want => Math.abs(l - want) < 0.05)) return false;
  if (cyl != null && fam.cyl != null && cyl !== fam.cyl) return false;
  return true;
}
/* "2004–2008" (part-row fits provenance) -> [2004, 2008] or null. */
function pfParseFits(fits) {
  const m = String(fits || '').match(/(\d{4})\s*[–-]\s*(\d{4})/);
  return m ? [parseInt(m[1], 10), parseInt(m[2], 10)] : null;
}
function pfPartRow(v, cat) {
  for (const p of v.topParts || []) {
    const nl = p.name.toLowerCase();
    if (cat.tokens.some(t => nl.includes(t))) return p;
  }
  return null;
}
function pfDateLabel(dateAdded) {
  const d = new Date(String(dateAdded || '').slice(0, 10) + 'T12:00:00');
  return isNaN(d) ? '' : d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

let pfCat = null;        // chosen category object
let pfChosenFam = null;  // chosen engine family id when the model had several

function pfSaveState() {
  try {
    localStorage.setItem('jh_pf', JSON.stringify({
      cat: pfCat ? pfCat.id : '', year: document.getElementById('pf-year').value,
      make: document.getElementById('pf-make').value,
      model: document.getElementById('pf-model').value,
    }));
  } catch (e) { /* storage full/blocked — state restore is a nicety */ }
}

/* Pickers: makes/models come from the live inventory UNSCOPED (your car is
 * wherever you are), merged with the interchange table's own applications so
 * a car no yard currently has (e.g. MR2 Spyder) is still pickable. */
function pfPopulatePickers() {
  const ySel = document.getElementById('pf-year');
  if (!ySel.options.length) {
    const now = new Date().getFullYear() + 1;
    ySel.innerHTML = '<option value="">Year</option>' + Array.from(
      { length: now - 1979 }, (_, i) => `<option>${now - i}</option>`).join('');
  }
  const mSel = document.getElementById('pf-make');
  const prev = mSel.value;
  const makes = new Set();
  for (const v of liveInventory) {
    if (v.make && !JUNK_MAKES.has(v.make.toLowerCase())) makes.add(canonicalMake(v.make));
  }
  if (interchangeData) {
    for (const f of interchangeData.engineFamilies) {
      for (const a of f.apps) a[0].split('|').forEach(mk => makes.add(mk));
    }
  }
  mSel.innerHTML = '<option value="">Make</option>' +
    [...makes].sort().map(m => `<option>${escapeHtml(m)}</option>`).join('');
  if (prev && makes.has(prev)) mSel.value = prev;
  pfPopulateModels();
}
function pfPopulateModels() {
  const make = document.getElementById('pf-make').value;
  const mSel = document.getElementById('pf-model');
  const prev = mSel.value;
  if (!make) {
    mSel.innerHTML = '<option value="">Model</option>';
    mSel.disabled = true;
    return;
  }
  const models = new Map(); // squashed -> display
  for (const v of liveInventory) {
    if (canonicalMake(v.make) !== make || !v.model) continue;
    const disp = canonicalModel(v.make, v.model);
    const key = pfSquashModel(disp, make);
    if (key && !models.has(key)) models.set(key, disp);
  }
  if (interchangeData) {
    const pools = [...interchangeData.engineFamilies,
                   ...interchangeData.platformGroups.map(g => ({ apps: g.apps }))];
    for (const f of pools) {
      for (const a of f.apps) {
        if (!a[0].split('|').includes(make) || a[1].endsWith('*')) continue;
        const key = pfSquash(a[1]);
        if (key && !models.has(key)) models.set(key, a[1]);
      }
    }
  }
  mSel.innerHTML = '<option value="">Model</option>' +
    [...models.values()].sort((a, b) => a.localeCompare(b))
      .map(m => `<option>${escapeHtml(m)}</option>`).join('');
  mSel.disabled = false;
  if (prev && [...models.values()].includes(prev)) mSel.value = prev;
}

/* Part combobox: tap-to-browse the full category list, type to narrow —
 * same pattern as the price-compare input. */
const pfPartInput = document.getElementById('pf-part');
const pfPartSuggest = document.getElementById('pf-part-suggest');
function pfRenderPartSuggest() {
  if (!interchangeData) return;
  const q = pfPartInput.value.trim().toLowerCase();
  const cats = interchangeData.categories.filter(c =>
    !q || c.label.toLowerCase().includes(q) || c.tokens.some(t => t.includes(q)));
  pfPartSuggest.innerHTML = cats.length
    ? cats.map(c => `<div class="compare-suggest-item" role="option" data-cat="${c.id}">
        <span>${escapeHtml(c.label)}</span>
        <span class="csi-count">${c.kind === 'engine' ? 'engine-driven' : 'body / interior'}</span>
      </div>`).join('')
    : '<div class="compare-suggest-empty">No matching part — interchange currently covers the parts in this list. More families land as they\u2019re verified.' + pfAskHtml('part') + '</div>';
  pfPartSuggest.style.display = '';
  pfPartInput.setAttribute('aria-expanded', 'true');
}
function pfHidePartSuggest() {
  pfPartSuggest.style.display = 'none';
  pfPartInput.setAttribute('aria-expanded', 'false');
}
pfPartInput.addEventListener('focus', () => { loadInterchange().then(pfRenderPartSuggest); });
pfPartInput.addEventListener('input', () => {
  pfCat = null;  // typed text invalidates the picked category until re-chosen
  pfRenderPartSuggest();
});
pfPartInput.addEventListener('blur', () => setTimeout(pfHidePartSuggest, 150));
pfPartSuggest.addEventListener('mousedown', e => {
  // Coverage ask inside the "no matching part" row: mousedown (not click)
  // so the input's blur-hide doesn't eat the tap. Form lands in #pf-results.
  const ask = e.target.closest('.pfc-ask');
  if (ask) {
    e.preventDefault();
    pfHidePartSuggest();
    pfCoverageOpen('part', null);
    return;
  }
  const item = e.target.closest('.compare-suggest-item');
  if (!item) return;
  e.preventDefault();
  pfCat = interchangeData.categories.find(c => c.id === item.dataset.cat) || null;
  pfPartInput.value = pfCat ? pfCat.label : '';
  pfChosenFam = null;
  pfHidePartSuggest();
  pfMaybeSearch();
});

/* Engine-family chooser chips: a model that offered several family engines
 * in that year can't be guessed at — the seeker tells us which engine. */
function pfRenderEngineChips(fams) {
  const wrap = document.getElementById('pf-engine');
  if (!fams || fams.length <= 1) {
    wrap.style.display = 'none';
    wrap.innerHTML = '';
    return;
  }
  wrap.style.display = '';
  // The escape hatch matters as much as the chips: these are only the
  // engines we have interchange data FOR — a model could carry an engine we
  // don't cover yet (e.g. a 2005 Camry 3.0 V6). Picking the wrong family
  // sends someone on a wasted drive, so "not listed" is always offered.
  wrap.innerHTML =
    '<span class="pf-engine-label">This model came with more than one engine — which one is in YOUR car? (Check the emissions sticker or engine cover; guessing wrong wastes the drive.)</span>'
    + fams.map(f => `<button type="button" class="pf-chip ${pfChosenFam === f.id ? 'active' : ''}" data-fam="${f.id}">${escapeHtml(f.label)}</button>`).join('')
    + `<button type="button" class="pf-chip ${pfChosenFam === '__none__' ? 'active' : ''}" data-fam="__none__">My engine isn\u2019t listed</button>`;
}
document.getElementById('pf-engine').addEventListener('click', e => {
  const chip = e.target.closest('.pf-chip');
  if (!chip) return;
  pfChosenFam = chip.dataset.fam;
  pfRunSearch();
});

function pfSeeker() {
  return {
    year: parseInt(document.getElementById('pf-year').value, 10) || 0,
    make: document.getElementById('pf-make').value,
    model: document.getElementById('pf-model').value,
  };
}
function pfMaybeSearch() {
  // The car is OPTIONAL now: part + car runs the fitment search, part alone
  // runs browse mode (every nearby car carrying the part). Any change with a
  // part picked re-renders whichever mode the inputs imply.
  if (pfCat) pfRunSearch();
}

function pfTierChip(tier) {
  return tier === 'verified'
    ? '<span class="pf-tier pf-tier-verified" title="This part application was cross-checked against public part-number fitment data, and this donor\u2019s engine is confirmed. Still match the part number at the yard.">Verified fit</span>'
    : '<span class="pf-tier pf-tier-likely" title="Same engine family / same generation, so it very likely fits — but this exact pairing wasn\u2019t individually verified. Verify the part number before driving out.">Likely fit &mdash; verify part #</span>';
}

/* 'Verified fits only' (owner request, 2026-10-23): a pure VIEW filter over
 * the already-rendered list — CSS hides the Likely rows, nothing refetches,
 * and it's free for everyone (it filters a view, it doesn't unlock data).
 * The tier counts always render beside it so filtering never hides that more
 * donors exist. Fitment mode filters by fit tier; engine-browse mode filters
 * by its own tier vocabulary (VIN-confirmed). Spotted-part browse makes no
 * fit claims at all, so it gets no toggle. Default OFF on load; it holds for
 * the session (a view preference), and when a later search has zero verified
 * rows the explicit "flip the toggle off" note keeps that state honest. */
let pfVerifiedOnly = false;
function pfVonlyRowHtml(nVer, nOther, vocab) {
  const verWord = vocab === 'vin' ? 'VIN-confirmed' : 'verified';
  const otherWord = vocab === 'vin' ? 'unconfirmed' : 'likely';
  return `<div class="pf-vonly-row">
      <span class="pf-tier-counts"><strong>${nVer.toLocaleString()}</strong> ${verWord} &middot; <strong>${nOther.toLocaleString()}</strong> ${otherWord}</span>
      <label class="pf-vonly"><input type="checkbox" id="pf-vonly-cb"${pfVerifiedOnly ? ' checked' : ''}> ${vocab === 'vin' ? 'VIN-confirmed only' : 'Verified fits only'}</label>
    </div>`
    // What 'verified' means, said out loud (honesty audit, 2026-10-23): the
    // definition used to live only in a hover tooltip phone users never see.
    + `<div class="pf-hint">${vocab === 'vin'
        ? 'VIN-confirmed = the donor\u2019s VIN decode shows this engine, not a physical inspection &mdash; still check under the hood at the yard.'
        : 'Verified = published catalog fitment data, not a physical inspection &mdash; match the part number at the yard.'}</div>`
    + (nVer === 0
      ? `<div class="pf-vonly-none pf-empty">No ${verWord} donors in range right now &mdash; flip the toggle off to see the ${nOther.toLocaleString()} ${otherWord} one${nOther === 1 ? '' : 's'}.</div>`
      : '');
}
document.getElementById('pf-results').addEventListener('change', e => {
  if (e.target.id !== 'pf-vonly-cb') return;
  pfVerifiedOnly = e.target.checked;
  // State class is pf-vonly-on, NOT pf-vonly: the label already owns
  // .pf-vonly (display:flex + white-space:nowrap), and putting that class on
  // the results container inherited nowrap into every line — the header grew
  // past the viewport and iOS zoomed the whole page out to fit it.
  document.getElementById('pf-results').classList.toggle('pf-vonly-on', pfVerifiedOnly);
  track(pfVerifiedOnly ? 'pf-verified-only-on' : 'pf-verified-only-off');
});

/* ===== BROWSE MODE (owner request, 2026-10): part chosen, no car =========
 * Lists every nearby car CARRYING the part — the old Live-tab spotted-part
 * filter's job, now living where parts people look. No fit claims are made
 * (there's no seeker car to claim against). Per rule class:
 *   - engine-class categories (engine assembly, alternator, starter, coils):
 *     browse keys off the ENGINE-FAMILY data — pick a family ("Vortec 5.3"),
 *     donors are cars whose applications match it, with VIN-decode
 *     confirmation badges. This is the "any LS/5.3 near me" flow.
 *   - body/platform categories: spotted-part semantics — cars whose
 *     valuable-parts list names the part (same matching the Live filter had).
 *   - combo/exact (transmissions, ECM, radio): spotted semantics too, but
 *     the valuable-parts data rarely tracks them — the honest empty state
 *     points at adding a car to run the fit search instead.
 * Partial car fields (just a make, say) act as plain filters on the browse
 * list, never as fit claims. */
function pfRenderBrowseFamPicker() {
  const wrap = document.getElementById('pf-engine');
  wrap.style.display = '';
  const fams = [...interchangeData.engineFamilies]
    .sort((a, b) => a.label.localeCompare(b.label));
  wrap.innerHTML =
    '<span class="pf-engine-label">Browsing by engine — which engine are you hunting? Donors are matched by engine family, not by keyword.</span>'
    + '<select id="pf-browse-fam" class="pf-browse-fam">'
    + '<option value="">Pick an engine&hellip;</option>'
    + fams.map(f => `<option value="${f.id}" ${pfChosenFam === f.id ? 'selected' : ''}>${escapeHtml(f.label)}</option>`).join('')
    + '</select>';
}
document.getElementById('pf-engine').addEventListener('change', e => {
  if (e.target.id === 'pf-browse-fam') {
    pfChosenFam = e.target.value || null;
    pfRunSearch();
  }
});

function pfRunBrowse(s) {
  const out = document.getElementById('pf-results');
  track('part-browse');
  pfSaveState();
  const radius = effectiveRadiusMi();
  const unlocked = isPro();
  const sMakeOk = v => !s.make || canonicalMake(v.make) === s.make;
  const sModelOk = v => !s.model
    || pfSquashModel(canonicalModel(v.make, v.model), v.make)
       === pfSquashModel(s.model, s.make);
  const sYearOk = v => !s.year || v.year === s.year;
  const inScope = v => {
    if (!sMakeOk(v) || !sModelOk(v) || !sYearOk(v)) return false;
    const d = vehicleDistanceMi(v);
    return !(radius && (d == null || d > radius));
  };
  const rows = [];
  let fam = null;
  let headTop = '';

  if (pfCat.kind === 'engine') {
    // Family browse: donors by engine-family application lists + VIN decode,
    // never by a "spotted" keyword (the parts DB doesn't track engines).
    pfRenderBrowseFamPicker();
    fam = interchangeData.engineFamilies.find(f => f.id === pfChosenFam);
    if (!fam) {
      out.innerHTML = '<div class="pf-empty">Browsing without a car: pick the engine you\u2019re hunting above and we\u2019ll list every nearby car that came with it. Or add your car (year, make, model) to run the fit search instead.</div>';
      return;
    }
    for (const v of liveInventory) {
      if (!inScope(v)) continue;
      const app = fam.apps.find(a => pfAppMatches(a, v.year, canonicalMake(v.make), v.model));
      if (!app) continue;
      const ex = extrasFor(v);
      const verdict = pfEngineVerdict(ex ? ex[2] : '', fam);
      if (verdict === false) continue;  // decode says a different engine
      const engineOk = verdict === true || (verdict === null && !!app[4] && !app[5]);
      const warns = [];
      if (!engineOk) warns.push(`engine not confirmed — this ${escapeHtml(v.model)} also came with other engines; check under the hood before pulling`);
      if (app[5]) warns.push(escapeHtml(app[5]));
      rows.push({ v, d: vehicleDistanceMi(v), warns,
                  badge: verdict === true
                    ? `<span class="pf-tier pf-tier-verified" title="The donor\u2019s VIN decode confirms a ${escapeHtml(fam.label)}.">VIN-confirmed</span>`
                    : '' });
    }
    headTop = `<strong>${rows.length.toLocaleString()} car${rows.length === 1 ? '' : 's'} near you</strong> carrying a ${escapeHtml(fam.label)} &mdash; add your car (year, make, model) above to check what fits.`;
  } else {
    pfRenderEngineChips(null);
    // Spotted-part semantics: the car's valuable-parts list names the part —
    // exactly what the old Live-tab part filter matched on.
    const kws = (pfCat.tokens.length ? pfCat.tokens : [pfCat.label]).map(t => t.toLowerCase());
    for (const v of liveInventory) {
      if (!inScope(v)) continue;
      const hit = (v.topParts || []).find(p => kws.some(t => partQueryHit(p, t)));
      if (!hit) continue;
      rows.push({ v, d: vehicleDistanceMi(v), warns: [], hit, badge: '' });
    }
    headTop = `<strong>Showing all cars with this part near you</strong> &mdash; add your car to check what fits. ${rows.length.toLocaleString()} car${rows.length === 1 ? '' : 's'} list${rows.length === 1 ? 's' : ''} a spotted ${escapeHtml(pfCat.label.toLowerCase())}.`;
  }

  if (!rows.length) {
    const kindNote = (pfCat.kind === 'combo' || pfCat.kind === 'exact')
      ? ` The spotted-parts data tracks smaller carry-out parts, and ${escapeHtml(pfCat.label.toLowerCase())}s mostly aren\u2019t in it — add your car above and the fit search will find donors by ${pfCat.kind === 'combo' ? 'generation and engine' : 'generation'} instead.`
      : ' Yards rotate stock weekly — widen the radius or check back.';
    out.innerHTML = `<div class="pf-empty">No cars within ${radius ? radius + ' mi' : 'range'} ${pfCat.kind === 'engine' ? `carrying a ${escapeHtml(fam.label)}` : `listing a spotted ${escapeHtml(pfCat.label.toLowerCase())}`} right now.${kindNote}</div>`;
    return;
  }

  rows.sort((a, b) => (a.d ?? 1e9) - (b.d ?? 1e9));
  const CAP = 120;
  let quoteVariants = pfCat.priceTokens.map(t => t.toLowerCase());
  if (pfCat.id === 'engine-assembly' && fam) {
    quoteVariants = pfEngineQuoteVariants(fam.cyl).concat(quoteVariants);
  }
  const filterNote = (s.make || s.model || s.year)
    ? `<div class="pf-caveat">Filtered to ${escapeHtml([s.year || '', s.make || '', s.model || ''].join(' ').trim())} — clear those fields to browse everything.</div>` : '';
  // Engine browse carries its own tier vocabulary (VIN-confirmed vs not), so
  // the view toggle applies there; spotted-part browse makes no claims.
  const nVin = rows.filter(r => r.badge).length;
  out.classList.toggle('pf-vonly-on', pfCat.kind === 'engine' && pfVerifiedOnly);
  out.innerHTML =
    `<div class="pf-results-head">${headTop} Sorted by distance. Yards track cars, not parts left on them &mdash; a long-sitting donor may be picked over.</div>`
    + (pfCat.kind === 'engine' ? pfVonlyRowHtml(nVin, rows.length - nVin, 'vin') : '')
    + filterNote
    + (pfCat.notes || []).map(n => `<div class="pf-caveat">${escapeHtml(n)}</div>`).join('')
    + rows.slice(0, CAP).map(r => {
      const v = r.v;
      const quote = yardPartQuote(v.location, quoteVariants);
      const priceHtml = quote.status === 'priced'
        ? `<span class="pf-yard-price" title="${escapeHtml(quote.part)} — from the yard\u2019s own published price list">Yard: $${quote.price.toFixed(2)}${quote.core > 0 ? ` <span style="font-weight:400;color:var(--text-dim);">+ $${quote.core.toFixed(2)} core</span>` : ''}</span>`
        : `<span class="pf-ebay">${quote.status === 'not-listed' ? 'not on the yard\u2019s published list — ask at the counter' : 'yard posts prices in-store only'}</span>`;
      const worthHtml = (!pfCat.noValue && r.hit)
        ? (unlocked
          ? `<span class="pf-ebay" title="Typical online price for this used part (eBay sold listings, national) — what you\u2019d pay if you didn\u2019t pull it yourself">Used online: ~${formatPrice(r.hit.low)}&ndash;${formatPrice(r.hit.high)}</span>`
          : `<span class="pf-ebay locked-blur" role="button" onclick="openUpgradeSheet('pf-value')">Used online: ${LOCKED_PRICE_MASK}</span>`)
        : '';
      // Buyer's savings line — only when BOTH sides are real: a published
      // yard price and a value band (Pro; free users would back the band out).
      const saveHtml = (unlocked && !pfCat.noValue && r.hit && quote.status === 'priced' && r.hit.high - quote.price > 0)
        ? `<span class="pf-save" title="What you\u2019d save over buying this part used online — if the part on this car is good">Save ~${formatPrice(Math.max(0, Math.round(r.hit.low - quote.price)))}&ndash;${formatPrice(Math.round(r.hit.high - quote.price))}</span>`
        : '';
      const dateLbl = pfDateLabel(v.dateAdded);
      return `<div class="pf-row-card pf-browse${r.badge ? ' pf-vin' : ''}">
        <div class="pf-car-line"><span class="pf-car-name">${v.year} ${escapeHtml(v.make)} ${escapeHtml(v.model.toLowerCase().startsWith(v.make.toLowerCase() + ' ') ? v.model.slice(v.make.length + 1) : v.model)}</span>${r.badge}</div>
        <div class="pf-meta">${escapeHtml(v.location)}${r.d != null ? ` &middot; <span class="dist">${Math.round(r.d)} mi</span>` : ''}${v.row ? ` &middot; Row ${escapeHtml(String(v.row))}` : ''}${dateLbl ? ` &middot; set out ${dateLbl}` : ''}${saleBadgeHtml(v.location)}</div>
        <div class="pf-value">${worthHtml}${priceHtml}${saveHtml}</div>
        ${r.warns.length ? `<div class="pf-warn">${r.warns.join(' &middot; ')}</div>` : ''}
      </div>`;
    }).join('')
    + (rows.length > CAP
      ? `<div class="pf-more">Showing the ${CAP} nearest of ${rows.length.toLocaleString()} cars — tighten the radius to narrow.</div>`
      : '');
}

function pfRunSearch() {
  const out = document.getElementById('pf-results');
  const status = document.getElementById('pf-status');
  const s = pfSeeker();
  if (!pfCat) { status.textContent = 'Pick a part first.'; return; }
  if (!activeZipCoords) {
    out.innerHTML = '<div class="pf-empty">Set a zip code (or use your location) up top so we know which yards are near you — distances drive this whole list.</div>';
    return;
  }
  if (!interchangeData) { loadInterchange().then(() => pfRunSearch()); return; }
  status.textContent = '';
  // Part chosen but no (full) car: BROWSE mode — every nearby car carrying
  // the part, no fit claims. Fitment needs all three car fields.
  if (!s.year || !s.make || !s.model) { pfRunBrowse(s); return; }
  track('part-first-search');
  pfSaveState();

  const radius = effectiveRadiusMi();
  const results = new Map();  // vehicle id -> result row (verified wins)
  let famNote = '';
  let groupNotes = [];

  if (pfCat.kind === 'engine') {
    // A family offers the part to this seeker only when the part's own
    // (possibly narrower) researched year window also covers the seeker —
    // e.g. the 1MZ alternator claim is 97–03 even though the engine ran
    // 94–06. Outside the window we'd be guessing; we don't.
    const partOk = f => {
      const p = f.parts[pfCat.id];
      return p && (!p.years || (s.year >= p.years[0] && s.year <= p.years[1]));
    };
    const fams = interchangeData.engineFamilies.filter(f =>
      partOk(f) && f.apps.some(a => pfAppMatches(a, s.year, s.make, s.model)));
    pfRenderEngineChips(fams);
    if (!fams.length) {
      // Performance trims with unique, unpublished engines get a real
      // explanation (and a pointer at the body-part search that DOES work)
      // instead of a bare "no data".
      const trimNote = (interchangeData.trimEngineNotes || []).find(t =>
        t.apps.some(a => pfAppMatches(a, s.year, s.make, s.model)));
      if (trimNote) {
        const nTrim = liveInventory.filter(v =>
          trimNote.apps.some(a => pfAppMatches(a, v.year, canonicalMake(v.make), v.model))).length;
        out.innerHTML = `<div class="pf-empty">${escapeHtml(trimNote.note)}`
          + ` (${nTrim} in tracked yards right now.)`
          + ` Body parts are a different story — window regulators, switches and`
          + ` climate controls share the platform, so search one of those to see`
          + ` every platform donor near you.${pfAskHtml('car')}</div>`;
        return;
      }
      out.innerHTML = `<div class="pf-empty">No interchange data yet for a ${s.year} ${escapeHtml(s.make)} ${escapeHtml(s.model)} ${escapeHtml(pfCat.label.toLowerCase())}. We only list fits we can stand behind — this car\u2019s engine family isn\u2019t in the verified table yet, so we\u2019d rather show nothing than guess.${pfAskHtml('car')}</div>`;
      return;
    }
    if (pfChosenFam === '__none__') {
      out.innerHTML = `<div class="pf-empty">We don\u2019t have interchange data for your engine yet — only the engines listed above are in the verified table. We\u2019d rather show nothing than guess a fit that wastes your drive.${pfAskHtml('engine')}</div>`;
      return;
    }
    let fam = fams.length === 1 ? fams[0] : fams.find(f => f.id === pfChosenFam);
    if (!fam) {
      out.innerHTML = '<div class="pf-empty">Pick your engine above and we\u2019ll list the donors.</div>';
      return;
    }
    pfChosenFam = fam.id;
    pfRenderEngineChips(fams);  // repaint active state
    const part = fam.parts[pfCat.id];
    famNote = `${fam.label} — ${part.note}`;
    const seekerApp = fam.apps.find(a => pfAppMatches(a, s.year, s.make, s.model));
    const seekerAmbig = seekerApp && seekerApp[5];
    if (seekerAmbig) groupNotes.push('Your car: ' + seekerAmbig);
    for (const v of liveInventory) {
      if (part.years && (v.year < part.years[0] || v.year > part.years[1])) continue;
      const app = fam.apps.find(a => pfAppMatches(a, v.year, canonicalMake(v.make), v.model));
      if (!app) continue;
      const d = vehicleDistanceMi(v);
      if (radius && (d == null || d > radius)) continue;
      const ex = extrasFor(v);
      const verdict = pfEngineVerdict(ex ? ex[2] : '', fam);
      if (verdict === false) continue;  // decode says a different engine — out
      const engineOk = verdict === true || (verdict === null && !!app[4] && !app[5]);
      const warns = [];
      if (!engineOk) {
        warns.push(`engine not confirmed — this ${escapeHtml(v.model)} also came with other engines; check under the hood before pulling`);
      }
      if (app[5]) warns.push(escapeHtml(app[5]));
      // Verified only when seeker AND donor sit inside ONE published
      // part-number application list (a verified group) — a family can span
      // several distinct units, so family membership alone is never enough.
      let tier = 'likely';
      if (engineOk && !app[5] && !seekerAmbig && part.vg) {
        for (const g of part.vg) {
          if (g.some(sp => pfAppMatches(sp, s.year, s.make, s.model))
              && g.some(sp => pfAppMatches(sp, v.year, canonicalMake(v.make), v.model))) {
            tier = 'verified';
            break;
          }
        }
      }
      // Engine assemblies (spec §4): "Verified" is reserved for donors whose
      // VIN decode CONFIRMS the engine — family application lists alone
      // can't rule out an option engine sitting in the donor. Decode-silent
      // donors stay Likely and keep the check-under-the-hood warning.
      if (pfCat.id === 'engine-assembly') {
        tier = (verdict === true && !app[5] && !seekerAmbig) ? 'verified' : 'likely';
      }
      results.set(v.id, { v, d, tier, warns });
    }
  } else {
    // Chassis-side kinds (spec §3): body = platform groups + same-model
    // generation; combo = same-model generation × engine-family chip,
    // always Likely; exact = same-model generation ONLY, always Likely.
    let famFilter = null;
    if (pfCat.kind === 'combo') {
      // Which engine drives which transmission/ECM — offer the same chips
      // the engine path uses. Unlike engines, an unpicked chip doesn't
      // block results: generation match alone is an honest Likely, the
      // chip just narrows donors to matching drivetrains.
      const fams = interchangeData.engineFamilies.filter(f =>
        f.apps.some(a => pfAppMatches(a, s.year, s.make, s.model)));
      pfRenderEngineChips(fams);
      const fam = fams.length === 1 ? fams[0]
        : (pfChosenFam !== '__none__' ? fams.find(f => f.id === pfChosenFam) : null);
      if (fam) {
        pfChosenFam = fam.id;
        pfRenderEngineChips(fams);  // repaint active state
        famFilter = fam;
        groupNotes.push(`Donors narrowed to cars that came with the ${fam.label} — a different engine usually means a different ${pfCat.label.toLowerCase()}.`);
      } else if (fams.length > 1) {
        groupNotes.push('Showing every same-generation donor — pick your engine above to narrow to donors with a matching drivetrain.');
      }
    } else {
      pfRenderEngineChips(null);
    }
    if (pfCat.kind === 'body') {
      // Cross-model groups: hand-verified platform families ship tier
      // "verified"; performance-trim platform mappings (M3 -> E46 etc.) are
      // reasoned claims, not published part-number lists, and ship "likely".
      // combo/exact categories NEVER use platform groups (spec §3): a
      // chassis-mate's transmission or radio is not a fit claim we can make.
      for (const g of interchangeData.platformGroups) {
        if (g.cat !== pfCat.id) continue;
        if (!g.apps.some(a => pfAppMatches(a, s.year, s.make, s.model))) continue;
        const gTier = g.tier === 'likely' ? 'likely' : 'verified';
        groupNotes.push(`${g.label}: ${g.note}`);
        for (const v of liveInventory) {
          if (!g.apps.some(a => pfAppMatches(a, v.year, canonicalMake(v.make), v.model))) continue;
          const d = vehicleDistanceMi(v);
          if (radius && (d == null || d > radius)) continue;
          const prev = results.get(v.id);
          if (prev && prev.tier === 'verified') continue; // verified wins
          results.set(v.id, { v, d, tier: gTier, warns: [escapeHtml(g.note)] });
        }
      }
    }
    // Same model, same generation. Two honest sources, donor-row first:
    // (1) the donor's own researched part row carries a fits window;
    // (2) the factory generation table — seeker and donor years inside ONE
    //     window of the same model. Both are Likely, never Verified.
    const sKey = pfSquashModel(s.model, s.make);
    const sWin = pfGenWindow(s.make, s.model, s.year);
    const rowWarn = pfCat.rowWarn ? escapeHtml(pfCat.rowWarn) : '';
    for (const v of liveInventory) {
      if (results.has(v.id)) continue;  // verified group row already won
      if (canonicalMake(v.make) !== s.make) continue;
      if (pfSquashModel(canonicalModel(v.make, v.model), v.make) !== sKey) continue;
      const d = vehicleDistanceMi(v);
      if (radius && (d == null || d > radius)) continue;
      if (famFilter) {
        // The chosen engine must be plausible in the donor: it must be a
        // listed application AND the donor's decode must not contradict it.
        const dApp = famFilter.apps.find(a => pfAppMatches(a, v.year, canonicalMake(v.make), v.model));
        if (!dApp) continue;
        const ex = extrasFor(v);
        if (pfEngineVerdict(ex ? ex[2] : '', famFilter) === false) continue;
      }
      const warns = [];
      const row = pfPartRow(v, pfCat);
      const win = row ? pfParseFits(row.fits) : null;
      if (win && s.year >= win[0] && s.year <= win[1]) {
        warns.push(`same ${escapeHtml(s.make)} ${escapeHtml(s.model)} generation (${row.fits}) — trim and options still vary, verify part number`);
      } else if (sWin && v.year >= sWin[0] && v.year <= sWin[1]) {
        warns.push(`same ${escapeHtml(s.make)} ${escapeHtml(s.model)} generation (${sWin[0]}\u2013${sWin[1]}) — trim and options still vary`);
      } else {
        continue;  // outside every window we can vouch for
      }
      if (rowWarn) warns.push(rowWarn);
      results.set(v.id, { v, d, tier: 'likely', warns });
    }
    if (!groupNotes.length) famNote = 'Same-generation donors of your own model' + (pfCat ? ` — ${pfCat.label.toLowerCase()}s rarely cross model lines without a verified platform group` : '');
  }

  const rows = [...results.values()].sort((a, b) =>
    (a.d ?? 1e9) - (b.d ?? 1e9)
    || (a.tier === b.tier ? 0 : a.tier === 'verified' ? -1 : 1));
  const nVer = rows.filter(r => r.tier === 'verified').length;
  if (!rows.length) {
    out.innerHTML = `<div class="pf-empty">No donor cars for a ${s.year} ${escapeHtml(s.make)} ${escapeHtml(s.model)} ${escapeHtml(pfCat.label.toLowerCase())} within ${radius ? radius + ' mi' : 'range'} right now. Yards rotate stock weekly — add a watch on the Alerts tab, or widen the radius.</div>`;
    return;
  }
  const CAP = 120;
  const unlocked = isPro();
  out.classList.toggle('pf-vonly-on', pfVerifiedOnly);
  const head = `<div class="pf-results-head"><strong>${rows.length.toLocaleString()} donor car${rows.length === 1 ? '' : 's'}</strong> in range carrying a fitting ${escapeHtml(pfCat.label.toLowerCase())} &mdash; sorted by distance, then confidence. Yards track cars, not parts left on them — a long-sitting donor may be picked over.</div>`
    + pfVonlyRowHtml(nVer, rows.length - nVer, 'fit')
    + (famNote ? `<div class="pf-caveat">${escapeHtml(famNote)}</div>` : '')
    + groupNotes.map(n => `<div class="pf-caveat">${n}</div>`).join('')
    // Category-level honesty notes always show (spec: engine long-block
    // caveat, unknown mileage, pull logistics, VIN-lock, airbag handling…).
    + (pfCat.notes || []).map(n => `<div class="pf-caveat">${escapeHtml(n)}</div>`).join('');
  // Engine-assembly rows on most yard lists are cylinder-tiered — quote the
  // row matching the chosen family's cylinder count ahead of the generics.
  let quoteVariants = pfCat.priceTokens.map(t => t.toLowerCase());
  if (pfCat.id === 'engine-assembly' && pfChosenFam) {
    const qFam = interchangeData.engineFamilies.find(f => f.id === pfChosenFam);
    if (qFam) quoteVariants = pfEngineQuoteVariants(qFam.cyl).concat(quoteVariants);
  }
  out.innerHTML = head + rows.slice(0, CAP).map(r => {
    const v = r.v;
    const quote = yardPartQuote(v.location, quoteVariants);
    const priceHtml = quote.status === 'priced'
      ? `<span class="pf-yard-price" title="${escapeHtml(quote.part)} — from the yard\u2019s own published price list">Yard: $${quote.price.toFixed(2)}${quote.core > 0 ? ` <span style="font-weight:400;color:var(--text-dim);">+ $${quote.core.toFixed(2)} core</span>` : ''}</span>`
      : `<span class="pf-ebay">${quote.status === 'not-listed' ? 'not on the yard\u2019s published list — ask at the counter' : 'yard posts prices in-store only'}</span>`;
    // noValue categories (engine assemblies, transmissions) ship no value
    // band by charter — you can't carry one out, so "worth" is misleading.
    const partRow = pfCat.noValue ? null : pfPartRow(v, pfCat);
    const ebayHtml = partRow
      ? (unlocked
        ? `<span class="pf-ebay" title="Typical online price for this used part (eBay sold listings, national) — what you\u2019d pay if you didn\u2019t pull it yourself">Used online: ~${formatPrice(partRow.low)}&ndash;${formatPrice(partRow.high)}</span>`
        : `<span class="pf-ebay locked-blur" role="button" onclick="openUpgradeSheet('pf-value')">Used online: ${LOCKED_PRICE_MASK}</span>`)
      : '';
    // Buyer's savings line — both sides real, Pro only (free users would
    // back the blurred band out of price + savings).
    const saveHtml = (unlocked && partRow && quote.status === 'priced' && partRow.high - quote.price > 0)
      ? `<span class="pf-save" title="What you\u2019d save over buying this part used online — if the part on this car is good">Save ~${formatPrice(Math.max(0, Math.round(partRow.low - quote.price)))}&ndash;${formatPrice(Math.round(partRow.high - quote.price))}</span>`
      : '';
    const dateLbl = pfDateLabel(v.dateAdded);
    return `<div class="pf-row-card ${r.tier === 'verified' ? 'pf-verified' : 'pf-likely'}">
      <div class="pf-car-line"><span class="pf-car-name">${v.year} ${escapeHtml(v.make)} ${escapeHtml(v.model.toLowerCase().startsWith(v.make.toLowerCase() + ' ') ? v.model.slice(v.make.length + 1) : v.model)}</span>${pfTierChip(r.tier)}</div>
      <div class="pf-meta">${escapeHtml(v.location)}${r.d != null ? ` &middot; <span class="dist">${Math.round(r.d)} mi</span>` : ''}${v.row ? ` &middot; Row ${escapeHtml(String(v.row))}` : ''}${dateLbl ? ` &middot; set out ${dateLbl}` : ' &middot; set-out date unknown'}${saleBadgeHtml(v.location)}</div>
      <div class="pf-value">${ebayHtml}${priceHtml}${saveHtml}</div>
      ${r.warns.length ? `<div class="pf-warn">${r.warns.join(' &middot; ')}</div>` : ''}
    </div>`;
  }).join('') + (rows.length > CAP
    ? `<div class="pf-more">Showing the ${CAP} nearest of ${rows.length.toLocaleString()} donors — tighten the radius to narrow.</div>`
    : '');
}

/* ===== COVERAGE REQUESTS (owner ask, 2026-10) ============================
 * The honest empty states above say "we don't cover this yet" — this is the
 * reply channel. A quiet one-liner + link opens a tiny inline form PREFILLED
 * with what the seeker already entered (car, part, zip); one tap files it.
 * No login. Email is optional and the copy promises nothing automated — when
 * coverage lands we may ping them by hand. Requests aggregate server-side by
 * a normalized key and surface to the owner (admin GET + a max-once-a-day
 * digest email). Server: POST /v1/coverage/request (backend/src/coverage.js). */
const COVERAGE_API = 'https://yardscout-api.yardscout.workers.dev';
let _covPending = null;   // context captured when the form opens

function pfAskHtml(kind) {
  return `<div class="pfc-line">We don\u2019t cover this yet \u2014 <button type="button" class="pfc-ask" data-kind="${kind}">ask us to add it</button>.</div>`;
}

function pfCoverageContext(kind) {
  const s = pfSeeker();
  return {
    kind,
    year: s.year || null,
    make: s.make || null,
    model: s.model || null,
    part: (pfCat ? pfCat.label : pfPartInput.value.trim()) || null,
    zip: localStorage.getItem('jh_zip') || null,
  };
}

function pfCoverageFormHtml(ctx) {
  const what = [[ctx.year, ctx.make, ctx.model].filter(Boolean).join(' '), ctx.part]
    .filter(Boolean).join(' \u2014 ');
  // Placeholder says what the box IS; the how/why lives in the hint below
  // (placeholder-pattern sweep 2026-10-26, same fix as the compare box).
  const notePh = ctx.kind === 'engine'
    ? 'Engine (e.g. 3.0 V6) — optional'
    : 'Notes — optional';
  return `<div class="pf-coverage-form" id="pf-coverage-form">
    <div class="pfc-what">Asking us to add: <strong>${escapeHtml(what)}</strong>${ctx.zip ? ` <span class="pfc-zip">(near ${escapeHtml(ctx.zip)})</span>` : ''}</div>
    <input type="email" id="pfc-email" placeholder="you@email.com — optional" autocomplete="email">
    <input type="text" id="pfc-note" placeholder="${notePh}" maxlength="500">
    <div class="pf-hint">A note helps us verify it. Leave an email and we may ping you if it lands &mdash; nothing automated.</div>
    <div class="pfc-actions">
      <button type="button" class="btn btn-primary" id="pfc-send" onclick="pfCoverageSubmit()">Add it to the list</button>
      <span class="pfc-status" id="pfc-status"></span>
    </div>
  </div>`;
}

function pfCoverageOpen(kind, linkEl) {
  _covPending = pfCoverageContext(kind);
  track('coverage-ask-open');
  const html = pfCoverageFormHtml(_covPending);
  const line = linkEl && linkEl.closest('.pfc-line');
  if (line) line.outerHTML = html;                                 // in place, inside the empty state
  else document.getElementById('pf-results').innerHTML = html;     // part-combobox path (dropdown closes)
}

async function pfCoverageSubmit() {
  if (!_covPending) return;
  const btn = document.getElementById('pfc-send');
  const status = document.getElementById('pfc-status');
  const email = (document.getElementById('pfc-email').value || '').trim();
  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    status.textContent = 'That email doesn\u2019t look right — fix it or leave it blank.';
    return;
  }
  btn.disabled = true;
  status.textContent = 'Sending\u2026';
  const body = Object.assign({}, _covPending, {
    email: email || null,
    note: (document.getElementById('pfc-note').value || '').trim() || null,
  });
  try {
    const r = await fetch(COVERAGE_API + '/v1/coverage/request', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(r.status === 429 ? 'rate' : 'http');
    track('coverage-ask-sent');
    document.getElementById('pf-coverage-form').outerHTML =
      '<div class="pfc-thanks">Added to the list \u2014 requests like this decide what we verify next.</div>';
    _covPending = null;
  } catch (e) {
    btn.disabled = false;
    status.textContent = e.message === 'rate'
      ? 'We got your earlier requests \u2014 that\u2019s plenty for today.'
      : 'Couldn\u2019t send right now \u2014 try again in a minute.';
  }
}

/* Ask-links live inside innerHTML-built empty states — delegate the clicks. */
document.getElementById('pf-results').addEventListener('click', e => {
  const ask = e.target.closest('.pfc-ask');
  if (ask) pfCoverageOpen(ask.dataset.kind, ask);
});

document.getElementById('pf-go').addEventListener('click', pfRunSearch);
['pf-year', 'pf-make', 'pf-model'].forEach(id => {
  document.getElementById(id).addEventListener('change', () => {
    if (id === 'pf-make') pfPopulateModels();
    // Keep a chosen engine family across car-field changes: a browse-mode
    // "Vortec 5.3" pick survives adding a make filter, and carries into the
    // fitment flow when it's valid for the car (the chips validate it).
    // Only the sticky escape hatch resets — "my engine isn't listed" for an
    // old car must never silence a new one.
    if (pfChosenFam === '__none__') pfChosenFam = null;
    pfMaybeSearch();
  });
});
/* ===== PARTS-TAB WHERE CONTROLS (owner request, 2026-10-23) ==============
 * The Parts search always ran inside the app's zip/radius — these controls
 * make that visible on the tab itself. Same stored center (setZipCenter,
 * jh_zip) and radius (jh_radius) as the Live and Yards tabs — one
 * implementation, three entry points — with the identical free 250 mi cap
 * and Pro gate. Changing either re-runs whatever search/browse is on
 * screen; with no part picked yet, the try-example chips recompute for the
 * new area instead. */
document.getElementById('pf-zip').addEventListener('input', async e => {
  const v = e.target.value.trim();
  document.getElementById('live-zip').value = v;
  await setZipCenter(v);
  updateZipBanner();
  if (pfCat) pfRunSearch(); else pfRenderTry();
});
document.getElementById('pf-radius').addEventListener('change', e => {
  const sel = e.target;
  if (!isPro() && (sel.value === '' || parseFloat(sel.value) > FREE_MAX_RADIUS_MI)) {
    const trigger = sel.value === '' ? 'radius-any-distance' : 'radius-' + sel.value + 'mi';
    // Snap back to the radius actually in effect (the Live select is the
    // source of truth), then pitch — identical to the Yards-tab gate.
    sel.value = document.getElementById('live-radius').value || String(FREE_MAX_RADIUS_MI);
    openUpgradeSheet(trigger);
    return;
  }
  document.getElementById('live-radius').value = sel.value;
  localStorage.setItem('jh_radius', sel.value);
  if (pfCat) pfRunSearch();
});
/* Resync so the three tabs' where controls never disagree: on every Parts
 * visit, and whenever the center changes elsewhere (zip banner, GPS). The
 * zip is left alone while the user is typing in it. */
function pfSyncWhere() {
  const pr = document.getElementById('pf-radius');
  if (!pr) return;
  pr.value = document.getElementById('live-radius').value;
  const pz = document.getElementById('pf-zip');
  const lz = document.getElementById('live-zip');
  if (document.activeElement !== pz) {
    pz.value = lz.value;
    pz.placeholder = lz.placeholder;   // carries 'Using your location' when GPS is the center
  }
}

/* ===== TRY-EXAMPLE CHIPS (owner request, 2026-10-23) =====================
 * The empty Parts tab used to greet people with a paragraph of instructions;
 * now it greets them with 2-3 one-tap examples that prefill AND run. Picks
 * are computed from the live inventory near the user's zip — the commonest
 * covered car for a fitment query, the engine family with the most donors on
 * rows for a hunt, the spotted part nearby yards list most for a browse — so
 * the first tap always lands on results. Nationwide-common picks fill in
 * when no zip is set (or the area is sparse). One hint line survives: the
 * engine-hunt move isn't guessable from the controls (the owner stumbled
 * there); everything else the examples teach by doing. */
let _pfTry = null, _pfTryKey = null;

function pfTryExamples() {
  const radius = effectiveRadiusMi() || 100;  // examples should be NEAR
  const key = (activeZipCoords ? activeZipCoords.lat + ',' + activeZipCoords.lng : 'nozip') + '|' + radius;
  if (_pfTry && _pfTryKey === key) return _pfTry;
  const cats = interchangeData.categories;
  const catById = id => cats.find(c => c.id === id);
  const ex = { fit: null, hunt: null, browse: null };

  if (activeZipCoords && liveInventory.length) {
    // Index family applications by make|model so the tally pass is a map
    // lookup per car, not a scan of 180+ families per car.
    const famIdx = new Map();
    for (const f of interchangeData.engineFamilies) {
      for (const a of f.apps) {
        if (a[1].endsWith('*')) continue;
        for (const mk of a[0].split('|')) {
          const k = pfSquash(mk) + '|' + pfSquashModel(a[1], mk);
          if (!famIdx.has(k)) famIdx.set(k, new Set());
          famIdx.get(k).add(f);
        }
      }
    }
    const browseCands = ['tailgate', 'headlights', 'front-seats', 'side-mirrors']
      .map(catById).filter(Boolean);
    const models = new Map();   // covered models in range, by popularity
    const famN = new Map();     // engine family -> in-range donor count
    const browseN = new Map();  // spotted-part category -> in-range hits
    for (const v of liveInventory) {
      const d = vehicleDistanceMi(v);
      if (d == null || d > radius) continue;
      const make = canonicalMake(v.make);
      const model = canonicalModel(v.make, v.model);
      const k = pfSquash(make) + '|' + pfSquashModel(model, make);
      const fams = famIdx.get(k);
      let covered = false;
      if (fams) for (const f of fams) {
        if (!f.apps.some(a => pfAppMatches(a, v.year, make, v.model))) continue;
        covered = true;
        famN.set(f, (famN.get(f) || 0) + 1);
      }
      if (covered) {
        let m = models.get(k);
        if (!m) models.set(k, m = { make, model, byYear: new Map(), n: 0 });
        m.n++;
        m.byYear.set(v.year, (m.byYear.get(v.year) || 0) + 1);
      }
      for (const p of (v.topParts || [])) {
        for (const c of browseCands) {
          const toks = c.tokens.length ? c.tokens : [c.label];
          if (toks.some(t => partQueryHit(p, t.toLowerCase()))) {
            browseN.set(c, (browseN.get(c) || 0) + 1);
          }
        }
      }
    }
    // Fitment pick: commonest in-range model with a year that maps to exactly
    // ONE alternator-covered family — one tap, straight to donor rows, no
    // which-engine chooser stop in between. Prefer a year sitting inside a
    // verified group so the showcase search carries Verified-fit rows (a
    // first impression of all-Likely undersells the tier system).
    const alt = catById('alternator');
    const byCount = [...models.values()].sort((a, b) => b.n - a.n);
    let fitFallback = null;
    outer: for (const m of byCount.slice(0, 25)) {
      if (m.n < 3) break;
      const years = [...m.byYear.entries()].sort((a, b) => b[1] - a[1]).map(e => e[0]);
      for (const y of years) {
        const fams = interchangeData.engineFamilies.filter(f => {
          const p = f.parts[alt.id];
          return p && (!p.years || (y >= p.years[0] && y <= p.years[1]))
            && f.apps.some(a => pfAppMatches(a, y, m.make, m.model));
        });
        if (fams.length !== 1) continue;
        const pick = { label: `Alternator — ${y} ${m.make} ${m.model}`,
                       run: () => pfTryRun(alt, { year: y, make: m.make, model: m.model }) };
        const vg = fams[0].parts[alt.id].vg;
        if (vg && vg.some(g => g.some(sp => pfAppMatches(sp, y, m.make, m.model)))) {
          ex.fit = pick;
          break outer;
        }
        if (!fitFallback) fitFallback = pick;
      }
    }
    if (!ex.fit) ex.fit = fitFallback;
    // Hunt pick: the engine family with the most donors on rows near you.
    const topFam = [...famN.entries()].sort((a, b) => b[1] - a[1])[0];
    if (topFam && topFam[1] >= 3) {
      const f = topFam[0];
      ex.hunt = { label: `Hunt a ${f.label.replace(/\s*\(.*\)$/, '')} engine`,
                  run: () => pfTryRun(catById('engine-assembly'), null, f.id) };
    }
    // Browse pick: the spotted body part nearby yards list most.
    const topB = [...browseN.entries()].sort((a, b) => b[1] - a[1])[0];
    if (topB && topB[1] >= 2) {
      const c = topB[0];
      const noun = c.label.toLowerCase();
      ex.browse = { label: `Browse ${noun}${noun.endsWith('s') ? '' : 's'} near you`,
                    run: () => pfTryRun(c, null) };
    }
  }
  // Nationwide-common fallbacks fill any empty slot.
  if (!ex.fit) {
    const alt = catById('alternator');
    ex.fit = { label: 'Alternator — 2005 Toyota Camry',
               run: () => pfTryRun(alt, { year: 2005, make: 'Toyota', model: 'Camry' }) };
  }
  if (!ex.hunt) {
    const f = interchangeData.engineFamilies.find(x => x.label.startsWith('GM Gen III Vortec'));
    if (f) ex.hunt = { label: `Hunt a ${f.label.replace(/\s*\(.*\)$/, '')} engine`,
                       run: () => pfTryRun(catById('engine-assembly'), null, f.id) };
  }
  if (!ex.browse) {
    const c = catById('tailgate');
    if (c) ex.browse = { label: 'Browse tailgates near you', run: () => pfTryRun(c, null) };
  }
  _pfTry = [ex.fit, ex.hunt, ex.browse].filter(Boolean);
  _pfTryKey = key;
  return _pfTry;
}

function pfTryRun(cat, car, famId) {
  track('pf-try-chip');
  pfCat = cat;
  pfPartInput.value = cat.label;
  pfChosenFam = famId || null;
  document.getElementById('pf-year').value = car ? String(car.year) : '';
  document.getElementById('pf-make').value = car ? car.make : '';
  pfPopulateModels();
  document.getElementById('pf-model').value = car ? car.model : '';
  if (!activeZipCoords) {
    // Keep the chips on screen — the generic empty state would eat them.
    document.getElementById('pf-status').textContent =
      'Set a zip (or use your location) up top, then tap an example.';
    return;
  }
  pfRunSearch();
}

function pfRenderTry() {
  const out = document.getElementById('pf-results');
  // Only greet an idle results area — never stomp on real search output.
  if (out.querySelector('.pf-row-card, .pf-results-head, .pf-empty:not(.pf-vonly-none), .pf-coverage-form')) return;
  if (!interchangeData) return;
  const ex = pfTryExamples();
  out.innerHTML =
    `<div class="pf-try"><span class="pf-try-label">Try:</span>`
    + ex.map((e, i) => `<button type="button" class="pf-chip pf-try-chip" data-try="${i}">${escapeHtml(e.label)}</button>`).join('')
    + `</div>`
    + `<div class="pf-hint">Hunting an engine? Pick &ldquo;Engine assembly&rdquo; as the part, then choose your engine.</div>`;
}
document.getElementById('pf-results').addEventListener('click', e => {
  const chip = e.target.closest('.pf-try-chip');
  if (chip && _pfTry && _pfTry[chip.dataset.try]) _pfTry[chip.dataset.try].run();
});

/* The Parts tab owns the finder now: data loads lazily on first visit, the
 * last search is restored so a returning user is one tap from results, and
 * an idle results area greets every visit with the try-example chips
 * (recomputed if the zip changed since last look). */
let pfInited = false;
function initPartsTab() {
  pfSyncWhere();   // pick up any zip/radius change made on the other tabs
  if (pfInited) { loadInterchange().then(pfRenderTry); return; }
  pfInited = true;
  track('part-finder-open');
  loadInterchange().then(() => {
    pfPopulatePickers();
    try {
      const saved = JSON.parse(localStorage.getItem('jh_pf') || 'null');
      if (saved && !pfCat) {
        const cat = (interchangeData ? interchangeData.categories : []).find(c => c.id === saved.cat);
        if (cat) { pfCat = cat; pfPartInput.value = cat.label; }
        if (saved.year) document.getElementById('pf-year').value = saved.year;
        if (saved.make) { document.getElementById('pf-make').value = saved.make; pfPopulateModels(); }
        if (saved.model) document.getElementById('pf-model').value = saved.model;
      }
    } catch (e) { /* corrupt saved state — start clean */ }
    pfRenderTry();
  });
}
// Quiet hand-off to the Yards price comparison — the compare feature lives
// there; we just carry the chosen part across and let its combobox resolve.
document.getElementById('pf-compare-link').addEventListener('click', () => {
  const label = pfCat ? pfCat.label : '';
  document.querySelector('.tab[data-tab="yards"]').click();
  if (label) {
    compareInput.value = label;
    document.getElementById('compare-go').click();
  } else {
    compareInput.focus();
  }
});
document.getElementById('yards-filter-chain').addEventListener('change', renderYards);
document.getElementById('yards-filter-state').addEventListener('change', renderYards);

/* ===== PROFIT BREAKDOWN ===== */
/* ===== TABS ===== */
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
    if (tab.dataset.tab === 'yards') renderYards();
    if (tab.dataset.tab === 'live') renderLive();
    if (tab.dataset.tab === 'parts') initPartsTab();
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
function saveWatchlist(list) {
  localStorage.setItem(WATCHLIST_KEY, JSON.stringify(list));
  // Native app: mirror watches to the alert backend (no-op until push enabled).
  if (IS_NATIVE && typeof syncDeviceRegistration === 'function') syncDeviceRegistration();
  // Web Pro members with email alerts on: mirror watches for email dispatch
  // (no-op for free users / alerts off — see the EMAIL ALERTS section).
  if (!IS_NATIVE && typeof syncEmailAlertWatches === 'function') syncEmailAlertWatches();
}
function loadAlerted() {
  try { return JSON.parse(localStorage.getItem(ALERTED_KEY)) || {}; }
  catch { return {}; }
}
function saveAlerted(obj) { localStorage.setItem(ALERTED_KEY, JSON.stringify(obj)); }

function watchlistMatches(entry, v) {
  // Canonicalize BOTH makes: a watch saved as "MINI Cooper" or "Vw" before
  // the 2026-10 make merge must keep matching the merged inventory.
  const makeLow = canonicalMake(entry.make).toLowerCase();
  const modelLow = (entry.model || '').toLowerCase();
  if (makeLow && !canonicalMake(v.make).toLowerCase().includes(makeLow)) return false;
  if (modelLow) {
    // Match raw yard spelling OR the canonical alias (so a watch for "WRX"
    // catches a car a yard filed as "Impreza WRX", and vice versa).
    const rawMatch = (v.model || '').toLowerCase().includes(modelLow);
    const canonMatch = String(canonicalModel(v.make, v.model) || '').toLowerCase()
      === String(canonicalModel(entry.make, entry.model) || '').toLowerCase();
    if (!rawMatch && !canonMatch) return false;
  }
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
  // Email-alerts panel state (web only; defined in the EMAIL ALERTS section).
  if (typeof refreshEmailAlertsUi === 'function') refreshEmailAlertsUi();

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
          <span class="wl-name">${escapeHtml(label)}</span>
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
  allHitVehicles.sort((a, b) => yardDateMs(b.dateAdded) - yardDateMs(a.dateAdded));

  const grid = document.getElementById('alert-matches-grid');
  if (!allHitVehicles.length) {
    grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1;"><h3>No matches yet</h3><p>None of your watchlist vehicles are in the yard right now. The scraper checks automatically in <code>--watch</code> mode.</p></div>';
    return;
  }

  grid.innerHTML = allHitVehicles.slice(0, 100).map(v => {
    const isMatch = v.hasMatch;
    const setOutDate = parseYardDate(v.dateAdded);
    const dateStr = setOutDate ? setOutDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';
    const matchedRules = watchlist.filter(e => watchlistMatches(e, v)).map(e =>
      [e.make, e.model].filter(Boolean).join(' ') || 'Any'
    );
    return `
      <div class="car-card match-card" style="--tier-color:var(--accent);">
        <div class="car-header">
          <div style="min-width:0;">
            <div class="car-name">${escapeHtml(`${v.year} ${v.make} ${v.model}`)}</div>
            <div class="live-card-location">${ICON.pin} <span class="loc-name">${escapeHtml(v.location)}</span>${(() => { const d = vehicleDistanceMi(v); return d != null ? ' <span class="dist">&middot; ' + Math.round(d) + ' mi</span>' : ''; })()}${v.row ? '<span class="live-card-row">Row ' + escapeHtml(v.row) + '</span>' : ''}${saleBadgeHtml(v.location)}</div>
            <div class="car-meta">${dateStr ? `<span title="Set-out date published by the yard">Set out ${dateStr}</span>` : 'Set-out date unknown'}${vinMetaHtml(v)} &middot; matched: ${matchedRules.join(', ')}</div>
          </div>
          <div class="car-badges">
            <span class="badge badge-new">Watchlist hit</span>
          </div>
        </div>
        ${isMatch && v.topParts && v.topParts.length ? `
          <details class="parts-details">
            <summary>Up to ${v.topParts.length} part${v.topParts.length > 1 ? 's' : ''} to check <span class="chev">${ICON.chev}</span></summary>
            <div class="car-body">
              <ul class="parts-list">
                ${v.topParts.slice(0, 5).map(p => `
                  <li class="part-item">
                    <span class="part-name">${escapeHtml(p.name)}</span>
                    
                    ${isPro()
                      ? `<span class="part-price" title="Typical online price for this used part (eBay sold listings, national) — what you\u2019d pay if you didn\u2019t pull it yourself">Used online: ~${formatPrice(p.low)}&ndash;${formatPrice(p.high)}</span>`
                      : `<span class="part-price locked-blur" role="button" onclick="openUpgradeSheet('alerts-value')">Used online: ${LOCKED_PRICE_MASK}</span>`}
                  </li>
                `).join('')}
              </ul>
            </div>
          </details>
        ` : ''}
        ${yardSiteLinkHtml(v)}
      </div>`;
  }).join('');
}

/* True when an existing watch already covers this make+model (an "any model"
 * watch on the make counts). Drives the bell state on car cards. */
function hasWatchFor(make, model) {
  if (!make) return false;
  // canonicalMake on both sides: a pre-merge watch saved as "MINI Cooper"
  // still lights the bell on a (now-canonical) MINI card.
  // canonicalModel on both sides: a pre-merge watch saved as 'Mazda 3' or
  // 'F250Sd Pickup' still lights the bell on the renamed card.
  return loadWatchlist().some(e =>
    canonicalMake(e.make).toLowerCase() === canonicalMake(make).toLowerCase() &&
    (!e.model || String(canonicalModel(e.make, e.model) || '').toLowerCase()
      === String(canonicalModel(make, model) || '').toLowerCase()));
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
  const raw = (document.getElementById('alert-model-search').value || '').trim();
  const models = [..._watchModelCounts.keys()].sort()
    .filter(m => modelSearchMatch(m, q));  // same squashed match as the live filter
  const rows = models.map(m => `
    <label class="multi-select-row">
      <input type="checkbox" data-model="${escapeHtml(m)}" ${watchSelectedModels.has(m) ? 'checked' : ''}>
      <span>${escapeHtml(m)}</span>
    </label>`);
  // "Watch anyway": the picker only lists models sitting in a tracked yard
  // right now, so an '86 Celica can't be watched until one lands. When the
  // typed text matches no listed model, offer it as a free-text watch. The
  // stored string goes through the same canonicalModel/substring matching
  // as picked models (watchlistMatches), so it fires when one shows up.
  if (raw && !models.some(m => modelSearchMatch(m, q) && modelSearchMatch(q, m))) {
    rows.push(`
    <label class="multi-select-row multi-select-row-free">
      <input type="checkbox" data-model="${escapeHtml(raw)}" ${watchSelectedModels.has(raw) ? 'checked' : ''}>
      <span>Watch &ldquo;${escapeHtml(raw)}&rdquo; anyway</span>
    </label>
    <div class="multi-select-empty multi-select-note">None in the rows right now &mdash; we&rsquo;ll alert you when one lands.</div>`);
  }
  list.innerHTML = rows.length ? rows.join('')
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
    return alert('Set a zip code (or use "near me") in the Cars tab first, so the radius has a center.');
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
  const apiMode = !IS_NATIVE && window.YSApi && YSApi.enabled();
  panel.style.display = apiMode ? '' : 'none';
  // Web visitors get pointed at the iOS app for real push; the native app
  // has its own APNs panel instead.
  const webPush = document.getElementById('appstore-alerts-panel');
  if (webPush) webPush.style.display = (apiMode || IS_NATIVE) ? 'none' : '';
  const nativeNote = document.getElementById('native-alerts-note');
  if (nativeNote) nativeNote.style.display = IS_NATIVE ? '' : 'none';
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
// Native app: the web Notification API doesn't exist in the WKWebView — hide
// the dead button and swap the intro copy (no "browser notification" talk).
if (IS_NATIVE) {
  document.getElementById('alert-notif-btn').style.display = 'none';
  const intro = document.getElementById('alerts-intro-copy');
  if (intro) intro.innerHTML = 'Add vehicles you want to track &mdash; watching is free, '
    + 'no signup, no email. Free watches get a <strong>weekly recap push</strong>; '
    + '<strong>push alerts within hours</strong> of a car hitting the yard are Pro.';
}

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
// shared-find suppression) immediately instead of after the ~37MB fetch.
applyShareHash();
updateZipBanner();
// Launched via an alert deep link (#alert=<id> in web-push / FCM / APNs
// payload urls): normalize to the #car= focus form and make the first fetch
// bypass the HTTP cache — the alert exists because a newer scan published.
const _bootAlertId = (location.hash.match(/#alert=([^&]+)/) || [])[1] || null;
if (_bootAlertId) {
  history.replaceState(null, '', location.pathname + location.search + '#car=' + _bootAlertId);
}
loadLiveInventory({ fresh: !!_bootAlertId });
// #tab=<name> opens a tab directly (share pages link to #tab=alerts).
{
  const t = (location.hash.match(/#tab=([a-z]+)/) || [])[1];
  const el = t && document.querySelector(`.tab[data-tab="${t}"]`);
  if (el) { el.click(); history.replaceState(null, '', location.pathname + location.search); }
}

// Offline + instant-launch cache. Needs a secure context (HTTPS or localhost) —
// silently skipped when served over plain LAN IP, active once on GitHub Pages.
if (!IS_NATIVE && 'serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js').catch(() => {});
  // Web-push tap while the app is already open: sw.js focuses this window
  // and posts the alert url (navigating would reload the whole app).
  navigator.serviceWorker.addEventListener('message', (e) => {
    const url = e.data && e.data.type === 'open-alert' && e.data.url;
    if (!url) return;
    const m = String(url).match(/#(?:alert|car)=([^&]+)/);
    openFromAlert(m ? safeDecode(m[1]) : null);
  });
}

/* ===== NATIVE APP PROMO =====
 * Replaces the old add-to-home-screen hint now that the native apps are live.
 * Mobile-browser visitors get a one-time, dismissible pointer at the store
 * for their platform (App Store / Google Play). Never shown in the native
 * shells (IS_NATIVE — the same bundle ships into them via native/stage.sh),
 * in an installed PWA (standalone display-mode), or on desktop. iOS Safari
 * additionally gets the system Smart App Banner via the apple-itunes-app
 * meta tag in index.html; Android Chrome gets the native Play-install offer
 * via related_applications in manifest.webmanifest.
 * Test hook: ?appbanner=ios|android forces the platform for QA. */
(function appPromo() {
  const APP_STORE_URL = 'https://apps.apple.com/app/yardscout-junkyard-parts/id6817126581';
  const PLAY_URL = 'https://play.google.com/store/apps/details?id=io.yardscout.app';
  if (IS_NATIVE) return; // already inside the native app — never promote
  const qs = new URLSearchParams(location.search).get('appbanner');
  const forced = (qs === 'ios' || qs === 'android') ? qs : null;
  const standalone = window.matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
  const isIOS = /iphone|ipod|ipad/i.test(navigator.userAgent)
    || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1); // iPadOS
  const isAndroid = /android/i.test(navigator.userAgent);
  const platform = forced || (isIOS ? 'ios' : (isAndroid ? 'android' : null));
  if (!platform) return; // desktop: unchanged
  if (!forced && (standalone || localStorage.getItem('ys_app_promo') === '1')) return;
  // First visit is for the cars, not the install pitch: show from the
  // second visit on.
  let visits = 0;
  try { visits = parseInt(localStorage.getItem('jh_visits') || '0', 10) + 1; localStorage.setItem('jh_visits', String(visits)); } catch (e) { visits = 2; }
  if (visits < 2) return;
  const el = document.getElementById('app-promo');
  if (!el) return;
  const link = document.getElementById('app-promo-link');
  link.href = platform === 'android' ? PLAY_URL : APP_STORE_URL;
  link.textContent = platform === 'android' ? 'Google Play' : 'App Store';
  el.style.display = '';
  document.getElementById('app-promo-close').addEventListener('click', () => {
    localStorage.setItem('ys_app_promo', '1');
    el.style.display = 'none';
  });
})();

/* ===== STORE BADGES (header + footer) =====
 * Persistent, quiet store presence to complement the mobile-only promo above:
 * official Apple / Google Play badges right-aligned in the header on
 * desktop/tablet widths (>=768px — CSS keeps phones on the banner alone) and
 * a standard-size pair in the footer by Privacy/Terms at every width.
 * Gating mirrors appPromo: never inside the native shells (IS_NATIVE);
 * installed PWAs get footer badges but no header push; and while the mobile
 * promo banner is showing, the banner stays the only above-the-fold promo —
 * header badges wait until it's been dismissed. */
(function storeBadges() {
  if (IS_NATIVE) return; // never promote the store from inside the store build
  const standalone = window.matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
  document.body.classList.add('has-store-badges'); // footer pair: all web contexts
  const promo = document.getElementById('app-promo');
  const promoShowing = !!promo && promo.style.display !== 'none';
  if (!standalone && !promoShowing) document.body.classList.add('has-header-badges');
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

/* ===== NATIVE (iOS + Android): store IAP + push alerts (iOS only) =====
 * Everything below is inert on the web (IS_NATIVE false).
 *
 * IAP: both platforms expose the SAME Capacitor plugin surface as
 * window.Capacitor.Plugins.Purchases — StoreKit 2 on iOS
 * (ios/App/App/PurchasesPlugin.swift), Google Play Billing on Android
 * (android/app/src/main/java/com/benvuolo/yardscout/PurchasesPlugin.java).
 * The store is the account — subscribe with Face ID / Play auth, restore on
 * any device, no signup. The upgrade sheet shows a real Subscribe button
 * whenever the store product loads (so a build without store-console config
 * degrades to a "can't reach the store" status automatically).
 *
 * Push: official @capacitor/push-notifications plugin + the Worker's
 * anonymous device model (/v1/device/register). Free = weekly recap push,
 * Pro = instant. Watches mirror to the server on every change. The plugin's
 * 'registration' event hands back an APNs token on iOS and an FCM token on
 * Android — the only platform difference below is which field carries it. */

const NATIVE_API_BASE = 'https://yardscout-api.yardscout.workers.dev';
// Same product id on both stores: App Store subscription + Play subscription.
const IAP_PRODUCT_ID = 'yardscout_pro_monthly';
const STORE_NAME = IS_ANDROID ? 'Google Play' : 'the App Store';
const STORE_ACCOUNT = IS_ANDROID ? 'Google account' : 'Apple account';

function nativePlugin(name) {
  return (IS_NATIVE && window.Capacitor && window.Capacitor.Plugins
    && window.Capacitor.Plugins[name]) || null;
}

function deviceId() {
  let id = localStorage.getItem('ys_device_id');
  if (!id) { id = crypto.randomUUID(); localStorage.setItem('ys_device_id', id); }
  return id;
}

/* Mirror local watches to the Worker keyed by device id + push token
 * (APNs on iOS, FCM on Android). 'ys_apns_token' is the legacy iOS
 * storage key — kept as a read fallback so existing installs don't
 * re-prompt; new writes land in 'ys_push_token'. */
function storedPushToken() {
  return localStorage.getItem('ys_push_token') || localStorage.getItem('ys_apns_token');
}

async function syncDeviceRegistration(freshToken) {
  if (!IS_NATIVE || !NATIVE_API_BASE) return;
  const token = freshToken || storedPushToken();
  if (!token) return;   // nothing to sync until push is enabled
  try {
    const body = {
      deviceId: deviceId(),
      platform: IS_ANDROID ? 'android' : 'ios',
      tier: isPro() ? 'pro' : 'free',
      watches: loadWatchlist().map((w) => ({
        make: w.make, model: w.model, yearMin: w.yrMin, yearMax: w.yrMax,
        // Rounded to ~1 km: the Worker only needs a radius centre, never
        // the exact GPS fix — and the privacy policy promises as much.
        lat: w.lat == null ? w.lat : Math.round(w.lat * 100) / 100,
        lng: w.lng == null ? w.lng : Math.round(w.lng * 100) / 100,
        radiusMi: w.radiusMi,
      })),
    };
    body[IS_ANDROID ? 'fcmToken' : 'apnsToken'] = token;
    await fetch(NATIVE_API_BASE + '/v1/device/register', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
  } catch (e) { /* re-synced on next change/launch */ }
}

/* ---- push enable flow (native Alerts tab) ---- */
(function nativePushInit() {
  if (!IS_NATIVE) return;
  const btn = document.getElementById('native-push-enable');
  const status = document.getElementById('native-push-status');
  const PN = nativePlugin('PushNotifications');
  if (!btn) return;
  if (!PN || !NATIVE_API_BASE) {
    // Plugin missing or backend not deployed yet — honest "coming soon".
    btn.style.display = 'none';
    if (status) status.textContent = 'Push alerts are coming in the next update — watches still light up in-app.';
    return;
  }

  PN.addListener('registration', async (t) => {
    // iOS fires this only after register(); Android ALSO fires it at app
    // start (FCM mints tokens eagerly via onNewToken) — before the user
    // asked for anything. Only treat it as "push is on" when the user
    // explicitly enabled alerts AND the OS display permission is granted
    // (Android 13+ POST_NOTIFICATIONS; silently-dropped pushes are worse
    // than no pushes).
    const wanted = localStorage.getItem('ys_push_on') === '1'
      || localStorage.getItem('ys_push_intent') === '1';
    if (!wanted) return;
    let perm = { receive: 'granted' };
    try { perm = await PN.checkPermissions(); } catch (e) { /* assume ok */ }
    if (perm.receive !== 'granted') return;
    localStorage.setItem('ys_push_token', t.value);
    localStorage.setItem('ys_push_on', '1');
    localStorage.removeItem('ys_push_intent');
    await syncDeviceRegistration(t.value);
    btn.style.display = 'none';
    if (status) status.textContent = isPro()
      ? 'Push is on — you\u2019ll hear within hours of a watched car landing.'
      : 'Push is on — your weekly recap arrives Monday morning.';
  });
  PN.addListener('registrationError', (e) => {
    if (status) status.textContent = 'Could not register for push — try again later.';
    console.log('push registration error', e);
  });
  PN.addListener('pushNotificationActionPerformed', (action) => {
    // Notification tap. New payloads carry url:'/#alert=<vehicleId>' — a
    // top-level key in the APNs JSON, data.url in FCM; the plugin surfaces
    // both as notification.data.url (iOS: full userInfo; Android: intent
    // extras, warm AND cold start — BridgeActivity replays the launch
    // intent). openFromAlert refetches fresh inventory and lands on the
    // car's card. Old payloads without a url fall back to the Alerts tab.
    const data = (action && action.notification && action.notification.data) || {};
    const m = String(data.url || '').match(/#(?:alert|car)=([^&]+)/);
    openFromAlert(m ? safeDecode(m[1]) : null);
  });

  // Permission is requested HERE, on the user's explicit "enable alerts" tap —
  // never at app open. On Android 13+ requestPermissions() surfaces the
  // POST_NOTIFICATIONS runtime prompt; on iOS it's the APNs dialog.
  btn.addEventListener('click', async () => {
    track('native-push-enable');
    localStorage.setItem('ys_push_intent', '1');   // registration listener checks this
    try {
      let perm = await PN.checkPermissions();
      if (perm.receive !== 'granted') perm = await PN.requestPermissions();
      if (perm.receive !== 'granted') {
        localStorage.removeItem('ys_push_intent');
        if (status) status.textContent = 'Notifications are off for YardScout in '
          + (IS_ANDROID ? 'Android' : 'iOS') + ' Settings.';
        return;
      }
      await PN.register();
    } catch (e) {
      if (status) status.textContent = 'Push setup failed — try again later.';
    }
  });

  // Already enabled previously: refresh the token + mirror watches silently —
  // but re-verify the display permission first (revocable in OS settings,
  // and pre-fix Android builds could set ys_push_on without it).
  if (localStorage.getItem('ys_push_on') === '1') {
    (async () => {
      try {
        const perm = await PN.checkPermissions();
        if (perm.receive !== 'granted') {
          localStorage.removeItem('ys_push_on');   // button stays visible
          return;
        }
        btn.style.display = 'none';
        if (status) status.textContent = 'Push alerts are on for this device.';
        await PN.register();
      } catch (e) { /* retried next launch */ }
    })();
  }
})();

/* ---- IAP: entitlement on launch + upgrade sheet flow ---- */
function grantNativePro() {
  localStorage.setItem('jh_pro', '1');
  localStorage.setItem('jh_pro_source', 'iap');
  applyProGates();
  if (typeof liveLoaded !== 'undefined' && liveLoaded) renderLive();
  syncDeviceRegistration();
}

function revokeNativePro() {
  if (localStorage.getItem('jh_pro_source') !== 'iap') return; // never touch dev toggle
  localStorage.removeItem('jh_pro');
  localStorage.removeItem('jh_pro_source');
  applyProGates();
  if (typeof liveLoaded !== 'undefined' && liveLoaded) renderLive();
  syncDeviceRegistration();
}

(async function nativeIapInit() {
  if (!IS_NATIVE) return;
  const P = nativePlugin('Purchases');
  if (!P) return;
  // Subscription state is re-derived from StoreKit on every launch: renewals
  // extend it, cancellations lapse at period end, refunds revoke.
  try {
    const r = await P.isEntitled({ productId: IAP_PRODUCT_ID });
    if (r && r.entitled) grantNativePro();
    else revokeNativePro();
  } catch (e) { /* offline: keep last known state */ }

  const subBtn = document.getElementById('iap-subscribe');
  const restoreBtn = document.getElementById('iap-restore');
  const status = document.getElementById('iap-status');
  // The static fine print is written for iOS; reword for Play on Android.
  if (IS_ANDROID) {
    const note = document.getElementById('iap-note');
    if (note) note.innerHTML = 'Auto-renews monthly through your Google Play account &mdash; '
      + 'cancel anytime in Play Store subscriptions. '
      + '<a href="privacy.html">Privacy</a> &middot; <a href="terms.html">Terms</a>.';
    // Push is live on Android as of 1.2 (FCM) — the static "Push alerts
    // within hours" copy is now honest on both platforms, no override needed.
  }
  if (subBtn) subBtn.addEventListener('click', async () => {
    track('iap-subscribe/' + upgradeTrigger);
    subBtn.disabled = true;
    if (status) status.textContent = '';
    try {
      const r = await P.purchase({ productId: IAP_PRODUCT_ID });
      if (r && r.entitled) {
        grantNativePro();
        track('iap-purchased');
        closeUpgradeSheet();
      } else if (r && r.pending) {
        if (status) status.textContent = 'Purchase pending approval — Pro unlocks automatically once approved.';
      } else if (status && !(r && r.cancelled)) {
        status.textContent = 'Purchase did not complete.';
      }
    } catch (e) {
      if (status) status.textContent = e.message || 'Purchase failed.';
    } finally {
      subBtn.disabled = false;
    }
  });
  if (restoreBtn) restoreBtn.addEventListener('click', async () => {
    track('iap-restore');
    restoreBtn.disabled = true;
    try {
      const r = await P.restore();
      if (r && r.entitled) {
        grantNativePro();
        if (status) status.textContent = 'Pro restored on this device.';
        closeUpgradeSheet();
      } else if (status) {
        status.textContent = 'No active subscription found on this ' + STORE_ACCOUNT + '.';
      }
    } catch (e) {
      if (status) status.textContent = e.message || 'Restore failed.';
    } finally {
      restoreBtn.disabled = false;
    }
  });
})();

/* Native upgrade sheet: the StoreKit subscribe flow IS the offer — no
 * waitlist, ever. If the App Store product can't load right now, the button
 * stays (with its baked-in price) and a status line says to retry; the
 * purchase call does its own product lookup, so a tap can still succeed the
 * moment connectivity returns. */
async function refreshNativeIapUi() {
  if (!IS_NATIVE) return;
  if (isPro()) return;   // already Pro — the sheet shows the Pro state instead
  const P = nativePlugin('Purchases');
  const wrap = document.getElementById('native-iap');
  if (!P || !wrap) return;
  wrap.style.display = '';
  const status = document.getElementById('iap-status');
  try {
    const p = await P.getProduct({ productId: IAP_PRODUCT_ID });
    if (p && p.available) {
      const sub = document.getElementById('iap-subscribe');
      if (sub && p.price) sub.textContent = 'Subscribe — ' + p.price + '/mo';
      if (status) status.textContent = '';
    } else if (status) {
      status.textContent = 'Can\u2019t reach ' + STORE_NAME + ' right now — try again in a minute.';
    }
  } catch (e) {
    if (status) status.textContent = 'Can\u2019t reach ' + STORE_NAME + ' right now — try again in a minute.';
  }
}

/* ===== NATIVE → EVERYWHERE: optional email link (iOS 1.4, Android 1.1) =====
 * After a verified store purchase, "Use Pro on other devices" lets the user
 * link an email. Both platforms hand their proof-of-purchase to the
 * entitlement API, which verifies it server-side and makes the email
 * redeemable anywhere via a 6-digit code:
 *   iOS:     StoreKit 2 signed transaction (Purchases.getTransactionJws) →
 *            /verify-ios (offline JWS check against Apple's root cert)
 *   Android: Play Billing purchase token (Purchases.getPurchaseToken) →
 *            /verify-android (server-to-server Play Developer API check)
 *
 * Always optional — never required to buy or to use Pro in this app. The UI
 * mentions no prices and links nowhere (App Review guideline 3.1.1/3.1.3 and
 * the Play equivalent — anti-steering copy stays intact on both platforms). */
(() => {
  if (!IS_NATIVE) return;
  const ENT_API = 'https://yardscout.io/api/ent';
  // Separate keys per store: a device only ever has one store, but the name
  // records WHICH subscription the email is pinned to.
  const LINK_KEY = IS_ANDROID ? 'ys_play_linked_email' : 'ys_ios_linked_email';
  const wrap = () => document.getElementById('ios-link');
  const status = () => document.getElementById('ios-link-status');

  function refreshLinkUi() {
    const el = wrap();
    if (!el) return;
    // Only for a real store entitlement on THIS device (never the
    // email-code path — that email is already linked by definition).
    const show = isPro() && localStorage.getItem('jh_pro_source') === 'iap';
    el.style.display = show ? '' : 'none';
    if (!show) return;
    const P = nativePlugin('Purchases');
    if (!P) {
      el.style.display = 'none';
      return;
    }
    // NOTE: Capacitor's plugin proxy returns a function for ANY method name,
    // so `typeof P.getTransactionJws` can't detect an older shell. The click
    // handler catches the "not implemented" rejection honestly instead.
    const linked = localStorage.getItem(LINK_KEY);
    if (linked) {
      document.getElementById('ios-link-email').value = linked;
      status().textContent = 'Linked to ' + linked + ' — use "Already have Pro?" with that email on any other device.';
    }
  }
  // The sheet re-renders on every open; keep this block in sync then too.
  document.getElementById('pro-pill').addEventListener('click', refreshLinkUi);
  setTimeout(refreshLinkUi, 1500); // after the launch entitlement check

  /* Platform proof-of-purchase → the request body for its verify endpoint.
   * Returns null (with a status message set) when there's nothing to send. */
  async function buildVerifyRequest(P, email) {
    if (IS_ANDROID) {
      const t = await P.getPurchaseToken({ productId: IAP_PRODUCT_ID });
      if (!t || !t.entitled || !t.purchaseToken) return null;
      return {
        path: '/verify-android',
        body: { email, purchaseToken: t.purchaseToken, productId: IAP_PRODUCT_ID },
      };
    }
    const t = await P.getTransactionJws({ productId: IAP_PRODUCT_ID });
    if (!t || !t.entitled || !t.jws) return null;
    return { path: '/verify-ios', body: { email, jws: t.jws } };
  }

  const btn = document.getElementById('ios-link-btn');
  if (btn) btn.addEventListener('click', async () => {
    const email = (document.getElementById('ios-link-email').value || '').trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      status().textContent = 'Enter a valid email address.';
      return;
    }
    const P = nativePlugin('Purchases');
    if (!P) return;
    track(IS_ANDROID ? 'android-link-email' : 'ios-link-email');
    btn.disabled = true;
    status().textContent = 'Linking\u2026';
    // Two separate try/catches so a store/plugin problem is never
    // misreported as a network problem (and vice versa).
    let reqSpec = null;
    try {
      reqSpec = await buildVerifyRequest(P, email);
    } catch (e) {
      // Plugin call rejected — e.g. an older native shell without the
      // method ("not implemented") or a store hiccup.
      status().textContent = /implemented/i.test((e && e.message) || '')
        ? 'This needs the latest YardScout update — update the app and try again.'
        : 'Could not read your subscription from ' + STORE_NAME + ' — try again in a minute.';
      btn.disabled = false;
      return;
    }
    try {
      if (!reqSpec) {
        status().textContent = 'No active subscription found on this device.';
        return;
      }
      // NOTE: no content-type header on purpose — that keeps this a CORS
      // "simple request" (no OPTIONS preflight from capacitor://localhost),
      // which is one less round trip that can fail in the yard. The Worker
      // parses the JSON body regardless of content-type.
      const r = await fetch(ENT_API + reqSpec.path, {
        method: 'POST',
        body: JSON.stringify(reqSpec.body),
      });
      const data = await r.json().catch(() => ({}));
      if (r.ok && data.linked) {
        localStorage.setItem(LINK_KEY, email);
        status().textContent = 'Linked to ' + email + ' — on any other device, choose "Already have Pro?" and enter this email.';
        track(IS_ANDROID ? 'android-link-done' : 'ios-link-done');
      } else {
        status().textContent = data.message || ('Could not link right now (error ' + r.status + ') — try again later.');
      }
    } catch (e) {
      status().textContent = 'Could not reach the server — check your connection and try again.';
    } finally {
      btn.disabled = false;
    }
  });
})();

/* ===== WEB PRO (account-less entitlements) =====
 * Backend: the yardscout.io site Worker (backend/site-proxy/src/entitlements.js).
 * No accounts or passwords — the email given at Stripe Checkout IS the
 * entitlement, and a 6-digit email code unlocks it on any other device.
 * Everything here is WEB ONLY (inert on native — Apple guideline 3.1.1 keeps
 * Stripe out of the app; the native build buys through StoreKit/Play instead).
 *
 * localStorage:
 *   ys_ent_token  device token minted by the Worker (re-validation + billing portal)
 *   ys_ent_email  the entitlement email (display only)
 *   ys_ent_src    'stripe' | 'apple_iap' (portal button is stripe-only)
 *   ys_ent_checked  last successful re-validation (ms epoch)
 * Pro gate: jh_pro='1' + jh_pro_source='account' (accepted by the boot
 * honesty-check alongside the native 'iap' source). */
(() => {
  if (IS_NATIVE) return;

  // Same-origin on yardscout.io; absolute from github.io / localhost.
  // Dev override: ?entbase=http://127.0.0.1:8799 (persisted; ?entbase= clears).
  const ENT_BASE = (() => {
    try {
      const qp = new URLSearchParams(location.search);
      const b = qp.get('entbase');
      if (b) localStorage.setItem('ys_ent_base', b.replace(/\/+$/, ''));
      if (b === '') localStorage.removeItem('ys_ent_base');
    } catch (e) { /* ignore */ }
    return localStorage.getItem('ys_ent_base')
      || (location.hostname === 'yardscout.io' ? '' : 'https://yardscout.io');
  })();

  async function entApi(path, opts) {
    const r = await fetch(ENT_BASE + '/api/ent/' + path, opts);
    const data = await r.json().catch(() => ({}));
    return { ok: r.ok, status: r.status, data };
  }
  // Deliberately NO content-type header: the request stays CORS-"simple"
  // (no OPTIONS preflight — matters from github.io and the native WebView);
  // the Worker parses the JSON body regardless of content-type.
  const postJson = (path, body) => entApi(path, {
    method: 'POST',
    body: JSON.stringify(body),
  });

  const $id = (x) => document.getElementById(x);
  function setMsg(el, msg, isError) {
    if (!el) return;
    el.textContent = msg || '';
    el.style.color = isError ? 'var(--red)' : '';
  }

  /* Show/hide the Pro-state extras (manage billing) for web entitlements. */
  function refreshProActions() {
    const wrap = $id('ent-pro-actions');
    if (!wrap) return;
    const token = localStorage.getItem('ys_ent_token');
    const hasWebEnt = !!token && localStorage.getItem('jh_pro_source') === 'account';
    wrap.style.display = hasWebEnt ? '' : 'none';
    const portal = $id('ent-portal');
    if (portal) portal.style.display = (hasWebEnt && localStorage.getItem('ys_ent_src') === 'stripe') ? '' : 'none';
    const email = localStorage.getItem('ys_ent_email');
    if (hasWebEnt && email) setMsg($id('ent-pro-status'), 'Pro is linked to ' + email + '.');
  }

  // Exposed for the email-alerts panel's inline link flow (same grant path
  // as checkout-return and code-redeem; see the EMAIL ALERTS section).
  window.ysGrantWebPro = (args) => grantWebPro(args);

  function grantWebPro({ email, token, source, note }) {
    localStorage.setItem('jh_pro', '1');
    localStorage.setItem('jh_pro_source', 'account');
    if (token) localStorage.setItem('ys_ent_token', token);
    if (email) localStorage.setItem('ys_ent_email', email);
    if (source) localStorage.setItem('ys_ent_src', source);
    localStorage.setItem('ys_ent_checked', String(Date.now()));
    applyProGates();
    if (typeof liveLoaded !== 'undefined' && liveLoaded) renderLive();
    refreshProActions();
    if (typeof refreshEmailAlertsUi === 'function') refreshEmailAlertsUi();
    if (note) setMsg($id('ent-pro-status'), note);
  }

  function revokeWebPro() {
    if (localStorage.getItem('jh_pro_source') !== 'account') return;
    localStorage.removeItem('jh_pro');
    localStorage.removeItem('jh_pro_source');
    localStorage.removeItem('ys_ent_token');
    localStorage.removeItem('ys_ent_src');
    localStorage.removeItem('ys_ent_checked');
    applyProGates();
    if (typeof liveLoaded !== 'undefined' && liveLoaded) renderLive();
    refreshProActions();
    if (typeof refreshEmailAlertsUi === 'function') refreshEmailAlertsUi();
  }

  /* ---- purchase button: shown only once the Worker reports billing live ---- */
  (async () => {
    try {
      const { ok, data } = await entApi('config');
      if (ok && data.billing) {
        const buy = $id('ent-buy');
        if (buy) buy.style.display = '';
        const head = $id('ent-appstore-head');
        if (head) head.textContent = 'Prefer the app?';
        // The static sheet intro ends "Subscribe in the YardScout iOS app." —
        // contradicts the live web checkout button right below it.
        const sub = document.querySelector('#upgrade-sheet .sheet-sub');
        if (sub) sub.textContent = sub.textContent.replace(
          'Subscribe in the YardScout iOS app.',
          'Subscribe right here or in the YardScout app; cancel anytime.');
      }
    } catch (e) { /* worker unreachable → App-Store-only copy stands */ }
  })();

  const checkoutBtn = $id('ent-checkout');
  if (checkoutBtn) checkoutBtn.addEventListener('click', async () => {
    track('ent-checkout-start');
    checkoutBtn.disabled = true;
    setMsg($id('ent-checkout-status'), 'Opening secure checkout\u2026');
    try {
      const { ok, status, data } = await postJson('checkout', {});
      if (ok && data.url) { location.href = data.url; return; }
      setMsg($id('ent-checkout-status'), status === 503
        ? 'Web checkout isn\u2019t live quite yet — Pro is available in the iOS app.'
        : (data.message || 'Could not start checkout — try again.'), true);
    } catch (e) {
      setMsg($id('ent-checkout-status'), 'Could not reach checkout — check your connection.', true);
    } finally {
      checkoutBtn.disabled = false;
    }
  });

  /* ---- returning from Stripe: ?entco=<session id> (or =cancel) ----
   * The Worker re-confirms payment with Stripe server-side; the URL param
   * alone grants nothing. */
  (async () => {
    let id = null;
    try {
      const qp = new URLSearchParams(location.search);
      id = qp.get('entco');
      if (id !== null) {
        qp.delete('entco');
        const qs = qp.toString();
        history.replaceState(null, '', location.pathname + (qs ? '?' + qs : '') + location.hash);
      }
    } catch (e) { /* ignore */ }
    if (!id || id === 'cancel') {
      if (id === 'cancel') track('ent-checkout-cancel');
      return;
    }
    track('ent-checkout-return');
    openUpgradeSheet('checkout-return');
    setMsg($id('ent-status'), 'Payment received — activating Pro\u2026');
    // The webhook usually lands within seconds; poll the confirm endpoint a few times.
    for (let i = 0; i < 8; i++) {
      try {
        const { ok, data } = await entApi('checkout-session?id=' + encodeURIComponent(id));
        if (ok && data.pro) {
          grantWebPro({ email: data.email, token: data.token, source: 'stripe',
            note: 'Payment received — Pro is unlocked on this device and linked to ' + data.email + '.' });
          track('ent-purchased');
          openUpgradeSheet('checkout-done'); // re-render: now shows the Pro state
          return;
        }
      } catch (e) { /* retry */ }
      await new Promise((res) => setTimeout(res, 2500));
    }
    setMsg($id('ent-status'),
      'Payment received. Activation can take a minute — use "Already have Pro?" with your checkout email if it doesn\u2019t unlock shortly.', true);
  })();

  /* ---- "Already have Pro?" — email a 6-digit code, redeem it here ---- */
  const sendBtn = $id('ent-send-code');
  if (sendBtn) sendBtn.addEventListener('click', async () => {
    const email = ($id('ent-email').value || '').trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setMsg($id('ent-status'), 'Enter a valid email address.', true);
      return;
    }
    track('ent-code-request');
    sendBtn.disabled = true;
    setMsg($id('ent-status'), 'Sending\u2026');
    try {
      const { ok, data } = await postJson('request-code', { email });
      if (ok) {
        $id('ent-code-row').style.display = '';
        $id('ent-code').focus();
        setMsg($id('ent-status'), data.message || 'Check your email for the 6-digit code (expires in 10 minutes).');
      } else {
        setMsg($id('ent-status'), data.message || 'Could not send the code — try again.', true);
      }
    } catch (e) {
      setMsg($id('ent-status'), 'Could not reach the server — check your connection.', true);
    } finally {
      sendBtn.disabled = false;
    }
  });

  const redeemBtn = $id('ent-redeem-btn');
  if (redeemBtn) redeemBtn.addEventListener('click', async () => {
    const email = ($id('ent-email').value || '').trim();
    const code = ($id('ent-code').value || '').trim();
    if (!/^\d{6}$/.test(code)) { setMsg($id('ent-status'), 'Enter the 6-digit code from the email.', true); return; }
    redeemBtn.disabled = true;
    setMsg($id('ent-status'), 'Checking\u2026');
    try {
      const { ok, data } = await postJson('redeem-code', { email, code });
      if (ok && data.pro) {
        grantWebPro({ email, token: data.token, source: data.source,
          note: 'Pro is unlocked on this device — linked to ' + email + '.' });
        track('ent-code-redeemed');
        openUpgradeSheet('code-redeemed'); // re-render into the Pro state
      } else {
        setMsg($id('ent-status'), data.message || 'That code didn\u2019t work — request a new one.', true);
      }
    } catch (e) {
      setMsg($id('ent-status'), 'Could not reach the server — check your connection.', true);
    } finally {
      redeemBtn.disabled = false;
    }
  });
  const codeInput = $id('ent-code');
  if (codeInput) codeInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') redeemBtn.click(); });
  const emailInput = $id('ent-email');
  if (emailInput) emailInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendBtn.click(); });

  /* ---- manage billing (Stripe customer portal; token-gated) ---- */
  const portalBtn = $id('ent-portal');
  if (portalBtn) portalBtn.addEventListener('click', async () => {
    portalBtn.disabled = true;
    try {
      const { ok, data } = await postJson('portal', { token: localStorage.getItem('ys_ent_token') || '' });
      if (ok && data.url) { location.href = data.url; return; }
      setMsg($id('ent-pro-status'), data.message || 'Could not open billing.', true);
    } catch (e) {
      setMsg($id('ent-pro-status'), 'Could not reach the server.', true);
    } finally {
      portalBtn.disabled = false;
    }
  });

  /* ---- daily re-validation: subscriptions lapse honestly ----
   * Only a definitive server "not pro" revokes; network failures keep the
   * last known state (the yard has bad cell signal — don't punish that). */
  (async () => {
    if (localStorage.getItem('jh_pro_source') !== 'account') { refreshProActions(); return; }
    const token = localStorage.getItem('ys_ent_token');
    refreshProActions();
    if (!token) return;
    const last = Number(localStorage.getItem('ys_ent_checked') || 0);
    if (Date.now() - last < 24 * 3600 * 1000) return;
    try {
      const { ok, data } = await entApi('status?token=' + encodeURIComponent(token));
      if (!ok) return;
      if (data.pro) {
        localStorage.setItem('ys_ent_checked', String(Date.now()));
      } else {
        revokeWebPro();
      }
    } catch (e) { /* offline — keep last known state */ }
  })();
})();

/* ===== EMAIL ALERTS (web Pro members) =====
 * The web counterpart of native push: a Pro member's watchlist mirrors to the
 * backend (yardscout-api) keyed by their entitlement email; every inventory
 * scan that finds new matches sends ONE digest email (see
 * backend/src/email_alerts.js). WEB ONLY — IS_NATIVE exits immediately so the
 * panel never appears in the App Store build (same anti-steering pattern as
 * #upgrade-form-wrap); native keeps its push-based story.
 *
 * Exposed on window (called from saveWatchlist / renderAlerts / grantWebPro):
 *   refreshEmailAlertsUi()   — render the Alerts-tab panel for the current state
 *   syncEmailAlertWatches()  — debounced mirror of the local watchlist */
(() => {
  if (IS_NATIVE) return;
  const API_BASE = 'https://yardscout-api.yardscout.workers.dev';
  const ENABLED_KEY = 'ys_email_alerts_on';   // last known server state (UI cache)
  const $id = (x) => document.getElementById(x);

  const entToken = () =>
    localStorage.getItem('jh_pro_source') === 'account'
      ? localStorage.getItem('ys_ent_token') : null;

  function serverWatches() {
    // Local entries use yrMin/yrMax; the API takes yearMin/yearMax (same
    // sanitizer as native device registration). matchOnly is a local-display
    // filter with no server meaning — dropped deliberately.
    return loadWatchlist().map((e) => ({
      make: e.make || null, model: e.model || null,
      yearMin: e.yrMin || null, yearMax: e.yrMax || null,
      lat: e.lat != null ? e.lat : null, lng: e.lng != null ? e.lng : null,
      radiusMi: e.radiusMi || null,
    }));
  }

  async function postSync(enabled) {
    const token = entToken();
    if (!token) return null;
    const r = await fetch(API_BASE + '/v1/email-alerts/sync', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ token, watches: serverWatches(), enabled }),
    });
    const data = await r.json().catch(() => ({}));
    return { ok: r.ok, status: r.status, data };
  }

  /* Watchlist changed: if alerts are on, mirror silently (debounced — adding
   * several models in one tap burst is one request). */
  let syncTimer = null;
  window.syncEmailAlertWatches = () => {
    if (!entToken() || localStorage.getItem(ENABLED_KEY) !== '1') return;
    clearTimeout(syncTimer);
    syncTimer = setTimeout(() => {
      postSync(true).catch(() => { /* offline — next change or toggle retries */ });
    }, 1500);
  };

  function setStatus(msg, isError) {
    const el = $id('email-alerts-status');
    if (!el) return;
    el.textContent = msg || '';
    el.style.color = isError ? 'var(--red)' : '';
  }

  window.refreshEmailAlertsUi = function refreshEmailAlertsUi() {
    const panel = $id('email-alerts-panel');
    if (!panel) return;
    panel.style.display = '';   // web always sees the panel (perk visibility)
    const toggleWrap = $id('email-alerts-toggle-wrap');
    const upgradeBtn = $id('email-alerts-upgrade');
    const linkWrap = $id('email-alerts-link');
    const token = entToken();

    if (!token) {
      toggleWrap.style.display = 'none';
      if (isPro()) {
        // Pro on this browser but no entitlement token (account-session Pro,
        // or Pro granted before email linking existed): the upgrade sheet
        // would only say "You're Pro ✓", so link the email right here.
        upgradeBtn.style.display = 'none';
        linkWrap.style.display = '';
      } else {
        // Free: honest Pro-perk pitch.
        upgradeBtn.style.display = '';
        linkWrap.style.display = 'none';
      }
      setStatus('');
      return;
    }
    upgradeBtn.style.display = 'none';
    linkWrap.style.display = 'none';
    toggleWrap.style.display = 'flex';
    const toggle = $id('email-alerts-toggle');
    toggle.checked = localStorage.getItem(ENABLED_KEY) === '1';
    const email = localStorage.getItem('ys_ent_email');
    setStatus(toggle.checked && email ? 'Alert emails go to ' + email + '.' : '');

    // Confirm against the server once per render of the Alerts tab (cheap,
    // and catches "unsubscribed from the email link" done elsewhere).
    fetch(API_BASE + '/v1/email-alerts/status?token=' + encodeURIComponent(token))
      .then((r) => r.ok ? r.json() : null)
      .then((data) => {
        if (!data) return;
        localStorage.setItem(ENABLED_KEY, data.enabled ? '1' : '0');
        toggle.checked = !!data.enabled;
        if (data.enabled) {
          setStatus('Alert emails go to ' + (data.email || email) + '. One email per scan with new matches — scans run about every 4 hours.');
        }
      })
      .catch(() => { /* offline — cached state stands */ });
  };

  const toggleEl = $id('email-alerts-toggle');
  if (toggleEl) toggleEl.addEventListener('change', async () => {
    const on = toggleEl.checked;
    toggleEl.disabled = true;
    setStatus(on ? 'Turning on…' : 'Turning off…');
    try {
      const res = await postSync(on);
      if (res && res.ok) {
        localStorage.setItem(ENABLED_KEY, on ? '1' : '0');
        track(on ? 'email-alerts-on' : 'email-alerts-off');
        setStatus(on
          ? 'On — alert emails go to ' + (res.data.email || localStorage.getItem('ys_ent_email') || 'your Pro email')
            + '. You get one email per scan that finds new matches (scans run about every 4 hours).'
          : 'Email alerts are off. Your watchlist still works right here.');
      } else {
        toggleEl.checked = !on;
        setStatus(res && res.status === 403
          ? 'Your Pro has lapsed — renew to use email alerts.'
          : 'Could not update email alerts — try again.', true);
      }
    } catch (e) {
      toggleEl.checked = !on;
      setStatus('Could not reach the server — check your connection.', true);
    } finally {
      toggleEl.disabled = false;
    }
  });

  /* ---- inline email-link flow (Pro without an entitlement token) ----
   * Same account-less request-code / redeem-code endpoints as the Pro
   * sheet's "Already have Pro?" — but that section is unreachable for a
   * user the sheet already considers Pro, so it lives here too. */
  const ENT_LINK_BASE = localStorage.getItem('ys_ent_base')
    || (location.hostname === 'yardscout.io' ? '' : 'https://yardscout.io');
  // No content-type header on purpose: keeps the request CORS-"simple"
  // (no preflight), matching every other entitlement call in this file.
  const entPost = async (path, body) => {
    const r = await fetch(ENT_LINK_BASE + '/api/ent/' + path, { method: 'POST', body: JSON.stringify(body) });
    return { ok: r.ok, data: await r.json().catch(() => ({})) };
  };
  const setLinkStatus = (msg, isError) => {
    const el = $id('email-alerts-link-status');
    if (!el) return;
    el.textContent = msg || '';
    el.style.color = isError ? 'var(--red)' : '';
  };

  const linkSendBtn = $id('email-alerts-link-send');
  if (linkSendBtn) linkSendBtn.addEventListener('click', async () => {
    const email = ($id('email-alerts-link-email').value || '').trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setLinkStatus('Enter a valid email address.', true);
      return;
    }
    track('email-alerts-link-request');
    linkSendBtn.disabled = true;
    setLinkStatus('Sending\u2026');
    try {
      const { ok, data } = await entPost('request-code', { email });
      if (ok) {
        $id('email-alerts-link-code-row').style.display = '';
        $id('email-alerts-link-code').focus();
        setLinkStatus(data.message || 'Check your email for the 6-digit code (expires in 10 minutes).');
      } else {
        setLinkStatus(data.message || 'Could not send the code — try again.', true);
      }
    } catch (e) {
      setLinkStatus('Could not reach the server — check your connection.', true);
    } finally {
      linkSendBtn.disabled = false;
    }
  });

  const linkBtn = $id('email-alerts-link-btn');
  if (linkBtn) linkBtn.addEventListener('click', async () => {
    const email = ($id('email-alerts-link-email').value || '').trim();
    const code = ($id('email-alerts-link-code').value || '').trim();
    if (!/^\d{6}$/.test(code)) { setLinkStatus('Enter the 6-digit code from the email.', true); return; }
    linkBtn.disabled = true;
    setLinkStatus('Checking\u2026');
    try {
      const { ok, data } = await entPost('redeem-code', { email, code });
      if (ok && data.pro) {
        // Same grant path as the Pro sheet — sets ys_ent_token/email/src.
        if (window.ysGrantWebPro) window.ysGrantWebPro({ email, token: data.token, source: data.source });
        track('email-alerts-linked');
        // The user linked from the EMAIL ALERTS panel — their intent is to
        // turn alerts on, so do that now rather than making them find a toggle.
        const res = await postSync(true);
        if (res && res.ok) localStorage.setItem(ENABLED_KEY, '1');
        window.refreshEmailAlertsUi();
        setStatus('Linked — alert emails go to ' + email + '. One email per scan with new matches (scans run about every 4 hours).');
      } else {
        setLinkStatus(data.message || 'That code didn\u2019t work — request a new one.', true);
      }
    } catch (e) {
      setLinkStatus('Could not reach the server — check your connection.', true);
    } finally {
      linkBtn.disabled = false;
    }
  });
  const linkCodeInput = $id('email-alerts-link-code');
  if (linkCodeInput) linkCodeInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') linkBtn.click(); });
  const linkEmailInput = $id('email-alerts-link-email');
  if (linkEmailInput) linkEmailInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') linkSendBtn.click(); });

  // Initial paint (the Alerts tab may be the landing tab via deep link).
  window.refreshEmailAlertsUi();
})();
