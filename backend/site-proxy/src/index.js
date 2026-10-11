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

export default {
  async fetch(req) {
    const url = new URL(req.url);
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
