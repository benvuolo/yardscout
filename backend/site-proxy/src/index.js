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

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname.startsWith('/api/ent/')) return handleEntitlements(req, env, url);
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
    return new Response(r.body, { status: r.status, headers: h });
  },
};
