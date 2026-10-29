/* Native app update check (2026-10-29): GET /v1/app-version?platform=ios|android
 *
 * The apps compare their own version (Capacitor App.getInfo) with this and
 * show either a dismissible "Update available" banner (behind `latest`) or a
 * blocking "Update required" screen (behind `min`).
 *
 *   latest (iOS)      docs/app-version.json "ios", written by app-store-version.yml
 *                     from the App Store Connect API once a version is live
 *                     (READY_FOR_SALE). Apple's public lookup answers 403 to
 *                     Cloudflare, so the Worker no longer calls it.
 *   latest (Android)  docs/app-version.json, written by release-android.yml on
 *                     a production upload. Play has no public lookup, so it is
 *                     held back ANDROID_REVIEW_HOLD_MS after the upload (review).
 *   min               docs/app-version.json "min" — the owner edits this one
 *                     number on GitHub to force an update. Empty = no minimum.
 *
 * Cached: the site file at the edge for 5 min, and the response for 5 min.
 * Any failure answers {latest:null,min:null} — an update check must never
 * block the app because a lookup failed.
 */
import { json, err } from './util.js';

const H = 3600_000;
const ANDROID_REVIEW_HOLD_MS = 48 * H;
const STORE = {
  ios: 'https://apps.apple.com/app/id6817126581',
  android: 'https://play.google.com/store/apps/details?id=io.yardscout.app',
};
const VERSION_RE = /^\d+(\.\d+){0,3}$/;
const cleanVersion = (v) => (VERSION_RE.test(String(v || '').trim()) ? String(v).trim() : null);

function siteBases(env) {
  if (env.DEV_MODE === '1' && env.APPVER_SITE_TEST) return [env.APPVER_SITE_TEST];
  return ['https://benvuolo.github.io/yardscout', 'https://yardscout.io'];
}

async function loadSiteFile(env) {
  for (const base of siteBases(env)) {
    try {
      const r = await fetch(`${base}/app-version.json`, { cf: { cacheTtl: 300 }, signal: AbortSignal.timeout(6000) });
      if (r.ok) return await r.json();
    } catch { /* try the next base */ }
  }
  return {};
}

export async function appVersionInfo(env, platform, now = Date.now()) {
  const file = await loadSiteFile(env);
  const min = cleanVersion(file && file.min && file.min[platform]);
  let latest = null;
  if (platform === 'ios') {
    // Recorded only once the version is live, so no hold is needed.
    latest = cleanVersion(file && file.ios && file.ios.latest);
  } else {
    const a = (file && file.android) || {};
    const at = Date.parse(a.releasedAt || '');
    if (Number.isFinite(at) && now - at >= ANDROID_REVIEW_HOLD_MS) latest = cleanVersion(a.latest);
  }
  const message = typeof file.message === 'string' ? file.message.slice(0, 240) : '';
  return { platform, latest, min, storeUrl: STORE[platform], message };
}

export async function handleAppVersion(req, env) {
  const platform = new URL(req.url).searchParams.get('platform');
  if (platform !== 'ios' && platform !== 'android') return err(400, 'bad_platform', 'platform must be ios or android.');
  let info;
  try { info = await appVersionInfo(env, platform); } catch { info = { platform, latest: null, min: null, storeUrl: STORE[platform], message: '' }; }
  return json(info, { headers: { 'cache-control': 'public, max-age=300' } });
}
