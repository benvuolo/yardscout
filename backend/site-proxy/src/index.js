/**
 * yardscout.io site proxy.
 *
 * WHY THIS EXISTS: GitHub Pages' custom-domain mode 301-redirects the old
 * benvuolo.github.io/yardscout/* URLs, and those 301s carry no CORS headers —
 * which silently breaks every in-app fetch() from shipped native builds
 * (origin capacitor://localhost). So instead of GitHub owning the domain:
 *   - GitHub Pages serves plainly at benvuolo.github.io/yardscout (no
 *     redirect, ACAO:* intact) → shipped builds keep working.
 *   - This Worker serves yardscout.io by proxying that origin, adding
 *     permissive CORS so future builds can fetch from yardscout.io directly.
 * Do NOT re-add a custom domain in the GitHub Pages settings (or a docs/CNAME
 * file) — that reintroduces the redirect and re-breaks shipped apps.
 */
const UPSTREAM = 'https://benvuolo.github.io/yardscout';

// Pro entitlements API (account-less, email-anchored) — see entitlements.js.
// Lives here (not in yardscout-api) so the web app talks same-origin.
import { handleEntitlements } from './entitlements.js';
// Server-rendered share pages (/car/<vin>, /yard/<slug>) — see share.js.
import { renderCarPage, renderYardPage, renderYardSitemap, renderYardsPage, renderLandedPage } from './share.js';

// Fixed-allowlist upstream mirror for the scan workflow. Some independent
// yards' hosts (first case: indyupullit.com) hard-block GitHub Actions'
// Azure IP ranges while allowing Cloudflare egress, so the scraper falls
// back to these routes when a direct fetch fails. Deliberately NOT an open
// proxy: only these exact URLs, GET only, cached 1h so even hammering this
// route can't load the yard's site (robots.txt there is allow-all).
const MIRRORS = {
  '/_upstream/indy-inventory': 'https://indyupullit.com/vehicle-inventory/',
  '/_upstream/indy-prices': 'https://indyupullit.com/price-list/',
};
const MIRROR_UA =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36';

/* Universal Links (iOS) + App Links (Android): car share links open the app
 * when it's installed. Apple's CDN and Google's verifier fetch these; both
 * must be 200 application/json with no redirect. */
const AASA = JSON.stringify({
  applinks: {
    apps: [],
    details: [{
      appIDs: ['G23Z9MSBUG.com.benvuolo.yardscout'],
      appID: 'G23Z9MSBUG.com.benvuolo.yardscout',
      components: [{ '/': '/car/*', comment: 'shared car pages' }],
      paths: ['/car/*'],
    }],
  },
});
const ASSET_LINKS = JSON.stringify([{
  relation: ['delegate_permission/common.handle_all_urls'],
  target: {
    namespace: 'android_app',
    package_name: 'io.yardscout.app',
    // Google Play app-signing certificate (Play Console > App integrity).
    sha256_cert_fingerprints: ['19:7D:A7:E9:5D:E5:36:12:32:E0:D7:69:CC:EE:C0:91:47:F3:78:3D:15:87:BE:DA:22:ED:24:BD:F2:F8:CE:EF'],
  },
}]);
function wellKnown(body) {
  return new Response(body, { headers: { 'content-type': 'application/json', 'cache-control': 'public, max-age=3600' } });
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname.startsWith('/api/ent/')) return handleEntitlements(req, env, url);
    if (req.method === 'GET' || req.method === 'HEAD') {
      if (url.pathname === '/.well-known/apple-app-site-association' || url.pathname === '/apple-app-site-association') return wellKnown(AASA);
      if (url.pathname === '/.well-known/assetlinks.json') return wellKnown(ASSET_LINKS);
      let sm = url.pathname.match(/^\/car\/([^/]+)\/?$/);
      if (sm) return renderCarPage(sm[1]);
      sm = url.pathname.match(/^\/yard\/([^/]+)\/?$/);
      if (sm) return renderYardPage(sm[1]);
      if (url.pathname === '/sitemap-yards.xml') return renderYardSitemap();
      if (/^\/yards\/?$/.test(url.pathname)) return renderYardsPage();
      sm = url.pathname.match(/^\/landed(?:\/([^/]+))?\/?$/);
      if (sm) return renderLandedPage(sm[1] || '');
    }
    const mirror = MIRRORS[url.pathname];
    if (mirror) {
      if (req.method !== 'GET') return new Response('GET only', { status: 405 });
      const r = await fetch(mirror, {
        headers: {
          'user-agent': MIRROR_UA,
          accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'accept-language': 'en-US,en;q=0.9',
          'cache-control': 'no-cache',
          referer: 'https://indyupullit.com/',
        },
        cf: { cacheTtl: 3600, cacheEverything: true },
      });
      const h = new Headers({ 'content-type': 'text/html; charset=utf-8' });
      h.set('access-control-allow-origin', '*');
      return new Response(r.body, { status: r.status, headers: h });
    }
    // Normalize www → apex.
    if (url.hostname === 'www.yardscout.io') {
      url.hostname = 'yardscout.io';
      return Response.redirect(url.toString(), 301);
    }
    const upstream = UPSTREAM + url.pathname + url.search;
    const r = await fetch(upstream, {
      method: req.method,
      headers: { accept: req.headers.get('accept') || '*/*' },
      cf: { cacheTtl: 300, cacheEverything: true },
    });
    const h = new Headers(r.headers);
    h.set('access-control-allow-origin', '*');
    // App-shell files must revalidate on every load. Without this, the zone's
    // 4-hour browser TTL (max-age=14400) meant a deploy could be invisible to
    // returning visitors for hours (owner-reported: new Alerts-tab feature
    // missing on a browser that had the site cached). ETags pass through from
    // GitHub Pages, so revalidation is a cheap 304 — and the edge cache above
    // (cacheTtl 300) still shields the origin. The big /data/ inventory files
    // keep their long cache deliberately: the app refreshes those itself
    // (cache-first + background revalidate in its jh-data store).
    const p = url.pathname;
    if (!p.startsWith('/data/') && (p === '/' || /\.(html|js|css|webmanifest)$/.test(p))) {
      h.set('cache-control', 'no-cache');
    }
    return new Response(r.body, { status: r.status, headers: h });
  },
};
