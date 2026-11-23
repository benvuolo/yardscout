/* Counting views of the public "what landed" pages (2026-11-20).
 *
 * The make page (/landed/<make>) and the model page (/landed/<make>/<model>)
 * carry one small inline script. In the visitor's browser it sends, with
 * navigator.sendBeacon, to the API's existing event endpoint (the one the
 * app's sendEvent uses, backend/src/attribution.js):
 *   landed-view/<page>                 one per page view
 *   landed-src/<source>/<page>         a second one when the source is known
 * <page> is the make slug, or "<make>-<model>", cut to fit the API's name
 * rule (at most 48 characters, [a-z0-9/_-]). The body is {e, p:'web'} only:
 * no ids, no cookies, nothing stored on the device, no call from the edge
 * worker. Scripts off or the endpoint down: the page is the same.
 *
 * Source: an explicit ?s=<word> on the URL (letters, digits, hyphen, at most
 * 12, lowercased; anything else is ignored) wins; else the referrer's site
 * when it is one of reddit, google, bing, duckduckgo, facebook, youtube;
 * else none. With an explicit ?s=<word>, the page's app buttons also carry
 * it as utm_source=<word> (their utm_medium and utm_campaign stay): the
 * app's own first-visit attribution (docs/app.js ATTRIB) reads utm_source.
 *
 * landedSource and landedEventNames are self-contained (no outside names):
 * the page script is built from their own source text, so the browser and
 * the tests run the same code. */

export const EVENTS_URL = 'https://yardscout-api.yardscout.workers.dev/v1/events';

/** {src, explicit}: the visit's source, '' when none. */
export function landedSource(search, referrer) {
  var q = String(search || '');
  var m = /[?&]s=([^&#]*)/.exec(q);
  if (m) {
    var w = '';
    try { w = decodeURIComponent(m[1].replace(/\+/g, ' ')); } catch (e) { w = ''; }
    if (/^[A-Za-z0-9][A-Za-z0-9-]{0,11}$/.test(w)) return { src: w.toLowerCase(), explicit: true };
  }
  var host = '';
  try { host = new URL(String(referrer || '')).hostname.toLowerCase(); } catch (e) { host = ''; }
  if (!host) return { src: '', explicit: false };
  var sites = { reddit: /(^|\.)reddit\.com$/, google: /(^|\.)google\.[a-z]{2,3}(\.[a-z]{2})?$/, bing: /(^|\.)bing\.com$/,
    duckduckgo: /(^|\.)duckduckgo\.com$/, facebook: /(^|\.)facebook\.com$/, youtube: /(^|\.)youtube\.com$/ };
  for (var k in sites) if (Object.prototype.hasOwnProperty.call(sites, k) && sites[k].test(host)) return { src: k, explicit: false };
  return { src: '', explicit: false };
}

/** The event names for a page slug and a source ('' = none). */
export function landedEventNames(page, src) {
  var cut = function (s, n) { return String(s).slice(0, n).replace(/-+$/, ''); };
  var p = String(page || '').toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '');
  if (!p) return [];
  var out = ['landed-view/' + cut(p, 48 - 12)];
  var s = String(src || '').toLowerCase();
  if (/^[a-z0-9][a-z0-9-]{0,11}$/.test(s)) {
    var head = 'landed-src/' + s.replace(/-+$/, '') + '/';
    var rest = cut(p, 48 - head.length);
    if (rest) out.push(head + rest);
  }
  return out;
}

/** The inline script for a landed page whose slug is `page`. */
export function landedCountScript(page) {
  const p = String(page || '').toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '');
  if (!p) return '';
  // The Worker is bundled before it runs, and the bundler may wrap inner
  // functions in its own helper (`__name(fn, "x")`), which then appears in
  // the .toString() text below. A browser has no such helper, so the script
  // brings a harmless one (2026-11-23: without it every page view threw and
  // nothing was counted for three days).
  return `<script>(function(){try{var __name=function(f){return f;};
var n=navigator;if(n.webdriver||/^(localhost|127\\.0\\.0\\.1|\\[::1\\])$/.test(location.hostname))return;
var S=(${landedSource.toString()})(location.search,document.referrer);
var E=(${landedEventNames.toString()})(${JSON.stringify(p)},S.src);
if(S.explicit)document.addEventListener('DOMContentLoaded',function(){[].forEach.call(document.querySelectorAll('a[href*="utm_source=page"]'),function(a){a.setAttribute('href',a.getAttribute('href').replace('utm_source=page','utm_source='+S.src));});});
if(!n.sendBeacon)return;
E.forEach(function(e){try{n.sendBeacon(${JSON.stringify(EVENTS_URL)},new Blob([JSON.stringify({e:e,p:'web'})],{type:'text/plain'}));}catch(x){}});
}catch(x){}})();</script>`;
}
