/* Per-account alerts: server-side watches + dispatch on inventory commit.
 *
 * Flow: the scan's push_inventory.py includes recent arrivals in the commit
 * body → dispatchAlerts() matches them against every Pro user's watches →
 * one digest Web Push per device (and an email fallback for users with no
 * push subscription). alerts_sent dedupes so overlapping scans never
 * re-alert the same (user, vehicle) pair.
 *
 * Sends run in ctx.waitUntil after the commit response, capped to stay inside
 * the Workers free-plan subrequest budget (50/request). With more users than
 * the cap, upgrade the Worker to paid ($5/mo → 1000 subrequests).
 */

import { json, err, isoNow, haversineMiles } from './util.js';
import { getSessionUser, resolveTier } from './auth.js';
import { sendWebPush, pushConfigured } from './push.js';

const MAX_WATCHES_PER_USER = 20;
const MAX_WATCHES_FREE = 5;
const MAX_VEHICLES_PER_DIGEST = 6;   // keep the notification readable
const MAX_SENDS_PER_COMMIT = 35;     // subrequest budget (free plan: 50/req)
const MAX_WEEKLY_EMAILS = 40;        // cron invocations get their own budget
const ARRIVALS_RETENTION_DAYS = 10;

/* ===== watches CRUD (session + Pro) ===== */

export async function handleWatchesList(req, env) {
  const user = await getSessionUser(req, env);
  if (!user) return err(401, 'auth_required', 'Sign in first.');
  const rows = (await env.DB.prepare(
    'SELECT id, make, model, year_min, year_max, lat, lng, radius_mi, drive_filter, trim_filter, created_at FROM watches WHERE user_id = ?1 ORDER BY created_at DESC'
  ).bind(user.id).all()).results || [];
  return json({ watches: rows, tier: resolveTier(user) });
}

export async function handleWatchCreate(req, env) {
  const user = await getSessionUser(req, env);
  if (!user) return err(401, 'auth_required', 'Sign in first.');
  const tier = resolveTier(user);
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }

  const make = String(body.make || '').trim().slice(0, 40) || null;
  const model = String(body.model || '').trim().slice(0, 60) || null;
  if (!make && !model) return err(400, 'bad_watch', 'A watch needs at least a make or a model.');
  const yearMin = Number.isFinite(+body.yearMin) && +body.yearMin > 1900 ? Math.floor(+body.yearMin) : null;
  const yearMax = Number.isFinite(+body.yearMax) && +body.yearMax > 1900 ? Math.floor(+body.yearMax) : null;
  const lat = Number.isFinite(+body.lat) ? +body.lat : null;
  const lng = Number.isFinite(+body.lng) ? +body.lng : null;
  let radiusMi = Number.isFinite(+body.radiusMi) && +body.radiusMi > 0
    ? Math.min(Math.floor(+body.radiusMi), 3000) : null;

  // Free watches feed the weekly digest email; instant push stays Pro (the
  // subscribe + dispatch paths check tier). Free watches must be
  // radius-scoped — "anywhere" is the Pro tier of alerts — and free radius
  // caps at 250 mi, mirroring the app's search radius.
  if (tier !== 'pro') {
    if (!radiusMi || lat == null || lng == null) {
      return err(403, 'pro_required', 'Nationwide watches are a Pro feature — free watches need a home ZIP and radius.');
    }
    radiusMi = Math.min(radiusMi, 250);
  }

  // Trim / drivetrain filters are Pro (free watches stay make/model/years).
  // Old clients never send them; an empty string means "any".
  const { driveFilter, trimFilter } = sanitizeVpicFilters(body);
  if (tier !== 'pro' && (driveFilter || trimFilter)) {
    return err(403, 'pro_required', 'Trim and drivetrain filters are a Pro feature.');
  }

  const maxWatches = tier === 'pro' ? MAX_WATCHES_PER_USER : MAX_WATCHES_FREE;
  const n = await env.DB.prepare('SELECT COUNT(*) AS n FROM watches WHERE user_id = ?1')
    .bind(user.id).first();
  if ((n?.n || 0) >= maxWatches) {
    return err(400, 'too_many', tier === 'pro'
      ? `Max ${MAX_WATCHES_PER_USER} watches — remove one first.`
      : `Free accounts get ${MAX_WATCHES_FREE} watches — remove one first, or Pro raises the cap to ${MAX_WATCHES_PER_USER}.`);
  }

  const id = crypto.randomUUID();
  await env.DB.prepare(
    `INSERT INTO watches (id, user_id, make, model, year_min, year_max, lat, lng, radius_mi, drive_filter, trim_filter, created_at)
     VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12)`
  ).bind(id, user.id, make, model, yearMin, yearMax,
         (lat != null && lng != null) ? lat : null,
         (lat != null && lng != null) ? lng : null,
         radiusMi, driveFilter || null, trimFilter || null, isoNow()).run();

  // Watches alert on FUTURE arrivals only: seed the sent-log with every
  // current match in the arrivals window (a 10-day superset of the 3-day
  // dispatch window) so the next commit/digest doesn't "alert" the user
  // about cars that were already on the lot when they created the watch.
  const w = {
    make, model, year_min: yearMin, year_max: yearMax,
    lat: (lat != null && lng != null) ? lat : null,
    lng: (lat != null && lng != null) ? lng : null,
    radius_mi: radiusMi,
    drive_filter: driveFilter || null, trim_filter: trimFilter || null,
  };
  const existing = await loadArrivals(env);
  const seedStmt = env.DB.prepare(
    'INSERT OR IGNORE INTO alerts_sent (user_id, vehicle_id, sent_at) VALUES (?1, ?2, ?3)'
  );
  const now = isoNow();
  const seeds = existing.filter((v) => watchMatches(w, v))
    .map((v) => seedStmt.bind(user.id, String(v.id), now));
  for (let i = 0; i < seeds.length; i += 80) {
    await env.DB.batch(seeds.slice(i, i + 80));
  }

  return json({ ok: true, id, seeded: seeds.length });
}

export async function handleWatchDelete(req, env, watchId) {
  const user = await getSessionUser(req, env);
  if (!user) return err(401, 'auth_required', 'Sign in first.');
  await env.DB.prepare('DELETE FROM watches WHERE id = ?1 AND user_id = ?2')
    .bind(watchId, user.id).run();
  return json({ ok: true });
}

/* ===== push subscriptions ===== */

export function handleVapidKey(env) {
  if (!pushConfigured(env)) return err(503, 'push_off', 'Push is not configured yet.');
  return json({ publicKey: env.VAPID_PUBLIC_KEY });
}

export async function handlePushSubscribe(req, env) {
  const user = await getSessionUser(req, env);
  if (!user) return err(401, 'auth_required', 'Sign in first.');
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  const sub = body.subscription || body;
  const endpoint = String(sub.endpoint || '');
  const p256dh = sub.keys && String(sub.keys.p256dh || '');
  const auth = sub.keys && String(sub.keys.auth || '');
  // Real push services are always https; localhost is allowed only in dev so
  // the e2e test can stand in as the push service.
  const okEndpoint = endpoint.startsWith('https://')
    || (env.DEV_MODE === '1' && /^http:\/\/(127\.0\.0\.1|localhost):/.test(endpoint));
  if (!okEndpoint || !p256dh || !auth) {
    return err(400, 'bad_subscription', 'Missing endpoint or keys.');
  }
  await env.DB.prepare(
    `INSERT INTO push_subscriptions (endpoint, user_id, p256dh, auth, created_at)
     VALUES (?1, ?2, ?3, ?4, ?5)
     ON CONFLICT (endpoint) DO UPDATE SET user_id = ?2, p256dh = ?3, auth = ?4`
  ).bind(endpoint, user.id, p256dh, auth, isoNow()).run();
  return json({ ok: true });
}

export async function handlePushUnsubscribe(req, env) {
  const user = await getSessionUser(req, env);
  if (!user) return err(401, 'auth_required', 'Sign in first.');
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  await env.DB.prepare('DELETE FROM push_subscriptions WHERE endpoint = ?1 AND user_id = ?2')
    .bind(String(body.endpoint || ''), user.id).run();
  return json({ ok: true });
}

/** Self-test: sends a push to every device the signed-in user registered. */
export async function handlePushTest(req, env) {
  const user = await getSessionUser(req, env);
  if (!user) return err(401, 'auth_required', 'Sign in first.');
  if (!pushConfigured(env)) return err(503, 'push_off', 'Push is not configured yet.');
  const subs = (await env.DB.prepare(
    'SELECT endpoint, p256dh, auth FROM push_subscriptions WHERE user_id = ?1 LIMIT 5'
  ).bind(user.id).all()).results || [];
  if (!subs.length) return err(404, 'no_subscriptions', 'No devices registered for push on this account.');
  let sent = 0;
  for (const sub of subs) {
    const res = await sendWebPush(env, sub, {
      title: 'YardScout test',
      body: 'Push alerts are working on this device.',
      url: '/',
    });
    if (res.gone) {
      await env.DB.prepare('DELETE FROM push_subscriptions WHERE endpoint = ?1').bind(sub.endpoint).run();
    } else if (res.ok) sent++;
  }
  return json({ ok: true, sent, devices: subs.length });
}

/* ===== dispatch on inventory commit ===== */

/* Make aliases — mirror of the scraper's _MAKE_ALIASES (2026-10 make-name
 * merge: MINI Cooper->MINI, Vw->Volkswagen, ...). Arrivals now carry
 * canonical makes, but watches saved BEFORE the merge still hold the old
 * spellings in D1 — canonicalize both sides at comparison time instead of
 * migrating stored rows. Keys are squashed lowercase alphanumerics. */
const MAKE_ALIASES = {
  minicooper: 'mini',
  alfaromeo: 'alfa romeo',
  fiatlancia: 'fiat',
  mercedes: 'mercedes-benz',
  mercedesbenz: 'mercedes-benz',
  vw: 'volkswagen',
  volkswagon: 'volkswagen',
  chevy: 'chevrolet',
  chev: 'chevrolet',
  rover: 'land rover',
  landrover: 'land rover',
  rangerover: 'land rover',
  infinity: 'infiniti',
};

function canonMakeLow(s) {
  const low = String(s || '').toLowerCase();
  return MAKE_ALIASES[low.replace(/[^a-z0-9]/g, '')] || low;
}

/* 2026-10 model merge — lowercase mirror of the scraper's normalize_model
 * output for every pre-merge spelling whose canonical form differs beyond
 * case. Watches saved before the merge (D1 rows are untouched by design)
 * canonicalize at comparison time, like MAKE_ALIASES above. Keep in sync
 * with scraper/test_model_normalization.py. */
const MODEL_RENAMES = {
  "alfaromeo": {
    "alfaromeogtv6": "gtv-6",
  },
  "audi": {
    "audi4000": "4000", "audia3": "a3", "audia4": "a4", "audia5": "a5", "audia6": "a6",
    "audia8": "a8", "audiallroad": "allroad", "audicabriolet": "cabriolet", "audiq3": "q3",
    "audiq5": "q5", "audiq7": "q7", "audis3": "s3", "audis5": "s5", "auditt": "tt",
  },
  "bmw": {
    "525ia": "525i", "530ia": "530i", "bmw128i": "128i", "bmw318i": "318i", "bmw320i": "320i",
    "bmw323i": "323i", "bmw325i": "325i", "bmw328i": "328i", "bmw330i": "330i",
    "bmw335i": "335i", "bmw430i": "430i", "bmw525i": "525i", "bmw528e": "528e",
    "bmw528i": "528i", "bmw530i": "530i", "bmw535i": "535i", "bmw540i": "540i",
    "bmw550i": "550i", "bmw550igt": "550i gt", "bmw645i": "645i", "bmw650i": "650i",
    "bmw735i": "735i", "bmw740i": "740i", "bmw745i": "745i", "bmw750i": "750i",
    "bmwalpinab7": "alpina b7", "bmwi3": "i3", "bmwx1": "x1", "bmwx3": "x3", "bmwx5": "x5",
    "bmwz3": "z3", "bmwz4": "z4",
  },
  "buick": {
    "rendezvoussrv": "rendezvous",
  },
  "cadillac": {
    "eldorado": "eldorado",
  },
  "chevrolet": {
    "astrovan": "astro", "belair": "bel air", "blazers10jimmys15": "blazer s10/jimmy s15",
    "c10": "c10", "c10pickup": "c10", "c20truck": "c20", "c30pickup": "c30",
    "chevrolet10pickup": "10 pickup", "chevrolet10van": "10 van",
    "chevrolet1500pickup": "1500 pickup", "chevrolet20pickup": "20 pickup",
    "chevrolet20van": "20 van", "chevrolet2500pickup": "2500 pickup", "chevrolet30van": "30 van",
    "chevrolet3500pickup": "3500 pickup", "chevyvanclassic": "chevy van",
    "cityexpressls": "city express", "ck10series": "c/k 10", "ck1500series": "c/k 1500",
    "ck20series": "c/k 20", "ck2500series": "c/k 2500", "ck30series": "c/k 30",
    "ck3500series": "c/k 3500", "express1500van": "express 1500",
    "express2500van": "express 2500", "express3500van": "express 3500", "geoprizm": "prizm",
    "gseriesvan": "g-series", "luminacar": "lumina", "luminaminivan": "lumina apv",
    "luminavan": "lumina apv", "pu": "p.u", "rv20series": "r/v 20", "s10pickup": "s-10",
    "s10pu": "s-10", "s10s15sonoma": "s10/s15/sonoma", "silverado1500hd": "silverado 1500hd",
    "silverado1500pickup": "silverado 1500", "silverado2500pickup": "silverado 2500",
    "silverado3500pickup": "silverado 3500", "silveradoclassic1500": "silverado 1500 classic",
    "silveradohd2500": "silverado 2500hd", "ventureapv": "venture",
  },
  "chrysler": {
    "200js": "200", "200lx": "200", "200uf": "200", "300clx": "300c", "300lx": "300",
    "300m": "300m", "aspenhg": "aspen", "concordelh": "concorde", "crossfirezh": "crossfire",
    "lhslh": "lhs", "pacificacs": "pacifica", "ptcruiserpt": "pt cruiser",
    "sebringjr": "sebring", "sebringjs": "sebring", "tcmaserati": "tc by maserati",
    "townampcountry": "town & country", "townandcountry": "town & country",
    "townandcountryrs": "town & country", "townandcountryrt": "town & country",
    "voyagerrs": "voyager",
  },
  "dodge": {
    "200pu": "200 p.u", "avengerjs": "avenger", "caliberpm": "caliber",
    "caravangrandcaravanrs": "caravan/grand caravan", "caravanrs": "caravan",
    "challengerla": "challenger", "challengerlc": "challenger", "chargerlc": "charger",
    "chargerlx": "charger", "d100pickup": "d100", "d10pu": "d-10 p.u", "d150pickup": "d150",
    "dakotaan": "dakota", "dakotand": "dakota", "dartpf": "dart",
    "dodge1500pickup": "1500 pickup", "dodge1500van": "1500 van", "dodge150pickup": "150 pickup",
    "dodge2500pickup": "2500 pickup", "dodge2500van": "2500 van",
    "dodge3500pickup": "3500 pickup", "dodge3500van": "3500 van", "dodge600": "600",
    "durangodn": "durango", "durangohb": "durango", "grandcaravan": "grand caravan",
    "grandcaravanrs": "grand caravan", "grandcaravanrt": "grand caravan",
    "intrepidlh": "intrepid", "journeyjc": "journey", "magnumlx": "magnum", "neonpl": "neon",
    "nitroka": "nitro", "pud250": "d250", "ram1500van": "ram van 1500",
    "ram2500van": "ram van 2500", "ram3500van": "ram van 3500", "stratusja": "stratus",
    "stratusjr": "stratus", "w100pickup": "w100", "w150pickup": "w150", "w200pickup": "w200",
    "w250pickup": "w250", "w350pickup": "w350",
  },
  "fiat": {
    "fiat500": "500", "fiatfiat500": "500",
  },
  "ford": {
    "e100econoline": "e-100", "e150clubwagon": "e-150", "e150econoline": "e-150",
    "e150econolineclubwagon": "e-150", "e150van": "e-150", "e250econoline": "e-250",
    "e250van": "e-250", "e300econoline": "e-300", "e350clubwagon": "e-350",
    "e350econoline": "e-350", "e350econolineclubwagon": "e-350", "e350van": "e-350",
    "e350wagon": "e-350", "e450sdvan": "e-450 super duty", "ecosportse": "ecosport",
    "ecosportses": "ecosport", "escapelimited": "escape", "escapexls": "escape",
    "escapexlt": "escape", "f100pickup": "f-100", "f100truck": "f-100", "f150pickup": "f-150",
    "f250pickup": "f-250", "f250sd": "f-250 super duty", "f250sdpickup": "f-250 super duty",
    "f350pickup": "f-350", "f350sd": "f-350 super duty", "f350sdpickup": "f-350 super duty",
    "f450sd": "f-450 super duty", "f450sdpickup": "f-450 super duty", "forde150van": "e-150",
    "forde250van": "e-250", "forde350van": "e-350", "forde450sdvan": "e-450 super duty",
    "fordf150pickup": "f-150", "fordf250pickup": "f-250", "fordf250sdpickup": "f-250 super duty",
    "fordf350pickup": "f-350", "fordf350sdpickup": "f-350 super duty",
    "fordf450sdpickup": "f-450 super duty", "fordf550sdpickup": "f-550 super duty",
    "fordpass": "pass", "transit150": "transit-150", "transit250": "transit-250",
    "transit350": "transit-350",
  },
  "gmc": {
    "c15c1500pickup": "c1500", "ck1500series": "c/k 1500", "ck2500series": "c/k 2500",
    "gmc1500pickup": "1500 pickup", "gmc1500van": "1500 van", "gmc2500pickup": "2500 pickup",
    "gmc2500van": "2500 van", "gmc3500pickup": "3500 pickup", "gmcenvoy": "envoy",
    "gmcenvoyxl": "envoy xl", "gmcs10s15sonoma": "s10/s15/sonoma", "gmcsafarigmc": "safari",
    "gmcsierra1500pickup": "sierra 1500", "gmcsierradenaliev": "sierra denali ev",
    "gmcterrain": "terrain", "gmcyukon": "yukon", "gmcyukonxl1500": "yukon xl 1500",
    "jimmys15": "s-15 jimmy", "jimmyutility": "jimmy", "s15pickup": "s-15",
    "s15utility": "s-15 jimmy", "safarigmc": "safari", "savana1500van": "savana 1500",
    "savana2500van": "savana 2500", "savana3500van": "savana 3500",
    "sierra1500pickup": "sierra 1500", "sierra2500pickup": "sierra 2500",
    "sierrack1500": "sierra 1500", "sierrack2500": "sierra 2500", "sierrack3500": "sierra 3500",
  },
  "honda": {
    "civiccrx": "crx",
  },
  "hummer": {
    "hummerh3": "h3",
  },
  "infiniti": {
    "infinitiex35": "ex35", "infinitiex37": "ex37", "infinitifxseries": "fx series",
    "infinitig20": "g20", "infinitig25": "g25", "infinitig35": "g35", "infinitig37": "g37",
    "infinitii30": "i30", "infinitii35": "i35", "infinitij30": "j30", "infinitijx35": "jx35",
    "infinitim35": "m35", "infinitim37": "m37", "infinitiq45": "q45", "infinitiq50": "q50",
    "infinitiq60": "q60", "infinitiq70": "q70", "infinitiqx30": "qx30", "infinitiqx4": "qx4",
    "infinitiqx50": "qx50", "infinitiqx56": "qx56", "infinitiqx60": "qx60",
    "infinitiqx80": "qx80", "qx41999": "qx4",
  },
  "isuzu": {
    "isuzuascender": "ascender", "isuzui280": "i-280", "isuzupuppickup": "pup (pickup)",
    "isuzurodeo": "rodeo", "isuzutrooper": "trooper",
  },
  "jaguar": {
    "xj6": "xj6", "xjsedan": "xj",
  },
  "jeep": {
    "cherokeekl": "cherokee", "cherokeexj": "cherokee", "cj7": "cj7", "commanderxh": "commander",
    "commanderxk": "commander", "compassmk": "compass", "grandcherokeewj": "grand cherokee",
    "grandcherokeewk": "grand cherokee", "j10pickup": "j10", "libertykj": "liberty",
    "libertykk": "liberty", "patriotmk": "patriot", "pucomanche": "comanche",
    "wranglerjk": "wrangler",
  },
  "kia": {
    "forte5door": "forte5", "rio5door": "rio5", "riocinco": "rio5",
  },
  "landrover": {
    "discoveryii": "discovery series ii", "evoque": "range rover evoque",
    "landroverdiscovery": "discovery", "landroverevoque": "range rover evoque",
    "landroverlr2": "lr2", "landroverrangerover": "range rover",
    "landroverrangesport": "range rover sport",
  },
  "lexus": {
    "es300h": "es 300h", "is200t": "is 200t", "lexusct200h": "ct 200h", "lexuses300": "es 300",
    "lexuses330": "es 330", "lexuses350": "es 350", "lexusgs300": "gs 300",
    "lexusgs350": "gs 350", "lexusgs400": "gs 400", "lexusgs430": "gs 430",
    "lexusgs450h": "gs 450h", "lexusgs460": "gs 460", "lexusis250": "is 250",
    "lexusis300": "is 300", "lexusis350": "is 350", "lexusls400": "ls 400",
    "lexusls430": "ls 430", "lexusls460": "ls 460", "lexusls600hl": "ls 600h l",
    "lexusrx300": "rx 300", "lexusrx330": "rx 330", "lexusrx350": "rx 350",
    "lexusrx400h": "rx 400h", "lexusscseries": "sc series", "rx450h": "rx 450h",
    "ux250h": "ux 250h",
  },
  "lincoln": {
    "lincolnls": "ls",
  },
  "mazda": {
    "2": "mazda2", "3": "mazda3", "5": "mazda5", "6": "mazda6", "b2000": "b2000",
    "b2200": "b2200", "b2300": "b2300", "mazda2": "mazda2", "mazda3": "mazda3",
    "mazda5": "mazda5", "mazda6": "mazda6", "mazda626": "626", "mazdab2200": "b2200",
    "mazdab2300": "b2300", "mazdab2600": "b2600", "mazdab3000": "b3000", "mazdab4000": "b4000",
    "mazdacx30": "cx-30", "mazdacx5": "cx-5", "mazdacx7": "cx-7", "mazdacx9": "cx-9",
    "mazdamillenia": "millenia", "mazdampv": "mpv", "mazdamx5miata": "mx-5 miata",
    "mazdamx6": "mx-6", "mazdaprotege": "protege", "mazdarx8": "rx-8", "mazdatribute": "tribute",
    "miata": "mx-5 miata", "mx5": "mx-5 miata", "rx8": "rx-8", "tributedx": "tribute",
    "tributees": "tribute", "tributelx": "tribute",
  },
  "mercedesbenz": {
    "mercedes190": "190", "mercedes2304": "230-4", "mercedes280": "280", "mercedes300d": "300d",
    "mercedes300e": "300e", "mercedes380": "380", "mercedes560": "560",
    "mercedescclass": "c-class", "mercedesclaclass": "cla-class", "mercedesclclass": "cl-class",
    "mercedesclk": "clk", "mercedesclsclass": "cls-class", "mercedeseclass": "e-class",
    "mercedesglaclass": "gla-class", "mercedesglclass": "gl-class",
    "mercedesglkclass": "glk-class", "mercedesmlclass": "m-class", "mercedesrclass": "r-class",
    "mercedessclass": "s-class", "mercedesslk": "slk", "mercedessprinter2500": "sprinter 2500",
    "mercedessprinter3500": "sprinter 3500", "mlclass": "m-class", "smartsmart": "smart",
  },
  "mini": {
    "cooperclubman": "clubman", "cooperconvertible": "convertible",
    "coopercountryman": "countryman", "cooperhardtop": "hardtop", "cooperpaceman": "paceman",
    "miniclubman": "clubman", "minicooper": "cooper", "minicountryman": "countryman",
    "miniminicooper": "cooper",
  },
  "mitsubishi": {
    "mitsubishipickup": "pickup", "mitsubishiraider": "raider", "raidernm": "raider",
  },
  "nissan": {
    "nissanpickup": "pickup", "nv1500": "nv1500", "nv2500hd": "nv2500 hd", "nv3500": "nv3500",
    "pathfinder19995": "pathfinder", "pu": "p.u",
  },
  "oldsmobile": {
    "ciera": "cutlass ciera", "culassciera": "cutlass ciera",
    "deltaeightyeightroyale": "delta 88", "eightyeight88": "eighty-eight",
    "eightyeightroyale": "eighty-eight", "intriguegls": "intrigue", "intriguegx": "intrigue",
    "ninetyeight98": "ninety-eight", "oldsmobilebravada": "bravada",
    "silhouetteapv": "silhouette",
  },
  "pontiac": {
    "azteksrv": "aztek", "bonnevillegxp": "bonneville", "bonnevillese": "bonneville",
    "g3wave": "g3", "grandamgt": "grand am", "grandamgt1": "grand am", "grandamse": "grand am",
    "grandamse1": "grand am", "grandprixgt": "grand prix", "grandprixgt2": "grand prix",
    "grandprixgtp": "grand prix", "grandprixse": "grand prix", "grandprixse1": "grand prix",
    "pontiacfirebird": "firebird", "pontiacg6": "g6", "pontiacgrandam": "grand am",
    "pontiacgrandprix": "grand prix", "pontiacmontana": "montana", "pontiactorrent": "torrent",
    "sunfirese": "sunfire",
  },
  "porsche": {
    "porsche944": "944", "porscheboxster": "boxster", "porschecayenne": "cayenne",
  },
  "ram": {
    "dodge1500pickup": "1500", "dodge2500pickup": "2500", "promaster1500van": "promaster 1500",
    "promaster2500van": "promaster 2500", "promaster3500van": "promaster 3500",
  },
  "saab": {
    "saab93": "9-3", "saab95": "9-5", "saab97x": "9-7x",
  },
  "saturn": {
    "astraxe": "astra", "auragreenlinehybrid": "aura green line", "auraxe": "aura",
    "auraxr": "aura", "l300sedan": "l300", "saturnaura": "aura", "saturnion": "ion",
    "saturnlseries": "l-series", "saturnsseries": "s-series", "saturnvue": "vue", "sl1": "sl1",
    "vuegreenlinehybrid": "vue green line",
  },
  "scion": {
    "scionia": "ia", "sciontc": "tc", "scionxa": "xa", "scionxb": "xb", "scionxd": "xd",
    "toyotascionxa": "xa", "toyotatc": "tc", "toyotaxb": "xb", "toyotaxd": "xd",
  },
  "suzuki": {
    "grandvitaraxl7": "xl-7", "sx4sedan": "sx4 sport",
  },
  "toyota": {
    "corollamatrix": "matrix", "pickup": "pickup", "pickupdlx": "pickup", "pickupstd": "pickup",
    "solara": "camry solara", "toyotapickup": "pickup", "vanwagon": "van",
  },
  "volkswagen": {
    "cabrioletconvertible": "cabriolet", "gli": "jetta gli", "golfgti": "gti",
  },
  "volvo": {
    "240series": "240", "240series240": "240", "740series": "740", "760series": "760",
    "850series": "850", "850series850": "850", "940series": "940", "940series940": "940",
    "960series": "960", "volvo120series": "120 series", "volvo240series": "240",
    "volvo30series": "30 series", "volvo40series": "40 series", "volvo50series": "50 series",
    "volvo60series": "60 series", "volvo70series": "70 series", "volvo740": "740",
    "volvo80series": "80 series", "volvos60": "s60", "volvoxc60": "xc60", "volvoxc90": "xc90",
  },
};

function canonModelLow(make, model) {
  const mk = canonMakeLow(make).replace(/[^a-z0-9]/g, '');
  const low = String(model || '').toLowerCase();
  const ren = MODEL_RENAMES[mk];
  return (ren && ren[low.replace(/[^a-z0-9]/g, '')]) || low;
}

/* ===== trim / drivetrain filters (Pro) =====
 * Shared by every sync path (account watches, native devices, email
 * watchers). Returns {driveFilter: '4x4'|'2wd'|'', trimFilter: string}.
 * Both optional; old clients never send them. */
export function sanitizeVpicFilters(w) {
  const d = String(w?.driveFilter || '').toLowerCase();
  const driveFilter = d === '4x4' || d === '2wd' ? d : '';
  const trimFilter = String(w?.trimFilter || '').trim().slice(0, 40);
  return { driveFilter, trimFilter };
}

/** The one matching rule for VIN-decode filters — mirrored verbatim by
 * watchlistMatches() in docs/app.js. vpic = [trim, trimQuality, series,
 * driveType] (the per-vehicle decode the shards carry).
 *   drive '4x4' → driveType names 4WD or AWD; '2wd' → FWD, RWD or 4x2.
 *     No decoded drive type → no match ("only cars whose VIN decode
 *     confirms it").
 *   trim → case-insensitive substring of trim OR series, only when the
 *     decode's trimQuality is 'usable'. No usable decode → no match.
 * TODO(manual-transmission): "manual confirmed" lives in
 * docs/data/vehicle_extras.json, not in the shards — not filterable here yet. */
/* Trim watch matching, shared by the Worker (alerts.js) and the web shell
 * (app.js) — keep the two copies identical.
 *
 * The decoder (NHTSA vPIC) names trims in its own words, not the badge's:
 * "Grade: SR5 V6", "Luxury" for a Toyota Limited, "Base/LS", "1LT". A
 * plain substring test also over-matches ("LT" hits "LTZ", "SE" hits
 * "SEL"). So: both sides are split into lowercase tokens, a leading
 * digit is split off a token ("1LT" -> "1","lt"), and the query's tokens
 * must appear contiguously in trim+series. Then a small, make-scoped
 * alias table lets the words a shopper would type ("Limited", "base")
 * find the decoder's label. */
const TRIM_ALIASES = [
  // make (lowercase, or '*' for any) + a set of interchangeable words
  { make: 'toyota', words: ['limited', 'luxury'] },
  { make: 'lexus', words: ['limited', 'luxury'] },
  { make: '*', words: ['base', 'std', 'standard'] },
  { make: '*', words: ['grand touring', 'gt'] },
];
function trimTokens(s) {
  const out = [];
  for (const raw of String(s || '').toLowerCase().replace(/grade:/g, ' ').split(/[^a-z0-9]+/)) {
    if (!raw) continue;
    const m = raw.match(/^(\d)([a-z]{2,})$/); // "1lt" -> "1","lt"
    if (m) { out.push(m[1]); out.push(m[2]); } else out.push(raw);
  }
  return out;
}
function tokensContain(hay, needle) {
  if (!needle.length) return false;
  outer: for (let i = 0; i + needle.length <= hay.length; i++) {
    for (let j = 0; j < needle.length; j++) if (hay[i + j] !== needle[j]) continue outer;
    return true;
  }
  return false;
}
function trimQueryVariants(query, make) {
  const q = String(query || '').trim().toLowerCase();
  const mk = String(make || '').trim().toLowerCase();
  const variants = new Set([q]);
  for (const a of TRIM_ALIASES) {
    if (a.make !== '*' && a.make !== mk) continue;
    for (const w of a.words) {
      if (!tokensContain(trimTokens(q), trimTokens(w))) continue;
      for (const alt of a.words) if (alt !== w) variants.add(q.replace(w, alt));
    }
  }
  return [...variants];
}
function trimFilterMatches(query, trim, series, make) {
  const hay = trimTokens(`${trim || ''} ${series || ''}`);
  return trimQueryVariants(query, make).some((v) => tokensContain(hay, trimTokens(v)));
}

export function vpicMatches(w, vpic, make) {
  const drive = w.drive_filter || '';
  const trim = String(w.trim_filter || '').trim().toLowerCase();
  if (!drive && !trim) return true;
  if (!Array.isArray(vpic)) return false;
  if (drive) {
    const dt = String(vpic[3] || '');
    if (!dt) return false;
    if (drive === '4x4' && !/4WD|AWD|4x4/i.test(dt)) return false;
    if (drive === '2wd' && !/FWD|RWD|4x2/i.test(dt)) return false;
  }
  if (trim) {
    if (vpic[1] !== 'usable') return false;
    if (!trimFilterMatches(trim, vpic[0], vpic[2], make)) return false;
  }
  return true;
}

export function watchMatches(w, v) {
  if (w.make && canonMakeLow(v.make) !== canonMakeLow(w.make)) return false;
  if (w.model && canonModelLow(v.make, v.model) !== canonModelLow(w.make, w.model)) return false;
  if (w.year_min && (!v.year || v.year < w.year_min)) return false;
  if (w.year_max && (!v.year || v.year > w.year_max)) return false;
  if (w.lat != null && w.lng != null && w.radius_mi) {
    if (v.lat == null || v.lng == null) return false;
    if (haversineMiles(w.lat, w.lng, v.lat, v.lng) > w.radius_mi) return false;
  }
  if (!vpicMatches(w, v.vpic, v.make)) return false;
  return true;
}

/** Rolling-window arrivals as the dispatch-shaped objects watchMatches
 * expects (vpic parsed from vpic_json). Used by the seed-on-create paths
 * and the weekly digests. */
export async function loadArrivals(env, since = null) {
  const sql = 'SELECT vehicle_id, year, make, model, row, location, lat, lng, vpic_json FROM arrivals'
    + (since ? ' WHERE seen_at >= ?1' : '');
  const stmt = env.DB.prepare(sql);
  const rows = (await (since ? stmt.bind(since) : stmt).all()).results || [];
  return rows.map((r) => {
    let vpic = null;
    if (r.vpic_json) { try { vpic = JSON.parse(r.vpic_json); } catch { vpic = null; } }
    return {
      id: r.vehicle_id, year: r.year, make: r.make, model: r.model,
      row: r.row, location: r.location, lat: r.lat, lng: r.lng, vpic,
    };
  });
}

export function digestText(matches) {
  const lines = matches.slice(0, MAX_VEHICLES_PER_DIGEST).map((v) =>
    `${v.year || ''} ${v.make} ${v.model} — ${v.location}${v.row ? ` (row ${v.row})` : ''}`.trim());
  const more = matches.length - MAX_VEHICLES_PER_DIGEST;
  if (more > 0) lines.push(`…and ${more} more`);
  return lines.join('\n');
}

async function emailDigest(env, email, matches, { weekly = false, sales = [] } = {}) {
  if (!env.RESEND_API_KEY) {
    // Local dev has no Resend key — log-and-succeed so e2e tests can assert
    // the dedupe bookkeeping. Production without a key correctly reports
    // undelivered (false) so nothing is marked as sent.
    if (env.DEV_MODE === '1') {
      console.log(`DEV email → ${email} (${weekly ? 'weekly' : 'instant'}): ${matches.length} matches, ${sales.length} sales`);
      return true;
    }
    return false;
  }
  const n = matches.length;
  const subject = n
    ? (weekly
      ? `Your week at the yards — ${n} watched car${n === 1 ? '' : 's'} arrived`
      : `${n} watched car${n === 1 ? '' : 's'} just hit the yard`)
    : `Sale days coming up at ${sales.length} yard${sales.length === 1 ? '' : 's'} near you`;
  const intro = weekly
    ? 'Arrivals from the past week matching your YardScout watches — Pro members were pushed each of these within hours of it hitting the yard, up to a week ago:'
    : 'New arrivals matching your YardScout watches:';
  const salesTxt = sales.length
    ? `\n\nSale days at yards near your watches:\n` + sales.slice(0, 6).map((s) =>
        `${s.yard} — ${fmtSaleRange(s.start_date, s.end_date)}${s.pct ? ` (${s.pct}% off)` : ''}`).join('\n')
    : '';
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { authorization: 'Bearer ' + env.RESEND_API_KEY, 'content-type': 'application/json' },
    body: JSON.stringify({
      from: env.EMAIL_FROM || 'YardScout <onboarding@resend.dev>',
      to: [email],
      subject,
      text:
        (n ? `${intro}\n\n${digestText(matches)}` : 'Nothing new matched your watches this week, but:') +
        salesTxt + `\n\n` +
        `Open the app for rows, VINs, and part details:\n${(env.APP_URL || '').trim()}\n\n` +
        `Yards crush cars within weeks — fresh arrivals are the best odds.` +
        (weekly ? `\n\nWant to hear within hours of a watched car arriving, not a week later? Instant push alerts are part of Pro.` : ''),
    }),
  });
  if (!r.ok) console.log('alert email failed:', r.status, (await r.text()).slice(0, 200));
  return r.ok;
}

/** Called from handleCommit (via ctx.waitUntil) with the commit's newArrivals:
 * [{id, year, make, model, row, location, city, state, lat, lng, dateAdded}]. */
export async function dispatchAlerts(env, arrivals) {
  if (!Array.isArray(arrivals) || !arrivals.length) return { users: 0, sends: 0 };

  // Active watches for users whose tier is currently pro (expiry honored).
  const rows = (await env.DB.prepare(
    `SELECT w.id AS wid, w.make, w.model, w.year_min, w.year_max, w.lat, w.lng, w.radius_mi,
            w.drive_filter, w.trim_filter,
            u.id AS user_id, u.email, u.tier, u.tier_expires_at
       FROM watches w JOIN users u ON u.id = w.user_id`
  ).all()).results || [];

  const byUser = new Map();
  for (const r of rows) {
    if (resolveTier(r) !== 'pro') continue;
    if (!byUser.has(r.user_id)) byUser.set(r.user_id, { email: r.email, watches: [] });
    byUser.get(r.user_id).watches.push(r);
  }
  if (!byUser.size) return { users: 0, sends: 0 };

  let sends = 0;
  let usersAlerted = 0;

  for (const [userId, { email, watches }] of byUser) {
    if (sends >= MAX_SENDS_PER_COMMIT) { console.log('alert send budget hit — remaining users deferred'); break; }
    const matched = arrivals.filter((v) => watches.some((w) => watchMatches(w, v)));
    if (!matched.length) continue;

    // Dedupe: drop vehicles this user was already alerted about.
    const fresh = [];
    for (const v of matched) {
      const seen = await env.DB.prepare(
        'SELECT 1 AS x FROM alerts_sent WHERE user_id = ?1 AND vehicle_id = ?2'
      ).bind(userId, String(v.id)).first();
      if (!seen) fresh.push(v);
    }
    if (!fresh.length) continue;

    const payload = {
      title: `${fresh.length} watched car${fresh.length === 1 ? '' : 's'} just hit the yard`,
      body: digestText(fresh),
      // Deep link to the (first) alerted car — the app/PWA bypasses its
      // inventory cache on #alert= entry and focuses the card.
      url: '/#alert=' + encodeURIComponent(String(fresh[0].id)),
    };

    const subs = (await env.DB.prepare(
      'SELECT endpoint, p256dh, auth FROM push_subscriptions WHERE user_id = ?1 LIMIT 3'
    ).bind(userId).all()).results || [];

    let delivered = false;
    if (pushConfigured(env)) {
      for (const sub of subs) {
        if (sends >= MAX_SENDS_PER_COMMIT) break;
        sends++;
        const res = await sendWebPush(env, sub, payload);
        if (res.gone) {
          await env.DB.prepare('DELETE FROM push_subscriptions WHERE endpoint = ?1').bind(sub.endpoint).run();
        } else if (res.ok) delivered = true;
      }
    }
    if (!delivered && sends < MAX_SENDS_PER_COMMIT) {
      sends++;
      delivered = await emailDigest(env, email, fresh);
    }

    if (delivered) {
      usersAlerted++;
      for (const v of fresh) {
        await env.DB.prepare(
          'INSERT OR IGNORE INTO alerts_sent (user_id, vehicle_id, sent_at) VALUES (?1, ?2, ?3)'
        ).bind(userId, String(v.id), isoNow()).run();
      }
    }
  }

  // Prune dedupe rows older than 90 days (yard cycles are ~6 weeks).
  await env.DB.prepare("DELETE FROM alerts_sent WHERE sent_at < ?1")
    .bind(new Date(Date.now() - 90 * 86400_000).toISOString()).run();

  return { users: usersAlerted, sends };
}

/* ===== weekly digest (free tier) =====
 * Pro hears instantly via dispatchAlerts above; free users get one email a
 * week. Arrivals are snapshotted into D1 on every commit so the cron has a
 * week of history to match against. */

/** Called from handleCommit (via ctx.waitUntil). Upserts the commit's
 * arrivals into the rolling window and prunes old rows. */
export async function storeArrivals(env, arrivals) {
  if (!Array.isArray(arrivals) || !arrivals.length) return { stored: 0 };
  const now = isoNow();
  const stmt = env.DB.prepare(
    `INSERT INTO arrivals (vehicle_id, year, make, model, row, location, city, state, lat, lng, date_added, seen_at, vpic_json)
     VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13)
     ON CONFLICT (vehicle_id) DO NOTHING`   // first sighting wins — keeps seen_at honest
  );
  // D1 batches keep this to one round trip per chunk (a commit can carry
  // a few thousand arrivals).
  const CHUNK = 80;
  let stored = 0;
  for (let i = 0; i < arrivals.length; i += CHUNK) {
    const batch = arrivals.slice(i, i + CHUNK).map((v) => stmt.bind(
      String(v.id), v.year ?? null, v.make ?? null, v.model ?? null,
      v.row ?? null, v.location ?? null, v.city ?? null, v.state ?? null,
      v.lat ?? null, v.lng ?? null, v.dateAdded ?? null, now,
      Array.isArray(v.vpic) ? JSON.stringify(v.vpic.slice(0, 4)) : null,
    ));
    await env.DB.batch(batch);
    stored += batch.length;
  }
  await env.DB.prepare('DELETE FROM arrivals WHERE seen_at < ?1')
    .bind(new Date(Date.now() - ARRIVALS_RETENTION_DAYS * 86400_000).toISOString()).run();
  return { stored };
}

/** Cron entry point (see wrangler.toml [triggers]): one digest email per
 * free user whose watches matched anything this week. Shares the
 * alerts_sent dedupe with instant alerts, so a user upgraded mid-week never
 * hears about the same car twice. */
export async function sendWeeklyDigests(env) {
  const since = new Date(Date.now() - 7 * 86400_000).toISOString();
  const arrivals = await loadArrivals(env, since);
  if (!arrivals.length) return { users: 0, emails: 0, arrivals: 0 };

  const rows = (await env.DB.prepare(
    `SELECT w.make, w.model, w.year_min, w.year_max, w.lat, w.lng, w.radius_mi,
            w.drive_filter, w.trim_filter,
            u.id AS user_id, u.email, u.tier, u.tier_expires_at
       FROM watches w JOIN users u ON u.id = w.user_id`
  ).all()).results || [];

  const byUser = new Map();
  for (const r of rows) {
    if (resolveTier(r) === 'pro') continue;   // Pro already heard instantly
    if (!byUser.has(r.user_id)) byUser.set(r.user_id, { email: r.email, watches: [] });
    byUser.get(r.user_id).watches.push(r);
  }

  let emails = 0, usersMatched = 0;
  for (const [userId, { email, watches }] of byUser) {
    if (emails >= MAX_WEEKLY_EMAILS) { console.log('digest email budget hit — remaining users deferred to next week'); break; }
    const matched = arrivals.filter((v) => watches.some((w) => watchMatches(w, v)));
    if (!matched.length) continue;
    const fresh = [];
    for (const v of matched) {
      const seen = await env.DB.prepare(
        'SELECT 1 AS x FROM alerts_sent WHERE user_id = ?1 AND vehicle_id = ?2'
      ).bind(userId, String(v.id)).first();
      if (!seen) fresh.push(v);
    }
    // Upcoming sale days at yards inside this user's watch radii ride along
    // in the same email (dedupe shared with the instant sale pushes).
    const sales = await salesForWatches(env, watches);
    const freshSales = [];
    for (const s of sales) {
      const seen = await env.DB.prepare(
        'SELECT 1 AS x FROM sale_alerts_sent WHERE user_id = ?1 AND event_key = ?2'
      ).bind(userId, s.event_key).first();
      if (!seen) freshSales.push(s);
    }
    if (!fresh.length && !freshSales.length) continue;
    usersMatched++;
    emails++;
    const delivered = await emailDigest(env, email, fresh, { weekly: true, sales: freshSales });
    if (delivered) {
      for (const v of fresh) {
        await env.DB.prepare(
          'INSERT OR IGNORE INTO alerts_sent (user_id, vehicle_id, sent_at) VALUES (?1, ?2, ?3)'
        ).bind(userId, String(v.id), isoNow()).run();
      }
      for (const s of freshSales) {
        await env.DB.prepare(
          'INSERT OR IGNORE INTO sale_alerts_sent (user_id, event_key, sent_at) VALUES (?1, ?2, ?3)'
        ).bind(userId, s.event_key, isoNow()).run();
      }
    }
  }
  return { users: usersMatched, emails, arrivals: arrivals.length };
}

/* ===== sale-day alerts (chain sale calendars) =====
 * Events arrive on every commit already expanded per-yard with coords
 * (see scraper/sale_events.py + push_inventory.py). Pro users with a push
 * subscription hear about sales at yards inside any of their watch radii;
 * free users get them folded into the weekly digest email above. */

const SALE_PUSH_LOOKAHEAD_DAYS = 10;
const MAX_SALE_YARDS_PER_PUSH = 3;

export function fmtSaleRange(startIso, endIso) {
  const opts = { month: 'short', day: 'numeric' };
  const s = new Date(startIso + 'T00:00:00');
  const e = new Date(endIso + 'T00:00:00');
  if (startIso === endIso) return s.toLocaleDateString('en-US', opts);
  const eTxt = e.getMonth() === s.getMonth()
    ? e.toLocaleDateString('en-US', { day: 'numeric' })
    : e.toLocaleDateString('en-US', opts);
  return `${s.toLocaleDateString('en-US', opts)}\u2013${eTxt}`;
}

/** Replace the sale_events table with this commit's snapshot. */
export async function storeSaleEvents(env, events) {
  if (!Array.isArray(events)) return { stored: 0 };
  await env.DB.prepare('DELETE FROM sale_events').run();
  if (!events.length) return { stored: 0 };
  const now = isoNow();
  const stmt = env.DB.prepare(
    `INSERT OR REPLACE INTO sale_events
       (event_key, chain, yard, title, start_date, end_date, pct, lat, lng, stored_at)
     VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)`
  );
  const batch = events.slice(0, 500).map((s) => stmt.bind(
    `${s.yard}|${s.start}`, s.chain ?? null, String(s.yard), s.title ?? null,
    String(s.start), String(s.end || s.start), s.pct ?? null,
    s.lat ?? null, s.lng ?? null, now,
  ));
  await env.DB.batch(batch);
  // Dedupe log outlives events by design; prune at 60 days.
  await env.DB.prepare('DELETE FROM sale_alerts_sent WHERE sent_at < ?1')
    .bind(new Date(Date.now() - 60 * 86400_000).toISOString()).run();
  return { stored: batch.length };
}

/** Active/upcoming stored sales inside any of the user's radius watches.
 * Nationwide watches (no center) are deliberately excluded — a chain-wide
 * sale would blast every yard in the country at them. */
export async function salesForWatches(env, watches) {
  const centers = watches.filter((w) => w.lat != null && w.lng != null && w.radius_mi);
  if (!centers.length) return [];
  const today = new Date().toISOString().slice(0, 10);
  const horizon = new Date(Date.now() + SALE_PUSH_LOOKAHEAD_DAYS * 86400_000)
    .toISOString().slice(0, 10);
  const rows = (await env.DB.prepare(
    `SELECT event_key, yard, title, start_date, end_date, pct, lat, lng
       FROM sale_events WHERE end_date >= ?1 AND start_date <= ?2`
  ).bind(today, horizon).all()).results || [];
  const out = [];
  for (const s of rows) {
    if (s.lat == null || s.lng == null) continue;
    const d = Math.min(...centers.map((w) => haversineMiles(w.lat, w.lng, s.lat, s.lng)));
    const within = centers.some((w) => haversineMiles(w.lat, w.lng, s.lat, s.lng) <= w.radius_mi);
    if (within) out.push({ ...s, dist: Math.round(d) });
  }
  out.sort((a, b) => (a.start_date < b.start_date ? -1 : 1) || a.dist - b.dist);
  return out;
}

/** Called from handleCommit (via ctx.waitUntil) with the commit's saleEvents. */
export async function dispatchSaleAlerts(env, events) {
  const stored = await storeSaleEvents(env, events);
  if (!stored.stored || !pushConfigured(env)) return { ...stored, users: 0, sends: 0 };

  const rows = (await env.DB.prepare(
    `SELECT w.lat, w.lng, w.radius_mi,
            u.id AS user_id, u.email, u.tier, u.tier_expires_at
       FROM watches w JOIN users u ON u.id = w.user_id
      WHERE w.lat IS NOT NULL AND w.radius_mi IS NOT NULL`
  ).all()).results || [];
  const byUser = new Map();
  for (const r of rows) {
    if (resolveTier(r) !== 'pro') continue;   // free tier hears via the digest
    if (!byUser.has(r.user_id)) byUser.set(r.user_id, []);
    byUser.get(r.user_id).push(r);
  }

  let sends = 0, users = 0;
  for (const [userId, watches] of byUser) {
    if (sends >= MAX_SENDS_PER_COMMIT) { console.log('sale-alert send budget hit'); break; }
    const sales = await salesForWatches(env, watches);
    const fresh = [];
    for (const s of sales) {
      const seen = await env.DB.prepare(
        'SELECT 1 AS x FROM sale_alerts_sent WHERE user_id = ?1 AND event_key = ?2'
      ).bind(userId, s.event_key).first();
      if (!seen) fresh.push(s);
    }
    if (!fresh.length) continue;

    const shown = fresh.slice(0, MAX_SALE_YARDS_PER_PUSH);
    const top = shown[0];
    const payload = {
      title: top.pct ? `${top.pct}% off sale near you` : 'Yard sale day near you',
      body: shown.map((s) =>
        `${s.yard} — ${fmtSaleRange(s.start_date, s.end_date)}${s.pct ? ` (${s.pct}% off)` : ''}`
      ).join('\n') + (fresh.length > shown.length ? `\n…and ${fresh.length - shown.length} more` : ''),
      url: '/',
    };
    const subs = (await env.DB.prepare(
      'SELECT endpoint, p256dh, auth FROM push_subscriptions WHERE user_id = ?1 LIMIT 3'
    ).bind(userId).all()).results || [];
    let delivered = false;
    for (const sub of subs) {
      if (sends >= MAX_SENDS_PER_COMMIT) break;
      sends++;
      const res = await sendWebPush(env, sub, payload);
      if (res.gone) {
        await env.DB.prepare('DELETE FROM push_subscriptions WHERE endpoint = ?1').bind(sub.endpoint).run();
      } else if (res.ok) delivered = true;
    }
    if (delivered) {
      users++;
      for (const s of fresh) {
        await env.DB.prepare(
          'INSERT OR IGNORE INTO sale_alerts_sent (user_id, event_key, sent_at) VALUES (?1, ?2, ?3)'
        ).bind(userId, s.event_key, isoNow()).run();
      }
    }
  }
  return { ...stored, users, sends };
}
